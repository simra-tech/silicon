#!/usr/bin/env python3
"""Parse source-bound macro LEFs in OpenROAD and verify saved OpenDB pins."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

PDK=Path('/foss/pdks/ihp-sg13g2')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def quote(path):
    assert not any(c in str(path)for c in '{}\n')
    return '{'+str(path)+'}'


def inspect_tcl(output):
    return [
        'set fp [open '+quote(output)+' w]',
        'set units [[ord::get_db_tech] getDbUnitsPerMicron]',
        'puts $fp "UNITS\t$units"',
        'foreach lib [[ord::get_db] getLibs] {',
        '  foreach m [$lib getMasters] {',
        '    set n [$m getName]',
        '    if {$n ni {g1_bgr g1_sense}} {continue}',
        '    puts $fp "MASTER\t$n\t[$m getWidth]\t[$m getHeight]"',
        '    foreach t [$m getMTerms] {',
        '      puts $fp "PIN\t$n\t[$t getName]\t[$t getIoType]\t[$t getSigType]"',
        '      foreach p [$t getMPins] {',
        '        foreach b [$p getGeometry] {',
        '          puts $fp "RECT\t$n\t[$t getName]\t[[$b getTechLayer] getName]\t[$b xMin]\t[$b yMin]\t[$b xMax]\t[$b yMax]"',
        '        }',
        '      }',
        '    }',
        '  }',
        '}',
        'close $fp',
    ]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bgr',type=Path,required=True)
    p.add_argument('--sense',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--openroad',type=Path,help='Explicit integration-flow binary; schema identity recorded')
    a=p.parse_args()
    assert not a.output.exists() and len(os.sched_getaffinity(0))==1
    assert (PDK/'COMMIT').read_text().strip()=='84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
    masters={}
    for name,path in [('g1_bgr',a.bgr),('g1_sense',a.sense)]:
        data=json.loads((path/'analysis.json').read_text())
        assert data['status']=='passed conservative native-metal LEF abstraction'
        assert sha(path/(name+'.lef'))==data['LEF_sha256']
        assert sha(path/(name+'.gds'))==data['abstract_GDS_sha256']
        masters[name]=data
    a.output.mkdir(parents=True)
    (a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    tech=PDK/'libs.ref/sg13g2_stdcell/lef/sg13g2_tech.lef'
    exe=a.openroad if a.openroad else Path(shutil.which('openroad'))
    assert exe.is_file()
    version=subprocess.run([str(exe),'-version'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,check=True).stdout
    (a.output/'openroad-version.txt').write_text(version)
    runs=[]
    database=a.output/'closed_macro_views.odb'
    for kind in ['parse','roundtrip']:
        commands=['set_thread_count 1']
        if kind=='parse':
            commands+=['read_lef '+quote(tech),'read_lef '+quote(a.bgr/'g1_bgr.lef'),
                       'read_lef '+quote(a.sense/'g1_sense.lef')]
        else:
            commands+=['read_db '+quote(database)]
        commands+=inspect_tcl(a.output/(kind+'.tsv'))
        if kind=='parse':
            commands+=['write_db '+quote(database)]
        script=a.output/(kind+'.tcl');script.write_text('\n'.join(commands)+'\n')
        start=time.monotonic()
        command=['timeout','--kill-after=5','90',str(exe),'-exit',str(script)]
        with(a.output/(kind+'.log')).open('x')as log:
            r=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
        runs.append(dict(kind=kind,command=command,returncode=r.returncode,wall_s=time.monotonic()-start))
        (a.output/'runs.json').write_text(json.dumps(runs,indent=2)+'\n')
        assert r.returncode==0,(kind,r.returncode)
    parse=(a.output/'parse.tsv').read_text().splitlines()
    replay=(a.output/'roundtrip.tsv').read_text().splitlines()
    assert sorted(parse)==sorted(replay)
    rows=[line.split('\t')for line in parse]
    units=int(next(r[1]for r in rows if r[0]=='UNITS'))
    assert units>0
    seen=set();rects=0
    layer_names={8:'Metal1',10:'Metal2',30:'Metal3',50:'Metal4',67:'Metal5',126:'TopMetal1',134:'TopMetal2'}
    for name,data in masters.items():
        size=[r for r in rows if r[:2]==['MASTER',name]]
        assert len(size)==1 and [int(v)/units for v in size[0][2:]]==data['size_um']
        for pin,info in data['pins'].items():
            header=[r for r in rows if r[:3]==['PIN',name,pin]]
            assert len(header)==1 and header[0][3:]==[info['direction'],info['use']]
            boxes=[r for r in rows if r[:3]==['RECT',name,pin]]
            assert len(boxes)==1 and boxes[0][3]==layer_names[info['layer']]
            assert [int(v)*1000/units for v in boxes[0][4:]]==info['bbox_dbu']
            seen.add((name,pin));rects+=1
    assert len(seen)==18 and sum(r[0]=='PIN'for r in rows)==18 and rects==18
    result=dict(status='passed native-bound LEF OpenDB parse and saved roundtrip',
                OpenROAD_version=version.strip(),OpenROAD_binary_sha256=sha(exe),
                PDK_commit=(PDK/'COMMIT').read_text().strip(),tech_LEF_sha256=sha(tech),
                source_macro_abstracts={k:dict(LEF_sha256=v['LEF_sha256'],GDS_sha256=v['abstract_GDS_sha256'])for k,v in masters.items()},
                OpenDB_sha256=sha(database),script_sha256=sha(Path(__file__)),units_per_um=units,
                macro_sizes=2,pin_names_directions_uses_rectangles=18,saved_OpenDB_roundtrip='passed',runs=runs,
                not_run=['macro obstacle roundtrip detail','fullchip placement/routing','fullchip DRC/LVS/PEX','electrical adoption'])
    (a.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    main()

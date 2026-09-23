#!/usr/bin/env python3
"""Import isolated full-chip DEF with native-bound macro LEFs; audit OpenDB."""
import argparse
import collections
import json
import os
from pathlib import Path
import subprocess
import time
from check_closed_macro_odb import sha, quote

HERE = Path(__file__).resolve().parent
DESIGN = HERE.parents[1]
PDK = Path('/foss/pdks/ihp-sg13g2')
OPENROAD = Path('/foss/tools/openroad-librelane/bin/openroad')


def observation(path):
    return [
        'set fp [open '+quote(path)+' w]',
        'set b [ord::get_db_block]',
        'set die [$b getDieArea]',
        'puts $fp "DIE\t[$die xMin]\t[$die yMin]\t[$die xMax]\t[$die yMax]"',
        'foreach i [$b getInsts] {',
        '  set m [$i getMaster]; set bb [$i getBBox]',
        '  puts $fp "INST\t[$i getName]\t[$m getName]\t[$i getOrient]\t[$bb xMin]\t[$bb yMin]\t[$bb xMax]\t[$bb yMax]"',
        '  foreach t [$m getMTerms] {puts $fp "MTERM\t[$m getName]\t[$t getName]"}',
        '}',
        'foreach n [$b getNets] {',
        '  puts $fp "NET\t[$n getName]"',
        '  foreach t [$n getITerms] {',
        '    puts $fp "CONN\t[$n getName]\t[[$t getInst] getName]\t[[$t getMTerm] getName]"',
        '  }',
        '  foreach t [$n getBTerms] {puts $fp "CONN\t[$n getName]\tPIN\t[$t getName]"}',
        '}',
        'close $fp',
    ]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--prepared',type=Path,required=True)
    p.add_argument('--bgr',type=Path,required=True)
    p.add_argument('--sense',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a = p.parse_args()
    assert not a.output.exists() and len(os.sched_getaffinity(0)) == 1
    assert sha(OPENROAD)=='a20f82ef703596ff75e8ddba7a89c8447f62c5113dcb9d8be8740eb229a44ddc'
    assert (PDK/'COMMIT').read_text().strip()=='84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
    meta = json.loads((a.prepared/'analysis.json').read_text())
    source = a.prepared/'g1_chip_top_unrouted.def'
    assert meta['status']=='passed source-preserving unrouted DEF preparation' and sha(source)==meta['DEF_sha256']
    for name,folder in [('g1_bgr',a.bgr),('g1_sense',a.sense)]:
        data = json.loads((folder/'analysis.json').read_text())
        assert data['status']=='passed conservative native-metal LEF abstraction'
        assert sha(folder/(name+'.lef'))==data['LEF_sha256']
    lefs = [PDK/'libs.ref/sg13g2_stdcell/lef/sg13g2_tech.lef',PDK/'libs.ref/sg13g2_stdcell/lef/sg13g2_stdcell.lef',
            DESIGN/'blocks/g1_padring/ip/sg13g2_io_padbare/lef/sg13g2_io.lef',
            DESIGN/'blocks/g1_padring/ip/bondpad_70x70_tm1/lef/bondpad_70x70_tm1.lef',
            a.bgr/'g1_bgr.lef', a.sense/'g1_sense.lef']
    lefs += [DESIGN/'blocks'/rel for rel in [
        'g1_ctrl/layout/g1_digital.lef','g1_trip/layout/g1_trip.lef','g1_gate/layout/g1_gate.lef',
        'g1_osc/layout/g1_osc.lef','g1_t2f/layout/g1_t2f.lef','g1_dut/layout/g1_dut_macro.lef',
        'g1_dose/layout/g1_dose_macro.lef','g1_ctrl/ls/layout/g1_ls_up.lef']]
    assert all(path.is_file() for path in lefs)
    a.output.mkdir(parents=True)
    (a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    runs=[]; odb=a.output/'unrouted_fullchip.odb'
    for mode in ['import','roundtrip']:
        lines=['set_thread_count 1']
        lines += ['read_lef '+quote(path) for path in lefs]+['read_def '+quote(source)] if mode=='import' else ['read_db '+quote(odb)]
        lines += observation(a.output/(mode+'.tsv'))
        if mode=='import':
            lines += ['write_db '+quote(odb)]
        script=a.output/(mode+'.tcl');script.write_text('\n'.join(lines)+'\n')
        command=['timeout','--kill-after=5','120',str(OPENROAD),'-exit',str(script)]
        start=time.monotonic()
        with (a.output/(mode+'.log')).open('x') as log:
            result=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
        runs.append(dict(mode=mode,command=command,returncode=result.returncode,wall_s=time.monotonic()-start))
        (a.output/'runs.json').write_text(json.dumps(runs,indent=2)+'\n')
        assert result.returncode==0,(mode,result.returncode)
    original=(a.output/'import.tsv').read_text().splitlines()
    assert sorted(original)==sorted((a.output/'roundtrip.tsv').read_text().splitlines())
    rows=[r.split('\t') for r in original]
    assert [r for r in rows if r[0]=='DIE']==[['DIE','0','0','1414000','1414000']]
    actual={r[1]:r for r in rows if r[0]=='INST'}
    expected={r['instance']:dict(master=r['master'],xy=r['new'][:2],orient=r['new'][2])for r in meta['changes']}
    expected.update({r['instance']:r for r in meta['added_native_IO_fillers']})
    assert len(actual)==len(expected)==4904 and set(actual)==set(expected)
    orientations=dict(N='R0',W='R90',S='R180',E='R270',FS='MX',FN='MY',FW='MXR90',FE='MYR90')
    for name,info in expected.items():
        row=actual[name]
        assert row[2]==info['master'] and row[3]==orientations[info['orient']],(name,row,info)
        assert [int(v)for v in row[4:6]]==info['xy'],(name,row,info)
    pins=collections.defaultdict(set)
    for row in rows:
        if row[0]=='MTERM':
            pins[row[1]].add(row[2])
    expected_nets={}
    for scope,nets in meta['original_connectivity'].items():
        for name,terminals in nets.items():
            assert name not in expected_nets
            values=set()
            for inst,pin in terminals:
                if inst=='*':
                    values.update((n,pin)for n,c in expected.items()if pin in pins[c['master']])
                else:
                    values.add((inst,pin))
            if scope=='SPECIALNETS' and name in ('VDD','VSS','IOVDD','IOVSS'):
                pin=dict(VDD='vdd',VSS='vss',IOVDD='iovdd',IOVSS='iovss')[name]
                values.update((r['instance'],pin)for r in meta['added_native_IO_fillers'])
            expected_nets[name]=values
    observed=collections.defaultdict(set)
    for row in rows:
        if row[0]=='NET': observed[row[1]]
        if row[0]=='CONN': observed[row[1]].add(tuple(row[2:]))
    differences={name:dict(missing=sorted(expected_nets.get(name,set())-observed.get(name,set())),extra=sorted(observed.get(name,set())-expected_nets.get(name,set())))for name in set(expected_nets)|set(observed)if expected_nets.get(name)!=observed.get(name)}
    (a.output/'connectivity_differences.json').write_text(json.dumps(differences,indent=2)+'\n')
    assert not differences
    result=dict(status='passed full-chip native LEF import and OpenDB placement/connectivity roundtrip',
                source_DEF_sha256=sha(source),ODB_sha256=sha(odb),script_sha256=sha(Path(__file__)),
                OpenROAD_sha256=sha(OPENROAD),LEFs=[dict(path=str(q),sha256=sha(q))for q in lefs],
                instances=len(actual),nets=len(observed),terminal_connections=sum(map(len,observed.values())),runs=runs,
                not_run=['macro obstacle/IO native geometry roundtrip','PDN and signal routing','fullchip LVS/PEX/DRC/density/antenna/STA/currentIR','electrical adoption'])
    (a.output/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    main()

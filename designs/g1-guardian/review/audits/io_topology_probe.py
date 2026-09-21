#!/usr/bin/env python3
"""Stock flat IO LVS probes: global substrate declaration and resistor marker.

No implicit connections, device removals, ignored pins or altered PDK rules.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time

p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',type=Path,required=True);p.add_argument('--report',type=Path,required=True);a=p.parse_args()
if a.work.exists() or a.report.exists():raise FileExistsError('Preserve old runs')
a.work.mkdir(parents=True);a.report.mkdir(parents=True)
work,report=a.work.resolve(),a.report.resolve();pdk=Path('/foss/pdks/ihp-sg13g2')
gds=pdk/'libs.ref/sg13g2_io/gds/sg13g2_io.gds';cdl=pdk/'libs.ref/sg13g2_io/cdl/sg13g2_io.cdl'
annotated=Path('build/scratch/io-recognition-20260921/sg13g2_io_annotation_only.gds').resolve();assert annotated.exists()
global_cdl=work/'sg13g2_io_global_sub.cdl';global_cdl.write_text('* DIAGNOSTIC reference-view global substrate declaration\n.GLOBAL sub!\n'+cdl.read_text())
rows=[]
for name,layout,reference in [('flat_baseline',gds,cdl),('flat_global_substrate',gds,global_cdl),('flat_global_and_polyres',annotated,global_cdl)]:
    target=report/name
    cmd=['python3',str(pdk/'libs.tech/klayout/tech/lvs/run_lvs.py'),'--layout',str(layout),'--netlist',str(reference),
         '--topcell','sg13g2_IOPadAnalog','--run_mode','flat','--combine_devices','--run_dir',str(target),'--top_lvl_pins','--spice_comments']
    start=time.monotonic()
    with (report/(name+'.log')).open('w') as f:proc=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,timeout=180)
    txt=(report/(name+'.log')).read_text();rows.append({'name':name,'command':cmd,'exit_code':proc.returncode,
        'status':'passed' if proc.returncode==0 and 'Comparison mode: PASS (netlists match).' in txt else 'failed','wall_seconds':time.monotonic()-start,
        'layout_sha256':hashlib.sha256(layout.read_bytes()).hexdigest(),'reference_sha256':hashlib.sha256(reference.read_bytes()).hexdigest()})
    (report/'manifest.json').write_text(json.dumps({'scope':'NON-PRODUCTION topology diagnostic; no global assumption adopted without full assembly validation','reference_delta':'.GLOBAL sub!; original devices and parameters unchanged','checks':rows},indent=2)+'\n')
    root=Path(__file__).resolve().parents[4]
    db=next(target.glob('*.lvsdb'))
    with (target/'xref.txt').open('w') as f:subprocess.run(['klayout','-b','-rd','db='+str(db),'-r',str(root/'designs/g1-guardian/blocks/g1_padring/flow/lvs/xref_summary.py')],stdout=f,stderr=subprocess.STDOUT,timeout=120)
    print(json.dumps(rows[-1]),flush=True)

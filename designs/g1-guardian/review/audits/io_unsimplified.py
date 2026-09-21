#!/usr/bin/env python3
"""Retain all-VDD dummy devices using the stock no_simplify option; no deck edits."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time

ROOT=Path(__file__).resolve().parents[4];B=ROOT/'designs/g1-guardian/blocks/g1_padring'
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
if a.output.exists():raise FileExistsError('Preserve earlier evidence')
a.output.mkdir(parents=True);out=a.output.resolve()
candidate=ROOT/'build/scratch/pad-outward-dummy-clean-20260921/g1_chip_top.gds'
intent=ROOT/'build/scratch/pad-outward-dummy-clean-lvs-20260921/g1_chip_top_intentional_dummy.cdl'
rows=[]
for name,gds,cdl in [('baseline',B/'layout/g1_chip_top.gds',B/'netlist/g1_chip_top.cdl'),
                     ('candidate_stock',candidate,B/'netlist/g1_chip_top.cdl'),('candidate_intent',candidate,intent)]:
    target=out/name
    cmd=['python3','/foss/pdks/ihp-sg13g2/libs.tech/klayout/tech/lvs/run_lvs.py','--layout',str(gds),
         '--netlist',str(cdl),'--topcell','sg13g2_IOPadIn','--run_mode','deep','--run_dir',str(target),
         '--top_lvl_pins','--spice_comments','--no_simplify']
    start=time.monotonic()
    with (out/(name+'.log')).open('w') as f:proc=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,timeout=180)
    txt=(out/(name+'.log')).read_text()
    rows.append({'name':name,'command':cmd,'status':'passed' if proc.returncode==0 and 'Comparison mode: PASS (netlists match).' in txt else 'failed',
                 'process_exit':proc.returncode,'wall_seconds':time.monotonic()-start,'gds_sha256':hashlib.sha256(gds.read_bytes()).hexdigest(),
                 'cdl_sha256':hashlib.sha256(cdl.read_bytes()).hexdigest()})
    (out/'manifest.json').write_text(json.dumps({'scope':'Stock no_simplify diagnostic; expected pre-existing IO failures retained','checks':rows},indent=2)+'\n')
    db=next(target.glob('*.lvsdb'))
    with (target/'xref.txt').open('w') as f:subprocess.run(['klayout','-b','-rd','db='+str(db),'-r',str(B/'flow/lvs/xref_summary.py')],stdout=f,stderr=subprocess.STDOUT,timeout=120)
    print(json.dumps(rows[-1]),flush=True)

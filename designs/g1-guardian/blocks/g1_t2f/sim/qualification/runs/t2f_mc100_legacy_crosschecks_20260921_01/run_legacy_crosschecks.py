#!/usr/bin/env python3
"""Repeat selected complete physical samples on legacy runtime, one at a time."""
import argparse,json,shutil,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--run-id',required=True);ap.add_argument('--image-id',required=True);a=ap.parse_args()
out=HERE/'runs'/a.run_id;out.mkdir(parents=True,exist_ok=False)
shutil.copy(Path(__file__),out/Path(__file__).name);shutil.copy(HERE/'legacy_crosscheck_selection.json',out/'selection.json')
selection=json.loads((out/'selection.json').read_text());ledger={'command':sys.argv,'scope':'Repeat all four points of each selected physical sample on one runtime;25/100 are calibration members,−40/125 independent checks. Repeats are not additional independent MC samples.','cases':[]}
for sample in selection['samples']:
 name=sample['legacy_run_id'];cmd=[sys.executable,str(HERE/'run_joint.py'),'--run-id',name,'--image-id',a.image_id,'--mismatch','--seed',str(sample['seed']),'--temperatures=-40,25,100,125'];start=time.monotonic()
 with (out/(name+'_driver.log')).open('x') as f:rc=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT).returncode
 m=HERE/'runs'/name/'manifest.json';cases=json.loads(m.read_text())['cases'] if m.exists() else []
 row={'run_id':name,'seed':sample['seed'],'driver_exit':rc,'completed_points':sum(c['status']=='passed' for c in cases),'wall_seconds':time.monotonic()-start};ledger['cases'].append(row);(out/'manifest.json').write_text(json.dumps(ledger,indent=2)+'\n');print(json.dumps(row),flush=True)

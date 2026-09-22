#!/usr/bin/env python3
"""Bounded isolated solver comparisons against archived completed leaves."""
import argparse,json,subprocess,sys
from pathlib import Path
SIM=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--run-id',required=True);p.add_argument('--references',required=True);a=p.parse_args()
out=SIM/'qualification'/a.run_id;out.mkdir(exist_ok=False);(out/'driver.py').write_text(Path(__file__).read_text());(out/'provenance.json').write_text(json.dumps({'arguments':sys.argv[1:],'scope':'Same source and sampled devices; only sparse to KLU solver changes.600s watchdog.'},indent=2)+'\n');results=[]
for i,reference in enumerate(a.references.split(',')):
 if (out/'PAUSE_REQUESTED').exists(): break
 provenance=json.loads((SIM/'qualification'/reference/'provenance.json').read_text());args=provenance['runner_arguments'];new=[];j=0
 while j<len(args):
  if args[j] in ['--run-id','--timeout-s','--replay-reference','--solver','--solver-reference']:j+=2
  else:new.append(args[j]);j+=1
 leaf=f'{a.run_id}-p{i:02d}'
 rc=subprocess.run([sys.executable,str(SIM/'run_kickback_qualification.py'),'--run-id',leaf,*new,'--solver','klu','--solver-reference',reference,'--timeout-s','600'],cwd=SIM).returncode
 entry={'reference':reference,'leaf':leaf,'runner_returncode':rc};results.append(entry)
 if rc==0:entry['comparison_returncode']=subprocess.run([sys.executable,str(SIM/'compare_joint_solver.py'),leaf],cwd=SIM).returncode
 (out/'summary.json').write_text(json.dumps(results,indent=2)+'\n')

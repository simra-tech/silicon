#!/usr/bin/env python3
"""Replay one retained joint leaf with a longer watchdog and exact-deck checks."""
import argparse
import json
import subprocess
import sys
from pathlib import Path
SIM=Path(__file__).resolve().parent

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--source-run',required=True);p.add_argument('--run-id',required=True)
 p.add_argument('--timeout-s',type=float,default=600)
 a=p.parse_args();source=SIM/'qualification'/a.source_run
 old=json.loads((source/'provenance.json').read_text())
 args=old['runner_arguments'].copy()
 if '--replay-reference' in args:raise ValueError('Replay an original leaf, not a previous replay')
 if '--timeout-s' in args:
  i=args.index('--timeout-s');del args[i:i+2]
 args[args.index('--run-id')+1]=a.run_id
 args += ['--timeout-s',str(a.timeout_s),'--replay-reference',a.source_run]
 rc=subprocess.run([sys.executable,str(SIM/'run_kickback_qualification.py'),*args],cwd=SIM).returncode
 out=SIM/'qualification'/a.run_id
 (out/'replay_driver.py').write_text(Path(__file__).read_text())
 fpref=a.source_run.rsplit('-p',1)[0]+'-p00'
 initial=json.loads((SIM/'qualification'/fpref/'summary.json').read_text())[0]
 result=json.loads((out/'summary.json').read_text())[0] if (out/'summary.json').exists() else {}
 comparison=json.loads((out/'same_deck_replay.json').read_text())
 report={'reference_run':a.source_run,'recovery_run':a.run_id,'original_timeout_s':comparison['original_timeout_s'],
         'new_timeout_s':a.timeout_s,'runner_returncode':rc,'same_deck_check':comparison['status'],
         'solver_status':result.get('solver_status','not run'),'wall_s':result.get('wall_s'),
         'fingerprint_reference_run':fpref,'observed_parameter_count':len(result.get('fingerprints',[])),
         'observed_fingerprints_match_sample_anchor':result.get('fingerprints')==initial['fingerprints'],
         'scope':'Original timed-out leaf is retained. Same normalized deck, source snapshots, model hashes, image and engine required before launch. Fingerprints compare the same sample first successful code probe because timed-out leaf did not print its final parameter block.'}
 report['status']='passed' if rc==0 and report['same_deck_check']=='passed' and report['solver_status']=='passed' and report['observed_parameter_count']==27 and report['observed_fingerprints_match_sample_anchor'] else 'failed'
 (out/'recovery_validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
 if report['status']!='passed':sys.exit(1)
if __name__=='__main__':main()

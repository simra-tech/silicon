#!/usr/bin/env python3
"""Run one tool with immutable input fingerprints and bounded evidence capture."""
import argparse,datetime,hashlib,json,os,subprocess,sys,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'designs/g1-guardian/blocks/g1_top/sim'))
from run_bounded import run_bounded,atomic_json
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',required=True,type=Path);ap.add_argument('--timeout',required=True,type=float);ap.add_argument('--input',action='append',default=[],type=Path);ap.add_argument('--image-id',required=True);ap.add_argument('command',nargs=argparse.REMAINDER);a=ap.parse_args()
cmd=a.command[1:] if a.command[:1]==['--'] else a.command
if not cmd:ap.error('no command')
a.out.mkdir(parents=True,exist_ok=False)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
md=dict(input_sha256={str(p):sha(p) for p in a.input},image_id=a.image_id,runner_sha256=sha(Path(__file__)),helper_sha256=sha(ROOT/'designs/g1-guardian/blocks/g1_top/sim/run_bounded.py'),working_directory=str(Path.cwd()),pdk_commit=Path('/foss/pdks/ihp-sg13g2/COMMIT').read_text().strip(),acceptance='not assessed; inspect tool report, not exit code alone')
with (a.out/'tool.log').open('x') as log:r=run_bounded(cmd,log,a.out/'run.json',a.timeout,metadata=md,interval_s=5)
print(json.dumps({k:r.get(k) for k in ['status','returncode','wall_s','acceptance']},indent=2))
if r['status']!='completed':raise SystemExit(1)

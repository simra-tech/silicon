#!/usr/bin/env python3
"""Run the frozen three-point bias control with exact cards and a30s child bound."""
import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[2]/'g1_trip/sim'))
from run_nominal_clock_probe import run_bounded


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,required=True)
    a=p.parse_args();assert os.sched_getaffinity(0)=={6}
    contract=json.loads((a.run/'contract.json').read_text())
    assert contract['status']=='prepared only; not run' and not (a.run/'run.log').exists()
    assert sha(a.run/'probe.cir')==contract['deck_sha256']
    source=HERE.parents[1]/'reports/resume-server-20260922/gm4comp3-qualified-source.spice'
    assert sha(source)==contract['source_sha256']
    pd=Path('/foss/pdks/ihp-sg13g2');assert (pd/'COMMIT').read_text().strip()=='84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
    expected=json.loads((HERE/'psp-junction-source-equations-20260922-r1.json').read_text())['file_hashes']
    assert all(sha(pd/n)==h for n,h in expected.items())
    binding=dict(source_sha256=sha(source),deck_sha256=sha(a.run/'probe.cir'),contract_sha256=sha(a.run/'contract.json'),
                 files=expected,ngspice_version=subprocess.check_output(['ngspice','--version'],text=True),
                 runner_sha256=sha(Path(__file__)))
    (a.run/'bindings.json').write_text(json.dumps(binding,indent=2)+'\n')
    (a.run/'runner_snapshot.py').write_bytes(Path(__file__).read_bytes())
    with (a.run/'run.log').open('x') as log:
        result=run_bounded(['ngspice','-b','probe.cir'],log,a.run/'run.json',30,cwd=a.run,interval_s=.5)
    assert all(sha(pd/n)==h for n,h in expected.items()) and sha(source)==contract['source_sha256']
    print(json.dumps(result,indent=2))
    assert result['status']=='completed' and result['returncode']==0


if __name__=='__main__':main()

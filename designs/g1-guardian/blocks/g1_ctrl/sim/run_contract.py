#!/usr/bin/env python3
"""Bounded RTL evidence, preserving each invocation and its source hashes."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
BLOCKS = HERE.parents[1]
sys.path.insert(0, str(BLOCKS / 'g1_top/sim'))
from run_bounded import run_bounded, atomic_json

def bounded_timeout(value):
    try:
        seconds = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError('timeout must be an integer in 1..120 seconds') from exc
    if not 1 <= seconds <= 120:
        raise argparse.ArgumentTypeError('timeout must be in 1..120 seconds')
    return seconds

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--image-id', required=True)
    ap.add_argument('--suite', choices=['trim','digital','cdc','fault','bench'], default='trim')
    ap.add_argument('--timeout-seconds', type=bounded_timeout, default=120)
    a=ap.parse_args()
    tag=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid.uuid4().hex[:8]
    out=HERE/'campaigns'/tag
    out.mkdir(parents=True, exist_ok=False)
    build=ROOT/'build/g1_contract'/tag
    build.mkdir(parents=True, exist_ok=False)
    if a.suite=='trim':
        sources=[HERE/'tb_trim_contract.v', HERE.parent/'rtl/g1_sync2.v', HERE.parent/'rtl/g1_trip_timer.v']
    else:
        sources=[HERE/({'cdc':'tb_cdc_contract.v','fault':'tb_fault_contract.v','bench':'tb_bench_contract.v'}.get(a.suite,'tb_g1_digital.v'))]+[HERE.parent/'rtl'/p for p in ['g1_sync2.v','g1_serial.v','g1_trip_timer.v','g1_regfile.v','g1_digital_top.v']]
        sources += [BLOCKS/'g1_seu/rtl'/p for p in ['g1_tmr_reg.v','g1_seu_chain.v','g1_seu.v']]
    env=dict(os.environ)
    env['LD_LIBRARY_PATH']='/foss/tools/iverilog/lib:'+env.get('LD_LIBRARY_PATH','')
    metadata=dict(suite=a.suite, image_id=a.image_id,
        source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources+[Path(__file__)]},
        git_revision=subprocess.check_output(['git','-c','safe.directory='+str(ROOT),'rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        version=subprocess.run(['iverilog','-V'],capture_output=True,text=True).stdout.splitlines()[0],
        command_invocation=sys.argv, analog_validation='not run', physical_checks='not run')
    with (out/'compile.log').open('x') as log:
        compile_result=run_bounded(['iverilog','-g2012','-Wall','-Wno-timescale','-o',str(build/'test.vvp')]+list(map(str,sources)),log,out/'compile.json',a.timeout_seconds,env=env,metadata=metadata)
    if compile_result['status']!='completed': raise SystemExit(1)
    with (out/'simulation.log').open('x') as log:
        result=run_bounded(['vvp','-n',str(build/'test.vvp')],log,out/'simulation.json',a.timeout_seconds,cwd=build,env=env,metadata=metadata,interval_s=1)
    content=(out/'simulation.log').read_text()
    result['acceptance']='passed' if result['status']=='completed' and 'ALL TESTS PASSED' in content and 'FAIL' not in content else 'failed' if result['status']!='timeout' else 'not run to completion'
    atomic_json(out/'simulation.json',result)
    print(out.relative_to(ROOT),result['acceptance'])
    print(content[-1800:])
    if result['acceptance']!='passed': raise SystemExit(1)

if __name__=='__main__': main()

#!/usr/bin/env python3
"""Serial text-control gate before one raw geometry recovery; no extraction."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    assert not a.output.exists() and set(os.sched_getaffinity(0))=={48}
    here=Path(__file__).resolve().parent;bulk=Path(os.environ['G1_RESULTS_ROOT'])
    tasks=[('text_control',here/'probe_text_regions_r2.py',bulk/'io-text-control-20260923-r2',60),
           ('raw_geometry',here/'derive_deep_taps_r4.py',bulk/'io-deep-geometry-20260923-r4',120)]
    a.output.mkdir(parents=True)
    result=dict(status='running serial control and recovery',inputs={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__).resolve()]+[t[1] for t in tasks]},stages=[])
    try:
        for name,script,dest,bound in tasks:
            start=time.monotonic()
            with (a.output/(name+'.log')).open('x') as log:
                child=subprocess.run(['timeout','-k','5',str(bound),'python3',str(script),'--output',str(dest)],stdout=log,stderr=subprocess.STDOUT)
            result['stages'].append(dict(name=name,returncode=child.returncode,wall_s=time.monotonic()-start,watchdog_s=bound))
            assert child.returncode==0,name
        assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in result['inputs'].items())
        result['status']='passed serial text control and raw geometry; no source adoption'
    except Exception as exc:
        result.update(status='failed serial control/recovery',error=repr(exc));raise
    finally:
        (a.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
        (a.output/'source.py').write_bytes(Path(__file__).read_bytes())


if __name__=='__main__':main()

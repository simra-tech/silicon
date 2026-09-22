#!/usr/bin/env python3
"""Solve an immutable earlier raw network with the qualified refined solver."""
import argparse
import datetime
import gzip
import json
import os
from pathlib import Path
import time
import numpy as np
import extract_metal_r as worker


def main():
    ap=argparse.ArgumentParser()
    for name in ('original','preparation','control','output','resource-gate'):
        ap.add_argument('--'+name,type=Path,required=True)
    a=ap.parse_args()
    gate=json.loads(a.resource_gate.read_text())
    age=(datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(gate['utc'])).total_seconds()
    assert gate['status']=='passed' and 0<=age<1800 and len(os.sched_getaffinity(0))==1
    old=json.loads((a.original/'summary.json').read_text())
    control=json.loads(a.control.read_text())
    assert control['status']=='passed controls' and control['scenario']==old['scenario']
    assert control['worker_sha256']==worker.sha(Path(worker.__file__))
    assert old['preparation_sha256']==worker.sha(a.preparation/'summary.json')
    prep=json.loads((a.preparation/'summary.json').read_text())
    assert all(worker.sha(a.preparation/n)==h for n,h in prep['outputs'].items())
    a.output.mkdir(exist_ok=False)
    (a.output/'worker_snapshot.py').write_bytes(Path(__file__).read_bytes())
    original_bytes=(a.original/'raw_network.json.gz').read_bytes()
    (a.output/'raw_network.json.gz').write_bytes(original_bytes)
    raw=json.loads(gzip.decompress(original_bytes))
    raw['point_to_node']={int(k):v for k,v in raw['point_to_node'].items()}
    points=json.loads((a.preparation/'points.json').read_text())
    start=time.monotonic()
    receipt=dict(status='running',scenario=old['scenario'],new_native_extraction='not run',
        inputs={str(p):worker.sha(p) for p in (a.original/'summary.json',a.original/'raw_network.json.gz',
                a.preparation/'points.json',a.control,Path(worker.__file__),Path(__file__),a.resource_gate)},
        source_insertion='not run',physical_IR_qualification='not run')
    worker.dump(a.output/'summary.json',receipt)
    try:
        result,voltage=worker.solve(raw,points,55)
        worker.dump(a.output/'solution.json',result)
        np.save(str(a.output/'node_voltages.npy'),voltage)
        assert (a.output/'raw_network.json.gz').read_bytes()==original_bytes
        receipt.update(status=result['status'],original_raw_bytes_exact=True,
            maximum_absolute_delta_V=result['maximum_absolute_delta_V'],
            power_W=result['power_W'],source_power_W=result['source_power_W'])
    except Exception as error:
        receipt.update(status='failed',error=repr(error));raise
    finally:
        receipt.update(wall_s=time.monotonic()-start)
        worker.dump(a.output/'summary.json',receipt)
        print(json.dumps({k:v for k,v in receipt.items() if k!='inputs'},indent=2))


if __name__=='__main__':main()

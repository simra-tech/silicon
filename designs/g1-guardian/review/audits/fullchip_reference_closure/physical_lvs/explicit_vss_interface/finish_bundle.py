#!/usr/bin/env python3
"""One short source-only preparation/export bundle; no LVS or analog engine."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

HERE=Path(__file__).resolve().parent


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--resource-gate',type=Path,required=True)
    p.add_argument('--inventory',type=Path,required=True)
    a=p.parse_args()
    bulk=Path(os.environ['G1_RESULTS_ROOT'])
    helpers=[HERE/n for n in ('prepare_dummy_reference.py','prepare_r5.py','export_evidence.py',Path(__file__).name)]
    hashes={str(q):hashlib.sha256(q.read_bytes()).hexdigest() for q in helpers}
    commands=[
        [sys.executable,str(HERE/'prepare_dummy_reference.py'),
         '--preparation',str(bulk/'io-explicit-vss-reference-20260923-r5'),
         '--native-proof',str(bulk/'full-io-marker-dummy-proof-20260923-r1/summary.json'),
         '--output',str(bulk/'io-explicit-vss-dummy-reference-20260923-r1')],
        [sys.executable,str(HERE/'export_evidence.py'),'--resource-gate',str(a.resource_gate),
         '--inventory',str(a.inventory)]]
    for command in commands:
        subprocess.run(command,check=True)
        assert all(hashlib.sha256(Path(q).read_bytes()).hexdigest()==v for q,v in hashes.items())
    print(json.dumps(dict(status='passed source-only preparation and export',helper_hashes=hashes),indent=2))


if __name__=='__main__':main()

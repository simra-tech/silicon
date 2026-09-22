#!/usr/bin/env python3
"""Sequential opposite-rail screens inside one allocated simulation CPU."""
import argparse
import hashlib
from pathlib import Path
import subprocess
import sys

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--order',choices=['A','D','S'],required=True)
p.add_argument('--qualification',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args()
assert not a.output.exists()
runner=Path(__file__).with_name('run_power_order.py')
identity=hashlib.sha256(runner.read_bytes()).hexdigest()
a.output.mkdir(parents=True)
for name,vdd,vdda in [('weak_core',1.08,3.6),('strong_core',1.32,3.0)]:
    assert hashlib.sha256(runner.read_bytes()).hexdigest()==identity
    subprocess.run([sys.executable,str(runner),'--order',a.order,'--qualification',str(a.qualification),
                    '--output',str(a.output/name),'--vdd',str(vdd),'--vdda',str(vdda)],check=True)

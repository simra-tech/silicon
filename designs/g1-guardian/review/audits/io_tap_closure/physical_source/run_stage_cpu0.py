#!/usr/bin/env python3
"""Same fixed-30s resource gate, explicitly transferred CPU0 LVS lease only."""
import hashlib
import json
from pathlib import Path
import sys

root=next(p for p in Path(__file__).resolve().parents if (p/'flow/run.sh').is_file())
base=root/'designs/g1-guardian/blocks/g1_bgr/layout/coordinated_residual_diagnosis_20260923/run_stage_v3_30.py'
assert hashlib.sha256(base.read_bytes()).hexdigest()=='c972370ae81f9d3cb21875cdcd720ce15b6a0ca78ae20e52cf34b7deea2375c2'
text=base.read_text()
needle="exec(compile(text, str(predecessor), 'exec'), globals())"
assert text.count(needle)==1
scope={'__file__':str(base),'__name__':'prepare_transferred_CPU_lease'}
exec(compile(text.replace(needle,''),str(base),'exec'),scope)
code=scope['text']
needle="code = BASE.read_text()"
assert code.count(needle)==1
code=code.replace(needle,needle+"\nassert code.count(\"os.environ['G1_CPUSET'] == '48'\") == 1\n"
    "code=code.replace(\"os.environ['G1_CPUSET'] == '48'\", \"os.environ['G1_CPUSET'] == '0'\").replace('CPU=48','CPU=0')\n")
code=code.replace('CPU48 and combined allocation unchanged','transferred CPU0 lease; combined allocation unchanged')
scope['__name__']='__main__'
try:
    exec(compile(code,str(scope['predecessor']),'exec'),scope)
finally:
    receipt=Path(sys.argv[sys.argv.index('--receipt')+1])
    if receipt.is_dir():
        (receipt/'CPU0_successor.json').write_text(json.dumps(dict(
            CPU=0,wrapper_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            inherited_30second_runner_sha256=hashlib.sha256(base.read_bytes()).hexdigest(),
            scope='only CPU lease and accurate receipt metadata changed; resource policy unchanged'),indent=2)+'\n')

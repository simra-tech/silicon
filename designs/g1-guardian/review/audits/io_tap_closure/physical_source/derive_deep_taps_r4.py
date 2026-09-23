#!/usr/bin/env python3
"""Use separately controlled documented deep-store text conversion."""
import hashlib
import json
import os
from pathlib import Path

control=Path(os.environ['G1_RESULTS_ROOT'])/'io-text-control-20260923-r2/summary.json'
passed=json.loads(control.read_text())
assert passed['status']=='passed literal label and API diagnostic' and passed['all_original_labels_exact']
assert all(r['deep_area']==r['flat_area'] for r in passed['synthetic'])
previous=Path(__file__).resolve().with_name('derive_deep_taps_r3.py')
assert hashlib.sha256(previous.read_bytes()).hexdigest()=='20874516f2cc5d9f8dbc3e5f238bc363894c8b07d408820bb3a026aed38af00c'
text=previous.read_text()
suffix="exec(compile(code,str(scope['original']),'exec'),globals())"
assert text.count(suffix)==1
namespace={'__file__':str(Path(__file__).resolve()),'__name__':'prepare_text_conversion_control'}
exec(compile(text.replace(suffix,''),str(previous),'exec'),namespace)
code=namespace['code']
needle='        dss=pya.DeepShapeStore();dss.threads=1\n'
assert code.count(needle)==1
code=code.replace(needle,needle+"        dss.text_enlargement=1;dss.text_property_name='G1_RAW_TEXT'\n")
needle="    a.output.mkdir(parents=True);(a.output/'source.py').write_bytes(Path(__file__).read_bytes())"
assert code.count(needle)==1
code=code.replace(needle,"    inputs[str(control)]=sha(control)\n"+needle)
exec(compile(code,str(namespace['scope']['original']),'exec'),globals())

#!/usr/bin/env python3
"""Recover only saved name-control analysis; never rerun the stock command."""
import argparse
import json
from pathlib import Path
from run_name_control import strict, sha, dump, PDK

ap = argparse.ArgumentParser()
ap.add_argument('--saved', type=Path, required=True)
ap.add_argument('--output', type=Path, required=True)
a = ap.parse_args()
assert not a.output.exists()
original = json.loads((a.saved / 'summary.json').read_text())
assert original['case']['name'] == 'same_names' and original['returncode'] == 0
assert original['detail'] == "'LayoutVsSchematic' object has no attribute 'schematic'"
assert all(sha(PDK / name) == value for name, value in original['stock_rule_hashes'].items())
path, = list((a.saved / 'reports').rglob('*.lvsdb'))
report = strict(path)
assert report['status'] == 'passed'
for side in ('layout', 'reference'):
    assert report[side]['NAME_CONTROL_TOP']['expanded_devices'] == 4
    assert len(report[side]['NAME_CONTROL_TOP']['pins']) == 4
logs = '\n'.join(p.read_text() for p in (a.saved / 'reports').rglob('*.log'))
assert 'Congratulations! Netlists match.' in logs and "Netlists don't match" not in logs
a.output.mkdir(parents=True)
(a.output / 'worker_snapshot.py').write_bytes(Path(__file__).read_bytes())
result = dict(status='passed saved same-name stock control; original analysis failure retained',
              original_summary_sha256=sha(a.saved / 'summary.json'), report=report,
              API_correction='LayoutVsSchematic.reference(), not schematic()',
              new_stock_run='not run', physical_extraction='not run', fullchip_LVS='not run',
              script_sha256=sha(Path(__file__)))
dump(a.output / 'summary.json', result)
print(json.dumps(result, indent=2))

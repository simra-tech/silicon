"""One bounded, source-frozen final VREF/OSC diagnostic; no automatic scaling."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

root = Path.cwd()
audit = root/'designs/g1-guardian/review/audits'
p = argparse.ArgumentParser()
p.add_argument('--output', type=Path, required=True)
p.add_argument('--context-um', type=int, choices=(12, 24, 48), required=True)
a = p.parse_args()
assert not a.output.exists() and len(os.sched_getaffinity(0)) == 1
a.output.mkdir(parents=True)
paths = [audit/'final_route_context'/n for n in ('prepare_clip.py', 'route_inventory.py', 'audit_geometry.py')]
paths += [audit/n for n in ('run_fill_clip_pex.py', 'export_clip_lvsdb.lvs', 'analyze_interface_clip.py', 'clip_cap_graph.py', 'check_fill_clip_ac.py')]
paths += [root/'designs/g1-guardian/blocks/g1_top/sim/run_bounded.py']
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
bound = {str(p): sha(p) for p in paths}
commands = [
 [sys.executable, str(audit/'final_route_context/prepare_clip.py'),
  '--inventory', '@RESULTS@/final-route-inventory-20260923-r2/analysis.json',
  '--geometry', '@RESULTS@/final-route-geometry-20260923-r1/analysis.json',
  '--candidate', '@RESULTS@/final-native-poly-fill-20260923-r2',
  '--victim', 'i_core.vref', '--neighbor', 'i_core.osc_clk',
  '--victim-segment', '8', '--neighbor-segment', '5',
  '--context-um', str(a.context_um), '--output', str(a.output/'clip')],
 [sys.executable, str(audit/'run_fill_clip_pex.py'), '--clip', str(a.output/'clip'), '--output', str(a.output/'pex')],
 [sys.executable, str(audit/'analyze_interface_clip.py'), '--input', str(a.output/'pex'), '--output', str(a.output/'analysis')],
 [sys.executable, str(audit/'check_fill_clip_ac.py'), str(a.output/'analysis')],
]
result = dict(status='running', context_um=a.context_um, sources=bound, steps=[],
    scope='One final VREF/OSC midpoint20um metal-only clip with explicit grounded-context boundary; no full-route scaling/adoption.',
    not_run=['24-to48um context convergence', 'longitudinal/end context', 'actual-source electrical acceptance', 'fullchip PEX'])
(a.output/'runner.py').write_bytes(Path(__file__).read_bytes())
try:
    for index, command in enumerate(commands):
        assert all(sha(Path(name)) == value for name, value in bound.items())
        started = time.monotonic()
        with (a.output/('step%d.log' % index)).open('x') as log:
            completed = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
        result['steps'].append(dict(command=command, returncode=completed.returncode, wall_s=time.monotonic()-started))
        (a.output/'manifest.json').write_text(json.dumps(result, indent=2)+'\n')
        assert completed.returncode == 0, ('stage', index)
        if index == 1:
            extraction = json.loads((a.output/'pex/manifest.json').read_text())
            assert len(extraction) == 2
            assert all(r.get('extract_status') == r.get('kpex_status') == 'completed' and
                       r.get('extract_returncode') == r.get('kpex_returncode') == 0 for r in extraction)
        if index == 3:
            checks = json.loads((a.output/'analysis/ac_checks.json').read_text())
            expected = {f'{v}_{m}_{d}.cir' for v in ('no_fill', 'actual_fill')
                        for m in ('grounded', 'floating') for d in ('P', 'N')}
            assert len(checks) == 8 and {r['deck'] for r in checks} == expected
            assert all(r['status'] == 'passed' and r['returncode'] == 0 for r in checks)
    assert all(sha(Path(name)) == value for name, value in bound.items())
    result['status'] = 'passed local paired extraction and independent capacitor-network AC check'
except Exception as error:
    result.update(status='failed final local coupling diagnostic', error=repr(error))
    raise
finally:
    (a.output/'manifest.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))

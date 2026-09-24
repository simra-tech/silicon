#!/usr/bin/env python3
"""Bounded, unchanged stock checks on an explicitly hashed scratch route candidate."""
import argparse
import collections
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
import pya

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'designs/g1-guardian/blocks/g1_top/sim'))
from run_bounded import run_bounded

PDK = Path('/foss/pdks/ihp-sg13g2')
PIN = '84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--candidate', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--check', choices=['drc_recommended', 'antenna', 'density'], required=True)
parser.add_argument('--timeout', type=float, default=900)
a = parser.parse_args()
assert a.timeout > 0 and a.timeout <= 3600
assert pya.__version__ == '0.30.9', pya.__version__
assert (PDK / 'COMMIT').read_text().strip() == PIN
assert len(os.sched_getaffinity(0)) == 1, 'Initial physical allocation is exactly one CPU'
candidate = a.candidate.resolve()
candidate_manifest = json.loads(candidate.with_name('manifest.json').read_text())
assert sha(candidate) == candidate_manifest['candidate_sha256']
a.output.mkdir(parents=True, exist_ok=False)
out = a.output.resolve()
shutil.copyfile(__file__, out / 'runner.py')
drc_root = PDK / 'libs.tech/klayout/tech/drc'
deck = drc_root / {'drc_recommended': 'ihp-sg13g2.drc',
                   'antenna': 'rule_decks/antenna.drc',
                   'density': 'rule_decks/density.drc'}[a.check]
report = out / (a.check + '.lyrdb')
cmd = ['klayout', '-b', '-zz', '-r', str(deck), '-rd', 'input=' + str(candidate),
       '-rd', 'topcell=g1_chip_top', '-rd', 'report=' + str(report), '-rd', 'threads=1']
if a.check == 'drc_recommended':
    cmd += ['-rd', 'run_mode=deep']
provenance = {'candidate_sha256': sha(candidate), 'pdk_commit': PIN,
              'klayout_python_version': pya.__version__,
              'klayout_cli_version': subprocess.check_output(['klayout', '-v'], text=True).strip(),
              'cpu_affinity': sorted(os.sched_getaffinity(0)), 'command': cmd,
              'deck_sha256': sha(deck), 'runner_sha256': sha(Path(__file__)),
              'stock_rule_hashes': {str(p.relative_to(drc_root)): sha(p)
                                    for p in sorted(drc_root.rglob('*'))
                                    if p.is_file() and p.suffix in ('.drc', '.json')}}
(out / 'provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')
with (out / 'tool.log').open('x') as stream:
    state = run_bounded(cmd, stream, out / 'run.json', a.timeout, cwd=ROOT,
                        env=dict(os.environ, OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1'),
                        metadata={'candidate_sha256': sha(candidate), 'check': a.check}, interval_s=1)
result = {'check': a.check, 'status': 'failed', 'watchdog_status': state['status'],
          'returncode': state['returncode'], 'wall_s': state['wall_s']}
if state['status'] in ('timeout', 'interrupted', 'launch_failed'):
    result['status'] = 'not run'
    result['completion'] = 'Check did not run to a valid final endpoint; see watchdog status'
elif state['returncode'] == 0 and report.exists():
    categories = collections.Counter(item.findtext('category').strip("'")
                                     for item in ET.parse(report).findall('.//items/item'))
    result.update(status='failed' if categories else 'passed', markers=sum(categories.values()),
                  categories=dict(categories), report_sha256=sha(report))
(out / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
sys.exit(0 if result['status'] == 'passed' else 1)

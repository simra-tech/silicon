#!/usr/bin/env python3
"""Assess only a SPICE title difference after preserving strict host parity failure.

Every executable deck byte and every waveform byte must match. Only line1,
SPICE's title line, is considered separately; arbitrary comments are not stripped.
"""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--reference', required=True)
parser.add_argument('--candidate', required=True)
args = parser.parse_args()
assert all(Path(name).name == name for name in [args.reference, args.candidate])
assert args.reference != args.candidate
directories = [HERE/'runs'/name for name in [args.reference, args.candidate]]
strict_path = directories[1]/'host_parity.json'
strict = json.loads(strict_path.read_text())
checks = dict(strict_record_preserved=strict['status']=='failed',
              strict_top_level_checks=all(strict['checks'].values()),
              exactly_four_cases=len(strict['cases'])==4,
              strict_manifests_authentic=[sha(d/'manifest.json') for d in directories]==strict['manifest_sha256'])
cases = []
for case in strict['cases']:
    decks = [d/(case['name']+'.cir') for d in directories]
    waves = [d/(case['name']+'.dat') for d in directories]
    content = [p.read_bytes().splitlines(keepends=True) for p in decks]
    item = dict(name=case['name'], titles=[lines[0].decode().strip() for lines in content], checks={})
    item['checks']['deck_hashes_authentic'] = [sha(p) for p in decks]==case['cir_sha256']
    item['checks']['wave_hashes_authentic'] = [sha(p) for p in waves]==case['dat_sha256']
    item['checks']['every_executable_deck_byte_identical'] = b''.join(content[0][1:])==b''.join(content[1][1:])
    item['checks']['explicit_title_comments'] = all(lines[0].startswith(b'*') for lines in content)
    item['checks']['only_strict_deck_identity_failed'] = {k for k,v in case['checks'].items() if not v}=={'deck_sha256','cir_byte_identical'}
    cases.append(item)
checks['all_case_checks'] = all(all(case['checks'].values()) for case in cases)
report = dict(status='passed' if all(checks.values()) else 'failed', checks=checks, cases=cases,
              strict_result_sha256=sha(strict_path), checker_sha256=sha(Path(__file__)),
              scope='SPICE executable input identity and exact sampled parameters/full saved vectors for one same-seed four-temperature replay. Original full-deck identity failure is retained; title metadata differs. No numerical tolerance or endpoint relaxation.')
with (directories[1]/'host_executable_deck_parity.json').open('x') as output:
    output.write(json.dumps(report, indent=2)+'\n')
print(json.dumps(report, indent=2))
raise SystemExit(0 if report['status']=='passed' else 1)

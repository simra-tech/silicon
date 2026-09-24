#!/usr/bin/env python3
"""Saved-only exact-input audit of one versioned OSC recovery canary."""
import argparse
import json
import math
from pathlib import Path

import audit_newpex_population as base

HERE = Path(__file__).resolve().parent
RUNNER = HERE/'run_mc_newpex_population_recovery_r1.py'
QUAL = HERE/'runs/osc_r095_newpex_qual_20260924_r1'
SOURCE_NAMES = ('baseline.spice', 'mismatch.spice', 'disabled.spice', '.spiceinit')


def audit(seed):
    assert 63101 <= seed <= 63109
    run_id = 'osc_r095_newpex_nominal100_recovery1_20260924_r1_s%d' % seed
    folder = HERE/'runs'/run_id
    qpath = QUAL/'manifest.json'
    qanalysis = QUAL/'analysis.json'
    q, qa = json.loads(qpath.read_text()), json.loads(qanalysis.read_text())
    assert qa['status'] == 'passed' and qa['manifest_sha256'] == base.sha(qpath)
    path = folder/'manifest.json'
    if not path.is_file():
        return {'status': 'not run', 'seed': seed, 'run_id': run_id}
    m = json.loads(path.read_text())
    rows = m.get('cases', [])
    expected = [0, 15]
    checks = {
        'runner': m['source_sha256'].get('run_mc_newpex_population_recovery_r1.py') == base.sha(RUNNER) == base.sha(folder/'run_mc_newpex_population_recovery_r1.py'),
        'source': all(m['source_sha256'].get(name) == q['source_sha256'][name] and base.sha(folder/name) == q['source_sha256'][name] for name in SOURCE_NAMES),
        'environment': all(m[key] == q[key] for key in ('image_id', 'ngspice', 'pdk_commit', 'model_sha256', 'fingerprint_parameters')),
        'expected_cases': m.get('expected_cases') == ['s%d_c%d' % (seed, code) for code in expected],
        'numeric': len(rows) == 2 and [r['code'] for r in rows] == expected and all(r['status'] == 'passed' and r['solver_exit'] == 0 and not r['timed_out'] for r in rows),
        'conditions': all((r['seed'], r['mos'], r['res'], r['cap'], r['vdd'], r['temperature_C'], r['mm'], r['op_only']) == (seed, 'tt', 'typ', 'typ', 1.2, 27, True, False) for r in rows),
        'decks': all((folder/(r['name']+'.cir')).is_file() and (folder/(r['name']+'.cir')).read_text() == base.expected_deck(r, m['fingerprint_parameters']) and base.sha(folder/(r['name']+'.cir')) == r['deck_sha256'] for r in rows),
        'waves': all(base.wave_complete(folder/(r['name']+'.dat')) for r in rows),
        'logs': all(base.log_matches(folder/(r['name']+'.log'), folder/(r['name']+'.stderr'), r) for r in rows),
    }
    fp = [r['fingerprints'] for r in rows]
    checks['all_269_parameters_frozen'] = len(m['fingerprint_parameters']) == 269 and len(fp) == 2 and all(len(f) == 538 and f[:269] == fp[0][:269] == f[269:] and all(math.isfinite(float(v)) for v in f) for f in fp)
    values = [r['measurements'].get('fmhz') for r in rows]
    checks['frequency_finite'] = len(values) == 2 and all(isinstance(v, (float, int)) and math.isfinite(v) and v > 0 for v in values)
    return {'status': 'passed canary numerical/source audit; no population credit' if all(checks.values()) else 'failed',
            'seed': seed, 'run_id': run_id, 'checks': checks,
            'manifest_sha256': base.sha(path), 'qualification_manifest_sha256': base.sha(qpath),
            'qualification_analysis_sha256': base.sha(qanalysis),
            'frequency_MHz': values if checks['frequency_finite'] else None,
            'brackets_10MHz': min(values) <= 10 <= max(values) if checks['frequency_finite'] else None,
            'waveform_sha256': {r['name']: base.sha(folder/(r['name']+'.dat')) for r in rows if (folder/(r['name']+'.dat')).is_file()},
            'scope': 'One exact fixed seed on newly extracted physical CPEX; old pre-container wrapper failure retained. No full population, geometry integration, actual receiver or silicon-yield credit.'}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seed', type=int, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    if args.output.exists():
        raise ValueError('Refusing overwrite')
    result = audit(args.seed)
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()

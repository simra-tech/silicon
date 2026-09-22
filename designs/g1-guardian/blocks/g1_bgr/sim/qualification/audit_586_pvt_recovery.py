#!/usr/bin/env python3
"""Explicit coverage join; never rewrite the original81-attempt failure audit."""
import argparse
import json
from pathlib import Path
import re
import numpy as np
from run_586_pvt import sha

HERE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    oldaudit = HERE/'bgr586-pvt81-audit-20260922.json'
    original = json.loads(oldaudit.read_text())
    assert original['completed_conditions'] == 80 and original['numerically_failed_conditions'] == 1
    failure, = [r for r in original['records'] if r['status'] == 'failed']
    old = HERE/failure['run']
    new = HERE/'runs/bgr586-pvt-typ-ff-typ-v30-recovery240s-20260922-a'
    row, = json.loads((new/'summary.json').read_text())
    prov = json.loads((new/'provenance.json').read_text())
    assert row['status'] == 'passed exact-input recovery' and row['original_failure_retained']
    assert all(sha(old/name) == digest for name, digest in prov['original_receipts_sha256'].items())
    for name in ['nominal.cir', 'pex_nominal.spice', '.spiceinit']:
        assert (new/name).read_bytes() == (old/name).read_bytes()
    assert prov['runtime'] == original['runtime_identity'] and prov['source_sha256'] == original['source_sha256']
    before = re.findall(r'^(@[^\s]+)\s*=\s*(\S+)', (old/'run.log').read_text(), re.M)
    after = re.findall(r'^(@[^\s]+)\s*=\s*(\S+)', (new/'run.log').read_text(), re.M)
    assert len(before) == 2842 and after == before*2
    assert [list(p) for p in before] == row['parameters_before'] == row['parameters_after']
    data = np.loadtxt(str(new/'nominal.dat'), skiprows=1)
    assert data.shape == (34, 12) and np.isfinite(data).all() and np.array_equal(data[:, 0], np.arange(-40, 126, 5))
    tc = float(np.ptp(data[:, 1])/data[13, 1]/165*1e6)
    assert tc == row['tc_ppm_C'] and row['tc_status'] == ('passed' if tc <= 50 else 'failed')
    assert sha(new/'nominal.dat') == row['waveform_sha256']
    result = {'status': 'passed explicit81condition coverage audit; original120s failure retained',
              'original_audit_sha256': sha(oldaudit), 'original_attempts_completed': 80, 'original_attempts_failed': 1,
              'recovery_attempts': 1, 'recovery_completed': 1, 'covered_distinct_grid_conditions': 81,
              'completed_tc_failures': original['tc_failed_completed_conditions']+int(tc > 50),
              'maximum_completed_tc_ppm_C': max(original['maximum_completed_tc_ppm_C'], tc),
              'explicit_recovery_mapping': {'original_run': failure['run'], 'recovery_run': str(new.relative_to(HERE)), 'condition': failure['condition'],
                                           'summary_sha256': sha(new/'summary.json'), 'provenance_sha256': sha(new/'provenance.json'), 'wave_sha256': sha(new/'nominal.dat'),
                                           'all2842_original_before_new_before_after_exact': True, 'tc_ppm_C': tc,
                                           'wave_prefix_parity': 'not run; failed original never exported a waveform'},
              'scope': 'All81fixedPVTconditions numericallycovered via80originalcomplete+1exact-input240s recovery. Original120s timeout remainsfailed. Unchanged50ppm/C criterion; not mismatch/yield or futurephysicalCC coverage.'}
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Rehash candidate inputs and reproduce TC for every prespecified BGR sample."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-id', action='append', required=True)
    parser.add_argument('--samples', type=int, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    qfolder = HERE/'runs/bgr_selective_loop16_qualify_20260922_r1'
    qual = json.loads((qfolder/'manifest.json').read_text())
    analysis = json.loads((qfolder/'analysis.json').read_text())
    assert analysis['qualification_status'] == 'passed' and analysis['manifest_sha256'] == sha(qfolder/'manifest.json')
    checks, samples, fingerprints = {}, [], []
    for run_id in args.run_id:
        folder = HERE/'runs'/run_id
        manifest = json.loads((folder/'manifest.json').read_text())
        checks[run_id] = {key: manifest[key] == qual[key] for key in ['image_id', 'pdk_commit', 'ngspice', 'pex_sha256', 'runner_sha256', 'model_sha256', 'osdi_sha256', 'solver', 'r4_default_V']}
        checks[run_id]['sources_match'] = all(sha(folder/name) == sha(qfolder/name) for name in ['pex_nominal.spice', 'pex_mm.spice', '.spiceinit', 'run_campaign.py'])
        for row in manifest['cases']:
            n = len(row['fingerprint_parameters'])
            frozen = n == 1877 and row['fingerprint_parameters'] == qual['cases'][0]['fingerprint_parameters'] and len(row['fingerprints']) == 2*n and row['fingerprints'][:n] == row['fingerprints'][n:]
            fingerprints.append(tuple(row['fingerprints'][:n]))
            datapath = folder/(row['name']+'.dat')
            data = np.loadtxt(str(datapath), skiprows=1)
            complete = data.shape == (34, 12) and np.isfinite(data).all() and np.array_equal(data[:, 0], np.arange(-40, 126, 5))
            tc = float((data[:, 1].max()-data[:, 1].min())/np.interp(25, data[:, 0], data[:, 1])/165*1e6)
            case_checks = {'numerical_status': row['status'] == 'passed' and row['solver_exit'] == 0 and not row['timed_out'],
                           'full_sample_frozen': frozen, 'full_temperature_waveform': bool(complete),
                           'deck_sha256': sha(folder/(row['name']+'.cir')) == row['deck_sha256'],
                           'recomputed_tc': tc == row['tc_ppm_C']}
            samples.append({'run_id': run_id, 'seed': row['seed'], 'checks': case_checks,
                            'tc_ppm_C': tc, 'tc_status': 'passed' if tc <= 50 else 'failed',
                            'waveform_sha256': sha(datapath), 'wall_seconds': row['wall_seconds']})
    seeds = sorted(row['seed'] for row in samples)
    expected = list(range(43001, 43001+args.samples))
    global_checks = {'input_identity': all(all(value.values()) for value in checks.values()),
                     'exact_expected_seeds': seeds == expected, 'independent_fingerprints': len(set(fingerprints)) == args.samples,
                     'all_samples_qualified': all(all(row['checks'].values()) for row in samples)}
    result = {'qualification_manifest_sha256': sha(qfolder/'manifest.json'), 'source_checks': checks,
              'checks': global_checks, 'status': 'passed' if all(global_checks.values()) else 'failed',
              'sample_count': len(samples), 'tc_failures': sum(row['tc_status'] == 'failed' for row in samples),
              'samples': samples, 'scope': 'Fixed-netlist independent simulated local-mismatch samples. No paired-baseline claim, spatial-correlation qualification, new geometry/PEX or adoption.'}
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({key: value for key, value in result.items() if key != 'samples'}, indent=2))
    raise SystemExit(0 if result['status'] == 'passed' else 1)


if __name__ == '__main__':
    main()

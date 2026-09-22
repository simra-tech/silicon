#!/usr/bin/env python3
"""Reviewed two-seed/four-variant BGR counterfactual, exact non-target draw gates."""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
PDK = Path('/foss/pdks/ihp-sg13g2')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fingerprint(text):
    return dict(re.findall(r'(?m)^(@[^\s]+)\s*=\s*([-+0-9.eE]+)', text))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--image-id', required=True)
    args = parser.parse_args()
    output = HERE/'runs'/args.run_id
    output.mkdir(exist_ok=False)
    shutil.copy(__file__, output/Path(__file__).name)
    reference = HERE/'runs/bgr_selective_loop16_mc20_20260922_r1'
    for name in ['.spiceinit', 'pex_mm.spice', 'pex_nominal.spice']:
        shutil.copy(reference/name, output/name)
    manifest = {'command': sys.argv, 'image_id': args.image_id,
                'ngspice': subprocess.check_output(['ngspice', '--version'], universal_newlines=True),
                'pdk_commit': (PDK/'COMMIT').read_text().strip(),
                'model_sha256': {str(path.relative_to(PDK)): sha(path) for path in sorted((PDK/'libs.tech/ngspice/models').glob('*.lib'))},
                'osdi_sha256': {str(path.relative_to(PDK)): sha(path) for path in sorted((PDK/'libs.tech/ngspice/osdi').glob('*.osdi'))},
                'source_sha256': {name: sha(output/name) for name in ['.spiceinit', 'pex_mm.spice', 'pex_nominal.spice']},
                'scope': 'Diagnostic only, no geometry/model-card/distribution adoption. Qref and PTAT Q1/Q2 realized area overrides to exactly1, preserving all other1877parameter entries. PTAT intervention removes area-ratio and within-group variation, not a pure ratio-only derivative.',
                'cases': [], 'expected_cases': ['s%d_%s'%(seed, variant) for seed in [43047, 43001] for variant in ['all_on', 'qref_nominal', 'ptat_hbt_nominal', 'both_nominal']]}
    save = lambda: (output/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    save()
    for seed in [43047, 43001]:
        folder = HERE/'runs'/('bgr_selective_loop16_mc20_20260922_r1' if seed == 43001 else 'bgr_selective_loop16_mc80_20260922_r1')
        original = json.loads((folder/'manifest.json').read_text())
        assert all(manifest[key] == original[key] for key in ['image_id', 'ngspice', 'pdk_commit', 'model_sha256', 'osdi_sha256'])
        assert all(sha(folder/name) == digest for name, digest in manifest['source_sha256'].items())
        old = next(row for row in original['cases'] if row['seed'] == seed)
        queries = old['fingerprint_parameters']
        assert old['status'] == 'passed' and len(queries) == 1877 and old['fingerprints'][:1877] == old['fingerprints'][1877:]
        expected = dict(zip(queries, old['fingerprints'][:1877]))
        qref = {key for key in queries if key == '@q.xbgr.xq60.qnpn13g2[area]'}
        ptat = {key for key in queries if re.search(r'\.xq(?:56|68|69|70|71|72|73|74|76)(?:_u\d+)?\.', key) and key.endswith('[area]')}
        assert len(qref) == 1 and len(ptat) == 144
        deckpath = folder/(old['name']+'.cir')
        assert sha(deckpath) == old['deck_sha256']
        original_deck = deckpath.read_text()
        before, after = original_deck.split('dc temp -40 125 5\n')
        dump = ''.join('print '+query+'\n' for query in queries)
        for variant, targets in [('all_on', set()), ('qref_nominal', qref), ('ptat_hbt_nominal', ptat), ('both_nominal', qref | ptat)]:
            name = 's%d_%s'%(seed, variant)
            deck = before.replace('\nop\n', '\nop\necho FINGERPRINT_BEFORE\n', 1)
            if targets:
                deck += ''.join('alter '+query+' = 1\n' for query in sorted(targets))+'op\n'
            deck += 'echo FINGERPRINT_AFTER_ALTER\n'+dump+'dc temp -40 125 5\necho FINGERPRINT_AFTER_SWEEP\n'+after
            deck = deck.replace('wrdata '+old['name']+'.dat', 'wrdata '+name+'.dat')
            (output/(name+'.cir')).write_text(deck)
            start = time.monotonic()
            with (output/(name+'.log')).open('w') as log, (output/(name+'.stderr')).open('w') as error:
                try:
                    rc = subprocess.run(['ngspice', '-b', name+'.cir'], cwd=output, stdout=log, stderr=error, timeout=120).returncode
                    timed = False
                except subprocess.TimeoutExpired:
                    rc, timed = None, True
            row = {'seed': seed, 'variant': variant, 'name': name, 'intervened_parameters': sorted(targets),
                   'original_manifest_sha256': sha(folder/'manifest.json'), 'original_deck_sha256': sha(deckpath),
                   'deck_sha256': sha(output/(name+'.cir')), 'original_waveform_sha256': sha(folder/(old['name']+'.dat')),
                   'solver_exit': rc, 'timed_out': timed, 'watchdog_seconds': 120, 'wall_seconds': time.monotonic()-start,
                   'status': 'not run' if timed else 'failed'}
            log = (output/(name+'.log')).read_text()
            errors = (output/(name+'.stderr')).read_text()
            first = fingerprint(log.split('FINGERPRINT_BEFORE')[-1].split('FINGERPRINT_AFTER_ALTER')[0])
            second = fingerprint(log.split('FINGERPRINT_AFTER_ALTER')[-1].split('FINGERPRINT_AFTER_SWEEP')[0])
            final = fingerprint(log.split('FINGERPRINT_AFTER_SWEEP')[-1])
            row['fingerprints'] = {'before': first, 'after_alter': second, 'after_sweep': final}
            checks = {'before_exact_archived_sample': first == expected,
                      'complete_parameter_sets': set(first) == set(second) == set(final) == set(expected),
                      'non_target_exact': all(first.get(key) == second.get(key) == final.get(key) for key in expected if key not in targets),
                      'targets_exactly_nominal': all(float(second.get(key, 'nan')) == float(final.get(key, 'nan')) == 1 for key in targets)}
            try:
                path = output/(name+'.dat')
                data = np.loadtxt(str(path), skiprows=1)
                assert data.shape == (34, 12) and np.isfinite(data).all() and np.array_equal(data[:, 0], np.arange(-40, 126, 5))
                assert rc == 0 and not timed and not re.search(r'(?im)^Error|no such parameter|Timestep too small|analysis aborted', log+'\n'+errors)
                row.update(status='passed', waveform_sha256=sha(path), vref25_V=float(data[13, 1]),
                           iptat25_A=float(data[13, 2]), supply_current25_A=float(-data[13, 3]),
                           tc_ppm_C=float((data[:, 1].max()-data[:, 1].min())/data[13, 1]/165*1e6),
                           signed_endpoint_slope_ppm_C=float((data[-1, 1]-data[0, 1])/data[13, 1]/165*1e6))
                if variant == 'all_on':
                    checks['original_waveform_byte_identical'] = sha(path) == row['original_waveform_sha256']
            except (OSError, ValueError, AssertionError, IndexError) as error:
                row['analysis_error'] = str(error)
            row['checks'] = checks
            row['diagnostic_gate_status'] = 'passed' if row['status'] == 'passed' and all(checks.values()) else 'failed'
            manifest['cases'].append(row)
            manifest['not_run_cases'] = [name for name in manifest['expected_cases'] if name not in [case['name'] for case in manifest['cases']]]
            save()
            print(json.dumps({key: value for key, value in row.items() if key not in ['fingerprints', 'intervened_parameters']}), flush=True)
            if row['diagnostic_gate_status'] != 'passed':
                manifest['failure_stop'] = 'Exact diagnostic gate failed; remaining variants not run.'
                save()
                raise SystemExit(1)


if __name__ == '__main__':
    main()

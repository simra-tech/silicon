#!/usr/bin/env python3
"""Strict output-save-only fixture and waveform comparison; no limit relaxation."""
import argparse
import hashlib
import json
import math
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def strip_save(text):
    return '\n'.join(line for line in text.splitlines() if not line.strip().lower().startswith('save '))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--reference', type=Path, required=True)
    ap.add_argument('--candidate', type=Path, required=True)
    ap.add_argument('--stem', required=True)
    args = ap.parse_args()
    assert Path(args.stem).name == args.stem
    directories = [args.reference, args.candidate]
    manifests = [json.loads((p/'manifest.json').read_text()) for p in directories]
    old, new = manifests
    checks = {key: old[key] == new[key] for key in ['image_id', 'pdk_commit', 'ngspice', 'model_sha256']}
    source_names = sorted(p.name for p in directories[0].iterdir()
                          if p.suffix in ['.spice', '.spef'] or p.name == '.spiceinit')
    checks['sources_present'] = bool(source_names)
    source_hashes = {}
    for name in source_names:
        hashes = [sha(d/name) for d in directories]
        source_hashes[name] = hashes
        checks['source_'+name] = hashes[0] == hashes[1]
    if args.stem == 'receiver':
        checks['numerically_complete'] = all(m['status'] == 'passed' and m['solver_exit'] == 0
                                             and not m['timed_out'] for m in manifests)
        checks['receiver_function'] = all(m['receiver_function_status'] == 'passed' for m in manifests)
    else:
        assert args.stem.startswith('rms_') and args.stem.endswith('mV')
        amplitude = float(args.stem[4:-2])
        rows = [next(c for c in m['cases'] if c['requested_rms_mV'] == amplitude) for m in manifests]
        checks['numerically_complete'] = all(c['status'] == 'passed' and c['solver_exit'] == 0
                                             and not c['timed_out'] for c in rows)
        checks['same_pwl'] = sha(directories[0]/'normalized_pwl.json') == sha(directories[1]/'normalized_pwl.json')
    decks = [(d/(args.stem+'.cir')).read_text() for d in directories]
    checks['deck_only_save_change'] = strip_save(decks[0]) == strip_save(decks[1])
    saves = [line.strip().split()[1:] for line in decks[1].splitlines() if line.strip().lower().startswith('save ')]
    exports = [line.strip().split()[2:] for line in decks[1].splitlines() if line.strip().lower().startswith('wrdata ')]
    checks['only_exported_vectors_saved'] = len(saves) == len(exports) == 1 and saves[0] == exports[0]
    data = [d/(args.stem+'.dat') for d in directories]
    hashes = [sha(p) for p in data]
    checks['full_waveform_byte_identical'] = hashes[0] == hashes[1]
    final_rows = []
    row_counts = []
    for path in data:
        count = 0
        with path.open() as stream:
            next(stream)
            for line in stream:
                if not line.strip():
                    continue
                row = list(map(float, line.split()))
                assert all(map(math.isfinite, row))
                count += 1
        assert count
        final_rows.append(row)
        row_counts.append(count)
    checks['same_final_row'] = final_rows[0] == final_rows[1]
    checks['same_row_count'] = row_counts[0] == row_counts[1]
    result = {'reference_run': directories[0].name, 'candidate_run': directories[1].name,
              'stem': args.stem, 'source_sha256': source_hashes, 'waveform_sha256': hashes,
              'row_counts': row_counts, 'checks': checks,
              'status': 'passed' if all(checks.values()) else 'failed',
              'scope': 'Save-policy-only deck comparison plus exact full exported waveforms on this fixture.'}
    with (directories[1]/'output_save_parity.json').open('x') as output:
        output.write(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result['status'] == 'passed' else 1)


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Characterize a qualified differential leaf without requiring valid loop probes."""
import argparse
import json
from pathlib import Path
import numpy as np
from analyze_loaded_followthrough import leaf, tests
from analyze_loaded_ac_audit import crossings
from run_loaded_noise_audit import sha, table


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--leaf', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    control = tests()
    record, contract = leaf(args.leaf)
    assert record['kind'] == 'adverse' and record['mode'] == 'differential'
    assert not args.output.exists()
    wave = table(args.leaf/'ac.dat', ['frequency', 'ac_re', 'ac_im'])
    assert wave.shape == (901, 3)
    mag = abs(wave[:, 1]+1j*wave[:, 2])
    assert np.all(mag > 0)
    db = 20*np.log10(mag)
    points = crossings(wave[:, 0], db, db[0]-3.010299956639812)
    result = dict(status='completed qualified differential-only analysis',
        case=record['case'], gain_1Hz_V_per_V=float(mag[0]),
        gain_status='passed' if 19.9 <= mag[0] <= 20.1 else 'failed',
        halfpower_downcrossings_Hz=[p[2] for p in points],
        bandwidth_status='passed' if points and points[0][2] >= 2e6 else 'failed',
        phase_margin='not run: this analysis uses no loop probe',
        gain_margin='not run: this analysis uses no loop probe',
        controls=control, source_hashes=contract['source_hashes'],
        bindings={name:sha(args.leaf/name) for name in
            ['summary.json', 'contract.json', 'probe.cir', 'provenance.json',
             'run.log', 'ac.dat', 'input_basis.dat']},
        scope='One frozen DC operating point, one source-bound differential leaf. No inference from unqualified loop data or physical PEX.')
    args.output.mkdir(parents=True)
    (args.output/'summary.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()

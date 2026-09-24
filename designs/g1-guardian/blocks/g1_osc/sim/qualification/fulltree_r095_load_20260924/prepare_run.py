#!/usr/bin/env python3
"""Prepare an exact saved oscillator load fixture; does not run a solver."""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
CASES = {
    'nominal_code0': ('nominal', 'code0.cir'),
    'nominal_code8': ('nominal', 'code8.cir'),
    'slowhot_code0': ('slowhot', 'code0.cir'),
    'slowhot_code15': ('slowhot', 'code15.cir'),
}


def prepare(case, destination):
    inventory = json.loads((HERE / 'INPUTS.json').read_text())
    for item in inventory['files']:
        source = HERE / item['path']
        assert source.is_file() and not source.is_symlink()
        assert hashlib.sha256(source.read_bytes()).hexdigest() == item['sha256']
    corner, deck = CASES[case]
    copies = {
        'osc.spice': HERE / 'common/osc.spice',
        'stdcells.spice': HERE / 'common/stdcells.spice',
        '.spiceinit': HERE / 'common/.spiceinit',
        'clock_load.spice': HERE / corner / 'clock_load.spice',
        'receiver.cir': HERE / corner / deck,
    }
    destination.mkdir(parents=True, exist_ok=False)
    for name, source in copies.items():
        data = source.read_bytes()
        with (destination / name).open('xb') as stream:
            stream.write(data)
    return {'status': 'prepared exact inputs; solver not run', 'case': case,
            'inputs_sha256': {name: hashlib.sha256(source.read_bytes()).hexdigest()
                              for name, source in copies.items()}}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('case', choices=sorted(CASES))
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    print(json.dumps(prepare(args.case, args.destination), indent=2))

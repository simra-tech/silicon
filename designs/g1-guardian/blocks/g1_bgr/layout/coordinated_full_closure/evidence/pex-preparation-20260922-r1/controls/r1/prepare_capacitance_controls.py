#!/usr/bin/env python3
"""Prepare exact oldCC reconstruction/cap-free controls without new extraction."""
import argparse
import hashlib
import json
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    here = Path(__file__).resolve().parent
    source = here.parent.parent / 'sim/qualification/candidates/bgr_loop24_qref4_r253p465_hv06/bgr_loop24_qref4_r253p465_hv06.spice'
    prior = here.parent.parent / 'sim/postlayout/g1_bgr_pex.spice'
    assert sha(source) == '586ffb58b6af31c77a2e7cbcb83b173ffa4713ec62401da30901c5a7e606283b'
    assert sha(prior) == '72417e072003d2ce28a108c47ef6ac86927ce6c6f89f3a614f360165a31c9d77'
    lines = source.read_bytes().decode().splitlines(keepends=True)
    caps = [(i, line) for i, line in enumerate(lines) if line.lstrip().lower().startswith('c')]
    assert len(caps) == 329 and all(line.startswith('Cext_') and len(line.split()) == 4 for _, line in caps)
    assert [line for _, line in caps] == [line for line in prior.read_text().splitlines(keepends=True) if line.startswith('Cext_')]
    positions = {i for i, _ in caps}
    kept = [(i, line) for i, line in enumerate(lines) if i not in positions]
    reconstructed = ''.join(line for _, line in sorted(caps + kept)).encode()
    assert reconstructed == source.read_bytes()
    skeleton = ''.join(line for _, line in kept).encode()
    device = lambda text: [line for line in text.decode().splitlines(keepends=True) if line.startswith(('XM', 'XR', 'XQ'))]
    assert len(device(skeleton)) == 1036 and device(skeleton) == device(source.read_bytes())
    assert not any(line.lstrip().lower().startswith('c') for line in skeleton.decode().splitlines())
    args.output.mkdir()
    for name, data in [('baseline_586.spice', source.read_bytes()), ('reconstructed_586.spice', reconstructed),
                       ('zero_new_capacitance.spice', skeleton)]:
        (args.output / name).write_bytes(data)
    (args.output / 'historical_329_ledger.json').write_text(json.dumps([{'line_index_zero_based': i, 'line_exact': line} for i, line in caps], indent=2) + '\n')
    (args.output / Path(__file__).name).write_bytes(Path(__file__).read_bytes())
    report = {'status': 'passed control preparation', 'source_devices': 1036, 'historical_capacitors': 329,
              'line_position_reconstruction': 'passed byte-identical source586',
              'zero_newC': 'passed exact cap-free1036-device skeleton; NOT identical original329-C source',
              'historical_cap_provenance': 'passed all329C statements identical pinned priorpostlayoutsource; no otherC statements',
              'input_sha256': {str(path): sha(path) for path in (source, prior, Path(__file__))},
              'artifact_sha256': {path.name: sha(path) for path in args.output.iterdir()},
              'electrical': 'not run', 'new_capacitance': 'not run', 'seed': 'not applicable'}
    (args.output / 'summary.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()

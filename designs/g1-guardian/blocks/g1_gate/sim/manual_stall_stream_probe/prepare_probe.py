#!/usr/bin/env python3
"""Derive output-only GATE stall probes from the exact frozen fixture."""
import argparse
import hashlib
import json
from pathlib import Path

EXPECTED = 'd55c4b9fd10572478981b652b7cda2b6e14f6247303d9850dd3ba8fbc9b86743'
CONTROL = ('.control\nset num_threads=1\nset numdgt=17\nset wr_singlescale\n'
           'set wr_vecnames\ntran 1n 16u 0 1n\n')
EXTRA = ['v(xpe.xi0.net4)', 'v(xpe.xi0.net7)', 'v(xpe.xi0.net1)',
         'v(xpg.net1)', 'v(xpg.net2)', 'v(xpf.net1)',
         'v(xpf.net2)', 'v(gate_core)', 'v(fault_core)',
         'v(vdda)', 'v(vdd)', 'v(gate)', 'v(fault_n)', 'v(tripped)',
         'v(en_core)', 'v(bus)', 'v(gfet)', 'v(drain)', 'i(vfet)']


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--fixture', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--mode', choices=['control_prefix', 'raw_prefix', 'raw_full',
                                      'raw_prefix_all', 'raw_full_all'], required=True)
    a = p.parse_args()
    assert not a.output.exists()
    original = a.fixture.read_bytes()
    assert sha(original) == EXPECTED
    source, control = original.decode().split('.control\n', 1)
    assert original.decode().count('.control\n') == 1
    assert control.startswith(CONTROL[len('.control\n'):])
    assert control.endswith('quit 0\n.endc\n.end\n')
    assert '.option method=gear reltol=0.005 itl4=100 abstol=1e-9 vntol=1e-5 chgtol=1e-13' in source
    stop = '16u' if a.mode in ('raw_full', 'raw_full_all') else '1.2u'
    if a.mode == 'control_prefix':
        old = 'tran 1n 16u 0 1n\n'
        assert control.count(old) == 1
        old_wave = str(a.fixture.parent / 'wave.tsv')
        assert control.count(old_wave) == 1
        deck = source + '.control\n' + control.replace(old, 'tran 1n 1.2u 0 1n\n').replace(
            old_wave, str(a.output / 'wave.tsv'))
    else:
        saved = 'all' if a.mode.endswith('_all') else ' '.join(EXTRA)
        deck = source + '.save ' + saved + '\n.tran 1n ' + stop + ' 0 1n\n.end\n'
    assert deck.split('.control\n')[0].split('.save ')[0] == source
    a.output.mkdir(parents=True)
    (a.output / 'fixture.cir').write_text(deck)
    (a.output / '.spiceinit').write_bytes((a.fixture.parent / '.spiceinit').read_bytes())
    contract = dict(status='prepared diagnostic; not electrical acceptance',
                    original_fixture_sha256=EXPECTED, source_sha256=sha(source.encode()),
                    deck_sha256=sha(deck.encode()), mode=a.mode, stop=stop,
                    timeout_s=120, vectors=EXTRA,
                    source_unchanged=True, solver_options_unchanged=True,
                    original_control_sha256=sha(('.control\n'+control).encode()))
    (a.output / 'contract.json').write_text(json.dumps(contract, indent=2) + '\n')
    print(json.dumps({k: contract[k] for k in ['mode', 'deck_sha256', 'source_sha256']}))


if __name__ == '__main__':
    main()

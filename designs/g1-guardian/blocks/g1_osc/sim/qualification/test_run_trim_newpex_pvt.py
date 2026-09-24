#!/usr/bin/env python3
"""Pure protocol/source controls; no solver or output-run allocation."""
import argparse
import importlib.util
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE/'run_trim_newpex_pvt.py'
spec = importlib.util.spec_from_file_location('newpex_pvt', str(SOURCE))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--pex-source', type=Path, required=True)
    args = ap.parse_args()
    checks = []
    positions = [module.positions(shard) for shard in range(4)]
    checks.append(all(len(rows) == 20 for rows in positions))
    checks.append(sorted(row for rows in positions for row in rows) ==
                  [(index, code) for index in range(5) for code in range(16)])
    source = args.pex_source
    checks.append(module.source_valid(source))
    template = (HERE.parent/'postlayout/tb_osc_pex.cir').read_text()
    old_runs = [HERE/'runs'/name for name in
                ('osc_r095_candidate_shard0_20260921_01',
                 'osc_r095_candidate_shard1_20260921_01',
                 'osc_r095_remaining48_20260922_r1')]
    exact_decks = 0
    for index in range(5):
        for code in range(16):
            name, deck = module.deck_for(template, 'osc.spice', module.TUPLES[index], code)
            matches = [folder/(name+'.cir') for folder in old_runs if (folder/(name+'.cir')).exists()]
            assert len(matches) == 1
            if deck == matches[0].read_text():
                exact_decks += 1
    checks.append(exact_decks == 80)
    with tempfile.TemporaryDirectory() as folder:
        fake = Path(folder)/'pex.spice'
        fake.write_bytes(source.read_bytes().replace(b'l=55.575u', b'l=55.576u', 1))
        checks.append(not module.source_valid(fake))
        fake.write_bytes(source.read_bytes().replace(b'l=55.575u', b'l=58.5u', 1))
        checks.append(not module.source_valid(fake))
        wave = Path(folder)/'test.dat'
        wave.write_text('time v i va vb\n0 1 2 3 4\n0.000006 1 2 3 4\n')
        checks.append(module.wave_valid(wave))
        wave.write_text('time v i va vb\n0 1 2 3 4\n0.000006 NaN 2 3 4\n')
        checks.append(not module.wave_valid(wave))
        wave.write_text('time v i va vb\n0 1 2 3 4\n0 1 2 3 4\n')
        checks.append(not module.wave_valid(wave))
    assert all(checks), checks
    print('PASS %d pure controls; 80/80 exact original deck bytes excluding bound source contents' % len(checks))


if __name__ == '__main__':
    main()

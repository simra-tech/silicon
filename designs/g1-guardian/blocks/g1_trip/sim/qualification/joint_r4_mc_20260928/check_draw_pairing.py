#!/usr/bin/env python3
"""joint_r4_mc_20260928: check that the r4 deck draws, per seed, exactly the r3 mismatch vector for every r3 device.

Builds the r4 calibration deck (codes [0,0], 25 mV, 25 C) with runner_r4mc.make_deck, cuts it after the
BEFORE parameter prints (op only, no transient), runs ngspice and compares the printed vector with the r3 screen's
parameters_before.json of the same seed (bulk). Expected: the r3 entries are equal value for value; the 80 novclk
entries are additional.

  python3 qualification/joint_r4_mc_20260928/check_draw_pairing.py --seed N --r3-bulk DIR --out DIR
"""
import argparse, json, re, subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import runner_r4mc as R  # noqa: E402

p = argparse.ArgumentParser(); p.add_argument('--seed', type=int, required=True); p.add_argument('--r3-bulk', type=Path, required=True)
p.add_argument('--out', type=Path, required=True); a = p.parse_args()
a.out.mkdir(parents=True, exist_ok=True)
contract = json.loads((R.REF / 'contract.json').read_text()); groups = contract['groups']
deck = R.make_deck((R.REF / 'c00/probe.cir').read_text(), a.seed, [0, 0], .025, 25, str(a.out / 'unused.dat'))
head, tail = deck.split('echo NF4_BEFORE_END\n')
deck = head + 'echo NF4_BEFORE_END\nquit 0\n.endc\n.end\n'
cir = a.out / ('draw_s%d.cir' % a.seed); cir.write_text(deck)
log = subprocess.run(['ngspice', '-b', str(cir)], cwd=str(R.SIM), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True).stdout
(a.out / ('draw_s%d.log' % a.seed)).write_text(log)
nb = R.read_group(log, 'NON_BGR_BEFORE', groups['NON_BGR'] + R.NOV_PARAMS)
bg = R.read_group(log, 'BGR_BEFORE', groups['BGR'])
r4 = nb + bg
r3 = json.loads((a.r3_bulk / ('s%d' % a.seed) / 'parameters_before.json').read_text())
r4_shared = [x for x in r4 if x[0] not in set(R.NOV_PARAMS)]
nov = [x for x in r4 if x[0] in set(R.NOV_PARAMS)]
same = r4_shared == r3
res = dict(seed=a.seed, r3_parameters=len(r3), r4_parameters=len(r4), r3_entries_identical=same,
           differing=[(x, y) for x, y in zip(r4_shared, r3) if x != y][:10],
           novclk_delvto_mV=[round(float(v) * 1e3, 3) for k, v in nov if k.endswith('[delvto]')])
print(json.dumps(res))
(a.out / ('draw_s%d.json' % a.seed)).write_text(json.dumps(res, indent=1) + '\n')
sys.exit(0 if same else 1)

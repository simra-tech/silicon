#!/usr/bin/env python3
"""T2p (2026-10-30): code-level R2-4 of PLAN.md D30 item 2.

The final code of every slot with the real reference buffer, the real wiring and the real strobe (proxy deck of T2m,
buffer run) is compared with the final code of the same slot with ideal slice reference ports (base run, ports at the
buffer operating-point value of the same corner). Codes from the 14 raw decisions with the design weights
(sim/post/post_post.py win method). Limit: |code(buffer) - code(base)| <= 1 LSB in every slot, both slices.
Slot 0 of the ref10 deck is the first conversion of the run (0 V, after 0.6 us of track from t = 0).
usage: code_r24.py OUT.json <buffer run> <base run> [<label>]"""
import json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
POST = os.path.dirname(HERE)
BLOCK = os.path.dirname(os.path.dirname(POST))
sys.path.insert(0, os.path.join(BLOCK, 'sim', 'r4'))
sys.path.insert(0, os.path.join(BLOCK, 'sim', 'r3'))
from p4common import load_segments  # noqa
import cal3  # noqa
root = os.environ['G1_RESULTS_ROOT']
out, rb, rs = sys.argv[1:4]
WL = np.array(json.load(open(os.path.join(BLOCK, 'sim', 'results', 'r3', 'cdac3_mc50_tt_cp100_globalfit.json')))['nominal_design_weights_lsb'])
WD = cal3.quantise(WL)
res = {'tool': 'sim/post/b10/code_r24.py', 'buffer_run': rb, 'base_run': rs, 'limit_lsb': 1,
       'label': 'simulated; final codes with design weights; buffer run minus ideal-port base run'}
worst = 0
for sl in 'ab':
    codes = {}
    for k, rid in (('buf', rb), ('base', rs)):
        st = json.load(open(os.path.join(POST, 'runs', rid, 'run.json')))['status']
        if st != 'completed':
            sys.exit('run %s is %s' % (rid, st))
        slots, ba, bb = load_segments(os.path.join(POST, 'results', rid + '_segments.json'), root)
        bits = ba if sl == 'a' else bb
        codes[k] = [int(cal3.code(bits[i:i + 1], WD)[0]) for i in range(len(slots))]
    d = [x - y for x, y in zip(codes['buf'], codes['base'])]
    worst = max(worst, max(abs(x) for x in d))
    res[sl] = {'codes_buffer': codes['buf'], 'codes_base': codes['base'], 'diff_lsb': d, 'max_abs_diff_lsb': max(abs(x) for x in d)}
res['max_abs_diff_lsb'] = worst
res['result'] = 'passed' if worst <= 1 else 'failed'
json.dump(res, open(out, 'w'), indent=1)
print(rb, rs, 'A', res['a']['diff_lsb'], 'B', res['b']['diff_lsb'], res['result'])

#!/usr/bin/env python3
"""joint_r4_mc_20260928: per seed, compare the r4 runner's parameters_before.json (11592 entries) with the r3 screen's
(11512) after dropping the 80 novclk entries. No simulation; reads the two bulk run roots.

  python3 pairing_all.py <r4 bulk run root> <r3 bulk run root>
"""
import json, sys
from pathlib import Path
r4b, r3b = Path(sys.argv[1]), Path(sys.argv[2])
ok = []
for sd in range(79001, 79025):
    a, b = r4b / ('s%d' % sd) / 'parameters_before.json', r3b / ('s%d' % sd) / 'parameters_before.json'
    if not (a.exists() and b.exists()):
        print(sd, 'missing', a.exists(), b.exists()); continue
    v4, v3 = json.loads(a.read_text()), json.loads(b.read_text())
    shared = [x for x in v4 if not x[0].startswith('@n.xnov.')]
    same = shared == v3
    ok.append(same)
    print(sd, len(v4), len(v3), 'r3 entries identical' if same else 'DIFFERENT')
print('seeds identical: %d of %d' % (sum(ok), len(ok)))

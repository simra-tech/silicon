#!/usr/bin/env python3
"""Layout B4, INTERFACES row "ADC -> ctrl timing": when the ADC output word changes relative to the shared clock edge.
Reads a post-layout run (codes.raw with v(clk30), v(rawa), v(rawb)): every change of the raw word image (rawa / rawb:
the 14 decision bits ra0..ra13 of the r1_sar5_logic output registers, weighted, so a change of any bit changes it) is
located (first sample where the value leaves the old code by 0.5, linear interpolation), and its delay from the latest
rising clk30 edge (0.6 V crossing) is reported. Also the latX strobe edges if saved.
usage: out_timing.py OUT.json <run id> [<run id> ...]"""
import json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'r4'))
from p4common import read      # noqa: E402
root = os.environ['G1_RESULTS_ROOT']
out = sys.argv[1]
res = dict(label='simulated; output-word change times relative to the latest rising clk30 edge (0.6 V); sim/post/b4/out_timing.py', runs={})


def cross_up(t, v, th):
    i = np.nonzero((v[:-1] < th) & (v[1:] >= th))[0]
    return t[i] + (th - v[i]) / (v[i + 1] - v[i]) * (t[i + 1] - t[i])


for rid in sys.argv[2:]:
    d, _ = read(os.path.join(root, 'r1_adc', rid, 'codes.raw'))
    t = d['time']
    if 'v(clk30)' in d:
        ck = cross_up(t, d['v(clk30)'], 0.6)
        cks = 'v(clk30) 0.6 V crossing'
    else:   # deck source: Vclk30 PULSE(0 1.2 T 50p 50p ...) -> 0.6 V at n T + 25 ps (ideal source, not loaded)
        T = 1.0 / 30e6
        ck = np.arange(1, int(t[-1] / T) + 2) * T + 25e-12
        cks = 'deck clk30 source timing (n T + 25 ps)'
    for nm in ('v(lata)', 'v(latb)'):
        if nm in d:
            lt = cross_up(t, d[nm], 0.6)
            dl = [(x - ck[ck <= x][-1]) * 1e9 for x in lt if (ck <= x).any()]
            res.setdefault('lat_strobe', {})['%s %s' % (rid, nm)] = [round(min(dl), 3), round(max(dl), 3)] if dl else None
    r = {}
    for nm in ('v(rawa)', 'v(rawb)'):
        if nm not in d:
            continue
        v = d[nm]
        ch = []
        i = 1
        while i < len(v):
            if abs(v[i] - v[i - 1]) > 0.5:
                old = v[i - 1]
                k = i - 1
                # interpolate the time where the value leaves old by 0.5
                tc = t[k] + (0.5 * np.sign(v[i] - old)) / (v[i] - old) * (t[i] - t[k])
                j = i
                while j + 1 < len(v) and abs(v[j + 1] - v[j]) > 0.5:
                    j += 1
                ch.append(tc)
                i = j + 1
            else:
                i += 1
        dl = []
        for tc in ch:
            prev = ck[ck <= tc]
            if prev.size:
                dl.append((tc - prev[-1]) * 1e9)
        r[nm] = dict(changes=len(dl), delay_after_edge_ns_min=round(min(dl), 3) if dl else None,
                     delay_after_edge_ns_max=round(max(dl), 3) if dl else None)
    r['clock_reference'] = cks
    res['runs'][rid] = r
    print(rid, r)
json.dump(res, open(out, 'w'), indent=1)

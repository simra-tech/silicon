#!/usr/bin/env python3
"""Item 3 (revision 5): place the MC calibration windows from the nominal-circuit locate run and record the check.

usage: place_windows5.py <locate run id> OUT_points.json OUT_check.json
From the locate run (locate5.json, nominal r1_adc5_core_fast, ideal VREF 1.045 V, tt): per slice, codes with the
design weights; the input level of the code transitions 2047/2048 (A and B), 3071/3072 (A, + side) and 1023/1024
(B, - side) by linear interpolation of the code against the input; the decision-0 and decision-1 toggles (raw
bits 0 and 1). Window = +-2 LSB at 4 points per LSB (17 inputs; budget) around each transition. Check: every window
holds its code transition (else the point file is not written); toggles reported. Outer transitions outside
the locate range are extrapolated from the local slope (recorded).
Points (per slice): 15 spread inputs over +-0.93 V (fixed seeds, different for A and B) for the global weight fit,
then the 3 windows (transition 1023/1024, 2047/2048, 3071/3072); slice B windows at its own (B) levels.
"""
import json
import os
import sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
BLOCK = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(HERE, "..", "r4"))
sys.path.insert(0, os.path.join(HERE, "..", "r3"))
from p4common import load_segments
import cal3
rid, outp, outc = sys.argv[1:4]
root = os.environ["G1_RESULTS_ROOT"]
segj = os.path.join(BLOCK, "sim", "results", "r5", rid + "_segments.json")
S = json.load(open(segj))
if not S["segments"]:
    sys.exit("locate run did not complete")
P = json.load(open(os.path.join(BLOCK, S["points"])))
slots, ba, bb = load_segments(segj, root)
Wl = np.array(json.load(open(os.path.join(BLOCK, "sim", "results", "r3", "cdac3_mc50_tt_cp100_globalfit.json")))["nominal_design_weights_lsb"])
W = cal3.quantise(Wl)
LSB = 446.4e-6 * 1.045
chk = {"label": "simulated (locate run, nominal circuit, tt, ideal VREF 1.045 V) + place_windows5.py", "run": rid,
       "lsb_V": LSB, "slices": {}}


def crossing(v, y, level):
    o = np.argsort(v)
    v, y = v[o], y[o]
    i = np.nonzero((y[:-1] < level) & (y[1:] >= level))[0]
    if not i.size:
        return None
    j = i[0]
    return float(v[j] + (level - y[j]) * (v[j + 1] - v[j]) / (y[j + 1] - y[j]))


cent = {}
for sl, bits in (("a", ba), ("b", bb)):
    v = np.array(P[sl])[slots]
    c = cal3.code(bits, W).astype(float)
    near0 = np.abs(v) < 0.01
    far = ~near0
    t2048 = crossing(v[near0], c[near0], 2047.5)
    tmaj = crossing(v[far], c[far], 3071.5) if sl == "a" else crossing(v[far], c[far], 1023.5)
    extrap = False
    if tmaj is None:
        # first run (2026-10-21): the transition lies about 5 mV inside the locate range (LSB 455 uV, not the
        # assumed 466.5 uV); straight-line fit of the 12 far codes, extrapolated (recorded in the check)
        g, o = np.polyfit(v[far], c[far], 1)
        tmaj = float(((3071.5 if sl == "a" else 1023.5) - o) / g)
        extrap = True
        chk.setdefault("extrapolated", {})[sl] = {"slope_codes_per_mV": float(g * 1e-3), "transition_V": tmaj}
    d0 = crossing(v[near0], bits[near0, 0].astype(float), 0.5)
    d1 = crossing(v[far], bits[far, 1].astype(float), 0.5) if sl == "a" else crossing(v[far], 1.0 - bits[far, 1].astype(float), 0.5)
    chk["slices"][sl] = {"code_2047_2048_V": t2048, ("code_3071_3072_V" if sl == "a" else "code_1023_1024_V"): tmaj,
                         "decision0_toggle_V": d0, "decision1_toggle_V": d1,
                         "codes_near0": [int(x) for x in c[near0]], "codes_far": [int(x) for x in c[far]]}
    cent[sl] = (t2048, tmaj, d0, d1)
ok = True
win = np.arange(-8, 9) * 0.25 * LSB
pts = {}
for sl in ("a", "b"):
    t2048, tmaj, d0, d1 = cent[sl]
    if None in (t2048, tmaj):
        ok = False
        continue
    wl = [-abs(tmaj), t2048, abs(tmaj)]          # transitions 1023/1024, 2047/2048, 3071/3072 (symmetric CDAC)
    # windows serve the DNL at the major code transitions (the 14 weights come from the global fit over all
    # points), so the check is: the window holds the code transition. Decision toggles are reported only.
    chk["slices"][sl]["window_centres_V"] = wl
    chk["slices"][sl]["decision0_toggle_inside_window_2048"] = bool(d0 is not None and wl[1] + win[0] <= d0 <= wl[1] + win[-1])
    rng = np.random.RandomState(51 if sl == "a" else 52)
    spread = np.sort(rng.uniform(-0.93, 0.93, 15))
    pts[sl] = list(spread) + [x for w in wl for x in (w + win)]
chk["windows_ok"] = bool(ok)
chk["window"] = "+-2 LSB, 4 per LSB, 17 inputs; centres = nominal code transitions (+- symmetric for 1023/3071)"
json.dump(chk, open(outc, "w"), indent=1)
print(json.dumps({k: chk["slices"][k] for k in chk["slices"]}, indent=0)[:2000], "\nwindows_ok", ok)
if ok:
    json.dump({"a": [round(float(x), 7) for x in pts["a"]], "b": [round(float(x), 7) for x in pts["b"]], "n_spread": 15,
               "windows": [[15, 17], [32, 17], [49, 17]], "points_per_lsb": 4, "lsb_V": LSB,
               "note": "MC calibration set (item 3): 15 spread inputs, then windows around the nominal transitions 1023/1024, 2047/2048, 3071/3072 (check: %s)" % os.path.basename(outc)},
              open(outp, "w"), indent=0)
    print("wrote", outp)

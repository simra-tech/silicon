#!/usr/bin/env python3
"""T2j: codes of the mixed-signal run (sar/sim/tb_gl_mux.cir, gate-level r1_adc_sar) against the behavioural run.

usage: ms_compare.py <ms run id> <out json> [frames]
The 14-bit word of each frame and slice is read from adc_raw_X_13..0 (raw[13] = decision 0) 1.0 ns before edge
E15 of the frame (the edge at which r1_ctrl captures it), threshold 0.6 V; adc_valid_X must be high there and low
1.0 ns before E14. Reference: the words of the behavioural full-core run t2j-beh-mux-tt (= the SAR-only runs
t2j-bsar-mux-tt-c, README "Status"), order frame 0 A, 0 B, 1 A, ...
Runs inside the container (numpy), working directory designs/r1-joint/blocks/r1_adc.
"""
import json, os, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "sim"))
import rawread

REF = [11675, 4708, 15660, 723, 4707, 11676, 14541, 1842]
T = 1e-6 / 30.0
rid, out = sys.argv[1:3]
frames = sys.argv[3] if len(sys.argv) > 3 else "ecee"
raw = os.path.join(os.environ["G1_RESULTS_ROOT"], "r1_adc_sar", rid, "sar.raw")
names = ["time"] + ["v(adc_valid_%s)" % s for s in "ab"] + ["v(adc_raw_%s_%d)" % (s, k) for s in "ab" for k in range(14)]
d, _ = rawread.read(raw, names)
t = d["time"]


def at(name, tt):
    import numpy as np
    return float(np.interp(tt, t, d[name]))


res = {"run": rid, "reference": "t2j-beh-mux-tt words (frame 0 A, 0 B, ...)", "frames": [], "pass": True}
i = 0
for f, c in enumerate(frames):
    n0 = 18 + 22 * f
    t15 = (n0 + 15) * T - 1e-9
    t14 = (n0 + 14) * T - 1e-9
    for s in "ab":
        word = 0
        for k in range(14):
            word |= (1 if at("v(adc_raw_%s_%d)" % (s, k), t15) > 0.6 else 0) << k
        v_on = at("v(adc_valid_%s)" % s, t15) > 0.6
        v_off = at("v(adc_valid_%s)" % s, t14) < 0.6
        ok = word == REF[i] and v_on and v_off
        res["frames"].append({"frame": f, "type": c, "slice": s.upper(), "word": word, "ref": REF[i],
                              "word_bits": format(word, "014b"), "ref_bits": format(REF[i], "014b"),
                              "valid_at_E15": v_on, "valid_low_before_E14": v_off, "equal": ok})
        res["pass"] = res["pass"] and ok
        i += 1
json.dump(res, open(out, "w"), indent=1)
for r in res["frames"]:
    print(r["frame"], r["type"], r["slice"], r["word_bits"], r["ref_bits"], r["valid_at_E15"], r["equal"])
print("pass", res["pass"])

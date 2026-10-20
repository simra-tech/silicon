#!/usr/bin/env python3
"""Revision-3 dynamic test (tb_adc3_dyn.cir): codes of N slots per slice with design weights, coherent FFT
(no window), SNDR / SFDR / THD / ENOB. usage: post_dyn3.py <run id> N M OUT.json (slot 0 dropped: start-up; the
N slots after it are used)."""
import json
import os
import sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p3common import read, ts, sample, bits_from_raw, BLOCK
import cal3

rid, N, Mc, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
root = os.environ["G1_RESULTS_ROOT"]
Wd = cal3.quantise(json.load(open(os.path.join(BLOCK, "sim", "results", "r3", "cdac3_mc50_tt_cp100_globalfit.json")))["nominal_design_weights_lsb"])
d, _ = read(os.path.join(root, "r1_adc", rid, "codes.raw"))
s = np.arange(1, N + 1)
res = {"label": "simulated (tb_adc3_dyn.cir), design weights, no device noise", "run": rid, "N": N, "cycles": Mc}
for sl in ("a", "b"):
    c = cal3.code(bits_from_raw(sample(d, "v(raw%s)" % sl, ts(s) + 260e-9)), Wd).astype(float)
    X = np.abs(np.fft.rfft(c - c.mean())) ** 2
    sig = X[Mc]
    harm = [X[(k * Mc) % N if (k * Mc) % N <= N // 2 else N - (k * Mc) % N] for k in range(2, 6)]
    noise = X[1:].sum() - sig
    sndr = 10 * np.log10(sig / noise)
    res[sl] = {"sndr_dB": float(sndr), "enob": float((sndr - 1.76) / 6.02),
               "sfdr_dB": float(10 * np.log10(sig / np.max(np.delete(X[1:], Mc - 1)))),
               "thd_dB": float(10 * np.log10(sum(harm) / sig)),
               "amplitude_codes": float(2 * np.sqrt(sig) / N), "codes_min_max": [int(c.min()), int(c.max())]}
json.dump(res, open(out, "w"), indent=1)
print(json.dumps(res, indent=1))

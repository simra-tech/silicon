#!/usr/bin/env python3
"""Revision-4 dynamic test (tb_adc4_dyn.cir, chunks of an N 256 record): codes with the design weights of local
frames 1..86 of every chunk (chunk c = global frames 86c..86c+85; local frame 0 is start-up), first N used;
coherent FFT (no window), SNDR / SFDR / THD / ENOB per slice. With fewer than N frames: sine fit with the known
frequency (IEEE 1241 three-parameter form), SNDR from the residual, THD from fitted harmonics 2..5.
usage: post_dyn4.py N M OUT.json <run id chunk 0> <run id chunk 1> ..."""
import json
import os
import sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "r3"))
from p4common import read, ts, sample, bits_from_raw, BLOCK, TLAT
import cal3
N, Mc, out, runs = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3], sys.argv[4:]
root = os.environ["G1_RESULTS_ROOT"]
Wd = cal3.quantise(json.load(open(os.path.join(BLOCK, "sim", "results", "r3", "cdac3_mc50_tt_cp100_globalfit.json")))["nominal_design_weights_lsb"])
codes = {"a": [], "b": []}
for rid in runs:
    d, _ = read(os.path.join(root, "r1_adc", rid, "codes.raw"))
    nloc = int((d["time"][-1] - ts(0) - TLAT) // ts(1) + 0) 
    loc = np.arange(1, 87)
    loc = loc[ts(loc) + TLAT < d["time"][-1]]
    for sl in ("a", "b"):
        codes[sl] += list(cal3.code(bits_from_raw(sample(d, "v(raw%s)" % sl, ts(loc, sl) + TLAT)), Wd))
res = {"label": "simulated (tb_adc4_dyn.cir, r1_adc4_core_fast, r1_refbuf4), design weights, no device noise",
       "runs": runs, "N": N, "cycles": Mc, "frames_available": len(codes["a"])}
if len(codes["a"]) < N:
    # fewer frames than N (chunks missing): IEEE 1241 sine fit with the known frequency (Mc / N cycles per frame,
    # frames contiguous from global frame 1), harmonics 2..5 fitted separately for THD. No FFT.
    n = np.arange(1, len(codes["a"]) + 1)
    res["method"] = "sine fit (known frequency), %d contiguous frames; N %d not reached" % (len(n), N)
    for sl in ("a", "b"):
        c = np.array(codes[sl], dtype=float)
        ph = 2 * np.pi * Mc / N * n
        A1 = np.column_stack([np.sin(ph), np.cos(ph), np.ones_like(ph)])
        x1 = np.linalg.lstsq(A1, c, rcond=None)[0]
        r1 = c - A1 @ x1
        cols = [np.sin(ph), np.cos(ph), np.ones_like(ph)] + [f(k * ph) for k in range(2, 6) for f in (np.sin, np.cos)]
        A5 = np.column_stack(cols)
        x5 = np.linalg.lstsq(A5, c, rcond=None)[0]
        amp = float(np.hypot(x1[0], x1[1]))
        hp = sum((x5[3 + 2 * i] ** 2 + x5[4 + 2 * i] ** 2) / 2 for i in range(4))
        sndr = 10 * np.log10(amp ** 2 / 2 / np.mean(r1 ** 2))
        res[sl] = {"sndr_dB": float(sndr), "enob": float((sndr - 1.76) / 6.02), "thd_dB": float(10 * np.log10(hp / (amp ** 2 / 2))),
                   "amplitude_codes": amp, "codes_min_max": [int(c.min()), int(c.max())], "frames": int(len(c))}
    json.dump(res, open(out, "w"), indent=1)
    print(json.dumps(res, indent=1))
    sys.exit(0)
for sl in ("a", "b"):
    c = np.array(codes[sl][:N], dtype=float)
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

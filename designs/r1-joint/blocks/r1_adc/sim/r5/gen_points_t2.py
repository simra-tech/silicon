#!/usr/bin/env python3
"""T2 2026-10-21: input point sets of the revision-5 closure campaign (sim/r5/points/).
Every set starts with one start-up frame (frame 0, input 0 V) that no post-processor uses (open issue 1).
  cornwin5.json  static windows at the corners: +-6 LSB around the transitions 2047/2048 and 3071/3072, 2 points per
                 LSB (spacing 0.5 x 466.5 uV, the point-placement scale of sim/results/r5/mc_window_check.json; the LSB is 454.9 uV, so 1.95 points per LSB; centres from the same file); slice B +1/4 LSB.
  inlramp5.json  (run as halves inlramp5a.json / inlramp5b.json, each with its own start-up frame) reduced ramp for the INL with fitted weights: 96 inputs per slice over -0.90 .. +0.90 V (step
                 18.95 mV = 40.6 LSB) with a fixed pseudo-random offset of 0..1 LSB per point (seed 5); slice B
                 offset by half a step. A full ramp (>= 4096 conversions) needs >= 60 CPU-h at 55 s per frame.
  fixtt.json     first-conversion check at tt: 0 V in frames 0 and 1.
"""
import json
import os
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
C = json.load(open(os.path.join(HERE, "..", "results", "r5", "mc_window_check.json")))
LSB = C["lsb_V"]


def w(name, a, b, note):
    json.dump({"a": [round(float(x), 7) for x in a], "b": [round(float(x), 7) for x in b], "note": note},
              open(os.path.join(HERE, "points", name), "w"), indent=0)


win = np.arange(-12, 13) * 0.5 * LSB
a = np.concatenate([[0.0]] + [C["slices"]["a"]["window_centres_V"][k] + win for k in (1, 2)])
b = np.concatenate([[0.0]] + [C["slices"]["b"]["window_centres_V"][k] + win + 0.25 * LSB for k in (1, 2)])
w("cornwin5.json", a, b, "frame 0 start-up (0 V, not used); 2 windows x 25 points: +-6 LSB at 2047/2048 and 3071/3072, 2 per LSB; B +1/4 LSB")
rng = np.random.RandomState(5)
u = np.linspace(-0.90, 0.90, 96)
st = u[1] - u[0]
off = rng.rand(96) * LSB
a = np.concatenate([[0.0], u + off])
b = np.concatenate([[0.0], np.clip(u + st / 2 + off, -0.9, 0.9)])
w("inlramp5.json", a, b, "frame 0 start-up (0 V, not used); 96 inputs over +-0.90 V, step %.5f V, offset 0..1 LSB (seed 5); B + half step (clipped at 0.9 V)" % st)
w("fixtt.json", [0.0, 0.0], [0.0, 0.0], "first-conversion check at tt: 0 V in frames 0 and 1")
print("LSB", LSB, "step", st, st / LSB)

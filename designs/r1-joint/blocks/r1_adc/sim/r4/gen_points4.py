#!/usr/bin/env python3
"""Write the revision-4 input point sets (sim/r4/points/*.json). LSB 446.4 uV (revision-3 tt static windows; the
revision-4 CDAC is unchanged). Toggle levels from revision 3 (runs r3-loc-tt-c*): decision 0 at -4.20 mV,
decision 1 at +-455.3 mV (set by the CDAC and the sampling switch, both unchanged in revision 4).
  ss_sweep64.json  R2-3 / open issue 3: 64 inputs per slice at ss: 48 spread over +-0.9 V, 16 in 1 mV steps
                   around the decision-0 toggle (-12..+3 mV); slice B gets the same levels shifted by half a step.
  cornwin3.json    static windows at corners: +-6 LSB around codes 1024, 2048, 3072 (0 V and -+457 mV), 2 per LSB.
  mcwin3.json      MC calibration windows: +-3.5 LSB around the three toggles, 4 per LSB; slice B + 1/8 LSB.
  mcwin0.json      MC calibration window around the revision-4 decision-0 toggle (see the note at the end).
"""
import json
import os
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
LSB = 446.4e-6


def w(name, a, b, note):
    json.dump({"a": [round(float(x), 7) for x in a], "b": [round(float(x), 7) for x in b], "note": note},
              open(os.path.join(HERE, "points", name), "w"), indent=0)


u = np.linspace(-0.9, 0.9, 48)
z = -0.012 + 0.001 * np.arange(16)
a = np.concatenate([u, z])
b = np.concatenate([u + (u[1] - u[0]) / 2 * np.where(u < 0.85, 1, -1), z + 0.0005])
w("ss_sweep64.json", a, b, "64 inputs per slice: 48 over +-0.9 V, 16 at -12..+3 mV (1 mV); B shifted by half a step")
win = np.arange(-12, 13) * 0.5 * LSB
cent = [-1024 * LSB, 0.0, 1024 * LSB]
a = np.concatenate([c + win for c in cent])
w("cornwin3.json", a, a + 0.25 * LSB, "corner windows +-6 LSB around codes 1024/2048/3072 (centres -457.1, 0, +457.1 mV), 2 per LSB; B + 1/4 LSB")
win = np.arange(-14, 15) * 0.25 * LSB
cent = [-4.20e-3, 455.3e-3, -455.3e-3]
a = np.concatenate([c + win for c in cent])
w("mcwin3.json", a, a + LSB / 8, "MC calibration windows +-3.5 LSB around the decision toggles -4.20 mV, +-455.3 mV, 4 per LSB; B + 1/8 LSB")
# mcwin0.json (added after the seed-12 run): mcwin3 window 0 at -4.20 mV holds no decision-0 toggle in revision 4
# (b0 = 0 for all 29 inputs, -5.76..-2.64 mV, run r4-mc-tt-s12b); the toggle is above -2.6 mV. New window:
# +-5 LSB around -1.0 mV, 4 per LSB (41 inputs).
win = np.arange(-20, 21) * 0.25 * LSB
a = -1.0e-3 + win
w("mcwin0.json", a, a + LSB / 8, "MC calibration window +-5 LSB around -1.0 mV (decision-0 toggle, revision 4), 4 per LSB; B + 1/8 LSB")
print("wrote ss_sweep64.json cornwin3.json mcwin3.json mcwin0.json")

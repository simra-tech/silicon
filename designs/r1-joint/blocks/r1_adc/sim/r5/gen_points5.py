#!/usr/bin/env python3
"""Write revision-5 input point sets (sim/r5/points/*.json). LSB about 446.4 uV x 1.045 (revision-3 tt windows
scaled to the r1_refbuf5h reference 1.045 V).
  locate5.json  window-placement check on the nominal circuit (item 3, before the MC): slice A 17 inputs at
                -4..+4 mV (0.5 mV) for the decision-0 toggle and code 2047/2048, 12 inputs at +471..+482 mV (1 mV)
                for the decision-1 toggle and code 3071/3072; slice B the same at +0.25 mV and -482..-471 mV.
                Scaled to VREF 1.045 V: revision-3 decision-1 toggle 455.3 mV x 1.045 = 475.8 mV, code 3072 at
                1024 x 466.5 uV = 477.7 mV. (A first version used the 1.0 V levels 451..459 mV; found before the
                run and not used.)
  ref10.json, ss_sweep64.json: copies of the revision-4 sets (sim/r4/points).
  mccal5.json   written by place_windows5.py after the locate run (window centres from the nominal circuit).
"""
import json
import os
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))


def w(name, a, b, note):
    json.dump({"a": [round(float(x), 7) for x in a], "b": [round(float(x), 7) for x in b], "note": note},
              open(os.path.join(HERE, "points", name), "w"), indent=0)


d0 = -4e-3 + 0.5e-3 * np.arange(17)
d1 = 471e-3 + 1e-3 * np.arange(12)
w("locate5.json", np.concatenate([d0, d1]), np.concatenate([d0 + 0.25e-3, -d1[::-1]]),
  "window-placement check (nominal circuit, tt, VREF 1.045 V): A -4..+4 mV (0.5 mV) and +471..+482 mV (1 mV); B +0.25 mV and -482..-471 mV")
print("wrote locate5.json")

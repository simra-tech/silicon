#!/usr/bin/env python3
"""Shared helpers for the revision-4 post-processors (D18 frame): frame timing, raw-word decoding, segments."""
import json
import os
import sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(HERE, "..", "r3"))
from rawread import read

T = 1.0 / 30e6
F = 22 * T
T0 = 18 * T
ND = 14
BLOCK = os.path.dirname(os.path.dirname(HERE))
TLAT = ND * T + 20e-9          # raw word read 20 ns after the latch of the frame


def ts(s, sl="a", n_stag=0):
    return T0 + np.asarray(s) * F + (n_stag * T if sl == "b" else 0.0)


def bits_from_raw(x):
    """x: analog image of the raw word (0..16383). Returns (N, 14) bits, column 0 = first decision."""
    r = np.rint(np.asarray(x)).astype(np.int64)
    return np.array([(r >> (ND - 1 - j)) & 1 for j in range(ND)]).T.astype(np.uint8)


def sample(d, name, t):
    return np.interp(t, d["time"], d[name])


def raw_bits(d, sl, frames, n_stag=0, inst=""):
    return bits_from_raw(sample(d, "v(%sraw%s)" % (inst, sl), ts(frames, sl, n_stag) + TLAT))


def load_segments(seg_json, root, inst=""):
    """Returns (frame index array, bits A, bits B) for all kept frames of a run_points4.py run."""
    S = json.load(open(seg_json))
    n = S.get("n_stag", 0)
    slots, ra, rb = [], [], []
    for sg in S["segments"]:
        d, _ = read(os.path.join(root, "r1_adc", sg["run_id"], "codes.raw"))
        loc = np.arange(sg["slots"])
        ra.append(raw_bits(d, "a", loc, n, inst))
        rb.append(raw_bits(d, "b", loc, n, inst))
        slots.append(sg["first_slot"] + loc)
    return np.concatenate(slots), np.concatenate(ra), np.concatenate(rb)

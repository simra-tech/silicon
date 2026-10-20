#!/usr/bin/env python3
"""Shared helpers for the revision-3 post-processors: slot timing, raw-word decoding, segment loading."""
import json
import os
import sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from rawread import read

T = 1.0 / 30e6
H = T / 2
SLOT = 18 * T
T0 = 600e-9
ND = 14
BLOCK = os.path.dirname(os.path.dirname(HERE))


def ts(s):
    return T0 + s * SLOT


def bits_from_raw(x):
    """x: analog image of the raw word (0..16383). Returns (N, 14) bits, column 0 = first decision."""
    r = np.rint(np.asarray(x)).astype(np.int64)
    return np.array([(r >> (ND - 1 - j)) & 1 for j in range(ND)]).T.astype(np.uint8)


def sample(d, name, t):
    return np.interp(t, d["time"], d[name])


def load_segments(seg_json, root):
    """Returns (slot index array, bits A, bits B) for all kept slots of a run_points3.py run."""
    S = json.load(open(seg_json))
    slots, ra, rb = [], [], []
    for sg in S["segments"]:
        d, _ = read(os.path.join(root, "r1_adc", sg["run_id"], "codes.raw"))
        loc = np.arange(sg["slots"])
        t = ts(loc) + 260e-9
        ra.append(sample(d, "v(rawa)", t))
        rb.append(sample(d, "v(rawb)", t))
        slots.append(sg["first_slot"] + loc)
    return np.concatenate(slots), bits_from_raw(np.concatenate(ra)), bits_from_raw(np.concatenate(rb))

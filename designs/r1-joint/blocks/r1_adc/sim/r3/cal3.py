#!/usr/bin/env python3
"""R1 ADC revision 3: bench weight calibration (R2-11), behavioural model. Python 3.6 + numpy.

Methods (both produce 14 weights W_j in 1/8 LSB, 14 bit, sum 4095 LSB; code = sat12((sum b_j W_j + 4) >> 3)):
  G  global (revision-2 method): one ramp over +-0.995 FS, M conversions per LSB, least squares of the ramp
     index against [1, b_0..b_13]. A smooth INL bow of the analog front (sampling network) is absorbed into the
     MSB weights, which moves the major transitions (revision-2 circuit result: code 2048 2.8 LSB wide).
  W  windowed (revision-3 method): (1) coarse ramp, 1 conversion per LSB, locates the input levels where one of
     the decisions 0..J changes, and K levels each where decisions J+1..8 change; (2) fine ramp windows of +-h LSB with M conversions per LSB centred on those
     levels; (3) least squares of the ramp index against [one offset per window, b_0..b_13]. The per-window
     offsets take up the slow bow, so the weights are fixed by the local continuity of the transfer at each
     major transition only.
Functions take a `convert(v)` callable that returns raw bits (N, 14) for input levels v (V), so the same code runs
on the behavioural model (MC) and on circuit results (sim/r3/post_cal3_circuit.py).
"""
import numpy as np


def quantise(w_lsb):
    W = np.rint(np.asarray(w_lsb) * 8.0).astype(np.int64)
    if W.min() < 0 or W.max() >= 16384:
        raise ValueError("weight outside 14-bit range: %s" % W)
    return W


def code(bits, W):
    return np.clip((bits.astype(np.int64) @ W + 4) >> 3, 0, 4095)


def fit_global(bits, idx):
    A = np.column_stack([np.ones(len(idx)), bits.astype(float)])
    x = np.linalg.lstsq(A, idx.astype(float), rcond=None)[0]
    w = x[1:]
    return w * 4095.0 / w.sum()


def fit_windowed(bits, pos, win):
    """pos: ramp position (any linear unit), win: window index per row."""
    nw = int(win.max()) + 1
    O = np.zeros((len(pos), nw))
    O[np.arange(len(pos)), win] = 1.0
    A = np.column_stack([O, bits.astype(float)])
    x = np.linalg.lstsq(A, pos.astype(float), rcond=None)[0]
    w = x[nw:]
    return w * 4095.0 / w.sum()


def locate(vc, bits_c, J, K=4, JL=8):
    """Window centres from a coarse ramp (input levels vc, raw bits bits_c): every level where one of the
    decisions 0..J changes, plus K levels (spread over the range) for each decision J+1..JL. Decisions above JL
    (weights <= 5 LSB) change inside every window. Changes within 3 coarse steps are merged (noise chatter)."""
    centres = []
    for j in range(JL + 1):
        i = np.nonzero(bits_c[1:, j] != bits_c[:-1, j])[0]
        cj, grp = [], []
        for k in i:
            if grp and k - grp[-1] > 3:
                cj.append(0.5 * (vc[grp[0]] + vc[grp[-1] + 1]))
                grp = []
            grp.append(k)
        if grp:
            cj.append(0.5 * (vc[grp[0]] + vc[grp[-1] + 1]))
        if j > J and len(cj) > K:
            cj = [cj[int(x)] for x in np.linspace(0, len(cj) - 1, K + 2)[1:-1]]
        centres += cj
    return np.array(sorted(centres))


def windows(centres, lsb_v, h, M):
    """Fine ramp points: for each centre, 2 h M points at lsb_v / M spacing. Returns (v, window index)."""
    off = (np.arange(-h * M, h * M) + 0.5) * lsb_v / M
    v = (centres[:, None] + off[None, :]).ravel()
    w = np.repeat(np.arange(len(centres)), len(off))
    return v, w


def dnl_inl(vd, c):
    trans = np.full(4096, np.nan)
    cmax = np.maximum.accumulate(c)
    for k in range(1, 4096):
        i = np.searchsorted(cmax, k)
        if i < len(vd):
            trans[k] = vd[i]
    lsb = (trans[4095] - trans[1]) / 4094.0
    dnl = np.diff(trans[1:]) / lsb - 1.0          # dnl[k-1] = width of code k
    inl = (trans[1:] - (trans[1] + lsb * np.arange(4095))) / lsb
    hist = np.bincount(c, minlength=4096)
    return dnl, inl, int(np.sum(hist[1:4095] == 0))


def major(dnl):
    """|DNL| of the codes on both sides of the major transitions 1024, 2048, 3072."""
    return {str(k): [float(dnl[k - 2]), float(dnl[k - 1])] for k in (1024, 2048, 3072)}

#!/usr/bin/env python3
"""R1 ADC revision 2: behavioural model of the 13-decision SAR and of the digital weight correction (D12).
Python 3.6 + numpy. Used by post_cdac2_mc.py and post_static2.py.

Conventions
  * Decision j = 0..12 (j = 0 first). After decision j <= 11 the capacitor k = 11 - j of the side that was
    higher steps VREF -> GND (monotonic switching). wp[k], wn[k] are the simulated top-node steps in volts.
  * Raw word: bits b[:, j]. Code (r1_ctrl): code = sat12((sum_j b_j * W_j + 4) >> 3), W_j = 14-bit unsigned
    weights in units of 1/8 LSB (11.3 fixed point), W_j < 16384.
  * Bench calibration ("ramp"): a slow linear input ramp, M conversions per nominal LSB; least squares of the
    sample index against [1, b_0..b_12] gives the weights up to scale and offset; scaled so that the all-ones
    word maps to 4095 (sum W = 4095 LSB), quantised to 1/8 LSB.
"""
import numpy as np

ND = 13
NB = 12
KT = 1.380649e-23 * 300.15


def convert(vd, wp, wn, noise=0.0, offset=0.0, rng=None):
    """vd: differential input (V) after sampling. Returns bits (N, 13) as uint8."""
    vd = np.asarray(vd, dtype=float)
    NB = len(wp)
    ND = NB + 1
    vp = vd / 2.0
    vn = -vd / 2.0
    bits = np.zeros((vd.size, ND), dtype=np.uint8)
    for j in range(ND):
        n = 0.0 if noise == 0.0 else rng.normal(0.0, noise, vd.size)
        b = (vp - vn + n + offset) > 0
        bits[:, j] = b
        if j < NB:
            k = NB - 1 - j
            vp = vp - b * wp[k]
            vn = vn - (~b) * wn[k]
    return bits


def nominal_weights_lsb(wp, wn):
    """Design weights (LSB): W_j = (wp + wn)[11-j], W_12 = (wp + wn)[0] / 2, scaled to sum 4095."""
    NB = len(wp)
    w = np.array([wp[NB - 1 - j] + wn[NB - 1 - j] for j in range(NB)] + [(wp[0] + wn[0]) / 2.0])
    return w * 4095.0 / w.sum()


def extract_weights(bits, idx):
    """Least squares of the ramp index idx against [1, bits]; returns weights (LSB) with sum 4095."""
    A = np.column_stack([np.ones(len(idx)), bits.astype(float)])
    x, *_ = np.linalg.lstsq(A, idx.astype(float), rcond=None)
    w = x[1:]
    return w * 4095.0 / w.sum()


def quantise(w_lsb):
    W = np.rint(np.asarray(w_lsb) * 8.0).astype(np.int64)
    if W.min() < 0 or W.max() >= 16384:
        raise ValueError("weight outside 14-bit range: %s" % W)
    return W


def code_from_bits(bits, W):
    s = bits.astype(np.int64) @ W
    return np.clip((s + 4) >> 3, 0, 4095)


def dnl_inl(vd, code):
    """vd ascending, code per point. End-point DNL / INL over codes 1..4094 from code transitions."""
    trans = np.full(4096, np.nan)
    cmax = np.maximum.accumulate(code)
    for c in range(1, 4096):
        i = np.searchsorted(cmax, c)
        if i < len(vd):
            trans[c] = vd[i]
    lsb = (trans[4095] - trans[1]) / 4094.0
    width = np.diff(trans[1:])
    dnl = width / lsb - 1.0
    inl = (trans[1:] - (trans[1] + lsb * np.arange(4095))) / lsb
    hist = np.bincount(code, minlength=4096)
    missing = int(np.sum(hist[1:4095] == 0))
    nonmono = int(np.sum(np.diff(code) < 0))
    return lsb, dnl, inl, missing, nonmono


def full_scale(wp, wn):
    """Differential input range (V) that the conversion resolves: sum of all steps / 2 per side."""
    return 0.5 * (np.sum(wp) + np.sum(wn))

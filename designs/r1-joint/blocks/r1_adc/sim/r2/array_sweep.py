#!/usr/bin/env python3
"""Derived (not circuit-simulated) array study for revision 2: analytic capacitive weights with random unit
mismatch (sigma 1 %/sqrt(area um2), S4 cap_cmim model), same SAR / correction model as post_cdac2_mc.py with
true (exact) weights quantised to 1/8 LSB. Validated against the AC-solved MC (run r2-cdac-mc50-tt-c-cp0):
the nominal analytic weights must agree to < 0.01 %.
usage: array_sweep.py <validate rawdir> | sweep
"""
import sys
import numpy as np
import sar2_model as m

TOP = [16, 8, 4, 2, 1]
LSB = [64, 32, 16, 8, 4, 2, 1]
AU = 3.78 ** 2
CU = 1.5 * AU + 0.04 * 4 * 3.78     # fF


def weights(cb_cu, rng=None, af=1.0, cpar=0.0, cplsb=0.0, lsb_caps=None):
    """Returns wp-like weight vector (V per VREF=1) for caps C11..C0 (index k), one side."""
    sig = 0.01 / np.sqrt(AU * af)
    def draw(n):
        if rng is None:
            return float(n)
        return float(np.sum(1 + sig * rng.normal(size=n)))
    top = [draw(n) for n in TOP]
    L = LSB if lsb_caps is None else lsb_caps
    lsb = [draw(n) if n >= 1 else 1.0 / (1.0 / draw(1) + 1.0 / draw(1)) for n in L]   # 0.5 = two units in series
    cb = cb_cu * (1 + (0 if rng is None else 0.01 / np.sqrt(AU * cb_cu * af) * rng.normal()))
    CL = sum(lsb) + cplsb / CU
    ct = sum(top) + cb * CL / (cb + CL) + cpar / CU
    nb = len(top) + len(lsb)
    w = np.zeros(nb)
    for i, c in enumerate(top):
        w[nb - 1 - i] = c / ct
    for i, c in enumerate(lsb):
        w[len(lsb) - 1 - i] = c * cb / (cb + CL) / ct
    return w


def evaluate(cb, af, n=50, seed=1, lsb_caps=None):
    rng = np.random.RandomState(seed)
    out = []
    for _ in range(n):
        wp, wn = weights(cb, rng, af, lsb_caps=lsb_caps), weights(cb, rng, af, lsb_caps=lsb_caps)
        fs = m.full_scale(wp, wn)
        vd = np.arange(-fs * 1.002, fs * 1.002, 2 * fs / 4096 / 32)
        bits = m.convert(vd, wp, wn)
        W = m.quantise(m.nominal_weights_lsb(wp, wn))
        _, dnl, inl, miss, _ = m.dnl_inl(vd, m.code_from_bits(bits, W))
        out.append((np.nanmax(np.abs(dnl)), miss, np.nanmax(np.abs(inl))))
    a = np.array(out)
    return a


if __name__ == "__main__":
    if sys.argv[1] == "validate":
        sys.path.insert(0, ".")
        import post_cdac2_mc as p
        _, w = p.parse(sys.argv[2])
        sim = np.median(w["p"], axis=0)
        ana = weights(27.52 / CU)
        print("analytic vs AC-solved (median) relative difference per cap:", np.round((ana - sim) / sim * 100, 4), "%")
    elif sys.argv[1] == "nd14":
        # 14 decisions: LSB array 64..1 plus a half unit (two units in series), same top array.
        L14 = LSB + [0.5]
        for cb in (1.249, 1.30):
            a = evaluate(cb, 1, lsb_caps=L14)
            print("14 decisions, Cb %.3f Cu, unit x1: DNLmax median %.3f max %.3f, n<=0.5: %d/50, missing-code samples %d, INLmax %.2f"
                  % (cb, np.median(a[:, 0]), a[:, 0].max(), np.sum(a[:, 0] <= 0.5), np.sum(a[:, 1] > 0), a[:, 2].max()))
    else:
        for cb in (1.249, 1.30, 1.351, 1.40):
            step = 4096 / (31 * 2 / (cb / (127 + cb)) + 255)
            for af in (1, 2, 4):
                a = evaluate(cb, af)
                print("Cb %.3f Cu (raw step %.3f LSB) unit x%d: DNLmax median %.3f max %.3f, n<=0.5: %d/50, missing-code samples %d, INLmax %.2f"
                      % (cb, step, af, np.median(a[:, 0]), a[:, 0].max(), np.sum(a[:, 0] <= 0.5), np.sum(a[:, 1] > 0), a[:, 2].max()))

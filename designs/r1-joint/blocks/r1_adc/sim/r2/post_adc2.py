#!/usr/bin/env python3
"""Post-process revision-2 conversion decks (Python 3.6, numpy). Raw 13-bit words from v(rawa)/v(rawb).

usage:
  post_adc2.py words  <codes.raw> [nframes]                       print frame, rawA, rawB, codes (design weights)
  post_adc2.py static OUT.json VSTEP seg1.raw@VSTART [seg2.raw@VSTART ...] [--weights W.json] [--fit-top K]
  post_adc2.py dyn    OUT.json M N AMP codes.raw [--weights W.json]
  post_adc2.py frames OUT.json codes.raw "labelA0,labelB0;labelA1,labelB1;..." [--weights W.json]   held-frame decks

Frame f is sampled at T0 + f us (T0 = 0.6 us); slice A word is read at T0 + f us + 20 T (latched at 12.66 T),
slice B at T0 + f us + 29 T (latched at 25.66 T).
Codes: code = sat12((sum b_j W_j + 4) >> 3) with W = 14-bit weights in 1/8 LSB:
  design weights (nominal AC-solved array, normalised to sum 4095) unless --weights is given;
  static: additionally weights extracted from the same ramp by least squares (bench method, D12) and the
  DNL/INL with those weights ("ramp-calibrated").
"""
import json
import os
import sys

import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
import sar2_model as m
from rawread import read

T = 1.0 / 30e6
T0 = 0.6e-6
# design weights: nominal array from run r2-cdac-mc50-tt-c-cp0 (median over 50 samples), sar2_model.nominal_weights_lsb
DESIGN_W_LSB = [2032.179, 1016.163, 508.002, 254.002, 127.028, 79.12, 39.559, 19.782, 9.892, 4.945, 2.472, 1.236, 0.618]


def words(path):
    d, _ = read(path, ["time", "v(rawa)", "v(rawb)"])
    t = d["time"]
    nf = int((t[-1] - T0 - 29.5 * T) // 1e-6) + 1
    fa = T0 + np.arange(nf) * 1e-6 + 20 * T
    fb = T0 + np.arange(nf) * 1e-6 + 29 * T
    ra = np.rint(np.interp(fa, t, d["v(rawa)"])).astype(np.int64)
    rb = np.rint(np.interp(fb, t, d["v(rawb)"])).astype(np.int64)
    return np.arange(nf), ra, rb


def bits_of(raw):
    return ((raw[:, None] >> (12 - np.arange(13))[None, :]) & 1).astype(np.uint8)


def codes(raw, W):
    return m.code_from_bits(bits_of(raw), W)


def extract_top(bits, idx, k):
    """Least squares with the top k weights free and the lower weights fixed to the design ratios
    (one common gain). Used when the ramp step is too coarse to resolve the small weights."""
    d = np.array(DESIGN_W_LSB)
    low = bits[:, k:].astype(float) @ d[k:]
    A = np.column_stack([np.ones(len(idx)), bits[:, :k].astype(float), low])
    x, *_ = np.linalg.lstsq(A, idx.astype(float), rcond=None)
    w = np.concatenate([x[1:k + 1], x[k + 1] * d[k:]])
    return w * 4095.0 / w.sum()


def static(out, vstep, segs, W, wfile=None, fit_top=None):
    vin, ra = [], []
    for path, v0, nf in segs:
        f, a, _ = words(path)
        if nf is not None:
            f, a = f[:nf], a[:nf]
        vin.append(v0 + f * vstep)
        ra.append(a)
    vin = np.concatenate(vin)
    ra = np.concatenate(ra)
    _, order = np.unique(np.round(vin / vstep).astype(np.int64), return_index=True)
    vin, ra = vin[order], ra[order]
    b = bits_of(ra)
    res = {"label": "simulated (schematic, fast core slice A, ideal VREF, no device noise)", "frames": int(len(vin)),
           "vstep_V": vstep, "vin_span_V": [float(vin[0]), float(vin[-1])]}
    # ramp-calibrated weights: least squares of the input value against the bits (inputs inside the code range)
    inside = (ra > 0) & (ra < 8191)
    Wext = None
    if np.all(b[inside].min(axis=0) == 0) and np.all(b[inside].max(axis=0) == 1) and inside.sum() > 60:
        try:
            if fit_top:
                Wext = m.quantise(extract_top(b[inside], np.round(vin[inside] / vstep), fit_top))
                res["weights_fit"] = "top %d weights free, lower weights fixed to design ratios with one gain" % fit_top
            else:
                Wext = m.quantise(m.extract_weights(b[inside], np.round(vin[inside] / vstep)))
                res["weights_fit"] = "all 13 weights free"
            res["weights_ramp_calibrated_W"] = [int(x) for x in Wext]
        except ValueError:
            Wext = None
    if Wext is None:
        res["weights_ramp_calibrated_W"] = "not extracted (window too narrow: not every bit toggles)"
    res["weights_design_W"] = [int(x) for x in W]
    sets = (("design_weights" if wfile is None else "given_weights", W),) + ((("ramp_calibrated_weights", Wext),) if Wext is not None else ())
    if wfile is not None:
        res["given_weights_from"] = os.path.basename(wfile)
    for name, WW in sets:
        c = m.code_from_bits(b, WW)
        lo, hi = int(c.min()), int(c.max())
        c1, c2 = lo + 1, hi - 1
        hist = np.bincount(c, minlength=4096)[c1:c2 + 1].astype(float)
        avg = hist.mean()
        dnl = hist / avg - 1.0
        cm = np.maximum.accumulate(c)
        ks = np.arange(c1, c2 + 2)
        tr = np.array([vin[min(np.searchsorted(cm, k), len(vin) - 1)] for k in ks])
        lsb = (tr[-1] - tr[0]) / (len(tr) - 1)
        inl = (tr - (tr[0] + lsb * np.arange(len(tr)))) / lsb
        ins = (c > 0) & (c < 4095)
        A = np.column_stack([np.ones(ins.sum()), vin[ins]])
        x, *_ = np.linalg.lstsq(A, c[ins].astype(float), rcond=None)
        r = c[ins] - A @ x
        fit = {"lsb_uV": float(1e6 / x[1]), "full_scale_diff_V": float(2048 / x[1]),
               "input_at_code_2047p5_mV": float((2047.5 - x[0]) / x[1] * 1e3),
               "residual_min_lsb": float(r.min()), "residual_max_lsb": float(r.max()),
               "frames_at_code_0": int(np.sum(c == 0)), "frames_at_code_4095": int(np.sum(c == 4095)),
               "note": "best-fit line of code against input at the sample points (codes 1..4094); the residual "
                       "includes +-0.5 LSB quantisation and is the INL estimate when the step is > 1 LSB"}
        res[name + "_bestfit"] = fit
        res[name] = {"code_range_observed": [lo, hi], "codes_evaluated": [c1, c2], "hits_per_code_mean": float(avg),
                     "dnl_resolution_lsb": float(1.0 / avg), "lsb_uV": float(lsb * 1e6),
                     "full_scale_diff_V_est": float(lsb * 2048),
                     "mid_transition_mV": float(tr[np.searchsorted(ks, 2048)] * 1e3) if c1 < 2048 < c2 else None,
                     "dnl_min": float(dnl.min()), "dnl_max": float(dnl.max()), "inl_min": float(inl.min()),
                     "inl_max": float(inl.max()), "missing_codes": int(np.sum(hist == 0)),
                     "non_monotonic_steps": int(np.sum(np.diff(c) < 0))}
        np.savetxt(out.replace(".json", "_%s_dnl_inl.txt" % name), np.column_stack([np.arange(c1, c2 + 1), dnl, inl[:-1]]),
                   fmt="%d %.4f %.4f", header="code dnl_lsb inl_lsb (transition of code)")
    json.dump(res, open(out, "w"), indent=1)
    print(json.dumps(res, indent=1))


def dyn(out, M, N, amp, path, W):
    if path.endswith(".json"):
        j = json.load(open(path))
        root = os.environ["G1_RESULTS_ROOT"]
        ra, rb = [], []
        for g in j["segments"]:
            _, a_, b_ = words(os.path.join(root, g["raw"]))
            ra.append(a_[:g["frames"]])
            rb.append(b_[:g["frames"]])
        ra, rb = np.concatenate(ra), np.concatenate(rb)
    else:
        f, ra, rb = words(path)
    res = {"label": "simulated (schematic, fast core, ideal VREF, no device noise)", "N": N, "M": M,
           "fin_Hz": M / N * 1e6, "amp_diff_peak_V": amp}
    for name, raw in (("A_sin", ra), ("B_cos", rb)):
        x = codes(raw[:N], W).astype(float) - 2047.5
        if np.ptp(x) == 0:
            res[name] = "not converted in this deck (slice tied off)"
            continue
        P = np.abs(np.fft.rfft(x)) ** 2
        P[0] = 0
        sig = P[M]
        harm = sum(P[min((h * M) % N, N - (h * M) % N)] for h in range(2, 10))
        nd = P.sum() - sig
        spur = np.delete(P.copy(), [0, M])
        a = 2 * np.sqrt(sig) / N
        sndr = 10 * np.log10(sig / nd)
        res[name] = {"SNDR_dB": float(sndr), "SFDR_dB": float(10 * np.log10(sig / spur.max())),
                     "THD_dB": float(10 * np.log10(harm / sig)), "ENOB": float((sndr - 1.76) / 6.02),
                     "signal_dBFS": float(20 * np.log10(a / 2048)), "amplitude_lsb": float(a)}
        np.savetxt(out.replace(".json", "_%s_spectrum.txt" % name),
                   np.column_stack([np.arange(len(P)) / N * 1e6, 10 * np.log10(P / sig + 1e-30)]), fmt="%.1f %.2f",
                   header="f_Hz dBc")
    json.dump(res, open(out, "w"), indent=1)
    print(json.dumps(res, indent=1))


def main():
    a = sys.argv[1:]
    W = m.quantise(DESIGN_W_LSB)
    wfile = None
    if "--weights" in a:
        wfile = a[a.index("--weights") + 1]
        jw = json.load(open(wfile))
        W = np.array(jw["W"] if "W" in jw else jw["weights_ramp_calibrated_W"], dtype=np.int64)
        i = a.index("--weights")
        a = a[:i] + a[i + 2:]
    fit_top = None
    if "--fit-top" in a:
        i = a.index("--fit-top")
        fit_top = int(a[i + 1])
        a = a[:i] + a[i + 2:]
    if a[0] == "words":
        f, ra, rb = words(a[1])
        for i in range(len(f)):
            print(f[i], ra[i], rb[i], int(codes(ra[i:i + 1], W)[0]), int(codes(rb[i:i + 1], W)[0]))
    elif a[0] == "frames":
        f, ra, rb = words(a[2])
        labels = [x.split(",") for x in a[3].split(";")]
        n = min(len(labels), len(f))
        ca, cb = codes(ra[:n], W), codes(rb[:n], W)
        res = {"label": "simulated (schematic)", "weights": os.path.basename(wfile) if wfile else "design",
               "frames_in_raw": int(len(f)), "frames": [
                   {"frame": i, "input_A": labels[i][0], "input_B": labels[i][1], "rawA": int(ra[i]), "rawB": int(rb[i]),
                    "codeA": int(ca[i]), "codeB": int(cb[i])} for i in range(n)]}
        json.dump(res, open(a[1], "w"), indent=1)
        print(json.dumps(res, indent=1))
    elif a[0] == "static":
        segs = []
        for s in a[3:]:
            if s.endswith(".json"):
                j = json.load(open(s))
                root = os.environ["G1_RESULTS_ROOT"]
                segs += [(os.path.join(root, g["raw"]), g["vstart"], g["frames"]) for g in j["segments"]]
            else:
                segs.append((s.split("@")[0], float(s.split("@")[1]), None))
        static(a[1], float(a[2]), segs, W, wfile, fit_top)
    else:
        dyn(a[1], int(a[2]), int(a[3]), float(a[4]), a[5], W)


if __name__ == "__main__":
    main()

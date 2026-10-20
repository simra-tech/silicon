#!/usr/bin/env python3
"""Post-process the R1 ADC transient decks (Python 3.6, numpy).

usage:
  post_adc.py static OUT.json VSTART VSTEP codes1.txt [codes2.txt ...]   (segments in ramp order)
  post_adc.py dyn    OUT.json M N AMP codes.txt

codes*.txt: ngspice wrdata of linearize(v(codea), v(codeb)), one row per frame (frame n at 1.2 us + n us).
static: histogram DNL (codes 1..4094 inside the ramp span) and code-transition INL with an end-point line,
        separately for slice A and slice B. Each segment file carries its own VSTART in the order given:
        pass "VSTART:VSTEP" per file through env-free argument form "file@vstart".
dyn:    coherent FFT per channel (no window), SNDR, SFDR, THD (h2..h9), ENOB = (SNDR - 1.76)/6.02,
        and ENOB referred to the measured full scale.
"""
import json
import sys

import numpy as np


def load_codes(path, tmax=None):
    """Returns frame index, codea, codeb. Accepts ngspice wrdata (time ...) or run_resume merged files (frame ...).
    tmax: drop wrdata rows at or after an abort time."""
    merged = open(path).readline().split()[0] == "frame"
    rows = []
    for line in open(path):
        p = line.split()
        if not p:
            continue
        try:
            vals = [float(x) for x in p]
        except ValueError:
            continue
        rows.append(vals)
    a = np.array(rows)
    if merged:
        f = a[:, 0].astype(int)
    else:
        if tmax is not None:
            a = a[a[:, 0] < tmax]
        f = np.rint((a[:, 0] - 1.2e-6) / 1e-6).astype(int)
    return f, np.rint(a[:, 1]).astype(int), np.rint(a[:, 2]).astype(int)


def static(out, vstep, segs):
    vin, ca, cb = [], [], []
    for path, v0, tmax in segs:
        f, a, b = load_codes(path, tmax)
        vin.append(v0 + f * vstep)
        ca.append(a)
        cb.append(b)
    vin = np.concatenate(vin)
    # overlapping segments: keep the first occurrence of every input value
    _, order = np.unique(np.round(vin / vstep).astype(np.int64), return_index=True)
    vin = vin[order]
    res = {"deck": "tb_adc_static.cir", "label": "simulated", "frames": int(len(vin)), "vstep_V": vstep,
           "vin_span_V": [float(vin[0]), float(vin[-1])]}
    for name, c in (("A", np.concatenate(ca)[order]), ("B", np.concatenate(cb)[order])):
        lo, hi = int(c.min()), int(c.max())
        if hi - lo < 10:
            res[name] = {"note": "slice not converting in this deck (r1_adc_core_fast_a has slice A only)"}
            continue
        # full codes strictly inside the observed range
        c1, c2 = lo + 1, hi - 1
        hist = np.bincount(c, minlength=4096)
        h = hist[c1:c2 + 1].astype(float)
        avg = h.mean()
        dnl = h / avg - 1.0
        # code transitions: first input with code >= k (monotonic check separately)
        cm = np.maximum.accumulate(c)
        nonmono = int(np.sum(np.diff(c) < 0))
        ks = np.arange(c1, c2 + 2)
        tr = np.array([vin[np.searchsorted(cm, k)] for k in ks])
        lsb = (tr[-1] - tr[0]) / (len(tr) - 1)
        inl = (tr - (tr[0] + lsb * np.arange(len(tr)))) / lsb
        miss = int(np.sum(h == 0))
        worst = np.argsort(np.abs(dnl))[::-1][:6]
        res[name] = {"code_range_observed": [lo, hi], "codes_evaluated": [c1, c2],
                     "hits_per_code_mean": float(avg), "dnl_resolution_lsb": float(1.0 / avg),
                     "lsb_from_transitions_uV": float(lsb * 1e6),
                     "full_scale_diff_V_est": float(lsb * 4096),
                     "offset_mid_transition_mV": float((tr[np.searchsorted(ks, 2048)] - 0.0) * 1e3) if c1 < 2048 < c2 else None,
                     "dnl_min": float(dnl.min()), "dnl_max": float(dnl.max()),
                     "inl_min": float(inl.min()), "inl_max": float(inl.max()),
                     "missing_codes": miss, "non_monotonic_steps": nonmono,
                     "dnl_worst": [{"code": int(c1 + i), "dnl": float(dnl[i])} for i in worst]}
        np.savetxt(out.replace(".json", "_%s_dnl_inl.txt" % name),
                   np.column_stack([np.arange(c1, c2 + 1), dnl, inl[:-1]]), fmt="%d %.4f %.4f",
                   header="code dnl_lsb inl_lsb (transition of code)")
    with open(out, "w") as f:
        json.dump(res, f, indent=1)
    print(json.dumps(res, indent=1))


def dyn(out, M, N, amp, path):
    fr, ca, cb = load_codes(path)
    o = np.argsort(fr)
    fr, ca, cb = fr[o], ca[o], cb[o]
    res = {"deck": "tb_adc_dyn.cir", "label": "simulated (no device noise: quantisation + distortion + settling only)",
           "N": N, "M": M, "fin_Hz": M / N * 1e6, "fs_per_channel_Hz": 1e6, "conversion_rate_Hz": 2e6,
           "amp_diff_peak_V": amp}
    for name, c in (("A_sin", ca), ("B_cos", cb)):
        x = c[:N].astype(float) - 2047.5
        X = np.fft.rfft(x)
        P = np.abs(X) ** 2
        P[0] = 0.0
        sig = P[M]
        harm = []
        for h in range(2, 10):
            k = (h * M) % N
            if k > N // 2:
                k = N - k
            harm.append(float(P[k]))
        noise_dist = P.sum() - sig
        sndr = 10 * np.log10(sig / noise_dist)
        spur = np.delete(P.copy(), [0, M])
        sfdr = 10 * np.log10(sig / spur.max())
        thd = 10 * np.log10(sum(harm) / sig)
        a_codes = 2 * np.sqrt(sig) / N             # amplitude in LSB
        fs_dbfs = 20 * np.log10(a_codes / 2048.0)
        enob = (sndr - 1.76) / 6.02
        res[name] = {"amplitude_lsb": float(a_codes), "signal_dBFS": float(fs_dbfs), "SNDR_dB": float(sndr),
                     "SFDR_dB": float(sfdr), "THD_dB": float(thd), "ENOB": float(enob),
                     "ENOB_fullscale_referred": float((sndr - fs_dbfs - 1.76) / 6.02),
                     "code_min": int(c[:N].min()), "code_max": int(c[:N].max())}
        np.savetxt(out.replace(".json", "_%s_spectrum.txt" % name),
                   np.column_stack([np.arange(len(P)) / N * 1e6, 10 * np.log10(P / sig + 1e-30)]),
                   fmt="%.1f %.2f", header="f_Hz dBc")
    with open(out, "w") as f:
        json.dump(res, f, indent=1)
    print(json.dumps(res, indent=1))


def main():
    mode, out = sys.argv[1], sys.argv[2]
    if mode == "static":
        vstep = float(sys.argv[3])
        segs = []
        for a in sys.argv[4:]:
            q = a.split("@")                       # file@vstart[@tmax]
            segs.append((q[0], float(q[1]), float(q[2]) if len(q) > 2 else None))
        static(out, vstep, segs)
    else:
        dyn(out, int(sys.argv[3]), int(sys.argv[4]), float(sys.argv[5]), sys.argv[6])


if __name__ == "__main__":
    main()

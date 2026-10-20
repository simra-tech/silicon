#!/usr/bin/env python3
"""Derived study (behavioural model, not circuit simulation): weight calibration methods G and W (cal3.py) on
the revision-3 array (14 decisions) with MIM mismatch, comparator noise, kT/C noise and a smooth INL bow.
Weights per sample: analytic (array_sweep.weights, 1 %.um MIM model) or AC-solved circuit MC (--mc <bulk dir>).
usage: study_cal3_model.py OUT.json [--mc DIR] [--bow 1.0] [--noise-uV 60] [--ktc-uV 101] [--n 50]
       [--J 4] [--K 4] [--h 8] [--M 8] [--MG 16]
"""
import json
import os
import sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "r2"))
import cal3
import sar2_model as m


def arg(k, d):
    return type(d)(sys.argv[sys.argv.index(k) + 1]) if k in sys.argv else d


out = sys.argv[1]
bow, noise, ktc = arg("--bow", 1.0), arg("--noise-uV", 60.0) * 1e-6, arg("--ktc-uV", 101.0) * 1e-6
n, J, h, M, MG, K = arg("--n", 50), arg("--J", 4), arg("--h", 8), arg("--M", 8), arg("--MG", 16), arg("--K", 4)
rng = np.random.RandomState(20261020)
if "--mc" in sys.argv:
    import importlib.util
    spec = importlib.util.spec_from_file_location("pmc", os.path.join(HERE, "post_cdac3_mc.py"))
    pmc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pmc)
    n, W_all = pmc.parse(arg("--mc", ""))
    samples = [(W_all["p"][i], W_all["n"][i]) for i in range(n)]
    src = "AC-solved circuit MC (cap_typ_mismatch)"
else:
    import array_sweep as asw
    L14 = asw.LSB + [0.5]
    samples = [(asw.weights(1.249, rng, 1, lsb_caps=L14), asw.weights(1.249, rng, 1, lsb_caps=L14)) for _ in range(n)]
    src = "analytic (array_sweep.weights, 1 %.um)"

res = []
for i, (wp, wn) in enumerate(samples):
    fs = m.full_scale(wp, wn)
    lsb = 2 * fs / 4096

    def conv(v, noisy=True):
        v = np.asarray(v, float)
        ve = v + bow * lsb * np.sin(np.pi * v / fs)          # smooth odd bow, amplitude `bow` LSB
        if noisy:
            ve = ve + rng.normal(0, ktc, ve.size)
            return m.convert(ve, wp, wn, noise=noise, rng=rng)
        return m.convert(ve, wp, wn)
    vf = np.arange(-fs * 1.002, fs * 1.002, lsb / 16)
    bf = conv(vf, False)
    r = {"sample": i}
    # method G
    vg = np.linspace(-0.995 * fs, 0.995 * fs, int(4096 * 0.995 * MG))
    Wg = cal3.quantise(cal3.fit_global(conv(vg), np.arange(vg.size)))
    # method W
    vc = np.arange(-0.995 * fs, 0.995 * fs, lsb)
    cen = cal3.locate(vc, conv(vc), J, K=K)
    vw, ww = cal3.windows(cen, lsb, h, M)
    Ww = cal3.quantise(cal3.fit_windowed(conv(vw), vw / lsb * M, ww))
    for tag, W, nconv in (("G", Wg, vg.size), ("W", Ww, vc.size + vw.size)):
        dnl, inl, miss = cal3.dnl_inl(vf, cal3.code(bf, W))
        mj = cal3.major(dnl)
        r[tag] = {"dnl_max": float(np.nanmax(np.abs(dnl))), "inl_max": float(np.nanmax(np.abs(inl))), "missing": miss,
                  "major_dnl": mj, "major_max": max(abs(x) for v in mj.values() for x in v), "conversions": int(nconv),
                  "W": [int(x) for x in W]}
    r["W"]["windows"] = int(len(cen))
    res.append(r)


def summ(tag):
    d = np.array([r[tag]["dnl_max"] for r in res])
    j = np.array([r[tag]["major_max"] for r in res])
    q = np.array([r[tag]["inl_max"] for r in res])
    mi = np.array([r[tag]["missing"] for r in res])
    return {"dnl_max_median": float(np.median(d)), "dnl_max_p90": float(np.percentile(d, 90)), "dnl_max_max": float(d.max()),
            "samples_dnl_le_0p5": int(np.sum(d <= 0.5)), "major_dnl_max_median": float(np.median(j)),
            "major_dnl_max_max": float(j.max()), "samples_major_le_0p5": int(np.sum(j <= 0.5)),
            "inl_max_median": float(np.median(q)), "inl_max_max": float(q.max()),
            "samples_without_missing_codes": int(np.sum(mi == 0)),
            "conversions_per_calibration": int(np.median([r[tag]["conversions"] for r in res]))}


S = {"label": "derived: behavioural SAR + calibration model (sim/r3/cal3.py); weights: " + src,
     "samples": len(res), "bow_lsb": bow, "comparator_noise_uV": noise * 1e6, "ktc_uV": ktc * 1e6,
     "method_G": dict(summ("G"), ramp_conversions_per_lsb=MG),
     "method_W": dict(summ("W"), decisions_located=J + 1, extra_windows_per_decision_5_to_8=K, half_width_lsb=h, conversions_per_lsb=M,
                      windows_median=int(np.median([r["W"]["windows"] for r in res]))),
     "per_sample": res}
json.dump(S, open(out, "w"), indent=1)
print(json.dumps({k: v for k, v in S.items() if k != "per_sample"}, indent=1))

#!/usr/bin/env python3
"""Reference model for r1_adcw (ADC weight correction, PLAN.md D12).

  adcw_ref.py gen   <outdir>   SAR model with a mismatched CDAC -> raw decisions, weights
  adcw_ref.py check <outdir>   RTL codes vs the integer model; DNL/INL with binary and
                               calibrated weights

SAR model (behavioural, not r1_adc): 13 decisions in the order
2048, 1024, 512, 256, 128, 64, R, 32, 16, 8, 4, 2, 1 LSB (R = redundant decision,
nominal 64 LSB). Each decision keeps its capacitor when vin >= sum + W_actual[k]
(add-only search; the redundant step lets a too-small MSB weight be recovered).
The mismatched CDAC example has an MSB 0.20 % small, 1024 0.25 % large, 512
0.15 % small, 256 0.12 % large and the rest with sigma 0.1 % (seed 20261020):
this gives the missing codes and wide codes seen in the r1_adc MC (README open
issue 1). Calibrated weights are round(4 * W_actual), i.e. a perfect bench
measurement quantised to the 1/4-LSB register resolution.
RTL ordering: raw[11:0] binary decisions (raw[11] = 2048), raw[12] = R.
SPDX-License-Identifier: Apache-2.0
"""
import json
import sys

import numpy as np

ORDER = [11, 10, 9, 8, 7, 6, 12, 5, 4, 3, 2, 1, 0]          # raw index of each decision
NOM = {i: float(2 ** i) for i in range(12)}
NOM[12] = 64.0
BIN_W = [4 * 2 ** i for i in range(12)] + [256]                # RTL reset weights


def actual_weights():
    rng = np.random.default_rng(20261020)
    eps = {i: rng.normal(0.0, 0.001) for i in range(13)}
    eps.update({11: -0.0020, 10: +0.0025, 9: -0.0015, 8: +0.0012})
    return {i: NOM[i] * (1.0 + eps[i]) for i in range(13)}


def sar(vin, wa):
    acc, raw = 0.0, 0
    for i in ORDER:
        if vin >= acc + wa[i]:
            acc += wa[i]
            raw |= 1 << i
    return raw


def rtl_code(raw, w):
    s = sum(w[i] for i in range(13) if raw >> i & 1)
    c = (s + 2) >> 2
    return min(c, 4095)


def lin(codes, vin):
    """DNL/INL from a fine ramp: transition levels from the first input reaching each code."""
    codes = np.asarray(codes)
    trans = np.full(4096, np.nan)
    for k in range(1, 4096):
        idx = np.nonzero(codes >= k)[0]
        if len(idx):
            trans[k] = vin[idx[0]]
    t = trans[1:4095]                         # transitions 1..4094
    ok = ~np.isnan(t)
    width = np.diff(t)                        # code widths 1..4093
    dnl = width - 1.0
    present = np.zeros(4096, bool)
    present[np.unique(codes)] = True
    missing = int((~present[1:4095]).sum())
    # INL against the endpoint line through the first and last transitions
    # (offset and gain removed), in LSB of the measured code width
    k = np.arange(1, 4095)
    kk, tt = k[ok], t[ok]
    lsb = (tt[-1] - tt[0]) / (kk[-1] - kk[0])
    inl = (tt - tt[0]) / lsb - (kk - kk[0])
    return dict(max_abs_dnl=float(np.nanmax(np.abs(dnl))), max_abs_inl=float(np.max(np.abs(inl))),
                missing_codes=missing, ramp_step_lsb=0.0625)


def gen(out):
    wa = actual_weights()
    vin = np.arange(0.0, 4096.0, 0.0625)
    raws = [sar(v, wa) for v in vin]
    wcal = [int(round(4 * wa[i])) for i in range(13)]
    with open(f"{out}/adcw_raw.hex", "w") as fh:
        fh.writelines(f"{r:04x}\n" for r in raws)
    for name, w in (("bin", BIN_W), ("cal", wcal)):
        with open(f"{out}/adcw_w_{name}.hex", "w") as fh:
            fh.writelines(f"{x:04x}\n" for x in w)
    json.dump(dict(n=len(vin), w_actual_lsb=[wa[i] for i in range(13)], w_cal=wcal, w_bin=BIN_W),
              open(f"{out}/adcw_meta.json", "w"), indent=1)
    print(f"adcw gen: {len(vin)} ramp points (1/16 LSB step), calibrated weights {wcal}")


def check(out):
    meta = json.load(open(f"{out}/adcw_meta.json"))
    raws = [int(l, 16) for l in open(f"{out}/adcw_raw.hex")]
    vin = np.arange(0.0, 4096.0, 0.0625)
    res, ok = {}, True
    for name in ("bin", "cal"):
        w = meta["w_" + name]
        model = [rtl_code(r, w) for r in raws]
        rtl = [int(l.split()[1]) for l in open(f"{out}/adcw_{name}_out.txt") if l.startswith("C ")]
        mism = sum(1 for a, b in zip(model, rtl) if a != b) + abs(len(model) - len(rtl))
        r = lin(rtl, vin)
        r.update(n=len(rtl), mismatches_vs_model=mism)
        res[name] = r
        ok &= (mism == 0)
    ideal = lin([min(4095, max(0, int(np.floor(v + 0.5)))) for v in vin], vin)
    res["ideal_quantiser"] = ideal
    # Context (model only, not RTL): weight-resolution sweep. Exact float weights
    # do not give DNL <= 0.5: the analog decision levels of a 12-bit SAR with
    # mismatched capacitors are irregular by fractions of an LSB, and a 12-bit
    # output cannot remove that. The criterion is therefore the usual ADC claim:
    # no missing codes, |DNL| < 1, |INL| <= 1.
    wa = {i: v for i, v in enumerate(meta["w_actual_lsb"])}
    sweep = {"exact": lin([min(4095, int(np.floor(sum(wa[i] for i in range(13) if r >> i & 1) + 0.5))) for r in raws], vin)}
    for q in (2, 4, 8, 16):
        wq = [int(round(q * wa[i])) for i in range(13)]
        sweep[f"1/{q}_lsb"] = lin([min(4095, (sum(wq[i] for i in range(13) if r >> i & 1) + q // 2) // q) for r in raws], vin)
    res["model_weight_resolution_sweep"] = sweep
    bin_err = res["bin"]["missing_codes"] > 0 or res["bin"]["max_abs_dnl"] > 1.0
    cal_ok = res["cal"]["missing_codes"] == 0 and res["cal"]["max_abs_dnl"] < 1.0 and res["cal"]["max_abs_inl"] <= 1.0
    res["checks"] = dict(rtl_bit_exact=ok, mismatch_example_shows_error_with_binary_weights=bin_err,
                         calibrated_no_missing_dnl_lt_1_inl_le_1=cal_ok)
    res["passed"] = bool(ok and bin_err and cal_ok)
    json.dump(res, open(f"{out}/adcw_result.json", "w"), indent=1)
    print(json.dumps(res, indent=1))
    print("ALL TESTS PASSED" if res["passed"] else "TESTS FAILED")


if __name__ == "__main__":
    {"gen": gen, "check": check}[sys.argv[1]](sys.argv[2])

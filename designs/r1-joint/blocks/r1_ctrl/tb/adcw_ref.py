#!/usr/bin/env python3
"""Reference model for r1_adcw (ADC weight correction, PLAN.md D12).

  adcw_ref.py gen   <outdir>   SAR model with a mismatched CDAC -> raw decisions, weights
  adcw_ref.py check <outdir>   RTL codes vs the integer model; DNL/INL with binary and
                               calibrated weights

SAR model (behavioural, not r1_adc), revision 0.3 (D18): 14 decisions per
slice in the order raw[13] (first) .. raw[0], nominal weights of r1_adc
revision 3 (2032.4, 1016.3, 507.9, 253.9, 127.0, 78.8, 39.4, 19.7, 9.85, 4.93,
2.46, 1.23, 0.62, 0.31 LSB; sub-binary with redundancy). Each decision keeps
its capacitor when vin >= sum + W_actual[k] (add-only search). The mismatched
CDAC example has the first decision 0.20 % small, the second 0.25 % large, the
third 0.15 % small, the fourth 0.12 % large and the rest with sigma 0.1 % (seed
20261020). 'nom' = the RTL reset weights round(4 * nominal); 'cal' =
round(4 * W_actual), i.e. a perfect bench measurement quantised to the 1/4-LSB
register resolution. One r1_adcw instance per slice; both are the same module.
SPDX-License-Identifier: Apache-2.0
"""
import json
import sys

import numpy as np

ND = 14
ORDER = list(range(ND - 1, -1, -1))                            # raw index of each decision
NOM_L = [0.31, 0.62, 1.23, 2.46, 4.93, 9.85, 19.7, 39.4, 78.8, 127.0, 253.9, 507.9, 1016.3, 2032.4]
NOM = {i: NOM_L[i] for i in range(ND)}
NOM_W = [8130, 4065, 2032, 1016, 508, 315, 158, 79, 39, 20, 10, 5, 2, 1][::-1]   # RTL reset weights


def actual_weights():
    rng = np.random.default_rng(20261020)
    eps = {i: rng.normal(0.0, 0.001) for i in range(ND)}
    eps.update({13: -0.0020, 12: +0.0025, 11: -0.0015, 10: +0.0012})
    return {i: NOM[i] * (1.0 + eps[i]) for i in range(ND)}


def sar(vin, wa):
    acc, raw = 0.0, 0
    for i in ORDER:
        if vin >= acc + wa[i]:
            acc += wa[i]
            raw |= 1 << i
    return raw


def rtl_code(raw, w):
    s = sum(w[i] for i in range(ND) if raw >> i & 1)
    c = (s + 2) >> 2
    return min(c, 4095)


def lin(codes, vin, hi=4094):
    """DNL/INL from a fine ramp: transition levels from the first input reaching each code.
    Missing codes are counted in 1..hi (hi < 4094 when the array full scale is below 4095 LSB:
    a gain error, not a DNL error; revision 0.3, D18 weights sum to 4094.8 LSB nominal)."""
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
    missing = int((~present[1:hi + 1]).sum())
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
    wcal = [int(round(4 * wa[i])) for i in range(ND)]
    with open(f"{out}/adcw_raw.hex", "w") as fh:
        fh.writelines(f"{r:04x}\n" for r in raws)
    for name, w in (("nom", NOM_W), ("cal", wcal)):
        with open(f"{out}/adcw_w_{name}.hex", "w") as fh:
            fh.writelines(f"{x:04x}\n" for x in w)
    json.dump(dict(n=len(vin), w_actual_lsb=[wa[i] for i in range(ND)], w_cal=wcal, w_nom=NOM_W),
              open(f"{out}/adcw_meta.json", "w"), indent=1)
    print(f"adcw gen: {len(vin)} ramp points (1/16 LSB step), calibrated weights {wcal}")


def check(out):
    meta = json.load(open(f"{out}/adcw_meta.json"))
    raws = [int(l, 16) for l in open(f"{out}/adcw_raw.hex")]
    vin = np.arange(0.0, 4096.0, 0.0625)
    res, ok = {}, True
    fs = sum(meta["w_actual_lsb"])                 # analog full scale of the example array (LSB)
    hi = min(4094, int(np.floor(fs + 0.5)) - 1)
    res["array_full_scale_lsb"] = fs
    for name in ("nom", "cal"):
        w = meta["w_" + name]
        model = [rtl_code(r, w) for r in raws]
        rtl = [int(l.split()[1]) for l in open(f"{out}/adcw_{name}_out.txt") if l.startswith("C ")]
        mism = sum(1 for a, b in zip(model, rtl) if a != b) + abs(len(model) - len(rtl))
        r = lin(rtl, vin, hi)
        r.update(n=len(rtl), mismatches_vs_model=mism, missing_code_range=[1, hi])
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
    sweep = {"exact": lin([min(4095, int(np.floor(sum(wa[i] for i in range(ND) if r >> i & 1) + 0.5))) for r in raws], vin)}
    for q in (2, 4, 8, 16):
        wq = [int(round(q * wa[i])) for i in range(ND)]
        sweep[f"1/{q}_lsb"] = lin([min(4095, (sum(wq[i] for i in range(ND) if r >> i & 1) + q // 2) // q) for r in raws], vin)
    res["model_weight_resolution_sweep"] = sweep
    nom_err = res["nom"]["missing_codes"] > 0 or res["nom"]["max_abs_dnl"] > 1.0
    cal_ok = res["cal"]["missing_codes"] == 0 and res["cal"]["max_abs_dnl"] < 1.0 and res["cal"]["max_abs_inl"] <= 1.0
    res["checks"] = dict(rtl_bit_exact=ok, mismatch_example_shows_error_with_nominal_weights=nom_err,
                         calibrated_no_missing_dnl_lt_1_inl_le_1=cal_ok)
    res["passed"] = bool(ok and nom_err and cal_ok)
    json.dump(res, open(f"{out}/adcw_result.json", "w"), indent=1)
    print(json.dumps(res, indent=1))
    print("ALL TESTS PASSED" if res["passed"] else "TESTS FAILED")


if __name__ == "__main__":
    {"gen": gen, "check": check}[sys.argv[1]](sys.argv[2])

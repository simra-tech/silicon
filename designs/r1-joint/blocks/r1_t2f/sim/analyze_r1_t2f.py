#!/usr/bin/env python3
"""Tables for the R1_T2F README from results/{ftemp,supply,corners}_<run-id>.json (host Python 3.6, no simulator).
Writes results/summary.json and results/tables.md. All numbers are simulated."""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
RID = os.environ.get("R1_T2F_RUN_ID", "20261020-a")
CLK_NOM = 30e6
CLK_LO, CLK_HI = 23e6, 39e6
G1 = {"f25": 1.5898e6, "slope": 5.217e3, "sup_ptat_ppmV": -8394, "sup_ref_ppmV": -8275}


def load(s):
    p = os.path.join(RES, "%s_%s.json" % (s, RID))
    return json.load(open(p)) if os.path.exists(p) else {}


def T(n):
    return float(re.search(r"_T(-?\d+)", n).group(1))


ft, sp, co = load("ftemp"), load("supply"), load("corners")
RIDB = "20261020-b"   # retry of the -40 C / 3.6 V corner decks with tight options
pb = os.path.join(RES, "tight_%s.json" % RIDB)
if os.path.exists(pb):
    for k, v in json.load(open(pb)).items():
        if v.get("freq"):
            co[k] = v
out, summ = [], {}
fp = {T(n): r["freq"] for n, r in ft.items() if "_ptat_" in n and "freq" in r}
fr = {T(n): r["freq"] for n, r in ft.items() if "_ref_" in n and "freq" in r}
ts = sorted(fp)
n = len(ts)
mt, mf = sum(ts) / n, sum(fp[t] for t in ts) / n
slope = sum((t - mt) * (fp[t] - mf) for t in ts) / sum((t - mt) ** 2 for t in ts)
icpt = mf - slope * mt
loc = [(fp[b] - fp[a]) / (b - a) for a, b in zip(ts, ts[1:])]
summ["slope_LS_Hz_per_C"] = slope
summ["local_slope_min_max_Hz_per_C"] = [min(loc), max(loc)]
summ["f_ptat_Hz"] = fp
summ["f_ref_Hz"] = fr
out.append("### f(T), 3.3 V, tt (simulated)\n")
out.append("| T [C] | f PTAT [MHz] | f REF [MHz] | f_PTAT/f_REF | I(3.3 V) [uA] | I(1.2 V) [uA] | V_REF [V] | fit residual [C] |")
out.append("| --- | --- | --- | --- | --- | --- | --- | --- |")
for t in ts:
    r = ft["ftemp_ptat_vdd3.3_T%d" % t]
    rr = fr.get(t)
    ref = ft.get("ftemp_ref_vdd3.3_T%d" % t)
    res = (fp[t] - icpt) / slope - t
    out.append("| %g | %.4f | %s | %s | %.1f | %.2f | %.4f | %+.2f |" % (
        t, fp[t] / 1e6, "%.4f" % (rr / 1e6) if rr else "not run", "%.4f" % (fp[t] / rr) if rr else "not run",
        abs(r["i33_avg"]) * 1e6, abs(r["i12_avg"]) * 1e6, r["vref_avg"], res))
out.append("\nLeast-squares slope over %g..%g C: %.3f kHz/C; local slope %.3f .. %.3f kHz/C; fit residual of one straight line %+.2f .. %+.2f C.\n" % (
    ts[0], ts[-1], slope / 1e3, min(loc) / 1e3, max(loc) / 1e3, min((fp[t] - icpt) / slope - t for t in ts), max((fp[t] - icpt) / slope - t for t in ts)))
if 27 in fp:
    summ["f27_Hz"] = fp[27]

out.append("### Supply sensitivity (simulated)\n")
out.append("| mode | T [C] | f at 3.0 V [MHz] | 3.3 V | 3.6 V | sensitivity [ppm/V] | [kHz/V] | [C/V] | I(VDDA) 3.0/3.3/3.6 V [uA] |")
out.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- |")
summ["supply"] = {}
for m, tt in (("ptat", 27), ("ptat", 125), ("ref", 27)):
    f, cur = {}, {}
    for v in ("3.0", "3.3", "3.6"):
        key = ("supply_%s_vdd%s_T%d" % (m, v, tt)) if v != "3.3" else ("ftemp_%s_vdd3.3_T%d" % (m, tt))
        if key in sp or key in ft:
            r = (sp.get(key) or ft.get(key))
            f[v], cur[v] = r.get("freq"), abs(r.get("i33_avg", float("nan"))) * 1e6
    if len(f) == 3 and all(f.values()):
        s = (f["3.6"] - f["3.0"]) / f["3.3"] / 0.6 * 1e6
        dk = (f["3.6"] - f["3.0"]) / 0.6 / 1e3
        # C/V: PTAT -> f proportional to T (slope in Hz/C); REF -> equivalent shift versus PTAT slope
        cv = (f["3.6"] - f["3.0"]) / 0.6 / slope
        out.append("| %s | %d | %.4f | %.4f | %.4f | %.0f | %.2f | %+.2f | %.1f / %.1f / %.1f |" % (
            m.upper(), tt, f["3.0"] / 1e6, f["3.3"] / 1e6, f["3.6"] / 1e6, s, dk, cv, cur["3.0"], cur["3.3"], cur["3.6"]))
        summ["supply"]["%s_T%d" % (m, tt)] = {"f_Hz": f, "ppm_per_V": s, "kHz_per_V": dk, "C_per_V": cv, "I_uA": cur}
    else:
        out.append("| %s | %d | not run (incomplete) | | | | | | |" % (m.upper(), tt))
out.append("\n[C/V] divides the frequency change per volt by the simulated PTAT slope (LS, kHz/C above).\n")

out.append("### Process corners at 3.0 and 3.6 V, PTAT (simulated; ss = hbt_wcs+mos_ss+res_wcs, ff = hbt_bcs+mos_ff+res_bcs)\n")
out.append("| corner | VDDA [V] | f(-40 C) [MHz] | f(27 C) | f(125 C) | slope -40..125 C [kHz/C] | note |")
out.append("| --- | --- | --- | --- | --- | --- | --- |")
summ["corners"] = {}
for c in ("ss", "tt", "ff"):
    for v in ("3.0", "3.6"):
        f = {t: (co.get("corners_ptat_%s_vdd%s_T%d" % (c, v, t)) or {}).get("freq") for t in (-40, 27, 125)}
        sl = (f[125] - f[-40]) / 165 / 1e3 if f[125] and f[-40] else None
        out.append("| %s | %s | %s | %s | %s | %s | %s |" % (c, v, *[("%.4f" % (f[t] / 1e6)) if f[t] else "not run" for t in (-40, 27, 125)], "%.3f" % sl if sl else "not run", "-40 C point: tight options (retry)" if v == "3.6" and f[-40] else ""))
        summ["corners"]["%s_%s" % (c, v)] = {"f_Hz": f, "slope_kHz_per_C": sl}

out.append("\n### TEMP_COUNT resolution (simulated f; slope %.3f kHz/C, least squares)\n" % (slope / 1e3))
out.append("Method A: count T2F rising edges in a gate of N cycles of the 30 MHz clock. count = N x f_T2F / f_clk.\n")
out.append("| N [clk cycles] | gate at 30 MHz | count at -40 C | 27 C | 125 C | LSB [Hz] | LSB [C] (+/-1 count) | gate at 23 / 39 MHz clock |")
out.append("| --- | --- | --- | --- | --- | --- | --- | --- |")
summ["count_A"] = {}
for k in (14, 16, 18):
    N = 2 ** k
    g = N / CLK_NOM
    cnt = {t: fp[t] * g for t in (-40, 27, 125) if t in fp}
    lsb = 1 / g
    out.append("| 2^%d = %d | %.3f ms | %.0f | %.0f | %.0f | %.0f | %.3f | %.3f / %.3f ms |" % (
        k, N, g * 1e3, cnt[-40], cnt[27], cnt[125], lsb, lsb / slope, N / CLK_LO * 1e3, N / CLK_HI * 1e3))
    summ["count_A"]["2^%d" % k] = {"gate_s": g, "counts": cnt, "LSB_Hz": lsb, "LSB_C": lsb / slope}
out.append("\nMethod B: count 30 MHz clock cycles over K T2F periods (reciprocal count). count = K x f_clk / f_T2F.\n")
out.append("| K [T2F periods] | gate at -40 / 27 / 125 C [ms] | count at -40 C | 27 C | 125 C | LSB [C] at -40 / 27 / 125 C (+/-1 count) |")
out.append("| --- | --- | --- | --- | --- | --- |")
summ["count_B"] = {}
for k in (10, 12, 14):
    K = 2 ** k
    cnt = {t: K * CLK_NOM / fp[t] for t in (-40, 27, 125) if t in fp}
    # one count changes f by f/count; degC = that over local slope (use LS slope)
    lsbC = {t: fp[t] / cnt[t] / slope for t in cnt}
    gate = {t: K / fp[t] * 1e3 for t in cnt}
    out.append("| 2^%d = %d | %.3f / %.3f / %.3f | %.0f | %.0f | %.0f | %.3f / %.3f / %.3f |" % (
        k, K, gate[-40], gate[27], gate[125], cnt[-40], cnt[27], cnt[125], lsbC[-40], lsbC[27], lsbC[125]))
    summ["count_B"]["2^%d" % k] = {"counts": cnt, "LSB_C": lsbC, "gate_ms": gate}
if fr and 27 in fr:
    rs = (fp[125] / fr[125] - fp[-40] / fr[-40]) / 165
    summ["ratio_slope_per_C"] = rs
    out.append("\nRatio readout: f_PTAT/f_REF changes by %.5f per C (mean over -40..125 C, simulated). One count in each of two counts N_P, N_R (method A, 2^16 window: N_P = %.0f, N_R = %.0f at 27 C) gives a ratio step of about %.5f, i.e. about %.2f C (worst case, both counts +/-1)." % (
        rs, fp[27] * 2 ** 16 / CLK_NOM, fr[27] * 2 ** 16 / CLK_NOM,
        (1 / (fp[27] * 2 ** 16 / CLK_NOM) + 1 / (fr[27] * 2 ** 16 / CLK_NOM)) * fp[27] / fr[27], (1 / (fp[27] * 2 ** 16 / CLK_NOM) + 1 / (fr[27] * 2 ** 16 / CLK_NOM)) * fp[27] / fr[27] / rs))
open(os.path.join(RES, "tables.md"), "w").write("\n".join(out) + "\n")
json.dump(summ, open(os.path.join(RES, "summary.json"), "w"), indent=1, sort_keys=True)
print("\n".join(out))

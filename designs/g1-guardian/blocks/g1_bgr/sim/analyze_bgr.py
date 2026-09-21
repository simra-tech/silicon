#!/usr/bin/env python3
"""Turn results/*_summary.csv of run_bgr.py into the Markdown tables of the README
(written to results/tables.md). Host-side, no simulator needed."""
import csv, os, statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")


def load(name):
    p = os.path.join(RES, f"{name}_summary.csv")
    if not os.path.exists(p):
        return []
    rows = list(csv.DictReader(open(p)))
    for r in rows:
        for k, v in r.items():
            if k != "deck":
                try:
                    r[k] = float(v)
                except ValueError:
                    r[k] = None
    return rows


out = []
# ---------------- temperature / corners ----------------
temp = [r for r in load("temp") if "_r4_" not in r["deck"]]
if temp:
    out.append("### V_REF(T), -40 to 175 C in 5 C steps, 27 process corners x 3 supplies (simulated)\n")
    out.append("| HBT | RES | V_REF 27 C [V] (mos_tt, 3.3 V) | V_REF 27 C range, all MOS/VDD [V] | TC box -40..125 C [ppm/C] min..max | TC box -40..175 C [ppm/C] min..max | I_PTAT 27 C [uA] (tt, 3.3 V) |")
    out.append("| --- | --- | --- | --- | --- | --- | --- |")
    for h in ("hbt_typ", "hbt_bcs", "hbt_wcs"):
        for rc in ("res_typ", "res_bcs", "res_wcs"):
            sel = [r for r in temp if f"_{h}_" in r["deck"] and f"_{rc}_" in r["deck"]]
            nom = [r for r in sel if "mos_tt" in r["deck"] and r["deck"].endswith("_3.3")][0]
            v27 = [r["v27"] for r in sel]
            ti = [r["tc_ind"] for r in sel]
            tf = [r["tc_full"] for r in sel]
            out.append(f"| {h} | {rc} | {nom['v27']:.4f} | {min(v27):.4f} .. {max(v27):.4f} | {min(ti):.1f} .. {max(ti):.1f} | {min(tf):.1f} .. {max(tf):.1f} | {abs(nom['ip27'])*1e6:.3f} |")
    allv = [r["v27"] for r in temp]
    out.append(f"\nAll 81 runs: V_REF(27 C) = {min(allv):.4f} .. {max(allv):.4f} V; TC box -40..125 C = {min(r['tc_ind'] for r in temp):.1f} .. {max(r['tc_ind'] for r in temp):.1f} ppm/C; -40..175 C = {min(r['tc_full'] for r in temp):.1f} .. {max(r['tc_full'] for r in temp):.1f} ppm/C.\n")
    nom = [r for r in temp if r["deck"] == "temp_hbt_typ_mos_tt_res_typ_3.3"][0]
    out.append("### Nominal (hbt_typ, mos_tt, res_typ, 3.3 V)\n")
    out.append("| T [C] | -40 | 27 | 85 | 125 | 150 | 175 |\n| --- | --- | --- | --- | --- | --- | --- |")
    out.append(f"| V_REF [V] | {nom['vm40']:.4f} | {nom['v27']:.4f} | {nom['v85']:.4f} | {nom['v125']:.4f} | {nom['v150']:.4f} | {nom['v175']:.4f} |")
    out.append(f"| I_PTAT [uA] | {abs(nom['ipm40'])*1e6:.3f} | {abs(nom['ip27'])*1e6:.3f} | - | {abs(nom['ip125'])*1e6:.3f} | - | {abs(nom['ip175'])*1e6:.3f} |")
    out.append(f"| total current [uA] | - | {nom['itot27']*1e6:.1f} | - | - | - | {nom['itot175']*1e6:.1f} |")
    out.append(f"\ndelta-V_BE at 27 C = {nom['dvbe27']*1e3:.2f} mV (ideal kT/q ln 8 = 53.7 mV).\n")
    sup = {r["deck"][-3:]: r["v27"] for r in temp if "hbt_typ_mos_tt_res_typ" in r["deck"]}
    out.append(f"Supply: V_REF(27 C) = {sup['3.0']:.5f} / {sup['3.3']:.5f} / {sup['3.6']:.5f} V at 3.0 / 3.3 / 3.6 V.\n")
    r4 = load("temp")
    r4 = [r for r in r4 if "_r4_" in r["deck"]]
    if r4:
        r = r4[0]
        out.append(f"Ratio test mode (r4=1, 2:8 = 1:4): V_REF(27 C) = {r['v27']:.4f} V, I_PTAT = {abs(r['ip27'])*1e6:.3f} uA, delta-V_BE = {r['dvbe27']*1e3:.2f} mV (ideal kT/q ln 4 = 35.8 mV).\n")
# ---------------- extrapolation ----------------
ext = load("extrap")
if ext:
    out.append("### Cryogenic run, MODEL EXTRAPOLATED (PDK cards are not characterised below -40 C; numbers are not a prediction)\n")
    out.append("| HBT corner | V_REF -196 C | -150 C | -100 C | -40 C | I_PTAT -196 C [uA] | V_BE -196 C | delta-V_BE -196 C [mV] |\n| --- | --- | --- | --- | --- | --- | --- | --- |")
    for r in ext:
        out.append(f"| {r['deck'].split('_')[1]}_{r['deck'].split('_')[2]} | {r['vm196']:.4f} | {r['vm150']:.4f} | {r['vm100']:.4f} | {r['vm40']:.4f} | {abs(r['ipm196'])*1e6:.3f} | {r['vbem196']:.3f} | {r['dvbem196']*1e3:.2f} |")
    out.append("")
# ---------------- PSRR ----------------
ps = load("psrr")
if ps:
    out.append("### PSRR (AC, V_REF/V_DD), 27 process corners x 3 temperatures, 3.3 V\n")
    out.append("| | DC (1 Hz) | 1 kHz | 100 kHz | 1 MHz |\n| --- | --- | --- | --- | --- |")
    nom = [r for r in ps if r["deck"] == "psrr_hbt_typ_mos_tt_res_typ_T27_3.3"][0]
    out.append(f"| nominal 27 C [dB] | {nom['psrr_dc']:.1f} | {nom['psrr_1k']:.1f} | {nom['psrr_100k']:.1f} | {nom['psrr_1m']:.1f} |")
    out.append("| worst of 81 runs [dB] | " + " | ".join(f"{max(r[k] for r in ps):.1f}" for k in ("psrr_dc", "psrr_1k", "psrr_100k", "psrr_1m")) + " |")
    out.append("")
# ---------------- MC ----------------
mc = load("mc")
if mc:
    v = [r["vref"] for r in mc]
    ip = [abs(r["iptat"]) for r in mc]
    dv = [r["dvbe"] for r in mc]
    out.append(f"### Monte Carlo, {len(mc)} samples, hbt_typ_mismatch + mos_tt_mismatch + res_typ_mismatch, 27 C, 3.3 V\n")
    out.append("| quantity | mean | sigma | sigma / mean | min | max |\n| --- | --- | --- | --- | --- | --- |")
    out.append(f"| V_REF [V] | {st.mean(v):.4f} | {st.pstdev(v)*1e3:.1f} mV | {100*st.pstdev(v)/st.mean(v):.2f} % | {min(v):.4f} | {max(v):.4f} |")
    out.append(f"| I_PTAT [uA] | {st.mean(ip)*1e6:.3f} | {st.pstdev(ip)*1e6:.3f} | {100*st.pstdev(ip)/st.mean(ip):.2f} % | {min(ip)*1e6:.3f} | {max(ip)*1e6:.3f} |")
    out.append(f"| delta-V_BE [mV] | {st.mean(dv)*1e3:.2f} | {st.pstdev(dv)*1e3:.2f} | {100*st.pstdev(dv)/st.mean(dv):.2f} % | {min(dv)*1e3:.2f} | {max(dv)*1e3:.2f} |")
    out.append("")
# ---------------- start-up ----------------
for name, label in (("startup", "1 ms supply ramp to 3.0 V, 3 ms simulated, 27 corners x {-40, 27, 175} C"),
                    ("startupslow", "100 ms supply ramp to 3.0 V, 130 ms simulated, 27 corners at 27 C + typ at -40/175 C")):
    su = load(name)
    if su:
        ok = [r for r in su if r.get("vref_end") and 0.9 < r["vref_end"] < 1.2 and r.get("iptat_end") and abs(r["iptat_end"]) > 1e-6]
        out.append(f"### Start-up, {label}\n")
        out.append(f"{len(ok)} of {len(su)} runs end with 0.9 V < V_REF < 1.2 V and |I_PTAT| > 1 uA (no stuck zero state). "
                   f"V_REF at the end: {min(r['vref_end'] for r in su):.4f} .. {max(r['vref_end'] for r in su):.4f} V. "
                   f"Time to V_REF = 0.93 V: {min(r['t_90'] for r in su if r.get('t_90'))*1e3:.3f} .. {max(r['t_90'] for r in su if r.get('t_90'))*1e3:.3f} ms after the ramp starts. "
                   f"Overshoot: max V_REF {max(r['vref_max'] for r in su):.4f} V.\n")
        bad = [r["deck"] for r in su if r not in ok]
        if bad:
            out.append("Failed: " + ", ".join(bad) + "\n")
open(os.path.join(RES, "tables.md"), "w").write("\n".join(out) + "\n")
print("\n".join(out))

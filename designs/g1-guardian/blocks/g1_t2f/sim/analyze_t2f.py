#!/usr/bin/env python3
"""Turn results/*_summary.csv of run_t2f.py into README tables (results/tables.md):
f(T) in both modes, two-point (25/100 C) fit residuals in degrees, supply sensitivity,
corner spread, current, and the V_CE check of every comparator HBT (revision 2 against the
superseded revision 1 when results/vce_rev1_summary.csv exists). Host-side, no simulator needed."""
import csv, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")


def load(name):
    p = os.path.join(RES, f"{name}_summary.csv")
    rows = list(csv.DictReader(open(p))) if os.path.exists(p) else []
    for r in rows:
        for k, v in r.items():
            if k != "deck":
                try:
                    r[k] = float(v)
                except ValueError:
                    r[k] = None
    return rows


def temp_of(deck):
    return float(re.search(r"_T(-?\d+)", deck).group(1))


def fmt(x, spec):
    return format(x, spec) if isinstance(x, float) and x == x else "-"


def two_point(pts, t1=25.0, t2=100.0):
    """pts: {T: y}. Line through (t1, y1) and (t2, y2); returns residual T_est - T per point."""
    a = (pts[t2] - pts[t1]) / (t2 - t1)
    b = pts[t1] - a * t1
    return a, b, {t: (y - b) / a - t for t, y in pts.items()}


out = []
ft = load("ftemp")
if ft:
    fp = {temp_of(r["deck"]): r["freq"] for r in ft if "_ptat_" in r["deck"] and r.get("freq")}
    fr = {temp_of(r["deck"]): r["freq"] for r in ft if "_ref_" in r["deck"] and r.get("freq")}
    ratio = {t: fp[t] / fr[t] for t in fp if t in fr}
    ap, bp, rp = two_point(fp)
    ar, br, rr = two_point(ratio)
    ip = {temp_of(r["deck"]): r for r in ft if "_ptat_" in r["deck"]}
    out.append("### f(T), nominal corner (hbt_typ, mos_tt, res_typ, cap_typ), 3.3 V / 1.2 V (simulated transient, period averaged over 20 cycles)\n")
    out.append("| T [C] | f PTAT [MHz] | f REF [MHz] | f_PTAT / f_REF | two-point fit residual, f PTAT [C] | two-point fit residual, ratio [C] | I(3.3 V) [uA] | V_REF [V] | cap peak - V_th [mV] |")
    out.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for t in sorted(fp):
        r = ip[t]
        out.append(f"| {t:g} | {fp[t]/1e6:.4f} | {fmt(fr.get(t, float('nan'))/1e6, '.4f')} | {fmt(ratio.get(t, float('nan')), '.4f')} | {rp[t]:+.2f} | {fmt(rr.get(t, float('nan')), '+.2f')} | {abs(r['i33_avg'])*1e6:.1f} | {r['vref_avg']:.4f} | {(r['cap1_max']-r['vth_avg'])*1e3:.1f} |")
    out.append(f"\nPTAT mode: slope of the 25/100 C line {ap/1e3:.3f} kHz/C ({ap/fp[25.0]*1e6:.0f} ppm/C of f(25 C)); f(25 C) = {fp[25.0]/1e6:.4f} MHz.")
    r40_150 = [rp[t] for t in rp if -40 <= t <= 150]
    rr40_150 = [rr[t] for t in rr if -40 <= t <= 150]
    out.append(f"Two-point (25 C, 100 C) fit residual over -40..150 C: f PTAT {min(r40_150):+.2f} .. {max(r40_150):+.2f} C; ratio f_PTAT/f_REF {min(rr40_150):+.2f} .. {max(rr40_150):+.2f} C. Over -40..175 C: f PTAT {min(rp.values()):+.2f} .. {max(rp.values()):+.2f} C; ratio {min(rr.values()):+.2f} .. {max(rr.values()):+.2f} C.\n")
    out.append(f"REF mode: f = {min(fr.values())/1e6:.4f} .. {max(fr.values())/1e6:.4f} MHz over -40..175 C ({(max(fr.values())-min(fr.values()))/fr[25.0]*1e6/215:.0f} ppm/C box).\n")
sp = load("supply")
if sp:
    out.append("### Supply sensitivity, 27 C, nominal corner\n")
    out.append("| mode | f at 3.0 V | 3.3 V | 3.6 V [MHz] | sensitivity [ppm/V] | equivalent [C/V] |\n| --- | --- | --- | --- | --- | --- |")
    for m in ("ptat", "ref"):
        f = {re.search(r"vdd(\d\.\d)", r["deck"]).group(1): r["freq"] for r in sp if f"_{m}_vdd" in r["deck"] and "vdd12" not in r["deck"]}
        s = (f["3.6"] - f["3.0"]) / f["3.3"] / 0.6 * 1e6
        out.append(f"| {m.upper()} | {f['3.0']/1e6:.4f} | {f['3.3']/1e6:.4f} | {f['3.6']/1e6:.4f} | {s:.0f} | {s*1e-6*300:.2f} |")
    f12 = {re.search(r"vdd12_(\d\.\d+)", r["deck"]).group(1): r["freq"] for r in sp if "vdd12_" in r["deck"]}
    f33 = [r["freq"] for r in sp if r["deck"] == "supply_ptat_vdd3.3_T27"][0]
    if f12:
        out.append(f"\n1.2 V domain (output level shifter only): f PTAT = {f12['1.08']/1e6:.4f} MHz at 1.08 V, {f33/1e6:.4f} at 1.20 V, {f12['1.32']/1e6:.4f} at 1.32 V.\n")
    out.append("Equivalent [C/V] uses f proportional to absolute temperature (300 K at 27 C).\n")
co = load("corners")
if co:
    out.append("### Corner spread at 27 C (f PTAT), 8 extreme process corners (hbt bcs/wcs x mos ss/ff x res bcs/wcs) + nominal, cap_typ, plus cap corners\n")
    proc = [r for r in co if "_ptat_" in r["deck"] and "cap_typ_T27" in r["deck"]]
    f = [r["freq"] for r in proc if r.get("freq")]
    nom = [r["freq"] for r in proc if "hbt_typ_mos_tt_res_typ" in r["deck"]][0]
    out.append(f"9 process corners: f PTAT = {min(f)/1e6:.4f} .. {max(f)/1e6:.4f} MHz ({(min(f)/nom-1)*100:+.1f} % .. {(max(f)/nom-1)*100:+.1f} % of nominal {nom/1e6:.4f} MHz); {len(f)} of {len(proc)} runs oscillate.\n")
    out.append("| corner | f PTAT [MHz] | f REF [MHz] | ratio |\n| --- | --- | --- | --- |")
    for tag in ("hbt_typ_mos_tt_res_typ_cap_typ", "hbt_bcs_mos_ff_res_bcs_cap_typ", "hbt_wcs_mos_ss_res_wcs_cap_typ", "hbt_typ_mos_tt_res_typ_cap_bcs", "hbt_typ_mos_tt_res_typ_cap_wcs"):
        p = [r["freq"] for r in co if r["deck"] == f"corners_ptat_{tag}_T27"]
        q = [r["freq"] for r in co if r["deck"] == f"corners_ref_{tag}_T27"]
        if p:
            out.append(f"| {tag} | {p[0]/1e6:.4f} | {fmt(q[0]/1e6 if q and q[0] else float('nan'), '.4f')} | {fmt(p[0]/q[0] if q and q[0] else float('nan'), '.4f')} |")
    out.append("\nExtreme corners over temperature (f PTAT):\n")
    out.append("| corner | f(-40 C) | f(27 C) | f(175 C) [MHz] | slope -40..175 vs nominal |\n| --- | --- | --- | --- | --- |")
    nomT = {t: [r["freq"] for r in load("ftemp") if r["deck"] == f"ftemp_ptat_T{t}"][0] for t in (-40, 175)}
    for tag in ("hbt_bcs_mos_ff_res_bcs", "hbt_wcs_mos_ss_res_wcs"):
        fx = {t: [r["freq"] for r in co if r["deck"] == f"corners_ptat_{tag}_cap_typ_T{t}"] for t in (-40, 27, 175)}
        if all(fx.values()):
            sl = (fx[175][0] - fx[-40][0]) / (nomT[175] - nomT[-40])
            out.append(f"| {tag} | {fx[-40][0]/1e6:.4f} | {fx[27][0]/1e6:.4f} | {fx[175][0]/1e6:.4f} | {sl:.3f} |")
    out.append("")
ex = load("extrap")
if ex:
    out.append("### Cryogenic run, MODEL EXTRAPOLATED (not a prediction: the PDK HBT cards are not characterised below -40 C and the measured SG13G2 ideality factor departs strongly below ~100 K)\n")
    out.append("| T [C] | mode | f [MHz] | f / f(27 C) | (T / 300 K) for comparison |\n| --- | --- | --- | --- | --- |")
    f27 = [r["freq"] for r in load("ftemp") if r["deck"] == "ftemp_ptat_T27"]
    f27 = f27[0] if f27 else float("nan")
    for r in sorted(ex, key=lambda r: temp_of(r["deck"])):
        t = temp_of(r["deck"])
        fq = r.get("freq")
        out.append(f"| {t:g} | {'REF' if '_ref_' in r['deck'] else 'PTAT'} | {fmt(fq/1e6, '.4f') if fq else 'no oscillation within the run'} | {fmt(fq/f27, '.3f') if fq else '-'} | {(t+273.15)/300.15:.3f} |")
    out.append("")
vc, vr1 = load("vce"), load("vce_rev1")
if vc:
    out.append("### V_CE of the comparator HBTs (vce suite: whole run including the en=0 hold; min over the oscillation), model card vce_max = 1.6 V\n")
    out.append("| condition | mode | revision | max V_CE QA1 / QB1 / QA2 / QB2 [V] | min V_CE (oscillating) QA1 / QB1 [V] | f [MHz] | V_th [V] |")
    out.append("| --- | --- | --- | --- | --- | --- | --- |")
    def row(r, label):
        mx = " / ".join(fmt(r.get(k, float("nan")), ".2f") for k in ("vce_qa1_max", "vce_qb1_max", "vce_qa2_max", "vce_qb2_max"))
        mn = " / ".join(fmt(r.get(k, float("nan")), ".2f") for k in ("vce_qa1_min", "vce_qb1_min"))
        fq = r.get("freq")
        return f"| {label} | {'REF' if '_ref_' in r['deck'] else 'PTAT'} | {'1 (superseded)' if r['deck'].startswith('vce_rev1') else '2'} | {mx} | {mn} | {fmt(fq / 1e6 if fq else float('nan'), '.4f')} | {fmt(r.get('vth_avg', float('nan')), '.4f')} |"
    for cond, label in (("vdd3.6_T175", "3.6 V, 175 C"), ("vdd3.0_T-40", "3.0 V, -40 C"), ("vdd3.3_T27", "3.3 V, 27 C")):
        for m in ("ptat", "ref"):
            for rows_, tag in ((vc, "vce"), (vr1, "vce_rev1")):
                for r in rows_:
                    if r["deck"] == f"{tag}_{m}_{cond}":
                        out.append(row(r, label))
    allmax = max(r[k] for r in vc for k in ("vce_qa1_max", "vce_qb1_max", "vce_qa2_max", "vce_qb2_max") if r.get(k) is not None)
    out.append(f"\nRevision 2: max V_CE of any comparator HBT over the six runs = {allmax:.2f} V.")
    if vr1:
        allmax1 = max(r[k] for r in vr1 for k in ("vce_qa1_max", "vce_qb1_max", "vce_qa2_max", "vce_qb2_max") if r.get(k) is not None)
        out.append(f"Revision 1 (same decks on rev1/xschem/g1_t2f.spice): {allmax1:.2f} V.")
    bg = [k for k in vc[0] if k.startswith("vce_bgr_")]
    if bg:
        out.append("Bandgap HBTs in the same runs (for reference; the bandgap has its own cascodes): max V_CE " + ", ".join(f"{k[8:-4]} {max(r[k] for r in vc if r.get(k) is not None):.2f} V" for k in sorted(bg)) + ".")
    out.append("")
open(os.path.join(RES, "tables.md"), "w").write("\n".join(out) + "\n")
print("\n".join(out))

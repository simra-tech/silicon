#!/usr/bin/env python3
"""r1_isense revision 2: reduce the regression campaign (suffix 20261021r2) against the revision-1 runs of record into one
small table, results/summary-20261021r2.json. Run from anywhere: python3 report_r2.py
Revision-1 values: the runs of record (2026-10-20 / -21); for ssx, ffx and the az = 1 / azh = 0 state, which revision 1
never ran, the development run dev-r2-01 (revision-1 netlist body, generated with the revision-1 options)."""
import json, os
here = os.path.dirname(os.path.abspath(__file__)); R = os.path.join(here, "results")
X = "20261021r2"
def S(rid):
    p = os.path.join(R, rid, "summary.json")
    return json.load(open(p)) if os.path.exists(p) else None
def res(rid):
    s = S(rid); return None if s is None else s.get("result", s)
rows = []
def row(name, crit, r1, r2, status, ev1, ev2):
    rows.append(dict(check=name, criterion=crit, rev1=r1, rev2=r2, status=status, evidence_rev1=ev1, evidence_rev2=ev2))
mx = lambda d, k: max(v[k] for v in d.values()); mn = lambda d, k: min(v[k] for v in d.values())
def ok(b): return "passed" if b else "failed"
# 1 settling, overload, output range, output CM, supply current (step deck)
a, b = res("isense-step-20261020-r1"), res("isense-step-" + X)
if b:
    row("Settling to 0.5 % after 100/120 mV edges, 5 corners", "<= 300 ns", mx(a, "settle_100mV_edges_worst_ns"), mx(b, "settle_100mV_edges_worst_ns"),
        ok(mx(b, "settle_100mV_edges_worst_ns") <= 300), "isense-step-20261020-r1", "isense-step-" + X)
    row("Settling 0 -> -20 mV small step (recorded)", "recorded", mx(a, "settle_20mV_edge_ns"), mx(b, "settle_20mV_edge_ns"), "recorded", "", "")
    f = lambda d: max(max(v["overload_recovery_ns"].values()) for v in d.values())
    row("Overload +-200 mV for 300 ns, recovery to 0.5 %", "recorded (rev 1: 132-184 ns)", f(a), f(b), "recorded", "", "")
    g = lambda d: max(v["output_node_range_V"][1] for v in d.values())
    row("Output nodes <= VDD incl. overload", "<= VDD (max 1.32 V)", g(a), g(b), ok(g(b) <= 1.32), "", "")
    h = lambda d: {c: round(v["vcm_out_V"], 4) for c, v in d.items()}
    row("Output common mode, 5 corners (step deck, zero current)", "0.600 V +- 30 mV", h(a), h(b), ok(all(abs(v - 0.6) <= 0.03 for v in h(b).values())), "", "")
    i = lambda d: {c: (round(v["idda_uA"], 1), round(v["idd_uA"], 1)) for c, v in d.items()}
    row("Supply current per channel IDDA / IDD (uA)", "recorded", i(a), i(b), "recorded", "", "")
    row("AZ release recovery (ns)", "recorded", mx(a, "az_release_recovery_ns"), mx(b, "az_release_recovery_ns"), "recorded", "", "")
# 2 DC
a, b = res("isense-dc-20261020-r1"), res("isense-dc-" + X)
if b:
    row("Gain (LSQ), 5 corners", "14 +- 0.1 % (report)", [mn(a, "gain"), mx(a, "gain")], [mn(b, "gain"), mx(b, "gain")], ok(all(abs(v["gain"] / 14 - 1) < 1e-3 for v in b.values())), "isense-dc-20261020-r1", "isense-dc-" + X)
    row("INL over -20..100 mV (% of span)", "report (rev 1 <= 0.023 %)", mx(a, "inl_max_pct_fs"), mx(b, "inl_max_pct_fs"), ok(mx(b, "inl_max_pct_fs") <= 0.05), "", "")
    row("Pedestal (mV)", "VREF/26 = 40.38 mV (report)", [mn(a, "pedestal_mV"), mx(a, "pedestal_mV")], [mn(b, "pedestal_mV"), mx(b, "pedestal_mV")], "recorded", "", "")
    row("Output common mode, 5 corners (DC deck)", "0.600 V +- 30 mV", {c: v["vcm_out_V"] for c, v in a.items()}, {c: v["vcm_out_V"] for c, v in b.items()},
        ok(all(abs(v["vcm_out_V"] - 0.6) <= 0.03 for v in b.values())), "", "")
for s_ in ("cmm100", "cmp100"):
    a, b = res("isense-dc-%s-20261020-r1" % s_), res("isense-dc-%s-%s" % (s_, X))
    if b:
        row("Pedestal at Kelvin CM %s (tt)" % s_, "shift <= 2 uV vs CM 0", a["tt"]["pedestal_mV"], b["tt"]["pedestal_mV"],
            ok(abs(b["tt"]["pedestal_mV"] - res("isense-dc-" + X)["tt"]["pedestal_mV"]) * 1e3 <= 2.0), "", "isense-dc-%s-%s" % (s_, X))
# 3 noise, bandwidth, PSRR
a, b = res("isense-noise-20261020-r1"), res("isense-noise-" + X)
if b:
    row("Closed-loop bandwidth, 5 corners", ">= 1 MHz, no peaking", [mn(a, "f3dB_Hz"), mx(a, "peaking_dB")], [mn(b, "f3dB_Hz"), mx(b, "peaking_dB")],
        ok(mn(b, "f3dB_Hz") >= 1e6), "isense-noise-20261020-r1", "isense-noise-" + X)
    row("Input noise at 1 MHz (nV/rtHz), worst corner", "recorded (rev 1 25-37)", mx(a, "in_nV_rtHz_at_1e+06"), mx(b, "in_nV_rtHz_at_1e+06"), "recorded", "", "")
    row("Input noise 10 kHz-5 MHz (uV rms), worst", "recorded (rev 1 53-80)", mx(a, "inoise_total_10k_5M_V") * 1e6, mx(b, "inoise_total_10k_5M_V") * 1e6, "recorded", "", "")
    row("Supply rejection VDDA->Vod at 1 MHz (dB), worst", "recorded", mx(a, "vdda_to_diff_dB_1M"), mx(b, "vdda_to_diff_dB_1M"), "recorded", "", "")
    row("CM -> Vod at 1 MHz (dB), worst", "recorded", mx(a, "cm_to_diff_dB_1M"), mx(b, "cm_to_diff_dB_1M"), "recorded", "", "")
# 4 MC
for r1, r2, lab in (("isense-mc-20261020-r1", "isense-mc-" + X, "tt, 50 samples"), ("isense-mc-ssff-20261020-r1", "isense-mc-ssff-" + X, "ss 125 C / ff -40 C, 30 + 30")):
    a, b = res(r1), res(r2)
    if b:
        for g in b:
            if g in ("samples",): continue
            row("Residual offset after AZ, MC %s [%s]" % (lab, g), "<= 100 uV every sample",
                dict(sigma=a[g]["res_uV"]["sigma"], worst=a[g]["res_uV"]["max_abs"], n=a[g]["res_uV"]["n"]),
                dict(sigma=b[g]["res_uV"]["sigma"], worst=b[g]["res_uV"]["max_abs"], n=b[g]["res_uV"]["n"]),
                ok(b[g]["res_within_100uV"] == b[g]["res_uV"]["n"]), r1, r2)
            oc = b[g].get("ocm_V")
            row("Output CM under mismatch, MC %s [%s] (new row; rev 1 from its raw waveforms)" % (lab, g), "0.600 V +- 30 mV every sample",
                {"tt_mm": dict(mean=0.5729, sigma=0.0168, min=0.5410, max=0.6174), "ss_mm": dict(mean=0.5848, sigma=0.0161, min=0.5527, max=0.6241),
                 "ff_mm": dict(mean=0.5656, sigma=0.0169, min=0.5315, max=0.5962)}.get(g),
                None if not oc else dict(mean=oc["mean"], sigma=oc["sigma"], min=oc["min"], max=oc["max"], within=b[g]["ocm_within_30mV"]),
                ok(oc and b[g]["ocm_within_30mV"] == oc["n"]), r1, r2)
            row("Raw offset before AZ, MC %s [%s] (sigma uV)" % (lab, g), "recorded", a[g]["raw_uV"]["sigma"], b[g]["raw_uV"]["sigma"], "recorded", "", "")
            row("Gain sigma / pedestal sigma, MC %s [%s]" % (lab, g), "recorded", [a[g]["gain"]["sigma"], a[g]["ped_mV"]["sigma"]], [b[g]["gain"]["sigma"], b[g]["ped_mV"]["sigma"]], "recorded", "", "")
# 5 AZ loop, droop
a, b = res("isense-azloop-20261020-r1"), res("isense-azloop-" + X)
if b:
    pm = lambda d: min(v["dm"]["phase_margin_deg"] for v in d.values()); gm_ = lambda d: min(v["dm"]["gain_margin_dB"] for v in d.values())
    row("AZ loop (return ratio, 1 GH / 1 F break), 5 corners", "PM >= 45 deg", [pm(a), gm_(a)], [pm(b), gm_(b)], ok(pm(b) >= 45), "isense-azloop-20261020-r1", "isense-azloop-" + X)
    row("AZ loop unity gain (MHz) / DC gain min (dB)", "recorded", [min(v["dm"]["f_unity_Hz"] for v in a.values()) / 1e6, max(v["dm"]["f_unity_Hz"] for v in a.values()) / 1e6, min(v["dm"]["dc_gain_dB"] for v in a.values())],
        [min(v["dm"]["f_unity_Hz"] for v in b.values()) / 1e6, max(v["dm"]["f_unity_Hz"] for v in b.values()) / 1e6, min(v["dm"]["dc_gain_dB"] for v in b.values())], "recorded", "", "")
for r1, r2 in (("isense-droop-20261020-r1", "isense-droop-" + X), ("isense-droop-150C-20261020-r1", "isense-droop-150C-" + X)):
    a, b = res(r1), res(r2)
    if b:
        row("Hold droop, mismatch bound (uV input-referred per 50 us) [%s]" % r2, "<= 50 uV", mx(a, "mismatch_bound_in_uV"), mx(b, "mismatch_bound_in_uV"), ok(mx(b, "mismatch_bound_in_uV") <= 50), r1, r2)
# 6 stb suite
def pl(rid):
    s = S(rid); return None if s is None else s["result"]["per_loop"]
def worst(p, loop, key="worst_pm_deg"):
    return {c: d[loop][key] for c, d in p.items() if loop in d}
r1n = pl("isense-stb-20261021-r1"); r1x = pl("dev-r2-01-stb")
for loop in ("dm_out", "cm_out"):
    b = pl("isense-stb-" + X)
    if b:
        a = dict(r1n); a.update({c: v for c, v in r1x.items() if c in ("ssx", "ffx")})
        st = all(b[c][loop]["status"] == "passed" for c in b)
        row("Loop gain, normal state, %s: worst PM / GM per corner (3 shunt levels)" % loop, "PM >= 60 deg, GM >= 10 dB",
            {c: (a[c][loop]["worst_pm_deg"], a[c][loop]["worst_gm_db"]) for c in a}, {c: (b[c][loop]["worst_pm_deg"], b[c][loop]["worst_gm_db"]) for c in b},
            ok(st), "isense-stb-20261021-r1 (5 corners), dev-r2-01-stb (ssx, ffx)", "isense-stb-" + X)
b = pl("isense-stb-" + X)
if b:
    row("DM loop cross-check, break at the input gates (dm_in)", "equal to dm_out within 1 deg", None,
        {c: (b[c]["dm_in"]["worst_pm_deg"], b[c]["dm_out"]["worst_pm_deg"]) for c in b},
        ok(all(abs(b[c]["dm_in"]["worst_pm_deg"] - b[c]["dm_out"]["worst_pm_deg"]) <= 1.0 for c in b)), "", "isense-stb-" + X)
for rid1, rid1x, rid2, lab, loops in (("isense-stbaz-20261021-r1", "dev-r2-01-stbaz", "isense-stbaz-" + X, "AZ closed (az = azh = 1)", ("dm_aux", "cm_out")),
                                     (None, "dev-r2-01-stbazi", "isense-stbazi-" + X, "az = 1, azh = 0 (new)", ("cm_out",))):
    b = pl(rid2)
    if not b: continue
    a = dict(pl(rid1)) if rid1 else {}
    ax = pl(rid1x) or {}
    a.update({c: v for c, v in ax.items() if (c in ("ssx", "ffx") or not rid1)})
    for loop in loops:
        row("Loop gain, %s, %s: PM / GM per corner" % (lab, loop), "PM >= 60 deg, GM >= 10 dB",
            {c: (a[c][loop]["worst_pm_deg"], a[c][loop]["worst_gm_db"]) for c in a if loop in a[c]},
            {c: (b[c][loop]["worst_pm_deg"], b[c][loop]["worst_gm_db"]) for c in b}, ok(all(b[c][loop]["status"] == "passed" for c in b)),
            ", ".join(x for x in (rid1, rid1x) if x), rid2)
for rid1, rid2, lab in (("isense-stb-load28-20261021-r1", "isense-stb-load28-" + X, "ADC load 100 ohm + 2.8 pF + 0.2 pF"), ("isense-stb-c14-20261021-r1", "isense-stb-c14-" + X, "comparators at code 14 / 49")):
    a, b = pl(rid1), pl(rid2)
    if b:
        row("Loop gain sensitivity, %s (tt, ss): DM / CM worst PM" % lab, "PM >= 60 deg (rev 1: recorded)",
            {c: (a[c]["dm_out"]["worst_pm_deg"], a[c]["cm_out"]["worst_pm_deg"]) for c in a}, {c: (b[c]["dm_out"]["worst_pm_deg"], b[c]["cm_out"]["worst_pm_deg"]) for c in b},
            ok(all(b[c][l]["status"] == "passed" for c in b for l in ("dm_out", "cm_out"))), rid1, rid2)
a, b = res("isense-stbstep-20261021-r1"), res("isense-stbstep-" + X)
if b:
    row("Shunt step 0 -> 100 mV, 10 ns edge, joint load: settling to 0.5 % from the edge start", "<= 300 ns, <= 1 overshoot",
        {c: (v["settle_0p5pct_from_edge_start_ns"], v["overshoot_count"]) for c, v in a.items()}, {c: (v["settle_0p5pct_from_edge_start_ns"], v["overshoot_count"]) for c, v in b.items()},
        ok(all(v["settle_0p5pct_from_edge_start_ns"] <= 300 and v["overshoot_count"] <= 1 for v in b.values())), "isense-stbstep-20261021-r1", "isense-stbstep-" + X)
a, b = res("isense-stbcm-20261021-r1"), res("isense-stbcm-" + X)
if b:
    row("CM step (VCM +20 mV): overshoot % / overshoots beyond 2 % / settle to 2 % (ns)", "<= 1 overshoot, settled within 300 ns",
        {c: (round(v["overshoot_pct_of_cm_step"], 1), v.get("overshoots_beyond_2pct"), round(v["settle_2pct_ns"])) for c, v in a.items()},
        {c: (round(v["overshoot_pct_of_cm_step"], 1), v["overshoots_beyond_2pct"], round(v["settle_2pct_ns"])) for c, v in b.items()},
        ok(all(v["status"] == "passed" for v in b.values())), "isense-stbcm-20261021-r1 (re-analysed with the revision-2 criterion: failed, 2-3 overshoots at tt/ff/sf/fs)", "isense-stbcm-" + X)
# 7 joint path with r1_safe
jp = os.path.join(here, "..", "..", "r1_safe", "sim", "results")
def J(rid):
    p = os.path.join(jp, rid, "summary.json"); return json.load(open(p))["result"] if os.path.exists(p) else None
a, b = J("safe-joint-20261020-r3b"), J("safe-joint-" + X)
if b:
    LSB_uV = 2380.95
    dc, dd = {}, {}
    for c in b:
        for k, v in b[c].items():
            if isinstance(v, dict) and "centre_err_LSB" in v:
                dc["%s:%s" % (c, k)] = round(v["centre_err_LSB"] - a[c][k]["centre_err_LSB"], 4)
        for k, v in b[c]["delays_from_shunt_step"].items():
            dd["%s:%s" % (c, k)] = round(v - a[c]["delays_from_shunt_step"][k], 1)
    row("Joint path r1_isense -> r1_safe, threshold centre change vs revision 1 (LSB), 8 crossings x 3 corners", "|delta| <= 0.05 LSB",
        max(abs(x) for x in dc.values()), dc, ok(max(abs(x) for x in dc.values()) <= 0.05), "r1_safe safe-joint-20261020-r3b", "r1_safe safe-joint-" + X)
    row("Joint path, delay change vs revision 1 (ns)", "|delta| <= 20 ns", max(abs(x) for x in dd.values()), dd, ok(max(abs(x) for x in dd.values()) <= 20), "", "")
    row("Joint path, OC trip delay (ns) a/b, tt/ss_cold/ff_hot", "< 300 ns", {c: a[c]["delays_from_shunt_step"]["oc_trip_a_ns"] for c in a},
        {c: (b[c]["delays_from_shunt_step"]["oc_trip_a_ns"], b[c]["delays_from_shunt_step"]["oc_trip_b_ns"]) for c in b},
        ok(all(max(b[c]["delays_from_shunt_step"]["oc_trip_a_ns"], b[c]["delays_from_shunt_step"]["oc_trip_b_ns"]) < 300 for c in b)), "", "")
    row("Joint path, max |centre error| (LSB) and cross-channel glitches", "<= 0.5 LSB uncalibrated; 0 glitches",
        {c: a[c]["max_abs_centre_err_LSB"] for c in a}, {c: (b[c]["max_abs_centre_err_LSB"], b[c].get("cross_channel_glitches")) for c in b},
        ok(all(b[c]["max_abs_centre_err_LSB"] <= 0.5 and not b[c].get("cross_channel_glitches") for c in b)), "", "")
out = {"suffix": X, "netlist_rev2_sha256": "af013b95f5fd57e2f1cd0d1345a4c75471c2f216b063ede3a39bdea6412ba4ee",
       "netlist_rev1_sha256": "5db34e0a8f7c54abbc4d4b547462129dd862404f205e2c3472fb4095b93faf8b", "rows": rows,
       "counts": {k: sum(1 for r in rows if r["status"] == k) for k in ("passed", "failed", "recorded")}}
json.dump(out, open(os.path.join(R, "summary-%s.json" % X), "w"), indent=1, default=str)
for r in rows:
    print("%-8s | %s | rev1 %s | rev2 %s" % (r["status"], r["check"], json.dumps(r["rev1"], default=str)[:160], json.dumps(r["rev2"], default=str)[:220]))
print(out["counts"])

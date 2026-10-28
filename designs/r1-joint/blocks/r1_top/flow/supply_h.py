# SPDX-License-Identifier: Apache-2.0
"""Supply network of r1_top try h0 (track T8f): collects the extracted DC runs of flow/supply_h_rnet.py (VSS, VDD,
VDDA; typ and max sheet), computes the supply loss at every macro and the ctrl feed resistance, lists the segment
breakdown and checks EM of the new feed shapes (bound rows: the whole net current in one shape; extracted rows where
the cut or gradient method has nodes). Limits: process specification Rev 1.2, section 2.15 (105 C, DC), as supply_g.py.
  python3 supply_h.py <run dir> <out.json> [<reference run dir for the comparison, e.g. try g with supply_rnet of
  supply_h_rnet.py>]
"""
import json
import os
import sys

RUN, OUT = sys.argv[1], sys.argv[2]
REF = sys.argv[3] if len(sys.argv) > 3 else None
EM_LINE = {"M3": 2.0, "M4": 2.0, "M5": 2.0, "TM1": 15.0, "TM2": 16.0}
EM_VIA = {"V3": 0.4, "V4": 0.4, "TV1": 1.4, "TV2": 10.0}
I_CTRL = 40.25
DOMAIN = {"ctrl": ["VDD"], "adc": ["VDD", "VDDA"], "isense": ["VDD", "VDDA"], "osc": ["VDD"], "bias": ["VDD", "VDDA"],
          "afe": ["VDDA"], "safe": ["VDDA"], "bgr": ["VDDA"], "t2f": ["VDDA"]}


def via_count(w, h, v):
    size, sp, enc = {"V3": (0.19, 0.29, 0.10), "V4": (0.19, 0.29, 0.10), "TV1": (0.42, 0.42, 0.45),
                     "TV2": (0.90, 1.06, 0.55)}[v]
    nx = max(1, int((w - 2 * enc + sp) // (size + sp)))
    ny = max(1, int((h - 2 * enc + sp) // (size + sp)))
    return nx * ny


def load(run):
    d = os.path.join(run, "supply_rnet")
    rn = {}
    for net in ("VSS", "VDD", "VDDA"):
        for c in ("typ", "max"):
            tag = c if net == "VSS" else "%s_%s" % (net.lower(), c)
            p = os.path.join(d, "supply_h_rnet_%s.json" % tag)
            rn[(net, c)] = json.load(open(p)) if os.path.exists(p) else None
    return rn


def summary(rn):
    s = {}
    for c in ("typ", "max"):
        vss = rn[("VSS", c)]["runs"]["all"]["port_voltage_mV"]
        vdd = rn[("VDD", c)]["static_drop_mV"]
        vda = rn[("VDDA", c)]["static_drop_mV"] if rn[("VDDA", c)] else {}
        cs = [v for k, v in vss.items() if k.startswith("ctrl")]
        cd = [v for k, v in vdd.items() if k.startswith("ctrl")]
        e = {"ctrl_vss_rise_worst_mV": max(cs), "ctrl_vss_rise_best_mV": min(cs),
             "ctrl_vdd_drop_worst_mV": max(cd), "ctrl_vdd_drop_best_mV": min(cd)}
        e["ctrl_loss_worst_mV"] = round(e["ctrl_vss_rise_worst_mV"] + e["ctrl_vdd_drop_worst_mV"], 3)
        e["ctrl_loss_best_mV"] = round(e["ctrl_vss_rise_best_mV"] + e["ctrl_vdd_drop_best_mV"], 3)
        e["ctrl_feed_R_ohm"] = round(e["ctrl_loss_worst_mV"] / I_CTRL, 4)
        loss = {}
        for m, doms in DOMAIN.items():
            if m == "ctrl":
                continue
            rise = max(v for k, v in vss.items() if k == m or k.startswith(m + "_"))
            for dm in doms:
                drop = vdd if dm == "VDD" else vda
                if m in drop:
                    loss["%s (%s)" % (m, dm)] = {"vss_rise_mV": round(rise, 3), "supply_drop_mV": round(drop[m], 3),
                                                 "loss_mV": round(rise + drop[m], 3)}
                elif any(k.startswith(m + "_") for k in drop):
                    dd = max(v for k, v in drop.items() if k.startswith(m + "_"))
                    loss["%s (%s)" % (m, dm)] = {"vss_rise_mV": round(rise, 3), "supply_drop_mV": round(dd, 3),
                                                 "loss_mV": round(rise + dd, 3)}
        loss["ctrl (VDD), worst grid point"] = {"vss_rise_mV": e["ctrl_vss_rise_worst_mV"],
                                                "supply_drop_mV": e["ctrl_vdd_drop_worst_mV"], "loss_mV": e["ctrl_loss_worst_mV"]}
        e["macro_loss"] = loss
        j = rn[("VSS", c)]
        e["isense_bgr_path_R_ohm"] = j["path_R_isense_bgr_ohm"]
        e["isense_minus_bgr_mV"] = {t: j["runs"][t]["isense_minus_bgr_mV"] for t in j["runs"]}
        e["offset_R_isense_bgr_pads_grounded_ohm"] = j["offset_R_isense_bgr_pads_grounded_ohm"]
        e["breakdown"] = {n: rn[(n, c)]["breakdown"] for n in ("VSS", "VDD") if rn[(n, c)] and "breakdown" in rn[(n, c)]}
        s[c] = e
    return s


rn = load(RUN)
out = {"method": "extracted (KLayout RNetExtractor, flow/supply_h_rnet.py) + EM (bound and extracted rows)",
       "summary": summary(rn)}
if REF:
    out["reference"] = {"run": "<G1_RESULTS_ROOT>/r1_top/" + os.path.basename(REF.rstrip("/")), "summary": summary(load(REF))}
asm = json.load(open(os.path.join(RUN, "r1_top_assembly.json")))
feed = asm.get("supply_h_feed", {})
em = []
# extracted rows (max of cut and gradient where measured), both corners
for c in ("typ", "max"):
    for net in ("VSS", "VDD"):
        for r in (rn[(net, c)] or {}).get("em_feed", []):
            if r["cut_elements"] == 0 and r["I_gradient_mA"] == 0.0:
                em.append({"item": r["item"], "corner": c, "kind": "extracted", "I_mA": None, "limit_mA": r["limit_mA"],
                           "state": "not measured (no node pair in the shape; see the bound row)"})
            else:
                em.append({"item": r["item"], "corner": c, "kind": "extracted", "I_mA": r["I_used_mA"],
                           "limit_mA": r["limit_mA"], "state": "passed" if r["pass"] else "failed"})
# bound rows: the whole net current (VSS: all block currents; VDD: all VDD currents) in one shape
I_VSS = sum(rn[("VSS", "typ")]["currents_mA"].values())
I_VDD = sum(rn[("VDD", "typ")]["currents_mA"].values())
south_vss = [x["I_mA"] for x in rn[("VSS", "max")]["breakdown"]["cuts"] if {x["from"], x["to"]} == {"S_feed", "ctrl_grid"}]
south_vdd = [x["I_mA"] for x in rn[("VDD", "max")]["breakdown"]["cuts"] if {x["from"], x["to"]} == {"S_feed", "ctrl_grid"} or
             {x["from"], x["to"]} == {"S_core_row", "ctrl_grid"}]
I_SV = abs(sum(south_vss))
I_SD = abs(sum(south_vdd))
for it in feed.get("em_items", []):
    tot = I_VSS if it["net"] == "VSS" else I_VDD
    lim = EM_LINE[it["layer"]] * it["width"]
    if "stripe south end" in it["name"]:
        tot = I_SV                                           # all south VSS inflow into one stripe end
    em.append({"item": it["name"], "corner": "typ/max", "kind": "bound (%s in one shape)" % (
        "all %s current %.2f mA" % (it["net"], tot) if "stripe" not in it["name"] else "all south VSS inflow %.2f mA" % tot),
        "I_mA": round(tot, 3), "limit_mA": lim, "state": "passed" if tot <= lim else "failed"})
for nm, n_cuts, cur in [
        ("IOPadVss riser TopVia2 onto the VSS rail (per pad)", feed.get("ring_eco", {}).get("iopadvss_riser_tv2", 0), I_VSS),
        ("VSS bridge TopVia2, west overlap (x 429-452)", via_count(23.0, 12.94, "TV2"), I_VSS),
        ("VSS tab TopVia2 (22 um tab)", via_count(22.0, 12.94, "TV2"), I_VSS),
        ("VDD south bar TopVia2 per ctrl VDD stripe (2.2 x 7 um), all south VDD inflow", via_count(2.2, 7.0, "TV2"), I_SD)]:
    lim = EM_VIA["TV2"] * n_cuts
    em.append({"item": nm, "corner": "typ/max", "kind": "bound", "cuts": n_cuts, "I_mA": round(cur, 3), "limit_mA": lim,
               "state": "passed" if cur <= lim else "failed"})
out["em"] = em
out["em_summary"] = {"rows": len(em), "failed": sum(1 for r in em if r["state"] == "failed"),
                     "not_measured": sum(1 for r in em if r["state"].startswith("not"))}
out["currents_mA"] = {"VSS_total": round(I_VSS, 3), "VDD_total": round(I_VDD, 3), "south_VSS_inflow_ctrl_max": round(I_SV, 3),
                      "south_VDD_inflow_ctrl_max": round(I_SD, 3)}
json.dump(out, open(OUT, "w"), indent=1)
for c in ("typ", "max"):
    e = out["summary"][c]
    print(c, "ctrl VSS %.2f/%.2f VDD %.2f/%.2f loss %.2f/%.2f mV feed R %.3f ohm; isense-bgr %.3f ohm, offset %.2f mV" % (
        e["ctrl_vss_rise_worst_mV"], e["ctrl_vss_rise_best_mV"], e["ctrl_vdd_drop_worst_mV"], e["ctrl_vdd_drop_best_mV"],
        e["ctrl_loss_worst_mV"], e["ctrl_loss_best_mV"], e["ctrl_feed_R_ohm"], e["isense_bgr_path_R_ohm"],
        e["isense_minus_bgr_mV"]["all"]))
    for m, l in e["macro_loss"].items():
        print("   ", m, l)
print("EM", out["em_summary"])
for r in em:
    print("  ", r["state"][:6], r["item"], r["corner"], r["I_mA"], r["limit_mA"])

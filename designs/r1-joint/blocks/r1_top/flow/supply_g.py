# SPDX-License-Identifier: Apache-2.0
"""Supply network of r1_top try g (track T8e): collects the extracted DC runs of flow/supply_g_rnet.py (VSS, VDD, VDDA,
typ and max sheet) and checks EM of the top-level supply shapes and of the macro supply pins against the PDK limits
(process specification Rev 1.2, section 2.15, 105 C, DC; the values of supply_f.py). Writes <out>.json and prints
the tables of reports/supply_g.md.
  python3 supply_g.py <run dir> <out.json>
"""
import json
import os
import sys

RUN, OUT = sys.argv[1], sys.argv[2]
D = os.path.join(RUN, "supply_rnet")
EM_LINE = {"M3": 2.0, "M4": 2.0, "M5": 2.0, "TM1": 15.0, "TM2": 16.0}
EM_VIA = {"V3": 0.4, "V4": 0.4, "TV1": 1.4, "TV2": 10.0}


def via_count(w, h, v):
    size, sp, enc = {"V3": (0.19, 0.29, 0.10), "V4": (0.19, 0.29, 0.10), "TV1": (0.42, 0.42, 0.45),
                     "TV2": (0.90, 1.06, 0.55)}[v]
    nx = max(1, int((w - 2 * enc + sp) // (size + sp)))
    ny = max(1, int((h - 2 * enc + sp) // (size + sp)))
    return nx * ny


rn = {}
for net in ("VSS", "VDD", "VDDA"):
    for c in ("typ", "max"):
        tag = c if net == "VSS" else "%s_%s" % (net.lower(), c)
        p = os.path.join(D, "supply_g_rnet_%s.json" % tag)
        rn[(net, c)] = json.load(open(p)) if os.path.exists(p) else None
out = {"method": "extracted (KLayout RNetExtractor, flow/supply_g_rnet.py) + EM by shape width", "rnet": {}}
for (net, c), j in rn.items():
    if j is None:
        out["rnet"]["%s_%s" % (net, c)] = "not run"
        continue
    r = {"resistors": j["resistors"], "currents_mA": j["currents_mA"]}
    if net == "VSS":
        r.update({k: j[k] for k in ("path_R_isense_bgr_ohm", "offset_R_isense_bgr_pads_grounded_ohm")})
        r["isense_minus_bgr_mV"] = {t: j["runs"][t]["isense_minus_bgr_mV"] for t in j["runs"]}
        r["vss_rise_mV"] = {k: v for k, v in j["runs"]["all"]["port_voltage_mV"].items() if not k.startswith("pad")}
    else:
        d = j["static_drop_mV"]
        r["static_drop_mV"] = {k: v for k, v in d.items() if not k.startswith("ctrl")}
        cs = [v for k, v in d.items() if k.startswith("ctrl")]
        if cs:
            r["static_drop_mV"]["ctrl (worst of 63 grid points)"] = max(cs)
            r["static_drop_mV"]["ctrl (best of 63 grid points)"] = min(cs)
    out["rnet"]["%s_%s" % (net, c)] = r
I_CTRL = 40.25
em = []
for name, Iv, layer, w in [
        ("VDDA trunk Metal4 8 um (all VDDA, 4.31 mA, bound)", 4.31, "M4", 8.0),
        ("VDDA Metal5 trunk, lower part at the notches (11.4 um, all VDDA)", 4.31, "M5", 11.4),
        ("pad-7 VDDA riser Metal4 6 um (all VDDA, bound)", 4.31, "M4", 6.0),
        ("pad-7 VDDA riser Metal5 15 um (all VDDA, bound)", 4.31, "M5", 15.0),
        ("west VDDA riser Metal3 9.4 um (all VDDA, bound)", 4.31, "M3", 9.4),
        ("AFE VDDA rail Metal4 2.8 um", 2.0, "M4", 2.8),
        ("isense VDDA Metal4 2 um", 0.45, "M4", 2.0), ("isense VDD Metal4 2 um", 1.138, "M4", 2.0),
        ("ctrl VDD TopMetal1 stripe 2.2 um (1/7 of 40.25 mA)", I_CTRL / 7, "TM1", 2.2),
        ("south VDD feed TopMetal2 strap 24 um (all ctrl VDD, bound)", I_CTRL, "TM2", 24.0),
        ("south VDD feed TopMetal2 bar 8.0 um (all ctrl VDD, bound)", I_CTRL, "TM2", 8.0),
        ("ADC vdda riser Metal3 2 um", 1.102, "M3", 2.0),
        ("ADC vdda pin Metal3 1.0 um", 1.102, "M3", 1.0), ("ADC vdd pin Metal3 1.0 um", 0.870, "M3", 1.0),
        ("ADC vss pin Metal3 1.0 um (IDD + IDDA, tt)", 1.972, "M3", 1.0),
        ("AFE vss pin Metal3 1.0 um (2 pins, half each)", 1.0, "M3", 1.0),
        ("AFE vdd pin Metal3 1.0 um (2 pins, half each)", 1.0, "M3", 1.0),
        ("AFE vss pin Metal3 1.0 um (all 2.0 mA in one pin, bound)", 2.0, "M3", 1.0),
        ("safe vdda pin Metal3 0.4 um", 0.418, "M3", 0.4), ("bias vdd neck Metal4 0.5 um", 0.05, "M4", 0.5),
        ("osc vdd Metal4 2 um", 0.317, "M4", 2.0)]:
    lim = EM_LINE[layer] * w
    em.append({"item": name, "I_mA": round(Iv, 3), "limit_mA": round(lim, 3), "pass": Iv <= lim})
for name, Iv, v, n in [("ctrl VDD TopVia2 per stripe, north row", I_CTRL / 7, "TV2", via_count(2.2, 15.0, "TV2")),
                       ("ctrl VDD TopVia2 per stripe, south bar (all ctrl VDD over 7 stripes)", I_CTRL / 7, "TV2", via_count(2.2, 7.0, "TV2")),
                       ("south VDD stack TopVia2 (one of 5, all ctrl VDD, bound)", I_CTRL, "TV2", via_count(8.8, 15.0, "TV2")),
                       ("south VDD stack TopVia1 (one of 5, all ctrl VDD, bound)", I_CTRL, "TV1", via_count(8.8, 6.0, "TV1")),
                       ("south VDD stack Via4 (one of 5, all ctrl VDD, bound)", I_CTRL, "V4", via_count(8.8, 6.0, "V4")),
                       ("isense VSS TopVia1 into the column", 1.588, "TV1", via_count(14.0, 21.0, "TV1")),
                       ("AFE VSS stack TopVia1", 2.0, "TV1", via_count(14.0, 4.0, "TV1")),
                       ("AFE vss / vdd Via3 at the pin (1.0 x 2.0 um, all 2.0 mA, bound)", 2.0, "V3", via_count(1.0, 2.0, "V3")),
                       ("ADC vdda Via3 at the trunk", 1.102, "V3", via_count(2.0, 7.0, "V3")),
                       ("ADC vss Via3 at the trunk", 1.972, "V3", via_count(2.0, 7.0, "V3"))]:
    lim = EM_VIA[v] * n
    em.append({"item": name, "I_mA": round(Iv, 3), "limit_mA": round(lim, 3), "vias": n, "pass": Iv <= lim})
# extracted rows (flow/supply_g_rnet.py): cut-line sums on the narrow IO-filler straps and voltage-gradient values on
# the trunks and on the ctrl TopMetal1 stripes, typ and max sheet; a cut with 0 elements is "not measured".
for (net, c), j in sorted(rn.items()):
    if j is None:
        continue
    for e in j.get("em_cuts", []):
        em.append({"item": "%s (extracted, cut, %s)" % (e["cut"], c), "I_mA": e["I_mA"], "limit_mA": e["limit_mA"],
                   "pass": e["pass"] if e["elements"] else "not measured"})
    for e in j.get("em_gradient", []):
        em.append({"item": "%s (extracted, gradient, %s)" % (e["item"], c), "I_mA": e["I_mA"], "limit_mA": e["limit_mA"],
                   "pass": e["pass"] if e["node_groups"] > 1 else "not measured"})
out["em"] = em
json.dump(out, open(OUT, "w"), indent=1)
print(json.dumps(out["rnet"], indent=1))
for e in em:
    print("| %s | %.3f | %.3f | %s |" % (e["item"], e["I_mA"], e["limit_mA"], {True: "passed", False: "failed"}.get(e["pass"], e["pass"])))

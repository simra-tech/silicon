# SPDX-License-Identifier: Apache-2.0
"""Supply network of r1_top try f by square count (track T8). Writes <out>.json and prints the tables of
reports/supply_f.md. No extraction tool: every resistance is (length / width) x sheet resistance of a drawn
top-level shape of layout/r1_top_assemble_f.py, or N vias in parallel. Sheet and via resistance and the EM limits are
from the IHP SG13G2 process specification, Rev 1.2 (PDK doc `SG13G2_os_process_spec.pdf`, sections 2.12-2.15;
EM: section 2.15, page 16, 11 years at 105 C). Currents are the block README worst cases (simulated or estimated).
  python3 supply_f.py <out.json>
"""
import json
import sys

# sheet resistance mOhm/sq (min, typ, max)
RS = {"M3": (73, 88, 103), "M4": (73, 88, 103), "M5": (73, 88, 103), "TM1": (15, 18, 21), "TM2": (7.5, 11, 14.5)}
# via resistance Ohm per via (min, typ, max)
RV = {"V3": (5, 9, 20), "V4": (5, 9, 20), "TV1": (1, 2.2, 4), "TV2": (0.5, 1.1, 2.2)}
# EM limits: mA per um of width (lines), mA per via
EM_LINE = {"M3": 2.0, "M4": 2.0, "M5": 2.0, "TM1": 15.0, "TM2": 16.0}
EM_VIA = {"V3": 0.4, "V4": 0.4, "TV1": 1.4, "TV2": 10.0}
CORNER = {"min": 0, "typ": 1, "max": 2}


def seg(layer, length, width, what, n_parallel=1):
    return {"kind": "line", "layer": layer, "L": length, "W": width, "n": n_parallel, "what": what}


def via(v, n, what):
    return {"kind": "via", "layer": v, "n": n, "what": what}


def r_of(s, c="typ"):
    k = CORNER[c]
    if s["kind"] == "line":
        return s["L"] / s["W"] * RS[s["layer"]][k] / 1000.0 / s["n"]
    return RV[s["layer"]][k] / s["n"]


def via_count(w, h, v):
    size, sp, enc = {"V3": (0.19, 0.29, 0.10), "V4": (0.19, 0.29, 0.10), "TV1": (0.42, 0.42, 0.45),
                     "TV2": (0.90, 1.06, 0.55)}[v]
    nx = max(1, int((w - 2 * enc + sp) // (size + sp)))
    ny = max(1, int((h - 2 * enc + sp) // (size + sp)))
    return nx * ny


# block currents, mA (worst case from the block READMEs)
I = {"ctrl_VDD": 33.4, "afe_VDDA": 2.00, "adc_VDD": 0.903, "adc_VDDA": 1.036, "isense_VDDA": 0.450,
     "isense_VDD": 1.138, "bias_VDDA": 0.196, "bgr_VDDA": 0.080, "t2f_VDDA": 0.0625, "osc_VDD": 0.317,
     "safe_VDDA": 0.418}
I_SRC = {"ctrl_VDD": "r1_ctrl 0.6 final/metrics.json power__total 0.0401 W (typ) / 1.2 V",
         "afe_VDDA": "r1_afe README, ff", "adc_VDD": "r1_adc README revision 5, pre-layout tt",
         "adc_VDDA": "r1_adc README revision 5, pre-layout tt", "isense_VDDA": "r1_isense README, 2 x 225 uA ff_hot",
         "isense_VDD": "r1_isense README, 2 x 569 uA ff_hot", "bias_VDDA": "r1_bias README revision 2, ffx",
         "bgr_VDDA": "r1_bgr README, max", "t2f_VDDA": "r1_t2f README", "osc_VDD": "r1_osc README, max",
         "safe_VDDA": "r1_safe README"}

# ---------------- VDDA: pad 7 core pin (x 1379, y 493) -> feed -> riser (M4 6 um || M5 15 um) -> trunk (M4 8 || M5 18)
TRUNK_RPU = {c: 1.0 / (8.0 / (RS["M4"][k] / 1000.0) + 18.0 / (RS["M5"][k] / 1000.0)) for c, k in CORNER.items()}
RISER_RPU = {c: 1.0 / (6.0 / (RS["M4"][k] / 1000.0) + 15.0 / (RS["M5"][k] / 1000.0)) for c, k in CORNER.items()}
FEED = [seg("M3", 13.3, 23.0, "pad-7 Metal3 feed x 1366-1379.29"), via("V3", via_count(6, 23, "V3"), "feed Via3")]


def trunk(L):
    return {"kind": "rpu", "rpu": TRUNK_RPU, "L": L, "what": "VDDA trunk M4 8 um || M5 18 um, %.0f um" % L}


def riser(L):
    return {"kind": "rpu", "rpu": RISER_RPU, "L": L, "what": "pad-7 riser M4 6 um || M5 15 um, %.0f um" % L}


def R(path, c="typ"):
    t = 0.0
    for s in path:
        t += s["rpu"][c] * s["L"] if s["kind"] == "rpu" else r_of(s, c)
    return t


WEST = [riser(137.0), trunk(1042.0), seg("M3", 4.7, 8.0, "trunk -> west riser (Via3 area)")]
VDDA = {
    "u_safe": FEED + [riser(112.0), seg("M4", 33.0, 2.2, "Metal4 y 379.8-382 to the riser"),
                      seg("M3", 2.2, 2.2, "Metal3 at the pin"), seg("M3", 1.0, 0.4, "safe vdda pin 0.4 um")],
    "u_isense": FEED + [seg("M3", 228.0, 4.0, "Metal3 riser x 1366-1370, y 505-733"),
                        seg("M4", 243.0, 2.0, "Metal4 y 732-734 to x 1125"), seg("M3", 2.2, 1.6, "Metal3 at the pin")],
    "u_adc": FEED + [riser(137.0), trunk(727.0), seg("M3", 19.6, 2.0, "Metal3 riser x 641-643"),
                     seg("M3", 1.6, 0.4, "0.4 um neck into the 0.4 um pin")],
    "u_afe (far pin x 520.8)": FEED + WEST + [seg("M3", 381.0, 9.4, "west riser x 322.6-332, y 356-737"),
                                               seg("M4", 194.0, 2.8, "AFE rail y 735.6-738.4"),
                                               seg("M3", 3.0, 0.4, "Metal3 into the 0.4 um pin")],
    "u_bgr": FEED + WEST + [seg("M3", 217.0, 9.4, "west riser to y 573"), seg("M4", 56.0, 2.0, "Metal4 y 572-574"),
                            seg("M3", 4.0, 6.0, "Metal3 x 380-386 into the bar")],
    "u_bias": FEED + WEST + [seg("M3", 217.0, 9.4, "west riser to y 573"), seg("M4", 114.5, 2.0, "Metal4 y 572-574"),
                             seg("M3", 37.0, 0.5, "Metal3 x 441.25-441.75 to the bar")],
    "u_t2f": FEED + WEST + [seg("M3", 381.0, 9.4, "west riser"), seg("M4", 44.0, 2.8, "AFE rail to x 371"),
                            seg("M3", 13.0, 4.0, "Metal3 x 369-373")],
}
# ---------------- VDD / VSS: from the core ring (TopMetal) to the macro pins; ring resistance listed separately
VDD = {
    "u_ctrl (7 TopMetal1 stripes)": [seg("TM1", 13.3, 2.2, "stripe extension into the north VDD row", 7),
                                     via("TV2", 7 * via_count(2.2, 15.0, "TV2"), "TopVia2 in the row")],
    "u_isense": [seg("M3", 7.6, 1.6, "Metal3 at the pin"), via("V3", via_count(1.6, 2.0, "V3"), "Via3"),
                 seg("M4", 87.0, 2.0, "Metal4 y 728.6-730.6 to the east column"),
                 via("V4", via_count(13.5, 2.0, "V4"), "Via4"), via("TV1", via_count(13.5, 2.0, "TV1"), "TopVia1")],
    "u_osc": [seg("M3", 9.0, 2.0, "Metal3 bar extension to x 1246.5"), seg("M4", 108.0, 2.0, "Metal4 to the column"),
              via("TV1", via_count(13.5, 2.0, "TV1"), "TopVia1")],
    "u_adc (from the M4 VDD trunk)": [seg("M3", 29.6, 2.0, "Metal3 riser x 691-693"),
                                      seg("M3", 1.6, 0.4, "0.4 um neck into the 0.4 um pin")],
}
VSS = {
    "u_ctrl (7 TopMetal1 stripes)": [seg("TM1", 18.6, 2.2, "stripe extension to the north VSS row", 7),
                                     via("TV2", 7 * via_count(2.2, 15.0, "TV2"), "TopVia2 in the row")],
    "u_isense (to the east outer column)": [seg("M3", 0.5, 1.6, "Metal3 pin to the stack"),
                                            via("V3", via_count(1.6, 29.5, "V3"), "Via3 stack"),
                                            via("V4", via_count(1.6, 29.5, "V4"), "Via4 stack"),
                                            {"kind": "par", "what": "TopMetal1 plate 26 um || Metal5 plate 21 um, 216 um",
                                             "a": seg("TM1", 216.0, 26.0, ""), "b": seg("M5", 216.0, 21.0, "")},
                                            seg("M5", 22.3, 21.0, "Metal5 under the VDD column"),
                                            via("TV1", via_count(14.0, 21.0, "TV1"), "TopVia1 into the VSS column")],
    "u_bgr (to the south outer row)": [seg("M3", 9.0, 90.0, "Metal3 riser x 340-430, y 333-342"), seg("M3", 35.0, 84.0, "Metal3 riser, 4 bars (2 um gaps), y 342-377"),
                                      via("V3", via_count(59.0, 7.0, "V3"), "Via3"),
                                      via("V4", via_count(20.0, 8.5, "V4"), "Via4"),
                                      via("TV1", via_count(20.0, 8.5, "TV1"), "TopVia1"),
                                      via("TV2", via_count(20.0, 8.5, "TV2"), "TopVia2")],
    "u_afe": [seg("M4", 13.0, 2.0, "Metal4 y 731-733 to x 344"), seg("M3", 9.0, 0.5, "Metal3 into the pin"),
              via("V4", via_count(14.0, 4.0, "V4"), "Via4"), via("TV1", via_count(14.0, 4.0, "TV1"), "TopVia1")],
    "u_adc (from the M4 VSS trunk)": [seg("M3", 39.6, 2.0, "Metal3 riser x 741-743"),
                                      seg("M3", 1.6, 0.4, "0.4 um neck into the 0.4 um pin")],
}


def r_any(s, c):
    if s["kind"] == "par":
        a, b = r_of(s["a"], c), r_of(s["b"], c)
        return a * b / (a + b)
    if s["kind"] == "rpu":
        return s["rpu"][c] * s["L"]
    return r_of(s, c)


def Rp(path, c="typ"):
    return sum(r_any(s, c) for s in path)


# ring: shared isense <-> bgr ground path (east outer column, corner, south outer row)
RING_ISN_BGR = [seg("TM1", 380.0, 15.0, "east outer VSS column TopMetal1, y 715 -> 335"),
                via("TV2", via_count(15, 15, "TV2"), "corner TopVia2"),
                seg("TM2", 986.0, 15.0, "south outer VSS row TopMetal2, x 1368 -> 382")]
out = {"method": __doc__.strip().splitlines()[0], "currents_mA": I, "current_sources": I_SRC, "tables": {}}
for name, tab in [("VDDA", VDDA), ("VDD", VDD), ("VSS", VSS)]:
    rows = {}
    for k, p in tab.items():
        rows[k] = {c: round(Rp(p, c), 3) for c in CORNER}
        rows[k]["segments"] = [s.get("what", "") for s in p]
    out["tables"][name] = rows
shared = VSS["u_isense (to the east outer column)"] + RING_ISN_BGR + VSS["u_bgr (to the south outer row)"]
out["isense_bgr_shared_vss_ohm"] = {c: round(Rp(shared, c), 3) for c in CORNER}
# ring paths (VDD, from pad 1 at x 495 south; inner columns 17 / 15 um; cut west column replaced by TopMetal2)
west = Rp([seg("TM1", 365.0, 17.0, ""), seg("TM2", 534.0, 17.0, ""), seg("TM1", 91.0, 17.0, ""),
           seg("TM2", 142.0, 15.0, "")])
east = Rp([seg("TM1", 990.0, 15.0, ""), seg("TM2", 853.0, 15.0, "")])
north = Rp([seg("TM2", 220.0, 15.0, "")])
out["ring_vdd_pad1_to_north_row_ohm"] = round(west * east / (west + east) + north, 3)
# static drops (mV) at the block currents; shared trunk segments carry the sum of the loads beyond them
dr = {}
dr["VDDA u_afe far pin"] = (I["afe_VDDA"] + I["bgr_VDDA"] + I["bias_VDDA"] + I["t2f_VDDA"]) * \
    (Rp(FEED + WEST, "max")) + I["afe_VDDA"] * Rp(VDDA["u_afe (far pin x 520.8)"][len(FEED + WEST):], "max")
dr["VDDA u_adc"] = (I["adc_VDDA"] + I["afe_VDDA"] + I["bgr_VDDA"] + I["bias_VDDA"] + I["t2f_VDDA"]) * \
    Rp(FEED + [riser(137.0)], "max") + (I["adc_VDDA"] + I["afe_VDDA"] + 0.34) * Rp([trunk(727.0)], "max") + \
    I["adc_VDDA"] * Rp(VDDA["u_adc"][-2:], "max")
dr["VDDA u_isense"] = I["isense_VDDA"] * Rp(VDDA["u_isense"], "max")
dr["VDDA u_bias"] = (I["afe_VDDA"] + 0.34 + I["adc_VDDA"]) * Rp(FEED + WEST, "max") + I["bias_VDDA"] * \
    Rp(VDDA["u_bias"][len(FEED + WEST):], "max")
dr["VDD u_ctrl (ring from pad 1 + stripes)"] = I["ctrl_VDD"] * (out["ring_vdd_pad1_to_north_row_ohm"] *
                                                                  RS["TM1"][2] / RS["TM1"][1] +
                                                                  Rp(VDD["u_ctrl (7 TopMetal1 stripes)"], "max"))
dr["VDD u_isense"] = I["isense_VDD"] * Rp(VDD["u_isense"], "max")
dr["VSS isense - bgr ground offset (own current)"] = I["isense_VDDA"] + I["isense_VDD"]
dr["VSS isense - bgr ground offset (own current)"] *= Rp(shared, "max")
out["static_drop_mV_max_sheet"] = {k: round(v, 2) for k, v in dr.items()}
# EM at the block currents (top-level shapes; the macro pins are listed separately)
em = []
for name, Iv, layer, w in [("VDDA trunk Metal4 8 um (all VDDA)", 4.3, "M4", 8.0), ("pad-7 riser Metal4 6 um", 4.3, "M4", 6.0),
                           ("west VDDA riser Metal3 9.4 um", 2.34, "M3", 9.4), ("AFE VDDA rail Metal4 2.8 um", 2.0, "M4", 2.8),
                           ("isense VDDA Metal4 2 um", 0.45, "M4", 2.0), ("isense VDD Metal4 2 um", 1.138, "M4", 2.0),
                           ("ctrl VDD TopMetal1 stripe 2.2 um (1/7 of 33.4 mA)", 33.4 / 7, "TM1", 2.2),
                           ("ctrl VDD TopMetal1 stripe 2.2 um (all 33.4 mA in one stripe)", 33.4, "TM1", 2.2),
                           ("ADC vdda riser Metal3 2 um", 1.036, "M3", 2.0),
                           ("ADC vdda neck / pin Metal3 0.4 um", 1.036, "M3", 0.4),
                           ("ADC vdd neck / pin Metal3 0.4 um", 0.903, "M3", 0.4),
                           ("ADC vss neck / pin Metal3 0.4 um", 1.939, "M3", 0.4),
                           ("AFE vss pin Metal3 0.4 um (2 pins, half each)", 1.0, "M3", 0.4),
                           ("AFE vdd pin Metal3 0.4 um (2 pins, half each)", 1.0, "M3", 0.4),
                           ("safe vdda pin Metal3 0.4 um", 0.418, "M3", 0.4),
                           ("bias vdd neck Metal4 0.5 um", 0.05, "M4", 0.5),
                           ("osc vdd Metal4 2 um", 0.317, "M4", 2.0)]:
    lim = EM_LINE[layer] * w
    em.append({"item": name, "I_mA": round(Iv, 3), "limit_mA": round(lim, 3), "pass": Iv <= lim})
for name, Iv, v, n in [("ctrl VDD TopVia2 per stripe", 33.4 / 7, "TV2", via_count(2.2, 15.0, "TV2")),
                       ("isense VSS TopVia1 into the column", 1.588, "TV1", via_count(14.0, 21.0, "TV1")),
                       ("AFE VSS stack TopVia1", 2.0, "TV1", via_count(14.0, 4.0, "TV1")),
                       ("ADC vdda Via3 at the trunk", 1.036, "V3", via_count(2.0, 7.0, "V3"))]:
    lim = EM_VIA[v] * n
    em.append({"item": name, "I_mA": round(Iv, 3), "limit_mA": round(lim, 3), "vias": n, "pass": Iv <= lim})
out["em"] = em
json.dump(out, open(sys.argv[1], "w"), indent=1)
for name in ("VDDA", "VDD", "VSS"):
    print("\n%s" % name)
    for k, r in out["tables"][name].items():
        print("| %s | %.3f | %.3f | %.3f |" % (k, r["min"], r["typ"], r["max"]))
print("\nshared isense-bgr VSS", out["isense_bgr_shared_vss_ohm"])
print("ring VDD pad1 -> north row", out["ring_vdd_pad1_to_north_row_ohm"])
print("\ndrops", json.dumps(out["static_drop_mV_max_sheet"], indent=1))
for e in em:
    print("| %s | %.3f | %.3f | %s |" % (e["item"], e["I_mA"], e["limit_mA"], "passed" if e["pass"] else "failed"))

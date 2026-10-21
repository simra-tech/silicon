#!/usr/bin/env python3
"""Collect the revision-5 R2-4 results (sim/results/r5/ref5_<corner>_<option>.json) into ref5_options.json with the
estimated area of each reference option. Area (estimated from device sizes, no layout): MIM decoupling cell 70 x 70
um = 4900 um^2 (ndec, ndecl, 2 x nres), gate capacitor 50 x 50 um = 2500 um^2 (ncg), input filter 82 x 82 um =
6724 um^2, devices 2100 um^2 (revision-4 estimate) + 300 um^2 per extra follower group (opt3) or 2100 um^2 for a
second buffer (opt3b) or 400 um^2 for the two per-slice switches (opt2).
usage: sum_ref5.py"""
import glob
import json
import os
HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.join(HERE, "..", "results", "r5")
BLOCK = os.path.dirname(os.path.dirname(HERE))
out = {"label": "simulated R2-4 metrics (post_ref5.py) + estimated areas", "options": {}}
for f in sorted(x for x in glob.glob(os.path.join(R, "ref5_*.json")) if not x.endswith("ref5_options.json") and not x.endswith("_interp.json")):
    d = json.load(open(f))
    rj = json.load(open(os.path.join(BLOCK, "sim", "runs", d["run_buffer"], "run.json")))
    p = dict(msf=32, mib=160, ndec=6, ncg=1, msfl=8, mibl=40, ndecl=1, nres=3)
    ref = rj["ref_model"]
    for s, sfx in ((rj.get("ref_params") or "", ""), (rj.get("refl_params") or "", "_l" if ref == "opt3b" else "")):
        for kv in s.split(","):
            if "=" in kv:
                k, v = kv.split("=")
                p[k + sfx] = int(v) if v.isdigit() else v
    cells = p["ndec"] + (p["ndecl"] if ref == "opt3" else 0) + (2 * p["nres"] if ref == "opt2" else 0)
    dev = 2100 + {"opt3": 300 * max(1, p["msfl"] // 8), "opt3b": 2100, "opt2": 400}.get(ref, 0)
    if ref == "opt3b":
        cells += int(p.get("ndec_l", 1))
    area = 4900 * cells + 2500 * int(p["ncg"]) + 6724 + dev
    out["options"][os.path.basename(f)[5:-5]] = {
        "run": d["run_buffer"], "gmin": rj.get("gmin"), "ref_model": ref, "params": [rj.get("ref_params"), rj.get("refl_params")],
        "worst_case_lsb": round(d["max_abs_input_error_mid_eval_lsb"], 3), "after_gain_fit_lsb": round(d["max_abs_error_after_gain_fit_lsb"], 3),
        "final_residue_lsb": round(max(d["slices"][s]["max_abs_final_residue_error_lsb"] for s in "ab"), 3),
        "per_decision_lsb_a": d["slices"]["a"]["max_abs_error_vs_decision_lsb"],
        "idda_mA": round(d.get("idda_mA", 0), 3), "area_mm2_est": round(area * 1e-6, 4), "pass_0p25": d["pass_0p25_r24"]}
    fi = f[:-5] + "_interp.json"
    o = out["options"][os.path.basename(f)[5:-5]]
    o["base_ideal_run"] = d["run_ideal"]
    if os.path.exists(fi):
        # cross-check: two-ideal-run interpolation (valid only where both ideal runs take the same bits)
        o["worst_case_interp_lsb"] = round(json.load(open(fi))["max_abs_input_error_mid_eval_lsb"], 3)
        o["pass_0p25"] = bool(max(o["worst_case_lsb"], o["worst_case_interp_lsb"]) <= 0.25)
json.dump(out, open(os.path.join(R, "ref5_options.json"), "w"), indent=1)
for k, v in out["options"].items():
    print("%-16s worst %.3f gainfit %.3f resid %.3f IDDA %.3f area %.4f %s" % (k, v["worst_case_lsb"], v["after_gain_fit_lsb"], v["final_residue_lsb"], v["idda_mA"], v["area_mm2_est"], v["params"]))

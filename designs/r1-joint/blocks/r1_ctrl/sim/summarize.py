#!/usr/bin/env python3
"""Collect an r1_ctrl run into sim/results/<run-id>/: summary.md, run.json, small logs.
SPDX-License-Identifier: Apache-2.0"""
import glob
import json
import os
import re
import shutil
import sys

rid, out, summ = sys.argv[1:4]
ver = dict(l.strip().split(" ", 1) for l in open(f"{out}/versions.txt") if " " in l)
res = {"pos": {}, "top": {}, "syn": {}}
lines = [f"# r1_ctrl run {rid}", "", f"Tools: {ver.get('iverilog')}; {ver.get('yosys')}; Python {ver.get('python')}; "
         f"PDK commit {ver.get('pdk_commit')}. Date {ver.get('date_utc')}.", ""]

lines += ["## (a) V3 position: RTL against the floating-point reference (deg el)", "",
          "| Case | Head | RTL vs true max / rms | RTL vs true, mean removed max | RTL vs float reference max | tracked vs true (after settle) max, mean removed | lock (pairs) | velocity rel. error |",
          "| --- | --- | --- | --- | --- | --- | --- | --- |"]
for f in sorted(glob.glob(f"{out}/pos_*_result.json")):
    r = json.load(open(f))
    meta = json.load(open(f.replace("_result.json", "_meta.json")))
    h = meta["head"]
    m, rf, im, tr = (r["measured_vs_true_deg_el"], r["reference_vs_true_deg_el"],
                     r["rtl_vs_float_reference_deg_el"], r.get("tracked_vs_true_deg_el_after_settle", {}))
    res["pos"][r["case"]] = r
    head = (f"ofs {h['ofs']}, gain {h['gain']}, ph {h['ph']} deg, h3 {h['h3']}, f {h['f']/1e3:g} kHz, "
            f"noise {h['noise']} LSB, cal {'self' if h.get('self') else ('reference' if h['cal'] else 'none')}, extrap {h['extrap']}")
    lines.append(f"| {r['case']} | {head} | {m['max_abs']:.3f} / {m['rms']:.3f} | {m['max_abs_zeroed']:.3f} | "
                 f"{im['max_abs']:.4f} | {tr.get('max_abs_zeroed', float('nan')):.3f} | {r.get('lock_pairs_to_0p5deg_from_reset')} | "
                 f"{r.get('velocity_lsb_per_tick', {}).get('rel_err', float('nan')):+.4f} |")
lines += ["", "## (b..f) chip-level testbench", "", "| Log | Checks | Failed | Verdict |", "| --- | --- | --- | --- |"]
info = []
for f in sorted(glob.glob(f"{out}/top_*.log")):
    t = open(f).read()
    m = re.search(r"# (\d+) checks, (\d+) failed", t)
    ok = "ALL TESTS PASSED" in t
    n, nf = (int(m.group(1)), int(m.group(2))) if m else (0, -1)
    name = os.path.basename(f)
    res["top"][name] = dict(checks=n, failed=nf, passed=ok)
    lines.append(f"| {name} | {n} | {nf} | {'passed' if ok else 'FAILED'} |")
    info += [f"- `{name}`: {l[5:]}" for l in t.splitlines() if l.startswith("INFO") or l.startswith("FAIL")]
    shutil.copy(f, summ)
lines += ["", "Information lines:", ""] + info
st = open(f"{out}/syn/stat_flat.txt").read()
area = float(re.search(r"Chip area for module '\\r1_ctrl_top': ([\d.]+)", st).group(1))
seq = float(re.search(r"used for sequential elements: ([\d.]+)", st).group(1))
cells = int(re.search(r"^\s+(\d+)\s+[\d.E+]+\s+cells", st, re.M).group(1))
flops = sum(int(x) for x in re.findall(r"^\s+(\d+)\s+[\d.E+]+\s+sg13g2_(?:dfrbp|sdf|dll|dlh)\w*", st, re.M))
nand2 = 7.2576
res["syn"] = dict(cell_area_um2=area, seq_area_um2=seq, cells=cells, flops=flops,
                  kGE_nand2=area / nand2 / 1000, ratio_cell_area_to_0p18mm2=area / 180000.0,
                  macro_est_um2_at_g1_ratio=area * 129600 / 84796.0)
hier = {}
for mod, a in re.findall(r"Chip area for module '(.+?)': ([\d.]+)", open(f"{out}/syn/stat_hier.txt").read()):
    parts = mod.split("\\")
    key = parts[1] if len(parts) > 1 else mod
    hier[key] = hier.get(key, 0.0) + float(a)
res["syn"]["per_module_um2"] = hier
lines += ["", "## Synthesis (Yosys, sg13g2_stdcell typ 1.2 V 25 C, abc -D 33333)", "",
          f"- cells {cells}, flops {flops}, cell area {area:.0f} um2 ({area/nand2/1000:.1f} kGE at 7.26 um2 per nand2_1), "
          f"sequential {seq:.0f} um2 ({100*seq/area:.0f} %)",
          f"- ratio of cell area to the 0.18 mm2 digital budget: {area/180000:.2f}",
          f"- macro estimate at the G1 run7 ratio (129 600 um2 macro / 84 796 um2 synthesis): "
          f"{area*129600/84796/1e6:.3f} mm2 = {area*129600/84796/180000:.2f} x budget",
          "- per module (hierarchical synthesis, um2): " + ", ".join(f"{k} {v:.0f}" for k, v in sorted(hier.items(), key=lambda x: -x[1]) if v > 500)]
for f in ("stat_flat.txt", "stat_hier.txt"):
    shutil.copy(f"{out}/syn/{f}", summ)
for f in glob.glob(f"{out}/pos_*_check.log") + glob.glob(f"{out}/pos_*_result.json"):
    shutil.copy(f, summ)
shutil.copy(f"{out}/versions.txt", summ)
shutil.copy(f"{out}/inputs.sha256", summ)
open(f"{summ}/summary.md", "w").write("\n".join(lines) + "\n")
top_ok = all(v["passed"] for v in res["top"].values()) and len(res["top"]) == 9
pos_ok = all(v["rtl_vs_float_reference_deg_el"]["max_abs"] < 0.05 for v in res["pos"].values()) and len(res["pos"]) == 9
run = dict(
    run_id=rid,
    command="flow/run.sh sh sim/run_all.sh " + rid,
    container_image="tapeoutbench-eda:latest (id pinned in flow/run.sh)",
    tools=ver, pdk_commit=ver.get("pdk_commit"),
    inputs="inputs.sha256 (RTL, testbenches, scripts)",
    bulk_results="$G1_RESULTS_ROOT/r1_ctrl/" + rid,
    question="Does the r1_ctrl RTL (r1_pos, r1_bus, r1_gate logic, r1_safe FSM, registers) meet the V3 position, "
             "V4 protocol (S2 items 1-9) and V5 digital safety checks in simulation, and what is its synthesized "
             "cell area against the 0.18 mm2 budget?",
    result=res,
    disposition=("simulation checks passed" if (top_ok and pos_ok) else "simulation checks FAILED (see summary.md)")
                + f"; cell area {area/1e6:.3f} mm2 = {area/180000:.2f} x the 0.18 mm2 budget (before placement)",
)
json.dump(run, open(f"{summ}/run.json", "w"), indent=1)
print("\n".join(lines))

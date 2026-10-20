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
# per-block cell area, children included (hierarchical synthesis): each
# top-level instance type of r1_ctrl_top with its sub-modules (r1_cword
# latches, r1_adcw, r1_sinlut, r1_sync2 ...), plus the top-level glue
sec, local, kids, cur = {}, {}, {}, None
for l in open(f"{out}/syn/stat_hier.txt"):
    m = re.match(r"^=== (.+) ===$", l.strip())
    if m:
        cur = m.group(1); kids[cur] = []; continue
    m = re.match(r"^\s+Chip area for module '(.+?)': ([\d.]+)", l)
    if m:
        local[m.group(1).lstrip("\\")] = float(m.group(2)); continue
    m = re.match(r"^\s+(\d+)\s+-\s+(\S+)\s*$", l)
    if m and cur and (m.group(2).startswith("r1_") or m.group(2).startswith("$paramod")):
        kids[cur].append((int(m.group(1)), m.group(2)))
def incl(mod):
    return local.get(mod, 0.0) + sum(n * incl(c) for n, c in kids.get(mod, []))
def base(mod):
    b = mod.split("\\")[-1] if "\\" in mod else mod
    return re.sub(r"\\.*", "", b)
hier = {"r1_ctrl_top (glue)": local.get("r1_ctrl_top", 0.0)}
for n, c in kids.get("r1_ctrl_top", []):
    k = base(c) if not c.startswith("$paramod") else re.split(r"\\", c)[1]
    hier[k] = hier.get(k, 0.0) + n * incl(c)
res["syn"]["per_block_um2_incl_children"] = hier
res["syn"]["hier_total_um2"] = incl("r1_ctrl_top")
lines += ["", "## Synthesis (Yosys, sg13g2_stdcell typ 1.2 V 25 C, Booth, PDK latch map, abc -D 23810)", "",
          f"- cells {cells}, flops {flops}, cell area {area:.0f} um2 ({area/nand2/1000:.1f} kGE at 7.26 um2 per nand2_1), "
          f"sequential {seq:.0f} um2 ({100*seq/area:.0f} %)",
          f"- ratio of cell area to the 0.18 mm2 cell-area target (0.28 mm2 placed at about 65 %): {area/180000:.2f}",
          f"- macro estimate at the G1 run7 ratio (129 600 um2 macro / 84 796 um2 synthesis): "
          f"{area*129600/84796/1e6:.3f} mm2 = {area*129600/84796/180000:.2f} x budget",
          f"- per block, children included (hierarchical synthesis, total {incl('r1_ctrl_top'):.0f} um2; "
          "the flat run optimises across blocks): " + ", ".join(f"{k} {v:.0f}" for k, v in sorted(hier.items(), key=lambda x: -x[1]))]
# ADC weight correction (tb_adcw + adcw_ref.py)
aw = json.load(open(f"{out}/adcw/adcw_result.json"))
res["adcw"] = aw
lines += ["", "## ADC weight correction (r1_adcw, tb_adcw + adcw_ref.py, mismatched-CDAC example)", "",
          "| Weights | max abs DNL (LSB) | max abs INL (LSB) | missing codes | RTL vs integer model mismatches |",
          "| --- | --- | --- | --- | --- |"]
for k in ("bin", "cal"):
    r = aw[k]
    lines.append(f"| {'binary (reset)' if k == 'bin' else 'calibrated (1/4 LSB)'} | {r['max_abs_dnl']:.3f} | "
                 f"{r['max_abs_inl']:.3f} | {r['missing_codes']} | {r['mismatches_vs_model']} |")
lines += ["", "Model-only weight-resolution sweep (same raw decisions): " + "; ".join(
          f"{k}: DNL {v['max_abs_dnl']:.3f}, INL {v['max_abs_inl']:.3f}, missing {v['missing_codes']}"
          for k, v in aw["model_weight_resolution_sweep"].items()),
          f"Checks: {aw['checks']}; verdict {'passed' if aw['passed'] else 'FAILED'}."]
shutil.copy(f"{out}/adcw/adcw_result.json", summ)
shutil.copy(f"{out}/adcw/adcw_meta.json", summ)
for f in ("stat_flat.txt", "stat_hier.txt"):
    shutil.copy(f"{out}/syn/{f}", summ)
for f in glob.glob(f"{out}/pos_*_check.log") + glob.glob(f"{out}/pos_*_result.json"):
    shutil.copy(f, summ)
shutil.copy(f"{out}/versions.txt", summ)
shutil.copy(f"{out}/inputs.sha256", summ)
open(f"{summ}/summary.md", "w").write("\n".join(lines) + "\n")
top_ok = all(v["passed"] for v in res["top"].values()) and len(res["top"]) == 10
pos_ok = all(v["rtl_vs_float_reference_deg_el"]["max_abs"] < 0.05 for v in res["pos"].values()) and len(res["pos"]) == 9
run = dict(
    run_id=rid,
    command="flow/run.sh sh sim/run_all.sh " + rid,
    container_image="tapeoutbench-eda:latest (id pinned in flow/run.sh)",
    tools=ver, pdk_commit=ver.get("pdk_commit"),
    inputs="inputs.sha256 (RTL, testbenches, scripts)",
    bulk_results="$G1_RESULTS_ROOT/r1_ctrl/" + rid,
    question="Does the r1_ctrl revision 0.2 RTL (r1_pos, r1_bus, r1_gate logic, r1_safe FSM, comparator "
             "calibration, ADC weight correction, registers) meet the V3 position, V4 protocol (S2 items 1-9, "
             "BiSS D2 control channel) and V5 digital safety checks in simulation, and what is its synthesized "
             "cell area against the 0.18 mm2 cell-area target?",
    result=res,
    disposition=("simulation checks passed" if (top_ok and pos_ok and aw["passed"]) else "simulation checks FAILED (see summary.md)")
                + f"; cell area {area/1e6:.3f} mm2 = {area/180000:.2f} x the 0.18 mm2 budget (before placement)",
)
json.dump(run, open(f"{summ}/run.json", "w"), indent=1)
print("\n".join(lines))

# SPDX-License-Identifier: Apache-2.0
"""Write run.json for one r1_top try-h0 run (track T8f; copy of write_run_json_g.py).

  python3 write_run_json_h.py <run_dir> <question> <disposition>

Runs flow/write_run_json.py (the try-e/f writer) and adds the try-g items: the input snapshot list
(inputs/inputs.sha256), the try-g generator records (merged standard cells, removed antenna diodes, south VDD feed,
south supply stacks), the supply and skew result files and the CPU set 112-119. Paths use <G1_RESULTS_ROOT>.
"""
import json
import os
import runpy
import sys

run = sys.argv[1]
sys.argv = [os.path.join(os.path.dirname(__file__), "write_run_json.py")] + sys.argv[1:4] + ["run_try_h.sh"]
runpy.run_path(sys.argv[0], run_name="__main__")
p = os.path.join(run, "run.json")
r = json.load(open(p))
asm = json.load(open(os.path.join(run, "r1_top_assembly.json")))
name = r["run"]
r["track"] = "T8f (r1_top supply feed redesign, try h0)"
r["tools"]["cpuset"] = "112-119"
snap = os.path.join(run, "inputs", "inputs.sha256")
if os.path.exists(snap):
    r["input_snapshots"]["inputs/inputs.sha256"] = [
        l.replace(os.environ.get("G1_RESULTS_ROOT", "/nonexistent"), "<G1_RESULTS_ROOT>")
        for l in open(snap).read().splitlines()]
for k in ("try", "antenna_diodes_removed", "merged_std_cells", "south_vdd_feed", "south_supply_stacks", "supply_h_feed"):
    if k in asm:
        r[k] = asm[k]
for f in ("supply_h0.json", "clk_skew_g.json"):
    r.setdefault("results", {})[f] = ("<G1_RESULTS_ROOT>/r1_top/%s/%s" % (name, f)
                                      if os.path.exists(os.path.join(run, f)) else "not run")
s = json.dumps(r, indent=1)
root = os.environ.get("G1_RESULTS_ROOT")
if root:
    s = s.replace(root, "<G1_RESULTS_ROOT>")
open(p, "w").write(s)
print("run.json (try h0)", name)

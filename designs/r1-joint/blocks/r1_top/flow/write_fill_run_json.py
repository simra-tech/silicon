# SPDX-License-Identifier: Apache-2.0
"""Write run.json for one r1_top fill run (track T8).

  python3 write_fill_run_json.py <fill run dir> <source run dir> <question> <disposition> <out.json>

Reads fill_exclusions.json, fill_counts.json, filler_macro_diff.txt, checks_steps.log and the check directories.
Paths are written relative to the results root (<G1_RESULTS_ROOT>) or to the repository root.
"""
import glob
import hashlib
import json
import os
import re
import sys

run, src, question, disposition, out = sys.argv[1:6]
name, sname = os.path.basename(run.rstrip("/")), os.path.basename(src.rstrip("/"))

def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()

def rd(p):
    return open(p).read() if os.path.exists(p) else ""

def js(p):
    return json.load(open(p)) if os.path.exists(p) else {}

ex, cnt = js(os.path.join(run, "fill_exclusions.json")), js(os.path.join(run, "fill_counts.json"))
checks = {}
for c in ("main", "maximal", "density", "antenna"):
    d = os.path.join(run, "drc_" + c)
    s = os.path.join(d, "summary.json")
    if not os.path.exists(s):
        checks["drc_" + c] = {"state": "not run" if not os.path.isdir(d) else "incomplete (no summary)"}
        continue
    j = js(s)
    m = re.findall(r"^exit (\d+)", rd(os.path.join(d, "console.log")), re.M)
    checks["drc_" + c] = {"state": "completed", "exit": m[-1] if m else None, "total": j["total"],
                          "rules": {k: v["count"] for k, v in j["rules"].items()},
                          "evidence": "<G1_RESULTS_ROOT>/r1_top/%s/drc_%s/" % (name, c)}
mk = js(os.path.join(run, "drc_density", "markers.json"))
if mk:
    checks["drc_density"]["markers_overlapping_adc_box"] = mk["overlap_adc"]
    checks["drc_density"]["markers_not_overlapping_adc_box"] = mk["not_overlapping_adc"]
lv = rd(os.path.join(run, "lvs_limits", "console.log"))
checks["lvs_limits"] = {"state": ("match" if "Congratulations! Netlists match" in lv else
                                  "no match" if "Netlists don't match" in lv else "not run or no result"),
                        "evidence": "<G1_RESULTS_ROOT>/r1_top/%s/lvs_limits/" % name}
bm = js(os.path.join(run, "bondmap", "verify_bondmap_chip.json"))
checks["bondmap"] = {"state": "not run"} if not bm else {
    "state": "passed" if bm.get("all_ok") else "failed", "openings_in_gds": bm.get("openings_in_gds"), "rows": bm.get("rows"),
    "labels_134_25": bm.get("labels_134_25"), "openings_unmatched": bm.get("openings_unmatched"),
    "evidence": "<G1_RESULTS_ROOT>/r1_top/%s/bondmap/" % name}
rec = {
    "run": name, "track": "T8 (r1_top chip fill)", "question": question,
    "command": "sh designs/r1-joint/blocks/r1_top/flow/fill_top.sh <G1_RESULTS_ROOT>/r1_top/%s <G1_RESULTS_ROOT>/r1_top/%s [args]; "
               "sh designs/r1-joint/blocks/r1_top/flow/run_fill_checks.sh <source> <run>" % (sname, name),
    "tools": {"klayout": "0.30.9 (container)", "container": "tapeoutbench-eda:latest sha256:ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2",
              "cpuset": "116-119"},
    "pdk_commit": "84374023ee8b4b126bebbba67fcbada0a9c0ff0b",
    "input": {"source_run": sname, "gds": "<G1_RESULTS_ROOT>/r1_top/%s/r1_top.gds" % sname,
              "sha256": rd(os.path.join(run, "input_gds.sha256")).split()[0] if rd(os.path.join(run, "input_gds.sha256")) else None},
    "output": {"gds": "<G1_RESULTS_ROOT>/r1_top/%s/r1_top.gds" % name,
               "sha256": sha(os.path.join(run, "r1_top.gds")) if os.path.exists(os.path.join(run, "r1_top.gds")) else None},
    "filler_macro_changes_against_pdk": rd(os.path.join(run, "filler_macro_diff.txt")).strip().splitlines(),
    "exclusions": {k: ex.get(k) for k in ("thru", "ring_depth_um", "halo_um", "bond_openings", "excluded_area_um2", "deleted_orphan_cells")},
    "excluded_instances": ex.get("instances"),
    "fill": {"layers": cnt.get("layers"), "cells": cnt.get("cells"), "gate_passed": cnt.get("gate_passed")},
    "steps_log": rd(os.path.join(run, "checks_steps.log")).strip().splitlines(),
    "checks": checks, "disposition": disposition,
}
json.dump(rec, open(out, "w"), indent=1)
print("wrote", out)

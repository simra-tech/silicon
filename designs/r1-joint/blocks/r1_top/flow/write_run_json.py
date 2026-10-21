# SPDX-License-Identifier: Apache-2.0
"""Write run.json for one r1_top assembly try (track T8).

  python3 write_run_json.py <run_dir> <question> <disposition>

Reads r1_top_assembly.json, cdl/r1_top_cdl.json, steps.log and the check directories of the run.
Paths are written relative to the results root (<G1_RESULTS_ROOT>) or to the repository root.
"""
import glob
import hashlib
import json
import os
import re
import sys

run, question, disposition = sys.argv[1:4]
name = os.path.basename(run.rstrip("/"))

def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()

def rd(p):
    return open(p).read() if os.path.exists(p) else ""

asm = json.load(open(os.path.join(run, "r1_top_assembly.json")))
cdl = json.load(open(os.path.join(run, "cdl", "r1_top_cdl.json"))) if os.path.exists(os.path.join(run, "cdl", "r1_top_cdl.json")) else {}

checks = {}
for c in ("main", "maximal", "density", "antenna"):
    d = os.path.join(run, "drc_" + c)
    if not os.path.isdir(d):
        checks["drc_" + c] = {"state": "not run"}
        continue
    s = os.path.join(d, "summary.json")
    con = rd(os.path.join(d, "console.log"))
    m = re.findall(r"^exit (\d+)", con, re.M)
    if os.path.exists(s):
        j = json.load(open(s))
        checks["drc_" + c] = {"state": "completed", "exit": m[-1] if m else None, "total": j["total"],
                              "class_a": j["total_a"], "class_b": j["total_b"],
                              "rules": {k: v["count"] for k, v in j["rules"].items()},
                              "evidence": "<G1_RESULTS_ROOT>/r1_top/%s/drc_%s/" % (name, c)}
    else:
        checks["drc_" + c] = {"state": "incomplete (no summary)", "exit": m[-1] if m else None}
for mode in ("limits", "stock"):
    d = os.path.join(run, "lvs_" + mode)
    if not os.path.isdir(d):
        checks["lvs_" + mode] = {"state": "not run"}
        continue
    con = rd(os.path.join(d, "console.log"))
    if "Congratulations! Netlists match" in con:
        st = "match"
    elif "Netlists don't match" in con:
        st = "no match"
    elif os.path.exists(os.path.join(d, "exit.txt")):
        st = "ended without a comparison result (%s)" % rd(os.path.join(d, "exit.txt")).strip()
    else:
        st = "incomplete"
    checks["lvs_" + mode] = {"state": st, "start": rd(os.path.join(d, "start.txt")).strip(),
                             "end": rd(os.path.join(d, "end.txt")).strip(),
                             "exit": rd(os.path.join(d, "exit.txt")).strip(),
                             "deck": "PDK deck unmodified" if mode == "stock" else
                                     "run-time copy of the PDK LVS directory with max_depth(8) and max_branch_complexity(100) after align",
                             "evidence": "<G1_RESULTS_ROOT>/r1_top/%s/lvs_%s/" % (name, mode)}

res = {
    "run": name,
    "track": "T8 (r1_top assembly, P3 preparation)",
    "question": question,
    "command": "sh designs/r1-joint/blocks/r1_top/flow/run_try.sh %s <steps>  (steps in steps.log)" % name,
    "steps_log": rd(os.path.join(run, "steps.log")).splitlines(),
    "tools": {"klayout": "0.30.9 (container)", "python": "3 (container)",
              "container": "tapeoutbench-eda:latest sha256:ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2",
              "cpuset": "116-119"},
    "pdk_commit": "84374023ee8b4b126bebbba67fcbada0a9c0ff0b",
    "inputs": {r["instance"]: {"macro": r["macro"], "source": r["source"], "sha256": r["source_sha256"]}
               for r in asm["placement"]},
    "lvs_reference_inputs": cdl.get("inputs", {}),
    "placeholders": {k: [p["pin"] for p in v] for k, v in asm["placeholder_pins"].items()},
    "outputs": {"r1_top.gds": asm["gds_sha256"],
                "cdl/r1_top.cdl": cdl.get("output_sha256"),
                "r1_top.png": sha(os.path.join(run, "r1_top.png")) if os.path.exists(os.path.join(run, "r1_top.png")) else None},
    "self_check": {"net_conflicts": len(asm["self_check_net_conflicts"]), "instance_overlaps": asm["instance_overlaps"],
                   "outside_io_row": asm["outside_io_row"]},
    "ring_eco": asm["ring_eco"],
    "antenna_decap_row": asm.get("antenna_decap_row"),
    "checks": checks,
    "disposition": disposition,
}
json.dump(res, open(os.path.join(run, "run.json"), "w"), indent=1)
print("run.json", name, {k: v.get("state") for k, v in checks.items()})

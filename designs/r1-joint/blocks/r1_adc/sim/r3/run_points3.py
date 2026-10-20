#!/usr/bin/env python3
"""Run tb_adc3_points.cir for a list of per-slot inputs, with automatic resume after a numerical abort.

usage: run_points3.py --id <run id> --cpu N --points <json: {"a": [...], "b": [...]}> [--corner mos_tt --temp 27
       --vdd 1.2 --timing r1_adc_timing_r3.inc --core r1_adc3_core_fast --ref ideal|buf[:msf,mib,ndec,ncg]
       --vref 1.0 --save codes|full --question "..."]
Writes sim/results/r3/<id>_segments.json (run ids, first slot, number of slots kept) for the post-processors.
Options: reltol=1e-4 vntol=1e-6 abstol=1e-12 method=trap klu rshunt=1e12, tmax 0.2 ns (revision-2 finding);
a resumed segment uses tmax 0.25 ns.
"""
import argparse
import json
import os
import re
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
BLOCK = os.path.dirname(os.path.dirname(HERE))
T0, SLOT = 0.6e-6, 0.6e-6

ap = argparse.ArgumentParser()
ap.add_argument("--id", required=True)
ap.add_argument("--cpu", required=True)
ap.add_argument("--points", required=True)
ap.add_argument("--corner", default="mos_tt")
ap.add_argument("--temp", default="27")
ap.add_argument("--vdd", default="1.2")
ap.add_argument("--cm", default="0.6")
ap.add_argument("--timing", default="r1_adc_timing_r3.inc")
ap.add_argument("--core", default="r1_adc3_core_fast")
ap.add_argument("--ref", default="ideal")
ap.add_argument("--vref", default="1.0")
ap.add_argument("--save", default="codes")
ap.add_argument("--question", default="")
ap.add_argument("--timeout", default="21600")
a = ap.parse_args()
P = json.load(open(a.points))
va, vb = P["a"], P["b"]
n_all = len(va)


def pwl(v):
    pts = []
    for s, x in enumerate(v):
        t = 0.0 if s == 0 else T0 + s * SLOT - 550e-9
        if s:
            pts.append("%.6e %.7f" % (t, v[s - 1]))
            pts.append("%.6e %.7f" % (t + 10e-9, x))
        else:
            pts.append("0 %.7f" % x)
    out, line = [], []
    for p in pts:
        line.append(p)
        if len(line) == 8:
            out.append(" ".join(line))
            line = []
    if line:
        out.append(" ".join(line))
    return "\n+ ".join(out)


if a.ref == "ideal":
    reflines = "Vref vref 0 %s" % a.vref
else:
    prm = (a.ref.split(":")[1] if ":" in a.ref else "").split(",")
    extra = " ".join("%s=%s" % (k, v) for k, v in zip(("msf", "mib", "ndec", "ncg"), prm) if v)
    reflines = "Vdda vdda 0 3.3\nVbg vbg 0 1.045\nXREF vbg vref vdda 0 r1_refbuf3 %s" % extra
save = ("v(rawa) v(rawb)" if a.save == "codes" else
        "v(rawa) v(rawb) v(vref) v(topap) v(topan) v(topbp) v(topbn) i(vdd) v(mclk) v(trka0) v(trka1)")
if a.ref != "ideal":
    save += " v(vref) i(vdda)"
opts = "reltol=1e-4 vntol=1e-6 abstol=1e-12 method=trap klu rshunt=1e12" + (" interp" if a.save == "codes" else "")
segs, start, k = [], 0, 0
while start < n_all and k < 10:
    rid = a.id if k == 0 else "%s-r%d" % (a.id, k)
    sa, sb = va[start:], vb[start:]
    tstop = "%.4fu" % ((T0 + (len(sa) - 1) * SLOT + 0.3e-6) * 1e6)
    cmd = ["python3", "sim/run_ngspice.py", "--deck", "sim/r3/tb_adc3_points.cir", "--run-id", rid, "--cpuset", a.cpu,
           "--sub", "CORNER=" + a.corner, "--sub", "TEMP=" + a.temp, "--sub", "VDD=" + a.vdd, "--sub", "CM=" + a.cm,
           "--sub", "CORE=" + a.core, "--sub", "TIMING=" + a.timing, "--sub", "OPTS=" + opts,
           "--sub", "TMAX=" + ("0.2n" if k % 2 == 0 else "0.25n"), "--sub", "TSTOP=" + tstop,
           "--sub", "PWLA=" + pwl(sa), "--sub", "PWLB=" + pwl(sb), "--sub", "REFLINES=" + reflines,
           "--sub", "SAVE=" + save, "--timeout", a.timeout,
           "--question", a.question + (" (slots %d.. of %s; resume %d after a numerical abort)" % (start, a.id, k) if k else "")]
    subprocess.call(cmd, cwd=BLOCK)
    rj = os.path.join(BLOCK, "sim", "runs", rid, "run.json")
    log = open(os.path.join(BLOCK, "sim", "runs", rid, "ngspice.log"), errors="replace").read()
    m = re.search(r"Timestep too small; time = ([0-9.eE+-]+)", log)
    d = json.load(open(rj))
    d["points_file"] = os.path.relpath(a.points, BLOCK) if os.path.isabs(a.points) else a.points
    d["first_slot"] = start
    if m:
        tab = float(m.group(1))
        done = max(0, int((tab - T0 - 240e-9) // SLOT) + 1)
        done = min(done, len(sa))
        d["result"] = "numerical abort at %.4g s; slots %d..%d kept" % (tab, start, start + done - 1)
        d["disposition"] = "partial (resumed in %s-r%d)" % (a.id, k + 1)
    else:
        done = len(sa) if d["status"] == "completed" else 0
    json.dump(d, open(rj, "w"), indent=2)
    if done > 0:
        segs.append({"run_id": rid, "first_slot": start, "slots": done})
    if done == 0:
        done = 1                       # skip the slot that aborts at its own edge
    start += done
    k += 1
json.dump({"id": a.id, "points": d["points_file"], "segments": segs, "slots_total": n_all},
          open(os.path.join(BLOCK, "sim", "results", "r3", a.id + "_segments.json"), "w"), indent=1)
print("segments:", segs)

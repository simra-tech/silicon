#!/usr/bin/env python3
"""Run a revision-2 static ramp (tb_adc2_static.cir) with automatic resume after a numerical abort.

usage: run_static2.py --id <run-id base> --cpu N --corner mos_tt --temp 27 --vdd 1.2 --timing r1_adc_timing_r2.inc
                      --vstart V --vstep V --frames N [--core r1_adc2_core_fast_a] [--question "..."]

ngspice sometimes stops with "Timestep too small" inside a long conversion deck (revision 1, open issue 9; the
same frame runs in a fresh run). After an abort at time t, the frames whose slice-A word was latched before t
are kept and a new run (<id>-r<k>, tmax alternating 0.2 ns / 0.25 ns) starts at the next frame. The list of segments
(raw file, vstart, frames used) is written to sim/results/r2/<id>_segments.json for post_adc2.py.
Simulator options: reltol=1e-4 with tmax 0.2 ns. Looser settings (reltol 1e-3 with tmax 5 ns, or reltol 1e-4
with tmax 5 ns) give wrong comparator decisions for residues up to about 6 mV or 0.3 mV (runs r2-dbg-probe-c2048,
r2-dbg-probe1024-*, r2-dbg-cmptol-*).
"""
import argparse
import json
import os
import re
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
BLOCK = os.path.dirname(os.path.dirname(HERE))
T = 1.0 / 30e6

ap = argparse.ArgumentParser()
for k in ("id", "cpu", "corner", "temp", "vdd", "timing", "vstart", "vstep", "frames"):
    ap.add_argument("--" + k, required=True)
ap.add_argument("--core", default="r1_adc2_core_fast_a")
ap.add_argument("--kind", default="static", choices=["static", "dyn"])
ap.add_argument("--amp", default="0.88")
ap.add_argument("--fin", default="0")
ap.add_argument("--question", default="")
a = ap.parse_args()
root = os.environ["G1_RESULTS_ROOT"]
v0, vs, nleft = float(a.vstart), float(a.vstep), int(a.frames)
segs = []
k = 0
while nleft > 0 and k < 8:
    rid = a.id if k == 0 else "%s-r%d" % (a.id, k)
    tstop = "%.3fu" % (0.6 + nleft + 0.1)
    deck = "sim/r2/tb_adc2_static.cir" if a.kind == "static" else "sim/r2/tb_adc2_dyn.cir"
    extra = [] if a.kind == "static" else ["--sub", "AMP=" + a.amp, "--sub", "FIN=" + a.fin,
                                           "--sub", "TOFF=%.9e" % (v0 * 1e-6)]
    cmd = ["python3", "sim/run_ngspice.py", "--deck", deck, "--run-id", rid, "--cpuset", a.cpu] + extra + [
           "--sub", "CORNER=" + a.corner, "--sub", "TEMP=" + a.temp, "--sub", "VDD=" + a.vdd, "--sub", "VREF=1.0",
           "--sub", "VSTART=%.7f" % v0, "--sub", "VSTEP=%.6e" % vs, "--sub", "TSTOP=" + tstop, "--sub", "CORE=" + a.core,
           "--sub", "TIMING=" + a.timing, "--sub", "TMAX=%s" % ("0.2n" if k % 2 == 0 else "0.25n"),
           "--sub", "OPTS=reltol=1e-4 vntol=1e-6 abstol=1e-12 method=trap klu rshunt=1e12", "--timeout", "14400",
           "--question", (a.question + (" (resume %d after a numerical abort)" % k if k else ""))]
    if a.kind == "dyn":
        cmd = [c for c in cmd]
    subprocess.call(cmd, cwd=BLOCK)
    log = open(os.path.join(BLOCK, "sim", "runs", rid, "ngspice.log"), errors="replace").read()
    m = re.search(r"Timestep too small; time = ([0-9.eE+-]+)", log)
    raw = os.path.join(root, "r1_adc", rid, "codes.raw")
    if m:
        tab = float(m.group(1))
        done = max(0, int((tab - 0.6e-6 - 13 * T) // 1e-6) + 1)
        done = min(done, nleft)
        rj = os.path.join(BLOCK, "sim", "runs", rid, "run.json")
        d = json.load(open(rj))
        d["result"] = "numerical abort at %.4g s; frames 0..%d of this segment kept" % (tab, done - 1)
        d["disposition"] = "partial (resumed in %s-r%d)" % (a.id, k + 1)
        json.dump(d, open(rj, "w"), indent=2)
    else:
        done = nleft
    if done > 0 and os.path.exists(raw):
        segs.append({"run_id": rid, "raw": "r1_adc/%s/codes.raw" % rid, "vstart": v0, "frames": done})
    v0 += done * vs
    nleft -= done
    k += 1
    if done == 0:
        v0 += vs          # skip one frame if the abort happened in the first frame
        nleft -= 1
json.dump({"id": a.id, "vstep": vs, "segments": segs, "frames_missing_at_end": nleft},
          open(os.path.join(BLOCK, "sim", "results", "r2", a.id + "_segments.json"), "w"), indent=1)
print("segments:", segs)

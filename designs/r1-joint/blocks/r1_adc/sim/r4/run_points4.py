#!/usr/bin/env python3
"""Run tb_adc4_points.cir for a list of per-frame inputs (D18 frame), with resume after a numerical abort only.

usage: run_points4.py --id <run id> --cpu N --points <json: {"a": [...], "b": [...]}> [--corner mos_tt --temp 27
       --vdd 1.2 --stag N --core r1_adc4_core_fast --ref ideal|buf[:msf,mib,ndec,ncg] --refl same|buf[:...]
       --vref 1.0 --save codes|full --mc K --seed S --question "..." --disposition "..."]
Writes sim/results/r4/<id>_segments.json (run ids, first frame, number of frames kept) for the post-processors.
Options: reltol=1e-4 vntol=1e-6 abstol=1e-12 gmin=<--gmin> method=trap klu rshunt=1e12, tmax 0.2 ns (revision-2
finding); a resumed segment uses tmax 0.25 ns. --gmin default 1e-9: the revision-4 operating point does not converge
with the default 1e-12 (runs r4-dbg-op-a..c) and not at 1e-10 for MC decks and some ideal runs (r4-dbg-opmc-a..c,
r4-ref-tt-n0-ideal10054). Runs before 23:45 CEST 2026-10-20 used 1e-10 (recorded in each run.json).
Stop rule (revision 4): a run that fails without "Timestep too small" in its log (netlist error, timeout, other)
stops the runner: no resubmission, no skipped frame. A numerical abort resumes at the first frame not converted.
--mc K: K instances of r1_adc4_core_fast_mc (MIM mismatch, cap_typ_mismatch, seed S), outputs m<i>rawa/b; each
instance gives two slice samples.
"""
import argparse
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BLOCK = os.path.dirname(os.path.dirname(HERE))
T = 1.0 / 30e6
F, T0 = 22 * T, 18 * T

ap = argparse.ArgumentParser()
ap.add_argument("--id", required=True)
ap.add_argument("--cpu", required=True)
ap.add_argument("--points", required=True)
ap.add_argument("--corner", default="mos_tt")
ap.add_argument("--temp", default="27")
ap.add_argument("--vdd", default="1.2")
ap.add_argument("--cm", default="0.6")
ap.add_argument("--stag", type=int, default=0)
ap.add_argument("--core", default="r1_adc4_core_fast")
ap.add_argument("--ref", default="ideal")
ap.add_argument("--refl", default="same")
ap.add_argument("--vref", default="1.0")
ap.add_argument("--save", default="codes")
ap.add_argument("--mc", type=int, default=0)
ap.add_argument("--seed", type=int, default=1)
ap.add_argument("--question", default="")
ap.add_argument("--disposition", default="")
ap.add_argument("--timeout", default="21600")
ap.add_argument("--nodeset", default="", help="extra deck lines for the operating point, e.g. .nodeset v(vref)=1.004")
ap.add_argument("--gmin", default="1e-9")
ap.add_argument("--deck", default="sim/r4/tb_adc4_points.cir")
ap.add_argument("--refcell", default="r1_refbuf4", help="buffer cell (r1_refbuf4h needs --deck sim/r4/tb_adc4h_points.cir)")
ap.add_argument("--bgr", default="", help="bandgap Thevenin model 'R,w': source R and input filter MIM w (r1_reffilt4); default ideal 1.045 V")
ap.add_argument("--tie", default="v", help="vrefl tie when --refl same: v (0 V source) or r (1 mohm)")
a = ap.parse_args()
P = json.load(open(a.points))
va, vb = P["a"], P["b"]
n_all = len(va)
vtag = {"1.2": "", "1.08": "_vdd108", "1.32": "_vdd132"}[a.vdd]
timing = "r1_adc_timing_r4_n%d%s.inc" % (a.stag, vtag)


def pwl(v, off):
    pts = []
    for s, x in enumerate(v):
        if s:
            t = T0 + s * F - 550e-9 + off
            pts.append("%.6e %.7f" % (t, v[s - 1]))
            pts.append("%.6e %.7f" % (t + 10e-9, x))
        else:
            pts.append("0 %.7f" % x)
    out = [" ".join(pts[i:i + 8]) for i in range(0, len(pts), 8)]
    return "\n+ ".join(out)


def buf(spec, name, node):
    prm = (spec.split(":")[1] if ":" in spec else "").split(",")
    if any("=" in x for x in prm):
        extra = " ".join(x for x in prm if x)
    else:
        extra = " ".join("%s=%s" % (k, v) for k, v in zip(("msf", "mib", "ndec", "ncg"), prm) if v)
    return "%s vbg %s vdda 0 %s %s" % (name, node, a.refcell, extra)


if a.ref == "ideal":
    reflines = "Vref vref 0 %s" % a.vref
else:
    vbg = "Vbg vbg 0 1.045"
    if a.bgr:
        rs, cw = a.bgr.split(",")
        vbg = "Vbgi vbgi 0 1.045\nRbg vbgi vbg %s\nXCF vbg 0 r1_reffilt4 w=%s" % (rs, cw)
    reflines = "Vdda vdda 0 3.3\n" + vbg + "\n" + buf(a.ref, "XREF", "vref")
if a.refl == "same":
    reflines += "\nVrl vrefl vref 0" if a.tie == "v" else "\nRrl vrefl vref 1m"
elif a.refl == "ideal":
    reflines += "\nVrefl vrefl 0 %s" % a.vref
else:
    if a.ref == "ideal":
        reflines += "\nVdda vdda 0 3.3\nVbg vbg 0 1.045"
    reflines += "\n" + buf(a.refl, "XREFL", "vrefl")
if a.nodeset:
    reflines += "\n" + a.nodeset

STB = " ".join("stba%d" % k for k in range(14)) + "\n+ " + " ".join("stbb%d" % k for k in range(14))
if a.mc:
    inst = []
    for i in range(a.mc):
        inst.append("XM%d sinp sinn cosp cosn isap isan isap isan trka0 trka1 trkb0 trkb1 clk30 wina winb lata latb\n+ %s\n"
                    "+ m%drawa m%drawb m%dtpa m%dtna m%dtpb m%dtnb vdd vref vrefl 0 r1_adc4_core_fast_mc" % (i, STB, i, i, i, i, i, i))
    instances = "\n".join(inst)
    save = " ".join("v(m%drawa) v(m%drawb)" % (i, i) for i in range(a.mc))
    caplib = "cap_typ_mismatch"
else:
    instances = ("XADC sinp sinn cosp cosn isap isan isap isan trka0 trka1 trkb0 trkb1 clk30 wina winb lata latb\n+ %s\n"
                 "+ rawa rawb topap topan topbp topbn vdd vref vrefl 0 %s" % (STB, a.core))
    save = ("v(rawa) v(rawb)" if a.save == "codes" else
            "v(rawa) v(rawb) v(vref) v(vrefl) v(topap) v(topan) v(topbp) v(topbn) i(vdd) v(clk30) v(trka0) v(trkb0)")
    caplib = "cap_typ"
if a.ref != "ideal" or a.refl not in ("same", "ideal"):
    save += " i(vdda)"
# gmin: 1e-10 for the runs before 23:45 CEST 2026-10-20 (R2-4 option runs, ss sweep); 1e-9 from then on: the
# operating point failed at 1e-10 for the MC deck and for an ideal run at 1.0054 V (r4-ref-tt-n0-ideal10054)
opts = "reltol=1e-4 vntol=1e-6 abstol=1e-12 gmin=%s method=trap klu rshunt=1e12" % a.gmin + (" interp" if a.save == "codes" else "")
if a.mc:
    opts = opts + " seed=%d" % a.seed
segs, start, k, stopped = [], 0, 0, None
while start < n_all and k < 10:
    rid = a.id if k == 0 else "%s-r%d" % (a.id, k)
    sa, sb = va[start:], vb[start:]
    tstop = "%.4fu" % ((T0 + (len(sa) - 1) * F + a.stag * T + 14 * T + 60e-9) * 1e6)
    cmd = ["python3", "sim/run_ngspice.py", "--deck", a.deck, "--run-id", rid, "--cpuset", a.cpu,
           "--sub", "CORNER=" + a.corner, "--sub", "TEMP=" + a.temp, "--sub", "VDD=" + a.vdd, "--sub", "CM=" + a.cm,
           "--sub", "CAPLIB=" + caplib, "--sub", "TIMING=" + timing, "--sub", "OPTS=" + opts,
           "--sub", "TMAX=" + ("0.2n" if k % 2 == 0 else "0.25n"), "--sub", "TSTOP=" + tstop,
           "--sub", "PWLA=" + pwl(sa, 0.0), "--sub", "PWLB=" + pwl(sb, a.stag * T), "--sub", "REFLINES=" + reflines,
           "--sub", "INSTANCES=" + instances, "--sub", "SAVE=" + save, "--timeout", a.timeout,
           "--question", a.question + (" (frames %d.. of %s; resume %d after a numerical abort)" % (start, a.id, k) if k else "")]
    subprocess.call(cmd, cwd=BLOCK)
    rj = os.path.join(BLOCK, "sim", "runs", rid, "run.json")
    if not os.path.exists(rj):
        stopped = "run_ngspice.py wrote no run.json"
        break
    log = open(os.path.join(BLOCK, "sim", "runs", rid, "ngspice.log"), errors="replace").read()
    m = re.search(r"Timestep too small; time = ([0-9.eE+-]+)", log)
    d = json.load(open(rj))
    d["points_file"] = os.path.relpath(a.points, BLOCK) if os.path.isabs(a.points) else a.points
    d["first_slot"] = start
    d["n_stag"] = a.stag
    d["disposition"] = a.disposition
    if m:
        tab = float(m.group(1))
        done = max(0, int((tab - T0 - a.stag * T - 14 * T - 30e-9) // F) + 1)
        done = min(done, len(sa))
        d["result"] = "numerical abort at %.4g s; frames %d..%d kept" % (tab, start, start + done - 1)
        d["disposition"] = "partial (resumed in %s-r%d)" % (a.id, k + 1)
        if done == 0:
            # abort inside the first frame of this segment: deterministic, resuming would only skip frames
            d["disposition"] = "failed (numerical abort in the first frame of the segment): runner stopped"
            json.dump(d, open(rj, "w"), indent=2)
            stopped = "%s: %s" % (rid, d["result"])
            break
    elif d["status"] == "completed":
        done = len(sa)
    else:
        d["disposition"] = "failed (%s, no timestep abort): runner stopped, not resubmitted" % d["status"]
        json.dump(d, open(rj, "w"), indent=2)
        stopped = "%s %s: %s" % (rid, d["status"], "; ".join(d["errors"][:3]))
        break
    json.dump(d, open(rj, "w"), indent=2)
    if done > 0 and not (m and "skipped" in d["result"]):
        segs.append({"run_id": rid, "first_slot": start, "slots": done})
    start += done
    k += 1
json.dump({"id": a.id, "points": os.path.relpath(a.points, BLOCK) if os.path.isabs(a.points) else a.points,
           "n_stag": a.stag, "mc": a.mc, "seed": a.seed if a.mc else None, "segments": segs, "slots_total": n_all,
           "stopped": stopped}, open(os.path.join(BLOCK, "sim", "results", "r4", a.id + "_segments.json"), "w"), indent=1)
print("segments:", segs, "stopped:", stopped)
sys.exit(1 if stopped else 0)

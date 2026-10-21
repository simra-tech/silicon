#!/usr/bin/env python3
"""Run sim/r5/tb_adc5_points.cir for a list of per-frame inputs (D18 frame). Revision-5 runner.

usage: run_points5.py --id <run id> --cpu N --points <json: {"a": [...], "b": [...]}> [--corner mos_tt --temp 27
       --vdd 1.2 --cm 0.6 --core r1_adc5_core_fast --ref ideal|buf|opt2|opt3|opt3b --refp "k=v,..." --reflp "k=v,..."
       --vref 1.045 --bgr 190k,82u --noise tt|ss|none --gmin default|1e-15 --save codes|full --mc K --seed S
       --op-only --question "..." --disposition "..."]

Runner rules (revision 5, item 4; revision 4 resubmitted failed runs and its wrapper returned 0 on failure):
  * one ngspice job per call; no resume, no resubmission, no frame skipping. A job that is not "completed"
    (sim/r5/run_ngspice5.py: return code, abort lines in the log, missing raw file) ends the runner with exit 1.
  * <id>_segments.json lists the job as one segment only if it completed; otherwise "stopped" names the cause and
    "segments" is empty, so no post-processor can read a partial run as complete.
Options: reltol=1e-4 vntol=1e-6 abstol=1e-12 method=trap klu, tmax 0.2 ns (revision-2 finding), gmin = PDK
default (1e-12, no option) unless --gmin is given; no rshunt (revision 4 used rshunt=1e12 and gmin 1e-9/1e-10).
Reference models (every buffer deck: r1_bgr Thevenin source Rs + input filter + transient noise, coordinator
2026-10-21):
  ideal  Vref = --vref on all four reference ports
  buf    r1_refbuf5h (baseline: no input divider, 10 pF input filter), all ports on vref
  opt2   r1_refbuf5h + per-slice r1_refps5 (switch closed in track, open in conversion): vrefa/vrefla, vrefb/vreflb
  opt3   r1_refbuf5 (sub-reference follower on the same gate): vrefa = vrefb = vref, vrefla = vreflb = vrefl
  opt3b  r1_refbuf5h for the MSB array + a second light r1_refbuf5h (--reflp) for the LSB array
Bandgap model: Vbgi 1.045 V DC + TRNOISE white (NA) + TRNOISE 1/f (alpha 1.15, NAMP), NT 50 ns, from
sim/results/r5/trnoise_cal.json (r1_bgr run bgr-noise-20261021-b: tt27 or ss125 densities; ff uses tt27), Rs
(--bgr R) from the r1_bgr noise roll-off (180-200 kOhm), input filter r1_reffilt5 (MIM w x w).
"""
import argparse
import json
import os
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
ap.add_argument("--core", default="r1_adc5_core_fast")
ap.add_argument("--ref", default="ideal")
ap.add_argument("--refp", default="", help="instance parameters of the main buffer, k=v,k=v")
ap.add_argument("--reflp", default="", help="opt3b: parameters of the LSB buffer; opt2: parameters of r1_refps5")
ap.add_argument("--vref", default="1.045", help="ideal VREF in V, or op:<run id> = v(vrefa) of an op-only run (buffer DC value)")
ap.add_argument("--ibias", default="5u", help="opt3: bias current into the r1_refbuf5 pin nb (r1_bias ib_adc_ref; 5.07 uA tt, 3.5-7.7 uA PVT)")
ap.add_argument("--bgr", default="190k,82u")
ap.add_argument("--noise", default="auto", help="tt | ss | none | auto (ss for mos_ss, else tt)")
ap.add_argument("--gmin", default="default")
ap.add_argument("--rshunt", default="", help="MC deck only (revision-4 setting 1e12): the unit-capacitor MC CDAC has no DC operating point without it")
ap.add_argument("--save", default="codes", help="codes | full | nodes:<vec1>,<vec2>,... (codes plus named vectors)")
ap.add_argument("--mc", type=int, default=0)
ap.add_argument("--seed", type=int, default=1)
ap.add_argument("--mcs", type=int, default=0, help="sampled MIM mismatch: K instances of the nominal fast core with per-capacitor scale "
                "factors drawn here (PDK cap_typ_mismatch statistics: sigma 1 %% / sqrt(unit area in um^2) per unit, units of one "
                "capacitor independent). Used because the unit-capacitor MC core has no DC operating point (runs r5-dbg-opmc-*)")
ap.add_argument("--timing", default="")
ap.add_argument("--op-only", action="store_true")
ap.add_argument("--question", default="")
ap.add_argument("--disposition", default="")
ap.add_argument("--timeout", default="21600")
a = ap.parse_args()
P = json.load(open(a.points))
va, vb = P["a"], P["b"]
vtag = {"1.2": "", "1.08": "_vdd108", "1.32": "_vdd132"}[a.vdd]
PWL_SHIFT = 5e-9
# _cq timing: track falling edge 0.3 ns after the clk30 edge (r1_ctrl flip-flop clock-to-q); sampling instant
# ts = edge + 0.3 ns. Without rshunt / large gmin an edge on the clock grid stops ngspice (run r5-dbg-nz-none).
timing = a.timing or "r1_adc_timing_r5_n0_cq%s.inc" % vtag


def pwl(v):
    pts = []
    for s, x in enumerate(v):
        if s:
            # +5 ns (revision-5 fix, 2026-10-21 04:20): T0 + s F - 550 ns is a clk30 falling edge (e.g. 2.25 us = 67.5 T);
            # input steps on that edge stopped ngspice (runs r5-ref-tt-buf-g15-cq, r5-ref-ss125-buf, r5-dbg-gdef-ea10u).
            # Runs before this change use the edge-aligned steps (pwl_shift_ns 0 in run.json).
            t = T0 + s * F - 550e-9 + PWL_SHIFT
            pts.append("%.6e %.7f" % (t, v[s - 1]))
            pts.append("%.6e %.7f" % (t + 10e-9, x))
        else:
            pts.append("0 %.7f" % x)
    return "\n+ ".join(" ".join(pts[i:i + 8]) for i in range(0, len(pts), 8))


def kv(s):
    return " ".join(x for x in s.split(",") if x)


ties = {"vrefa": "vref", "vrefb": "vref", "vrefla": "vref", "vreflb": "vref"}
PIN = ".subckt r1_refbuf5 vbg vref vrefl nb vdda gnd" in open(os.path.join(BLOCK, "schematic", "r1_adc_r5.spice")).read()
if a.vref.startswith("op:"):
    # T2 2026-10-21: ideal base run at the buffer DC value of an op-only run (revision-4 rule, revision-5 failure 7)
    opf = os.path.join(os.environ["G1_RESULTS_ROOT"], "r1_adc", a.vref[3:], "op.txt")
    a.vref = "%.6f" % float([l.split("=")[1] for l in open(opf) if l.startswith("v(vrefa)")][0])
if a.ref == "ideal":
    lines = ["Vref vref 0 %s" % a.vref]
else:
    cal = json.load(open(os.path.join(BLOCK, "sim", "results", "r5", "trnoise_cal.json")))
    nz = a.noise if a.noise != "auto" else ("ss" if a.corner == "mos_ss" else "tt")
    rs, cw = a.bgr.split(",")
    if nz == "none":
        src = "Vbgi vbgi 0 DC 1.045"
    else:
        c = cal["corners"]["ss125" if nz.startswith("ss") else "tt27"]
        na = 0.0 if nz.endswith("f") else c["NA_V"]          # debug modes: tt_w / ss_w white only, tt_f / ss_f 1/f only
        namp = 0.0 if nz.endswith("w") else c["NAMP_V"]
        # NT 47.3 ns (not a rational multiple of the 33.33 ns tick): NT 50 ns put a noise breakpoint on every
        # third clk30 edge and stopped ngspice at 100 ns (run r5-dbg-nz-w). White NA rescaled for the same density
        # (S = k NA^2 NT); NAMP kept (1/f calibration at NT 50 ns, 5 % step change, recorded)
        nt = 47.3e-9
        src = ("Vbgi vbgw 0 DC 1.045 TRNOISE(%.4g %.4g 0 0)\nVbgf vbgi vbgw DC 0 TRNOISE(0 %.4g %.3g %.4g)"
               % (na * (50e-9 / nt) ** 0.5, nt, nt, cal["alpha"], namp))
    lines = ["Vdda vdda 0 3.3", src, "Rbg vbgi vbg %s" % rs, "XCF vbg 0 r1_reffilt5 w=%s" % cw]
    if a.ref == "buf":
        lines.append("XREF vbg vref vdda 0 r1_refbuf5h %s" % kv(a.refp))
    elif a.ref == "opt3":
        if PIN:   # bias pin nb (netlist after 2026-10-21 T2): external current into the diode XMB0
            lines += ["Ibref vdda nbr %s" % a.ibias, "XREF vbg vref vrefl nbr vdda 0 r1_refbuf5 %s" % kv(a.refp)]
        else:
            if a.ibias != "5u":
                sys.exit("--ibias needs the r1_refbuf5 bias pin (regenerate schematic/r1_adc_r5.spice)")
            lines.append("XREF vbg vref vrefl vdda 0 r1_refbuf5 %s" % kv(a.refp))
        ties.update(vrefla="vrefl", vreflb="vrefl")
    elif a.ref == "opt3b":
        lines.append("XREF vbg vref vdda 0 r1_refbuf5h %s" % kv(a.refp))
        lines.append("XREFL vbg vrefl vdda 0 r1_refbuf5h %s" % kv(a.reflp))
        ties.update(vrefla="vrefl", vreflb="vrefl")
    elif a.ref == "opt2":
        lines.append("XREF vbg vref vdda 0 r1_refbuf5h %s" % kv(a.refp))
        lines.append("XPSA vref vrefa trka0 trka1 vdd 0 r1_refps5 %s" % kv(a.reflp))
        lines.append("XPSB vref vrefb trkb0 trkb1 vdd 0 r1_refps5 %s" % kv(a.reflp))
        ties = {"vrefla": "vrefa", "vreflb": "vrefb"}
    else:
        sys.exit("unknown --ref %s" % a.ref)
for n, m in ties.items():
    lines.append("Vt%s %s %s 0" % (n, n, m))
reflines = "\n".join(lines)

STB = " ".join("stba%d" % k for k in range(14)) + "\n+ " + " ".join("stbb%d" % k for k in range(14))
MCS = None
if a.mcs:
    import numpy as np
    lib = open(os.path.join(BLOCK, "schematic", "r1_adc_r5.spice")).read().splitlines()

    def block(name):
        i0 = next(i for i, l in enumerate(lib) if l.startswith(".subckt %s " % name))
        i1 = next(i for i in range(i0, len(lib)) if lib[i].startswith(".ends"))
        return lib[i0:i1 + 1]
    cdac, th, core = block("r1_cdac3_side"), block("r1_th4_fast"), block("r1_adc5_core_fast")
    rng = np.random.RandomState(a.seed)
    MCS = {}
    sub = []
    for i in range(a.mcs):
        for sl in "ab":
            for sd in "pn":
                nm = "r1_cdac5s_%d%s%s" % (i, sl, sd)
                sc = {}
                body = [".subckt %s top lsb b12 b11 b10 b9 b8 b7 b6 b5 b4 b3 b2 b1 b0" % nm]
                for l in cdac[1:-1]:
                    f = l.split()
                    w = float(f[4][2:-1])
                    m = int(f[6][2:]) if len(f) > 6 else 1
                    k = 1.0 + 0.01 / w / np.sqrt(m) * rng.randn()      # sigma 1 % / sqrt(w l / um^2) per unit, m units
                    sc[f[0]] = round(float(k), 6)
                    ws = "%.5fu" % (w * np.sqrt(k))
                    f[4], f[5] = "w=" + ws, "l=" + ws
                    body.append(" ".join(f))
                body.append(".ends %s" % nm)
                sub += body
                MCS["m%d%s%s" % (i, sl, sd)] = sc
            t = [l.replace("r1_th4_fast", "r1_th5s_%d%s" % (i, sl)) for l in th]
            t = [l.replace("r1_cdac3_side", "r1_cdac5s_%d%s%s" % (i, sl, "p" if l.startswith("XDACP") else "n")) if l.startswith("XDAC") else l for l in t]
            sub += t
        c = [l.replace("r1_adc5_core_fast", "r1_core5s_%d" % i) for l in core]
        c = [l.replace("r1_th4_fast", "r1_th5s_%da" % i) if l.startswith("XTHA") else
             (l.replace("r1_th4_fast", "r1_th5s_%db" % i) if l.startswith("XTHB") else l) for l in c]
        sub += c
    inst = ["XM%d sinp sinn cosp cosn isap isan isap isan trka0 trka1 trkb0 trkb1 clk30 wina winb lata latb\n+ %s\n"
            "+ m%drawa m%drawb m%dtpa m%dtna m%dtpb m%dtnb vdd vrefa vrefb vrefla vreflb 0 r1_core5s_%d"
            % (i, STB, i, i, i, i, i, i, i) for i in range(a.mcs)]
    instances = "\n".join(sub + inst)
    save = " ".join("v(m%drawa) v(m%drawb)" % (i, i) for i in range(a.mcs))
    caplib = "cap_typ"
    a.mc = a.mcs
elif a.mc:
    inst = ["XM%d sinp sinn cosp cosn isap isan isap isan trka0 trka1 trkb0 trkb1 clk30 wina winb lata latb\n+ %s\n"
            "+ m%drawa m%drawb m%dtpa m%dtna m%dtpb m%dtnb vdd vrefa vrefb vrefla vreflb 0 r1_adc5_core_fast_mc"
            % (i, STB, i, i, i, i, i, i) for i in range(a.mc)]
    instances = "\n".join(inst)
    save = " ".join("v(m%drawa) v(m%drawb)" % (i, i) for i in range(a.mc))
    caplib = "cap_typ_mismatch"
else:
    instances = ("XADC sinp sinn cosp cosn isap isan isap isan trka0 trka1 trkb0 trkb1 clk30 wina winb lata latb\n+ %s\n"
                 "+ rawa rawb topap topan topbp topbn vdd vrefa vrefb vrefla vreflb 0 %s" % (STB, a.core))
    save = ("v(rawa) v(rawb)" if a.save == "codes" else
            # T2 2026-10-21: "nodes:n1,n2,..." saves rawa/rawb plus the named vectors (first-frame instrumentation)
            "v(rawa) v(rawb) " + " ".join(a.save[6:].split(",")) if a.save.startswith("nodes:") else
            "v(rawa) v(rawb) v(vrefa) v(vrefb) v(vrefla) v(vreflb) v(topap) v(topan) v(topbp) v(topbn) i(vdd) v(clk30) "
            "v(trka0) v(trkb0)")
    caplib = "cap_typ"
if a.ref != "ideal":
    save += " i(vdda) v(vbg)"
opts = "reltol=1e-4 vntol=1e-6 abstol=1e-12 method=trap klu seed=%d" % a.seed
if a.gmin != "default":
    opts += " gmin=%s" % a.gmin
if a.rshunt:
    opts += " rshunt=%s" % a.rshunt
if a.save == "codes":
    opts += " interp"
tstop = "%.4fu" % ((T0 + (len(va) - 1) * F + 14 * T + 60e-9) * 1e6)
if a.op_only:
    probe = "v(vrefa) v(vrefb) v(vrefla) v(vreflb) v(topap) v(topan) v(xadc.xtha.lsb_p) v(xadc.xtha.lsb_n)"
    if a.ref != "ideal":
        probe += " v(vbg) v(xref.ng) i(vdda)"
    analysis = "op\nprint %s > @RAW@/op.txt" % probe
    save = "all"
    expect = "op.txt"
else:
    analysis = "tran 1n %s 0 %s\nwrite @RAW@/codes.raw" % (tstop, "0.2n")
    expect = "codes.raw"
cmd = ["python3", "sim/r5/run_ngspice5.py", "--deck", "sim/r5/tb_adc5_points.cir", "--run-id", a.id, "--cpuset", a.cpu,
       "--sub", "CORNER=" + a.corner, "--sub", "TEMP=" + a.temp, "--sub", "VDD=" + a.vdd, "--sub", "CM=" + a.cm,
       "--sub", "CAPLIB=" + caplib, "--sub", "TIMING=" + timing, "--sub", "OPTS=" + opts, "--sub", "TSTOP=" + tstop,
       "--sub", "PWLA=" + pwl(va), "--sub", "PWLB=" + pwl(vb), "--sub", "REFLINES=" + reflines,
       "--sub", "INSTANCES=" + instances, "--sub", "SAVE=" + save, "--sub", "ANALYSIS=" + analysis,
       "--timeout", a.timeout, "--expect", expect, "--question", a.question, "--disposition", a.disposition]
rc = subprocess.call(cmd, cwd=BLOCK)
rj = os.path.join(BLOCK, "sim", "runs", a.id, "run.json")
stopped = None
if not os.path.exists(rj):
    stopped = "run_ngspice5.py wrote no run.json"
else:
    d = json.load(open(rj))
    d.update({"points_file": os.path.relpath(os.path.abspath(a.points), BLOCK), "first_slot": 0, "n_stag": 0,
              "runner": "sim/r5/run_points5.py", "ref_model": a.ref, "ref_params": a.refp, "refl_params": a.reflp,
              "bgr_model": a.bgr if a.ref != "ideal" else None, "ref_ibias": a.ibias if a.ref == "opt3" else None, "refbuf5_bias_pin": PIN, "vref_ideal": a.vref if a.ref == "ideal" else None, "pwl_shift_ns": PWL_SHIFT * 1e9, "gmin": a.gmin, "rshunt": a.rshunt or None, "mc": a.mc, "seed": a.seed, "mc_mode": "sampled (--mcs)" if MCS else ("pdk agauss" if a.mc else None), "mcs_scales": MCS})
    if d["status"] != "completed":
        stopped = "%s %s: %s" % (a.id, d["status"], "; ".join((d.get("failure_lines") or d.get("errors") or [])[:3]))
    json.dump(d, open(rj, "w"), indent=2)
segs = [] if stopped else [{"run_id": a.id, "first_slot": 0, "slots": len(va)}]
json.dump({"id": a.id, "points": os.path.relpath(os.path.abspath(a.points), BLOCK), "n_stag": 0, "mc": a.mc,
           "seed": a.seed if a.mc else None, "segments": segs, "slots_total": len(va), "stopped": stopped,
           "op_only": a.op_only}, open(os.path.join(BLOCK, "sim", "results", "r5", a.id + "_segments.json"), "w"), indent=1)
print("segments:", segs, "stopped:", stopped)
sys.exit(1 if (stopped or rc) else 0)

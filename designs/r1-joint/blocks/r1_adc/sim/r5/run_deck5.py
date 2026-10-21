#!/usr/bin/env python3
"""T2 2026-10-21: run one revision-5 deck that is not a held-input points deck (dynamic, mux sequence, reference
noise) through sim/r5/run_ngspice5.py (same run.json, frozen-netlist check, non-zero exit on any failure; no resume,
no resubmission). The reference lines are built as in sim/r5/run_points5.py (copied, not imported: run_points5.py
parses its arguments at import).

usage: run_deck5.py --id <run id> --cpu N --deck sim/r5/tb_x.cir [--corner mos_tt --temp 27 --vdd 1.2 --cm 0.6
       --ref ideal|opt3 --refp "ndec=4,ndecl=2" --vref 1.045 --bgr 190k,82u --noise auto|tt|ss|none --timing <inc>
       --tstop 3.31u --tmax 0.2n --sub K=V ... --expect codes.raw --question ... --disposition ...]
"""
import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BLOCK = os.path.dirname(os.path.dirname(HERE))
ap = argparse.ArgumentParser()
for k, d in (("--id", None), ("--cpu", None), ("--deck", None), ("--corner", "mos_tt"), ("--temp", "27"), ("--vdd", "1.2"),
             ("--cm", "0.6"), ("--ref", "ideal"), ("--refp", ""), ("--vref", "1.045"), ("--ibias", "5u"), ("--bgr", "190k,82u"),
             ("--noise", "auto"), ("--timing", ""), ("--tstop", "3.31u"), ("--tmax", "0.2n"), ("--question", ""),
             ("--disposition", ""), ("--timeout", "36000"), ("--seed", "1")):
    ap.add_argument(k, required=d is None, default=d)
ap.add_argument("--sub", action="append", default=[])
ap.add_argument("--expect", action="append", default=[])
ap.add_argument("--interp", action="store_true")
a = ap.parse_args()
vtag = {"1.2": "", "1.08": "_vdd108", "1.32": "_vdd132"}[a.vdd]
ties = {"vrefa": "vref", "vrefb": "vref", "vrefla": "vref", "vreflb": "vref"}
kv = lambda s: " ".join(x for x in s.split(",") if x)
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
        nt = 47.3e-9
        src = ("Vbgi vbgw 0 DC 1.045 TRNOISE(%.4g %.4g 0 0)\nVbgf vbgi vbgw DC 0 TRNOISE(0 %.4g %.3g %.4g)"
               % (c["NA_V"] * (50e-9 / nt) ** 0.5, nt, nt, cal["alpha"], c["NAMP_V"]))
    lines = ["Vdda vdda 0 3.3", src, "Rbg vbgi vbg %s" % rs, "XCF vbg 0 r1_reffilt5 w=%s" % cw]
    if a.ref == "opt3":
        if PIN:   # bias pin nb (netlist after 2026-10-21 T2): external current into the diode XMB0
            lines += ["Ibref vdda nbr %s" % a.ibias, "XREF vbg vref vrefl nbr vdda 0 r1_refbuf5 %s" % kv(a.refp)]
        else:
            if a.ibias != "5u":
                sys.exit("--ibias needs the r1_refbuf5 bias pin (regenerate schematic/r1_adc_r5.spice)")
            lines.append("XREF vbg vref vrefl vdda 0 r1_refbuf5 %s" % kv(a.refp))
        ties.update(vrefla="vrefl", vreflb="vrefl")
    else:
        sys.exit("unknown --ref %s" % a.ref)
for n, m in ties.items():
    lines.append("Vt%s %s %s 0" % (n, n, m))
opts = "reltol=1e-4 vntol=1e-6 abstol=1e-12 method=trap klu seed=%s%s" % (a.seed, " interp" if a.interp else "")
cmd = ["python3", "sim/r5/run_ngspice5.py", "--deck", a.deck, "--run-id", a.id, "--cpuset", a.cpu,
       "--sub", "CORNER=" + a.corner, "--sub", "TEMP=" + a.temp, "--sub", "VDD=" + a.vdd, "--sub", "CM=" + a.cm,
       "--sub", "TIMING=" + (a.timing or "r1_adc_timing_r5_n0_cq%s.inc" % vtag), "--sub", "OPTS=" + opts,
       "--sub", "TSTOP=" + a.tstop, "--sub", "TMAX=" + a.tmax, "--sub", "REFLINES=" + "\n".join(lines),
       "--timeout", a.timeout, "--question", a.question, "--disposition", a.disposition]
for s in a.sub:
    cmd += ["--sub", s]
for e in (a.expect or ["codes.raw"]):
    cmd += ["--expect", e]
rc = subprocess.call(cmd, cwd=BLOCK)
rj = os.path.join(BLOCK, "sim", "runs", a.id, "run.json")
if os.path.exists(rj):
    d = json.load(open(rj))
    d.update({"runner": "sim/r5/run_deck5.py", "ref_model": a.ref, "ref_params": a.refp,
              "bgr_model": a.bgr if a.ref != "ideal" else None, "noise": a.noise if a.ref != "ideal" else None,
              "ref_ibias": a.ibias if a.ref == "opt3" else None, "refbuf5_bias_pin": PIN})
    json.dump(d, open(rj, "w"), indent=2)
sys.exit(rc)

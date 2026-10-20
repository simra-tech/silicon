#!/usr/bin/env python3
"""r1_gate: one simulation case with the PDK sg13g2_IOPadOut30mA pad model, then analysis.
Host python 3.6. Run from the repository root, for example:
  G1_CPUSET=119 G1_CPUS=1 G1_RESULTS_ROOT=<G1_RESULTS_ROOT> \
    python3 designs/r1-joint/blocks/r1_gate/sim/run_gate.py --topo hv --corner tt --load 5n --pkg 0 --tag g20261020a
Deck and raw waveform go to <G1_RESULTS_ROOT>/r1_gate/<tag>/<case>/ . The summary goes to sim/runs/<tag>/<case>/run.json .
"""
import argparse, json, os, re, subprocess, sys, hashlib, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
BLK = os.path.relpath(HERE, os.getcwd())
CORNERS = {"tt": ("mos_tt", 27, 3.3, 1.2), "ss": ("mos_ss", 125, 3.0, 1.08), "ff": ("mos_ff", -40, 3.6, 1.32)}
EDGE = 2e-9   # stimulus edge time, as in the G1 gate deck (needed for convergence with the pad model)

ap = argparse.ArgumentParser()
ap.add_argument("--topo", choices=["hv", "lv"], required=True)
ap.add_argument("--corner", choices=list(CORNERS), required=True)
ap.add_argument("--load", default="5n")        # gate load capacitance, e.g. 5n, 1n, 1p
ap.add_argument("--pkg", type=int, default=0)  # 1: package model 1 nH + 0.1 ohm per supply pin, 1 IOVDD pin, 2 IOVSS pins
ap.add_argument("--cdec", default="1n")        # on-chip IOVDD-IOVSS decoupling (pkg 1) or IOVDD-gnd (pkg 0)
ap.add_argument("--seg", type=float, default=4.0)   # segment length in us
ap.add_argument("--rg", default="10")
ap.add_argument("--nodcn", type=int, default=0)
ap.add_argument("--tag", required=True)
ap.add_argument("--step", default="1n")
ap.add_argument("--timeout", type=int, default=5400)
a = ap.parse_args()

mos, temp, iovdd, vdd = CORNERS[a.corner]
case = "%s_%s_%s_pkg%d%s%s" % (a.topo, a.corner, a.load, a.pkg, ("_cd" + a.cdec) if a.pkg else "", "_nodcn" if a.nodcn else "")
root = os.environ["G1_RESULTS_ROOT"]
odir = os.path.join(root, "r1_gate", a.tag, case)
os.makedirs(odir, exist_ok=True)
rdir = os.path.join(HERE, "runs", a.tag, case)
os.makedirs(rdir, exist_ok=True)
S = a.seg * 1e-6

def pwl(init, toggles, hi):
    pts = [(0.0, init * hi)]
    lvl = init
    for t in sorted(toggles):
        pts.append((t, lvl * hi)); lvl = 1 - lvl; pts.append((t + EDGE, lvl * hi))
    return " ".join("%.6gn %.4g" % (t * 1e9, v) for t, v in pts)

T = {"en": [0.2e-6, 9 * S],
     "a": [S, 2 * S, 6 * S, 7 * S, 8 * S],
     "b": [S - 50e-9, 2 * S + 50e-9, 3 * S, 6 * S, 7 * S, 8 * S],
     "c": [S, 2 * S, 4 * S, 5 * S, 6 * S, 7 * S, 8 * S]}
INIT = {"en": 0, "a": 0, "b": 1, "c": 0}
tstop = 10 * S

pad_spi = "/foss/pdks/ihp-sg13g2/libs.ref/sg13g2_io/spice/sg13g2_io.spi"
if a.nodcn:
    # deck-local copy of the PDK pad file without dantenna devices; made once inside the container by make_nodcn.sh
    pad_spi = os.path.join(root, "r1_gate", "sg13g2_io_nodcn.spi")   # made once by make_nodcn.sh inside the container

L = []
L.append("* r1_gate %s: topology %s, corner %s (%s, %s C, IOVDD %s, VDD %s), load %s + %s ohm, pkg %d" % (case, a.topo, a.corner, mos, temp, iovdd, vdd, a.load, a.rg, a.pkg))
L.append(".param IOVDD=%s VDD=%s" % (iovdd, vdd))
for lib, c in (("cornerMOSlv.lib", mos), ("cornerMOShv.lib", mos), ("cornerRES.lib", "res_typ"), ("cornerCAP.lib", "cap_typ"), ("cornerDIO.lib", "dio_tt")):
    L.append(".lib /foss/pdks/ihp-sg13g2/libs.tech/ngspice/models/%s %s" % (lib, c))
L.append(".include %s" % pad_spi)
L.append(".include ../schematic/r1_gate.spice")
L.append(".temp %s" % temp)
L.append(".global sub!")
L.append("Vsub sub! 0 dc 0")
L.append("* solver settings as in the G1 gate deck: gear, series R in the supplies, local decoupling")
L.append(".option method=gear reltol=0.005 itl4=100 abstol=1e-9 vntol=1e-5 chgtol=1e-13")
L.append("Viov iov_b 0 dc {IOVDD}")
L.append("Vcore vdd_b 0 dc {VDD}")
L.append("Rsd vdd_b vdd_i 0.5")
L.append("Cdd vdd_i 0 1n")
if a.pkg:
    L.append("* package: IOVDD 1 pin (1 nH + 0.1 ohm); IOVSS 2 pins in parallel (0.5 nH + 0.05 ohm); on-chip decoupling IOVDD-IOVSS")
    L.append("Lpd iov_b iov_m 1n")
    L.append("Rpd iov_m iovdd_i 0.1")
    L.append("Cda iovdd_i iovss_i %s" % a.cdec)
    L.append("Lps iovss_i ss_m 0.5n")
    L.append("Rps ss_m ss_n 0.05")
    L.append("Viss ss_n 0 dc 0")
else:
    L.append("Rsa iov_b iovdd_i 0.5")
    L.append("Cda iovdd_i 0 %s" % a.cdec)
    L.append("Viss iovss_i 0 dc 0")
L.append("Ven gate_en 0 pwl(%s)" % pwl(INIT["en"], T["en"], vdd))
for x in "abc":
    L.append("Vp%s pwm_%s 0 pwl(%s)" % (x, x, pwl(INIT[x], T[x], vdd)))
L.append("XG pwm_a pwm_b pwm_c gate_en gc_a gc_b gc_c vdd_i iovdd_i 0 r1_gate_%s" % a.topo)
for x in "abc":
    L.append("XP%s pad_%s gc_%s vdd_i 0 iovdd_i iovss_i sg13g2_IOPadOut30mA" % (x, x, x))
    L.append("Rg%s pad_%s gf_%s %s" % (x, x, x, a.rg))
    L.append("CL%s gf_%s 0 %s" % (x, x, a.load))
L.append(".control")
L.append("set filetype=ascii")
L.append("set wr_singlescale")
L.append("set wr_vecnames")
L.append("option numdgt=7")
L.append("tran %s %.6gn" % (a.step, tstop * 1e9))
L.append("let iiov = -i(Viov)")
L.append("let icore = -i(Vcore)")
L.append("let iiss = i(Viss)")
L.append("wrdata %s/wave.dat v(pwm_a) v(pwm_b) v(pwm_c) v(gate_en) v(gc_a) v(gc_b) v(gc_c) v(pad_a) v(pad_b) v(pad_c) v(gf_a) v(gf_b) v(gf_c) iiov iiss icore v(iovdd_i) v(iovss_i) v(vdd_i)" % odir)
L.append("echo CASE_DONE")
L.append(".endc")
L.append(".end")
deck_txt = "\n".join(L) + "\n"
open(os.path.join(odir, "deck.cir"), "w").write(deck_txt)
local = os.path.join(HERE, "_deck_%s_%s.cir" % (a.tag, case))
open(local, "w").write(deck_txt)

env = dict(os.environ, G1_WORKDIR=BLK)
cmd = ["flow/run.sh", "ngspice", "-b", os.path.basename(local)]
t0 = datetime.datetime.utcnow()
try:
    p = subprocess.run(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, timeout=a.timeout)
    out, rc = p.stdout, p.returncode
except subprocess.TimeoutExpired as e:
    out, rc = (e.stdout or "") + "\nTIMEOUT", -9
t1 = datetime.datetime.utcnow()
os.remove(local)
open(os.path.join(odir, "ngspice.log"), "w").write(out)
done = ("CASE_DONE" in out) and ("aborted" not in out) and ("Timestep too small" not in out)

summary = {"case": case, "tag": a.tag, "topology": a.topo, "corner": a.corner, "mos_corner": mos, "temp_C": temp, "iovdd_V": iovdd,
           "vdd_V": vdd, "load_F": a.load, "rg_ohm": a.rg, "pkg": a.pkg, "cdec": a.cdec, "seg_us": a.seg, "nodcn": a.nodcn,
           "wall_s": (t1 - t0).total_seconds(), "ngspice_rc": rc, "completed": done}
if not done:
    tail = [l for l in out.splitlines() if l.strip()][-6:]
    summary["error_tail"] = tail
    m = re.search(r"Timestep too small; time = (\S+), timestep = (\S+): trouble with node \"([^\"]+)\"", out)
    if m:
        summary["stall"] = {"time_s": float(m.group(1)), "node": m.group(3)}
    summary["result"] = "failed to complete (solver stall)" if m else "failed to complete"
else:
    import analyze_gate
    try:
        summary["metrics"] = analyze_gate.analyze(os.path.join(odir, "wave.dat"), iovdd, vdd, S, EDGE)
        summary["result"] = "completed"
    except Exception as ex:
        summary["result"] = "analysis failed: %r" % (ex,)
json.dump(summary, open(os.path.join(rdir, "metrics.json"), "w"), indent=1, sort_keys=True)
print(case, summary["result"], "%.0f s" % summary["wall_s"])

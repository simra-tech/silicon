#!/usr/bin/env python3
"""r1_ls: delay, duty distortion, skew and static current of g1_ls_up, g1_lvlup, g1_lvldn.
Run from the repository root (host python 3.6, ngspice through flow/run.sh):
  G1_CPUSET=119 G1_CPUS=1 G1_RESULTS_ROOT=<G1_RESULTS_ROOT> python3 designs/r1-joint/blocks/r1_ls/sim/run_ls.py <run-id>
Decks and logs go to <G1_RESULTS_ROOT>/r1_ls/<run-id>/. The summary goes to results/<run-id>.json.
"""
import json, os, re, subprocess, sys, hashlib, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
BLK = os.path.relpath(HERE, os.getcwd())
ROOT = os.environ["G1_RESULTS_ROOT"]
RUN = sys.argv[1]
OUT = os.path.join(ROOT, "r1_ls", RUN)
os.makedirs(OUT, exist_ok=True)
CORNERS = [("tt_27C_3p3_1p2", "mos_tt", 27, 3.3, 1.2),
           ("ss_125C_3p0_1p08", "mos_ss", 125, 3.0, 1.08),
           ("ff_m40C_3p6_1p32", "mos_ff", -40, 3.6, 1.32),
           # extra stress point (not one of the three required corners): slow core drive against the strongest 3.3 V keeper
           ("ss_m40C_3p6_1p08_stress", "mos_ss", -40, 3.6, 1.08)]
CELLS = ["g1_ls_up", "g1_lvlup", "g1_lvldn"]
INC = {"g1_ls_up": "../schematic/g1_ls_up_copy.spice",
       "g1_lvlup": "../schematic/g1_lvlup_copy.spice",
       "g1_lvldn": "../schematic/g1_lvldn_copy.spice"}

def pwl(lo, hi, edges, tr=1e-9):
    """edges: list of (t_rise, t_fall) in s; returns pwl text for a signal low=lo, high=hi."""
    pts = [(0.0, lo)]
    for a, b in edges:
        pts += [(a, lo), (a + tr, hi), (b, hi), (b + tr, lo)]
    return " ".join("%.4gn %.4g" % (t * 1e9, v) for t, v in pts)

def build(cell, mos, temp, vdda, vdd, tag):
    per, hi = 100e-9 / 3.0, 50e-9 / 3.0
    edges = [(50e-9, 150e-9)] + [(300e-9 + k * per, 300e-9 + k * per + hi) for k in range(6)]
    tstop = 300e-9 + 7 * per
    lvdn = (cell == "g1_lvldn")
    s = ["* r1_ls %s %s %s C vdda=%s vdd=%s" % (cell, mos, temp, vdda, vdd),
         ".param VDDA=%s VDD=%s" % (vdda, vdd),
         ".lib /foss/pdks/ihp-sg13g2/libs.tech/ngspice/models/cornerMOSlv.lib %s" % mos,
         ".lib /foss/pdks/ihp-sg13g2/libs.tech/ngspice/models/cornerMOShv.lib %s" % mos,
         ".include %s" % INC[cell]]
    if cell != "g1_lvlup":
        s.append(".include ../schematic/g1_lvlup_copy.spice")   # g1_lv_inv, g1_hv_inv
    s += [".temp %s" % temp, ".option reltol=0.001 abstol=1e-12 vntol=1e-6 chgtol=1e-14",
          "Vdda vdda 0 dc {VDDA}", "Vdd vdd 0 dc {VDD}"]
    if not lvdn:
        s += ["Vin in 0 dc 0 pwl(%s)" % pwl(0, vdd, edges), "X1 in out vdd vdda 0 %s" % cell,
              "XL out lo vdda 0 g1_hv_inv", "Cl out 0 20f"]          # 20 fF + one HV inverter
        thin, thout = vdd / 2.0, vdda / 2.0
    else:
        s += ["Vin in 0 dc 0 pwl(%s)" % pwl(0, vdda, edges), "Vinb inb 0 dc %s pwl(%s)" % (vdda, pwl(vdda, 0, edges)),
              "X1 in inb out vdd 0 g1_lvldn", "XL out lo vdd 0 g1_lv_inv", "Cl out 0 20f"]   # 20 fF + one LV inverter
        thin, thout = vdda / 2.0, vdd / 2.0
    s.append(".control")
    s.append("set filetype=ascii")
    for state, (a, ab) in (("0", (0, vdda)), ("1", (vdda, 0))) if lvdn else (("0", (0, 0)), ("1", (vdd, 0))):
        if lvdn:
            s.append("alter Vin dc=%s" % a); s.append("alter Vinb dc=%s" % ab)
        else:
            s.append("alter Vin dc=%s" % a)
        s.append("op")
        s.append("let ia = -i(vdda)"); s.append("let ic = -i(vdd)")
        s.append("echo STATIC in=%s ivdda_A= $&ia ivdd_A= $&ic vout= $&v(out)" % state)
    s.append("alter Vin dc=0")
    if lvdn:
        s.append("alter Vinb dc=%s" % vdda)
    s.append("tran 10p %.4gn" % (tstop * 1e9 + 20))
    t1, t0 = "%.4g" % thin, "%.4g" % thout
    s.append("meas tran tr trig v(in) val=%s rise=1 targ v(out) val=%s rise=1" % (t1, t0))
    s.append("meas tran tf trig v(in) val=%s fall=1 targ v(out) val=%s fall=1" % (t1, t0))
    s.append("meas tran tr10 trig v(out) val=%.4g rise=1 targ v(out) val=%.4g rise=1" % (0.1 * (vdd if lvdn else vdda), 0.9 * (vdd if lvdn else vdda)))
    s.append("meas tran tf10 trig v(out) val=%.4g fall=1 targ v(out) val=%.4g fall=1" % (0.9 * (vdd if lvdn else vdda), 0.1 * (vdd if lvdn else vdda)))
    s.append("meas tran hin trig v(in) val=%s rise=4 targ v(in) val=%s fall=4" % (t1, t1))
    s.append("meas tran hout trig v(out) val=%s rise=4 targ v(out) val=%s fall=4" % (t0, t0))
    s.append("meas tran pin trig v(in) val=%s rise=4 targ v(in) val=%s rise=5" % (t1, t1))
    s.append("meas tran pout trig v(out) val=%s rise=4 targ v(out) val=%s rise=5" % (t0, t0))
    top = vdd if lvdn else vdda
    s.append("meas tran vhi find v(out) at=140n")
    s.append("meas tran vlo find v(out) at=290n")
    s.append("let ia = -i(vdda)")
    s.append("meas tran iapk max ia from=49n to=60n")
    s.append("meas tran iapkf max ia from=149n to=160n")
    s.append("let ic = -i(vdd)")
    s.append("meas tran icpk max ic from=49n to=60n")
    s.append('echo RES tr_ps= $&{tr*1e12} tf_ps= $&{tf*1e12} tr1090_ps= $&{tr10*1e12} tf9010_ps= $&{tf10*1e12} hin_ns= $&{hin*1e9} hout_ns= $&{hout*1e9} pin_ns= $&{pin*1e9} pout_ns= $&{pout*1e9} vhi= $&vhi vlo= $&vlo iapk_uA= $&{iapk*1e6} iapkf_uA= $&{iapkf*1e6} icpk_uA= $&{icpk*1e6}')
    s.append(".endc")
    s.append(".end")
    return "\n".join(s) + "\n"

def num(line, key):
    m = re.search(key + r"=\s*(\S+)", line)
    return float(m.group(1)) if m else None

res = {}
for cell in CELLS:
    for cname, mos, temp, vdda, vdd in CORNERS:
        tag = "%s_%s" % (cell, cname)
        deckp = os.path.join(OUT, tag + ".cir")
        # ngspice echo cannot evaluate expressions: write one "let" per expression first
        exprs = {}
        raw = build(cell, mos, temp, vdda, vdd, tag)
        for m in re.finditer(r"\$&\{([^}]*)\}", raw):
            exprs[m.group(1)] = "x%d" % len(exprs)
        out = []
        for line in raw.splitlines():
            if line.startswith("echo RES"):
                for e, v in exprs.items():
                    out.append("let %s = %s" % (v, e))
                for e, v in exprs.items():
                    line = line.replace("$&{%s}" % e, "$&%s" % v)
            out.append(line)
        open(deckp, "w").write("\n".join(out) + "\n")
        # run from the block sim dir so that relative includes resolve; copy deck beside the netlists
        local = os.path.join(HERE, "_deck_%s.cir" % tag)
        open(local, "w").write("\n".join(out) + "\n")
        env = dict(os.environ, G1_WORKDIR=os.path.join(BLK))
        cmd = ["flow/run.sh", "ngspice", "-b", os.path.basename(local)]
        p = subprocess.run(cmd, cwd=os.getcwd(), env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
        open(os.path.join(OUT, tag + ".log"), "w").write(p.stdout)
        os.remove(local)
        r = {"corner": cname, "mos": mos, "temp_C": temp, "vdda": vdda, "vdd": vdd}
        for line in p.stdout.splitlines():
            if line.startswith("STATIC"):
                st = num(line, "in")
                r.setdefault("static", {})[line.split()[1]] = {"ivdda_A": num(line, "ivdda_A"), "ivdd_A": num(line, "ivdd_A"), "vout": num(line, "vout")}
            if line.startswith("RES"):
                for k in ["tr_ps", "tf_ps", "tr1090_ps", "tf9010_ps", "hin_ns", "hout_ns", "pin_ns", "pout_ns", "vhi", "vlo", "iapk_uA", "iapkf_uA", "icpk_uA"]:
                    r[k] = num(line, k)
        if "tr_ps" not in r:
            r["error"] = "no RES line; see log"
        res["%s/%s" % (cell, cname)] = r
        print(tag, json.dumps(r), flush=True)

json.dump(res, open(os.path.join(HERE, "results", RUN + ".json"), "w"), indent=1, sort_keys=True)

#!/usr/bin/env python3
"""Post-layout re-run of the G1_BGR block testbench on the kpex-extracted netlist.

Same template and control blocks as the schematic runs (../tb_g1_bgr.spice.tmpl, ../ctl_*.txt), with the
.include of xschem/g1_bgr.spice replaced by g1_bgr_pex.spice (made by make_pex_netlist.py). Decks, logs and
result files land in decks/, logs/, results/ next to this script; compare.py builds the table against the
schematic results in ../results.

Run inside the pinned container from the repository root:
  G1_WORKDIR=designs/g1-guardian/blocks/g1_bgr/sim/postlayout flow/run.sh python3 run_postlayout.py <suite> [-j N]
suites: op temp startup psrr psrr_var wire all

psrr_var is a sensitivity check on the extracted capacitances (27 C, nominal corner): variant A moves the
capacitances that kpex reports between the substrate and the nets living over the mirror n-well (pbias,
pcasc, d1..d5, det) from vss to vdd, where the n-well (tied to vdd) actually sits under those shapes; the
2.5D engine has no well conductor. Variant B removes every parasitic capacitor and leaves only the
extracted device geometry. Netlists are written to variants/.

wire is a hand-counted wiring-resistance variant (C), because the kpex RC extraction is not usable (see
make_pex_netlist.py): series resistors from the PDK LEF values (Metal2/Metal3 0.103 Ohm/sq, Via1/Via2
20 Ohm per cut, so 10 Ohm per 2-cut pair) on the DC current path of the layout are inserted into the
capacitance netlist: R1 top to the Q2 emitters 60 Ohm (four via pairs, 3.7 um BA track, 21 um column,
about 30 um of CB track), R1 bottom to the HBT ring 41 Ohm (two via pairs, 62 um of 0.3 um Metal2),
R2 top to MC3 60 Ohm of vias plus 21 Ohm of track (81), R2 bottom to Q3 48 Ohm, and 15 Ohm between the
HBT ring (emitters of Q1, Q1B, Q3, QD2) and the vss pin (four ring straps in parallel plus ring Metal1).
Numbers are estimates from geometry, not an extraction; the deck runs op and the nominal temperature
sweep.
"""
import argparse, os, re, subprocess
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
SIM = os.path.dirname(HERE)
DECKS, LOGS, RES = (os.path.join(HERE, d) for d in ("decks", "logs", "results"))
TMPL = open(os.path.join(SIM, "tb_g1_bgr.spice.tmpl")).read()
assert ".include ../../xschem/g1_bgr.spice" in TMPL
TMPL = TMPL.replace(".include ../../xschem/g1_bgr.spice", ".include ../g1_bgr_pex.spice")
TMPL = TMPL.replace("* G1_BGR testbench", "* G1_BGR POST-LAYOUT (kpex RC) testbench")


def ctl(name):
    return open(os.path.join(SIM, f"ctl_{name}.txt")).read()


def deck(name, kind, hbt, mos, res, vdd, control, r4="0", vddac="", **subs):
    text = TMPL.replace("@@KIND@@", kind).replace("@@HBT@@", hbt).replace("@@MOS@@", mos)
    text = text.replace("@@RES@@", res).replace("@@VDD@@", vdd).replace("@@R4@@", r4).replace("@@VDDAC@@", vddac)
    control = control.replace("@@OUT@@", os.path.join("..", "results", name)).replace("@@VDD@@", vdd)
    for k, v in subs.items():
        control = control.replace(f"@@{k}@@", str(v))
    text = text.replace("@@CONTROL@@", control)
    path = os.path.join(DECKS, name + ".cir")
    with open(path, "w") as f:
        f.write(text)
    return path


WELL_NETS = {'pbias', 'pcasc', 'd1', 'd2', 'd3', 'd4', 'd5', 'det'}


def variants():
    """write variants/pex_wellcaps_to_vdd.spice (A) and variants/pex_nocaps.spice (B) from g1_bgr_pex.spice"""
    vdir = os.path.join(HERE, "variants")
    os.makedirs(vdir, exist_ok=True)
    net = open(os.path.join(HERE, "g1_bgr_pex.spice")).read().split("\n")
    va, moved = [], 0
    for line in net:
        t = line.split()
        if t and t[0].startswith("Cext") and "vss" in t[1:3] and (set(t[1:3]) & WELL_NETS):
            t[1 if t[1] == "vss" else 2] = "vdd"
            line, moved = " ".join(t), moved + 1
        va.append(line)
    va.insert(3, "* VARIANT A: %d substrate capacitors of the n-well nets %s referenced to vdd instead of vss"
              % (moved, " ".join(sorted(WELL_NETS))))
    with open(os.path.join(vdir, "pex_wellcaps_to_vdd.spice"), "w") as f:
        f.write("\n".join(va))
    vb = [line for line in net if not line.startswith("Cext")]
    vb.insert(3, "* VARIANT B: all parasitic capacitors removed, extracted device geometry only")
    with open(os.path.join(vdir, "pex_nocaps.spice"), "w") as f:
        f.write("\n".join(vb))
    return {"A_wellcaps_to_vdd": "../variants/pex_wellcaps_to_vdd.spice", "B_nocaps": "../variants/pex_nocaps.spice"}


WIRE = {'r1_top': 60.0, 'r1_bot': 41.0, 'r2_top': 81.0, 'r2_bot': 48.0, 'ring': 15.0}   # Ohm, see docstring


def wire_variant():
    """write variants/pex_wire.spice: g1_bgr_pex.spice plus the hand-counted series resistances"""
    vdir = os.path.join(HERE, "variants")
    os.makedirs(vdir, exist_ok=True)
    out = []
    hit = {"emitters": 0, "r1": 0, "r2_top": 0, "r2_bot": 0}
    for line in open(os.path.join(HERE, "g1_bgr_pex.spice")).read().split("\n"):
        t = line.split()
        # devices are selected by their nets (kpex renumbers the instances between runs)
        if t and t[0].startswith("XQ") and t[3] == "vss" and t[1] in ("vbe", "vbe3", "vd2"):   # Q1 Q1B Q3 QD2: emitter on the ring
            t[3] = "vss_ring"
            line = " ".join(t)
            hit["emitters"] += 1
        elif t and t[0].startswith("XR") and t[4] == "rppd" and set(t[1:3]) == {"vss", "dvbe"}:   # R1: bottom to the ring, top to dvbe
            line = "%s r1_bot r1_top vss rppd %s" % (t[0], " ".join(t[5:]))
            hit["r1"] += 1
        elif t and t[0].startswith("XR") and t[4] == "rppd" and "vref" in t[1:3]:                # R2 top segment
            other = t[1] if t[2] == "vref" else t[2]
            line = "%s %s r2_top vss rppd %s" % (t[0], other, " ".join(t[5:]))
            hit["r2_top"] += 1
        elif t and t[0].startswith("XR") and t[4] == "rppd" and "vbe3" in t[1:3]:                # R2 bottom segment
            other = t[1] if t[2] == "vbe3" else t[2]
            line = "%s %s r2_bot vss rppd %s" % (t[0], other, " ".join(t[5:]))
            hit["r2_bot"] += 1
        if line.startswith(".ends"):
            out.append("* VARIANT C: hand-counted wiring resistances (PDK LEF sheet/via values), see run_postlayout.py")
            out.append("Rw_r1_top r1_top dvbe %g" % WIRE['r1_top'])
            out.append("Rw_r1_bot r1_bot vss_ring %g" % WIRE['r1_bot'])
            out.append("Rw_r2_top r2_top vref %g" % WIRE['r2_top'])
            out.append("Rw_r2_bot r2_bot vbe3 %g" % WIRE['r2_bot'])
            out.append("Rw_ring vss_ring vss %g" % WIRE['ring'])
        out.append(line)
    assert hit == {"emitters": 4, "r1": 1, "r2_top": 1, "r2_bot": 1}, hit
    path = os.path.join(vdir, "pex_wire.spice")
    with open(path, "w") as f:
        f.write("\n".join(out))
    return "../variants/pex_wire.spice"


def gen(suite):
    decks = []
    if suite in ("op", "all"):
        for t in ("-40", "27", "125", "175"):
            decks.append(deck(f"op_typ_T{t}_3.3", "op", "hbt_typ", "mos_tt", "res_typ", "3.3", ctl("op"), TEMP=t))
        decks.append(deck("op_typ_T27_3.3_r4", "op ratio4", "hbt_typ", "mos_tt", "res_typ", "3.3", ctl("op"), r4="3.3", TEMP="27"))
    if suite in ("temp", "all"):
        for h in ("hbt_typ", "hbt_bcs", "hbt_wcs"):
            decks.append(deck(f"temp_{h}_mos_tt_res_typ_3.3", "temp sweep", h, "mos_tt", "res_typ", "3.3", ctl("temp")))
    if suite in ("startup", "all"):
        decks.append(deck("startup_hbt_typ_mos_tt_res_typ_T27_3.0", "start-up 1 ms ramp", "hbt_typ", "mos_tt", "res_typ", "3.0",
                          ctl("startup"), TEMP="27", TRAMP="1m", TEND="3m", TSTEP="2u"))
    if suite in ("psrr", "all"):
        for t in ("-40", "27", "175"):
            decks.append(deck(f"psrr_hbt_typ_mos_tt_res_typ_T{t}_3.3", "PSRR", "hbt_typ", "mos_tt", "res_typ", "3.3", ctl("psrr"),
                              vddac="ac 1", TEMP=t))
    if suite in ("wire", "all"):
        inc = wire_variant()
        for name, control, subs in (("op_T27_3.3", ctl("op"), {"TEMP": "27"}), ("temp_3.3", ctl("temp"), {})):
            path = deck("wire_hbt_typ_mos_tt_res_typ_" + name, "wiring-resistance variant C", "hbt_typ", "mos_tt", "res_typ",
                        "3.3", control, **subs)
            text = open(path).read().replace(".include ../g1_bgr_pex.spice", ".include " + inc)
            with open(path, "w") as f:
                f.write(text)
            decks.append(path)
    if suite in ("psrr_var", "all"):
        for name, inc in variants().items():
            path = deck(f"psrrvar_{name}_T27_3.3", "PSRR capacitance variant " + name, "hbt_typ", "mos_tt", "res_typ", "3.3",
                        ctl("psrr"), vddac="ac 1", TEMP="27")
            text = open(path).read().replace(".include ../g1_bgr_pex.spice", ".include " + inc)
            with open(path, "w") as f:
                f.write(text)
            decks.append(path)
    return decks


def run_one(path):
    log = os.path.join(LOGS, os.path.basename(path).replace(".cir", ".log"))
    with open(log, "w") as f:
        subprocess.run(["ngspice", "-b", os.path.basename(path)], cwd=DECKS, stdout=f, stderr=subprocess.STDOUT)
    return log


def meas(log):
    d = {}
    for line in open(log, errors="replace"):
        m = re.match(r"^(\w+)\s*=\s*([-+0-9.eE]+)", line.strip())
        if m:
            d[m.group(1)] = float(m.group(2))
    return d


def parse(suite):
    rows = []
    for f in sorted(os.listdir(LOGS)):
        if not f.startswith(suite + "_") or not f.endswith(".log"):
            continue
        d = meas(os.path.join(LOGS, f))
        d["deck"] = f[:-4]
        rows.append(d)
    if not rows:
        return
    keys = ["deck"] + sorted({k for r in rows for k in r if k != "deck"})
    with open(os.path.join(RES, f"{suite}_summary.csv"), "w") as out:
        out.write(",".join(keys) + "\n")
        for r in rows:
            out.write(",".join(str(r.get(k, "")) for k in keys) + "\n")
    print(f"{suite}: {len(rows)} logs -> results/{suite}_summary.csv")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("suite")
    ap.add_argument("-j", type=int, default=4)
    ap.add_argument("--parse-only", action="store_true")
    a = ap.parse_args()
    for d in (DECKS, LOGS, RES):
        os.makedirs(d, exist_ok=True)
    with open(os.path.join(DECKS, ".spiceinit"), "w") as f:
        f.write(open(os.path.join(SIM, ".spiceinit")).read())
    if not a.parse_only:
        decks = gen(a.suite)
        print(f"{len(decks)} decks, {a.j} parallel")
        with ThreadPoolExecutor(a.j) as ex:
            list(ex.map(run_one, decks))
    for s in (["op", "temp", "startup", "psrr", "psrrvar", "wire"] if a.suite == "all" else [a.suite.replace("psrr_var", "psrrvar")]):
        parse(s)

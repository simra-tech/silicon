#!/usr/bin/env python3
"""R1_T2F runner: re-runs the G1 T2F revision 2 decks under R1 supplies, one CPU, sequential.
Host Python 3.6.  From the repository root:
  export G1_CPUSET=118 G1_CPUS=1 G1_RESULTS_ROOT=/opt/sim/amirmabhout/r1-traces/sims
  python3 designs/r1-joint/blocks/r1_t2f/sim/r1_run_t2f.py <suite>      (suites: ftemp supply corners tight)
Decks go to decks/, ngspice logs to <G1_RESULTS_ROOT>/r1_t2f/<run-id>/, parsed .meas values to results/<suite>.json.
Deck settings are those of the G1 runner (gmin=1e-15 abstol=1e-13 reltol=1e-4 vntol=1e-6 method=gear, tran 5n,
period averaged over cycles 8..24)."""
import json, os, re, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "../../../../.."))
DECKS, RES = os.path.join(HERE, "decks"), os.path.join(HERE, "results")
TMPL = open(os.path.join(HERE, "tb_g1_t2f.spice.tmpl")).read()
CTL = open(os.path.join(HERE, "ctl_freq.txt")).read()
OPT = "gmin=1e-15 abstol=1e-13 reltol=1e-4 vntol=1e-6 method=gear"
CORNER = {"tt": ("hbt_typ", "mos_tt", "res_typ"), "ss": ("hbt_wcs", "mos_ss", "res_wcs"), "ff": ("hbt_bcs", "mos_ff", "res_bcs")}
RUN_ID = os.environ.get("R1_T2F_RUN_ID", "20261020-a")


def deck(name, temp, mode, vdd="3.3", corner="tt", tight=False):
    h, m, r = CORNER[corner]
    tend = "40u" if temp < 0 else "32u"
    subs = {"KIND": "R1 re-run", "HBT": h, "MOS": m, "RES": r, "CAP": "cap_typ", "VDD": vdd, "VDD12": "1.2", "TEMP": str(temp),
            "MODE": "ref" if mode else "ptat", "MODEV": vdd if mode else "0", "TEND": tend, "NA": "8", "NB": "24",
            "OPTIONS": OPT, "WRDATA": ""}
    ctl = CTL
    if tight:   # G1 remedy for the VBIC self-heating NaN at -40 C: reltol 1e-5 and 10 ns maximum step
        subs["OPTIONS"] = OPT.replace("reltol=1e-4", "reltol=1e-5")
        ctl = CTL.replace("tran 5n @@TEND@@\n", "tran 5n @@TEND@@ 0 10n\n")
    text = TMPL.replace("@@CONTROL@@", ctl)
    for k, v in subs.items():
        text = text.replace("@@%s@@" % k, v)
    open(os.path.join(DECKS, name + ".cir"), "w").write(text)
    return name


def gen(suite):
    d = []
    if suite == "ftemp":
        for t in (-40, -25, 0, 27, 50, 75, 100, 125):
            d.append(deck("ftemp_ptat_vdd3.3_T%d" % t, t, 0))
        for t in (-40, 27, 125):
            d.append(deck("ftemp_ref_vdd3.3_T%d" % t, t, 1))
    if suite == "supply":
        for t in (27, 125):
            for v in ("3.0", "3.6"):
                d.append(deck("supply_ptat_vdd%s_T%d" % (v, t), t, 0, vdd=v))
        for v in ("3.0", "3.6"):
            d.append(deck("supply_ref_vdd%s_T27" % v, 27, 1, vdd=v))
    if suite == "corners":
        for c in ("ss", "ff", "tt"):
            for v in ("3.0", "3.6"):
                for t in (27, 125, -40):
                    d.append(deck("corners_ptat_%s_vdd%s_T%d" % (c, v, t), t, 0, vdd=v, corner=c))
    if suite == "tight":   # retry of the -40 C / 3.6 V corner decks that aborted with NaN in run 20261020-a
        for c in ("ss", "ff", "tt"):
            d.append(deck("corners_ptat_%s_vdd3.6_T-40" % c, -40, 0, vdd="3.6", corner=c, tight=True))
    return d


def parse(log):
    d = {}
    for line in open(log, errors="replace"):
        m = re.match(r"^(\w+)\s*=\s*([-+0-9.eE]+)", line.strip())
        if m:
            d[m.group(1)] = float(m.group(2))
    return d


def main():
    suite = sys.argv[1]
    out = os.path.join(os.environ["G1_RESULTS_ROOT"], "r1_t2f", RUN_ID)
    os.makedirs(out, exist_ok=True)
    env = dict(os.environ, G1_WORKDIR="designs/r1-joint/blocks/r1_t2f/sim/decks")
    rows = {}
    for name in gen(suite):
        log = os.path.join(out, name + ".log")
        t0 = time.time()
        with open(log, "w") as f:
            rc = subprocess.call(["flow/run.sh", "ngspice", "-b", name + ".cir"], cwd=ROOT, env=env, stdout=f, stderr=subprocess.STDOUT)
        r = parse(log)
        r["wall_s"] = round(time.time() - t0, 1)
        r["rc"] = rc
        rows[name] = r
        print(name, r.get("freq"), r["wall_s"], flush=True)
        json.dump(rows, open(os.path.join(RES, "%s_%s.json" % (suite, RUN_ID)), "w"), indent=1, sort_keys=True)


if __name__ == "__main__":
    main()

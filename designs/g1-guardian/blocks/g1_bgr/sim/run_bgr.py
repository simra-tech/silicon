#!/usr/bin/env python3
"""G1_BGR simulation runner. Generates ngspice decks from tb_g1_bgr.spice.tmpl + ctl_*.txt,
runs them in parallel and parses the logs into results/*.csv.

Run inside the pinned container from the repository root:
  G1_WORKDIR=designs/g1-guardian/blocks/g1_bgr/sim flow/run.sh python3 run_bgr.py <suite> [-j N]
suites: op temp extrap startup startup_slow psrr mc all
"""
import argparse, itertools, os, re, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
DECKS, LOGS, RES = (os.path.join(HERE, d) for d in ("decks", "logs", "results"))
HBT = ["hbt_typ", "hbt_bcs", "hbt_wcs"]
MOS = ["mos_tt", "mos_ss", "mos_ff"]
RESC = ["res_typ", "res_bcs", "res_wcs"]
VDDS = ["3.0", "3.3", "3.6"]
TMPL = open(os.path.join(HERE, "tb_g1_bgr.spice.tmpl")).read()


def ctl(name):
    return open(os.path.join(HERE, f"ctl_{name}.txt")).read()


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


def gen(suite):
    decks = []
    if suite in ("op", "all"):
        for t in ("-40", "27", "175"):
            decks.append(deck(f"op_typ_T{t}_3.3", "op", "hbt_typ", "mos_tt", "res_typ", "3.3", ctl("op"), TEMP=t))
        decks.append(deck("op_typ_T27_3.3_r4", "op ratio4", "hbt_typ", "mos_tt", "res_typ", "3.3", ctl("op"), r4="3.3", TEMP="27"))
    if suite in ("temp", "all"):
        for h, m, r, v in itertools.product(HBT, MOS, RESC, VDDS):
            decks.append(deck(f"temp_{h}_{m}_{r}_{v}", "temp sweep", h, m, r, v, ctl("temp")))
        decks.append(deck("temp_typ_r4_3.3", "temp sweep ratio4", "hbt_typ", "mos_tt", "res_typ", "3.3", ctl("temp"), r4="3.3"))
    if suite in ("extrap", "all"):
        for h in HBT:
            decks.append(deck(f"extrap_{h}_mos_tt_res_typ_3.3", "MODEL EXTRAPOLATED below -40 C", h, "mos_tt", "res_typ", "3.3", ctl("extrap")))
    if suite in ("startup", "all"):
        for h, m, r in itertools.product(HBT, MOS, RESC):
            for t in ("-40", "27", "175"):
                decks.append(deck(f"startup_{h}_{m}_{r}_T{t}_3.0", "start-up 1 ms ramp", h, m, r, "3.0", ctl("startup"),
                                  TEMP=t, TRAMP="1m", TEND="3m", TSTEP="2u"))
    if suite in ("startup_slow", "all"):
        for h, m, r in itertools.product(HBT, MOS, RESC):
            decks.append(deck(f"startupslow_{h}_{m}_{r}_T27_3.0", "start-up 100 ms ramp", h, m, r, "3.0", ctl("startup"),
                              TEMP="27", TRAMP="100m", TEND="130m", TSTEP="100u"))
        for t in ("-40", "175"):
            decks.append(deck(f"startupslow_hbt_typ_mos_tt_res_typ_T{t}_3.0", "start-up 100 ms ramp", "hbt_typ", "mos_tt", "res_typ", "3.0",
                              ctl("startup"), TEMP=t, TRAMP="100m", TEND="130m", TSTEP="100u"))
    if suite in ("psrr", "all"):
        for h, m, r in itertools.product(HBT, MOS, RESC):
            for t in ("-40", "27", "175"):
                decks.append(deck(f"psrr_{h}_{m}_{r}_T{t}_3.3", "PSRR", h, m, r, "3.3", ctl("psrr"), vddac="ac 1", TEMP=t))
    if suite in ("mc", "all"):
        for i in range(300):
            decks.append(deck(f"mc_typ_mismatch_T27_3.3_s{i:03d}", f"Monte Carlo mismatch seed {i + 1}", "hbt_typ_mismatch",
                              "mos_tt_mismatch", "res_typ_mismatch", "3.3", ctl("mc"), SEED=i + 1))
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
    ap.add_argument("-j", type=int, default=os.cpu_count() or 2)
    ap.add_argument("--parse-only", action="store_true")
    a = ap.parse_args()
    for d in (DECKS, LOGS, RES):
        os.makedirs(d, exist_ok=True)
    # ngspice reads .spiceinit from its working directory: the OSDI model loader must sit next to the decks
    with open(os.path.join(DECKS, ".spiceinit"), "w") as f:
        f.write(open(os.path.join(HERE, ".spiceinit")).read())
    if not a.parse_only:
        decks = gen(a.suite)
        print(f"{len(decks)} decks, {a.j} parallel")
        with ThreadPoolExecutor(a.j) as ex:
            list(ex.map(run_one, decks))
    for s in (["op", "temp", "extrap", "startup", "startupslow", "psrr", "mc"] if a.suite == "all" else [a.suite.replace("startup_slow", "startupslow")]):
        parse(s)

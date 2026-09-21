#!/usr/bin/env python3
"""G1_T2F simulation runner (decks from tb_g1_t2f.spice.tmpl + ctl_freq.txt / ctl_vce.txt).
Inside the pinned container, from the repository root:
  G1_WORKDIR=designs/g1-guardian/blocks/g1_t2f/sim flow/run.sh python3 run_t2f.py <suite> [-j N] [--rev1]
suites: nom ftemp corners supply extrap vce all
  vce   max V_CE of every comparator HBT (whole run, including the en=0 hold) at 3.6 V / 175 C, 3.0 V / -40 C
        and 3.3 V / 27 C, both modes; --rev1 runs the same decks on the superseded revision-1 netlist
        (../rev1/xschem/g1_t2f.spice, collector nodes oa/ob) and names them vce_rev1_*.
  --only <substring>  run only the decks of the suite whose name contains the substring (the parse step
        still collects every log of the suite).
Decks are written to decks/, the ngspice logs to logs/ (kept in the tree as evidence), the parsed .meas values
to results/<suite>_summary.csv. Decks listed in TIGHT use the convergence settings of the vce suite
(reltol=1e-5, 10 ns maximum step): with the standard options the npn13G2 VBIC self-heating solution aborts
with a NaN at -40 C in some decks (revision 1's netlist too); the frequency difference between the two
settings is 0.03 %.
"""
import argparse, itertools, os, re, subprocess
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
DECKS, LOGS, RES = (os.path.join(HERE, d) for d in ("decks", "logs", "results"))
TMPL = open(os.path.join(HERE, "tb_g1_t2f.spice.tmpl")).read()
CTL = open(os.path.join(HERE, "ctl_freq.txt")).read()
CTL_VCE = open(os.path.join(HERE, "ctl_vce.txt")).read()
OPTIONS = "gmin=1e-15 abstol=1e-13 reltol=1e-4 vntol=1e-6 method=gear"       # every suite except vce
OPTIONS_VCE = "gmin=1e-15 abstol=1e-13 reltol=1e-5 vntol=1e-6 method=gear"   # 3.0 V / -40 C: the VBIC self-heating
# solution of the npn13G2 model aborts with a NaN at reltol=1e-4; reltol=1e-5 plus the 10 ns maximum step in ctl_vce.txt converges
TIGHT = {"corners_ptat_hbt_wcs_mos_ss_res_wcs_cap_typ_T-40"}   # aborted at 3.7 us with the standard options
T2F = "../../xschem/g1_t2f.spice"
T2F_REV1 = "../../rev1/xschem/g1_t2f.spice"
HBT, MOS, RESC = ["hbt_typ", "hbt_bcs", "hbt_wcs"], ["mos_tt", "mos_ss", "mos_ff"], ["res_typ", "res_bcs", "res_wcs"]
TEMPS = [-40, -25, -10, 5, 20, 25, 35, 50, 65, 80, 95, 100, 110, 125, 140, 155, 170, 175]
REF_TEMPS = [-40, -10, 25, 50, 65, 100, 125, 150, 175]   # REF mode (ratio) at fewer points to bound run time
TEMPS = sorted(set(TEMPS) | {150})
NA, NB = 8, 24    # average the period over cycles 8..24 after enable


def deck(name, kind, temp, mode, hbt="hbt_typ", mos="mos_tt", res="res_typ", cap="cap_typ", vdd="3.3", vdd12="1.2", tend="32u",
         wrdata=False, ctl=CTL, options=OPTIONS, t2f=T2F, rev1=False):
    if name in TIGHT:
        options, ctl = OPTIONS_VCE, ctl.replace("tran 5n @@TEND@@\n", "tran 5n @@TEND@@ 0 10n\n")
    subs = {"KIND": kind, "HBT": hbt, "MOS": mos, "RES": res, "CAP": cap, "VDD": vdd, "VDD12": vdd12, "TEMP": str(temp),
            "MODE": "ref" if mode else "ptat", "MODEV": vdd if mode else "0", "TEND": tend, "NA": str(NA), "NB": str(NB),
            "OPTIONS": options, "T2F": t2f,
            "CA1": "oa1" if rev1 else "ca1", "CB1": "ob1" if rev1 else "cb1", "CA2": "oa2" if rev1 else "ca2", "CB2": "ob2" if rev1 else "cb2",
            "WRDATA": f"wrdata ../results/{name}.dat v(fout) v(xt2f.cap1) v(xt2f.cap2) v(xt2f.vth) v(xt2f.q)" if wrdata else ""}
    text = TMPL.replace("@@CONTROL@@", ctl)
    for k, v in subs.items():
        text = text.replace(f"@@{k}@@", v)
    path = os.path.join(DECKS, name + ".cir")
    open(path, "w").write(text)
    return path


def gen(suite, rev1=False):
    d = []
    if suite in ("nom", "all"):
        d.append(deck("nom_ptat_T27", "nominal", 27, 0, wrdata=True))
        d.append(deck("nom_ref_T27", "nominal", 27, 1, wrdata=True))
    if suite in ("ftemp", "all"):
        for t in TEMPS:
            tend = "40u" if t < 0 else "32u"
            d.append(deck(f"ftemp_ptat_T{t}", "f(T) nominal", t, 0, tend=tend))
            if t in REF_TEMPS:
                d.append(deck(f"ftemp_ref_T{t}", "f(T) nominal", t, 1, tend=tend))
    if suite in ("corners", "all"):
        for h, m, r in itertools.product(HBT[1:], MOS[1:], RESC[1:]):
            d.append(deck(f"corners_ptat_{h}_{m}_{r}_cap_typ_T27", "process corners", 27, 0, h, m, r))
        d.append(deck("corners_ptat_hbt_typ_mos_tt_res_typ_cap_typ_T27", "process corners", 27, 0))
        for c in ("cap_bcs", "cap_wcs"):
            d.append(deck(f"corners_ptat_hbt_typ_mos_tt_res_typ_{c}_T27", "cap corners", 27, 0, cap=c))
            d.append(deck(f"corners_ref_hbt_typ_mos_tt_res_typ_{c}_T27", "cap corners", 27, 1, cap=c))
        for h, m, r in (("hbt_bcs", "mos_ff", "res_bcs"), ("hbt_wcs", "mos_ss", "res_wcs")):
            d.append(deck(f"corners_ref_{h}_{m}_{r}_cap_typ_T27", "process corners", 27, 1, h, m, r))
            for t in (-40, 175):
                d.append(deck(f"corners_ptat_{h}_{m}_{r}_cap_typ_T{t}", "process corners", t, 0, h, m, r, tend="40u" if t < 0 else "32u"))
    if suite in ("supply", "all"):
        for v in ("3.0", "3.3", "3.6"):
            d.append(deck(f"supply_ptat_vdd{v}_T27", "supply", 27, 0, vdd=v))
            d.append(deck(f"supply_ref_vdd{v}_T27", "supply", 27, 1, vdd=v))
        for v in ("1.08", "1.32"):
            d.append(deck(f"supply_ptat_vdd12_{v}_T27", "supply 1.2 V", 27, 0, vdd12=v))
    if suite in ("extrap", "all"):
        for t in (-196, -100):
            d.append(deck(f"extrap_ptat_T{t}", "MODEL EXTRAPOLATED below -40 C", t, 0, tend="80u"))
        d.append(deck("extrap_ref_T-196", "MODEL EXTRAPOLATED below -40 C", -196, 1, tend="80u"))
    if suite in ("vce", "all"):
        tag = "vce_rev1" if rev1 else "vce"
        t2f = T2F_REV1 if rev1 else T2F
        for v, t in (("3.6", 175), ("3.0", -40), ("3.3", 27)):
            for m in (0, 1):
                d.append(deck(f"{tag}_{'ref' if m else 'ptat'}_vdd{v}_T{t}", "V_CE check" + (" (revision 1 netlist)" if rev1 else ""),
                              t, m, vdd=v, tend="40u" if t < 0 else "32u", ctl=CTL_VCE, options=OPTIONS_VCE, t2f=t2f, rev1=rev1))
    return d


def run_one(path):
    log = os.path.join(LOGS, os.path.basename(path).replace(".cir", ".log"))
    with open(log, "w") as f:
        subprocess.run(["ngspice", "-b", os.path.basename(path)], cwd=DECKS, stdout=f, stderr=subprocess.STDOUT)


def parse(suite):
    rows = []
    for f in sorted(os.listdir(LOGS)):
        if f.startswith(suite + "_") and f.endswith(".log") and not (suite == "vce" and f.startswith("vce_rev1_")):
            d = {"deck": f[:-4]}
            for line in open(os.path.join(LOGS, f), errors="replace"):
                m = re.match(r"^(\w+)\s*=\s*([-+0-9.eE]+)", line.strip())
                if m:
                    d[m.group(1)] = float(m.group(2))
            rows.append(d)
    if rows:
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
    ap.add_argument("--rev1", action="store_true", help="vce suite on the revision-1 netlist (../rev1), decks vce_rev1_*")
    ap.add_argument("--only", default=None, help="run only the decks whose name contains this substring")
    a = ap.parse_args()
    for p in (DECKS, LOGS, RES):
        os.makedirs(p, exist_ok=True)
    open(os.path.join(DECKS, ".spiceinit"), "w").write(open(os.path.join(HERE, ".spiceinit")).read())
    if not a.parse_only:
        decks = gen(a.suite, a.rev1)
        if a.only:
            decks = [d for d in decks if a.only in os.path.basename(d)]
        print(f"{len(decks)} decks, {a.j} parallel")
        with ThreadPoolExecutor(a.j) as ex:
            list(ex.map(run_one, decks))
    suites = ["nom", "ftemp", "corners", "supply", "extrap", "vce"] if a.suite == "all" else [a.suite]
    if a.rev1 and a.suite == "vce":
        suites = ["vce_rev1"]
    for s in suites:
        parse(s)

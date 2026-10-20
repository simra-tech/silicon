#!/usr/bin/env python3
"""r1_bgr simulation runner. Runs inside the pinned container (flow/run.sh python3 run_bgr.py ...).
Writes decks, logs and raw data to $G1_RESULTS_ROOT/r1_bgr/<run-id>/ and a summary JSON to
results/<run-id>.json (tracked). Suites: size, temp, mc, startup, psrr.
"""
import json, math, os, subprocess, sys, time, itertools, hashlib
from multiprocessing.pool import ThreadPool

HERE = os.path.dirname(os.path.abspath(__file__))
SCH = os.path.join(HERE, "..", "schematic")
sys.path.insert(0, SCH)
from gen_r1_bgr import gen

JOBS = int(os.environ.get("BGR_JOBS", "2"))
ROOT = os.environ["G1_RESULTS_ROOT"]

def tmpl():
    return open(os.path.join(HERE, "tb_r1_bgr.spice.tmpl")).read()

def deck(kind, netlist, hbt, mos, res, vdd, control, vddac=""):
    s = tmpl()
    for k, v in dict(KIND=kind, NETLIST=netlist, HBT=hbt, MOS=mos, RES=res, VDD=str(vdd), VDDAC=vddac, CONTROL=control).items():
        s = s.replace("@@%s@@" % k, v)
    return s

CTL_TEMP = """.control
set filetype=ascii
set wr_singlescale
set wr_vecnames
dc temp -40 125 5
let iptat = i(vload)
let idd = -i(vdd)
wrdata @@OUT@@.dat v(vref) iptat idd v(dvbe) v(vbe) v(pbias)
.endc
"""
CTL_PSRR = """.control
set filetype=ascii
option temp=@@TEMP@@
op
let idd = -i(vdd)
print v(vref) idd
ac dec 20 1 100meg
let psrr_db = db(v(vref))
meas ac psrr_dc find psrr_db at=1
meas ac psrr_1k find psrr_db at=1k
meas ac psrr_20k find psrr_db at=20k
meas ac psrr_1m find psrr_db at=1meg
.endc
"""
CTL_OP = """.control
option temp=@@TEMP@@
op
let idd = -i(vdd)
print v(vdd) v(xbgr.d2) v(pbias) v(pcasc) v(xbgr.n1) v(xbgr.c2) v(vbe) v(dvbe) v(xbgr.vb2) v(xbgr.d1_0) v(vref) v(xbgr.d3) v(xbgr.vbe3) v(xbgr.det) v(xbgr.kick) idd i(vload)
.endc
"""

CTL_START = """.control
set filetype=ascii
set wr_singlescale
set wr_vecnames
option temp=@@TEMP@@
alter @vdd[pwl] = [ 0 0 @@TRAMP@@ @@VDD@@ @@TEND@@ @@VDD@@ ]
tran @@TSTEP@@ @@TEND@@ uic
let iptat = i(vload)
meas tran vref_end find v(vref) at=@@TEND@@
meas tran iptat_end find iptat at=@@TEND@@
meas tran t_99 when v(vref)=@@V99@@ rise=1
meas tran vref_max max v(vref)
wrdata @@OUT@@.dat v(vref) iptat v(vdd)
.endc
"""

def run_one(args):
    path, log = args
    t0 = time.time()
    with open(log, "w") as f:
        rc = subprocess.call(["ngspice", "-b", path], stdout=f, stderr=subprocess.STDOUT, cwd=HERE)
    return path, rc, time.time() - t0

def run_all(items):
    pool = ThreadPool(JOBS)
    out = pool.map(run_one, items)
    pool.close(); pool.join()
    return out

def readdat(p):
    rows = [l.split() for l in open(p) if l.strip()]
    hdr = rows[0]; data = [[float(x) for x in r] for r in rows[1:]]
    return {h: [r[i] for r in data] for i, h in enumerate(hdr)}

def tcbox(T, v, lo=-40, hi=125):
    sel = [x for t, x in zip(T, v) if lo - 1e-6 <= t <= hi + 1e-6]
    vm = [x for t, x in zip(T, v) if abs(t - 27) < 3]
    ref = sum(sel) / len(sel)
    return (max(sel) - min(sel)) / ref / (hi - lo) * 1e6

def val_at(T, v, t0):
    best = min(range(len(T)), key=lambda i: abs(T[i] - t0))
    return v[best]

def write_netlist(rundir, p):
    net = os.path.join(rundir, "r1_bgr.spice")
    open(net, "w").write(gen(p["n1"], p["n2"], p["n3"], p["m"], p["r1"], p["r2"], p["rb"], p["rx"]))
    return net

def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()

DEF = dict(n1=12, n2=48, n3=4, m=8, r1=84.0, r2=347.5, rb=500.0, rx=192.0)

def parse_params(argv):
    p = dict(DEF)
    for a in argv:
        if "=" in a:
            k, v = a.split("=", 1)
            p[k] = type(DEF[k])(v) if k in DEF else v
    return p

def temp_suite(rundir, net, cases):
    items = []
    for name, hbt, mos, res, vdd in cases:
        out = os.path.join(rundir, name)
        d = deck("temp", net, hbt, mos, res, vdd, CTL_TEMP.replace("@@OUT@@", out))
        open(out + ".cir", "w").write(d)
        items.append((out + ".cir", out + ".log"))
    res = run_all(items)
    rows = []
    for (name, hbt, mos, res_, vdd), (path, rc, dt) in zip(cases, res):
        try:
            d = readdat(os.path.join(rundir, name) + ".dat")
            T = d["temp-sweep"] if "temp-sweep" in d else d[list(d)[0]]
            v = d["v(vref)"]
            rows.append(dict(case=name, hbt=hbt, mos=mos, res=res_, vdd=vdd, rc=rc, seconds=round(dt, 1),
                             vref27=val_at(T, v, 27), vref_m40=val_at(T, v, -40), vref125=val_at(T, v, 125),
                             vmin=min(v), vmax=max(v), tc_box=tcbox(T, v),
                             iptat27_uA=val_at(T, d["iptat"], 27) * 1e6, idd27_uA=val_at(T, d["idd"], 27) * 1e6,
                             idd_max_uA=max(d["idd"]) * 1e6, dvbe27_mV=val_at(T, d["v(dvbe)"], 27) * 1e3))
        except Exception as e:
            rows.append(dict(case=name, rc=rc, error=str(e)))
    return rows

CORN = [("hbt_typ", "mos_tt", "res_typ")] + [(h, m, r) for h in ("hbt_typ", "hbt_bcs", "hbt_wcs") for m in ("mos_tt", "mos_ss", "mos_ff") for r in ("res_typ", "res_bcs", "res_wcs")][1:]

def main():
    suite, runid = sys.argv[1], sys.argv[2]
    p = parse_params(sys.argv[3:])
    rundir = os.path.join(ROOT, "r1_bgr", runid)
    os.makedirs(rundir, exist_ok=False)
    t0 = time.time()
    summary = dict(run_id=runid, suite=suite, params=p, started=time.strftime("%Y-%m-%dT%H:%M:%S"))
    if suite == "size":
        rows = []
        r2s = [float(x) for x in p.get("r2list", "300,320,340,360,380").split(",")]
        cases = []; nets = {}
        for r2 in r2s:
            q = dict(p); q["r2"] = r2
            sub = os.path.join(rundir, "r2_%g" % r2); os.makedirs(sub)
            net = write_netlist(sub, q)
            cases.append((sub, net))
        items = []
        for sub, net in cases:
            out = os.path.join(sub, "tt")
            open(out + ".cir", "w").write(deck("temp", net, "hbt_typ", "mos_tt", "res_typ", 3.3, CTL_TEMP.replace("@@OUT@@", out)))
            items.append((out + ".cir", out + ".log"))
        res = run_all(items)
        for r2, (sub, net), (path, rc, dt) in zip(r2s, cases, res):
            try:
                d = readdat(os.path.join(sub, "tt.dat")); T = d[list(d)[0]]; v = d["v(vref)"]
                rows.append(dict(r2=r2, rc=rc, vref27=val_at(T, v, 27), tc_box=tcbox(T, v), vmin=min(v), vmax=max(v),
                                 iptat27_uA=val_at(T, d["iptat"], 27) * 1e6, idd27_uA=val_at(T, d["idd"], 27) * 1e6,
                                 dvbe27_mV=val_at(T, d["v(dvbe)"], 27) * 1e3))
            except Exception as e:
                rows.append(dict(r2=r2, rc=rc, error=str(e)))
        summary["rows"] = rows
    else:
        net = write_netlist(rundir, p)
        summary["netlist_sha256"] = sha(net)
        if suite == "temp":
            vdds = [float(x) for x in str(p.get("vdds", "3.0,3.3,3.6")).split(",")]
            cases = [("%s_%s_%s_%g" % (h, m, r, v), h, m, r, v) for (h, m, r) in CORN for v in vdds]
            summary["rows"] = temp_suite(rundir, net, cases)
        elif suite == "mc":
            n = int(p.get("nmc", "50"))
            cases = []
            items = []
            for s in range(1, n + 1):
                out = os.path.join(rundir, "mc_s%03d" % s)
                ctl = ".option seed=%d\n" % s + CTL_TEMP.replace("@@OUT@@", out)
                open(out + ".cir", "w").write(deck("mc", net, "hbt_typ_mismatch", "mos_tt_mismatch", "res_typ_mismatch", 3.3, ctl))
                items.append((out + ".cir", out + ".log")); cases.append(s)
            res = run_all(items)
            rows = []
            for s, (path, rc, dt) in zip(cases, res):
                try:
                    d = readdat(os.path.join(rundir, "mc_s%03d.dat" % s)); T = d[list(d)[0]]; v = d["v(vref)"]
                    rows.append(dict(seed=s, rc=rc, vref27=val_at(T, v, 27), tc_box=tcbox(T, v), iptat27_uA=val_at(T, d["iptat"], 27) * 1e6,
                                     dvbe27_mV=val_at(T, d["v(dvbe)"], 27) * 1e3))
                except Exception as e:
                    rows.append(dict(seed=s, rc=rc, error=str(e)))
            ok = [r for r in rows if "vref27" in r]
            vs = [r["vref27"] for r in ok]; mu = sum(vs) / len(vs)
            sd = math.sqrt(sum((x - mu) ** 2 for x in vs) / (len(vs) - 1))
            ip = [r["iptat27_uA"] for r in ok]; mi = sum(ip) / len(ip)
            si = math.sqrt(sum((x - mi) ** 2 for x in ip) / (len(ip) - 1))
            tcs = [r["tc_box"] for r in ok]
            summary["stats"] = dict(n_attempted=n, n_completed=len(ok), vref_mean=mu, vref_sigma=sd, vref_sigma_pct=100 * sd / mu,
                                    vref_min=min(vs), vref_max=max(vs), iptat_mean_uA=mi, iptat_sigma_pct=100 * si / mi,
                                    tc_max=max(tcs), tc_mean=sum(tcs) / len(tcs), tc_le30=sum(1 for t in tcs if t <= 30))
            summary["rows"] = rows
        elif suite == "op":
            cs = [(h, m, r, t, v) for (h, m, r) in [("hbt_typ","mos_tt","res_typ"),("hbt_wcs","mos_ss","res_wcs"),("hbt_bcs","mos_ff","res_bcs"),("hbt_bcs","mos_ss","res_wcs"),("hbt_wcs","mos_ff","res_bcs")] for t in (-40, 27, 125) for v in (3.0, 3.6)]
            items = []; names = []
            for h, m, r, t, v in cs:
                name = "%s_%s_%s_T%g_%g" % (h, m, r, t, v); names.append(name)
                out = os.path.join(rundir, name)
                open(out + ".cir", "w").write(deck("op", net, h, m, r, v, CTL_OP.replace("@@TEMP@@", str(t))))
                items.append((out + ".cir", out + ".log"))
            res = run_all(items)
            rows = []
            for name, (h, m, r, t, v), (path, rc, dt) in zip(names, cs, res):
                nv = {}
                for l in open(os.path.join(rundir, name + ".log")):
                    if " = " in l and (l.strip().startswith("v(") or l.strip().startswith("idd") or l.strip().startswith("i(")):
                        k, x = l.split(" = ")
                        try: nv[k.strip()] = float(x.split()[0])
                        except Exception: pass
                g = lambda k: nv.get(k, float("nan"))
                rows.append(dict(case=name, hbt=h, mos=m, res=r, temp=t, vdd=v, rc=rc, vref=g("v(vref)"), idd_uA=g("idd") * 1e6, iptat_uA=-g("i(vload)") * 1e6,
                                 vds_mp2=g("v(vdd)") - g("v(xbgr.d2)"), vds_mc2=g("v(xbgr.d2)") - g("v(pbias)"), vds_mp1=g("v(vdd)") - g("v(xbgr.d1_0)"),
                                 vds_mc1=g("v(xbgr.d1_0)") - g("v(xbgr.n1)"), vds_mnc1=g("v(xbgr.n1)") - g("v(vbe)"), vce_q2=g("v(xbgr.c2)") - g("v(dvbe)"),
                                 vds_mc3=g("v(xbgr.d3)") - g("v(vref)"), vsg_mirror=g("v(vdd)") - g("v(pbias)"), vbe1=g("v(vbe)"), vbe3=g("v(xbgr.vbe3)"),
                                 kick=g("v(xbgr.kick)"), det=g("v(xbgr.det)")))
            summary["rows"] = rows
        elif suite == "psrr":
            cs = [("tt27", "hbt_typ", "mos_tt", "res_typ", 27, 3.3), ("ss125", "hbt_wcs", "mos_ss", "res_wcs", 125, 3.0), ("ff_m40", "hbt_bcs", "mos_ff", "res_bcs", -40, 3.6),
                  ("tt27_3v0", "hbt_typ", "mos_tt", "res_typ", 27, 3.0), ("tt125_3v0", "hbt_typ", "mos_tt", "res_typ", 125, 3.0)]
            items = []
            for name, h, m, r, t, v in cs:
                out = os.path.join(rundir, name)
                open(out + ".cir", "w").write(deck("psrr", net, h, m, r, v, CTL_PSRR.replace("@@TEMP@@", str(t)), vddac="ac 1"))
                items.append((out + ".cir", out + ".log"))
            res = run_all(items)
            rows = []
            for (name, h, m, r, t, v), (path, rc, dt) in zip(cs, res):
                row = dict(case=name, hbt=h, mos=m, res=r, temp=t, vdd=v, rc=rc)
                for l in open(os.path.join(rundir, name + ".log")):
                    for k in ("psrr_dc", "psrr_1k", "psrr_20k", "psrr_1m"):
                        if l.strip().startswith(k + " "):
                            row[k + "_dB"] = float(l.split("=")[1].split()[0])
                    if l.strip().startswith("v(vref) ="):
                        row["vref"] = float(l.split("=")[1])
                    if l.strip().startswith("idd ="):
                        row["idd_uA"] = float(l.split("=")[1]) * 1e6
                rows.append(row)
            summary["rows"] = rows
        elif suite == "startup":
            cs = [("tt27", "hbt_typ", "mos_tt", "res_typ", 27), ("ss125", "hbt_wcs", "mos_ss", "res_wcs", 125), ("ff_m40", "hbt_bcs", "mos_ff", "res_bcs", -40),
                  ("ss_m40", "hbt_wcs", "mos_ss", "res_wcs", -40), ("ff125", "hbt_bcs", "mos_ff", "res_bcs", 125)]
            ramps = [("r1ms", 1e-3, 3e-3, 1e-6), ("r10us", 10e-6, 1e-3, 0.2e-6)]
            items = []; meta = []
            for (name, h, m, r, t), (rn, tr, te, ts) in itertools.product(cs, ramps):
                out = os.path.join(rundir, "%s_%s" % (name, rn))
                ctl = CTL_START
                for k, v in dict(TEMP=t, TRAMP=tr, VDD=3.0, TEND=te, TSTEP=ts, OUT=out, V99="%(v99)s").items():
                    ctl = ctl.replace("@@%s@@" % k, str(v))
                meta.append((name, h, m, r, t, rn, out, ctl))
            # first get final vref per corner from op, then 99 % threshold: use 0.99 * nominal 1.04 V as fixed level
            for name, h, m, r, t, rn, out, ctl in meta:
                ctl = ctl % dict(v99="1.0")
                d = deck("startup", net, h, m, r, 3.0, ctl).replace("Vdd vdd 0 dc 3.0", "Vdd vdd 0 dc 3.0 pwl(0 0 1 3.0)")
                open(out + ".cir", "w").write(d)
                items.append((out + ".cir", out + ".log"))
            res = run_all(items)
            rows = []
            for (name, h, m, r, t, rn, out, ctl), (path, rc, dt) in zip(meta, res):
                row = dict(case=name, ramp=rn, hbt=h, mos=m, res=r, temp=t, rc=rc)
                for l in open(out + ".log"):
                    for k in ("vref_end", "iptat_end", "t_99", "vref_max"):
                        if l.strip().startswith(k + " "):
                            try:
                                row[k] = float(l.split("=")[1].split()[0])
                            except Exception:
                                pass
                # settle time to within 1 % of end value
                try:
                    d = readdat(out + ".dat"); tt = d[list(d)[0]]; v = d["v(vref)"]; ve = v[-1]
                    tset = None
                    for i in range(len(v) - 1, -1, -1):
                        if abs(v[i] - ve) > 0.01 * ve:
                            tset = tt[i + 1] if i + 1 < len(tt) else tt[i]; break
                    row["t_settle_1pct"] = tset
                    row["ok"] = bool(0.95 < ve < 1.15 and abs(row.get("iptat_end", 0)) > 1e-6)
                except Exception as e:
                    row["error"] = str(e); row["ok"] = False
                rows.append(row)
            summary["rows"] = rows
    summary["wall_s"] = round(time.time() - t0, 1)
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    json.dump(summary, open(os.path.join(HERE, "results", runid + ".json"), "w"), indent=1)
    json.dump(summary, open(os.path.join(rundir, "summary.json"), "w"), indent=1)
    print(json.dumps(summary.get("stats", summary.get("rows", [])[:40]), indent=0)[:6000])

if __name__ == "__main__":
    main()

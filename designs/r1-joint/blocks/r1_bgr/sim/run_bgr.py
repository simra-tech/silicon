#!/usr/bin/env python3
"""r1_bgr simulation runner. Runs inside the pinned container (flow/run.sh python3 run_bgr.py ...).
Writes decks, logs and raw data to $G1_RESULTS_ROOT/r1_bgr/<run-id>/ and a summary JSON to
results/<run-id>.json (tracked). Suites: size, temp, mc, startup, psrr, op; stb and noise (T7 follow-up).
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


# ---------------------------------------------------------------------------------------------------------------
# Revision-r1 follow-up (track T7): suites `stb` (loop gain, supply-step transient, toy-loop method check) and
# `noise`. Loop-gain method: Tian double injection (Wiedmann form), validated on the toy loop of tb_stb_toy.cir
# (same method as r1_afe/sim/tb_afe_stb.cir). Probes are inserted into a copy of the frozen netlist; the netlist
# of record is not changed.
# ---------------------------------------------------------------------------------------------------------------
NETLIST_SHA = "c19a7425d605906962724fdda21add8ae3926dc9a097c6f835a16f05f92c0c26"

# loop cuts: (name, net, instance-name prefixes whose pin `pin` (0-based token of the instance line) is moved to the receiver side)
CUTS = [
    ("pbias", "pbias", ("XMP",), 2, "PMOS mirror gate line (core loop through the 1:8 / 1:1 mirror)"),
    ("pcasc", "pcasc", ("XMC",), 2, "PMOS cascode gate line (RB / MNC2 cascode-bias loop)"),
    ("vb2", "vb2", ("XMNC",), 2, "NMOS cascode gate line (MP5/MC5/RX/QD1/QD2 bias into the Q1/Q2 cascodes)"),
    ("vbe", "vbe", ("XQ2_",), 2, "Q2 base line (PTAT loop through V_BE and the DVBE pair)"),
    ("kick", "kick", ("XMKFB",), 2, "start-up detector: kick gate of MKFB (det inverter and MPS current source)"),
]
# MPS (detector current source, gate pbias) and MP1_x ... are all caught by the "XMP" prefix; XMPS/XMPI are excluded by name below
CUT_EXCLUDE = {"pbias": ("XMPI",)}

PORTS = ("vdd", "vss", "vref", "iptat", "pbias", "pcasc", "vbe", "dvbe")   # subckt ports are top-level nets
STB_CORNERS = [("tt27_3v3", "hbt_typ", "mos_tt", "res_typ", 27, 3.3),
               ("ss125_3v0", "hbt_wcs", "mos_ss", "res_wcs", 125, 3.0),
               ("ffm40_3v6", "hbt_bcs", "mos_ff", "res_bcs", -40, 3.6)] + \
              [("tcfail_%s_%gV" % (m, v), "hbt_wcs", m, "res_bcs", 27, v) for m in ("mos_tt", "mos_ss", "mos_ff") for v in (3.0, 3.3, 3.6)]

def probe_netlist(text, cutname):
    """Return the netlist text with the cut inserted: the driver keeps net `x`; the receiver pins move to `x_rx`;
    Vp x x_rx (ac vinj), Ip 0 x (ac iinj) are added after the .ends line (inside the subckt, before .ends)."""
    for name, net, prefixes, pin, _ in CUTS:
        if name != cutname:
            continue
        out, moved = [], []
        for l in text.splitlines():
            t = l.split()
            if t and t[0].startswith(prefixes) and not t[0].startswith(CUT_EXCLUDE.get(name, ())) and len(t) > pin and t[pin] == net:
                t[pin] = net + "_rx"
                moved.append(t[0])
                l = " ".join(t)
            if l.strip() == ".ends":
                out.append("Vprobe %s %s_rx dc 0 ac {vinj}" % (net, net))
                out.append("Iprobe 0 %s dc 0 ac {iinj}" % net)
            out.append(l)
        return "\n".join(out) + "\n", moved
    raise KeyError(cutname)

CTL_STB = """.control
set filetype=ascii
set wr_singlescale
set wr_vecnames
op
print v(vref)
ac dec 20 0.1 10g
alterparam vinj=0
alterparam iinj=1
reset
ac dec 20 0.1 10g
let v1 = ac1.v(@@NET@@)
let i1 = ac1.i(v.xbgr.vprobe)
let v2 = ac2.v(@@NET@@)
let i2 = ac2.i(v.xbgr.vprobe)
let tl = -1/(1-1/(2*(i1*v2-v1*i2)+v1+i2))
let tre = real(tl)
let tim = imag(tl)
wrdata @@OUT@@.dat tre tim
.endc
"""

def curve_margins(f, re, im):
    """Margins of a return ratio T (instability at T = -1; stabilising feedback has T > 0 at DC). The phase theta is
    unwrapped from f_min. PM = angular distance of theta at |T| = 1 from the -1 point (minimum over crossings);
    GM = -|T| (dB) where theta is an odd multiple of 180 deg (minimum over crossings). A positive-feedback loop at DC
    (T(0) real negative, |T(0)| < 1) has theta = 180 deg at f_min: its GM is then -|T(0)| (dB) and it is listed as such."""
    n = len(f)
    mag = [math.hypot(a, b) for a, b in zip(re, im)]
    gdb = [20 * math.log10(max(m, 1e-30)) for m in mag]
    th, prev = [], None
    for a, b in zip(re, im):
        x = math.degrees(math.atan2(b, a))
        if prev is not None:
            while x - prev > 180: x -= 360
            while x - prev < -180: x += 360
        th.append(x); prev = x
    dc_pos = abs(abs(th[0]) - 180) < 5
    if dc_pos and th[0] < 0:
        th = [x + 360 for x in th]          # start at +180 so the "departure" below is monotone in sign
    r = dict(t_dc_db=round(gdb[0], 2), phase_dc_deg=round(th[0], 1), dc_feedback="positive" if dc_pos else "negative",
             gain_max_db=round(max(gdb), 2), f_gain_max=f[max(range(n), key=lambda i: gdb[i])])
    d1 = [math.hypot(1 + a, b) for a, b in zip(re, im)]
    k = min(range(n), key=lambda i: d1[i])
    r["min_1pT"] = round(d1[k], 4); r["f_min_1pT"] = f[k]
    wrap = lambda x: (x + 180) % 360 - 180
    pm = fu = None
    for i in range(1, n):
        if gdb[i - 1] >= 0 > gdb[i]:
            a = gdb[i - 1] / (gdb[i - 1] - gdb[i])
            fx = f[i - 1] * (f[i] / f[i - 1]) ** a
            m = abs(wrap(th[i - 1] + a * (th[i] - th[i - 1]) + 180))
            if pm is None or m < pm:
                pm, fu = m, fx
    r["unity"] = pm is not None
    r["pm_deg"] = None if pm is None else round(pm, 2); r["f_unity"] = fu
    gm = f180 = None
    if dc_pos and gdb[0] < 0:
        gm, f180 = -gdb[0], f[0]
    started = not dc_pos
    for i in range(1, n):
        if not started and abs(th[i] - 180) > 5:
            started = True
        if not started:
            continue
        for L in range(-1260, 1261, 360):   # -1260 = -7 x 180: odd multiples of 180 deg
            lim = L
            if (th[i - 1] - lim) * (th[i] - lim) < 0 and abs(th[i - 1] - lim) > 1e-6:
                a = (th[i - 1] - lim) / (th[i - 1] - th[i])
                gx = gdb[i - 1] + a * (gdb[i] - gdb[i - 1])
                if gm is None or -gx < gm:
                    gm, f180 = -gx, f[i - 1] * (f[i] / f[i - 1]) ** a
    r["gm_db"] = None if gm is None else round(gm, 2); r["f_180"] = f180
    if pm is not None:
        icr = max([i for i in range(n) if f[i] <= fu] or [0])
        r["rhp_flag"] = (max(th[:icr + 1]) - th[0]) > 30.0     # phase rising > 30 deg above DC before unity (r1_afe check)
    else:
        r["rhp_flag"] = None
    r["th_min_deg"] = round(min(th), 1); r["th_max_deg"] = round(max(th), 1)
    return r

def read_cols(p):
    rows = [l.split() for l in open(p) if l.strip()]
    data = []
    for r in rows:
        try: data.append([float(x) for x in r])
        except ValueError: pass
    return [list(c) for c in zip(*data)]

CTL_TRAN_STEP = """.control
set filetype=ascii
set wr_singlescale
set wr_vecnames
option temp=@@TEMP@@
tran 20n 250u 0 50n
wrdata @@OUT@@.dat v(vref) v(vdd)
.endc
"""

def tran_metrics(t, v, vdd, t_step=5e-6, t_edge=100e-9):
    # baseline = vref just before the step; final = mean over the last 10 % of the record
    i0 = max(i for i in range(len(t)) if t[i] <= t_step)
    v0 = v[i0]
    nf = max(3, len(t) // 10)
    vf = sum(v[-nf:]) / nf
    drift = max(v[-nf:]) - min(v[-nf:])
    dev = [x - vf for x in v]
    tol = 0.01 * vf
    tset = None
    for i in range(len(t) - 1, -1, -1):
        if t[i] >= t_step and abs(dev[i]) > tol:
            tset = t[i] - (t_step + t_edge); break
    if tset is None: tset = 0.0
    def tlast(th):
        for i in range(len(t) - 1, -1, -1):
            if t[i] >= t_step and abs(dev[i]) > th:
                return (t[i] - (t_step + t_edge)) * 1e6
        return 0.0
    t_01 = tlast(0.001 * vf); t_100u = tlast(100e-6); t_10u = tlast(10e-6)
    k = max(range(len(t)), key=lambda i: abs(dev[i]) if t[i] >= t_step else 0)
    # extrema of the deviation after the step; hysteresis 10 % of the largest excursion (min 2 uV)
    post = [(t[i], dev[i]) for i in range(len(t)) if t[i] >= t_step]
    pk = max(abs(d) for _, d in post)
    hyst = max(0.1 * pk, 2e-6)
    exts, state, lastv = [], 0, post[0][1]
    hi = lo = post[0][1]
    for _, d in post:
        if state >= 0 and d > hi: hi = d
        if state <= 0 and d < lo: lo = d
        if d - lo > hyst and state <= 0:
            if state == -1 or state == 0: exts.append(("min", lo))
            state = 1; hi = d
        elif hi - d > hyst and state >= 0:
            exts.append(("max", hi)); state = -1; lo = d
    # number of excursions across the final value with amplitude above the hysteresis
    cross = 0; sgn = 0
    for _, d in post:
        if abs(d) > hyst:
            s = 1 if d > 0 else -1
            if sgn != 0 and s != sgn: cross += 1
            sgn = s
    # tail time constant: time for |dev| to fall below 10 % of its peak after the peak
    return dict(vref_before=v0, vref_final=vf, delta_mV=(vf - v0) * 1e3, peak_dev_mV=pk * 1e3, tail_drift_uV=drift * 1e6,
                t_settle_1pct_us=tset * 1e6, t_settle_0p1pct_us=t_01, t_settle_100uV_us=t_100u, t_settle_10uV_us=t_10u, t_peak_us=(t[k] - t_step) * 1e6, peak_sign=1 if dev[k] > 0 else -1, peak_dev_pct=100 * abs(dev[k]) / vf, sign_changes_beyond_hyst=cross, hyst_uV=hyst * 1e6,
                n_extrema=len(exts))

def stb_suite(runid, rundir):
    net_src = os.path.join(SCH, "r1_bgr.spice")
    net = os.path.join(rundir, "r1_bgr.spice")
    open(net, "w").write(open(net_src).read())
    sha_net = sha(net)
    assert sha_net == NETLIST_SHA, "netlist sha256 mismatch: %s" % sha_net
    text = open(net).read()
    summary = dict(netlist_sha256=sha_net)
    items, meta = [], []
    # toy-loop method check
    toy = open(os.path.join(HERE, "tb_stb_toy.cir")).read().replace("@@RAW@@", os.path.join(rundir, "toy"))
    open(os.path.join(rundir, "toy.cir"), "w").write(toy)
    items.append((os.path.join(rundir, "toy.cir"), os.path.join(rundir, "toy.log"))); meta.append(("toy",))
    # loop gain
    moved_all = {}
    for cname, h, m, r, t, v in STB_CORNERS:
        for cut in CUTS:
            ptxt, moved = probe_netlist(text, cut[0])
            moved_all[cut[0]] = moved
            sub = "%s__%s" % (cname, cut[0])
            pn = os.path.join(rundir, sub + ".spice"); open(pn, "w").write(ptxt)
            out = os.path.join(rundir, sub)
            ctl = CTL_STB.replace("@@NET@@", cut[1] if cut[1] in PORTS else "xbgr." + cut[1]).replace("@@OUT@@", out)
            dk = deck("stb", pn, h, m, r, v, ctl).replace(".global sub!", ".global sub!\n.param vinj=1 iinj=0\n.temp %g" % t)
            open(out + ".cir", "w").write(dk)
            items.append((out + ".cir", out + ".log")); meta.append(("stb", cname, cut[0], h, m, r, t, v, out))
    # supply-step transient
    for cname, h, m, r, t in (("tt27", "hbt_typ", "mos_tt", "res_typ", 27), ("ss125", "hbt_wcs", "mos_ss", "res_wcs", 125)):
        out = os.path.join(rundir, "step_" + cname)
        ctl = CTL_TRAN_STEP.replace("@@TEMP@@", str(t)).replace("@@OUT@@", out)
        dk = deck("step", net, h, m, r, 3.3, ctl, vddac="pwl(0 3.3 5u 3.3 5.1u 3.0 1 3.0)")
        open(out + ".cir", "w").write(dk)
        items.append((out + ".cir", out + ".log")); meta.append(("step", cname, h, m, r, t, out))
    res = run_all(items)
    rows, steps = [], []
    for mt, (path, rc, dt) in zip(meta, res):
        if mt[0] == "toy":
            for l in open(os.path.join(rundir, "toy.log")):
                if "TOYROW" in l: summary["toy"] = l.strip()
            continue
        if mt[0] == "stb":
            _, cname, cut, h, m, r, t, v, out = mt
            row = dict(case=cname, cut=cut, hbt=h, mos=m, res=r, temp=t, vdd=v, rc=rc, seconds=round(dt, 1))
            try:
                c = read_cols(out + ".dat"); f, re, im = c[0], c[1], c[2]
                # sanity: DC operating point
                row.update(curve_margins(f, re, im))
                row["pass_pm60"] = True if row["pm_deg"] is None else row["pm_deg"] >= 60
                row["pass_gm10"] = True if row["gm_db"] is None else row["gm_db"] >= 10
                for l in open(out + ".log"):
                    if l.strip().startswith("v(vref)"): row["vref_op"] = float(l.split("=")[1]); break
            except Exception as e:
                row["error"] = str(e)
            rows.append(row)
        else:
            _, cname, h, m, r, t, out = mt
            row = dict(case=cname, hbt=h, mos=m, res=r, temp=t, rc=rc)
            try:
                c = read_cols(out + ".dat"); row.update(tran_metrics(c[0], c[1], c[2]))
            except Exception as e:
                row["error"] = str(e)
            steps.append(row)
    summary["rows"] = rows; summary["steps"] = steps; summary["moved_pins"] = {k: len(v) for k, v in moved_all.items()}
    return summary

CTL_NOISE = """.control
set filetype=ascii
set wr_singlescale
set wr_vecnames
option temp=@@TEMP@@
op
print v(vref)
noise v(vref) vdd dec 100 10 10meg
setplot noise2
print onoise_total
setplot noise1
let nd = onoise_spectrum
wrdata @@OUT@@.dat nd
.endc
"""

def noise_suite(runid, rundir):
    net = os.path.join(rundir, "r1_bgr.spice")
    open(net, "w").write(open(os.path.join(SCH, "r1_bgr.spice")).read())
    sha_net = sha(net)
    assert sha_net == NETLIST_SHA, "netlist sha256 mismatch: %s" % sha_net
    cs = [("tt27", "hbt_typ", "mos_tt", "res_typ", 27, 3.3), ("ss125", "hbt_wcs", "mos_ss", "res_wcs", 125, 3.0)]
    items = []
    for name, h, m, r, t, v in cs:
        out = os.path.join(rundir, "noise_" + name)
        open(out + ".cir", "w").write(deck("noise", net, h, m, r, v, CTL_NOISE.replace("@@TEMP@@", str(t)).replace("@@OUT@@", out), vddac="ac 1"))
        items.append((out + ".cir", out + ".log"))
    res = run_all(items)
    rows = []
    for (name, h, m, r, t, v), (path, rc, dt) in zip(cs, res):
        row = dict(case=name, hbt=h, mos=m, res=r, temp=t, vdd=v, rc=rc)
        out = os.path.join(rundir, "noise_" + name)
        try:
            for l in open(out + ".log"):
                if l.strip().startswith("onoise_total"): row["onoise_total_10_10M_uV_ngspice"] = float(l.split("=")[1]) * 1e6
                if l.strip().startswith("v(vref)"): row["vref"] = float(l.split("=")[1])
            c = read_cols(out + ".dat"); f, nd = c[0], c[1]
            row.update(noise_reduce(f, nd))
        except Exception as e:
            row["error"] = str(e)
        rows.append(row)
    return dict(netlist_sha256=sha_net, rows=rows)

def integ(f, s2, lo, hi):
    """integral of a PSD (V^2/Hz, piecewise power law between log-spaced points) from lo to hi."""
    tot = 0.0
    for i in range(1, len(f)):
        a, b = max(f[i - 1], lo), min(f[i], hi)
        if b <= a: continue
        s1, s2_ = s2[i - 1], s2[i]
        # interpolate in log-log
        k = math.log(s2_ / s1) / math.log(f[i] / f[i - 1]) if s1 > 0 and s2_ > 0 else 0.0
        sa = s1 * (a / f[i - 1]) ** k; sb = s1 * (b / f[i - 1]) ** k
        if abs(k + 1) < 1e-9: tot += sa * a * math.log(b / a)
        else: tot += (sb * b - sa * a) / (k + 1)
    return tot

def noise_reduce(f, nd):
    s2 = [x * x for x in nd]
    r = dict(n_points=len(f), f_min=f[0], f_max=f[-1])
    r["rms_10_100k_uV"] = math.sqrt(integ(f, s2, 10, 1e5)) * 1e6
    r["rms_10_10M_uV"] = math.sqrt(integ(f, s2, 10, 1e7)) * 1e6
    r["rms_10_1k_uV"] = math.sqrt(integ(f, s2, 10, 1e3)) * 1e6
    r["rms_1k_100k_uV"] = math.sqrt(integ(f, s2, 1e3, 1e5)) * 1e6
    r["density_nV_rtHz"] = {("%g" % x): round(nd[min(range(len(f)), key=lambda i: abs(f[i] - x))] * 1e9, 3) for x in (10, 100, 1e3, 1e4, 1e5, 1e6, 1e7)}
    # white floor: density at 200 kHz (flat plateau of the spectrum, below the pole formed by the vref output resistance
    # and the 1 pF load); 1/f corner: frequency where the density squared falls to 2 x the floor squared
    kf = min(range(len(f)), key=lambda i: abs(f[i] - 2e5)); fl = s2[kf]
    r["floor_nV_rtHz"] = math.sqrt(fl) * 1e9
    corner = None
    for i in range(1, kf + 1):
        if s2[i - 1] >= 2 * fl > s2[i]:
            a = (math.log(s2[i - 1]) - math.log(2 * fl)) / (math.log(s2[i - 1]) - math.log(s2[i]))
            corner = f[i - 1] * (f[i] / f[i - 1]) ** a
    r["f_corner_1_over_f_Hz"] = corner
    # -3 dB frequency of the roll-off above the plateau
    pole = None
    for i in range(kf, len(f)):
        if s2[i] < 0.5 * fl:
            a = (math.log(s2[i - 1]) - math.log(0.5 * fl)) / (math.log(s2[i - 1]) - math.log(s2[i]))
            pole = f[i - 1] * (f[i] / f[i - 1]) ** a; break
    r["f_rolloff_3dB_Hz"] = pole
    # 1/f slope between 10 and 100 Hz
    i10 = min(range(len(f)), key=lambda i: abs(f[i] - 10)); i100 = min(range(len(f)), key=lambda i: abs(f[i] - 100))
    r["slope_10_100Hz_dec"] = math.log10(s2[i100] / s2[i10]) / math.log10(f[i100] / f[i10])
    # buffer estimate: PSD x first-order low pass at fb
    est = {}
    for fb in (1e5, 3e5, 1e6, 3e6, 1e7):
        sh = [x / (1 + (ff / fb) ** 2) for x, ff in zip(s2, f)]
        est["%g" % fb] = round(math.sqrt(integ(f, sh, 10, 1e7)) * 1e6, 2)
    r["rms_after_buffer_pole_uV"] = est
    # buffer pole at which the integrated noise reaches 110 uV (0.25 LSB of 12 bit, 0.9 V full scale)
    lo, hi = 1e3, 1e7
    for _ in range(60):
        mid = math.sqrt(lo * hi)
        sh = [x / (1 + (ff / mid) ** 2) for x, ff in zip(s2, f)]
        if math.sqrt(integ(f, sh, 10, 1e7)) * 1e6 > 110: hi = mid
        else: lo = mid
    r["fb_for_110uV_Hz"] = lo
    return r

def new_main():
    suite, runid = sys.argv[1], sys.argv[2]
    rundir = os.path.join(ROOT, "r1_bgr", runid)
    os.makedirs(rundir, exist_ok=False)
    t0 = time.time()
    summary = dict(run_id=runid, suite=suite, started=time.strftime("%Y-%m-%dT%H:%M:%S"))
    summary.update(stb_suite(runid, rundir) if suite == "stb" else noise_suite(runid, rundir))
    summary["wall_s"] = round(time.time() - t0, 1)
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    json.dump(summary, open(os.path.join(HERE, "results", runid + ".json"), "w"), indent=1)
    json.dump(summary, open(os.path.join(rundir, "summary.json"), "w"), indent=1)
    print(json.dumps({k: v for k, v in summary.items() if k != "rows"}, indent=0)[:3000])

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ("stb", "noise"):
        new_main()
    else:
        main()

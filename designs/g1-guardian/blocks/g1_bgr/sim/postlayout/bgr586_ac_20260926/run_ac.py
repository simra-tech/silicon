#!/usr/bin/env python3
"""BGR586 extraction (g1_bgr586_pex.spice) AC / PSRR / noise / start-up, 2026-09-26.

Netlists (same subckt name and pin order):
  pex = ../g1_bgr586_pex.spice (kpex 2.5D CC of bank.gds, sha256 01227a3d...)
  sch = ../../qualification/candidates/bgr_loop24_qref4_r253p465_hv06/...spice (586ffb58..., 329 Sep-19 caps)
  old = ../g1_bgr_pex.spice (Sep-19 bandgap C-PEX, 72417e07...; AC-only comparison)

Fixtures, all copied from existing decks with only the netlist / corner / supply changed:
  tian_*    ../../qualification/runs/bgr_local_stability_20260921_01/*_voltage.cir / *_current.cir
            (Tian two-injection probe on the PBIAS or PCASC gate fanout; 1 pF VREF, ideal 1 V IPTAT)
  psrrnoise ../../qualification/runs/bgr_noise_20260921_01/noise.cir, plus a second noise analysis 10 Hz-10 MHz
  su1ms     ../../qualification/runs/bgr_loop24q4_hv06_startup2_20260922_r3/typ_tt_typ_27_0.001.cir
            with the supply end value 3.3 V instead of 3.0 V (1 ms ramp, 3 ms window, uic, 1 pF VREF)
  pad10n    ../../system_checks_20260924/bgr_sys.py startup deck, 10 nF board C, stock sg13g2_IOPadAnalog,
            and the pad-less stand-in (variant nopad)

  python3 run_ac.py gen
  python3 run_ac.py run 116-123 [filter]   host: each deck via flow/launch_pinned.sh (1 CPU each)
  python3 run_ac.py analyze                -> summary.json
"""
import cmath, hashlib, json, math, os, re, subprocess, sys, threading, time, queue
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, *[".."] * 7))
DECKS = os.path.join(HERE, "decks")
LOGS = os.path.join(HERE, "logs")
OUT = os.path.join(os.environ.get("BULK", "${BULK}"), "bgr586_ac_20260926")
M = "/foss/pdks/ihp-sg13g2/libs.tech/ngspice/models"
NETS = {"pex": "../../g1_bgr586_pex.spice",
        "sch": "../../../qualification/candidates/bgr_loop24_qref4_r253p465_hv06/bgr_loop24_qref4_r253p465_hv06.spice",
        "old": "../../g1_bgr_pex.spice"}
# name: (hbt, mos, res, dio, temp, vdd)
CORNERS = {"tt27": ("typ", "tt", "typ", "tt", 27, 3.3), "ss125": ("wcs", "ss", "wcs", "ss", 125, 3.3),
           "ff-40": ("bcs", "ff", "bcs", "ff", -40, 3.3),
           # the two historical local-stability tuples (recorded 586 schematic values exist for them)
           "slowhist": ("wcs", "ss", "wcs", "ss", -40, 3.0), "fasthist": ("bcs", "ff", "bcs", "ff", 125, 3.6)}
MAIN = ["tt27", "ss125", "ff-40"]
OPT = ".option gmin=1e-15 abstol=1e-14 reltol=1e-5 vntol=1e-7"


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def head(title, net, c, vddline, include=None):
    h, m, r, _, t, _ = CORNERS[c]
    return [title, f".lib {M}/cornerHBT.lib hbt_{h}", f".lib {M}/cornerMOShv.lib mos_{m}",
            f".lib {M}/cornerRES.lib res_{r}", f".include {include or NETS[net]}", OPT, f".temp {t}",
            ".global sub!", "Vsub sub! 0 0", vddline, "Vr4 r4 0 0",
            "Xbgr vdd 0 r4 vref iptat pbias pcasc vbe dvbe g1_bgr", "Vload iptat 0 1", "Cload vref 0 1p"]


def probe_netlist(net, probe):
    """copy of the netlist with the gate pins on net `probe` moved to gate_probe (as run_586_required_ac.py)"""
    src = open(os.path.join(DECKS, NETS[net])).read()
    lines, changed = [], []
    for line in src.splitlines():
        f = line.split()
        if line.startswith("XM") and f[2] == probe:
            changed.append(f[0])
            f[2] = "gate_probe"
            line = " ".join(f)
        if line.lower().startswith(".ends"):
            lines += ["Vprobe gate_probe " + probe + " dc 0 ac {pv}", "Iprobe vss gate_probe dc 0 ac {pi}"]
        lines.append(line)
    name = f"probe_{net}_{probe}.spice"
    open(os.path.join(DECKS, name), "w").write("\n".join(lines) + "\n")
    return name, len(changed)


def w(name, L):
    open(os.path.join(DECKS, name + ".cir"), "w").write("\n".join(L) + "\n")
    return name


def jobs():
    J = []   # (name, kind, wall_s)
    for net in ("pex", "sch", "old"):
        for c in MAIN + (["slowhist", "fasthist"] if net != "old" else []):
            for p in ("pbias", "pcasc"):
                for inj in ("voltage", "current"):
                    J.append((f"tian_{net}_{p}_{c}_{inj}", "tian", 900))
        for c in MAIN:
            J.append((f"psrrnoise_{net}_{c}", "psrrnoise", 900))
    for net in ("pex", "sch"):
        for c in MAIN:
            J.append((f"su1ms_{net}_{c}", "su1ms", 7200))
    for c in MAIN:
        for v in ("pad", "nopad"):
            J.append((f"pad10n_{v}_pex_{c}", "pad10n", 10800))
    return J


def gen():
    os.makedirs(DECKS, exist_ok=True)
    open(os.path.join(DECKS, ".spiceinit"), "w").write(open(os.path.join(HERE, "../../.spiceinit")).read())
    counts = {}
    for net in NETS:
        for p in ("pbias", "pcasc"):
            counts[(net, p)] = probe_netlist(net, p)
    for name, kind, _ in jobs():
        if kind == "tian":
            _, net, p, c, inj = name.split("_")
            vdd = CORNERS[c][5]
            pv, pi = (1, 0) if inj == "voltage" else (0, 1)
            L = head("* BGR local stability diagnostic (Tian two-injection), " + name, net, c, f"Vdd vdd 0 {vdd}",
                     include=counts[(net, p)][0])
            L += [f".param pv={pv} pi={pi}", ".control", "set num_threads=1", "set numdgt=15", "set wr_singlescale",
                  "set wr_vecnames", "op", "print v(vref) v(pbias) v(pcasc)", "ac dec 100 1 1g",
                  "let ifout=-i(v.xbgr.vprobe)", "let ve=v(xbgr.gate_probe)",
                  f"wrdata {OUT}/{name}.dat real(ifout) imag(ifout) real(ve) imag(ve)", "echo RUN_END", "quit",
                  ".endc", ".end"]
            w(name, L)
        elif kind == "psrrnoise":
            _, net, c = name.split("_")
            L = head("* BGR standalone AC noise/PSRR, " + name, net, c, f"Vdd vdd 0 dc {CORNERS[c][5]} ac 1")
            L += [".control", "set num_threads=1", "set numdgt=15", "set wr_singlescale", "set wr_vecnames",
                  "op", "print v(vref) i(vload) i(vdd)",
                  "ac dec 50 .1 100Meg", "let rejection = -db(v(vref))", f"wrdata {OUT}/{name}_psrr.dat rejection",
                  "noise v(vref) Vdd dec 50 1 10Meg", "setplot noise1", f"wrdata {OUT}/{name}_noise.dat onoise_spectrum",
                  "setplot noise2", "echo NOISE_1HZ_10MHZ", "print onoise_total",
                  "noise v(vref) Vdd dec 50 10 10Meg", "setplot noise4", "echo NOISE_10HZ_10MHZ", "print onoise_total",
                  "echo RUN_END", "quit", ".endc", ".end"]
            w(name, L)
        elif kind == "su1ms":
            _, net, c = name.split("_")
            L = head("* BGR 1 ms start-up (3.3 V), " + name, net, c, "Vdd vdd 0 3.3")
            L += [".control", "set num_threads=1", "set numdgt=15", "set wr_singlescale", "set wr_vecnames",
                  "alter @vdd[pwl] = [ 0 0 0.001 3.3 0.003 3.3 ]", "tran 2e-06 0.003 uic",
                  f"wrdata {OUT}/{name}.dat v(vref) i(vload) i(vdd) v(pbias) v(pcasc)",
                  "op", "echo DCREF", "print v(vref) i(vload) i(vdd)", "echo RUN_END", "quit", ".endc", ".end"]
            w(name, L)
        elif kind == "pad10n":
            _, v, net, c = name.split("_")
            sys.path.insert(0, os.path.join(HERE, "../../system_checks_20260924"))
            os.environ.setdefault("BULK", "${BULK}")
            import bgr_sys
            bgr_sys.NETLIST, bgr_sys.DECKS, bgr_sys.OUT = NETS[net], DECKS, OUT
            bgr_sys.deck(name, c, "10nF", "startup", variant="nopad" if v == "nopad" else "")
            txt = open(os.path.join(DECKS, name + ".cir")).read().replace("echo SYS_END", "echo SYS_END\necho RUN_END")
            open(os.path.join(DECKS, name + ".cir"), "w").write(txt)
    json.dump({"netlists": {k: {"path": v, "sha256": sha(os.path.join(DECKS, v))} for k, v in NETS.items()},
               "probe_gate_pins": {f"{n}_{p}": v[1] for (n, p), v in counts.items()},
               "spiceinit_sha256": sha(os.path.join(DECKS, ".spiceinit"))},
              open(os.path.join(HERE, "inputs.json"), "w"), indent=1)


def done(name):
    p = os.path.join(LOGS, name + ".log")
    if not os.path.exists(p):
        return False
    txt = open(p, errors="replace").read()
    return "RUN_END" in txt and "simulation(s) aborted" not in txt and "Timestep too small" not in txt


STALL_S = 300


def run_one(cpu, name, wall):
    log = os.path.join(LOGS, name + ".log")
    for ext in ("", ".rc", ".pid"):
        if os.path.exists(log + ext):
            os.remove(log + ext)
    t0 = time.time()
    subprocess.check_call([os.path.join(REPO, "flow/launch_pinned.sh"), str(cpu), os.path.relpath(DECKS, REPO), str(wall),
                           log, "ngspice", "-b", name + ".cir"], env=dict(os.environ, G1_RESULTS_ROOT=os.environ["BULK"]),
                          stdout=subprocess.DEVNULL)
    last, since, stalled = None, time.time(), False
    pid = int(open(log + ".pid").read())
    while not os.path.exists(log + ".rc"):
        time.sleep(5)
        if not os.path.exists("/proc/%d" % pid) and not os.path.exists(log + ".rc"):
            # launch_pinned.sh runs under set -e: a nonzero exit ends its subshell before it writes <log>.rc
            open(log + ".rc", "w").write("nonzero (launch_pinned.sh wrote no rc)\n")
            break
        try:
            with open(log, "rb") as g:
                g.seek(max(0, os.path.getsize(log) - 300))
                tail = g.read().decode(errors="replace")
        except OSError:
            continue
        m = re.findall(r"Reference value :\s*([-+0-9.eE]+)", tail)
        cur = m[-1] if m else None
        if cur != last:
            last, since = cur, time.time()
        elif cur is not None and not stalled and time.time() - since > STALL_S:
            stalled = True   # simulated time did not advance for STALL_S: kill ngspice
            subprocess.call(["pkill", "-f", f"ngspice -b {name}.cir"])
    rc = open(log + ".rc").read().strip()
    json.dump({"rc": rc, "wall_s": round(time.time() - t0, 1), "cpu": cpu,
               "stall_killed_after_s": STALL_S if stalled else None}, open(os.path.join(LOGS, name + ".meta"), "w"))


def run(cpus, flt=None):
    os.makedirs(LOGS, exist_ok=True)
    q = queue.Queue()
    order = {"tian": 0, "psrrnoise": 1, "pad10n": 2, "su1ms": 3}
    for n, k, wall in sorted(jobs(), key=lambda j: order[j[1]]):
        if (flt is None or flt in n) and not done(n):
            q.put((n, k, wall))

    def worker(cpu):
        while True:
            try:
                n, k, wall = q.get_nowait()
            except queue.Empty:
                return
            run_one(cpu, n, wall)
            ok = done(n)
            print(time.strftime("%H:%M:%S"), cpu, n, "ok" if ok else "FAILED", flush=True)
            if not ok and k in ("pad10n", "su1ms") and not n.endswith("_gear"):
                txt = open(os.path.join(DECKS, n + ".cir")).read()
                txt = txt.replace(OPT, OPT + " method=gear").replace(f"{OUT}/{n}", f"{OUT}/{n}_gear")
                open(os.path.join(DECKS, n + "_gear.cir"), "w").write(txt)
                q.put((n + "_gear", k, wall))
    th = [threading.Thread(target=worker, args=(c,)) for c in cpus]
    [t.start() for t in th]
    [t.join() for t in th]


# ---------------------------------------------------------------- analysis
def loadtxt(p):
    import numpy as np
    return np.loadtxt(p, skiprows=1, ndmin=2)


def printed(log, key, after=None):
    txt = open(log, errors="replace").read()
    if after:
        i = txt.find(after)
        if i < 0:
            return None
        txt = txt[i:]
    m = re.search(rf"^{re.escape(key)}\s*=\s*([-+0-9.eE]+)", txt, re.M)
    return float(m.group(1)) if m else None


def meta(n):
    p = os.path.join(LOGS, n + ".meta")
    return json.load(open(p)) if os.path.exists(p) else {}


def errs(n):
    txt = open(os.path.join(LOGS, n + ".log"), errors="replace").read()
    return {"errors": [l for l in txt.splitlines() if re.search(r"(?i)^error|timestep too small|analysis aborted|no such vector|singular", l)][:5],
            "nan_warnings": len(re.findall(r"(?i)\bnan\b", txt))}


def tian(net, p, c):
    r0 = tian1(net, p, c, "")
    if r0["status"] != "completed" and os.path.exists(os.path.join(LOGS, f"tian_{net}_{p}_{c}_voltage_ns.log")):
        # retry with .nodeset from the unmodified netlist's op at the same corner (numerical aid; deck otherwise identical)
        r1 = tian1(net, p, c, "_ns")
        r1["first_attempt"] = {k: r0.get(k) for k in ("status", "wall_voltage_s", "wall_current_s")}
        r1["method"] = "nodeset retry (opdump_" + net + "_" + c + ")"
        return r1
    return r0


def tian1(net, p, c, sfx):
    import numpy as np
    base = f"tian_{net}_{p}_{c}"
    rec = {"status": "not run"}
    d = {}
    for inj in ("voltage", "current"):
        n = f"{base}_{inj}{sfx}"
        if not os.path.exists(os.path.join(LOGS, n + ".log")):
            return rec
        rec[f"wall_{inj}_s"] = meta(n).get("wall_s")
        e = errs(n)
        rec.setdefault("errors", []).extend(e["errors"])
        rec["nan_in_log"] = rec.get("nan_in_log", 0) + e["nan_warnings"]
        if not done(n) or not os.path.exists(os.path.join(OUT, n + ".dat")):
            rec["status"] = "failed"
            return rec
        x = loadtxt(os.path.join(OUT, n + ".dat"))
        if not np.isfinite(x).all() or x[-1, 0] < .999e9:
            rec["status"] = "failed (non-finite or truncated data)"
            return rec
        d[inj] = x
        rec["vref_op"] = printed(os.path.join(LOGS, n + ".log"), "v(vref)")
    pts, prev = [], None
    for vv, ii in zip(d["voltage"], d["current"]):
        A, B, C, D = complex(*ii[1:3]), complex(*vv[1:3]), complex(*ii[3:5]), complex(*vv[3:5])
        delta = A * D - B * C
        T = (2 * delta - A + D) / (1 + A - D - 2 * delta)
        ph = math.degrees(cmath.phase(T))
        if prev is not None:
            while ph - prev > 180: ph -= 360
            while ph - prev < -180: ph += 360
        prev = ph
        pts.append((vv[0], abs(T), ph, abs(1 + T), T))
    cross = []
    for a, b in zip(pts, pts[1:]):
        if a[1] >= 1 > b[1]:
            fr = -math.log(a[1]) / (math.log(b[1]) - math.log(a[1]))
            cross.append({"f_Hz": math.exp(math.log(a[0]) + fr * math.log(b[0] / a[0])), "pm_deg": 180 + a[2] + fr * (b[2] - a[2])})
    # gain margin: |T| where the unwrapped phase passes -180 deg
    gm = []
    for a, b in zip(pts, pts[1:]):
        if (a[2] + 180) * (b[2] + 180) < 0:
            gm.append({"f_Hz": a[0], "gm_dB": -20 * math.log10(a[1])})
    rec.update(status="completed", T_dc=[pts[0][4].real, pts[0][4].imag], T_dc_mag=pts[0][1],
               min_return_difference=min(q[3] for q in pts), f_min_return_difference=min(pts, key=lambda q: q[3])[0],
               max_T=max(q[1] for q in pts), unity_crossings=cross, phase_crossings_m180=gm)
    json.dump([{"f_Hz": q[0], "T_mag": q[1], "T_phase_unwrapped_deg": q[2], "abs_1_plus_T": q[3]} for q in pts],
              open(os.path.join(OUT, base + "_return_ratio.json"), "w"))
    return rec


def psrrnoise(net, c):
    import numpy as np
    n = f"psrrnoise_{net}_{c}"
    rec = {"status": "not run"}
    log = os.path.join(LOGS, n + ".log")
    if not os.path.exists(log):
        return rec
    rec.update(errs(n), wall_s=meta(n).get("wall_s"))
    if not done(n):
        rec["status"] = "failed"
        return rec
    ps = loadtxt(os.path.join(OUT, n + "_psrr.dat"))
    no = loadtxt(os.path.join(OUT, n + "_noise.dat"))
    if not (np.isfinite(ps).all() and np.isfinite(no).all()):
        rec["status"] = "failed (non-finite)"
        return rec
    f, rj = ps[:, 0], ps[:, 1]
    band = (f >= 10 * 0.999) & (f <= 1e8 * 1.001)
    rec.update(vref_op=printed(log, "v(vref)"),
               psrr_dB={str(k): float(np.interp(math.log10(k), np.log10(f), rj)) for k in (1, 10, 100, 1e3, 1e4, 1e5, 1e6, 1e7, 1e8)},
               psrr_min_10Hz_100MHz_dB=float(rj[band].min()), psrr_min_f_Hz=float(f[band][np.argmin(rj[band])]),
               noise_rms_1Hz_10MHz_V=printed(log, "onoise_total", "NOISE_1HZ_10MHZ"),
               noise_rms_10Hz_10MHz_V=printed(log, "onoise_total", "NOISE_10HZ_10MHZ"))
    fn, sn = no[:, 0], no[:, 1]
    rec["noise_density_V_rtHz"] = {str(k): float(10 ** np.interp(math.log10(k), np.log10(fn), np.log10(sn))) for k in (10, 1e3, 1e5, 1e6)}
    m = fn >= 10 * 0.999
    rec["noise_rms_10Hz_10MHz_trapz_check_V"] = float(np.sqrt(np.trapz(sn[m] ** 2, fn[m])))
    rec["status"] = "completed"
    return rec


def use_of(n):
    return n if done(n) else (n + "_gear" if done(n + "_gear") else None)


def stall(n):
    out = {}
    for m in (n, n + "_gear"):
        lp = os.path.join(LOGS, m + ".log")
        if os.path.exists(lp):
            tx = open(lp, errors="replace").read().replace("\r", "\n")
            last = re.findall(r"Reference value :\s*([-+0-9.eE]+)", tx)
            ab = re.findall(r"Timestep too small; time = ([-+0-9.eE]+), timestep = \S+: trouble with (?:node )?\"?([^\"\s]+)", tx)
            out["gear" if m.endswith("_gear") else "trap"] = (
                f"timestep too small at t={ab[0][0]} s ({ab[0][1]})" if ab else
                f"no progress past t={last[-1]} s" + (", killed by watchdog" if meta(m).get("stall_killed_after_s") else "")
                if last else "no output") + f"; wall {meta(m).get('wall_s')} s"
    return out


def settle(tt, v, ref):
    import numpy as np
    r = {}
    for lab, tol in (("1pct", .01), ("0p1pct", .001)):
        bad = np.nonzero(np.abs(v - ref) > tol * ref)[0]
        r[lab] = None if len(bad) and bad[-1] == len(v) - 1 else float(tt[bad[-1] + 1]) if len(bad) else 0.0
    return r


def su1ms(net, c):
    import numpy as np
    n = f"su1ms_{net}_{c}"
    rec = {"status": "not run"}
    if not os.path.exists(os.path.join(LOGS, n + ".log")):
        return rec
    u = use_of(n)
    if u is None:
        rec.update(status="not converged", stall=stall(n))
        return rec
    x = loadtxt(os.path.join(OUT, u + ".dat"))
    tt, v, il, idd = x[:, 0], x[:, 1], x[:, 2], x[:, 3]
    ref = printed(os.path.join(LOGS, u + ".log"), "v(vref)", "DCREF")
    s = settle(tt, v, ref)
    i093 = np.nonzero(v >= 0.93)[0]
    rec.update(status="completed", method="gear" if u.endswith("_gear") else "trap", wall_s=meta(u).get("wall_s"),
               finite=bool(np.isfinite(x).all()), t_end=float(tt[-1]), vref_dc=ref, vref_end=float(v[-1]),
               iptat_end_uA=float(il[-1] * 1e6), supply_end_uA=float(-idd[-1] * 1e6), t_vref_0p93_ms=float(tt[i093[0]] * 1e3) if len(i093) else None,
               t_settle_1pct_ms=None if s["1pct"] is None else s["1pct"] * 1e3,
               t_settle_0p1pct_ms=None if s["0p1pct"] is None else s["0p1pct"] * 1e3,
               vref_max=float(v.max()), overshoot_mV=float((v.max() - ref) * 1e3), **errs(u))
    return rec


def pad10n(v, c):
    import numpy as np
    n = f"pad10n_{v}_pex_{c}"
    rec = {"status": "not run"}
    if not os.path.exists(os.path.join(LOGS, n + ".log")):
        return rec
    u = use_of(n)
    ref = None
    if u is None:
        rec.update(status="not converged", stall=stall(n))
        if not done(n + "_noop"):
            return rec
        # stand-in without the .op (the .op stalls without nodeset; with nodeset the uic transient aborts at 1 ns);
        # settling reference = the converged nodeset .op printed in the base log
        rec["attempts"] = rec.pop("stall")
        u, ref = n + "_noop", printed(os.path.join(LOGS, n + ".log"), "v(vref)")
    x = loadtxt(os.path.join(OUT, u + ".dat"))
    tt, vref, vpad = x[:, 0], x[:, 1], x[:, 2]
    ref = ref if ref is not None else printed(os.path.join(LOGS, u + ".log"), "v(vref)")
    s, sp = settle(tt, vref, ref), settle(tt, vpad, ref)
    tail = tt > tt[-1] * 0.8
    rec.update(status="completed", method="gear" if u.endswith("_gear") else "trap" + (", no .op (noop)" if u.endswith("_noop") else ""),
               deck_run=u, wall_s=meta(u).get("wall_s"), finite=bool(np.isfinite(x).all()), t_end=float(tt[-1]), vref_op=ref,
               t_settle_1pct_ms=None if s["1pct"] is None else s["1pct"] * 1e3,
               t_settle_0p1pct_ms=None if s["0p1pct"] is None else s["0p1pct"] * 1e3,
               pad_t_settle_1pct_ms=None if sp["1pct"] is None else sp["1pct"] * 1e3,
               overshoot_mV=float((vref.max() - ref) * 1e3), vref_pp_last20pct_uV=float(np.ptp(vref[tail]) * 1e6), **errs(u))
    return rec


def analyze():
    res = {"tian": {}, "psrrnoise": {}, "su1ms": {}, "pad10n": {}}
    for net in NETS:
        for c in CORNERS:
            for p in ("pbias", "pcasc"):
                res["tian"][f"{net}_{p}_{c}"] = tian(net, p, c)
            if c in MAIN:
                res["psrrnoise"][f"{net}_{c}"] = psrrnoise(net, c)
                if net != "old":
                    res["su1ms"][f"{net}_{c}"] = su1ms(net, c)
    for c in MAIN:
        for v in ("pad", "nopad"):
            res["pad10n"][f"{v}_pex_{c}"] = pad10n(v, c)
    json.dump(res, open(os.path.join(HERE, "summary.json"), "w"), indent=1)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "gen":
        gen()
    elif cmd == "run":
        a, b = sys.argv[2].split("-")
        run(list(range(int(a), int(b) + 1)), sys.argv[3] if len(sys.argv) > 3 else None)
    elif cmd == "analyze":
        analyze()

#!/usr/bin/env python3
"""G1_BGR system check 2026-09-24: post-layout BGR driving the VREF pad (sg13g2_IOPadAnalog) with board C.

Deck structure follows ../tb_g1_bgr.spice.tmpl (same .lib sections, options, Vload iptat=1.0 V termination,
kpex CC netlist as in ../postlayout/run_postlayout.py). Additions: stock sg13g2_IOPadAnalog (padres = core
side, pad = pin), 613.34 ohm VREF route (whole-tree series estimate from
review/audits/VREF_PAD_LOADING_20260922.md), internal load 100 kohm in series with 2 pF on vref, board C
with 1 ohm ESR on the pin. The testbench's own 1 pF Cload is replaced by that internal load.

  python3 bgr_sys.py gen                 write decks/ (host or container)
  python3 bgr_sys.py run [--cpus 50-57]  host: run every deck through flow/run.sh pinned, one CPU each;
                                         a deck that does not reach SYS_END is re-run once with method=gear
  python3 bgr_sys.py analyze             parse waveforms -> summary.json
Bulk outputs (waveforms, ngspice logs): ${BULK}/blockchecks-20260924/bgr/
"""
import json, os, re, subprocess, sys, threading, queue, time
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, *[".."] * 6))
# BGR586=1 selects the netlist on the chip (bgr_loop24_qref4_r253p465_hv06, SHA-256 586ffb58...); decks in bgr586/decks
NET586 = os.environ.get("BGR586") == "1"
SUB = os.path.join(HERE, "bgr586") if NET586 else HERE
DECKS = os.path.join(SUB, "decks")
OUT = os.environ["BULK"] + "/blockchecks-20260924/" + ("bgr586" if NET586 else "bgr")
NETLIST = ("../../../qualification/candidates/bgr_loop24_qref4_r253p465_hv06/bgr_loop24_qref4_r253p465_hv06.spice"
           if NET586 else "../../postlayout/g1_bgr_pex.spice")
M = "/foss/pdks/ihp-sg13g2/libs.tech/ngspice/models"
CORNERS = {  # name: (hbt, mos, res, dio, temp)
    "tt27": ("hbt_typ", "mos_tt", "res_typ", "dio_tt", 27),
    "ss125": ("hbt_wcs", "mos_ss", "res_wcs", "dio_ss", 125),
    "ff-40": ("hbt_bcs", "mos_ff", "res_bcs", "dio_ff", -40),
}
CAPS = {"0nF": None, "10nF": "10n", "100nF": "100n"}
# (tstep, tend, tmax) per test and board capacitance
TIMING = {
    ("startup", "0nF"): ("10n", "1m", "20n"), ("startup", "10nF"): ("100n", "15m", "500n"),
    ("startup", "100nF"): ("1u", "100m", "2u"),
    ("vstep", "0nF"): ("1n", "150u", "5n"), ("vstep", "10nF"): ("20n", "8.1m", "200n"),
    ("vstep", "100nF"): ("200n", "60.1m", "1u"),
}
TIMING.update({("istep", c): v for (k, c), v in list(TIMING.items()) if k == "vstep"})
T0 = {"0nF": "50u", "10nF": "100u", "100nF": "100u"}


def deck(name, corner, cap, test, gear=False, shunt=False, variant=""):
    """variant (diagnostics of stalled startups): 'rampload' = IPTAT 1.0 V termination ramped 0->1.0 V with the
    supply instead of an ideal 1.0 V from t=0; 'nopad' = sg13g2_IOPadAnalog removed (board C via ESR straight on
    padres); 'tend=<t>' = stop the transient early to capture the waveform before a stall"""
    hbt, mos, res, dio, temp = CORNERS[corner]
    tstep, tend, tmax = TIMING[(test, cap)]
    for v in variant.split(","):
        if v.startswith("tend="):
            tend = v[5:]
    extra = " ".join(v[4:] for v in variant.split(",") if v.startswith("opt:"))
    t0 = T0[cap]
    L = [f"* G1_BGR SYSTEM CHECK {test}{(' variant ' + variant) if variant else ''}: post-layout BGR + VREF pad, board C={cap}, {corner} ({hbt} {mos} {res} {dio}) T={temp} C",
         f".lib {M}/cornerHBT.lib {hbt}", f".lib {M}/cornerMOShv.lib {mos}", f".lib {M}/cornerRES.lib {res}",
         f".lib {M}/cornerMOSlv.lib {mos}", f".lib {M}/cornerCAP.lib cap_typ", f".lib {M}/cornerDIO.lib {dio}",
         f".include {NETLIST}",
         ".include /foss/pdks/ihp-sg13g2/libs.ref/sg13g2_io/spice/sg13g2_io.spi",
         ".option gmin=1e-15 abstol=1e-14 reltol=1e-5 vntol=1e-7" + (" method=gear" if gear else "") + (" " + extra if extra else ""),
         f".temp {temp}", ".global sub!", "Vsub sub! 0 dc 0"]
    if test == "startup":
        L += ["Vdd vdd 0 dc 3.3 pwl(0 0 10u 3.3)", "Vdd12 vdd12 0 dc 1.2 pwl(0 0 10u 1.2)"]
    else:
        L += ["Vdd vdd 0 dc 3.3", "Vdd12 vdd12 0 dc 1.2"]
    L += ["Vr4 r4 0 dc 0", "Xbgr vdd 0 r4 vref iptat pbias pcasc vbe dvbe g1_bgr",
          "* PTAT output leg sinks into a 1.0 V node (as ../tb_g1_bgr.spice.tmpl)",
          "Vload iptat 0 dc 1.0 pwl(0 0 10u 1.0)" if "rampload" in variant else "Vload iptat 0 dc 1.0",
          "* representative internal load: 100 kohm in series with 2 pF", "Rint vref nint 100k", "Cint nint 0 2p"]
    if shunt:
        L += ["* variant: 100 kohm DC shunt to ground on vref", "Rshunt vref 0 100k"]
    L += ["* VREF route to the pad ring (whole-tree series estimate) and stock analog pad",
          "Rroute vref padres 613.3425"]
    if "nopad" in variant:
        L += ["* variant nopad: pad cell removed, pin node shorted to padres", "Rnopad padres pad 1m"]
    elif "padsec" in variant or "padpri" in variant:
        # split copy of the stock sg13g2_IOPadAnalog body (instances verbatim from sg13g2_io.spi, PDK file untouched)
        sec = "padsec" in variant
        L += [f"* variant {'padsec: only the secondary protection' if sec else 'padpri: only primary clamps and diodes'} "
              "of sg13g2_IOPadAnalog; the other part replaced by a 1 mohm short pad-padres" if not sec else
              "* variant padsec: only XI3 sg13g2_SecondaryProtection of sg13g2_IOPadAnalog",
              ".subckt padsplit pad padres vdd vss iovdd iovss"]
        if "padsecR" in variant:     # secondary protection resistor only (instance verbatim), diodes omitted
            L += ["XI3R pad padres sub! rppd R=586.899 l=2u w=1u", "XI3Rp iovss sub! ptap1 R=46.556"]
        elif "padsecD" in variant:   # secondary protection diodes only (instances verbatim), resistor replaced by 1 mohm
            L += ["RI3s pad padres 1m", "XI3D1 sub! padres dantenna l=3.1u w=640n m=1",
                  "XI3D0 padres iovdd dpantenna l=4.98u w=640n m=1", "XI3Rp iovss sub! ptap1 R=46.556"]
        L += [] if ("padsecR" in variant or "padsecD" in variant) else ["XI3 padres iovss pad iovdd sg13g2_SecondaryProtection"] if sec else \
             ["XI0 iovdd iovss pad sg13g2_Clamp_P20N0D", "XI5 iovss pad iovdd sg13g2_DCNDiode",
              "XI2 pad iovdd iovss sg13g2_DCPDiode", "XI4 iovss pad sg13g2_Clamp_N20N0D", "Rshort padres pad 1m"]
        L += ["XR0 vss sub! ptap1 R=22.579", "XR1 iovss sub! ptap1 R=214.8m", ".ends",
              "XP pad padres vdd12 0 vdd 0 padsplit"]
    else:
        L += ["XP pad padres vdd12 0 vdd 0 sg13g2_IOPadAnalog"]
    vinj = f"pwl(0 0 {t0} 0 {float(t0[:-1]) + 1}u 10m)" if test == "vstep" else "0"
    if CAPS[cap]:
        L += [f"* board capacitor on the pin, 1 ohm ESR; Vinj = 10 mV / 1 us step in series (vstep test)",
              "Resr pad nesr 1", f"Vinj nesr ncb {vinj}", f"Cboard ncb 0 {CAPS[cap]}"]
    elif test == "vstep":
        L += ["* pad open: 10 mV / 1 us step coupled through 10 pF (probe stand-in) and 1 ohm",
              "Resr pad nesr 1", f"Vinj nesr ncb {vinj}", "Cc ncb 0 10p"]
    if test == "istep":
        L += [f"* 10 nA current step into the pin", f"Iinj 0 pad pwl(0 0 {t0} 0 {float(t0[:-1]) + 1}u 10n)"]
    uic = " uic" if test == "startup" else ""
    L += [".control", "set wr_singlescale", "set wr_vecnames", "option numdgt=12", "op",
          "print v(vref) v(padres) v(pad) i(vload) i(vdd)",
          f"tran {tstep} {tend} 0 {tmax}{uic}",
          f"wrdata {OUT}/{name}.dat v(vref) v(pad) v(vdd)", "echo SYS_END", "quit 0", ".endc", ".end"]
    os.makedirs(DECKS, exist_ok=True)
    open(os.path.join(DECKS, name + ".cir"), "w").write("\n".join(L) + "\n")
    return name


DIAG = [("diag_startup_0nF_tt27_rampload", "tt27", "0nF", "rampload"),
        ("diag_startup_0nF_ss125_rampload", "ss125", "0nF", "rampload"),
        ("diag_startup_10nF_ss125_rampload", "ss125", "10nF", "rampload"),
        ("diag_startup_10nF_ss125_nopad", "ss125", "10nF", "nopad"),
        ("diag_startup_10nF_ss125_to210u", "ss125", "10nF", "tend=210u"),
        ("diag_startup_100nF_ss125_rampload", "ss125", "100nF", "rampload"),
        ("diag_startup_100nF_ss125_nopad", "ss125", "100nF", "nopad"),
        ("diag_startup_10nF_tt27_rampload", "tt27", "10nF", "rampload"),
        ("diag_startup_0nF_tt27_nopad", "tt27", "0nF", "nopad"),
        ("diag_startup_0nF_ss125_nopad", "ss125", "0nF", "nopad"),
        ("diag_startup_0nF_tt27_to2p9u", "tt27", "0nF", "tend=2.9u"),
        ("diag_startup_0nF_tt27_rshunt", "tt27", "0nF", "opt:rshunt=1e12"),
        ("diag_startup_10nF_ss125_rshunt", "ss125", "10nF", "opt:rshunt=1e12"),
        ("diag_startup_10nF_ss125_gearreltol4", "ss125", "10nF", "opt:method=gear reltol=1e-4"),
        ("diag_startup_0nF_tt27_klu", "tt27", "0nF", "opt:klu"),
        ("diag_startup_10nF_ss125_klu", "ss125", "10nF", "opt:klu"),
        ("diag_startup_0nF_tt27_gearmaxord2", "tt27", "0nF", "opt:method=gear maxord=2"),
        ("diag_startup_0nF_tt27_padsec", "tt27", "0nF", "padsec"),
        ("diag_startup_0nF_tt27_padpri", "tt27", "0nF", "padpri"),
        ("diag_startup_10nF_ss125_padsec", "ss125", "10nF", "padsec"),
        ("diag_startup_10nF_ss125_padpri", "ss125", "10nF", "padpri"),
        ("diag_startup_0nF_tt27_padsecR", "tt27", "0nF", "padsec,padsecR"),
        ("diag_startup_0nF_tt27_padsecD", "tt27", "0nF", "padsec,padsecD"),
        ("diag_startup_10nF_ss125_padsecR", "ss125", "10nF", "padsec,padsecR"),
        ("diag_startup_10nF_ss125_padsecD", "ss125", "10nF", "padsec,padsecD")]


def temp_deck(corner):
    """VREF (core and pin) at -40/27/125 C for one process corner, 3.3 V, stock pad open, internal load"""
    hbt, mos, res, dio, _ = CORNERS[corner]
    name = f"vreftemp_{corner[:2]}"
    L = [f"* G1_BGR SYSTEM CHECK vref(T): {hbt} {mos} {res} {dio}, stock pad, pin open",
         f".lib {M}/cornerHBT.lib {hbt}", f".lib {M}/cornerMOShv.lib {mos}", f".lib {M}/cornerRES.lib {res}",
         f".lib {M}/cornerMOSlv.lib {mos}", f".lib {M}/cornerCAP.lib cap_typ", f".lib {M}/cornerDIO.lib {dio}",
         f".include {NETLIST}", ".include /foss/pdks/ihp-sg13g2/libs.ref/sg13g2_io/spice/sg13g2_io.spi",
         ".option gmin=1e-15 abstol=1e-14 reltol=1e-5 vntol=1e-7", ".global sub!", "Vsub sub! 0 dc 0",
         "Vdd vdd 0 dc 3.3", "Vdd12 vdd12 0 dc 1.2", "Vr4 r4 0 dc 0",
         "Xbgr vdd 0 r4 vref iptat pbias pcasc vbe dvbe g1_bgr", "Vload iptat 0 dc 1.0",
         "Rint vref nint 100k", "Cint nint 0 2p", "Rroute vref padres 613.3425",
         "XP pad padres vdd12 0 vdd 0 sg13g2_IOPadAnalog", ".control", "option numdgt=12"]
    for t in (-40, 27, 125):
        L += [f"option temp={t}", "op", f"echo VREFTEMP {t}", "print v(vref) v(pad) i(vload)"]
    L += ["echo SYS_END", "quit 0", ".endc", ".end"]
    os.makedirs(DECKS, exist_ok=True)
    open(os.path.join(DECKS, name + ".cir"), "w").write("\n".join(L) + "\n")
    return name


def names():
    out = []
    if NET586:   # pad-less stand-in for every startup, run alongside the stock-pad deck
        for c in CORNERS:
            for cap in CAPS:
                out.append((f"startupnopad_{cap}_{c}", c, cap, "startup", "nopad"))
    for c in CORNERS:
        for cap in CAPS:
            for t in ("startup", "vstep", "istep"):
                out.append((f"{t}_{cap}_{c}", c, cap, t, False))
    out.append(("startup_10nF_tt27_shunt100k", "tt27", "10nF", "startup", True))
    return out


def gen():
    for n, c, cap, t, sh in names():
        deck(n, c, cap, t, shunt=sh is True, variant=sh if isinstance(sh, str) else "")
    open(os.path.join(DECKS, ".spiceinit"), "w").write(open(os.path.join(os.path.dirname(HERE), ".spiceinit")).read())


def ok(name):
    p = os.path.join(OUT, name + ".log")
    if not os.path.exists(p):
        return False
    txt = open(p, errors="replace").read()
    return "SYS_END" in txt and "simulation(s) aborted" not in txt


STALL_S = 300


def run_one(cpu, name, wall=5400):
    env = dict(os.environ, G1_CPUSET=str(cpu), G1_CPUS="1", G1_CONTAINER_ENGINE="podman",
               G1_WORKDIR=os.path.relpath(DECKS, REPO), G1_RESULTS_ROOT=os.environ["BULK"])
    t = time.time()
    lp = os.path.join(OUT, name + ".log")
    stalled = False
    with open(lp, "w") as f:
        pr = subprocess.Popen(["timeout", "--kill-after=10s", str(wall), os.path.join(REPO, "flow/run.sh"),
                               "ngspice", "-b", name + ".cir"], env=env, stdout=f, stderr=subprocess.STDOUT)
        last, since = None, time.time()
        while pr.poll() is None:
            time.sleep(10)
            # stall watchdog: the transient's "Reference value" (simulated time) unchanged for STALL_S -> kill ngspice
            try:
                with open(lp, "rb") as g:
                    g.seek(max(0, os.path.getsize(lp) - 200))
                    tail = g.read().decode(errors="replace")
            except OSError:
                continue
            m = re.findall(r"Reference value :\s*([-+0-9.eE]+)", tail)
            cur = m[-1] if m else None
            if cur != last:
                last, since = cur, time.time()
            elif cur is not None and time.time() - since > STALL_S:
                stalled = True
                subprocess.run(["pkill", "-f", f"ngspice -b {name}.cir"])
                since = time.time() + 1e9
        rc = pr.returncode
    open(os.path.join(OUT, name + ".meta"), "w").write(json.dumps({"rc": rc, "wall_s": round(time.time() - t, 1), "cpu": cpu,
                                                                   "stall_killed_after_s": STALL_S if stalled else None}))


def run(cpus, only=None):
    q = queue.Queue()
    for n, c, cap, t, sh in names():
        if (only is None or only in n) and not ("--skip-done" in sys.argv and ok(n)):
            q.put((n, c, cap, t, sh, False))

    def worker(cpu):
        while True:
            try:
                n, c, cap, t, sh, gear = q.get_nowait()
            except queue.Empty:
                return
            run_one(cpu, n)
            print(n, "ok" if ok(n) else "FAILED", flush=True)
            if not ok(n) and not gear:
                g = n + "_gear"
                deck(g, c, cap, t, gear=True, shunt=sh is True, variant=sh if isinstance(sh, str) else "")
                q.put((g, c, cap, t, sh, True))
    th = [threading.Thread(target=worker, args=(c,)) for c in cpus]
    [x.start() for x in th]
    [x.join() for x in th]


def load(name):
    import numpy as np
    return np.loadtxt(os.path.join(OUT, name + ".dat"), skiprows=1)


def opval(name, node):
    for line in open(os.path.join(OUT, name + ".log"), errors="replace"):
        m = re.match(rf"^{re.escape(node)}\s*=\s*([-+0-9.eE]+)", line.strip())
        if m:
            return float(m.group(1))


def extrema_count(t, r, thr):
    """number of alternating local extrema of r with |r| > thr (ringing half-cycles) and their times"""
    import numpy as np
    s = np.sign(np.where(np.abs(r) > thr, r, 0))
    idx = np.nonzero(s)[0]
    if len(idx) == 0:
        return 0, []
    flips = [i for a, i in zip(idx[:-1], idx[1:]) if s[a] != s[i]]
    return len(flips), [float(t[i]) for i in flips]


def analyze():
    import numpy as np
    res = {}
    todo = names() + ([] if NET586 else [(n, c, cap, "startup", False) for n, c, cap, v in DIAG if "tend=" not in v])
    for n, c, cap, t, sh in todo:
        rec = {"corner": c, "cap": cap, "test": t}
        use = n if ok(n) else (n + "_gear" if ok(n + "_gear") else None)
        if use is None:
            rec["status"] = "not converged"
            for m in (n, n + "_gear"):
                lp = os.path.join(OUT, m + ".log")
                if os.path.exists(lp):
                    tx = open(lp, errors="replace").read().replace("\r", "\n")
                    last = re.findall(r"Reference value :\s*([-+0-9.eE]+)", tx)
                    ab = re.findall(r"Timestep too small; time = ([-+0-9.eE]+).*?node \"([^\"]+)\"", tx)
                    rec["stall_" + ("gear" if m.endswith("_gear") else "trap")] = (
                        f"timestep too small at t={ab[0][0]} s (node {ab[0][1]})" if ab else
                        f"no progress past t={last[-1]} s, killed" if last else "no output")
            res[n] = rec
            continue
        rec["deck_run"] = use
        rec["method"] = "gear" if use.endswith("_gear") else "trap"
        meta = os.path.join(OUT, use + ".meta")
        if os.path.exists(meta):
            rec["wall_s"] = json.load(open(meta))["wall_s"]
        d = load(use)
        tt, vref, vpad = d[:, 0], d[:, 1], d[:, 2]
        vop = opval(use, "v(vref)")
        rec["vref_op"] = vop
        rec["vpad_op"] = opval(use, "v(pad)")
        if t == "startup":
            rec["vref_end"], rec["vpad_end"] = float(vref[-1]), float(vpad[-1])
            for lab, tol in (("1pct", 0.01), ("0p1pct", 0.001)):
                for node, v in (("vref", vref), ("pad", vpad)):
                    bad = np.nonzero(np.abs(v - vop) > tol * vop)[0]
                    rec[f"t_settle_{lab}_{node}"] = (None if len(bad) and bad[-1] == len(v) - 1 else
                                                     float(tt[bad[-1] + 1]) if len(bad) else 0.0)
            rec["vref_max"], rec["overshoot_mV"] = float(vref.max()), float((vref.max() - vop) * 1e3)
            tail = tt > tt[-1] * 0.8
            rec["vref_pp_last20pct_uV"] = float(np.ptp(vref[tail]) * 1e6)
            n_ext, _ = extrema_count(tt[tail], vref[tail] - vref[tail].mean(), 1e-6)
            rec["sign_flips_last20pct_gt1uV"] = n_ext
        else:
            t0 = float(T0[cap][:-1]) * 1e-6
            base = float(np.interp(t0, tt, vref))
            post = tt >= t0
            tp, r = tt[post] - t0, vref[post] - base
            rp = vpad[post] - float(np.interp(t0, tt, vpad))
            rec["vref_base"] = base
            ipk = int(np.argmax(np.abs(r)))
            rec["peak_dev_mV"], rec["t_peak_us"] = float(r[ipk] * 1e3), float(tp[ipk] * 1e6)
            rec["pad_peak_dev_mV"] = float(rp[np.argmax(np.abs(rp))] * 1e3)
            rec["final_dev_mV"] = float(r[-1] * 1e3)
            if t == "vstep":
                # recovery back to baseline: undershoot below 0 = ringing/overshoot through the baseline
                rec["undershoot_mV"] = float(-r[ipk:].min() * 1e3) if r[ipk] > 0 else float(r[ipk:].max() * 1e3)
                pk = abs(r[ipk])
                after = np.abs(r[ipk:])
                for lab, fr in (("1e", np.exp(-1)), ("10pct", 0.1), ("1pct", 0.01)):
                    below = np.nonzero(after <= fr * pk)[0]
                    rec[f"t_decay_{lab}_us"] = float((tp[ipk + below[0]] - tp[ipk]) * 1e6) if len(below) else None
                thr = max(0.001 * pk, 2e-6)
            else:
                fin = r[-1]
                rec["overshoot_pct_of_final"] = float((r.max() - fin) / fin * 100) if fin > 0 else None
                bad = np.nonzero(np.abs(r - fin) > 0.01 * abs(fin))[0]
                rec["t_settle_1pct_us"] = float(tp[bad[-1] + 1] * 1e6) if len(bad) and bad[-1] < len(r) - 1 else None
                thr = max(0.01 * abs(fin), 2e-6)
                r = r - fin
            n_ext, times = extrema_count(tp[ipk:], r[ipk:], thr)
            rec["zero_crossings_beyond_thr"] = n_ext
            rec["ring_threshold_uV"] = thr * 1e6
            if n_ext >= 2:
                rec["ring_freq_Hz"] = float((n_ext - 1) / (2 * (times[-1] - times[0])))
        rec["status"] = "completed"
        res[n] = rec
    json.dump(res, open(os.path.join(SUB, "summary.json"), "w"), indent=1)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "gen":
        gen()
    elif cmd == "run":
        a, b = (sys.argv[sys.argv.index("--cpus") + 1] if "--cpus" in sys.argv else "50-57").split("-")
        only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None
        run(list(range(int(a), int(b) + 1)), only)
    elif cmd == "vreftemp":
        cpus = [int(x) for x in sys.argv[2].split(",")]
        ns = [temp_deck(c) for c in CORNERS]
        th = [threading.Thread(target=run_one, args=(cp, n, 1800)) for cp, n in zip(cpus, ns)]
        [x.start() for x in th]
        [x.join() for x in th]
    elif cmd == "diag":
        cpus = [int(x) for x in sys.argv[2].split(",")]
        q = queue.Queue()
        for n, c, cap, v in DIAG:
            if len(sys.argv) < 4 or sys.argv[3] in n:
                deck(n, c, cap, "startup", variant=v)
                q.put(n)
        def w(cpu):
            while True:
                try:
                    n = q.get_nowait()
                except queue.Empty:
                    return
                run_one(cpu, n, wall=900)
                print(n, "ok" if ok(n) else "FAILED", flush=True)
        th = [threading.Thread(target=w, args=(c,)) for c in cpus]
        [x.start() for x in th]
        [x.join() for x in th]
    elif cmd == "analyze":
        analyze()

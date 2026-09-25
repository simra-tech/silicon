#!/usr/bin/env python3
"""G1_T2F system check 2026-09-24: comparator HBT bias with EN = 0 and start-up after a 100 us EN = 0 hold.

Deck structure follows ../tb_g1_t2f.spice.tmpl (same .lib sections, .option line incl. method=gear, Vload iptat=1.0 V,
Cout 50 fF on fout, PTAT mode) with both post-layout netlists: ../../../g1_bgr/sim/postlayout/g1_bgr_pex.spice and
../postlayout/g1_t2f_pex.spice. HBT instance map of the extracted T2F netlist (from LVS pairing, schematic name):
XQ42 = QA1 (ca1 vth tail1), XQ45 = QB1 (cb1 cap1 tail1), XQ44 = QA2 (ca2 vth tail2), XQ43 = QB2 (cb2 cap2 tail2),
XQ40/XQ41 dummies (all terminals vss).

  python3 t2f_sys.py gen | run [--cpus 50-57] [--only s] | analyze
Bulk outputs: ${BULK}/blockchecks-20260924/t2f/
"""
import json, os, re, subprocess, sys, threading, queue, time
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, *[".."] * 6))
DECKS = os.path.join(HERE, "decks")
OUT = os.environ["BULK"] + "/blockchecks-20260924/t2f"
M = "/foss/pdks/ihp-sg13g2/libs.tech/ngspice/models"
CORNERS = {"tt27": ("hbt_typ", "mos_tt", "res_typ", "cap_typ", 27),
           "ss125": ("hbt_wcs", "mos_ss", "res_wcs", "cap_typ", 125),
           "ff-40": ("hbt_bcs", "mos_ff", "res_bcs", "cap_typ", -40)}
HBTS = {"QA1": ("xq42", "ca1", "vth", "tail1"), "QB1": ("xq45", "cb1", "cap1", "tail1"),
        "QA2": ("xq44", "ca2", "vth", "tail2"), "QB2": ("xq43", "cb2", "cap2", "tail2"),
        "QDUM40": ("xq40", "0", "0", "0"), "QDUM41": ("xq41", "0", "0", "0")}
OPTS = {"gear": "gmin=1e-15 abstol=1e-13 reltol=1e-4 vntol=1e-6 method=gear",          # block tb options
        "tight": "gmin=1e-15 abstol=1e-13 reltol=1e-5 vntol=1e-6 method=gear"}         # vce-suite options
TEN = {"en100u": "100u", "en1u": "1u"}


def node(n):
    return "0" if n == "0" else f"xt2f.{n}"


def deck(name, corner, en, opts="gear"):
    hbt, mos, res, cap, temp = CORNERS[corner]
    ten = TEN[en]
    L = [f"* G1_T2F SYSTEM CHECK: post-layout BGR + post-layout T2F, EN=0 until {ten}, {corner} ({hbt} {mos} {res} {cap}) T={temp} C PTAT",
         f".lib {M}/cornerHBT.lib {hbt}", f".lib {M}/cornerMOShv.lib {mos}", f".lib {M}/cornerMOSlv.lib {mos}",
         f".lib {M}/cornerRES.lib {res}", f".lib {M}/cornerCAP.lib {cap}",
         ".include ../../../../g1_bgr/sim/postlayout/g1_bgr_pex.spice", ".include ../../postlayout/g1_t2f_pex.spice",
         f".option {OPTS[opts]}", f".temp {temp}", ".global sub!", "Vsub sub! 0 dc 0",
         "Vdd vdd 0 dc 3.3", "Vdd12 vdd12 0 dc 1.2", "Vr4 r4 0 dc 0",
         f"Ven en 0 pwl(0 0 {ten} 0 {float(ten[:-1]) + 0.01}u 3.3)", "Vmode mode 0 dc 0",
         "Xbgr vdd 0 r4 vref iptat pbias pcasc vbe dvbe g1_bgr", "Vload iptat 0 dc 1.0",
         "Xt2f vdd vdd12 0 pbias pcasc vref en mode fout g1_t2f",
         "* TEMP_OUT pad stand-in: ~50 fF of core wiring plus the IO cell input", "Cout fout 0 50f",
         ".control", "set wr_singlescale", "set wr_vecnames", "option numdgt=10", "op", "echo OP_BEGIN"]
    for q, (inst, c, b, e) in HBTS.items():
        L.append(f"print v({node(c)}) v({node(b)}) v({node(e)}) v(xt2f.{inst}.t) "
                 f"@q.xt2f.{inst}.qnpn13g2[ic] @q.xt2f.{inst}.qnpn13g2[ib] @q.xt2f.{inst}.qnpn13g2[ie]")
    L += ["print v(vref) v(pbias) v(pcasc) v(xt2f.nbias) v(xt2f.vcg) v(xt2f.oa1) v(xt2f.ob1) v(xt2f.oa2) v(xt2f.ob2) "
          "v(xt2f.isrc) v(xt2f.q) v(xt2f.qn) v(xt2f.d1g) v(xt2f.d2g) v(fout) i(vdd) i(vdd12)", "echo OP_END"]
    tend = float(ten[:-1]) + 100
    L += [f"tran 5n {tend}u 0 10n",
          f"wrdata {OUT}/{name}.dat v(fout) v(en) v(xt2f.vth) v(xt2f.cap1) v(xt2f.cap2) v(xt2f.tail2) v(xt2f.cb2) v(xt2f.ca2) v(vref)",
          "echo SYS_END", "quit 0", ".endc", ".end"]
    os.makedirs(DECKS, exist_ok=True)
    open(os.path.join(DECKS, name + ".cir"), "w").write("\n".join(L) + "\n")
    return name


def diag_deck(name, corner, variant):
    """op-only attribution decks for the 'temperature limiting function received NaN' message"""
    hbt, mos, res, cap, temp = CORNERS[corner]
    op = {"tt27": (2.3030183146, 1.7690614391, 1.0374504883)}.get(corner)
    L = [f"* G1_T2F SYSTEM CHECK diag {variant}: {corner} ({hbt} {mos} {res} {cap}) T={temp} C PTAT, op only",
         f".lib {M}/cornerHBT.lib {hbt}", f".lib {M}/cornerMOShv.lib {mos}", f".lib {M}/cornerMOSlv.lib {mos}",
         f".lib {M}/cornerRES.lib {res}", f".lib {M}/cornerCAP.lib {cap}",
         ".include ../../../../g1_bgr/sim/postlayout/g1_bgr_pex.spice", ".include ../../postlayout/g1_t2f_pex.spice",
         f".option {OPTS['gear']}", f".temp {temp}", ".global sub!", "Vsub sub! 0 dc 0",
         "Vdd vdd 0 dc 3.3", "Vdd12 vdd12 0 dc 1.2", "Vr4 r4 0 dc 0", "Vmode mode 0 dc 0",
         "Ven en 0 dc " + ("3.3" if "en1" in variant else "0")]
    if variant.startswith("bgr_only"):
        L += ["Xbgr vdd 0 r4 vref iptat pbias pcasc vbe dvbe g1_bgr", "Vload iptat 0 dc 1.0"]
    elif variant.startswith("t2f_idealbias"):
        L += [f"Vpb pbias 0 dc {op[0]}", f"Vpc pcasc 0 dc {op[1]}", f"Vvr vref 0 dc {op[2]}",
              "Xt2f vdd vdd12 0 pbias pcasc vref en mode fout g1_t2f", "Cout fout 0 50f"]
    else:
        L += ["Xbgr vdd 0 r4 vref iptat pbias pcasc vbe dvbe g1_bgr", "Vload iptat 0 dc 1.0",
              "Xt2f vdd vdd12 0 pbias pcasc vref en mode fout g1_t2f", "Cout fout 0 50f"]
    if variant.endswith("nodeset"):
        L += [".nodeset v(pbias)=2.3030 v(pcasc)=1.7691 v(vref)=1.0375 v(xt2f.vth)=1.0374 v(xt2f.tail1)=0.3171 "
              "v(xt2f.tail2)=0.3171 v(xt2f.ca1)=1.1565 v(xt2f.ca2)=1.1565 v(xt2f.cb1)=1.3312 v(xt2f.cb2)=1.3312 "
              "v(xt2f.nbias)=0.7045 v(xt2f.vcg)=2.2168 v(xt2f.oa1)=2.2963 v(xt2f.oa2)=2.2963 v(xt2f.ob1)=3.2952 "
              "v(xt2f.ob2)=3.2952 v(xt2f.cap1)=0 v(xt2f.cap2)=0"]
    L += [".control", "option numdgt=10", "op", "echo OP_BEGIN",
          "print v(xt2f.cap2) v(xt2f.tail2) v(xt2f.cb2) v(xt2f.vth) v(vref)", "echo OP_END", "echo SYS_END", "quit 0", ".endc", ".end"]
    os.makedirs(DECKS, exist_ok=True)
    open(os.path.join(DECKS, name + ".cir"), "w").write("\n".join(L) + "\n")


DIAG = [("diag_" + v + "_" + c, c, v) for c in ("tt27",) for v in
        ("bgr_only", "t2f_idealbias_en0", "t2f_idealbias_en1", "joint_en0", "joint_en1", "joint_en0_nodeset")] + \
       [("diag_" + v + "_" + c, c, v) for c in ("ss125", "ff-40") for v in ("bgr_only", "joint_en1")]


def names():
    return [(f"{en}_{c}", c, en) for c in CORNERS for en in TEN]


def gen():
    for n, c, en in names():
        deck(n, c, en)
    open(os.path.join(DECKS, ".spiceinit"), "w").write(open(os.path.join(HERE, "..", ".spiceinit")).read())


def ok(name):
    p = os.path.join(OUT, name + ".log")
    return os.path.exists(p) and "SYS_END" in open(p, errors="replace").read()


def run_one(cpu, name, wall=5400):
    env = dict(os.environ, G1_CPUSET=str(cpu), G1_CPUS="1", G1_CONTAINER_ENGINE="podman",
               G1_WORKDIR=os.path.relpath(DECKS, REPO), G1_RESULTS_ROOT=os.environ["BULK"])
    t = time.time()
    with open(os.path.join(OUT, name + ".log"), "w") as f:
        rc = subprocess.run(["timeout", "--kill-after=10s", str(wall), os.path.join(REPO, "flow/run.sh"),
                             "ngspice", "-b", name + ".cir"], env=env, stdout=f, stderr=subprocess.STDOUT).returncode
    open(os.path.join(OUT, name + ".meta"), "w").write(json.dumps({"rc": rc, "wall_s": round(time.time() - t, 1), "cpu": cpu}))


def run(cpus, only=None):
    q = queue.Queue()
    for n, c, en in names():
        if only is None or only in n:
            q.put((n, c, en, False))

    def worker(cpu):
        while True:
            try:
                n, c, en, retry = q.get_nowait()
            except queue.Empty:
                return
            run_one(cpu, n)
            print(n, "ok" if ok(n) else "FAILED", flush=True)
            if not ok(n) and not retry:
                g = n + "_tight"
                deck(g, c, en, opts="tight")
                q.put((g, c, en, True))
    th = [threading.Thread(target=worker, args=(c,)) for c in cpus]
    [x.start() for x in th]
    [x.join() for x in th]


def parse_op(log):
    txt = open(log, errors="replace").read()
    seg = txt[txt.find("OP_BEGIN"):txt.find("OP_END")]
    d = {}
    for line in seg.splitlines():
        m = re.match(r"^(\S+)\s*=\s*([-+0-9.eE]+|nan|-?inf)", line.strip())
        if m:
            d[m.group(1)] = float(m.group(2))
    pre = txt[:txt.find("OP_BEGIN")]
    warn = [l.strip() for l in pre.splitlines() if re.search(r"warning|nan|gmin|error|singular|trouble", l, re.I)
            and "level=warning" not in l]
    return d, warn


def analyze():
    import numpy as np
    res = {}
    for n, c, en in names():
        use = n if ok(n) else (n + "_tight" if ok(n + "_tight") else None)
        rec = {"corner": c, "en_rise": TEN[en]}
        if use is None:
            rec["status"] = "not converged"
            res[n] = rec
            continue
        rec["deck_run"] = use
        rec["wall_s"] = json.load(open(os.path.join(OUT, use + ".meta")))["wall_s"]
        op, warn = parse_op(os.path.join(OUT, use + ".log"))
        rec["op_warnings"] = warn[:20]
        rec["op_warning_count"] = len(warn)
        hb = {}
        for q, (inst, cn, bn, enode) in HBTS.items():
            g = lambda x: 0.0 if x == "0" else op.get(f"v(xt2f.{x})")
            vc, vb, ve = g(cn), g(bn), g(enode)
            hb[q] = {"VC": vc, "VB": vb, "VE": ve, "VBE": vb - ve, "VCE": vc - ve, "VBC": vb - vc,
                     "IC": op.get(f"@q.xt2f.{inst}.qnpn13g2[ic]"), "IB": op.get(f"@q.xt2f.{inst}.qnpn13g2[ib]"),
                     "IE": op.get(f"@q.xt2f.{inst}.qnpn13g2[ie]"), "dT_selfheat_K": op.get(f"v(xt2f.{inst}.t)")}
        rec["hbt_op_en0"] = hb
        rec["op_other"] = {k: v for k, v in op.items() if not k.startswith("@") and "xq4" not in k}
        d = np.loadtxt(os.path.join(OUT, use + ".dat"), skiprows=1)
        t, fout = d[:, 0], d[:, 1]
        ten = float(TEN[en][:-1]) * 1e-6
        rec["fout_edges_before_en"] = int(np.sum((fout[1:] > 0.6) & (fout[:-1] <= 0.6) & (t[1:] < ten)))
        i = np.nonzero((fout[1:] > 0.6) & (fout[:-1] <= 0.6))[0]
        tr = t[i] + (0.6 - fout[i]) / (fout[i + 1] - fout[i]) * (t[i + 1] - t[i])
        tr = tr[tr > ten]
        per = np.diff(tr)
        f = 1 / per
        late = tr[1:] > tr[-1] - 50e-6
        fin = float(np.mean(f[late]))
        rec["n_rising_edges"] = int(len(tr))
        rec["t_first_edge_after_en_us"] = float((tr[0] - ten) * 1e6)
        rec["f_final_MHz"] = fin / 1e6
        rec["f_final_spread_ppm"] = float(np.ptp(f[late]) / fin * 1e6)
        rec["f_first_period_MHz"] = float(f[0] / 1e6)
        for lab, tol in (("1pct", 0.01), ("0p1pct", 0.001)):
            bad = np.nonzero(np.abs(f - fin) > tol * fin)[0]
            rec[f"t_settle_{lab}_us"] = float((tr[bad[-1] + 1] - ten) * 1e6) if len(bad) else float((tr[1] - ten) * 1e6)
        vth = d[:, 3]
        rec["vth_at_en_V"] = float(np.interp(ten, t, vth))
        rec["vth_final_V"] = float(np.mean(vth[t > t[-1] - 50e-6]))
        rec["status"] = "completed"
        res[n] = rec
    json.dump(res, open(os.path.join(HERE, "summary.json"), "w"), indent=1)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "gen":
        gen()
    elif cmd == "run":
        spec = sys.argv[sys.argv.index("--cpus") + 1] if "--cpus" in sys.argv else "50-57"
        cpus = [int(x) for x in spec.split(",")] if "," in spec else list(range(int(spec.split("-")[0]), int(spec.split("-")[-1]) + 1))
        only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None
        run(cpus, only)
    elif cmd == "diag":
        spec = sys.argv[2]
        for n, c, v in DIAG:
            diag_deck(n, c, v)
        q = [n for n, c, v in DIAG]
        cpus = [int(x) for x in spec.split(",")]
        def w(cpu):
            while q:
                n = q.pop(0)
                run_one(cpu, n, wall=1800)
                print(n, open(os.path.join(OUT, n + ".log"), errors="replace").read().count("received NaN"), "NaN", flush=True)
        th = [threading.Thread(target=w, args=(c,)) for c in cpus]
        [x.start() for x in th]
        [x.join() for x in th]
    elif cmd == "analyze":
        analyze()

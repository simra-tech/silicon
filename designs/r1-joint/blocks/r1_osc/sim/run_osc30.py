#!/usr/bin/env python3
"""Runner for the R1_OSC decks (inside the pinned container, via flow/run.sh).

Usage (from the repository root):
  G1_CPUSET=100-102 G1_CPUS=3 G1_WORKDIR=designs/r1-joint/blocks/r1_osc \
  G1_RESULTS_ROOT=<bulk results root> flow/run.sh python3 sim/run_osc30.py SUITE RUN_ID [--jobs 3]

Suites (tb_osc30.cir unless noted):
  quick      tt/1.2/27 at the mid code 16
  trim32     all 32 codes at tt/1.2/27
  corners27  mid code at tt/ss/ff (with res/cap typ/wcs/bcs) x 1.08/1.2/1.32 V x -40/27/125 C
  reach      ss/1.08/125 and ff/1.32/-40, all 32 codes
  psrr       tb_osc30_psrr.cir: dc step and ripple cases
  startup    tb_osc30_startup.cir at tt/27, ss/1.08/125, ff/1.32/-40
  mc         tb_osc30_mc.cir, 50 mismatch samples (seed 1..50) at tt/1.2/27, mid code
  mcreach    tb_osc30_mc.cir, 50 mismatch samples at ss/1.08/125, code 0 (slow-corner reach)
  smoke, mcseed, probe, jitter: deck checks, seed check, tuning probes, transient-noise jitter
  cmpnoise   tb_osc30_cmpnoise.cir (.noise of one comparator at the threshold)

Expanded decks, logs and raw waveforms go to $G1_RESULTS_ROOT/r1_osc/RUN_ID/.
Summary (JSON + CSV) and run.json go to sim/runs/RUN_ID/ in the tree.
"""
import datetime
import hashlib
import json
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
BLOCK = os.path.dirname(HERE)
NETLIST = os.path.join(BLOCK, "schematic", "r1_osc.spice")
# --netlist <path>: run the decks on another netlist with the same subckt ports (post-layout netlists from
# layout/pex_build.py, which live in the results root); its sha256 and path go to run.json, it is not copied.
NETLIST_OF_RECORD = NETLIST
if "--netlist" in sys.argv:
    NETLIST = os.path.abspath(sys.argv[sys.argv.index("--netlist") + 1])
MOD = {"tt": ("mos_tt", "res_typ", "cap_typ"), "ss": ("mos_ss", "res_wcs", "cap_wcs"),
       "ff": ("mos_ff", "res_bcs", "cap_bcs")}
MID = 16
# PSRR cases: supply source and stop time; ripple and step amplitude 10 mV around 1.2 V
PSRR_CASES = {"step": ("pwl(0 1.2 1u 1.2 1.0001u 1.21 10u 1.21)", "2.2u"),
              "rip20k": ("sin(1.2 0.01 20k 0 0 0)", "13.2u"),
              "rip1M": ("sin(1.2 0.01 1Meg 0 0 0)", "4.2u")}


def ARG(name, default=""):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


def sha(p):
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def points(suite):
    P = []
    if suite == "quick":
        P.append(dict(deck="tb_osc30.cir", corner="tt", vdd=1.2, temp=27, code=MID))
    elif suite == "trim32":
        P += [dict(deck="tb_osc30.cir", corner="tt", vdd=1.2, temp=27, code=c) for c in range(32)]
    elif suite == "corners27":
        for c in ("tt", "ss", "ff"):
            for v in (1.08, 1.2, 1.32):
                for t in (-40, 27, 125):
                    P.append(dict(deck="tb_osc30.cir", corner=c, vdd=v, temp=t, code=int(ARG("--code", str(MID)))))
    elif suite == "reach":
        for (c, v, t) in (("ss", 1.08, 125), ("ff", 1.32, -40)):
            P += [dict(deck="tb_osc30.cir", corner=c, vdd=v, temp=t, code=k) for k in range(32)]
    elif suite == "psrr":
        for case in ("step", "rip20k", "rip1M"):
            P.append(dict(deck="tb_osc30_psrr.cir", corner="tt", vdd=1.2, temp=27, code=MID, case=case))
    elif suite == "startup":
        for (c, v, t) in (("tt", 1.2, 27), ("ss", 1.08, 125), ("ff", 1.32, -40)):
            P.append(dict(deck="tb_osc30_startup.cir", corner=c, vdd=v, temp=t, code=MID))
    elif suite == "mc":
        P += [dict(deck="tb_osc30_mc.cir", corner="tt", vdd=1.2, temp=27, code=MID, seed=s) for s in range(1, 51)]
    elif suite == "smoke":  # deck check: short versions of psrr step, startup, one mc seed, short jitter
        P.append(dict(deck="tb_osc30_psrr.cir", corner="tt", vdd=1.2, temp=27, code=MID, case="step"))
        P.append(dict(deck="tb_osc30_startup.cir", corner="tt", vdd=1.2, temp=27, code=MID))
        P.append(dict(deck="tb_osc30_mc.cir", corner="tt", vdd=1.2, temp=27, code=MID, seed=1))
        P.append(dict(deck="tb_osc30_mc.cir", corner="tt", vdd=1.2, temp=27, code=MID, seed=2))
        P.append(dict(deck="tb_osc30_mc.cir", corner="tt", vdd=1.2, temp=27, code=MID, seed=1, rep=1))
        P.append(dict(deck="tb_osc30_jitter.cir", corner="tt", vdd=1.2, temp=27, code=MID, case="noise"))
    elif suite == "mcreach":  # mismatch MC at the slow reach point: ss/1.08/125, code 0
        P += [dict(deck="tb_osc30_mc.cir", corner="ss", vdd=1.08, temp=125, code=0, seed=s_) for s_ in range(1, 51)]
    elif suite == "mcseed":  # check that the seed selects and reproduces the mismatch sample
        for s_, rep in ((1, 0), (2, 0), (1, 1)):
            d = dict(deck="tb_osc30_mc.cir", corner="tt", vdd=1.2, temp=27, code=MID, seed=s_)
            if rep:
                d["rep"] = rep
            P.append(d)
    elif suite == "cmpnoise":
        P.append(dict(deck="tb_osc30_cmpnoise.cir", corner="tt", vdd=1.2, temp=27, code=MID))
    elif suite == "jitter":
        for case in ARG("--cases", "noise ref").split():
            P.append(dict(deck="tb_osc30_jitter.cir", corner="tt", vdd=1.2, temp=27, code=int(ARG("--code", str(MID))),
                          case=case))
    elif suite == "probe":  # tuning probe: list of corner:vdd:temp:code from env R1OSC_PROBE
        for item in ARG("--probe").split():
            c, v, t, k = item.split(":")
            P.append(dict(deck="tb_osc30.cir", corner=c, vdd=float(v), temp=float(t), code=int(k)))
    else:
        raise SystemExit("unknown suite " + suite)
    return P


def tag(p):
    t = "%s_%s_%gV_%gC_c%02d" % (p["deck"][:-4], p["corner"], p["vdd"], p["temp"], p["code"])
    if "case" in p:
        t += "_" + p["case"]
    if "seed" in p:
        t += "_s%03d" % p["seed"]
    if "rep" in p:
        t += "_rep%d" % p["rep"]
    return t


def run_point(p, outdir):
    t = tag(p)
    mos, res, cap = MOD[p["corner"]]
    with open(os.path.join(HERE, p["deck"])) as f:
        txt = f.read()
    sub = {"VDD": "%g" % p["vdd"], "MOS": mos, "RES": res, "CAP": cap, "TEMP": "%g" % p["temp"],
           "NETLIST": NETLIST, "CASE": p.get("case", ""), "RAW": os.path.join(outdir, t + ".raw"),
           "SEED": str(p.get("seed", 0))}
    for i in range(5):
        sub["B%d" % i] = str((p["code"] >> i) & 1)
    if p["deck"] == "tb_osc30_psrr.cir":
        sub["VSRC"], sub["TSTOP"] = PSRR_CASES[p["case"]]
    with open(NETLIST_OF_RECORD) as f:
        hdr = f.read(2000)
    if p["deck"] == "tb_osc30_jitter.cir":
        sub.update(jitter_netlist(p, outdir, t))
    sub["LRBIAS"] = re.search(r"L_RBIAS=(\S+)", hdr).group(1)
    for k, v in sub.items():
        txt = txt.replace("@@%s@@" % k, v)
    if "seed" in p:  # mismatch sections; per-sample working dir with its own .spiceinit carrying the seed
        txt = (txt.replace("@@MOSMM@@", mos + "_mismatch").replace("@@RESMM@@", res + "_mismatch")
               .replace("@@CAPMM@@", cap + "_mismatch"))
    wd = os.path.join(outdir, "wd_" + t)
    os.makedirs(wd, exist_ok=True)
    with open(os.path.join(HERE, ".spiceinit")) as f:
        init = f.read()
    if "seed" in p:
        init += "set rndseed=%d\n" % p["seed"]
    with open(os.path.join(wd, ".spiceinit"), "w") as f:
        f.write(init)
    deck = os.path.join(outdir, t + ".cir")
    with open(deck, "w") as f:
        f.write(txt)
    log = os.path.join(outdir, t + ".log")
    t0 = datetime.datetime.now()
    with open(log, "w") as lf:
        rc = subprocess.call(["ngspice", "-b", deck], stdout=lf, stderr=subprocess.STDOUT, cwd=wd)
    dt = (datetime.datetime.now() - t0).total_seconds()
    r = dict(p, tag=t, rc=rc, wall_s=round(dt, 1))
    with open(log, errors="replace") as lf:
        for line in lf:
            m = re.match(r"^(OSC|PSRR|STARTUP|MC|NOISE|JIT)\s+(.*)$", line.strip())
            if m:
                for k, v in re.findall(r"(\w+)=\s*([-+0-9.eE]+)(?=\s|$)", m.group(2)):
                    try:
                        r[k] = float(v)
                    except ValueError:
                        r[k] = v
    if p["deck"] == "tb_osc30_psrr.cir" and rc == 0:
        r.update(psrr_post(sub["RAW"] + ".txt", p["case"]))
    if p["deck"] == "tb_osc30_jitter.cir" and rc == 0:
        r.update(jitter_post(sub["RAW"] + ".txt"))
    return r


def jitter_netlist(p, outdir, t):
    """Deck-local noisy copy of the netlist (see tb_osc30_jitter.cir)."""
    en = float(ARG("--en", "20e-9")) if p["case"] == "noise" else 0.0
    with open(NETLIST) as f:
        net = f.read()
    with open(NETLIST_OF_RECORD) as f:
        lr = float(re.search(r"L_R=([0-9.]+)u", f.read()).group(1))
    r = 70.0 + 260.0 * lr                  # rppd w = 1 um, typ (estimate, Ohm)
    i_n = (4 * 1.380649e-23 * 300.15 / r) ** 0.5 if p["case"] == "noise" else 0.0
    nt = 50e-12    # white to 10 GHz; 200 ps aborted with "timestep too small" at 25 ns (run r1a-jitter)
    bw = (1.0 / (2 * nt)) ** 0.5
    if "pex_build.py" in net[:300]:   # post-layout netlist: same sources on the extracted nodes
        return jitter_netlist_pex(net, p, outdir, t, en, i_n, nt, bw)
    if p["case"] == "noise":
        net = net.replace("XM1 d1 inp tail", "VNI inpn inp dc 0 trnoise(%g %g 0 0)\nXM1 d1 inpn tail" % (en * bw, nt))
        net = net.replace("XRA vdd va", "INRA vdd va dc 0 trnoise(%g %g 0 0)\nINRB vdd vb dc 0 trnoise(%g %g 0 0)\nXRA vdd va"
                          % (i_n * bw, nt, i_n * bw, nt))
    else:  # ref: zero-amplitude trnoise aborts ("timestep too small", r1b-jitter); plain 0 V / 0 A sources instead,
        # same maximum time step as the noise sample time
        net = net.replace("XM1 d1 inp tail", "VNI inpn inp dc 0\nXM1 d1 inpn tail")
        net = net.replace("XRA vdd va", "INRA vdd va dc 0\nINRB vdd vb dc 0\nXRA vdd va")
    fn = os.path.join(outdir, t + "_netlist.spice")
    with open(fn, "w") as f:
        f.write(net)
    return {"NETLIST": fn, "EN": "%g" % en, "IN": "%g" % i_n, "NT": "%g" % nt, "TMAX": "%g" % nt, "TSTOP": ARG("--tstop", "35u")}


def jitter_netlist_pex(net, p, outdir, t, en, i_n, nt, bw):
    """Post-layout jitter netlist: comparator + input noise in series with the gate of each comparator input
    device (the only NMOS w=4u l=0.3u whose gate is on the va / vb main node), 4kT/R current from vdd to va / vb."""
    out = []
    if ARG("--method"):
        # integration method for the stiff RC network (trapezoidal stalls on the PEX netlist with trnoise)
        out.append(".option method=%s" % ARG("--method"))
    hit = {"va": 0, "vb": 0}
    for ln in net.splitlines():
        f = ln.split()
        if f and f[0].startswith("XM") and len(f) > 5 and f[5] == "sg13_lv_nmos" and f[2] in hit and "w=4u" in ln and "l=0.3u" in ln:
            node = f[2]
            hit[node] += 1
            f[2] = node + "_nin"
            if p["case"] == "noise":
                out.append("VNI_%s %s_nin %s dc 0 trnoise(%g %g 0 0)" % (node, node, node, en * bw, nt))
            else:
                out.append("VNI_%s %s_nin %s dc 0" % (node, node, node))
            ln = " ".join(f)
        if ln.startswith(".ends"):
            for node in ("va", "vb"):
                if p["case"] == "noise":
                    out.append("INR_%s vdd %s dc 0 trnoise(%g %g 0 0)" % (node, node, i_n * bw, nt))
                else:
                    out.append("INR_%s vdd %s dc 0" % (node, node))
        out.append(ln)
    assert hit == {"va": 1, "vb": 1}, hit
    fn = os.path.join(outdir, t + "_netlist.spice")
    with open(fn, "w") as f:
        f.write("\n".join(out) + "\n")
    return {"NETLIST": fn, "EN": "%g" % en, "IN": "%g" % i_n, "NT": "%g" % nt, "TMAX": "%g" % nt, "TSTOP": ARG("--tstop", "35u")}


def jitter_post(fn):
    import numpy as np
    d = np.loadtxt(fn, skiprows=1)
    e = edges(d[:, 0], d[:, 1], 0.6)[10:]
    per = np.diff(e)
    n = 30
    tn = e[n:] - e[:-n]
    return {"n_periods": int(len(per)), "period_ns": float(per.mean() * 1e9), "sigma_period_ps": float(per.std() * 1e12),
            "sigma_30cyc_ps": float(tn.std() * 1e12), "sigma_period_ppm": float(per.std() / per.mean() * 1e6)}


def edges(t, v, th):
    import numpy as np
    i = np.where((v[:-1] < th) & (v[1:] >= th))[0]
    return t[i] + (th - v[i]) * (t[i + 1] - t[i]) / (v[i + 1] - v[i])


def psrr_post(fn, case):
    """Per-period frequency from rising osc_clk edges; supply sensitivity in ppm of f per mV."""
    import numpy as np
    d = np.loadtxt(fn, skiprows=1)
    t, vc, vd = d[:, 0], d[:, 1], d[:, 2]
    e = edges(t, vc, 0.6)[10:]
    per = np.diff(e)
    f = 1.0 / per
    tm = 0.5 * (e[1:] + e[:-1])
    vm = np.interp(tm, t, vd)
    out = {"n_periods": int(len(f))}
    if case == "step":
        fb = f[e[1:] < 1.0e-6].mean()
        fa = f[e[:-1] > 1.3e-6].mean()
        out.update(f_before_MHz=fb / 1e6, f_after_MHz=fa / 1e6, sens_ppm_per_mV=(fa - fb) / fb / 10.0 * 1e6)
    else:
        fr = 20e3 if case == "rip20k" else 1e6
        A = np.vstack([np.ones_like(vm), vm - 1.2]).T
        c = np.linalg.lstsq(A, f, rcond=None)[0]
        out["sens_ppm_per_mV_regress"] = c[1] / c[0] * 1e-3 * 1e6
        w = 2 * np.pi * fr
        B = np.vstack([np.ones_like(tm), np.sin(w * tm), np.cos(w * tm)]).T
        b = np.linalg.lstsq(B, f, rcond=None)[0]
        amp = float(np.hypot(b[1], b[2]))
        # supply ripple is 10 mV peak with phase sin(w t + phi0); report magnitude per mV and phase lag
        phi0 = 0.0
        ph = float(np.degrees(np.arctan2(b[2], b[1]) - phi0))
        out.update(f0_MHz=b[0] / 1e6, fm_amp_ppm_per_mV=amp / b[0] / 10.0 * 1e6, fm_phase_deg=(ph + 180) % 360 - 180,
                   f_min_MHz=float(f.min()) / 1e6, f_max_MHz=float(f.max()) / 1e6)
    return out


def main():
    suite, run_id = sys.argv[1], sys.argv[2]
    runner_sha = sha(os.path.abspath(__file__))
    jobs = int(sys.argv[sys.argv.index("--jobs") + 1]) if "--jobs" in sys.argv else 3
    root = os.environ["G1_RESULTS_ROOT"]
    outdir = os.path.join(root, "r1_osc", run_id)
    os.makedirs(outdir, exist_ok=False)
    rundir = os.path.join(HERE, "runs", run_id)
    os.makedirs(rundir, exist_ok=False)
    P = points(suite)
    import shutil
    if NETLIST == NETLIST_OF_RECORD:
        shutil.copy(NETLIST, os.path.join(rundir, "r1_osc.spice"))  # netlist snapshot as simulated
    start = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    with ThreadPoolExecutor(max_workers=jobs) as ex:
        res = list(ex.map(lambda p: run_point(p, outdir), P))
    end = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    ver = subprocess.check_output(["ngspice", "-v"]).decode()
    ver = re.search(r"ngspice-\d+", ver).group(0)
    with open("/foss/pdks/ihp-sg13g2/COMMIT") as f:
        pdk = f.read().strip()
    with open(os.path.join(rundir, "results.json"), "w") as f:
        json.dump(res, f, indent=1)
    keys = []
    for r in res:
        for k in r:
            if k not in keys:
                keys.append(k)
    with open(os.path.join(rundir, "results.csv"), "w") as f:
        f.write(",".join(keys) + "\n")
        for r in res:
            f.write(",".join(str(r.get(k, "")) for k in keys) + "\n")
    decks = sorted(set(p["deck"] for p in P))
    run = {
        "run_id": run_id, "suite": suite,
        "command": "G1_CPUSET=%s G1_CPUS=%s G1_WORKDIR=designs/r1-joint/blocks/r1_osc flow/run.sh python3 sim/run_osc30.py %s"
                   % (ARG("--cpuset", "100-102"), ARG("--cpus", "3"), " ".join((repr(a) if " " in a else a).replace(root, "<G1_RESULTS_ROOT>") for a in sys.argv[1:])),
        "start_utc": start.isoformat() + "Z", "end_utc": end.isoformat() + "Z",
        "wall_s": round((end - start).total_seconds(), 1),
        "tools": {"ngspice": ver, "container_image": "tapeoutbench-eda:latest sha256:ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2"},
        "pdk_commit": pdk,
        "inputs": {"netlist": ("schematic/r1_osc.spice" if NETLIST == NETLIST_OF_RECORD else
                               NETLIST.replace(root, "<G1_RESULTS_ROOT>")), "netlist_sha256": sha(NETLIST),
                   "netlist_of_record_sha256": sha(NETLIST_OF_RECORD),
                   "decks": {d: sha(os.path.join(HERE, d)) for d in decks},
                   "runner_sha256": runner_sha},
        "raw_results": "G1_RESULTS_ROOT/r1_osc/%s/ (expanded decks, logs, raw)" % run_id,
        "n_points": len(P), "n_rc_nonzero": sum(1 for r in res if r["rc"] != 0),
        "question": ARG("--question"), "result": "", "disposition": "",
        "probe": ARG("--probe") or None,
    }
    with open(os.path.join(rundir, "run.json"), "w") as f:
        json.dump(run, f, indent=1)
    for r in res:
        print(json.dumps(r))
    bad = [r["tag"] for r in res if r["rc"] != 0 or (r["deck"] == "tb_osc30.cir" and "f_MHz" not in r)]
    if bad:   # block rule: runners exit non-zero on a failed job
        print("FAILED jobs:", bad)
        sys.exit(1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""r1_bias revision 2 (D20): suites for the VREF buffer r1_vbuf (track T9, 2026-10-26). Runs inside the pinned container:

  G1_CPUSET=116-119 G1_WORKDIR=designs/r1-joint/blocks/r1_bias/sim G1_RESULTS_ROOT=<G1_RESULTS_ROOT> \
      flow/run.sh python3 run_vbuf.py <suite> <run-id> [key=value ...]

Every deck is the run_bias.py deck: the real r1_bgr (sha256 checked), r1_t2f on vref_b, the ADC filter 11 pF on the
raw vref, the consumer bias loads, and on vref_b the r1_safe string, two r1_isense pedestal arms and cvb (default
25 pF = 20 pF decoupling + 5 pF routing). Suites:
  vbstb    loop gain of r1_vbuf (Tian probe at the XM2 gate), cases x states (n = pedestals on, az = both off),
           optional cvb=, ib= (buffer bias per unit leg forced by a current at the diode node), PM >= 65, GM >= 10 dB
  vbzout   output impedance looking into the buffer (Z_buf) and of the loaded node (Z_node), 1 Hz - 100 MHz
  vbpsrr   supply rejection of vref_b and of the raw vref
  vbstep   VDDA 3.3 -> 3.0 V in 100 ns and back: vref_b deviation (1 % criterion) and overshoots
  vbaz     auto-zero load steps (pedestal switch of channel A, then B, then both, 2 us windows)
  vbnoise  output noise of vref_b and of the raw vref, integrated 10 Hz - 100 kHz
  vbdrive  extra DC load at vref_b 0 - 80 uA: vref_b shift (drive capability)
pex=<run> view=rc runs the extracted r1_bias (run_bias.py convention). Exit status 1 if any job fails or is unparsed.
"""
import json, math, os, sys, time
import run_bias as RB

HERE = RB.HERE
STB7 = ["tt", "ss", "ff", "sf", "fs", "ssx", "ffx"]
MAIN5 = ["tt", "ss", "ff", "ssx", "ffx"]
I_LEG_TT = 5.071e-6     # r1_bias leg ibvb at tt/27 C (dev-op-20261026-r2a); the bias-extreme decks force ib per unit


def wr(out, vecs):
    return "set filetype=ascii\nset wr_singlescale\nset wr_vecnames\n", "wrdata %s.dat %s\n" % (out, " ".join(vecs))


def probe_net(src, dst):
    """copy of the r1_bias netlist (schematic or extracted) with the Tian probe at the XM2 gate of r1_vbuf and a bias
    trim source Ixb at the diode node (param ixb, 0 = no change). Schematic: inside .subckt r1_vbuf (gate net vout).
    Extracted (flat inside r1_bias): every sg13_hv_nmos unit whose gate is on vref_b (the four XM2 units)."""
    text = open(src).read()
    flat = ".subckt r1_vbuf" not in text.lower()
    tgt, gate, nodes = ("r1_bias", "vref_b", ("vref_b", "ibvb", "vss")) if flat else ("r1_vbuf", "vout", ("vout", "ibn", "vss"))
    out, sub, n_moved = [], None, 0
    for l in text.splitlines():
        t = l.split()
        if t and t[0].lower() == ".subckt":
            sub = t[1].lower()
        if (sub == tgt and t and t[0].upper().startswith("X") and len(t) > 5 and "hv_nmos" in t[5]
                and t[2].split("__")[0] == gate):
            t[2] = "vout_rx"; l = " ".join(t); n_moved += 1
        if sub == tgt and t and t[0].lower() == ".ends":
            o, b, v = nodes
            out += ["Vprobe %s vout_rx dc 0 ac {vinj}" % o, "Iprobe 0 %s dc 0 ac {iinj}" % o, "Ixb %s %s dc {ixb}" % (b, v)]
            sub = None
        out.append(l)
    assert n_moved == (4 if flat else 1), "XM2 gate cut: %d instances moved in %s" % (n_moved, src)
    open(dst, "w").write("\n".join(out) + "\n")
    return n_moved


def azb(state, va):
    return ("dc 0", "dc 0") if state == "az" else (None, None)


def ixb_for(ib):
    return 0.0 if ib is None else I_LEG_TT - ib


# ------------------------------------------------------------------ loop gain
def stb_jobs(args):
    if "cases" in args or "states" in args or "ib" in args or "cvb" in args:
        cases = args.get("cases", ",".join(STB7)).split(",")
        states = args.get("states", "n,az").split(",")
        cvbs = args.get("cvb", RB.CVB).split(",")
        ibs = [float(x) for x in args["ib"].split(",")] if "ib" in args else [None]
        return [(c, s, cv, ib) for c in cases for s in states for cv in cvbs for ib in ibs]
    j = [(c, s, RB.CVB, None) for c in STB7 for s in ("n", "az")]
    j += [("tt", s, RB.CVB, ib) for ib in (3.5e-6, 7.7e-6) for s in ("n", "az")]
    j += [(c, "n", cv, None) for c in ("tt", "ff", "ffx", "ssx") for cv in ("2p", "50p")]
    return j


def stb_suite(rundir, args):
    from run_bgr import curve_margins
    pn = os.path.join(rundir, "r1_bias_probe.spice")
    moved = probe_net(RB.NET, pn)
    flat = ".subckt r1_vbuf" not in open(RB.NET).read().lower()
    vp = "v.xbias.vprobe" if flat else "v.xbias.xvb.vprobe"
    vbd = RB.vb_devices()
    items, meta = [], []
    toy = open(os.path.join(HERE, "tb_stb_toy.cir")).read().replace("@@RAW@@", os.path.join(rundir, "toy"))
    open(os.path.join(rundir, "toy.cir"), "w").write(toy)
    items.append((os.path.join(rundir, "toy.cir"), os.path.join(rundir, "toy.log"))); meta.append(("toy",))
    for c, st, cv, ib in stb_jobs(args):
        name = "vbstb_%s_%s_%s%s" % (c, st, cv, "" if ib is None else "_ib%.1f" % (ib * 1e6))
        out = os.path.join(rundir, name)
        h, f = wr(out, ["tre", "tim"])
        ctl = """.control
%sop
print v(vref) v(vref_b) %s
ac dec 20 1 1g
alterparam vinj=0
alterparam iinj=1
reset
ac dec 20 1 1g
let v1 = ac1.v(vref_b)
let i1 = ac1.i(%s)
let v2 = ac2.v(vref_b)
let i2 = ac2.i(%s)
let tl = -1/(1-1/(2*(i1*v2-v1*i2)+v1+i2))
let tre = real(tl)
let tim = imag(tl)
%s.endc
""" % (h, " ".join(vbd["xmb"] + vbd["xm7"]), vp, vp, f)
        va = RB.CORNERS[c][5]
        body = ".param vinj=1 iinj=0 ixb=%g" % ixb_for(ib)
        nl = RB.NET
        RB.NET = pn
        try:
            open(out + ".cir", "w").write(RB.deck(c, body, ctl, azb_src=azb(st, va), cvb=cv))
        finally:
            RB.NET = nl
        items.append((out + ".cir", out + ".log")); meta.append(("stb", c, st, cv, ib, out))
    res = RB.run_all(items)
    rows, fails, summ = [], 0, {"probe_moved_gates": moved}
    for mt, (_, rc, dt) in zip(meta, res):
        if mt[0] == "toy":
            for l in open(os.path.join(rundir, "toy.log")):
                if "TOYROW" in l:
                    summ["toy"] = l.strip()
            fails += rc != 0
            continue
        _, c, st, cv, ib, out = mt
        row = dict(case=c, state=st, cvb=cv, ib_unit_uA=None if ib is None else ib * 1e6, rc=rc, seconds=round(dt, 1))
        try:
            d = RB.read_cols(out + ".dat")
            k = list(d)
            row.update(curve_margins(d[k[0]], d[k[1]], d[k[2]]))
            row["pass_pm65"] = row["pm_deg"] is not None and row["pm_deg"] >= 65
            row["pass_gm10"] = row["gm_db"] is None or row["gm_db"] >= 10
            pr = RB.parse_prints(out + ".log")
            row["vref"] = pr.get("v(vref)"); row["vref_b"] = pr.get("v(vref_b)")
            row["i_bias_diode_uA"] = sum(abs(pr.get(v, float("nan"))) for v in vbd["xmb"]) * 1e6
            row["i_m7_uA"] = sum(abs(pr.get(v, float("nan"))) for v in vbd["xm7"]) * 1e6
        except Exception as e:
            row["error"] = repr(e); fails += 1
        fails += rc != 0
        rows.append(row)
    summ["rows"] = rows
    summ["all_pass_pm65_gm10_25p"] = all(r.get("pass_pm65") and r.get("pass_gm10") for r in rows if r["cvb"] == RB.CVB)
    return summ, fails


# ------------------------------------------------------------------ output impedance
FPTS = [1, 10, 100, 1e3, 1e4, 1e5, 3e5, 1e6, 3e6, 1e7, 3e7, 1e8]


def zout_suite(rundir, args):
    cases = args.get("cases", ",".join(MAIN5)).split(",")
    states = args.get("states", "n,az").split(",")
    items, meta = [], []
    for c in cases:
        for st in states:
            out = os.path.join(rundir, "vbz_%s_%s" % (c, st))
            h, f = wr(out, ["zbr", "zbi", "znr", "zni"])
            ctl = """.control
%sop
print v(vref_b)
ac dec 20 1 100meg
let ib = -(i(vmvb)+i(vmtv))
let zb = v(vref_b)/ib
let zn = v(vref_bl)
let zbr = real(zb)
let zbi = imag(zb)
let znr = real(zn)
let zni = imag(zn)
%s.endc
""" % (h, f)
            body = "Izo 0 vref_bl dc 0 ac 1"
            open(out + ".cir", "w").write(RB.deck(c, body, ctl, azb_src=azb(st, RB.CORNERS[c][5])))
            items.append((out + ".cir", out + ".log")); meta.append((c, st, out))
    res = RB.run_all(items)
    rows, fails = [], 0
    for (c, st, out), (_, rc, dt) in zip(meta, res):
        row = dict(case=c, state=st, rc=rc, seconds=round(dt, 1))
        try:
            d = RB.read_cols(out + ".dat")
            k = list(d); fr = d[k[0]]
            zb = [math.hypot(a, b) for a, b in zip(d[k[1]], d[k[2]])]
            zn = [math.hypot(a, b) for a, b in zip(d[k[3]], d[k[4]])]
            ph = [math.degrees(math.atan2(b, a)) for a, b in zip(d[k[1]], d[k[2]])]
            pick = lambda fq: min(range(len(fr)), key=lambda j: abs(math.log(fr[j] / fq)))
            row["zbuf_ohm"] = {("%g" % fq): round(zb[pick(fq)], 3) for fq in FPTS}
            row["zbuf_phase_deg"] = {("%g" % fq): round(ph[pick(fq)], 1) for fq in FPTS}
            row["znode_ohm"] = {("%g" % fq): round(zn[pick(fq)], 3) for fq in FPTS}
            kmax = max(range(len(fr)), key=lambda j: zb[j] if fr[j] <= 1e7 else -1)
            row["zbuf_max_to_10M_ohm"] = round(zb[kmax], 1); row["f_zbuf_max"] = fr[kmax]
            kn = max(range(len(fr)), key=lambda j: zn[j])
            row["znode_max_ohm"] = round(zn[kn], 1); row["f_znode_max"] = fr[kn]
            row["pass_zdc_1k"] = zb[0] <= 1000
            # small table for the consumer decks (frequency, |Z_buf|, phase): results/<run>_zbuf_<case>_<state>.csv
            csv = os.path.join(HERE, "results", "%s_zbuf_%s_%s.csv" % (os.path.basename(rundir), c, st))
            with open(csv, "w") as fh:
                fh.write("f_Hz,zbuf_re_ohm,zbuf_im_ohm\n")
                for j in range(0, len(fr), 5):
                    fh.write("%.4g,%.5g,%.5g\n" % (fr[j], d[k[1]][j], d[k[2]][j]))
            row["csv"] = "sim/results/" + os.path.basename(csv)
        except Exception as e:
            row["error"] = repr(e); fails += 1
        fails += rc != 0
        rows.append(row)
    return rows, fails


# ------------------------------------------------------------------ PSRR
def psrr_suite(rundir, args):
    cases = args.get("cases", ",".join(MAIN5)).split(",")
    items, meta = [], []
    for c in cases:
        out = os.path.join(rundir, "vbpsrr_%s" % c)
        h, f = wr(out, ["mag(v(vref_b))", "mag(v(vref))"])
        ctl = ".control\n%sop\nac dec 20 1 100meg\n%s.endc\n" % (h, f)
        open(out + ".cir", "w").write(RB.deck(c, "", ctl, vdda_src="dc %g ac 1" % RB.CORNERS[c][5]))
        items.append((out + ".cir", out + ".log")); meta.append((c, out))
    res = RB.run_all(items)
    rows, fails = [], 0
    for (c, out), (_, rc, dt) in zip(meta, res):
        row = dict(case=c, rc=rc, seconds=round(dt, 1))
        try:
            d = RB.read_cols(out + ".dat"); k = list(d); fr = d[k[0]]
            pick = lambda fq: min(range(len(fr)), key=lambda j: abs(math.log(fr[j] / fq)))
            for nm, kk in (("vref_b", k[1]), ("vref", k[2])):
                row[nm + "_dB"] = {("%g" % fq): round(20 * math.log10(max(d[kk][pick(fq)], 1e-30)), 2) for fq in (10, 1e3, 2e4, 1e5, 1e6, 1e7)}
                row[nm + "_worst_dB"] = round(max(20 * math.log10(max(x, 1e-30)) for x in d[kk]), 2)
        except Exception as e:
            row["error"] = repr(e); fails += 1
        fails += rc != 0
        rows.append(row)
    return rows, fails


# ------------------------------------------------------------------ transients
def excursions(t, x, t0, t1, xf, band):
    """signs of the excursions of x - xf beyond +-band in [t0, t1] (consecutive same-sign samples merged)"""
    seq, cur = [], 0
    for tt, v in zip(t, x):
        if tt < t0 or tt > t1:
            continue
        e = v - xf
        s = 1 if e > band else -1 if e < -band else 0
        if s and s != cur:
            seq.append(s); cur = s
    return seq


def settle_after(t, x, t0, t1, xf, tol):
    last = t0
    for tt, v in zip(t, x):
        if t0 <= tt <= t1 and abs(v - xf) > tol:
            last = tt
    return last - t0


def window(t, x, t0, t1):
    return [v for tt, v in zip(t, x) if t0 <= tt <= t1]


def step_suite(rundir, args):
    cases = args.get("cases", ",".join(MAIN5)).split(",")
    items, meta = [], []
    T1, T2, TE = 30e-6, 80e-6, 130e-6
    for c in cases:
        out = os.path.join(rundir, "vbstep_%s" % c)
        h, f = wr(out, ["v(vdda)", "v(vref)", "v(vref_b)"])
        src = "pwl(0 3.3 %g 3.3 %g 3.0 %g 3.0 %g 3.3 %g 3.3)" % (T1, T1 + 100e-9, T2, T2 + 100e-9, TE)
        ctl = ".control\n%stran 5n %g 0 20n\n%s.endc\n" % (h, TE, f)
        open(out + ".cir", "w").write(RB.deck(c, "", ctl, vdda_src=src))
        items.append((out + ".cir", out + ".log")); meta.append((c, out))
    res = RB.run_all(items)
    rows, fails = [], 0
    for (c, out), (_, rc, dt) in zip(meta, res):
        row = dict(case=c, rc=rc, seconds=round(dt, 1))
        try:
            d = RB.read_cols(out + ".dat"); k = list(d); t = d[k[0]]
            vb, vr = d["v(vref_b)"], d["v(vref)"]
            for lab, ts, te in (("down", T1, T2), ("up", T2, TE)):
                pre = window(t, vb, ts - 5e-6, ts)
                v0 = sum(pre) / len(pre)
                fin = window(t, vb, te - 5e-6, te)
                vf = sum(fin) / len(fin)
                w = window(t, vb, ts, te)
                dev = max(abs(v - v0) for v in w)
                prer = window(t, vr, ts - 5e-6, ts); r0 = sum(prer) / len(prer)
                devr = max(abs(v - r0) for v in window(t, vr, ts, te))
                diff = [b - a for a, b in zip(vr, vb)]
                dw = window(t, diff, ts - 5e-6, ts); d0 = sum(dw) / len(dw)
                devd = max(abs(v - d0) for v in window(t, diff, ts, te))
                seq = excursions(t, vb, ts, te, vf, 0.5e-3)
                row[lab] = dict(v_before=round(v0, 6), v_final=round(vf, 6), dev_max_mV=round(dev * 1e3, 3),
                                dev_max_pct=round(dev / v0 * 100, 3), vref_dev_max_mV=round(devr * 1e3, 3),
                                buffer_dev_max_mV=round(devd * 1e3, 3), excursions_0p5mV=seq,
                                settle_1mV_us=round(settle_after(t, vb, ts, te, vf, 1e-3) * 1e6, 2),
                                pass_1pct=dev / v0 <= 0.01, pass_one_overshoot=len(seq) <= 2,
                                info_buffer_within_1pct=devd / v0 <= 0.01)
        except Exception as e:
            row["error"] = repr(e); fails += 1
        fails += rc != 0
        rows.append(row)
    return rows, fails


def az_suite(rundir, args):
    cases = args.get("cases", ",".join(MAIN5)).split(",")
    items, meta = [], []
    EV = [("a", 20e-6), ("b", 40e-6), ("ab", 60e-6)]
    TW, TR, TE = 2e-6, 2e-9, 80e-6
    for c in cases:
        va = RB.CORNERS[c][5]
        pa, pb = ["0 %g" % va], ["0 %g" % va]
        for ch, t0 in EV:
            for lst, on in ((pa, "a" in ch), (pb, "b" in ch)):
                if on:
                    lst.append("%g %g %g 0 %g 0 %g %g" % (t0, va, t0 + TR, t0 + TW, t0 + TW + TR, va))
        pa.append("%g %g" % (TE, va)); pb.append("%g %g" % (TE, va))
        out = os.path.join(rundir, "vbaz_%s" % c)
        h, f = wr(out, ["v(vref_b)", "v(vref)", "i(vmvb)"])
        ctl = ".control\n%stran 2n %g 0 10n\n%s.endc\n" % (h, TE, f)
        open(out + ".cir", "w").write(RB.deck(c, "", ctl, azb_src=("pwl(%s)" % " ".join(pa), "pwl(%s)" % " ".join(pb))))
        items.append((out + ".cir", out + ".log")); meta.append((c, out))
    res = RB.run_all(items)
    rows, fails = [], 0
    for (c, out), (_, rc, dt) in zip(meta, res):
        row = dict(case=c, rc=rc, seconds=round(dt, 1), events={})
        try:
            d = RB.read_cols(out + ".dat"); k = list(d); t = d[k[0]]
            vb = d["v(vref_b)"]; il = d["i(vmvb)"]
            for ch, t0 in EV:
                pre = window(t, vb, t0 - 3e-6, t0); v0 = sum(pre) / len(pre)
                ion = sum(window(t, il, t0 - 3e-6, t0)) / len(pre)
                ioff = window(t, il, t0 + 1.5e-6, t0 + TW)
                ev = {}
                for edge, ts, te in (("open", t0, t0 + TW), ("close", t0 + TW, t0 + TW + 15e-6)):
                    w = window(t, vb, ts, te)
                    ev[edge] = dict(dev_max_mV=round(max(abs(v - v0) for v in w) * 1e3, 3),
                                    settle_0p5mV_us=round(settle_after(t, vb, ts, te, v0, 0.5e-3) * 1e6, 3))
                ev["load_step_uA"] = round((ion - sum(ioff) / len(ioff)) * 1e6, 3)
                row["events"][ch] = ev
        except Exception as e:
            row["error"] = repr(e); fails += 1
        fails += rc != 0
        rows.append(row)
    return rows, fails


# ------------------------------------------------------------------ noise
def noise_suite(rundir, args):
    cases = args.get("cases", "tt,ss,ff").split(",")
    items, meta = [], []
    for c in cases:
        for node in ("vref_b", "vref"):
            out = os.path.join(rundir, "vbnoise_%s_%s" % (c, node))
            ctl = """.control
set filetype=ascii
set wr_singlescale
set wr_vecnames
op
noise v(%s) vdda dec 20 10 100k
setplot noise2
print onoise_total
setplot noise1
wrdata %s.dat onoise_spectrum
.endc
""" % (node, out)
            # the noise input source needs an AC value (vb-noise-20261026-r2b: "no AC value", then no convergence)
            open(out + ".cir", "w").write(RB.deck(c, "", ctl, vdda_src="dc %g ac 1" % RB.CORNERS[c][5]))
            items.append((out + ".cir", out + ".log")); meta.append((c, node, out))
    res = RB.run_all(items)
    rows, fails, by = [], 0, {}
    for (c, node, out), (_, rc, dt) in zip(meta, res):
        try:
            pr = RB.parse_prints(out + ".log")
            v = pr["onoise_total"]
            d = RB.read_cols(out + ".dat"); k = list(d); fr = d[k[0]]; sp = d[k[1]]
            pick = lambda fq: min(range(len(fr)), key=lambda j: abs(math.log(fr[j] / fq)))
            by.setdefault(c, {})[node] = dict(rms_uV_10Hz_100kHz=round(v * 1e6, 3),
                                              density_nV_rtHz={("%g" % fq): round(sp[pick(fq)] * 1e9, 1) for fq in (10, 100, 1e3, 1e4, 1e5)})
        except Exception as e:
            by.setdefault(c, {})[node] = dict(error=repr(e)); fails += 1
        fails += rc != 0
    for c, dd in by.items():
        r = dict(case=c, **dd)
        try:
            r["buffer_added_rms_uV"] = round(max(dd["vref_b"]["rms_uV_10Hz_100kHz"] ** 2 - dd["vref"]["rms_uV_10Hz_100kHz"] ** 2, 0) ** 0.5, 3)
        except Exception:
            pass
        rows.append(r)
    return rows, fails


# ------------------------------------------------------------------ drive
def drive_suite(rundir, args):
    cases = args.get("cases", ",".join(MAIN5)).split(",")
    items, meta = [], []
    for c in cases:
        out = os.path.join(rundir, "vbdrive_%s" % c)
        h, f = wr(out, ["v(vref_b)", "v(vref)", "i(vmvb)"])
        ctl = ".control\n%sdc iex 0 80u 1u\n%s.endc\n" % (h, f)
        open(out + ".cir", "w").write(RB.deck(c, "Iex vref_bl 0 dc 0", ctl))
        items.append((out + ".cir", out + ".log")); meta.append((c, out))
    res = RB.run_all(items)
    rows, fails = [], 0
    for (c, out), (_, rc, dt) in zip(meta, res):
        row = dict(case=c, rc=rc, seconds=round(dt, 1))
        try:
            d = RB.read_cols(out + ".dat"); k = list(d)
            ix, vb, vr, il = d[k[0]], d["v(vref_b)"], d["v(vref)"], d["i(vmvb)"]
            v0 = vb[0]
            tot = [a for a in il]
            j50 = min(range(len(tot)), key=lambda j: abs(tot[j] - 50e-6))
            row["load_at_zero_extra_uA"] = round(il[0] * 1e6, 3)
            row["shift_at_total_50uA_mV"] = round((vb[j50] - v0) * 1e3, 4)
            row["offset_at_total_50uA_mV"] = round((vb[j50] - vr[j50]) * 1e3, 4)
            jm = [j for j in range(len(ix)) if abs(vb[j] - v0) > 1e-3]
            row["total_load_at_1mV_drop_uA"] = round(tot[jm[0]] * 1e6, 2) if jm else ">%.1f" % (tot[-1] * 1e6)
            row["pass_50uA_1mV"] = abs(vb[j50] - v0) <= 1e-3
        except Exception as e:
            row["error"] = repr(e); fails += 1
        fails += rc != 0
        rows.append(row)
    return rows, fails


QUESTIONS = {
    "vbstb": "r1_vbuf loop gain (Tian probe at the XM2 gate) with the real vref_b load: PM >= 65 deg, GM >= 10 dB.",
    "vbzout": "Output impedance of r1_vbuf under the real load, 1 Hz - 100 MHz (<= 1 kOhm at DC; table for the consumer decks).",
    "vbpsrr": "Supply rejection of vref_b and of the raw vref.",
    "vbstep": "VDDA step 3.3 -> 3.0 V in 100 ns and back: vref_b within 1 %, at most one overshoot.",
    "vbaz": "r1_isense auto-zero load steps (pedestal arms off for 2 us): vref_b glitch and settling.",
    "vbnoise": "Output noise of vref_b against the raw vref, 10 Hz - 100 kHz.",
    "vbdrive": "Drive capability: vref_b shift with an extra DC load up to 80 uA.",
}


def main():
    suite, runid = sys.argv[1], sys.argv[2]
    args = dict(a.split("=", 1) for a in sys.argv[3:] if "=" in a)
    assert RB.ROOT, "G1_RESULTS_ROOT not set"
    rundir = os.path.join(RB.ROOT, "r1_bias", runid)
    os.makedirs(rundir, exist_ok=True)
    assert RB.sha(RB.BGR) == RB.BGR_SHA and RB.sha(RB.T2F) == RB.T2F_SHA, "neighbour netlist sha256 mismatch"
    if "pex" in args:
        sfx = {"rc": "", "c": "_c", "dev": "_dev"}[args.get("view", "rc")]
        RB.NET = os.path.join(RB.ROOT, "r1_bias", args["pex"], "r1_bias_pex%s.spice" % sfx)
        assert os.path.exists(RB.NET), "no extracted netlist for pex=%s" % args["pex"]
    RB.CONV = args.get("conv") in ("1", "2"); RB.CONV2 = args.get("conv") == "2"
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    t0 = time.time()
    fn = dict(vbstb=stb_suite, vbzout=zout_suite, vbpsrr=psrr_suite, vbstep=step_suite, vbaz=az_suite,
              vbnoise=noise_suite, vbdrive=drive_suite)[suite]
    res, fails = fn(rundir, args)

    def spec_fails(x, path=""):
        # every pass_* flag that is False is a specification failure (the runner then exits 1)
        out = []
        if isinstance(x, dict):
            for k, v in x.items():
                if k.startswith("pass_") and v is False:
                    out.append(path + "/" + k)
                elif isinstance(v, (dict, list)):
                    out += spec_fails(v, path + "/" + str(x.get("case", k)) + ("" if "case" not in x else "." + str(k)))
        elif isinstance(x, list):
            for i, v in enumerate(x):
                out += spec_fails(v, path)
        return out
    sf = spec_fails(res)
    summary = dict(run_id=runid, suite=suite, question=QUESTIONS.get(suite), args=args,
                   command="G1_CPUSET=116-119 G1_WORKDIR=designs/r1-joint/blocks/r1_bias/sim G1_RESULTS_ROOT=<G1_RESULTS_ROOT> "
                           "flow/run.sh python3 run_vbuf.py %s %s %s" % (suite, runid, " ".join("%s=%s" % kv for kv in args.items())),
                   r1_bias_netlist=("<G1_RESULTS_ROOT>/r1_bias/%s/%s" % (args["pex"], os.path.basename(RB.NET))) if "pex" in args
                   else "designs/r1-joint/blocks/r1_bias/schematic/r1_bias.spice",
                   pdk_commit=RB.PDK_COMMIT, ngspice=RB.ngspice_version(), git_head=RB.git_rev(),
                   netlist_sha256=dict(r1_bias=RB.sha(RB.NET), r1_bgr=RB.sha(RB.BGR), r1_t2f=RB.sha(RB.T2F),
                                       loads=RB.sha(RB.LOADS), vrefb_loads=RB.sha(RB.VBLOADS)),
                   cvb_default=RB.CVB, raw="<G1_RESULTS_ROOT>/r1_bias/%s/" % runid, seconds=round(time.time() - t0, 1),
                   failed_jobs=fails, spec_failures=sf, result=res)
    json.dump(summary, open(os.path.join(HERE, "results", runid + ".json"), "w"), indent=1, default=str)
    rd = os.path.join(HERE, "runs", runid)
    os.makedirs(rd, exist_ok=True)
    runjson = {k: v for k, v in summary.items() if k != "result"}
    runjson["summary"] = "sim/results/%s.json" % runid
    runjson["disposition"] = ("failed: %d job(s) failed or unparsed" % fails if fails else
                              "failed: %d specification check(s) failed" % len(sf) if sf else "pending review")
    json.dump(runjson, open(os.path.join(rd, "run.json"), "w"), indent=1)
    print("suite", suite, "run", runid, "failed jobs", fails, "spec failures", len(sf), sf[:8])
    sys.exit(1 if fails or sf else 0)


if __name__ == "__main__":
    main()

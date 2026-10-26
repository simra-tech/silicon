#!/usr/bin/env python3
"""r1_bias simulation runner (track T9). Runs inside the pinned container:

  G1_CPUSET=116-119 G1_WORKDIR=designs/r1-joint/blocks/r1_bias/sim G1_RESULTS_ROOT=<G1_RESULTS_ROOT> \
      flow/run.sh python3 run_bias.py <suite> <run-id>

Suites: op comp mc startup psrr stb thr por mcthr. Every deck contains the real r1_bgr netlist of record (sha256
checked), the r1_t2f netlist (en = 0, pbias/pcasc gate load), the ADC reference filter on vref (10 pF + 1 pF) and the
consumer bias-pin loads of sim/r1_bias_loads.spice. Raw decks, logs and waveforms go to
$G1_RESULTS_ROOT/r1_bias/<run-id>/; the summary goes to results/<run-id>.json and runs/<run-id>/run.json.
At most BIAS_JOBS (default 3) ngspice processes run at a time. Exit status 1 if any job fails or cannot be parsed.
Post-layout (layout track, 2026-10-21): pex=<pex-rc run id> view=rc|c|dev replaces the schematic r1_bias with the
extracted netlist <G1_RESULTS_ROOT>/r1_bias/<pex run>/r1_bias_pex[_c|_dev].spice (layout/pex_build.py); suite por takes
ramps=<s,...> and kinds=upA,upD,bo.
"""
# transient tmax: 0.2 us (1 us stalls in the r1_bgr HBTs at POR comparator edges at ssx/ffx, dev-num-20261021-a)
TMAX = "0.2u"
CONV = False   # set by the argument conv=1 (conv=2: also more op iterations and finer stepping)
CONV2 = False
import hashlib, json, math, os, subprocess, sys, time
from multiprocessing.pool import ThreadPool

HERE = os.path.dirname(os.path.abspath(__file__))
BLK = os.path.dirname(HERE)
R1 = os.path.dirname(BLK)
REPO = os.path.dirname(os.path.dirname(R1))
NET = os.path.join(BLK, "schematic", "r1_bias.spice")
BGR = os.path.join(R1, "r1_bgr", "schematic", "r1_bgr.spice")
T2F = os.path.join(R1, "r1_t2f", "schematic", "g1_t2f_rev2.spice")
LOADS = os.path.join(HERE, "r1_bias_loads.spice")
VBLOADS = os.path.join(HERE, "r1_vrefb_loads.spice")   # revision 2: vref_b consumers (make_vrefb_loads.py)
CVB = "25p"      # vref_b load capacitance: 20 pF decoupling (D20) + 5 pF chip routing (estimate), argument cvb=
VSB = 0.04       # r1_isense summing-node voltage held under the pedestal arms (sb = sa = 0.02-0.06 V at zero current)
BGR_SHA = "c19a7425d605906962724fdda21add8ae3926dc9a097c6f835a16f05f92c0c26"
T2F_SHA = "8011b76104e9faa4a29dae4323ce59fb6f5864373a087df0767a61672a7b4391"
JOBS = int(os.environ.get("BIAS_JOBS", "3"))
ROOT = os.environ.get("G1_RESULTS_ROOT", "")
PDK_COMMIT = "84374023ee8b4b126bebbba67fcbada0a9c0ff0b"
sys.path.insert(0, os.path.join(R1, "r1_bgr", "sim"))
sys.path.insert(0, os.path.join(BLK, "schematic"))

# (pin, load subckt, nominal current in A, polarity text)
OUTS = [("ib_afe_s1", "ld_afe_ota1", 10e-6), ("ib_afe_s2", "ld_afe_ota2", 10e-6),
        ("ib_afe_c1", "ld_afe_ota1", 10e-6), ("ib_afe_c2", "ld_afe_ota2", 10e-6),
        ("ib_is_a", "ld_isense", 5e-6), ("ib_is_b", "ld_isense", 5e-6),
        ("ib_sf_oa", "ld_safe", 5e-6), ("ib_sf_na", "ld_safe", 5e-6),
        ("ib_sf_ob", "ld_safe", 5e-6), ("ib_sf_nb", "ld_safe", 5e-6),
        ("ib_adc_ref", "ld_adcref", 5e-6)]
PINS = [o[0] for o in OUTS]

# corner: (hbt, mos, res, cap, temp, vdda, vdd)
CORNERS = {
    "tt": ("hbt_typ", "mos_tt", "res_typ", "cap_typ", 27, 3.3, 1.2),
    "ss": ("hbt_wcs", "mos_ss", "res_wcs", "cap_wcs", 125, 3.0, 1.08),
    "ff": ("hbt_bcs", "mos_ff", "res_bcs", "cap_bcs", -40, 3.6, 1.32),
    "sf": ("hbt_typ", "mos_sf", "res_typ", "cap_typ", 27, 3.3, 1.2),
    "fs": ("hbt_typ", "mos_fs", "res_typ", "cap_typ", 27, 3.3, 1.2),
    "ssx": ("hbt_wcs", "mos_ss", "res_wcs", "cap_wcs", -40, 3.6, 1.32),
    "ffx": ("hbt_bcs", "mos_ff", "res_bcs", "cap_bcs", 125, 3.0, 1.08),
    "tt_m40": ("hbt_typ", "mos_tt", "res_typ", "cap_typ", -40, 3.3, 1.2),
    "tt_125": ("hbt_typ", "mos_tt", "res_typ", "cap_typ", 125, 3.3, 1.2),
    "tt_rbcs": ("hbt_typ", "mos_tt", "res_bcs", "cap_typ", 27, 3.3, 1.2),
    "tt_rwcs": ("hbt_typ", "mos_tt", "res_wcs", "cap_typ", 27, 3.3, 1.2),
    "tt_3v0": ("hbt_typ", "mos_tt", "res_typ", "cap_typ", 27, 3.0, 1.2),
    "tt_3v6": ("hbt_typ", "mos_tt", "res_typ", "cap_typ", 27, 3.6, 1.2),
}
MAIN3 = ["tt", "ss", "ff"]

VB_NODES = ["xbias.xvb.x1", "xbias.xvb.ns", "xbias.xvb.d1", "xbias.ibvb"]
POR_NODES = ["xbias.xpor.gooda", "xbias.xpor.goodd", "xbias.xpor.rst", "xbias.xpor.cdel", "xbias.xpor.ready",
             "xbias.xpor.vrh", "xbias.xpor.vrl", "xbias.xpor.tapa"]


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def deck(corner, body, control, mism=False, outs_mode="load", vdda_src=None, vdd_src=None, bgr_net=None, azb_src=(None, None), cvb=None):
    h, m, r, c, t, va, vd = CORNERS[corner]
    sfx = "_mismatch" if mism else ""
    L = ["* r1_bias deck, corner %s (%s %s %s %s, %g C, VDDA %g V, VDD %g V)%s" % (corner, h, m, r, c, t, va, vd, " mismatch" if mism else "")]
    L.append(".lib /foss/pdks/ihp-sg13g2/libs.tech/ngspice/models/cornerHBT.lib %s%s" % (h, sfx))
    L.append(".lib /foss/pdks/ihp-sg13g2/libs.tech/ngspice/models/cornerMOShv.lib %s%s" % (m, sfx))
    L.append(".lib /foss/pdks/ihp-sg13g2/libs.tech/ngspice/models/cornerMOSlv.lib %s%s" % (m, sfx))
    L.append(".lib /foss/pdks/ihp-sg13g2/libs.tech/ngspice/models/cornerRES.lib %s%s" % (r, sfx))
    L.append(".lib /foss/pdks/ihp-sg13g2/libs.tech/ngspice/models/cornerCAP.lib %s%s" % (c, sfx))
    L.append(".include %s" % (bgr_net or BGR))
    L.append(".include %s" % T2F)
    L.append(".include %s" % NET)
    L.append(".include %s" % LOADS)
    L.append(".include %s" % VBLOADS)
    L.append(".option gmin=1e-15 abstol=1e-14 reltol=1e-5 vntol=1e-7")
    if CONV:
        # convergence aids for the retry runs (chain d): <= 1 pA/V per node, negligible against uA bias currents
        L.append(".option gmin=1e-12 rshunt=1e12")
    if CONV2:
        # conv=2 (revision 2 post-layout retry): more operating-point iterations and finer gmin / source stepping
        L.append(".option itl1=1000 gminsteps=100 srcsteps=100")
    if "tran " in control:
        # trapezoidal integration stalls ("timestep too small" in the r1_bgr HBTs) at POR comparator edges (dev-thr-20261021-a)
        L.append(".option method=gear")
    L.append(".temp %g" % t)
    L.append(".global sub!")
    L.append("Vsub sub! 0 0")
    L.append("Vdda vdda 0 %s" % (vdda_src or "dc %g" % va))
    L.append("Vdd vdd 0 %s" % (vdd_src or "dc %g" % vd))
    L.append("Vdl vdl 0 dc 1.0")
    L.append("* supply ammeters: bandgap, T2F, r1_bias")
    L.append("Vmg vdda vdda_g dc 0")
    L.append("Vmt vdda vdda_t dc 0")
    L.append("Vmb vdda vdda_b dc 0")
    L.append("Xbgr vdda_g 0 vref iptat pbias pcasc vbe dvbe r1_bgr")
    L.append("Vload iptat 0 dc 1.0")
    L.append("* vref load: ADC r1_reffilt5 10 pF MIM + 1 pF (r1_bgr deck load)")
    L.append("Cvref vref 0 11p")
    L.append("Ven en 0 dc 0")
    L.append("Vmode mode 0 dc 0")
    L.append("* revision 2 (D20): the T2F vref pin is on vref_b (its mode-0 base current must not load the raw vref)")
    L.append("Vmtv vref_b vref_bt dc 0")
    L.append("XT2F vdda_t vdd 0 pbias pcasc vref_bt en mode fout g1_t2f")
    L.append("* raw vref -> r1_bias vref pin (buffer gate) through an ammeter")
    L.append("Vmvr vref vref_bi dc 0")
    L.append("Xbias vdda_b vdd 0 pbias pcasc %s por_n vref_bi vref_b r1_bias" % " ".join(PINS))
    L.append("* vref_b loads (sim/r1_vrefb_loads.spice): r1_safe threshold string, two r1_isense pedestal arms, decoupling + routing C")
    L.append("Vmvb vref_b vref_bl dc 0")
    L.append("XSTR vref_bl %s 0 r1_safe_string" % " ".join("st%d" % i for i in range(253)))
    L.append("XPA vref_bl azb_a sba 0 ld_isped")
    L.append("XPB vref_bl azb_b sbb 0 ld_isped")
    L.append("Vsba sba 0 dc %g" % VSB)
    L.append("Vsbb sbb 0 dc %g" % VSB)
    L.append("Vaza azb_a 0 %s" % (azb_src[0] or "dc %g" % va))
    L.append("Vazb azb_b 0 %s" % (azb_src[1] or "dc %g" % va))
    L.append("Cvb vref_bl 0 %s" % (cvb or CVB))
    L.append("* por_n load: r1_ctrl reset input and wiring (estimate)")
    L.append("Cpor por_n 0 0.2p")
    for pin, ld, _ in OUTS:
        if outs_mode == "load":
            L.append("Vm_%s %s %s_l dc 0" % (pin, pin, pin))
            L.append("XLD_%s %s_l vdl 0 %s" % (pin, pin, ld))
        else:  # compliance sweep: all outputs into the swept node vsw
            L.append("Vm_%s %s vsw dc 0" % (pin, pin))
    if outs_mode != "load":
        L.append("Vsw vsw 0 dc 1.0")
    L.append(body)
    L.append(control)
    L.append(".end")
    return "\n".join(L) + "\n"


def run_one(args):
    path, log = args
    t0 = time.time()
    with open(log, "w") as f:
        rc = subprocess.call(["ngspice", "-b", path], stdout=f, stderr=subprocess.STDOUT, cwd=HERE)
    txt = open(log, errors="replace").read()
    if rc == 0 and ("Error" in txt and "simulation(s) aborted" in txt or "Timestep too small" in txt):
        rc = 99
    return path, rc, time.time() - t0


def run_all(items):
    pool = ThreadPool(JOBS)
    out = pool.map(run_one, items)
    pool.close(); pool.join()
    return out


def read_cols(p):
    rows = [l.split() for l in open(p) if l.strip()]
    hdr = rows[0]
    data = []
    for r in rows[1:]:
        try:
            data.append([float(x) for x in r])
        except ValueError:
            pass
    return {h: [r[i] for r in data] for i, h in enumerate(hdr)}


def parse_prints(log):
    d = {}
    for l in open(log, errors="replace"):
        if " = " in l and not l.startswith("Note"):
            k, v = l.split(" = ", 1)
            try:
                d[k.strip()] = float(v.split()[0])
            except (ValueError, IndexError):
                pass
    return d


# ------------------------------------------------------------------ op
def vb_devices():
    """r1_vbuf output/bias devices of the current netlist: class -> list of ngspice device names (the extracted
    netlist is flat inside r1_bias, so the units are found by their terminal nets: XM7 gate x1 on vref_b/vdda, XM8
    gate ibvb on vref_b, XMT gate ibvb on ns, XMB gate ibvb on ibvb)."""
    if "pex" not in os.path.basename(NET):
        return {k: ["@n.xbias.xvb.%s.nsg13_hv_nmos[ids]" % k] for k in ("xm7", "xm8", "xmt", "xmb")}
    base = lambda n: n.split("__")[0]
    out = {"xm7": [], "xm8": [], "xmt": [], "xmb": []}
    for l in open(NET):
        t = l.split()
        if len(t) < 6 or not t[0].upper().startswith("X") or t[5] != "sg13_hv_nmos":
            continue
        d, g, s_ = base(t[1]), base(t[2]), base(t[3])
        ds = {d, s_}
        k = ("xm7" if g == "xvb.x1" and ds == {"vref_b", "vdda"} else "xm8" if g == "ibvb" and "vref_b" in ds else
             "xmt" if g == "ibvb" and "xvb.ns" in ds else "xmb" if g == "ibvb" and "ibvb" in ds else None)
        if k:
            out[k].append("@n.xbias.%s.nsg13_hv_nmos[ids]" % t[0].lower())
    assert all(out.values()), out
    return out


def ctl_op():
    pr = " ".join("i(vm_%s)" % p for p in PINS)
    pv = " ".join("v(%s_l)" % p for p in PINS)
    return """.control
op
print %s
print %s
print i(vmb) i(vmg) i(vmt) i(vdd) i(vload) v(vref) v(pbias) v(pcasc) v(por_n)
print %s
print v(xbias.xl_ib_afe_s1.d) v(xbias.xl_ib_is_a.d)
print v(vref_b) i(vmvr) i(vmvb) i(vmtv) i(vsba) i(vsbb)
print %s
print %s
.endc
""" % (pr, pv, " ".join("v(%s)" % n for n in POR_NODES), " ".join(sum(vb_devices().values(), [])),
       " ".join("v(%s)" % n for n in VB_NODES))


def op_rows(rundir, cases, mism_seeds=None):
    items, meta = [], []
    for c in cases:
        seeds = mism_seeds or [None]
        for s in seeds:
            name = "op_%s" % c + ("_s%03d" % s if s is not None else "")
            out = os.path.join(rundir, name)
            body = ".option seed=%d" % s if s is not None else ""
            open(out + ".cir", "w").write(deck(c, body, ctl_op(), mism=s is not None))
            items.append((out + ".cir", out + ".log")); meta.append((c, s, out))
    res = run_all(items)
    rows, fails = [], 0
    for (c, s, out), (_, rc, dt) in zip(meta, res):
        row = dict(case=c, rc=rc, seconds=round(dt, 1))
        if s is not None:
            row["seed"] = s
        try:
            d = parse_prints(out + ".log")
            row["i_uA"] = {p: d["i(vm_%s)" % p] * 1e6 for p in PINS}
            row["v_pin"] = {p: d["v(%s_l)" % p] for p in PINS}
            legs = sum(d["i(vm_%s)" % p] for p in PINS)
            row["idda_bias_uA"] = d["i(vmb)"] * 1e6
            row["idda_legs_uA"] = legs * 1e6
            row["idda_por_uA"] = (d["i(vmb)"] - legs) * 1e6
            row["idda_bgr_uA"] = d["i(vmg)"] * 1e6
            row["idda_t2f_uA"] = d["i(vmt)"] * 1e6
            row["idd_uA"] = -d["i(vdd)"] * 1e6
            row["iptat_uA"] = d["i(vload)"] * 1e6
            for k in ("v(vref)", "v(pbias)", "v(pcasc)", "v(por_n)") + tuple("v(%s)" % n for n in POR_NODES):
                row[k] = d[k]
            row["vds_leg_afe_s1"] = CORNERS[c][5] - d["v(xbias.xl_ib_afe_s1.d)"]
            row["vds_casc_afe_s1"] = d["v(xbias.xl_ib_afe_s1.d)"] - d["v(ib_afe_s1_l)"]
            # revision 2: VREF buffer
            vbd = vb_devices()
            i7, i8, it, ib = (sum(abs(d[v]) for v in vbd[k]) for k in ("xm7", "xm8", "xmt", "xmb"))
            row["vref_b"] = d["v(vref_b)"]
            row["vos_mV"] = (d["v(vref_b)"] - d["v(vref)"]) * 1e3
            row["i_vref_in_nA"] = d["i(vmvr)"] * 1e9
            row["i_load_vrefb_uA"] = (d["i(vmvb)"] + d["i(vmtv)"]) * 1e6
            row["i_t2f_vref_nA"] = d["i(vmtv)"] * 1e9
            row["i_ped_a_uA"] = d["i(vsba)"] * 1e6
            row["i_ped_b_uA"] = d["i(vsbb)"] * 1e6
            row["i_string_uA"] = (d["i(vmvb)"] - d["i(vsba)"] - d["i(vsbb)"]) * 1e6
            row["vb_i_m7_uA"] = i7 * 1e6; row["vb_i_tail_uA"] = it * 1e6; row["vb_i_bias_uA"] = ib * 1e6; row["vb_i_sink_uA"] = i8 * 1e6
            row["idda_vbuf_uA"] = (i7 + it + ib) * 1e6
            row["idda_por_uA"] = row["idda_bias_uA"] - row["idda_legs_uA"] - row["idda_vbuf_uA"]
            for n in VB_NODES:
                row["v(%s)" % n] = d["v(%s)" % n]
        except Exception as e:
            row["error"] = repr(e); fails += 1
        if rc != 0:
            fails += 1
        rows.append(row)
    return rows, fails


# ------------------------------------------------------------------ compliance
def ctl_comp(out, vmax):
    pr = " ".join("i(vm_%s)" % p for p in PINS)
    return """.control
set filetype=ascii
set wr_singlescale
set wr_vecnames
dc vsw 0 %g 0.01
wrdata %s.dat %s
.endc
""" % (vmax, out, pr)


def comp_suite(rundir, cases):
    items, meta = [], []
    for c in cases:
        out = os.path.join(rundir, "comp_%s" % c)
        open(out + ".cir", "w").write(deck(c, "", ctl_comp(out, CORNERS[c][5]), outs_mode="sweep"))
        items.append((out + ".cir", out + ".log")); meta.append((c, out))
    oprows, opf = op_rows(rundir, cases)
    res = run_all(items)
    rows, fails = [], opf
    for (c, out), (_, rc, dt), opr in zip(meta, res, oprows):
        row = dict(case=c, rc=rc, seconds=round(dt, 1), outputs={})
        try:
            d = read_cols(out + ".dat")
            v = d[list(d)[0]]
            for p in PINS:
                i = d["i(vm_%s)" % p]
                vp = opr["v_pin"][p]
                k0 = min(range(len(v)), key=lambda k: abs(v[k] - vp))
                i0 = i[k0]
                ok = [abs(x / i0 - 1) <= 0.01 for x in i]
                lo = k0
                while lo > 0 and ok[lo - 1]:
                    lo -= 1
                hi = k0
                while hi < len(v) - 1 and ok[hi + 1]:
                    hi += 1
                row["outputs"][p] = dict(v_pin=round(vp, 4), i_at_pin_uA=round(i0 * 1e6, 4), vmin_1pct=round(v[lo], 3),
                                         vmax_1pct=round(v[hi], 3), headroom_to_vmax=round(v[hi] - vp, 3))
        except Exception as e:
            row["error"] = repr(e); fails += 1
        if rc != 0:
            fails += 1
        rows.append(row)
    return dict(rows=rows, op=oprows), fails


# ------------------------------------------------------------------ startup
def ctl_tran(out, tstep, tend, tmax, vecs):
    return """.control
set filetype=ascii
set wr_singlescale
set wr_vecnames
tran %s %s 0 %s uic
let ilegs = %s
wrdata %s.dat %s
.endc
""" % (tstep, tend, TMAX, " + ".join("i(vm_%s)" % p for p in PINS), out, " ".join(vecs))


def settle_time(t, x, t0, tol):
    xf = x[-1]
    for k in range(len(t) - 1, -1, -1):
        if abs(x[k] - xf) > tol * abs(xf):
            return t[k] - t0 if t[k] >= t0 else 0.0
    return 0.0


def crossings(t, x, th):
    r, f = [], []
    for k in range(1, len(t)):
        if x[k - 1] < th <= x[k]:
            r.append(t[k - 1] + (th - x[k - 1]) / (x[k] - x[k - 1]) * (t[k] - t[k - 1]))
        elif x[k - 1] >= th > x[k]:
            f.append(t[k - 1] + (th - x[k - 1]) / (x[k] - x[k - 1]) * (t[k] - t[k - 1]))
    return r, f


def startup_suite(rundir, cases, ramps=(10e-6, 1e-3)):
    items, meta = [], []
    vecs = ["v(vdda)", "v(vdd)", "v(vref)", "v(pbias)", "v(por_n)", "v(vref_b)"] + ["i(vm_%s)" % p for p in PINS] + ["v(%s)" % n for n in POR_NODES[:5]]
    for c in cases:
        va, vd = CORNERS[c][5], CORNERS[c][6]
        for tr in ramps:
            tend = tr + 1.2e-3
            name = "su_%s_%s" % (c, "%gus" % (tr * 1e6))
            out = os.path.join(rundir, name)
            vsrc = "pwl(0 0 %g %g %g %g)" % (tr, va, tend, va)
            dsrc = "pwl(0 0 1u %g %g %g)" % (vd, tend, vd)
            ctl = ctl_tran(out, "50n", "%g" % tend, "%g" % min(2e-6, tr / 50), vecs)
            open(out + ".cir", "w").write(deck(c, "", ctl, vdda_src=vsrc, vdd_src=dsrc))
            items.append((out + ".cir", out + ".log")); meta.append((c, tr, out))
    res = run_all(items)
    rows, fails = [], 0
    for (c, tr, out), (_, rc, dt) in zip(meta, res):
        row = dict(case=c, ramp_s=tr, rc=rc, seconds=round(dt, 1))
        try:
            d = read_cols(out + ".dat")
            t = d[list(d)[0]]
            row["t99_us"] = {p: round(settle_time(t, d["i(vm_%s)" % p], tr, 0.01) * 1e6, 2) for p in PINS}
            row["t99_from_start_us"] = {p: round(settle_time(t, d["i(vm_%s)" % p], 0.0, 0.01) * 1e6, 2) for p in PINS}
            row["t99_vref_from_start_us"] = round(settle_time(t, d["v(vref)"], 0.0, 0.01) * 1e6, 2)
            rr = crossings(t, d["v(por_n)"], CORNERS[c][6] / 2)[0]
            row["por_n_max_before_release"] = round(max([v for tt, v in zip(t, d["v(por_n)"]) if not rr or tt < rr[0] - 1e-6] or [0]), 4)
            row["i_end_uA"] = {p: round(d["i(vm_%s)" % p][-1] * 1e6, 4) for p in PINS}
            row["overshoot_pct"] = {p: round((max(d["i(vm_%s)" % p]) / d["i(vm_%s)" % p][-1] - 1) * 100, 2) for p in PINS}
            row["vref_end"] = d["v(vref)"][-1]
            row["t99_vref_us"] = round(settle_time(t, d["v(vref)"], tr, 0.01) * 1e6, 2)
            # revision 2: buffered reference
            vb = d["v(vref_b)"]
            row["t99_vref_b_from_start_us"] = round(settle_time(t, vb, 0.0, 0.01) * 1e6, 2)
            row["t999_vref_b_from_start_us"] = round(settle_time(t, vb, 0.0, 0.001) * 1e6, 2)
            row["vref_b_end"] = vb[-1]
            row["vos_end_mV"] = round((vb[-1] - d["v(vref)"][-1]) * 1e3, 4)
            row["vref_b_overshoot_pct"] = round((max(vb) / vb[-1] - 1) * 100, 3)
            kp = [k for k in range(len(t)) if rr and abs(t[k] - rr[0]) < 2e-6]
            row["vref_b_dev_at_por_edge_mV"] = round(max(abs(vb[k] - vb[-1]) for k in kp) * 1e3, 3) if kp else None
            vd = CORNERS[c][6]
            r, f = crossings(t, d["v(por_n)"], vd / 2)
            row["por_n_rise_us"] = [round(x * 1e6, 2) for x in r]
            row["por_n_fall_us"] = [round(x * 1e6, 2) for x in f]
            row["por_n_end"] = d["v(por_n)"][-1]
        except Exception as e:
            row["error"] = repr(e); fails += 1
        if rc != 0:
            fails += 1
        rows.append(row)
    return rows, fails


# ------------------------------------------------------------------ psrr
def ctl_psrr(out):
    return """.control
set filetype=ascii
set wr_singlescale
set wr_vecnames
op
print i(vm_ib_afe_s1) i(vm_ib_is_a) i(vm_ib_adc_ref)
ac dec 20 10 100meg
wrdata %s.dat mag(i(vm_ib_afe_s1)) mag(i(vm_ib_is_a)) mag(i(vm_ib_adc_ref)) mag(v(pbias)) mag(v(vref))
.endc
""" % out


def psrr_suite(rundir, cases):
    items, meta = [], []
    for c in cases:
        out = os.path.join(rundir, "psrr_%s" % c)
        open(out + ".cir", "w").write(deck(c, "", ctl_psrr(out), vdda_src="dc %g ac 1" % CORNERS[c][5]))
        items.append((out + ".cir", out + ".log")); meta.append((c, out))
    res = run_all(items)
    rows, fails = [], 0
    for (c, out), (_, rc, dt) in zip(meta, res):
        row = dict(case=c, rc=rc, seconds=round(dt, 1))
        try:
            pr = parse_prints(out + ".log")
            d = read_cols(out + ".dat")
            f = d[list(d)[0]]
            keys = list(d)[1:]
            names = ["ib_afe_s1", "ib_is_a", "ib_adc_ref", "pbias", "vref"]
            for fq, lab in ((20e3, "20k"), (1e6, "1M"), (10.0, "dc")):
                k = min(range(len(f)), key=lambda j: abs(math.log(f[j] / fq)))
                for nm, key in zip(names, keys):
                    val = d[key][k]
                    if nm.startswith("ib"):
                        i0 = pr["i(vm_%s)" % nm]
                        row["%s_%s_nA_per_V" % (nm, lab)] = round(val * 1e9, 4)
                        row["%s_%s_dB" % (nm, lab)] = round(20 * math.log10(max(val / i0, 1e-30)), 2)
                    else:
                        row["%s_%s_dB" % (nm, lab)] = round(20 * math.log10(max(val, 1e-30)), 2)
        except Exception as e:
            row["error"] = repr(e); fails += 1
        if rc != 0:
            fails += 1
        rows.append(row)
    return rows, fails


# ------------------------------------------------------------------ stb (r1_bgr loops with the r1_bias + T2F load)
STB_CASES = ["tt", "ss", "ff", "sf", "fs", "ssx", "ffx"]


def stb_suite(rundir):
    from run_bgr import probe_netlist, curve_margins, CUTS
    text = open(BGR).read()
    items, meta = [], []
    toy = open(os.path.join(HERE, "tb_stb_toy.cir")).read().replace("@@RAW@@", os.path.join(rundir, "toy"))
    open(os.path.join(rundir, "toy.cir"), "w").write(toy)
    items.append((os.path.join(rundir, "toy.cir"), os.path.join(rundir, "toy.log"))); meta.append(("toy",))
    moved = {}
    for cut in CUTS:
        ptxt, mv = probe_netlist(text, cut[0])
        moved[cut[0]] = mv
        pn = os.path.join(rundir, "bgr_probe_%s.spice" % cut[0]); open(pn, "w").write(ptxt)
        net = cut[1] if cut[1] in ("vdd", "vss", "vref", "iptat", "pbias", "pcasc", "vbe", "dvbe") else "xbgr." + cut[1]
        for c in STB_CASES:
            out = os.path.join(rundir, "stb_%s_%s" % (c, cut[0]))
            ctl = """.control
set filetype=ascii
set wr_singlescale
set wr_vecnames
op
print v(vref) i(vm_ib_afe_s1)
ac dec 20 0.1 10g
alterparam vinj=0
alterparam iinj=1
reset
ac dec 20 0.1 10g
let v1 = ac1.v(%s)
let i1 = ac1.i(v.xbgr.vprobe)
let v2 = ac2.v(%s)
let i2 = ac2.i(v.xbgr.vprobe)
let tl = -1/(1-1/(2*(i1*v2-v1*i2)+v1+i2))
let tre = real(tl)
let tim = imag(tl)
wrdata %s.dat tre tim
.endc
""" % (net, net, out)
            open(out + ".cir", "w").write(deck(c, ".param vinj=1 iinj=0", ctl, bgr_net=pn))
            items.append((out + ".cir", out + ".log")); meta.append(("stb", c, cut[0], out))
    res = run_all(items)
    rows, fails, summ = [], 0, {}
    for mt, (_, rc, dt) in zip(meta, res):
        if mt[0] == "toy":
            for l in open(os.path.join(rundir, "toy.log")):
                if "TOYROW" in l:
                    summ["toy"] = l.strip()
            if rc != 0:
                fails += 1
            continue
        _, c, cut, out = mt
        row = dict(case=c, cut=cut, rc=rc, seconds=round(dt, 1))
        try:
            d = read_cols(out + ".dat")
            k = list(d)
            row.update(curve_margins(d[k[0]], d[k[1]], d[k[2]]))
            row["pass_pm60"] = True if row["pm_deg"] is None else row["pm_deg"] >= 60
            row["pass_gm10"] = True if row["gm_db"] is None else row["gm_db"] >= 10
            pr = parse_prints(out + ".log")
            row["vref_op"] = pr.get("v(vref)")
        except Exception as e:
            row["error"] = repr(e); fails += 1
        if rc != 0:
            fails += 1
        rows.append(row)
    summ["rows"] = rows
    summ["moved_pins"] = {k: len(v) for k, v in moved.items()}
    return summ, fails


# ------------------------------------------------------------------ thresholds (slow triangle ramps)
def thr_src(c):
    va, vd = CORNERS[c][5], CORNERS[c][6]
    # 0-0.2 ms settle; VDDA va -> 2.40 V (1 ms) -> 2.95 V (1 ms) -> va; then VDD vd -> 0.85 V (1 ms) -> 1.10 V (1 ms) -> vd
    a = "pwl(0 %g 0.2m %g 1.2m 2.40 2.2m 2.95 2.3m %g 6m %g)" % (va, va, va, va)
    d = "pwl(0 %g 2.5m %g 3.5m 0.85 4.5m 1.10 4.6m %g 6m %g)" % (vd, vd, vd, vd)
    return a, d


def thr_metrics(d):
    t = d[list(d)[0]]
    va = d["v(vdda)"]; vd = d["v(vdd)"]
    ga = d["v(xbias.xpor.gooda)"]; gd = d["v(xbias.xpor.goodd)"]
    half = [x / 2 for x in va]
    da = [g - h for g, h in zip(ga, half)]
    dd = [g - h for g, h in zip(gd, half)]
    ra, fa = crossings(t, da, 0.0)
    rd, fd = crossings(t, dd, 0.0)
    at = lambda tt, x: x[min(range(len(t)), key=lambda k: abs(t[k] - tt))]
    r = dict(n_gooda_rise=len(ra), n_gooda_fall=len(fa), n_goodd_rise=len(rd), n_goodd_fall=len(fd))
    if fa: r["vdda_fall_V"] = round(at(fa[0], va), 4)
    if ra: r["vdda_rise_V"] = round(at(ra[0], va), 4)
    if fd: r["vdd_fall_V"] = round(at(fd[0], vd), 4)
    if rd: r["vdd_rise_V"] = round(at(rd[0], vd), 4)
    return r


def thr_suite(rundir, cases, seeds=None):
    items, meta = [], []
    vecs = ["v(vdda)", "v(vdd)", "v(xbias.xpor.gooda)", "v(xbias.xpor.goodd)", "v(por_n)"]
    for c in cases:
        for s in (seeds or [None]):
            a, dsrc = thr_src(c)
            name = "thr_%s" % c + ("_s%03d" % s if s is not None else "")
            out = os.path.join(rundir, name)
            body = ".option seed=%d" % s if s is not None else ""
            ctl = """.control
set filetype=ascii
set wr_singlescale
set wr_vecnames
tran 0.2u 4.6m 0 0.2u
wrdata %s.dat %s
.endc
""" % (out, " ".join(vecs))
            open(out + ".cir", "w").write(deck(c, body, ctl, mism=s is not None, vdda_src=a, vdd_src=dsrc))
            items.append((out + ".cir", out + ".log")); meta.append((c, s, out))
    res = run_all(items)
    rows, fails = [], 0
    for (c, s, out), (_, rc, dt) in zip(meta, res):
        row = dict(case=c, rc=rc, seconds=round(dt, 1))
        if s is not None:
            row["seed"] = s
        try:
            row.update(thr_metrics(read_cols(out + ".dat")))
            for k in ("vdda_fall_V", "vdda_rise_V", "vdd_fall_V", "vdd_rise_V"):
                if k not in row:
                    raise ValueError("missing " + k)
        except Exception as e:
            row["error"] = repr(e); fails += 1
        if rc != 0:
            fails += 1
        rows.append(row)
    return rows, fails


# ------------------------------------------------------------------ POR power-up / brown-out
def por_srcs(c, kind, tr):
    va, vd = CORNERS[c][5], CORNERS[c][6]
    if kind == "upA":    # VDD first (on at 1 us), VDDA 0 -> va in tr, hold 1 ms, va -> 0 in tr
        t1 = tr; t2 = t1 + 1e-3; t3 = t2 + tr
        return "pwl(0 0 %g %g %g %g %g 0 %g 0)" % (t1, va, t2, va, t3, t3 + 0.2e-3), "pwl(0 0 1u %g %g %g)" % (vd, t3 + 0.2e-3, vd), t3 + 0.2e-3
    if kind == "upD":    # VDDA first (10 us ramp), VDD 0 from 0.3 ms -> vd in tr, hold 1 ms, -> 0 in tr
        t0 = 0.3e-3; t1 = t0 + tr; t2 = t1 + 1e-3; t3 = t2 + tr
        return "pwl(0 0 10u %g %g %g)" % (va, t3 + 0.2e-3, va), "pwl(0 0 %g 0 %g %g %g %g %g 0 %g 0)" % (t0, t1, vd, t2, vd, t3, t3 + 0.2e-3), t3 + 0.2e-3
    if kind == "bo":     # both on (10 us); dips: VDD -> 0.90 V at 1.0 ms, VDD -> 0.975 V at 1.5 ms, VDDA -> 2.50 V at 2.0 ms (20 us, 1 us edges)
        def dip(base, lo, t):
            return "%g %g %g %g %g %g %g %g" % (t, base, t + 1e-6, lo, t + 21e-6, lo, t + 22e-6, base)
        a = "pwl(0 0 10u %g %s 2.6m %g)" % (va, dip(va, 2.50, 2.0e-3), va)
        d = "pwl(0 0 10u %g %s %s 2.6m %g)" % (vd, dip(vd, 0.90, 1.0e-3), dip(vd, 0.975, 1.5e-3), vd)
        return a, d, 2.6e-3
    raise KeyError(kind)


def por_suite(rundir, cases, ramps=(1e-3, 10e-3), kinds=("upA", "upD", "bo")):
    items, meta = [], []
    vecs = ["v(vdda)", "v(vdd)", "v(por_n)", "i(vmb)", "i(vdd)", "ilegs", "v(pbias)", "v(vref)"] + ["v(%s)" % n for n in POR_NODES[:5]]
    jobs = [(c, k, tr) for c in cases for k in ("upA", "upD") if k in kinds for tr in ramps] + \
        [(c, "bo", 0) for c in cases if "bo" in kinds]
    for c, kind, tr in jobs:
        a, d, tend = por_srcs(c, kind, tr)
        name = "por_%s_%s_%s" % (c, kind, "%gms" % (tr * 1e3))
        out = os.path.join(rundir, name)
        ctl = ctl_tran(out, "1u", "%g" % tend, "2u", vecs)
        open(out + ".cir", "w").write(deck(c, "", ctl, vdda_src=a, vdd_src=d))
        items.append((out + ".cir", out + ".log")); meta.append((c, kind, tr, out))
    res = run_all(items)
    rows, fails = [], 0
    for (c, kind, tr, out), (_, rc, dt) in zip(meta, res):
        row = dict(case=c, kind=kind, ramp_s=tr, rc=rc, seconds=round(dt, 1))
        try:
            d = read_cols(out + ".dat")
            t = d[list(d)[0]]
            vdn = CORNERS[c][6]
            r, f = crossings(t, d["v(por_n)"], vdn / 2)
            row["por_n_rise_ms"] = [round(x * 1e3, 4) for x in r]
            row["por_n_fall_ms"] = [round(x * 1e3, 4) for x in f]
            rr, rf = crossings(t, d["v(xbias.xpor.rst)"], 0.9)  # rst is a VDDA-domain signal: low = both supplies good
            row["rst_fall_ms"] = [round(x * 1e3, 4) for x in rf]
            at = lambda tt, x: x[min(range(len(t)), key=lambda k: abs(t[k] - tt))]
            if r and rf:
                prior = [x for x in rf if x <= r[0]]
                if prior:
                    row["delay_us"] = round((r[0] - prior[-1]) * 1e6, 2)
                row["vdda_at_rst_fall"] = round(at(rf[0], d["v(vdda)"]), 4)
                row["vdd_at_rst_fall"] = round(at(rf[0], d["v(vdd)"]), 4)
            if f:
                row["vdda_at_por_fall"] = round(at(f[0], d["v(vdda)"]), 4)
                row["vdd_at_por_fall"] = round(at(f[0], d["v(vdd)"]), 4)
            # steady current with both supplies up and por_n high: average over the hold (r1_bias minus legs)
            if r:
                k = [j for j in range(len(t)) if t[j] > r[0] + 50e-6 and t[j] < r[0] + 200e-6]
                if k:
                    ib = sum(d["i(vmb)"][j] for j in k) / len(k)
                    legs = sum(d["ilegs"][j] for j in k) / len(k)
                    row["idda_por_uA"] = round((ib - legs) * 1e6, 3)
                    row["idd_por_uA"] = round(-sum(d["i(vdd)"][j] for j in k) / len(k) * 1e6, 4)
            row["por_n_max_before_release"] = round(max([v for tt, v in zip(t, d["v(por_n)"]) if not r or tt < r[0] - 1e-6] or [0]), 4)
        except Exception as e:
            row["error"] = repr(e); fails += 1
        if rc != 0:
            fails += 1
        rows.append(row)
    return rows, fails


# ------------------------------------------------------------------ main
def git_rev():
    try:
        return subprocess.check_output(["git", "-C", REPO, "rev-parse", "HEAD"], stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        return "unknown (git not in container)"


def ngspice_version():
    try:
        out = subprocess.check_output(["ngspice", "-v"], stderr=subprocess.STDOUT).decode()
        return [l.strip() for l in out.splitlines() if "ngspice-" in l][0]
    except Exception:
        return "unknown"


QUESTIONS = {
    "op": "Output currents, consumer pin voltages and supply currents at the corners (DC, real loads).",
    "comp": "Output compliance: voltage range where each output stays within 1 % of its value at the consumer pin voltage.",
    "mc": "Mismatch (50 samples, tt/27 C/3.3 V): sigma of every output current and of the POR reference.",
    "startup": "Start-up with r1_bgr from 0 V, VDDA ramps 10 us and 1 ms: 1 % settling of every output, por_n release.",
    "psrr": "Supply rejection of representative output currents (AFE 10 uA, isense 5 uA, ADC ref 5 uA) at 20 kHz and 1 MHz.",
    "stb": "r1_bgr loop gain (5 cuts) with the r1_bias + T2F + consumer loads attached, 7 corners; PM >= 60 deg, GM >= 10 dB.",
    "thr": "POR thresholds (VDDA/VDD rising and falling) from slow triangle ramps (0.55 V/ms and 0.35 V/ms).",
    "mcthr": "POR thresholds under mismatch (seeds, tt).",
    "retry": "",
    "por": "POR power-up (VDD first / VDDA first) with 1 ms and 10 ms ramps, ramp-down, brown-out dips: thresholds, delay, transitions, current.",
}


def main():
    suite, runid = sys.argv[1], sys.argv[2]
    args = dict(a.split("=", 1) for a in sys.argv[3:] if "=" in a)
    assert ROOT, "G1_RESULTS_ROOT not set"
    rundir = os.path.join(ROOT, "r1_bias", runid)
    os.makedirs(rundir, exist_ok=True)
    assert sha(BGR) == BGR_SHA, "r1_bgr netlist sha256 mismatch"
    assert sha(T2F) == T2F_SHA, "r1_t2f netlist sha256 mismatch"
    cases = args.get("cases", ",".join(MAIN3)).split(",")
    global NET
    if "pex" in args:
        # post-layout: the extracted r1_bias (layout/pex_build.py, same pins, main nodes keep the hierarchical names)
        # replaces the schematic subcircuit; view rc (full RC), c (wiring R shorted) or dev (layout devices + MIM only)
        sfx = {"rc": "", "c": "_c", "dev": "_dev"}[args.get("view", "rc")]
        NET = os.path.join(ROOT, "r1_bias", args["pex"], "r1_bias_pex%s.spice" % sfx)
        assert os.path.exists(NET), "no extracted netlist for pex=%s" % args["pex"]
    global CONV, CONV2
    CONV = args.get("conv") in ("1", "2")
    CONV2 = args.get("conv") == "2"
    seeds_arg = [int(x) for x in args["seeds"].split(",")] if "seeds" in args else None
    ramps_arg = tuple(float(x) for x in args["ramps"].split(",")) if "ramps" in args else None
    t0 = time.time()
    if suite == "op":
        res, fails = op_rows(rundir, cases)
    elif suite == "comp":
        res, fails = comp_suite(rundir, cases)
    elif suite == "mc":
        n = int(args.get("n", "50"))
        res, fails = op_rows(rundir, ["tt"], mism_seeds=seeds_arg or list(range(1, n + 1)))
        ok = [r for r in res if "i_uA" in r]
        if len(ok) < 2:
            res = dict(n_ok=len(ok), rows=res)
            ok = None
        stats = {}
        for p in (PINS + ["vrh", "vrl"]) if ok else []:
            xs = [r["i_uA"][p] for r in ok] if p in PINS else [r["v(xbias.xpor.%s)" % p] for r in ok]
            m = sum(xs) / len(xs); s = (sum((x - m) ** 2 for x in xs) / (len(xs) - 1)) ** 0.5
            stats[p] = dict(mean=m, sigma=s, sigma_pct=100 * s / m, min=min(xs), max=max(xs))
        ratios = {}
        for p in PINS if ok else []:
            xs = [r["i_uA"][p] / r["iptat_uA"] for r in ok]
            m = sum(xs) / len(xs); s = (sum((x - m) ** 2 for x in xs) / (len(xs) - 1)) ** 0.5
            ratios[p] = dict(mean=m, sigma_pct=100 * s / m)
        if ok:
            ip = [r["iptat_uA"] for r in ok]; m = sum(ip) / len(ip)
            stats["iptat"] = dict(mean=m, sigma_pct=100 * (sum((x - m) ** 2 for x in ip) / (len(ip) - 1)) ** 0.5 / m)
            vs = [r["vos_mV"] for r in ok]; m = sum(vs) / len(vs); sd = (sum((x - m) ** 2 for x in vs) / (len(vs) - 1)) ** 0.5
            stats["vos_mV"] = dict(mean=m, sigma=sd, abs_mean_plus_3sigma=abs(m) + 3 * sd, min=min(vs), max=max(vs))
            res = dict(stats=stats, ratio_to_iptat=ratios, n_ok=len(ok), n=n, rows=res)
    elif suite == "startup":
        res, fails = startup_suite(rundir, cases, ramps=ramps_arg or (10e-6, 1e-3))
    elif suite == "psrr":
        res, fails = psrr_suite(rundir, cases)
    elif suite == "stb":
        res, fails = stb_suite(rundir)
    elif suite == "thr":
        res, fails = thr_suite(rundir, cases)
    elif suite == "mcthr":
        n = int(args.get("n", "30"))
        res, fails = thr_suite(rundir, ["tt"], seeds=list(range(1, n + 1)))
        ok = [r for r in res if "error" not in r]
        st = {}
        for k in ("vdda_rise_V", "vdda_fall_V", "vdd_rise_V", "vdd_fall_V"):
            xs = [r[k] for r in ok]
            m = sum(xs) / len(xs); s = (sum((x - m) ** 2 for x in xs) / (len(xs) - 1)) ** 0.5
            st[k] = dict(mean=m, sigma=s, min=min(xs), max=max(xs))
        res = dict(stats=st, n_ok=len(ok), n=n, rows=res)
    elif suite == "por":
        res, fails = por_suite(rundir, cases, ramps=ramps_arg or (1e-3, 10e-3),
                               kinds=tuple(args.get("kinds", "upA,upD,bo").split(",")))
    else:
        raise SystemExit("unknown suite " + suite)
    summary = dict(run_id=runid, suite=suite, question=QUESTIONS.get(suite), args=args,
                   command="G1_CPUSET=116-119 G1_WORKDIR=designs/r1-joint/blocks/r1_bias/sim G1_RESULTS_ROOT=<G1_RESULTS_ROOT> "
                           "flow/run.sh python3 run_bias.py %s %s %s" % (suite, runid, " ".join("%s=%s" % kv for kv in args.items())),
                   r1_bias_netlist=("<G1_RESULTS_ROOT>/r1_bias/%s/%s" % (args["pex"], os.path.basename(NET))) if "pex" in args
                   else "designs/r1-joint/blocks/r1_bias/schematic/r1_bias.spice",
                   pdk_commit=PDK_COMMIT, ngspice=ngspice_version(), git_head=git_rev(),
                   netlist_sha256=dict(r1_bias=sha(NET), r1_bgr=sha(BGR), r1_t2f=sha(T2F), loads=sha(LOADS), vrefb_loads=sha(VBLOADS)),
                   raw="<G1_RESULTS_ROOT>/r1_bias/%s/" % runid, seconds=round(time.time() - t0, 1),
                   failed_jobs=fails, result=res)
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    json.dump(summary, open(os.path.join(HERE, "results", runid + ".json"), "w"), indent=1, default=str)
    rd = os.path.join(HERE, "runs", runid)
    os.makedirs(rd, exist_ok=True)
    runjson = {k: v for k, v in summary.items() if k != "result"}
    runjson["summary"] = "sim/results/%s.json" % runid
    runjson["disposition"] = "pending review" if fails == 0 else "failed: %d job(s) failed or unparsed" % fails
    json.dump(runjson, open(os.path.join(rd, "run.json"), "w"), indent=1)
    print("suite", suite, "run", runid, "failed jobs", fails)
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()

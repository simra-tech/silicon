# SPDX-License-Identifier: Apache-2.0
"""r1_top try g, chip-level extraction (track T11), step 4: checks (a), (b), (c) and the reduction error.

  python3 top_checks.py <run dir asm-20261028-g3> <wire dir> <rnet typ json> <rnet max json> <netlist dir> <out dir>

(a) Connectivity: r1_top_rc and r1_top_pex of r1_top_g_pex.spice are read back; every resistor is shorted (union
    find); every macro pin of the instance lines of r1_top_pex lands in one group; each group must hold the macro pins
    of exactly one CDL net of r1_top_g.cdl and every CDL net must be one group (no open, no short).
(b) Supply DC: ngspice operating point of r1_top_rc (typ and max networks) with the block currents of
    flow/supply_g_rnet.py at the macro supply pins, r1_ctrl_top 40.25 mA over its 63 grid points (parameter
    ictrl_p), pads VDD, VSS, VDDA at 0 V; compared with reports/supply_g.md (limit 10 %).
(c) Per-net R and C: R = largest effective resistance between two ports of the net (supply nets: from the bond
    pads to the farthest port); C = grounded + coupling C of the net (full network). OSC_CLK skew (ADC clk pin
    against ctrl clk pin): Elmore delay from the osc pin with the pin loads of flow/clk_skew_g.py (ADC 50 fF, ctrl
    5 fF; coupling C counted to ground), and an ngspice transient of the extracted OSC_CLK network (250 ps edge).
    AFE -> ADC pair imbalance, VREF_B line.
(e) Reduction error: the same quantities on r1_top_g_pex_red.spice for OSC_CLK, the AFE output pairs and VREF_B.
Outputs: <out>/checks.json, <out>/checks.log, decks and ngspice logs in <out>/.
"""
import csv
import json
import os
import re
import subprocess
import sys
from collections import defaultdict

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spl

RUN, WD, RTYP, RMAX, ND, OUT = sys.argv[1:7]
os.makedirs(OUT, exist_ok=True)
LOG = open(os.path.join(OUT, "checks.log"), "w")


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    LOG.write(s + "\n")
    LOG.flush()


def norm(p):
    return re.sub(r"_+$", "", re.sub(r"[\[\]<>]", "_", p.lower()))


def read_spice(path):
    sub, cur, lines = {}, None, []
    for raw in open(path):
        raw = raw.rstrip("\n")
        if raw.startswith("+") and lines:
            lines[-1] += " " + raw[1:]
        else:
            lines.append(raw)
    for ln in lines:
        t = ln.split()
        if not t or t[0].startswith("*"):
            continue
        if t[0].lower() == ".subckt":
            cur = t[1]
            pins = [x for x in t[2:] if "=" not in x and x != "params:"]
            sub[cur] = {"pins": pins, "el": []}
        elif t[0].lower() == ".ends":
            cur = None
        elif cur:
            sub[cur]["el"].append(t)
    return sub


res = {}
# ---------------- (a) connectivity of the netlist itself
NL = read_spice(os.path.join(ND, "r1_top_g_pex.spice"))
CDL = read_spice(os.path.join(RUN, "lvs", "r1_top_g.cdl"))
par = {}


def find(x):
    par.setdefault(x, x)
    while par[x] != x:
        par[x] = par[par[x]]
        x = par[x]
    return x


def union(a, b):
    ra, rb = find(a), find(b)
    if ra != rb:
        par[ra] = rb


rc = NL["r1_top_rc"]
for t in rc["el"]:
    if t[0][0] in "Rr":
        union(t[1], t[2])
wrap = NL["r1_top_pex"]
xrc = [t for t in wrap["el"] if t[0] == "Xrc"][0]
toks = [x for x in xrc[1:] if "=" not in x]
rcpins = rc["pins"]
assert len(toks) - 1 == len(rcpins), (len(toks), len(rcpins))
wnode_group = {w: find(p) for w, p in zip(toks[:-1], rcpins)}
# CDL expectation
cdl_top = [t for t in CDL["r1_top"]["el"] if t[0][0] in "Xx"]
exp = defaultdict(set)
for t in cdl_top:
    tk = [x for x in t[1:] if x != "/"]
    cell, nets = tk[-1], tk[:-1]
    for pn, n in zip(CDL[cell]["pins"], nets):
        exp[n].add("%s/%s" % (t[0][1:], norm(pn)))
got_group = defaultdict(set)
pin_group = {}
for t in wrap["el"]:
    if t[0] == "Xrc" or t[0][0] not in "Xx":
        continue
    inst, cell, nodes = t[0][1:], t[-1], t[1:-1]
    if cell.startswith("sg13g2_IOPad"):
        continue
    for pn, n in zip(CDL[cell]["pins"], nodes):
        key = "%s/%s" % (inst, norm(pn))
        g = wnode_group.get(n, "nc:" + n)
        pin_group[key] = g
        got_group[g].add(key)
opens, shorts, ok = [], [], 0
for n, pins in exp.items():
    gs = set(pin_group.get(p, "missing:" + p) for p in pins)
    if len(gs) > 1:
        opens.append({"net": n, "groups": len(gs), "pins": sorted(pins)[:6]})
    else:
        ok += 1
for g, pins in got_group.items():
    nets = set(n for n, ps in exp.items() if ps & pins)
    if len(nets) > 1:
        shorts.append({"nets": sorted(nets)})
nc_expected = [n for n, pins in exp.items() if len(pins) == 1]
res["a_connectivity"] = {"cdl_nets_with_macro_pins": len(exp), "nets_one_group": ok, "opens": opens, "shorts": shorts,
                         "single_pin_cdl_nets": sorted(nc_expected),
                         "pass": not opens and not shorts}
log("(a) CDL nets", len(exp), "one group", ok, "opens", len(opens), "shorts", len(shorts))
for o in opens:
    log("   open", o)
for s in shorts:
    log("   short", s)

# ---------------- (b) supply DC with ngspice
I_VSS = {"u_ctrl": None, "u_afe": 2.00, "u_adc": 1.97, "u_isense": 1.588, "u_safe": 0.418, "u_bias": 0.196,
         "u_bgr": 0.080, "u_t2f": 0.0625, "u_osc": 0.317}
I_VDD = {"u_adc": 0.870, "u_isense": 1.138, "u_osc": 0.317, "u_bias": 0.05}
I_VDDA = {"u_afe": 2.00, "u_adc": 1.102, "u_isense": 0.450, "u_safe": 0.418, "u_bgr": 0.080, "u_bias": 0.196,
          "u_t2f": 0.0625}
SUPPIN = {"VSS": {"u_afe": "vss", "u_adc": "vss", "u_isense": "vss", "u_safe": "vss", "u_bias": "vss", "u_bgr": "vss",
                  "u_t2f": "vss", "u_osc": "vss"},
          "VDD": {"u_adc": "vdd", "u_isense": "vdd", "u_osc": "vdd", "u_bias": "vdd"},
          "VDDA": {"u_afe": "vdd", "u_adc": "vdda", "u_isense": "vdda", "u_safe": "vdda", "u_bgr": "vdd", "u_bias": "vdda",
                   "u_t2f": "vdd"}}
build = json.load(open(os.path.join(ND, "netlist_build.json")))
PORTNET = {}
for row in csv.reader(open(os.path.join(ND, "pin_map.csv"))):
    PORTNET[row[0]] = row[4]
PORTNET.update({"u_ctrl__vdd": "VDD", "u_ctrl__vss": "VSS"})
GRID = build["ctrl_grid"]


def run_ng(deck, name):
    f = os.path.join(OUT, name + ".cir")
    open(f, "w").write(deck)
    o = subprocess.run(["ngspice", "-b", f], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       universal_newlines=True).stdout
    open(os.path.join(OUT, name + ".log"), "w").write(o)
    v = {}
    for ln in o.splitlines():
        m = re.match(r"\s*(\S+)\s*=\s*([-+0-9.eE]+)", ln)
        if m:
            v[m.group(1).lower()] = float(m.group(2))
    return v, o


def dc_deck(spice, mode):
    L = ["* T11 check (b): supply DC on the extracted chip network (%s)" % mode, ".include %s" % spice,
         ".options rshunt=1e9"]
    L.append("Xrc " + " ".join(rcpins) + " r1_top_rc ictrl_p=%s" % ("40.25m" if mode == "all" else "0"))
    if mode == "all":
        for nm in ("VDD", "VSS", "VDDA", "IOVDD", "IOVSS"):
            L.append("V%s %s 0 0" % (nm, nm))
        for inst, pin in SUPPIN["VSS"].items():
            L.append("I%s_vss 0 %s__%s %gm" % (inst, inst, pin, I_VSS[inst]))
        for inst, pin in SUPPIN["VDD"].items():
            L.append("I%s_vdd %s__%s 0 %gm" % (inst, inst, pin, I_VDD[inst]))
        for inst, pin in SUPPIN["VDDA"].items():
            L.append("I%s_vdda %s__%s 0 %gm" % (inst, inst, pin, I_VDDA[inst]))
    else:   # path resistance isense VSS pin -> bgr VSS pin, pads open
        for nm in ("VDD", "VDDA", "IOVDD", "IOVSS"):
            L.append("V%s %s 0 0" % (nm, nm))
        L.append("Vbgr u_bgr__vss 0 0")
        L.append("Itest 0 u_isense__vss 1m")
    L.append("Vsub sub 0 0")
    # signal nets carry no DC current here: one 1 kOhm to ground per signal port removes the floating subnetworks
    for k, q in enumerate(rcpins):
        if PORTNET.get(q) not in ("VDD", "VSS", "VDDA", "IOVDD", "IOVSS") and q != "sub":
            L.append("Rgnd%d %s 0 1k" % (k, q))
    probes = ["u_isense__vss", "u_bgr__vss", "u_afe__vss", "u_afe__vdd", "u_adc__vss", "u_adc__vdd", "u_adc__vdda",
              "u_isense__vdd", "u_isense__vdda", "u_osc__vss", "u_osc__vdd", "u_bias__vdd", "u_bias__vdda", "u_bgr__vdd",
              "u_safe__vdda", "u_t2f__vdd"]
    L += [".control", "op"]
    for i in range(0, len(probes), 6):
        L.append("print " + " ".join("v(%s)" % p for p in probes[i:i + 6]))
    g = ["xrc.%s" % a for a, b in GRID] + ["xrc.%s" % b for a, b in GRID]
    for i in range(0, len(g), 6):
        L.append("print " + " ".join("v(%s)" % p for p in g[i:i + 6]))
    L += [".endc", ".end"]
    return "\n".join(L) + "\n", probes


ref = {"typ": {"vdd_ctrl_worst": 22.8, "vss_ctrl_worst": 46.1, "vdda_afe_far": 45.3, "isense_bgr_offset": 5.34,
               "path_R": 1.494},
       "max": {"vdd_ctrl_worst": 30.6, "vss_ctrl_worst": 63.6, "vdda_afe_far": 57.2, "isense_bgr_offset": 6.78,
               "path_R": 2.021}}
# T8h (try h): R1_PEX_SUPPLY_REF=<supply_h*.json of flow/supply_h.py> replaces the try-g reference values above
# (the h networks have lower losses); the row key stays "supply_g" for the readers, the source is recorded.
REF_SRC = "reports/supply_g.md (try g)"
if os.environ.get("R1_PEX_SUPPLY_REF"):
    _sj = json.load(open(os.environ["R1_PEX_SUPPLY_REF"]))["summary"]
    ref = {c: {"vdd_ctrl_worst": _sj[c]["ctrl_vdd_drop_worst_mV"], "vss_ctrl_worst": _sj[c]["ctrl_vss_rise_worst_mV"],
               "vdda_afe_far": _sj[c]["macro_loss"]["afe (VDDA)"]["supply_drop_mV"],
               "isense_bgr_offset": _sj[c]["isense_minus_bgr_mV"]["all"], "path_R": _sj[c]["isense_bgr_path_R_ohm"]}
           for c in ("typ", "max")}
    REF_SRC = os.path.basename(os.environ["R1_PEX_SUPPLY_REF"])
res["b_supply"] = {"reference_source": REF_SRC}
for corner, rj in (("typ", RTYP), ("max", RMAX)):
    spice = os.path.join(ND, "r1_top_g_pex.spice") if corner == "typ" else os.path.join(ND, "max", "r1_top_g_pex.spice")
    if not os.path.exists(spice):
        log("(b)", corner, "netlist not found, not run")
        res["b_supply"][corner] = "not run"
        continue
    d, probes = dc_deck(spice, "all")
    v, o = run_ng(d, "dc_supply_%s" % corner)
    gv = [v.get("v(xrc.%s)" % a.lower()) for a, b in GRID]
    gs = [v.get("v(xrc.%s)" % b.lower()) for a, b in GRID]
    if None in gv or None in gs or "v(u_afe__vdd)" not in v:
        log("(b)", corner, "ngspice output incomplete; see dc_supply_%s.log" % corner)
        res["b_supply"][corner] = "failed to run"
        continue
    got = {"vdd_ctrl_worst": -min(gv) * 1e3, "vss_ctrl_worst": max(gs) * 1e3, "vdda_afe_far": -v["v(u_afe__vdd)"] * 1e3,
           "isense_bgr_offset": (v["v(u_isense__vss)"] - v["v(u_bgr__vss)"]) * 1e3}
    d2, _ = dc_deck(spice, "path")
    v2, _ = run_ng(d2, "dc_path_%s" % corner)
    got["path_R"] = v2.get("v(u_isense__vss)", float("nan")) / 1e-3
    rows = {}
    for k, x in got.items():
        r = ref[corner][k]
        rows[k] = {"extracted": round(x, 3), "supply_g": r, "delta_pct": round(100 * (x - r) / r, 2),
                   "pass": abs(x - r) / r <= 0.10}
    res["b_supply"][corner] = {"rows": rows, "all_port_mV": {p: round(v.get("v(%s)" % p, float("nan")) * 1e3, 3)
                                                            for p in probes}}
    for k, r in rows.items():
        log("(b) %s %-18s extracted %8.3f  supply_g %7.3f  delta %+6.2f %%  %s" % (
            corner, k, r["extracted"], r["supply_g"], r["delta_pct"], "pass" if r["pass"] else "FAIL"))

# ---------------- (c) per-net R and C, skew, pairs, VREF_B
RN = json.load(open(RTYP))["nets"]
CN = json.load(open(os.path.join(ND, "c_nodes.json")))
node_net = {}
for net, d in RN.items():
    for z in d["nodes"]:
        node_net[z[0]] = net
Cnet = defaultdict(float)
Cgnet = defaultdict(float)
Ccnet = defaultdict(float)
for n, c in CN["Cg"].items():
    Cnet[node_net[n]] += c
    Cgnet[node_net[n]] += c
pairC = defaultdict(float)
for a, b, c in CN["Cc"]:
    Cnet[node_net[a]] += c
    Cnet[node_net[b]] += c
    Ccnet[node_net[a]] += c
    Ccnet[node_net[b]] += c
    x, y = sorted((node_net[a], node_net[b]))
    pairC[(x, y)] += c


def lap(net):
    d = RN[net]
    idx = {z[0]: i for i, z in enumerate(d["nodes"])}
    n = len(idx)
    rows, cols, vals = [], [], []
    for a, b, r in d["elements"]:
        g = 1.0 / r
        i, j = idx[a], idx[b]
        rows += [i, j, i, j]
        cols += [i, j, j, i]
        vals += [g, g, -g, -g]
    return idx, sp.csr_matrix((vals, (rows, cols)), shape=(n, n))


def reff(net, srcs, dst):
    """effective resistance from the node set srcs (shorted) to node dst"""
    idx, Gm = lap(net)
    n = Gm.shape[0]
    s = [idx[x] for x in srcs]
    keep = [i for i in range(n) if i != s[0]]
    # short the sources: add a large conductance between them and s[0], ground s[0]
    G = Gm.tolil()
    for k in s[1:]:
        G[k, k] += 1e9
        G[s[0], s[0]] += 1e9
        G[k, s[0]] -= 1e9
        G[s[0], k] -= 1e9
    G = G.tocsr()[keep][:, keep]
    b = np.zeros(len(keep))
    j = keep.index(idx[dst])
    b[j] = 1.0
    x = spl.spsolve(G.tocsc(), b)
    return x[j]


SUPPLY = ("VDD", "VSS", "VDDA", "IOVDD", "IOVSS")
table = []
for net, d in RN.items():
    ports = d["ports"]
    pn = sorted(set(ports.values()))
    R = 0.0
    if net in SUPPLY:
        pads = sorted(set(v for k, v in ports.items() if k.startswith("pad/")))
        far = [v for k, v in ports.items() if not k.startswith("pad/") and not k.startswith("io_")]
        if pads and far and len(d["elements"]):
            # farthest port by the voltage of a 1 A injection at each port is costly; use the 20 macro ports
            R = max(reff(net, pads, f) for f in sorted(set(far))[:200:10])
    elif len(pn) >= 2 and len(d["elements"]):
        R = max(reff(net, [pn[i]], pn[j]) for i in range(len(pn)) for j in range(i + 1, len(pn)))
    table.append({"net": net, "ports": len(ports), "R_ohm": round(R, 3), "C_fF": round(Cnet[net] * 1e15, 3),
                  "Cg_fF": round(Cgnet[net] * 1e15, 3), "Cc_fF": round(Ccnet[net] * 1e15, 3)})
byC = sorted(table, key=lambda r: -r["C_fF"])[:20]
byR = sorted(table, key=lambda r: -r["R_ohm"])[:20]
res["c_table_by_C"] = byC
res["c_table_by_R"] = byR
res["c_all_nets"] = sorted(table, key=lambda r: r["net"])
log("(c) top 20 by C:")
for r in byC:
    log("   %-16s C %9.1f fF (ground %8.1f, coupling %8.1f)  R %8.2f ohm  ports %d" % (
        r["net"], r["C_fF"], r["Cg_fF"], r["Cc_fF"], r["R_ohm"], r["ports"]))
log("(c) top 20 by R:")
for r in byR:
    log("   %-16s R %8.2f ohm  C %8.1f fF  ports %d" % (r["net"], r["R_ohm"], r["C_fF"], r["ports"]))


def elmore(net, drv, loads, cnodes=None):
    """Elmore delay from node drv (ideal source) to every node: tau = G^-1 * C (coupling counted to ground)"""
    idx, Gm = lap(net)
    n = Gm.shape[0]
    C = np.zeros(n)
    cg = cnodes["Cg"] if cnodes else CN["Cg"]
    cc = cnodes["Cc"] if cnodes else CN["Cc"]
    for nm, c in cg.items():
        if nm in idx:
            C[idx[nm]] += c
    for a, b, c in cc:
        if a in idx:
            C[idx[a]] += c
        if b in idx:
            C[idx[b]] += c
    for nm, c in loads.items():
        C[idx[nm]] += c
    keep = [i for i in range(n) if i != idx[drv]]
    G = Gm.tocsr()[keep][:, keep]
    x = spl.spsolve(G.tocsc(), C[keep])
    out = {}
    for nm, i in idx.items():
        out[nm] = 0.0 if i == idx[drv] else x[keep.index(i)]
    return out, C.sum()


P = RN["OSC_CLK"]["ports"]
osc, ctl, adc = P["u_osc/osc_clk"], P["u_ctrl/clk"], P["u_adc/clk"]
sk = {}
for cadc in (34e-15, 50e-15, 60e-15):
    t, ctot = elmore("OSC_CLK", osc, {adc: cadc, ctl: 5e-15})
    sk["adc_pin_%.0ffF" % (cadc * 1e15)] = {"tau_adc_ps": round(t[adc] * 1e12, 2), "tau_ctrl_ps": round(t[ctl] * 1e12, 2),
                                           "skew_ps": round((t[adc] - t[ctl]) * 1e12, 2),
                                           "net_C_fF_with_loads": round(ctot * 1e15, 2)}
r_osc_adc = reff("OSC_CLK", [osc], adc)
r_osc_ctl = reff("OSC_CLK", [osc], ctl)
res["c_osc_clk"] = {"elmore": sk, "R_osc_adc": round(r_osc_adc, 2), "R_osc_ctrl": round(r_osc_ctl, 2),
                    "C_wire_fF": round(Cnet["OSC_CLK"] * 1e15, 2), "estimate_ps": "48-51 (flow/clk_skew_g.py, typ)"}
log("(c) OSC_CLK R osc->adc %.1f ohm, osc->ctrl %.1f ohm, wire C %.1f fF" % (r_osc_adc, r_osc_ctl, Cnet["OSC_CLK"] * 1e15))
for k, v in sk.items():
    log("    Elmore %s: ADC %.2f ps, ctrl %.2f ps, skew %.2f ps" % (k, v["tau_adc_ps"], v["tau_ctrl_ps"], v["skew_ps"]))

# ngspice transient on the OSC_CLK network alone (coupling C to ground), 250 ps edge, ideal driver
d = RN["OSC_CLK"]
L = ["* T11 OSC_CLK transient, extracted network (typ), ideal driver with 250 ps edge"]
for k, (a, b, r) in enumerate(d["elements"]):
    L.append("R%d %s %s %.6g" % (k, a, b, r))
cn = defaultdict(float)
for nm, c in CN["Cg"].items():
    if node_net.get(nm) == "OSC_CLK":
        cn[nm] += c
for a, b, c in CN["Cc"]:
    for z in (a, b):
        if node_net.get(z) == "OSC_CLK":
            cn[z] += c
for k, (nm, c) in enumerate(cn.items()):
    L.append("C%d %s 0 %.6g" % (k, nm, c))
L += ["Cadc %s 0 50f" % adc, "Cctl %s 0 5f" % ctl, "Vdrv %s 0 pulse(0 1.2 100p 250p 250p 2n 5n)" % osc,
      ".control", "tran 0.5p 1.5n",
      "meas tran tctl when v(%s)=0.6 rise=1" % ctl, "meas tran tadc when v(%s)=0.6 rise=1" % adc,
      "meas tran tosc when v(%s)=0.6 rise=1" % osc, ".endc", ".end"]
v, o = run_ng("\n".join(L) + "\n", "osc_clk_tran")
if "tadc" in v and "tctl" in v:
    res["c_osc_clk"]["tran_skew_ps"] = round((v["tadc"] - v["tctl"]) * 1e12, 2)
    res["c_osc_clk"]["tran_delay_ctrl_ps"] = round((v["tctl"] - v["tosc"]) * 1e12, 2)
    res["c_osc_clk"]["tran_delay_adc_ps"] = round((v["tadc"] - v["tosc"]) * 1e12, 2)
    log("    transient 50 %%: ctrl %.2f ps, ADC %.2f ps after the osc pin, skew %.2f ps" % (
        (v["tctl"] - v["tosc"]) * 1e12, (v["tadc"] - v["tosc"]) * 1e12, (v["tadc"] - v["tctl"]) * 1e12))
else:
    res["c_osc_clk"]["tran_skew_ps"] = "failed (see osc_clk_tran.log)"

pairs = {}
for p, n in (("AFE_SOUTS_P", "AFE_SOUTS_N"), ("AFE_SOUTC_P", "AFE_SOUTC_N")):
    rr = {}
    for net in (p, n):
        P = RN[net]["ports"]
        a = [v for k, v in P.items() if k.startswith("u_afe/")][0]
        b = [v for k, v in P.items() if k.startswith("u_adc/")][0]
        rr[net] = {"R_ohm": reff(net, [a], b), "C_fF": Cnet[net] * 1e15, "Cg_fF": Cgnet[net] * 1e15}
    cpn = pairC.get(tuple(sorted((p, n))), 0.0) * 1e15
    pairs[p[:-2]] = {"P": {k: round(x, 3) for k, x in rr[p].items()}, "N": {k: round(x, 3) for k, x in rr[n].items()},
                     "dR_ohm": round(rr[p]["R_ohm"] - rr[n]["R_ohm"], 3), "dC_fF": round(rr[p]["C_fF"] - rr[n]["C_fF"], 3),
                     "C_P_to_N_fF": round(cpn, 3)}
    log("(c) %s: R P %.2f / N %.2f ohm (dR %.2f), C P %.2f / N %.2f fF (dC %.2f), P-N coupling %.2f fF" % (
        p[:-2], rr[p]["R_ohm"], rr[n]["R_ohm"], rr[p]["R_ohm"] - rr[n]["R_ohm"], rr[p]["C_fF"], rr[n]["C_fF"],
        rr[p]["C_fF"] - rr[n]["C_fF"], cpn))
res["c_afe_adc_pairs"] = pairs
P = RN["VREF_B"]["ports"]
src = [v for k, v in P.items() if k.startswith("u_bias/")][0]
vr = {k: round(reff("VREF_B", [src], v), 3) for k, v in P.items() if not k.startswith("u_bias/")}
res["c_vref_b"] = {"R_from_bias_ohm": vr, "C_fF": round(Cnet["VREF_B"] * 1e15, 2), "Cg_fF": round(Cgnet["VREF_B"] * 1e15, 2),
                   "largest_couplings_fF": sorted([[x if y == "VREF_B" else y, round(c * 1e15, 3)] for (x, y), c in pairC.items()
                                                   if "VREF_B" in (x, y)], key=lambda q: -q[1])[:6]}
log("(c) VREF_B: R from the bias pin", vr, "C %.1f fF" % (Cnet["VREF_B"] * 1e15), "couplings",
    res["c_vref_b"]["largest_couplings_fF"])

# ---------------- (e) reduction error on the sensitive nets
REDF = os.path.join(ND, "r1_top_g_pex_red.spice")
NLr = read_spice(REDF)
rcr = NLr["r1_top_rc"]
portnode = {}
for t in rcr["el"]:
    if t[0].startswith("Rp_"):
        portnode[t[1]] = t[2]
Rr = [(t[1], t[2], float(t[3])) for t in rcr["el"] if t[0][0] == "R" and not t[0].startswith("Rp_") and not t[0].startswith("Rtie")]
Cgr = {t[1]: float(t[3]) for t in rcr["el"] if t[0].startswith("Cg")}
Ccr = [(t[1], t[2], float(t[3])) for t in rcr["el"] if t[0].startswith("Cc")]
err = {}
for net in ("OSC_CLK", "AFE_SOUTS_P", "AFE_SOUTS_N", "AFE_SOUTC_P", "AFE_SOUTC_N", "VREF_B"):
    nodes = set(z[0] for z in RN[net]["nodes"])
    el = [e for e in Rr if e[0] in nodes]
    rnodes = sorted(set([e[0] for e in el] + [e[1] for e in el]) | (set(RN[net]["ports"].values()) & (set(Cgr) | nodes)))
    full_C = Cnet[net]
    red_C = sum(c for n, c in Cgr.items() if n in nodes) + sum(c for a, b, c in Ccr if a in nodes) + \
        sum(c for a, b, c in Ccr if b in nodes)
    RN2 = {"nodes": [[n, "", 0, 0] for n in rnodes], "elements": [list(e) for e in el], "ports": RN[net]["ports"]}
    saved = RN[net]
    RN[net] = RN2
    out = {"nodes_full": len(saved["nodes"]), "nodes_red": len(rnodes), "C_full_fF": round(full_C * 1e15, 3),
           "C_red_fF": round(red_C * 1e15, 3)}
    if net == "OSC_CLK":
        t, _ = elmore(net, osc, {adc: 50e-15, ctl: 5e-15}, {"Cg": Cgr, "Cc": Ccr})
        out["skew_red_ps"] = round((t[adc] - t[ctl]) * 1e12, 3)
        out["skew_full_ps"] = sk["adc_pin_50fF"]["skew_ps"]
        out["tau_adc_red_ps"] = round(t[adc] * 1e12, 3)
        out["tau_adc_full_ps"] = sk["adc_pin_50fF"]["tau_adc_ps"]
    elif net.startswith("AFE"):
        P = saved["ports"]
        a = [v for k, v in P.items() if k.startswith("u_afe/")][0]
        b = [v for k, v in P.items() if k.startswith("u_adc/")][0]
        t, _ = elmore(net, a, {b: 1e-15}, {"Cg": Cgr, "Cc": Ccr})
        out["tau_adc_pin_red_ps"] = round(t[b] * 1e12, 4)
        RN[net] = saved
        t0, _ = elmore(net, a, {b: 1e-15})
        out["tau_adc_pin_full_ps"] = round(t0[b] * 1e12, 4)
    elif net == "VREF_B":
        t, _ = elmore(net, src, {}, {"Cg": Cgr, "Cc": Ccr})
        far = max((v for k, v in saved["ports"].items() if not k.startswith("u_bias/")), key=lambda q: t.get(q, 0))
        out["tau_far_red_ps"] = round(t[far] * 1e12, 4)
        RN[net] = saved
        t0, _ = elmore(net, src, {})
        out["tau_far_full_ps"] = round(t0[far] * 1e12, 4)
    RN[net] = saved
    err[net] = out
    log("(e) reduction", net, out)
res["e_reduction"] = err
json.dump(res, open(os.path.join(OUT, "checks.json"), "w"), indent=1)
log("wrote", os.path.join(OUT, "checks.json"))

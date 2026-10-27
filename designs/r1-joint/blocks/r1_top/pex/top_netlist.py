# SPDX-License-Identifier: Apache-2.0
"""r1_top try g, chip-level extraction (track T11), step 3: RC netlist r1_top_g_pex.spice.

  python3 top_netlist.py <wire dir> <rnet json> <kpex run dir (…/r1_top_wire__r1_top_wire) | none> <CDL> <out dir>
        [--tau 1e-12] [--maxdeg 8] [--fast] [--cfill <fill_net.json>] [--stem r1_top_g_pex]

Method:
  1. R: the per-net RNetExtractor networks of top_rnet.py (one node every 20 um along the signal wires, the
     triangulated mesh on the supply nets).
  2. C: kpex 2.5D CC totals per net pair (r1_top_wire_k25d_pex_netlist.csv, exact values). The kpex report database
     (…_pex_report.rdb.gz) gives every overlap, fringe and sidewall contribution with its location; each pair total
     is split over the contribution locations in proportion to the reported values, and each share goes to the
     nearest R node of each of the two nets. Substrate (VSUBS) is the port "sub" (tied to VSS in r1_top_pex, as the
     block extractions). Nets without an R network (unnamed metal of the IO cells, the dummy substrate tap) are AC
     ground: their coupling goes to "sub" (sum reported per net).
  3. Subcircuits: r1_top_rc (the RC network; ports = the macro pins, the IO-cell pins, the pad-level nets and "sub";
     parameter ictrl = r1_ctrl_top supply current, spread as 63 current sources over its grid, default 0) and
     r1_top_pex (pad-level ports of the CDL r1_top, the macros by their subcircuit names of record with the CDL pin
     order, the signal IO cells by their PDK names as tb/r1_chip.sp, and r1_top_rc).
  4. Reduced variant (tag _red): TICER elimination of the internal nodes with a time constant C/G below 1 ps and at
     most 8 neighbours (Kron reduction of R; the node capacitances moved to the neighbours in proportion to the
     conductances). DC resistances between ports are exact; total C per net is kept.
  5. Optional (--cfill, track T11b): the fill correction of pex/fill_net.py is added to the kpex pair totals before
     the split (pair_delta_fF: one delta per net pair; a total that would go below 0 is set to 0 and logged). A pair
     that exists only through the fill (no kpex location) takes the locations of the pair (sensitive net, VSUBS), so
     the fill C is spread along the sensitive net. --stem sets the output file stem (default r1_top_g_pex).
Outputs: <out>/r1_top_g_pex.spice, r1_top_g_pex_red.spice, pin_map.csv, netlist_build.json, top_netlist.log.
"""
import csv
import gzip
import heapq
import json
import math
import os
import re
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict

import numpy as np
from scipy.spatial import cKDTree

WD, RNETF, KDIR, CDLF, OUT = sys.argv[1:6]
TAU, MAXDEG = 1e-12, 8
FAST = False
CFILL, STEM = None, "r1_top_g_pex"
SUPPLY = {"VDD", "VSS", "VDDA", "IOVDD", "IOVSS"}
_a = sys.argv[6:]
while _a:
    _k = _a.pop(0)
    if _k == "--tau":
        TAU = float(_a.pop(0))
    elif _k == "--maxdeg":
        MAXDEG = int(_a.pop(0))
    elif _k == "--fast":
        FAST = True
    elif _k == "--cfill":
        CFILL = _a.pop(0)
    elif _k == "--stem":
        STEM = _a.pop(0)
os.makedirs(OUT, exist_ok=True)
LOG = open(os.path.join(OUT, "top_netlist.log"), "w")


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    LOG.write(s + "\n")
    LOG.flush()


def norm(p):
    return re.sub(r"_+$", "", re.sub(r"[\[\]<>]", "_", p.lower()))


PJ = json.load(open(os.path.join(WD, "ports.json")))
RN = json.load(open(RNETF))["nets"]
# ---- CDL: top ports, instance lines, pin orders
SUB, XL, cur, lines = {}, [], None, []
for raw in open(CDLF):
    raw = raw.rstrip("\n")
    if raw.startswith("+") and lines:
        lines[-1] += " " + raw[1:]
    else:
        lines.append(raw)
for ln in lines:
    t = ln.split()
    if not t:
        continue
    if t[0].lower() == ".subckt":
        cur = t[1]
        SUB[cur] = t[2:]
    elif t[0].lower() == ".ends":
        cur = None
    elif cur == "r1_top" and t[0][0] in "Xx":
        toks = [x for x in t[1:] if x != "/"]
        XL.append((t[0][1:], toks[-1], toks[:-1]))
TOPPORTS = SUB["r1_top"]

# ---- 1. R network, node coordinates
nodes_xy = {}         # node -> (x, y)
node_net = {}
R_el = []
for net, d in RN.items():
    for nm, lay, x, y in d["nodes"]:
        nodes_xy[nm] = (x, y)
        node_net[nm] = net
    for a, b, r in d["elements"]:
        R_el.append((a, b, r))
log("R network: nets", len(RN), "nodes", len(nodes_xy), "resistors", len(R_el))
KD = {}
for net, d in RN.items():
    pts = np.array([[n[2], n[3]] for n in d["nodes"]])
    if len(pts):
        KD[net] = (cKDTree(pts), [n[0] for n in d["nodes"]])


def nearest(net, x, y):
    t, names = KD[net]
    _, i = t.query([x, y])
    return names[int(i)]


# ---- 2. C: pair totals and locations
pair = defaultdict(float)
csvf = [f for f in os.listdir(KDIR) if f.endswith("_k25d_pex_netlist.csv")][0] if KDIR != "none" else None
for row in (csv.reader(open(os.path.join(KDIR, csvf)), delimiter=";") if csvf else []):
    if not row or not row[0].startswith("C"):
        continue
    a, b, c = row[1], row[2], float(row[3])
    if a > b:
        a, b = b, a
    pair[(a, b)] += c
log("kpex pairs", len(pair), "total fF %.1f" % sum(pair.values()))
CF = None
clipped = []
if CFILL:
    CF = json.load(open(CFILL))
    t0 = sum(pair.values())
    for a, b, d in CF["pair_delta_fF"]:
        k = (a, b) if a < b else (b, a)
        v = pair.get(k, 0.0) + d
        if v < 0:
            clipped.append([k[0], k[1], round(v, 4)])
            v = 0.0
        pair[k] = v
    log("cfill: %d pair deltas, total %+.1f fF, %d pairs clipped at 0" % (len(CF["pair_delta_fF"]),
                                                                       sum(pair.values()) - t0, len(clipped)))
loc = defaultdict(list)       # (a, b) -> [(value, x, y)]
rdbf = [f for f in os.listdir(KDIR) if f.endswith("_pex_report.rdb.gz")] if KDIR != "none" else []
seen = set()
nitems = 0
VAL = re.compile(r"([0-9.eE+-]+) fF$")
NUM = re.compile(r"(-?[0-9.]+),(-?[0-9.]+)")
MERGED = os.path.join(KDIR, "merged_contributions.json") if KDIR != "none" else ""
if MERGED and os.path.exists(MERGED):
    # tiled kpex (kpex_tiles.py merge): located contributions, each counted once (tile core)
    for a, b, v, x, y in json.load(open(MERGED)):
        loc[(a, b)].append((v, x, y))
        nitems += 1
    rdbf = []
    log("tiled kpex input: merged_contributions.json")
if rdbf:
    for ev, el in ET.iterparse(gzip.open(os.path.join(KDIR, rdbf[0])), events=("end",)):
        if el.tag != "item":
            continue
        cat = el.findtext("category") or ""
        comps = cat.strip("'").split("'.'")
        nitems += 1
        kind = comps[0]
        key = None
        if kind == "[C] Overlap" and comps[-1] == "Overlap Area":
            nets = re.split(r" (?:\u2013|\\342\\200\\223) ", comps[3])   # en dash, raw or octal-escaped in the XML
            key, val = cat, comps[4]
        elif kind.startswith("[C] Fringe") and comps[-1] == "Inside Edge":
            nets = [comps[2].split("=", 1)[1], comps[4].split("=", 1)[1]]
            key, val = cat, comps[5]
        elif kind == "[C] Sidewall":
            nets = [comps[2].split("=", 1)[1], comps[3].split("=", 1)[1]]
            key, val = cat, comps[4]
        if key is not None and key not in seen:
            seen.add(key)
            m = VAL.search(val)
            v = float(m.group(1)) if m else 0.0
            vals = el.find("values")
            g = vals.find("value").text if vals is not None and vals.find("value") is not None else ""
            xy = [(float(p), float(q)) for p, q in NUM.findall(g)]
            if xy and len(nets) == 2:
                x = sum(p for p, q in xy) / len(xy)
                y = sum(q for p, q in xy) / len(xy)
                a, b = sorted(nets)
                loc[(a, b)].append((v, x, y))
        el.clear()
log("rdb items", nitems, "contributions", len(seen), "pairs with locations", len(loc))
if CF:
    sens = set(CF["sensitive_nets"])
    nfb = 0
    for (a, b) in list(pair):
        if (a, b) in loc:
            continue
        s = a if a in sens else (b if b in sens else None)
        if s is None:
            continue
        k = (s, "VSUBS") if s < "VSUBS" else ("VSUBS", s)
        if k in loc:
            loc[(a, b)] = loc[k]
            nfb += 1
    log("cfill: pairs without kpex location placed along the sensitive net", nfb)

GND = "sub"
Cg = defaultdict(float)        # node -> C to sub (F)
Cc = defaultdict(float)        # (n1, n2) sorted -> C (F)
to_sub_unnamed = defaultdict(float)
nolocs = 0


def endpoint(net, x, y):
    if net == "VSUBS":
        return GND
    if net in KD:
        return nearest(net, x, y)
    return None


for (a, b), ctot in pair.items():
    L = loc.get((a, b))
    if not L:
        nolocs += 1
        # no location: the centroid of the nodes of the routed net(s)
        pts = []
        for n in (a, b):
            if n in RN and RN[n]["nodes"]:
                pts += [(z[2], z[3]) for z in RN[n]["nodes"]]
        if not pts:
            continue
        L = [(1.0, sum(p for p, q in pts) / len(pts), sum(q for p, q in pts) / len(pts))]
    s = sum(v for v, x, y in L)
    for v, x, y in L:
        w = (v / s) if s > 0 else 1.0 / len(L)
        c = ctot * w * 1e-15
        ea, eb = endpoint(a, x, y), endpoint(b, x, y)
        if ea is None and eb is None:
            continue
        if ea is None or eb is None:
            n = ea if ea is not None else eb
            other = b if ea is not None else a
            if n == GND:
                continue
            Cg[n] += c
            if other != "VSUBS":
                to_sub_unnamed[node_net[n]] += c
            continue
        if ea == GND or eb == GND:
            n = eb if ea == GND else ea
            if n != GND:
                Cg[n] += c
            continue
        if node_net[ea] == node_net[eb]:
            continue                     # same net (cannot happen for kpex pairs)
        k = (ea, eb) if ea < eb else (eb, ea)
        Cc[k] += c
log("C: grounded nodes", len(Cg), "coupling pairs", len(Cc), "pairs without location", nolocs,
    "total C %.1f fF" % ((sum(Cg.values()) + sum(Cc.values())) * 1e15))

# ---- 3. ports: macro pins, IO pins, pads, ctrl grid
pmap = []           # rows for pin_map.csv
rcport = {}         # rc port name -> node
ties = []           # (node1, node2) 1 mOhm ties (same-name pins of one macro, pads of one package pin)
dropped = []
for p in PJ["ports"]:
    net = p["net"]
    if not net or net.startswith("unnamed") or net not in RN:
        continue
    node = RN[net]["ports"].get(p["name"])
    joined = RN[net]["ports_joined_to_nearest_node_um"].get(p["name"])
    if node is None:
        dropped.append((p["name"], "no node"))
        continue
    if p["kind"] == "macro":
        if p["inst"] == "u_ctrl" and norm(p["pin"]) in ("vdd", "vss"):
            continue                     # the ctrl supply pins: grid ports below
        pn = "%s__%s" % (p["inst"], norm(p["pin"]))
    elif p["kind"] == "io":
        pn = "%s__%s" % (p["inst"], p["pin"])
    else:
        pn = p["pin"]                    # pad-level net (CDL port name)
    if joined is not None and joined > 2.0 and p["kind"] == "macro":
        dropped.append((p["name"], "second pin shape, not connected at the top level (%.1f um to the net)" % joined))
        continue
    if pn in rcport:
        if rcport[pn] != node:
            ties.append((rcport[pn], node))
    else:
        rcport[pn] = node
    b = p["poly"]
    xs = [q[0] for q in b]
    ys = [q[1] for q in b]
    pmap.append([pn, p["kind"], p.get("inst"), p.get("pin"), net, node, "%.2f" % (sum(xs) / len(xs) * PJ["dbu"]),
                 "%.2f" % (sum(ys) / len(ys) * PJ["dbu"]), "" if joined is None else "%.2f" % joined])
for sup in ("VDD", "VSS"):
    g = RN[sup]["ports"]
    rcport["u_ctrl__%s" % sup.lower()] = g["ctrlgrid/%s_s3_y350" % sup]
    for k in range(7):
        for yy in range(50, 651, 75):
            nm = "ctrlgrid/%s_s%d_y%d" % (sup, k, yy)
            pmap.append(["(internal) " + nm, "ctrlgrid", "u_ctrl", sup, sup, g[nm], "", "", ""])
GRID = [(RN["VDD"]["ports"]["ctrlgrid/VDD_s%d_y%d" % (k, yy)], RN["VSS"]["ports"]["ctrlgrid/VSS_s%d_y%d" % (k, yy)])
        for k in range(7) for yy in range(50, 651, 75)]
log("rc ports", len(rcport), "ties", len(ties), "dropped", len(dropped))
for d in dropped:
    log("  dropped port", d)


# ---- 4. reduction (TICER)
def reduce_network(R_el, Cg, Cc, keep):
    G = defaultdict(dict)
    for a, b, r in R_el:
        if a == b:
            continue
        g = 1.0 / r
        G[a][b] = G[a].get(b, 0.0) + g
        G[b][a] = G[b].get(a, 0.0) + g
    CG = dict(Cg)
    CC = defaultdict(dict)
    for (a, b), c in Cc.items():
        CC[a][b] = CC[a].get(b, 0.0) + c
        CC[b][a] = CC[b].get(a, 0.0) + c
    alive = set(G) | set(CG) | set(CC)
    heap = [(len(G[n]), n) for n in G if n not in keep]
    heapq.heapify(heap)
    elim = 0
    while heap:
        d, n = heapq.heappop(heap)
        if n not in alive or n in keep:
            continue
        nb = G.get(n, {})
        if len(nb) != d:
            heapq.heappush(heap, (len(nb), n))
            continue
        if d == 0 or d > MAXDEG:
            continue
        gt = sum(nb.values())
        ctot = CG.get(n, 0.0) + sum(CC.get(n, {}).values())
        if ctot / gt > TAU:
            continue
        # Kron: new conductances between neighbours
        items = list(nb.items())
        for i in range(len(items)):
            a, ga = items[i]
            for j in range(i + 1, len(items)):
                b, gb = items[j]
                g = ga * gb / gt
                G[a][b] = G[a].get(b, 0.0) + g
                G[b][a] = G[b].get(a, 0.0) + g
        # capacitances to the neighbours in proportion to the conductances
        cg = CG.pop(n, 0.0)
        for a, ga in items:
            w = ga / gt
            if cg:
                CG[a] = CG.get(a, 0.0) + cg * w
            for m, c in CC.get(n, {}).items():
                if m == a:
                    CG[a] = CG.get(a, 0.0)          # coupling to its own neighbour: drops out (same potential path)
                    continue
                CC[a][m] = CC[a].get(m, 0.0) + c * w
                CC[m][a] = CC[m].get(a, 0.0) + c * w
        for m in list(CC.get(n, {})):
            CC[m].pop(n, None)
        CC.pop(n, None)
        for a, ga in items:
            G[a].pop(n, None)
            heapq.heappush(heap, (len(G[a]), a))
        G.pop(n, None)
        alive.discard(n)
        elim += 1
    Rn = []
    for a in G:
        for b, g in G[a].items():
            if a < b:
                Rn.append((a, b, 1.0 / g))
    Cgn = {n: c for n, c in CG.items() if c > 0}
    Ccn = {}
    for a in CC:
        for b, c in CC[a].items():
            if a < b and c > 0:
                Ccn[(a, b)] = c
    return Rn, Cgn, Ccn, elim


def write_netlist(path, R_el, Cg, Cc, title):
    ports = sorted(rcport)
    portset = set(rcport.values())
    L = ["* %s" % title,
         ("* r1_top try g (run asm-20261028-g3, unfilled GDS sha256 8f1c5d7c…), chip-level extraction, track T11"
          if not CF else "* r1_top try g, chip-level extraction with the metal fill of asm-20261028-g3-fill (GDS sha256 "
          "3b337a55…) on the sensitive nets (pex/fill_net.py), track T11b"),
         "* Generated by designs/r1-joint/blocks/r1_top/pex/top_netlist.py; method in its docstring and in",
         "* designs/r1-joint/blocks/r1_top/README.md, section \"Chip-level extraction (try g)\".",
         "* Elements: %d resistors, %d grounded capacitors (to port sub), %d coupling capacitors" % (
             len(R_el), len(Cg), len(Cc)),
         "* Units: Ohm, F. Port sub = substrate (VSUBS of kpex); r1_top_pex ties it to VSS.",
         ""]
    L.append(".subckt r1_top_rc")
    for i in range(0, len(ports), 8):
        L.append("+ " + " ".join(ports[i:i + 8]))
    L.append("+ sub params: ictrl_p=0")
    L.append("* port -> extracted node")
    for p in ports:
        L.append("Rp_%s %s %s 1e-3" % (p, p, rcport[p]))
    for k, (a, b) in enumerate(ties):
        L.append("Rtie%d %s %s 1e-3" % (k, a, b))
    for k, (a, b, r) in enumerate(R_el):
        L.append("R%d %s %s %.6g" % (k, a, b, max(r, 1e-5)))
    for k, (n, c) in enumerate(sorted(Cg.items())):
        L.append("Cg%d %s sub %.6g" % (k, n, c))
    for k, ((a, b), c) in enumerate(sorted(Cc.items())):
        L.append("Cc%d %s %s %.6g" % (k, a, b, c))
    L.append("* r1_ctrl_top supply current (parameter ictrl_p, A), spread over its 63 grid points (VDD -> VSS)")
    for k, (a, b) in enumerate(GRID):
        L.append("Ictrl%d %s %s {ictrl_p/63}" % (k, a, b))
    L.append(".ends r1_top_rc")
    L.append("")
    # wrapper
    L.append("* r1_top_pex: pad-level ports as the CDL r1_top; macros by their subcircuit names of record (CDL pin order);")
    L.append("* signal IO cells by their PDK names as tb/r1_chip.sp (pad, core pin, vdd, vss, iovdd, iovss); the supply")
    L.append("* IO cells (IOPadVdd/Vss/IOVdd/IOVss) are not instantiated (as tb/r1_chip.sp).")
    L.append(".subckt r1_top_pex %s params: ictrl=0" % " ".join(TOPPORTS))
    L.append("Xrc " + " ".join(ports) + " VSS r1_top_rc ictrl_p={ictrl}")
    for p in TOPPORTS:
        if p not in rcport:
            L.append("* pad-level port %s has no extracted node" % p)
    nc = 0
    for inst, cell, nets in XL:
        pins = SUB[cell]
        nodes = []
        for pn in pins:
            q = "%s__%s" % (inst, norm(pn))
            if q in rcport:
                nodes.append(q)
            else:
                nodes.append(q + "_nc")
                nc += 1
        L.append("X%s %s %s" % (inst, " ".join(nodes), cell))
    for e in IOS:
        cell, inst = e["cell"], e["inst"]
        if cell in ("sg13g2_IOPadVdd", "sg13g2_IOPadVss", "sg13g2_IOPadIOVdd", "sg13g2_IOPadIOVss"):
            continue
        core = {"sg13g2_IOPadIn": "p2c", "sg13g2_IOPadAnalog": "padres"}.get(cell, "c2p")
        pad = "%s__pad" % inst if cell == "sg13g2_IOPadAnalog" else "%s__pad_outer" % inst
        sup = ["%s__%s" % (inst, s) for s in ("vdd", "vss", "iovdd", "iovss")]
        nodes = [pad, "%s__%s" % (inst, core)] + sup
        nodes = [n if n in rcport else n + "_nc" for n in nodes]
        L.append("X%s %s %s" % (inst, " ".join(nodes), cell))
    L.append(".ends r1_top_pex")
    L.append(".end")
    open(path, "w").write("\n".join(L) + "\n")
    log("wrote", path, "lines", len(L), "unconnected macro pins", nc)


IOS = json.load(open(os.path.join(WD, "conn.json")))["io_cells"]
keep = set(rcport.values()) | {n for t in ties for n in t} | {n for t in GRID for n in t}
if FAST:
    # fast variant (simulation speed): every coupling capacitor with a supply net at one end goes to ground at both
    # ends (the supplies are AC ground for the signals; supply-to-supply coupling becomes decoupling to ground); then
    # TICER with the --tau / --maxdeg values given.
    Cg2 = defaultdict(float, Cg)
    Cc2 = {}
    nsup = 0
    for (a, b), c in Cc.items():
        if node_net[a] in SUPPLY or node_net[b] in SUPPLY:
            Cg2[a] += c
            Cg2[b] += c
            nsup += 1
        else:
            Cc2[(a, b)] = c
    log("fast: coupling capacitors with a supply net moved to ground", nsup, "kept", len(Cc2))
    Rr, Cgr, Ccr, ne = reduce_network(R_el, dict(Cg2), Cc2, keep)
    log("fast: eliminated", ne, "resistors", len(Rr), "grounded C", len(Cgr), "coupling C", len(Ccr))
    write_netlist(os.path.join(OUT, STEM + "_fast.spice"), Rr, Cgr, Ccr,
                  STEM + "_fast.spice: fast RC network (supply couplings to ground, TICER tau %.3g s, max degree %d)"
                  % (TAU, MAXDEG))
    json.dump({"fast": {"resistors": len(Rr), "cg": len(Cgr), "cc": len(Ccr), "eliminated": ne, "tau_s": TAU,
                        "maxdeg": MAXDEG, "supply_couplings_to_ground": nsup}},
              open(os.path.join(OUT, "netlist_build_fast.json"), "w"), indent=1)
    sys.exit(0)
write_netlist(os.path.join(OUT, STEM + ".spice"), R_el, Cg, Cc, STEM + ".spice: full RC network")
Rr, Cgr, Ccr, ne = reduce_network(R_el, Cg, Cc, keep)
log("reduced: eliminated", ne, "resistors", len(Rr), "grounded C", len(Cgr), "coupling C", len(Ccr))
write_netlist(os.path.join(OUT, STEM + "_red.spice"), Rr, Cgr, Ccr,
              STEM + "_red.spice: reduced RC network (TICER, tau %.3g s, max degree %d)" % (TAU, MAXDEG))
with open(os.path.join(OUT, "pin_map.csv"), "w") as f:
    w = csv.writer(f)
    w.writerow(["rc_port", "kind", "instance", "pin", "net (CDL)", "extracted node", "x_um", "y_um", "joined_um"])
    for r in sorted(pmap):
        w.writerow(r)
json.dump({"pairs": len(pair), "rdb_items": nitems, "contributions": len(seen), "pairs_without_location": nolocs,
           "coupling_to_unnamed_as_ground_fF": {k: round(v * 1e15, 4) for k, v in sorted(to_sub_unnamed.items())},
           "full": {"resistors": len(R_el), "cg": len(Cg), "cc": len(Cc), "nodes": len(nodes_xy)},
           "reduced": {"resistors": len(Rr), "cg": len(Cgr), "cc": len(Ccr), "eliminated": ne, "tau_s": TAU,
                       "maxdeg": MAXDEG},
           "cfill": CFILL, "cfill_clipped_pairs": clipped,
           "rc_ports": rcport, "ties": ties, "dropped_ports": dropped, "ctrl_grid": GRID},
          open(os.path.join(OUT, "netlist_build.json"), "w"), indent=1)
# per-node C for the checks (full network)
json.dump({"Cg": Cg, "Cc": [[a, b, c] for (a, b), c in Cc.items()]}, open(os.path.join(OUT, "c_nodes.json"), "w"))

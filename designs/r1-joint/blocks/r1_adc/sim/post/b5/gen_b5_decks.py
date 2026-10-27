#!/usr/bin/env python3
"""T2k (layout B5 helper, 2026-10-27): closed-loop post-layout decks for r1_adc = extracted analog part + the hardened
SAR sub-macro r1_adc_sar (gate-level netlist with PDK standard-cell transistor subcircuits, release-t2j-h).

Start: sar/sim/gen_gl_deck.py (T2j, run t2j-ms-h-tt). Changes:
  * The schematic core r1_adc5_core (without XSAR) is replaced by the post-layout ADC netlist (--adc-netlist, default
    the B4 RC netlist sim/post/r1_adc_post_rc_mb4.spice, subcircuit r1_adc_lay_pr = ports TOP_PORTS + vref vrefl).
  * The ADC instance sits in a small wrapper `r1_adc_b5w` instantiated as XADC, so the inner nodes have the B4 names
    (v(xadc.xl.<node>), as the r1_adc5_core_lay wrapper of sim/post).
  * Ports are mapped by name, not by position (the B5 netlist may order them differently):
      analog / supply  clk ain_* ibias vdda vdd vss vref_in topap.. vref vrefl -> clk sinp.. nbr vdda vdd 0 vbg topap..
                       vrefa vrefla (vref / vrefl = probe ports at the follower sources, as sim/post)
      vcm vcm2         -> 1 kOhm to ground (no driver, as sim/post/r1_adc5_post.spice)
      north pins       adc_hold is_smp adc_start adc_sel cur_trk por_n adc_valid_* adc_raw_* -> deck nets of the same
                       name (ctrl-side sources / outputs, 50 fF load = r1_adc_sar.sdc set_load of the ctrl outputs)
      sar_<pin>        -> net sar_<pin>, which is also the macro pin <pin> (B4: the open SAR-side labels)
    Macro pin <pin> connects to the ADC port sar_<pin> if it exists, else to the deck net <pin> (north pins, clk).
    B5 (lead, 2026-10-27): r1_adc_lay / r1_adc_lay_pr keep the B4 ports; the new subcircuit r1_adc_lay_sar has the
    ports of r1_adc_lay_pr + vdd_sar vss_sar (macro supply points, Metal5 buses over the macro). --b5 selects
    r1_adc_lay_sar (unless --adc-subckt is given) and requires the two ports; when present the macro VDD / VSS connect to them (the supply then reaches the macro only
    through the extracted ADC vdd / vss wiring, and i(vsarm) is 0: the SAR current is inside i(vdd)). --b5 requires them.
    So a B5 netlist that ends each SAR interconnect net at a port sar_<pin> at the macro pin (and the north wires at
    ports sar_adc_raw_a_0 ...) needs no change here. Macro VDD / VSS: port vdd_sar / vss_sar if present, else the
    deck vdd (through the 0 V ammeter Vsarm) / ground. Any other port: --port-map PORT=NET, else the script stops.
  * SAR macro internal parasitics (--sar-par lumped, default): the total capacitance of each of the 408 SPEF nets of
    the release (r1_adc_sar.nom.spef, coupling included) as one capacitor to VSS inside a copy of the gate-level
    subcircuit (written to sim/post/b5/sar/r1_adc_sar_gl_lumpc.spice, subcircuit r1_adc_sar_glc). Wire resistance:
    not modelled. --sar-par none: the gate-level netlist as T2j ran it.
  * ctrl side: r1_gate protocol as T2j (clk rising at n T; ctrl edges 0.3 ns after the clk edge, 50 ps): por_n low
    until 50 ns; start-up hold adc_hold ticks 3..5 (PRE_HOLD); frame f at tick 18 + 22 f: adc_start one tick,
    adc_hold (encoder) or is_smp (current) from E0 to E15; adc_sel = 0 (dummy load only).
    cur_trk per INTERFACES ctrl 0.7: rises 20 ticks (GUARD) before a current frame, falls one tick after its start
    (registered `soon` window); low at encoder frames.

Decks (written to sim/post/b5/decks/<tag>/; placeholders left: RAW, GLNET):
  mux_tt          r5 mux sequence e c e e, tt / 27 C / 1.2 V, buffer + bandgap model (as postb4-isa-tt-rc), 3.31 us
  fc_tt           first conversion, tt, 0 V in frames 0 and 1 (sim/r5/points/fixtt.json), ideal VREF 1.045 V forced at
                  the follower nodes (as postb4-fc-tt-rc), 1.86 us
  fc_ss125        first conversion, ss / 125 C / 1.08 V, -0.80 V (sim/post/points/ffb.json) (as postb4-fc-ss125-rc)
  ref_tt_buf      R2-4 buffer run, tt, sim/r5/points/ref10.json, buffer + bandgap (as postb4-ref-tt-rc), slice-port
                  reference nodes saved (--ref-probes)
  ref_tt_base     R2-4 base run: the same deck with --adc-netlist-base (slice reference ports on ideal DC sources at the
                  buffer-OP values, make_sp_netlist.py --per-port; as postb4-ref-tt-sp)
  --ref-slots N   R2-4 decks with the first N slots of ref10.json only (run-time option; default 10)

usage: gen_b5_decks.py [--tag b4] [--adc-netlist sim/post/r1_adc_post_rc_mb4.spice]
         [--adc-netlist-base sim/post/r1_adc_post_rc_mb4_sp_tt.spice] [--adc-subckt r1_adc_lay_pr]
         [--sar-par lumped|none] [--port-map PORT=NET ...] [--ref-probes "v(xadc.xl.vref__p13) ..."] [--ref-slots 10]
Paths are relative to designs/r1-joint/blocks/r1_adc (the ngspice working directory). Needs G1_RESULTS_ROOT (the
release netlist and SPEF are read for the port list and --sar-par lumped).
"""
import argparse, hashlib, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ADC = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
REL = "r1_adc_sar/release-t2j-h"
T = 1e9 / 30e6          # ns
CQ = 0.3

ap = argparse.ArgumentParser()
ap.add_argument("--tag", default="b4")
ap.add_argument("--adc-netlist", default="sim/post/r1_adc_post_rc_mb4.spice")
ap.add_argument("--adc-netlist-base", default="sim/post/r1_adc_post_rc_mb4_sp_tt.spice")
ap.add_argument("--adc-subckt", default="r1_adc_lay_pr")
ap.add_argument("--sar-par", default="lumped", choices=["lumped", "none"])
ap.add_argument("--port-map", action="append", default=[])
ap.add_argument("--ref-probes", default="v(xadc.xl.vref__p13) v(xadc.xl.vref__p16) v(xadc.xl.vrefl__p4) v(xadc.xl.vrefl__p6)")
ap.add_argument("--ref-slots", type=int, default=10)
ap.add_argument("--out-load", default="50f")
ap.add_argument("--b5", action="store_true", help="B5 netlist: require the ports vdd_sar / vss_sar (macro supply points)")
a = ap.parse_args()
if a.b5 and a.adc_subckt == "r1_adc_lay_pr":
    a.adc_subckt = "r1_adc_lay_sar"      # B5: ports of r1_adc_lay_pr + vdd_sar vss_sar (lead, 2026-10-27)
root = os.environ["G1_RESULTS_ROOT"]
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()


def subckt_ports(path, name):
    txt = open(path).read().replace("\n+", " ")
    m = re.search(r"^\.subckt\s+%s\s+([^\n]*)" % re.escape(name), txt, re.M | re.I)
    if not m:
        sys.exit("%s: no .subckt %s" % (path, name))
    return [p for p in m.group(1).split() if "=" not in p]


# ---------------------------------------------------------------- SAR macro (gate level)
glsrc = os.path.join(root, REL, "r1_adc_sar_gl_sim.spice")
glports = subckt_ports(glsrc, "r1_adc_sar_gl")
glcell = "r1_adc_sar_gl"
glinc = "GLNET"
if a.sar_par == "lumped":
    spef = os.path.join(root, REL, "r1_adc_sar.nom.spef")
    nm, caps, f = {}, [], False
    for ln in open(spef):
        if ln.startswith("*NAME_MAP"):
            f = True
            continue
        t = ln.split()
        if f and len(t) == 2 and re.fullmatch(r"\*\d+", t[0]):
            nm[t[0]] = t[1]
        elif ln.startswith("*D_NET"):
            f = False
            caps.append((t[1], float(t[2])))
    conv = lambda n: re.sub(r"\[(\d+)\]", r"_\1", n.replace("\\", ""))
    src = open(glsrc).read()
    nets = set()
    for ln in src.splitlines():
        if ln.startswith("X"):
            nets.update(ln.split()[1:-1])
    nets.update(glports)
    C = []
    for i, (k, c) in enumerate(caps):
        n = conv(nm.get(k, k))
        if n not in nets:
            sys.exit("SPEF net %s (%s) not in the gate-level netlist" % (k, n))
        C.append("Cspef%d %s VSS %.6gp" % (i, n, c))
    assert src.count(".ends") == 1
    out = src.replace(".subckt r1_adc_sar_gl ", ".subckt r1_adc_sar_glc ")
    out = out.replace(".ends", "* SPEF lumped wire C (total per net, coupling included, to VSS); wire R not modelled\n"
                      + "\n".join(C) + "\n.ends")
    hdr = ("* r1_adc_sar_gl_lumpc.spice -- written by sim/post/b5/gen_b5_decks.py (do not edit): the gate-level netlist "
           "<G1_RESULTS_ROOT>/%s/r1_adc_sar_gl_sim.spice (sha256 %s)\n* + one capacitor per SPEF net (r1_adc_sar.nom.spef, "
           "sha256 %s; %d nets, total %.4f pF)\n" % (REL, sha(glsrc), sha(spef), len(C), sum(c for _, c in caps)))
    os.makedirs(os.path.join(HERE, "sar"), exist_ok=True)
    open(os.path.join(HERE, "sar", "r1_adc_sar_gl_lumpc.spice"), "w").write(hdr + out)
    glcell, glinc = "r1_adc_sar_glc", "sim/post/b5/sar/r1_adc_sar_gl_lumpc.spice"

# ---------------------------------------------------------------- port maps
NORTH_IN = ["clk", "por_n", "adc_hold", "is_smp", "adc_start", "adc_sel", "cur_trk"]
NORTH_OUT = ["adc_valid_a", "adc_valid_b"] + ["adc_raw_%s_%d" % (s, k) for s in "ab" for k in range(14)]
TOP = {"ain_sin_p": "sinp", "ain_sin_n": "sinn", "ain_cos_p": "cosp", "ain_cos_n": "cosn", "ain_isa_p": "isap",
       "ain_isa_n": "isan", "ain_isb_p": "isbp", "ain_isb_n": "isbn", "ibias": "nbr", "vdda": "vdda", "vdd": "vdd",
       "vss": "0", "vref_in": "vbg", "topap": "topap", "topan": "topan", "topbp": "topbp", "topbn": "topbn",
       "vref": "vrefa", "vrefl": "vrefla", "vcm": "nc_vcm", "vcm2": "nc_vcm2"}
PMAP = dict(s.split("=", 1) for s in a.port_map)


def adc_map(ports):
    conn = []
    for p in ports:
        if p in PMAP:
            conn.append(PMAP[p])
        elif p in TOP:
            conn.append(TOP[p])
        elif p in NORTH_IN or p in NORTH_OUT:
            conn.append(p)
        elif p.startswith("sar_") or p in ("vdd_sar", "vss_sar"):
            conn.append(p)
        else:
            sys.exit("ADC port %s has no mapping: add --port-map %s=<net>" % (p, p))
    return conn


def macro_base(p):
    m = re.fullmatch(r"(cpa|cna|cpb|cnb)_(\d+)", p)
    return m.group(1) + m.group(2) if m else p


def macro_map(adc_ports):
    s = set(adc_ports)
    conn = []
    if a.b5 and not {"vdd_sar", "vss_sar"} <= s:
        sys.exit("--b5: the ADC netlist has no ports vdd_sar / vss_sar")
    for p in glports:
        b = macro_base(p)
        if p == "VDD":
            conn.append("vdd_sar" if "vdd_sar" in s else "vddsar")
        elif p == "VSS":
            conn.append("vss_sar" if "vss_sar" in s else "0")
        elif "sar_" + b in s:
            conn.append("sar_" + b)
        elif b in NORTH_IN or b in NORTH_OUT:
            conn.append(b)
        else:
            sys.exit("macro pin %s: no ADC port sar_%s and not a north pin" % (p, b))
    return conn


def pwl(name, segs, vdd):
    pts = ["0 0"]
    for t0, t1 in segs:
        pts += ["%.4fn 0" % t0, "%.4fn %s" % (t0 + 0.05, vdd), "%.4fn %s" % (t1, vdd), "%.4fn 0" % (t1 + 0.05)]
    return "V%s %s 0 PWL(%s)" % (name, name, " ".join(pts))


def pwl_points(vals):
    """sim/post/run_post.py points PWL: value of frame s from 550 ns (+5 ns shift) before its sampling edge."""
    pts = []
    for s, x in enumerate(vals):
        if s:
            t = (18 * T + s * 22 * T - 550 + 5) * 1e-9
            pts += ["%.6e %.7f" % (t, vals[s - 1]), "%.6e %.7f" % (t + 10e-9, x)]
        else:
            pts.append("0 %.7f" % x)
    return "\n+ ".join(" ".join(pts[i:i + 8]) for i in range(0, len(pts), 8))


edge = lambda n: n * T + CQ
CORNERS = {"tt": ("mos_tt", "27", "1.2"), "ss125": ("mos_ss", "125", "1.08"), "ffm40": ("mos_ff", "-40", "1.32")}
OPTS = "reltol=1e-4 vntol=1e-6 abstol=1e-12 method=trap sparse seed=1 noopiter"


def deck(name, netlist, corner, frames, ref, inputs, tstop, note, extra_save=""):
    mos, temp, vdd = CORNERS[corner]
    path = os.path.join(ADC, netlist)
    ports = subckt_ports(path, a.adc_subckt)
    aconn = adc_map(ports)
    mconn = macro_map(ports)
    ext = sorted(set(n for n in aconn if n != "0"))
    start, hold, smp, cur = [], [(edge(3), edge(5))], [], []
    for f, c in enumerate(frames):
        n0 = 18 + 22 * f
        start.append((edge(n0), edge(n0 + 1)))
        (smp if c == "c" else hold).append((edge(n0), edge(n0 + 15)))
        if c == "c":
            cur.append((edge(n0 - 20), edge(n0 + 1)))
    L = ["* sim/post/b5/decks/%s/%s.cir -- generated by sim/post/b5/gen_b5_decks.py (T2k); do not edit." % (a.tag, name),
         "* %s" % note,
         "* ADC netlist: %s (subckt %s, sha256 %s); SAR: %s (%s); frames %s; corner %s %s C %s V."
         % (netlist, a.adc_subckt, sha(path), glcell, "SPEF lumped C" if a.sar_par == "lumped" else "no wire parasitics",
            frames, mos, temp, vdd),
         "* Placeholders: RAW (bulk run directory), GLNET (release gate-level netlist, used with --sar-par none).",
         ".lib /foss/pdks/ihp-sg13g2/libs.tech/ngspice/models/cornerMOSlv.lib %s" % mos,
         ".lib /foss/pdks/ihp-sg13g2/libs.tech/ngspice/models/cornerCAP.lib cap_typ",
         ".lib /foss/pdks/ihp-sg13g2/libs.tech/ngspice/models/cornerMOShv.lib %s" % mos,
         ".lib /foss/pdks/ihp-sg13g2/libs.tech/ngspice/models/cornerRES.lib res_typ",
         ".include %s" % netlist,
         ".include /foss/pdks/ihp-sg13g2/libs.ref/sg13g2_stdcell/spice/sg13g2_stdcell.spice",
         ".include %s" % glinc,
         ".temp %s" % temp,
         "* sparse + noopiter: as the B4 RC runs (KLU fails the OP on the RC netlist and with the cell netlists)",
         ".option %s" % OPTS,
         "Vdd vdd 0 %s" % vdd,
         "Vsarm vddsar vdd 0",
         "Vdda vdda 0 3.3"]
    if ref == "lay":
        L += ["Vbgi vbgw 0 DC 1.045 TRNOISE(0.0004646 4.73e-08 0 0)",
              "Vbgf vbgi vbgw DC 0 TRNOISE(0 4.73e-08 1.15 1.285e-05)",
              "Rbg vbgi vbg 190k", "Ibref vdda nbr 5u"]
    else:   # lay-ideal (run_post.py --ref lay-ideal --vref 1.045, ideal-bgr off50m)
        L += ["Vbgi vbgi 0 DC 0.995000", "Rbg vbgi vbg 190k", "Ibref vdda nbr 5u",
              "Vrefi vrefa 0 1.045", "Vrefli vrefla 0 1.045"]
    L += inputs
    L += ["* ctrl side (r1_gate protocol, T2j sar/sim/gen_gl_deck.py; cur_trk per INTERFACES ctrl 0.7)",
          "Vclk clk 0 PULSE(0 %s %.9gn 50p 50p %.9gn %.9gn)" % (vdd, T, T / 2 - 0.05, T),
          "Vpor por_n 0 PWL(0 0 50n 0 50.05n %s)" % vdd,
          pwl("adc_start", start, vdd), pwl("adc_hold", hold, vdd), pwl("is_smp", smp, vdd), pwl("cur_trk", cur, vdd),
          "Vsel adc_sel 0 0"]
    L += ["Cl_%s %s 0 %s" % (o, o, a.out_load) for o in NORTH_OUT]
    L += ["* post-layout ADC (wrapper keeps the B4 node names xadc.xl.*)",
          ".subckt r1_adc_b5w " + " ".join(ext),
          "XL " + " ".join(aconn) + " " + a.adc_subckt,
          "Rnc_vcm nc_vcm 0 1k", "Rnc_vcm2 nc_vcm2 0 1k",
          ".ends r1_adc_b5w",
          "XADC " + " ".join(ext) + " r1_adc_b5w",
          "* hardened SAR sub-macro",
          "XSAR " + " ".join(mconn) + " " + glcell]
    sv = ["clk", "por_n", "adc_hold", "is_smp", "adc_start", "cur_trk", "topap", "topan", "topbp", "topbn",
          "vrefa", "vrefla", "vbg"] + NORTH_OUT
    sv += sorted(set(n for n in mconn if n.startswith("sar_")))
    save = " ".join("v(%s)" % n for n in sv) + " i(vdd) i(vdda) i(vsarm)" + (" " + extra_save if extra_save else "")
    L += [".control", "set num_threads=1", "save " + save, "tran 1n %s 0 0.2n" % tstop, "write RAW/b5.raw", ".endc", ".end"]
    od = os.path.join(HERE, "decks", a.tag)
    os.makedirs(od, exist_ok=True)
    open(os.path.join(od, name + ".cir"), "w").write("\n".join(L) + "\n")
    return {"deck": "sim/post/b5/decks/%s/%s.cir" % (a.tag, name), "adc_netlist": netlist, "adc_netlist_sha256": sha(path),
            "corner": [mos, temp, vdd], "frames": frames, "ref": ref, "tstop": tstop, "note": note,
            "unmapped_ports": [], "sar_ports_on_adc": sorted(set(n for n in mconn if n.startswith("sar_")))}


MUXIN = ["Vcme vcme 0 0.6", "Vcmi vcmi 0 0.6",
         "Vsin vsin 0 PWL(0 0.40 1.012u 0.40 1.022u -0.40 2.352u -0.40 2.362u 0.72 6u 0.72)", "Visa visa 0 0.85",
         "Esp sinp vcme vsin 0 0.5", "Esn sinn vcme vsin 0 -0.5", "Ecp cosp vcme vsin 0 -0.5", "Ecn cosn vcme vsin 0 0.5",
         "Eap isap vcmi visa 0 0.5", "Ean isan vcmi visa 0 -0.5", "Ebp isbp vcmi visa 0 -0.5", "Ebn isbn vcmi visa 0 0.5"]


def pts_inputs(pfile, n=None):
    P = json.load(open(os.path.join(ADC, pfile)))
    va, vb = P["a"][:n] if n else P["a"], P["b"][:n] if n else P["b"]
    return va, ["Vcm vcm 0 0.6", "Vda vda 0 PWL(%s)" % pwl_points(va), "Vdb vdb 0 PWL(%s)" % pwl_points(vb),
                "Esp sinp vcm vda 0 0.5", "Esn sinn vcm vda 0 -0.5", "Ecp cosp vcm vdb 0 0.5", "Ecn cosn vcm vdb 0 -0.5",
                "* in1 inputs idle at the common mode (as tb_post_points.cir: both slices on isap / isan = 0.6 V)",
                "Vip isap 0 0.6", "Vin isan 0 0.6", "Vibp isbp 0 0.6", "Vibn isbn 0 0.6"]


rec = {}
rec["mux_tt"] = deck("mux_tt", a.adc_netlist, "tt", "ecee", "lay", MUXIN, "3.31u",
                     "r5 mux sequence e c e e at tt, buffer + bandgap model (as postb4-isa-tt-rc / T2j t2j-ms-h-tt)")
va, inp = pts_inputs("sim/r5/points/fixtt.json")
rec["fc_tt"] = deck("fc_tt", a.adc_netlist, "tt", "ee", "lay-ideal", inp, "1.86u",
                    "first conversion at tt, 0 V, ideal VREF 1.045 V at the follower nodes (as postb4-fc-tt-rc)")
va, inp = pts_inputs("sim/post/points/ffb.json")
rec["fc_ss125"] = deck("fc_ss125", a.adc_netlist, "ss125", "ee", "lay-ideal", inp, "1.86u",
                       "first conversion at ss / 125 C / 1.08 V, A -0.80 V, B -0.781 V (as postb4-fc-ss125-rc)")
va, inp = pts_inputs("sim/r5/points/ref10.json", a.ref_slots)
tst = "%.4fu" % ((18 * T + (len(va) - 1) * 22 * T + 14 * T + 60) * 1e-3)
rec["ref_tt_buf"] = deck("ref_tt_buf", a.adc_netlist, "tt", "e" * len(va), "lay", inp, tst,
                         "R2-4 buffer run at tt, %d slots of sim/r5/points/ref10.json (as postb4-ref-tt-rc)" % len(va),
                         a.ref_probes)
rec["ref_tt_base"] = deck("ref_tt_base", a.adc_netlist_base, "tt", "e" * len(va), "lay", inp, tst,
                          "R2-4 base run at tt: slice reference ports on ideal DC sources (as postb4-ref-tt-sp)")
meta = {"generator": "sim/post/b5/gen_b5_decks.py", "argv": sys.argv[1:], "tag": a.tag, "adc_subckt": a.adc_subckt,
        "sar_release": "<G1_RESULTS_ROOT>/%s" % REL, "sar_gl_sha256": sha(glsrc), "sar_cell": glcell, "sar_par": a.sar_par,
        "sar_include": glinc if glinc != "GLNET" else "<G1_RESULTS_ROOT>/%s/r1_adc_sar_gl_sim.spice" % REL,
        "out_load": a.out_load, "decks": rec}
json.dump(meta, open(os.path.join(HERE, "decks", a.tag, "decks.json"), "w"), indent=1)
for k, v in rec.items():
    print(k, v["deck"], v["corner"], v["frames"], v["tstop"], "sar ports", len(v["sar_ports_on_adc"]))

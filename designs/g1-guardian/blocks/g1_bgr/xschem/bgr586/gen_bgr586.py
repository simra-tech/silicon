"""Hierarchical xschem schematic of BGR586, the bandgap on the chip of record.

Cell bgr_loop24_qref4_r253p465_hv06 ("BGR586", after its netlist hash 586ffb58): the Sep-19
self-biased cascoded HBT bandgap (../gen_g1_bgr.py) with the PTAT/bias loop built from 24
parallel units, the VREF branch from 4 units, R2 units of 53.465 um and the start-up / test NMOS
XM31/XM33 at L = 0.6 um.  Until now it existed only as the flat netlist
../../sim/qualification/candidates/bgr_loop24_qref4_r253p465_hv06/bgr_loop24_qref4_r253p465_hv06.spice
(1036 devices and 329 extraction capacitors Cext_*, LVS reference bank.cdl 7f8e6e8c).

The sheets below draw the same devices as unit sub-sheets instantiated as xschem instance
arrays (name[N-1:0]), so the netlist has one line per physical unit:

  bgr586_pleg   PMOS mirror unit (2 x 5u/4u halves on pbias) + cascode (10u/4u on pcasc, body = source)
  bgr586_pmir   PMOS mirror unit without cascode (start-up copy MPS)
  bgr586_ncas   NMOS collector cascode unit (2 x 10u/1u fingers, drain/source alternating)
  bgr586_hbt    one npn13G2 unit (we=0.07u, le=0.9u)
  bgr586_r1u / _rbu / _rxu / _r2u / _rdetu   one resistor unit of R1, RB, RX, R2, RDET
  bgr586_cext   the 329 extraction capacitors of the candidate netlist (not a design element;
                kept so the drawn netlist is complete; values read from the candidate file)

Device lines use local primitive symbols (b586_*.sym) whose netlist format reproduces the
candidate's parameter set exactly (MOS l/w/as/ad/ps/pd/rfmode, npn we/le/Nx/m, resistors w/l/b/m
with the body terminal), not the PDK symbols' w/l/ng/m/mm_ok set.  Equivalence to the candidate is
recorded in designs/g1-guardian/review/schematics-readability-20260925/README.md.

Run from this directory: python3 gen_bgr586.py   (BGR586_OUT_DIR overrides the output directory)
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.environ.get("BGR586_OUT_DIR", HERE)
CAND = os.path.join(HERE, "..", "..", "sim", "qualification", "candidates", "bgr_loop24_qref4_r253p465_hv06",
                    "bgr_loop24_qref4_r253p465_hv06.spice")


def _find_flow():
    d = HERE
    while not os.path.isdir(os.path.join(d, "flow", "schematic")):
        if os.path.dirname(d) == d:
            raise SystemExit("flow/schematic not found above " + HERE)
        d = os.path.dirname(d)
    return os.path.join(d, "flow", "schematic")


sys.path.insert(0, _find_flow())
from xsch_readable import Sheet, HDR, write_symbol  # noqa: E402

REF = "sim/qualification/candidates/bgr_loop24_qref4_r253p465_hv06/bgr_loop24_qref4_r253p465_hv06.spice sha256 586ffb58"
VAR = ("BGR586 = the chip BGR (cell __rz_port_text_031_g1_bgr_candidate); layout bank.gds e3ecfc62, "
       "LVS reference bank.cdl 7f8e6e8c")
P = lambda *a: os.path.join(OUT, *a)

# ------------------------------------------------------------ primitives --
# pin offsets; drawn in the style of the PDK symbols, netlisted with the candidate's parameter set
MOSN = {"D": (20, -30), "G": (-20, 0), "S": (20, 30), "B": (20, 0)}
MOSP = {"D": (20, 30), "G": (-20, 0), "S": (20, -30), "B": (20, 0)}
NPN = {"C": (20, -30), "B": (-20, 0), "E": (20, 30), "S": (40, 0)}
RES = {"P": (0, -30), "M": (0, 30), "B": (20, 0)}
CAP = {"p": (0, -30), "m": (0, 30)}


def _prim(name, ktype, fmt, template, pins, lines, texts):
    out = [HDR.replace("K {}", 'K {type=%s\nformat="%s"\ntemplate="%s"}' % (ktype, fmt, template))]
    out += ["L 4 %s %s %s %s {}\n" % l for l in lines]
    out += ["T {%s} %s %s 0 0 %s %s {%s}\n" % t for t in texts]
    for p, (x, y) in pins.items():
        out.append("B 5 %s %s %s %s {name=%s dir=inout}\n" % (x - 2.5, y - 2.5, x + 2.5, y + 2.5, p))
    open(P(name), "w").write("".join(out))


def write_primitives():
    mos_fmt = "@name @pinlist @model l=@l w=@w as=@as ad=@ad ps=@ps pd=@pd rfmode=@rfmode"
    gate = [(-20, 0, 5, 0), (5, -20, 5, 20), (10, -22, 10, 22), (10, -18, 20, -18), (20, -18, 20, -30),
            (10, 18, 20, 18), (20, 18, 20, 30), (10, 0, 20, 0)]
    txt = [("@name", 25, -45, 0.2, 0.2, ""), ("w=@w l=@l", 25, -28, 0.18, 0.18, "layer=13"), ("@model", 25, 18, 0.15, 0.15, "layer=13")]
    _prim("b586_nmos.sym", "nmos", mos_fmt, "name=XM1 model=sg13_hv_nmos l=1u w=1u as=0 ad=0 ps=0 pd=0 rfmode=0", MOSN,
          gate + [(14, 15, 20, 18), (14, 21, 20, 18)], txt)
    _prim("b586_pmos.sym", "pmos", mos_fmt, "name=XM1 model=sg13_hv_pmos l=1u w=1u as=0 ad=0 ps=0 pd=0 rfmode=0", MOSP,
          gate + [(10, -18, 16, -21), (10, -18, 16, -15), (-5, 0, -5, 0)], txt)
    _prim("b586_npn.sym", "npn", "@name @pinlist @model we=@we le=@le m=@mult Nx=@Nx",
          "name=XQ1 model=npn13G2 we=0.07u le=0.9u Nx=1 mult=1", NPN,
          [(-20, 0, 0, 0), (0, -15, 0, 15), (0, -6, 20, -20), (20, -20, 20, -30), (0, 6, 20, 20), (20, 20, 20, 30),
           (20, 20, 12, 19), (20, 20, 15, 13), (30, 0, 40, 0)],
          [("@name", 25, -45, 0.2, 0.2, ""), ("@model", 25, -25, 0.15, 0.15, "layer=13"), ("s", 30, -12, 0.12, 0.12, "")])
    zig = [(0, -30, 0, -20), (0, -20, 6, -16), (6, -16, -6, -8), (-6, -8, 6, 0), (6, 0, -6, 8), (-6, 8, 6, 16),
           (6, 16, 0, 20), (0, 20, 0, 30), (8, 0, 20, 0)]
    _prim("b586_res.sym", "resistor", "@name @pinlist @model w=@w l=@l m=@mult b=@b",
          "name=XR1 model=rppd w=1u l=10u b=0 mult=1", RES, zig,
          [("@name", 12, -40, 0.18, 0.18, ""), ("@model @w/@l", 12, 8, 0.15, 0.15, "layer=13")])
    _prim("b586_cap.sym", "capacitor", "@name @pinlist @value", "name=C1 value=1f", CAP,
          [(0, -30, 0, -4), (-10, -4, 10, -4), (-10, 4, 10, 4), (0, 4, 0, 30)],
          [("@name", 12, -20, 0.15, 0.15, ""), ("@value", 12, 4, 0.15, 0.15, "layer=13")])


def mos_attrs(name, model, l, w, a, p):
    return "name=%s model=%s l=%s w=%s as=%s ad=%s ps=%s pd=%s rfmode=0" % (name, model, l, w, a, a, p, p)


HALF = ("4u", "5u", "1.7p", "10.68u")      # mirror half: l, w, as=ad, ps=pd
CASC = ("4u", "10u", "3.4p", "20.68u")     # PMOS cascode
NCAS = ("1u", "10u", "3.4p", "20.68u")     # NMOS collector cascode finger


def glyph_symbol(path, cell, ports, pins, lines, texts):
    """Unit symbol drawn as the device it contains; pin order = subcircuit port order."""
    k = 'type=subcircuit\nformat="@name @pinlist @symname"\ntemplate="name=x1"'
    out = [HDR.replace("K {}", "K {%s}" % k)]
    out += ["L 4 %s %s %s %s {}\n" % l for l in lines]
    out += ["T {%s} %s %s 0 0 %s %s {%s}\n" % t for t in texts]
    for p in ports:
        x, y = pins[p]
        out.append("B 5 %s %s %s %s {name=%s dir=inout}\n" % (x - 2.5, y - 2.5, x + 2.5, y + 2.5, p))
    open(path, "w").write("".join(out))


def res_glyph(cell, label):
    zig = [(0, -50, 0, -24), (0, -24, 8, -20), (8, -20, -8, -12), (-8, -12, 8, -4), (8, -4, -8, 4), (-8, 4, 8, 12),
           (8, 12, -8, 20), (-8, 20, 0, 24), (0, 24, 0, 50), (60, 0, 14, 0)]
    glyph_symbol(P(cell + ".sym"), cell, ["p", "m", "bd"], {"p": (0, -50), "m": (0, 50), "bd": (60, 0)}, zig,
                 [("@name", -70, -28, 0.2, 0.2, ""), (label, -70, -8, 0.15, 0.15, "layer=13"), ("bd", 40, -12, 0.12, 0.12, "")])


def hbt_glyph(cell):
    ls = [(-60, 0, -12, 0), (-12, -20, -12, 20), (-12, -8, 0, -20), (0, -20, 0, -50), (-12, 8, 0, 20), (0, 20, 0, 50),
          (0, 20, -8, 18), (0, 20, -4, 12), (60, 0, 20, 0)]
    glyph_symbol(P(cell + ".sym"), cell, ["c", "b", "e", "s"], {"c": (0, -50), "b": (-60, 0), "e": (0, 50), "s": (60, 0)}, ls,
                 [("@name", 8, -46, 0.2, 0.2, ""), ("npn13G2 unit", 8, 24, 0.15, 0.15, "layer=13"), ("s", 40, -12, 0.12, 0.12, "")])


def unit_sheet(cell, what, ports, build, sym_pins, dirs=None, label=None, shape="box", glyph=None):
    s = Sheet(cell)
    build(s)
    s.title_block(40, -560, cell, what, "the %s subcircuit of the drawn BGR586 netlist (flattened comparison against %s)" % (cell, REF),
                  VAR, width=1000)
    s.write(P(cell + ".sch"))
    if glyph:
        glyph()
    else:
        write_symbol(P(cell + ".sym"), cell, ports, dirs or {}, label=label, shape=shape, **sym_pins)


def build_pleg(s):
    h1 = s.place("b586_pmos.sym", MOSP, "XMA", 200, -300, mos_attrs("XMA", "sg13_hv_pmos", *HALF), {"D": "mid", "G": "pbias", "S": "vdd", "B": "vdd"})
    h2 = s.place("b586_pmos.sym", MOSP, "XMB", 360, -300, mos_attrs("XMB", "sg13_hv_pmos", *HALF), {"D": "mid", "G": "pbias", "S": "vdd", "B": "vdd"})
    mc = s.place("b586_pmos.sym", MOSP, "XMC", 200, -170, mos_attrs("XMC", "sg13_hv_pmos", *CASC), {"D": "out", "G": "pcasc", "S": "mid", "B": "mid"})
    for d in (h1, h2, mc):
        s.wire(d["B"], d["S"])
    s.wire(h1["D"], (220, -235), (380, -235), h2["D"]); s.wire((220, -235), mc["S"])
    s.wire(h1["G"], (170, -300), (170, -340), (330, -340), (330, -300), h2["G"])
    s.wire(h1["S"], (220, -380), (380, -380), h2["S"])
    s.port("out", (220, -60), "out"); s.wire(mc["D"], (220, -60))
    s.port("mid", (500, -235), "inout"); s.wire((380, -235), (500, -235))
    s.port("pbias", (80, -340), "in"); s.wire((80, -340), (170, -340))
    s.port("pcasc", (80, -170), "in"); s.wire((80, -170), mc["G"])
    s.port("vdd", (80, -380), "inout"); s.wire((80, -380), (220, -380))
    s.text("mirror half pair = one 10u/4u mirror unit (MPx); cascode MCx in its own n-well, body = source", 60, -20)


def build_pmir(s):
    h1 = s.place("b586_pmos.sym", MOSP, "XMA", 200, -300, mos_attrs("XMA", "sg13_hv_pmos", *HALF), {"D": "d", "G": "g", "S": "vdd", "B": "vdd"})
    h2 = s.place("b586_pmos.sym", MOSP, "XMB", 360, -300, mos_attrs("XMB", "sg13_hv_pmos", *HALF), {"D": "d", "G": "g", "S": "vdd", "B": "vdd"})
    for d in (h1, h2):
        s.wire(d["B"], d["S"])
    s.wire(h1["D"], (220, -235), (380, -235), h2["D"])
    s.wire(h1["G"], (170, -300), (170, -340), (330, -340), (330, -300), h2["G"])
    s.wire(h1["S"], (220, -380), (380, -380), h2["S"])
    s.port("d", (220, -150), "out"); s.wire((220, -235), (220, -150))
    s.port("g", (80, -340), "in"); s.wire((80, -340), (170, -340))
    s.port("vdd", (80, -380), "inout"); s.wire((80, -380), (220, -380))


def build_ncas(s):
    ma = s.place("b586_nmos.sym", MOSN, "XMA", 200, -250, mos_attrs("XMA", "sg13_hv_nmos", *NCAS), {"D": "a", "G": "g", "S": "b", "B": "vss"})
    mb = s.place("b586_nmos.sym", MOSN, "XMB", 360, -250, mos_attrs("XMB", "sg13_hv_nmos", *NCAS), {"D": "b", "G": "g", "S": "a", "B": "vss"})
    s.wire(ma["D"], (220, -320), (440, -320), (440, -200), (380, -200), mb["S"])
    s.wire(ma["S"], (220, -190), (300, -190), (300, -300), (380, -300), mb["D"])
    s.port("a", (220, -380), "inout"); s.wire((220, -380), (220, -320))
    s.port("b", (220, -120), "inout"); s.wire((220, -190), (220, -120))
    s.port("g", (80, -250), "in"); s.wire((80, -250), ma["G"])
    s.lab(mb["G"], "g", "l")
    s.port("vss", (80, -80), "inout"); s.lab(ma["B"], "vss", "r"); s.lab(mb["B"], "vss", "r")
    s.text("two 10u/1u fingers with drain and source swapped (shared diffusion); gate on vb2", 60, -40)


def build_hbt(s):
    q = s.place("b586_npn.sym", NPN, "XQ", 200, -250, "name=XQ model=npn13G2 we=0.07u le=0.9u Nx=1 mult=1", {"C": "c", "B": "b", "E": "e", "S": "s"})
    s.port("c", (220, -360), "inout"); s.wire(q["C"], (220, -360))
    s.port("b", (80, -250), "in"); s.wire((80, -250), q["B"])
    s.port("e", (220, -140), "inout"); s.wire(q["E"], (220, -140))
    s.port("s", (340, -250), "inout"); s.wire(q["S"], (340, -250))


def res_builder(model, w, l):
    def b(s):
        r = s.place("b586_res.sym", RES, "XR", 200, -250, "name=XR model=%s w=%s l=%s b=0 mult=1" % (model, w, l), {"P": "p", "M": "m", "B": "bd"})
        s.port("p", (200, -340), "inout"); s.wire(r["P"], (200, -340))
        s.port("m", (200, -160), "inout"); s.wire(r["M"], (200, -160))
        s.port("bd", (320, -250), "inout"); s.wire(r["B"], (320, -250))
    return b


RUNITS = {"bgr586_r1u": ("rppd", "1u", "51.5u", "R1 unit"), "bgr586_rbu": ("rppd", "1u", "50u", "RB unit"),
          "bgr586_rxu": ("rppd", "1u", "48u", "RX unit"), "bgr586_r2u": ("rppd", "1u", "53.465u", "R2 unit"),
          "bgr586_rdetu": ("rhigh", "0.5u", "49u", "RDET unit")}


def read_cext():
    caps = []
    for line in open(CAND):
        t = line.split()
        if t and t[0].startswith("Cext_"):
            caps.append((t[0], t[1], t[2], t[3]))
    assert len(caps) == 329, len(caps)
    return caps


def main():
    write_primitives()
    unit_sheet("bgr586_pleg", "PMOS mirror unit + cascode (one PTAT-loop leg unit)", ["out", "mid", "pbias", "pcasc", "vdd"], build_pleg,
               dict(left=["pbias", "pcasc"], right=["mid"], top=["vdd"], bottom=["out"]), {"pbias": "in", "pcasc": "in"}, "MP + MC unit")
    unit_sheet("bgr586_pmir", "PMOS mirror unit (start-up copy MPS)", ["d", "g", "vdd"], build_pmir,
               dict(left=["g"], right=[], top=["vdd"], bottom=["d"]), {"g": "in"}, "MP unit")
    unit_sheet("bgr586_ncas", "NMOS collector cascode unit", ["a", "b", "g", "vss"], build_ncas,
               dict(left=["g"], right=["vss"], top=["a"], bottom=["b"]), {"g": "in"}, "MNC unit")
    unit_sheet("bgr586_hbt", "npn13G2 unit", ["c", "b", "e", "s"], build_hbt,
               dict(left=["b"], right=["s"], top=["c"], bottom=["e"]), {"b": "in"}, "npn unit", glyph=lambda: hbt_glyph("bgr586_hbt"))
    for cell, (model, w, l, what) in RUNITS.items():
        unit_sheet(cell, "%s: %s %s x %s" % (what, model, w, l), ["p", "m", "bd"], res_builder(model, w, l),
                   dict(left=[], right=["bd"], top=["p"], bottom=["m"]), {}, "%s %s/%s" % (model, w, l),
                   glyph=(lambda c=cell, t="%s %s/%s" % (model, w, l): res_glyph(c, t)))
    # extraction capacitors
    caps = read_cext()
    nets = sorted(set([c[1] for c in caps] + [c[2] for c in caps]), key=lambda n: (n.startswith("n_"), len(n), n))
    s = Sheet("bgr586_cext")
    for i, (name, a, b, val) in enumerate(caps):
        x, y = 200 + 140 * (i % 30), -2600 + 160 * (i // 30)
        s.place("b586_cap.sym", CAP, name, x, y, "name=%s value=%s" % (name, val), {"p": a, "m": b})
    for i, n in enumerate(nets):
        s.port(n, (40, -2700 - 30 * i), "inout")
    s.title_block(40, -4600, "bgr586_cext", "329 extraction capacitors of the candidate netlist (not design elements)",
                  "the Cext_* lines of " + REF, VAR, width=2000)
    s.write(P("bgr586_cext.sch"))
    write_symbol(P("bgr586_cext.sym"), "bgr586_cext", nets, {}, label="329 Cext", left=[], right=nets, top=[], bottom=[])
    top(nets)


def top(cext_nets):
    s = Sheet("g1_bgr")
    I = {}

    def unit(name, cell, n, x, y, nets, vflip=False):
        inst = "X%s[%d:0]" % (name, n - 1) if n > 1 else "X" + name
        I[name] = s.inst(inst, cell + ".sym", x, y, nets, rot=2 if vflip else 0, flip=1 if vflip else 0, sympath=P(cell + ".sym"))
        s.text("x%d" % n, x + 70, y - 45, 0.4, layer=5)
        return I[name]

    def mos(name, model, x, y, lw, nets):
        sym, off = ("b586_pmos.sym", MOSP) if "pmos" in model else ("b586_nmos.sym", MOSN)
        I[name] = s.place(sym, off, name, x, y, mos_attrs(name, model, *lw), nets)
        return I[name]

    def chain(prefix, cell, n, x, y0, nodes, pnets, label_nodes=True):
        """Series string drawn top to bottom through nodes[0..k]; pnets[k] is the netlist P terminal of
        segment k (the other end is its M terminal), so every unit keeps its netlist orientation."""
        us = []
        for k in range(len(nodes) - 1):
            up, lo = nodes[k], nodes[k + 1]
            pn = pnets[k]
            mn = lo if pn == up else up
            u = unit("%s%d" % (prefix, k + 1), cell, n, x, y0 + 120 * k, {"p": pn, "m": mn, "bd": "vss"}, vflip=(pn == lo))
            us.append(u)
            s.lab(u["bd"], "vss", "r")
            if k:
                a, b = us[k - 1], u
                ya = a.origin[1] + 50
                s.wire((x, ya), (x, b.origin[1] - 50))
                if label_nodes:
                    s.slab((x, ya + 10), up)
        return us

    YV, YS = -2300, -150
    PL = -2150                                    # PMOS leg row
    legs = {}
    # ---------------------------------------------------------------- start-up
    legs["MPS"] = unit("MPS", "bgr586_pmir", 1, 250, PL, {"d": "det", "g": "pbias", "vdd": "vdd"})
    rdet_nodes = ["det", "n_12", "n_25", "n_13", "n_24", "n_14", "n_26", "n_15", "n_27", "n_16", "n_21", "n_17", "n_22",
                  "n_18", "n_23", "vss"]
    rdet_p = ["n_12", "n_12", "n_13", "n_13", "n_14", "n_14", "n_15", "n_15", "n_16", "n_16", "n_17", "n_17", "n_18", "n_18", "vss"]
    rdet = chain("RDET", "bgr586_rdetu", 1, 250, -1960, rdet_nodes, rdet_p)
    s.wire(legs["MPS"]["d"], rdet[0].pins["p" if rdet[0].pins["p"][1] == "det" else "m"][0])
    s.wire((250, -2080), (400, -2080)); s.wlab((400, -2080), "det")
    s.wire((250, -230), (250, YS))
    x27 = mos("XM27", "sg13_hv_pmos", 460, -1000, ("0.5u", "2u", "0.68p", "4.68u"), {"D": "kick", "G": "det", "S": "vdd", "B": "vdd"})
    x31 = mos("XM31", "sg13_hv_nmos", 460, -870, ("0.6u", "1u", "0.34p", "2.68u"), {"D": "kick", "G": "det", "S": "vss", "B": "vss"})
    x30 = mos("XM30", "sg13_hv_nmos", 580, -700, ("4u", "1u", "0.34p", "2.68u"), {"D": "pbias", "G": "kick", "S": "vss", "B": "vss"})
    s.wire(x27["G"], x31["G"]); s.wire(x27["D"], x31["D"]); s.wire(x27["B"], x27["S"]); s.wire(x31["B"], x31["S"]); s.wire(x30["B"], x30["S"])
    s.stub((440, -935), "det", -40)
    s.wire((480, -935), (540, -935), (540, -700), x30["G"]); s.wlab((530, -935), "kick")
    s.stub(x27["S"], "vdd", 0, -20); s.stub(x31["S"], "vss", 0, 20); s.stub(x30["S"], "vss", 0, 20); s.stub(x30["D"], "pbias", 0, -20)
    # ------------------------------------------------------ cascode bias vb2
    legs["MP5"] = unit("MP5", "bgr586_pleg", 24, 800, PL, {"out": "vb2", "mid": "d5", "pbias": "pbias", "pcasc": "pcasc", "vdd": "vdd"})
    rx = chain("RX", "bgr586_rxu", 24, 800, -1960, ["vb2", "n_6", "n_19", "n_9", "vd1"], ["n_6", "n_6", "n_9", "n_9"])
    s.wire(legs["MP5"]["out"], (800, -2010))
    s.wire((800, -2080), (940, -2080)); s.wlab((940, -2080), "vb2")
    qd1 = unit("QD1", "bgr586_hbt", 24, 800, -1400, {"c": "vd1", "b": "vd1", "e": "vd2", "s": "vss"})
    qd2 = unit("QD2", "bgr586_hbt", 24, 800, -1200, {"c": "vd2", "b": "vd2", "e": "vss", "s": "vss"})
    s.wire((800, -1550), qd1["c"]); s.wire(qd1["b"], (740, -1480), (800, -1480)); s.slab((800, -1520), "vd1")
    s.wire(qd1["e"], qd2["c"]); s.wire(qd2["b"], (740, -1280), (800, -1280)); s.slab((800, -1300), "vd2")
    s.wire(qd2["e"], (800, YS)); s.lab(qd1["s"], "vss", "r"); s.lab(qd2["s"], "vss", "r")
    # ------------------------------------------------------------ Q1 branch
    legs["MP1"] = unit("MP1", "bgr586_pleg", 24, 1300, PL, {"out": "n1", "mid": "d1", "pbias": "pbias", "pcasc": "pcasc", "vdd": "vdd"})
    mnc1 = unit("MNC1", "bgr586_ncas", 24, 1300, -1100, {"a": "n1", "b": "vbe", "g": "vb2", "vss": "vss"})
    q1 = unit("Q1", "bgr586_hbt", 24, 1300, -500, {"c": "vbe", "b": "vbe", "e": "vss", "s": "vss"})
    q1b = unit("Q1B", "bgr586_hbt", 24, 1530, -500, {"c": "vbe", "b": "b1b", "e": "vss", "s": "vss"})
    s.wire(legs["MP1"]["out"], mnc1["a"])
    s.slab((1300, -1800), "n1")
    s.wire(mnc1["b"], q1["c"]); s.wire(q1["b"], (1240, -600), (1300, -600))
    s.wire((1300, -640), (1530, -640), q1b["c"])
    s.wire(q1["e"], (1300, YS)); s.wire(q1b["e"], (1530, YS))
    s.lab(mnc1["g"], "vb2", "l"); s.lab(mnc1["vss"], "vss", "r"); s.lab(q1["s"], "vss", "r"); s.lab(q1b["s"], "vss", "r")
    s.lab(q1b["b"], "b1b", "l")
    # ------------------------------------------------------------ Q2 branch
    legs["MP2"] = unit("MP2", "bgr586_pleg", 24, 1900, PL, {"out": "pbias", "mid": "d2", "pbias": "pbias", "pcasc": "pcasc", "vdd": "vdd"})
    rb = chain("RB", "bgr586_rbu", 24, 1900, -1960,
               ["pbias", "n_4", "n_30", "n_5", "n_31", "n_3", "n_33", "n_10", "n_34", "n_11", "pcasc"],
               ["n_4", "n_4", "n_5", "n_5", "n_3", "n_3", "n_10", "n_10", "n_11", "n_11"])
    s.wire(legs["MP2"]["out"], (1900, -2010))
    s.wire((1900, -2080), (2040, -2080)); s.wlab((2040, -2080), "pbias")
    mnc2 = unit("MNC2", "bgr586_ncas", 24, 1900, -700, {"a": "c2", "b": "pcasc", "g": "vb2", "vss": "vss"}, vflip=True)
    q2 = unit("Q2", "bgr586_hbt", 192, 1900, -500, {"c": "c2", "b": "vbe", "e": "dvbe", "s": "vss"})
    r1 = unit("R1", "bgr586_r1u", 24, 1900, -300, {"p": "vss", "m": "dvbe", "bd": "vss"}, vflip=True)
    s.wire((1900, -830), mnc2["b"]); s.wire((1900, -790), (2040, -790)); s.wlab((2040, -790), "pcasc")
    s.wire(mnc2["a"], q2["c"]); s.slab((1900, -600), "c2")
    s.wire(q2["e"], r1["m"]); s.wire(r1["p"], (1900, YS)); s.lab(r1["bd"], "vss", "r")
    s.lab(mnc2["g"], "vb2", "l"); s.lab(mnc2["vss"], "vss", "r"); s.lab(q2["b"], "vbe", "l"); s.lab(q2["s"], "vss", "r")
    # ---------------------------------------------------------- VREF branch
    legs["MP3"] = unit("MP3", "bgr586_pleg", 4, 2550, PL, {"out": "vref", "mid": "d3", "pbias": "pbias", "pcasc": "pcasc", "vdd": "vdd"})
    r2 = chain("R2", "bgr586_r2u", 4, 2550, -1960, ["vref", "n_7", "n_36", "n_2", "n_37", "n_8", "vbe3"],
               ["n_7", "n_7", "n_2", "n_2", "n_8", "n_8"])
    s.wire(legs["MP3"]["out"], (2550, -2010))
    qref = unit("QREF", "bgr586_hbt", 4, 2550, -1150, {"c": "vbe3", "b": "vbe3", "e": "vss", "s": "vss"})
    s.wire((2550, -1310), qref["c"]); s.wire(qref["b"], (2490, -1230), (2550, -1230)); s.slab((2550, -1260), "vbe3")
    s.wire(qref["e"], (2550, YS)); s.lab(qref["s"], "vss", "r")
    # ---------------------------------------------------------- IPTAT output
    legs["MP4"] = unit("MP4", "bgr586_pleg", 1, 3100, PL, {"out": "iptat", "mid": "d4", "pbias": "pbias", "pcasc": "pcasc", "vdd": "vdd"})
    for k, u in legs.items():
        s.wire(u["vdd"], (u["vdd"][0], YV))
    s.wire((100, YV), (3100, YV)); s.wire((100, YS), (2550, YS))
    # ---------------------------------------------------------- r4 test mode
    x28 = mos("XM28", "sg13_hv_pmos", 3300, -1000, ("0.5u", "2u", "0.68p", "4.68u"), {"D": "r4n", "G": "r4", "S": "vdd", "B": "vdd"})
    x29 = mos("XM29", "sg13_hv_nmos", 3700, -700, ("0.5u", "2u", "0.68p", "4.68u"), {"D": "vbe", "G": "r4", "S": "b1b", "B": "vss"})
    x32 = mos("XM32", "sg13_hv_nmos", 3300, -870, ("0.5u", "1u", "0.34p", "2.68u"), {"D": "r4n", "G": "r4", "S": "vss", "B": "vss"})
    x33 = mos("XM33", "sg13_hv_nmos", 3500, -700, ("0.6u", "1u", "0.34p", "2.68u"), {"D": "b1b", "G": "r4n", "S": "vss", "B": "vss"})
    for d in (x28, x32, x33):
        s.wire(d["B"], d["S"])
    s.lab(x29["B"], "vss", "r")
    s.wire(x28["G"], x32["G"]); s.wire(x28["D"], x32["D"])
    s.wire((3320, -935), (3440, -935), (3440, -700), x33["G"]); s.wlab((3430, -935), "r4n")
    s.stub(x28["S"], "vdd", 0, -20); s.stub(x32["S"], "vss", 0, 20); s.stub(x33["S"], "vss", 0, 20)
    s.stub(x33["D"], "b1b", 0, -20); s.stub(x29["D"], "vbe", 0, -20); s.stub(x29["S"], "b1b", 0, 20); s.stub(x29["G"], "r4", -30)
    # dummies and extraction capacitors
    unit("QDUM", "bgr586_hbt", 9, 3300, -400, {"c": "vss", "b": "vss", "e": "vss", "s": "vss"})
    s.inst("XCEXT", "bgr586_cext.sym", 4100, -1300, dict((n, n) for n in cext_nets), sympath=P("bgr586_cext.sym"))
    # ports, in the candidate's pin order: vdd vss r4 vref iptat pbias pcasc vbe dvbe
    s.port("vdd", (100, YV), "inout", flip=1)
    s.port("vss", (100, YS), "inout", flip=1)
    s.port("r4", (3200, -935), "in"); s.wire((3200, -935), (3280, -935))
    s.port("vref", (2700, -2080), "out"); s.wire((2550, -2080), (2700, -2080))
    s.port("iptat", (3100, -1950), "out"); s.wire(legs["MP4"]["out"], (3100, -1950))
    s.port("pbias", (2100, -2040), "out"); s.wire((2040, -2080), (2040, -2040), (2100, -2040))
    s.port("pcasc", (2100, -750), "out"); s.wire((2040, -790), (2040, -750), (2100, -750))
    s.port("vbe", (1140, -640), "out"); s.wire((1140, -640), (1300, -640))
    s.port("dvbe", (2050, -400), "out"); s.wire((1900, -400), (2050, -400))
    s.frame(140, -2260, 700, -200, "start-up: MPS -> RDET (15 rhigh); det low: kick pulls pbias")
    s.frame(720, -2260, 1040, -1100, "cascode bias vb2 = 2 VBE + I RX")
    s.frame(1080, -2260, 1680, -200, "Q1 branch (vbe), Q1B = r4 test")
    s.frame(1720, -2260, 2300, -200, "Q2 branch: 192 units, dVBE on R1; RB sets pcasc")
    s.frame(2340, -2260, 2900, -1050, "VREF branch x4, Qref x4")
    s.frame(3000, -2260, 3250, -1850, "IPTAT out")
    s.frame(3160, -1100, 3820, -560, "r4 test mode (r4 = 1 adds Q1B)")
    s.text("VREF = VBE(Qref) + (R2/R1) dVBE, dVBE = VT ln 8 (Q1 : Q2 = 24 : 192 units).  Mirror gates on pbias (diode node MP2/MC2),\n"
           "cascodes on pcasc = pbias - I RB.  Simulated (not measured), tt/27 C: VREF 1.04546 V, IPTAT 4.13 uA, nominal TC 8.53 ppm/C\n"
           "(-40..125 C), supply 319.7 uA (blocks/g1_bgr/sim/postlayout/README_bgr586_pex.md).  xN = instance array of N units.", 140, 60)
    s.title_block(140, -2750, "g1_bgr (BGR586)", "self-biased cascoded HBT bandgap, PTAT loop x24, VREF branch x4",
                  REF + " (flattened device comparison)", VAR, width=2600)
    s.write(P("g1_bgr.sch"))


if __name__ == "__main__":
    main()

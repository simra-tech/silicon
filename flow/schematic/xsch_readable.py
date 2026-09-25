"""Readable xschem sheet writer for the G1 schematic generators.

The block generators (``gen_*.py``) describe devices, their exact attributes and
their nets.  This module places them with explicit coordinates, draws
orthogonal wires, puts net labels where wires end and checks, before writing,
that the drawn geometry connects exactly the intended nets.  The check mirrors
the xschem rules that matter here: pins, labels and wire end points join when
they coincide or when one lies on a wire; wires that only cross do not join;
nets with equal label names are one net.  A component without a label would be
auto-named by xschem and change the netlist, so every component gets one
(an automatic ``lab_pin`` at a pin if the generator did not place one).

Only drawing changes.  Device attribute strings, instance order and port order
are the ones of the original label-per-pin generators, so the xschem netlist is
unchanged; review/schematics-readability-20260925 records the proof per sheet.
Written for xschem 3.4.8RC and the IHP SG13G2 xschem symbols (sg13g2_pr/*.sym).
"""
import math
import os
import re

HDR = "v {xschem version=3.4.8RC file_version=1.3}\nG {}\nK {}\nV {}\nS {}\nE {}\n"

# PDK symbols: pin offsets at rotation 0, flip 0 (from sg13g2_pr/*.sym)
MOS_N = {"D": (20, -30), "G": (-20, 0), "S": (20, 30), "B": (20, 0)}
MOS_P = {"D": (20, 30), "G": (-20, 0), "S": (20, -30), "B": (20, 0)}
TWO = {"P": (0, -30), "M": (0, 30)}
PDK = {
    "sg13_hv_nmos": ("sg13g2_pr/sg13_hv_nmos.sym", MOS_N),
    "sg13_lv_nmos": ("sg13g2_pr/sg13_lv_nmos.sym", MOS_N),
    "sg13_hv_pmos": ("sg13g2_pr/sg13_hv_pmos.sym", MOS_P),
    "sg13_lv_pmos": ("sg13g2_pr/sg13_lv_pmos.sym", MOS_P),
    "rppd": ("sg13g2_pr/rppd.sym", TWO),
    "rhigh": ("sg13g2_pr/rhigh.sym", TWO),
    "cap_cmim": ("sg13g2_pr/cap_cmim.sym", {"c0": (0, -30), "c1": (0, 30)}),
    "npn13G2": ("sg13g2_pr/npn13G2.sym", {"C": (20, -30), "B": (-20, 0), "E": (20, 30), "S": (20, 0)}),
    "dpantenna": ("sg13g2_pr/dpantenna.sym", {"d0": (0, 30), "d1": (0, -30)}),
    "dantenna": ("sg13g2_pr/dantenna.sym", {"d0": (0, 30), "d1": (0, -30)}),
}

CHIP = ("G1 guardian, chip of record g1_chip_top_1414_r2.gds 9049e87b (r2 2026-09-25; geometry XOR-identical to r1 629d303a); "
        "block map: g1_padring/reports/signoff-1414-20260924")


def xform(dx, dy, rot, flip):
    """xschem ROTATION() for an offset from the instance origin."""
    if flip:
        dx = -dx
    for _ in range(rot % 4):
        dx, dy = -dy, dx
    return dx, dy


def sym_pins(path):
    """Pin name -> centre offset, in file order, from the B 5 boxes of a .sym."""
    pins = {}
    for line in open(path):
        if line.startswith("B 5 "):
            v = line.split()
            x = (float(v[2]) + float(v[4])) / 2
            y = (float(v[3]) + float(v[5])) / 2
            pins[re.search(r"name=([^ }]+)", line).group(1)] = (x, y)
    return pins


def _poly(pts):
    return "P 4 %d %s {}\n" % (len(pts), " ".join("%s %s" % (_g(round(x, 1)), _g(round(y, 1))) for x, y in pts))


def _bez(a, c, b, t):
    return ((1 - t) ** 2 * a[0] + 2 * (1 - t) * t * c[0] + t * t * b[0], (1 - t) ** 2 * a[1] + 2 * (1 - t) * t * c[1] + t * t * b[1])


def _txt(s):
    return s.replace("{", "(").replace("}", ")")


def _g(v):
    return ("%g" % v)


class Inst:
    def __init__(self, name, pins, origin=(0, 0)):
        self.name, self.pins, self.origin = name, pins, origin      # pin -> ((x, y), net)

    def __getitem__(self, pin):
        return self.pins[pin][0]


class Sheet:
    """One xschem schematic.  Coordinates are xschem units (y grows downwards)."""

    def __init__(self, title):
        self.title = title
        self.dev_lines, self.port_lines, self.lab_lines = [], [], []
        self.wires, self.texts, self.rects = [], [], []
        self.insts = {}
        self.points = []           # (x, y, net or None, kind, ref)
        self.nlab = 0

    # ------------------------------------------------------------ devices --
    def place(self, sym, pinoff, name, x, y, attrs, nets, rot=0, flip=0):
        self.dev_lines.append("C {%s} %s %s %d %d {%s}\n" % (sym, _g(x), _g(y), rot, flip, attrs))
        pins = {}
        for p, (dx, dy) in pinoff.items():
            if p not in nets:
                raise ValueError("%s: pin %s has no net" % (name, p))
            ox, oy = xform(dx, dy, rot, flip)
            pt = (x + ox, y + oy)
            pins[p] = (pt, nets[p])
            self.points.append((pt[0], pt[1], nets[p], "pin", "%s.%s" % (name, p)))
        inst = Inst(name, pins, (x, y))
        self.insts[name] = inst
        return inst

    def mos(self, name, model, x, y, w, l, D, G, S, B, ng=1, m=1, rot=0, flip=0, extra=""):
        sym, off = PDK[model]
        attrs = "name=%s model=%s w=%s l=%s ng=%d m=%d%s" % (name, model, w, l, ng, m, extra)
        return self.place(sym, off, name, x, y, attrs, {"D": D, "G": G, "S": S, "B": B}, rot, flip)

    def res(self, name, x, y, w, l, P, M, b=0, m=1, model="rppd", body=None, rot=0, flip=0):
        sym, off = PDK[model]
        attrs = "name=%s w=%s l=%s model=%s b=%d m=%d" % (name, w, l, model, b, m)
        if body is not None:
            attrs += " body=%s" % body
        return self.place(sym, off, name, x, y, attrs, {"P": P, "M": M}, rot, flip)

    def cap(self, name, x, y, w, l, c0, c1, m=1, rot=0, flip=0):
        sym, off = PDK["cap_cmim"]
        attrs = "name=%s model=cap_cmim w=%s l=%s m=%d" % (name, w, l, m)
        return self.place(sym, off, name, x, y, attrs, {"c0": c0, "c1": c1}, rot, flip)

    def diode(self, name, x, y, w, l, anode, cathode, model="dantenna", rot=0, flip=0):
        sym, off = PDK[model]
        attrs = "name=%s model=%s l=%s w=%s" % (name, model, l, w)
        return self.place(sym, off, name, x, y, attrs, {"d0": anode, "d1": cathode}, rot, flip)

    def inst(self, name, symfile, x, y, nets, params="", rot=0, flip=0, sympath=None):
        """Instance of a local symbol; pin positions are read from sympath (default: symfile)."""
        attrs = "name=%s %s" % (name, params)
        return self.place(symfile, sym_pins(sympath or symfile), name, x, y, attrs, nets, rot, flip)

    # -------------------------------------------------------------- ports --
    def port(self, net, pt, kind="in", flip=0):
        """ipin / opin / iopin at pt.  Call in the original port order."""
        sym = {"in": "ipin", "out": "opin", "inout": "iopin"}[kind]
        self.port_lines.append("C {devices/%s.sym} %s %s 0 %d {name=p%d lab=%s}\n"
                               % (sym, _g(pt[0]), _g(pt[1]), flip, len(self.port_lines), net))
        self.points.append((pt[0], pt[1], net, "port", net))

    # ------------------------------------------------------------- labels --
    def lab(self, pt, net, side="l"):
        """lab_pin at pt; side 'l' writes the name to the left, 'r' to the right."""
        self.nlab += 1
        self.lab_lines.append("C {devices/lab_pin.sym} %s %s 0 %d {name=l%d lab=%s}\n"
                              % (_g(pt[0]), _g(pt[1]), 1 if side == "r" else 0, self.nlab, net))
        self.points.append((pt[0], pt[1], net, "lab", net))

    def wlab(self, pt, net):
        """lab_wire on a horizontal wire: the name is written above the wire, ending at pt."""
        self.nlab += 1
        self.lab_lines.append("C {devices/lab_wire.sym} %s %s 0 0 {name=l%d lab=%s}\n"
                              % (_g(pt[0]), _g(pt[1]), self.nlab, net))
        self.points.append((pt[0], pt[1], net, "lab", net))

    def rail(self, net, y, pins, label_x=None, side="l"):
        """Supply rail at height y: a vertical drop from every pin, one horizontal line, one label."""
        xs = [p[0] for p in pins]
        for p in pins:
            self.wire(p, (p[0], y))
        x0 = min(xs) if label_x is None else label_x
        self.wire((x0, y), (max(xs + [x0]), y))
        self.wire((min(xs + [x0]), y), (x0, y))
        self.lab((x0, y), net, side)

    def tie(self, *devs):
        """Body tied to source, drawn as a wire along the symbol from B to S."""
        for d in devs:
            if d.pins["B"][1] != d.pins["S"][1]:
                raise ValueError("%s: body %s is not its source %s" % (d.name, d.pins["B"][1], d.pins["S"][1]))
            self.wire(d["B"], d["S"])

    def body(self, *devs):
        """Body = source: wire along the symbol.  Otherwise a small body label (g1_body_lab.sym)."""
        for d in devs:
            if d.pins["B"][1] == d.pins["S"][1]:
                self.wire(d["B"], d["S"])
            else:
                self.nlab += 1
                self.uses_body_lab = True
                pt = d["B"]
                self.lab_lines.append("C {g1_body_lab.sym} %s %s 0 0 {name=l%d lab=%s}\n"
                                      % (_g(pt[0]), _g(pt[1]), self.nlab, d.pins["B"][1]))
                self.points.append((pt[0], pt[1], d.pins["B"][1], "lab", d.pins["B"][1]))

    def supplies(self, inst, nets=None, length=20):
        """Short vertical stubs with labels on the top/bottom pins of a block symbol."""
        ox, oy = inst.origin
        for p, (pt, net) in inst.pins.items():
            if nets is not None and net not in nets:
                continue
            if abs(pt[0] - ox) < abs(pt[1] - oy):
                self.stub(pt, net, 0, -length if pt[1] < oy else length, "l" if pt[0] < ox else "r")

    def slab(self, pt, net):
        """Small net label (g1_node_lab.sym) for internal nodes such as resistor-string taps."""
        self.nlab += 1
        self.uses_node_lab = True
        self.lab_lines.append("C {g1_node_lab.sym} %s %s 0 0 {name=l%d lab=%s}\n" % (_g(pt[0]), _g(pt[1]), self.nlab, net))
        self.points.append((pt[0], pt[1], net, "lab", net))

    def stub(self, pt, net, dx=-20, dy=0, side=None):
        """Short wire from pt then a label at its end."""
        end = (pt[0] + dx, pt[1] + dy)
        self.wire(pt, end)
        if side is None:
            side = "r" if dx > 0 else "l"
        self.lab(end, net, side)
        return end

    # -------------------------------------------------------------- wires --
    def wire(self, *pts):
        for a, b in zip(pts, pts[1:]):
            if a == b:
                continue
            if a[0] != b[0] and a[1] != b[1]:
                raise ValueError("diagonal wire %s -> %s in %s" % (a, b, self.title))
            self.wires.append((a, b))

    def hv(self, a, b):
        """Horizontal then vertical."""
        self.wire(a, (b[0], a[1]), b)

    def vh(self, a, b):
        """Vertical then horizontal."""
        self.wire(a, (a[0], b[1]), b)

    def hvh(self, a, b, xm):
        """Horizontal to x = xm, vertical, horizontal."""
        self.wire(a, (xm, a[1]), (xm, b[1]), b)

    def vhv(self, a, b, ym):
        self.wire(a, (a[0], ym), (b[0], ym), b)

    # --------------------------------------------------------- decoration --
    def text(self, s, x, y, size=0.3, layer=None):
        attr = "layer=%d" % layer if layer is not None else ""
        for i, line in enumerate(s.split("\n")):
            self.texts.append("T {%s} %s %s 0 0 %g %g {%s}\n" % (_txt(line), _g(x), _g(y + i * size * 60), size, size, attr))

    def frame(self, x0, y0, x1, y1, label=None, layer=4):
        """Dashed box around a functional group, with its name at the top left."""
        self.rects.append("B %d %s %s %s %s {dash=5 fill=false}\n" % (layer, _g(x0), _g(y0), _g(x1), _g(y1)))
        if label:
            self.text(label, x0 + 8, y0 + 6, 0.3, layer=layer)

    def title_block(self, x, y, cell, what, ref, variant, notes=(), width=1500):
        """Title block: cell, function, chip of record, variant, netlist reference, date."""
        lines = [(cell + " - " + what, 0.55),
                 (CHIP, 0.3),
                 ("On-chip variant: " + variant, 0.3),
                 ("Netlist-equivalent to " + ref, 0.3)]
        lines += [(n, 0.25) for n in notes]
        lines.append(("Drawn 2026-09-25 by the block generator; device sizes (w, l, ng, m) are on each symbol. "
                      "Proof: review/schematics-readability-20260925", 0.25))
        h = 20 + sum(int(s * 60) + 6 for _, s in lines)
        width = max(width, max(int(len(t) * s * 31) + 40 for t, s in lines))
        self.rects.append("B 4 %s %s %s %s {fill=false}\n" % (_g(x), _g(y), _g(x + width), _g(y + h)))
        yy = y + 10
        for s, size in lines:
            self.texts.append("T {%s} %s %s 0 0 %g %g {}\n" % (_txt(s), _g(x + 12), _g(yy), size, size))
            yy += int(size * 60) + 6
        return y + h

    # -------------------------------------------------------------- check --
    def _connect(self):
        pts = self.points
        n = len(pts)
        parent = list(range(n + len(self.wires)))

        def find(i):
            while parent[i] != i:
                parent[i] = parent[parent[i]]
                i = parent[i]
            return i

        def union(i, j):
            parent[find(i)] = find(j)

        def on(w, p):
            (x0, y0), (x1, y1) = w
            if x0 == x1 == p[0]:
                return min(y0, y1) <= p[1] <= max(y0, y1)
            if y0 == y1 == p[1]:
                return min(x0, x1) <= p[0] <= max(x0, x1)
            return False

        bypos = {}
        for i, p in enumerate(pts):
            bypos.setdefault((p[0], p[1]), []).append(i)
        for ids in bypos.values():
            for j in ids[1:]:
                union(ids[0], j)
        for k, w in enumerate(self.wires):
            wi = n + k
            for i, p in enumerate(pts):
                if on(w, p):
                    union(wi, i)
            for k2, w2 in enumerate(self.wires):
                if k2 != k and (on(w, w2[0]) or on(w, w2[1])):
                    union(wi, n + k2)
        comps = {}
        for i in range(n + len(self.wires)):
            comps.setdefault(find(i), []).append(i)
        return comps

    def check(self, autolabel=True):
        """Raise if the drawing joins different nets; add labels to unnamed components."""
        n = len(self.points)
        comps = self._connect()
        errors = []
        for root, ids in comps.items():
            pins = [self.points[i] for i in ids if i < n]
            nets = set(p[2] for p in pins)
            if len(nets) > 1:
                errors.append("short between %s: %s" % (sorted(nets), [p[4] for p in pins]))
                continue
            if not pins:
                errors.append("floating wire %s" % [self.wires[i - n] for i in ids])
                continue
            named = [p for p in pins if p[3] in ("lab", "port")]
            if not named:
                if not autolabel:
                    errors.append("unnamed component %s" % [p[4] for p in pins])
                    continue
                p = pins[0]
                owner = self.insts.get(p[4].split(".")[0]) if p[3] == "pin" else None
                side = "r" if owner is not None and p[0] > owner.origin[0] else "l"
                self.lab((p[0], p[1]), p[2], side)
        if errors:
            raise ValueError("%s:\n  " % self.title + "\n  ".join(errors))
        return comps

    def write(self, path):
        self.check()
        if getattr(self, "uses_node_lab", False):
            write_node_label(os.path.join(os.path.dirname(os.path.abspath(path)), "g1_node_lab.sym"))
        if getattr(self, "uses_body_lab", False):
            write_body_label(os.path.join(os.path.dirname(os.path.abspath(path)), "g1_body_lab.sym"))
        body = [HDR]
        body += self.rects + self.texts + self.dev_lines + self.port_lines + self.lab_lines
        body += ["N %s %s %s %s {}\n" % (_g(a[0]), _g(a[1]), _g(b[0]), _g(b[1])) for a, b in self.wires]
        with open(path, "w") as f:
            f.write("".join(body))


# ------------------------------------------------------------------ symbols --
def write_node_label(path):
    """Small net label: netlists like devices/lab_pin.sym (type=label, no netlist line)."""
    with open(path, "w") as f:
        f.write(HDR.replace("K {}", 'K {type=label\nformat="*.alias @lab"\ntemplate="name=l1 lab=n"}')
                + "B 5 -1.25 -1.25 1.25 1.25 {name=p dir=inout}\n"
                + "T {@lab} -4 -2 0 1 0.14 0.14 {layer=4}\n")


def write_body_label(path):
    """Net label for a MOS body that is not its source: same netlisting as devices/lab_pin.sym
    (type=label, no netlist line), drawn as a small 'b:<net>' tag inside the MOS symbol."""
    with open(path, "w") as f:
        f.write(HDR.replace("K {}", 'K {type=label\nformat="*.alias @lab"\ntemplate="name=l1 lab=vss"}')
                + "B 5 -1.25 -1.25 1.25 1.25 {name=p dir=inout}\n"
                + "T {b:@lab} -3 3 0 1 0.12 0.12 {layer=4}\n")


SUPPLY_TOP = ("vdd", "vdda", "vdd12", "VDD", "VDDA")
SUPPLY_BOT = ("vss", "VSS")


def write_symbol(path, cell, pins, dirs=None, label=None, shape="box", left=None, right=None,
                 top=None, bottom=None, width=None, schematic=None, ktype="subcircuit", names=None, netlist_name=None):
    """Symbol with inputs left, outputs right, supplies top/bottom.

    The B 5 pin boxes are written in the order of `pins`, which is the order xschem
    uses for the subcircuit pin list, so the netlist does not change with the drawing.
    shape: box | inv | nand | nor | amp.
    """
    dirs = dirs or {}
    if left is None:
        left = [p for p in pins if dirs.get(p) == "in" and p not in SUPPLY_TOP + SUPPLY_BOT]
    if top is None:
        top = [p for p in pins if p in SUPPLY_TOP]
    if bottom is None:
        bottom = [p for p in pins if p in SUPPLY_BOT]
    if right is None:
        right = [p for p in pins if p not in left + top + bottom]
    assert sorted(left + right + top + bottom) == sorted(pins), (cell, pins)
    nside = max(len(left), len(right), 1)
    h = max(20 * (nside + 1), 60)
    if width is None:
        longest = max([len(p) for p in left] + [0]) + max([len(p) for p in right] + [0])
        width = max(80, 20 * ((longest * 9 + 40) // 20 + 1), 40 * len(top) + 20, 40 * len(bottom) + 20)
    if shape in ("inv", "nand", "nor", "amp"):
        width = max(width, 80)
    hw, hh = width // 2, h // 2
    pos = {}
    for i, p in enumerate(left):
        pos[p] = (-hw - 20, -hh + 20 * (i + 1) + (h - 20 * (len(left) + 1)) // 2)
    for i, p in enumerate(right):
        pos[p] = (hw + 20, -hh + 20 * (i + 1) + (h - 20 * (len(right) + 1)) // 2)
    for i, p in enumerate(top):
        pos[p] = (-40 * (len(top) - 1) // 2 + 40 * i, -hh - 20)
    for i, p in enumerate(bottom):
        pos[p] = (-40 * (len(bottom) - 1) // 2 + 40 * i, hh + 20)
    k = 'type=%s\nformat="@name @pinlist %s"\ntemplate="name=x1"' % (ktype, netlist_name or "@symname")
    if schematic:
        k += "\nschematic=%s" % schematic
    out = [HDR.replace("K {}", "K {%s}" % k)]
    # body
    if shape == "box":
        out.append("B 4 %d %d %d %d {fill=false}\n" % (-hw, -hh, hw, hh))
    elif shape in ("inv", "amp"):
        tip = hw - (10 if shape == "inv" else 0)
        out.append("L 4 %d %d %d %d {}\nL 4 %d %d %d 0 {}\nL 4 %d %d %d 0 {}\n" % (-hw, -hh, -hw, hh, -hw, -hh, tip, -hw, hh, tip))
        if shape == "inv":
            out.append("A 4 %d 0 5 0 360 {}\n" % (tip + 5))
    elif shape == "nand":
        x0 = hw - 10 - hh
        arc = [(x0 + hh * math.cos(math.radians(t)), hh * math.sin(math.radians(t))) for t in range(-90, 91, 10)]
        out.append(_poly([(x0, hh), (-hw, hh), (-hw, -hh), (x0, -hh)] + arc))
        out.append("A 4 %d 0 5 0 360 {}\n" % (hw - 5))
    elif shape == "nor":
        tip = hw - 10
        back = [(-hw + 12 * (1 - (y / hh) ** 2), y) for y in [hh * k / 8 for k in range(8, -9, -1)]]
        top = [_bez((-hw, -hh), (hw * 0.2, -hh), (tip, 0), t / 10) for t in range(0, 11)]
        bot = [_bez((tip, 0), (hw * 0.2, hh), (-hw, hh), t / 10) for t in range(1, 11)]
        out.append(_poly(back + top + bot))
        out.append("A 4 %d 0 5 0 360 {}\n" % (hw - 5))
    else:
        raise ValueError(shape)
    # pins, stubs and names
    for p in pins:
        x, y = pos[p]
        if p in left:
            xin = -hw + (12 * (1 - (y / hh) ** 2) if shape == "nor" else 0)
            out.append("L 4 %d %d %s %d {}\n" % (x, y, _g(round(xin, 1)), y))
            out.append("T {%s} %d %d 0 0 0.2 0.2 {}\n" % ((names or {}).get(p, p), -hw + 4, y - 7))
        elif p in right:
            out.append("L 4 %d %d %d %d {}\n" % (hw, y, x, y))
            out.append("T {%s} %d %d 0 1 0.2 0.2 {}\n" % ((names or {}).get(p, p), hw - 4 - (12 if shape in ("inv", "nand", "nor") else 0), y - 7))
        elif p in top:
            out.append("L 4 %d %d %d %d {}\n" % (x, y, x, -hh))
            out.append("T {%s} %d %d 0 0 0.15 0.15 {}\n" % (p, x + 3, y - 2))
        else:
            out.append("L 4 %d %d %d %d {}\n" % (x, hh, x, y))
            out.append("T {%s} %d %d 0 0 0.15 0.15 {}\n" % (p, x + 3, y - 10))
    if shape == "box":
        out.append("T {@name} %d %d 0 0 0.22 0.22 {}\n" % (-hw + 4, -hh + 3))
        out.append("T {%s} %d %d 0 0 0.18 0.18 {layer=13}\n" % (label or cell, -hw + 4, hh - 15))
    else:
        out.append("T {@name} %d %d 0 0 0.25 0.25 {}\n" % (-hw, -hh - 38))
        out.append("T {%s} %d %d 0 0 0.2 0.2 {layer=13}\n" % (label or cell, -hw, -hh - 20))
    for p in pins:
        x, y = pos[p]
        out.append("B 5 %s %s %s %s {name=%s dir=%s}\n" % (_g(x - 2.5), _g(y - 2.5), _g(x + 2.5), _g(y + 2.5), p, dirs.get(p, "inout")))
    with open(path, "w") as f:
        f.write("".join(out))
    return pos

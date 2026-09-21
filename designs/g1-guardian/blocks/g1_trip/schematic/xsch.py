"""Minimal xschem schematic/symbol writer used by the G1 analog block generators.

Devices are placed on a grid and every pin gets a `devices/lab_pin.sym` label
carrying its net name, so the netlist is defined by the labels and not by
drawn wires.  Pin offsets below are those of the IHP SG13G2 xschem symbols
(sg13g2_pr/*.sym) at rotation 0, flip 0.  Written for xschem 3.4.8RC.
"""

HDR = "v {xschem version=3.4.8RC file_version=1.3}\nG {}\nK {}\nV {}\nS {}\nE {}\n"

# pin name -> (dx, dy) at rot 0 flip 0
PINS = {
    "nmos": {"D": (20, -30), "G": (-20, 0), "S": (20, 30), "B": (20, 0)},
    "pmos": {"D": (20, 30), "G": (-20, 0), "S": (20, -30), "B": (20, 0)},
    "res": {"P": (0, -30), "M": (0, 30)},
    "cap": {"c0": (0, -30), "c1": (0, 30)},
}
SYM = {
    "sg13_hv_nmos": ("sg13g2_pr/sg13_hv_nmos.sym", "nmos"),
    "sg13_hv_pmos": ("sg13g2_pr/sg13_hv_pmos.sym", "pmos"),
    "sg13_lv_nmos": ("sg13g2_pr/sg13_lv_nmos.sym", "nmos"),
    "sg13_lv_pmos": ("sg13g2_pr/sg13_lv_pmos.sym", "pmos"),
    "rppd": ("sg13g2_pr/rppd.sym", "res"),
    "cap_cmim": ("sg13g2_pr/cap_cmim.sym", "cap"),
}


class Sch:
    def __init__(self, title=""):
        self.lines = [HDR]
        self.n = 0
        self.title = title
        if title:
            self.lines.append("T {%s} 0 -40 0 0 0.4 0.4 {}\n" % title)

    def _lab(self, x, y, net):
        self.n += 1
        self.lines.append("C {devices/lab_pin.sym} %g %g 0 0 {name=l%d lab=%s}\n" % (x, y, self.n, net))

    def mos(self, name, model, x, y, w, l, D, G, S, B, ng=1, m=1):
        sym, kind = SYM[model]
        self.lines.append("C {%s} %g %g 0 0 {name=%s model=%s w=%s l=%s ng=%d m=%d}\n" % (sym, x, y, name, model, w, l, ng, m))
        for pin, net in (("D", D), ("G", G), ("S", S), ("B", B)):
            dx, dy = PINS[kind][pin]
            self._lab(x + dx, y + dy, net)

    def res(self, name, x, y, w, l, P, M, b=0, m=1, model="rppd"):
        sym, kind = SYM[model]
        self.lines.append("C {%s} %g %g 0 0 {name=%s w=%s l=%s model=%s b=%d m=%d}\n" % (sym, x, y, name, w, l, model, b, m))
        dx, dy = PINS[kind]["P"]; self._lab(x + dx, y + dy, P)
        dx, dy = PINS[kind]["M"]; self._lab(x + dx, y + dy, M)

    def cap(self, name, x, y, w, l, c0, c1, m=1):
        sym, kind = SYM["cap_cmim"]
        self.lines.append("C {%s} %g %g 0 0 {name=%s model=cap_cmim w=%s l=%s m=%d}\n" % (sym, x, y, name, w, l, m))
        dx, dy = PINS[kind]["c0"]; self._lab(x + dx, y + dy, c0)
        dx, dy = PINS[kind]["c1"]; self._lab(x + dx, y + dy, c1)

    def inst(self, name, symfile, pins, x, y, nets, params=""):
        """Instance of a locally generated symbol; `pins` is the list used by Sym()."""
        self.lines.append("C {%s} %g %g 0 0 {name=%s %s}\n" % (symfile, x, y, name, params))
        for i, p in enumerate(pins):
            px, py = Sym.pinpos(i, len(pins))
            self._lab(x + px, y + py, nets[p])

    def ports(self, x, y, ins=(), outs=(), ios=()):
        for i, p in enumerate(ins):
            self.lines.append("C {devices/ipin.sym} %g %g 0 0 {name=pi%d lab=%s}\n" % (x, y + 20 * i, i, p))
        y += 20 * len(ins)
        for i, p in enumerate(outs):
            self.lines.append("C {devices/opin.sym} %g %g 0 0 {name=po%d lab=%s}\n" % (x, y + 20 * i, i, p))
        y += 20 * len(outs)
        for i, p in enumerate(ios):
            self.lines.append("C {devices/iopin.sym} %g %g 0 0 {name=pb%d lab=%s}\n" % (x, y + 20 * i, i, p))

    def text(self, s, x, y):
        self.lines.append("T {%s} %g %g 0 0 0.3 0.3 {}\n" % (s.replace("{", "(").replace("}", ")"), x, y))

    def write(self, path):
        with open(path, "w") as f:
            f.write("".join(self.lines))


class Sym:
    """Rectangular symbol: pins on the left edge, 20 units apart, matching Sch.inst()."""

    @staticmethod
    def pinpos(i, n):
        return (-60, -20 * (n - 1) / 2 * 0 + 20 * i - 20 * (n - 1) // 2)

    @staticmethod
    def write(path, name, pins, dirs=None):
        n = len(pins)
        h = 20 * n
        out = [HDR.replace("K {}", "K {type=subcircuit\nformat=\"@name @pinlist @symname\"\ntemplate=\"name=x1\"}")]
        out.append("L 4 -50 %g 50 %g {}\nL 4 50 %g 50 %g {}\nL 4 50 %g -50 %g {}\nL 4 -50 %g -50 %g {}\n" % (-h / 2, -h / 2, -h / 2, h / 2, h / 2, h / 2, h / 2, -h / 2))
        out.append("T {%s} -45 %g 0 0 0.3 0.3 {}\n" % (name, -h / 2 - 20))
        for i, p in enumerate(pins):
            x, y = Sym.pinpos(i, n)
            d = (dirs or {}).get(p, "inout")
            out.append("L 4 %g %g %g %g {}\n" % (x, y, x + 10, y))
            out.append("B 5 %g %g %g %g {name=%s dir=%s}\n" % (x - 2.5, y - 2.5, x + 2.5, y + 2.5, p, d))
            out.append("T {%s} %g %g 0 0 0.2 0.2 {}\n" % (p, x + 12, y - 4))
        with open(path, "w") as f:
            f.write("".join(out))

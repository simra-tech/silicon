#!/usr/bin/env python3
"""g1_ls_up layout: 1.2 V -> 3.3 V level shifter cell of the g1_ls library, built from the
PDK MOS PCells (SG13_dev: nmos, pmos, nmosHV, pmosHV) plus hand-drawn well/substrate ties,
Metal1/Metal2 wiring, one ThickGateOx rectangle over the 3.3 V part, pin labels and a prBoundary (189/4).

Devices (must match ../xschem/gen_ls.py SIZES):
  MPI  sg13_lv_pmos 2/0.13     LV inverter (vdd well)           MNI  sg13_lv_nmos 1/0.13
  MN1  sg13_hv_nmos 3.8/0.45   pull-down of nb, gate = in      MN2  sg13_hv_nmos 3.8/0.45  gate = inb
  MP1  sg13_hv_pmos 0.3/0.45   keeper of nb, gate = n          MP2  sg13_hv_pmos 0.3/0.45  gate = nb
  MPO  sg13_hv_pmos 3.9/0.45   output inverter (vdda well)     MNO  sg13_hv_nmos 1.9/0.45

Floorplan (design coordinates, um; the written cell is shifted so its lower-left is (0,0)):
  LV column at x = -3.70 (own NWell on vdd, 1.96 um from the vdda NWell: NW.b1 1.8),
  HV NMOS row with Activ bottom at y = 0, HV PMOS row at y = 5.10 inside one NWell on vdda
  (-0.62..4.55 x 4.48..9.62), one ThickGateOx rectangle -0.90..4.90 x -1.90..9.80.
  vss rail along the bottom over two p+ substrate ties, vdda rail on top, vdd rail top-left.
  Signals in/inb/n/nb on Metal2 (0.20 um), everything else Metal1; via pads 0.30 x 0.30 Metal1.
Rule values used (DRC deck at PDK commit 8437402): Act.b 0.21, Gat.b1 0.25, Gat.d 0.07,
  Cnt.a 0.16, Cnt.b 0.18, Cnt.c/d 0.07, Cnt.e 0.14, Cnt.f 0.11, M1.a/b 0.16/0.18, V1.a 0.19,
  V1.c1 0.05, M2.a/b 0.20/0.21, pSD.c1 0.03, pSD.d 0.18, pSD.d1 0.03, pSD.j1 0.40, NW.b1 1.8,
  NW.c 0.31, NW.d1 0.62, NW.e 0.24, NW.f1 0.62, TGO.a/b 0.27, TGO.c/d 0.34.

Run inside the pinned container (KLayout 0.30.9, PDK commit 8437402):
  G1_WORKDIR=designs/g1-guardian/blocks/g1_ctrl/ls/layout flow/run.sh klayout -b -r g1_ls_up.py
Writes g1_ls_up.gds (top cell g1_ls_up), g1_ls_up.lef and g1_ls_up.vh next to this script.
"""
import os, sys
K = '/foss/pdks/ihp-sg13g2/libs.tech/klayout/python'
for p in [K, K + '/pycell4klayout-api/source/python']:
    sys.path.insert(0, p)
import pya
import sg13g2_pycell_lib  # registers library SG13_dev (technology sg13g2)

HERE = os.path.dirname(os.path.abspath(__file__))
lib = pya.Library.library_by_name('SG13_dev', 'sg13g2')
LAYERS = {'Activ': (1, 0), 'GatPoly': (5, 0), 'Cont': (6, 0), 'M1': (8, 0), 'M1pin': (8, 2), 'M1txt': (8, 25),
          'M2': (10, 0), 'M2pin': (10, 2), 'M2txt': (10, 25), 'Via1': (19, 0), 'pSD': (14, 0),
          'NWell': (31, 0), 'TGO': (44, 0), 'prBoundary': (189, 4)}
CONT, VIA = 0.16, 0.19
OX, OY = 4.30, 1.90            # shift so that the cell's lower-left corner is (0, 0)
CELL_W, CELL_H = 9.20, 11.70   # cell size (um)

def um(v):
    return int(round(v * 1000))

class Draw:
    def __init__(self, ly, cell):
        self.ly, self.cell = ly, cell
        self.L = {n: ly.layer(*v) for n, v in LAYERS.items()}
        self.pins = []   # (name, layer, box) for the LEF
    def box(self, layer, x1, y1, x2, y2):
        self.cell.shapes(self.L[layer]).insert(pya.Box(um(x1 + OX), um(y1 + OY), um(x2 + OX), um(y2 + OY)))
    def square(self, layer, cx, cy, size):
        self.box(layer, cx - size / 2, cy - size / 2, cx + size / 2, cy + size / 2)
    def label(self, layer, x, y, text):
        t = pya.Text(text, pya.Trans(pya.Point(um(x + OX), um(y + OY))))
        t.size = um(0.2)
        self.cell.shapes(self.L[layer]).insert(t)
    def pin(self, name, metal, x1, y1, x2, y2):
        """pin rectangle on Metal1 or Metal2 (drawing + pin datatype + text)"""
        self.box(metal, x1, y1, x2, y2)
        self.box(metal + 'pin', x1, y1, x2, y2)
        self.label(metal + 'txt', (x1 + x2) / 2, (y1 + y2) / 2, name)
        self.pins.append((name, 'Metal1' if metal == 'M1' else 'Metal2', (x1 + OX, y1 + OY, x2 + OX, y2 + OY)))
    def pcell(self, name, w, l, x, y):
        pcv = lib.layout().add_pcell_variant(lib.layout().pcell_id(name), {'w': '%gu' % w, 'l': '%gu' % l, 'ng': 1})
        cell = self.ly.cell(self.ly.add_lib_cell(lib, pcv))
        self.cell.insert(pya.CellInstArray(cell.cell_index(), pya.Trans(pya.Point(um(x + OX), um(y + OY)))))
    def m1pad(self, cx, cy, via=True):
        """0.30 x 0.30 Metal1 pad, with a Via1 (and a 0.29 x 0.29 Metal2 pad) when via=True"""
        self.square('M1', cx, cy, 0.30)
        if via:
            self.square('Via1', cx, cy, VIA)
            self.square('M2', cx, cy, 0.29)
    def gate_pad(self, gx1, gx2, y_from, y_to, via=True):
        """poly tab from the PCell end cap (y_from) to y_to with one contact and a Metal1 pad;
        the Metal1 pad is 0.30 wide, centred on the gate; returns the contact centre"""
        cy = (y_from + y_to) / 2
        cx = (gx1 + gx2) / 2
        self.box('GatPoly', gx1, min(y_from, y_to), gx2, max(y_from, y_to))
        self.square('Cont', cx, cy, CONT)
        self.m1pad(cx, cy, via)
        return cx, cy
    def m2h(self, y, x1, x2, w=0.20):
        """Metal2 wire along y between the centre points x1 and x2, ends extended by w/2 so that
        a horizontal and a vertical wire meeting at a point form a full corner (no M2.a notch)"""
        self.box('M2', min(x1, x2) - w / 2, y - w / 2, max(x1, x2) + w / 2, y + w / 2)
    def m2v(self, x, y1, y2, w=0.20):
        self.box('M2', x - w / 2, min(y1, y2) - w / 2, x + w / 2, max(y1, y2) + w / 2)
    def tap(self, kind, x1, y1, x2, y2, cx_list, cy):
        """n+ (kind='n', inside an NWell) or p+ (kind='p', pSD ring) tie: Activ box, contacts, Metal1"""
        self.box('Activ', x1, y1, x2, y2)
        if kind == 'p':
            self.box('pSD', x1 - 0.03, y1 - 0.03, x2 + 0.03, y2 + 0.03)
        for cx in cx_list:
            self.square('Cont', cx, cy, CONT)
        self.box('M1', x1, y1, x2, y2)

def build():
    ly = pya.Layout(); ly.dbu = 0.001
    top = ly.create_cell('g1_ls_up')
    D = Draw(ly, top)

    # ------------------------------------------------------------------ devices
    D.pcell('nmos',   1.0, 0.13, -3.70, 0.00)   # MNI: S -3.63..-3.47, D -3.12..-2.96, poly -3.36..-3.23 x -0.18..1.18
    D.pcell('pmos',   2.0, 0.13, -3.70, 5.10)   # MPI: same x, Activ y 5.10..7.10, poly y 4.92..7.28
    D.pcell('nmosHV', 3.8, 0.45,  0.00, 0.00)   # MN1: S 0.07..0.23, D 0.90..1.06, poly 0.34..0.79 x -0.18..3.98
    D.pcell('nmosHV', 3.8, 0.45,  1.40, 0.00)   # MN2: S 1.47..1.63, D 2.30..2.46, poly 1.74..2.19
    D.pcell('nmosHV', 1.9, 0.45,  2.80, 0.00)   # MNO: S 2.87..3.03, D 3.70..3.86, poly 3.14..3.59 x -0.18..2.08
    D.pcell('pmosHV', 0.3, 0.45,  0.00, 5.10)   # MP1: S 0.07..0.23, D 0.90..1.06, poly 0.34..0.79 x 4.92..5.58
    D.pcell('pmosHV', 0.3, 0.45,  1.40, 5.10)   # MP2: S 1.47..1.63, D 2.30..2.46, poly 1.74..2.19
    D.pcell('pmosHV', 3.9, 0.45,  2.80, 5.10)   # MPO: S 2.87..3.03, D 3.70..3.86, poly 3.14..3.59 x 4.92..9.18

    # wells and thick oxide: one NWell per supply, one ThickGateOx over the whole 3.3 V part
    D.box('NWell', -4.01, 4.79, -2.58, 8.14)    # vdd well (LV PMOS + its tie)
    D.box('NWell', -0.62, 4.48,  4.55, 9.62)    # vdda well (HV PMOS + tie)
    D.box('TGO',   -0.90, -1.90, 4.90, 9.80)

    # ------------------------------------------------------------------ LV inverter (in -> inb)
    # gate: poly strip joins the two gates, tab to the left with the contact
    D.box('GatPoly', -3.36, 1.18, -3.23, 4.92)
    D.box('GatPoly', -3.70, 2.85, -3.23, 3.15)
    D.square('Cont', -3.55, 3.00, CONT)
    D.m1pad(-3.55, 3.00)                                     # via to the in Metal2
    # inb: drain strips joined on Metal1, via pad for the Metal2 wire
    D.box('M1', -3.12, 1.00, -2.96, 5.10)
    D.m1pad(-3.04, 2.00)
    # vdd: source strip up to the n+ tie and the rail
    D.box('M1', -3.63, 7.10, -3.47, 7.50)
    D.tap('n', -3.63, 7.50, -2.96, 7.90, [-3.48, -3.14], 7.70)     # Cnt.b 0.18 between the contacts, Cnt.c 0.07 to the Activ edge
    D.pin('vdd', 'M1', -4.10, 7.90, -2.50, 8.30)
    # vss: source strip down to the rail
    D.box('M1', -3.63, -1.05, -3.47, 0.00)

    # ------------------------------------------------------------------ HV NMOS gates (bottom pads)
    D.gate_pad(0.34, 0.79, -0.18, -0.62)     # MN1 gate = in   (contact at (0.565, -0.40))
    D.gate_pad(1.74, 2.19, -0.18, -0.62)     # MN2 gate = inb
    D.gate_pad(3.14, 3.59, -0.18, -0.62)     # MNO gate = nb
    # sources to the vss rail
    for xs in (0.07, 1.47, 2.87):
        D.box('M1', xs, -1.05, xs + 0.16, 0.00)
    # ------------------------------------------------------------------ HV PMOS gates
    D.gate_pad(0.34, 0.79, 4.92, 4.43)       # MP1 gate = n   (bottom pad, contact (0.565, 4.675))
    D.gate_pad(3.14, 3.59, 4.92, 4.43)       # MPO gate = nb  (bottom pad)
    D.gate_pad(1.74, 2.19, 5.58, 6.37)       # MP2 gate = nb  (top pad, contact (1.965, 5.975))
    # sources to the vdda rail (through the n+ tie)
    for xs in (0.07, 1.47):
        D.box('M1', xs, 5.40, xs + 0.16, 9.30)
    D.box('M1', 2.87, 9.00, 3.03, 9.30)
    D.tap('n', 0.07, 6.80, 2.46, 7.20, [0.22 + 0.34 * i for i in range(7)], 7.00)   # Cnt.c 0.07 enclosure, Cnt.b 0.18
    D.pin('vdda', 'M1', -0.30, 9.30, 4.30, 9.70)

    # ------------------------------------------------------------------ nb and n verticals (Metal1)
    D.box('M1', 0.90, 3.80, 1.06, 6.30)      # nb: MN1 drain -> MP1 drain -> pad for MP2 gate wire
    D.m1pad(0.98, 4.10)                      # via: nb wire to MPO/MNO gates
    D.m1pad(0.98, 6.15)                      # via: nb wire to MP2 gate
    D.box('M1', 2.30, 3.80, 2.46, 5.10)      # n: MN2 drain -> MP2 drain
    D.m1pad(2.38, 4.65)                      # via: n wire to MP1 gate
    D.box('M1', 3.70, 1.90, 3.86, 5.10)      # out: MNO drain -> MPO drain
    D.pin('out', 'M1', 3.70, 2.20, 4.90, 3.80)   # to the right cell edge (Metal1 access from the side, Metal2 window in the LEF)

    # ------------------------------------------------------------------ Metal2 wiring
    # n: MP1 gate pad (0.565, 4.675) <- n via pad (2.38, 4.65)
    D.m2h(4.65, 0.565, 2.38)
    # nb: via pad (0.98, 4.10) -> MPO gate pad (3.365, 4.675) and down to MNO gate pad (3.365, -0.40)
    D.m2h(4.10, 0.98, 3.365)
    D.m2v(3.365, -0.40, 4.675)
    # nb: via pad (0.98, 6.15) -> MP2 gate pad (1.965, 5.975)
    D.m2h(6.15, 0.98, 1.965)
    D.m2v(1.965, 5.975, 6.15)
    # in: LV gate contact (-3.55, 3.00) -> down the left -> along the bottom -> MN1 gate pad (0.565, -0.40)
    D.m2v(-3.55, -0.40, 3.00)
    D.m2h(-0.40, -3.55, 0.565)
    D.pin('in', 'M2', -4.30, 2.90, -3.45, 3.10)
    # inb: LV drain via (-3.04, 2.00) -> right -> down -> MN2 gate pad (1.965, -0.40)
    D.m2h(2.00, -3.04, 1.965)
    D.m2v(1.965, -0.40, 2.00)

    # ------------------------------------------------------------------ substrate ties and vss rail
    D.tap('p', -3.80, -1.58, -2.80, -1.08, [-3.55, -3.05], -1.33)
    D.tap('p', -0.30, -1.58, 4.20, -1.08, [-0.15 + 0.35 * i for i in range(13)], -1.33)
    D.pin('vss', 'M1', -4.10, -1.60, 4.40, -1.05)

    # placement boundary of the cell (prBoundary 189/4), the LEF SIZE; the chip flow's macro
    # abstraction (magic, MAGIC_MACRO_STD_CELL_SOURCE) and KLayout's LEF/DEF import expect it
    top.shapes(D.L['prBoundary']).insert(pya.Box(0, 0, um(CELL_W), um(CELL_H)))

    out = os.path.join(HERE, 'g1_ls_up.gds')
    ly.write(out)
    bb = top.dbbox()
    print('wrote', out, 'bbox', bb, 'cell size', CELL_W, 'x', CELL_H)
    write_lef(D, ly, top)
    write_vh()
    return ly, top

def rectangles(region):
    """axis-aligned rectangle cover of a merged rectilinear Region: cut it into horizontal bands at
    every polygon vertex y, then take each band's x extents (all edges here are axis-aligned)"""
    ys = set()
    for poly in region.each():
        ys.update(pt.y for pt in poly.each_point_hull())
        for h in range(poly.holes()):
            ys.update(pt.y for pt in poly.each_point_hole(h))
    ys = sorted(ys)
    rects = []
    for y1, y2 in zip(ys, ys[1:]):
        band = region & pya.Region(pya.Box(region.bbox().left, y1, region.bbox().right, y2))
        band.merge()
        for poly in band.each():
            rects.append(poly.bbox())      # a band of a rectilinear region merged without holes is a set of rectangles
    return rects

# Metal2 access windows over the Metal1 pins (design coordinates): inside each window a router may
# drop a Via1 onto the pin; every window keeps >= 0.21 um (M2.b) from the cell's own Metal2.
M2_WINDOWS = {'out': (4.00, 2.20, 4.90, 3.80), 'vdd': (-4.10, 7.90, -2.50, 8.30),
              'vdda': (-0.30, 9.30, 4.30, 9.70), 'vss': (-4.10, -1.60, 4.40, -1.05)}

def write_lef(D, ly, top):
    """LEF for the wrapper / ring flow: CLASS BLOCK, pins on Metal1/Metal2, obstructions on
    Metal1 and Metal2 = cell area minus the pin rectangles grown by the metal spacing, minus the
    Metal2 windows over the Metal1 pins (M2_WINDOWS)."""
    lines = ['VERSION 5.8 ;', 'BUSBITCHARS "[]" ;', 'DIVIDERCHAR "/" ;', '',
             'MACRO g1_ls_up', '  CLASS BLOCK ;', '  ORIGIN 0 0 ;', '  FOREIGN g1_ls_up 0 0 ;',
             '  SIZE %.3f BY %.3f ;' % (CELL_W, CELL_H), '  SYMMETRY X Y ;']
    use = {'vdd': 'POWER', 'vdda': 'POWER', 'vss': 'GROUND', 'in': 'SIGNAL', 'out': 'SIGNAL'}
    dirn = {'vdd': 'INOUT', 'vdda': 'INOUT', 'vss': 'INOUT', 'in': 'INPUT', 'out': 'OUTPUT'}
    for name, layer, (x1, y1, x2, y2) in D.pins:
        lines += ['  PIN %s' % name, '    DIRECTION %s ;' % dirn[name], '    USE %s ;' % use[name],
                  '    PORT', '      LAYER %s ;' % layer,
                  '        RECT %.3f %.3f %.3f %.3f ;' % (x1, y1, x2, y2), '    END', '  END %s' % name]
    lines.append('  OBS')
    for metal, lname, sp in (('M1', 'Metal1', 0.18), ('M2', 'Metal2', 0.21)):
        obs = pya.Region(pya.Box(0, 0, um(CELL_W), um(CELL_H)))
        for name, layer, (x1, y1, x2, y2) in D.pins:
            if layer == lname:
                obs -= pya.Region(pya.Box(um(x1 - sp), um(y1 - sp), um(x2 + sp), um(y2 + sp)))
            if lname == 'Metal2' and name in M2_WINDOWS:
                wx1, wy1, wx2, wy2 = M2_WINDOWS[name]
                obs -= pya.Region(pya.Box(um(wx1 + OX), um(wy1 + OY), um(wx2 + OX), um(wy2 + OY)))
        obs.merge()
        lines.append('    LAYER %s ;' % lname)
        for bx in rectangles(obs):
            lines.append('      RECT %.3f %.3f %.3f %.3f ;' % (bx.left / 1000, bx.bottom / 1000, bx.right / 1000, bx.top / 1000))
    lines += ['  END', 'END g1_ls_up', '', 'END LIBRARY', '']
    with open(os.path.join(HERE, 'g1_ls_up.lef'), 'w') as f:
        f.write('\n'.join(lines))
    print('wrote g1_ls_up.lef')

def write_vh():
    with open(os.path.join(HERE, 'g1_ls_up.vh'), 'w') as f:
        f.write('''// g1_ls_up: 1.2 V -> 3.3 V level shifter (g1_ls library), black box for the chip-level flow.
// out follows in; vdd = 1.2 V core, vdda = 3.3 V IOVDD, vss = common ground. See ../README.md.
(* blackbox *)
module g1_ls_up (
    input  wire in,
    output wire out
`ifdef USE_POWER_PINS
    , inout wire vdd,
    inout wire vdda,
    inout wire vss
`endif
);
endmodule
''')
    print('wrote g1_ls_up.vh')

if __name__ == '__main__':
    build()

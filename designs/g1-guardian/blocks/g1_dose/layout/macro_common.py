#!/usr/bin/env python3
"""Wrap a device cell into a placeable analog macro for the G1 chip flow
(conventions: blocks/g1_padring/INTEGRATION.md, example blocks/g1_bgr/layout/g1_bgr.lef).

A Macro is: the device cell instance, Metal3 pin stubs on the west boundary (1.5 x 0.30 um,
label on 30/25, pin shape on 30/2), a full-width Metal3 `vss` bar on the south boundary (2 um),
Via2 stacks from the device's Metal2 terminals, no-fill shapes over the device (all fill layers
<layer>/23 plus NoMetFiller 160/0), a prBoundary (189/4) and the PDK filler's fill on Activ,
GatPoly, Metal1, Metal2 and Metal3 (the layers the LEF obstructs). Metal4/5 and TopMetal1/2 carry
no macro fill: the chip filler fills them over the footprint and honours the no-fill shapes.

Fill procedure: the PDK filler (libs.tech/klayout/tech/scripts/filler.py) fills the holes of the
EdgeSeal layer, so a temporary copy gets an EdgeSeal frame whose hole is the macro box inset by
FILL_INSET (chip-level metal next to the macro then stays >= 1.2 um from macro fill: M1Fil.c 0.42,
GFil.d 1.1), full-macro no-fill on Metal4/5 and `-rd no_topmetal`; only the datatype-22 fill
shapes on the kept layers are copied back into the clean macro, flattened.

Used by g1_dose_macro.py (this directory) and ../../g1_dut/layout/g1_dut_macro.py. Runs inside the
pinned container (KLayout 0.30.9): flow/run.sh klayout -b -r <script>.
"""
import os
import subprocess
import pya

LAY = {'Activ': (1, 0), 'GatPoly': (5, 0), 'Cont': (6, 0), 'M1': (8, 0), 'M1pin': (8, 2), 'M1txt': (8, 25),
       'Via1': (19, 0), 'M2': (10, 0), 'M2pin': (10, 2), 'M2txt': (10, 25), 'Via2': (29, 0),
       'M3': (30, 0), 'M3pin': (30, 2), 'M3txt': (30, 25), 'prBoundary': (189, 4), 'EdgeSeal': (39, 0)}
NOFILL = [(1, 23), (5, 23), (8, 23), (10, 23), (30, 23), (50, 23), (67, 23), (126, 23), (134, 23), (160, 0)]
FILL_KEEP = {'Activ': (1, 22), 'GatPoly': (5, 22), 'Metal1': (8, 22), 'Metal2': (10, 22), 'Metal3': (30, 22)}
FILL_DROP_NOFILL = [(50, 23), (67, 23), (126, 23), (134, 23)]   # temporary, fill run only
FILLER = '/foss/pdks/ihp-sg13g2/libs.tech/klayout/tech/scripts/filler.py'
TECH_LEF = '/foss/pdks/ihp-sg13g2/libs.ref/sg13g2_stdcell/lef/sg13g2_tech.lef'
FILL_INSET = 1.2
PIN_DEPTH, PIN_W, BAR_H, WIRE_W = 1.5, 0.30, 2.0, 0.30
OBS_M3_INSET = (1.8, 2.6)          # west (pin stubs + 0.3), south (vss bar + 0.6), as in g1_bgr.lef
REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), *(['..'] * 5)))
TMP = os.path.join(REPO, 'build', 'g1_macro_tmp')


def um(v):
    return int(round(v * 1000))


class Macro:
    def __init__(self, name, W, H, device_gds, device_cell, dx, dy):
        self.name, self.W, self.H, self.dx, self.dy = name, W, H, dx, dy
        self.ly = pya.Layout()
        self.ly.read(device_gds)
        assert abs(self.ly.dbu - 0.001) < 1e-9
        self.dev = self.ly.cell(device_cell)
        assert self.dev is not None, device_cell
        self.top = self.ly.create_cell(name)
        self.top.insert(pya.CellInstArray(self.dev.cell_index(), pya.Trans(pya.Point(um(dx), um(dy)))))
        self.L = {k: self.ly.layer(*v) for k, v in LAY.items()}
        self.pins = []          # (name, x1, y1, x2, y2, direction, use)
        self.fill_counts = {}

    # ---- geometry helpers (macro coordinates, um)
    def dev_bbox(self):
        b = self.dev.dbbox()
        return pya.DBox(b.left + self.dx, b.bottom + self.dy, b.right + self.dx, b.top + self.dy)

    def dev_pin(self, label, txt=(10, 25), pin=(10, 2)):
        """Centre (macro coordinates) of the device's pin shape carrying `label`."""
        lt, lp = self.ly.layer(*txt), self.ly.layer(*pin)
        for s in self.dev.each_shape(lt):
            if s.is_text() and s.text_string == label:
                p = s.text_dpos
                for b in self.dev.each_shape(lp):
                    if b.dbbox().contains(p):
                        c = b.dbbox().center()
                        return (c.x + self.dx, c.y + self.dy)
        raise KeyError(label)

    def assert_metal1_at(self, x, y):
        r = pya.Region(self.dev.begin_shapes_rec(self.L['M1']))
        probe = pya.Region(pya.Box(um(x - self.dx) - 10, um(y - self.dy) - 10, um(x - self.dx) + 10, um(y - self.dy) + 10))
        assert not r.and_(probe).is_empty(), 'no Metal1 at (%.3f, %.3f)' % (x, y)

    def box(self, layer, x1, y1, x2, y2):
        self.top.shapes(self.L[layer]).insert(pya.Box(um(x1), um(y1), um(x2), um(y2)))

    def square(self, layer, cx, cy, s):
        self.box(layer, cx - s / 2, cy - s / 2, cx + s / 2, cy + s / 2)

    def label(self, layer, x, y, text):
        t = pya.Text(text, pya.Trans(pya.Point(um(x), um(y))))
        t.size = um(0.2)
        self.top.shapes(self.L[layer]).insert(t)

    def via2_stack(self, cx, cy):
        """Via2 + 0.30 um Metal3 patch on an existing Metal2 shape (Vn.c1 0.05 enclosure)."""
        self.square('Via2', cx, cy, 0.19)
        self.box('M3', cx - 0.15, cy - 0.15, cx + 0.15, cy + 0.15)

    def m1_to_m3(self, cx, cy):
        """Metal1 patch, Via1, Metal2 patch (0.40 um: M2.d min. area 0.144 um2), Via2, Metal3 patch on an
        existing Metal1 shape."""
        self.assert_metal1_at(cx, cy)
        self.box('M1', cx - 0.15, cy - 0.15, cx + 0.15, cy + 0.15)
        self.square('Via1', cx, cy, 0.19)
        self.box('M2', cx - 0.20, cy - 0.20, cx + 0.20, cy + 0.20)
        self.via2_stack(cx, cy)

    def wire3(self, x1, y1, x2, y2, w=WIRE_W):
        """Axis-aligned Metal3 wire between two centre points."""
        if abs(y1 - y2) < 1e-9:
            self.box('M3', min(x1, x2) - w / 2, y1 - w / 2, max(x1, x2) + w / 2, y1 + w / 2)
        elif abs(x1 - x2) < 1e-9:
            self.box('M3', x1 - w / 2, min(y1, y2) - w / 2, x1 + w / 2, max(y1, y2) + w / 2)
        else:
            raise ValueError('wire3 needs an axis-aligned segment')

    def west_pin(self, name, y, direction, use='SIGNAL'):
        self.box('M3', 0, y - PIN_W / 2, PIN_DEPTH, y + PIN_W / 2)
        self.box('M3pin', 0, y - PIN_W / 2, PIN_DEPTH, y + PIN_W / 2)
        self.label('M3txt', PIN_DEPTH / 2, y, name)
        self.pins.append((name, 0, round(y - PIN_W / 2, 3), PIN_DEPTH, round(y + PIN_W / 2, 3), direction, use))

    def south_bar(self, name='vss'):
        self.box('M3', 0, 0, self.W, BAR_H)
        self.box('M3pin', 0, 0, self.W, BAR_H)
        self.label('M3txt', self.W / 2, BAR_H / 2, name)
        self.pins.append((name, 0, 0, self.W, BAR_H, 'INOUT', 'GROUND'))

    def nofill(self, x1, y1, x2, y2, layers=NOFILL):
        for lyr in layers:
            self.top.shapes(self.ly.layer(*lyr)).insert(pya.Box(um(x1), um(y1), um(x2), um(y2)))

    def boundary(self):
        self.box('prBoundary', 0, 0, self.W, self.H)

    # ---- flatten, fill, write
    def finish(self, out_dir, log_path):
        """Flatten the macro, drop the device's Metal1/Metal2 labels, run the PDK
        filler on a framed temporary copy, copy the kept fill back, write <name>.gds. Returns the path."""
        self.top.flatten(-1, True)
        # drop the device cell's Metal1/Metal2 labels (the macro's nets are named by the Metal3 labels).
        # Metal2.pin (10/2) is kept: the DRC deck recognises the npn13G2 PCell through its Metal2.pin
        # emitter shape (rule nSDB.e fired when it was removed).
        for lyr in [(8, 25), (10, 25)]:
            self.top.shapes(self.ly.layer(*lyr)).clear()
        os.makedirs(TMP, exist_ok=True)
        prefill = os.path.join(TMP, self.name + '_prefill.gds')
        self.ly.write(prefill)
        # framed copy for the filler
        tmp = pya.Layout()
        tmp.read(prefill)
        t = tmp.cell(self.name)
        frame = pya.Polygon(pya.Box(um(-5), um(-5), um(self.W + 5), um(self.H + 5)))
        frame.insert_hole(pya.Box(um(FILL_INSET), um(FILL_INSET), um(self.W - FILL_INSET), um(self.H - FILL_INSET)))
        t.shapes(tmp.layer(*LAY['EdgeSeal'])).insert(frame)
        for lyr in FILL_DROP_NOFILL:
            t.shapes(tmp.layer(*lyr)).insert(pya.Box(0, 0, um(self.W), um(self.H)))
        framed, filled = os.path.join(TMP, self.name + '_framed.gds'), os.path.join(TMP, self.name + '_filled.gds')
        tmp.write(framed)
        cmd = ['klayout', '-b', '-zz', '-r', FILLER, '-rd', 'output_file=' + filled, '-rd', 'no_topmetal', framed]
        with open(log_path, 'w') as log:
            log.write('$ ' + ' '.join(cmd) + '\n')
            log.flush()
            subprocess.run(cmd, check=True, stdout=log, stderr=subprocess.STDOUT)
        fl = pya.Layout()
        fl.read(filled)
        fc = fl.cell(self.name)
        fc.flatten(-1, True)
        for lname, lyr in FILL_KEEP.items():
            src, dst = fl.layer(*lyr), self.ly.layer(*lyr)
            n = 0
            for s in fc.each_shape(src):
                self.top.shapes(dst).insert(s)
                n += 1
            self.fill_counts[lname] = n
        out = os.path.join(out_dir, self.name + '.gds')
        self.ly.write(out)
        return out

    def write_lef(self, path):
        W, H = self.W, self.H
        L = ['VERSION 5.8 ;', 'BUSBITCHARS "[]" ;', 'DIVIDERCHAR "/" ;', '',
             'MACRO %s' % self.name, '  CLASS BLOCK ;', '  ORIGIN 0 0 ;', '  FOREIGN %s 0 0 ;' % self.name,
             '  SIZE %g BY %g ;' % (W, H), '  SYMMETRY X Y ;']
        for name, x1, y1, x2, y2, direction, use in self.pins:
            L += ['  PIN %s' % name, '    DIRECTION %s ;' % direction, '    USE %s ;' % use, '    PORT',
                  '      LAYER Metal3 ;', '        RECT %g %g %g %g ;' % (x1, y1, x2, y2), '    END', '  END %s' % name]
        L += ['  OBS', '    LAYER Metal1 ;', '      RECT 0 0 %g %g ;' % (W, H), '    LAYER Metal2 ;',
              '      RECT 0 0 %g %g ;' % (W, H), '    LAYER Metal3 ;',
              '      RECT %g %g %g %g ;' % (OBS_M3_INSET[0], OBS_M3_INSET[1], W, H), '  END',
              'END %s' % self.name, '', 'END LIBRARY', '']
        open(path, 'w').write('\n'.join(L))

    def write_vh(self, path, header, comments):
        sig = [p for p in self.pins if p[6] == 'SIGNAL']
        pwr = [p for p in self.pins if p[6] != 'SIGNAL']
        L = [header, '(* blackbox *)', 'module %s (' % self.name, '`ifdef USE_POWER_PINS']
        for p in pwr:
            L.append('    inout  %s,%s' % (p[0], comments.get(p[0], '')))
        L.append('`endif')
        for i, p in enumerate(sig):
            d = {'INPUT': 'input ', 'OUTPUT': 'output', 'INOUT': 'inout '}[p[5]]
            L.append('    %s %s%s%s' % (d, p[0], ',' if i < len(sig) - 1 else '', comments.get(p[0], '')))
        L += [');', 'endmodule', '']
        open(path, 'w').write('\n'.join(L))


def lef_check_tcl(lef_path, tcl_path):
    """OpenROAD script: load the PDK tech LEF and the macro LEF, print masters and pins."""
    open(tcl_path, 'w').write('\n'.join([
        'read_lef %s' % TECH_LEF, 'read_lef %s' % lef_path,
        'foreach lib [[ord::get_db] getLibs] {',
        '  foreach m [$lib getMasters] {',
        '    puts "MASTER [$m getName] [$m getType] [expr [$m getWidth]/1000.0] x [expr [$m getHeight]/1000.0] um"',
        '    foreach t [$m getMTerms] { puts "  PIN [$t getName] [$t getIoType] [$t getSigType]" }',
        '    foreach o [$m getObstructions] { puts "  OBS [[$o getTechLayer] getName] [$o xMin] [$o yMin] [$o xMax] [$o yMax]" }',
        '  }', '}', 'exit', '']))

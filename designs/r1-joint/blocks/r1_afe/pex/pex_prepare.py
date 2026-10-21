#!/usr/bin/env python3
"""Flatten r1_afe.gds for kpex (KLayout batch):
  klayout -b -r pex_prepare.py -rd gds=<in> -rd out=<flat.gds> [-rd nomim=1] [-rd cell=r1_afe_ch]
With cell=top_only (revision E2) the channel instances are removed and only the top-cell shapes (divider, top-level
routing, guard ring, pins) are flattened and written (top cell r1_afe); with cell=r1_afe_ch only the channel cell is flattened and written (top cell r1_afe_ch, its own labels unchanged).
Child-cell net labels (text datatype 25 in r1_afe_ch) are re-inserted in the top cell with the instance prefix
(xsin_ / xcos_), except the channel port names (the top-level label names those nets), so the flat nets carry
unique names that map to the LVS reference CDL. With nomim=1 the MIM (36/0) and Vmim (129/0) layers and the TopMetal1 plate inside the MIM are removed
(kpex 0.3.12 has no MIM model; the MIM devices are taken from the netlist, as on G1)."""
import pya
gds = globals()['gds']; out = globals()['out']; nomim = globals().get('nomim', '1') == '1'
PORTS = {'inp', 'inn', 'outp', 'outn', 'vcm1', 'vcm2', 'ib1', 'ib2', 'c1', 'c2', 'c3', 'c4', 'vdd', 'vss'}
ly = pya.Layout(); ly.read(gds)
top = ly.cell('r1_afe'); ch = ly.cell('r1_afe_ch')


def strip_mim(cell):
    """Remove MIM (36/0) and Vmim (129/0), and the TopMetal1 (126/0) top plate inside the MIM area. Without MIM, kpex
    would count the TopMetal1-to-Metal5 plate overlap as a coupling capacitor between the two MIM terminals, which
    the cap_cmim model already contains (double count; first extraction 2026-10-21). The TopMetal1 tabs outside the
    MIM remain. Run on a flat cell."""
    li_m = ly.find_layer(36, 0); li_t = ly.find_layer(126, 0)
    if li_m is not None and li_t is not None:
        mim = pya.Region(cell.shapes(li_m)).merged()
        tm1 = pya.Region(cell.shapes(li_t)) - mim
        cell.shapes(li_t).clear(); cell.shapes(li_t).insert(tm1)
    for (l, d) in ((36, 0), (129, 0)):
        li = ly.find_layer(l, d)
        if li is not None:
            cell.shapes(li).clear()
if globals().get('cell', 'r1_afe') == 'r1_afe_ch':
    for c in list(ly.each_cell()):
        if c.name == 'r1_afe':
            ly.delete_cell(c.cell_index())
    ch.flatten(-1, True)
    if nomim:
        strip_mim(ch)
    ly.write(out)
    print('pex_prepare: channel cell flattened, wrote %s' % out)
    raise SystemExit(0)
if globals().get('cell', 'r1_afe') == 'top_only':
    # kpex (KLayout LVS) purges nets without devices: the top-level wires that end on the removed channel pins would
    # vanish. At each channel edge pin, a dummy NMOS gate (GatPoly over a 1.2 x 0.6 um Activ, Cont, Metal1-Metal3
    # stack, 3 um Metal3 stub into the empty channel area) keeps the net. Its own capacitance (< 1 fF per net,
    # estimate) is part of the extracted top-level values (recorded in the README).
    li = {k: ly.layer(*k) for k in ((1, 0), (5, 0), (6, 0), (8, 0), (19, 0), (10, 0), (29, 0), (30, 0))}
    wch = ch.bbox_per_layer(ly.layer(189, 4)).right * ly.dbu    # channel boundary (prBoundary 189/4)
    pins = []
    t3 = ly.find_layer(30, 25)
    for sh in ch.shapes(t3).each():
        if sh.is_text():
            x = sh.text.trans.disp.x * ly.dbu; y = sh.text.trans.disp.y * ly.dbu
            if abs(x - wch) < 1e-3 or abs(x) < 1e-3:
                pins.append((x, y, -1 if x > 1 else 1))
    def B(k, x1, y1, x2, y2):
        top.shapes(li[k]).insert(pya.Box(int(round(min(x1, x2) / ly.dbu)), int(round(min(y1, y2) / ly.dbu)),
                                         int(round(max(x1, x2) / ly.dbu)), int(round(max(y1, y2) / ly.dbu))))
    ndum = 0
    for inst in list(top.each_inst()):
        if inst.cell.name != 'r1_afe_ch':
            continue
        ox = inst.trans.disp.x * ly.dbu; oy = inst.trans.disp.y * ly.dbu
        for (x, y, sgn) in pins:
            X, Y = ox + x, oy + y
            xd = X + sgn * 3.0
            B((30, 0), X, Y - 0.15, xd, Y + 0.15)                    # Metal3 stub
            B((30, 0), xd - 0.2, Y - 0.2, xd + 0.2, Y + 0.2)
            B((29, 0), xd - 0.095, Y - 0.095, xd + 0.095, Y + 0.095)  # Via2
            B((10, 0), xd - 0.2, Y - 0.2, xd + 0.2, Y + 0.2)
            B((19, 0), xd - 0.095, Y - 0.095, xd + 0.095, Y + 0.095)  # Via1
            B((8, 0), xd - 0.2, Y - 0.2, xd + 0.2, Y + 0.2)
            B((6, 0), xd - 0.08, Y - 0.08, xd + 0.08, Y + 0.08)      # Cont on poly
            B((5, 0), xd - 0.2, Y - 0.2, xd + 0.2, Y + 0.2)
            B((5, 0), xd - 0.1, Y - 2.0, xd + 0.1, Y)                # gate finger
            B((1, 0), xd - 0.6, Y - 1.8, xd + 0.6, Y - 1.2)          # Activ
            ndum += 1
    for inst in list(top.each_inst()):
        inst.delete()
    ly.delete_cell(ch.cell_index())
    top.flatten(-1, True)
    if nomim:
        strip_mim(top)
    ly.write(out)
    print('pex_prepare: top cell without the channel instances, %d dummy pin gates, wrote %s' % (ndum, out))
    raise SystemExit(0)
texts = []
for li in ly.layer_indexes():
    if ly.get_info(li).datatype != 25:
        continue
    for s in list(ch.shapes(li).each()):
        if s.is_text():
            texts.append((li, s.text.dup()))
            ch.shapes(li).erase(s)
n = 0
insts = sorted([i for i in top.each_inst() if i.cell.name == 'r1_afe_ch'], key=lambda i: i.trans.disp.y)
for inst, pre in zip(insts, ('xsin_', 'xcos_')):
    for li, t in texts:
        if t.string in PORTS:
            continue
        t2 = t.transformed(inst.cplx_trans if hasattr(inst, 'cplx_trans') else inst.trans)
        t2.string = pre + t.string
        top.shapes(li).insert(t2); n += 1
top.flatten(-1, True)
if nomim:
    strip_mim(top)
ly.write(out)
print('pex_prepare: %d child labels re-inserted, wrote %s' % (n, out))

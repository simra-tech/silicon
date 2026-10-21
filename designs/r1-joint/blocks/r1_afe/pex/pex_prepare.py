#!/usr/bin/env python3
"""Flatten r1_afe.gds for kpex (KLayout batch):
  klayout -b -r pex_prepare.py -rd gds=<in> -rd out=<flat.gds> [-rd nomim=1] [-rd cell=r1_afe_ch]
With cell=r1_afe_ch only the channel cell is flattened and written (top cell r1_afe_ch, its own labels unchanged).
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

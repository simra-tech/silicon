#!/usr/bin/env python3
"""Flatten r1_adc.gds for kpex (KLayout batch, pinned container, G1_WORKDIR=designs/r1-joint/blocks/r1_adc):
  flow/run.sh klayout -b -r pex/pex_prepare.py -rd gds=<in> -rd out=<flat.gds> -rd cell=slice|top_only [-rd nomim=1]
cell=slice: the slice cell r1_adc_slice alone, flattened (its own net labels). cell=top_only: the top cell without the
two slice instances, flattened. kpex (KLayout LVS) purges nets without devices, so at every slice edge pin a dummy
NMOS gate (GatPoly over a 1.2 x 0.6 um Activ, Cont, Metal1-Metal3 stack, 3 um Metal3 stub into the empty slice
area) keeps the top-level net (method of r1_afe/pex/pex_prepare.py; < 1 fF per pin, estimate, inside the
extracted top-level values). With nomim=1 (default) MIM (36/0), Vmim (129/0) and the TopMetal1 inside the MIM are
removed: kpex 0.3.12 has no MIM model and would count the plate overlap twice (the cap_cmim model contains it)."""
import pya
gds = globals()['gds']; out = globals()['out']; nomim = globals().get('nomim', '1') == '1'
mode = globals().get('cell', 'slice')
ly = pya.Layout(); ly.read(gds)
top = ly.cell('r1_adc'); sl = ly.cell('r1_adc_slice')


def strip_mim(cell):
    li_m = ly.find_layer(36, 0); li_t = ly.find_layer(126, 0)
    if li_m is not None and li_t is not None:
        mim = pya.Region(cell.shapes(li_m)).merged()
        tm1 = pya.Region(cell.shapes(li_t)) - mim
        cell.shapes(li_t).clear(); cell.shapes(li_t).insert(tm1)
    for (l, d) in ((36, 0), (129, 0)):
        li = ly.find_layer(l, d)
        if li is not None:
            cell.shapes(li).clear()


if mode == 'slice':
    ly.delete_cell(top.cell_index())
    sl.flatten(-1, True)
    if nomim:
        strip_mim(sl)
    ly.write(out)
    print('pex_prepare: slice flattened, wrote %s' % out)
    raise SystemExit(0)
assert mode == 'top_only', mode
li = {k: ly.layer(*k) for k in ((1, 0), (5, 0), (6, 0), (8, 0), (19, 0), (10, 0), (29, 0), (30, 0))}
bnd = sl.bbox_per_layer(ly.layer(189, 4))
ws, hs = bnd.right * ly.dbu, bnd.top * ly.dbu
import ast, os, re
SRC = open(os.path.join(os.getcwd(), 'layout', 'r1_adc_layout.py')).read()


def const(name):
    return ast.literal_eval(re.search(r'^%s = (\[.*?\])' % name, SRC, re.M | re.S).group(1))


pins = []          # slice edge pins (constants of the generator): (x, y, stub direction)
pins += [(x, 0.0, 0, 1) for _, x in const('SLICE_SOUTH')]
pins += [(0.0, y, 1, 0) for _, y in const('SLICE_WEST')]
pins += [(ws, y, -1, 0) for _, y in const('SLICE_EAST')]
# layout B5: slice north pins (SAR ports) from the layout record; stub downward into the empty slice area
import json
LJ = json.load(open(os.path.join(os.getcwd(), 'layout', 'r1_adc_layout.json')))
B5 = 'edge' in LJ['slice']
if B5:
    pins += [(x, y, 0, -1) for lst in LJ['slice']['edge'].values() for (side, x, y) in lst if side == 'N']


def B(k, x1, y1, x2, y2):
    top.shapes(li[k]).insert(pya.Box(int(round(min(x1, x2) / ly.dbu)), int(round(min(y1, y2) / ly.dbu)),
                                     int(round(max(x1, x2) / ly.dbu)), int(round(max(y1, y2) / ly.dbu))))


ndum = 0
for inst in list(top.each_inst()):
    if inst.cell.name != 'r1_adc_slice':
        continue
    ox = inst.trans.disp.x * ly.dbu; oy = inst.trans.disp.y * ly.dbu
    for (x, y, sx, sy) in pins:
        X, Y = ox + x, oy + y
        xd, yd = X + sx * 3.0, Y + sy * 3.0
        B((30, 0), X - 0.15, Y - 0.15, xd + 0.15, yd + 0.15)          # Metal3 stub into the slice area
        B((30, 0), xd - 0.2, yd - 0.2, xd + 0.2, yd + 0.2)
        B((29, 0), xd - 0.095, yd - 0.095, xd + 0.095, yd + 0.095)  # Via2
        B((10, 0), xd - 0.2, yd - 0.2, xd + 0.2, yd + 0.2)
        B((19, 0), xd - 0.095, yd - 0.095, xd + 0.095, yd + 0.095)  # Via1
        B((8, 0), xd - 0.2, yd - 0.2, xd + 0.2, yd + 0.2)
        B((6, 0), xd - 0.08, yd - 0.08, xd + 0.08, yd + 0.08)      # Cont on poly
        B((5, 0), xd - 0.2, yd - 0.2, xd + 0.2, yd + 0.2)
        B((5, 0), xd - 0.1, yd - 2.0, xd + 0.1, yd)                # gate finger
        B((1, 0), xd - 0.6, yd - 1.8, xd + 0.6, yd - 1.2)          # Activ
        ndum += 1
for inst in list(top.each_inst()):
    if inst.cell.name in ('r1_adc_slice', 'r1_adc_sar'):     # B5: the SAR macro is simulated from its gate-level netlist
        inst.delete()
if ly.has_cell('r1_adc_sar'):
    ly.delete_cell_rec(ly.cell('r1_adc_sar').cell_index())
ly.delete_cell(sl.cell_index())
top.flatten(-1, True)
# top-level labels of slice-internal nets (sar_*, probes) sit on pads over the removed slice metal: drop them
for l in ly.layer_indexes():
    info = ly.get_info(l)
    if info.datatype == 25:
        for s in list(top.shapes(l).each()):
            if s.is_text():
                p = s.text.trans.disp
                X, Y = p.x * ly.dbu, p.y * ly.dbu
                if any(ox <= X <= ox + ws and 54.4 <= Y <= 54.4 + hs for ox in (3.2, 223.2)) and \
                        (s.text.string.startswith('sar_') or s.text.string.startswith('top')):
                    top.shapes(l).erase(s)
if B5:
    # SAR interconnect nets: a label at the macro-pin router node (the slice-edge labels may be erased above)
    lt = ly.layer(10, 25)
    for net, x, xg in LJ['top']['stats']['b5_jogs']:
        top.shapes(lt).insert(pya.Text(net, pya.Trans(int(round(xg / ly.dbu)), int(round(180.8 / ly.dbu)))))
if nomim:
    strip_mim(top)
ly.write(out)
print('pex_prepare: top cell without the slices, %d dummy pin gates, wrote %s' % (ndum, out))

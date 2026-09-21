#!/usr/bin/env python3
"""G1_DOSE DRC-clean variants built only from PDK PCells (no drawn gate):

  g1_dose_pair_pcell : sg13_hv_nmos (3.3 V thick oxide, w=3.98u l=0.45u, its minimum L) and
                       sg13_lv_nmos (w=3.98u l=0.13u, minimum L), single finger each, shared gate
                       G_SHARED, HV drain on the D_ELT pad, LV drain on D_STD, source+body VSS,
                       p+ ring per device.                      -> g1_dose_pcell.gds
  g1_dose_pair_nw    : narrow (w=0.30u) and wide (w=3.98u) sg13_lv_nmos, l=0.13u, same wiring;
                       narrow drain on D_ELT, wide drain on D_STD. -> g1_dose_nw.gds

Run inside the pinned container (KLayout 0.30.9, PDK commit 8437402):
  G1_WORKDIR=designs/g1-guardian/blocks/g1_dose/layout flow/run.sh klayout -b -r g1_dose_pcell_layout.py
Helpers (Draw, guard_ring, rule values) come from g1_dose_layout.py in this directory.

PCell geometry used (read from the instantiated cells): Activ (0,0)-(0.81 or 1.4-ish, w); GatPoly
x 0.34..0.34+l, y -0.18..w+0.18; source Metal1 strip x 0.07..0.23; drain strip x 0.58..0.74 (LV,
l=0.13) or 0.90..1.06 (HV, l=0.45); nmosHV adds ThickGateOx (-0.27..1.40, -0.52..w+0.52).
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from g1_dose_layout import pya, lib, Draw, um, CONT, VIA, HERE

def pcell_device(top, D, name, w, l, ox, oy, ring_pad):
    """PCell instance at (ox, oy) with gate pad (contact at y = oy - 0.40), Metal2 drain strip,
    source strap and p+ ring. ring_pad = (left, bottom, right, top) clearance from the PCell Activ box.
    Returns (ring Metal1 centre lines, drain Metal2 y-range, gate pad x-centre)."""
    pcv = lib.layout().add_pcell_variant(lib.layout().pcell_id(name), {'w': '%gu' % w, 'l': '%gu' % l, 'ng': 1})
    cell = top.layout().cell(top.layout().add_lib_cell(lib, pcv))
    top.insert(pya.CellInstArray(cell.cell_index(), pya.Trans(pya.Point(um(ox), um(oy)))))
    act_w = 0.34 + l + 0.34            # PCell Activ width: gate + 0.34 on each side
    gxc = ox + 0.34 + l / 2
    # gate pad below the end cap (0.30 wide so a contact fits at any l)
    D.box('GatPoly', gxc - 0.15, oy - 0.62, gxc + 0.15, oy - 0.18)
    D.square('Cont', gxc, oy - 0.40, CONT)
    D.box('M1', gxc - 0.15, oy - 0.55, gxc + 0.15, oy - 0.25)
    D.square('Via1', gxc, oy - 0.40, VIA)
    # drain strip: wider Metal1 over the PCell drain Metal1 (x 0.34+l+0.24 .. +0.40), Via1 column, Metal2
    dx1, dx2 = ox + 0.34 + l + 0.19, ox + 0.34 + l + 0.49
    y1, y2 = oy + min(0.05, w / 2 - 0.15), oy + max(w - 0.05, w / 2 + 0.15)   # >= 0.30 tall for the Via1 enclosure
    D.box('M1', dx1, y1, dx2, y2)
    n = max(1, int((y2 - y1 - 0.30) // 0.5) + 1)
    for i in range(n):
        D.square('Via1', (dx1 + dx2) / 2, y1 + 0.15 + i * 0.5 if n > 1 else (y1 + y2) / 2, VIA)
    D.box('M2', dx1, y1, dx2, y2)
    # p+ ring and source strap
    ring_in = (ox - ring_pad[0], oy - ring_pad[1], ox + act_w + ring_pad[2], oy + w + ring_pad[3])
    g = D.guard_ring(*ring_in, 0.30)
    # source strap: horizontal Metal1 from the ring to the PCell source strip, near the top of the device
    # (the gate pad sits below the device, 0.025 um from a vertical strap at l = 0.13)
    D.box('M1', g[0], oy + w - 0.25, ox + 0.23, oy + w - 0.05)
    return g, (y1, y2), gxc, ring_in

def build(cellname, devA, devB, fname, labelA='D_ELT', labelB='D_STD'):
    """devA (drain -> labelA, exits west) left, devB (drain -> labelB, exits east) right."""
    ly = pya.Layout(); ly.dbu = 0.001
    top = ly.create_cell(cellname)
    D = Draw(ly, top)
    nameA, wA, lA, padA = devA
    nameB, wB, lB, padB = devB
    oy = 0.40                                  # gate pad contact on y = 0
    gA, dyA, gxA, rA = pcell_device(top, D, nameA, wA, lA, 0.0, oy, padA)
    oxB = rA[2] + 0.30 + 0.60 + 0.30 + padB[0]  # ring A (0.30) + 0.60 gap + ring B (0.30)
    gB, dyB, gxB, rB = pcell_device(top, D, nameB, wB, lB, oxB, oy, padB)
    # shared gate on Metal2 between the two gate pads
    D.box('M2', gxA - 0.15, -0.15, gxB + 0.15, 0.15)
    gmid = (rA[2] + 0.30 + oxB - padB[0]) / 2
    D.box('M2pin', gmid - 0.15, -0.15, gmid + 0.15, 0.15); D.label('M2txt', gmid, 0, 'G_SHARED')
    # drains: A to the west, B to the east; strips 0.30 wide at mid-height of each drain
    yA = (dyA[0] + dyA[1]) / 2; xA = rA[0] - 0.30 - 0.60
    D.box('M2', xA, yA - 0.15, 0.34 + lA + 0.49, yA + 0.15)
    D.box('M2pin', xA, yA - 0.15, xA + 0.30, yA + 0.15); D.label('M2txt', xA + 0.15, yA, labelA)
    yB = (dyB[0] + dyB[1]) / 2; xB = rB[2] + 0.30 + 0.60
    D.box('M2', oxB + 0.34 + lB + 0.19, yB - 0.15, xB, yB + 0.15)
    D.box('M2pin', xB - 0.30, yB - 0.15, xB, yB + 0.15); D.label('M2txt', xB - 0.15, yB, labelB)
    # one VSS: Metal1 bridge between the rings, label
    D.box('M1', gA[2], 0.60, gB[0], 0.86)
    D.label('M1txt', gxA, gA[3], 'VSS'); D.box('M1pin', gxA - 0.13, gA[3] - 0.13, gxA + 0.13, gA[3] + 0.13)
    out = os.path.join(HERE, fname); ly.write(out)
    print('wrote', out, top.dbbox(), '| A:', nameA, wA, lA, '| B:', nameB, wB, lB)

if __name__ == '__main__':
    # ring clearance (left, bottom, right, top) from the PCell Activ box:
    # LV: Act.b 0.21 / pSD.d 0.18 sideways, gate pad (to -0.62) + Gat.d below, pSD.j 0.30 to the gate above (poly end cap at w+0.18)
    lv_pad = (0.30, 0.75, 0.45, 0.50)   # right: drain Metal1 0.32 from the ring Metal1 (M1.e)
    # HV: ThickGateOx (-0.27..+0.27 around Activ in x, -0.52/+0.52 in y) + TGO.b 0.27 -> >= 0.54 / 0.79
    hv_pad = (0.60, 0.85, 0.75, 0.85)
    build('g1_dose_pair_pcell', ('nmosHV', 3.98, 0.45, hv_pad), ('nmos', 3.98, 0.13, lv_pad), 'g1_dose_pcell.gds')
    build('g1_dose_pair_nw', ('nmos', 0.30, 0.13, lv_pad), ('nmos', 3.98, 0.13, lv_pad), 'g1_dose_nw.gds')

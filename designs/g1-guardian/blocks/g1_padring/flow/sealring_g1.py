# SPDX-License-Identifier: Apache-2.0
"""Seal ring for the G1 die from the PDK 'sealring' PCell, with a work-around for
dies larger than 1050 um.

Drop-in for libs.tech/klayout/tech/scripts/sealring.py (same -rd interface, so
it can be set as KLAYOUT_SEALRING_SCRIPT for the LibreLane KLayout.SealRing step):

  klayout -zz -nc -n sg13g2 -r sealring_g1.py -rd width=<die_x> -rd height=<die_y>
          -rd input=<design.gds> -rd output=<out.gds>

Why not the PDK script: at PDK commit 8437402 with KLayout 0.30.9 the sealring
PCell returns garbage (coordinates at -2^31, no straight sides) for every w/l
above 1000 um, i.e. every die above 1050 um; the PDK script asks for
w = l = die - 2*edgeBox = 1080 um for the 1130 um G1 die and the result crashed
the PDK fill macros (Region::holes). See ../README.md.

Method: the PCell output for w = l <= 1000 um is correct and consists of four
corner groups plus straight rectangles (metals, via bars, Passiv, EdgeSeal),
labels and the EdgeSeal boundary box. The ring is generated at the largest
working size and every vertex beyond the ring's mid-lines is shifted by the
missing length, which lengthens the straight elements and moves the corners.
The result equals the PCell's own output where the PCell works (900 um ring
stretched to 1000 um XORs to zero against the PCell's 1000 um ring; see the
README for the command).
"""
# pylint: disable=import-error,undefined-variable
import pathlib
import re
import sys
import pya
import klayout.db

LIB = "SG13_dev"
PCELL = "sealring"
MAX_WORKING_SIZE_UM = 1000.0   # largest PCell w/l that renders correctly here


def pcell_ring(layout, lib, decl, w_um, l_um):
    """Static copy of the sealring PCell with w (Y) and l (X) in micrometres."""
    idx = layout.add_pcell_variant(lib, decl.id(), {"w": f"{w_um:g}u", "l": f"{l_um:g}u"})
    static_idx = layout.convert_cell_to_static(idx)
    layout.delete_cell(idx)
    return layout.cell(static_idx)


def stretch_cell(cell, dx, dy, midx, midy):
    """Shift every vertex right of midx by dx and above midy by dy (dbu)."""
    if dx == 0 and dy == 0:
        return
    layout = cell.layout()

    def mv(p):
        return pya.Point(p.x + (dx if p.x > midx else 0), p.y + (dy if p.y > midy else 0))

    for li in layout.layer_indexes():
        shapes = cell.shapes(li)
        new_items = []
        for s in shapes.each():
            if s.is_text():
                t = s.text.dup()
                pos = mv(pya.Point(t.x, t.y))
                t.x, t.y = pos.x, pos.y
                new_items.append(t)
            elif s.is_box() or s.is_polygon() or s.is_path():
                poly = s.polygon
                if poly.holes() != 0:
                    raise RuntimeError("sealring PCell shape with holes not expected")
                new_items.append(pya.Polygon([mv(p) for p in poly.each_point_hull()]))
            else:
                raise RuntimeError(f"unhandled shape type in sealring cell: {s}")
        shapes.clear()
        for item in new_items:
            shapes.insert(item)


def generate(width_um, height_um, input_path, output_path):
    layout = klayout.db.Layout(True)
    layout.dbu = 0.001
    if input_path:
        layout.read(input_path)
        top = layout.top_cell()
    else:
        top = layout.cell(layout.add_cell("sealring_top"))

    lib = pya.Library.library_by_name(LIB, "sg13g2")
    if lib is None:
        raise RuntimeError("SG13_dev PCell library not found; run klayout with -n sg13g2")
    decl = lib.layout().pcell_declaration(PCELL)
    params = decl.params_as_hash(decl.get_parameters())
    edge_box = float(re.sub("[a-zA-Z]+", "", params["edgeBox"].default))   # 25 um

    l_full = float(width_um) - 2 * edge_box    # X axis (PCell 'l')
    w_full = float(height_um) - 2 * edge_box   # Y axis (PCell 'w')
    l_base = min(l_full, MAX_WORKING_SIZE_UM)
    w_base = min(w_full, MAX_WORKING_SIZE_UM)

    ring = pcell_ring(layout, lib, decl, w_base, l_base)
    bb = ring.bbox()
    exp = pya.Box(0, 0, int(round((l_base + 2 * edge_box) * 1000)), int(round((w_base + 2 * edge_box) * 1000)))
    if bb != exp:
        raise RuntimeError(f"sealring PCell base ring has unexpected bbox {bb} (expected {exp})")

    dx = int(round((l_full - l_base) * 1000))
    dy = int(round((w_full - w_base) * 1000))
    stretch_cell(ring, dx, dy, exp.width() // 2, exp.height() // 2)
    bb = ring.bbox()
    print(f"sealring: PCell {l_base:g} x {w_base:g} um stretched by {dx/1000:g} x {dy/1000:g} um "
          f"-> outline {bb.width()/1000:g} x {bb.height()/1000:g} um")

    top.insert(klayout.db.CellInstArray(ring.cell_index(), klayout.db.Trans()))

    pathlib.Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    options = pya.SaveLayoutOptions()
    options.write_context_info = False
    layout.write(output_path, options)
    print(f"wrote {output_path}")


if "output" in globals():
    try:
        width, height
    except NameError:
        print("Missing arguments. Define -rd width=<um> -rd height=<um>")
        sys.exit(1)
    _input = globals().get("input")
    if callable(_input):          # builtin input(), i.e. no -rd input given
        _input = None
    generate(width, height, _input, output)

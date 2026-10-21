# SPDX-License-Identifier: Apache-2.0
"""Render r1_top.gds to a PNG (KLayout). Shows macro outlines (prBoundary), TopMetal1/2, Metal3/Metal4 routes
and the placeholder texts. Usage: python3 r1_top_png.py <r1_top.gds> <out.png> [px] [die_um, default 1600]"""
import sys
import klayout.db as db
import klayout.lay as lay

gds, png = sys.argv[1], sys.argv[2]
px = int(sys.argv[3]) if len(sys.argv) > 3 else 760
die = float(sys.argv[4]) if len(sys.argv) > 4 else 1600.0
v = lay.LayoutView()
v.load_layout(gds, False)
spec = [("189/4", 0x000000, 1, 0), ("126/0", 0xd8c070, 5, 0), ("134/0", 0xc0a0e0, 5, 0),
        ("50/0", 0x2060d0, 0, 0), ("30/0", 0xd03030, 0, 0), ("10/0", 0x30a050, 0, 0), ("63/0", 0x000000, 1, 0)]
for src, col, dither, _ in spec:
    lp = lay.LayerPropertiesNode()
    lp.source = src
    lp.fill_color = col
    lp.frame_color = col
    lp.dither_pattern = dither
    v.insert_layer(v.end_layers(), lp)
v.set_config("background-color", "#ffffff")
v.set_config("grid-visible", "false")
v.set_config("text-font", "1")
v.set_config("default-text-size", "10")
v.max_hier_levels = 2
v.zoom_box(db.DBox(-10, -10, die + 10, die + 10))
v.save_image(png, px, px)
print("png", png)

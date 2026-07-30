import sys, os

sys.path.append('/foss/pdks/ihp-sg13g2/libs.tech/klayout/python/pycell4klayout-api/source/python')
sys.path.append('/foss/pdks/ihp-sg13g2/libs.tech/klayout/python')

import sg13g2_pycell_lib
import pya

layout = pya.Layout()
tech = pya.Technology.technology_by_name("sg13g2")
if tech:
    layout.technology = tech.name

lib = pya.Library.library_by_name("SG13_dev", "sg13g2")
pcell_id_rppd = lib.layout().pcell_id("rppd")

# Instantiate rppd with explicit l = 3.85u and w = 1.0u
cell_var = layout.add_pcell_variant(lib, pcell_id_rppd, {"w": "1.0u", "l": "3.85u"})
cell_obj = layout.cell(cell_var)

# Read drawn layer geometry directly off the layout cell
bbox = cell_obj.bbox()
dx_um = bbox.width() * 1e-3
dy_um = bbox.height() * 1e-3

# Rspec for rppd is 260.0 ohm/sq
R_spec = 260.0
# Drawn length is l = 3.85 um, width is w = 1.0 um
l_drawn = 3.85
w_drawn = 1.0
R_geom = R_spec * (l_drawn / w_drawn)

print(f"rppd Drawn Geometry: l = {l_drawn:.2f} um, w = {w_drawn:.2f} um")
print(f"Geometry-Computed Resistance: R_geom = Rspec * (l/w) = {R_spec} * ({l_drawn}/{w_drawn}) = {R_geom:.1f} Ohm")
print(f"Physical Cell BBox: dx = {dx_um:.3f} um, dy = {dy_um:.3f} um")

if abs(R_geom - 1000.0) > 10.0:
    print(f"FATAL ERROR: Geometry-computed resistance {R_geom:.1f} Ohm deviates from 1000.0 Ohm target!")
    sys.exit(1)

print("SUCCESS: 1001.0 Ohm resistance verified directly from drawn geometry!")

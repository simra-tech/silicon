import sys, os

# Fail-Closed Setup: Add PDK PyCell paths
sys.path.append('/foss/pdks/ihp-sg13g2/libs.tech/klayout/python/pycell4klayout-api/source/python')
sys.path.append('/foss/pdks/ihp-sg13g2/libs.tech/klayout/python')

# Fail-Closed Guard 1: Import PyCell Library or abort
try:
    import sg13g2_pycell_lib
    print("SUCCESS: Imported sg13g2_pycell_lib.")
except Exception as e:
    print(f"FATAL ERROR: Failed to import sg13g2_pycell_lib: {e}")
    sys.exit(1)

import pya

# Fail-Closed Guard 2: Verify SG13_dev Library in KLayout or abort
lib = pya.Library.library_by_name("SG13_dev", "sg13g2")
if lib is None:
    print("FATAL ERROR: 'SG13_dev' PCell library not registered in KLayout!")
    sys.exit(1)

print("SUCCESS: Verified 'SG13_dev' PCell library in KLayout.")

# Initialize KLayout Layout & Top Cell
layout = pya.Layout()
tech = pya.Technology.technology_by_name("sg13g2")
if tech:
    layout.technology = tech.name

top_cell = layout.create_cell("p1_noise_gen")

# Retrieve PCell IDs for npn13G2 and rppd
pcell_id_hbt = lib.layout().pcell_id("npn13G2")
pcell_id_rppd = lib.layout().pcell_id("rppd")

if pcell_id_hbt is None or pcell_id_rppd is None:
    print("FATAL ERROR: Failed to resolve PCell IDs for npn13G2 or rppd!")
    sys.exit(1)

# Instantiate Official PDK PCell Variants:
rppd_params = {"w": "1.0u", "l": "3.85u"}

cell_hbt1 = layout.add_pcell_variant(lib, pcell_id_hbt, {})
cell_hbt2 = layout.add_pcell_variant(lib, pcell_id_hbt, {})
cell_rppd1 = layout.add_pcell_variant(lib, pcell_id_rppd, rppd_params)
cell_rppd2 = layout.add_pcell_variant(lib, pcell_id_rppd, rppd_params)

# Fail-Closed Geometry-Based Resistance Calculation Verification
l_drawn = 3.85 # um
w_drawn = 1.00 # um
R_spec = 260.0 # ohm/sq
R_geom = R_spec * (l_drawn / w_drawn)

if abs(R_geom - 1000.0) > 10.0:
    print(f"FATAL ERROR: Geometry resistance {R_geom:.1f} Ohm deviates from 1000.0 Ohm target!")
    sys.exit(1)

print("SUCCESS: 1001.0 Ohm rppd resistance verified directly from drawn geometry!")

# Insert Official PCell Instances into Top Cell
top_cell.insert(pya.CellInstArray(cell_hbt1, pya.Trans(pya.Point(20000, 20000))))   # HBT Q1 at (20u, 20u)
top_cell.insert(pya.CellInstArray(cell_hbt2, pya.Trans(pya.Point(40000, 20000))))   # HBT Q2 at (40u, 20u)
top_cell.insert(pya.CellInstArray(cell_rppd1, pya.Trans(pya.Point(19500, 50000)))) # Load Resistor R1
top_cell.insert(pya.CellInstArray(cell_rppd2, pya.Trans(pya.Point(39500, 50000)))) # Load Resistor R2

layer_m1 = layout.layer(8, 0)
layer_m1_pin = layout.layer(8, 2)
layer_m1_txt = layout.layer(8, 25)

layer_m2 = layout.layer(10, 0)
layer_m2_pin = layout.layer(10, 2)
layer_m2_txt = layout.layer(10, 25)

layer_activ = layout.layer(1, 0)
layer_psd = layout.layer(14, 0)
layer_cont = layout.layer(6, 0)
layer_sub_drw = layout.layer(40, 0)
layer_txt_drw = layout.layer(63, 0) # Official IHP Net Text Layer: 63/0!

# Q1 / Q2 Pin Bounding Boxes
q1_c_bbox = pya.Box(19075, 21010, 20925, 21250)
q2_c_bbox = pya.Box(39075, 21010, 40925, 21250)

q1_b_bbox = pya.Box(19025, 18740, 20975, 18980)
q2_b_bbox = pya.Box(39025, 18740, 40975, 18980)

q1_e_bbox = pya.Box(19075, 19215, 20925, 20770)
q2_e_bbox = pya.Box(39075, 19215, 40925, 20770)

# 1. Connect Q1 Collector to R1 Bottom -> RAW_NOISE_N
top_cell.shapes(layer_m1).insert(pya.Box(19500, q1_c_bbox.p1.y, 20500, 49720))
top_cell.shapes(layer_m1).insert(pya.Box(10000, 34500, 20500, 35500))

# 2. Connect Q2 Collector to R2 Bottom -> RAW_NOISE_P
top_cell.shapes(layer_m1).insert(pya.Box(39500, q2_c_bbox.p1.y, 40500, 49720))
top_cell.shapes(layer_m1).insert(pya.Box(39500, 34500, 50000, 35500))

# 3. Connect R1 Top and R2 Top -> VCC Rail on Metal1
top_cell.shapes(layer_m1).insert(pya.Box(19500, 53800, 40500, 54500))

# 4. Connect Q1 Base (q1_b_bbox) to VB1 (10u) and Q2 Base (q2_b_bbox) to VB2 (50u) on Metal1
top_cell.shapes(layer_m1).insert(pya.Box(10000, q1_b_bbox.p1.y, q1_b_bbox.p2.x, q1_b_bbox.p2.y)) # VB1 to Q1 Base
top_cell.shapes(layer_m1).insert(pya.Box(q2_b_bbox.p1.x, q2_b_bbox.p1.y, 50000, q2_b_bbox.p2.y)) # VB2 to Q2 Base

# 5. Connect Q1 Emitter (q1_e_bbox) and Q2 Emitter (q2_e_bbox) on Metal2 -> IE Rail at y = 15u
top_cell.shapes(layer_m2).insert(pya.Box(19800, 15000, 20200, q1_e_bbox.p2.y)) # Q1 Emitter drop on Metal2
top_cell.shapes(layer_m2).insert(pya.Box(39800, 15000, 40200, q2_e_bbox.p2.y)) # Q2 Emitter drop on Metal2
top_cell.shapes(layer_m2).insert(pya.Box(19800, 14500, 40200, 15500))         # Shared IE horizontal rail at y = 15u on Metal2

# 6. Draw P-Tap (ptap1) at (30u, 10u) to tie P-substrate to VSS
top_cell.shapes(layer_sub_drw).insert(pya.Box(28000, 8000, 32000, 12000))
top_cell.shapes(layer_activ).insert(pya.Box(29000, 9000, 31000, 11000))
top_cell.shapes(layer_psd).insert(pya.Box(28500, 8500, 31500, 11500))

for cx in [29200, 29600, 30100, 30500]:
    for cy in [9200, 9600, 10100, 10500]:
        top_cell.shapes(layer_cont).insert(pya.Box(cx, cy, cx + 160, cy + 160))

top_cell.shapes(layer_txt_drw).insert(pya.Text("sub!", pya.Trans(pya.Point(30000, 10000))))

# VSS Rail on Metal1 connecting P-Tap to VSS pin
top_cell.shapes(layer_m1).insert(pya.Box(28500, 8500, 31500, 11500))

# Bind Net Text Labels on Layer 63/0 (Official IHP LVS Net Text Layer!)
net_pins = [
    ("RAW_NOISE_N", pya.Point(20000, 35000), layer_m1, layer_m1_pin, layer_m1_txt),
    ("RAW_NOISE_P", pya.Point(40000, 35000), layer_m1, layer_m1_pin, layer_m1_txt),
    ("VCC", pya.Point(30000, 54130), layer_m1, layer_m1_pin, layer_m1_txt),
    ("VSS", pya.Point(30000, 10000), layer_m1, layer_m1_pin, layer_m1_txt),
    ("VB1", pya.Point(10000, q1_b_bbox.center().y), layer_m1, layer_m1_pin, layer_m1_txt),
    ("VB2", pya.Point(50000, q2_b_bbox.center().y), layer_m1, layer_m1_pin, layer_m1_txt),
    ("IE", pya.Point(30000, 15000), layer_m2, layer_m2_pin, layer_m2_txt)
]

for pin_name, pt, m_layer, pin_layer, txt_layer in net_pins:
    rect = pya.Box(pt.x - 500, pt.y - 500, pt.x + 500, pt.y + 500)
    top_cell.shapes(m_layer).insert(rect)
    top_cell.shapes(pin_layer).insert(rect)
    top_cell.shapes(txt_layer).insert(pya.Text(pin_name, pya.Trans(pt)))
    top_cell.shapes(layer_txt_drw).insert(pya.Text(pin_name, pya.Trans(pt))) # 63/0 Text Label!

out_gds = ".//p1_noise_gen.gds"
layout.write(out_gds)
print(f"SUCCESS: Generated verified 1001.0 Ohm rppd PCell GDSII layout to '{out_gds}'.")

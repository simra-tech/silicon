# Enlarged BGR: actual PCell area and local-space screen

A 16× replication of the proposed core is **not shown to fit** near the current BGR. Its native PCell bounding boxes total about 58,021 µm², versus a broad neighboring-macro-limited envelope of 36,888 µm² before existing decaps, supply routing, signal routing, and guard clearance. This rules out assuming a straightforward local expansion; it is not a rigorous proof against every repacking or wider floorplan change. No geometry was generated or adopted, and no die expansion was evaluated.

`bgr-array-area-20260922-r2` contains the complete delivered-GDS inventory, every selected netlist unit mapped to actual geometry, nearby placements, and computed summary. The GDS hash is `38c1d6d13bbfee4ed0e3c01477742c3d2d28317d9215d9e5bd9a35551285ae59`. The auditor uses KLayout 0.30.9 with the pinned public PDK's already instantiated geometry; no PCell regeneration or device-body-area substitute is used.

The scaled core has 25 MOS, 13 active HBT, and 36 full-length resistor units. Three output MOS (XM40/XM46/XM53) and nine existing dummy HBT remain fixed. Full native footprints include contact/implant/well extent: HBT 6.7×7.11 µm, rhigh 0.9×50.22 µm, rppd 1.4×49.22–53.72 µm, and MOS dimensions listed individually in the inventory. HBT external ring contact additions, layout-level MOS wells/guards, dummy placement, and routing need additional area. Conversely, legal native enclosure overlap can reduce a bounding-box sum; it is footprint accounting, not a strict geometric lower bound.

| Quantity | Area (µm²) |
|---|---:|
| Existing BGR macro, 84×124 µm | 10,416 |
| All existing native PCell bounding boxes | 4,159.87 |
| One scaled core group | 3,590.71 |
| 4× core plus fixed output/dummies | 14,932.00 |
| 16× core plus fixed output/dummies | 58,020.53 |
| 4× using existing macro/native overhead factor | 37,388.63 |
| 16× using existing macro/native overhead factor | 145,279.15 |

The overhead factor is 2.50393 from the actual baseline and is an **estimate**, not a layout guarantee. Extra array-edge dummies, matching arrangement and long buses have not been designed. In particular, the larger scheme would add 375 MOS, 195 HBT, and 540 resistors, 1,110 units total.

The existing BGR occupies x=645–729, y=862–986 µm. T2F reaches x=638; TRIP reaches y=855; GATE starts x=850; inward top IO cells start y=1029. The rectangle x=638–850, y=855–1029 contains the current BGR and avoids these neighboring macro interiors. It is a local screening envelope, not all free die space. Existing decap intersections are itemized in the JSON; routed supply and signal conductors also consume it. The full 1350×1350 µm die area must not be treated as freely available for this change.

A 4× candidate already needs macro resizing and new placement/routing; baseline-overhead extrapolation is approximately the entire local envelope. A 16× candidate needs an explicit broader floorplan tradeoff before claiming fit. Electrical pilot results cannot establish area, density, matching, LVS, DRC, routing, supply, or extracted-performance acceptance.

Reproduce read-only accounting with an unused output path:

```sh
G1_CPUS=2 flow/run.sh python3 designs/g1-guardian/review/audits/audit_bgr_array_area.py --output designs/g1-guardian/review/audits/bgr-array-area-new
```

Inventory-only r1 is preserved. R2 adds independent netlist-to-PCell mapping and scope-limited area estimates. Canonical layout, models, and decks remain unchanged.

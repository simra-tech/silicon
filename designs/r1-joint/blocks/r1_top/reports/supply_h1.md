# r1_top try h1: ctrl supply feed with unmodified IO cells (track T8g, 2026-10-28)

Run of record: `asm-20261030-h1` (unfilled GDS; the fill adds only floating shapes). Decision basis: PLAN.md D24 (the
IO cells stay as shipped; the h0 `IOPadVss` riser is rejected). Reference runs: try h0 `asm-20261030-h0` (riser,
record of the rejected candidate) and try g `asm-20261028-g3`. Generator: `layout/r1_top_assemble_h.py` (default:
try h1). Scripts: `flow/supply_h_rnet.py` and `flow/supply_h.py` (as `supply_h0.md`; the VSS pads follow the
assembly JSON key `vss_pad_cell_origins_x`). Outputs: `<G1_RESULTS_ROOT>/r1_top/<run>/supply_rnet/` and
`<G1_RESULTS_ROOT>/r1_top/<run>/supply_h1.json`. All numbers are extracted, simulated or STA results. Nothing is
measured.

Commands (repository root; `G1_CPUSET`, `G1_RESULTS_ROOT`, `G1_WORKDIR` exported):

1. For each net in `VSS VDD VDDA` and each corner in `typ max`, run
   `flow/run.sh python3 designs/r1-joint/blocks/r1_top/flow/supply_h_rnet.py <run> <run>/supply_rnet <corner> <net>`.
2. Run `flow/run.sh python3 designs/r1-joint/blocks/r1_top/flow/supply_h.py <run> <run>/supply_h1.json <reference run>`.

## Method

Same as `supply_h0.md` (KLayout RNetExtractor on the top-level Metal1-TopMetal2 shapes, the ring with its IO cells
flat and the ctrl TopMetal1/TopVia2/TopMetal2 grid; typ and max sheet values; block currents as current sources;
ctrl 40.25 mA on 63 ports; pads at 0 V; ngspice DC; segment breakdown by region cut sets; EM of the new shapes with
extracted and bound rows).

## Why top-level metal cannot replace the riser

The PDK `sg13g2_IOPadVss` joins its bondpad strip (local y 0-3) to the core `vss` rail (TopMetal1 / Metal5, local
y 160-178) only through its Metal2 plate (x 3.91-75, y 0-158). Every layer from Metal3 to TopMetal2 carries the
full-width `iovss` / `iovdd` rails between them, and the LEF obstructs Metal1-TopMetal1 over y 0-178 and TopMetal2
over y 0-132.5. The fillers continue the rails around the ring. A top-cell shape from the bondpad to the `vss` rail
must cross an `iovdd` rail. The only free top-cell layer over the cell is TopMetal2 above local y 132.5; try h1 uses it
for pin access (fingers with TopVia2 onto the TopMetal1 `vss` pin). The `IOPadVss` and `IOPadIOVss` cells in the h1
GDS are identical to the PDK cells on every layer (XOR, `<G1_RESULTS_ROOT>/r1_top/asm-20261030-h1/probe_io_cells.json`).

## Variants (max sheet, worst ctrl grid point)

| Variant | Run | VSS: pad cells -> rail (mV) | VSS worst in ctrl (mV) | VDD worst (mV) | Loss (mV) | Feed R typ / max (Ω) |
| --- | --- | --- | --- | --- | --- | --- |
| try g | `asm-20261028-g3` | 26.9 | 63.6 | 30.6 | 94.2 | 1.71 / 2.34 |
| h0, riser (rejected) | `asm-20261030-h0` | 1.2 | 12.1 | 17.1 | 29.2 | 0.575 / 0.726 |
| h1a, h0 without the riser | `asm-20261030-h1-dev1` | 26.9 | 38.5 | 17.1 | 55.7 | 0.943 / 1.383 |
| h1b, + pad 4 `IOVSS` → `VSS` | `asm-20261030-h1-dev2` | 18.4 | 30.1 | 17.1 | 47.2 | 0.823 / 1.173 |
| h1c, + pad 6 `IOVSS` → `VSS` | `asm-20261030-h1-dev3` | 18.4 | 30.1 | 17.1 | 47.2 | 0.822 / 1.172 |
| **h1 (record)**: h1a + AFE VDDA strap | `asm-20261030-h1` | 26.9 | 38.5 | 17.1 | 55.7 | 0.943 / **1.383** |
| h1c with the AFE VDDA strap | `asm-20261030-h1-vss6` | 18.4 | 30.1 | 17.1 | 47.2 | 0.822 / 1.172 |

Target (T11b, `integration_checklist_g.md`): feed R ≤ 1.43 Ω, loss ≤ 57.6 mV, max sheet. h1: **passed**, 3.3 %
margin. h1c: passed, 18 % margin.

Breakdown of h1 (max sheet, region cut sets, `supply_h1.json` key `summary.max.breakdown` and the console logs):

| Net | Segment | Current (mA) | Voltage at the segment end (mV) |
| --- | --- | --- | --- |
| VSS | bondpads -> VSS IO rail, inside the two `IOPadVss` cells (Metal2 plate) | 44.5 | 26.9 |
| VSS | IO rail and south core rows | 26.2 (rail -> rows) | 28.0-28.5 |
| VSS | south straps and bar -> ctrl south stripe ends | 23.7 | 32.6 |
| VSS | columns and IO rows -> north row -> ctrl north stripe ends | 16.6 | 36.2 |
| VSS | worst point inside the ctrl grid | — | **38.5** |
| VDD | as h0 (no VDD change): pad-1 fingers, straps, bar, north path | 24.2 south / 16.0 north | worst **17.1** |

## Supply loss at every macro (supply drop + VSS rise, worst pin, mV)

| Macro (domain) | try g max | h0 typ / max | h1 typ / max | h1c (vss6, with strap) max |
| --- | --- | --- | --- | --- |
| `r1_ctrl` (VDD), worst grid point | 94.2 | 23.1 / 29.2 | 38.0 / 55.7 | 47.2 |
| `r1_adc` (VDD / VDDA) | 47.7 / 61.7 | 9.4 / 27.2, 12.2 / 35.2 | 24.1 / 41.9, 38.4 / 61.4 | 30.4 / 53.5 |
| `r1_isense` (VDD / VDDA) | 62.0 / 59.5 | 17.8 / 21.9, 23.6 / 29.1 | 32.5 / 36.6, 49.9 / 55.4 | 40.9 / 46.4 |
| `r1_osc` (VDD) | 63.0 | 17.3 / 22.0 | 32.0 / 48.3 | 39.4 |
| `r1_bias` (VDD / VDDA) | 45.6 / 70.5 | 5.7 / 34.0, 8.2 / 43.4 | 20.5 / 48.8, 34.6 / 69.7 | 26.7 / 61.8 |
| `r1_afe` (VDDA) | 106.4 | 59.8 / 75.8 | 66.7 / **93.1** | 84.9 |
| `r1_safe` (VDDA) | 48.5 | 16.1 / 22.1 | 30.7 / 48.2 | 39.4 |
| `r1_bgr` (VDDA) | 68.2 | 32.0 / 40.5 | 46.8 / 67.0 | 59.0 |
| `r1_t2f` (VDDA) | 79.5 | 39.5 / 49.5 | 54.2 / 75.9 | 67.7 |

Every VSS rise returns to about the try-g level of the pad cells (the 26.9 mV of the two Metal2 plates is common to
all macros). Every loss is below try g. The AFE VDDA strap (x 368-522, y 727-738, TopMetal1 11 µm) lowers the AFE
VDDA drop from 57.2 to 48.2 mV (max sheet); the AFE loss is 93.1 mV against 75.8 mV in h0 and 106.4 mV in try g.

## isense-bgr shared ground

Path R with the pads open 1.357 Ω typ / 1.822 Ω max (limit 2.3 Ω): **passed**. Offset isense - bgr with all
currents 3.01 / 3.87 mV, ctrl current alone 1.27 / 1.53 mV, isense current alone 1.82 / 2.45 mV (typ / max).

## EM

Limits as `supply_g.md` (Metal3/4/5 2 mA/µm, TopMetal1 15 mA/µm, TopMetal2 16 mA/µm; Via3/Via4 0.4 mA, TopVia1
1.4 mA, TopVia2 10 mA per cut). New shapes and via arrays (`supply_h1.json` key `em`): 69 rows, 0 failed, 10 rows
"not measured" (no node pair inside the shape; each has a passing bound row with the whole net current in the shape).
Trunks and straps of the network (`supply_rnet/supply_h_rnet_*.json` keys `em_cuts`, `em_gradient`), max sheet:
IO-filler VSS straps Metal4 ≤ 0.99 mA (limit 60), IO-filler VDD straps Metal3 ≤ 1.53 mA (limit 20), Metal4 VSS trunk
1.26 mA (limit 16), Metal4 VDD trunk 0.40 mA (limit 12), ctrl VDD stripes ≤ 3.74 mA (limit 33), west VDDA riser
Metal3 2.06 mA (limit 18.8): all passed. Largest new-shape currents: VDD pad-1 finger 17.9 mA (448), VSS bar 8.8 mA
(420), ctrl VSS stripe south end 3.9 mA (33). The macro supply pins carry the try-g currents (`supply_g.md`).

## Conclusion

1. With the IO cells as shipped, the ctrl feed resistance is 1.383 Ω at max sheet (limit 1.43 Ω): **passed**, small
   margin. The pin-map option h1c gives 1.172 Ω.
2. The isense-bgr shared ground is 1.82 Ω at max sheet (limit 2.3 Ω): **passed**.
3. EM: 69 new-shape rows and all trunk rows passed.
4. The ctrl derate and the chip checks of the same GDS: `README.md` "Supply feed with unmodified pads (try h1)".

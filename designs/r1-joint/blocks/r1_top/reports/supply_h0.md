# r1_top try h0: supply feed redesign for r1_ctrl (track T8f, 2026-10-28)

Run of record: `asm-20261030-h0` (unfilled GDS; the fill adds only floating shapes). Reference: try g, run
`asm-20261028-g3`, extracted again with the same script (`<G1_RESULTS_ROOT>/r1_top/supply-h-dev/diag_g3/`; the port
voltages equal `supply_g.md` to 0.000 mV). Generator: `layout/r1_top_assemble_h.py`. Scripts:
`flow/supply_h_rnet.py` (extraction, DC run, segment breakdown, EM of the new shapes) and `flow/supply_h.py`
(collection, macro loss, EM bound rows). Outputs: `<G1_RESULTS_ROOT>/r1_top/asm-20261030-h0/supply_rnet/` and
`<G1_RESULTS_ROOT>/r1_top/asm-20261030-h0/supply_h0.json`. All numbers are extracted or simulated; nothing is measured.

Commands (repository root, `G1_CPUSET`, `G1_RESULTS_ROOT`, `G1_WORKDIR` exported):

1. For each net in `VSS VDD VDDA` and each corner in `typ max`, run
   `flow/run.sh python3 designs/r1-joint/blocks/r1_top/flow/supply_h_rnet.py <run> <run>/supply_rnet <corner> <net>`.
2. Run `flow/run.sh python3 designs/r1-joint/blocks/r1_top/flow/supply_h.py <run> <run>/supply_h0.json <reference run>`.

## Method

Same as `supply_g.md` (KLayout RNetExtractor on the top-level Metal2-TopMetal2 shapes, the ring with its IO cells
and the ctrl TopMetal1/TopVia2/TopMetal2 grid; Metal1 and Via1 left out; typ and max sheet values; block currents as
current sources; ctrl 40.25 mA on 63 ports; pads at 0 V; ngspice DC). Two additions:

1. Segment breakdown. Every node is put in one region: `S_io_pad` (south IO cells below the inner rail, y < 299),
   `S_io_rail` (south inner IO rail band, y 299-322), `io_other` (west, east and north IO rows), `S_core_row`
   (south core rows, trunks and stacks, y 322-376), `WE_columns` (core columns), `N_core_row` (y > 1336),
   `S_feed` (y 376-684 between the columns), `ctrl_grid` (the ctrl box above y 684), `core_other`. For each region
   pair the element currents across the boundary are summed (an exact cut set) with the current-weighted mean voltage
   on both sides.
2. EM of the new shapes: bound rows (the whole net current in one shape) for every new shape and via array, plus the
   extracted cut or gradient value where the shape has nodes.

## Diagnosis (try g, max sheet, worst ctrl grid point)

| Net | Segment | Current (mA) | Voltage at the segment end (mV) | Share of the loss |
| --- | --- | --- | --- | --- |
| VSS | bondpads -> VSS IO rail, inside the two `IOPadVss` cells (Metal2 plate, one via strip) | 42.7 | 26.9 | 42 % |
| VSS | IO rail and south core rows | 20.4 / 22.5 (two ways) | 27.7-31.2 | 7 % |
| VSS | core columns and west/east/north IO rows to the north VSS row | 40.3 | 45.2 | 22 % |
| VSS | north row -> ctrl stripe ends (TopVia2) | 40.3 | 47.2 | 3 % |
| VSS | along the ctrl VSS stripes (2.2 um TopMetal1, fed from the north end only) | 40.3 | 63.6 | 26 % |
| VDD | bondpad -> VDD IO rail, `IOPadVdd` cell and ring TopMetal2 riser | 42.6 | 6.9 | 23 % |
| VDD | IO rail -> inner south VDD row (Metal3 straps, Metal4 trunk, stacks) | 30.8 | 12.0 | 17 % |
| VDD | south strap and 8 um bar -> ctrl south ends | 19.5 | 20.4 | 27 % |
| VDD | ring path to the north row -> ctrl north ends | 20.8 | 26.5 | — |
| VDD | along the ctrl VDD stripes (fed from both ends) | 40.3 | 30.6 | 13 % |

The VSS return is 63.6 of the 94.2 mV. Its two largest parts are the `IOPadVss` cells (27 mV) and the one-ended
feed of the ctrl VSS stripes (16 mV along the stripes plus 20 mV of ring path to the north row).

## New network (try h0)

| # | Change | Layers and size | Reason |
| --- | --- | --- | --- |
| 1 | `IOPadVss` riser (ring ECO in the ring copy of the cell, pads 2 and 5): IO TopMetal2 rails cut to 3.9 um stubs, TopVia2 only under the stubs, `iovdd` / `iovss` labels moved to the stubs, riser = three 18.33 um TopMetal2 fingers from the bondpad strip to a 65 x 18.5 um band with 297 TopVia2 onto the VSS TopMetal1 rail | the pattern of the PDK `IOPadVdd` cell of the same ring | removes the Metal2 path of the cell (27 -> 1.2 mV) |
| 2 | Two 28 um TopMetal2 fingers per VSS pad from the riser to the outer south VSS row | TopMetal2, y 317-342.16 | pad -> core row |
| 3 | VDD riser at pad 1: the outer VSS TopMetal2 row is opened over x 453-537; two 28 um TopMetal2 fingers join the pad-1 riser to the inner VDD row; a TopMetal1 bridge (x 425-571, 17.5 um) under the fingers keeps the VSS row continuous | TopMetal2 / TopMetal1 | VDD pad -> inner row without the Metal3/Metal4 path |
| 4 | TopMetal1 tabs between the VSS TopMetal1 IO rail and the outer VSS TopMetal2 row (9 new 22-23 um tabs with TopVia2, 5 stack pads extended) | TopMetal1, TopVia2 | rail and row in parallel |
| 5 | South VSS feed: TopMetal1 straps from the VSS IO rail, west x 566-590 (24 um, under the VDD TopMetal2 strap) and east x 1036-1064 (28 um, ADC-safe channel), to a TopMetal1 bar y 654.5-682.5 (28 um, x 561-1068), extensions onto the 7 ctrl VSS stripes | TopMetal1 only; no TopMetal1 over a MIM block | the ctrl VSS stripes are fed from both ends |
| 6 | South VDD feed: bar 28 um (y 664-692, try g 8 um), second TopMetal2 strap x 1036-1064 from the inner VDD row over the east VSS strap | TopMetal2 | wider bar, second strap |

Not used: TopMetal2 straps over the ADC. The rule allows TopMetal2 over MIM blocks, but the ADC TopMetal1 over the
CDAC is the MIM top plate, and a strap with 40 mA of digital return current over it couples into the comparator
input (recommended option: avoid). No macro moved. No signal route is crossed: the new shapes are TopMetal1 and
TopMetal2, the signal routes are on Metal2-Metal5 (generator self-check: 0 net conflicts, 0 routes inside macros,
0 TopMetal1 over MIM blocks).

## Results (extracted)

| Item | try g typ | try g max | try h0 typ | try h0 max | Limit / target |
| --- | --- | --- | --- | --- | --- |
| VSS rise at the ctrl, worst / best grid point (mV) | 46.1 / 31.7 | 63.6 / 46.8 | 10.1 / 5.2 | 12.1 / 6.3 | — |
| VDD drop at the ctrl, worst / best grid point (mV) | 22.8 / 18.0 | 30.6 / 25.1 | 13.1 / 7.9 | 17.1 / 11.1 | — |
| Supply loss at the ctrl, worst (mV) | 68.9 | 94.2 | 23.1 | 29.2 | ≤ 57.6 (T11b) |
| VDD + VSS feed resistance at 40.25 mA (Ω) | 1.71 | 2.34 | 0.575 | **0.726** | ≤ 1.2 (target), ≤ 1.43 |
| Shared isense-bgr VSS path, pads open (Ω) | 1.494 | 2.021 | 1.353 | 1.818 | ≤ 2.3 |
| Ground offset isense - bgr, all currents / ctrl alone (mV) | 5.34 / 3.60 | 6.78 / 4.46 | 3.14 / 1.36 | 3.99 / 1.61 | — |

Breakdown after the change (max sheet): VSS bondpads -> rail 1.2 mV (45.5 mA); south rows 1.4-1.8 mV; south straps
and bar to the ctrl south ends 5.9 mV (23.9 mA); north path 9.6 mV (16.3 mA); worst point inside the ctrl 12.1 mV.
VDD: pad riser fingers to the inner row 2.5 mV (30.2 mA); straps and bar to the ctrl south ends 8.1 mV (24.2 mA);
north path 14.9 mV (16.0 mA); worst point 17.1 mV. Full cut tables: `supply_h0.json`, key `summary.<corner>.breakdown`.

Supply loss at every macro (supply drop + VSS rise, worst pin, mV):

| Macro (domain) | try g typ | try g max | try h0 typ | try h0 max |
| --- | --- | --- | --- | --- |
| `r1_ctrl` (VDD), worst grid point | 68.9 | 94.2 | 23.1 | 29.2 |
| `r1_adc` (VDD / VDDA) | 31.1 / 42.2 | 47.7 / 61.7 | 9.4 / 27.2 | 12.2 / 35.2 |
| `r1_isense` (VDD / VDDA) | 41.6 / 40.0 | 62.0 / 59.5 | 17.8 / 21.9 | 23.6 / 29.1 |
| `r1_osc` (VDD) | 43.3 | 63.0 | 17.3 | 22.0 |
| `r1_bias` (VDD / VDDA) | 29.0 / 49.6 | 45.6 / 70.5 | 5.7 / 34.0 | 8.2 / 43.4 |
| `r1_afe` (VDDA) | 78.4 | 106.4 | 59.8 | 75.8 |
| `r1_safe` (VDDA) | 31.1 | 48.5 | 16.1 | 22.1 |
| `r1_bgr` (VDDA) | 47.9 | 68.2 | 32.0 | 40.5 |
| `r1_t2f` (VDDA) | 57.5 | 79.5 | 39.5 | 49.5 |

The VDDA network is not changed (drops equal try g); every VSS rise is lower. The largest remaining loss is the AFE
on VDDA (57 mV drop + 18.5 mV VSS rise at max sheet, out of 3.3 V).

## EM

Limits as `supply_g.md` (TopMetal1 15 mA/um, TopMetal2 16 mA/um, TopVia2 10 mA per cut). 64 rows, 0 failed:

| Item | I (mA) | Limit (mA) | Kind | State |
| --- | --- | --- | --- | --- |
| VSS pad riser fingers TopMetal2 28 um (4) | 46.9 | 448 | bound (all VSS current) | passed |
| VDD pad-1 riser fingers TopMetal2 28 um (2) | 17.9 (worst, max sheet) | 448 | extracted | passed |
| VSS bridge TopMetal1 17.5 um | 46.9 | 262.5 | bound | passed |
| west / east VSS TopMetal1 straps 24 / 28 um | 46.9 | 360 / 420 | bound | passed |
| VSS TopMetal1 bar 28 um | 46.9 | 420 | bound | passed |
| VSS stripe south ends TopMetal1 2.2 um (7) | 3.1-3.9 extracted; 23.9 bound (all south inflow in one) | 33 | extracted and bound | passed |
| west / east VDD TopMetal2 straps, VDD bar 28 um | 42.6 | 384 / 448 / 448 | bound | passed |
| `IOPadVss` riser TopVia2 (297 per pad) | 46.9 | 2970 | bound | passed |
| VSS bridge / tab TopVia2 (66 per tab) | 46.9 | 660 | bound | passed |
| VDD bar TopVia2 per ctrl VDD stripe (3 cuts) | 24.2 (all south VDD inflow) | 30 | bound | passed |

12 extracted rows are "not measured" (no node pair inside the shape); for each of them the bound row passes. The
macro supply pins carry the same currents as try g (`supply_g.md`; smallest margin `r1_adc` `vss` 1.4 %).

## Conclusion

1. The ctrl feed resistance is 0.726 Ω at max sheet (target ≤ 1.2 Ω, T11b limit 1.43 Ω): **passed**.
2. The isense-bgr shared ground is 1.82 Ω at max sheet (limit 2.3 Ω): **passed**; the offset falls from 6.8 to 4.0 mV.
3. EM: 64 rows, 0 failed.
4. The ctrl derate with this loss: `README.md` "Supply feed redesign (try h preparation)".
5. Chip checks of the same GDS: DRC main, antenna and maximal 0 (unfilled and filled), density 0, LVS (comparer-limit
   deck) "Netlists match", bond map `all_ok`. The stock LVS deck fails to run (KLayout signal 11, as try g).
   Status table: `README.md` "Supply feed redesign (try h preparation)".

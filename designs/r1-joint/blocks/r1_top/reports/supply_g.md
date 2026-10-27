# r1_top try g: supply network check (track T8e, 2026-10-27)

Run of record: `asm-20261028-g3` (unfilled GDS; the fill adds only floating fill shapes). Scripts:
`flow/supply_g_rnet.py` (extraction and DC run per net and corner), `flow/supply_g.py` (collection and EM table).
Outputs: `<G1_RESULTS_ROOT>/r1_top/asm-20261028-g3/supply_rnet/` (decks, ngspice logs, `supply_g_rnet_*.json`) and
`<G1_RESULTS_ROOT>/r1_top/asm-20261028-g3/supply_g.json`.

Commands (repository root, `G1_CPUSET`, `G1_RESULTS_ROOT`, `G1_WORKDIR` exported):

1. For each net in `VSS VDD VDDA` and each corner in `typ max`, run
   `flow/run.sh python3 designs/r1-joint/blocks/r1_top/flow/supply_g_rnet.py <run> <run>/supply_rnet <corner> <net>`.
2. Run `flow/run.sh python3 designs/r1-joint/blocks/r1_top/flow/supply_g.py <run> <run>/supply_g.json`.

## Method

1. The numbers are **extracted** from the layout, not estimated by square count as in try f. The method is the
   RNetExtractor method of `r1_isense` (`layout/pex/pex_build.py`), applied to the chip.
2. Geometry: every top-level Metal2-TopMetal2 and Via2-TopVia2 shape, flat, with the ring cell and its IO cells.
   The power grid of `r1_ctrl_top` (TopMetal1 stripes, TopVia2, TopMetal2 straps) is kept. The other macro metal is
   not part of the network.
3. Metal1 and Via1 are left out. The RNetExtractor stops with an internal error (`dbPLC.cc:543`) on the Metal1 ring
   annulus. Leaving out a parallel layer can only increase the resistance, so the result is conservative.
4. Net: KLayout `LayoutToNetlist`. The net is the net under the south Metal4 trunk at chip (380, 336 / 346 / 356).
5. Resistance: KLayout `RNetExtractor`, square counting. Sheet and via values: typ from `sg13g2_typ.itf`; max from
   the process specification Rev 1.2 (Metal2-5 0.088 / 0.103, TopMetal1 0.018 / 0.021, TopMetal2 0.011 / 0.0145
   Ω/sq; Via 9 / 20, TopVia1 2.2 / 4, TopVia2 1.1 / 2.2 Ω per cut).
6. Ports: one polygon port per macro supply hookup, with the block current as a current source. The `r1_ctrl`
   current is spread over 63 ports on its own TopMetal1 stripes (7 stripes × 9 heights). The pad openings are 0 V
   (VSS pads 2 and 5, VDD pad 1, VDDA pad 7). Bond wires and package are not modelled.
7. DC operating point with ngspice (pinned container).
8. Block currents (mA): `r1_ctrl` 40.25 (0.8 sign-off power 0.0483 W typ / 1.2 V), `r1_afe` 2.0 (ff), `r1_adc`
   1.97 (B5 tt: IDD 0.870 with the SAR + IDDA 1.102, simulated), `r1_isense` 1.588, `r1_safe` 0.418, `r1_bias`
   0.196, `r1_bgr` 0.080, `r1_t2f` 0.0625, `r1_osc` 0.317. Sources: `supply_g_rnet_*.json`, key `current_sources`.
9. Not included: dynamic drop, decoupling, package and bond wires, the macro-internal grids (except `r1_ctrl`).

## Shared ground of `r1_isense` and `r1_bgr` (VSS)

| Item | typ | max | Limit | State |
| --- | --- | --- | --- | --- |
| Path resistance isense VSS pin – bgr VSS pins, pads open | 1.494 Ω | 2.021 Ω | ≤ 2.3 Ω (brief) | passed |
| Offset resistance, pads at 0 V, isense current alone | 1.205 Ω | 1.623 Ω | — | — |
| V(isense) − V(bgr), all block currents | 5.34 mV | 6.78 mV | — | — |
| part from the `r1_ctrl` return current alone | 3.60 mV | 4.46 mV | — | — |
| part from the isense current alone | 1.91 mV | 2.58 mV | — | — |

The `r1_ctrl` return current gives a 3.6 mV (typ) offset between the isense ground and the bgr ground. Try f
estimated about 8 mV by square count. Try g runs g1 and g2: 4.52 mV and 3.60 mV typ (the south supply stacks of g2
carry part of the ctrl return current).

## Static IR drop

| Net | Point | typ (mV) | max sheet (mV) |
| --- | --- | --- | --- |
| VSS | `r1_ctrl` grid, worst / best of 63 points (rise above pad) | 46.1 / 31.7 | 63.6 / 46.8 |
| VSS | `r1_afe` pins (2) | 25.9 / 33.1 | 40.7 / 49.2 |
| VSS | `r1_adc`, `r1_isense`, `r1_osc`, `r1_bgr` | 19.9, 23.3, 26.9, 18.0 | 32.6, 37.0, 41.0, 30.3 |
| VDD | `r1_ctrl` grid, worst / best of 63 points | 22.8 / 18.0 | 30.6 / 25.1 |
| VDD | `r1_isense`, `r1_osc`, `r1_adc`, `r1_bias` | 18.3, 16.5, 11.2, 11.5 | 25.0, 22.0, 15.1, 16.0 |
| VDDA | `r1_afe` far pin / near pin | 45.3 / 44.6 | 57.2 / 56.4 |
| VDDA | `r1_adc`, `r1_isense`, `r1_safe` | 22.4, 16.7, 11.6 | 29.1, 22.5, 16.3 |
| VDDA | `r1_bgr`, `r1_bias`, `r1_t2f` | 29.9, 32.1, 35.3 | 37.9, 40.9, 44.4 |

`r1_ctrl` sees 22.8 + 46.1 = 69 mV (typ) of supply loss, 94 mV with max sheet: 5.7 % and 7.8 % of 1.2 V. The ctrl
sign-off was not checked for an IR-drop derate (not run). Run g1 had 56.3 mV VDD drop at the ctrl. The south VDD feed of run g2 (TopMetal2
strap x 566-590 and bar over the ctrl south band) reduced it to 23.6 mV. The analog blocks are on VDDA (3.3 V). The
largest VDDA drop is 57 mV at the AFE far pin (1.7 %).

## EM

Limits: process specification Rev 1.2, section 2.15 (105 °C, DC): Metal3-5 2.0 mA/µm, TopMetal1 15 mA/µm,
TopMetal2 16 mA/µm; Via3/Via4 0.4 mA, TopVia1 1.4 mA, TopVia2 10 mA per cut. Three kinds of rows:

1. **bound**: the whole block (or net) current in that one shape. If a bound passes, the shape passes.
2. **extracted, cut**: sum of the element currents across a line through a narrow strap (10 µm or 30 µm IO-filler
   straps). Used only where the strap is a single narrow conductor.
3. **extracted, gradient**: I = w × |dV/dl| / R_sheet along a long uniform strip, from the node voltages of the DC
   solve. Used for the Metal4 trunks and for the ctrl TopMetal1 stripes.

| Item | I (mA) | Limit (mA) | State |
| --- | --- | --- | --- |
| IO-filler VDD straps Metal3 10 µm (5), extracted cut typ | 8.85, 6.00, 3.88, 2.74, 2.00 | 20.0 | passed |
| same, max sheet | 8.26, 5.68, 3.81, 2.81, 2.07 | 20.0 | passed |
| Metal4 VDD trunk 6 µm, extracted gradient (typ / max) | 1.13 / 1.18 | 12.0 | passed |
| Metal4 VSS trunk 8 µm, extracted gradient (typ / max) | 1.23 / 1.24 | 16.0 | passed |
| ctrl VDD TopMetal1 stripes 2.2 µm (7), extracted gradient, worst (typ / max) | 4.05 / 3.87 | 33.0 | passed |
| south VDD feed TopMetal2 strap 24 µm / bar 8 µm (all ctrl VDD, bound) | 40.25 | 384 / 128 | passed |
| south VDD stack TopVia2 / TopVia1 / Via4 (one of 5, all ctrl VDD, bound) | 40.25 | 280 / 75.6 / 86.4 | passed |
| ctrl VDD TopVia2 per stripe at the south bar (1/7 of ctrl) | 5.75 | 30.0 | passed |
| VDDA trunks, risers (all 4.31 mA of VDDA, bound): Metal4 8 µm, pad-7 Metal4 6 µm, Metal5 15 µm, west Metal3 9.4 µm | 4.31 | 16 / 12 / 30 / 18.8 | passed |
| IO-filler VSS straps Metal4 30 µm (bound: all 46.9 mA of VSS in one strap) | 46.9 | 60.0 | passed |
| `r1_adc` pin `vss` Metal3 1.0 µm (IDD + IDDA, tt) | **1.972** | 2.0 | passed, margin 1.4 % |
| `r1_adc` pins `vdda` / `vdd` Metal3 1.0 µm | 1.102 / 0.870 | 2.0 | passed |
| `r1_afe` pins `vss` / `vdd` Metal3 1.0 µm (all 2.0 mA in one pin, bound) | 2.0 | 2.0 | passed, margin 0 |
| `r1_afe` Via3 at each supply pin (8 cuts, bound) | 2.0 | 3.2 | passed |
| `r1_safe` `vdda` 0.4 µm, `r1_bias` `vdd` neck 0.5 µm, `r1_osc` `vdd` 2 µm | 0.418, 0.050, 0.317 | 0.8, 1.0, 4.0 | passed |

Full table (75 rows): `supply_g.json`, key `em`. Some cut and gradient rows are "not measured": the line or the
strip has no extracted node pair (VSS straps x 828 and x 970; VDDA Metal4 trunk and pad-7 riser). For each of
these shapes, the bound row passes.

Method notes (evidence of runs g2 and g3 try 1): the cut-line sum is not valid on wide meshed shapes. It gave 12.6,
135 and 324 mA on the VDDA risers, with a total VDDA current of 4.31 mA. Cause: the RNetExtractor elements of a wide
polygon connect nodes that are not neighbours. These cuts were removed and replaced by the gradient method and the
bound rows.

## Conclusion

1. Every EM row passes at tt currents. The `r1_adc` `vss` pin (1.4 % margin) and the `r1_afe` supply pins (0 %
   margin if one pin carries all current) are the smallest margins. The ff currents of the ADC are not known.
   Recommendation for B6/B7 and E7: `vss` pin ≥ 2 µm (`reports/integration_checklist_g.md`).
2. The isense–bgr shared ground is 1.49 Ω typ / 2.02 Ω max (limit 2.3 Ω): passed.
3. Static drop at `r1_ctrl`: 69 mV typ / 94 mV max sheet, VDD plus VSS. This is an input for the ctrl timing derate
   (not run).

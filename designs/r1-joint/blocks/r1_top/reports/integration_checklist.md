# Integration checklist for the four pending macros (r1_top, 2026-10-21)

The assembly holds `r1_afe`, `r1_adc`, `r1_isense` (two instances) and `r1_osc` as placeholder outlines with
Metal3 pin stubs (`layout/r1_top_assemble.py`, list `PH`; pin positions in `r1_top_assembly.json`,
key `placeholder_pins`). A block replaces its placeholder when every item below is true.

## Common items (all four blocks)

1. Deliver the layout as GDS with one top cell and a `prBoundary` (189/4) equal to the outline.
2. Deliver a LEF (or a pin table with layer, side and box), the LVS CDL of record and the sha256 of each file.
3. Show block DRC (main, maximal, antenna) and block LVS with the stock deck. If the stock deck crashes, use the
   run-time copy with comparer limits only (T4 method) and say so.
4. Put signal and supply pins on Metal2, Metal3 or Metal4, on the side named in the table below.
   The top level lands on these pins with Metal3 (vertical) and Metal4 (horizontal).
5. Use no Metal5, TopMetal1 or TopMetal2 under the core-ring band (S6 cut C7), except as stated in item 6.
6. **MIM rule (coordinator, 2026-10-21).** The PDK MIM top plate is TopMetal1. A block with MIM carries TopMetal1
   over its capacitors. Over such a block the core ring uses TopMetal2 only and puts no via into the block.
   - Option taken in this assembly: TopMetal2 only, no detour. The west ring TopMetal1 columns are cut for
     y 645–1148 and replaced by TopMetal2 strips. TopVia2 arrays sit only at y 630–645 and 1148–1163, outside
     the AFE outline. The resistance does not increase; it decreases by about 0.17–0.19 Ω per column
     (`reports/connectivity.md`).
   - The block must keep its TopMetal1 at least 1.64 µm (TM1.b) from the remaining ring TopMetal1. Today the
     margin is 5 µm (AFE outline y 650–1143 against the cut ends at 645 and 1148).
   - If a block moves, the cut in `RING_ECO` of the generator must move with it.
7. Keep the 5 µm keep-out (S6 A1) inside the outline, with the block's own tap ring.
8. Give the supply current per supply (`VDDA`, `VDD`) so that the trunk widths can be checked (IR drop not run).

## Per block

| Block | S6 limit | Placeholder slot (x, y in µm) | Pin sides of the placeholder | MIM / TopMetal1 | State on 2026-10-21 |
| --- | --- | --- | --- | --- | --- |
| `r1_afe` | ≤ 0.069 mm² (C6); slot 140 × 493 µm | 336–476, 650–1143 | west: `sinp sinn cosp cosn` (from pads 21–24); south: `souts_p/n`, `soutc_p/n`, `vcm2`, `ib_s1/2`, `ib_c1/2`, `c1..c4`, `vdd`, `vss` | yes (TopMetal1 over MIM; also Metal5 and TopVia1). Ring over it: TopMetal2 only (done) | Laid out (commit d17d505f7, `blocks/r1_afe/layout/r1_afe.gds`): 192.8 × 494.4 µm = 0.095 mm². Over the limit by 0.026 mm². Pin sides match (inputs west on Metal3, outputs and controls south on Metal3). **Does not fit floorplan F1** (see README, open issue 1) |
| `r1_adc` | ≤ 0.050 mm² (C5); slot 291 × 172 µm | 381–672, 371–543 | north: 2 × 14 raw bits, `adc_valid_a/b`, `adc_hold`, `adc_start`, `adc_sel`, `is_smp` (to `r1_ctrl` south pins); west: `ain_sin_*`, `ain_cos_*` (from the AFE); east: `ain_isa_*`, `ain_isb_*`, `vref_in`; south: `vdda`, `vdd`, `vss` | yes (reference decoupling MIM). The slot starts at y 371, above the south TopMetal2 rows (y 327–362): no ring over it | not delivered |
| `r1_isense` (× 2) | ≈ 0.029 mm² each; slot 180 × 161 µm each, 180 × 332 µm for both | a: 1056–1236, 682–843; b: 1056–1236, 853–1014 | east: `inp`, `inn` (from pads 8–9 and 10–11); west: `outp`, `outn`, `az_win`, `is_smp`; south: `vdda`, `vdd`, `vss` | yes (hold capacitors). The slots end at x 1236, 4.4 µm west of the east ring TopMetal1 (x 1240.42): no ring over them. A wider block must use the same TopMetal2 conversion | In progress (T4f; untracked GDS seen at 07:10, not of record): one cell for both channels, 158.4 × 296.8 µm = 0.047 mm², fits the joint slot. Inputs east, outputs west, supplies south: sides match. Pin set differs from the placeholder: adds `vcm`, `vref`, `ibias_a/b`, `azh_a/b`; `is_smp` absent. The top must supply `vref`, `vcm` and two bias currents (no source block today) |
| `r1_osc` | ≈ 0.018 mm²; slot 170 × 106 µm | 1066–1236, 1064–1170 | west: `clk`, `osc_trim[4:0]`, `vdd`, `vss` (all toward `r1_ctrl`); `osc_en` is tied high at the top (register map §ANA_CTRL) | yes (Metal5/TopMetal1 for the MIM plates, PLAN.md §5 T1 row) | Laid out (PLAN.md §5: 154.4 × 118.4 µm; the working-tree GDS at 07:10 is 150.1 × 110.4 µm, T1b in progress). Height exceeds the slot (106 µm); the slot can grow down to y 1024 (`r1_isense_b` ends at 1014). **Pin side conflict:** `osc_clk` is on the east edge, `trim0..4` and `en` on the west edge. `r1_ctrl` is to the west. Ask for `osc_clk` on the west edge, or route it around the block (≈ 300 µm). `vdd` is north, `vss` south |

## Top-level work that each delivery starts

| Block | Top-level work |
| --- | --- |
| `r1_afe` | Pad 21–24 landings; AFE-to-ADC lines (shielded); PGA decoder `ana_ctrl[2:0]` to `c1..c4` (no block holds it); connect `u_ls_afe0..3`; bias source for `ib_*` (none exists) |
| `r1_adc` | 34 digital lines to `r1_ctrl`; `vref_in` from `VREF_BG` (check the load on the bandgap, rule of 2026-10-21) |
| `r1_isense` | Pad 8–11 landings; outputs to the ADC; `az_win`, `is_smp` from `r1_ctrl` |
| `r1_osc` | `clk` to `r1_ctrl/clk`; `osc_trim[4:0]` from `r1_ctrl` |

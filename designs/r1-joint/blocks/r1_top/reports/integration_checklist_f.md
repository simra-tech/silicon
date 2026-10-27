# Integration checklist, assembly try f (1700 µm ring, every macro real, 2026-10-27)

This list replaces `integration_checklist_e.md` for the drop-in of `r1_afe` layout E4 and `r1_adc` layout B into
`layout/r1_top_assemble_f.py`. The try-e list stays as the try-e record. Coordinates: "chip" = µm in the die frame;
"local" = µm in the macro frame (origin at the lower-left corner of the `prBoundary`), orientation R0. Pin positions
are pin-shape centres. Evidence for the numbers: README "Try f" and `reports/supply_f.md`.

## How a drop-in works

1. Put the new GDS and LVS CDL into `<G1_RESULTS_ROOT>/r1_top/<new run>/inputs/ofrecord/` with the names
   `r1_afe.gds`, `r1_afe_lvs.cdl`, `r1_adc.gds`, `r1_adc_lvs.cdl` (copy the other ofrecord files from the try-f run).
2. Export `R1F_SHA_r1_afe` / `R1F_SHA_r1_adc` (GDS sha256) and `R1F_CDL_SHA_r1_afe` / `R1F_CDL_SHA_r1_adc`
   (CDL sha256). Without them the generator and the CDL builder stop on the hash check.
3. Run `sh designs/r1-joint/blocks/r1_top/flow/run_try_f.sh <new run>` and then the fill steps (README "Try f").
4. The generator reads every pin from the GDS labels. A drop-in needs no code change if all items below hold.
   The self-check (`r1_top_assembly.json`: `self_check_net_conflicts`, `routes_inside_macros`,
   `tm1_over_mim_blocks`, `maze.failed`, `maze.access_failed`) must stay empty.

## Common items

1. One top cell, `prBoundary` (189/4) equal to the outline, origin at local (0, 0).
2. Block DRC (main, maximal, antenna) and block LVS with the PDK decks; the README names GDS and CDL sha256.
3. Pins: Metal3 pin shape (30/2) and Metal3 label (30/25) on the edge given below. Pin width along the edge
   ≥ 0.3 µm; signal pins ≥ 0.4 µm recommended (the access stub is 0.4 µm wide outside the outline).
4. MIM blocks: no TopMetal1 or TopMetal2 of the top level over the block. The top level runs Metal5 only outside
   the outline (exception: `r1_safe`, which has no Metal5).
5. Nothing of the block outside the outline. Keep 0.45 µm of the outline free of block metal next to a pin on
   Metal2–Metal4 only if the pin is closer than 0.45 µm to another pin (the router keeps 0.45 µm off the outline).
6. **Supply pins wide enough for EM** (failed in try f, `reports/supply_f.md`): PDK limit 2 mA per µm of Metal3
   width (process spec Rev 1.2, section 2.15). A 0.4 µm pin carries 0.8 mA at most.
7. **Density** (chip fill, run `asm-20261027-f3-fill`): the 800 µm window at chip (400, 400) is the weakest. Its
   minimum coverage is Metal2 25.97 %, Metal3 25.58 %, Metal1 26.41 % (limit 25 %). The top-level fill does not
   enter `r1_adc`, `r1_afe`, `r1_bias`, `r1_bgr` or `r1_t2f`. A new revision must not lower its own Metal1-Metal5
   coverage below the record (layout A, E3), or it must bring its own fill. `r1_safe` is open to Metal2 fill.
8. Maximal deck: no Metal1-TopMetal2 shape wider than 30 µm without a slit (`Slt.c`), in the block and at the top.

## r1_adc layout B (layout A in try f)

| Item | Requirement |
| --- | --- |
| Box, origin | ≤ 439.0 × 182.3 µm at chip (592.0, 376.0), R0. Free space: west 28 µm to `r1_bias` (x 564), east 57 µm channel to `r1_safe` (x 1088.8), north 115 µm to `r1_ctrl` (y 673.3) |
| North edge (local y 182.3), 36 digital pins | as layout A: `adc_hold` 2.0, `is_smp` 4.0, `clk` 6.0, `adc_start` 9.88, `adc_sel` 24.28, `adc_valid_a` 38.68, `adc_raw_a[k]` 53.08 + 14.4 k, `adc_valid_b` 254.68, `adc_raw_b[k]` 269.08 + 14.4 k (k ≤ 11), `adc_raw_b[12]` 431.0, `adc_raw_b[13]` 433.0, `por_n` 437.0. Other positions are allowed (maze router) if the pitch stays ≥ 1.6 µm |
| **SAR logic** | **Layout A has no SAR logic: the 34 digital north pins and `clk`, `por_n` connect to nothing inside the macro. Layout B must contain the SAR logic (or the digital pins must move to a logic block). Until then the chip cannot convert** (open issue 1 of try f) |
| West edge (local x 0) | `ain_sin_p` 110.0, `ain_sin_n` 114.0, `ain_cos_p` 130.0, `ain_cos_n` 134.0 (Metal5 pairs land by Metal3 necks from x −2.75; keep these four y values or tell T8), `vcm2` 150.0, `ibias` 165.0 |
| East edge (local x 439.0) | `ain_isa_p` 110.0, `ain_isa_n` 114.0, `ain_isb_p` 130.0, `ain_isb_n` 134.0 (Metal4 jogs from x 1044–1041, keep these four y values), `vcm` 150.0 |
| South edge (local y 0) | `vdda` 50.0, `vdd` 100.0, `vss` 150.0, `vref_in` 400.0. **Supply pins ≥ 1.0 µm wide** (IDDA 1.04 mA, IDD 0.90 mA, VSS 1.94 mA; layout A: 0.4 µm, EM failed) — or several pins per supply. Top-level risers are 2 µm Metal3 and can widen to 6 µm |
| Metal5 | the top level runs `VREF_BG` (Metal5 y 367.5–368.5, shields 365–366 and 370–371) and the isense lines (y 364.75–368.25 from x 1040.75) under the south edge. Keep the ADC Metal5 inside the outline |

## r1_afe layout E4 (E3 in try f)

| Item | Requirement |
| --- | --- |
| Box, origin | ≤ 192.8 µm wide (10 µm to `r1_ctrl` at x 538.8) at chip (336.0, 740.0), R0. Height ≤ 546 µm: top ≤ 1286 µm, 10 µm under `r1_gate_lv` (x 440–468.4, y 1296–1323.9); taller needs a `r1_gate_lv` move (tell T8). The ring ECO follows the height (TopMetal1 cut = outline ± 5 µm, TopMetal2 strips 15 µm longer) |
| South edge (local y 0) | as E3: `vss` 8.0, `souts_p` 18.4, `souts_n` 29.6, `vcm2` 40.8, `ib_s1` 52.0, `ib_s2` 63.2, `c1` 73.6, `c2` 84.8, `c3` 96.0, `c4` 107.2, `ib_c1` 118.4, `ib_c2` 128.8, `soutc_p` 140.0, `soutc_n` 151.2, `vdd` 162.4, `vss` 173.6, `vdd` 184.8. Other x values are allowed if `souts_*` stay west of x local 30.8 (the t2f west edge is at 30.8) and `soutc_*` stay east of x local 123 (east of the t2f) |
| **Supply pins** | **≥ 1.0 µm wide** (VDDA 2.0 mA at ff over 2 pins: 1.0 mA each, 0.4 µm pins carry 0.8 mA; EM failed in try f). The VSS pin at local 8.0 lands on the outer west column stack; the others on Metal4 rails at y 731–733 (VSS) and 735.6–738.4 (VDDA) |
| West edge (local x 0) | `sinp` 36.8, `sinn` 40.8, `cosp` 316.8, `cosn` 320.8. `sinp` and `cosp` must stay inside the pad windows (pads 21 and 23: chip y 765.11–789.88 and 1049.11–1073.88); `sinn`, `cosn` are free (jogs) |
| MIM | allowed (the ring over the AFE is TopMetal2 only); no TopMetal2 in the block |

## Other blocks (unchanged in try f; a change means a re-route)

| Block | Items the try-f routes depend on |
| --- | --- |
| `r1_ctrl_top` 0.7 (drop-in for 0.6; release `<G1_RESULTS_ROOT>/r1_ctrl/r1ctrl_07_release`, run `r1ctrl_ll_20261027_t17`) | same box and the same 127 pins as 0.6 (`pins_v06` slots unchanged), plus one new south pin `cur_trk` (ADC group, slot 35): local (280.80, 0) = chip (819.60, 673.3) at the try-f origin; route it to the SAR sub-macro input `cur_trk` (D21). box 532 × 679 at (538.8, 673.3); east taps local y 7.98–113.82 (crossbar), `az_win` 114.66, `clk` 389.34 and `osc_trim` 394.38 + 0.84 k (straight lines to the osc pins: an osc or ctrl pin move ≥ 0.1 µm breaks the overlap check), `fault_n` 531.30 |
| `r1_bias` revision 2 | box 120 × 236.74 at (444.0, 376.0); `vref_b` east y 147.14 (Metal4 1 µm riser, VSS shield), `vref` west y 116.44, `vdd` east y 48.74 |
| `r1_isense` layout c | (1113.8, 735.0); south pins at the 0.8 µm router grid (local x 1.6 … 4.8); outputs west y 34.4, 56.0, 179.2, 201.0; `vss` south x 8.8–10.4 (Metal3-Metal5 stack, shared ground ≤ 2.3 Ω, `reports/supply_f.md`) |
| `r1_safe` | (1088.8, 376.0); no Metal5 or TopMetal inside (the `VREF_B` Metal5 branch crosses it at y 644.5–645.5) |
| `r1_osc` revision 2 | (1088.8, 1041.8); west pins `osc_clk` 21.15, `en` 25.15, `trim0..4` 25.95 + 0.8 k |

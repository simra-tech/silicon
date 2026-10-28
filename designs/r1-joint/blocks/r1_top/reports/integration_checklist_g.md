# Integration checklist, assembly try g (1700 µm ring, current macros, 2026-10-27)

This list replaces `integration_checklist_f.md` for the drop-in of `r1_adc` layout B6 (final) and `r1_afe` layout E7
into `layout/r1_top_assemble_g.py`. The try-f list stays as the try-f record. Coordinates: "chip" = µm in the die
frame; "local" = µm in the macro frame (origin at the lower-left corner of the `prBoundary`), orientation R0. Pin
positions are pin-shape centres. Evidence: README "Try g" and `reports/supply_g.md`.

## How a drop-in works

1. Make a new run directory `<G1_RESULTS_ROOT>/r1_top/<new run>/inputs/` and copy `inputs/` of the run of record
   (`asm-20261028-g3`) into it.
2. Put the new GDS and LVS CDL into `inputs/ofrecord/` with the names `r1_adc.gds`, `r1_adc_lvs.cdl`, `r1_afe.gds`,
   `r1_afe_lvs.cdl`.
3. Export `R1G_SHA_r1_adc` / `R1G_SHA_r1_afe` (GDS sha256) and `R1G_CDL_SHA_r1_adc` / `R1G_CDL_SHA_r1_afe` (CDL
   sha256). Without them the generator and the CDL builder stop on the hash check.
4. Run `sh designs/r1-joint/blocks/r1_top/flow/run_try_g.sh <new run>` (all steps), then the fill and the fill checks
   (README "Try g", reproduction), then `flow/supply_g_rnet.py` for VSS, VDD and VDDA at typ and max and
   `flow/supply_g.py`.
5. The generator reads every pin from the GDS labels. A drop-in needs no code change if all items below hold. The
   self-check in `r1_top_assembly.json` (`self_check_net_conflicts`, `routes_inside_macros`, `tm1_over_mim_blocks`,
   `maze.failed`, `maze.access_failed`) must stay empty, and `merged_std_cells` must show no entry with
   `"merged": false`.
6. The chip CDL of record (`cdl/r1_top.cdl`) changes with every new block CDL. The post-layout campaign must take the
   CDL of the new run, not the try-g file.

## Common items

1. One top cell, `prBoundary` (189/4) equal to the outline, origin at local (0, 0).
2. Block DRC (main, maximal, antenna) and block LVS with the PDK decks; the README names GDS and CDL sha256.
3. PDK cells inside a macro must be the unmodified PDK cells. The generator merges a second copy (`sg13g2_*$N`) with
   the first copy only if both are identical; a differing copy stays a separate cell (`"merged": false`) and the
   CDL builder stops on the differing `.SUBCKT`.
4. A subcircuit that the block CDL defines and that another block CDL defines too (PDK standard cells, the bondpad
   cell) must be identical text; `lvs/make_top_cdl_g.py` stops otherwise.
5. MIM blocks: no TopMetal1 of the top level over the block. The top level uses TopMetal2 only over the AFE
   (west ring columns) and nowhere over the ADC.
6. Supply pins ≥ 1.0 µm (EM 2 mA per µm of Metal3). Currents above the values in `reports/supply_g.md` need a
   wider pin or a second pin.
7. Density: the chip fill does not enter `r1_adc`, `r1_afe`, `r1_bias`, `r1_bgr`, `r1_t2f`, `r1_isense`, `r1_osc`.
   A new revision must not lower its own Metal1-Metal5 coverage below the try-g inputs, or the chip window minimum
   (README "Try g", fill) can fail.
8. Maximal deck: no Metal1-TopMetal2 shape wider than 30 µm without a slit (`Slt.c`).

## r1_adc layout B6 (final) — what it must keep

| Item | Requirement |
| --- | --- |
| Box, origin | ≤ 439.0 × 205.42 µm at chip (592.0, 376.0), R0 (as B5 / B6-dev3). Free space: west 28.0 µm to `r1_bias` (x 564; the TopMetal2 VDD strap at x 566–590 is in this channel), east 57.8 µm to `r1_safe`, north 91.88 µm to `r1_ctrl` (the 37 digital routes and `VREF_B` Metal5 at y 642–648 use this channel). A taller box needs a new routing check (tell T8) |
| North edge (local y 205.42), 37 digital pins | Metal2 0.40 × 0.40 µm at y 205.02–205.42, labels in CDL form (`adc_raw_a<k>`): `adc_hold` 2.40, `is_smp` 4.32, `clk` 6.24, `adc_start` 10.08, `cur_trk` 16.80, `adc_sel` 24.48, `adc_valid_a` 38.88, `adc_raw_a<k>` 53.28 + 14.40 k, `adc_valid_b` 254.88, `adc_raw_b<k>` 269.28 + 14.40 k (k ≤ 11), `adc_raw_b<12>` 430.56, `adc_raw_b<13>` 433.44, `por_n` 437.28. Other x values are allowed (maze router) if the pitch stays ≥ 1.6 µm and the pins stay on Metal2 |
| West edge (local x 0) | `ain_sin_p` 110.0, `ain_sin_n` 114.0, `ain_cos_p` 130.0, `ain_cos_n` 134.0 (Metal5 pairs land by Metal3 necks from x −2.5; keep these four y values), `vcm2` 150.0, `ibias` 165.0 |
| East edge (local x 439.0) | `ain_isa_p` 110.0, `ain_isa_n` 114.0, `ain_isb_p` 130.0, `ain_isb_n` 134.0 (Metal4 jogs; keep these four y values), `vcm` 150.0 |
| South edge (local y 0) | `vdda` 50.0, `vdd` 100.0, `vss` 150.0, `vref_in` 400.0, Metal3 1.0 µm. **`vss` carries 1.97 mA (IDD + IDDA, B5 tt) against 2.0 mA for 1.0 µm: margin 1.5 %, ff not known. Recommended: `vss` ≥ 2.0 µm (or a second `vss` pin); the top-level riser is 2 µm and can widen** |
| `clk` pin load | ≤ 60 fF (top-level clock skew estimate, README "Try g"); B6-dev3 extracted top-level `clk` wiring 34.0 fF |
| Output timing | decision bits change ≥ 0.596 ns after the `clk` pin edge (tt); the top-level skew adds +31 … +97 ps (ADC later) to this margin |
| Metal5 / TopMetal | Keep the ADC Metal5 inside the outline. No TopMetal2 in the ADC (the top level keeps TopMetal2 off it). Metal5 density inside the box: see README "Try g", fill (chip deck result) |
| LVS CDL | port names as the B5 CDL (`adc_raw_a<k>`, `cur_trk`); extra ports (`topap`, `topan`, `topbp`, `topbn`) stay unconnected at the top level |

## r1_afe layout E7 — what it must keep

| Item | Requirement |
| --- | --- |
| Box, origin | ≤ 192.8 × 494.4 µm at chip (336.0, 740.0), R0 (E6). Height ≤ 546 µm (top ≤ 1286 µm, 10 µm under `r1_gate_lv`); the ring ECO follows the height |
| South edge (local y 0) | as E6 / E3: `vss` 8.0, `souts_p` 18.4, `souts_n` 29.6, `vcm2` 40.8, `ib_s1` 52.0, `ib_s2` 63.2, `c1` 73.6, `c2` 84.8, `c3` 96.0, `c4` 107.2, `ib_c1` 118.4, `ib_c2` 128.8, `soutc_p` 140.0, `soutc_n` 151.2, `vdd` 162.4, `vss` 173.6, `vdd` 184.8. `souts_*` west of local x 30.8, `soutc_*` east of local x 123 |
| Supply pins | ≥ 1.0 µm (E6: 1.0 µm). Two `vdd` and two `vss` pins, 1.0 mA each (2.0 mA at ff); the top level lands each pin at its full width with 8 Via3 |
| West edge (local x 0) | `sinp` 36.8, `sinn` 40.8, `cosp` 316.8, `cosn` 320.8; `sinp` and `cosp` inside the pad windows (pads 21 and 23: chip y 765.11–789.88 and 1049.11–1073.88) |
| MIM | allowed; no TopMetal2 in the block |

## Other blocks (unchanged in try g; a change means a re-route)

| Block | Items the try-g routes depend on |
| --- | --- |
| `r1_ctrl_top` 0.8 | box 532 × 679 at (538.8, 673.3), 128 pins `pins_v07` (`cur_trk` south local x 280.80, Metal2). **New in try g:** a top-level TopMetal2 bar over the ctrl south band (chip y 684.0–692.0 = local 10.7–18.7, x 561–1068) with TopVia2 onto the 7 VDD TopMetal1 stripes (local x 23.54 + 75.6 k, from local y 10.71). A new ctrl revision must keep these stripes (x and start height) and keep its own TopMetal2 at local y ≥ 23.7 (`TM2.bR`: 5.0 µm to the bar; its first strap is at local 23.84, 0.14 µm margin) |
| `r1_bias` revision 2 | box 120 × 236.74 at (444.0, 376.0); `vref_b` east y 147.14, `vref` west y 116.44, `vdd` east y 48.74 |
| `r1_isense` layout c | (1113.8, 735.0); `vss` south x 8.8–10.4 (shared ground with the bgr: path 1.49 Ω typ / 2.02 Ω max, `reports/supply_g.md`) |
| `r1_safe` | (1088.8, 376.0); no Metal5 or TopMetal inside (`VREF_B` Metal5 crosses at y 644.5–645.5) |
| `r1_osc` revision 2 | (1088.8, 1041.8); west pins `osc_clk` 21.15, `en` 25.15, `trim0..4` 25.95 + 0.8 k |
| `r1_ctrl_top` supply feed (target for try h, T11b 2026-10-28) | VDD + VSS feed resistance seen by the worst ctrl grid point ≤ **1.43 Ω** at 40.25 mA, max sheet (static loss ≤ 57.6 mV; try g 2.34 Ω / 94.2 mV max, 1.71 Ω / 68.9 mV typ). Reason: at the spec minimum 1.08 V the 0.8 setup slack is −1.13 ns with the try-g loss and needs ≥ 1 ns (README "Filled-chip extraction and ctrl IR derate (try g)"). The VSS return carries 63.6 of the 94.2 mV: widen or add the ctrl VSS return first. **Try h0 (T8f, 2026-10-28, run `asm-20261030-h0`, extracted): 0.726 Ω max / 0.575 Ω typ (loss 29.2 / 23.1 mV), passed (target ≤ 1.2 Ω).** Network: `layout/r1_top_assemble_h.py` (`IOPadVss` riser ECO in the ring copy of pads 2 and 5, south VSS TopMetal1 straps x 566-590 and 1036-1064 with a bar y 654.5-682.5, VDD TopMetal2 bar 28 µm at y 664-692 and a second strap x 1036-1064). Ctrl derate setup +2.42 ns worst (max sheet, grid spread), hold ≥ +0.10 ns. The ring ECO needs T6 acceptance (README "Supply feed redesign (try h preparation)", H1) |

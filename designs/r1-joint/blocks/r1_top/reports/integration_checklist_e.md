# Integration checklist, assembly try e (1700 um ring, floorplan C4, 2026-10-21)

This list replaces the try-d checklist (`integration_checklist.md`, 1600 um, kept as the try-d record) for the
1700 um die. A delivery drops into `layout/r1_top_assemble_e.py` without a top-level re-plan only if every item
below holds. Coordinates: "chip" = µm in the die frame (origin lower-left die corner); "local" = µm in the macro
frame (origin lower-left corner of the `prBoundary`), orientation R0. Pin positions are pin-shape centres.

## Common items (every block)

1. GDS with one top cell and a `prBoundary` (189/4) equal to the outline; the outline origin at local (0, 0).
2. LVS CDL of record and the sha256 of GDS and CDL; the block README names them. The generator checks the GDS
   hash (`EXPECT_SHA`), the CDL builder checks the CDL hash (`lvs/make_top_cdl_e.py`, `EXPECT`): update both
   lines in the same change that adopts a new revision.
3. Block DRC (main, maximal, antenna) and block LVS with the PDK decks; if the stock LVS deck crashes, the
   run-time copy with comparer limits only (T4 method), and say so.
4. Pins: Metal3 pin shape (30/2 or 30/0) with a Metal3 label (30/25) on the edge given below, ≥ 0.3 µm in the
   direction along the edge. A label that repeats (internal straps with the pin name) is allowed; the pin on the
   edge must be the smallest shape with that label at that edge (the generator picks it so).
5. MIM blocks: TopMetal1 on the MIM plates only, no TopMetal2. The top level puts no via into the block. Over a
   MIM block under a ring column the ring is TopMetal2 only (today only `r1_afe`). A taller AFE moves the cut
   (generator constants `AFE_Y0`, `AFE_Y1`).
6. Keep-out: 5 µm outside the outline (S7 A1); 10 µm between neighbours. Routes of the top level run in the
   halo; nothing of the block may stick out of the outline.
7. Supply current per supply (`VDDA`, `VDD`): needed for the trunk and riser widths (IR drop and EM not run).

## r1_adc (placeholder `r1_adc_ph` today)

| Item | Requirement |
| --- | --- |
| Box | ≤ 439.0 × 182.3 µm (S7 hard slot, gate G1 of the 1.6 mm option; 0.080 mm²) |
| Origin, orientation | chip (592.0, 376.0), R0. S7 C4 drew the ADC at x 556.0; +36 µm because `r1_bias` (120 µm wide) replaced its 87 µm slot |
| Ring | none above (south TopMetal2 rows end at y 362.16). MIM allowed; no TopMetal2 |
| North edge (local y = 182.3), 36 digital pins | `adc_hold` 2.0, `is_smp` 4.0, `clk` 6.0, `adc_start` 9.88, `adc_sel` 24.28, `adc_valid_a` 38.68, `adc_raw_a[k]` 53.08 + 14.4 k (k = 0…13, to 240.28), `adc_valid_b` 254.68, `adc_raw_b[k]` 269.08 + 14.4 k (k = 0…11, to 427.48), `adc_raw_b[12]` 431.0, `adc_raw_b[13]` 433.0, `por_n` 437.0. The 30 positions from `adc_start` to `adc_raw_b[11]` face the ctrl 0.4 south pins (straight drop, 114.7 µm); the other 6 need ctrl 0.6 template positions (below) or jogs |
| West edge (local x = 0) | `ain_sin_p` 110.0, `ain_sin_n` 114.0, `ain_cos_p` 130.0, `ain_cos_n` 134.0, `vcm2` 150.0 (output to the AFE), `ibias` 165.0 (new pin: `r1_bias` `ib_adc_ref`, 5 µA sourced into the ADC diode; `r1_bias` README open issue 2) |
| East edge (local x = 439.0) | `ain_isa_p` 110.0, `ain_isa_n` 114.0, `ain_isb_p` 130.0, `ain_isb_n` 134.0, `vcm` 150.0 (output to `r1_isense`) |
| South edge (local y = 0) | `vdda` 50.0, `vdd` 100.0, `vss` 150.0, `vref_in` 400.0 (from the `VREF_BG` strip at chip y 361) |
| Top-level work it starts | AFE → ADC (5 shielded, `chan_wv` x 569–587); isense → ADC (4 shielded, `chan_se` x 1036–1060); 36 digital; `ib_adc_ref`; `vref_in` (the bandgap then drives t2f, safe, isense and the ADC buffer: load check, rule of 2026-10-21); supplies from the trunks |

## r1_bias (placed in try e, layout of record 934b90195)

| Item | Requirement for later revisions |
| --- | --- |
| Box, origin | 120.0 × 165.94 µm at chip (444.0, 488.6), R0. S7 had an 86.8 × 69.7 µm bias slot at (442.0, 488.6) and a 55 × 55 µm POR slot at (345, 1270); the layout holds both functions: +2 µm in x, the POR slot is free |
| Pins to keep (local) | top edge (y 165.34): `ib_is_a` 30.49, `ib_sf_oa` 38.49, `ib_afe_s1` 42.39, `ib_sf_na` 46.49, `ib_adc_ref` 54.94, `ib_afe_c1` 55.89, `ib_sf_ob` 62.49, `ib_afe_s2` 69.19, `ib_sf_nb` 70.49, `ib_is_b` 78.49, `ib_afe_c2` 82.59; `vdda` bar y 162.34–164.34 full width; west: `pbias` y 142.19, `pcasc` 121.14; east: `por_n` 38.38, `vdd` 48.74; `vss` bar y 0–2 full width |
| Ring | none above; MIM (TopMetal1 on 4 plates) allowed |

## r1_ctrl 0.6 (hardened macro, today 0.4 t7)

| Item | Requirement |
| --- | --- |
| Box, origin | DIE_AREA 0 0 520 664 at chip (543.8, 673.0), R0 (S7 C4: 673.3; the top edge stays 0.3 µm under the inner north TopMetal2 row as in try d) |
| Unchanged pins (routed in try e; a move means a re-route) | north (Metal2, y 663.8): `gate_a` 36.5, `gate_b` 110.9, `gate_c` 185.3, `cs_n` 259.7, `ma_sclk` 334.1, `slo_sdo` 408.5; west (Metal3, x 0.2): `sdi` 27.7, `en_pad` 63.4; south (Metal2, y 0.2): `t2f_clk` 14.9 and the 30 ADC pins `adc_start` … `adc_raw_b[11]` at their 0.4 x (58.1 … 475.7) |
| Safe taps (new in 0.5) | `tap_p[31:0]`, `tap_n[31:0]` on the **east edge, local y 1.50 + 0.64 k (k = 0…63, to 41.82)**. The 64 lines run in `chan_safe` (chip y 674.5–715.0) from the `r1_safe` top edge, Metal2 and Metal4 alternating (1.28 µm pitch per layer), and must stay below chip y 716 (the `r1_isense` supply lines are at 717–730) |
| Moved pins (east) | `fault_n`, `clk`, `az_*`, `osc_trim[4:0]`, `cmp[3:0]` move up out of the tap band: east edge local y ≥ 50 (recommended 52.0, 62.5, 73.0 … at the 0.4 spacing of 10.5 µm, same order). Then `FAULT_N`, `OSC_CLK`, `OSC_TRIM`, `CMP` are re-landed (the `chan_e` tracks stay) |
| `por_n` | move from the north edge (local x 482.9, today a 1 330 µm route) to the **south edge local x 23.7** (chip 567.5, the `POR_N` riser): a 146 µm straight line from `r1_bias` |
| ADC pins without a facing stub | south edge local x: `adc_hold` 50.2, `is_smp` 52.2, `adc_clk` (new buffered clock output for the ADC) 54.2, `adc_raw_b[12]` 479.2, `adc_raw_b[13]` 481.2 (they then face the ADC stubs at chip 594.0, 596.0, 598.0, 1023.0, 1025.0) |
| isense auto-zero | outputs `az_a`, `azh_a`, `az_b`, `azh_b` (1.2 V; `r1_isense` shifts internally) on the east edge, above `cmp`; the contract (which ctrl signal drives `azh`) is not written yet (`INTERFACES.md`) |
| AFE gain and T2F controls (0.5 decode) | `pga_c[3:0]` on the west edge local y 41.0, 45.0, 49.0, 53.0 (chip 714–726, toward `u_ls_afe0..3` at chip x 405–447.8, y 716–727.7); `t2f_en`, `t2f_mode` on the west edge local y 1.0, 3.0 (needs two more tracks in the bgr–t2f gap: open item, try f) |
| Constraints kept | ≤ 240 000 µm² placed, 42 MHz, three corners (D10); TopMetal1/TopMetal2 stripes as t7 (`CTRL_VDD_X`, `CTRL_VSS_X` in the generator) |

## r1_afe revision E2 (today revision E of record, d17d505f7)

| Item | Requirement |
| --- | --- |
| Box, origin | ≤ 192.8 × 494.4 µm at chip (336.0, 740.0), R0. S7 C4: (336.0, 720.0); +20 µm so that `sinp` and `cosp` sit inside the `pad` windows of pads 21 and 23 at the 142 µm pitch |
| West pins (Metal3, x 0) | `sinp` y in 25.5–49.5 (today 36.8) and `cosp` in 309.5–333.5 (today 316.8): straight 15 µm lines from the pads. `sinn` 40.8 and `cosn` 320.8 (jogged from pads 22, 24; any y between 4 and 490 works, keep 4 µm from `sinp`/`cosp`) |
| South pins (Metal3, y 0) | routed: `vss` 8.0 and 173.6, `vdd` (VDDA) 162.4 and 184.8, `ib_s1` 52.0, `ib_s2` 63.2, `ib_c1` 118.4, `ib_c2` 128.8; pending: `souts_p` 18.4, `souts_n` 29.6, `vcm2` 40.8, `c1..c4` 73.6, 84.8, 96.0, 107.2, `soutc_p` 140.0, `soutc_n` 151.2. Width ≥ 0.4 µm |
| Ring | west columns over the AFE are TopMetal2 only (cut y 735–1239.4); a taller block needs a new cut |
| Note | the AFE was designed with ideal 10 µA; `r1_bias` gives 6.9–15.4 µA PTAT (`r1_bias` README open issue 1) |

## r1_isense revision b (today layout a of record, db5461161)

| Item | Requirement |
| --- | --- |
| Box, origin | ≤ 158.4 × 296.8 µm at chip (1088.8, 735.0), R0 (S7 C4, delta 0) |
| East pins (Kelvin bands) | `isa_n` local y in 30.6–54.4 (today 44.0) and `isb_p` in 172.6–196.4 (today 185.6): straight lines from pads 9 and 10; `isa_p` 40.8 and `isb_n` 188.8 are jogged (keep ≥ 3.2 µm from the straight ones) |
| South pins | routed: `vss` 9.6, `vdda` 12.0, `vdd` 153.6, `vref` 2.4, `ibias_a` 3.2; pending: `vcm` 1.6, `az_a` 4.0, `azh_a` 4.8. Recommended: ≥ 1.2 µm pitch for the control pins (today 0.8 µm; a landing via needs a 0.5 µm pad, so neighbours at 0.8 µm force staggered vias) |
| North pins | routed: `ibias_b` 3.2; pending: `az_b` 1.6, `azh_b` 2.4 |
| West pins | pending: `outa_p` 33.6–34.6, `outa_n` 55.2–56.2, `outb_p` 178.4–179.4, `outb_n` 200.0–201.0 |
| Ring | none above (east column from chip x 1340.42); a block wider than 251.6 µm would reach it |

## r1_osc (placed in try e: revision 2, layout r2d, commit 679a97320)

Revision 2 came during try e and is placed from run `asm-20261021-e3` on (run of record `asm-20261021-e4`). It meets the try-e request: `osc_clk` is on
the west edge, so `OSC_CLK` is a straight line from the ctrl `clk` pin.

| Item | Requirement for later revisions |
| --- | --- |
| Box, origin | 148.2 × 110.4 µm at chip (1088.8, 1041.8), R0 (S7 C4, delta 0). Keep ≤ 154.4 × 118.4 µm |
| West pins to keep (local y) | `osc_clk` 21.15, `en` 25.15, `trim0..4` 25.95, 26.75, 27.55, 28.35, 29.15 (0.8 µm pitch). A move re-lands `OSC_CLK`, `OSC_EN` and five trims |
| Supplies | `vss` bar y 0–2 and `vdd` bar y 108.4–110.4, full width. The top level lands at the east end of each bar, the `vdd` bar also at its west end, and the tie cell `VSS` at local x 6.4–7.9 of the `vss` bar |
| `en` | held high by `u_tie_osc` (`sg13g2_tiehi`) in the gap below the macro. Do not tie `en` to `VDD` directly: the four `en` gates then fail `Ant.e` (ring metal on the net). A ctrl `osc_en` output (0.6) replaces the tie cell |
| Ring | none above in C4 |

## Pad-adjacent positions (142 µm pitch against the S7 assumption of 140 µm)

Pad centres: S7 assumed 500, 640, 780, 920, 1060, 1200 µm (centred, 140 µm). Ring of record: 495, 637, 779, 921,
1063, 1205 µm. Delta per pad slot: −5, −3, −1, +1, +3, +5 µm (south, west from the corner at 141 µm; north,
east the same coordinates).

| Item | S7 C4 | Try e | Delta | Reason |
| --- | --- | --- | --- | --- |
| `r1_afe` origin | (336.0, 720.0) | (336.0, 740.0) | +20.0 y | `sinp`/`cosp` inside the pad 21/23 `pad` windows (y0 range 732.6–752.8): `SIN_P`, `COS_P` straight 15 µm (S7: 36 µm) |
| `r1_isense` origin | (1088.8, 735.0) | (1088.8, 735.0) | 0 | `isa_n`/`isb_p` already inside the pad 9/10 windows |
| `r1_gate_lv` origin | (440.0, 1300.0) | (440.0, 1296.0) | −4.0 y | try-d relation to the north ring row (+100 µm) |
| `GATE_A..C`, `CS_N`, `MA_SCLK`, `SLO_SDO` pad pins | x 500 … 1200 | x 495 … 1205 | −5 … +5 | ring of record |
| `SDI`, `EN` pad pins | y 500, 640 | y 495, 637 | −5, −3 | ring of record |
| `VDDA` feed (pad 7) | y 500 | y 481.1–505.9 | −5 | ring of record |
| `FAULT_N` pad pin | y 1200 | y 1203.1–1206.9 | +5 | ring of record |
| Pad route lengths (Manhattan) | `SIN`/`COS` 36 and 172; `ISA`/`ISB` 132–268 | `SIN_P`, `COS_P` 15; `SIN_N` 153, `COS_N` 157; `ISA_N`, `ISB_P` 132; `ISA_P` 272, `ISB_N` 270 | — | — |

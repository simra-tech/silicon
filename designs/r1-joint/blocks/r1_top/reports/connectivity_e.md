# r1_top connectivity table (assembly try e, 1700 um ring, floorplan C4, 2026-10-21)

Source of the routed rows: `r1_top_assembly.json` key `nets` (run `asm-20261021-e4`, the run of record of try e; runs `-e`, `-e2` and `-e3` are superseded) and the generator
`layout/r1_top_assemble_e.py`. Source of the pending rows: the `r1_adc_ph` pin list (same JSON, key
`placeholder_pins`), the unconnected instance pins in `cdl/r1_top_cdl.json`, the `r1_ctrl` 0.4 pin list (GDS labels
of run `r1ctrl_ll_20261021_t7`), the `r1_bias` README pin list and `blocks/INTERFACES.md`.
Coordinates are in µm in the chip frame. "Routed" means drawn in `r1_top.gds`; the LVS state is in the README
"Try e" status table. Routing rule (as try d): vertical segments on Metal3, horizontal segments on Metal4,
Via3 at the bends, 0.5 µm signal width (0.3–0.4 µm necks into narrow pins).

Try d had 20 routed signal nets. Try e has 46: the 20 of try d on the new geometry, 8 pad-to-macro analog lines,
13 bias lines (`PBIAS`, `PCASC`, 10 outputs, `POR_N`), `OSC_CLK`, `OSC_TRIM[4:0]`, `OSC_EN` and the new `VREF_BG` branch to
`r1_isense`.

## Supplies

| Net | Source | Destinations | Metal | State |
| --- | --- | --- | --- | --- |
| `VSS` | pads 2, 5 (IO-row `vss` rail) | outer core ring; `r1_ctrl` VSS TopMetal1 stripes to the outer north TopMetal2 row and the IO `vss` TopMetal1 rail (y 1381–1399); south Metal4 trunk y 332–340 with 5 Metal4 straps to the IO `vss` Metal4 rail (filler gaps x 535–597 … 1103–1165); `r1_bgr` (riser x 380–386), `r1_t2f` (x 470–476), `r1_bias` (x 562.5–563.5), `r1_safe` (west riser x 1086.5); `r1_afe` (stack on the outer west column y 729.5–733.5, Metal4 y 731–733); `r1_isense` (outer east column, Metal4 y 721–724); `r1_osc` (outer east column, Metal4 at its `vss` bar y 1041.8–1043.8); `u_tie_osc` `VSS` rail (riser into the osc `vss` bar); `r1_gate_lv` (outer west column, as try d); decap row (Metal4 strap x 1300–1306); `r1_ls` substrate | M2–M4, TM1, TM2 | routed |
| `VDD` | pad 1 (IO-row `vdd` rail) | inner core ring; `r1_ctrl` VDD stripes to the inner north TopMetal2 row; 4 north Metal3 straps (x 840, 975, 1120, 1250) stacked to TopMetal2; 5 south Metal3 straps to the Metal4 trunk y 343–349; `r1_t2f` `vdd12` (x 433.5), `r1_bias` `vdd` (x 566), `r1_safe` `vdd` (x 1085.5); `r1_isense` `vdd` (inner east column, Metal4 y 726–729.5); `r1_osc` `vdd` (inner east column, Metal4 at its `vdd` bar y 1150.2–1152.2, and the west riser x 1086.25–1086.75); `u_tie_osc` (`sg13g2_tiehi`) `VDD` rail; `r1_gate_lv` `vdd`, `gate_en`; 34 × `sg13g2_decap_8` | M1–M4, TM1, TM2 | routed |
| `VDDA` | pad 7 (`sg13g2_IOPadAnalog` `pad`, x 1379, y 481.1–505.9) | feed Metal4 x 1366–1372 to the trunk y 352–360 (x 326–1372); `r1_safe` `vdda` (east pin, Metal4 y 379.6–382); `r1_isense` `vdda` (Metal3 riser x 1366–1370 to y 719, Metal4 y 717–719); west riser Metal3 x 327–329 (y 352–738): `r1_bgr` `vdd` (Metal4 y 572–574), `r1_bias` `vdda` (riser x 441.5), `r1_afe` `vdd` ×2 (Metal4 y 736–738); `r1_t2f` `vdd` (riser x 537–541) | M3, M4 | routed |
| `VDDA`, `VDD`, `VSS` to `r1_adc_ph` | trunks | placeholder pins (S edge) | — | pending (placeholder) |
| `vdda`, `vdd` of the 6 `r1_ls` | — | — | — | pending (cells placed, not connected; as try d) |

### Core ring over MIM-bearing blocks (coordinator rule)

Option as try d: **TopMetal2 only over the block, no via into the block**. In C4 only `r1_afe` sits under a
ring column. The west TopMetal1 columns (x 324.82–339.82 VSS, 344.82–361.8 VDD) are cut for y 735–1239.4
(AFE outline 740–1234.4 ± 5 µm). Two TopMetal2 strips (same x, y 720–1254.4) replace them, with TopVia2
arrays only in the 15 µm overlaps (y 720–735 and 1239.4–1254.4). Resistance (estimated, square count as
try d, TopMetal1 0.018 Ω/sq, TopMetal2 0.011 Ω/sq, TopVia2 1.1 Ω per via, not extracted): outer column
cut 504.4 µm: TopMetal1 0.605 Ω → TopMetal2 strip 534.4 µm 0.39 Ω + two via arrays ≈ 0.04 Ω = 0.43 Ω;
inner (16.98 µm wide): 0.535 → 0.35 + 0.04 = 0.39 Ω. No penalty.

`r1_isense` (to x 1247.2), `r1_osc` (revision 2, to 1237.0) and `r1_safe` (to 1338.14, no MIM) end west of the east
TopMetal1 columns (from x 1340.42): **no east cut** (S7 §3.3 item 3 applies to the 1.6 mm C5 only).
`r1_adc_ph` (MIM allowed) and `r1_bias` (MIM, TopMetal1 on 4 plates) are under no ring conductor
(the south TopMetal2 rows end at y 362.16; the blocks start at y 376).

## Signals routed in try e

| Net | Source pin | Destination pin(s) | Metal and path | State |
| --- | --- | --- | --- | --- |
| `SIN_P`, `COS_P` | pads 21, 23 `pad` (y windows 765.1–789.9, 1049.1–1073.9) | `u_afe/sinp` (y 776.8), `cosp` (1056.8) | M3 straight, 15 µm | routed |
| `SIN_N`, `COS_N` | pads 22, 24 `pad` (centre y 919.5, 1203.5) | `u_afe/sinn` (780.8), `cosn` (1060.8) | M4, M3 x 330.5, M4; ≈ 153 / 157 µm | routed |
| `ISA_N`, `ISB_P` | pads 9, 10 `pad` | `u_isense/isa_n` (y 779.0), `isb_p` (920.6) | M3 straight, 132 µm | routed |
| `ISA_P`, `ISB_N` | pads 8, 11 `pad` (centre y 635.5, 1061.5) | `u_isense/isa_p` (775.8), `isb_n` (923.8) | M4, M3 (x 1345 / 1300), M4; ≈ 272 / 270 µm | routed |
| `VREF_BG` | `u_bgr/vref` (west pin, x 336, y 432.55) | `u_t2f/vref`, `u_safe/vref`, `u_isense/vref` | M3 x 333 down, M4 strip y 361 (x 333–1083), M3 x 1083 up, M4 y 728; branches M3 x 441.5 (t2f), M4 y 623 (safe); ≈ 1 250 µm, unshielded | routed; `r1_adc_ph/vref_in` pending |
| `PBIAS`, `PCASC` | `u_bgr/pbias`, `pcasc` (east pins) | `u_t2f/pbias`, `pcasc` (west pins after MY); `u_bias/pbias`, `pcasc` (west pins) | M4 necks, M3 tracks x 435.5 / 437.5, M4 | routed |
| `T2F_FOUT` | `u_t2f/fout` | `u_ctrl/t2f_clk` (south, Metal2) | M3 x 439.5, M4 y 662, M3, Via2 | routed |
| `SDI_P2C`, `EN_STO_IN_P2C` | pads 19, 20 p2c (y 495.0, 637.0) | `u_ctrl/sdi`, `en_pad` (west) | M4, M3 x 330.75 / 332.5, M4 y 663.5 / 665, M3 x 536 / 538 | routed |
| `POR_N` | `u_bias/por_n` (east pin, y 527.0) | `u_ctrl/por_n` (north pin, x 1026.7) | M4, M3 x 567.5, M4 y 666.5, M3 x 541 (strip between AFE and ctrl), M4 y 1348, M3, Via2; ≈ 1 330 µm | routed (the coordinator note said 0.4 has no `por_n`; the t7 GDS and CDL have it on the north edge) |
| `IB_AFE_S1`, `_C1`, `_S2`, `_C2` | `u_bias` top-edge outputs | `u_afe/ib_s1`, `ib_c1`, `ib_s2`, `ib_c2` (south) | M3 up, M4 y 668 / 669.5 / 671 / 672.5 west, M3 up; 0.4 µm neck | routed, unshielded |
| `IB_SF_OA`, `_NA`, `_OB`, `_NB` | `u_bias` top-edge outputs | `u_safe/ibias_oa`, `_na`, `_ob`, `_nb` (south edge) | M4 y 656.5–659.5 east under `r1_ctrl` (y < 673), M3 x 1038–1044 down, M4 strip y 362.2–365.8, M3 up | routed, unshielded |
| `IB_IS_A` | `u_bias/ib_is_a` | `u_isense/ibias_a` (south edge) | M4 y 655.5, M3 x 1084.5, M4 y 731, M3 | routed |
| `IB_IS_B` | `u_bias/ib_is_b` | `u_isense/ibias_b` (north edge) | M4 y 660.5, M3 x 1086 (west of the isense), M4 y 1034.5, M3 down | routed |
| `CMP_OC_A`, `CMP_NEG_A`, `CMP_OC_B`, `CMP_NEG_B` | `u_safe/oc_a`, `neg_a`, `oc_b`, `neg_b` (south edge) | `u_ctrl/cmp[0..3]` (east) | M4 strip y 367.0–370.6, M3 x 1077–1081.5, M4 | routed |
| `FAULT_N_C2P` | `u_ctrl/fault_n` | pad 12 c2p (y 1205) | M4, M3 x 1066.5, M4 y 1205 | routed |
| `OSC_CLK` | `u_osc/osc_clk` (revision 2, west edge, y 1062.95) | `u_ctrl/clk` (east) | M3 x 1068, M4 into the pin | routed (layout k needed a 360 µm detour around the osc; revision 2 removes it) |
| `OSC_TRIM_0..4` | `u_ctrl/osc_trim[0..4]` | `u_osc/trim0..4` (west, y 1067.75–1070.95, 0.8 µm pitch) | M3 x 1069.5–1075.5, M4 at the pin pitch | routed |
| `CS_N_P2C`, `MA_SCLK_P2C`, `SLO_SDO_C2P` | pads 16, 17 / `u_ctrl/slo_sdo` | `u_ctrl/cs_n`, `ma_sclk` / pad 18 | M2 stub, M3, M4 y 1368 / 1370.5 / 1373 | routed |
| `PWM_A`, `PWM_B`, `PWM_C` | `u_ctrl/gate_a`, `gate_b`, `gate_c` | `u_gate/pwm_a..c` | M2 stub, M3, M4 y 1340.5–1345.5 | routed |
| `GATE_A_C2P`, `GATE_B_C2P`, `GATE_C_C2P` | `u_gate/gc_a..c` | pads 13–15 c2p (`sg13g2_IOPadOut30mA`, shifter inside the pad) | M3, M4 y 1356 / 1358.5 / 1361 | routed |
| `OSC_EN` | `u_tie_osc/L_HI` (`sg13g2_tiehi`, MX at (1095.0, 1040.0), gap between isense and osc) | `u_osc/en` (west, y 1066.95) | M1 pad, M4 y 1037.5, M3 x 1084, M4 into the pin | routed: held high (oscillator always enabled; ctrl 0.4 has no oscillator enable). Runs `-e` and `-e2` tied `en` straight to `VDD`: 8 antenna markers (`Ant.e_TopMetal1/2`) on the four `en` gates |

## Signals pending

| Net group | Source | Destination | Blocker | Planned channel (try e geometry) |
| --- | --- | --- | --- | --- |
| AFE outputs `souts_p/n`, `soutc_p/n` (shielded) and `vcm2` | `u_afe` south (x 354.4, 365.6, 476.0, 487.2; `vcm2` 376.8) / `r1_adc` `vcm2` | `r1_adc_ph` W `ain_sin_*`, `ain_cos_*`, `vcm2` | ADC placeholder | M3 down from y 740 to y 674–690 (above the bias tracks), M4 east to `chan_wv` x 569–587, M3 down to the ADC west pins (y 486–541) |
| AFE gain `c1..c4` | `u_ctrl` (0.5: `pga_c[3:0]` decoded in `r1_ctrl`) → `u_ls_afe0..3` | `u_afe/c1..c4` (south, x 409.6–443.2) | ctrl 0.6 pins; LS supplies | LS cells sit under the pins (x 405–447.8, y 716–727.7); LS input lines from the ctrl west edge |
| ADC digital (2 × 14 raw, 2 valid, `adc_hold`, `adc_start`, `adc_sel`, `is_smp`), ADC `clk`, ADC `por_n` | `u_ctrl` south / `r1_adc` | each other | ADC placeholder; ADC clock source (not a ctrl 0.4 output; `OSC_CLK` is in `chan_e`) | band y 558.3–673 between the ADC slot and `r1_ctrl` (114.7 µm); straight drops for the 30 stubs that face a ctrl pin |
| `ib_adc_ref` | `u_bias/ib_adc_ref` (top edge x 498.94) | `r1_adc_ph/ibias` (W, y 541) | ADC placeholder; ADC must add the pin (`r1_bias` README open issue 2) | — |
| `VREF_BG` → ADC | strip y 361 | `r1_adc_ph/vref_in` (S, x 992) | ADC placeholder | M3 riser from the strip |
| isense outputs `outa_p/n`, `outb_p/n` (shielded) | `u_isense` west (y 768.6–935.8) | `r1_adc_ph` E `ain_isa_*`, `ain_isb_*` | ADC placeholder; `chan_e` is full (14 tracks) | `chan_se` x 1036–1060, down to the ADC east pins (y 486–510) |
| isense `vcm` | `r1_adc` reference | `u_isense/vcm` (south x 1090.4) | ADC placeholder | — |
| isense `az_a`, `azh_a`, `az_b`, `azh_b` | ctrl 0.4 has `az_win` only | `u_isense` (south x 1092.8, 1093.6; north x 1090.4, 1091.2) | the az/azh mapping is not in a contract (`INTERFACES.md`); ctrl 0.6 | — |
| safe tap inputs `oa_p0..nb_n7` (64) | ctrl 0.4 has `thr_*`/`cal_*` (48 bits); the adders are in ctrl 0.5 (`tap_p[31:0]`, `tap_n[31:0]`) | `u_safe` top edge (y 663.81) | **pending until ctrl 0.6** (hardened 0.5 RTL) | `chan_safe` y 669–715, Metal2 and Metal4 alternating, into the ctrl east edge (see checklist) |
| `t2f en`, `t2f mode` | ctrl 0.5 `t2f_en`, `t2f_mode` → `u_ls_t2f0/1` | `u_t2f` west pins (y 475.1, 411.2) | ctrl 0.6 pins; LS supplies | — |
| `bias_en` (ctrl 0.5) | `u_ctrl` | — | `r1_bias` has no enable pin | not applicable today |
| `ana_ctrl[15:0]` (ctrl 0.4 raw register bits) | `u_ctrl` west | — | replaced by the 0.5 decode | not applicable to 0.4 |
| safe diagnostics `outa_p/n`, `outb_p/n`; `r1_bgr` `iptat`, `vbe`, `dvbe`; `r1_gate_lv` `vdda` | — | — | — | not applicable (test or spare pins) |

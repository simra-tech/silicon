# r1_top connectivity table (assembly try d, 2026-10-21)

Source of the routed rows: `r1_top_assembly.json` key `nets` and the generator `layout/r1_top_assemble.py`.
Source of the pending rows: the placeholder pin lists (same JSON, key `placeholder_pins`), the unconnected
pins in `cdl/r1_top_cdl.json`, the `r1_ctrl` 0.4 pin list (`r1_ctrl_top.lef`, run `r1ctrl_ll_20261021_t7`)
and S6 §4. Coordinates are in µm in the chip frame. "Routed" means drawn in `r1_top.gds` and confirmed by LVS.
Routing rule: vertical segments on Metal3, horizontal segments on Metal4, Via3 at the bends, 0.5 µm signal width.

## Supplies

| Net | Source | Destinations | Metal | State |
| --- | --- | --- | --- | --- |
| `VSS` | pads 2, 5 (IO-row `vss` rail, Metal3 to TopMetal1) | outer core ring (TopMetal1 columns, TopMetal2 rows); `r1_ctrl` VSS TopMetal1 stripes extended to the IO `vss` TopMetal1 rail (y 1281–1299) with TopVia2 on the outer row; south Metal4 trunk y 332–340 with 5 Metal4 straps to the IO `vss` Metal4 rail; `r1_bgr`, `r1_t2f`, `r1_safe`, `r1_gate_lv` `vss`; `r1_ls` `vss` (substrate); decap row (Metal4 strap x 1160–1166) | M2–M4, TM1, TM2 | routed |
| `VDD` | pad 1 (IO-row `vdd` rail) | inner core ring; `r1_ctrl` VDD TopMetal1 stripes to the inner TopMetal2 row; 4 north Metal3 straps (x 776, 916, 1056, 1196) stacked to TopMetal2; 5 south Metal3 straps to the Metal4 trunk y 343–349; `r1_t2f` `vdd12`, `r1_safe` `vdd`, `r1_gate_lv` `vdd` and `gate_en`; 34 × `sg13g2_decap_8` (antenna load) | M1–M4, TM1, TM2 | routed |
| `VDDA` | pad 7 (`sg13g2_IOPadAnalog` `pad`, x 1279, y 436–461) | Metal4 trunk y 352–360; `r1_bgr` `vdd`, `r1_t2f` `vdd`, `r1_safe` `vdda` | M3, M4 | routed |
| `VDDA`, `VDD`, `VSS` to `r1_afe`, `r1_adc`, `r1_isense_a/b`, `r1_osc` | trunks above | placeholder pins | — | pending (placeholders) |
| `vdda` of the 6 `r1_ls` cells, `vdd` of the 6 `r1_ls` cells | — | — | — | pending (cells placed, not connected) |

### Core ring over MIM-bearing blocks (coordinator rule of 2026-10-21)

Option taken: **TopMetal2 only over the block, no via into the block**. The west ring TopMetal1 columns
(x 324.82–339.82 VSS, 344.82–361.8 VDD) are cut for y 645–1148, over the AFE outline (y 650–1143). Two TopMetal2
strips (same x, y 630–1163) replace them. TopVia2 arrays sit only in the 15 µm overlaps at y 630–645 and
1148–1163, outside the AFE outline. There is no detour. Estimated resistance (square count, ITF sheet
resistance TopMetal1 0.018 Ω/sq, TopMetal2 0.011 Ω/sq, TopVia2 1.1 Ω per via; not extracted):

| Column | TopMetal1 before | TopMetal2 strip + 2 via arrays | Change |
| --- | --- | --- | --- |
| outer (VSS), 15 µm wide, 503 µm long | 0.604 Ω | 0.369 + 2 × 0.022 = 0.414 Ω | −0.19 Ω |
| inner (VDD), 16.98 µm wide | 0.533 Ω | 0.326 + 2 × 0.020 = 0.365 Ω | −0.17 Ω |

So the change has no resistance penalty. The east columns (x 1240.42–1275.42) do not overlap a MIM-bearing
block: the `r1_isense` and `r1_osc` placeholders end at x 1236. `r1_safe` (Metal1–Metal4 only) sits under the
east columns as S6 cut C7 allows. The south TopMetal2 rows (y 327–362) end above no block (the blocks start at y 371).

## Signals routed today

| Net | Source pin | Destination pin(s) | Metal | State |
| --- | --- | --- | --- | --- |
| `CS_N_P2C` | pad 16 `CS_N` p2c | `u_ctrl/cs_n` | M2 stub, M3, M4 (track y 1268) | routed |
| `MA_SCLK_P2C` | pad 17 `MA_SCLK` p2c | `u_ctrl/ma_sclk` | M2 stub, M3, M4 (y 1270.5) | routed |
| `SLO_SDO_C2P` | `u_ctrl/slo_sdo` | pad 18 `SLO_SDO` c2p | M2 stub, M3, M4 (y 1273) | routed |
| `PWM_A`, `PWM_B`, `PWM_C` | `u_ctrl/gate_a`, `gate_b`, `gate_c` | `u_gate/pwm_a`, `pwm_b`, `pwm_c` | M2 stub, M3, M4 (y 1240.5, 1243, 1245.5) | routed |
| `GATE_A_C2P`, `GATE_B_C2P`, `GATE_C_C2P` | `u_gate/gc_a`, `gc_b`, `gc_c` | pads 13–15 c2p (`sg13g2_IOPadOut30mA`, 1.2 V input, shifter inside the pad) | M3, M4 (y 1256, 1258.5, 1261) | routed |
| `FAULT_N_C2P` | `u_ctrl/fault_n` | pad 12 `FAULT_N` c2p | M3, M4 (y 1175, x 1277.5) | routed |
| `SDI_P2C` | pad 19 `SDI` p2c | `u_ctrl/sdi` | M3, M4 | routed |
| `EN_STO_IN_P2C` | pad 20 `EN` p2c | `u_ctrl/en_pad` | M3, M4 (y 590) | routed |
| `T2F_PBIAS`, `T2F_PCASC` | `u_bgr/pbias`, `pcasc` | `u_t2f/pbias`, `pcasc` | M3, M4 (y 368.5, 366.5) | routed |
| `VREF_BG` | `u_bgr/vref` | `u_t2f/vref`, `u_safe/vref` | M3, M4 | routed; `r1_adc` `vref_in` pending |
| `T2F_FOUT` | `u_t2f/fout` | `u_ctrl/t2f_clk` | M2 stub, M3, M4 | routed |
| `CMP_OC_A`, `CMP_NEG_A`, `CMP_OC_B`, `CMP_NEG_B` | `u_safe/oc_a`, `neg_a`, `oc_b`, `neg_b` | `u_ctrl/cmp[0..3]` | M3, M4 (y 362.5–367) | routed |

## Signals pending

| Net group | Source | Destination | Planned metal | State and blocker |
| --- | --- | --- | --- | --- |
| encoder inputs `SIN_P/N`, `COS_P/N` | pads 21–24 (`pad` or `padres`) | `r1_afe` `sinp sinn cosp cosn` (west side) | M2–M4 | pending: placeholder |
| AFE outputs (4) and `vcm2` | `r1_afe` `souts_p/n`, `soutc_p/n`, `vcm2` | `r1_adc` `ain_sin_*`, `ain_cos_*` | M2–M4, shielded | pending: placeholder; real AFE does not fit F1 (README, open issue 1) |
| AFE gain `c1..c4` | `u_ctrl/ana_ctrl[2:0]` through a decoder (codes 0–7 to `c1..c4`) and `u_ls_afe0..3` | `r1_afe` `c1..c4` | M2–M4 | pending: the decoder exists in no block (`R1_REGISTER_MAP.md` §ANA_CTRL gives it to the chip level) |
| AFE bias `ib_s1 ib_s2 ib_c1 ib_c2` | no source in the block set | `r1_afe` | — | pending: no bias source block |
| ADC digital (2 × 14 raw bits, 2 valid, `adc_hold`, `adc_start`, `adc_sel`, `is_smp`) | `u_ctrl` south pins / `r1_adc` | each other | M2–M4 | pending: placeholder |
| ADC current inputs (4) | `r1_isense_a/b` `outp outn` | `r1_adc` `ain_isa_*`, `ain_isb_*` | M2–M4 | pending: placeholders |
| current-sense inputs | pads 8–11 `ISA_P/N`, `ISB_P/N` | `r1_isense_a/b` `inp inn` (east side) | M2–M4 | pending: placeholders |
| `az_win`, `is_smp` | `u_ctrl` | `r1_isense_a/b` | M2–M4 | pending: placeholders |
| `clk` | `r1_osc` `clk` | `u_ctrl/clk` | M2–M4 | pending: placeholder (`osc_en` tied high at the top, no pin on the placeholder) |
| `osc_trim[4:0]` | `u_ctrl/osc_trim` | `r1_osc` | M2–M4 | pending: placeholder |
| `por_n` | none | `u_ctrl/por_n` | — | pending: no POR block |
| safe thresholds `nP/nN[7:0]` × 4 (64 bits) | `u_ctrl` has `thr_*`/`cal_*` (6 + 6 bits × 4 = 48 bits) | `u_safe` `oa_p*`…`nb_n*` | M2–M4 | **blocked**: interface gap, the adders `nP = 4c + ceil(d/2)`, `nN = 4(63−c) − floor(d/2)` exist in no block |
| safe bias `ibias_oa/na/ob/nb` (4 × 5 µA PTAT) | `r1_bgr` has one `iptat` | `u_safe` | M2–M4 | pending: no 4-output bias source |
| safe diagnostics `outa_p/n`, `outb_p/n` | `u_safe` | — | — | not applicable (test outputs, no destination in the pin map) |
| `t2f en`, `t2f mode` | no `r1_ctrl` output (proposal `ana_ctrl[3]`, `[4]`) | `u_t2f` through `u_ls_t2f0/1` | M2–M4 | pending: interface gap; the `r1_t2f` gates on these pins float today |
| `r1_bgr` `iptat`, `vbe`, `dvbe` | `u_bgr` | — | — | not applicable today (test or spare outputs) |
| `r1_gate_lv` `vdda` | — | — | — | not applicable (bare pin of variant L, `r1_gate` README) |

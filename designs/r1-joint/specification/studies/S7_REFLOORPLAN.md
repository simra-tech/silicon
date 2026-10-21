# S7 — re-floorplan with the real macros (2026-10-21)

Study by an agent (Opus 5.5). The floorplans are rectangles only. Nothing in this study is laid out or checked by DRC.
Labels: **laid out** (a block GDS exists), **working tree** (a block GDS exists but it is not of record),
**slot** (no layout; this study sets the box), **assumed** (a choice of this study, with a reason).

Question: with the real macro sizes, does R1 fit the 1.6 mm die with ≥ 5 % margin and with routable channels?
Or must D10 escalate to 1.7 mm (PLAN.md §2a)?

Answer in short:

1. **The try-d topology does not hold the real macros.** `r1_safe` (249.3 µm wide) has no place (candidate C0).
2. **Without new integration rules, no 1.6 mm candidate reaches 5 %.** The best is 4.2 % (C3, pin-map swap,
   `r1_safe` re-shaped). C1 (no pin-map change) gives 3.8 %. C2 (digital macro in landscape) gives 3.1 %.
3. **One 1.6 mm candidate reaches 5.5 % (C5).** It is C3 plus two levers. The first lever moves the `VDDA`
   decoupling into the south ring band, over the trunks. The second lever uses the `r1_osc` revision-2 size.
   The channels are routable only with a pin template for `r1_ctrl` 0.5. The headroom above the 5 % bar is
   0.004 mm².
4. **The S6 escalation trigger has tripped as written.** The laid-out analog sum is 0.215 mm². With the
   working-tree `r1_isense` (0.047) and the ADC slot (0.080), it is 0.342 mm² > 0.30 mm².
5. **1.7 mm fits with 13.4 % (C4).** All macros stay as laid out. No block re-shape and no new rule is necessary.
6. **Recommendation (§5):** keep 1.6 mm with floorplan C5 as a gated option. Replace the 0.30 mm² proxy
   trigger with the seven S7 gates. Escalate to 1.7 mm (C4) at the first missed gate. This recommendation
   changes a rule that was agreed in advance. The coordinator records it as a D10 amendment.

## 1. Macros and allowances

### 1.1 Macro table

Sizes are the block outline (prBoundary). Pin sides are as laid out.

| Block | Size (µm) | mm² | State and source | Pin sides (as laid out) | MIM / TopMetal1 |
| --- | --- | ---: | --- | --- | --- |
| `r1_ctrl` 0.4 | 520 × 664 | 0.3453 | hardened, run `r1ctrl_ll_20261021_t7` (239 201 µm² placed, 75.15 % of the snapped core) | N 7 (gates, bus, `por_n`); E 60 (`fault_n`, `clk`, `az_win`, `osc_trim`, `cmp`, `thr_*`, `cal_*`); S 35 (ADC, `t2f_clk`); W 18 (`ana_ctrl`, `sdi`, `en_pad`) | TopMetal1 stripes; stays in the conservative window |
| `r1_afe` E | 192.8 × 494.4 | 0.0953 | laid out, d17d505f7 | W: `sinp`/`sinn` at y 36.8/40.8, `cosp`/`cosn` at 316.8/320.8; S: 17 pins (outputs, `vcm2`, bias, `c1..c4`, supplies) | yes (TopMetal1 over MIM) |
| `r1_safe` 3 | 249.34 × 287.81 | 0.0718 | laid out, `layout-gen-20261021-b` | top: 64 code bits; bottom: flags, `ibias_*`, `outa/b`; W: `vref`; supplies both sides | no (Metal1–Metal4) |
| `r1_isense` (2 channels) | 158.4 × 296.8 | 0.0470 | working tree 2026-10-21 07:41 (not of record) | E: `isa_p/n` at y ≈ 41–44, `isb_p/n` at ≈ 186–189; W: outputs, `az`, `azh`, `ibias`, `vref`, `vcm`; S: supplies | yes |
| `r1_osc` | 154.4 × 118.4 (revision 2 working tree 148.2 × 110.4 = 0.0164) | 0.0183 | laid out (layout k) | W: `en`, `trim0..4`; E: `osc_clk`; N `vdd`, S `vss` | yes (Metal5/TopMetal1 plates) |
| `r1_bgr` | 96.0 × 194.3 | 0.0187 | laid out | 8 Metal3 pins | no |
| `r1_t2f` | 92.0 × 102.6 | 0.0094 | laid out (G1 revision 2) | — | no |
| `r1_gate_lv` | 28.39 × 27.9, one instance with three channels | 0.0008 | laid out (variant L) | — | no |
| `r1_ls` × 6 | 9.2 × 11.7 each | 0.0006 | laid out | — | no |
| `r1_adc` 5 | **slot 0.080** | 0.0800 | not laid out; revision 5 estimate 0.0755 (CDAC 0.0185, comparators 0.004, switches and SAR 0.012, reference 3c with filter 0.041) | slot (§5) | yes (reference decoupling) |
| bias source | slot 87 × 70 | 0.006 | **assumed**: no block exists (`r1_top` interface gap 3) | — | — |
| POR | slot 55 × 55 | 0.003 | **assumed**: no block exists (gap 2) | — | — |
| **Analog sum** (ADC slot, isense working tree) | | **0.342** | laid out 0.215 | | |

The brief gave the ADC as 0.068 mm². That was revision 4. Revision 5 is 0.0755 mm² (`blocks/r1_adc/README.md`).
The slot adds 6 % for layout.

### 1.2 Allowances (S6, with the corrections from the try-d assembly)

| # | Allowance | S6 | S7 | Reason for the change |
| --- | --- | --- | --- | --- |
| A1 | Keep-out around each analog block | 5 µm per side, outside | 5 µm outside the outline (halo), 10 µm between neighbours. It is not also inside the outline | `reports/integration_checklist.md` item 7 puts the 5 µm inside the outline. If both apply, the keep-out is counted twice (about 0.035 mm²). Try d has 10–19 µm gaps |
| A2 | Guard strip between `r1_ctrl` and analog | 30 µm | **10 µm** | Try d: 7–10 µm strips, DRC and LVS clean. With the 11 µm core margin inside the macro and A1, digital cells are ≥ 26 µm from analog devices. Interface lines cross the strip straight (pin template, §3.2). Substrate coupling: not run |
| A2b | `SDI`/`EN` channel | 0.009 mm² | in the channels of each candidate | — |
| A3 | South trunk band | 30 µm | **40 µm**, y 331–371 | Try d: Metal4 `VSS`/`VDD`/`VDDA` trunks at y 332–360, a signal strip at y 361–371 (`VREF_BG`, comparator flags), blocks from y 371 |
| A4 | Chip decoupling in the window | `VDDA` 0.015 + `VDD` 0.010 | `VDD` 0. `VDDA` 0.0076 (C0–C3), or 0 (C5, C6: in the ring band) | `r1_ctrl` holds about 25 % fill and decap in its core. The try-d antenna decap row is in the north band |
| A5 | North routing band (new) | 0 (gate routes in the ring band) | **31.7 µm**, y 1237.3–1269, x 405–1195: 0.025 mm² | Try d routes pads 13–18, the PWM and gate lines and `FAULT_N` there, and puts the 34-cell decap row there. No macro fits under it |
| A6 | Pending blocks with no owner (new) | 0 | bias source 0.006, POR 0.003, PGA decoder in a channel | `r1_top` interface gaps 2, 3 and 5 |
| A7 | Ring over MIM blocks (new) | — | 0 area | Coordinator rule: TopMetal2 only over a MIM block, no via into it (try d, west columns) |
| A8 | Routing channels | inside A2 | drawn per interface (§3.2) | — |

Correction to S6: A5 alone takes 2.8 percentage points from the S6 margin. With the S6 block areas and A5, the
S6 margin of 10.6 % would have been about 7.8 %.

## 2. Candidate floorplans

Method. The generator [`S7_floorplan/gen_s7_floorplan.py`](S7_floorplan/gen_s7_floorplan.py) draws each candidate.
It checks each candidate for overlaps (with halos) and for rectangles outside the extended window. It also checks
that the digital macro is in the conservative window and that each channel has enough tracks for its nets.
It lists the ring ECO zones (MIM blocks under a TopMetal1 column) and the pad-to-pin Manhattan lengths.
Margin = 1 − required / window. Required = drawn rectangles + halos + shortfall. The window is the S6 extended
window, x and y 331–1269 µm = 0.8798 mm² at 1.6 mm (1.0774 mm² at 1.7 mm).
Run of record: `<G1_RESULTS_ROOT>/s7-floorplan/run-20261021-d` (`run.json`, one outline GDS per candidate,
`s7_floorplan.json`). The PNG files are in [`S7_floorplan/`](S7_floorplan/) (36–45 kB each).

| Candidate | Die | Topology | Re-shapes and new rules | Margin | Pictures |
| --- | --- | --- | --- | ---: | --- |
| C0 | 1.6 | try d (S6 F1) with the real macros | none | **does not fit**: `r1_safe` not placed (0.072 mm² outside) | [`s7_c0.png`](S7_floorplan/s7_c0.png) |
| C1 | 1.6 | try d; `r1_safe` in the east column | `r1_safe` re-shaped 175.2 × 409.6 | 3.79 % | [`s7_c1.png`](S7_floorplan/s7_c1.png) |
| C2 | 1.6 | `r1_ctrl` landscape 664 × 520 at the north; all analog except the AFE in one south band 326 µm high | `r1_ctrl` re-hardened in landscape; `r1_isense` 296.8 × 158.4 with inputs on a short edge; `r1_osc` pins north | 3.11 % | [`s7_c2.png`](S7_floorplan/s7_c2.png) |
| C3 | 1.6 | pin-map swap (S6 §5 item 6); AFE in the south-west corner next to the ADC; `bgr`, `t2f`, bias and POR above the AFE | `r1_safe` re-shaped (as C1); pin-map change | 4.17 % | [`s7_c3.png`](S7_floorplan/s7_c3.png) |
| **C5** | 1.6 | C3 + `VDDA` decap in the south ring band + `r1_osc` revision 2 | as C3 + ring-band decap + `r1_osc` ≤ 148.2 × 110.4 | **5.48 %** | [`s7_c5.png`](S7_floorplan/s7_c5.png) |
| C6 | 1.6 | C1 + the same two levers (no pin-map change) | as C1 + ring-band decap + `r1_osc` revision 2 | 5.09 % | [`s7_c6.png`](S7_floorplan/s7_c6.png) |
| C4 | 1.7 | try d, macros as laid out | none | **13.39 %** | [`s7_c4.png`](S7_floorplan/s7_c4.png) |

All drawn candidates: 0 overlaps, 0 rectangles outside the extended window, the digital macro inside the
conservative window, every channel within its track capacity.

Notes on the candidates:

- **Why `r1_safe` must change at 1.6 mm.** The AFE column (202.8 µm with halo) plus `r1_ctrl` (520) plus two
  strips leaves 175–195 µm for the east column. `r1_safe` is 249.3 µm wide. The south band under `r1_ctrl` is
  182 µm high. `r1_safe` needs 249.3 µm in its other orientation. So `r1_safe` fits nowhere as laid out.
  A `r1_ctrl` with another aspect does not help. At 456 × 757 µm the safe fits the east column, but the band
  under the macro falls to 89 µm and the ADC (0.080 mm²) fits nowhere (estimated shortfall ≈ 0.007 mm²). This
  was not drawn.
- **AFE orientation.** As laid out, the AFE is portrait (494.4 µm high). In C0, C1, C2, C4 and C6 its long side
  is along the west edge, next to pads 21–24. In C3 and C5 it is in the south-west corner. A landscape AFE in the
  south band was not drawn. Its inputs are on a long edge, so a rotation puts them toward the trunk or toward
  the digital macro. The encoder pads would then be 200–600 µm away. A re-pin of the AFE would be a second
  re-layout.
- **Digital macro in landscape (C2).** Rotating the t7 macro puts its north pins (gates, bus) on the west or the
  east edge. So landscape needs a re-harden at `DIE_AREA 0 0 664 520`. C2 puts every analog interface on the
  south edge of the macro, which is good. But the south band is full to 10.7 µm of the width. The margin is
  3.1 %. The `ISB_N` pad is 562 µm from the `r1_isense` input.
- **ADC shape (free parameter).** In C1, C3, C5 and C6 the ADC height is set by the macro bottom
  (1237.3 − 664 − 10 − 5 − 376 = 182.3 µm). So the slot is 439.0 × 182.3 µm. In C2 it is 245.2 × 326.3 µm,
  and in C4 it is 283.4 × 282.3 µm. The 439.0 × 182.3 slot also fits the C4 south band. Thus one ADC slot
  serves both dies.

## 3. Best candidate: C5 (1.6 mm)

### 3.1 Placement and area

| Item | Box (chip µm, lower left – upper right) | Note |
| --- | --- | --- |
| `r1_ctrl` | 543.8, 573.3 – 1063.8, 1237.3 | as t7 (520 × 664); pin template in 0.5 |
| `r1_afe` | 336.0, 400.0 – 528.8, 894.4 | as laid out; needs the pin-map swap |
| `r1_adc` (slot) | 556.0, 376.0 – 995.0, 558.3 | 439.0 × 182.3 |
| `r1_safe` (re-shaped) | 1088.8, 376.0 – 1264.0, 785.6 | 175.2 × 409.6, under the east TopMetal1 columns (no MIM, C7) |
| `r1_isense` | 1088.8, 795.8 – 1247.2, 1092.6 | working-tree size; east ring ECO |
| `r1_osc` (revision 2) | 1088.8, 1102.6 – 1237.0, 1213.0 | 148.2 × 110.4; MIM 3.4 µm clear of the east TopMetal1, no ECO |
| `r1_bgr`, `r1_t2f` | 336.0, 904.4 (R0); 336.0, 1108.7 (R0) | north-west pocket above the AFE |
| bias, POR (slots) | 442.0, 904.4 (86.8 × 69.7); 442.0, 1060.0 (55 × 55) | north-west pocket |
| `r1_gate_lv` | 440.0, 1196.0 | as try d |
| `r1_ls` × 4 (AFE gain) | in `chan_afe` | next to the AFE `c1..c4` pins |

| Area (1.6 mm, C5) | mm² |
| --- | ---: |
| `r1_ctrl` | 0.3453 |
| Analog blocks, slots and re-shapes (incl. bias 0.006, POR 0.003) | 0.348 |
| Halos (A1) | 0.035 |
| Strips (A2) | 0.012 |
| Channels (A8) | 0.029 |
| South trunk band (A3) | 0.0375 |
| North routing band (A5) | 0.025 |
| **Required** | **0.8317** |
| Extended window | 0.8798 |
| **Free (white)** | **0.0482 (margin 5.48 %)** |
| Headroom above the 5 % bar | 0.0041 |

The largest free piece is the south-east corner below `chan_se` (x 1000–1084, y 371–484, ≈ 0.0094 mm²).
The rest is in fragments: the north-west pocket, the north-band corners and the strip east of `r1_isense`.
Sensitivity: an ADC of 0.084 mm² (+5 % over the slot) takes C5 to 5.0 %. `r1_osc` at the revision-1 size
gives 5.25 %. If the ring-band decap is not possible, the decap returns to the window (C3 + osc revision 2:
≈ 4.4 %).

### 3.2 Channels (20 routed nets of try d and the pending nets of `r1_top/reports/connectivity.md`)

Routing pitch assumed: 0.84 µm for digital lines (2 × the Metal2–Metal4 minimum pitch, room for via landings),
2.0 µm per shielded analog line. "Pin template" means that `r1_ctrl` 0.5 puts each interface pin at the
coordinate of the analog pin it faces, so the line crosses the strip straight.

| Interface | Nets | Channel and width | Capacity | Condition |
| --- | ---: | --- | --- | --- |
| `r1_ctrl` S → ADC N (`adc_raw_a/b`, `adc_valid_a/b`, `adc_hold`, `adc_start`, `adc_sel`) | 35 | strip + halo, 15 µm | straight drops along 439 µm | **pin template**. Without it, a river route needs ≈ 29 µm |
| `r1_ctrl` E → `r1_safe` W (64 code bits after the `nP`/`nN` adders, 4 flags) | 68 | `chan_e`, 20 µm | facing span y 578–786 = 207 µm: 3.0 µm pitch | **pin template** and safe pins in the top 207 µm of its west edge. Without them ≈ 57 µm |
| `r1_ctrl` E → `r1_isense` W (`az_a/b`, `azh_a/b`) | 4 | `chan_e` | straight | — |
| `r1_ctrl` E → `r1_osc` W (`clk`, `osc_trim[4:0]`) | 6 | `chan_e` | straight | `osc_clk` moves to the west edge (revision 2) |
| AFE S → ADC W (`souts_p/n`, `soutc_p/n`, `vcm2`, shielded) | 5 | `chan_afe` 24 µm (y 371–395), `chan_wv` 17.2 µm | 14 / 8 | no digital crossing |
| `ana_ctrl[2:0]` → PGA decoder → 4 × `r1_ls` → AFE `c1..c4` | 7 | `chan_wv`, `chan_afe` | in the 14 tracks of `chan_afe` | decoder exists in no block (gap 5) |
| `r1_isense` W → ADC E (4 shielded outputs; `vref`, `vcm`, `ibias_a/b` in) | 8 | `chan_e` (10 tracks at 2 µm) → `chan_se` 79.7 µm | 10 / 39 | crosses the 68 ctrl → safe lines at right angles (Metal3 over Metal4) |
| `r1_bgr` → `r1_t2f` (`pbias`, `pcasc`, `vref`) | 3 | north-west pocket | local | — |
| `r1_bgr` `vref` → `r1_safe`, ADC `vref_in` | 2 | west band x 321–331, then the south strip y 361–371 (try d), ≈ 1 100 µm | — | **risk**: high-impedance node (90–200 kΩ). C1 and C6 keep `r1_bgr` in the south-west, so the route is ≈ 700 µm |
| bias → AFE `ib_*` (4), `r1_safe` `ibias_*` (4), `r1_isense` `ibias_a/b` (2) | 10 | `chan_wv`, south strip, `chan_e` | — | bias block pending |
| pads 23–24 (`SDI`, `EN` after the swap) → `r1_ctrl` W | 2 | straight east above the AFE, ≈ 200 µm | — | — |
| pads 13–18, PWM, `GATE_*`, `FAULT_N` (12) | 10 | north band (try d) | routed in try d | — |
| pads 8–11 → `r1_isense` E (Kelvin lines) | 4 | east band x 1269–1279 | 2 µm pitch | 57–278 µm (`ISA_P` 278) |
| `r1_t2f` `fout` → `r1_ctrl` `t2f_clk` | 1 | north-west pocket → `r1_ctrl` W | — | pin moves from S to W in 0.5 |
| `r1_t2f` `en`, `mode` (gap 4); `por_n` (gap 2) | 3 | north-west pocket | — | sources pending |
| `VREF_BG`, `CMP_*`, `T2F_*` of try d | 7 | change with the new placement | — | rerouted by T8 |

Pad routes (Manhattan, IO inner edge to block pin): `SIN_P` 26, `SIN_N` 162, `COS_P` 26, `COS_N` 162 µm
(after the pin-map swap; C1/C6 without the swap: 71 and 211 µm). `ISA_P` 278, `ISA_N` 142, `ISB_P` 143, `ISB_N` 57 µm.

### 3.3 Ring and trunk path

1. Core ring as try d: outer conductor `VSS`, inner `VDD`; `r1_ctrl` TopMetal1 stripes join the north TopMetal2 rows.
2. West TopMetal1 columns: cut at y 395–899.4 over the AFE (outline ± 5 µm). TopMetal2 strips run at y 380–914.4.
   TopVia2 arrays are at y 380–395 and 899.4–914.4 only. This is the try-d ECO moved from y 645–1148.
3. East TopMetal1 columns: cut at y 790.8–1097.6 over `r1_isense` (MIM, it extends 6.8 µm under the column).
   The same TopMetal2 rule applies. `r1_osc` revision 2 at 148.2 µm needs no cut. At its revision-1 width it
   needs a cut at y 1097.6–1226. `r1_safe` (no MIM) sits under the columns as in try d.
4. South: Metal4 trunks `VSS` y 332–340, `VDD` 343–349, `VDDA` 352–360 (try d). The `VDDA` decoupling (C5 lever)
   is MIM (Metal5 bottom plate, TopMetal1 top plate) over the trunks at x 371–1238.4, y 332–360. Under the
   TopMetal2 rows, it has no TopVia2. A thick-oxide MOS capacitor is on Metal1/Metal2 under it. MIM: 0.024 mm²
   ≈ 36 pF at 1.5 fF/µm² (S4). MOS: estimated. The total is in the S6 range of 60–130 pF (estimated). This rule
   is new. The MIM top plate must stay ≥ 1.64 µm (TM1.b) from the ring TopMetal1. DRC: not run.
5. `VDDA` from pad 7 through the feed at x 1272–1279 (try d). `VDD` and `VSS` straps as try d.

### 3.4 Re-shapes

| Block | Change | Box | Layout only? |
| --- | --- | --- | --- |
| `r1_safe` | re-floorplan of the same netlist | ≤ 175.2 × 409.6 µm (0.0718 mm²) | **yes** (generator layout; DRC, LVS, PEX and the post-layout code-44 check rerun). A shrink to 0.06 mm² (T4 options: one mux column, narrower level shifters) is not required. It would add 1.3 points |
| `r1_ctrl` 0.5 | pin template (south: ADC; east: safe, isense, osc; west: `sdi`, `en_pad`, `ana_ctrl`, `t2f_clk`) | 520 × 664 unchanged | re-harden (0.5 is re-hardened anyway for the safe adders, gap 1). Area risk: 799 µm² headroom to 240 000 µm² |
| `r1_osc` revision 2 | `osc_clk` on the west edge; ≤ 148.2 × 110.4 preferred | ≤ 154.4 × 118.4 allowed (5.25 %) | yes |
| `r1_isense` | none; working-tree size and pins match the slot | 158.4 × 296.8 | — |
| `r1_afe` | **none** | 192.8 × 494.4 | — (the pin-map swap moves it) |
| pin map | west side, bottom to top: `SIN_P`, `SIN_N`, `COS_P`, `COS_N`, `SDI`, `EN` (S6 §5 item 6) | — | spec §3, T6 ring and bond-plan rerun. Without it, use C6 (5.09 %) |

## 4. 1.7 mm floorplan (C4)

C4 keeps the try-d topology. All macros are used as laid out. `r1_safe` keeps its native pins (codes on the top
edge into a 61 µm channel, `chan_safe`, 72 tracks for 68 nets). No pin template is necessary. `r1_osc` has the
revision-1 size. The `VDDA` decap stays in the window.

| Item (1.7 mm, C4) | Value |
| --- | --- |
| Die, extended window | 1700 µm; 1038 × 1038 µm = 1.0774 mm² (ring offsets as at 1.6 mm, pads at pitch 140 µm, centred: assumed) |
| Required | 0.9332 mm² |
| Margin | **13.39 %** (0.144 mm² free) |
| ADC | slot 283.4 × 282.3 drawn; the 439.0 × 182.3 slot also fits |
| Ring ECO | west columns over the AFE only |
| Pad routes | `SIN`/`COS` 36 and 172 µm; `ISA`/`ISB` 132–268 µm |
| Cost | die area 2.89 mm² against 2.56 mm² (+12.9 %); T6 ring and bond-plan rerun |

The escalation trigger of S6 (analog sum > 0.30 mm²) applies as written: 0.342 mm².

## 5. Recommendation for D10 and the hard slots

1. **Keep the 1.6 mm die, with floorplan C5 as the floorplan of record, as a gated option.** The 1.6 mm option
   meets the 5 % bar with routable channels only in C5 (5.48 %) and C6 (5.09 %). Both need a pin template and
   the ring-band decap.
2. **Replace the S6 trigger "analog sum > 0.30 mm²" with the gates below.** That trigger was a proxy for the S6
   area budget. It has tripped (0.342 mm²). S7 measures the fit directly. This is a change of a rule that was
   agreed in advance. The coordinator records it as a D10 amendment, and it stays reversible.
3. **Escalate to 1.7 mm (C4, 13.4 %) at the first missed gate.** Decide at the latest when the ADC layout is
   delivered, or at P3 entry, whichever comes first.

| Gate | Pass condition | If missed |
| --- | --- | --- |
| G1 | `r1_adc` layout ≤ 439.0 × 182.3 µm with the pin sides below | 1.7 mm |
| G2 | `r1_safe` re-layout ≤ 175.2 × 409.6 µm, codes and flags on the west edge in its top 207 µm | 1.7 mm |
| G3 | `r1_ctrl` 0.5 (with the safe adders) closes at ≤ 240 000 µm² placed, 42 MHz, three corners, in 520 × 664 with the pin template | 1.7 mm (S6 second trigger) |
| G4 | Ring-band `VDDA` decap (MIM over the south trunks) passes main, maximal and antenna DRC in the `r1_top` assembly | 1.7 mm (without it, 1.6 mm is ≈ 4.4 %) |
| G5 | `r1_isense` of record ≤ 158.4 × 296.8 µm | 1.7 mm |
| G6 | `r1_osc` revision 2 ≤ 154.4 × 118.4 µm (≤ 148.2 × 110.4 preferred) | 1.7 mm |
| G7 | Pin-map swap accepted (spec §3, T6, bond plan) | not a die gate: use C6 (5.09 %) |

### Hard slots for the pending macros (chip coordinates of C5; prBoundary = slot; the top level keeps 5 µm outside)

| Block | Box (µm) | Origin (µm) | Pin sides | Other rules |
| --- | --- | --- | --- | --- |
| `r1_adc` | **≤ 439.0 × 182.3** (0.080 mm²) | 556.0, 376.0 | N: 35 digital pins, Metal3, at the x coordinates of the `r1_ctrl` 0.5 template (pitch ≥ 2 µm). W: `ain_sin_p/n`, `ain_cos_p/n` (from `chan_wv`). E: `ain_isa_p/n`, `ain_isb_p/n` in the upper half (y ≥ 484, from `chan_se`). S: `vdda`, `vdd`, `vss`, `vref_in` | MIM allowed (no ring above). The same slot fits the 1.7 mm floorplan |
| `r1_osc` revision 2 | **≤ 148.2 × 110.4** (allowed ≤ 154.4 × 118.4) | 1088.8, 1102.6 | W: `osc_clk`, `trim0..4`, `en`. N: `vdd`. S: `vss` | at ≤ 148.2 µm wide, no ring ECO |
| `r1_isense` | **≤ 158.4 × 296.8** | 1088.8, 795.8 | E: `isa_p/n` at local y ≈ 41–44, `isb_p/n` at ≈ 186–189. W: outputs, `az_*`, `azh_*`, `ibias_*`, `vref`, `vcm`. S: supplies | east ring ECO (TopMetal2 only) over it. At ≤ 149.9 µm wide, no ECO |
| `r1_safe` (re-shape) | **≤ 175.2 × 409.6** | 1088.8, 376.0 | W: 64 code bits and 4 flags in the top 207 µm; `ibias_*` W. S: `vdda`, `vdd`, `vss`, `vref` | Metal1–Metal4 only (it sits under the east ring columns) |
| `r1_afe` | no re-shape: 192.8 × 494.4 as laid out | 336.0, 400.0 (C5) or 336.0, 620.0 (C6) | as laid out | west ring ECO moves with it |
| bias source, POR | 87 × 70 and 55 × 55 (assumed) | 442.0, 904.4 and 442.0, 1060.0 | toward `chan_wv` and the west edge of `r1_ctrl` | no block owner yet |

## 6. Status of checks

| Check | Status |
| --- | --- |
| Macro sizes collected (laid out, working tree, slots) | passed (§1.1) |
| Overlap, window and conservative-window checks of all drawn candidates | passed: 0 overlaps, 0 outside, digital inside (run d) |
| Channel track capacity against the net count (drawn channels) | passed for all channels in all candidates (run d) |
| Pin-template feasibility in LibreLane (exact pin coordinates) | not run |
| `r1_ctrl` 0.5 area with the safe adders | not run |
| Ring-band decap: DRC, capacitance extraction | not run |
| Ring ECO on the east columns | not run |
| Routing of any pending net | not run |
| IR drop and EM of trunks and ring | not run |
| Substrate coupling across the 10 µm strip | not run |
| 1.7 mm ring build and bond plan | not run |

## Built against

| Item | Value | How established |
| --- | --- | --- |
| KLayout | 0.30.9 (`klayout.db`, `klayout.lay`) | `klayout -v` in the container |
| Container | `tapeoutbench-eda:latest`, `sha256:ddeb6957…` | `flow/run.sh` identity check |
| PDK | IHP-Open-PDK `84374023ee8b4b126bebbba67fcbada0a9c0ff0b` (checked; no PDK layers used) | `flow/run.sh` commit check |
| ngspice, xschem, LibreLane, CACE | not used | — |
| CPUs | 116–119 (`G1_CPUSET`) | command line in `run.json` |

Runs: `<G1_RESULTS_ROOT>/s7-floorplan/run-20261021-d` (of record); `-a`, `-b`, `-c` superseded, each with a
`run.json` that gives the reason.

## Failures and mistakes

| # | What happened | Class | Disposition |
| --- | --- | --- | --- |
| 1 | The hand check before the first run found six geometry errors: halo overlaps of 0.04 and 0.1 µm (C2), POR and `r1_gate_lv` halos outside the window (C2), `r1_t2f` in the guard strip (C3), and two channels over each other (C4) | arithmetic | fixed before run a |
| 2 | Run a: `chan_safe` overlapped the `r1_safe` halo by 0.01 µm (C4) | arithmetic | found by the overlap check; fixed in run b |
| 3 | Run b: the lever variants counted a false `r1_osc` shortfall of 0.0019 mm², because the need table kept the revision-1 area | tooling | per-candidate need override; run c |
| 4 | Run c: the C0 picture showed "margin 4.5 %" for a candidate that does not fit (area margin with the safe counted as a shortfall) | reporting | the label says "does not fit"; run d of record |
| 5 | The run-c stdout was first written to the study root of the results directory, not into the run directory | housekeeping | moved into the run directory |
| 6 | The run-d stdout went through a temporary file under `/tmp` before it was copied to the run directory | process-hygiene | copied, `/tmp` file deleted; nothing remains only in `/tmp` |
| 7 | The link table in `s7_floorplan.json` for C3 and C5 still names `chan_sw` for the AFE gain and bias lines (from C1). The correct channels are `chan_afe` and `chan_wv` | reporting | corrected in §3.2. JSON not regenerated (text only, no check depends on it) |
| 8 | The brief gave the ADC as 0.068 mm² and `r1_gate_lv` as three 28 × 28 µm instances. The records give 0.0755 mm² (revision 5) and one instance with three channels | record inconsistency | the records are used (§1.1) |
| 9 | S6 A1 (keep-out outside) and integration checklist item 7 (keep-out inside the outline) count the same 5 µm twice if both apply | spec-ambiguity | S7 rule: outside only (§1.2); the checklist is not edited (outside this study) |
| 10 | S6 put the gate routes in the ring band at zero window area. Try d needs a 31.7 µm north band. The S6 margin was about 2.8 points too high | estimation (S6) | A5 added (§1.2) |
| 11 | The S6 escalation trigger (analog sum > 0.30 mm²) tripped before any S7 check. This study recommends replacing it instead of applying it | assumption (recorded for the owner) | §5 item 2; the 1.7 mm floorplan is drawn and ready (C4) |

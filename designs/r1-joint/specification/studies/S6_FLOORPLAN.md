# S6 — floorplan and area closure (2026-10-21)

Study by an agent (Opus 5.5). Nothing in this study is laid out. The floorplans are rectangles only.
Labels: **hardened** (LibreLane run with sign-off), **placed** (a laid-out G1 cell or macro reused unchanged),
**estimated** (device area × layout factor, no layout), **assumed** (a choice of this study, with a reason).

Question: do the R1 blocks fit the 1.414 mm die (G1 ring) or a 1.6 mm die with ≥ 10 % margin? Which cuts are
necessary? What size must the digital macro have (decision D10)?

Answer in short:

1. **1.414 mm does not fit.** With the five recommended cuts, 0.205 mm² stays outside the die (margin −31 %).
   With every cut on the list, including the functional cuts, the total is 0.62 mm² against a 0.566 mm² window.
2. **1.6 mm fits with 10.6 % margin**, but only with five cuts: digital at 75 % (C1), digital RTL trims to
   ≤ 240 000 µm² placed (C2), ADC reference decoupling on a MOS capacitor (C5), AFE MIM stacked over the
   resistors (C6), and analog macros under the core power ring as on G1 (C7). No functional cut is necessary.
3. **D10 recommendation: 1.6 mm die.** `r1_ctrl` revision 0.4 gets a hard macro size of **520 × 664 µm**
   (`DIE_AREA 0 0 520 664`, portrait, H/W 1.28) and a final standard-cell utilisation of **≤ 75 %**. This
   means ≤ 240 000 µm² of placed standard-cell area (t6: 269 618 µm²). Escalation rule: go to 1.7 mm if
   the laid-out analog sum exceeds 0.30 mm² or the macro cannot close at 75 %.

## 1. Block area table

Source: block READMEs as of 2026-10-20 (revision named). All areas are in mm².

| Block | Revision | Area (mm²) | State | Basis |
| --- | --- | --- | --- | --- |
| `r1_ctrl` (digital) | 0.3, run `r1ctrl_ll_20261020_t6` | **0.4772** macro (690.8 µm square); standard cells 0.2696 placed (60.2 %); fill and decap 0.1784; synthesis 0.2454 | hardened | `blocks/r1_ctrl/reports/ll_t6.md`; fill area from the run `metrics.json` (`design__instance__area__class:fill_cell` 178 385 µm²) |
| `r1_afe` | D | 0.099 (MOS 0.029, `rppd` 0.033, MIM 0.038) | estimated | `blocks/r1_afe/README.md` § Area and current (revision D) |
| `r1_adc` | 3 | 0.070 (CDAC 0.0185, comparators 0.0025, switches and SAR 0.012, `r1_refbuf3` with 44 pF MIM 0.037) | estimated | `blocks/r1_adc/README.md` § Area and power (revision 3). Revision 4 is in progress and is not read here |
| `r1_osc` | r1 | 0.018 (0.012 with a tighter layout) | estimated | `blocks/r1_osc/README.md` § Area and current |
| `r1_bgr` | r1 | 0.016–0.020 | estimated | `blocks/r1_bgr/README.md` § Area and current |
| `r1_isense` × 2 | — | 0.050–0.066 (device 0.0083 per channel × 3–4) | estimated | `blocks/r1_isense/README.md` § Area |
| `r1_safe` | 3 | 0.05–0.06 (device 0.020; 4 080 mux switches) | estimated | `blocks/r1_safe/README.md` § Area |
| `r1_t2f` | G1 revision 2 | 0.0094 (92 × 102.6 µm) | placed (G1 macro) | `blocks/r1_t2f/README.md` |
| `r1_gate` | variant L | ≈ 0 analog (the AND sits in the `r1_ctrl` RTL; the pad has its own shifter); variant H 0.0011–0.0057 | estimated | `blocks/r1_gate/README.md` § Area |
| `r1_ls` | — | 0.0014 (6 × `g1_ls_up` at 20 µm pitch) | placed (G1 cell) | `blocks/r1_ls/README.md` § Area |
| **Analog sum** | | **0.308 / 0.329 / 0.350** (low / central / high) | estimated | |

The central analog value uses the middle of each range and 0.018 for the oscillator.

Two records are stale. PLAN.md §2a shows `r1_safe` at 0.025 mm² (revision 2). Revision 3 gives 0.05–0.06.
The specification "Area" row lists isense, safe, BGR, T2F and gates as pending. This table replaces both.

### Allowances (assumed, with the reason)

The numbers are from the 1.6 mm drawing (§2). The 1.414 mm values are in brackets.

| # | Allowance | mm² | Reason |
| --- | --- | --- | --- |
| A1 | 5 µm keep-out on each side of each analog block (10 µm between neighbours) | 0.032 (0.028) | Room for a p+ tap ring per block and n-well spacing. G1 r4 has 10–16 µm gaps between analog macros (measured, run `g1check`) |
| A2 | Guard strip, 30 µm, on three sides of the digital macro and above `r1_isense_b` | 0.064 (0.041) | The macro has its own 10.7 µm core margin (t6: die 690.8 µm, core 669.3 µm). With the strip, digital cells are ≈ 40 µm from analog devices. The strip holds a p+ substrate ring and an n-well ring. About 80 interface lines cross it (ADC 2 × 14 raw bits and strobes, 4 comparator flags and 4 × 6 calibration bits, AFE gain, OSC trim and clock, T2F, isense auto-zero) |
| A2b | Digital channel for `SDI` and `EN` from pads 19–20 | 0.009 (0.011) | The two pads sit below the AFE on the west side (pin map). The channel continues the guard strip to the west edge |
| A3 | `VDDA` and analog ground trunk, 30 µm, from pad 7 along the south | 0.029 (0.021) | One `VDDA` pad carries ≈ 4.5 mA (specification, Power row). IR drop was not computed |
| A4 | Chip-level decoupling outside the macros: `VDDA` 0.015, `VDD` 0.010 | 0.025 (0.013) | `VDDA`: ≈ 60–130 pF with MIM (1.5 fF/µm², S4) stacked over a thick-oxide MOS capacitor (density assumed). `VDD` decoupling for the digital is mostly inside the macro: at 75 % the fill and decap share is ≈ 0.08 mm². The core decap also gives the gate load that clears the 12 antenna markers of the empty ring (`r1_padring` README) |
| — | Gate pad routes (pads 13–15) | 0 | They run in the core-ring band on Metal2–4 under the TopMetal ring, as on G1 |

The total allowance is 0.159 mm² at 1.6 mm (18 % of the window) and 0.115 mm² at 1.414 mm.

## 2. Floorplans

The run of record is `<G1_RESULTS_ROOT>/s6-floorplan/run-20261021-b` (`run.json`, two GDS files with
rectangles only, JSON with every rectangle and pad). The generator is
[`S6_floorplan/gen_s6_floorplan.py`](S6_floorplan/gen_s6_floorplan.py). It checks for overlaps and for
rectangles outside the window. It computes the shortfall of each block against its required area.
The images are [`S6_floorplan/s6_floorplan_1414.png`](S6_floorplan/s6_floorplan_1414.png) and
[`S6_floorplan/s6_floorplan_1600.png`](S6_floorplan/s6_floorplan_1600.png).

### Windows

| Die | IO row inner edge | Conservative window (inside the core ring) | Extended window (macros under the ring, G1 practice) |
| --- | --- | --- | --- |
| 1414 µm | 321 µm from the edge | x 361.8–1054.4, y 362.2–1051.3 µm: 692.6 × 689.1 = **0.477 mm²** (padring record) | 331–1083 µm: 752 × 752 = **0.566 mm²** |
| 1600 µm | 321 µm (same 180 µm pad depth, same 141 µm seal and bondpad band) | x 361.8–1240.4, y 362.2–1237.3 µm: 878.6 × 875.1 = **0.769 mm²** | 331–1269 µm: 938 × 938 = **0.880 mm²** |

The extended window starts 331 µm from the edge. That is where G1 r4 put its analog macros:
`g1_sense` bottom at y = 331.7 µm and `g1_bgr` left at x = 331.0 µm. The `g1_bgr` top is at 1083.7 µm
(run `g1check`, read from the G1 r4 GDS `225d0b53…`). The digital macro stays inside the conservative window.
Its power grid can then reach the ring without a conflict.

For the 1.6 mm ring, the same 24 cells stay in the same order. The pitch goes from 112 to 140 µm, centred on each
side, so the pad centres are at 450, 590, 730, 870, 1010 and 1150 µm. The corners, the 180 µm IO depth and
the bondpad band do not change. Only the filler cells increase. T6 must rebuild the ring and rerun the bond
plan (not run).

### Placement rule

- Digital: one rectangle at the north. It touches the gate pads (13–15), the bus pads (16–18) and,
  through the north-east corner, `FAULT_N` (12).
- Analog: a U shape on the west, south and east sides, separated from the digital by the guard strip.
  - West column: `r1_afe` next to `SIN`/`COS` (21–24), with the four AFE gain level shifters below it.
  - East column: `r1_safe`, `r1_isense_a` next to `ISA` (8–9) and `r1_isense_b` next to `ISB` (10–11).
  - South band: `r1_adc` below the AFE, then `r1_bgr`, `VDDA` decoupling, and `r1_t2f` with its two
    level shifters. The `VDDA` trunk runs from pad 7 along the south edge.
- `r1_osc` is in the north-east corner, on the digital side of the guard strip. It is a clock source on
  `VDD` and feeds only the digital.
- `SDI` and `EN` (19–20) reach the digital through a channel under the AFE. The AFE-to-ADC lines cross
  this channel once, with a shield.

### (b) 1.6 mm die: fits (drawn to scale in `s6_floorplan_1600.png`)

```
 y=1269 +--------------------------------------------------------------+   pads (north): 13 GATE_A 14 GATE_B
        |  (gate routes in the ring band)                               |   15 GATE_C 16 CS_N 17 MA 18 SLO
 1237   |        |s|                                    |s| decap VDD |
        | r1_afe |t|                                    |t| r1_osc    |  <- 12 FAULT_N (1150)
 24 COS_N        |r|          r1_ctrl (digital)         |r|-----------|  strip_ne
 23 COS_P 140 x  |i|          520 x 664 um              |i| isense_b  |  <- 11 ISB_N, 10 ISB_P
 22 SIN_N  493   |p|          0.345 mm2                 |p| 180 x 161 |
 21 SIN_P        |_|          75 % at 240 000 um2       |_| isense_a  |  <- 9 ISA_N, 8 ISA_P
        |        |w|                                    |e| 180 x 161 |
 20 EN  | ls_afe |-|------------- strip_s --------------|-|  r1_safe  |
 19 SDI | chan_sw (SDI/EN)                                 | 180 x 306 |  <- 7 VDDA
        | r1_adc 291 x 172 | r1_bgr | decap VDDA | r1_t2f  |           |
  331   +===================== VDDA / AVSS trunk ======================+
        x=331                                                     x=1269
                 pads (south): 1 VDD 2 VSS 3 IOVDD 4 IOVSS 5 VSS 6 IOVSS
```

| Item (1.6 mm, run b) | mm² |
| --- | --- |
| Digital macro (C1 + C2) | 0.345 |
| Analog blocks as drawn (after C5, C6) | 0.283 |
| Strips, channels, trunks, decoupling (A2–A4) | 0.127 |
| Keep-out (A1) | 0.032 |
| **Required** | **0.787** |
| Extended window | 0.880 → **margin 10.6 %** |
| Conservative window (without C7) | 0.769 → margin −2.3 % (does not fit) |

### (a) 1.414 mm die: does not fit (drawn to scale in `s6_floorplan_1414.png`)

The same topology is drawn in the extended window with the same five cuts. The digital macro gets only
362 × 478 µm = 0.173 mm² of the 0.345 mm² it needs. `r1_osc` does not fit. `r1_safe` is 0.013 mm² short.
The red square beside the die in the image is the shortfall.

```
 y=1083 +----------------------------------------------+
 24 COS_N        |s|                        |s| r1_safe  |  <- 12 FAULT_N
 23 COS_P r1_afe |t|  r1_ctrl: only         |t| (short)  |
 22 SIN_N        |r|  362 x 478 um free     |r| isense_b |  <- 11, 10
 21 SIN_P        |w|  (needs 520 x 664)     |e| isense_a |  <- 9, 8
 20 EN  chan_sw  |-|-------- strip_s -------|-| decap    |  <- 7 VDDA
 19 SDI | r1_adc | r1_bgr | r1_t2f |                     |
  331   +============ VDDA trunk =======================+
          not placed: r1_osc 0.018, r1_ctrl 0.172, r1_safe 0.013, decap 0.002 = 0.205 mm2
```

| Item (1.414 mm, run b) | mm² |
| --- | --- |
| Required (same blocks and allowances) | 0.741 |
| Extended window | 0.566 → margin −31 % |
| Conservative window | 0.477 → margin −55 % |

## 3. Cut list for 1.414 mm

The cuts are in the order to take them. The saving is the reduction of the required area or the increase of the window.
"Revision" names the block revision that must carry the cut.

| # | Cut | Saving (mm²) | Revision needed | Risk |
| --- | --- | --- | --- | --- |
| C1 | Digital final utilisation 60.2 → 75 % (same RTL): 269 618 µm² in a 359 500 µm² core, 0.477 → 0.386 mm² | 0.092 | `r1_ctrl` 0.4 hardening | medium: more timing-repair buffers at 42 MHz. The t1 trial reached 82.6 % after CTS but stopped in routing (latch file, 2 h limit). t6 grew from 55 to 60.2 % during the flow |
| C2 | Register and interface trims: placed standard cells ≤ 240 000 µm² (synthesis ≈ 218 000). Listed in the `r1_ctrl` README: 12–13-bit PWM words and relative counters (−10 to −15 k synthesis), register widths, `TEST_POS` and diagnostic counters (−5 to −8 k), fewer writable words. Not recommended: shared `r1_adcw` (frame +4 ticks, breaks the D18 22-tick frame), latch weight words (≈ −14 k, the latch file failed slow-corner STA at −2.10 ns) | 0.040 (0.386 → 0.345) | `r1_ctrl` 0.4 RTL, register map 0.4, full regression | medium: the register map changes; the 250 kHz proof stays valid if the frame does not change |
| C3 | Cut 3 in full: PWM generator back to pass-through (`r1_gate` ≈ 32 k synthesis, with `r1_adcw` 6 k) | ≈ 0.03 | `r1_ctrl` 0.4, specification open item 6 reversed | high: D18 samples the currents at the centre-of-on-time strobe of the on-chip PWM. No pin is free for an external strobe. Not recommended |
| C4 | I²t winding model to the host (part of `r1_safe` RTL, 23 k) | ≈ 0.01 (assumed −6 to −8 k synthesis) | `r1_ctrl` 0.4, specification `r1_safe` row | high: the safety channel then depends on the host for thermal overload. Not recommended |
| C5 | ADC reference decoupling (44 pF, 29 400 µm² MIM + 2 500 µm² gate capacitor) as MIM stacked over a thin-oxide MOS capacitor | 0.020 (0.070 → 0.050) | `r1_adc` revision 4 if not frozen, else revision 5 | medium: MOS capacitor ESR and gate leakage at 125 °C. Reference settling (R2-4) already fails, so it must be simulated again with the MOS model |
| C6 | AFE layout rule: MIM capacitors (0.038 mm² with overhead) stacked over the `rppd` arrays and MOS devices | 0.030 (0.099 → 0.069) | `r1_afe` revision E (layout) | medium: resistor-to-MIM bottom-plate coupling moves the anti-alias poles (1 % matching), so PEX is mandatory. Metal5 is blocked under the MIM |
| C7 | Analog macros under the core power ring (G1 r4 practice, measured) | +0.088 window (+0.111 at 1.6 mm) | integration rule; analog macros use no TopMetal1/2 in the ring band | low to medium: proven on G1. Pad signals must cross the band on Metal2–4 |
| C8 | Cut 4: one current channel (`r1_isense` − 0.029, `r1_safe` half ≈ − 0.028) | ≈ 0.057 | specification change (single-phase monitoring) | high: function loss. Not recommended |
| C9 | Digital 75 → 80 % | ≈ 0.017 | `r1_ctrl` 0.4 | high: routing at 42 MHz. Not recommended |
| C10 | `r1_osc` tighter layout (README: ≈ 0.012) | 0.006 | `r1_osc` layout | low |

Result for 1.414 mm:

| Cut set | Required (mm²) | Window (mm²) | Margin |
| --- | --- | --- | --- |
| C1, C2, C5, C6, C7 (drawn, run b) | 0.741 | 0.566 | −31 % |
| all cuts C1–C10 (arithmetic from the drawing) | 0.621 | 0.566 | −10 % |
| needed for 10 % margin | ≤ 0.509 | 0.566 | — |

**The total does not fit 1.414 mm, even with every cut and no margin.** The analog blocks and allowances alone
take ≈ 0.40 mm² of the 0.566 mm² window. The smallest credible digital macro (C1–C4 and C9: ≈ 210 000 µm² placed at
80 %) is ≈ 0.285 mm².

## 4. 1.6 mm: margin and necessary cuts

| Variant (1.6 mm) | Required (mm²) | Margin, extended window 0.880 | Margin, conservative window 0.769 |
| --- | --- | --- | --- |
| No cuts (digital as hardened, 0.477) | ≈ 0.97 | −10 % | −26 % |
| C1 only (extended column assumes C7) | ≈ 0.877 | 0.3 % | −14 % |
| C1, C2, C7 | 0.837 | 4.9 % | — |
| C1, C2, C5, C7 | 0.817 | 7.1 % | — |
| C1, C2, C6, C7 | 0.807 | 8.3 % | — |
| **C1, C2, C5, C6, C7 (drawn, run b)** | **0.787** | **10.6 %** | −2.3 % |
| same, analog at the high estimate (+0.021) | 0.808 | 8.2 % | — |

Rows other than run b are the run-b value plus or minus the stated area. The drawing has 0.125 mm² of white space
for this.

Cuts are still necessary at 1.6 mm: C1, C2, C5, C6 and C7. No functional cut (C3, C4, C8) is necessary.
The 10.6 % margin (0.093 mm²) covers an error of about +30 % on the analog blocks (0.283 mm² as drawn). The analog numbers
are not laid out. `r1_safe` doubled from revision 2 to revision 3, and `r1_afe` grew from 0.084 to 0.099 mm². So the margin
is thin.

A 1.7 mm die (window 0.954 mm² conservative, 1.077 mm² extended) would give ≈ 20 % margin (extended window) or ≈ 10 % (conservative) with C1 and C2 only
(arithmetic from run b with longer strips, not drawn). The cost is +13 % die area (2.89 against 2.56 mm²).

## 5. Recommendation for D10

1. **Take the 1.6 mm die (2.56 mm²).** 1.414 mm cannot close (§3). 1.5 mm (extended window 0.702 mm²) cannot
   close either, because the 1.6 mm cut set needs 0.787 mm².
2. **Take cuts C1, C2, C5, C6 and C7.** Do not take C3, C4, C8 or C9.
3. **Hard constraint for `r1_ctrl` revision 0.4:**

   | Item | Value |
   | --- | --- |
   | `DIE_AREA` | `0 0 520 664` (µm), 0.3453 mm², portrait, H/W = 1.28 |
   | Core (t6 margins, 10.7 µm per side) | ≈ 498.6 × 642.6 µm = 320 400 µm² |
   | Final standard-cell utilisation | ≤ 75 %, so ≤ 240 000 µm² placed standard cells (t6: 269 618) |
   | Synthesis target (t6 placed/synthesis ratio 1.099) | ≤ 218 000 µm² (0.3: 245 386) |
   | Timing | 42 MHz, 3 corners, as in t6 |
   | Pin sides | north: gate and bus pads. East: `r1_safe`, `r1_isense`, `FAULT_N`, `r1_osc`. South: `r1_adc`, `r1_bgr`, `r1_t2f`. West: AFE gain controls; `SDI`/`EN` at the south-west corner |
   | Power | the macro grid stays inside the conservative window and connects to the core ring at the north edge |

4. **Block requirements:** `r1_adc` ≤ 0.050 mm² (C5). `r1_afe` ≤ 0.069 mm² (C6). The rest of the analog
   stays at or below the central values in §1.
5. **Escalation gate (floorplan gate, P3 entry):** go to 1.7 mm if the laid-out analog sum exceeds 0.30 mm².
   Also go to 1.7 mm if `r1_ctrl` 0.4 cannot close at 75 % in 520 × 664 µm. The T6 ring build is scripted, so
   a die change before integration costs one ring run and one bond-plan run.
6. **Optional pin-map change for the 1.6 mm ring (recommended, not applied).** On the west side, put the
   encoder pads at the bottom and `SDI`/`EN` at the top (pads 19–22 `SIN_P`, `SIN_N`, `COS_P`, `COS_N`;
   23 `SDI`; 24 `EN`). The AFE then sits next to the ADC. The `SDI`/`EN` channel under the AFE (A2b) goes
   away, and the AFE-to-ADC lines no longer cross a digital channel. This changes specification §3 and the bond plan.
7. Owner confirmation is still needed for the die area above the 2 mm² budget (as in PLAN.md §2a).

## 6. Status of checks

| Check | Status |
| --- | --- |
| Block areas collected from the records | passed (§1) |
| Overlap and window check of the drawn rectangles (1.414 and 1.6) | passed, 0 overlaps, 0 rectangles outside the extended window (run b) |
| G1 r4 macro positions (under-ring placement) | passed (run `g1check`) |
| Layout of any analog block | not run |
| Digital macro at 520 × 664 µm, 75 % | not run (`r1_ctrl` 0.4) |
| 1.6 mm ring build, DRC, bond plan | not run (T6) |
| IR drop of the `VDDA` trunk and the core ring | not run |
| Substrate coupling digital → AFE across the guard strip | not run |
| QFN24 paddle size for a 1.6 mm die | not run |

## Built against

| Item | Value | How established |
| --- | --- | --- |
| KLayout | 0.30.9 (Python modules `klayout.db`, `klayout.lay`) | `klayout -v` in the container |
| Container | `tapeoutbench-eda:latest`, `sha256:ddeb6957…` | `flow/run.sh` identity check |
| PDK | IHP-Open-PDK `84374023ee8b4b126bebbba67fcbada0a9c0ff0b` (only for the decap cell data; the floorplan uses no PDK layers) | `/foss/pdks/ihp-sg13g2/COMMIT` |
| ngspice, xschem, LibreLane, CACE | not used | — |
| CPUs | 100–102 (`G1_CPUSET`) | command lines in `run.json` |

Runs: `<G1_RESULTS_ROOT>/s6-floorplan/run-20261021-b` (of record), `run-20261021-a` (superseded),
`g1check`. Each run has a `run.json`.

## Failures and mistakes

| # | What happened | Class | Disposition |
| --- | --- | --- | --- |
| 1 | The first `flow/run.sh` call passed the whole command as one quoted string, so `exec` did not find it | tooling | rerun with `sh -c` |
| 2 | The G1 check script was first written under `/tmp`. The container mounts only the repository and the results root, so the script was not found | environment | moved to `<G1_RESULTS_ROOT>/s6-floorplan/g1check`; the `/tmp` copy deleted |
| 3 | The G1 check script was copied for a moment to the top of the results root instead of the study directory | housekeeping | moved within one minute |
| 4 | Run a counted the guard-strip corners twice (two overlaps). The ADC rectangle was 0.0004 mm² short | arithmetic | found by the overlap and shortfall checks; fixed in run b |
| 5 | Run a used 40 µm strips and a dedicated window channel for the gate routes, which gave a 5.4 % margin at 1.6 mm. Run b uses 30 µm strips (with the 10.7 µm macro margin) and routes the gates in the ring band (G1 practice): 10.6 %. **The 1.6 mm margin depends on these allowance choices** | assumption | both runs kept; the reasons are in §1 |
| 6 | Records disagree: the `r1_padring` README says G1 macros sat inside x, y = 364–1050 µm. The G1 r4 GDS shows analog macros at 331 µm (under the ring), as S3 says | record inconsistency | measured (run `g1check`); the `r1_padring` README is not edited by this study (outside its files) |
| 7 | PLAN.md §2a lists `r1_safe` at 0.025 mm² (revision 2); revision 3 gives 0.05–0.06. The specification "Area" row lists blocks as pending that have areas | stale record | §1 of this study replaces them; the coordinator updates the specification |

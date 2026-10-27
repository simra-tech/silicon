# R1_TOP

Block `r1_top` (track T8, P3 preparation). This block assembles the R1 chip top level from the ring of record and
the finished macros. The four macros that are not finished are placeholder outlines.

## Full-chip testbench, schematic level (track T10, 2026-10-26)

Method, coverage, MODEL parts and the swap to post-layout netlists: [`tb/README.md`](tb/README.md). One deck per
test on the schematic netlists of record, with the r1_ctrl 0.5 RTL in an XSPICE `d_cosim` instance (G1 method).
Raw data: `<G1_RESULTS_ROOT>/r1_top/tb/<run-id>/`. Summaries: `tb/results/<run-id>.json`. Every result uses the
ideal VREF buffer model M6 (D20: `r1_bias` revision 2 output `vref_b`, not yet designed). Second-budget decks use
the fast view (`tb/README.md` section 12): `r1_bgr`, `r1_bias` and the POR as recorded behaviour, everything else real.

| Test | Status | Evidence |
| --- | --- | --- |
| 1 Power-up (ramps, `por_n`, bandgap and bias settle, oscillator at code 22, reset exit, `ID` over SPI) | 1a **passed** (real `r1_bgr` + `r1_bias` rev 1d/POR + loads, 10 µs ramps: VREF 1.0449 V settled 1.9 µs after VDDA, all 11 bias outputs 10.14 / 5.07 µA within 0.02 % of the record, settled by 11.2 µs, `por_n` held low to 40 µs; deck 13 s). Oscillator part **passed** against the schematic record: 32.72 MHz at code 22 (record 32.69 MHz); the D13 band 28-32 MHz is not applicable at schematic level (post-layout record 30.30 MHz); deck 317 s. POR release not simulated: 197-247 µs (`r1_bias` record). 1b **failed** on one criterion (run `t10-t1b-sub-a`: subset F18, fast view, M6, `reltol=1e-4`, `por_n` step at 1.0 µs, 13 µs, deck 717 s): reset exit passed (1.041 µs, limit `por_n` + 0.17 µs); `ID` passed (0x5205); `FAULT` has POR and CAL set (passed) but reads 0x1900, not the reset value 0x1800 (failed: finding R3, STO latched at reset exit). Next lever: `r1_ctrl` owner, `u_sen` reset value. The full fast-view deck `t10-t1b-fast-b` (8 µs, deck 5516 s) gave the same reset exit and `ID`; its `tstop` was too short for the `FAULT` read (F17). First-budget full-chip ramp `t10-t1-sch-a` failed (simulator abort) | `tb/results/t10-t1a-dc-a.json`, `tb/results/t10-t1a-osc-a.json`, `tb/results/t10-t1b-sub-a.json`, `tb/results/t10-t1b-fast-b.json` |
| 2 Encoder path (10 kHz, pads → AFE → ADC → weights → CORDIC; SPI `POS`; one BiSS-C frame with CRC) | **failed** (testbench, not a chip result). Run `t10-t2-fast-b` (fast view, D11, M6, R2 fix, 3 threads, 24 µs, deck 9004 s): the testbench ADC sequencer / ctrl handshake stopped after the third conversion (3.5 µs; the F19 change caused this early stop and is reverted; open issue O10), so 0 encoder pairs (limit ≥ 10). Parts that ran: strobe position passed (0.595-0.603 ns); SPI reads answered (`STATUS` 0x0190); one BiSS-C frame with ACK, stop bit and CRC equal to the computed CRC (0x3F; data 0). Next lever: O10, then rerun on the HEAD model. Run `t10-t2-fast-a` stopped by the track (rate) | `tb/results/t10-t2-fast-b.json`, `tb/runs/t10-t2-fast-a/run.json` |
| 3 Current path (shunt levels at the PWM centre strobe; `I_A`/`I_B` within 1 %) | **failed** (testbench, not a chip result). Rerun `t10-t3-fast-c` (fast view, D11, M6, F19 change since reverted, 2 threads, 20 µs, deck 9257 s): the testbench ADC sequencer / ctrl handshake stopped after the third conversion (3.5 µs); no current frame; `I_A`/`I_B` read 0 (open issue O10 in `tb/README.md`). Run `t10-t3-fast-b` (deck 10 495 s): 13 conversions, then the same stop; strobe position passed (0.593-0.605 ns, limit 0.3-0.9 ns); isense outputs correct (gain 14: level 0 −0.560 V, level 1 A −0.140 V, B +0.559 V); steps failed (−101 %). Next lever: handshake monitors and a 5 µs reproduction deck (O10). First budget: simulator abort in `xu_bgr.xqd1` | `tb/results/t10-t3-fast-c.json`, `tb/results/t10-t3-fast-b.json` |
| 4 Safety (OC step → `FAULT_N` and gates low; EN low → gates low; clear sequences) | 8 criteria **passed**, 1 **not run** (run `t10-t4-safe-a`: safety subset, isense/safe/gate real, AFE and ADC stubs; fast view, D11, M6, THR_NEG fix F20; 38 µs, deck 8121 s). OC step (30 → 100 mV on ISA, threshold 69.8 mV): `FAULT_N` low after 166 ns, all gates < 1 V after 278 ns (limit 1369 ns); cause OC_A; after `CLR` PWM on `GATE_A` again. EN low: gates < 1 V after 85 ns (limit 1 µs); `FAULT` = 0x0100 (STO). After EN high and `CLR`: not run, the 3.6 µs window ends at 39.3 µs and `tstop` was 38 µs (F21). Rerun `t10-t4-safe-b` (`tstop` 40.5 µs, 2 threads) running. Earlier run `t10-t4-fast-b` failed: gates never on (F20, finding R4) | `tb/results/t10-t4-safe-a.json`, `tb/runs/t10-t4-safe-b/run.json`, `tb/results/t10-t4-fast-b.json` |
| 5 Thermal (T2F count at 27 °C and 125 °C) | 27 °C **passed** (run `t10-t5-sub-27-a`, thermal subset F18, fast view, M6, `reltol=1e-4`, 25 µs, deck 650 s): `TEMP` = 14, expected 13.86 ± 1 (f_T2F × 2^8 / f_clk); f_T2F 1.624 MHz, +1.49 % against the T2F record 1.6003 MHz (limit 3 %). 125 °C **passed** (run `t10-t5-sub-125-a`, deck 716 s): `TEMP` = 18, expected 18.22 ± 1; f_T2F 2.135 MHz, +1.17 % against the record 2.1100 MHz. The full fast view cannot run this test: the T2F HBT aborts at `reltol=2e-3` (F18) | `tb/runs/t10-t5-sub-27-a/run.json`, `tb/results/t10-t5-sub-27-a.json`, `tb/results/t10-t5-sub-125-a.json` |
| 6 Oscillator trim count (`OSC_COUNT` against the simulated frequency) | **passed** (run `t10-t6-sub-a`: thermal subset F18 with the transistor-level `r1_osc`, fast view, M6, `reltol=1e-4`, 12.5 µs, deck 1939 s): `OSC_COUNT` = 53, expected 52.33 ± 1.5 (16 f_osc / f_ref, f_ref 10 MHz); `r1_osc` at code 22: 32.71 MHz (schematic record 32.69 MHz ± 2 %); `STATUS.OSC_DONE` set (0x0580) | `tb/runs/t10-t6-sub-a/run.json`, `tb/results/t10-t6-sub-a.json` |
| Post-layout rerun (`--view pex`) | not run (no `views/pex.inc`; ADC layout does not exist) | — |

Finding R1 (functional bug, chip level): no block of record buffers `vref_bg`. The `r1_bgr` output (about 180 kΩ
source) is loaded by the `r1_safe` string and the `r1_isense` pedestals to 0.22 V instead of 1.045 V (runs
`t10-diag-nodeset-b`, `t10-diag-m6-a`). The decks use an ideal buffer model (M6 in `tb/README.md`) until a VREF
buffer exists. All results above are with M6.

Finding R2 (testbench bug, fixed): in deck 2 both ADC slices returned the constant code 2063. The cause is the
testbench sequencer model M1: its strobes reached the ADC 0.54 ns after the clk30 edge (`tb/README.md` section 10).
The fix is in `tb/rtl/r1_chip_dig.v` and is confirmed on the first conversion (run `t10-diag-t2enc-b`); deck 2
runs again with it (run `t10-t2-fast-a`, fast view).

Finding R3 (functional bug, `r1_ctrl` RTL 0.5): after reset, `FAULT` reads 0x1900, not the register-map reset value
0x1800, with `EN_STO_IN` high the whole time (run `t10-t1b-sub-a`). Bit 8 (STO) is latched. Cause (from the RTL):
the EN synchroniser `u_sen` in `r1_safe.v` uses `r1_sync2` with the default `RST_VAL = 0`. For two ticks after the
reset release `en_s` = 0, and the fault latch takes `~en_s` as a cause. The host must write `CLR` once after
power-up. Next step (owner `r1_ctrl`): `RST_VAL(1)` on `u_sen`, or document 0x1900 as the reset value. The
combinational gate-off path from the EN pad does not use `en_s`, so `RST_VAL = 1` does not weaken STO.

Finding R4 (specification, `r1_ctrl` register map): the reset value of `CMP_THR_A/B` (0x3F3F) makes both NEG
comparators active at zero current (NEG cell code c = 63 − THR_NEG = 0, threshold −VREF; `cmp_neg_a/b` = 1.2 V in
decks 3 and 4). FAULT bits 1 and 3 latch at every reset exit and `CLR` cannot clear them, even when masked, until
the host writes NEG thresholds. Next step (owner `r1_ctrl`): reset THR_NEG 0, or document the reset behaviour.

## Try e (2026-10-21): floorplan C4 on the 1700 µm ring — run of record `asm-20261021-e4`

Try e builds `r1_top` on the 1700 µm ring of record (`r1_padring` revision d, GDS `81bba04b…`) with floorplan C4
of S7. Every macro that exists today is placed. Only `r1_adc` is a placeholder. The generator is
`layout/r1_top_assemble_e.py`. The try-d files below this section stay as the record of try d.

### What try e contains

1. Ring of record, 1700 × 1700 µm, pitch 142 µm (4141 fill instances removed; 22 pad labels copied to the top).
2. Real macros: `r1_ctrl_top` 0.4 (t7), `r1_afe` revision E (d17d505f7), `r1_isense` layout a (db5461161),
   `r1_osc` revision 2 layout r2d (679a97320), `r1_bias` (934b90195), `r1_safe`, `r1_bgr`, `r1_t2f` (MY),
   `r1_gate_lv`, 6 × `r1_ls`, 34 × `sg13g2_decap_8`, 1 × `sg13g2_tiehi` (`u_tie_osc`).
3. Placeholder: `r1_adc_ph`, S7 hard slot 439.0 × 182.3 µm at (592.0, 376.0), 51 Metal3 pin stubs.
4. Supplies per S7: core ring (outer `VSS`, inner `VDD`), `r1_ctrl` stripes, north and south straps, south
   Metal4 trunks (`VSS`, `VDD`, `VDDA`), `VDDA` feed from pad 7, west `VDDA` riser.
5. MIM rule: TopMetal2 only over MIM blocks. In C4 only `r1_afe` is under a ring column. The west TopMetal1
   columns are cut for y 735–1239.4 and replaced by TopMetal2 (y 720–1254.4); TopVia2 only in the 15 µm overlaps.
   `r1_isense`, `r1_osc` and the ADC slot are not under the ring.
6. 46 routed signal nets (try d: 20). List: [`reports/connectivity_e.md`](reports/connectivity_e.md).

Placement with the S7 C4 deltas: [`reports/placement_e.csv`](reports/placement_e.csv). Drop-in requirements:
[`reports/integration_checklist_e.md`](reports/integration_checklist_e.md). Picture:
[`layout/r1_top_e.png`](layout/r1_top_e.png) (run e4, 96 kB).

### Position deltas against S7 C4

| Item | S7 C4 | Try e | Delta | Reason |
| --- | --- | --- | --- | --- |
| Pad centres (all sides) | 500, 640, 780, 920, 1060, 1200 | 495, 637, 779, 921, 1063, 1205 | −5, −3, −1, +1, +3, +5 | ring of record, pitch 142 µm (S7 assumed 140) |
| `r1_afe` | (336.0, 720.0) | (336.0, 740.0) | +20.0 y | `sinp`, `cosp` inside the pad 21 / 23 `pad` windows: straight 15 µm lines (S7: 36 µm) |
| `r1_ctrl_top` | (543.8, 673.3) | (543.8, 673.0) | −0.3 y | top edge 0.3 µm under the inner north TopMetal2 row (as try d) |
| `r1_bias` (real, 120 × 165.94) | bias slot (442.0, 488.6), 86.8 × 69.7; POR slot (345, 1270) | (444.0, 488.6) | +2.0 x; POR slot dropped (POR is inside `r1_bias`) | layout larger than the slot; 10 µm from `r1_bgr` |
| `r1_t2f` (MY) | (442.0, 376.0) | (444.0, 376.0) | +2.0 x | aligned with `r1_bias` |
| ADC slot | (556.0, 376.0) | (592.0, 376.0) | +36.0 x | the wider `r1_bias` and its east supply risers |
| `VDDA` decap of C4 | (849.4, 376) | not placed | — | the 439 µm ADC slot takes the place |
| `r1_gate_lv` | (440.0, 1300.0) | (440.0, 1296.0) | −4.0 y | try-d relation to the north ring row |
| `r1_isense`, `r1_osc`, `r1_safe`, `r1_bgr` | C4 | C4 | 0 | — |

Pad route lengths: `SIN_P`, `COS_P` 15 µm; `SIN_N` 153, `COS_N` 157 µm; `ISA_N`, `ISB_P` 132 µm; `ISA_P` 272,
`ISB_N` 270 µm (Manhattan).

### Status (run `asm-20261021-e4`)

GDS `<G1_RESULTS_ROOT>/r1_top/asm-20261021-e4/r1_top.gds`, SHA-256 `67d5148ef70d5d413925072c75386045ccaa6077c27121dde076d7de84d9378e`.
LVS reference `<G1_RESULTS_ROOT>/r1_top/asm-20261021-e4/cdl/r1_top.cdl`, SHA-256 `6d117ccaaf3bbe5aa9534c06f5c8d5b8df1407d2cfb975cd58806f617687fc95`.
LVS pair report: `reports/runs/asm-20261021-e4_lvs_report.txt`.

| Check | Result | Evidence |
| --- | --- | --- |
| Generator self-check (net spacing, overlaps, pairs < 10 µm, outside window, routes inside macros) | passed (0 / 0 / 0 / 0 / 0) | `<G1_RESULTS_ROOT>/r1_top/asm-20261021-e4/r1_top_assembly.json` |
| KLayout DRC main (deep, no density, `--disable_extra_rules`) | passed, 0 markers (run `-e3`: 34 `*_drw_Offgrid`, fixed, E9) | `<G1_RESULTS_ROOT>/r1_top/asm-20261021-e4/drc_main/` |
| KLayout DRC maximal | passed, 0 markers | `<G1_RESULTS_ROOT>/r1_top/asm-20261021-e4/drc_maximal/` |
| KLayout antenna | passed, 0 (runs `-e`, `-e2`: 8, fixed, E7) | `<G1_RESULTS_ROOT>/r1_top/asm-20261021-e4/drc_antenna/` |
| KLayout density | failed, 53 markers, all class (b): no fill, empty ADC slot | `<G1_RESULTS_ROOT>/r1_top/asm-20261021-e4/drc_density/` |
| LVS, deck copy with comparer limits | passed: "Netlists match"; all 52 circuit pairs match; `r1_top` 261 devices, 50 subcircuits | `<G1_RESULTS_ROOT>/r1_top/asm-20261021-e4/lvs_limits/` (`report.txt`) |
| LVS, stock PDK deck | failed: crash in the comparison (exit 11) after extraction; no comparison result. The wrapper prints "Status PASS"; that line is wrong and is not used (as try d) | `<G1_RESULTS_ROOT>/r1_top/asm-20261021-e4/lvs_stock/` |
| Run record | written | `reports/runs/asm-20261021-e4.json` (and `-e`, `-e2`, `-e3`, superseded) |
| Chip fill | see "Try e fill" below (run `-fill3`: density 2 markers, ADC window) | `<G1_RESULTS_ROOT>/r1_top/asm-20261021-e4-fill3/` |
| IR drop and EM of ring and trunks | not run (ring resistance estimated by square count only) | `reports/connectivity_e.md` |
| Post-layout simulation of any top-level net | not run | — |
| Bond plan on the chip GDS | passed on the filled GDS 24/24, see "Try e fill" (unfilled e4: not run) | `<G1_RESULTS_ROOT>/r1_top/asm-20261021-e4-fill3/bondmap/` |
| IHP intake pre-check | not run (chip not complete) | — |
| Drop-in probe of the in-progress `r1_afe` E2, `r1_isense` b | not run (tracks still running; the checklist states the requirements instead) | — |

DRC classes as try d: (a) violation in the assembled parts; (b) placeholder or empty-region density (no fill).

| Deck | Rule | Count | Class (a) | Class (b) |
| --- | --- | --- | --- | --- |
| main | all | 0 | 0 | 0 |
| maximal | all | 0 | 0 | 0 |
| antenna | all | 0 | 0 | 0 (runs `-e`, `-e2`: `Ant.e_TopMetal1` 4 + `Ant.e_TopMetal2` 4, class a, fixed, E7) |
| density | `M2Fil.h` | 16 | 0 | 16 |
| density | `M1Fil.h`, `M4Fil.h` | 7 + 7 | 0 | 14 |
| density | `AFil.g2`, `M5Fil.h` | 6 + 6 | 0 | 12 |
| density | `M3Fil.h` | 4 | 0 | 4 |
| density | `AFil.g`, `GFil.g`, `M1.j`…`M5.j` | 7 × 1 | 0 | 7 |
| **all** | | **53** | **0** | **53** |

Density cause: 800 × 800 µm window coverage and global density below the minimum, because no fill is inserted and
the ADC slot is empty (try d: 35 on the 1600 µm die).

### LVS: what is checked and what is not

The reference is `lvs/make_top_cdl_e.py`: `r1_ctrl_top` 0.4 netlist, the block CDLs of record (hash-checked),
the ring (flat projected reference), decaps and the tie cell. The ADC placeholder is an empty subcircuit; the deck
drops it on both sides. Layout `r1_top` has 147 nets and the reference 362: the reference counts every floating pin net of the unconnected macro pins; they have no layout counterpart and cause no mismatch. Not checked by this comparison:

1. The 51 ADC placeholder pins (floating on both sides).
2. Unconnected macro pins (floating on both sides): `r1_ctrl` 99 (ADC bus 36, `thr_*`/`cal_*` 48 (the
   0.4 safe-threshold words), `ana_ctrl`, `az_win`), `r1_safe` 68 (64 tap inputs, 4 outputs), `r1_afe` 9, `r1_isense` 9, `r1_bgr` 3
   (`iptat`, `vbe`, `dvbe`), `r1_t2f` 2 (`en`, `mode`), `r1_bias` 1 (`ib_adc_ref`), `r1_gate_lv` 1 (`vdda`), and all
   pins except `vss` of the 6 `r1_ls`.
3. The comparison uses the comparer-limit deck copy (`max_depth(8)`, `max_branch_complexity(100)` after `align`,
   no extraction change; `deck_diff.txt` in the run). The stock-deck state is in the table.
4. Block-internal correctness is from the block LVS runs, not from this run (the macros are compared as cells).

### Open issues (try e)

1. `r1_adc` does not exist: 36 digital, 9 analog, `ib_adc_ref`, `vref_in` and supplies are pending (checklist).
2. ctrl 0.4 has no safe tap outputs, `pga_c`, `t2f_en/mode`, `az*`, ADC clock or `osc_en`. ctrl 0.6 template:
   checklist. `OSC_EN` is held by a tie cell until then.
3. `POR_N` runs about 1 330 µm (bias east pin → ctrl north pin, around the AFE). ctrl 0.6 should put `por_n` on
   the south edge (local x 23.7): 146 µm.
4. `VREF_BG` and the 13 bias lines are not shielded. Coupling and the bandgap load (t2f, safe, isense, later the
   ADC) are not simulated.
5. The C4 `VDDA` decap is not placed (ADC slot). The `VDDA` decoupling is open.
6. `u_ls_t2f0/1` at x 545 sit under the bias-output path region; they are not connected. A t2f level-shift place
   is open with ctrl 0.6 (`t2f_en`, `mode`).
7. The north IO-row rail heights (y 1381–1399) are the try-d values + 100 µm, not probed separately; DRC is clean.
8. `r1_gate_lv` `vdda` is not connected (as try d).

### Failures and mistakes (try e)

| # | What happened | Class | Fix |
| --- | --- | --- | --- |
| E1 | The brief named the working-tree files of `r1_afe`, `r1_isense`, `r1_osc`. At the start they were revisions in progress, without block LVS. | spec-ambiguity | Used the committed layouts of record (GDS and CDL agree, block LVS passed); snapshots kept in the run `inputs/` |
| E2 | `pin()` by edge chose large internal straps with the same label: 3 routes ended inside macros (dev run). | functional-bug | Smallest shape at the edge wins; self-check "routes inside macros" added (0) |
| E3 | `r1_t2f` pins asked on the east edge after the MY mirror. | functional-bug | West edge |
| E4 | The coordinator said ctrl 0.4 has no `por_n` port. The t7 GDS and CDL have it (north edge, local (482.9, 663.8)). | coordination | Routed `POR_N`; recorded here |
| E5 | `r1_bias` (120 × 165.94) is larger than the S7 slots; the ADC slot moves +36 µm east and the C4 `VDDA` decap drops out. | estimation | Placement table; open issue 5 |
| E6 | `r1_osc` revision 2 was committed during the run (run `-e` used layout k, `osc_clk` east, 360 µm detour). | coordination | Run `-e2` with revision 2 |
| E7 | Runs `-e` and `-e2`: antenna 8 (`Ant.e_TopMetal1/2`) on the four `r1_osc` `en` gates; `en` was tied straight to `VDD`, which carries the ring metal. Try d had an osc placeholder, so the tie was never checked. | verification-gap | `sg13g2_tiehi` drives `OSC_EN` (run `-e3`: antenna 0) |
| E8 | Run `-e2` clean-up deleted its finished `lvs_limits` directory; the result is lost. | process-hygiene | Recorded in `steps.log` and `run.json`; run `-e3` repeated LVS |
| E9 | Run `-e3`: DRC main 34 × `*_drw_Offgrid` at the tie-cell `L_HI` pad (centre y 1037.4625). | numerical | Pad centre rounded to 1037.46 (run `-e4`) |

### Built against (try e)

| Item | Version | How established |
| --- | --- | --- |
| PDK | IHP-Open-PDK `84374023ee8b4b126bebbba67fcbada0a9c0ff0b` | checked by `flow/run.sh` |
| KLayout | 0.30.9 | container, DRC and LVS logs |
| Container | `tapeoutbench-eda:latest`, id `sha256:ddeb6957…` | `flow/run.sh` |
| ngspice / xschem / LibreLane / CACE | not used | — |
| Ring | `r1_padring` revision d GDS `81bba04b…` | hash checked by the generator |
| `r1_ctrl_top` | 0.4, run `r1ctrl_ll_20261021_t7`, GDS `d52e67e8…` | hash in `run.json` |
| `r1_afe` | revision E, GDS `0181e988…`, CDL `0cfb1980…` | `EXPECT_SHA` (generator) and `EXPECT` (CDL builder) |
| `r1_isense` | layout a, GDS `054373fc…`, CDL `b7923cbd…` | same |
| `r1_osc` | revision 2 (layout r2d), GDS `7c5fb60f…`, CDL `600d5f2b…` | same |
| `r1_bias` | GDS `354fa73c…`, CDL `37636bf6…` | same |
| Other blocks | as try d | `reports/placement_e.csv` |

### Reproduce try e (repository root, POSIX shell)

1. Copy the GDS, CDL and layout JSON of record of `r1_afe` (revision E) and `r1_isense` (layout a) from git into
   `<G1_RESULTS_ROOT>/r1_top/<run>/inputs/ofrecord/` (names `r1_afe.gds`, `r1_afe_lvs.cdl`, `r1_isense.gds`,
   `r1_isense_lvs.cdl`). The generator and the CDL builder check the hashes.
2. Set the environment:
   `G1_CPUSET=116-119; export G1_CPUSET; G1_RESULTS_ROOT=<results root>; export G1_RESULTS_ROOT; G1_WORKDIR=.; export G1_WORKDIR`.
3. Run `sh designs/r1-joint/blocks/r1_top/flow/run_try_e.sh asm-20261021-e4` (steps: gen cdl lvs main antenna
   density maximal stock; one KLayout job at a time).
4. Write the record: `python3 designs/r1-joint/blocks/r1_top/flow/write_run_json.py <run dir> <question> <disposition> run_try_e.sh`.
5. Write the placement table: `python3 designs/r1-joint/blocks/r1_top/flow/write_placement_e.py <run dir>/r1_top_assembly.json designs/r1-joint/blocks/r1_top/reports/placement_e.csv`.

New files of try e: `layout/r1_top_assemble_e.py`, `lvs/make_top_cdl_e.py`, `flow/run_try_e.sh`,
`flow/write_placement_e.py`, `flow/probe_ring_pins.py`, `flow/probe_pin_boxes.py`; changed: `layout/r1_top_png.py`
(die size argument), `flow/write_run_json.py` (driver argument, input snapshots, try-e self-check keys).


### Try e fill (track T8, 2026-10-26)

The chip fill of try e is done. Density has 2 markers left. Both markers are one 800 × 800 µm window, and the ADC
placeholder is the cause. The filled GDS is `<G1_RESULTS_ROOT>/r1_top/asm-20261021-e4-fill3/r1_top.gds`, SHA-256
`7c1dd00ec08e0d4dae5052e51019a6e7bb598de775eb841e4ba241416951d512`. Input: run `asm-20261021-e4` (GDS `67d5148e…`).
Run record: `reports/runs/asm-20261021-e4-fill3.json`. The name `asm-20261021-e4-fill` is the first, partial attempt of
this track (see "Reused"). It stays as a record and is not the result.

Method (`flow/fill_top.sh`):

1. `fill_top_pre.py` draws a temporary no-fill cell. It covers every macro and the ADC placeholder box (bbox + 1 µm),
   the 24 bond openings (+10 µm) and the pad ring. The ring is the whole die outside the sealring hole.
2. The unmodified PDK filler (`filler.py`, macros ActGatP, Metal, TopMetal) runs on a run-time copy of the macros.
   It fills the free area and keeps its own distance from routed metal.
3. `fill_top_fixj.py` removes the GatPoly filler rectangles that break rule `GFil.j` (2215 rectangles).
4. `fill_top_post.py` removes the temporary cell. It checks that only the datatype-22 fill layers differ from the input,
   that all texts and instances are kept and that no pattern cell is orphaned.

Changes to the PDK filler parameters (all inside the rule limits, no rule deck or model card changed): Metal2-Metal5
filler distance 0.45 µm (default 1.5 / 2.0; minimum 0.42 µm by `M2Fil.b`…`M5Fil.b`); GatPoly horizontal gap 1.6 µm
(default 5.0; minimum 0.8 µm by `GFil.c`). Cause: the default values give less than the 800 µm window minimum
(25 %, `M2Fil.h`…`M5Fil.h`) because the macros are sparse in M2-M4.
Exception to "no fill over macros": on `r1_ctrl_top` the chip filler may fill Metal2-Metal5 (option `thru`). The fill is
top-cell shapes. No macro cell is edited. The analog macros, the ADC box, the ring and the bond openings get no fill.

| Check | Result | Evidence |
| --- | --- | --- |
| Fill gate (only fill layers differ, texts/instances kept, no orphan) | passed | `reports/runs/asm-20261021-e4-fill3.json` |
| DRC main | passed, 0 markers | `<G1_RESULTS_ROOT>/r1_top/asm-20261021-e4-fill3/drc_main/` |
| DRC maximal | passed, 0 markers (2215 `GFil.j` removed by step 3) | `<G1_RESULTS_ROOT>/r1_top/asm-20261021-e4-fill3/drc_maximal/` |
| DRC antenna | passed, 0 | `<G1_RESULTS_ROOT>/r1_top/asm-20261021-e4-fill3/drc_antenna/` |
| DRC density | failed, 2 markers: `M2Fil.h`, `M5Fil.h`. Both are the window (400, 400)–(1200, 1200); both overlap the ADC box | `<G1_RESULTS_ROOT>/r1_top/asm-20261021-e4-fill3/drc_density/` (`markers.json`) |
| Density with the ADC box open to fill (what-if, not a deliverable) | passed, 0 markers | `<G1_RESULTS_ROOT>/r1_top/asm-20261021-e4-fill3-whatif-adc/drc_density/` |
| LVS, deck copy with comparer limits, on the filled GDS | passed: "Netlists match", 52 of 52 circuit pairs match, `r1_top` 261 devices, 50 subcircuits (as unfilled e4) | `reports/runs/asm-20261021-e4-fill3_lvs_report.txt` |
| LVS, stock PDK deck | not run (crashes on e4 already, exit 11) | — |
| Bond map on the chip GDS | passed: 24 of 24 openings matched, 22 labels, die 1700 µm, hash ok | `<G1_RESULTS_ROOT>/r1_top/asm-20261021-e4-fill3/bondmap/verify_bondmap_chip.json` |
| Post-fill parasitics, timing or simulation | not run | — |

Density markers that remain (class: ADC placeholder):

| Rule | Window (µm) | Window coverage | Minimum | Cause |
| --- | --- | --- | --- | --- |
| `M2Fil.h` | 400, 400, 1200, 1200 | 23.69 % | 25 % | 69 494 µm² of the ADC box in the window have no metal (no fill) |
| `M5Fil.h` | 400, 400, 1200, 1200 | 23.35 % | 25 % | same |

The what-if run opens the ADC box to the same filler. All density rules then pass. The ADC macro must bring fill of
at least about 15 % Metal2 and Metal5 coverage over the part of its 439 × 182 µm box inside the window (estimate) (what-if: Metal2 56.7 %). Window values from
the 100 µm-step scan: `reports/runs/asm-20261021-e4-fill3_window_density.json`.

Fill and density of the delivered GDS (counts from `fill_counts.json`; density from `flow/probe_window_minmax.py`,
100 µm step, drawn + filler; the deck reports violations only, it has no per-window numbers):

| Layer | Fill rectangles | Fill area (µm²) | Window min / max (%) | Global (%) |
| --- | --- | --- | --- | --- |
| Activ | 37 349 | 431 754 | not scanned | — |
| GatPoly | 53 235 | 372 645 | not scanned | — |
| Metal1 | 53 463 | 484 192 | 26.5 / 49.4 | 42.2 |
| Metal2 | 211 982 | 1 163 693 | 23.7 / 51.0 | 46.3 |
| Metal3 | 142 493 | 674 879 | 25.5 / 58.3 | 52.6 |
| Metal4 | 160 233 | 723 655 | 28.1 / 60.6 | 53.3 |
| Metal5 | 41 652 | 455 337 | 21.9 / 50.7 | 43.7 |
| TopMetal1 | 6 388 | 319 400 | not scanned | — |
| TopMetal2 | 7 759 | 387 950 | not scanned | — |

The minimum windows are in the ADC corner (400, 400), (500, 400). Metal5 shows 21.9 % on the scan grid; the deck
windows flag (400, 400) only.

Reused from the terminated attempt of 2026-10-21 (killed by an API limit): `fill_top_pre.py`, `fill_top_post.py`,
`fill_density_markers.py`, `run_fill_checks.sh`, `write_fill_run_json.py`, the ideas of `thru` and of the run-time
filler copy, and the density what-if. Its runs `asm-20261021-e4-fill`, `-attempt1`…`-attempt5`, `-whatif-adc` stay in
`<G1_RESULTS_ROOT>/r1_top/`. Its best result: density 4 markers, main 0, antenna 0; maximal had 2215 `GFil.j` (attempt 5). Changed
in this resume: `fill_top.sh` (Metal3-5 distance argument, `fill_top_fixj.py` step), `fill_top_fixj.py` (it had a
syntax error and never ran; repaired), new probes `probe_window_cov.py`, `probe_window_minmax.py`, `probe_gfilj.py`.

Reproduce (repository root, POSIX shell; one KLayout job at a time):

1. `G1_CPUSET=116-119; export G1_CPUSET; G1_RESULTS_ROOT=<results root>; export G1_RESULTS_ROOT; G1_WORKDIR=.; export G1_WORKDIR`
2. `sh designs/r1-joint/blocks/r1_top/flow/fill_top.sh $G1_RESULTS_ROOT/r1_top/asm-20261021-e4 $G1_RESULTS_ROOT/r1_top/asm-20261021-e4-fill3 0 "r1_ctrl_top:10,30,50,67" 0.45 1.6 0.45`
3. `sh designs/r1-joint/blocks/r1_top/flow/run_fill_checks.sh $G1_RESULTS_ROOT/r1_top/asm-20261021-e4 $G1_RESULTS_ROOT/r1_top/asm-20261021-e4-fill3`
4. What-if: same as step 2 with the `thru` argument `"r1_ctrl_top:10,30,50,67;r1_adc_ph:1,5,8,10,30,50,67,126,134"` into a new run directory.

Open issues (fill):

1. Two density markers (`M2Fil.h`, `M5Fil.h`) wait for the ADC macro and its own fill. Recheck when the ADC is placed.
2. The fill is floating metal at 0.45 µm spacing next to routed metal. Coupling to the bias and reference lines is not simulated.
3. The analog macros (`r1_afe`, `r1_isense`, `r1_osc`, `r1_bias`) have 1-8 % Metal2-Metal4 coverage inside their boxes. They carry the window minima. A fill inside them is a block decision.
4. The `thru` fill over `r1_ctrl_top` is a deviation from "no fill over macros". Confirm it with the owner of the ctrl hardening.
5. File size: filled GDS is 76 MB. IHP intake size limits are not checked.

Failures and mistakes (fill):

| # | What happened | Class | Fix |
| --- | --- | --- | --- |
| F1 | Default filler distances give 44 % coverage on free area and the macros are sparse. Windows stayed under 25 %. | estimation | Distances 0.45 µm (Metal2-5), gap 1.6 µm (GatPoly) |
| F2 | Narrow GatPoly gap leaves 2215 rectangles that break `GFil.j` (maximal deck). Earlier attempts ran main and density only. | verification-gap | Step `fill_top_fixj.py`; maximal deck added to the checks, 0 markers |
| F3 | `fill_top_fixj.py` of the earlier attempt was never run and had a syntax error. Three further faults followed: a Region copy call, zero-width marker boxes dropped, an orphan pattern cell. | functional-bug | Repaired in this resume; the post-step gate catches the orphan |
| F4 | The first re-run (`-fill2`, distance 0.6 µm) left 3 markers. I picked the distance by guess, without a coverage estimate. | planning | Window coverage probe, then 0.45 µm (`-fill3`); `-fill2` has no checks beyond density |
| F5 | The target name `asm-20261021-e4-fill` already held the earlier attempt. Run directories are not deleted. | process-hygiene | Result is `-fill3`; the name is explained above |
| F6 | `fill_density_markers.py` needs the container Python (`klayout` module). Host Python failed. | tooling | Run it with `flow/run.sh python3` |

## What it is (try d, 1600 µm)

`layout/r1_top_assemble.py` is a KLayout generator. It writes `r1_top.gds` (top cell `r1_top`, 1600 × 1600 µm).
It does these steps:

1. It reads the ring of record `r1_padring_1600.gds` (SHA-256 `40514b4f…`, revision b/c) and checks the hash.
2. It removes the 4198 fill instances from the ring top cell. The ring fill covers the core area. Chip fill comes later.
3. It copies the pad labels of the ring (22 × TopMetal2 pin text) into the top cell (see failure F1).
4. It places the finished macros: `r1_ctrl_top` (0.4, run `r1ctrl_ll_20261021_t7`), `r1_safe`, `r1_bgr`, `r1_t2f`,
   `r1_gate_lv` (one instance with three channels), and six `r1_ls`.
5. It draws placeholders for `r1_afe`, `r1_adc`, `r1_isense_a`, `r1_isense_b` and `r1_osc`. Each placeholder is a
   `prBoundary` outline with a text and Metal3 pin stubs with pin labels. The sizes are the S6 sizes.
6. It builds the supplies: core ring identity, `r1_ctrl` stripes, north and south straps, the south Metal4 trunks
   (`VSS`, `VDD`, `VDDA`) and the `VDDA` feed from pad 7.
7. It applies the coordinator MIM rule on the west ring columns (TopMetal2 only over the AFE).
8. It places 34 `sg13g2_decap_8` cells on `VDD` (antenna load, see failure F2).
9. It routes the 20 signal nets that exist today on Metal2–Metal4. The IO-row TopMetal is not touched inside the
   analog band (S6 cut C7).
10. It runs a self-check (different nets on one layer, with the PDK spacing) and an overlap check.

Placement: [`reports/placement.csv`](reports/placement.csv). Connectivity: [`reports/connectivity.md`](reports/connectivity.md).
Integration checklist for the pending macros: [`reports/integration_checklist.md`](reports/integration_checklist.md).
Picture: [`layout/r1_top.png`](layout/r1_top.png) (try d, 93 kB).

## State (2026-10-21, try d of record)

| Item | Value |
| --- | --- |
| GDS | `<G1_RESULTS_ROOT>/r1_top/asm-20261021-d/r1_top.gds`, SHA-256 `9cd93bb976eb264422c64472985de7fdf9447b537b04889d3b929852267cf508` |
| LVS reference | `<G1_RESULTS_ROOT>/r1_top/asm-20261021-d/cdl/r1_top.cdl`, SHA-256 `94f191a8542556acdbab68cb422f34c78a3cb77b2901f056741bd850974b53ae` |
| Run record | `<G1_RESULTS_ROOT>/r1_top/asm-20261021-d/run.json` (and `asm-20261021-a`, `-b`, `-c`, superseded) |
| Self-check | 0 net conflicts, 0 instance overlaps, 0 instances outside the IO row |

## Status

| Check | Result | Evidence |
| --- | --- | --- |
| Generator self-check (net spacing, overlaps) | passed (0 / 0 / 0) | `<G1_RESULTS_ROOT>/r1_top/asm-20261021-d/r1_top_assembly.json` |
| KLayout DRC main (deep, no density, `--disable_extra_rules`) | passed, 0 markers (try a: 0) | `<G1_RESULTS_ROOT>/r1_top/asm-20261021-d/drc_main/` |
| KLayout DRC maximal | passed, 0 markers (try a: 6 × `V3.c1`, fixed) | `<G1_RESULTS_ROOT>/r1_top/asm-20261021-d/drc_maximal/` |
| KLayout antenna | passed, 0 (try a: 12, fixed) | `<G1_RESULTS_ROOT>/r1_top/asm-20261021-d/drc_antenna/` |
| KLayout density | failed, 35 markers, all class (b): no fill yet | `<G1_RESULTS_ROOT>/r1_top/asm-20261021-d/drc_density/` |
| LVS, deck copy with comparer limits | passed: "Netlists match"; all 46 circuit pairs match; `r1_top` 261 devices, 45 subcircuits | `<G1_RESULTS_ROOT>/r1_top/asm-20261021-d/lvs_limits/` (`report.txt`) |
| LVS, stock PDK deck | failed: crash in the comparison (signal 11, exit 11) after extraction, 5 min; no comparison result. The wrapper summary prints "Status PASS"; that line is wrong and is not used. Same behaviour as `r1_safe` (T4). The comparer-limit copy is the LVS of record | `<G1_RESULTS_ROOT>/r1_top/asm-20261021-d/lvs_stock/` |
| Chip fill | see "Try e fill" below (run `-fill3`: density 2 markers, ADC window) | `<G1_RESULTS_ROOT>/r1_top/asm-20261021-e4-fill3/` |
| IR drop and EM of the trunks and ring | not run (ring resistance only estimated by square count) | `reports/connectivity.md` |
| Post-layout simulation of any top-level net | not run | — |
| Bond plan on the chip GDS | not run | — |
| IHP intake pre-check | not run (the chip is not complete) | — |

DRC classes. Class (a) is a violation in the assembled parts (macros, ring, routes). Class (b) comes from the
placeholders or from empty regions: density and fill-coverage rules, because no fill is inserted yet, and any
marker inside a placeholder outline. `flow/drc_summary.py` makes the split by rule name and marker position.

| Deck | Rule | Count | Class (a) | Class (b) | Cause |
| --- | --- | --- | --- | --- | --- |
| main | all | 0 | 0 | 0 | — |
| maximal | all | 0 | 0 | 0 | — (try a: `V3.c1` 6, class a, fixed in try d) |
| antenna | all | 0 | 0 | 0 | — (try a: `Ant.e_Metal5` 4, `Ant.e_TopMetal1` 4, `Ant.e_TopMetal2` 4, class a, fixed in try b) |
| density | `M2Fil.h` | 9 | 0 | 9 | 800 × 800 µm window coverage < 25 %: no fill, empty placeholders |
| density | `M4Fil.h`, `M5Fil.h` | 5 + 5 | 0 | 10 | same |
| density | `M1Fil.h`, `M3Fil.h` | 3 + 3 | 0 | 6 | same |
| density | `AFil.g2` | 3 | 0 | 3 | same (Activ) |
| density | `AFil.g`, `GFil.g`, `M1.j`…`M5.j` | 7 × 1 | 0 | 7 | global density below the minimum: no fill |
| **all** | | **35** | **0** | **35** | |

### LVS and the placeholders

The placeholders are empty subcircuits in the reference. Their layout cells have no devices. The deck drops both
sides, so the placeholders cause **no mismatch**. Their pin nets are floating on both sides. The comparison
therefore says nothing about the 91 placeholder pins and the 106 `r1_ctrl` pins that are not routed.
They are listed as pending in `reports/connectivity.md`.

Try a failed with all 46 circuit pairs matched. The cause was `flag_missing_ports` (strict port mode of the deck):
the 22 pad labels were inside the ring cell, so the top-level nets had no names (failure F1). This was not
caused by a placeholder.

The comparer-limit copy is the T4 method (`blocks/r1_safe`): `max_depth(8)` and `max_branch_complexity(100)`
after `align`, no extraction or rule line changed (`lvs/run_lvs_top.sh`, `deck_diff.txt` in the run).

## Floorplan: deviations from S6 and open issues

1. **Floorplan F1 cannot hold the real AFE.** The AFE layout (d17d505f7) is 192.8 × 494.4 µm. The S6 slot is
   140 × 493 µm. Real AFE (192.8) + `r1_ctrl` (520) + `r1_safe` (249.34) = 962 µm. The extended window is 938 µm.
   Options (not drawn):
   - F2: AFE rotated into the south band, `r1_ctrl` moved west, the east column for the analog blocks.
     The encoder input routes become long unless the optional S6 pin-map change (§5 item 6) is made.
   - A narrower `r1_safe` layout (≤ 225 µm wide).
   - The 1.7 mm die (S6 escalation rule).
   **Recommended: 1.7 mm**, because the escalation gate also trips (item 2). This needs a T6 ring run, a bond-plan
   run and owner confirmation of the die area. Not applied here.
2. **S6 escalation gate (laid-out analog sum > 0.30 mm²).** Laid out: `r1_afe` 0.0953, `r1_safe` 0.0718,
   `r1_bgr` 0.0187, `r1_t2f` 0.0094, `r1_osc` 0.0183 (PLAN.md §5), `r1_ls` × 6 0.0006, `r1_gate_lv` 0.0008, sum
   0.215 mm². With `r1_isense` (working-tree layout 0.047, not of record) the sum is 0.262. The gate trips if
   `r1_adc` is above 0.038 mm². The `r1_adc` revision 4 estimate is ≈ 0.068 mm² (sum ≈ 0.33 mm²).
3. `r1_safe` is 249.34 × 287.81 µm against an S6 slot of 180 × 306. It sits at x 1021–1270, under the east ring
   columns (it has Metal1–Metal4 only, so C7 allows it).
4. `r1_bgr` is 96 × 194.3 µm against a slot 172 µm high. It is rotated (R270) into the south band.
5. `r1_ctrl` is 23 µm west of the S6 position. The guard strips are 7–10 µm, not 30 µm (S6 A2).
6. The `r1_isense` and `r1_osc` placeholders are 10 µm west of S6, so they clear the east ring TopMetal1.

### Interface gaps (the top level cannot close these alone)

1. **Safe thresholds (blocked).** `r1_ctrl` has `thr_*`/`cal_*` (6 + 6 bits × 4 = 48 bits). `r1_safe` needs
   `nP/nN[7:0]` × 4 (64 bits). The adders `nP = 4c + ceil(d/2)` and `nN = 4(63−c) − floor(d/2)` are in no block.
   Recommended: put them in `r1_ctrl` 0.5. The margin to 240 000 µm² placed is only 799 µm² (`r1_ctrl` README);
   the next trim (12-bit PWM words) gives about 1 000 µm².
2. `por_n` of `r1_ctrl` has no source (no POR block).
3. `r1_safe` needs 4 × 5 µA PTAT bias (`ibias_*`). `r1_bgr` has one `iptat`. The AFE (`ib_*`) and the
   working-tree `r1_isense` (`ibias_a/b`) also need bias currents. No bias block exists.
4. `r1_t2f` `en` and `mode` have no `r1_ctrl` output (proposal: `ana_ctrl[3]`, `[4]` through `u_ls_t2f0/1`).
   Today these gate inputs float. The six `r1_ls` cells are placed but not connected.
5. The PGA decoder (`ana_ctrl[2:0]` to `c1..c4`) is in no block. The register map gives it to the chip level.
6. `VREF_BG` drives the `r1_safe` string (4.2 µA) directly. `r1_safe` assumed a buffered reference. The load on
   the bandgap is not simulated (block rule of 2026-10-21: real neighbour load). The ADC will add its own load.
7. Gate path. The `r1_ctrl` RTL already makes `gate_x = pwm_x & gate_ok & en_pad`. So `r1_gate_lv` is a buffer.
   One instance has three channels (the brief said three instances). `gate_en` is tied to `VDD`. The level shift
   is inside the `sg13g2_IOPadOut30mA` pad (core input 1.2 V). No `r1_ls` is on the gate path.

### Ring over MIM blocks (coordinator rule)

The west ring TopMetal1 columns are replaced by TopMetal2 strips over the AFE. TopVia2 is placed only outside the
AFE outline. There is no detour and no resistance penalty (estimated −0.17 to −0.19 Ω per column). Details and the
numbers are in `reports/connectivity.md` and `reports/integration_checklist.md`.

## Failures and mistakes

| # | What happened | Class | Fix |
| --- | --- | --- | --- |
| F1 | Try a LVS: all circuits matched, but the run failed. The deck runs `flag_missing_ports`. The pad labels were in the ring cell, so the top nets had no names. | verification-gap | Copy the 22 ring labels into `r1_top` (try b) |
| F2 | Try a antenna: 12 markers (`Ant.e_Metal5/TopMetal1/TopMetal2` at the four `IOPadIn` receiver gates). The `r1_padring` README gave the cause and the fix (gate load on `vdd`) before the first build. The `r1_ctrl` decaps join `VDD` only at TopMetal1/TopMetal2, so they do not count for these rules. | planning | 34 `sg13g2_decap_8` (28.6 µm² gate on `VDD`), joined on Metal1–Metal4 (try b). Antenna 0 |
| F3 | Try b LVS: the new decap cell got the name `sg13g2_decap_8$1` (a second copy next to the one from `r1_ctrl_top`). The deck flattened it. | tooling | Reuse the library cell that is already in the layout (try c) |
| F4 | Try a maximal: 6 × `V3.c1` (Via3 endcap). The Via3 at the narrow `r1_bgr` and `r1_safe` Metal3 pins sat on the pin end. The generator self-check tests spacing only; the main deck does not have `V3.c1`. | verification-gap | 0.5 µm Metal3 pad under each such via (try d) |
| F5 | The first south `VDD` straps overlapped the `r1_bgr` `vss` hookup. | planning | Found by the self-check before any DRC; straps moved to f0+2…f0+8 |
| F6 | The first `run_try.sh` call set `G1_WORKDIR` to a results path; `flow/run.sh` uses it as a path under the repository. | tooling | `G1_WORKDIR=.` |
| F7 | Tries b and c were stopped after the step that tested their fix, to save CPU. Their records say so. | process-hygiene | Labelled in `steps.log` and `run.json` |
| F8 | S6 sizes were estimates. Three laid-out blocks (`r1_afe`, `r1_safe`, `r1_bgr`) do not fit their S6 slots. | estimation | Open issue 1 and 2 above |
| F9 | Interface gaps between blocks (safe codes, biases, t2f controls, PGA decoder, POR). | coordination | Open interface gaps 1–5 |

## Built against

| Item | Version | How established |
| --- | --- | --- |
| PDK | IHP-Open-PDK `84374023ee8b4b126bebbba67fcbada0a9c0ff0b` | checked by `flow/run.sh` before every run |
| KLayout | 0.30.9 | `klayout -v` in the container; DRC and LVS logs |
| Container | `tapeoutbench-eda:latest`, id `sha256:ddeb6957…` | checked by `flow/run.sh` |
| ngspice / xschem / LibreLane / CACE | not used | — |
| Ring | `r1_padring` revision b/c GDS `40514b4f…` | hash checked by the generator |
| `r1_ctrl_top` | 0.4, run `r1ctrl_ll_20261021_t7`, GDS `d52e67e8…` | hash in `run.json` |
| Block GDS | `r1_safe` `fbc31139…`, `r1_bgr` `324e3c27…`, `r1_t2f` `5e7aa75a…`, `r1_ls` `a4f49636…`, `r1_gate_lv` (filled) `a3dee0f0…` | hashes in `reports/placement.csv` |

## Files and reproduction

| File | Purpose |
| --- | --- |
| `layout/r1_top_assemble.py` | generator: `python3 r1_top_assemble.py <G1_RESULTS_ROOT> <out_dir>` |
| `layout/r1_top_png.py` | picture: `python3 r1_top_png.py <gds> <png> [px]` |
| `layout/r1_top.png` | picture of try d |
| `lvs/pnl2cdl.py` | copy of the G1 `g1_padring` converter; bus ports expanded |
| `lvs/make_top_cdl.py` | top reference: `r1_ctrl` CDL + block CDLs of record + empty placeholders + ring (flat) + decaps |
| `lvs/run_lvs_top.sh` | LVS: `stock` or `limits` |
| `flow/run_try.sh` | one try: `sh .../run_try.sh <try> [gen cdl lvs antenna main maximal density stock]` |
| `flow/run_drc_set.sh` | DRC main, maximal, density, antenna with the stock decks |
| `flow/drc_summary.py` | counts per rule, class (a)/(b) |
| `flow/lvs_report.py` | circuit, net, device and pin pairs of an LVS database |
| `flow/write_run_json.py` | `run.json` of a try |
| `flow/probe_*.py` | probes of the ring and macros used for the plan |
| `reports/placement.csv`, `reports/connectivity.md`, `reports/integration_checklist.md` | deliverables 1, 4 and 5 |
| `reports/runs/asm-20261021-{a,b,c,d}.json`, `reports/runs/asm-20261021-d_lvs_report.txt` | copies of the `run.json` of each try and the LVS pair report of try d |

Reproduce try d from the repository root (POSIX shell):

```
G1_CPUSET=116-119; export G1_CPUSET
G1_RESULTS_ROOT=<results root>; export G1_RESULTS_ROOT
G1_WORKDIR=.; export G1_WORKDIR
sh designs/r1-joint/blocks/r1_top/flow/run_try.sh asm-20261021-d
```

# r1_adc_sar: SAR logic and frame sequencer of r1_adc (standard-cell sub-macro, decision D21, track T2j)

State: **hardened, sign-off clean in a 439.0 × 23.12 µm box (five rows); the D21 box of 439 × 15 µm is not met**
(2026-10-27, run of record `t2j-ll-h2312-h`, release `release-t2j-h`). RTL and gate level (SDF, slow and fast) are
bit-exact against the behavioural model on the r5 vectors. The closed-loop mixed-signal run: section "Status". All
numbers in this file come from simulation or from layout tools. Nothing is measured.

`r1_adc_sar` is the silicon form of the behavioural SAR logic `r1_sar5_logic` of `r1_adc` revision 5
(`schematic/r1_adc_r5.spice`), plus the frame sequencer that the r5 decks take from ideal sources
(`sim/r5/gen_timing_r5.py`) and the full-chip testbench takes from a model (`r1_top/tb/rtl/r1_chip_dig.v`, part 2a).
It sits inside the `r1_adc` macro at its north edge. ADC layout B5 integrates it (`INTEGRATION.md`). The `r1_ctrl`
contract (INTERFACES.md "ADC → ctrl") does not change, with one exception: the new input `cur_trk` (open issue S1).

## Contents

| Path | Content |
| --- | --- |
| `rtl/r1_adc_sar.v` | RTL of record (one module; four `sg13g2_dlhq_1` latches, two `sg13g2_dlygate4sd3_1` delay cells and five dummy-load buffers are instantiated under `SYNTHESIS`) |
| `tb/tb_sar_vec.v`, `tb/run_vec.sh` | Vector testbench (RTL or gate level with SDF) with a model of the `r1_gate` frame protocol |
| `tb/vec_extract.py`, `tb/vec/` | Vector extraction from a behavioural full-core run; stimulus, schedule, case record |
| `tb/compare.py`, `tb/results/` | Comparison with the behavioural model; one JSON per case and run |
| `sim/tb_beh_mux.cir`, `sim/tb_beh_fc.cir` | The r5 mux-sequence and first-conversion decks of record with the SAR boundary saved |
| `sim/tb_beh_sar.cir`, `sim/vec/` | `r1_sar5_logic` alone on the extracted vectors (behavioural reference) |
| `sim/run_ng.py`, `sim/runs/<id>/` | ngspice runner and run records (`run.json`, deck with the `<G1_RESULTS_ROOT>` placeholder) |
| `flow/config.yaml`, `flow/r1_adc_sar_pnr.sdc` (PnR), `flow/r1_adc_sar.sdc` (sign-off), `flow/gen_pins.py`, `flow/pins.*`, `flow/run_harden.sh` | LibreLane hardening |
| `flow/sta/` | sign-off STA (`signoff_sta.tcl`) and window analysis (`sta_windows.tcl`, `.sdc`, `.py`) per corner, `run_sta.sh`; summaries in `flow/sta/results/<id>/` |
| `flow/release.sh` | copies GDS, LEF, netlists, SDF, SPEF to `<G1_RESULTS_ROOT>/r1_adc_sar/release-<tag>/` with `SHA256SUMS` |
| `tools/v2spice.py`, `sim/gen_gl_deck.py`, `sim/tb_gl_mux.cir`, `sim/ms_compare.py` | gate-level SPICE netlist (PDK cell subcircuits), mixed-signal r5 mux deck, code comparison |
| `tools/check_pins.py` | pin check of the final DEF against `flow/pins.json` |
| `reports/` | sign-off metrics (`signoff_t2j-ll-h2312-h.json`), window table, pin check, B3 label dump |
| `INTEGRATION.md` | Placement, supplies, ground, LVS method for layout B5 |

## Specification

### Function of the behavioural model (`r1_sar5_logic`, per slice X = A, B)

1. Comparator clocks: `clkX = mclk AND winX`, `clkXb = NOT clkX` (`r1_cmp4`, decisions 1–13);
   `clknX = mclk AND winX AND NOT V0`, `clknXb = NOT clknX` (`r1_cmp5n`, decision 0 only; V0 = V flag of decision 0).
   `mclk` comes from the one-shot `r1_cmp4_clkgen`: low (comparator reset) for 0.91 / 1.38 / 2.27 ns
   (ff / tt / ss) after each `clk30` rising edge, high (evaluate) for the rest of the tick.
2. Decision k (k = 0…13) at the strobe `stbX_k`: P_k ← comparator output (k = 0: `r1_cmp5n` output `o?np`;
   k ≥ 1: `r1_cmp4` output `o?p`), threshold 0.6 V (`adc_bridge`); V_k ← 1 (k ≤ 12); N_k = V_k AND NOT P_k.
   So exactly one side switches. A comparator with no output at the strobe (metastable: both outputs below
   0.6 V) gives P = 0, so the N side switches.
3. CDAC lines: decision k drives bottom plate 12 − k: `cpX(12−k) = P_k`, `cnX(12−k) = N_k` (k = 0…12;
   decision 13 has no CDAC line). The line switches 0.16 ns after the strobe (flip-flop 80 ps + bridge 80 ps),
   that is 0.44 ns before the next `clk30` edge.
4. Flags P, V reset asynchronously while either track signal of the slice is high (`trkX0 OR trkX1`).
5. Raw word: at `latX` the 14 P flags are copied to the raw register; raw[13] = decision 0 (the first),
   raw[0] = decision 13. The raw register is not reset. Redundancy (D17/D18): 14 decisions, 12 + 2 redundant,
   weights per decision in `r1_ctrl` (`r1_adcw`); the logic does not combine them.
6. Timing (ideal sources, D18, `gen_timing_r5.py`): frame 22 ticks; sampling edge ts (track falls, `_cq`:
   0.3 ns after the edge); `win` ts + 1 ns … ts + 14 T + 1 ns; `stb_k` ts + (k + 1) T − 0.6 ns, 0.3 ns wide;
   `lat` ts + 14 T + 0.5 ns; track rises at ts − 8 T + 6 ns of the next frame of that input (slice B +1.5 ns).
   Start-up: one hold pulse of 33 ns on `trk*0` before the first frame (`_pre33`, INTERFACES.md first conversion).

### Function of `r1_adc_sar` (both slices, one sequencer: D18 converts both slices on one `adc_start`)

E0 = the `clk` edge at which `r1_ctrl` raises `adc_start` and `adc_hold` (encoder) or `is_smp` (current);
En = E0 + n ticks.

| Item | Behaviour | Same as the model |
| --- | --- | --- |
| Hold (sampling) | `hold = busy OR ((adc_hold OR is_smp) AND NOT done)`; the selected track switch opens when the request rises (combinational, E0 + ctrl clock-to-output + gate delay) | the model samples at E0 + 0.3 ns (`_cq` decks) |
| Comparator window | `win = hsd AND (adc_start OR wq)`, `wq` = a copy of `busy` in its own flip-flop (low fan-out, for the gate timing); `hsd` = hold request through two `sg13g2_dlygate4sd3_1` (0.55 / 0.8 / 1.3 ns ff / tt / ss, liberty), so the comparators start after the track switch has opened; closes at E14 | the model: ts + 1 ns … ts + 14 T + 1 ns |
| Comparator clocks | `clkX = mclk AND win`, `clknX = mclk AND win AND NOT fv0`, complements by inverters; `fv0` = V0 in its own flip-flop (`fv0 ← adc_start OR (fv0 AND NOT vd)`, equal for both slices) | identical function |
| Decision take | one level latch per comparator, transparent while its comparator clock is high, closed when it falls (the one-shot at E(k+1)); the decision flip-flops load the latch at E(k+1): decision 0 when `adc_start` is seen, decision k when `step = k` | the model samples 0.6 ns before E(k+1); see "Equivalence" for the difference |
| P/N rule | P_k ← latch; N_k ← NOT latch (two flip-flops, so no glitch); V0 = P_0 OR N_0 | N = V AND NOT P; identical values |
| CDAC lines | `cpX(12−k) = P_k AND busy`, `cnX(12−k) = N_k AND busy` (line 12: `AND wq`, because P_0 and the enable rise at the same edge); switch at E(k+1) + clock-to-output; all lines to 0 at E14 | the model: 0.44 ns before E(k+1); to 0 when track rises (E14 + 6 ns in the decks) |
| Valid and raw | `adc_valid_X` high E14 … E15 (one tick, r1_ctrl samples it at E15); `adc_raw_X` = P flags, raw[13] = decision 0; held until E16, then the flags clear | the model latches raw at E14 + 0.5 ns; the T10 model raises valid at E14 + 5 ns for one tick |
| Release | the track switch of the selected input closes at E14 (`done`), before `r1_ctrl` drops the request at E15 | as the decks and the T10 model (release at the latch) |
| Input choice | `sel0`/`sel1` flip-flops from `cur_trk` with one tick break before make; `trkX0 = NOT hold AND sel0`, `trkX1 = NOT hold AND sel1` | the decks choose by frame type; the T10 model by `cur_q` (ctrl `soon`, registered) |
| Start-up hold | a hold request without `adc_start` (r1_gate PRE_HOLD, 2 ticks) opens the track switch and no comparator window | the decks: 33 ns pulse on `trk*0` |
| Reset | `por_n` low: all flip-flops 0 (`sel0` = 1): track on in0, no window, CDAC lines 0, valid 0; release through a 2-flop synchroniser | the model tracks in reset (track high at t = 0) |

Glitch analysis of the outputs that the analog part samples or integrates (CDAC lines, track switches, comparator
clocks): every CDAC line is a flip-flop output ANDed with `busy`. At E1 `busy` rises while all flags are 0 except
decision 0, which rises with it. At E(k+1) one flag rises while `busy` is 1. At E14 `busy` falls while the flags are
constant. At E16 the flags clear while `busy` is 0. So at every edge at most one input of each AND changes, or both
change in the same direction. The comparator window has one hand-over at E1 (`adc_start` falls, `wq` rises).
A gap there is masked while `mclk` is low; this holds if `clk → wq` reaches the clock gates before `mclk` rises.
STA checks this at the gates (clock-gating checks, mclk rise per corner: "Timing"). The track switches change on the request edge, at E14 and on
`sel` changes, which are one tick apart (break before make).

### Ports

Domain of every pin: 1.2 V `VDD` / `VSS` (core supply of `r1_adc`).

| Pin | Dir | Edge | From / to | Function |
| --- | --- | --- | --- | --- |
| `clk` | in | N | oscillator net (same as `r1_ctrl` clk and the ADC clkgen) | sequencer clock |
| `por_n` | in | N | `r1_bias` `r1_por` | reset, low active |
| `adc_hold`, `is_smp` | in | N | `r1_ctrl` (`r1_gate`) | hold requests SIN/COS, ISA/ISB |
| `adc_start` | in | N | `r1_ctrl` | one-tick start, both slices |
| `adc_sel` | in | N | `r1_ctrl` | frame type; dummy load only (the input is chosen at track time) |
| `cur_trk` | in | N | **new**: `r1_ctrl` `soon` (registered), open issue S1 | 1: track in1 (ISA/ISB) while idle |
| `adc_valid_a`, `adc_valid_b` | out | N | `r1_ctrl` | one-tick valid per slice |
| `adc_raw_a[13:0]`, `adc_raw_b[13:0]` | out | N | `r1_ctrl` (`r1_adcw`) | 14 decisions, [13] first |
| `mclk` | in | S | `r1_cmp4_clkgen` | comparator one-shot |
| `oap`, `obp` | in | S | `r1_cmp4` `outp`, slice A / B | decisions 1–13 |
| `oanp`, `obnp` | in | S | `r1_cmp5n` `outp`, slice A / B | decision 0 |
| `oan`, `obn`, `oann`, `obnn` | in | S | the complementary comparator outputs | dummy load (`sg13g2_buf_1`), so both latch nodes see the same pin and route |
| `clka clkab clkna clknab clkb clkbb clknb clknbb` | out | S | comparator clock inputs | evaluate while high |
| `cpa[12:0] cna[12:0] cpb[12:0] cnb[12:0]` | out | S | CDAC bottom-plate drivers `r1_drv` | 1 = plate from VREF to GND |
| `trka0 trka1 trkb0 trkb1` | out | S | bootstrapped switches (`r1_bootsw`) | track while high |
| `VDD`, `VSS` | supply | Metal4 straps | ADC `vdd` / `vss` | 1.2 V |

Pin positions: `flow/pins.md` (generated with the die; north pins at the x of the r1_adc north pins of layouts
A–B3, south pins at the x of the slice pin each net connects to in layout B3).

### Timing requirements

| # | Requirement | Source of the number |
| --- | --- | --- |
| 1 | CDAC switch: `clk` edge → `cp`/`cn` at the macro pin shorter than the one-shot width minus 0.2 ns at the same corner: ≤ 0.71 / 1.18 / 2.07 ns (ff / tt / ss); the CDAC then settles during the comparator reset and the evaluation, the budget of the R2-4 settling metric (error sampled 25 ns into the tick, limit 0.25 LSB) | one-shot width: r1_adc README revision 4; R2-4: README layout B4 |
| 2 | Decision take: the decision latch closes before the comparator output starts to reset: `mclk` → latch gate shorter than `mclk` → comparator clock pin + comparator reset response (0.18–0.23 ns after the clock, behavioural decks) | sta_windows.tcl; `tb/vec/*.json` |
| 3 | Decision flip-flop hold: the flip-flop at E(k+1) loads the latch before it reopens (one-shot width after the edge) | sign-off STA, mclk rise per corner (0.95 / 1.42 / 2.31 ns) |
| 4 | Outputs to `r1_ctrl`: change ≥ 0.5 ns after the `clk` edge (all corners; the worst is fast) and settle ≤ 7.0 ns after it | `r1_ctrl/flow/r1_ctrl.sdc`; INTERFACES.md "ADC → ctrl timing" |
| 5 | Comparator clocks: `mclk` → `clk?`/`clk?b` with the true and complement edges close together (reported, no limit given) | sta_windows.tcl |
| 6 | Conversion ≤ 17 ticks from `adc_start` to the later `valid` (contract): 15 ticks (E0 to E15) | RTL |
| 7 | Track ≥ 250 ns before each sample at 30 MHz with PAIR_TICKS 22: release at E14 gives 8 ticks (267 ns) | RTL; r1_gate |

## Equivalence with the behavioural model

Method (chosen: vector comparison; co-simulation with `d_cosim` was not used because its digital side may lead the
analog time by up to 1.88 ns, r1_top tb README M7, which is larger than the strobe-to-edge window):

1. The two r5 decks of record are re-run with the SAR boundary saved: mux sequence e c e e at tt (`t2j-beh-mux-tt`,
   deck `sim/tb_beh_mux.cir` = run `t2-isa-tt` plus the `r1_refbuf5` bias pin), first conversion at ss / 125 °C /
   1.08 V, −0.90 V, 33 ns start-up hold (`t2j-beh-fc-ss125`, = run `t2-ff-ss-pre33`).
2. `tb/vec_extract.py` digitises `mclk` and the comparator outputs at 0.6 V (the bridge threshold). Strobe hold: for
   each decision the comparator output is held at its value at the behavioural strobe (E − 0.6 ns) until E + 1.0 ns.
   Reason: in the deck the model resets the decision-0 comparator at its own strobe (`clkna` falls with V0, 0.5 ns
   before E), and the `r1_cmp4` outputs start to reset 0.23–0.28 ns after E in response to the model's 30 ps clock
   gate. With `r1_adc_sar` the comparators are reset by its own clocks, so these edges move. Forced cases: the
   comparator output is set to "no output" (0.5 V in the PWL, 0 in Verilog) from E − 3 ns to E + 1 ns.
3. The behavioural `r1_sar5_logic` alone runs on the vectors in ngspice with the deck's ideal timing
   (`sim/tb_beh_sar.cir`); `r1_adc_sar` runs on the same vectors in Icarus with the `r1_gate` protocol model
   (`tb/tb_sar_vec.v`). Check: the SAR-only runs give the same 8 + 4 raw words as the full-core runs.
4. `tb/compare.py` compares at every tick at E + 10 ns and E + 20 ns: 52 CDAC lines, 8 comparator clocks, 4 track
   switches; and per frame and slice the 14 decisions and the valid tick (RTL valid at E14 ↔ model `lat` at E14).
   Expected differences, listed and counted, not hidden: the start-up hold (deck 33 ns pulse, ctrl 2 ticks: track
   only, ticks 3–5) and the end of the deck (the deck has no track edge after the last frame).

Results: section "Status".

## Status

Run of record: hardening `t2j-ll-h2312-h` (RTL sha256 in its `run.json`; = `rtl/r1_adc_sar.v`), sign-off STA
`t2j-sta-h-c`, release `<G1_RESULTS_ROOT>/r1_adc_sar/release-t2j-h/` (`SHA256SUMS`; GDS sha256 `70e2c5b7…`).

| Check | Result | Evidence |
| --- | --- | --- |
| Behavioural reference runs (full core) | done: mux tt 210 s, first conversion ss 94 s | `sim/runs/t2j-beh-mux-tt/`, `sim/runs/t2j-beh-fc-ss125/`; raw `<G1_RESULTS_ROOT>/r1_adc_sar/<id>/sar.raw` |
| SAR-only behavioural runs = full-core runs (raw words) | **passed**: mux 8/8, first conversion 4/4 words identical | `sim/runs/t2j-bsar-*-c/` |
| RTL equivalence, 4 cases (mux tt, mux tt with 5 forced decisions, first conversion ss, first conversion with 4 forced decisions), RTL of record | **passed**: mux 112/112 decisions, 8/8 valid ticks, CDAC 10 192 and comparator-clock 1 568 samples identical; first conversion 56/56, CDAC 5 616, clocks 864 identical; only the listed expected differences (track: start-up 4, end of deck 4 + CDAC 52 after the last frame) | `tb/results/t2j-rtl-f_*.json` (earlier RTL: `t2j-rtl-b_*`, `-c_*`, `-e_*`) |
| LibreLane hardening, 439.0 × 23.12 µm | **passed** for the physical flow (all steps complete). Exit code 2: the flow's own STA step used the SDC copy of the launch (one `mclk` waveform, 0.91 ns, at all corners; 3 ns `trk` bound) and reports setup −0.14 ns (typ) and −0.74 ns (slow), hold ≥ 0.096 ns. The sign-off STA of record is the next row | `<G1_RESULTS_ROOT>/r1_adc_sar/t2j-ll-h2312-h/` |
| Sign-off STA typ / fast / slow (nom RC from the final SPEF, `flow/r1_adc_sar.sdc`, mclk rise per corner) | **passed**: setup and hold slack ≥ 0 at all corners, 0 max slew / cap / fanout violators. Worst setup: fast 0.228 ns (clock gate `_179_`, window close), typ 0.366 ns (same), slow 0.518 ns (`cna[12]`); latch endpoints 0 by time borrowing. Worst hold: fast 0.096, typ 0.162, slow 0.309 ns (`_383_/D`) | `flow/sta/results/t2j-sta-h-c/signoff.json`; logs `<G1_RESULTS_ROOT>/r1_adc_sar/t2j-sta-h-c/` |
| Window analysis (timing requirements 1, 2, 4, 5) | **passed** (requirement 5 reported): table "Timing" | `reports/sta_windows_t2j-sta-h-c.md`, `flow/sta/results/t2j-sta-h-c/windows.json` |
| Magic DRC, KLayout DRC (LibreLane decks) | **passed**: 0 / 0; XOR Magic vs KLayout stream 0 | `reports/signoff_t2j-ll-h2312-h.json` |
| LVS (netgen, LibreLane) | **passed**: 0 errors, 0 unmatched pins / nets / devices | same |
| Antenna | **passed**: 0 violating nets and pins (one diode inserted) | same |
| PDK main / maximal DRC deck on the macro alone | **not run** (B5 runs it on the ADC with the macro, INTEGRATION.md § 6) | — |
| Pin check (final DEF against `flow/pins.json`) | **passed**: 110/110 pins on Metal2 at the planned x and edge, no extra pins | `reports/pin_check_t2j-ll-h2312-h.txt` |
| Gate-level SDF simulation, slow (`nom_slow_1p08V_125C`, max delays), 4 cases | **passed**: same counts as RTL | `tb/results/t2j-gl-h-slow_*.json` |
| Gate-level SDF simulation, fast, 4 cases | **passed**: same counts as RTL | `tb/results/t2j-gl-h-fast_*.json` |
| Mixed-signal r5 mux deck at tt with the gate-level netlist (PDK cell transistor netlists) | **failed** (bit-exact): 110/112 decisions and 8/8 valid ticks equal; 6/8 words identical. Frame 3, slices A and B: decision 13 differs (beh `…01` / `…10`, gate level `…00` / `…11`). The top-plate difference in that last tick stays within ±0.04 mV until the comparator kickback in the last 5 ns, so the input lies on the decision-13 boundary (analog tie, failure 15). Run time 4 144 s (limit 2 h). Probe with netlist `e`: 111/112 (frame 3 B only) | `sim/runs/t2j-ms-h-tt/` (`codes.json`), `sim/runs/t2j-ms-e-tt-d/`; raw `<G1_RESULTS_ROOT>/r1_adc_sar/t2j-ms-h-tt/sar.raw` |
| Supply current | estimated only: 0.44 mW at typ, OpenROAD vectorless (default activity) | `<G1_RESULTS_ROOT>/r1_adc_sar/t2j-ll-h2312-h/…/56-openroad-stapostpnr/nom_typ_1p20V_25C/power.rpt` |

## Area

| Item | Value | Source |
| --- | --- | --- |
| Box | 439.0 × 23.12 µm = 0.01015 mm² (five 3.78 µm rows, core y 3.78–22.68 µm) | `t2j-ll-h2312-h` |
| Synthesized cell area | 5 978 µm² (Yosys, AREA 0) | `06-yosys-synthesis/reports/stat.rpt` |
| Placed cell area | 7 038 µm² (402 cells; 3 507 µm² flip-flops and latches, 610 µm² timing-repair buffers), utilization 85.9 % | `reports/signoff_t2j-ll-h2312-h.json` |

Why five rows and not the D21 box: the logic needs 5 870–5 980 µm² before repair. A 15 or 16 µm box holds two or
three rows (at most 4 915 µm² of core; global placement 183 % and 122 %, `t2j-ll-h15-a`, `-h16-a`). The core bottom snaps to a multiple of
3.78 µm from the die origin, and the cell rails reach 0.22 µm past the row edge, so four rows need a 19.34 µm box
(core 3.78–18.90 µm). Four rows failed detailed placement after timing repair in every trial (`t2j-ll-h198-a`,
`t2j-ll-h1934-c`, `-d`, `-e`; the four-row trials ran with the RTL before `wq` / `fv0`, which is 105 µm² smaller). Synthesis strategies AREA 1–3 gave no smaller netlist
(`t2j-syn2-area_*`: 5 880 / 5 873 / 6 038 µm² for AREA 1 / 2 / 3). Five rows close at 85.9 %. So the smallest height
is **23.12 µm** (open issue S2).

Hardening trials (all under `<G1_RESULTS_ROOT>/r1_adc_sar/`):

| Run | Height (µm) | Result | Cause or change |
| --- | --- | --- | --- |
| `t2j-ll-h15-a`, `-h16-a` | 15.0, 16.0 | failed: GPL-0301 (183 %, 122 %) | three rows too small |
| `t2j-ll-h198-a` | 19.8 | failed: DPL-0036 | four rows |
| `t2j-ll-h1556-b`, `-h1934-b`, `-h2312-b` | 15.56, 19.34, 23.12 | failed: OpenROAD CTS signal 11 | gated `mclk` declared as a clock with sink clustering; PnR SDC without the `mclk` clock from `-c` |
| `t2j-ll-h1934-c`, `-h2312-c` | 19.34, 23.12 | failed: DPL-0036 | PnR SDC error: ctrl input → `trk` combinational path with input and output delay (−17 ns); false path from `-d` |
| `t2j-ll-h1934-d`, `-h2312-d` | 19.34, 23.12 | failed: DPL-0036 | 1.5 ns CDAC bound and `adc_raw` hold repair: +33 % area (95.7 %); CDAC bound 2.0 ns and raw hold multicycle from `-e` |
| `t2j-ll-h1934-e` | 19.34 | failed: DPL-0036 | four rows |
| `t2j-ll-h2312-e`, `-f`, `-g` | 23.12 | flow complete, physical checks clean; timing windows failed (`t2j-sta-e-*`, `t2j-sta-f-a`) | CDAC switch 0.79 ns > 0.71 ns at fast, window gate margin 0.02 ns: `busy` fan-out tree on the critical paths |
| **`t2j-ll-h2312-h`** | **23.12** | **run of record**: clean | RTL with `wq` / `fv0` flip-flops; PnR CDAC bound 1.5 ns |

## Timing

Sign-off STA: OpenSTA 2.7.0 (image `tapeoutbench-eda`) on `final/nl` + `final/spef/nom` with the PDK liberty of each
corner and `flow/r1_adc_sar.sdc`; `mclk` rise = 0.04 ns + one-shot width of the corner (fast 0.95, typ 1.42, slow
2.31 ns). Window analysis: `flow/sta/sta_windows.tcl` (arrival times per launch clock, `report_arrival`), same
netlist and RC. Run `t2j-sta-h-c`. All values simulated (STA), not measured.

| Corner | clk → CDAC line (req. 1) | clk → valid / raw (req. 4: valid ≥ 0.5, all ≤ 7.0) | mclk rise / fall → comparator clock pins (req. 5) | true / complement skew | window gates (clock-gating check slack, setup / hold) | latch close margin (req. 2) | ctrl request → `trk` fall (A / B) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| fast | 0.49–0.65 ns (≤ 0.71) pass | 0.90–1.11 / 0.44–0.50 ns pass | 0.33–0.73 / 0.32–0.60 ns | 0.25 ns | 0.228 / 0.146 ns pass | 0.16 ns pass | 0.34–0.36 / 0.49–0.52 ns |
| typ | 0.74–0.99 ns (≤ 1.18) pass | 1.34–1.70 / 0.66–0.76 ns pass | 0.50–1.12 / 0.49–0.91 ns | 0.40 ns | 0.366 / 0.268 ns pass | 0.16 ns pass | 0.50–0.53 / 0.74–0.78 ns |
| slow | 1.16–1.55 ns (≤ 2.07) pass | 2.14–2.70 / 1.05–1.19 ns pass | 0.80–1.78 / 0.77–1.44 ns | 0.63 ns | 0.710 / 0.475 ns pass | 0.15 ns pass | 0.82–0.86 / 1.21–1.26 ns |

Notes:

1. CDAC lines 11..0 are timed from their flag flip-flops; `busy` only enables them (it rises before their flags and
   falls at E14 after the last decision). The `busy` → line clear takes ≤ 2.86 ns (slow), limit one tick. Line 12 is
   timed from all launches.
2. `adc_raw_*` change ≥ 0.44 ns after the edge at fast, but only at E1–E14 and E16. `r1_ctrl` captures them at E15
   only, so the sign-off hold check on `adc_raw_*` moves back one cycle (multicycle −hold 1). `adc_valid_*` keep
   the 0.5 ns requirement (0.90 ns at fast).
3. Latch close margin = comparator clock pin fall (min) + 0.18 ns comparator response − latch gate fall (max); the
   latch hold time is ≤ 0 at all corners (liberty). The latch gate is the comparator clock net itself.
4. The sample instants of slices A and B differ by 0.16 / 0.25 / 0.41 ns (fast / typ / slow) because the two track
   drivers are at different distances from the request pins.

## Open issues

1. **S1 `cur_trk` has no driver in `r1_ctrl`.** The shared CDAC of each slice must track ISA/ISB before the current
   frame; only `r1_ctrl` knows when (`soon`). Without the pin a current frame converts SIN/COS. The full-chip
   testbench models the same signal (r1_top tb M2). Recommended: `r1_ctrl` 0.8 exports `soon` registered as
   `adc_cur_trk` (one output, north edge near `adc_start`); until then B5 ties `cur_trk` low and the current frames are
   not valid.
2. **S2 box height.** The macro is 23.12 µm high, not ≤ 15 µm (D21), and B4 gives a 10.7 µm free north band.
   Recommended: B5 extends the ADC box north by 23.12 µm to 439.0 × 205.42 µm and places the macro at (0, 182.3)
   (INTEGRATION.md § 1). The chip floor plan (`r1_top`) must accept the taller ADC. Alternative not taken: share the
   north rows with the clock generator band (needs a slice floor-plan change).
3. The comparator clocks reach their pins 0.33–1.78 ns after `mclk` (fast–slow), with up to 0.63 ns between a clock
   and its complement. No limit is given (requirement 5). The closed-loop check at tt is the mixed-signal run; ff and
   ss closed-loop runs are not run.
4. The CDAC lines switch 0.5–1.6 ns after the edge, against 0.44 ns before the edge in the behavioural model. The
   reference settling budget (R2-4, error at 25 ns into the tick) loses this time. B5 post-layout runs must include
   the gate-level macro to measure it.
5. The closed-loop run differs from the behavioural run in decision 13 of one frame (an analog tie, Status). A
   comparison that tolerates ties needs the top-plate residue of the behavioural run, which `t2j-beh-mux-tt` did not
   save. Not run: the closed-loop runs at ff and ss.

## Failures and mistakes

| # | What happened | Class | Fix or state |
| --- | --- | --- | --- |
| 1 | First SAR-only runs (`t2j-bsar-*` without suffix): the deck placeholder `VEC_pwl.inc` was not replaced (`\b` word match does not split at `_`) | tooling | placeholder is now the full file name (`-b` runs) |
| 2 | First RTL comparison (`t2j-rtl-a`): decision 0 differed in 6 of 8 slice frames. The deck's decision-0 comparator resets 0.1 ns before the edge in response to the behavioural model's own early `clkna` close; the open-loop vectors carried that edge into the RTL | verification-gap | strobe hold in `vec_extract.py` (`-c` / `t2j-rtl-b`); the closed-loop check is the mixed-signal run |
| 3 | The first RTL opened the comparator window during the start-up hold (one tick, no decision taken); not in the model | spec-ambiguity | window gated with `adc_start OR busy` (RTL of record) |
| 4 | `reports/b3_sar_labels.txt` was first parsed with the datatype column as x; all south pins got x = 25 µm | functional-bug | parser fixed before any hardening run |
| 5 | The D21 box was taken as feasible before any synthesis: 15 µm holds two or three rows, the logic needs five | estimation | five rows (23.12 µm) recorded as the smallest height; open issue S2 |
| 6 | The core bottom snaps to a multiple of 3.78 µm from the die origin (IFP-0028); the first trials assumed a 0.44 µm margin | tooling | core from y 3.78 µm, die = rows + 0.44 µm |
| 7 | The synthesis-strategy study `t2j-syn-*` ran without the strategy: `flow/run.sh` does not pass the caller environment into the container | tooling | options are arguments of `run_harden.sh`; study repeated as `t2j-syn2-*` |
| 8 | OpenROAD CTS crashed (signal 11) with the gated `mclk` as a clock and sink clustering (`t2j-ll-h*-b`) | tooling | PnR SDC without the `mclk` clock (`flow/r1_adc_sar_pnr.sdc`); CTS on `clk` only, no clustering |
| 9 | PnR SDC: the ctrl request → `trk` path had both an 18.81 ns input delay and a 20.81 ns output delay (−17 ns); the repair grew the area 15 % (`t2j-ll-h2312-c`) | functional-bug | false path, delay measured in the window analysis |
| 10 | Sign-off SDC: comparator inputs against `clk` and comparator-clock outputs against `mclk` paired the wrong edges (−21 / −22 ns, `t2j-ll-h2312-e`); one `mclk` waveform for all corners failed the slow gating checks | functional-bug | inputs against the `mclk` rise; no output delay on the comparator clocks; `mclk` rise per corner in the sign-off STA |
| 11 | Hardening `-e`/`-f`/`-g` met the physical checks but missed timing requirement 1 at fast (0.79 > 0.71 ns) with a 0.02 ns window-gate margin: `busy` drove the gates and line 12 through a fan-out tree | functional-bug | `wq` and `fv0` flip-flops (RTL `t2j-rtl-f`, equivalence repeated) |
| 12 | The first window-close metric compared arrivals at different output pins and reported a false failure (`t2j-sta-h-a`, `-b`); `{gated clock}` was read as two group names | verification-gap | clock-gating checks of the sign-off STA at the gates (`t2j-sta-h-c`) |
| 13 | Gate-level simulation: Icarus needs `sg13g2_udp.v`, `-ginterconnect` and `-Tmax`; runs `t2j-gl-e-slow`, `-b`, `-c` are invalid | tooling | `tb/run_vec.sh` fixed (`t2j-gl-e-slow-d`, `t2j-gl-h-*`) |
| 14 | Mixed-signal deck: the antenna cell needs the `dantenna` model, `pnl.v` lists `VDD`/`VSS` twice, `.param VDD=VDD` was substituted, and the KLU operating point fails (`t2j-ms-e-tt`, `-b`, `-c`) | tooling | antenna cell left out of the simulation netlist, single supply ports, SPARSE solver (`t2j-ms-e-tt-d`, `t2j-ms-h-tt`) |
| 15 | The mixed-signal check was planned as bit-exact; frame 3 converts an input on the decision-13 boundary, so the last decision depends on the comparator timing and kickback (two runs with different netlists give different ties) | numerical | recorded as failed bit-exact with the cause; the behavioural reference did not save the top plates (verification-gap, open issue 5) |

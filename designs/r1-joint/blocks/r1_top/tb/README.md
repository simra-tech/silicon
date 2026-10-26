# R1 full-chip functional testbench (track T10)

State (2026-10-26, end of the track budget): no test deck has completed. Deck 4 (`t10-t4-sch-c`) and deck 2 with the R2 fix (`t10-t2-sch-c`) run on; `run_tb.py` writes `results/<run-id>.json` and the verdict when each ends. The status table is not yet updated for them. This file is updated after each test. The status table is in
[`../README.md`](../README.md), section "Full-chip testbench, schematic level".

## 1. What it is

One ngspice 46 transient deck per test. The deck holds the whole chip at the schematic level of record, the board
(supplies, encoder head, shunts, loads) and a host and bench master. The chip netlist is `r1_chip.sp`. The block
cells come from one view include, `views/sch.inc`. The digital macro comes from `views/ctrl_rtl.inc`.

## 2. Method for the digital macro (choice and reason)

Chosen: the **r1_ctrl revision 0.5 RTL in one XSPICE `d_cosim` instance with the Icarus Verilog shim `ivlng`**.
This is the method of the G1 full-chip campaign (`designs/g1-guardian/blocks/g1_top/sim/run_top.py`,
`run_top_cdl.py`). Reasons:

1. It runs in the pinned container today (G1 used the same image).
2. The RTL is the 0.5 source of record, unchanged, compiled with `-DR1_CFG_FLOPS -DR1_CFG_GATED` as the r1_ctrl
   regression. A behavioural model would be a second implementation that can differ from the RTL.
3. The Yosys netlist with the PDK cell models was rejected: about 30 000 cells at transistor level make the
   decks far slower than the 2 h limit, and 0.5 has no hardened netlist of record (0.6 hardening is open).

Bridges: core inputs through `adc_bridge` with one 0.6 V threshold (no unknown state, G1 numerical note 7); pad
probes at 1.65 V; core outputs through `dac_bridge` at 0 / 1.2 V; master pad drives at 0 / 3.3 V.

What this method does not cover:

1. Gate delays, setup and hold of the digital macro (RTL is zero-delay). Covered by STA and gate-level simulation
   in `r1_ctrl` (0.4 done, 0.5/0.6 not run).
2. The supply current and the supply noise of the digital macro. The macro draws no current in these decks.
3. Analog loading of the digital pins of the macro (bridges have about 1 fF input load).

## 3. What the decks contain, and the MODEL and TESTBENCH parts

Real (schematic netlists of record, sha256 in every `run.json`): `r1_afe` revision E, `r1_adc` revision 5
(`r1_adc5_core`, `r1_reffilt5`, `r1_refbuf5` with bias pin `nb`), `r1_isense` revision 2, `r1_safe` revision 3
netlist, `r1_bgr`, `r1_bias` (with `r1_por`), `r1_osc` revision 2, `r1_t2f` (G1 revision 2 copy), `r1_gate_lv`,
7 x `r1_ls` (`g1_ls_up`), the PDK `sg13g2_io` pad cells of the pin map, `sg13g2_tiehi` for `osc_en`.

MODEL parts (no block owns them yet; each is a gap of the chip, listed as an open issue):

| # | Part | Where | Why |
| --- | --- | --- | --- |
| M1 | ADC sequencer: `adc_start`/`adc_sel`/`adc_hold`/`is_smp` to the `r1_adc5_core` timing ports (trk, win, stb, lat) with the revision-5 D18 timing of `gen_timing_r5.py`, and `adc_valid` | `rtl/r1_chip_dig.v` | `r1_adc` revision 5 has no sequencer; its decks drive these ports with ideal sources |
| M2 | `cur_trk`: the CDAC tracks ISA/ISB before the current strobe (ctrl `soon` window, by hierarchical reference) | `rtl/r1_chip_dig.v` | no pin carries this request today |
| M3 | isense auto-zero: `azh` = `az_win`, `az` = `az_win` stretched by 2 ticks | `rtl/r1_chip_dig.v` | ctrl has one `az_win`; isense needs two phases |
| M4 | `vcm2` (AFE output CM) and `vcm` (isense CM): ideal 0.6 V, 1 kOhm | `views/sch.inc` | the ADC revision 5 has no CM generator |
| M5 | raw decisions: decoded from the ADC netlist raw word (`rawa`, `rawb`) by B sources | `views/sch.inc` | the ADC netlist exports the word as one analog node |
| M6 | VREF buffer: ideal unity gain, 10 Ohm output, from `vref_bg` to `vref_l`; `r1_isense` and `r1_safe` take `vref_l`, T2F and the ADC filter keep `vref_bg` | `gen_chip.py` → `r1_chip.sp` | finding R1 (section 9): no block of record buffers the bandgap; without it `vref_bg` is 0.22 V |

TESTBENCH parts (not chip logic): the host/bench master `rtl/t10_master.v` (SPI host at 20 MHz, BiSS-C master at
10 MHz, reference clock for `OSC_COUNT`, shunt level selector, testbench reset pulse `tb_rst_n` for decks 2-5),
the board in `run_tb.py`, the monitors in `rtl/r1_chip_dig.v`.

Deviations:

| # | Deviation | Reason |
| --- | --- | --- |
| D1 | All pad cells use a deck-local copy of `sg13g2_io.spi` without the `dantenna` instances (G1 `--pads nodcn`) | the PDK `dantenna` model jumps at −3nVt and stalls transients (G1 numerical notes); PDK file unchanged |
| D2 | Decks 2-5 start from the operating point with the supplies on; `tb_rst_n` resets the macro | the POR delay of about 240 µs would use the whole wall-time budget of every deck; deck 1 runs the real ramp and POR |
| D3 | `TIMEOUT_TICKS` written to 64 in deck 2 | the 20 µs reset timeout costs simulated time; the BiSS logic is the same |
| D4 | `--hbt-selft0`: deck-local copies of the netlists that contain `npn13G2` (74 instances) with `selft=0` (no HBT self-heating) | the self-heating node of the PDK HBT model gives NaN temperatures and stops the OP and the ramp (F4, F7); the electrical model is unchanged, only the thermal node is removed |
| D5 | `--osc ideal` in decks 2-5: `osc_clk` is an ideal 30 MHz pulse scaled by `v(vdd)` instead of the `r1_osc` netlist | the ring oscillator sets the time step of the whole deck (F8); deck 6 and deck 1 keep the real `r1_osc` |
| D6 | `--start op --nodeset vref_bg=1.045,pbias=2.297,pcasc=1.75,bgr_vbe=0.693`: decks 2-6 start from the operating point (values from `r1_bgr` run `bgr-op-20261020-b`, tt 27 °C) | start-up from 0 V aborts in the HBTs (F7); the nodeset is a guess only, the start-state criterion checks `vref_bg` at t = 0 |
| D7 | Compressed sequences: CS_N gap 300 ns (≥ 8 ticks); deck 2 without the final `ID` read (deck 1 reads `ID`); deck 3 with PWM period 64 ticks and two levels (0 and A 30 mV / B 80 mV); deck 4 with PWM period 100, duties 75, 3.6 µs resume windows, CLR and GATE_EN in one write; deck 6 with a 10 MHz reference (16 periods = 1.6 µs) | wall time (F8); each criterion keeps its specification limit |
| D8 | Clock and core-output edges 250 ps (were 100 ps / 80 ps) | a realistic clock-tree slew; no measurable change of the wall time (run `t10-diag-m6-a`) |
| D9 | Simulator options of decks 2-6: `method=gear maxord=2 reltol=2e-3 abstol=1e-10 vntol=1e-5 chgtol=1e-14 trtol=30` (were `reltol=1e-3 vntol=1e-6`) | about 1.25x faster (563 against 690 s per simulated µs, runs `t10-diag-opt-b`/`-a`). `trtol=30` has no effect: XSPICE sets `trtol` to 1 (log line "Reducing trtol to 1 for xspice 'A' devices"; G1 numerical note 6); this is why `t10-diag-trtol-a` changed nothing. `abstol=1e-9 chgtol=1e-13` were faster (355 s/µs) but abort in `xu_bgr.xqd1` (F11, run `t10-diag-opt-c` at 0.264 µs). Newton tolerance on a 1 V node is 2 mV + 10 µV; the criteria are ≥ 1 % (test 3), 0.25° (≈ 0.4 % amplitude, test 2) and ns-scale delays (test 4). Not cross-checked against the tight options on a full deck (O3) |
| D10 | `gmin=1e-10` in deck 3 runs `-c`, `-d` (default 1e-12); `-d` also `method=trap` | aid against the `xu_bgr.xqd1` abort (F11); 100 pA at 1 V across each junction, against µA branch currents |

## 4. Tests and pass criteria

| Test | Deck | Pass criterion (source) |
| --- | --- | --- |
| 1 power-up | `--test 1` | `por_n` rises after both rails are up; VREF and the bias line settle (within 1 % of the final value) before `por_n`; oscillator 28-32 MHz at code 22 (r1_osc revision 2 band); macro out of reset; `ID` reads the RTL value over SPI |
| all of 2-6 | — | start state: `vref_bg` at t = 0 within 1.00-1.09 V (on-state of `r1_bgr`; F9); master sequence reaches its DONE line |
| 2 encoder | `--test 2` | per-pair `MEAS_ANGLE` residual after a constant ≤ ±0.25° el (spec §4 electronic accuracy); SPI `POS` residual ≤ ±0.64° el (spec total target); one BiSS-C frame with ACK, START, CRC match |
| 3 current | `--test 3` | `I_A`/`I_B` code steps (level 0 to A 30 mV, B 80 mV) within 1 % of 14 x ΔV_shunt / LSB (isense gain, ADC LSB from the measured reference) |
| 4 safety | `--test 4` | OC step to `FAULT_N` low and all gates < 1 V within 236 ns + 4 ticks + 1 µs; EN low to gates < 1 V within 1 µs; both clear sequences restore PWM |
| 5 thermal | `--test 5` at 27 and 125 °C | `TEMP` = f_T2F x window within ±1 count; f_T2F within ±3 % of the T2F record (1.600 / 2.110 MHz, G1 bandgap) |
| 6 oscillator | `--test 6` (real `r1_osc`) | `OSC_COUNT` = 16 f_osc / f_ref within ±1.5 counts, f_osc from the waveform |

## 5. Swap to the post-layout netlists

1. Write `views/pex.inc` with the same subckt names and pins as `views/sch.inc` (`r1_afe`, `r1_isense`,
   `r1_safe`, `r1_bgr`, `r1_bias`, `r1_osc`, `r1_t2f`, `r1_gate_lv`, `t10_ls`, `r1_adc`), each pointing at the
   extracted netlist of the block.
2. Run the same command with `--view pex`. Nothing else changes.
3. The MODEL parts M1-M6 stay in the chip netlist and in `rtl/r1_chip_dig.v`; they are the same in both views.
4. `views/pex.inc` holds `*PENDING` lines today. `run_tb.py` refuses to run while one exists.

## 6. Reuse of the previous attempt (2026-10-21, terminated)

Triage on 2026-10-26: the previous attempt chose the same method (d_cosim + Icarus). It left `gen_chip.py`,
`r1_chip.sp`, `views/sch.inc`, `views/ctrl_rtl.inc.tmpl`, `rtl/r1_chip_dig.v`, `rtl/tb_crc_reset.v` and two
probe runs under `<G1_RESULTS_ROOT>/r1_top/tb/` (`probe-cosim`, no result recorded; `crc-reset`: CAL_CRC of the
reset values 0xBA, `CAL_VALID` = 1). No runner, no deck and no result existed; `tb/results/` was empty.
The resume note named `win-ss125-*` runs; those runs belong to `r1_adc` (`<G1_RESULTS_ROOT>/r1_adc/`), not to T10.

Kept: the chip netlist content of `gen_chip.py`, `views/sch.inc`, `rtl/r1_chip_dig.v`, `rtl/tb_crc_reset.v` and
the CRC value. Changed: the level-shifter cell is `t10_ls` (`r1_isense.spice` defines its own `r1_ls` with other
pins: a name clash), the d_cosim port list is generated from one list (`gen_chip.py` also writes
`rtl/t10_top.v`), and the master is new. The previous files are kept in
`<G1_RESULTS_ROOT>/r1_top/tb/prev-attempt-20261021/`.

## 7. Commands and time per deck

Environment (POSIX shell): `G1_CPUSET=100; export G1_CPUSET`, `G1_RESULTS_ROOT=<G1_RESULTS_ROOT>; export G1_RESULTS_ROOT`,
`G1_WORKDIR=designs/r1-joint/blocks/r1_top/tb; export G1_WORKDIR`. Command (from the repository root):

```
flow/run.sh python3 run_tb.py --test N --run-id ID --osc ideal --start op --settle 1 --hbt-selft0 \
    --nodeset vref_bg=1.045,pbias=2.297,pcasc=1.75,bgr_vbe=0.693 [--temp 125] [--view pex]
```

Deck 6 uses `--osc tl`. The runner writes `run.json` (machine paths as `<G1_RESULTS_ROOT>`), runs `post_tb.py`,
writes `results/<run-id>.json` and exits 0 only if the verdict is passed. `post_tb.py <run-id>` reruns the
evaluation alone.

| Deck | Simulated time | Wall time, 1 thread (measured or estimated) |
| --- | --- | --- |
| 2 | 24 µs | estimate 3.8 h at 563 s/µs (exceeds 2 h: F8) |
| 3 | 20 µs | estimate 3.1 h (exceeds 2 h: F8) |
| 4 | 36 µs | estimate 5.6 h (exceeds 2 h: F8) |
| 5 | 25 µs | estimate 3.9 h per temperature (exceeds 2 h: F8) |
| 6 | 12.5 µs | not measured with the real oscillator and D9 |

## 8. Run log (all runs kept under `<G1_RESULTS_ROOT>/r1_top/tb/`, records in `runs/<run-id>/run.json`)

| Run | Question | Result |
| --- | --- | --- |
| `t10-smoke-a` | does the deck build | failed: iverilog rejects `wait ($realtime > …)` (F3); no simulation |
| `t10-smoke-b` | operating point with the supplies on | failed: OP not found (dynamic and true gmin stepping, then "timestep too small" in `xu_bgr.xqd1`, HBT temperature NaN); 47 993 equations, 26-40 ms per Newton iteration (F4) |
| `t10-speed-th1-a`, `-th2-a` | wall time, 1 vs 2 threads, ramp from zero, 3 µs | completed; 2 threads: matrix load 53 → 32 s (1.4x) |
| `t10-speed-t5-a`, `-t3-a` | decks 5 and 3 to 20 µs, trap | failed: "timestep too small" at 1.31 µs, `xu_t2f.x1.xqb2` (HBT) during the 2 µs rail ramp (F5) |
| `t10-speed-t3-b` | deck 3, gear | failed: same HBT at 1.39 µs (F5) |
| `t10-speed-t3-c`, `-e` | short rate probes | killed by PID after the rate reading; no result needed |
| `t10-speed-t3-d` | deck 3, loose tolerances, 10 µs ramp | failed: T2F HBT "timestep too small" at 4.76 µs (F7) |
| `t10-t1-sch-a` | deck 1, real ramps and POR | failed: T2F HBT "timestep too small" at 16.28 µs; rate about 800 s per simulated µs (F7) |
| `t10-speed-t3-f` | deck 3, `selft=0`, ramp | failed: "timestep too small" in `xu_bgr.xqd1` at about 5 µs (F7) |
| `t10-diag-nosafe-a`, `t10-diag-tol-a` | OP without `r1_safe` (diagnostic view) / with loose tolerances | failed: OP not found (gmin and source stepping) |
| `t10-speed-t3-g` | deck 3, OP start, `selft=0`, real oscillator | OP found; 1500-1680 s per simulated µs; killed by PID: the bandgap is off in this OP (F9) |
| `t10-diag-oscideal-a`, `-b` | ideal clock, OP start | `-b` completed (1 µs): 716 s per simulated µs, 95 % of the time points at the clock edges (about 53 per edge); `vref_bg` = 0.223 V: zero-current OP (F9). `-a` killed by PID for the same reason |
| `t10-diag-nodeset-a`, `-b` | does a bandgap nodeset give the on-state | no: `vref_bg` 0.2195 V in both (`-a` had the wrong syntax, F10); `pbias` 2.295 V shows the core is on: the output is loaded (R1) |
| `t10-diag-m6-a` | OP with the VREF buffer model M6, 0.3 µs, 250 ps edges | completed: `vref_bg` 1.0430 V at t = 0, `xu_adc.vrefo` 1.0482 V; 754 s per simulated µs (1 thread) |
| `t10-diag-trtol-a` | as `m6-a` with `trtol=30` | completed: 712 s per µs, same 1291 time points: the step is not set by the truncation error |
| `t10-diag-trtol-b` | as `m6-a` with the D9 options | completed: 355 s per µs, 507 time points |
| `t10-t4-sch-a` | deck 4 with the tight options | killed by PID after 6 min (replaced by `-b` with D9) |
| `t10-t4-sch-b`, `t10-t3-sch-a`, `t10-t2-sch-a` | decks 4, 3, 2 with M6 and D9 | failed: "timestep too small" in the `r1_bgr` HBT `xu_bgr.xqd1` (diode stack of the cascode bias) at 0.265, 0.866 and 0.264 µs; `vref_bg` steady at 1.050 V before the abort (F11) |
| `t10-diag-opt-a`, `-b`, `-c` | deck 3 to 1.5 µs: tight / reltol+vntol loose / abstol+chgtol loose | `-c` aborted in `xu_bgr.xqd1` at 0.264 µs; `-a` (690 s/µs) and `-b` (563 s/µs) passed 1.0 and 1.27 µs without abort, then killed by PID to free the CPUs |
| `t10-t4-sch-c` | deck 4 with M6 and D9 | running |
| `t10-t2-sch-b` | deck 2 with M6 and D9 | failed: `xu_bgr.xqd1` abort at 4.551 µs, after the reset, the `TIMEOUT` write and two encoder conversions. The waveform file was written. Evidence up to the abort: start state passed (`vref_bg` 1.0430 V); the pads and the AFE pass the signal (at 3.4 µs `souts` 0.343 V and `soutc` 0.380 V differential, as expected at 42° el); the RTL monitor gives `sin` = `cos` = 2063 in both conversions (expected about 2810 and 2900 at about 0.45 mV per LSB). See finding R2 |
| `t10-t3-sch-b` | deck 3 with M6 and D9 | failed: "timestep too small" in `xu_bgr.xqd1` at 0.8668 µs, the same time as `t10-t3-sch-a`: the abort depends on the time-point sequence (the 1.5 µs probe `-opt-b` with the same options passed this time). G1 saw the same `XQD1` abort in 14 variants (`designs/g1-guardian/blocks/g1_top/README.md`, numerical note 4) |
| `t10-t3-sch-c` | deck 3 with D9 and `gmin=1e-10` | failed: same `xu_bgr.xqd1` abort, later, at 1.784 µs |
| `t10-t3-sch-d` | deck 3 with `method=trap` (the G1 transistor-level method, `chgtol` 1e-14) and `gmin=1e-10`; `xqd1` nodes and currents saved | failed: same abort, earlier, at 0.5635 µs. `xqd1` is quiet before the abort (I_C 4.34 µA, `vd1` 1.4088 V, `vd2` 0.7044 V, drifting by < 1 mV/µs; clock low, no digital event) |
| `t10-t3-sch-e` | as `-c` plus `minbreak=1e-12` (test of near-coincident breakpoints) | failed: same abort at the same time as `-c`, 1.78417 µs. Breakpoints are not the cause; the abort is deterministic for one option set |
| `t10-t5-sch-27-a` | deck 5 at 27 °C, D9 | killed by PID after 4 min to free CPU 101 for the ADC diagnostic below (the deck could not end in the track budget) |
| `t10-diag-t2enc-b` | first conversion with the M1 strobe correction (2.6 µs) | completed: `seq_stb0` 0.60 ns before the clk30 edge (2039.857 / 2040.457 ns); the top plates converge (residue 0.8 mV slice A, 0.2 mV slice B); raw words 10900 / 11840 for 0.306 / 0.410 V at the sampling edge: (raw − 8192) ratio 0.742 against input ratio 0.746. R2 fix confirmed |
| `t10-t2-sch-c` | deck 2 with the R2 fix, M6, D9 | running at the end of the track budget (started 20:21 local; estimate 6-7 h) |
| `t10-diag-t2enc-a` | deck 2 to 4.3 µs with the ADC top plates, raw words, reference and sequencer nodes saved | completed (no abort): raw words 8191 in both slices, top plates not converged, strobes 0.54 ns late (F13). Reason: the RTL monitor of `t10-t2-sch-b` shows `sin` = `cos` = 2063 in the first two encoder samples (3.41 and 4.14 µs), with 0.25 V and 0.43 V differential at the pads |

## 9. Failures and mistakes

| # | What happened | Class | Fix |
| --- | --- | --- | --- |
| F1 | The resume note named `win-ss125-*` runs and a driver log as the previous T10 work; they are `r1_adc` runs. The previous T10 attempt had no results. | coordination | Triage recorded in section 6 |
| F2 | The previous `views/sch.inc` defined the chip cell `r1_ls (in out vdd vdda vss)`; `r1_isense.spice` defines its own `r1_ls (in vdd vdda vss out outb)`. One of them would silently win. | verification-gap | Cell renamed `t10_ls`; `run_tb.py` refuses a deck with duplicate subckt names |
| F3 | `wait ($realtime > t)` is not legal in Icarus (empty sensitivity). | tooling | `#(t - $realtime)` |
| F4 | The full-chip operating point with the supplies on does not converge (HBT self-heating NaN in `r1_bgr`, then gmin stepping fails). | numerical | All decks start at 0 V and ramp the rails (deviation D2) |
| F5 | trap and then gear aborted in the T2F HBT during a 2 µs rail ramp. The core outputs of the bridges were 1.2 V while VDD was still ramping (the level shifters saw an input above their supply). G1 had recorded that T2F decks need gear; the first probe used trap. | numerical / planning | gear by default; core outputs scaled by `v(vdd)/1.2`; 10 µs ramp (the ramp of the `r1_bias` start-up record) |
| F6 | The task asks for `ID` = 0x5204. That is RTL 0.4; the 0.5 RTL of record returns 0x5205 (register map 0.5). | spec-ambiguity | Criterion 0x5205, recorded |
| F7 | The rail ramp aborts in an HBT in every variant (T2F without `selft=0`, `r1_bgr` with it). No deck reached the end of the ramp. | numerical | decks 2-6 start from the OP (D6); deck 1 is partial (section 9) |
| F8 | The wall-time estimate of the brief (each deck < 2 h on 3 CPUs) assumed the G1 rate. The R1 deck has 47 993 equations (G1: about 3x fewer) and the ideal clock alone costs 716 s per simulated µs. | estimation | ideal clock (D5), compressed sequences (D7); time per deck recorded in section 7 |
| F9 | The OP gave `vref_bg` = 0.22 V. I first took it for the zero-current state of `r1_bgr` and added a nodeset (run `t10-diag-nodeset-a` also had a wrong `.nodeset` syntax, `v(n=x)`). The nodeset did not change it (`-b`): `pbias` was 2.295 V, so the bandgap core was on and its output was loaded (finding R1). Two runs were made on that state before the node voltages were checked. | verification-gap | M6; `post_tb.py` checks `vref_bg` at t = 0 in decks 2-6 |
| F10 | `.nodeset` written as `v(vref_bg=1.045)` (no error from ngspice, no effect). | tooling | syntax `v(n)=x` |
| F11 | The first D9 options (`abstol=1e-9 chgtol=1e-13`) were chosen from one 0.3 µs probe. All three decks then aborted in `xu_bgr.xqd1` within 0.26-0.87 µs. | numerical / planning | option study `t10-diag-opt-a..c`: the abort follows the loose `abstol`/`chgtol`; D9 keeps them tight |
| F12 | Deck 3 aborts in `xu_bgr.xqd1` in five option sets (gear/trap, gmin, minbreak) at a fixed time per option set, from a quiet state: Newton does not converge at any step size. Likely cause (not proven): a derivative discontinuity of the VBIC quasi-saturation terms (`rci`, `vo`, `gamm`, `hrcf`) in a diode-connected HBT whose emitter is not at ground, crossed while the bandgap drifts slowly from the OP. G1 met the same device in 14 variants. The model card may not be changed. | numerical | open (O8) |
| F13 | MODEL M1 timed the ADC strobes from the analog-delayed `adc_start` (1.14 ns after clk30), so every decision was sampled 0.54 ns after the comparator reset; deck 2 gave constant ADC words. Found from the RTL monitor, then confirmed with saved top plates. | verification-gap (testbench) | `T10_SEQ_LAT` correction; run `t10-diag-t2enc-b` |

## 10. Findings on the chip (from the testbench)

| # | Finding | Evidence | Owner / next step |
| --- | --- | --- | --- |
| R1 | **No VREF buffer in the chip.** `r1_bgr` drives `vref_bg` with a source of about 180 kΩ (r1_bgr noise section). The chip netlist connects it directly to the `r1_safe` threshold string (252 kΩ, 4.2 µA) and to the `r1_isense` pedestal resistors (104 kΩ units; the isense netlist states "buffered; ideal source in this step"). The OP gives `vref_bg` = 0.22 V instead of 1.045 V; the OC thresholds and the isense pedestal scale with it. The `r1_bgr` README lists the load row as not run. | runs `t10-diag-oscideal-b`, `t10-diag-nodeset-b` (loaded, 0.2195 V) and `t10-diag-m6-a` (buffered, 1.0430 V) | functional-bug, chip level: a VREF buffer (or a buffered output of `r1_bgr`) for the resistive loads is needed; the testbench uses the ideal model M6 until then |

## 11. Open issues

| # | Issue | Class |
| --- | --- | --- |
| O1 | VREF buffer missing in the chip (R1). All results use the ideal model M6. | functional-bug |
| O2 | Deck 1 (power-up) does not complete: the ramp aborts in an HBT, and the POR delay (about 240 µs) is about 50x the deck budget. Power-up, `por_n`, reset exit from POR and the oscillator start are not verified at chip level. | numerical / estimation |
| O3 | D9 options are not cross-checked against the tight options on one full deck. | verification-gap |
| O4 | Decks 2-5 use an ideal clock (D5) and `selft=0` HBTs (D4). | verification-gap |
| O5 | `views/pex.inc` is a template: extracted netlists of `r1_safe` (full block), `r1_t2f`, level shifters, `r1_gate_lv`, `r1_adc` (no layout of record) and the top wiring do not exist. | coordination |
| O6 | MODEL parts M1-M5 (ADC sequencer, `cur_trk`, isense auto-zero phases, CM sources, raw-word decode) have no block of record. | coordination |
| O8 | `xu_bgr.xqd1` (VBIC, diode-connected, emitter on `vd2`) aborts the transient in a reproducible way (F12). A fix needs either a model-side answer (PDK issue) or an accepted deck-local numerical aid. | numerical |
| O7 | Every deck exceeds the 2 h budget (3.1-5.6 h at 563 s per simulated µs). Decks 5 (27 and 125 °C) and 6 did not run in the 8 h track budget: the three CPUs ran decks 2-4. | estimation |

Finding R2 (cause found: testbench bug in MODEL M1, not a chip bug). In deck 2 both ADC slices returned 2063 (raw
word 8191) for any input. Run `t10-diag-t2enc-a` shows why: the top plates do not converge (differential 0.306 V
at the sampling edge, still 0.30 V after 14 decisions; the first CDAC step moves the plates the wrong way), and the
strobes reach the ADC 0.54 ns **after** the clk30 edge (`seq_stb0` 2040.997 ns, clock 2040.456 ns) instead of
0.6 ns before it (`gen_timing_r5.py`). M1 timed the strobes from `adc_start`, and `adc_start` reaches the analog side
1.14 ns after the clock edge (d_cosim output latency). The decision registers then sample the comparator after its
reset. Fix: M1 subtracts `T10_SEQ_LAT` = 1.14 ns from the strobe and latch times (`rtl/r1_chip_dig.v`). Run
`t10-diag-t2enc-b` confirms the fix (first conversion: residue below 1 mV, raw-word ratio within 0.5 % of the input ratio). Interface note for the real sequencer: the strobe position
must hold 0.6 ns before the clk30 edge with sub-ns accuracy; a sequencer clocked from the same clk30 must
account for its clock-to-output delay.

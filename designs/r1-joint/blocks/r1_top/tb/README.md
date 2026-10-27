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
| M7 | Co-simulation time: Icarus cannot step back. When ngspice rejects a step, the shim reports "time reversal" and the digital side keeps its later time. Measured lead: up to 1.88 ns, mean 0.5-0.85 ns, 9-77 events per deck (runs `t10-t1b-fast-b`, `t10-t3-fast-b`, `t10-t4-fast-b`, `t10-t4-fast-a`, `t10-diag-t2enc-b`) | ngspice `d_cosim` + Icarus shim | the ADC strobe window (0.3-0.9 ns before the clk edge) is smaller than this lead; `post_tb.py` measures the strobe in the analog domain, so a moved strobe shows as a failure. Third budget: an output event that the shim returned in a step that ngspice then rejects is lost (the HDL cannot repeat it): `seq_valid` (F22) and strobes (F24). Cause: the d_cosim default output delay (about 1 ns) lets a second output event replace a pending one; fixed with `delay=1e-12` (section 13.3). `post_tb.py` counts the analog edges per conversion (handshake integrity criterion) |

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
| D11 | `--t2f-off`: the T2F enable input is held at VSS in decks without a T2F criterion (1b, 2, 3, 4, 6); the ctrl `t2f_en` output (reset 1) still drives its level shifter, loaded by 1 MΩ | the T2F comparator HBTs abort the transient in the fast view (F15); the T2F is checked in deck 5 |

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
| F14 | All first-budget chip decks included the working-tree `r1_afe.spice` (revision F work of another track), not the revision E of record; `run.json` recorded its sha but nothing compared it with the record. | process-hygiene | `PINNED` sha table in `run_tb.py`; decks include `r1_afe_revE.spice`, `r1_bias_rev1d.spice` |
| F15 | With `abstol=1e-12 gmin=1e-15` the fast-view decks still aborted in `xu_t2f.x1.xqa1` (deck 4 at 3.912 µs, deck 1b at 2.686 µs). The 0.6 µs probe that cleared these options was too short again (same mistake as F11). | numerical / verification-gap | D11 for decks without a T2F criterion; deck 5 handled separately |
| F16 | Fast view: the `pcasc` source used VDDA − (2 VSG + VDS(MP1)) = VDDA − 2.550 V (0.75 V) in place of VDDA − (VSG + VDS(MP1)) = VDDA − 1.547 V (1.75 V, chip OP of `t10-diag-m6-a`). Only the T2F uses `pcasc`. Decks with the T2F held off (D11) are not affected. The fast-view T2F aborts of F15 ran with this wrong bias. | functional-bug (testbench) | fixed in `run_tb.py` (2026-10-26 23:15); T2F-alone decks `t10-diag-t2falone-a` (correct) and `-b` (old value) |
| F17 | Deck 1b `tstop` 8 µs was set without timing the host sequence (2 µs wait, then six 1.575 µs SPI frames: about 12.5 µs). The `FAULT` read did not happen. | estimation | rerun to 13 µs, or pipeline the reads |
| F18 | The T2F alone (`g1_t2f` rev 2, ideal fast-view rails, enable step at 1 µs) aborts in `x1.xqa1` 0.24-0.58 µs after the enable at `reltol` 2e-3, 1e-3, 5e-4 and 2e-4, with every other production option varied (`maxord`, `rshunt`, `vntol`, `abstol`, `method=trap`, no `klu`). It runs at `reltol=1e-4`, the value of the T2F block decks (1.624 MHz at 27 °C). The `pcasc` error F16 does not change it. `reltol` cannot be changed during a run (stop/resume test: same time points). | numerical | test 5 runs on the thermal subset at `reltol=1e-4` (section 12.6); decks 2-4 keep D11 |
| F19 | Deck 3 (`t10-t3-fast-b`): the ADC sequencer model M1 stopped after the conversion that started at 12.94 µs; no conversion followed, so `I_A`/`I_B` kept the level-0 values (821/823 → 811) and both step criteria failed. The isense outputs were correct (level 0: −0.560 V on both channels; level 1: A −0.140 V, B +0.559 V; gain 14 as specified). Time reversals came at every strobe of that conversion (13.04-13.34 µs). Cause (most likely, not observed directly): a clock edge delivered twice gave a period near zero, a delay became negative, and Verilog took it as a very large delay. | verification-gap (testbench, M1 with M7) | periods below 20 ns ignored, delays clamped at zero (`rtl/r1_chip_dig.v`). The fix did **not** cure it: rerun `t10-t3-fast-c` (20 µs, deck 9257 s) stopped after the third conversion (`adc_start` last at 3.475 µs, `seq_stb13` last at 3.940 µs; no PWM edge, no `is_smp`; SPI still answers, `I_A`/`I_B` read 0). The negative-delay cause is therefore not confirmed. Deck 2 rerun `t10-t2-fast-b` with the same change stopped at the same conversion (START 3.507 µs in both decks), so the change itself causes this early stop; it is reverted (`rtl/r1_chip_dig.v` = HEAD, sha `9bc7ff1e…`). Decks `t10-t4-safe-a/-b` used the changed file; their ADC is a stub, so the change has no effect there. **Correction (third budget, section 13):** the HEAD model with handshake monitors (`t10-diag-hs-head-a`) stops at the same conversion, so the change was not the cause. The cause is a lost `d_cosim` output event (F22). The change returns as F23 |
| F20 | Deck 4 (`t10-t4-fast-b`, 36 µs, deck 11 634 s): the gates never switched, so the OC step was never applied (master waits for `GATE_A`). Cause: the sequence wrote `CMP_THR_A` = 0x3F2C (THR_NEG_A 63) and left THR_NEG_B at its reset value 63. NEG cell code c = 63 − THR_NEG = 0 gives the cell threshold −VREF, so NEG is active at zero current (`cmp_neg_a`, `cmp_neg_b` = 1.2 V from t = 0 in decks 3 and 4). FAULT bits 1 and 3 latch at the reset exit, and `CLR` keeps a bit whose source is active, also when it is masked. | functional-bug (testbench) | THR_NEG 0 on both channels (`rtl/t10_master.v`), `tstop` 38 µs; rerun `t10-t4-safe-a` |
| F21 | Deck 4 `tstop` 38 µs (36 + one added SPI write) did not cover the last 3.6 µs clear window, which ends at 39.3 µs (the gate waits add time). The last criterion is not run. | estimation | rerun `t10-t4-safe-b` with `tstop` 40.5 µs |
| F22 | The ctrl frame stopped because one `seq_valid` output event of the macro did not reach the analog side (O10). | verification-gap (testbench, co-simulation) | the ctrl takes the valid inside the macro (section 13.3) |
| F23 | The sequencer model re-measured the clock period inside a conversion; a late or doubled clock edge gave a wrong or negative delay (stop in `t10-t4-safe-vb-a`; strobes moved 4.7 ns in the subsets). | functional-bug (testbench model) | period frozen per conversion as the mean of 7 periods, delays limited at zero (F23b) |
| F24 | Macro output events (strobes, `seq_valid`, one master `MA_SCLK` pulse) were lost when a second output event came within about 1 ns: the default d_cosim output delay. | tooling | `delay=1e-12`, `T10_SEQ_LAT` 0.141 ns (`t10-diag-hs-dly-b`: no loss) |

## 10. Findings on the chip (from the testbench)

| # | Finding | Evidence | Owner / next step |
| --- | --- | --- | --- |
| R1 | **No VREF buffer in the chip.** `r1_bgr` drives `vref_bg` with a source of about 180 kΩ (r1_bgr noise section). The chip netlist connects it directly to the `r1_safe` threshold string (252 kΩ, 4.2 µA) and to the `r1_isense` pedestal resistors (104 kΩ units; the isense netlist states "buffered; ideal source in this step"). The OP gives `vref_bg` = 0.22 V instead of 1.045 V; the OC thresholds and the isense pedestal scale with it. The `r1_bgr` README lists the load row as not run. | runs `t10-diag-oscideal-b`, `t10-diag-nodeset-b` (loaded, 0.2195 V) and `t10-diag-m6-a` (buffered, 1.0430 V) | functional-bug, chip level: a VREF buffer (or a buffered output of `r1_bgr`) for the resistive loads is needed; the testbench uses the ideal model M6 until then |
| R3 | **`FAULT` reset value 0x1900, not 0x1800.** With `EN_STO_IN` high from t = 0, bit 8 (STO) is latched at the reset exit: the EN synchroniser `u_sen` (`r1_sync2`, default `RST_VAL = 0`) gives `en_s` = 0 for two ticks, and the latch takes `~en_s` as a cause. | run `t10-t1b-sub-a` (`FAULT` read 0x1900); RTL `r1_safe.v` lines with `u_sen` and the cause latch | `r1_ctrl`: `RST_VAL(1)` on `u_sen` (the combinational gate-off path does not use `en_s`), or a register-map change |
| R4 | **Reset value of THR_NEG trips NEG.** `CMP_THR_A/B` reset 0x3F3F: for OC, THR 63 is the never-trip end; for NEG (c = 63 − THR_NEG) it is the always-trip end. After every reset FAULT bits 1 and 3 latch and stay until the host writes NEG thresholds; masking does not help (`CLR` keeps active sources). The register map lists the threshold write as host step 1, so the chip can work, but the reset state is not fail-quiet and is asymmetric. | decks `t10-t3-fast-b`, `t10-t4-fast-b`: `cmp_neg_a/b` = 1.2 V at zero current with reset codes | `r1_ctrl` / register map owner: reset THR_NEG 0, or state the reset FAULT value with NEG set |

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
| O9 | Decks 2-4 run at `reltol=2e-3` (D9). The T2F needs `reltol=1e-4` (F18). The other block decks of record were not re-run at `reltol=2e-3` by this track; a block-level comparison at both values is not run | verification-gap |
| O10 | Closed in the third budget (section 13). The ADC handshake stop is a lost `d_cosim` output event (`seq_valid`), not a chip-contract problem; the D18 frame (22 ticks, 733 ns) is confirmed. Fix F22: the ctrl takes the valid inside the macro. Lost strobe and master events (F24: `seq_stb13`, `seq_stb6`, one master `MA_SCLK` pulse): cause is the about 1 ns default `d_cosim` output delay; fixed with `delay=1e-12` (`t10-diag-hs-dly-b`: no loss). Decks before this fix (`t10-t3-fast-d`, `t10-t2-fast-d`) carry the loss; `post_tb.py` flags every affected conversion | verification-gap (testbench) |
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

## 12. Second budget (2026-10-26 evening): fast view, speed, power-up split

All results in this section use the ideal VREF buffer model M6. Decision D20 (PLAN.md section 2a) makes the buffer
a new `r1_bias` revision 2 output `vref_b`; M6 stays until that output exists.

### 12.1 Netlists of record (pinned)

The working tree holds revision work of other tracks: `r1_afe.spice` is revision F work (sha `44b7b406…`) and
`r1_bias.spice` is revision 2 work (two new pins `vref`, `vref_b`). The decks now include the committed
netlists of record: `r1_afe_revE.spice` (sha `4a84a3d8…` = HEAD `r1_afe.spice`) and `r1_bias_rev1d.spice` (sha
`3fa56d92…` = HEAD `r1_bias.spice`). `run_tb.py` holds a `PINNED` sha table and refuses a deck whose input
differs. All first-budget chip decks used a working-tree `r1_afe.spice` that was not the record (F14).

### 12.2 Speed: what dominates (test 3 deck, 0.6 µs after the OP, ideal clock, 1 thread unless stated)

| Run | Digital macro | bgr/bias/POR | Time points | s per simulated µs |
| --- | --- | --- | --- | --- |
| `t10-speed2-sch-rtl` | RTL co-simulation | real | 1945 | 622 |
| `t10-speed2-sch-static-c` | static (DIAGNOSTIC) | real | 1687 | 494 |
| `t10-speed2-fast-static-c` | static (DIAGNOSTIC) | behavioural | 1687 | 487 |
| `t10-speed2-fast-static-th3` | static, 3 threads | behavioural | 1687 | 297 |
| `t10-abort-fast-a` | RTL, `abstol=1e-12 gmin=1e-15` | behavioural | 1913 | 573 |

Findings:

1. The co-simulation costs about 25 % (15 % more time points, plus the bridge evaluation).
2. Replacing `r1_bgr`, `r1_bias` and the POR saves 1-2 %: they are about 2 % of the 47 990 equations.
3. The rest is the analog netlist itself at about 2800 time points per µs (about 47 per 30 MHz clock period),
   at about 0.17 s per time point. Matrix load dominates (`r1_safe` holds 5146 of about 7500 devices).
   Correction (section 12.7): `r1_safe` is not the only large term. With the AFE and ADC as stubs and `r1_safe` +
   `r1_isense` real, the deck runs at about 350 s per simulated µs (1 thread, shared host), about half the full rate.
4. Three threads give 1.64x. This is the main lever within the allowed options. Each production deck now runs with
   2 or 3 threads.

### 12.3 Fast view (`--fast`)

| Block | In the fast view |
| --- | --- |
| `r1_bgr` | `vref` = ideal 1.0449 V (27 °C) / 1.04397 V (125 °C); `pbias` = VDDA − VSG, `pcasc` = VDDA − 2 VSG − VDS(MP1) (record `bgr-op-20261020-b`, tt); `iptat`, `vbe`, `dvbe` unloaded (not connected in the chip) |
| `r1_bias` | 11 ideal current sources from VDDA: 10.14 / 5.07 µA at 27 °C, 13.41 / 6.71 µA at 125 °C (record `bias-op-20261021-d`, tt) |
| POR | `por_n` = VDD from t = 0 (decks 2-6); in deck 1b a step at `--por-step` µs. The POR delay is the `r1_bias` record (197-247 µs) |
| everything else | real netlists of record: pads (nodcn, D1), AFE, ADC, isense, safe, gate, level shifters, T2F, ctrl (RTL), osc (ideal clock D5 in decks 1b-5; real in deck 6) |

Start: `--start op`. ngspice computes the operating point with the supplies on (fast view: converges in one
gmin-stepping pass), then the transient starts from it; `tb_rst_n` resets the macro (D2). Options of every
production deck: `method=gear maxord=2 reltol=2e-3 abstol=1e-12 vntol=1e-5 chgtol=1e-14 gmin=1e-15 itl4=100 klu
rshunt=1e12` (D9 revised); `run.json` lists them with `fast`, `ctrl`, `threads`, `bridge_delay_ps`, `m6_vref_buffer`.

### 12.4 The HBT abort

| Run | View | Result |
| --- | --- | --- |
| `t10-speed2-fast-rtl-b` (`selft=0`), `-c` (`selft=1`), `-d` (50 ps bridge delay) | fast, RTL, `abstol=1e-10` | "timestep too small" at 0.2329 / 0.2340 / 0.2329 µs in the T2F HBT `xu_t2f.x1.xqa1`; clock low, no saved node switching. Self-heating and the bridge delay are not the cause |
| `t10-speed2-fast-static-c` | fast, static macro | no abort to 0.6 µs (but the static macro also changes the circuit state: `t2f_en` = 0) |
| `t10-abort-fast-a` | fast, RTL, `abstol=1e-12 gmin=1e-15` | **no abort** to 0.6 µs |
| `t10-abort-fast-b` | fast, RTL, `reltol=1e-4 vntol=1e-7` as well | OP not found |

The abort moves from `xu_bgr.xqd1` (schematic view) to the T2F HBT (fast view). It follows `abstol`: with 1e-9 it
came earlier (F11), with 1e-12 and `gmin=1e-15` (the values of the `r1_bias` block decks, which never aborted) it
did not come in 0.6 µs. It came later in the production decks (deck 4 `t10-t4-fast-a` at 3.912 µs, deck 1b
`t10-t1b-fast-a` at 2.686 µs, both in `xu_t2f.x1.xqa1`, the T2F comparator input HBT). In the fast view the T2F holds
the only active HBTs. Decks without a T2F criterion therefore hold the T2F enable low (D11).

### 12.5 Power-up (test 1)

Deck 1a (`run_pwrup.py`, real `r1_bgr` + `r1_bias` rev 1d with `r1_por` + the `r1_bias` consumer loads; `r1_osc`
separately, because its 30 MHz edges set the step): rails ramp 0 → 3.3 V (VDDA, 10 µs from 1 µs) and 0 → 1.2 V
(VDD, 10 µs from 2 µs), start from 0 V (`uic`). The POR release is not simulated (197-247 µs, `r1_bias` record).
Deck 1b (`run_tb.py --test 1 --fast --start op --por-step 1`): `por_n` steps at 1 µs, the macro leaves reset and the
host reads `ID`, `STATUS`, `FAULT`.

### 12.6 The HBT abort: cause found in the T2F-alone deck, and the thermal subset

The T2F-alone deck (`g1_t2f` rev 2 only, 3 s per run) reproduces the chip abort in `xu_t2f.x1.xqa1`
(run `t10-diag-t2fopt-a`, `summary.txt`):

| `reltol` | other options | Result |
| --- | --- | --- |
| 2e-3 (production) | production; also without `maxord`, `rshunt`, `klu`; `vntol=1e-6`; `abstol=1e-13`; `method=trap` | abort at 1.28 µs (0.28 µs after the enable) |
| 1e-3 | production | abort at 1.58 µs |
| 5e-4, 2e-4 | production | abort at 1.59 / 1.28 µs |
| 1e-4 | production | **no abort** to 12 µs; 1.624 MHz |
| 1e-4 | T2F block-deck options (`gmin=1e-15 abstol=1e-13 vntol=1e-6 method=gear`) | **no abort**; 1.624 MHz |

With the enable high from t = 0 the T2F does not start (the operating point is a stable non-oscillating state;
runs `t10-diag-t2falone-a`, `-b`). With the enable step it starts in 0.28 µs. In the chip the ctrl reset value
`ANA_CTRL` = 0x0028 sets `T2F_EN` = 1 after the reset release, so the chip decks also have an enable step.

The whole chip at `reltol=1e-4` does not fit the budget. Test 5 checks only the path T2F → level shifter → ctrl
counter → SPI. The thermal subset (`--thermal-subset`, `run_tb.py`) keeps the pads, T2F, level shifters, gate,
oscillator, the fast-view bgr/bias and the ctrl RTL, and replaces `r1_afe`, `r1_isense`, `r1_safe` and `r1_adc` by
stubs (every pin to ground through 1 GOhm: comparator and ADC outputs read 0). Deck rate: about 37 s per simulated
µs at `reltol=1e-4`, 1 thread (probe `t10-diag-t5sub-a`, 4 µs, T2F at 1.624 MHz, no abort). The subset is not a
view for tests 2-4.

Open: the decks of tests 2-4 run at `reltol=2e-3` with the T2F held off (D11). The other blocks with HBTs
(`r1_bgr`) are behavioural in the fast view. This track did not re-run the block decks of record of the AFE, ADC,
isense or safe at `reltol=2e-3`. This is open issue O9.

### 12.7 Subset decks (tests 1b, 4, 5, 6)

| Option | Real netlists | Stubs (every pin to ground through 1 GOhm; `vcm`, `vcm2` keep MODEL M4) | Used for |
| --- | --- | --- | --- |
| `--thermal-subset` | pads, T2F, level shifters, gate, osc (ideal or real), ctrl RTL; bgr/bias in the fast view | `r1_afe`, `r1_isense`, `r1_safe`, `r1_adc` | test 1b (reset exit, `ID`, `FAULT`), test 5 (T2F), test 6 (`OSC_COUNT`) |
| `--safety-subset` | as above plus `r1_isense` and `r1_safe` | `r1_afe`, `r1_adc` | test 4 (OC, EN, clear) |

Reason: each of these tests uses only the listed path. The subsets let the T2F run at `reltol=1e-4` (F18) and cut
the deck time from about 600-700 s per simulated µs to 26 s (test 5), 55 s (test 1b), 155 s (test 6, real
`r1_osc`) and about 350 s (test 4, safety subset). Effects not in a subset deck: the ADC sampling load
(kickback) on the isense outputs, and the AFE and ADC supply current. Tests 2 and 3 need the AFE and the ADC; they
run on the full fast view.

### 12.8 Run log, second budget (all with M6; records in `runs/<run-id>/run.json`)

| Run | Test | View, options | Simulated | Deck time | Result |
| --- | --- | --- | --- | --- | --- |
| `t10-t1a-dc-a` | 1a | `run_pwrup.py --part dc`, real bgr + bias rev 1d + POR, `reltol=1e-4` | 40 µs | 13 s | passed |
| `t10-t1a-osc-a` | 1a | `run_pwrup.py --part osc`, real `r1_osc` | 20 µs | 317 s | passed (32.72 MHz) |
| `t10-t1b-fast-a` | 1b | fast, T2F on, production options | 2.686 µs of 8 | 1807 s | failed: HBT abort `xu_t2f.x1.xqa1` (F15, F18) |
| `t10-t1b-fast-b` | 1b | fast, D11 | 8 µs | 5515 s | 2 of 3 criteria passed; `FAULT` not read (F17) |
| `t10-t1b-sub-a` | 1b | thermal subset, `reltol=1e-4` | 13 µs | 717 s | failed: `FAULT` 0x1900 (R3); reset exit and `ID` passed |
| `t10-t2-fast-a` | 2 | fast, D11, 1 thread | 4.3 µs of 24 | 5073 s | stopped by the track (rate; F19) |
| `t10-t3-fast-a` | 3 | fast, T2F on | — | 1206 s | failed: HBT abort (superseded by D11) |
| `t10-t3-fast-b` | 3 | fast, D11, 2 threads | 20 µs | 10 495 s | failed: sequencer model stopped (F19) |
| `t10-t4-fast-a` | 4 | fast, T2F on, 3 threads | 3.912 µs of 36 | 1716 s | failed: HBT abort `xu_t2f.x1.xqa1` |
| `t10-t4-fast-b` | 4 | fast, D11, 3 threads | 36 µs | 11 634 s | failed: gates never on (F20, R4) |
| `t10-t5-sub-27-a` | 5 | thermal subset, `reltol=1e-4`, 27 °C | 25 µs | 650 s | passed |
| `t10-t5-sub-125-a` | 5 | thermal subset, `reltol=1e-4`, 125 °C | 25 µs | 716 s | passed |
| `t10-t6-sub-a` | 6 | thermal subset, real `r1_osc`, `reltol=1e-4` | 12.5 µs | 1939 s | passed |
| `t10-diag-t5sub-a` | 5 (probe) | thermal subset, 4 µs | 4 µs | 147 s | DIAGNOSTIC (T2F starts, no abort; verdict not used) |
| `t10-diag-t2fopt-a` | — | T2F alone, 12 option sets | 12 µs each | 1-24 s each | DIAGNOSTIC (F18) |
| `t10-t3-fast-c` | 3 | fast, D11, F19 change, 2 threads | 20 µs | 9257 s | failed: ADC handshake stopped after 3 conversions (O10) |
| `t10-t4-safe-a` | 4 | safety subset, D11, F20 fix, 1 thread | 38 µs | 8121 s | 8 passed, 1 not run (F21) |
| `t10-t2-fast-b` | 2 | fast, D11, R2 fix, F19 change (reverted), 3 threads | 24 µs | 9004 s | failed: 0 encoder pairs, ADC handshake stopped after 3 conversions (O10); SPI and BiSS frame worked |

## 13. Third budget (2026-10-27): ADC handshake (O10), tests 2-4 to completion, real VREF buffer

Every result names the VREF buffer: **M6** (ideal unity buffer) or **r1_vbuf** (the buffer of `r1_bias`
revision 2, commit ae4dfac95).

### 13.1 New runner options

| Option | What it does |
| --- | --- |
| `--vbuf real` | Takes `.subckt r1_vbuf` from `blocks/r1_bias/schematic/r1_bias.spice` (sha256 checked: `5511ea8d…`) into the run directory and replaces M6 by `XU_VBUF vref_bg vref_l ibvb VDDA VSS r1_vbuf`. The bias leg is an ideal current source `ibvb` (5.07 µA at 27 °C, the fast-view value). The T2F `vref` pin moves to `vref_l` |
| `--vdefine NAME` | Extra iverilog define (for example `T10_SEQ_F19`, `T10_VALID_BRIDGE`, `T10_STALL_TICKS`) |
| `--stall-abort` | The runner stops ngspice when the log has `T10MON STALL` (a frame open for 60 ticks) |
| `--current-subset` | Test 3 only: `r1_afe` and `r1_t2f` as 1 GΩ stubs. Measured: not faster than the fast view (the ADC dominates), so no result uses it |
| `--cosim-delay S` | `d_cosim` output delay, default 1e-12 s (F24 fix); with it the runner sets `T10_SEQ_LAT` = 0.141 ns. `0` = not set (d_cosim default, about 1 ns) |
| `--cosim-irrev N` | Sets the `d_cosim` parameter `irreversible=N` (O10 test only) |
| frozen ctrl RTL | The runner compiles the ctrl from `<G1_RESULTS_ROOT>/r1_top/tb/ctrl_rtl_0.5` (r1_ctrl RTL 0.5, f65d55c49, sha256 checked), because track T5g changes the tree copy to revision 0.7. `run.json` field `ctrl_rtl_dir` |

### 13.2 Handshake monitors (`rtl/r1_chip_dig.v`, section 3b)

The model prints `T10HS` lines: sequencer start (`SEQ`), model valid (`SVAL1`, `SVAL0`), analog valid at the
macro input (`VA1`/`VB1` with the raw word), ctrl conversion start and frame number (`CSTART`), and the valid as
the ctrl samples it (`CSEEN`). `T10MON STALL` marks a frame open for `T10_STALL_TICKS` (60) ticks. `T10MON
LOSTEV` marks a model `seq_valid` rise that did not come back through the analog `adc_valid_a` in 20 ns.
`T10MON CLKPER` marks a clock period outside 30-37 ns. `post_tb.py` has the criterion "ADC handshake integrity"
in tests 2 and 3: analog strobe and latch rises per started conversion, lost valid events and stalls.

### 13.3 O10: cause and fix

1. Reproduction on 5 µs test-3 decks from the operating point (3 threads, about 40 min each). The F19 variant
   (`t10-diag-hs-f19-a`, `-b`) and the HEAD model (`t10-diag-hs-head-a`) stop at the same conversion (frame 3,
   start 3.507 µs). The F19 change is therefore not the cause (correction of the second-budget text, F19).
2. In frame 3 the model `seq_valid` rose at 3945.624 ns. The analog `seq_valid` and `adc_valid_a` did not rise
   (raw file of `t10-diag-hs-f19-b`: rises only at 2479.7 and 3213.1 ns). The ctrl frame generator closes a frame
   only when it has seen the valid of both slices (D18), so the frame stayed open.
3. Mechanism (M7): when the HDL output changes, the shim stops the HDL and returns the change at the HDL time.
   If ngspice then rejects that step, the event is rolled back. Icarus cannot step back, so the change is lost.
4. Fix **F22** (testbench): the ctrl takes `adc_valid_a/b` from the model `seq_valid` inside the macro. The
   analog `adc_valid_a/b` nets stay for observation. `-DT10_VALID_BRIDGE` restores the old path. Check
   `t10-diag-hs-f19-c`: the valid at 3945.6 ns is lost on the analog side (`LOSTEV`), and frames 4 and 5 start.
5. Fix **F23** (testbench): the sequencer model re-measured the clock period on every clock input inside a
   conversion. In `t10-t4-safe-vb-a` it stopped inside conversion 2 (no `SVAL1`); a negative delay is a very long
   delay in Icarus. The period is now frozen at the start of a conversion (20-50 ns, else 33.333 ns), and every
   delay is limited at zero.
   **F23b**: one clock edge that the shim delivers 0.34 ns late (subset decks: period 33.670 ns at the conversion
   start) moved all 14 strobes by up to 4.7 ns when the period of one cycle was frozen. The model now uses the mean
   of the last 7 periods. In the full fast view the measured period is 33.329-33.334 ns (`t10-t2-fast-d`).
   The thermal subset runs with `T10_VALID_BRIDGE` by default (frames stop after frame 1 with the ADC stub, as in
   the second-budget subset results).
6. Finding **F24** (testbench, open): strobe events are also lost. In 5 µs decks `seq_stb13` reached the ADC in
   2 of 4 conversions (`t10-diag-hs-f23-a`, 1 thread; `t10-diag-hs-irr1-a`, `irreversible=1`, 2 threads) and in
   3 of 4 (`t10-diag-hs-f19-c`). `seq_stb0`, `seq_stb6`, `seq_lat` and the valid were complete in these short decks;
   the 20 µs test-3 deck `t10-t3-fast-d` also lost `seq_stb6` in 2 of 19 conversions (a mid-word decision: the word is
   wrong by more than 1 LSB). `irreversible=1`
   gave no change. `seq_stb13` clocks only the LSB decision register (`AFPa13`, no DAC bit), so a lost
   `seq_stb13` gives a raw-word error of at most 1 LSB of 14 bits. The decks of tests 2 and 3 save all 14
   strobes and the latch, and the integrity criterion lists every short strobe.
   The loss also hits testbench outputs: in the test-5 subset one master `MA_SCLK` pulse (2377.5-2402.5 ns)
   was lost 1.3 ns after a `seq_stb10` event, so the `T2F_WIN` write did not happen and `TEMP` read 0
   (`t10-t5-sub-27-vb-a`, `-m6-b`, `-m6-c`, `-vb-b`). Two output events of the macro within about 1.5 ns are the
   common condition of every loss seen.
7. Cause and fix of F24 (testbench): the `d_cosim` output delay. Without the `delay` parameter, every macro
   output reaches the analog side about 1 ns after the HDL event (this is most of the 1.14 ns latency of R2). In
   every loss seen, a second output event of the macro came less than about 1.5 ns after the lost one, so the
   pending output was replaced. Run `t10-diag-hs-dly-b` (`delay=1e-12`, strobe latency define
   `T10_SEQ_LAT` = 0.141 ns, 5 µs, 3 threads, 2618 s): all 14 strobes, the latch and the valid in every
   conversion (4 of 4; the same deck without the change: `seq_stb13` 2 of 4), strobe position 0.596-0.601 ns, raw
   word 10458-10459 in all four conversions (with the 1 ns delay: 10304-10459, so conversions with a lost
   strobe gave wrong words). `run_tb.py` now sets `delay=1e-12` and `T10_SEQ_LAT=0.141` by default
   (`--cosim-delay 0` restores the old set-up). A 1 ps step warning ("output scheduled with impossible delay",
   one at 10 ps) is harmless.
8. Chip-level contract: not affected. The D18 frame (22 ticks, `CSTART` 733 ns apart: 2040.5, 2773.8, 3507.1 ns),
   the current pair at the centre strobe and the first-conversion hold are as specified. O10 is a testbench
   (co-simulation) finding, not a chip finding.

### 13.4 Real VREF buffer (`--vbuf real`) against M6

| Test | Run with r1_vbuf | Against M6 | Difference |
| --- | --- | --- | --- |
| 1b subset | `t10-t1b-sub-vb-b` (13 µs, 363 s) | `t10-t1b-sub-a` | none in the criteria: reset exit, `ID` 0x5205, POR/CAL passed; `FAULT` 0x1900 failed in both (R3). `vref_l` mean 1.04497 V against `vref_bg` 1.04490 V (+0.07 mV), range 1.04447-1.04549 V. T2F output mean 0.5889 V (M6: 0.5885 V) |
| 5 thermal subset, 27 °C | `t10-t5-sub-27-vb-c` (25 µs, 1 thread, F23b) | `t10-t5-sub-27-a` | none: `TEMP` = 14 in both (expected 13.86 ± 1); f_T2F 1.62395 MHz, +1.478 % against the record (M6: 1.62406 MHz, +1.485 %): −0.007 % |
| 5 thermal subset, 125 °C | `t10-t5-sub-125-vb-a` (25 µs, 1 thread, F23b) | `t10-t5-sub-125-a` | none: `TEMP` = 18 in both (expected 18.21 ± 1); f_T2F 2.13439 MHz, +1.156 % (M6: 2.13459 MHz, +1.165 %): −0.009 % |
| 4 safety subset | `t10-t4-safe-vb-a` (40.5 µs, 1 thread, 8360 s) | `t10-t4-safe-b` | none: all 10 criteria passed in both. OC threshold 69.806 mV, `FAULT_N` 165.507 ns, gates 277.686 ns, EN low 85.258 ns: equal to M6 within 0.01 ps. `vref_l` time-weighted mean 1.04495 V (+0.05 mV), rms deviation 0.56 mV. Two dips to 1.0218 V (−23 mV, 23 ns above 5 mV, 49 ns above 1 mV) at 3.676 µs and 5.242 µs, the two `CMP_THR` writes (register 0x36, 0x37: the comparator tap codes change); no dip at the OC step or at EN low |

Result: with the D20 buffer in place of M6, tests 1b, 4 and 5 (27 °C and 125 °C) give the same verdicts and the same numbers. The
`vref_l` load steps at the threshold writes are the only visible effect. Tests 2 and 3 run with M6 in this
budget (the decks were started before the r1_vbuf result; one deck each fits the CPU budget).

### 13.5 Run log, third budget (records in `runs/<run-id>/run.json`)

`rtl/r1_chip_dig.v` changed during the budget (monitors, F22, F23, F23b). Each `run.json` holds the sha256 of the
file that the deck compiled (`inputs_sha256`).

| Run | Test | View, options | VREF buffer | Simulated | Deck time | Result |
| --- | --- | --- | --- | --- | --- | --- |
| `t10-t4-safe-b` | 4 | safety subset, D11, F20 fix, 2 threads | M6 | 40.5 µs | 5980 s | passed (10 of 10) |
| `t10-diag-hs-f19-a` | 3 | F19 variant, monitors, 3 threads | M6 | 5 µs | 2168 s | DIAGNOSTIC (O10 reproduction) |
| `t10-diag-hs-f19-b` | 3 | F19 variant, monitors, 3 threads | M6 | 4.3 µs | 1958 s | DIAGNOSTIC (valid lost at 3945.6 ns) |
| `t10-diag-hs-head-a` | 3 | HEAD model, monitors, stall abort | M6 | 5.47 µs | 4087 s | DIAGNOSTIC (same stop as F19 variant; stall abort) |
| `t10-diag-hs-f19-c` | 3 | F19 variant + F22, 3 threads | M6 | 5 µs | 2401 s | DIAGNOSTIC (frames 4, 5 start; stb13 3 of 4) |
| `t10-t1b-sub-vb-a` | 1b | thermal subset | r1_vbuf | — | — | failed: empty netlist (runner bug: a variable shadowed the deck list; fixed) |
| `t10-t1b-sub-vb-b` | 1b | thermal subset, `reltol=1e-4` | r1_vbuf | 13 µs | 363 s | same as M6: `FAULT` 0x1900 (R3, expected until ctrl 0.7); reset exit, `ID`, POR/CAL passed |
| `t10-diag-hs-f23-a` | 3 | F22 + F23, 1 thread | M6 | 5 µs | 3864 s | DIAGNOSTIC (no lost valid; stb13 2 of 4) |
| `t10-diag-hs-irr1-a` | 3 | F22 + F23, `irreversible=1`, 2 threads | M6 | 5 µs | 2673 s | DIAGNOSTIC (same as f23-a) |
| `t10-t4-safe-vb-a` | 4 | safety subset, D11, F20 fix, F22, 1 thread | r1_vbuf | 40.5 µs | 8360 s | passed (10 of 10), equal to M6 |
| `t10-t3-sub-a` | 3 | current subset (AFE stub), F22 + F23, 1 thread | M6 | 1.347 µs of 19.6 | 1238 s | failed: HBT abort `xu_t2f.x1.xqa1` (F18; the T2F is now a stub in this subset; the subset is not faster, so not used) |
| `t10-t5-sub-27-vb-a` | 5 | thermal subset, F22 + F23 | r1_vbuf | 25 µs | 305 s | failed: `TEMP` 0 (lost `MA_SCLK` pulse, F24; not a buffer effect) |
| `t10-t5-sub-27-m6-b` | 5 | thermal subset, F22 + F23 (control) | M6 | 25 µs | 299 s | failed: `TEMP` 0 (same cause) |
| `t10-t5-sub-27-m6-c` | 5 | as `-m6-b` + T2F edge counters | M6 | 25 µs | 326 s | DIAGNOSTIC (T2F edges reach the ctrl; the `T2F_WIN` write is missing) |
| `t10-t5-sub-27-vb-b` | 5 | thermal subset, valid bridge, F23 | r1_vbuf | 25 µs | 362 s | failed: same lost SCLK pulse (frame 1 strobes) |
| `t10-t5-sub-27-vb-c` | 5 | thermal subset, valid bridge, F23b | r1_vbuf | 25 µs | 358 s | passed: `TEMP` 14, f_T2F +1.478 % |
| `t10-t5-sub-125-vb-a` | 5 | thermal subset, 125 °C, valid bridge, F23b | r1_vbuf | 25 µs | 388 s | passed: `TEMP` 18, f_T2F +1.156 % |
| `t10-t3-fast-d` | 3 | fast, D11, F22 (F23 not yet), 2 threads, runner paused so its timeout check did not stop the deck (T10-28) | M6 | 20 µs | 11 600 s | failed: `I_B` step +2.37 %, `I_A` step +9.1 % (level-0 word from a conversion with lost strobes), integrity failed (stb6 2, stb13 6 of 19) |
| `t10-diag-hs-dly-a` | 3 | `delay=1e-12` without the latency change | M6 | — | — | stopped by the track (strobe latency define not adapted) |
| `t10-diag-hs-dly-b` | 3 | F22 + F23b, `delay=1e-12`, `T10_SEQ_LAT=0.141`, 3 threads | M6 | 5 µs | 2618 s | DIAGNOSTIC: no lost event (all 14 strobes, latch, valid in 4 of 4 conversions) |
| `t10-t2-fast-c` | 2 | fast, D11, before F22 | M6 | — | — | stopped by the track (superseded by F22) |
| `t10-t2-fast-d` | 2 | fast, D11, F22 + F23, 3 threads, runner paused for its timeout check (T10-28) | M6 | 21.5 µs | 11 813 s | failed (testbench): words invalid, strobes lost (F24); BiSS-C frame and CRC passed; residual 128° el on invalid words |
| `t10-t3-fast-e` | 3 | fast, D11, F22 + F23b + F24 fix, 3 threads | M6 | 19.6 µs | running | not run yet (started 09:21) |
| `t10-t2-fast-e` | 2 | fast, D11, F22 + F23b + F24 fix, 3 threads | M6 | 21.5 µs | running | not run yet (started 09:51) |

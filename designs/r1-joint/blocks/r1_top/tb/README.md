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
(`t10-t3-fast-e` and `t10-t2-fast-e`: section 14.4.)

## 14. Fourth budget (2026-10-27): tests 2 and 3 with the F24 fix, current-word scale, stage separation

All decks in this section use M6 (ideal VREF buffer). Tests 1b and 4 are not rerun: F22-F24 change only the ADC
handshake and the macro output timing, and the safety and power-up paths do not use ADC words.

New runner options: `--t2f-stub` (decks 2 and 3: `r1_t2f` as a 1 GΩ output stub, because the held-off T2F
aborted both long decks on its HBT, T10-32) and `--encoder-subset` (test 2: `r1_isense` and `r1_safe` as stubs).
`post_tb.py` `adc_lsb` now uses the `r1_adc` revision-5 record (14.1).

### 14.1 The I_B +2.37 % scale error (third budget, `t10-t3-fast-d`): cause

1. The ctrl does not add a pedestal to the current word. `I_A`/`I_B` = the r1_adcw code of the current slice:
   `code = (Σ raw[i]·w[i] + 2) >> 2` with the reset (design) weights of `r1_regs` (`WNOM`, revision-3 weights × 4,
   which are also the revision-5 design weights).
2. The decks use the schematic `r1_adc` revision 5, not the extraction. The D16 amendment gain 1.058 is a
   post-layout number and does not apply here. The revision-5 record with the design weights is: code =
   2047.5 + v / LSB, LSB = 454.9 µV × VREF / 1.045 V, gain fit 0.99825 (`blocks/r1_adc/sim/results/r5/isa5_tt.json`).
   At the deck `vrefo` 1.0499 V: LSB 457.0 µV.
3. `post_tb.py` used LSB = 2 × 0.914 V × `vrefo` / 4096 = 468.6 µV. 0.914 V is the revision-3 full scale at VREF
   1.0 V, so this LSB is 2.5 % too large for revision 5. That is the +2.37 %.
4. Measured in `t10-t3-fast-d`: isense output 14.01 × shunt on both channels (level 0 −0.560 V; level 1
   A −0.1402 V, B +0.5593 V). Expected words with LSB 457.0 µV: level 0: 822.1; level 1 A: 1740.7; level 1 B:
   3271.4. Read: `I_B` 821 (level 0) and 3268 (level 1); `I_A` 1740 (level 1). The A level-0 read (762) is raw
   word 3072 from the conversion at 6.51 µs, which lost strobes (F24); the two level-1 A words and the B words
   give a common level-0 code of 823.
5. Both numbers for the `I_B` step (2447 codes for 80 mV × 14): against the revision-3 LSB +2.37 % (failed);
   against the revision-5 record LSB −0.15 % (passed, limit 1 %). With the expected step scaled by the simulated
   gain 0.99825 (2446.3 codes): +0.03 %. `post_tb.py` now uses the revision-5 record LSB
   (`adc_lsb`); `t10-t3-fast-d` re-evaluated: `I_B` −0.15 % passed, `I_A` +6.4 % failed (invalid level-0 word).
   The previous result file is kept in the run directory (`result_lsb_rev3.json`).
6. Post-layout (not simulated in these decks): the gain 1.058 would make the words 5.8 % larger. The host weight
   calibration (R2-11) removes it; with design weights a post-layout deck would fail the 1 % criterion by design.

### 14.2 Stage separation tool for test 2 (`enc_stage_check.py <run-id>`)

For every encoder conversion the tool compares, against the stimulus angle at the hold instant:
(1) the AFE held outputs (`souts`, `soutc`): angle and amplitude; (2) the code from the raw decisions with the
design weights against 2047.5 + v_AFE / LSB; (3) the r1_gate `sin_code`/`cos_code` (the `RAW_SIN`/`RAW_COS`
register source, registers 0x1D/0x1E) against the stage-2 codes; (4) the MEAS angle after the pair against atan2
of the stage-3 codes. The monitor values are the register sources, so no extra SPI reads (and no new deck) are
needed. Output: `results/<run-id>.stages.json`.

Check on `t10-t2-fast-d` (words with lost strobes): AFE angle residual 0.004° (constant −0.17°), amplitude
0.512 V; ADC codes differ from the AFE-based expectation by up to 1896 LSB (lost strobes); ctrl codes equal the
raw-word codes (0 difference in 22 pairs); CORDIC MEAS against atan2 of the codes ≤ 0.03° in 21 of 22 pairs,
0.185° in one. So in that deck the ADC conversion (strobe loss, F24) was the failing stage.

### 14.3 Results

1. Test 2, stage separation on `t10-t2-fast-e` (`enc_stage_check.py`, 15 encoder conversions, F24 fix):

   | Stage | Result |
   | --- | --- |
   | 1 AFE (pads → held AFE outputs) | angle residual 0.0023° max after a constant −0.17°; amplitude 0.5124 V (input 0.5 V) |
   | 2 ADC (AFE output → code, design weights, LSB 457.0 µV) | code error mean −4.0 (sin) / +6.0 (cos) LSB, max 7.4 LSB; code-angle residual 0.053° max after a constant −0.55° |
   | 3 ctrl codes (`RAW_SIN`/`RAW_COS` source) against stage 2 | 0 difference in 14 pairs |
   | 4 CORDIC (MEAS against atan2 of the codes) | 0.009° max |
   | 5 tracking loop (`POS`, `pos_out`) | not settled: error −41.6° at 3.4 µs, −19.7° at 6.3 µs, −8.2° at 10.0 µs, −3.3° at 14.4 µs (constant removed); velocity 616 of about 700 (3.6°/µs); POS_VALID 0 |

   The failing stage is the `r1_pos` tracking loop acquisition, not the AFE, ADC, weight or CORDIC path. The loop
   starts at velocity 0 at the reset and the error decays with about 4.5 µs time constant (reset `POS_CFG` 0x164:
   KP 2, KI 11). The master reads `POS` at 6.6 and 9.8 µs, inside the acquisition. The specification gives no
   acquisition time; the POS criterion needs reads after the loop settles (about 22 µs from the reset at the reset
   gains), or a higher loop gain written by the host. Not done in this budget (the deck would exceed 3 h).
2. Test 3: see 14.1 for the scale; `t10-t3-fast-e` level-0 reads `I_A` 821, `I_B` 823 (expected 822.1).
3. Test 2 after the lock (`t10-t2-fast-h`, master define `T10_T2_WAIT_NS` = 16 µs before the reads): all position
   criteria passed (row in `r1_top/README.md`). The ENC/MEAS pairs in this deck give the same stage figures as
   `-e`. The encoder subset runs 38 µs in 32 min on 3 threads (isense and safe dominate the full fast view).
4. Test 3 (`t10-t3-sub-b`): passed, `I_A` +0.11 %, `I_B` +0.10 %. The same `I_B` step against the revision-3 LSB
   would read +2.6 %, and against the record line scaled by the gain fit 0.99825, +0.27 %. The current subset
   (`--current-subset`: `r1_afe`, `r1_safe`, `r1_t2f` stubs) runs 19.6 µs in 16 min on 3 threads.
5. The full fast view of decks 2 and 3 aborts between 14 and 17 µs (T2F HBT, pad diodes `xp_sin_p`, `xp_isa_p`,
   fast-view POR source) at `tmax` 5 ns; the subsets with `tmax` 4 ns completed. Open: a full-view deck 2/3 to
   completion (not run in this budget).

### 14.4 Run log, fourth budget

| Run | Test | View, options | VREF buffer | Simulated | Deck time | Result |
| --- | --- | --- | --- | --- | --- | --- |
| `t10-t3-fast-e` | 3 | fast, D11, F22 + F23b + F24 fix, 3 threads | M6 | 14.06 µs of 19.6 | 7569 s | failed: HBT abort `xu_t2f.x1.xqa1` (T10-32). Before the abort: no lost event (14 conversions, all strobes); level-0 reads `I_A` 821, `I_B` 823 (expected 822.1); level-1 raw words 6946 / 13109 (codes 1740 / 3271) |
| `t10-t2-fast-e` | 2 | fast, D11, F22 + F23b + F24 fix, 3 threads | M6 | 14.93 µs of 21.5 | — | failed: HBT abort `xu_t2f.x1.xqa1` (T10-32). Before it: no lost event (18 conversions); MEAS residual 0.054° el **passed** (15 pairs, limit 0.25°); POS over SPI −19.9° / −7.5° at 6.6 / 9.8 µs failed (tracking loop not settled, 14.3); `STATUS` 0x0190; BiSS-C frame not reached |
| `t10-t3-fast-f` | 3 | as `-e` + `--t2f-stub`, 3 threads | M6 | 14.06 µs of 19.6 | 7684 s | failed: timestep too small at the same time as `-e` (14.0601 µs), now at the `SIN_P` pad diode `xp_sin_p.xi2.xd1`; level-0 reads as `-e` |
| `t10-t3-sub-b` | 3 | current subset (AFE, safe, T2F stubs), F22-F24, `tmax` 4 ns, 3 threads | M6 | 19.6 µs | 941 s | **passed**: `I_A` step +0.11 %, `I_B` +0.10 % (words 820/1740, 821/3274), no lost event |
| `t10-t3-sub-c` | 3 | as `-b`, `tmax` 3 ns | M6 | 17.18 µs of 19.6 | 773 s | failed: timestep too small at the `ISA_P` pad diode `xp_isa_p.xi2.xd1` |
| `t10-t2-fast-f` | 2 | as `-e` + `--encoder-subset --t2f-stub` (isense, safe, T2F stubs), 3 threads | M6 | 21.5 µs | 1148 s | failed: POS −19.9° / −7.5° (reads inside the acquisition), `STATUS` 0x0190, BiSS data null with nE = nW = 0 (no POS_VALID); MEAS 0.049° passed; BiSS CRC passed |
| `t10-t2-fast-g` | 2 | as `-f` + `T10_T2_WAIT_NS=16000` | M6 | 11.9 µs of 38 | — | failed: timestep too small at `b.xu_bias.bpor` (fast-view POR source) |
| `t10-t2-fast-h` | 2 | as `-g`, `tmax` 4 ns | M6 | 38 µs | 1922 s | position criteria passed (MEAS 0.045°, POS 0.50°, ST 0.42°, STATUS 0x01D0, BiSS CRC); nW = 0 failed (R3) |

## 15. Fifth budget (2026-10-27): ctrl revision 0.7, abort bisection, test 2 nW

### 15.1 Changes to the testbench

| Item | Change |
| --- | --- |
| `--ctrl-rev 0.7` | Compiles the ctrl from `<G1_RESULTS_ROOT>/r1_top/tb/ctrl_rtl_0.7` (r1_ctrl RTL 0.7, commit fdf0fcc0a, every file sha256-checked against `PINNED_RTL_07`) and adds `-DT10_CTRL07`. `run.json` fields `ctrl_rev`, `ctrl_rtl_dir`. Default stays 0.5 |
| `rtl/r1_chip_dig.v` | With `T10_CTRL07`, the 0.7 output port `cur_trk` drives the idle-track choice of the sequencer model (`t0_on` / `t1_on`). The hierarchical reference to `u_gate.soon` is used only for 0.5 |
| `rtl/t10_master.v` | With `T10_CTRL07`, the `CAL_CRC` shadow uses the 0.7 reset value of `CMP_THR_A/B` (0x003F, was 0x3F3F): CRC 0x46, not 0xBA. Test 2 writes `CTRL.CLR` after the lock wait (register map section 4, step 4; `T10_T2_NO_CLR` removes it). New define `T10_SCK_HALF_NS` (SPI half period, default 25 ns) |
| `post_tb.py` | The `ID` criterion uses the ctrl revision of the run (0x5205 for 0.5, 0x5207 for 0.7). The `FAULT` criterion names the STO bit |
| `--nodcp` | Bisection option: the deck-local pad copy also loses the `dpantenna` instances (6 more than the 7 `dantenna` of deviation D1). Extends D1 |
| `--por-fixed` | Bisection option: the fast-view POR source `Bpor por_n vss V=v(vdd)` becomes `Vpor por_n vss DC 1.2` |
| `--bridge-fixed` | Bisection option (static VDD only): the 111 core output bridges `V=v(q)*v(vdd)/1.2` become `V=v(q)` |
| `run.json` `command` | Records the real CPU list of the process (it was a fixed `100-102`, T10-36) |

### 15.2 Test 1b and test 3 with ctrl 0.7

- `t10-t1b-sub-07-a` (as `t10-t1b-sub-a`, ctrl 0.7): **passed**. Reset exit 1.041 µs, `ID` 0x5207, `FAULT` 0x1800 (POR and CAL set, STO bit 8 clear). Finding R3 is closed at chip level.
- `t10-t3-sub-07-a` (as `t10-t3-sub-b`, ctrl 0.7): **passed**. `I_A` step +0.11 %, `I_B` +0.10 %, 19 conversions, no lost event. `cur_trk` from the ctrl port is high for 0.70 µs before each PWM-centre strobe (PWM period 2.133 µs).

### 15.3 Abort bisection (priority 2)

1. All T10 decks already used the deck-local pad copy without `dantenna` (the G1 `--inpads nodcn` method, 7 instances). The remaining pad diodes are `dpantenna` (`dparea`), the element named in three aborts.
2. Two full-view bisection decks (`t10-t3-bis-a`, `--nodcp`; `t10-t3-bis-b`, `--por-fixed`) ran at 4.5-5 µs per hour on 1-2 threads. They could not reach 14 µs inside 3 h, so they were stopped (by PID) and the bisection used the faster decks that show the same failure (T10-38).
3. Results (each row changes one item against the row named in "Base"):

| Run | Base | Change | Result |
| --- | --- | --- | --- |
| `t10-t3-fast-f` | `t10-t3-fast-e` (abort 14.0601 µs, T2F HBT) | T2F stub | abort at the same time, now `xp_sin_p.xi2.xd1` (`dparea`) |
| `t10-t2-fast-h` | `t10-t2-fast-g` (abort 11.9 µs, `bpor`) | `tmax` 5 → 4 ns | completed (fourth budget) |
| `t10-t3-sub-d` | `t10-t3-sub-c` (abort 17.18 µs, `xp_isa_p.xi2.xd1`) | `--nodcp` | **completed**, test 3 passed |
| `t10-t2-fast-07-b` | `t10-t2-fast-07-a` (abort 24.01 µs, `xp_sin_p.xi2.xd1`) | `--nodcp` | abort 25.04 µs at `b.xu_ctrl.b_osc_trim1` |
| `t10-t2-fast-07-c` | `t10-t2-fast-07-a` | `d_cosim irreversible=1` | bit-identical to the base (no effect, T10-39) |
| `t10-t2-fast-07-d` | `t10-t2-fast-07-b` | `--por-fixed --bridge-fixed` | abort 25.09 µs, "cause unrecorded" |
| `t10-t2-fast-07-e` | `t10-t2-fast-07-a` | SCLK 12.5 MHz | abort 27.37 µs at `b_osc_trim1` |
| `t10-t2-fast-07-f` | `t10-t2-fast-07-a` | master CRC fix (digital change only) | abort 14.84 µs at `b_osc_trim1` |
| `t10-t2-fast-07-i` | `t10-t2-fast-07-f` | `--nodcp --por-fixed --bridge-fixed` | abort 6.86 µs, "cause unrecorded" |
| `t10-t2-fast-07-g` | `t10-t2-fast-07-f` | `tmax` 4 → 3.5 ns | **completed** (38 µs) |
| `t10-t2-fast-07-h` | `t10-t2-fast-07-f` | `tmax` 4 → 4.5 ns | **completed** (38 µs) |

4. Conclusion: no single element causes the abort. The element in the message is the place where the step fails. When it is removed, the abort moves to another element (T2F HBT → `SIN_P` pad diode → bridge source `b_osc_trim1`). The aborts are deterministic (a rerun is bit-identical), but a small change (one `tmax` step, one SPI write, the CRC value) moves the abort time or removes it. Every abort comes after `d_cosim` "time reversal in Icarus Shim VPI" messages: the analog solver rejects a step after the digital side has advanced. Passing decks have the same messages (`t10-t2-fast-h`: 1609), so the count does not predict an abort. The `osc_trim` outputs are static (code 22), so `b_osc_trim1` is not active at the abort.
5. The working method: if a deck aborts, rerun it with one other `tmax` (3.5 or 4.5 ns). In this budget 3 of 5 such reruns completed (`-07-g`, `-07-h`, `-07-k`); `-07-j` (3.5 ns) aborted at 25.48 µs at the `SIN_P` pad diode, and `-07-l` (4 ns) repeated the 14.84 µs abort of `-07-f` (same deck up to that time).
6. Full-chip deck (all blocks real, fast view, D11): `t10-t3-full-07-a` (ctrl 0.7, `--nodcp --por-fixed`, `tmax` 4 ns, 3 threads) ran through the 14.06 µs point of `t10-t3-fast-e` and through the master `DONE` at 19.401 µs. The runner stopped it at its 3 h limit (10 802 s) at 19.574 of 19.6 µs, so it has no `tran.raw`. Its SPI words are in the log and give test 3 **passed** (`tb/results/t10-t3-full-07-a.logeval.json`, LSB 457.0 µV taken from `t10-t3-sub-07-a`, same reference path): `I_A` 821 → 1740, step 919 against 919.0 (+0.00 %); `I_B` 823 → 3272, step 2449 against 2450.6 (−0.07 %); no `STALL` or `LOSTEV` line, 18 conversions. Strobe position: not run (needs the waveform).
7. Named elements, as asked: the abort is not caused by one element. The `dpantenna` pad diodes (`xp_sin_p` / `xp_isa_p` `.xi2.xd1`, DCPDiode pad to IOVDD) are the most frequent place (5 of 14 aborts; `b_osc_trim1` 4, T2F HBT 2, POR source 1, cause unrecorded 2). `--nodcp` removed the abort in `t10-t3-sub-c` → `-d` and is in the full-chip deck above, but it moved the abort in `-07-a` → `-07-b`. The T2F HBT and the fast-view POR source are also places only.

### 15.4 Test 2 nW (priority 1)

1. With ctrl 0.7 the first decks (`-07-a` to `-07-e`) read the SPI status byte 0xC0, not 0xD0: `CAL_VALID` (bit 4) was 0, because the master `CAL_CRC` shadow had the 0.5 reset value of `CMP_THR_A/B` (T10-40). Fixed.
2. With the CRC fix (`-07-g`, `-07-h`): all position and bus criteria passed (MEAS 0.045°, POS 0.50°, ST −0.42°, `STATUS` 0x01D0, BiSS-C CRC), but nW = 0. `STATUS` bit 7 (`FAULT`) is 1: test 2 never wrote `CTRL.CLR`, so the reset value POR (bit 12) stayed latched. nW = 0 is the register-map rule for a set `FAULT`, not a design error. The fourth budget gave R3 as the only cause; that was incomplete (T10-41).
3. Test 2 now writes `CTRL.CLR` after the lock wait. `t10-t2-fast-07-k` (ctrl 0.7, CRC fix, CLR, `tmax` 4.5 ns, encoder subset, T2F stub, M6, 1 thread, 4088 s): **passed**, all 11 criteria. MEAS residual 0.046°; `POS` 0.39°; `STATUS` 0x0150 (POS_VALID, CAL_VALID, EN, FAULT clear); BiSS-C ACK, start, CRC and stop correct; nE = 1, nW = 1; ST −0.43°. The CLR reruns with 3.5 ns and 4 ns aborted (15.3 item 5).

### 15.5 Run log, fifth budget

| Run | Test | View, options | VREF buffer | Simulated | Deck time | Result |
| --- | --- | --- | --- | --- | --- | --- |
| `t10-t1b-sub-07-a` | 1b | thermal subset, fast, ctrl 0.7, `reltol=1e-4`, 1 thread | M6 | 13 µs | 367 s | **passed**: `ID` 0x5207, `FAULT` 0x1800 |
| `t10-t2-fast-07-a` | 2 | encoder subset, T2F stub, ctrl 0.7, `tmax` 4 ns, 3 threads | M6 | 24.01 of 38 µs | 1145 s | failed: abort at `xp_sin_p.xi2.xd1`; `CAL_VALID` 0 (T10-40) |
| `t10-t3-bis-a` | 3 | as `t10-t3-fast-e` + `--nodcp`, 2 threads | M6 | 3.9 µs | stopped | not run to the abort point (T10-38) |
| `t10-t3-bis-b` | 3 | as `t10-t3-fast-e` + `--por-fixed`, 1 thread | M6 | 2.3 µs | stopped | not run to the abort point (T10-38) |
| `t10-t2-fast-07-b` | 2 | `-07-a` + `--nodcp` | M6 | 25.04 µs | — | failed: abort at `b_osc_trim1` |
| `t10-t3-sub-d` | 3 | `t10-t3-sub-c` + `--nodcp`, 1 thread | M6 | 19.6 µs | 1649 s | **passed**: A +0.11 %, B +0.10 % |
| `t10-t2-fast-07-c` | 2 | `-07-a` + `irreversible=1` | M6 | 24.01 µs | 1148 s | failed: identical to `-07-a` (T10-39) |
| `t10-t3-sub-07-a` | 3 | current subset, ctrl 0.7, `tmax` 4 ns, 2 threads | M6 | 19.6 µs | 1091 s | **passed**: A +0.11 %, B +0.10 %; `cur_trk` from the port |
| `t10-t3-full-07-a` | 3 | all blocks real, ctrl 0.7, `--nodcp --por-fixed`, `tmax` 4 ns, 3 threads | M6 | 19.574 of 19.6 µs | 10 802 s (limit) | **passed** from the log (DONE 19.401 µs): A +0.00 %, B −0.07 %; no raw file |
| `t10-t3-full-07-b` | 3 | as `full-07-a`, `tmax` 5 ns | M6 | under 1 µs | stopped | not run: stopped by PID after 2 min, CPUs 109-111 used for test 2 |
| `t10-t2-fast-07-d` | 2 | `-07-b` + `--por-fixed --bridge-fixed` | M6 | 25.09 µs | — | failed: abort, cause unrecorded |
| `t10-t2-fast-07-e` | 2 | `-07-a`, SCLK 12.5 MHz | M6 | 27.37 µs | — | failed: abort at `b_osc_trim1` |
| `t10-t2-fast-07-f` | 2 | `-07-a` + CRC fix | M6 | 14.84 µs | 687 s | failed: abort at `b_osc_trim1` |
| `t10-t2-fast-07-g` | 2 | `-07-f`, `tmax` 3.5 ns, 1 thread | M6 | 38 µs | 3846 s | position and bus criteria passed; nW = 0 (no CLR, T10-41) |
| `t10-t2-fast-07-h` | 2 | `-07-f`, `tmax` 4.5 ns, 1 thread | M6 | 38 µs | 3824 s | as `-07-g` |
| `t10-t2-fast-07-i` | 2 | `-07-f` + `--nodcp --por-fixed --bridge-fixed`, 1 thread | M6 | 6.86 µs | 694 s | failed: abort, cause unrecorded |
| `t10-t2-fast-07-j` | 2 | CRC fix + CLR, `tmax` 3.5 ns, 1 thread | M6 | 25.48 µs | 2674 s | failed: abort at `xp_sin_p.xi2.xd1` |
| `t10-t2-fast-07-k` | 2 | CRC fix + CLR, `tmax` 4.5 ns, 1 thread | M6 | 39 µs | 4088 s | **passed**, all 11 criteria, nW = 1 |
| `t10-t2-fast-07-l` | 2 | CRC fix + CLR, `tmax` 4 ns, 1 thread | M6 | 14.84 µs | 1522 s | failed: abort at `b_osc_trim1` (as `-07-f`) |

All runs: tt, 27 °C, fast view, D11 (T2F held off), fixes F22-F24, PDK 84374023. Evidence: `tb/results/<run>.json` and
`tb/runs/<run>/` (deck and `run.json`); waveforms and logs under `<G1_RESULTS_ROOT>/r1_top/tb/<run>/`.

## 16. Sixth budget (2026-10-28): post-layout view (`--view pex`) with the block extractions of record

This is the first half of the closing bar (full-chip post-layout functional campaign). The second half (top-level
routing parasitics) comes after chip assembly try g.

### 16.1 Extracted netlists of record (inventory)

| Block | Netlist used | sha256 (first 8) | Notes |
| --- | --- | --- | --- |
| `r1_afe` | layout E6 (dev16) RC, `<G1_RESULTS_ROOT>/r1_afe/pexrc-layout-e6-dev16/r1_afe_post_rc.spice` | ed92a249 | same subckt name and pins as the schematic (fd0fcf4e4) |
| `r1_isense` | layout c RC, `<G1_RESULTS_ROOT>/r1_isense/pex-20261026-c/rc/r1_isense_post.spice` | 1989529b | also defines its internal `r1_ls` |
| `r1_safe` | comparator cell only, `<G1_RESULTS_ROOT>/r1_safe/pex-cmp-20261021-a/rc/r1_safe_cmp_pex.spice` | 598c5bd6 | string, mux, level shifters and threshold DACs: schematic |
| `r1_bgr` | `<G1_RESULTS_ROOT>/r1_bgr/pex-rc-20261021-b/r1_bgr_pex.spice` | 0b5a7299 | used only in full-view decks; the fast view keeps the recorded behaviour |
| `r1_bias` revision 2 | `<G1_RESULTS_ROOT>/r1_bias/pex-rc-20261026-r2d/r1_bias_pex.spice` | 0ae828e6 | POR and VREF buffer (`vref`, `vref_b`) extracted; replaces MODEL M6 |
| `r1_osc` r2d | `<G1_RESULTS_ROOT>/r1_osc/pex-rc-20261021-r2d/r1_osc_pex.spice` | c6d76aac | used with `--osc tl` |
| `r1_adc` B5 | `r1_adc/sim/post/r1_adc_post_rc_mb5.spice` + SAR `r1_adc/sim/post/b5/sar/r1_adc_sar_gl_lumpc.spice` (transistor-level stdcells, lumped C) | 7bf2b33f / 102f66b6 | the SAR makes its own timing and `valid`; the ctrl takes `valid` from the pins (`T10_VALID_BRIDGE`), the sequencer model is not used |
| `r1_t2f`, `r1_ls`, `r1_gate` | none | — | no extraction of record; LVS netlists equal the schematic |
| padring | `r1_padring/netlist/r1_padring_1700.cdl` | db5b69f1 | not a simulation netlist (not LVS-qualified); the decks keep the PDK IO cells with deviation D1 (`nodcn`) |
| `r1_ctrl` 0.8 | gate level `<G1_RESULTS_ROOT>/r1_ctrl/r1ctrl_08_release/r1_ctrl_top.nl.v`, SDF slow/typ/fast | ddd4e85c; SDF c407b0f2 / 766a8e02 / fdf83c12 | not co-simulated; the decks use RTL 0.8 (665f75453) |

The runner checks every sha256 in `views/pex.inc` (`*T10SHA` lines) and records them in `run.json`
(`pex_inputs_sha256`, `pex_view`).

### 16.2 Changes to the testbench

| Item | Change |
| --- | --- |
| `--ctrl-rev 0.8` | ctrl RTL 0.8 from `<G1_RESULTS_ROOT>/r1_top/tb/ctrl_rtl_0.8` (665f75453, sha256 list `PINNED_RTL_08`); adds `T10_CTRL07` and `T10_CTRL08`. `ID` 0x5208 |
| `rtl/t10_master.v` | With `T10_CTRL08`: `COS_GAIN` (0x3F, reset 0x4000) is the 44th `CAL_CRC` word, after 0x60-0x6D. Reset CRC 0x7E |
| `views/pex.inc` | One section per block (16.1). Sections `*T10PEX <schematic include> [DROP sub] [RENAME old=new] [CHIPBIAS]` and `*T10CELL r1_adc`, each closed by `*T10END` |
| `--view pex` | The runner builds the schematic deck with every option (subsets, fast view, ideal clock), then replaces each schematic block that is still in the deck. Stubs and behavioural blocks stay. `CHIPBIAS`: `XU_BIAS` gets the revision-2 pins (`vref` on `vref_bg`, `vref_b` on `vref_l`), MODEL M6 is removed, the T2F reference moves to `vref_l` |
| `--pex-bias` | With `--fast`: keep the extracted `r1_bias` revision 2 in place of its recorded behaviour. VREF buffer label: `r1_bias rev 2 (extracted)` |
| `post_tb.py` | Extracted ADC: `valid_check` (one `adc_valid_a` pulse per started conversion, no stall) replaces the strobe and handshake checks of model M1. Test 3 adds the step error after the B5 layout gain 1.0570 is removed (D16 amendment) |
| `--pex-skip <blocks>` | `--view pex`: keep the named blocks (for example `r1_isense`, `r1_adc`) at schematic level, for deck time. Recorded in `run.json` `pex_view` as "schematic (--pex-skip)" |
| `--vdefine T10_T3_LEVEL0=1` | `rtl/t10_master.v`: test 3 runs level 1 only (deck-time split; not used for a result) |
| `adc_pex_check.py <run-id>` | Extracted ADC in the chip: for each `adc_valid_a` rise, the 14 raw decisions with the ctrl reset weights against `2047.5 + v_in / LSB` at the `adc_hold` rise; writes `results/<run-id>.adccheck.json` |

### 16.3 Deck time and convergence on the pex view (step 2)

Measured rates (tt, 27 °C, fast view, ideal clock; simulated µs per wall hour):

| Deck content (extracted blocks) | Rate | Run |
| --- | --- | --- |
| test 3 current subset: isense, ADC B5 + SAR, bias rev 2; before the first conversion | 7.5 µs/h (3 threads), 480 s/µs; 2 µs probe 989 s | `t10-pex-probe-d` |
| same, after the first conversion | 2.7-3.7 µs/h (7 µs in 5551 s, 3 threads) | `t10-t3-pex-a`, `t10-t3-pex-adc-b` |
| test 4 safety subset: isense, safe comparator, bias rev 2 | 5.5-6.5 µs/h (1 thread) | `t10-t4-pex-c`, `-d` |
| test 4 safety subset: safe comparator, bias rev 2 (isense schematic) | 9.2 µs/h | `t10-t4-pex-e` |
| test 3 current subset: isense, bias rev 2 (ADC schematic) | 15.3 µs/h (19.6 µs in 4611 s) | `t10-t3-pex-is-b` |
| test 2 encoder subset: AFE E6 (bias behaviour, ADC schematic) | 13.5 µs/h (39 µs in 10 390 s) | `t10-t2-pex-afe-d` |
| tests 5 and 6 thermal subset: bias rev 2, or osc r2d | 110 µs/h (test 5), 30 µs/h (test 6) | `t10-t5-pex-27-a`, `t10-t6-pex-d` |

Consequences for the 3 h deck limit:

1. The transistor-level SAR of the B5 ADC (stdcells as transistors) is the main cost. With it, the test 3 sequence (DONE at 19.4 µs) needs about 6 h. It does not fit. The extracted ADC is therefore checked in a 7 µs integration deck (`t10-t3-pex-adc-a`), and the current words use the ADC at schematic level (`t10-t3-pex-is-a`).
2. Test 4 with the extracted isense needs about 6 h for 40.5 µs; without it about 4.4 h. Only the OC part (to 21 µs) runs on the pex view (`t10-t4-pex-f`). The EN-low and clear parts are **not run** on the pex view.
3. Test 2 with the extracted ADC does not fit (39 µs at under 4 µs/h). Test 2 runs with the extracted AFE and the ADC at schematic level.

Convergence (ledger T10-45 to T10-55):

1. The extracted `r1_afe` E6 needs Sparse 1.3, `gmin=1e-12`, `rshunt=1e10` and a nodeset of its outputs for the operating point. KLU fails with a singular matrix at internal nodes of the split `rppd` resistors.
2. The extracted `r1_safe` comparator with the extracted `r1_bias` needs a nodeset of the bias outputs (`--nodeset`, values from `t10-pex-probe-d`).
3. The extracted `r1_bias` revision 2 aborts transients at `xu_bias.xq127` (the diode-connected POR reference `npn13G2`) in four decks: the test 1 rail ramps (all four option sets, 20-85 µs) and test 6 together with the extracted `r1_osc`. With the supplies on from the operating point it runs (tests 3, 4, 5).

### 16.4 Results on the pex view (step 3)

All runs: tt, 27 °C unless stated, fast view, ctrl RTL 0.8, D11 (T2F held off) except tests 5 and 6, PDK 84374023.
VREF buffer label: "bias rev 2 (extracted)" = `--pex-bias`; "M6" = the ideal model of the fast view.

| Test | Extracted blocks in the deck | VREF buffer | Run | Result |
| --- | --- | --- | --- | --- |
| 1 power-up (rail ramps) | bias rev 2 (POR, buffer) | bias rev 2 (extracted) | `t10-t1-pex-a` … `-d` | **failed to simulate**: all four decks abort at the POR reference npn `xu_bias.xq127` (20.1-84.5 µs), before the extracted POR releases (about 200 µs) |
| 1b (POR step, ID, FAULT) | bias rev 2 | bias rev 2 (extracted) | `t10-t1b-pex-b` | **not applicable**: with the extracted POR the operating point has `por_n` = VDD, so there is no reset; reads 0xFFFF (T10-47). Schematic result 0.8: passed (`t10-t1b-sub-08-a`) |
| 2 encoder path | AFE E6 (bias behaviour, ADC schematic) | M6 | `t10-t2-pex-afe-d` (39 µs, 10 390 s) | **passed**, all 11 criteria: MEAS residual 0.048°, `POS` 0.39°, `STATUS` 0x0150, BiSS-C CRC, nE = 1, nW = 1, ST −0.43° (schematic `-07-k`: 0.046°, 0.39°, −0.43°) |
| 2 with the extracted ADC | AFE E6 + ADC B5 | — | — | **not run**: does not fit 3 h (16.3) |
| 3 current words | isense c, bias rev 2 (ADC schematic) | bias rev 2 (extracted) | `t10-t3-pex-is-b` (19.6 µs, 4611 s) | **passed**: `I_A` step +0.22 %, `I_B` step +0.26 % (limit 1 %); level-0 words 827 / 827 (schematic 820 / 821); 19 conversions, strobes 0.595-0.599 ns, no stall |
| 3 with the extracted ADC | isense c, ADC B5 + SAR, bias rev 2 | bias rev 2 (extracted) | `t10-t3-pex-adc-b` (7 µs, 5551 s) | **partial**: `valid` per started conversion passed (7 pulses, 6 complete conversions, 0 stalls). One current-path conversion: code 757.0 against 828.5 from the pin voltage at the track end (−71.5 LSB raw; −1.9 LSB after the B5 layout gain 1.0570 is removed, D16 amendment). The encoder conversions are not evaluable (AFE stub, floating ADC input). The current-word criterion: **not run** (sequence does not fit 3 h) |
| 4 OC part (to 20.5 µs) | safe comparator, bias rev 2 (isense schematic) | bias rev 2 (extracted) | `t10-t4-pex-g` (ctrl 0.8, FAULT_MASK fix, 1 thread, 7588 s) | **passed**, the 5 OC criteria: all gates 3.3 V before the step; OC step at 18.04 µs (threshold 69.81 mV); `FAULT_N` low after 200.4 ns; all gates < 1 V after 312.5 ns (limit 1369 ns); cause OC_A. Schematic with the same ctrl 0.8 and fix (`t10-t4-sub-08-b`, M6): 167.0 ns and 279.2 ns. The pex view adds 33.3 ns to each delay; both stay within the 1369 ns limit. The other 4 criteria (DONE line, PWM after `CLR`, EN low, PWM after EN high and `CLR`) are after `tstop`: **not run**. Earlier: `t10-t4-pex-f` (ctrl 0.8) and `t10-t4-pex-05-a` (ctrl 0.5) failed with the testbench fault of 16.4.1 |
| 4 EN-low and clear parts | — | — | — | **not run** on the pex view (deck time, 16.3) |
| 5 at 27 °C | bias rev 2 (T2F reference) | bias rev 2 (extracted) | `t10-t5-pex-27-a` (805 s) | **passed**: `TEMP` 14 (expected 13.86 ± 1); f_T2F 1.6240 MHz, +1.48 % against the record (schematic with r1_vbuf: 1.6240 MHz, +1.48 %); `vref_l` 1.0445-1.0455 V |
| 5 at 125 °C | bias rev 2 | bias rev 2 (extracted) | `t10-t5-pex-125-a` (821 s) | **passed**: `TEMP` 18 (expected 18.21 ± 1); f_T2F 2.1344 MHz, +1.16 % (schematic +1.16 %) |
| 6 oscillator count | osc r2d (bias behaviour) | M6 | `t10-t6-pex-d` (1283 s) | **passed**: `OSC_COUNT` 49 (expected 48.50 ± 1.5); extracted r1_osc at code 22: 30.31 MHz, post-layout record 30.30 MHz (D13 band 28-32 MHz). With the extracted bias as well: aborts (T10-52) |

#### 16.4.1 Test 4 with ctrl 0.8: FAULT_MASK order (testbench fix)

1. With ctrl 0.8, test 4 kept `FAULT_N` low and the gates off after `CTRL.CLR` + `GATE_EN`, on the pex view (`t10-t4-pex-f`) and on the schematic view (`t10-t4-sub-08-a`). The same latch occurs on the pex view with ctrl 0.5 (`t10-t4-pex-05-a`) and in a digital-only diagnostic with ctrl 0.5 (`t10-diag-t4ctrl05-a`). The schematic pass `t10-t4-safe-vb-a` (ctrl 0.5) did not latch source 5. With the ADC stubbed, the amplitude input depends on stub levels, which differ between decks.
2. Cause (digital-only diagnostic `t10-diag-t4ctrl08-a`, the master and ctrl 0.8 in Icarus with the analog inputs at 0): fault source 5 (amplitude low/high) is active about 6 µs after the reset, because the safety subset has no encoder signal. It latched before the master wrote `FAULT_MASK` 0x000E (which does not mask bit 5), and `CTRL.CLR` clears only inactive sources. Cause register 0x0020 after the clear.
3. Fix (`rtl/t10_master.v`, `T10_CTRL07`): `FAULT_MASK` 0x06FE (every maskable source except OC_A) is the first write of test 4. Diagnostic `t10-diag-t4ctrl08-b`: cause 0x0000 after the clear, `FAULT_N` high, gates on, OC step at 17.95 µs.
4. Reruns with the fix:
   - Schematic view, ctrl 0.8 (`t10-t4-sub-08-b`, 38.7 µs, 1 thread, 10507 s, VREF buffer M6): all 10 criteria **passed**. `FAULT_N` 167.0 ns, gates 279.2 ns, EN low 84.3 ns, `FAULT` 0x0100 after EN low, PWM on `GATE_A` after both clears, `DONE` at 37.86 µs.
   - Pex view, ctrl 0.8, OC part (`t10-t4-pex-g`, 20.5 µs, 1 thread, 7588 s, VREF buffer r1_vbuf in the extracted r1_bias revision 2): the 5 OC criteria **passed** (`FAULT_N` 200.4 ns, gates 312.5 ns, cause OC_A). The EN-low and clear criteria are after `tstop`: **not run**.

### 16.5 What the pex view does not cover (step 4)

1. **Top-level routing parasitics.** `r1_chip.sp` connects the blocks with ideal wires. The routing between blocks, the supply rails and the pad-to-core nets come after chip assembly try g and its extraction.
2. **Blocks without an extraction of record:** `r1_t2f`, `r1_gate` (LV and HV cells), `r1_ls` (`t10_ls`), and the `r1_safe` string, mux, level shifters and threshold DACs (only the comparator cell is extracted). These stay at schematic level.
3. **Padring.** `r1_padring_1700.cdl` is not a simulation netlist. The decks use the PDK `sg13g2_io` cells with deviation D1 (`nodcn`; `dantenna` removed).
4. **`r1_ctrl` at gate level.** The gate-level netlist and SDF of 0.8 (`r1ctrl_08_release`) are not co-simulated. The decks use RTL 0.8. Digital timing is covered by the ctrl STA, not by these decks.
5. **The SAR as gate-level Verilog with SDF.** The B5 SAR runs as transistor-level stdcells (lumped C). This is accurate but too slow for full sequences (16.3).
6. **Fast-view behaviour.** `r1_bgr` stays the recorded behaviour in every fast deck (the `r1_bgr` extraction is used only in full-view decks, and none ran). `r1_bias` is extracted only with `--pex-bias`.
7. **Ideal parts of the deck:** the 30 MHz ideal clock (D5) except in test 6; the MODEL `vcm` / `vcm2` 0.6 V sources in the ADC wrapper; the board model; the stubs of each subset.
8. **Tests and parts not run on the pex view:** test 1 power-up (aborts, T10-54), test 1b (no POR step with the extracted bias), test 2 with the extracted ADC, test 3 sequence with the extracted ADC, test 4 EN-low and clear parts, test 4 with the extracted isense.
9. **Corners.** tt only (test 5 at 27 °C and 125 °C). No ss/ff, no supply corners, no mismatch.
10. **Open items of the extractions themselves:** B5 ADC offset +12 LSB and R2-4 with real CDAC timing (r1_adc README); AFE E6 CM 2.5 V offset drift (r1_afe README).

### 16.6 Chip view: block extractions + try-g top-level routing RC (`--chip-rc`)

Method (`chip_rc.py`, called by `run_tb.py --chip-rc`):

1. Include `<G1_RESULTS_ROOT>/r1_top/pex-20261029-g3/fast/r1_top_g_pex_fast.spice` (fast variant, typ sheet, sha256 `cce466ec…`, checked by the runner) and instantiate its RC network `r1_top_rc` (the `Xrc` line of the wrapper `r1_top_pex`, `ictrl=0`).
2. Move every pad, block and ctrl pin of the deck netlist from its deck net to its RC port node (`u_<inst>__<pin>`, `io_<pad>__<pin>`): by position where the pin lists are equal (pads and analog blocks), by name for `r1_adc` (the CDL has 4 more `*_nc` pins) and for the ctrl wrapper (`CTRL_MAP`; testbench pins stay on their deck nets). The pad and supply nets of the deck are the top ports of the RC network.
3. Each other deck net is tied by a 0 V source to the RC node of its first moved pin, so that stubs, MODEL sources, loads and probes stay connected there (179 nets, 493 pins moved).
4. Deck ties of non-supply pins to a supply are kept (D11 T2F enable at VSS, `r1_gate` `gate_en` at VDD).

Probes (2 µs, 1 thread):

| Probe | Deck | Rate | Result |
| --- | --- | --- | --- |
| `t10-chip-probe-t5-a` | test 5 thermal subset, bias rev 2 extracted, Sparse, `reltol=1e-4` | 4349 s for 2 µs (2175 s/µs; 3066 s/µs over 0.27-0.99 µs) | completed 2 µs |
| `t10-chip-probe-t3-a` / `-b` / `-c` | test 3 current subset (isense extracted, ADC schematic), with / without the extracted bias | — | operating point failed (`xu_bias.xq127`; pad `dparea` and `t10_ls` node) |
| `t10-chip-probe-t3-d` | as `-c` with Sparse, `gmin=1e-12`, `rshunt=1e10`, bias nodeset | 2846 s for 2 µs (1423 s/µs; 1381 s/µs over 0.31-0.56 µs) | completed 2 µs; no stall |
| `t10-chip-probe-t6-a` / `-b` | test 6 (osc extracted, bias behaviour) | under 0.1 µs/h (`-b`) | `-a` operating point failed at the T2F HBT; `-b` stopped by PID after 17 min |

Result: no subset deck fits the 3 h limit on the chip view (test 3: 19.6 µs × 1423 s = 7.7 h; tests 1b, 5: 13-25 µs × 2175 s = 8-15 h; test 6 slower; test 2 and test 4 are longer). The subset decks 1b, 3, 4, 5, 6 and test 2 are **not run** on the chip view. The tool and the include are ready; the decks need a faster top-level netlist (fewer RC nodes on the slow nets) or more than 3 h per deck.

What the fast variant does not cover (in addition to 16.5):

1. Supply noise coupled into signals: every coupling capacitor to a supply net goes to ground at both ends (r1_top README, chip-level extraction open issue 9).
2. Fill: the netlist of record is unfilled. With the fill, the C of `OSC_CLK` and `VREF_B` rises by 22-91 % and the AFE pair C by 22-41 % (band check, `fill_eff.json`); not in the netlist.
3. Coupling between top-level wires and macro-internal metal (black boxes), the supply pad cells and their ESD paths, and the 34 `sg13g2_decap_8` antenna/decap cells (their RC ports are left open in the deck).
4. The ctrl supply: one grid node for `vdd`/`vss` of the co-simulated ctrl (`ictrl=0`); the ctrl current is not spread over the grid.
5. The deck nets tied at one RC node (item 3 of the method): testbench parts on such a net see the RC node of the first pin only.

## 17. Seventh budget (2026-10-28): gaps of the pex view closed or bounded

Goal: close the gaps of the pex view (section 16) before the chip-view campaign on the try-h chip. All numbers are
simulated (tt, 27 °C, fast view, ideal 30 MHz clock unless stated). Failures are in the R1 failure ledger
(F-20261028-T10-63 to -68).

### 17.1 Changes to the testbench

| Item | Change |
| --- | --- |
| `run_tb.py`, deck 1b with `--pex-bias --view pex` | POR step on the extracted `r1_bias` POR: switch `Spor_hold` holds the delay capacitor node `xu_bias.xpor.cdel` at VSS until `--por-step`; switch `Spor_set` then charges it to VDDA in 100 ns (1 kΩ). The extracted Schmitt trigger, `ready` inverter, VDD pass device, `por_raw` pull-down and output inverters make the `por_n` edge. The 197-247 µs of the PMOS delay stack are not simulated (`r1_bias` record) |
| `rtl/t10_master.v`, `T10_T4_ENONLY` | Test 4 EN-low and clear parts only: `FAULT_MASK` 0x06FF (all maskable sources), no `CMP_THR` writes, no OC step. Digital diagnostic `t10-diag-t4enonly-a`: `DONE` at 24.64 µs. `T10_T4_NOCRC` (no `CAL_CRC` write) is a diagnostic only: without it `CAL` (bit 11) stays latched and the gates stay off |
| `post_tb.py` test 4 | With `T10_T4_ENONLY` the 5 OC criteria are "not applicable" (they are in the OC-part deck) |
| `post_tb.py` verdict | `passed`: every criterion passed or not applicable. New `partial`: every evaluated criterion passed, the rest "not run" (deck time) |
| `views/pex.inc` section `*T10CELL r1_adc BEHAV`, `--adc-behav` | `r1_adc` layout B5 RC extraction (`r1_adc_lay_pr`, with the layout filter and buffer) and the behavioural SAR `r1_sar5_logic` through the ADC owner wrapper `r1_adc5_core_lay` (`sim/post/r1_adc5_post.spice`, sha256 checked): the configuration of the B5 gain and offset record. Timing and `valid` come from the sequencer model (`seq_*`), as in the schematic view. Faster than the transistor-level SAR sub-macro: 7.5 µs in 5374 s with 1 thread (`t10-t3-pex-adcbh-a`) against 7 µs in 5551 s with 3 threads (`t10-t3-pex-adc-b`) |
| `post_tb.py` test 2, `T10_T2_PAIRS` | Pair-only deck: `MEAS_ANGLE` per pair, strobes and handshake are evaluated; `POS`, `MEAS_ANGLE` over SPI, `STATUS`, BiSS-C and `DONE` are "not run" (they need the lock at about 21 µs) |
| `adc_pex_check.py` | Track end from `seq_trka0/1` (sequencer model) when the SAR track signals are not saved; new column `error_lsb_b5_fit`: residual against the B5 mux fit (gain 1.0570, offset +8.0 LSB) |
| `t3_split.py <l0-run> <l1-run> <out-id>` | Test 3 step from two half decks (level 0 = full sequence cut after the level-0 reads, level 1 = `T10_T3_LEVEL0=1`) |
| `--pex-bias-drop <regex>` | BISECTION only: drop the C/R/X lines of the renamed `r1_bias` extraction that match |

### 17.2 Test 1 and 1b on the pex view

Test 1b **passed** on the pex view with the extracted `r1_bias` revision 2 (POR and VREF buffer r1_vbuf extracted),
thermal subset, ctrl 0.8:

| Run | Options | Result |
| --- | --- | --- |
| `t10-t1b-pex-c` | default (KLU, `gmin=1e-15`, `rshunt=1e12`, `tmax` 5 ns) | aborted at 2.43 µs after singular-matrix warnings at floating stub nodes (pad `xp_cos_n`, `xu_ls_afe0`) |
| `t10-t1b-pex-d` | KLU, `gmin=1e-12`, `rshunt=1e10` | POR step, reset exit and `ID` passed; aborted at 8.28 µs (singular matrix at an internal node of the extracted POR resistor `xu_bias.xr143`) |
| `t10-t1b-pex-e` | as `-d`, `tmax` 1 ns | **passed**, all 5 criteria (366 s): `por_n` at 1.005 µs (4 ns after the capacitor release), ctrl out of reset at 1.04 µs, `ID` 0x5208, `FAULT` 0x1800, `DONE` 12.45 µs |
| `t10-t1b-pex-f` | Sparse 1.3, `gmin=1e-12`, `rshunt=1e10`, `itl1=400 itl2=200`, `tmax` 5 ns | **passed**, same values |

Test 1 (rail ramps) on the pex view: **failed to simulate**. Bisection of the abort at `xu_bias.xq127` (diode-connected
POR reference `npn13G2`, node `n149` = `vq`):

| Run | Change against `t10-t1-pex-a` (KLU, 20.13 µs) | Abort at |
| --- | --- | --- |
| `t10-t1-pex-bis-a` | without `--hbt-selft0` (self-heating model of record) | 19.5 µs, now at `xu_t2f.x1.xqb2` (another npn) |
| `t10-t1-pex-bis-b` | `tmax` 1 ns | 23.2 µs |
| `t10-t1-pex-bis-c` | coupling C of `n149` to all non-VSS nets removed (14 lines, `--pex-bias-drop`) | 20.1 µs |
| `t10-t1-pex-bis-d` | `gmin=1e-12`, `rshunt=1e10` | 17.9 µs |
| `t10-t1-pex-bis-f` | `-d` + `tmax` 1 ns | 36.4 µs (singular matrix at the buffer node `xvb.ns__p3` first) |
| `t10-t1-pex-bis-g` | `-f` with Sparse 1.3 | **62.2 µs** (best) |
| `t10-t1-pex-bis-h` | `-g` without `--hbt-selft0` | 23.8 µs |
| `t10-t1-pex-bis-e` | `--ctrl static` (no co-simulation), options of `-a` | no abort to 24.2 µs, then the 3 h limit (8 µs/h; no raw file) |

Findings:

1. The abort is not caused by the coupling capacitors of `n149`, by `tmax` alone or by self-heating. Without
   `--hbt-selft0` it moves to another npn.
2. In `-bis-h` the node `n149` is flat at 0.6667 V from 10 µs to the abort. Nothing in the POR switches near the
   abort (`gooda`/`goodd` high since 20/22 µs, `cdel` 7.7 mV). The abort is numerical, inside the `npn13G2` VBIC
   instance at a quiet state. It is not a circuit event.
3. Without the co-simulation the deck passes the abort point of the same options (20.1 µs), so the d_cosim time
   steps may take part. This is not proven beyond 24 µs.
4. "Schematic bias with the extracted buffer only" is **not run**: the extraction is flat (POR, mirrors and
   buffer in one netlist), and the schematic revision 2 cannot be combined with part of it without a split by the
   `r1_bias` owner.
5. The POR release (about 220 µs after the ramps) is not reached in any variant. The extracted POR delay is
   therefore covered only by the `r1_bias` post-layout record (delay +2…+3 %), not in the chip deck.

### 17.3 Test 4 EN-low and clear parts on the pex view

Deck sizing: 370 s/µs (`t10-t4-pex-g`), so the full 38.7 µs sequence needs about 4 h. The EN-only sequence
(`T10_T4_ENONLY`, 25.3 µs) needs about 2.6 h.

Run `t10-t4-pex-en-a` (safe comparator and `r1_bias` revision 2 extracted, VREF buffer r1_vbuf extracted, isense
schematic, AFE and ADC stubs, ctrl 0.8; 8576 s): **passed**, all evaluated criteria. All gates < 1 V 84.3 ns after EN
low (limit 1 µs; schematic `t10-t4-sub-08-b` 84.3 ns), `FAULT` 0x0100 (STO), PWM on `GATE_A` again after EN high and
`CTRL.CLR`, `DONE` at 24.70 µs. With the OC part (`t10-t4-pex-g`, 16.4) all 10 criteria of test 4 passed on the
pex view.

### 17.4 Extracted-ADC current conversion at −71.5 LSB (`t10-t3-pex-adc-b`)

Which conversion: the 7th conversion of the deck, at 6.51 µs. It is the first current-path conversion (`adc_sel`
high, current frame), not the first conversion after enable. The first conversion after enable (2.48 µs) is an
encoder conversion with the AFE stubbed, so its input floats (−225 / −347 LSB). It is not evaluable, as are the
other encoder conversions of the current subset.

Cause: the same deck with the behavioural SAR and the sequencer model (`t10-t3-pex-adcbh-a`, `--adc-behav`, 7.5 µs,
5374 s, VREF buffer r1_vbuf extracted for the chip and the ADC layout buffer for the ADC) gives code 757.25 against
757.0 with the hardened SAR. The input is −557.2 mV (expected 828.46).

| Model | Residual (LSB) |
| --- | --- |
| raw | −71.2 (hardened SAR −71.5) |
| B5 gain 1.0570 removed | −1.6 (−1.9) |
| B5 mux fit (gain 1.0570, offset +8.0 LSB) | −9.7 (−10.0) |
| B5 gain with +12 LSB offset (R2-4 slot estimate) | −14.0 |

1. The error does not depend on the SAR (hardened or behavioural: 0.25 LSB apart). So it is not the B5
   first-conversion hold, and not the SAR timing.
2. It is not the `DISCARD` count: the check uses the raw decisions at the macro pins, before the ctrl.
3. The B5 gain explains −69.5 LSB of it (0.0570 × 1219.6 LSB from mid-scale). After the gain is removed, −1.6 LSB is
   left. With the +8.0 LSB mux-fit offset, −9.7 LSB is left (0.8 % of the reading, about 3 × the fit residual). In
   this chip deck the encoder conversions near −0.17 V show about −2 LSB after the gain is removed, so the offset in
   the chip deck is near 0, not +8. With one current-path sample, the offset is not resolved further.

**Chip finding (not a testbench artefact):** the ADC layout gain (B5 1.0570, B6 1.0496) goes 1:1 into the current
words `I_A` / `I_B` (+5.7 % for B5). `r1_ctrl` 0.8 has no current-gain correction: D22 covers only the encoder
channels (`SIN_GAIN`, `COS_GAIN`), and `I_ZERO` is an offset only. The test 3 limit (1 % of 14 × dV / LSB) is met with
the extracted ADC only after the gain is removed by the host. Decision needed: host calibration of the current
gain (with the shunt tolerance) or an ADC gain fix in B7/B8. Owner: coordinator / `r1_adc`.

### 17.5 Test 2 with the extracted AFE E6 and the extracted ADC B5

Deck sizing: 2 µs probe `t10-t2-pex-probe-a` 790 s (395 s/µs, before the conversions). Once the conversions run:
4.2 µs/h with 3 threads (`t10-t2-pex-afeadc-a`, stopped at 2.5 µs by PID). The full sequence (39 µs, lock at about
21 µs) needs about 9 h. The pair-only deck runs instead.

Run `t10-t2-pex-afeadc-c` (`T10_T2_PAIRS`, 12.5 µs, `--nodcp`, 3 threads, 6473 s; ctrl 0.8 design weights, D22 words
at reset; chip VREF M6, ADC on its own layout buffer): **partial**.

| Criterion | Pex AFE + ADC (`-afeadc-c`) | Pex AFE, ADC schematic (`t10-t2-pex-afe-d`) |
| --- | --- | --- |
| ADC strobes, handshake | passed (15 conversions) | passed (51) |
| `MEAS_ANGLE` per pair, residual after a constant (≤ 0.25°) | **passed**: 0.142° max, 0.069° rms, 11 pairs; constant −0.672° | passed: 0.048° max, 0.022° rms, 47 pairs; −0.621° |
| `POS`, `MEAS_ANGLE` over SPI, `STATUS`, BiSS-C, `DONE` | **not run** (lock at about 21 µs) | passed |

`t10-t2-pex-afeadc-b` (same deck without `--nodcp`) aborted at 3.62 µs (`dparea` instance, after `vmax` warnings
of the extracted AFE resistor segments).

### 17.6 Test 3 current words with the extracted ADC B5

Two half decks (12.4 µs each, 1 thread; isense c and `r1_bias` revision 2 with r1_vbuf extracted, ADC B5 with the
behavioural SAR, `--adc-behav`): `t10-t3-pex-adcbh-l0` (level 0, 8390 s) and `t10-t3-pex-adcbh-l1` (level 1,
`T10_T3_LEVEL0=1`, 8456 s). Strobes and handshake passed in both (12 conversions each). Step from `t3_split.py`
(`results/t10-t3-pex-adcbh-split.json`; ADC VREF 1.0502 V, LSB 457.1 µV):

| Channel | Level 0 / level 1 word | Step measured / expected | Error | Error after the B5 gain 1.0570 is removed |
| --- | --- | --- | --- | --- |
| `I_A` (30 mV) | 757 / 1734 | 977 / 918.7 | **+6.34 % (failed, limit 1 %)** | +0.61 % (passed) |
| `I_B` (80 mV) | 759 / 3365 | 2606 / 2450.0 | **+6.37 % (failed)** | +0.63 % (passed) |

With the ADC at schematic level the same step is +0.22 % / +0.26 % (`t10-t3-pex-is-b`; level-0 words 827 / 827).
This confirms the chip finding of 17.4: the ADC layout gain goes 1:1 into the current words. The isense, bias and
ADC extractions together are within 1 % only after a host gain calibration.

### 17.7 State of the pex view after the seventh budget

| Test | Pex view |
| --- | --- |
| 1 ramps | **failed to simulate** (17.2) |
| 1b | **passed** (`t10-t1b-pex-e`, `-f`) |
| 2 | **passed** with the extracted AFE (`t10-t2-pex-afe-d`); with AFE and ADC extracted **partial** (pairs passed; lock-dependent criteria not run) |
| 3 | **passed** with the ADC schematic (`t10-t3-pex-is-b`); with the extracted ADC: **failed** against the 1 % limit (+6.3 %, the B5 gain; +0.6 % after the gain is removed; 17.6) |
| 4 | **passed**, all 10 criteria (`t10-t4-pex-g` + `t10-t4-pex-en-a`) |
| 5, 6 | **passed** (16.4) |

Not run on the pex view: test 1 to the POR release; the lock-dependent part of test 2 with the extracted ADC
(about 9 h); the extracted `r1_osc` together with the extracted `r1_bias` (T10-52); the extracted `r1_isense` in
test 4 (deck time); corners. The list of 16.5 is unchanged otherwise.

### 17.8 Run log, seventh budget

| Run | Deck | Wall | Verdict |
| --- | --- | --- | --- |
| `t10-diag-t4ctrl05-a` | digital-only test 4, ctrl 0.5 (source 5 latch, T10-62) | < 1 min | diagnostic |
| `t10-diag-t4enonly-a` | digital-only test 4 EN-only, with / without CRC | < 1 min | diagnostic |
| `t10-t4-pex-en-a` | test 4 EN-low and clear, pex | 8576 s | passed |
| `t10-t1b-pex-c` / `-d` / `-e` / `-f` | test 1b, pex, POR step | 15-366 s | failed / failed / passed / passed |
| `t10-t1-pex-bis-a` … `-h` | test 1 ramp bisection | 120-10803 s | failed (abort or limit) |
| `t10-t2-pex-probe-a` | 2 µs rate probe, AFE + ADC extracted | 790 s | probe |
| `t10-t2-pex-afeadc-a` / `-b` / `-c` | test 2, AFE + ADC extracted | stopped / 25 min / 6473 s | failed (stopped) / failed (abort) / partial |
| `t10-t3-pex-adcbh-a` | ADC current conversion, behavioural SAR | 5374 s | ADC check (17.4) |
| `t10-t3-pex-adcbh-l0` / `-l1` | test 3 halves, extracted ADC | 8390 / 8456 s | step +6.34 % / +6.37 % (failed; +0.61 / +0.63 % after the B5 gain is removed) |

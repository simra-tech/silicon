# G1_TOP chip-level campaign on the chip-of-record netlists — results (2026-09-25)

Scope: `run_top.py --blockset c1414` (block netlists of `g1_chip_top_1414.gds`,
`629d303a…`; netlist map and hashes in [../../README.md](../../README.md)), run
2026-09-24 to 2026-09-25. Every number here is **simulated**. Nothing is measured.
Logs: `../logs/<log>` (one `.log`, `.json` and `.progress.jsonl` per run). The
`QUIET`, `TRIP`/`NO_TRIP_EXPECTED`, `REARM`, `POWERUP`, `T2F`, `CLOCK`,
`SUPPLY_uA` lines and the `# run status` footer of each log are the source of every
row. Toolchain: ngspice-46, Icarus Verilog 14.0 (devel), PDK commit
`84374023ee8b4b126bebbba67fcbada0a9c0ff0b`, repository revision `dc516d39` plus the
uncommitted `run_top.py` recorded by `runner_sha256` in each `.progress.jsonl`.

Night campaign job file: [night_20260924.json](night_20260924.json) (162 jobs).
Summary table: `python3 launch_matrix.py night_20260924.json --summarize` (writes
`night_20260924_run/summary.csv`). The summarizer marks runs "completed" by the
footer only. This record also treats a log that contains `mismatched XSPICE` as
**invalid**, whatever its footer says.

## Status at time of writing ({{when}})

Night campaign, 162 jobs: {{counts}}

- **Invalid (46)**: an RTL-loading defect in the first night launch (log contains
  `mismatched XSPICE` or ends `# run status failed (cosim)`). The defect is fixed.
  Every invalid job was re-run under an `_r3` (or `_r2_r3`) id, and only those
  re-runs are used. `f_mid_ss_85C_c1414m` has a `completed` footer and is still
  invalid. Its log carries the mismatch and a spurious `GATE` < 1 V at 10.39 µs.
- **Timeout (16)**: stopped at the 12 300 s limit. Four were superseded by
  valid `_r2_r3` re-runs. Eleven were relaunched as `_r4` with a 25 200 s limit,
  and `q_ss_125C` was relaunched outside the job file as `q_ss_125C_r4_c1414m`.
  All twelve completed and passed. With them, all 72 cells of the night matrix
  (section 1) have a valid completed run: 72/72 completed, 0 failed.
- **Numerical failure (3)**: "timestep too small", listed below.

## Deviations used by the tables

| Label | Meaning | Where used |
| --- | --- | --- |
| `bgr=sch` | `--view-override bgr=sch`: the BGR586 schematic netlist (`586ffb58`, with 329 historical Sep-19 capacitors) replaces its extraction. With both the BGR586 and TRIP extractions, the deck runs about 4× slower. The BGR586 extraction is DC-identical: 319.704 µA and `VREF` 1.04546/1.04547 V at tt/27 °C in both views (`c1414fullc` vs. `c1414n2`) | every table except "Both extractions" and "Oscillator" |
| `inpads nodcn` | `--inpads nodcn`: `SENSE_P`/`SENSE_N` use a deck-local copy of `sg13g2_IOPadAnalog` without its `dantenna` parts. The reason is the model discontinuity of the PDK `darea` diode at −3·n·V<sub>t</sub> ([../../README.md](../../README.md) "Pad-diode finding"). Simulator work-around, not a statement about silicon | night matrix, supply, hot, amplitude sweep, T2F |
| `pads nodcn` | `--pads nodcn`: every PDK pad instance of the deck without `dantenna` parts (power-up decks with PDK pad models) | power-up |
| ideal clock | the RTL clock is an ideal 1.2 V square wave at 9.436194721 MHz (R0.95 loaded nominal trim 8) at **every** corner, temperature and supply | every trip/no-trip table |
| gear | `--method gear` (osc, T2F, power-up decks); the trip decks use trap, maximum step 5 ns | osc, T2F, power-up |

Times are measured from the load event: `trip_d` is the RTL trip latch, then
`GATE` < 1 V and < 0.33 V are the first crossings. Cause 2 is hard and cause 1
is soft. `VDDA` is the 3.3 V analog-rail current averaged over the armed window
before the event (BGR + SENSE + TRIP 3.3 V). The 1.2 V `VDD` current in these
decks (3.5–5.6 µA) is the RTL/ideal-clock stand-in and is not a physical
estimate. Wall time is ngspice wall time on the emulated container. Cases:
`c_mid` = 1.8 A/45 mV in 20 ns at hard code 200 (39.25 mV); `c` = 3× (75 mV);
`e20` = 4× (100 mV) in 20 ns (`c` and `e20` at the default hard code 0xFE, 49.8
mV); `f_mid` = `c_mid`, then load back at 36 µs and `EN` low 40–42 µs (re-arm);
`b_s` = 1.5× held with `SOFT_TIME` = 0x0001 (256 osc_clk); `q` = nominal 1 A, no
event. Pass criteria: the expected cause, `GATE` < 1 V within 10 µs for the hard
cases, and `GATE` held at `IOVDD` with cause 0 for `q`. `f_mid` must also end
with `GATE` 3.3 V and 1 A load after `EN` re-arm.

## 1. Night matrix: case × corner × temperature (`bgr=sch`, `inpads nodcn`, ideal clock)

{{matrix}}

Across all 72 completed cells, `trip_d` is 1.046–1.047 µs and `GATE` < 1 V is
1.333–1.335 µs for every hard case (1.8×, 3× and 4×), every corner and every
temperature. `GATE` < 0.33 V is 1.649–1.651 µs. The soft case `b_s` trips at
27.646 µs. That timing is the ideal clock's: four hard decisions at a fixed
4.718 MHz strobe plus the G1_GATE/pad fall. The matrix therefore does not
show how the trip time moves with the oscillator's own PVT spread. Section 6
gives the oscillator frequencies.

`VDDA` (armed, from the `c_mid` rows): 957 µA (ss/−40 °C) to 2188 µA (ff/125 °C);
1421 µA at tt/27 °C (BGR 319.7 µA, SENSE 1101.4 µA, TRIP 3.3 V 0.01 µA).
BGR586 alone: 218.7 µA (ss/−40 °C) to 484.0 µA (ff/125 °C).

## 2. Supply extremes (`bgr=sch`, `inpads nodcn`, ideal clock; VDDA tied to IOVDD)

{{supply}}

`GATE` < 1 V moves with `IOVDD` (1.306–1.310 µs at 3.0 V, 1.358–1.361 µs at 3.6 V)
because `GATE` starts from `IOVDD`. It does not move with `VDD`. `VDDA` is 1415 µA
at 3.0 V and 1427 µA at 3.6 V (tt/27 °C). Supply extremes on `b_s`, `f_mid`, `c`
and `e20`: **not run**.

## 3. Additional trip-path runs

### 3a. Nominal, stock SENSE pads (`bgr=sch`, run tag `c1414n2`, tt/27 °C)

{{n2}}

The four "stopped" runs were ended externally at about 4384 s (exit −15), before
the 30 µs load event. The simulated time was still advancing. They are **not run
to completion**. The 3× and 4× cases with stock pads have no result. Their
nodcn equivalents are in section 1.

### 3b. Corners without the pad deviation (`bgr=sch`, stock SENSE pads, run tag `c1414k1`)

{{k1}}

### 3c. Hot and 3×/4× cases (`bgr=sch`, `inpads nodcn`, run tag `c1414hot_*`)

{{hot}}

The compact timeline (28 µs, `--timeline compact`) trips 0.011 µs later than the
default timeline in every pair (`GATE` < 1 V 1.345–1.346 µs vs 1.333–1.334 µs).
The fault falls at a different phase of the strobe.

### 3d. Both extractions (BGR586 C-PEX **and** TRIP NF4 C-PEX; stock SENSE pads; run tags `c1414full`, `c1414fullc`)

{{full}}

Only the compact `c_mid` completed with both extractions: `GATE` < 1 V 1.345 µs,
the same as the `bgr=sch` compact runs. The default-timeline `q` and `c_mid`
reached 33.2 and 33.3 µs of 44 and 42 µs in 25 000 s and are **not run to completion**.

## 4. Hard-threshold amplitude sweep (`c_mid` timing, hard code 200 = 39.25 mV; tt/27 °C; `bgr=sch`, `inpads nodcn`)

Run tags `c1414thr` and `c1414thr3` (`--fault-mult`). The three `c1414thr2` runs
are invalid (RTL-loading defect, 72 s) and were re-run as `c1414thr3`.

{{thr}}

**Simulated characterization result, not a sign-off verdict.** At code 200 the
effective hard threshold on the chip netlists lies between 30.00 mV (no trip) and
31.25 mV (trip), which is 8.0–9.25 mV (41–47 LSB) below the code value. The block
strobe-train bench on the TRIP NF4 extraction gives the same kind of offset
(`../../../g1_trip/sim/postlayout/README.md`, `results_postlayout_nf4.txt`). There
the hard comparator trips 40–56 LSB (7.9–11.0 mV of shunt) below its DAC code
over tt/ss/ff at codes 200 and 254, with a corner spread of 10–11 LSB. The soft
path stays within 1 LSB. The mechanism: the soft comparator's reset kick lands
on the shared input `icmp` at the hard strobe. Consequences:

- Uncalibrated, the `c_mid` stimuli at 0.80T and 0.89T trip. These are inside
  the §6 no-trip region (≤ 0.9T) of the code value. Calibration of the hard
  path must therefore bracket the **effective** threshold, not the code. Expect
  the calibrated code to land about 45–50 codes above the nominal code (effective
  threshold about 8–11 mV below code).
- The usable hard range is about 25–40 mV of shunt instead of 25–50 mV.
- Just above the effective threshold (1.25×, 31.25 mV) the trip comes one
  strobe period (0.212 µs) later: `GATE` < 1 V at 1.546 µs.
- A parked 2× hold-capacitor candidate (`../../../g1_trip/layout/candidates/nf4_hold2x/`)
  halves the offset in the block bench (−21 to −25 LSB at code 200). It is **not
  adopted**: owner decision pending. None of the runs here use it.

## 5. Power-up (`--front beh`, PDK pad models with `pads nodcn`, `bgr=sch`, gear)

`gA`: `IOVDD`/`VDDA` ramp 1–3 µs, then `VDD` 5–7 µs (IO first). `gB`: `VDD` first.
`EN` is low until 12 µs in both. `_pd` adds 10 kΩ from `GATE` to ground.

| Case | Corner, T | Status | `GATE` max while EN low (V) | `GATE` > 1 V from–to (µs) | Load charge (µAs) | Wall (s) | Log |
| --- | --- | --- | --- | --- | --- | --- | --- |
{{pwr}}

IO-first (`gA`, `gA_pd`) drives `GATE` to `IOVDD` for 4.2–4.4 µs at all three
corners, with or without the 10 kΩ pull-down. The load conducts 1 A for that
time. This is the IO-cell property that P1 excludes (the output pad's driver gate
signals come from core-powered level-up cells). A 10 kΩ pull-down does not hold
`GATE` low against the pad driver. With IO first, only the independent load-bus
inhibit (P2) keeps the FET off. As a power-order safety condition, IO-first
**failed**, which is expected and confirms P1. Core-first (`gB`, `gB_pd`)
**passed** at ss/125 °C and ff/−40 °C. `gA`/`gA_pd` with the stock pads at
tt/27 °C (`c1414n1`) timed out at 8800 s and are **not run to completion**.

## 6. Transistor-level oscillator clocking the RTL (`osc` case: G1_OSC R0.95, BGR586 C-PEX unless `bgr=sch`, SENSE R100; no TRIP, no pads)

{{osc}}

The ideal clock of every trip deck is 9.436 MHz. The chip-context oscillator
depends on the time step. At tt/27 °C and 0.5 ns maximum step it runs at
9.443–9.483 MHz (0.1–0.5 % above the ideal clock). With 1, 2 and 3 ns steps it
reads 9.48–9.50, 9.61–9.74 and 9.86 MHz, and 10.14 MHz with no step limit. The
corner runs used gear with 2 ns (+3.2 % against the 0.5 ns value at tt). Their
7.61 MHz (ss/125 °C) and 12.43 MHz (ff/−40 °C) therefore carry that step bias
and are not corrected. The 2 ns tt runs are identical with and without the
`bgr=sch` override and the Schmitt receiver (9.74156 MHz). Eleven tt/27 °C
variants (gear or trap, 1 ns or no step limit) failed with "timestep too small" on
the oscillator's `dparea` diode `d.xosc.xd52.d1`, and one timed out. The two
supply-corner jobs failed on the same diode: ss/125 °C at `VDD` 1.08 V, and
ff/−40 °C at `VDD` 1.32 V, whose job id says `vddlo`. The ff/−40 °C, `VDD` 1.32 V
re-run `c1414oscv2` (trap, 1 ns, Schmitt) completed at 12.41 MHz. The matching
ss/125 °C, `VDD` 1.08 V trap re-run is **not run**: its launch at 04:27 was
refused by the runner's evidence-overwrite guard (a same-tag deck from a parser
test already existed in `build/`) and produced no log. The ss/125 °C, 1.08 V
oscillator point therefore has no completed run.

## 7. Temperature-to-frequency (`q` with `--t2f tl`, gear, `bgr=sch`, `inpads nodcn`)

{{t2f}}

The G1_T2F block result is 1.59 MHz at 25 °C and 5.2 kHz/°C
(`../../../g1_t2f/README.md`). On the chip netlists it is 1.518 MHz at 27 °C,
about 5 % below the block value but inside the ±15 % pre-calibration spread.
The slope from 27 to 125 °C is 4.9 kHz/°C. At −40 °C both attempts with
`bgr=sch` stopped with "timestep too small" on the BGR HBT `xbgr.xq56`. A third
attempt, `c1414t2fv3`, used the BGR586 extraction instead of `bgr=sch` and
stopped with "timestep too small" at 11.80 µs on the T2F HBT `xt2f.xq42`. T2F at
−40 °C is therefore **not run to completion** (numerical, three attempts, all gear: `bgr=sch` with 5 ns
maximum step; `bgr=sch` with 2 ns and `xtrtol` 7; the BGR586 extraction with
5 ns).

## 8. Invalid, superseded and failed night jobs

{{inval}}

## What this establishes

- On the chip-of-record block netlists (SENSE R100 partial C, TRIP NF4 C-PEX,
  GATE PEX, BGR586 schematic with its DC-identical extraction), the real RTL
  closes the breaker loop at tt/ss/ff × −40/27/85/125 °C for the cells marked
  passed. In-range (1.8×) and over-range (3×, 4×) hard faults drive `GATE`
  below 1 V 1.31–1.36 µs after the fault, far inside the 10 µs target. The
  nominal load does not trip, the soft window trips once, and `EN` re-arms.
- The same holds at the supply corners run (VDD 1.08/1.32 V × VDDA 3.0/3.6 V at
  tt/27 °C, plus ss/125 °C low-low and ff/−40 °C high-high).
- The analog-rail current on these netlists is 0.96–2.19 mA over corners, and
  1.42 mA at tt/27 °C.
- The effective hard threshold at code 200 is 30.0–31.25 mV on the chip netlists.
  Hard-path calibration must bracket it (section 4).
- IO-first power-up drives `GATE` high, even with a 10 kΩ pull-down. P1 and the
  P2 inhibit are hard board requirements.

## What this does not establish

- **No full-chip PEX.** The block extractions are separate: BGR586 C only, TRIP NF4 C
  only, SENSE partial field, OSC isolated macro. The inter-macro wiring is
  estimated. Only one compact run used both the BGR586 and TRIP extractions.
- **Ideal clock.** Trip timing at every corner uses the tt/27 °C oscillator
  frequency. The oscillator's own spread (section 6) and a stopped clock are
  not in the trip decks.
- **Pad deviations.** The matrix, sweep and T2F runs use `inpads nodcn` and the
  power-up runs use `pads nodcn`. The stock pad models are not verified by them.
  The stock-pad 3×/4× runs are not run to completion.
- `GATE`/`FAULT_N` output pads are fitted behavioural drivers in the trip decks;
  `EN`/`SCLK`/`SDI` are ideal copies. RTL co-simulation, not gate level.
- No mismatch, no joint calibrated Monte Carlo, no brownout, no simultaneous
  ramps, no real FET/board. The default 1 ms `SOFT_TIME` window at transistor
  level is not covered (`b_s` uses 256 osc_clk).
- Cells still running or not run to completion are listed above. They are not
  passed.

# POSTSUB_20260928, track T4: remaining simulations on the r4 chip of record

Every number in this record is **simulated**. Nothing here is measured.

**Status: final (2026-09-29 21:40 CEST).** 118 chip-deck runs (91 completed, 27 failed or stopped, each listed with
its last simulated time and solver message), 3 operating-point checks and 3 pad-deck runs; 427 CPU-hours of wall time,
one CPU per run, from 2026-09-28 14:18 to 2026-09-29 21:35 CEST.

## Summary (simulated)

| Item | Result |
| --- | --- |
| 1. T2F at −40 °C on the chip netlists | **passed**: 1.17961 MHz (12 periods), −1.79 °C from the block 25/100 °C line; 85 °C 1.80236 MHz (+0.09 °C); ss/27 °C 1.22017 MHz, ff/27 °C 1.91547 MHz (the corners scale the line by 0.804 / 1.262) |
| 2. Full-chip mismatch MC, tt/27 °C | `c_mid` 1.25×: **50/50 seeds passed** (no trip); `q`: **12/12 passed**; hard crossing after a calibration sweep on 12 seeds: 121 … 135 (ideal 127.1), within 3 codes of the static SENSE/BGR/DAC estimate; static crossing over 50 seeds 126.9 ± 3.1 codes (0.6 mV of shunt, 1σ) |
| 3. Stock pad diodes | **not run to completion**: six option sets stop at 1.19 ns (power-up) or 0.70–1.68 µs (functional) |
| 4. 3.3 V dropout | **all three completed**: `armed_io0` reconnects the load and trips spuriously 1.07 µs after the rail returns (F4 confirmed on the full chip); `armed_io2` (2.0 V sag) no spurious trip, then trips on the fault; `trip_io0` stays tripped |
| 5. ff/−40 °C 1.05×, calibration at ss/ff, other rows | ff 1.05× **passed** (no trip); hard crossing 127 ± 1 (ss/125 °C) and 129 ± 1 (ff/−40 °C), soft 129 ± 1 at both; `b_s` window rows at tt and ff **passed**; oscillator at ss/125 °C, 1.08 V **passed** (7.308 MHz, `GATE` < 1 V 2.035 µs); 1 ms proportional ramp completed (`GATE` 1.70–2.06 V peak) |

## Scope

This track reruns existing decks for the specification rows that were *not run* or *not run to completion*.
It adds no new circuit or stimulus. The work list, in order:

1. T2F at −40 °C on the chip netlists, then 85 °C and ss/ff.
2. Full-chip mismatch Monte Carlo: case `c_mid` at 1.25× (hard code 200) and case `q`, tt/27 °C.
3. Stock pad diodes (`--pads pdk`): the power-up and functional runs that stalled before.
4. The 3.3 V dropout cases `armed_io0`, `armed_io2` and `trip_io0`.
5. The ff/−40 °C 1.05× case, and the calibration rehearsal at ss/125 °C and ff/−40 °C.

## Deck and tools

Every run uses the r4 full-chip layout-netlist deck of [`../../FULLCHIP_CDL_R4_20260927.md`](../../FULLCHIP_CDL_R4_20260927.md) (`r4a`), unchanged unless a row says otherwise:

| Item | Value |
| --- | --- |
| Chip netlist | `blocks/g1_padring/netlist/g1_chip_top_1414_r4.cdl`, SHA-256 `e060c0c59a168e5b69b0c47dc31cbfe4f4444d2ec8af62960c339c1230a2c99f` (chip of record r4, GDS `225d0b53…`) |
| Block views | `--netlist pex --blockset c1414r4`: BGR586 kpex `01227a3d`, SENSE R100 partial C `ffb14762`, TRIP `nf4_novclk` kpex `6f518e07`, GATE PEX `e91617f5`, T2F PEX `441edabc` |
| Interconnect | `--interconnect extracted` (`ddc88cc7`, C only) |
| Digital | frozen ECO RTL (`--rtl-dir eco_20260925`, register map 1.2) through `d_cosim` |
| Pads | `--pads nodcn` (documented deviation: `dantenna` removed from the IO cells), except item 3 (`--pads pdk`) |
| Solver | gear; maximum step and tolerance per row |
| Clock | ideal 9.436194721 MHz |
| T2F | on from reset |
| PDK | IHP-Open-PDK `84374023ee8b4b126bebbba67fcbada0a9c0ff0b` (`/foss/pdks/ihp-sg13g2/COMMIT`, checked by `flow/run.sh`) |
| Simulator | ngspice-46 (log header of every run), Icarus Verilog `d_cosim` |
| Container | `tapeoutbench-eda:latest`, `sha256:ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2` (`flow/run.sh` identity check) |
| Runner | `run_top.py` `477eb0e9…` for every run; `run_top_cdl.py` `9f6c42de…` (the version of the late r4 runs; first 16 launches), `de704f53…` (5 runs) and `cc64d387…` (97 runs). The later two are track T1's edits, which add the `--interconnect extracted-rc` option (committed in `b4aef336e`). Deck check: with the options used here, `cc64d387` builds a deck line-identical to the r4b deck of `9f6c42de` (`c_mid` compact `--tstop 19`, after normalising run id, build path and RTL file name), and the `de704f53` MC deck of seed 80003 is line-identical to the `cc64d387` deck of seed 80004 after normalising the seed. Launched through [`psrun.py`](psrun.py) |

[`psrun.py`](psrun.py) imports the runners unchanged and adds four things:
- **`--ps-build`**: the build directory (deck as run, compiled RTL, full waves and state files) moves to bulk storage.
- **`--ps-mc-seed`** (item 2): the PDK's own mismatch sections and per-instance switch, described under item 2.
- **`--ps-drop`** (item 4): the V33/Vprof/tstop substitutions of the red-team dropout generator.
- The runner's progress record is sampled every 60 s instead of 5 s (the first 16 launches used 5 s).

Logs, run JSONs, deck copies and decimated waves are written by the runners to `sim/logs/`, `sim/decks/` and `sim/results/waves/` as usual; after each run they were moved to bulk storage (section "Evidence kept outside the tree"). The runner's summary lines also went to the shared `sim/results_cdl.txt` (not part of this record).

Process:
- Every run was launched detached with `flow/launch_pinned.sh`, one ngspice per CPU, at nice 0.
- CPUs 101–105 and 107–117 (the T4 allocation).
- The mismatch runs are fed to free CPUs by a queue scheduler (`${BULK}/postsub-20260928/sims/sched/sched.py`); it
  queues one reltol 5e-4 retry for a mismatch run that stops numerically. For two calibration seeds a hedge
  (2 ns, reltol 5e-4) ran next to the retry; the one that finished second was stopped.
- A run that I stopped is marked "stopped" with the reason. No run was stopped after its result was emitted unless a
  sibling had completed.
- Machine load average 95–150 (other users) during the campaign; per-run speed 1.3–3.3 µs of simulated time per 1000 s.

## Results

The per-run summary (status, wall time, last simulated time, solver message, result lines) is [`runs.json`](runs.json) / [`runs.csv`](runs.csv), written by [`summarize.py`](summarize.py). Tags below drop the common infix `_cdle060c0c5_rtleco20260925`; the full tag is `cdl_<case>_pex_<corner>_<T>C_<method>…_<run id>`.

### Item 1: T2F on the chip netlists

Case `q` (44 µs, nominal 1 A load, armed, no event; T2F on from reset in PTAT mode). The T2F frequency is measured
over 12 periods in 32–44 µs (the `T2F` result line). Every run below is on the r4 chip deck; the three earlier −40 °C
attempts used the hand-wired `c1414` deck ([RESULTS_20260925](../RESULTS_20260925.md) §7).

| Corner / T | Run | Status | f<sub>T2F</sub> (MHz) | T2F `VDDA` (µA) | Chip `VDDA` (µA) | No trip | Wall (s) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| tt / −40 °C | `q…tt_-40C…maxstep1ns…ps4` | **passed** (completed) | **1.17961** | 32.57 | 1117.5 | `tripped` max 6.4 mV, `GATE` min 3.2980 V | 16 816 |
| tt / −40 °C, twin | `…optreltol5em4…ps4` (reltol 5e-4) | not run to completion (stopped at 39.08 µs: the primary completed) | — | | | | 17 260 |
| tt / 27 °C (reference) | `r4a` q ([FULLCHIP_CDL_R4](../../FULLCHIP_CDL_R4_20260927.md)) | passed | 1.51725 | 41.41 | 1462.5 | yes | — |
| tt / 85 °C | `q…tt_85C…ps4` | **passed** (completed) | **1.80236** | 49.04 | 1761.0 | `tripped` max 8.3 mV, `GATE` min 3.2987 V | 18 488 |
| ss / 27 °C | `q…ss_27C…ps4` | **passed** (completed) | **1.22017** | 35.93 | 1288.2 | `tripped` max 7.7 mV, `GATE` min 3.2988 V | 16 470 |
| ff / 27 °C | `q…ff_27C…ps4` | **failed** (numerical) at 19.0776 µs: `Timestep too small … xchip.xi_core_u_bgr.xq736` (BGR HBT), 7388 s | — | | | | 7388 |
| ff / 27 °C, rerun | `q…ff_27C…optreltol5em4…ps4b` (reltol 5e-4) | **passed** (completed) | **1.91547** | 48.25 | 1675.4 | `tripped` max 6.8 mV, `GATE` min 3.2980 V | 21 049 |

Other T2F readings on the same r4 deck, from the compact `c_mid` runs of the r4 campaign (2 periods, 13.86–16 µs,
before the fault; `r4c` logs): tt/125 °C 1.9956 MHz, ss/125 °C 1.6034 MHz, ff/−40 °C 1.4918 MHz, tt/−40 °C 1.1819 MHz.
At tt/27 °C the 2-period value is 1.51635 MHz against 1.51725 MHz over 12 periods (−0.06 %).

Accuracy at typical process (derived from the table, not a separate run):
- The block-level BGR586 line of [`g1_t2f/README.md`](../../../../g1_t2f/README.md) (25/100 °C calibration, 1.507431 MHz at 25 °C,
  4.9085 kHz/°C) predicts 1.18838 MHz at −40 °C and 1.80194 MHz at 85 °C. The chip values are 8.8 kHz below at −40 °C
  (**−1.79 °C**) and 0.4 kHz above at 85 °C (**+0.09 °C**). The block-level nominal held-out residual at −40 °C was −1.26 °C.
- A chip-level two-point calibration at 27 and 85 °C (4.9157 kHz/°C) gives −1.69 °C at −40 °C and −0.42 °C at 125 °C
  (with the hand-wired-deck q value 1.99692 MHz; −0.68 °C with the 2-period r4 value). Inside the ±2 °C criterion at typical process.
- Process corner: the ss/tt frequency ratio is 0.804 at 27 °C (12 periods: 1.22017 / 1.51725 MHz) and 0.803 at 125 °C
  (2 periods: 1.6034 / 1.9956 MHz); the ff/tt ratio is 1.262 at 27 °C (1.91547 / 1.51725 MHz) and 1.265 at −40 °C
  (2 periods: 1.4918 / 1.17961 MHz). Each corner therefore scales the whole f(T) line by one factor, which a per-part
  two-point calibration removes (derived from two temperatures per corner only). Read through the typical line, the ss part at 27 °C would be about 60 °C low (0.297 MHz at 4.9 kHz/°C).

Result: **T2F at −40 °C on the chip netlists: passed (completed)**, 1.17961 MHz. 85 °C: passed, 1.80236 MHz. ss/27 °C: passed,
1.22017 MHz. ff/27 °C: passed on the reltol 5e-4 rerun, 1.91547 MHz (the standard-tolerance run failed numerically at 19.08 µs).
Not run: T2F at ss and ff at 85 °C and the full 12-period window at ss/−40, ss/125, ff/−40 and ff/125 °C (the 2-period values above cover
three of them); supply variation; the TEMP_OUT pad.

### Item 2: full-chip mismatch Monte Carlo

**Method.** The chip deck of every other item, at tt/27 °C, with the PDK's own mismatch model set on every analog
device of the chip (`psrun.py --ps-mc-seed N`):
- the corner sections `mos_tt`, `res_typ`, `cap_typ`, `hbt_typ` are replaced by `mos_tt_mismatch`, `res_typ_mismatch`,
  `cap_typ_mismatch` and `hbt_typ_mismatch` (the model files are unchanged);
- `mm_ok=1` is set on every instance of a PDK device subcircuit that has the switch (`sg13_lv/hv_nmos/pmos`, `rppd`,
  `rhigh`, `rsil`, `cap_cmim`): 253 in the translated chip (IO cells and top level) and 3385 in copies of the block
  extractions (BGR586 735, SENSE R100 138, TRIP `nf4_novclk` 2347, GATE 78, T2F 87). The copies are hash-recorded
  per run in `${BULK}/postsub-20260928/sims/mcnet/mc_<tag>.json`;
- `.option seed=N` sets the draw. It is read at parse time: checked on a two-device deck (reproducible per seed,
  different between seeds) and on the chip deck (operating points of seeds 1 and 2 differ from nominal:
  `VREF` 1.04539 / 1.04551 V against 1.04500 V; `ISENSE` 1.00021 / 1.01166 V against 1.00748 V).
- The HBT mismatch section of this PDK revision has no per-instance draw (`sg13g2_hbt_mod_mismatch.lib` has no
  `agauss`); the HBTs take the typical card. The digital macro is RTL (no devices).
- The same seed gives the same draw in `c_mid` and `q`: seed 80003 gives `VREF` 1.04658 V and `ISENSE` 1.49265 V in both.

Cases: `c_mid` compact at **1.25×** (31.25 mV of shunt at hard code 200, whose nominal threshold is 39.25 mV:
a no-trip point 8 mV below the code), `--tstop 19` (3 µs, 14 comparator strobes after the event), gear 1 ns; and `q`
(44 µs, 1 A, no event), gear 1 ns. Seeds 80001–80050 (`c_mid`) and 80001–80012 (`q`), run ids `psmc<seed>`.
**Retry rule:** a seed that fails numerically is rerun once with reltol 5e-4 (the r4 campaign's mitigation for the
BGR HBT stops), run id `psmc<seed>rt`; a seed that fails twice counts as a numerical failure.

Pass criterion (electrical): no trip (`tripped` below 0.6 V) and `GATE` above 3.0 V throughout.

**Static crossing code (derived).** The DAC thresholds are linear in the code, vth = s·(code + 254.92) (from the
nominal r4 q run: vth_soft 0.804266 V at 153, vth_hard 1.00340 V at 254). Per seed, s comes from the QUIET threshold
at the written code and the crossing code at 1 A is icmp/s − 254.92. This contains the SENSE, BGR and DAC-string
mismatch but **not the comparators' own offset** (the calibration sweeps below measure the whole crossing). Per-seed values:
[`mc_seeds.csv`](mc_seeds.csv); statistics: [`mc_summary.json`](mc_summary.json) ([`analyze_mc.py`](analyze_mc.py)).

**Calibration sweeps per seed (added within the budget).** For 12 seeds chosen across the static-crossing range
(extremes and middle), case `cal` hard at tt/27 °C, a descending 2-code window of 9 codes centred on the seed's
static estimate (`--cal-codes A:A-18:-2`, A = static rounded to even + 8), gear 1 ns; for three of them also `cal`
soft. The crossing is the code between the first firing code and the silent code above it (±1 code). A sweep that
stopped numerically after its first firing emitted the CAL measures on the partial run; it is counted as *not run to
completion after the crossing (numbers usable)*, as in the r4a record.

Results (simulated, tt/27 °C; per seed in [`mc_seeds.csv`](mc_seeds.csv)):

| Case | Seeds | Completed (of which on the retry) | Electrical pass / fail | Numerical failure (after the retry) | First-attempt numerical stops |
| --- | --- | --- | --- | --- | --- |
| `c_mid` 1.25× (31.25 mV, code 200) | 50 | 50 (4) | 50 / 0 | 0 | 4 |
| `q` (1 A, 44 µs) | 12 | 12 (4) | 12 / 0 | 0 | 4 |
| `cal` hard | 12 | 12 (2) | 12 / 0 | 0 | 2 |
| `cal` soft | 3 | 3 (0) | 3 / 0 | 0 | 0 |

| Quantity (simulated) | `c_mid` | `q` |
| --- | --- | --- |
| `tripped` maximum (mV) | mean 7.32, sd 0.32, 7.08 … 8.69 (n = 50) | mean 7.27, sd 0.24, 7.12 … 8.03 (n = 12) |
| QUIET `VREF` (V) | mean 1.04496, sd 0.00086, 1.04298 … 1.04658 (n = 50) | mean 1.04499, sd 0.00089, 1.04396 … 1.04658 (n = 12) |
| QUIET `ISENSE` at 1 A (V) | mean 1.5070, sd 0.0131, 1.4745 … 1.5349 (n = 50) | mean 1.5092, sd 0.0149, 1.4871 … 1.5349 (n = 12) |
| static hard crossing code (derived) | mean 126.9, sd 3.1, 120.3 … 134.7 (n = 50) | mean 127.8, sd 3.7, 123.0 … 134.9 (n = 12) |
| static soft crossing code (derived) | mean 127.1, sd 3.1, 120.6 … 135.1 (n = 50) | mean 127.7, sd 3.7, 122.9 … 135.0 (n = 12) |
| T2F frequency (MHz; `c_mid`: 2 periods, `q`: 12 periods) | mean 1.5163, sd 0.0057, 1.5031 … 1.5294 (n = 50) | mean 1.5157, sd 0.0055, 1.5085 … 1.5224 (n = 12) |

| Seed | Static hard (derived) | Calibrated hard crossing | Hard − static | Static soft (derived) | Calibrated soft crossing | Run(s) and status |
| --- | --- | --- | --- | --- | --- | --- |
| 80041 | 120.3 | 121 ± 1 | +0.7 | 120.6 | 123 ± 1 | hard `psmc80041` completed; soft `psmc80041` completed |
| 80032 | 121.4 | 121 ± 1 | -0.4 | 121.6 | 125 ± 1 | hard `psmc80032` completed; soft `psmc80032` completed |
| 80016 | 122.3 | 125 ± 1 | +2.7 | 122.7 | not run | hard `psmc80016` not run to completion after the crossing (numbers usable); hard `psmc80016rt` stopped by me (the first attempt is usable) |
| 80009 | 122.8 | 125 ± 1 | +2.2 | 123.0 | not run | hard `psmc80009` not run to completion after the crossing (numbers usable); hard `psmc80009rt` stopped by me (the first attempt is usable) |
| 80018 | 123.5 | 125 ± 1 | +1.5 | 123.5 | not run | hard `psmc80018` completed |
| 80003 | 125.6 | 125 ± 1 | -0.6 | 125.9 | not run | hard `psmc80003` completed |
| 80014 | 127.5 | 127 ± 1 | -0.5 | 127.7 | not run | hard `psmc80014` completed |
| 80001 | 127.9 | 129 ± 1 | +1.1 | 128.2 | not run | hard `psmc80001` failed; hard `psmc80001rt` completed; hard `psmc80001h` stopped by me (the retry completed) |
| 80022 | 130.8 | 131 ± 1 | +0.2 | 131.0 | not run | hard `psmc80022` failed; hard `psmc80022rt` stopped by me (the hedge psmc80022h completed); hard `psmc80022h` completed |
| 80037 | 131.4 | 133 ± 1 | +1.6 | 131.4 | not run | hard `psmc80037` completed |
| 80007 | 133.5 | 133 ± 1 | -0.5 | 133.8 | not run | hard `psmc80007` completed |
| 80008 | 134.7 | 135 ± 1 | +0.3 | 135.1 | 135 ± 1 | hard `psmc80008` completed; soft `psmc80008` completed |

Reading of the tables:
- **No electrical failure in 77 mismatch runs.** No seed trips at 1.25× (the largest `tripped` excursion is 8.7 mV),
  and no seed trips or loses `GATE` in the 44 µs `q` window. The four `c_mid` and four `q` seeds that stopped
  numerically completed on the reltol 5e-4 retry (list below).
- **Hard threshold spread.** The static crossing (SENSE, BGR and DAC mismatch) is 126.9 ± 3.1 codes over 50 seeds,
  range 120.3–134.7 (−6.8 to +7.6 codes, −1.3 to +1.5 mV of shunt, from the ideal 127.1). The 12 calibration sweeps
  land within −0.6 … +2.7 codes of their seed's static estimate: the comparator's own offset adds at most about
  3 codes (0.5 mV) at chip level. The spread is dominated by the SENSE offset (`ISENSE` at 1 A: sd 13 mV at the
  output, 0.65 mV at the input).
- **Hard − soft** after calibration: −2 (80041), −4 (80032), 0 (80008), against −2 on the nominal part (r4b).
- **For the bench:** an uncalibrated part sits within about ±8 codes (±1.5 mV) of the code at room temperature;
  per-part calibration (H6) stays required for the ±0.5 mV target, and its range is ample (signed correction
  −128 … 127).
- **T2F spread with mismatch** at 27 °C: sd 5.5 kHz over 12 seeds (12 periods), about 1.1 °C (1σ) before calibration.
- Mismatch runs that did not complete (all "Timestep too small" on a BGR586 HBT, `xchip.xi_core_u_bgr.xq736`
  unless stated; last simulated time in µs):

  | Run | Stop | Outcome |
  | --- | --- | --- |
  | `c_mid` `psmc80002` / `80006` / `80044` / `80049` | 17.595 / 16.111 (`xq760`) / 8.905 / 10.600 | each completed on its `…rt` retry |
  | `q` `psmc80001` / `80005` / `80008` / `80012` | 19.927 / 24.589 / 16.111 / 36.566 | each completed on its `…rt` retry |
  | `cal` hard `psmc80001` / `80022` | 23.953 / 18.018 (before the crossing) | `psmc80001rt` and `psmc80022h` completed |
  | `cal` hard `psmc80009` / `80016` | 51.827 / 48.648 of 55 µs (after the crossing) | not run to completion after the crossing, numbers usable; their retries were stopped at 5.3 / 7.3 µs |
  | `cal` hard `psmc80001h` / `psmc80022rt` | stopped at 38.36 / 51.02 µs | the sibling run had completed |
- Not run: the mismatch MC at other corners and temperatures; calibration sweeps for the other 38 seeds; mismatch
  with the stock pad diodes.


### Item 3: stock pad diodes (`--pads pdk`)

`--pads pdk` keeps every `dantenna`/`dpantenna` of the translated CDL, i.e. the stock PDK models on all 22 pads, the
`EN`/`SCLK`/`SDI` input pads included. On the CDL deck this is the chip-level form of `--pads pdk --inpads model`.

| Case | Options | Status | Last simulated time | Solver message | Wall (s) |
| --- | --- | --- | --- | --- | --- |
| `c_mid` compact 1.8×, tt/27 °C, `--tstop 19` | gear, 1 ns, reltol 5e-4 | **not run to completion** (stalled; stopped after 2707 s with no progress for about 1300 s) | 1.05575 µs | none (stall: steps of about 1e-20 s) | 2707 |
| same | gear, 1 ns, `.option klu` | **failed** (numerical) | 1.67927 µs | `Timestep too small … trouble with node "b.xchip.xi_core_u_osc.bosc_clk#branch"` (the same time and node as the r3 stock run) | 202 |
| same, `--osc tl` (transistor-level oscillator, no ideal-clock source) | gear, 1 ns | **not run to completion** (stalled; stopped after 5631 s) | 0.70434 µs | none (stall) | 5631 |
| `gB` core-first power-up, `--por-pin`, tt/27 °C | gear, 2 ns, reltol 5e-4 | **not run to completion** (stalled; stopped after 1392 s) | 1.1861 ns | none (stall) | 1392 |
| same | trap, 2 ns, `.option klu` | **not run to completion** (stalled; stopped after 581 s) | 1.18623 ns | none (stall) | 581 |
| same | gear, 2 ns, reltol 1e-5 abstol 1e-14 vntol 1e-7 (the `--accuracy tight` set) | **failed** (numerical) | 1.18579 ns | `Timestep too small; time = 1.18579e-09, timestep = 2.5e-21: trouble with node "v.xchip.vm_tripa#branch"` | 95 |

Result: with the stock pad diodes the chip deck still does not pass the first microsecond. Every option set stops at
the same points as the r3 attempts (power-up 1.19 ns, functional 1.06 or 1.68 µs), whatever the method, tolerance or
linear solver. This is consistent with the `dantenna` reverse-bias model discontinuity at 3·n·V<sub>T</sub>
([power_io F5](../../../../../review/redteam-20260927/power_io/FINDINGS.md)). The `nodcn` deviation therefore
remains the only way to run the chip deck. Stock-pad behaviour is **not run to completion** on r4.

### Item 4: 3.3 V dropout (`IOVDD` = `VDDA` rail, `VDD` and `EN` held), tt/27 °C

Decks: the r4 `c_mid` compact deck with the red-team substitutions (`psrun.py --ps-drop`, `DROP_CASES`: V33 PWL,
load profile, stop time). The timeline analysis is [`analyze_drop.py`](analyze_drop.py); its outputs are
`drop_<case>.json`.

| Case | Run | Status | Result (simulated) |
| --- | --- | --- | --- |
| `armed_io0`: armed at 1 A, rail 3.3 → 0 V at 13–14 µs, 0 V to 17 µs, back at 18 µs; 1.8× fault at 21 µs | `ps4drop-armed_io0`, gear 1 ns, 10 355 s | **completed** | `GATE` follows the rail down (0.38 V at the bottom) and is back above 3 V at 18.36 µs: **the load reconnects by itself**. `VREF` 1.045 → 0.524 V, 0.549 V when the rail returns, not back within 1 % by 27 µs. `icmp` > `vth_hard` from 18.04 µs. **Spurious hard trip at 19.07 µs** (cause 2, 1.07 µs after the rail returned, at nominal load, 1.9 µs before the fault); `GATE` < 1 V at 19.46 µs; latched at the end. This reproduces red-team finding F4 on the full chip. |
| `armed_io2`: as above, sag to 2.0 V | `ps4drop-armed_io2`, gear 1 ns | **failed** (numerical) at 18.6547 µs, `Timestep too small … trouble with xchip.xi_core_u_dut.xq1` (the DUT HBT), 7825 s | see the rerun row |
| `armed_io2`, rerun | `ps4bdrop-armed_io2`, gear 1 ns, reltol 5e-4, 13 225 s | **completed** | `GATE` follows the rail to 2.00 V during the sag (a logic-level FET stays on) and is back at 3.3 V with the rail. `VREF` dips to 1.0241 V (−2.0 %) and is within 1 % when the rail returns. **No spurious trip.** The 1.8× fault at 21 µs trips: `trip_d` 22.25 µs (1.25 µs after the fault, cause 2), `GATE` < 1 V at 22.64 µs (1.64 µs after the fault; undisturbed r4 `c_mid`: 1.164 / 1.543 µs). |
| `trip_io0`: 1.8× fault at 16 µs (hard trip), rail to 0 V at 19–24 µs, fault persisting | `ps4drop-trip_io0`, gear 1 ns, 11 526 s | **completed** | Trip as the r4 `c_mid` (`trip_d` 1.1639 µs, `GATE` < 1 V 1.5432 µs after the fault, cause 2). Through and after the dropout `GATE` stays ≤ 0.55 mV and `tripped` is 1.2 V at the end: **the breaker stays tripped** (F4). |

On r3 these three decks were stopped at 11.9–13.1 µs (about 3000 s per µs at the dip). On r4, under a lower machine
load, the dip itself ran at about 1000 s per µs.

### Item 5: ff/−40 °C 1.05× and calibration rehearsal at ss/ff

| Case | Run | Status | Result (simulated) |
| --- | --- | --- | --- |
| `c_mid` compact, ff/−40 °C, 1.05× (26.25 mV, code 200 nominal 39.14 mV) | `ps4`, gear 1 ns, 12 164 s | **passed** (completed) | no trip: `tripped` max 6.0 mV, `GATE` min 3.297 V, 1.05 A at the end. QUIET `VREF` 1.04208 V, equal to r4a. (r3x: this row was not run to completion; r3 tripped at 1.15× at this corner.) |
| `cal` hard, ss/125 °C, codes 136→118 step 2 | `ps4`, gear 5 ns | **failed** (numerical) at 17.7063 µs, before the first code write: `Timestep too small … xchip.xi_core_u_bgr.xq736` (BGR HBT), 7330 s | see the rerun row |
| `cal` hard, ss/125 °C, rerun | `ps4b`, gear 5 ns, reltol 5e-4, 28 760 s | **passed** (completed) | 136 … 128 silent, **126 fires**: first `cmp_hard` 35.287 µs, 0.692 µs after the code-126 write; `trip_d` 36.239 µs (cause 2). Hard crossing **127 ± 1** (tt: 127 ± 1). |
| `cal` soft, ss/125 °C, 136→118 | `ps4`, gear 5 ns, 23 975 s | **not run to completion after the crossing** (numerical stop at 54.4767 µs of 55 µs, BGR `xq736`; the CAL measures were emitted, numbers usable, as for the r4a coarse window) | 136 … 130 silent, **128 fires**: first `cmp_soft` 31.790 µs, 0.587 µs after the code-128 write; soft crossing **129 ± 1** (tt: 129 ± 1). No trip (`tripped` max 9.8 mV). |
| `cal` hard, ff/−40 °C, 136→118 | `ps4`, gear 1 ns, 27 638 s | **passed** (completed) | 136 … 130 silent, **128 fires**: first `cmp_hard` 31.683 µs, 0.480 µs after the code-128 write; `trip_d` 32.636 µs (cause 2). Hard crossing **129 ± 1** (tt: 127 ± 1). |
| `cal` soft, ff/−40 °C, 136→118 | `ps4`, gear 1 ns, 24 559 s | **passed** (completed) | 136 … 130 silent, **128 fires**: first `cmp_soft` 31.578 µs, 0.374 µs after the code-128 write; soft crossing **129 ± 1**. No trip (`tripped` max 6.0 mV). |

Calibration rehearsal: stimulus and detection as in the r4a record (1 A = 25 mV, each code held 3.39 µs, schedule in
the first line of each deck, `* CALSCHED`: 136 written at 17.64 µs, then every 3.39 µs down to 118 at 48.16 µs; 128 at
31.20 µs). The ideal crossing is 127.1 codes at tt (r4a convention), 126.9 at ss/125 °C and 127.5 at ff/−40 °C (scaled
with the corner's QUIET `VREF`). Summary of the crossings (first firing code in a descending 2-code sweep; the crossing lies between it and the silent code above):

| Corner | Ideal | Hard | Soft | Hard − soft |
| --- | --- | --- | --- | --- |
| tt/27 °C (r4b) | 127.1 | 127 ± 1 | 129 ± 1 | −2 |
| ss/125 °C | 126.9 | **127 ± 1** | **129 ± 1** | −2 |
| ff/−40 °C | 127.5 | **129 ± 1** | **129 ± 1** | 0 |

The hard crossing is within 1 LSB of the ideal at ss/125 °C and 0.5–2.5 codes (0.1–0.5 mV) above it at ff/−40 °C.
This bounds the r4 hard threshold at both corners to within about 3 LSB of the code, finer than the ±6 LSB of the
r4a ±3 % brackets, and closes "calibration rehearsal at ss/ff: not run" (single nominal part; mismatch: item 2).

### Item 5 (continued): other rows recorded as not run to completion

| Row (source) | Run | Status | Result (simulated) |
| --- | --- | --- | --- |
| 1 ms proportional ramp, `EN` low, tt/27 °C, reduced pad deck `sim_1ms_r2_nodcn` ([power_io F1](../../../../../review/redteam-20260927/power_io/FINDINGS.md); stopped at 0.519 ms on the `EN` pad `dpantenna`, maximum step 100 ns) | the red-team deck unchanged except the maximum step and options: (a) gear, 10 ns; (b) gear, 20 ns, `.option klu reltol=1e-4`; (c) trap, 20 ns | **completed** (all three, 1.5 ms) | (a) and (b) agree: `GATE` peak **2.057 V** at 0.624 ms (`VDD` 0.748 V, `IOVDD` 2.058 V), above 1 V from 0.304 to 0.624 ms, above 0.5 V from 0.228 ms. (c) trap: peak 1.696 V at 0.514 ms (`VDD` 0.617 V), above 1 V from 0.304 to 0.515 ms. The two methods place the pad level-shifter flip at different `VDD` (0.75 / 0.62 V); both put `GATE` above 1 V for 0.2–0.3 ms. Consistent with F1: a proportional ramp drives `GATE` high (P1 stands). Summaries: `pg_sim_1ms_nodcn_{a,b,c}.json` ([`analyze_pg.py`](analyze_pg.py)). |
| Transistor-level oscillator at ss/125 °C, `VDD` 1.08 V (hand-wired `c1414oscv3`: not run to completion, 14 000 s bound) | r4 chip deck, `c_mid` compact 1.8×, `--osc tl --corner ss --temp 125 --vdd 1.08`, gear 5 ns, reltol 5e-4 (the settings of r4c group E at ss), `ps4`, 14 783 s | **passed** (completed) | f<sub>osc</sub> **7.308 MHz** (1.2 V, r4c: 7.491 MHz), f<sub>cmp</sub> 3.654 MHz. Hard trip: `trip_d` 1.470 µs, `GATE` < 1 V **2.035 µs**, < 0.33 V 2.369 µs after the fault (cause 2); r4c at 1.2 V: 1.571 / 2.134 µs. |
| Soft code 153 window rows (`b_s`, `SOFT_TIME` = 1, 256 samples) at tt/27 °C and ff/−40 °C, 0.97× / 1.03× (r4c group B: not run to completion, stopped inside the 24 000 s wall; ss/125 °C passed there) | r4 chip deck, `b_s` compact, gear 1 ns, `--timeout 60000`, `ps4` | **passed** (all four completed) | tt 0.97× (1.165 A): no trip (`tripped` max 7.6 mV, `GATE` min 3.298 V), 19 972 s. tt 1.03× (1.2371 A): **soft trip**, cause 1, `trip_d` 27.764 µs after the event, `GATE` < 1 V 28.143 µs, 20 848 s. ff/−40 °C 0.97× (1.1618 A): no trip (`tripped` max 6.0 mV, `GATE` min 3.297 V), 18 582 s. ff/−40 °C 1.03× (1.2336 A): **soft trip**, cause 1, `trip_d` 27.764 µs, `GATE` < 1 V 28.033 µs, 17 696 s. |

## Not run, and not run to completion

| Item | Status | Reason |
| --- | --- | --- |
| Stock pad diodes (`--pads pdk`) on the chip deck: power-up and functional | **not run to completion** | six option sets, all stop at 1.19 ns (power-up) or 0.70–1.68 µs (functional); item 3 |
| Stock-pad 3×/4× `SENSE` faults, stock-pad slow ramps and dips of the pad deck | **not run** | the stock pads do not pass the first microsecond on any option set (item 3); not repeated |
| T2F at ss/85 °C and ff/85 °C; the 12-period window at ss/−40, ss/125, ff/−40, ff/125 °C | **not run** | not in the work list; three of them have 2-period values from the r4c logs |
| T2F supply sensitivity; `TEMP_OUT` pad | **not run** | not in the work list |
| Full-chip mismatch at corners other than tt/27 °C; calibration sweeps for the other 38 seeds (hard) and 47 seeds (soft) | **not run** | CPU budget; the sweeps ran for 12 seeds (hard) and 3 seeds (soft) |
| Mismatch of the HBTs | **not applicable** in this PDK revision | `sg13g2_hbt_mod_mismatch.lib` has no per-instance draw |
| 3.3 V dropout at corners, with 0 nF / 100 nF on `VREF`, and a `VDD` dip with the gate-level digital | **not run** | not in the work list |
| ESD (HBM/CDM), latch-up, package parasitics | **not run** | outside this track |

## Commands

Repository root; `$BULK` below stands for the T4 bulk directory `${BULK}/postsub-20260928/sims`; `W=designs/g1-guardian/blocks/g1_top/sim`.

```
C="--cdl /work/designs/g1-guardian/blocks/g1_padring/netlist/g1_chip_top_1414_r4.cdl \
   --cdl-sha256 e060c0c59a168e5b69b0c47dc31cbfe4f4444d2ec8af62960c339c1230a2c99f --blockset c1414r4 \
   --rtl-dir eco_20260925 --netlist pex --method gear --interconnect extracted"
P="python3 campaigns/POSTSUB_20260928/psrun.py cdl --ps-build $BULK/build"
# item 1
flow/launch_pinned.sh <cpu> $W 36400 <log> $P q --corner {tt --temp -40|tt --temp 85|ss --temp 27|ff --temp 27} \
    --maxstep-ns 1 [--extra-options reltol=5e-4] --timeout 36000 --run-id {ps4|ps4b} $C
# item 2 (seed N; the scheduler adds --extra-options reltol=5e-4 and run id psmc<N>rt to a retry)
flow/launch_pinned.sh <cpu> $W 36400 <log> $P --ps-mc-seed N --ps-mc-dir $BULK/mcnet c_mid --timeline compact \
    --fault-mult 1.25 --tstop 19 --maxstep-ns 1 --timeout 36000 --run-id psmcN $C
flow/launch_pinned.sh <cpu> $W 50400 <log> $P --ps-mc-seed N --ps-mc-dir $BULK/mcnet q --maxstep-ns 1 --timeout 50000 --run-id psmcN $C
flow/launch_pinned.sh <cpu> $W 60400 <log> $P --ps-mc-seed N --ps-mc-dir $BULK/mcnet cal --cal-kind hard \
    --cal-codes A:A-18:-2 --ser-start-us 4 --maxstep-ns 1 --timeout 60000 --run-id psmcN $C
# item 3
flow/launch_pinned.sh <cpu> $W 14400 <log> $P c_mid --timeline compact --tstop 19 --pads pdk --maxstep-ns 1 \
    --extra-options {reltol=5e-4|klu} [--osc tl] --timeout 14000 --run-id ps4 $C
flow/launch_pinned.sh <cpu> $W 14400 <log> $P gB --por-pin --pads pdk --maxstep-ns 2 \
    {--extra-options reltol=5e-4|--method trap --extra-options klu|--extra-options 'reltol=1e-5 abstol=1e-14 vntol=1e-7'} --timeout 14000 --run-id ps4 $C
# item 4
flow/launch_pinned.sh <cpu> $W 100400 <log> $P --ps-drop {armed_io0|armed_io2|trip_io0} c_mid --timeline compact \
    --maxstep-ns 1 [--extra-options reltol=5e-4] --timeout 100000 --run-id {ps4|ps4b}drop-<case> $C
# item 5
flow/launch_pinned.sh <cpu> $W 36400 <log> $P c_mid --timeline compact --corner ff --temp -40 --fault-mult 1.05 --maxstep-ns 1 --timeout 36000 --run-id ps4 $C
flow/launch_pinned.sh <cpu> $W 60400 <log> $P cal --cal-kind {hard|soft} --cal-codes 136:116:-2 --ser-start-us 4 \
    {--corner ss --temp 125 --maxstep-ns 5|--corner ff --temp -40 --maxstep-ns 1} [--extra-options reltol=5e-4] --timeout 60000 --run-id {ps4|ps4b} $C
flow/launch_pinned.sh <cpu> $W 60400 <log> $P b_s --timeline compact --corner {tt --temp 27|ff --temp -40} \
    --fault-mult {1.165|1.2371|1.1618|1.2336} --maxstep-ns 1 --timeout 60000 --run-id ps4 $C
flow/launch_pinned.sh <cpu> $W 60400 <log> $P c_mid --timeline compact --osc tl --corner ss --temp 125 --vdd 1.08 \
    --maxstep-ns 5 --extra-options reltol=5e-4 --timeout 60000 --run-id ps4 $C
# pad deck (1 ms ramp): the red-team deck ${BULK}/redteam-20260927/power_io/pg/sim_1ms_r2_nodcn.cir with only the
# tran maximum step / .option line changed, run as: flow/run.sh ngspice -b <copy>.cir
```

Summaries (with `PS_EVIDENCE=$BULK/evidence`, where the runner files now are): `python3 summarize.py` (runs.json, runs.csv), `python3 analyze_mc.py` (mc_seeds.csv, mc_summary.json),
`python3 analyze_drop.py <waves> --json drop_<case>.json`, `python3 analyze_pg.py <wrdata>`.

## Evidence kept outside the tree

Under `${BULK}/postsub-20260928/sims/`: `build/` (decks as run, compiled RTL, full waves and state files), `evidence/`
(the runner logs, run JSONs, progress records, deck copies and decimated waves of every run of this record, moved
out of `sim/logs`, `sim/decks` and `sim/results/waves`), `mcnet/` (the `mm_ok` copies of the block extractions and
the per-run MC transform records), `pg/` (pad-deck variants), `launch/` (launcher logs), `sched/` (scheduler, queue
and its log), `killed_niced/` (seed 80001 first started at nice 5 by mistake, stopped within 3 minutes and repeated at nice 0; its files are not used).

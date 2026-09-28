# G1 r4 candidate, full-chip characterisation phase 2 (run `r4c`, 2026-09-27/28)

Every number here is **simulated**. The runs used:
- ngspice-46 with the Icarus d_cosim;
- IHP SG13G2 open PDK `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`;
- image `tapeoutbench-eda:latest` (`sha256:ddeb6957…`, the `flow/run.sh` identity check).

This record is phase 2 of the r4 characterisation. Phase 1 (run ids `r4a`/`r4b`) has its own record, [`FULLCHIP_CDL_R4_20260927.md`](FULLCHIP_CDL_R4_20260927.md). The deck is the r3x deck of [`FULLCHIP_CDL_R3_CORNERS_20260927.md`](FULLCHIP_CDL_R3_CORNERS_20260927.md), with two changes for r4:
- **Chip CDL:** r4 `blocks/g1_padring/netlist/g1_chip_top_1414_r4.cdl`, SHA-256 `e060c0c59a168e5b69b0c47dc31cbfe4f4444d2ec8af62960c339c1230a2c99f`.
- **TRIP view:** `--blockset c1414r4`, i.e. the nf4_novclk kpex extraction `g1_trip/sim/postlayout/g1_trip_nf4_novclk_pex.spice` (SHA-256 `6f518e07…`), per [`../../g1_trip/layout/candidates/nf4_novclk/README.md`](../../g1_trip/layout/candidates/nf4_novclk/README.md).

Everything else is unchanged from r3x:
- BGR586 `01227a3d`, SENSE R100 `ffb14762`, GATE Sep-19 PEX, T2F `441edabc`, OSC R0.95 CPEX with `--osc tl`;
- frozen ECO RTL (`--rtl-dir eco_20260925`, map 1.2);
- `--interconnect extracted` (`ddc88cc7`, C only);
- `--pads nodcn`, gear, T2F on from reset, ideal 9.436 MHz clock unless `--osc tl`.

Process:
- **Launch.** One ngspice per CPU, CPUs 48–95, launched detached with `flow/launch_pinned.sh` at nice 0. The first wave of 48 started at 22:20 CEST (wall 24 000 s, `--timeout 23600`); later launches are listed under "Launch history".
- **Logs.** No log contains "mismatched XSPICE".
- **Runner.** Three working-tree versions of `run_top.py` / `run_top_cdl.py` were used. Each version only adds cases; the existing cases and the deck builder are unchanged (see "Runner changes"). The per-run record is the deck: `sim/decks/<tag>.cir`, whose SHA-256 is in the run JSON and in the table below (first 8 hex digits).

## Nominal thresholds and brackets

The r3x convention is kept: code 200 is 39.25 mV of shunt at VREF 1.04501 V, and the nominal threshold scales with the code and with the corner's QUIET VREF, T(code) = code × 0.19625 mV × VREF / 1.04501 V.
- **Code 200:** tt 39.25 mV, ss 125 °C 39.32 mV, ff −40 °C 39.14 mV.
- **Soft code 153 (DAC_SOFT reset value 0x99):** 30.03 / 30.08 / 29.94 mV.
- **Hard code 254 (DAC_HARD reset value 0xFE):** 49.85 mV (tt) and 49.71 mV (ff −40 °C).

The brackets are 0.97 × and 1.03 × of these values, applied as `--fault-mult` (1 A = 25 mV). The tt multipliers were also used at tt −40 °C and tt 125 °C, where the QUIET VREF is 1.04386 V and 1.04313 V. The brackets there are therefore 0.971 × / 1.031 × and 0.972 × / 1.032 × of the corner's own nominal.

Pass criteria:
- **0.97 × rows:** no trip (`tripped` stays below 0.6 V; cause 0).
- **1.03 × rows:** trip with the expected cause (2 hard, 1 soft).
- **Group F:** no trip before the 1.03 × step (event + 9.5 µs).
- **f_mid_c:** trip, then EN re-arm with the load restored.

On r3 every 0.97 × hard bracket would trip: its effective threshold sat 8–11.6 mV below the code (r3x record).

## Status by group

| Group | Verdict | Evidence (simulated) |
|---|---|---|
| A: FAST_EN = 1, hard code 200, 0.97 × / 1.03 × | **passed** at tt, ss 125 °C and ff −40 °C | 0.97 ×: no trip (`tripped` max 6.1–9.8 mV). 1.03 ×: fast-path latch 0.213 µs (ff −40 °C) / 0.214 µs (tt) / 0.428 µs (ss 125 °C), `GATE` < 1 V 0.481 / 0.591 / 0.987 µs, cause 2. The tt 1.03 × primary is not run to completion (16.11 µs, BGR); its reltol 5e-4 twin passed. |
| B: soft code 153, 0.97 × / 1.03 × | **passed** at tt, ss 125 °C and ff −40 °C | Single-sample rows (`b_s0`, SOFT_TIME = 0): 0.97 × silent at all three corners; 1.03 × soft trip (cause 1), trip_d 0.634 µs, `GATE` < 1 V 0.904 µs (ff) / 1.013 µs (tt) / 1.197 µs (ss). Window rows (`b_s`, SOFT_TIME = 1, 256 samples) at ss 125 °C: 0.97 × no trip; 1.03 × soft trip at 27.763 µs. The tt and ff window rows are not run to completion: stopped because they could not finish inside the wall. |
| C: hard code 200 brackets at 1.08/3.0 V, 1.32/3.6 V, tt −40 °C, tt 125 °C | **passed** | 0.97 × no trip and 1.03 × trip at all four conditions. trip_d 1.1636–1.1639 µs; `GATE` < 1 V 1.547 µs (1.08/3.0 V), 1.543 µs (1.32/3.6 V), 1.471 µs (−40 °C), 1.666 µs (125 °C). The 1.32/3.6 V rows passed on the reltol 5e-4 twin; the standard rows are not run to completion (15.05 µs, before the event). The tt 125 °C rows passed with reltol 5e-4 at 5 ns and at 2 ns, both with `--tstop 19` (3 µs, about 14 strobes, after the event); 1 ns and 5 ns at standard tolerance are not run to completion (7.85 / 13.99 µs, before the event). |
| D: hard code 254, 0.97 × / 1.03 × | **passed** at tt and ff −40 °C | 0.97 × no trip; 1.03 × trip_d 1.3756 µs (tt, one strobe later than at code 200) and 1.1637 µs (ff), `GATE` < 1 V 1.755 / 1.433 µs |
| E: c_mid 1.8 ×, transistor-level oscillator | **passed** at ss 125 °C and ff −40 °C | ss 125 °C: f_osc 7.491 MHz; 1.5712 / 1.5752 / 2.1337 / 2.4671 µs (reltol 5e-4; standard tolerance not run to completion, 5.34 µs, before the event). ff −40 °C: f_osc 12.050 MHz; 0.9025 / 0.9044 / 1.1722 / 1.3514 µs. |
| F: DAC_HARD 200 → 180 → 200 and 200 → 190 → 200 under a 0.90 × fault, then 1.03 × | **passed** (tt) | No trip during either rewrite. At code 180, whose nominal equals the 0.90 × fault (35.33 mV), one hard decision fired (fewer than HARD_N = 4); at code 190 none fired. Trip 1.20 µs after the 1.03 × step (trip_d 10.70 µs from the 0.90 × event), `GATE` < 1 V 11.08 µs. |
| G: f_mid and hard_pulse at ss 125 °C and ff −40 °C | f_mid (`f_mid_c`) **passed** at both corners; hard_pulse: ss 125 °C: **passed** (no trip; `tripped` max 54.8 mV, `GATE` min 3.299 V); ff −40 °C: **passed** (no trip; `tripped` max 48.7 mV, `GATE` min 3.297 V). Compact timeline, `--tstop 20` (3.8 µs, about 18 strobes, after the 200 ns pulse); the baseline and first compact attempts are not run to completion | f_mid_c: trip_d 1.1638 µs (ss) / 1.1637 µs (ff), `GATE` < 1 V 1.726 / 1.433 µs; EN re-arm to `GATE` 90 % in 0.958 / 0.515 µs, 1 A restored (r3: 0.958 / 0.514 µs) |
| H: 1.15 × and 1.25 × at ff −40 °C, 2 ns (control) | **passed** as a control | Standard tolerance not run to completion (5.38 µs, before the event, BGR). The reltol 5e-4 re-run gives no trip at 1.15 × and 1.25 × (`tripped` max 5.9 mV), agreeing with phase 1's 1 ns ff −40 °C rows (no trip at 1.10 × and 1.15 ×). On r3 both levels tripped. |

## Run table

Times are from the load event (`--timeline compact`: event at 16 µs; group F: from the 0.90 × step): trip_d / `tripped` / `GATE` < 1 V / < 0.33 V. Cause 1 = soft, 2 = hard, read at the stop time (f_mid_c shows 0 because the EN re-arm has cleared it). "osc tl" = transistor-level R0.95 oscillator. The CPU is the one the run was pinned to. Tag is `cdl_<shown>_functional_r4c`; `…` stands for `_cdle060c0c5_rtleco20260925`.

| Group | Case / point | Corner, supply | Options | Status | Measures | Wall (s) | CPU | Deck | Tag |
|---|---|---|---|---|---|---|---|---|---|
| A | FAST_EN=1, code 200, 0.97x (1.5229 A) | tt 27 °C | 1 ns | passed | no trip; tripped max 7.2 mV, GATE min 3.298 V, cause 0; VREF 1.04501 V, fast_en 1.20 V | 20801 | 67 | `b349ef52` | `c_mid_fast_pex_tt_27C_gear_compact_…_icx_fm1p5229_maxstep1ns` |
| A | FAST_EN=1, code 200, 1.03x (1.6171 A) | tt 27 °C | 1 ns | not run to completion: timestep too small at 16.11 us (xq736), after the event at 16.11 us | – | 10318 | 68 | `d90094fe` | `c_mid_fast_pex_tt_27C_gear_compact_…_icx_fm1p6171_maxstep1ns` |
| A | FAST_EN=1, code 200, 0.97x (1.5256 A) | ss 125 °C | 5 ns | passed | no trip; tripped max 9.8 mV, GATE min 3.299 V, cause 0; VREF 1.04682 V, fast_en 1.20 V | 16388 | 69 | `a45d191f` | `c_mid_fast_pex_ss_125C_gear_compact_…_icx_fm1p5256_maxstep5ns` |
| A | FAST_EN=1, code 200, 1.03x (1.62 A) | ss 125 °C | 5 ns | passed | 0.7399 / 0.4281 / 0.9866 / 1.3200 us, cause 2; VREF 1.04682 V, fast_en 1.20 V | 14493 | 70 | `a9b1eaae` | `c_mid_fast_pex_ss_125C_gear_compact_…_icx_fm1p62_maxstep5ns` |
| A | FAST_EN=1, code 200, 0.97x (1.5186 A) | ff -40 °C | 1 ns | passed | no trip; tripped max 6.1 mV, GATE min 3.297 V, cause 0; VREF 1.04208 V, fast_en 1.20 V | 15220 | 71 | `624e2655` | `c_mid_fast_pex_ff_-40C_gear_compact_…_icx_fm1p5186_maxstep1ns` |
| A | FAST_EN=1, code 200, 1.03x (1.6126 A) | ff -40 °C | 1 ns | passed | 0.5280 / 0.2132 / 0.4810 / 0.6601 us, cause 2; VREF 1.04208 V, fast_en 1.20 V | 13684 | 73 | `f7a83743` | `c_mid_fast_pex_ff_-40C_gear_compact_…_icx_fm1p6126_maxstep1ns` |
| A | FAST_EN=1, code 200, 0.97x (1.5229 A) | tt 27 °C | 1 ns, reltol 5e-4 | passed | no trip; tripped max 7.2 mV, GATE min 3.298 V, cause 0; VREF 1.04501 V, fast_en 1.20 V | 17998 | 74 | `898719bb` | `c_mid_fast_pex_tt_27C_gear_compact_…_icx_fm1p5229_maxstep1ns_optreltol5em4` |
| A | FAST_EN=1, code 200, 1.03x (1.6171 A) | tt 27 °C | 1 ns, reltol 5e-4 | passed | 0.5280 / 0.2144 / 0.5909 / 0.8270 us, cause 2; VREF 1.04501 V, fast_en 1.20 V | 15424 | 75 | `b452f92e` | `c_mid_fast_pex_tt_27C_gear_compact_…_icx_fm1p6171_maxstep1ns_optreltol5em4` |
| A | FAST_EN=1, code 200, 1.03x (1.6171 A) | tt 27 °C | 2 ns, reltol 5e-4, tstop 19 us | not run to completion (stopped: reltol twin completed) | – | 5114 | 68 | `813c47ba` | `c_mid_fast_pex_tt_27C_gear_compact_…_icx_fm1p6171_t19_maxstep2ns_optreltol5em4` |
| B | b_s (SOFT_TIME=1), soft code 153, 0.97x (1.165 A) | tt 27 °C | 1 ns | not run to completion (stopped: projected 33 000 s for the 50 us stop (wall 24 000 s); replaced by b_s0) | – | 4967 | 54 | `e708a459` | `b_s_pex_tt_27C_gear_compact_…_icx_fm1p165_maxstep1ns` |
| B | b_s (SOFT_TIME=1), soft code 153, 1.03x (1.2371 A) | tt 27 °C | 1 ns | not run to completion (stopped: same as the 0.97x row) | – | 4993 | 55 | `2440e24f` | `b_s_pex_tt_27C_gear_compact_…_icx_fm1p2371_maxstep1ns` |
| B | b_s (SOFT_TIME=1), soft code 153, 0.97x (1.1671 A) | ss 125 °C | 5 ns | passed | no trip; tripped max 9.8 mV, GATE min 3.299 V, cause 0; VREF 1.04682 V | 21185 | 56 | `64dcff97` | `b_s_pex_ss_125C_gear_compact_…_icx_fm1p1671_maxstep5ns` |
| B | b_s (SOFT_TIME=1), soft code 153, 1.03x (1.2393 A) | ss 125 °C | 5 ns | passed | 27.7634 / 27.7674 / 28.3259 / 28.6592 us, cause 1; VREF 1.04682 V | 21309 | 57 | `093d8f46` | `b_s_pex_ss_125C_gear_compact_…_icx_fm1p2393_maxstep5ns` |
| B | b_s (SOFT_TIME=1), soft code 153, 0.97x (1.1618 A) | ff -40 °C | 1 ns | not run to completion (stopped: projected 24 000 s for 50 us, at the 23 600 s runner timeout; replaced by b_s0) | – | 5000 | 60 | `dc1691cf` | `b_s_pex_ff_-40C_gear_compact_…_icx_fm1p1618_maxstep1ns` |
| B | b_s (SOFT_TIME=1), soft code 153, 1.03x (1.2336 A) | ff -40 °C | 1 ns | not run to completion (stopped: same as the 0.97x row) | – | 4996 | 64 | `9384934e` | `b_s_pex_ff_-40C_gear_compact_…_icx_fm1p2336_maxstep1ns` |
| B | b_s (SOFT_TIME=1), soft code 153, 0.97x (1.165 A) | tt 27 °C | 1 ns, reltol 5e-4 | not run to completion (stopped: same) | – | 4971 | 65 | `21997dee` | `b_s_pex_tt_27C_gear_compact_…_icx_fm1p165_maxstep1ns_optreltol5em4` |
| B | b_s (SOFT_TIME=1), soft code 153, 1.03x (1.2371 A) | tt 27 °C | 1 ns, reltol 5e-4 | not run to completion (stopped: same) | – | 4998 | 66 | `f779baab` | `b_s_pex_tt_27C_gear_compact_…_icx_fm1p2371_maxstep1ns_optreltol5em4` |
| B | b_s0 (SOFT_TIME=0), soft code 153, 0.97x (1.165 A) | tt 27 °C | 1 ns | passed | no trip; tripped max 7.2 mV, GATE min 3.298 V, cause 0; VREF 1.04501 V | 15902 | 54 | `b060d5f7` | `b_s0_pex_tt_27C_gear_compact_…_icx_fm1p165_maxstep1ns` |
| B | b_s0 (SOFT_TIME=0), soft code 153, 1.03x (1.2371 A) | tt 27 °C | 1 ns | passed | 0.6340 / 0.6368 / 1.0132 / 1.2493 us, cause 1; VREF 1.04501 V | 16356 | 55 | `c30d4c89` | `b_s0_pex_tt_27C_gear_compact_…_icx_fm1p2371_maxstep1ns` |
| B | b_s0 (SOFT_TIME=0), soft code 153, 0.97x (1.165 A) | tt 27 °C | 1 ns, reltol 5e-4 | passed | no trip; tripped max 7.2 mV, GATE min 3.298 V, cause 0; VREF 1.04501 V | 17540 | 65 | `1d91f7bf` | `b_s0_pex_tt_27C_gear_compact_…_icx_fm1p165_maxstep1ns_optreltol5em4` |
| B | b_s0 (SOFT_TIME=0), soft code 153, 1.03x (1.2371 A) | tt 27 °C | 1 ns, reltol 5e-4 | passed | 0.6338 / 0.6366 / 1.0131 / 1.2491 us, cause 1; VREF 1.04501 V | 17799 | 66 | `9b2728c4` | `b_s0_pex_tt_27C_gear_compact_…_icx_fm1p2371_maxstep1ns_optreltol5em4` |
| B | b_s0 (SOFT_TIME=0), soft code 153, 0.97x (1.1618 A) | ff -40 °C | 1 ns | passed | no trip; tripped max 6.0 mV, GATE min 3.297 V, cause 0; VREF 1.04208 V | 10691 | 60 | `143b881c` | `b_s0_pex_ff_-40C_gear_compact_…_icx_fm1p1618_maxstep1ns` |
| B | b_s0 (SOFT_TIME=0), soft code 153, 1.03x (1.2336 A) | ff -40 °C | 1 ns | passed | 0.6339 / 0.6358 / 0.9036 / 1.0828 us, cause 1; VREF 1.04208 V | 14136 | 64 | `97be1061` | `b_s0_pex_ff_-40C_gear_compact_…_icx_fm1p2336_maxstep1ns` |
| B | b_s0 (SOFT_TIME=0), soft code 153, 0.97x (1.1671 A) | ss 125 °C | 5 ns | passed | no trip; tripped max 9.8 mV, GATE min 3.299 V, cause 0; VREF 1.04682 V | 9313 | 58 | `00a11208` | `b_s0_pex_ss_125C_gear_compact_…_icx_fm1p1671_maxstep5ns` |
| B | b_s0 (SOFT_TIME=0), soft code 153, 1.03x (1.2393 A) | ss 125 °C | 5 ns | passed | 0.6339 / 0.6379 / 1.1965 / 1.5298 us, cause 1; VREF 1.04682 V | 8809 | 59 | `720964f7` | `b_s0_pex_ss_125C_gear_compact_…_icx_fm1p2393_maxstep5ns` |
| C | hard code 200, 0.97x (1.5229 A) | tt 27 °C, 1.08 V / 3.0 V | 1 ns | passed | no trip; tripped max 7.3 mV, GATE min 2.999 V, cause 0; VREF 1.04501 V | 13377 | 76 | `733f9066` | `c_mid_pex_tt_27C_gear_compact_…_icx_fm1p5229_vdd1p08_vdda3_maxstep1ns` |
| C | hard code 200, 1.03x (1.6171 A) | tt 27 °C, 1.08 V / 3.0 V | 1 ns | passed | 1.1636 / 1.1675 / 1.5465 / 1.7992 us, cause 2; VREF 1.04501 V | 13659 | 77 | `fcff5834` | `c_mid_pex_tt_27C_gear_compact_…_icx_fm1p6171_vdd1p08_vdda3_maxstep1ns` |
| C | hard code 200, 0.97x (1.5229 A) | tt 27 °C, 1.32 V / 3.6 V | 1 ns | not run to completion: timestep too small at 15.05 us (xq736), before the event | – | 8299 | 78 | `1efc3b4f` | `c_mid_pex_tt_27C_gear_compact_…_icx_fm1p5229_vdd1p32_vdda3p6_maxstep1ns` |
| C | hard code 200, 1.03x (1.6171 A) | tt 27 °C, 1.32 V / 3.6 V | 1 ns | not run to completion: timestep too small at 15.05 us (xq736), before the event | – | 9507 | 79 | `20202168` | `c_mid_pex_tt_27C_gear_compact_…_icx_fm1p6171_vdd1p32_vdda3p6_maxstep1ns` |
| C | hard code 200, 0.97x (1.5229 A) | tt -40 °C | 1 ns | passed | no trip; tripped max 6.4 mV, GATE min 3.298 V, cause 0; VREF 1.04386 V | 13152 | 80 | `ec917b16` | `c_mid_pex_tt_-40C_gear_compact_…_icx_fm1p5229_maxstep1ns` |
| C | hard code 200, 1.03x (1.6171 A) | tt -40 °C | 1 ns | passed | 1.1639 / 1.1662 / 1.4708 / 1.6630 us, cause 2; VREF 1.04386 V | 15670 | 82 | `736e3f8f` | `c_mid_pex_tt_-40C_gear_compact_…_icx_fm1p6171_maxstep1ns` |
| C | hard code 200, 0.97x (1.5229 A) | tt 125 °C | 1 ns | not run to completion: timestep too small at 7.85 us (xq736), before the event | – | 3712 | 84 | `5736a767` | `c_mid_pex_tt_125C_gear_compact_…_icx_fm1p5229_maxstep1ns` |
| C | hard code 200, 1.03x (1.6171 A) | tt 125 °C | 1 ns | not run to completion: timestep too small at 7.85 us (xq736), before the event | – | 3706 | 85 | `09ec1938` | `c_mid_pex_tt_125C_gear_compact_…_icx_fm1p6171_maxstep1ns` |
| C | hard code 200, 0.97x (1.5229 A) | tt 27 °C, 1.08 V / 3.0 V | 1 ns, reltol 5e-4 | not run to completion (stopped: primary completed) | – | 13403 | 86 | `35967064` | `c_mid_pex_tt_27C_gear_compact_…_icx_fm1p5229_vdd1p08_vdda3_maxstep1ns_optreltol5em4` |
| C | hard code 200, 1.03x (1.6171 A) | tt 27 °C, 1.08 V / 3.0 V | 1 ns, reltol 5e-4 | not run to completion (stopped: primary completed) | – | 13692 | 88 | `01012d88` | `c_mid_pex_tt_27C_gear_compact_…_icx_fm1p6171_vdd1p08_vdda3_maxstep1ns_optreltol5em4` |
| C | hard code 200, 0.97x (1.5229 A) | tt 27 °C, 1.32 V / 3.6 V | 1 ns, reltol 5e-4 | passed | no trip; tripped max 7.2 mV, GATE min 3.598 V, cause 0; VREF 1.04501 V | 16032 | 90 | `b55c3d2a` | `c_mid_pex_tt_27C_gear_compact_…_icx_fm1p5229_vdd1p32_vdda3p6_maxstep1ns_optreltol5em4` |
| C | hard code 200, 1.03x (1.6171 A) | tt 27 °C, 1.32 V / 3.6 V | 1 ns, reltol 5e-4 | passed | 1.1638 / 1.1661 / 1.5428 / 1.7675 us, cause 2; VREF 1.04501 V | 15869 | 91 | `d1ca2dce` | `c_mid_pex_tt_27C_gear_compact_…_icx_fm1p6171_vdd1p32_vdda3p6_maxstep1ns_optreltol5em4` |
| C | hard code 200, 0.97x (1.5229 A) | tt -40 °C | 1 ns, reltol 5e-4 | not run to completion (stopped: primary completed) | – | 13196 | 93 | `ae7a098f` | `c_mid_pex_tt_-40C_gear_compact_…_icx_fm1p5229_maxstep1ns_optreltol5em4` |
| C | hard code 200, 1.03x (1.6171 A) | tt -40 °C | 1 ns, reltol 5e-4 | not run to completion (stopped: primary completed) | – | 15681 | 94 | `e4ef80e7` | `c_mid_pex_tt_-40C_gear_compact_…_icx_fm1p6171_maxstep1ns_optreltol5em4` |
| C | hard code 200, 0.97x (1.5229 A) | tt 125 °C | 1 ns, reltol 5e-4 | not run to completion (stopped: projected 24 200 s, over the 23 600 s runner timeout; replaced by the truncated rows) | – | 7752 | 51 | `7d97dc90` | `c_mid_pex_tt_125C_gear_compact_…_icx_fm1p5229_maxstep1ns_optreltol5em4` |
| C | hard code 200, 1.03x (1.6171 A) | tt 125 °C | 1 ns, reltol 5e-4 | not run to completion (stopped: same as the 0.97x row) | – | 7762 | 53 | `9d31f38f` | `c_mid_pex_tt_125C_gear_compact_…_icx_fm1p6171_maxstep1ns_optreltol5em4` |
| C | hard code 200, 0.97x (1.5229 A) | tt 125 °C | 5 ns | not run to completion: timestep too small at 13.99 us (xq736), before the event | – | 6782 | 84 | `fc6baae2` | `c_mid_pex_tt_125C_gear_compact_…_icx_fm1p5229_maxstep5ns` |
| C | hard code 200, 1.03x (1.6171 A) | tt 125 °C | 5 ns | not run to completion: timestep too small at 13.99 us (xq736), before the event | – | 6545 | 85 | `ca8f4ba3` | `c_mid_pex_tt_125C_gear_compact_…_icx_fm1p6171_maxstep5ns` |
| C | hard code 200, 0.97x (1.5229 A) | tt 27 °C, 1.32 V / 3.6 V | 2 ns, reltol 5e-4 | not run to completion (stopped: reltol twin completed) | – | 7735 | 78 | `730fe29e` | `c_mid_pex_tt_27C_gear_compact_…_icx_fm1p5229_vdd1p32_vdda3p6_maxstep2ns_optreltol5em4` |
| C | hard code 200, 1.03x (1.6171 A) | tt 27 °C, 1.32 V / 3.6 V | 2 ns, reltol 5e-4 | not run to completion (stopped: reltol twin completed) | – | 6356 | 79 | `6c4ba871` | `c_mid_pex_tt_27C_gear_compact_…_icx_fm1p6171_vdd1p32_vdda3p6_maxstep2ns_optreltol5em4` |
| C | hard code 200, 1.03x (1.6171 A) | tt 125 °C | 5 ns, reltol 5e-4, tstop 19 us | passed | 1.1638 / 1.1670 / 1.6661 / 1.9777 us, cause 2; VREF 1.04313 V | 9086 | 85 | `f25eb02e` | `c_mid_pex_tt_125C_gear_compact_…_icx_fm1p6171_t19_maxstep5ns_optreltol5em4` |
| C | hard code 200, 0.97x (1.5229 A) | tt 125 °C | 5 ns, reltol 5e-4, tstop 19 us | passed | no trip; tripped max 9.1 mV, GATE min 3.299 V, cause 0; VREF 1.04313 V | 9490 | 63 | `bf6dda28` | `c_mid_pex_tt_125C_gear_compact_…_icx_fm1p5229_t19_maxstep5ns_optreltol5em4` |
| C | hard code 200, 0.97x (1.5229 A) | tt 125 °C | 2 ns, reltol 5e-4, tstop 19 us | passed | no trip; tripped max 9.1 mV, GATE min 3.299 V, cause 0; VREF 1.04313 V | 9014 | 72 | `cda78562` | `c_mid_pex_tt_125C_gear_compact_…_icx_fm1p5229_t19_maxstep2ns_optreltol5em4` |
| C | hard code 200, 1.03x (1.6171 A) | tt 125 °C | 2 ns, reltol 5e-4, tstop 19 us | passed | 1.1637 / 1.1670 / 1.6660 / 1.9776 us, cause 2; VREF 1.04313 V | 9343 | 84 | `789b9a6c` | `c_mid_pex_tt_125C_gear_compact_…_icx_fm1p6171_t19_maxstep2ns_optreltol5em4` |
| D | hard code 254, 0.97x (1.9341 A) | tt 27 °C | 1 ns | passed | no trip; tripped max 7.2 mV, GATE min 3.298 V, cause 0; VREF 1.04501 V | 10449 | 58 | `be934e52` | `c_pex_tt_27C_gear_compact_…_icx_fm1p9341_maxstep1ns` |
| D | hard code 254, 1.03x (2.0537 A) | tt 27 °C | 1 ns | passed | 1.3756 / 1.3784 / 1.7549 / 1.9909 us, cause 2; VREF 1.04501 V | 10354 | 59 | `6c64a15d` | `c_pex_tt_27C_gear_compact_…_icx_fm2p0537_maxstep1ns` |
| D | hard code 254, 0.97x (1.9287 A) | ff -40 °C | 1 ns | passed | no trip; tripped max 6.0 mV, GATE min 3.297 V, cause 0; VREF 1.04208 V | 10691 | 61 | `7a595372` | `c_pex_ff_-40C_gear_compact_…_icx_fm1p9287_maxstep1ns` |
| D | hard code 254, 1.03x (2.048 A) | ff -40 °C | 1 ns | passed | 1.1637 / 1.1656 / 1.4334 / 1.6125 us, cause 2; VREF 1.04208 V | 10618 | 62 | `2c52c6d2` | `c_pex_ff_-40C_gear_compact_…_icx_fm2p048_maxstep1ns` |
| D | hard code 254, 0.97x (1.9341 A) | tt 27 °C | 1 ns, reltol 5e-4 | not run to completion (stopped: primary completed) | – | 10494 | 63 | `0fd5263b` | `c_pex_tt_27C_gear_compact_…_icx_fm1p9341_maxstep1ns_optreltol5em4` |
| D | hard code 254, 1.03x (2.0537 A) | tt 27 °C | 1 ns, reltol 5e-4 | not run to completion (stopped: primary completed) | – | 10477 | 72 | `cc83fc76` | `c_pex_tt_27C_gear_compact_…_icx_fm2p0537_maxstep1ns_optreltol5em4` |
| E | c_mid 1.8x, code 200, transistor-level oscillator | ss 125 °C | 5 ns, osc tl | not run to completion: timestep too small at 5.34 us (xq736), before the event | – | 3227 | 81 | `3615428d` | `c_mid_pex_ss_125C_gear_osctl_compact_…_icx_maxstep5ns` |
| E | c_mid 1.8x, code 200, transistor-level oscillator | ff -40 °C | 1 ns, osc tl | passed | 0.9025 / 0.9044 / 1.1722 / 1.3514 us, cause 2; VREF 1.04208 V; f_osc 12.0498 MHz | 22801 | 83 | `bdecad62` | `c_mid_pex_ff_-40C_gear_osctl_compact_…_icx_maxstep1ns` |
| E | c_mid 1.8x, code 200, transistor-level oscillator | ss 125 °C | 5 ns, reltol 5e-4, osc tl | passed | 1.5712 / 1.5752 / 2.1337 / 2.4671 us, cause 2; VREF 1.04681 V; f_osc 7.4914 MHz | 18435 | 81 | `fc188057` | `c_mid_pex_ss_125C_gear_osctl_compact_…_icx_maxstep5ns_optreltol5em4` |
| E | c_mid 1.8x, code 200, transistor-level oscillator | ff -40 °C | 1 ns, tstop 19 us, osc tl | not run to completion (stopped: projected 22 000 s, over its 18 600 s runner timeout; relaunched as E_ff_t19_L) | – | 4813 | 51 | `7aac7507` | `c_mid_pex_ff_-40C_gear_osctl_compact_…_icx_t19_maxstep1ns` |
| E | c_mid 1.8x, code 200, transistor-level oscillator | ff -40 °C | 2 ns, tstop 19 us, osc tl | not run to completion: timestep too small at 1.18 us (xq736), before the event | – | 1482 | 53 | `dcce8d3c` | `c_mid_pex_ff_-40C_gear_osctl_compact_…_icx_t19_maxstep2ns` |
| E | c_mid 1.8x, code 200, transistor-level oscillator | ff -40 °C | 1 ns, reltol 5e-4, tstop 19 us, osc tl | not run to completion (stopped: projected 24 000 s, over its 18 600 s runner timeout; relaunched as E_ff_t19_rt_L) | – | 3270 | 53 | `0af6871d` | `c_mid_pex_ff_-40C_gear_osctl_compact_…_icx_t19_maxstep1ns_optreltol5em4` |
| E | c_mid 1.8x, code 200, transistor-level oscillator | ss 125 °C | 5 ns, reltol 5e-4, tstop 19 us, osc tl | not run to completion (stopped: the full-length reltol row E_ss_rt completed) | – | 9082 | 51 | `901a966c` | `c_mid_pex_ss_125C_gear_osctl_compact_…_icx_t19_maxstep5ns_optreltol5em4` |
| E | c_mid 1.8x, code 200, transistor-level oscillator | ff -40 °C | 1 ns, tstop 19.5 us, osc tl | not run to completion (stopped: the full-length primary E_ff completed) | – | 10206 | 53 | `72b33e26` | `c_mid_pex_ff_-40C_gear_osctl_compact_…_icx_t19.5_maxstep1ns` |
| E | c_mid 1.8x, code 200, transistor-level oscillator | ff -40 °C | 1 ns, reltol 5e-4, tstop 19.5 us, osc tl | not run to completion (stopped: the full-length primary E_ff completed) | – | 10205 | 61 | `994a7a58` | `c_mid_pex_ff_-40C_gear_osctl_compact_…_icx_t19.5_maxstep1ns_optreltol5em4` |
| F | DAC_HARD 200->180->200 at 0.90x, then 1.03x | tt 27 °C | 1 ns | passed | 10.7015 / 10.7043 / 11.0808 / 11.3168 us, cause 2; VREF 1.04501 V | 14810 | 87 | `6a5c7b81` | `dac_rw180_pex_tt_27C_gear_compact_…_icx_maxstep1ns` |
| F | DAC_HARD 200->190->200 at 0.90x, then 1.03x | tt 27 °C | 1 ns | passed | 10.7016 / 10.7044 / 11.0809 / 11.3169 us, cause 2; VREF 1.04501 V | 14436 | 89 | `57de38ed` | `dac_rw190_pex_tt_27C_gear_compact_…_icx_maxstep1ns` |
| G | hard_pulse 45 mV 200 ns, no trip expected (baseline) | ss 125 °C | 5 ns | not run to completion: timestep too small at 9.86 us (xq736), before the event | – | 5145 | 48 | `9ad3f0c4` | `hard_pulse_pex_ss_125C_gear_…_icx_maxstep5ns` |
| G | hard_pulse 45 mV 200 ns, no trip expected (baseline) | ff -40 °C | 1 ns | not run to completion (stopped: baseline timeline projected 26 600 s (wall 24 000 s); replaced by the compact row) | – | 5960 | 49 | `58b3a3ca` | `hard_pulse_pex_ff_-40C_gear_…_icx_maxstep1ns` |
| G | f_mid (baseline): 1.8x trip, then EN re-arm | ss 125 °C | 5 ns | not run to completion: timestep too small at 9.86 us (xq736), before the event | – | 5122 | 50 | `0b7500a6` | `f_mid_pex_ss_125C_gear_…_icx_maxstep5ns` |
| G | f_mid (baseline): 1.8x trip, then EN re-arm | ff -40 °C | 1 ns | not run to completion (stopped: baseline timeline projected 28 700 s; replaced by f_mid_c) | – | 5930 | 52 | `c5bb2b46` | `f_mid_pex_ff_-40C_gear_…_icx_maxstep1ns` |
| G | hard_pulse 45 mV 200 ns, no trip expected (compact) | ss 125 °C | 5 ns, reltol 5e-4 | not run to completion (stopped: projected 22 400 s, over its 18 600 s runner timeout; relaunched with --tstop 20) | – | 6612 | 48 | `a243b5ef` | `hard_pulse_pex_ss_125C_gear_compact_…_icx_maxstep5ns_optreltol5em4` |
| G | hard_pulse 45 mV 200 ns, no trip expected (compact) | ff -40 °C | 1 ns | not run to completion (stopped: projected 21 800 s, over its 18 600 s runner timeout; relaunched with --tstop 20) | – | 6612 | 49 | `048a4e4e` | `hard_pulse_pex_ff_-40C_gear_compact_…_icx_maxstep1ns` |
| G | f_mid_c: 1.8x trip, load back +4 us, EN low +6..+8 us | ss 125 °C | 5 ns, reltol 5e-4 | not run to completion (stopped: projected 20 700 s, over its 18 600 s runner timeout; relaunched (wall 30 000 s)) | – | 6612 | 50 | `19f90e28` | `f_mid_c_pex_ss_125C_gear_compact_…_icx_maxstep5ns_optreltol5em4` |
| G | f_mid_c: 1.8x trip, load back +4 us, EN low +6..+8 us | ff -40 °C | 1 ns | passed | 1.1637 / 1.1656 / 1.4334 / 1.6125 us, cause 0; re-arm: GATE 90 % 0.514 us after EN, GATE end 3.300 V, load 1.000 A; VREF 1.04208 V | 15821 | 52 | `85428e42` | `f_mid_c_pex_ff_-40C_gear_compact_…_icx_maxstep1ns` |
| G | hard_pulse 45 mV 200 ns, no trip expected (compact) | ss 125 °C | 5 ns, reltol 5e-4, tstop 20 us | passed | no trip; tripped max 54.8 mV, GATE min 3.299 V, cause 0; VREF 1.04681 V | 13019 | 48 | `d130a7c4` | `hard_pulse_pex_ss_125C_gear_compact_…_icx_t20_maxstep5ns_optreltol5em4` |
| G | hard_pulse 45 mV 200 ns, no trip expected (compact) | ff -40 °C | 1 ns, tstop 20 us | passed | no trip; tripped max 48.7 mV, GATE min 3.297 V, cause 0; VREF 1.04208 V | 12983 | 49 | `be6e23af` | `hard_pulse_pex_ff_-40C_gear_compact_…_icx_t20_maxstep1ns` |
| G | f_mid_c: 1.8x trip, load back +4 us, EN low +6..+8 us | ss 125 °C | 5 ns, reltol 5e-4, tstop 27 us | not run to completion (stopped: the standard-tolerance row Gc_fm_ss_std completed) | – | 9883 | 50 | `b4c83cde` | `f_mid_c_pex_ss_125C_gear_compact_…_icx_t27_maxstep5ns_optreltol5em4` |
| G | f_mid_c: 1.8x trip, load back +4 us, EN low +6..+8 us | ss 125 °C | 5 ns | passed | 1.1638 / 1.1677 / 1.7263 / 2.0596 us, cause 0; re-arm: GATE 90 % 0.958 us after EN, GATE end 3.299 V, load 1.000 A; VREF 1.04682 V | 9836 | 62 | `91250c28` | `f_mid_c_pex_ss_125C_gear_compact_…_icx_maxstep5ns` |
| H | hard code 200, 1.15 A (control, 2 ns) | ff -40 °C | 2 ns | not run to completion: timestep too small at 5.38 us (xq760), before the event | – | 1993 | 92 | `92df6d74` | `c_mid_pex_ff_-40C_gear_compact_…_icx_fm1p15_maxstep2ns` |
| H | hard code 200, 1.25 A (control, 2 ns) | ff -40 °C | 2 ns | not run to completion: timestep too small at 5.38 us (xq760), before the event | – | 2039 | 95 | `ca178b96` | `c_mid_pex_ff_-40C_gear_compact_…_icx_fm1p25_maxstep2ns` |
| H | hard code 200, 1.15 A (control, 2 ns) | ff -40 °C | 2 ns, reltol 5e-4 | passed | no trip; tripped max 5.9 mV, GATE min 3.297 V, cause 0; VREF 1.04208 V | 14793 | 92 | `0494f45d` | `c_mid_pex_ff_-40C_gear_compact_…_icx_fm1p15_maxstep2ns_optreltol5em4` |
| H | hard code 200, 1.25 A (control, 2 ns) | ff -40 °C | 2 ns, reltol 5e-4 | passed | no trip; tripped max 5.9 mV, GATE min 3.297 V, cause 0; VREF 1.04208 V | 14442 | 95 | `1bf6c74d` | `c_mid_pex_ff_-40C_gear_compact_…_icx_fm1p25_maxstep2ns_optreltol5em4` |

## r3 reference numbers

| Group | r3 (r3full/r3x records) | r4c |
|---|---|---|
| A (FAST_EN = 1) | not run on r3 (r3x "not run" list); map 1.2 evaluation `eco_c_mid_r3`: fast path trips 0.21 µs after a 1.8 × fault | 1.03 ×: `tripped` 0.213 µs (ff −40 °C), 0.214 µs (tt), 0.428 µs (ss 125 °C); 0.97 ×: no trip at all three |
| B (soft) | cal rehearsal tt: soft crossing 128/130 against ideal 127.1 (1–3 codes early); b_s 1.5 × soft trip 27.752 µs | window rows ss 125 °C: 0.97 × no trip, 1.03 × soft trip 27.763 µs; single-sample rows (SOFT_TIME = 0): 0.97 × silent, 1.03 × trips 0.634 µs at tt, ss 125 °C, ff −40 °C |
| C (supply, temperature) | tt code 200 effective threshold 30.0–31.25 mV (trips at 0.80 T); 1.8 × at 1.08/3.0 V: 1.1637 / 1.1676 / 1.5466 / 1.7993 µs; at 1.32/3.6 V: 1.1639 / 1.1661 / 1.5429 / 1.7675 µs | brackets hold at 1.08/3.0 V, 1.32/3.6 V, tt −40 °C and tt 125 °C; 1.03 × decisions 1.1636–1.1639 µs |
| D (code 254) | cal: no crossing from 254 down to 206 at 1 A (as expected); the 254 bracket was not run | tt: 0.97 × no trip, 1.03 × 1.3756 µs; ff −40 °C: 0.97 × no trip, 1.03 × 1.1637 µs |
| E (osc tl) | tt: f_osc 9.4415 MHz, 1.1211 / 1.1239 / 1.5004 / 1.7364 µs; ss/ff not run | ss 125 °C: 7.491 MHz, 1.5712 / 1.5752 / 2.1337 / 2.4671 µs; ff −40 °C: 12.050 MHz, 0.9025 / 0.9044 / 1.1722 / 1.3514 µs |
| G | hard_pulse ss 125 °C latch max 54 mV, ff −40 °C 49 mV; f_mid ss 1.1526 / 1.1565 / 1.7151 / 2.0484 µs, re-arm 0.958 µs; ff 1.1526 / 1.1545 / 1.4223 / 1.6014 µs, re-arm 0.514 µs | hard_pulse (compact, `--tstop 20`): latch max 54.8 mV (ss), 48.7 mV (ff), no trip; f_mid_c: 1.1638 / 1.1677 / 1.7263 / 2.0596 µs, re-arm 0.958 µs (ss); 1.1637 / 1.1656 / 1.4334 / 1.6125 µs, re-arm 0.514 µs (ff) |
| H | ff −40 °C 1 ns: 1.15 × trips (1.1639 µs), 1.25 × trips | 2 ns: no trip at 1.15 × and 1.25 × (phase 1, 1 ns: no trip at 1.10 × and 1.15 ×) |

## Findings

1. **The effective hard threshold sits within ±3 % of the DAC code in every condition tried.**
   - Coverage: codes 200 and 254; tt, ss 125 °C and ff −40 °C; tt at −40, 27 and 125 °C; supplies 1.08/3.0 V and 1.32/3.6 V; digital path and the FAST_EN analog path.
   - This is the r4 fix. On r3 the same deck tripped 8–11.6 mV below code 200, and the offset moved about 2.3 mV with temperature (r3x record).
   - At 0.97 × the `tripped` latch never exceeds 9.8 mV. At 1.03 × the digital decision lands on the same strobe as a 1.8 × fault (1.1636–1.1639 µs), except at code 254 at tt, where it lands one strobe later (1.3756 µs).
2. **The soft threshold also sits within ±3 % of its code** (code 153, 30.03 mV at tt), at all three corners. The single-sample rows (SOFT_TIME = 0) are the stricter test: one sample above the threshold trips. The 256-sample window behaves as on r3 (ss 125 °C: 27.763 µs against r3's 27.752 µs at 1.5 ×).
3. **With FAST_EN = 1 a single hard strobe sets the latch.** No 0.97 × fault fired it at any corner, VREF coupling of the extracted interconnect included. At 1.03 × the latch is set 0.21–0.43 µs after the fault.
4. **A DAC_HARD rewrite while armed does not trip on the rewrite.**
   - Code 200 → 180 → 200 under a 0.90 × fault: the fault equals the code-180 nominal (35.33 mV). While code 180 was set, `cmp_hard` decided high exactly once (20.88–21.10 µs, one strobe period, from the decimated waveform), which is fewer than HARD_N = 4 decisions, so there was no trip.
   - Code 190 (5 % above the fault): no hard decision at all.
   - A fault sitting exactly at the code therefore decides about once in 16 strobes. The effective threshold is at the code, as the block bench found ("hard −1": 0 to 1 LSB above the code).
   - With FAST_EN = 1, that single decision would have set the latch. That is the intended FAST_EN behaviour at the threshold (register map: the fast path acts on a single strobe).
5. **The transistor-level oscillator at ss 125 °C runs at 7.491 MHz**, below the 7.6–12.4 MHz range quoted for the oscillator over corners (here the loaded R0.95 CPEX in the chip deck, T2F on, trim 8). The trip path still works: trip_d 1.571 µs, `GATE` < 1 V 2.134 µs, far inside 10 µs. At ff −40 °C it runs at 12.050 MHz, and the non-overlap generator sees these real edges.
6. **Numerics.** On this deck, 13 runs stopped with "timestep too small" in a BGR VBIC HBT (`xq736` in 11, `xq760` in 2), all at standard tolerances:
   - at 1 ns: tt 125 °C (7.85 µs), 1.32/3.6 V (15.05 µs), and A tt 1.03 × (16.11 µs, 0.11 µs after the event, before the first strobe);
   - at 2 ns: ff −40 °C, H rows (5.38 µs) and osc tl (1.18 µs);
   - at 5 ns: ss 125 °C osc tl (5.34 µs), ss 125 °C baseline hard_pulse/f_mid (9.86 µs), tt 125 °C (13.99 µs).

   Identical decks at the same step fail at the identical time, so this is deterministic, not random. The same condition completed every time with reltol 5e-4, or at another step where one was tried. The BGR view is the r3 one (`01227a3d`). Where a twin or hedge completed alongside its sibling, the trip times agree within 0.2 ns and the no-trip rows agree.

## Runner changes (this phase)

These are additions only. Existing cases, the deck builder, the measurement lines and the solver lines are unchanged.
- **`run_top.py` cases:**
  - `c_mid_fast`: c_mid with a third frame, MODE = 0x23 (FAST_EN = 1), supply window event − 1 µs.
  - `dac_rw180` / `dac_rw190`: 0.90 × of code 200 held from the event; late frames at event + 1 µs set DAC_HARD = 180 or 190, then 200; step to 1.03 × at event + 9.5 µs.
  - `b_s0`: b_s with SOFT_TIME_L = 0x00 written in place of 0x01. The first soft sample above the threshold trips (register map: "0x0000 trips on the first sample above threshold").
  - `f_mid_c`: f_mid with event-relative times, load back at + 4 µs and EN low from + 6 to + 8 µs.
- **`run_top_cdl.py`:** the compact timeline accepts these cases, `b_s` (tstop 50 µs) and `hard_pulse` (tstop 30 µs, i.e. event + 14 µs as on the baseline).

Runner hashes (`runner_sha256` / `run_top_sha256`) recorded by the runs:
- `10d72fa0` / `69df9ce1`: the first wave, 22:20 CEST.
- `02711744` / `fb20d854`: after `b_s0` was added, 23:44 CEST.
- `9f6c42de` / `477eb0e9`: after `f_mid_c` and compact `hard_pulse` were added, from 00:00 CEST.

## Launch history

All runs are pinned one per CPU, and every row of the run table is a separate run.

| Time (CEST) | Runs | Wall / `--timeout` (s) | Why |
|---|---|---|---|
| 27 Sep 22:20 | the 48 of groups A–H, including a reltol 5e-4 twin of each tt 1 ns row of A, B, C and D (the r4a tt 1 ns runs aborted in the BGR at random times) | 24 000 / 23 600 | primary set |
| 22:55 | H 1.15 × and 1.25 × with reltol 5e-4 | 22 000 / 21 600 | the one re-run after the H abort at 5.38 µs |
| 23:15 | E ss 125 °C with reltol 5e-4 | 21 000 / 20 600 | the one re-run after the abort at 5.34 µs |
| 23:23 | tt 125 °C brackets at 5 ns | 21 000 / 20 600 | hedge after both 1 ns rows aborted at 7.85 µs |
| 23:44, 23:49 | `b_s0` brackets tt (with twins) and ff −40 °C | 21 000 / 20 600 | the tt and ff `b_s` rows (50 µs) were projected past the wall and were stopped |
| 28 Sep 00:00 | compact `hard_pulse` and `f_mid_c` at ss 125 °C (reltol 5e-4) and ff −40 °C | 19 000 / 18 600 | baseline G rows: ss aborted at 9.86 µs, ff projected past the wall |
| 00:31–01:17 | E ff −40 °C `--tstop 19` at 1 ns and 2 ns; 2 ns reltol hedges for the 1.32/3.6 V rows; `b_s0` ss 125 °C; tt 125 °C with reltol 5e-4 and `--tstop 19` at 5 ns and 2 ns; a 2 ns hedge of A tt 1.03 × | 19 000 / 18 600 | hedges for runs projected past their timeout or aborted |
| 01:51 | hard_pulse ss/ff `--tstop 20`, f_mid_c ss (two), E ss/ff `--tstop 19`/`19.5` | 30 000 / 29 600 | the 00:00 and 00:31 relaunches were projected past their 18 600 s timeout |

A run that I stopped is recorded as "not run to completion (stopped: reason)", with the reason in its row. None was stopped after its trip measure. A stopped twin or hedge was stopped because its sibling had already completed.

## Retention and figures

- **Retention.** Logs and `.progress.jsonl` files over 300 kB were copied to `${BULK}/g1-freeze-retention-20260925/g1_top_logs_r4c/` and removed from the tree. They are listed in `review/local-retention-20260925.json` under `addition_20260928_r4c`. The `.json` and a `.tail.txt` extract (header, measure lines, last 40 lines) stay in `sim/logs/`.
- **Figures.** Waveform figures are in [`figures/fullchip_r4c/`](figures/fullchip_r4c/README.md), drawn from the completed runs before retention.

## Commands (repository root, `BULK` set; `W=designs/g1-guardian/blocks/g1_top/sim`)

```
C="--cdl /work/designs/g1-guardian/blocks/g1_padring/netlist/g1_chip_top_1414_r4.cdl \
   --cdl-sha256 e060c0c59a168e5b69b0c47dc31cbfe4f4444d2ec8af62960c339c1230a2c99f --blockset c1414r4 \
   --rtl-dir eco_20260925 --netlist pex --pads nodcn --method gear --interconnect extracted --run-id r4c"
# first wave: --timeout 23600, wall 24000; the relaunches: see "Launch history"
flow/launch_pinned.sh <cpu> $W 24000 <log> python3 run_top_cdl.py c_mid_fast --timeline compact --fault-mult 1.6171 --maxstep-ns 1 --timeout 23600 $C
flow/launch_pinned.sh <cpu> $W 24000 <log> python3 run_top_cdl.py c_mid_fast --timeline compact --fault-mult 1.62 --corner ss --temp 125 --maxstep-ns 5 --timeout 23600 $C
flow/launch_pinned.sh <cpu> $W 21000 <log> python3 run_top_cdl.py b_s0 --timeline compact --fault-mult 1.2336 --corner ff --temp -40 --maxstep-ns 1 --timeout 20600 $C
flow/launch_pinned.sh <cpu> $W 24000 <log> python3 run_top_cdl.py c_mid --timeline compact --fault-mult 1.5229 --vdd 1.32 --vdda 3.6 --maxstep-ns 1 --extra-options reltol=5e-4 --timeout 23600 $C
flow/launch_pinned.sh <cpu> $W 19000 <log> python3 run_top_cdl.py c_mid --timeline compact --fault-mult 1.6171 --temp 125 --maxstep-ns 2 --tstop 19 --extra-options reltol=5e-4 --timeout 18600 $C
flow/launch_pinned.sh <cpu> $W 24000 <log> python3 run_top_cdl.py c --timeline compact --fault-mult 2.0537 --maxstep-ns 1 --timeout 23600 $C
flow/launch_pinned.sh <cpu> $W 24000 <log> python3 run_top_cdl.py c_mid --timeline compact --osc tl --corner ff --temp -40 --maxstep-ns 1 --timeout 23600 $C
flow/launch_pinned.sh <cpu> $W 24000 <log> python3 run_top_cdl.py dac_rw180 --timeline compact --maxstep-ns 1 --timeout 23600 $C
flow/launch_pinned.sh <cpu> $W 30000 <log> python3 run_top_cdl.py hard_pulse --timeline compact --corner ff --temp -40 --maxstep-ns 1 --tstop 20 --timeout 29600 $C
flow/launch_pinned.sh <cpu> $W 19000 <log> python3 run_top_cdl.py f_mid_c --timeline compact --corner ff --temp -40 --maxstep-ns 1 --timeout 18600 $C
flow/launch_pinned.sh <cpu> $W 24000 <log> python3 run_top_cdl.py c_mid --timeline compact --fault-mult 1.25 --corner ff --temp -40 --maxstep-ns 2 --timeout 23600 $C
```
Every row of the run table is one such command. Its options are the row's `options` in its run JSON (`sim/logs/<tag>.json`).

# G1 r4 candidate full-chip layout-netlist campaign (runs `r4a`, `r4b`, 2026-09-27/28)

Every number here is **simulated**. The runs used:
- ngspice-46 with the Icarus d_cosim;
- IHP SG13G2 open PDK `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`;
- image `tapeoutbench-eda:latest` (`sha256:ddeb6957…`).

**Status of this record: final (2026-09-28 08:20 CEST).** Every requested case has a completed run. The failed and timed-out attempts are listed with their reasons.

## What r4 is, and what the deck is

r4 is the r3 chip of record with two changes:
- the TRIP macro is replaced by the `nf4_novclk` candidate, which has a non-overlapping comparator clock ([`../../g1_trip/layout/candidates/nf4_novclk/`](../../g1_trip/layout/candidates/nf4_novclk/));
- 406 µm² of GatPoly fill is added.

The deck is the r3x deck of [`FULLCHIP_CDL_R3_CORNERS_20260927.md`](FULLCHIP_CDL_R3_CORNERS_20260927.md), with two substitutions: the chip CDL and the TRIP extraction.

| Item | Value |
|---|---|
| Chip GDS | `blocks/g1_padring/layout/g1_chip_top_1414_r4.gds`, SHA-256 `225d0b535321ed312594bb13d97b7271014f487162564a56c874572de715173a` |
| Chip netlist | `blocks/g1_padring/netlist/g1_chip_top_1414_r4.cdl`, SHA-256 `e060c0c59a168e5b69b0c47dc31cbfe4f4444d2ec8af62960c339c1230a2c99f` (`--cdl`/`--cdl-sha256`). It is translated by `run_top_cdl.py` exactly as for r3: 40 subckts, 8 `dantenna` removed (`--pads nodcn`), 4833 filler instances merged. |
| TRIP extraction | `blocks/g1_trip/sim/postlayout/g1_trip_nf4_novclk_pex.spice`, SHA-256 `6f518e0758a87b334ab5ae98a8ad43d79dd03ab4ba52c241f742280b6d2f770b`. This is the kpex 2.5D CC extraction of the candidate macro; the bulk copy of the kpex run output under `${BULK}/r4-20260927/pex/` has the same hash. It is bound in `run_top.py` `BLOCKSET_SHA256` and selected by the new blockset `c1414r4` (`--blockset c1414r4`). |
| Other block views | as r3: BGR586 kpex `01227a3d`, SENSE R100 partial-C `ffb14762`, GATE Sep-19 PEX `e91617f5`, T2F PEX `441edabc`, OSC R0.95 CPEX `8efd7a09` (`--osc tl` only) |
| Digital | frozen ECO RTL, `--rtl-dir eco_20260925` (map 1.2); `--por-pin` for the power-up cases |
| Interconnect | `--interconnect extracted` (`ddc88cc7`, C only, r1 geometry as in r3) |
| Solver | gear, 1 ns maximum step unless a row says otherwise (power-up: case step 20 ns at ss, 2 ns at ff); `reltol 1e-3` unless `reltol 5e-4` is shown |
| Clock | ideal 9.436194721 MHz unless `--osc tl` |
| T2F | on from reset |

**Deck check.** A dry build of `c_mid` compact at tt with the r3 CDL and the r4 CDL gives decks that differ in exactly four places: the CDL path/hash header, the `g1_trip` include and its hash, the compiled-RTL file name, and the output file names (`diff`, 2026-09-27). The translated chip is otherwise line-identical. The fill adds no devices.

**Runner.**
- `run_top.py` gains the blockset `c1414r4`, which is `c1414` with only the trip `pex` entry changed.
- `run_top_cdl.py` gains `--blockset {c1414,c1414r4}` (default `c1414`, so r3 behaviour is unchanged). It also records the blockset in each JSON (`options.blockset`).
- 50 of the runs record `runner_sha256` `82a34a11…` and `run_top_sha256` `e2a43d7a…`, which are the versions committed in `9b4e1b6ea`.
- The five late `r4b` runs record working-tree versions: `10d72fa0…`/`69df9ce1…` (b_s, f_mid) and `9f6c42de…`/`477eb0e9…` (hard_pulse, the two cal windows). A parallel session was adding new cases (`c_mid_fast`, `dac_rw*`, `b_s0`, `f_mid_c`) and compact-timeline stops for new case names. The cases and timelines used here are unchanged by those edits.
- The deck of each run is in `sim/decks/`, and its `deck_sha256` is in the run JSON.

**Process.**
- Every run was launched with `flow/launch_pinned.sh`, one CPU each, at nice 0.
- CPUs: 0–15 and 32–47. The `r4b` reruns ran on CPUs 1–6.
- Wall bound 25 200 s with `--timeout 24800`, as in r3x. The four long-bound reruns (`b_s`, `f_mid`, `hard_pulse` and cal `r4b`) used 36 400 s / `--timeout 36000`.
- The machine load average was 240–250 on 128 CPUs overnight. Per-run speed fell to about 1.4–1.7 µs of simulated time per 1000 s, against about 2.4 in r3x. Every timeout below comes from this.
- For about 45 minutes, CPUs 45–47 were shared with another session's short nice-5 block runs.

## Status

The event is at 16 µs (compact) or 30 µs (baseline). Times are measured from the event, in the order `trip_d` / `tripped` / `GATE` < 1 V / < 0.33 V, in µs. The r3 numbers come from `FULLCHIP_CDL_R3_20260926.md` (r3full) and `FULLCHIP_CDL_R3_CORNERS_20260927.md` (r3x). Cause 2 = hard, 1 = soft.

### a. c_mid compact (1.8×, 45 mV at code 200)

| Corner | r3 | r4 | Status | Log (`cdl_…`) |
|---|---|---|---|---|
| tt 27 °C | 1.1639 / 1.1666 / 1.5432 / 1.7792 | 1.1639 / 1.1666 / **1.5432** / 1.7792 (`--tstop 19`, r4b); reltol 5e-4 to 28 µs: 1.1637 / 1.1665 / 1.5430 / 1.7790 | passed | `c_mid_pex_tt_27C_gear_compact_…_icx_t19_maxstep1ns_functional_r4b`; `c_mid_pex_tt_27C_gear_compact_…_icx_maxstep1ns_optreltol5em4_functional_r4a` |
| tt, first attempt (1 ns, 28 µs) | — | the trip measures (same numbers as above) were emitted, then the solver stopped at 27.77 µs of 28 µs (BGR `xq736` timestep too small) | not run to completion after the trip event at 1.16 µs (numbers usable) | `c_mid_pex_tt_27C_gear_compact_…_icx_maxstep1ns_functional_r4a` |
| ss 125 °C | 1.1638 / 1.1678 / 1.7264 / 2.0597 | 1.1638 / 1.1677 / **1.7263** / 2.0597 (5 ns); 1 ns reltol 5e-4: 1.1638 / 1.1678 / 1.7263 / 2.0597 | passed | `c_mid_pex_ss_125C_…_icx_maxstep5ns_functional_r4a`; `c_mid_pex_ss_125C_gear_compact_…_icx_maxstep1ns_optreltol5em4_functional_r4a` |
| ss, 1 ns and 2 ns | — | failed (numerical) at 6.789 µs (BGR `xq760`) and at 10.50 µs (BGR `xq736`), before the fault | failed (numerical), superseded by the 5 ns and reltol rows | `c_mid_pex_ss_125C_gear_compact_…_icx_maxstep1ns_functional_r4a`, `c_mid_pex_ss_125C_gear_compact_…_icx_maxstep2ns_functional_r4a` |
| ff −40 °C | 1.1637 / 1.1656 / 1.4334 / 1.6126 | 1.1637 / 1.1656 / **1.4334** / 1.6126 | passed | `c_mid_pex_ff_-40C_…_icx_maxstep1ns_functional_r4a` |

QUIET, 2 µs before the fault: VREF 1.04501 / 1.04682 / 1.04208 V (tt / ss / ff). vth_hard is 0.8972 / 0.8989 / 0.8946 V. VDDA is 1462.8 µA at tt and 1727.8 µA at ss/125 °C. All of these equal r3 within 0.2 mV and 0.1 µA.

### b. Near-threshold hard brackets at code 200 (`--fault-mult`)

The code-200 nominal is VREF·455/530 referred to the shunt: 39.25 mV at tt, 39.32 mV at ss 125 °C and 39.14 mV at ff −40 °C, as in the r3x record. The r4 VREF values are unchanged. The fault-mult for 0.97T and 1.03T is (0.97 or 1.03) × nominal / 25 mV.

| Corner | Point | r3 | r4 | Status | Log (`cdl_…`) |
|---|---|---|---|---|---|
| tt | 30.0 mV (1.20×) | no trip | no trip (tripped max 7.2 mV, GATE min 3.298 V) | passed | `c_mid_pex_tt_27C_gear_compact_…_icx_fm1p2_maxstep1ns_functional_r4a` |
| tt | 31.25 mV (1.25×) | **trips** 1.1638 µs | **no trip**: reltol 5e-4 to 28 µs; `--tstop 19` (r4b); first attempt no trip through 19.08 µs, then numerical stop | passed | `c_mid_pex_tt_27C_gear_compact_…_fm1p25_maxstep1ns_optreltol5em4_functional_r4a`, `c_mid_pex_tt_27C_gear_compact_…_fm1p25_t19_maxstep1ns_functional_r4b` |
| tt | 38.07 mV (0.97T, 1.5229×) | not run | no trip (tripped max 7.2 mV) | passed | `c_mid_pex_tt_27C_gear_compact_…_fm1p5229_maxstep1ns_functional_r4a` |
| tt | 40.43 mV (1.03T, 1.6171×) | not run | **trips** 1.1637 / 1.1664 / 1.5430 / 1.7790, cause 2 | passed | `c_mid_pex_tt_27C_gear_compact_…_fm1p6171_maxstep1ns_functional_r4a` |
| ss 125 °C | 30.0 mV (1.20×) | no trip | no trip (tripped max 9.8 mV), 5 ns | passed | `c_mid_pex_ss_125C_gear_compact_…_fm1p2_maxstep5ns_functional_r4a` |
| ss | 31.25 mV (1.25×) | **trips** late, 1.7995 µs | **no trip**: 5 ns and 1 ns reltol 5e-4 | passed | `c_mid_pex_ss_125C_gear_compact_…_fm1p25_maxstep5ns_functional_r4a`, `c_mid_pex_ss_125C_gear_compact_…_fm1p25_maxstep1ns_optreltol5em4_functional_r4a` |
| ss | 38.14 mV (0.97T, 1.5256×) | not run | no trip: 5 ns and 1 ns reltol 5e-4 | passed | `c_mid_pex_ss_125C_gear_compact_…_fm1p5256_maxstep5ns_functional_r4a`, `c_mid_pex_ss_125C_gear_compact_…_fm1p5256_maxstep1ns_optreltol5em4_functional_r4a` |
| ss | 40.50 mV (1.03T, 1.62×) | not run | **trips late**: 1.3757 / 1.3797 / 1.9382 / 2.2716 (5 ns); 1 ns reltol 5e-4 1.3757 / 1.3797 / 1.9383 / 2.2716, cause 2 | passed | `c_mid_pex_ss_125C_gear_compact_…_fm1p62_maxstep5ns_functional_r4a`, `c_mid_pex_ss_125C_gear_compact_…_fm1p62_maxstep1ns_optreltol5em4_functional_r4a` |
| ff −40 °C | 27.5 mV (1.10×) | no trip | no trip (tripped max 6.0 mV) | passed | `c_mid_pex_ff_-40C_gear_compact_…_fm1p1_maxstep1ns_functional_r4a` |
| ff | 28.75 mV (1.15×) | **trips** 1.1639 µs | **no trip** | passed | `c_mid_pex_ff_-40C_gear_compact_…_fm1p15_maxstep1ns_functional_r4a` |
| ff | 37.97 mV (0.97T, 1.5186×) | not run | no trip | passed | `c_mid_pex_ff_-40C_gear_compact_…_fm1p5186_maxstep1ns_functional_r4a` |
| ff | 40.31 mV (1.03T, 1.6126×) | not run | **trips** 1.1637 / 1.1656 / 1.4334 / 1.6126, cause 2 | passed | `c_mid_pex_ff_-40C_gear_compact_…_fm1p6126_maxstep1ns_functional_r4a` |

The ss 1 ns and 2 ns attempts of 1.20×, 1.25×, 0.97T and 1.03T all **failed (numerical)**, at 6.789 µs and 10.50 µs respectively, before the fault. They are superseded by the 5 ns rows and the 1 ns reltol 5e-4 rows. There is no 2 ns attempt for 1.20×.

**Effective hard threshold at code 200:**

| Corner | r3: no trip / trips | r3 offset below the code | r4: no trip / trips | r4 offset |
|---|---|---|---|---|
| tt 27 °C | 30.0 / 31.25 mV | 8.0–9.25 mV = 40–47 LSB | 38.07 / 40.43 mV | within ±1.18 mV = **±6 LSB** of the code |
| ss 125 °C | 30.0 / 31.25 mV | 8.1–9.3 mV = 41–47 LSB | 38.14 / 40.50 mV | within ±1.18 mV = ±6 LSB |
| ff −40 °C | 27.5 / 28.75 mV | 10.4–11.6 mV = 53–59 LSB | 37.97 / 40.31 mV | within ±1.17 mV = ±6 LSB |

(LSB = 0.198 mV shunt-referred.)
- The ±3 % brackets resolve the threshold to ±6 LSB only. The 2-LSB claim of the block bench (hard −1 LSB on the kpex of the drawn cell) is tested more finely by the calibration rehearsal below, at tt only.
- At ss 125 °C, 1.03T decides 212 ns later than the 1.8× fault (1.376 vs 1.164 µs): this point is close to that corner's threshold. At tt and ff −40 °C, 1.03T decides on the same strobe as 1.8×.

### c. Calibration rehearsal (case `cal`, tt, 1 A = 25 mV, ideal crossing code 127.1)

The stimulus and detection are as in the r3x record. Each code is held 3.39 µs. The code schedule is the first line of each deck (`* CALSCHED`).

| Comparator / window | r3 | r4 | Status | Log (`cdl_…`) |
|---|---|---|---|---|
| hard, coarse 150→94 step 8 | coarse 206→142 step 8: 174 silent, 166 fires | **134 silent, 126 fires**: first `cmp_hard` 28.29 µs, 0.48 µs after the code-126 write; trip_d 29.24 µs. The solver then stopped at 44.83 µs of 48 µs (BGR `xq736` timestep too small). The CAL and TRIP measures were emitted. | not run to completion after the crossing (numbers usable) | `cal_pex_tt_27C_gear_…_ser4_icx_hard150-86-8_maxstep1ns_functional_r4a` |
| hard, 2-code 134→118 | 2-code 172→156: 172 silent, **170 fires** | reached 41.06 µs of 52 µs at the 24 800 s bound; no measures | not run to completion (timeout) | `cal_pex_tt_27C_gear_…_ser4_icx_hard134-116-2_maxstep1ns_functional_r4a` |
| hard, 2-code 132→124 | — | reached 36.77 µs of 38 µs at the 24 800 s bound; no measures | not run to completion (timeout) | `cal_pex_tt_27C_gear_…_ser4_icx_hard132-122-2_maxstep1ns_functional_r4a` |
| hard, 2-code 130→126 (36 000 s bound) | 2-code 172→156: 172 silent, **170 fires** | 130 and 128 silent, **126 fires**: first `cmp_hard` 24.90 µs, 0.48 µs after the code-126 write; trip_d 25.85 µs (cause 2) | passed | `cal_pex_tt_27C_gear_…_ser4_icx_hard130-124-2_maxstep1ns_functional_r4b` |
| soft, 2-code 130→126 (36 000 s bound) | 130 silent, **128 fires** (0.59 µs after the write) | 130 silent, **128 fires**: first `cmp_soft` 21.62 µs, 0.59 µs after the code-128 write; soft_armed 21.93 µs; no hard decision, no trip | passed | `cal_pex_tt_27C_gear_…_ser4_icx_soft130-124-2_maxstep1ns_functional_r4b` |
| soft, 2-code 134→118 and 132→124 | — | reached 41.11 / 36.25 µs at the 24 800 s bound; no measures | not run to completion (timeout) | `cal_pex_tt_27C_gear_…_ser4_icx_soft134-116-2_maxstep1ns_functional_r4a`, `cal_pex_tt_27C_gear_…_ser4_icx_soft132-122-2_maxstep1ns_functional_r4a` |

- **Hard crossing.** Code 128 is silent and 126 fires (2-code window; coarse: 134 silent, 126 fires). The r4 hard crossing is therefore 127 ± 1, against the ideal 127.1: −1.1 to +0.9 codes = **within 1 LSB (0.2 mV)**. On r3 it was 171 ± 1 (+43 to +45 codes, 8.5–8.9 mV).
- **Soft crossing.** It is unchanged against r3 (129 ± 1).
- **hard_extra.** On r3, the hard crossing sat 41–43 codes above the soft crossing (the `hard_extra` of bring-up step S9). On r4 the hard comparator fires 2 codes (0.4 mV) below the soft one (126 vs 128 first firing), so `hard_extra` goes from about +42 to about −2 codes.

### d. tt functional cases

| Case | r3 (r3full, tt) | r4 | Status | Log (`cdl_…`) |
|---|---|---|---|---|
| q, 44 µs, 1 A (no trip) | no trip; tripped max 7.6 mV, GATE min 3.298 V; VDDA 1462.5 µA, IOVDD 104.0 µA | no trip; tripped max 7.6 mV, GATE min 3.298 V, 1 A at the end; VDDA 1462.5 µA, IOVDD 104.1 µA | passed | `q_pex_tt_27C_gear_…_icx_maxstep1ns_functional_r4a` |
| e20, 4× in 20 ns (hard trip) | 1.1526 / 1.1553 / 1.5318 / 1.7679 | 1.1524 / 1.1552 / **1.5317** / 1.7677, cause 2 | passed | `e20_pex_tt_27C_gear_…_icx_maxstep1ns_functional_r4a` |
| hard_pulse, 45 mV for 200 ns (no trip) | no trip; tripped max 49 mV, GATE min 3.298 V | reltol 5e-4 with the 36 000 s bound (r4b, 26 090 s): no trip; tripped max 49 mV, GATE min 3.298 V, 1 A at the end. The first attempt failed (numerical) at 23.32 µs (BGR `xq736`), before the pulse; reltol 5e-4 (r4a) reached 33.70 µs of 44 µs at the 24 800 s bound, with no measures | passed | `hard_pulse_pex_tt_27C_gear_…_icx_maxstep1ns_functional_r4a`, `hard_pulse_pex_tt_27C_gear_…_optreltol5em4_functional_r4a`, `hard_pulse_pex_tt_27C_gear_…_optreltol5em4_functional_r4b` |
| f_mid, trip then EN re-arm | 1.1526 / 1.1553 / 1.5318 / 1.7679; re-arm 0.678 µs | reltol 5e-4 with the 36 000 s bound (r4b, 28 285 s): 1.1525 / 1.1552 / **1.5317** / 1.7678, cause 2; re-arm: GATE 2.7 nV while EN low, GATE 90 % **0.678 µs** after EN high, 3.300 V and 1 A at the end, tripped 49 nV. The first attempt failed (numerical) at 23.32 µs (BGR `xq736`), before the event; reltol 5e-4 (r4a) reached 34.87 µs of 50 µs at the 24 800 s bound, with no measures | passed | `f_mid_pex_tt_27C_gear_…_icx_maxstep1ns_functional_r4a`, `f_mid_pex_tt_27C_gear_…_optreltol5em4_functional_r4a`, `f_mid_pex_tt_27C_gear_…_optreltol5em4_functional_r4b` |
| b_s, 1.5× held, SOFT_TIME_L = 1 (soft trip) | 27.752 / 27.755 / 28.131 / 28.367, cause 1 | with the 36 000 s bound (r4b, 34 255 s): **soft trip** 27.752 / 27.755 / **28.131** / 28.368, cause 1 (soft_peak 1). The first attempt (r4a) reached 48.65 µs of 64 µs at the 24 800 s bound, before the soft decision, with no measures | passed | `b_s_pex_tt_27C_gear_…_functional_r4a`, `b_s_pex_tt_27C_gear_…_functional_r4b` |

### e. Transistor-level oscillator clocking the RTL (`--osc tl`, c_mid compact, tt)

| | r3x | r4 | Status | Log |
|---|---|---|---|---|
| f_osc / f_cmp | 9.4415 / 4.7207 MHz | 9.4414 / 4.7207 MHz | — | |
| trip | 1.1211 / 1.1239 / 1.5004 / 1.7364, cause 2 | 1.1211 / 1.1239 / **1.5004** / 1.7364, cause 2 | passed | `cdl_c_mid_pex_tt_27C_gear_osctl_compact_…_icx_maxstep1ns_functional_r4a` (21 739 s) |

### f. Power-up (`--por-pin`, real EN/GATE/FAULT_N pads)

| Case | Corner / step | r3x | r4 (`GATE` max while EN low / `GATE` after EN / `en_i` max / `tripped` max) | Status | Log |
|---|---|---|---|---|---|
| gB | ss 125 °C, 20 ns | 36 µV; 3.300 V | 36.2 µV / 3.300 V / 0.933 V / 1.227 V (spurious latch window with IOVDD absent, as r3; GATE never rises) | passed | `cdl_gB_pex_ss_125C_gear_por_…_icx_functional_r4a` |
| gB_pd | ss 125 °C, 20 ns | 36 µV; 3.283 V | 36.0 µV / 3.283 V / 0.933 V / 1.228 V | passed | `cdl_gB_pd_pex_ss_125C_…_r4a` |
| gB | ff −40 °C, 2 ns | 28 µV; 3.300 V | 28.2 µV / 3.300 V / 0.844 V / 1.239 V | passed | `cdl_gB_pex_ff_-40C_…_maxstep2ns_functional_r4a` |
| gB_pd | ff −40 °C, 2 ns | 28 µV; 3.291 V | 28.1 µV / 3.291 V / 0.844 V / 1.239 V | passed | `cdl_gB_pd_pex_ff_-40C_…_maxstep2ns_functional_r4a` |
| gS (simultaneous ramp) | ss 125 °C, 20 ns | 0.521 V peak, no trip | **0.520 V** peak (`gate_core` 0.517 V, `en_i` ≤ 61 mV), never above 1 V; `tripped` max 0.321 V (no trip) | passed | `cdl_gS_pex_ss_125C_…_r4a` (1840 s) |

## Findings

1. **The early hard trip is gone on the full-chip layout netlist.** On r3 the hard comparator decided 40–59 LSB below the code. On r4, at all three corners, it does not trip at 0.97T and trips at 1.03T of the code-200 nominal.
   - Every r3x bracket point that tripped on r3 (31.25 mV at tt and ss 125 °C, 28.75 mV at ff −40 °C) now gives no trip.
   - The soft crossing is unchanged (129 ± 1).
   - The tt calibration rehearsal puts the hard crossing at code 127 ± 1, against the ideal 127.1 (r3: 171 ± 1).
   - This closes the §6 near-threshold failure of the r3x record: within 1 LSB at tt (calibration), and within ±6 LSB at ss 125 °C and ff −40 °C (the ±3 % brackets).
2. **Trip timing and the rest of the trip path are unchanged.**
   - c_mid, e20, f_mid and the real-oscillator trip agree with r3 within 0.3 ns in every column, at all three corners, as do the QUIET voltages and supply currents.
   - The f_mid re-arm is 0.678 µs, as on r3.
   - The b_s soft trip (cause 1) is at 27.752 µs, as on r3.
   - hard_pulse does not trip (tripped max 49 mV, as on r3).
   - Only the near-threshold 1.03T point at ss 125 °C is slower (decision 1.376 µs), as expected so close to the threshold.
3. **Power-up is unchanged**: gB/gB_pd ss and ff, and gS ss, match r3x to within 0.2 µV / 1 mV.
4. **Numerics.** Fourteen `r4a` attempts **failed (numerical)** with "timestep too small" on a BGR VBIC instance (`xq760` or `xq736`):
   - c_mid ss at 1 ns (6.789 µs) and 2 ns (10.50 µs);
   - c_mid tt at 27.77 µs and 1.25× tt at 19.08 µs, both after their event;
   - f_mid and hard_pulse at 23.32 µs;
   - the coarse hard cal at 44.83 µs, after its crossing.

   The deck differs from r3 only in the TRIP extraction and the CDL (deck check above); BGR, SENSE, GATE, T2F, interconnect and solver options are identical to the r3x commands. The failures are therefore solver-trajectory effects of the same BGR HBTs that failed r3 runs at other steps (r3full ff 5 ns at 7.385 µs `xq760`; r3x gB ff 20 ns `xq736`/`xq760`). No evidence points elsewhere.

   Each failed case was rerun once with an r3-proven mitigation:
   - 5 ns step at ss, as r3full c_mid ss;
   - `reltol 5e-4`, as r3full c_mid tt;
   - or `--tstop 19` for compact c_mid, as the gap runs used.

   Every rerun that completed agrees with the other variants within 0.2 ns.
5. **Timeouts.** The overnight machine load (load average about 245) slowed each run by about 1.5× against r3x. The 24 800 s bound therefore stopped:
   - b_s at 48.65 µs;
   - the four 2-code cal windows at 36.3–41.1 µs;
   - the reltol reruns of f_mid (34.87 µs) and hard_pulse (33.70 µs).

   None produced measures. Short windows (130→126) and the 36 000 s reruns cover them.

## Not run / not run to completion

| Item | Status |
|---|---|
| b_s tt (soft trip) | r4a: not run to completion (timeout at 48.65 µs); r4b with the 36 000 s bound: passed |
| f_mid tt | r4a: failed (numerical, 23.32 µs); r4a reltol: not run to completion (timeout at 34.87 µs); r4b reltol 5e-4 with the 36 000 s bound: passed |
| hard_pulse tt | r4a: failed (numerical, 23.32 µs); r4a reltol: not run to completion (timeout at 33.70 µs); r4b reltol 5e-4 with the 36 000 s bound: passed |
| cal hard 2-code | 134→118 and 132→124: not run to completion (timeout); 130→126 (r4b) passed |
| cal soft 134→118, 132→124 | not run to completion (timeout); superseded by 130→126 (passed) |
| cal hard coarse 150→94 | not run to completion (numerical at 44.83 µs, after the crossing; measures emitted) |
| cal at ss/ff; near threshold at the supply extremes; real oscillator at ss/ff; stock pads; series wire R, bondpad and fill C | not run (as r3x) |
| hard threshold finer than ±3 % at ss and ff | not run |
| mismatch / Monte Carlo on the full chip | not run (block-level 60-seed MC of the non-overlap window: `g1_trip` qualification, commit `b089b9545`) |

## Wall time and CPU

The first launch was at 17:51 CEST on 2026-09-27 and the last run ended at 08:18 CEST on 2026-09-28, 14.5 h of elapsed time. 55 runs were made (29 in the first launch, 26 reruns), for 208.8 CPU-hours summed wall time, one CPU each. Per-run wall times are in the JSONs (`wall_s`):
- c_mid compact: 11 600–12 500 s (1 ns); about 10 000 s (5 ns at ss); 16 000–21 000 s (reltol 5e-4 under the night load);
- osc tl: 21 739 s;
- q: 21 523 s;
- f_mid / hard_pulse / b_s (r4b, 36 000 s bound): 28 285 / 26 090 / 34 255 s;
- calibration 130→126 (r4b): 18 892 s (hard) / 15 257 s (soft);
- e20: 16 048 s;
- power-up: 1840–3227 s.

## Commands (repository root, `BULK` set; `W=designs/g1-guardian/blocks/g1_top/sim`)

```
C="--cdl /work/designs/g1-guardian/blocks/g1_padring/netlist/g1_chip_top_1414_r4.cdl \
   --cdl-sha256 e060c0c59a168e5b69b0c47dc31cbfe4f4444d2ec8af62960c339c1230a2c99f --blockset c1414r4 \
   --rtl-dir eco_20260925 --netlist pex --method gear --interconnect extracted --timeout 24800 --run-id r4a"
CM="c_mid --timeline compact --maxstep-ns 1"
flow/launch_pinned.sh <cpu> $W 25200 <log> python3 run_top_cdl.py $CM {--corner tt --temp 27|--corner ss --temp 125|--corner ff --temp -40} $C
flow/launch_pinned.sh <cpu> $W 25200 <log> python3 run_top_cdl.py $CM <corner> --fault-mult {1.2|1.25|1.1|1.15|1.5229|1.6171|1.5256|1.62|1.5186|1.6126} $C
flow/launch_pinned.sh <cpu> $W 25200 <log> python3 run_top_cdl.py cal --cal-kind {hard|soft} --cal-codes {150:86:-8|134:116:-2|132:122:-2} --ser-start-us 4 --maxstep-ns 1 $C
flow/launch_pinned.sh <cpu> $W 25200 <log> python3 run_top_cdl.py {hard_pulse|q|f_mid|b_s|e20} --maxstep-ns 1 $C
flow/launch_pinned.sh <cpu> $W 25200 <log> python3 run_top_cdl.py $CM --osc tl $C
flow/launch_pinned.sh <cpu> $W 25200 <log> python3 run_top_cdl.py {gB|gB_pd} --por-pin --corner ss --temp 125 $C
flow/launch_pinned.sh <cpu> $W 25200 <log> python3 run_top_cdl.py {gB|gB_pd} --por-pin --corner ff --temp -40 --maxstep-ns 2 $C
flow/launch_pinned.sh <cpu> $W 25200 <log> python3 run_top_cdl.py gS --por-pin --corner ss --temp 125 $C
# reruns after the numerical failures (same C):
#   ss c_mid rows: --maxstep-ns 5 (and --maxstep-ns 2, failed); 1 ns with --extra-options reltol=5e-4
#   tt c_mid, tt 1.25x, f_mid, hard_pulse: --extra-options reltol=5e-4
# r4b (C with --run-id r4b): $CM --corner tt --temp 27 --tstop 19 [--fault-mult 1.25]
# r4b with --timeout 36000 and wall 36400: b_s --maxstep-ns 1; {f_mid|hard_pulse} --maxstep-ns 1 --extra-options reltol=5e-4;
#   cal --cal-kind {hard|soft} --cal-codes 130:124:-2 --ser-start-us 4 --maxstep-ns 1
```

Logs over 300 kB are retained in `${BULK}/g1-freeze-retention-20260925/g1_top_logs_r4a/` (hash-verified, entries `addition_20260928_r4a` in `review/local-retention-20260925.json`). A `.tail.txt` extract (header plus the last 140 lines) stays in `sim/logs/`. Waveform figures: [`figures/fullchip_r4a/`](figures/fullchip_r4a/).

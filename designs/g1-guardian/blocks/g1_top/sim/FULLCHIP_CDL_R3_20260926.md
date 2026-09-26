# G1 full-chip simulation of the r3 chip of record: layout netlist, block extractions and top-level interconnect (2026-09-26)

Every number here is **simulated**. The runs used:
- ngspice-46 with the Icarus d_cosim;
- IHP SG13G2 open PDK `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`;
- image `tapeoutbench-eda:latest` (`sha256:ddeb6957…`).

Run id prefix: `r3full` (and `r3full2` for two relaunches). Logs are `sim/logs/cdl_*_r3full*.log/.json`, decks are `sim/decks/cdl_*_r3full*.cir`, and summaries are appended to `sim/results_cdl.txt`.

## What the deck is

| Item | Value |
|---|---|
| Chip netlist | `blocks/g1_padring/netlist/g1_chip_top_1414_r3.cdl`, SHA-256 `5e47ae022ab73b4e060afaee22a1299bc62e1a895f4c9e15f865820505d52629`. It is translated by `run_top_cdl.py` exactly as in `FULLCHIP_CDL_20260925.md`: CDL IO cells (`G1_VSS_DERIVATIVE__*`), top-level decaps merged with `m=N`, supply-pin ammeters, and one `g1_chip_top` instance on the run_top board. |
| Digital | The gate-level `g1_digital` of the CDL is replaced by the XSPICE d_cosim of the frozen ECO RTL (`--rtl-dir eco_20260925`, register map 1.2; `g1_regfile.v` `33d549da`, `g1_digital_top.v` `4e3b8ff6`). The wrapper is `rtl/g1_dig_cosim_cdl.v`, with `por_n` tied high. Power-up cases use `rtl/g1_dig_cosim_cdl_por.v` (`--por-pin`), so `por_n` comes from the CDL `sg13g2_tiehi`. |
| Block views (`--netlist pex`) | BGR586 kpex `01227a3d`; SENSE R100 partial-C `ffb14762`; TRIP NF4 kpex `ba86b7b2`; GATE Sep-19 PEX; T2F PEX `441edabc`; OSC R0.95 CPEX `8efd7a09` (osc case only, `--osc tl`). Level shifters, DOSE/DUT and IO cells come from the CDL. |
| Top-level interconnect (`--interconnect extracted`, new) | `postlayout/top_interconnect_20260925.spice`, SHA-256 `ddc88cc765e99a0e982c9b6bc24817bfe336ae686930b2c12a85d514fb2adcc2`. The C-only subckt `g1_top_interconnect` (57 nets, kpex 2.5D CC) is instantiated inside the deck-local `g1_chip_top`. Port to CDL net: the 8 pad nets upper case, `en_i`/`gate_o`/`fault_n_o`/`net` by name, every other net as `i_core_<port>`; `sub` goes to VSS. Nothing is removed, because the CDL deck has no `Cw_*` estimates. The extraction is of the r1 geometry; per its README, r3 differs only inside the digital macro and in fill. **Not included:** the series wire R (the pi variant needs split nets), bondpad C, fill. |
| Clock | Ideal 9.436194721 MHz (R0.95 loaded, trim 8), gated by the RTL `osc_en`, except in the osc case. |
| Solver | gear, `reltol 1e-3`, `abstol 1e-10`, `vntol 1e-6`, `chgtol 1e-14`, maximum step 1 ns unless a row says otherwise |
| Pads | `--pads nodcn` in **every** result row: all 8 `dantenna` instances are removed from the IO cells (SENSE, VREF, EN, SCLK, SDI, GATE, FAULT_N, …) and from `sg13g2_antennanp`. Stock pads (`--pads pdk`) did not complete in any case, see "Not run to completion". |
| Timeline | c_mid, c_mid ss/ff and the near-threshold rows use `--timeline compact` (frames from 4 µs, as `eco4_cdl_c_mid_ser4`; fault at 16 µs; stop 28 µs). All other cases use the run_top baseline timeline (frames from 18 µs, event at 30 µs). The T2F-off witness rows use frames from 4 µs (`--ser-start-us 4`), with the event still at 30 µs. |
| T2F | On from reset in every primary row: TEMP_CTRL = 1, 1.516 MHz, driving `TEMP_OUT` into 20 pF. Witness rows `_t2foff` add a serial write TEMP_CTRL = 0 (address 0x29, map 1.2) right after the INRUSH frame: **"T2F disabled by register write (stimulus), sensor accuracy not exercised"**. |
| Process | Every run was launched with `flow/launch_pinned.sh`, one CPU each, wall 25 200 s, `--timeout 24800`. The first wave and the near-threshold rows ran at nice 0; the relaunch waves (`_optreltol5em4`, `_t2foff`, `osc` variants, `gA` reltol) ran at nice 5. "mismatched XSPICE" appears in no log. |

## Results (tt 27 °C unless noted)

Times are measured from the load event. `trip_d` is the RTL trip decision, followed by the G1_GATE latch `tripped` and then `GATE` < 1 V and < 0.33 V. Cause 1 = soft, 2 = hard.
The QUIET values are 2 µs averages before the event, in the order VREF / ISENSE / icmp / vth_soft / vth_hard, in V.
Supply currents are averaged over the armed window.

| Case (expected) | Deck variant | Status | trip_d / tripped / GATE<1 V / <0.33 V (µs) | Cause | QUIET (V) | VDDA / IOVDD (µA) | Verdict (spec §6) | Log (`cdl_…_r3full`) |
|---|---|---|---|---|---|---|---|---|
| q, 44 µs, nominal 1 A (no trip) | 1 ns, T2F on | completed, 15 184 s | no trip; tripped max 7.6 mV, GATE min 3.298 V, 1 A at the end | 0 | 1.04501 / 1.50693 / 0.75338 / 0.80454 / 1.00339 | 1462.5 / 104.0 | **pass** (no false trip) | `q_pex_tt_27C_gear_…_icx_maxstep1ns` |
| q, T2F off | 1 ns, ser4, T2F off | completed, 12 716 s | no trip; GATE min 3.300 V | 0 | 1.04501 / 1.50692 / 0.75338 / 0.80455 / 1.00338 | 1454.5 / 0.002 | pass | `q_…_ser4_icx_t2foff_maxstep1ns` |
| c_mid compact, 1.8×/45 mV at code 200 (hard trip) | 1 ns | completed, 12 316 s | 1.1639 / 1.1666 / **1.5432** / 1.7792 | 2 | 1.04501 / 1.50691 / 0.75300 / 0.80408 / 0.89715 | 1462.8 / 128.1 | **pass** (≥1.1T, < 10 µs) | `c_mid_…_compact_…_icx_maxstep1ns` |
| c_mid compact | 5 ns, reltol 5e-4 | completed, 12 047 s | 1.1637 / 1.1665 / 1.5430 / 1.7790 | 2 | same | 1462.8 / 128.2 | pass | `…_compact_…_icx_optreltol5em4` |
| c_mid compact, T2F off | 1 ns, T2F off | completed, 11 029 s | 1.1639 / 1.1666 / 1.5431 / 1.7792 | 2 | vth_hard 0.9257 (window overlaps the last frame) | not valid (window) | pass | `…_compact_…_ser4_icx_t2foff_maxstep1ns` |
| c_mid compact, **ss 125 °C** | 5 ns | completed, 7915 s | 1.1638 / 1.1678 / **1.7264** / 2.0597 | 2 | 1.04682 / 1.51004 / 0.75453 / 0.80539 / 0.89876 | 1727.9 / 97.9 | **pass** | `c_mid_pex_ss_125C_…_compact_…_icx` |
| c_mid compact, ss 125 °C | 1 ns; 5 ns T2F off; 1 ns T2F off | completed, 12 368 / 10 322 / 7698 s | 1.1639 / – / 1.7264 / 2.0597 (all three within 0.03 ns) | 2 | same | 1727.8 | pass | `…ss_125C…maxstep1ns`, `…_t2foff`, `…_t2foff_maxstep1ns` |
| c_mid compact, **ff −40 °C** | 1 ns | completed, 12 586 s | 1.1637 / 1.1656 / **1.4334** / 1.6126 | 2 | 1.04208 / 1.50320 / 0.75120 / 0.80191 / 0.89458 | 1279.4 / 97.1 | **pass** | `c_mid_pex_ff_-40C_…_compact_…_icx_maxstep1ns` |
| c_mid compact, ff −40 °C, T2F off | 1 ns | completed, 7784 s | 1.1639 / 1.1658 / 1.4336 / 1.6127 | 2 | same | 1271.2 | pass | `…ff_-40C…_t2foff_maxstep1ns` |
| c, 3× (75 mV), code 0xFE (hard trip) | 1 ns | completed, 12 821 s | 1.1524 / 1.1552 / 1.5316 / 1.7677 | 2 | 1.04501 / 1.50693 / 0.75338 / 0.80454 / 1.00339 | 1462.3 / 100.0 | **pass** | `c_pex_…_icx_maxstep1ns` |
| c, T2F off | 1 ns | completed, 11 609 s | 1.1524 / 1.1552 / 1.5317 / 1.7677 | 2 | same | 1454.5 | pass | `c_…_ser4_icx_t2foff_maxstep1ns` |
| e20, 4× in 20 ns (hard trip) | 1 ns | completed, 12 987 s | 1.1526 / 1.1553 / 1.5318 / 1.7679 | 2 | same as c | 1462.3 / 100.0 | **pass** | `e20_…_icx_maxstep1ns` |
| e20, T2F off | 1 ns | completed, 11 424 s | 1.1524 / 1.1552 / 1.5317 / 1.7677 | 2 | same | 1454.5 | pass | `e20_…_t2foff_maxstep1ns` |
| f_mid: c_mid trip, load back at 36 µs, EN low 40–42 µs (re-arm) | 1 ns | completed, 17 123 s | 1.1526 / 1.1553 / 1.5318 / 1.7679; **re-arm:** GATE 2.7 nV while EN low, GATE 90 % 0.678 µs after EN high, 3.300 V and 1 A at the end, tripped 49 nV | 0 after re-arm (cleared by EN) | 1.04501 / 1.50693 / 0.75338 / 0.80454 / 0.89697 | 1462.2 / 96.5 | **pass** (trip + re-arm) | `f_mid_…_icx_maxstep1ns` |
| f_mid, T2F off | 1 ns | completed, 14 984 s | identical within 0.02 ns; re-arm 0.678 µs | 0 | same | 1454.5 | pass | `f_mid_…_t2foff_maxstep1ns` |
| b_s, 1.5× held, SOFT_TIME_L = 1 (256 osc_clk; soft trip) | 1 ns | completed, 18 802 s | **27.752** / 27.755 / 28.131 / 28.367 | **1** | 1.04501 / 1.50693 / 0.75338 / 0.80454 / 1.00339 | 1462.2 / 96.6 | **pass** (soft window: 256 samples = 27.13 µs + decision) | `b_s_…_icx_maxstep1ns` |
| b_s, T2F off | 1 ns | completed, 16 508 s | 27.752 / 27.755 / 28.132 / 28.368 | 1 | same | 1454.5 | pass | `b_s_…_t2foff_maxstep1ns` |
| hard_pulse, 45 mV for 200 ns (no trip, FAST_EN = 0) | 1 ns | completed, 13 295 s | no trip; tripped max 49 mV, GATE min 3.298 V | 0 | 1.04501 / 1.50693 / 0.75338 / 0.80454 / 0.89697 | 1462.2 / 96.5 | **pass** (a pulse shorter than HARD_N decisions does not trip) | `hard_pulse_…_icx_maxstep1ns` |
| hard_pulse, T2F off | 1 ns | completed, 12 257 s | no trip; tripped max 49 mV, GATE min 3.300 V | 0 | same | 1454.5 | pass | `hard_pulse_…_t2foff_maxstep1ns` |
| gB, core first: VDD 1–3 µs, IOVDD 5–7 µs, EN low until 12 µs (GATE low) | 20 ns (case default), `--por-pin`, real EN/GATE/FAULT_N pads (nodcn) | completed, 2594 s | GATE max while EN low **31 µV**; after EN 3.300 V | — | — | — | **pass** (no false GATE at power-up, no false trip at EN) | `gB_pex_…_por_…_icx` |
| gB_pd, as gB with 10 kΩ on GATE | same | completed, 2360 s | GATE max while EN low 31 µV; after EN 3.288 V | — | — | — | **pass** | `gB_pd_…_por_…_icx` |
| gA, IO first: IOVDD/VDDA 1–3 µs, VDD 5–7 µs (GATE high while EN low, expected) | 2 ns, `--por-pin` | completed, 2928 s | **GATE 3.300 V from 2.38 to 6.72 µs (4.34 µs)** while EN is low; the 1 A load flows (4.06 µAs); GATE 3.300 V after EN | — | — | — | expected condition, recorded (P1 excludes this order) | `gA_…_por_…_icx_maxstep2ns` |
| gA | 20 ns, reltol 5e-4 (`r3full2`) | completed, 2302 s | identical: 2.38–6.72 µs, 3.300 V | — | — | — | same | `gA_…_por_…_icx_optreltol5em4_…r3full2` |
| osc: q with the transistor-level R0.95 CPEX clocking the RTL | OSC_PENDING | | | | | | | |
| near threshold, c_mid compact, `--fault-mult 1.15` (28.8 mV vs 39.25 mV code 200; expected: no trip) | FM_PENDING | | | | | | | |
| near threshold, c_mid compact, `--fault-mult 1.25` (31.3 mV; expected: trip) | FM_PENDING | | | | | | | |

**Power-up detail (gB, `por_n` from the CDL tie-high, frozen ECO RTL).**
- `por_n` crosses 0.6 V at 2.001 µs, with VDD. IOVDD reaches 1.1 V at 5.667 µs.
- With IOVDD absent, the `EN` pad output `en_i` floats to 0.864 V; it is above 0.6 V from 2.34 to 5.70 µs.
- The G1_GATE `tripped` latch is set from 2.36 to 6.66 µs, and the RTL trip latch from 3.18 to 6.66 µs.
- Both clear at 6.66 µs, one EN deglitch (8 EN-low samples) after `en_i` falls. `GATE` never exceeds 31 µV.
- This is the spurious-latch window already recorded with the map-1.1 RTL. It is reproduced with the map-1.2 RTL and real pads.

## Findings

1. **VREF spikes from the top-level routing.** With the extracted interconnect, the internal VREF net (`i_core_vref`, the padres side of the VREF pad) carries spikes at every `osc_clk` edge.
   - Size: **42.3 mV p-p**, rms 2.5 mV, 26 of 601 samples outside ±2 mV (q, 32–44 µs).
   - Sampling is the 20 ns `linearize` grid, so the true peaks can be higher.
   - Without the interconnect the same case gives 1.3 mV p-p (`cdlpwr`). The ripple is the same with T2F off (42.3 mV).
   - The source is the extracted 38.3 fF `osc_clk`–VREF coupling (46 fC per 1.2 V edge; interconnect README).
   - The mean VREF is unchanged (1.04496 V vs 1.04500 V). No trip decision in this set changed at 1.15–4× nominal.
   - Near-threshold behaviour is covered only by the two `fault-mult` rows.
   - The DAC thresholds follow from VREF_BUF, and `vth_hard` shows ±20–40 mV comparator-kickback spikes with or without the interconnect.
2. **The real GATE pad at ss 125 °C.** `GATE` < 1 V is 0.559 µs after `tripped` (ss/125 °C), against 0.377 µs (tt) and 0.268 µs (ff/−40 °C). The worst case, 1.726 µs from the fault, is well inside the 10 µs target.
3. **The ECO RTL decision is 1.164 µs** (compact, all three corners) against 1.058 µs with the map-1.1 RTL (`FULLCHIP_CDL_20260925.md`). This is the documented one-`osc_clk` sampling phase (+106 ns).
4. **T2F does not change the trip path.** In every case, the T2F-off witnesses agree with the T2F-on runs within 0.2 ns on trip_d/`GATE` and within 0.1 mV on QUIET values. With T2F on, VDDA is 8 µA higher (1462 vs 1454 µA), and IOVDD is 96–128 µA (TEMP_OUT toggling into 20 pF) against ≈ 0.
5. **Numerics.**
   - Every tt run with the 5 ns maximum step failed at 2.664 µs. The failures are "timestep too small" on T2F `xq42` (VBIC), from the T2F running at reset. The 1 ns step removes the failure.
   - reltol 5e-4 at 5 ns completed for `c_mid` compact only; the other reltol runs were stopped (see below).
   - ss/125 °C at 5 ns completed; ff/−40 °C at 5 ns failed at 7.385 µs (BGR `xq760`), and at 1 ns it completed.
   - The osc "loose" settings (reltol 2e-3, xtrtol 7) failed at 0.96 µs (2 ns step; T2F `xq42`), 2.69 µs (1 ns; BGR `xq736`) and 23.7 µs (0.5 ns; BGR `xq736`).

## Verdict against the acceptance criteria (spec §6)

| Criterion | Evidence (this deck) | Verdict |
|---|---|---|
| No trip at nominal and on short pulses (region ≤ 0.9T) | q (1 A = 25 mV vs 39.25/49.8 mV thresholds): no trip at 44 µs; hard_pulse 200 ns: no trip | pass |
| Trip on a persistent fault ≥ 1.1T within 10 µs | c_mid 1.8× (45 mV vs 39.25 mV): GATE < 1 V 1.543 µs tt, 1.726 µs ss/125, 1.433 µs ff/−40; c 3×: 1.532 µs; e20 4×: 1.532 µs | pass |
| Soft window | b_s: soft trip (cause 1) 27.75 µs after a 1.5× step with a 256-sample window; GATE < 1 V 28.13 µs | pass |
| Re-arm | f_mid: EN low clears both latches; GATE 90 % 0.678 µs after EN; 1 A restored | pass |
| No false trip at EN / power-up | gB, gB_pd: GATE ≤ 31 µV with EN low; no trip before the event or at EN rise in any functional case (tripped before the event ≤ 11 mV) | pass; latches toggle while IOVDD is absent (finding above; P2 inhibit) |
| IO-first order | gA: GATE 3.30 V for 4.34 µs | expected; excluded by P1 |
| Near threshold | FM_VERDICT | |

## Not run to completion / not run

| Item | Status |
|---|---|
| Stock pads (`--pads pdk`, with `dantenna`): q, c_mid, c, e20, f_mid, b_s, hard_pulse | **failed**: timestep too small at 1.679 µs at both 5 ns and 1 ns steps (every run) |
| Stock-pad power-up gB, gB_pd, gA (20 ns, and gB at 2 ns) | **not run to completion**: stalled at 1.19 ns, stopped after 668–885 s |
| 5 ns-step tt runs of every functional case | **failed** at 2.664 µs (T2F `xq42`); superseded by the 1 ns rows |
| reltol 5e-4 variants of q, c, e20, f_mid, b_s, hard_pulse, gA | **not run to completion**: stopped by me at 1.3–2.8 µs to free CPUs (gA relaunched as `r3full2`, completed) |
| T2F-off variants at 5 ns (tt) | **not run to completion**: stopped or failed at 0.7–2.4 µs (the T2F is on until the register write) |
| c_mid ff −40 °C at 5 ns (T2F on and T2F off) | **failed** at 7.385 µs (BGR `xq760`); the 1 ns rows completed |
| gA at 20 ns (T2F on) | **failed** at 1.87 µs (T2F `xq42`); 2 ns completed |
| OSC_NOTRUN | |
| Series wire R of the interconnect (pi variant), bondpad C, fill C | not run |
| Corners other than c_mid ss/125 and ff/−40; supply ±10 %; the 72-cell matrix on this deck | not run |
| T2F accuracy on this deck | not run (T2F on in the primary rows, not evaluated) |
| Soft-window cases a/b/d (≈ 1 ms), c_fast, clear_read, inrush_pulse | not run |

## Commands (repository root, `BULK` set; `W=designs/g1-guardian/blocks/g1_top/sim`)

```
C="--cdl /work/designs/g1-guardian/blocks/g1_padring/netlist/g1_chip_top_1414_r3.cdl \
   --cdl-sha256 5e47ae022ab73b4e060afaee22a1299bc62e1a895f4c9e15f865820505d52629 --rtl-dir eco_20260925 \
   --netlist pex --method gear --interconnect extracted --timeout 24800 --run-id r3full"
flow/launch_pinned.sh <cpu> $W 25200 <log> python3 run_top_cdl.py q --maxstep-ns 1 $C
flow/launch_pinned.sh <cpu> $W 25200 <log> python3 run_top_cdl.py c_mid --timeline compact --maxstep-ns 1 $C
flow/launch_pinned.sh <cpu> $W 25200 <log> python3 run_top_cdl.py c_mid --timeline compact --corner ss --temp 125 $C
flow/launch_pinned.sh <cpu> $W 25200 <log> python3 run_top_cdl.py c_mid --timeline compact --corner ff --temp -40 --maxstep-ns 1 $C
flow/launch_pinned.sh <cpu> $W 25200 <log> python3 run_top_cdl.py {c|e20|f_mid|b_s|hard_pulse} --maxstep-ns 1 $C
flow/launch_pinned.sh <cpu> $W 25200 <log> python3 run_top_cdl.py {gB|gB_pd} --por-pin $C
flow/launch_pinned.sh <cpu> $W 25200 <log> python3 run_top_cdl.py gA --por-pin --maxstep-ns 2 $C
flow/launch_pinned.sh <cpu> $W 25200 <log> python3 run_top_cdl.py q --osc tl --maxstep-ns 1 $C
# T2F-off witnesses: add  --t2f-off-write --ser-start-us 4 --maxstep-ns 1
# near threshold (run-id r3full2): c_mid --timeline compact --maxstep-ns 1 --fault-mult {1.15|1.25}
```

New `run_top_cdl.py` options in this round: `--interconnect extracted` (hash-bound), `--t2f-off-write`, `--ser-start-us` for the baseline timeline, and `--fault-mult` (`run_top.scale_fault`). `run_top.py` is unchanged by this work.

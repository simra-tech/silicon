# G1 r3 full-chip corners, supply extremes, real-oscillator trip and calibration rehearsal (run `r3x`, 2026-09-26/27)

Every number here is **simulated**. The runs used:
- ngspice-46 with the Icarus d_cosim;
- IHP SG13G2 open PDK `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`;
- image `tapeoutbench-eda:latest` (`sha256:ddeb6957…`).

The deck is the r3full deck of [`FULLCHIP_CDL_R3_20260926.md`](FULLCHIP_CDL_R3_20260926.md), unchanged:
- r3 CDL `5e47ae02`;
- frozen ECO RTL (`--rtl-dir eco_20260925`, map 1.2);
- all block extractions (BGR586, SENSE R100, TRIP NF4, GATE, T2F; OSC R0.95 CPEX with `--osc tl`);
- `--interconnect extracted` (`ddc88cc7`, C only);
- gear, 1 ns maximum step (power-up: the case step, 20 ns, or 2 ns where noted);
- `--pads nodcn` (all 8 `dantenna` removed, including the EN/GATE/FAULT_N pads);
- T2F on from reset;
- ideal 9.436 MHz clock unless `--osc tl`.

Run ids `r3x` and `r3x2`, one CPU each via `flow/launch_pinned.sh`, wall 25 200 s, all at nice 0. No log contains "mismatched XSPICE". Logs are in `sim/logs/cdl_*_r3x*.log`.

New `run_top_cdl.py` options:
- `--vdd` / `--vdda` set run_top `VDD_V`/`VDDA_V` and the bridge band, so rails, EN/SCLK/SDI PWLs, adc/dac bridges and measurement thresholds all scale. The CDL deck uses the real pads, so there is no EN copy or fitted GATE fixture to scale.
- Case `cal` with `--cal-kind hard|soft` and `--cal-codes`, described below.

## Status (spec §6 acceptance)

Times are from the load event: trip_d / `tripped` / `GATE` < 1 V / < 0.33 V.

| Case | Corner / supply | Result | Status | Log (`cdl_…`) |
|---|---|---|---|---|
| gB core first (VDD 1–3 µs, IOVDD 5–7 µs, EN low until 12 µs), `--por-pin`, real EN/GATE/FAULT_N pads | ss 125 °C, 20 ns | `GATE` max while EN low 36 µV; 3.300 V after EN; `en_i` floats to 0.935 V while IOVDD is absent; `tripped` set spuriously 2.90–5.82 µs, RTL trip 5.84–6.66 µs | passed | `gB_pex_ss_125C_…_por_…_icx` |
| gB_pd, 10 kΩ on GATE | ss 125 °C, 20 ns | `GATE` max 36 µV while EN low; 3.283 V after EN | passed | `gB_pd_pex_ss_125C_…_por_…_icx` |
| gB | ff −40 °C, 2 ns | `GATE` max 28 µV while EN low; 3.300 V after EN; `en_i` 0.844 V; latch window 2.26–6.66 µs | passed | `gB_pex_ff_-40C_…_por_…_icx_maxstep2ns` |
| gB_pd | ff −40 °C, 2 ns | `GATE` max 28 µV; 3.291 V after EN | passed | `gB_pd_pex_ff_-40C_…_por_…_icx_maxstep2ns` |
| gB and gB_pd | ff −40 °C, 20 ns | timestep too small at 6.31 / 6.49 µs (BGR `xq736` / `xq760`); superseded by the 2 ns rows | failed (numerical) | `gB_pex_ff_-40C_…_por_…_icx` |
| f_mid (trip, then EN re-arm) | ss 125 °C | 1.1526 / 1.1565 / 1.7151 / 2.0484 µs; re-arm: `GATE` 90 % 0.958 µs after EN; 1 A at the end | passed | `f_mid_pex_ss_125C_…_icx_maxstep1ns` |
| f_mid | ff −40 °C | 1.1526 / 1.1545 / 1.4223 / 1.6014 µs; re-arm 0.514 µs; 1 A at the end | passed | `f_mid_pex_ff_-40C_…_icx_maxstep1ns` |
| b_s (1.5× held, SOFT_TIME_L = 1) | ss 125 °C | soft trip (cause 1): 27.752 / 27.756 / 28.315 / 28.648 µs | passed | `b_s_pex_ss_125C_…_icx_maxstep1ns` |
| b_s | ff −40 °C | soft trip (cause 1): 27.752 / 27.754 / 28.022 / 28.201 µs | passed | `b_s_pex_ff_-40C_…_icx_maxstep1ns` |
| hard_pulse (45 mV, 200 ns; no trip) | ss 125 °C | no trip; latch max 54 mV; GATE min 3.299 V | passed | `hard_pulse_pex_ss_125C_…_icx_maxstep1ns` |
| hard_pulse | ff −40 °C | no trip; latch max 49 mV; GATE min 3.297 V | passed | `hard_pulse_pex_ff_-40C_…_icx_maxstep1ns` |
| q 44 µs (no trip) | tt, VDD 1.08 V / VDDA = IOVDD 3.0 V | no trip; GATE min 2.999 V; VDDA 1455 µA | passed | `q_pex_tt_27C_…_icx_vdd1p08_vdda3_maxstep1ns` |
| q 44 µs | tt, VDD 1.32 V / VDDA 3.6 V | no trip; GATE min 3.598 V; VDDA 1470 µA | passed | `q_pex_tt_27C_…_icx_vdd1p32_vdda3p6_maxstep1ns` |
| c_mid compact (1.8×, code 200) | tt, 1.08 V / 3.0 V | 1.1637 / 1.1676 / 1.5466 / 1.7993 µs, cause 2 | passed | `c_mid_pex_tt_27C_…_compact_…_icx_vdd1p08_vdda3_maxstep1ns` |
| c_mid compact | tt, 1.32 V / 3.6 V | 1.1639 / 1.1661 / 1.5429 / 1.7675 µs, cause 2 | passed | `c_mid_pex_tt_27C_…_compact_…_icx_vdd1p32_vdda3p6_maxstep1ns` |
| c_mid compact, **transistor-level R0.95 oscillator** (`--osc tl`, standard tolerances) | tt | f_osc 9.4415 MHz, f_cmp 4.7207 MHz; 1.1211 / 1.1239 / **1.5004** / 1.7364 µs, cause 2 | passed | `c_mid_pex_tt_27C_gear_osctl_compact_…_icx_maxstep1ns` |
| c_mid compact, `--osc tl`, reltol 5e-4 (second attempt) | tt | 1.1241 / 1.1269 / 1.5034 / 1.7394 µs | not needed, superseded (it completed, 19 300 s) | `c_mid_pex_tt_27C_gear_osctl_compact_…_icx_maxstep1ns_optreltol5em4` |
| near threshold 1.15× (28.75 mV at code 200) | ss 125 °C | no trip (latch max 9.8 mV) | passed | `c_mid_pex_ss_125C_…_compact_…_icx_fm1p15_maxstep1ns` |
| near threshold 1.20× (30.0 mV) | ss 125 °C | no trip (latch max 9.8 mV), run `r3x2` | passed | `c_mid_pex_ss_125C_…_compact_…_icx_fm1p2_maxstep1ns` |
| near threshold 1.25× (31.25 mV = 0.80T) | ss 125 °C | trips late: 1.7995 / 1.8035 / 2.3620 / 2.6954 µs, cause 2 | failed (calibration requirement, planned host compensation) | `c_mid_pex_ss_125C_…_compact_…_icx_fm1p25_maxstep1ns` |
| near threshold 1.10× (27.5 mV = 0.70T) | ff −40 °C | no trip (latch max 6.0 mV). The transient reached 28 µs; the log is truncated after the trip measures by the disk-quota stop, so the JSON status stays "running" | passed | `c_mid_pex_ff_-40C_…_compact_…_icx_fm1p1_maxstep1ns` |
| near threshold 1.05× (26.25 mV) | ff −40 °C | stopped at 27.84 of 28 µs by the disk quota, no measures; not relaunched (1.10× already gives no trip) | not run to completion | `c_mid_pex_ff_-40C_…_compact_…_icx_fm1p05_maxstep1ns` |
| near threshold 1.15× (28.75 mV = 0.73T) | ff −40 °C | **trips**: 1.1639 / 1.1658 / 1.4336 / 1.6128 µs, cause 2 | failed (calibration requirement, planned host compensation) | `c_mid_pex_ff_-40C_…_compact_…_icx_fm1p15_maxstep1ns` |
| near threshold 1.25× (31.25 mV) | ff −40 °C | trips: 1.1637 / 1.1657 / 1.4335 / 1.6126 µs | failed (calibration requirement, planned host compensation) | `c_mid_pex_ff_-40C_…_compact_…_icx_fm1p25_maxstep1ns` |
| near threshold 1.20× (30.0 mV = 0.76T) | tt | no trip (latch max 7.3 mV) | passed | `c_mid_pex_tt_27C_…_compact_…_icx_fm1p2_maxstep1ns` |
| near threshold 1.25× (31.25 mV) | tt (r3full2, earlier record) | trips on the same strobe as at 1.8× | failed (calibration requirement, planned host compensation) | `FULLCHIP_CDL_R3_20260926.md` |
| cal hard, coarse 254→206 in steps of 8 | tt | no crossing (as expected) | passed | `cal_pex_tt_27C_gear_…_ser4_icx_hard254-198-8_maxstep1ns` |
| cal hard, coarse 206→142 in steps of 8 | tt | 174 no, **166 fires** (first cmp_hard 35.07 µs, trip_d 36.03 µs) | passed | `cal_pex_tt_27C_gear_…_ser4_icx_hard206-134-8_maxstep1ns` |
| cal hard, 2-code window 186→172 | tt | no crossing down to 172 (172 held 6.6 µs) | passed | `cal_pex_tt_27C_gear_…_ser4_icx_hard186-170-2_maxstep1ns` |
| cal hard, 2-code window 172→156 | tt | 172 no, **170 fires** (first cmp_hard 21.51 µs, 0.48 µs after the write; trip_d 22.46 µs) | passed | `cal_pex_tt_27C_gear_…_ser4_icx_hard172-154-2_maxstep1ns` |
| cal soft, coarse 254→206 and 206→142 in steps of 8 | tt | no soft decision down to code 142 (cmp_soft max 0.08 V) | passed | `cal_pex_tt_27C_gear_…_ser4_icx_soft254-198-8_maxstep1ns`, `cal_pex_tt_27C_gear_…_ser4_icx_soft206-134-8_maxstep1ns` |
| cal soft, coarse 150→94 in steps of 8 (r3x2) | tt | 134 silent, **126 fires** (first cmp_soft 28.19 µs, 0.37 µs after the code-126 write; soft_armed 28.50 µs); no hard decision, no trip | passed | `cal_pex_tt_27C_gear_…_ser4_icx_soft150-86-8_maxstep1ns` |
| cal soft, 2-code window 134→118 (r3x2) | tt | 130 silent, **128 fires** (first cmp_soft 28.40 µs, 0.59 µs after the code-128 write; soft_armed 28.71 µs); no hard decision, no trip | passed | `cal_pex_tt_27C_gear_…_ser4_icx_soft134-116-2_maxstep1ns` |

The soft cal rows of the first launch (`r3x`, 150→94 and 134→118) were stopped by the home-directory disk quota at 24 µs. They are **not run to completion** and are replaced by `r3x2`.

## Calibration rehearsal (case `cal`, tt 27 °C)

**Stimulus.**
- 1 A steady (25 mV across the shunt) and EN.
- Serial frames from 4 µs: first the swept DAC is written to 254, then INRUSH = 0, then MODE = HARD only (0x02) or SOFT only (0x01).
- SOFT_CFG (hysteresis off) and SENSE_OFS (0) stay at their reset values and are not written.
- Then one DAC write per frame. A frame is 16 SCLK at f_osc/2, so each code is held 3.39 µs (not 3 µs).

**Detection.**
- Hard: by the trip, with HARD_N = 4 decisions.
- Soft: by the first `cmp_soft` decision and `soft_armed` (SOFT_TIME at its ~1 ms default, so no soft trip).
- The code schedule, as code@write-end in µs, is the first line of each deck (`sim/decks/cdl_cal_*.cir`, `* CALSCHED`).

**Ideal crossing.** At 1 A, QUIET icmp = 0.75338 V and VREF = 1.04501 V. So C<sub>ideal</sub> = icmp·530/VREF − 255 = **127.1**, the "code 128 = 25 mV" of the register map. The shunt-referred LSB is (39.25 − 25.0 mV)/72 = 0.198 mV.

| Comparator | Crossing (first firing code / last silent code) | Offset vs ideal | Documented expectation |
|---|---|---|---|
| hard | **170 / 172** (coarse sweep: 166 / 174) | +43 to +45 codes = **8.5–8.9 mV** below the code | ideal + ~45 codes; spec §6: 40–56 LSB, 7.9–11.0 mV (TRIP NF4 block bench) |
| soft | **128 / 130** (coarse sweep: 126 / 134) | +0.9 to +2.9 codes = 0.18–0.57 mV below the code (includes the systematic sense-chain offset at tt; absorbed by `SENSE_OFS`) | spec §6: soft path within 1 LSB on the block bench; here 1–3 codes, all of it removed by the `SENSE_OFS` step |

The hard crossing sits 41–43 codes above the soft crossing at the same input, which is the `hard_extra` of the bring-up sequence (S9). Both sweeps ran 19 000 s wall each.

## Effective hard threshold vs corner at code 200 (simulated)

The code-200 nominal is VREF·(455/530), referred to the shunt: 39.25 mV (tt), 39.32 mV (ss 125 °C), 39.14 mV (ff −40 °C).

| Corner | No trip at | Trips at | Effective threshold | Offset below the code |
|---|---|---|---|---|
| tt 27 °C | 30.0 mV (1.20×) | 31.25 mV (1.25×) | 30.0–31.25 mV (cal sweep: 30.5–30.9 mV equivalent) | 8.0–9.25 mV = 40–47 LSB (cal: 43–45 LSB) |
| ss 125 °C | 30.0 mV (1.20×) | 31.25 mV (1.25×, decision delayed to 1.80 µs) | 30.0–31.25 mV | 8.1–9.3 mV = 41–47 LSB |
| ff −40 °C | 27.5 mV (1.10×) | 28.75 mV (1.15×) | 27.5–28.75 mV | **10.4–11.6 mV = 53–59 LSB** |

## Findings and disposition

1. **The near-threshold fault trips in the no-trip region of spec §6 at ff −40 °C: failed against §6 as written.**
   - At code 200 (T = 39.14 mV), 28.75 mV (0.73 T) trips at ff −40 °C. At tt and ss 125 °C the no-trip bound is 0.76 T (30.0 mV).
   - Cause: the hard-comparator kick offset, documented at tt (effective 30–31 mV at code 200), grows at the fast/cold corner by about 2.3 mV (≈ 12 LSB) against tt and ss 125 °C, which agree within the 1.25 mV step.
   - Not a wiring issue, not the ECO: the decision logic is identical and the offset follows the comparator.
   - The chip is frozen; no layout change. Plan:
     - (a) Per-part hard-threshold calibration on the bench stays mandatory: bracket the effective threshold with the DAC sweep, exactly as the `cal` case does. The table above gives the simulated offset per corner.
     - (b) The offset depends on temperature, so the host applies a temperature-dependent code correction from the on-chip T2F reading. New host rule **H6**: hard code = calibrated code + k(T) from the calibration table.
     - (c) Spec §6 restates the guaranteed no-trip band as "below the calibrated effective threshold minus the corner-dependent margin". The simulated margin table stays until silicon characterisation replaces it.
2. **The trip path with the real oscillator works.** The transistor-level R0.95 CPEX clocks the RTL at 9.4415 MHz. The c_mid decision comes 43 ns earlier than with the ideal clock (1.121 vs 1.164 µs), from the oscillator's own phase at the fault, and `GATE` < 1 V is 1.500 µs.
3. **Supply extremes do not move the decision** (1.1637–1.1639 µs). `GATE` < 1 V is 1.547 µs at 1.08/3.0 V and 1.543 µs at 1.32/3.6 V; the pad fall scales with IOVDD.
4. **Power-up at the corners** reproduces the spurious-latch window with the real EN pad and the map-1.2 RTL. `GATE` never rises (≤ 36 µV), and gB/gB_pd pass at ss 125 °C and ff −40 °C. The ff −40 °C cases need a 2 ns step (20 ns fails on BGR HBTs).
5. **The re-arm slows at ss 125 °C**: `GATE` 90 % 0.958 µs after EN (tt 0.678 µs, ff −40 °C 0.514 µs).

## Not run / not run to completion

| Item | Status |
|---|---|
| c_mid ff −40 °C at 1.05× | not run to completion (disk quota at 27.84 µs) |
| first soft-cal launch (`r3x`), 150→94 and 134→118 | not run to completion (disk quota at 24 µs); replaced by `r3x2` |
| gB/gB_pd ff −40 °C at 20 ns | failed (numerical); 2 ns rows passed |
| supply extremes at ss/ff; near threshold at supply extremes | not run |
| real oscillator at ss/ff (trip path) | not run |
| calibration rehearsal at ss/ff (the k(T) table from simulation beyond the three near-threshold corners) | not run |
| stock pads (with `dantenna`) at these corners | not run (all stock-pad runs failed or stalled on this deck, see the r3full record) |
| series R of the interconnect, bondpad and fill C | not run |

## Commands (repository root, `BULK` set; `W=designs/g1-guardian/blocks/g1_top/sim`)

```
C="--cdl /work/designs/g1-guardian/blocks/g1_padring/netlist/g1_chip_top_1414_r3.cdl \
   --cdl-sha256 5e47ae022ab73b4e060afaee22a1299bc62e1a895f4c9e15f865820505d52629 --rtl-dir eco_20260925 \
   --netlist pex --method gear --interconnect extracted --timeout 24800 --run-id r3x"
flow/launch_pinned.sh <cpu> $W 25200 <log> python3 run_top_cdl.py gB --por-pin --corner ss --temp 125 $C
flow/launch_pinned.sh <cpu> $W 25200 <log> python3 run_top_cdl.py gB --por-pin --corner ff --temp -40 --maxstep-ns 2 $C
flow/launch_pinned.sh <cpu> $W 25200 <log> python3 run_top_cdl.py {f_mid|b_s|hard_pulse} --corner {ss --temp 125|ff --temp -40} --maxstep-ns 1 $C
flow/launch_pinned.sh <cpu> $W 25200 <log> python3 run_top_cdl.py {q|c_mid --timeline compact} --vdd 1.08 --vdda 3.0 --maxstep-ns 1 $C
flow/launch_pinned.sh <cpu> $W 25200 <log> python3 run_top_cdl.py c_mid --timeline compact --fault-mult 1.15 --corner ff --temp -40 --maxstep-ns 1 $C
flow/launch_pinned.sh <cpu> $W 25200 <log> python3 run_top_cdl.py c_mid --timeline compact --osc tl --maxstep-ns 1 $C
flow/launch_pinned.sh <cpu> $W 25200 <log> python3 run_top_cdl.py cal --cal-kind hard --cal-codes 172:154:-2 --ser-start-us 4 --maxstep-ns 1 $C
```

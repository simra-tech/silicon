# G1 first-silicon bring-up sequence (chip of record r3, register map 1.2)

This is the ordered procedure for the first packaged parts. It implements the bench plan
[`../README.md`](../README.md) on the board of [`BOARD_CHECKLIST.md`](BOARD_CHECKLIST.md), using
the host library [`g1_host.py`](g1_host.py).

**Every step is not run.** No silicon exists. "Expected" values are **simulated** unless marked
*computed*, and each one names its source. "Screen" values are **proposed bring-up screening
bands**, an engineering assumption chosen here. They are not specification limits. A part outside
a screen is **flagged and kept**, not discarded, and the run is recorded as it happened (bench plan:
keep aborted and out-of-range runs). The specification limits that do apply are called out
explicitly (spec §4, §6).

Before every step, record the sample ID, run ID, board revision, instruments (model, serial,
calibration date, range, input impedance), rail voltages, ambient/case temperature, `VREF` capacitor
and host software revision (`g1_host.__version__` plus git hash). Keep the raw data.

Main sources used for the expected values:
- **[R3]** `blocks/g1_top/sim/FULLCHIP_CDL_R3_20260926.md` (r3 full-chip layout-netlist deck, `nodcn`
  pads, ideal 9.436 MHz clock, tt/27 °C unless stated)
- **[RES]** `blocks/g1_top/sim/campaigns/RESULTS_20260925.md`
- **[TRIP]** `blocks/g1_trip/sim/postlayout/README.md`
- **[BGR]** `blocks/g1_bgr/sim/system_checks_20260924/RESULTS.md`
- **[SPEC]** `specification/G1_TOP_LEVEL_SPECIFICATION.md`
- **[MAP]** `specification/G1_REGISTER_MAP.md`

## S0. Fixture qualification (no DUT)

| Action | Expected | Accept | Record |
| --- | --- | --- | --- |
| With an empty socket, exercise the independent load-bus inhibit. Inject a bounded fault from the fault source into the Kelvin pins. Remove control power | inhibit opens and closes on command; removing control power leaves it asserted | cut-off delay and delivered energy measured and below the fixture's declared limits; sense-pin overshoot ≤ 50 mV at the 2 A ceiling (feasibility envelope) | inhibit timing, pin-level overshoot, source compliance transients |
| Check the host adapter with a scope on the empty socket: read frame = 24 contiguous SCLK, write = 16, SCLK idles low, idle before each frame ≥ 25 µs | as specified in [MAP] §1 | no SCLK-low stall > 2 µs inside a frame | scope capture |

## S1. Unpowered continuity and leakage, per pin (pad level)

Put all supplies at 0 V and connect them to ground through the supply outputs (disabled but
connected). Use an SMU on one lead at a time with every other lead grounded. Force the currents
listed below with ±1.0 V compliance. For `G_SHARED` (lead 24) use ±10 µA with ±0.8 V compliance.

| Action | Expected | Screen | Record |
| --- | --- | --- | --- |
| Signal and analog leads (8–24): force −100 µA (diode to `IOVSS`/`VSS`) and +100 µA (diode to the grounded `IOVDD`) | diode-like forward drop both ways (ESD diodes of every `sg13g2_io` pad). Typical silicon junction about 0.5–0.8 V. **Not simulated** for these pads | forward drop within ±100 mV of the lot median; \|V\| at compliance = open bond; \|V\| < 0.1 V = short | V at ±100 µA per lead, per sample |
| Same leads at +0.2 V and −0.2 V (below diode turn-on): leakage | nA range or less (the pad diodes set the floor for S12) | flag anything above 100 nA (*proposed*) | I per lead, settling time |
| Supply leads 1 (`VDD`), 3 (`IOVDD`), 7 (`VDDA`) vs ground: force +10 µA and −10 µA with ±0.5 V compliance | power-clamp/diode behaviour; not simulated | no short (\|V\| > 0.1 V) | V, I |
| Ground leads 2, 4, 5, 6 vs paddle, 4-wire | low-ohmic after board tie (B7) | < 1 Ω (*proposed*) | R |
| Adjacent-lead check between `SENSE_P`/`SENSE_N` (8/9) and `GATE`/`FAULT_N`/`EN` (10–12) | isolation through the pad diodes only | no short | V |

Stop if any short or open is found. The part stays unpowered and is recorded as failed continuity.

## S2. Power-up in the required order, inhibit asserted (P1, P2, P4, P6)

Assert the inhibit first. Hold `EN` low from the buffer. Connect the FET but leave the load bus
de-energized. Capture `VDD`, `IOVDD`, `EN` and `GATE` on a scope.

| Action | Expected (simulated) | Accept | Record |
| --- | --- | --- | --- |
| Ramp `VDD` 1.2 V, then `IOVDD`/`VDDA` 3.3 V (< 100 µs ramp) | `GATE` ≤ 31 µV while `EN` low [R3 gB, gB_pd], ≤ 72.5 mV with stock pad models [RES §5]. The G1_GATE `tripped` latch may toggle while `IOVDD` < 1.1 V (spurious-latch window, invisible at `GATE`) [R3] | `GATE` < 0.5 V throughout (*proposed*, below FET threshold) | both ramps, `VDD`→`IOVDD` delay, `GATE` max |
| Supply currents with `EN` low, rails stable | not simulated as a separate state | none; record only | I(`VDD`), I(`VDDA`), I(`IOVDD`) |
| Wait the `VREF` settling delay with `EN` low | 10 nF: 1 % in 1.20–1.32 ms [BGR]; use ≥ 2 ms (P4) | — | delay used |

IO-first order is a known unsafe condition (`GATE` 3.300 V for 4.34 µs, [R3] gA). It is **not**
performed on first parts.

## S3. Identify (map 1.2)

`G1.enable(vref_cap_nF=10)` raises `EN` and waits ≥ 128 osc cycles. Then run `G1.identify()` and
`G1.dump()`.

| Action | Expected | Accept | Record |
| --- | --- | --- | --- |
| Read `CHIP_ID` (0x00) and `VERSION` (0x01) | 0x47, **0x12** (r3). 0x11 means an r2/r1 die with map 1.1 | exact. 0x11: stop and record the die as r2, then rerun with the map-1.1 host rules. Anything else: check wiring and idle timing | both bytes, 10 repeats |
| Dump all readable registers | reset table of [MAP] §4 (`DAC_SOFT` 0x99, `DAC_HARD` 0xFE, `SOFT_TIME` 0x0027, `HARD_N` 0x04, `INRUSH` 0x02, `MODE` 0x03, `OSC_CTRL` 0x18, `TEMP_CTRL` 0x01, `SEU_CTRL` 0x01, `STATUS` 0x80 after the inrush window, `DAC_*_EFF` 0x99/0xFE) | exact match | full dump |
| Write/read-back pattern test on every RW register (0x00, 0xFF, 0x55, 0xAA masked to the defined bits; `SOFT_TIME` via H then L). Then `safe_defaults()` | reserved bits read 0, `OSC_CTRL` bit 4 reads 1; no mismatches | 0 mismatches over ≥ 1000 frames | mismatch count, SCLK frequency |

## S4. Oscillator alive and trimmed

| Action | Expected (simulated) | Screen | Record |
| --- | --- | --- | --- |
| Read `OSC_CNT` twice about 50 ms apart (`measure_fosc`) | increments every 256 osc cycles (25.6 µs at 10 MHz); f<sub>OSC</sub> 9.436 MHz at trim 8, tt/27 °C (loaded; transistor-level run 9.4416 MHz [R3] osc); corner span 7.61–12.43 MHz [RES §6] | 7.0–13.0 MHz | f, host interval |
| Trim sweep 0..15 (`trim_osc(10e6)`) | monotonic, higher code = slower, about 2.7 %/LSB; 10 MHz reachable at every simulated PVT (slow/hot code 0 10.447 MHz) | monotonic; one code within ±1.5 % of 10 MHz | f per code, chosen code |
| `watchdog(duration_s=10)` | CHIP_ID constant; OSC_CNT advancing | no failure | f estimate |

## S5. `VREF` pin voltage (lead 13)

| Action | Expected (simulated) | Screen | Record |
| --- | --- | --- | --- |
| DMM in high-Z (≥ 10 GΩ) mode, armed defaults, `TEMP_OUT` on | 1.04501 V on the r3 chip deck [R3] QUIET; BGR586 pin open 1.04546 V tt/27 °C, corners 1.0418–1.0493 V [BGR]; the T2F load lowers it by 0.47 mV [SPEC §4] | 1.024–1.066 V (±2 %) | V, meter model/mode |
| Repeat with a 10 MΩ meter | about −2.3 mV (*computed*: V<sub>REF</sub> × 22.3 kΩ / 10 MΩ, not a pad simulation) | shift 1–4 mV | ΔV (gives R<sub>out</sub>) |

The on-chip `VREF` node carries 32–46 mV p-p clock spikes (simulated). With 10 nF they do not
reach the pin, so a pin measurement does not show them. `VREF` scales every threshold (LSB =
V<sub>REF</sub>/5300). Record V<sub>REF</sub> for use in `G1(vref_V=...)`.

## S6. Quiescent currents (armed defaults, no load current, 3.3 V/1.2 V nominal)

| Action | Expected (simulated) | Screen | Record |
| --- | --- | --- | --- |
| I(`VDDA`), T2F on (reset default) | 1462.5 µA [R3] q, tt/27 °C (includes SENSE/TRIP biased at 1 A load); hand-wired netlists 1421 µA; ss/125 °C 1727.9 µA, ff/−40 °C 1279.4 µA; BGR586 alone 319.7 µA | 1.0–2.2 mA | I, T |
| I(`VDDA`), `TEMP_CTRL` = 0 | 1454.5 µA (8 µA lower) [R3] | ΔI 0–30 µA | I |
| I(`IOVDD`) | 96–128 µA with `TEMP_OUT` toggling into 20 pF, about 0 (0.002 µA) with T2F off and static outputs [R3] | T2F off: < 10 µA | I with and without the counter connected |
| I(`VDD`) | oscillator 114.9 µA, 122 µA total on `VDD` in the transistor-level osc run [R3]. **The digital macro's current was not simulated** (RTL co-simulation) | none; record | I with `SEU_CTRL` pattern checkerboard (every SEU flop toggles) and all-zeros |
| Total power | spec target < 10 mW (declared state) | < 10 mW | sum of V × I |

## S7. `TEMP_OUT` frequency (lead 14)

`t2f_read("ptat", gate_time=1.0, counter=...)`, then `"ref"`. Use a reciprocal counter, DC coupled,
triggering near 1.65 V, with ≤ 20 pF load.

| Action | Expected (simulated) | Screen | Record |
| --- | --- | --- | --- |
| PTAT mode at room temperature | 1.518 MHz at 27 °C (chip netlists, tt); block 1.5074 MHz at 25 °C, slope 4.909 kHz/°C (BGR586, typical) [SPEC §4] | ±15 % of the value at the measured temperature (historical process spread, **not** re-established with BGR586) | f, reference-thermometer T, case T |
| REF mode | about 1.6 MHz ([`g1_t2f/INTERFACE.md`](../../blocks/g1_t2f/INTERFACE.md); not re-established with BGR586) | record | f, ratio PTAT/REF |
| Two-point calibration at 25/100 °C, verification at −40…125 °C | ±2 °C after calibration (237/300 completed MC samples, typical process; 63 not run to completion) | ±2 °C (spec target) | per bench plan "Temperature" section |

## S8. Serial/SEU monitor readout (baseline)

| Action | Expected | Accept | Record |
| --- | --- | --- | --- |
| `seu_readout()` after the EN rise | `SEU_STATUS.ACTIVE` = 1 after the 256-clock fill; `plain`/`corr`/`unc`/`run` = 0 | counters 0 at start | readout |
| `seu_self_test()` (`INJ_PLAIN`, `INJ_TMR`) | `SEU_PLAIN` +1, `SEU_CORR` +1, `SEU_UNC` unchanged ([MAP] §6, RTL-simulated) | exact | before/after |
| 10-minute soak, each pattern (checkerboard, all-0, all-1) | 0 at ground level expected; not a guarantee | record | counts, time, T |

## S9. Calibration of the soft and hard thresholds (inhibit asserted)

This follows the calibration contract (spec §6). The load bus is inhibited. A traceable source
applies **25.00 mV** at the Kelvin pins (verify with the DMM across `SENSE_P`–`SENSE_N`).
`SENSE_OFS` = 0, hysteresis off, trip paths disabled during the sweep. The sweep runs downward from
255 in 4-code steps and then 1-code steps, with 200 µs settling and 16 `STATUS2` reads per code. It
confirms two codes below and repeats upward. `calibrate_soft(25.0)` and `calibrate_hard(25.0)` do
this, and `compute_calibration()` follows. Repeat each 3×.

| Action | Expected (simulated) | Accept | Record |
| --- | --- | --- | --- |
| Soft crossing | Cideal = 25/0.19623 = 127.4 at V<sub>REF</sub> 1.04 V (126.7 with the measured 1.0455 V). NF4 soft comparator within 0–1 LSB of its code [TRIP], so the highest code reading high is about 127 plus the sense-amplifier offset / 0.196 mV. Full-chip rehearsal at tt (1 A, r3 deck): 130 silent, 128 fires [R3X] | bracketed to 1 code, monotonic, repeats within ±1 code (*proposed*) | full sweep (code, fraction high), both directions |
| `SENSE_OFS` = round(Ccross − Cideal) | the part's sense offset in LSB (standalone R100 MC: ≤ 0.5 mV residual after an ideal correction; joint chip MC not run) | −128…127, and no target in S10 clips (spec §6: clipping = calibration failure) | value |
| Hard crossing | the effective hard threshold is about 45 LSB **below** the code (40–56 over tt/ss/ff on the block bench, 41–47 on the chip netlists at tt/27 °C [TRIP], [SPEC §4]). So the highest high code is about Cideal + 45 = **172**, range 167–183. Full-chip rehearsal at tt: 172 silent, 170 fires, 41–43 codes above the soft crossing [R3X] | bracketed, monotonic, repeats within ±1 code (*proposed*); outside 167–183: flag | full sweep, both directions |
| `hard_extra` = hard correction − `SENSE_OFS` | about +45 (applied via `DAC_HARD`, because one `SENSE_OFS` cannot correct both comparators) | the target code + extra + `SENSE_OFS` ≤ 255 | value |
| Uncalibrated witness: `DAC_HARD` 200, soft path off, step 28.75 mV and 31.25 mV | no trip at 28.75 mV; hard trip at 31.25 mV (1.25× nominal, inside the uncalibrated no-trip region: documented kick offset, calibration requirement) [R3] | record | trip/no-trip |

| Hard crossing vs temperature (−40 / 25 / 125 °C, inhibit asserted, same sweep) | the hard offset is temperature-dependent: simulated effective threshold at code 200 is 8.0–9.3 mV below the code at tt/27 °C and ss/125 °C and **10.4–11.6 mV** at ff/−40 °C (r3 full-chip deck, [R3X]); joint MC: room calibration drifts > 0.5 mV of shunt at 125 °C in 4 of 20 seeds [JMC] | bracketed at each temperature | table code(T), the input to k(T) (H6) |

Freeze the room-temperature calibration per sample, then build the per-part hard-code correction
table k(T) from the three temperatures above. The host applies **hard code = calibrated code + k(T)**
from the on-chip T2F reading (spec §6 H6); the soft path needs no temperature correction in
simulation. Acceptance at each temperature (S10) uses the k(T)-corrected code; the ±0.5 mV hard
accuracy statement holds at the calibration temperature only until this table exists (spec §6).

[R3X] `../../blocks/g1_top/sim/FULLCHIP_CDL_R3_CORNERS_20260927.md` (simulated).
[JMC] `../../blocks/g1_trip/sim/qualification/joint_r3_mc_20260926/RESULTS.md` (simulated).

## S10. Threshold verification with frozen calibration

Use `arm(hard_mV=35, soft_mV=30, soft_time_ms=1)`. The hard target must be ≤ 39 mV so that the
search range stays ≤ 255; the usable hard range is about 25–40 mV. Test each path with the other
disabled, outside the inrush window, with the inhibit released onto the resistive load or with the
source at the Kelvin pins.

| Action | Expected | Accept (spec §6) | Record |
| --- | --- | --- | --- |
| `kelvin_check()` with 1 A flowing (P9) | `CMP_SOFT` = 1 at `DAC_SOFT` 5 | pass, otherwise stop (possible open `SENSE_N`) | fraction |
| Soft: hold 0.9T (27 mV) for ≥ 3 windows; hold 1.1T (33 mV) | no trip; trip after the configured window (cause soft) | no trip ≤ 0.9T; trip ≥ 1.1T after the window | outcome, time to trip, `SOFT_PEAK` |
| Hard: 0.9T (31.5 mV) and 1.1T (38.5 mV) persistent | no trip; hard trip | same | outcome, time |
| Band between 0.9T and 1.1T | characterization only | none | crossing |

## S11. Breaker demonstration, low-energy source (feasibility envelope)

Conditions: 5 V resistive current-limited load, 25 mΩ shunt, 1 A nominal. `FAST_EN` = 0, hysteresis
off, codes static while energized. The hard target is calibrated at 35–39 mV and the soft target at
30 mV. The fault is a **1.8 A / 45 mV** step (≥ 1.1 × 39 mV), with ≤ 50 mV at the pins including
overshoot. Capture shunt differential, `GATE`, FET V<sub>GS</sub>/V<sub>DS</sub>, load current,
`FAULT_N` and `EN` with declared probe skew.

| Action | Expected (simulated) | Accept | Record |
| --- | --- | --- | --- |
| Nominal 1 A for ≥ 1 s | no trip (`GATE` min 3.298 V, [R3] q) | no trip | `status()` |
| 45 mV step, persistent | trip decision 1.164 µs, `tripped` 1.167 µs, **`GATE` < 1 V at 1.543 µs** (tt/27 °C), 1.433 µs ff/−40 °C, 1.726 µs ss/125 °C; cause hard [R3] c_mid. That run used code 200 uncalibrated, 5 nF + 10 Ω and an ideal clock | `GATE` < 1 V and staying below within **< 10 µs** (spec target); `STATUS` cause = hard, `TRIP_CNT` +1, `FAULT_N` low | event-to-`GATE`<1 V, time to 1 % load current, peak V<sub>DS</sub>, energy |
| 45 mV for 200 ns (short pulse), `HARD_N` 4 | no trip (`tripped` max 49 mV, [R3] hard_pulse) | no trip | outcome |
| Soft window: 1.5× nominal (37.5 mV) held, `SOFT_TIME` = 1, **hard path disabled** (`MODE` = `SOFT_EN`), because 37.5 mV is above a 35 mV hard target | soft trip 27.75 µs after the step, `GATE` < 1 V 28.13 µs ([R3] b_s; 256 samples = 27.13 µs + decision) | cause soft, time = window ± 1 sample period at the measured f<sub>OSC</sub> | time |
| Re-arm, **inhibit reasserted first**: (a) `CTRL.CLEAR`; (b) `EN` low ≥ 2 µs, reprogram and read back, `kelvin_check`, release | (b) `GATE` back to 90 % 0.678 µs after `EN` high, 1 A restored ([R3] f_mid); `EN` low clears both latches | trip cleared, configuration verified before release | sequence, `GATE` rise |

Inductive loads, `FAST_EN` = 1, retrigger mode and a fault present at `EN` rise (P7 inrush
window, about 0.11 ms) are separate, later steps. Each needs its own declared envelope.

## S12. Device coupons and DUT HBT, within the rails

Set `TEMP_CTRL` = 0 (T2F off) for low-current work. Keep 3.3 V up and every device pin
≥ −0.3 V. Measure the fixture-open, short and pad-reference controls first, at the same range and
settling.

| Action | Expected (simulated) | Limits | Record |
| --- | --- | --- | --- |
| HBT (leads 19–21) forward Gummel, V<sub>CB</sub> = 0, V<sub>BE</sub> 0.30–1.00 V | V<sub>BE</sub> 665.4 mV at 1 µA and 726.6 mV at 10 µA; β 678 at 1 µA and 754 at 10 µA (`npn13G2`, typ, 27 °C; corners −6/+8 mV, β ×1.8/×0.57) ([`g1_dut/README.md`](../../blocks/g1_dut/README.md)). The pad leakage floor limits the low-V<sub>BE</sub> end | I<sub>C</sub> compliance 1 mA (*proposed*) | I<sub>C</sub>, I<sub>B</sub> vs V<sub>BE</sub>, T |
| HBT output curves, I<sub>B</sub> 1–8 µA | per model card | **V<sub>CE</sub> ≤ 1.6 V** | I<sub>C</sub>(V<sub>CE</sub>) |
| DOSE pair I<sub>D</sub>–V<sub>G</sub>: `G_SHARED` 0 → 1.2 V at V<sub>D</sub> = 0.05 V and 1.0 V, LV (`D_STD`) and HV (`D_ELT`) separately | no committed simulated curve for the assembled pair; compare LV and HV | **`G_SHARED` ≤ 1.32 V**; drains ≤ 1.2 V (*proposed*); compliance 100 µA | raw currents before any subtraction, noise floor |

## S13. SEU register readout and final state

| Action | Expected | Accept | Record |
| --- | --- | --- | --- |
| `status()` and `seu_readout()` at the end of the session; `check_config()` against the snapshot | counters as S8 plus any self-test injections; no configuration change | no unexplained change | readout |
| Shutdown: assert inhibit, `EN` low, 3.3 V off, then 1.2 V off | `GATE` stays low | `GATE` < 0.5 V | scope capture |

## Status

| Step | Status |
| --- | --- |
| S0–S13 | not run (no silicon, no board) |
| `g1_host.py` against `DummyTransport` | passed: 29/29 unit tests (`python3 -m unittest -v test_g1_host`, Python 3.6.8). This tests host logic only, not hardware |
| `g1_host.py` hardware transports (FTDI, spidev) | not run (stubs) |

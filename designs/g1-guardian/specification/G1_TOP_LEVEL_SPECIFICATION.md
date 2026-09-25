# G1 Radiation-Aware Node Guardian — Top-Level Specification & Architecture Record

## 1. Overview and intent

G1 is a mixed-signal test chip on the IHP SG13G2 0.13 µm SiGe BiCMOS open PDK.
It sits between a power rail and a commercial compute load and does four things:
disconnects an external FET on a programmed overcurrent signature while letting ordinary
load steps through; measures its own temperature with an HBT-based sensor;
provides transistor-leakage coupons for dose characterization; and counts
upsets in a scrubbed register. Telemetry and settings go over a three-wire
serial interface.

Design principles:

- **Device implementation:** the bandgap and temperature sensor use
  `npn13G2`; the SENSE revision-B input pairs are thick-oxide PMOS.
  Digital and switching functions use CMOS.
- **Board-measurable:** every signal is DC or below 10 MHz. The die is packaged
  in QFN24 and measured in a socket. No RF pads.
- **Device characterization:** the assembled NMOS coupons are standard LV
  and HV PCells with shared gate; a separate HBT exposes base current.
  No dose calibration or radiation qualification has been measured. The
  experimental enclosed-layout device is absent from the assembled chip.
- **Direct device access:** one HBT and the canary transistors are pinned out
  so the physics can be measured without the on-chip readout.
- **Area:** 1.414 × 1.414 mm die including sealring and IO ring (chip of record, owner decision 2026-09-24; it supersedes the 1.35 mm LibreLane assembly). The 1 × 1 mm allocation was withdrawn on 2026-09-18 because the IO cells need an external bondpad and sealring clearance (`PLAN.md` D10); 1.2 mm was withdrawn on 2026-09-19 when the laid-out macros exceeded its core window (D13).

## 2. Block breakdown

| Block | Function | Devices | Interfaces |
| --- | --- | --- | --- |
| `G1_SENSE` | Low-side Kelvin shunt amplifier. Differential input 0 to 50 mV across an external shunt, gain 20, bandwidth ≥ 2 MHz, input-referred offset target < 0.5 mV after trim. Common-mode −0.1 to +0.3 V. Difference amplifier around a 3.3 V PMOS-input OTA with a V<sub>REF</sub>-derived output pedestal (`PLAN.md` D1). | thick-oxide PMOS input pair, thick-oxide MOS, `rppd` | in: `SENSE_P`, `SENSE_N`; out: internal `ISENSE` (pedestal + 20 × V<sub>shunt</sub>) |
| `G1_TRIP` | Two clocked comparators on `ISENSE`: (a) hard threshold, trips after N consecutive samples above it (blanking); (b) soft threshold, trips when an up/down sample counter reaches the programmed trip-off window (`PLAN.md` D3). Thresholds are 8-bit codes of V<sub>REF</sub>-referenced resistor-string DACs; hysteresis and all windows programmable. | 1.2 V StrongARM comparators with SR latches, two 8-bit `rppd` string DACs, digital timers in `G1_CTRL` | in: `ISENSE`, `TRIP_SET`, registers; out: `cmp_soft`, `cmp_hard` to `G1_CTRL` |
| `G1_GATE` | Drives an external low-side logic-level N-FET. On `TRIP`: gate low within the response target, then latched off or retriggered after a programmable hold. Enable input. | `sg13g2_IOPadOut30mA`, LV/HV level shift | out: `GATE`, `FAULT_N`; in: `EN` |
| `G1_BGR` | Op-amp-less, self-biased cascoded HBT bandgap in the 3.3 V domain (chip variant `bgr_loop24_qref4_r253p465_hv06`, "BGR586": 336 HV MOS, 301 `npn13G2`, 399 resistors), in which the PTAT/bias loop is built from 24 parallel original units (feedback resistors scaled to R/24, XR17–22 at 53.465 µm to centre the nominal TC) and the V<sub>REF</sub> (Qref) branch from 4 units, to average HBT and resistor mismatch (`../blocks/g1_bgr/sim/qualification/BGR_REMEDY_REVIEW_20260922.md`). Simulated, tt/27 °C: V<sub>REF</sub> 1.04546 V, I<sub>PTAT</sub> 4.13 µA, nominal TC 8.53 ppm/°C over −40…125 °C, supply current 319.7 µA, output resistance 22.3 kΩ (`../blocks/g1_bgr/sim/postlayout/README_bgr586_pex.md`). | `npn13G2`, thick-oxide MOS, `rppd`, `rhigh` | out: `VREF`, internal `IPTAT`, `VBE`, `dVBE` |
| `G1_T2F` | HBTs at a 1:8 current ratio; ΔV<sub>BE</sub> converted to a PTAT current that charges a `cmim` relaxation oscillator against a V<sub>REF</sub>-derived threshold, so frequency is linear in T (`PLAN.md` D2); register-selectable reference mode runs the same oscillator from V<sub>REF</sub>/R so the ratio cancels C and thresholds. About 1.6 MHz at 27 °C (simulated). | `npn13G2`, thick-oxide MOS, `rppd`, `cmim`, LV CMOS output | out: `TEMP_OUT`; mode bits from registers |
| `G1_DOSE` | Two NMOS canaries with a shared gate and both drains pinned out: a thin-oxide `sg13_lv_nmos` beside a thick-oxide `sg13_hv_nmos`. `D_ELT` is a legacy pin name for the HV drain; experimental ELT geometry is excluded. No on-chip readout in run 1. | `sg13_lv_nmos`, `sg13_hv_nmos` | pins: `G_SHARED`, `D_STD`, `D_ELT` |
| `G1_SEU` | Plain shift register and per-stage-voted TMR register (depth parameterised, 256 + 3 × 128 bits in the assembled macro), continuously shifted and scrubbed against a selectable pattern (checkerboard, all-0, all-1; constant patterns give the static-data case); TMR-protected counters for plain errors, TMR corrected events and TMR uncorrectable errors. | LV CMOS standard cells | registers |
| `G1_CTRL` | Register file, three-wire serial (mode-0 SPI-like, 7-bit address + R/W bit, 8-bit data, 24-clock read frame), trip timers, scrub state machine, event counters; full map in `G1_REGISTER_MAP.md`. | LV CMOS standard cells | `SCLK`, `SDI`, `SDO` |
| `G1_DUT` | One `npn13G2` HBT, all three terminals on analog pads, substrate to `VSS`. | `npn13G2` | `HBT_E`, `HBT_B`, `HBT_C` |

## 3. Pin map (24)

| # | Pin | IO cell | Domain | Function |
| ---: | --- | --- | --- | --- |
| 1 | `VDD` | `sg13g2_IOPadVdd` | 1.2 V | core supply |
| 2 | `VSS` | `sg13g2_IOPadVss` | 0 V | core ground, substrate |
| 3 | `IOVDD` | `sg13g2_IOPadIOVdd` | 3.3 V | IO and analog supply |
| 4 | `IOVSS` | `sg13g2_IOPadIOVss` | 0 V | IO ground |
| 5 | `VSS` | `sg13g2_IOPadVss` | 0 V | second ground pad |
| 6 | `IOVSS` | `sg13g2_IOPadIOVss` | 0 V | second IO ground pad |
| 7 | `VDDA` | `sg13g2_IOPadAnalog` (bare terminal) | 3.3 V | analog supply for the 3.3 V core blocks (bandgap, sensor, sense amplifier, comparator DACs, gate latch; G1_OSC uses 1.2 V VDD); tied to the same 3.3 V rail as `IOVDD` on the board (`PLAN.md` D14) |
| 8 | `SENSE_P` | `sg13g2_IOPadAnalog` | analog | shunt Kelvin, positive |
| 9 | `SENSE_N` | `sg13g2_IOPadAnalog` | analog | shunt Kelvin, negative |
| 10 | `GATE` | `sg13g2_IOPadOut30mA` | 3.3 V | external N-FET gate |
| 11 | `FAULT_N` | `sg13g2_IOPadOut4mA` | 3.3 V | low while tripped |
| 12 | `EN` | `sg13g2_IOPadIn` | 3.3 V | enable / reset of trip latch |
| 13 | `TRIP_SET` | `sg13g2_IOPadAnalog` | analog | external hard-threshold override, optional |
| 14 | `SCLK` | `sg13g2_IOPadIn` | 3.3 V | serial clock |
| 15 | `SDI` | `sg13g2_IOPadIn` | 3.3 V | serial data in |
| 16 | `SDO` | `sg13g2_IOPadOut4mA` | 3.3 V | serial data out |
| 17 | `TEMP_OUT` | `sg13g2_IOPadOut16mA` | 3.3 V | temperature as frequency |
| 18 | `VREF` | `sg13g2_IOPadAnalog` | analog | bandgap output, for test |
| 19 | `G_SHARED` | `sg13g2_IOPadAnalog` | analog | canary pair gate |
| 20 | `D_STD` | `sg13g2_IOPadAnalog` | analog | standard NMOS drain |
| 21 | `D_ELT` | `sg13g2_IOPadAnalog` | analog | HV NMOS drain in the assembled chip; legacy pin name |
| 22 | `HBT_E` | `sg13g2_IOPadAnalog` | analog | test HBT emitter |
| 23 | `HBT_B` | `sg13g2_IOPadAnalog` | analog | test HBT base |
| 24 | `HBT_C` | `sg13g2_IOPadAnalog` | analog | test HBT collector |

Side assignment: pins 1 to 6 south, 7 to 12 east, 13 to 18 north, 19 to 24
west, so that the analog device pins sit together on one side away from the
switching outputs, and the supplies are split between two sides.

The 3.3 V analog blocks are supplied from `VDDA`, not from the ring's `IOVDD`: the `sg13g2_io` cells give no DRC-legal way to tap their `iovdd` rail into the core (the rail sits behind `vdd`/`vss` on every metal level), so `VDDA` enters through the bare terminal of an analog pad and is strapped to the macros inside the core. Analog ground shares the core `VSS` grid. `VDDA` must not exceed `IOVDD` by more than a diode drop, which the shared board rail guarantees.

Analog pads carry the IO cell's ESD diodes to `IOVDD`/`IOVSS`. Their leakage
bounds the lowest usable current on the device pins; the measurement plan keeps
device currents in the nanoampere-to-microampere range for that reason.

## 4. Parameter classification

| Parameter | Value / range | Status | Basis |
| --- | --- | :---: | --- |
| Process | IHP SG13G2 0.13 µm SiGe BiCMOS, open PDK | Specified | PDK |
| HBT primitive | `npn13G2` | Specified | PDK model library |
| Core supply | 1.2 V (1.08 to 1.32) on one `VDD` pad | Specified | PDK |
| Analog supply | 3.3 V (3.0 to 3.6) on `VDDA`, tied to the `IOVDD` rail on the board. Current of the chip-of-record 3.3 V blocks: BGR586 alone 319.7 µA (simulated, tt/27 °C); chip 3.3 V analog sum (BGR586 + SENSE + TRIP, armed, 1 A load) 1421 µA at tt/27 °C, 957 µA (ss/−40 °C) to 2188 µA (ff/125 °C), 1415/1427 µA at 3.0/3.6 V (simulated, `g1_top --blockset c1414`, BGR586 schematic view (its extraction is DC-identical), [RESULTS_20260925](../blocks/g1_top/sim/campaigns/RESULTS_20260925.md)). Digital and IO rail currents are not in this sum. The earlier 1.5 mA sum used the Sep-19 bandgap (22 µA) | Specified | block READMEs; D14; `../blocks/g1_bgr/sim/postlayout/README_bgr586_pex.md` |
| IO / analog supply | 3.3 V (3.0 to 3.6) | Specified | `sg13g2_io` |
| Die | 1414 × 1414 µm incl. sealring (`g1_chip_top_1414.gds`, `629d303a…`) | Specified | owner decision 2026-09-24; `../blocks/g1_padring/reports/signoff-1414-20260924/README.md`; QFN24 accepts up to 2 × 2 mm |
| Package | QFN24, 4 × 4 mm, 0.5 mm pitch, 200 µm die | Specified | packaging offer |
| Shunt sense range | 0 to 50 mV differential, low-side; `ISENSE` = 1.0 V pedestal + 20 × V<sub>shunt</sub>, i.e. 1.0 to 2.0 V | Specified | chip variant comp45 + R100: simulated gain 19.905 to 20.050 over 100 mismatch samples (`../blocks/g1_sense/reports/R100_MC_100_20260923.md`); earlier revision 19.98 to 19.99, 3.6 to 4.8 MHz in `../blocks/g1_sense/README.md` |
| Trip response | <10 µs from a persistent hard fault outside the guard band to `GATE` <1.0 V; only after arming and outside the inrush mask, for declared settings/clock/load | Specified target | `HARD_N` counts decisions every 2 oscillator cycles; default N=4. Chip netlists (`g1_top --blockset c1414`), compact 28 µs in-range fault, tt/27 °C: 1.345 µs (simulated, ideal clock at the R0.95 loaded frequency, fitted pad). tt/ss/ff × −40/27/85/125 °C and VDD/VDDA ±10 %, 1.8×/3×/4× faults: 1.306–1.361 µs in every completed cell. The clock stays ideal at 9.436 MHz and the SENSE pads have no `dantenna`. All 72 matrix cells completed (72/72, none failed) ([RESULTS_20260925](../blocks/g1_top/sim/campaigns/RESULTS_20260925.md)) |
| I²t window | 50 µs to 10 ms, programmable | Assumed | design target |
| Hard threshold | 8-bit DAC code, 0.5 to 1.0 of the sense full scale (about 25 to 50 mV of shunt drop), programmable; nominal load current is mapped to 20 to 25 mV of the 50 mV range | Specified (code range); effective threshold: simulated characterization result | `blocks/g1_trip/INTERFACE.md`; the earlier "1.5× to 8× nominal" was unreachable. **Effective hard threshold is below the code (simulated):** the TRIP NF4 block bench trips 40–56 LSB (7.9–11.0 mV of shunt) below the DAC code over tt/ss/ff at codes 200 and 254, corner spread 10–11 LSB; soft path within 1 LSB (`../blocks/g1_trip/sim/postlayout/README.md`, `results_postlayout_nf4.txt`). Chip netlists, code 200 (39.25 mV), tt/27 °C: no trip at 30.00 mV, trip at 31.25 mV ([RESULTS_20260925](../blocks/g1_top/sim/campaigns/RESULTS_20260925.md) §4). Cause: the soft comparator's reset kick lands on the shared input at the hard strobe. Consequence: hard calibration lands about 45–50 codes above nominal, and the usable hard range is about 25–40 mV of shunt. A parked 2× hold-capacitor candidate (`../blocks/g1_trip/layout/candidates/nf4_hold2x/`) halves the offset in simulation; not adopted, owner decision pending. Calibration requirement in §6; not a sign-off failure |
| `TEMP_OUT` frequency | 1.59 MHz at 25 °C (simulated, PTAT mode), 5.2 kHz/°C; 1.2 to 2.4 MHz over −40 to 175 °C; ±15 % process spread before calibration | Specified (simulated) | `blocks/g1_t2f/README.md` |
| Sensor accuracy | ±2 °C after fixed per-sample two-point calibration, −40 to 125 °C | Simulated characterization result (not a sign-off gate) | T2F baseline, typical process, 300/300 samples: linear two-point calibration 14/300 fail; frozen lookup calibration 0/300 fail (unadopted in firmware) (`../blocks/g1_t2f/sim/qualification/README.md`). Nominal and beyond-range results do not establish package-stress accuracy |
| Characterisation range | 77 K to 175 °C | Assumed | package limits, not verified |
| Sense-amp input offset | Residual <0.5 mV after calibration. Signed digital correction −128…127, ~0.196 mV/code; available range depends on threshold | Simulated characterization result (not a sign-off gate) | Chip variant R100, standalone: 100/100 samples ≤ 0.5 mV, worst 498 µV, ideal continuous correction (`../blocks/g1_sense/reports/R100_MC_100_20260923.md`). The rev-B 43/100 failures belong to the earlier block. Code 254 permits only +1 step; joint calibrated chip MC not run |
| ELT NMOS | Experimental layout excluded from assembled chip | Not applicable to assembled chip | `blocks/g1_dose/README.md`; historical `Gat.f` failure retained |
| Total power | <10 mW, sum of core, analog and IO rail input power, declared load/activity | Specified target | Full operating-state coverage not run |
| BGR temperature coefficient | ≤50 ppm/°C over −40…125 °C | Simulated characterization result (not a sign-off gate) | Chip BGR586: 299 of 300 mismatch samples completed and all ≤ 50 ppm/°C, max 46.88 ppm/°C; 1 numerical watchdog failure, no TC assigned (`../blocks/g1_bgr/sim/qualification/BGR586_SCREEN300_20260922.md`). The 54/100 failures belong to the superseded Sep-19 bandgap |
| SENSE gain / bandwidth | 20 ±0.1 / ≥2 MHz, common mode −0.1…+0.3 V | Specified target | Selected block results exist; complete corners and joint loaded PEX not run |
| OSC trim reach | 10 MHz reachable by a code 0…15 at supported PVT | Simulated characterization result (not a sign-off gate) | Chip variant R0.95: slow/hot code 0 reaches 10.445 MHz with the actual receiver (old block 9.975 MHz); loaded nominal trim 8 9.436 MHz (`../blocks/g1_osc/sim/qualification/README.md`, `fulltree_r095_load_20260924/`). Expanded mismatch and rail perturbation not run to completion |

## 5. Verification gates

Status is scoped to the recorded subset; a passed subset does not pass its
unrun extensions. Evidence index: `../review/G1_DESIGN_REVIEW.md`, block
READMEs, `../blocks/g1_padring/reports/signoff-1414-20260924/README.md` (physical checks of the chip of
record `g1_chip_top_1414.gds`, `629d303a…`) and `../blocks/g1_top/README.md` (chip-level simulation,
`--blockset c1414`). These are baseline facts, not claims that the closure campaigns have completed.
BGR TC, trimmed SENSE residual, OSC 10 MHz reach and T2F ±2 °C are simulated characterization
results (§4), not sign-off gates.

| Gate | Scope | Status / remaining coverage |
| --- | --- | --- |
| Schematic simulation | Recorded nominal block cases | passed subsets; complete corner/load matrix not run |
| Corner / mismatch | Chip-of-record block ensembles (standalone) | characterization, not a gate: SENSE R100 100/100 ≤ 0.5 mV (worst 498 µV); BGR586 299/300 completed ≤ 50 ppm/°C (max 46.88), 1 numerical failure; T2F 14/300 linear-calibration failures, 0/300 lookup; OSC R0.95 slow/hot code 0 10.445 MHz. The 43/100 SENSE and 54/100 BGR failures are historical blocks. Joint calibrated chip MC: not run |
| Temperature | Model-supported −40…125 °C | joint extracted subsets completed with linear-calibration failures; numerical failures retained; 300-sample and adverse coverage incomplete |
| Beyond-range temperature | 150/175 °C and 77 K | selected exploratory data only; qualification not applicable with nominal model extrapolation |
| RTL / functional GLS | Recorded built 256 + 3×128 configuration | functional, expanded CDC and fault-injection subsets passed; missing-clock and unprotected-configuration hazards remain; timed GLS is unqualified because timing checks are unsupported |
| Breaker co-simulation | Corrected-clock schematic cases | passed subsets; old clock-bridge timings invalid for acceptance |
| Chip-level simulation, chip netlists | `g1_top --blockset c1414`: BGR586 C-PEX or schematic, SENSE R100 partial C, TRIP NF4 C-PEX, R0.95 clock frequency, real RTL | tt/27 °C passed: 28 µs hard fault (transistor-level front end) `GATE` < 1 V 1.345 µs after the fault; with the behavioural front end, the 1 ms soft window trips at 1.059 ms and a 100 µs 1.5× pulse does not trip; core-first power-up `GATE` ≤ 0.073 V with EN low; CDL-vs-deck connectivity audit 0 unexplained differences. Corner/temperature matrix (q, c_mid, c, e20, f_mid, b_s × tt/ss/ff × −40/27/85/125 °C): 72/72 cells completed and passed, none failed (the last 12 as `_r4` re-runs, including q ss/125 °C as `q_ss_125C_r4_c1414m`). T2F at −40 °C: not run to completion (numerical, three attempts). Transistor-level OSC at ss/125 °C, `VDD` 1.08 V: not run. Supply ±10 % (c_mid, q): 12/12 passed. Hard faults: `GATE` < 1 V 1.306–1.361 µs. Stock-pad corners (`c1414k1`): 10 passed, 2 not run to completion. Both BGR586 and TRIP extractions: compact c_mid passed, full length not run to completion. Deviations: ideal clock at the tt/27 °C frequency, `--inpads nodcn` (SENSE pads without `dantenna`), BGR586 schematic view. Chip-level PEX: not run. Effective hard threshold at code 200: 30.00–31.25 mV (characterization, §4) ([RESULTS_20260925](../blocks/g1_top/sim/campaigns/RESULTS_20260925.md)) |
| Block DRC / LVS | Assembled macro versions | passed recorded checks; experimental ELT excluded |
| Block PEX | Existing capacitance extraction and selected tests | passed subsets; full wire-R, fill coupling and statistical scaling not established |
| Assembled DRC / precheck | 1414 µm chip of record | main and maximal passed, 0 markers; `--precheck_drc`: not run. 1350 µm assembly: passed (superseded) |
| Density | 1414 µm chip of record | passed, 0 markers |
| Recommended pad rules | 1414 µm chip of record | passed inside the maximal run (`Pad.*R`, `Pad.d`: 0 errors, `drc_maximal/run.log`). 1350 µm assembly failed (superseded) |
| Antenna | 1414 µm chip of record | passed, 0 markers. 1350 µm assembly failed (superseded) |
| Projected-reference LVS | 1414 µm chip, full chip, strict ports | passed: 61 684/61 684 devices, 31 173 nets, 22 pins; comparison-only reference (3 all-VDD pad dummy PMOS removed). 1350 µm core-only LVS (52 pairs): passed (superseded) |
| Canonical (unprojected) LVS | 1414 µm chip, full chip | failed: 14 stock IO/level-shifter sub-cells NoMatch, top skipped (PDK deck limitation, `PLAN.md` R13) |
| Top-cell rename identity | `g1_chip_top_1414_src.gds` → `g1_chip_top_1414.gds` | passed: 306 cells, deep XOR empty on all 73 layers. Earlier 1350 µm streamout differences are superseded |
| Power-order safety | Chip netlists: core-first, EN low, with and without 10 kΩ `GATE` pull-down; IO-first | core-first passed (`GATE` ≤ 0.073 V, 0.009 V with pull-down; ≤ 0.014 V at ss/125 °C and ff/−40 °C with `--pads nodcn`). IO-first on the chip netlists (`--pads nodcn`, tt/27, ss/125, ff/−40 °C) **failed** as a safety condition, as expected: `GATE` 3.28–3.30 V for 4.2–4.4 µs until `VDD` is up, with or without 10 kΩ ([RESULTS_20260925](../blocks/g1_top/sim/campaigns/RESULTS_20260925.md) §5); P1 excludes this order. IO-only drives `GATE` to 3.288 V (block power screen, simulated): board constraints in §6 |
| Digital timing | run7 macro and routed chip signal netlist, merged chip SDC, 3 corners, nominal RC | setup/hold passed; annotation, max-slew and max-fanout items failed and dispositioned, not waived; timing of the final GDS not run |
| Full-chip PEX | 1414 µm chip | not run |
| Physical measurement / irradiation | No fabricated samples | not run |

## 6. Acceptance and calibration contract

The breaker disconnects an external switch; analog constant-current regulation
is not implemented. The soft path accumulates time above threshold minus
programmable decay, not a measurement of the integral of current squared.

Use `G1_REGISTER_MAP.md` for timer units: hard decisions every 2/fOSC;
soft accumulation every 1/fOSC; soft window = SOFT_TIME×256/fOSC;
inrush = INRUSH×512/fOSC; hold = max(1,HOLD_TIME)×8192/fOSC.
A ±20% frequency range does not imply ±20% time: an 8–12 MHz clock gives
+25%/−16.7% time relative to 10 MHz. Wider unverified PVT extrema remain open.
The <10 µs target cannot apply to every programmable blanking/window value,
to masked faults, or to a stopped clock with FAST_EN disabled.

For closure screening, adopt ±10% total calibrated shunt-threshold error as an
**engineering acceptance assumption**, as suggested by the existing trip
interface. At a requested threshold T, stimuli ≤0.9T are the no-trip region,
and persistent stimuli ≥1.1T are the trip region. The region between is a
characterization band, not a promised exact decision. Evaluate soft and hard
paths separately with the other path disabled; a persistent soft-band stimulus
must trip only after its configured accumulation window. Characterize smaller
±0.1/0.25/0.5/1 mV offsets separately without falsely labeling every decision
inside this guard band a system failure.

Hard-path calibration must bracket the **effective** hard threshold, not the
DAC code. In simulation the hard comparator trips 7.9–11.0 mV of shunt (40–56
LSB) below its code, with a 10–11 LSB corner spread (TRIP NF4 block bench). On
the chip netlists at code 200 (39.25 mV) the trip point is 30.00–31.25 mV at tt/27 °C
([RESULTS_20260925](../blocks/g1_top/sim/campaigns/RESULTS_20260925.md) §4). Uncalibrated, the `c_mid` sweep trips at 0.80T and 0.89T,
inside the no-trip region above. Expect the calibrated hard code about 45–50
codes above the nominal one, and a usable hard range of about 25–40 mV of shunt.
The code search must extend at least 56 codes above the target. The corner
spread is larger than 2 LSB, so one room-temperature calibration does not absorb
it: verify the ±10 % guard band at each declared temperature. The soft path is
within 1 LSB. The 2× hold-capacitor candidate that would halve the offset is not
adopted (decision pending), so this contract applies to the chip of record.

GATE-low means the first downward crossing of 1.0 V that remains below 1.0 V
for the remainder of the observed tripped interval. Measure external drain
current decay and let-through energy separately. The existing fixture is a
5 nF gate with 10 Ω series resistance and a switched synthetic load. A selected
real FET model, board/package impedance and declared bus/load are required
before claiming real-load safety. Separate CSD16340Q3 model tests use explicitly
assumed 5/12 V loads; no board BOM or operating bus was selected. Selected
nominal cases complete, but the timestep-refinement ladder fails numerically
at 250 ps and does not establish convergence. The existing nominal shunt fixture is 25 mΩ at 1 A (25 mV); fault
profiles reach 3 A or 4 A (75/100 mV, above the specified 50 mV input range;
these are fault-stress fixtures, not in-range accuracy tests). The `c_mid`
fixture programs hard code 200 and applies 1.8 A/45 mV, above its 10% trip
guard band while remaining in-range. The behavioral current source has no declared
load-bus voltage. Shunt tolerance
and temperature coefficient are idealized unless explicitly swept. No physical
shunt tolerance allocation has yet been verified.

Power-up requirements (board constraints decided 2026-09-24):

| # | Requirement | Reason | Evidence / status |
| --- | --- | --- | --- |
| P1 | `VDD` (1.2 V) comes up before or together with `IOVDD` (3.3 V); during shutdown `VDD` stays until `IOVDD` is down | Every `sg13g2_io` output pad, the tri-state variants included, takes its driver gate signals from core-powered level-up cells. With `IOVDD` alone the `GATE` pad can float high | IO-only: `GATE` 3.288 V (simulated, `../blocks/g1_gate/sim/POWER_SCREEN_20260921.md`). Core-first on the chip netlists: `GATE` ≤ 0.073 V with EN low (simulated, `g1_top` gB). IO-first on the chip netlists: `GATE` 3.28–3.30 V for 4.2–4.4 µs until `VDD` is up, at three corners (simulated, `--pads nodcn`, [RESULTS_20260925](../blocks/g1_top/sim/campaigns/RESULTS_20260925.md) §5) |
| P2 | External `GATE` pull-down or independent load-bus inhibit during power-up | Holds the FET off while the rails ramp. With IO first, only the inhibit does: a 10 kΩ pull-down does not | Core-first with 10 kΩ: `GATE` ≤ 0.009 V (simulated, `g1_top` gB_pd). IO-first with 10 kΩ: `GATE` 3.28–3.30 V for 4.2–4.4 µs (simulated, `gA_pd`). A pull-down strong enough to hold `GATE` against the 30 mA pad drive was not qualified |
| P3 | `VDDA` (pin 7) tied to the `IOVDD` rail | Analog-pad ESD diodes reference `IOVDD`; `VDDA` above `IOVDD` by a diode drop forward-biases them (D14) | specified |
| P4 | `EN` held low ≥ 2 ms after both rails are stable when 10 nF is on the `VREF` pin | EN low resets the digital state and holds `GATE` off. BGR586 output resistance 19.3–25.8 kΩ over corners (22.3 kΩ at tt/27 °C), so 10 nF gives τ ≈ 0.2–0.27 ms | Simulated 1 % settling from ramp start with 10 nF: 1.26 ms (tt/27 °C), 1.20 ms (ff/−40 °C), 1.32 ms (ss/125 °C, pad-less stand-in; the stock pad did not converge) (`../blocks/g1_bgr/sim/system_checks_20260924/RESULTS.md`) |
| P5 | Scale the P4 delay with the `VREF` pin capacitance | Settling scales with Rout·C. More capacitance filters probe and board noise on the test pin but lengthens the delay | 0 nF: about 7–8 µs, with a 1.3–1.7 % overshoot during the ramp; 100 nF: 12.0–13.2 ms to 1 % (simulated). Other values: not run |

Simultaneous ramps, missing rails, brownout and shutdown are not qualified by
these cases. “Core before or with IO” is a board requirement, not a general
safety guarantee.

For calibration, keep the load bus isolated by an independent external inhibit,
then raise EN, allow synchronous reset release, and program/read back the
configuration. EN low resets serial/register state and cannot preserve custom
configuration while holding the gate off. Keep the external inhibit asserted
through calibration; reassert it before any EN cycle and reprogram afterward.
The bench sequence and its unrun hardware checks are in
`../measurement/README.md`.

With automatic load arming externally inhibited, inject a
known interior shunt voltage (nominally 25 mV), use zero SENSE_OFS and disable
hysteresis. Sweep each threshold independently after settling and locate a
bracketed crossing Ccross. Under the nominal mapping Cideal=Vin/LSB, the shared
correction is **Ccross−Cideal**, rounded to a representable integer. A positive
input-path offset needs a positive correction, because the RTL adds SENSE_OFS
to the DAC code. The old instruction to negate a zero-input crossing had the
wrong sign under this convention and cannot bracket negative offsets at code 0.
The 25 mV fixture demonstrates policy arithmetic; analog calibration yield
requires the joint loaded-chain simulations and measurements.

A nominal threshold C can accept correction O only if 0≤C+O≤255. For the reset
hard code 254 the positive allowance is +1 (~0.196 mV). A sample needing +20
must use C≤235 (~46.1 mV), or be rejected for the intended threshold. Independent
threshold programming may compensate comparator differences; it cannot extend
the DAC range. One offset cannot independently correct gain, both comparators,
and temperature drift. Freeze each sample's calibration at room temperature,
then evaluate residual <0.5 mV and threshold error at temperature/common-mode
and supply endpoints. Recalibration at each test point is not acceptance.

For valid feedback-loop measurements, phase margin ≥60° and gain margin ≥10 dB
are proposed screening limits. They do not replace a valid loop-injection model
or establish stability from transient appearance alone.

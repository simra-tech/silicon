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
- **Area:** 1.35 × 1.35 mm die including sealring and IO ring. The 1 × 1 mm allocation was withdrawn on 2026-09-18 because the IO cells need an external bondpad and sealring clearance (`PLAN.md` D10); 1.2 mm was withdrawn on 2026-09-19 when the laid-out macros exceeded its core window (D13).

## 2. Block breakdown

| Block | Function | Devices | Interfaces |
| --- | --- | --- | --- |
| `G1_SENSE` | Low-side Kelvin shunt amplifier. Differential input 0 to 50 mV across an external shunt, gain 20, bandwidth ≥ 2 MHz, input-referred offset target < 0.5 mV after trim. Common-mode −0.1 to +0.3 V. Difference amplifier around a 3.3 V PMOS-input OTA with a V<sub>REF</sub>-derived output pedestal (`PLAN.md` D1). | thick-oxide PMOS input pair, thick-oxide MOS, `rppd` | in: `SENSE_P`, `SENSE_N`; out: internal `ISENSE` (pedestal + 20 × V<sub>shunt</sub>) |
| `G1_TRIP` | Two clocked comparators on `ISENSE`: (a) hard threshold, trips after N consecutive samples above it (blanking); (b) soft threshold, trips when an up/down sample counter reaches the programmed trip-off window (`PLAN.md` D3). Thresholds are 8-bit codes of V<sub>REF</sub>-referenced resistor-string DACs; hysteresis and all windows programmable. | 1.2 V StrongARM comparators with SR latches, two 8-bit `rppd` string DACs, digital timers in `G1_CTRL` | in: `ISENSE`, `TRIP_SET`, registers; out: `cmp_soft`, `cmp_hard` to `G1_CTRL` |
| `G1_GATE` | Drives an external low-side logic-level N-FET. On `TRIP`: gate low within the response target, then latched off or retriggered after a programmable hold. Enable input. | `sg13g2_IOPadOut30mA`, LV/HV level shift | out: `GATE`, `FAULT_N`; in: `EN` |
| `G1_BGR` | First-order op-amp-less cascoded HBT bandgap in the 3.3 V domain, 1:8 emitter units. V<sub>REF</sub> nominal 1.04 V (simulated, untrimmed), TC 11 to 52 ppm/°C over −40 to 125 °C across corners; I<sub>PTAT</sub> 4.1 µA at 27 °C for the sensor and DACs; 1:4 ratio test mode. | `npn13G2`, thick-oxide MOS, `rppd`, `rhigh` | out: `VREF`, internal `IPTAT`, `VBE`, `dVBE` |
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
| Analog supply | 3.3 V (3.0 to 3.6) on `VDDA`, about 1.5 mA (simulated sum of the 3.3 V blocks) | Specified | block READMEs; D14 |
| IO / analog supply | 3.3 V (3.0 to 3.6) | Specified | `sg13g2_io` |
| Die | 1350 × 1350 µm incl. sealring | Specified | macro area budget, `PLAN.md` D13; QFN24 accepts up to 2 × 2 mm |
| Package | QFN24, 4 × 4 mm, 0.5 mm pitch, 200 µm die | Specified | packaging offer |
| Shunt sense range | 0 to 50 mV differential, low-side; `ISENSE` = 1.0 V pedestal + 20 × V<sub>shunt</sub>, i.e. 1.0 to 2.0 V | Specified | `blocks/g1_sense/README.md` (simulated gain 19.98 to 19.99, bandwidth 3.6 to 4.8 MHz) |
| Trip response | <10 µs from a persistent hard fault outside the guard band to `GATE` <1.0 V; only after arming and outside the inrush mask, for declared settings/clock/load | Specified target | `HARD_N` counts decisions every 2 oscillator cycles; default N=4. Nominal compact C-PEX/RTL anchor passed at simulated 1.40346 µs with ideal clock and fitted pad; broader coverage remains incomplete |
| I²t window | 50 µs to 10 ms, programmable | Assumed | design target |
| Hard threshold | 8-bit DAC code, 0.5 to 1.0 of the sense full scale (about 25 to 50 mV of shunt drop), programmable; nominal load current is mapped to 20 to 25 mV of the 50 mV range | Specified | `blocks/g1_trip/INTERFACE.md`; the earlier "1.5× to 8× nominal" was unreachable |
| `TEMP_OUT` frequency | 1.59 MHz at 25 °C (simulated, PTAT mode), 5.2 kHz/°C; 1.2 to 2.4 MHz over −40 to 175 °C; ±15 % process spread before calibration | Specified (simulated) | `blocks/g1_t2f/README.md` |
| Sensor accuracy | ±2 °C after fixed per-sample two-point calibration, −40 to 125 °C | Specified target | Joint extracted mismatch subsets contain failures under the original linear calibration; alternative mappings remain unadopted. Historical nominal residual and beyond-range results do not establish mismatch or package-stress accuracy |
| Characterisation range | 77 K to 175 °C | Assumed | package limits, not verified |
| Sense-amp input offset | Residual <0.5 mV after calibration; revision-A simulated σ≈4 mV is historical, not revision-B qualification. Signed digital correction −128…127, ~0.196 mV/code; available range depends on threshold | Specified target | Code 254 permits only +1 step; see calibration contract. Joint calibrated rev-B MC not run to completion |
| ELT NMOS | Experimental layout excluded from assembled chip | Not applicable to assembled chip | `blocks/g1_dose/README.md`; historical `Gat.f` failure retained |
| Total power | <10 mW, sum of core, analog and IO rail input power, declared load/activity | Specified target | Full operating-state coverage not run |
| BGR temperature coefficient | ≤50 ppm/°C over −40…125 °C | Specified target | Baseline qualified 100-sample screen has 54 failures; enlarged-array candidates also fail and remain unadopted |
| SENSE gain / bandwidth | 20 ±0.1 / ≥2 MHz, common mode −0.1…+0.3 V | Specified target | Selected block results exist; complete corners and joint loaded PEX not run |
| OSC trim reach | 10 MHz reachable by a code 0…15 at supported PVT | Specified target | Screen contains a slow/hot 9.9748 MHz maximum failure; actual-receiver loading and expanded mismatch coverage remain incomplete |

## 5. Verification gates

Status is scoped to the recorded subset; a passed subset does not pass its
unrun extensions. Evidence index: `../review/G1_DESIGN_REVIEW.md`, block
READMEs, and `../blocks/g1_top/sim/DIAGNOSTICS_20260921.md`. These are baseline
facts, not claims that the closure campaigns have completed.

| Gate | Scope | Status / remaining coverage |
| --- | --- | --- |
| Schematic simulation | Recorded nominal block cases | passed subsets; complete corner/load matrix not run |
| Corner / mismatch | Qualified block ensembles and joint calibration pilots | baseline SENSE residual failed 43/100 and BGR TC failed 54/100; joint pilots expose hard-code clipping; complete joint qualification remains incomplete |
| Temperature | Model-supported −40…125 °C | joint extracted subsets completed with linear-calibration failures; numerical failures retained; 300-sample and adverse coverage incomplete |
| Beyond-range temperature | 150/175 °C and 77 K | selected exploratory data only; qualification not applicable with nominal model extrapolation |
| RTL / functional GLS | Recorded built 256 + 3×128 configuration | functional, expanded CDC and fault-injection subsets passed; missing-clock and unprotected-configuration hazards remain; timed GLS is unqualified because timing checks are unsupported |
| Breaker co-simulation | Corrected-clock schematic cases | passed subsets; old clock-bridge timings invalid for acceptance |
| Integrated PEX | OP, 1/4/10/24 µs prefixes and compact 28 µs configured fault | startup subsets and nominal compact hard-trip acceptance passed; historical interrupted runs retained; baseline-preamble equivalence and broader fault coverage incomplete |
| Block DRC / LVS | Assembled macro versions | passed recorded checks; experimental ELT excluded |
| Block PEX | Existing capacitance extraction and selected tests | passed subsets; full wire-R, fill coupling and statistical scaling not established |
| Assembled hard DRC / precheck | 1350 µm final GDS | passed recorded checks |
| Density | 1350 µm filled GDS | passed recorded checks |
| Recommended pad rules | Final assembly | failed; unresolved |
| Antenna | Final assembly | failed; unresolved |
| Core-only LVS | 52 matched circuit pairs | passed; excludes full IO-ring verification |
| IO-inclusive LVS | Final assembly | failed; unresolved |
| Streamout comparison | Delivered final views and separate candidate | delivered differences unresolved; scoped namespaced prefill comparison passed, final filled-view closure incomplete |
| Power-order safety | IO first, core absent, EN low and expanded fixtures | original unsafe-high case failed; 216-case expanded screen has 156 passes, 22 failures and 38 timeouts; no general sequencing qualification |
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

Keep EN low until both rails are stable, the analog bias is settled, and the
required reset delay has elapsed. Existing evidence supports a selected
core-first startup only. IO-first is failed. Simultaneous ramps, missing rails,
brownout and shutdown are unqualified until their detailed pad-model tests
complete; “core before or with IO” is not a general safety guarantee.

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

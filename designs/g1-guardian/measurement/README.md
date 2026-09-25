# G1 measurement plan

Physical measurements: **not run**; no fabricated samples or instrument records
are available. The part count is **open**: the tape-in package
(`../review/TAPEIN_PACKAGE_20260924.md` §5) lists 10 packaged parts, the
specification states no count, and an earlier draft of this plan proposed 20. This procedure is a test plan,
not evidence of silicon, package, radiation or cryogenic qualification.

## Fixture and records

Use the released pad/bond map revision, a socket or soldered adapter rated for
the intended temperature, and separate current-monitoring links for VDDA and
IOVDD even when both derive from the same 3.3 V supply. Use four-wire connections
to a characterized 25 mΩ shunt. Record its measured resistance and temperature
coefficient, conductor return resistance, board revision, FET part/lot, gate
resistor, load topology, bus voltage and clamp components. A voltage/current
rating alone does not define an inductive load or its shutdown energy.

The recovered simulation fixture is 1 A nominal, 5 nF/10 Ω gate loading and a
behavioral switch; its 3 A/4 A faults exceed the specified 50 mV SENSE range.
CSD16340Q3 is now a **simulation characterization candidate**, not a selected
board BOM. Its assumed 5 V/12 V R-L fixtures are documented separately in
`../blocks/g1_gate/sim/REAL_FET_20260921.md`.

Every record names sample ID, instrument model/serial, calibration date, fixture
revision, software revision, actual rail voltages and local case/shunt
 temperatures. Preserve raw scope/SMU/counter data, commanded stimulus, register
readback and uncertainty calculation. Instrument ranges, input impedance,
bandwidth, probe loading and current compliance must accompany results.

Before testing, issue a revisioned run sheet for each sample and fixture. Pin
the released 24-pad/bond-map revision, package/board continuity record,
instrument connection diagram, rail and load-source current limits, interlock
and external cut-off settings, capture channels/skew, calibration files and
analysis-script version. Save raw data with an immutable sample/run identifier;
keep aborted and out-of-range runs rather than replacing them with a successful
repeat. State the specified acceptance limit, assumed stimulus and unknown
fixture limit separately. Log the measured value, uncertainty, and
pass/fail/not-run decision against the predeclared limit. Reserve and identify
unpowered controls and separately designated stress samples before exposure.

## Board and bench requirements (2026-09-24)

These apply to the chip of record `g1_chip_top_1414.gds` (`629d303a…`). The
numbers are **simulated**; none has been measured. Specification:
`../specification/G1_TOP_LEVEL_SPECIFICATION.md` §6, P1–P9. Rows B2, B3, B6–B8 were
corrected on 2026-09-25 from the electrical red-team review
([ELECTRICAL_SYSTEM.md](../review/redteam-20260925/ELECTRICAL_SYSTEM.md)).

| # | Requirement | Bench implementation | Basis (simulated) |
| --- | --- | --- | --- |
| B1 | Power sequencing: `VDD` (1.2 V) before or with `IOVDD` (3.3 V); `VDD` stays until `IOVDD` is down | Sequenced supplies, or a supervisor that holds the 3.3 V rail off until 1.2 V is valid. Capture both rails and `GATE` on every power cycle | With `IOVDD` alone the IO output pads have no core-driven gate signals; `GATE` reached 3.288 V (`../blocks/g1_gate/sim/POWER_SCREEN_20260921.md`). Core-first, chip netlists: `GATE` ≤ 0.073 V with EN low, **with an ideal `EN` copy**. With pad models the `EN` input reads enabled and the `GATE` latch state is undefined until `IOVDD` ≈ 1.1 V (1 of 6 runs commanded the gate on); B1 alone is not sufficient, B2 is mandatory |
| B2 | **Independent load-bus inhibit asserted during every power-up, whatever the order** (mandatory); optional `GATE` pull-down; ramp `IOVDD`/`VDDA` fast (target < 100 µs) | The independent load-bus inhibit, asserted before any rail rises; optionally a resistor from `GATE` to ground at the FET. Record both | Core-first with 10 kΩ: `GATE` ≤ 0.009 V (≤ 0.014 V at ss/125 °C and ff/−40 °C, `pads nodcn`). IO-first on the chip netlists, with or without 10 kΩ: `GATE` 3.28–3.30 V for 4.2–4.4 µs until `VDD` is up, and 1 A load flows ([RESULTS_20260925](../blocks/g1_top/sim/campaigns/RESULTS_20260925.md) §5). A 10 kΩ pull-down does not hold `GATE` low with IO first. Keep the independent inhibit asserted through every power-up |
| B3 | `EN` delay: `EN` low ≥ 2 ms after both rails are stable with 10 nF on `VREF` | Drive `EN` from the host or a low-impedance CMOS/Schmitt buffer after a rail power-good, with a fast, clean edge; never from a slow RC timer (the input has no hysteresis and chatters through its threshold). Do not tie `EN` high | BGR586 output resistance 22.3 kΩ (tt/27 °C); 1 % settling 1.20–1.32 ms over three corners with 10 nF (`../blocks/g1_bgr/sim/system_checks_20260924/RESULTS.md`) |
| B4 | `VREF` pin capacitance trade-off | Choose the capacitor before the run and record it. Scale the B3 delay with it | 0 nF: 1 % in about 7–8 µs, 1.3–1.7 % overshoot during the ramp, and the pin sees probe loading directly. 10 nF: 1.2–1.3 ms. 100 nF: 11.8–13.2 ms. Stock-pad startup at ss/125 °C did not converge in simulation (numerical; the pad-less stand-in settles) |
| B5 | `VDDA` (pin 7) tied to the `IOVDD` rail | One 3.3 V source with separate current-sense links for `VDDA` and `IOVDD` (≤ 0.5 Ω each, decoupled on the chip side), or the sense on the common 3.3 V source; no separate `VDDA` supply; decouple `VDDA` at pin 7 | Analog-pad ESD diodes reference `IOVDD` (`PLAN.md` D14); a larger `IOVDD` link lets `VDDA` exceed `IOVDD` during 30 mA `GATE` / 16 mA `TEMP_OUT` edges |
| B6 | Pull-downs on `EN`, `SCLK`, `SDI`; `EN` routed away from `FAULT_N`/`GATE` | For example 100 kΩ at the package on each | The input pads have no pull and no hysteresis; noise on floating `SCLK`/`SDI` can complete write frames (e.g. stop the clock or disable both paths); floating `EN` gives a random enable. `EN` is an unfiltered asynchronous reset: a few-ns low glitch clears a latched trip, resets all registers and re-opens the 1 ms inrush mask |
| B7 | `VDD` supervisor; grounds | A `VDD` undervoltage supervisor asserts the load-bus inhibit. Tie `VSS`, `IOVSS` and the paddle together at the package | A `VDD` brownout with `IOVDD` present reproduces the IO-first unsafe state. `VSS` and `IOVSS` are joined on the die only through substrate resistors |
| B8 | Device-pin limits | `G_SHARED` ≤ 1.32 V except in a declared stress experiment (thin-oxide gate, no secondary protection; handle pin 19 as ESD-sensitive); every device pin ≥ −0.3 V while powered; shunt voltage at the sense pins ≤ 100 mV; never leave `SENSE_P` open while powered | spec §4 absolute maximum; `ELECTRICAL_SYSTEM.md` S1, S5 |

Record the actual ramp times, the `VDD`-to-`IOVDD` delay, the pull-down value,
the `VREF` capacitor (value and ESR) and the `EN` delay in the run sheet. The
BGR586 supply current (319.7 µA simulated, tt/27 °C) is a large part of the
3.3 V quiescent current; compare the measured `VDDA` current against it.

## Before enabling a load

1. Check unpowered continuity and pin isolation with bounded test current.
   Confirm pin map, paddle/ground connectivity, both Kelvin sense leads and
   separate supply currents. Keep the load bus physically isolated or inhibited
   by an independent external device; document and verify that device's state.
   EN is not a configuration-preserving load-bus inhibit.
2. Hold external EN low and keep the independent load-bus inhibit asserted
   (mandatory for every power-up order, B2).
   Bring 1.2 V VDD up before or with the 3.3 V IO/analog rail (B1), with the GATE
   pull-down fitted (B2); observe GATE throughout
   both ramps with the real FET attached but no energized load bus.
   IO-first is a known simulated unsafe condition.
   Simultaneous startup is not generally qualified by one passing ramp shape.
3. Establish rail/reference settling and the required reset delay with EN low
   (at least the B3/B4 delay for the fitted VREF capacitor).
   With the load bus still independently isolated, raise EN and allow synchronous
   reset release. EN high can permit GATE arming before custom configuration.
   Only now verify reset defaults, program/read back the required configuration
   and perform calibration. EN low holds the serial interface and registers in
   reset; register access while EN low is not a valid verification step.
4. Confirm calibrated settings, fault/inrush state and intact sense wiring, then
   deliberately release the independent load-bus inhibit using a current-limited
   fixture. Test a persistent fault already present when the bus is applied,
   with the declared inrush/mask policy; do not assume immediate protection
   under reset defaults. Reassert the independent inhibit before cycling EN,
   and repeat configuration/readback after every EN reset.
5. During shutdown isolate the load bus, lower EN, and keep the core rail present
   until the IO rail is down. Test each permitted ramp, brownout and missing-rail
   response before a load-energy test. Capture actual rail/GATE/FET VGS waveforms.

Qualify the independent protection fixture without relying on G1 before any
energized load test: inject a bounded external fault while the DUT is isolated,
measure the inhibit's actual open/close state, cut-off delay, source-current
overshoot at the intended Kelvin pins and maximum delivered/stored energy, and
verify that removing control power cannot silently energize the bus. Record
source-compliance transients and the clamp return path, not just set points.
Permitted fault-energy and FET/package limits are **unknown** until the BOM and
fixture test establish them; a 50 mV sense-range setting is not a survival
limit. Keep the supervised, current-limited, non-inductive
[feasibility envelope](../specification/FEASIBILITY_DEMO_ENVELOPE_20260922.md)
separate from later real-use load qualification.

Determine reference settling from the observed waveform and a declared error
band before releasing EN. With the chip's BGR586 and 10 nF on the pin, the
simulated time to 0.1 % is 1.67–1.93 ms over three corners (B3/B4). The earlier
7.35 ms (27 °C) and 7.84 ms (−40 °C) figures belong to the superseded Sep-19
bandgap (output resistance 76–101 kΩ). These are characterization results, not a
guaranteed delay. The integrated
functional fixture starts from solved DC and does not establish cold power-up
settling. See [VREF dynamic evidence](../review/audits/VREF_PAD_DYNAMIC_20260922.md).

The corrected sequence is consistent with `g1_digital_top.v` resetting both
serial and register-file state from EN. An [isolated RTL regression](../blocks/g1_ctrl/sim/BENCH_SEQUENCE_CONTRACT_20260922.md)
passed two scenarios and 2,888 checks, using ideal external inhibition and
comparator signals; this does not validate physical protection. Execution of this complete procedure
with real pads, FET, load-bus inhibit and instruments is **not run**. The inhibit
hardware/BOM and verified fault-energy limits remain unspecified. The
[proposed supervised-demo envelope](../specification/FEASIBILITY_DEMO_ENVELOPE_20260922.md)
is an assumption, not a qualified board: keep hysteresis/FAST_EN off and codes
static while energized. Response to open/shorted Kelvin wiring remains unqualified; do not infer sensor
single-fault tolerance or overload survival from ordinary breaker tests.

## Host rules for register access and EN (2026-09-25)

From the digital red-team review
([DIGITAL.md](../review/redteam-20260925/DIGITAL.md); hazards reproduced in RTL and
functional gate-level simulation of the on-chip netlist, simulated only). The bench
host software follows these rules on every run:

- **Read back every safety-relevant write** (DAC codes, MODE, INRUSH, SOFT_TIME,
  HOLD_TIME, RETRY_MAX, OSC_CTRL, SENSE_OFS) and idle at least 128 oscillator cycles
  (≥ 16 µs at 8 MHz) with SCLK low before each such frame. Back-to-back frames are
  not used for these registers. Keep every SCLK-low phase inside a frame below
  64 oscillator cycles (< 5.3 µs); a longer stall or one SCLK glitch re-frames the
  stream and can redirect a write to another register (hazard S1).
- **Change SOFT_TIME only with MODE.SOFT_EN cleared**, then restore SOFT_EN after
  both bytes are written and read back. Neither byte order is safe while the soft
  path is live: the intermediate value can be 0x0000, "trip on the first sample" (S2).
- **Increase INRUSH only with the external inhibit asserted**, then wait for
  STATUS.INRUSH_ACTIVE = 0 before releasing the inhibit. Raising INRUSH while armed
  re-opens the inrush mask; the hard path is blind for up to (255 − old) × 512
  cycles, about 13 ms (M2).
- **Clock watchdog.** Alternate reads of CHIP_ID and OSC_CNT_L. If CHIP_ID stops
  reading 0x47 or OSC_CNT_L stops changing, drop EN and assert the external
  inhibit. A stopped oscillator removes all protection, FAST_EN included (both
  comparators are clocked), and serial reads then return stale data (M1).
- **Kelvin-integrity check** before arming and after every EN cycle: with load
  current flowing and DAC_SOFT at a low code, STATUS2.CMP_SOFT must read 1. An
  open SENSE_N makes ISENSE ≈ 0.05–0.29 V and the breaker blind with no indication;
  an open SENSE_P trips permanently ([ELECTRICAL_SYSTEM.md](../review/redteam-20260925/ELECTRICAL_SYSTEM.md) M3).
- **Unexpected-reset check.** An EN glitch resets every register silently; check
  periodically that a written configuration (or TRIP_CNT) has not returned to its
  default, and periodically rewrite the configuration (registers are not TMR).
- **EN low at power-up.** EN is the only reset (no on-chip POR, no pull-down on the
  EN pad); the board must hold it low. Every EN rise restores the register defaults
  (FAST_EN = 0) and reopens the ≈ 1 ms inrush window, so a fault present at EN rise
  or at a retry conducts for about 1 ms, limited only by the FET and bus. This is
  **accepted design behaviour covered by the external inhibit, pending owner
  confirmation** (M3). Keep the inhibit asserted across every EN rise.

## Calibration and breaker tests

1. Apply a traceable interior shunt voltage, initially 25 mV (1 A at nominal
   25 mΩ). Use zero SENSE_OFS and zero hysteresis to bracket each comparator's
   crossing with threshold codes. Include both approach directions and repeated
   decisions. A shorted-shunt point alone need not bracket both offset signs.
2. Calculate signed correction with the documented register convention and
   saturated arithmetic. Verify reachable corrected soft/hard endpoints and
   their ordering. Hard default 254 has only one positive correction code;
   record clipping as a failure, not successful calibration.
   The hard comparator trips below its DAC code. In simulation the offset is
   40–56 LSB (7.9–11.0 mV of shunt) on the TRIP NF4 block bench, with a
   10–11 LSB corner spread. On the chip netlists the effective hard threshold
   at code 200 (39.25 mV) is 30.00–31.25 mV (tt/27 °C, [RESULTS_20260925](../blocks/g1_top/sim/campaigns/RESULTS_20260925.md) §4).
   Bracket the hard crossing starting about 60 codes above the target and
   stepping down, not only around the target code. Expect the calibrated hard
   code 40–56 codes above the nominal one (simulated block bench over corners), and a usable hard range of
   about 25–40 mV of shunt. Record the measured offset at each temperature.
   The simulated corner spread exceeds what one room-temperature point absorbs.
   The soft path is within 1 LSB in simulation. A common offset
   correction cannot cancel independent comparator errors and gain error.
3. Freeze room-temperature calibration. At declared thresholds outside inrush,
   test no-trip at or below 0.9× threshold and trip at or above 1.1× threshold.
   Characterize the intervening band separately. Include event phase, short
   pulse rejection, FAST_EN, soft persistence, retry and clear/rearm.
4. Capture shunt voltage, GATE, actual FET VGS/VDS, load current and FAULT_N.
   Measure event-to-GATE below 1 V and remaining below 1 V; the hard-path target is
   <10 µs for declared settings. Separately report time to 1 % load current,
   peak VDS, and integrated FET/load energy. Inductive current may continue
   through a clamp after the FET switches off. State probe skew/error bounds.
5. Replay a saved load waveform with exact sample rate and injected fault
   shape. The implemented soft path uses comparator persistence; do not label
   it an established I²t estimator.

For a real FET/load run, capture the commanded and independently measured bus
voltage/current and shunt-pin differential before and after each fault. Preserve
the FET part/lot, gate resistor, wiring/clamp topology and board temperature.
Test only the prequalified current-limited resistive envelope first, with fixed
codes and FAST_EN/hysteresis off. Predeclare normal steps, sustained faults,
event phases, reset/rearm and stop conditions; repeat boundary cases with the
same configuration readback. Analyze GATE crossing, current decay, peak VDS and
energy as distinct outcomes. Inductive or autonomous-load testing is **not
run** and requires a separately established energy/thermal envelope; passed
GATE timing alone cannot release it.

## Temperature, reference and device coupons

Calibrate TEMP_OUT separately for each part at 25/100 °C. Freeze those coefficients
and measure independent −40/−20/0/50/75/85/125 °C points after documented thermal
settling. Compare against a calibrated reference thermometer adjacent to the
package, including thermal gradient and self-heating uncertainty. Record
VREF, IPTAT observables, oscillator trim/frequency, supply current and threshold
residuals at each point. Compare the original linear calibration and any
predeclared fixed correction separately; do not fit the verification points.
Repeat selected cycles to expose hysteresis and package stress.

Expected TEMP_OUT with the chip's bandgap (BGR586), all **simulated**: block level,
typical process, nominal rails, 1.5074 MHz at 25 °C and 4.9085 kHz/°C
(`../blocks/g1_t2f/sim/qualification/t2f586-nominal-calibration-20260922.json`);
chip level on the chip netlists, tt, 1.518 MHz at 27 °C and 1.997 MHz at 125 °C,
−40 °C not run to completion ([RESULTS_20260925](../blocks/g1_top/sim/campaigns/RESULTS_20260925.md) §7).
The 25/100 °C linear calibration kept −40/125 °C within ±2 °C for the nominal
source and for the 237 of 300 mismatch samples that completed; 63 samples did not
complete (numerical), and corners, 85 °C and supply sensitivity with BGR586 are
**not run** (`../blocks/g1_t2f/README.md`). The 1.59 MHz, 5.2 kHz/°C and
−2.5 °C/V figures in the T2F block README are historical results with the
superseded Sep-19 bandgap; do not use them as acceptance values. The ±2 °C
target is therefore an expectation to test, not a simulated guarantee over PVT.

For thermal cycling, define chamber set points, ramp/dwell schedule, maximum
allowed package-to-reference temperature difference, humidity/condensation
controls and cooldown before placing a sample in the chamber. Log time-stamped
chamber, adjacent reference, case and shunt temperatures and rail currents;
start a measurement only after the declared stability window. Keep initial
calibration coefficients frozen through verification cycles and report each
point's residual and pre/post room-temperature shift by sample. If a package,
socket, probe or board exceeds its documented rating, stop and mark the point
**not run**. Cycle count/dwell and hardware limits remain **unknown** until
fixture selection; the −40…125 °C sensor target does not qualify a package or
77 K/175 °C exposure.

Characterize VREF probe loading before treating its reading as the unloaded
reference. The pad-inclusive simulation that predicts about 9.07 mV of
core-reference droop with a 10 MΩ load at 25 °C applies to the superseded
Sep-19 bandgap only (output resistance 76–101 kΩ). For the chip's BGR586
(simulated output resistance 19.3/22.3/25.8 kΩ,
`../blocks/g1_bgr/sim/system_checks_20260924/RESULTS.md`) the resistive divider
V<sub>REF</sub> × R<sub>out</sub> / (R<sub>out</sub> + 10 MΩ) gives about 2.0–2.7 mV
(2.33 mV at 22.3 kΩ, tt/27 °C). This is computed from the simulated R<sub>out</sub>, not
a pad-inclusive simulation of BGR586, which is **not run**. Record the instrument's
input resistance, bias/leakage and capacitance, and compare controlled loading
states or a characterized buffer. A nominally high-impedance probe can alter
the circuit being calibrated; see [pad loading evidence](../review/audits/VREF_PAD_LOADING_20260922.md).

For HBT_E/B/C, use SMUs with explicit compliance and VCE≤1.6 V in normal tests.
Record base/collector currents and local heating. Destructive breakdown testing,
if later requested, uses separately designated samples and its own procedure.

The default DOSE coupon is an HV/LV pair; `D_ELT` is a legacy pin name. Measure
fixture-open leakage, a pad-reference path and DUT path over voltage and
 temperature, using guarded/triax connections where appropriate. Report the
noise/leakage floor and uncertainty. Subtraction only identifies the DUT when
reference paths are demonstrably comparable; it cannot automatically recover
fA device leakage behind much larger pad leakage.

Before each DOSE bias sweep, measure instrument zero, guarded fixture-open,
short and pad/reference controls at the same range, cable routing, voltage,
temperature and settling time. Record bias polarity/direction, compliance,
current versus settling time and noise-floor distribution; retain raw currents
before subtraction. Sweep only within approved pad/device terminal limits and
stop on unexpected leakage or self-heating. Compare LV and HV drains separately
and state when reference-path mismatch or instrument floor makes DUT leakage
unresolvable. No fA-resolution or dose-response claim follows from an
unqualified subtraction.

## Exploratory temperature and irradiation

150/175 °C and 77 K are separate beyond-range experiments. Qualify the package,
socket, PCB, instruments and handling procedure for each before testing; record
exposure duration and pre/post room-temperature measurements. Successful model
extrapolation does not establish safe operation or accuracy at these temperatures.

An irradiation campaign requires a facility-specific approved procedure,
calibrated dosimetry, dose rate, radiation type/energy, bias, temperature,
measurement timing and annealing history. Retain control parts and pre-exposure
baselines; choose dose steps with the facility. Record flux/fluence and counter
readout for SEU observations. Keep TID leakage/drift and single-event results
separate. Ordinary transistor simulations establish neither LET thresholds nor
radiation hardness. Irradiation, annealing and packaged measurements remain
**not run**.

Before facility booking, freeze sample/control allocation, powered versus
unpowered bias states, the same pre/post electrical measurement script, counter
initialization/scrub/readout cadence, timestamps, dosimeter placement and
chain-of-custody identifiers. The licensed facility must approve beam safety,
dosimetry, shielding, handling, dose steps and annealing/storage protocol;
these are **unknown**, not a board-team default. Record interruptions and
annealing time between exposure and readout. Report counter upset rates with
observed fluence and uncertainty, and leakage/threshold drift with absorbed
dose and controls, without converting either into an unmeasured LET threshold
or radiation-qualification claim.

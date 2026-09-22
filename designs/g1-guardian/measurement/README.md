# G1 measurement plan

Physical measurements: **not run**; no fabricated samples or instrument records
are available. 20 packaged parts are proposed. This procedure is a test plan,
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

## Before enabling a load

1. Check unpowered continuity and pin isolation with bounded test current.
   Confirm pin map, paddle/ground connectivity, both Kelvin sense leads and
   separate supply currents. Keep the load bus physically isolated or inhibited
   by an independent external device; document and verify that device's state.
   EN is not a configuration-preserving load-bus inhibit.
2. Hold external EN low and keep the independent load-bus inhibit asserted.
   Bring 1.2 V VDD up before the 3.3 V IO/analog rail; observe GATE throughout
   both ramps with the real FET attached but no energized load bus.
   IO-first is a known simulated unsafe condition.
   Simultaneous startup is not generally qualified by one passing ramp shape.
3. Establish rail/reference settling and the required reset delay with EN low.
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

Determine reference settling from the observed waveform and a declared error
band before releasing EN. The selected simulated 10 nF VREF fixture needed
about 7.35 ms at 27 °C and 7.84 ms at −40 °C to remain within 0.1% of its
numerical DC value after a 1 ms supply ramp; its 125 °C startup did not complete.
These are characterization results, not a guaranteed delay. The integrated
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

## Calibration and breaker tests

1. Apply a traceable interior shunt voltage, initially 25 mV (1 A at nominal
   25 mΩ). Use zero SENSE_OFS and zero hysteresis to bracket each comparator's
   crossing with threshold codes. Include both approach directions and repeated
   decisions. A shorted-shunt point alone need not bracket both offset signs.
2. Calculate signed correction with the documented register convention and
   saturated arithmetic. Verify reachable corrected soft/hard endpoints and
   their ordering. Hard default254 has only one positive correction code;
   record clipping as a failure, not successful calibration. A common offset
   correction cannot cancel independent comparator errors and gain error.
3. Freeze room-temperature calibration. At declared thresholds outside inrush,
   test no-trip at or below0.9× threshold and trip at or above1.1× threshold.
   Characterize the intervening band separately. Include event phase, short
   pulse rejection, FAST_EN, soft persistence, retry and clear/rearm.
4. Capture shunt voltage, GATE, actual FET VGS/VDS, load current and FAULT_N.
   Measure event-to-GATE below1 V and remaining below1 V; the hard-path target is
   <10 µs for declared settings. Separately report time to1% load current,
   peak VDS, and integrated FET/load energy. Inductive current may continue
   through a clamp after the FET switches off. State probe skew/error bounds.
5. Replay a saved load waveform with exact sample rate and injected fault
   shape. The implemented soft path uses comparator persistence; do not label
   it an established I²t estimator.

## Temperature, reference and device coupons

Calibrate TEMP_OUT separately for each part at25/100 °C. Freeze those coefficients
and measure independent−40/−20/0/50/75/85/125 °C points after documented thermal
settling. Compare against a calibrated reference thermometer adjacent to the
package, including thermal gradient and self-heating uncertainty. Record
VREF, IPTAT observables, oscillator trim/frequency, supply current and threshold
residuals at each point. Compare the original linear calibration and any
predeclared fixed correction separately; do not fit the verification points.
Repeat selected cycles to expose hysteresis and package stress.

Characterize VREF probe loading before treating its reading as the unloaded
reference. The selected pad-inclusive simulation predicts about 9.07 mV of
core-reference droop with a 10 MΩ load at 25 °C. Record the instrument's
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

## Exploratory temperature and irradiation

150/175 °C and77 K are separate beyond-range experiments. Qualify the package,
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

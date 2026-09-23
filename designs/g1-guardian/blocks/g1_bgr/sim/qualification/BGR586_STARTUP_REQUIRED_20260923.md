# Current-source startup completion

The six original 3 V startup stimuli are retained: nominal/27 C,
slow/−40 C and fast/125 C, each with a 1 ms or 100 ms supply ramp and a
three-ramp-duration endpoint. Source SHA256 is
`586ffb58b6af31c77a2e7cbcb83b173ffa4713ec62401da30901c5a7e606283b`.
This is the source used by the current statistical campaigns, with its
legacy capacitance model. It is not final native RC extraction.

## Existing evidence reused

- Nominal 1 ms: passed in `bgr_loop24q4_hv06_startup2_20260922_r3`.
  Its exact waveform is the read-only instrumentation control, not a
  reason to rerun another uninstrumented simulation.
- Nominal 100 ms: original failed with an explicit numerical error despite
  zero process exit. That failure remains. The separately declared 20 us
  maximum-step diagnostic `bgr_hv06_startup100ms_maxstep20us_20260922_r1`
  reached 300 ms and passed its scoped numerical/level/HBT screen. Neither
  attempt is repeated by this runner. The refined recovery does not turn
  the original failed fixture into a pass.
- The four slow/fast cases for this source: passed with the original stimuli.

## Completed simulated results

| Process / temperature | Ramp | VREF at endpoint (V) | IPTAT (uA) | Maximum saved HBT external \|VCE\| (V) | Status |
| --- | ---: | ---: | ---: | ---: | --- |
| Nominal / 27 C instrumentation control | 1 ms | 1.045457678 | 4.134103 | 0.720765 | passed |
| Slow / -40 C | 1 ms | 1.047318828 | 2.829469 | 0.784545 | passed |
| Slow / -40 C | 100 ms | 1.047318829 | 2.829469 | 0.784240 | passed |
| Fast / 125 C | 1 ms | 1.041546947 | 6.253693 | 0.638535 | passed |
| Fast / 125 C | 100 ms | 1.041546947 | 6.253694 | 0.638518 | passed |

All five new runs reached their full 3 ms or 300 ms endpoints, with finite
2,842-parameter endpoint readbacks and saved external terminal voltages for
all 637 MOS/HBT instances. The instrumented nominal waveform equals the
original 1,627-row, 12-column waveform byte-for-byte. Six source/parser
controls passed; an independent saved-data audit passed in 9.752 s.
Original nominal 100 ms remains **failed**, with its separate maximum-step
recovery **passed** only in its documented scope. No original stimulus is
unrun, but the six original fixtures do not constitute six original passes.

The exact commands, executed runner snapshots, runtime identity, raw log
hashes and deterministic compressed waves are in
`bgr586-startup-required-evidence-20260923-r1`. Runtime is ngspice 46,
IHP PDK `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`, image manifest
`sha256:5fd78498e578c6e9ec10828c248ca3790fc88250ff6caf545521b29e448ea3c0`;
actual version output and all model/OSDI hashes were checked against the
qualified harness before each simulation.

## Executed bounded procedure

First run nominal 1 ms with added endpoint-only queries for all 2,842
qualified primitive parameters and saved native MOS/HBT terminal voltages.
Require its original 12-column waveform to equal the completed control
byte-for-byte. Then run the four remaining original stimuli, at most 300 s
per child and one CPU each. No timeout ladder is authorized here.

Require the original endpoint, strictly increasing finite saved time grid,
exact vector count, finite parameter inventory in its original order,
source/runtime/model identity and no solver error even with exit zero.
Retain the existing startup screen: final VREF between 0.9 and 1.2 V and
IPTAT above 1 uA; report HBT external |VCE| ≤1.6 V separately. These are
startup screens, not a substitute for temperature coefficient or accuracy.

No operating point is inserted before the original UIC transient. Thus
pre-transient parameter readback is **not run**; endpoint readback must not
be labelled a before/after fingerprint. The unsaved interval before the
first positive-time row has no measured/simulated peak bound. Mismatch is
disabled; statistical yield is **not applicable**. Full downstream loading,
startup-before-EN, final physical parasitics and lifetime qualification
remain **not run**. Model cards, circuit, tolerances, seed, process sections,
waveform and acceptance criteria are unchanged. The initializer's four
threads are reduced to one to comply with the shared resource policy.

# Loaded SENSE/TRIP qualification, 2026-09-21

All numbers below are simulated with ngspice 46, PDK commit
`84374023ee8b4b126bebbba67fcbada0a9c0ff0b`, image content ID
`sha256:5fd78498e578c6e9ec10828c248ca3790fc88250ff6caf545521b29e448ea3c0`.
Every run directory under `qualification/` retains exact source snapshots, runner,
arguments, model hashes, deck, log, waveform and bounded solver status. Existing
historical evidence is retained. `assessment_20260921.json` separates numerical
completion, narrow boundary characterization and adopted system bands.

The fixture includes the actual SENSE amplifier and its reference buffer, both full
DAC strings/switch trees, hold capacitors and comparators, clocked on opposite
phases at 10 MHz with 0.2 ns edges. VREF and PTAT sources are ideal. This is not a
joint BGR, RTL, pads or external-FET test. Nominal tt/typ, 27 °C, 3.3/1.2 V.
Schematic resistor bulks are tied to local ground in archived derived fixtures,
matching physical substrate connectivity. No model cards or rule decks changed.

## Guard-band interpretation

Hard code 254 has nominal threshold 49.841509 mV. Its ±0.25 mV characterization
points lie **inside the adopted ±10% system ambiguity band**. A disagreement
with the quiet DC comparator differential at those points is a boundary shift,
not a formal robust no-trip failure. The diagnostic guard is 1 mV comparator
input differential, approximately 0.1 mV shunt equivalent. System-band results
are assessed separately using all saved late-cycle decisions.

| Baseline case | Solver result | Narrow boundary result |
|---|---|---|
| Schematic hard −0.25 mV, 0.2 ns max step | passed, 179.8 s | failed: quiet differential −3.4924 mV, all 10 late decisions high |
| Schematic hard +0.25 mV, 0.2 ns | passed, 189.7 s | passed |
| PEX hard ±0.25 mV, 0.2 ns | **not run to completion**, each 300 s timeout | not run; endpoints only 0.828/0.743 µs of 1.52 µs |
| Schematic hard −0.25 mV, 1 ns | passed, 93.5 s | same 10/10 high; sample differential differs by 24.0 µV from finer run |
| PEX hard −0.25 mV, 1 ns | passed, 238.6 s | failed: quiet −3.5664 mV, all 10 late decisions high |
| PEX hard +0.25 mV, 1 ns | passed, 210.2 s | passed |
| PEX hard −0.25 mV, 0.2 ns, 0.52 µs prefix | passed, 195 s | same 3/3 high; selected steady-cycle differential measures within 27 µV of 1 ns run |

The prefix and selected observable comparisons qualify these anchors only, not
all future transient steps or trajectories. Full fine-step PEX endpoints remain
not run to completion. Prefix raw-summary legacy text says ten evaluations;
the saved list and independent assessment correctly contain three.

## Robust system-band anchors

All eight nominal anchors completed numerically and produced the expected ten late-cycle decisions: hard threshold at ±6 mV, soft at ±4 mV, each schematic and PEX. These points lie outside the adopted ±10% ambiguity bands. Schematic cases took 87–102 s; PEX 221–242 s. Runs `band-{hard,soft}-{sch,pex}-20260921-a` retain exact waveforms. The positive hard points are55.8415mV and exceed the specified SENSE0–50mV range; they are outside-contract diagnostics, not accepted hard-trip-band coverage. Only six of these eight anchors lie within range. No complete nominal50mV hard robust band can be qualified within that input range. This is nominal loaded-chain characterization, not PVT or calibrated yield.

## Stronger numerical qualification

The comparator statistical investigation exposed sensitivity to default solver tolerances. All four schematic robust-band points were replayed with reltol1e−5, vntol1e−7, abstol1e−14, Gear and0.2ns maximum step. The four full1.52µs cases **timed out at300s** (about1.22µs reached); no completed long-waveform result is claimed. Separate0.52µs runs all passed their three late-cycle decisions, taking143–167s each. These short settled-decision anchors support the observed nominal discrimination; longer settling and tightly solved PEX robust anchors remain **not run to completion/not run**.

## Isolated remedies tested, not adopted

At the negative hard boundary point, increasing all three hold capacitances 4×
reduces the sampled differential from approximately 3.56 to 2.13 mV, but all ten
late decisions remain high. A separate conditioner for the hard comparator also
leaves ten high decisions; its input has reversed by the sample time, after the
latch decision. A sampled input alone therefore does not predict the decision.
Neither candidate changes the canonical circuit or layout.

A 1 ns shunt step at 0.5 µs from 25 mV to 50.091509 mV gives:

| Schematic candidate | First hard output above 0.6 V | Conditioner phase-sampled 1% settling |
|---|---:|---:|
| baseline | 170.91 ns after input step | 270 ns |
| 4× hold capacitance | 470.96 ns | 570 ns |

Both analog step checks completed, but their50.091509mV target also lies just outside the specified SENSE range and is diagnostic only. Settling uses samples at a fixed clock phase,
100 ns apart, relative to the final three-cycle mean; it is not continuous-time
settling or top-level GATE response. Early step summaries retain an inactive
quiet-state wrong-decision count; the independent assessment marks it not
applicable. The larger hold capacitor adds about 300 ns and fails to resolve the
boundary displacement, so there is no evidence for adopting it.

## Reproduction

From repository root, using a new run ID:

```sh
G1_WORKDIR=designs/g1-guardian/blocks/g1_trip/sim G1_CPUS=1 flow/run.sh \
  python3 run_kickback_qualification.py --run-id NEW_ID --netlist sch \
  --image-id sha256:5fd78498e578c6e9ec10828c248ca3790fc88250ff6caf545521b29e448ea3c0
```

Use `--netlist pex --maxstep-ns 1` for bounded extracted anchors.
`--hold-scale 4`, `--separate-conditioners` and `--step-from .025` select
archived candidate/step fixtures. The hard robust-band campaign uses
`--offsets-mv=-6,6`; soft uses `--threshold soft --offsets-mv=-4,4`.
Each process is single-threaded and each transient case has a 300 s watchdog.

## Remaining checks

Full fine PEX endpoints, threshold sweeps at ±0.1/0.5/1 mV, slow ramps, event-phase
sweeps, clock duty/edge extremes, process/voltage/temperature expansion, actual
BGR and pads, joint frozen calibration MC, receiver timing and top-level GATE
response are **not run** by this campaign. V14 full-switch mismatch and V15 fine
comparator MC are separate pilots, not established by nominal kickback anchors.


The same input-range limit applies to the positive hard0.25mV boundary point and
the positive hard6mV tight short-prefix anchor. Existing raw summaries are
preserved. `assessment_input_range_20260921-b.json` adds explicit range scope and
marks those system-band conclusions not applicable outside0–50mV.

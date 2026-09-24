# Incremental clock mutual-capacitance diagnostic

Prospective electrical status: **not run**. This does not close V21a or adopt
new geometry. No physical measurement applies to this numerical diagnostic.

The whole-parallel-interval clock study has four completed clips and 32 passed
independent AC matrix checks. Its full-matrix transverse-context criterion
**failed** (up to 18.272%). Increasing the clip width also includes more actual
horizontal clock wire beyond the parallel interval, changing its ground load;
this is not a fixed-target ground-capacitance convergence experiment. Preserve
that failure. Midpoint context convergence passed separately. Neither result
is a complete routed-net R/C model.

For a separate incremental sensitivity, add only a 5.233872140 fF capacitor
between `isense` and `clk`, the largest floating-fill mutual entry among the
four full-interval clips. Their mutual entries are 5.232855634, 5.232828531,
5.233872140 and 5.233830490 fF. This observed context spread is not a bound on
omitted return paths, grounded-fill alternatives or full-net loading. Keep the
original assumed 300 fF ISENSE ground load unchanged, rather than claim it is
extracted. No ground-capacitance replacement or full-matrix convergence waiver.

Controls are completed exact-host replays `clock-coupling-host-low-20260922-a`
and `clock-coupling-host-high-20260922-a`: seed 71001, actual BGR C-PEX with
schematic SENSE/TRIP, physical DAC codes 171/240, nominal 25 °C, 0.52 µs stop,
0.2 ns maximum step, existing tight Gear/SPARSE settings and 300 s watchdog.
These use the calibrated nominal 40 mV hard threshold's low/high input anchors,
not an unqualified physical-code-204 or full 50 mV hard-threshold claim.
Both controls passed exact source/model/runtime/27-parameter/whole-wave parity.
Clock stimulus remains the actual fixture's 10 MHz, 1.2 V, 0.2 ns edge source;
it is not the integrated design's nominal comparator-clock frequency.

Only one capacitor line may change in a coupling leaf. Separate zero-added-C
leaves change only the DC shunt input by +5 and +10 µV to establish the local
phase-specific differential transfer gain. All 27 archived parameter strings
must remain exact, with complete finite waveforms and clean solver logs. The
two finite-difference gains must agree within 1%, and have nonzero magnitude,
before reporting input-referred error. No assumed gain-20 conversion.

At each of the last three soft/hard decision samples (20 ns after evaluation),
compare differential input against the unchanged baseline and divide by the
local gain. The previously declared 50 µV incremental shunt-equivalent
diagnostic limit applies; require unchanged correct guard decisions. Report
saved transient peaks separately, not as continuous-time peak bounds. Numerical
failure, gain nonconvergence or altered guard decisions remain failures; no
watchdog extension or tolerance relaxation. A pass cannot compensate for a
failed baseline calibration or establish full-interface/total-error compliance.

Pinned ngspice 46, image manifest
`sha256:5fd78498e578c6e9ec10828c248ca3790fc88250ff6caf545521b29e448ea3c0`,
IHP PDK `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`. The original interval
manifest and this contract are hashed in each new run. Exact launch arguments,
source snapshots and all status fields are retained; fresh run IDs only.

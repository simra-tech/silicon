# Prospective one-LSB loaded-feedback mechanism study

One3 µs nominal seed71001 case,900-second watchdog,1 CPU and0.15 GiB HOME
output forecast. Coordinator authorization and a fresh resource gate are
required before launch. No automatic HYS2, offset carry, PVT or skew expansion.

Reuse the passed direct-transient prefix's exact analog sources, actual timer,
compiled/attested VVP, model/init/runtime identities and static configuration.
Relative to that prefix deck, the ONLY declared changes are transient endpoint
0.9→3 µs, output filename, and adding `v(xt.cmp_clk_n)` to save/export so the
actual hard-comparator clock can be timestamped. Sources, options, seed and
all electrical stimuli remain unchanged. Exact27 POST-transient parameters
must match the frozen reference; same-instance BEFORE query remains **not run**.

Before interpreting feedback, require the original60-column projection and
time grid to be numerically EXACT against the passed prefix on0–0.85 µs.
The new header/vector is explicitly a projection difference. A parity failure
is retained as failed, never assumed harmless. No separate extra prefix run.

Numeric/identity gates: finite strictly increasing61-vector waveform to3 µs,
zero simulator exit, no solver/bridge error, actual reset/divider behavior,
valid sampled digital levels, unchanged source/model/VVP/control attestations
and27 exact post parameters. Preserve and count all model warnings separately.

Stimulus gates: verify10 mV before1.2 µs,35 mV on1.201–1.6 µs,10 mV after
1.601 µs, with1 ns edges. These are ideal imposed sense voltages, not a board
overshoot or energy bound. Read all24 counter bits and both8-bit physical DAC
codes. Check real synchronizer latency and timer up/down recurrence after the
passed initial quiet interval; require hard240 constant and soft code128 when
count0,127 when charged. Require BOTH physical128→127 and127→128 transitions,
all8 bit changes per major carry, and final low comparator/sync, zero count,
zero trip. Missing exercise is failed coverage, not a passed empty test.

Report EVERY soft and hard evaluation edge (actual delivered soft clock rise,
actual internal inverted hard clock rise), input differential at that edge,
raw result20 ns later, synchronized result and counter. For this mechanism
diagnostic, classify a comparison only when the actual differential magnitude
exceeds a prospectively declared5 mV comparator-input guard; inside it report
unclassified/not run, not an invented electrical failure.5 mV is a diagnostic
guard, not an allocated product accuracy or offset allowance. Require at least
one guarded soft HIGH during the fault and guarded LOW before/after it, and
report every guarded wrong or invalid decision, not merely final latch state.

For each DAC major-carry event report individual bit timestamps, resulting code,
real VREF-buffer/VTH waveform samples/extrema, next actual evaluation and raw/
synchronized decisions. Report all counts even if final count recovers.

The stated1 µs settling requirement remains unchanged. For every code change,
report delay to the next relevant evaluation and mark a delay<1 µs as FAILED
settling-interval contract, separately from mechanism/numeric status. Rapid
feedback does not earn1 µs settling credit, even if every observed decision is
correct. Do not claim waveform accuracy settled merely from digital recovery.

No serial, FAST/GATE, pad/package/route-skew, full physical adoption or complete
hysteresis qualification follows. Mechanism gates and the existing interface
settling conflict are separate explicitly reported outcomes; overall design
qualification remains not run.

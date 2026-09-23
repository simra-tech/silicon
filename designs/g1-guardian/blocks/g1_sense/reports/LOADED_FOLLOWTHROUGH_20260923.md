# Source-held loaded SENSE adverse AC and settling

Status: **failed** selected slow/cold bandwidth; other scoped checks below.
This is schematic gm4/comp3 SENSE with actual BGR586 and full TRIP loading,
not physical PEX or global/periodic-loop qualification. No circuit parameter,
model, numerical criterion or source interface was changed.

## Adverse coverage

The slow/low-cold fixture uses original-SPARSE seed77001, SS/worst resistor and
capacitor corner, −40 °C, 3.0/1.08 V rails, true common mode0 V and25 mV shunt.
Its exact source/OP anchor is the previously qualified
`joint586-slow-fixture-controls-20260923-b-low_cold_cm0` fixture. The companion
fast/high-hot seed78001 fixture was run independently at125 °C and3.6/1.32 V.
These are two selected own-corner draws, not a
corner population or all-common-mode proof.

| Slow/low-cold result | Simulated value | Existing criterion | Status |
|---|---:|---:|---|
| Differential gain at1 Hz |19.9984788695 V/V|19.9–20.1|passed|
| First closed-loop half-power bandwidth |1.566201948 MHz|≥2 MHz|**failed**|
| Conditional main-loop phase margin |71.6579417° at0.992595037 MHz|≥60°|passed|
| Minimum odd-180° gain margin |17.8623144 dB|≥10 dB|passed|

All three slow leaves completed with901 finite complex points from1 Hz to1 GHz,
exact pinned runtime/model identities, and exact11,512+27 parameter checks.
The differential excitation is P=+0.5 V/N=−0.5 V AC, so its differential basis
is exactly1 V and its common-mode excitation is zero. All nine baseline quiet
voltages match the original source fixture exactly.

The established two-injection Tian probe preserves the canonical source on
inverse transformation. The two probes have exact mutual DC/source equality.
Their exact DC comparison to the unprobed baseline **fails** (largest observed
voltage change13.03597 nV); the prospectively established1 µV/1 nA probe-DC
equivalence check passes. The added1 TΩ node contributes59.1603 fA of signed
DC shunt current, recorded rather than omitted. Higher odd-180° crossings are
retained in the full analysis, not replaced by the first crossing alone.

The batch stopped on the bandwidth failure. That result is retained even if
independent subsequent cases complete. No compensation or bias retuning is
implied. The inherited model temperature/limiter warnings remain in the logs.

The fast/high-hot differential leaf separately passed its exact source,
runtime,11,512+27 parameter and nine-value OP checks, with901 finite complex
points. Its gain is19.9834448022 V/V and bandwidth3.472025243 MHz: both pass
their unchanged criteria. These results do not depend on a loop-probe result.

The fast Tian voltage probe completed numerically, but **failed** the frozen
1 µV DC-equivalence criterion: ICMP changed5.183948772 µV and the hard
threshold changed4.657254696 µV. Its full parameter inventory remained exact.
The independent current-injection leaf is **not run** after that failure;
fast phase/gain margins are **not run**, not inferred from the failed probe.
The original failed receipt and raw data are retained without a tolerance
waiver, changed solver or unchanged retry.

## Loaded step coverage

Rise/fall preparation holds the nominal seed73001, canonical gm4/comp3 source,
actual BGR586, full TRIP and original clock/loading/numerics. Positive input
changes25→50 mV or25→0 mV in1 ns at200–201 ns; negative input remains0 V.
Each target is a separately solved final DC point, not the transient endpoint.
The original nine initial OP values and full parameter inventory must match.

All four nominal target/transient leaves completed with exact source/runtime
and11,512+27 parameter checks. Both transient initial nine-value OP anchors
match exactly. The independent DC targets are2.001857457733844 V at50 mV
and1.003942357239692 V at0 mV shunt.

| Simulated nominal step |25→50 mV|25→0 mV|
|---|---:|---:|
| Independent endpoint gain, V/V |19.9590005852|19.9576034346|
| Gain19.9–20.1 |passed|passed|
| Last outside / next inside±1% band, absolute ns |558.559327 /558.759327|563.646602 /563.846602|
| First saved point after final entry, delay ns |358.759327|363.846602|
| Sampled overshoot |3.61896%|4.08850%|
| In band through1.02 us |yes|yes|
| Last200 ns ISENSE min/max,V |2.001198307 /2.002058775|1.003872931 /1.004381737|

Two prelaunch resource checks for the falling transient failed53 versus55
required CPUs; they launched no analog job. A later fresh56-CPU check allowed
the unchanged leaf to run. The completed falling DC target was reused by exact
hash, not rerun. These deferrals remain separate from electrical dispositions.

Settling reports the last saved-point entry into±1% of the independently
determined step amplitude, including subsequent ringing through the saved
endpoint. No settling-time limit is invented. The fixed clock remains active;
its ripple is neither filtered nor absorbed into a fitted target. This does
not prove behavior between saved points or actual package/route parasitics.

## Reproducibility and exclusions

Runner: `../sim/run_loaded_followthrough.py`; preparation/rejection controls:
`../sim/test_loaded_followthrough.py`; analysis/analytic sign, ringing and
crossing controls: `../sim/analyze_loaded_followthrough.py`.
Independent fast differential-only analysis:
`../sim/analyze_loaded_differential.py`; it cannot report loop margins.
Each leaf has its source hashes, original fixture/deck/log hashes, exact
generated deck and inverse check, runtime/model inventory, bounded child
receipt, raw complex data or waveform, warning/error audit, and summary.

Built against the pinned SG13G2 PDK commit
`84374023ee8b4b126bebbba67fcbada0a9c0ff0b`, ngspice46/SPARSE (creation
2026-07-27), image config
`ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2`
and corresponding manifest
`5fd78498e578c6e9ec10828c248ca3790fc88250ff6caf545521b29e448ea3c0`.
The host independently verifies config identity; the simulator receipt compares
the entire expected runtime/model identity with the qualified source fixture.

Full physical extraction/model-plane applicability, all PVT/common modes,
buffer/reference loop coverage, periodic stability, pad/board loading and
production adoption remain **not run** or independently unresolved. Existing
nominal AC/noise evidence and original failed resource gates are not replaced.

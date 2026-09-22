# Extracted mismatch power-order pilot

Simulated with the same pinned ngspice46 / IHP
`84374023ee8b4b126bebbba67fcbada0a9c0ff0b` runtime and eight-device CPEX source
as [the qualified mismatch screen](MISMATCH_RESULTS_20260922.md). The enabled
source is byte-identical to its qualified copy; the realized seed56001 vector
matches all32 previously observed parameters exactly, at all before/after
markers. Canonical sources and PDK cards remain unchanged.

Three sequences are exercised: analog first (A), core first (D), simultaneous
(S). The early rail ramps0.5–1.5µs, the delayed rail3–4µs. Input is low during
startup, high6.001–7µs, low afterward. Core supply is removed9–9.5µs while the
analog rail stays powered. Each sequence uses nominal1.2/3.3V, weak-core
1.08/3.6V and strong-core1.32/3.0V. Each run visits27→125→−40→27°C with one
initial seed/reset; 20fF load, 12µs stop, 100ps maximum step, one thread.

| Check | Status | Result |
| --- | --- | --- |
| Nine runs /36 temperature transients | passed | Finite saved vectors through12µs |
| Five settled logic windows per transient | passed | All180 checks; low≤10%VDDA/high≥90%VDDA |
| Exact qualified draw / temperature-return waveform | passed | All32 parameters; all nine return waves identical |
| Original source/model and retained bulk hashes | passed | See [audit](powerorder-audit-20260922.json) |
| Missing-core output characterization | passed | Maximum simulated0.177µV |
| Missing-core signed current characterization | passed | Peak injection into clamped core rail0.468nA; analog draw0.362nA |
| Current/back-powering limit acceptance | not run | No new limit allocated |
| Floating absent rail / actual receiver mismatch | not run | Ideal-clamped absent rail; fixed20fF macro load |
| Physical measurement | not applicable | Simulation only |

The source has TT mismatch models and one draw. These are not process-corner
statistics, terminal-reliability checks, all supply sequences, or wholeV16
closure. Reported currents do not establish floating-rail voltage or safe
injection for connected receivers. No acceptance criterion was relaxed.

Reproduction inside the pinned runtime, fresh mounted output directories:

```sh
python3 designs/g1-guardian/blocks/g1_ctrl/ls/sim/qualification/run_power_order.py --order "$ORDER" --qualification "$RESULTS_ROOT/ls-mismatch-qualify-20260922-r1/qualification.json" --output "$FRESH_OUTPUT"
python3 designs/g1-guardian/blocks/g1_ctrl/ls/sim/qualification/run_power_adverse.py --order "$ORDER" --qualification "$RESULTS_ROOT/ls-mismatch-qualify-20260922-r1/qualification.json" --output "$FRESH_ADVERSE_OUTPUT"
python3 designs/g1-guardian/blocks/g1_ctrl/ls/sim/qualification/audit_power_order.py --results-root "$RESULTS_ROOT" --output "$FRESH_AUDIT_JSON"
```

Use A/D/S. Original nominal runs are`ls-powerorder-a/d/s-20260922-r1`;
adverse parents`ls-poweradverse-a/d/s-20260922-r1` each hold`weak_core` and
`strong_core`. Nominal wrapper times65.516/65.648/63.779s; adverse two-leaf
wrapper times115.787/115.268/116.969s. Each simulator has a180s watchdog.
All bulk waveforms/decks/logs remain outside Git; the audit binds their hashes
and retains the complete per-condition metrics and frozen parameter vectors.

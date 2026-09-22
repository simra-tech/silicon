# Prospective direct-transient HYS prefix revision

The preceding explicitOP→TRAN pilot failed: its Icarus instance could not be
reused, even though the analog solver reached the endpoint and its54 parameter
observations matched. Preserve that failure; it is not analog feedback evidence.

This separate lifecycle revision removes ONLY the explicit `op` and the
pre-transient parameter-print block from the analog control sequence. `setseed
71001`, `reset`, source snapshots, instance names, temperature, sources, stimulus,
tight Gear settings and0.2 ns maximum step remain unchanged. A single direct
transient uses its own internal initial operating point; no `uic`, forced state,
model/card edit or tolerance change is allowed.

The prospective parameter gate is **27 post-transient values exactly matching
the frozen passed seed71001 reference**. An independent before-transient query
on this same simulation instance is **not run**; this revision must never be
reported as54 before/after observations. A separate no-cosim OP, if later used,
is a separate control, not the same-instance before state.

Before an analog rerun, test the direct-transient lifecycle with the actual
timer and imposed comparator signals: add `setseed71001`/`reset` to the previously
passed digital-only control (which already has no explicit OP), require all its
existing functional checks plus byte-identical waveform against that control,
and bind the newly compiled VVP hash to the passing execution. Configuration,
reset/divider, bridges and port ordering remain unchanged.

Only a reviewed0.9 µs prefix with300-second watchdog is planned; no automatic
launch and no3 µs launch follow this contract. Preserve source/model/runtime/
VVP attestation and all finite-waveform, reset/divider/valid digital level,
quiet-code/counter/comparator gates. Prefix success still does not exercise
the1.2 µs HYS event or qualify closed-loop feedback, PVT, skew, FAST or GATE.
Full-loop throughput cannot be inferred from the failed dead-bridge run.

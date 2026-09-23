# Slow-corner calibration continuation

Simulated sample 77101 completed its ten original binary-search calibration
probes. Both observed decision sequences were monotonic. Soft/hard brackets
were 124–125 and 135–136; the unchanged rounding/correction rule froze guard
codes 150/212 and half-millivolt residual codes 125/136. This is calibration,
not a passed adverse-corner accuracy result: the sixty held-out tests remain
in progress, and the remaining 29 samples are not run.

The first two resumed-stage launch attempts failed before creating a leaf
directory or starting ngspice. The archived runner compared in-memory condition
tuples with JSON-decoded lists. Their values and order were identical, but the
Python comparison rejected the representation difference. These failed
launches remain failed preflight attempts, not simulated electrical failures.

`run_joint586_adverse_json_continuation.py` is an explicit continuation adapter,
not a replacement for the frozen runner. It normalizes only the condition
sequence representation, rejects changed values/order, and regenerates all
sixty frozen deck hashes before invoking the original runner. The original
runner, calibration summary, provenance, population vector and held-out plan
remain unchanged. Each new leaf records the adapter hash separately. Three
regression tests cover the original mismatch, rejection of actual value
changes, and all sixty exact deck hashes.

No source, PDK/model, seed, solver, timestep, stimulus, 1.02 µs endpoint,
1,200-second leaf watchdog, parameter inventory, decision rule or acceptance
criterion changed. The full 11,512 parameters and 27 legacy anchors remain
mandatory. Original electrical and numerical failures elsewhere are retained.
This remains model-level characterization, not physical qualification or a
yield claim.

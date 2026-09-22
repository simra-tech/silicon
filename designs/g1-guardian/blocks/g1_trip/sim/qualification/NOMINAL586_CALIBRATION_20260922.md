# Nominal586 one-realization calibration control

The fixed old non-BGR seed71002 realization with nominal586 reference passed
the[50-probe audit](nominal586-calibration-pilot-audit-20260922.json): ten
selected binary-tree probes,22 preserved off-path probes,12 application
guards and six residual points. All8670 non-BGR parameters,2842 nominal BGR
parameters and24 legacy anchors remain exact. Simulated total:20793.840s.

The unchanged binary algorithm gives soft bracket132–133 and hard150–151.
Frozen signed corrections are+5/+23; application codes158/227 and residual
codes133/151. Neither application code clips. All observed calibration probes
are monotonic. No interpolated crossings or off-path selection are used.

All12 application guards and six residual decisions pass at25/−40/125C.
Each decision uses the original three late cycles,20ns after actual comparator
evaluate crossings, with retained legacy samples checked separately. The
executable clock is5MHz, endpoint1.02us; inherited10MHz comments are stale and
were not silently rewritten in hash-bound decks.

This is **one controlled realization**, not joint-mismatch population or yield.
Old-source calibration failures, old codes136/154 failures,10MHz failures and
the prior600s timeout/prefix measurement failure remain unchanged. Existing
model-level physical-fidelity limitations remain; no physical adoption.

Exact commands, sources, runtime and lossless waveform hashes are retained in
the[audit](nominal586-calibration-pilot-audit-20260922.json) and
[portable run receipts](portable_evidence/electrical-r9-20260922).
Read-only reproduction:

```sh
python3 designs/g1-guardian/blocks/g1_trip/sim/audit_nominal586_calibration.py --output NEW_AUDIT.json
```

Built against pinned image manifest5fd78498e578c6e9ec10828c248ca3790fc88250ff6caf545521b29e448ea3c0,
ngspice46 and PDK84374023ee8b4b126bebbba67fcbada0a9c0ff0b, verified through
each probe's full runtime/source/model bindings. New population and final
physical-PEX calibration300: **not run** in this result.

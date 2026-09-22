# Full joint586 transient qualification

All seven controls passed the[strict full-wave audit](joint586-transient-full-audit-20260922.json).
Every phase retained all11512 parameters before/after and matched its qualified
OP realization; all27 legacy anchors and18 finite saved vectors were checked.
Actual-edge and retained legacy late-three-cycle decisions agree.

Decoded waveform bytes, numeric rows and time grids are exactly equal for:

- enabled73001 and its repeat,6600 rows;
- disabled73001 and disabled73002,6571 rows;
- same-instance initial25C and standalone25C,6600 rows;
- same-instance125C and standalone125C,6547 rows;
- same-instance−40C and standalone−40C,6632 rows;
- initial and returned25C after25→125→−40→25,6600 rows.

Maximum node difference on each exact grid is0V. No numerical tolerance replaces
an exact-equality check. The same-instance control took1361.011 simulated-run
seconds, with one reset/seed before all four1.02us phases. Six independent
controls took371.147–778.230s; disabled controls are slower than enabled ones.
All observed soft/hard decisions at codes135/151 and25mV were LOW/LOW. That is
a calibration starting point, not a threshold-accuracy result.

Source/model/runtime bindings are exact: SENSEbaab6183..., TRIPf49e17db...,
enabled BGR7de0fc30... (nominal586 source with1036 mismatch opt-ins). All3500
randomized primitives and11512 parameters were qualified by the separate
[OP controls](JOINT586_OP_20260922.md). The executable clock is5MHz; old10MHz
comments remain stale in immutable source decks. Model warnings are retained,
not converted into model-validity approval.

Built against pinned image manifest5fd78498e578c6e9ec10828c248ca3790fc88250ff6caf545521b29e448ea3c0,
ngspice46 and PDK84374023ee8b4b126bebbba67fcbada0a9c0ff0b.
Exact commands, full parameter arrays, source hashes and raw/gzip waveform
receipts are in[portable evidence](portable_evidence/electrical-r10-20260922).
Read-only reproduction:

```sh
python3 designs/g1-guardian/blocks/g1_trip/sim/audit_joint586_transients.py --prefix joint586-mm-tranqual-20260922-a --output NEW_AUDIT.json
```

Independent calibration population300: **not run to completion** here.
New physical capacitance extraction and final physical qualification: **not run**.
Old-source electrical failures and physical-fidelity limitations remain.

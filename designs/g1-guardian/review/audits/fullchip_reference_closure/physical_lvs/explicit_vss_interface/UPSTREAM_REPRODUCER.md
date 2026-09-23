# Draft technical reproducer: I/O tap geometry and source-body interfaces

Prepared for review; no issue or pull request has been submitted. This describes
observed pinned-public-PDK behavior, not a proposed comparator waiver.

Environment: IHP commit `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`, KLayout
0.30.9, unmodified stock LVS rules, tap extraction enabled.

## Minimal local A/P discrepancy

Use original `sg13g2_LevelUpInv` from the pinned IO GDS and CDL. Its tap record is
`XR0 vss sub! ptap1 A=1.051p P=4.1u`. A separately reversible X-to-R instance-prefix
adapter makes the existing two-terminal primitive visible to the stock reader;
all terminal/model/A/P suffix bytes remain unchanged.

The completed normalized local comparison has a paired tap `MatchWithWarning`:
source A1.051 µm²/P4.1 µm versus native A1.053 µm²/P7.62 µm. Independent raw-layer
geometry yields a hole-free 3.51×0.30 µm rectangle and exactly the native values.
[Actual local comparison](../../../io-tap-binding-lvs-levelup-20260922-r1/tap_warning_analysis.json)
and [pinned parameter/geometry evidence](../../../io_tap_closure/pinned-20260922-r2/summary.json)
preserve the original reports and view hashes.

The pinned reader treats A/P as primary geometric fields. The native primitive
generator derives A/P from actual W/L, while the IO source perimeter resembles
an equivalent-area square. The electrical tap wrapper consumes externally
calculated R. Clarification requested: what physical/electrical interpretation
is intended for the IO tap fields, and which consistent source/native view
should be used? Copying extracted values into a golden reference or disabling
tap extraction would not answer that question.

## Separate substrate interface question

The pinned IO CDL has local `sub!` nodes but no explicit `.GLOBAL` declaration.
Our complete chip contains 245 reachable local body domains/941 terminal
incidences. The native geometry connects these bodies to external VSS; IOVSS
remains a separate metal domain. We have explicitly authorized and documented a
design-local VSS body-port derivative. It resolves the large topology mismatch
and all 22 external pin pairs, but the two combined tap A/P warnings remain.
This is our intentional source-interface choice, not a claim that the original
library already declared global VSS or that it qualifies ESD/latch-up behavior.

Requested clarification is the intended library substrate interface and tap
model geometry, not permission to suppress original mismatches. A proposed
upstream code change requires that interpretation and affected checks first.

# Native supply integration and final routing checkpoint

The seven qualified supply overlays are integrated with the **actual retained
TRIP source**, and the resulting routed/sealed candidate has no disconnected
declared signal or supply terminals. This is not full-chip signoff: stock main
DRC still has the inherited pad failures, strict device-aware LVS failed, and
new fill/PEX/current qualification remains open.

Built against the immutable EDA image config
`ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2`,
IHP SG13G2 PDK `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`, KLayout 0.30.9,
and OpenROAD `26Q1-1024`. Runtime receipts and analysis records bind the
actual commands, input hashes, versions and unchanged stock rule files.

## Exact geometry lineage

| Artifact | SHA256 |
| --- | --- |
| Retained native parent | `9940011f4061ec17815ff65f86c2448ad07145cf6a1d87645f4ab80bbb815669` |
| Seven-overlay supply integration | `c61380a3343c574a5affe21108458f0189c678fa042f43ff7e823ee191699986` |
| Signal-routed native | `b5f8f7ed9388920af19eef19be58ad3eac271aede15b36c93bf76bfb549670b1` |
| Sealed candidate | `3a24f4d76b3d91141d09515e498383ec36bec4f5bbcffbb7a53456f82259c0e9` |

The 1.414 mm square die remains 1.999396 mm². No bondpad coordinates changed.
The separate BGR bias-bypass experiment is **not** in this candidate.

## Integration gates and retained failures

An adversarial synthetic test demonstrated that the old integration checker
could accept a declared but floating added island. The corrected checker
requires every added metal polygon, both faces of every added cut, and every
declared seed to reach the assigned saved native root. Ten controls pass,
including two opposite-layer floating additions captured by an old bare cut.
The original false acceptance and source snapshots remain in the evidence.

The first real merge failed before pruning: the independently qualified
standalone TRIP had upper-layer fill absent from the retained chip source.
The [actual-source audit](sense_power_interface/TRIP_ACTUAL_SOURCE_REVIEW.md)
binds the exact retained subtree and its 56 lower-layer fill removals. The
obsolete 125-polygon standalone ledger was not applied to the chip. The final
merge checks target/source equality before pruning, exact removal geometry,
native functional geometry/text/instances, all 9,324 decap pin pairs, 104
native supply probes, foreign contacts, root closure and frozen input hashes.

| Check on the stated artifact | Status | Evidence/result |
| --- | --- | --- |
| Old checker floating-island rejection | Failed | Original false acceptance retained |
| Corrected synthetic integration controls | Passed | 10 controls; 14.147 s |
| Initial standalone-source chip merge | Failed | Strict source-layer mismatch; no pruning applied |
| Actual-source seven-overlay merge | Passed | 393.777 s; five distinct supply domains |
| Source-bound obstacles/global/detailed routing | Passed | Zero detailed-router markers; 40 nm Metal5 obstacle halo |
| Native streamout and isolated sealring merge | Passed | 223.041/234.618 s; exact saved geometry/text/hierarchy checks |
| Raw terminal-name interpretation | Failed | Eight analog-pad aliases; original raw report retained |
| Source-declared alias interpretation | Passed | 10,222 terminal observations; zero off-metal errors, signal splits or unexpected merges |
| Declared supply-terminal continuity | Passed | VDD 4,877; VSS 4,882; VDDA 11; IOVDD 141; IOVSS 142 observations, each domain one component |
| External port binding | Passed | All 22 logical BTerms / 24 entire pad rectangles; 135.121 s |
| Stock antenna | Passed | Zero markers; 145.002 s wrapper |
| Stock main DRC | Failed | 60 inherited pad markers; exact unchanged marker comparison passed |
| Strict device-aware full-chip LVS | Failed | Actual engine mismatch; saved-database diagnosis is separate |
| New candidate density | Failed | 19 markers; subsequent fill closure is separate |
| Final filled physical/PEX, actual current IR/EM and affected electrical adoption | Not run | No result inherited from an earlier filled geometry |
| Label-based virtual net joining; silicon measurement | Not applicable | Neither performed nor claimed by these geometric checks |

The eight allowed aliases come only from the unchanged analog-pad Verilog
assignments, not from observed shorts. Continuity at declared terminals does
not prove every device/body terminal, current capacity, contact sharing,
electromigration lifetime or parasitic model applicability.

The compact [evidence manifest](final-native-integration-evidence-20260923-r1/manifest.json)
contains exact commands, completed receipts, source snapshots, declared path
normalizations, original/exported hashes and compact reconstruction overlays.
Large native GDS/ODB objects remain hash-bound bulk artifacts. This checkpoint
does not supersede failed physical checks or qualify the circuit for tapeout.

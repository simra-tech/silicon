# G1 native assembly and signal-route integration

These are intermediate physical integration results, not tapeout signoff or
electrical adoption. The original circuit/acceptance criteria are unchanged.
The candidate die is 1414 by 1414 micrometres (1.999396 square millimetres).

## Built against

| Item | Identity and establishment |
| --- | --- |
| IHP SG13G2 PDK | `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`; runtime COMMIT and rule hashes |
| KLayout / pya | 0.30.9; runtime assertion |
| OpenROAD, LibreLane distribution | `26Q1-1024-gdcf36133a`; executable SHA256 `a20f82ef703596ff75e8ddba7a89c8447f62c5113dcb9d8be8740eb229a44ddc` |
| Alternate installed OpenROAD | Different executable/schema; separately tested, not used for this route |
| ngspice | 46; established runtime identity; no new electrical simulation in this milestone |

## Results and boundaries

| Check | Status | Scope |
| --- | --- | --- |
| Decap M2 access | Passed | 9324 native M1/M2 pin pairs, 464 original components, 9756 Via1 cuts; no unexpected original-net merge |
| Decap-access core main/maximal DRC | Passed | Both zero markers; does not establish row-to-ring feeds |
| SENSE r8 in earlier closed core | Passed | Main and maximal zero markers; earlier BGR candidate, not a waiver for a newer assembly |
| Current dual-macro native refresh | Passed | BGR `71892e43…` and SENSE `8060e30a…`, source-native geometry/text preserved, separate supply rings |
| Full component DEF and OpenDB roundtrip | Passed | 4904 instances, 90 logical nets, 10244 terminal connections; original connectivity retained |
| Full native instance assembly | Passed | 4674 core plus 230 IO/glue/filler instances; exact native polygon/text preservation and saved roundtrip |
| First full native stock main DRC | Failed | 66 markers: six NW.b1 glue gaps and 60 Pad.fR recommendations; all remain unwaived |
| First full native maximal DRC | Not run | Main failed |
| Global routing | Passed | 57 routed signal nets, zero overflow, exact instance/terminal graph |
| Detailed routing | Passed | One thread, seed 42, 64-iteration bound; zero router violations |
| Native signal-route streamout | Passed | Stock KLayout DEF/layer mapping; exact added-route union, all 4904 native instances preserved, saved GDS roundtrip |
| Routed stock main DRC | Failed | 60 Pad.fR markers (24 TM1, 36 TM2), 400.47 s stock runtime; earlier six NW.b1 markers cleared, no additional route markers |
| Routed stock maximal DRC | Not run | Main failed; remains an independent required check |
| Full PDN, physical signal connectivity, LVS, PEX, density, antenna, STA and current/IR/EM | Not run | Required independent gates; incomplete power feeds explicitly remain |
| Rule/model-card modifications | Not applicable | None made |

The latest source-preserving routed GDS is
`301cb530b14dd7e36c8a30b7f840aac62295f95642ed9264423de2b455bfc6f7`.
Its native-instance parent is
`8b66a958759478987fa9de59746a0554f9bd065307e730342f10e891082134e6`;
the detailed DEF is
`0e2091e0e03ed321a18a69840ffc1e2997e0ed708f07fa864171baede55b9c84`.
The contiguous-glue preparation cleared the earlier six NW.b1 markers in the
new stock check. All 60 remaining recommended pad-exit markers stay unwaived.

The router sees conservative macro obstacles derived from actual native metal,
plus actual top-level decap access and ring obstacles. BGR's dvbe pin access
was extended only to the boundary of its existing rectangular M3 conductor;
empty egress space was opened without deleting a native obstruction. This
corrected the first detailed-route failure without changing the native pin.
The current signal route precedes complete PDN construction and must be
rechecked/rerouted against the completed power geometry.

## Retained failures

The record retains the decap-generation timeout, old SENSE ring shorts and
spacing violation, wrong decap pin-midpoint and DEF orientation checker
assumptions, unused-route-via lookup collision, fragmented glue placement,
BGR pin-access routing failure, and streamout layer/text-alias checker failures.
Streamout text comparison now uses physical layer/datatype identity rather
than optional LEF display aliases; strings, coordinates and multiplicities
remain exact. The recognized DEF outline is checked against the exact die.

An inward pad-exit trial failed before output: extending a native pad stub
to the required seven micrometres touches another supply conductor. It was
not adopted. Outward bond-pad relocation is a separate proposed bonding-map
change and is not represented as approved or verified here.

## Reproduction and evidence

The helpers in this directory take explicit input/output directories and
require hash-bound parent metadata. The evidence manifest records original
and exported hashes, exact commands, watchdogs, runtime receipts and declared
host-path normalization. Use the pinned image, one CPU per run, and fresh
output directories. Do not run a standalone OpenROAD of another version
against this distribution's OpenDB files. No failed artifact is overwritten.

This milestone does not establish silicon measurements, package effects,
fault survival, radiation qualification, or a completed integrated electrical
campaign. Existing IO-inclusive LVS/model-applicability failures remain open.

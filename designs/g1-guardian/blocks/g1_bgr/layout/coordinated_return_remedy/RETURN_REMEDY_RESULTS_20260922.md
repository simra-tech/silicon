# Source586 return-path diagnostic and common-via candidate

The isolated `bgr-assembly-viaquad-20260922-r3` candidate passes stock DRC
(zero markers, 35.130 s), strict LVS (32 combined devices, 24 nets, nine pins,
all Match, 7.246 s), and independent source-node attribution of all 336 MOS
W/L and junction fields. It has **not** replaced the canonical geometry.

The change replaces 36 two-cut Via2/Via3 arrays at 20 common-return sites
with four-cut arrays and minimum 0.72 µm square M3 landings. There are 72
removed cuts and 144 added cuts. Source586, all 1036 native-device placements,
all text, source CDL and the original hierarchy are preserved. Saved-layer
XOR matches the declared shape ledger; the 55-net terminal graph, seven star
cuts, enclosure, role-clearance and grid/bounds checks passed. No ring or
upper-metal/shared interface was relocated.

## Preserved failures

| Check | Disposition |
|---|---|
| r1 preparation | Failed: flattening retained orphan children, creating multiple top cells. |
| r2 preparation and stock DRC | Passed; DRC zero, 39.825 s. |
| r2 strict LVS | Failed: full flattening triggered removal of the nine all-ground HBT dummies; one device and VSS mismatch. |
| r3 hierarchy-preserving preparation | Passed, 17.138 s; exact declared world-layer geometry retained. |
| r3 stock DRC/LVS and MOS junction attribution | Passed as detailed above. |
| Density, antenna, extracted full resistance and electrical adoption | Not run. |
| Simulation seed | Not applicable to geometry and deterministic sensitivity calculations. |

No rules, model cards, source dimensions, device multiplicities or extraction
reference were changed to make stock LVS pass. The original failed artifacts
remain separate from the successful hierarchy-preserving revision.

## Nominal partial resistance sensitivity—not circuit qualification

The independently supplied source586 nominal 27 °C external-current ledger
contains 76 relevant HBT emitter injections totaling 214.8231815 µA. It is a
common-wrapper inference over 1036 devices, qualified using 22 representative
external port probes (maximum difference 2.694 fA), **not** 1036 individually
metered devices. The aggregate source-node residual is 1.296 pA; no new KCL
acceptance threshold or all-temperature resistor-substrate zero claim follows.

Exact geometry-owned centerline wire trees and all 376 existing ledger
Via2/Via3 cuts are accounted for. Independent branch-current accumulation
agrees with the transfer-matrix calculation. Two pinned resistance tables
differ and are deliberately reported separately: LEF M2/M4 = 0.103 Ω/square,
Via2/Via3 = 20 Ω/cut; installed KPEX = 0.088 Ω/square and 9 Ω/cut. These are
not process corners, a qualified resistance bound, or tunable parameters.

Maximum nominal partial drops, in simulated-current-derived mV:

| Return | LEF original | LEF four-cut | KPEX original | KPEX four-cut |
|---|---:|---:|---:|---:|
| XQ56, 24 emitters | 7.9497 | 5.9683 | 5.1562 | 4.2646 |
| XQ60, 4 emitters | 1.3547 | 1.0239 | 0.8565 | 0.7077 |
| XQ62, 24 emitters | 7.3115 | 5.5339 | 4.7757 | 3.9757 |
| XQ67, 24 emitters | < 1e-10 | < 1e-10 | < 1e-10 | < 1e-10 |

The native emitter/contact/Via1 path, bends and spreading, finite common
hub/general VSS, precision resistor rail, PVT and self-consistent current
redistribution are omitted here. Accordingly these are **partial diagnostic
sensitivities, not full IR drops or an error budget**. Long M2 trunks remain
important: the XQ56 wire-only maximum is 3.9044 mV using LEF resistance.
Further work must close those missing path domains before an electrical
remedy can be qualified. The separate resistor-field CC completeness blocker
also remains unresolved; this via improvement does not address it.

Built against the already pinned image/config `ddeb6957…`, IHP PDK
`84374023ee8b4b126bebbba67fcbada0a9c0ff0b`, KLayout 0.30.9 and KPEX 0.3.12.
Source hashes, exact commands, shape ledgers, tool/rule bindings and original
versus exported artifact hashes accompany the evidence export.

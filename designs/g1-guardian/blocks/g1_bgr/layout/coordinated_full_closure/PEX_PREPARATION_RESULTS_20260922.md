# Coordinated BGR extraction preparation

The exact source/device mapping is verified. A full-macro capacitance netlist
has **not** completed in this milestone. The canonical source and golden layout
are unchanged; no extracted electrical-view adoption is claimed.

Built against pinned ngspice 46, KLayout 0.30.9, KPEX 0.3.12, and IHP PDK
`84374023ee8b4b126bebbba67fcbada0a9c0ff0b`, through the verified amd64 image
`ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2`.
No ngspice simulation was run by this extraction milestone. Raw run commands,
watchdogs, source/support hashes, and output hashes are in its receipts.

## Device and parasitic boundaries

The unchanged canonical source SHA-256 is
`586ffb58b6af31c77a2e7cbcb83b173ffa4713ec62401da30901c5a7e606283b`.
The unchanged golden GDS SHA-256 is
`0083eabb0f730b2cb27eeb0bda1ac8f173a21e03e2aa5a329b01ef5cba21b3ed`.

The installed extractor unconditionally purges nine externally all-grounded
HBT dummies. The derived reference therefore covers **1,027 extracted devices
plus nine independently geometrically verified grounded dummies**, not 1,036
extracted devices. All nine canonical electrical models, including their internal
substrate and thermal networks, remain. See
`GROUNDED_DUMMY_EXTRACTION_20260922.md` for the exact records and exclusion proof.

The canonical source already contains 329 historical `Cext_` parasitics, totaling
399.745776298 fF. Their lines exactly match the pinned prior post-layout source;
no other capacitor statements occur. Adding new CC to these would double-count
parasitics. The initial append-only proposal is superseded by isolated
replacement-only views: preserve all 1,036 device records, remove only those
329 enumerated historical capacitors, and insert the complete mapped new CC.

The old-capacitor line-position reconstruction is byte-identical to source586.
The zero-new-capacitance control is the exact capacitor-free 1,036-device
skeleton, SHA-256
`08f55fa0a1f797f7cbf277e5ca1cffc0eaf1ec3b38be082e071535766e2d98be`.
It is deliberately **not** described as identical to the original 329-C source.

## Completed checks

| Check | Result |
|---|---|
| First unsimplified 1,036-reference LVS | Failed: 1,027 Match, nine reference-only grounded HBTs |
| Nine source records, 36 C/B/E/S probes, native/text parity and installed purge control | Passed |
| First proof reporter | Failed: model-header trailing-space parser; retained |
| Corrected proof reporter | Passed; whitespace-only parser correction |
| Derived-reference original-representation LVS | Passed: 1,027 devices, 55 nets, nine pins, all strict Match |
| Original-representation per-instance source/model/node/WL/AP/HBT/R fields | Passed for all 1,027 extracted devices |
| Full CC original representation, 300 s | Failed: timeout 124 after 300.054 s; no C netlist |
| Full CC original representation, 900 s | Failed: timeout 124 after 900.060 s; no C netlist |
| Historical 329-C provenance, reconstruction and cap-free controls | Passed |
| Capacitor parser/continuation helper unit checks | Passed: eight synthetic tests, not extraction evidence |
| 34-HBT exact-union control geometry and labels | Passed: every layer zero XOR; all 322 texts exact |
| Both 34-HBT control LVS/device-field/node checks | Passed: 34 devices, six nets, six pins each |
| 34-HBT full unpruned CC multiset and matrix parity | Passed: all 21 capacitors exactly equal; no tolerance or pruning |
| Full exact-union geometry and labels | Passed: every layer zero XOR; all 3,285 texts exact |
| Full union-representation LVS and per-instance fields | Passed: 1,027 devices, 55 nets, nine pins; nine geometric dummies separately retained |
| New full-macro CC electrical behavior, wire RC, density and antenna | Not run in this completed preparation milestone |
| External thermal pin of four-port npn13G2; random seed | Not applicable |

The 900 s diagnostic's repeated `Timeout (0:01:00)!` lines are read-only
faulthandler stack snapshots, not additional watchdog failures. They locate the
slow stage at geometric overlap-capacitance extraction. Neither rule decks nor
the installed extractor package were patched.

## Exact-union experiment

The representation experiment unions duplicate/overlapping drawn polygons while
preserving their exact occupied area on every layer and every text string and
position. It does not change the golden GDS or remove device/coupling geometry.
The small control completed CC in 14.022 s before union and 11.699 s after union;
this modest approximately 1.20x result is not a full-macro runtime guarantee.

Full-view M1 polygon count changes from 7,995 to 3,005, M2 from 8,967 to 3,028,
and M3 from 4,405 to 734. M3's largest union polygon has 388 vertices, so reduced
polygon count is not assumed to imply reduced cost. The full union GDS SHA-256
is `8ca01519b43b3fb7cb494131ba8d3280eea23ff8ec47a5c498ecc35f6d82b7cb`;
its audited LVS database SHA-256 is
`6bc87673405b26f4cbc9f23c7ddf77d49c35b2ae12ec70dc0c0786f8d797856f`.
A subsequent bounded union-view full CC run is outside this frozen completed
preparation snapshot and must receive its own disposition.

## Return resistance remains a separate gate

Analytical route-ledger/technology-LEF arithmetic estimates 31.08–42.98 ohms for
the four functional HBT return trunks, 13.78–23.61 ohms for the longest row
segments, and 1.42–1.91 ohms for their star branches. These are **not extracted
RC or full-path bounds**. Native stubs, contacts/vias, spreading, the general-VSS
hub, temperature variation, and current distribution are omitted. Actual IR
error was not simulated here. A geometrically single star connection does not
establish an ideal zero-ohm return or a precision sign-off result.

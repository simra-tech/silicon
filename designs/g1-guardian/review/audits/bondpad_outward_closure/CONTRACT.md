# Outward bond-pad closure contract, 2026-09-23

This candidate moves the 24 bond-pad cells outward by exactly 5.000 µm,
without changing the 1414 × 1414 µm die, circuit, logical pin assignments,
IO-device positions, or other native geometry. The input is the final filled
GDS `4d3907c50f07946ef27a6d53402cf319264499a21379d2de80e9c4f1adbae299`.
It does **not** include the separately investigated IO PolyRes-marker or
dummy-reference candidates.

The pad's passivation opening (9/0), dfpad boundary (41/0), and 132 TopVia2
cuts (133/0) move with each pad. Exact old TopMetal1 frame and TopMetal2
plate geometry is retained in a new bridge cell; this is not a filled
bounding-box approximation. Hence the two metal-layer changes are additive.
The three other pad layers have explicit translated-shape deltas. All native
cell definitions remain unchanged. The old and new pad plates overlap;
actual net connectivity must still be checked, not inferred from overlap.

The bonding map names **physical opening centres**, not old wire anchors.
There are 24 physical pads and 22 logical pins (two VSS and two IOVSS pads).
An isolated unrouted DEF placement/interface projection moves exactly those
24 component origins and 24 BTerm rectangles. All circuit connectivity and
other DEF bytes must recover exactly by reversing those edits. An actual
OpenDB import/roundtrip is a separate check. This projection is not the final
routed OpenDB and does not establish updated pad RC; earlier routed-wire RC
remains historical evidence on its original database.

## Required checks

- Exact original-input hashes and unchanged pinned tools, PDK, and rules.
- Exact inverse movement/removal of the new bridge restores every local
  shape, text, cell and instance transform; serialization preserves the
  candidate. All unchanged cells have exact structural signatures.
- Per-layer geometric delta equals only the declared pad movement/bridge;
  all moved shapes remain inside the unchanged die boundary.
- Actual OpenDB roundtrip: 4904 instances, original nets/connections, only
  24 pad coordinates changed, no source circuit or LEF edit.
- Fresh instance-resolved physical graph: all 10222 ITerm probes, five
  distinct supply roots, no signal/supply split or unexplained merge;
  exactly the eight independently source-declared analog-pad aliases remain.
- All 24 moved BTerm rectangles are covered by actual pad metal and join
  the same source-bound native pad terminals. All 22 external identities
  remain present; no text-driven or name-forced joining is used.
- Unmodified stock full main, maximal, antenna, and density checks. Original
  60 Pad.fR and four Pad.d1R failures remain separate historical results.

Each heavy child gets a fresh 50%-availability resource gate and the single
allocated CPU. Initial bounds: geometry 180 s, OpenDB 300 s, connectivity
600 s, main 600 s, maximal 900 s, antenna 360 s, density 180 s. Failures and
timeouts are retained with unique IDs; output-only harness repairs do not
erase original results. Final acceptance requires actual completed reports,
not successful wrapper exit alone.

## Status at preparation

Geometry generation and every listed check: **not run** at contract freeze.
Measured bonding, package qualification, shifted-pad RC/electrical response,
and full-chip device-aware LVS closure: **not run**. Model/rule changes,
new circuit devices, and unrelated IO-marker adoption: **not applicable**.

## R3 amendment after preserved R2 unit failure

The retained/translated native TM1 frames leave two 0.93 µm gaps per pad:
the 5.00 µm displacement exceeds the native frame's 4.07 µm width. The
unchanged stock unit check reported two `TM1.b` markers (minimum 1.64 µm),
plus three Pad.fR markers in this isolated unit without its IO-cell context.
R2 remains preserved and is not adopted.

R3 replaces the retained-only TM1 bridge with the exact axis-aligned sweep
of the four native frame bars. This fills only movement-created gaps and
retains a central hole; it does not fill the pad bounding rectangle. TM2
retention and all 24 five-micrometre movements are unchanged. Native frame
decomposition must XOR exactly against the original PCell frame before
sweeping. The full layer-delta, inverse, serialization, topology and stock
gates apply afresh. The isolated stock comparison is a notch diagnosis,
not full-chip Pad.fR acceptance.

# Isolated C45/R62 native candidate

This branch implements only the two passive changes in SENSE source
`b8912a862b61554266239634dd388ed0ffad229c0b0e48819ad129d589352e97`:
main `XCC` width 69→45 µm at length 23 µm, and main `XRZ` length 6.2→62 µm
at width 1 µm. Models, transistor identities, buffers and nine external ports
are unchanged. It does not mutate the canonical block or full-chip assembly.

The parent native GDS is
`8060e30ac14a1c4aeb1cf62204c9e95d9a68dbad3d73412fbb34c6a33be8b4f7`.
Original primitive regions must be exact subsets of that parent. Native PCell
GDS round-trip controls establish annotation serialization before replacement.
The resistor rotates 270° so `out1` remains the left terminal; its `cz` contact
joins the existing `cz` M4 bus through a new M1–M3 stack and M3 route. Narrow
M5/TM1 routes join the reduced MIM plates to their retained egress tabs.

Required checks are unchanged active/channel geometry (835 channels), all
134 source-net witnesses, independent 58-MOS native/source dimensions and
centroids, exactly 98 resistors and three MIMs with the new passive dimensions,
exactly nine external ports, 5 nm grid, saved polygon/text round trip, stock
full DRC excluding density, and strict source LVS with nine matching pins.
Primitive-local pin markers change only with the two native templates;
external pin polygons and labels remain held.

Build failures are retained, not replaced. An API rotation-constructor failure,
an API mixed-transform failure, an unsaved-versus-GDS native annotation mismatch,
and an overly broad assertion requiring internal passive pin markers to remain
unchanged all stopped before a candidate was accepted. Their source snapshots
and receipts accompany any later export.

The hierarchy-preserving r9 candidate has GDS SHA
`cec94187d33b60a654cb12213cfb7e0904fc2a0b5d70a3763fd9d223f44d34f7`.
Independent reference r3 **passed**. Stock r2 **passed** full main/maximal DRC
with zero markers (35.140 s wrapper) and strict source LVS with all nine pins
matched (3.934 s wrapper). Original r8 stock **failed** seven M1/via markers:
primitive subtraction clipped two overlapping routing pads. R9 restores only
same-net M1 landing metal. The earlier flattened r7 view failed independent
top-port scope (27 labels instead of nine); r8/r9 preserve the original
hierarchy and change only main-OTA cell shapes/text. Earlier missing MIM
egress and native text-layer failures are also retained.

Full-chip integration, density/antenna, affected fields, and
electrical adoption are **not run** in this isolated branch. Existing 51
stock junction-annotation differences, shared-strip/body attachment questions,
and incomplete MIM extrinsic field coverage remain unresolved; neither native
area arithmetic nor stock LVS waives them. The selected three-case schematic
AC pass is not population qualification or all-PVT/global-loop stability.

## Built against

| Item | Identity |
|---|---|
| PDK | IHP SG13G2 `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`; pinned native PCells and stock decks |
| KLayout | 0.30.9, checked in each geometry command |
| Source | Candidate SHA above; exact two-line inverse to original `baab6183…` |
| Electrical models | Unchanged pinned ngspice models; no model/rule edits |

Commands are `inspect_passive_sites.py`, `build_candidate.py`,
`audit_candidate.py`, and `run_stock.py`, with explicit parent, source and
output paths. They require isolated output directories and preserve input
hashes. Detailed runtime receipts bind the exact commands and source snapshots.

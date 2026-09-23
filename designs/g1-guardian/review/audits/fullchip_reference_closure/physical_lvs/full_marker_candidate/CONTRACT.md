# Source-held full-chip IO marker candidate

Start only from the checked 5 µm outward-pad candidate
`ab02b653c6b0e29e7693bed55e097081e6e41f67e24c59102494e6fbc1724541`.
Keep its 24 opening centres, die, all conductor/cut geometry, native devices,
labels, source circuit, model cards, and unmodified rule decks.

In a separate design-local GDS, add the previously proved PolyRes 128/0
bodies to namespaced copies of SecondaryProtection and RCClampResistor.
The exact native parent cells must first match the pinned public PDK cells
on every polygon layer and all text. Body construction must independently
equal GatPoly ∩ SalBlock ∩ EXTBlock ∩ pSD, match the frozen isolated repaired
cells, and exclude contacts. Expect one 1×2 µm marker per SecondaryProtection
and 26 separate 1×20 µm markers per RCClampResistor. Source-bound expected
reachability is 14 SecondaryProtection and two RCClampResistor occurrences:
66 actual marker rectangles, 1068 µm² total. A different count is a failed
gate, not a new assumption.

Preparation r1 failed before mutation because its name matcher omitted the
native `$1` duplicate aliases. The separate read-only alias audit proves
11+3 SecondaryProtection and 1+1 RCClampResistor occurrences, every alias
exactly matching the stock cell on all layers and text. Revision r2 includes
all four aliases under distinct design-local names, retains the original
14+2 source expectation and requires the passed audit's exact transforms.

This is an actual design-layer change, **not** a claim of mask inertness.
No original PDK library or canonical electrical source is edited. The marker
adds previously missing resistor recognition; it does not alter drawn
resistor material, contacts, device widths/lengths or original R values.

Required preparation evidence: complete cell/source bindings, all-layer
delta, unchanged text and conductors, exact inverse including namespace
restoration, all 24 pad cells/placements held, explicit source-net mappings
and native body/source geometry. Required affected checks: unchanged stock
main/maximal and strict full-chip comparison, with actual reports and
unresolved mismatches retained. Density/antenna applicability must be
established from the pinned decks; if affected, run the same unchanged decks.

The original full-chip reference remains a separate failed control. The
qualified tap-prefix adapter retains every node/model/A/P suffix and has
exact reverse source equality. Separately derived extraction-only references
may exclude exactly the three independently proved all-VDD LevelDown dummy
occurrences, bound to proof `b74ba626…`; all three physical devices and full
canonical electrical source remain. No source A/P copied from layout, rule
tolerance change, global SUB! forcing, virtual same-net hint, or warning
promotion is permitted. Tap A/P and local-vs-common substrate semantics
remain unresolved acceptance blockers.

Initial preparation: CPU1, one thread, fresh coordinated budget ≥44,
180 s bound, 8 GiB reservation (not enforced in rootless cgroups v1), 0.05 GiB
home growth and 2 GiB bulk growth. Each subsequent bounded child needs a fresh
resource gate. Preserve each failure and use a new run ID for corrections.
No full-chip electrical or tapeout adoption follows merely from this repair.

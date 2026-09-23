# Current fullchip reference preparation

Prepare a distinct, non-adopted source-bound reference for the 4,904-instance
round-trip graph. Do not run LVS until the coordinator supplies completed
power/signal geometry. The original IO tap mismatch remains an explicit
failure, not a reason to rewrite a golden source.

Inputs are the unchanged original powered chip netlist (4,884 instances),
the unchanged powered digital macro netlist, pinned original IO/standard-cell
CDL, and the original source-derived references for other macros. Add only
the 20 explicit native filler instances and their source-graph power nets.
Bind the exact current BGR `6d86b9d4...` geometry to local reference
`7f8e6e8c...`, and SENSE `8060e30a...` to local reference `e3e3c22f...`.
The SENSE reference's top name alone is projected from `g1_sense_physical`
to logical `g1_sense`; source hierarchy, pins and device records are held.
No electrical source/model change follows from an LVS reference projection.

Prospective checks:

- Reconstruct BGR local reference exactly from canonical source 586: all
  1,036 primitive records, including nine grounded dummies. Historical
  parasitic capacitors remain outside this physical-device LVS view.
- Reconstruct SENSE's already qualified reference projection exactly from
  source `baab6183...`: primitive X-to-M/R/C conversion, declared ng/mm_ok
  removal, unchanged remaining tokens and hierarchy. Do not infer junction
  A/P or compact-model geometry qualification from strict local LVS.
- Preserve complete original IO and standard-cell CDL bytes. No tap-prefix,
  area/perimeter, substrate-global, model-card, deck or tolerance edit.
- Independently check all 4,884 original instance/master pairs, all named
  source pin connections, all 20 new fillers and all 90 round-trip net names.
  Detect missing/extra pins, unintended floating nets and name collisions.
- Permit only the eight previously documented analog pad/padbare aliases,
  justified by unchanged library assignments, not extracted short results.
  Bondpads remain declared metal-only cells, not omitted instances.
- Independently parse the emitted top, digital macro and copied cell bodies;
  verify instance/pin/net mapping, port order and exact model/parameter tokens.
  Report projection scope separately from physical connectivity and LVS.

One-thread CPU0 preparation/audit, maximum 180 seconds per process, 2 GiB RAM
reservation and 0.10 GiB external output bound after fresh resource checks.
Retain every failed unique output. No analog, layout modification, device
replacement, golden-reference overwrite, rule changes or new qualification.

# Actual retained TRIP source binding

The first chip integration failed source equality on Metal4 fill. This failure
is retained; standalone qualification was not qualification of the retained
chip fill view.

The exact three-way audit shows delivered chip `38c1d6d1` TRIP equals retained
parent `9940011f` TRIP on every polygon layer and all texts. Standalone `c99f3ae1`
differs only in datatype22 fill: its Metal4/Metal5 fill areas are 12,510 and
14,661 square micrometres; both are absent in the delivered/retained view.
All functional geometry and Metal1–Metal3 fill are identical.

The r4 isolated source is an exact saved copy of the actual parent subtree,
not an edited golden layout. Its unchanged source CDL remains SHA256
`60a9ad6e3744ff0b3dcd407a78febcb49315840a65fdf8ef851032d6e88bfd76`.
The same positive-metal recipe is applied to this separately bound source.
Only 56 actual fill polygons intersect its pinned 0.42 micrometre spacing
halos: 10 Metal2 and 46 Metal3, none Metal4. Affected fill-only arrays are split
into their exact surviving repetitions. Functional instances, child geometry,
all non-fill layers, and all texts remain held.

The reusable pruning helper requires the caller's explicit qualified source
hash for this variant. Its default remains the original standalone binding.
The chip integrator must first prove exact target/source equality and then
apply the source-bound repetition ledger; importing a replacement functional
TRIP hierarchy is not permitted.

Run-specific stock/LVS, saved-view and pruning-control statuses are recorded
in the r4 evidence receipts. Whole-chip final context, density/refill and
near-fill PEX remain separate checks, not inherited from isolated results.
No current-sharing, contact capacity, PVT/IR/EM or adoption claim is made.

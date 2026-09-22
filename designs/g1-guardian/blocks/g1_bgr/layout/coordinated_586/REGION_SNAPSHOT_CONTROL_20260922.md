# Immutable geometry snapshot control

The first eight-MOS prototype generation completed, but its added-body-Activ
audit reported zero for every tile. That audit is **failed**, not a qualified
source/diffusion-preservation result. Original r1 scripts/GDS/manifest remain.
Native channel and junction dimensions were evaluated before mutation; no
stock DRC/LVS or complete prototype adoption was claimed.

A pinned KLayout0.30.9 synthetic reproduction creates one10×10-DBU rectangle,
constructs a Region from a recursive shape iterator, then adds another disjoint
10×10 rectangle. Both old Region.area() and an explicitly flattened copy report
100, but subtracting the old iterator-backed Region from the new live geometry
returns area0; subtracting the flattened snapshot returns the expected100.
Thus the old area cache did not establish an immutable pre-mutation polygon
snapshot. Runtime stdout: `before 100 100`, then `after 100 100 0 100`.

The separate r2 generator materializes each native Region with `dup(); flatten()`
before adding geometry and requires positive added-body-Activ area plus no
interaction with the frozen native source/drain Activ. All physical recipes and
source parameters remain unchanged. This is an analysis repair, not a PDK edit.
Require r1/r2 generated nontext geometry XOR0 before transferring any later
stock result between them. Full contact electrical connectivity, stock checks,
all1,036-device placement and full well/guard/PDN fit remain **not run**.

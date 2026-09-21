# Assembled G1 design snapshot

`g1_chip_top.gds` is a byte-identical copy of the assembly-1350 final GDS
from `../flow/runs/assembly-1350/final/gds/`. SHA-256:

`38c1d6d13bbfee4ed0e3c01477742c3d2d28317d9215d9e5bd9a35551285ae59`

Die: 1350 × 1350 µm. This is a review snapshot, not signed-off tape-out data.
Hard-rule DRC, density and core-only LVS passed. IO-inclusive LVS, antenna,
recommended-rule checks and streamout comparison have unresolved failures.
See `../reports/assembly-1350/` and `../INTEGRATION.md` for check scope.
Netlist: `../netlist/g1_chip_top.cdl`. No geometry changes were made for this copy.

# Assembled G1 design snapshot

`g1_chip_top.gds` is a byte-identical copy of the assembly-1350 final GDS
from `../flow/runs/assembly-1350/final/gds/`. SHA-256:

`38c1d6d13bbfee4ed0e3c01477742c3d2d28317d9215d9e5bd9a35551285ae59`

Die: 1350 × 1350 µm. This is a review snapshot, not signed-off tape-out data.
Hard-rule DRC, density and core-only LVS passed. IO-inclusive LVS, antenna,
recommended-rule checks and streamout comparison have unresolved failures.
See `../reports/assembly-1350/` and `../INTEGRATION.md` for check scope.
Netlist: `../netlist/g1_chip_top.cdl`. No geometry changes were made for this copy.

## 1414 µm artifact of record (2026-09-24)

The owner selected the 1414 × 1414 µm native-lineage chip as the tape-out
artifact of record. It supersedes `g1_chip_top.gds` (1350 µm review snapshot,
kept unchanged above) as the file to check and submit.

| File | SHA-256 | Top cell |
|---|---|---|
| `g1_chip_top_1414_src.gds` | `60730627d24e1fb6b880138edc3e50fdd7c14624bb2dfbbc631e084b7415eca1` | `placed_core_NOT_CONNECTED_FULLCHIP` (byte copy of the selected candidate) |
| `g1_chip_top_1414.gds` | `629d303abf594ec90593f1d28a8d9ad19673ea6662780ba428a6d9c5685986ba` | `g1_chip_top` (top cell renamed only; geometry identical) |

`g1_chip_top_1414.gds` was written by `../flow/signoff/1414/rename_top.py`
(no GDS timestamps, so the bytes are reproducible). `../flow/signoff/1414/verify_rename.py`
confirmed that the geometry is identical. Netlists are in `../netlist/g1_chip_top_1414*.cdl`.
Sign-off results are in `../reports/signoff-1414-20260924/README.md`.
The legacy name `placed_core_NOT_CONNECTED_FULLCHIP` is only a name. The routed
and filled lineage is recorded in the design history.

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

## Revision r2: file of record (2026-09-25)

`g1_chip_top_1414_r2.gds` is the **file of record** and supersedes `g1_chip_top_1414.gds` (r1).
r1 is kept unchanged.

| File | SHA-256 | Status |
|---|---|---|
| `g1_chip_top_1414_r2.gds` | `9049e87b0303893573ed82f56a5d41f926c4db126e8d972062553c7d19996d2c` | **file of record**, top `g1_chip_top`, 306 cells, 84 500 300 bytes |
| `g1_chip_top_1414.gds` (r1) | `629d303abf594ec90593f1d28a8d9ad19673ea6662780ba428a6d9c5685986ba` | superseded |

r2 was written from r1 by `../flow/signoff/1414r2/make_r2.py`, without GDS timestamps; two writes
were byte-identical. It changes metadata only:

- the two seal-ring registration texts on TEXT 63/0 in the top cell now read
  `Device registration size: x=1414.0 um ; y=1414.0 um` / `Calculated area: 1.999396 sq mm`
  (from the EdgeSeal boundary) and `PDK version: IHP-Open-PDK 84374023ee8b4b126bebbba67fcbada0a9c0ff0b`,
  with the same position, layer and size;
- three modified cells that carried stock PDK names were renamed: `sg13g2_LevelDown` →
  `g1_LevelDown_polyres` (it carries 2 µm² PolyRes), `nmos` → `g1_gate_nmos` and
  `pmos` → `g1_gate_pmos` (PCell variants in the GATE block that differ from the `sg13g2_pr` defaults).

`../flow/signoff/1414r2/verify_r2.py` and `gds_record_diff.py` prove that nothing else changed:
the per-layer XOR is empty on all 73 layers, and the cell count, hierarchy and instance tree are
identical apart from the renames. Canonical netlist for r2: `../netlist/g1_chip_top_1414_r2.cdl`
(same sub-circuit rename). The projected reference `../netlist/g1_chip_top_1414_projected_ref.cdl`
is unchanged. Sign-off: `../reports/signoff-1414r2-20260925/README.md`.

# Isolated R0.95 full-chip preparation

Structural preparation passed; this is not production adoption or circuit
qualification. Only the OSC direct geometry is replaced. All 305 other cells,
58 retained fill instances, top-level name and 1414 µm square die boundary are
unchanged, including after GDS readback. The full-chip source changes only the
two charging resistor lengths, from 117 µm to 111.15 µm.

| Check | Status |
| --- | --- |
| Hash-bound source transformation and four negative/unit controls | passed |
| Direct geometry, retained hierarchy and emitted-GDS structural checks | passed |
| Eight pinned KLayout primitive/hierarchy controls | passed |
| Initial flat-macro assumption | failed; corrected after hierarchy inspection |
| Initial SimplePolygon copy representation | failed; corrected without geometric relaxation |
| New full-chip physical/electrical acceptance | not run to completion at this checkpoint |
| Production adoption | not run |
| Hardware measurement for this preparation-only change | not applicable |

No PDK rules or model cards were changed. Full-chip DRC, density, antenna, LVS
and affected electrical campaigns remain required. Stock main DRC was running
at this checkpoint; no outcome is inferred from structural preparation.

## Built against

| Component | Identity and establishment |
| --- | --- |
| IHP SG13G2 public PDK | `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`; pinned runtime COMMIT check |
| KLayout | 0.30.9; verified pinned image and executed eight KLayout fixtures |
| Image config | `ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2` |
| Image amd64 manifest | `5fd78498e578c6e9ec10828c248ca3790fc88250ff6caf545521b29e448ea3c0` |

## Reproduction

Run from the OSC layout directory using the pinned image. Input identities and
output hashes are recorded in the adjacent preparation reports; supply those
exact inputs at local paths. Bulk GDS/CDL outputs are not duplicated here.

```sh
python3 -m unittest test_osc_r095_fullchip_source.py
klayout -b -r test_osc_r095_fullchip_geometry.py
python3 prepare_osc_r095_fullchip_source.py --source CURRENT.cdl --output CANDIDATE.cdl --report SOURCE.json
klayout -b -r prepare_osc_r095_fullchip_geometry.py -rd chip=CURRENT.gds -rd baseline=BASELINE.gds -rd candidate=BARE_R095.gds -rd out=CANDIDATE.gds -rd report=GEOMETRY.json
```

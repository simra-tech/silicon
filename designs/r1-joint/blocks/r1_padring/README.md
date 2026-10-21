# R1_PADRING

Block `r1_padring` (track T6). This block builds the pad ring of the R1 chip: 24 pads, empty core.

## Revision b (1600 um)

State 2026-10-21: **the 1600 um ring is the ring of record**, run `ring-20261021-b`. It follows decision D10
(`../../PLAN.md` section 2a and `../../specification/studies/S6_FLOORPLAN.md`). It is a reference for chip assembly.
It is not a tape-out file and it has no core.
The 1414 um ring (revision a, section "Revision a (1414 um, superseded)" below) stays in the tree as the superseded record.

Result in one paragraph. Main DRC, maximal DRC, precheck DRC and density (with fill) pass with 0 markers.
The bond-map check passes: 24 of 24 openings. The core window is 878.6 x 875.1 um (0.769 mm2).
The antenna check fails with 12 markers, the same 12 as revision a (empty core).
The LVS results are worse than revision a. The ring-only projected LVS **fails** (259 of 261 devices, 116 of 119 nets; revision a: 261 of 261, 119 of 119).
The G1-form projected LVS fails as in revision a, with counts that differ by one. The canonical LVS fails in the same 12 circuits as revision a.
I did not find the cause of the ring-only difference (see "Failures and mistakes", item 2).

### What changed against revision a

| Item | Revision a (1414 um) | Revision b (1600 um) |
| --- | --- | --- |
| Die, EdgeSeal 39/4 | 0 to 1414 um | 0 to 1600 um |
| IO cells | 24, same types, order and orientation | the same 24 (`reports/ring-20261021-b/compare_order.json`: identical) |
| Pad pitch, pad centres | 112 um; 395, 507, 619, 731, 843, 955 | 140 um, row centred; 450, 590, 730, 870, 1010, 1150 |
| Pad centre from the edge | 101 um (south, west) | 101 um (south, west); 1499 um (north, east) |
| Corner cells | 180 x 180 um at 141 and 1093 | 180 x 180 um at 141 and 1279 |
| IO row inner edge | 321 um (south, west), 1093 um (north, east) | 321 um (south, west), 1279 um (north, east) |
| IO fillers | 112 cells (20 / 10 / 2 um) | 132 cells (92 x `Filler4000`, 32 x `Filler400`, 8 x `Filler200`); every gap is filled |
| Seal ring, core power ring, registration texts | 1414 um | stretched by 186 um at the die centre line; texts read 1600.0 um and 2.560000 sq mm |
| Core power ring width and spacing | as G1 r4 | unchanged (same rectangles, longer) |
| Pin map | specification section 3 | unchanged. The optional S6 pin-map change is not applied |

### How the ring was made

The script `flow/build_ring_1600.py` reads the 1414 um ring before fill (`r1_padring_nofill.gds` of run `ring-20261020-a`).
It makes the 1600 um ring in these steps.

1. Move the IO cells, bondpad cells, the TopMetal2 pad squares and the TopMetal1 bridge shapes of each pad to the new pad centre.
   The cell types, the order and the orientation do not change.
2. Move the four corner cells. Map all top-level shapes (seal ring, Passiv ring, EdgeSeal, core power ring, TopVia2 array)
   with the rule: a coordinate of 707 um or more moves by +186 um.
3. Delete the 112 IO fillers. Write new fillers in every gap with the same orientation per side as in revision a.
   A gap of 60 um uses 3 x `Filler4000`. A gap of 89 um (corner to first IO cell) uses 4 x `Filler4000`, 4 x `Filler400` and 1 x `Filler200`.
   The 89 um gap is odd. The 1 um filler is the PDK cell `sg13g2_Filler200`, copied under the name `retained_fullchip_sg13g2_Filler200`.
4. Write the 22 net labels (134/25) and the 24 pad labels of `new_signal_routes` at the new centres. Change the registration text.
5. Run the PDK filler script (Activ/GatPoly, Metal1-5, TopMetal1/2) on the empty core. Write the GDS without timestamps (`flow/rewrite_gds.py`).

`flow/run_signoff.sh` ran the checks with the revision a commands. In revision b the two LVS runs go in parallel with the DRC runs.
I ran the steps one by one with the commands in `reports/ring-20261021-b/run.json`.

### Ring reference (identity)

| Item | Value |
| --- | --- |
| Ring GDS | `r1_padring_1600.gds`, run `ring-20261021-b`, in `<G1_RESULTS_ROOT>/r1_padring/ring-20261021-b/`. Not in the tree (47 MB) |
| SHA-256 | `40514b4f4ff7888ac0ca95329470e47c8c93c1b3efc7fec1bee2f646b8dbac19` (unchanged after all checks: `<G1_RESULTS_ROOT>/r1_padring/ring-20261021-b/signoff/input_gds.sha256` and `.after`) |
| Cells, top cell, size | 63 cells, one top cell `r1_padring`, bbox 0,0 to 1600,1600 um, database unit 1 nm |
| Same ring before fill | `r1_padring_1600_nofill.gds`, `edd52b57cfb1156d555713a56bd8cbc227067de3f71e62e2b6c33d86d3d4b39a` (bulk only) |
| Source | `r1_padring_nofill.gds` of run `ring-20261020-a`, `6d8a34d04c9e5d03d6fbfcdb0a6d8d07d113a9abd289fc88f6fd353232ffc730` |
| LEF reference | [`layout/r1_padring_1600_ref.lef`](layout/r1_padring_1600_ref.lef) (`flow/make_lef.py <out> 1600`) |
| Netlists | the revision a netlists apply without change: the cells, their order and their nets are the same |
| Bond map and plan | [`../../padframe/`](../../padframe/README.md): `bondmap_r1_1600_ring.csv`, `bondplan_r1_1600.svg`, `bondplan_r1_1600.json` |
| Screenshot | [`reports/ring-20261021-b/r1_padring_1600.png`](reports/ring-20261021-b/r1_padring_1600.png) (249 kB, 700 x 700 px) |

### Core window (KLayout measurement, `reports/ring-20261021-b/measure_ring_1600.json`)

| Edge | IO row inner edge (um) | Core power ring inner edge (um) |
| --- | ---: | ---: |
| West | x = 321.0 | x = 361.8 (TopMetal1 column) |
| East | x = 1279.0 | x = 1240.42 (TopMetal1 column) |
| South | y = 321.0 | y = 362.16 (TopMetal2 row) |
| North | y = 1279.0 | y = 1237.3 (TopMetal2 row) |

The core window inside the ring is x = 361.8 to 1240.42 um, y = 362.16 to 1237.3 um. Size 878.62 x 875.14 um = **0.769 mm2**.
This equals the conservative window of S6 (878.6 x 875.1 um). The IO row window is 958 x 958 um = 0.918 mm2.
The extended window of S6 (analog macros under the core ring, from 331 um) is 0.880 mm2. It was not measured on this GDS.
The ring conductors carry no net name in this GDS (same as revision a). The ring has no TopVia1.

### Status (revision b)

| Check | Status | Evidence |
| --- | --- | --- |
| Ring built: die 1600 x 1600 um, EdgeSeal 0..1600, 24 IO cells, 4 corners, 24 bondpads, seal ring, core ring | passed | `reports/ring-20261021-b/build_ring_1600.json`, `measure_ring_1600.json` |
| Same 24 IO cells in the same order and orientation as revision a | passed | `reports/ring-20261021-b/compare_order.json` (`identical_order_type_orientation: true`) |
| Corner cells, IO cells and IO fillers continuous on all four sides (no gap, no overlap, 141 to 1459 um) | passed (geometric abutment) | `measure_ring_1600.json` (`row_continuous_all: true`). Rail connectivity by extraction: not shown, the ring-only LVS failed |
| Bond map against the GDS (24 openings, size 65.8 um, TopMetal2 enclosure, dfpad, labels, die size, hash) | passed | `reports/bondmap/verify_bondmap_r1_1600.json` (`all_ok: true`, 24 of 24, 22 labels) |
| Bond plan: 0 wire crossings | passed | `../../padframe/bondplan_r1_1600.json` |
| PDK fill (Activ/GatPoly, Metal1-5, TopMetal1/2) | passed | `reports/ring-20261021-b/fill.log`; density below |
| KLayout main DRC (`run_drc.py`, deep, no density, no extra rules) | **passed**, 0 items, 561 rule categories, 179.5 s | `reports/ring-20261021-b/drc_main/`, `drc_summary.json` |
| KLayout maximal DRC (`sg13g2_maximal`, G1 wrapper) | **passed**, 0 items, 272 categories, 271.8 s | `reports/ring-20261021-b/drc_maximal/` |
| KLayout precheck DRC (`--precheck_drc --disable_extra_rules`, with density) | **passed**, 0 items, 455 categories, 107.3 s | `reports/ring-20261021-b/precheck/` |
| Density with fill | **passed**, 0 items, 7 categories | `reports/ring-20261021-b/density/`; values below |
| DRC density waivers | none needed | no density item |
| KLayout antenna | **failed**, 12 items (4 x `Ant.e_Metal5`, 4 x `Ant.e_TopMetal1`, 4 x `Ant.e_TopMetal2`) | `reports/ring-20261021-b/antenna/`; same cause as revision a: empty core, no gate load on `vdd` |
| LVS, projected reference, G1 form (`netlist/r1_padring_projected_ref.cdl`) | **failed** (as revision a): 209 of 261 devices match, 1 with warning; 58 of 119 nets match (revision a: 210 and 59) | `reports/ring-20261021-b/lvs_projected/`. Cause of the revision a failure: empty core, substrate not tied to `VSS`. The difference of one device and one net is not explained |
| LVS, projected reference, ring-only form (`netlist/r1_padring_ringonly_projected_ref.cdl`) | **failed**: 259 of 261 devices match, 2 tap devices with warning; 116 of 119 nets match. The 3 nets are the substrate net `$1` (`SUBSTRATE_NODE`), `VSS` and `IOVSS`. Revision a passed 261 of 261 and 119 of 119 | `reports/ring-20261021-b/lvs_projected_ringonly/` (`diagnosis.txt`). Cause not established |
| LVS, canonical reference (`netlist/r1_padring.cdl`) | **failed** (known): 14 circuit pairs, 12 NoMatch, 2 Skipped, 0 Match. Same as revision a | `reports/ring-20261021-b/lvs_canonical/` |
| Hash of the ring GDS unchanged by the checks | passed | `<G1_RESULTS_ROOT>/r1_padring/ring-20261021-b/signoff/input_gds.sha256`, `.after` |
| LibreLane `Chip` flow | not applicable | the ring is a hand-assembled lineage, as revision a |
| IHP `dev` branch DRC deck on this ring | not run | not repeated for R1 |
| Magic DRC, Magic or netgen LVS | not run | known library failures on G1 |
| IHP submission intake pre-check | not run | ring only; run it on the full chip. The registration texts read 1600.0 um |
| Full-chip PEX, IR drop, EM, ESD or latch-up simulation | not run | no core |
| Identity of the core ring nets (`VDD` or `VSS` per conductor) | not run | as revision a |
| Design-local copy of `sg13g2_IOPadTriOut4mA` with PolyRes 128/0 | not run | only needed if SLO and SDO are bused |
| Optional S6 pin-map change on the west side | not applied | the owner brief says: do not apply |
| Measurement | not run | no silicon |

Density with fill (die area 2 560 000 um2): Activ 50.21 % (limit 35 to 55), GatPoly 17.88 % (min 15), Metal1 52.68 %, Metal2 45.25 %,
Metal3 52.84 %, Metal4 52.47 %, Metal5 52.83 % (limit 35 to 60), TopMetal1 53.52 %, TopMetal2 50.62 % (limit 25 to 70), LBE 0 % (max 20).

### Built against (revision b)

| Item | Value | How established |
| --- | --- | --- |
| PDK | IHP-Open-PDK `84374023ee8b4b126bebbba67fcbada0a9c0ff0b` | `flow/run.sh` stops if `/foss/pdks/ihp-sg13g2/COMMIT` differs |
| Container image | `tapeoutbench-eda:latest`, `sha256:ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2` | `flow/run.sh` identity check |
| KLayout | 0.30.9 | DRC and LVS logs |
| Rule decks | stock PDK `run_drc.py`, `run_lvs.py`, decks unmodified | invoked from `/foss/pdks/ihp-sg13g2/libs.tech/klayout/tech/` |
| ngspice, xschem | not applicable | no simulation or schematic in this block |
| LibreLane | not used | see "Status" |
| Source ring | `r1_padring_nofill.gds` of `ring-20261020-a`, `6d8a34d0…` | SHA-256 of the file |
| CPUs | 116-119 (`G1_CPUSET`, `G1_CPUS=4`) | `reports/ring-20261021-b/run.json` |

### Failures and mistakes (revision b)

| # | Class | What happened | Effect and fix |
| --- | --- | --- | --- |
| 1 | spec-ambiguity | S6 gives pad centres 450 to 1150 um (centred row). That makes a gap of 89 um between a corner and the first IO cell. The filler cells have widths 20, 10 and 2 um, so an odd gap needs a 1 um cell. S6 did not say this. | Used the PDK `Filler200` (1 um). The pads stay centred. The other choice was a 1 um shift of the row (gaps 88 and 90 um) |
| 2 | regression | In try 1 (GDS `16ba76ab…`) the 1 um filler kept the PDK name `sg13g2_Filler200`. The canonical LVS then paired this cell with the reference and reported one more NoMatch circuit (13 instead of 12). | Renamed the copy `retained_fullchip_sg13g2_Filler200`, like the other filler copies. The canonical LVS is back to 12 NoMatch. Rebuilt, refilled and re-ran every check. Try 1 stays in `<G1_RESULTS_ROOT>/r1_padring/ring-20261021-b-try1/` (DRC 0 items there too) |
| 2b | regression | The final ring-only projected LVS fails (3 nets: `$1`, `VSS`, `IOVSS`; 2 tap devices with a warning). Revision a passed. The G1-form LVS shows one device and one net more mismatch. The device and net counts per net are equal in layout and reference. The layout shows source and drain of the `sg13_hv_nmos` devices on `VSS` and `IOVSS` in the other order than the reference, which should not matter. Only the pad positions, the filler cells and the die size changed. | **Not resolved.** I had no time left to find out if this is a graph-matching ambiguity of the LVS tool or a layout fault. A test is needed: LVS of the revision a ring-only GDS with the 1 um filler added, or of a 1600 um ring with a 1 um row shift and no `Filler200`. Evidence: `reports/ring-20261021-b/lvs_projected_ringonly/diagnosis.txt` |
| 3 | estimation | I planned the LVS runs as 10 minutes each from revision a. On the busy server one run took 34 minutes. Try 1 and the re-run together used about 2 hours 30 minutes, not 2 hours. | Ran the three LVS in parallel on the re-run |
| 4 | tooling | The first inspection script was in `/tmp`. The container mounts only the repository, so it did not start. | Put scripts in `flow/`. The inspection scripts were deleted after use, except `flow/inspect_fillers.py` |
| 5 | tooling | `G1_WORKDIR` is the block directory. The first measure run used a repository-relative output path and failed. | Used paths relative to the block directory |
| 6 | verification-gap | The first `flow/compare_order.py` sorted pad 1 of the old ring into the wrong side. It reported "not identical" for a ring that was identical. | Classified the side by the position relative to the die centre. Result now `true` |
| 7 | tooling | The first screenshot at 1000 px was 514 kB (limit 300 kB). | 700 px gives 249 kB |
| 8 | process-hygiene | I stopped the try 1 ring-only LVS by killing its own process ids (SIGTERM did not stop it; SIGKILL did). No other process was touched. | Recorded here. The try 1 ring-only result does not exist |
| 9 | process-hygiene | The first draft of `flow/build_ring_1600.py` had dead code from editing. | Removed before the build that counts |

### Open items (revision b)

1. Find the cause of the ring-only LVS failure (item 2b) before the ring is used as an LVS reference for the chip.
2. Place the core in the 878.6 x 875.1 um window. Run all checks on the full chip with the G1 form of the projected LVS.
3. The antenna check, the pad 18 cell decision, the ring net identity and the intake pre-check stay as in revision a (below).
4. Re-run the bond plan on the chip GDS. The package paddle for a 1.6 mm die is not checked (S6 lists it as not run).

---

# Revision a (1414 um, superseded)

Block `r1_padring` (track T6). This block builds the pad ring of the R1 chip: 24 pads, 1414 um die, empty core.
State 2026-10-20: **ring reference built and checked, run `ring-20261020-a`**. It is a reference for chip assembly.
It is not a tape-out file and it has no core.

Result in one paragraph. Main DRC, maximal DRC, precheck DRC and density (with fill) pass with 0 markers.
The antenna check fails with 12 markers: the empty core has no gate load on the `vdd` net (a control proves this).
The G1-form projected LVS fails for the same reason (the substrate is not tied to `VSS`).
The ring-only projected LVS passes (261 of 261 devices, 119 of 119 nets, 22 of 22 named ports).
The canonical LVS fails in the same IO cells as on G1 (known PDK reason).

## Ring reference (identity)

| Item | Value |
| --- | --- |
| Ring GDS | `r1_padring_a.gds`, run `ring-20261020-a`, in the bulk results root `r1_padring/ring-20261020-a/`. Not in the tree (47 MB) |
| SHA-256 | `3a477ab4534834cd8e551d6f3d1e3be5ed90a7851957fb505564c868a8eee0f0` (unchanged after all checks: `reports/ring-20261020-a/input_gds.sha256.after`) |
| Size, cells, top cell | 47 233 086 bytes, 63 cells, one top cell `r1_padring`, bbox 0,0 to 1414,1414 um, database unit 1 nm |
| Same ring before fill | `r1_padring_nofill.gds`, `6d8a34d04c9e5d03d6fbfcdb0a6d8d07d113a9abd289fc88f6fd353232ffc730` (bulk only) |
| LEF reference | [`layout/r1_padring_ref.lef`](layout/r1_padring_ref.lef), `04123bfa72e73ea52ce113f33288d70e62c9aa900e6c6f051f20b0b419c14160`. Die size, 22 pins (24 TopMetal2 pad squares), the core power ring as obstructions. A script writes it: `flow/make_lef.py` |
| Canonical netlist | [`netlist/r1_padring.cdl`](netlist/r1_padring.cdl) `8a28d3d7…` |
| Projected references | [`netlist/r1_padring_projected_ref.cdl`](netlist/r1_padring_projected_ref.cdl) `cd127125…` (G1 form); [`netlist/r1_padring_ringonly_projected_ref.cdl`](netlist/r1_padring_ringonly_projected_ref.cdl) `32e94246…` (ring-only form). Sources: `netlist/*_projection_src.cdl` |
| Bond map and plan | [`../../padframe/`](../../padframe/README.md) |

## How the ring was made

The G1 ring of record is `designs/g1-guardian/blocks/g1_padring/layout/g1_chip_top_1414_r4.gds`
(SHA-256 `225d0b535321ed312594bb13d97b7271014f487162564a56c874572de715173a`).
Its IO cells are design-local copies of the PDK `sg13g2_io` cells. They carry PolyRes 128/0 for resistor recognition.
Its bondpads sit 5 um further out than the PDK default, with a TopMetal1 bridge to the IO cell stub.
The G1 1414 um chip is not a LibreLane output. It is a hand-assembled lineage. So this block does not rerun LibreLane.
It reuses the G1 r4 ring cells directly. The script `flow/build_ring.py` does the following.

1. Read the G1 r4 GDS.
2. Keep the 4 corner cells, the 112 IO filler cells, the 24 bondpad cells, the cell `bondpad_outward_5um_retained_metal`
   and the TopMetal2 pad squares, pins and labels of the cell `new_signal_routes` (only shapes outside the core box).
3. Replace the IO cell of each pad slot with the cell type of the R1 pin map. All IO cell types have the same
   80 x 180 um outline and the same orientation on a given side, so every slot keeps its place.
4. Delete the macros, standard cells, core routing, the VDDA grid and all old fill.
5. Keep the seal ring, the two registration texts (63/0) and the core power ring (4 TopMetal1 columns, 4 TopMetal2 rows,
   TopVia2 at the crossings). Delete the TopVia1 array of the ring, because it only joined the ring to the macro Metal5 grid.
6. Write one label per net on the first pad of the net (22 labels, same rule as G1 r4), and one label per pad in `new_signal_routes`.
7. Remove cells that no instance uses any more (304 cells become 63).

Then the PDK filler script (`libs.tech/klayout/tech/scripts/filler.py`: Activ/GatPoly, Metal1-5, TopMetal1/2) fills the empty core.
A rewrite without timestamps gives the final bytes (`flow/rewrite_gds.py`).
`flow/run_ring_r1.sh` lists the full command sequence. I ran the steps one by one with these commands. I did not run the chained script as one piece.
`flow/run_signoff.sh` runs the checks with the same commands and options as the G1 r4 sign-off
(`designs/g1-guardian/blocks/g1_ctrl/flow/eco/run_candidate.sh`, function `signoff`), except the thread count: 4 for density, antenna and precheck (G1 used 2). The thread count does not select rules.

Cell types in the R1 ring: 1 x `IOPadVdd`, 2 x `IOPadVss`, 1 x `IOPadIOVdd`, 2 x `IOPadIOVss`, 9 x `IOPadAnalog`
(pads 7-11 and 21-24), 4 x `IOPadIn` (pads 16, 17, 19, 20), 2 x `IOPadOut4mA` (pads 12 and 18), 3 x `IOPadOut30mA` (pads 13-15).
There is no `IOPadOut16mA`. Pad 18 (`SLO` / `SDO`) uses `IOPadOut4mA`.
**If the SLO and SDO lines are bused with other drivers, use `sg13g2_IOPadTriOut4mA` on pad 18.**
All `sg13g2_IOPad*` cells are 80 x 180 um (G1 README), so the slot does not change. The PDK CDL has `sg13g2_IOPadTriOut4mA`.
The tri-state cell needs a design-local copy with PolyRes 128/0, like the other IO cells. That copy does not exist yet.
The ring GDS does not contain it.

## Pad table

IO cell origins and orientations are those of the G1 ring (cell outline 80 x 180 um, origin = lower-left corner of the unrotated cell).
The pad centre is the centre of the 70 x 70 um TopMetal2 bondpad and of its 65.8 um passivation opening.

| Die pad | Net | IO cell | Side | Cell origin x, y (um) | Orientation | Pad centre x, y (um) |
| ---: | --- | --- | --- | --- | --- | --- |
| 1 | `VDD` | IOPadVdd | south | 355, 141 | R0 | 395, 101 |
| 2 | `VSS` | IOPadVss | south | 467, 141 | R0 | 507, 101 |
| 3 | `IOVDD` | IOPadIOVdd | south | 579, 141 | R0 | 619, 101 |
| 4 | `IOVSS` | IOPadIOVss | south | 691, 141 | R0 | 731, 101 |
| 5 | `VSS` | IOPadVss | south | 803, 141 | R0 | 843, 101 |
| 6 | `IOVSS` | IOPadIOVss | south | 915, 141 | R0 | 955, 101 |
| 7 | `VDDA` | IOPadAnalog | east | 1273, 355 | R90 | 1313, 395 |
| 8 | `ISA_P` | IOPadAnalog | east | 1273, 467 | R90 | 1313, 507 |
| 9 | `ISA_N` | IOPadAnalog | east | 1273, 579 | R90 | 1313, 619 |
| 10 | `ISB_P` | IOPadAnalog | east | 1273, 691 | R90 | 1313, 731 |
| 11 | `ISB_N` | IOPadAnalog | east | 1273, 803 | R90 | 1313, 843 |
| 12 | `FAULT_N` | IOPadOut4mA | east | 1273, 915 | R90 | 1313, 955 |
| 13 | `GATE_A` | IOPadOut30mA | north | 355, 1273 | M0 | 395, 1313 |
| 14 | `GATE_B` | IOPadOut30mA | north | 467, 1273 | M0 | 507, 1313 |
| 15 | `GATE_C` | IOPadOut30mA | north | 579, 1273 | M0 | 619, 1313 |
| 16 | `CS_N` | IOPadIn | north | 691, 1273 | M0 | 731, 1313 |
| 17 | `MA_SCLK` | IOPadIn | north | 803, 1273 | M0 | 843, 1313 |
| 18 | `SLO_SDO` | IOPadOut4mA | north | 915, 1273 | M0 | 955, 1313 |
| 19 | `SDI` | IOPadIn | west | 141, 355 | M45 | 101, 395 |
| 20 | `EN_STO_IN` | IOPadIn | west | 141, 467 | M45 | 101, 507 |
| 21 | `SIN_P` | IOPadAnalog | west | 141, 579 | M45 | 101, 619 |
| 22 | `SIN_N` | IOPadAnalog | west | 141, 691 | M45 | 101, 731 |
| 23 | `COS_P` | IOPadAnalog | west | 141, 803 | M45 | 101, 843 |
| 24 | `COS_N` | IOPadAnalog | west | 141, 915 | M45 | 101, 955 |

The IO cell names in the GDS are `retained_fullchip_sg13g2_IOPad<type>` (the G1 r4 copies).
The net names replace "/" with "_" (`MA_SCLK`, `SLO_SDO`, `EN_STO_IN`).
The origin and orientation of the cell types were read from the G1 r4 GDS. They are the same for every type on one side.
The pad centre and the opening were measured again on the R1 GDS (`reports/bondmap/verify_bondmap_r1.json`).
The pad-side pins `c2p`, `p2c` and `padres` of the cells have no connection. The core will connect them.

## Ring geometry

| Item | Value | How established |
| --- | --- | --- |
| Die | 1414 x 1414 um, EdgeSeal boundary (39/4) 0..1414 | GDS |
| Seal ring | metal 32.2 to 1381.8 um, Passiv ring 25 to 1389 um (copied from G1 r4) | GDS shapes |
| Corner cells | 4 x `sg13g2_Corner` 180 x 180 um, lower-left corners at (141,141), (1093,141), (141,1093), (1093,1093) | GDS |
| IO row | 24 cells, 80 x 180 um, pitch 112 um, first cell at 355 um; row inner edge 321 um (south, west) and 1093 um (north, east) from the lower-left origin | GDS |
| IO fillers | 112 cells: 40 x `Filler4000`, 28 x `Filler2000`, 44 x `Filler400` | GDS |
| Bondpads | 24 x `bondpad_70x70_tm1`, TopMetal2 pad 70 x 70 um (66 to 136 um from the edge), Passiv opening 65.8 um, centres at 101 um (south, west) and 1313 um (north, east) | GDS, bond map check |
| Core power ring | TopMetal1 columns x = 324.82 to 339.82, 344.82 to 361.8, 1054.42 to 1069.42, 1074.42 to 1089.42 um (y = 321 to 1093); TopMetal2 rows y = 327.16 to 342.16, 347.16 to 362.16, 1051.3 to 1066.3, 1071.3 to 1086.3 um (x = 328 to 1086) | GDS shapes (build script lists them) |
| **Core window** | free inside the ring: **x = 361.8 to 1054.42 um, y = 362.16 to 1051.3 um**, 692.6 x 689.1 um = **0.477 mm²** | derived from the ring edges |
| Ring to IO row | IO row inner edge 321 um; ring outer edge 324.8 um (west) | GDS |

Macros of G1 r4 sat from 331 um (analog macros under the core power ring; measured in S6, run `g1check`), the digital inside the conservative window. The R1 specification budget is about 0.45 to 0.50 mm² of macros (section 4).
The window is therefore **marginal** for the R1 macro budget, as the specification says.
The ring carries no net name in this GDS. I did not extract which ring conductor is `VDD` and which is `VSS`
(a probe of the LVS database returned the substrate net on every layer; not pursued). The LEF lists the ring as obstructions.
The ring has no TopVia1 and so no connection to Metal5.

## Status

| Check | Status | Evidence |
| --- | --- | --- |
| Ring assembled to the R1 pin map (24 pads, 4 corners, 112 fillers, 24 bondpads, seal ring, core ring, empty core) | passed | `reports/ring-20261020-a/build_ring.json` |
| Bond map against the GDS (24 openings, size, TopMetal2 enclosure, dfpad, labels, die size, hash) | passed | `reports/bondmap/verify_bondmap_r1.json` (`all_ok: true`) |
| PDK fill (Activ/GatPoly, Metal1-5, TopMetal1/2) | passed | `reports/ring-20261020-a/fill.log`; density check below |
| KLayout main DRC (`run_drc.py`, deep, no density, no extra rules) | **passed**, 0 items, 561 rule categories, 146.7 s | `reports/ring-20261020-a/drc_main/` |
| KLayout maximal DRC (`sg13g2_maximal`, via the G1 wrapper `run_maximal.py`) | **passed**, 0 items, 272 categories, 208.4 s | `reports/ring-20261020-a/drc_maximal/` |
| KLayout precheck DRC (`--precheck_drc --disable_extra_rules`, with density) | **passed**, 0 items, 455 categories, 98.2 s | `reports/ring-20261020-a/precheck/` |
| Density with fill | **passed**, 0 items, 7 categories | `reports/ring-20261020-a/density/`; values below |
| KLayout antenna | **failed**, 12 items | `reports/ring-20261020-a/antenna/`; cause below |
| LVS, projected reference, G1 form (`netlist/r1_padring_projected_ref.cdl`) | **failed** | `reports/ring-20261020-a/lvs_projected/` (`diagnosis.txt`); cause below |
| LVS, projected reference, ring-only form (`netlist/r1_padring_ringonly_projected_ref.cdl`) | **passed** | `reports/ring-20261020-a/lvs_projected_ringonly/`; details below |
| LVS, canonical reference (`netlist/r1_padring.cdl`) | **failed** (known) | `reports/ring-20261020-a/lvs_canonical/`; details below |
| Antenna control: G1 r4 without decap cells | passed as a control (reproduces the markers) | `reports/ring-20261020-a/control_antenna_g1r4_nodecap/` |
| CDL projection method control (G1 r3) | passed (output equals the G1 r3 projected reference byte for byte) | `reports/ring-20261020-a/control_cdl_g1r3/` |
| Hash of the ring GDS unchanged by the checks | passed | `reports/ring-20261020-a/input_gds.sha256`, `.after` |
| LibreLane `Chip` flow | not applicable | the G1 1414 um ring is not a LibreLane output; the flow was not used |
| IHP `dev` branch DRC deck on this ring | not run | G1 ran it on r3 and r4; not repeated for R1 |
| Magic DRC, Magic or netgen LVS | not run | G1 recorded these as failing for library reasons; not repeated |
| IHP submission intake pre-check | not run | the ring has one top cell and the G1 registration texts (63/0, 1414.0 um); no other intake item was checked |
| Full-chip PEX, IR drop, EM, ESD or latch-up simulation of the IO cells | not run | no core, no model for the design-local IO copies beyond G1 |
| Identity of the core ring nets (`VDD` or `VSS` per conductor) | not run | see "Ring geometry" |
| Design-local copy of `sg13g2_IOPadTriOut4mA` with PolyRes 128/0 | not run | only needed if SLO and SDO are bused |
| Measurement | not run | no silicon |

### Density with fill (`reports/ring-20261020-a/density/…_density.log`, die area 1 999 396 um²)

| Layer | Density | Limit |
| --- | --- | --- |
| Activ | 49.74 % | 35 to 55 % |
| GatPoly | 17.03 % | min 15 % |
| Metal1 | 52.22 % | 35 to 60 % |
| Metal2 | 44.77 % | 35 to 60 % |
| Metal3 | 53.19 % | 35 to 60 % |
| Metal4 | 52.88 % | 35 to 60 % |
| Metal5 | 53.18 % | 35 to 60 % |
| TopMetal1 | 53.59 % | 25 to 70 % |
| TopMetal2 | 51.16 % | 25 to 70 % |
| LBE | 0 % | max 20 % |

### Antenna: 12 items

All items are `Ant.e_Metal5`, `Ant.e_TopMetal1` and `Ant.e_TopMetal2`, 4 pads each: the receiver gates of the four `IOPadIn`
cells (pads 16, 17, 19, 20). The gate ties to the `vdd` rail of the cell. The deck adds the metal of the whole `vdd` net
(Metal1 to Metal5: 20 727.6 um²) and divides it by the gate area on the net. The limit is 20 000 with a diode.
The empty core has no other gate on the `vdd` net, so the ratio is above the limit.
G1 r4 passes (0 items) because its 4662 decap cells put a large gate area on `vdd`.
Control: G1 r4 with only the decap cells deleted gives 9 items (3 `IOPadIn` x 3 rules)
(`control_antenna_g1r4_nodecap/`, input `4390d7c4…`). This supports the cause. It does not prove that the R1 core will clear the rule.
**Disposition:** expected to clear when the core adds gate load on `vdd` (decap or tie cells). Re-run the antenna check on the full chip.
This is the same deck interaction that G1 recorded for its ring-only runs (`g1_padring/reports/antenna_reference/`).

### LVS, projected reference, G1 form: failed

Command: `run_lvs.py --run_mode deep --top_lvl_pins --spice_comments`. The reference is the G1 recipe: the canonical CDL
without the dummy PMOS `MP0` of the `LevelDown` derivative, flattened (`flow/make_cdl.py`, `flow/flatten_reference.rb`).
The recipe is checked: applied to the G1 r3 canonical CDL it gives the G1 r3 projected reference byte for byte.
Result: 210 of 261 devices and 59 of 119 nets match. All mismatches sit in cells where the layout substrate net `$1` is separate
from `VSS` (`diagnosis.txt`: tap, antenna diode and NMOS bulk terminals). In the reference, the substrate pin of every IO cell is tied to `VSS`.
The cause is the empty core. The IO cells mark their p-taps with the `sub!` label, so the deck extracts them as `ptap1` devices.
The deck joins the substrate to a metal net only through ordinary p-taps (`connect(pwell, ptap)`, `connect(ptap, cont_drw)`),
which the G1 core cells supply and this ring does not.

### LVS, projected reference, ring-only form: passed

The reference differs in one point: the substrate node of every ring cell is a separate internal net `SUBSTRATE_NODE`, not `VSS`
(`netlist/r1_padring_ringonly_projection_src.cdl`, 140 instance lines changed by `flow/make_cdl.py`).
Result: "Congratulations! Netlists match." 261 of 261 devices, 119 of 119 nets. The 22 named ports match by name.
The layout also reports 18 pins without a reference partner: the floating pad-side nets `padres` (9), `p2c` (4) and `c2p` (5)
(`lvs_projected_ringonly/pins.txt`). The comparison does not flag them (`pair_counts.json`: pin Match 40). G1 shows 22 pins
because its core connects these nets.
The ring-only form is a variation of the G1 method, not the G1 method. Use the G1 form on the full chip.

### LVS, canonical reference: failed

14 circuit pairs: 12 NoMatch, 2 Skipped (`r1_padring` and `sg13g2_GateLevelUpInv`), 0 Match.
The 12 NoMatch circuits are the 14 of G1 r4 (`g1_LevelDown_polyres`, the clamps, `DCNDiode`, `DCPDiode`, `LevelUpInv`,
`RCClampInverter`) without `Clamp_N8N8D` and `Clamp_P8N8D`, which only the 16 mA pad uses. The cause is the IO-cell reference
semantics of the PDK (G1 record R13; upstream issues in `designs/g1-guardian/review/upstream/evidence/README.md`).

## Built against

| Item | Value | How established |
| --- | --- | --- |
| PDK | IHP-Open-PDK `84374023ee8b4b126bebbba67fcbada0a9c0ff0b` | `flow/run.sh` stops if `/foss/pdks/ihp-sg13g2/COMMIT` differs |
| Container image | `tapeoutbench-eda:latest`, `sha256:ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2` | `flow/run.sh` identity check |
| KLayout | 0.30.9 (Ruby 3.2.3 in the DRC logs) | `klayout -v`; DRC and LVS logs |
| Rule decks | stock PDK `run_drc.py`, `run_lvs.py`, decks unmodified | invoked from `/foss/pdks/ihp-sg13g2/libs.tech/klayout/tech/` |
| ngspice | not applicable | no simulation in this block |
| xschem | not applicable | no schematic in this block |
| LibreLane | 3.1.0.dev2 is in the image; not used | see "How the ring was made" |
| Source ring | G1 r4 `225d0b53…` | SHA-256 of the file in the tree |
| CPUs | 116-119 (`G1_CPUSET`, `G1_CPUS=4`) | `run.json` |

Run records: [`reports/ring-20261020-a/run.json`](reports/ring-20261020-a/run.json) and the two control `run.json` files.
Paths of the bulk results root in the copied logs read `${RESULTS_ROOT}`.
The `lvsdb` files (155 MB each) stay in the bulk results root.

## Files

| Path | Content |
| --- | --- |
| `flow/build_ring.py` | builds the ring from the G1 r4 GDS (cell swap, core removal) |
| `flow/rewrite_gds.py` | timestamp-free rewrite |
| `flow/make_cdl.py` | writes the canonical CDL, the G1-form projection source and the ring-only projection source |
| `flow/flatten_reference.rb` | copy of the G1 flatten script (`g1_ctrl/flow/eco/`), unchanged |
| `flow/run_signoff.sh`, `flow/run_maximal.py`, `flow/lvs_pair_counts.py`, `flow/verify_bondmap.py` | copies of the G1 sign-off helpers, paths adapted |
| `flow/lvs_diag*.py`, `flow/lvs_pins.py`, `flow/text_scan.py`, `flow/strip_cells.py` | diagnostics and the antenna control |
| `flow/make_lef.py` | writes `layout/r1_padring_ref.lef` |
| `flow/run_ring_r1.sh` | the command sequence of run `ring-20261020-a` |
| `layout/r1_padring_ref.lef` | LEF reference |
| `netlist/` | canonical CDL, projection sources, flat projected references (with their `.json` records) |
| `reports/ring-20261020-a/` | logs, lyrdb reports, pair counts, `run.json` per run |
| `reports/bondmap/` | bond map check (`verify_bondmap_r1.json` for revision a, `verify_bondmap_r1_1600.json` for revision b) |
| `flow/build_ring_1600.py`, `flow/measure_ring_1600.py`, `flow/compare_order.py`, `flow/screenshot_ring.py`, `flow/summarize_lyrdb.py` | revision b: build, geometry measurement, order check, PNG, marker count per rule |
| `flow/inspect_fillers.py`, `flow/lvs_netdiff.py`, `flow/lvs_netterms.py` | revision b diagnostics (filler cells, LVS net mismatch) |
| `layout/r1_padring_1600_ref.lef` | LEF reference of revision b |
| `reports/ring-20261021-b/` | revision b: logs, lyrdb reports, `run.json`, `measure_ring_1600.json`, PNG |

## Open items for the next steps

1. Place the core. Re-run all checks on the full chip with the G1 form of the projected LVS.
2. Re-run the antenna check on the full chip. Add decap or tie cells if the 4 `IOPadIn` markers remain.
3. Decide `IOPadOut4mA` or `IOPadTriOut4mA` for pad 18 (bus decision). For the tri-state cell, build a design-local copy with PolyRes 128/0.
4. Find out which ring conductor is `VDD` and which is `VSS` before the core supply straps are drawn.
5. Run the IHP intake pre-check on the full chip, not on the ring.

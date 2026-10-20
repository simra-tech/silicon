# R1_PADRING

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
| `reports/bondmap/` | bond map check |

## Open items for the next steps

1. Place the core. Re-run all checks on the full chip with the G1 form of the projected LVS.
2. Re-run the antenna check on the full chip. Add decap or tie cells if the 4 `IOPadIn` markers remain.
3. Decide `IOPadOut4mA` or `IOPadTriOut4mA` for pad 18 (bus decision). For the tri-state cell, build a design-local copy with PolyRes 128/0.
4. Find out which ring conductor is `VDD` and which is `VSS` before the core supply straps are drawn.
5. Run the IHP intake pre-check on the full chip, not on the ring.

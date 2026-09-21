# G1_PADRING

State: **1350 × 1350 µm ring (`PLAN.md` D13) assembled through the LibreLane `Chip` flow;
KLayout DRC (hard rules) 0 markers and density 0 markers after fill; KLayout
antenna, Magic DRC and LVS fail for the library/deck reasons given in
"Checks". Assembly of record with all twelve macros and the VDDA supply (D14):
KLayout DRC 0 (hard rules and precheck), density 0, routing DRC 0, PDN
connected on VDD/VSS/VDDA, STA clean with the digital owner's SDC, supply nets
isolated (three geometric checks), core-only KLayout LVS **passed (52 circuit pairs matched)**
(`INTEGRATION.md`, `reports/assembly-1350/`). The first assembly run passed
all flow checks with VDDA, VSS and VDD shorted together by the supply straps;
only the core-only LVS found it (`reports/assembly-1350-r1/`, `INTEGRATION.md`
"Shorts found by the core-only LVS")**. The die carries the 24 `sg13g2_io` pads of the
specification pin map, four `sg13g2_Corner` cells, IO fillers, a 70 µm bondpad
per pad, the core power ring and a placeholder core (one flop, three gates)
so that every digital pad is driven or loaded. No G1 function is implemented
here; `rtl/g1_core_placeholder.sv` is the module the block macros replace.

Built against PDK commit `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`
(`/foss/pdks/ihp-sg13g2/COMMIT` inside the pinned container, see `PLAN.md`
section 2). Tool versions are taken from the run logs, see "Tool versions".

## What is here

| Path | Content |
| --- | --- |
| `rtl/g1_chip_top.sv` | chip top: 24 pad instances named `padNN_<pin>` (pin number of the specification), supply pads with `(* keep *)`, pin 7 `pad07_vdda` = analog pad whose `padbare` is the VDDA supply net (D14), measurement pads on `padbare`, TRIP_SET/VREF on `padres`, placeholder core instance |
| `rtl/g1_core_placeholder.sv` | placeholder core: `GATE = EN`, `FAULT_N = ~EN`, `SDO = SDI` registered on `SCLK`, `TEMP_OUT = EN & SDI`; analog terminals accepted, unconnected |
| `flow/config.yaml` | LibreLane `Chip` flow configuration (relative `dir::` paths, PDK defaults for libraries and corners) |
| `flow/g1_chip_top.sdc` | constraints: 10 MHz clock at `pad14_sclk/p2c`, IO delays on the digital pads |
| `flow/sealring_g1.py` | seal-ring driver replacing the PDK script (work-around, see "Surprises") |
| `flow/lvs/pnl2cdl.py` | converts the flow's powered Verilog netlist to CDL (PDK stdcell + IO CDL appended) for the KLayout LVS deck |
| `flow/config_dryrun.yaml`, `flow/pdn_cfg_g1.tcl`, `flow/analog_straps.tcl` (+ `_standalone.tcl` wrapper), `flow/macro_gds_assembly/`, `rtl/g1_core_dryrun.sv`, `rtl/bb/`, `../../../../flow/run_dryrun.sh` | chip assembly with all macros of record (floorplan, VDDA grid and feed, via stacks onto the macro supply bars with obstruction checks, macro GDS preparation), see `INTEGRATION.md` |
| `flow/lvs/` | `assemble_chip_cdl.py` (chip CDL from the flow netlist + PDK + macro CDLs), `core_cdl.py` / `core_only_gds.py` / `run_core_lvs.sh` / `xref_summary.py` (core-only KLayout LVS and its per-circuit summary), `pdn_net_overlap.py` / `pdn_macro_overlap.py` / `supply_isolation.py` (geometric short checks of the supply nets: between nets, onto macro and IO-cell metal, metal-only connectivity of the chip pins), `pnl2cdl.py` (ring-only CDL) |
| `flow/signoff/signoff.sh` | sign-off of an assembly run beyond the flow's steps (DRC with recommended rules, precheck DRC, density table, antenna marker list, the three supply short checks, core-only LVS) and evidence collection into `reports/<run tag>/` |
| `netlist/` | `g1_chip_top.pnl.v`, `g1_chip_top.nl.v` (flow), `g1_chip_top.cdl` (assembled) |
| `ip/sg13g2_io_padbare/` | LEF/Verilog/liberty views of the PDK IO library with the analog pad's resistor-free core terminal exposed as `padbare` (derived from the PDK files by script; GDS/CDL stay stock), README there |
| `INTEGRATION.md` | how macros are dropped into the ring, power for 1.2 V and 3.3 V macros, the `g1_digital` dry run |
| `ip/bondpad_70x70_tm1/` | bondpad generated from the PDK `bondpad` PCell, LEF, README |
| `reports/run-1350/`, `reports/run-1200/`, `reports/run-1130/` (no `layout/`: the final GDS is about 50 MB, above the 20 MB copy limit; it stays under `flow/runs/<tag>/final/gds/`, sha256 in each `final_gds.sha256`) | logs and reports copied from the two runs (see "Checks"); `run1_*` are from the first 1130 µm attempt with the Metal3-stack bondpad and the PDK seal-ring script |
| `../../../../flow/run_ring.sh` | the exact command sequence (bondpad generation, LibreLane run) |

## Command

```
flow/run_ring.sh
```

which runs, inside the pinned container (`flow/run.sh`, working directory
`designs/g1-guardian/blocks/g1_padring`):

```
KLAYOUT_PATH=$PDK_ROOT/$PDK/libs.tech/klayout klayout -zz -nc -n sg13g2 \
    -r ip/bondpad_70x70_tm1/gen_bondpad.py -rd output=ip/bondpad_70x70_tm1/gds/bondpad_70x70_tm1.gds
librelane flow/config.yaml --pdk ihp-sg13g2 --pdk-root /foss/pdks --manual-pdk --run-tag ring-1350 --overwrite
```

The run directories `flow/runs/<tag>/` are gitignored; the evidence listed under
"Checks" is copied to `reports/`.

## Ring geometry

| Item | 1350 µm frame (current, `PLAN.md` D13) | 1200 µm frame | 1130 µm frame | Established by |
| --- | --- | --- | --- | --- |
| Die (`DIE_AREA`) | 1350 × 1350 µm | 1200 × 1200 µm | 1130 × 1130 µm | config; `DIEAREA` in `padring.def` |
| Seal ring | PDK `sealring` PCell geometry (`edgeBox` 25 µm, Passiv ring 25–29.2 µm, metal/via ring 32.2–36.4 µm inside the die edge, EdgeSeal boundary = die outline); 1000 µm PCell ring stretched by 300 µm | stretched by 150 µm | by 80 µm | `sg13g2_tech.json`, `sealring_code.py`, `klayout-sealring.log` |
| Corner cells | 4 × `sg13g2_Corner` 180 × 180 µm at (141, 141), (1029, 141), (141, 1029), (1029, 1029) | at 140.5 / 879.5 | at 140.5 / 809.5 | `padring.def` |
| Edge spacing (`PAD_EDGE_SPACING`) | 141 µm | 140.5 µm | 140.5 µm | config (PDK default 140); chosen so the row ends land on the 1 µm site grid |
| IO cells | 24 × `sg13g2_IOPad*` 80 × 180 µm, six per side, **pitch 112 µm** (first pad at 355 µm, then 467, 579, 691, 803, 915) | pitch 91 µm (first pad 332.5) | pitch 81 µm (first pad 322.5) | `padring.def` |
| Fillers | 32 µm between pads, 34 µm at row ends: 28 × Filler4000, 28 × Filler2000, 36 × Filler400 | 11 µm / 12 µm: 28 × Filler2000, 20 × Filler200, 8 × Filler400 | 1 µm / 2 µm: 20 × Filler200, 8 × Filler400 | `padring.def` |
| Bondpads | 24 × `bondpad_70x70_tm1`, 70 × 70 µm, TopMetal1 + TopVia2 + TopMetal2, Passiv opening 65.8 µm, offset (5, −70) from the IO cell, 71–141 µm from the die edge | 70.5–140.5 µm | same | `ip/bondpad_70x70_tm1`, `openroad-padring.log` |
| IO-row inner edge | 321 µm from the die edge | 320.5 µm | 320.5 µm | edge spacing + 180 |
| Core window (`CORE_AREA`) | [364, 364, 986, 986] = **622 × 622 µm** (0.387 mm²), 43 µm to the IO row; OpenROAD snaps the lower-left to (366.24, 366.66) | [364, 836]² = 472 × 472 µm | [366, 764]² = 398 × 398 µm | config; floorplan warning IFP-0028 |
| Core power ring | TopMetal1 vertical / TopMetal2 horizontal, 2 × 15 µm, 5 µm spacing, 4.5 µm offset, connected to the pads | same | same | `PDN_CORE_RING_*` |
| Pad opening to EdgeSeal | 73.1 − 36.4 = 36.7 µm (rule Pad.d 7.5 µm, recommended 25 µm) | 36.2 µm | 36.2 µm | derived |

Pad placement arithmetic (`librelane/scripts/openroad/common/pad_cfg.tcl`,
logged in `reports/run-1350/openroad-padring.log`):

```
side  = 1350 - 2 x 141 - 2 x 180 = 708 um
fill  = 708 - 6 x 80 = 228 um
gap   = floor(228 / 7 / PAD_SPACING_MULTIPLE) x PAD_SPACING_MULTIPLE = 32 um   (MULTIPLE = 1)
ends  = (228 - 5 x 32) / 2 = 34 um                                              on the 1 um IO-site grid
(with the previous edge spacing of 140.5: side 709, fill 229, gap 32, ends 34.5 -> off grid, hence 141)
(1200 um frame: side 559, fill 79, gap 11, ends 12;  1130 um frame: side 489, fill 9, gap 1, ends 2)
```

Why 1200 µm did not hold: the macros laid out so far (digital 360 × 360,
sense 252 × 189, trip 229 × 207, osc 166 × 138, bandgap 84 × 124, T2F
92 × 103, gate 131 × 51) total 0.274 mm² against the 0.223 mm² core window of
the 1200 µm frame; the 622 µm window of the 1350 µm frame holds them at 71 %
(`INTEGRATION.md`).

### Why the die is not 1000 × 1000 µm

The specification allocates 1000 × 1000 µm. With six 80 µm pads and two
corners per side (2 × 180 + 480 = 840 µm) that leaves 80 µm per side for the
sealring region and the bondpad. In this PDK:

- the stock `sg13g2_IOPad*` cells have **no passivation opening** (no `Passiv`
  9/0 shapes in `sg13g2_io.gds`); each exposes a 70 × 3 µm `pad` stub on
  Metal2…TopMetal2 at its outer edge and the PDK's LibreLane configuration
  places an external `bondpad_70x70` at offset (5, −70), outside the cell;
- the sealring metal ends 36.4 µm inside the die edge and the pad opening must
  keep 7.5 µm (Pad.d; 25 µm recommended for wire bonding) from it;
- the IO cell's TopMetal2 is fully used by the ring supply rails (8.5–132.5 µm),
  so a bondpad cannot sit over the cell.

Hence the IO row cannot start closer than 36.4 + 7.5 − 2.1 + 70 ≈ 112 µm (hard
rules) or ≈ 129 µm (recommended) from the edge, and the smallest legal die is
about 1073 µm (hard) or 1108 µm (recommended) with the 1 µm supply fillers.
1130 µm keeps IHP's default 140 µm inset and the recommended pad-to-seal
distance; it is the same frame as IHP's own 24-pad reference
(`OCDCPro-padframe/24`: 1120 µm, pads abutted).

## Sources

| Repository (commit) | Licence | Used for |
| --- | --- | --- |
| iic-jku/ihp-sg13g2-ams-chip-template (`6524ffdd`) | Apache-2.0 WITH SHL-2.1 | config pattern (`PAD_*`, core ring PDN, `MAGIC_EXT_UNIQUE`, `Checker.IllegalOverlap` substitution), pad idiom, base SDC (adapted); its bondpad GDS as XOR cross-check; the `padbare` idea for `sg13g2_IOPadAnalog` (our views are re-derived from the PDK files by `ip/sg13g2_io_padbare/make_padbare_views.py`, nothing copied); its final chip GDS and older IO GDS as antenna-deck references. Its bondpad IP was not copied. |
| ChipDesign-BV/pad-ring-ihp (`6d0f4882`) | Apache-2.0 | placement arithmetic, flat pad naming |
| IHP-GmbH/OCDCPro-padframe/24 (`0c9ff61b`) | see repo | die-size reference (1120 µm), bondpad naming |
| IHP-Open-PDK `libs.tech/klayout/tech/scripts/{bondpad,sealring}.py` | Apache-2.0 | bondpad generation; seal-ring script interface |

Nothing from these repositories is copied into this directory; the bondpad and
seal ring come from the PDK PCells through the scripts in this directory.

## Surprises about the IO cells and the PDK

1. **No bondpad in the IO cells.** See above. `pad-ring-ihp`'s README states the
   opposite for PDK `144f811c`; at `8437402` the GDS has no Passiv shapes.
2. **Antenna markers on every `sg13g2_IOPadIn` — a library-revision artefact.**
   The PDK antenna deck reports `Ant.e` (cumulative metal to gate ratio
   ≥ 20 000, with diode) once per input pad (EN, SCLK, SDI): a gate at cell
   coordinates (41.5–42.0, 161.6–166.3) µm is contacted to the cell's `vdd`
   rail, so the deck sums the ring's `vdd` rail metal against it (24 503 µm² at
   1130 µm, 27 624 µm² at 1200 µm). It is independent of the bondpad (same
   with the Metal3 stack, the TopMetal1 stack, or no bondpads). The same deck
   gives 0 items on the iic-jku template's final chip and 0 items on the G1
   ring itself when only `sg13g2_IOPadIn` is replaced by the template's older
   cell revision; the two revisions differ only in the input-receiver region
   ("I/O Update 2"). Evidence and the question for the foundry:
   `reports/antenna_reference/README.md`.
3. **Seal-ring PCell broken above 1000 µm.** `SG13_dev/sealring` with
   `w`/`l` > 1000 µm returns shapes at −2³¹ dbu and no straight sides (tested
   1000 OK, 1001…2649 broken, any unit spelling). The PDK script asks for
   die − 50 = 1080 µm, and the degenerate `EdgeSeal` layer then crashes all
   three PDK fill macros (`Region::holes` internal error,
   `reports/run1_klayout_filler_crash.log`). `flow/sealring_g1.py` builds the
   1000 µm ring and stretches every vertex beyond the mid-lines; stretching the
   900 µm ring to 1000 µm XORs to zero against the PCell's 1000 µm ring on all
   20 layers (command in the file header; script `build/scratch/seal/stretch_xor.py`
   was ad hoc, the check is repeated by the DRC `Seal.*` rules on the final GDS).
4. **`sg13g2_IOPadAnalog` core-side terminals.** The stock cell has `pad` and
   `padres` only; `padres` is behind a 587 Ω `rppd` (CDL `sg13g2_SecondaryProtection`).
   The `pad` pin has a second port geometry on the core side (Metal2/Metal3,
   y = 179–180) with no pin name of its own, so a resistor-free connection is
   impossible with the stock LEF. `ip/sg13g2_io_padbare/` renames that geometry
   `padbare` (template approach, re-derived from the PDK files); the eight
   measurement pins use it, TRIP_SET and VREF stay on `padres`.
5. **Non-integer edge spacing.** 140.5 µm keeps the 1 µm gaps on the IO-site
   grid with a 1130 µm die; OpenROAD accepted it (rows at 140.5, pads at
   x = 322.5 + 81 n).

## Checks

Three frames were run through the same flow; the 1350 µm frame is the frame of
record (`PLAN.md` D13), the 1200 and 1130 µm frames are kept as evidence. The
KLayout decks are the sign-off decks (`AGENTS.md`); Magic DRC and LVS are
reported with their failure causes (tool/library limitations documented under
`reports/lvs_reference/` and `reports/antenna_reference/`).

### 1350 × 1350 µm frame (`reports/run-1350/`, run tag `ring-1350`, 2026-09-19) — current

Run of record with the `padbare` IO views; final GDS
`flow/runs/ring-1350/final/gds/g1_chip_top.gds`, about 50 MB (above the 20 MB
copy limit, so not copied to `layout/`), sha256
`7d5910b57178f15233cebe33bacf3071684b8361cedb344d3587dd2e4d0ccacd`
(`final_gds.sha256`).

| Check | Status | Evidence, cause |
| --- | --- | --- |
| Ring assembled (24 pads at 112 µm pitch, 4 corners, 92 fillers, 24 bondpads, core ring, routed placeholder core) | passed | `openroad-padring.log` (side 708, fill 228, gap 32, ends 34), `padring.def` (pad01 at x = 355, corners at 141/1029, `DIEAREA 1350 × 1350`); 0 routing DRC after 2 iterations, 0 critical disconnected pins, Magic/KLayout GDS XOR 0 (`metrics_summary.json`) |
| Seal ring | passed (generated) | `klayout-sealring.log`: PCell 1000 µm stretched by 300 µm to the 1350 µm outline |
| Fill | passed | `klayout-filler.log` |
| Density (after fill) | **passed, 0 markers** | `density.klayout.json`, `klayout-density.log` |
| KLayout DRC, PDK sign-off deck, hard rules (`ihp-sg13g2.drc`, `no_recommended`, deep, on the filled GDS with seal ring) | **passed, 0 markers** | `drc.klayout.json` (every rule 0), `drc.klayout.lyrdb`, `klayout-drc.log` (`RECOMMENDED enabled: false`) |
| KLayout DRC with the recommended rules | not run on this frame | the 1200 µm frame showed 63 × `Pad.fR` (IO cells' 3 µm pad stub vs 7 µm recommended exit length), a PDK-cell property that does not depend on the frame |
| KLayout antenna | failed, 9 markers — library/deck artefact, `reports/antenna_reference/` | `antenna.klayout.json/.lyrdb`: `Ant.e_Metal5/TopMetal1/TopMetal2` at the three `sg13g2_IOPadIn` cells, cumulative `vdd`-rail area 34 266 µm² (grows with the ring perimeter: 24 503 at 1130, 27 624 at 1200 µm) against the rail-tied receiver gate; the previous cell revision is clean on the same ring |
| Magic DRC | failed, 578 markers | `drc.magic.rpt`: 336 abutment-between-subcells at the IO rails, 215 CntB.h1 and 28 layer overlaps inside the PDK IO cells (566 on the smaller frames; the 12 extra are more filler abutments) |
| LVS (netgen black-box, the flow's step) | failed, 39 errors | `lvs.netgen.rpt`: abutting black boxes not connected by the extractor, as on the smaller frames; the KLayout deck cannot match the PDK IO cells either (`reports/lvs_reference/`); not pursued further |
| `pad`/`padbare` same conductor | passed | `reports/lvs_reference/padbare_conductor.log` |
| `Checker.IllegalOverlap` | not run | disabled as in the template |
| Timing (placeholder core, 10 MHz) | passed | `stapostpnr_summary.rpt`: setup slack ≥ 56.5 ns, hold ≥ 0.18 ns in all three corners |

### 1200 × 1200 µm frame (`reports/run-1200/`, run tag `ring-1200`, 2026-09-18)

Run of record: the flow with the `padbare` IO views (`ip/sg13g2_io_padbare`),
final GDS sha256 `0d8d355e8bc6b57dcef533d539d5ad54d92c4fe86721f7d6a0390f2aac1a8196`
(`final_gds.sha256`). The same frame before the `padbare` change (analog pads on
`padres`, GDS sha256 `f04ba54d…`) is kept in `reports/run-1200-prepadbare/`;
its numbers are identical except where stated.

| Check | Status | Evidence, cause |
| --- | --- | --- |
| Ring assembled (24 pads at 91 µm pitch, 4 corners, 56 fillers, 24 bondpads, core ring, routed placeholder core) | passed | `openroad-padring.log` (side 559, fill 79, gap 11, ends 12), `padring.def` (pad01 at x = 332.5, `DIEAREA 1200 × 1200`); 0 routing DRC, 0 critical disconnected pins (10 non-critical: the unused `padres`/`padbare` INOUT terminals of the analog pads), Magic/KLayout GDS XOR 0 (`metrics_summary.json`) |
| Seal ring | passed (generated) | `klayout-sealring.log`: PCell 1000 µm stretched by 150 µm to 1200 µm outline |
| Fill | passed | `klayout-filler.log`: Activ/GatPoly, Metal1–5, TopMetal1/2 fill without error |
| Density (after fill) | passed, 0 markers | `density.klayout.json`, `klayout-density.log` |
| KLayout antenna | failed, 9 markers — **library/deck artefact, see `reports/antenna_reference/`** | `antenna.klayout.json/.lyrdb`: `Ant.e_Metal5/TopMetal1/TopMetal2` at the three `sg13g2_IOPadIn` cells (cumulative `vdd`-rail area 27 624 µm² attributed to a rail-tied gate, limit 20 000). The same deck gives 0 items on the template's 1600 µm chip and 0 items on this very GDS with only `sg13g2_IOPadIn` swapped for the previous cell revision; the two revisions differ in the input-receiver region only. OpenROAD antenna check on the routing: 0 violations |
| KLayout DRC, PDK sign-off deck, hard rules (`ihp-sg13g2.drc`, `no_recommended`, run mode deep, tables `main`, on the filled GDS with seal ring) | **passed, 0 markers** | `drc.klayout.json` (every rule 0, `total 0`), `drc.klayout.lyrdb`, `klayout-drc.log` (`RECOMMENDED enabled: false`). Pre-padbare frame: `run-1200-prepadbare/drc_hardrules.*` (0 markers) |
| KLayout DRC with the recommended rules on | failed, 63 markers, all `Pad.fR` — the IO cells' 3 µm TopMetal1/TopMetal2 `pad` stubs are shorter than the recommended 7 µm metal exit length under a bond pad (24 TM1 + 39 TM2, a property of the PDK cells, not of the ring) | `run-1200-prepadbare/drc.klayout.json/.lyrdb`, `klayout-drc.log` (`RECOMMENDED enabled: true`; the flow had passed `no_recommended=1`, which the deck does not read as true — fixed in `config.yaml`) |
| Magic DRC | failed, 566 markers | `drc.magic.rpt`: 336 abutment-between-subcells at the IO rails, 215 CntB.h1 and 16 layer overlaps inside the PDK IO cells; identical to the 1130 µm frame |
| LVS, black-box (Magic DEF/LEF extraction + netgen, the flow's step) | failed, 37 errors | `lvs.netgen.rpt`: abutting black boxes are not connected by the extractor (17 bondpad/pad nets, `pad12_en` supply rails); not a verification of the ring, recorded and not pursued further |
| LVS, transistor level with Magic (`MAGIC_EXT_USE_GDS`) | failed, 208 errors | `run-1130/lvs_gds/`: Magic's extraction of the IO sub-cells does not match the PDK models; not pursued further |
| **LVS with the PDK KLayout deck** (`run_lvs.py`, final GDS vs `flow/lvs/pnl2cdl.py` netlist = flow's powered Verilog netlist + PDK stdcell CDL + PDK IO CDL) | failed — **deck/library limitation**, see `reports/lvs_reference/` | deep mode, 34 min, pre-padbare GDS: "Netlists don't match" inside the PDK clamp cells (`run-1200-prepadbare/lvs_klayout_deep/xref_summary.txt`: 14 IO sub-circuits NOMATCH, top skipped). On the padbare GDS (`lvs_klayout_deep/`, 38 min: same 14 IO sub-circuits NOMATCH, top skipped; `lvs_klayout_flat/`, 19 min, flat with device combination: top-level NOMATCH with 249 unmatched nets and 390 unmatched devices, all of them the diodes `I*.D0/D1`, the `rppd` resistors and the `SUB!` nets inside the 24 IO cells — none in the core, the bondpads or the ring wiring). Schematic netlist used: `lvs_klayout_flat/g1_chip_top_sch.cdl.gz`. The same deck fails on every bare PDK IO cell against the PDK's own CDL (`rppd` series resistor of the secondary protection not extracted; rails joined only by abutment) |
| `pad`/`padbare` same conductor | **passed** | `reports/lvs_reference/padbare_conductor.log`: KLayout netlist extraction of the stock `sg13g2_IOPadAnalog` — die-side `pad` stub and core-side `padbare` strip are one net, `padres` a different one |
| `Checker.IllegalOverlap` | not run | disabled as in the template |
| Timing (placeholder core, 10 MHz) | passed | `stapostpnr_summary.rpt`: setup slack ≥ 56.5 ns, hold ≥ 0.17 ns in all three corners |
| Final GDS | — | `flow/runs/ring-1200/final/gds/g1_chip_top.gds`, 48.8 MB (above the 20 MB copy limit, so not copied to `layout/`), sha256 `0d8d355e…` (`final_gds.sha256`); pre-padbare `f04ba54d…` |


### 1130 × 1130 µm frame (`reports/run-1130/`, run tag `ring`, 2026-09-18)

| Check | Status | Evidence, cause |
| --- | --- | --- |
| Ring assembled (24 pads, 4 corners, 28 fillers, 24 bondpads, core ring, routed placeholder core) | passed | `openroad-padring.log`, `padring.def`; 0 routing DRC (`route__drc_errors 0`), 0 disconnected pins, XOR Magic/KLayout GDS 0 (`metrics_summary.json`) |
| Seal ring | passed (generated) | `klayout-sealring.log`: PCell 1000 µm stretched by 80 µm to 1130 µm outline |
| Fill | passed | `klayout-filler.log`: Activ/GatPoly, Metal1–5, TopMetal1/2 fill without error |
| Density (after fill) | passed, 0 markers | `density.klayout.json`, `klayout-density.log` (`klayout__density_error__count 0`) |
| KLayout antenna | failed, 6 markers | `antenna.klayout.json/.lyrdb`: `Ant.e_TopMetal1/2` at the three `sg13g2_IOPadIn` cells (EN, SCLK, SDI). The marked gate is tied to the `vdd` rail inside the PDK cell (traced through Metal1 → Metal3 rail 160–178 µm → Metal4/5/TopMetal1 rail 140–158 µm, labelled `vdd`); the deck sums the whole ring's `vdd` rail metal (24 503 µm², limit 20 000 with diode). Same result with the Metal3-stack bondpad (`run1_antenna.klayout.json`), the TopMetal1 bondpad and with all bondpads deleted; the bare cell passes the deck (`ant__bare_iopadin.lyrdb`, 0 items). Deck/library interaction, not a layout defect; OpenROAD's antenna check on the routing: 0 violations |
| KLayout DRC | failed, 63 markers, all recommended rule `Pad.fR` | `drc.klayout.json/.lyrdb`, `klayout-drc.log`: `Pad.fR_TM1` 24, `Pad.fR_TM2` 39 ("Min. recommended metal exit length 7.00 µm") at the 3 µm `pad` stubs of the IO cells. Zero markers from hard rules. The recommended rules ran because LibreLane passed `no_recommended=1` and the deck accepts only `true` (`RECOMMENDED enabled: true` in the log); fixed in `flow/config.yaml` for later runs |
| Magic DRC | failed, 566 markers | `drc.magic.rpt`, `magic-drc.log`: 336 "layer can't abut or partially overlap between subcells" at the IO rails across pad/filler boundaries, 215 "Metal enclosure of ContBar (CntB.h1)" inside the PDK IO cells, 16 "Can't overlap those layers" inside IO cells. All inside PDK cells or at their intended abutments; nothing in the placed/routed core or bondpads |
| LVS of the ring netlist (Magic black-box extraction + netgen) | failed, 37 errors | `lvs.netgen.rpt`, `netgen-lvs.log`, `magic-spiceextraction.log`: the extraction reads the DEF with the IO cells and bondpads as LEF black boxes and does not connect abutting cells: every signal pad's bondpad is on the port net while the IO cell's `pad` pin is a local net (17 nets), `pad12_en` keeps local `iovdd/iovss` (no top-level pin label on that pad), the supply ring is merged only through the top-level port labels (`MAGIC_EXT_UNIQUE notopports`, Magic feedback "Label … attached to more than one unconnected node"). The GDS metal is continuous at all 24 bondpad/stub joints (checked in KLayout). This LVS method cannot verify an abutment-joined ring; see the 1200 µm table for the transistor-level attempt |
| `Checker.IllegalOverlap` | not run | disabled as in the template (Magic reports the intended pad abutments) |
| Timing (placeholder core, 10 MHz) | passed | `stapostpnr_summary.rpt`: setup slack ≥ 56.5 ns, hold ≥ 0.18 ns in all three corners; max-slew warnings on the pad output nets |
| Final GDS | — | `flow/runs/ring/final/gds/g1_chip_top.gds`, 47.8 MB (not copied), sha256 `dd9e996a80a881cb93c82916b389478f58844a89b2c9eff6b93c806dcbd99ca3` (`final_gds.sha256`) |

## Tool versions

| Tool | Version | Established by |
| --- | --- | --- |
| LibreLane | v3.1.0.dev2 | `librelane --version` in the container (flow logs `reports/run-*/flow.log`) |
| Yosys | 0.67 (git 2d1509d1b) | `reports/run-1200/../flow/runs/ring-1200/06-yosys-synthesis/yosys-synthesis.log` |
| OpenROAD | 26Q3-850-gc74892e7b | `openroad -version` in the container (not printed in the step logs) |
| KLayout | 0.30.9 | `klayout -v` in the container |
| Magic | 8.3 revision 678 | `reports/run-1200/magic-drc.log` |
| Netgen | 1.5.323 | `reports/run-1200/netgen-lvs.log` |
| Verilator | 5.050 | `flow/runs/ring-1200/01-verilator-lint/verilator-lint.log` |
| PDK | IHP SG13G2 commit `84374023ee8b4b126bebbba67fcbada0a9c0ff0b` | `/foss/pdks/ihp-sg13g2/COMMIT` |
| Container | `tapeoutbench-eda:latest` = digest `sha256:5fd78498…` (`PLAN.md` section 2) | `docker images` |

## Open items

- KLayout antenna markers on the `vdd`-tied gate of the current `sg13g2_IOPadIn`
  revision: for the foundry (`reports/antenna_reference/README.md`); the
  previous cell revision is clean on the same ring.
- `Pad.fR` (recommended): the IO cells' 3 µm TopMetal1/2 `pad` stub is shorter
  than the recommended 7 µm exit length for any external bondpad.
- A real LVS of the ring cells themselves is not possible with the PDK's own
  decks at this commit (`reports/lvs_reference/`); the assembled chip is
  verified with the core-only KLayout LVS (ring cells excluded, `INTEGRATION.md`)
  plus the metal-only connectivity check of all 22 chip pins through the pads.
- Macros replace `g1_core_placeholder`; the 622 × 622 µm core window is the
  budget (`INTEGRATION.md`: floorplan for all seven macros at 71 % area).
  Measurement pads are on `padbare`, TRIP_SET/VREF on `padres`.
- 1350 µm frame differences from `PLAN.md` D7: pitch 112 µm (not 80), die
  1350 µm (not 1000; D13), end fillers 34 µm (not 55).
- Integration (`INTEGRATION.md`): the assembly of record closes KLayout DRC
  (hard rules and precheck), density, routing, PDN connectivity, supply
  isolation and STA; core-only KLayout LVS **passed (52 circuit pairs matched)**. Open for the
  block owners: deliver `g1_sense`, `g1_gate`, `g1_trip`, `g1_osc` without
  fill above Metal3 (the assembly strips it, `flow/macro_gds_assembly/`); no
  189/0 `prBoundary` in any macro (stripped likewise); `g1_ls_up` with real
  Metal1/Metal2 obstructions instead of the blanket ones (or Metal3 supply
  pins) so the strap checks need no exemption; `g1_trip` has no `TRIP_SET`
  input, so pin 13 ends at the core boundary.
- Lesson recorded: none of the flow's sign-off steps detects a same-layer
  overlap of two supply nets (KLayout DRC merges the metal, `check_power_grid`
  tests one net at a time, the router's DRC skips special wires). The
  assembly now runs `flow/lvs/pdn_net_overlap.py`, `pdn_macro_overlap.py`
  and `supply_isolation.py` (`flow/signoff/signoff.sh`) and the core-only LVS.



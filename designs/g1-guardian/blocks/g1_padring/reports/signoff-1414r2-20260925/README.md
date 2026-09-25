# G1 1414 µm chip, revision r2: metadata-only correction and full physical sign-off rerun (2026-09-25)

`g1_chip_top_1414_r2.gds` replaces `g1_chip_top_1414.gds` (r1, `629d303a…`) as the file of
record. r2 differs from r1 only in metadata: two text labels and three cell names. The
geometry is identical on every layer. This report proves that, then reruns the whole r1
sign-off suite on r2 with the same options, and adds the stock precheck mode.

It addresses findings 1 (registration text only), 4 (bond-map binding) and 6 (a modified
cell with a stock name) of [`review/redteam-20260925/PHYSICAL_TAPEIN.md`](../../../../review/redteam-20260925/PHYSICAL_TAPEIN.md).
Written confirmation from IHP of the allocated die area (finding 1) is still **open**.

This is physical verification only. Full-chip PEX, IR/EM, timing sign-off and electrical
qualification of the assembled chip are **not run** here (see "Not run").

## Built against

| Item | Value | How established |
|---|---|---|
| PDK | IHP-Open-PDK `84374023ee8b4b126bebbba67fcbada0a9c0ff0b` | `flow/run.sh` refuses to start unless `/foss/pdks/ihp-sg13g2/COMMIT` matches |
| KLayout | 0.30.9 | `klayout -v` in the container; `run_drc.py` log line "KLayout version detected: 0.30.9" |
| Container image | `sha256:ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2` | `flow/run.sh` image identity check |
| Rule decks | stock `run_drc.py`, `run_lvs.py` and decks from the PDK above, unmodified | invoked from `/foss/pdks/ihp-sg13g2/libs.tech/klayout/tech/` inside the container |
| CPUs | 64-79 (`taskset`, rootless cgroups v1) | `flow/launch_pinned.sh`; per-run sets below |

## Files of record

| File | SHA-256 | Notes |
|---|---|---|
| `layout/g1_chip_top_1414_r2.gds` | `9049e87b0303893573ed82f56a5d41f926c4db126e8d972062553c7d19996d2c` | **File of record. This is the file checked below.** 84 500 300 bytes (r1: 84 500 250; the two new strings are 50 bytes longer in total) |
| `layout/g1_chip_top_1414.gds` (r1) | `629d303abf594ec90593f1d28a8d9ad19673ea6662780ba428a6d9c5685986ba` | Superseded; kept unchanged. Its sign-off: [`signoff-1414-20260924`](../signoff-1414-20260924/README.md) |
| `netlist/g1_chip_top_1414_r2.cdl` | `41d478778390ef9f39f51c9729cd015fefbad084b44b3d6e3a59753480df0d29` | Canonical (unprojected) reference for r2: r1 `g1_chip_top_1414.cdl` `af5a4dbd…` with `sg13g2_LevelDown` renamed to `g1_LevelDown_polyres` (6 lines, see below) |
| `netlist/g1_chip_top_1414_projected_ref.cdl` | `e1d06919fedea1c1e2c171ab52a35cdec4dc7132470c5887561ad2a0cf27640e` | Comparison-only projected reference, **unchanged from r1**. It is flat and contains none of the renamed names (`sg13g2_LevelDown`, `nmos`, `pmos`: 0 occurrences), so an r2 copy would be byte-identical and was not created |
| `padframe/bondmap_20260925_r3.csv` | `ead5f1090861a4e5e80e3fcbfb9ca81cd9d04f56df9e8b21279050947e673726` | Bond map bound to r2, with QFN24 lead columns (see "Bond map") |

## What changed from r1

Script [`flow/signoff/1414r2/make_r2.py`](../../flow/signoff/1414r2/make_r2.py). It checks the r1
SHA, edits in place and writes GDS2 with `gds2_write_timestamps = False`. Two writes were
byte-identical (`9049e87b…`). Output: [`r2_identity/make_r2.json`](r2_identity/make_r2.json).

1. **Registration texts** (top cell, TEXT 63/0, size 5 µm, MAG 5, R0, presentation `0008`, all kept):

   | Position (µm) | r1 string | r2 string |
   |---|---|---|
   | (5, 5) | `Device registration size: x=1050.0 um ; y=1050.0 um\nCalculated area: 1.1e-06 sq mm` | `Device registration size: x=1414.0 um ; y=1414.0 um\nCalculated area: 1.999396 sq mm` |
   | (5, 1404) | `PDK version: Unknown (Not a Git repo or Git not installed)` | `PDK version: IHP-Open-PDK 84374023ee8b4b126bebbba67fcbada0a9c0ff0b` |

   The size and area are computed in the script from the EdgeSeal boundary 39/4, one
   polygon `(0,0;1414000,1414000)` dbu: 1414.0 × 1414.0 µm = 1 999 396 µm² = 1.999396 mm²,
   and asserted equal to the string written.
2. **Cell renames** (design-local names for cells that carry a stock PDK name but differ from the PDK cell):

   | r1 name | r2 name | Parent | Difference from the PDK cell of that name |
   |---|---|---|---|
   | `sg13g2_LevelDown` | `g1_LevelDown_polyres` | `retained_fullchip_sg13g2_IOPadIn` | 2.00 µm² PolyRes 128/0 (through `g1_io_secondary_polyres_r1_alias1`); every other layer and all texts identical to `sg13g2_io.gds` (finding 6) |
   | `nmos` | `g1_gate_nmos` | `retained_g1_gate` | a PCell variant; differs from the `nmos` default cell in `sg13g2_pr.gds` on 8 layers and texts |
   | `pmos` | `g1_gate_pmos` | `retained_g1_gate` | a PCell variant; differs from the `pmos` default cell in `sg13g2_pr.gds` on 10 layers and texts |

   The `nmos`/`pmos` renames go beyond finding 6: the reviewer compared against
   `sg13g2_io.gds` and `sg13g2_stdcell.gds` only; this check also used `sg13g2_pr.gds` and the
   SRAM GDS files (see "Stock-name check").

## r2 identity (passed)

| Check | Result | Output |
|---|---|---|
| KLayout hierarchy and geometry, [`verify_r2.py`](../../flow/signoff/1414r2/verify_r2.py) | **passed** (`metadata_only_change: true`): 306 / 306 cells; names equal modulo the 3 renames; DBU, library name `LIB` and bbox `(0,0;1414000,1414000)` equal; every cell's direct shapes and instance list identical (0 differing cells); recursive instance tree identical, 60 118 / 60 118 instances with identical transformations; deep per-layer XOR of the flattened top **empty on all 73 layers** (63/0 included); flattened text lists identical on every layer except 63/0, where exactly the two labels above differ with identical position, size, font and alignment | [`r2_identity/verify_r2.json`](r2_identity/verify_r2.json) |
| Raw GDS records, [`gds_record_diff.py`](../../flow/signoff/1414r2/gds_record_diff.py) (host `python3`, no KLayout) | **passed** (`only_expected_differences: true`): 6 717 548 / 6 717 548 records, 306 / 306 structures, 1 334 598 / 1 334 598 elements; header records (HEADER, BGNLIB, LIBNAME, UNITS) identical; per structure, the element multisets are identical after the 3 renames (3 STRNAME, 3 SNAME), except two TEXT elements of `g1_chip_top` that differ only in STRING. The writer changes the order of structures and elements, which is why the comparison is by multiset | [`r2_identity/gds_record_diff.json`](r2_identity/gds_record_diff.json) |
| GDS inventory (`review/tapein/gds_inventory.py`) | **passed**: identical to the r1 inventory in every layer count, text count and cell list (modulo the renames) apart from the SHA | [`review/tapein/gds_inventory_g1_chip_top_1414_r2.json`](../../../../review/tapein/gds_inventory_g1_chip_top_1414_r2.json) |

## Stock-name check (passed after the renames)

[`flow/signoff/1414r2/stock_compare.py`](../../flow/signoff/1414r2/stock_compare.py), the reviewer's s3
method (per-layer XOR of the recursive cell content in cell coordinates on the union of
layers, plus a flattened text comparison), run against every GDS under
`libs.ref/*/gds/` (`sg13g2_io`, `sg13g2_stdcell`, `sg13g2_pr` and the 29 SRAM files).

| Set | r1 | r2 |
|---|---|---|
| Cells whose exact name exists in a PDK GDS | 54, of which 3 differ: `sg13g2_LevelDown`, `nmos`, `pmos` | 51, **0 differ** |
| Renamed cells vs their stock origin | — | `g1_LevelDown_polyres` vs `sg13g2_LevelDown`: 128/0 only (+2.00 µm²); `g1_gate_nmos`/`g1_gate_pmos`: PCell parameter differences |
| Cells named `<stock name>$N` | 61, of which 43 differ: all PCell variants from `sg13g2_pr` (`nmos`, `pmos`, `nmosHV`, `pmosHV`, `rppd`, `cmim`, `npn13G2`, `NoFillerStack`) | unchanged, not renamed: the name is not a stock name |
| `retained_*` copies (informational) | 19; `retained_fullchip_sg13g2_IOPad{In,Analog}` +2 µm² and `IOPad{Vdd,IOVdd}` +520 µm² on 128/0 only; the other 15 identical | unchanged |

`npn13G2$7` differs from the `sg13g2_pr` `npn13G2` default cell only on the pin layers
8/2 and 10/2 (the reviewer's s9 compared FEOL layers against a fresh PCell and found it identical).
Outputs: [`stock_compare/stock_compare_r1.json`](stock_compare/stock_compare_r1.json),
[`stock_compare/stock_compare_r2.json`](stock_compare/stock_compare_r2.json).

## Netlists

`g1_chip_top_1414_r2.cdl` was made from r1 `af5a4dbd…` by replacing the whole token
`sg13g2_LevelDown` (not preceded or followed by a word character or `$`) with
`g1_LevelDown_polyres`: 6 occurrences. `G1_VSS_DERIVATIVE__sg13g2_LevelDown` is a different
sub-circuit name, has no layout cell of that name, and is unchanged. Nothing else changed:

```
# summary of `diff g1_chip_top_1414.cdl g1_chip_top_1414_r2.cdl` (enclosing sub-circuit in parentheses)
2272c2272  * Cell Name:    sg13g2_LevelDown                     -> g1_LevelDown_polyres
2276c2276  .SUBCKT sg13g2_LevelDown core pad iovdd iovss vdd vss -> .SUBCKT g1_LevelDown_polyres ...
2304c2304  XI4 p2c pad iovdd iovss vdd vss / sg13g2_LevelDown    -> / g1_LevelDown_polyres  (sg13g2_IOPadInOut4mA)
2345c2345  XI4 ... / sg13g2_LevelDown                             -> / g1_LevelDown_polyres  (sg13g2_IOPadInOut30mA)
2428c2428  XI0 ... / sg13g2_LevelDown                             -> / g1_LevelDown_polyres  (sg13g2_IOPadIn)
2474c2474  XI4 ... / sg13g2_LevelDown                             -> / g1_LevelDown_polyres  (sg13g2_IOPadInOut16mA)
```

Full `diff` output: [`netlist_diff.txt`](netlist_diff.txt). Copies of every summary here are listed with
original and copy hashes in [`manifest.json`](manifest.json) (bulk paths normalised to `${BULK}`). Neither CDL contains `nmos`/`pmos`
as a sub-circuit or instance name (whole-word count 0), so the two GATE renames need no netlist change.

## Physical checks on `g1_chip_top_1414_r2.gds` (`9049e87b…`)

Each check ran detached through `flow/launch_pinned.sh` with a 5400 s wall bound and top
cell `g1_chip_top`, all seven at the same time on disjoint CPU sets. Paths are inside the
container. `$G` is `/work/designs/g1-guardian/blocks/g1_padring/layout/g1_chip_top_1414_r2.gds`,
`$N` is `/work/designs/g1-guardian/blocks/g1_padring/netlist`, `$D` is
`/foss/pdks/ihp-sg13g2/libs.tech/klayout/tech` and `$B` is `${BULK}/signoff-1414r2-20260925`.

| Check | CPUs | Result | Markers | Wall | Report (bulk) / copy here |
|---|---|---|---|---|---|
| Main DRC (table `main`, recommended on) | 64-67 | **passed** | 0 | 351 s | `drc_main/g1_chip_top_1414_r2_g1_chip_top_main.lyrdb` `3da5e270…` |
| Maximal DRC (`sg13g2_maximal`) | 68-71 | **passed** | 0 | 763 s | `drc_maximal/g1_chip_top_1414_r2_g1_chip_top_sg13g2_maximal.lyrdb` `f54b65a5…` |
| Density | 72-73 | **passed** | 0 | 40 s | `density/g1_chip_top_1414_r2_g1_chip_top_density.lyrdb` `89149c55…` |
| Antenna | 74-75 | **passed** | 0 | 154 s | `antenna/g1_chip_top_1414_r2_g1_chip_top_antenna.lyrdb` `71533d82…` |
| Precheck (`--precheck_drc --disable_extra_rules`, with density; new, not in the r1 sign-off) | 76-77 | **passed** | 0 (main + density) | 275 s | `precheck/g1_chip_top_1414_r2_g1_chip_top_full.lyrdb` `92416e92…` |
| LVS, projected reference, strict ports | 78 | **passed** | Netlists match: 61 684/61 684 devices, 31 173/31 173 nets, 22/22 pins, 0 warnings, 0 errors | 204 s | `lvs_projected/pair_counts.json`, logs; lvsdb `3d688aa4…` bulk only |
| LVS, canonical unprojected reference (r2 CDL) | 79 | **failed** (as r1) | "Netlists don't match". 14 IO/level-shifter sub-circuit pairs NoMatch, top `Skipped`; 34 Match. Every per-circuit status and device/net/pin/subcircuit count equals r1's with `sg13g2_LevelDown`→`g1_LevelDown_polyres` | 161 s | `lvs_canonical/pair_counts.json`, logs; lvsdb `5337dbd2…` bulk only |

The four DRC lyrdb files are byte-identical to r1's (same SHA-256 prefixes as in
`signoff-1414-20260924`): an empty report carries only the rule catalogue, not the input name.
Every run exited with code 0 (`run.log.rc`). The GDS SHA was checked again after all runs
and was unchanged (`9049e87b…`). Wall times are the tools' own "Total DRC Run time" /
"Run Time" lines. Commands:

```sh
# launcher, from the repository root (BULK=<bulk results root>; G1_RESULTS_ROOT=$B):
#   flow/launch_pinned.sh <cpus> . 5400 $B/<check>/run.log <command>
# main DRC
python3 $D/drc/run_drc.py --path=$G --topcell=g1_chip_top --run_mode=deep --no_density --disable_extra_rules --density_thr=4 --run_dir=$B/drc_main
# maximal DRC (stock run_drc.run_check on sg13g2_maximal.drc with the switches run_drc.py generates for --run_mode=deep --no_density)
python3 designs/g1-guardian/blocks/g1_padring/flow/signoff/1414/run_maximal.py $G g1_chip_top $B/drc_maximal 4
# density
python3 $D/drc/run_drc.py --path=$G --topcell=g1_chip_top --run_mode=deep --density_thr=2 --density_only --run_dir=$B/density
# antenna
python3 $D/drc/run_drc.py --path=$G --topcell=g1_chip_top --run_mode=deep --density_thr=2 --antenna_only --run_dir=$B/antenna --antenna
# precheck (the physical reviewer's mode on r1: --precheck_drc --disable_extra_rules, density included)
python3 $D/drc/run_drc.py --path=$G --topcell=g1_chip_top --run_mode=deep --precheck_drc --disable_extra_rules --density_thr=2 --run_dir=$B/precheck
# projected-reference LVS (reference unchanged from r1)
python3 $D/lvs/run_lvs.py --layout $G --netlist $N/g1_chip_top_1414_projected_ref.cdl --topcell g1_chip_top --run_mode deep --top_lvl_pins --spice_comments --run_dir $B/lvs_projected
# canonical LVS
python3 $D/lvs/run_lvs.py --layout $G --netlist $N/g1_chip_top_1414_r2.cdl --topcell g1_chip_top --run_mode deep --top_lvl_pins --spice_comments --run_dir $B/lvs_canonical
# LVS pair counts (both runs)
klayout -b -r designs/g1-guardian/blocks/g1_padring/flow/signoff/1414/lvs_pair_counts.py -rd db=$B/lvs_<kind>/g1_chip_top_1414_r2.lvsdb
```

Differences from the r1 command lines: the input file, the canonical CDL, the run
directory and the CPU sets. All options are the same. Precheck is new; its log shows
`tables selected: main`, `PreCheck DRC enabled: true`, and OFFGRID, ANGLE, PIN, FORBIDDEN and
RECOMMENDED enabled, then the density table. That matches the reviewer's r1 run
(`${BULK}/redteam-20260925-physical/precheck/`, 0 markers, 321 s).

Projected LVS scope (unchanged from r1): the reference removes exactly three source-only
dummy PMOS (VDD to VDD, all-VDDIO pad). It is a comparison projection, **not** canonical
unprojected sign-off.

Canonical LVS failure: the same 14 stock-named IO sub-cells NoMatch as on r1
(`sg13g2_Clamp_*` ×9, `DCN/DCPDiode`, `GateLevelUpInv`, `LevelUpInv`, `RCClampInverter` and
now `g1_LevelDown_polyres`/`G1_LEVELDOWN_POLYRES`). Cause as recorded for r1: substrate/tap/diode
netlist semantics of the IO-cell reference in the PDK
([`review/upstream/evidence/`](../../../../review/upstream/evidence/README.md), issues #1218/#1130).
The rename does not change it.

## Block-to-netlist map

**Unchanged from r1** ([`signoff-1414-20260924` block map](../signoff-1414-20260924/README.md#block-to-netlist-map-what-is-physically-in-629d303a)).
It was not re-run: `verify_r2.py` shows every cell of r2 has the same direct shapes and
instances as the r1 cell of the same (mapped) name, so each per-cell XOR in
`signoff-1414-20260924/blockmap/` gives the same result on r2. The GATE cell
`retained_g1_gate` now instantiates `g1_gate_nmos`/`g1_gate_pmos` instead of `nmos`/`pmos`, with the same geometry.

## Bond map

`padframe/bondmap_20260925_r3.csv` (`ead5f109…`) = the rows of `bondmap_candidate_20260923_r2.csv`
(`201612db…`) with columns 1-9 unchanged, `candidate_gds_sha256` = `9049e87b…`, `status` =
`chip_of_record`, and two added columns `qfn24_lead` and `lead_side`. The hash column keeps its
name so that the existing validators still read it. The CSV is written by
[`padframe/bondplan_20260925.py`](../../../../padframe/bondplan_20260925.py), which reads the
openings and labels from the r2 GDS and derives each lead from the package geometry (owner
decision 2026-09-25: pad bonded to the lead directly opposite, counter-clockwise numbering,
pin 1 top-left; [`padframe/BONDPLAN_20260925.md`](../../../../padframe/BONDPLAN_20260925.md)).

[`flow/signoff/1414r2/verify_bondmap.py`](../../flow/signoff/1414r2/verify_bondmap.py) (the reviewer's s2 method)
checked the CSV independently: **passed** (`all_ok: true`). There are 24 Passiv openings in r2 and 24 rows.
Each row matches exactly one opening whose centre equals the CSV centre to 1 dbu. All are 65.8 × 65.8 µm
rectangles with TopMetal2 enclosure ≥ 2.1 µm, inside dfpad, die 1414 µm, and the hash equals the r2 SHA.
The 22 TopMetal2 labels (134/25) sit at the row centres and equal `logical_pin`; pads 5 and 6 carry no label.
Output: [`bondmap/verify_bondmap_r3.json`](bondmap/verify_bondmap_r3.json).

## Not run

- IHP MPW Rejection Test or any IHP intake check (PHYSICAL_TAPEIN finding 3).
- Written IHP confirmation of the allocated die area 1.999396 mm² (finding 1): open.
- Full-chip (assembled) PEX, full-chip transient/electrical simulation, IR drop/EM, full-chip STA with extracted parasitics.
- Canonical unprojected LVS passing: run, **failed** (PDK IO-cell reference semantics, as r1).
- Block-map XOR re-run on r2: not run (carried over by identity, see above).
- Measurement: not run (no silicon).

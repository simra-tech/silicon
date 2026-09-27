# G1 1414 µm chip, revision r4 candidate: TRIP macro `nf4_novclk` (non-overlapping comparator clock) and GatPoly fill, physical sign-off (2026-09-27)

`g1_chip_top_1414_r4.gds` is a **candidate**. It is not adopted: the file of record stays
`g1_chip_top_1414_r3.gds` (`7d07a7841a531f51e08b0c90e76fe603889cd2ef29905e309e63f09742e688f2`), with its
sign-off in [`signoff-1414r3-20260926`](../signoff-1414r3-20260926/README.md). This folder gathers the
chip-level physical evidence of the r4 build so that an adoption decision can rest on it.

**r4 = r3 + the patched TRIP macro + 406 µm² of GatPoly fill.**
1. **The TRIP macro.** The cell `__rz_port_text_033_retained_g1_trip` (R0 at 771, 736 µm) has the
   inverter `XCLKI` replaced by the 20-device generator `g1_novclk` (red-team finding F1). Cell name,
   placement, outline (229 × 207 µm), pins and sub-cells are unchanged. Design, block checks and
   simulations: [`blocks/g1_trip/layout/candidates/nf4_novclk/README.md`](../../../g1_trip/layout/candidates/nf4_novclk/README.md)
   and [`BLOCK_QUALIFICATION_20260927.md`](../../../g1_trip/layout/candidates/nf4_novclk/BLOCK_QUALIFICATION_20260927.md).
2. **The fill.** 58 GatPoly fill rectangles (5/22, 406.0 µm²) in the top cell, outside every macro
   box, restore the GFil.g margin that the patch had reduced.
3. **The digital macro** `__rz_port_text_000_retained_g1_digital` is **byte-identical to r3** (see
   "Digital macro identity"). The macro flow, STA, GLS and equivalence results of r3 therefore carry over.

This is physical verification only. Full-chip PEX, IR/EM, timing sign-off of the assembled chip and the
bond-map re-verification are **not run** (see "Not run"). Full-chip transients on r4 are run separately
under `blocks/g1_top/sim/` and are not part of this folder.

## Built against

| Item | Value | How established |
|---|---|---|
| PDK | IHP-Open-PDK `84374023ee8b4b126bebbba67fcbada0a9c0ff0b` | `flow/run.sh` refuses to start unless `/foss/pdks/ihp-sg13g2/COMMIT` matches |
| Container image | `sha256:ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2` | `flow/run.sh` image identity check |
| KLayout | 0.30.9 | `klayout -v`; DRC/LVS logs (Ruby 3.2.3 in `drc_maximal/…_maximal.log`) |
| Rule decks | stock `run_drc.py`, `run_lvs.py` and decks of the PDK above, unmodified | invoked from `/foss/pdks/ihp-sg13g2/libs.tech/klayout/tech/` (`drc_maximal/run.log` option dump) |
| Digital macro flow | not re-run; r3's (LibreLane 3.1.0.dev2, OpenROAD 26Q1-1024-gdcf36133a, OpenSTA 3.1.0) | r3 README "Built against" |
| CPUs | r4 build and sign-off: 22-31, 50-55 (per-check split not recorded in the logs); report XOR checks: 45-47 | candidate README "Chip r4" step 4; `G1_CPUSET` of this assembly |

## Files

| File | SHA-256 | Notes |
|---|---|---|
| `layout/g1_chip_top_1414_r4.gds` | `225d0b535321ed312594bb13d97b7271014f487162564a56c874572de715173a` | **Candidate.** Byte copy of the checked bulk file `${BULK}/r4-20260927/chip/g1_chip_top_1414_r4.gds` ([`input_gds.sha256.assembly`](input_gds.sha256.assembly)) |
| `${BULK}/r4-20260927/chip/g1_chip_top_1414_r4_prefill.gds` | `5b3c414371a0ea999b261b6574bbbb4dd7a4f1c70b7c2c68dd930902e7237768` | r3 + TRIP patch, before the GatPoly fill (bulk only) |
| `netlist/g1_chip_top_1414_r4.cdl` | `e060c0c59a168e5b69b0c47dc31cbfe4f4444d2ec8af62960c339c1230a2c99f` | Canonical reference: r3 CDLs with the `g1_trip` source block edited (`make_chip_cdl.py`) |
| `${BULK}/r4-20260927/cdl/g1_chip_top_1414_r4_projected_ref.cdl` | `27a27cd64dfa18db66e2e9374c78b62f2d4ac95440d071149ffb048702e08fda` | Flat comparison-only projected reference, 77 035 devices, 22 pins (17 MB, bulk only) |
| `${BULK}/r4-20260927/cand/g1_trip_nf4_novclk.gds` | `3213819a47b6a43d370318b3b8520b05fc61b2806a745d03541040bc199d80c5` | Candidate TRIP macro (top `g1_trip`) |

`$R` below is `${BULK}/r4-20260927`, the run root.

## r4 identity

| Check | Result | Output |
|---|---|---|
| XOR r3 → r4 (`chip_xor.py`, TRIP box 771,736,1000,943 µm) | **passed**. Outside the box only 5/22 changed: +58 polygons, 406.0 µm², 0 text differences. Inside the box only macro layers changed: 1/0, 1/22, 1/23, 5/0, 5/2, 5/22, 5/23, 6/0, 8/0, 8/2, 8/22, 8/23, 10/0, 10/22, 10/23, 14/0, 19/0, 29/0, 30/0, 30/22, 30/23, 31/0, 40/0, 51/0 (51/0 HeatTrans: 22 polygons and 22 texts, the device markers of the new generator); no other text difference | [`r4_identity/chip_xor.json`](r4_identity/chip_xor.json), `.log`, `.log.rc` |
| XOR r3 → r4 before the fill (`…_prefill.gds`) | **passed**. Nothing changed outside the TRIP box | [`r4_identity/chip_xor_prefill.json`](r4_identity/chip_xor_prefill.json) |
| XOR method control (r3 rewritten by KLayout vs r3) | **passed**: no layer changed inside or outside | [`r4_identity/chip_xor_control.json`](r4_identity/chip_xor_control.json) |
| GatPoly fill (`add_gatpoly_fill.py`) | 58 rectangles, 406.0 µm², only 5/22 changed, texts and instances held; GatPoly 300 422.381 → 300 828.381 µm² (15.0257 → 15.046 %) | [`r4_identity/fill.json`](r4_identity/fill.json) |
| TRIP cell in r4 vs candidate macro (`cell_xor.py`, run for this report) | **passed**: 48 layers compared, XOR 0 polygons on every layer, all texts equal (80 827 polygons, 2 404 texts flattened), bbox (0,0;229,207) both, 12 sub-cells each. The sub-cell name sets differ (names not compared further); content is equal by the flattened XOR | [`trip_identity/trip_cand_vs_r4chip_xor.json`](trip_identity/trip_cand_vs_r4chip_xor.json) |
| Projected reference (`flatten_reference.rb` on `comparison_only_r4.cdl`) | **passed**: 77 035 devices, 22 pins, roundtrip Match (77 035 devices, 32 557 nets, 22 pins) | [`r4_identity/g1_chip_top_1414_r4_projected_ref.cdl.json`](r4_identity/g1_chip_top_1414_r4_projected_ref.cdl.json), [`flatten.log`](r4_identity/flatten.log) |
| CDL method control (same command on r3's `comparison_only.cdl`) | **passed**: reproduces r3's projected reference `d0d36c84…` exactly (77 017 devices, roundtrip Match) | [`r4_identity/r3_projected_ref_control.cdl.json`](r4_identity/r3_projected_ref_control.cdl.json), [`flatten_control.log`](r4_identity/flatten_control.log) |
| GDS inventory (`review/tapein/gds_inventory.py`) | **not run** on r4. The XOR above bounds the change to the TRIP box and 5/22 | — |
| Stock-name check (`stock_compare.py`) | **not run** on r4 | — |
| Swap method control | **not applicable**: r4 is not made by `swap_macro.py` but by the `NovclkPatch` of `gen_trip_layout.py` | candidate README "Layout" |

## Digital macro identity

The cell `__rz_port_text_000_retained_g1_digital` was taken out of both the r3 and the r4 GDS with KLayout
in the container (`G1_CPUSET=45-47`, 2026-09-27) and compared two ways:

| Check | Result | Output |
|---|---|---|
| Per-layer XOR, hierarchy flattened, plus text and sub-cell comparison ([`cell_xor.py`](digital_identity/cell_xor.py)) | **passed**: 31 layers, XOR 0 polygons on every layer (698 456 polygons, 32 483 texts, all texts equal), 74 sub-cells with equal names, bbox (0,0;360,360), placement `r0 *1 367,364` in both tops | [`digital_identity/digital_xor_r3_r4.json`](digital_identity/digital_xor_r3_r4.json), `.log`, `.log.rc` |
| Byte comparison of the cut cells ([`cell_cut.py`](digital_identity/cell_cut.py): the cell and its sub-hierarchy written without timestamps or context) | **passed**: both cuts `183a3496a144bbcc3ad6a2a9a32526e43e59ef8022d81ece768f5051c5b29ef9`, 4 838 446 bytes, `cmp` equal | [`digital_identity/g1_digital_cut.sha256`](digital_identity/g1_digital_cut.sha256); cuts bulk only (`${BULK}/r4-20260927/signoff_report_xor/`) |

The macro is therefore the r3 macro (final GDS `67d049bf…`). Its STA, carried over unchanged from r3
(not re-run for r4; values from [`../signoff-1414r3-20260926/macro/`](../signoff-1414r3-20260926/macro/)):

| Case | Corner | Worst setup (ns) | Worst hold (ns) | TNS setup / hold | Registers | Source |
|---|---|---|---|---|---|---|
| Macro | typ | 28.821 | 0.195 | 0 / 0 | 1170 `osc_clk`, 52 `sclk` | `sta_macro_typ.tsv` |
| Macro | fast | 29.044 | 0.114 | 0 / 0 | 1170, 52 | `sta_macro_fast.tsv` |
| Macro | slow | 28.447 | 0.337 | 0 / 0 | 1170, 52 | `sta_macro_slow.tsv` |
| Merged chip SDC | typ | 27.248 | 0.195 | 0 / 0 | 1170, 52 | `sta_chip_merged_typ.tsv` |
| Merged chip SDC | fast | 27.988 | 0.114 | 0 / 0 | 1170, 52 | `sta_chip_merged_fast.tsv` |
| Merged chip SDC | slow | 25.704 | 0.337 | 0 / 0 | 1170, 52 | `sta_chip_merged_slow.tsv` |

The merged-SDC rows were computed on the r3 chip netlist and were not re-run on the r4 netlist.

## Physical checks on `g1_chip_top_1414_r4.gds` (`225d0b53…`)

Same commands and options as `run_candidate.sh signoff` for r3 (r3 README "Physical checks"), top cell
`g1_chip_top`, all started 2026-09-27 17:17:33 +0200 on the bulk file `$R/chip/g1_chip_top_1414_r4.gds`.
Run time is the tool's own total from the log named.

| Check | Result | Markers | Run time | Report (copy here; original in `$R/signoff/`) |
|---|---|---|---|---|
| Main DRC | **passed** | 0 items, 561 rule categories | 266.06 s (`drc_main/run.log`) | `drc_main/…_main.lyrdb` `3da5e270…` |
| Maximal DRC | **passed** | 0 items, 272 categories; "Number of DRC errors for maximum rule set: 0" | 665.74 s (`drc_maximal/…_maximal.log`) | `drc_maximal/…_sg13g2_maximal.lyrdb` `f54b65a5…` |
| Density | **passed** | 0 items, 7 categories | 31.26 s (`density/run.log`) | `density/…_density.lyrdb` `89149c55…` |
| Antenna | **passed** | 0 items, 31 categories | 129.19 s (`antenna/run.log`) | `antenna/…_antenna.lyrdb` `71533d82…` |
| Precheck (PreCheck DRC enabled, with density) | **passed** | 0 items, 455 categories | 241.32 s (`precheck/run.log`) | `precheck/…_full.lyrdb` `92416e92…` |
| LVS, projected reference (`…_r4_projected_ref.cdl` `27a27cd6…`), strict ports | **passed** | "Congratulations! Netlists match": 62 956/62 956 devices, 31 824/31 824 nets, **22/22 pins** (r3: 62 940, 31 816, 22) | 155.05 s (`lvs_projected/run.log`) | [`lvs_projected/pair_counts.json`](lvs_projected/pair_counts.json); lvsdb bulk only |
| LVS, canonical unprojected reference (`netlist/g1_chip_top_1414_r4.cdl` `e060c0c5…`) | **failed** (as r2/r3) | "Netlists don't match". 51 circuit pairs: 35 Match, 14 NoMatch (IO/level-shifter), 2 Skipped (top, `sg13g2_GateLevelUpInv`). `pair_counts.json` is byte-identical to r3's (`cmp`) | 138.75 s (`lvs_canonical/run.log`) | [`lvs_canonical/pair_counts.json`](lvs_canonical/pair_counts.json); lvsdb bulk only |

- Item counts are the number of `<item>` entries in each lyrdb; categories are `<category>` entries.
- The five DRC lyrdb hashes equal r3's (an empty report carries only the rule catalogue).
- Every run exited with code 0 (`*/run.log.rc`).
- The input GDS hash was recorded before the runs ([`input_gds.sha256`](input_gds.sha256)). No hash was
  recorded right after the runs (r3 had `input_gds.sha256.after`). The bulk and tracked files were
  re-hashed at report assembly, 2026-09-27 20:47 +0200, and are unchanged
  ([`input_gds.sha256.assembly`](input_gds.sha256.assembly)).

### Density table (`density/…_density.log`, r3 from `../signoff-1414r3-20260926/density/…_density.log`)

Chip area 1 999 396.0 µm² (EdgeSeal.boundary 39/4).

| Layer | r4 area (µm²) | r4 density | r3 density | Limits |
|---|---|---|---|---|
| Activ | 883 778.21 | 44.20 % | 44.22 % | 35-55 % |
| GatPoly | 300 828.38 | **15.05 %** | 15.03 % | min 15 % |
| Metal1 | 938 897.62 | 46.96 % | 46.97 % | 35-60 % |
| Metal2 | 747 308.29 | 37.38 % | 37.39 % | 35-60 % |
| Metal3 | 958 278.62 | 47.93 % | 47.93 % | 35-60 % |
| Metal4 | 934 735.00 | 46.75 % | 46.75 % | 35-60 % |
| Metal5 | 966 803.80 | 48.35 % | 48.35 % | 35-60 % |
| TopMetal1 | 1 006 324.11 | 50.33 % | 50.33 % | 25-70 % |
| TopMetal2 | 936 474.03 | 46.84 % | 46.84 % | 25-70 % |
| LBE | 0.00 | 0.00 % | 0.00 % | max 20 % |

GFil.g margin: 300 828.38 − 0.15 × 1 999 396.0 = **918.98 µm²** (r3: 300 527.47 − 299 909.40 = 618.07 µm²).

## Evidence copies in this folder

The summary logs, reports, `run.log` and return codes of every chip check were copied from `$R/signoff/`;
the identity JSONs and logs from `$R/chip/` and `$R/cdl/`; the report XOR outputs from
`$R/signoff_report_xor/`. Only `${BULK}` and `${REPO}` (host path or the container mount `/work`) were
substituted, and `.lyrdb` files are unmodified. [`manifest.json`](manifest.json) lists every copy with its
original path, original SHA-256 and bytes, and copy SHA-256. All copies are < 300 kB (largest: the main
lyrdb, 113 758 bytes). `*.pid` files were not copied.

Retention list (bulk only, over 300 kB; also in `manifest.json` → `bulk_only`):

| File | Bytes | SHA-256 |
|---|---|---|
| `$R/signoff/lvs_projected/g1_chip_top_1414_r4.lvsdb` | 189 319 950 | `7b8232b3944299d8b2b5fdbc94122b069ee6857d02753e8d5f5b2331b717d086` |
| `$R/signoff/lvs_projected/g1_chip_top_1414_r4_extracted.cir` | 10 906 907 | `9edb95aa118063f90ed3e1e9660b9a5faa4f1e0260a98e67c2bac68112f795b4` |
| `$R/signoff/lvs_canonical/g1_chip_top_1414_r4.lvsdb` | 133 620 580 | `4a89f32984851815093c7327b61ac8e7dac51c3122a31cccd971066adfccbc7a` |
| `$R/signoff/lvs_canonical/g1_chip_top_1414_r4_extracted.cir` | 874 668 | `e720b1719671b53e588a147e3555dd4472d25cabf26dc37a0b68a1f06a8718c3` |
| `$R/signoff_report_xor/g1_digital_cut_r3.gds` | 4 838 446 | `183a3496a144bbcc3ad6a2a9a32526e43e59ef8022d81ece768f5051c5b29ef9` |
| `$R/signoff_report_xor/g1_digital_cut_r4.gds` | 4 838 446 | `183a3496a144bbcc3ad6a2a9a32526e43e59ef8022d81ece768f5051c5b29ef9` |
| `$R/cdl/g1_chip_top_1414_r4_projected_ref.cdl` | 17 122 133 | `27a27cd64dfa18db66e2e9374c78b62f2d4ac95440d071149ffb048702e08fda` |

Failed build attempts 1 and 2 and the superseded build 3 are kept in `$R/signoff_attempt1/`, `$R/attempt2/`,
`$R/attempt3/` (candidate README "Chip r4").

Commands for the report XOR checks (from `${REPO}`, `G1_CPUSET=45-47 G1_CONTAINER_ENGINE=podman G1_RESULTS_ROOT=$R`,
scripts copied under `digital_identity/`):

```
flow/run.sh klayout -b -r cell_xor.py -rd a=<r3 gds> -rd ca=__rz_port_text_000_retained_g1_digital \
   -rd b=<r4 gds> -rd cb=__rz_port_text_000_retained_g1_digital -rd out=$R/signoff_report_xor/digital_xor_r3_r4.json
flow/run.sh klayout -b -r cell_cut.py -rd src=<r3|r4 gds> -rd cell=__rz_port_text_000_retained_g1_digital -rd out=$R/signoff_report_xor/g1_digital_cut_<r3|r4>.gds
flow/run.sh klayout -b -r cell_xor.py -rd a=$R/cand/g1_trip_nf4_novclk.gds -rd ca=g1_trip \
   -rd b=<r4 gds> -rd cb=__rz_port_text_033_retained_g1_trip -rd out=$R/signoff_report_xor/trip_cand_vs_r4chip_xor.json
```

The TRIP-cell check was re-run here because the candidate README records its result ("XOR 0 on every
layer, texts equal") without a retrievable output file.

## Block-to-netlist map

All blocks except TRIP are unchanged from r3 (digital: byte-identical, above; others: XOR r3 → r4 shows no
change outside the TRIP box except 5/22). The TRIP row is replaced:

| Block (chip cell) | Variant physically present | Layout identity | Netlist in canonical CDL | Post-layout extraction bound to this layout |
|---|---|---|---|---|
| TRIP (`__rz_port_text_033_retained_g1_trip`, R0 at 771, 736 µm) | `nf4_novclk`: r3 NF4 TRIP with `XCLKI` replaced by `g1_novclk` | equal to `$R/cand/g1_trip_nf4_novclk.gds` `3213819a…` (XOR 0, texts equal, this report) | `g1_trip` source block of the r3 CDL with the two-line edit and `g1_novclk` subckt (`make_chip_cdl.py`); block LVS vs `g1_trip_nf4_novclk_lvs.cdl` `8943a5a8…` passed (candidate README gate 2) | kpex 2.5D CC `blocks/g1_trip/sim/postlayout/g1_trip_nf4_novclk_pex.spice` `6f518e07…` (run on the first write `ef3f07b0…`, XOR 0 against `3213819a…`) |

## Bond map

**Not run** for r4. The r3 bond map `padframe/bondmap_20260926_r4.csv` is bound to r3's hash `7d07a784…`.
Pads, openings and labels are unchanged by the XOR r3 → r4 (no change outside the TRIP box except 5/22 fill,
0 text differences), but `verify_bondmap.py` was not run on r4 and no r4-bound bond map was written.

## Not run

- GDS inventory and stock-name check on r4: not run (XOR r3 → r4 bounds the change).
- Bond-map verification against the r4 hash: not run.
- Second-opinion DRC with the IHP dev-branch deck (r3 `devdeck_check/`): not run on r4.
- Digital macro flow, STA, GLS, formal equivalence: not re-run; the macro is byte-identical to r3 and r3's results apply.
- Merged-SDC chip STA on the r4 chip netlist: not run.
- Full-chip (assembled) PEX, IR drop/EM, full-chip STA with extracted parasitics: not run.
- Full-chip transient simulation of r4: run separately under `blocks/g1_top/sim/`; not part of this report.
- Canonical unprojected LVS passing: run, **failed** (PDK IO-cell reference semantics, as r1/r2/r3).
- Block-map XOR re-run for the unchanged analog blocks: not run. XOR r3 → r4 shows no change outside the TRIP box except 5/22.
- GDS hash recorded immediately after the runs: not recorded; re-hashed at report assembly instead.
- IHP intake/rejection test; written IHP die-area confirmation: open (as r3).
- Measurement: not run (no silicon).

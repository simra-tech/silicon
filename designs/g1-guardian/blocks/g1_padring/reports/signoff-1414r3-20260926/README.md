# G1 1414 µm chip, revision r3: re-hardened g1_digital (RTL ECO, register map 1.2) and GatPoly fill, full physical sign-off (2026-09-26)

`g1_chip_top_1414_r3.gds` is the **file of record** from 2026-09-26. It supersedes `g1_chip_top_1414_r2.gds`
(`9049e87b0303893573ed82f56a5d41f926c4db126e8d972062553c7d19996d2c`). r2 stays the documented fallback: its
GDS is retained outside the tree (`review/local-retention-20260925.json`), and its CDLs and sign-off
([`signoff-1414r2-20260925`](../signoff-1414r2-20260925/README.md)) are unchanged.

**r3 = r2 + the re-hardened `g1_digital` macro + 700 µm² of GatPoly fill.**
1. **The macro.** The cell `__rz_port_text_000_retained_g1_digital` has new content. It is
   hardened from the RTL ECO of 2026-09-25/26 (register map 1.2,
   [`blocks/g1_ctrl/ECO_20260925.md`](../../../g1_ctrl/ECO_20260925.md)) and is pin-compatible with
   r2's macro. The instance, its placement and the cell name are unchanged.
2. **The fill.** 100 GatPoly fill rectangles (5/22) in the top cell, outside the macro outline,
   restore global GatPoly density.

Owner decision 2026-09-25: adopt the RTL ECO through pin-compatible re-hardening (`PLAN.md` D16).
The RTL was confirmed at chip level before promotion, on the hand-wired chip deck
(`run_top.py --blockset c1414`: block extractions with the BGR586 schematic view, SENSE pads
without `dantenna`, fitted `GATE` driver about 7 % optimistic, ideal clock, ECO RTL as a
behavioural digital; not a full-chip extraction):
- `eco_c_mid_m03`: `tripped` 1.166 µs, `GATE` < 1 V at 1.451 µs;
- `eco_hard_pulse_m03`: no trip.

Both are recorded in `ECO_20260925.md`. Their decks, JSON summaries and tail extracts are committed under `blocks/g1_top/sim/` (commit d53aeedb); raw logs over 300 kB are retained by hash in `review/local-retention-20260925.json`.

No top-level routing, pad, opening, label, block or other fill changed (XOR below). This is
physical verification only. Full-chip PEX, IR/EM and timing sign-off of the assembled chip are
**not run** (see "Not run").

## Built against

| Item | Value | How established |
|---|---|---|
| PDK | IHP-Open-PDK `84374023ee8b4b126bebbba67fcbada0a9c0ff0b` | `flow/run.sh` refuses to start unless `/foss/pdks/ihp-sg13g2/COMMIT` matches |
| Container image | `sha256:ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2` | `flow/run.sh` image identity check |
| LibreLane | 3.1.0.dev2, Classic flow plus the `librelane_plugin_g1eco` step `G1.SplitClockRoot` | `librelane --version`; `resolved.json` |
| OpenROAD | 26Q1-1024-gdcf36133a (`openroad-librelane`, via `_LLN_OVERRIDE_OPENROAD`) | SPEF header |
| KLayout / OpenSTA / Icarus | 0.30.9 / 3.1.0 / 14.0 (devel) | `klayout -v`, `sta -version`, GLS log headers |
| Rule decks | stock `run_drc.py`, `run_lvs.py` and decks of the PDK above, unmodified | invoked from `/foss/pdks/ihp-sg13g2/libs.tech/klayout/tech/` |
| CPUs | macro flow 88-95; chip checks 64-79 (`taskset`, rootless cgroups v1) | `flow/launch_pinned.sh`, `G1_CPUSET` |

## Files of record

| File | SHA-256 | Notes |
|---|---|---|
| `layout/g1_chip_top_1414_r3.gds` | `7d07a7841a531f51e08b0c90e76fe603889cd2ef29905e309e63f09742e688f2` | **File of record.** Top `g1_chip_top`, 304 cells, 84 097 180 bytes, BGNLIB timestamps zero. Byte copy of the checked file `${BULK}/digital-eco-r3cand2-20260926/chip/g1_chip_top_1414_r3_candidate.gds` (written by `add_gatpoly_fill.py` without GDS timestamps) |
| `netlist/g1_chip_top_1414_r3.cdl` | `5e47ae022ab73b4e060afaee22a1299bc62e1a895f4c9e15f865820505d52629` | Canonical reference: r2 CDL (`41d47877…`) with only the `.SUBCKT g1_digital` block replaced, plus one header line. The header still reads "CANDIDATE … not promoted", as written; it was kept so the bytes stay the ones LVS ran on |
| `netlist/g1_chip_top_1414_r3_projected_ref.cdl` | `d0d36c841a7a111d19fead1c973cec51fd4134251216c99f177ce01e7f71ccea` | Flat comparison-only projected reference (77 017 devices, 22 pins) |
| `padframe/bondmap_20260926_r4.csv` | `99080d81a3871d668bfe3ddf0c79faee7351371aa8c3cae9d4d3b7469630ebd2` | Bond map bound to r3 (see "Bond map") |
| `review/tapein/gds_inventory_g1_chip_top_1414_r3.json` | — | GDS inventory (see "r3 identity") |

`$R` below is `${BULK}/digital-eco-r3cand2-20260926`, the full run root. It holds the RTL
snapshot, LibreLane runs, final views, STA, swap, fill, CDL and sign-off reports. The whole run is
`BULK=${BULK} designs/g1-guardian/blocks/g1_ctrl/flow/eco/run_candidate.sh $R` (stages
`macro`, `chip`, `signoff`, `post`).

RTL (hashes in `$R/inputs_sha256.txt`, checked against the frozen list):

| File | SHA-256 |
|---|---|
| `g1_ctrl/rtl_eco_20260925/g1_regfile.v` | `33d549da…` (MODE reset 0x03, FAST_EN = 0) |
| `g1_digital_top.v` | `4e3b8ff6…` (fast path gated by `fast_dly[2]`) |
| `g1_digital.v` | `36757122…` |
| `g1_serial.v` | `df4341e1…` |
| `g1_sync2.v` | `c14906d7…` |
| `g1_trip_timer.v` | `5cab0bc3…` |
| `g1_seu/rtl_eco_20260925/g1_tmr_reg.v` | `f53f82d9…` |
| `g1_seu_chain.v` | `6e10bbc0…` |
| `g1_seu.v` | `7c1831c9…` |
| SDC `blocks/g1_ctrl/flow/g1_digital.sdc` | `c36bf030…`, unchanged |

## r3 identity

| Check | Result | Output |
|---|---|---|
| GDS inventory (`review/tapein/gds_inventory.py`) | **passed**. 73 layers, all defined in the PDK `sg13g2.lyp`, none outside it. Top `g1_chip_top`, bbox 1414 × 1414 µm, 304 cells (r2: 306). Seal ring, 24 Passiv openings, bondpad and IO cells, PolyRes and text-purpose layers equal r2's. The flat counts of 22 layers differ, all from macro content (e.g. 8/25 +281 texts, 30/0 +2480) and 5/22 +100. Control: `gds_inventory.py` re-run on the retained r2 GDS reproduces the committed r2 inventory exactly (only the path differs) | [`review/tapein/gds_inventory_g1_chip_top_1414_r3.json`](../../../../review/tapein/gds_inventory_g1_chip_top_1414_r3.json) |
| Stock-name check (`flow/signoff/1414r2/stock_compare.py`) | **passed**. 52 cells whose exact name is a PDK cell, **0 differ** (r2: 51/0; the new stdcell set of the macro). `$N` variants 61/43 and `retained_*` 19, as r2 | [`stock_compare/stock_compare_r3.json`](stock_compare/stock_compare_r3.json) |
| Swap method control (`swap_macro.py` with r2's own macro `1a662082` swapped into r2) | **passed**: whole-cell XOR 0 on all layers, deep Metal1 labels 31 928 = 31 928, 29 label clones as in r2, rest of the chip unchanged. Re-run after the floating-output fix | [`controls/swap_self_control.json`](controls/swap_self_control.json) |
| CDL method control (`regen_chip_cdl.py` + `flatten_reference.rb` from r2's pnl `4fd0b616`) | **passed**: `g1_digital` block byte-identical to r2's; flat reference Match with `g1_chip_top_1414_projected_ref.cdl` (76 059 devices, 31 906 nets, 22 pins) | [`controls/cdl_regen_control.json`](controls/cdl_regen_control.json), [`controls/flatten_control.json`](controls/flatten_control.json) |

## What changed from r2, and how it was made

The steps are [`../../../g1_ctrl/flow/eco/RUNBOOK.md`](../../../g1_ctrl/flow/eco/RUNBOOK.md)
1-6. The method and dry run are in
[`../../../g1_ctrl/ECO_FLOW_FEASIBILITY_20260925.md`](../../../g1_ctrl/ECO_FLOW_FEASIBILITY_20260925.md).

1. **Macro.** LibreLane re-hardened the macro from `config_tmr_spread.yaml` (run7) with these changes:
   - pins copied from run7 through `FP_DEF_TEMPLATE` in strict mode (44 signal pins);
   - `CTS_SINK_CLUSTERING_SIZE` 8, plus `G1.SplitClockRoot`;
   - `RT_MAX_LAYER` Metal5;
   - TMR seeds regenerated from this RTL's first pass (`tmr_spread.py`).

   Results (typ/fast/slow):

   | Check | Result |
   |---|---|
   | Setup / hold worst slack | 28.82/29.04/28.45 ns / 0.195/0.114/0.337 ns |
   | Violations | 0 setup, hold, max-slew, max-cap and max-fanout |
   | Clock-buffer fanout | 225 clock-buffer nets, maximum fanout 8 |
   | Routing DRC, antenna | 0 / 0 |
   | Magic / KLayout DRC | 0 / 0 |
   | netgen LVS | clean |
   | Stream-out XOR | 0 |
   | TMR separation | all 199 stages ≥ 27.4 µm (criterion 20 µm) |
   | Merged-SDC STA inside the chip netlist (`reports/sta_merged_sdc_20260924/run_sta.sh`, unchanged) | setup 27.25/27.99/25.70 ns, hold 0.195/0.114/0.337 ns: 0 setup/hold violations; 12 analog-pad max-slew flags per corner (placeholder library values) and 98 unannotated drivers, dispositioned (`$R/sta/main/`) |
   | Registers | 1170 `osc_clk`, 52 `sclk` |

   Wall time: first pass 54 s, main flow 1237 s on 8 CPUs.
2. **Pins** ([`r3_identity/pincmp_final.json`](r3_identity/pincmp_final.json)):
   - all 64 pin shapes are identical to r2's macro cell;
   - the new TopMetal1/2 drawing is a subset of r2's (PDN only);
   - labels differ only by the 7 unconnected-pin labels that r2's port-text normalisation
     had already removed.
3. **Swap** (`swap_macro.py`, [`r3_identity/swap.json`](r3_identity/swap.json)):
   - the 76 private sub-cells of the old macro were removed and 49 new ones created;
   - the 7 unconnected-pin labels were removed;
   - 27 per-instance clones strip the output label of floating clock dummy loads
     (`sg13g2_inv_2/4` and `sg13g2_buf_4`);
   - pin-layer XOR 0; TopMetal inside the old; rest of the chip unchanged on every layer.
   - The first swap attempt aborted on an assertion (a floating-output detection bug on the
     buffer `wire100`; fixed, see RUNBOOK). It is kept in `$R/chip_attempt1_swap_assert/`.
4. **GatPoly fill** (`add_gatpoly_fill.py`, [`r3_identity/fill.json`](r3_identity/fill.json)):
   - 100 rectangles of at most 5.0 × 1.4 µm, 700 µm² in total;
   - placed only outside the macro outline + 1.1 µm, and 1.1 µm from the GFil.d/e layers;
   - global GatPoly goes from 14.9959 % (after the swap) to **15.0309 %**. r2 is at 15.02 %.
5. **XOR r2 → r3** (`chip_xor.py`, [`r3_identity/chip_xor.json`](r3_identity/chip_xor.json)):
   - **outside the macro outline, only 5/22 changed** (+100 polygons, 700.0 µm²), with 0 text
     differences;
   - inside the outline, only the macro's own layers changed: 1/0, 5/0, 6/0, 8/0, 8/2, 8/25, 10/0,
     14/0, 19/0, 29/0, 30/0, 31/0, 49/0, 50/0, 66/0, 67/0, 125/0, 126/0 (cell content and routing),
     63/0 (4 texts of the macro content differ) and 99/31 (4 more antenna-diode recognition shapes);
   - 134/0, the macro pin layers 10/2, 30/2, 126/2, 134/2, and 9/0 and 39/x are unchanged.
6. **CDL** (`regen_chip_cdl.py`, [`r3_identity/regen.json`](r3_identity/regen.json)):
   - `g1_digital` comes from the new powered netlist through `verilog_to_subckt`
     (`assemble_chip_cdl.py`), with the top-level bus spelling restored;
   - `assign osc_en = net385` (tie-high) is resolved;
   - every other line is byte-identical to r2's CDL (checked);
   - projection: the one dummy `MP0` line of `G1_VSS_DERIVATIVE__sg13g2_LevelDown` is removed
     (exact inverse);
   - flattened by `flatten_reference.rb`, roundtrip Match
     ([`r3_identity/flatten_projected_ref.json`](r3_identity/flatten_projected_ref.json)).

   Method control: from the r2 chip's own pnl (`4fd0b616`), the regenerated `g1_digital` block
   is byte-identical to r2's, and the flat reference matches `g1_chip_top_1414_projected_ref.cdl`
   (76 059 devices, 31 906 nets, 22 pins).

## Physical checks on `g1_chip_top_1414_r3.gds` (`7d07a784…`)

Every check ran detached through `flow/launch_pinned.sh` with a 5400 s bound and top cell
`g1_chip_top`, all at the same time on disjoint CPU sets. The options are the same as r2's
(r2 README "Commands"; `run_candidate.sh` stage `signoff`).

| Check | CPUs | Result | Markers | Wall | Report (copy here; original in `$R/signoff/`) |
|---|---|---|---|---|---|
| Main DRC | 64-67 | **passed** | 0 | 416 s | `drc_main/…_main.lyrdb` `3da5e270…` |
| Maximal DRC | 68-71 | **passed** | 0 | 887 s | `drc_maximal/…_sg13g2_maximal.lyrdb` `f54b65a5…` |
| Density | 72-73 | **passed** | 0 | 55 s | `density/…_density.lyrdb` `89149c55…` |
| Antenna | 74-75 | **passed** | 0 | 183 s | `antenna/…_antenna.lyrdb` `71533d82…` |
| Precheck (`--precheck_drc --disable_extra_rules`, with density) | 76-77 | **passed** | 0 | 369 s | `precheck/…_full.lyrdb` `92416e92…` |
| LVS, projected reference (`netlist/g1_chip_top_1414_r3_projected_ref.cdl`), strict ports | 78 | **passed** | Netlists match: 62 940/62 940 devices, 31 816/31 816 nets, **22/22 pins** | 276 s | [`lvs_projected/pair_counts.json`](lvs_projected/pair_counts.json); lvsdb `0f79a4b4…` bulk only |
| LVS, canonical unprojected reference (`netlist/g1_chip_top_1414_r3.cdl`) | 79 | **failed** (as r2) | "Netlists don't match". The same 14 IO/level-shifter sub-circuits NoMatch, top `Skipped`. Every non-Match circuit has exactly r2's status and device/net/pin/subcircuit counts. 35 Match: r2's 34 plus `sg13g2_antennanp` (antenna diodes in the new macro) | 238 s | [`lvs_canonical/pair_counts.json`](lvs_canonical/pair_counts.json); lvsdb `1e1d14a0…` bulk only |

The five DRC lyrdb hashes equal r2's (an empty report carries only the rule catalogue). Every
run exited with code 0. The checks ran on the bulk file `$R/chip/g1_chip_top_1414_r3_candidate.gds`, which is byte-identical to `layout/g1_chip_top_1414_r3.gds` (same SHA-256 `7d07a784…`). The GDS SHA was checked again after all runs and was unchanged.

## Evidence copies in this folder

The summary logs, reports, `run.log` and return codes of every chip check were copied from `$R/signoff/`.
As in r2, only `${BULK}` and `${REPO}` were substituted in the copies. [`manifest.json`](manifest.json) lists, per
file, the original and copy SHA-256. All copies are < 300 kB.

The LVS databases and extracted netlists are bulk only, with their hashes in `review/local-retention-20260925.json`:

| File | Bytes | SHA-256 |
|---|---|---|
| `lvs_projected/…lvsdb` | 189 314 512 | `0f79a4b4…` |
| `lvs_projected/…_extracted.cir` | 10 904 326 | `91a9a77f…` |
| `lvs_canonical/…lvsdb` | 133 615 872 | `1e1d14a0…` |
| `lvs_canonical/…_extracted.cir` | 872 087 | `d2a436f0…` |

The macro flow summary, the TMR separation, the view hashes and the 6 STA summaries are in [`macro/`](macro/).

| File | Bytes (original) | Original SHA-256 | Paths normalised |
|---|---|---|---|
| [`drc_main/drc_run_2026_09_25_19_41_07.log`](drc_main/drc_run_2026_09_25_19_41_07.log) | 882 | `732670ae…` | yes |
| [`drc_main/g1_chip_top_1414_r3_candidate_g1_chip_top_main.log`](drc_main/g1_chip_top_1414_r3_candidate_g1_chip_top_main.log) | 80 241 | `7d918609…` | yes |
| [`drc_main/g1_chip_top_1414_r3_candidate_g1_chip_top_main.lyrdb`](drc_main/g1_chip_top_1414_r3_candidate_g1_chip_top_main.lyrdb) | 113 758 | `3da5e270…` | no |
| [`drc_main/run.log`](drc_main/run.log) | 81 727 | `9a952371…` | yes |
| [`drc_main/run.log.rc`](drc_main/run.log.rc) | 2 | `9a271f2a…` | no |
| [`drc_maximal/g1_chip_top_1414_r3_candidate_g1_chip_top_sg13g2_maximal.log`](drc_maximal/g1_chip_top_1414_r3_candidate_g1_chip_top_sg13g2_maximal.log) | 1 045 | `a493fcbc…` | yes |
| [`drc_maximal/g1_chip_top_1414_r3_candidate_g1_chip_top_sg13g2_maximal.lyrdb`](drc_maximal/g1_chip_top_1414_r3_candidate_g1_chip_top_sg13g2_maximal.lyrdb) | 46 871 | `f54b65a5…` | no |
| [`drc_maximal/run.log`](drc_maximal/run.log) | 9 827 | `bbfd1750…` | yes |
| [`drc_maximal/run.log.rc`](drc_maximal/run.log.rc) | 2 | `9a271f2a…` | no |
| [`density/drc_run_2026_09_25_19_41_11.log`](density/drc_run_2026_09_25_19_41_11.log) | 951 | `6a85b2f8…` | yes |
| [`density/g1_chip_top_1414_r3_candidate_g1_chip_top_density.log`](density/g1_chip_top_1414_r3_candidate_g1_chip_top_density.log) | 12 064 | `f3ec557a…` | yes |
| [`density/g1_chip_top_1414_r3_candidate_g1_chip_top_density.lyrdb`](density/g1_chip_top_1414_r3_candidate_g1_chip_top_density.lyrdb) | 1 889 | `89149c55…` | no |
| [`density/run.log`](density/run.log) | 13 619 | `8caaebb1…` | yes |
| [`density/run.log.rc`](density/run.log.rc) | 2 | `9a271f2a…` | no |
| [`antenna/drc_run_2026_09_25_19_41_11.log`](antenna/drc_run_2026_09_25_19_41_11.log) | 952 | `fc11d476…` | yes |
| [`antenna/g1_chip_top_1414_r3_candidate_g1_chip_top_antenna.log`](antenna/g1_chip_top_1414_r3_candidate_g1_chip_top_antenna.log) | 9 334 | `bc30192a…` | yes |
| [`antenna/g1_chip_top_1414_r3_candidate_g1_chip_top_antenna.lyrdb`](antenna/g1_chip_top_1414_r3_candidate_g1_chip_top_antenna.lyrdb) | 7 361 | `71533d82…` | no |
| [`antenna/run.log`](antenna/run.log) | 10 890 | `095ca7b5…` | yes |
| [`antenna/run.log.rc`](antenna/run.log.rc) | 2 | `9a271f2a…` | no |
| [`precheck/drc_run_2026_09_25_19_41_09.log`](precheck/drc_run_2026_09_25_19_41_09.log) | 1 137 | `0ad841b0…` | yes |
| [`precheck/g1_chip_top_1414_r3_candidate_g1_chip_top_density.log`](precheck/g1_chip_top_1414_r3_candidate_g1_chip_top_density.log) | 11 530 | `b44a3078…` | yes |
| [`precheck/g1_chip_top_1414_r3_candidate_g1_chip_top_full.lyrdb`](precheck/g1_chip_top_1414_r3_candidate_g1_chip_top_full.lyrdb) | 93 590 | `92416e92…` | no |
| [`precheck/g1_chip_top_1414_r3_candidate_g1_chip_top_main.log`](precheck/g1_chip_top_1414_r3_candidate_g1_chip_top_main.log) | 72 143 | `eeac3d59…` | yes |
| [`precheck/run.log`](precheck/run.log) | 85 347 | `54dc31b8…` | yes |
| [`precheck/run.log.rc`](precheck/run.log.rc) | 2 | `9a271f2a…` | no |
| [`lvs_projected/g1_chip_top_1414_r3_candidate.log`](lvs_projected/g1_chip_top_1414_r3_candidate.log) | 36 463 | `6fe814fe…` | yes |
| [`lvs_projected/lvs_run_2026_09_25_19_41_10.log`](lvs_projected/lvs_run_2026_09_25_19_41_10.log) | 1 955 | `05511807…` | yes |
| [`lvs_projected/run.log`](lvs_projected/run.log) | 39 022 | `9049ecde…` | yes |
| [`lvs_projected/run.log.rc`](lvs_projected/run.log.rc) | 2 | `9a271f2a…` | no |
| [`lvs_canonical/g1_chip_top_1414_r3_candidate.log`](lvs_canonical/g1_chip_top_1414_r3_candidate.log) | 36 417 | `a2b8463f…` | yes |
| [`lvs_canonical/lvs_run_2026_09_25_19_41_11.log`](lvs_canonical/lvs_run_2026_09_25_19_41_11.log) | 2 118 | `5d4027d8…` | yes |
| [`lvs_canonical/run.log`](lvs_canonical/run.log) | 39 139 | `57b2b367…` | yes |
| [`lvs_canonical/run.log.rc`](lvs_canonical/run.log.rc) | 2 | `9a271f2a…` | no |
| [`input_gds.sha256`](input_gds.sha256) | 155 | `26d447f6…` | yes |
| [`input_gds.sha256.after`](input_gds.sha256.after) | 155 | `26d447f6…` | yes |

## Block-to-netlist map

All blocks except the digital are **unchanged from r2** (and r1: [`signoff-1414-20260924` block map](../signoff-1414-20260924/README.md#block-to-netlist-map-what-is-physically-in-629d303a)).
The XOR r2 → r3 above shows no change outside the macro outline except 5/22. The digital row is replaced:

| Block (chip cell) | Variant physically present | Layout identity | Netlist in canonical CDL = | Simulation | Post-layout extraction bound to this layout |
|---|---|---|---|---|---|
| Digital (`__rz_port_text_000_retained_g1_digital`, R0 at 367, 364 µm) | RTL ECO, register map 1.2, re-hardened pin-compatible (LibreLane, run `$R/runs/main`) | `$R/final/gds/g1_digital.gds` `67d049bf…`, copied into the cell by `swap_macro.py` (content equal apart from the 7 removed unconnected-pin labels and 27 label-stripped dummy-load clones) | `g1_digital` from powered netlist `476885d7…` (`verilog_to_subckt`, `assign osc_en` resolved) | Gate netlist `4b83f1812af385d22302123970443cf63d8889d622794671d31a8e05c9cd9347`, GLS **passed**: 21 tests / 260 checks, functional (unit delay) and SDF typ `f2a807f0…` (`blocks/g1_ctrl/sim/gls_eco_r3v2/`). 21/21 functional. Red-team bench on the netlist: 4 pass, R3 **fails** (serial framing, out of the ECO scope) (`tb_redteam_eco_gls_r3cand2.log`). Icarus executes no timing checks and drops part of the SDF delay model (68 unsupported `ifnone` paths) | SPEF nominal `0b626c7f…`. STA with the merged chip SDC (`reports/sta_merged_sdc_20260924/run_sta.sh`), typ/fast/slow: macro setup 28.82/29.04/28.45 ns, hold 0.195/0.114/0.337 ns; inside the chip netlist setup 27.25/27.99/25.70 ns, same hold; 0 violations (`$R/sta/main/`) |

## Bond map

[`padframe/bondmap_20260926_r4.csv`](../../../../padframe/bondmap_20260926_r4.csv) (`99080d81…`) is
[`bondmap_20260925_r3.csv`](../../../../padframe/bondmap_20260925_r3.csv) (`ead5f109…`, r2-bound) with only
the hash column set to `7d07a784…`. Pads, openings and labels are unchanged. It was written by
`padframe/bondplan_20260925.py` with `-rd gds_sha=7d07a784…`, which also rewrote the SVG title hash and the
JSON path and hash lines. Lead assignment, wire lengths and 0 crossings are unchanged.

`verify_bondmap.py` result:
- **passed** (`all_ok: true`);
- 24 openings and 24 rows, 22 labels at the row centres;
- output: [`bondmap/verify_bondmap_r4.json`](bondmap/verify_bondmap_r4.json).

## History (candidates)

The promoted file is candidate v2, unchanged. **Candidate v1 (2026-09-25), superseded.** Its RTL had `g1_regfile.v` `605d7385…` (MODE reset
0x23, FAST_EN = 1) and `g1_digital_top.v` `5c872e3b…`; the coordinator withdrew that default.
Its README and evidence are kept in [`history_v1/`](history_v1/README_v1_superseded.md), and
its bulk root is `${BULK}/digital-eco-r3cand-20260925/`.

| v1 file | SHA-256 |
|---|---|
| Candidate GDS | `c88261ff5185fb1409408c8ca76c4fc62de8abac8d050483bc34edee48e02545` |
| Canonical CDL | `21152b66b813f0937931b2e40fb4c0a140c6cdf78d7c66c1b91590223f7ad4c5` |
| Projected reference | `af66d18d3aa8add68d96ee28ac8332b6bf8a4a3ca1bff701503c685f8d0fa97b` |
| Macro GDS | `89bce861…` |
| Gate netlist | `c3aa2856…` |

v1's results: all DRC checks 0, projected LVS 22/22 pins, and canonical LVS equal to r2's
pattern.

## Not run

- Full-chip (assembled) PEX, full-chip transient/electrical simulation of the r3 GDS itself, IR drop/EM, full-chip STA with extracted parasitics.
  - The chip-level ECO runs (`eco_c_mid_m03`, `eco_hard_pulse_m03`) use the extracted chip with the ECO RTL as a
    behavioural digital, not this extracted macro.
- Formal equivalence of the ECO RTL against the gate netlist `4b83f181`: not run.
- SDF GLS at fast and slow corners (SDFs exist in bulk): not run.
- Chip-level co-simulation with the hardened macro's gate netlist + SPEF: not run.
- Chip-level power-up (gB/gA), the 72-cell matrix and the CDL-driven deck with the frozen ECO RTL: not run.
- Canonical unprojected LVS passing: run, **failed** (PDK IO-cell reference semantics, as r1/r2).
- Block-map XOR re-run for the unchanged blocks: not run. The r2 → r3 XOR shows no change outside the macro except 5/22.
- IHP intake/rejection test; written IHP die-area confirmation: open (as r2).
- Measurement: not run (no silicon).

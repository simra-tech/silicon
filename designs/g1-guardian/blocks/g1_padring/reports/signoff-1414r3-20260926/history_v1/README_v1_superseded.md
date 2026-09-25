> **SUPERSEDED (2026-09-26)** by r3 candidate v2 (`../README.md`). Kept for history only.

# G1 1414 µm chip, revision r3 CANDIDATE: g1_digital ECO swap, poly fill, physical sign-off (2026-09-25/26)

> **CANDIDATE — not promoted; awaiting chip-level co-sim of the RTL.**
> The ECO RTL was hardened before it was frozen. If the chip-level co-sim (`eco_c_mid_r2`)
> fails, this candidate is discarded. The r3 candidate GDS and CDLs are held in bulk storage,
> not in this repository. `g1_chip_top_1414_r2.gds` (`9049e87b…`) stays the file of record,
> and its records are unchanged.

r3 differs from r2 in two ways only:
1. **The cell `__rz_port_text_000_retained_g1_digital` has new content.** The instance, its
   placement and the cell name are unchanged. The new macro is re-hardened from the ECO RTL,
   pin-compatible with r2's macro.
2. **100 GatPoly fill rectangles (5/22, 700 µm²) were added in the top cell.** They are
   outside the macro outline and restore global GatPoly density.

No top-level routing, pad, block or other fill changed (XOR below). This is physical
verification only. Full-chip PEX, IR/EM and timing sign-off are **not run** (see "Not run").

## Built against

| Item | Value | How established |
|---|---|---|
| PDK | IHP-Open-PDK `84374023ee8b4b126bebbba67fcbada0a9c0ff0b` | `flow/run.sh` refuses to start unless `/foss/pdks/ihp-sg13g2/COMMIT` matches |
| Container image | `sha256:ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2` | `flow/run.sh` image identity check |
| LibreLane | 3.1.0.dev2, Classic flow plus the `librelane_plugin_g1eco` step `G1.SplitClockRoot` | `librelane --version`; `resolved.json` |
| OpenROAD | 26Q1-1024-gdcf36133a (`openroad-librelane`, via `_LLN_OVERRIDE_OPENROAD`) | SPEF header |
| KLayout | 0.30.9 | `klayout -v` in the container |
| OpenSTA | 3.1.0 | `sta -version` |
| Rule decks | stock `run_drc.py`, `run_lvs.py` and decks of the PDK above, unmodified | invoked from `/foss/pdks/ihp-sg13g2/libs.tech/klayout/tech/` |
| CPUs | macro flow 88-95; chip checks 64-79 (`taskset`, rootless cgroups v1) | `flow/launch_pinned.sh`, `G1_CPUSET` |

## Files (candidate; bulk only until promotion)

`$R` = `${BULK}/digital-eco-r3cand-20260925`.

| File | SHA-256 | Notes |
|---|---|---|
| `$R/chip/g1_chip_top_1414_r3_candidate.gds` | `c88261ff5185fb1409408c8ca76c4fc62de8abac8d050483bc34edee48e02545` | **The file checked below.** Top cell `g1_chip_top` |
| `$R/chip/swapped.gds` | `8c6902fd…` | Intermediate: r2 with the macro swapped, before fill |
| `$R/cdl/g1_chip_top_1414_r3.cdl` | `21152b66b813f0937931b2e40fb4c0a140c6cdf78d7c66c1b91590223f7ad4c5` | Canonical reference: r2 CDL (`41d47877…`) with only the `.SUBCKT g1_digital` block replaced, plus one header line |
| `$R/cdl/g1_chip_top_1414_r3_projected_ref.cdl` | `af66d18d3aa8add68d96ee28ac8332b6bf8a4a3ca1bff701503c685f8d0fa97b` | Flat comparison-only projected reference (76 919 devices, 22 pins) |
| `$R/final/gds/g1_digital.gds` | `89bce861…` | New macro. Its netlist, SDF and SPEF hashes are in [`../../../g1_ctrl/flow/eco/HANDOFF.md`](../../../../g1_ctrl/flow/eco/HANDOFF.md) |
| `$R/bondmap/bondmap_r3cand.csv` | `70980fc0…` | Candidate bond map. Copy here: [`bondmap/bondmap_r3cand.csv`](bondmap/bondmap_r3cand.csv) |

RTL: `g1_ctrl/rtl_eco_20260925/` and `g1_seu/rtl_eco_20260925/`, read from a snapshot in
`$R/rtl_snapshot/`. `g1_digital_top.v` is `5c872e3b…` (fast path gated by `fast_dly[2]`).
The other eight files are listed with their hashes in `HANDOFF.md`. The SDC is unchanged
(`c36bf030…`).

## What changed from r2, and how it was made

The commands are [`../../../g1_ctrl/flow/eco/RUNBOOK.md`](../../../../g1_ctrl/flow/eco/RUNBOOK.md)
steps 1-5, with `R` as above. The method and dry run are in
[`../../../g1_ctrl/ECO_FLOW_FEASIBILITY_20260925.md`](../../../../g1_ctrl/ECO_FLOW_FEASIBILITY_20260925.md).

1. **Macro.** LibreLane re-hardened the macro from `config_tmr_spread.yaml` (run7) with these changes:
   - pins copied from run7 through `FP_DEF_TEMPLATE` in strict mode (44 signal pins);
   - `CTS_SINK_CLUSTERING_SIZE` 8, plus `G1.SplitClockRoot` (clock-buffer fanout ≤ 8);
   - `RT_MAX_LAYER` Metal5;
   - TMR seeds regenerated from this RTL's first pass (`tmr_spread.py`).

   Results (typ/fast/slow):

   | Check | Result |
   |---|---|
   | Setup / hold worst slack | 28.82/29.04/28.44 ns / 0.186/0.106/0.328 ns |
   | Violations | 0 setup, hold, max-slew, max-cap and max-fanout |
   | Clock-buffer fanout | 223 clock-buffer nets, maximum fanout 8 |
   | Routing DRC, antenna | 0 / 0 |
   | Magic / KLayout DRC | 0 / 0 |
   | netgen LVS | clean |
   | Stream-out XOR | 0 |
   | TMR separation | all 199 stages ≥ 22.9 µm (criterion 20 µm) |
   | Merged-SDC STA inside the chip netlist (`reports/sta_merged_sdc_20260924/run_sta.sh`, unchanged) | setup 27.25/27.99/25.70 ns, hold 0.186/0.106/0.328 ns, 0 violations |
   | Registers | 1170 `osc_clk`, 52 `sclk` |

   Wall time: first pass 51 s, main flow 757 s on 8 CPUs.
2. **Pins** ([`r3_identity/pincmp_final.json`](r3_identity/pincmp_final.json)):
   - all 64 pin shapes are identical to r2's macro cell;
   - the new TopMetal1/2 drawing is a subset of r2's (PDN only);
   - labels differ only by the 7 unconnected-pin labels that r2's port-text normalisation
     had already removed.
3. **Swap** (`swap_macro.py`, [`r3_identity/swap.json`](r3_identity/swap.json)):
   - the 76 private sub-cells of the old macro were removed and 49 new ones created;
   - the 7 unconnected-pin labels were removed;
   - 18 per-instance clones strip the output label of floating clock dummy loads:
     15 `sg13g2_inv_{2,4,8}` and 3 `sg13g2_buf_4`;
   - pin-layer XOR 0; TopMetal inside the old; rest of the chip unchanged on every layer.
4. **GatPoly fill** (`add_gatpoly_fill.py`, [`r3_identity/fill.json`](r3_identity/fill.json)):
   - 100 rectangles of at most 5.0 × 1.4 µm, 700 µm² in total;
   - placed only outside the macro outline + 1.1 µm, and 1.1 µm from the GFil.d/e layers;
   - global GatPoly goes from 14.9948 % (after the swap) to **15.0299 %**. r2 is at 15.02 %.
5. **XOR r2 → r3 candidate** (`chip_xor.py`, [`r3_identity/chip_xor.json`](r3_identity/chip_xor.json)):
   - **outside the macro outline, only 5/22 changed** (+100 polygons, 700.0 µm²), with 0 text
     differences;
   - inside the outline, only the macro's own layers changed.
6. **CDL** (`regen_chip_cdl.py`, [`r3_identity/regen.json`](r3_identity/regen.json)):
   - `g1_digital` comes from the new powered netlist through `verilog_to_subckt`
     (`assemble_chip_cdl.py`), with the top-level bus spelling restored;
   - `assign osc_en = net383` (tie-high) is resolved;
   - every other line is byte-identical to r2's CDL (checked);
   - projection: the one dummy `MP0` line of `G1_VSS_DERIVATIVE__sg13g2_LevelDown` is removed
     (exact inverse);
   - flattened by `flatten_reference.rb`, roundtrip Match
     ([`r3_identity/flatten_projected_ref.json`](r3_identity/flatten_projected_ref.json)).

   Method control: from the r2 chip's own pnl (`4fd0b616`), the regenerated `g1_digital` block
   is byte-identical to r2's, and the flat reference matches `g1_chip_top_1414_projected_ref.cdl`
   (76 059 devices, 31 906 nets, 22 pins).

## Physical checks on `g1_chip_top_1414_r3_candidate.gds` (`c88261ff…`)

Every check ran detached through `flow/launch_pinned.sh` with a 5400 s bound and top cell
`g1_chip_top`, on disjoint CPU sets. The options are the same as r2's (see r2 README "Commands").

| Check | CPUs | Result | Markers | Wall | Report (bulk `$R/signoff/`) |
|---|---|---|---|---|---|
| Main DRC | 64-67 | **passed** | 0 | 460 s | `drc_main/…_main.lyrdb` `3da5e270…` |
| Maximal DRC | 68-71 | **passed** | 0 | 595 s (attempt 2; attempt 1 crashed with KLayout SIGSEGV at start, kept in `drc_maximal_attempt1_sigsegv/`) | `drc_maximal/…_sg13g2_maximal.lyrdb` `f54b65a5…` |
| Density | 72-73 | **passed** | 0 | 64 s | `density/…_density.lyrdb` `89149c55…` |
| Antenna | 74-75 | **passed** | 0 | 190 s | `antenna/…_antenna.lyrdb` `71533d82…` |
| Precheck (`--precheck_drc --disable_extra_rules`, with density) | 76-77 | **passed** | 0 | 399 s | `precheck/…_full.lyrdb` `92416e92…` |
| LVS, projected reference, strict ports | 78 | **passed** | Netlists match: 62 914/62 914 devices, 31 788/31 788 nets, **22/22 pins** | 258 s | [`lvs_projected/pair_counts.json`](lvs_projected/pair_counts.json); lvsdb `66e8edc3…` bulk only |
| LVS, canonical unprojected reference (r3 CDL) | 79 | **failed** (as r2) | "Netlists don't match". The same 14 IO/level-shifter sub-circuits NoMatch, top `Skipped`. Every non-Match circuit has exactly r2's status and device/net/pin/subcircuit counts. 33 Match: r2's 34 minus `sg13g2_buf_4`, whose 3 instances are all label clones | 219 s | [`lvs_canonical/pair_counts.json`](lvs_canonical/pair_counts.json); lvsdb `bedb6524…` bulk only |

The five DRC lyrdb hashes equal r2's (an empty report carries only the rule catalogue). Every
completed run exited with code 0. The GDS SHA was checked again after all runs and was unchanged
(`c88261ff…`).

Superseded first attempt (v1, `$R/signoff_v1_superseded/`, `$R/chip_v1_superseded/`):
- the swap cloned only `inv_2/4/8` dummy loads;
- projected LVS passed with **25** pins, 3 of them synthetic layout pins (`$5096.X`,
  `$5097.X`, `$5695.X`) from the 3 `buf_4` dummy loads;
- v2 (this file) adds `buf_4` to the rule;
- v1's main, precheck, density and antenna passed; its maximal run was stopped.

## Bond map

`bondmap_r3cand.csv` has the rows of `padframe/bondmap_20260925_r3.csv` with
`candidate_gds_sha256` set to `c88261ff…` and `status` set to `candidate_not_promoted`.
`verify_bondmap.py` result:
- **passed** (`all_ok: true`);
- 24 openings and 24 rows, 22 labels at the row centres;
- output: [`bondmap/verify_bondmap_r3cand.json`](bondmap/verify_bondmap_r3cand.json).

On promotion, the tracked bond map is rebound by the owner's process.

## Not run

- Chip-level co-sim of this RTL (`eco_c_mid_r2`, coordinator): **pending**. It decides promotion.
- GLS of the r3-candidate netlist: handed off (`g1_ctrl/flow/eco/HANDOFF.md`), result not recorded here.
- Full-chip PEX, transient/electrical simulation, IR drop/EM, full-chip STA with extracted parasitics.
- Canonical unprojected LVS passing: run, **failed** (PDK IO-cell reference semantics, as r1/r2).
- Block-map XOR re-run: not run. The XOR above shows no change outside the macro except 5/22.
- IHP intake/rejection test; written IHP die-area confirmation: open (as r2).
- Measurement: not run (no silicon).

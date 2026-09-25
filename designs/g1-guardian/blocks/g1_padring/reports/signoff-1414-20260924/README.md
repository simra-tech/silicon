# G1 1414 µm chip: physical sign-off rerun on the final file (2026-09-24)

The owner selected the 1414 × 1414 µm native-lineage chip as the tape-out
artifact of record. This report reruns physical checks on that exact file,
after renaming only its top cell to `g1_chip_top`. It also records which block
variant and netlist are physically present.

This is physical verification only. Full-chip PEX, IR/EM, timing sign-off and
electrical qualification of the assembled chip are **not run** here. See
"Not run" below.

## Built against

| Item | Value | How established |
|---|---|---|
| PDK | IHP-Open-PDK `84374023ee8b4b126bebbba67fcbada0a9c0ff0b` | `flow/run.sh` refuses to start unless `/foss/pdks/ihp-sg13g2/COMMIT` matches |
| KLayout | 0.30.9 | `run_drc.py` log line "Your Klayout version is: KLayout 0.30.9" |
| Container image | `sha256:ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2` | `flow/run.sh` image identity check |
| Rule decks | stock `run_drc.py`, `run_lvs.py` and decks from the PDK above, unmodified | invoked from `/foss/pdks/ihp-sg13g2/libs.tech/klayout/tech/` inside the container |
| CPUs | 64-79 (`taskset`, rootless cgroups v1) | `flow/launch_pinned.sh` |

## Files of record

| File | SHA-256 | Notes |
|---|---|---|
| `layout/g1_chip_top_1414_src.gds` | `60730627d24e1fb6b880138edc3e50fdd7c14624bb2dfbbc631e084b7415eca1` | Byte copy of `${BULK}/soft-inputpair4-parent-20260924-r3/candidate.gds`. Top `placed_core_NOT_CONNECTED_FULLCHIP`. |
| `layout/g1_chip_top_1414.gds` | `629d303abf594ec90593f1d28a8d9ad19673ea6662780ba428a6d9c5685986ba` | Top cell renamed to `g1_chip_top`. Nothing else changed. **This is the file checked below.** |
| `netlist/g1_chip_top_1414.cdl` | `af5a4dbd0b17013b11d32f31221353a22b2676ea884e3487db3f14d9c5443a36` | Canonical (unprojected) reference. It is `candidate.cdl` `984f82dd…` with the top `.SUBCKT` renamed and one header comment added. |
| `netlist/g1_chip_top_1414_projected_ref.cdl` | `e1d06919fedea1c1e2c171ab52a35cdec4dc7132470c5887561ad2a0cf27640e` | Comparison-only projected reference. It is `physical_AP_three_dummy_flat_reference.cdl` `417bf0d7…` with the top name changed to `G1_CHIP_TOP` on 3 lines and one header comment added. |

Parent lineage: the OSC R0.95 full chip `osc_r095_fullchip.gds` `18b897fe…` with
canonical CDL `126acd51…` (`${BULK}/osc-r095-physical-20260924-r1/fullchip_r095_candidate.cdl`).
`candidate.cdl` (`984f82dd…`) is the canonical CDL for `60730627`. It already
exists and was not rebuilt here. `prepare_soft_inputpair4_parent_r3.py` (`208f6c18…`)
generated it from `126acd51…` with exactly one edit, checked by an exact
inverse. The edit is in `.subckt g1_cmp`:
`MM1`/`MM2` `sg13_lv_nmos w=12u l=0.34u` → `w=24u l=0.68u`.
The layout uses four folded fingers. The CDL states total W and has no `ng`
parameter. The body of `g1_cmp` is identical, line for line, to
`${BULK}/soft-inputpair4-folded-native-20260924-r1/standalone.cdl`
(`g1_cmp_soft_inputpair4_folded_r1`). The header of `candidate.cdl` says "not LVS-qualified".
The canonical LVS below confirms this.

### Rename identity (passed)

`flow/signoff/1414/rename_top.py` renamed only the top cell and wrote the GDS
without timestamps. Two writes were byte-identical (`629d303a…`). An earlier
write that included timestamps (`1c5eaeec…`) is kept only in bulk storage and
is not used. `flow/signoff/1414/verify_rename.py` compared the source and the
renamed file ([rename_verify/verify_rename.json](rename_verify/verify_rename.json)).
Both have 306 cells, the same cell names apart from the top, the same DBU, and
the same bounding box `(0,0;1414000,1414000)`. Each cell's direct shapes and
instance lists are identical. A deep-mode XOR over all 73 layers is empty on
every layer, and the flattened text lists are identical.
`identical_geometry: true`.

## Physical checks on `g1_chip_top_1414.gds` (`629d303a…`)

Each check ran detached through `flow/launch_pinned.sh` with a 5400 s wall
bound and top cell `g1_chip_top`. Paths are inside the container. `$G` is
`/work/designs/g1-guardian/blocks/g1_padring/layout/g1_chip_top_1414.gds`,
`$D` is `/foss/pdks/ihp-sg13g2/libs.tech/klayout/tech` and `$B` is
`${BULK}/signoff-1414-20260924`.

| Check | Result | Markers | Wall | Report (bulk) / copy here |
|---|---|---|---|---|
| Main DRC (table `main`) | **passed** | 0 | 253 s | `drc_main/g1_chip_top_1414_g1_chip_top_main.lyrdb` `3da5e270…` |
| Maximal DRC (`sg13g2_maximal`) | **passed** | 0 | 559 s | `drc_maximal/g1_chip_top_1414_g1_chip_top_sg13g2_maximal.lyrdb` `f54b65a5…` |
| Density | **passed** | 0 | 31 s | `density/g1_chip_top_1414_g1_chip_top_density.lyrdb` `89149c55…` |
| Antenna | **passed** | 0 | 116 s | `antenna/g1_chip_top_1414_g1_chip_top_antenna.lyrdb` `71533d82…` |
| LVS, projected reference, strict ports | **passed** | Netlists match: 61684/61684 devices, 31173/31173 nets, 22/22 pins, 0 warnings, 0 errors | 146 s | `lvs_projected/pair_counts.json`, log; lvsdb `eb2d3b5f…` bulk only |
| LVS, canonical unprojected reference | **failed** | "Netlists don't match". 14 IO/level-shifter subcircuit pairs NoMatch, top `Skipped` | 111 s | `lvs_canonical/pair_counts.json`, log; lvsdb bulk only |

Every run exited with code 0 (`run.log.rc`). The GDS SHA was checked again
after all runs and was unchanged (`629d303a…`). Commands:

```sh
# main DRC (previous --no_density command; --disable_extra_rules keeps only table main)
python3 $D/drc/run_drc.py --path=$G --topcell=g1_chip_top --run_mode=deep --no_density --disable_extra_rules --density_thr=4 --run_dir=$B/drc_main
# maximal DRC: stock run_drc.run_check on rule_decks/sg13g2_maximal.drc with the switches run_drc.py generates for
# "--run_mode=deep --no_density" (same method as review/audits/run_core_candidate_drc.py --execute maximal)
python3 designs/g1-guardian/blocks/g1_padring/flow/signoff/1414/run_maximal.py $G g1_chip_top $B/drc_maximal 4
# density
python3 $D/drc/run_drc.py --path=$G --topcell=g1_chip_top --run_mode=deep --density_thr=2 --density_only --run_dir=$B/density
# antenna
python3 $D/drc/run_drc.py --path=$G --topcell=g1_chip_top --run_mode=deep --density_thr=2 --antenna_only --run_dir=$B/antenna --antenna
# projected-reference LVS
python3 $D/lvs/run_lvs.py --layout $G --netlist /work/designs/g1-guardian/blocks/g1_padring/netlist/g1_chip_top_1414_projected_ref.cdl --topcell g1_chip_top --run_mode deep --top_lvl_pins --spice_comments --run_dir $B/lvs_projected
# canonical LVS (extra; same options)
python3 $D/lvs/run_lvs.py --layout $G --netlist /work/designs/g1-guardian/blocks/g1_padring/netlist/g1_chip_top_1414.cdl --topcell g1_chip_top --run_mode deep --top_lvl_pins --spice_comments --run_dir $B/lvs_canonical
```

Differences from the earlier command lines:

- The input file, top cell and run directory are new.
- The `--density_thr` thread count is set to the allocated CPUs (earlier: 1
  for density/antenna, or the default). The thread count does not change the
  checks that run.
- Main and maximal were run separately. Earlier, one `--no_density` run
  covered both, and that combined run hit its 1130 s bound (rc 124) after
  main had passed. The stock CLI has no maximal-only switch, so maximal was
  run through `run_maximal.py`, which calls the PDK's own `run_check`.

The main and maximal decks passed here, on the same file, in two separate
runs.

Projected LVS scope: the reference removes exactly three source-only dummy
PMOS devices (VDD to VDD, all-VDDIO pad) that were proved in earlier
evidence. This is a comparison projection. It is **not** canonical
unprojected sign-off.

Canonical LVS failure scope: hierarchical matching paired 34 circuits as
Match. These were `g1_dac8` and the standard cells. The 14 NoMatch circuits
are the stock-named layout IO sub-cells: `sg13g2_Clamp_*`, `DCN/DCPDiode`,
`LevelDown`, `LevelUpInv` and `RCClampInverter`. They were compared against
the reference `sg13g2_*` subckt definitions. The canonical reference carries
both those and the `G1_VSS_DERIVATIVE__*` explicit-substrate variants.
Top-level comparison was skipped. This failure is recorded and has not been
investigated further in this run.

## Block-to-netlist map (what is physically in `629d303a…`)

The layout identity of each row was checked by per-layer XOR, excluding
text, of the chip cell (in its own coordinates) against the named block GDS.
Fill datatypes 22/23 were excluded. Results are in
[blockmap/block_xor.json](blockmap/block_xor.json), `bgr_xor.json`,
`trip_xor.json` and `digital_xor.json`. Netlist identity was checked by
matching normalized `.subckt` bodies of the canonical CDL against the named
files.

Paths starting `blocks/` are under `designs/g1-guardian/blocks/`. `${BULK}` is
the bulk results root. Hashes are SHA-256, first 8 hex digits.

| Block (chip cell) | Variant physically present | Layout identity (XOR empty vs.) | Netlist in canonical CDL = | Schematic / simulation source | Post-layout extraction bound to this layout |
|---|---|---|---|---|---|
| SENSE (`__rz_port_text_030_g1_sense_candidate`, r90 at 1031,331 µm) | comp45 + **RZ100**: `g1_ota_main_candidate` has `RRZ … rppd w=1u l=100u` | `blocks/g1_sense/reports/rz100-partial-field-evidence-20260923-r1/sense-comp45-rz100-native-build-20260923-r1/g1_sense_physical.gds` `450a4906` | `…/sense-comp45-rz100-native-reference-20260923-r1/g1_sense_physical.cdl` `696b43fd`. `g1_sense` body identical apart from the subckt name; `g1_ota` and `g1_ota_main_candidate` exact | `${BULK}/sense-comp45-rz100-actual-source-20260923-r1/candidate.spice` `bb933fda`. Repo decoded copy `…/sense-comp45-rz100-actual-source-20260923-r1/candidate.spice` `aeee4d41` | **Partial-field only.** Partial-C `sense_partial_c.spice` `ffb14762` (bulk; repo decoded copy `ffb5bcd0`), from the view GDS `01f950f6` derived from `450a4906` (`sense-comp45-rz100-field-extract-20260923-r1/summary.json.gz`: `native_GDS_sha256`=450a4906). 844 C added, 134 VSUBS pairs omitted. Recorded field acceptance: FAILED/unresolved |
| TRIP (`__rz_port_text_033_retained_g1_trip`) | Hard comparator **regenpair4** (`XCH` MM3/MM4 w=6u l=0.26u) + soft comparator **NF4** input pair (MM1/MM2 w=24u l=0.68u, 4 folded fingers) + moved q-feed | Hard `__rz_port_text_033_g1_cmp_regenpair4` = `${BULK}/trip-regenpair4-native-20260923-r1/hard_cmp.gds` `58b5ea23`. Soft `__rz_port_text_034_g1_cmp` = `${BULK}/soft-inputpair4-folded-native-20260924-r1/standalone.gds` `576427ba`. Remainder = regenpair4 trip `1c953318`/`retained_g1_trip`, except the soft cell and q-feed (layers 10/29/30) | `g1_trip`, `g1_cond`, `g1_dac8`, `g1_inv`, `g1_tlvlup`, `g1_thv_inv` = `blocks/g1_trip/layout/g1_trip_lvs.cdl` `60a9ad6e`. `g1_cmp_regenpair4` = `${BULK}/trip-regenpair4-native-20260923-r1/hard_cmp.cdl` `c0e1718a`. `g1_cmp` body = `${BULK}/soft-inputpair4-folded-native-20260924-r1/standalone.cdl` `04f688ed` | The same CDLs. NF4 simulations: `blocks/g1_trip/sim/qualification/joint586-softinputpair4-nf4-*` | **None.** No CPEX of either new comparator. `blocks/g1_trip/reports/pex/g1_trip_k25d_pex_netlist.spice` is the older full-trip extraction and is not bound |
| OSC (`__rz_port_text_032_retained_g1_osc`) | **R0.95**: `RRA`/`RRB` rppd l=111.15u (was 117u) | `${BULK}/osc-r095-physical-20260924-r1/osc_r095.gds` `411d52f7` and `osc_r095_filled.gds` `960a9e9a` (non-fill layers) | `g1_osc` = `126acd51` edit of the earlier `g1_osc` (`blocks/g1_osc/reports/r095_fullchip_preparation_20260924/source.json`). Sub-cells = `blocks/g1_osc/layout/g1_osc_lvs.cdl` `8a8fa94a`. Flat standalone LVS reference `${BULK}/osc-r095-physical-20260924-r1/osc_r095.cdl` `b5bdd554` | `blocks/g1_osc/sim/qualification/runs/osc_r095_candidate_shard0_20260921_01/osc.spice` `f08bf051` | Isolated macro CPEX `${BULK}/osc-r095-physical-20260924-r1/pex_cc_r1/osc_r095_pex.spice` `8efd7a09`, from `osc_r095_pexin.gds` `2de63498`, derived from the **filled** `960a9e9a` (MIM/floating fill stripped, 11 ideal MIM re-inserted). Not assembled-parent PEX |
| BGR (`__rz_port_text_031_g1_bgr_candidate` at 331,732 µm, plus top overlay `bgr_supply_additive_context_candidate`) | `bgr_loop24_qref4_r253p465_hv06`, **supply follow-up** geometry (native signal-bypass cell plus additive M5/Via4 supply overlay) | Cell + overlay shifted to local coordinates = `blocks/g1_bgr/layout/coordinated_supply_followup_20260923/evidence/supply-20260923-r1/candidate/bank.gds` `e3ecfc62` (all 33 layers empty). Control: pre-supply collector `1f32630e` differs on 66/0 and 67/0 | `g1_bgr` = `…/supply-20260923-r1/candidate/bank.cdl` `7f8e6e8c` (the same body appears in the other coordinated BGR bank.cdl files) | `blocks/g1_bgr/sim/qualification/candidates/bgr_loop24_qref4_r253p465_hv06/bgr_loop24_qref4_r253p465_hv06.spice` `586ffb58` | **No capacitance PEX.** DC metal-R network only: `…/supply-20260923-r1/kpex/conditional_metal.spice` `2015e6c9`, via metallization `8788952d` from `e3ecfc62` |
| T2F (`__rz_port_text_037_retained_g1_t2f`) | baseline (not `rev1`) | `blocks/g1_t2f/layout/g1_t2f.gds` `c2ae89a9` | `blocks/g1_t2f/layout/g1_t2f_lvs.cdl` `ce4d82b7` | `blocks/g1_t2f/xschem/g1_t2f.spice` `8011b761` | `blocks/g1_t2f/reports/pex/cc/g1_t2f_k25d_pex_netlist.spice` `0f9ef98a` (sim form `sim/postlayout/g1_t2f_pex.spice` `441edabc`). Bound by path, timestamp and README text only; no hash record |
| GATE (`retained_g1_gate`) | baseline | `blocks/g1_gate/layout/g1_gate.gds` `ddf2c44a` (and `g1_gate_filled.gds` `ba9d1311`, non-fill layers) | `blocks/g1_gate/layout/g1_gate.cdl` `27548c03` | `blocks/g1_gate/sim/netlist/g1_gate.spice` `846a55e0` | **Not bound.** `reports/pex/cc/g1_gate_k25d_pex_netlist.spice` `e136c884` was extracted from an earlier build file (`build/g1_gate_lay/g1_gate.gds`); no hash links it to `ddf2c44a` |
| Digital (`__rz_port_text_000_retained_g1_digital`) | LibreLane post-route, final rename (differs from `blocks/g1_ctrl/layout/g1_digital.gds`) | `${BULK}/digital-postroute-20260923-r1/flow/05-klayout-streamout/g1_digital.gds` `1a662082` | `g1_digital` = `${BULK}/digital-cleanflat-lvs-20260923-r1/g1_digital_source.cdl` `3cb199c1`, from `digital-final-pnlrename-20260923-r1/g1_digital.nl.v` `4fd0b616` | same Verilog netlist | `digital-postroute-20260923-r1/flow/01-openroad-rcx/nom/g1_digital.nom.spef` `e6c89575` (same ODB `05568ddf` as the streamout) |
| Level shifters ×3 (`retained_g1_ls_up`) | baseline | `blocks/g1_ctrl/ls/layout/g1_ls_up.gds` `85de277c` | `blocks/g1_ctrl/ls/sim/netlist/g1_ls_up.cdl` `3465d0a6` | same, plus `g1_ls_up.spice` `5567c807` | `blocks/g1_ctrl/ls/reports/flat-pex-20260921T150429Z_42162722/ngspice_pex.spice` `087bdf16` (`capacitance.json` binds GDS `85de277c`) |
| DOSE / DUT macros | baseline | `blocks/g1_dose/layout/g1_dose_macro.gds` `5fc05ceb`; `blocks/g1_dut/layout/g1_dut_macro.gds` `c577c9e3` | `blocks/g1_dose/schematic/g1_dose_macro.cdl` `7d3e134d`; `blocks/g1_dut/schematic/g1_dut_macro.cdl` `48da3016` | same | not applicable (single-device test structures) |
| IO ring | `sg13g2_io` cells with design-local explicit-VSS derivatives and `g1_io_*_polyres_r1` resistor sub-cells | not XOR-checked in this run | `G1_VSS_DERIVATIVE__*` section of the canonical CDL | PDK `sg13g2_io.cdl` | not run |

Earlier revisions of the digital and OSC GDS in the repository (`blocks/g1_ctrl/layout/g1_digital.gds`
`065b4504`, `blocks/g1_padring/flow/macro_gds_assembly/g1_digital.gds` `553b3fe1`,
`blocks/g1_osc/layout/g1_osc.gds` `3f188401`) are **not** what is on the chip;
their XOR is non-empty.

## PolyRes 128/0 in the design-local IO cells

**Finding.** In SG13G2, PolyRes 128/0 is a drawn polysilicon layer: it
defines the poly body of a resistor. It is not a recognition-only marker.
Nothing in the PDK labels it a non-mask layer. In the design-local IO copies,
the added 128/0 lies entirely on top of the GatPoly 5/0 that was already
drawn. The union GatPoly ∪ PolyRes, which is the poly the PDK decks work
with, is therefore exactly the stock poly. So either reading of the layer
gives the same patterned poly.

Evidence, from PDK `84374023` under `ihp-sg13g2/`:

1. `libs.doc/doc/SG13G2_os_layout_rules.pdf`, §2 Layer Table (Rev 0.4) lists
   `PolyRes drawing 128 0 "used to mark net resistors"` and
   `PolyRes pin 128 2 "Defines polysilicon gates and interconnect"`.
   That table does not give PolyRes a separate `mask` (datatype 20) purpose.
   Only Activ, Metal1-5 and TopMetal1-2 have one.
2. The same PDF, §3.1, lists the layers "not considered for mask generation":
   DigiBnd, DigiSub, dfpad, EdgeSeal, HeatRes, HeatTrans, IND, NoDRC,
   NoMetFiller, NoRCX, RadHard, Recog, RES, Scribe, SRAM and TEXT.
   **PolyRes is not in that list.**
3. The PDK resistor PCells draw the resistor **body** on PolyRes and the
   contact heads on GatPoly: `libs.tech/klayout/python/sg13g2_pycell_lib/ihp/rppd_code.py:112-113`
   (`contpolylayer = Layer('GatPoly')`, `bodypolylayer = Layer('PolyRes')`),
   and the same in `rhigh_code.py:119-120` and `rsil_code.py:109-110`. A
   PDK rppd/rhigh/rsil resistor has poly in its body only through PolyRes.
   If PolyRes did not reach the poly mask, those resistors would have no body.
4. `libs.tech/klayout/tech/drc/rule_decks/sg13g2_maximal.drc:1636`
   builds `GatPoly_res = GatPoly.ext_or(PolyRes)`. It uses that union as the
   poly for all resistor derivations (Rppd, Rhigh, Rsil, lines 1730-1901) and
   for the SalBlock enclosure rules (2241, 2246).
   `drc/ihp-sg13g2.drc:321` and `lvs/rule_decks/general_derivations.lvs:55`
   also use `polyres_drw` as the resistor marker (`res_mk`).
   `lvs/rule_decks/res_extraction.lvs:35-45` uses it as the resistor
   measure/device marker. The MOS, BJT, diode, ESD, cap and inductor
   derivations exclude it.
5. `libs.tech/klayout/tech/sg13g2.lyp` defines `PolyRes.drawing` = `128/0`.
   `libs.tech/klayout/tech/sg13g2.map` (the LEF/DEF stream map) has no
   PolyRes entry; it covers routing layers only.
   `SG13G2_os_process_spec.pdf` contains no mask list and does not mention
   PolyRes.
6. No document in this PDK spells out the foundry's GDS-to-mask Boolean. The
   statement that PolyRes merges into the GatPoly mask is inferred from
   items 2-4, not quoted. That caveat stands.

Measured on this chip
([polyres/io_layers.txt](polyres/io_layers.txt), script `flow/signoff/1414/polyres_io_layers.py`):

| Cell | GatPoly 5/0 area | PolyRes 128/0 area | GatPoly ∩ PolyRes |
|---|---|---|---|
| stock `sg13g2_RCClampResistor` (PDK `sg13g2_io.gds`) | 542.36 µm² | 0 | 0 |
| `g1_io_rc_polyres_r1` and `_alias1` (in IOPadVdd/IOPadIOVdd) | 542.36 µm² | 520.00 µm² | 520.00 µm² |
| stock `sg13g2_SecondaryProtection` | 2.86 µm² | 0 | 0 |
| `g1_io_secondary_polyres_r1` and `_alias1` (in IOPadAnalog/IOPadIn LevelDown) | 2.86 µm² | 2.00 µm² | 2.00 µm² |

GatPoly is unchanged, and PolyRes is fully contained in GatPoly. So
GatPoly ∪ PolyRes equals the stock GatPoly and the poly mask is unchanged.
According to
`review/audits/fullchip_reference_closure/physical_lvs/marker_remedy/RESULTS_20260923.md`,
each added body is the intersection of the unchanged GatPoly, SalBlock,
EXTBlock and pSD layers. The addition lets the stock LVS recognise the IO
resistors as `rppd` devices. That record declares this a design-layer change,
"not an assertion that 128/0 is fabrication-mask-inert". Main, maximal and antenna
DRC pass on the full chip with these cells in place.

## Not run

- Full-chip (assembled) PEX, full-chip transient/electrical simulation on
  this GDS, IR drop/EM, and full-chip STA with extracted parasitics.
- Canonical unprojected LVS passing. It was run and **failed**; see above.
- Seal-ring and IO-ring foundry precheck beyond the stock DRC decks, and
  bond-map revalidation against this renamed file. The rename does not
  change geometry.
- Measurement: not run (no silicon).

## Follow-ups (2026-09-24)

**Digital identity chain.** On-chip digital cell = `${BULK}/digital-postroute-20260923-r1/flow/05-klayout-streamout/g1_digital.gds`
`1a662082` (XOR empty). That GDS was streamed from `digital-final-dbrename-20260923-r1/g1_digital.def`/ODB `05568ddf`,
which is LibreLane g1_ctrl `run7` (synthesis to detailed placement, `blocks/g1_ctrl/flow/runs/run7/34-openroad-detailedplacement`)
with the rest redone outside run7: CTS `digital-cts-split-20260923-r1` (cluster 8, split root), then `digital-postcts-20260923-r2`
(resize, global/detailed route, fill), then renaming. Final nl `6181b988`, pnl `4fd0b616`. The canonical-CDL `g1_digital`
subckt is `digital-cleanflat-lvs-20260923-r1/g1_digital_source.cdl` `3cb199c1`. It was made from pnl `4fd0b616` by
`verilog_to_subckt` in `flow/lvs/assemble_chip_cdl.py` (`54b0feed`), which uses the same net merging as `pnl2cdl.py` but is not `pnl2cdl.py` itself.
Function: `digital-equivalence-final-20260923-r2` proved final nl `6181b988` ≡ run7 pre-CTS nl `2b342c24` (4042/4042).
This run proved run7 final nl `fce14375` (the netlist of `sim/tb_g1_digital_gls_run7.log`, 13 tests / 193 checks passed)
≡ `2b342c24` with the same script (4042/4042, `digital_equiv/control.tail.txt`). By transitivity, the chip digital
is Boolean-equivalent to the run7 GLS netlist. The direct fce14375 vs 6181b988 comparison is **unproven** by this
name-matching method (19 unproven with `equiv_struct`, 778 without). This is a limit of the method, not a demonstrated difference.
GLS was **not run** on the chip netlist itself, and timing and SDF are not covered.
RTL: run7 read `blocks/g1_ctrl/rtl/{g1_sync2,g1_serial,g1_trip_timer,g1_regfile,g1_digital_top,g1_digital}.v` and
`blocks/g1_seu/rtl/{g1_tmr_reg,g1_seu_chain,g1_seu}.v`. All of these were last modified before run7 (latest 2026-09-19 01:16, run7 at 08:03).
No hashes were recorded at synthesis time. The current RTL has register map 1.1 (`VERSION=8'h11`).

**Heat/TEXT labels.** 51/0 (HeatTrans) and 52/0 (HeatRes) texts are device-name labels (`nmos`, `pmos`, `nmosHV`,
`npn13G2`, `rppd`, `rhigh`). Each sits at the centre of a device's thermal-marker rectangle. The PDK PCells place them
(`sg13g2_pycell_lib/ihp/thermal.py` `ihpAddThermalLayer`, `dbCreateLabel`). They are found in the PCell sub-cells of every analog
block and in stock `sg13g2_io` `LevelDown`. The port-text normalisation did not create them. Layout rules §3.1 lists HeatRes and
HeatTrans (and TEXT 63/0) among the layers "not considered for mask generation". Full list: `text_layers_51_52_63.txt`.
The top cell also carries the seal-ring PCell registration text on 63/0, "Device registration size: x=1050.0 um" (stale:
it comes from the 1000 µm PCell that `sealring_g1.py` stretches to 1414 µm, as documented in `review/audits/prepare_sealring_1414.py`),
plus "PDK version: Unknown".

**BGR variant.** Schematic `blocks/g1_bgr/sim/qualification/candidates/bgr_loop24_qref4_r253p465_hv06/bgr_loop24_qref4_r253p465_hv06.spice`
`586ffb58` (manifest: parent `53513ab4` + XM31/XM33 L 0.5→0.6 µm). It has 336 MOS (235 hv_pmos, 101 hv_nmos), 301 npn13G2 (Nx=1),
384 rppd (240×1/50 µm, 96×1/48, 24×1/51.5, 24×1/53.465), 15 rhigh 0.5/49 µm and 329 C. The Sep-19 `xschem/g1_bgr.spice` has 13 npn13G2,
20 MOS, 4 rppd (500/192/51.5/315 µm) and 1 rhigh 0.5/735 µm. The LVS CDL is `bank.cdl` `7f8e6e8c`. Block simulations of this
variant are the `bgr586-*` audits and `BGR586_*.md` under `blocks/g1_bgr/sim/qualification/` (screen300, pvt81, required AC/PVT,
startup, stress, capload9, one-draw, matched-load). CPEX inputs exist but CPEX was **not run**: standalone layout
`blocks/g1_bgr/layout/coordinated_supply_followup_20260923/evidence/supply-20260923-r1/candidate/bank.gds` `e3ecfc62`
(top `g1_bgr`, equal to the chip's BGR) with `bank.cdl` `7f8e6e8c`.

# Top-level interconnect parasitics of the 1414 µm chip (2026-09-25)

This is the routing *between* the block macros of `g1_chip_top_1414.gds`
(`629d303a…`), which none of the block extractions cover. The result is
`top_interconnect_20260925.spice`: lumped C (ground and net-to-net) for the
57 routed top-level signal nets, plus a pi-RC variant with the series wire R.
It can be added next to the block PEX netlists in the chip deck. All values
are **extracted or estimated from layout**. None is measured, and none has been
simulated in the chip deck (**not run**, see "Not run").

## Built against

| Item | Value | How established |
|---|---|---|
| Layout | `blocks/g1_padring/layout/g1_chip_top_1414.gds` `629d303abf59…` | `strip_fill.py` report, `input_sha256` |
| Netlist used for net identity | `blocks/g1_padring/netlist/g1_chip_top_1414.cdl` `af5a4dbd…` (top `.SUBCKT g1_chip_top`) | `prepare.json` `cdl_sha256` |
| PDK | IHP-Open-PDK `84374023ee8b4b126bebbba67fcbada0a9c0ff0b` | `flow/run.sh` commit check |
| Container | `tapeoutbench-eda:latest` `sha256:ddeb6957…` | `flow/run.sh` image check |
| KLayout | 0.30.9 | `klayout -v` |
| kpex | 0.3.12, 2.5D engine, `--mode CC` | `kpex --version` |
| kpex technology | `klayout_pex_protobuf/ihp-sg13g2_tech.pb.json` `6ece2ac7…` (as installed in the image) | `sha256sum` |
| ngspice | 46 (syntax check of the subcircuits only) | `ngspice -v` |
| CPUs | 34-35 (`taskset`) | `flow/launch_pinned.sh` |

Revision r2 (`g1_chip_top_1414_r2.gds` `9049e87b…`, now the file of record)
changes only metadata: two text labels and three cell names. Its sign-off
report states that the geometry is identical on every layer
(`../../../g1_padring/reports/signoff-1414r2-20260925/README.md`). The
numbers here therefore apply to r2 as well. r2 was **not re-extracted**.

## Method

1. **Fill removed.** `flow/pex/strip_fill.py` wrote a copy of the GDS with every
   datatype-22 shape deleted from every cell (`<layer>.filler` in the PDK's `sg13g2.lyp`;
   the nofill markers on datatype 23 were kept). Output: `g1_chip_top_1414_nofill.gds` `6406ba36…`
   (bulk). Removed flat: 279 928 shapes on Activ, GatPoly, Metal1-5 and TopMetal1-2. See
   [fullchip_strip_fill_20260925.json](fullchip_strip_fill_20260925.json).
2. **Top-interconnect view.** `flow/pex/prepare_top_interconnect.py` flattens into one
   cell the top cell's own non-fill shapes and the cells that contain only routing:
   `new_signal_routes` with its via cells, `bondpad_outward_5um_retained_metal`,
   `bgr_supply_additive_context_candidate` and the 24 bondpads. **Every other child instance
   is replaced by its own pin shapes (`<layer>/2`, moved to `/0`) and nothing else.** That
   covers the nine block macros (digital, SENSE, BGR, OSC, TRIP, T2F, GATE, DOSE, DUT),
   the three level shifters, all IO pad, corner and filler cells, and the top-level
   standard cells (decap, fill, antenna, tiehi). Output: `g1_top_interconnect_view.gds`
   `78eeec9c…` (bulk).
3. **Net identity, checked against the CDL.** A metal/via connectivity pass puts
   each of the 15 417 pin shapes on a connected cluster. The pin's label and the
   instance's port order in the canonical CDL then give the CDL net. IO pads are
   identified by the nearest top-level pad label, and level shifters by the net
   on their `in` pin. **Shorts: 0.** Every CDL signal net is on one routed cluster,
   except for these cases. (a) IO-cell pin stacks. The same pad pin is drawn on
   M2 to TM2, and the cell's own metal joins those layers; that metal was
   removed, so each layer's pin is a separate fragment. (b) The `vref` pin of
   T2F. No top-level shape touches that pin shape. The connection is
   presumably made on T2F metal that is not a pin shape; that was not
   examined. The chip's projected-reference LVS (passed, sign-off report)
   covers that connection; this view does not. One label per cluster carries the CDL name. Clusters with no
   CDL identity are left unnamed: standard-cell and IO-filler supply rails, and
   pin shapes of cells outside the top subckt's port list.
4. **Capacitance: kpex 2.5D CC.** The stock kpex LVS deck returns an empty layout
   netlist for this device-free view: its LVSDB has no circuit, and kpex stops with
   "No extracted layers found". So `flow/pex/make_view_lvsdb.py` builds the LVSDB
   with the KLayout API. It uses the kpex ihp-sg13g2 LVS layer names (`metal1_con`…
   `topmetal2_con`, `via1_drw`…`topvia2_drw`), so kpex maps the layers to the same
   GDS pairs as in a normal run. kpex then runs through `flow/pex/kpex_named_top.py`.
   This is unchanged kpex with one runtime patch: the top cell is looked up by
   name when kpex sizes the substrate halo. The patch is needed for the full chip
   (see the feasibility note). Result: 6 174 capacitors, 7 min 45 s wall on one
   CPU. CSV `53a20e34…`.
5. **Resistance: geometry.** `flow/pex/top_route_rc.py` takes each unmerged route
   shape and assigns it to its view net. For each shape, R = R<sub>s</sub>·L/W,
   with L and W taken from the rectangle that has the same area and perimeter.
   Vias are grouped into parallel arrays (cuts within 0.4 µm), and each array
   gives R<sub>via</sub>/n. The per-net sum puts every segment in series, so it
   is an **upper bound** of any pin-to-pin path. The same script also gives a
   field-only area/perimeter C as a cross-check of the kpex numbers.
6. **Lumping.** `flow/pex/make_top_interconnect_spice.py` builds the lumps as
   follows. For each routed net, the C to substrate, to supplies, to unnamed
   rails, to pin-only fragments and to bondpads becomes `Cg_<net>` to `sub`.
   The C between two routed nets becomes `Cc_<a>__<b>`, kept when it is at least
   0.01 fF. Couplings between fragments of the same net are dropped.

### Parasitic tables used

The kpex ihp-sg13g2 technology file is the same source kpex uses for the block
extractions. Units: aF/µm² for area, aF/µm for perimeter and sidewall, and
Ω/□ or Ω per cut for resistance.

| Layer | area to substrate | perimeter to substrate | sidewall coefficient (offset µm) | sheet R (kpex) | sheet R (PDK tech LEF) |
|---|---|---|---|---|---|
| Metal1 | 35.015 | 39.585 | 28.735 (−0.057) | 0.110 | 0.135 |
| Metal2 | 18.180 | 34.798 | 40.981 (−0.033) | 0.088 | 0.103 |
| Metal3 | 11.994 | 31.352 | 37.679 (−0.045) | 0.088 | 0.103 |
| Metal4 | 8.948 | 29.083 | 49.526 (0.004) | 0.088 | 0.103 |
| Metal5 | 7.136 | 27.527 | 53.129 (0.021) | 0.088 | 0.103 |
| TopMetal1 | 5.649 | 37.383 | 162.172 (0.343) | 0.018 | 0.021 |
| TopMetal2 | 3.233 | 31.175 | 227.323 (1.893) | 0.011 | 0.0145 |

Vias (kpex / PDK LEF, Ω per cut): Via1-Via4 9 / 20, TopVia1 2.2 / 4.0,
TopVia2 1.1 / 2.2. The inter-layer overlap and side-overlap tables are in the
same file (`process_parasitics.capacitance.overlaps`, `sideoverlaps`). The LEF is
`libs.ref/sg13g2_stdcell/lef/sg13g2_tech.lef` `054f5b7b…`. R uses the kpex (typical)
values. With the LEF values, R rises by about 17 % on the wires and by 2.2× on
the vias.

## Per-net result

"C to ground" is everything except the other routed signal nets. The sum of the
two C columns is the total load of the net's top-level routing. The
area/perimeter column is the field-only check: no neighbours, no shielding.
kpex's ground C is lower than that check because neighbours shield the wire,
and its total is higher because of the sidewall coupling. R is the series upper
bound.

| CDL net | port | route length (µm) | R (Ω) | C to ground (fF) | C to other routed nets (fF) | total (fF) | area/perimeter check (fF) | largest couplings (fF) |
|---|---|---|---|---|---|---|---|---|
| **Analog** | | | | | | | | |
| `i_core_isense` | `isense` | 258 | 140 | 6.4 | 58.1 | **64.5** | 16.0 | vref_buf 27.9; en_i 13.3 |
| `i_core_vref` | `vref` | 771 | 447 | 35.6 | 135.2 | **170.8** | 48.4 | pbias 38.8; osc_clk 38.3 |
| `i_core_vref_buf` | `vref_buf` | 251 | 137 | 10.3 | 34.5 | **44.8** | 14.9 | isense 27.9; dac_soft_4_ 1.9 |
| `i_core_iptat` | `iptat` | 258 | 158 | 13.4 | 31.0 | **44.4** | 16.2 | dac_hard_3_ 16.6; isense 11.0 |
| `i_core_pbias` | `pbias` | 448 | 233 | 9.9 | 129.5 | **139.4** | 28.6 | pcasc 72.5; vref 38.8 |
| `i_core_pcasc` | `pcasc` | 446 | 232 | 20.6 | 75.0 | **95.7** | 28.5 | pbias 72.5; osc_trim_0_ 0.5 |
| `i_core_bgr_r4_33` | `bgr_r4_33` | 443 | 249 | 29.1 | 40.4 | **69.4** | 27.0 | HBT_E 22.0; clr_d 7.5 |
| `SENSE_P` | `sense_p` | 288 | 172 | 30.9 | 0.5 | **31.3** | 17.9 | SENSE_N 0.3; net 0.2 |
| `SENSE_N` | `sense_n` | 180 | 106 | 20.0 | 0.3 | **20.3** | 10.8 | SENSE_P 0.3; net 0.0 |
| **Comparator / clock / trip** | | | | | | | | |
| `i_core_cmp_soft` | `cmp_soft` | 1005 | 541 | 39.0 | 230.8 | **269.7** | 68.7 | dac_hard_1_ 84.0; dac_hard_0_ 83.7 |
| `i_core_cmp_hard` | `cmp_hard` | 694 | 422 | 24.3 | 156.4 | **180.7** | 43.2 | tripped 47.3; dac_hard_3_ 47.1 |
| `i_core_cmp_clk` | `cmp_clk` | 682 | 283 | 34.3 | 88.2 | **122.5** | 45.3 | cmp_hard 41.0; dac_hard_7_ 21.0 |
| `i_core_osc_clk` | `osc_clk` | 825 | 417 | 21.9 | 123.1 | **145.0** | 50.8 | vref 38.3; osc_trim_3_ 27.9 |
| `i_core_osc_en` | `osc_en` | 476 | 246 | 19.3 | 77.6 | **96.9** | 29.1 | osc_trim_3_ 50.7; osc_clk 15.0 |
| `i_core_trip_d` | `trip_d` | 89 | 57 | 2.0 | 24.2 | **26.2** | 5.8 | clr_d 9.3; osc_clk 7.4 |
| `i_core_clr_d` | `clr_d` | 87 | 56 | 1.6 | 23.0 | **24.7** | 5.6 | trip_d 9.3; bgr_r4_33 7.5 |
| `i_core_fast_en` | `fast_en` | 56 | 61 | 2.5 | 9.5 | **12.0** | 3.7 | bgr_r4_12 2.6; osc_clk 2.6 |
| `i_core_tripped` | `tripped` | 644 | 364 | 28.0 | 115.3 | **143.2** | 42.9 | t2f_mode_33 51.4; cmp_hard 47.3 |
| `gate_o` | `gate_o` | 390 | 216 | 20.8 | 59.2 | **80.0** | 25.3 | dac_hard_2_ 46.6; cmp_clk 3.4 |
| `fault_n_o` | `fault_n_o` | 515 | 290 | 36.5 | 24.9 | **61.4** | 32.7 | cmp_hard 8.8; en_i 6.4 |
| **DAC codes** | | | | | | | | |
| `i_core_dac_soft_0_` | `dac_soft_0_` | 187 | 109 | 3.0 | 65.7 | **68.7** | 12.5 | dac_hard_1_ 33.2; dac_hard_2_ 29.9 |
| `i_core_dac_soft_1_` | `dac_soft_1_` | 193 | 130 | 2.9 | 58.7 | **61.6** | 12.8 | dac_soft_7_ 25.8; dac_soft_5_ 24.2 |
| `i_core_dac_soft_2_` | `dac_soft_2_` | 196 | 131 | 4.7 | 44.0 | **48.7** | 11.4 | dac_hard_4_ 32.8; dac_soft_3_ 3.2 |
| `i_core_dac_soft_3_` | `dac_soft_3_` | 190 | 129 | 1.4 | 77.9 | **79.3** | 11.1 | dac_hard_5_ 34.4; dac_hard_4_ 34.0 |
| `i_core_dac_soft_4_` | `dac_soft_4_` | 173 | 103 | 4.6 | 39.8 | **44.4** | 11.4 | dac_hard_2_ 33.5; vref_buf 1.9 |
| `i_core_dac_soft_5_` | `dac_soft_5_` | 176 | 105 | 5.0 | 43.5 | **48.5** | 11.5 | dac_soft_1_ 24.2; osc_trim_3_ 6.5 |
| `i_core_dac_soft_6_` | `dac_soft_6_` | 195 | 63 | 10.1 | 11.9 | **22.0** | 15.0 | sdo_o 8.4; dac_soft_7_ 1.2 |
| `i_core_dac_soft_7_` | `dac_soft_7_` | 179 | 106 | 2.2 | 62.0 | **64.3** | 11.8 | dac_soft_1_ 25.8; dac_hard_6_ 17.2 |
| `i_core_dac_hard_0_` | `dac_hard_0_` | 419 | 211 | 9.2 | 135.4 | **144.6** | 27.6 | cmp_soft 83.7; en_i 45.8 |
| `i_core_dac_hard_1_` | `dac_hard_1_` | 421 | 212 | 4.2 | 137.4 | **141.6** | 27.7 | cmp_soft 84.0; dac_soft_0_ 33.2 |
| `i_core_dac_hard_2_` | `dac_hard_2_` | 424 | 250 | 5.2 | 131.1 | **136.3** | 28.0 | gate_o 46.6; dac_soft_4_ 33.5 |
| `i_core_dac_hard_3_` | `dac_hard_3_` | 411 | 235 | 16.5 | 78.3 | **94.8** | 26.1 | cmp_hard 47.1; iptat 16.6 |
| `i_core_dac_hard_4_` | `dac_hard_4_` | 405 | 223 | 4.7 | 103.3 | **108.0** | 23.2 | dac_soft_3_ 34.0; dac_soft_2_ 32.8 |
| `i_core_dac_hard_5_` | `dac_hard_5_` | 408 | 224 | 7.4 | 79.6 | **87.0** | 23.4 | dac_soft_3_ 34.4; dac_hard_4_ 21.4 |
| `i_core_dac_hard_6_` | `dac_hard_6_` | 406 | 223 | 13.3 | 43.0 | **56.3** | 24.2 | dac_soft_7_ 17.2; dac_hard_4_ 8.2 |
| `i_core_dac_hard_7_` | `dac_hard_7_` | 440 | 213 | 18.3 | 39.0 | **57.3** | 28.1 | cmp_clk 21.0; dac_hard_6_ 5.0 |
| **Oscillator trim** | | | | | | | | |
| `i_core_osc_trim_0_` | `osc_trim_0_` | 418 | 220 | 13.2 | 79.2 | **92.4** | 25.2 | osc_trim_1_ 46.5; vref 27.4 |
| `i_core_osc_trim_1_` | `osc_trim_1_` | 473 | 244 | 4.9 | 111.5 | **116.4** | 28.8 | osc_trim_0_ 46.5; osc_clk 15.0 |
| `i_core_osc_trim_2_` | `osc_trim_2_` | 425 | 223 | 20.9 | 21.5 | **42.4** | 25.6 | pbias 13.4; osc_clk 2.8 |
| `i_core_osc_trim_3_` | `osc_trim_3_` | 482 | 248 | 5.6 | 126.5 | **132.1** | 29.3 | osc_en 50.7; osc_clk 27.9 |
| **Pads / serial / T2F / misc** | | | | | | | | |
| `en_i` | `en_i` | 801 | 478 | 43.1 | 78.6 | **121.7** | 50.0 | dac_hard_0_ 45.8; isense 13.3 |
| `i_core_sclk_i` | `sclk_i` | 834 | 412 | 54.3 | 103.6 | **157.9** | 57.5 | cmp_soft 52.7; sdi_i 49.1 |
| `i_core_sdi_i` | `sdi_i` | 1406 | 709 | 105.1 | 60.3 | **165.4** | 96.6 | sclk_i 49.1; cmp_soft 5.1 |
| `i_core_sdo_o` | `sdo_o` | 549 | 72 | 54.8 | 20.8 | **75.6** | 44.5 | dac_soft_6_ 8.4; HBT_E 5.9 |
| `i_core_t2f_en_12` | `t2f_en_12` | 112 | 58 | 4.7 | 24.4 | **29.1** | 8.2 | t2f_mode_12 16.9; tripped 6.4 |
| `i_core_t2f_en_33` | `t2f_en_33` | 869 | 454 | 35.5 | 146.9 | **182.4** | 59.1 | t2f_mode_33 81.2; net 55.3 |
| `i_core_t2f_mode_12` | `t2f_mode_12` | 151 | 94 | 6.2 | 25.9 | **32.1** | 10.9 | t2f_en_12 16.9; t2f_en_33 6.3 |
| `i_core_t2f_mode_33` | `t2f_mode_33` | 760 | 388 | 29.7 | 137.6 | **167.3** | 50.2 | t2f_en_33 81.2; tripped 51.4 |
| `i_core_temp_out_o` | `temp_out_o` | 246 | 126 | 20.4 | 0.5 | **20.9** | 16.5 | t2f_en_33 0.5; vref 0.0 |
| `i_core_bgr_r4_12` | `bgr_r4_12` | 125 | 82 | 5.4 | 16.3 | **21.7** | 7.8 | osc_trim_3_ 5.5; osc_clk 3.1 |
| `net` | `net` | 656 | 325 | 41.5 | 70.5 | **112.0** | 45.3 | t2f_en_33 55.3; osc_trim_3_ 6.5 |
| **Test-structure pad nets** | | | | | | | | |
| `D_ELT` | `d_elt` | 774 | 376 | 54.7 | 113.8 | **168.6** | 45.5 | HBT_B 83.0; D_STD 17.9 |
| `D_STD` | `d_std` | 652 | 323 | 24.5 | 147.1 | **171.7** | 41.4 | HBT_C 110.8; G_SHARED 17.9 |
| `G_SHARED` | `g_shared` | 542 | 274 | 34.2 | 35.9 | **70.0** | 34.9 | D_STD 17.9; HBT_B 11.1 |
| `HBT_B` | `hbt_b` | 943 | 451 | 68.4 | 102.1 | **170.5** | 55.3 | D_ELT 83.0; G_SHARED 11.1 |
| `HBT_C` | `hbt_c` | 1053 | 499 | 49.9 | 136.6 | **186.5** | 65.5 | D_STD 110.8; D_ELT 10.1 |
| `HBT_E` | `hbt_e` | 752 | 203 | 42.5 | 43.4 | **85.8** | 50.3 | bgr_r4_33 22.0; sdo_o 5.9 |

Pin-only fragments are not in the lumps. They are IO-cell pin stacks (72-82 fF per
pad, the metal inside the pad cell) and single pin shapes (up to 6 fF).
**Bondpads are not in the lumps either.** Each 70 × 70 µm TopMetal1/TopMetal2
bondpad stack is 53.4 fF by kpex and 132.6 fF by the field-only area/perimeter
check. Add it to a pad net only if the deck does not already model pad metal.
The PDK `sg13g2_bondpad.lib` subcircuit is empty (no elements), and the
`sg13g2_IOPad*` models are not checked here for pad-metal C.

## Comparison with the estimates in the chip deck (`g1_top/README.md`, `run_top.py`)

| Deck element | Deck value | This extraction (total) | Ratio |
|---|---|---|---|
| `Cw_isense` (ISENSE) | 300 fF | 64.5 fF (6.4 to ground, 58.1 coupling: vref_buf 27.9, en_i 13.3, iptat 11.0) | 0.22× |
| `Cw_soft` (cmp_soft) | 20 fF | 269.7 fF (84.0 dac_hard_1, 83.7 dac_hard_0, 52.7 sclk_i) | 13× |
| `Cw_hard` (cmp_hard) | 20 fF | 180.7 fF (47.3 tripped, 47.1 dac_hard_3, 41.0 cmp_clk) | 9× |
| `Cw_en` (EN core side, `en_i`) | 20 fF | 121.7 fF | 6× |
| `Cw_sclk` / `Cw_sdi` | 20 fF | 157.9 / 165.4 fF | 8× |
| `Cw_tripped` | 20 fF | 143.3 fF | 7× |
| `Cw_clk` (osc_clk, ideal-clock case) | 100 fF | 145.0 fF (vref 38.3, osc_trim_3 27.9) | 1.5× |
| `Cosc_rx` | 10 fF | not the same node (receiver input inside the deck) | — |
| not in deck | — | vref 170.8 fF (pbias 38.8, **osc_clk 38.3**, osc_trim_0 27.4); vref_buf 44.8 fF; iptat 44.4 fF; pbias 139.4; pcasc 95.7; cmp_clk 122.5; DAC codes 44-145 fF each; gate_o 80.0; fault_n_o 61.4 | — |
| not in deck | — | series R: 106 Ω `SENSE_N`, 171 Ω `SENSE_P`; 60-710 Ω on the other nets | — |

Findings from the table. These are extraction results. Their effect on the
circuit has not been simulated.

- The 300 fF ISENSE estimate is about 4.7× pessimistic. The digital-net estimates
  are 6-13× optimistic.
- **VREF couples 38.3 fF to `osc_clk`.** That is 46 fC per 1.2 V clock edge
  into the bandgap output. VREF also couples 27.4, 12.8 and 12.8 fF to
  `osc_trim_0`, `osc_trim_1` and `osc_trim_3`, which are static.
- **ISENSE couples 13.3 fF to `en_i`.** It also couples 27.9 fF to
  `vref_buf`, which is quiet.
- **The SENSE pad routes are unequal.** `SENSE_P` is 171 Ω (287 µm) and `SENSE_N`
  is 106 Ω (180 µm), a 65 Ω difference. The G1_SENSE input resistors are
  `rppd w=2u l=76.7u`, about 9.97 kΩ body at the model's nominal 260 Ω/□
  (`cornerRES.lib`), so the difference is about 0.65 % of R1. It adds to the
  differential-amplifier arm mismatch. The effect on CMRR and offset is
  **not simulated**. The pad-cell metal and bond wire, which come before these
  routes, are not included.

## Using the file (not done here; `run_top.py` is owned by another agent)

`.include` the file and instantiate `g1_top_interconnect` (C only) with
each port on the deck node of the same net and `sub` on `0`. The pi variant
`g1_top_interconnect_pi` needs the deck net split into a driver side `<port>`
and a receiver side `<port>_far`. Remove the deck's `Cw_*` estimates for the
nets it covers, or the routing is counted twice. The block PEX netlists hold
only in-macro wiring, so there is no double count with them.

CDL port → deck node (from `run_top.py` as read on 2026-09-25): `isense`→`isense`,
`vref_buf`→`vref_buf`, `vref`→`vref`, `iptat`/`pbias`/`pcasc`→same, `cmp_soft`/`cmp_hard`→same,
`cmp_clk`→`cmp_clk`, `osc_clk`→`osc_clk`, `dac_soft_k_`→`soft<k>`, `dac_hard_k_`→`hard<k>`,
`trip_d`/`clr_d`/`fast_en`/`tripped`→same, `en_i`→`en_core`, `sclk_i`→`sclk_core`, `sdi_i`→`sdi_core`,
`gate_o`→`gate_core`, `fault_n_o`→`fault_core`, `t2f_en_33`/`t2f_mode_33`→`t2f_en33`/`t2f_mode33`,
`temp_out_o`→`temp_out`, `sense_p`/`sense_n`→`sense_p`/`sense_n` (after the pad), `bgr_r4_33`→`r4`.
`net` is the `por_n` tie-high of the digital macro. `osc_en`, `osc_trim_*`, `bgr_r4_12`,
`t2f_*_12`, `sdo_o` and the six test-structure pad nets have no deck node today.

## Limitations

- **Black boxes see no macro geometry.** A top-level wire that runs over a
  macro sees only substrate below it, not the macro's own metal. The
  wire-to-macro-internal coupling is missing, and so is the extra ground C
  from macro metal under the wire. The block PEX, extracted without top-level
  wiring above it, misses the same coupling from the other side.
- **Fill removed.** Floating fill raises the ground and coupling C of the
  routes. It is not included, and its effect was not estimated separately.
- A routed cluster also contains the pin shapes it lands on: macro pins, and
  the core-side M2/M3 pin of an IO cell. Their C is included here and may also
  be in the block PEX, so it can be counted twice. The pin shapes are small
  next to the routes.
- R is a series upper bound per net. For multi-pin nets it is not a
  pin-to-pin value. Contact R to the macro pins is not included.
- kpex 2.5D is an analytical model, not a field solver. Nothing here has been
  compared with a field solver or with a measurement.
- A 1 × 1 µm isolated Metal1 tap (`dummy_tap`, at 700, 1000 µm, no other Metal1
  within 20 µm) is in the view file. It was added for the stock-deck attempt and
  is not connected to any signal.

## Not run

| Item | Status |
|---|---|
| Chip deck simulation with these lumps (any case) | not run |
| Effect of the VREF–osc_clk and ISENSE couplings, and of the SENSE_P/N R mismatch | not run |
| Field-solver (FasterCap) cross-check of any net | not run |
| With-fill extraction of the routes | not run |
| kpex RC (distributed R) mode | not run |

## Files

In this directory: `top_interconnect_20260925.spice` (subcircuits),
`top_interconnect_20260925_summary.json` (per-net table, every coupling ≥ 0 fF),
`top_interconnect_20260925_route_rc.json` (per-net geometry, R, area/perimeter C),
`fullchip_strip_fill_20260925.json` (fill-strip report). In bulk (`${BULK}/fullchip-pex-20260925/`):
`nofill/g1_chip_top_1414_nofill.gds` `6406ba36…`, `topic/g1_top_interconnect_view.gds` `78eeec9c…`,
`topic/prepare.json` `4117b5f2…` (every pin → cluster → CDL net), `topic/kpex/view.lvsdb` `979e6609…`,
`topic/kpex/out/view__g1_chip_top/g1_chip_top_k25d_pex_netlist.csv` `53a20e34…` (raw extraction).

## Commands (repository root, pinned container, CPUs 34-35)

```sh
B=${BULK}/fullchip-pex-20260925
python3 flow/pex/strip_fill.py --input designs/g1-guardian/blocks/g1_padring/layout/g1_chip_top_1414.gds \
  --output $B/nofill/g1_chip_top_1414_nofill.gds --report $B/nofill/strip_fill.json
python3 flow/pex/prepare_top_interconnect.py --input $B/nofill/g1_chip_top_1414_nofill.gds \
  --cdl designs/g1-guardian/blocks/g1_padring/netlist/g1_chip_top_1414.cdl \
  --output $B/topic/g1_top_interconnect_view.gds --report $B/topic/prepare.json
python3 flow/pex/make_view_lvsdb.py $B/topic/g1_top_interconnect_view.gds $B/topic/kpex/view.lvsdb g1_chip_top
python3 flow/pex/kpex_named_top.py --pdk ihp_sg13g2 --threads 2 --lvsdb $B/topic/kpex/view.lvsdb \
  --cell g1_chip_top --2.5D --mode CC --out_dir $B/topic/kpex/out
python3 flow/pex/top_route_rc.py $B/nofill/g1_chip_top_1414_nofill.gds $B/topic/g1_top_interconnect_view.gds \
  <kpex ihp-sg13g2_tech.pb.json> $B/topic/route_rc.json
python3 flow/pex/make_top_interconnect_spice.py $B/topic/kpex/out/view__g1_chip_top/g1_chip_top_k25d_pex_netlist.csv \
  $B/topic/route_rc.json $B/topic/prepare.json top_interconnect_20260925.spice top_interconnect_20260925_summary.json
```

Each command ran inside `flow/run.sh` (the kpex step through `flow/launch_pinned.sh`).
The stock-deck attempt (`kpex --gds` on the view, run twice, the second time with
the dummy tap) ended both times with "No extracted layers found". Those run
directories were deleted before the successful run and are not retained. A
KLayout LVS run with the kpex deck in `run_mode=flat` also produced an LVSDB with
no circuits.

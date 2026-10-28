# Integration checklist, assembly try h (1700 µm ring, h1 supply network, current macros, track T8h)

This list replaces `integration_checklist_g.md` for drop-ins into try h (`layout/r1_top_assemble_h.py`, default =
the h1 supply network, every IO cell as shipped, PLAN.md D24). The try-g list stays as the try-g record; its "Common
items" and block tables stay valid unless a row below changes them. Coordinates: "chip" = µm in the die frame;
"local" = µm in the macro frame (origin at the lower-left corner of the `prBoundary`), orientation R0. Evidence:
README "Try h (track T8h)".

## Macros of try h (run `asm-20261030-h2`)

Snapshot: `<G1_RESULTS_ROOT>/r1_top/asm-20261030-h2/inputs/` (`inputs.sha256`). The generator and the CDL builder
stop if a file does not have the sha256 below (environment `R1G_SHA_<macro>` / `R1G_CDL_SHA_<macro>` for the
drop-ins, `env.sh` in the run directory).

| Macro | Revision | GDS sha256 | LVS netlist sha256 | Drop-in variable |
| --- | --- | --- | --- | --- |
| `r1_padring` | revision d (IO cells as shipped) | `81bba04b3c0655ece75587d6c90b159d4bb860e0dbe0e3dd80e2c65c50d0725d` | projected ref `62405f601d7e5c250fc4ad08359553d8185609e559c2dfecc7fa4ca2166bd8dc` | — |
| `r1_ctrl_top` | 0.9, release `r1ctrl_09_release` (run `r1ctrl_ll_20261028_t32`, signed off; `SHA256SUMS` checked) | `aabd9fe045de988dbb9364ca36424dfb6bb497f42a4455a3ed1e32df218165e6` (LEF `f4d575a43a4c40465f4753423dd8dbd5ff4768a32e4216d3ac8f5d2969d799fe`) | netlist `r1_ctrl_top.nl.v` `e8cac55e47864a8a8793104201dca9327f578d0952faca06f8a9f0ce84bf5502`; `final/pnl/r1_ctrl_top.pnl.v` `0da12f3eac87b726bd14719e0e18d44b1272d0da4959a4974580a91502a6ae50` (CDL by `pnl2cdl`: `429dd8acc502089eaf471b4c8b8081eb68adc8127cd53160d371797b6972de2c`) | `R1G_SHA_r1_ctrl_top`, `R1H_CTRL_RELEASE=r1ctrl_09_release`, `R1H_CTRL_RUN=r1ctrl_ll_20261028_t32` |
| `r1_adc` | layout B7, netlist revision 5, SAR sub-macro `t2j-ll-h2312-h` | `5dcf53803eb33c931f558f857bd609e5b6e6a858f9bcc8161550a29be042ad7b` (= `layout/r1_adc_layout_b7.gds`) | `layout/r1_adc_lvs_b5.cdl` `0740d3a21d00e32faeec149c3f5b594d45e4791c6ffee137edf84795e70b0392` (the B7 block LVS reference) | `R1G_SHA_r1_adc`, `R1G_CDL_SHA_r1_adc` |
| `r1_afe` | layout E9c (`layout-e9c-cal19`), netlist F3 | `adb7632ba4d7df94a0a18ae01f7c3fcd50c10c5f3e87a688de6f66fc873b8a08` | `layout/r1_afe_lvs.cdl` `cc9d997a512bf7d691504f2e694319e8daa8d3868c8c9522366c0d7533a30cd9` | `R1G_SHA_r1_afe`, `R1G_CDL_SHA_r1_afe` |
| `r1_isense` | layout c (revision 2) | `192dd37aa592b85d68b158b18f0f71c8e906664783b047dcdd3bf1ceacd6c7ac` | `3021793df19e112a96bdcb6d5618b3b3a00e06bc80baa02c7e293da16f3212f2` | — |
| `r1_bias` | revision 2 | `e7ee13940db0ecc2a36c8bf7c6d1947358aceb6dd1dff3b3add9f4eafa2bb78c` | `abb7bc280fd1632ec405e7cef62a2b4ba0ab688bc6fa85d897d1b0913a36b4a8` | — |
| `r1_osc` | revision 2, layout r2d | `7c5fb60fdbbfa3cce7714520d3bc652292f0ff964452e3bf4afe226ea68ba971` | `600d5f2bb983601d904142c9d15f62beb363b91bbfafe7ded63c1e2cea6912aa` | — |
| `r1_safe` | revision 3 | `fbc3113948e0c15e1e049cfad1e2e5c5349b10ba0ae7d250f5b228e50aa28324` | `a083d26387c3006de04e2f6b19f454aaa39c81af23b213f545aae8af3b570732` | — |
| `r1_bgr` | as try f | `324e3c27477a77c4a32d6760366d8d1fb82bea4887ae26b905cd7022aac54005` | `c4d175eebf104a852ce0d9b4b426a0cfa6ede80bc39e7088c179c9ae179fae2b` | — |
| `r1_t2f` | as try f | `5e7aa75ae9335b12b1c825d326e586c742755bd9305074fc1cdc2507d17af9a7` | `9867279d8e07805a9af642fd42067b14862e43fcbc39ae31cbb17bf753cef9aa` | — |
| `r1_ls` (6) | as try f | `a4f496364b55c71a035f44a9b13b68fd8475f98b05f5e13a4e38e9ec1703b4de` | `4f3fefbedfa219acf7d9506d8e8edc878be372f5abc551cba2471caaf2a12460` | — |
| `r1_gate_lv` | as try f | `a3dee0f091c5236f7b6ff231b765d0b70e60a6e791d9db0b12fd821ce44e013b` | `c0602540bbe0bc34c023a511e7ee1c8f03e6c4e519624d611fe187a5b3afe4ea` | — |

## How a drop-in works (try h)

1. Make a new run directory `<G1_RESULTS_ROOT>/r1_top/<new run>/inputs/` and copy `inputs/` of the run of record
   (`asm-20261030-h2`) into it.
2. Put the new GDS and LVS CDL into `inputs/ofrecord/` with the names `r1_adc.gds`, `r1_adc_lvs.cdl`, `r1_afe.gds`,
   `r1_afe_lvs.cdl` (or a new ctrl release under `<G1_RESULTS_ROOT>/r1_ctrl/<release>/`).
3. Copy `env.sh` of the run of record and change the sha256 of the new file (`R1G_SHA_<macro>`,
   `R1G_CDL_SHA_<macro>`; ctrl: `R1G_SHA_r1_ctrl_top`, `R1H_CTRL_RELEASE`, `R1H_CTRL_RUN`). Without them the
   generator and the CDL builder stop on the hash check.
4. Run `sh designs/r1-joint/blocks/r1_top/flow/run_try_h.sh <new run> gen cdl`, then the checks, the supply
   extraction, the fill and the filled checks as in `chain.sh` of the run of record, the ctrl derate
   (`irderate/run_derate.sh` with `R1_DERATE_CTRL_RELEASE` / `R1_DERATE_CTRL_RUN`) and the chip PEX (README "Try h
   (track T8h)", reproduction).
5. The self-check in `r1_top_assembly.json` must stay empty (`self_check_net_conflicts`, `routes_inside_macros`,
   `tm1_over_mim_blocks`, `maze.failed`, `maze.access_failed`) and `merged_std_cells` must show no entry with
   `"merged": false`.
6. The chip CDL of record changes with every new block CDL or ctrl netlist: `<run>/lvs/r1_top_h.cdl` with
   `r1_top_h_includes.txt`. The post-layout campaign takes the CDL of the new run.

## r1_adc layout B10 (expected drop-in)

B10 (drift routing inside the slice, `layout/r1_adc_layout_b10.gds`) has the same pins and box as B7. If it is
adopted, it drops in by `R1G_SHA_r1_adc` (and `R1G_CDL_SHA_r1_adc` if its LVS reference changes). Keep:

| Item | Requirement |
| --- | --- |
| Box, origin, pins | as B7 (`integration_checklist_g.md`, r1_adc table): 439.0 × 205.42 µm at chip (592.0, 376.0), 52 pins at the B7 positions |
| `vss` pin | 2.0 µm (B7). The top-level `vss` neck follows the pin width; the Metal3 riser (x 741-743) is 2.0 µm, EM 2 mA/µm: 4 mA against 1.97 mA (B5 tt) |
| Metal1-Metal5 coverage | not below B7 (chip window minimum at the ADC corner: README "Try h (track T8h)", fill) |
| Metal5 inside the box | informational (D23); the chip density deck decides |

## Supply feed (try h, unchanged from h1)

| Item | Requirement |
| --- | --- |
| `r1_ctrl_top` stripes | The top-level feed lands on the 7 VDD TopMetal1 stripes (local x 23.54 + 75.6 k, from local y 11.12) and the 7 VSS stripes (local x 29.74 + 75.6 k, from local y 10.71). A ctrl revision must keep them and keep its own TopMetal2 at local y ≥ 23.7 (`TM2.bR` to the h1 VDD TopMetal2 bar). ctrl 0.9 against 0.8: stripes and pins identical; TopMetal1 signal routes and two TopMetal2 signal pieces (local y 57-59 and 69-71) differ (`<G1_RESULTS_ROOT>/r1_top/asm-20261030-h2/probe/xor_ctrl08_09_detail.json`) |
| Feed resistance | VDD + VSS ≤ 1.43 Ω at the worst ctrl grid point, max sheet (40.25 mA, ctrl 0.8 typ power; ctrl 0.9 LibreLane typ power is 30.16 mW = 25.1 mA, so 40.25 mA is conservative) |
| Ctrl derated setup | ≥ 1 ns at the extracted losses (`irderate/run_derate.sh`, release netlist, sign-off SDC, nominal SPEF) |
| Shared isense-bgr VSS path | ≤ 2.3 Ω (INTERFACES "isense pedestal vs bandgap ground") |
| IO cells | `sg13g2_io` cells as shipped (D24); no top-level metal across the `iovdd` / `iovss` rails |

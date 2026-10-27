# R1_TOP

Block `r1_top` (track T8, P3 preparation). This block assembles the R1 chip top level from the ring of record and
the macros. Try g (below) is the current state: the current macros, the chip CDL of record and the extracted supply network. Try f has no placeholder: every macro is a real layout. Tries d and e had placeholder outlines.

## Try g (2026-10-27, track T8e; run names as the brief, `asm-20261028-g…`): current macros, ADC 23.12 µm taller, ctrl 0.8 — run of record `asm-20261028-g3`, filled `asm-20261028-g3-fill`

State: every macro is the current layout: `r1_ctrl_top` 0.8, `r1_adc` with the SAR sub-macro (439.0 × 205.42 µm),
`r1_afe` E6. All 173 top-level signal nets are routed, including the new `CUR_TRK`. The 30 temporary antenna diodes
of try f are removed. Chip DRC (main, antenna, maximal, density) and LVS (comparer-limit deck) pass on the filled
chip; the stock LVS deck crashes in KLayout (tooling, F1). The supply network is **extracted** (KLayout
RNetExtractor and ngspice DC), not estimated. The chip CDL of record for the post-layout campaign is
`<G1_RESULTS_ROOT>/r1_top/asm-20261028-g3/lvs/r1_top_g.cdl`. Generator: `layout/r1_top_assemble_g.py`. Driver:
`flow/run_try_g.sh`. LVS reference builder: `lvs/make_top_cdl_g.py`. Picture: [`layout/r1_top_g.png`](layout/r1_top_g.png).

Runs: `g1` and `g2` are development runs; `g3` is the run of record.

| Run | Change | GDS sha256 (unfilled) | Result |
| --- | --- | --- | --- |
| `asm-20261028-g1` | try-f floorplan with the current macros | `cd045218…` | DRC main / antenna / maximal 0; LVS limits deck match; VDD drop at the ctrl 56 mV typ (too high, F5) |
| `asm-20261028-g2` | + south VDD feed (TopMetal2 strap and bar to the ctrl stripes), south supply stacks | `9d379180…` | VDD drop 23.6 mV; DRC main 1 (`TM2.bR`, the bar 3.14 µm from the first ctrl TopMetal2 strap, F6); IO-filler VDD strap 10.5 mA in 6 µm (limit 12 mA) |
| `asm-20261028-g3` | bar 2 µm lower (5.14 µm space), IO-filler VDD straps 6 → 10 µm | `8f1c5d7cd9df4a1e47ef9c19b009f4b7b8eb06b4c60493b2f1c964d4aaa510b7` | of record (below) |

### Inputs (sha256)

The ADC GDS is the file `blocks/r1_adc/layout/r1_adc.gds` at the start of try g (2026-10-27 17:47 CET). It is the
B6 generator run `layout-b6-dev3`. Its README gives block DRC, antenna, LVS on both decks and the pin check as
passed. B6 has the same box, the same pins and the same LVS netlist as B5. Layout B5
(`r1_adc_layout_b5.gds`) is in the snapshot as the fallback; the generator takes it with `R1G_SHA_r1_adc`.
Snapshots: `<G1_RESULTS_ROOT>/r1_top/asm-20261028-g3/inputs/` (`inputs.sha256`).

| Macro | Revision | GDS sha256 | LVS netlist sha256 |
| --- | --- | --- | --- |
| `r1_padring` | revision d | `81bba04b3c0655ece75587d6c90b159d4bb860e0dbe0e3dd80e2c65c50d0725d` | projected ref `62405f601d7e5c250fc4ad08359553d8185609e559c2dfecc7fa4ca2166bd8dc` |
| `r1_ctrl_top` | 0.8, release `r1ctrl_08_release` (run `r1ctrl_ll_20261027_t22`; `SHA256SUMS` checked) | `f8bc16ed7233d1ea3eb12dd3f0cc1045eb169ea842c0d7ab6aad06d9ed302d2e` | `final/pnl/r1_ctrl_top.pnl.v` `160148ae00de2bec44a6ec40d08497e346e2009b95246f9ce3983da93b75415a` (CDL by `pnl2cdl`: `6cdbdd21fae2c8b564cc6157f0ec1f1b74878e717aa9274a27ae694819826926`) |
| `r1_adc` | B6-dev3 at the start (B5 analog part + SAR sub-macro `r1_adc_sar` `t2j-ll-h2312-h`) | `9d6dad3d23a033e0484d4fc8d23ba25280c3231680f244c25b44dc9c5c49d880` (B5: `551dab83d55b31763e292663fd24b6b74f5cb5bd628db89a28f9d1dbaf0ae327`) | B5 CDL `layout/r1_adc_lvs_b5.cdl` (analog netlist of record + SAR gate level) `0740d3a21d00e32faeec149c3f5b594d45e4791c6ffee137edf84795e70b0392` |
| `r1_afe` | layout E6 (`layout-e6-dev16`, revision F2, commit fd0fcf4e4) | `12a059ca4b9468541c479b13e8e77d946852b57c826f7dd568db60ae4f64ba7f` | `4271a5f9d38794c7be2daa399c04ba8a702daae5cd796a3e525d300f0bec91a7` |
| `r1_isense` | layout c (revision 2) | `192dd37aa592b85d68b158b18f0f71c8e906664783b047dcdd3bf1ceacd6c7ac` | `3021793df19e112a96bdcb6d5618b3b3a00e06bc80baa02c7e293da16f3212f2` |
| `r1_bias` | revision 2 | `e7ee13940db0ecc2a36c8bf7c6d1947358aceb6dd1dff3b3add9f4eafa2bb78c` | `abb7bc280fd1632ec405e7cef62a2b4ba0ab688bc6fa85d897d1b0913a36b4a8` |
| `r1_osc` | revision 2, layout r2d | `7c5fb60fdbbfa3cce7714520d3bc652292f0ff964452e3bf4afe226ea68ba971` | `600d5f2bb983601d904142c9d15f62beb363b91bbfafe7ded63c1e2cea6912aa` |
| `r1_safe` | revision 3 (as try f) | `fbc3113948e0c15e1e049cfad1e2e5c5349b10ba0ae7d250f5b228e50aa28324` | `a083d26387c3006de04e2f6b19f454aaa39c81af23b213f545aae8af3b570732` |
| `r1_bgr` | as try f | `324e3c27477a77c4a32d6760366d8d1fb82bea4887ae26b905cd7022aac54005` | `c4d175eebf104a852ce0d9b4b426a0cfa6ede80bc39e7088c179c9ae179fae2b` |
| `r1_t2f` | as try f | `5e7aa75ae9335b12b1c825d326e586c742755bd9305074fc1cdc2507d17af9a7` | `9867279d8e07805a9af642fd42067b14862e43fcbc39ae31cbb17bf753cef9aa` |
| `r1_ls` (6) | as try f | `a4f496364b55c71a035f44a9b13b68fd8475f98b05f5e13a4e38e9ec1703b4de` | `4f3fefbedfa219acf7d9506d8e8edc878be372f5abc551cba2471caaf2a12460` |
| `r1_gate_lv` | as try f | `a3dee0f091c5236f7b6ff231b765d0b70e60a6e791d9db0b12fd821ce44e013b` | `c0602540bbe0bc34c023a511e7ee1c8f03e6c4e519624d611fe187a5b3afe4ea` |

### Placement (deltas against try f)

No macro moved. The ADC stays at its try-f origin and grows 23.12 µm to the north only.

| Macro | Origin (µm) | Size (µm) | Delta against try f | Note |
| --- | --- | --- | --- | --- |
| `r1_adc` | (592.0, 376.0) | 439.0 × 205.42 (try f 439.0 × 182.3) | (0, 0); north edge +23.12 µm (y 558.3 → 581.42) | channel ADC north edge – `r1_ctrl` south edge: 91.88 µm (try f 115.0 µm) |
| `r1_ctrl_top` 0.8 | (538.8, 673.3) | 532 × 679 | (0, 0) | same box and pins as 0.6, plus `cur_trk` (south, local x 280.80) |
| `r1_afe` E6 | (336.0, 740.0) | 192.8 × 494.4 | (0, 0) | same pins as E3; supply pins 1.0 µm |
| all other macros, the decap row and the tie cell | as try f | as try f | (0, 0) | — |
| 30 × `sg13g2_antennanp` (y 661.0) | — | — | removed | the SAR sub-macro drives the ADC outputs |

Clearances at the ADC: west 28.0 µm to `r1_bias` (x 564), east 57.8 µm to `r1_safe` (x 1088.8), north 91.88 µm to
`r1_ctrl`. The `VREF_B` Metal5 run (y 642–648) is 60.6 µm above the new ADC north edge. Full table:
[`reports/placement_g.csv`](reports/placement_g.csv).

### Connectivity

1. 173 top-level signal nets, all routed: 99 by hand, 74 by the maze router (try f: 172). 76 maze jobs and 139
   access stubs, 0 failed. Generator self-check: 0 net conflicts, 0 overlaps, 0 pairs closer than 10 µm, 0 routes
   inside macros, 0 TopMetal1 over MIM blocks.
2. The 37 ADC north pins (`adc_*`, `is_smp`, `clk`, `cur_trk`, `por_n`) are on Metal2 in B5/B6. The access stubs now
   start on Metal2 and go north. The labels use the CDL form (`adc_raw_a<k>`).
3. `CUR_TRK` (new): `r1_ctrl` south pin (local x 280.80) → `r1_adc` north pin (local x 16.80), maze, Metal2 1.6,
   Metal3 89.6, Metal4 209.6 µm.
4. `OSC_CLK`: osc → ctrl clk by the straight Metal3 line; ADC branch by the maze, 1032.8 µm (Metal2 26.4, Metal3
   479.2, Metal4 527.2 µm, 9 vias).
5. `VREF_B` (Metal4 riser x 566, Metal5 run y 642–648 with VSS shields) and the isense VSS trunk are as try f.
6. 45 PDK cells that the macro GDS files bring as second copies (`sg13g2_*$N`: 31 standard cells, mostly of the ADC
   SAR, and 14 IO-cell sub-cells such as `sg13g2_DCNDiode`) are merged with the identical first copies (shapes and
   labels compared per layer; 0 cells differ). The CDL builder drops 85 duplicate
   `.SUBCKT` blocks of the ADC CDL (84 standard cells and the bondpad); each one is identical text.
7. Unconnected macro pins: `r1_ctrl` `bias_en`; `r1_bgr` `iptat`, `vbe`, `dvbe` (test nodes); `r1_adc` `topap`,
   `topan`, `topbp`, `topbn` (CDAC top-plate test ports).
8. Supply: south VDD feed (TopMetal2 strap x 566–590 from the inner south VDD row to a TopMetal2 bar at y 684–692,
   with TopVia2 onto the 7 ctrl VDD TopMetal1 stripes); five south supply stacks (Metal4 → TopMetal2) at the
   IO-filler straps; IO-filler VDD Metal3 straps 10 µm.

### Clock skew (`OSC_CLK`, ADC pin against ctrl pin)

**Estimated** (`flow/clk_skew_g.py`): RNetExtractor resistance of the extracted `OSC_CLK` net, Elmore delay with
assumed wire capacitance. Resistance osc → ADC clk 313.3 Ω typ / 451.9 Ω max sheet; osc → ctrl clk 5.2 / 6.1 Ω.

| Case | Skew (ps) |
| --- | --- |
| typ sheet, 0.2 fF/µm, ADC pin 34–60 fF | 48–51 |
| all cases (typ / max sheet, 0.1–0.3 fF/µm, 34–60 fF) | +30.7 to +97.1 |

The INTERFACES row "ADC → ctrl timing" allows 0.09 ns (ADC bits change ≥ 0.596 ns after the `clk30` edge at tt,
0.096 ns margin). Result: typ 48–51 ps, **passed**; the bound case (max sheet, 0.3 fF/µm, 60 fF) is 97 ps. The sign
is always positive: the ADC clock edge is later than the ctrl clock edge, so the ADC → ctrl hold margin grows (0.096
→ ≥ 0.127 ns). The ctrl → ADC direction has ≥ 0.6 ns (ctrl outputs change after its clock latency of about
0.67 ns; estimate). No length matching or retiming is needed. The skew is not extracted with capacitance (not run).

### Supply network

Report: [`reports/supply_g.md`](reports/supply_g.md). **Extracted**: KLayout RNetExtractor on the top-level
supply nets plus the ctrl power grid; ngspice DC with the block currents (ctrl 0.8: 40.25 mA).

| Item | typ | max sheet | State |
| --- | --- | --- | --- |
| Shared `r1_isense`–`r1_bgr` VSS path resistance (limit ≤ 2.3 Ω) | 1.494 Ω | 2.021 Ω | passed |
| Ground offset isense − bgr, all currents / ctrl return current alone | 5.34 / 3.60 mV | 6.78 / 4.46 mV | — |
| Static drop VDD at `r1_ctrl` (worst of 63 grid points) | 22.8 mV | 30.6 mV | — |
| VSS rise at `r1_ctrl` (worst) | 46.1 mV | 63.6 mV | — |
| Static drop VDDA, worst (`r1_afe` far pin) | 45.3 mV | 57.2 mV | — |
| EM, top-level trunks, straps, stacks (75 rows, bound or extracted) | all passed | all passed | passed |
| EM, macro supply pins (all ≥ 1 µm now) | `r1_adc` `vss` 1.972 mA of 2.0 mA (1.4 % margin) | — | passed |

### Fill and density

Fill (`flow/fill_top.sh`, thru `r1_ctrl_top:10,30,50,67;r1_safe:10`, distances Metal2 0.45, GatPoly gap 1.6,
Metal3-5 0.45 µm): geometry gate passed (only fill datatypes differ). Chip density deck: **0**.

Window coverage, 800 µm windows, 100 µm step (`flow/probe_window_minmax.py`, finer than the deck's 400 µm step):
minimum Metal1 26.29 %, Metal2 25.58 %, Metal3 25.86 %, Metal4 27.30 %, Metal5 27.35 % (limit 25 %), all at the
ADC corner window (400, 400) or (500, 500). Maximum Metal5 54.52 % (limit 75 %, `M5Fil.k`). Global Metal1-Metal5
42.0 / 46.9 / 52.4 / 52.9 / 46.2 % (limits 35-60 %). Margins are small: Metal2 0.58 %, Metal3 0.86 %.

ADC Metal5 density: inside the ADC box the chip has 70.46 % Metal5 (`flow/probe_adc_box_density.py`; B5 block
value 71.6 %). The chip density deck does **not** flag it. The deck checks Metal5 only over the whole chip (`M5.j`
/ `M5.k`, 35-60 %) and in 800 × 800 µm windows (`M5Fil.h` / `M5Fil.k`, 25-75 %). The ADC box is 0.09 mm², 14 % of a
window; the highest Metal5 window is 54.52 %, at (100, 100), not at the ADC.

### Status

GDS (unfilled) `<G1_RESULTS_ROOT>/r1_top/asm-20261028-g3/r1_top.gds`, sha256
`8f1c5d7cd9df4a1e47ef9c19b009f4b7b8eb06b4c60493b2f1c964d4aaa510b7`. Filled chip (the deliverable)
`<G1_RESULTS_ROOT>/r1_top/asm-20261028-g3-fill/r1_top.gds`, sha256
`3b337a55e747942c0c202888bbf675a65222e64645f565688355e23ba8c4ddff`. Chip CDL of record
`<G1_RESULTS_ROOT>/r1_top/asm-20261028-g3/lvs/r1_top_g.cdl`, sha256
`979e6cc3f27c5787c06f270e015a04e8334bb30a8a6403ef512fe9c699043b72`; include list with the sha256 of each source:
`lvs/r1_top_g_includes.txt` in the same directory. The CDL is the same for g1, g2 and g3.

| Check | Unfilled `-g3` | Filled `-g3-fill` (of record) | Evidence |
| --- | --- | --- | --- |
| Generator self-check | passed (0 / 0 / 0 / 0 / 0) | — | `r1_top_assembly.json` |
| DRC main | passed, 0 (run `-g2`: 1, F6) | passed, 0 | `drc_main/` |
| DRC antenna | passed, 0 (try f needed 30 diodes) | passed, 0 | `drc_antenna/` |
| DRC maximal | passed, 0 (run `-g1`: 0) | passed, 0 | `drc_maximal/` |
| DRC density | not run on the unfilled GDS | passed, 0 | `drc_density/` |
| LVS, comparer-limit deck copy | passed: "Netlists match", 59 circuit pairs; `r1_top` 261 devices, 51 subcircuits; `r1_ctrl_top` 19465 / 19469 nets | passed: "Netlists match", 59 pairs, `r1_top` 261 devices, 51 subcircuits | `lvs_limits/`, [`reports/runs/asm-20261028-g3_lvs_report.txt`](reports/runs/asm-20261028-g3_lvs_report.txt) |
| LVS, stock PDK deck | failed to run: KLayout signal 11 at "Extracting diodevdd_2kv ESD device" (g1 twice, g2, g3; F1) | not run (same deck, same crash expected) | `lvs_stock/` |
| Bond map (24 openings) | — | passed, 24 of 24 openings matched, 22 labels at row centres, `all_ok` | `bondmap/` |
| Supply R, IR drop, EM | passed (extracted; see the table above) | — | `supply_g.json`, `supply_rnet/`, `reports/supply_g.md` |
| `OSC_CLK` skew | passed at typ (48–51 ps ≤ 90 ps; estimated, not extracted with C) | — | `clk_skew_g.json` |
| Post-layout simulation of top-level nets | not run | not run | — |
| IHP intake pre-check | not run | not run | — |
| Run records | written | written | `reports/runs/asm-20261028-g1.json`, `-g2.json`, `-g3.json`, `-g3-fill.json` |

Evidence paths are relative to `<G1_RESULTS_ROOT>/r1_top/<run>/` unless they start with `reports/`.

### Open issues (try g)

1. `r1_adc` B6 final and `r1_afe` E7 are not in this try. Drop-in: `reports/integration_checklist_g.md`.
2. The stock LVS deck crashes on the chip (F1). Only the comparer-limit deck copy gives a result.
3. `r1_adc` `vss` pin: 1.972 mA in 1.0 µm (limit 2.0 mA, tt; ff not known). Recommended: ≥ 2 µm in B6/B7.
4. Window density margins are small (Metal2 0.58 %, Metal3 0.86 %, at the ADC corner). A lower Metal2/Metal3 coverage
   in B6 or E7 can fail `M2Fil.h` / `M3Fil.h`.
5. Supply loss at `r1_ctrl`: 69 mV typ / 94 mV max sheet (VDD drop + VSS rise). The ctrl timing sign-off has no
   IR-drop derate check (not run).
6. The `OSC_CLK` skew is an Elmore estimate with assumed capacitance; extraction with capacitance not run.
7. `bias_en` is open; `az` pins are tied to `az_win`; `r1_t2f` vref is on `VREF_B` (INTERFACES T9), as try f.
8. No post-layout simulation of any top-level net with this GDS (the T10 campaign takes the CDL of record).

### Failures and mistakes (try g)

| # | What happened | Class | Fix |
| --- | --- | --- | --- |
| F1 | The stock PDK LVS deck crashes with signal 11 at "Extracting diodevdd_2kv ESD device" on the chip (g1 twice, g2, g3). The same crash is in the `r1_safe` record (KLayout 0.30.9). | tooling | Recorded; the comparer-limit deck copy gives the result |
| F2 | The ADC GDS in the working tree at the start was B6-dev3, not B5 of record. | spec-ambiguity | Took the file as found (brief: "take the GDS as it is at your start"); B5 kept as fallback |
| F3 | RNetExtractor internal error (`dbPLC.cc:543`) on the Metal1 ring annulus. | tooling | Metal1 and Via1 left out of the supply network (conservative) |
| F4 | Run g2, first supply run: the ctrl internal grid was not in the network, so the new south feed showed no effect. | verification-gap | Ctrl TopMetal1/TopVia2/TopMetal2 grid and 63 ctrl ports added; first files kept as `*_try1` |
| F5 | Run g1: VDD drop at the ctrl 56 mV typ; the ctrl 0.8 current (40 mA) came from pad 1 around the ring. Try f estimated 32 mV by square count. | estimation | South VDD feed (run g2): 23.6 mV |
| F6 | Run g2: DRC main 1, `TM2.bR`: the new TopMetal2 bar was 3.14 µm from the first ctrl TopMetal2 strap (5.0 µm needed for a parallel run > 50 µm). | functional-bug | Bar top 694.0 → 692.0 µm (run g3) |
| F7 | EM cut lines: first 0 elements (node locations are already in µm, the script scaled them again); then values above the total net current on wide shapes (Metal4 trunks, VDDA risers: up to 324 mA against 4.31 mA). | numerical | Unit fix; cut sums only on narrow straps; gradient method and bound rows for the rest |
| F8 | Run g2: IO-filler VDD strap at x 537 carried 10.5 mA in 6 µm (limit 12 mA). | estimation | Straps 10 µm (run g3: 8.85 mA, limit 20 mA) |
| F9 | A foreground `sleep` to wait for a run was blocked by the tool. | process-hygiene | Background wait loop |
| F10 | `flow/write_run_json.py` reads only `inputs/**/sha256.txt` and cpuset 116-119. | tooling | `flow/write_run_json_g.py` adds the try-g snapshot list and cpuset |

### Built against (try g)

| Item | Version | How established |
| --- | --- | --- |
| PDK | IHP-Open-PDK `84374023ee8b4b126bebbba67fcbada0a9c0ff0b` | checked by `flow/run.sh` |
| KLayout | 0.30.9 | container, DRC and LVS logs |
| ngspice | 46 | `ngspice -v` in the container |
| Container | `tapeoutbench-eda:latest`, `sha256:ddeb6957…` | `flow/run.sh` |
| xschem / LibreLane / CACE | not used by this try (ctrl 0.8 is a LibreLane release) | — |

### Reproduce try g (repository root, POSIX shell)

1. Set the environment: `G1_CPUSET=112-119; export G1_CPUSET; G1_RESULTS_ROOT=<results root>; export G1_RESULTS_ROOT; G1_WORKDIR=.; export G1_WORKDIR`.
2. Copy the snapshot `inputs/` of `asm-20261028-g3` into `<G1_RESULTS_ROOT>/r1_top/<run>/inputs/`. The scripts
   check every hash (`R1G_SHA_<macro>`, `R1G_CDL_SHA_<macro>` select other revisions).
3. Run `sh designs/r1-joint/blocks/r1_top/flow/run_try_g.sh <run> gen cdl main antenna maximal lvs lvsstock`.
4. Run `sh designs/r1-joint/blocks/r1_top/flow/fill_top.sh <run dir> <run dir>-fill 0 "r1_ctrl_top:10,30,50,67;r1_safe:10" 0.45 1.6 0.45`.
5. Run `sh designs/r1-joint/blocks/r1_top/flow/run_fill_checks.sh <run dir> <run dir>-fill`.
6. Run `flow/run.sh klayout -b -r designs/r1-joint/blocks/r1_top/flow/probe_window_minmax.py -rd g=<run dir>-fill/r1_top.gds -rd out=<run dir>-fill/window_density.json`
   and the same with `flow/probe_adc_box_density.py`.
7. Run the supply and skew scripts as in `reports/supply_g.md`, then
   `flow/run.sh python3 designs/r1-joint/blocks/r1_top/flow/clk_skew_g.py <run dir> <run dir>/clk_skew_g.json`.
8. Write the records with `flow/write_run_json_g.py` and `flow/write_fill_run_json.py`, and the placement with
   `flow/write_placement_g.py`.

New files of try g: `layout/r1_top_assemble_g.py`, `lvs/make_top_cdl_g.py`, `flow/run_try_g.sh`,
`flow/write_placement_g.py`, `flow/supply_g_rnet.py`, `flow/supply_g.py`, `flow/clk_skew_g.py`,
`flow/probe_adc_box_density.py`, `flow/write_run_json_g.py`, `reports/supply_g.md`,
`reports/integration_checklist_g.md`, `reports/placement_g.csv`, `layout/r1_top_g.png`.

## Try f (2026-10-27, track T8): every macro real — run of record `asm-20261027-f3`, filled `asm-20261027-f3-fill`

State: every macro is a real layout. No placeholder is left. All 172 top-level signal nets are routed. The filled
chip passes LVS (limits deck), density, maximal, antenna and the bond map (24/24). DRC main has 1 marker inside
`r1_afe` E3 (a macro defect, not top-level). The supply network is checked by square count (estimated). The chip is **not** functional: `r1_adc`
layout A has no SAR logic (open issue 1). Generator: `layout/r1_top_assemble_f.py`. Driver: `flow/run_try_f.sh`.

### Inputs (sha256)

| Macro | Revision | GDS sha256 | LVS netlist sha256 |
| --- | --- | --- | --- |
| `r1_padring` | revision d | `81bba04b3c0655ece75587d6c90b159d4bb860e0dbe0e3dd80e2c65c50d0725d` | projected ref `62405f601d7e5c250fc4ad08359553d8185609e559c2dfecc7fa4ca2166bd8dc` |
| `r1_ctrl_top` | 0.6, run `r1ctrl_ll_20261026_t12` | `a16423f78e8039b5fe033377d1d856dea9012501fb9888ad37b26809ccf97497` | `final/pnl/r1_ctrl_top.pnl.v` `8f8a70771beccdcdd72247103eb33f36fce1a4e12a77cc977de3baad645ce242` (CDL by `pnl2cdl`: `6c8ccf850e52314bd5a69550f5262df8b8490f77386e2031b4fc8efa1101fef7`) |
| `r1_afe` | E3 (commit 902d1ab26) | `1f3ad1f16b9595098779d73dee59694415ffb054e13e811acd63bcea1b5f33f4` | `112be732b3b772301fd1bb7c20dc1f697788197573fd83976aa49019419bad69` |
| `r1_adc` | layout A (commit b4a95ae60) | `95c8296acc97bc3ace0e09a51db01465a0e800aa4fa2fc3162b784e316578a5d` | `2e18b5c2f80a2755f83f4c181012f6733bfb8cbede01f993abfadf51a534e18b` |
| `r1_isense` | layout c (commit c09410f07) | `192dd37aa592b85d68b158b18f0f71c8e906664783b047dcdd3bf1ceacd6c7ac` | `3021793df19e112a96bdcb6d5618b3b3a00e06bc80baa02c7e293da16f3212f2` |
| `r1_bias` | revision 2 (commit ae4dfac95) | `e7ee13940db0ecc2a36c8bf7c6d1947358aceb6dd1dff3b3add9f4eafa2bb78c` | `abb7bc280fd1632ec405e7cef62a2b4ba0ab688bc6fa85d897d1b0913a36b4a8` |
| `r1_osc` | revision 2, layout r2d | `7c5fb60fdbbfa3cce7714520d3bc652292f0ff964452e3bf4afe226ea68ba971` | `600d5f2bb983601d904142c9d15f62beb363b91bbfafe7ded63c1e2cea6912aa` |
| `r1_safe` | as try e | `fbc3113948e0c15e1e049cfad1e2e5c5349b10ba0ae7d250f5b228e50aa28324` | `a083d26387c3006de04e2f6b19f454aaa39c81af23b213f545aae8af3b570732` |
| `r1_bgr` | as try e | `324e3c27477a77c4a32d6760366d8d1fb82bea4887ae26b905cd7022aac54005` | `c4d175eebf104a852ce0d9b4b426a0cfa6ede80bc39e7088c179c9ae179fae2b` |
| `r1_t2f` | as try e (now R0) | `5e7aa75ae9335b12b1c825d326e586c742755bd9305074fc1cdc2507d17af9a7` | `9867279d8e07805a9af642fd42067b14862e43fcbc39ae31cbb17bf753cef9aa` |
| `r1_ls` (6) | as try e | `a4f496364b55c71a035f44a9b13b68fd8475f98b05f5e13a4e38e9ec1703b4de` | `4f3fefbedfa219acf7d9506d8e8edc878be372f5abc551cba2471caaf2a12460` |
| `r1_gate_lv` | as try e | `a3dee0f091c5236f7b6ff231b765d0b70e60a6e791d9db0b12fd821ce44e013b` | `c0602540bbe0bc34c023a511e7ee1c8f03e6c4e519624d611fe187a5b3afe4ea` |

The generator and `lvs/make_top_cdl_f.py` check every hash. Snapshots of the inputs of record and of the working-tree
files at the start: `<G1_RESULTS_ROOT>/r1_top/asm-20261027-f2/inputs/` (`inputs.sha256`).

### Placement (deltas against try e)

| Macro | Origin (µm) | Delta against try e | Reason |
| --- | --- | --- | --- |
| `r1_ctrl_top` 0.6 | (538.8, 673.3) | (−5.0, +0.3) | 0.6 outline 532 × 679 µm and its pin template |
| `r1_bias` revision 2 | (444, 376) | y −112.6 | 236.74 µm high; next to `r1_bgr`, short bias lines to the ADC and the AFE |
| `r1_t2f` | (366.8, 622.74), R0 | was MY at (444, 376) | the slot under the bias is taken; t2f moves west of the bias, above the bgr |
| `r1_isense` layout c | (1113.8, 735) | (+25, 0) | clear channel for the isense pairs between `r1_safe` and `r1_ctrl` |
| `r1_adc` layout A | (592, 376) | 0 (real macro in the try-e slot) | — |
| `r1_ls` (6) | x 480.25 / 495.45 / 510.65, y 640.3 / 660.3 | moved from x 545 | under the t2f and AFE control lines |
| `r1_afe`, `r1_osc`, `r1_safe`, `r1_bgr`, `r1_gate_lv` | as try e | 0 | — |

Full table with the S7 C4 deltas: [`reports/placement_f.csv`](reports/placement_f.csv). Generator self-check: 0 net
conflicts, 0 overlaps, 0 pairs closer than 10 µm, 0 routes inside macros, 0 shapes outside the window.
Picture: [`layout/r1_top_f.png`](layout/r1_top_f.png) (run f3, about 100 kB).

### Connectivity

1. 172 signal nets routed: 99 by hand-drawn geometry, 73 by the maze router (`layout/maze_router_top.py`, grid
   origin (319.4, 330.0), pitch 0.8 µm, Metal2-Metal4). 75 maze jobs, 0 failed; 137 pin access stubs, 0 failed.
2. `r1_ctrl` 0.6 pins: all used except `bias_en` (no consumer in revision 2 of `r1_bias`; left open, recorded).
3. 64 safe taps: crossbar, Metal3 columns x = 1075.6 + 0.54 r, Metal4 rows y = 665.4 + 0.6 r (r = rank by ctrl pin y).
4. 36 ADC north pins to the `r1_ctrl` south pins (34 nets plus `OSC_CLK` and `POR_N` branches).
5. `VREF_B` (buffered, `r1_bias` revision 2): Metal5 2 µm at y 645 with Metal5 `VSS` shields at y 642 and 648, and a
   Metal4 riser at x 566 with a `VSS` shield at x 568. Loads: `r1_safe` vref, `r1_isense` vref, `r1_t2f` vref.
6. `VREF_BG` (raw bandgap): Metal5 1 µm at y 368, `VSS` shields at y 365.5 and 370.5, to the ADC `vref_in` and the
   bias `vref` only.
7. 11 bias currents, `POR_N` (bias → ctrl → ADC), AFE pairs (Metal5 0.5 µm), isense pairs, `az` pins tied to `az_win`.
8. `OSC_CLK`: osc → ctrl clk by a straight Metal3 line; branch to the ADC clk by the maze, 1057 µm (Metal2 25.6,
   Metal3 504.0, Metal4 527.2 µm, 8 vias). Skew ADC clk against ctrl clk: about 27 ps typ, 32 ps at max sheet
   (**estimated**, Elmore, 0.4 µm wire 232-272 Ω, assumed 0.2 fF/µm wire and 10 fF pin load; not extracted).
9. Unconnected macro pins: `r1_ctrl` `bias_en`; `r1_bgr` `iptat`, `vbe`, `dvbe` (test nodes); `r1_adc` 77 SAR-internal
   pins of layout A (`sar_*`, `top*`), which wait for the SAR logic of layout B.
10. 30 `sg13g2_antennanp` diodes at y 661 under the `r1_ctrl` `adc_raw_*` / `adc_valid_*` inputs (temporary, open issue 1).

### Supply network

Core ring, `r1_ctrl` TopMetal1 stripes, south Metal4 trunks, a Metal5 `VDDA` trunk (y 343-361) in parallel with the
Metal4 trunk, and a Metal4/Metal5 riser from pad 7. TopMetal2 only over MIM blocks (`tm1_over_mim_blocks`: none).
Report: [`reports/supply_f.md`](reports/supply_f.md) (square count, **estimated**; PDK process specification
Rev 1.2, EM section 2.15).

| Item | Result |
| --- | --- |
| Shared `r1_isense`–`r1_bgr` VSS resistance (limit ≤ 2.3 Ω) | passed: 1.657 Ω typ, 2.218 Ω at max sheet |
| Worst static drop VDDA | 35.75 mV at the far `r1_afe` pin (max sheet, 1.1 %) |
| Worst static drop VDD | 32.38 mV at `r1_ctrl` (ring from pad 1 and stripes, 2.7 %) |
| EM, top-level shapes | passed (all) |
| EM, macro supply pins | failed: `r1_adc` vdda/vdd/vss and `r1_afe` vdd/vss pins are 0.4 µm (limit 0.8 mA, current up to 1.94 mA) |

### Status

Run f3 is run f2 with two top-level fixes from the maximal deck (F13): the west `VDDA` Via3 row ends inside the
Metal3 riser, and the two wide `VSS` Metal3 bodies under `r1_bgr` and `r1_bias` have 2 µm gaps. The LVS reference
is unchanged. GDS (unfilled) `<G1_RESULTS_ROOT>/r1_top/asm-20261027-f3/r1_top.gds`, sha256
`c69abb8e19f16030d82ec06a752f8c6f10f7bddefcafa9d446075336ec6a50e8`. Filled chip (the deliverable)
`<G1_RESULTS_ROOT>/r1_top/asm-20261027-f3-fill/r1_top.gds`, sha256
`53f25a1975bba3af7ce60194452b03b6d72699f2f3a77aa5586bdc86462a8bf0`. LVS reference
`<G1_RESULTS_ROOT>/r1_top/asm-20261027-f3/cdl/r1_top.cdl`, sha256
`42c6a5de163f3fdd287bb161d6b13436a9afe162cf53ce2f1beb0150da0841b5`.

| Check | Unfilled `-f2` | Filled `-f3-fill` (of record) | Evidence |
| --- | --- | --- | --- |
| Generator self-check | passed (0 / 0 / 0 / 0 / 0) | — | `r1_top_assembly.json` |
| DRC main | failed, 1: `M2.b` inside `r1_afe_ch` (E3 macro defect, `r1_afe` README failure 3); top-level 0 (run `-f`: 9) | failed, 1: the same `r1_afe_ch` `M2.b`; top-level and fill 0 | `drc_main/` |
| DRC antenna | passed, 0 (run `-f`: 296) | passed, 0 | `drc_antenna/` |
| DRC maximal | not run on the unfilled GDS | passed, 0 (run `-f2-fill2`: 21, F13) | `drc_maximal/` |
| DRC density | not run on the unfilled GDS | passed, 0 (run `-f2-fill`: 1, `M2Fil.h`, F9; `-f2-fill2`: 0) | `drc_density/` |
| LVS, comparer-limit deck copy | passed: "Netlists match", 53 circuit pairs; `r1_top` 261 devices, 81 subcircuits | passed: "Netlists match", 53 pairs, `r1_top` 261 devices, 81 subcircuits (`-f2-fill2`: the same) | `lvs_limits/`, [`reports/runs/asm-20261027-f3-fill_lvs_report.txt`](reports/runs/asm-20261027-f3-fill_lvs_report.txt), [`reports/runs/asm-20261027-f2_lvs_report.txt`](reports/runs/asm-20261027-f2_lvs_report.txt) |
| LVS, stock PDK deck | not run (try e: the comparison crashes; no change expected) | not run | — |
| Bond map (24 openings) | — | passed, 24 of 24 openings matched, labels and sizes correct (`-f2-fill2`: the same) | `bondmap/` |
| Supply R, IR drop, EM | estimated by square count (run `-f3`): shared VSS passed; macro pin EM failed | — | `<G1_RESULTS_ROOT>/r1_top/asm-20261027-f3/supply_f.json`, `reports/supply_f.md` |
| `OSC_CLK` skew | estimated 27 ps typ (not extracted) | — | this section |
| Post-layout simulation of top-level nets | not run | not run | — |
| IHP intake pre-check | not run | not run | — |
| Run records | written | written | `reports/runs/asm-20261027-f.json`, `-f2.json`, `-f2-fill.json`, `-f2-fill2.json`, `-f3.json`, `-f3-fill.json` |

Fill (`flow/fill_top.sh`, thru `r1_ctrl_top:10,30,50,67;r1_safe:10`, distances Metal2 0.45, GatPoly gap 1.6,
Metal3-5 0.45 µm): geometry gate passed (only fill datatypes differ). Window coverage, 800 µm windows, 100 µm step:
minimum Metal1 26.41 %, Metal2 25.97 % (run `-f2-fill`: 23.87 %), Metal3 25.58 %, Metal4 27.94 %, Metal5 28.92 % (limit 25 %; all at the ADC corner (400, 400) or (500, 500)); global Metal1-Metal5 42.0 / 47.1 / 52.5 / 53.1 / 46.5 %. Margins are small: Metal3 0.58 %, Metal2 0.97 %. `flow/probe_window_minmax.py`, `<G1_RESULTS_ROOT>/r1_top/asm-20261027-f3-fill/window_density.json` (run `-f3-fill`; `-f2-fill2` the same within 0.01 %).

### Open issues (try f)

1. `r1_adc` layout A has no SAR logic. 77 SAR-internal pins are open and the 30 ADC outputs to `r1_ctrl` are not
   driven. The 30 antenna diodes are a temporary fix for the 296 antenna markers; remove them when layout B
   drives the pins. The chip is not functional until layout B.
2. Macro supply pins fail EM: `r1_adc` and `r1_afe` supply pins are 0.4 µm. Layout B and E4 must give pins ≥ 1 µm
   (`reports/integration_checklist_f.md`).
3. `r1_afe` E3 has 1 `M2.b` marker inside `r1_afe_ch`. Chip DRC main stays at 1 until E4.
4. The `r1_ctrl` return current shares the east `VSS` column and the south row with the isense ground. Estimated
   ground offset about 8 mV between the isense and the bgr (not simulated).
5. `r1_safe` is open to Metal2 fill (F9). Its effect on the safe comparators and string is not simulated.
6. `bias_en` is open; `az` pins are tied to `az_win`; `r1_t2f` vref is on `VREF_B` (INTERFACES T9), not on raw vref.
7. ADC-to-ctrl output timing window: open row in the interfaces (ctrl 0.6 SDC assumption).
8. No post-layout simulation of any top-level net; the `OSC_CLK` skew and all supply numbers are estimates.

### Failures and mistakes (try f)

| # | What happened | Class | Fix |
| --- | --- | --- | --- |
| F1 | The working-tree `r1_afe` and `r1_adc` at the start were work in progress (E4, layout B) without block LVS. | spec-ambiguity | Used the committed records (E3, layout A); snapshots in `inputs/` |
| F2 | The brief says raw vref to the ADC and t2f only; INTERFACES T9 puts t2f on `VREF_B`. | spec-ambiguity | Followed INTERFACES T9; recorded |
| F3 | Dev runs: isense lines and the `VREF_B` Metal5 ran inside the `r1_ctrl` box (self-check). | functional-bug | Isense rows at y 667-670; `VREF_B` isense branch at y 645 over `r1_safe` |
| F4 | Dev run: Metal3 VDD/VSS short between the IO-filler strap at x 537 and the bias VSS riser. | functional-bug | Riser ends at x 534 |
| F5 | Run `-f`: DRC main 7 notches (`M2.b`, `M3.b`) between 0.3 µm access stubs and 0.4 µm pins (same lesson as `r1_adc` failure 14). | regression | 0.4 µm stubs and jogs outside the macro outline |
| F6 | Run `-f`: `M3.f` in `r1_bias`: the wide top-level riser made the bias VSS bar a wide shape. | functional-bug | Riser joins the bar by six 6 µm fingers |
| F7 | Run `-f`: antenna 296 (`Ant.b`, Metal3-TopMetal2) at the `r1_ctrl` inputs from the ADC: layout A has no drivers. | verification-gap | 30 `sg13g2_antennanp` diodes (run `-f2`: 0) |
| F8 | Generator crashes during development (`path` overwritten by a loop variable, `DBox.contains` with a box, `ADC_NET` used before definition, a TopVia1 box too small). | tooling | Fixed in the generator |
| F9 | Run `-f2-fill`: density 1, `M2Fil.h` window (400, 400)-(1200, 1200) at 23.87 % (minimum 25 %); the real ADC box gets no fill. | estimation | `r1_safe` opened to Metal2 fill (its README defers density to chip fill); ADC not opened (CDAC) |
| F10 | `flow/drc_summary.py` labels the `r1_afe_ch` item as "top-level". | tooling | Cell read from the database by hand; recorded |
| F11 | `flow/write_run_json.py` failed on try f (no placeholder pins). | tooling | Key made optional; maze and diode keys added |
| F12 | The `-f2-fill` check chain was stopped by the track after density to start `-fill2`; its main step ended without a summary. | process-hygiene | Recorded in its `checks_steps.log`; `-fill2` repeats all checks |
| F13 | Run `-f2-fill2`: DRC maximal 21. 19 `V3.c1`: the west `VDDA` Via3 array box went to y 738.4, the Metal3 riser ends at y 738.0 (one via row outside the metal; the main deck does not check it). 2 `Slt.c.M3`: the `VSS` Metal3 bodies under `r1_bgr` (90 × 44 µm) and `r1_bias` (84 × 41 µm) are wider than 30 µm without a slit. The maximal deck was not run on the unfilled `-f2`. | verification-gap | Via box to y 738.0; bodies split in bars ≤ 24 µm by 2 µm gaps above y 342 (run `-f3`); maximal now runs first on the filled chip |

### Built against (try f)

| Item | Version | How established |
| --- | --- | --- |
| PDK | IHP-Open-PDK `84374023ee8b4b126bebbba67fcbada0a9c0ff0b` | checked by `flow/run.sh` |
| KLayout | 0.30.9 | container, DRC and LVS logs |
| Container | `tapeoutbench-eda:latest`, `sha256:ddeb6957…` | `flow/run.sh` |
| ngspice / xschem / LibreLane / CACE | not used by this try | — |

### Reproduce try f (repository root, POSIX shell)

1. Set the environment: `G1_CPUSET=116-119; export G1_CPUSET; G1_RESULTS_ROOT=<results root>; export G1_RESULTS_ROOT; G1_WORKDIR=.; export G1_WORKDIR`.
2. Copy the GDS and CDL of record of `r1_afe`, `r1_adc`, `r1_isense` and `r1_bias` from git into
   `<G1_RESULTS_ROOT>/r1_top/<run>/inputs/ofrecord/`. The scripts check the hashes.
3. Run `sh designs/r1-joint/blocks/r1_top/flow/run_try_f.sh <run> gen cdl` (add `main antenna lvs maximal` for the unfilled checks).
4. Run `sh designs/r1-joint/blocks/r1_top/flow/fill_top.sh <run dir> <run dir>-fill 0 "r1_ctrl_top:10,30,50,67;r1_safe:10" 0.45 1.6 0.45`.
5. Run `sh designs/r1-joint/blocks/r1_top/flow/run_fill_checks.sh <run dir> <run dir>-fill`.
6. Run `python3 designs/r1-joint/blocks/r1_top/flow/supply_f.py <run dir>/supply_f.json`.
7. Write the records with `flow/write_run_json.py` and `flow/write_fill_run_json.py`, and the placement with
   `flow/write_placement_e.py`.

New files of try f: `layout/r1_top_assemble_f.py`, `layout/maze_router_top.py`, `lvs/make_top_cdl_f.py`,
`flow/run_try_f.sh`, `flow/supply_f.py`, `reports/supply_f.md`, `reports/integration_checklist_f.md`,
`reports/placement_f.csv`, `layout/r1_top_f.png`; changed: `flow/write_run_json.py`.

## Full-chip testbench, schematic level (track T10, 2026-10-26)

Method, coverage, MODEL parts and the swap to post-layout netlists: [`tb/README.md`](tb/README.md). One deck per
test on the schematic netlists of record, with the r1_ctrl 0.5 RTL in an XSPICE `d_cosim` instance (G1 method).
Raw data: `<G1_RESULTS_ROOT>/r1_top/tb/<run-id>/`. Summaries: `tb/results/<run-id>.json`. Every result uses the
ideal VREF buffer model M6 (D20: `r1_bias` revision 2 output `vref_b`, not yet designed). Second-budget decks use
the fast view (`tb/README.md` section 12): `r1_bgr`, `r1_bias` and the POR as recorded behaviour, everything else real.

| Test | Status | Evidence |
| --- | --- | --- |
| 1 Power-up (ramps, `por_n`, bandgap and bias settle, oscillator at code 22, reset exit, `ID` over SPI) | 1a **passed** (real `r1_bgr` + `r1_bias` rev 1d/POR + loads, 10 µs ramps: VREF 1.0449 V settled 1.9 µs after VDDA, all 11 bias outputs 10.14 / 5.07 µA within 0.02 % of the record, settled by 11.2 µs, `por_n` held low to 40 µs; deck 13 s). Oscillator part **passed** against the schematic record: 32.72 MHz at code 22 (record 32.69 MHz); the D13 band 28-32 MHz is not applicable at schematic level (post-layout record 30.30 MHz); deck 317 s. POR release not simulated: 197-247 µs (`r1_bias` record). 1b **passed** with ctrl RTL 0.7 (run `t10-t1b-sub-07-a`: frozen copy of fdf0fcc0a, otherwise the same subset deck as `t10-t1b-sub-a`, M6, deck 367 s): reset exit 1.041 µs; `ID` 0x5207; `FAULT` 0x1800 (POR and CAL set, STO bit 8 clear), so finding R3 is closed at chip level. With ctrl 0.5, 1b failed on one criterion (run `t10-t1b-sub-a`: subset F18, fast view, M6, `reltol=1e-4`, `por_n` step at 1.0 µs, 13 µs, deck 717 s): reset exit passed (1.041 µs, limit `por_n` + 0.17 µs); `ID` passed (0x5205); `FAULT` has POR and CAL set (passed) but reads 0x1900, not the reset value 0x1800 (failed: finding R3, STO latched at reset exit). The 0.7 `u_sen` reset value 1 removes it (run above). The same subset deck with the real `r1_vbuf` (`t10-t1b-sub-vb-b`, deck 363 s) gives the same result on every criterion: `vref_l` mean 1.04497 V against `vref_bg` 1.04490 V (+0.07 mV), ripple 1.04447-1.04549 V; T2F output mean 0.5889 V against 0.5885 V with M6. The full fast-view deck `t10-t1b-fast-b` (8 µs, deck 5516 s) gave the same reset exit and `ID`; its `tstop` was too short for the `FAULT` read (F17). First-budget full-chip ramp `t10-t1-sch-a` failed (simulator abort) | `tb/results/t10-t1a-dc-a.json`, `tb/results/t10-t1a-osc-a.json`, `tb/results/t10-t1b-sub-07-a.json`, `tb/results/t10-t1b-sub-a.json`, `tb/results/t10-t1b-sub-vb-b.json`, `tb/results/t10-t1b-fast-b.json` |
| 2 Encoder path (10 kHz, pads → AFE → ADC → weights → CORDIC; SPI `POS`; one BiSS-C frame with CRC) | **passed**, all 11 criteria, with ctrl RTL 0.7 (run `t10-t2-fast-07-k`: encoder subset, T2F stub, fast view, D11, M6, fixes F22-F24, `tmax` 4.5 ns, 1 thread, deck 4088 s; master `CAL_CRC` shadow for the 0.7 reset values and `CTRL.CLR` after the lock wait, `tb/README.md` 15.4): MEAS residual 0.046°; `POS` 0.39°; `STATUS` 0x0150 (FAULT clear); BiSS-C CRC correct; nE = 1, nW = 1; ST −0.43°. The nW = 0 of the fourth budget had two causes: STO latched at reset (R3, fixed in ctrl 0.7) and no `CTRL.CLR` in the test sequence, so POR stayed latched (testbench). Fourth-budget record with ctrl 0.5: run `t10-t2-fast-h` (fast view, D11, M6, fixes F22-F24; encoder subset: `r1_isense`, `r1_safe` and the held-off `r1_t2f` as stubs, pads/AFE/ADC/ctrl real; reads after a 16 µs wait for the tracking-loop lock; `tmax` 4 ns; 38 µs, 3 threads, deck 1922 s): no lost event (50 conversions, all strobes); MEAS residual 0.045° el max, 0.024° rms over 46 pairs (limit 0.25°): passed; `POS` over SPI −0.50° / −0.19° (limit 0.64°): passed; `MEAS_ANGLE` over SPI equals a pair value: passed; `STATUS` 0x01D0 (POS_VALID, CAL_VALID, no AMP flag): passed; BiSS-C frame ACK, start, stop, CRC 0x02 equal to the computed CRC: passed; ST −0.42° (limit 0.64°): passed; nE = 1 passed, nW = 0 failed (FAULT set from reset, R3). Stage separation (`tb/enc_stage_check.py`): AFE angle 0.02° rms, ADC code error ≤ 8 LSB, ctrl codes = raw codes, CORDIC ≤ 0.01°. Acquisition: the tracking loop starts at velocity 0; at the reset gains (`POS_CFG` 0x164) `POS` error is −19.9° at 6.6 µs and POS_VALID is not set before about 21 µs after the reset (`t10-t2-fast-f`, reads at 6.6 / 9.8 µs fail; the specification gives no acquisition time). Aborted decks: `t10-t2-fast-e` (T2F HBT, 14.9 µs), `t10-t2-fast-g` (fast-view POR source, 11.9 µs, `tmax` 5 ns) | `tb/results/t10-t2-fast-07-k.json`, `tb/results/t10-t2-fast-h.json`, `tb/results/t10-t2-fast-h.stages.json`, `tb/results/t10-t2-fast-f.json`, `tb/results/t10-t2-fast-e.json` |
| 3 Current path (shunt levels at the PWM centre strobe; `I_A`/`I_B` within 1 %) | **passed** (run `t10-t3-sub-b`: fast view, D11, M6, fixes F22-F24; current subset: `r1_afe`, `r1_safe` and the held-off `r1_t2f` as stubs, shunts/isense/ADC/ctrl real; `tmax` 4 ns; 19.6 µs, 3 threads, deck 941 s): master `DONE` at 19.40 µs; 19 conversions, no lost event; strobe position 0.596-0.600 ns. Words: `I_A` 820 → 1740 (30 mV), `I_B` 821 → 3274 (80 mV). Steps against 14 × ΔV / LSB with the `r1_adc` revision-5 record LSB (457.0 µV): A +0.11 %, B +0.10 % (limit 1 %): passed. Expected words at the measured isense outputs (gain 14.01): level 0 822.1, level 1 A 1740.7, B 3271.4. The third-budget +2.37 % was the revision-3 LSB constant in `post_tb.py` (B step +2.6 % against it in this deck), not the ADC gain: the decks use the schematic ADC (gain 0.998 against its record line); the post-layout gain 1.058 (D16 amendment) is not in these decks (`tb/README.md` 14.1). Full-chip deck (all blocks real) `t10-t3-full-07-a` (ctrl 0.7, `--nodcp --por-fixed`, `tmax` 4 ns, 3 threads): master `DONE` at 19.401 µs, then stopped by the 3 h runner limit at 19.574 of 19.6 µs (no waveform file); words from the log: `I_A` 821 → 1740 (+0.00 %), `I_B` 823 → 3272 (−0.07 %): **passed** (`tb/results/t10-t3-full-07-a.logeval.json`; strobe position not run). Full fast view, earlier: `t10-t3-fast-e` / `-f` aborted at 14.06 µs (T2F HBT; `SIN_P` pad diode) after the level-0 reads 821 / 823; `t10-t3-sub-c` (`tmax` 3 ns) aborted at 17.18 µs (`ISA_P` pad diode); the same deck with the `dpantenna` pad diodes removed (`t10-t3-sub-d`, `--nodcp`) **passed** (A +0.11 %, B +0.10 %). With ctrl RTL 0.7 (`t10-t3-sub-07-a`: as `-b`, ctrl 0.7, `cur_trk` from the ctrl port, 2 threads, deck 1091 s): **passed**, A +0.11 %, B +0.10 %, 19 conversions, no lost event; `cur_trk` high 0.70 µs before each PWM-centre strobe (period 2.133 µs) | `tb/results/t10-t3-full-07-a.logeval.json`, `tb/results/t10-t3-sub-07-a.json`, `tb/results/t10-t3-sub-d.json`, `tb/results/t10-t3-sub-b.json`, `tb/results/t10-t3-fast-e.json`, `tb/results/t10-t3-fast-d.json` |
| 4 Safety (OC step → `FAULT_N` and gates low; EN low → gates low; clear sequences) | **passed**, all 10 criteria (run `t10-t4-safe-b`: safety subset, isense/safe/gate real, AFE and ADC stubs; fast view, D11, M6, THR_NEG fix F20; `tstop` 40.5 µs, 2 threads, deck 5980 s; master `DONE` at 39.6 µs). OC step (30 → 100 mV on ISA, threshold 69.8 mV): `FAULT_N` low after 166 ns, all gates < 1 V after 278 ns (limit 1369 ns); cause OC_A; after `CLR` PWM on `GATE_A` again. EN low: gates < 1 V after 85 ns (limit 1 µs); `FAULT` = 0x0100 (STO). After EN high and `CLR`: PWM on `GATE_A` again (the F21 criterion, now run). Same deck with the real `r1_vbuf` (D20, `r1_bias` revision 2) instead of M6 (`t10-t4-safe-vb-a`, 1 thread, deck 8360 s): all 10 criteria **passed**, every delay equal to M6 within 0.01 ps; `vref_l` +0.05 mV mean, two 23 mV dips of 23 ns at the `CMP_THR` writes (`tb/README.md` 13.4). Earlier runs: `t10-t4-safe-a` (8 passed, 1 not run, F21), `t10-t4-fast-b` (gates never on, F20, finding R4) | `tb/results/t10-t4-safe-b.json`, `tb/results/t10-t4-safe-vb-a.json`, `tb/results/t10-t4-safe-a.json`, `tb/results/t10-t4-fast-b.json` |
| 5 Thermal (T2F count at 27 °C and 125 °C) | 27 °C **passed** (run `t10-t5-sub-27-a`, thermal subset F18, fast view, M6, `reltol=1e-4`, 25 µs, deck 650 s): `TEMP` = 14, expected 13.86 ± 1 (f_T2F × 2^8 / f_clk); f_T2F 1.624 MHz, +1.49 % against the T2F record 1.6003 MHz (limit 3 %). 125 °C **passed** (run `t10-t5-sub-125-a`, deck 716 s): `TEMP` = 18, expected 18.22 ± 1; f_T2F 2.135 MHz, +1.17 % against the record 2.1100 MHz. With the real `r1_vbuf` instead of M6 (`t10-t5-sub-27-vb-c`, deck 358 s): **passed**, `TEMP` = 14, f_T2F +1.478 % (−0.007 % against M6); 125 °C (`t10-t5-sub-125-vb-a`, deck 388 s) **passed**, `TEMP` = 18, f_T2F +1.156 % (−0.009 %). The full fast view cannot run this test: the T2F HBT aborts at `reltol=2e-3` (F18) | `tb/runs/t10-t5-sub-27-a/run.json`, `tb/results/t10-t5-sub-27-a.json`, `tb/results/t10-t5-sub-125-a.json`, `tb/results/t10-t5-sub-27-vb-c.json`, `tb/results/t10-t5-sub-125-vb-a.json` |
| 6 Oscillator trim count (`OSC_COUNT` against the simulated frequency) | **passed** (run `t10-t6-sub-a`: thermal subset F18 with the transistor-level `r1_osc`, fast view, M6, `reltol=1e-4`, 12.5 µs, deck 1939 s): `OSC_COUNT` = 53, expected 52.33 ± 1.5 (16 f_osc / f_ref, f_ref 10 MHz); `r1_osc` at code 22: 32.71 MHz (schematic record 32.69 MHz ± 2 %); `STATUS.OSC_DONE` set (0x0580) | `tb/runs/t10-t6-sub-a/run.json`, `tb/results/t10-t6-sub-a.json` |
| Post-layout rerun (`--view pex`) | not run (no `views/pex.inc`; ADC layout does not exist) | — |

Finding R1 (functional bug, chip level): no block of record buffers `vref_bg`. The `r1_bgr` output (about 180 kΩ
source) is loaded by the `r1_safe` string and the `r1_isense` pedestals to 0.22 V instead of 1.045 V (runs
`t10-diag-nodeset-b`, `t10-diag-m6-a`). The decks use an ideal buffer model (M6 in `tb/README.md`) until a VREF
buffer exists. All results above are with M6.

Finding R2 (testbench bug, fixed): in deck 2 both ADC slices returned the constant code 2063. The cause is the
testbench sequencer model M1: its strobes reached the ADC 0.54 ns after the clk30 edge (`tb/README.md` section 10).
The fix is in `tb/rtl/r1_chip_dig.v` and is confirmed on the first conversion (run `t10-diag-t2enc-b`); deck 2
runs again with it (run `t10-t2-fast-a`, fast view).

Finding R3 (functional bug, `r1_ctrl` RTL 0.5): after reset, `FAULT` reads 0x1900, not the register-map reset value
0x1800, with `EN_STO_IN` high the whole time (run `t10-t1b-sub-a`). Bit 8 (STO) is latched. Cause (from the RTL):
the EN synchroniser `u_sen` in `r1_safe.v` uses `r1_sync2` with the default `RST_VAL = 0`. For two ticks after the
reset release `en_s` = 0, and the fault latch takes `~en_s` as a cause. The host must write `CLR` once after
power-up. Next step (owner `r1_ctrl`): `RST_VAL(1)` on `u_sen`, or document 0x1900 as the reset value. The
combinational gate-off path from the EN pad does not use `en_s`, so `RST_VAL = 1` does not weaken STO. Closed: ctrl RTL 0.7
(fdf0fcc0a) uses `RST_VAL(1)`; run `t10-t1b-sub-07-a` reads `FAULT` 0x1800.

Finding R4 (specification, `r1_ctrl` register map): the reset value of `CMP_THR_A/B` (0x3F3F) makes both NEG
comparators active at zero current (NEG cell code c = 63 − THR_NEG = 0, threshold −VREF; `cmp_neg_a/b` = 1.2 V in
decks 3 and 4). FAULT bits 1 and 3 latch at every reset exit and `CLR` cannot clear them, even when masked, until
the host writes NEG thresholds. Next step (owner `r1_ctrl`): reset THR_NEG 0, or document the reset behaviour. Fixed in
ctrl RTL 0.7 (reset 0x003F); the chip-level check of the NEG flags at reset is not run. The testbench `CAL_CRC` shadow follows it under `T10_CTRL07` (`tb/README.md` 15.4).

## Try e (2026-10-21): floorplan C4 on the 1700 µm ring — run of record `asm-20261021-e4`

Try e builds `r1_top` on the 1700 µm ring of record (`r1_padring` revision d, GDS `81bba04b…`) with floorplan C4
of S7. Every macro that exists today is placed. Only `r1_adc` is a placeholder. The generator is
`layout/r1_top_assemble_e.py`. The try-d files below this section stay as the record of try d.

### What try e contains

1. Ring of record, 1700 × 1700 µm, pitch 142 µm (4141 fill instances removed; 22 pad labels copied to the top).
2. Real macros: `r1_ctrl_top` 0.4 (t7), `r1_afe` revision E (d17d505f7), `r1_isense` layout a (db5461161),
   `r1_osc` revision 2 layout r2d (679a97320), `r1_bias` (934b90195), `r1_safe`, `r1_bgr`, `r1_t2f` (MY),
   `r1_gate_lv`, 6 × `r1_ls`, 34 × `sg13g2_decap_8`, 1 × `sg13g2_tiehi` (`u_tie_osc`).
3. Placeholder: `r1_adc_ph`, S7 hard slot 439.0 × 182.3 µm at (592.0, 376.0), 51 Metal3 pin stubs.
4. Supplies per S7: core ring (outer `VSS`, inner `VDD`), `r1_ctrl` stripes, north and south straps, south
   Metal4 trunks (`VSS`, `VDD`, `VDDA`), `VDDA` feed from pad 7, west `VDDA` riser.
5. MIM rule: TopMetal2 only over MIM blocks. In C4 only `r1_afe` is under a ring column. The west TopMetal1
   columns are cut for y 735–1239.4 and replaced by TopMetal2 (y 720–1254.4); TopVia2 only in the 15 µm overlaps.
   `r1_isense`, `r1_osc` and the ADC slot are not under the ring.
6. 46 routed signal nets (try d: 20). List: [`reports/connectivity_e.md`](reports/connectivity_e.md).

Placement with the S7 C4 deltas: [`reports/placement_e.csv`](reports/placement_e.csv). Drop-in requirements:
[`reports/integration_checklist_e.md`](reports/integration_checklist_e.md). Picture:
[`layout/r1_top_e.png`](layout/r1_top_e.png) (run e4, 96 kB).

### Position deltas against S7 C4

| Item | S7 C4 | Try e | Delta | Reason |
| --- | --- | --- | --- | --- |
| Pad centres (all sides) | 500, 640, 780, 920, 1060, 1200 | 495, 637, 779, 921, 1063, 1205 | −5, −3, −1, +1, +3, +5 | ring of record, pitch 142 µm (S7 assumed 140) |
| `r1_afe` | (336.0, 720.0) | (336.0, 740.0) | +20.0 y | `sinp`, `cosp` inside the pad 21 / 23 `pad` windows: straight 15 µm lines (S7: 36 µm) |
| `r1_ctrl_top` | (543.8, 673.3) | (543.8, 673.0) | −0.3 y | top edge 0.3 µm under the inner north TopMetal2 row (as try d) |
| `r1_bias` (real, 120 × 165.94) | bias slot (442.0, 488.6), 86.8 × 69.7; POR slot (345, 1270) | (444.0, 488.6) | +2.0 x; POR slot dropped (POR is inside `r1_bias`) | layout larger than the slot; 10 µm from `r1_bgr` |
| `r1_t2f` (MY) | (442.0, 376.0) | (444.0, 376.0) | +2.0 x | aligned with `r1_bias` |
| ADC slot | (556.0, 376.0) | (592.0, 376.0) | +36.0 x | the wider `r1_bias` and its east supply risers |
| `VDDA` decap of C4 | (849.4, 376) | not placed | — | the 439 µm ADC slot takes the place |
| `r1_gate_lv` | (440.0, 1300.0) | (440.0, 1296.0) | −4.0 y | try-d relation to the north ring row |
| `r1_isense`, `r1_osc`, `r1_safe`, `r1_bgr` | C4 | C4 | 0 | — |

Pad route lengths: `SIN_P`, `COS_P` 15 µm; `SIN_N` 153, `COS_N` 157 µm; `ISA_N`, `ISB_P` 132 µm; `ISA_P` 272,
`ISB_N` 270 µm (Manhattan).

### Status (run `asm-20261021-e4`)

GDS `<G1_RESULTS_ROOT>/r1_top/asm-20261021-e4/r1_top.gds`, SHA-256 `67d5148ef70d5d413925072c75386045ccaa6077c27121dde076d7de84d9378e`.
LVS reference `<G1_RESULTS_ROOT>/r1_top/asm-20261021-e4/cdl/r1_top.cdl`, SHA-256 `6d117ccaaf3bbe5aa9534c06f5c8d5b8df1407d2cfb975cd58806f617687fc95`.
LVS pair report: `reports/runs/asm-20261021-e4_lvs_report.txt`.

| Check | Result | Evidence |
| --- | --- | --- |
| Generator self-check (net spacing, overlaps, pairs < 10 µm, outside window, routes inside macros) | passed (0 / 0 / 0 / 0 / 0) | `<G1_RESULTS_ROOT>/r1_top/asm-20261021-e4/r1_top_assembly.json` |
| KLayout DRC main (deep, no density, `--disable_extra_rules`) | passed, 0 markers (run `-e3`: 34 `*_drw_Offgrid`, fixed, E9) | `<G1_RESULTS_ROOT>/r1_top/asm-20261021-e4/drc_main/` |
| KLayout DRC maximal | passed, 0 markers | `<G1_RESULTS_ROOT>/r1_top/asm-20261021-e4/drc_maximal/` |
| KLayout antenna | passed, 0 (runs `-e`, `-e2`: 8, fixed, E7) | `<G1_RESULTS_ROOT>/r1_top/asm-20261021-e4/drc_antenna/` |
| KLayout density | failed, 53 markers, all class (b): no fill, empty ADC slot | `<G1_RESULTS_ROOT>/r1_top/asm-20261021-e4/drc_density/` |
| LVS, deck copy with comparer limits | passed: "Netlists match"; all 52 circuit pairs match; `r1_top` 261 devices, 50 subcircuits | `<G1_RESULTS_ROOT>/r1_top/asm-20261021-e4/lvs_limits/` (`report.txt`) |
| LVS, stock PDK deck | failed: crash in the comparison (exit 11) after extraction; no comparison result. The wrapper prints "Status PASS"; that line is wrong and is not used (as try d) | `<G1_RESULTS_ROOT>/r1_top/asm-20261021-e4/lvs_stock/` |
| Run record | written | `reports/runs/asm-20261021-e4.json` (and `-e`, `-e2`, `-e3`, superseded) |
| Chip fill | see "Try e fill" below (run `-fill3`: density 2 markers, ADC window) | `<G1_RESULTS_ROOT>/r1_top/asm-20261021-e4-fill3/` |
| IR drop and EM of ring and trunks | not run (ring resistance estimated by square count only) | `reports/connectivity_e.md` |
| Post-layout simulation of any top-level net | not run | — |
| Bond plan on the chip GDS | passed on the filled GDS 24/24, see "Try e fill" (unfilled e4: not run) | `<G1_RESULTS_ROOT>/r1_top/asm-20261021-e4-fill3/bondmap/` |
| IHP intake pre-check | not run (chip not complete) | — |
| Drop-in probe of the in-progress `r1_afe` E2, `r1_isense` b | not run (tracks still running; the checklist states the requirements instead) | — |

DRC classes as try d: (a) violation in the assembled parts; (b) placeholder or empty-region density (no fill).

| Deck | Rule | Count | Class (a) | Class (b) |
| --- | --- | --- | --- | --- |
| main | all | 0 | 0 | 0 |
| maximal | all | 0 | 0 | 0 |
| antenna | all | 0 | 0 | 0 (runs `-e`, `-e2`: `Ant.e_TopMetal1` 4 + `Ant.e_TopMetal2` 4, class a, fixed, E7) |
| density | `M2Fil.h` | 16 | 0 | 16 |
| density | `M1Fil.h`, `M4Fil.h` | 7 + 7 | 0 | 14 |
| density | `AFil.g2`, `M5Fil.h` | 6 + 6 | 0 | 12 |
| density | `M3Fil.h` | 4 | 0 | 4 |
| density | `AFil.g`, `GFil.g`, `M1.j`…`M5.j` | 7 × 1 | 0 | 7 |
| **all** | | **53** | **0** | **53** |

Density cause: 800 × 800 µm window coverage and global density below the minimum, because no fill is inserted and
the ADC slot is empty (try d: 35 on the 1600 µm die).

### LVS: what is checked and what is not

The reference is `lvs/make_top_cdl_e.py`: `r1_ctrl_top` 0.4 netlist, the block CDLs of record (hash-checked),
the ring (flat projected reference), decaps and the tie cell. The ADC placeholder is an empty subcircuit; the deck
drops it on both sides. Layout `r1_top` has 147 nets and the reference 362: the reference counts every floating pin net of the unconnected macro pins; they have no layout counterpart and cause no mismatch. Not checked by this comparison:

1. The 51 ADC placeholder pins (floating on both sides).
2. Unconnected macro pins (floating on both sides): `r1_ctrl` 99 (ADC bus 36, `thr_*`/`cal_*` 48 (the
   0.4 safe-threshold words), `ana_ctrl`, `az_win`), `r1_safe` 68 (64 tap inputs, 4 outputs), `r1_afe` 9, `r1_isense` 9, `r1_bgr` 3
   (`iptat`, `vbe`, `dvbe`), `r1_t2f` 2 (`en`, `mode`), `r1_bias` 1 (`ib_adc_ref`), `r1_gate_lv` 1 (`vdda`), and all
   pins except `vss` of the 6 `r1_ls`.
3. The comparison uses the comparer-limit deck copy (`max_depth(8)`, `max_branch_complexity(100)` after `align`,
   no extraction change; `deck_diff.txt` in the run). The stock-deck state is in the table.
4. Block-internal correctness is from the block LVS runs, not from this run (the macros are compared as cells).

### Open issues (try e)

1. `r1_adc` does not exist: 36 digital, 9 analog, `ib_adc_ref`, `vref_in` and supplies are pending (checklist).
2. ctrl 0.4 has no safe tap outputs, `pga_c`, `t2f_en/mode`, `az*`, ADC clock or `osc_en`. ctrl 0.6 template:
   checklist. `OSC_EN` is held by a tie cell until then.
3. `POR_N` runs about 1 330 µm (bias east pin → ctrl north pin, around the AFE). ctrl 0.6 should put `por_n` on
   the south edge (local x 23.7): 146 µm.
4. `VREF_BG` and the 13 bias lines are not shielded. Coupling and the bandgap load (t2f, safe, isense, later the
   ADC) are not simulated.
5. The C4 `VDDA` decap is not placed (ADC slot). The `VDDA` decoupling is open.
6. `u_ls_t2f0/1` at x 545 sit under the bias-output path region; they are not connected. A t2f level-shift place
   is open with ctrl 0.6 (`t2f_en`, `mode`).
7. The north IO-row rail heights (y 1381–1399) are the try-d values + 100 µm, not probed separately; DRC is clean.
8. `r1_gate_lv` `vdda` is not connected (as try d).

### Failures and mistakes (try e)

| # | What happened | Class | Fix |
| --- | --- | --- | --- |
| E1 | The brief named the working-tree files of `r1_afe`, `r1_isense`, `r1_osc`. At the start they were revisions in progress, without block LVS. | spec-ambiguity | Used the committed layouts of record (GDS and CDL agree, block LVS passed); snapshots kept in the run `inputs/` |
| E2 | `pin()` by edge chose large internal straps with the same label: 3 routes ended inside macros (dev run). | functional-bug | Smallest shape at the edge wins; self-check "routes inside macros" added (0) |
| E3 | `r1_t2f` pins asked on the east edge after the MY mirror. | functional-bug | West edge |
| E4 | The coordinator said ctrl 0.4 has no `por_n` port. The t7 GDS and CDL have it (north edge, local (482.9, 663.8)). | coordination | Routed `POR_N`; recorded here |
| E5 | `r1_bias` (120 × 165.94) is larger than the S7 slots; the ADC slot moves +36 µm east and the C4 `VDDA` decap drops out. | estimation | Placement table; open issue 5 |
| E6 | `r1_osc` revision 2 was committed during the run (run `-e` used layout k, `osc_clk` east, 360 µm detour). | coordination | Run `-e2` with revision 2 |
| E7 | Runs `-e` and `-e2`: antenna 8 (`Ant.e_TopMetal1/2`) on the four `r1_osc` `en` gates; `en` was tied straight to `VDD`, which carries the ring metal. Try d had an osc placeholder, so the tie was never checked. | verification-gap | `sg13g2_tiehi` drives `OSC_EN` (run `-e3`: antenna 0) |
| E8 | Run `-e2` clean-up deleted its finished `lvs_limits` directory; the result is lost. | process-hygiene | Recorded in `steps.log` and `run.json`; run `-e3` repeated LVS |
| E9 | Run `-e3`: DRC main 34 × `*_drw_Offgrid` at the tie-cell `L_HI` pad (centre y 1037.4625). | numerical | Pad centre rounded to 1037.46 (run `-e4`) |

### Built against (try e)

| Item | Version | How established |
| --- | --- | --- |
| PDK | IHP-Open-PDK `84374023ee8b4b126bebbba67fcbada0a9c0ff0b` | checked by `flow/run.sh` |
| KLayout | 0.30.9 | container, DRC and LVS logs |
| Container | `tapeoutbench-eda:latest`, id `sha256:ddeb6957…` | `flow/run.sh` |
| ngspice / xschem / LibreLane / CACE | not used | — |
| Ring | `r1_padring` revision d GDS `81bba04b…` | hash checked by the generator |
| `r1_ctrl_top` | 0.4, run `r1ctrl_ll_20261021_t7`, GDS `d52e67e8…` | hash in `run.json` |
| `r1_afe` | revision E, GDS `0181e988…`, CDL `0cfb1980…` | `EXPECT_SHA` (generator) and `EXPECT` (CDL builder) |
| `r1_isense` | layout a, GDS `054373fc…`, CDL `b7923cbd…` | same |
| `r1_osc` | revision 2 (layout r2d), GDS `7c5fb60f…`, CDL `600d5f2b…` | same |
| `r1_bias` | GDS `354fa73c…`, CDL `37636bf6…` | same |
| Other blocks | as try d | `reports/placement_e.csv` |

### Reproduce try e (repository root, POSIX shell)

1. Copy the GDS, CDL and layout JSON of record of `r1_afe` (revision E) and `r1_isense` (layout a) from git into
   `<G1_RESULTS_ROOT>/r1_top/<run>/inputs/ofrecord/` (names `r1_afe.gds`, `r1_afe_lvs.cdl`, `r1_isense.gds`,
   `r1_isense_lvs.cdl`). The generator and the CDL builder check the hashes.
2. Set the environment:
   `G1_CPUSET=116-119; export G1_CPUSET; G1_RESULTS_ROOT=<results root>; export G1_RESULTS_ROOT; G1_WORKDIR=.; export G1_WORKDIR`.
3. Run `sh designs/r1-joint/blocks/r1_top/flow/run_try_e.sh asm-20261021-e4` (steps: gen cdl lvs main antenna
   density maximal stock; one KLayout job at a time).
4. Write the record: `python3 designs/r1-joint/blocks/r1_top/flow/write_run_json.py <run dir> <question> <disposition> run_try_e.sh`.
5. Write the placement table: `python3 designs/r1-joint/blocks/r1_top/flow/write_placement_e.py <run dir>/r1_top_assembly.json designs/r1-joint/blocks/r1_top/reports/placement_e.csv`.

New files of try e: `layout/r1_top_assemble_e.py`, `lvs/make_top_cdl_e.py`, `flow/run_try_e.sh`,
`flow/write_placement_e.py`, `flow/probe_ring_pins.py`, `flow/probe_pin_boxes.py`; changed: `layout/r1_top_png.py`
(die size argument), `flow/write_run_json.py` (driver argument, input snapshots, try-e self-check keys).


### Try e fill (track T8, 2026-10-26)

The chip fill of try e is done. Density has 2 markers left. Both markers are one 800 × 800 µm window, and the ADC
placeholder is the cause. The filled GDS is `<G1_RESULTS_ROOT>/r1_top/asm-20261021-e4-fill3/r1_top.gds`, SHA-256
`7c1dd00ec08e0d4dae5052e51019a6e7bb598de775eb841e4ba241416951d512`. Input: run `asm-20261021-e4` (GDS `67d5148e…`).
Run record: `reports/runs/asm-20261021-e4-fill3.json`. The name `asm-20261021-e4-fill` is the first, partial attempt of
this track (see "Reused"). It stays as a record and is not the result.

Method (`flow/fill_top.sh`):

1. `fill_top_pre.py` draws a temporary no-fill cell. It covers every macro and the ADC placeholder box (bbox + 1 µm),
   the 24 bond openings (+10 µm) and the pad ring. The ring is the whole die outside the sealring hole.
2. The unmodified PDK filler (`filler.py`, macros ActGatP, Metal, TopMetal) runs on a run-time copy of the macros.
   It fills the free area and keeps its own distance from routed metal.
3. `fill_top_fixj.py` removes the GatPoly filler rectangles that break rule `GFil.j` (2215 rectangles).
4. `fill_top_post.py` removes the temporary cell. It checks that only the datatype-22 fill layers differ from the input,
   that all texts and instances are kept and that no pattern cell is orphaned.

Changes to the PDK filler parameters (all inside the rule limits, no rule deck or model card changed): Metal2-Metal5
filler distance 0.45 µm (default 1.5 / 2.0; minimum 0.42 µm by `M2Fil.b`…`M5Fil.b`); GatPoly horizontal gap 1.6 µm
(default 5.0; minimum 0.8 µm by `GFil.c`). Cause: the default values give less than the 800 µm window minimum
(25 %, `M2Fil.h`…`M5Fil.h`) because the macros are sparse in M2-M4.
Exception to "no fill over macros": on `r1_ctrl_top` the chip filler may fill Metal2-Metal5 (option `thru`). The fill is
top-cell shapes. No macro cell is edited. The analog macros, the ADC box, the ring and the bond openings get no fill.

| Check | Result | Evidence |
| --- | --- | --- |
| Fill gate (only fill layers differ, texts/instances kept, no orphan) | passed | `reports/runs/asm-20261021-e4-fill3.json` |
| DRC main | passed, 0 markers | `<G1_RESULTS_ROOT>/r1_top/asm-20261021-e4-fill3/drc_main/` |
| DRC maximal | passed, 0 markers (2215 `GFil.j` removed by step 3) | `<G1_RESULTS_ROOT>/r1_top/asm-20261021-e4-fill3/drc_maximal/` |
| DRC antenna | passed, 0 | `<G1_RESULTS_ROOT>/r1_top/asm-20261021-e4-fill3/drc_antenna/` |
| DRC density | failed, 2 markers: `M2Fil.h`, `M5Fil.h`. Both are the window (400, 400)–(1200, 1200); both overlap the ADC box | `<G1_RESULTS_ROOT>/r1_top/asm-20261021-e4-fill3/drc_density/` (`markers.json`) |
| Density with the ADC box open to fill (what-if, not a deliverable) | passed, 0 markers | `<G1_RESULTS_ROOT>/r1_top/asm-20261021-e4-fill3-whatif-adc/drc_density/` |
| LVS, deck copy with comparer limits, on the filled GDS | passed: "Netlists match", 52 of 52 circuit pairs match, `r1_top` 261 devices, 50 subcircuits (as unfilled e4) | `reports/runs/asm-20261021-e4-fill3_lvs_report.txt` |
| LVS, stock PDK deck | not run (crashes on e4 already, exit 11) | — |
| Bond map on the chip GDS | passed: 24 of 24 openings matched, 22 labels, die 1700 µm, hash ok | `<G1_RESULTS_ROOT>/r1_top/asm-20261021-e4-fill3/bondmap/verify_bondmap_chip.json` |
| Post-fill parasitics, timing or simulation | not run | — |

Density markers that remain (class: ADC placeholder):

| Rule | Window (µm) | Window coverage | Minimum | Cause |
| --- | --- | --- | --- | --- |
| `M2Fil.h` | 400, 400, 1200, 1200 | 23.69 % | 25 % | 69 494 µm² of the ADC box in the window have no metal (no fill) |
| `M5Fil.h` | 400, 400, 1200, 1200 | 23.35 % | 25 % | same |

The what-if run opens the ADC box to the same filler. All density rules then pass. The ADC macro must bring fill of
at least about 15 % Metal2 and Metal5 coverage over the part of its 439 × 182 µm box inside the window (estimate) (what-if: Metal2 56.7 %). Window values from
the 100 µm-step scan: `reports/runs/asm-20261021-e4-fill3_window_density.json`.

Fill and density of the delivered GDS (counts from `fill_counts.json`; density from `flow/probe_window_minmax.py`,
100 µm step, drawn + filler; the deck reports violations only, it has no per-window numbers):

| Layer | Fill rectangles | Fill area (µm²) | Window min / max (%) | Global (%) |
| --- | --- | --- | --- | --- |
| Activ | 37 349 | 431 754 | not scanned | — |
| GatPoly | 53 235 | 372 645 | not scanned | — |
| Metal1 | 53 463 | 484 192 | 26.5 / 49.4 | 42.2 |
| Metal2 | 211 982 | 1 163 693 | 23.7 / 51.0 | 46.3 |
| Metal3 | 142 493 | 674 879 | 25.5 / 58.3 | 52.6 |
| Metal4 | 160 233 | 723 655 | 28.1 / 60.6 | 53.3 |
| Metal5 | 41 652 | 455 337 | 21.9 / 50.7 | 43.7 |
| TopMetal1 | 6 388 | 319 400 | not scanned | — |
| TopMetal2 | 7 759 | 387 950 | not scanned | — |

The minimum windows are in the ADC corner (400, 400), (500, 400). Metal5 shows 21.9 % on the scan grid; the deck
windows flag (400, 400) only.

Reused from the terminated attempt of 2026-10-21 (killed by an API limit): `fill_top_pre.py`, `fill_top_post.py`,
`fill_density_markers.py`, `run_fill_checks.sh`, `write_fill_run_json.py`, the ideas of `thru` and of the run-time
filler copy, and the density what-if. Its runs `asm-20261021-e4-fill`, `-attempt1`…`-attempt5`, `-whatif-adc` stay in
`<G1_RESULTS_ROOT>/r1_top/`. Its best result: density 4 markers, main 0, antenna 0; maximal had 2215 `GFil.j` (attempt 5). Changed
in this resume: `fill_top.sh` (Metal3-5 distance argument, `fill_top_fixj.py` step), `fill_top_fixj.py` (it had a
syntax error and never ran; repaired), new probes `probe_window_cov.py`, `probe_window_minmax.py`, `probe_gfilj.py`.

Reproduce (repository root, POSIX shell; one KLayout job at a time):

1. `G1_CPUSET=116-119; export G1_CPUSET; G1_RESULTS_ROOT=<results root>; export G1_RESULTS_ROOT; G1_WORKDIR=.; export G1_WORKDIR`
2. `sh designs/r1-joint/blocks/r1_top/flow/fill_top.sh $G1_RESULTS_ROOT/r1_top/asm-20261021-e4 $G1_RESULTS_ROOT/r1_top/asm-20261021-e4-fill3 0 "r1_ctrl_top:10,30,50,67" 0.45 1.6 0.45`
3. `sh designs/r1-joint/blocks/r1_top/flow/run_fill_checks.sh $G1_RESULTS_ROOT/r1_top/asm-20261021-e4 $G1_RESULTS_ROOT/r1_top/asm-20261021-e4-fill3`
4. What-if: same as step 2 with the `thru` argument `"r1_ctrl_top:10,30,50,67;r1_adc_ph:1,5,8,10,30,50,67,126,134"` into a new run directory.

Open issues (fill):

1. Two density markers (`M2Fil.h`, `M5Fil.h`) wait for the ADC macro and its own fill. Recheck when the ADC is placed.
2. The fill is floating metal at 0.45 µm spacing next to routed metal. Coupling to the bias and reference lines is not simulated.
3. The analog macros (`r1_afe`, `r1_isense`, `r1_osc`, `r1_bias`) have 1-8 % Metal2-Metal4 coverage inside their boxes. They carry the window minima. A fill inside them is a block decision.
4. The `thru` fill over `r1_ctrl_top` is a deviation from "no fill over macros". Confirm it with the owner of the ctrl hardening.
5. File size: filled GDS is 76 MB. IHP intake size limits are not checked.

Failures and mistakes (fill):

| # | What happened | Class | Fix |
| --- | --- | --- | --- |
| F1 | Default filler distances give 44 % coverage on free area and the macros are sparse. Windows stayed under 25 %. | estimation | Distances 0.45 µm (Metal2-5), gap 1.6 µm (GatPoly) |
| F2 | Narrow GatPoly gap leaves 2215 rectangles that break `GFil.j` (maximal deck). Earlier attempts ran main and density only. | verification-gap | Step `fill_top_fixj.py`; maximal deck added to the checks, 0 markers |
| F3 | `fill_top_fixj.py` of the earlier attempt was never run and had a syntax error. Three further faults followed: a Region copy call, zero-width marker boxes dropped, an orphan pattern cell. | functional-bug | Repaired in this resume; the post-step gate catches the orphan |
| F4 | The first re-run (`-fill2`, distance 0.6 µm) left 3 markers. I picked the distance by guess, without a coverage estimate. | planning | Window coverage probe, then 0.45 µm (`-fill3`); `-fill2` has no checks beyond density |
| F5 | The target name `asm-20261021-e4-fill` already held the earlier attempt. Run directories are not deleted. | process-hygiene | Result is `-fill3`; the name is explained above |
| F6 | `fill_density_markers.py` needs the container Python (`klayout` module). Host Python failed. | tooling | Run it with `flow/run.sh python3` |

## What it is (try d, 1600 µm)

`layout/r1_top_assemble.py` is a KLayout generator. It writes `r1_top.gds` (top cell `r1_top`, 1600 × 1600 µm).
It does these steps:

1. It reads the ring of record `r1_padring_1600.gds` (SHA-256 `40514b4f…`, revision b/c) and checks the hash.
2. It removes the 4198 fill instances from the ring top cell. The ring fill covers the core area. Chip fill comes later.
3. It copies the pad labels of the ring (22 × TopMetal2 pin text) into the top cell (see failure F1).
4. It places the finished macros: `r1_ctrl_top` (0.4, run `r1ctrl_ll_20261021_t7`), `r1_safe`, `r1_bgr`, `r1_t2f`,
   `r1_gate_lv` (one instance with three channels), and six `r1_ls`.
5. It draws placeholders for `r1_afe`, `r1_adc`, `r1_isense_a`, `r1_isense_b` and `r1_osc`. Each placeholder is a
   `prBoundary` outline with a text and Metal3 pin stubs with pin labels. The sizes are the S6 sizes.
6. It builds the supplies: core ring identity, `r1_ctrl` stripes, north and south straps, the south Metal4 trunks
   (`VSS`, `VDD`, `VDDA`) and the `VDDA` feed from pad 7.
7. It applies the coordinator MIM rule on the west ring columns (TopMetal2 only over the AFE).
8. It places 34 `sg13g2_decap_8` cells on `VDD` (antenna load, see failure F2).
9. It routes the 20 signal nets that exist today on Metal2–Metal4. The IO-row TopMetal is not touched inside the
   analog band (S6 cut C7).
10. It runs a self-check (different nets on one layer, with the PDK spacing) and an overlap check.

Placement: [`reports/placement.csv`](reports/placement.csv). Connectivity: [`reports/connectivity.md`](reports/connectivity.md).
Integration checklist for the pending macros: [`reports/integration_checklist.md`](reports/integration_checklist.md).
Picture: [`layout/r1_top.png`](layout/r1_top.png) (try d, 93 kB).

## State (2026-10-21, try d of record)

| Item | Value |
| --- | --- |
| GDS | `<G1_RESULTS_ROOT>/r1_top/asm-20261021-d/r1_top.gds`, SHA-256 `9cd93bb976eb264422c64472985de7fdf9447b537b04889d3b929852267cf508` |
| LVS reference | `<G1_RESULTS_ROOT>/r1_top/asm-20261021-d/cdl/r1_top.cdl`, SHA-256 `94f191a8542556acdbab68cb422f34c78a3cb77b2901f056741bd850974b53ae` |
| Run record | `<G1_RESULTS_ROOT>/r1_top/asm-20261021-d/run.json` (and `asm-20261021-a`, `-b`, `-c`, superseded) |
| Self-check | 0 net conflicts, 0 instance overlaps, 0 instances outside the IO row |

## Status

| Check | Result | Evidence |
| --- | --- | --- |
| Generator self-check (net spacing, overlaps) | passed (0 / 0 / 0) | `<G1_RESULTS_ROOT>/r1_top/asm-20261021-d/r1_top_assembly.json` |
| KLayout DRC main (deep, no density, `--disable_extra_rules`) | passed, 0 markers (try a: 0) | `<G1_RESULTS_ROOT>/r1_top/asm-20261021-d/drc_main/` |
| KLayout DRC maximal | passed, 0 markers (try a: 6 × `V3.c1`, fixed) | `<G1_RESULTS_ROOT>/r1_top/asm-20261021-d/drc_maximal/` |
| KLayout antenna | passed, 0 (try a: 12, fixed) | `<G1_RESULTS_ROOT>/r1_top/asm-20261021-d/drc_antenna/` |
| KLayout density | failed, 35 markers, all class (b): no fill yet | `<G1_RESULTS_ROOT>/r1_top/asm-20261021-d/drc_density/` |
| LVS, deck copy with comparer limits | passed: "Netlists match"; all 46 circuit pairs match; `r1_top` 261 devices, 45 subcircuits | `<G1_RESULTS_ROOT>/r1_top/asm-20261021-d/lvs_limits/` (`report.txt`) |
| LVS, stock PDK deck | failed: crash in the comparison (signal 11, exit 11) after extraction, 5 min; no comparison result. The wrapper summary prints "Status PASS"; that line is wrong and is not used. Same behaviour as `r1_safe` (T4). The comparer-limit copy is the LVS of record | `<G1_RESULTS_ROOT>/r1_top/asm-20261021-d/lvs_stock/` |
| Chip fill | see "Try e fill" below (run `-fill3`: density 2 markers, ADC window) | `<G1_RESULTS_ROOT>/r1_top/asm-20261021-e4-fill3/` |
| IR drop and EM of the trunks and ring | not run (ring resistance only estimated by square count) | `reports/connectivity.md` |
| Post-layout simulation of any top-level net | not run | — |
| Bond plan on the chip GDS | not run | — |
| IHP intake pre-check | not run (the chip is not complete) | — |

DRC classes. Class (a) is a violation in the assembled parts (macros, ring, routes). Class (b) comes from the
placeholders or from empty regions: density and fill-coverage rules, because no fill is inserted yet, and any
marker inside a placeholder outline. `flow/drc_summary.py` makes the split by rule name and marker position.

| Deck | Rule | Count | Class (a) | Class (b) | Cause |
| --- | --- | --- | --- | --- | --- |
| main | all | 0 | 0 | 0 | — |
| maximal | all | 0 | 0 | 0 | — (try a: `V3.c1` 6, class a, fixed in try d) |
| antenna | all | 0 | 0 | 0 | — (try a: `Ant.e_Metal5` 4, `Ant.e_TopMetal1` 4, `Ant.e_TopMetal2` 4, class a, fixed in try b) |
| density | `M2Fil.h` | 9 | 0 | 9 | 800 × 800 µm window coverage < 25 %: no fill, empty placeholders |
| density | `M4Fil.h`, `M5Fil.h` | 5 + 5 | 0 | 10 | same |
| density | `M1Fil.h`, `M3Fil.h` | 3 + 3 | 0 | 6 | same |
| density | `AFil.g2` | 3 | 0 | 3 | same (Activ) |
| density | `AFil.g`, `GFil.g`, `M1.j`…`M5.j` | 7 × 1 | 0 | 7 | global density below the minimum: no fill |
| **all** | | **35** | **0** | **35** | |

### LVS and the placeholders

The placeholders are empty subcircuits in the reference. Their layout cells have no devices. The deck drops both
sides, so the placeholders cause **no mismatch**. Their pin nets are floating on both sides. The comparison
therefore says nothing about the 91 placeholder pins and the 106 `r1_ctrl` pins that are not routed.
They are listed as pending in `reports/connectivity.md`.

Try a failed with all 46 circuit pairs matched. The cause was `flag_missing_ports` (strict port mode of the deck):
the 22 pad labels were inside the ring cell, so the top-level nets had no names (failure F1). This was not
caused by a placeholder.

The comparer-limit copy is the T4 method (`blocks/r1_safe`): `max_depth(8)` and `max_branch_complexity(100)`
after `align`, no extraction or rule line changed (`lvs/run_lvs_top.sh`, `deck_diff.txt` in the run).

## Floorplan: deviations from S6 and open issues

1. **Floorplan F1 cannot hold the real AFE.** The AFE layout (d17d505f7) is 192.8 × 494.4 µm. The S6 slot is
   140 × 493 µm. Real AFE (192.8) + `r1_ctrl` (520) + `r1_safe` (249.34) = 962 µm. The extended window is 938 µm.
   Options (not drawn):
   - F2: AFE rotated into the south band, `r1_ctrl` moved west, the east column for the analog blocks.
     The encoder input routes become long unless the optional S6 pin-map change (§5 item 6) is made.
   - A narrower `r1_safe` layout (≤ 225 µm wide).
   - The 1.7 mm die (S6 escalation rule).
   **Recommended: 1.7 mm**, because the escalation gate also trips (item 2). This needs a T6 ring run, a bond-plan
   run and owner confirmation of the die area. Not applied here.
2. **S6 escalation gate (laid-out analog sum > 0.30 mm²).** Laid out: `r1_afe` 0.0953, `r1_safe` 0.0718,
   `r1_bgr` 0.0187, `r1_t2f` 0.0094, `r1_osc` 0.0183 (PLAN.md §5), `r1_ls` × 6 0.0006, `r1_gate_lv` 0.0008, sum
   0.215 mm². With `r1_isense` (working-tree layout 0.047, not of record) the sum is 0.262. The gate trips if
   `r1_adc` is above 0.038 mm². The `r1_adc` revision 4 estimate is ≈ 0.068 mm² (sum ≈ 0.33 mm²).
3. `r1_safe` is 249.34 × 287.81 µm against an S6 slot of 180 × 306. It sits at x 1021–1270, under the east ring
   columns (it has Metal1–Metal4 only, so C7 allows it).
4. `r1_bgr` is 96 × 194.3 µm against a slot 172 µm high. It is rotated (R270) into the south band.
5. `r1_ctrl` is 23 µm west of the S6 position. The guard strips are 7–10 µm, not 30 µm (S6 A2).
6. The `r1_isense` and `r1_osc` placeholders are 10 µm west of S6, so they clear the east ring TopMetal1.

### Interface gaps (the top level cannot close these alone)

1. **Safe thresholds (blocked).** `r1_ctrl` has `thr_*`/`cal_*` (6 + 6 bits × 4 = 48 bits). `r1_safe` needs
   `nP/nN[7:0]` × 4 (64 bits). The adders `nP = 4c + ceil(d/2)` and `nN = 4(63−c) − floor(d/2)` are in no block.
   Recommended: put them in `r1_ctrl` 0.5. The margin to 240 000 µm² placed is only 799 µm² (`r1_ctrl` README);
   the next trim (12-bit PWM words) gives about 1 000 µm².
2. `por_n` of `r1_ctrl` has no source (no POR block).
3. `r1_safe` needs 4 × 5 µA PTAT bias (`ibias_*`). `r1_bgr` has one `iptat`. The AFE (`ib_*`) and the
   working-tree `r1_isense` (`ibias_a/b`) also need bias currents. No bias block exists.
4. `r1_t2f` `en` and `mode` have no `r1_ctrl` output (proposal: `ana_ctrl[3]`, `[4]` through `u_ls_t2f0/1`).
   Today these gate inputs float. The six `r1_ls` cells are placed but not connected.
5. The PGA decoder (`ana_ctrl[2:0]` to `c1..c4`) is in no block. The register map gives it to the chip level.
6. `VREF_BG` drives the `r1_safe` string (4.2 µA) directly. `r1_safe` assumed a buffered reference. The load on
   the bandgap is not simulated (block rule of 2026-10-21: real neighbour load). The ADC will add its own load.
7. Gate path. The `r1_ctrl` RTL already makes `gate_x = pwm_x & gate_ok & en_pad`. So `r1_gate_lv` is a buffer.
   One instance has three channels (the brief said three instances). `gate_en` is tied to `VDD`. The level shift
   is inside the `sg13g2_IOPadOut30mA` pad (core input 1.2 V). No `r1_ls` is on the gate path.

### Ring over MIM blocks (coordinator rule)

The west ring TopMetal1 columns are replaced by TopMetal2 strips over the AFE. TopVia2 is placed only outside the
AFE outline. There is no detour and no resistance penalty (estimated −0.17 to −0.19 Ω per column). Details and the
numbers are in `reports/connectivity.md` and `reports/integration_checklist.md`.

## Failures and mistakes

| # | What happened | Class | Fix |
| --- | --- | --- | --- |
| F1 | Try a LVS: all circuits matched, but the run failed. The deck runs `flag_missing_ports`. The pad labels were in the ring cell, so the top nets had no names. | verification-gap | Copy the 22 ring labels into `r1_top` (try b) |
| F2 | Try a antenna: 12 markers (`Ant.e_Metal5/TopMetal1/TopMetal2` at the four `IOPadIn` receiver gates). The `r1_padring` README gave the cause and the fix (gate load on `vdd`) before the first build. The `r1_ctrl` decaps join `VDD` only at TopMetal1/TopMetal2, so they do not count for these rules. | planning | 34 `sg13g2_decap_8` (28.6 µm² gate on `VDD`), joined on Metal1–Metal4 (try b). Antenna 0 |
| F3 | Try b LVS: the new decap cell got the name `sg13g2_decap_8$1` (a second copy next to the one from `r1_ctrl_top`). The deck flattened it. | tooling | Reuse the library cell that is already in the layout (try c) |
| F4 | Try a maximal: 6 × `V3.c1` (Via3 endcap). The Via3 at the narrow `r1_bgr` and `r1_safe` Metal3 pins sat on the pin end. The generator self-check tests spacing only; the main deck does not have `V3.c1`. | verification-gap | 0.5 µm Metal3 pad under each such via (try d) |
| F5 | The first south `VDD` straps overlapped the `r1_bgr` `vss` hookup. | planning | Found by the self-check before any DRC; straps moved to f0+2…f0+8 |
| F6 | The first `run_try.sh` call set `G1_WORKDIR` to a results path; `flow/run.sh` uses it as a path under the repository. | tooling | `G1_WORKDIR=.` |
| F7 | Tries b and c were stopped after the step that tested their fix, to save CPU. Their records say so. | process-hygiene | Labelled in `steps.log` and `run.json` |
| F8 | S6 sizes were estimates. Three laid-out blocks (`r1_afe`, `r1_safe`, `r1_bgr`) do not fit their S6 slots. | estimation | Open issue 1 and 2 above |
| F9 | Interface gaps between blocks (safe codes, biases, t2f controls, PGA decoder, POR). | coordination | Open interface gaps 1–5 |

## Built against

| Item | Version | How established |
| --- | --- | --- |
| PDK | IHP-Open-PDK `84374023ee8b4b126bebbba67fcbada0a9c0ff0b` | checked by `flow/run.sh` before every run |
| KLayout | 0.30.9 | `klayout -v` in the container; DRC and LVS logs |
| Container | `tapeoutbench-eda:latest`, id `sha256:ddeb6957…` | checked by `flow/run.sh` |
| ngspice / xschem / LibreLane / CACE | not used | — |
| Ring | `r1_padring` revision b/c GDS `40514b4f…` | hash checked by the generator |
| `r1_ctrl_top` | 0.4, run `r1ctrl_ll_20261021_t7`, GDS `d52e67e8…` | hash in `run.json` |
| Block GDS | `r1_safe` `fbc31139…`, `r1_bgr` `324e3c27…`, `r1_t2f` `5e7aa75a…`, `r1_ls` `a4f49636…`, `r1_gate_lv` (filled) `a3dee0f0…` | hashes in `reports/placement.csv` |

## Files and reproduction

| File | Purpose |
| --- | --- |
| `layout/r1_top_assemble.py` | generator: `python3 r1_top_assemble.py <G1_RESULTS_ROOT> <out_dir>` |
| `layout/r1_top_png.py` | picture: `python3 r1_top_png.py <gds> <png> [px]` |
| `layout/r1_top.png` | picture of try d |
| `lvs/pnl2cdl.py` | copy of the G1 `g1_padring` converter; bus ports expanded |
| `lvs/make_top_cdl.py` | top reference: `r1_ctrl` CDL + block CDLs of record + empty placeholders + ring (flat) + decaps |
| `lvs/run_lvs_top.sh` | LVS: `stock` or `limits` |
| `flow/run_try.sh` | one try: `sh .../run_try.sh <try> [gen cdl lvs antenna main maximal density stock]` |
| `flow/run_drc_set.sh` | DRC main, maximal, density, antenna with the stock decks |
| `flow/drc_summary.py` | counts per rule, class (a)/(b) |
| `flow/lvs_report.py` | circuit, net, device and pin pairs of an LVS database |
| `flow/write_run_json.py` | `run.json` of a try |
| `flow/probe_*.py` | probes of the ring and macros used for the plan |
| `reports/placement.csv`, `reports/connectivity.md`, `reports/integration_checklist.md` | deliverables 1, 4 and 5 |
| `reports/runs/asm-20261021-{a,b,c,d}.json`, `reports/runs/asm-20261021-d_lvs_report.txt` | copies of the `run.json` of each try and the LVS pair report of try d |

Reproduce try d from the repository root (POSIX shell):

```
G1_CPUSET=116-119; export G1_CPUSET
G1_RESULTS_ROOT=<results root>; export G1_RESULTS_ROOT
G1_WORKDIR=.; export G1_WORKDIR
sh designs/r1-joint/blocks/r1_top/flow/run_try.sh asm-20261021-d
```

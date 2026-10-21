# R1_TOP

Block `r1_top` (track T8, P3 preparation). This block assembles the R1 chip top level from the ring of record and
the finished macros. The four macros that are not finished are placeholder outlines.

## What it is

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
| Chip fill | not run | — |
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

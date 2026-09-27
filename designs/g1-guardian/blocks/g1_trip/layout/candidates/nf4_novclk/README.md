# nf4_novclk: non-overlapping comparator clock for the TRIP macro. CANDIDATE r4, NOT ADOPTED

**This is a candidate.** The chip of record stays r3 (`g1_chip_top_1414_r3.gds`, `7d07a784…`), and r3 was not
changed. The r4 files below are new files. The owner decides whether to adopt them.

## What it is

Red-team finding F1 (`review/redteam-20260927/trip_path/FINDINGS.md` §3.1, §6) found a 0.2–0.34 ns race.
The hard comparator's strobe (`cmp_clk_n`, from the inverter `XCLKI`) lands just after the soft
comparator's reset edge (`cmp_clk`). The result is a hard early trip of 46–48 LSB (tt, block bench).

This candidate removes `XCLKI` and adds the generator `g1_novclk` in its place (20 LV devices, `layout/novclk.py`):

```
cmp_clk -> 3 inverters, long L (n 0.3/2.5 um, p 0.6/2.5 um) -> sharpening inverter (p 1/0.13, n 0.5/0.13) -> dly
cmp_clk_s = OR(cmp_clk, dly)   NOR2 (p 2/0.13 series, n 0.5/0.13) + inverter (p 2x2/0.13, n 2x1/0.13) -> soft comparator clk
cmp_clk_n = NAND(cmp_clk, dly) NAND2 (p 1.5/0.13 parallel, n 1/0.13 series)                          -> hard comparator clk
```

- Each comparator evaluates on an undelayed `cmp_clk` edge.
- Each comparator resets D later, after the other comparator has decided.
- The macro pin `clk`, all other nets, the outline, the pins, the LEF and the sub-cells are unchanged.

## Built against

| Item | Value | How established |
|---|---|---|
| PDK | IHP-Open-PDK `84374023ee8b4b126bebbba67fcbada0a9c0ff0b` | `flow/run.sh` checks `/foss/pdks/ihp-sg13g2/COMMIT` |
| Container image | `sha256:ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2` | `flow/run.sh` identity check |
| ngspice | ngspice-46 (KLU) | `ngspice -v` in the container |
| KLayout | 0.30.9 | `klayout -v`; DRC/LVS logs |
| kpex (klayout-pex) | 0.3.12 | `pip show klayout-pex` in the container |
| Rule decks | stock `run_drc.py` / `run_lvs.py` of the PDK above, unmodified | invoked from `/foss/pdks/ihp-sg13g2/libs.tech/klayout/tech/` |

All jobs ran in the container, pinned with `G1_CPUSET` inside 16–31 / 48–63 (detached ones through
`flow/launch_pinned.sh`). `${BULK}` is the external artifact root. The run root is `${BULK}/r4-20260927`.

## Status

| Gate | Check | Result | Evidence |
|---|---|---|---|
| 1 | Schematic generator spliced into the r3 extraction; kick_rt brackets, hard 200 / soft 153, 212 ns | **passed**: hard −1 (trip at −1, none at 0) and soft +1 (trip at +1, none at +2), at tt, ss/1.08 V/−40 °C and ff/1.32 V/125 °C. Control: the unmodified r3 extraction still trips at ud 40 (tt) | `evidence/sim/gate1_table.txt`, `gate1_kick_*.jsonl` |
| 1 | Generator alone, lumped comparator clock loads, 5 corners | window 5.85/6.74 ns (ss/−40), 6.39/7.17 ns (ff/125), min 3.87 ns (ff/−40), max 10.26 ns (ss/125); full swing; no glitch (hold excursion ≤ 50 mV) | `evidence/sim/gen_sweep_table.txt`, `gen_glitch.txt` |
| 2 | PDK DRC deep, main + sg13g2_maximal, `--no_density` | **passed**, 0 items (7.6 s + 15.3 s) | `evidence/macro/drc.log`, `…_full.lyrdb` |
| 2 | PDK antenna (block) | **passed**, 0 items | `evidence/macro/antenna.log` |
| 2 | PDK LVS `--topcell=g1_trip --run_mode=deep` vs `g1_trip_nf4_novclk_lvs.cdl` | **passed** (netlists match, 5.5 s) | `evidence/macro/lvs.log` |
| 2 | Negative control: same layout vs the r3 CDL `g1_trip_nf4_lvs.cdl` | failed, as expected | `evidence/macro/lvs_negative_control.log` |
| 2 | XOR of the candidate vs the r3 TRIP cut (`macro_xor.py`) | differences only in (155, 177.5)–(195, 206.3) µm (generator, risers, removed fill); sub-cells identical; outline 229 × 207 µm unchanged | this README |
| 3 | kpex 2.5D CC on the candidate | run, rc 0, 14 min, 1264 MOS (= 1246 − 2 + 20), 18 399 C; clock gates checked: 8 soft devices on `cmp_clk_s`, 8 hard on `cmp_clk_n`, 6 generator gates on `cmp_clk` | `sim/postlayout/g1_trip_nf4_novclk_pex.spice` |
| 3 | kick_rt brackets on the extraction (11 brackets) | **passed**: hard −1 at tt, ss/−40, ff/125; hard code 254 −1 at all three corners; hard tt/27 °C at VDD 1.08 V and 1.32 V −1; soft +1 at tt, ss/−40, ff/125 | `evidence/sim/gate3_table.txt`, `gate3_kick_*.jsonl` |
| 3 | Non-overlap window on the extraction (`sim/win_pex.py`), fall / rise edge | **passed**: ss/1.08 V/−40 °C 10.31 / 8.41 ns (> 2.5); ff/1.32 V/125 °C 9.90 / 8.60 ns (< 15). Also tt 9.37 / 7.86, ff/−40 °C 6.40 / 5.26, ss/125 °C **15.11** / 13.07 (not a gated corner; under the red-team cap of 20 ns) | `evidence/sim/window_extracted.txt` |
| 3 | Clock edges, 10–90 %, extraction (hard evaluate/reset; soft) | hard 0.44/0.59 ns tt, 0.61/0.83 ss/−40, 0.34/0.57 ff/125; r3 XCLKI on the same bench 0.62/0.62, 0.87/0.92, 0.47/0.55. Soft 0.21/0.19 tt, 0.28/0.24 ss/−40 (r3: the pin source, 0.16) | `window_r3_reference.txt` (same deck on r3: hard evaluates 0.29 ns after the soft reset, the F1 race) |
| 3 | F2 dependency points (hard 200, tt, ud −2 / +2) | **passed**: T / n at period 161 ns, period 263 ns, soft code 100 and soft code 255 (r3: 43–51 LSB early depending on these) | `evidence/sim/f2_points.txt` |
| 4 | r4 chip DRC main / maximal / precheck / density / antenna | **passed**, 0 markers each (main 263 s, maximal 666 s) | `evidence/chip/*/` |
| 4 | Global GatPoly (GFil.g, min 15 %) | 300 828.38 µm² = 15.05 %, margin **918.98 µm²** (r3: 300 527.47, margin 618.07) | `evidence/chip/density/run.log`, `fill.json` |
| 4 | Projected LVS vs `g1_chip_top_1414_r4_projected_ref.cdl`, strict ports | **passed**: 62 956/62 956 devices, 31 824/31 824 nets, 22/22 pins (r3 62 940 / 31 816; +16 devices after parallel combining, +8 nets) | `evidence/chip/lvs_projected/pair_counts.json` |
| 4 | Canonical LVS vs `g1_chip_top_1414_r4.cdl` | failed, as for r2/r3: the 51 circuit pairs have exactly r3's status and counts (35 Match, 14 NoMatch IO/level-shifter, 2 Skipped) | `evidence/chip/lvs_canonical/pair_counts.json` |
| 4 | XOR r3 → r4 (`chip_xor.py`, box 771,736,1000,943) | inside the TRIP box: the macro's layers only. Outside: only 5/22 (+58 polygons, 406.0 µm², the GatPoly fill), 0 text differences. Before the GatPoly fill (`…_prefill.gds`): nothing outside the box | `evidence/chip/chip_xor.json`, `chip_xor_prefill.json` |
| 4 | TRIP cell cut from r4 vs the candidate macro | XOR 0 on every layer, texts equal | this README |
| 5 | Comparator delay, settle and DAC decks; window mismatch MC; kick screen under mismatch (27 Sep) | delay deck **failed** at tt 1 mV (strobe 1 decided high, soft path ~1 LSB early); ss 1 mV passed (1.996 ns); settle and DAC equal to r3; window MC 30+30 seeds passed (min 8.30 ns at ss/−40 °C, max 10.03 ns at ff/125 °C); kick ±10 LSB screen passed on 19 seeds; brackets not run | `BLOCK_QUALIFICATION_20260927.md` |
| — | RC extraction | **not run** | — |
| — | Chip-level transient re-runs (`c_mid`, near-threshold, `cal`, `hard_pulse`, `q`) | **not run** (done by someone else) | — |

1 LSB = 1.962 mV at `icmp` = 0.196 mV of shunt. "hard −1" means the effective threshold lies between
0 and 1 LSB **above** the code. On the same bench r3 is 46–48 LSB below the code.

## Layout (`gen_trip_layout.py what=novclk`, class `NovclkPatch`)

The r3 macro is not produced by `gen_trip_layout.py what=top`: that mode generates the Sep-19 macro. The NF4
input pair and regenpair4 were edited into the chip afterwards. So the r4 change is a **patch** of the
TRIP cell as it sits in r3. The same code runs on the macro cut (top `g1_trip`) and on the chip (cell
`__rz_port_text_033_retained_g1_trip`). `what=top` and every r3 output are unchanged; `RowLayout` is not used by
`TopBuilder`. `g1_layout_lib.py` only generalises RowLayout's PMOS drain-stub offset from 0.66 to 0.53 + L,
which is identical for L = 0.13.

1. Remove the 59 XCLKI shapes inside (174.0, 184.4)–(178.8, 188.95). Remove its input riser, the VDD/VSS
   Metal2 risers and their ring Via1. The VDD-bar Via2 at (176.4, 206) is reused.
2. Cut the Metal3 clock polygon at x = 170.8. Its west part (the y = 192 line to the soft comparator)
   becomes `cmp_clk_s`. Trim the `cmp_clk_n` polygon to start at the ckh port.
3. Draw a RowLayout block at (160.5, 182.6)–(190.68, 193.75), with a p+ tie under the VSS rail. Ports:
   - cks goes on Metal3 up to the y = 192 line;
   - clk goes (188.53, 191) → (172, 191) → the existing clk Via2 at (172, 192);
   - ckh goes on Metal3 to y = 188;
   - VDD goes on a Metal2 riser at x = 176.4;
   - VSS goes on a Metal2 riser at x = 191.58 to the p+ ring.
4. Remove the macro fill instances within 1.5 µm (35 arrays expanded, 124 instances removed). Mark the
   block no-fill (Activ, GatPoly, Metal1–3, datatype 23).
5. Chip only: remove the 15 chip-level fill shapes (8/22 ×5, 10/22 ×5, 30/22 ×5) of the top cell that lie
   entirely over the macro within 1.5 µm of new shapes.

Commands (from `${REPO}`, with `export G1_CPUSET=<cpu> G1_CONTAINER_ENGINE=podman G1_RESULTS_ROOT=${BULK}/r4-20260927`):

```
# macro cut of the r3 chip (identical to the NF4 cut c8efefe3…: XOR 0, texts equal)
flow/run.sh klayout -b -r <cut_macro.py of trip-nf4-pex-20260924-r1> -rd src=designs/g1-guardian/blocks/g1_padring/layout/g1_chip_top_1414_r3.gds \
   -rd cell=__rz_port_text_033_retained_g1_trip -rd out=${BULK}/r4-20260927/g1_trip_r3cut.gds
G1_WORKDIR=designs/g1-guardian/blocks/g1_trip/layout flow/run.sh klayout -b -r gen_trip_layout.py -rd what=novclk \
   -rd src=${BULK}/r4-20260927/g1_trip_r3cut.gds -rd out=${BULK}/r4-20260927/cand/g1_trip_nf4_novclk.gds
python3 make_cdl.py ../../../reports/pex/nf4/g1_trip_nf4_lvs.cdl g1_trip_nf4_novclk_lvs.cdl      # in this directory
python3 $D/drc/run_drc.py --path=<cand gds> --topcell=g1_trip --run_mode=deep --no_density --run_dir=…   # D = PDK klayout/tech
python3 $D/drc/run_drc.py --path=<cand gds> --topcell=g1_trip --run_mode=deep --antenna_only --run_dir=…
python3 $D/lvs/run_lvs.py --layout=<cand gds> --netlist=<this dir>/g1_trip_nf4_novclk_lvs.cdl --topcell=g1_trip --run_mode=deep --run_dir=…
python3 $D/lvs/run_lvs.py --layout=<cand gds> --netlist=<r3 g1_trip_nf4_lvs.cdl> --topcell=g1_trip --run_mode=deep --run_dir=…   # negative control
```

## Extraction

As in `sim/postlayout/README.md`, with the labels file `g1_trip_nf4_novclk_pexlabels.txt`:
- `cmp_clk_n` moved to (195, 188) on the trimmed line;
- `cmp_clk_s` added at (150, 192).

`make_pex_netlist.py` has a new config, `trip_novclk`. It lets `cmp_clk_s` win over the comparator
sub-cell's `clk` label; that label maps to the pin name and would otherwise short the two clocks.

```
G1_WORKDIR=designs/g1-guardian/blocks/g1_trip/layout flow/run.sh klayout -b -r pex_input.py -rd gds=${BULK}/r4-20260927/pex/g1_trip_nf4_novclk.gds -rd out=${BULK}/r4-20260927/pex/g1_trip_nf4_novclk_pexin.gds
flow/run.sh kpex --pdk ihp_sg13g2 --gds ${BULK}/r4-20260927/pex/g1_trip_nf4_novclk_pexin.gds --cell g1_trip --schematic ${BULK}/r4-20260927/pex/g1_trip_nf4_novclk_lvs.cdl --2.5D --mode CC --out_dir ${BULK}/r4-20260927/pex/cc
python3 make_pex_netlist.py trip_novclk ${BULK}/r4-20260927/pex/cc/g1_trip_nf4_novclk_pexin__g1_trip/g1_trip_k25d_pex_netlist.spice g1_trip_nf4_novclk_pex.spice
```

kpex ran on the first write of the candidate (`ef3f07b0…`, with GDS timestamps). That file has XOR 0 against
the file of record `3213819a…`. The kpex-internal LVS failed, as for every earlier TRIP extraction
(flat, MIM-less input); it is not sign-off.

## Simulation benches (`sim/`)

- `mkgen.py`, `gen_sweep.py`, `sweep.sh`, `run_decks.sh`, `tab.py`, `check_glitch.py`: generator sizing
  sweep. Variants are in `variants/`; the final netlist is `../g1_novclk.spice` (variant `final` = `a3L2p5`).
- `make_novclk_splice.py`: Gate 1 netlist, i.e. the r3 extraction with XCLKI removed and `g1_novclk.spice`
  spliced in.
- `kick_rt.py`, `tb_kick_rt.cir.tmpl`: copies of `review/redteam-20260927/trip_path/` (`0690d3e2…`,
  `9d7abd2b…`). Only the REPO depth in `kick_rt.py` changed. Queue lines are as in FINDINGS §6.4, run with
  `BULK=… python3 kick_rt.py worker <cpu> <outdir> <queue>`.
- `win_pex.py`: window and edge deck on an extraction.

Run note: `run_decks.sh` drops ngspice's progress lines. More than about 5 parallel ngspice in one container
slowed every run by 10× or more here, so use one container per 4–5 decks.

## Chip r4 (`blocks/g1_padring/layout/g1_chip_top_1414_r4.gds`)

1. Take r3 `7d07a784…` and apply `gen_trip_layout.py what=novclk -rd cell=__rz_port_text_033_retained_g1_trip`.
   This gives `${BULK}/r4-20260927/chip/g1_chip_top_1414_r4_prefill.gds` (`5b3c4143…`, byte-reproducible).
2. Run `blocks/g1_ctrl/flow/eco/add_gatpoly_fill.py --target-um2 400 --min-width-nm 700 --obstacles 1/0,5/0,6/0,14/0,7/21,28/0,31/0,32/0,26/0,1/22:300`
   with `--exclude-box` for every analog/digital macro (digital, TRIP, SENSE, BGR + its supply context, OSC,
   T2F, GATE). The result is 58 rectangles and 406 µm² in the top cell, 5/22 only (`fill.json`).
   - Reason: the coordinator asked (red-team PH-1) to keep the GFil.g margin at least r3's.
   - The patch had lowered it by 105.1 µm² (to 513 µm²).
   - A core-only placement (IO rows excluded) found 0 candidates. As in r3, the rectangles lie in the free
     area between the core and the pads.
3. Chip CDL: `make_chip_cdl.py`, the same two-line edit plus the `g1_novclk` subckt inside the g1_trip
   source block of the r3 CDLs. It is asserted invertible; every other line is unchanged.
   - Projected reference: `flatten_reference.rb` on the edited r3 `comparison_only.cdl`.
   - Method control: the same command on r3's `comparison_only.cdl` reproduces `d0d36c84…` exactly.
   - 77 035 devices (77 017 − 2 + 20), 22 pins, roundtrip Match.
4. Sign-off: the same commands and options as `run_candidate.sh signoff` (r3), on CPUs 22–31, 50–55.

Build attempts that failed:
- Build 1: chip-level fill over the macro touched the new wires. Main DRC showed 2 M3.b, 3 M1Fil.c and
  1 M3Fil.c markers, and projected LVS failed (20 devices, 12 nets). Fixed by step 5 above.
- Build 2: one M2 fill shape straddling the macro outline was removed, which gave an XOR outside the box.
  Fixed by removing only fill that lies entirely over the macro.

Both are kept in `${BULK}/r4-20260927/signoff_attempt1`, `attempt2`. Build 3 was superseded by the GatPoly
fill before its checks finished.

## Files and hashes

| File | SHA-256 |
|---|---|
| r3 chip (input, unchanged) | `7d07a7841a531f51e08b0c90e76fe603889cd2ef29905e309e63f09742e688f2` |
| r3 TRIP cut `${BULK}/r4-20260927/g1_trip_r3cut.gds` | `9a99a89b7d9f58884813ec45441aa0bce284c57674526b837936a120affecb45` |
| **Candidate macro** `${BULK}/r4-20260927/cand/g1_trip_nf4_novclk.gds` | `3213819a47b6a43d370318b3b8520b05fc61b2806a745d03541040bc199d80c5` |
| **r4 chip** `blocks/g1_padring/layout/g1_chip_top_1414_r4.gds` (= bulk `chip/`) | `225d0b535321ed312594bb13d97b7271014f487162564a56c874572de715173a` |
| r4 before GatPoly fill `${BULK}/r4-20260927/chip/g1_chip_top_1414_r4_prefill.gds` | `5b3c414371a0ea999b261b6574bbbb4dd7a4f1c70b7c2c68dd930902e7237768` |
| r4 canonical CDL `blocks/g1_padring/netlist/g1_chip_top_1414_r4.cdl` | `e060c0c59a168e5b69b0c47dc31cbfe4f4444d2ec8af62960c339c1230a2c99f` |
| r4 projected reference `${BULK}/r4-20260927/cdl/g1_chip_top_1414_r4_projected_ref.cdl` (17 MB, bulk only) | `27a27cd64dfa18db66e2e9374c78b62f2d4ac95440d071149ffb048702e08fda` |
| r4 comparison-only CDL `${BULK}/r4-20260927/cdl/comparison_only_r4.cdl` | `47eea6f204cf6520b1adf6585c66eed06eeb18c12eeae666737036ff7e2de963` |
| Macro LVS CDL `g1_trip_nf4_novclk_lvs.cdl` | `8943a5a8a3d6ad28179fa3027539dfe3c9f4f91c968a6f2cd9e978b42309945e` |
| `g1_novclk.spice` / `g1_novclk.cdl` | `1750146f…5172` / `5284ea4e…fe3f` |
| TRIP extraction `sim/postlayout/g1_trip_nf4_novclk_pex.spice` | `6f518e0758a87b334ab5ae98a8ad43d79dd03ab4ba52c241f742280b6d2f770b` |
| kpex raw netlist | `633db464a16171157d1ffdf0de5758429fd076951460b7667c568d5a51608468` |
| Gate 1 netlist `${BULK}/r4-20260927/net/g1_trip_nf4_novclk_sch.spice` | `258115a4704f88851cb9dcbb60196f27fd4159870bd63e61587a2ce1ab964e6b` |
| r3 extraction (base) `sim/postlayout/g1_trip_nf4_pex.spice` | `ba86b7b2a530abae365d539297909e033b24a54597f9cc75d8dff273c30d401c` |

`gen_trip_layout.py` and `novclk.py` hashes: take them from the commit. The candidate macro and the prefill
chip were regenerated after the last edit and are byte-identical.

## For the chip-level re-runs (not run here)

- CDL: `blocks/g1_padring/netlist/g1_chip_top_1414_r4.cdl`.
- TRIP extraction: `blocks/g1_trip/sim/postlayout/g1_trip_nf4_novclk_pex.spice`. It has the same
  `.subckt g1_trip` name and port order as `g1_trip_nf4_pex.spice`, so swap the include.

## Not run

- Comparator delay, settle and DAC decks and the window MC: run 27 Sep, see `BLOCK_QUALIFICATION_20260927.md` (its own "Not run" list applies).
- RC extraction, IR/EM and full-chip PEX.
- Chip-level transients.
- Bond map re-verification for r4: pads and openings are unchanged (XOR), but it was not run.
- LEF regeneration: not needed; outline, pins and Metal4+ are unchanged.
- Measurement: not run (no silicon).

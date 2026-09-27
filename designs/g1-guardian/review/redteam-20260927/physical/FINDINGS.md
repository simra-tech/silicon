# G1 physical tape-in red team, round 2 (2026-09-27)

Aspect: physical verification and tape-in readiness of the chip of record.
Reviewed file: `designs/g1-guardian/blocks/g1_padring/layout/g1_chip_top_1414_r3.gds`.
Its SHA-256 was checked before the first run: `7d07a7841a531f51e08b0c90e76fe603889cd2ef29905e309e63f09742e688f2`, 84 097 180 bytes.
Reference netlists:
- canonical `netlist/g1_chip_top_1414_r3.cdl` `5e47ae02…`;
- projected `netlist/g1_chip_top_1414_r3_projected_ref.cdl` `d0d36c84…`.

Nothing tracked was modified, and the GDS was not edited.

This review builds on `review/redteam-20260925/PHYSICAL_TAPEIN.md`, which covered r1. Its closed items are not repeated here. Items that are unchanged in r3 are listed under "Checked and clean" only where they were re-run on r3.

**Built against:**
- IHP-Open-PDK `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`: `flow/run.sh` commit gate.
- KLayout 0.30.9 and container `tapeoutbench-eda` `sha256:ddeb6957…`: `flow/run.sh` image check.
- CPUs 24-31, pinned with `taskset` through `G1_CPUSET`.
- Raw outputs are under `${BULK}/redteam-20260927/physical/`. Small copies, with paths normalised to `${BULK}`/`${REPO}`, are in `evidence/` next to this file.

## 1. Verdict

**Yes: for the physical aspect, r3 is safe to submit as it is.** Every check I could run on the exact file passed:
- stock PDK DRC in maximal mode, precheck mode with the extra rules and density, and antenna: 0 markers;
- projected LVS, re-run: match;
- an independent metal-only connectivity extraction: 22 distinct pad nets, exactly the expected grouping, the 5 supply domains distinct, no label shorts, no floating pad;
- sliding-window density at 5 µm steps on every filled layer: every window passes;
- a raw GDS record audit: no zero-area polygons, no width-0 paths, no off-grid or illegal-angle vertices, no duplicate, empty or undefined cells, one top cell, nothing outside the die.

I found no BLOCKER or MAJOR issue. What remains:
- IHP's own rejection test on this SHA has no recorded result. The GatPoly global density passes by only 618 µm², so that test should be recorded before submission.
- Three minor items: bond-wire angle, one wrong statement in the tape-in package, and the missing DigiBnd layer. None needs a GDS change.

## 2. Findings

| ID | Title | Severity | Evidence | Proposed fix | Effort / GDS change |
|---|---|---|---|---|---|
| PH-1 | IHP's rejection test on r3 has no recorded result. GFil.g (a critical rule, no waivers) passes by 0.031 points = 618 µm² | MINOR (submission gate) | `evidence/precheck/*_density.log`: GatPoly 300 527.47 µm² of 1 999 396 µm² = 15.03 % (min 15 %). `evidence/p2/density_win5um.json`: 15.0309 %. `.private` notes show the owner planned the test; no result is recorded in the repository | Owner runs IHP's MPW rejection test (or the intake check) on `7d07a784…` and records pass or fail and the date in `TAPEIN_PACKAGE_20260924.md` §6. Only if it fails on GFil.g: add GatPoly fill with `add_gatpoly_fill.py`, but only about 574 µm² more fits under its current constraints (182 candidates, 100 used; `r3_identity/fill.json`) | 0.5 h, no GDS change. If the test fails: about 3-4 h for fill with relaxed exclusions plus a full re-sign-off, GDS changes |
| PH-2 | Bond-wire angle reaches 45.2° at the four pads nearest the package corners (pads 6, 12, 18, 24). Bonding-house acceptance is still not run | MINOR | `evidence/p4_bondgeom.json`, nominal QFN24 4 × 4 mm drawing from `bondplan_20260925.py`: angle to the pad-edge normal is 9.3-45.2°, wires 1.007-1.411 mm, minimum wire-to-wire distance 95.3 µm (2-D) | Send the bond plan with this angle table to the bonding house and get acceptance in writing. If they cap the angle at 45°, the fix is a package drawing choice, not the die | 0.5 h, no GDS change |
| PH-3 | `TAPEIN_PACKAGE_20260924.md` §6 says the r3 DRC, maximal, precheck, density and antenna reports are "bulk only; not committed in the r3 sign-off directory, not in a retention manifest". They are committed | MINOR (documentation) | `blocks/g1_padring/reports/signoff-1414r3-20260926/{drc_main,drc_maximal,precheck,density,antenna}/` exist and are listed with hashes in its `manifest.json` and README | Correct the five evidence cells to point at the committed copies | 0.2 h, no GDS change |
| PH-4 | No DigiBnd (16/0) around the standard-cell macro. Layout rules §8.1 says DigiBnd "must be used when using IHP's standard digital libraries" | MINOR (note) | `evidence/p1_gdsraw.json`: 16/0 is absent from the layer list. The only effect of DigiBnd is to relax Cnt.c and NW.c1/d1/e1/f1. The stricter analog rules were applied and gave 0 markers (maximal and precheck), so this carries no rejection risk | Mention it in the IHP submission note. Do **not** add the layer now: adding it only relaxes rules, and it would need a re-sign-off | 0.1 h, no GDS change |

## 3. Findings in detail

### PH-1: IHP's rejection test not recorded; GatPoly margin

- **What:** the global GatPoly density (5/0 ∪ 5/22, merged) was computed twice on r3:
  - the stock density table inside my precheck run gave 15.03 %;
  - my own 5 µm tiling gave 15.0309 %.

  The rule minimum is 15 %. The margin is 300 527.47 − 0.15 × 1 999 396 = **618 µm²**. If IHP's check used a chip area 0.206 % larger, the rule would fail. That is about +4 120 µm², or a die 1.46 µm wider in each direction, for example a frame or scribe margin added before the density step.
- **Area basis:** IHP's public community-MPW text states that the 2 mm² area includes the seal ring. That matches the 1414 µm EdgeSeal boundary the deck uses (the log says "Total area of the design is 1999396.0 um^2"). So the stock basis agrees with IHP's stated basis.
- **Why it matters:** GFil.g is on the precheck (critical) list, and the layout rules §4.1 say no waivers are granted. The owner accepted the thin margin on 2026-09-25. The only thing that settles it is IHP's own test on this SHA.
- **Commands:**
  - `flow/launch_pinned.sh 28-29 . 5400 ${BULK}/redteam-20260927/physical/precheck/run.log python3 /foss/pdks/ihp-sg13g2/libs.tech/klayout/tech/drc/run_drc.py --path=designs/g1-guardian/blocks/g1_padring/layout/g1_chip_top_1414_r3.gds --topcell=g1_chip_top --run_mode=deep --precheck_drc --density_thr=2 --run_dir=${BULK}/redteam-20260927/physical/precheck`
  - `flow/launch_pinned.sh 24-31 . 3600 …/p2/run.log klayout -b -r evidence/scripts/p2_density.py`

### PH-2: Bond-wire angle

- **What:** I re-derived the bond geometry in package coordinates from `padframe/bondplan_20260925.json`. The inputs were the r3 opening centres and the generator's nominal package: body 4.00 mm, pitch 0.50 mm, lead 0.25 × 0.40 mm, paddle 2.60 mm, die centred and rotated 90° clockwise.
- **Result:**
  - All pads sit in 395-955 µm of each 1414 µm edge, while the leads span 2.5 mm. The wires therefore fan out: 9.3°, 12.8°, 29.0°, 31.7°, 43.3° and 45.2° from the edge normal.
  - Wire lengths are 1.007-1.411 mm.
  - The closest two wires come within 95.3 µm of each other (pads 5/6 and the equivalent pairs on the other sides), measured at the die end.
  - No wire passes closer than 95 µm to another pad centre. The opening half-width is 32.9 µm.
  - There are 0 crossings, as the generator also reports.
- **Why it matters:** ball bonding is omnidirectional, and 45° is inside common practice. Some houses nevertheless cap the angle or the wire length, and the package drawing is still nominal (`BONDPLAN_20260925.md` "What the bonding house still has to confirm").
- **Pads:** the opening is 65.8 µm at a 112 µm pitch, the opening-to-opening gap is 46.2 µm and the opening is 68.1 µm from the die edge. These are comfortable for 25 µm Au ball bonding. Bonding-house acceptance: **not run**.
- **Command:** `python3 evidence/scripts/p4_bondgeom.py designs/g1-guardian/padframe/bondplan_20260925.json …/p4_bondgeom.json` (geometry only, no EDA tool).

### PH-3: Tape-in package statement

- `review/TAPEIN_PACKAGE_20260924.md` §6, the rows "KLayout DRC main", "maximal", "precheck", "Density" and "Antenna", say "bulk only; not committed…".
- The sign-off directory does contain these reports: `…/drc_main/*_main.lyrdb` `3da5e270…`, `drc_maximal/*.lyrdb` `f54b65a5…`, `density/*.lyrdb` `89149c55…`, `antenna/*.lyrdb` `71533d82…` and `precheck/*_full.lyrdb` `92416e92…`. They are listed in `manifest.json`.
- Two of these hashes match my runs byte for byte: maximal (`f54b65a5…`) and antenna (`71533d82…`).
- Fix: text only.

### PH-4: DigiBnd absent

- Layer 16/0 does not appear in the file (raw record parse).
- The deck (`feol/5_14_cont.drc`) applies Cnt.c at 0.05 µm inside DigiBnd and at the analog value outside it. The macro therefore got the stricter analog check, and it passed.
- This is recorded so that IHP is not surprised. No action on the GDS.

## 4. Checked and clean (r3, `7d07a784…`, this review)

| Check | Result | Evidence |
|---|---|---|
| File identity | sha256 `7d07a784…` = record; `5e47ae02…` CDL = record | `sha256sum` |
| Maximal DRC (`run_maximal.py`, stock `sg13g2_maximal.drc`, recommended rules on, 4 threads) | **passed**, 0 items; 292 rules executed with "0 error(s)", including LU.*, Seal.*, Pad.* (Pad.jR, Pad.kR), MIM.*, GFil.*, MxFil.*; 557 s. The lyrdb is byte-identical to the sign-off lyrdb (`f54b65a5…`) | `evidence/drc_maximal/` |
| Precheck DRC with the extra rules (`--precheck_drc`, **without** the sign-off's `--disable_extra_rules`; density included) | **passed**, 0 items, 801 s. OFFGRID, ANGLE, PIN, FORBIDDEN and RECOMMENDED were enabled | `evidence/precheck/` (`51f39614…`) |
| Antenna (`--antenna_only --antenna`) | **passed**, 0 items, 128 s; lyrdb byte-identical to the sign-off (`71533d82…`) | `evidence/antenna/` |
| Global densities (deck) | Activ 44.22, GatPoly 15.03, M1 46.97, M2 37.39, M3 47.93, M4 46.75, M5 48.35, TM1 50.33, TM2 46.84 % (all within the limits) | `evidence/precheck/*_density.log` |
| 800 × 800 µm window density, every window fully inside the die on a 5 µm grid (15 129 windows per layer) | **passed** on all layers. Worst minimums: M2 25.335 % at (290, 320); M4 26.839 %; Activ 26.937 %; M3 30.03 %; M5 31.38 %; M1 31.68 % (limit 25 %). Worst maximum: Activ 46.79 % (limit 65 %), M1-M5 ≤ 53.39 % (limit 75 %). The macro swap did not lower the M2 window found in round 1 (r1: 25.21 %, same origin) | `evidence/p2/density_win5um.json` |
| Projected LVS re-run on the in-tree file (strict ports, deep) | **passed**, "Congratulations! Netlists match", 62 940 extracted device lines as in the sign-off. The extracted netlist differs from the sign-off's only by the date line and internal net numbering | `evidence/lvs_projected/`; lvsdb `b782081a…` and `_extracted.cir` `e061d71f…` bulk only |
| Independent top-level connectivity (KLayout `LayoutToNetlist`, Metal1…TopMetal2 with vias and pin shapes, no LVS deck) | **passed**: 24 pads → 22 distinct nets. Grouping exactly VDD{1}, VSS{2,5}, IOVDD{3}, IOVSS{4,6} and 18 single pads. VDD, VSS, IOVDD, IOVSS and VDDA are 5 distinct nets (no inter-domain short at metal level). Every pad net carries exactly its own top-level label. No net carries two different top-level label names. 0 top-cell labels off metal | `evidence/p3/conn.json` |
| Pad-to-core nets against the CDL | **consistent**: the metal of the 9 pads that the CDL wires directly into the core (VDDA, SENSE_P/N, G_SHARED, D_STD, D_ELT, HBT_E/B/C) reaches the core. The 9 that the CDL connects only to the pad cell (TRIP_SET and VREF via `padres`; EN, SCLK, SDI via `p2c`; GATE, FAULT_N, SDO, TEMP_OUT via `c2p`) stop at the IO cell. In the CDL top subcircuit each of those 9 port names occurs only on the pad and its bondpad | `evidence/p3/conn.json`; CDL top subckt |
| Raw GDS record audit | **passed**: GDS 600, UNITS 1 nm/1e-9, library `LIB`, 304 cells, 1 top (`g1_chip_top`); 0 duplicate, 0 empty, 0 undefined references; 0 zero-area or unclosed boundaries; 0 width-0 or absolute-width paths; 0 vertices off the 5 nm grid, and no non-45° edges on mask layers (Manhattan only on via layers); maximum 539 vertices per boundary; instance angles 0/90/180 only, no MAG on instances; 468 AREFs; 82 properties, all `oaBoundary:pr` on stock standard cells; no cell-name characters outside `[A-Za-z0-9_$]` (24 names > 32 characters, as in r1) | `evidence/p1_gdsraw.json`, `scripts/p1_gdsraw.py` |
| Layers | 73 layer/datatype pairs. None forbidden (§3.2). Only 39/4 and 189/4 are missing from the rules-PDF table (both from PDK cells; as round 1). No 9/40 plasma-dicing, 76/0 DevTrench or scribe/mark layers | `evidence/p1_gdsraw.json` |
| Nothing outside the die | 0 shape area outside (0,0;1414,1414) on any layer. All 56 067 texts (recursive) lie strictly inside the die | `evidence/p5/misc.json`, `evidence/p6_texts.log` |
| Registration texts (TEXT 63/0, top) | "x=1414.0 um ; y=1414.0 um / Calculated area: 1.999396 sq mm" and "PDK version: IHP-Open-PDK 84374023…" at (5, 5) and (5, 1404) | `evidence/p5/misc.json` |
| Die area | 1.999396 mm² ≤ 2 mm². IHP's public community-MPW page states that the 2 mm² includes the seal ring, which is the basis used here | EdgeSeal boundary 39/4 = bbox |
| MIM.gR (recommended total MIM area; not implemented in the deck) | 10 368 µm² in 19 shapes, far below 174 800 µm² | `evidence/p5/misc.json` |
| IO ring composition | 24 pad cells (11 Analog, 3 In, 2 Out4mA, 1 Out16mA, 1 Out30mA, 1 Vdd, 2 Vss, 1 IOVdd, 2 IOVss), 4 corners, 112 fillers, 24 bondpads, unchanged from r2 | `evidence/p5/misc.json` |

## 5. Not run

- IHP's MPW rejection test or intake check on `7d07a784…` (PH-1; owner action).
- Bonding-house acceptance of pad size, pitch, wire angle and length, and paddle size (PH-2).
- Canonical LVS: not re-run (accepted IO-cell limitation, R13).
- Main DRC table on its own with `--disable_extra_rules`: not re-run. It is covered by the precheck run with the extra rules on.
- The macro power-pin probe in `p3_conn.py`: the result is **invalid** and not used. The label transform omitted the instance displacement. Macro power connectivity is covered by the projected LVS match.
- Tracing the OSC antenna diode to `vth`, device-level ESD path checks, and comparison of `retained_fullchip_bondpad_70x70_tm1` against a fresh PDK `bondpad` PCell: not run (as round 1).
- Full-chip PEX, IR drop and EM of the assembled chip: not run (outside this aspect).

# G1 evidence audit (red team), 2026-09-25

Independent audit of the public tape-out records against the evidence they cite.
Audited revision: `270f24b2` (HEAD at the time of writing; one commit, `270f24b2`,
landed during the audit and is included). Nothing was re-simulated; every check
below reads committed files, the JSON summaries and tail extracts under
`blocks/g1_top/sim/logs/`, and, where stated, the raw logs retained under
`${BULK}` per `review/local-retention-20260925.json`. No tracked file was modified.

Paths are relative to `designs/g1-guardian/` unless they start with `flow/`.

Severity: **blocker**: a sign-off or tape-in statement is false or rests on the
wrong object; **must-fix**: a public claim is contradicted by its evidence or by
another record; **should-fix**: missing disclosure, missing "not run" row or
number mismatch that does not change a verdict; **note**: minor.

## Summary of checks run

| Check | Result |
| --- | --- |
| RESULTS_20260925 counts vs `night_20260924_run/summary.csv` | passed: 162 jobs = 97 completed + 46 invalid + 16 timeout + 3 numerical; every job id in exactly one category; csv and job file have the same 162 ids |
| 72 matrix cells + 12 supply + §3/§4 trip rows: status, trip_d, GATE<1 V, GATE<0.33 V, cause, VDDA, wall vs log `TRIP`/`SUPPLY_uA`/footer | passed: all values match to rounding (script over 249 table rows) except the one row in M5 |
| Deviation flags in each cited JSON (`view_override`, `inpads`, `pads`, `osc`, `method`) vs table labels | passed for RESULTS tables; failed for the `c1414v1` headline row (B4) |
| Invalid rows "log contains mismatched XSPICE" | passed: confirmed in the raw logs in `${BULK}` (6 committed tail extracts do not show the line) |
| Retention manifest: 20 random entries re-hashed in `${BULK}` | passed 20/20; extended to all 423 entries: 423/423 match, 0 missing |
| Built-against versions from banners | ngspice-46, PDK `84374023`, Icarus 14.0 in all 456 g1_top logs; KLayout 0.30.9 in 1414 `run_drc.py` logs; kpex 0.3.12 in `kpex_console.log`; OpenSTA 3.1.0 in STA README: passed, with exceptions S13 |
| 1414 physical sign-off (DRC main/maximal/density/antenna, LVS pair counts) | passed: 0 lyrdb items, rc 0, all `Pad.*`/`Seal.*` 0 errors, projected LVS 61684/31173/22 Match, canonical NoMatch as reported |
| GDS identity | passed: `g1_chip_top_1414.gds` sha256 `629d303a…`, 84 500 250 bytes |

## Blockers

**B1. Digital timing "passed" is evidence for run7, not for the digital on the chip.**
`README.md:58-61`, `specification/G1_TOP_LEVEL_SPECIFICATION.md:135`,
`review/TAPEIN_PACKAGE_20260924.md:147`. `blocks/g1_ctrl/reports/sta_merged_sdc_20260924/sta.tcl`
loads run7 `layout/g1_digital.nl.v` (`fce14375`) and `g1_digital.nom.spef` (`42dbd018`), and
its README (l.7-9) says the 1414 GDS "keeps the same run7 macro unchanged". The signoff block
map (`blocks/g1_padring/reports/signoff-1414-20260924/README.md:142, 229-236`) shows the chip
digital is a different build: CTS/route/fill redone outside run7, nl `6181b988`, pnl
`4fd0b616`, SPEF `e6c89575`, GDS `1a662082`; run7 `layout/g1_digital.gds` `065b4504` has a
non-empty XOR against the chip. The fanout disposition (78 CTS buffers, STA README l.84/96) is
a run7 property; the chip CTS has max clock fanout 8 (`…/digital-postroute-20260923-r1/independent_sta_audit.json` in `${BULK}`).
The only timing run on the chip digital is the LibreLane post-route STA with the macro SDC on
OpenSTA 2.7.0 (setup +28.487 ns, hold +0.104 ns fast), cited nowhere at top level.
Merged chip SDC on the chip digital: **not run**. `blocks/g1_ctrl/README.md:3-7` also names
run7 `layout/` as "macro of record" and says nothing of the redone CTS; GLS on the chip netlist
is **not run** (signoff l.241) and is missing from spec §5 row "RTL / functional GLS" (l.122).

**B2. Canonical LVS failure is attributed to the PDK deck (R13) without evidence.**
`README.md:57-58, 144-146`, spec l.132, `TAPEIN_PACKAGE_20260924.md:143, 163-166`.
The signoff (`signoff-1414-20260924/README.md:112-119`) says the 14 NoMatch cells
(`sg13g2_Clamp_*`, `DCN/DCPDiode`, `LevelDown`, `LevelUpInv`, `RCClampInverter`) were compared
against reference `sg13g2_*` subckts while the canonical CDL carries `G1_VSS_DERIVATIVE__*`
variants, and that the failure "has not been investigated further". The chip's IO cells are
design-local copies with added PolyRes 128/0 and explicit-VSS derivatives, not stock cells.
R13 (`PLAN.md:191`) was written for stock cells; the tape-in question l.165 ("the rppd of the
secondary protection is not extracted") no longer describes cells that now carry PolyRes so
that rppd *is* extracted. Status should read **failed, cause not established**, not "PDK deck
limitation". Evidence: `signoff-1414-20260924/lvs_canonical/pair_counts.json`.

**B3. The cited sign-off block map contradicts the extractions used as chip evidence.**
`signoff-1414-20260924/README.md:137` (TRIP: "None. No CPEX of either new comparator"),
l.139 and l.255-262 (BGR: "No capacitance PEX", "CPEX was not run"), versus `README.md:82,84,148`,
spec l.124 and `blocks/g1_top/README.md:39-41`, which use BGR586 C-PEX (`g1_bgr586_pex.spice`
`01227a3d`, from `bank.gds` `e3ecfc62`, kpex 0.3.12) and TRIP NF4 C-PEX (`reports/pex/nf4/kpex_cc.log`,
cut of `60730627`). The extractions exist; the sign-off text is stale and is the document the
README names as "Sign-off and block-to-netlist map". Same staleness:
`blocks/g1_bgr/sim/system_checks_20260924/RESULTS.md` (Chip BGR section: extraction "does not exist yet").
Conversely **GATE**: signoff l.141 says the GATE PEX is **not bound** to the chip layout
(`kpex_plain.log` input `/work/build/g1_gate_lay/g1_gate.gds` at 09-19 09:37, rewritten 14:38,
now `ddf2c44a`), yet every chip-level deck uses `g1_gate_pex.spice` and RESULTS l.506 calls it
"GATE PEX"; `blocks/g1_gate/README.md:197` claims PEX ran "on `layout/g1_gate.gds`" and
`README.md:83` says "DRC and LVS clean, PEX done" with no disclosure. The unfilled GATE DRC/LVS
logs (09:34) also predate the last write of the GDS.

**B4. The headline tt/27 °C compact hard-fault row ran on schematic BGR and TRIP, labelled pex.**
`blocks/g1_top/README.md:75` ("`--netlist pex`, transistor-level front end … 1.345 µs … passed",
log `c_mid_pex_c1414_tl_tt_27C_clockfix_compact_functional_c1414v1.log`). The JSON
`effective.blockset_warnings` say: "WARNING bgr: no pex netlist exists for blockset c1414; using
the sch netlist", "WARNING trip: pex netlist … g1_trip_nf4_pex.spice does not exist; using the sch
netlist", "NOTE trip: NF4 schematic netlist (no parasitics)". The same 1.345 µs is independently
supported by `c1414fullc` (both extractions, `c_mid_pex_c1414_tl_tt_27C_clockfix_compact_functional_c1414fullc.json`,
1.34544 µs), so the number stands, but the row must cite `c1414fullc` or disclose the fallback.

**B5. T2F accuracy and frequency claims are not for the chip's bandgap.**
`README.md:85`, spec l.36, 96, 97, 119. `blocks/g1_t2f/sim/qualification/run_joint.py:15`
uses the Sep-19 `g1_bgr/sim/postlayout/g1_bgr_pex.spice`, not BGR586; 280/300 samples of
`mc300_summary.json` ran on an ngspice-47 image (not in "Built against"). The chip-relevant
campaign `t2f586-300sample-audit-20260923.json` has 237/300 completed, 63 numerical
watchdog failures (0 completed samples out of ±2 °C) and is cited nowhere. Frequencies with
BGR586 + T2F PEX: 1.5074 MHz at 25 °C, 4.9085 kHz/°C (`t2f586-nominal-calibration-20260922.json`),
consistent with the chip-level 1.518 MHz / 4.9 kHz/°C (RESULTS §7), not "1.59 MHz, 5.2 kHz/°C,
about 1.6 MHz". Residual −0.85…+0.17 °C and −2.5 °C/V are schematic values
(post-layout −3.26 °C/V; −1.26 °C at −40 °C with BGR586) and are unlabelled. T2F at −40 °C on
the chip netlists is **not run to completion**; T2F at 85 °C and at ss/ff: **not run** (absent).

## Must-fix

**M1. "The GDS is not in Git" is false.** `README.md:41`, `TAPEIN_PACKAGE_20260924.md:28`
("no … untracked"). `blocks/g1_padring/layout/g1_chip_top_1414.gds` is tracked since `10ee4868`
(84 500 250 bytes, `629d303a…`). The retention manifest (`local-retention-20260925.json`, entry
for `_src.gds`) also says "`g1_chip_top_1414.gds` … is the committed GDS of record".

**M2. Stale ss/125 °C, 1.08 V oscillator status.** `README.md:173-175` and
`blocks/g1_top/README.md:95` still say "not run (launch refused …, no log)". RESULTS §6 (after
`270f24b2`) and the committed JSON/tail record run `c1414oscv3` as not run to completion.

**M3. Wrong wall bound for `c1414oscv3`.** RESULTS l.354 ("wall bound 14 400 s", Wall 14400) and
l.398 ("14 400 s"); commit `e1627e8c` message too. JSON: `timeout_s 14000.0`, `wall_s 14000.17`,
footer "wall time 14000 s", status `timeout`. "Oscillator running" is not shown in the committed
tail or the retained raw log (no `CLOCK` line); the source is the untracked `.progress.jsonl`.

**M4. Block READMEs describe superseded variants as the block.**
- `blocks/g1_bgr/README.md`: entirely the Sep-19 bandgap (1.038 V, 22.0 µA, 84 × 124 µm,
  32-device LVS, 54/100 mismatch); BGR586 never mentioned.
- `blocks/g1_osc/README.md`: the 117 µm macro (9.919/8.994 MHz); R0.95, 111.15 µm, 9.436 MHz
  absent; state line "every corner reaches 10 MHz" contradicted by its own ss/1.08 V/125 °C 9.9748 MHz.
  `sim/qualification/README.md` and `reports/r095_physical_20260924/README.md` still call R0.95 unadopted.
- `blocks/g1_sense/README.md:3-6, 25-380`: rev-B only; comp45/R100 absent; l.350/376 antenna
  "failed (9 markers)" from assembly-1350 (chip antenna passed).
- `blocks/g1_trip/README.md:3-12, 359-372`: two identical 12/0.34 StrongARMs; NF4, regenpair4,
  the 40–56 LSB offset absent. `sim/postlayout/README.md:94` "hard threshold not bracketed: not run"
  contradicted by its own l.103-128.
- `blocks/g1_gate/README.md:3-8, 243, 253-261`: IO-first "open", density/antenna "not run",
  power-up "not repeated post-layout" contradicted by l.258-261.

**M5. Sign-off padring and padframe records present the 1350 µm frame as current.**
`blocks/g1_padring/README.md:3-19, 65, 75, 170-176, 192, 267-274`; `blocks/g1_padring/INTEGRATION.md:4`
("1200 × 1200 µm ring"), 11, 97-99, 213-215, 263; `padframe/README.md:85-103` (antenna failed 9,
`Pad.fR` failed 60, core-only LVS 52 pairs, present tense); `PLAN.md:121` D13 "Die is 1350 × 1350 µm"
is the last die decision, there is no 1414 decision, progress log ends 2026-09-20 (l.41).

**M6. Tape-in package §7 board constraints cite superseded schematic evidence.**
`TAPEIN_PACKAGE_20260924.md:155-156` ("schematic only. Post-layout power-up not run";
"VDD-first without it did not converge") from `review/G1_DESIGN_REVIEW.md` (21 Sep, 1350 chip).
Chip netlists: gB core-first without pull-down passed, `GATE` ≤ 0.0725 V
(`gB_pex_c1414_beh_tt_27C_clockfix_functional_c1414n1.log`); IO-first 3.28–3.30 V (RESULTS §5).
Spec §5 l.109 also names `G1_DESIGN_REVIEW.md` as the evidence index.

**M7. Bond map not bound to the chip; padframe links the older CSV.** `padframe/README.md:5, 13-14`
links `bondmap_candidate_20260923.csv` (`ab02b653…`); the tape-in uses `_r2` (`3e363438…`);
neither is `629d303a`. Recorded as open in the tape-in (l.122); padframe README should say so.

**M8. SENSE area is wrong.** `README.md:81` "0.048 mm² (Sep-19 layout)". Chip SENSE cell bbox
384.3 × 238.7 µm ≈ 0.092 mm² (`signoff-1414-20260924/blockmap/block_xor.json`).

**M9. Feasibility envelope target is outside the calibration contract.**
`specification/FEASIBILITY_DEMO_ENVELOPE_20260922.md:12` "hard 40 mV": code ≈ 204 + 40–56 LSB
offset = 244–260 > 255; spec l.95/169-171 give the usable range as about 25–40 mV and require a
search ≥ 56 codes above target. `specification/G1_REGISTER_MAP.md:157, 189` still describe the
reset code 0xFE as 49.8 mV / 2.0× nominal with no effective-threshold note.

**M10. Measurement plan uses the Sep-19 bandgap number.** `measurement/README.md:190` "about
9.07 mV of core-reference droop with a 10 MΩ load"; source `review/audits/VREF_PAD_LOADING_20260922.md:44`
says it applies to the baseline only (Rout 76–101 kΩ vs BGR586 ≈ 22 kΩ).

**M11. Chip-level evidence was produced by eight runner versions, one committed.**
RESULTS l.10-11 says "plus the uncommitted `run_top.py` recorded by `runner_sha256`". The cited
JSONs carry `runner_sha256` `d6bd5574` (25 rows), `bc15450b` (68, = committed), `ac9c1c45` (34),
`f9e56cae` (38), `9147f75b` (24), `25f47d21` (11), `dcc31f41` (4), `38fdf715` (45 invalid);
`c1414v1` used `4438037a`, `c1414n1` b/d used `8d87feef`. Only `bc15450b` exists in any
commit; the others and the generated decks (`/work/build/g1_top/*.cir`, `deck_sha256`) are
neither committed nor in the retention manifest. Most matrix cells cannot be regenerated from
the repository.

**M12. `CDL-vs-deck connectivity audit: 0 unexplained differences` has no committed output.**
Spec l.124, `blocks/g1_top/README.md:63-68` (and device fingerprints 1036/159/2305/78). No log,
JSON or text output of `sim/check_cdl_vs_deck.py` exists in the tree.

## Should-fix

- **S1. Spec §5 omits rows that are not run** (reporting rule): IR drop/EM, package/bond-wire
  parasitics, IO-ring XOR vs stock cells, GLS on the chip netlist (B1), trip path with the
  transistor-level oscillator, T2F at 85 °C / ss / ff and −40 °C (not run to completion), stock-pad
  3×/4× faults (RESULTS §3a, not run to completion), supply extremes on `b_s`/`f_mid`/`c`/`e20`
  (RESULTS l.194), default 1 ms `SOFT_TIME` on the transistor-level front end, hard-comparator
  (regenpair4) post-layout delay and NF4 at ff, ESD/latch-up and ERC checks. All are in README
  prose or RESULTS but absent from the gate table.
- **S2. Deviation lists omit the behavioural output pad.** README l.137 and spec l.93/124 list
  ideal clock, `nodcn`, `bgr=sch` but not that `GATE`/`FAULT_N` are fitted behavioural drivers
  (`effective.outpads = beh` in every trip JSON), although `GATE` < 1 V timing depends on that pad.
  `bgr=sch` is also a netlist with 329 Sep-19 capacitors (JSON NOTE), not a plain schematic.
- **S3. Oscillator spread exceeds the §6 frequency window.** Chip-context R0.95 at trim 8: 7.61 MHz
  (ss/125 °C) and 12.43 MHz (ff/−40 °C) (`CLOCK` lines, RESULTS §6), outside the 8–12 MHz range
  used in spec §6 l.148; trip timings "at every corner" (1.306–1.361 µs) use the fixed 9.436 MHz.
  Disclosed as "ideal clock", but no statement of the corner trip time with the corner clock.
- **S4. Offset/calibration numbers differ between records.** README l.72 "8–9 mV"; RESULTS
  8.0–9.25 mV (41–47 LSB); spec l.95/l.169 "calibrated code about 45–50 codes above" while the
  block bench gives 40–56 LSB. Code 200 = 39.25 mV assumes VREF 1.04 V; with BGR586 1.04546 V it is
  39.45 mV. Offset bracket −3.9…+0.77 mV (README l.82) is referred to `icmp`, not the shunt; unsaid.
- **S5. OSC 10.445 MHz (README l.89, spec l.104)** comes from the pre-CPEX candidate netlist
  `f08bf051` (`runs/osc_actual_receiver_slowhot_c0_r095_20260922_01/manifest.json`); the new CPEX
  gives 10.447 MHz (`fulltree_r095_load_20260924/results/slowhot_code0.json`). Conditions
  (ss, 1.08 V, 125 °C) unstated. OSC isolated filled-macro density-only check **failed** (8 markers)
  and its kpex internal LVS failed (`reports/r095_physical_20260924/README.md`); absent from README l.89.
  The 9.436 MHz load includes an estimated 459.8 Ω / 60.4 fF root route.
- **S6. BGR citations and ranges.** Spec l.35 cites `README_bgr586_pex.md` for 22.3 kΩ; the value
  is in `sim/system_checks_20260924/RESULTS.md`. README l.140 "100 nF about 12.5–13.2 ms" vs spec
  P5 l.201 "12.0–13.2 ms" (`bgr586/summary.json` has 11.84–11.96 ms at ff/−40). P5 0 nF "7–8 µs"
  mixes stock-pad (7.0 µs ff/−40) and pad-less stand-in values (tt/27 stock pad did not converge),
  a caveat P4 states and P5 does not. "DC identical to the schematic" (README l.84) is the only
  PEX-vs-schematic check; AC/PSRR/start-up on the PEX netlist: not run.
- **S7. SENSE numbers.** README l.81 "calibrated residual ≤ 498 µV" omits "ideal continuous
  room-temperature correction" (`R100_MC_100_20260923.md:19-21`); SENSE README gives 982/976 µA
  (rev-B) vs chip-level 1101.4 µA; R100 slow/low/cold bandwidth 2.28 MHz and settling 306.5 ns
  appear only in `RZ100_PARTIAL_FIELD_20260923.md`, which still says R100 is "not adopted".
- **S8. Retention manifest.** `review/local-retention-20260925.json`: `file_count` 422 vs 423
  entries, `total_bytes` excludes the added entry, which uses a different schema (`size`/`bulk`
  vs `size_bytes`/`bulk_copy`). `not_inventoried: "Nothing"` is not true: the 245 c1414
  `.progress.jsonl` (1.5 GB, gitignored, cited in RESULTS l.6/11 for `runner_sha256`), the 851
  c1414 wave files under `sim/results/waves/` whose hashes the JSONs record, and the decks are
  neither committed nor inventoried.
- **S9. RESULTS internal staleness.** l.15-17 "the summarizer marks runs completed by the footer
  only": `launch_matrix.py:389-409` now flags `cosim mismatch` and `summary.csv` marks
  `f_mid_ss_85C_c1414m` "failed (invalid)". l.538 "Cells still running" vs l.21 "0 running".
  README l.63 "passed the tt/27 °C cases run so far".
- **S10. Power-up side observation not reported.** In gB/gB_pd at ss/125 °C and ff/−40 °C the
  `tripped` node reaches 1.20 V while EN is low (`POWERUP … tripped_max= 1.20`), vs 0.354 V at
  tt/27 (`c1414n1`). `GATE` stays low, so the verdict holds, but `FAULT_N` behaviour during
  power-up is not reported.
- **S11. `blocks/g1_top/README.md:3-16, 139`** header still says "built and run (2026-09-19),
  schematic netlists … No layout exists"; clock "9.919 MHz schematic, 8.994 MHz post-layout" with
  no legacy label.
- **S12. DOSE ELT still an "approval-gated alternative"** in README l.86 and
  `blocks/g1_dose/README.md:3-6, 36-41`; spec l.37 and tape-in l.173 exclude it.
- **S13. Built-against gaps.** OpenSTA 2.7.0 (the only chip-digital STA, B1) and ngspice 47
  (T2F MC, B5) are not listed; two `.sch` headers are 3.4.6RC (`blocks/g1_sense/source/TO_Nov2024_BG/OTA3C.sch`,
  `OTA33_BiAS.sch`); g1_top JSONs have `image_id: null`, so the container identity is not
  recorded per simulation; Icarus is a `-dirty` build. `PLAN.md:70` and padring README l.254
  give container digest `5fd78498…` vs README `ddeb6957…`.
- **S14. TMR separation "≥ 27 µm"** (README l.88) is run7 placement
  (`reports/librelane_run7/tmr_separation.txt`); the chip digital is only shown to meet 20 µm.
- **S15. Measurement / package counts.** `measurement/README.md:4` "20 packaged parts" vs tape-in
  l.124 "10 packaged parts, specified" (the spec states no count).

## Notes

- N1. Six invalid-job tail extracts (`e20_tt_85C`, `e20_ss_125C`, `e20_ff_85C`, `c_mid_tt_85C_r2`,
  `c_mid_ss_125C_r2`, `c_tt_85C_r2`) do not contain the "mismatched XSPICE" line; the retained raw
  logs do. Consider adding the line to the extracts.
- N2. Every TRIP comparator log carries rppd OSDI "voltage is greater than specified by vmax"
  warnings (1574 lines in the NF4 tt log); not disclosed. NF4 postlayout ngspice logs carry no
  version banner (only the results file header).
- N3. `README.md:81` "three PMOS-input OTAs" vs spec l.32 "a 3.3 V PMOS-input OTA".
- N4. `padframe/README.md:71-72` "lead directly opposite": north and west pad order in the CSV is
  not one continuous rotation; a pad-to-lead table is needed.
- N5. SOURCES.md:10 licence "Solderpad" vs padring README l.123 "Apache-2.0 WITH SHL-2.1";
  SOURCES:16 and PLAN:98 call G1_OSC a ring-oscillator derivative (it is RC relaxation).
- N6. Measurement README typos (missing spaces) at l.143, 147-148, 168-169, 219.
- N7. `blocks/README.md:3-17` lists every block as "not started".

## Verified as stated

- 72/72 matrix cells: every cited log completed with the stated cause and timing; `GATE` < 1 V
  1.333–1.335 µs (hard, nominal supply), 1.306–1.361 µs with supply extremes; b_s 27.93 µs;
  f_mid re-arm 0.61 µs, 1 A; q no trip, gate_min = IOVDD.
- VDDA 957–2188 µA, 1421.11 µA tt/27 (BGR 319.704, SENSE 1101.4); BGR 218.7–484.0 µA.
- Power-up: gA/gA_pd 3.2826–3.3000 V for 4.21–4.37 µs; gB 0.0725 / 0.0029 / 0.0135 V, gB_pd 0.0090 V.
- Threshold sweep: no trip at 30.00 mV, trip at 31.25 mV (1.546 µs); block bench 40–56 LSB,
  hold2x −21 to −25 LSB.
- BGR586: 1.04546 V, 4.134 µA, 319.69 µA, 8.53 ppm/°C; 299/300, max 46.878; Rout 19.3/22.3/25.8 kΩ;
  settling 1.256/1.201/1.324 ms; block LVS passed (KLayout 0.30.9).
- SENSE R100 MC 100/100, gain 19.905–20.050, 498 µV (source `bb933fda` = chip source).
- NF4 delay 1.6935 ns; TRIP macro-cut LVS passed.
- run7: GLS 13 tests/193 checks, 360 × 360 µm, 46 pins, 0 DRC/antenna/XOR, TMR min 27.4 µm.
- Physical sign-off on `629d303a`: as reported, including canonical LVS **failed**.
- Retention: 423/423 bulk copies hash-match.

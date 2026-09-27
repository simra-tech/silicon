# Red team 2026-09-27, aspect `evidence`: correctness and honesty of the G1 evidence package

Auditor: independent verification agent. Repository `${REPO}` at the 27 Sep head of branch `redteam-20260927`.
Scope:
- `README.md`, the spec status tables and `review/TAPEIN_PACKAGE_20260924.md`;
- the block READMEs changed since r3;
- `RESULTS_20260925.md` §10–§13, `FULLCHIP_CDL_R3_20260926.md` and `FULLCHIP_CDL_R3_CORNERS_20260927.md`;
- `review/local-retention-20260925.json`;
- git history.

The earlier audits (`review/redteam-20260925/EVIDENCE_AUDIT*.md`) were not redone. Their clean rows were sampled, and everything committed after `30f5192a` was audited.
Paths below are relative to `designs/g1-guardian/` unless they start with `${REPO}`.
**No new simulation was run.** Every number below comes from committed logs, JSONs and tails, from `${BULK}` retained copies (re-hashed here), or from git.

## 1. Verdict

**Yes: r3 (`7d07a784…`) is safe to submit as-is for this aspect.**
- No finding changes the GDS or questions a silicon function.
- Every "passed" row I sampled points to a committed log or JSON, or to a hash-verified retained copy, and the quoted numbers match it to rounding. That covers 40 completed r3full/r3x runs, pi5, gS, the SDF corners, formal equivalence, the BGR586 AC run, r3 DRC/LVS and STA.
- All 122 retention entries I re-hashed match (r1 and r2 GDS, every r3full, r3x, eco4, gap, equivalence and BGR-AC entry).
- All r3 decks hash-match their JSON `deck_sha256`, and every run's `rtl_sha256` equals the frozen ECO RTL at HEAD.

The package is not clean, though:
- **Several records contradict each other:**
  - SDF-corner GLS and formal equivalence are recorded as "not run" in the README, the tape-in package and one spec row, but as "passed" in two other spec rows.
  - The README's r3full not-run list is stale.
- **One headline number is wrong:** "pi-RC wiring adds about 10 ns" compares different timelines. Like-for-like, the difference is −0.04 ns.
- **One "not run" item was silently dropped:** the trip path with the real oscillator at ss/ff.

All findings are documentation or policy fixes, together about 4–6 h.

## 2. Findings

| ID | Title | Severity | Evidence | Proposed fix | Effort / GDS |
|---|---|---|---|---|---|
| E3 | SDF fast/slow GLS and formal equivalence are "not run" in three records and "passed" in two others | MINOR | "not run": `README.md:107`, `specification/G1_TOP_LEVEL_SPECIFICATION.md:137`, `review/TAPEIN_PACKAGE_20260924.md:170` and `blocks/g1_padring/reports/signoff-1414r3-20260926/README.md:270-271`. "passed": spec `:162`/`:163`. The logs support passed: `blocks/g1_ctrl/sim/gls_eco_r3v2/sdf_corners/tb_g1_digital_eco_gls_sdf_r3cand2_{fast,slow}.log` "SUMMARY tests_pass=21 tests_fail=0 checks=260"; `equiv/dprove.log` "Networks are equivalent"; negative control "not equivalent", frame 17. Commit `200fe17b` updated only spec rows 162/163 | Update the four stale rows to "passed" with the evidence paths | 0.3 h; no GDS |
| E4 | pi-RC interconnect "adds about 10 ns" compares different timelines and a wrongly named baseline | MINOR | `blocks/g1_top/sim/campaigns/RESULTS_20260925.md:667`, spec `:141` and commit title `5faa7096` say pi5 `GATE` < 1 V 1.4514 µs is "about 10 ns above the C-only interconnect … 1.4393–1.4411 µs (§10)". The §10 `eco4` runs use the **baseline** timeline and the **estimated** wiring (`interconnect: estimate`), not the extracted C-only interconnect. Like-for-like, compact timeline and same RTL, is `eco_c_mid_m03`: `t_trip_d` 1.16385 / `t_gate_1V` 1.45142 µs vs pi5 1.16372 / 1.45138 µs, i.e. **−0.04 ns** (`evidence/pi5_like_for_like.txt`). The whole +11 ns is the decision-strobe phase (`trip_d` 1.1525 vs 1.1637 µs). §9 had already retracted the same error ("the earlier ≤ 10 ns compared different timelines") | Restate as "pi-RC vs the same compact deck without extraction (`eco_c_mid_m03`): −0.04 ns"; the conclusion (wiring R is not a timing factor) stands and is stronger | 0.2 h; no GDS |
| E5 | Real-oscillator trip path: the ss/ff part was dropped from the not-run list when tt passed | MINOR | At `30f5192a` spec §5 had "Trip path with the transistor-level oscillator in the loop, chip netlists: not run". Now spec `:166` and `README.md:262` say **passed**, which covers tt/27 °C only. The r3x record (`blocks/g1_top/sim/FULLCHIP_CDL_R3_CORNERS_20260927.md:121`) and RESULTS §12 (`:655`) list "real oscillator at ss/ff (trip path): not run", as does spec §6 ("trip time with the corner clock: not run"). The oscillator spans 7.61–12.43 MHz over corners, so this is the case that moves the timer windows | Add "ss/125 and ff/−40 °C: not run" to spec `:166` and `README.md:262` | 0.1 h; no GDS |
| E6 | README's r3full not-run list is stale and contradicts the next paragraph | MINOR | `README.md:128` still lists as not run: the trip path with the transistor-level oscillator, "power-up gB/gB_pd/gA at ss/ff", "near-threshold points at corners", and "`f_mid`/`b_s`/`hard_pulse` at corners". `README.md:130`/`:262` (r3x) record these as run, except gA at ss/ff. `RESULTS_20260925.md` §11 (`:629-634`) has the same list but is a dated section followed by §12. The spec's merged row (`:141`) is correct | Replace the README list with the spec `:141` wording | 0.2 h; no GDS |
| E7 | TAPEIN says the r3 DRC evidence is "bulk only; not committed; not in a retention manifest". It is committed | MINOR | `review/TAPEIN_PACKAGE_20260924.md:162-166`. In fact `blocks/g1_padring/reports/signoff-1414r3-20260926/{drc_main,drc_maximal,precheck,density,antenna}/` are tracked: run logs, lyrdb, 0 `<item>` in each lyrdb, hashes `3da5e270` / `f54b65a5` / `92416e92` as that README states. `input_gds.sha256` and `.after` = `7d07a784…` | Point the five rows at the committed copies | 0.1 h; no GDS |
| E9 | Near-threshold ff/−40 °C bracket rests on a run whose JSON says `running` | MINOR | `blocks/g1_top/sim/logs/cdl_c_mid_pex_ff_-40C_…_icx_fm1p1_maxstep1ns_functional_r3x.json`: `status` "running", `last_reported_sim_time_s` 2.797e-5. Its tail has the end-of-run measures (`tripped_max` = 6.04 mV, trip/`GATE` measures "out of interval" = no trip). The record discloses the truncation at `FULLCHIP_CDL_R3_CORNERS_20260927.md:50`. The summaries (README `:130`, spec `:141`, `:257-259`, RESULTS `:651`) state "not at 27.5 mV" without the caveat | Add "(transient complete, log truncated by the quota stop)" wherever the 27.5 mV bound is quoted, or re-run (≈ 2.5 h on one CPU) | 0.1 h (or a 2.5 h re-run); no GDS |
| E10 | Count and label inconsistencies | MINOR | (a) "28 runs" for r3x (README `:130`, spec `:141`, TAPEIN `:173`): the logs hold 36 r3x/r3x2 JSONs, 30 `completed`, 4 `running` (quota), 2 `failed`; 28 matches no count. (b) spec `:143` "passed, 15/15 done except the CDL run" vs RESULTS §10 "14 of 15". (c) RESULTS `:655` "4 of 20 seeds" vs the joint-MC RESULTS: 22 calibrated seeds, all 22 reached the 125 °C residual probes. (d) README `:118` and spec `:143` put "`GATE` < 1 V 28.040 µs" next to "baseline 27.65 µs", but the baseline is the pre-ECO `trip_d` (27.646 µs); the pre-ECO `GATE` < 1 V was 27.934 µs (RESULTS `:146-157`) | Correct the four statements | 0.3 h; no GDS |
| E11 | Hold slack quoted at the slow corner only | MINOR | README `:99`, spec `:155` and TAPEIN `:161`/`:171` quote "setup/hold slow 28.45/0.337 ns". The worst hold is **0.114 ns** at the fast corner (`blocks/g1_padring/reports/signoff-1414r3-20260926/macro/sta_chip_merged_fast.tsv` `worst_hold_ns 0.11405776`; `summary_main.txt` `timing__hold__ws = 0.114`), nominal RC only | Quote the worst corner: "hold ≥ 0.114 ns (fast, nominal RC)" | 0.1 h; no GDS |
| E12 | Retention manifest header still inconsistent | MINOR | `review/local-retention-20260925.json:3999-4000`: `file_count` 516 and `total_bytes` 967 113 973, against 570 entries and 1 028 953 454 bytes. 10 entries use the old schema (`size`/`bulk`); 3 paths appear twice (`*_c1414thr3.log`). The cdlv2 log entry (`:3040`) records 728 320 bytes, but the retained copy is 728 352 bytes with the recorded sha256 `a772028d…` (the hash matches, the size field is wrong) | Recount the header; normalise and de-duplicate | 0.2 h; no GDS |
| E13 | r3x runs came from a runner that was never committed | MINOR | 26 of the 30 completed r3x runs record `runner_sha256` `5d054dfd`. The only `run_top_cdl.py` versions in git are `76e88396` (HEAD, 8ad24f68), `c54a0beb` and `e2d75a88`. Mitigation: all 36 decks are committed and hash-match `deck_sha256` (checked), and RESULTS makes the deck the record. The r3x record does not state this; the earlier audit's S2 raised the same point for r3full | One sentence in the r3x record | 0.1 h; no GDS |
| E14 | Simultaneous ramp only with an ideal `EN` copy | MINOR | Spec P1 (`:300`) allows `VDD` "together with" `IOVDD`. Its evidence is `gS` on the hand-wired deck with an ideal `EN` copy (RESULTS `:364`, `:370-380`). With the real `EN` pad, `en_i` floats to 0.84–0.94 V while `IOVDD` is absent (r3full/r3x gB). No `gS` on the r3 CDL deck, and it is not in any not-run list. The gS `GATE` peak is 0.545 V with `EN` low | List "gS on the r3 full-chip deck (real `EN` pad): not run"; optional run (~1 h on one CPU, like gB) | 0.1 h (+1 h run); no GDS |
| E15 | Spec parameter "Die" still cites the r1 file | MINOR | `specification/G1_TOP_LEVEL_SPECIFICATION.md:102`: "`g1_chip_top_1414.gds`, `629d303a…`" (r1). The chip of record is r3 `7d07a784…` | Cite r3 | 0.05 h; no GDS |

## 3. Per finding

**E3.** Read the four records, the two SDF-corner logs, the two red-team SDF logs, `equiv/dprove.log`, `equiv/dprove_negctl.log` and `equiv/run_equiv.out`. The input hashes are `4b83f181…` (netlist) and the RTL `33d549da`/`4e3b8ff6`/…, the same as the `rtl_sha256` of every r3 simulation. The contradiction understates the evidence, but a reviewer reading the tape-in checklist (TAPEIN `:170`) would see two digital closure items as open.

**E4.** Ran `evidence/pi5_like_for_like.txt`: the JSON `options` (timeline, interconnect) and the `TRIP` lines of the three runs. Latch-to-`GATE` time is 0.2849 µs for pi5, 0.2853 µs for m03 and 0.2853 µs for eco4 tt. The number is wrong, but the engineering conclusion survives. It matters because the same mis-comparison was retracted once already (§9) and is now in a commit title.

**E5.** `git show 30f5192a:designs/g1-guardian/specification/G1_TOP_LEVEL_SPECIFICATION.md` was diffed row by row against HEAD. No row was removed. The only row whose "not run" count fell is this one, from 1 to 0.

**E6.** Read `README.md:122-131`.

**E7.** Ran `git ls-files blocks/g1_padring/reports/signoff-1414r3-20260926/`, `grep -c '<item>'` on the five lyrdb files (0 each) and `sha256sum layout/g1_chip_top_1414_r3.gds` (`7d07a784…`, equal to `input_gds.sha256` and `.after`).

**E9.** Read the JSON and `.tail.txt`. The measures appear only after `tran` completes, so the 28 µs transient did finish. The missing footer is a logging truncation.

**E10.** Ran a status tabulation over `logs/*_r3x*.json`, and read `joint_r3_mc_20260926/RESULTS.md` and RESULTS §1 `b_s`.

**E11.** Read the six `sta_*.tsv` files and `summary_main.txt`.

**E12.** Parsed the manifest with Python, checked every `bulk_copy` path exists (570/570) and re-hashed 122 entries: 0 mismatches.

**E13.** Compared the `runner_sha256` of every r3x/r3full JSON against `git show <c>:…/run_top_cdl.py | sha256sum` for every commit touching the file. Also re-hashed every committed deck against its JSON `deck_sha256`: 0 mismatches for completed runs. The one mismatch is the already-invalid `eco4_cdl_c_mid_ser4`.

**E14.** Read RESULTS §5 and the spec P1 row; `gS` `POWERUP` line: `GATE_max_EN_low= 0.545348`.

**E15.** Read the spec line.

## 4. Checked and clean

- r3 GDS in the tree hashes to `7d07a784…`; the r3 CDL to `5e47ae02…`; the interconnect to `ddc88cc7…`.
- r3full (earlier audit) and r3x numbers against the tails, all to rounding:
  - c_mid tt/ss/ff 1.5431 / 1.7264 / 1.4334 µs;
  - c/e20 1.5316 / 1.5318 µs;
  - b_s 27.752 / 28.131 µs, and at ss/ff 28.315 / 28.022 µs;
  - f_mid ss/ff 1.7151 / 1.4223 µs;
  - supply extremes 1.5466 / 1.5429 µs;
  - `osc tl` 1.1211 / 1.5004 µs;
  - ss 1.25× 1.7995 / 2.3620 µs;
  - ff 1.15× trips 1.4336 µs;
  - hard_pulse latch max 54 / 49 mV;
  - gB ss `en_i` 0.935 V.
- All 36 r3x JSONs, including the failed and stopped runs, are tracked; nothing over 300 kB is tracked in `sim/logs` for r3full/r3x.
- `rtl_sha256` of every completed r3full/r3x/eco4/pi5 run equals the frozen ECO RTL files at HEAD.
- Retention: 122 of 570 entries re-hashed against `${BULK}`, 0 mismatches. They include the r1 GDS `629d303a`, the r2 GDS `9049e87b` and the source candidate `60730627`; all 570 bulk paths exist.
- SDF slow/fast GLS: 21/21, 260 checks; red-team R3 fails as documented. Formal equivalence: proven, and the negative control is not equivalent.
- BGR586 extraction AC: PBIAS phase margin 107.38–111.80° (`bgr586_ac_20260926/summary.json`), matching "107.4–111.8°".
- Joint MC summary (16 / 4 / 4; hard offset +7.95 mV, sd 1.06 mV; 262 guard probes) matches its RESULTS.
- `gS` 0.5453 V matches its log.
- STA setup 28.45 / 25.70 ns matches the TSVs.
- Tracked files contain no `/home/`, `/opt/sim` or `/Users/` paths (only in path-guard assertions of export scripts), no username, and no credentials (patterns for GitHub/AWS/Slack tokens and private keys). The only e-mail addresses are tool banners (Icarus, Yosys), one upstream third-party address and the project address. No pricing, customer or competitor content in tracked markdown.
- `.private/` is gitignored and has never been committed (`git log --all -- .private` is empty).
- The spec's §6 near-threshold disposition is honest: ff/−40 °C is labelled **failed** against §6 as written, and 1.25× is not counted as a pass.

## 5. Not run

- No simulation was re-run (CPUs 32–35 unused). The ff 1.10× re-run (E9) and a `gS` run on the r3 deck (E14) are proposed, not done.
- The identity of `133ecf65` in `review/audits/reuse-20260921.json` was not established.
- The derivation of the r3x power-up latch windows (2.90–5.82 µs etc.) and the calibration `cmp_hard`/`cmp_soft` first-decision times was not checked. They appear to come from waveform files not in `derived_wave_numbers_20260926.json`, the same pattern as the earlier audit's S3.
- Block READMEs not changed since `30f5192a` (DOSE, DUT, GATE, OSC, SENSE, SEU, T2F) were not re-audited beyond the earlier audits.

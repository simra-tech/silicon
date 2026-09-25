# G1 evidence audit, r3 chip of record (red team, re-audit)

Scope: what changed between `840dd681` and `7219e7e5` (HEAD at audit time): the r3 chip of
record `blocks/g1_padring/layout/g1_chip_top_1414_r3.gds`, `reports/signoff-1414r3-20260926/`,
the r3 CDLs, the r4 bond map and `BONDPLAN`, `TAPEIN_PACKAGE`, `PLAN.md` D15/D16, README/spec
updates, the ECO records (`blocks/g1_ctrl/ECO_20260925.md`, `ECO_FLOW_FEASIBILITY_20260925.md`,
`flow/eco/`, `rtl_eco_20260925/`, `sim/eco_20260925/`, `sim/gls_eco_r3v2/`), register map 1.2,
spec §5/§6, `blocks/g1_top/sim/FULLCHIP_CDL_20260925.md`, the interconnect extraction records
and RESULTS_20260925 §9. Same method and severity scale as `EVIDENCE_AUDIT.md`. Committed content
was read with `git show 7219e7e5:<path>`; the working tree carries uncommitted edits from another
session, which are **not** counted as evidence. Bulk (`${BULK}`) is the operator's external root.
Nothing tracked was modified. Paths are relative to `designs/g1-guardian/`.

## Checks run

| Check | Result |
| --- | --- |
| r3 GDS sha256 / size vs README, sign-off, tape-in, bond map | passed: `7d07a784…`, 84 097 180 bytes, tracked at HEAD; bulk copy identical |
| r3 canonical CDL, projected reference, r2 CDL | passed: `5e47ae02…`, `d0d36c84…`, `41d47877…` |
| Bond map r4 | passed: `99080d81…`; differs from r3 CSV only in the hash column; 24/24 rows bound to `7d07a784…`; `verify_bondmap_r4.json` `all_ok: true` |
| r3 DRC main/maximal/density/antenna/precheck | passed: bulk lyrdb hashes `3da5e270`/`f54b65a5`/`89149c55`/`71533d82`/`92416e92`, 0 items, rc 0 (bulk only, see M4) |
| r3 LVS pair counts | passed as stated: projected 62 940 / 31 816 / 22 Match; canonical 14 NoMatch identical per circuit to r2, +`sg13g2_antennanp` Match |
| r3 XOR vs r2, fill | passed: outside macro only 5/22 (+100, 700 µm²); GatPoly 14.9959 → 15.0309 % |
| RTL hashes (9 files), macro views (10 in `final_views.sha256`) | passed |
| Macro STA, GLS, RTL test counts | passed as stated, except S1/S2 below |
| CDL-deck and `c1414icx` numbers vs tails/JSON/`results_cdl.txt` | passed (values), provenance findings below |
| Retention manifest `local-retention-20260925.json` | 450/450 bulk copies hash-match; header still says `file_count` 423 |
| Private/machine absolute paths in tracked files changed since `840dd681` | none (only container `/foss`, `/work`); two pre-existing log hits outside scope (`blocks/g1_bgr/reports/fill/fill_g1_bgr.log`, `review/audits/digital-closure-evidence-20260923-r1/…/odb-checkdesignantennaproperties.log`) |

## Blockers

**B1. The chip-level ECO runs that justified promoting r3 have no committed or retained evidence.**
`README.md:106-109`, spec §5 row "Chip-level runs with the ECO RTL" (l.142, cites `results_top.txt`),
`signoff-1414r3-20260926/README.md:17-21`, `TAPEIN_PACKAGE_20260924.md:172`, `PLAN.md` D16,
`blocks/g1_ctrl/ECO_20260925.md:214-220`. At HEAD no `*rtleco20260925*` log, JSON or deck is tracked,
none is in either retention manifest, and `results_top.txt` has no ECO entry (`git diff 840dd681 7219e7e5`
leaves it unchanged). The files exist only untracked in the working tree; their values do match
(`eco_c_mid_m03`: `t_tripped_us= 1.16616`, `t_gate_1V_us= 1.45142`, frozen RTL `33d549da`/`4e3b8ff6`;
`eco_hard_pulse_m03`: `cause= 0`, `gate_end= 3.3`).

**B2. Register map and spec §6 still say the chip of record implements map 1.1.**
- `specification/G1_REGISTER_MAP.md:9-13` ("until then the chip of record (`6181b988`) implements version 1.1"), `:244` ("the chip of record reads 0x11"; RTL `g1_regfile.v:107` returns 0x12), `:419`.
- Spec §6: "Register map 1.2 … applies after the `g1_digital` macro is re-hardened, not to the chip of record"; P7 "Chip of record (map 1.1): default 0x14, about 1 ms"; `OSC_CTRL[4]=0` can stop the clock (tied to 1 in `g1_regfile.v:130`); H2/H4 still required without a 1.2 qualifier; P6/P8 describe the 1.1 EN reset.
- `TAPEIN_PACKAGE_20260924.md:196` ("Every EN rise re-opens the ~1 ms inrush window") and `measurement/README.md:57, 145-148, 157-163` (1 ms mask, unfiltered EN glitch reset) are 1.1. The board/firmware contract shipped with r3 contradicts its own RTL.

**B3. The ECO chip-level runs are described as "extracted chip"; they are the hand-wired deck with deviations.**
README l.106, spec l.142, tape-in l.172. The `eco_c_mid_m03` JSON: `--blockset c1414`, `view_override bgr=sch`,
`inpads nodcn`, `outpads beh` (fitted `GATE` driver, about 7 % optimistic by the project's own figure), ideal clock.
None of these deviations is stated where the 1.166/1.451 µs figures are quoted. The ECO record (l.205) states the command correctly.

## Must-fix

**M1. "r3 is not yet committed" is false.** `README.md:64`; `TAPEIN_PACKAGE_20260924.md:30`
("r3: not yet committed … r3 open"). `git ls-tree 7219e7e5` lists `g1_chip_top_1414_r3.gds`, 84 097 180 bytes, blob sha256 `7d07a784…`.

**M2. Chip-context STA reports "0 violations" but the bulk reports show failed items.** r3 sign-off l.102/170,
spec §5 "Digital timing", README l.98-100. `$R/sta/main/chip_merged-{typ,fast,slow}`: 12 max-slew violations per corner
(analog pads, e.g. `pad07_vdda/pad 3.5000 200.0000 -196.5000 (VIOLATED)`) and "Found 98 unannotated drivers". The pre-ECO row
reported the same classes as "failed, dispositioned"; the r3 rows dropped them.

**M3. Headline trip response uses the r1 CDL and the pre-ECO RTL without saying so in the rows that quote it.**
Every `cdl_*` JSON has `cdl_sha256` `af5a4dbd` (r1 `g1_chip_top_1414.cdl`) and RTL `g1_ctrl/rtl` (`42430b79`/`16e48edd`).
README l.197 and spec §4 "Trip response" / §5 "Full-chip simulation" present 1.437 µs as the chip response; only README l.111
discloses "pre-ECO digital, r2 content" (it was the r1 file). The rows also omit `pads nodcn` (all `dantenna` removed) and that the
CDL deck has no top-level wiring C. The chip-of-record ECO figure (1.451 µs, hand-wired) is later than the 1.437 µs headline.
"LVS-matched canonical CDL" (README l.112, spec l.105) is false: the CDL header says "not LVS-qualified" and canonical LVS failed.

**M4. The chip-of-record DRC evidence is bulk-only and unmanifested.** `signoff-1414r3-20260926/` commits only LVS pair counts and
identity JSONs; the DRC/precheck logs, `run.log.rc` and lyrdb files (committed for r1 and r2) are in `$R/signoff/` only and are in no
retention manifest. `TAPEIN_PACKAGE_20260924.md:162-166` cite `drc_main/`, `drc_maximal/`, `precheck/`, `density/`, `antenna/`, which
do not exist in the r3 directory. Values were verified in bulk (see table).

**M5. Power-up and matrix results are pre-ECO; gB/gA with the frozen RTL: not run.** `run_top.py:227-230` defaults to `rtl`
(labelled "chip of record"); `run_top_cdl.py` at HEAD has no `--rtl-dir`. So the 72-cell matrix, the CDL deck and every power-order
row (spec §5, P6) use map 1.1 RTL. Spec P6 cites "chip-level gB with the ECO RTL", but `eco_gB_r2` used the superseded
`605d7385`/`5c872e3b` (MODE 0x23); the ECO record (l.217) says "not rerun with the frozen RTL". The floating-EN latch window
(2.34–5.70 µs) is from pre-ECO RTL, although map 1.2 changes the EN reset. gA with the ECO RTL: not run and not listed.

**M6. Formal/logic equivalence and fast/slow SDF GLS missing from the r3 "Not run" lists.** RTL-vs-`4b83f181` equivalence appears only
in `ECO_20260925.md:268`; absent from spec §5, README and `signoff-1414r3-20260926/README.md:203-211`. Fast/slow SDF GLS is in README
and spec but not in the sign-off list (SDFs `cdc404bd…`/`f379a556…` exist in bulk). Chip-level runs with the hardened macro's gate
netlist + SPEF: stated only in the sign-off (l.206-207), not in README/spec.

**M7. GLS "passed" omits the red-team failure and Icarus model gaps.** README l.101, tape-in l.170, PLAN l.41: the sign-off (l.170)
and spec record "red-team bench on the netlist: 4 pass, 1 FAIL". The typ-SDF log also has 68 "sorry: ifnone with an edge-sensitive
path is not supported" messages and one "Could not insert intermodpath", i.e. part of the delay model was dropped, not only the timing checks.

**M8. Stale current-state text.**
- `README.md:118` "q full length and power-up on the CDL deck: running, not yet reported" (reported in l.198 and `FULLCHIP_CDL:169`); l.119 and spec §5 icx row "T2F-on run in progress".
- `README.md:146` G1_CTRL row: "run 7: DRC, LVS, antenna, XOR and timing clean; TMR ≥ 27 µm; 46 pins" still describes run7 as the macro.
- `padframe/README.md:159` heading "Chip of record, `g1_chip_top_1414_r2.gds`"; no r3 check table.
- `blocks/g1_ctrl/README.md:3-13` "Macro of record: run7 … not yet re-hardened"; `ECO_20260925.md:6` "Not promoted, not on the chip of record", l.266-270 list chip DRC/LVS and pin check as not run (done); `flow/eco/RUNBOOK.md:6` "waiting for the corrected ECO RTL".
- `blocks/g1_top/README.md:3-9` names r1 `629d303a` as chip of record; l.15/257 call `g1_ctrl/rtl` (map 1.1) the chip RTL.
- `README_top_interconnect_20260925.md:8-9, 25, 266` and `FULLCHIP_PEX_FEASIBILITY_20260925.md:23, 158`: "r2 … now the file of record", "chip deck with the lumps: not run" (the `c1414icx` runs are committed).
- Spec §3 note links `bondmap_20260925_r3.csv` (r2-bound) instead of r4; r3 CDL header still says "CANDIDATE … not promoted" (disclosed).

**M9. The "≤ 10 ns" interconnect delta is a timeline artefact.** RESULTS §9, `g1_top/README.md`, spec §5, README l.119. The reference
1.049/1.334 µs is the default-timeline run; `icx` is compact (`trip_d` 1.05778, `GATE` 1.34544). The like-for-like compact `c1414fullc`
gives 1.05788 / 1.34544: the extracted interconnect changes `GATE` < 1 V by < 0.1 ns. The `icx` decks are C-only (SENSE R only in the
`srr` run); §9 does not say so. The extraction is of r1 `629d303a` (`fullchip_strip_fill_20260925.json`), valid for r3 only through the
r2 → r3 XOR, which is not stated; r1 is no longer in the tree, so the committed commands point at a missing path.

**M10. The r3 macro cannot be rebuilt from tracked files.** The seeds and config that built r3 are bulk only
(`seeds_digital-eco-r3cand2-20260926.yaml` `40f086bb…`; the config embeds external absolute paths). Committed
`flow/eco/seeds_r3cand.yaml` is the superseded v1 set; `seeds_final.yaml`/`config_final.yaml` are the rehearsal's.

## Should-fix

- **S1.** `ECO_20260925.md:168` "1208 `TIMINGCHECK not supported`"; the v2 typ-SDF log has 1222 (= 1222 flops).
- **S2.** `ECO_20260925.md:125` old-testbench regression `tb_g1_digital_on_eco.log` ran on superseded `605d7385`/`5c872e3b` (fails "MODE got 0x23", "fast_en got 0x1"); relabel or re-run. l.129 R1 cause is X at t = 0 (`fast_en 0: got 0xX`), not "expected 0".
- **S3.** `ECO_20260925.md:213` baseline 1.049/1.334 µs labelled `c1414hot`; values are `c1414n2` (default timeline, no `nodcn`). No like-for-like committed baseline for `m03` (compact, `nodcn`, `bgr=sch`).
- **S4.** Runner provenance: CDL runs `cdlv1`–`v5` carry `runner_sha256` values never committed (`1f1993fd` for the headline, `4da29bca`, `c77f2fe6`, `986d625b`, `844a09fd`, `65138450`); only `e2d75a88` (`cdlpwr`) and HEAD `run_top.py` `3377410c` (ECO and `icx` runs) are committed.
- **S5.** Unretained cited evidence: `cdlref1` rows (`FULLCHIP_CDL:97-110`, incl. the gear 1.344 µs control); `cdl_gB_pex_ff_-40C…cdlpwr.log` (285 kB, no tail, not manifested); the floating-EN window, pad-waveform and `ng` OP numbers exist only in gitignored waves. The retained `cdlv2` reltol-5e-4 log is truncated (728 352 B vs JSON `log_bytes` 786 639; manifest size 728 320).
- **S6.** Retention manifest header: `file_count` 423 vs 450 entries; `total_bytes` 376 753 028 vs 566 020 109; the r1 GDS entry size (84 500 272) is `_src.gds`'s, the file is 84 500 250. PEX bulk artefacts (`nofill` `6406ba36`, view `78eeec9c`, CSV `53a20e34`) are unmanifested.
- **S7.** RESULTS §9 `osc` row "same, gear": the log uses BGR586 pex (not `bgr=sch`), 2 ns max step and relaxed tolerances.
- **S8.** Dates: records say "frozen/promoted 2026-09-26"; commits are 2026-09-25 22:00/23:14 +0200, SDF `Fri Sep 25 21:20:26 2026`, sign-off DRC run `2026_09_25_19_41_07`.
- **S9.** `FULLCHIP_CDL:169` "wall 25200 s" vs JSON `timeout_s` 24800; `FULLCHIP_CDL:50` recommends gear with the pex BGR, which failed at 2.83 µs (`cdlv3`).
- **S10.** GatPoly margin: 15.0309 % against the density limit, 14.9959 % after the swap; any later macro change will need the fill regenerated (note for the freeze rule).
- **S11.** `HANDOFF.md:47`, `RUNBOOK.md:88` point to `sim/run_gls.sh` (1.1 testbench); the evidence came from `gls_eco_r3v2/run_gls_eco.sh`. `RUNBOOK.md:75` hard-codes the rehearsal STA root.

## Notes

- N1. `bondmap_20260925_r3.csv` (r2-bound, superseded) still carries status `chip_of_record` (disclosed in padframe README l.26).
- N2. `PLAN.md` has no decision row for the r1 → r2 metadata revision; D15 names r1, D16 supersedes "r2 … of D15's lineage".
- N3. Findings of `EVIDENCE_AUDIT.md` now resolved at HEAD: GDS-in-Git wording for r1, `c1414oscv3` wall bound (14 000 s), `c1414v1` disclosure, BGR/TRIP PEX in the sign-off narrative, GATE PEX binding (`README_chip_binding_20260925.md`), CDL-vs-deck output (`cdl_vs_deck_20260925.txt`), canonical-LVS cause (now backed by `review/upstream/evidence/`), T2F with BGR586, SENSE area, 100 nF range, digital STA on the chip netlist.

## Verified as stated

- r3 = r2 + macro + 5/22 fill: `chip_xor.json`, `fill.json`, `pincmp_final.json` (64/64), `stock_compare_r3.json` (52 / 0 differ), swap and CDL method controls.
- Macro: setup 28.821/29.044/28.447 ns, hold 0.1948/0.1141/0.3375 ns; in chip setup 27.248/27.988/25.704 ns; max slew/cap/fanout 0 inside the macro; 225 clock nets, fanout ≤ 8; TMR min 27.4 µm; 1170 + 52 flops.
- RTL: `INRUSH` 0x02, `MODE` 0x03, `VERSION` 0x12, `osc_en` tied 1, FAST_EN = 0; RTL tests 23 pass / 283 checks; GLS zero-delay and typ SDF 21 / 260, 0 errors.
- CDL deck: `cdlv1` `trip_d` 1.0578, `GATE` < 1 V 1.437 µs; `q` 44 µs no trip, VDDA 1462.49 µA; power-up values match `results_cdl.txt`; `icx` values match their tails; all committed `cdl_*`/`icx` decks match their JSON `deck_sha256`.

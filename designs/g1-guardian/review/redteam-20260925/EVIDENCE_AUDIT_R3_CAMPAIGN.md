# G1 evidence audit: r3 full-chip campaign (`r3full`)

Scope: `blocks/g1_top/sim/FULLCHIP_CDL_R3_20260926.md`, the run evidence
`blocks/g1_top/sim/logs/*r3full*` and `sim/decks/*r3full*`, `run_top_cdl.py`, and the records that
cite it (RESULTS_20260925 §11, spec §4/§5, README, TAPEIN §6). Campaign evidence was audited at
`ff774d24`. The records commit `5a2ee263` landed during the audit; it changes only `README.md`,
`RESULTS_20260925.md`, the spec and `TAPEIN_PACKAGE_20260924.md`, and those records were audited at
`5a2ee263`. The working tree carries uncommitted edits (the eco3/eco4 logs), which are outside scope
and not counted. Same severity scale as `EVIDENCE_AUDIT.md`. Nothing tracked was modified.
Paths are relative to `designs/g1-guardian/`.

## Checks run

| Check | Result |
| --- | --- |
| Every number in the record's results table (trip_d / tripped / `GATE` < 1 V / < 0.33 V, cause, QUIET, VDDA/IOVDD, re-arm, power-up, f_osc) against the committed tails | **passed**: 45 runs, all values match to rounding (e.g. c_mid tt 1.16386 / 1.16662 / 1.54315 / 1.77919; ss/125 1.72635; ff/−40 1.43339; b_s 27.7521 / 28.1314; gA 2.38165–6.71873 µs, 4.057 µAs; osc 9.44158 MHz; gB 31.4 µV) |
| Deck identity | **passed**: all 45 committed decks match their JSON `deck_sha256`. Every header names CDL `5e47ae02…`, BGR586 `01227a3d`, SENSE `ffb14762`, TRIP `ba86b7b2`, T2F `441edabc` and interconnect `ddc88cc7…`; the osc decks name OSC CPEX `8efd7a09`. JSON `rtl_sha256` = frozen ECO RTL (`33d549da`, `4e3b8ff6`, …). The interconnect file and the r3 CDL hash-match at HEAD |
| `run_top_cdl.py` options (`--interconnect` hash-bound, `--t2f-off-write`, `--ser-start-us`, `--fault-mult`, `--por-pin`, `--osc`) | present at HEAD; `run_top_sha256` 3377410c in all 45 runs = committed `run_top.py` |
| Owner-requested cases with a completed run | **passed**: q, c_mid, c, e20, f_mid, b_s, hard_pulse, gB, gB_pd, gA, osc, c_mid ss/125 and ff/−40, 1.15×, 1.25×. All with `--pads nodcn` |
| Invalid runs ("mismatched XSPICE") | none: no hit in any tail, tracked log or retained raw log |
| Retention: raw logs of the 45 JSON runs | 45/45 are in `review/local-retention-20260925.json` and hash-match their `${BULK}` copies |
| Machine or private paths in the in-scope tracked files | none (container `/work`, `/foss` only) |

## Must-fix

**M1. The 1.25× witness is labelled "passed". Uncalibrated, 31.25 mV = 0.80T trips inside the §6 no-trip region (≤ 0.9T).**
Where: RESULTS §11 (row "near threshold … 1.25×: passed (characterization)"), spec §5 r3 row ("Passed, 14/14 … incl. … the
near-threshold witnesses"), README l.128, TAPEIN l.173; the record's verdict table labels this row "consistent" and its commit title says "all cases pass".
Log: `…_icx_fm1p25_maxstep1ns_functional_r3full2`, `cause= 2`, `t_gate_1V_us= 1.54312`.
The spec's own §6 (l.241) says the uncalibrated code trips inside the no-trip region. The status should read "trips inside the
uncalibrated no-trip region (0.80T), as documented; calibration requirement", not "passed". This row cannot count towards "14/14 passed".

**M2. Stale "not run" statements that r3full now contradicts.**
- `README.md:136-138`: "so the r3 value on the CDL deck is expected later than 1.437 µs (not run)". It ran: 1.543 µs.
- Spec §5 l.142: "r3 CDL with the ECO RTL: not run". That is this campaign.

**M3. The r1-vs-r2 baseline is misnamed in the same records.**
- RESULTS §11 and spec §4 l.105 say "+106 ns against r2's CDL run (1.437 µs)".
- That run used the r1 CDL `af5a4dbd` with the map-1.1 RTL. The same spec cell calls it "the canonical CDL of r1", and README l.219 says "r1/r2".

**M4. The not-run lists are incomplete.** The record, RESULTS §11, spec §5, README and TAPEIN omit:
- the chip digital as its hardened gate netlist + SPEF: every run replaces the CDL's gate-level `g1_digital` with RTL d_cosim;
- the trip path with the transistor-level oscillator: the osc case is `q` only, and every trip row uses the ideal 9.436 MHz clock;
- power-up gB/gB_pd/gA at ss/ff: tt only;
- the near-threshold points at corners, and with `FAST_EN`=1;
- `f_mid`/`b_s`/`hard_pulse` at corners (implied only by "corners other than c_mid").

**M5. Every pass depends on the `nodcn` pad deviation, and the stock-pad variants of every case failed or stalled.**
- The record states both facts.
- The summary rows (README l.128, TAPEIN l.173, spec §5) put "real IO pads" in the headline and move "stock-diode pads" into the not-run list.
- The reporting rule needs the stock-pad result stated as **failed** (functional cases: "timestep too small" at 1.679 µs) / **not run to completion** (power-up stalled at 1.19 ns) next to each "passed".

## Should-fix

- **S1. Failed and stopped runs lack JSONs and decks.** The 31 failed/stopped runs cited in the record's not-run list have their small raw logs tracked, but their JSONs and decks are untracked (working tree only):
  - the 5 ns tt failures of q/c/c_mid/e20/f_mid/b_s/hard_pulse;
  - the reltol 5e-4 kills (returncode −15);
  - the 5 ns T2F-off runs;
  - gA 20 ns (1.87 µs);
  - stock-pad gA and gB (20 ns, 2 ns);
  - the osc loose 2 ns and 1 ns runs;
  - an osc T2F-off run without `ser4` (0.70 µs).

  Two first `fm1p15`/`fm1p25` attempts (`r3full`, failed after 10 s) are not in the record.
- **S2. Runner provenance.** The JSON `runner_sha256` values 196545c1 (30 runs), a83ccbaf (10) and 2f2aa41b (3) were never committed. Only c54a0beb (the two `r3full2` near-threshold runs) equals `run_top_cdl.py` at HEAD.
- **S3. Some quoted numbers are not in committed evidence.** They exist only in gitignored waveform files or in figures derived by hand:
  - the VREF ripple (42.3 / 32.3 mV p-p, rms, "26 of 601 samples");
  - the power-up latch window (en_i > 0.6 V 2.34–5.70 µs; `tripped` 2.36–6.66 µs; RTL latch 3.18–6.66 µs);
  - "INRUSH cleared at 8.22 µs" and "no T2F edges after the write" (T2F off).

  The PORTIMING line supports only `por_n` 2.001 µs and IOVDD 1.1 V at 5.667 µs.
- **S4. The power-up verdict hides spurious trip latches.** The "No false trip at EN / power-up: pass" verdict (record, RESULTS §11 "no false trip") sits beside `tripped_max= 1.22388` in gB and gB_pd. The G1_GATE trip latch sets at power-up. `GATE` stays ≤ 31 µV. Better wording: "`GATE` passed; trip latches set spuriously while IOVDD is absent (P2)".
- **S5. The cited commit is not the final record.** Spec §4/§5, RESULTS §11 and TAPEIN cite the detailed record as committed `f81d3c6d`, which is the interim version (osc and near-threshold rows pending). The final record is `ff774d24`.
- **S6. "14/14" is ambiguous.** The owner's list gives 15 cases (gB and gB_pd separate); RESULTS §11 has 14 rows with gB/gB_pd merged and gA counted in the table. With M1, the passed count is 13 plus 1 characterization plus 1 expected-fail.
- **S7. The retention manifest header is still inconsistent:** `file_count` 470 vs 516 entries; `total_bytes` 921 240 189 vs 967 113 973.
- **S8. A deck comment names the wrong CDL.** Deck header line 58 says "the chip: g1_chip_top_1414.cdl" (r1 name) while line 2 and the hash name the r3 CDL. The GATE block is `g1_gate_pex.spice` `e91617f5` "not hash-bound in run_top.py"; the record says only "GATE Sep-19 PEX".

## Notes

- N1. The reltol 5e-4 variants are status `failed` with returncode −15 in their JSONs. The record's "stopped by me … to free CPUs" is consistent with this, but the status field does not say stopped.
- N2. The interconnect is an extraction of the r1 geometry, applied to r3 through the r2 → r3 XOR (outside the macro only 5/22 fill). The record states this.
- N3. The q and osc cases run at hard code 254 (`vth_hard` 1.003 V). c_mid, f_mid, hard_pulse and the near-threshold rows run at code 200. The verdict table states both thresholds.

## Verified as stated

- Deck: r3 CDL `5e47ae02`, ECO RTL (map 1.2), BGR586/SENSE/TRIP/T2F extractions, OSC CPEX in the osc case, interconnect `ddc88cc7` (C only), `nodcn` (8 `dantenna` removed), gear with a 1 ns step, ideal clock, T2F on.
- c_mid `GATE` < 1 V 1.543 / 1.726 / 1.433 µs (tt / ss125 / ff−40); decision 1.1637–1.1639 µs.
- c, e20 1.5316 / 1.5318 µs; f_mid re-arm 0.678 µs; b_s soft trip 27.752 µs.
- hard_pulse no trip (`tripped` 49 mV).
- q and osc no trip; osc 9.4416 MHz.
- gB/gB_pd `GATE` ≤ 31 µV; gA 3.30 V for 4.34 µs.
- 1.15× no trip; 1.25× trip.
- The T2F-off witnesses agree with the T2F-on runs within 0.2 ns.
- Stock-pad runs failed at 1.679 µs and stalled at 1.19 ns, as listed.

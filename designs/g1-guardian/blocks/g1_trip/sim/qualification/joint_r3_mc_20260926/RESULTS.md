# joint_r3_mc_20260926: joint calibrated mismatch screen of the on-chip TRIP chain (24 fresh seeds)

Simulated Monte Carlo mismatch of the blocks as they are on the chip, run through the original joint586
calibration contract. This is not hardware measurement, and 24 seeds are not a yield qualification.

## Result

Seeds 24: **passed 16**, electrical fail 4, numerical fail 4.

| Seed | Result | Calibration reach at 25 C / 25 mV: offset before calibration, mV shunt (signed correction, LSB) | Codes soft/hard | Guards 25 / -40 / 125 C (correct/probes) | Residual +/-0.5 mV 25 / -40 / 125 C | Core h |
| --- | --- | --- | --- | --- | --- | --- |
| 79001 | passed | soft -0.57 mV (-3), hard +6.69 mV (+34) | guard 150/238, residual 125/162 | 4/4 / 4/4 / 4/4 | 2/2 / 2/2 / 2/2 | 4.8 |
| 79002 | passed | soft -1.16 mV (-6), hard +5.71 mV (+29) | guard 147/233, residual 122/157 | 4/4 / 4/4 / 4/4 | 2/2 / 2/2 / 2/2 | 5.0 |
| 79003 | electrical | soft +0.61 mV (+3), hard +9.44 mV (+48) | guard 156/252, residual 131/176 | 4/4 / 4/4 / 4/4 | 2/2 / 2/2 / 1/2 | 4.8 |
| 79004 | passed | soft -0.57 mV (-3), hard +7.48 mV (+38) | guard 150/242, residual 125/166 | 4/4 / 4/4 / 4/4 | 2/2 / 2/2 / 2/2 | 4.8 |
| 79005 | passed | soft +1.00 mV (+5), hard +8.46 mV (+43) | guard 158/247, residual 133/171 | 4/4 / 4/4 / 4/4 | 2/2 / 2/2 / 2/2 | 3.6 |
| 79006 | passed | soft -0.37 mV (-2), hard +7.67 mV (+39) | guard 151/243, residual 126/167 | 4/4 / 4/4 / 4/4 | 2/2 / 2/2 / 2/2 | 4.7 |
| 79007 | numerical | not reached: failed selected probe; no automatic retry | - | not run / not run / not run | not run / not run / not run | 1.4 |
| 79008 | passed | soft +1.39 mV (+7), hard +9.63 mV (+49) | guard 160/253, residual 135/177 | 4/4 / 4/4 / 4/4 | 2/2 / 2/2 / 2/2 | 4.8 |
| 79009 | electrical | soft +0.80 mV (+4), hard +9.05 mV (+46) | guard 157/250, residual 132/174 | 4/4 / 4/4 / 4/4 | 2/2 / 2/2 / 1/2 | 4.8 |
| 79010 | passed | soft +0.02 mV (+0), hard +7.87 mV (+40) | guard 153/244, residual 128/168 | 4/4 / 4/4 / 4/4 | 2/2 / 2/2 / 2/2 | 4.8 |
| 79011 | passed | soft -0.96 mV (-5), hard +7.87 mV (+40) | guard 148/244, residual 123/168 | 4/4 / 4/4 / 4/4 | 2/2 / 2/2 / 2/2 | 4.7 |
| 79012 | passed | soft +0.22 mV (+1), hard +7.87 mV (+40) | guard 154/244, residual 129/168 | 4/4 / 4/4 / 4/4 | 2/2 / 2/2 / 2/2 | 6.0 |
| 79013 | electrical | soft +0.41 mV (+2), hard +8.06 mV (+41) | guard 155/245, residual 130/169 | 4/4 / 4/4 / 4/4 | 2/2 / 2/2 / 1/2 | 4.7 |
| 79014 | passed | soft -2.34 mV (-12), hard +5.51 mV (+28) | guard 141/232, residual 116/156 | 4/4 / 4/4 / 4/4 | 2/2 / 2/2 / 2/2 | 5.5 |
| 79015 | passed | soft -0.57 mV (-3), hard +7.08 mV (+36) | guard 150/240, residual 125/164 | 4/4 / 4/4 / 4/4 | 2/2 / 2/2 / 2/2 | 4.7 |
| 79016 | numerical | soft +0.41 mV (+2), hard +8.46 mV (+43) | guard 155/247, residual 130/171 | 3/4 (1 num.) / 4/4 / 4/4 | 2/2 / 2/2 / 2/2 | 5.6 |
| 79017 | passed | soft +0.61 mV (+3), hard +8.26 mV (+42) | guard 156/246, residual 131/170 | 4/4 / 4/4 / 4/4 | 2/2 / 2/2 / 2/2 | 3.3 |
| 79018 | electrical | soft -0.57 mV (-3), hard +7.67 mV (+39) | guard 150/243, residual 125/167 | 4/4 / 4/4 / 4/4 | 2/2 / 2/2 / 1/2 | 2.9 |
| 79019 | passed | soft -0.77 mV (-4), hard +7.87 mV (+40) | guard 149/244, residual 124/168 | 4/4 / 4/4 / 4/4 | 2/2 / 2/2 / 2/2 | 2.8 |
| 79020 | numerical | not reached: failed selected probe; no automatic retry | - | not run / not run / not run | not run / not run / not run | 0.6 |
| 79021 | passed | soft +0.22 mV (+1), hard +7.87 mV (+40) | guard 154/244, residual 129/168 | 4/4 / 4/4 / 4/4 | 2/2 / 2/2 / 2/2 | 4.0 |
| 79022 | passed | soft +1.00 mV (+5), hard +9.44 mV (+48) | guard 158/252, residual 133/176 | 4/4 / 4/4 / 4/4 | 2/2 / 2/2 / 2/2 | 4.0 |
| 79023 | passed | soft +0.41 mV (+2), hard +8.26 mV (+42) | guard 155/246, residual 130/170 | 4/4 / 4/4 / 4/4 | 2/2 / 2/2 / 2/2 | 4.1 |
| 79024 | numerical | soft +1.20 mV (+6), hard +8.65 mV (+44) | guard 159/248, residual 134/172 | 4/4 / 3/4 (1 num.) / 4/4 | 2/2 / 2/2 / 2/2 | 4.0 |

Calibrated seeds (22): offset before calibration, mV shunt: soft mean +0.02, sd 0.90, range -2.34..+1.39; hard mean +7.95, sd 1.06, range +5.51..+9.63.

| Seed | Probe | Kind | T (C) | Shunt (mV) | Codes | Decisions | Expected | Class |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 79003 | p26 | residual | 125 | 24.50 | [131, 176] | {'soft': False, 'hard': True} | {'soft': False, 'hard': False} | electrical |
| 79007 | p06 | calibration | 25 | 25.00 | [135, 167] | {} | None | numerical: timeout, 1200 s |
| 79009 | p26 | residual | 125 | 24.50 | [132, 174] | {'soft': False, 'hard': True} | {'soft': False, 'hard': False} | electrical |
| 79013 | p26 | residual | 125 | 24.50 | [130, 169] | {'soft': False, 'hard': True} | {'soft': False, 'hard': False} | electrical |
| 79016 | p11 | guard | 25 | 33.00 | [155, 247] | {} | {'soft': True, 'hard': False} | numerical: timeout, 1200 s |
| 79018 | p26 | residual | 125 | 24.50 | [125, 167] | {'soft': False, 'hard': True} | {'soft': False, 'hard': False} | electrical |
| 79020 | p02 | calibration | 25 | 25.00 | [127, 127] | {} | None | numerical: timeout, 1200 s |
| 79024 | p15 | guard | -40 | 33.00 | [159, 248] | {} | {'soft': True, 'hard': False} | numerical: completed, 1079 s; Error: Transient op failed, timestep too small |

Reading:
- **Calibration.** It reached a bracket for 22 of 24 seeds. The two that did not (79007, 79020) hit the
  1200 s solver watchdog on one calibration probe; these are numerical failures.
- **Offset before calibration** (25 C, 25 mV input, in mV of shunt voltage):
  - soft: mean +0.02, sd 0.90;
  - hard: mean +7.95, sd 1.06. This is the hard-path early trip found in the post-layout analysis; the room
    calibration absorbs it with a signed correction of +28 to +49 LSB, with no clipping in any seed.
- **Residual after calibration.** The bracket-midpoint (residual) code sits half an LSB (+0.098 mV shunt) above
  the room crossing in every seed. The held-out residual probes at +/-0.5 mV test whether that holds over temperature.
- **Guards** (at <= 0.9 T no trip and >= 1.1 T trip, with the corrected codes; soft T = 30 mV, hard
  T = 40.03 mV): every numerically completed guard probe of the 22 calibrated seeds decided correctly at
  25, -40 and 125 C, 262 probes in all. Two guard probes were numerical failures:
  - 79016 at 25 C: watchdog timeout;
  - 79024 at -40 C: the operating point failed ("timestep too small").
- **Residual +/-0.5 mV** (24.5 mV no trip / 25.5 mV trip, residual codes):
  - all correct at 25 C and -40 C;
  - at 125 C, 4 seeds (79003, 79009, 79013, 79018) have the **hard** comparator trip at 24.5 mV. That is a
    hot drift of the calibrated hard threshold of more than 0.5 mV shunt, which is **electrical**.
  - Soft residuals were correct in every seed and temperature.

Summary: **16 passed / 4 electrical fail (all: hard residual at 125 C, -0.5 mV side) / 4 numerical fail**
(3 watchdog timeouts, 1 operating-point failure). Numerical failures are not counted as electrical passes.

## Blocks and method

| Item | Identity |
| --- | --- |
| BGR586 | `sources/bgr.spice` `7de0fc30…`: the BGR586 source `586ffb58…` (`g1_bgr/sim/qualification/candidates/bgr_loop24_qref4_r253p465_hv06/`) with `mm_ok=1` on all 1036 devices. The device multiset is otherwise identical (checked). |
| SENSE comp45 + R100 | `sources/sense.spice` `bb933fda…` |
| TRIP, NF4 soft + regenpair4 hard | `sources/trip.spice` `f5f0a90a…` |
| Deck template | `../joint586-softinputpair4-nf4-roomcal-s73133-20260924-r1/c00/probe.cir` `ede03377…`; contract (groups, sampling, NF4 geometry) `../joint586-softinputpair4-nf4-roomcal-s73133-20260924-r1/contract.json` `5d123f6e…` |
| Runtime | pinned image (`flow/run.sh`), PDK 84374023, ngspice-46, `*_mismatch` model sections, `setseed <seed>`, gear, reltol 1e-5 |

- `runner_r3mc.py --selftest` reproduces, for seed 73133, the c00, c05 and heldout-p27 decks of the passed NF4
  run byte for byte (only include paths differ).
- Per probe, only these change: seed, `.temp`, the shunt source, the 16 code bits and the wave path.

The method is the original joint586 runner (`../joint586-calibration-s73133-20260922-a/runner.py`):
- **Calibration** at 25 C, 25 mV: codes [0,0], then [255,255], then the original binary rule
  (`audit_bgr_calibration_tree.replay`), hard nominal code 204, signed correction with clipping.
- **Guards** with the corrected codes at 25, -40 and 125 C: 27 / 33 / 36.03 / 44.03 mV.
- **Residuals** with the midpoint codes at 25, -40 and 125 C: 24.5 and 25.5 mV.
- **Checks on every probe:**
  - the 1200 s solver watchdog (`run_bounded`);
  - the log error scan and completion marker;
  - the NF4 native geometry, before and after;
  - the 11 512 mismatch parameters, before and after, which must be identical across all probes of a seed;
  - the measured-edge sampling rule (3 decisions per comparator, all must agree, no majority vote).

A probe that fails any check is numerical. A clean probe with a wrong decision is electrical.

## Seeds, launches and incidents

- Seeds 79001-79024 are new. Earlier runs used 73001-73300, 77101-77130 and 78101-78130.
- All launches: nice 0, one seed per CPU through `flow/launch_pinned.sh`, at most 16 concurrent before 21:00 CEST.
  - 2026-09-26 09:26 CEST: 79001-79016 on CPUs 100-115 (`launch.sh`).
  - 79005, 79007, 79017-79024 were started as CPUs freed (`dispatch.sh`, `dispatch2.sh`); all were launched by 14:15.
  - All finished by 18:24.
- Two aborted launch attempts before 09:26 (bulk `aborted_*`):
  - the first ran at nice 5 because of the background-job nice setting of zsh; it was stopped at once;
  - the second hit an assertion from a hard-cell name check that does not apply to regenpair4; that check was
    removed and deck identity is established by `--selftest` instead.
- **CPU contention (voided, `voided_cpu_contention/`):** 79005 and 79007 first ran on CPUs 104 and 106. Other
  chip-level ngspice runs of the same account were pinned there. They and the relaunched 79017 and 79018 timed
  out at the watchdog. All four were rerun from scratch on uncontended CPUs.
- **Home quota:** the account's home quota reached its hard limit at 16:44 CEST. Runners crashed while writing
  `summary.json`, and podman could not start containers for several minutes. `runner_r3mc_r2.py` (same method,
  plus `--resume` and `--summary-dir`) and `resume_watch.sh` restarted 79022, 79023 and 79024. Leaves whose
  `run.json` was terminal and whose deck was identical were analysed again, not re-simulated; the rest were
  simulated. Resumed seeds record `reused_leaves` in their summary.

## Reproduction

```
cd designs/g1-guardian/blocks/g1_trip/sim            # inside the pinned container (flow/run.sh), BULK = results root
python3 qualification/joint_r3_mc_20260926/runner_r3mc.py --selftest
python3 qualification/joint_r3_mc_20260926/runner_r3mc.py --seed 79001 --bulk $BULK/joint_r3_mc_20260926
# resume after an interruption:
python3 <runner_r3mc_r2.py> --seed N --bulk $BULK/joint_r3_mc_20260926 --summary-dir $BULK/joint_r3_mc_20260926/summaries --resume
python3 qualification/joint_r3_mc_20260926/make_results.py $BULK/joint_r3_mc_20260926/full_summaries qualification/joint_r3_mc_20260926
```

Hashes (sha256):

| File | sha256 |
| --- | --- |
| runner_r3mc.py | 3891de0c2544e518a6d1859071bb86eda943c2aa130290272716d165a7027acf |
| runner_r3mc_r2.py (as run; the copy here has only paths replaced) | b2e87b80de10720399aa4c7b3075b6c303847d112709d56da75d809516700aca |
| launch.sh / dispatch.sh / dispatch2.sh / resume_watch.sh (as run) | ec19cd0f… / 7016ee7f… / 3dd949e3… / f7de389a… |
| make_results.py (as run) | 06fdf3a43bd5d10e3867b43a55dd03df81088a268780430de1d892126e719fea |
| helpers in `../../` (unchanged): audit_bgr_calibration_tree.py, run_nominal_clock_probe.py, run_joint586_transients.py, run_bgr_substitution_draw_audit.py, analyze_bgr_substitution_outcomes.py, wave_archive.py, run_joint_calibration.py, compare_hot_residual_probes.py, g1_top/sim/run_bounded.py, .spiceinit | 7c2d5023…, c818d804…, b8f39cfd…, a01a8667…, 73d3a553…, 440be122…, 349239ce…, 66fb63e1…, a78744ac…, 17082317… |

- Per-seed compact summaries: `s<seed>/summary.json`. They drop only the per-probe warning inventories and the
  repeated calibration attempt list. The full summaries are in bulk `full_summaries/`.
- Probe decks, logs, waves, analyses and the 11 512-parameter vectors: bulk `s<seed>/pNN/`.

Not run: mismatch of the parasitic (PEX) netlists (the screen uses schematic sources), supply corners other than
typical, a larger population, and hardware.

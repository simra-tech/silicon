# One-draw reference harness qualification — simulated

Source586ffb58, pinned ngspice46/IHP84374023, seed44001. The five fixtures
in [the prospective contract](ONE_DRAW_QUALIFICATION_20260922.md) completed
in22.830,21.443,18.174,15.332 and15.395 seconds, each below120 seconds.
[Manifest](runs/bgr_one_draw_20260922_r1/manifest.json) contains complete
runtime/source/model hashes, all named parameter values and wave hashes.

| Check | Status | Evidence |
|---|---|---|
| Five finite full34-temperature sweeps | passed | -40..125 C/5 C, all12 output columns |
| 2,842 unique parameters before/after each sweep | passed | Exact named order, finite and same-instance equality |
| Enabled forward/repeat/reverse parameter identity | passed | One unchanged draw, not three samples |
| Same-seed forward/repeat waveform bytes | passed | Full exported wave hashes equal |
| Two disabled seeds against retained nominal | passed | Full wave bytes equal; parameter vectors equal |
| Reverse normalized exact numeric equality | failed | Nonzero final-bit differences retained |
| Predeclared reverse numerical consistency | passed | Largest voltage difference0.1966 nV; current0.1085 pA |
| One drawTC<=50 ppm/C | passed | 11.7117232 ppm/C; nominal8.52982258 ppm/C |
| Broad population, source geometry PEX, adoption | not run | No statistical yield or physical qualification |
| Physical measurement in this harness check | not applicable | All numbers simulated |

Each enabled log retains1,629 warning lines (including an initial temperature-
limiter NaN); each disabled log retains one such initial NaN warning. Existing
literal resistor-model diagnostic and high-voltage/temperature applicability
limits are not cleared by finite output or a numerical TC pass. No model edits.

Reproduce with `flow/run.sh python3 designs/g1-guardian/blocks/g1_bgr/sim/qualification/run_one_draw_qualification.py`
in a workspace with no corresponding result directory. Five exact deck-transform
checks passed before launch. The runner stops at numerical/parameter failure;
no seed replacement, automatic retry or population expansion is provided.

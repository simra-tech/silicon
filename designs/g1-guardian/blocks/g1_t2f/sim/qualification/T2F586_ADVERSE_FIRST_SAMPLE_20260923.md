# Final586 slow-corner first sample: numerical failure retained

Simulated seed **75101** completed six attempted conditions. Five leaves passed
the frozen source/runtime, full3180 before/after, 32us waveform and external HBT
VCE checks. The 100C calibration leaf failed its original 600s watchdog.
Consequently the frozen 25/100C linear fit and held-out ±2C accuracy result are
**not run to completion**, not passed. Samples75102–75130 remain **not run**.
The separate fast-corner population75201–75230 remains **not run** because its
own qualification failed. Neither population is replaced by the typical cohort.

| Condition | Numerical/full3180/wave result |
| --- | --- |
| 25C, nominal rails | passed |
| 100C, nominal rails | failed: 600.205s watchdog |
| −40C, low rails | passed |
| 125C, low rails | passed |
| −40C, high rails | passed |
| 125C, high rails | passed |

The failed leaf is `runs/t2f586-slow-calibration-s75101-20260923-a/p01`.
Its exact deck SHA256 is
`96f070389b6fb908ea984f6152b1e22d26c3d928970f4362de9981fe93633edd`.
The read-only failure audit verifies the source, deck, runtime and all3180
BEFORE parameters against the completed25C leaf. AFTER queries, exported
waveform and frequency are **not run to completion**. All3272 logged warnings
precede the initial transient; no positive-time warning or explicit solver error
was found. This is not a model-validity or numerical-cause conclusion.

Host progress reached approximately2us at216s,3us at364s,4us at512s and
4.64435us at600s. These are sampled progress messages, not accepted-step or
terminal-wave observations. They do not justify a blind timeout extension or
attribute the slowdown to a device. No retry, replacement seed, refit, tolerance
change or solver adoption is included in this result.

Evidence:

- [Independent first-sample evidence audit](t2f586-slow-firstsample-failed-audit-20260923.json): one failed complete sample, five numerical completions; evidence integrity passed.
- [Failed-leaf input and available-parameter audit](t2f586-s75101-cal100-failure-analysis-20260923.json): missing outputs explicitly retained.
- [Frozen adverse contract](t2f586-adverse-calibration-contract-20260923-a/contract.json): original six conditions, full3180, watchdog and accuracy criteria.

The first-sample audit's aggregate primitive-distinctness status is **not run**:
there is no fully completed six-leaf sample pair. Its individual zero-draw
records carry a vacuous `passed` label from the frozen auditor; those records
are not evidence of population variation. The original report is preserved.

All results remain schematic/model-level controls with nominal586 geometry
source identity and mismatch enabled, not qualification of a new physical
parasitic view. The fixed30-sample obligation remains open; failures remain in
the denominator.

# T2F final-source KLU controls

The fast-corner six-control same-KLU qualification passed. This is a simulated
source/runtime/draw-consistency result, not calibration accuracy, yield,
physical qualification, or permission to replace the ongoing SPARSE population.
Original SPARSE numerical failures remain in the evidence.

[Independent fast qualification](t2f586-klu-fast-own6-qualification-20260923.json)
has SHA-256 `6718bddf41533b83379be0488b196e6cde0e68fa67bf41ffa44177415a27c270`.
Its six controls cover enabled, exact repeat, changed seed, disabled, disabled
changed seed and same-instance temperature return. The audit independently
checks every source/deck/runtime receipt, log, finite full waveform, all 3,180
parameters and the 1.6 V external T2F HBT VCE ceiling. All 1,129 randomized
primitives vary with the changed seed.

The following comparisons pass exact decoded-byte, numeric-row and time-grid
equality, with exact full parameter identity:

- Enabled repeat.
- Initial and returned 25 °C wave in the 25 → 125 → −40 → 25 °C control.
- Disabled versus disabled changed seed.
- Disabled versus an independently executed same-KLU nominal reference.

All three corner return diagnostics completed under their original 2400 s
limits, without extending an existing failed job:

| Corner | Simulated runtime | Full 3,180 parameters at all four phases | Returned-room exact waveform |
| --- | ---: | --- | --- |
| Fast | 1536.478 s | Passed | Passed |
| Slow | 1117.951 s | Passed | Passed |
| Typical | 1568.286 s | Passed | Passed |

These return results do not substitute for the remaining slow/typical own-six
controls. Those independent qualification sequences are still in progress at
this checkpoint. KLU-versus-SPARSE exact waveform differences remain failed
exact comparisons, even when both runs are numerically valid.

The implementation is bound by
[own-six implementation](t2f586-klu-own6-implementation-20260923-a.json),
SHA-256 `dd58c9eb8b525fa43458e47305ba67e6290410e3e587747d6ffcc6f1b4d5a720`.
It reuses ten completed controls only through exact input and independent
receipt checks, and declares eleven new bounded controls. No existing source
or model card is changed.

## Prospective adverse first sample — not run

[Prepared fast 75201 contract](t2f586-klu-fast-firstsample-contract-20260923-a/contract.json)
SHA-256 `b1880210392b26467d56b95ef86961864339fcf7ac28f31ebb42c60290b58d29`
contains six deck examples whose only solver change from the original declared
sample is `.options klu`. The original six conditions, seed, 600 s leaf limit,
32 µs endpoint, full parameter checks, 25/100 °C linear calibration and four
held-out rail/temperature endpoints within ±2 °C are unchanged. Two transform
tests pass. Execution and rail-extreme first-sample qualification are **not run**;
no next-29 release or general solver adoption is claimed.

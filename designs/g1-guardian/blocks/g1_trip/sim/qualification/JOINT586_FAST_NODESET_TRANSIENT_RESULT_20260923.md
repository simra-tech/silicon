# Fast-corner nodeset transient pair

Both separately declared full-length diagnostics completed. This updates the
**not run** state of the earlier preparation checkpoint; it does not rewrite
the original SPARSE 1200 s timeout or original KLU initialization failure.

| Diagnostic | Simulated runtime | Full 11,512 before/after + 27 anchors | Original sampling | Soft / hard |
| --- | ---: | --- | --- | --- |
| SPARSE plus fixed eight-node guesses | 308.258 s | Passed exact identity | Passed | Low / low |
| KLU plus the same guesses | 235.521 s | Passed exact identity | Passed | Low / low |

Both outputs have 6,593 finite rows, all 19 declared vectors and the original
1.02 µs endpoint. Source, model, seed 78001, codes 135/151, rail/common-mode
stimulus, timing, tolerances and 1200 s leaf bound remained frozen under
[contract b](joint586-fastcold-nodeset-transients-contract-20260923-b.json).
Warnings remain in the original logs: five for SPARSE and seven for KLU. No
model-validity or physical-qualification conclusion follows from completion.

The independent [pair audit](joint586-fastcold-nodeset-pair-audit-20260923.json),
SHA-256 `2e025668ef66600f329a8a9810efc5c7a5739056673138f1de8953edac35315d`,
reopens runtime/source/deck receipts, full logs, parameter vectors and decoded
waveforms. The exact decoded-byte, numeric-row and time-grid comparisons
**failed**. These are not converted into passes by a tolerance.

As descriptive comparisons only, the two runs agree on both decisions and
clock-event counts. Linear interpolation on the union of saved output grids
gives a largest voltage difference of 16.778 nV at `xt.xch.yn`; the largest
paired hard-clock crossing difference is about 3.39 × 10⁻²⁰ s. These numbers
are not accuracy limits, evidence of rejected solver steps, or exact parity
with the original failed transient, which has no completed full waveform.

The fixed nodeset guesses make the SPARSE diagnostic numerically tractable in
this one fixture. A causal attribution, general solver change, new-fixture
qualification, fast 30-sample release and adoption into calibration are all
**not run**. Five previously successful fixtures cannot silently substitute
for qualification of an initialization change.

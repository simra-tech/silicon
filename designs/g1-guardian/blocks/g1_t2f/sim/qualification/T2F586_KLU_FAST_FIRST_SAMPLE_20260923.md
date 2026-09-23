# Fast75201: first six-condition KLU diagnostic

Status: **failed**, with all six requested attempts retained. The independent
evidence audit passed; that is not an electrical or numerical pass for the
sample. No next29 samples or population solver switch is qualified.

| Condition | Numerical result | Simulated runtime (s) |
|---|---|---:|
|25C,3.3V/1.2V calibration|passed|402.506|
|100C,3.3V/1.2V calibration|passed|479.983|
|−40C,3.0V/1.08V|failed initial operating point|30.478|
|125C,3.0V/1.08V|passed|497.975|
|−40C,3.6V/1.32V|passed|358.334|
|125C,3.6V/1.32V|passed|499.395|

The low-cold failure reports an OP timestep failure at the BGR XQ55 VBIC
instance, then an initial-timepoint transient failure and empty-output
measurement errors. It is not a wall-clock timeout. No valid full waveform,
frequency or full3180 parameter qualification is claimed for that leaf.
The other five leaves passed the original3180 before/after, source/runtime,
32us endpoint,13-column waveform and1.6V HBT VCE gates. Maximum observed
VCE across those leaves was1.091152V, not an all-corner device bound.

The parent calibration status remains **not run**, because complete required
coverage failed. A separate read-only diagnostic evaluates the original
25/100 linear formula on the completed leaves, without replacing a point:
slope6204.55373697Hz/C and intercept1748429.79341008Hz. Conditional errors
are+0.871250C at low-hot,−2.138305C at high-cold (**failed±2C**), and−1.839951C
at high-hot. Low-cold remains **not run**. Therefore fixing initialization
alone would not establish electrical passage of this sample.

Evidence is in
[the independent audit](t2f586-klu-fast-s75201-firstsample-audit-20260923.json)
(SHA256`bd1c570530aa1cd14dc803a7db508499926f4caa9c2fc81cd9099876d3c66fe5`)
and[the conditional diagnostic](t2f586-klu-fast-s75201-partial-diagnostic-20260923.json).
The audit binds the six original leaf receipts and immutable implementation
`6f6d420a192ce71342a0ccae1d220f1531c7bb4391aba5786ad3dbdef3ba36f9`.
Original SPARSE failures, cross-solver exact-wave failures and all prior
population denominators remain unchanged. No layout or silicon claim follows.

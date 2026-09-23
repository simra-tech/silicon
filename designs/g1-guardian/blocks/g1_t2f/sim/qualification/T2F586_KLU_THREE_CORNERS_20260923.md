# Three-corner same-KLU consistency qualification

All three six-control qualifications passed their independent evidence audits.
These simulated results establish the declared source/runtime/draw consistency;
they are not a statistical accuracy or yield claim, physical qualification, or
a general replacement of the original SPARSE campaigns.

| Corner | Independent audit | Audit SHA-256 |
| --- | --- | --- |
| Fast | [Passed](t2f586-klu-fast-own6-qualification-20260923.json) | `6718bddf41533b83379be0488b196e6cde0e68fa67bf41ffa44177415a27c270` |
| Slow | [Passed](t2f586-klu-slow-own6-qualification-20260923.json) | `a3464b740bbe83cdb2614ed9d88954bd0c7297b964c5b6340217e7adfdac7f06` |
| Typical | [Passed](t2f586-klu-typical-own6-qualification-20260923.json) | `1cb23d65521091da1bbf0854a5c9e91438f02773bfe08c229438828dc4b49d3e` |

For each corner, all 3,180 parameters match exactly before and after each
phase. Enabled repeat, initial and returned 25 °C, disabled changed seed, and
disabled versus the same-KLU nominal reference pass exact decoded-byte,
numeric-row and time-grid comparisons. All 1,129 randomized primitives change
under the declared changed-seed control. The source-bound implementation
independently verifies original receipts when reusing completed controls.

The same-instance return sequence is 25 → 125 → −40 → 25 °C. Every phase
retains the full 32 µs endpoint, named 13-vector finite waveform, original
scalar measurements and 1.6 V external T2F HBT VCE limit. Original warnings
remain in their logs. Numerical completion does not establish validity outside
the documented model limits.

Original SPARSE timeouts and cross-solver exact-wave comparison failures remain
failed evidence. No tolerance, recalibration, altered seed, source/model-card
change or watchdog ladder replaces them. The ongoing typical SPARSE population
is unchanged.

A separately declared first fast adverse sample, seed 75201, is in progress
under [implementation contract](t2f586-klu-fast-firstsample-implementation-20260923-a.json)
SHA-256 `6f6d420a192ce71342a0ccae1d220f1531c7bb4391aba5786ad3dbdef3ba36f9`.
Its six conditions retain the original 600 s leaf bound, full parameter and
waveform checks, 25/100 °C linear calibration, and ±2 °C criterion at four
held-out rail/temperature endpoints. Its completed first-sample audit and any
next-29 population release are **not run** at this checkpoint.

# Final-reference T2F matrix-solver diagnostics

These are simulated numerical diagnostics, not a solver-adoption or population
qualification. Original failures remain failed and retain their original sample
denominators. Models, sources, mismatch realization, integration method, timing,
load and tolerances were unchanged; `.options klu` was the sole algorithm change.

The [matched 2 µs comparison](t2f586-fast76002-klu2us-comparison-20260923.json)
completed in 24.025 s with KLU versus 456.692 s with SPARSE 1.3. All 3,180
parameters matched exactly before/after and across solvers. Both saved 855 rows;
exact waveform-byte and time-grid equality **failed**. The two rising FOUT
crossings shifted by −1.84e−17 and −1.04e−16 s. Maximum linearly interpolated
union-grid FOUT difference was 1.8762 µV. No numerical tolerance replaces the
failed exact comparisons.

The separate original-full-32-µs 76002 diagnostic completed in 359.877 s under
the unchanged 600 s watchdog, with all 3,180 parameters exact, 21,835 finite
13-column rows, and external HBT VCE maximum 1.066560508 V. The original frequency
measurement was simulated 1,921,582.615 Hz; this is not a temperature-accuracy
or calibrated-population result. Thirteen initialization warning occurrences
remain recorded. The original SPARSE 600 s timeout and the separate failed trap
diagnostic are unchanged. See the [portable full-run receipts](portable_evidence/t2f586-klu32us-20260923/).

A [retrospective same-KLU interior-prefix comparison](t2f586-klu-prefix-full-comparison-20260923.json)
found all 834 saved rows through 1.9 µs exactly equal between the 2 and 32 µs
runs. This explicitly excludes the 2 µs endpoint and is not an independent
repeat or a retrospectively changed acceptance gate.

Three already-completed typical/slow/fast 32 µs controls and independent KLU
repeats have a [frozen preparation](t2f586-klu-matched-controls-20260923-a.json);
their separate qualification sequence is in progress, not yet completed.
Full parameter and finite-endpoint checks, frequency observations, separate
SPARSE/KLU exact comparisons, and exact same-KLU repeat checks are required
before any proposed remaining-sample solver change. No active campaign was
changed by these diagnostics; no population release is implied.

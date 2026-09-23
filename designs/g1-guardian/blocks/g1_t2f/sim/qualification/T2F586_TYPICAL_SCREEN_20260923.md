# Final-reference T2F typical screening

The first twenty independent final-586 samples passed their original four-leaf
and linear ±2 °C checks. The same immutable campaign continues with a fixed
100-sample independent audit before samples 101–300. It does not inherit the
historical-source population, exclude failed samples, or refit acceptance.

Samples 74121–74125 passed the independent full-deck, source, runtime, 3,180
parameter and waveform re-audit. Samples 74126–74130 have four passes and one
numerical failure, all retained in the [five-sample audit](t2f586-s74126-74130-audit-20260923.json).
The corresponding [portable receipts](portable_evidence/t2f586-s74126-74130-20260923/)
retain all twenty attempted leaves, including the failed leaf.

Seed 74128's 100 °C leaf reached the original 600-second watchdog at a reported
9.45244 µs of the required 32 µs. Its 25/−40/125 °C leaves completed with exact
full parameters and accepted waveforms/VCE; the 100 °C BEFORE vector also exactly
matches its own completed 25 °C draw. AFTER, the complete 100 °C waveform,
frequency and two-point calibration are **not run** to completion. The sample
therefore remains **failed**, not an electrical accuracy pass or fail.

The [read-only failure analysis](t2f586-s74128-cal100-failure-analysis-20260923.json)
finds no source/deck/runtime discrepancy. All 3,368 warning occurrences precede
the initial transient solution; none occur in the positive-time progress region.
Host telemetry reaches 2/4/6/8 µs at approximately 99/236/363/501 seconds.
This describes progress, not accepted-step waveform data or a demonstrated
numerical cause. No retry, replacement, solver change or acceptance change is
made by this report. The declared 300-sample denominator remains intact.

Samples 74131–74135 also passed the independent full-source, runtime, parameter,
waveform and original linear-error audit, including distinct draws for every
one of the 1,129 randomized primitives across all five samples. See their
[audit](t2f586-s74131-74135-audit-20260923.json) and
[portable receipts](portable_evidence/t2f586-s74131-74135-20260923/).

Seed 74140's 25 °C leaf reached the original 600 s watchdog at a reported
29.0854 µs. Its full BEFORE inventory exactly matches its completed 100 °C
phase; AFTER and the full 25 °C waveform are not run to completion. The
[read-only failure analysis](t2f586-s74140-cal25-failure-analysis-20260923.json)
retains 3,272 initialization warnings and no positive-time warnings. Remaining
required phases continue independently. The failed initial calibration is not
replaced by a fit from other temperatures or by a solver diagnostic.

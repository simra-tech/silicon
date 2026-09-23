# JOINT adverse qualification and numerical observations

Both slow and fast process corners passed the ten-control full-transient
source/draw/sampling qualification, including all 11,512 parameters, 27 legacy
anchors, exact repeat/disabled/temperature-return checks, and the appended SHN
observation's exact projection to the original 18 columns. This qualifies their
declared harness, not electrical accuracy or physical extraction.

The slow corner's six required rail/temperature/common-mode fixtures passed.
Its first sample 77101 is undergoing unchanged binary calibration; held-out
guards/residuals and the 30-sample cohort are **not run** to completion. The fast
corner's low-rail cold fixture reached its original 1,200 s watchdog at a reported
220.114 ns; its other five fixtures passed. The failed fixture retains an exact
11,512-value BEFORE vector, but AFTER, final legacy anchors and the full waveform
are **not run**. Its [read-only failure analysis](qualification/joint586-fast-lowcold-fixture-failure-20260923.json)
does not demonstrate a numerical cause. First fast sample 78101 and fast cohort
remain **not run**.

Separately, typical sample 73048 completed all 28 attempts but **failed** because
cold guard p14 timed out at its original 1,200 s bound. The selected calibration
bracket and completed residual probes passed; they do not waive the failed guard.
The [independent sample audit](qualification/joint586-s73048-failed-audit-20260923.json)
and [failed-leaf analysis](qualification/joint586-s73048-p14-failure-analysis-20260923.json)
retain exact BEFORE parameters and missing AFTER/waveform evidence. All 12,536
warning occurrences preceded the initial transient solution. No retry or
replacement sample is introduced.

A separately authorized full replay of completed typical 73001p00 changed only
the matrix-solver selector to KLU and the fresh waveform output path. The source
includes, seed, integration method, timing, tolerances, codes and models were
unchanged. It completed in simulated-run wall time 292.720 s versus 310.933 s for
SPARSE 1.3. All 11,512 parameters and 27 anchors matched the original and each
other before/after; the full 1.02 µs/18-vector and actual/legacy sampling checks
passed. Both comparator decisions remained HIGH. Exact decoded waveform and
time-grid equality **failed**. Both runs saved 6,653 rows; the largest union-grid
interpolated voltage difference was 51.703 nV on the hard comparator's `xn` node.
These descriptive differences do not replace exact equality. See the
[portable replay and failed-sample receipts](qualification/portable_evidence/joint586-klu-and-73048-failure-20260923/).

The approximately 6% observed JOINT speed difference is not the much larger
T2F-prefix speedup. No JOINT solver adoption or active campaign change follows.
All results remain model-level: unresolved physical applicability and final
extraction qualification are separate obligations.

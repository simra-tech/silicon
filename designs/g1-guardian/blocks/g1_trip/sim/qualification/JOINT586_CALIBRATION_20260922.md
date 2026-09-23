# Full-population 586 calibration: campaign in progress

This is the independently qualified new BGR586/SENSE gm4 population, not the
older nominal-BGR substitution experiment or a new physical C-PEX source.
The [transient qualification](JOINT586_TRANSIENT_20260922.md) fixes the source,
pinned runtime/models, 11,512 mismatch parameters, 27 anchors, 5 MHz clock,
1.02 µs waveform and actual-edge/legacy decision policies. One independent
sample parent runs the original binary algorithm, then all 12 guard conditions
and six half-millivolt residual conditions with frozen calibrated codes.

The first 36 parents use seeds 73001–73036. The independent first-20 audit has
**passed** all 560 leaves and the original calibration, guard and half-millivolt
residual criteria. The remaining 264 samples are in progress and have **not run
to completion**. No 300-sample calibration accuracy or yield result is claimed.
Electrical and numerical failures remain in the attempted population.

## First-20 gate and complete initial-attempt denominator

The [first-20 audit](joint586-first20-audit-20260922.json), SHA-256
`9f9f9aa4e2a642250d2bf86b70406cd7e038406c2f727168247c742d7f4b7ad9`,
independently checks full 11,512-entry inventories, 27 anchors, source/deck/runtime,
waveforms and decisions for seeds 73001–73020. All twenty full parameter vectors
are distinct. Their 560 completed leaves used 245,835.936 summed wall seconds,
about 3.414 CPU-hours per sample. This gives a planning estimate of roughly
30 hours for the remaining 264 samples on thirty one-thread slots, excluding
runtime variation and final audits; it is not a completion guarantee.

[Portable first-20 evidence](portable_evidence/joint586-first20-20260923)
retains exact sample receipts, content-addressed sources and every leaf artifact
hash without copying bulk waveforms. The audit also binds a separate snapshot
of **all 36 initial attempts**, not just the passing gate subset. That snapshot
is parent-level accounting, not an independent full-wave audit of every sample
outside the requested first twenty.

The 36 parent outcomes comprise 33 reported full passes and these three distinct
failures, all retained in the denominator:

- **73023:** numerical completion and parameter checks passed, but hot residual
  p26 at 24.5 mV, codes 128/143, observed soft LOW / hard HIGH instead of LOW /
  LOW. This is an electrical decision failure.
- **73025:** cold residual p24 at 24.5 mV, codes 139/154, hit its 1,200-second
  watchdog. Its decision is missing, not an observed wrong decision. All 28
  conditions were attempted; complete numerical coverage did not pass.
- **73034:** calibration p09 and its one distinct longer-watchdog recovery
  failed as detailed below. Guards and residuals remain not run.

The source, algorithm, clock, per-leaf watchdog and acceptance criteria are
unchanged for seeds 73037–73300. Thirty initial children of this remaining queue
started after the full gate and a fresh CPU/RAM/storage check. Independent
one-sample dispatch changes scheduling only; failed seeds are not replaced.

## First completed independent sample

Seed 73033 completed the full original calibration, all 12 guards and all six
half-millivolt residual conditions. The [independent evidence audit](joint586-calibration-s73033-firstcomplete-audit-20260922.json)
passes all saved full-parameter, waveform, source/runtime and decision checks.
Its completed one-thread leaves took 10,004.812 seconds of summed wall time. The
[portable export](portable_evidence/joint586-firstcomplete-s73033-20260922)
preserves the full sample realization, frozen source objects and every leaf's
artifact hashes without duplicating bulk waveforms.

This one completed sample does not release the first-20 gate or establish
300-sample accuracy, yield or new-geometry physical qualification. The seed
73034 failures below remain in the attempted population.

## Preserved seed 73034 failure

Seed 73034's first nine calibration leaves completed with exact full parameter
contracts and sampled monotonic decisions. Leaf p09, codes 130/146 at 25 C
and shunt 25 mV, hit its declared 1,200-second watchdog at a reported simulated
time of 120.540 ns. The original parent stopped as **failed calibration**;
its unresolved brackets remain soft 129–131 and hard 145–147. Guard and
residual checks for that original parent are **not run**.

All 11,512 BEFORE values equal the original sample vector. The 27 legacy keys
are included in that vector, but the separate legacy print command was after
the unfinished transient and did **not run**. The full AFTER inventory and
exported waveform likewise did **not run**. Consequently an exact comparison
against an original exported waveform prefix cannot be performed.

All 12,561 retained model warnings occurred before the initial transient
solution; none were logged afterward. Progress slowed near the first hard
evaluation edge. This timing association alone does not establish a physical
or numerical cause. The source, cards, solver, tolerances, seed and stimulus
remain unchanged.

The [completed-parent read-only audit](joint586-calibration-s73034-failure-audit-20260922.json)
passes evidence integrity while retaining the failed electrical/numerical
outcome. [Portable failure evidence](portable_evidence/joint586-s73034-original-failure-20260922)
contains the exact parent vector, source/inventory/runner objects and hashes
for every artifact of all ten original leaves. It does not replace the failed
sample with a survivor. Initial completed-parent audit attempts exposed two
auditor representation bugs (audit-only fields and tuple-versus-JSON arrays);
the auditor alone was corrected and three regression tests passed. Simulator
inputs, original data and acceptance criteria were not changed.

The separately declared 2,400-second same-input recovery also **failed its
watchdog**, after 2,400.191 s at a reported simulated time of 362.025 ns. Only
its waveform output path differs in the SPICE deck. Its full 11,512 BEFORE
inventory is exactly the original realization. The AFTER inventory, independent
27-anchor output, waveform and decisions did **not run to completion**. All
12,561 warnings again preceded the initial transient solution; zero occurred
after it, and no simulator error lines were logged. Reporting points alone
do not establish a cause or constitute a waveform.

The [recovery audit](joint586-s73034-recovery-audit-20260922.json) verifies the
frozen inputs and complete BEFORE inventory while retaining the numerical
failure. [Portable recovery evidence](portable_evidence/joint586-s73034-failed-recovery-20260922)
preserves the distinct failed attempt. The original 1,200-second failure and
failed sample remain unchanged. No further retry, sample exclusion, threshold
waiver or population-expansion gate bypass is authorized by this record.

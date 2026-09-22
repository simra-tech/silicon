# Full-population 586 calibration: campaign in progress

This is the independently qualified new BGR586/SENSE gm4 population, not the
older nominal-BGR substitution experiment or a new physical C-PEX source.
The [transient qualification](JOINT586_TRANSIENT_20260922.md) fixes the source,
pinned runtime/models, 11,512 mismatch parameters, 27 anchors, 5 MHz clock,
1.02 µs waveform and actual-edge/legacy decision policies. One independent
sample parent runs the original binary algorithm, then all 12 guard conditions
and six half-millivolt residual conditions with frozen calibrated codes.

The first 36 parents use seeds 73001–73036. The required first-20 completed
audit and the remaining 264 sample launches have **not run to completion**.
No 300-sample calibration accuracy or yield result is claimed. Electrical or
numerical failures remain in the attempted population.

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

One separately declared 2,400-second same-input recovery has been launched
under a distinct run ID. Only its waveform output path differs in the SPICE
deck. Its completed numerical, full-before/after and decision checks are
**not run to completion** at this record. The original 1,200-second failure
remains unchanged regardless of that diagnostic outcome. No automatic repeat,
sample exclusion, threshold waiver or population-expansion gate bypass is
authorized by this record.

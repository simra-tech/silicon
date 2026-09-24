# Priority21 candidate: incremental clock mutual-C follow-up

Prospective status: **not run**. Exactly two new low/high input anchors, one
unchanged seed71001, are authorized for this diagnostic; not two independent
samples. Apply the original clock diagnostic's source, solver, sample times,
27-parameter, correct-guard, local-gain convergence and 50 µV incremental
input-referred limits without relaxation. Reuse the four completed zero-added-C
gain probes and the two exact-host controls with unchanged source identities.
The clock remains the fixture's 10 MHz, not the integrated nominal 5 MHz.

Replace only the added mutual capacitor by **5.286345256 fF**, from the
priority21 candidate's actual-fill, floating-fill 24 µm-context / 20 µm-end
clock clip. Summary SHA256:
`2758f6c62836e699aa8fa3120e9dff6451b3864ff7f3b3661e47890c2a0bea90`.
Candidate GDS SHA256:
`04fb6443010bed31595974cca636a9dbd292fda47f0cd45507688f05b1c9a7d8`.
The paired parent mutual value is 5.233830490 fF; its observed increase is
0.052514766 fF, about 1.003%. Numerical representation is rounded to nine
decimal fF places, checked against extraction within 1e-9 fF.

The original 300 fF assumed ISENSE ground load is retained. The extracted
ground-capacitance deltas are not incorporated in this mutual-only diagnostic;
the clock source remains ideal. No full-RC, driver-loading, return-path, full
matrix-context convergence, PVT, receiver-pulse or layout-adoption claim follows.
Only three of the 21 modified via sites are covered by this physical clip.
The original context-convergence failure remains failed.

Fresh IDs `clock-via-low-20260922-a` and `clock-via-high-20260922-a`, each with
the same 300 s watchdog and pinned runtime/PDK as the original contract. Outputs
use HOME while the external results volume is mounted read-only in purpose for
immutable input access; no external output growth is authorized. Reserve 0.05
GiB HOME after a fresh CPU/RAM/quota/inode gate, maximum two single-CPU workers.
Actual physical measurements are **not applicable** to this numerical check.

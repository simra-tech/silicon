# Remaining local via coverage: staged proposal

## Completion update, 22 September

Cohorts2–4 completed in parallel under a fresh resource gate, using the same
qualified clip/parser/reduction/AC logic and original bounds. All96 actual AC
comparisons and six synthetic controls **passed**. Local coverage is now21/21
changed stages. The [compact receipt](priority-via-remaining-20260922-r1/manifest.json)
binds every retained bulk artifact and exact compact copy; manifest SHA256
`e6be2fc6ea9849ae1083de480333468a365b90c1a8757e641a1f05e1500297bb`.
Cohort2/3/4 wall times were114.587/112.635/111.742s including container overhead;
bulk output was4,125,365/3,637,606/3,645,729bytes respectively.

Actual-fill floating-load increases were0.04223–0.07650fF for the remaining
IPTAT/VREF sites, except VDDA stage20 at0.17831fF. These are local simulated
capacitance differences under the documented boundaries, not actual
source-impedance transient errors. Full-route RC/convergence, source-loaded
transients, per-cut current/IR and adoption remain **not run**. Physical
measurement and statistical seed are **not applicable** to these deterministic
checks. Earlier wide-window timeout/context failures remain.

The staged proposal below is retained as the pre-run record. Its unrun-cohort
and per-cohort-approval statements are superseded by these results and the
owner's bounded ordinary implementation/test-cycle authorization.

[Exact prepared windows and changed rectangles](remaining-local-via-coverage-plan-20260922-r2.json), SHA-256 `a225de9b6411711d8dae39242bcb0ed796307b6afcc71e32c84fe29656e32f1f`, bind the unchanged SENSE-parent GDS `af9ac300...` and priority21 GDS `04fb6443...` through the full hashes in the plan. These are 12 × 12 µm windows centered on each listed cut. The existing clock interval and two pilot sites cover stages 2,3,4,10,19; no other stages inherit their results.

| Cohort | Stage | Target net | Center (µm) | Changed stages fully in window |
|---|---:|---|---|---|
| 1 | 0 | gate_o | (1018.56,732.48) | 0 |
| 1 | 1 | gate_o | (1018.56,882) | 1 |
| 1 | 5 | cmp_clk | (965.76,844.9) | 5 |
| 1 | 6 | iptat | (733.44,447.72) | 6 |
| 2 | 7 | iptat | (733.44,781.2) | 7 |
| 2 | 8 | iptat | (645.12,781.2) | 8 |
| 2 | 9 | iptat | (645.12,949.2) | 9,16 |
| 2 | 16 | vref | (644.64,948) | 9,16 |
| 3 | 11 | vref | (732,774.48) | 11 |
| 3 | 12 | vref | (644.16,933.24) | 12 |
| 3 | 13 | vref | (845.76,1022.7) | 13 |
| 3 | 14 | vref | (972.48,1022.7) | 14 |
| 4 | 15 | vref | (644.16,774.48) | 15 |
| 4 | 17 | vref | (644.64,989.94) | 17 |
| 4 | 18 | vref | (845.76,989.94) | 18 |
| 4 | 20 | VDDA | (568.02,948.36) | 20 |

No proposed window partially intersects a changed landing/cut rectangle. Stages 9 and16 share geometry coverage but target **different actual nets**: each requires its own target identity, matrix reduction and eight paired AC checks. Neither result may silently count as the other's load measurement.

Cohort1 completed **passed** after its fresh resource gate: all 32 actual AC comparisons and two synthetic controls, with 2,982,009 bytes of output. Actual-fill floating-load deltas were +0.0677300234 fF (stage0), +0.0625083792 fF (stage1), +0.0560064499 fF (stage5), and +0.0292380617 fF (stage6). [Summary](priority-via-local-cohort1-20260922-r1/summary.json) retains the complete controls. Cumulative local coverage is now nine of21 stages: 0,1,2,3,4,5,6,10,19. [Runner](run_local_via_cohort1.py) and [clip helper](prepare_local_via_cohort1_clip.py) are mechanical forks of the qualified two-pilot harness: fixed allowed IDs, four labels, 32 MiB instead of 128 MiB, 34 required AC controls instead of18. The original files, extraction logic, strict parser, matrix reduction and tolerances are unchanged. Cohorts2–4 (12 stages) are **not run**, require separate approval/fresh gates and have no automatic continuation.

Each paired site requires parent/candidate × no-fill/actual-fill × grounded/floating-fill = **eight** independent capacitor-network AC comparisons. Each cohort also reruns the 6/3.5 fF synthetic controls. Required checks are full-source physical target membership at every route anchor; unique per-piece labels; complete source/clip nontext XOR; preserved GDS hashes; strict capacitance parser; explicit finite completion; finite Schur charge residual ≤1e-25 F; AC agreement ≤1e-25 F; and unchanged 120-second extraction/KPEX and 30-second AC limits. A failure stops the cohort; there is no wider-window or watchdog escalation. The existing harness checks total output after each bounded phase; it is not a filesystem quota mechanism.

The completed two pilots used 1,664,636 bytes and48.82 bounded-child seconds. Pure same-complexity scaling predicts about13.3 MB and390.6 seconds for16 sites, or3.33 MB and97.6 seconds per four-site cohort. These are estimates, not limits or guaranteed completion; local net/fill complexity is not uniform. Every cohort has a32 MiB stop gate and separate resource approval.

Even complete local coverage would leave **not run**: full-route resistance/capacitance and convergence; VREF/IPTAT/GATE operating-source-impedance transients; supply-feed voltage drop and per-cut current partition; PVT coupling, EM/pulse qualification, global-fill changes, and geometry adoption. GATE local capacitance does not validate held-off/unsafe-IO state assumptions, pad output loading or safe external behavior. The existing mutual-only clock dynamic pass does not qualify ground-load changes or these other nets. Existing full-IO failure, wide-IPTAT timeout and context-convergence failure remain unchanged.

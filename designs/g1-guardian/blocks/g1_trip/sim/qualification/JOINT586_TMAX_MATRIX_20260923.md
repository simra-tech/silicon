# Matched timestep diagnostics — no method adoption

Simulated on the original baab SENSE /586 BGR/full TRIP source, with the pinned runtime, SPARSE solver, physical mismatch draws, full11512+27 observations, original1200s watchdog,1.02µs endpoint and sampling rules. Only the fourth TRAN argument and output destination changed. These are definition-selected ±0.5mV residual pairs, not±0.1mV qualification. Fast78101 retains its originally qualified fixed nodeset.

| Original sample/leaf | Original0.2ns wall(s) | Diagnostic1ns wall(s) | Numerical/full-vector audit | Unchanged prospective consistency screen |
| --- | ---: | ---: | --- | --- |
| Typical73001p22 | 444.510 | 190.720 | passed | passed |
| Typical73001p23 | 416.312 | 194.202 | passed | passed |
| Slow77101p52 | 371.936 | 205.590 | passed | failed |
| Slow77101p53 | 377.229 | 212.327 | passed | failed |
| Fast78101p54 | 339.799 | 182.785 | passed | passed |
| Fast78101p55 | 319.490 | 186.877 | passed | passed |

The independent pinned-runtime audit is `joint586-tmax-matrix-audit-20260923-c.json`, SHA256 `62dcb240614cd89890d6ed2c8c735aca96048f45e647e3a11770ad8020a71e1e`. All exact original waveform/grid comparisons failed and remain separate from the engineering screen.

The original auditor assumed gzip-only new output and failed. The representation-aware host re-audit then failed exact comparison of several RMS values at the final binary64 bit. Running that unchanged representation-aware auditor in the pinned simulator runtime reconstructed all six receipts exactly. Both earlier failed audit receipts remain retained; neither simulation nor threshold was changed.

## Smaller-step hypothesis

The separately frozen original slow pair used0.5ns instead of1ns, with the same original sources, inputs and prospective bounds. Both simulations and independent evidence audits passed, but both consistency screens failed. p52 took246.152s and p53 took258.322s. Audit SHA256 `1dd196ef308f4c9a9b892fac1dd7b2cdb975c5532e844f6657f47bb10b0b94db`.

The worst `cmp_soft` differences remain0.612076V and0.660606V, exceeding the unchanged50mV whole-wave screen. For p53, a saved candidate sample at20.456924ns is0.54327V while the original trace is about1.20387V. The original interpolation bracket is11.379ps and candidate neighboring bracket4.149ps. Both1ns and0.5ns p53 have an extra falling/rising0.6V crossing near the first clock; original traces have none. p52's paired falling-edge shift is about−61.774ps. Late actual/legacy decisions and quiet analog checks agree, but do not waive the other failures.

These saved-data observations do not establish an internal solver cause. First-clock location is descriptive, not an excluded startup window or an interpolation-error excuse. The branch stopped after this pair. No method/population/new-SENSE adoption, universal error bound or campaign-wide speedup is established.

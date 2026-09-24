# Single-leaf maximum-step diagnostic

Status: simulated numerical completion **passed**; prospective engineering
consistency screen **passed**; exact waveform bytes, numeric rows and time grid
**failed**. Population adoption, near-threshold qualification and qualification
of a changed SENSE source are **not run**.

The original completed seed73001/p00 source, model/runtime identity, physical
draw, code0/0, stimulus, measurements and 1.02µs endpoint were preserved. The
only analog-control change was the fourth transient argument, maximum step
0.2ns to1ns. The 1200s watchdog was unchanged. New output destinations were
separate. The original result remains authoritative historical evidence.

| Simulated observation | Original | Diagnostic |
| --- | ---: | ---: |
| Wall time | 310.933s | 188.663s |
| Saved rows | 6653 | 2650 |
| Full11512 parameters and legacy27 | reference | exact |
| Actual-edge and legacy late-three decisions | reference | unchanged |

The observed wall-time ratio was1.648× for this leaf, not an established
campaign speedup. Maximum interpolated paired clock/output crossing shift was
0.0903ps, below the declared200ps screen; both crossing brackets also met the
declared resolution screen. Maximum phase-aligned analog difference was7.229µV
(screen100µV). Maximum union-grid analog difference was29.624µV
(screen1mV). Other internal/output nodes were screened separately at50mV.

These are prospective engineering comparison screens, not proven universal
integration-error bounds. Saved accepted-grid observations do not reveal
rejected internal solver steps. Linear interpolation is not an independent
error guarantee. A strong-HIGH code0 result does not establish calibration,
residual-boundary or adverse-corner equivalence.

Reproduction uses `prepare_joint586_tmax_probe.py`,
`run_joint586_tmax_probe.py` and `compare_joint586_tmax_probe.py`. The frozen
packet is `joint586-s73001p00-tmax1ns-20260923-a.json`, SHA256
`6d0b413c4b1f97f1bf741bdb94a6de02b15371630b69d919a3fa0cef0499608d`.
The result summary SHA256 is
`bc96f12bbb4bbb40616879f41b1eae5b86ed8d6e1fcb4488ef3fa3c7e35853bf`.
Six transform/runtime tests, six comparison negative controls and two host
release/audit controls passed. PDK, simulator, image and model hashes are
asserted against the original frozen runtime in preparation/provenance.

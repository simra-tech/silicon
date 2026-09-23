# Final586 T2F independent calibration campaign

The first three distinct samples, 74101–74103, passed their independent evidence
audit and original two-point linear calibration criterion. This is an early
three-sample result, not completion of the required 300-sample population or a
yield claim. The next seventeen samples are in progress; the remaining 280
are **not run** pending the separate first-twenty gate.

| Seed | −40 °C simulated error | 125 °C simulated error | Sum of four leaf wall times |
|---|---:|---:|---:|
| 74101 | −1.442275 °C | −0.406123 °C | 1,621.973 s |
| 74102 | −1.135664 °C | −0.381607 °C | 1,380.990 s |
| 74103 | −1.371588 °C | −0.432894 °C | 1,336.415 s |

Each sample calibrates at 25/100 °C at nominal rails, freezes those linear
coefficients, then evaluates −40/125 °C against the original ±2 °C requirement.
All twelve 32 µs leaves passed full 3,180-entry BEFORE/AFTER and cross-temperature
identity checks, finite thirteen-column waveform and external HBT VCE checks.
Every one of the 1,129 randomized primitives has three numerically distinct
draws across the three seeds. The independent auditor binds each source, deck,
runtime, parameter vector, waveform, measurement and calibration result.

The [first-three audit](t2f586-first3-audit-20260922.json) has SHA-256
`552d1cbe11319667ccb33b178eb345df0d99da9398df9c470bd2e40829a5d5c7`.
[Portable evidence](portable_evidence/t2f586-first3-calibration-20260923)
contains exact parent receipts, content-addressed source/inventory/runner
objects and every leaf-artifact hash, without duplicating bulk waveforms.

The immutable runner is `run_586_calibration_sample.py`. Its prospective
300-seed contract is `t2f586-calibration-contract-20260922-a/contract.json`,
SHA-256 `e4ae423a1c969457d94dad81050a7297969833eab1d416f11a4943e1308b764b`.
Seeds are 74101–74400; each leaf retains its 600-second watchdog. Failed leaves
and samples remain in the denominator, with no automatic retries or replacement
seeds. The only sample transforms are the declared seed and two temperature
directives. Original source devices, model cards, rails, timing and load remain
unchanged. One-sample parent scheduling changes throughput, not calibration.

The first three samples used about 24.1 minutes per sample on average. A simple
planning extrapolation gives about 120.5 CPU-hours for 300, or 20.1 hours on six
workers, before qualification/audit overhead and runtime variation. This is a
forecast, not a completed result or a guaranteed bound; the per-leaf cap remains
600 seconds.

The full six-control typical-population qualification, including exact
same-instance temperature return, is recorded separately in
[T2F586_POPULATION_CONTRACT_20260922.md](T2F586_POPULATION_CONTRACT_20260922.md).
The source remains the final586-derived mismatch BGR `7de0fc30697d1e81...` and
T2F `7770b233e5681759...`, with full hashes in every provenance receipt.
Runtime is ngspice 46, image manifest
`5fd78498e578c6e9ec10828c248ca3790fc88250ff6caf545521b29e448ea3c0`,
PDK `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`.
This campaign does not adopt the new coordinated physical capacitance or
qualify actual pad loading; those affected checks remain **not run** here.

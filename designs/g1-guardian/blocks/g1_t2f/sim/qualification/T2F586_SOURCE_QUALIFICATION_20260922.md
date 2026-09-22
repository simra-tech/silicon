# T2F final-reference source controls

These simulated controls qualify the nominal BGR source
`586ffb58b6af31c77a2e7cbcb83b173ffa4713ec62401da30901c5a7e606283b`
with the unchanged T2F source
`441edabc0484c9de1e035d585369f37d460afe32370e73935044693bbfd0c78a`.
Historical T2F statistical cohorts used a different BGR source and are not
coverage of this combination. No model card or canonical device source changed.

| Control | Status | Simulated evidence |
|---|---|---|
| Historical 12.5 °C host replay | passed | 32 µs; 53.375 s wall; original 13-column decoded bytes, numeric rows and time grid exact |
| Historical source plus explicit OP/full 580-query instrumentation | passed | 32 µs; 52.989 s wall; all parameters before/after exact and original waveform exact |
| Source-only BGR586 substitution at 12.5 °C | passed | 334.328 s wall; 17,974 finite rows through 32 µs; all 3,180 before/after parameters and both retained reference inventories exact |
| BGR586 nominal 25/100 °C calibration and −40/125 °C endpoints | passed | All four full inventories exact; held-out residuals −1.260980 °C and −0.419880 °C, within the original ±2 °C criterion |
| Final-source mismatch, intermediate temperatures, PVT and temperature return | not run | Historical cohorts cannot be relabelled |
| Actual pad load or new coordinated physical capacitance | not run | Existing source capacitances, 50 fF output and ideal IPTAT termination only |

The first two completed runs are `t2f586-source-controls-20260922-a-old-host`
and `t2f586-source-controls-20260922-a-old-inventory`. Compact public records are
under `portable_evidence/t2f586-source-controls-20260922/`; their manifests
bind retained bulk waveforms, logs and source copies by repository-relative run
identity and SHA-256. No machine-specific storage location is required to read
the summaries.

The paired source substitution simulates 1.445337 MHz and a maximum external
T2F HBT VCE magnitude of 1.039737 V, below the unchanged 1.6 V check. Its source
diff is intentional, so waveform equality across the old and new BGR sources
is not an applicable gate. All four nominal anchors completed with the same
full 3,180 parameters before/after and across temperatures:

| Temperature | Frequency, simulated | Role / residual | Wall time |
|---|---|---|---|
| −40 °C | 1.182187 MHz | held out / −1.260980 °C | 321.137 s |
| 25 °C | 1.507431 MHz | calibration | 334.231 s |
| 100 °C | 1.875571 MHz | calibration | 553.260 s |
| 125 °C | 1.996224 MHz | held out / −0.419880 °C | 531.749 s |

The [four-anchor analysis](t2f586-nominal-calibration-20260922.json) binds the
completed receipts and original linear criterion. Its slope is 4,908.533 Hz/°C.
The 125 °C maximum external HBT VCE is 1.056303 V. These are nominal simulated
results, not a statistical or physical-source adoption claim. All seven
completed controls have compact portable exports in the directory above.

## Frozen contract

The historical 12.5 °C deck is unchanged for the host replay. The second control
adds an explicit operating-point analysis and complete parameter queries; its
exact waveform gate establishes transparency for this specific fixture rather
than assuming it. The new-reference paired body is identical after removing
query output, with only the copied BGR source content substituted. Candidate
controls require all 338 T2F parameters to equal the old instrumented control
and all 2,842 BGR parameters to equal the retained nominal BGR inventory, both
before and after each transient. The total inventory covers 411 MOS, 409
resistors, 307 HBTs and two CMIM devices.

All controls retain 3.3/1.2 V rails, ideal 1 V IPTAT termination, 50 fF output,
the original 1–1.01 µs enable edge, `tran 5n 32u`, Gear/tolerances and frequency
measurement edges 8–24. The original deck explicitly selects one simulator
thread, overriding the unchanged initialization file. Full finite 13-column
output, a 32 µs endpoint, valid original frequency measurements and the existing
1.6 V T2F HBT external VCE check are required. Watchdogs are 300 s for the old
controls and 600 s for new-reference controls; a failed predecessor stops
dependent launches. These bounds are not electrical acceptance criteria.

The four-anchor analysis uses only
`T_est = 25 + (f-f25)/((f100-f25)/75)` and the original ±2 °C held-out endpoint
limit. No LUT, reciprocal correction, recalibration at held-out temperatures,
population claim or source adoption follows from a nominal control.

## Built against and reproduction

| Item | Pinned identity and establishment |
|---|---|
| PDK | `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`; live COMMIT and model/OSDI file hashes checked against preparation |
| ngspice | 46; full live version output bound in each provenance record |
| Container image | `sha256:5fd78498e578c6e9ec10828c248ca3790fc88250ff6caf545521b29e448ea3c0`; pinned runtime identity |
| Preparation | `t2f586-source-controls-20260922-a.json`; SHA-256 `db53e71329d791a99df254dd4071a64e2d5e41bbaa1b8c8df0ee1ef3894e5986` |

Preparation allocates fresh run IDs and writes declared deck/source differences:

```sh
python3 designs/g1-guardian/blocks/g1_t2f/sim/qualification/prepare_586_source_controls.py --campaign-id NEW_LOWERCASE_ID
```

Each prepared label is executed in order through the pinned runtime after a
resource gate; use a CPU allocated to the job:

```sh
G1_CPUSET=ALLOCATED_CPU G1_CPUS=1 G1_MEMORY=4g G1_CONTAINER_ENGINE=podman \
G1_WORKDIR=designs/g1-guardian/blocks/g1_t2f/sim/qualification \
flow/run.sh env G1_ARCHIVE_NEW_WAVES=1 python3 run_586_source_control.py \
  --packet NEW_LOWERCASE_ID.json --label old-host \
  --image-id sha256:5fd78498e578c6e9ec10828c248ca3790fc88250ff6caf545521b29e448ea3c0
```

The remaining labels are `old-inventory`, `new-paired`, `new-t25`, `new-t100`,
`new-tm40` and `new-t125`. Seven focused regression tests passed with the host
Python environment providing NumPy. A separate Python 3.11 test attempt lacked
NumPy and did not execute tests; it was not a simulation failure.

## Additional held-out nominal temperatures

The separate [intermediate-temperature audit](t2f586-nominal-intermediates-analysis-20260922.json)
retains the same original 25/100 °C calibration. Simulated −20, 0 and 50 °C
checks passed with residuals −0.770671, −0.347579 and +0.192089 °C,
respectively. Their full 3,180 BEFORE/AFTER values match the nominal reference.

The 75 °C attempt **failed its 600-second numerical watchdog**, reaching a
reported 27.4819 µs of the required 32 µs. Full 3,180 BEFORE values and all
source/deck/runtime bindings passed. AFTER inventory, exported waveform,
frequency and calibration residual are **not run to completion**. All 3,176
warning lines preceded the initial transient solution; none occurred afterward,
and no simulator error lines were recorded. This does not establish the cause
of slow progress. No held-out result is inferred or fitted for the missing point.

[Portable intermediate evidence](portable_evidence/t2f586-nominal-intermediates-20260922)
preserves all four attempted outcomes, including the failed 75 °C run. The four
original anchor passes above remain valid; expanded nominal temperature
coverage is incomplete, and no full-range or population claim follows.

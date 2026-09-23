# T2F586 mismatch qualification

Status: **passed six-control harness qualification**. All six controls completed;
the return control took 1,491.368844 seconds. Full inventories, repeated and
disabled waveforms, and returned 25 °C waveforms passed their exact comparisons.
All 1,129 primitives changed numerically between the two enabled seeds.
This is a new population, not equivalence to any historical T2F seed or joint
SENSE realization. It is not a statistical accuracy or yield result.

The completed audit is `t2f586-population-qualification-20260922.json`, SHA-256
`ccb86b47f7b7dbd317fcb9fd6a30f134adf9a0b8e3910832b130ebd47f97677d`.
Portable receipts and complete retained-artifact hashes are under
`portable_evidence/t2f586-population-controls-20260923/`.
The independent 300-sample campaign remains **not run to completion**; its first
three distinct samples are a separate staged audit, not part of these controls.

The final-reference combination requires its own electrical coverage. The
original 300-independent-sample obligation, 25/100 °C two-point linear
calibration, −40/125 °C held-out ±2 °C criterion, timing and loading are not
relaxed. The historical old-reference cohorts and their failures remain
separate. A six-control pass would qualify a harness, not provide a population
accuracy or yield result, or adopt a new physical extraction.

## Exact preparation

`t2f586-population-controls-20260922-a.json` has SHA-256
`6916e82c3254981334591494efb458a804e027dbb7812efee4a776b48470f001`.
Its inventory has SHA-256
`d21d5c2ce4279f71ac2620e225e4bed19ef409c7173a0996a94fe42f2a2d0168`:
1,129 original primitive calls, comprising BGR 1,036 and T2F 93, with all
3,180 primitive parameter queries (2,842 BGR and 338 T2F).

Simulation-only source copies add `mm_ok=1` or `mm_ok=0` at precisely those
original calls. Removing the flags restores each complete nominal source
byte for byte. Canonical sources and PDK cards are unchanged.

| Source copy | SHA-256 |
|---|---|
| Enabled BGR | `7de0fc30697d1e81d40c3200a511faf0479cfd8b397bbaa3cec6dbc4fa758c61` |
| Enabled T2F | `7770b233e5681759fb6dc8cfbd6f9297459555ab5d14dc376ee9a774c0183f0b` |
| Disabled BGR | `a465eaade559e57955d9e4455e425686c5a497e8672c078f9a839adaf79a9a80` |
| Disabled T2F | `02957521e3a42c31c1ae8540d0c53d40920c4d14e4aa8931b7c429a102f2121b` |

The deck body changes only the five library section selections to their pinned
mismatch sections and the declared initial temperature to 25 °C. The control
block seeds and resets once, then queries the full inventory before and after
each original `tran 5n 32u` phase. Original rails, 50 fF output, ideal 1 V IPTAT
termination, finite enable edge, Gear/tolerances, frequency measurement edges
and 13 waveform columns remain unchanged. The inherited title still says
nominal 12.5 °C/seed 51001; that stale comment is retained explicitly. Executable
temperature, seed and mismatch controls in the prepared decks are authoritative.

## Six controls and gates

| Label | Seed | Temperature sequence | Wall watchdog |
|---|---|---|---|
| enabled | 74001 | 25 °C | 600 s |
| repeat | 74001 | 25 °C | 600 s |
| changed | 74002 | 25 °C | 600 s |
| disabled | 74001 | 25 °C | 600 s |
| disabledchanged | 74002 | 25 °C | 600 s |
| return | 74001 | 25 → 125 → −40 → 25 °C, one initial seed/reset | 2,400 s |

Every phase requires full finite 3,180-entry inventories in the declared order,
exact before/after values, a finite 32 µs waveform, original frequency
measurements and the unchanged external T2F HBT VCE ≤1.6 V check. All returned
temperature inventories must remain exactly the same physical realization.

The changed seed must numerically vary at least one randomized parameter of
**every** original primitive in each block, not merely one representative
device or a text representation. Enabled/repeat, initial/returned 25 °C and
disabled/changed-disabled comparisons require exact decoded waveform bytes,
numeric rows and time grid. Disabled controls must additionally match the
retained nominal 25 °C waveform and full nominal inventory exactly. No numerical
tolerance silently replaces a failed equality check.

The runner requires the completed nominal calibration analysis and its live
receipt hashes before launching. A single allocated CPU executes the reviewed
controls sequentially, with fresh resource gates. Failures and watchdogs are
retained; no retries or statistical dispatch are built into this qualification.
The public analyzer performs the separate six-control comparison. Intermediate
temperatures, PVT, actual pad loading, a statistical ensemble and coordinated
physical capacitance are **not run** by this contract.

## Reproduction

Prepare fresh lowercase IDs with `prepare_586_population.py --campaign-id ID`.
The declared differences and source inventory are retained in each prepared
run. After the prerequisite nominal analysis has passed, execute each label
through the pinned runtime with the allocated CPU:

```sh
G1_CPUSET=ALLOCATED_CPU G1_CPUS=1 G1_MEMORY=4g G1_CONTAINER_ENGINE=podman \
G1_WORKDIR=designs/g1-guardian/blocks/g1_t2f/sim/qualification \
flow/run.sh env G1_ARCHIVE_NEW_WAVES=1 python3 run_586_population_control.py \
  --packet ID.json --label enabled \
  --image-id sha256:5fd78498e578c6e9ec10828c248ca3790fc88250ff6caf545521b29e448ea3c0
```

Observed ngspice 46, PDK commit
`84374023ee8b4b126bebbba67fcbada0a9c0ff0b`, all model/OSDI hashes, copied source
hashes, runtime identity and command arguments are checked and recorded by
each run. Fourteen focused nominal/population regression tests passed before
any population simulation.

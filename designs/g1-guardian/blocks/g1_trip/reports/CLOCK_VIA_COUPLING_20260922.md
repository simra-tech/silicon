# Priority21 via candidate: nominal mutual-coupling diagnostic

**Passed within this two-anchor diagnostic**, not full-route or layout adoption.
The new candidate mutual capacitor is 5.286345256 fF, bound to GDS
`04fb6443010bed31595974cca636a9dbd292fda47f0cd45507688f05b1c9a7d8`.

| Check | Status | Simulated result / limitation |
| --- | --- | --- |
| Two new low/high leaves, same seed71001 | passed | Complete0.52µs, exact27 parameters and source/model/runtime pins, clean solver logs |
| Last three decisions for both comparators at both anchors | passed | All12 correct and unchanged |
| Input-referred incremental error | passed | Maximum8.66733µV against prospective50µV; retained paired5/10µV local-gain checks agree within0.2751% |
| Saved piecewise-linear transient differences | passed as finite diagnostic data | Peak ISENSE13.46455mV, conditioner155.1423µV; not continuous-time bounds |
| Whole-matrix context convergence | failed | Original18.2721% failure retained, not waived |
| Other18 via sites, ground-load deltas, fullRC, actual clock driver, other corners/seeds and full fast-latch waveform | not run | This clip covers only3of21 modified sites; ideal10MHz fixture and assumed300fF ground load retained |
| Physical measurement for numerical diagnostic | not applicable | Silicon measurements remain not run |

The new leaves took135.092/159.263s of solver time, each under the same
300s watchdog. Pinned ngspice46, IHP PDK
`84374023ee8b4b126bebbba67fcbada0a9c0ff0b`, image manifest
`sha256:5fd78498e578c6e9ec10828c248ca3790fc88250ff6caf545521b29e448ea3c0`.
These are two input anchors of one sample, not two independent samples.

[Prospective contract](../sim/CLOCK_VIA_CANDIDATE_DIAGNOSTIC_20260922.md),
[complete evaluation](../sim/qualification/clock-via-coupling-diagnostic-20260922-a.json)
and [portable run exports](clock-via-coupling-20260922/) preserve commands,
source snapshots and hashes of separately retained bulk data. Eight focused
harness/checker unit tests passed. Re-evaluation with retained inputs:

```sh
python3 designs/g1-guardian/blocks/g1_trip/sim/check_clock_coupling.py --via-candidate --output FRESH_RESULT.json
```

No production GDS, PDK model or rule deck changed. This result cannot cancel
the joint calibration failure, unsafe IO sequencing or full-IO LVS failure.

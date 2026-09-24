# Nominal incremental clock-coupling result

**Passed within the declared diagnostic scope**, not full-interface qualification.
All values are simulated using pinned ngspice 46 and IHP PDK
`84374023ee8b4b126bebbba67fcbada0a9c0ff0b`.

| Check | Status | Result |
| --- | --- | --- |
| Two zero-added-C host controls | passed | Exact 27 parameters, sources/models/runtime and every saved waveform byte versus archived low/high anchors |
| Two coupling and four local-gain runs | passed | Complete 0.52 µs endpoints, clean solver logs and exact original 27 parameters; 300 s watchdog unchanged |
| Local gain from +5/+10 µV shunt perturbations | passed | All 12 phase-specific gain pairs within 1%; worst relative difference 0.2751% |
| Incremental decision-time error | passed | Maximum 8.5811 µV shunt-equivalent against the prospective 50 µV diagnostic limit |
| Correct low/high guard decisions | passed | Both comparators' last three decisions unchanged at both anchors |
| Whole-interval full capacitance-matrix context convergence | failed | Earlier 18.2721% maximum relative change retained; not waived by this mutual-only diagnostic |
| New via-candidate geometry, other corners/seeds, full routed R/C and total error budget | not run | No adoption or broader qualification |
| Physical measurement for this numerical diagnostic | not applicable | Silicon coupling measurement remains not run |

Only 5.233872140 fF between ISENSE and the clock was added; the existing
assumed 300 fF ground load remains. The saved piecewise-linear difference
peaked at 13.3324 mV on ISENSE and 153.609 µV after the conditioner. These
are not continuous-time peak bounds or additional product acceptance limits.
The existing 10 MHz fixture has ideal 1.2 V/0.2 ns clock edges, actual BGR
C-PEX and schematic SENSE/TRIP. Physical codes are 171/240 at calibrated
nominal-40 mV hard-threshold low/high anchors, not a full 50 mV threshold claim.

The [prospective contract](../sim/CLOCK_COUPLING_DIAGNOSTIC_20260922.md)
preserves extraction limitations. The
[complete evaluation](../sim/qualification/clock-coupling-diagnostic-20260922-a.json)
records every gain, decision and input-referred error.
[Portable run exports](clock-coupling-20260922/) retain exact summaries,
provenance, runner snapshots and hashes for separately retained bulk artifacts.

Re-evaluate retained local waveforms from the repository root with:

```sh
python3 designs/g1-guardian/blocks/g1_trip/sim/check_clock_coupling.py --output FRESH_RESULT.json
```

Seven focused harness/checker unit tests passed. No PDK model or rule-deck
changes were made. This pass cannot cancel unrelated calibration, comparator,
IO power-sequencing or physical sign-off failures.

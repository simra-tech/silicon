# Standalone reference electrical charge exploration

Six simulations and the [independent audit](reference-pilot-audit-20260922.json)
passed numerical completion, exact source/model/2,842-parameter binding,
before/after parameter freeze and imposed-charge integration. This is the
original `586ffb58…` electrical reference with 329 historical parasitics, not
the new physical assembly's extracted capacitance view.

At 27°C and 3.3 V, IPTAT is held at 1 V by the measurement source and VREF has
1 pF load. Seed42001 and nominal libraries disable mismatch. A zero-current
control and ±100 fC pulses into `pbias` run to40µs at maximum timesteps2ns and1ns.
The imposed pulse starts20µs, has10ps edges and990ps plateau; positive current
injects charge. All other deck content is exact across timestep pairs after
normalizing only the output directory.

| Simulated1ns result | +100fC | −100fC |
|---|---:|---:|
| VREF minimum | 1.040416395V | 1.045302194V |
| VREF maximum | 1.045618674V | 1.050523712V |
| Maximum VREF return error,35–40µs | 0.2873nV | 0.2855nV |
| Maximum IPTAT return error,35–40µs | 8.165pA | 7.828pA |

Pre-pulse VREF is1.045460219V and IPTAT4.134131µA. All six runs pass the prior
load-test diagnostic return limits of1mV VREF and0.1% IPTAT. These are not
allocated radiation or transient-safety criteria.

The2ns→1ns full-trace differences, interpolating the finer trace onto the
coarser times, are at most19.308µV VREF and1.339nA IPTAT for charged runs.
After35µs, they are at most0.151nV and45.748pA. This reports timestep sensitivity;
an exact-waveform or independently allocated numerical-convergence gate is
**not run**. The smallest reported residuals must not be interpreted as a
model-accuracy bound.

The first read-only host audit failed exact arithmetic comparison because it
used the host Python runtime rather than the pinned simulation runtime. The
pinned audit then failed its deck normalizer on `1.0n` versus `2n` spelling.
Correcting that audit-only normalization preserved the original six decks,
waves and parameters; the pinned audit passed. No simulator rerun or tolerance
change was used to resolve these audit failures.

Built against ngspice46, pinned image manifest
`5fd78498e578c6e9ec10828c248ca3790fc88250ff6caf545521b29e448ea3c0`,
IHP PDK`84374023ee8b4b126bebbba67fcbada0a9c0ff0b`. Exact model, deck, log,
waveform and runner hashes are in the audit. Commands, using a fresh results
directory for each run:

```sh
bash flow/run.sh python3 designs/g1-guardian/blocks/g1_trip/sim/set_exploration/run_reference_pilot.py --charge-fc 100 --polarity 1 --maxstep-ns 1 --output NEW_RESULTS_DIRECTORY
bash flow/run.sh python3 designs/g1-guardian/blocks/g1_trip/sim/set_exploration/audit_reference_pilot.py --results-root RESULTS_ROOT --output NEW_AUDIT.json
```

Use charge0/polarity1 for controls and charge100/polarity±1 for charged cases;
repeat with maxstep2 and1. Each simulation uses one CPU and a300s watchdog.
Six simulator times are retained individually; finer-step walltimes are
approximately283–291s excluding container startup and export.

Full-chain downstream recovery and model-reliability/fault-survival checks:
**not run**. Radiation LET, collected charge, cross-section and upset rate:
**not applicable** to this imposed electrical-charge characterization.

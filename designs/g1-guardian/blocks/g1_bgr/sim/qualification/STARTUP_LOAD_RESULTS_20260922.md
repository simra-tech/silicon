# Coordinated reference startup and load controls — simulated

Source `586ffb58b6af31c77a2e7cbcb83b173ffa4713ec62401da30901c5a7e606283b`
retains the fixed loop24/Qref4/R2 candidate and lengthens only XM31/XM33
from0.5 to0.6 µm. These are development controls, not source adoption.
Runtime: pinned ngspice46, image config
`ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2`, IHP PDK
`84374023ee8b4b126bebbba67fcbada0a9c0ff0b`; complete model/init hashes are
in the linked manifests. No model cards or rule decks changed.

| Check | Status | Result and scope |
|---|---|---|
| Original1 ms ramp,3 V/27 C | passed | Full3 ms endpoint; see prior short-HV control |
| Original100 ms ramp, derivative | failed | Solver stopped39.2694945 ms atQ76_u24; exit0 did not qualify completion |
| Same original100 ms deck, parent535 | failed | Stopped39.2693836 ms atsame device; failure predates HV length change |
| Derivative100 ms ramp, explicit20 µs maxstep | passed | 15,036 finite rows through300 ms; numerical, endpoint-level and HBT VCE screens |
| Same100 nA load fixture, baseline and derivative | passed | Both full40 µs; finite data and prospective return bands |
| Timestep convergence, full terminal/reliability bounds | not run | A single refined timestep and limited load outputs do not establish these |
| New geometry PEX, broad MC, actual periodic loads | not run | Standalone fixtures retain original wiring C-PEX |
| Random population for startup/load controls | not applicable | Mismatch disabled; no yield claim |

## Slow-ramp numerical diagnostic

The only deck change was `tran 0.0002 0.30000000000000004 0 20u uic`;
all source/init/stimulus/tolerances remained exact. Runtime97.886 s, bounded300 s.
Main/terminal saved grids matched exactly and increased strictly. First sample
is2 µs: the initial[0,2 µs) interval remains unobserved, not interpolated to0.
Endpoint VREF1.04545767786 V, IPTAT4.13410269 µA, sampled supply peak319.5666 µA.
No numerical errors or warning lines were observed in this particular run.
All mapped HBT sampled external VCE values met the separate1.6 V screen.
This does not bound continuous peaks or establish full hot/HV reliability.

[Prospective contract](STARTUP_STEP_DIAGNOSTIC_20260922.md),
[runner](run_startup_step_diagnostic.py), and
[complete manifest](runs/bgr_hv06_startup100ms_maxstep20us_20260922_r1/manifest.json)
retain exact source/deck/runtime hashes, terminal extrema and waveform hashes.
Reproduce with `flow/run.sh python3 designs/g1-guardian/blocks/g1_bgr/sim/qualification/run_startup_step_diagnostic.py`
in a workspace without that result directory; the runner refuses overwrite.

## Matched100 nA VREF load

The original deck was copied byte-for-byte to both fresh runs:
SHA256 `3ca490362a50e621969a70d53922c757fde93f334d0a46393846403fe60aade2`.
At27 C/3.3 V, VREF load ramps0→100 nA at5–5.01 µs and returns at20–20.01 µs.
IPTAT is held at1 V; VREF has1 pF. Neither is actual downstream loading.

| Simulated observation | Baseline72417e07 | Derivative586ffb58 |
|---|---:|---:|
| Runtime, s | 11.725 | 119.621 |
| Saved rows | 20,020 | 20,020 |
| Pre-load VREF, V | 1.03931048236 | 1.04546021858 |
| Loaded VREF, V | 1.03052454728 | 1.04322802783 |
| Finite100 nA step response, V/A | −87,859.35 | −22,321.91 |
| Final5 µs max VREF return error, nV | 0.0497 | 0.3363 |
| Sampled supply-current peak, µA | 22.0377 | 319.6936 |

Both meet the prospective1 mV VREF and0.1% IPTAT engineering return bands.
Those bands are not product allocations, and finite-step V/A is not AC impedance.
Both logs contain an initial temperature-limiter NaN warning, retained explicitly;
finite final waveforms are not a model-validity or device-reliability pass.
The baseline scalar results match the retained historical fixture, but a complete
archived waveform comparison was not performed and is **not run**.

[Contract](MATCHED_LOAD_CONTROL_20260922.md), [runner](run_matched_load_control.py),
[six focused checker tests](test_matched_load_control.py) and
[manifest](runs/bgr_matched_load_20260922_r1/manifest.json) provide reproduction
and exact hashes. All six tests passed. Execute the runner through `flow/run.sh`
in a fresh workspace; it refuses existing results and stops on the first failed
leaf. No startup/load sweep expansion or retry is implicit in these results.

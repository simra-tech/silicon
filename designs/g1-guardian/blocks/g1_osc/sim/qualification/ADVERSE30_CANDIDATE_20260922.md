# OSC R0.95 candidate: 30-sample adverse endpoint screen

All simulated slow/hot endpoint runs complete:30 independent samples per geometry,
codes0/15,120 transients total. The baseline has16/30 failures to bracket10MHz;
the separate R0.95 candidate has0/30. The new62021–62030 extension contributes
7/10 baseline failures and0/10 candidate failures, with40/40 numerical passes,
no timeouts and all269 realized parameters fixed before/after and across codes.

`analyze_adverse30.py` rechecks exact source/model/runtime identity within each
variant, source/deck/waveform hashes and per-sample fingerprint invariance.
`adverse30_comparison_20260922_r1.json` retains every result, including failures.
Equal seeds across changed resistor geometry are not paired physical samples.
The new extension uses139MiB and approximately897.47 cumulative solver-seconds.

This is ss/wcs/wcs,1.08V,125°C and an ideal50fF load. Endpoint bracketing is
not full-code monotonicity, a post-trim error bound or measured silicon yield.
The candidate changes four charging resistors from58.5µm to55.575µm while
retaining old extracted wire capacitances; it remains **unadopted**.

Remaining gates include candidate nominal100 endpoint samples, independent20
all-code samples, expanded adverse coverage, actual-receiver startup/re-enable
and load checks, physical geometry DRC/LVS/new extraction, requalification of
the extracted candidate and its integrated power/clock behavior. These checks
are **not run** to completion for the adopted-source candidate because no
candidate has been adopted. Baseline nominal100 and independent20 all-code
results cannot be substituted for candidate coverage.

## Prospective expansion protocol

After separate nominal-tuple qualification `osc_r095_nominal_qualify_20260922_r1`
passes all9 cases and full269-parameter/repeat-waveform checks, use fixed seeds
63101–63200 for the candidate100-sample codes0/15 screen. Use disjoint seeds
63301–63320 for the independent all16-code campaign. Neither set overlaps the
63001/63002 qualification seeds or62001–62030 adverse set. No post-outcome
seed selection or calibration fitting is performed.

The nominal100 run prefix is `osc_r095_nom100_20260922_r1`, up to4 single-thread
workers and300s per leaf, with a fresh1GiB resource reservation. All-code data
are split into two10-sample batches to remain below1GiB per batch. Source/netlist,
runtime, model and all realized device parameters are audited against the
nominal qualification using `audit_candidate_batch.py`. Numeric failures,
electrical bracket failures, monotonicity and missing cases remain distinct.
These simulation-only fixed-source runs do not bypass the separate via/current,
route, stock-check and geometry-freeze gates before broader affected-layout PEX.

The nominal100 endpoint campaign now completes200/200 transients with100 distinct
full fingerprints and0 bracket failures. `r095_nominal100_audit_20260922_r2.json`
records the final source/model/runtime/deck/wave audit and explicitly marks
all-code monotonicity **not run** for these endpoint-only samples. R1 is retained;
R2 adds explicit evaluated/not-run monotonicity counts without changing results.
Output occupies691MiB. Independent all16-code samples remain a separate campaign.

Three R0.95 actual-receiver regressions also pass numerical/function checks:
nominal code8 at9.435520MHz; slow/cold code15 disable/re-enable with all19 observed
clock points quiet while disabled and5.892208→5.892625MHz before/after; fast/cold
with1µs enable ramp at12.238517MHz. Each retains the original estimated assemblyRC,
internal SPEF and100fF assumed leaf loads. These do not establish whole-tree
loading, a pulse-width budget or physical jitter.

The candidate1000fF sensitivity `osc_r095_receiver1000_20260922_r1` now passes
6us numerical/function checks, all19 observed nodes with36 rising edges in
the steady window,9.4356467MHz,40.87solver-seconds. This is an assumed leaf
capacitor sensitivity, not actual whole-tree downstream loading.

The remaining48 selected PVT leaves now complete. `audit_r095_pvt.py` and
`r095_pvt80_audit_20260922_r1.json` join their exact-source results with the
retained32 nominal/slowhot leaves:80/80 finite6us transients, five tuples
all strictly decreasing across16codes and all bracketing10MHz. Nearest-code
errors are−0.9950%,+0.3653%,−0.5843%,+0.2520%,−1.3809% for nominal,
slowcold,slowhot,fastcold,fasthot respectively. These are descriptive without
an invented trim-error allocation; five tuples are not full Cartesian PVT.

Independent all-code batch1 seeds63301–63310 also completes160/160 numerical
leaves,10 unique full fingerprints,0 bracket and0 monotonicity failures.
`r095_all16_b1_audit_20260922_r1.json` retains the exact qualification/source/
model/deck/wave audit.

Both independent all-code batches now complete:20/20 samples,320/320 leaves,
20 unique full269-parameter fingerprints, zero numerical/timeouts, zero
bracket failures and zero monotonicity failures. The combined
`r095_all16_20_audit_20260922_r1.json` audits both finished manifests against
the same nominal qualification, source/models/runtime/decks/waveforms.
All-code frequencies span7.36702–13.76848MHz; maximum absolute nearest-code
error is1.58013%, descriptive without a new trim-error budget. The campaign
uses7226.59 cumulative solver-seconds (~22.58s/leaf), about1.1GiB across two
separately gated batches, and roughly43min wall time at3then4workers.

Completed candidate gates are nominal100 endpoints, independent20all-code,
adverse30 endpoints, five selected all-code PVT tuples and the four retained
actual-receiver regressions. Physical candidate layout/stockchecks/newPEX,
requalification of that extracted source and integrated power/clock behavior
remain **not run** to completion. Existing source/geometry is not adopted or
silently replaced by these simulation-only passes. Original baseline failures
and all prior numerical failures remain retained.

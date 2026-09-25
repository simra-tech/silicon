# Extracted OSC trim screen, 2026-09-21

> **Update 2026-09-25.** R0.95 (four 55.575 µm segments) **is adopted**: it is the oscillator in the
> chip of record `g1_chip_top_1414.gds` (`629d303a…`, owner decision 2026-09-24). Statements below
> that call R0.95 "unadopted" or "not adopted" describe the state on their dates. The on-chip
> variant and its evidence are summarised in `../../README.md` "Variant on the chip of record".
> The 10.445340 MHz slow/hot code-0 value below is from the pre-CPEX R0.95 source `f08bf051` at
> ss/wcs/wcs, 1.08 V, 125 °C; the R0.95 CPEX gives 10.447 MHz
> (`fulltree_r095_load_20260924/results/slowhot_code0.json`). The −2 % candidate was not adopted.

All results are **simulated** on the existing capacitance-only PEX, with a
50 fF output stand-in. Circuit/layout/model cards were not modified.

| MOS / R / C | VDD / temperature | Frequency range, codes 15..0 (MHz) | 10 MHz bracket | Nearest code / frequency (MHz) |
|---|---|---|---|---|
| tt / typ / typ | 1.20 V / 27 °C | 7.174229–12.926776 | passed | 5 / 10.179087 |
| ss / wcs / wcs | 1.08 V / −40 °C | 5.617356–10.073457 | passed | 0 / 10.073457 |
| ss / wcs / wcs | 1.08 V / 125 °C | 5.560405–9.974814 | **failed** | 0 / 9.974814 |
| ff / bcs / bcs | 1.32 V / −40 °C | 9.303165–16.776615 | passed | 12 / 10.140284 |
| ff / bcs / bcs | 1.32 V / 125 °C | 9.153871–16.454378 | passed | 12 / 9.970945 |

All **80/80** transients completed through 6 µs with finite saved vectors and
required measurements, no solver failures/timeouts. All five frequency-versus-code
sequences decrease monotonically. Across the selected tuples/codes, duty is
49.134–49.752%; minimum measured high/low widths are 29.429/30.178 ns.
These bounds concern the screened cases and stand-in load, not an exhaustive
PVT/mismatch bound for the final chip receiver.

The slow/hot maximum misses exact 10 MHz by 0.252%. The bracket check means
that 10 MHz lies between minimum and maximum available code frequencies;
it does not guarantee a code exactly equals 10 MHz. Nominal nearest code 5
has +1.791% error. Any allowed trim quantization/timing tolerance must be
stated by the system contract; it is not inferred from these results.
Default code 8 spans 6.963740–11.660697 MHz across these tuples, so an
assumed untrimmed lower bound of 8 MHz is not supported by this screen.

| Remaining check | Status |
|---|---|
| Full Cartesian process/temperature/rail coverage | not run |
| Bank/comparator/passive mismatch | qualified20-sample nominal endpoint smoke complete; expanded/adverse coverage incomplete |
| Real routed clock/receiver load | nominal pilot complete | Actual root buf16 plus16 buf8 and internal SPEF; assembly RC and leaf loads remain estimates. |
| Slow startup and disable/re-enable at adverse corners | not run in this campaign |
| Physical jitter/phase noise | not run |
| Wire R, MIM plate/fill coupling | not run; known extraction limitations |

## Reproduction and provenance

`runs/osc_pilot_20260921_01` first repeated the original 3.3 µs nominal
code-8 fixture: 8.994415 MHz, 49.535843% duty, matching the prior result.
The four `osc_trim80_shard[0-3]_20260921_01` directories then covered
mutually exclusive `(tuple_index*16+code) mod 4` partitions, using one
ngspice thread per process and a 300 s per-case watchdog. The longer 6 µs
endpoint allows 20 edges at the slowest codes. The inherited `rshunt=1e12`
fixture setting was retained; it was not increased to obtain convergence.

From the repository root, repeat each shard with a **new** run ID:

```sh
G1_WORKDIR=designs/g1-guardian/blocks/g1_osc/sim/qualification flow/run.sh python3 run_trim.py --run-id NEW_ID --image-id sha256:5fd78498e578c6e9ec10828c248ca3790fc88250ff6caf545521b29e448ea3c0 --suite trim --shards 4 --shard-index 0
```

Use shard indices 0 through 3. `--suite pilot` reproduces the short nominal
pilot. Each manifest records exact arguments, observed ngspice 46, PDK
`84374023ee8b4b126bebbba67fcbada0a9c0ff0b`, image ID, source/model/runner/deck
hashes, actual exits and watchdog outcomes. Runner source snapshots are retained.
`python3 designs/g1-guardian/blocks/g1_osc/sim/qualification/summarize.py`
requires all 80 unique attempts and writes `summary.json`/`summary.csv`.

## Isolated charging-resistor candidates

Two simulation-only candidates shorten all four extracted charging-resistor
segments XR53–XR56 from 58.5 µm to 57.33 µm (−2%) or 55.575 µm (−5%).
Widths, other devices, extracted capacitances, trim bank, 50 fF output load,
solver settings and duty measurement remain unchanged. Resistor intrinsic
model parasitics follow the changed geometry. Both candidates complete all
16 codes at nominal and the failed slow/hot tuple: **32/32 each**.

| Candidate | Nominal range (MHz) | Slow/hot range (MHz) | Slow/hot nearest code / frequency (MHz) | Maximum duty change (percentage points) |
|---|---|---|---|---|
| −2% charging length | 7.312657–13.167380 | 5.666493–10.158346 | 0 / 10.158346 | 0.0341 |
| −5% charging length | 7.530336–13.547017 | 5.834166–10.446105 | 1 / 9.941573 | 0.0413 |

Both simulated trim sequences remain monotonic and bracket 10 MHz in these
two tuples. Maximum supply current for the −5% candidate is 116.363 µA at
nominal and 88.132 µA at slow/hot. Its slow/hot upper reach has 4.46% margin;
the −2% candidate has only 1.58%, comparable to the existing estimate of
period uncertainty from omitted wire resistance. Neither candidate is adopted
in the design or layout. Regenerated PEX, physical checks, full process/rail
coverage, mismatch and actual receiver loading are **not run** for either.

`candidate_summary.json` and `candidate_comparison.csv` retain the comparisons;
`compare_candidates.py` verifies that exactly these four length lines changed.
Run directories `osc_r098_candidate_shard[0-1]_20260921_01` and
`osc_r095_candidate_shard[0-1]_20260921_01` retain original/variant netlists,
decks, manifests and vectors. Reproduce each with a new ID, `--suite trim
--tuples candidate --shards 2 --shard-index 0 --r-charge-scale 0.98` or
`0.95`, then shard index 1. Pilot code subsets remain independent evidence.

## Mismatch qualification and smoke screen, 2026-09-22

`osc_mc_qualification_20260922_01` passes all nine legacy-ngspice qualification
cases. Explicit mismatch flags cover80 physical MOS/resistor/CMIM instances;
all269 recorded parameters remain fixed across temperature, trim code and
transient analysis. Same-seed waveforms repeat byte for byte, disabled devices
are seed-invariant, and each device class varies with enabled seeds.

`osc_mc20_endpoints_20260922_01` completes40/40 transients for20 nominal samples
(seeds61001–61020), with no numerical failures or timeouts. All samples bracket
10MHz between codes0/15 and retain identical parameters across codes. This
endpoint smoke screen does not establish all-code mismatch monotonicity,
adverse-corner yield, receiver loading or physical jitter. The baseline
slow/hot reach failure above remains unchanged. Use `analyze_mc.py RUN_ID` to
reproduce the saved qualification/screen analysis.

The native-ngspice47 pilot passes its own nine qualification cases and matches
measured frequency/duty/current, but **fails** the predeclared strict
cross-runtime fingerprint gate. The separate four-ULP diagnostic also fails:
maximum51ULP, absolute difference7.08e−16. Both results are retained in
`native_runtime_comparison_20260922.json` and
`native_fingerprint_diagnostic_20260922.json`; this OSC campaign continues on
the legacy runtime. No global native-runtime qualification is claimed.

## Actual clock receiver pilot

`osc_actual_receiver_nominal_20260922_01` replaces the50fF stand-in with the
actual `sg13g2_buf_16` root and16 immediate `sg13g2_buf_8` receivers. Their
internal input/output SPEF networks are copied from the retained CTRL run.
The assembly link uses a459.7558Ω/60.3853fF pi sensitivity estimate: summed
whole-tree resistance is not an extracted driver-to-receiver path. Each leaf
output has an explicit assumed100fF load, and one15.4008aF external coupling
is clamped quiet. Further clock-tree stages and DFF loads are absent.

At nominal27°C/code8, the6µs run completes and all19 observed clock nodes
have34 rising edges in the2–5.8µs window. Simulated frequency is8.99456067MHz;
minimum high/low widths are54.9923/56.0684ns. These are characterization
results without a newly invented pulse-width acceptance budget. Supply
integration in `actual_receiver_current_20260922.json` gives0.168636mW
combined OSC and immediate clock-tree power. Sampled clock receiver current
peaks at20.517mA under ideal rails; this is not a worst-case current bound.
Adverse startup/re-enable and leaf-load sensitivity fixtures are queued
separately and remain not run until their manifests complete.

## Completed overnight campaigns, migration pause 2026-09-22

Nominal100 endpoint samples complete200/200 leaves with no10MHz bracket or
fingerprint failures. A separate20-sample all16-code campaign completes
320/320 leaves; all20 trim curves are strictly monotonic and bracket10MHz.
Slow/hot baseline20 completes40/40 leaves with **nine bracket failures**.
The isolated R0.95 candidate completes its separately qualified20-sample
slow/hot screen with zero bracket failures. `completed_mc_screens_20260922.json`
retains these populations separately; the candidate remains unadopted and
has no regenerated physical extraction.

Actual receiver slow/hot code0 completes at9.974853MHz baseline(still below
10MHz) and10.445340MHz for R0.95. Fast/cold with1µs enable ramp and nominal
1000fF leaf loads also complete. The slow/cold disable/re-enable run **fails**
ngspice's output-memory availability check, with solver exit1 and no acceptance
waveform. All three synthetic OSC rail perturbation leaves fail the same type
of output-memory check. They are retained failures, not timeouts or passed
jitter evidence. Targeted retries need new run IDs after resource/output
diagnosis. Owner paused simulations for migration; no OSC runner remains active.

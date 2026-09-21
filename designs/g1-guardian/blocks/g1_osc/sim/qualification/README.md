# Extracted OSC trim screen, 2026-09-21

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
| Bank/comparator/passive mismatch | not run |
| Real routed clock/receiver load | not run |
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

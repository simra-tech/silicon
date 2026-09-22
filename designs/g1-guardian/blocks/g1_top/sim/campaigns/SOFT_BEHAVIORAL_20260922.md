# Reduced-front soft-path regression

Three corrected-clock fixtures use actual RTL, GATE C-PEX, a behavioral
BGR/SENSE/TRIP front end, ideal8.994MHz oscillator, fitted output pads and
a modeled external switch. These are logic/transition checks; full analog
threshold accuracy, mismatch, real-FET current decay and assembled RC remain
separate.

All three corrected runs `*_20260921T222432Z_8d606f1b` complete and pass
saved-waveform/state criteria in `soft_behavioral_20260921T222432Z/summary.json`:

| Case | Saved behavior | Status |
|---|---|---|
| `a_s` | 1.5A for2.5µs; gate remains armed, no trip/cause, peak<256cycles | passed |
| `b_s` | Held1.5A; configured256cycle soft window; soft cause1, peak1, gate below1V after29.32µs | passed |
| `d_s` | Five1.4A bursts,2.5µs on/off; no trip/cause, load follows requested profile | passed |

Each case verifies prior arming, soft153/hard254, inactive hard comparator,
exercised soft comparator, full endpoint and clean solver log. The held-soft
latency includes settling/synchronization/pad discharge and is checked against
the declared256cycle window with12cycle overhead allowance. This is a soft
window test, not the separate hard-trip<10µs criterion.

The preceding runs `*_20260921T222155Z_72aa3f3b` retain analog waveforms but
no-trip cases attempted measurements of nonexistent trip crossings, emitting
postprocessing errors. The generator now omits those measurements for
explicit no-trip fixtures and saves soft-peak bits. Original logs remain
unchanged. The checker identifies the active case within a multi-case
manifest instead of confusing the requested case list with one fixture.

Command:

```sh
G1_CPUS=1 G1_MEMORY=2g G1_WORKDIR=designs/g1-guardian/blocks/g1_top/sim \
 flow/run.sh python3 run_top.py a_s b_s d_s --netlist pex --front beh \
 --outpads beh --threads 1 --timeout 180 \
 --image-id sha256:5fd78498e578c6e9ec10828c248ca3790fc88250ff6caf545521b29e448ea3c0
```

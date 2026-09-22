# Reduced-front transition and serial regression

Six fixtures `*_20260921T225115Z_e2f0b588` completed and passed saved-waveform
acceptance. They use actual RTL, GATE block C-PEX, behavioral BGR/SENSE/TRIP,
an ideal8.994MHz clock, fitted output pads and a modeled external switch.
This is scoped logic/transition evidence; analog accuracy, real-FET discharge,
physical output pads, mismatch and assembled RC are not qualified.

| Fixture | Observed simulated behavior | Status |
|---|---|---|
| `q` | Nominal1A through44µs, armed without trip | passed |
| `c_fast` | FAST_EN written1; GATE below1V at0.42µs after3A fault; both latches and hard cause | passed |
| `f_mid` | In-range1.8A/45mV hard fault, load returns, EN low40–42µs clears both latches, nominal current resumes | passed |
| `hard_pulse` | In-range45mV pulse200ns exercises comparator but does not satisfy four-decision hard filter | passed |
| `inrush_pulse` |45mV pulse30–35µs occurs under512cycle mask; no trip, mask releases before68µs endpoint | passed |
| `clear_read` | Serial STATUS=0x85, TRIP_CNT=1; CLEAR then STATUS=0x80, TRIP_CNT remains1 and GATE re-arms | passed |

The FAST_EN fixture is an above-range fault-stress profile, not an input
accuracy test. CLEAR retains threshold configuration and does not restart
the inrush mask; the separate EN-reset fixture restores reset codes. Serial
readback is decoded from complete pad-side clock/data and SDO waveforms,
including turnaround and response bytes, rather than inferred from probes.
No analog pad delay is modeled on these serial inputs/SDO.

Acceptance artifacts are the `*_r2.json` files and `summary.json` in
[`transitions_behavioral_20260921T225115Z_e2f0b588`](transitions_behavioral_20260921T225115Z_e2f0b588).
Full analog and state text is preserved as deterministic gzip files under
`../results/waves/*_analog_full.txt.gz` and `*_state_full.txt.gz`; acceptance
hashes refer to decompressed content. The checker can use these if the build
directory is unavailable. Earlier assessments without state hashes remain
historical; r2 adds that provenance without changing the tests.

The preceding six runs `*_20260921T224813Z_17d3fd01` reached analog endpoints
but failed state export because SDO was missing from the explicit save list.
They remain failed acceptance evidence. The save list was corrected, and the
fresh runs have byte-identical analog waveforms. The generator now rejects
export requests for unsaved voltage/current vectors before launching ngspice.

Command:

```sh
G1_CPUS=1 G1_MEMORY=2g G1_WORKDIR=designs/g1-guardian/blocks/g1_top/sim \
 flow/run.sh python3 run_top.py q c_fast f_mid hard_pulse inrush_pulse clear_read \
 --netlist pex --front beh --outpads beh --threads 1 --timeout 180 \
 --image-id sha256:5fd78498e578c6e9ec10828c248ca3790fc88250ff6caf545521b29e448ea3c0
```

The full retry/give-up and serial counter fixture subsequently passed; see
[retry recovery](RETRY_RECOVERY_20260922.md). Phase/threshold sweeps, adverse
rails and transistor-level front-end anchors remain incomplete.

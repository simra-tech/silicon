# Bounded restart diagnostics — 21 September 2026

These are **simulated startup diagnostics**, not a completed hard-trip or tape-out
verification. No device models, rule decks, extracted capacitances, circuit RTL,
clock slew or load stimulus were changed. The runner now preserves live output,
limits wall time and uses measurements valid inside short prefixes. Historical
run tags, decks and logs are preserved.

## Built against

| Item | Version / establishment |
| --- | --- |
| PDK | IHP SG13G2 `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`; container COMMIT file recorded in each circuit log |
| ngspice | 46; `ngspice -v`, log/manifest |
| Icarus | 14.0 development; `iverilog -V`, log/manifest |
| EDA image | `sha256:5fd78498e578c6e9ec10828c248ca3790fc88250ff6caf545521b29e448ea3c0`, linux/amd64; host `docker image inspect`, recorded in PEX/forced-timeout manifests |
| Execution | Existing `flow/run.sh` amd64 container on ARM host; no CPU scaling claim |
| Extraction | Existing block CC netlists; kpex 0.3.12 provenance in block records; extraction not rerun |
| New physical DRC/LVS | not run; no design geometry/circuit modification |

The first schematic OP and 0.2 µs runs preceded the image-ID manifest field;
their log tool/PDK banners and input hashes are present, but an immutable image
ID was not captured in those per-run manifests. Each new manifest records the
runner/helper/deck version hashes actually used: observability code evolved
during this sequence. `options` and `effective` distinguish requested defaults
from resolved settings. Full waveform files are under `build/g1_top/`; copied
selected-vector evidence is in `results/waves/`.

## Results

All c-case circuit diagnostics use tt, 27 °C, nominal supplies, corrected clock
receiver, ideal clock, fitted output pads, transistor-level analog front end,
trap integration and 5 ns maximum timestep. The PEX ideal clock is 8.994 MHz;
the schematic clock is 9.919 MHz. The analog operating point precedes RTL
configuration and EN. Prefix runs restart from zero; they are not checkpoints.

| Diagnostic | Status | Wall seconds | Circuit equations | Transient accepted / rejected points | Transient iterations |
| --- | --- | ---: | ---: | ---: | ---: |
| Schematic OP | passed: one OP row, finite node values, exit 0 | 15 | 17486 | not applicable | 0 |
| Schematic 0–0.2 µs | passed: reached 0.2 µs, saved waveform, exit 0 | 20 | 17486 | 160 / 40 | 627 |
| PEX OP | passed: one OP row, finite node values, exit 0 | 25 | 21112 | not applicable | 0 |
| PEX 0–1 µs | passed: reached 1 µs, saved waveform, exit 0 | 50 | 21112 | 565 / 67 | 1600 |
| PEX 0–4 µs | passed: reached 4 µs, saved waveform, exit 0 | 135 | 21112 | 2429 / 339 | 7220 |
| PEX 0–10 µs request | not run to completion: watchdog at 300 s; last reported 7.55122 µs | 300 | not reported at interruption | not reported at interruption | not reported at interruption |
| Forced 1-second ngspice interruption | watchdog passed; circuit not run to completion | 1.013 | not established | not applicable | not established |
| Corrected isolated bridge | passed: 4.959501 MHz from 9.919 MHz | under 60-second bound | not applicable | not applicable | not applicable |
| Historical band isolated bridge | failed clock behavior, reproduced intentionally as regression | under 60-second bound | not applicable | not applicable | not applicable |
| New full q/c functional event runs, integrated power-up, hot/process corners | not run in this restart | not applicable | not applicable | not applicable | not applicable |

Wall times include up to five seconds of completion-poll overhead; ngspice's
own elapsed times are retained. OP matrix factor time was 1.26661 s schematic
and 7.97149 s PEX. The 4 µs PEX log reports 131.501 s simulator elapsed, 60.6997 s
matrix load, 53.8902 s factor and 5.8524 s solve; these are simulator-reported
statistics, not an independently profiled scaling model. Linux progress
snapshots show about 200 MiB RSS and nine threads during PEX activity. ngspice
also reports a much larger virtual program size; do not label that physical RAM.

Schematic OP: VREF 1.037848 V, ISENSE 0.997131 V, GATE approximately 0 V.
PEX OP: VREF 1.039303 V, ISENSE 0.998437 V, GATE approximately 0 V. At the end
of the 4 µs PEX prefix, after EN: VREF 1.039244 V, ISENSE 1.498102 V, GATE
3.200007 V. These observations characterize startup/arming only. Serial
configuration around 18–21 µs and the hard-trip load step at 30 µs were **not
reached**, and the default inrush mask is still active in these prefixes.

The further 10 µs PEX prefix reached a reported 7.55122 µs when the 300-second
watchdog stopped it (ngspice returncode −15; wrapper 124). Progress remained
advancing in the final snapshots. No final waveform, final accepted/rejected
step totals, or functional verdict exists for this interrupted prefix. It did
not reach SPI configuration or the load event. The existing completed 4 µs
waveform remains the furthest saved prefix in this restart.

All completed circuit diagnostics retained warnings: non-increasing SCLK PWL
points; temperature-limiting NaN during initialization; resistor-model voltage
limit warnings during convergence; dynamic gmin recovery. They subsequently
returned valid OP/transient data, but warning-free verification is not claimed.
The SCLK generator appends equal-time, equal-voltage points at edge starts;
those points were not edited in this experiment. Prefix waveform vectors are finite.
The 4 µs file has repeated printed timestamps near EN (3.04840872 µs) at
ngspice's default text precision; they are not evidence of reversed solver time.
Subsequent diagnostic decks request 15-digit text output.

The forced-timeout log contains simulator output written before termination,
manifest `status=timeout`, actual ngspice `returncode=-15`, and diagnostic
acceptance `not run to completion`. The wrapper exits 124 separately. This
checks that a watchdog event cannot be confused with a completed circuit test.
Three process-level watchdog tests also passed: timeout output retention,
nonzero-exit classification, and successful output/progress plus overwrite
rejection. See `test_run_bounded.py` and `logs/watchdog_tests_20260921.txt`.

## Exact circuit commands and evidence tags

Run from repository root. These commands are the executed commands; repeating
an already-existing ID is intentionally refused. Choose a new ID for a rerun.

```
G1_WORKDIR=designs/g1-guardian/blocks/g1_top/sim flow/run.sh python3 run_top.py c --analysis op --timeout 300 --run-id s0_20260921_op1
G1_WORKDIR=designs/g1-guardian/blocks/g1_top/sim flow/run.sh python3 run_top.py c --analysis prefix --tstop 0.2 --timeout 300 --run-id s1_20260921_smoke1
G1_WORKDIR=designs/g1-guardian/blocks/g1_top/sim flow/run.sh python3 run_top.py c --netlist pex --analysis op --timeout 300 --run-id s2_20260921_pexop1 --image-id sha256:5fd78498e578c6e9ec10828c248ca3790fc88250ff6caf545521b29e448ea3c0
G1_WORKDIR=designs/g1-guardian/blocks/g1_top/sim flow/run.sh python3 run_top.py c --netlist pex --analysis prefix --tstop 1 --timeout 300 --run-id s2_20260921_pex1us --image-id sha256:5fd78498e578c6e9ec10828c248ca3790fc88250ff6caf545521b29e448ea3c0
G1_WORKDIR=designs/g1-guardian/blocks/g1_top/sim flow/run.sh python3 run_top.py c --netlist pex --analysis prefix --tstop 4 --timeout 300 --run-id s2_20260921_pex4us --image-id sha256:5fd78498e578c6e9ec10828c248ca3790fc88250ff6caf545521b29e448ea3c0
G1_WORKDIR=designs/g1-guardian/blocks/g1_top/sim flow/run.sh python3 run_top.py c --netlist pex --analysis prefix --tstop 10 --timeout 300 --run-id s2_20260921_pex10us --image-id sha256:5fd78498e578c6e9ec10828c248ca3790fc88250ff6caf545521b29e448ea3c0
G1_WORKDIR=designs/g1-guardian/blocks/g1_top/sim flow/run.sh python3 run_top.py c --analysis op --timeout 1 --run-id s0_20260921_ngtimeout --image-id sha256:5fd78498e578c6e9ec10828c248ca3790fc88250ff6caf545521b29e448ea3c0
```

Each tag below identifies `logs/<tag>.log`, `.json`, `.progress.jsonl` and
`decks/<tag>.cir` under `designs/g1-guardian/blocks/g1_top/sim/`:

- `c_sch_tl_tt_27C_clockfix_op_s0_20260921_op1`
- `c_sch_tl_tt_27C_clockfix_t0.2_prefix_s1_20260921_smoke1`
- `c_pex_tl_tt_27C_clockfix_op_s2_20260921_pexop1`
- `c_pex_tl_tt_27C_clockfix_t1_prefix_s2_20260921_pex1us`
- `c_pex_tl_tt_27C_clockfix_t4_prefix_s2_20260921_pex4us`
- `c_sch_tl_tt_27C_clockfix_op_s0_20260921_ngtimeout`
- `c_pex_tl_tt_27C_clockfix_t10_prefix_s2_20260921_pex10us`

Bridge sources are `bridge_probe/divider.v`, `threshold.cir`, `band.cir`.
Fresh deck/log/manifest evidence is in `build/g1_top/bridge_s1_20260921/`;
only the compiled divider path changed to that new directory. Commands inside
the existing flow container: `iverilog -o /work/build/g1_top/bridge_s1_20260921/divider.vvp designs/g1-guardian/blocks/g1_top/sim/bridge_probe/divider.v`, then
`ngspice -b /work/build/g1_top/bridge_s1_20260921/threshold.cir` and the corresponding
`band.cir`, each through the bounded helper with a 60-second limit. Existing
bridge logs were not overwritten. No PDK device model is used in that probe.

## Final runner fixture verification

The final runner version postdates the circuit runs above. Its additional
launch-failure handling and saved-waveform acceptance checks were verified with
fixtures only; no circuit simulations were rerun for these changes. Historical
run manifests retain their original runner and helper hashes. Previously saved
completed prefix waveforms were separately reviewed for finite vectors and
reached endpoints; the new automatic checks are not retroactively attributed
to those executions.

Six fixture tests passed: the three watchdog tests above, terminal manifest
creation for launch failure without a child return code, a required finite saved
waveform, and rejection of nonfinite or truncated waveform data. Command:
`python3 -m unittest discover -s designs/g1-guardian/blocks/g1_top/sim -p test_run_bounded.py -v`.
Evidence: `logs/runner_fixtures_final_20260921.txt`.

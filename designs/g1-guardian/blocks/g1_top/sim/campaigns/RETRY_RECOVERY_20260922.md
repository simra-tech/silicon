# Full retry/readback recovery

The corrected-clock `retry_read` fixture **passed** all14 saved-waveform checks
in [retry_read_server_20260922_r1.json](retry_read_server_20260922_r1.json).
The full1.14ms endpoint completed; the earlier900s timeout is preserved.

This is simulated actual RTL plus GATE C-PEX, with behavioral BGR/SENSE/TRIP,
ideal8.994MHz clock, fitted output pads and a modeled external cutoff switch.
It does not establish analog threshold accuracy, real-FET current decay,
power-order safety, full assembled RC, or physical measurement.

The45mV-equivalent held fault starts at40µs. Saved digital trip rises at
41.129066µs, releases at952.067771µs for the single programmed retry, and
reasserts at953.513176µs. The simulated hold interval is910.938705µs,
consistent with the declared8192-cycle hold plus synchronization allowance.
The gate and modeled load actually re-enable between trips, then remain off.

Serial readback passes: STATUS=0xA5, STATUS2=0x18, TRIP_CNT low=2/high=0.
Both trip latencies are below10µs in this fixture. The original frozen checker
also verifies prior arming, final latching/current, requested fault, complete
state waveform and clean simulator log. Its generic limitation sentence about
separate readback qualification does not negate the explicit readback test;
other serial registers and timing/CDC coverage remain separate.

```sh
G1_CPUSET=8 G1_CPUS=1 G1_MEMORY=3g \
 G1_WORKDIR=designs/g1-guardian/blocks/g1_top/sim \
 flow/run.sh python3 run_top.py retry_read --netlist pex --front beh \
 --outpads beh --threads 1 --timeout 1200 --run-id server_retry_20260922_r1 \
 --image-id sha256:5fd78498e578c6e9ec10828c248ca3790fc88250ff6caf545521b29e448ea3c0

python3 designs/g1-guardian/blocks/g1_top/sim/check_campaign.py \
 retry_read_pex_beh_tt_27C_clockfix_threads1_functional_server_retry_20260922_r1 \
 --output designs/g1-guardian/blocks/g1_top/sim/campaigns/retry_read_server_20260922_r1.json
```

Exact deck, models, RTL, init, image/PDK/tool identities and timings are in the
run manifest under `../logs/`. Reruns require fresh IDs/output filenames.
`test_retry_acceptance.py` adds negative controls for missing load re-enable,
wrong hold interval, extra retry, wrong counter and ambiguous serial output.
All28 root harness tests passed after this addition. Physical measurements
are **not run**; a physical-test result is **not applicable** to this digital/
mixed-signal simulated fixture. Full integrated plan completion is **not run**.

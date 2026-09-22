# Server integration verification — 22 September 2026

All numbers below are simulated. Pinned ngspice 46 and IHP PDK
`84374023ee8b4b126bebbba67fcbada0a9c0ff0b` were used. Runtime and source hashes
are preserved in the linked run manifests; an archive transfer is not circuit
qualification.

| Check | Status | Evidence and scope |
| --- | --- | --- |
| Full-length hard fault, actual analog block C-PEX and RTL | passed | `stream_20260922t131258z_4a11d67b/electrical_acceptance.json`: all 14 checks; 42 µs endpoint, simulated gate-off delay 1.4127686 µs; elapsed launch time 3446.776 s. |
| Compact versus full-length settled pre-fault states | passed | `preamble_comparison_server_20260922_r1.json`: same models, RTL and image; identical declared digital states; largest analog mean difference 32.8135 µV against the prospectively declared 1 mV limit. |
| Earlier full-length attempt | failed | Original 3600 s watchdog stopped before the 42 µs endpoint. Retained, not replaced by the fresh successful run. |
| Retry / give-up, behavioral front with actual RTL and GATE C-PEX | passed | `RETRY_RECOVERY_20260922.md`: full 1140 µs, all 14 checks and serial readback. |
| Eight-phase sustained-hard-fault sweep | passed | All eight 42 µs cases meet the frozen electrical checks. |
| Eight-phase short-pulse sweep, complete acceptance | failed | Six passed; shifts 55.593 and 83.389 ns failed only `hard_comparator_exercised`. All eight completed and passed no-trip, load tracking, no-cause and configuration checks. A pulse missed by the sampled comparator does not demonstrate persistence-filter rejection. |
| Distinct 400 ns pulse, eight phases | passed | `pulse400_pilot_acceptance_20260922_r1.json` plus `pulse400_phase_20260922t144110z_eef4c4dc/summary.json`: all eight completed and exercised the comparator without a trip; 400 ns width independently checked. This is additional coverage, not a replacement for the original 200 ns results. |
| Actual-analog soft-fault endpoint | passed | `soft_analog_server_20260922_acceptance.json`: all 17 checks; complete 64 µs waveform, simulated gate-low delay 29.32 µs after the 30 µs fault; launch elapsed 5256.077 s under the declared 5400 s watchdog. Actual analog block C-PEX and RTL, with ideal oscillator, fitted output pads and modeled switch. |
| Full SEU history equivalence, real-FET behavior, full assembled RC and analog PVT/MC qualification | not run | These are not established by the above anchors. |
| Physical measurement for this simulation-only comparison | not applicable | No measured silicon result is claimed. |

Phase coverage is the union of two corrected 111.185 ns pilot assessments,
`phase_20260922t134404z_9ba71163` (six cases), and
`phase_20260922t140347z_7352e87b` (eight cases). The declared shifts are
0, 27.796, 55.593, 83.389, 111.185, 138.981, 166.778 and 194.574 ns.
The two initial pilot attempts failed endpoint acceptance because shifting the
end time exposed output-grid rounding; both failures remain archived. The
corrected fixture shifts only the event, keeping the original integer-grid end
time. It does not change the acceptance thresholds.

The phase fixtures use a behavioral front end, ideal oscillator, fitted pads
and modeled external switch. They establish only sampled functional behavior,
not comparator accuracy or arbitrary-phase proof. The full analog hard-fault
anchor also retains an ideal oscillator, fitted pads and modeled switch.

Reproduce the new baseline checks from the repository root:

```sh
python3 designs/g1-guardian/blocks/g1_top/sim/check_stream.py designs/g1-guardian/blocks/g1_top/sim/campaigns/stream_20260922t131258z_4a11d67b
python3 designs/g1-guardian/blocks/g1_top/sim/compare_preambles.py designs/g1-guardian/blocks/g1_top/sim/campaigns/stream_20260921T220244Z_879e85e2 designs/g1-guardian/blocks/g1_top/sim/campaigns/stream_20260922t131258z_4a11d67b --output FRESH_COMPARISON.json
```

The first checker intentionally refuses to overwrite existing acceptance
evidence; use a separate evidence copy for a replay.

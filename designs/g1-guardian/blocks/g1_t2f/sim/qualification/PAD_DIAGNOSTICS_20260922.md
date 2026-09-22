# TEMP_OUT stock-pad numerical localization

All results below are simulated numerical diagnostics using unchanged pinned
PDK cards and original tolerances. Original failed artifacts are retained.

| Fresh run | Status | Endpoint | Wall time |
|---|---|---|---|
| `t2f_output_pad_nominal10p_20260922_r1` | failed |1.59569µs of32µs |59.1355s |
| `t2f_pad_replay_20260922_r1` | failed |1.275603954µs |0.9960s |
| `t2f_core_route_control_20260922_r1` | passed numerical completion |32µs,27001 rows |80.3784s |

Both failures report timestep-too-small despite solver exit0. The original
reports `vmode#branch`; the reduction reports `vpad12#branch`. The pad-only
replay replaces the BGR/T2F core with an ideal PWL source from the retained
nominal25°C waveform, keeps the exact210.936Ω/23.4407fF route, stock IO cell and
10pF external load. All18569 PWL points are finite with strictly increasing
times; minimum step8.9905ps. It intentionally removes core output impedance and
feedback, so it is not an electrical pad-drive acceptance fixture.

The complementary control retains the original core and route while removing
the stock pad and external load. Its successful full endpoint, together with
pad-only failure, localizes this numerical problem to the pad path. The source
label on the timestep error is not proof of which device causes the failure.
The known GATE protected-pad diode discontinuity is a plausible related mechanism,
but this experiment does **not** prove an identical intrinsic branch crossing:
the recorded pad internal nodes at failure do not directly establish that crossing.
No tolerance/model-card ladder is justified by this result.

`run_pad_reduction.py --case replay-pad|core-route` records source hashes,
PWL validity, decks, solver exit, numerical errors, saved endpoint and a300s
watchdog in fresh run manifests. Actual-pad edge quality, current, recovery and
downstream electrical acceptance remain **not run**. No pad or design was adopted.

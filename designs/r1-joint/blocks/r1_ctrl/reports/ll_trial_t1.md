# LibreLane hardening trial `r1ctrl_ll_20261020_t1` (r1_ctrl revision 0.2)

Command (repository root):

```
G1_CPUSET=112-115 G1_CPUS=4 G1_WORKDIR=designs/r1-joint/blocks/r1_ctrl \
G1_RESULTS_ROOT=/opt/sim/<user>/r1-traces/sims flow/run.sh sh flow/librelane/run_trial.sh r1ctrl_ll_20261020_t1
```

- LibreLane 3.1.0.dev2, Classic flow, PDK commit `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`,
  `flow/librelane/config.yaml`, `flow/r1_ctrl.sdc` (clk 23.81 ns = 42 MHz).
- Start 2026-10-20 15:03 UTC, wall-clock limit 2 h (`timeout 7200`), 4 CPUs.
- Bulk run: `$G1_RESULTS_ROOT/r1_ctrl/r1ctrl_ll_20261020_t1/` (input hashes in `inputs.sha256`).
- RTL: revision 0.2 before two later changes: the `sc_pend` pair interlock and the `u_sa` removal
  in `r1_gate.v` (see the README run history). The trial netlist therefore still has `u_sa`.

## Result

**Not run to completion (time limit).** `timeout 7200` stopped the flow (exit 124) at
19:03 local time, in detailed routing (step 45, iteration 16, 17 DRC violations left). The
numbers below come from the steps that finished.

| Step | Metric | Value |
| --- | --- | --- |
| Synthesis (LibreLane Yosys) | cell area, instances | 181 746 µm², 12 906 |
| Floorplan | die, core area, utilisation | 521.11 × 539.83 µm = 0.281 mm², core 257 961 µm², 70.5 % |
| Detailed placement | instance area, utilisation | 192 602 µm², 74.7 % (1 489 timing-repair buffers) |
| CTS + post-CTS repair | instance area, utilisation | 212 963 µm², 82.6 % (413 clock buffers 15 014 µm², 1 856 repair buffers 15 185 µm²) |
| Mid-PnR STA after global routing (step 44), typical corner | setup WNS / TNS, hold WS | −3.33 ns / −52.0 ns, +0.19 ns |
| | setup violators | 17, all ending in the `u_gate.u_sa` shadow latch (strobe centre and valid), latch-to-latch paths timed over half a period; no flop-to-flop violator |
| Detailed routing (step 45) | DRC violations | 49 for iterations 11–14 (Metal2: 36 spacing, 12 short; Metal3: 1 short), 17 at iteration 15; stopped by the time limit |
| Sign-off STA at the 3 corners, DRC, LVS, antenna | — | not run (flow did not reach these steps) |

Disposition: the 42 MHz constraint fails only on the `u_sa` latch path, which revision 0.2
(run `r1ctrl_20261020_v02b`) removes. Routing at 82.6 % utilisation after CTS did not finish in 2 h; the next trial needs a lower
start utilisation (about 60 %) or fewer latch-word clock gates.

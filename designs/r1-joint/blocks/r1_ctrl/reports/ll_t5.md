# LibreLane run `r1ctrl_ll_20261020_t5` (r1_ctrl)

Command (repository root, `designs/r1-joint/blocks/r1_ctrl` as `G1_WORKDIR`, CPU set 112-115):

```
flow/run.sh sh flow/librelane/run_harden.sh r1ctrl_ll_20261020_t5 10800
```

- LibreLane 3.1.0.dev2, Classic flow, PDK commit `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`, container tapeoutbench-eda:latest sha256:ddeb69576f28
- Start 2026-10-20T19:39:36Z, end 2026-10-20T20:58:04Z, exit code 0 (timeout 10800 s)
- RTL: sha256 of the concatenated `rtl/*.v` copy in the run: `970c08bb59a9a2adc4a6a98a2861889fc5a97aaa12c0707ab8fc82ff0faa52ce`; register-file variant: variant <G1_RESULTS_ROOT>/r1_ctrl/.../r1_lib_flops_variant.v (R1_CFG_FLOPS)
- Bulk run: `<G1_RESULTS_ROOT>/r1_ctrl/r1ctrl_ll_20261020_t5/` (inputs in `inputs.sha256`); last step `76-misc-reportmanufacturability`

| Metric | Value |
| --- | --- |
| Die / core area (µm²) | 419687 / 390985 |
| Standard-cell area (µm²), utilisation | 236277, 0.604 |
| Sequential / clock buffers / timing-repair buffers (µm²) | 87387 / 6704 / 12764 |
| Sign-off STA nom_typ_1p20V_25C at 42 MHz: setup WS / TNS (ns), violators; hold WS (ns); max-slew violations | 0.000 / 0.00, 0; 0.186; 0 |
| Sign-off STA nom_fast_1p32V_m40C at 42 MHz: setup WS / TNS (ns), violators; hold WS (ns); max-slew violations | 0.000 / 0.00, 0; 0.106; 0 |
| Sign-off STA nom_slow_1p08V_125C at 42 MHz: setup WS / TNS (ns), violators; hold WS (ns); max-slew violations | 0.000 / 0.00, 0; 0.319; 2 |
| Detailed routing DRC errors (final) | 0 |
| Magic DRC / KLayout DRC errors | 0 / 0 |
| LVS errors (netgen) | 0 |
| Antenna violating nets | 0 |

Slow-corner setup violators in the sign-off report, by start-point type: none

Notes: this is the hardening run of record for revision 0.3. Its RTL copy differs from the tree
only by a comment in `rtl/r1_lib.v` (the comment that labelled the flip-flop form a "comparison
variant" was changed to "design of record"); its `config.yaml` equals the tree file apart from
comments (`R1_CFG_FLOPS` added). A setup WS of 0.000 is the clipped report value. At the slow
corner the smallest slacks are flop-to-PWM-shadow-latch paths that borrow ≤ 1.16 ns (counted as
met by STA); the worst other setup slack is +7.95 ns (run `r1ctrl_sta_ss_20261020`). The 2
max-slew violations are at the slow corner only. Utilisation was 55 % at the start; a denser
floorplan was not tried in this revision.

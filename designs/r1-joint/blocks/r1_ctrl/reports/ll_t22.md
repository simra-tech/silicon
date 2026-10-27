# LibreLane run `r1ctrl_ll_20261027_t22` (r1_ctrl)

Command (repository root, `designs/r1-joint/blocks/r1_ctrl` as `G1_WORKDIR`, CPU set 112-113):

```
flow/run.sh env R1_CFG_APPEND=flow/librelane/cfg_v08_t22.yaml sh flow/librelane/run_harden.sh r1ctrl_ll_20261027_t22 18000   (variable set inside the container command)
```

- LibreLane 3.1.0.dev2, Classic flow, PDK commit `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`, container tapeoutbench-eda:latest sha256:ddeb69576f28
- Start 2026-10-27T12:05:52Z, end 2026-10-27T14:25:43Z, exit code 0 (timeout 18000 s)
- RTL: sha256 of the concatenated `rtl/*.v` copy in the run: `0ad07872c6b916f290193d4ef0e77e13e9d7f70da334c9818239f4167fae5244`; register-file variant: flip-flops (`R1_CFG_FLOPS` in config.yaml)
- Bulk run: `<G1_RESULTS_ROOT>/r1_ctrl/r1ctrl_ll_20261027_t22/` (inputs in `inputs.sha256`); last step `77-misc-reportmanufacturability`

| Metric | Value |
| --- | --- |
| Die / core area (µm²) | 361228 / 333666 |
| Standard-cell area (µm²), utilisation | 266436, 0.799 |
| Sequential / clock buffers / timing-repair buffers (µm²) | 103169 / 7249 / 21640 |
| Sign-off STA nom_typ_1p20V_25C at 42 MHz: setup WS / TNS (ns), violators; hold WS (ns); max-slew violations | 0.000 / 0.00, 0; 0.205; 0 |
| Sign-off STA nom_fast_1p32V_m40C at 42 MHz: setup WS / TNS (ns), violators; hold WS (ns); max-slew violations | 0.000 / 0.00, 0; 0.120; 0 |
| Sign-off STA nom_slow_1p08V_125C at 42 MHz: setup WS / TNS (ns), violators; hold WS (ns); max-slew violations | 0.000 / 0.00, 0; 0.360; 0 |
| Detailed routing DRC errors (final) | 0 |
| Magic DRC / KLayout DRC errors | 0 / 0 |
| LVS errors (netgen) | 0 |
| Antenna violating nets | 0 |

Slow-corner setup violators in the sign-off report, by start-point type: none

# LibreLane run `r1ctrl_ll_20261028_t32` (r1_ctrl)

Command (repository root, `designs/r1-joint/blocks/r1_ctrl` as `G1_WORKDIR`, CPU set 112-115):

```
flow/run.sh env R1_CFG_APPEND=flow/librelane/cfg_v09_t32.yaml sh flow/librelane/run_harden.sh r1ctrl_ll_20261028_t32 18000
```

- LibreLane 3.1.0.dev2, Classic flow, PDK commit `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`, container tapeoutbench-eda:latest sha256:ddeb69576f28
- Start 2026-10-28T12:59:50Z, end 2026-10-28T16:26:22Z, exit code 0 (timeout 18000 s)
- RTL: sha256 of the concatenated `rtl/*.v` copy in the run: `f68edabeb4746bcadabad68116083c1791c6616be1a26bef2647bd73be47d2d8`; register-file variant: flip-flops (`R1_CFG_FLOPS` in config.yaml)
- Bulk run: `<G1_RESULTS_ROOT>/r1_ctrl/r1ctrl_ll_20261028_t32/` (inputs in `inputs.sha256`); last step `77-misc-reportmanufacturability`
- Configuration: `config.yaml` + `flow/librelane/cfg_v09_t32.yaml` (the t24 settings, which are the 0.8 record settings t22, plus `PL_TIMING_DRIVEN` true and `GRT_DESIGN_REPAIR_MAX_SLEW_PCT` 30). One uninterrupted LibreLane run, no hand repair: CTS kept all 75 clock-gate sinks and the disconnected-pins checker passed. The sign-off setup slack to flop D is in `<G1_RESULTS_ROOT>/r1_ctrl/r1ctrl_20261028_t32sta/` (slow +5.676 ns; the WS 0.000 below is the latch time borrowing). Revision 0.9 sign-off: README "Revision 0.9 sign-off".

| Metric | Value |
| --- | --- |
| Die / core area (µm²) | 361228 / 333666 |
| Standard-cell area (µm²), utilisation | 281533, 0.844 |
| Sequential / clock buffers / timing-repair buffers (µm²) | 112005 / 7630 / 20060 |
| Sign-off STA nom_typ_1p20V_25C at 42 MHz: setup WS / TNS (ns), violators; hold WS (ns); max-slew violations | 0.000 / 0.00, 0; 0.211; 0 |
| Sign-off STA nom_fast_1p32V_m40C at 42 MHz: setup WS / TNS (ns), violators; hold WS (ns); max-slew violations | 0.000 / 0.00, 0; 0.120; 0 |
| Sign-off STA nom_slow_1p08V_125C at 42 MHz: setup WS / TNS (ns), violators; hold WS (ns); max-slew violations | 0.000 / 0.00, 0; 0.369; 0 |
| Detailed routing DRC errors (final) | 0 |
| Magic DRC / KLayout DRC errors | 0 / 0 |
| LVS errors (netgen) | 0 |
| Antenna violating nets | 0 |

Slow-corner setup violators in the sign-off report, by start-point type: none

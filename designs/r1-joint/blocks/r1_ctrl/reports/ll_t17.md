# LibreLane run `r1ctrl_ll_20261027_t17` (r1_ctrl)

Command (repository root, `designs/r1-joint/blocks/r1_ctrl` as `G1_WORKDIR`, CPU set 114-115):

```
flow/run.sh env R1_CFG_APPEND=flow/librelane/cfg_v07_t17.yaml sh flow/librelane/run_harden.sh r1ctrl_ll_20261027_t17 12600
```

- LibreLane 3.1.0.dev2, Classic flow, PDK commit `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`, container tapeoutbench-eda:latest sha256:ddeb69576f28
- Start 2026-10-27T06:08:15Z, end 2026-10-27T09:32:31Z, exit code 0 (timeout 12600 s)
- RTL: sha256 of the concatenated `rtl/*.v` copy in the run: `cb0e2d35af6e0a307277812e651772e28cb92562c83ce9729dd4ff3af8822a6a`; register-file variant: flip-flops (`R1_CFG_FLOPS` in config.yaml)
- Bulk run: `<G1_RESULTS_ROOT>/r1_ctrl/r1ctrl_ll_20261027_t17/` (inputs in `inputs.sha256`); last step `77-misc-reportmanufacturability`

| Metric | Value |
| --- | --- |
| Die / core area (µm²) | 361228 / 333666 |
| Standard-cell area (µm²), utilisation | 283041, 0.848 |
| Sequential / clock buffers / timing-repair buffers (µm²) | 100004 / 6831 / 45182 |
| Sign-off STA nom_typ_1p20V_25C at 42 MHz: setup WS / TNS (ns), violators; hold WS (ns); max-slew violations | 0.000 / 0.00, 0; 0.323; 0 |
| Sign-off STA nom_fast_1p32V_m40C at 42 MHz: setup WS / TNS (ns), violators; hold WS (ns); max-slew violations | 0.000 / 0.00, 0; 0.195; 0 |
| Sign-off STA nom_slow_1p08V_125C at 42 MHz: setup WS / TNS (ns), violators; hold WS (ns); max-slew violations | 0.000 / 0.00, 0; 0.550; 0 |
| Detailed routing DRC errors (final) | 0 |
| Magic DRC / KLayout DRC errors | 0 / 0 |
| LVS errors (netgen) | 0 |
| Antenna violating nets | 0 |

Slow-corner setup violators in the sign-off report, by start-point type: none

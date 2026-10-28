# LibreLane run `r1ctrl_ll_20261028_t30` (r1_ctrl)

Command (repository root, `designs/r1-joint/blocks/r1_ctrl` as `G1_WORKDIR`, CPU set 112-115):

```
flow/run.sh sh flow/librelane/run_harden_eco.sh r1ctrl_ll_20261028_t24 r1ctrl_ll_20261028_t30 _16393_ delaynet_15_clk flow/librelane/cfg_v09_t29.yaml
```

- LibreLane 3.1.0.dev2, Classic flow, PDK commit `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`, container tapeoutbench-eda:latest sha256:ddeb69576f28
- Start 2026-10-28T10:00:10Z, end 2026-10-28T12:25:55Z, exit code 0 (timeout 14400 s)
- RTL: sha256 of the concatenated `rtl/*.v` copy in the run: `f68edabeb4746bcadabad68116083c1791c6616be1a26bef2647bd73be47d2d8`; register-file variant: flip-flops (`R1_CFG_FLOPS` in config.yaml)
- Bulk run: `<G1_RESULTS_ROOT>/r1_ctrl/r1ctrl_ll_20261028_t30/` (inputs in `inputs.sha256`); last step `41-misc-reportmanufacturability`
- Steps 1-35 (synthesis to CTS) are those of `r1ctrl_ll_20261028_t24`; between CTS and `OpenROAD.ResizerTimingPostCTS` the input A of `_16393_` (lost by CTS) was connected to `delaynet_15_clk` (`flow/librelane/eco_cts_pin.tcl`, log `eco/eco.log`); the step numbers of this run start at 01 after the repair. The slow max-slew count (6 pins = 3 nets) is a sign-off failure (README revision 0.9, row 10).

| Metric | Value |
| --- | --- |
| Die / core area (µm²) | 361228 / 333666 |
| Standard-cell area (µm²), utilisation | 284899, 0.854 |
| Sequential / clock buffers / timing-repair buffers (µm²) | 112005 / 7376 / 23522 |
| Sign-off STA nom_typ_1p20V_25C at 42 MHz: setup WS / TNS (ns), violators; hold WS (ns); max-slew violations | 0.000 / 0.00, 0; 0.195; 0 |
| Sign-off STA nom_fast_1p32V_m40C at 42 MHz: setup WS / TNS (ns), violators; hold WS (ns); max-slew violations | 0.000 / 0.00, 0; 0.111; 0 |
| Sign-off STA nom_slow_1p08V_125C at 42 MHz: setup WS / TNS (ns), violators; hold WS (ns); max-slew violations | 0.000 / 0.00, 0; 0.341; 6 |
| Detailed routing DRC errors (final) | 0 |
| Magic DRC / KLayout DRC errors | 0 / 0 |
| LVS errors (netgen) | 0 |
| Antenna violating nets | 0 |

Slow-corner setup violators in the sign-off report, by start-point type: none

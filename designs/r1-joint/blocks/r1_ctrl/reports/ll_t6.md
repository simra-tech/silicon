# LibreLane run `r1ctrl_ll_20261020_t6` (r1_ctrl)

Command (repository root, `designs/r1-joint/blocks/r1_ctrl` as `G1_WORKDIR`, CPU set 112-115):

```
flow/run.sh sh flow/librelane/run_harden.sh r1ctrl_ll_20261020_t6 7200
```

- LibreLane 3.1.0.dev2, Classic flow, PDK commit `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`, container tapeoutbench-eda:latest sha256:ddeb69576f28
- Start 2026-10-20T21:42:37Z, end 2026-10-20T22:41:26Z, exit code 0 (timeout 7200 s)
- RTL: sha256 of the concatenated `rtl/*.v` copy in the run: `7f147fe9017556df9f7c41bd2aaf126f1ce036c78bdbff8904ee467d9adbb131`; register-file variant: flip-flops (`R1_CFG_FLOPS` in config.yaml)
- Bulk run: `<G1_RESULTS_ROOT>/r1_ctrl/r1ctrl_ll_20261020_t6/` (inputs in `inputs.sha256`); last step `76-misc-reportmanufacturability`

| Metric | Value |
| --- | --- |
| Die / core area (µm²) | 477221 / 448003 |
| Standard-cell area (µm²), utilisation | 269618, 0.602 |
| Sequential / clock buffers / timing-repair buffers (µm²) | 99977 / 6984 / 15040 |
| Sign-off STA nom_typ_1p20V_25C at 42 MHz: setup WS / TNS (ns), violators; hold WS (ns); max-slew violations | 0.000 / 0.00, 0; 0.182; 0 |
| Sign-off STA nom_fast_1p32V_m40C at 42 MHz: setup WS / TNS (ns), violators; hold WS (ns); max-slew violations | 0.000 / 0.00, 0; 0.102; 0 |
| Sign-off STA nom_slow_1p08V_125C at 42 MHz: setup WS / TNS (ns), violators; hold WS (ns); max-slew violations | 0.000 / 0.00, 0; 0.314; 0 |
| Detailed routing DRC errors (final) | 0 |
| Magic DRC / KLayout DRC errors | 0 / 0 |
| LVS errors (netgen) | 0 |
| Antenna violating nets | 0 |

Slow-corner setup violators in the sign-off report, by start-point type: none

Notes: this is the hardening run of record for revision 0.3 (D18 RTL). Its RTL copy is identical
to the tree and to the simulation run of record `r1ctrl_20261020_v03` (same sha256). A setup WS of
0.000 is the clipped report value (0 violators at all corners). Compared with t5 (RTL before D18):
die 0.477 vs 0.420 mm², standard-cell area 269 618 vs 236 277 µm², no max-slew violations (t5: 2 at
the slow corner). Utilisation was 55 % at the start; a denser floorplan was not tried.

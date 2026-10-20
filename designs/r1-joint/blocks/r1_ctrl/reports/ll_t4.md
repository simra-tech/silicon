# LibreLane run `r1ctrl_ll_20261020_t4` (r1_ctrl)

Command (repository root, `designs/r1-joint/blocks/r1_ctrl` as `G1_WORKDIR`, CPU set 112-115):

```
flow/run.sh sh flow/librelane/run_harden.sh r1ctrl_ll_20261020_t4 12600
```

- LibreLane 3.1.0.dev2, Classic flow, PDK commit `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`, container tapeoutbench-eda:latest sha256:ddeb69576f28
- Start 2026-10-20T19:05:47Z, end 2026-10-20T21:07:13Z, exit code 2 (timeout 12600 s)
- RTL: sha256 of the concatenated `rtl/*.v` copy in the run: `207758df7f87212304493a5d940f0ee812d88642418ecc19af6ade903d961d19`; register-file variant: latch words (no `R1_CFG_FLOPS`)
- Bulk run: `<G1_RESULTS_ROOT>/r1_ctrl/r1ctrl_ll_20261020_t4/` (inputs in `inputs.sha256`); last step `76-misc-reportmanufacturability`

| Metric | Value |
| --- | --- |
| Die / core area (µm²) | 371762 / 344790 |
| Standard-cell area (µm²), utilisation | 218207, 0.633 |
| Sequential / clock buffers / timing-repair buffers (µm²) | 73307 / 13795 / 12953 |
| Sign-off STA nom_typ_1p20V_25C at 42 MHz: setup WS / TNS (ns), violators; hold WS (ns); max-slew violations | 0.000 / 0.00, 0; 0.190; 0 |
| Sign-off STA nom_fast_1p32V_m40C at 42 MHz: setup WS / TNS (ns), violators; hold WS (ns); max-slew violations | 0.000 / 0.00, 0; 0.108; 0 |
| Sign-off STA nom_slow_1p08V_125C at 42 MHz: setup WS / TNS (ns), violators; hold WS (ns); max-slew violations | -2.098 / -129.78, 180; 0.248; 9 |
| Detailed routing DRC errors (final) | 0 |
| Magic DRC / KLayout DRC errors | 0 / 0 |
| LVS errors (netgen) | 0 |
| Antenna violating nets | 0 |

Slow-corner setup violators in the sign-off report, by start-point type: 180 × positive level-sensitive latch clocked by clk

Notes: revision-0.3 RTL with the latch register file (before the change to flip-flops). The flow
completed with exit code 2 because sign-off STA failed at the slow corner: setup WNS −2.098 ns,
TNS −129.78 ns, 180 violators, all from configuration latches (latch transparency carries the
write-data path into the datapath). Typical and fast corners met; DRC, LVS and antenna clean.
At 32.61 MHz (the fastest `r1_osc` clock at ss) the slow corner still fails by −0.75 ns (run
`r1ctrl_sta_ss_20261020`). This run is the reason the register file of record is flip-flops (t5).
It is on the pre-D18 RTL.

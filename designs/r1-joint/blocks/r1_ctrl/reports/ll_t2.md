# LibreLane run `r1ctrl_ll_20261020_t2` (r1_ctrl)

Command (repository root, `designs/r1-joint/blocks/r1_ctrl` as `G1_WORKDIR`, CPU set 112-115):

```
flow/run.sh sh flow/librelane/run_harden.sh r1ctrl_ll_20261020_t2 10800
```

- LibreLane 3.1.0.dev2, Classic flow, PDK commit `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`, container tapeoutbench-eda:latest sha256:ddeb69576f28
- Start 2026-10-20T18:05:30Z, end 2026-10-20T20:02:15Z, exit code 2 (timeout 10800 s)
- RTL: sha256 of the concatenated `rtl/*.v` copy in the run: `5caf33967b11446d41de593d20e5b82d5c802d9a0b75412922bfc0cb99f9a50f`; register-file variant: latch words (no `R1_CFG_FLOPS`)
- Bulk run: `<G1_RESULTS_ROOT>/r1_ctrl/r1ctrl_ll_20261020_t2/` (inputs in `inputs.sha256`); last step `76-misc-reportmanufacturability`

| Metric | Value |
| --- | --- |
| Die / core area (µm²) | 354122 / 327673 |
| Standard-cell area (µm²), utilisation | 208580, 0.637 |
| Sequential / clock buffers / timing-repair buffers (µm²) | 69658 / 13142 / 13180 |
| Sign-off STA nom_typ_1p20V_25C at 42 MHz: setup WS / TNS (ns), violators; hold WS (ns); max-slew violations | 0.000 / 0.00, 0; 0.173; 0 |
| Sign-off STA nom_fast_1p32V_m40C at 42 MHz: setup WS / TNS (ns), violators; hold WS (ns); max-slew violations | 0.000 / 0.00, 0; 0.096; 0 |
| Sign-off STA nom_slow_1p08V_125C at 42 MHz: setup WS / TNS (ns), violators; hold WS (ns); max-slew violations | -2.206 / -118.38, 152; 0.305; 5 |
| Detailed routing DRC errors (final) | 0 |
| Magic DRC / KLayout DRC errors | 0 / 0 |
| LVS errors (netgen) | 0 |
| Antenna violating nets | 0 |

Slow-corner setup violators in the sign-off report, by start-point type: 152 × positive level-sensitive latch clocked by clk

Notes: RTL of this run is revision 0.2 (run of record `r1ctrl_20261020_v02b`, before the 0.3 changes);
it was started first to learn whether the latch register file routes and times at 55 % start
utilisation. A setup WS of 0.000 is the clipped report value (no negative slack). The slow-corner
STA was repeated outside LibreLane at 32.61 MHz (the fastest r1_osc clock at ss, 1.08 V, 125 °C,
code 0; `r1_osc` README) on the same netlist and SPEF: WNS −0.72 ns, TNS −58.5 ns; the worst
path is a latch-to-latch path with time borrowing from a configuration word into a PWM shadow
latch (run `r1ctrl_sta_ss_20261020`, script `sta_ss.tcl` there). The same script at 42 MHz
reproduces the LibreLane value (−2.206 ns).

# LibreLane run `r1ctrl_ll_20261021_t7` (r1_ctrl)

Command (repository root, `designs/r1-joint/blocks/r1_ctrl` as `G1_WORKDIR`, CPU set 112-115):

```
flow/run.sh sh flow/librelane/run_harden.sh r1ctrl_ll_20261021_t7 7200
```

- LibreLane 3.1.0.dev2, Classic flow, PDK commit `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`, container tapeoutbench-eda:latest sha256:ddeb69576f28
- Start 2026-10-21T00:09:05Z, end 2026-10-21T01:21:03Z, exit code 0 (timeout 7200 s)
- RTL: sha256 of the concatenated `rtl/*.v` copy in the run: `6ca24fce22d79594601c5d73de0db91f73fd3fa7b62944b96e08eda01e2f6eb0`; register-file variant: flip-flops (`R1_CFG_FLOPS` in config.yaml)
- Bulk run: `<G1_RESULTS_ROOT>/r1_ctrl/r1ctrl_ll_20261021_t7/` (inputs in `inputs.sha256`); last step `76-misc-reportmanufacturability`

| Metric | Value |
| --- | --- |
| Die / core area (µm²) | 345280 / 318286 |
| Standard-cell area (µm²), utilisation | 239201, 0.752 |
| Sequential / clock buffers / timing-repair buffers (µm²) | 94753 / 4736 / 13354 |
| Sign-off STA nom_typ_1p20V_25C at 42 MHz: setup WS / TNS (ns), violators; hold WS (ns); max-slew violations | 0.000 / 0.00, 0; 0.075; 0 |
| Sign-off STA nom_fast_1p32V_m40C at 42 MHz: setup WS / TNS (ns), violators; hold WS (ns); max-slew violations | 0.000 / 0.00, 0; 0.021; 0 |
| Sign-off STA nom_slow_1p08V_125C at 42 MHz: setup WS / TNS (ns), violators; hold WS (ns); max-slew violations | 0.000 / 0.00, 0; 0.183; 0 |
| Detailed routing DRC errors (final) | 0 |
| Magic DRC / KLayout DRC errors | 0 / 0 |
| LVS errors (netgen) | 0 |
| Antenna violating nets | 0 |

Slow-corner setup violators in the sign-off report, by start-point type: none

Notes: hardening run of record for revision 0.4 (D10 area closure). The RTL copy is identical to the tree and to the
simulation run of record `r1ctrl_20261021_v04` (same sha256). Setup WS 0.000 is the clipped report value (0 violators
at all corners). Core bbox 11.04 11.34 509.28 650.16 um (498.24 x 638.82 = 318 286 um^2; the requested core of
320 400 um^2 was snapped to the site grid). Utilisation 75.15 % of that core, 74.65 % of 320 400 um^2. Die 520 x 664 um.
6 max-fanout violations (limit 16) at each corner; 0 max-slew and 0 max-cap violations. Pin sides: north gate/bus,
east analog-safe/osc, south ADC/T2F, west `ana_ctrl`/`sdi`/`en_pad` (`flow/librelane/pins.cfg`). CTS: `buf_2` only,
cluster size 30, diameter 120 (config.yaml). Class split: sequential 94 753, clock buffers 4 736, timing-repair
buffers 13 354 um^2; 115 hold buffers. Compared with t6 (RTL 0.3): placed area 269 618 -> 239 201 um^2.
Companion trial `r1ctrl_ll_20261021_t8` (core 323 070 um^2) timed out in detailed routing (exit 124) and is not a result.

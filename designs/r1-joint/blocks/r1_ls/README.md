# R1_LS — level-shifter count and characterisation (schematic level)

State on 2026-10-20: **count made, cells characterised at schematic level, nothing laid out here.** The block reuses the G1
cells unchanged. All numbers are **simulated** (ngspice-46, schematic level, no parasitics). Nothing is measured.

The G1 cell `g1_ls_up` (1.2 V to 3.3 V) is copied byte for byte. Its layout (GDS, LEF) stays in the G1 tree. R1 uses that layout.
The 3.3 V to 1.2 V cell `g1_lvldn` and the shifter `g1_lvlup` come from the G1 gate block. They are also copied unchanged.

## Built against

| Item | Value | How established |
| --- | --- | --- |
| PDK | IHP-Open-PDK `84374023ee8b4b126bebbba67fcbada0a9c0ff0b` | `/foss/pdks/ihp-sg13g2/COMMIT` in the container (`flow/run.sh` checks it) |
| ngspice | 46 | `ngspice -v` in the container |
| Container image | `tapeoutbench-eda:latest`, `sha256:ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2` | `flow/run.sh` compares the image id before every run |
| Models | `cornerMOSlv.lib`, `cornerMOShv.lib` (`mos_tt`, `mos_ss`, `mos_ff`), PSP103 OSDI | decks `sim/run_ls.py` |
| Python on the host | 3.6 | deck generator and table script only |
| CPU | CPU 119 only (`G1_CPUSET=119`, `G1_CPUS=1`) | run command in `sim/runs/ls-20261020b/run.json` |

## Cells (reused, unchanged)

| Cell | Function | Source in the G1 tree | sha256 of the copied netlist (`schematic/`) |
| --- | --- | --- | --- |
| `g1_ls_up` | 1.2 V to 3.3 V, `in out vdd vdda vss` | `designs/g1-guardian/blocks/g1_ctrl/ls/sim/netlist/g1_ls_up.spice` | `5567c8079e57ced973d3e47dad6a7afe1776987de3962f9be397c6a8d0549b56` (`schematic/g1_ls_up_copy.spice`) |
| `g1_lvlup` | 1.2 V to 3.3 V, smaller pull-downs (1.9 um), inside `g1_gate` | `designs/g1-guardian/blocks/g1_gate/sim/netlist/g1_lvlup.spice` | `71af3cd83a2cdd921a23d8a056e7c32290961842cb0247d88d3811da68eaab12` (`schematic/g1_lvlup_copy.spice`; also holds `g1_lv_inv`, `g1_hv_inv`) |
| `g1_lvldn` | 3.3 V to 1.2 V, differential input `a ab`, `a ab y vdd vss` | `designs/g1-guardian/blocks/g1_gate/sim/netlist/g1_lvldn.spice` | `d253d0a60a34cfa169db3b9204f0914ec821d804dbccfd16ee493c2c61696af6` (`schematic/g1_lvldn_copy.spice`) |

Layout identity of `g1_ls_up` (G1 tree, not copied): `layout/g1_ls_up.lef` sha256 `d67765cb55fd013d92771aee6201cb482a6a297f89910925f67251c2f5429088`,
`layout/g1_ls_up.gds` sha256 `85de277ca1c2de41fa59e577db1d6d7633edddb24abf3b6d57e6787afd335546`. DRC and LVS of that GDS passed in G1
(`designs/g1-guardian/blocks/g1_ctrl/ls/README.md`). They were not repeated here.
`g1_lvlup` and `g1_lvldn` have no stand-alone layout. They exist only inside the G1 `g1_gate` macro.

## Count of level shifters

Source: `../INTERFACES.md`, the block READMEs, and `designs/g1-guardian/blocks/g1_t2f/INTERFACE.md`.

| Signal group | Direction | Where the shifter is | Count in r1_ls | Basis |
| --- | --- | --- | ---: | --- |
| `pwm_a/b/c`, `gate_en` to the three `sg13g2_IOPadOut30mA` | 1.2 V to 3.3 V | **Not needed if the AND is done in the core.** The pad has its own core-to-IO shifter on `c2p` (see below). `g1_lvlup` x 4 only if the AND is done in the 3.3 V domain (variant H of `../r1_gate`) | 0 (variant L) or 4 `g1_lvlup` (variant H, counted in `r1_gate`) | `../r1_gate/README.md` |
| `c1 c2 c3 c4` (AFE gain controls) | 1.2 V to 3.3 V | needed: ports are 3.3 V signals, the decoder and shifters are not in `r1_afe` | **4 `g1_ls_up`** | `../r1_afe/README.md`, open issue 6 |
| T2F `en`, `mode` | 1.2 V to 3.3 V | needed: ports `en`, `mode` sit on the 3.3 V `vdd` of the T2F rev2 netlist (`fout` is on `vdd12`) | **2 `g1_ls_up`** (assumed: the R1 T2F README does not exist yet; the netlist `../r1_t2f/schematic/g1_t2f_rev2.spice` keeps the G1 ports) | `../r1_t2f/schematic/G1_INTERFACE.md`, G1 `g1_t2f/INTERFACE.md` |
| BGR `r4` test bit | 1.2 V to 3.3 V | not needed: the R1 bandgap removed the `r4` mode | 0 | `../r1_bgr/README.md` (table "r4 1:4 test mode: removed") |
| `oc_a neg_a oc_b neg_b` (comparator flags) | 3.3 V to 1.2 V | inside `r1_safe` (down-shift stage in every comparator, output is 1.2 V logic) | not applicable, inside `r1_safe` | `../r1_safe/README.md` (Outputs row: 1.2 V logic) |
| `r1_safe` threshold and calibration code bits | 1.2 V to 3.3 V | inside `r1_safe` (`r1_safe_ls`, 24 shifters counted in its area table) | not applicable, inside `r1_safe` | `../r1_safe/README.md` |
| `r1_isense` auto-zero phases `az_lv`, `azh_lv` | 1.2 V to 3.3 V | inside `r1_isense` | not applicable, inside `r1_isense` | `../r1_isense/README.md` |
| `EN` / `STO_IN` pad input | 3.3 V to 1.2 V | inside the `sg13g2_IOPadIn` cell (its `p2c` output is 1.2 V) | not applicable, inside the pad | PDK `sg13g2_IOPadIn` |
| `r1_osc`, `r1_adc`, `r1_ctrl` interfaces | 1.2 V only | no domain crossing | not applicable | `../r1_osc/README.md`, `../r1_adc/README.md` |

**Total in `r1_ls`: 6 x `g1_ls_up` (4 for AFE c1..c4, 2 for T2F en and mode). 3.3 V to 1.2 V receivers needed in `r1_ls`: 0.**
The cell `g1_lvldn` is the available cell if a later block needs a down-shifter (it is characterised below).
The same count with the G1 allocation (3 shifters, one of them for `r4`) shows the change: AFE adds 4, `r4` is gone.

Open point for the owner of `r1_t2f`: the `en` and `mode` bits may stay at 1.2 V if the T2F is re-written on the 1.2 V domain.
Then the count drops to 4. This block counts the T2F netlist as it is today.

## Result tables (simulated)

Method (script `sim/run_ls.py`, decks generated per cell and corner):

- Input: 1 ns edges between 0 and the input-domain supply. First a 100 ns pulse (rise at 50 ns, fall at 150 ns) for the delays.
  Then six cycles at 30 MHz (33.33 ns period, 50 % duty) for the duty distortion.
- Load: 20 fF plus one inverter of the output domain. `g1_ls_up` and `g1_lvlup` drive one `g1_hv_inv`. `g1_lvldn` drives one `g1_lv_inv`.
- Delay: input 50 % to output 50 % of the output domain. Edge times: 10 % to 90 % of the output swing.
- Rise-fall skew = rise delay minus fall delay. Pulse width change = output high time minus input high time in the fourth cycle. Duty distortion = pulse width change / 33.33 ns.
- Skew between two instances of the same cell is 0 ps in this simulation (identical devices, no mismatch). A mismatch Monte Carlo was **not run**.
- The corner is: MOS corner, temperature, 3.3 V rail (3.0 / 3.3 / 3.6 V), 1.2 V rail (1.08 / 1.2 / 1.32 V). The "stress" row is an extra point:
  slow core devices at -40 C with the highest 3.3 V rail. It tests the contention of the 3.3 V keeper against a weakly driven pull-down.
- `g1_lvldn` input is an ideal 1 ns ramp of 3.3 V. Its delay is short against the input ramp. At the slow-input stress point the output falls before the input
  reaches 50 % (negative delay). The delay of the real chain (HV inverter driving `g1_lvldn`) is in `../r1_gate/README.md`.

### Timing, duty distortion and skew

| Cell | Corner | rise delay (ps) | fall delay (ps) | rise-fall skew (ps) | 10-90 rise (ps) | 90-10 fall (ps) | pulse width change at 30 MHz (ps) | duty distortion (% of period) | levels low / high (V) |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `g1_ls_up` | tt, 27 C, 3.3 / 1.2 V | 662 | 824 | -162 | 222 | 309 | +162 | +0.49 | 3.2e-09 / 3.3 |
| `g1_ls_up` | ss, 125 C, 3.0 / 1.08 V | 1011 | 1351 | -341 | 410 | 469 | +341 | +1.02 | 8.3e-08 / 3 |
| `g1_ls_up` | ff, -40 C, 3.6 / 1.32 V | 489 | 556 | -67 | 153 | 233 | +67 | +0.20 | 5.7e-09 / 3.6 |
| `g1_ls_up` | ss, -40 C, 3.6 / 1.08 V (stress) | 1011 | 1040 | -29 | 298 | 294 | +29 | +0.09 | 2.2e-09 / 3.6 |
| `g1_lvlup` | tt, 27 C, 3.3 / 1.2 V | 937 | 801 | 136 | 276 | 300 | -136 | -0.41 | 3.2e-09 / 3.3 |
| `g1_lvlup` | ss, 125 C, 3.0 / 1.08 V | 1745 | 1494 | 250 | 498 | 454 | -251 | -0.75 | 8.3e-08 / 3 |
| `g1_lvlup` | ff, -40 C, 3.6 / 1.32 V | 636 | 524 | 112 | 169 | 225 | -112 | -0.34 | 5.7e-09 / 3.6 |
| `g1_lvlup` | ss, -40 C, 3.6 / 1.08 V (stress) | 1699 | 1453 | 246 | 310 | 287 | -246 | -0.74 | 2.2e-09 / 3.6 |
| `g1_lvldn` | tt, 27 C, 3.3 / 1.2 V | 241 | 44 | 197 | 298 | 327 | -197 | -0.59 | 7.1e-08 / 1.2 |
| `g1_lvldn` | ss, 125 C, 3.0 / 1.08 V | 328 | 117 | 211 | 365 | 366 | -211 | -0.63 | 4.6e-07 / 1.08 |
| `g1_lvldn` | ff, -40 C, 3.6 / 1.32 V | 209 | 5 | 205 | 285 | 328 | -205 | -0.61 | 8.7e-08 / 1.32 |
| `g1_lvldn` | ss, -40 C, 3.6 / 1.08 V (stress) | 316 | -38 | 354 | 389 | 266 | -354 | -1.06 | 4.9e-09 / 1.08 |

### Supply current

| Cell | Corner | static I(3.3 V domain), in low / high (pA) | static I(1.2 V domain), in low / high (pA) | peak I(3.3 V) rising edge (uA) | peak I(3.3 V) falling edge (uA) | peak I(1.2 V) rising edge (uA) |
| --- | --- | --- | --- | ---: | ---: | ---: |
| `g1_ls_up` | tt, 27 C, 3.3 / 1.2 V | 14.9 / 14.9 | 60.7 / 81.2 | 783 | 387 | 9.1 |
| `g1_ls_up` | ss, 125 C, 3.0 / 1.08 V | 131.9 / 131.9 | 188.2 / 765.7 | 417 | 213 | 3.9 |
| `g1_ls_up` | ff, -40 C, 3.6 / 1.32 V | 21.8 / 21.8 | 105.1 / 33.2 | 1249 | 651 | 28.9 |
| `g1_ls_up` | ss, -40 C, 3.6 / 1.08 V (stress) | 14.4 / 14.4 | 5.9 / 1.1 | 742 | 450 | 4.2 |
| `g1_lvlup` | tt, 27 C, 3.3 / 1.2 V | 14.8 / 14.8 | 60.7 / 81.2 | 672 | 386 | 11.1 |
| `g1_lvlup` | ss, 125 C, 3.0 / 1.08 V | 119.7 / 119.7 | 188.2 / 765.7 | 349 | 212 | 4.7 |
| `g1_lvlup` | ff, -40 C, 3.6 / 1.32 V | 21.8 / 21.8 | 105.1 / 33.2 | 1145 | 649 | 32.9 |
| `g1_lvlup` | ss, -40 C, 3.6 / 1.08 V (stress) | 14.4 / 14.4 | 5.9 / 1.1 | 660 | 448 | 4.5 |
| `g1_lvldn` | tt, 27 C, 3.3 / 1.2 V | n/a (no 3.3 V supply pin) | 125.3 / 177.3 | n/a | n/a | 264.4 |
| `g1_lvldn` | ss, 125 C, 3.0 / 1.08 V | n/a (no 3.3 V supply pin) | 594.0 / 1177.9 | n/a | n/a | 148.9 |
| `g1_lvldn` | ff, -40 C, 3.6 / 1.32 V | n/a (no 3.3 V supply pin) | 175.9 / 243.9 | n/a | n/a | 464.3 |
| `g1_lvldn` | ss, -40 C, 3.6 / 1.08 V (stress) | n/a (no 3.3 V supply pin) | 10.5 / 8.3 | n/a | n/a | 181.8 |

Static current is the DC operating point with the input at 0 and at the supply. The 3.3 V domain of `g1_lvldn` has no supply pin
(the thick-oxide gates draw no DC current). Reference from the G1 evidence (not repeated here): the G1 81-point sweep of `g1_ls_up` gave
at most 10.3 nA (3.3 V rail) and 116 nA (1.2 V rail) at ff/175 C (`designs/g1-guardian/blocks/g1_ctrl/ls/README.md`).
The R1 corners above stay in the pA range. The hot-ff point is **not run** in R1 (R1 specifies up to 125 C).

## Area

| Item | Value | Basis |
| --- | --- | --- |
| One `g1_ls_up` | 9.20 x 11.70 um = **107.64 um2** | G1 LEF `SIZE 9.200 BY 11.700` |
| 6 x `g1_ls_up` (the counted set) | **645.8 um2 = 0.00065 mm2** | 6 x 107.64 |
| Spacing rule from G1 | instances at least 1.2 um apart, own three supply straps each | `designs/g1-guardian/blocks/g1_ctrl/ls/README.md` |
| `g1_lvlup`, `g1_lvldn` | no stand-alone layout | laid out inside `../r1_gate/layout/r1_gate_hv_filled.gds` (variant H only) |

At 20 um pitch (the G1 placement) six cells use a strip of 120 um by 11.7 um, about 0.0014 mm2 including the gaps. This is a placement choice and is not part of the count.
The P0 budget line "BGR, T2F, 3 gates, level shifters 0.055 mm2" is not affected.

## Status

| Check | Status | Evidence |
| --- | --- | --- |
| Count of shifters from INTERFACES.md and block READMEs | done (6 `g1_ls_up`; 0 receivers) | this file, section "Count" |
| Reuse of `g1_ls_up` unchanged | passed (netlist copy sha256 equals the G1 netlist) | `schematic/g1_ls_up_copy.spice`, `sim/runs/ls-20261020b/run.json` |
| Delay, edge times, duty distortion, skew: `g1_ls_up`, `g1_lvlup`, `g1_lvldn` at tt, ss, ff | passed (full swing in every run, results above) | `sim/results/ls-20261020b.json`, run `ls-20261020b` |
| Stress point (ss, -40 C, 3.6 V / 1.08 V) | passed: all three cells switch fully | same |
| Static current per shifter | done at three corners and the stress point (pA range) | same |
| Area | done (from the G1 LEF) | this file |
| Receivers for `oc_a neg_a oc_b neg_b` | not applicable, inside `r1_safe` | `../r1_safe/README.md` |
| 81-point sweep, hot-ff static current, back-powering and power-up order of `g1_ls_up` in R1 | not run in R1 (G1 ran 81 points and 6 power-up cases on the same netlist) | G1 README |
| Mismatch Monte Carlo, instance-to-instance skew | not run | - |
| Layout, DRC, LVS, antenna of the cell | passed (R1 copy of the G1 cell), see "Layout" below | `layout/runs/` |
| PEX of the R1 placement | not run | - |
| Timing into the real loads (AFE gain switches, T2F pins) | not run (20 fF + 1 inverter only) | - |

## Open issues

1. The T2F `en` and `mode` shifters are counted from the netlist and the G1 interface. The `r1_t2f` README does not exist yet. Confirm the domain.
2. The AFE decoder `PGA_GAIN` to `c1..c4` (table in `../r1_afe/README.md`) is not written. It belongs in `r1_ctrl` (1.2 V) in front of the four shifters.
3. `c1..c4` and `en`, `mode` are quasi-static. A gain change moves the AFE operating point. Settling after a gain change is **not run**.
4. Power-up sequence: G1 checked `g1_ls_up` for the cases "3.3 V first" and "1.2 V first" and "1.2 V removed". The check must be repeated on the R1 supplies if the R1 power sequence differs.

## Files

| File | Content |
| --- | --- |
| `schematic/g1_ls_up_copy.spice`, `g1_lvlup_copy.spice`, `g1_lvldn_copy.spice` | unchanged copies of the G1 netlists |
| `sim/run_ls.py` | deck generator and runner (host python 3.6, ngspice through `flow/run.sh`) |
| `sim/make_tables.py` | makes the tables from `sim/results/<run-id>.json` |
| `sim/results/ls-20261020b.json`, `ls-20261020b_tables.md` | results, tables |
| `sim/runs/ls-20261020b/run.json` | command, versions, inputs, result, disposition |
| `<G1_RESULTS_ROOT>/r1_ls/ls-20261020b/` | decks and logs (bulk results root) |

## Layout

Source: the G1 cell layout, copied and renamed. `designs/g1-guardian/blocks/g1_ctrl/ls/layout/g1_ls_up.gds` sha256
`85de277ca1c2de41fa59e577db1d6d7633edddb24abf3b6d57e6787afd335546` (generator `g1_ls_up.py`, sha256 `3f441cd5...`). The netlist of record
`schematic/g1_ls_up_copy.spice` (sha256 `5567c807...`) is the G1 netlist. The layout is one cell: one `g1_ls_up` level shifter (1.2 V to 3.3 V).
The top cell is named `r1_ls`. The chip places this cell several times (six in the S6 floorplan); a placement is not part of this layout.
`g1_lvlup` and `g1_lvldn` have no stand-alone layout; they exist in `../r1_gate/layout/r1_gate_hv_filled.gds` (variant H only).

Files in `layout/`:

| File | Content |
| --- | --- |
| `r1_ls.gds` | GDS of record, top cell `r1_ls`, sha256 `a4f496364b55c71a035f44a9b13b68fd8475f98b05f5e13a4e38e9ec1703b4de`, 21 kB. No fill (single cell) |
| `r1_ls.lef`, `r1_ls.vh` | LEF and black-box Verilog, macro and module `r1_ls` |
| `r1_ls_lvs.cdl` | LVS reference from `schematic/g1_ls_up_copy.spice` by `make_lvs_cdl.py` (sha256 `4f3fefbe...`); equal to the G1 `g1_ls_up.cdl` except the subcircuit name |
| `r1_ls_layout.py` | generator (G1 `g1_ls_up.py`, cell and file names changed) |
| `run_checks.sh`, `write_runjson.py`, `check_pins.py`, `xor_vs_g1.py` | check flow |
| `runs/` | `run.json` of the runs (tag `a`) |

Built against: PDK commit `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`, KLayout 0.30.9, container image `sha256:ddeb6957...`, CPU set 100-102.

| Check | Status | Evidence |
| --- | --- | --- |
| Generator runs | passed | `<G1_RESULTS_ROOT>/r1_ls/layout-gen-a/gen.log` |
| Geometry equal to the G1 GDS (XOR, every layer) | passed, XOR area 0 | `layout/runs/layout-gen-a/xor_vs_g1.log` |
| DRC, deep, `--no_density`, main + maximal tables | passed, 0 markers | `layout/runs/layout-drc-a/run.json`, `<G1_RESULTS_ROOT>/r1_ls/layout-drc-a/` |
| Antenna, `--antenna_only` | passed, 0 markers | `layout/runs/layout-ant-a/run.json` |
| LVS, deep, against `r1_ls_lvs.cdl` | passed, netlists match (8 devices: 3 HV PMOS, 3 HV NMOS, 1 LV PMOS, 1 LV NMOS; 8 nets) | `layout/runs/layout-lvs-a/run.json`, `<G1_RESULTS_ROOT>/r1_ls/layout-lvs-a/` |
| Pin names equal the CDL ports | passed | `layout/runs/layout-gen-a/check_pins.log` |
| Density, PEX, post-layout simulation | not run (density: chip level; PEX: G1 ran a bounded C-PEX on this geometry, not repeated) | - |

Area: 9.2 x 11.7 um = 107.64 um2 (`prBoundary` 189/4). Pins: `in` Metal2 (0..0.85, 4.8..5.0), west edge; `out` Metal1 (8.0..9.2, 4.1..5.7), east edge;
`vdd` Metal1 (0.2..1.8, 9.8..10.2), `vdda` Metal1 (4.0..8.6, 11.2..11.6), `vss` Metal1 (0.2..8.7, 0.3..0.85), inside the cell (the chip strapping reaches them).

| Item | G1 | R1 |
| --- | --- | --- |
| Top cell, LEF macro, Verilog module | `g1_ls_up` | `r1_ls` |
| LVS reference subcircuit | `g1_ls_up` | `r1_ls` |
| Devices, geometry, pins | - | no difference (XOR 0) |

Open issues: the power-up check on the R1 supply order (see "Open issues" above) is a schematic-level item and is still open. Rail strapping of the six placements is a chip-level item.

Failures and mistakes: none in this block. (The shared T7 tooling failure of the fill script does not apply: this cell has no fill step.)

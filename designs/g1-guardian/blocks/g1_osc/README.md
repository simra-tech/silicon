# G1_OSC

## Variant on the chip of record (2026-09-25)

The oscillator placed in the chip of record (`g1_chip_top_1414.gds`, `629d303a…`) is **R0.95**:
the macro below with the four `RRA`/`RRB` charging-resistor PolyRes segments shortened from 58.5 µm
to 55.575 µm (each 1 µm × 117 µm resistor becomes 1 µm × 111.15 µm). Adopted on the chip of record by
the owner decision of 2026-09-24. Outline and pins are those of the 166 × 137.6 µm macro.

| Item | Path (block-relative) | Identity |
| --- | --- | --- |
| Schematic-level R0.95 source | `sim/qualification/runs/osc_r095_candidate_shard0_20260921_01/osc.spice` | `f08bf051…` |
| Capacitance extraction of the isolated filled R0.95 macro (kpex 0.3.12, 2.5D CC; used by `g1_top --blockset c1414`) | `sim/qualification/fulltree_r095_load_20260924/common/osc.spice` | `8efd7a09…` |
| Isolated-macro physical record | `reports/r095_physical_20260924/README.md` | — |
| Chip OSC cell vs isolated R0.95 GDS (bare `411d52f7…`, filled `960a9e9a…`) | XOR empty outside fill layers; the 117 µm `layout/g1_osc.gds` differs on the resistor layers | `../g1_padring/reports/signoff-1414-20260924/blockmap/block_xor.json` |
| R0.95 in the full chip | `reports/r095_fullchip_physical_20260924/README.md` | — |

| Check / number (R0.95) | Status | Evidence |
| --- | --- | --- |
| Isolated bare and filled macro: main/maximal DRC, antenna, stock strict-port LVS | passed | `reports/r095_physical_20260924/README.md` |
| Isolated filled macro, stock density-only | **failed** (8 markers: `AFil.g`, `M1.j`–`M5.j`, `TM1.c`, `TM2.c`; macro bbox used as the density-window origin) | same |
| kpex internal LVS of the MIM-stripped PEX input | **failed** ("Netlists don't match"; the separate stock LVS passed) | same |
| Chip-level DRC, density and antenna on `629d303a…` | passed (0 markers) | `../g1_padring/reports/signoff-1414-20260924/README.md` |
| Frequency, nominal trim 8, tt / 1.2 V / 27 °C, with the 94-buffer clock-tree load | 9.436 MHz (simulated; includes an estimated 459.8 Ω / 60.4 fF OSC-to-root route, not extracted) | `sim/qualification/fulltree_r095_load_20260924/README.md` |
| Slow/hot reach, code 0, ss/wcs/wcs, 1.08 V, 125 °C | 10.447 MHz on the CPEX with the full-tree load (`results/slowhot_code0.json`); 10.445 MHz on the pre-CPEX schematic source `f08bf051` with the actual receiver; baseline 117 µm macro 9.975 MHz (simulated) | same; `sim/qualification/README.md` |
| Chip netlists, OSC clocking the RTL (no TRIP), trim 8 | tt/27 °C 9.443–9.483 MHz (0.5 ns step); ss/125 °C 7.61 MHz and ff/−40 °C 12.43 MHz (2 ns step, +3 % step bias not corrected); ff/−40 °C/1.32 V 12.41 MHz; ss/125 °C/1.08 V **not run to completion** (simulated) | `../g1_top/sim/campaigns/RESULTS_20260925.md` §6 |
| Selected PVT trim screen on the R0.95 CPEX (5 tuples × 16 codes, 50 fF stand-in load) | passed: 80/80, every curve monotonic and brackets 10 MHz; ss/1.08 V/125 °C 5.834–10.448 MHz (simulated) | `reports/r095_newpex_pvt_20260924/README.md` |
| Full Cartesian PVT and mismatch population on the R0.95 CPEX; loaded re-enable; jitter | **not run** | same; `sim/qualification/fulltree_r095_load_20260924/README.md` |

**Schematic drawing: pending.** The committed schematic generator `schematic/gen_osc.py` and the
xschem sheets it writes still draw RA/RB as `rppd` 1 µm × 117 µm (the baseline); the chip carries
R0.95 (1 µm × 111.15 µm). The R0.95 netlist of record is the schematic-level source in the table
above. A generator update that draws R0.95 is in
progress and not yet committed; until it is, the tracked sheets are the 117 µm history, not the chip.

Everything below this section describes the **117 µm macro (9.919 MHz schematic, 8.994 MHz post-layout
at trim 8), which is not on the chip**. It is kept as history and as the base of R0.95.

Historical state of the 117 µm macro (not on the chip): **schematic frozen (revision 5, 2026-09-19: revision 4 plus an antenna diode on `vth`, no
change of any simulated number)**, simulated at schematic level (nominal, corners, temperature,
supply, trim, start-up); every corner of that screen reaches 10 MHz inside the trim range, but the
later extracted screen **fails** the 10 MHz bracket at ss/wcs/wcs, 1.08 V, 125 °C (9.9748 MHz at code 0,
see "Additional extracted trim screen"). **Laid out as the macro
`g1_osc` (166 × 137.6 µm), filled with the PDK filler, DRC clean with the full PDK rule set,
antenna deck clean, LVS clean against the frozen netlist; PEX (kpex 2.5D, capacitances) and
post-layout runs done: the layout parasitics lower the frequency by about 9 % at every code, the
trim reaches 10 MHz at the corners of that run (see "Post-layout"); not at ss/1.08 V/125 °C (above).**

## What it is

Internal ~10 MHz clock for the comparators, trip timers and scrubber (PLAN D4). A 1.2 V
ping-pong RC relaxation oscillator built only from `sg13_lv_*` MOS, `rppd` and `cmim`:

- Two timing branches. Each half period one `cmim` bank charges from `vdd` through an
  `rppd` resistor (1 µm × 117 µm, ≈30.5 kΩ) toward `vdd`; the other bank is held at 0 V by an
  NMOS switch.
- A continuous-time comparator per branch (5-transistor NMOS-input pair with PMOS mirror,
  ≈20 µA tail from a 35 kΩ `rppd` into an NMOS diode, two inverters) compares the ramp with
  `vdd`/2 from a 2 × 100 kΩ `rppd` divider with a 1 pF `cmim` hold capacitor.
- An SR latch (NOR3/NOR2) toggles on each crossing; its output is `osc_clk` (50 % duty by
  symmetry, so no divide-by-two is needed) and drives the two reset switches.
- Because the threshold is a fixed fraction of `vdd`, the half period is
  R·C·ln 2 + t<sub>delay</sub> and is first-order independent of the supply.
- 4-bit binary-weighted `cmim` trim on both banks (fixed 1.50 pF + 100 fF × code, NMOS switches
  to `vss`), code `trim[3:0]`, mid code 8 is the 10 MHz design point (9.92 MHz simulated, tt).
- `en` = 0 forces the latch to Q = 0, discharges both banks and holds `osc_clk` low; `en` = 1
  starts the oscillator (start-up simulated with a supply ramp).

Interface (all 1.2 V core domain): `en` and `trim0..3` come from the digital macro (`osc_trim[3:0]`
register, mid code 8 at power-up); `osc_clk` goes to the digital macro, which derives the comparator strobe (5 MHz) and the
timer clocks. Ports of `g1_osc`: `en trim0 trim1 trim2 trim3 osc_clk vdd vss`.

## Source

Nothing ported. `algofoogle/tt09-ring-osc2` (listed in `../../PLAN.md` as the ring-oscillator
reference) was not used: the plan's own notes require the clock to be RC-referenced rather than a
supply-referenced ring, so this block was drawn from scratch with PDK primitives only.

## Files

| Path | Content |
| --- | --- |
| `schematic/gen_osc.py` | generator of all xschem schematics and symbols (device sizes are here). Since 2026-09-25 it draws the chip-of-record R0.95 timing resistors (RA/RB l=111.15u) by default; `G1_OSC_VARIANT=baseline` draws the 117 µm block whose netlist is `sim/netlist/g1_osc.spice` (the two differ only in XRA/XRB; `../../review/schematics-readability-20260925/README.md`) |
| `../../../../flow/schematic/xsch_readable.py` | readable xschem sheet writer shared by the block generators (replaces the former `schematic/xsch.py`) |
| `schematic/g1_osc.sch`, `g1_osc_cmp.sch`, `g1_osc_cbank.sch`, `g1_osc_inv/nor2/nor3/nand2.sch` (+ `.sym`) | schematics |
| `schematic/netlist.sh` | xschem headless netlisting into `sim/netlist/` |
| `sim/netlist/g1_osc.spice` | netlist as simulated (`.subckt g1_osc`) |
| `sim/tb_osc.cir`, `sim/tb_osc_startup.cir` | testbench templates (`@@` fields substituted by the runner); revision 5 added the diode model library (`cornerDIO.lib dio_tt`) and `.option rshunt=1e12` |
| `sim/run_osc.sh` | runner: `quick`, `trim`, `corners`, `startup`, `extremes` (the two extreme corners at 27 °C with the trim codes nearest 10 MHz), `all`; variants go to `build/g1_osc/` |
| `sim/.spiceinit` | loads the PDK OSDI (PSP103) models |
| `sim/logs/*.log`, `sim/results_osc.txt` | evidence for every number below (revision 4; the last `quick` block is the revision-5 nominal re-run: 9.91864 MHz vs 9.91863) |
| `sim/logs_rev3/`, `sim/results_osc_rev3.txt` | revision 3 (1.43 pF fixed capacitor), superseded, kept for the design history |
| `mk_readme_table.py`, `fill_readme.py` | rebuild the results table and the corner verdict from `sim/results_osc.txt` |
| `layout/gen_osc_layout.py`, `layout/g1_layout_lib.py` | layout generator (KLayout + PDK PCells) and the drawing library (copy of `../g1_trip/layout/g1_layout_lib.py`) |
| `layout/g1_osc.gds`, `layout/g1_osc.lef`, `layout/g1_osc.vh` | macro views |
| `layout/g1_osc_lvs.cdl`, `layout/lvs_netlist.py` | LVS reference netlist derived from `sim/netlist/g1_osc.spice` and the script that derives it |
| `layout/run_checks.sh`, `layout/pex_input.py` | generator + fill + DRC + LVS + antenna runner; PEX input preparation |
| `layout/fill_macro.sh`, `layout/fill_macro.py` | PDK filler on the macro (temporary EdgeSeal ring trick, see "Fill") |
| `reports/drc/`, `reports/lvs/`, `reports/antenna/`, `reports/fill/`, `reports/lef/`, `reports/pex/` | DRC, LVS, antenna, filler, LEF-load and kpex logs of the final (filled) GDS |
| `sim/postlayout/` | kpex netlist conversion (`make_pex_netlist.py`), post-layout decks, runner, logs and results |

## Simulated

Commands (from the repository root, inside the pinned container of `../../PLAN.md` section 2,
ngspice 46, xschem 3.4.8RC, PDK commit `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`):

```
G1_WORKDIR=designs/g1-guardian/blocks/g1_osc/schematic flow/run.sh bash netlist.sh
G1_WORKDIR=designs/g1-guardian/blocks/g1_osc/sim       flow/run.sh bash run_osc.sh all
```

Model libraries, exactly as in the decks (the `/foss/pdks` path is the container's PDK mount):

```
.lib /foss/pdks/ihp-sg13g2/libs.tech/ngspice/models/cornerMOSlv.lib  mos_tt | mos_ff | mos_ss
.lib /foss/pdks/ihp-sg13g2/libs.tech/ngspice/models/cornerRES.lib    res_typ | res_bcs | res_wcs
.lib /foss/pdks/ihp-sg13g2/libs.tech/ngspice/models/cornerCAP.lib    cap_typ | cap_bcs | cap_wcs
```

Temperatures: −40, 27, 85, 125, 150, 175 °C (`.temp`). The PDK models are characterised to
125 °C; 150 and 175 °C results are **model extrapolated**. Supplies 1.08 / 1.2 / 1.32 V.
Transient `tran 0.2n 2.6u`, frequency from ten periods (rising edges 12 to 22 at `vdd`/2),
duty from the falling edge, current averaged over 1.5–2.5 µs, 50 fF load on `osc_clk`.
Start-up: `vdd` ramp 0 → 1.2 V in 1 µs with `en` tied to `vdd`, time of the first `osc_clk`
rising edge.

### Results (simulated)

| MOS | RES | CAP | VDD (V) | T (°C) | trim code | f (MHz) | dev. from 10 MHz | duty (%) | I<sub>DD</sub> (µA) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| tt | typ | typ | 1.2 | 27 | 8 | 9.919 | -0.8 % | 50.0 | 107 |
| ff | bcs | bcs | 1.2 | 27 | 8 | 12.635 | +26.4 % | 50.0 | 126 |
| ff | bcs | bcs | 1.2 | 27 | 15 | 9.819 | -1.8 % | 49.9 | 126 |
| ff | bcs | bcs | 1.2 | 27 | 14 | 10.129 | +1.3 % | 50.0 | 126 |
| ss | wcs | wcs | 1.2 | 27 | 8 | 7.941 | -20.6 % | 50.0 | 91 |
| ss | wcs | wcs | 1.2 | 27 | 4 | 9.531 | -4.7 % | 50.0 | 92 |
| ss | wcs | wcs | 1.2 | 27 | 3 | 10.048 | +0.5 % | 49.9 | 92 |
| ss | wcs | wcs | 1.2 | 27 | 0 | 11.907 | +19.1 % | 49.9 | 92 |
| tt | typ | typ | 1.2 | 27 | 0 | 14.874 | +48.7 % | 50.0 | 108 |
| tt | typ | typ | 1.2 | 27 | 4 | 11.900 | +19.0 % | 50.0 | 107 |
| tt | typ | typ | 1.2 | 27 | 12 | 8.515 | -14.9 % | 50.0 | 107 |
| tt | typ | typ | 1.2 | 27 | 15 | 7.704 | -23.0 % | 50.0 | 106 |
| tt | typ | typ | 1.2 | -40 | 8 | 9.992 | -0.1 % | 50.0 | 106 |
| tt | typ | typ | 1.2 | 85 | 8 | 9.866 | -1.3 % | 50.0 | 108 |
| tt | typ | typ | 1.2 | 125 | 8 | 9.814 | -1.9 % | 50.0 | 109 |
| tt | typ | typ | 1.2 | 150 (model extrapolated) | 8 | 9.778 | -2.2 % | 50.0 | 109 |
| tt | typ | typ | 1.2 | 175 (model extrapolated) | 8 | 9.732 | -2.7 % | 50.0 | 110 |
| ff | bcs | bcs | 1.2 | -40 | 8 | 12.706 | +27.1 % | 50.0 | 125 |
| ss | wcs | wcs | 1.2 | -40 | 8 | 7.996 | -20.0 % | 50.0 | 90 |
| tt | bcs | wcs | 1.2 | -40 | 8 | 10.410 | +4.1 % | 50.0 | 120 |
| tt | wcs | bcs | 1.2 | -40 | 8 | 9.766 | -2.3 % | 50.0 | 94 |
| tt | bcs | wcs | 1.2 | 27 | 8 | 10.329 | +3.3 % | 50.0 | 121 |
| tt | wcs | bcs | 1.2 | 27 | 8 | 9.710 | -2.9 % | 49.9 | 95 |
| ff | bcs | bcs | 1.2 | 175 (model extrapolated) | 8 | 12.345 | +23.5 % | 50.1 | 132 |
| ss | wcs | wcs | 1.2 | 175 (model extrapolated) | 8 | 7.799 | -22.0 % | 50.0 | 94 |
| tt | bcs | wcs | 1.2 | 175 (model extrapolated) | 8 | 10.127 | +1.3 % | 50.0 | 124 |
| tt | wcs | bcs | 1.2 | 175 (model extrapolated) | 8 | 9.532 | -4.7 % | 50.0 | 99 |
| tt | typ | typ | 1.08 | 27 | 8 | 9.805 | -1.9 % | 49.9 | 94 |
| tt | typ | typ | 1.32 | 27 | 8 | 10.018 | +0.2 % | 50.0 | 120 |
| ss | wcs | wcs | 1.08 | 175 (model extrapolated) | 8 | 7.704 | -23.0 % | 49.9 | 82 |
| ff | bcs | bcs | 1.32 | -40 | 8 | 12.810 | +28.1 % | 49.9 | 141 |

Mid-code (8) at 1.2 V over 18 corner/temperature points: min 7.799 MHz (mos_ss/res_wcs/cap_wcs 175 °C), max 12.706 MHz (mos_ff/res_bcs/cap_bcs -40 °C): -22.0 % / +27.1 % from 10 MHz.
Supply: 9.805 MHz at 1.08 V, 9.919 at 1.2 V, 10.018 at 1.32 V -> 8.9 %/V (2.1 % over +/-10 %).
Trim ratio relative to mid code: x0.777 (code 15) to x1.500 (code 0). Best reachable frequency per corner (f_mid x ratio, nearest to 10 MHz): all corners reach 10 MHz
Trim (tt, 27 °C): code 0 -> 14.874 MHz, code 4 -> 11.900 MHz, code 8 -> 9.919 MHz, code 12 -> 8.515 MHz, code 15 -> 7.704 MHz
Start-up osc_startup_mos_tt_res_typ_cap_typ_27C: first osc_clk edge at 0.50 µs (VDD reaches 1.08 V at 0.90 µs), f at end 9.923 MHz
Start-up osc_startup_mos_ss_res_wcs_cap_wcs_-40C: first osc_clk edge at 0.66 µs (VDD reaches 1.08 V at 0.90 µs), f at end 7.996 MHz
Start-up osc_startup_mos_ss_res_wcs_cap_wcs_175C: first osc_clk edge at 0.54 µs (VDD reaches 1.08 V at 0.90 µs), f at end 7.799 MHz

## Design history (same day)

1. First netlist: R = 122 µm, no capacitor on the threshold node; 9.61 MHz at mid code (log
   not kept, superseded).
2. R = 117 µm, trim 60 fF LSB (±15 %): the comparators' switching disturbed the `vdd`/2
   divider node by up to 65 mV (`vth` min 0.536 V), so a 1 pF `cmim` was added there; the
   `mos_ff/res_bcs/cap_bcs` corner then read 13.0 MHz (+30 %), beyond the trim reach.
3. Trim LSB raised to 100 fF with the fixed capacitor lowered to keep mid code at 10 MHz
   (range about +55 % / −25 % in frequency). The `mos_ff/res_bcs/cap_bcs` corner trimmed only to
   10.04–10.17 MHz (code 15), recorded as a marginal fail; its results are kept in
   `sim/results_osc_rev3.txt` and `sim/logs_rev3/`.
4. (2026-09-19, **frozen**) Fixed capacitor 1.43 → 1.50 pF (`cmim` 30.9 → 31.65 µm square, +5 %);
   mid code moves from 10.23 to 9.92 MHz and code 15 reaches 9.82 MHz at the fast corner, code 3
   reaches 10.05 MHz at the slow corner. All numbers above are from this revision
   (`sim/results_osc.txt`, `sim/logs/`).
5. (2026-09-19, after the chip-level antenna check, **frozen**) Antenna diode `dpantenna`
   0.78 × 0.78 µm (p+ in n-well, anode `vth`, cathode `vdd`) on the threshold node: `vth` carries
   only the two comparator gates M2 (2.4 µm²), poly resistors and the 26 µm `cmim` top plate, so
   the PDK antenna deck flagged both gates (`Ant.b`, cumulative metal to gate area ratio 283 > 200
   without a diode). Reverse-biased at vdd/2, fA leakage (model `dparea`), ≈ 0.5 fF. The n+/substrate
   `dantenna` was tried first: its ngspice model (`darea`, series resistance 219 kΩ together with a
   700 ns transit time) stalls the transient of this circuit (the start-up deck never passes
   0.19 µs), the p+ model (`tt` = 1 ps) runs. The decks gained the diode library and
   `.option rshunt=1e12` (1 TΩ per node; the rppd body node `sub!` is floating). Nominal re-run:
   9.91864 MHz, 50.008 % duty, 106.9 µA against 9.91863 / 50.008 / 106.9 for revision 4 — nothing
   else was re-simulated at schematic level; the post-layout table below is from this revision.

## Laid out

Macro `g1_osc`, **166 × 137.6 µm** (`layout/g1_osc.gds`, LEF `layout/g1_osc.lef`), one flat cell
generated by `layout/gen_osc_layout.py` from the PDK PCells (`nmos`, `pmos`, `rppd`, `cmim`,
library `SG13_dev`) with the drawing library of G1_TRIP. Run from the repository root inside the
pinned container:

```
G1_WORKDIR=designs/g1-guardian/blocks/g1_osc/layout flow/run.sh bash run_checks.sh all   # gen + fill + DRC + LVS + antenna
```

The generator writes the bare macro to `build/`; `layout/fill_macro.sh` runs the PDK filler on it and
the filled GDS `layout/g1_osc.gds` is the macro of record (with a `prBoundary` 189/4).

- **Transistor row block** (82 × 20 µm, bottom centre): all 51 transistors in a standard-cell-like
  arrangement produced by `RowLayout` in the library — an NMOS row with the sources on a Metal1
  `vss` rail, a channel of 16 shared Metal2 tracks (0.5 µm pitch) and a PMOS row in one n-well with
  the `vdd` rail and its n+ tie on top; every other terminal is a Metal1 stub with a Via1 onto its
  net's track, gates are strapped away from the channel (NMOS) or towards it (PMOS) and contacted
  beside the Activ. PMOS x positions are chosen so that their stubs keep 0.42 µm from every NMOS
  stub of another net (the gate tab goes to the left if the right side conflicts). Device order:
  comparator A, comparator B (5-T pairs 4/0.3, mirrors 2/0.3, tails 2/0.5, two inverters each),
  bias diode, the eight trim switches and the two reset switches (4/0.13), then the latch logic
  (inverter, NOR3, NOR2, NAND2, buffers). Nets that leave the block (`va vb vth vbn b0..3 bb0..3
  en trim0..3 osc_clk`) end in a Via2 at the track end and go up on Metal3.
- **Resistor block** (left, 37 × 70 µm): `rppd` 1 µm wide segments side by side at 1.85 µm pitch
  (pSD/SalBlock/EXTBlock separate, `Sal.d` to the neighbours' heads), a dummy segment at each end:
  RA and RB as 2 × 58.5 µm interleaved A B B A, RT1 and RT2 as 6 × 64.05 µm serpentines with the
  `vth` node at the shared top head, RBIAS as 2 × 67.15 µm; all `vdd` ends at the top on a Metal2
  collector to the VDD bar. The LVS combines the series segments back to the schematic's single
  resistors (`reports/lvs/g1_osc_extracted.cir`: 117, 117, 384.3, 384.3 and 134.3 µm with the
  schematic's terminals; every internal joint is a two-terminal node, so nothing is merged through
  a node that carries a pin or a device).
- **Capacitors** (three columns above the tracks): `cmim` PCells with the trim capacitors at the
  bottom of each column (short bottom-plate wires), column 1 = CT2_A, CT3_A, CF_A (31.65 µm),
  column 2 = CT2_B, CT3_B, CF_B, column 3 = CT0_A, CT1_A, CT0_B, CT1_B, CTH (26 µm). Top plates
  leave on TopMetal1 tabs to the left (TopVia1/Via4/Via3 stack to Metal3, one Metal3 vertical per
  net per column), bottom plates on Metal5 tabs to the right (Via4/Via3 to Metal3); a **Metal4
  track channel** (19 tracks, 1.0 µm pitch, the timing nodes `va`/`vb` between static nets) links
  the capacitor pads, the row-block ports, the resistor heads and the pins.
- **Antenna diode** (revision 5): the `dpantenna` PCell sits just above the PMOS row, its n-well
  overlapping the row block's n-well (tied to `vdd` by the row's n+ bar), on the Metal3 vertical of
  the row block's `vth` port (Metal1 enclosure and a 0.40 × 0.72 µm Metal2 pad added for `M1.c1` /
  `Mn.d`). The antenna deck then passes (`reports/antenna/`, 0 violations; before: 4 `Ant.b`
  markers on the two `vth` gates at (50.44, 10–14) and (58.8, 10–14) µm). The extra Metal3 raises
  the `vth` parasitic from 26 to 34 fF (1 pF hold capacitor on the node).
- **Fill**: the chip-level filler does not fill inside placed macros, so `layout/fill_macro.sh`
  runs the PDK filler (`libs.tech/klayout/tech/scripts/filler.py`, `sg13g2_filler_{ActGatP,Metal}.lym`)
  on the macro. The PDK fill macros fill the *holes of the EdgeSeal layer*, so the script adds a
  temporary EdgeSeal ring whose hole is the macro shrunk by 3 µm, fills, and removes the ring;
  TopMetal1/2 fill is not placed (the chip PDN's TopMetal stripes cross the macro; the chip filler
  fills TopMetal after routing). No-fill shapes (`<layer>/23`, 3 µm margin, honoured by the PDK
  filler and by the chip filler) keep the fill away from the resistor block (Activ, GatPoly,
  Metal1–3), the row block (Activ … Metal3), the capacitor columns with their tabs (Metal4/5,
  TopMetal), the Metal4 track channel (Metal2–5, TopMetal) and the diode (all layers). Fill
  (datatype 22, `reports/fill/filler.log`): Activ 28 %, GatPoly 17 %, Metal1 29 %, Metal2 24 %,
  Metal3 19 %, Metal4 10.5 %, Metal5 10.5 % of the macro area (drawn: Metal1 1.9, Metal2 1.1,
  Metal3 4.4, Metal4 1.5, Metal5 23.4, TopMetal1 20.3 %). The fill is floating metal: the LVS deck
  does not read datatype 22 (LVS unchanged), kpex maps drawing and pin datatypes only (fill is
  **not in the post-layout netlist**; `layout/pex_input.py` strips it), the full DRC rule set is
  clean with it.
- **Pins** (`layout/g1_osc.lef`, checked with OpenROAD, `reports/lef/lef_check.log`): Metal3
  `VSS` bar along the south edge (y 0 … 2 µm) and `VDD` bar along the north edge (135.6 … 137.6),
  full width; `en` and `trim[3:0]` as 1.5 × 0.3 µm Metal3 stubs on the west edge (y 29.65, 32.65,
  35.65, 37.65, 39.65), `osc_clk` on the east edge (y 40.65 µm). A p+ guard ring (VSS) runs
  inside the boundary. Obstructions: Metal1/2 full, Metal3 inset by the bars and pin stubs,
  **Metal4/Metal5 the interior rectangle (3, 3) … (163, 134.57)** — 3 µm inside every edge, the
  fill window, so the 3 µm above the `VDD`/`VSS` bars stay free of Metal4/Metal5 shapes, fill and
  obstructions for the chip PDN's straps (the first LEF, 2026-09-19 morning, obstructed Metal4/5
  over the whole macro and the chip-level PDN dry run `../g1_padring/reports/dryrun-1350/` reported
  pdngen PDN-0006; an intermediate LEF listed only the real Metal4/5 shapes, superseded by the
  fill) — and TopMetal1 over the capacitor plates (from the shapes). 16 obstructions, 8 pins. Black
  box `layout/g1_osc.vh`.
- The LVS netlist `layout/g1_osc_lvs.cdl` is derived from `sim/netlist/g1_osc.spice` by
  `layout/lvs_netlist.py` (xschem's `X`-prefixed device instances → `M`/`R`/`C` device lines, rppd
  body `sub!` → `vss`, ports renamed `vdd`→`VDD`, `vss`→`VSS`, `trim<i>`→`trim[<i>]`); the
  circuit is unchanged.

## Checks

| Check | Status | Evidence / criterion |
| --- | --- | --- |
| Schematic simulation, nominal | passed (9.92 MHz at code 8, tt 1.2 V 27 °C) | `sim/logs/osc_mos_tt_res_typ_cap_typ_1.2V_27C_code8.log`: see table |
| Corners / temperature / supply | passed; mid trim, 1.2 V: 7.80 to 12.71 MHz | criterion: within ±20 % of 10 MHz at mid trim, or trimmable to 10 MHz with `trim[3:0]` |
| Start-up (supply ramp) | passed | `sim/logs/osc_startup_*.log` |
| Mismatch MC | not run | duty-cycle asymmetry from bank/comparator mismatch not quantified |
| DRC, `run_drc.py --run_mode=deep --no_density`, full rule set incl. the extra (`sg13g2_maximal`) rules, filled GDS with the diode | **passed, 0 violations** | `reports/drc/drc_run_2026_09_19_12_25_16.log`, `reports/drc/g1_osc_g1_osc_main.log`, `reports/drc/g1_osc_g1_osc_sg13g2_maximal.log` |
| LVS, `run_lvs.py --run_mode=deep` vs `layout/g1_osc_lvs.cdl` (revision 5: 51 MOS, 5 combined resistors, 11 capacitors, 1 `dpantenna`) | **passed** | `reports/lvs/lvs_run_2026_09_19_12_25_50.log`, `reports/lvs/g1_osc.log`, `reports/lvs/g1_osc_extracted.cir` |
| Antenna, `run_drc.py --antenna_only` (was: 4 `Ant.b` markers on the `vth` gates in the chip dry run) | **passed, 0 violations** | `reports/antenna/drc_run_2026_09_19_12_26_04.log`, `reports/antenna/g1_osc_g1_osc_antenna.log` |
| Fill (PDK filler, Activ/GatPoly/Metal1–5 with no-fill over the matched structures; DRC/LVS on the filled GDS) | done | `reports/fill/filler.log`, the DRC/LVS rows above |
| LEF loads in OpenROAD (8 pins, 16 obstructions, none of Metal4/5/TopMetal1 over the supply bars) | passed | `reports/lef/lef_check.log` |
| PEX, kpex 2.5D `--mode CC` (capacitances) | run | `reports/pex/kpex_cc.log`, `reports/pex/g1_osc_k25d_pex_netlist.spice` |
| Post-layout: nominal, trim, extreme corners at 27 °C, supply, temperature, start-up | passed (−9 % at mid code; 10 MHz reachable at every corner, slow corner at code 0) | `sim/postlayout/results_postlayout.txt`, `sim/postlayout/logs/` |
| Density | not run at block level (the PDK density rules are chip-global; the macro's own fill is listed above) | — |

## Post-layout (kpex 2.5D, capacitances)

PEX: `kpex 0.3.12` (KLayout-PEX), engine `--2.5D --mode CC`, on the PEX input
`layout/pex_input.py` makes from `layout/g1_osc.gds` (the flattened cell without the `cmim` layers
MIM/Vmim/TopVia1/TopMetal1/Metal5/Via4, which kpex's SG13G2 technology cannot model — the engine
stops with `KeyError: '<TODO>'` on any MIM shape — plus labels on the eight trim-capacitor
bottom-plate nets so that kpex names them). Command, from the repository root:

```
G1_WORKDIR=designs/g1-guardian/blocks/g1_osc/layout flow/run.sh klayout -b -r pex_input.py -rd gds=g1_osc.gds -rd out=/work/build/g1_osc/pex/g1_osc_pexin.gds
G1_WORKDIR=build/g1_osc/pex flow/run.sh kpex --pdk ihp_sg13g2 --gds /work/build/g1_osc/pex/g1_osc_pexin.gds --cell g1_osc \
    --schematic /work/designs/g1-guardian/blocks/g1_osc/layout/g1_osc_lvs.cdl --2.5D --mode CC --out_dir /work/build/g1_osc/pex/cc
```

(`reports/pex/kpex_cc.log`; the internal LVS that kpex runs with `--no_simplify` reports a
mismatch because it does not combine the resistor segments — it is not the sign-off LVS, which is
`reports/lvs/`.) `sim/postlayout/make_pex_netlist.py osc` turns `reports/pex/g1_osc_k25d_pex_netlist.spice`
(51 MOS, 18 resistor segments, 608 parasitic capacitors) into `sim/postlayout/g1_osc_pex.spice`
with the schematic's port names and the eleven `cmim` re-inserted as ideal devices (see its
docstring; revision 5 adds the extracted `dpantenna` as an `XD` instance of the PDK model).
Largest extracted parasitics (sums over `sim/postlayout/g1_osc_pex.spice`): `va` 42 fF and `vb`
42 fF (2.8 % of the 1.5 pF fixed capacitor; 11 fF each to `vss`/substrate, 3.2 fF between `va` and
`vb`), `vth` 33 fF (15 fF to `vss`; 26 fF before the diode's Metal3 vertical), `en` 34 fF, the
trim-capacitor bottom-plate nets 10–25 fF each (in series with the trim capacitor when its switch
is off), the comparator and latch nodes 15–27 fF each (the Metal2 tracks of the row block).

`sim/postlayout/run_postlayout.sh` runs `tb_osc_pex.cir` / `tb_osc_startup_pex.cir` (the schematic
decks with the `.include` swapped; same measurements) and `compare.py` writes the table:

| run (MOS / RES / CAP / VDD / T / code) | schematic f (MHz) | post-layout f (MHz) | delta | post-layout duty (%) | I<sub>DD</sub> (µA) |
| --- | --- | --- | --- | --- | --- |
| tt / typ / typ / 1.2V / 27C / code0 | 14.874 | 12.927 | -13.1 % | 49.3 | 113 |
| tt / typ / typ / 1.2V / 27C / code8 | 9.919 | 8.994 | -9.3 % | 49.5 | 110 |
| tt / typ / typ / 1.2V / 27C / code15 | 7.704 | 7.174 | -6.9 % | 49.7 | 109 |
| ff / bcs / bcs / 1.2V / 27C / code8 | 12.635 | 11.421 | -9.6 % | 49.5 | 131 |
| ff / bcs / bcs / 1.2V / 27C / code15 | 9.819 | 9.130 | -7.0 % | 49.7 | 129 |
| ff / bcs / bcs / 1.2V / 27C / code14 | 10.129 | 9.369 | -7.5 % | 49.6 | 129 |
| ff / bcs / bcs / 1.2V / 27C / code12 | not run | 9.945 | | 49.6 | 130 |
| ff / bcs / bcs / 1.2V / 27C / code11 | not run | 10.342 | | 49.6 | 130 |
| ss / wcs / wcs / 1.2V / 27C / code8 | 7.941 | 7.201 | -9.3 % | 49.5 | 94 |
| ss / wcs / wcs / 1.2V / 27C / code3 | 10.048 | 8.979 | -10.6 % | 49.5 | 95 |
| ss / wcs / wcs / 1.2V / 27C / code4 | 9.531 | 8.496 | -10.9 % | 49.4 | 95 |
| ss / wcs / wcs / 1.2V / 27C / code0 | 11.907 | 10.370 | -12.9 % | 49.3 | 96 |
| ss / wcs / wcs / 1.2V / 27C / code1 | not run | 9.857 | | 49.4 | 96 |
| tt / typ / typ / 1.08V / 27C / code8 | 9.805 | 8.785 | -10.4 % | 49.5 | 96 |
| tt / typ / typ / 1.32V / 27C / code8 | 10.018 | 9.150 | -8.7 % | 49.6 | 124 |
| tt / typ / typ / 1.2V / -40C / code8 | 9.992 | 9.041 | -9.5 % | 49.5 | 109 |
| tt / typ / typ / 1.2V / 125C / code8 | 9.814 | 8.907 | -9.2 % | 49.6 | 112 |
| startup / tt / typ / typ / 27C | first edge 0.50 µs, 9.923 MHz | first edge 0.50 µs, 8.995 MHz | -9.4 % | | |

Reading: the layout costs **9–13 % of frequency at every corner** (more at low codes, where the
fixed capacitor's share is smaller): about 3 % from the 42 fF on each timing node, the rest from the
larger comparator/latch delay (the ramp overshoots the threshold by 38 mV instead of 15 mV, i.e.
≈ 4 ns more delay per half period, from the parasitics on the comparator's internal nodes and the
trim-capacitor bottom-plate nets). Mid code sits at 9.0 MHz (−10 %), inside the ±20 % untrimmed
band the digital macro assumes (`../g1_trip/INTERFACE.md`); the trim reaches 10 MHz at every
corner, with less margin at the slow corner than the schematic had: mos_ss/res_wcs/cap_wcs needs
**code 0 (10.37 MHz)** instead of code 3, mos_ff/res_bcs/cap_bcs code 11–12 (10.34 / 9.94 MHz)
instead of 14–15. Start-up and duty cycle (49.3–49.7 %) are unchanged. Supply sensitivity
8.8 → 9.15 MHz over 1.08–1.32 V (+4 %) is slightly larger than the schematic's +2 %. **Antenna
diode (revision 5):** the table is the re-run with the `dpantenna` on `vth` (and the fill, which is
not extracted); against the revision-4 post-layout run of the morning (same layout without the
diode; its raw results file was overwritten by this run, the table it produced stood in this
README) no frequency changed by more than 0.01 %: 12.927 / 8.994 / 7.174 MHz at codes 0 / 8 / 15
(tt), 10.370 MHz at the slow corner's code 0, 10.342 MHz at the fast corner's code 11, start-up
8.994 → 8.995 MHz, as expected for 0.5 fF and fA-class leakage on a 1 pF DC node.

## Additional extracted trim screen (2026-09-21)

The [80-case screen](sim/qualification/README.md) completes all 16 codes at
five explicit PVT tuples. All runs complete and code transfer is monotonic,
but strict 10 MHz bracketing **fails** at ss/wcs/wcs, 1.08 V, 125 °C:
maximum frequency is 9.974814 MHz. The earlier “every corner” statement
above applies only to the previously listed tests; it does not establish
combined low-voltage/hot coverage. Across this new screen all-code frequency
is 5.560405–16.776615 MHz, and default code 8 reaches as low as 6.963740 MHz.
These simulated ranges use the 50 fF stand-in, not final receiver loading.
Mismatch, real load, slow startup/re-enable and jitter remain incomplete.

## Unverified

- Period jitter and phase noise (no transient-noise run); comparator noise near the crossing.
- Kickback of the oscillator's own switching into the 1.2 V rail and into neighbouring blocks
  (the reset switches dump ~2.5 pF × 0.6 V twice per period); local decoupling is assumed.
- Duty-cycle and period asymmetry from mismatch between the two banks/comparators (no MC); the
  layout is not symmetric between the A and B branches (one row block, separate capacitor
  columns), so the post-layout duty cycle (49.3 … 49.7 %) is the systematic part only.
- Post-layout parasitics are capacitances only (kpex 2.5D `--mode CC`): wiring resistance is not
  extracted (kpex 0.3.12 RC mode leaves the devices off the resistor trees, see the G1_BGR README);
  the timing nodes see at most ~120 µm of Metal4 (0.103 Ω/sq → 50 Ω) and 20 vias (20 Ω each), i.e.
  < 0.5 kΩ against the 30.5 kΩ charging resistor, so the omission is below 2 % of the period.
- The MIM capacitors were removed from the PEX input (kpex has no model for the MIM layer) and
  re-inserted as ideal `cap_cmim` devices: the parasitics of the capacitor plates to the wiring
  underneath them and to each other are not in the post-layout netlist.
- Behaviour below −40 °C and above 125 °C (model extrapolated, see above).
- The `cmim` and `rppd` temperature coefficients as modelled are what set the temperature
  drift below; not confirmed on silicon.
- The fill (floating Activ/GatPoly/Metal1–5 squares, kept 3 µm from the resistors, the row block,
  the track channel and the capacitors) is not in the post-layout netlist: kpex does not read the
  fill datatype. Its coupling to the timing nodes is bounded by the no-fill margins (no Metal2–5
  fill within 1 µm of the track channel, no Metal4/5 within 3 µm of the capacitor plates).
- Density rules (chip level, after the chip filler). For the chip-level check: the PDK density deck
  takes any `prBoundary` **189/0** shape in the GDS as the chip area (the dry run's
  `klayout-density.log`: `Using prBoundary (189/0) for chip area: 54340 um^2`, the union of the
  `g1_sense`/`g1_gate` 189/0 boundaries), which produced the *maximum*-density markers over that
  column; this macro carries its boundary on 189/4 only.
- The antenna diode's leakage at 150–175 °C (model characterised −40 … 125 °C): the `dparea`
  model gives fA at 27 °C; a nA at 175 °C would move `vth` by 50 µV (50 kΩ divider), 0.01 % of the
  period.

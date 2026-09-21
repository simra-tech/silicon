# G1_PADRING — dropping macros into the ring

How a hardened block (analog or digital) replaces part of `g1_core_placeholder`
inside the 1200 × 1200 µm ring. Geometry and PDN facts are from
`flow/config.yaml` and the run evidence in `README.md`.

## Core window and what is already there

| Item | Value |
| --- | --- |
| `CORE_AREA` | [364, 364, 986, 986] µm = 622 × 622 µm on the 1350 µm die (OpenROAD snaps the origin to the site grid, 366.24/366.66); 1200 µm frame: [364, 836]² = 472 × 472 µm |
| Core power ring | VDD/VSS, TopMetal1 vertical + TopMetal2 horizontal, 2 × 15 µm, 5 µm spacing, 4.5 µm outside the core; connected to the `sg13g2_IOPadVdd/Vss` rails by `-connect_to_pads` |
| Core PDN stripes (PDK defaults) | TopMetal1 vertical and TopMetal2 horizontal, 2.2 µm wide, 75.6 µm pitch, 13.6 µm offset from the core edge (first vertical stripe at x ≈ 377.6, then every 75.6 µm) |
| IOVDD/IOVSS ring (dry run, `flow/pdn_cfg_g1.tcl`) | second ring 5 µm wide, 2 µm apart, on TopMetal1/TopMetal2 just inside the core boundary, connected to the `sg13g2_IOPadIOVdd/IOVss` pad rails |
| Standard-cell rails | Metal1, 0.44 µm, follow-pins; no tap cells (`FP_TAPCELL_DIST 0`) |
| IO-cell inner edge | 320.5 µm from the die edge on all sides; the 43.5 µm between it and the core hold the core ring |
| Pad-to-core nets | `p2c` / `c2p` of the digital pads, `padbare` of the eight measurement pads, `padres` of TRIP_SET and VREF — all end at `i_core` ports (`rtl/g1_chip_top.sv`). The pad pins sit on the core-side edge of each IO cell (Metal2/Metal3, y = 179–180 of the cell) |

Everything inside the window is placeable; the placeholder logic (one flop,
three gates) is removed when a macro takes over its ports.

## Steps for any macro

1. **Views.** From the block's LibreLane `final/`: `gds/`, `lef/`, `nl/`,
   `pnl/`, `spef/nom/`, `lib/<corner>/`. A KLayout-drawn analog block needs a
   LEF (pins on the metals you want the router to hit, `OBS` on everything
   else, `CLASS BLOCK`), a Verilog black box (`.vh`) and, if it has to be
   timed, a liberty file; otherwise the flow treats it as a timing black box
   (list it in `IGNORE_DISCONNECTED_MODULES` only if it has pins the flow
   should not check).
2. **RTL.** Instantiate it in `rtl/g1_core_placeholder.sv` (or a module of the
   same name and port list, as `rtl/g1_core_dryrun.sv` does) and connect the
   `i_core` ports. Power pins go under `` `ifdef USE_POWER_PINS ``.
3. **`flow/config.yaml`.** Add a `MACROS:` entry:

   ```yaml
   MACROS:
     <cell>:
       gds: [dir::<path>.gds]
       lef: [dir::<path>.lef]
       nl:  [dir::<path>.nl.v]        # or vh: [dir::<path>.vh] for a black box
       pnl: [dir::<path>.pnl.v]
       spef: {nom_*: dir::<path>.nom.spef}
       lib:
         nom_typ_1p20V_25C:   dir::<path>__nom_typ_1p20V_25C.lib
         nom_fast_1p32V_m40C: dir::<path>__nom_fast_1p32V_m40C.lib
         nom_slow_1p08V_125C: dir::<path>__nom_slow_1p08V_125C.lib
       instances:
         i_core.<inst>:
           location: [x, y]           # lower-left, µm, inside CORE_AREA
           orientation: N
   ```

   `EXTRA_LEFS`/`EXTRA_GDS` is the alternative for cells that are placed by
   the tool rather than at fixed coordinates (bondpads, logos); macros with a
   fixed location use `MACROS`. Every macro must be listed in
   `IGNORE_DISCONNECTED_MODULES` when it has pins the placeholder leaves open
   (monitor outputs), otherwise `Checker.DisconnectedPins` stops the flow.
4. **Placement.** Inside [364, 836]², clear of other macros, with room for the
   halo (`PDN_HORIZONTAL_HALO`/`PDN_VERTICAL_HALO`, default 10 µm) and for
   standard-cell rows around it if the placeholder/glue logic remains. Put
   digital macros where their pins face the pads they serve (north edge pins
   of `g1_digital` → SCLK/SDI/SDO/TEMP_OUT on the north side). Analog macros
   that carry `padbare` nets go next to their pads (west side: G_SHARED,
   D_STD, D_ELT, HBT_*; east side: SENSE_P/N) so the bare nets stay short;
   give those nets an NDR (`NON_DEFAULT_RULES` + `DRT_ASSIGN_NDR`, template
   pattern) and keep them in `RSZ_DONT_TOUCH_RX` (already set for all analog
   nets).
5. **Power.**
   - **1.2 V macro on VDD/VSS** (e.g. `g1_digital`): pins on TopMetal1/TopMetal2
     stripes; `PDN_MACRO_CONNECTIONS: ["i_core.<inst> VDD VSS VDD VSS"]`; the
     default `macro` grid of the PDN script connects the chip stripes to the
     macro pins where they cross (TopMetal1 ↔ TopMetal2 vias). If the macro's
     pins are on Metal5 or below, add a `define_pdn_grid -macro -instances …` +
     `add_pdn_connect` pair in a custom `PDN_CFG` (template `pdn_cfg.tcl`,
     `sram_NS` block) — LibreLane's stock `pdn_cfg.tcl` is what runs now.
   - **3.3 V macro on IOVDD/IOVSS** (sense, trip, bandgap, gate driver): IOVDD
     and IOVSS are not chip PDN nets today (`VDD_NETS: [VDD]`, `GND_NETS: [VSS]`);
     they exist only as top-level ports tied to the pad rails by abutment. To
     power a macro from them: add them as secondary nets
     (`VDD_NETS: [VDD, IOVDD]`, `GND_NETS: [VSS, IOVSS]`), bind the macro pins
     with `PDN_MACRO_CONNECTIONS: ["i_core.<inst> IOVDD IOVSS <vddpin> <vsspin>"]`,
     and give the nets metal: either a second core ring
     (`add_pdn_ring -nets {IOVDD IOVSS} -connect_to_pads` in a custom
     `PDN_CFG`, inside the VDD/VSS ring — the 43.5 µm gap has room for one
     more pair at 5 µm width) or explicit straps from the `sg13g2_IOPadIOVdd/
     IOVss` cells' Metal3–TopMetal2 rails (which run along the whole ring) to
     the macro. Power nets are not routed by the detailed router, so one of
     the two is required. The macro must also expose its `vdd`/`vss` (1.2 V)
     pins if it contains level shifters.
   - Level shifting 3.3 V ↔ 1.2 V between analog and digital macros is the
     analog wrapper's job (`PLAN.md` D8); the ring provides nothing for it.
6. **Checks after the run.** Same as `README.md`: KLayout DRC (hard rules),
   density after fill, KLayout antenna, KLayout LVS with the CDL of the macro
   appended to the schematic netlist (`flow/lvs/pnl2cdl.py <pnl> <out> <cdl…>`).

## Floorplan (1350 µm frame, all macros of record)

Core window [364, 986]² (622 × 622 µm). Pads on the 1350 µm frame start at
355 + 112 n µm along each side (n = 0…5): east side, bottom to top, VDD (7),
SENSE_P (8, y = 467–547), SENSE_N (9, 579–659), GATE (10, 691), FAULT_N (11,
803), EN (12, 915); north side, left to right, TRIP_SET (13, x = 355), SCLK
(14, 467), SDI (15, 579), SDO (16, 691), TEMP_OUT (17, 803), VREF (18, 915);
west side the six device pins; south side supplies only. Rules used: the
sense amplifier's `sense_p/n` pins (east edge of the macro) face pads 8–9; the
gate latch sits under GATE/FAULT_N/EN; the digital macro's north pins (`sclk`,
`sdo`, DAC codes) face SCLK/SDO and its east pins (`osc_*`, `cmp_*`, `trip_d`,
`clr_d`, `fast_en`, `tripped`, `en`, `t2f_*`, `bgr_r4`) face the trip, gate and
oscillator blocks; bandgap and T2F sit under TEMP_OUT/VREF; `g1_trip` between
sense (its `ISENSE`/`VREF` west pins) and the digital DAC codes.

| Instance | Cell | Size (W × H µm) | Lower-left (x, y) | Upper-right | Orient. | Supplies (`PDN_MACRO_CONNECTIONS`) | Pins facing |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `i_core.u_digital` | `g1_digital` (run7) | 360 × 360 | (367, 372) | (727, 732) | N | VDD/VSS (TopMetal1/2 stripes) | N: SCLK/SDI/SDO pads, DAC codes to trip; E: trip/gate/osc; W: `sdi`, `cmp_soft` |
| `i_core.u_sense` | `g1_sense` | 252.16 × 189.25 | (733, 440) | (985.16, 629.25) | N | IOVDD/IOVSS (Metal3 N/S bars) | E: `sense_p/n` → pads 8–9 at y 467–659; W: `iptat`, `vref` from bgr, `isense`, `vref_buf` to trip |
| `i_core.u_trip` | `g1_trip` | 229 × 207 | (737, 648) | (966, 855) | N | VDD/VSS + IOVDD (three Metal3 bars) | W: `VREF`, `ISENSE`, `dac_soft` ← sense/digital; E: `cmp_*`, `clk`, `dac_hard` |
| `i_core.u_gate` | `g1_gate` | 130.68 × 50.65 | (850, 862) | (980.68, 912.65) | N | VDD (west stub) + IOVDD `vdda` (N bar) / VSS (S bar) | E: `gate_core`, `fault_core` → GATE/FAULT_N pads (y 691–883); W: `trip_d`, `clr_d`, `en_core`, `hard_cmp`, `fast_en` |
| `i_core.u_osc` | `g1_osc` | 166 × 137.57 | (366.5, 848) | (532.5, 985.57) | N | VDD/VSS (Metal3 bars) | W: `en`, `trim`; E: `osc_clk` → digital |
| `i_core.u_t2f` | `g1_t2f` | 92 × 102.6 | (546, 883) | (638, 985.6) | N | IOVDD/IOVSS (N/S bars) + VDD `vdd12` (E stub) | E: `pbias`, `pcasc`, `vref` from bgr, `en`, `mode`, `fout` → TEMP_OUT pad (x 803) |
| `i_core.u_bgr` | `g1_bgr` | 84 × 124 | (645, 862) | (729, 986) | N | IOVDD/IOVSS (N/S bars) | W: `vref`, `iptat`, `vbe`, `dvbe`; E: `pbias`, `pcasc`, `r4`; `vref` → VREF pad (x 915) and sense |
| `i_core.u_ls_r4`, `u_ls_mode`, `u_ls_en` | `g1_ls_up` | 9.2 × 11.7 | (546, 860), (566, 860), (586, 860) | | N | VDD + IOVDD `vdda` / VSS (Metal1) | between the digital's east pins and t2f/bgr |

Channels: 6 µm between digital and sense, 8 µm between trip and bgr, 7 µm
between t2f and bgr; osc, t2f and bgr are flush with the core top and trip
sits 18.75 µm above sense so that no standard-cell row band survives between
macros (see finding 3 below). The sense east pins at y 458–465 face pad 8
(SENSE_P, 467–547) directly; gate's east pins at y 882–890 sit between
FAULT_N (803–883) and EN (915–995).

Placeholder rectangles are no longer needed: `g1_trip` (229 × 207 instead of
the planned 250 × 200) and `g1_osc` (166 × 138 instead of 60 × 60) have LEF/GDS
of record.

Area: macros 129 600 + 47 721 + 47 403 + 6 619 + 22 837 + 9 439 + 10 416 + 3 × 108 =
274 358 µm² = 71 % of the 386 884 µm² core window; the rest is channels,
PDN and the few glue cells.

### Power connections used by the dry run

- `VDD_NETS: [VDD, IOVDD]`, `GND_NETS: [VSS, IOVSS]` — IOVDD/IOVSS become
  secondary PDN nets.
- `flow/pdn_cfg_g1.tcl`: LibreLane's stock `pdn_cfg.tcl` text (VDD/VSS ring,
  TopMetal1/TopMetal2 stripes, Metal1 rails) with two changes: the macro grid
  bound to `i_core.u_digital` only, and vertical TopMetal1 IOVDD/IOVSS stripes
  interleaved with the VDD/VSS ones and extended to the die boundary, where
  they overlap the IO cells' TopMetal1 `iovdd`/`iovss` rails (no second ring).
- `flow/analog_straps.tcl` (run by `flow/run_dryrun.sh` after `GeneratePDN`):
  at every same-net TopMetal1 stripe crossing an analog macro's Metal3 supply
  bar, a via stack TopMetal1→Metal5→Metal4→Metal3 with 2.2 µm Metal4/Metal5
  patches; for the two 0.5 µm stubs (`g1_gate/vdd`, `g1_t2f/vdd12`) and the
  shifters' Metal1 rails a jog to the nearest stripe; then `check_power_grid`.
- `PDN_MACRO_CONNECTIONS` (one line per macro pin pair) as in
  `flow/config_dryrun.yaml`: `g1_gate` and `g1_t2f` take both 1.2 V and 3.3 V;
  `g1_trip` takes VDD, IOVDD and one VSS; `g1_sense`/`g1_bgr` take
  IOVDD/IOVSS; `g1_ls_up` takes VDD, IOVDD (`vdda`) and VSS.
- Substrate: the analog blocks' `vss` bars are IOVSS (sense, bgr, t2f) or VSS
  (trip, gate, osc); both grounds meet at the ring pads (`sg13g2_IOPadVss` /
  `IOPadIOVss` share the substrate) — the chip has no separate analog ground.

Command (`flow/run_dryrun.sh` at the repository root): LibreLane to
`OpenROAD.GeneratePDN`, then `flow/analog_straps.tcl` on that step's ODB with
LibreLane's own OpenROAD binary (via stacks and jogs, `check_power_grid`),
then LibreLane from `Odb.RemovePDNObstructions`:

```
flow/run_dryrun.sh                       # full flow
flow/run_dryrun.sh --to OpenROAD.DetailedRouting
```

### Dry-run result (run tag `dryrun-1350`, 2026-09-19, evidence `reports/dryrun-1350/`)

The flow was run repeatedly up to `OpenROAD.GeneratePDN`; each stop is a real
integration finding and is recorded here with its fix or its open state.

| # | Stop | Cause | Action |
| --- | --- | --- | --- |
| 1 | `PDN-0006 VDD on Metal3 is blocked by obstructions on Metal4, Metal5 for i_core.u_osc` | the first `g1_osc.lef` and `g1_trip.lef` obstructed Metal4/Metal5 over the **whole** macro including the supply bars, so no via stack could land on the bars | block owners fixed the LEFs on 2026-09-19 (10:54 / 10:59): obstructions now follow the real Metal4/5/TopMetal1 shapes. The interim companion views (`dryrun_lef/`, Metal4/5 OBS inset) were used until then and are removed; the dry run of record uses the owners' LEFs |
| 2 | same for `i_core.u_t2f/vss` (Metal4/5/TopMetal1) | the first `g1_t2f.lef` had the `cmim` block obstruction (0–66 × 0–36.8 µm) over the south `vss` bar and a west `vss` stripe under it | fixed by the owner (10:46): OBS on the real capacitor shapes, `vss` = south bar only |
| 3 | `PDN-0179 Unable to repair all channels` | standard-cell row slivers in the 6–30 µm channels between macros have Metal1 rails that no TopMetal stripe crosses | rows narrower than 160 µm pruned (`FP_PRUNE_THRESHOLD: 160`), macros stacked so no row band remains between them (trip 18.75 µm above sense, gate on trip's halo, osc/t2f/bgr flush with the core top). Placement below is the result; the first draft had trip at (752, 646), gate at (850, 870), osc at (380, 800) |
| 4 | `PDN-0232 grid … does not contain any shapes` for every analog macro | pdngen drops vias only where two of its own stripes cross; the analog macros' 2–3 µm Metal3 bars are pins, not stripes | per-macro grids with a 1.5 µm Metal5 strap over each pg pin (`-grid_over_pg_pins`, pitch 9) and connects Metal3↔Metal5↔TopMetal1; shifters: Metal4 straps over the cell (`flow/pdn_cfg_g1.tcl`). Grid then generates fully |
| 5 | `PSM-0069 Check connectivity failed` on all four nets, 93 203 grid violations, every macro pin unconnected | see the PDN attempt log below | **closed**: stock pdngen configuration for VDD/VSS + digital macro, IOVDD/IOVSS as vertical TopMetal1 stripes into the pad rails, analog bars and shifter rails strapped by `flow/analog_straps.tcl` — **all four nets: "All shapes connected", 0 unconnected shapes** |

#### PDN attempt log (violation count = `design__power_grid_violation__count` after `GeneratePDN`)

| Attempt | Configuration | Result |
| --- | --- | --- |
| 0 | first `pdn_cfg_g1.tcl`: rewritten stdcell/ring section, inner IOVDD ring, per-macro grids over pg pins with Metal5 straps | 93 203 violations, PSM fails on every net, all macro pins unconnected (`reports/dryrun-1350/experiment_b/`) |
| 1 | + explicit per-layer connects M3–M4, M4–M5, M5–TM1 in the macro grids | 100 068 violations; unchanged picture (no `via3_4`/`via4_5` were ever generated: pdngen drops vias only where two of its own stripes cross, a pg pin is not a stripe) |
| 2 | + vertical Metal4 stripes in the macro grids so the Metal3 pin, Metal4 and Metal5 stripes intersect | 151 971 violations; worse |
| A/B/C/E | bisection: no IOVDD stripes / inner vs outer IOVDD ring / VDD-VSS only / no IOVDD shapes | 86 996 – 91 662: the failure is independent of the IOVDD nets and of the analog grids |
| D2 | LibreLane's **stock** `pdn_cfg.tcl` with the macro grid bound to `i_core.u_digital` only | **3 339** violations, digital macro connected, only the analog pins unconnected — the rewritten stdcell section (explicit `-nets` on stripes/rails/ring) was the defect |
| F | stock text + `VDD_NETS [VDD, IOVDD]` | 7 649: baseline holds with four nets |
| G | stock text + IOVDD/IOVSS ring outside the VDD/VSS ring (`-connect_to_pads`) + interleaved stripes | 10 629; the four `-connect_to_pads` segments are 15 µm wide (`-widths` ignored) and sit at 294–315 µm, inside the IO cells; no connection |
| H | stock text + IOVDD/IOVSS **vertical TopMetal1 stripes only**, `-extend_to_boundary` (through the IO cells, over their TopMetal1 iovdd/iovss rails), no ring | 3 851: only the unstrapped analog/shifter pins remain; IOVDD/IOVSS "connected" through the rail overlap |
| **H + straps** | `flow/analog_straps.tcl` on that ODB: via stacks (pdngen's `via3_4/4_5/5_6 …2200_440`) at each same-net TopMetal1 stripe crossing a Metal3 bar; Metal3/Metal2 jogs to the nearest stripe for the two 0.5 µm stubs and the nine shifter Metal1 rails | **0 unconnected shapes, `PSM-0040 All shapes on net … connected` for VDD, VSS, IOVDD, IOVSS** (45 via stacks). This is the variant that completes the flow — **but its IOVDD/IOVSS tap is DRC-illegal** (145 `TM1.b`/`TV2` markers: the stripes cross the cells' vdd/vss and the other IO rail on TopMetal1), see the open item |
| I | inner IOVDD/IOVSS ring (−14 µm) + stripes, with `-connect_to_pads` | 9 079 after straps; VDD/VSS connected, **IOVDD/IOVSS fail** (`PSM-0069`), `OpenROAD.IRDropReport` aborts |
| J | same without `-connect_to_pads` | 9 085 after straps; same failure |

Decision on the shifters (coordinator's option b): the three `g1_ls_up` are
placed as `MACROS` instances but are neither PDN-gridded nor listed in
`PDN_MACRO_CONNECTIONS`… their `vdd`/`vdda`/`vss` Metal1 rails are strapped
by the same script with a `via1_2` + Metal2 jog to the nearest TopMetal1
stripe. The router option (power pins as signal nets) does not exist in this
flow: the detailed router never routes to special nets, so a routed pin could
not reach VDD. Option (c) (absorb them into the digital macro) remains the
clean long-term answer.

Placement used in the last run (`reports/dryrun-1350/macro_placement.txt`,
also the table above): digital (367, 372), sense (733, 440), trip (737, 648),
gate (850, 862), osc (366.5, 848), t2f (546, 883), bgr (645, 862), shifters
(546/566/586, 860). Row cut: 163 → 58 rows (`openroad-cutrows.log`).

#### Assembly of record (`flow/run_dryrun.sh`, run tag `assembly-1350`, `reports/assembly-1350/`)

All macros of record placed (`g1_digital` run7, `g1_bgr` filled in place,
`g1_sense`/`g1_gate` filled, `g1_t2f`, `g1_trip`, `g1_osc`, `g1_ls_up` × 3,
and the device macros `g1_dose_macro` (30 × 30 µm at (367, 370), pins facing
pads 19–21) and `g1_dut_macro` (34 × 34 µm at (367, 800), pins facing pads
22–24); the digital macro moved from (367, 372) to (367, 408) to open the
west strip for them). Chip SDC sources `blocks/g1_ctrl/layout/g1_digital_top.sdc`
(osc_clk on the macro's clock-buffer input, asynchronous groups, 0.5/0.05 ns
uncertainties, false paths, SDI min delay).

##### Shorts found by the core-only LVS in the first run (r1) and the fix

The first assembly run (2026-09-19 14:44, evidence kept as
`reports/assembly-1350-r1/`, GDS sha256 `5325b02f…6121`) passed every check
of the flow — KLayout DRC 0, density 0, routing DRC 0, `check_power_grid` 0,
STA clean — and was electrically wrong. The core-only KLayout LVS
(`reports/assembly-1350-r1/core_lvs/xref.txt`) reported the layout net
`VDD,VDDA,VSS`: the three supplies were one conductor. Located with
metal-only connectivity extraction (`flow/lvs/supply_isolation.py` method) and
geometric overlap of the DEF special nets (`flow/lvs/pdn_net_overlap.py`,
`flow/lvs/pdn_macro_overlap.py`), all three causes were in
`flow/analog_straps.tcl` version 1:

| # | Short | Where | Why no check saw it |
| --- | --- | --- | --- |
| 1 | VDDA–VSS | the 8 µm TopMetal2 VDDA feed strap (y 384.2–392.2, x 942.9–1034.2) covered the first horizontal **VSS** TopMetal2 stripe (y 385.36–387.56, x 324.8–1025.4, extended to the core ring), plus 7 of that stripe's TopVia2 cuts and the strap's own TopVia2 at x 946 | same-layer overlap of two nets merges into one polygon: no DRC rule; `check_power_grid` tests one net at a time; the router's DRC ignores special wires. The strap position had been chosen against the VDD stripe (ends y 381.36) and the pad's ring-to-pad connection (y ≥ 395) only |
| 2 | VDDA–VDD, VDDA–VSS | the feed's Metal3/Metal4/Metal5/TopMetal1 patch column was placed "1 µm inside the core" with the sign of the pad side inverted: x 1030.0–1032.2, i.e. into the pad cell, where the pad's `vdd` rail (Metal3) and `vss` rails (Metal4, Metal5, TopMetal1) start at x 1031 | as above; pad-cell rails are LEF pins/obstructions the special-wire code never consulted |
| 3 | VDD to a `g1_osc` node | the three level shifters' `vdd` (Metal1 stubs at y 870) were jogged on Metal2 to the nearest VDD TopMetal1 stripe, x 529.1 — which runs over `g1_osc`; the Metal2 jog crossed the oscillator's east edge and the via stack Metal2 → TopMetal1 landed on its internal Metal3 at (529.1, 870.0) (`FOREIGN` in `pdn_macro_overlap`) | the jog code looked for the nearest same-net stripe and never at macro obstructions |

Fix (version 2 of the script, `analog_straps.tcl` header): the feed is rebuilt
on Metal3–Metal5 without any TopMetal near the pad (see "VDDA" below); every
via stack and jog is tested against all block instances' LEF obstructions and
pins on the layers it uses (the pin's own rectangle excepted, `g1_ls_up`'s
blanket Metal1/Metal2 obstruction excepted after a GDS check: the cell has no
Metal2 above y = 8.2 µm or below 1.35 µm, the jog rows are at 0.575, 10.0 and
11.4 µm); a blocked candidate stripe is skipped and logged; two helper VDD
TopMetal1 segments (x 604.72, y 831.5–872.5 in the channel between the
shifters and `g1_bgr`; x 630.0, y 907–988 over `g1_t2f` east of its TopMetal1
plate, crossing the `vdd12` pin) replace pdngen's stripe at x 604.72 that it
had cut above y 847 for the `g1_t2f` plate — without them the shifters' `vdd`
and `g1_t2f/vdd12` have no VDD stripe reachable without crossing `g1_osc` or
`g1_bgr` (log: `stripe at x=... skipped (obstruction of ...)`). The r1 run's
other numbers stand as recorded there; the run below supersedes it.

Two geometric checks now run in `flow/signoff/signoff.sh` on every assembly
(`pdn_net_overlap.log`, `pdn_macro_overlap.log`), plus the metal-only
connectivity check of all chip pins (`supply_isolation.log`); the core-only
LVS remains the arbiter.

##### Run of record (r2)

Run of 2026-09-19 16:45–17:13 (`flow/run_dryrun.sh`; this time the flow's
Magic DRC and netgen LVS steps also ran, their results are recorded below as
the known tool-limitation failures); 12 macros, 7 glue standard cells; final
GDS sha256 in `reports/assembly-1350/final_gds.sha256`; GDS 51 MB, kept under
`flow/runs/assembly-1350/final/gds/`.

| Check | Result | Log / report (`reports/assembly-1350/`) |
| --- | --- | --- |
| PDN connectivity (`check_power_grid` after the straps) | **failed for VDDA in the retained abstract-view check**: six unconnected shapes and two instances, `PSM-0069`; VDD/VSS passed. The aggregate zero metric does not represent this log. Independent 2026-09-21 GDS probes connect the reported residue to the macro supply grid; see below | `analog_straps.log` |
| **Supply nets: same-layer overlaps between different nets** (`flow/lvs/pdn_net_overlap.py`, DEF special nets + via cells) | **passed, 0** (r1: VDDA × VSS on TopMetal2 + 8 TopVia2 cuts) | `pdn_net_overlap.log` |
| **Supply shapes on macro / IO-cell metal outside their pins** (`flow/lvs/pdn_macro_overlap.py`, all 12 macros, 24 pads, corners, fillers) | **passed, 0**; every supply shape over a cell lies on that cell's pin of the same net (r1: 5 — VDDA patches on the pad's `vdd`/`vss` rails, VDD stack on `g1_osc` metal) | `pdn_macro_overlap.log` |
| **Supply isolation** (`flow/lvs/supply_isolation.py`, metal-only connectivity of the whole GDS, chip-pin labels) | **passed**: 22 labelled nets, none carrying two pin labels — VDD, VSS, VDDA, IOVDD, IOVSS and the 17 signals are separate conductors (r1: `VDD,VDDA,VSS`) | `supply_isolation.log` |
| Routing | **passed**: 0 DRC after 3 iterations (15 → 1 → 0), OpenROAD antenna 0/0, 3 diodes | `openroad-detailedrouting.log`, `metrics_summary.json` |
| Disconnected pins | **passed**: 0 critical; 11 non-critical = unused `padres`/`padbare` of the analog pads and `pad07_vdda/padres`. Note: `pad13_trip_set/padres` counts as connected but its net `i_core.trip_set` has no consumer — `g1_trip` has no TRIP_SET input (`rtl/g1_core_dryrun.sv`, specification: "optional") | `odb-reportdisconnectedpins.log`, `full_disconnected_pins_table.txt` |
| STA with the digital owner's SDC (`g1_digital_top.sdc` sourced) | **passed**: hold worst slack **+0.106 / +0.185 / +0.326 ns** (fast/typ/slow — the macro's own signoff values), setup 28.1 / 27.4 / 26.0 ns; both clock domains (`osc_clk`, `SCLK`) constrained | `stapostpnr_summary.rpt`, `sta_*_min.rpt` |
| **KLayout DRC, hard rules** (`ihp-sg13g2.drc`, deep, `no_recommended`) | **passed, 0 markers** | `drc.klayout.json`, `klayout-drc.log` |
| KLayout DRC, **precheck** (`precheck_drc=true`, hard rules) | **passed, 0 markers** — the precheck mode skips the metal/via rules the deck marks `unless PRECHECK_DRC` (5_16–5_19, density), nothing extra is flagged | `drc_precheck/drc_precheck.log` (`PreCheck DRC enabled: true`), `.lyrdb` |
| KLayout DRC with the **recommended** rules | 60 markers: `Pad.fR_TM1` 24 + `Pad.fR_TM2` 36 (the IO cells' 3 µm `pad` stub vs the recommended 7 µm metal exit length under a bond pad — PDK-cell property, as on the ring alone). The r1 `TM2.bR` marker (VDDA feed strap vs VDD stripe) is gone with the strap | `drc_recommended/drc_recommended.log`, `.lyrdb` |
| **Density after fill** (chip area = EdgeSeal boundary 1 822 500 µm²) | **passed, 0 windows**, default and precheck modes. Global per layer: Activ 46.1 % (35–55), GatPoly 15.4 (≥ 15), Metal1 48.3, Metal2 39.4, Metal3 48.2, Metal4 48.6, Metal5 50.5 (35–60), TopMetal1 47.8, TopMetal2 44.1 (25–70). No local window fails, so no per-layer relief over the matched devices is needed | `klayout-density.log`, `density.klayout.json`, `density_detail/density.log` (per-layer table), `density_detail/density_precheck.log` |
| KLayout antenna | 9 markers on the 3 `sg13g2_IOPadIn` receiver gates (EN, SCLK, SDI; `Ant.e_Metal5/TopMetal1/TopMetal2`, rail-tied gate — the library artefact of `reports/antenna_reference/`); r1 had 15 on the same 3 gates (`Ant.e_Metal4`, `Ant.f_TopVia2` in addition — the summed supply metal changed with the feed) | `antenna.klayout.json/.lyrdb`, `antenna_markers.txt` |
| XOR Magic vs KLayout streamout | 30 632 differences, expected with `MAGIC_MACRO_STD_CELL_SOURCE: PDK` (six macros lacked a `prBoundary` when this was set; KLayout GDS is the primary view) | `klayout-xor.log` |
| Magic DRC (flow step, not a sign-off deck — `AGENTS.md`) | failed, 675 markers: 524 in the PDK IO cells and their abutments (`This layer can't abut or partially overlap between subcells` 336, `CntB.h1` 164, `Can't overlap those layers` 24 — as on the ring alone, block README), 151 in the core (`MIM.e` 76 on the macros' MIM capacitors, `CntB.h1` 60, `Slt.c` 15 on the 15 µm core ring — Magic's 6 µm slot threshold); the KLayout deck reports 0 on the same GDS with its MIM, contact and TopMetal rules | `drc.magic.rpt` |
| netgen LVS (flow step, black-box) | failed, 42 errors (18 unmatched pins, 23 net differences: the abutment-joined bondpad/pad nets and the pad rails, as on every frame — `reports/lvs_reference/`); superseded by the core-only KLayout LVS below | `lvs.netgen.rpt` |
| Core-only KLayout LVS | **passed**, 52 circuit pairs matched, zero unmatched circuits; strict top-level port comparison; IO ring excluded | `core_lvs/` |

Netlists: `netlist/g1_chip_top.pnl.v` (powered) and `.nl.v` from the flow;
`netlist/g1_chip_top.cdl` assembled by `flow/lvs/assemble_chip_cdl.py`, now
run by `flow/run_dryrun.sh` at the end of every assembly so that the CDL is
always the one of the final GDS (PDK stdcell + IO CDL, the nine analog/device
macro CDLs, the digital macro from its own powered netlist; 160 subcircuits;
4 884 instances at chip level — 12 macros, 6 antenna diodes, 1 tie cell,
4 645 decap/fill cells, the 24 pads, 92 fillers, 4 corners and 24 bondpads —
and 7 992 inside `g1_digital`).

##### Core-only KLayout LVS (`flow/lvs/run_core_lvs.sh`, evidence `reports/assembly-1350/core_lvs/`)

The PDK IO cells cannot be matched by any available extractor
(`reports/lvs_reference/`), so the LVS of the assembled chip excludes the ring
and compares everything inside it at transistor level:

1. `core_cdl.py`: the chip CDL minus the ring instances (`sg13g2_IOPad*`,
   fillers, corners, bondpads) becomes `.SUBCKT g1_core` whose ports are the
   chip supplies and the nets the pads drove on their core-side terminals
   (`p2c`/`c2p`/`padres`/`padbare`), named as the CDL names them (`D_ELT`,
   `SENSE_P`, … for the `padbare` nets — merged with the pad net — and
   `en_i`, `i_core_sclk_i`, … for the digital pads). 19 ports; `TRIP_SET`
   has none because its `padres` net has no consumer in the core.
2. `core_only_gds.py` on the final GDS: the standard cells that arrived
   inside the digital macro's GDS exist as renamed copies (`sg13g2_nand2_1$1`
   …, the stream-out's cell-conflict handling) next to the PDK cells the chip
   flow placed — the LVS deck flattens cells without a schematic counterpart,
   which had made the layout `g1_digital` flat and KLayout skip its comparison
   ("subcircuits failed to compare", a bottom-up ordering effect); the 39
   variants are folded onto the PDK cells after a geometric identity check
   (merged shapes and texts per layer; 6 folded, 33 renamed, 0 differing).
   Then a text with the port name is placed on the routed wire nearest each
   removed pad (DEF NETS routing, on the wire's own layer), VDD/VSS/VDDA on
   their longest TopMetal stripe inside the core (DEF SPECIALNETS), the ring
   cells, bondpads and seal ring are removed together with every top-cell
   shape outside the ring's inner edge (the DEF pin squares on the bondpads and
   their texts), and the top cell is renamed `g1_core`.
3. The PDK deck (`run_lvs.py --run_mode deep --top_lvl_pins --spice_comments`,
   strict port mode) compares the two; `xref_summary.py` prints one line per
   circuit pair with the unmatched objects.

Excluded from this LVS by construction: the 24 IO cells and their internal
joins (`pad`–`padbare` conductor, ESD clamps), the bondpads and the ring rails;
those are covered by the metal-only supply-isolation check (all 22 chip pins on
separate conductors, including the pad-internal path from bondpad to core
terminal) and by the flow's connectivity checks.


Findings on the delivered macros, from the first assembly run (13:41, its
KLayout DRC/density reports in `reports/assembly-1350/drc_macrofill/`):

1. **Upper-metal fill inside macros collides with the chip PDN.**
   `g1_sense_filled.gds` and `g1_gate_filled.gds` arrived with PDK fill on
   Metal4 … TopMetal2 and `g1_osc.gds` with fill on Metal4/Metal5, although
   the plan is fill up to Metal3 only and Metal4 and above left to the chip
   filler (as `g1_bgr`, `g1_t2f`, `g1_dose_macro`, `g1_dut_macro` were
   delivered). Those are the layers where the chip stripes, the VDDA straps
   and the via stacks onto the Metal3 bars land: **234 KLayout DRC markers**
   (`TM2.b` 85, `TM1.b` 47, `TM2Fil.c` 40, `TM1Fil.c` 30, `M4.b`/`M5.b`/
   `M4Fil.c`/`M5Fil.c` 8 each), all fill-cell-to-chip-metal spacing, 46 of
   them inside the `g1_sense`/`g1_gate` cells themselves. Until the owners
   re-deliver, the assembly uses `flow/macro_gds_workaround/` (fill cells on
   those layers removed, no-fill rectangles added; README there) — not views
   of record.
2. **`prBoundary` on 189/0 hijacks the density check.** `g1_sense` (4 shapes,
   incl. its `g1_ota` sub-cells) and `g1_gate` (1) carry their boundary on
   189/0 (drawing) as well as 189/4. The PDK density deck takes *any* 189/0
   polygon as the chip area ("prBoundary takes precedence"): the chip-level
   check then used 54 340 µm² (the two macros' bbox) instead of the
   1 822 500 µm² EdgeSeal boundary and failed the **maximum**-density rules
   `AFil.g1` (> 55 %), `M1.k`…`M5.k` (> 60 %), `TM1.d`/`TM2.d` (> 70 %) over
   that rectangle — the "8 density errors" of every dry run since the filled
   macros were placed were this, not a fill shortage. Owners: boundary on
   189/4 only. The workaround variants have 189/0 removed.

The chip CDL (`netlist/g1_chip_top.cdl`, `flow/lvs/assemble_chip_cdl.py`) is
the flow's powered Verilog netlist with the PDK stdcell/IO CDLs, the nine
analog/device macro CDLs and the digital macro's own powered netlist expanded
to standard cells (160 subcircuits; bus ports of black boxes expanded from the
Verilog concatenations). `netlist/g1_chip_top.pnl.v` / `.nl.v` are the flow's
Verilog netlists. (The CDL must be rebuilt for every run: the first r2 LVS was
run against the r1 CDL and reported exactly the r1/r2 netlist difference — one
antenna diode more on `i_core.tripped` and a filler renamed — which is why
`flow/run_dryrun.sh` now assembles it itself.)

#### The 3.3 V supply of the analog macros: VDDA (D14)

Finding (2026-09-19, before D14): no DRC-legal tap of the pad ring's
`IOVDD`/`IOVSS` exists with the stock `sg13g2_io` cells. In every ring cell
the `iovdd`/`iovss` rails run behind the `vdd`/`vss` rails on all of Metal3 …
TopMetal2 (cell y 66–119 vs 140–178), `vss` covers the whole cell on
Metal1/Metal2, and all rails span the full cell width; a wire from the core to
an `iovdd` rail crosses another supply on the same layer whatever layer it
takes. pdngen's `-connect_to_pads` on an inner or outer IOVDD ring emitted
four stray 15 µm TopMetal segments inside the IO cells (DRC `TM1.b`/`TV2.*`)
and no connection; TopMetal1 stripes run through the cells did connect but
shorted the rails (145 DRC markers, `reports/dryrun-1350-iovdd/`).

Decision D14 (`PLAN.md`, specification section 3): pin 7 becomes `VDDA`, an
`sg13g2_IOPadAnalog` whose bare terminal is the 3.3 V analog supply net inside
the core; analog ground is the core `VSS`; `IOVDD`/`IOVSS` power only the ring.
Implementation (`rtl/g1_chip_top.sv`, `flow/config_dryrun.yaml`,
`flow/analog_straps.tcl`):

- `pad07_vdda` (`sg13g2_IOPadAnalog`, `.pad(VDDA), .padbare(VDDA)`), east side,
  first pad from the bottom (x 1029–1209, y 355–435; `padbare` strip at
  x 1029.0–1029.3, y 381.1–405.9);
- VDDA is **not** in `VDD_NETS` (a secondary net there makes pdngen drop the
  VDD/VSS pad connections — experiment K: 270 unconnected pad rails); the strap
  script draws the VDDA grid on the net's special wire: 8 vertical TopMetal1
  and 8 horizontal TopMetal2 stripes, 2.2 µm, interleaved between the VDD and
  VSS stripes (VDD offset + half a pitch), `via6_7` at every crossing,
  overhanging the core area by 2.5 µm, **cut around every macro's TopMetal1/2
  obstruction + 2 µm** (as pdngen does with its halo; without the cut the
  stripes passed 0.54 µm from the `g1_t2f` and `g1_trip` capacitor plates —
  `TM1.b`);
- feed (version 2, after the shorts of version 1 below): the `padbare`
  terminal is a Metal3 strip 24.8 × 0.29 µm at the IO row's inner edge; the
  bare conductor itself is the pad's 70 µm Metal2 plate under it, joined by a
  column of 60 Via2. Metal3, Metal4 and Metal5 patches 4.4 µm wide over the
  strip's height (x 1026.0–1030.4: 3 µm on the core side, 1.4 µm into the pad
  cell, 0.6 µm short of the pad's rails, which start 2 µm inside the cell —
  `vdd` on Metal3, `vss` on Metal4/Metal5/TopMetal1), 80 `via3_4` + 80
  `via4_5` (400 cuts per level) between them, then a **Metal4 + Metal5 strap
  5.1 µm wide (y 386.8–391.9), 85.5 µm west** to the first vertical VDDA
  TopMetal1 stripe (x 946.0) with three `via5_6` (6 TopVia1 cuts) onto it.
  The strap's y range is computed as the widest part of the terminal's height
  free of other nets' Metal4/Metal5 special wires with 0.6 µm clearance — the
  corridor between two of pdngen's VDD stripe-to-rail via stacks at x 982.7
  (candidates logged in `analog_straps.log`). Nothing is drawn on TopMetal1/2
  near the pad: the first VSS TopMetal2 stripe runs under the terminal at
  y 385.4–387.6 and pdngen's ring-to-pad connection sits at y 395–408;
- the macro bars (`g1_bgr.vdd`, `g1_sense.vdd`, `g1_t2f.vdd`, `g1_trip.IOVDD`,
  `g1_gate.vdda`, the shifters' `vdda`) are strapped from the VDDA stripes by
  the generic bar code; `g1_osc` is 1.2 V (VDD).

Resistance from the pad terminal to the farthest 3.3 V bar (`g1_t2f.vdd` at
x 546–638, y 983–986; sheet resistances from `sg13g2_tech.lef`: Metal4/5
0.103 Ω/□, TopMetal1 0.021 Ω/□, TopMetal2 0.0145 Ω/□, vias TopVia2 2.2 Ω,
TopVia1 4 Ω, Via3/Via4 20 Ω per cut): feed 1.4 Ω (Metal4‖Metal5 strap
16.8 □ = 0.9 Ω, 6 TopVia1 0.7 Ω, 400-cut Via3/Via4 arrays 0.1 Ω), one 2.2 µm
TopMetal1 stripe 583 µm = 5.6 Ω, one 2.2 µm TopMetal2 stripe 377 µm = 2.5 Ω,
via stack on the bar 12 Ω → **≈ 21 Ω worst single path, ≈ 11 Ω with the mesh
sharing the long runs; ≈ 32 mV at the blocks' 1.5 mA** (version 1: 26 / 13 Ω).
The bar via stacks dominate; doubling them would halve it if ever needed.

The retained `check_power_grid` invocation **failed** on VDDA (`PSM-0069`):
six shapes on Metal2–TopMetal2 and two instances, `pad07_vdda/pad` and
`IO_BOND_pad07_vdda/pad`. `flow/run_dryrun.sh` recorded a zero aggregate
metric despite this failure; the corrected signoff collector preserves the
raw failure. A 2026-09-21 independent GDS metal/via extraction, without labels
or same-name/virtual connections, places every reported stub layer, bondpad,
padbare feed, feed strap, and BGR/SENSE/T2F/TRIP/GATE/LS supply-stack probe
on one physical conductor in the delivered layout. This supports the
LEF abstraction explanation for these particular reported residues. It is
not a pass of the failed OpenROAD check or of loaded VDDA IR analysis.
See [`VDDA_AND_POWER_20260921.md`](../../review/audits/VDDA_AND_POWER_20260921.md)
and the hashed probe records for exact scope and reproduction.

## Earlier dry run: g1_digital run4 alone on the 1200 µm frame (`reports/dryrun-digital/`)

Placed at (420, 420) in the 472 × 472 µm core: PDN macro grid inserted, 0
power-grid violations, 0 routing DRC, KLayout DRC 0, density 0, antenna 9
(library artefact); hold −0.14 ns at the fast corner because `osc_clk` was fed
from SCLK. Config and wrapper superseded by `config_dryrun.yaml` /
`rtl/g1_core_dryrun.sv`.

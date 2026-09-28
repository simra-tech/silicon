# IR drop and electromigration of the chip of record r4 (track T2, 2026-09-28)

Static (DC) IR drop from the bondpads to every block supply pin, and an electromigration (EM) check of the
top-level supply routes, the IO ring rails, the `GATE` pad route, the `SENSE_P`/`SENSE_N` routes and the
bandgap `VREF` route, on the chip of record r4 `g1_chip_top_1414_r4.gds` (`225d0b53…`, identical geometry
to the submitted `SoC1816.gds`). The digital macro's own power grid was analysed with OpenROAD PSM on the
macro's final views. Every number here is **simulated or derived from layout**; nothing is measured.

## Result

| Check | Status | Worst value (case, resistance set) |
| --- | --- | --- |
| IR drop, `VDD`/`VSS`, pads to every block pin | passed (derived budget, see below) | digital macro 13.16 mV on `VDD` + 16.13 mV on `VSS` at the chip level, + 1.06 / 1.00 mV inside the macro: 31.4 mV = 2.6 % of 1.2 V (trip worst, worst R) |
| IR drop, `VDDA`/`VSS`, pads to every block pin | passed (derived budget) | G1_SENSE 24.45 mV on `VDDA` + 15.90 mV on `VSS` = 40.4 mV = 1.2 % of 3.3 V (trip worst, worst R) |
| IR drop, `IOVDD`/`IOVSS` ring | passed (derived budget) | `GATE` pad cell 11.06 mV + 7.11 mV with 64 mA drawn by four output pads at once (worst R) |
| IR drop, quiescent (armed, tt/27 °C currents) | passed | largest: `VDDA` 6.29 mV at G1_SENSE, `VSS` 3.86 mV at G1_SENSE, `VDD` 2.93 mV at the digital macro (typ R) |
| EM, top-level supply routes (`VDD`, `VSS`, `VDDA`, `IOVDD`, `IOVSS`) | passed | 23.4 % (`VDD` Via3 4-cut array and 0.8 µm Metal3 at (358.4, 318–328), 0.375 mA) |
| EM, IO-ring rails (Metal2–TopMetal2 of the `sg13g2_io` cells) | passed | 13.3 % (`VDDA` pad cell Via3); ring TopMetal2 7.5 % |
| EM, IO-cell Metal1 (library metal inside the ring cells) | passed, over 50 % | 84 % in a 0.16 µm Metal1 slice at an IO-cell abutment on `IOVSS`, with the 64 mA four-pad bound (converged: 83.6 % at 1 µm, 83.8 % at 0.5 µm mesh) |
| EM, `GATE` pad route (bondpad + outward stub) at 40 mA | passed | 3.9 % |
| EM, `SENSE_P`/`SENSE_N` routes | passed, over 50 % | 83 % in single Via3/Via4 cuts at the 0.331 mA fault bound; about 4 % at the derived operating bound of 16 µA |
| EM, `VREF` routes (pad net and on-chip `i_core_vref`) | passed | 25 % (single cuts at the 0.1 mA charging bound) |
| Digital macro grid, OpenROAD `analyze_power_grid` | passed | fed as in the chip (one TopMetal1 stripe per net): 1.06 mV `VDD`, 1.00 mV `VSS`, EM 9.0 % (Metal1 rail) at 3.31 mW |
| Cross-check of the resistances with KLayout's R extractor | passed on wire-like nets, differs on plate-like nets | within 5 % on `SENSE_P`/`SENSE_N`/`i_core_vref`; the extractor reads 4–36 % lower on `VDD`/`VDDA` (see "Cross-check"); `VSS`: not run (extractor internal error) |
| Dynamic IR (supply bounce at the clock edge and comparator strobe) | **not run** | — |
| Package, bond wire and board resistance | **not run** | pads are ideal sources |
| Supply grids inside the analog macros (BGR, SENSE, TRIP, OSC, T2F, GATE, level shifters) | **not run** | the check ends at the landing of the top-level metal on the macro |
| EM inside the `sg13g2_io` cells beyond the ring rails (pad-to-driver path, ESD devices) | not applicable | library cell; the 30 mA pad's own path is the foundry's |
| EM of contacts (0.3 mA/contact) | not applicable | no top-level contacts; contacts inside IO cells and macros are library or block content |
| EM of resistors (rppd 1.2 mA/µm, rhigh 0.6 mA/µm) | not run, except G1_SENSE input | `RR1P0`/`RR1N0` rppd w = 2 µm: 0.166 mA/µm = 14 % at the 0.331 mA bound (derived) |
| EM above 105 °C | **not run** | the limits hold for 11 years at 105 °C; the specification gives no derating to 125 °C |

"Derived budget": no IR budget is specified for G1. The table compares the worst supply loss (drop on
the supply plus rise on the ground at the same block) with the ±10 % supply range the chip-level
simulations cover (1.08–1.32 V, 3.0–3.6 V, all passed in the r3x/r4 campaigns). Every worst case is below
3 % of the nominal supply.

List of every segment over 50 % of its limit: [`em_over_50pct.csv`](em_over_50pct.csv) (56 rows, all of them
the two items above: IO-cell Metal1 slices on `IOVSS` and the single-cut `SENSE_P`/`SENSE_N` routes at the
fault bound).

## Built against

| Item | Value | How established |
| --- | --- | --- |
| Layout | `blocks/g1_padring/layout/g1_chip_top_1414_r4.gds` `225d0b53…` | `strip_fill.json` `input_sha256` |
| Fill-free copy | `${BULK}/postsub-20260928/irem/nofill/g1_chip_top_1414_r4_nofill.gds` `c41b6522…` | `flow/pex/strip_fill.py` report |
| Net identity | `blocks/g1_padring/netlist/g1_chip_top_1414_r4.cdl` `e060c0c5…`; view `g1_top_interconnect_view_r4.gds` `6b855c9a…`, `prepare.json` `bf36fc10…` | `flow/pex/prepare_top_interconnect.py` report (0 shorts) |
| PDK | IHP-Open-PDK `84374023ee8b4b126bebbba67fcbada0a9c0ff0b` | `flow/run.sh` commit check |
| Container | `tapeoutbench-eda`, `sha256:ddeb6957…` | `flow/run.sh` image check |
| KLayout (Python module, incl. `klayout.pex`) | 0.30.9 | `geometry_summary.json` |
| ngspice | 46 | solver logs |
| Python / numpy / scipy (container) | 3.12.3 / 2.5.1 / 1.18.0 | `python3 -c "import numpy, scipy"` in the container |
| OpenROAD | 26Q1-1024-gdcf36133a (`/foss/tools/openroad-librelane/bin/openroad`) | `openroad -version` |
| Digital macro views | ECO macro run `digital-eco-r3cand2-20260926` (in r3 and r4, byte-identical): DEF `dabad146…`, SPEF `0b626c7f…`, SDC `7de6a086…` | `final_views.sha256` of the run |
| Liberty (PSM) | PDK `sg13g2_stdcell_typ_1p20V_25C.lib`, `sg13g2_stdcell_fast_1p32V_m40C.lib` | `psm_macro.tcl` |
| EM limits | IHP `SG13G2_os_process_spec.pdf` rev 1.2 §2.15 and note A.v (11 years at 105 °C, < 0.01 % failures): Metal1 1 mA/µm (0.36 mA at w ≤ 0.36 µm), Metal2–5 2 mA/µm (0.6 mA at w ≤ 0.3 µm), TopMetal1 15 mA/µm, TopMetal2 16 mA/µm, Via1–4 0.4 mA, TopVia1 1.4 mA, TopVia2 10 mA per cut | PDK documentation |
| Sheet and via resistance | same specification §2.13/§2.14. **typ**: target values (Metal1 0.110, Metal2–5 0.088, TopMetal1 0.018, TopMetal2 0.011 Ω/□; Via1–4 9, TopVia1 2.2, TopVia2 1.1 Ω/cut; identical to the kpex ihp-sg13g2 table). **worst**: maximum values with the metal TC1 applied for +100 K (125 °C): 0.181, 0.139, 0.0288, 0.0200 Ω/□; vias 20 / 4 / 2.2 Ω/cut (no via TC is given; not scaled) | `flow/pex/supply_mesh_solve.py` `TECH` |
| CPUs | 89–95 (`taskset` through `flow/run.sh`) | launch logs |

## Method

1. **Geometry** (`flow/pex/supply_geometry.py`, new). The fill-free chip is flattened with three origins:
   `route` (the top cell's own shapes and the routing-only cells, as in the 2025-09-25 top-interconnect view),
   `io` (every metal and via shape of the `sg13g2_io` pad, corner and filler cells: the ring rails and the pad
   metal) and `pin` (only the pin shapes of every other cell). Nets are named through the label points of
   `prepare_top_interconnect.py` run on r4 with the r4 CDL (0 shorts; the opens it lists are the IO-cell pin
   stacks, which the `io` metal now joins). For each block macro the **landing areas** are the overlap of the
   net's metal with the macro's own metal on the same layer; the block draws its current there. This matters:
   the BGR586 `vdd`/`vss` pin shapes (0.15 µm² each) are not touched by any top-level shape; the supply overlay
   lands on BGR metal next to them.
2. **Mesh and solve** (`flow/pex/supply_mesh_solve.py`, new). Each net's metal is cut into rectangles and each
   rectangle into cells of at most 1 µm (record pitch); neighbouring cells are joined by R = R<sub>s</sub> ·
   distance / shared width, via cuts by R<sub>cut</sub>/n between the cells above and below. The bond-ball area
   (40 × 40 µm, TopMetal2) of every bondpad on the net is an ideal source (bond wire and package: not run).
   Each block's current is spread over its landing cells in proportion to area. The resistor network is solved
   by ngspice 46 (`op`, KLU); scipy solves the same matrix as a check (largest difference 1 × 10<sup>-8</sup> V).
   Parts of the metal not connected to a pad are listed: the digital macro's TopMetal2 pin stripes (756 µm²
   per net, reached only through the macro), the BGR pin shapes and one T2F `vref` pin piece (connected inside
   T2F); no block is left without a connected landing (0 opens).
3. **EM metric.** Via arrays: current per cut against the per-cut limit. Wires: for every rectangle, the net
   current through each internal cross-section and through each edge, divided by the rectangle's extent across
   that section, against the mA/µm limit. A piece at most 0.36 µm (Metal1) or 0.3 µm (Metal2–5) wide whose sides
   along the current do not abut other metal is treated as a minimum-width wire (0.36 / 0.6 mA). Peak currents
   are compared with the DC limits; the `GATE`, `TEMP_OUT`, `SDO` and `FAULT_N` peaks last about 100 ns, so the
   comparison is conservative.
4. **Loads** ([`make_loads.py`](make_loads.py), [`loads.json`](loads.json)); every current is simulated:
   - **quiescent**: armed, 1 A load, tt/27 °C, quiet window of the r4 full-chip deck
     (`cdl_c_mid_pex_tt_27C_…_r4a`): BGR 319.7 µA, SENSE 1101.4 µA, T2F 41.7 µA (`VDDA`); TRIP 5.2 µA, T2F
     0.3 µA (`VDD`); the oscillator 115.0 µA (transistor-level run `…_osctl_…_r4a`); the digital macro 0.960 mA
     (OpenROAD `report_power`, typ, 10 MHz, vectorless); `IOVDD` 128 µA shared by the seven digital IO cells.
   - **trip worst**: the largest block current over all 795 chip-level logs with a supply line (BGR 484 µA,
     SENSE 1704 µA at ff/125 °C; oscillator 150.3 µA at ff/−40 °C, 1.32 V), plus the trip-event rise of `VDDA`
     (0.837 mA at ss/125 °C, r4 waveforms) on SENSE, the digital macro at 2.51 mA (fast 1.32 V −40 °C, 12.44 MHz,
     switching activity 1.0 on every net: an upper bound), and 64 mA on `IOVDD` and on `IOVSS`: the `GATE`
     pad at 40 mA (r4 waveforms: (v(gate) − v(gfet))/10 Ω peaks 39.5 mA sinking and 38.3 mA sourcing at
     ff/−40 °C, 29.6 / 29.2 mA at tt) together with `TEMP_OUT` 16 mA, `SDO` 4 mA and `FAULT_N` 4 mA at their
     rated drive at the same instant. `GATE` pad route: 40 mA into the pad's TopMetal1/TopMetal2 pins.
     `SENSE_P`/`SENSE_N`: 0.331 mA bound (3.3 V across the 9.97 kΩ `RR1` input resistor); the operating
     current is below 16 µA (derived: (V<sub>SENSE</sub> − V<sub>vp</sub>)/R1 with the gain-20 divider and a
     pedestal up to `VDDA`). `VREF` pad: 0.1 mA bound (22 kΩ BGR output resistance charging the external
     10 nF, doubled).
   - Every block current returns on `VSS`; every IO-cell `IOVDD` current returns on `IOVSS`.
5. **Digital macro** ([`psm_macro.tcl`](psm_macro.tcl)): OpenROAD reads the tech and cell LEF, the macro DEF,
   the liberty, the macro SDC and SPEF, reports power and runs `analyze_power_grid -enable_em` on `VDD` and
   `VSS`. PSM puts its sources on the macro's power pins. Three pin sets were run: the stock DEF (5 TopMetal1
   + 5 TopMetal2 stripes per net), a copy with one TopMetal1 and one TopMetal2 stripe per net, and the chip
   case: a copy with only the west TopMetal1 stripe, the one the chip-level metal reaches (`chipfedtm1`).

## IR drop per block supply pin

Largest drop over the block's landing area, mV (mean values in [`ir_drop_by_pin.csv`](ir_drop_by_pin.csv)).
Ground nets give the rise above the pad. typ R / worst R as defined above.

| Block | Pin (net) | Load quiescent / trip (mA) | Quiescent, typ R | Quiescent, worst R | Trip worst, typ R | Trip worst, worst R |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| G1_CTRL digital macro | `VDD` | 0.960 / 2.51 | 2.93 | 5.15 | 7.50 | 13.16 |
| | `VSS` | 0.960 / 2.51 | 3.73 | 6.60 | 9.15 | 16.13 |
| | inside the macro, `VDD` / `VSS` (PSM, chip-fed) | 0.960 / 2.51 | 0.43 / 0.40 | — | — | 1.06 / 1.00 (fast lib) |
| G1_OSC | `VDD` | 0.115 / 0.150 | 1.89 | 3.46 | 3.72 | 6.90 |
| | `VSS` | | 2.60 | 4.80 | 5.24 | 9.70 |
| G1_TRIP | `VDD` | 0.0052 / 0.0071 | 1.16 | 2.19 | 2.77 | 5.24 |
| | `IOVDD` pin (`VDDA`) | ≈ 0 / 0.0001 | 5.28 | 9.53 | 10.89 | 19.65 |
| | `VSS` | | 1.97 | 3.68 | 4.36 | 8.16 |
| G1_T2F | `vdd12` (`VDD`) | 0.0003 / 0.0026 | 1.12 | 2.11 | 2.73 | 5.15 |
| | `vdd` (`VDDA`) | 0.042 / 0.054 | 5.51 | 9.96 | 11.19 | 20.21 |
| | `VSS` | | 2.15 | 4.00 | 4.62 | 8.62 |
| G1_GATE | `vdd` (`VDD`) | ≈ 0 | 1.11 | 2.11 | 2.71 | 5.13 |
| | `vdda` (`VDDA`) | ≈ 0 | 6.23 | 11.26 | 13.38 | 24.18 |
| | `VSS` | | 1.95 | 3.65 | 4.33 | 8.10 |
| `g1_ls_up` × 3 | `VDD` / `VDDA` / `VSS` | ≈ 0 | 1.11 / 6.23 / 2.04–2.10 | 2.10 / 11.26 / 3.82–3.90 | 2.70 / 13.38 / 4.54–4.67 | 5.12 / 24.18 / 8.50–8.68 |
| G1_BGR (BGR586) | `vdd` (`VDDA`) | 0.320 / 0.484 | 6.20 | 11.24 | 12.29 | 22.24 |
| | `vss` (`VSS`) | | 3.27 | 5.86 | 6.75 | 12.18 |
| G1_SENSE | `vdd` (`VDDA`) | 1.101 / 2.541 | 6.29 | 11.37 | 13.53 | 24.45 |
| | `vss` (`VSS`) | | 3.86 | 7.10 | 8.64 | 15.90 |
| G1_DOSE, G1_DUT | `vss` (`VSS`) | 0 (no own current) | 2.23, 2.13 | 4.17, 4.00 | 4.97, 4.74 | 9.28, 8.91 |
| `GATE` pad cell (pin 10) | `IOVDD` / `IOVSS` rail | 0.018 / 40.0 | 0.01 / 0.01 | 0.02 / 0.01 | 6.42 / 4.16 | 11.06 / 7.11 |
| `TEMP_OUT` pad cell (pin 17) | `IOVDD` / `IOVSS` rail | 0.018 / 16.0 | 0.01 / 0.01 | 0.02 / 0.02 | 6.24 / 4.36 | 10.73 / 7.42 |
| `GATE` pad route | bondpad to pad-cell pins | 40 | — | — | 0.38 | 0.70 |

Signal-net resistances (typ, mesh, 1 µm): `SENSE_P` bondpad to G1_SENSE 170.6 Ω, `SENSE_N` 106.3 Ω (the 64 Ω
mismatch reported on 25 Sep from the series sum, 171/106 Ω, is confirmed); BGR `vref` to G1_SENSE `vref`
137.5 Ω, to G1_T2F `vref` 232.6 Ω, to the `VREF` pad cell 247.3 Ω. With 1 µA drawn by each input, the static
`VREF` error at SENSE and T2F is below 0.3 mV (derived).

Derived observation (not simulated in a circuit): the blocks' grounds differ by up to 1.9 mV at quiescent
(G1_SENSE 3.86 mV, G1_TRIP 1.97 mV, G1_BGR 3.27 mV above the pads, typ R) and by up to 7.7 mV in the trip-worst,
worst-R case. The TRIP thresholds compare `ISENSE` (SENSE ground) with DAC levels derived from `VREF` (BGR
ground) on the TRIP ground, so these offsets add, at the `ISENSE` level, a static term of the order of 1 LSB
of the hard DAC (3.9 mV at `ISENSE`, 0.196 mV at the shunt). The static part is inside what the per-part
calibration absorbs; the effect has not been simulated.

## EM

Largest utilisation per net (record mesh 1 µm, typ R; worst R differs by at most 2 percentage points; per net, origin
and layer in [`em_max_by_layer.csv`](em_max_by_layer.csv); segment list ≥ 10 % plus the top 15 per
net and case in [`em_segments.csv`](em_segments.csv)).

| Net | Case | Top-level route, wire | Top-level route, via | IO-ring cells (`io`) | Where (route) |
| --- | --- | ---: | ---: | ---: | --- |
| `VDD` | trip worst | 23.4 % | 23.4 % | 7.3 % (Metal3) | Metal3 0.8 µm and Via3 4 cuts at (358.4–359.2, 318–328.2), 0.375 mA |
| `VSS` | trip worst | 22.0 % | 9.7 % | 11.7 % (Via3 in the `VSS` pad) | Metal5 1.1 µm to the BGR ground at (736–749, 872–876.5), 0.484 mA |
| `VDDA` | trip worst | 22.5 % | 14.1 % | 13.3 % (Via3 in the `VDDA` pad cell) | Metal3 trunk at (1046–1083, 390.7–397.1), 0.45 mA/µm |
| `IOVDD` | trip worst | 5.6 % (bondpad) | 0.4 % | 7.5 % (TopMetal2 rail) | bondpad TopMetal2, 62.5 mA |
| `IOVSS` | trip worst | 3.5 % | 0.3 % | 84 % (Metal1 slice), rails ≤ 7.9 % | bondpad and stub |
| `GATE` | 40 mA | 3.9 % | 2.5 % | — (not a check here) | bondpad and outward stub |
| `SENSE_P`, `SENSE_N` | 0.331 mA bound | 55 % (0.2 µm wires, minimum-width rule) | 83 % (single Via3/Via4 cuts) | 37 % | route from pad to G1_SENSE |
| `VREF` (pad net) | 0.1 mA | < 0.1 % | < 0.1 % | 0.2 % | — |
| `i_core_vref` (BGR to SENSE, T2F, pad) | 0.1 mA | 25 % | 25 % | 28 % | single cuts on the route to the `VREF` pad cell |
| quiescent, all nets | | ≤ 14.5 % | ≤ 9.5 % | ≤ 6.3 % | — |

Segments over 50 % (the complete list is [`em_over_50pct.csv`](em_over_50pct.csv)):

- **`SENSE_P`/`SENSE_N` single-cut vias (83 %) and 0.2 µm wires (55 %) at the 0.331 mA fault bound.** The bound
  puts the full 3.3 V across the input resistor. In operation the pad sits within about 0.1 V of ground and the
  current is below 16 µA (about 4 % of the via limit). The bound would apply only if a pad is driven to the
  rail for years.
- **`IOVSS` Metal1 inside the IO cells (84 %).** A 0.16 µm high slice of the Metal1 plate at the lower edge of
  the `GATE` pad cell (x 1132.8–1183.4, y 691.0) and at three other cell edges on the east side carries
  0.134 mA along it. This is library metal of `sg13g2_io`, in parallel with the ring rails, with the 64 mA
  four-pad bound; it converges with the mesh (45 / 54 / 83.6 / 83.8 % at 5 / 2.5 / 1 / 0.5 µm). The same
  0.134 mA is also below the 0.36 mA the specification allows a minimum-width Metal1 wire.

## Digital macro grid (OpenROAD PSM)

[`psm_macro.json`](psm_macro.json). EM utilisation from PSM's resistor currents, with the macro's widths (Metal1
follow-pin rails 0.44 µm, TopMetal1/2 stripes 2.2 µm) and cut counts (Via1–4 1 × 5, TopVia1 1 × 2, TopVia2 1 × 1,
from the DEF `VIAS`).

| Pin set | Corner | Power | `VDD` worst / mean IR | `VSS` worst / mean IR | EM max |
| --- | --- | ---: | ---: | ---: | ---: |
| stock (10 stripes per net) | typ 1.2 V 25 °C, 10 MHz, vectorless | 1.15 mW | 0.134 / 0.078 mV | 0.143 / 0.076 mV | 1.9 % |
| stock | fast 1.32 V −40 °C, 12.44 MHz, activity 1.0 | 3.31 mW | 0.299 / 0.202 mV | 0.267 / 0.199 mV | 3.0 % |
| one TopMetal1 + one TopMetal2 stripe | typ / fast bound | 1.15 / 3.31 mW | 0.360 / 0.878 mV | 0.337 / 0.815 mV | 3.4 / 7.7 % |
| **chip case: west TopMetal1 stripe only** | typ / fast bound | 1.15 / 3.31 mW | **0.430 / 1.06 mV** | **0.401 / 1.00 mV** | **4.0 / 9.0 %** (Metal1 rail 0.090 mA/µm) |

The LibreLane run's own IR report on the same macro (0.533 mV `VDD` at 1.15 mW) used its flow defaults and the
flow's database; it is not repeated here. **Finding (design information):** at the chip level the metal
reaches only the west TopMetal1 stripe of each digital supply net; the TopMetal2 pin stripes and the other four
TopMetal1 stripes are fed through the macro's own vias. The combined drop (chip plus macro, 31.4 mV worst) stays
below 3 % of `VDD`.

## Cross-check and convergence

- **Independent extractor** ([`crosscheck_reff.csv`](crosscheck_reff.csv)): `klayout.pex.RNetExtractor`
  (KLayout 0.30.9, `SquareCounting`) on the same geometry, pads and landings tied as equipotential ports
  (`flow/pex/supply_rnet_crosscheck.py`). Wire-like nets agree within 5 % (`SENSE_P` 169.7 vs 170.6 Ω, `SENSE_N`
  104.9 vs 106.3 Ω, `i_core_vref` +1.9 to +4.9 %). On `VDD` the extractor is within −7 to +10 % except G1_OSC
  (−27 %: its 166 µm Metal3 pin is equipotential in the extractor, while the mesh spreads the current along it).
  On `VDDA` it is 4–36 % lower; its square-counting does not model current spreading in the Metal3/Metal4
  plates. The mesh values, the higher ones, are used. `Tesselation` failed with an internal error of the
  extractor (`dbPLCTriangulation.cc:426`) on every net except `i_core_vref` (where it agrees with
  `SquareCounting` within 0.2 %); `VSS` failed in both modes (`dbPLC.cc:543`): **not run**. The `GATE` row
  compares different sink models (all pin layers tied versus spread) and is not a check.
- **Hand check** of the mesh: a 100 × 2 µm Metal3 wire, a 50 µm riser, 4 Via3 cuts and a Metal4 plate give
  8.81 Ω against 8.7 Ω plus plate spreading by hand; EM 25 % (wire) and 62.5 % (via) exactly as by hand.
- **Mesh convergence** ([`mesh_convergence.csv`](mesh_convergence.csv), typ, trip worst): the largest drop
  changes by at most 3 % from 5 to 1 µm (`VDDA` 13.16 → 13.53 mV, `SENSE_P` 54.7 → 56.5 mV) and by 0.1 % from
  1 to 0.5 µm (`IOVSS`); route EM values change by at most 0.02.

## Not run

| Item | Reason |
| --- | --- |
| Dynamic IR drop and supply bounce (clock edge of 1200 flops, comparator strobe; red-team S2) | static analysis only; needs the full-chip extraction with the grid (track T1) and time-domain currents |
| Package, bond wire, board | not modelled; the bondpad ball area is an ideal source |
| Supply grids inside the analog macros | not in the view; block extractions exist per block only |
| EM of resistors other than the G1_SENSE input pair; of the IO-cell internal path from pad to driver | library or block content, not a top-level route |
| EM derating to 125 °C | the specification gives the limits at 105 °C only |
| `VSS` and `Tesselation` cross-checks | internal errors of `klayout.pex` 0.30.9 (above) |

## Files

In this directory: `README.md`; `make_loads.py` → `loads.json`; `run_irem.sh` (record solve, 1 µm, typ and
worst R, and the 5 / 2.5 µm convergence runs); `run_crosscheck.sh`; `psm_macro.tcl`; `summarize.py`, which
writes `ir_drop_by_pin.csv`, `em_segments.csv`, `em_over_50pct.csv`, `em_max_by_layer.csv`, `solve_summary.json`
(per net and case: currents, max drop, EM maxima, mesh size, islands, ngspice/scipy agreement),
`mesh_convergence.csv`, `crosscheck_reff.csv`, `psm_macro.json`, and a copy of `geometry_summary.json`. In bulk
(`${BULK}/postsub-20260928/irem/`): `nofill/`, `topic/` (view and `prepare.json`), `geom/` (net geometry JSON),
`solve/` (meshes, ngspice decks, raw files and logs, per-case JSON/CSV), `pitch_*`, `xcheck/`, `psm/` (PSM logs,
voltage and EM CSV, the two derived DEF copies), `logs/`.

## Commands (repository root, `flow/run.sh`, `G1_CPUSET` in 89–95, `G1_RESULTS_ROOT` = `B` = `${BULK}/postsub-20260928/irem`)

```sh
python3 flow/pex/strip_fill.py --input designs/g1-guardian/blocks/g1_padring/layout/g1_chip_top_1414_r4.gds \
  --output $B/nofill/g1_chip_top_1414_r4_nofill.gds --report $B/nofill/strip_fill.json
python3 flow/pex/prepare_top_interconnect.py --input $B/nofill/g1_chip_top_1414_r4_nofill.gds \
  --cdl designs/g1-guardian/blocks/g1_padring/netlist/g1_chip_top_1414_r4.cdl \
  --output $B/topic/g1_top_interconnect_view_r4.gds --report $B/topic/prepare.json
python3 flow/pex/supply_geometry.py --input $B/nofill/g1_chip_top_1414_r4_nofill.gds --prepare $B/topic/prepare.json \
  --nets VDD,VSS,VDDA,IOVDD,IOVSS,GATE,SENSE_P,SENSE_N,VREF,i_core_vref --outdir $B/geom          # 42 s
sh designs/g1-guardian/blocks/g1_top/reports/ir_em_20260928/run_irem.sh $B                        # 16 min
python3 flow/pex/supply_mesh_solve.py --geom $B/geom/IOVSS.json --loads $B/loads/IOVSS.json --tech typ \
  --pitch 0.5 --cases trip_worst --outdir $B/pitch_0.5                                            # 15 min
sh designs/g1-guardian/blocks/g1_top/reports/ir_em_20260928/run_crosscheck.sh $B
# PSM, one run per pin set and corner (MACRO = the run's final/ directory; DEF = its def/g1_digital.def or a
# derived copy in $B/psm/ with the VDD/VSS PORT list reduced; typ: LIB=sg13g2_stdcell_typ_1p20V_25C.lib VDDV=1.2
# PERIOD=100 ACT=; fast bound: LIB=sg13g2_stdcell_fast_1p32V_m40C.lib VDDV=1.32 PERIOD=80.4 ACT=1.0)
env MACRO=… DEF=… LIB=… VDDV=… PERIOD=… ACT=… OUT=$B/psm/<tag> /foss/tools/openroad-librelane/bin/openroad \
  -no_splash -exit designs/g1-guardian/blocks/g1_top/reports/ir_em_20260928/psm_macro.tcl
python3 designs/g1-guardian/blocks/g1_top/reports/ir_em_20260928/summarize.py $B designs/g1-guardian/blocks/g1_top/reports/ir_em_20260928
```

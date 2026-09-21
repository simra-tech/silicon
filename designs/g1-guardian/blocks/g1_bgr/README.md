# G1_BGR — bandgap reference and PTAT current source

State: **schematic simulated (2026-09-18); laid out, DRC/LVS/antenna clean, PEX run, post-layout
simulated (2026-09-19)**. Macro `g1_bgr`, 84 × 124 µm, LEF and GDS in `layout/`; post-layout
V<sub>REF</sub> = 1.039 V from the extracted netlist, 1.037 V with the estimated wiring resistance
(schematic 1.038 V), see "Post-layout".

## What it is

A first-order, current-mode, op-amp-less bandgap in the 3.3 V (`IOVDD`) domain built
around `npn13G2` HBTs, thick-oxide `sg13_hv_*` MOS and p+ poly `rppd` resistors. It
delivers `VREF` (nominal **1.038 V**, simulated) and a PTAT current of **4.1 µA at 27 °C**
on a mirror leg (`iptat`) plus the mirror gate rails (`pbias`, `pcasc`) from which
`G1_T2F` and other blocks copy I<sub>PTAT</sub>.

Topology (schematic `xschem/g1_bgr.sch`, netlist `xschem/g1_bgr.spice`):

- PTAT cell: Q1 (one unit HBT, diode-connected) against Q2 (eight parallel unit HBTs,
  `XQ2A..H`) with R1 (`rppd` 13.4 kΩ) in the Q2 emitter. Equal branch currents are
  forced by a cascoded PMOS mirror (`MP1/MC1`, `MP2/MC2`, W/L = 10/4 µm), so
  ΔV<sub>BE</sub> = (kT/q) ln 8 ≈ 54 mV at 300 K appears across R1 and
  I<sub>PTAT</sub> = ΔV<sub>BE</sub>/R1. No amplifier: the self-biased Widlar loop has
  a loop gain of 1/(1 + ln 8) ≈ 0.32.
- NMOS cascodes `MNC1/MNC2` (gate at 2 V<sub>BE</sub> + I<sub>PTAT</sub>·RX from a
  fifth mirror leg) hold both HBT collectors within ~0.1 V of V<sub>BE</sub>. This is
  what makes the block work: `npn13G2` has V<sub>CE,max</sub> = 1.6 V in the model
  card, and with the Q2 collector on the mirror gate node (2.3 V) the first version
  showed avalanche-driven supply sensitivity of 16 mV/V (−36 dB PSRR). With the
  cascodes it is −101 dB.
- PMOS cascode rail `pcasc` = `pbias` − I<sub>PTAT</sub>·RB (RB = 130 kΩ), so every
  mirror device sees V<sub>DS</sub> ≈ 0.54 V at 300 K (PTAT). Cascode bodies are tied
  to their sources (separate n-wells) so the body effect does not eat that margin.
- Output: an I<sub>PTAT</sub> copy into R2 (`rppd`, 82 kΩ) in series with a
  diode-connected unit HBT Q3: V<sub>REF</sub> = V<sub>BE3</sub> + ΔV<sub>BE</sub>·R2/R1.
  R2 is sized for zero TC at mid-range; no curvature correction.
- Start-up: a full mirror copy (`MPS`) into `RDET` (`rhigh` 2 MΩ) drives an inverter
  and a weak NMOS `MKFB` that pulls `pbias` down until the mirror carries current
  (release at about 0.8 µA, i.e. 20 % of nominal); no resistor from V<sub>DD</sub>
  into the core.
- Test mode `r4` (3.3 V logic input, default 0): connects a second unit HBT `Q1B` in
  parallel with Q1, area ratio 2:8 = 1:4. Diagnostic for the HBT ideality factor;
  V<sub>REF</sub> drops to about 0.915 V in that mode.
- Monitor outputs `vbe` (Q1 node) and `dvbe` (top of R1) are brought to pins so the
  top level can route them to a test mux or the freed analog pads of `PLAN.md` §7.

Pins: `vdd vss r4 vref iptat pbias pcasc vbe dvbe` (`xschem/g1_bgr.sym`).

### Why 1.04 V and not 1.2 V

The zero-TC output of a bandgap is the extrapolated 0 K junction voltage. For the
SiGe-base `npn13G2` the PDK model puts it near 1.04 V, not the 1.2 V of a silicon
junction: sweeping R2 (`sim/results`, R2 = 305 .. 330 µm) moves the TC minimum to
R2 ≈ 315 µm and V<sub>REF</sub> ≈ 1.04 V; forcing 1.2 V would leave a slope of about
+0.8 mV/K. The 2AMLogic source (below) reports the same thing as a "~13 % low"
untrimmed output after re-tuning for TC. The specification's "1.2 V class" is therefore
met as "1.04 V, zero-TC"; `G1_TRIP` DAC scaling and the `VREF` pad expectation should use
1.04 V. If a 1.2 V level is wanted it should be a scaled copy, not a re-tuned R2.

## Built against

| Item | Value | Established by |
| --- | --- | --- |
| PDK | IHP SG13G2 open PDK, commit `84374023ee8b4b126bebbba67fcbada0a9c0ff0b` | `/foss/pdks/ihp-sg13g2/COMMIT` in the pinned container (`../../PLAN.md` §2) |
| ngspice | 46 (PSP 103 and r3_cmc via OSDI) | `../../PLAN.md` §2 (`ngspice -v` in the pinned container; the batch logs carry no banner) |
| xschem | 3.4.8RC | `../../PLAN.md` §2 (`xschem --version`) |
| KLayout | 0.30.9, PCell library `SG13_dev`, PDK DRC/LVS decks | `reports/drc/drc_run_*.log`, `reports/lvs/lvs_run_*.log` ("Klayout version") |
| kpex | 0.3.12 | `reports/pex/cc/kpex_plain.log` |
| OpenROAD | 26Q3-850 (LEF load check only) | `reports/lef/lef_check.log` |
| Container | `flow/run.sh` image pinned in `../../PLAN.md` §2 | — |

## Source

Studied: https://github.com/2AMLogic/sg13g2-bandgap, commit
`2b72c41276d7fb43966ca335f2ed674a54c45a12`, Apache-2.0 — the only SG13G2 bandgap on
`npn13G2` (op-amp loop with PMOS input pair, HBT diode Q1/Q2 at 1:8, `rppd`, `rhigh`
pull-up start-up; DRC-clean layout, 300-sample MC, LVS not closed because their
extraction deck could not recognise HBTs). Its schematics and flattened netlist are
copied with the licence to `source/2AMLogic-sg13g2-bandgap/`. Kept here: device
choice (`npn13G2`, `sg13_hv_*`, `rppd`), 1:8 ratio, a kick transistor on the mirror
gate for start-up. Replaced: the PMOS op-amp loop by the op-amp-less cascoded PTAT
cell (amplifier offset and its temperature drift would sit directly on a 54 mV
ΔV<sub>BE</sub>); the `rhigh` pull-up sense by a mirror-copy sense; R2 re-sized to the
zero-TC point. Nothing of the source is instantiated.

The topology follows the classic self-biased cascoded HBT PTAT cell used in published
SiGe references (Najafizadeh et al., IEEE BCTM 2006; Wang, Dai, Hamilton, arXiv 2018);
the first-order-only decision and the p+ poly resistor choice follow the same literature.
No text or figure of those papers is reproduced here.

## Simulated

All runs: ngspice 46 inside the pinned container (`flow/run.sh`), PDK
`/foss/pdks/ihp-sg13g2` commit `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`, models
loaded with

```
.lib .../libs.tech/ngspice/models/cornerHBT.lib   {hbt_typ | hbt_bcs | hbt_wcs}[_mismatch]
.lib .../libs.tech/ngspice/models/cornerMOShv.lib {mos_tt | mos_ss | mos_ff}[_mismatch]
.lib .../libs.tech/ngspice/models/cornerRES.lib   {res_typ | res_bcs | res_wcs}[_mismatch]
```

and the PDK's `psp103.osdi` / `r3_cmc.osdi` via `sim/.spiceinit`. Netlist:
`xschem/g1_bgr.spice`, produced by `xschem 3.4.8RC -n -q -x` from `xschem/g1_bgr.sch`
(`xschem/netlist.sh`). Testbench template `sim/tb_g1_bgr.spice.tmpl` with the control
blocks `sim/ctl_*.txt`; decks, logs and CSV summaries under `sim/decks`, `sim/logs`,
`sim/results`. Commands:

```
G1_WORKDIR=designs/g1-guardian/blocks/g1_bgr/xschem flow/run.sh bash netlist.sh g1_bgr
G1_WORKDIR=designs/g1-guardian/blocks/g1_bgr/sim    flow/run.sh python3 run_bgr.py all
python3 designs/g1-guardian/blocks/g1_bgr/sim/analyze_bgr.py     # -> sim/results/tables.md
```

Load in every deck: `iptat` sinks into a 1.0 V source (DAC-string stand-in), `vref`
carries 1 pF, `r4` = 0 unless stated.

| Suite | Analysis | Corners | Temperature | Supply |
| --- | --- | --- | --- | --- |
| `temp` | `.dc temp -40 175 5` | 3 HBT × 3 MOS × 3 RES = 27 | −40 .. 175 °C | 3.0, 3.3, 3.6 V |
| `extrap` | `.dc temp -196 -40 4`, **model extrapolated** | hbt_typ/bcs/wcs, mos_tt, res_typ | −196 .. −40 °C | 3.3 V |
| `startup` | `tran`, V<sub>DD</sub> PWL 0 → 3.0 V in 1 ms, 3 ms total | 27 | −40, 27, 175 °C | 3.0 V |
| `startup_slow` | `tran`, V<sub>DD</sub> PWL 0 → 3.0 V in 100 ms, 130 ms total | 27 at 27 °C; typ at −40/175 °C | | 3.0 V |
| `psrr` | `ac dec 10 1 10meg`, 1 V on V<sub>DD</sub> | 27 | −40, 27, 175 °C | 3.3 V |
| `mc` | `.op`, 300 decks with `.option seed=1..300`, `*_mismatch` libraries, `mm_ok=1` on every device | hbt_typ / mos_tt / res_typ mismatch | 27 °C | 3.3 V |

### V_REF(T), -40 to 175 C in 5 C steps, 27 process corners x 3 supplies (simulated)

| HBT | RES | V_REF 27 C [V] (mos_tt, 3.3 V) | V_REF 27 C range, all MOS/VDD [V] | TC box -40..125 C [ppm/C] min..max | TC box -40..175 C [ppm/C] min..max | I_PTAT 27 C [uA] (tt, 3.3 V) |
| --- | --- | --- | --- | --- | --- | --- |
| hbt_typ | res_typ | 1.0379 | 1.0378 .. 1.0379 | 24.6 .. 25.4 | 22.8 .. 23.8 | 4.134 |
| hbt_typ | res_bcs | 1.0413 | 1.0413 .. 1.0414 | 15.4 .. 16.0 | 14.6 .. 15.5 | 4.727 |
| hbt_typ | res_wcs | 1.0346 | 1.0346 .. 1.0347 | 34.7 .. 35.6 | 31.5 .. 32.7 | 3.648 |
| hbt_bcs | res_typ | 1.0320 | 1.0320 .. 1.0321 | 40.1 .. 40.9 | 36.8 .. 38.0 | 4.137 |
| hbt_bcs | res_bcs | 1.0354 | 1.0354 .. 1.0355 | 28.5 .. 29.2 | 26.7 .. 27.8 | 4.731 |
| hbt_bcs | res_wcs | 1.0288 | 1.0288 .. 1.0289 | 51.3 .. 52.2 | 46.5 .. 47.7 | 3.651 |
| hbt_wcs | res_typ | 1.0452 | 1.0452 .. 1.0453 | 11.0 .. 11.7 | 11.8 .. 12.3 | 4.127 |
| hbt_wcs | res_bcs | 1.0487 | 1.0487 .. 1.0488 | 12.4 .. 12.6 | 15.2 .. 16.7 | 4.720 |
| hbt_wcs | res_wcs | 1.0420 | 1.0419 .. 1.0420 | 18.4 .. 19.2 | 16.8 .. 17.9 | 3.642 |

All 81 runs: V_REF(27 C) = 1.0288 .. 1.0488 V; TC box -40..125 C = 11.0 .. 52.2 ppm/C; -40..175 C = 11.8 .. 47.7 ppm/C.

### Nominal (hbt_typ, mos_tt, res_typ, 3.3 V)

| T [C] | -40 | 27 | 85 | 125 | 150 | 175 |
| --- | --- | --- | --- | --- | --- | --- |
| V_REF [V] | 1.0381 | 1.0379 | 1.0360 | 1.0340 | 1.0331 | 1.0353 |
| I_PTAT [uA] | 3.209 | 4.134 | - | 5.459 | - | 6.167 |
| total current [uA] | - | 22.0 | - | - | - | 32.8 |

delta-V_BE at 27 C = 55.07 mV (ideal kT/q ln 8 = 53.7 mV).

Supply: V_REF(27 C) = 1.03786 / 1.03786 / 1.03786 V at 3.0 / 3.3 / 3.6 V.

Ratio test mode (r4=1, 2:8 = 1:4): V_REF(27 C) = 0.9150 V, I_PTAT = 2.751 uA, delta-V_BE = 36.65 mV (ideal kT/q ln 4 = 35.8 mV).

### Cryogenic run, MODEL EXTRAPOLATED (PDK cards are not characterised below -40 C; numbers are not a prediction)

| HBT corner | V_REF -196 C | -150 C | -100 C | -40 C | I_PTAT -196 C [uA] | V_BE -196 C | delta-V_BE -196 C [mV] |
| --- | --- | --- | --- | --- | --- | --- | --- |
| hbt_bcs | 1.0259 | 1.0301 | 1.0327 | 1.0334 | 1.041 | 0.943 | 13.64 |
| hbt_typ | 1.0275 | 1.0327 | 1.0362 | 1.0381 | 1.042 | 0.944 | 13.66 |
| hbt_wcs | 1.0295 | 1.0360 | 1.0408 | 1.0441 | 1.043 | 0.946 | 13.67 |

### PSRR (AC, V_REF/V_DD), 27 process corners x 3 temperatures, 3.3 V

| | DC (1 Hz) | 1 kHz | 100 kHz | 1 MHz |
| --- | --- | --- | --- | --- |
| nominal 27 C [dB] | -103.0 | -82.3 | -42.3 | -25.0 |
| worst of 81 runs [dB] | -97.3 | -80.8 | -40.9 | -24.3 |

### Monte Carlo, 300 samples, hbt_typ_mismatch + mos_tt_mismatch + res_typ_mismatch, 27 C, 3.3 V

| quantity | mean | sigma | sigma / mean | min | max |
| --- | --- | --- | --- | --- | --- |
| V_REF [V] | 1.0394 | 19.1 mV | 1.84 % | 0.9900 | 1.1028 |
| I_PTAT [uA] | 4.153 | 0.214 | 5.16 % | 3.592 | 4.794 |
| delta-V_BE [mV] | 55.31 | 2.81 | 5.08 % | 47.85 | 64.34 |

### Start-up, 1 ms supply ramp to 3.0 V, 3 ms simulated, 27 corners x {-40, 27, 175} C

81 of 81 runs end with 0.9 V < V_REF < 1.2 V and |I_PTAT| > 1 uA (no stuck zero state). V_REF at the end: 1.0225 .. 1.0505 V. Time to V_REF = 0.93 V: 0.484 .. 0.614 ms after the ramp starts. Overshoot: max V_REF 1.0506 V.

### Start-up, 100 ms supply ramp to 3.0 V, 130 ms simulated, 27 corners at 27 C + typ at -40/175 C

29 of 29 runs end with 0.9 V < V_REF < 1.2 V and |I_PTAT| > 1 uA (no stuck zero state). V_REF at the end: 1.0288 .. 1.0488 V. Time to V_REF = 0.93 V: 48.325 .. 57.891 ms after the ramp starts. Overshoot: max V_REF 1.0488 V.

## Laid out

State: **DRC clean, LVS clean, antenna clean, PEX run, post-layout simulated** (2026-09-19).
Macro `g1_bgr`, **84 × 124 µm** (0.0104 mm²), origin at the lower-left corner, Metal1–Metal3
only. Files in `layout/`:

| File | What |
| --- | --- |
| `g1_bgr_layout.py` | KLayout batch Python generator (PDK PCells from `SG13_dev`, everything else drawn, no-fill regions and `prBoundary`): `G1_WORKDIR=designs/g1-guardian/blocks/g1_bgr/layout flow/run.sh klayout -b -r g1_bgr_layout.py` |
| `fill_g1_bgr.sh`, `fill_pre.py`, `fill_post.py` | PDK fill inside the macro (run after the generator, same `G1_WORKDIR`: `flow/run.sh bash fill_g1_bgr.sh`), see "Fill" |
| `g1_bgr.gds` | top cell `g1_bgr` with fill, `prBoundary` 189/4 = 0,0 – 84,124, sha256 `4f83cc0830a97b61fda66113cc3768db54e762fc210b2f798d3dd035db30afeb` (the GDS header carries a write timestamp, so a regenerated file has a different checksum for the same geometry) |
| `g1_bgr.lef` | abstract, `CLASS BLOCK`, `SIZE 84 BY 124`, pins below, `OBS` on Metal1, Metal2 (whole macro) and Metal3 (1.8 .. 82.0 × 2.6 .. 121.4) |
| `g1_bgr.vh` | Verilog black box for the chip flow (`MACROS: vh:`), power pins under `` `ifdef USE_POWER_PINS `` |

Floorplan, bottom to top (y in µm): vss bus 0–2 (Metal3) · resistor arrays 5–58 in one p+ ring
(23 `rppd` columns and 17 `rhigh` columns) · channel BA 59.8–65.2 (10 Metal3 tracks) · HBT array
67–82 (2 rows × 11 `npn13G2`, outer p+ ring) · channel CB 82.4–87.2 (9 tracks) · cascode PMOS in
five separate n-wells and the NMOS group in a p+ ring, 89–103 · channel DC 104.2–109.6 (10 tracks)
· mirror PMOS row 111–120 in one n-well with a full-length n-tap strip · vdd bus 122–124 (Metal3).
Metal2 is vertical (0.3 µm signal, 1 µm vss columns at x = 1.0 and 83.0), Metal3 horizontal
(0.3 µm, 0.6 µm pitch). Every p+ ring and every n-well tie is contacted along its whole length and
tied to vss / its well net in Metal1. Vias are single 0.19 µm cuts (20 Ω each in the PDK LEF) except
on the DC current path through R1 and R2 and on the vss ring straps, which use 2-cut pairs.

### Matching

| Devices | Layout | Matching |
| --- | --- | --- |
| Q1 : Q2A–H (1 : 8) | HBT row 1 (y = 77.3): D Q2A Q2B Q2C Q2D **Q1** Q2E Q2F Q2G Q2H D, unit `npn13G2` Nx = 1 at 6.3 µm pitch; the PCells' own p+ rings abut (merged into one contacted ring grid) | Q1 sits at the centroid of the eight Q2 units (one-dimensional common centroid); identical unit cells, orientation and ring environment; a dummy unit at each end |
| Q1B, Q3, QD1, QD2 | HBT row 0 (y = 70.6): D D D QD2 QD1 Q1B Q3 D D D D | Q1B (the 1 : 4 test-mode unit) directly below Q1; seven dummies complete the array so every active unit has the same neighbours |
| R1 : R2 (51.5 µm : 6 × 52.5 µm) | 23 `rppd` columns, w = 1 µm, pitch 1.9 µm, x = 7.5 .. 49.3: D RB RB RB RB RB RX RX R2 R2 R2 **R1** R2 R2 R2 RX RX RB RB RB RB RB D; series straps in Metal1 (serpentine), two Metal3 jogs join the halves | R2's two halves are symmetric about R1 (common centroid), one width, one orientation, one segment length class (48 .. 52.5 µm); dummy column at each end. R2 has 12 resistor heads against 2 for R1: see post-layout (+0.43 % on R2/R1) |
| RX (4 × 48 µm), RB (10 × 50 µm) | the RX and RB pairs of columns flank R2/R1 symmetrically | same width and orientation as R1/R2 |
| RDET (`rhigh`, 15 × 49 µm) | 17 columns, w = 0.5 µm, pitch 1.4 µm, x = 53 .. 75.4, serpentine, dummy at each end | none required (start-up detector) |
| MP1 .. MP5, MPS (mirror, 10/4 each) | 12 half fingers (w = 5, l = 4) at 5.4 µm pitch, x = 12 .. 71.4: MPS MP5 MP4 MP2 MP1 MP3 · MP3 MP1 MP2 MP4 MP5 MPS; one n-well, n-tap strip along the row tied to vdd | every device is two half fingers mirror-symmetric about the row centre (common centroid for all six); common gate rail `pbias` on one Metal3 track |
| MC1 .. MC5 (cascodes, 10/4) | five identical cells at 8 µm pitch, each in its own n-well with an n-tap strip on its source node (body = source) | identical cells and orientation |
| MNC1 : MNC2 (20/1 each) | four `nmosHV` fingers w = 10, l = 1 at 2.8 µm pitch inside the NMOS p+ ring: MNC1 MNC2 MNC2 MNC1 | interdigitated a b b a (common centroid) |
| MNI, MKFB, MSW1, MSW2, MNI2 | same p+ ring, x = 60.3 .. 75.1; columns placed clear of the mirror-row columns above them | none required |
| MPI, MPI2 (2/0.5) | left end of the mirror n-well (x = 7.5, 9.8) | none required |

### Pins (LEF, all Metal3; x, y in µm from the lower-left corner)

| Pin | LEF `USE` / direction | Rectangle | Edge |
| --- | --- | --- | --- |
| `vdd` | POWER, INOUT | 0, 122 – 84, 124 | north, full width (2 µm bar) — the padring's IOVDD |
| `vss` | GROUND, INOUT | 0, 0 – 84, 2 | south, full width (2 µm bar) — IOVSS and substrate |
| `vref` | SIGNAL, OUTPUT | 0, 85.85 – 1.5, 86.15 | west |
| `iptat` | SIGNAL, OUTPUT | 0, 87.05 – 1.5, 87.35 | west |
| `vbe` | SIGNAL, OUTPUT | 0, 83.45 – 1.5, 83.75 | west |
| `dvbe` | SIGNAL, OUTPUT | 0, 82.85 – 1.5, 83.15 | west |
| `pbias` | SIGNAL, OUTPUT | 82.5, 104.05 – 84, 104.35 | east |
| `pcasc` | SIGNAL, OUTPUT | 82.5, 85.25 – 84, 85.55 | east |
| `r4` | SIGNAL, INPUT | 82.5, 109.45 – 84, 109.75 | east |

Pin shapes are on Metal3 drawing (30/0) with pin layer 30/2 and text 30/25 (LVS strict-port mode
passed with these labels); the cell carries a `prBoundary` (189/4) equal to the LEF `SIZE`.
Integration notes for `../g1_padring/INTEGRATION.md`: 3.3 V macro, power
through `PDN_MACRO_CONNECTIONS: ["i_core.<inst> IOVDD IOVSS vdd vss"]` with the IOVDD/IOVSS
straps landing on the two Metal3 bars (via stacks Metal3 → TopMetal in a custom `PDN_CFG`, since the
pins are below Metal5); keep the default 10 µm PDN halo around the macro; `vref` and `iptat` are
high-impedance (≈ 88 kΩ, and a current source) and should stay on `RSZ_DONT_TOUCH_RX` nets. The
`iptat` pin sources 4.1 µA at 27 °C into a node that must stay between 0 V and about 2 V.

### Guard rings, wells, routing

- p+ substrate rings (Activ + pSD, contacts at 0.34 µm pitch, 0.26 µm Metal1): around the resistor
  arrays, around the HBT array (in addition to the PCells' own rings, bridged in Metal1 at every
  column and row), and around the NMOS group. All on vss: the resistor ring through three Metal2
  drops to the vss bus and two Metal3 jumpers to the vss side columns, the HBT ring through four
  Metal3 jumpers to the side columns (two per side) and two Metal2 jumpers to the resistor ring, the
  NMOS ring through one jumper; all with 2-cut via pairs.
- Star ground for ΔV<sub>BE</sub>: R1's bottom terminal does not go to the vss bus but up a Metal2
  line (x = 28.1) to the HBT ring's bottom side, the ring Q1's emitter sits on, so the return drop of
  the ring (about 12 µA of emitter current through the ring Metal1 and straps) stays out of the
  ΔV<sub>BE</sub> loop; R1 ↔ ring is the only vss connection of that node.
- n-wells: one for the mirror row (tie strip n+ Activ 7.5 .. 76.1 × 118.6 .. 119.0, seven Metal2
  straps into the vdd bus), one per cascode (tie strip on the cascode's own source node).
- Routing: Metal1 inside devices and for the resistor/ring straps; Metal2 vertical only; Metal3
  horizontal only (three channels plus one `vbe` track between the HBT rows). The west side columns
  (`dvbe`, `vref`, `vb2`) sit at 0.9 µm pitch so that the `dvbe`/`vref` taps can carry 2-cut Via2
  pairs. The generator refuses to write the GDS if two Metal2 verticals or via pads of different
  nets come closer than the Metal2 spacing.

### Fill

The chip-level filler cannot lift a placed macro's density on its own (`../g1_padring/INTEGRATION.md`,
density probe), so the macro carries its own fill and tells the chip filler where to stay out:

- **No-fill regions**, one rectangle per layer on `Activ/GatPoly/Metal1-5/TopMetal1-2` datatype 23
  (the nine layers the `SG13_dev` `NoFillerStack` PCell writes) plus `NoMetFiller` 160/0, with a
  2.5 µm margin around every matched structure: the `rppd` array R1/R2/RX/RB (4.8, 1.9 – 53.0, 60.6),
  the HBT array (4.0, 64.0 – 80.1, 84.3), the cascodes (4.9, 87.9 – 47.8, 105.9), the MNC1/MNC2 pair
  (45.5, 88.5 – 60.6, 103.5) and the mirror row (3.8, 108.3 – 79.8, 123.0). RDET, the small NMOS, the
  buses and the channels may take fill. Metal3 (30/23 only) also stays free in the LEF pin margins
  outside the Metal3 obstruction, so chip-level Metal3 routing next to the pins never meets fill.
- **Block fill** by the PDK filler (`libs.tech/klayout/tech/scripts/filler.py`, the `sg13g2_filler_ActGatP`
  and `sg13g2_filler_Metal` macros, invoked as LibreLane's `KLayout.Filler` does: `klayout -b -zz -r
  filler.py -rd output_file=… -rd no_topmetal in.gds`). The macros fill only inside `EdgeSeal.holes`,
  so `fill_pre.py` adds a temporary EdgeSeal ring (39/0) whose hole is the macro inset by 1 µm, and a
  temporary no-fill on Metal4/Metal5 (the macro has no Metal4/5; the chip filler fills those layers and
  the TopMetals over the macro after routing); `fill_post.py` removes both, renames the fill cells to
  `g1_bgr_*_FILL_CELL` (no clash with the chip's own fill cells) and counts. Result
  (`reports/fill/fill_g1_bgr.log`): Activ 1, GatPoly 1, Metal1 157, Metal2 104, Metal3 85 fill shapes
  (datatype 22), mostly over RDET, along the side columns and under the bus bars; the channels are too
  dense for more. The no-fill regions and the `prBoundary` are in the GDS the generator writes; the fill
  is added in place by `fill_g1_bgr.sh`.
- The PDK DRC and LVS decks read datatype 22 (`metal1 = metal1_drw.join(metal1_filler)`), so the DRC
  fill rules (`AFil.*`, `GFil.*`, `M1Fil.*`…`M5Fil.*`) are checked and the LVS sees the fill as metal:
  both clean on the filled GDS, the extracted device netlist unchanged (`reports/lvs/`).
- kpex also joins the datatype into its metal layers, but its 2.5D extraction gives the identical
  capacitance netlist (330 capacitors, 508.5 fF, values equal to the attofarad) with and without fill,
  and also with the fill cells flattened into the top cell (`reports/fill/pex_cc_fill_flattened.spice`
  against `reports/pex/cc/g1_bgr_k25d_pex_netlist.spice`): the floating fill clusters get no net in
  kpex's netlist. **Fill is therefore excluded from the PEX**; the 27 °C post-layout V<sub>REF</sub>
  from the filled GDS is 1.03931 V, delta 0.00000 V against the unfilled extraction. The LEF was
  not regenerated for the fill (the boundary did not change; same file, sha256 `e00ab99d…`).

### Commands

All inside the pinned container, from the repository root, paths as the run logs record them:

```
G1_WORKDIR=designs/g1-guardian/blocks/g1_bgr/layout flow/run.sh klayout -b -r g1_bgr_layout.py
flow/run.sh python3 $PDK_ROOT/$PDK/libs.tech/klayout/tech/drc/run_drc.py \
    --path=/work/designs/g1-guardian/blocks/g1_bgr/layout/g1_bgr.gds --run_mode=deep --no_density --run_dir=<dir>
flow/run.sh python3 $PDK_ROOT/$PDK/libs.tech/klayout/tech/drc/run_drc.py \
    --path=/work/designs/g1-guardian/blocks/g1_bgr/layout/g1_bgr.gds --run_mode=deep --antenna_only --run_dir=<dir>
flow/run.sh python3 $PDK_ROOT/$PDK/libs.tech/klayout/tech/lvs/run_lvs.py \
    --layout=/work/designs/g1-guardian/blocks/g1_bgr/layout/g1_bgr.gds \
    --netlist=/work/designs/g1-guardian/blocks/g1_bgr/schematic/g1_bgr_lvs.cdl --topcell=g1_bgr --run_mode=deep --run_dir=<dir>
flow/run.sh openroad -exit /work/designs/g1-guardian/blocks/g1_bgr/reports/lef/lef_check.tcl
```

(`$PDK_ROOT/$PDK` = `/foss/pdks/ihp-sg13g2` in the container; the LVS CDL is written by
`python3 schematic/make_lvs_cdl.py` from the frozen `xschem/g1_bgr.spice`; the fill step
`G1_WORKDIR=designs/g1-guardian/blocks/g1_bgr/layout flow/run.sh bash fill_g1_bgr.sh` runs between
the generator and the checks.)

### Iterations

The first complete run of the generator (the state at the start of 2026-09-19) had 16 DRC markers
and one LVS mismatch, all fixed in one pass: `M1.b` — each cascode's source strip ended 0.07 µm
from its n-tap Metal1, which also left the cascode sources floating in LVS; `M1.e` — the
collector-base strap of the diode-connected HBTs 0.20 µm from the emitter Metal1 (0.22 required
for the wide line); `M2.b` — the MSW2 gate column 0.16 µm from the MP5 drain column; `M2.d` —
three isolated 0.3 µm Via2 pads under the 0.144 µm² Metal2 minimum; one `M1.b` at a ring jumper
touching an HBT ring bridge. LVS: `pbias` shorted to `r4` because the MNI2 gate column landed on
the MP3 gate column (the small NMOS were moved and the Metal2 self-check added), and R2, RX and RB
were extracted as two halves each because the labelled mid-jog nets stopped the deck's series
combination (the jogs are now unlabelled). Second run: 0 DRC markers, LVS pass. Third pass (same
day, after the wiring-resistance estimate below): 2-cut vias on the R1/R2 path and the ring straps,
the R1 star ground, four ring-to-column straps, west columns re-pitched; 0 DRC markers, LVS pass,
extracted netlist unchanged. Fourth pass: no-fill regions, `prBoundary` and the PDK fill (above);
0 DRC markers, LVS pass, extracted netlist unchanged, PEX identical. The reports under `reports/`
are from this final, filled GDS.

## Post-layout (kpex 2.5D, capacitances)

PEX: `kpex 0.3.12` (KLayout-PEX), engine `--2.5D --mode CC`, on `layout/g1_bgr.gds` with the LVS
CDL as schematic: `G1_WORKDIR=... flow/run.sh kpex --pdk ihp_sg13g2 --gds .../layout/g1_bgr.gds
--cell g1_bgr --schematic .../schematic/g1_bgr_lvs.cdl --2.5D --mode CC --out_dir ...`
(`reports/pex/cc/kpex_plain.log`, netlist `reports/pex/cc/g1_bgr_k25d_pex_netlist.spice`:
329 capacitors between nets, 400 fF in total, 17.5 fF on `vref`). `sim/postlayout/make_pex_netlist.py` turns
it into `sim/postlayout/g1_bgr_pex.spice` (format only, see its docstring: `M$`/`Q$`/`R$` → PDK
subcircuit calls, micrometre units restored, substrate node → `vss`, port list reduced to the nine
pins). The extracted device view is the layout's: 12 PMOS half fingers of w = 5 µm, four NMOS
fingers of 10 µm, the 22 HBT units (9 dummies on vss), the resistor segments (6 × 52.5 µm for R2,
etc.) with their own heads. `sim/postlayout/run_postlayout.py all` runs the block testbench
(`../tb_g1_bgr.spice.tmpl`, same options and loads) on it; `compare.py` writes
`sim/postlayout/results/compare.md`:

| quantity | unit | schematic | post-layout (kpex CC) | delta |
| --- | --- | --- | --- | --- |
| V_REF -40 C | V | 1.03811 | 1.03930 | +0.00119 |
| V_REF 27 C | V | 1.03786 | 1.03931 | +0.00145 |
| V_REF 85 C | V | 1.03597 | 1.03760 | +0.00163 |
| V_REF 125 C | V | 1.03399 | 1.03573 | +0.00174 |
| V_REF 175 C (model extrapolated) | V | 1.03530 | 1.03716 | +0.00186 |
| TC box -40..125 C | ppm/C | 25.07 | 22.56 | -2.51 |
| TC box -40..175 C | ppm/C | 23.36 | 21.15 | -2.20 |
| I_PTAT 27 C | uA | 4.1341 | 4.1341 | 0.0000 |
| I_PTAT 175 C | uA | 6.1669 | 6.1669 | +0.0001 |
| delta-V_BE 27 C | mV | 55.073 | 55.073 | 0.000 |
| total current 27 C | uA | 22.038 | 22.036 | -0.002 |
| V_REF 27 C, hbt_bcs | V | 1.03202 | 1.03346 | +0.00144 |
| V_REF 27 C, hbt_wcs | V | 1.04523 | 1.04668 | +0.00145 |
| TC box -40..125 C, hbt_bcs | ppm/C | 40.62 | 37.37 | -3.25 |
| TC box -40..125 C, hbt_wcs | ppm/C | 11.43 | 9.84 | -1.59 |
| start-up 1 ms ramp, 27 C: t(V_REF = 0.93 V) | ms | 0.5198 | 0.5188 | -0.0011 |
| start-up: V_REF at 3 ms | V | 1.03786 | 1.03931 | +0.00145 |
| start-up: max V_REF | V | 1.03792 | 1.03942 | +0.00150 |
| PSRR DC (1 Hz), 27 C | dB | -103.0 | -103.0 | +0.1 |
| PSRR 1 kHz, 27 C | dB | -82.3 | -75.3 | +6.9 |
| PSRR 100 kHz, 27 C | dB | -42.3 | -35.4 | +6.9 |
| PSRR 1 MHz, 27 C | dB | -25.0 | -18.5 | +6.5 |
| PSRR 1 kHz, -40 C | dB | -82.4 | -75.5 | +7.0 |
| PSRR 1 kHz, 175 C | dB | -81.8 | -75.0 | +6.8 |

Reading:

- **V_REF is +1.2 .. +1.9 mV higher post-layout (+0.14 % at 27 °C)** and I_PTAT, ΔV_BE and the
  supply current are unchanged. The shift is the resistor heads: the layout's R2 is six 52.5 µm
  segments with twelve contact heads, the schematic's a single 315 µm element with two, while R1
  is one segment in both. With the PDK's `rzspec` = 35 Ω·µm per head that is +350 Ω on 82 kΩ,
  i.e. +0.43 % on R2/R1, times the 0.335 V PTAT term = +1.44 mV at 27 °C (matches). The added
  PTAT tilt (+4.6 ppm/°C) moves the box TC from 25.1 to 22.6 ppm/°C at the nominal corner and
  keeps every HBT corner under the 50 ppm/°C criterion.
- **PSRR above DC is a pessimistic bound.** Removing every parasitic capacitor from the post-layout
  netlist gives back the schematic PSRR (variant B: −82.1 dB at 1 kHz), so the 7 dB come from the
  extracted capacitances, not from the device geometry. The 2.5D engine has no well conductor: the
  45 fF it reports between `pbias` and the substrate lie, in the real device, over the mirror
  n-well at vdd (and the gate-to-channel part is already in the MOS model); referencing the
  substrate capacitors of the n-well nets (`pbias pcasc d1..d5 det`) to vdd instead recovers 4 dB
  (variant A: −79.6 dB at 1 kHz). Both variants: `sim/postlayout/results/psrrvar_summary.csv`,
  netlists in `sim/postlayout/variants/`. DC PSRR is unchanged at −103 dB.
- **Wiring resistance is estimated, not extracted.** The RC run (`--mode RC`, `reports/pex/rc/`)
  is kept as evidence only: kpex 0.3.12 splits every net into a resistor tree with per-terminal
  `P` nodes but leaves the device instances on the unsplit net node, so only the nine port nets
  (whose label is on the tree) connect to their devices through the tree; every internal net's
  tree floats and the operating point is singular. Variant C (`run_postlayout.py wire`,
  `sim/postlayout/results/wire_summary.csv`, netlist `variants/pex_wire.spice`) therefore inserts
  hand-counted series resistances from the PDK LEF values (Metal2/Metal3 0.103 Ω/sq, 20 Ω per via
  cut, 10 Ω per 2-cut pair): 60 Ω from R1's top to the Q2 emitters, 41 Ω from R1's bottom to the
  HBT ring, 81 Ω / 48 Ω at the two ends of R2, 15 Ω between the HBT ring and the vss pin. Result
  at 27 °C nominal: V_REF 1.03734 V, I_PTAT 4.1029 µA (−0.75 %), TC box 27.9 ppm/°C. The two
  layout effects, the resistor heads (+1.45 mV) and the wiring (−2.0 mV), nearly cancel: the best
  estimate for the fabricated block is **V_REF ≈ 1.037 V at 27 °C, I_PTAT ≈ 4.10 µA**, within
  0.1 % / 0.8 % of the schematic, far inside the ±1 % corner and 1.8 % mismatch spread. Before the
  third layout pass the same count gave about 140 Ω in the R1 loop plus a ring return drop of
  about 0.7 mV entering ΔV<sub>BE</sub> (R1 returned to the bus, the Q1 emitter to the ring);
  the star ground and the 2-cut vias are what brought it to the numbers above.

## Checks

| Check | Status | Evidence |
| --- | --- | --- |
| Schematic netlists without unresolved symbols | passed | `xschem/g1_bgr.spice` |
| Operating point, nominal (−40, 27, 175 °C) | passed | `sim/logs/op_typ_*.log` |
| V<sub>REF</sub>(T) at 27 process corners × 3 supplies | passed (numbers above) | `sim/results/temp_summary.csv` |
| TC ≤ 50 ppm/°C (box) over −40..125 °C at every corner | failed at 1 of 9 HBT×RES pairs: hbt_bcs/res_wcs gives 51 .. 52 ppm/°C; 78 of 81 runs pass | `sim/results/temp_summary.csv` |
| Start-up, 1 ms ramp, 81 corner/temperature points | passed, 81/81 (V_REF 1.02 .. 1.05 V at 3 ms, reached 0.93 V 0.48 .. 0.61 ms into the ramp) | `sim/results/startup_summary.csv` |
| Start-up, 100 ms ramp, 29 points | passed, 29/29 (reached 0.93 V at 48 .. 58 ms, i.e. at V_DD ≈ 1.5 .. 1.7 V) | `sim/results/startupslow_summary.csv` |
| PSRR at DC and 1 kHz, 81 points | passed (numbers above) | `sim/results/psrr_summary.csv` |
| Monte Carlo 300 samples, mismatch, 27 °C | passed (numbers above) | `sim/results/mc_summary.csv` |
| Cryogenic extrapolation to −196 °C | run, **model extrapolated**, no pass criterion | `sim/results/extrap_summary.csv` |
| Loop stability (AC loop gain / phase) | not run | |
| Nominal standalone C-PEX AC output noise (2026-09-21) | passed execution; simulated 196.046 µV RMS over 1 Hz–10 MHz; no acceptance budget adopted | `sim/qualification/runs/bgr_noise_20260921_01/manifest.json` |
| Layout generator self-check (Metal2 spacing between nets) | passed (0 conflicts) | `layout/g1_bgr_layout.py` (aborts on a conflict) |
| Fill, PDK filler inside the macro (Activ, GatPoly, Metal1-3; no-fill over the matched structures) | run: 1 / 1 / 157 / 104 / 85 fill shapes | `reports/fill/fill_g1_bgr.log` |
| DRC on the filled GDS, `run_drc.py --run_mode=deep --no_density` (main table + `sg13g2_maximal` extra rules incl. the fill rules, recommended rules on) | **passed, 0 markers** | `reports/drc/drc_run_2026_09_19_10_53_29.log`, `reports/drc/g1_bgr_g1_bgr_main.log`, `reports/drc/g1_bgr_g1_bgr_sg13g2_maximal.log`, `reports/drc/g1_bgr_g1_bgr_full.lyrdb` |
| Antenna, `run_drc.py --run_mode=deep --antenna_only` | passed, 0 markers | `reports/antenna/drc_run_2026_09_19_10_57_13.log`, `reports/antenna/g1_bgr_g1_bgr_antenna.lyrdb` |
| Density | not run at block level (the chip-level check after the chip fill; the macro is 0.7 % of the die) | |
| LVS on the filled GDS, `run_lvs.py --run_mode=deep` vs `schematic/g1_bgr_lvs.cdl` (strict port mode, no purge) | **passed**, same 32 devices as before the fill | `reports/lvs/lvs_run_2026_09_19_10_53_29.log`, `reports/lvs/g1_bgr.log`, `reports/lvs/g1_bgr_extracted.cir` |
| LEF loads with the PDK tech LEF (OpenROAD 26Q3 `read_lef`, macro and nine pins listed, no warning) | passed | `reports/lef/lef_check.log` (`reports/lef/lef_check.tcl`) |
| LibreLane placement of the macro in the ring | not run (integration, `../g1_padring/INTEGRATION.md`) | |
| PEX, kpex 2.5D `--mode CC` (filled GDS; fill excluded by the tool, see "Fill") | run | `reports/pex/cc/kpex_plain.log`, `reports/pex/cc/g1_bgr_k25d_pex_netlist.spice`, `reports/fill/pex_cc_fill_flattened.spice` |
| PEX, kpex 2.5D `--mode RC` | run, **not usable** (device terminals not attached to the resistor trees, see above) | `reports/pex/rc/kpex_plain.log`, `reports/pex/rc/g1_bgr_k25d_pex_netlist.spice` |
| Post-layout V<sub>REF</sub>(T) −40 .. 175 °C, hbt_typ/bcs/wcs, mos_tt, res_typ, 3.3 V | passed (TC box 9.8 .. 37.4 ppm/°C, criterion 50) | `sim/postlayout/results/temp_summary.csv`, `sim/postlayout/results/compare.md` |
| Post-layout operating points −40, 27, 125, 175 °C and 1:4 test mode | passed (V_REF 0.9160 V in test mode) | `sim/postlayout/logs/op_typ_*.log` |
| Post-layout start-up, 1 ms ramp, 27 °C nominal | passed (V_REF 1.0393 V at 3 ms, 0.93 V at 0.519 ms) | `sim/postlayout/results/startup_summary.csv` |
| Post-layout PSRR, −40/27/175 °C nominal | run (−103 dB DC, −75 dB at 1 kHz, pessimistic bound, see above) | `sim/postlayout/results/psrr_summary.csv`, `psrrvar_summary.csv` |
| Wiring resistance, hand-counted variant C (estimate, not an extraction) | run (V_REF 1.0373 V, I_PTAT −0.75 % at 27 °C) | `sim/postlayout/results/wire_summary.csv`, `sim/postlayout/logs/wire_*.log` |
| Post-layout 27 corners ×3 supplies, −40..125 °C (2026-09-21) | passed, 81/81; maximum TC 49.341 ppm/°C | `sim/qualification/runs/bgr_corners81_20260921_01/manifest.json` |
| Post-layout mismatch temperature sweep (2026-09-21) | **failed TC: 54/100**; all 100 simulations complete, worst TC 178.540 ppm/°C | `sim/qualification/README.md`, `sim/qualification/summary.csv` |
| Post-layout 1 ms / 100 ms startup, three screened tuples (2026-09-21) | passed, 6/6 endpoints; real downstream loads and dips not run | `sim/qualification/runs/bgr_startup6_20260921_01/manifest.json` |

Extractor view against the schematic (`reports/lvs/g1_bgr_extracted.cir`): the deck combines the
parallel PMOS half fingers (`W=10u`) and NMOS fingers (`W=20u`), the eight Q2 units (`m=8`) and the
nine dummies (`m=9`), and the series `rppd`/`rhigh` segments (R2 `l=315u`, RX `192u`, RB `500u`,
RDET `735u`); MOS terminals are written S G D B; the resistor and HBT substrate terminal is the
`vss` net (the schematic's `sub!`); `AS/AD/PS/PD` are extracted and not compared. The CDL is the
frozen xschem netlist converted by `schematic/make_lvs_cdl.py` (format only) plus the nine dummy
HBTs `QDUM1..9` with all four terminals on `vss`.

## Unverified

- Behaviour at 77 K: the run to −196 °C only exercises the PDK model outside its
  characterised range. The measured SG13G2 HBT ideality factor rises strongly below
  ~100 K, so the PTAT term (and V<sub>REF</sub>) at 77 K is a bench result, not a
  design value. The block's job there is to stay biased and expose `vbe`, `dvbe`,
  `iptat` for measurement.
- Package stress shift of V<sub>BE</sub> (QFN, epoxy lid): not modelled; calibrate
  after packaging.
- No curvature correction: the residual bow of V<sub>REF</sub>(T) is what the model
  gives (tables above); no second-order or β-based term is built.
- Absolute V<sub>REF</sub> spread: the mismatch MC gives the σ above; process shift of
  the zero-TC point (HBT and `rppd` corners move V<sub>REF</sub> by ±1 %) is not
  trimmed. See "Trim decision".
- `VREF` is not buffered: output impedance ≈ R2 + 1/g<sub>m</sub> ≈ 88 kΩ. Every
  1 nA of load or pad leakage moves it by 88 µV. The `G1_TRIP` string DACs must not
  load it directly; the analog pad ESD leakage at 175 °C should be checked against
  this in the top-level simulation.
- Base currents of Q1 and Q2 are drawn from the Q1 collector node (inherent to the
  op-amp-less cell): the branch current ratio carries a 2/β term (≈ 0.2 .. 0.5 % over
  temperature with the model's β of 400 .. 1200), which is not PTAT. It is included
  in all numbers above but is a systematic term the two-point sensor calibration does
  not remove exactly.
- Wiring resistance is a hand count from the PDK LEF values (variant C), not an extraction (kpex
  RC mode unusable). New capacitance-PEX corner, mismatch-temperature and screened slow-startup
  results are in `sim/qualification/README.md`; loaded joint behavior remains incomplete.
- The post-layout PSRR above DC is a bound, not a value (2.5D engine without a well conductor).
- Matching geometry (common centroid, dummies, one orientation) does not establish silicon
  mismatch: schematic and extracted-unit MC use the PDK per-device model, which does not
  include physical spatial correlations or gradients.
- Density (chip level after the chip fill; the block fill adds 157/104/85 Metal1/2/3 squares and
  the matched arrays stay unfilled by design), the macro inside the ring (LibreLane run, PDN straps
  to the Metal3 power bars) and the top-level LVS with the macro CDL: not run here.
- Fill coupling is not in the PEX (kpex assigns no net to the floating fill); the fill sits over
  RDET, the buses and the channels only, never over the matched devices.
- Layout parasitics of the top-level wiring to the `VREF` pad and to `G1_TRIP`/`G1_T2F`: not part
  of this macro.

## Trim decision

Question: does the ±2 °C sensor goal need a 3-bit V<sub>REF</sub> trim? **No.** The
300-sample mismatch MC gives σ(V<sub>REF</sub>) = 19 mV (1.8 %), σ(I<sub>PTAT</sub>) =
σ(ΔV<sub>BE</sub>) = 5.1 %, dominated by the HBT area mismatch of the model card (10 %
σ per unit device, 1/√8 on the eight-unit side). In the sensor both quantities enter as
gain factors, f ∝ ΔV<sub>BE</sub>/V<sub>REF</sub>: a constant gain error is
PTAT-shaped and is removed exactly by the two-point (or PTAT-gain) calibration after
packaging. An analog trim would add nothing the calibration does not already do; the
trim that helps the sensor is the digital PTAT-shaped gain correction in the
calibration procedure, not a resistor tap.

An R2 trim is only useful for the absolute reference seen by `G1_TRIP`'s DACs and the
`VREF` pad: untrimmed 3σ ≈ ±5.5 % (mismatch) plus ±1 % (HBT/`rppd` process corners).
A 3-bit tap on R2 (±6 % range, 1.7 % steps) would bring that to about ±1 %. Cost: three
`rppd` segments, three HV switches, three register bits. Recommendation: draw the taps
on day 3 only if `G1_TRIP` asks for better than ±6 % absolute threshold accuracy;
otherwise leave V<sub>REF</sub> untrimmed and record each part's value from pin 18.

Note: the copied upstream netlist `source/2AMLogic-sg13g2-bandgap/bandgap_top.spice` had its xschem `sch_path`/`sym_path` comment lines removed because they carried the upstream author's machine paths; no circuit content changed.

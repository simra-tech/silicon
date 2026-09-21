# G1_DOSE

State: **three variants drawn; plan-of-record default `g1_dose_pair_pcell` is
DRC-clean (full rule set) and LVS-clean; the enclosed-layout (ELT) cell is
LVS-clean and fails one DRC rule (`Gat.f`) that a ring gate cannot satisfy and
is kept as the approval-gated option** (2026-09-18). **Placeable macro
`g1_dose_macro` (30 × 30 µm, Metal3 pins, LEF, own fill) around the default
cell: DRC 0, LVS pass, LEF loads in OpenROAD** (2026-09-19). Pad routing is
the chip level's; no PEX.

The block is the total-dose canary: two NMOS devices with a shared gate
(`G_SHARED`, pin 19), common source and body on `VSS`, and the two drains on
analog pads `D_STD` (pin 20) and `D_ELT` (pin 21). Ionising dose builds up
positive charge in the shallow-trench isolation and the gate oxide and opens
a parasitic drain-source path along the STI edge of a standard NMOS; the
ratio of the two off-currents is a dose indicator that is independent of
temperature and process to first order. The on-chip log-ratio readout is not
built this week (PLAN D5). Pin names are frozen; in variants 2 and 3 the pad
named `D_ELT` carries the drain of the second device (HV or narrow).

| # | Cell | Devices (single finger) | Drains | DRC full set | LVS | Role |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | `g1_dose_pair` (`layout/g1_dose.gds`) | drawn ELT NMOS L=0.50 µm (extractor W 3.98 µm) + `sg13_lv_nmos` w=3.98u l=0.5u | ELT → `D_ELT`, LV → `D_STD` | **failed: `Gat.f` only** (main set clean) | passed | approval-gated option |
| 2 | `g1_dose_pair_pcell` (`layout/g1_dose_pcell.gds`) | `sg13_hv_nmos` w=3.98u l=0.45u (3.3 V thick oxide, minimum L) + `sg13_lv_nmos` w=3.98u l=0.13u (minimum L) | HV → `D_ELT`, LV → `D_STD` | **passed, 0 errors** | passed | **plan-of-record default** |
| 3 | `g1_dose_pair_nw` (`layout/g1_dose_nw.gds`) | `sg13_lv_nmos` w=0.30u + w=3.98u, both l=0.13u | narrow → `D_ELT`, wide → `D_STD` | **passed, 0 errors** | passed | optional |

Why variant 2 is the default: the published TID data for this process (reading
list outside the repository) show the 3.3 V thick-oxide NMOS moving by orders
of magnitude at a few hundred krad while the 1.2 V device moves by less than a
decade, so the HV/LV pair gives the largest dose signal that can be drawn with
PCells only, and the LV device doubles as the low-sensitivity reference. Variant
3 is the pure STI-edge probe: edge leakage adds the same absolute current to
both devices, so the narrow device's off-current moves by a much larger factor.
Variant 1 is the textbook canary (edge-free reference) but violates `Gat.f`.

**What switches the default:** a written foundry statement that a closed
GatPoly ring over Activ (bends on Activ, `Gat.f`) is accepted on the open
shuttle switches the default to variant 1 with variant 2 as the second pair if
pins are freed (PLAN section 7). A statement that `Gat.f` is binding, or no
answer by the day-4 analog freeze, keeps variant 2. The three cells share the
pin map, so the choice is a top-level instantiation change only.

## Built against

| Item | Value | Established by |
| --- | --- | --- |
| PDK | IHP SG13G2 open PDK, commit `84374023ee8b4b126bebbba67fcbada0a9c0ff0b` | `sim/logs/pdk_commit.txt` |
| ngspice | 46, KLU build, PSP 103.6 via OSDI (`osdi/psp103.osdi`) | `sim/logs/ngspice_banner.txt` |
| KLayout | 0.30.9, PDK PCell library `SG13_dev`, PDK DRC and LVS decks | `reports/*/` logs |
| Container | `flow/run.sh` image pinned in `../../PLAN.md` section 2 | — |

## Source

None. No ELT PCell or community cell exists for SG13G2; the cell is drawn from
the PDK design-rule values in `layout/g1_dose_layout.py`. The standard device
is the PDK PCell `nmos`.

## Laid out

### Variants 2 and 3: PCells only

`layout/g1_dose_pcell_layout.py` (KLayout batch Python, run in the container;
it imports the drawing helpers from `g1_dose_layout.py`) writes
`layout/g1_dose_pcell.gds` (top `g1_dose_pair_pcell`, 7.0 × 6.3 µm) and
`layout/g1_dose_nw.gds` (top `g1_dose_pair_nw`, 6.1 × 5.9 µm). Each device is
a PDK PCell (`nmosHV` or `nmos`, `ng = 1`) with: a 0.30 µm GatPoly contact
pad below its end cap (Cont, Metal1, Via1), a 0.30 µm Metal1/Via1 strip over
the PCell drain Metal1 leaving on Metal2 (west for the first device, east for
the second), a horizontal Metal1 source strap to its own p+ substrate ring
(Activ + pSD 0.30 µm, contact ring, 0.26 µm Metal1, `VSS`), and the shared
gate on a 0.30 µm Metal2 strip between the two pads (`G_SHARED`). The two
rings are 0.60 µm apart and bridged on Metal1. The HV device's ring keeps
TGO.b 0.27 µm from its `ThickGateOx` (clearance 0.60/0.85 µm from the Activ
box instead of 0.30/0.75 for the LV device). DRC iterations: `pSD.b` (ring
spacing arithmetic), `M1.b`/`M1.e` (drain Metal1 to ring Metal1), `V1.c`
(narrow device's drain Metal1 too small for the via); all fixed in the
generator. Extracted netlists: `reports/lvs_pcell/g1_dose_pcell_extracted.cir`
(`sg13_hv_nmos L=0.45u W=3.98u`, `sg13_lv_nmos L=0.13u W=3.98u`) and
`reports/lvs_nw/g1_dose_nw_extracted.cir` (`W=0.3u` and `W=3.98u`, `L=0.13u`),
both matching the hand-written CDLs `schematic/g1_dose_pair_pcell.cdl` and
`schematic/g1_dose_pair_nw.cdl`.

### Variant 1: the drawn ELT

`layout/g1_dose_layout.py` (KLayout batch Python, run in the container) writes
two files:

- `layout/g1_dose.gds`, top cell `g1_dose_pair`, 8.2 × 7.1 µm: the ELT with
  L = 0.50 µm and the standard device, each in its own p+ substrate ring, with
  Metal2 terminals `D_ELT` (west), `G_SHARED` (between the rings), `D_STD`
  (east) and Metal1 `VSS` on the rings (labels on 8/25 and 10/25, pins on 8/2
  and 10/2).
- `layout/g1_elt_l130_test.gds`, top cell `g1_elt_l130_test`: the same ELT
  generator at the minimum gate length L = 0.13 µm, for DRC feasibility only.

### ELT geometry (L = 0.50 µm cell)

Standard layers only: Activ 1/0, GatPoly 5/0, Cont 6/0, Metal1 8/0, Via1 19/0,
Metal2 10/0, pSD 14/0. No nSD, no ThickGateOx, no nBuLay, no drawn PWell: the
same layer set the `nmos` PCell uses, so the LVS deck derives an LV NMOS
(`ngate_lv = GatPoly ∩ Activ ∖ pSD ∖ ThickGateOx`; nSD would exclude the device).

| Element | Geometry | Rule driving it |
| --- | --- | --- |
| Drain | inner Activ square, side d = 0.42 µm, one 0.16 µm contact at the centre | Cnt.a 0.16, Cnt.f 0.11 contact-to-gate on both sides (0.38 minimum) |
| Gate | closed GatPoly ring, inner half-side 0.21, outer 0.71 µm, width L = 0.50 µm | Gat.a 0.13 minimum; 0.50 chosen for DIBL and low pre-rad leakage |
| Source | Activ ring 0.45 µm wide outside the gate (Activ half-side 1.16 µm); contact ring at radius 0.90 µm, 0.34 µm pitch, 4 corner + 3 or 4 per side | Act.c 0.23, Cnt.f 0.11, Cnt.c 0.07 |
| Gate tab | one 0.30 µm GatPoly strip from the ring across the source ring (+x) to a pad on field oxide; contact 0.14 µm past the Activ edge | Gat.c 0.18 end cap, Cnt.e 0.14, Cnt.d 0.07 |
| Substrate ring | Activ + pSD ring 0.30 µm wide, inner half-side 1.71 µm, contact ring, 0.26 µm Metal1 ring; Metal1 bridges to the source ring on ±y | pSD.a 0.31, pSD.d 0.18, pSD.j 0.30 to the gate, Act.b 0.21, M1.b 0.18 |
| Exits | drain and gate on 0.30 µm Metal2 through Via1 (0.05 µm Metal1 enclosure), so both Metal1 rings stay closed | V1.c1 0.05, M2.a 0.20 |

The standard device is the PCell `nmos` with `w = 3.98u`, `l = 0.5u`,
`ng = 1` (a single finger: exactly two STI edges), plus a GatPoly contact pad
below its end cap, a widened Metal1/Via1 drain strip to Metal2, a Metal1
source strap to its own substrate ring, and the ring itself. The two n+
regions are 2.0 µm apart with both p+ rings between them; the two rings are
bridged on Metal1 so `VSS` is one net.

### W/L convention and the extractor's view

Three widths exist for the ring device and they must not be confused:

1. **Mean ring perimeter** (drawn, for the CDL before extraction):
   W = (P_inner + P_outer)/2 = 4·(d + L) = 4·(0.42 + 0.50) = **3.68 µm** for
   a square ring; L = 0.50 µm is the ring width.
2. **What the KLayout LVS extractor reports** (PDK deck `mos_extraction.lvs`,
   generic `mos4` extractor; W = half the length of all gate edges shared with
   source/drain, L = gate area / W): **`sg13_lv_nmos` W = 3.98 µm,
   L = 0.496231 µm**, extracted netlist `reports/lvs_pair/g1_dose_extracted.cir`.
   The 0.30 µm excess over (1) is the gate tab: where it crosses the 0.45 µm
   source ring its two side edges border source, and 0.30 µm of the ring's
   outer edge no longer does, (2·0.45 − 0.30)/2 = 0.30 µm. L = (ring area
   1.840 µm² + tab-over-Activ 0.135 µm²)/3.98 µm = 0.4962 µm. The tab region
   is a source-to-source MOS in parallel with nothing; it is not a second
   device in the extracted netlist (the gate polygon is one shape).
3. **Electrical W_eff.** The corner regions of a ring do not conduct as a
   straight channel of width L. Following the Giraldo/Anelli decomposition of
   the enclosed gate into straight sides and corner regions, with the corner
   region treated as radial conduction between an inner radius αL (the
   fraction of the corner the straight-side current spreads into) and the
   outer radius L:

   W_eff = 4·d + 4·L·(π/2)/ln(1/α)

   With α = 0.05: W_eff = 1.68 + 1.05 = **2.73 µm** (74 % of the mean
   perimeter, 69 % of the extractor's W). This is a derivation written here,
   not a transcription of the published formula: the published expression
   (with its corner factor K = 7/2 for the cut-corner geometry) was not
   available in this session and must be checked against the paper before
   the number is used for anything but a bound. The ratio of drain currents
   at equal V_GS − V_T in strong inversion measured pre-irradiation gives
   W_eff,ELT / W_std directly and supersedes all three numbers above.

The standard device is sized to the extractor's W (2), so the two devices are
identical in the extracted netlist except for L (0.4962 vs 0.500) and the
junction areas, and the pre-irradiation off-current ratio is 1.00 by
construction in simulation. If the true W_eff is (3), the measured pre-rad
ratio I_STD/I_ELT will be about 1.4; that is a calibration constant, not a
fault, and the ratio versus dose is what matters.

The `schematic/g1_dose_pair.cdl` used for LVS is written to the extractor's
values (PLAN risk R4, option c):

```
MSTD D_STD G_SHARED VSS VSS sg13_lv_nmos w=3.98u l=0.5u ng=1 m=1
MELT D_ELT G_SHARED VSS VSS sg13_lv_nmos w=3.98u l=0.496231u ng=1 m=1
```

### Recognition spike, what was tried

| Step | Result |
| --- | --- |
| Square ring, gate tab across the source ring, CDL with mean-perimeter W = 3.68 µm | recognised as `sg13_lv_nmos`, topology matched, LVS **failed** on W (3.98 vs 3.68) and L (0.4962 vs 0.5) |
| Same layout, CDL written to the extractor's W and L | LVS **passed** (`reports/lvs_pair/`) |
| (a) octagonal ring, (b) 45° free corners | not drawn: DRC rule `Gat.f` is implemented as "every GatPoly ∩ Activ polygon must be an axis-aligned rectangle" (`sg13g2_maximal.drc`, `ext_rectangles(true, …, inverted: true)`), so any closed ring, with or without cut corners, fails it identically; recognition is not the problem |
| Ring at L = 0.13 µm (`g1_elt_l130_test.gds`) | drawable inside all rules except `Gat.f`; mean-perimeter W = 2.20 µm; not extracted (test cell has no pair) |

### The DRC finding: `Gat.f`

`run_drc.py --run_mode=deep --no_density` on `g1_dose_pair` reports exactly
one violation, `Gat.f`: "45-degree and 90-degree angles for GatPoly on Activ
area are not allowed", flagged on the ring gate polygon
(`reports/drc_pair/g1_dose_g1_dose_pair_main.log`, marker database
`g1_dose_g1_dose_pair_full.lyrdb`). The rule is a bend-free-gate rule: a
gate must be a straight stripe over Activ. A closed annular gate has eight
bends on Activ by construction, so no ELT of this kind can pass it; cutting
the Activ at the corners would satisfy the checker but re-creates STI edges
along the gate stripes, which removes the reason to draw the device. The
deck lists `Gat.f` in its **extra rule set** (`docs/extra_rules.md`: rules
"not part of the main set … not verified or tested"); it is in neither the
main nor the precheck set. With `--disable_extra_rules` the cell is clean
(`reports/drc_pair_noextra/`). The rule name follows the foundry's own
numbering, so the safe reading is that it is a real process rule with an
unverified checker, not a checker artefact. Per `../../AGENTS.md` a failing
rule is a design problem; this README records it, it does not waive it.

Options for the go/no-go (not decided here):

1. Submit the ring gate with `Gat.f` documented and ask the foundry whether a
   bent gate over Activ is manufacturable on the open shuttle (the process
   has a proprietary rad-hard library with enclosed devices, so the fab knows
   the structure). Risk: rejection at precheck, or a silent yield problem.
2. Replace the ELT by a DRC-legal edge-sensitivity pair: two standard PCells
   at the same L with very different W (e.g. 0.15 µm and 3.98 µm). STI-edge
   leakage adds the same absolute current to each device, so the narrow
   device's off-current moves by a much larger factor; the ratio is again a
   dose indicator, weaker but clean. Pins and readout unchanged.
3. Pins-only fallback of PLAN R4 with the cell as a black box: same DRC
   problem, so it is not a fallback for `Gat.f`.

## Macro for integration: `g1_dose_macro`

`layout/g1_dose_macro.py` (helpers in `layout/macro_common.py`, both run in
the container) wraps the cell of record `g1_dose_pair_pcell` into the
placeable macro **`g1_dose_macro`, 30 × 30 µm, origin (0, 0)**, and writes
`layout/g1_dose_macro.gds` (flat, one cell), `layout/g1_dose_macro.lef`,
`layout/g1_dose_macro.vh` (black box) and `layout/lef_check.tcl`. The
conventions are those of `../g1_padring/INTEGRATION.md` and
`../g1_bgr/layout/g1_bgr.lef`. The DUT macro (`../g1_dut/layout/g1_dut_macro.py`)
uses the same helper module, so the two devices are two macros, not one
combined cell: each block keeps its own evidence.

| Pin | LEF | Metal3 RECT (µm) | Connection inside |
| --- | --- | --- | --- |
| `G_SHARED` | INPUT, SIGNAL | west edge, `0 12.46 1.5 12.76` | Via2 on the shared-gate Metal2 strip |
| `D_ELT` | INOUT, SIGNAL | west edge, `0 14.85 1.5 15.15` | Via2 on the HV drain Metal2 stub |
| `D_STD` | INOUT, SIGNAL | west edge, `0 19.02 1.5 19.32` | Via2 on the LV drain Metal2 stub, Metal3 north over the cell, then west |
| `vss` | INOUT, GROUND | south bar, `0 0 30 2` | Metal1 patch + Via1 + Metal2 + Via2 on the LV device's p+ ring (SE corner), Metal3 south |

Signal pins are 1.5 × 0.30 µm Metal3 stubs on the west edge (the device pads
19-21 are on the west side), labels on 30/25, pin shapes on 30/2. OBS: Metal1
and Metal2 over the whole macro, Metal3 from (1.8, 2.6) to (30, 30). No
obstruction on Metal4 and above (no macro metal there). prBoundary 189/4 =
the macro box. The device cell sits at (12.98, 12.61), bbox (11.48, 11.83)-
(18.52, 18.17); the device's own Metal1/Metal2 labels are removed in the flat
macro so every net is named once, by its Metal3 label. `lef_check.tcl` loads
the PDK tech LEF and the macro LEF in OpenROAD and prints masters, pins and
obstructions: `reports/lef_check_g1_dose_macro.log` shows `MASTER
g1_dose_macro BLOCK 30.0 x 30.0 um`, the four pins with the directions above
and the three OBS layers.

**Fill.** No-fill shapes (`Activ 1/23`, `GatPoly 5/23`, `Metal1 8/23`,
`Metal2 10/23`, `Metal3 30/23`, `Metal4 50/23`, `Metal5 67/23`, `TopMetal1
126/23`, `TopMetal2 134/23`, `NoMetFiller 160/0`, the same set the PDK
`NoFillerStack` PCell writes) cover the device cell with a 5 µm margin,
(6.48, 6.83)-(23.52, 23.17), plus Metal3 no-fill over the pin-access bands
(x < 2.3, y < 3.1) so Metal3 fill stays inside the Metal3 obstruction. The PDK
filler (`libs.tech/klayout/tech/scripts/filler.py`, `-rd no_topmetal`, log
`reports/filler_g1_dose_macro.log`) then fills the rest. Two facts about that
script decided the procedure: it fills only the *holes of the `EdgeSeal`
layer*, so a temporary copy gets an EdgeSeal frame whose hole is the macro box
inset by 1.2 µm (chip metal next to the macro then stays ≥ 1.2 µm from macro
fill: `M1Fil.c` 0.42, `GFil.d` 1.1); and it places a fill cell only where its
whole tile (cell + spacing: 2.5 µm Metal1/2, 3 µm Metal3, 5 µm Activ, lattice
anchored at the layout origin) fits. Only the datatype-22 fill on **Activ,
GatPoly, Metal1, Metal2, Metal3** is copied back, flattened: 4 Activ (3.4 ×
3.4), 4 GatPoly (5 × 1.4), 36 Metal1, 36 Metal2 and 17 Metal3 (1 × 1) shapes.
Metal4/5 and TopMetal1/2 carry no macro fill on purpose: the LEF does not
obstruct them, the chip filler fills them over the footprint (proven in
`../g1_padring/reports/density_nofill_probe/`) and the no-fill shapes keep it
off the transistors. Macro fill on those layers would sit under chip routing
the router cannot see.

**Fill and LVS.** The LVS deck does not ignore the fill datatypes: it joins
`activ_filler`, `gatpoly_filler` and `metal*_filler` into the connectivity
layers (`lvs/rule_decks/layers_definitions.lvs`) and excludes uncontacted
GatPoly fill from gates (`mos_derivations.lvs`). Fill islands are therefore
floating nets that the simplification purges; the check that they add
nothing is the LVS of the filled macro itself: it passes and its extracted
netlist (`reports/lvs_macro/g1_dose_macro_extracted.cir`) has the same two
devices with the same parameters as the unfilled cell.

One iteration: the first flat macro removed all Metal2.pin (10/2) shapes and
the 0.30 µm Metal2 via patch was below the Metal2 minimum area (`M2.d`
0.144 µm²); patch now 0.40 µm, and 10/2 is kept (see the DUT README for why
that matters to the DRC deck).

## Simulated

### Variants 2 and 3, off-current baseline

`sim/gen_offcurrent_variants.py` / `sim/run_offcurrent_variants.sh` (36 runs),
netlists derived from the extracted ones by `sim/make_sim_netlist.sh pcell|nw`
(device names and pin order edited for ngspice, see the script). Model lines
exactly as used, `<corner>` ∈ {`mos_tt`, `mos_ss`, `mos_ff`}, both libraries
carry the same corner names:

```
.lib /foss/pdks/ihp-sg13g2/libs.tech/ngspice/models/cornerMOSlv.lib <corner>
.lib /foss/pdks/ihp-sg13g2/libs.tech/ngspice/models/cornerMOShv.lib <corner>
pre_osdi /foss/pdks/ihp-sg13g2/libs.tech/ngspice/osdi/psp103.osdi
.option gmin=1e-16 abstol=1e-16 reltol=1e-4
```

VGS = 0, source and body 0 V, −40/27/85/125 °C and (model extrapolated)
150/175 °C. Full tables in `sim/results_variants.md`; `mos_tt` rows
(simulated, pre-irradiation, PSP has no STI-edge transistor):

| T (°C) | HV `D_ELT` @0.1 V | HV @1.2 V | HV @3.3 V | LV `D_STD` @0.1 V | LV @1.2 V | LV/HV @0.1 V | narrow @0.1 V | wide @0.1 V | wide/narrow |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| −40 | 0.18 fA | 0.57 fA | 2.6 fA | 0.68 pA | 5.0 pA | 3800 | 26 fA | 0.68 pA | 26 |
| 27 | 79 fA | 0.15 pA | 0.44 pA | 40 pA | 0.16 nA | 500 | 1.8 pA | 40 pA | 23 |
| 85 | 4.2 pA | 7.0 pA | 17 pA | 0.56 nA | 2.1 nA | 135 | 27 pA | 0.56 nA | 21 |
| 125 | 38 pA | 61 pA | 0.13 nA | 2.5 nA | 9.3 nA | 66 | 0.13 nA | 2.5 nA | 19 |
| 175 (extrap.) | 0.39 nA | 0.61 nA | 1.2 nA | 12.7 nA | 45 nA | 33 | 0.71 nA | 12.7 nA | 18 |

Corners move every current by about ×0.06 (ss) to ×6 (ff) at 27 °C; the
ratios move less (LV/HV 175 … 500, wide/narrow 16 … 35 at 27 °C).

What this says for the measurement: the thick-oxide device's pre-rad
off-current is **tens of fA at room temperature**, far below any analog pad's
ESD-diode leakage (PLAN R7, not yet simulated), so on `D_ELT` the bench will
see the pad leakage until dose lifts the device current above it; that is
acceptable for a canary whose signal is a rise by decades, but the pre-rad
point is a pad measurement, not a device measurement. The LV device at 40 pA
(27 °C, 0.1 V) is measurable with a pA-class SMU. The HV gate may see the
full 3.3 V of the analog pad; the exposure bias for the HV device is
`G_SHARED` = 3.3 V (its rail), which puts 3.3 V on the LV gate as well: the
LV device is a 1.2 V core transistor and 3.3 V on its 2 nm-class oxide is an
over-stress; either expose at 1.2 V (LV-safe, HV under-biased) or accept LV
gate stress; decide in the measurement plan, not here. The `l = 0.13u` LV
device shows *lower* off-current than the `l = 0.5u` device of variant 1
(40 pA vs 0.57 nA at 27 °C, 0.1 V): the PSP card's halo (reverse short-channel)
threshold increase at minimum L; taken from the model, not verified.

### Variant 1, off-current baseline

`sim/gen_offcurrent.py` writes one deck per MOS corner and temperature,
`sim/run_offcurrent.sh` runs them (inside `flow/run.sh`, working directory
`sim/`). The netlist is the LVS-extracted one, prepared by
`sim/make_sim_netlist.sh` (device names `M$1/M$2` → `XMELT/XMSTD` because `$`
is a comment character for ngspice and `sg13_lv_nmos` is a subcircuit; MOS
pins re-ordered from KLayout's S G D B to SPICE D G S B). Model lines exactly
as used, `<corner>` ∈ {`mos_tt`, `mos_ss`, `mos_ff`}:

```
.lib /foss/pdks/ihp-sg13g2/libs.tech/ngspice/models/cornerMOSlv.lib <corner>
pre_osdi /foss/pdks/ihp-sg13g2/libs.tech/ngspice/osdi/psp103.osdi
.option gmin=1e-16 abstol=1e-16 reltol=1e-4
```

Bias: `G_SHARED` = source = body = 0 V; drains at 0.1 V (primary readout
bias, ohmic, minimal GIDL) and 1.2 V; plus an ID(VGS) sweep −0.3 … 1.2 V at
both drain biases → `sim/decks/<corner>_T<T>C_idvg_v01.dat`, `_v12.dat`.
Temperatures −40, 27, 85, 125 °C and, **model extrapolated**, 150, 175 and
−196 °C. Results (simulated, VGS = 0), full table in `sim/results.md`:

| corner | T (°C) | ID_STD @0.1 V | ID_ELT @0.1 V | ratio | ID_STD @1.2 V | ID_ELT @1.2 V | ratio |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| mos_tt | −40 | 9.6 pA | 9.6 pA | 1.007 | 28.6 pA | 28.4 pA | 1.005 |
| mos_tt | 27 | 0.57 nA | 0.57 nA | 1.006 | 1.53 nA | 1.53 nA | 1.004 |
| mos_tt | 85 | 7.0 nA | 7.0 nA | 1.004 | 18.5 nA | 18.4 nA | 1.002 |
| mos_tt | 125 | 27.8 nA | 27.7 nA | 1.004 | 73 nA | 73 nA | 1.002 |
| mos_tt | 175 (extrapolated) | 117 nA | 117 nA | 1.003 | 303 nA | 303 nA | 1.001 |
| mos_ss | −40 | 0.98 pA | 0.97 pA | 1.012 | 3.3 pA | 3.3 pA | 1.008 |
| mos_ss | 27 | 0.10 nA | 0.10 nA | 1.009 | 0.27 nA | 0.27 nA | 1.007 |
| mos_ss | 125 | 7.7 nA | 7.7 nA | 1.006 | 20.7 nA | 20.6 nA | 1.004 |
| mos_ff | 27 | 2.5 nA | 2.5 nA | 1.004 | 6.7 nA | 6.7 nA | 1.002 |
| mos_ff | 125 | 85 nA | 85 nA | 1.002 | 218 nA | 218 nA | 1.000 |

A first run with the standard device at w = 3.7 µm (the mean-perimeter
estimate) gave a ratio of 0.90; the device was then sized to the extractor's
W = 3.98 µm and only that run is kept under `sim/logs/`.

What the model can and cannot say:

- **The PSP 103 model has no STI-edge transistor.** Both devices are
  simulated as identical planar channels of their extracted W/L; the ELT's
  freedom from edge leakage and the standard device's dose response are not
  represented. This table is the pre-irradiation baseline the bench compares
  against, nothing more.
- The off-current spans 5 decades over −40 … 175 °C (×40 per 50 K around room
  temperature) and ×25 across mos_ss … mos_ff. The bench must hold the die
  temperature during dose steps to better than ±1 °C for a 10 % ratio
  resolution, or use the ratio, which cancels both.
- At −196 °C the currents (10⁻¹⁶ A at 0.1 V) are below what `gmin = 1e-16`
  resolves; the row is a placeholder, not a value.
- Currents at 27 °C (0.6 nA at 0.1 V, 1.5 nA at 1.2 V) are in the range where
  the analog pad's ESD diode leakage matters (PLAN R7), not yet simulated.

Bias policy carried to the measurement plan (from the published TID studies
in the reading list, not reproduced here): expose with `G_SHARED` at 1.2 V
and drains/source at 0 V (worst case for oxide charge build-up), read at
VGS = 0 with VDS = 0.1 V (primary) and 1.2 V, sweep ID(VGS) at each step so a
threshold shift of the main channel can be separated from a sub-threshold hump
of the edge transistor; measure directly after each step and log the delay.

## Checks

| Check | Status | Evidence |
| --- | --- | --- |
| ELT pair: schematic simulation, nominal (mos_tt, 27 °C, extracted netlist) | passed | `sim/logs/mos_tt_Tp27C_off.log` |
| ELT pair: corners mos_tt/ss/ff × −40/27/85/125 °C | passed (all 12 runs complete) | `sim/logs/`, `sim/results.md` |
| ELT pair: 150, 175, −196 °C | run, **model extrapolated** | `sim/logs/*_Tp150C_*`, `*_Tp175C_*`, `*_Tm196C_*` |
| Mismatch MC | not run | — |
| DRC, `g1_dose_pair_pcell` (default), `--run_mode=deep --no_density`, full rule set incl. extra rules | **passed, 0 errors** | `reports/drc_pcell/g1_dose_pcell_g1_dose_pair_pcell_main.log` |
| DRC, macro `g1_dose_macro` with fill, same options | **passed, 0 errors** | `reports/drc_macro/g1_dose_macro_g1_dose_macro_main.log`, `reports/drc_macro/drc_run_2026_09_19_11_01_21.log` |
| LVS, macro `g1_dose_macro` with fill vs `schematic/g1_dose_macro.cdl` | passed (same devices as the unfilled cell) | `reports/lvs_macro/lvs_run_2026_09_19_11_01_56.log`, `reports/lvs_macro/g1_dose_macro_extracted.cir` |
| LEF loads in OpenROAD (26Q3-850) with the PDK tech LEF; pins and OBS as intended | passed | `reports/lef_check_g1_dose_macro.log` |
| Fill run (PDK `filler.py`, Activ/GatPoly/Metal1-3 kept) | passed | `reports/filler_g1_dose_macro.log` |
| LVS, `g1_dose_pair_pcell` vs `schematic/g1_dose_pair_pcell.cdl`, `--run_mode=deep` | passed | `reports/lvs_pcell/` |
| Off-current baseline, `g1_dose_pair_pcell`, mos_tt/ss/ff × −40…125 °C (+150/175 extrapolated) | passed, 18 runs | `sim/logs/pcell_*_off.log`, `sim/results_variants.md` |
| DRC, `g1_dose_pair_nw` (optional), same options | **passed, 0 errors** | `reports/drc_nw/g1_dose_nw_g1_dose_pair_nw_main.log` |
| LVS, `g1_dose_pair_nw` vs `schematic/g1_dose_pair_nw.cdl` | passed | `reports/lvs_nw/` |
| Off-current baseline, `g1_dose_pair_nw`, same sweep | passed, 18 runs | `sim/logs/nw_*_off.log`, `sim/results_variants.md` |
| DRC, `g1_dose_pair` (ELT), `--run_mode=deep --no_density`, full rule set | **failed**: 1 error, `Gat.f` only | `reports/drc_pair/g1_dose_g1_dose_pair_main.log` |
| DRC, `g1_dose_pair`, same with `--disable_extra_rules` (main set) | passed, 0 errors | `reports/drc_pair_noextra/g1_dose_g1_dose_pair_main.log` |
| DRC, `g1_elt_l130_test` (L = 0.13 µm ring), full rule set | **failed**: 1 error, `Gat.f` only | `reports/drc_l130/g1_elt_l130_test_g1_elt_l130_test_main.log` |
| LVS, `run_lvs.py --run_mode=deep` vs `schematic/g1_dose_pair.cdl` | passed (CDL at the extractor's W/L) | `reports/lvs_pair/lvs_run_2026_09_18_18_29_36.log`, `reports/lvs_pair/g1_dose_extracted.cir` |
| PEX + post-layout | not run | — |
| Antenna, density | not run (chip level) | — |

DRC iterations before the final state: `M1.b` (gate-pad Metal1 0.09 µm from
the substrate-ring Metal1; ring moved out to 0.18 µm) and `pSD.j` (standard
device's ring pSD 0.27 µm from the gate; 0.30 µm needed). Both fixed in the
generator; `Gat.f` remains.

## Unverified

- Chip-level PDN strap onto the 30 µm `vss` bar: the analog straps land via
  stacks where a TopMetal1 stripe (75.6 µm pitch) crosses a macro bar; a 30 µm
  bar may see no crossing, in which case the integrator needs a jog (as for the
  0.5 µm stubs in `INTEGRATION.md`). Pin stubs are not on the Metal3 track
  grid, same as the other analog macros.
- Density inside the macro is not checked at block level (the chip-level
  window check is the arbiter); the macro carries fill on the five obstructed
  layers and no-fill over the devices on all layers.
- Exposure gate bias for the default pair (3.3 V on the shared gate stresses
  the 1.2 V device; 1.2 V under-biases the HV device): to be decided in the
  measurement plan.
- HV pre-rad off-current (fA) is below the expected pad leakage; the bench
  needs a pad-leakage reference (e.g. an unconnected analog pad) to subtract.
- **`Gat.f` acceptance**: whether the foundry accepts a bent gate over Activ
  on the open shuttle is not known here; see the options above.
- Electrical W_eff of the ring (three candidate numbers above); to be
  measured pre-irradiation.
- Dose response: no model exists for STI-edge leakage; the ratio-versus-dose
  curve comes from the bench only. Published lab dose rates overstate
  in-orbit leakage; bench data are an upper envelope.
- Pad routing and the analog pad's ESD leakage floor on `D_STD`/`D_ELT` (PLAN
  R7): not drawn, not simulated. No ESD beyond the IO cell.
- Model extrapolation at 150, 175 and −196 °C.
- PEX, post-layout, mismatch MC: not run.
- Not attempted this week, listed for a later run: a JICG-style layout
  (junction-isolated gate with p-well strips) is drawable with open-PDK
  layers but has no model and would not extract as a known device. If the pin
  fallback of PLAN section 7 frees pins, a second pair in `sg13_hv_nmos`
  (3.3 V thick oxide, by far the more dose-sensitive device) is preferred
  over an ELT PMOS, which shows no STI leakage.

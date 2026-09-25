# G1 tape-out plan — one week to GDS

Plan of record for taking G1 from specification to a submission-ready GDS in
seven days: **start Thursday 18 September 2026, GDS frozen Thursday
25 September 2026.** Written 2026-09-18, replacing an earlier five-week draft.
The specification stays the source of truth for what the chip does; each
block's README is the source of truth for what was run.

A date below with no evidence linked next to it means the step did **not**
happen. Dropping a block is recorded in the README, never silently.

## 1. Shape of the week

Six tracks run in parallel from day 1, each as its own agent in its own
worktree, each owning one directory under `blocks/` or `padframe/`. Nothing is
serial except integration and the chip-level decks. Every track has a hard
freeze; what is not DRC/LVS-clean at its freeze is dropped and its pins are
re-pointed per section 7.

| Day | Date | Tracks | Freeze at end of day |
| --- | --- | --- | --- |
| 0 | Thu 18 Sep | plan, toolchain pin, block skeletons, source clones | this plan; `flow/run.sh` |
| 1 | Fri 19 Sep | R: empty 24-pad ring · A1: BGR sim · A2: T2F sim · A3: sense/trip sim · D: RTL · V: ELT draw + DRC | ring geometry; pin map frozen |
| 2 | Sat 20 Sep | R: ring DRC/density/antenna clean · A1–A3: corners, MC, temperature · D: RTL regression · V: ELT LVS recognition | **ring clean; ELT go/no-go; all schematics frozen** |
| 3 | Sun 21 Sep | A1–A3: layout · D: LibreLane hardening · V: DUT/DOSE cells final | digital macro GDS/LEF |
| 4 | Mon 22 Sep | A1–A3: DRC/LVS · D: level shifters · R: floorplan with real LEFs | **analog block freeze: DRC+LVS clean or cut** |
| 5 | Tue 23 Sep | A1–A3: PEX + post-layout · R: top assembly, supplies, routing | top netlist; block PEX evidence |
| 6 | Wed 24 Sep | R: full-chip DRC, density/fill, antenna, LVS; top-level sim with IO models | **top freeze: zero-marker decks** |
| 7 | Thu 25 Sep | signoff package, README status tables, bonding diagram, owner review | **GDS frozen; human signs** |

Long chip-level runs (density with fill, LibreLane) are started at the end of
a day and read at the start of the next. The container is amd64 emulated on
an arm64 host, so nothing chip-level is run ad hoc.

## 1a. Progress log

Kept short; block READMEs carry the evidence.

| Date | What happened |
| --- | --- |
| 2026-09-25/26 | RTL ECO (register map 1.2) re-hardened pin-compatible and swapped into the chip; r3 `7d07a784…` adopted (D16): all DRC 0, projected LVS passed, canonical LVS as r2; GLS and merged-SDC STA of the new digital passed; chip-level ECO runs passed (simulated). |
| 2026-09-24/25 | Chip of record frozen at 1414 µm (D15): DRC main/maximal, density, antenna passed with 0 markers; projected LVS passed; canonical LVS failed (IO-cell reference semantics, R13). Chip-level matrix on the chip netlists 72/72 passed (simulated). Red-team evidence audit and digital review (`review/redteam-20260925/`) and the record corrections that followed. |
| 2026-09-20 | Session recovery: completed core-only LVS evidence restored (52 matched pairs; final GDS hash verified). Found and reproduced a chip-simulation clock-bridge double-edge bug; separate single-threshold clock receiver passes the focused regression. Historical chip timing is not accepted; corrected schematic, PEX, behavioural and power-up reruns started. IO-ring LVS/antenna remain failed. See `blocks/g1_top/sim/bridge_probe/` and `blocks/g1_padring/reports/assembly-1350/core_lvs/`. |
| Thu 18 Sep | Plan, toolchain pin, wrapper, skeletons, sources cloned. All six tracks started the same evening. |
| Fri 19 Sep, 01:00 | Day-1 goals met early: ring closed at 1200 µm (D10) on DRC/density, LVS/antenna limits documented (R13, R14); every analog block schematic-frozen with corners, MC and temperature; digital macro hardened and signoff-clean; devices DRC/LVS clean with the dose-canary decision D11. Layout phase started for all analog blocks. |
| Fri 19 Sep, 01:40 | All layout agents stopped by a usage limit with partial generators on disk; VM resized to 16 vCPU / 32 GiB; resumed 07:50. |
| Sat 19 Sep, 23:00 | All eight macros final for assembly: filled inside with no-fill over matched devices, DRC/LVS/antenna clean, prBoundary on 189/4, LEFs with interior obstructions only. Oscillator antenna fixed with a diode (< 0.01 % frequency change). Device cells delivered as two 30/34 µm macros. Top-level SDC from the digital owner adopted. Dry-run density failure traced to a boundary-layer artefact. Assembly of record started. |
| Sat 19 Sep, 20:00 | Chip assembly with `VDDA` (D14): KLayout DRC 0, routing DRC 0, VDD/VSS/VDDA grids connected to every macro, `VDDA` path resistance about 26 Ω worst case. Open at block level: fill inside each macro (chip-level fill cannot fill over placed macros; no-fill layers work), four antenna markers on the oscillator capacitor nets, hold inside the digital macro at top-level STA, device cells still to be delivered as macros, prBoundary on six macros. All dispatched to block owners. Breaker-path chip simulation started. |
| Sat 19 Sep, 18:00 | `G1_TRIP` (229 × 207 µm) and `G1_OSC` (166 × 138 µm) DRC/LVS clean with PEX; a post-layout comparator offset from parasitic asymmetry was caught and fixed by re-ordering tracks (matched to 0.2 %). Every block is now laid out, two days ahead of the analog freeze line. |
| Sat 19 Sep, 17:00 | Chip-level dry run through routing: routing DRC 0, core supply grid connected to every macro (routed straps), 0 critical disconnected pins. Found that the IO ring cannot legally supply 3.3 V to the core: pin 7 becomes `VDDA` (D14). Remaining chip-level items: density inside the analog macro column, 13 antenna markers (9 known), hold inside the digital macro at the top-level STA. |
| Sat 19 Sep, 15:00 | `G1_T2F` revision 2 closed: comparator HBTs at ≤ 1.10 V V<sub>CE</sub> at 3.6 V / 175 °C (revision 1: 3.08 V), supply sensitivity −9.3 → −2.5 °C/V, two-point residual −0.85 to +0.17 °C; DRC/antenna/LVS clean, PEX done; LEF obstructions trimmed for the PDN. R15 closed for `G1_T2F`. |
| Sat 19 Sep, 13:00 | Ring closed at 1350 µm (DRC hard rules 0, density 0, XOR 0; core window 622 × 622 µm). Floorplan drafted with every macro as real LEF/GDS, 71 % fill. Chip-level dry run reaches PDN generation; power-grid connectivity to the analog macros' Metal3 bars is the open integration item (R16). |
| Sat 19 Sep, 12:00 | `G1_SENSE` (252 × 189 µm) and `G1_GATE` (131 × 51 µm) DRC/LVS clean with PEX. Area budget no longer closes at 1200 µm: die set to 1350 µm (D13), ring re-run started. |
| Sat 19 Sep, 10:00 | Digital macro of record (run 7, TMR copies separated), `G1_BGR` and `G1_T2F` layouts DRC/LVS/antenna clean with PEX. `G1_T2F` revision 1 found to run its comparator HBTs above the 1.6 V V<sub>CE</sub> limit; revision 2 with collector cascodes started (R15). kpex RC mode found unusable on this PDK; capacitance mode plus hand-counted wiring resistance is the PEX method of record. |

## 2. Toolchain, pinned

All runs happen inside one container image; versions were established on
2026-09-18 by running each tool's version flag. The PDK inside it is a
release checkout identified by its `COMMIT` file.

| Tool | Version | Established by |
| --- | --- | --- |
| PDK | IHP SG13G2, commit `84374023ee8b4b126bebbba67fcbada0a9c0ff0b` | `/foss/pdks/ihp-sg13g2/COMMIT` |
| ngspice | 46 | `ngspice -v` |
| KLayout | 0.30.9 | `klayout -v` |
| xschem | 3.4.8RC | `xschem --version` |
| LibreLane | 3.1.0.dev2 | `librelane --version` |
| Yosys / OpenROAD | 0.67 / 26Q3-850 | `yosys -V`, `openroad -version` |
| Icarus Verilog / Verilator | 14.0 / present | `iverilog -V` |
| kpex, CACE, magic 8.3.678, netgen 1.5.323 | present | `command -v` |
| Container image | digest `sha256:5fd78498e578c6e9ec10828c248ca3790fc88250ff6caf545521b29e448ea3c0` | `docker inspect` (recorded 2026-09-21). Since commit `0b67f4ee` (2026-09-22) `flow/run.sh` pins `sha256:ddeb6957…`, the image of the chip-of-record runs (README "Built against") |

The README's "Built against" table currently carries commit `144f811c…`
inherited from another design; G1 is built against `8437402…` and the README
is corrected with the first simulation log as evidence.

The IO library in this PDK revision is "I/O Update 2" (2026-06-18). Cell
sizes from the LEF: pads 80 × 180 µm, corner 180 × 180 µm, fillers 1, 2, 5,
10, 20 and 50 µm.

## 3. Sources

Open-source designs on SG13G2 are used as starting points where they exist.
Each is cited in the block README by URL and commit, its licence file is
carried along, and every one is re-verified here with the PDK's own decks.
No source below has published silicon measurements for the block we take
from it, so none is treated as proven.

| Block | Starts from | What it gives | What we must add |
| --- | --- | --- | --- |
| `G1_PADRING` | `iic-jku/ihp-sg13g2-ams-chip-template` (LibreLane chip flow, `sg13g2_io`, sealring, filler, bond plan); `ChipDesign-BV/pad-ring-ihp` (parametric ring recipe); `IHP-GmbH/OCDCPro-padframe/24` (IHP's own 24-pad frame, needs dev branches, reference only) | a working ring flow on this PDK with DRC/LVS/antenna/density steps | 1.2 × 1.2 mm (D10), 6 pads per side, our pin map; PDK bondpad PCell on TopMetal1/2 outside each IO cell; 1 µm filler between abutted power pads (contact-spacing DRC) |
| `G1_BGR` | `2AMLogic/sg13g2-bandgap` (`npn13G2` core, 3.3 V, DRC-clean, PEX, 300-sample MC) | the only SG13G2 bandgap that uses the HBT | LVS with the IHP deck (theirs could not extract HBTs); fix the ~13 % low V<sub>REF</sub>; PTAT current output; start-up over temperature |
| `G1_T2F` | none on SG13G2; HBT bias from the bandgap above, oscillator readout new | — | ΔV<sub>BE</sub> core (two `npn13G2` at 1:8), PTAT current into a `cmim` relaxation oscillator against a V<sub>REF</sub> threshold; divider to `TEMP_OUT` |
| `G1_SENSE` | `IHP-GmbH/TO_Nov2024/BG` OTA (3.3 V, PMOS input, recycling folded cascode, DRC/LVS, on silicon T576, no published measurement) | a 3.3 V PMOS-input OTA layout | difference-amplifier configuration with `rppd`, gain 20, offset trim |
| `G1_TRIP` | comparator: `IHP-GmbH/IHP-AnalogAcademy` module 3 dynamic comparator and `2AMLogic/sg13g2-comparator` (StrongARM, MC offset data); DAC: resistor-string topology (no SG13G2 source exists) | 1.2 V clocked comparator with offset statistics | two comparators (soft, hard), two 8-bit `rppd` string DACs from V<sub>REF</sub>, 3.3 V-to-1.2 V input conditioning |
| `G1_GATE` | `sg13g2_IOPadOut30mA` | driver and ESD | HV-MOS analog latch, `EN` gating, defined power-up state |
| `G1_CTRL` | `ChipDesign-BV/spi-slave-ihp` (mode-0 SPI, 8 × 8 register file, LibreLane, DRC 0 / LVS pass, Apache-2.0); `IHP-GmbH/ihp-sg13g2-librelane-template` (counter, config) | serial interface and register file RTL with a working LibreLane config | register map, trip timers, scrub state machine, event counters |
| `G1_SEU` | none; TMR pattern is standard | — | 1024-bit plain and TMR-voted shift registers, scrubber, counters (RTL, one day) |
| `G1_OSC` | `algofoogle/tt09-ring-osc2` (standard-cell ring oscillators, on TTIHP25a silicon) | trivially reproducible ring | current-starved or divided ring at ~10 MHz; not a reference, only a clock |
| Level shifters 1.2 V ↔ 3.3 V | none in the PDK (the shifters live inside the IO pads only) | — | custom `sg13_hv_*` cells in the analog wrapper |
| `G1_DOSE` | none; no ELT PCell or community cell exists | — | hand-drawn annular-gate NMOS cell; LVS recognition spike on day 2 |
| `G1_DUT` | `npn13G2` PCell | — | routing to three analog pads |

Published papers behind the topology choices are held in a reading list
outside this repository and are not copied into it.

## 4. Decisions

| # | Decision | Reason | If reversed |
| --- | --- | --- | --- |
| D1 | `G1_SENSE` input pair is thick-oxide PMOS, not NPN HBT | NPN bases at −0.1 to +0.3 V need emitters near −0.8 V; there is no negative rail. PMOS works at ground-referenced common mode. HBTs stay in the bandgap, sensor and device corner. | needs a level shift or high-side shunt; changes the pin map; not recommended |
| D2 | `G1_T2F` readout is a relaxation oscillator: I<sub>PTAT</sub> into `cmim`, threshold from V<sub>REF</sub> | f ∝ I<sub>PTAT</sub>/(C·V<sub>REF</sub>) is linear in T, which the ±2 °C two-point target needs | standard-cell ring readout: faster to build, nonlinear, target becomes "not met, documented" |
| D3 | Trip is two thresholds with programmable durations (soft with trip-off time, hard with short blanking), not a true I²t integrator | matches how current limiters are specified; needs no ADC | a real integrator needs a flash or ΣΔ front end; out of scope |
| D4 | One internal ring oscillator clocks comparators, timers and the scrubber; `SCLK` only accesses registers | a guardian must not depend on the host clock | — |
| D5 | `G1_DOSE` ships pins-first; the on-chip log-ratio readout is not in the week | pins give the physics | — |
| D6 | Ring flow: the IIC-JKU AMS chip-template LibreLane flow, time-boxed to day 1; fallback on day 2 is a KLayout Python assembly of the IO cells, sealring and macros | the template already closes DRC/LVS/antenna/density on this PDK; scripted assembly is fully under our control | either ends in the same checks |
| D7 | Pads as close to abutted as the placer allows, with the 1 µm filler between supply pads; the exact pitch follows from D10 and is recorded in the padring README | simplest ring | re-run ring DRC |
| D8 | 3.3 V analog uses `sg13_hv_*` + `npn13G2`; logic is 1.2 V `sg13g2_stdcell`; level shifters are our own HV-MOS cells | no standalone shifter exists in the PDK | — |
| D10 | **Die is 1200 × 1200 µm, not 1000 × 1000 µm.** | The stock `sg13g2_io` cells carry no passivation opening; the 70 µm bondpad sits outside the cell and the pad opening must clear the sealring, so the IO row cannot start closer than about 112 µm (hard rules) or 129 µm (recommended) from the die edge. Six pads plus corners per side therefore need at least about 1073 µm (hard) or 1108 µm (recommended); IHP's own 24-pad frame is 1120 µm. At 1130 µm the core window is 398 × 398 µm (0.158 mm²), while the digital macro alone synthesises to about 0.18 mm² of cells before shrinking the SEU register. 1200 µm gives a core window of about 470 × 470 µm. Established by the day-1 ring run, see `blocks/g1_padring/README.md`. | 1130 µm is possible only with the SEU register cut to 512 plain + 128 TMR bits and near-full core utilisation. |
| D11 | **`G1_DOSE` default is a thick-oxide (3.3 V) NMOS beside a thin-oxide (1.2 V) NMOS, both PDK PCells; the drawn enclosed-layout NMOS is carried as an approval-gated alternative.** | The ELT cell passes LVS (extracted as `sg13_lv_nmos`, W 3.98 µm, L 0.50 µm) but fails DRC rule `Gat.f` (bent gate poly on active), which is in the deck's unverified extra rule set yet names a foundry rule; a closed ring gate cannot satisfy it. On this process the 3.3 V NMOS is by far the more dose-sensitive device (published IHP data), so the HV/LV pair is a strong canary and is DRC-clean by construction. Established day 1, see `blocks/g1_dose/README.md`. | If the foundry confirms bent gates are acceptable on the open shuttle before the analog freeze (day 4), the ELT cell replaces the HV device on the `D_ELT` pad. |
| D12 | **SEU register depth is set at floorplan time (day 4) from the core area left after the analog macros are placed.** The RTL is parameterised; the day-1 hardening used 256 plain + 3 × 128 TMR bits in a 360 × 360 µm macro (85.6 % utilisation). 512/256 needs about 0.12 mm² of cells, 1024/256 about 0.145 mm². | `sg13g2_stdcell` has no reset-less or enable flop; the smallest is 49 µm², so flop count sets the macro size. The register is a test structure whose value is event statistics under beam; more bits are better but not at the expense of the analog blocks. | Grow the die to 1250 µm to keep 1024/256, or accept 256/128. |
| D13 | **Die is 1350 × 1350 µm** (supersedes D10's 1200 µm). | With every macro laid out to DRC/LVS, the digital macro (0.130 mm²) plus bandgap, sensor, sense amplifier and gate driver (0.074 mm²) already fill 0.204 of the 0.223 mm² core window at 1200 µm, before the comparator/DAC block (about 0.05 mm²), oscillator, devices, level shifters, halos and routing. A 620 µm core window (about 0.38 mm²) holds them at roughly 70 % macro fill. Die area 1.82 mm² instead of 1.44 mm². | Staying at 1200 µm needs the sense-amplifier resistor array halved and the digital macro at about 90 % utilisation, both risky in the week; 1300 µm (0.33 mm² core) is the fallback if the floorplan shows slack. |
| D14 | **Pin 7 becomes `VDDA`, a 3.3 V analog supply on the bare terminal of an `sg13g2_IOPadAnalog`; analog ground shares the core `VSS` grid.** | The chip-level dry run showed there is no DRC-legal tap of the ring's `iovdd` rail into the core: in every `sg13g2_io` cell the `iovdd`/`iovss` rails sit behind `vdd`/`vss` on Metal3 to TopMetal2 and `vss` fills Metal1/2, so any core-side connection crosses another rail on the same layer (145 DRC markers). IHP's template never needs the tap (1.2 V core). The 3.3 V blocks draw about 1.5 mA in total, well within a bare analog pad. The board ties `VDDA` and `IOVDD` to one rail, keeping the pad's ESD diodes reverse-biased. | Second core `VDD` pad is lost; the digital macro draws a few mA on one pad, acceptable. Alternative: a custom IOVdd pad view, rejected because it edits a PDK cell. |
| D15 | **Chip of record is the 1414 × 1414 µm native-lineage GDS `g1_chip_top_1414.gds` (`629d303a…`), decided 2026-09-24** (supersedes D13's 1350 µm LibreLane assembly). | Zero-marker DRC/antenna and the block variants (SENSE comp45 + R100, TRIP regenpair4 + NF4, OSC R0.95, BGR586); owner decision. Sign-off: `blocks/g1_padring/reports/signoff-1414-20260924/README.md`. | The 1350 µm assembly and its evidence are retained as history, not the chip. |
| D16 | **2026-09-26: RTL ECO adopted through pin-compatible re-hardening of `g1_digital`; chip of record becomes `g1_chip_top_1414_r3.gds` (`7d07a784…`)** (owner decision 2026-09-25; supersedes r2 `9049e87b…` of D15's lineage, which stays the documented fallback). | The ECO (register map 1.2, `blocks/g1_ctrl/ECO_20260925.md`) fixes the digital behaviours found in review. The frozen RTL was confirmed at chip level (`eco_c_mid_m03` trip 1.166 µs / `GATE` < 1 V 1.451 µs; `eco_hard_pulse_m03` no trip) and by GLS on the hardened netlist `4b83f181` (21 tests / 260 checks). The macro was re-hardened with run7's pins, outline and PDN (`blocks/g1_ctrl/flow/eco/`), swapped into the same cell with top-level routing untouched, and 700 µm² of GatPoly fill was added to restore global density. Sign-off: `blocks/g1_padring/reports/signoff-1414r3-20260926/README.md` (all DRC 0; projected LVS passed; canonical LVS failed as r2). | The pre-ECO digital (run7 placement, redone clock tree) and r2 are retained as history; r2 can be resubmitted unchanged if needed. |
| D9 | The bandgap is the 2AMLogic HBT topology, not the all-CMOS AnalogAcademy one | the chip's point is the HBT; the CMOS one is the fallback only if the HBT LVS cannot be closed by day 4 | fallback costs the SiGe reference claim |

## 5. Block plan and gates

One directory per block under `blocks/`. Same README skeleton everywhere:
what it is, source and commit, what was simulated (command, corners,
temperature), what was laid out, checks table with passed/failed/not run,
what is unverified.

Verification order per block, no step before the previous has a log:

1. xschem schematic, ngspice operating point.
2. Corners `mos_tt/ff/ss`, `hbt_typ/bcs/wcs`, `res_typ/bcs/wcs`; supplies ±10 %; temperatures −40, 27, 85, 125, 150, 175 °C; −196 °C as an extrapolation run labelled as such; mismatch MC with the PDK `*_mismatch` libraries on `G1_BGR`, `G1_SENSE`, `G1_TRIP`.
3. Layout with PDK PCells (plus the drawn ELT cell).
4. DRC `run_drc.py --run_mode=deep --no_density` at block level.
5. LVS `run_lvs.py` against the xschem netlist.
6. kpex PEX and post-layout re-run of the nominal and worst corner.
7. README status table with links to logs.

Chip level adds: density with sanity checks after the PDK filler flow,
antenna, full-chip LVS against the assembled netlist, top-level transient
with the IO cell SPICE models.

| Block | Day 1 | Day 2 | Day 3 | Day 4 | Day 5 |
| --- | --- | --- | --- | --- | --- |
| `G1_PADRING` | empty ring from template | ring DRC/density/antenna clean; fallback decision | — | floorplan with real LEFs | top assembly |
| `G1_BGR` | source ported, OP | corners/MC/temperature | layout | DRC/LVS | PEX, post-layout |
| `G1_T2F` + `G1_OSC` | ΔV<sub>BE</sub> core + oscillator sim | corners/temperature, f(T) linearity | layout | DRC/LVS | PEX, post-layout |
| `G1_SENSE` + `G1_TRIP` + `G1_GATE` | OTA ported, comparator, DAC sim | corners/MC, trip delay, kickback | layout | DRC/LVS | PEX, trip/no-trip table |
| `G1_CTRL` + `G1_SEU` + timers | RTL + iverilog | regression, fault injection | LibreLane hardening | level shifters, macro DRC/LVS | — |
| `G1_DOSE` + `G1_DUT` | ELT drawn, DRC | LVS recognition, W/L note | cells final, pad routing | — | — |

## 6. Pin map

Unchanged from the specification. Frozen at the end of day 1 because the
ring is built from it.

## 7. Pin fallback

If a block is cut at its freeze, its pads stay physically identical (analog
pads for freed signals) and are re-pointed at internal nodes so no pad
floats.

| Cut | Freed pins | Reassigned to |
| --- | --- | --- |
| digital core | 14 `SCLK`, 15 `SDI`, 16 `SDO` | `IPTAT` monitor, sensor `VBE1`, `VBE2` |
| breaker | 8–13 | second HBT variant (`npn13G2L` or `npn13G2V`, three pins), ELT PMOS pair |
| sensor | 17 `TEMP_OUT` | sensor ΔV<sub>BE</sub> node |

With the digital core cut, the analog latch still drives `GATE` and
`FAULT_N`, with the hard threshold from `TRIP_SET`. With the breaker cut, the
die is a reference, sensor and device chip.

## 8. Risks

| # | Risk | Mitigation |
| --- | --- | --- |
| R1 | Emulated container too slow for chip-level decks inside the week | block-level DRC without density; chip-level runs overnight; density only after fill |
| R2 | Template ring flow does not close at 1.2 × 1.2 mm with mixed-domain macros | day-1 time box; scripted KLayout assembly on day 2 (D6) |
| R3 | HBT bandgap LVS cannot be closed with the IHP deck | fallback D9 by day 4 |
| R4 | Drawn ELT NMOS violates `Gat.f` (bent gate on active); foundry acceptance unknown | default canary is the DRC-clean HV/LV PCell pair (D11); ELT swapped in only on written foundry confirmation |
| R5 | No level-shifter cell exists | own HV-MOS cells, simulated across corners on day 4 |
| R6 | Models not characterised at 77 K or above 125 °C | such runs labelled *model extrapolated*; bench decides |
| R7 | Analog pad ESD leakage sets the floor on device-pin currents | simulated with the IO SPICE model; measurement plan keeps device currents ≥ nA |
| R8 | `GATE` high at power-up when `IOVDD` is present without `VDD` (PDK output pad property, simulated day 1) | board constraint: `VDD` before or with `IOVDD`; `EN` gates the driver once both rails are up; written into the specification and the measurement plan |
| R9 | Foundry precheck differs from the open deck; drawn non-PCell NMOS and bonding geometry acceptance | assumed accepted; confirmation pending outside this repo |
| R10 | Two abutted IO power pads violate contact spacing | 1 µm filler between them, as in the template |
| R12 | Core window (about 0.22 mm²) is tight for the digital macro plus analog macros | digital macro closed at 360 × 360 µm with 256/128 SEU bits; depth re-decided at floorplan (D12) |
| R13 | The PDK's KLayout LVS deck does not match any stock `sg13g2_io` cell against the PDK's own CDL, so a full-chip LVS through the IO ring cannot pass at this PDK commit | LVS is run on every core macro and on the core assembly; ring connectivity is proven by OpenROAD's disconnected-pin check and KLayout metal continuity at every bondpad joint; the IO cells are taken as delivered. **Updated 2026-09-25 for the 1414 µm chip of record:** canonical LVS failed; cause: substrate/tap/diode netlist semantics of the IO-cell reference in the PDK, reproduced with stock cells and with IHP's latest `dev` deck and library; the design-local IO copies match IHP's `dev` library on every layer (PR #1223); upstream issues #1218/#1130 (`review/upstream/evidence/README.md`). Projected-reference LVS passed. Question raised with the foundry (tape-in package §8). |
| R16 | pdngen does not connect the analog macros' Metal3 supply bars (pins, not stripes) to the top-level grid: 93 k connectivity violations in the first dry run | explicit per-layer connects, then routed special-net straps as fallback; macro LEFs must leave upper metals free above their supply bars; time-boxed to day 3 |
| R15 | HBTs operated above the model card's V<sub>CE,max</sub> = 1.6 V in the 3.3 V domain (avalanche base current, supply sensitivity, reliability) | every 3.3 V block with HBTs uses collector cascodes (`G1_BGR` from the start, `G1_T2F` in revision 2); each block README reports max V<sub>CE</sub> at 3.6 V / 175 °C; the measurement plan keeps the bare HBT below 1.6 V except in one final breakdown sweep |
| R14 | Antenna deck flags every input pad of the current `sg13g2_IOPadIn` revision (receiver gate on the rail); the previous revision and IHP's own template chip pass | recorded with evidence as a deck/library artefact; question raised with the foundry; no layout change |

## 9. Out of scope this week

On-chip dose readout, curvature-corrected bandgap, chopping in the sense
amplifier, bench fixture, irradiation booking. Each is listed in the block
READMEs as *not built*, not as *not run*.

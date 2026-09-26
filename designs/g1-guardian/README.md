# G1 — radiation-aware node guardian (SiGe BiCMOS test chip)

A mixed-signal test chip intended to protect a compute load from single-event
latch-up and characterize temperature, dose-sensitive leakage and upset events.
Four functions on one 1.414 × 1.414 mm die, planned for QFN24 board measurements:

1. a current-limiting **breaker**: shunt sense amplifier, trip comparator, I²t
   timer and gate drive for an external switch, with a trip profile that lets a
   fast load step through and cuts a latch-up signature;
2. a **temperature sensor** with a one-wire frequency output, built on the
   HBT ΔV<sub>BE</sub> law; operation beyond the model range remains unverified;
3. a **dose canary**: two NMOS transistors of different oxide thickness at equal
   bias, for investigation of off-current versus total ionizing dose; no dose
   calibration has been measured. The experimental enclosed-layout alternative
   is not in the assembled chip;
4. an **upset canary**: scrubbed shift registers, plain and triple-modular-redundant, whose upset counts are reported.

A SiGe bandgap supplies the reference, and a three-wire serial interface exposes
telemetry and trip settings. A bare HBT and the canary transistors are also
brought out to pins for direct device characterisation.

Target process is the IHP SG13G2 open PDK (0.13 µm SiGe BiCMOS). The die uses
the PDK's `sg13g2_io` cells as its pad ring, six per side, and is wire-bonded
into a QFN24 package after bonding-service acceptance.

The implementation uses standard SG13G2 devices and requires no optional TSV,
localized backside etching, MEMRES/RRAM, photonics or copper-backend module.
The 3.3 V thick-oxide MOSFETs, SiGe HBTs, MIM capacitors and poly resistors are
part of the base open PDK. The legacy `D_ELT` pin connects to a standard HV
NMOS in the assembled netlist, not an enclosed-layout transistor.

Chip of record (owner decision 2026-09-24; revision r3, 2026-09-26):
[`g1_chip_top_1414_r3.gds`](blocks/g1_padring/layout/g1_chip_top_1414_r3.gds), top cell
`g1_chip_top`, 1414 × 1414 µm, SHA-256 `7d07a7841a531f51e08b0c90e76fe603889cd2ef29905e309e63f09742e688f2`.
It is r2 plus two changes:
- **the re-hardened `g1_digital` macro.** RTL ECO, register map 1.2
  ([`ECO_20260925`](blocks/g1_ctrl/ECO_20260925.md); owner decision 2026-09-25, `PLAN.md` D16),
  pin-compatible with r2's macro and swapped into the same cell with the top-level routing untouched;
- **700 µm² of GatPoly fill**, which restores the global GatPoly density.

Netlists:
- canonical [`g1_chip_top_1414_r3.cdl`](blocks/g1_padring/netlist/g1_chip_top_1414_r3.cdl) (`5e47ae02…`);
- comparison-only [projected reference](blocks/g1_padring/netlist/g1_chip_top_1414_r3_projected_ref.cdl) (`d0d36c84…`).

Sign-off: [`signoff-1414r3-20260926`](blocks/g1_padring/reports/signoff-1414r3-20260926/README.md):
- main, maximal, precheck, density and antenna DRC: 0 markers;
- projected LVS passed (62 940 devices, 22/22 pins); canonical LVS failed as before;
- XOR against r2: outside the macro only the added 5/22 fill differs.

Block-to-netlist map: [`signoff-1414-20260924`](blocks/g1_padring/reports/signoff-1414-20260924/README.md);
the digital row is replaced by the one in the r3 sign-off.

Superseded revisions:
- r2 `g1_chip_top_1414_r2.gds` ([sign-off](blocks/g1_padring/reports/signoff-1414r2-20260925/README.md);
  `9049e87b0303893573ed82f56a5d41f926c4db126e8d972062553c7d19996d2c`) is the documented fallback.
  Its GDS is retained outside the tree (`review/local-retention-20260925.json`) and its CDLs stay in
  `blocks/g1_padring/netlist/`.
- r1 (`629d303abf594ec90593f1d28a8d9ad19673ea6662780ba428a6d9c5685986ba`).

Bond plan (owner decision 2026-09-25, pad to the QFN24 lead directly opposite):
[`padframe/BONDPLAN_20260925.md`](padframe/BONDPLAN_20260925.md). The bond map
[`bondmap_20260926_r4.csv`](padframe/bondmap_20260926_r4.csv) is bound to r3.
Draft submission checklist: [`review/TAPEIN_PACKAGE_20260924.md`](review/TAPEIN_PACKAGE_20260924.md).
r3 (84.1 MB) is committed (`7219e7e5`). The SHA-256 is the identity of each file.
It supersedes the 1350 µm LibreLane assembly
([`g1_chip_top.gds`](blocks/g1_padring/layout/g1_chip_top.gds),
[`g1_chip_top.cdl`](blocks/g1_padring/netlist/g1_chip_top.cdl),
[`INTEGRATION.md`](blocks/g1_padring/INTEGRATION.md)). That evidence is retained but is not the chip.
The [design review PDF](review/G1_DESIGN_REVIEW.pdf) is a dated snapshot that predates this decision.

**State (2026-09-26): the chip of record is the 1414 µm native-lineage GDS above (r3).**
It contains:
- SENSE comp45 + R100;
- TRIP with the regenpair4 hard and NF4 soft comparators;
- OSC R0.95;
- BGR586 (`bgr_loop24_qref4_r253p465_hv06`);
- T2F baseline revision 2;
- GATE baseline;
- **the ECO digital (register map 1.2)**, re-hardened pin-compatible;
- three `g1_ls_up` level shifters;
- the DOSE HV/LV pair and the DUT HBT.

Bond pads are moved 5 µm outward. The IO ring uses design-local `sg13g2_io` copies that carry
PolyRes 128/0 over their existing gate poly.

Checks on that exact file:
- **DRC:** main, maximal, precheck, density and antenna **passed** (0 markers).
- **Projected-reference LVS: passed** (62 940/62 940 devices).
- **Canonical unprojected LVS: failed** on the same 14 IO/level-shifter sub-cells as r1/r2. Cause:
  substrate/tap/diode netlist semantics of the IO-cell reference in the PDK, reproduced with stock
  cells and with IHP's latest `dev` deck and library. The design-local IO copies match IHP's `dev`
  library on every layer (PR #1223; upstream issues #1218/#1130;
  [evidence](review/upstream/evidence/README.md)).
- **Full-chip PEX: not run.**

The digital macro on the chip:
- gate netlist `4b83f181…`, powered netlist `476885d7…`, nominal SPEF `0b626c7f…`;
- STA with the merged chip SDC **passed** at macro level and inside the routed signal netlist
  (3 corners, nominal RC; macro setup/hold slow 28.45/0.337 ns, in chip 25.70/0.337 ns):
  0 setup/hold violations; in the chip context 12 analog-pad max-slew flags per corner
  (placeholder library values) and 98 unannotated drivers, dispositioned;
- max slew, max cap and max fanout inside the macro **passed**; clock-buffer fanout ≤ 8;
- gate-level simulation of `4b83f181`: 21/21 functional tests (260 checks) **passed**,
  zero-delay and SDF-annotated typ; the red-team bench R3 **fails** (serial framing, out of
  the ECO scope); Icarus executes no timing checks and drops part of the SDF delay model
  (68 unsupported `ifnone` paths) ([gls_eco_r3v2](blocks/g1_ctrl/sim/gls_eco_r3v2/));
- not run: SDF GLS fast/slow, formal equivalence of the ECO RTL against `4b83f181`,
  chip-level co-simulation with the macro's gate netlist + SPEF.
- Timing of the final GDS: **not run**.

Chip-level runs with the ECO RTL (hand-wired chip deck (`run_top.py --blockset c1414`): block extractions with the BGR586 schematic view (`bgr=sch`), SENSE pads without `dantenna` (`inpads nodcn`), fitted `GATE` driver (about 7 % optimistic), ideal clock; not a full-chip extraction; RTL co-simulation, tt/27 °C,
[`ECO_20260925`](blocks/g1_ctrl/ECO_20260925.md)):
- `eco_c_mid_m03`: hard trip, `tripped` **1.166 µs**, `GATE` < 1 V **1.451 µs**;
- `eco_hard_pulse_m03`: 200 ns 45 mV pulse, no trip (simulated).
- `eco4` regression (same deck, 2026-09-26; RESULTS §10): all runs except the CDL run done and passed as
  expected: `c_mid` `GATE` < 1 V 1.439–1.441 µs at tt/27, ss/125, ff/−40 °C; `c`, `e20` 1.440 µs;
  `q` and `hard_pulse` no trip; `f_mid` re-arms; core-first power-up `GATE` ≤ 0.076 V (0.009 V
  with 10 kΩ) while EN low; IO-first 3.3 V for 4.3 µs (IO-pad property, P1). `b_s` soft trip, `GATE` < 1 V 28.040 µs after the event (baseline 27.65 µs); the
  CDL run on this deck is invalid (truncated log) and superseded by the r3 CDL campaign `r3full`.
  The +106 ns against pre-ECO is one `osc_clk` period of sampling phase, not a circuit change.

Full-chip layout-netlist campaign on the chip of record (`r3full`, interim, simulated;
[RESULTS §11](blocks/g1_top/sim/campaigns/RESULTS_20260925.md); detailed record
[`blocks/g1_top/sim/FULLCHIP_CDL_R3_20260926.md`](blocks/g1_top/sim/FULLCHIP_CDL_R3_20260926.md)): r3 CDL + ECO RTL + all block
extractions + extracted top-level interconnect (C only) + real IO pads (`nodcn`) + ideal clock +
T2F on. The hard fault takes `GATE` below 1 V **1.543 µs** after the fault at tt/27 °C, 1.726 µs at
ss/125 °C (slower real-pad fall) and 1.433 µs at ff/−40 °C. `q`, `c`, `e20`, `f_mid`, `hard_pulse`
`b_s` (soft trip, `GATE` < 1 V 28.131 µs) and real-pad power-up passed; `osc` and the near-threshold witnesses pending.

The results below this point were obtained with the pre-ECO digital (map 1.1 RTL) on r1/r2 content:
Full-chip simulation driven by the projected-LVS-matched canonical CDL of r1 (`g1_chip_top_1414.cdl` `af5a4dbd`; canonical LVS fails on the IO cells) with the pre-ECO RTL (map 1.1) (all blocks
extracted, real IO pads, RTL co-simulation, ideal clock; [FULLCHIP_CDL](blocks/g1_top/sim/FULLCHIP_CDL_20260925.md)):
`c_mid` compact at tt/27 °C **passed**, trip decision 1.058 µs, `GATE` < 1 V
**1.437 µs** after the fault with the real `sg13g2_IOPadOut30mA` (simulated). The
hand-wired decks below use a fitted 47 Ω `GATE` driver that is about 7 % (about 90 ns)
optimistic on `GATE` < 1 V; add about +90 ns to their values. The r3 digital adds about
one clock to the decision (1.166 vs 1.049 µs on the hand-wired deck), so the r3 value on the
CDL deck is expected later than 1.437 µs (not run). The CDL deck uses `pads nodcn` (all
`dantenna` removed) and has no top-level wiring C. `q` full length (44 µs, T2F on) on the
CDL deck: no trip; core-first power-up: see below.
With the extracted top-level interconnect (`c1414icx`, C only; extraction of r1 geometry, valid for r3 because r3 differs only inside the macro and in fill) the like-for-like chip-level trip time changes by < 0.1 ns (the earlier "≤ 10 ns" compared different timelines) and the on-chip `VREF` node carries 33–46 mV p-p clock ripple with its mean and the sampled thresholds unchanged (simulated; the T2F-on extracted run failed numerically at 40.8 µs, its reference completed).
Chip-level simulation on the chip's own block netlists
([`g1_top --blockset c1414`](blocks/g1_top/README.md)) passed these tt/27 °C
cases: nominal hard fault (BGR586 and TRIP NF4 extractions, run `c1414fullc`), 1 ms soft window and short pulse (the last two with the
behavioural front end), core-first power-up.
Corner, temperature and supply matrices (simulated, ideal clock at 9.436 MHz,
SENSE pads without `dantenna` diodes, BGR586 schematic view, fitted behavioural `GATE`/`FAULT_N` output pads: [RESULTS_20260925](blocks/g1_top/sim/campaigns/RESULTS_20260925.md)): all 72
case × corner × temperature cells completed and passed (72/72, none failed), the
last twelve as `_r4` re-runs. Hard faults took
`GATE` below 1 V 1.31–1.36 µs after the fault, including at the supply extremes.
IO-first power-up drove `GATE` high for 4.2–4.4 µs even with 10 kΩ (expected; the
P1 board rule). The effective hard threshold sits 8.0–9.25 mV (41–47 LSB) of shunt below its DAC code at tt/27 °C on the chip netlists (40–56 LSB over corners on the block bench)
(calibration requirement below).
Nothing has been fabricated, taped out or measured. This is not a signed-off
submission.**

## What the chip is meant to do

| Block | Function | Devices | Domain | Est. area |
| --- | --- | --- | --- | ---: |
| `G1_SENSE` | Kelvin shunt sense amplifier, low-side, gain 20; difference amplifier around 3.3 V PMOS-input OTAs. **Chip variant comp45 + R100** (`RRZ` `rppd` 1 × 100 µm in `g1_ota_main_candidate`), layout XOR-identical to the RZ100 native build (signoff block map). Simulated, standalone, 100/100 mismatch samples: gain 19.905–20.050, calibrated residual ≤ 498 µV with an ideal continuous room-temperature correction ([R100_MC_100](blocks/g1_sense/reports/R100_MC_100_20260923.md)). Post-layout: partial-field C only, field acceptance failed/unresolved | thick-oxide PMOS input, thick-oxide MOS, `rppd`, `cmim` | 3.3 V | 0.092 mm² (chip cell 384.3 × 238.7 µm, [block_xor.json](blocks/g1_padring/reports/signoff-1414-20260924/blockmap/block_xor.json); Sep-19 layout 0.048 mm²) |
| `G1_TRIP` | Two clocked comparators with V<sub>REF</sub>-referenced 8-bit resistor-string DACs, soft and hard thresholds. **Chip variant: hard comparator regenpair4** (regenerative NMOS 6/0.26 µm) **+ soft comparator NF4** input pair (W24/L0.68, four folded fingers). Block LVS of the TRIP macro cut from the full-chip NF4 candidate `60730627` passed; kpex CC extraction of that cut: `g1_trip_nf4_pex.spice` (XOR of the cut against the TRIP cell of `629d303a`: not run). NF4 kpex CC comparator, simulated: all decisions right, delay ≤ 1.694 ns at 1 mV overdrive (ss, 1.08 V, −40 °C), offset bracket −3.9…+0.77 mV at the comparator input `icmp` (tt), not referred to the shunt ([postlayout](blocks/g1_trip/sim/postlayout/README.md)). DAC deck, wiring R and MC on the NF4 extraction not run | 1.2 V StrongARM comparators, `rppd` strings, thick-oxide switch trees | 1.2 V / 3.3 V | 0.047 mm² |
| `G1_GATE` | Latch and driver core for the external low-side N-FET, latched or retriggering, fast path from the hard comparator (`blocks/g1_gate/layout/`: 131 × 51 µm, DRC and LVS clean; kpex extraction bound to the chip GATE layout `ddf2c44a` by XOR, block LVS and re-extraction: `blocks/g1_gate/sim/postlayout/README_chip_binding_20260925.md`) plus the 30 mA output pad in the ring | thick-oxide MOS, `sg13g2_IOPadOut30mA` | 3.3 V | 0.007 mm² + pad |
| `G1_BGR` | Bandgap reference and PTAT current. **Chip variant `bgr_loop24_qref4_r253p465_hv06` ("BGR586")**: 336 HV MOS, 301 `npn13G2`, 399 resistors. Block LVS passed; kpex 2.5D CC extraction run, DC operating point and V<sub>REF</sub>(T) identical to the schematic; AC/PSRR/start-up and corners on the extraction not run ([bgr586 PEX](blocks/g1_bgr/sim/postlayout/README_bgr586_pex.md)). Simulated: V<sub>REF</sub> 1.04546 V at 27 °C, nominal TC 8.53 ppm/°C, supply current 319.7 µA, I<sub>PTAT</sub> 4.13 µA; mismatch 299 of 300 samples completed and all ≤ 50 ppm/°C, max 46.88; 1 numerical failure ([screen](blocks/g1_bgr/sim/qualification/BGR586_SCREEN300_20260922.md)); output resistance 19.3–25.8 kΩ, VREF pin 1 % settling 1.26 ms with 10 nF at tt/27 °C (output resistance and settling are in the system check, not the PEX record) ([system check](blocks/g1_bgr/sim/system_checks_20260924/RESULTS.md)) | `npn13G2`, thick-oxide MOS, `rppd`, `rhigh` | 3.3 V | not recorded (Sep-19 layout 0.010 mm²) |
| `G1_T2F` | Temperature-to-frequency sensor: PTAT current from the bandgap core into a `cmim` relaxation oscillator with a V<sub>REF</sub> threshold, PTAT and reference modes (`blocks/g1_t2f/layout/`: revision 2 with collector cascodes, 92 × 103 µm, DRC, antenna and LVS clean, PEX done; every HBT within the 1.6 V V<sub>CE</sub> limit). With the chip's BGR586 (simulated, T2F C-PEX + BGR586 schematic-level netlist, typical process): 1.5074 MHz at 25 °C, 4.909 kHz/°C, two-point held-out residual −1.26 °C at −40 °C; 300-sample run: 237 completed and passed ±2 °C, 63 incomplete (numerical watchdog), 0 failed; worst residual over the 237: −1.62 °C at −40 °C, −0.50 °C at 125 °C (derived from the audit file's frequency intervals) ([T2F README](blocks/g1_t2f/README.md)). On the chip netlists: 1.518 MHz at 27 °C, 1.997 MHz at 125 °C, within 0.03 % of the BGR586 block-level values; −40 °C not run to completion. T2F load on `VREF` on the chip netlists: −0.47 mV (tt/27 °C). Start-up and EN-low bias checks ran with the superseded Sep-19 bandgap; with BGR586 not run. Accuracy after calibration with BGR586 over supply, ss/ff and 85 °C: not run. Historical, superseded Sep-19 bandgap: residual −0.85 to +0.17 °C (schematic), −2.5 °C/V (schematic), −3.26 °C/V (post-layout) | `npn13G2`, thick-oxide MOS, `rppd`, `cmim`, LV CMOS output | 3.3 V core, 1.2 V output | 0.009 mm² |
| `G1_DOSE` | Thin-oxide / thick-oxide NMOS canary pair with shared gate, drains pinned out; the drawn enclosed-layout NMOS is excluded from the chip of record | `sg13_lv_nmos`, `sg13_hv_nmos`, drawn ELT | 1.2 / 3.3 V | < 0.001 mm² |
| `G1_SEU` | Plain and triple-modular-redundant shift registers, scrubbed and counted; depth parameterised, 256 + 3 × 128 bits in the assembled digital macro | LV CMOS standard cells | 1.2 V | inside the digital macro |
| `G1_CTRL` | Register file, serial interface, trip timers, scrub state machine; hardened together with `G1_SEU` as one digital macro On r3: the ECO macro (register map 1.2, gate netlist `4b83f181`, re-hardened pin-compatible from run7's floorplan; macro DRC/LVS/antenna/XOR clean, TMR stages ≥ 27.4 µm apart, GLS 21/21; `blocks/g1_padring/reports/signoff-1414r3-20260926/README.md`). run7 (`blocks/g1_ctrl/layout/`) is the historical macro | LV CMOS standard cells | 1.2 V | 0.13 mm² (macro, 360 × 360 µm, 46 pins) |
| `G1_OSC` | Relaxation oscillator clocking the timers and scrubber, 4-bit trim. **Chip variant R0.95** (`RRA`/`RRB` `rppd` l = 111.15 µm, was 117 µm). Isolated macro CPEX run. Simulated with full clock-tree load: 9.436 MHz at nominal trim 8 ([full-tree load](blocks/g1_osc/sim/qualification/fulltree_r095_load_20260924/README.md)); slow/hot (ss, 1.08 V, 125 °C) code 0 reaches 10.447 MHz on the new CPEX (`fulltree_r095_load_20260924/results/slowhot_code0.json`; 10.445 MHz on the pre-CPEX candidate netlist; old block 9.975 MHz) ([qualification](blocks/g1_osc/sim/qualification/README.md)). The 9.436 MHz load includes an estimated 459.8 Ω / 60.4 fF root route. Isolated filled-macro density-only check **failed** (8 markers; chip density passed) and kpex internal LVS **failed** ([r095 physical](blocks/g1_osc/reports/r095_physical_20260924/README.md)). Full PVT and mismatch not run to completion | MOS, `rppd`, `cmim` | 1.2 V | 0.023 mm² (Sep-19 layout) |
| `G1_DUT` | One bare `npn13G2` with E, B, C on pins (`blocks/g1_dut/`: DRC and LVS clean) | `npn13G2` | — | < 0.001 mm² |
| `G1_PADRING` | 24 `sg13g2_io` cells, 24 bondpads, 4 corners, fillers, sealring | `sg13g2_io`, PDK PCells | 3.3 V / 1.2 V | about 1.4 mm² |

Area figures in the table are from the block layouts before the 1414 µm integration, except where the row says otherwise. The core-window figure of the superseded 1350 µm assembly (about 620 × 620 µm) does not describe the chip of record. See
[`padframe/`](padframe/README.md) for the ring geometry. Full specification, pin map
and parameter classification: [`specification/G1_TOP_LEVEL_SPECIFICATION.md`](specification/G1_TOP_LEVEL_SPECIFICATION.md).
Schedule, freeze lines, decisions and pin fallbacks: [`PLAN.md`](PLAN.md).

## Built against

| Thing | Version | How it was established |
| --- | --- | --- |
| PDK | IHP SG13G2, commit `84374023ee8b4b126bebbba67fcbada0a9c0ff0b` | `flow/run.sh` refuses to start unless `/foss/pdks/ihp-sg13g2/COMMIT` matches; `# PDK commit` line in every `g1_top` log |
| Container image | `tapeoutbench-eda`, config `sha256:ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2` | `flow/run.sh` image identity check |
| ngspice | 46 | `ngspice-46` banner in `blocks/g1_top/sim/logs/*c1414*.log` and the BGR/T2F system-check logs |
| ngspice (historical T2F MC only) | 47 | 280 of 300 samples of the historical Sep-19-bandgap `g1_t2f/sim/qualification/mc300_summary.json` ran on image `ab853b72…` (ngspice 47); not used for chip-of-record results |
| KLayout | 0.30.9 | "Your Klayout version is: KLayout 0.30.9" in the 1414 sign-off `run_drc.py` logs |
| kpex (klayout-pex) | 0.3.12 | `kpex --version` in `blocks/g1_bgr/reports/pex/cc_bgr586_20260924/kpex_console.log`; TRIP NF4 extraction record |
| OpenSTA | 3.1.0 | `sta -version` in the container (`blocks/g1_ctrl/reports/sta_merged_sdc_20260924/`) |
| Icarus Verilog | 14.0 (devel) | `iverilog -V` line in every `g1_top` log |
| xschem | 3.4.8RC | `v {xschem version=...}` header of each `.sch` |
| LibreLane | 3.1.0.dev2 | digital macro run7, the r3 ECO macro (`blocks/g1_ctrl/flow/eco/`, run `digital-eco-r3cand2-20260926`) and the superseded 1350 µm assembly flow logs; not used to assemble the 1414 µm chip |
| OpenROAD | 26Q1-1024-gdcf36133a (`openroad-librelane`) | SPEF header of run7 and of the r3 ECO macro; forced by `blocks/g1_ctrl/flow/eco/run_trial.sh` |

The versions come from the logs and records named above. The container was
not re-queried for this README.

## What was actually measured

Physical measurement: **not run**. Block simulation and post-layout results
are recorded in the block READMEs. The chip-level breaker simulation uses real
RTL, transistor-level analog blocks, an ideal clock and fitted output-pad
drivers; its model substitutions and incomplete cases are explicit in
[`blocks/g1_top/README.md`](blocks/g1_top/README.md).

The original chip-level simulation clock bridge can double-count RTL edges.
A focused regression reproduces the issue and verifies the corrected receiver
([bridge evidence](blocks/g1_top/sim/bridge_probe/README.md)). Historical trip
latencies are retained for diagnosis but are not accepted sign-off evidence.

## Assumptions carried into the design

| Assumption | Status |
| --- | --- |
| Drawn, non-PCell transistor geometry (the enclosed-layout NMOS in `G1_DOSE`) is acceptable on the target shuttle provided it is DRC-clean and its extraction is documented | **not applicable to assembled standard-PCell pair; experimental ELT fails `Gat.f`, acceptance not established** |
| Wire-bonding of 70 × 70 µm external bondpads at 112 µm pitch into QFN24, with the die paddle bonded out as a substrate connection | **assumed; bonding-service confirmation pending** |
| Package survives −196 °C to +175 °C for characterisation soaks | not verified; package and fixture qualification required |
| Low-side shunt sensing with common mode within −0.1 V to +0.3 V of ground | design choice |
| `VDDA` (pin 7) tied to the `IOVDD` 3.3 V board rail | required (board): the analog pad's ESD diodes reference `IOVDD`; `VDDA` above `IOVDD` by a diode drop would forward-bias them (`PLAN.md` D14) |
| Trip response target under 10 µs from overcurrent to gate low | **Chip of record r3, full-chip layout-netlist deck** (`r3full`: r3 CDL, ECO RTL, all block extractions, extracted interconnect C, real pads `nodcn`, ideal clock, T2F on): `GATE` < 1 V **1.543 µs** (tt/27 °C), 1.726 µs (ss/125 °C), 1.433 µs (ff/−40 °C) (simulated, RESULTS §11); the +106 ns against the r1/r2 CDL run is one `osc_clk` of sampling phase from the ECO reset release. Earlier: full-chip CDL-driven deck of the r1 CDL with the pre-ECO RTL (map 1.1) (all blocks extracted, real output pad, `pads nodcn`, no top-level wiring C, `cdlv1`), tt/27 °C, compact 28 µs in-range hard fault: `GATE` < 1 V **1.437 µs** after the fault (simulated; [FULLCHIP_CDL](blocks/g1_top/sim/FULLCHIP_CDL_20260925.md)); r3's digital adds about one clock (hand-wired deck: 1.166 vs 1.049 µs; `eco_c_mid_m03` `GATE` < 1 V 1.451 µs). Hand-wired chip netlists (`--blockset c1414`, fitted `GATE` driver, about 7 % optimistic) with the BGR586 and TRIP NF4 extractions (run `c1414fullc`), tt/27 °C, compact 28 µs in-range hard fault: `GATE` < 1 V 1.34544 µs after the fault (simulated; ideal clock, fitted behavioural output pad). The schematic-BGR/TRIP run `c1414v1` gives the same 1.345 µs. Corners (tt/ss/ff), −40/27/85/125 °C and VDD/VDDA ±10 %: 1.306–1.361 µs in every completed cell, with the ideal clock at 9.436 MHz, fitted behavioural `GATE`/`FAULT_N` output pads (optimistic by about 7 %, about +90 ns with the real pad) and the `nodcn`/`bgr=sch` deck deviations (`bgr=sch` is the BGR586 source with 329 Sep-19 capacitors); with the transistor-level oscillator the clock spans 7.61–12.43 MHz over corners at trim 8, so the timer windows scale accordingly (trip path with that clock not run); all 72 cells completed, 0 failed ([RESULTS_20260925](blocks/g1_top/sim/campaigns/RESULTS_20260925.md)) |
| Board powers `VDD` before or with `IOVDD` | required. Every `sg13g2_io` output pad, the tri-state variants included, takes its driver gate signals from core-powered level-up cells. With only `IOVDD` present, `GATE` can float high: simulated 3.288 V ([power screen](blocks/g1_gate/sim/POWER_SCREEN_20260921.md)). Core-first on the chip netlists: `GATE` ≤ 0.073 V while EN is low (simulated, `g1_top` case gB: behavioural front end, PDK output-pad models, **ideal `EN` copy**). Full-chip CDL deck with the real `EN`/`SCLK`/`SDI` pads and `por_n` tie-high (`cdlpwr`, simulated): core-first passed at tt/27, ss/125 °C and (gB_pd) ff/−40 °C, `GATE` ≤ 0.27 mV while EN low; gB ff/−40 °C failed numerically; stock-diode pads not run to completion. The `EN` pad output floats to 0.84–0.92 V without `IOVDD`, so the RTL and G1_GATE latches set spuriously until `IOVDD` passes 1.1 V; `GATE` never rose ([FULLCHIP_CDL](blocks/g1_top/sim/FULLCHIP_CDL_20260925.md)). The independent inhibit stays required for every order ([ELECTRICAL_SYSTEM.md](review/redteam-20260925/ELECTRICAL_SYSTEM.md) M1) |
| Independent load-bus inhibit during every power-up (a `GATE` pull-down is optional) | required (board, corrected 2026-09-25; spec §6 P2). Core-first with 10 kΩ: `GATE` ≤ 0.009 V while EN is low (simulated, case gB_pd). IO-first on the chip netlists (`pads nodcn`), with or without 10 kΩ: `GATE` 3.28–3.30 V for 4.2–4.4 µs until `VDD` is up, at tt/27, ss/125 and ff/−40 °C (simulated, [RESULTS_20260925](blocks/g1_top/sim/campaigns/RESULTS_20260925.md) §5). The pull-down does not replace P1. With IO first, only the independent load-bus inhibit keeps the FET off |
| `EN` held low ≥ 2 ms after both rails are stable when 10 nF sits on the `VREF` pin | required (board/firmware). BGR586 output resistance 22.3 kΩ (tt/27 °C) gives τ ≈ 0.24 ms with 10 nF. Simulated 1 % settling 1.26 ms (tt/27 °C), 1.20 ms (ff/−40 °C), 1.32 ms at ss/125 °C with the pad-less stand-in ([BGR system check](blocks/g1_bgr/sim/system_checks_20260924/RESULTS.md)). Scale the delay with the capacitor: 100 nF needs about 11.8–13.2 ms (simulated, 11.84–11.96 ms at ff/−40 °C) |

## What remains unverified

- Canonical unprojected full-chip LVS: **failed; cause: substrate/tap/diode netlist semantics of the IO-cell reference in the PDK, reproduced with stock cells and with IHP's latest `dev` deck and library; the design-local IO copies match IHP's `dev` library on every layer (PR #1223); upstream issues #1218/#1130 ([evidence](review/upstream/evidence/README.md))**. Only the projected-reference
  comparison passed. The design-local PolyRes IO cells were XOR-checked against IHP's
  `dev` cells (identical); the rest of the IO ring was not XOR-checked against stock cells.
- Full-chip PEX, IR drop/EM and full-chip timing of the final GDS: **not run**.
  Block extractions exist for BGR586 (C only), TRIP NF4, OSC R0.95 (isolated macro) and
  SENSE R100 (partial field). None is an extraction of the assembled chip.
- Chip-level 125 °C transients on the superseded legacy netlists: **failed** (solver
  timestep collapse; retained in `blocks/g1_top/README.md`).
- Chip-level corner, temperature and supply matrices on the chip netlists
  (`g1_top --blockset c1414`): 72/72 matrix cells completed and passed, 0 failed;
  12/12 supply cases passed. T2F at −40 °C is **not run to completion** (numerical,
  three attempts)
  ([RESULTS_20260925](blocks/g1_top/sim/campaigns/RESULTS_20260925.md)). Every cell uses an ideal clock at the tt/27 °C frequency, SENSE pads
  without `dantenna` diodes and the BGR586 schematic view. Only one compact run
  combined the BGR586 and TRIP extractions. The `GATE`/`FAULT_N` output pads are fitted
  behavioural drivers in every trip run. Chip-level PEX is still **not run**.
- Hard-comparator threshold: on the chip netlists the hard path trips at
  30.00–31.25 mV for code 200 (39.25 mV). The TRIP NF4 block bench gives 40–56 LSB
  (7.9–11.0 mV) below code over corners, with a 10–11 LSB spread (code 200 is 39.25 mV at
  V<sub>REF</sub> 1.04 V, 39.45 mV with the BGR586 value 1.04546 V); the soft path is
  within 1 LSB. The cause is the soft comparator's reset kick on the shared input at
  the hard strobe. Simulated characterization and calibration requirement (see the
  specification §4 and §6). The 2× hold-capacitor candidate
  (`blocks/g1_trip/layout/candidates/nf4_hold2x/`) halves it in simulation. It is not
  adopted: decision pending.
- The chip-level SENSE pads use a documented deck deviation (no `dantenna` diodes)
  for faults ≥ 2.3×. The PDK pad diode model stalls the solver there. This deviation is not a verification of the pad.
- Transistor-level oscillator (R0.95) clocking the RTL on the chip netlists, without
  G1_TRIP (simulated): 9.443–9.483 MHz at tt/27 °C with a 0.5 ns step, against the 9.436 MHz
  ideal clock of the trip decks. The corner values (ss/125 °C 7.61 MHz, ff/−40 °C 12.43 MHz)
  carry a 2 ns-step bias. The gear supply-corner runs **failed** numerically. The
  ff/−40 °C, `VDD` 1.32 V trap re-run completed at 12.41 MHz; the ss/125 °C, `VDD`
  1.08 V trap re-run `c1414oscv3` is **not run to completion** (timeout at its
  14 000 s wall bound at 17.82 µs of 36 µs, no numerical failure) ([RESULTS_20260925](blocks/g1_top/sim/campaigns/RESULTS_20260925.md) §6).
  The trip path with the transistor-level oscillator in the loop: **not run**.
- IHP's intake checks (MPW Rejection Test) and IHP's written confirmation of the
  1.999396 mm² die area: **not run** / open. The stock precheck mode passed on r3 (and r2), the bond map is
  bound to r3 and the registration text is corrected since r2
  ([tape-in checklist](review/TAPEIN_PACKAGE_20260924.md)).
- Package/bond-wire parasitics and physical measurements: **not run**.
- Bonding-service acceptance and final submission review: **not run**.

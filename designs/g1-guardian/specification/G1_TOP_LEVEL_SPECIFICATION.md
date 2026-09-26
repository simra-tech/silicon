# G1 Radiation-Aware Node Guardian — Top-Level Specification & Architecture Record

## 1. Overview and intent

G1 is a mixed-signal test chip on the IHP SG13G2 0.13 µm SiGe BiCMOS open PDK.
It sits between a power rail and a commercial compute load and does four things:
disconnects an external FET on a programmed overcurrent signature while letting ordinary
load steps through; measures its own temperature with an HBT-based sensor;
provides transistor-leakage coupons for dose characterization; and counts
upsets in a scrubbed register. Telemetry and settings go over a three-wire
serial interface.

Design principles:

- **Device implementation:** the bandgap and temperature sensor use
  `npn13G2`; the SENSE revision-B input pairs are thick-oxide PMOS.
  Digital and switching functions use CMOS.
- **Board-measurable:** every signal is DC or below 10 MHz. The die is packaged
  in QFN24 and measured in a socket. No RF pads.
- **Device characterization:** the assembled NMOS coupons are standard LV
  and HV PCells with shared gate; a separate HBT exposes base current.
  No dose calibration or radiation qualification has been measured. The
  experimental enclosed-layout device is absent from the assembled chip.
- **Direct device access:** one HBT and the canary transistors are pinned out
  so the physics can be measured without the on-chip readout.
- **Area:** 1.414 × 1.414 mm die including sealring and IO ring (chip of record, owner decision 2026-09-24; it supersedes the 1.35 mm LibreLane assembly). The 1 × 1 mm allocation was withdrawn on 2026-09-18 because the IO cells need an external bondpad and sealring clearance (`PLAN.md` D10); 1.2 mm was withdrawn on 2026-09-19 when the laid-out macros exceeded its core window (D13).

## 2. Block breakdown

| Block | Function | Devices | Interfaces |
| --- | --- | --- | --- |
| `G1_SENSE` | Low-side Kelvin shunt amplifier. Differential input 0 to 50 mV across an external shunt, gain 20, bandwidth ≥ 2 MHz, input-referred offset target < 0.5 mV after trim. Common-mode −0.1 to +0.3 V. Difference amplifier around a 3.3 V PMOS-input OTA with a V<sub>REF</sub>-derived output pedestal (`PLAN.md` D1). | thick-oxide PMOS input pair, thick-oxide MOS, `rppd` | in: `SENSE_P`, `SENSE_N`; out: internal `ISENSE` (pedestal + 20 × V<sub>shunt</sub>) |
| `G1_TRIP` | Two clocked comparators on `ISENSE`: (a) hard threshold, trips after N consecutive samples above it (blanking); (b) soft threshold, trips when an up/down sample counter reaches the programmed trip-off window (`PLAN.md` D3). Thresholds are 8-bit codes of V<sub>REF</sub>-referenced resistor-string DACs; hysteresis and all windows programmable. | 1.2 V StrongARM comparators with SR latches, two 8-bit `rppd` string DACs, digital timers in `G1_CTRL` | in: `ISENSE`, registers (`TRIP_SET` is not connected on the chip of record, §3); out: `cmp_soft`, `cmp_hard` to `G1_CTRL` |
| `G1_GATE` | Drives an external low-side logic-level N-FET. On `TRIP`: gate low within the response target, then latched off or retriggered after a programmable hold. Enable input. | `sg13g2_IOPadOut30mA`, LV/HV level shift | out: `GATE`, `FAULT_N`; in: `EN` |
| `G1_BGR` | Op-amp-less, self-biased cascoded HBT bandgap in the 3.3 V domain (chip variant `bgr_loop24_qref4_r253p465_hv06`, "BGR586": 336 HV MOS, 301 `npn13G2`, 399 resistors), in which the PTAT/bias loop is built from 24 parallel original units (feedback resistors scaled to R/24, XR17–22 at 53.465 µm to centre the nominal TC) and the V<sub>REF</sub> (Qref) branch from 4 units, to average HBT and resistor mismatch (`../blocks/g1_bgr/sim/qualification/BGR_REMEDY_REVIEW_20260922.md`). Simulated, tt/27 °C: V<sub>REF</sub> 1.04546 V, I<sub>PTAT</sub> 4.13 µA, nominal TC 8.53 ppm/°C over −40…125 °C, supply current 319.7 µA (`../blocks/g1_bgr/sim/postlayout/README_bgr586_pex.md`), output resistance 22.3 kΩ (`../blocks/g1_bgr/sim/system_checks_20260924/RESULTS.md`). | `npn13G2`, thick-oxide MOS, `rppd`, `rhigh` | out: `VREF`, internal `IPTAT`, `VBE`, `dVBE` |
| `G1_T2F` | HBTs at a 1:8 current ratio; ΔV<sub>BE</sub> converted to a PTAT current that charges a `cmim` relaxation oscillator against a V<sub>REF</sub>-derived threshold, so frequency is linear in T (`PLAN.md` D2); register-selectable reference mode runs the same oscillator from V<sub>REF</sub>/R so the ratio cancels C and thresholds. With the chip's BGR586: 1.507 MHz at 25 °C (block, simulated); 1.518 MHz at 27 °C on the chip netlists (simulated). The earlier "about 1.6 MHz" used the superseded Sep-19 bandgap. | `npn13G2`, thick-oxide MOS, `rppd`, `cmim`, LV CMOS output | out: `TEMP_OUT`; mode bits from registers |
| `G1_DOSE` | Two NMOS canaries with a shared gate and both drains pinned out: a thin-oxide `sg13_lv_nmos` beside a thick-oxide `sg13_hv_nmos`. `D_ELT` is a legacy pin name for the HV drain; experimental ELT geometry is excluded. No on-chip readout in run 1. | `sg13_lv_nmos`, `sg13_hv_nmos` | pins: `G_SHARED`, `D_STD`, `D_ELT` |
| `G1_SEU` | Plain shift register and per-stage-voted TMR register (depth parameterised, 256 + 3 × 128 bits in the assembled macro), continuously shifted and scrubbed against a selectable pattern (checkerboard, all-0, all-1; constant patterns give the static-data case); TMR-protected counters for plain errors, TMR corrected events and TMR uncorrectable errors. | LV CMOS standard cells | registers |
| `G1_CTRL` | Register file, three-wire serial (mode-0 SPI-like, 7-bit address + R/W bit, 8-bit data, 24-clock read frame), trip timers, scrub state machine, event counters; full map in `G1_REGISTER_MAP.md`. | LV CMOS standard cells | `SCLK`, `SDI`, `SDO` |
| `G1_DUT` | One `npn13G2` HBT, all three terminals on analog pads, substrate to `VSS`. | `npn13G2` | `HBT_E`, `HBT_B`, `HBT_C` |

## 3. Pin map (24)

| Die pad | QFN24 lead | Pin | IO cell | Domain | Function |
| ---: | ---: | --- | --- | --- | --- |
| 1 | 1 | `VDD` | `sg13g2_IOPadVdd` | 1.2 V | core supply |
| 2 | 2 | `VSS` | `sg13g2_IOPadVss` | 0 V | core ground, substrate |
| 3 | 3 | `IOVDD` | `sg13g2_IOPadIOVdd` | 3.3 V | IO and analog supply |
| 4 | 4 | `IOVSS` | `sg13g2_IOPadIOVss` | 0 V | IO ground |
| 5 | 5 | `VSS` | `sg13g2_IOPadVss` | 0 V | second ground pad |
| 6 | 6 | `IOVSS` | `sg13g2_IOPadIOVss` | 0 V | second IO ground pad |
| 7 | 7 | `VDDA` | `sg13g2_IOPadAnalog` (bare terminal) | 3.3 V | analog supply for the 3.3 V core blocks (bandgap, sensor, sense amplifier, comparator DACs, gate latch; G1_OSC uses 1.2 V VDD); tied to the same 3.3 V rail as `IOVDD` on the board (`PLAN.md` D14) |
| 8 | 8 | `SENSE_P` | `sg13g2_IOPadAnalog` | analog | shunt Kelvin, positive |
| 9 | 9 | `SENSE_N` | `sg13g2_IOPadAnalog` | analog | shunt Kelvin, negative |
| 10 | 10 | `GATE` | `sg13g2_IOPadOut30mA` | 3.3 V | external N-FET gate |
| 11 | 11 | `FAULT_N` | `sg13g2_IOPadOut4mA` | 3.3 V | low while tripped |
| 12 | 12 | `EN` | `sg13g2_IOPadIn` | 3.3 V | enable / reset of trip latch |
| 13 | 18 | `TRIP_SET` | `sg13g2_IOPadAnalog` | analog | external hard-threshold override, optional. **Not connected on the chip of record:** the pad's core net `i_core_trip_set` has no core load and `g1_trip` has no `trip_set_sel` input, so `MODE.TRIP_SET_SEL` has no effect (canonical CDL; `../review/redteam-20260925/DIGITAL.md` N2) |
| 14 | 17 | `SCLK` | `sg13g2_IOPadIn` | 3.3 V | serial clock |
| 15 | 16 | `SDI` | `sg13g2_IOPadIn` | 3.3 V | serial data in |
| 16 | 15 | `SDO` | `sg13g2_IOPadOut4mA` | 3.3 V | serial data out |
| 17 | 14 | `TEMP_OUT` | `sg13g2_IOPadOut16mA` | 3.3 V | temperature as frequency |
| 18 | 13 | `VREF` | `sg13g2_IOPadAnalog` | analog | bandgap output, for test |
| 19 | 24 | `G_SHARED` | `sg13g2_IOPadAnalog` | analog | canary pair gate |
| 20 | 23 | `D_STD` | `sg13g2_IOPadAnalog` | analog | standard NMOS drain |
| 21 | 22 | `D_ELT` | `sg13g2_IOPadAnalog` | analog | HV NMOS drain in the assembled chip; legacy pin name |
| 22 | 21 | `HBT_E` | `sg13g2_IOPadAnalog` | analog | test HBT emitter |
| 23 | 20 | `HBT_B` | `sg13g2_IOPadAnalog` | analog | test HBT base |
| 24 | 19 | `HBT_C` | `sg13g2_IOPadAnalog` | analog | test HBT collector |

Side assignment (die pads, GDS view): pads 1 to 6 south, 7 to 12 east, 13 to 18 north, 19 to 24
west, so that the analog device pins sit together on one side away from the
switching outputs, and the supplies are split between two sides.

**Note 2026-09-25 (owner decision): die pad and package lead numbers.** "Die pad" is the
pad number in the GDS, the bond map and all block documents; it is unchanged. "QFN24 lead"
is the package pin. Each die pad is bonded to the lead directly opposite it, with no crossing
wires, under the standard counter-clockwise lead numbering with pin 1 at the top-left of the
top view; the die sits rotated 90° clockwise from the GDS view, so the GDS south edge faces
leads 1–6. Die pads 1–12 land on leads 1–12. Die pads 13–18 and 19–24 run clockwise on the die, so they land on
leads 18–13 and 24–19 (reversed within their sides). Earlier revisions of this table had one number
column, which cannot be both the die pad and the package pin for pads 13–24. Board
schematics and pinouts use the QFN24 lead column. Plan, table and drawing:
[`../padframe/BONDPLAN_20260925.md`](../padframe/BONDPLAN_20260925.md); bond map
`../padframe/bondmap_20260926_r4.csv` (column `qfn24_lead`; bound to r3 `7d07a784…`; the r3 CSV is r2-bound and superseded).

The 3.3 V analog blocks are supplied from `VDDA`, not from the ring's `IOVDD`: the `sg13g2_io` cells give no DRC-legal way to tap their `iovdd` rail into the core (the rail sits behind `vdd`/`vss` on every metal level), so `VDDA` enters through the bare terminal of an analog pad and is strapped to the macros inside the core. Analog ground shares the core `VSS` grid. `VDDA` must not exceed `IOVDD` by more than a diode drop, which the shared board rail guarantees.

Analog pads carry the IO cell's ESD diodes to `IOVDD`/`IOVSS`. Their leakage
bounds the lowest usable current on the device pins; the measurement plan keeps
device currents in the nanoampere-to-microampere range for that reason.

## 4. Parameter classification

| Parameter | Value / range | Status | Basis |
| --- | --- | :---: | --- |
| Process | IHP SG13G2 0.13 µm SiGe BiCMOS, open PDK | Specified | PDK |
| HBT primitive | `npn13G2` | Specified | PDK model library |
| Core supply | 1.2 V (1.08 to 1.32) on one `VDD` pad | Specified | PDK |
| Analog supply | 3.3 V (3.0 to 3.6) on `VDDA`, tied to the `IOVDD` rail on the board. Current of the chip-of-record 3.3 V blocks: BGR586 alone 319.7 µA (simulated, tt/27 °C); chip 3.3 V analog sum (BGR586 + SENSE + TRIP, armed, 1 A load) 1421 µA at tt/27 °C, 957 µA (ss/−40 °C) to 2188 µA (ff/125 °C), 1415/1427 µA at 3.0/3.6 V (simulated, `g1_top --blockset c1414`, BGR586 schematic view (its extraction is DC-identical), [RESULTS_20260925](../blocks/g1_top/sim/campaigns/RESULTS_20260925.md)). Digital and IO rail currents are not in this sum. The earlier 1.5 mA sum used the Sep-19 bandgap (22 µA) | Specified | block READMEs; D14; `../blocks/g1_bgr/sim/postlayout/README_bgr586_pex.md` |
| IO / analog supply | 3.3 V (3.0 to 3.6) | Specified | `sg13g2_io` |
| Die | 1414 × 1414 µm incl. sealring (`g1_chip_top_1414.gds`, `629d303a…`) | Specified | owner decision 2026-09-24; `../blocks/g1_padring/reports/signoff-1414-20260924/README.md`; QFN24 accepts up to 2 × 2 mm |
| Package | QFN24, 4 × 4 mm, 0.5 mm pitch, 200 µm die | Specified | packaging offer |
| Shunt sense range | 0 to 50 mV differential, low-side; `ISENSE` = 1.0 V pedestal + 20 × V<sub>shunt</sub>, i.e. 1.0 to 2.0 V | Specified | chip variant comp45 + R100: simulated gain 19.905 to 20.050 over 100 mismatch samples (`../blocks/g1_sense/reports/R100_MC_100_20260923.md`); earlier revision 19.98 to 19.99, 3.6 to 4.8 MHz in `../blocks/g1_sense/README.md` |
| Trip response | <10 µs from a persistent hard fault outside the guard band to `GATE` <1.0 V; only after arming and outside the inrush mask, for declared settings/clock/load | Specified target | `HARD_N` counts decisions every 2 oscillator cycles; default N=4. **Chip of record r3, full-chip layout-netlist deck (`r3full`: r3 canonical CDL `5e47ae02` + frozen ECO RTL (map 1.2) + all block extractions + extracted top-level interconnect (C only) + IO pad cells with the `dantenna` diodes removed (`nodcn`); the stock-diode runs **failed** at 1.679 µs (functional cases) and were **not run to completion** (power-up stalled at 1.19 ns), numerically + gear, 1 ns maximum step + ideal 9.436 MHz clock + T2F on; tt/27 °C unless stated; simulated), compact 28 µs in-range fault: `GATE` < 1 V 1.543 µs at tt/27 °C, 1.726 µs at ss/125 °C, 1.433 µs at ff/−40 °C** (decision 1.164 µs at all three) (`../blocks/g1_top/sim/FULLCHIP_CDL_R3_20260926.md` (final record `ff774d24`); RESULTS §11). The +106 ns against the r1 CDL run with the map-1.1 RTL (1.437 µs) is one `osc_clk` period of sampling phase from the ECO's later reset release (the decision moves 1.058 → 1.164 µs), not a circuit change. At ss/125 °C the decision time is unchanged (1.1638 µs); the real `sg13g2_IOPadOut30mA` pulls the 5 nF gate down more slowly, so `GATE` < 1 V is 1.726 µs. Earlier: full-chip deck generated from the projected-LVS-matched canonical CDL of r1 (`af5a4dbd`; canonical LVS fails on the IO cells) with the pre-ECO RTL (map 1.1) (all blocks extracted, real `sg13g2_IOPadOut30mA`, `pads nodcn`, no top-level wiring C, RTL co-simulation, ideal clock; `cdlv1`), compact 28 µs in-range fault, tt/27 °C: `GATE` < 1 V **1.437 µs**, trip decision 1.058 µs (simulated, `../blocks/g1_top/sim/FULLCHIP_CDL_20260925.md`). The r3 digital (map 1.2) adds about one clock to the decision (hand-wired deck 1.166 vs 1.049 µs; `eco_c_mid_m03` `GATE` < 1 V 1.451 µs with the fitted driver); r3 on the CDL deck: `r3full` above. Hand-wired chip netlists (`g1_top --blockset c1414`) with the BGR586 and TRIP NF4 extractions (run `c1414fullc`): 1.34544 µs (simulated, ideal clock at the R0.95 loaded frequency, fitted behavioural `GATE` pad, about 7 % optimistic); the schematic-BGR/TRIP run `c1414v1` gives the same 1.345 µs. tt/ss/ff × −40/27/85/125 °C and VDD/VDDA ±10 %, 1.8×/3×/4× faults: 1.306–1.361 µs in every completed cell with the fitted driver (add about +90 ns for the real pad). The clock stays ideal at 9.436 MHz, the `GATE`/`FAULT_N` output pads are fitted behavioural drivers, the SENSE pads have no `dantenna` and the BGR is the `bgr=sch` view (BGR586 source with 329 Sep-19 capacitors). With the corner clock (7.61–12.43 MHz at trim 8) the trip time was not simulated (§6). All 72 matrix cells completed (72/72, none failed) ([RESULTS_20260925](../blocks/g1_top/sim/campaigns/RESULTS_20260925.md)) |
| I²t window | 50 µs to 10 ms, programmable | Assumed | design target |
| Hard threshold | 8-bit DAC code, 0.5 to 1.0 of the sense full scale (about 25 to 50 mV of shunt drop), programmable; nominal load current is mapped to 20 to 25 mV of the 50 mV range | Specified (code range); effective threshold: simulated characterization result | `blocks/g1_trip/INTERFACE.md`; the earlier "1.5× to 8× nominal" was unreachable. **Effective hard threshold is below the code (simulated):** the TRIP NF4 block bench trips 40–56 LSB (7.9–11.0 mV of shunt) below the DAC code over tt/ss/ff at codes 200 and 254, corner spread 10–11 LSB; soft path within 1 LSB (`../blocks/g1_trip/sim/postlayout/README.md`, `results_postlayout_nf4.txt`). Chip of record r3, full-chip layout-netlist deck (`r3full`, tt/27 °C, simulated; `../blocks/g1_top/sim/FULLCHIP_CDL_R3_20260926.md`): code 200 (39.25 mV), no trip at 28.75 mV (1.15×); at 31.25 mV (1.25× = 0.80T) a hard trip on the same strobe as at 1.8×, i.e. inside the uncalibrated no-trip region, as documented by the comparator kick offset: calibration requirement (the bench brackets the effective threshold, §6). Hand-wired chip netlists, code 200 (39.25 mV), tt/27 °C: no trip at 30.00 mV, trip at 31.25 mV ([RESULTS_20260925](../blocks/g1_top/sim/campaigns/RESULTS_20260925.md) §4). Cause: the soft comparator's reset kick lands on the shared input at the hard strobe. Consequence: hard calibration lands 40–56 codes above nominal (block bench; about 41–47 codes on the chip netlists at tt/27 °C), and the usable hard range is about 25–40 mV of shunt. Code 200 is 39.25 mV at V<sub>REF</sub> 1.04 V (39.45 mV with the BGR586 value 1.04546 V). A parked 2× hold-capacitor candidate (`../blocks/g1_trip/layout/candidates/nf4_hold2x/`) halves the offset in simulation; not adopted, owner decision pending. Calibration requirement in §6; not a sign-off failure |
| `TEMP_OUT` frequency | With the chip's BGR586 (simulated, PTAT mode, typical process): 1.5074 MHz at 25 °C, 4.909 kHz/°C (block: T2F C-PEX + BGR586 schematic-level netlist, `../blocks/g1_t2f/sim/qualification/t2f586-nominal-calibration-20260922.json`); on the chip netlists 1.518 MHz at 27 °C and 1.997 MHz at 125 °C, within 0.03 % of the BGR586 block-level line (computed), −40 °C not run to completion, 85 °C and ss/ff not run ([RESULTS_20260925](../blocks/g1_top/sim/campaigns/RESULTS_20260925.md) §7). T2F load on `VREF`: −0.47 mV on the chip netlists (tt/27 °C, BGR586 `bgr=sch`, T2F on vs off; `../review/redteam-20260925/ELECTRICAL_SYSTEM.md` N1); block-level base-current load 5.5 nA (ff/−40 °C) to 72 nA (ss/125 °C) and −1.8 mV at tt/27 °C were simulated on the Sep-19-bandgap bench. Start-up times and the EN-low "nothing floats" bias result (`../blocks/g1_t2f/sim/system_checks_20260924/RESULTS.md`) are from the superseded Sep-19 bandgap bench; with BGR586 not run. Historical, superseded Sep-19 bandgap: 1.59 MHz at 25 °C, 5.2 kHz/°C, 1.2 to 2.4 MHz over −40 to 175 °C; ±15 % process spread before calibration (not re-established with BGR586) | Specified (simulated) | `../blocks/g1_t2f/README.md` |
| Sensor accuracy | ±2 °C after fixed per-sample two-point calibration, −40 to 125 °C | Simulated characterization result (not a sign-off gate) | **With the chip's BGR586** (T2F C-PEX + BGR586 schematic-level netlist, typical process, nominal rails; `../blocks/g1_t2f/sim/qualification/t2f586-300sample-audit-20260923.json`): 300 attempted, 237 completed all four temperatures and passed ±2 °C, 63 incomplete (numerical watchdog), 0 completed samples failed; nominal held-out residual −1.26 °C at −40 °C; worst residual over the 237 completed samples −1.62 °C at −40 °C and −0.50 °C at 125 °C (derived from the audit file's per-leaf frequency intervals, not a committed summary). Established: two-point calibration keeps the 237 completed samples within ±2 °C at typical process and nominal supply. Not established: the 63 incomplete samples, supply sensitivity, ss/ff corners, 85 °C and the chip-level −40 °C point with BGR586, the BGR586 C-PEX in the T2F loop, package stress. Historical, superseded Sep-19 bandgap (`mc300_summary.json`, 280/300 samples on an ngspice-47 image): linear two-point 14/300 fail, frozen lookup 0/300 fail (unadopted in firmware); residual −0.85…+0.17 °C and −2.5 °C/V (schematic), −3.26 °C/V (post-layout) |
| `VREF` (on-chip node and pad) | 1.04546 V (simulated, tt/27 °C) | Simulated characterization result | On the on-chip `VREF` node the clock couples 33.1 mV p-p (real oscillator) to 46.2 mV p-p (ideal clock) of ripple, mean unchanged 1.0454–1.0455 V; sampled thresholds unaffected (extracted top-level interconnect, `c1414icx`, RESULTS §9). The `VREF` pad with 10 nF does not see this ripple; measurements at the pad do not show it |
| Characterisation range | 77 K to 175 °C | Assumed | package limits, not verified |
| Absolute maximum shunt voltage at the sense pins (powered) | ≤ 100 mV differential | Specified (derived, 2026-09-25) | Above about 115 mV `ISENSE` saturates at 3.288 V and the comparator input node `icmp` (= `ISENSE`/2, up to 1.644 V) exceeds the 1.2 V (1.32 V max) thin-oxide gate rating of the comparator inputs (simulated, `../review/redteam-20260925/ELECTRICAL_SYSTEM.md` S1). The 3×/4× (75/100 mV) and 150 mV stress fixtures are characterization only; SOA not simulated. An open `SENSE_P` lead drives `icmp` to 1.644 V continuously while powered: do not leave `SENSE_P` open |
| Sense-amp input offset | Residual <0.5 mV after calibration. Signed digital correction −128…127, ~0.196 mV/code; available range depends on threshold | Simulated characterization result (not a sign-off gate) | Chip variant R100, standalone: 100/100 samples ≤ 0.5 mV, worst 498 µV, ideal continuous correction (`../blocks/g1_sense/reports/R100_MC_100_20260923.md`). The rev-B 43/100 failures belong to the earlier block. Code 254 permits only +1 step; joint calibrated chip MC not run |
| ELT NMOS | Experimental layout excluded from assembled chip | Not applicable to assembled chip | `blocks/g1_dose/README.md`; historical `Gat.f` failure retained |
| Total power | <10 mW, sum of core, analog and IO rail input power, declared load/activity | Specified target | Full operating-state coverage not run |
| BGR temperature coefficient | ≤50 ppm/°C over −40…125 °C | Simulated characterization result (not a sign-off gate) | Chip BGR586: 299 of 300 mismatch samples completed and all ≤ 50 ppm/°C, max 46.88 ppm/°C; 1 numerical watchdog failure, no TC assigned (`../blocks/g1_bgr/sim/qualification/BGR586_SCREEN300_20260922.md`). The 54/100 failures belong to the superseded Sep-19 bandgap |
| SENSE gain / bandwidth | 20 ±0.1 / ≥2 MHz, common mode −0.1…+0.3 V | Specified target | Selected block results exist; complete corners and joint loaded PEX not run |
| OSC trim reach | 10 MHz reachable by a code 0…15 at supported PVT | Simulated characterization result (not a sign-off gate) | Chip variant R0.95: slow/hot (ss, 1.08 V, 125 °C) code 0 reaches 10.447 MHz on the new CPEX (10.445 MHz on the pre-CPEX candidate netlist `f08bf051`; old block 9.975 MHz); loaded nominal trim 8 9.436 MHz, including an estimated 459.8 Ω / 60.4 fF root route (`../blocks/g1_osc/sim/qualification/README.md`, `fulltree_r095_load_20260924/`). Expanded mismatch and rail perturbation not run to completion |

## 5. Verification gates

Status is scoped to the recorded subset; a passed subset does not pass its
unrun extensions. Evidence index: block READMEs, `../blocks/g1_padring/reports/signoff-1414r3-20260926/README.md` (physical checks of the chip of
record `g1_chip_top_1414_r3.gds`, `7d07a784…`, 2026-09-26; r2 `9049e87b…` and r1 `629d303a…` in `signoff-1414r2-20260925/` and `signoff-1414-20260924/`) and `../blocks/g1_top/README.md` (chip-level simulation,
`--blockset c1414`). These are baseline facts, not claims that the closure campaigns have completed.
`../review/G1_DESIGN_REVIEW.md` (21 Sep) describes the superseded 1350 µm chip and is
historical, not evidence for the chip of record.
BGR TC, trimmed SENSE residual, OSC 10 MHz reach and T2F ±2 °C are simulated characterization
results (§4), not sign-off gates.

| Gate | Scope | Status / remaining coverage |
| --- | --- | --- |
| Schematic simulation | Recorded nominal block cases | passed subsets; complete corner/load matrix not run |
| Corner / mismatch | Chip-of-record block ensembles (standalone) | characterization, not a gate: SENSE R100 100/100 ≤ 0.5 mV (worst 498 µV); BGR586 299/300 completed ≤ 50 ppm/°C (max 46.88), 1 numerical failure; T2F with BGR586 237/300 completed and passed ±2 °C, 63 incomplete (historical Sep-19 bandgap: 14/300 linear-calibration failures, 0/300 lookup); OSC R0.95 slow/hot code 0 10.447 MHz (CPEX). The 43/100 SENSE and 54/100 BGR failures are historical blocks. Joint calibrated chip MC: not run |
| Temperature | Model-supported −40…125 °C | joint extracted subsets completed with linear-calibration failures; numerical failures retained; 300-sample and adverse coverage incomplete |
| Beyond-range temperature | 150/175 °C and 77 K | selected exploratory data only; qualification not applicable with nominal model extrapolation |
| RTL / functional GLS | ECO RTL (register map 1.2, `../blocks/g1_ctrl/ECO_20260925.md`), built 256 + 3×128 configuration | RTL: ECO test set passed (`../blocks/g1_ctrl/sim/eco_20260925/`). GLS of the chip's digital netlist `4b83f181` (r3): 21 tests / 260 checks passed, zero-delay and SDF typ (`../blocks/g1_ctrl/sim/gls_eco_r3v2/`); red-team bench on the netlist: R3 **fails** (serial framing, out of the ECO scope). Icarus executes no timing checks and drops part of the SDF delay model (68 unsupported `ifnone` paths), so timed GLS is unqualified; fast/slow SDF GLS: not run; formal equivalence of the ECO RTL against `4b83f181`: not run. The pre-ECO results (run7 / `6181b988`) are history |
| Breaker co-simulation | Corrected-clock schematic cases | passed subsets; old clock-bridge timings invalid for acceptance |
| Chip-level simulation, chip netlists | `g1_top --blockset c1414`: BGR586 C-PEX or schematic, SENSE R100 partial C, TRIP NF4 C-PEX, R0.95 clock frequency, real RTL | tt/27 °C passed: 28 µs hard fault (transistor-level front end, BGR586 and TRIP NF4 extractions, run `c1414fullc`) `GATE` < 1 V 1.34544 µs after the fault (`c1414v1`, schematic BGR/TRIP: 1.345 µs); with the behavioural front end, the 1 ms soft window trips at 1.059 ms and a 100 µs 1.5× pulse does not trip; core-first power-up `GATE` ≤ 0.073 V with EN low; CDL-vs-deck connectivity audit 0 unexplained differences (`../blocks/g1_top/sim/campaigns/cdl_vs_deck_20260925.txt`). Corner/temperature matrix (q, c_mid, c, e20, f_mid, b_s × tt/ss/ff × −40/27/85/125 °C): 72/72 cells completed and passed, none failed (the last 12 as `_r4` re-runs, including q ss/125 °C as `q_ss_125C_r4_c1414m`). T2F at −40 °C: not run to completion (numerical, three attempts). Transistor-level OSC at ss/125 °C, `VDD` 1.08 V: not run to completion (`c1414oscv3`, 14 000 s wall bound). Supply ±10 % (c_mid, q): 12/12 passed. Hard faults: `GATE` < 1 V 1.306–1.361 µs. Stock-pad corners (`c1414k1`): 10 passed, 2 not run to completion. Both BGR586 and TRIP extractions: compact c_mid passed, full length not run to completion. Deviations: ideal clock at the tt/27 °C frequency, `--inpads nodcn` (SENSE pads without `dantenna`), BGR586 schematic view (`bgr=sch`, with 329 Sep-19 capacitors), fitted behavioural `GATE`/`FAULT_N` output pads (`outpads = beh` in every trip run; about 7 % optimistic on `GATE` < 1 V against the real pad, CDL-driven reference 1.437 vs 1.345 µs). Chip-level PEX: not run. Effective hard threshold at code 200: 30.00–31.25 mV (characterization, §4) ([RESULTS_20260925](../blocks/g1_top/sim/campaigns/RESULTS_20260925.md)) |
| Chip-level runs with extracted top-level interconnect | `c1414icx`: `c_mid` compact, `c_mid` 1.25× with SENSE route resistances, `q`, `osc`; tt/27 °C | passed; like-for-like (compact timeline, `c1414fullc`) the `GATE` < 1 V change is < 0.1 ns (the earlier "≤ 10 ns" compared different timelines); C-only interconnect (SENSE route R only in the `srr` run); extraction of r1 geometry, valid for r3 because r3 differs only inside the macro and in fill. `VREF` clock ripple 33–46 mV p-p on the on-chip node, sampled thresholds unaffected (QUIET within 0.05 mV). `q` with T2F on (`c1414icx2`): **failed** numerically at 40.8 µs (`xbgr.xq56`); its no-interconnect reference `c1414icx2ref` completed, no trip. Pre-ECO RTL (`../blocks/g1_top/sim/campaigns/RESULTS_20260925.md` §9) |
| Full-chip layout-netlist post-layout campaign (r3) | r3 canonical CDL `5e47ae02` + frozen ECO RTL (map 1.2) + all block extractions + extracted top-level interconnect (C only) + IO pad cells with the `dantenna` diodes removed (`nodcn`); the stock-diode runs **failed** at 1.679 µs (functional cases) and were **not run to completion** (power-up stalled at 1.19 ns), numerically + gear, 1 ns maximum step + ideal 9.436 MHz clock + T2F on; tt/27 °C unless stated; simulated | passed for the listed cases: `q` 44 µs no trip; `c_mid` compact `GATE` < 1 V 1.543 / 1.726 / 1.433 µs (tt/27, ss/125, ff/−40 °C); `c`, `e20` 1.532 µs; `f_mid` re-arms; `hard_pulse` no trip; core-first power-up gB/gB_pd `GATE` ≤ 31 µV while EN low (passed); the trip latches set spuriously while `IOVDD` is absent (`tripped_max` 1.22 V; `EN` pad output floats to 0.86 V), covered by P2; gA IO-first 3.30 V for 4.34 µs (P1). `b_s` soft trip `GATE` < 1 V 28.131 µs; `osc` (real R0.95 clocking the RTL, 9.4416 MHz, frames decoded, no trip); **All 15 requested cases were run (`q`, `c_mid` tt/ss125/ff−40, `c`, `e20`, `f_mid`, `hard_pulse`, `b_s`, `osc`, gB, gB_pd, gA, 1.15×, 1.25×): 13 pass (12 functional cases and the 1.15× no-trip witness); gA expected-fail (P1); near-threshold: 1.15× no trip, 1.25× (31.25 mV = 0.80T at code 200) trips inside the uncalibrated no-trip region, as documented by the comparator kick offset → calibration requirement (bench brackets the effective threshold).** Not run on this deck: series wire R, other corners, supply ±10 %, T2F accuracy, the ≈ 1 ms soft cases, hardened macro gate netlist + SPEF co-simulation (every run co-simulates the ECO RTL); trip path with the transistor-level oscillator (the `osc` case is `q` only; the trip rows use the ideal clock); power-up gB/gB_pd/gA at ss/ff; near-threshold points at corners and with `FAST_EN`=1; `f_mid`/`b_s`/`hard_pulse` at corners (`../blocks/g1_top/sim/FULLCHIP_CDL_R3_20260926.md` (final record `ff774d24`); RESULTS §11) |
| Full-chip simulation from the layout netlist | Deck generated from the r1 canonical CDL `g1_chip_top_1414.cdl` (projected-LVS-matched; canonical LVS fails on the IO cells) with the pre-ECO RTL (map 1.1) (all blocks extracted, real IO pads with `pads nodcn`, no top-level wiring C, RTL co-simulation, ideal clock), tt/27 °C; r3 CDL with the ECO RTL: run as `r3full` (row above) | passed for `c_mid` compact: trip decision 1.058 µs, `GATE` < 1 V 1.437 µs, < 0.33 V 1.673 µs (`../blocks/g1_top/sim/FULLCHIP_CDL_20260925.md`). `q` 44 µs with the T2F on: passed, no trip, `VDDA` 1462 µA (run `cdlpwr`, 9762 s); core-first power-up: see the power-order row. The CDL omits `ng` on 34 SENSE devices and the NF4 pair (simulation-source limitation; SENSE current −7.7 % in that deck, timing unaffected). Other corners/cases: not run |
| Chip-level runs with the ECO RTL | hand-wired chip deck (`run_top.py --blockset c1414`): block extractions with the BGR586 schematic view (`bgr=sch`), SENSE pads without `dantenna`, fitted `GATE` driver (about 7 % optimistic), ideal clock; not a full-chip extraction; frozen ECO RTL (MODE 0x03). `eco4` regression: `q`, `hard_pulse`, `c_mid` (tt/27, ss/125, ff/−40 °C), `c`, `e20`, `f_mid`, `b_s`, power-up gA/gB/gA_pd/gB_pd (`nodcn` pads). The 72-cell matrix with the ECO RTL: not run | **eco4 regression: passed, 15/15 done except the CDL run (invalid, truncated log) superseded by `r3full`**; `b_s` soft trip `GATE` < 1 V 28.040 µs after the event (baseline 27.65 µs): `c_mid` `GATE` < 1 V 1.4393–1.4411 µs over the three corners, `c`/`e20` 1.4400 µs, `q` and `hard_pulse` no trip, `f_mid` re-arms, gB/gB_pd `GATE` ≤ 0.076/0.009 V with EN low, gA/gA_pd 3.3 V for 4.3 µs (IO-pad property), no trip before any event or at EN rise; +106 ns against pre-ECO is one `osc_clk` of sampling phase (RESULTS §10). Earlier: `eco_c_mid_m03` hard trip, `tripped` 1.166 µs, `GATE` < 1 V 1.451 µs, < 0.33 V 1.767 µs; `eco_hard_pulse_m03` 200 ns 45 mV pulse, no trip (simulated; `../blocks/g1_ctrl/ECO_20260925.md`, `../blocks/g1_top/sim/results_top.txt`). The earlier `eco_c_mid` with FAST_EN = 1 found a false trip at EN rise and is superseded |
| Block DRC / LVS | Assembled macro versions | passed recorded checks; experimental ELT excluded |
| Block PEX | Existing capacitance extraction and selected tests | passed subsets; full wire-R, fill coupling and statistical scaling not established |
| Assembled DRC / precheck | 1414 µm chip of record (r3) | main, maximal and `--precheck_drc` passed, 0 markers (r2 likewise). 1350 µm assembly: passed (superseded) |
| Density | 1414 µm chip of record (r3) | passed, 0 markers; global GatPoly 15.03 % after the r3 fill regeneration |
| Recommended pad rules | 1414 µm chip of record | passed inside the maximal run (`Pad.*R`, `Pad.d`: 0 errors, `drc_maximal/run.log`). 1350 µm assembly failed (superseded) |
| Antenna | 1414 µm chip of record (r3) | passed, 0 markers. 1350 µm assembly failed (superseded) |
| Projected-reference LVS | 1414 µm chip (r3), full chip, strict ports | passed: 62 940/62 940 devices, 31 816 nets, 22 pins; comparison-only reference `g1_chip_top_1414_r3_projected_ref.cdl` (3 all-VDD pad dummy PMOS removed). r2: 61 684 devices, passed. 1350 µm core-only LVS (52 pairs): passed (superseded) |
| Canonical (unprojected) LVS | 1414 µm chip (r3, `g1_chip_top_1414_r3.cdl`), full chip | failed, identical per-circuit pattern to r1/r2; cause: substrate/tap/diode netlist semantics of the IO-cell reference in the PDK, reproduced with stock cells and with IHP's latest `dev` deck and library; the design-local IO copies match IHP's `dev` library on every layer (PR #1223); upstream issues #1218/#1130. 14 IO/level-shifter sub-cells NoMatch, top skipped (`../review/upstream/evidence/README.md`, `PLAN.md` R13) |
| Top-cell rename identity | `g1_chip_top_1414_src.gds` → `g1_chip_top_1414.gds` | passed: 306 cells, deep XOR empty on all 73 layers. Earlier 1350 µm streamout differences are superseded |
| r3 identity against r2 | macro swap + GatPoly fill | passed: outside the macro outline only 5/22 changed (+100 polygons, 700 µm²); macro pins 64/64 identical; stock-named cells 52, 0 differ (`signoff-1414r3-20260926/`) |
| Power-order safety | Chip netlists: core-first, EN low, with and without 10 kΩ `GATE` pull-down; IO-first | Core-first on the full-chip CDL deck with the real `EN`/`SCLK`/`SDI` input pads and `por_n` from the CDL tie-high (`cdlpwr`, `pads nodcn`, simulated): gB and gB_pd **passed** at tt/27 and ss/125 °C, gB_pd at ff/−40 °C (`GATE` ≤ 0.27 mV while EN low; 3.28–3.30 V after EN); gB ff/−40 °C **failed** numerically at 7.42 µs (`xbgr.xq784`); stock-diode pad runs **not run to completion** (stalled at 1.377 µs). Spurious-latch window: with `IOVDD` absent the `EN` pad output floats to 0.84–0.92 V (> 0.6 V 2.34–5.70 µs at tt), `por_n` releases at 2.0 µs, and the RTL and G1_GATE trip latches set spuriously and clear when `IOVDD` passes 1.1 V (5.67 µs); `GATE` never rises (`../blocks/g1_top/sim/FULLCHIP_CDL_20260925.md`). Earlier hand-wired runs, core-first passed **with an ideal `EN` copy**: `GATE` < 14 mV holds only with the `--pads nodcn` pad models (≤ 0.014 V at ss/125 °C and ff/−40 °C, with or without 10 kΩ); with the stock pad models at tt/27 °C the run without pull-down reads 72.5 mV (0.009 V with 10 kΩ); tt/27 °C with `nodcn`: not run. Block-level red-team bench (`g1_gate` + pads, no chip context): 1 of 6 runs (ff/−40 °C, stock pads) commanded the gate on before the solver stalled (`../review/redteam-20260925/ELECTRICAL_SYSTEM.md` M1). **Inhibit required** for every order (P2). IO-first on the chip netlists (`--pads nodcn`, tt/27, ss/125, ff/−40 °C) **failed** as a safety condition, as expected: `GATE` 3.28–3.30 V for 4.2–4.4 µs until `VDD` is up, with or without 10 kΩ ([RESULTS_20260925](../blocks/g1_top/sim/campaigns/RESULTS_20260925.md) §5); P1 excludes this order. IO-only drives `GATE` to 3.288 V (block power screen, simulated): board constraints in §6 |
| Digital timing | chip digital netlist `4b83f181` (r3, ECO re-hardened) + SPEF `0b626c7f`, standalone and in the routed chip signal netlist, merged chip SDC, 3 corners, nominal RC | setup/hold passed (macro slow 28.45/0.337 ns, in chip 25.70/0.337 ns): 0 setup/hold violations; in the chip context 12 analog-pad max-slew flags per corner (placeholder library values) and 98 unannotated drivers, dispositioned; macro max slew/cap/fanout passed, clock-buffer fanout ≤ 8. The pre-ECO netlist `6181b988` passed likewise (history). Corner RC and timing of the final GDS: not run |
| Full-chip PEX | 1414 µm chip | not run |
| IR drop / electromigration | 1414 µm chip | not run |
| Package / bond-wire parasitics | QFN24 | not run |
| IO-ring XOR vs stock cells | 1414 µm chip | PolyRes IO cells vs IHP `dev` cells: identical (`../review/upstream/evidence/`); rest of the ring: not run |
| ESD / latch-up, ERC | 1414 µm chip | not run |
| GLS of the chip digital netlist `4b83f181` (functional, zero-delay) | ECO system testbench | passed: 21/21 functional tests, 260 checks (`../blocks/g1_ctrl/sim/gls_eco_r3v2/`); red-team R3 fails (serial framing, out of scope). Pre-ECO `6181b988`: 13 tests / 193 checks (history) |
| Formal equivalence, ECO RTL vs chip digital netlist `4b83f181` | — | not run |
| SDF-annotated GLS | chip digital netlist `4b83f181`, SDF typ `f2a807f0` | passed functionally: 21/21 tests, 260 checks; Icarus executes no timing checks and drops part of the delay model (68 unsupported `ifnone` paths); fast/slow SDF GLS: not run |
| Digital switching noise on the shared `VDD`/`VSS` at chip level | chip netlists | not run (the digital runs as RTL through `d_cosim`; its supply current is not simulated) |
| Configuration registers | DAC codes, MODE, INRUSH, OSC_CTRL | design note: not TMR-protected; an upset persists until rewrite or EN (host read-back and rewrite, §6) |
| Trip path with the transistor-level oscillator in the loop | chip netlists | not run |
| T2F at 85 °C and at ss/ff; T2F at −40 °C | chip netlists | 85 °C, ss, ff: not run; −40 °C: not run to completion (three attempts) |
| Stock SENSE-pad 3×/4× faults | chip netlists | not run to completion (RESULTS §3a) |
| Supply extremes on `b_s`, `f_mid`, `c`, `e20` | chip netlists | not run (only `c_mid` and `q`) |
| Default 1 ms `SOFT_TIME` with the transistor-level front end | chip netlists | not run (behavioural front end only; `b_s` uses 256 cycles) |
| Hard comparator (regenpair4) post-layout delay; NF4 at ff | TRIP NF4 extraction | not run |
| Supply bounce from digital switching at the comparator strobe | chip level | not run |
| Hard threshold versus `VDD`, temperature and SEU pattern | chip level | not run (the supply matrix used only the 1.8× fault) |
| ESD (HBM/CDM) of pads and domain crossings | 1414 µm chip | not run |
| `VDD` brownout supervision | board | not run; board requirement P8 |
| `VSS`–`IOVSS` connection | 1414 µm chip | note: joined on the die only through the IO-cell substrate (`ptap1`) resistors, no metal; tie at the package (board) |
| `G_SHARED` pad | 1414 µm chip | note: bare pad on a thin-oxide gate without secondary protection; keep device-pin voltages within the rails (≤ 1.32 V on `G_SHARED` outside declared stress, ≥ −0.3 V on every device pin while powered) |
| Physical measurement / irradiation | No fabricated samples | not run |

## 6. Acceptance and calibration contract

The breaker disconnects an external switch; analog constant-current regulation
is not implemented. The soft path accumulates time above threshold minus
programmable decay, not a measurement of the integral of current squared.

Use `G1_REGISTER_MAP.md` for timer units: hard decisions every 2/fOSC;
soft accumulation every 1/fOSC; soft window = SOFT_TIME×256/fOSC;
inrush = INRUSH×512/fOSC; hold = max(1,HOLD_TIME)×8192/fOSC.
A ±20% frequency range does not imply ±20% time: an 8–12 MHz clock gives
+25%/−16.7% time relative to 10 MHz. The chip's oscillator (R0.95) at trim code 8
spans **7.61 MHz (ss/125 °C) to 12.43 MHz (ff/−40 °C)** on the chip netlists
(simulated, 2 ns step, [RESULTS_20260925](../blocks/g1_top/sim/campaigns/RESULTS_20260925.md) §6),
outside the 8–12 MHz window above. Consequence: before trimming, every timer window
(hard decision interval, soft window, inrush, hold) scales by 9.436 MHz / f, i.e.
+24 % at 7.61 MHz and −24 % at 12.43 MHz relative to the tt/27 °C clock; trim the
oscillator per sample (OSC_CNT) before relying on window values. The chip-level trip
times (1.306–1.361 µs) used the fixed 9.436 MHz ideal clock; trip time with the
corner clock: not run.
The <10 µs target cannot apply to every programmable blanking/window value,
to masked faults, or to a stopped clock. **A stopped oscillator removes all
protection, the FAST_EN path included:** both comparators are clocked by
`cmp_clk`, so without the clock no decision is made and neither the timers nor
the fast path can trip; there is no clock-loss detector.
**On the chip of record r3 (register map 1.2, `../blocks/g1_ctrl/ECO_20260925.md`,
`PLAN.md` D16)** `osc_en` is a constant 1, so no write, mis-framed write or register
upset can stop the clock; only an analog oscillator failure can, and H1 stays
required for that case. H2 and H4 are not needed on r3: the inrush window cannot
be re-opened by an `INRUSH` write, and `SOFT_TIME` is loaded atomically on the `_L`
write (`_H` first).
**On the r2 fallback (map 1.1)** the clock can also stop by a write of
`OSC_CTRL[4]=0`, an upset of that unprotected bit or a mis-framed serial write; a
serial write cannot restart it (only an EN cycle), and serial reads, resolved in the
oscillator domain, return the value of the last read before the stop (stale data)
(`../review/redteam-20260925/DIGITAL.md` M1).

Host rules (required for the bench contract; `../review/redteam-20260925/DIGITAL.md`):

| # | Rule | Reason |
| --- | --- | --- |
| H1 | Watchdog: alternate reads of `CHIP_ID` and `OSC_CNT_L`; if `CHIP_ID` is wrong or `OSC_CNT_L` stops changing, drop EN and assert the external inhibit | detects a stopped clock (M1); stale reads otherwise look valid |
| H2 | **r2 fallback (map 1.1) only; not needed on r3.** Increase `INRUSH` only with the external inhibit asserted, then wait for `STATUS.INRUSH_ACTIVE`=0 before releasing it | the inrush counter stops at the old limit, so raising `INRUSH` re-opens the mask while armed: hard path blind for up to (255−old)×512 cycles, about 13 ms (M2) |
| H3 | Follow every safety-relevant register write by a read-back, and idle ≥ 128 oscillator cycles of SCLK before each frame; keep SCLK low when idle and every SCLK-low phase inside a frame < 64 oscillator cycles | no chip select, parity or acknowledge: one SCLK glitch or stall re-frames a write onto another register (S1) |
| H4 | **r2 fallback (map 1.1) only; not needed on r3** (atomic `SOFT_TIME`). Change `SOFT_TIME` only with `MODE.SOFT_EN` cleared | no byte order is safe in both directions; the `_H`-then-`_L` order can pass through 0x0000 (trip on first sample) (S2) |
| H5 | Periodically read back and rewrite the configuration registers | they are not TMR-protected; an upset persists until rewrite or EN (S7) |

For closure screening, adopt ±10% total calibrated shunt-threshold error as an
**engineering acceptance assumption**, as suggested by the existing trip
interface. At a requested threshold T, stimuli ≤0.9T are the no-trip region,
and persistent stimuli ≥1.1T are the trip region. The region between is a
characterization band, not a promised exact decision. Evaluate soft and hard
paths separately with the other path disabled; a persistent soft-band stimulus
must trip only after its configured accumulation window. Characterize smaller
±0.1/0.25/0.5/1 mV offsets separately without falsely labeling every decision
inside this guard band a system failure.

Hard-path calibration must bracket the **effective** hard threshold, not the
DAC code. In simulation the hard comparator trips 7.9–11.0 mV of shunt (40–56
LSB) below its code, with a 10–11 LSB corner spread (TRIP NF4 block bench). On
the chip netlists at code 200 (39.25 mV) the trip point is 30.00–31.25 mV at tt/27 °C
([RESULTS_20260925](../blocks/g1_top/sim/campaigns/RESULTS_20260925.md) §4). Uncalibrated, the `c_mid` sweep trips at 0.80T and 0.89T,
inside the no-trip region above. Expect the calibrated hard code 40–56
codes above the nominal one (block bench over corners), and a usable hard range of about 25–40 mV of shunt.
The code search must extend at least 56 codes above the target. The corner
spread is larger than 2 LSB, so one room-temperature calibration does not absorb
it: verify the ±10 % guard band at each declared temperature. The soft path is
within 1 LSB. The 2× hold-capacitor candidate that would halve the offset is not
adopted (decision pending), so this contract applies to the chip of record.

GATE-low means the first downward crossing of 1.0 V that remains below 1.0 V
for the remainder of the observed tripped interval. Measure external drain
current decay and let-through energy separately. The existing fixture is a
5 nF gate with 10 Ω series resistance and a switched synthetic load. A selected
real FET model, board/package impedance and declared bus/load are required
before claiming real-load safety. Separate CSD16340Q3 model tests use explicitly
assumed 5/12 V loads; no board BOM or operating bus was selected. Selected
nominal cases complete, but the timestep-refinement ladder fails numerically
at 250 ps and does not establish convergence. The existing nominal shunt fixture is 25 mΩ at 1 A (25 mV); fault
profiles reach 3 A or 4 A (75/100 mV, above the specified 50 mV input range;
these are fault-stress fixtures, not in-range accuracy tests). The `c_mid`
fixture programs hard code 200 and applies 1.8 A/45 mV, above its 10% trip
guard band while remaining in-range. The behavioral current source has no declared
load-bus voltage. Shunt tolerance
and temperature coefficient are idealized unless explicitly swept. No physical
shunt tolerance allocation has yet been verified.

Power-up requirements (board constraints decided 2026-09-24):

| # | Requirement | Reason | Evidence / status |
| --- | --- | --- | --- |
| P1 | `VDD` (1.2 V) comes up before or together with `IOVDD` (3.3 V); during shutdown `VDD` stays until `IOVDD` is down | Every `sg13g2_io` output pad, the tri-state variants included, takes its driver gate signals from core-powered level-up cells. With `IOVDD` alone the `GATE` pad can float high | IO-only: `GATE` 3.288 V (simulated, `../blocks/g1_gate/sim/POWER_SCREEN_20260921.md`). Core-first on the chip netlists: `GATE` ≤ 0.073 V with EN low (simulated, `g1_top` gB, **ideal `EN` copy**). Core-first with pad models: `EN` reads enabled and the `GATE` latch state is undefined until `IOVDD` > 1.1 V; inhibit required (`ELECTRICAL_SYSTEM.md` M1). IO-first on the chip netlists: `GATE` 3.28–3.30 V for 4.2–4.4 µs until `VDD` is up, at three corners (simulated, `--pads nodcn`, [RESULTS_20260925](../blocks/g1_top/sim/campaigns/RESULTS_20260925.md) §5) |
| P2 | **Independent load-bus inhibit during every power-up, whatever the order** (a `GATE` pull-down may be added but does not replace it); ramp `IOVDD`/`VDDA` fast (target < 100 µs) | Holds the FET off while the rails ramp. With IO first, a 10 kΩ pull-down does not. With core first, the `EN` pad's core output floats and reads enabled until `IOVDD` ≈ 1.1 V, `por_n` is tied high and the `GATE` latch state at power-up is undefined (corrected 2026-09-25, `../review/redteam-20260925/ELECTRICAL_SYSTEM.md` M1) | Core-first with 10 kΩ: `GATE` ≤ 0.009 V (simulated, `g1_top` gB_pd). IO-first with 10 kΩ: `GATE` 3.28–3.30 V for 4.2–4.4 µs (simulated, `gA_pd`). A pull-down strong enough to hold `GATE` against the 30 mA pad drive was not qualified |
| P3 | `VDDA` (pin 7) tied to the `IOVDD` rail | Analog-pad ESD diodes reference `IOVDD`; `VDDA` above `IOVDD` by a diode drop forward-biases them (D14) | specified |
| P4 | `EN` held low ≥ 2 ms after both rails are stable when 10 nF is on the `VREF` pin | EN low resets the digital state and holds `GATE` off. BGR586 output resistance 19.3–25.8 kΩ over corners (22.3 kΩ at tt/27 °C), so 10 nF gives τ ≈ 0.2–0.27 ms | Simulated 1 % settling from ramp start with 10 nF: 1.26 ms (tt/27 °C), 1.20 ms (ff/−40 °C), 1.32 ms (ss/125 °C, pad-less stand-in; the stock pad did not converge) (`../blocks/g1_bgr/sim/system_checks_20260924/RESULTS.md`) |
| P5 | Scale the P4 delay with the `VREF` pin capacitance | Settling scales with Rout·C. More capacitance filters probe and board noise on the test pin but lengthens the delay | 0 nF: about 7–8 µs, with a 1.3–1.7 % overshoot during the ramp (mixes the stock-pad ff/−40 °C value 7.0 µs with pad-less stand-in values; the stock pad did not converge at tt/27 °C); 100 nF: 11.8–13.2 ms to 1 % (11.84–11.96 ms at ff/−40 °C) (simulated, `../blocks/g1_bgr/sim/system_checks_20260924/RESULTS.md`). Other values: not run |
| P6 | `EN` low at power-up, until P4 is met | EN is the only reset: no on-chip reset other than EN (`por_n` tied high) and no pull-down on the EN pad. **Chip of record r3 (map 1.2):** the oscillator always runs; with EN low the core is reset at once or, in the worst power-up state of the unreset flop `en_seen`, within 11 `osc_clk` edges of oscillator start (≤ 1.45 µs at 7.6 MHz); a reset needs 8 consecutive EN-low samples (EN deglitch); digital outputs are undefined until then, while `gate_core` = `en_core` & !tripped is held 0 by the EN pad directly and the external inhibit (P2) covers power-up. **r2 fallback (map 1.1):** with EN high at power-up the configuration (including `OSC_CTRL.OSC_EN`) is random. Both: with the `EN` pin low, the `EN` pad output floats to 0.84–0.92 V while `IOVDD` is absent, so with core first the trip latches set spuriously until `IOVDD` passes about 1.1 V; `GATE` stayed ≤ 0.27 mV in the chip-level real-pad runs, which used the **pre-ECO (map 1.1) RTL** (`../blocks/g1_top/sim/FULLCHIP_CDL_20260925.md`, simulated), hence P2 | required (board). Map 1.2: RTL E6/R1 (`en_seen` 0/1/X, `gate_core` model never 1); chip-level power-up with the frozen r3 RTL: run (gA/gB/gA_pd/gB_pd, `nodcn` pads, ideal `EN` copy; `eco4`, RESULTS §10): gB/gB_pd `GATE` ≤ 0.076/0.009 V while EN low. Real-pad (CDL) power-up with the frozen RTL: not run. Map 1.1: RTL and chip digital netlist (`../review/redteam-20260925/DIGITAL.md` S5), chip-level CDL runs `cdlpwr` |
| P7 | Every EN rise (and every retry) re-opens the inrush window (INRUSH×512 cycles) with all register defaults restored; the digital paths are masked during it. r2 fallback (map 1.1): default 0x14, about 1 ms, with `FAST_EN`=0, so the hard path is blind for about 1 ms. **Chip of record r3 (map 1.2**, ECO, owner decision 2026-09-25): default 0x02, 1024 cycles, about 0.11 ms at 9.4 MHz, `FAST_EN`=0 (host-selectable; `FAST_EN`=1 as default was evaluated: fast-path trip 0.21 µs, `GATE` < 1 V 0.50 µs, but single-strobe sensitivity to 200 ns pulses, so rejected) | **accepted design behaviour covered by the external inhibit, pending owner confirmation**. r2 fallback: without a host, a short at EN rise conducts for about 1 ms, limited by the FET and the bus (`DIGITAL.md` M3). r3 (map 1.2): the hard path is blind for about 0.11 ms instead of 1 ms; a host that needs a longer blanked start writes a larger `INRUSH` after EN rise, under the inhibit | 1.1: by specification, T05 tests it. 1.2: E7 in `../blocks/g1_ctrl/sim/eco_20260925/tb_g1_digital_eco.v` (RTL, simulated); chip level: see `ECO_20260925.md` |
| P8 | External pull-downs (for example 100 kΩ, at the package) on `EN`, `SCLK` and `SDI`; drive `EN` from a low-impedance CMOS or Schmitt buffer with a fast, clean edge, never a slow RC timer; keep `EN` routing away from `FAULT_N`/`GATE`; a `VDD` supervisor asserts the load-bus inhibit on `VDD` undervoltage | The input pads have no pull and no hysteresis: floating `SCLK`/`SDI` can complete register writes (e.g. stop the clock, disable both paths) and a floating `EN` gives a random enable. On r3 (map 1.2) the digital reset needs 8 consecutive EN-low samples (about 0.8 µs; reset within 11 `osc_clk` edges), so a short glitch no longer resets the configuration or clears a latched digital trip, but the analog `en_core` path still turns `GATE` off for the glitch and clears the G1_GATE latch. On the r2 fallback (map 1.1) `EN` is an unfiltered asynchronous reset: a few-ns low glitch clears a latched trip, resets every register and re-opens the 1 ms inrush mask. A `VDD` brownout with `IOVDD` present reproduces the IO-first unsafe state | required (board); `ELECTRICAL_SYSTEM.md` M4, M5, S6 |
| P9 | Kelvin-integrity check before arming and after every `EN` cycle: with load current flowing and `DAC_SOFT` at a low code, `STATUS2.CMP_SOFT` must read 1 | Open-lead behaviour is asymmetric: `SENSE_N` open gives `ISENSE` ≈ 0.05–0.29 V and the breaker is blind, silently; `SENSE_P` open trips permanently (and overstresses `icmp`, §4) (simulated, `ELECTRICAL_SYSTEM.md` M3) | required (bench/firmware) |

Simultaneous ramps, missing rails, brownout and shutdown are not qualified by
these cases. “Core before or with IO” is a board requirement, not a general
safety guarantee.

For calibration, keep the load bus isolated by an independent external inhibit,
then raise EN, allow synchronous reset release, and program/read back the
configuration. EN low resets serial/register state and cannot preserve custom
configuration while holding the gate off. Keep the external inhibit asserted
through calibration; reassert it before any EN cycle and reprogram afterward.
The bench sequence and its unrun hardware checks are in
`../measurement/README.md`.

With automatic load arming externally inhibited, inject a
known interior shunt voltage (nominally 25 mV), use zero SENSE_OFS and disable
hysteresis. Sweep each threshold independently after settling and locate a
bracketed crossing Ccross. Under the nominal mapping Cideal=Vin/LSB, the shared
correction is **Ccross−Cideal**, rounded to a representable integer. A positive
input-path offset needs a positive correction, because the RTL adds SENSE_OFS
to the DAC code. The old instruction to negate a zero-input crossing had the
wrong sign under this convention and cannot bracket negative offsets at code 0.
The 25 mV fixture demonstrates policy arithmetic; analog calibration yield
requires the joint loaded-chain simulations and measurements.

A nominal threshold C can accept correction O only if 0≤C+O≤255. For the reset
hard code 254 the positive allowance is +1 (~0.196 mV). A sample needing +20
must use C≤235 (~46.1 mV), or be rejected for the intended threshold. Independent
threshold programming may compensate comparator differences; it cannot extend
the DAC range. One offset cannot independently correct gain, both comparators,
and temperature drift. Freeze each sample's calibration at room temperature,
then evaluate residual <0.5 mV and threshold error at temperature/common-mode
and supply endpoints. Recalibration at each test point is not acceptance.

For valid feedback-loop measurements, phase margin ≥60° and gain margin ≥10 dB
are proposed screening limits. They do not replace a valid loop-injection model
or establish stability from transient appearance alone.

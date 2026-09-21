# G1 Radiation-Aware Node Guardian — Top-Level Specification & Architecture Record

## 1. Overview and intent

G1 is a mixed-signal test chip on the IHP SG13G2 0.13 µm SiGe BiCMOS open PDK.
It sits between a power rail and a commercial compute load and does four things:
limits and cuts the load current on a latch-up signature while letting ordinary
load steps through; measures its own temperature with an HBT-based sensor;
tracks accumulated ionizing dose with a transistor-leakage canary; and counts
upsets in a scrubbed register. Telemetry and settings go over a three-wire
serial interface.

Design principles:

- **HBTs where their physics matters:** the sense-amplifier input pair, the
  bandgap and the temperature sensor use `npn13G2`, for offset, ideality and
  wide-temperature behaviour. Digital and switching functions use CMOS.
- **Board-measurable:** every signal is DC or below 10 MHz. The die is packaged
  in QFN24 and measured in a socket. No RF pads.
- **Two canaries, two mechanisms:** dose is observed through NMOS STI-edge
  leakage (standard versus enclosed layout) and through HBT base current at
  low V<sub>BE</sub>. They fail differently, which is the point.
- **Direct device access:** one HBT and the canary transistors are pinned out
  so the physics can be measured without the on-chip readout.
- **Area:** 1.35 × 1.35 mm die including sealring and IO ring. The 1 × 1 mm allocation was withdrawn on 2026-09-18 because the IO cells need an external bondpad and sealring clearance (`PLAN.md` D10); 1.2 mm was withdrawn on 2026-09-19 when the laid-out macros exceeded its core window (D13).

## 2. Block breakdown

| Block | Function | Devices | Interfaces |
| --- | --- | --- | --- |
| `G1_SENSE` | Low-side Kelvin shunt amplifier. Differential input 0 to 50 mV across an external shunt, gain 20, bandwidth ≥ 2 MHz, input-referred offset target < 0.5 mV after trim. Common-mode −0.1 to +0.3 V. Difference amplifier around a 3.3 V PMOS-input OTA with a V<sub>REF</sub>-derived output pedestal (`PLAN.md` D1). | thick-oxide PMOS input pair, thick-oxide MOS, `rppd` | in: `SENSE_P`, `SENSE_N`; out: internal `ISENSE` (pedestal + 20 × V<sub>shunt</sub>) |
| `G1_TRIP` | Two clocked comparators on `ISENSE`: (a) hard threshold, trips after N consecutive samples above it (blanking); (b) soft threshold, trips when an up/down sample counter reaches the programmed trip-off window (`PLAN.md` D3). Thresholds are 8-bit codes of V<sub>REF</sub>-referenced resistor-string DACs; hysteresis and all windows programmable. | 1.2 V StrongARM comparators with SR latches, two 8-bit `rppd` string DACs, digital timers in `G1_CTRL` | in: `ISENSE`, `TRIP_SET`, registers; out: `cmp_soft`, `cmp_hard` to `G1_CTRL` |
| `G1_GATE` | Drives an external low-side logic-level N-FET. On `TRIP`: gate low within the response target, then latched off or retriggered after a programmable hold. Enable input. | `sg13g2_IOPadOut30mA`, LV/HV level shift | out: `GATE`, `FAULT_N`; in: `EN` |
| `G1_BGR` | First-order op-amp-less cascoded HBT bandgap in the 3.3 V domain, 1:8 emitter units. V<sub>REF</sub> nominal 1.04 V (simulated, untrimmed), TC 11 to 52 ppm/°C over −40 to 125 °C across corners; I<sub>PTAT</sub> 4.1 µA at 27 °C for the sensor and DACs; 1:4 ratio test mode. | `npn13G2`, thick-oxide MOS, `rppd`, `rhigh` | out: `VREF`, internal `IPTAT`, `VBE`, `dVBE` |
| `G1_T2F` | HBTs at a 1:8 current ratio; ΔV<sub>BE</sub> converted to a PTAT current that charges a `cmim` relaxation oscillator against a V<sub>REF</sub>-derived threshold, so frequency is linear in T (`PLAN.md` D2); register-selectable reference mode runs the same oscillator from V<sub>REF</sub>/R so the ratio cancels C and thresholds. About 1.6 MHz at 27 °C (simulated). | `npn13G2`, thick-oxide MOS, `rppd`, `cmim`, LV CMOS output | out: `TEMP_OUT`; mode bits from registers |
| `G1_DOSE` | Two NMOS canaries with a shared gate and both drains pinned out: default a thin-oxide `sg13_lv_nmos` beside a thick-oxide `sg13_hv_nmos` (the dose-sensitive device on this process); alternative, gated on foundry acceptance of a bent gate, a drawn enclosed-layout NMOS in place of the HV device (`PLAN.md` D11). No on-chip readout in run 1. | `sg13_lv_nmos`, `sg13_hv_nmos`, optional drawn ELT | pins: `G_SHARED`, `D_STD`, `D_ELT` |
| `G1_SEU` | Plain shift register and per-stage-voted TMR register (depth parameterised, 256 + 3 × 128 bits hardened on day 1, final depth fixed at floorplan per `PLAN.md` D12), continuously shifted and scrubbed against a selectable pattern (checkerboard, all-0, all-1; constant patterns give the static-data case); TMR-protected counters for plain errors, TMR corrected events and TMR uncorrectable errors. | LV CMOS standard cells | registers |
| `G1_CTRL` | Register file, three-wire serial (mode-0 SPI-like, 7-bit address + R/W bit, 8-bit data, 24-clock read frame), trip timers, scrub state machine, event counters; full map in `G1_REGISTER_MAP.md`. | LV CMOS standard cells | `SCLK`, `SDI`, `SDO` |
| `G1_DUT` | One `npn13G2` HBT, all three terminals on analog pads, substrate to `VSS`. | `npn13G2` | `HBT_E`, `HBT_B`, `HBT_C` |

## 3. Pin map (24)

| # | Pin | IO cell | Domain | Function |
| ---: | --- | --- | --- | --- |
| 1 | `VDD` | `sg13g2_IOPadVdd` | 1.2 V | core supply |
| 2 | `VSS` | `sg13g2_IOPadVss` | 0 V | core ground, substrate |
| 3 | `IOVDD` | `sg13g2_IOPadIOVdd` | 3.3 V | IO and analog supply |
| 4 | `IOVSS` | `sg13g2_IOPadIOVss` | 0 V | IO ground |
| 5 | `VSS` | `sg13g2_IOPadVss` | 0 V | second ground pad |
| 6 | `IOVSS` | `sg13g2_IOPadIOVss` | 0 V | second IO ground pad |
| 7 | `VDDA` | `sg13g2_IOPadAnalog` (bare terminal) | 3.3 V | analog supply for the 3.3 V core blocks (bandgap, sensor, sense amplifier, comparator DACs, gate latch, oscillator); tied to the same 3.3 V rail as `IOVDD` on the board (`PLAN.md` D14) |
| 8 | `SENSE_P` | `sg13g2_IOPadAnalog` | analog | shunt Kelvin, positive |
| 9 | `SENSE_N` | `sg13g2_IOPadAnalog` | analog | shunt Kelvin, negative |
| 10 | `GATE` | `sg13g2_IOPadOut30mA` | 3.3 V | external N-FET gate |
| 11 | `FAULT_N` | `sg13g2_IOPadOut4mA` | 3.3 V | low while tripped |
| 12 | `EN` | `sg13g2_IOPadIn` | 3.3 V | enable / reset of trip latch |
| 13 | `TRIP_SET` | `sg13g2_IOPadAnalog` | analog | external hard-threshold override, optional |
| 14 | `SCLK` | `sg13g2_IOPadIn` | 3.3 V | serial clock |
| 15 | `SDI` | `sg13g2_IOPadIn` | 3.3 V | serial data in |
| 16 | `SDO` | `sg13g2_IOPadOut4mA` | 3.3 V | serial data out |
| 17 | `TEMP_OUT` | `sg13g2_IOPadOut16mA` | 3.3 V | temperature as frequency |
| 18 | `VREF` | `sg13g2_IOPadAnalog` | analog | bandgap output, for test |
| 19 | `G_SHARED` | `sg13g2_IOPadAnalog` | analog | canary pair gate |
| 20 | `D_STD` | `sg13g2_IOPadAnalog` | analog | standard NMOS drain |
| 21 | `D_ELT` | `sg13g2_IOPadAnalog` | analog | second canary drain: thick-oxide NMOS by default, enclosed-layout NMOS if approved (D11) |
| 22 | `HBT_E` | `sg13g2_IOPadAnalog` | analog | test HBT emitter |
| 23 | `HBT_B` | `sg13g2_IOPadAnalog` | analog | test HBT base |
| 24 | `HBT_C` | `sg13g2_IOPadAnalog` | analog | test HBT collector |

Side assignment: pins 1 to 6 south, 7 to 12 east, 13 to 18 north, 19 to 24
west, so that the analog device pins sit together on one side away from the
switching outputs, and the supplies are split between two sides.

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
| Analog supply | 3.3 V (3.0 to 3.6) on `VDDA`, about 1.5 mA (simulated sum of the 3.3 V blocks) | Specified | block READMEs; D14 |
| IO / analog supply | 3.3 V (3.0 to 3.6) | Specified | `sg13g2_io` |
| Die | 1350 × 1350 µm incl. sealring | Specified | macro area budget, `PLAN.md` D13; QFN24 accepts up to 2 × 2 mm |
| Package | QFN24, 4 × 4 mm, 0.5 mm pitch, 200 µm die | Specified | packaging offer |
| Shunt sense range | 0 to 50 mV differential, low-side; `ISENSE` = 1.0 V pedestal + 20 × V<sub>shunt</sub>, i.e. 1.0 to 2.0 V | Specified | `blocks/g1_sense/README.md` (simulated gain 19.98 to 19.99, bandwidth 3.6 to 4.8 MHz) |
| Trip response | < 10 µs from overcurrent to `GATE` low; simulated chain: sense settling ≤ 164 ns, comparator ≤ 1.3 ns, hard-path blanking N × 100 ns, gate fall into 5 nF 0.42 to 0.61 µs | Specified (schematic level) | `blocks/g1_trip`, `blocks/g1_gate` READMEs; post-layout not run |
| I²t window | 50 µs to 10 ms, programmable | Assumed | design target |
| Hard threshold | 8-bit DAC code, 0.5 to 1.0 of the sense full scale (about 25 to 50 mV of shunt drop), programmable; nominal load current is mapped to 20 to 25 mV of the 50 mV range | Specified | `blocks/g1_trip/INTERFACE.md`; the earlier "1.5× to 8× nominal" was unreachable |
| `TEMP_OUT` frequency | 1.59 MHz at 25 °C (simulated, PTAT mode), 5.2 kHz/°C; 1.2 to 2.4 MHz over −40 to 175 °C; ±15 % process spread before calibration | Specified (simulated) | `blocks/g1_t2f/README.md` |
| Sensor accuracy | ±2 °C after two-point calibration, −40 to 125 °C; simulated post-layout residual −0.85 to +0.17 °C over −40 to 150 °C in PTAT mode (the frequency-ratio mode is less linear, +4.9 °C at 175 °C, and is a diagnostic, not the calibrated reading) | Specified (simulated) | `blocks/g1_t2f/README.md`; mismatch and package stress not simulated |
| Characterisation range | 77 K to 175 °C | Assumed | package limits, not verified |
| Sense-amp input offset | σ = 4.0 mV shunt-referred before trim (200-sample MC, simulated); trimmed digitally by an 8-bit signed code offset on both DAC codes, LSB 0.196 mV, range ±24.9 mV, residual ≤ 0.1 mV | Specified | `blocks/g1_sense/README.md` |
| ELT NMOS extraction | recognised as `sg13_lv_nmos`, W 3.98 µm, L 0.50 µm (simulated LVS); DRC fails `Gat.f` | Specified | `blocks/g1_dose/README.md` |
| Total power | < 10 mW | Unknown | to be simulated |

## 5. Verification gates

| Gate | Scope | Status |
| --- | --- | --- |
| Schematic simulation per block, nominal | all blocks | not run |
| Corner and Monte Carlo | `G1_SENSE`, `G1_BGR`, `G1_T2F` | not run |
| Temperature sweep −196 to 175 °C in the model | `G1_BGR`, `G1_T2F`, `G1_DUT` | not run |
| RTL simulation | `G1_TRIP` timer, `G1_SEU`, `G1_CTRL` | not run |
| AMS co-simulation of breaker path with load model | `G1_TOP` | not run |
| DRC per block | all | not run |
| LVS per block | all | not run |
| PEX and post-layout simulation | `G1_SENSE`, `G1_TRIP`, `G1_T2F`, `G1_BGR` | not run |
| Full-chip DRC incl. precheck rules | `G1_TOP` | not run |
| Density and fill | `G1_TOP` | not run |
| Antenna | `G1_TOP` | not run |
| Full-chip LVS against final netlist | `G1_TOP` | not run |

## 6. Settlement plan for unknowns

1. Run the HBT model over temperature and fix the ΔV<sub>BE</sub> ratio and
   readout topology for `G1_T2F`. This decides the sensor's frequency range.
2. Monte Carlo the `G1_SENSE` input pair; decide trim range and bits.
3. Simulate the breaker path against a synthetic load-step library; fix the
   default I²t profile and the hard-threshold range.
4. Draw the ELT NMOS, run DRC, and write the extraction rule; confirm the
   drawn geometry is acceptable for the shuttle (assumed, confirmation pending).
5. Assemble the ring in LibreLane, place the macros, close DRC and density.

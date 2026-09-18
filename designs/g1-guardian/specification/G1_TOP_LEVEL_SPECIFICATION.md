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
- **Area:** 1 × 1 mm die including sealring and IO ring.

## 2. Block breakdown

| Block | Function | Devices | Interfaces |
| --- | --- | --- | --- |
| `G1_SENSE` | Low-side Kelvin shunt amplifier. Differential input 0 to 50 mV across an external shunt, gain 20, bandwidth ≥ 2 MHz, input-referred offset target < 0.5 mV after trim. Common-mode −0.1 to +0.3 V. | `npn13G2` input pair, thick-oxide MOS, `rppd` | in: `SENSE_P`, `SENSE_N`; out: internal `ISENSE` (0 to 1 V) |
| `G1_TRIP` | Two paths on `ISENSE`: (a) fast comparator at a programmable hard threshold, (b) I²t integrator against a programmable energy limit and window. Either asserts `TRIP`. Hysteresis and blanking programmable. | LV CMOS comparator, 8-bit DACs for thresholds, digital integrator | in: `ISENSE`, `TRIP_SET`, registers; out: `TRIP` |
| `G1_GATE` | Drives an external low-side logic-level N-FET. On `TRIP`: gate low within the response target, then latched off or retriggered after a programmable hold. Enable input. | `sg13g2_IOPadOut30mA`, LV/HV level shift | out: `GATE`, `FAULT_N`; in: `EN` |
| `G1_BGR` | Bandgap in the 3.3 V domain. V<sub>REF</sub> nominal 1.2 V class, PTAT current output for the sensor and DACs. | `npn13G2`, thick-oxide MOS, `rppd` | out: `VREF`, internal `IPTAT` |
| `G1_T2F` | Two HBTs at a fixed current ratio; ΔV<sub>BE</sub> converted to a current that sets a ring-oscillator frequency. Output frequency in the 1 to 10 MHz range at room temperature. | `npn13G2`, LV CMOS | out: `TEMP_OUT` |
| `G1_DOSE` | One standard `sg13_lv_nmos` and one drawn enclosed-layout NMOS of equal W/L, shared gate. On-chip readout mirrors both off-currents into a log-ratio detector; both drains also pinned out. | `sg13_lv_nmos`, drawn ELT | pins: `G_SHARED`, `D_STD`, `D_ELT`; registers |
| `G1_SEU` | 1024-bit shift register in two flavours, plain and TMR-voted, continuously scrubbed against a known pattern; upset counter per flavour. | LV CMOS standard cells | registers |
| `G1_CTRL` | Register file, three-wire serial (mode-0 SPI-like, 8-bit address, 8-bit data), scrub state machine, trip state machine, event counters. | LV CMOS standard cells | `SCLK`, `SDI`, `SDO` |
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
| 7 | `VDD` | `sg13g2_IOPadVdd` | 1.2 V | second core supply pad |
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
| 21 | `D_ELT` | `sg13g2_IOPadAnalog` | analog | enclosed-layout NMOS drain |
| 22 | `HBT_E` | `sg13g2_IOPadAnalog` | analog | test HBT emitter |
| 23 | `HBT_B` | `sg13g2_IOPadAnalog` | analog | test HBT base |
| 24 | `HBT_C` | `sg13g2_IOPadAnalog` | analog | test HBT collector |

Side assignment: pins 1 to 6 south, 7 to 12 east, 13 to 18 north, 19 to 24
west, so that the analog device pins sit together on one side away from the
switching outputs, and the supplies are split between two sides.

Analog pads carry the IO cell's ESD diodes to `IOVDD`/`IOVSS`. Their leakage
bounds the lowest usable current on the device pins; the measurement plan keeps
device currents in the nanoampere-to-microampere range for that reason.

## 4. Parameter classification

| Parameter | Value / range | Status | Basis |
| --- | --- | :---: | --- |
| Process | IHP SG13G2 0.13 µm SiGe BiCMOS, open PDK | Specified | PDK |
| HBT primitive | `npn13G2` | Specified | PDK model library |
| Core supply | 1.2 V (1.08 to 1.32) | Specified | PDK |
| IO / analog supply | 3.3 V (3.0 to 3.6) | Specified | `sg13g2_io` |
| Die | 1000 × 1000 µm incl. sealring | Specified | allocation |
| Package | QFN24, 4 × 4 mm, 0.5 mm pitch, 200 µm die | Specified | packaging offer |
| Shunt sense range | 0 to 50 mV differential, low-side | Assumed | design choice; sets amplifier gain and shunt value |
| Trip response | < 10 µs from overcurrent to `GATE` low | Assumed | design target; to be set by simulation |
| I²t window | 50 µs to 10 ms, programmable | Assumed | design target |
| Hard threshold | 1.5× to 8× nominal, programmable | Assumed | design target |
| `TEMP_OUT` frequency | 1 to 10 MHz at 25 °C | Assumed | ring-oscillator readout range |
| Sensor accuracy | ±2 °C after two-point calibration, −40 to 125 °C | Assumed | target; ΔV<sub>BE</sub> law and readout nonlinearity to be simulated |
| Characterisation range | 77 K to 175 °C | Assumed | package limits, not verified |
| Sense-amp input offset | < 0.5 mV after trim | Unknown | Monte Carlo not run |
| ELT NMOS extraction | recognised as MOS with documented W/L | Unknown | extraction rule to be written and checked |
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

# R1 Open Joint Front-End — Top-Level Specification (draft 0.1, 2026-10-20)

Status: draft. No block has been simulated, laid out or checked. Every number below is labelled
specified (a target), estimated (from a study, no run), assumed, or unknown. The studies behind the
numbers are in [`studies/`](studies/). Decisions D1–D9 are in [`../PLAN.md`](../PLAN.md) §2a.

## 1. Overview and intent

R1 is a mixed-signal chip for one robot joint on the IHP SG13G2 0.13 µm SiGe BiCMOS open PDK. It
reads a sine/cosine encoder head, computes a calibrated absolute angle within one electrical period
and a turn count while powered, measures two phase currents on low-side shunts and the die
temperature, runs a hardware safety channel that can cut the gate drive independently of the motor
controller, passes three PWM signals through to external low-side FETs with dead time, and reports
over BiSS-C, SSI or SPI. Die 1.414 × 1.414 mm (2 mm² budget, fallback 1.5 mm per D9), 24-pad
`sg13g2_io` ring, QFN24.

The design goal is a complete, open, verifiable joint front-end, not a product. Blocks are chosen so
that the design exercises analog, mixed-signal, digital, system, sensor-interface and actuator-drive
work in one chip.

## 2. Block breakdown

| Block | Function | Devices | Interfaces | Origin |
| --- | --- | --- | --- | --- |
| `r1_afe` | Differential sine and cosine inputs, resistive-input PGA ×1–×32 on 3.3 V devices, output at 0.6 V common mode in the 1.2 V domain, matched anti-alias filters (f_c ≥ 1 MHz, poles matched to 1 %) | thick-oxide MOS, `rppd`, MIM | in: SIN±, COS±; out: 2 differential signals to the track-and-holds | new |
| `r1_adc` | Two track-and-holds sampled on one edge (skew < 0.5 ns) feeding one 12-bit SAR at ≥ 2 MSPS (ENOB ≥ 11.5), split 6+6 bridge MIM CDAC, bootstrapped switches, reference buffer; a multiplexer adds the two current channels between encoder conversions (D3). Alternate: two SARs at 1 MSPS if area allows | thin-oxide MOS, MIM | out: 12-bit codes, valid strobes | new; starts from IHP-AnalogAcademy module 3 |
| `r1_pos` | Offset, gain-ratio, phase and 3rd-harmonic correction (Heydemann form), iterative CORDIC (16-bit angle, 18 iterations, ≥ 25 MHz), type-II tracking loop (velocity, filtering), latch at bus request with velocity extrapolation, turn counter, amplitude monitor | std cells | registers, position bus | new (digital) |
| `r1_bus` | BiSS-C slave (Rev D2: ACK, START, CDS, data, nE/nW, CRC-6 0x43 inverted, static timeout, control channel with read-only IDs at 0x40–0x7F), SSI slave (Gray/binary, monoflop), SPI register access (mode 0, with an AS5047P-compatible 16-bit angle read frame as an option) | std cells, IO pads | MA/SCLK, SLO/SDO, SDI, CS | new (digital) |
| `r1_isense` | Two compact low-side shunt sense amplifiers with auto-zero, ≤ 100 mV input, settling < 300 ns after the PWM edge (target) | thick-oxide MOS, `rppd` | in: ISA±, ISB±; out: to ADC mux and comparators | G1 `g1_sense` lineage, re-sized (D5) |
| `r1_safe` | Two window comparators per channel (overcurrent, phase short), I²t winding model with a programmable thermal time constant, over-temperature from `r1_t2f`, amplitude-loss and overspeed from `r1_pos`, watchdog on the bus, `EN`/`STO_IN` input; any fault latches `FAULT_N` low and forces the three gate outputs low until cleared | thick-oxide MOS, std cells | FAULT_N, EN/STO_IN | G1 `g1_trip` lineage |
| `r1_gate` | PWM counter and three low-side gate outputs generated from a host-written duty/phase word (D4), programmable dead time, centre-of-on-time sample strobes for the current channels; safety-gated | `sg13g2_IOPadOut30mA` | GATE_A/B/C | G1 `g1_gate` × 3 |
| `r1_bgr` | Compact SiGe bandgap, V_REF ≈ 1.05 V, with a PTAT branch | `npn13G2`, thick-oxide MOS, `rppd` | internal | G1 lineage, re-sized (D5) |
| `r1_t2f` | Temperature-to-frequency, counted on chip | `npn13G2` | internal count register | G1 `g1_t2f` |
| `r1_osc` | RC relaxation oscillator, 30 MHz nominal, 5-bit capacitor trim; the BiSS timeout, SSI monoflop and watchdog count from it; `OSC_COUNT` over 16 MA periods lets the host trim it and detect a clock fault | thin-oxide MOS, MIM, `rppd` | internal; registers `OSC_TRIM`, `OSC_COUNT`, `TIMEOUT_TICKS` | G1 `g1_osc` lineage, re-tuned (S5) |
| `r1_padring` | 24 `sg13g2_io` pads, 6 per side, corner and filler cells, bondpads | PDK IO library | — | G1 `g1_padring` |

Not in R1 (parked, see `PLAN.md` cut list and D1–D8): second encoder track (nonius), ABZ output,
PWM pattern generator, TEMP_OUT pin.

## 3. Pin map (24)

| Die pad | Pin | IO cell | Domain | Function |
| --- | --- | --- | --- | --- |
| 1 | `VDD` | `sg13g2_IOPadVdd` | 1.2 V | core supply |
| 2 | `VSS` | `sg13g2_IOPadVss` | 0 V | core ground |
| 3 | `IOVDD` | `sg13g2_IOPadIOVdd` | 3.3 V | IO supply |
| 4 | `IOVSS` | `sg13g2_IOPadIOVss` | 0 V | IO ground |
| 5 | `VSS` | `sg13g2_IOPadVss` | 0 V | second core ground |
| 6 | `IOVSS` | `sg13g2_IOPadIOVss` | 0 V | second IO ground |
| 7 | `VDDA` | `sg13g2_IOPadAnalog` bare terminal | 3.3 V | analog supply (G1 D14 rule: tied to the IOVDD rail on the board) |
| 8 | `ISA_P` | `sg13g2_IOPadAnalog` | analog | shunt A Kelvin positive |
| 9 | `ISA_N` | `sg13g2_IOPadAnalog` | analog | shunt A Kelvin negative |
| 10 | `ISB_P` | `sg13g2_IOPadAnalog` | analog | shunt B Kelvin positive |
| 11 | `ISB_N` | `sg13g2_IOPadAnalog` | analog | shunt B Kelvin negative |
| 12 | `FAULT_N` | `sg13g2_IOPadOut4mA` | 3.3 V | low while a fault is latched |
| 13 | `GATE_A` | `sg13g2_IOPadOut30mA` | 3.3 V | gate output A |
| 14 | `GATE_B` | `sg13g2_IOPadOut30mA` | 3.3 V | gate output B |
| 15 | `GATE_C` | `sg13g2_IOPadOut30mA` | 3.3 V | gate output C |
| 16 | `CS_N` | `sg13g2_IOPadIn` | 3.3 V | SPI select; high = BiSS/SSI mode on pads 17–18 |
| 17 | `MA` / `SCLK` | `sg13g2_IOPadIn` | 3.3 V | BiSS/SSI clock or SPI clock |
| 18 | `SLO` / `SDO` | `sg13g2_IOPadOut4mA` (TriOut if bused) | 3.3 V | BiSS/SSI data out or SPI data out |
| 19 | `SDI` | `sg13g2_IOPadIn` | 3.3 V | SPI data in |
| 20 | `EN` / `STO_IN` | `sg13g2_IOPadIn` | 3.3 V | hardware enable; low forces the gates low and latches a fault |
| 21 | `SIN_P` | `sg13g2_IOPadAnalog` | analog | encoder sine positive |
| 22 | `SIN_N` | `sg13g2_IOPadAnalog` | analog | encoder sine negative |
| 23 | `COS_P` | `sg13g2_IOPadAnalog` | analog | encoder cosine positive |
| 24 | `COS_N` | `sg13g2_IOPadAnalog` | analog | encoder cosine negative |

Side assignment: pads 1–6 south, 7–12 east, 13–18 north, 19–24 west. The encoder inputs sit on
the west side, away from the gate outputs on the north side. Package lead numbering follows the
G1 bond plan rule (pad to the lead directly opposite). Board: one RS-422 transceiver between pads
17/18 and the BiSS/SSI cable; the master compensates the added line delay.

## 4. Parameter classification

| Parameter | Value | Class | Basis |
| --- | --- | --- | --- |
| Process | IHP SG13G2 open PDK, pinned commit to be set | specified | PDK |
| Die | 1.414 mm (fallback 1.5 mm, D9) | specified | PLAN.md |
| Supplies | VDD 1.2 V (1.08–1.32), IOVDD = VDDA 3.3 V (3.0–3.6) | specified | G1 |
| Encoder input | 40 mVpp–1.4 Vpp differential, common mode 0.5–2.8 V | specified | S1 |
| AFE, revision B result | gain step error ≤ 1.87 %; f_c ≥ 1.057 MHz; pole matching ≤ 0.895 % (20-sample MC); THD ≤ −65.4 dB at 100 kHz; noise 0.35 LSB at ×1, 35.3 µV at ×32 (ss, limit 35 µV, marginal fail); PSRR ≥ 54.9 dB; settling into the ADC track-and-hold 0.506 LSB (marginal fail, re-run at the D11 swing); area ≈ 0.084 mm², 5.0–6.4 mW | simulated (schematic) | `../blocks/r1_afe/README.md` |
| AFE, revision C result | revision B loop margins found inadequate (stage-1 DM PM 15–17°, CM PM 13° at ss ×32; explains the oscillation seen); revision C: stage-1 DM PM 68°, CM PM 54.3° at ss ×32 (target 60°, fails; f_c kept first), f_c ≥ 1.023 MHz, gain step error ≤ 1.70 %, pole matching ≤ 0.96 %, THD ≤ 0.032 %, noise 34.8 µV at ×32 (ss), settling total 1.29 LSB (linear, calibratable; non-linear residual 0.082 LSB), output CM 0.577–0.648 V (fails ±30 mV), D16 1.44 Vpp not yet applied (ADC sees 1.6 Vpp = 89 % FS); area ≈ 0.091 mm², 1.53–1.86 mA | simulated (schematic) | `../blocks/r1_afe/README.md` |
| AFE, revision D result | D16 applied (1.43–1.46 Vpp); output CM 0.594–0.597 V; stage-1 CM PM 62.4° at ×32 (cross-coupled Miller), f_c 1.020 MHz; noise 31.0 µV at ×32 (ss); THD 0.025 %; pole matching 0.961 %; PSRR 54.3 dB; settling non-linear residual 0.005 LSB, total 0.38 LSB (linear part removed by the ADC gain calibration, INTERFACES change); ffx corner (ff, 3.0 V, 125 °C) fails: DM1 PM 52.8°, CM1 54.3°, CM2 59.6° (fix for DM1 identified, not applied); area ≈ 0.099 mm², 1.71–2.00 mA | simulated (schematic) | `../blocks/r1_afe/README.md` |
| AFE, revision E result | compensation re-tuned: all seven corners ≥ 60° on every loop (ffx DM1 72.5°, CM1 62.3°, CM2 61.6°), f_c ≥ 1.017 MHz; stage-2 DM gain margin 7.0 dB (5.5 dB at ssx, no limit set); pole matching 0.976 %; settling residual criterion unchanged; area ≈ 0.100 mm² | simulated (schematic) | `../blocks/r1_afe/README.md` |
| ADC, revision 3 result | full scale ±0.914 V (D16); reference buffer best case ±1 LSB code error (fails 0.25; both slices switch the LSB array at decision 5 together); comparator noise 57.5 µV tt, 75.7 µV ss/125 °C (fails 60) under the 13 ns strobe forced by the D17 frame; weight-calibration method defined (model 50/50 MC samples DNL ≤ 0.5 LSB, circuit demo at tt); dynamic tt SNDR 70.9 dB (N 32); area ≈ 0.070 mm², VDDA 0.84–1.65 mA, VDD 0.45 mA; revision 4 under D18 in progress | simulated (schematic) | `../blocks/r1_adc/README.md` |
| ADC, revision 4 result | D18 frame passed (14 ticks, track ≥ 258 ns); comparator noise at ss 55.9 µV (passed); reference settling 0.71–0.86 LSB (fails 0.25; slice stagger worse; per-slice decoupling and separate LSB reference not run → revision 5); decision 0 at CM 0.6 V does not resolve at ss (comparator input stage to be changed in revision 5, contract CM stays 0.6 V); reference buffer without divider plus 10 pF filter adopted (bandgap noise at the CDAC 88 µV tt, 109–117 µV ss); dynamic tt N 256 SNDR 63.0 dB; area ≈ 0.068 mm², VDDA 0.84 mA, VDD 2.29 mA | simulated (schematic) | `../blocks/r1_adc/README.md` |
| Current sense, loop stability (revision 1) | differential loop PM 72–79°, AZ servo ≥ 92° (passed); CM/CMFB loop PM 35–50° normal, 21–42° with AZ closed, GM fails at ff (failed 60°/10 dB; CM-step overshoot 25–44 %); shunt step settles to 0.5 % in 102 ns tt / 205 ns ss; revision 2 in progress | simulated (schematic) | `../blocks/r1_isense/README.md` |
| Safety comparator hysteresis | 1.56–2.79 calibration steps (LSB/8) over corners; two-sided search residual ≤ 0.089 LSB | simulated (schematic) | `../blocks/r1_safe/README.md` |
| Bandgap layout | 96.0 × 194.3 µm = 0.0187 mm², Metal1–4, DRC 0, antenna 0, LVS passed; post-layout RC: VREF 1.0460 V (+0.11 %), TC 9.9 ppm/°C, 51.5 µA, loop PM 126–127°; contact resistance in PCells not extracted; fill, LEF, corner TC, PSRR, noise post-layout not run | simulated (post-layout RC) | `../blocks/r1_bgr/README.md` |
| Lineage block layouts (T2F, level shifter, gate logic) | DRC 0, antenna 0, LVS match; T2F 92 × 103 µm (XOR 0 against G1), level shifter 9.2 × 11.7 µm, gate logic 126 × 49 µm (HV variant) or 28 × 28 µm (LV variant, recommended); PEX and post-layout not run | measured on the GDS | block READMEs |
| Control, revision 0.3 result | D18 applied; comparator calibration search matches the r1_safe model 274/274; LibreLane sign-off clean at 42 MHz (0 timing violators at 3 corners, DRC/LVS/antenna 0), die 0.477 mm² at 60.2 % utilisation, cell area 0.245 mm²; count-safe: no count loss at 250 kHz with the 44-tick gap up to 1.6·10⁹ Hz/s (RTL snap-free limit) | simulated (RTL, hardened) | `../blocks/r1_ctrl/README.md` |
| Bandgap, revision r1 result | VREF 1.045 V, TC 8.4 ppm/°C nominal, 9/81 corner runs at 34–35 ppm/°C (fails 30), σ(VREF) 0.40 % over 50 mismatch samples, 52 µA, start-up ≤ 0.66 ms at a 1 ms ramp; loop stability and noise not run; area ≈ 0.016–0.020 mm² | simulated (schematic) | `../blocks/r1_bgr/README.md` |
| Encoder frequency | full accuracy ≤ 100 kHz; count-safe 250 kHz shown on the r1_ctrl 0.3 RTL with the D18 22-tick frame and one 44-tick gap per PWM period, up to 1.6·10⁹ Hz/s electrical acceleration; the D17 36-tick frame (208 kHz) is withdrawn | simulated (RTL) | S1, D18, r1_ctrl 0.3 |
| Angle resolution | 16 bit per period from the tracking filter; 12-bit raw samples | specified | S1 |
| Angle accuracy after host calibration | ≤ ±0.25° el electronic (RSS, estimated); ±0.64° el total target on a 32-pole ring | estimated | S1 |
| ADC | 12 bit, ENOB ≥ 11.5, 2 MSPS (one SAR, two top-plate CDAC track-and-holds, 4:1 mux), FS ±0.9 V differential from a unity-gain reference buffer (D16), 14 decisions with two redundant bits and host-loaded per-bit weights (D12, D17), both slices converting in parallel in a 36-tick frame (D17), comparator noise ≤ 60 µV rms (D14) | specified | S1, D3, T2 |
| ADC, revision 2 result | 50/50 mismatch samples without missing codes after weight correction (DNL median 0.53, max 0.69 LSB); FS ±0.919 V; INL ±1.3 LSB; ENOB 11.4 without device noise, 11.2 derived with noise; comparator noise 58 µV tt / 82 µV ss-125 °C (fails 60 µV at the hot corner); reference buffer settles to 1 LSB (target 0.25); area ≈ 0.066 mm² | simulated (schematic) | `../blocks/r1_adc/README.md` |
| ADC, revision 1 result | INL ≤ 0.49 LSB, DNL within ±0.25 LSB at tt (codes 0–2154); ENOB 11.76 without device noise, 11.35–11.55 derived with noise; skew σ 7.6 ps; CDAC mismatch MC failed (12/50 samples with missing codes) → D12; area ≈ 0.04 mm² | simulated | `../blocks/r1_adc/README.md` |
| Position latency | latched at bus request; extrapolation with velocity; published fixed value | specified | S1, S2 |
| BiSS-C | Rev D2, MA 80 kHz–10 MHz, t_busy = 2·T_MA, static timeout 20 µs nominal (14–26 µs over RC spread) | specified | S2 |
| SSI | Gray or binary, monoflop 15–25 µs | specified | S2 |
| Current sense input | ≤ 100 mV differential, settling < 300 ns | specified target | S3/joint study |
| Overcurrent response | comparator flag ≤ 236 ns after threshold (revision 3 full-path MC), ctrl 4 ticks, gate pad fall per the gate-drive row: < 1 µs at ≤ 1 nF, ≈ 1.2 µs at 5 nF | simulated (schematic) | `../blocks/r1_safe/README.md`, `../blocks/r1_gate/README.md` |
| Gate drive | 30 mA pads; dead time programmable 50 ns–2 µs; fault path (`gate_en` low to all gates below 1 V): ≤ 200 ns for gate loads ≤ 1 nF, ≤ 1 µs at 5 nF (simulated 443–933 ns over corners; the 200 ns requirement was written without a load figure) | specified from T7 results | `../blocks/r1_gate/README.md` |
| Oscillator | G1-lineage RC relaxation, 30.03 MHz at trim code 22 (D13), 5-bit trim with steps 1.16–1.81 %, reach 32.61 MHz at ss/1.08 V/125 °C, untrimmed spread at code 22 23.3–38.9 MHz, loop delay ≤ 2.32 ns, duty 49.8–49.9 %, mismatch σ_f 0.70 %, supply 117 ppm/mV (373 ppm/mV at 1 MHz ripple), white-noise jitter 103 ps over 30 cycles against the 280 ps budget, 169–311 µA, ≈ 0.018 mm² | simulated (schematic) | `../blocks/r1_osc/README.md` |
| Area | D10 decided 2026-10-21: die 1.6 mm (S6): required 0.787 mm² in a 0.880 mm² window with analog macros under the core ring, 10.6 % margin, with digital at 75 % in 520 × 664 µm and four analog layout cuts; 1.414 mm misses by 31 % | estimated from block results (S6 floorplan) | `studies/S6_FLOORPLAN.md` |
| Padring 1.6 mm (revision b) | 24 pads at 140 µm pitch, same order; DRC 0 markers on all decks (antenna 12, empty core); bond map 24/24; core window 878.6 × 875.1 µm = 0.769 mm²; ring-only LVS passes in revision c (261/261 devices, 119/119 nets; the revision b failure was a stale reference netlist) | measured on the ring GDS | `../blocks/r1_padring/README.md` |
| Power | ≈ 17–21 mW; ≈ 4.5 mA on one VDDA pad (≈ 95 mV drop on the G1 path) | estimated | S3 |
| MIM mismatch | 1 % (1σ) at 1 µm², ∝ 1/√area (PDK model; spec value blank); CDAC unit ≥ 22 fF (≈ 15 µm²) for DNL ≤ 0.5 LSB | specified from the PDK model | S4 |
| Calibration storage | none on chip; host loads registers after reset, CRC-checked | specified | S1 |

## 5. Verification gates

| Gate | What must exist | Status |
| --- | --- | --- |
| V1 AFE | gain steps, CM range, noise, AA matching at corners; pad ESD diode leakage over CM | not run |
| V2 ADC | INL/DNL and ENOB campaign (static ramp + sine), MC on the CDAC, skew between the two track-and-holds, reference buffer load | not run |
| V3 position | RTL model against a floating-point reference over head tolerances (offset 6.5 %, gain 1.25, phase 10°, h3 1 %), before and after calibration; latency and extrapolation | not run |
| V4 bus | protocol testbench per S2 list (CRC vectors, MA 80 kHz–10 MHz, t_busy, timeout corners, aborted frame, control channel, SSI); interop against ≥ 3 independent masters on the bench | not run |
| V5 current and safety | settling after a PWM edge, comparator thresholds at corners and MC, I²t model, EN/STO path, fault latch, gates low | not run |
| V6 digital | synthesis, LibreLane hardening, STA at 3 corners with derate, GLS with SDF, formal equivalence of any ECO | not run |
| V7 chip | DRC (main, maximal, density, antenna), LVS, hierarchical PEX, full-chip co-simulation with an encoder-head model and a motor-phase model | not run |
| V8 bench | encoder head on a motor, BiSS master, shunt fixture, thermal chamber | not run |

## 6. Open items before block design starts

1. ~~Oscillator~~ closed by S5: re-tuned G1 relaxation oscillator at 30 MHz with host trim; STA must close at the fastest untrimmed frequency (≈ 42 MHz) or a slow-side reset code is used.
2. ~~MIM matching coefficient~~ closed by S4: model value 1 %·µm; unit capacitor ≥ 22 fF; MC with `mm_ok=1` in V2.
3. ~~ADC reference~~ decided: 1.2 V domain SAR with an internal reference buffer and on-chip MIM decoupling (no pin is free); the buffer's area (≈ 0.02 mm²) and current (0.5–1 mA) are in the budget; V2 measures its settling under the CDAC load.
4. ~~5 V heads~~ decided: supported only while the pin voltage stays within 0.5–2.8 V (board rule; a 2.5 V common-mode head with > 0.3 V peak is out of range and needs a board divider); V1 measures pad-diode leakage up to 3.0 V.
5. BiSS Manufacturer ID not yet assigned; `MFR_ID` stays a changeable reset value.
6. ~~Current-sample timing~~ decided: the gate block generates the three low-side edges from the host-written duty/phase word and its own PWM counter, so the chip knows the phase and samples each shunt at the centre of its low-side on-time; the controller's PWM frequency and the word update rate are registers.

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
| `r1_adc` | Two track-and-holds sampled on one edge (skew < 0.5 ns) feeding a 12-bit SAR (two parallel slices, D17/D18; ENOB target 11.5, open), split 6+6 bridge MIM CDAC, bootstrapped switches, reference buffer; a multiplexer adds the two current channels between encoder conversions (D3). Alternate: two SARs at 1 MSPS if area allows | thin-oxide MOS, MIM | out: 12-bit codes, valid strobes | new; starts from IHP-AnalogAcademy module 3 |
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
| Safety comparators layout | 249 × 288 µm = 0.072 mm² (target 0.06 missed by 20 %); DRC 0, antenna 0; LVS match with a comparer-limit copy of the deck (stock deck crashes KLayout on the mux trees); post-layout comparator: threshold centre −0.044 LSB, OC trip 164–185 ns; full-block parasitics not run | simulated (post-layout, comparator only) | `../blocks/r1_safe/README.md` |
| AFE layout (revision E) | 192.8 × 494.4 µm = 0.095 mm²; DRC 0, antenna 0, LVS clean; post-layout (capacitance of the channel cell only): f_c 1.29 MHz, CM1/CM2 margin at ffx 59.7°/58.3° (fail 60°), DM1 67°, residual 0.006 LSB, noise 30.8 µV; unbalanced output routing adds −0.25 mV offset; wire resistance and top-level wiring not extracted | simulated (partial post-layout) | `../blocks/r1_afe/README.md` |
| AFE layout revision E2 | balanced pairs (≤ 3.4 fF), full RC; f_c 1.015 MHz at ss, pole matching 0.80 %, noise 31.5 µV, residual 0.005 LSB (passed); CM1/CM2 at ffx 61.3°/57.7° (fail 63° target), output CM 0.630 V at the limit from supply wiring, bias extremes fail (CM1 56° at 6.9 µA, CM 0.646 V at 15.4 µA); revision F (schematic + layout) in progress | simulated (post-layout RC) | `../blocks/r1_afe/README.md` |
| Oscillator layout (revision 1) | 154 × 118 µm = 0.018 mm²; DRC 0, antenna 0, LVS match; post-layout: 27.5 MHz at code 22 (fails 28–32), reach 28.4 MHz at ss (fails 32), trim step 2.5–2.6 % (fails 2 %), jitter 12.8 ps σ, 228 µA; wiring capacitance is the cause; revision 2 (schematic + layout) in progress | simulated (post-layout RC) | `../blocks/r1_osc/README.md` |
| Oscillator revision 2 (schematic + layout r2d) | 148 × 110 µm = 0.016 mm²; DRC 0, antenna 0, LVS match; post-layout: 30.30 MHz at code 22 (tt), reach 32.70 MHz at ss (passed), trim step ≤ 1.92 % (passed), jitter 11.6 ps σ, 39.5 MHz at code 22 and 56.4 MHz at code 0 at ff/−40 °C (trim-code rule, D13 amendment); mismatch, PSRR post-layout not run | simulated (post-layout RC) | `../blocks/r1_osc/README.md` |
| Current sense layout | 158 × 297 µm = 0.047 mm² in the S7 box; DRC 0, antenna 0, LVS match; post-layout: gain 14.05, CM 0.591 V, all loop margins ≥ 67°, step 94–249 ns, CMRR ≈ 93 dB; residual offset after auto-zero −216 µV (fails 100 µV, clock-coupling asymmetry; layout revision needed) | simulated (post-layout RC) | `../blocks/r1_isense/README.md` |
| Current sense layout revision b | same box; shielded hold nets; residual offset after auto-zero +26 to +35 µV (passed 100); gain 14.05, CM 0.59 V, step ≤ 278 ns, PM ≥ 71°; DRC 0, LVS match; DC loop-validity flag fails through the vss wiring resistance (closed loop stable; open) | simulated (post-layout RC) | `../blocks/r1_isense/README.md` |
| Bias distribution and POR (r1_bias 1d) | PTAT bias 10 µA ×4 (AFE) and 5 µA ×7 from the bandgap, σ ≈ 1 %, PSRR −45 dB at 20 kHz; POR thresholds VDDA 2.7 V / VDD 1.0 V rising with hysteresis, delay 200–250 µs, brown-out works; 97 µA tt, 147 µA worst (budget 150); bandgap loop PM 101° with the load; ffx falling threshold not run | simulated (schematic, with real bandgap and loads) | `../blocks/r1_bias/README.md` |
| Bias and POR layout | 120 × 166 µm = 0.020 mm²; DRC 0, antenna 0, LVS match; post-layout outputs within −0.1 %, POR delay 238–253 µs; does not fit the S7 placeholder slots (assembly to place) | simulated (post-layout RC) | `../blocks/r1_bias/README.md` |
| Current sense, revision 2 result | two-path CMFB: CM loop PM ≥ 67.8°, GM ≥ 28 dB in all three states at seven corners; CM-step overshoot ≤ 2.7 %; output CM 0.600–0.601 V, MC σ ≤ 4.1 mV; settling 208 ns; joint path with the comparators unchanged within 0.011 LSB and 1.8 ns; area ≈ 0.021 mm² for two channels, 171 µA VDDA + 404 µA VDD per channel | simulated (schematic) | `../blocks/r1_isense/README.md` |
| Current sense, loop stability (revision 1) | differential loop PM 72–79°, AZ servo ≥ 92° (passed); CM/CMFB loop PM 35–50° normal, 21–42° with AZ closed, GM fails at ff (failed 60°/10 dB; CM-step overshoot 25–44 %); shunt step settles to 0.5 % in 102 ns tt / 205 ns ss; revision 2 in progress | simulated (schematic) | `../blocks/r1_isense/README.md` |
| Safety comparator hysteresis | 1.56–2.79 calibration steps (LSB/8) over corners; two-sided search residual ≤ 0.089 LSB | simulated (schematic) | `../blocks/r1_safe/README.md` |
| Bandgap layout | 96.0 × 194.3 µm = 0.0187 mm², Metal1–4, DRC 0, antenna 0, LVS passed; post-layout RC: VREF 1.0460 V (+0.11 %), TC 9.9 ppm/°C, 51.5 µA, loop PM 126–127°; contact resistance in PCells not extracted; fill, LEF, corner TC, PSRR, noise post-layout not run | simulated (post-layout RC) | `../blocks/r1_bgr/README.md` |
| Lineage block layouts (T2F, level shifter, gate logic) | DRC 0, antenna 0, LVS match; T2F 92 × 103 µm (XOR 0 against G1), level shifter 9.2 × 11.7 µm, gate logic 126 × 49 µm (HV variant) or 28 × 28 µm (LV variant, recommended); PEX and post-layout not run | measured on the GDS | block READMEs |
| Control, revision 0.4 result | hardened in 520 × 664 µm at 75.15 %: setup 0 violators at three corners, hold ≥ +0.021 ns, DRC/LVS/antenna 0, 6 max-fanout violations; placed cells 239 201 µm² (limit 240 000); register map 0.4 (ANA_CTRL bits, raw ADC decision via one-hot weights); gate-level simulation, equivalence and CDC not run | simulated (RTL, hardened) | `../blocks/r1_ctrl/README.md` |
| ADC, revision 5 result | reference settling 0.16–0.21 LSB at tt/ss/ff with a separate LSB-array follower (passed 0.25, small margin); decision 0 resolved at 0.6 V CM by an NMOS-input comparator for decision 0 (63/64 inputs inside the redundancy at ss); noise at ss 57.0 µV; 12-sample MC after weight fit: major DNL ≤ 0.25 LSB on 11, 0.5 on 1; weights fit the register widths; first conversion after enable wrong (ctrl discards); area ≈ 0.07 mm² (buffer 0.041), VDDA 1.05 mA; corners, full ramp and layout not run | simulated (schematic) | `../blocks/r1_adc/README.md` |
| ADC, revision 5 closure | first-conversion cause: bootstrap charge (fixed by a hold pulse from ctrl); static windows at ss/ff clean (DNL 0.54); dynamic ENOB 11.4 at ss, 10.8 at ff (HD3); reference settling 0.16–0.21 LSB at all corners and bias extremes; reference noise 88 µV tt / 110 µV ss (marginal); INL 1.4–1.6 LSB with a 1.1 LSB cubic bow (open); IDD 0.9 mA, IDDA 1.0 mA (4.5 mW) | simulated (schematic) | `../blocks/r1_adc/README.md` |
| Top-level assembly (try e, 1.7 mm) | all macros but the ADC placed on the 1.7 mm ring at the C4 positions (deltas ≤ 36 µm), 46 nets routed; DRC main/maximal/antenna 0, density 53 (no fill yet); LVS 52/52 pairs with the comparer-limit deck; drop-in checklist for ADC, ctrl 0.6, AFE E2, isense b; fill, IR drop, bond plan, post-layout simulation not run | measured on the GDS | `../blocks/r1_top/README.md` |
| Control 0.4 sign-off verification | true worst setup slack +1.78 ns at slow, +9.6 ns typ; hold +0.021 ns at fast; gate-level simulation with SDF at slow passes (one testbench-criterion failure, not design); equivalence inconclusive (names lost in synthesis); CDC hand review: 6 unsynchronised paths to fix in 0.5; max-fanout limit 8 with 6 violators | simulated (gate level) | `../blocks/r1_ctrl/reports/signoff_v04.md` |
| Control, revision 0.5 result (RTL) | tap-index adders to r1_safe (exhaustive check passed), first-conversion discard, ANA_CTRL bit map, CDC fixes with a crossing table (SSI limited to 2 MHz), SDC port check; regression 316 + 16 + 274 cases passed; cell area +4 % (0.229 mm² synthesis); hardening and gate-level for 0.5 not run | simulated (RTL) | `../blocks/r1_ctrl/README.md` |
| Control, revision 0.3 result | D18 applied; comparator calibration search matches the r1_safe model 274/274; LibreLane sign-off clean at 42 MHz (0 timing violators at 3 corners, DRC/LVS/antenna 0), die 0.477 mm² at 60.2 % utilisation, cell area 0.245 mm²; count-safe: no count loss at 250 kHz with the 44-tick gap up to 1.6·10⁹ Hz/s (RTL snap-free limit) | simulated (RTL, hardened) | `../blocks/r1_ctrl/README.md` |
| Bandgap, revision r1 result | VREF 1.045 V, TC 8.4 ppm/°C nominal, 9/81 corner runs at 34–35 ppm/°C (fails 30), σ(VREF) 0.40 % over 50 mismatch samples, 52 µA, start-up ≤ 0.66 ms at a 1 ms ramp; loop stability and noise not run; area ≈ 0.016–0.020 mm² | simulated (schematic) | `../blocks/r1_bgr/README.md` |
| Encoder frequency | full accuracy ≤ 100 kHz; count-safe 250 kHz shown on the r1_ctrl 0.3 RTL with the D18 22-tick frame and one 44-tick gap per PWM period, up to 1.6·10⁹ Hz/s electrical acceleration; the D17 36-tick frame (208 kHz) is withdrawn | simulated (RTL) | S1, D18, r1_ctrl 0.3 |
| Angle resolution | 16 bit per period from the tracking filter; 12-bit raw samples | specified | S1 |
| Angle accuracy after host calibration | ≤ ±0.25° el electronic (RSS, estimated); ±0.64° el total target on a 32-pole ring | estimated | S1 |
| ADC | 12 bit, ENOB target ≥ 11.5 (simulated so far 10.2 at N 256 in revision 4, 11.4 in revision 2 without device noise: the target is not met in simulation and stays open), two slices each with its own comparator and sequencer, 22-tick encoder frame = 1.36 M pair conversions/s, the current pair once per PWM period (D18; the 2 MSPS / 4:1 mux text is withdrawn), FS ±0.9 V differential from a reference buffer (D16), 14 decisions with two redundant bits and host-loaded per-slice weights (D12, D17, D18), comparator noise ≤ 60 µV rms (D14) | specified; ENOB open | S1, D3, D16–D18, T2 |
| ADC, revision 2 result | 50/50 mismatch samples without missing codes after weight correction (DNL median 0.53, max 0.69 LSB); FS ±0.919 V; INL ±1.3 LSB; ENOB 11.4 without device noise, 11.2 derived with noise; comparator noise 58 µV tt / 82 µV ss-125 °C (fails 60 µV at the hot corner); reference buffer settles to 1 LSB (target 0.25); area ≈ 0.066 mm² | simulated (schematic) | `../blocks/r1_adc/README.md` |
| ADC, revision 1 result | INL ≤ 0.49 LSB, DNL within ±0.25 LSB at tt (codes 0–2154); ENOB 11.76 without device noise, 11.35–11.55 derived with noise; skew σ 7.6 ps; CDAC mismatch MC failed (12/50 samples with missing codes) → D12; area ≈ 0.04 mm² | simulated | `../blocks/r1_adc/README.md` |
| Position latency | latched at bus request; extrapolation with velocity; published fixed value | specified | S1, S2 |
| BiSS-C | Rev D2, MA 80 kHz–10 MHz, t_busy = 2·T_MA, static timeout 20 µs nominal (14–26 µs over RC spread) | specified | S2 |
| SSI | Gray or binary, monoflop 15–25 µs | specified | S2 |
| Current sense input | ≤ 100 mV differential, settling < 300 ns | specified target | S3/joint study |
| Overcurrent response | comparator flag ≤ 236 ns after threshold (revision 3 full-path MC), ctrl 4 ticks, gate pad fall per the gate-drive row: < 1 µs at ≤ 1 nF, ≈ 1.2 µs at 5 nF | simulated (schematic) | `../blocks/r1_safe/README.md`, `../blocks/r1_gate/README.md` |
| Gate drive | 30 mA pads; dead time programmable 50 ns–2 µs; fault path (`gate_en` low to all gates below 1 V): ≤ 1 µs for direct gate loads ≤ 1 nF (simulated 443–933 ns over corners); loads above 1 nF, e.g. 5 nF, are not a supported direct load and need an external gate driver (D19, 2026-10-21; the earlier 200 ns figure was written without a load and is withdrawn) | specified from T7 results | `../blocks/r1_gate/README.md` |
| Oscillator | G1-lineage RC relaxation, 30.03 MHz at trim code 22 (D13), 5-bit trim with steps 1.16–1.81 %, reach 32.61 MHz at ss/1.08 V/125 °C, untrimmed spread at code 22 23.3–38.9 MHz, loop delay ≤ 2.32 ns, duty 49.8–49.9 %, mismatch σ_f 0.70 %, supply 117 ppm/mV (373 ppm/mV at 1 MHz ripple), white-noise jitter 103 ps over 30 cycles against the 280 ps budget, 169–311 µA, ≈ 0.018 mm² | simulated (schematic) | `../blocks/r1_osc/README.md` |
| Area | D10 amended 2026-10-21 (S7): die 1.7 mm. Real macro sizes give an analog sum of 0.342 mm² (trigger 0.30); 1.6 mm reaches 5.5 % margin only with four unproven re-shapes; 1.7 mm holds every macro as laid out with 13.4 % margin. Laid out: digital 0.345, AFE 0.095, safe 0.072, isense ≈ 0.047, bandgap 0.019, osc 0.018, T2F 0.009, gates and level shifters; ADC slot 0.080 | estimated from block layouts (S7) | `studies/S7_REFLOORPLAN.md` |
| Padring 1.7 mm (revision d, ring of record) | 24 pads at 142 µm pitch, same order; DRC 0 on all decks (antenna 12, empty core); ring-only LVS 261/261; bond map 24/24; core window 978.6 × 975.1 µm = 0.954 mm²; canonical LVS not run | measured on the ring GDS | `../blocks/r1_padring/README.md` |
| Padring 1.6 mm (revision b) | 24 pads at 140 µm pitch, same order; DRC 0 markers on all decks (antenna 12, empty core); bond map 24/24; core window 878.6 × 875.1 µm = 0.769 mm²; ring-only LVS passes in revision c (261/261 devices, 119/119 nets; the revision b failure was a stale reference netlist) | measured on the ring GDS | `../blocks/r1_padring/README.md` |
| Power | ≈ 17–21 mW; ≈ 4.5 mA on one VDDA pad (≈ 95 mV drop on the G1 path) | estimated | S3 |
| MIM mismatch | 1 % (1σ) at 1 µm², ∝ 1/√area (PDK model; spec value blank); CDAC unit ≥ 22 fF (≈ 15 µm²) for DNL ≤ 0.5 LSB | specified from the PDK model | S4 |
| Calibration storage | none on chip; host loads registers after reset, CRC-checked | specified | S1 |
| AFE, netlist F3 and layout E9c result (2026-10-30, D26/D29) | OTA1 Miller Rz 23 µm; layout E9c (192.8 × 494.4 µm, 21 pins, C-trim 19/19): DRC/antenna 0, LVS, supply islands 0; extracted: all loop rows ≥ 63.31° / 11.51 dB incl. DM1 at the ffx 6.9 µA bias extreme 65.26°, supply-path loop gain ≤ −82.3 dB, CM step ≤ 1 loop overshoot, f_c ss 1.063 MHz, noise ×32 ss 32.65 µV, THD 0.010 %, static offset −4.0..−0.6 mV (limit 5), drift span 1.54 mV (D29 allocation 1.6 mV, condition: full-chip test 2), x1 ΔC +0.2 fF; MC pole matching 0.84 % | simulated | `blocks/r1_afe/README.md` |
| ADC, layout B7 final result (2026-10-30, D23/D30/D31) | 439.0 × 205.42 µm, 52 pins, SAR sub-macro r1_adc_sar (D21); DRC/antenna 0, LVS stock and comparer-limit; static offset 9 LSB (limit 10), windows 1024/3072 no missing code |DNL| ≤ 0.33, full scale ±0.86 V at tt/ss/ff, code-level reference check ≤ 1 LSB at tt and ss (ff slot 9 −2 LSB, carried), offset drift 11 / 9 LSB against 4 (carried to chip-level test 2 with host calibration, D31), INL bow 4.7 / 6.2 LSB (no limit), ff output window 0.401 ns (contract 0.40 ns); B8-B10 not adopted | simulated | `blocks/r1_adc/README.md` |
| Control, revision 0.9 result (2026-10-30, D27) | IA/IB offset and gain words (Q2.14) and raw IA/IB min/max capture, ID 0x5209; regression 600 checks 0 failed, gain/offset model 16 955 vectors 0 mismatches, chip-level current-step error +5.66 % → 0.00 % after host calibration; hardening t32 (timing-driven placement, no clock ECO): utilisation 84.4 %, 128 pins, DRC/LVS/antenna 0, setup +5.68 ns slow, hold +0.12 ns fast, derated setup at the try-h1 supply losses +3.34 ns, slew/cap/fanout clean, gate-level SDF slow 20/20; hold at a 0.40 ns ADC minimum input delay +0.67 ns | simulated / STA | `blocks/r1_ctrl/README.md` |
| Top-level supply feed, try h1 result (2026-10-30, D24) | every IO pad cell as shipped; top-level metal cannot bypass the IOPadVss Metal2 plate; h1 network (south VSS straps and bar, VDD fingers and tabs, TopMetal2 pad fingers, AFE VDDA strap): VDD + VSS feed at the worst ctrl grid point 1.383 Ω max sheet (limit 1.43), loss 55.7 mV, isense-bgr shared path 1.82 Ω (limit 2.3), EM 69 rows 0 failed, DRC/density/LVS (comparer-limit deck) clean, bond map 24/24; pin map unchanged (die pad 6 IOVSS→VSS option recorded, 1.172 Ω) | extracted / simulated | `blocks/r1_top/README.md` |

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

# R1 measurement plan (draft 0.1, 2026-10-21)

Status: **not run**. No R1 silicon exists. No fixture is built. No instrument record exists.
This file is a bench plan. It is not evidence of silicon behaviour.

Every pass criterion in this plan is copied from
[`../specification/R1_TOP_LEVEL_SPECIFICATION.md`](../specification/R1_TOP_LEVEL_SPECIFICATION.md)
section 4 (parameter table) or section 5 (gates V1-V8). Each value carries its class from that file:
*specified* (a target), *estimated*, or *simulated* (a schematic or RTL result, never measured).
A simulated value in this plan is a prediction. The bench must measure it. It does not replace it.

Register names and addresses are from
[`../blocks/r1_ctrl/R1_REGISTER_MAP.md`](../blocks/r1_ctrl/R1_REGISTER_MAP.md) (draft 0.4, `ID` 0x5204).
Pin names are from the specification section 3. The pad map at 1600 um is in
[`../padframe/README.md`](../padframe/README.md).

## Contents

1. Status summary
2. Test fixture
3. Bring-up sequence
4. Tests (one per gate V1-V8 and per parameter row)
5. Safety tests
6. Data record format and folder layout
7. Open items

## 1. Status summary

| Item | Status |
| --- | --- |
| Fixture design | not run |
| Fixture build and continuity check | not run |
| Bring-up sequence (section 3) | not run |
| Tests T01-T47 and S01-S13 (sections 4 and 5) | not run |
| Gates V1-V5 and V8 (bench part) | not run |
| Gates V6 and V7 | not applicable on the bench (see section 4.9) |
| Measured data in `results/` | none |

## 2. Test fixture

### 2.1 Samples and package

1. The QFN24 package is 4 x 4 mm, 0.5 mm pitch, six leads per side, exposed paddle = `VSS`.
2. The lead for each die pad is in the table of `../padframe/README.md` (pad n to lead 31 - n for pads 13-24).
3. Use a QFN24 test socket for bring-up and for temperature sweeps. Use soldered boards for the
   high-speed tests (T38, S04). A socket adds inductance and capacitance on the ISA/ISB and `GATE` leads.
4. Record the fixture type in every result record (field `fixture`).
5. The sample count is not set. This plan assumes N = 10 packaged dies, as in the G1 tape-in package.
   The count is an open item (O-01). Each test names its sample tier: *all* (every die), *3 dies*, or *1 die*.

### 2.2 Fixture blocks

| # | Block | Requirement | Pins |
| --- | --- | --- | --- |
| F1 | Core supply `VDD` | 1.2 V, adjustable 1.08-1.32 V, current limit set, series current sense | 1 (`VDD`) |
| F2 | IO and analog supply | 3.3 V, adjustable 3.0-3.6 V. One source. `VDDA` (pad 7) and `IOVDD` (pad 3) tie to the same rail on the board (G1 rule D14). Separate current-sense links for `VDDA` and `IOVDD`, each <= 0.5 ohm, with decoupling on the chip side | 3 (`IOVDD`), 7 (`VDDA`) |
| F3 | Current measurement | 4-wire sense across each link of F1 and F2. Use a 6.5-digit DMM or a source-measure unit (SMU) with a 1 uA range | 1, 3, 7 |
| F4 | Grounds | `VSS` (pads 2, 5), `IOVSS` (pads 4, 6) and the paddle tie to one board ground | 2, 4, 5, 6, paddle |
| F5 | Supply sequencer | `VDD` in regulation before `IOVDD`/`VDDA` rises, and the reverse at shutdown. The sequencing rule is **assumed** from G1 (rule B1). R1 has no own rule (O-02) | 1, 3, 7 |
| F6 | Encoder emulator | Two-channel arbitrary waveform generator (AWG), 16-bit, >= 10 MS/s per channel, true differential outputs or a balun-free differential driver stage. Default: 1 Vpp differential, sine on `SIN`, cosine on `COS` (90 degree offset), frequency 1 kHz-250 kHz, common mode (CM) 1.65 V. CM adjustable 0.5-2.8 V. Add a second AWG pair or a gain-error and phase-error stage to set the head errors of gate V3 (offset 6.5 %, gain 1.25, phase 10 degrees, h3 1 %) | 21-24 |
| F7 | Slow DC source for the encoder inputs | Differential DC source, +/-1 V in 1 mV steps, for ramps (T15, T16). Use a 6.5-digit DMM on the same nodes | 21-24 |
| F8 | Shunt-voltage source | Two differential sources, one for `ISA`, one for `ISB`. Range +/-100 mV. Static accuracy better than 20 uV (reference DMM, 6.5 digit). Step source: edge time <= 10 ns (10-90 %), 0 to +/-100 mV, with a 50 ohm source and a resistive divider to the pad. Common mode of the shunt pins: near `VSS` (low-side shunt). The step source triggers the oscilloscope | 8-11 |
| F9 | Gate loads | Per output: 1 nF to `VSS` (supported load). Switchable 5 nF to `VSS` (documented experiment, **not supported**; see S13). Use C0G/NP0 capacitors. A probe is high impedance, 1 pF class, 500 MHz class | 13-15 |
| F10 | Bus master | FPGA or MCU board with 3.3 V IO, one 3.3 V RS-422 transceiver (candidate THVD1450 class) between pads 17/18 and the cable for BiSS/SSI tests. SPI tests use a direct 3.3 V connection. The master generates the frames in section 2.3 | 16-19 |
| F11 | `EN`/`STO_IN` switch | Host-driven low-impedance 3.3 V CMOS buffer with a clean edge. A 100 kohm pull-down at the package. A manual switch to the same node for STO tests. Edge time <= 5 ns, trigger output to the oscilloscope | 20 |
| F12 | `FAULT_N` monitor | Logic-analyzer channel, oscilloscope channel and a host GPIO. Pad has a 4 mA driver. Load: >= 10 kohm | 12 |
| F13 | Thermal | Temperature chamber -40 to +125 C, or a hot plate for the upper range with a cold spray or Peltier plate for the lower range. A thermocouple (type K or T) on the package top, plus a second one on the board. Record both. Wait for 10 min at each point after the thermocouple settles | all |
| F14 | Oscilloscope | 4 channels, >= 500 MHz, with >= 2.5 GS/s. 200 MHz is the minimum for T38 and S04 | 8-15, 20 |
| F15 | Frequency counter | 6-digit counter with an external 10 MHz reference. Used for `MA` timing and the `OSC_COUNT` reference clock | 17 |
| F16 | Reference clock for `OSC_COUNT` | Square wave, 1 MHz, jitter < 1 ns, 3.3 V, on `MA`/`SCLK` | 17 |
| F17 | Encoder head and motor (gate V8 only) | An incremental or sin/cos head with a magnet or a scale, a motor with a shaft encoder as the reference, and a 3-phase low-side driver stage with external FETs and 3 shunt-isolated phases. Part numbers are open (O-12) | 8-15, 21-24 |

### 2.3 Frames the bus master must generate

All frames come from `R1_REGISTER_MAP.md`. The section numbers refer to that file.

| Frame | Format | Source |
| --- | --- | --- |
| SPI register frame | Mode 0, 24 bits, MSB first. `SDI` = `R/nW`, `A[6:0]`, `D[15:0]`. `SDO` = `STATUS[7:0]`, then the data of the **previous** frame. A read needs two frames. `CS_N` high >= 8 ticks between frames (about 270 ns at 30 MHz; use >= 1 us). A frame with other than 24 clocks is ignored and counts in `DIAG_SPI.SPI_ERR` | 2.1 |
| Mode switch | Wait until `SLO` is high. `SCLK` low. `CS_N` low. Send SPI frames. `CS_N` high, then `MA` high. Wait one `TIMEOUT_TICKS` | 1 |
| Write timing | A write takes effect 3-5 ticks after `CS_N` rises. Read back every safety-relevant write (G1 rule, adopted here as an assumption) | 4.12 |
| BiSS-C frame | `MA` idles high. Falling edge starts a frame. Rising edges: `LAT`, `ACK` (SLO = 0), busy (SLO = 0), `START` (SLO = 1), `CDS`, `[MT 16] ST nE nW` MSB first, CRC-6 (poly 0x43, start 0, inverted), stop (SLO = 0). Then wait `TIMEOUT_TICKS` quiet. `MA` 80 kHz-10 MHz | 3.1 |
| BiSS control channel | One CDM bit per frame. Header: `S=1`, `CTS=1`, `ID[2:0]=0`, `ADR[6:0]`, inverted CRC-4 (poly 0x13) over `CTS`, `ID`, `ADR`. Slave answers in the CDS bit of the next frame. Register read of 0x40-0x7F | 3.3 |
| SSI frame | `BUS_CFG.SSI` = 1. `MA` idles high. First falling edge freezes the word. Each rising edge shifts out one bit of `[MT 16] ST`, binary or Gray. Clock <= 2 MHz. Monoflop = `TIMEOUT_TICKS` | 3.2 |
| Oscillator measure frame | Write `OSC_CFG.MEAS` = 1. Send >= 32 periods of 1 MHz on `MA`/`SCLK`. Read `OSC_COUNT` | 4.3 |

The master software logs the line state with a time stamp for every frame. It also logs the raw
bit stream, not only the decoded values.

### 2.4 Safe-state rules for the fixture

1. Keep all external FETs unpowered, or use dummy loads, until T47. In T43-T45 and S01-S13 the gate outputs drive capacitors.
2. `GATE_A/B/C` stay low in reset. Verify this on the oscilloscope during every power-up.
3. Limit the supply currents. Set VDD to 100 mA and 3.3 V to 50 mA at first power-up (about 5 times the 4.5 mA estimate on `VDDA`).
4. Handle the `SIN`/`COS`/`ISx` pads as ESD-sensitive. Use a wrist strap.

## 3. Bring-up sequence

Run these steps in this order on every die. Stop at the first failed step. Log the stop. Do not skip a step.
Each step is a record with test id `B01`-`B14`.

| Step | Action | Check | Status |
| --- | --- | --- | --- |
| B01 | Unpowered. Measure continuity of each pin to `VSS` and to the supply rails with a bounded test current (< 1 mA, compliance >= 1 V). Check that the paddle and the four ground pads connect | No short. Supply diodes forward with >= 1 V compliance (an open supply bond shows as compliance). | not run |
| B02 | Hold `EN` low. Ramp `VDD` to 1.2 V (current limit 100 mA). Then ramp `IOVDD`/`VDDA` to 3.3 V (limit 50 mA). Ramp time 1 ms. Observe `GATE_A/B/C` on the oscilloscope during both ramps | `GATE_x` stay <= 0.3 V. No supply at its current limit. Record `I(VDD)`, `I(VDDA)`, `I(IOVDD)` | not run |
| B03 | Wait 5 ms. Read `FAULT_N`. | `FAULT_N` is low (reset value of `FAULT` = 0x1800, `POR` set). Gates low | not run |
| B04 | Set the mode (`CS_N` low, `SCLK` low). Read `ID` (0x00) twice. | `ID` = 0x5204 for RTL revision 0.4. A different value is logged and the register map version of the die is identified. | not run |
| B05 | Read `STATUS` (0x01), `FAULT` (0x02) and a few reset values: `SCHED` 0x1416, `TIMEOUT_TICKS` 600, `OSC_CFG` 0x0016, `GAIN` 0x4000 | All equal the reset values in the map | not run |
| B06 | Read BiSS IDs through SPI: 0x78-0x7D | Bytes 0x52 0x31 0x4A 0x46 0x45 0x30 ("R1JFE0"). 0x41 = 0x00 | not run |
| B07 | Oscillator trim. Start with `OSC_TRIM` = 22 (reset). Drive 1 MHz on `MA`. Write `OSC_CFG.MEAS`. Wait for `STATUS.OSC_DONE`. Read `OSC_COUNT`. f_clk = OSC_COUNT x 1 MHz / 16. Step `OSC_TRIM` until f_clk is nearest to 30 MHz. Write the final code. Write `TIMEOUT_TICKS` = OSC_COUNT x 20 us x 1 MHz / 16. Write `OSC_WIN` (for example 0x201C at 30 MHz). | `OSC_DONE` = 1. f_clk 23-39 MHz at code 22 (simulated untrimmed spread 23.3-38.9 MHz). Trim reaches 30 MHz +/-1 step (steps 1.16-1.81 %, simulated). The clock is not on a pad. Use the BiSS timeout (T30) as a cross check | not run |
| B08 | Reference check. The bandgap (`r1_bgr`) has no pin. Check it in three indirect ways. (a) Supply current at 3.3 V: record it as a signature (bandgap 51.5 uA simulated). (b) Apply a DC 0 V and a DC +0.5 V differential at `SIN`/`COS` and read `RAW_SIN`/`RAW_COS`. Full scale is +/-0.914 V at the ADC (simulated, set by the reference). (c) Read `TEMP` (0x2B). | Reference-dependent ADC code agrees with the gain model within the T15 limit. Do not accept a bandgap value from a single die. Compare with the sample median | not run |
| B09 | Write the position calibration words (0x10-0x17) with default values. Write the comparator words (0x36, 0x37, 0x39, 0x3C) and the ADC weights (0x50-0x5D, 0x60-0x6D) with reset values. | Read back. All values equal | not run |
| B10 | Set `PWM_PERIOD`, `AZ_START`, `AZ_CFG.AZ_LEN` for the comparator calibration (>= 100 ticks after `az_win` end, `CAL_STEP` = 1). Keep `THR_ZERO` = 14. Keep `CMP_CAL_IDEAL` = 0x3748. Gates are off. Write `CTRL.CMP_CAL` = 1. Wait for `STATUS.CAL_BUSY` = 0 (14 PWM periods). Read `CMP_CAL_A/B`. Check the `EXH` bits | All four `EXH` bits = 0. Codes in 1..62. The comparator order is `OC_A`, `NEG_A`, `OC_B`, `NEG_B`. Repeat 5 times. The code must repeat within +/-1 step | not run |
| B11 | ADC weight calibration, slice A, then slice B (section 3.1). Load the measured weights. | DNL/INL after calibration within the T16 and T17 limits | not run |
| B12 | Compute `CAL_CRC` (CRC-8, poly 0x07, init 0xFF, no reflection, no final XOR) over the 43 words of the map (section 4.4). Write it. Wait >= 172 ticks plus 2 ticks per SPI frame. | `STATUS.CAL_VALID` = 1 | not run |
| B13 | Write `CTRL.CLR` (clear faults). Read `FAULT`. | Bit 11 (CAL) and bit 12 (POR) clear. Bit 8 (STO) clear while `EN` is high. If `EN` is low, bit 8 stays set | not run |
| B14 | Raise `EN`. Write `CTRL.GATE_EN` = 1 with `PWM_PERIOD` = 0 (PWM off). Then enable a first PWM word with a low duty (about 5 %), `DEAD` = 15 and 1 nF load. | `STATUS.GATE_ACTIVE` = 1. Gate outputs show the pattern. Then go to the functional tests | not run |

The host rules for every write in B07-B14: read back every safety-relevant write; keep the SCLK-low phase
inside a frame short (the SPI re-frame hazard is a G1 finding; the R1 limit is not set, O-03).

### 3.1 ADC weight calibration with the ramp procedure

The ramp procedure is in `../blocks/r1_adc/README.md`, revision 3, "Weight calibration: bench procedure".
It needs the 14 raw decisions. The register map does not give a raw-decision read. It gives `RAW_SIN`
and `RAW_COS` (corrected 12-bit codes). Use the **one-hot-weight read**. This is a proposal. It is not simulated (O-04).

1. For slice A, write the weights `W[i]` = 2^(i+2) for decisions i = 0..11 and 0 for i = 12, 13. Each weight fits its
   stored width WW(i) = i + 3 bits.
2. Convert a fixed DC input. Read `RAW_SIN`. The code is the packed raw bits 0..11 (code = sum of raw[i] x 2^i).
3. Write `W[i]` = 2^(i-10) for i = 12, 13 (that is 4 and 8) and 0 for i = 0..11. Read again. The code is raw[12] + 2 x raw[13].
4. Restore the reset weights after the capture. Repeat steps 1-4 for slice B with `RAW_COS`.

The ramp, the least-squares fit and the conversion to weights follow the `r1_adc` procedure:

1. Apply a coarse DC ramp over +/-0.995 of full scale, one conversion per LSB. Source F7. Reference DMM on the same nodes.
2. Find the input levels where decisions 0-4 change, and 6 levels each for decisions 5-8 (about 81 levels).
3. At each level apply a fine ramp of +/-12 LSB, 8 conversions per LSB (about 19 600 conversions per slice).
4. Fit the ramp position to [one offset per window, b0...b13] by least squares.
5. Scale the weights to sum 4095 LSB. Quantise to the unit of the register map (1/4 LSB). The `r1_adc` README
   proposes 1/8 LSB. The map says both fit. Use 1/4 LSB (O-05).
6. Load the weights. Write `CAL_CRC`. Check `CAL_VALID`.
7. Verify with a new ramp (test T17). Repeat the calibration at 25 C, -40 C and 125 C (T17 sample plan).

Each read through SPI takes about 2 frames. At 10 MHz `SCLK` one pair takes about 10 us. The 19 600 conversions
per slice take about 0.2 s per pass. This is acceptable. The input must be static during a read.

## 4. Tests

### 4.0 Conventions

1. Test id `Txx`. One row per test. A test can have several sub-runs (corners, samples).
2. *Gate* is the verification gate (V1-V8) or the parameter row of specification section 4.
3. *Limit* is the specification value and its class. The `sim` value is the simulated number of the same row.
   It is a prediction. A bench value outside the `sim` value but inside the limit is a **pass**, with a note.
4. Standard corners: temperature -40, 25, 125 C. Supply: nominal (1.2 V / 3.3 V), low (1.08 V / 3.0 V),
   high (1.32 V / 3.6 V). A test lists which corners it uses. Default is "25 C, nominal".
5. Sample tier: *all*, *3 dies*, *1 die*.
6. **Status** is *not run* for every test in this draft.

### 4.1 Power, supply and clock (parameter rows: Supplies, Power, Oscillator)

| Test | Gate / row | Applied | Measured | Instruments | Pins | Limit (class) | Sample | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T01 | Power | Nominal supplies, `EN` high, gates on at 5 % duty, encoder emulator running (1 Vpp, 100 kHz), no bus traffic | `I(VDD)`, `I(VDDA)`, `I(IOVDD)`; total power | F3, DMM 6.5-digit | 1, 3, 7 | about 17-21 mW; about 4.5 mA on `VDDA` (estimated). Block sums (simulated): VDDA 0.84-1.65 mA and VDD 0.45-2.29 mA for the ADC | all | not run |
| T02 | Supplies | `VDD` 1.08 / 1.2 / 1.32 V and `IOVDD`/`VDDA` 3.0 / 3.3 / 3.6 V, all nine combinations at 25 C. Repeat the corner pairs (low, low) and (high, high) at -40 and 125 C | Function check: `ID` read, T22 BiSS frame, T13 code at one DC point | F1, F2, F10 | 1, 3, 7, 16-19 | Works over 1.08-1.32 V and 3.0-3.6 V (specified) | 3 dies | not run |
| T03 | Supplies (power-up) | Ramp `VDD`/`IOVDD` at 0.1 ms, 1 ms and 10 ms. Orders: `VDD` first (rule), simultaneous and `IOVDD` first (documented experiment, as in G1, rule B1). `EN` low | Gate pad voltage during the ramps, `FAULT` and `STATUS` after the ramp, time to read `ID` | F5, F14 | 1, 3, 7, 12-15 | Gates <= 0.3 V in the rule order (assumed). Bandgap start-up <= 0.66 ms at a 1 ms ramp (simulated) | 3 dies | not run |
| T04 | Oscillator (trim) | Procedure B07 at 25 C, nominal. Then repeat at -40 and 125 C with the 25 C code | f_clk vs `OSC_TRIM` for all 32 codes (each code: `OSC_COUNT`) | F16 | 17 | 30.03 MHz at code 22 (simulated); steps 1.16-1.81 %; monotonic; untrimmed spread 23.3-38.9 MHz; reach 32.61 MHz at ss/1.08 V/125 C (all simulated) | all | not run |
| T05 | Oscillator (supply, temperature) | Sweep `VDD` 1.08-1.32 V at the 25 C trim code. Add 1 MHz ripple 20 mVpp on `VDD` | f_clk vs `VDD` | F1, F16 | 1, 17 | 117 ppm/mV; 373 ppm/mV at 1 MHz ripple (simulated) | 3 dies | not run |
| T06 | Oscillator (clock fault) | Write `OSC_WIN` for +/-7 %. Drive the reference 20 % off (that is, a 1.2 MHz reference counts as a fast clock) | `STATUS.CLK_FAULT`; `nW` bit in the BiSS frame | F16, F10 | 16-18 | `CLK_FAULT` = 1 when the count is outside the window or >= 4096; no `FAULT` bit latches (register map 4.3) | 3 dies | not run |
| T07 | Oscillator (jitter) | Run BiSS at 10 MHz `MA`; capture `SLO` edges over 1000 frames | Edge-to-edge jitter on the `SLO` timing relative to `MA` | F14 | 17, 18 | Jitter 103 ps white noise over 30 cycles against a 280 ps budget (simulated) | 1 die | not run |

### 4.2 Gate V1: analog front end

| Test | Gate / row | Applied | Measured | Instruments | Pins | Limit (class) | Sample | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T08 | V1 AFE | Gain steps x1 to x32 (`ANA_CTRL`, O-06). Differential 1 kHz sine at an input that gives about 80 % full scale at each gain. CM 1.65 V. 25 C, nominal | Amplitude ratio between steps from `AMPLITUDE` (0x1C) or from the code-density amplitude | F6, F7, DMM | 21-24 | Gain step error <= 1.70 % (rev C) to 1.87 % (rev B), revision E number is not in the table (simulated) | all | not run |
| T09 | V1 AFE | Input differential amplitude 40 mVpp to 1.4 Vpp at the gain that makes the output fit; CM 0.5-2.8 V while each pin stays inside 0.5-2.8 V (the sweep points are in the result file) | Code error, `AMP_LOW`/`AMP_HIGH` flags, CM output (indirect) | F6, F7 | 21-24 | Input range 40 mVpp-1.4 Vpp differential, CM 0.5-2.8 V (specified). Output CM 0.594-0.597 V (simulated, rev D; not directly observable) | 3 dies | not run |
| T10 | V1 AFE | Short the inputs through 50 ohm. Gains x1 and x32. Read 100 000 codes over `RAW_SIN`/`RAW_COS` | RMS code noise, referred to the input | DMM, host | 21-24 | Noise 0.35 LSB at x1; 31.0 µV at x32 at ss (limit 35 µV) (simulated) | all | not run |
| T11 | V1 AFE | Sine on `SIN` and `COS` from 10 kHz to the highest frequency the ADC pair rate resolves (about 600 kHz). Same amplitude on both. Gain x1 | Amplitude ratio SIN/COS vs frequency. Phase difference vs frequency | F6, `AMPLITUDE`, TEST_POS (see O-07) | 21-24 | Pole matching <= 1 % (simulated 0.976 %, rev E); f_c >= 1 MHz is beyond the ADC Nyquist limit and not observable directly (O-07) | 3 dies | not run |
| T12 | V1 AFE | Sine 100 kHz at 1.4 Vpp, gain x1, CM 1.65 V. Capture 1 000 000 codes with a coherent or a histogram method (O-04) | THD / harmonic content from the code-density test, or the 3rd harmonic from position error (T23, T24) | F6 | 21-24 | THD <= 0.032 % (rev C, simulated), 0.025 % (rev D) | 3 dies | not run |
| T13 | V1 AFE (PSRR) | Add 100 mVpp ripple on `VDDA` at 1 kHz, 10 kHz and 100 kHz. Encoder inputs static at mid code | Code spread vs ripple frequency; input-referred ripple | F2, F6 | 3, 7, 21-24 | PSRR >= 54.3 dB (simulated, rev D) | 3 dies | not run |
| T14 | V1 (pad leakage) | DC 0, 0.5, 1.65, 2.8 and 3.0 V on each of the four encoder pins in turn, other inputs at 1.65 V. Read the pin current with an SMU (1 nA range) at 25 C and 125 C. Then repeat for the `ISA`/`ISB` pins over -0.3 to +0.2 V | Leakage current per pin vs voltage | SMU | 8-11, 21-24 | No limit set in the specification. The bench records the current to decide the 5 V head rule (open item 4 of the spec). Pin voltage stays within 0.5-2.8 V for supported heads | 3 dies | not run |

### 4.3 Gate V2: ADC and reference

| Test | Gate / row | Applied | Measured | Instruments | Pins | Limit (class) | Sample | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T15 | V2 ADC (static, before calibration) | Slow differential ramp on `SIN`/`COS` over +/-0.995 of full scale at AFE gain x1, in 1 LSB steps. Reset weights loaded. Slice A and slice B | Code vs DMM-measured input. INL, DNL, missing codes, offset, gain | F7, DMM 6.5-digit, host | 21-24 | Reference: weight correction needed (D12). Mismatch model without correction fails on 12/50 samples (missing codes) (simulated). Full scale +/-0.914 V (simulated) | all | not run |
| T16 | V2 ADC (weight calibration) | Procedure of section 3.1, 25 C | The 14 weights per slice; residual DNL and INL after loading | as T15 | 21-24 | DNL <= 0.5 LSB after calibration (model, 50/50 MC samples, simulated); INL +/-1.3 LSB (rev 2, simulated) | all | not run |
| T17 | V2 ADC (static, after calibration) | Repeat T15 with the T16 weights. Then repeat at -40 C and 125 C **without** a new calibration, then **with** one | INL, DNL, missing codes, gain drift | as T15, F13 | 21-24 | No missing codes (specified need). Gain drift of the AFE linear part up to about 0.4 LSB over temperature (INTERFACES) | 3 dies at 3 temperatures | not run |
| T18 | V2 ADC (dynamic) | Sine at 10 kHz, 100 kHz and 250 kHz, about 0.9 of full scale. Code-density histogram of 10^7 conversions, or a coherent capture if O-04 allows it | SNDR / ENOB, SFDR | F6, host | 21-24 | ENOB >= 11.5 at 2 MSPS (specified); 63.0 dB SNDR tt N 256 in rev 4; 70.9 dB in rev 3 (simulated). Both are below 11.5 bit (about 71 dB); the bench decides (O-08) | 3 dies | not run |
| T19 | V2 ADC (skew) | The same sine (100 kHz, 250 kHz) on `SIN` and `COS` (both inputs tied to one source through matched paths). Read the phase between the two codes | Skew between the two track-and-holds | F6, host | 21-24 | Skew < 0.5 ns (specified); sigma 7.6 ps (rev 1, simulated) | 3 dies | not run |
| T20 | V2 ADC (noise) | Input shorted, AFE x1. 100 000 conversions per slice | RMS code noise; comparator noise is not separable (O-09) | host | 21-24 | Comparator noise <= 60 uV rms (specified, D14); 55.9 uV ss, 57.5 uV tt (simulated) | all | not run |
| T21 | V2 ADC (reference buffer) | Step of 0.5 full scale between two conversions (DC step through the AFE, 1 conversion apart, if the source allows), or read the decision-5 INL signature of T15 | Code error right after a large input step | F6, host | 21-24 | Settling to 0.25 LSB (specified); rev 4: 0.71-0.86 LSB (simulated, fails) | 3 dies | not run |
| T22 | V2 ADC (current channels) | Static ramp on `ISA`/`ISB` +/-100 mV through the isense amplifier. Gate off. After the `az_win` window | Code vs input. Gain, offset, INL | F8, DMM | 8-11 | Isense gain 14; output +/-0.85 V at 0.57 V CM with a 40.38 mV pedestal (INTERFACES, simulated). Input <= 100 mV (specified) | all | not run |

### 4.4 Gate V3: position

| Test | Gate / row | Applied | Measured | Instruments | Pins | Limit (class) | Sample | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T23 | V3 position (raw, before calibration) | Emulator at 1 Vpp, 1 kHz. Head errors off. Read `POS` (0x19) and `MEAS_ANGLE` (0x1F) with a stop of the AWG at 4096 phases over one period (AWG in arbitrary-sample step mode, one SPI read per step) | Angle error vs AWG phase (peak-to-peak, RMS) | F6, host | 16-19, 21-24 | RTL against a float reference: <= 0.024 deg el (simulated). Angle resolution 16 bit (specified) | all | not run |
| T24 | V3 position (head errors) | Head errors from F6: offset 6.5 %, gain 1.25, phase 10 deg, h3 1 %. Run before and after the calibration words are loaded (`OFS_*`, `GAIN`, `PH_SIN`, `PH_ICOS`, `H3`). The host fits the words from a 4096-point scan (Heydemann form) | Angle error before and after | F6, host | 16-19, 21-24 | After calibration: RTL 0.051 deg el, 0.17 deg el with a constant (simulated); <= +/-0.25 deg el electronic (estimated); +/-0.64 deg el total on a 32-pole ring (target) | 3 dies | not run |
| T25 | V3 position (latency) | `MA` with the BiSS frame at 1 MHz. Emulator at 100 kHz. Scope on `MA` (LAT edge) and on a marker output of the AWG (phase zero) | Delay between the LAT edge and the phase of `POS` read in the frame; with `EXTRAP` = 0 and with a set value | F6, F14 | 17, 18, 21-24 | Fixed, published value (specified); latch spread 0.61 deg el with `LAT_HALF` = 1, 1.18 deg el without (simulated, 100 kHz el) | 3 dies | not run |
| T26 | V3 position (velocity) | Emulator frequency 1, 10, 50, 100, 250 kHz. Read `VELOCITY` and `POS` in BiSS frames | Velocity code vs frequency; position error vs frequency | F6, F10 | 16-19, 21-24 | Full accuracy <= 100 kHz; count-safe at 250 kHz up to 1.6e9 Hz/s acceleration (simulated). 1 unit of `VELOCITY` = 14.3 Hz el at 30 MHz | 3 dies | not run |
| T27 | V3 position (count) | Emulator sweeps from 0 to 250 kHz at a fixed acceleration (steps of 1e8, 1e9, 1.6e9 Hz/s), 10^5 electrical turns. Compare `TURNS` with the AWG cycle count | Lost counts | F6, host | 16-19, 21-24 | No count loss at 250 kHz with the 44-tick gap (simulated) | 3 dies | not run |
| T28 | V3 position (amplitude) | Reduce the input to 10 %, then remove one channel | `AMPLITUDE`, `STATUS.AMP_LOW`, `nE` bit; `FAULT` bit 5 | F6, F10 | 21-24, 12 | `AMP_LIM` (0x7C08 reset) sets the thresholds; the specification gives no value (O-10) | 3 dies | not run |

### 4.5 Gate V4: bus

| Test | Gate / row | Applied | Measured | Instruments | Pins | Limit (class) | Sample | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T29 | V4 BiSS-C | `MA` 80 kHz, 1 MHz and 10 MHz. 10^6 frames at each. Position from T23 as data | CRC-6 pass rate, `ACK` timing, t_busy, data vs `POS` read through SPI | F10, F14, logic analyzer | 16-18 | CRC-6 poly 0x43 inverted. t_busy = 2 T_MA up to 1 MHz, 2-6 T_MA above (simulated). D2 table 10: t_busy >= 2 T_MA and <= 40 us | all | not run |
| T30 | V4 BiSS-C (timeout) | Stop `MA` after a frame; measure the time from the last edge until `SLO` goes high. At -40, 25, 125 C, with the B07 trim | Timeout | F14 | 17, 18 | 20 us nominal, 14-26 us over the RC spread (specified). D2 range 12.5-40 us | 3 dies | not run |
| T31 | V4 BiSS-C (abort) | Abort a frame at each bit position (stop the clock, then restart after less than and after more than the timeout). Send a frame while `CS_N` is low | `SLO` state; next frame correct; no hang | F10, F14 | 16-18 | Slave re-arms after a timeout (map 1) | 3 dies | not run |
| T32 | V4 BiSS-C (control channel) | Read 0x41, 0x42-0x43, 0x44-0x47, 0x78-0x7F with sequential read. Send a header with a wrong CRC, a write, a read of an unmapped address and of 0x40 | Bytes; `DIAG_BISS.CC_ERR`; `W` inverted on refusal | F10 | 16-18 | Values in map section 4.9. `BP_ID` 0x0001 is a placeholder (O-11); `MFR_ID` 0x0000 (spec open item 5). Refusals per map 3.3 | all | not run |
| T33 | V4 SSI | `BUS_CFG.SSI` = 1. Gray and binary. `MA` 100 kHz, 1 MHz, 2 MHz. Position set by `TEST_POS` | Word vs `TEST_POS`; monoflop time | F10, F14 | 16-18 | Monoflop 15-25 us (specified); clock <= 2 MHz | all | not run |
| T34 | V4 SPI | 10^6 register read/write frames at 1, 5 and 10 MHz `SCLK`. Wrong frame lengths (23, 25 clocks) | Read-back, `DIAG_SPI.SPI_ERR`, `STATUS` byte on `SDO` | F10 | 16, 17, 19, 18 | Frame is 24 bits; other lengths are ignored and counted. No `SCLK` limit in the frame (map 2.3); `CS_N` high >= 8 ticks | all | not run |
| T35 | V4 interop | Three independent BiSS masters (for example a commercial controller, an open-source FPGA master, and the fixture master) read the same die. Line length 1 m and 10 m with the RS-422 transceiver | Frame errors per 10^6 frames per master | three masters, F14 | 16-18 | Interop against >= 3 independent masters (gate V4). The masters are not chosen (O-12) | 1 die | not run |
| T36 | Calibration storage | Corrupt one bit in each covered word group (0x10-0x17, 0x36-0x3C, 0x50-0x5D, 0x60-0x6D) by a host write. Then correct it | `CAL_VALID`, `FAULT` bit 11, `nW` bit, gate state | host, F12 | 12, 16-19 | `CAL_VALID` clears after any write to a covered word; recovered after `CAL_CRC` rewrite and `CLR`; check completes in <= 172 ticks plus 2 per SPI frame (simulated) | 3 dies | not run |

### 4.6 Gate V5: current sense, safety and gate (parametric part)

| Test | Gate / row | Applied | Measured | Instruments | Pins | Limit (class) | Sample | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T37 | V5 current sense (static) | Differential DC at `ISA` and `ISB`: -100, -50, 0, +50, +100 mV, gates off, and with 5 % PWM on. Read `I_A`, `I_B` (0x29, 0x2A) and set `I_ZERO` | Gain, offset, INL, offset after auto-zero (50 samples if Monte-Carlo comparison is wanted) | F8, DMM | 8-11 | Input <= 100 mV (specified). Residual offset sigma 16.2 uV, worst 35.5 uV (simulated MC) | all | not run |
| T38 | V5 current sense (settling) | Step 0 to +100 mV at the isense input, edge <= 10 ns, at a defined point in the PWM period. Read the code after k ticks by moving the strobe, or observe the comparator flag on the fault path (S04) | Settling time to 0.5 % | F8, F14 | 8-11 | < 300 ns after the PWM edge (specified target); 102 ns tt, 205-206 ns ss (simulated) | 3 dies | not run |
| T39 | V5 current sense (comparator thresholds) | After B10. Ramp the shunt voltage slowly (0.1 LSB steps) up and down at `THR_OC` / `THR_NEG` codes 8, 14, 32, 56. Observe the `FAULT` bit 0-3 and `FAULT_N` | Trip level, release level, hysteresis, repeat | F8, DMM, F12 | 8-11, 12 | Hysteresis 1.56-2.79 calibration steps (simulated); calibration residual <= 0.089 LSB (simulated); threshold error target 0.25 LSB (r1_safe); threshold DAC step = LSB/8 | all | not run |
| T40 | V5 comparator calibration | Run B10 at -40, 25, 125 C. Compare `k_cal` against the trip levels from T39 | Code repeat; threshold error after calibration | host, F8 | 8-11 | Search matches the `r1_safe` model on 274/274 samples (simulated RTL); `EXH` = 0 | all | not run |
| T41 | V5 I2T | Constant shunt voltage (about 30, 50, 70 % of the trip level) for 10 s to 100 s. `I2T_CFG` `TAU_SHIFT`, `PRESCALE` set. Read `I2T_A/B` (0x30, 0x31) and the `FAULT` bits 9, 10 | `E` vs time; time to trip vs level | F8, host | 8-11 | E[23:8] approaches i^2 with a time constant of 2^TAU_SHIFT updates (map 4.7). Trip when E[23:8] >= `I2T_LIM`. No numeric limit in the specification | 3 dies | not run |
| T42 | V5 over-temperature | Chamber -40 to +125 C in 15 C steps. Read `TEMP` (0x2B). Set `OT_LIM` between two readings | `TEMP` count vs thermocouple temperature; trip temperature | F13, host | none (internal) | No count-to-temperature limit exists. G1 `g1_t2f` lineage. Output is a frequency count; calibration is a bench result | all | not run |
| T43 | Gate drive (PWM) | `PWM_PERIOD` 1000-8191 ticks; `DUTY`, `PHASE` for three channels; `DEAD` 1, 15 and 255 ticks. 1 nF per output | Edge times, dead time (both ends of each on-window), period, duty, phase | F14, F9 | 13-15 | Dead time programmable 50 ns-2 us (specified); 15 ticks = 500 ns at 30 MHz (map). `GATE_x` is on while `DEAD <= (cnt - PHASE) mod PERIOD < DUTY - DEAD` | all | not run |
| T44 | Gate drive (load) | Levels at `GATE_A/B/C` with 1 nF and with 10 pF. Static high level and rise/fall time at 3.0 / 3.3 / 3.6 V | `V_OH`, `V_OL`, t_r, t_f | F14 | 13-15 | 30 mA pad class (`sg13g2_IOPadOut30mA`); no numeric limit set (O-13) | 3 dies | not run |
| T45 | Current sample strobe | Display `GATE_A` and the sample instant. The strobe is internal. Use a known current step that arrives before and after the centre of channel A; read `I_A` | Sample instant (centre of channel A: `PHASE_A + DUTY_A/2`); `LATE` counter (0x35) | F8, F14 | 8-11, 13 | Strobe at the centre of the A on-window (map 4.6); `LATE` stays 0 for the reset `SCHED` | 3 dies | not run |

### 4.7 Mapping of the gates

| Gate | Tests | Bench part |
| --- | --- | --- |
| V1 AFE | T08-T14 | gain steps, CM range, noise, AA matching, pad diode leakage over CM |
| V2 ADC | T15-T22 | static ramp, dynamic, skew, reference buffer load, MC (die-to-die statistics over the sample) |
| V3 position | T23-T28 | accuracy before and after calibration, latency, extrapolation |
| V4 bus | T29-T36 | protocol, corners, aborted frame, control channel, SSI, interop |
| V5 current and safety | T37-T45, S01-S13 (section 5) | settling, comparator thresholds, I2T, EN/STO path, fault latch, gates low |
| V6 digital | none | not applicable on the bench (section 4.9) |
| V7 chip | none | not applicable on the bench (section 4.9) |
| V8 bench | T46 and T47 (section 4.8) | encoder head on a motor, BiSS master, shunt fixture, thermal chamber |

### 4.8 Gate V8: system test

| Test | Gate / row | Applied | Measured | Instruments | Pins | Limit (class) | Sample | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T46 | V8 bench (encoder head) | Encoder head on the motor shaft (F17). Motor turned by a drive at 10, 100, 1000 rpm (electrical frequency from the pole count). Shaft reference encoder at the same shaft. Read BiSS frames | Position error vs the reference encoder over 10 turns; `AMPLITUDE` | F17, F10 | 16-18, 21-24 | +/-0.64 deg el total on a 32-pole ring (target); +/-0.25 deg el electronic (estimated) | 1 die | not run |
| T47 | V8 bench (current loop) | Three external low-side FETs driven by `GATE_A/B/C` at the motor, current limited. Shunts on two phases. Read `I_A`, `I_B` (third phase computed by the host). Compare with a clamp or an inline reference | Current error vs reference; settling after PWM edge in the real circuit | F17, F14 | 8-15 | No numeric limit set in the specification for the system. Record only (O-14) | 1 die | not run |

The plan has 47 tests (T01-T47), 13 safety tests (S01-S13) and 14 bring-up steps (B01-B14). S13 is an experiment, not a pass/fail test.

### 4.9 Gates that are not bench gates

1. **V6 digital** (synthesis, LibreLane, STA, GLS, formal equivalence): not applicable on the bench.
   The bench gives indirect evidence: T02 (supply corners), T04 (clock corners), T29-T34 (bus), T36 (CRC).
   A failed STA path would show as a protocol error at the fast clock (ff, 1.32 V, -40 C). T04 reports the fast-clock case.
2. **V7 chip** (DRC, LVS, PEX, full-chip co-simulation): not applicable on the bench.
   The bench compares silicon with the co-simulation where the co-simulation exists. The comparison is a task for the V7 owner.

## 5. Safety tests

Run S01-S12 with 1 nF on each `GATE` output, nominal supply, 25 C, and then at -40 and 125 C
(3 dies). Use the 10 ns step source F8 and the EN switch F11. The oscilloscope has `ISx` differential (two probes
or a differential probe), `GATE_A`, `FAULT_N` and the `EN` trigger. A host GPIO marks the start.

| Test | What | Applied | Measured | Limit (class) | Pins | Status |
| --- | --- | --- | --- | --- | --- | --- |
| S01 | `EN`/`STO_IN` to gates | PWM running at 50 % duty on all three channels. `EN` falls from high to low (edge <= 5 ns). | Time from the `EN` 50 % point to each `GATE_x` below 1 V (all three, 100 captures per die) | Fault path <= 200 ns at <= 1 nF and <= 1 us at 5 nF (specified, from T7 results). Simulated 443-933 ns over corners for the `gate_en` path: the 200 ns requirement and the simulation disagree (O-15) | 20, 13-15 | not run |
| S02 | `EN` latch | After S01 read `FAULT` (bit 8 STO), `STATUS.FAULT`, `FAULT_N` | `FAULT_N` low; bit 8 set. `EN` back high: the fault remains | The fault latches (spec section 2, `r1_safe`). Bit 8 cannot be masked (map 4.1) | 20, 12 | not run |
| S03 | STO with the bus at work | Run a BiSS frame train at 1 MHz while `EN` falls. | BiSS frames after the event; `nW` bit | `nW` = 0 when `FAULT` is set (map 3.1) | 20, 16-18 | not run |
| S04 | Overcurrent chain, time | Gates on at 50 % duty. Step on `ISA` from 0 to a level 20 % above the `THR_OC_A` trip level (after calibration), edge <= 10 ns. Trigger on the step. Repeat for `NEG_A`, `OC_B`, `NEG_B` (negative step for `NEG`) | Delay from the input crossing the threshold to `GATE_x` below 1 V; split in two parts: step to `FAULT_N` falls (comparator + ctrl), and `FAULT_N` to `GATE_x` | Comparator flag <= 236 ns after the threshold (simulated, revision 3 full-path MC); ctrl 4 ticks (about 133 ns at 30 MHz) with `CMP_FILT` = 0; gate pad fall < 1 us at <= 1 nF and about 1.2 us at 5 nF (simulated). Sum of the parts: about 0.4-1.4 us | 8-11, 12, 13-15 | not run |
| S05 | Overcurrent: overdrive | Repeat S04 at 1.05, 1.2, 2 and 5 times the threshold | Delay vs overdrive | Delay at small overdrive vs the 32-tick probe time: not run in simulation (INTERFACES) | 8-11, 13-15 | not run |
| S06 | Filter | Set `I2T_CFG.CMP_FILT` = 0, 1, 4. Apply a pulse on `ISA` of 50 ns, 100 ns, 500 ns above threshold | Trip or no trip; added delay | Flag must stay high for `CMP_FILT` + 1 ticks (map 4.7) | 8-11, 12 | not run |
| S07 | Latch | After S04, remove the overcurrent. Check `FAULT_N`, gates. Gates must stay low | `FAULT_N` and gate state for 1 s | Fault latches until cleared (spec section 2) | 8-15 | not run |
| S08 | Clear | `CTRL.CLR` with the source active and again with it inactive. `CTRL.GATE_EN` write. | `FAULT` after each; `GATE_ACTIVE` | `CLR` clears each bit whose source is inactive. Bit 11 stays while `CAL_VALID` = 0. Gates stay off until `GATE_EN` after reset (map 4.1) | 12, 16-19 | not run |
| S09 | Mask | `FAULT_MASK` bits 0-7, 9, 10 set. Apply the cause. Try bits 8, 11, 12 | Whether `FAULT_N` falls | Bits 8, 11, 12 cannot be masked (map 4.1) | 8-12, 20 | not run |
| S10 | Watchdog | `CTRL.WDT_EN` = 1, `WDT_PERIOD` = 100 (units of 1024 ticks). Stop all bus traffic. Then send a frame every 0.8 and 1.2 periods | Time to `FAULT` bit 7; `FAULT_N`; gates | Kicked by every BiSS/SSI frame end and every well-formed SPI frame (map 4.7). The period unit is 1024 ticks (about 34 us at 30 MHz). An ill-formed frame must not kick (O-16) | 16-19, 12 | not run |
| S11 | Overspeed and amplitude | Raise the emulator frequency above `OVS_LIM`. Remove one channel | `FAULT` bits 5, 6 and the gate state | Reset `OVS_LIM` 0x4000; no numeric limit in the specification | 21-24, 12-15 | not run |
| S12 | Power-up and brown-out | Lower `VDD` to 0.9 V for 10 us, then restore. Then lower `IOVDD` to 2.5 V for 10 us. `EN` high, gates on | Gate state, `FAULT`, `POR` bit, register content | No brown-out detector is specified (O-17). Record the response; apply the G1 B7/B11 supervisor rule on the board | 1, 3, 7, 13-15 | not run |
| S13 | Gate load experiment (not supported) | Repeat S01 and S04 with 5 nF per gate output. Run with 3 dies at 25 C only. Record this as an experiment | Fall time of `GATE_x`; fault-path delay | **Not supported** by the specification. Simulated fall about 1.2 us and fault path <= 1 us at 5 nF (simulated). Pass or fail is not declared; the data are for the record | 13-15, 20 | not run |

Safety rule: do not claim a safety function from this plan. The chip has no safety certification.
The tests only measure timing and state.

## 6. Data record format and folder layout

### 6.1 Folder layout

```
measurement/
  README.md                          this plan
  fixture/                           schematics, BOM, firmware for the fixture (to be created)
  results/
    <die_id>/                        one folder per die, id like R1-L1-D007
      <test_id>/                     B01..B14, T01..T47, S01..S13
        <run_id>.json                one JSON per die per test per run
        raw/                         small raw files (CSV, <= 1 MB)
    index.json                       list of all runs with the result and the status
    bulk/                            not in git: large raw data (scope captures, 10^7-code histograms)
```

Large files stay out of git. They sit in the bulk results root. The record points to them with a
path **relative to that root**, with a SHA-256. No machine-specific absolute path goes into a record.

### 6.2 Run id

`<test_id>-<YYYYMMDD>-<nn>`, for example `T04-20270312-01`. Aborted and out-of-range runs keep their record.
A repeat does not replace an earlier run.

### 6.3 JSON fields

```json
{
  "schema": "r1-meas-0.1",
  "run_id": "T04-20270312-01",
  "test_id": "T04",
  "die_id": "R1-L1-D007",
  "lot": "L1",
  "package": "QFN24",
  "fixture": {"type": "socket", "revision": "A", "board_id": "..."},
  "design": {"id_register": "0x5204", "gds_sha256": "...", "pdk_commit": "..."},
  "temperature_c": {"setpoint": 25.0, "package_tc": 25.3, "board_tc": 24.8},
  "supply": {"vdd_v": 1.2, "iovdd_vdda_v": 3.3, "i_vdd_a": 0.0, "i_vdda_a": 0.0, "i_iovdd_a": 0.0},
  "instruments": [{"role": "oscilloscope", "model": "...", "serial": "...", "cal_date": "YYYY-MM-DD", "range": "...", "bandwidth_hz": 0}],
  "stimulus": {"description": "...", "parameters": {}},
  "software": {"host_sw": "git sha", "analysis_sw": "git sha"},
  "registers_written": [{"addr": "0x08", "value": "0x0016", "readback": "0x0016"}],
  "raw_data": {"path": "relative/path", "sha256": "..."},
  "measured": {"name": "...", "value": 0.0, "unit": "...", "uncertainty": 0.0, "n": 1},
  "limit": {"value": "...", "class": "specified|estimated|simulated", "source": "spec row"},
  "result": "passed|failed|not run|not applicable",
  "notes": "..."
}
```

Rules:

1. `result` takes one of four values: passed, failed, not run, not applicable. No other word.
2. A measured number names the instrument and the sample (die id). A simulated number is labelled simulated.
3. The record gives the actual rail voltages and the package and board temperatures, not only the set points.
4. Each campaign has a run sheet (revisioned) that lists the fixture revision, connection diagram, current limits,
   calibration files and script versions. The run sheet is a file in `results/<die_id>/`.
5. `index.json` is regenerated by a script from the run files. It is never edited by hand.
6. Do not put customer, partner or private contact data in a record.

## 7. Open items

The bench must decide or measure these. Each item names the specification (or map) row that leaves it unknown.

| # | Open item | Source row | Bench action |
| --- | --- | --- | --- |
| O-01 | Number of packaged dies is not set (this plan assumes 10). | Spec: no row. G1 had the same open item | Set N before the order; tier the tests as in section 4 |
| O-02 | Power-up sequence for R1 is not specified. This plan uses the G1 rule (`VDD` first). | Spec section 4, Supplies | T03 measures the three orders; the result sets the board rule |
| O-03 | SPI re-framing hazard (G1 finding): R1 has no stated maximum SCLK-low time inside a frame, and no rule for back-to-back frames on safety registers. | Map 2.3, 4.12 | T34 finds the limit; the host adds read-back until it is known |
| O-04 | Raw decisions are not readable; no capture buffer exists; codes come by SPI/BiSS reads at random sample times. This blocks the ramp procedure as written, and coherent FFT tests. This plan proposes the one-hot-weight read (section 3.1) for the raw bits and a code-density histogram for dynamic tests. Neither is simulated. | Map 4.5, 4.11; `r1_adc` README, bench procedure | Run the one-hot read on RTL before silicon; run T18 with histograms; consider `TEST_POS` as a timing aid |
| O-05 | Weight unit: the map says 1/4 LSB, the `r1_adc` bench procedure says 1/8 LSB. | Map 4.11 | Use 1/4 LSB; confirm with `r1_adc` revision 4 or later |
| O-06 | `ANA_CTRL` (0x0C) bit assignment is open, so the PGA gain steps x1-x32 have no register address. | Map 4.8 | T08 cannot run until the bits are defined |
| O-07 | f_c >= 1 MHz and pole matching are not directly observable: the encoder pair rate is one pair per 22 ticks (about 1.36 MS/s), so the Nyquist limit is about 0.68 MHz. | Spec section 4, AFE rows | T11 measures the pass-band response to about 600 kHz and extrapolates; or probe an internal node (no pin exists) |
| O-08 | ADC row asks for ENOB >= 11.5 at 2 MSPS. D18 sets a 22-tick frame (1.36 MS/s per pair). Simulated SNDR is 63.0 dB (rev 4, N 256) and 70.9 dB (rev 3). 11.5 bit needs about 71 dB. | Spec section 4, ADC | T18 reports ENOB at the real rate; the bench decides the limit |
| O-09 | Comparator noise (60 uV) is not directly measurable; only code noise at the output. | Spec section 4, ADC | T20 reports code noise; derive an upper bound for the comparator noise |
| O-10 | `AMP_LIM` window and the amplitude fault levels have no specified value. | Spec section 2 (`r1_safe`), map 4.5 | T28 and S11 measure the thresholds; the bench proposes values |
| O-11 | `BP_ID` is a placeholder (0x0001) and `MFR_ID` is 0x0000. | Map 3.4, spec open item 5 | T32 records what the masters accept; interop masters may reject the ID |
| O-12 | Choice of three interop masters, the encoder head, the motor and the driver stage. | Spec section 5, V4 and V8 | Select before T35, T46, T47. Part numbers go into `fixture/` |
| O-13 | The gate pad has no stated V_OH, V_OL, rise and fall limits for 1 nF. | Spec section 4, Gate drive | T44 measures them; the bench proposes limits |
| O-14 | The system current-loop accuracy has no limit. | Spec section 4, Current sense | T47 records the error; the owner sets a limit |
| O-15 | Closed by D19 (2026-10-21): the requirement is <= 1 us at direct loads <= 1 nF; 5 nF is not a supported direct load and is measured as a documented experiment only. | Spec section 4, Gate drive | S01 measures; the result decides the final number |
| O-16 | Whether an ill-formed SPI/BiSS frame kicks the watchdog is not stated for BiSS frames with a CRC error. | Map 4.7 | S10 tests both cases |
| O-17 | No on-chip brown-out detector is specified. | Spec section 3 (no row) | S12 records the response; board supervisor per G1 B7/B11 |
| O-18 | Encoder CM at the default test point. The user plan default of 0.5 V CM with 1 Vpp differential puts the negative pin at 0.25 V, which is outside the supported pin range 0.5-2.8 V. | Spec section 6, open item 4 | This plan uses 1.65 V as the default CM; 0.5 V CM is allowed only up to 0.5 Vpp differential |
| O-19 | The temperature-to-count relation of `TEMP` has no specified slope or limit. | Spec section 4: no row | T42 measures it; the host builds a conversion |
| O-20 | Boundary of the unsupported 5 nF gate load: no limit is set. | Spec section 4, Gate drive | S13 records data without a pass or fail |
| O-21 | The build is not fixed: the chip of record, GDS hash and PDK commit are not set. Records name them when they exist. | Spec section 4, Process | Fill `design.gds_sha256` and `design.pdk_commit` at receipt of the dies |

## Built against

| Item | Version | How established |
| --- | --- | --- |
| Specification | `R1_TOP_LEVEL_SPECIFICATION.md` draft 0.1 | read 2026-10-21 |
| Register map | draft 0.4, `ID` 0x5204 | read 2026-10-21 |
| Pad map | 1600 um ring, revision b (`ring-20261021-b`) | `../padframe/README.md` |
| Silicon | none | not run |
| Instruments | none selected | not run |

# R1 bus protocols and register map (draft 0.1, 2026-10-20)

Owner block: `r1_ctrl` (`designs/r1-joint/blocks/r1_ctrl`). This document is the contract between
the host, the digital macro (`rtl/r1_ctrl_top.v`) and the analog blocks it connects to. It is a
draft: nothing here is on silicon. The RTL in `rtl/` implements this version. Items marked
**[verify]** are interpretations of the BiSS C Rev D2 document that the protocol testbench cannot
confirm, because it uses our own master model. They need the interop runs of gate V4.

All times are in ticks of the internal oscillator `r1_osc` (`clk`, 30 MHz nominal, untrimmed
spread about −30 % / +40 % per S5). The host measures the real frequency with `OSC_COUNT`
(section 4.3) and scales its settings.

## 1. Pads and modes

| Pad | Signal | Direction | Function |
| --- | --- | --- | --- |
| 16 | `CS_N` | in | high: BiSS-C or SSI on pads 17/18; low: SPI |
| 17 | `MA` / `SCLK` | in | BiSS/SSI clock (idle high) or SPI clock (idle low) |
| 18 | `SLO` / `SDO` | out | BiSS/SSI data or SPI data |
| 19 | `SDI` | in | SPI data in |
| 20 | `EN` / `STO_IN` | in | low: gates low at once (combinational), STO fault latched |
| 12 | `FAULT_N` | out | low while any `FAULT` bit is set |
| 13–15 | `GATE_A/B/C` | out | low-side gate outputs |

Mode switch on the shared pads (D7). Do these steps in this sequence:

1. Finish or abandon the BiSS/SSI frame, then wait until `SLO` is high (the timeout has ended).
2. Drive `SCLK` low.
3. Drive `CS_N` low. The BiSS/SSI logic is now held in reset.
4. Send the SPI frames. Keep `CS_N` high for at least 8 ticks (≤ 400 ns) between frames.
5. Drive `CS_N` high, then drive `MA` high.
6. Wait for one timeout (`TIMEOUT_TICKS`). The BiSS/SSI logic then arms and accepts the next frame.

The rising `MA` edge in step 5 does not start a frame: a frame starts only with a falling edge
after the slave has armed.

## 2. SPI

### 2.1 Native frames (`BUS_CFG.AS_MODE` = 0): mode 0, 24 bits

SPI mode 0: `SCLK` idles low, `SDI` is sampled on the rising edge, `SDO` changes on the falling
edge. Bits are MSB first.

```
SDI   R/nW A6..A0  D15 .. D0          R/nW = 0: write D to register A; 1: read register A
SDO   S7 .. S0     RD15 .. RD0        S = STATUS[7:0]; RD = result of the previous frame
```

The read data come one frame later (pipelined). `RD` holds the register value after a read
command, and the written value after a write command. A single read takes two frames; the
second frame can be the next read. A frame that does not have exactly 24 clocks is ignored: it
increments `DIAG_SPI.SPI_ERR`, and the next frame returns `S`, 0x0000.

### 2.2 AS5047P-compatible frames (`AS_MODE` = 1): mode 1, 16 bits

`SCLK` idles low; `SDI` is sampled on the falling edge; `SDO` changes on the rising edge.
Command: `PARC, R/W (1 = read), ADDR[13:0]`. Response in the next frame: `PARD, EF, DATA[13:0]`.
Parity is even over the 16 bits.

| ADDR | Name | DATA |
| --- | --- | --- |
| 0x3FFF | ANGLECOM | `POS[15:2]` (14 bit, extrapolated, after zero and direction) |
| 0x3FFE | ANGLEUNC | same as ANGLECOM (R1 has no separate uncompensated angle) |
| 0x3FFD | MAG | `AMPLITUDE` × 4 |
| 0x3FFC | DIAAGC | bit 11 MAGL (= `AMP_LOW`), bit 10 MAGH (= `AMP_HIGH`) |
| 0x0001 | ERRFL | bit 2 PARERR, bit 0 FRERR; a read clears it |
| 0x0000 | NOP | 0 |

`EF` = 1 in the response that follows a frame with a parity or length error. Writes are not
supported: the data frame that follows a write command is ignored. To return to native mode,
send one 24-bit native write frame (mode 1 timing) that clears `AS_MODE`.

### 2.3 Clock-domain rules

The SPI shift logic runs on `SCLK`. Its flip-flops update only while `CS_N` is low. The register
file decodes the frame 2–4 ticks after `CS_N` rises and prepares the next `SDO` word. There is no
limit on `f_SCLK` relative to `f_clk` inside a frame; the `CS_N` high time must be ≥ 8 ticks.

## 3. BiSS-C and SSI

### 3.1 BiSS-C frame (point-to-point sensor slave, Rev D2)

| Step | MA edge | SLO |
| --- | --- | --- |
| idle | — | 1 |
| frame start | falling edge after the slave has armed | 1 |
| LAT | first rising edge | 1 (position latch request to the clk domain) |
| ACK | second rising edge | 0 |
| busy | following rising edges | 0 until the latch handshake is complete |
| START | first rising edge after the handshake | 1 |
| CDS | next | control data bit (section 3.3) |
| data | next n | `[MT 16] ST (ST_LEN bits) nE nW`, MSB first |
| CRC | next 6 | CRC-6, polynomial 0x43, start 0, over data + nE + nW, sent inverted |
| stop | following rising edges | 0 |
| timeout | MA quiet for `TIMEOUT_TICKS` | 0, then 1 (slave ready) |

- t_busy (LAT to START) is 2 T_MA when the latch handshake ends within T_MA/2 after LAT. This is
  true up to 5 MHz at a 30 or 42 MHz clock. At 10 MHz, and at 5 MHz with a 21 MHz clock, it is
  3 T_MA (simulated, `sim/results/r1ctrl_20261020_r3`). D2 allows a longer busy time; the master
  waits for START.
- The data are latched 2–3 ticks after LAT, from the continuously running tracking estimate
  (section 5). `EXTRAP` (reset 0) adds ω × EXTRAP ticks if the host wants a different latch instant.
- nE = 0 when `AMP_LOW`, `AMP_HIGH`, `TRACK_ERR` or `BUS_CFG.FORCE_NE`. nW = 0 when `FAULT`,
  not `CAL_VALID`, `CLK_FAULT`, `OVERSPEED` or `FORCE_NW`.
- Null Value: while `POS_VALID` = 0 (and `TEST_POS_EN` = 0), MT and ST are all 0 and nE = 0.
- Assumption **[verify]**: the master clocks at least once after the last CRC bit (stop bit
  position). Without that edge, SLO keeps the last CRC bit until the timeout ends.
- `TEST_POS_EN` replaces ST by `TEST_POS` (18 bit) to check the CRC from the master side.

### 3.2 SSI frame (`BUS_CFG.SSI` = 1)

`MA` idles high. The first falling edge freezes the published word. The first rising edge drives
the MSB, and each following rising edge drives the next bit (`[MT 16] ST`, binary or Gray over the
whole word). After the last bit, `SLO` is 0 until `MA` has been quiet for `TIMEOUT_TICKS`
(monoflop), then 1. The SSI clock must be ≤ 2 MHz: the freeze needs about 3 ticks after the
first falling edge, and the word is read at the first rising edge.

### 3.3 Control channel (register read of 0x40–0x7F)

One CDM bit per frame: CDM = inverted `MA` level at the end of the timeout. One CDS bit per frame,
in the frame that follows. The sequence is:

```
CDM:  ... 0 0 (>= 14 x 0 resets) | S=1 | CTS=1 | ID[2:0]=000 | ADR[6:0] | CRC4[3:0] | R=1 | W=0 | S=1 | 0 ...
CDS:  0 ...                                                                     (next frames) | S=1 | D[7:0] | CRC4[3:0] | 0 ...
```

- CRC4: polynomial x⁴ + x + 1 (0x13), start 0, sent inverted. In the command it covers ID and ADR
  **[verify: whether CTS is included]**. In the reply it covers D.
- The channel answers only reads (R = 1, W = 0) of ADR 0x40–0x7F with ID 0. Anything else, or a
  CRC error, gives no reply (CDS stays 0) and increments `DIAG_BISS.CC_ERR`.
- Where the slave start bit sits, and the byte order of multi-byte IDs, are **[verify]** items.

## 4. Register map (native SPI addresses, 16-bit registers)

RW = read/write, RO = read only, W1 = write 1 to act (self-clearing, reads 0). Bits not listed
read 0. Reset values apply after `por_n`. `EN` does not reset the registers.

### 4.1 ID, status, safety

| Addr | Name | Type | Reset | Bits |
| --- | --- | --- | --- | --- |
| 0x00 | `ID` | RO | 0x5210 | chip 'R', version 1.0 |
| 0x01 | `STATUS` | RO | — | 0 AMP_LOW, 1 AMP_HIGH, 2 OVERSPEED, 3 TRACK_ERR, 4 CAL_VALID, 5 CLK_FAULT, 6 POS_VALID, 7 FAULT, 8 EN (synchronised), 9 GATE_ACTIVE, 10 OSC_DONE |
| 0x02 | `FAULT` | RO | 0x1800 | latched causes: 0–3 comparator flags `cmp[3:0]`, 4 OTEMP, 5 AMP, 6 OVERSPEED, 7 WDT, 8 STO (EN low), 9 I2T_A, 10 I2T_B, 11 CAL (CRC mismatch), 12 POR |
| 0x03 | `FAULT_MASK` | RW | 0x0000 | 1 = source does not latch; bits 8, 11, 12 cannot be masked |
| 0x04 | `CTRL` | RW | 0x0000 | 0 CLR (W1), 1 GATE_EN, 2 WDT_EN |

`CLR` clears each `FAULT` bit whose source is inactive at that moment. Bit 11 stays set while the
calibration CRC does not match. After reset, the gates stay off until the host does these steps:

1. Write the calibration registers.
2. Write `CAL_CRC`.
3. Write `CTRL.CLR`.
4. Write `CTRL.GATE_EN`.

### 4.2 Interface

| Addr | Name | Type | Reset | Bits |
| --- | --- | --- | --- | --- |
| 0x05 | `BUS_CFG` | RW | 0x00B2 | 4:0 ST_LEN (10–18), 5 MT_EN, 6 SSI, 7 GRAY (SSI), 8 AS_MODE, 9 TEST_POS_EN, 10 FORCE_NE, 11 FORCE_NW, 13:12 TEST_POS[17:16] |
| 0x06 | `TEST_POS` | RW | 0 | TEST_POS[15:0] |
| 0x07 | `TIMEOUT_TICKS` | RW | 600 | BiSS timeout and SSI monoflop, ticks (20 µs at 30 MHz) |
| 0x32 | `DIAG_BISS` | RO | 0 | 7:0 frame count, 15:8 control-channel errors (both wrap) |
| 0x33 | `DIAG_SPI` | RO | 0 | 7:0 SPI frame errors, 15:8 position pair overruns |

### 4.3 Clock

| Addr | Name | Type | Reset | Bits |
| --- | --- | --- | --- | --- |
| 0x08 | `OSC_CFG` | RW | 0x0010 | 4:0 OSC_TRIM (to `r1_osc`), 8 MEAS (W1) |
| 0x09 | `OSC_COUNT` | RO | 0 | clk ticks in 16 periods of the MA/SCLK pad |
| 0x0A | `OSC_WIN` | RW | 0 | 7:0 LO, 15:8 HI, compared with OSC_COUNT[11:4]; 0 = no check |

To measure the oscillator, do these steps:

1. Write `OSC_CFG.MEAS` = 1.
2. Send at least 32 clock periods of known frequency on the pad. For example, send one 40-clock
   SPI frame at 1 MHz; the frame is counted as an SPI error.
3. Wait until `STATUS.OSC_DONE` = 1.
4. Read `OSC_COUNT`. f_clk = OSC_COUNT × f_ref / 16.
5. Write `TIMEOUT_TICKS` = OSC_COUNT × 20 µs × f_ref / 16 for a 20 µs timeout.

`CLK_FAULT` is set when a completed count is outside `OSC_WIN` or ≥ 4096.

### 4.4 Calibration (covered by `CAL_CRC`)

| Addr | Name | Type | Reset | Format |
| --- | --- | --- | --- | --- |
| 0x10 | `OFS_SIN` | RW | 0 | [11:0] signed ADC LSB, subtracted from the sine code |
| 0x11 | `OFS_COS` | RW | 0 | [11:0] signed ADC LSB |
| 0x12 | `GAIN` | RW | 0x4000 | Q2.14, multiplies the sine channel (= A_cos / A_sin) |
| 0x13 | `PH_SIN` | RW | 0 | Q1.15 signed, sin α |
| 0x14 | `PH_ICOS` | RW | 0x4000 | Q2.14, 1 / cos α |
| 0x15 | `H3` | RW | 0 | 7:0 H3_AMP (16-bit angle LSB), 15:8 H3_PH (1/256 turn) |
| 0x16 | `ZERO_OFS` | RW | 0 | 16-bit angle LSB, subtracted after the direction |
| 0x17 | `POS_CFG` | RW | 0x0164 | 0 DIR, 4:1 KP (loop gain 2^−KP), 9:5 KI (2^−KI per tick) |
| 0x18 | `CAL_CRC` | RW | 0 | 7:0 CRC-8 of 0x10–0x17 |

`CAL_CRC` is CRC-8 with polynomial 0x07, initial value 0xFF, no reflection and no final XOR. It is
computed over the 16 bytes of 0x10..0x17 in address order, high byte first, with the unused bits
as 0 (the values that read back). The hardware checks it continuously. A write to 0x10..0x18
clears `CAL_VALID` until the next complete check (≤ 32 ticks). S1 lists `PHASE` as 10 bit with
a LUT. R1 uses two host-computed words (sin α, 1/cos α) instead, so no LUT is needed.

### 4.5 Position (read only)

| Addr | Name | Format |
| --- | --- | --- |
| 0x19 | `POS` | 16-bit angle within the period (extrapolated by `EXTRAP`, after DIR and ZERO_OFS) |
| 0x1A | `TURNS` | signed turn count while powered; counts wraps of POS |
| 0x1B | `VELOCITY` | signed, 2^−5 LSB16 per tick (30 MHz: 1 unit = 14.3 Hz el) |
| 0x1C | `AMPLITUDE` | [11:0] vector magnitude, ADC LSB (CORDIC gain removed) |
| 0x1D | `RAW_SIN` | [11:0] last sine code (offset binary); a read takes a snapshot of RAW_COS |
| 0x1E | `RAW_COS` | [11:0] cosine code of the same pair as the last RAW_SIN read |
| 0x1F | `MEAS_ANGLE` | corrected angle of the last pair, before the tracking loop |
| 0x0D | `EXTRAP` | RW, reset 0: ticks of velocity extrapolation |
| 0x0E | `AMP_LIM` | RW, reset 0x7C08: 7:0 LO, 15:8 HI, units of 16 ADC LSB (4 consecutive pairs) |
| 0x0F | `OVS_LIM` | RW, reset 0x4000: OVERSPEED when \|VELOCITY\| > OVS_LIM |

### 4.6 Gate path and ADC scheduling

| Addr | Name | Type | Reset | Format |
| --- | --- | --- | --- | --- |
| 0x20 | `PWM_PERIOD` | RW | 0 | ticks; 0 = PWM off (f_PWM = f_clk / PERIOD) |
| 0x21–0x23 | `DUTY_A/B/C` | RW | 0 | ideal low-side on-time, ticks |
| 0x24–0x26 | `PHASE_A/B/C` | RW | 0 | start of the ideal on-window, ticks (< PERIOD) |
| 0x27 | `DEAD` | RW | 15 | [7:0] ticks removed at both ends of each on-window (15 = 500 ns) |
| 0x28 | `SCHED` | RW | 0x201E | 7:0 PAIR_TICKS (sin/cos pair period), 15:8 GUARD |
| 0x35 | `LATE` | RO | 0 | current conversions that started after their strobe |

Channel x is on while DEAD ≤ (cnt − PHASE_x) mod PERIOD < DUTY_x − DEAD. The gate output is the
registered PWM AND `GATE_ACTIVE` AND the `EN` pad. PERIOD, DUTY and PHASE take effect at the
counter wrap. Channels A and B request a current conversion at the window centre
(PHASE + DUTY/2) when DUTY ≥ 2·DEAD + 2. A sin/cos pair does not start when a strobe is due
within GUARD ticks. GUARD must cover two conversions.

### 4.7 Current, temperature, I²t

| Addr | Name | Type | Reset | Format |
| --- | --- | --- | --- | --- |
| 0x29 | `I_A` | RO | 0 | [11:0] last ISA code |
| 0x2A | `I_B` | RO | 0 | [11:0] last ISB code |
| 0x2B | `TEMP` | RO | 0 | T2F edges in the last window |
| 0x2C | `OT_LIM` | RW | 0xFFFF | OTEMP when TEMP ≥ OT_LIM |
| 0x2D | `I2T_CFG` | RW | 0 | 3:0 TAU_SHIFT, 7:4 PRESCALE, 11:8 CMP_FILT |
| 0x2E | `I2T_LIM` | RW | 0xFFFF | I2T_x when E_x[23:8] ≥ I2T_LIM |
| 0x2F | `I_ZERO` | RW | 0 | [11:0] zero-current code |
| 0x30 | `I2T_A` | RO | 0 | E_A[23:8] |
| 0x31 | `I2T_B` | RO | 0 | E_B[23:8] |
| 0x34 | `T2F_WIN` | RW | 15 | window 2^T2F_WIN ticks (minimum 2^8) |
| 0x0B | `WDT_PERIOD` | RW | 0xFFFF | watchdog period, 1024-tick units; kicked by every BiSS/SSI frame end and every well-formed SPI frame |

I²t model: every 2^PRESCALE PWM periods, for each channel: i = |I − I_ZERO| >> 4 (8 bit);
E ← E + ((i² · 256 − E) >> TAU_SHIFT). For a constant current, E[23:8] approaches i², with a
time constant of 2^TAU_SHIFT updates. CMP_FILT: a comparator flag must stay high for
CMP_FILT + 1 ticks before it latches (0 = 1 tick, 4 ticks from the pin to `FAULT_N`).

### 4.8 Analog control

| Addr | Name | Type | Reset | Format |
| --- | --- | --- | --- | --- |
| 0x0C | `ANA_CTRL` | RW | 0 | 16 bits to the analog blocks (PGA gain, enables); bit assignment open until the AFE/ADC/T2F interfaces are written |

### 4.9 BiSS identification (0x40–0x7F)

A native SPI read of 0x40–0x7F returns the BiSS byte in [7:0].

| BiSS addr | Content | Value in this RTL |
| --- | --- | --- |
| 0x42–0x43 | Profile ID | 0x0001, placeholder **[verify the D2 profile code]** |
| 0x44–0x47 | DEV_SN | 0 (allowed by D2; no NVM) |
| 0x78–0x7D | DEV_ID | "R1JFE0" (0x52 0x31 0x4A 0x46 0x45 0x30) |
| 0x7E–0x7F | MFR_ID | 0x0000: the ID is not assigned yet (spec open item 5); RTL parameter `MFR_ID` |

## 5. Position path (r1_pos) number formats

| Signal | Format |
| --- | --- |
| ADC codes | 12-bit offset binary, mid-scale 0x800 = 0 |
| Corrected x, y | 4 fractional bits; ×2 into the CORDIC (5 fractional bits, saturated at ±4096 LSB) |
| CORDIC | 20-bit x/y, 18-bit angle (2^18 = one turn), 18 iterations after a ±90° pre-rotation |
| H3 correction | θ ← θ − H3_AMP · sin(4θ + H3_PH), 256-entry sine table (8 bit) |
| Tracking loop | NCO θ (16.20 bit) += ω every tick; per pair e = θ_meas − θ(at hold); θ += e·2^−KP, ω += e·2^−KI |
| Output | POS = (±(θ + ω·EXTRAP)) − ZERO_OFS, registered every tick |

One pair is processed in 27 ticks. A pair that arrives while the previous pair is still being
processed is dropped and counted in `DIAG_SPI[15:8]`.

## 6. Interface to the analog blocks (macro ports)

| Port | Direction | Meaning |
| --- | --- | --- |
| `clk` | in | `r1_osc` output |
| `por_n` | in | power-on reset, active low (asynchronous assert, synchronous release) |
| `adc_hold` | out | high: both sin/cos track-and-holds hold (rising edge = sampling instant) |
| `adc_start`, `adc_mux[1:0]` | out | one-tick pulse: convert channel 0 SIN T&H, 1 COS T&H, 2 ISA, 3 ISB (the mux is stable during the conversion) |
| `adc_done`, `adc_data[11:0]` | in | one-tick pulse with the code (offset binary), synchronous to `clk` |
| `cmp[3:0]` | in | comparator flags, asynchronous, synchronised inside |
| `t2f_clk` | in | T2F oscillator, asynchronous, ≤ f_clk/4 |
| `osc_trim[4:0]` | out | to `r1_osc` |
| `ana_ctrl[15:0]` | out | analog control word |
| `en_pad`, `cs_n`, `ma_sclk`, `sdi` | in | pads (level-shifted) |
| `slo_sdo`, `fault_n`, `gate_a/b/c` | out | pads |

The ADC must deliver `adc_done` 12–15 ticks after `adc_start` (≥ 2 MSPS at 30 MHz) so that one
pair fits in `PAIR_TICKS` = 30. The testbench uses 12 ticks (assumed).

## 7. Change log

| Version | Date | Change |
| --- | --- | --- |
| 0.1 | 2026-10-20 | first draft with the first RTL |

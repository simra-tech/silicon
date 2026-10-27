# R1 bus protocols and register map (draft 0.7, 2026-10-27)

Owner block: `r1_ctrl` (`designs/r1-joint/blocks/r1_ctrl`). This document is the contract between
the host, the digital macro (`rtl/r1_ctrl_top.v`) and the analog blocks it connects to. It is a
draft: nothing here is on silicon. The RTL in `rtl/` implements this version (revision 0.7; change log in section 7).
Versioning rule: `ID` = 0x52 followed by the RTL revision digit (0.5 = 0x5205, 0.7 = 0x5207). Revision 0.6 was a
hardening of the 0.5 RTL without an RTL change, so it has no `ID` of its own.
Revision 0.2 checked every BiSS interpretation item of 0.1 against the BiSS C Rev D2 document
("D2", page numbers of that PDF). Section 3.4 lists the result. One item stays **[verify]**: the
BP_ID (profile) code. The protocol testbench uses our own master model, so the interop runs of
gate V4 are still necessary.

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
   A write takes effect 3–5 ticks after `CS_N` rises (section 4.12).
5. Drive `CS_N` high, then drive `MA` high.
6. Wait for one timeout (`TIMEOUT_TICKS`). The BiSS/SSI logic then arms and accepts the next frame.

The rising `MA` edge in step 5 does not start a frame: a frame starts only with a falling edge
after the slave has armed.

## 2. SPI

### 2.1 Frames: mode 0, 24 bits

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

### 2.2 AS5047P-compatible frames (removed in 0.2)

Revision 0.1 had an AS5047P-compatible 16-bit mode (`BUS_CFG` bit 8). Revision 0.2 removes it to
save area (the 0.1 README listed it as an area trim). `BUS_CFG` bit 8 is reserved and reads 0.

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
  true up to 1 MHz at all clock corners; above 1 MHz it is 2–6 T_MA (simulated,
  `sim/results/r1ctrl_20261020_v02a`). D2 Table 10 requires t_busy ≥ 2 T_MA and ≤ 40 µs; the
  master waits for START.
- The data are latched 2–3 ticks after LAT, from the continuously running tracking estimate
  (section 5). `EXTRAP` (reset 0) adds ω × EXTRAP ticks if the host wants a different latch instant.
- Half-tick latch timing (`BUS_CFG.LAT_HALF`, reset 1): the LAT event is also sampled on the
  falling `clk` edge. When it was seen half a tick before the rising-edge capture, the latched
  position is moved back by half a tick of travel (`VELOCITY` / 16). This halves the latch-instant
  uncertainty from 1 tick to 1/2 tick. Simulated at 100 kHz el and 30 MHz: latch error spread
  1.18° el without, 0.61° el with `LAT_HALF` (1 tick = 1.20° el). Cost: 161 cells (1 700 µm²).
  `LAT_HALF` has no effect while `TEST_POS_EN` = 1.
- nE = 0 when `AMP_LOW`, `AMP_HIGH`, `TRACK_ERR` or `BUS_CFG.FORCE_NE`. nW = 0 when `FAULT`,
  not `CAL_VALID`, `CLK_FAULT`, `OVERSPEED` or `FORCE_NW`.
- Null Value: while `POS_VALID` = 0 (and `TEST_POS_EN` = 0), MT and ST are all 0 and nE = 0.
- Stop bit: the slave drives 0 (STP) at the last rising `MA` edge after the CRC (D2 p. 7). Without
  that edge, SLO keeps the last CRC bit until the timeout ends.
- `TEST_POS_EN` replaces ST by `TEST_POS` (18 bit) to check the CRC from the master side.

### 3.2 SSI frame (`BUS_CFG.SSI` = 1)

`MA` idles high. The first falling edge freezes the published word. The first rising edge drives
the MSB, and each following rising edge drives the next bit (`[MT 16] ST`, binary or Gray over the
whole word). After the last bit, `SLO` is 0 until `MA` has been quiet for `TIMEOUT_TICKS`
(monoflop), then 1. The SSI clock must be ≤ 2 MHz: the freeze needs about 3 ticks after the
first falling edge, and the word is read at the first rising edge. Revision 0.5 tests this with the word changing at every tick and the first falling edge at 16 phases of the `clk` period: 16 of 16 words are complete at 2 MHz; at 10 MHz words are mixed (README, revision 0.5, CDC table).

### 3.3 Control channel (register read of 0x40–0x7F, D2 pp. 13–17)

One CDM bit per frame: CDM = inverted `MA` level at the end of the timeout. One CDS bit per
frame. The slave answers the CDM bit of frame k in the CDS bit of frame k + 1 (D2 p. 14).

```
frame k  0   1    2..4       5..11     12..15     16  17  18   19..31          32
CDM      S=1 CTS=1 ID[2:0]=0 ADR[6:0]  ~CRC4[3:0] R   W   S=1  x (13 bits)     S=1: next byte
CDS(k+1) 1   0    0          0         0          R   W'  S    D[7:0] ~CRC4 P  ...
```

- `CTS` = 1 selects register communication; `CTS` = 0 (BiSS commands) is not supported and
  the frame is ignored (D2 p. 14).
- Header CRC-4: polynomial 0x13, start 0, sent inverted. It covers `CTS`, `ID` and `ADR`; the
  start bit is excluded (D2 p. 14).
- The slave sends IDL0 = 1 in the frame after the start bit, then 0 (slave 0 of a
  point-to-point link, D2 pp. 14–15).
- The slave repeats `R` and `W`. When it refuses the access, it sends `W` inverted (W') and no
  data (D2 p. 16). Refused: writes, reads of addresses outside the table of section 4.9, and
  0x40 `BSEL` (one bank only, D2 Table 4).
- The slave repeats the start bit `S` of the master. The master can send `S` later than frame 18;
  the slave waits (D2 p. 16). Then `D[7:0]`, the data CRC-4 (inverted, data only) and the stop
  bit `P` follow. P = 0 when the next address is readable, else P = 1 (D2 p. 16).
- Sequential read: after P = 0, a new `S` from the master reads ADR + 1 (D2 Figure 30).
- 14 consecutive CDM = 0 reset the channel to idle (D2 p. 15).
- A header CRC error, a refused access and an unsupported command increment
  `DIAG_BISS.CC_ERR` (4 bits, saturating).
- Multi-byte values are big-endian: the high byte is at the lower address (D2 p. 22).

### 3.4 D2 conformance of the 0.1 interpretation items

| 0.1 item | D2 reference | 0.2 result |
| --- | --- | --- |
| CTS in the header CRC | p. 14: "considers CTS and the addressing bits" | fixed: CRC over 11 bits (0.1: 10 bits) |
| Where the slave start bit sits | p. 16, Figure 30: slave repeats `S`, may be delayed | fixed: `S` echo, then `D`, CRC, `P` |
| R/W echo, refusal | p. 16 | added: R, W echo; W inverted on refusal (0.1: no reply) |
| IDL bits | pp. 14–15 | added: IDL0 = 1 |
| Stop bit `P` and sequential read | p. 16, Figure 30 | added |
| Byte order of multi-byte IDs | p. 22 | confirmed: big-endian |
| Stop bit STP of the frame | p. 7 | confirmed |
| BSEL, EDS_BANK | Tables 4, 5 | fixed: 0x40 refused; 0x41 = 0x00 (no EDS) readable |
| BP_ID (profile) code | pp. 21–22: ≠ 0x0000 without EDS; code assigned by iC-Haus / BiSS Association | open **[verify]**: placeholder 0x0001 |
| t_busy, timeout | Table 10: t_busy ≥ 2 T_MA, timeout 12.5–40 µs | confirmed (simulated) |

## 4. Register map (native SPI addresses, 16-bit registers)

RW = read/write, RO = read only, W1 = write 1 to act (self-clearing, reads 0). Bits not listed
read 0. Reset values apply after `por_n`. `EN` does not reset the registers.

### 4.1 ID, status, safety

| Addr | Name | Type | Reset | Bits |
| --- | --- | --- | --- | --- |
| 0x00 | `ID` | RO | 0x5207 | chip 'R', RTL revision 0.7 (0.5 and 0.6: 0x5205, 0.4: 0x5204, 0.3: 0x5203, 0.2: 0x5202, 0.1: 0x5210) |
| 0x01 | `STATUS` | RO | — | 0 AMP_LOW, 1 AMP_HIGH, 2 OVERSPEED, 3 TRACK_ERR, 4 CAL_VALID, 5 CLK_FAULT, 6 POS_VALID, 7 FAULT, 8 EN (synchronised), 9 GATE_ACTIVE, 10 OSC_DONE, 11 CAL_BUSY, 12 CAL_DONE, 13 CAL_EXH (any comparator), 14 TRIM_UNLK (0.7, section 4.3) |
| 0x02 | `FAULT` | RO | 0x1800 (EN high at reset; 0x1900 with EN low) | latched causes: 0–3 comparator flags `cmp[3:0]`, 4 OTEMP, 5 AMP, 6 OVERSPEED, 7 WDT, 8 STO (EN low), 9 I2T_A, 10 I2T_B, 11 CAL (CRC mismatch), 12 POR |
| 0x03 | `FAULT_MASK` | RW | 0x0000 | 1 = source does not latch; bits 8, 11, 12 cannot be masked |
| 0x04 | `CTRL` | RW | 0x0000 | 0 CLR (W1), 1 GATE_EN, 2 WDT_EN, 3 CMP_CAL (W1, section 4.10) |

`CLR` clears each `FAULT` bit whose source is inactive at that moment. Bit 11 stays set while the
calibration CRC does not match. Revision 0.7: the `EN` synchroniser resets to 1 (the idle level of the pad), so a
power-up with `EN` high gives 0x1800, not 0x1900 (0.5 and 0.6 latched STO for the two ticks of synchroniser latency,
r1_top finding R3). A power-up with `EN` low still latches STO. After reset, the gates stay off until the host does these steps:

1. Write the calibration registers (section 4.4), the comparator words and the ADC weights of both slices.
2. Run the comparator calibration (section 4.10), if it is used.
3. Write `CAL_CRC` (computed over the values that read back, section 4.4).
4. Write `CTRL.CLR`.
5. Write `CTRL.GATE_EN`.

### 4.2 Interface

| Addr | Name | Type | Reset | Bits |
| --- | --- | --- | --- | --- |
| 0x05 | `BUS_CFG` | RW | 0x40B2 | 4:0 ST_LEN (10–18), 5 MT_EN, 6 SSI, 7 GRAY (SSI), 8 reserved (reads 0), 9 TEST_POS_EN, 10 FORCE_NE, 11 FORCE_NW, 13:12 TEST_POS[17:16], 14 LAT_HALF |
| 0x06 | `TEST_POS` | RW | 0 | TEST_POS[15:0] |
| 0x07 | `TIMEOUT_TICKS` | RW | 600 | [11:0] BiSS timeout and SSI monoflop, ticks (20 µs at 30 MHz; maximum 4095 = 97 µs at 42 MHz) |
| 0x32 | `DIAG_BISS` | RO | 0 | 7:0 frame count (wraps), 11:8 CC_ERR: control-channel errors (saturating at 15) |
| 0x33 | `DIAG_SPI` | RO | 0 | 3:0 SPI frame errors, 11:8 position pair overruns (both saturating at 15) |

### 4.3 Clock

| Addr | Name | Type | Reset | Bits |
| --- | --- | --- | --- | --- |
| 0x08 | `OSC_CFG` | RW | 0x0016 | 4:0 OSC_TRIM (to `r1_osc`, reset 22, PLAN.md D13; codes below 18 locked, see the rule below), 8 MEAS (W1) |
| 0x09 | `OSC_COUNT` | RO | 0 | clk ticks in 16 periods of the MA/SCLK pad; a read before `OSC_DONE` returns the running count |
| 0x0A | `OSC_WIN` | RW | 0 | 7:0 LO, 15:8 HI, compared with OSC_COUNT[11:4]; 0 = no check |

To measure the oscillator, do these steps:

1. Write `OSC_CFG.MEAS` = 1.
2. Send at least 32 clock periods of known frequency on the pad. For example, send one 40-clock
   SPI frame at 1 MHz; the frame is counted as an SPI error.
3. Wait until `STATUS.OSC_DONE` = 1.
4. Read `OSC_COUNT`. f_clk = OSC_COUNT × f_ref / 16.
5. Write `TIMEOUT_TICKS` = OSC_COUNT × 20 µs × f_ref / 16 for a 20 µs timeout.

`CLK_FAULT` is set when a completed count is outside `OSC_WIN` or ≥ 4096. It sets nW = 0 in
the BiSS frame; it does not latch a `FAULT` bit. Example at 30 MHz with a 1 MHz reference:
OSC_COUNT = 480, OSC_COUNT[11:4] = 30; `OSC_WIN` = 0x201C (LO 28, HI 32) accepts ±7 %.

**`OSC_TRIM` rule (PLAN.md D13 amendment, 2026-10-21; hardware lock since revision 0.7).** With `r1_osc` revision 2 the
frequency at ff, 1.32 V, -40 C is 39.5 MHz at the reset code 22 and up to 56.4 MHz at code 0. The digital macro closes
static timing at 42 MHz only. Codes 0 to 17 can exceed 42 MHz at that corner. Rules for the host:

1. Keep the reset code 22. It is below 42 MHz at every corner.
2. Write a code below 18 only after `OSC_COUNT` shows that the resulting frequency is 40 MHz or less.
3. Do the check in small steps. Write one code, measure again (`OSC_CFG.MEAS`), then go on.

Hardware lock (revision 0.7). The macro enforces rules 2 and 3 with the status bit `STATUS.TRIM_UNLK` (bit 14, reset 0):

- A write to `OSC_CFG` changes `OSC_TRIM` only if the new code equals the present code, or is 18 or above, or
  `TRIM_UNLK` = 1. Otherwise the trim field keeps its value (read back `OSC_CFG` to see it); `MEAS` acts in all cases.
- `TRIM_UNLK` is set by the read path: an SPI read of `OSC_COUNT` (0x09) sets it when, at that read, `OSC_DONE` = 1,
  `OSC_WIN` is not 0 and the count is inside `OSC_WIN` (the `CLK_FAULT` compare: LO ≤ OSC_COUNT[11:4] ≤ HI and
  OSC_COUNT < 4096). The macro does not know the reference frequency, so the host states the 40 MHz limit through
  `OSC_WIN.HI`: HI = 40 MHz / f_ref − 1 for f ≤ 40 MHz (39 at f_ref = 1 MHz; HI = 40 allows up to 40.9 MHz).
- `TRIM_UNLK` is cleared by every accepted write that changes `OSC_TRIM` (also to a code of 18 or above), and by reset.
  Each step below 18 therefore needs a new measurement and read at the present code.

Procedure for a code below 18:

1. Write `OSC_WIN` with HI for 40 MHz at the reference frequency.
2. Write `OSC_CFG` = present code + `MEAS`, send the reference clock, wait for `STATUS.OSC_DONE` = 1.
3. Read `OSC_COUNT`. If the count is inside `OSC_WIN`, `STATUS.TRIM_UNLK` is 1.
4. Write the next code (one or two codes lower). Read `OSC_CFG` to confirm it.
5. Do steps 2 to 4 again for each further step.

The STA limit stays 42 MHz and no timing constraint changes.

### 4.4 Calibration (position words; `CAL_CRC`)

| Addr | Name | Type | Reset | Format |
| --- | --- | --- | --- | --- |
| 0x10 | `OFS_SIN` | RW | 0 | [11:0] signed ADC LSB, subtracted from the sine code |
| 0x11 | `OFS_COS` | RW | 0 | [11:0] signed ADC LSB |
| 0x12 | `GAIN` | RW | 0x4000 | Q2.14, multiplies the sine channel (= A_cos / A_sin) |
| 0x13 | `PH_SIN` | RW | 0 | Q1.15 signed, sin α |
| 0x14 | `PH_ICOS` | RW | 0x4000 | Q2.14, 1 / cos α |
| 0x15 | `H3` | RW | 0 | 7:0 H3_AMP (16-bit angle LSB), 15:8 H3_PH (1/256 turn) |
| 0x16 | `ZERO_OFS` | RW | 0 | 16-bit angle LSB, subtracted after the direction |
| 0x17 | `POS_CFG` | RW | 0x0164 | 0 DIR, 4:1 KP (loop gain 2^−KP), 9:5 KI (2^−KI per tick; values outside 8–23 are clamped to 8 or 23) |
| 0x18 | `CAL_CRC` | RW | 0 | 7:0 CRC-8 of 0x10–0x17, 0x36–0x3C, 0x50–0x5D, 0x60–0x6D (revision 0.3) |

`CAL_CRC` is CRC-8 with polynomial 0x07, initial value 0xFF, no reflection and no final XOR.
Revision 0.3 computes it over 43 words (86 bytes), high byte first, with the values that read
back (unused bits as 0, `EXH` bits as read), in this order:

1. 0x10..0x17 (position calibration, 8 words);
2. 0x36..0x3C (`CMP_THR_A/B`, `AZ_START`, `AZ_CFG`, `CMP_CAL_A/B`, `CMP_CAL_IDEAL`, 7 words);
3. 0x50..0x5D (`ADC_A_W0`–`ADC_A_W13`, 14 words);
4. 0x60..0x6D (`ADC_B_W0`–`ADC_B_W13`, 14 words).

The hardware checks it continuously, one byte per tick, through the register read multiplexer
(the SPI takes the multiplexer for 2 ticks per frame; the check then pauses). A write to a covered word or to
`CAL_CRC` clears `CAL_VALID` until the next complete check (≤ 172 ticks plus 2 ticks per SPI frame). A comparator
calibration search (`CAL_BUSY`) also clears it, because the search writes `CMP_CAL_A/B`: after a
search the host reads the codes, writes the new `CAL_CRC` and then `CTRL.CLR` (FAULT bit 11 is
latched while `CAL_VALID` = 0). Reason for the extension (0.2 open issue 6): the comparator
thresholds and calibration codes set the over-current trip points and the ADC weights set every
current and position code, so an upset in these registers is as safety-relevant as one in the
position words. Error detection: all single-bit and all odd-weight errors (0x07 has the factor
x + 1); 2-bit errors are detected while their distance is < 127 bits; other patterns escape with
probability 2^−8. S1 lists `PHASE` as 10 bit with a LUT. R1 uses two host-computed words (sin α,
1/cos α) instead, so no LUT is needed.

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
| 0x20 | `PWM_PERIOD` | RW | 0 | [12:0] ticks, 0 = PWM off (f_PWM = f_clk / PERIOD, at most 8191 ticks: 3.66 kHz at 30 MHz). Bits 15:13 read 0 and ignore writes (0.4; was 16 bit) |
| 0x21–0x23 | `DUTY_A/B/C` | RW | 0 | [12:0] ideal low-side on-time, ticks (bits 15:13 read 0, 0.4) |
| 0x24–0x26 | `PHASE_A/B/C` | RW | 0 | [12:0] start of the ideal on-window, ticks (< PERIOD; bits 15:13 read 0, 0.4) |
| 0x27 | `DEAD` | RW | 15 | [7:0] ticks removed at both ends of each on-window (15 = 500 ns) |
| 0x28 | `SCHED` | RW | 0x1416 | 7:0 PAIR_TICKS (encoder frame period, reset 22, D18), 15:8 GUARD (reset 20) |
| 0x35 | `LATE` | RO | 0 | [3:0] current frames that started after their strobe (saturating) |
| 0x38 | `AZ_START` | RW | 0 | [12:0] counter value at which `az_win` starts (bits 15:13 read 0, 0.4) |
| 0x39 | `AZ_CFG` | RW | 0x4E00 | 7:0 AZ_LEN (ticks; 0 = no window), 13:8 THR_ZERO (reset 14, section 4.10), 15:14 CAL_STEP (calibration step length 16 << CAL_STEP ticks, reset 1 = 32) |

Channel x is on while DEAD ≤ (cnt − PHASE_x) mod PERIOD < DUTY_x − DEAD. The gate output is the
registered PWM AND `GATE_ACTIVE` AND the `EN` pad. PERIOD, DUTY and PHASE take effect at the
counter wrap. `GATE_ACTIVE` is 0 while a comparator calibration runs.

ADC frames (revision 0.3, PLAN.md D18): the ADC has two slices that convert in parallel. Each
frame converts one pair: the encoder frame {SIN on slice A, COS on slice B} or the current frame
{ISA on slice A, ISB on slice B}. One `adc_start` pulse starts both slices; `adc_sel` selects the
pair.

Current frame: one strobe per period at the centre of the channel A window (PHASE_A + DUTY_A/2),
when DUTY_A ≥ 2·DEAD + 2. At the strobe `is_smp` goes high (both isense track-and-holds hold) and
the current frame starts. Channel B is therefore sampled at the channel A centre. For a centred
PWM pattern (PHASE_x = C − DUTY_x/2) all windows share that centre. If a frame is still
converting at the strobe, the current frame starts when both slices are free and `LATE` counts it.

Encoder frames: a frame starts every PAIR_TICKS (reset 22 = 0.733 µs at 30 MHz). No frame starts
when the strobe is due within GUARD ticks; GUARD must cover one conversion (reset 20). The frame
grid restarts at the current frame, so the current frame takes the place of one encoder frame.
For PERIOD = N × PAIR_TICKS the encoder gap is 2 × PAIR_TICKS once per period; otherwise it is at
most 2 × PAIR_TICKS + GUARD. An encoder frame also does not start before both codes of the
previous encoder frame are out of the weight correction (section 4.11). The frame is therefore
max(PAIR_TICKS, conversion + 5 ticks), with the conversion counted from the `adc_start` pulse to
the later `valid` of the two slices: 22 ticks for a conversion of ≤ 17 ticks. The holds
(`adc_hold`, `is_smp`) are released when both slices have returned `valid`.

Auto-zero window: `az_win` is high for AZ_LEN ticks from counter value AZ_START. The host puts
it where both low-side FETs are off. Comparator mask (revision 0.7, INTERFACES.md "vref_b disturbance at the isense
pedestal switch"): the four comparator flags are ignored during `az_win` and for `AZ_EXT` ticks after it (reset 120 =
4 µs at 30 MHz; 0.6: fixed 16 ticks). The mask is aligned with the synchronised flags: a flag sampled at the first
clock edge after the `az_win` rise up to the edge `AZ_EXT` ticks after the `az_win` fall is ignored; a flag sampled
one tick later latches. `AZ_EXT` = 0 masks the window only. A flag that stays high through the mask latches at the end
of the mask (it is not lost). The mask delays an over-current that starts in the window by up to AZ_LEN + AZ_EXT ticks.

| Addr | Name | Type | Reset | Format |
| --- | --- | --- | --- | --- |
| 0x3E | `AZ_EXT` | RW | 120 (0x0078) | [7:0] comparator mask after `az_win`, ticks (0 = window only, at most 255 = 8.5 µs at 30 MHz). Bits 15:8 read 0. Not covered by `CAL_CRC` |


### 4.7 Current, temperature, I²t

| Addr | Name | Type | Reset | Format |
| --- | --- | --- | --- | --- |
| 0x29 | `I_A` | RO | 0 | [11:0] last ISA code |
| 0x2A | `I_B` | RO | 0 | [11:0] last ISB code |
| 0x2B | `TEMP` | RO | 0 | [13:0] T2F edges in the last window (saturating) |
| 0x2C | `OT_LIM` | RW | 0x3FFF | [13:0] OTEMP when TEMP ≥ OT_LIM |
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
| 0x0C | `ANA_CTRL` | RW | 0x0028 | 16 bits; bits 6:0 are decoded in the macro (0.5), bits 15:7 are reserved. Reset 0x0028 (0.4: 0) |

`ANA_CTRL` bit assignment (revision 0.5; `PGA_GAIN` was named in 0.4). The macro has no `ana_ctrl` port
any more: the bits that reach analog blocks leave as the ports named in the last column.

| Bits | Name | Reset | Port | Meaning |
| --- | --- | --- | --- | --- |
| 2:0 | `PGA_GAIN` | 0 | `pga_c[3:0]` | Gain code of `r1_afe`, one code for both channels (SIN and COS), because `r1_afe` has one control vector `c1 c2 c3 c4`. 0 = x1, 1 = x2, 2 = x4, 3 = x8, 4 = x16, 5 = x32. Codes 6 and 7 act as 5. The decoder (below) is in the macro; it is registered, so `pga_c` changes one tick after the register. Gain steps are made by the host while the gates are off, because a step disturbs the encoder path for the settling time |
| 3 | `T2F_EN` | 1 | `t2f_en` | `r1_t2f` `en`. Reset 1, so the temperature count runs after reset. `fout` is undefined for about 1 us after `en` rises (`r1_t2f` README); the T2F window is at least 2^8 ticks, so the first window after a rising edge is not usable and the host or the over-temperature threshold must allow for it |
| 4 | `T2F_MODE` | 0 | `t2f_mode` | `r1_t2f` `mode`: 0 = PTAT mode (f proportional to absolute temperature), 1 = REF mode (temperature-independent frequency; the ratio of the two readings removes C and the comparator delay). Polarity as the G1 interface file (`T2F_MODE`) |
| 5 | `BIAS_EN` | 1 | `bias_en` | Enable of the `r1_bias` mirrors (assumed: one enable for all bias outputs; the bias block is not designed yet, so the polarity is a contract the block must meet: 1 = bias on). Reset 1 |
| 6 | `ADC_ARM` | 0 | none (internal) | Rising edge (0 to 1) re-arms the first-conversion discard (`ADC_CFG`, section 4.11). The host writes 1 and then 0 after it enables or resets the ADC. A reset of the macro (`por_n`) arms it too. Both events also start the bootstrap pre-charge hold of section 4.11. The macro does not gate the ADC with this bit |
| 15:7 | reserved | 0 | none | Stored and read back. No analog block uses them. Write 0 |

`PGA_GAIN` decoder, `pga_c[0]` = `c1` ... `pga_c[3]` = `c4` (table of `r1_afe` README, "PGA_GAIN code"; the AFE has four 3.3 V
switch lines, `c3b` is derived inside the channel). Reset value of `pga_c` is 0000 (x1):

| `PGA_GAIN` | Step | `c1 c2 c3 c4` | `pga_c[3:0]` |
| --- | --- | --- | --- |
| 0 | x1 | 0 0 0 0 | 0000 |
| 1 | x2 | 1 0 0 0 | 0001 |
| 2 | x4 | 1 1 0 0 | 0011 |
| 3 | x8 | 1 1 1 0 | 0111 |
| 4 | x16 | 1 1 0 1 | 1011 |
| 5, 6, 7 | x32 | 1 1 1 1 | 1111 |

The 1.2 V to 3.3 V level shifters (`r1_ls`) for `pga_c`, `t2f_en`, `t2f_mode` and `bias_en` are not in `r1_ctrl`; the
chip-level integration places them. There is no oscillator enable bit (confirmed in 0.5): `r1_ctrl` runs on the
`r1_osc` clock, so a register bit that stops that clock would stop the macro with no way to restart it. The top level ties
`osc_en` high. `osc_trim` is `OSC_CFG` (0x08).

**Reset polarity (`por_n`).** `por_n` is active low: asynchronous assert, synchronous release after two `clk` edges
(`rst_n` of the macro). Low means reset. `r1_adc` shares it. After the release the first `DISCARD` ADC conversions are dropped (section 4.11). Source of `por_n`: the
`r1_por` cell of the bias block (open, INTERFACES.md).


### 4.9 BiSS identification (0x40–0x7F)

A native SPI read of 0x40–0x7F returns the BiSS byte in [7:0], except 0x50–0x5D and 0x60–0x6D,
which are the ADC weights (section 4.11; the BiSS control channel does not access them).

| BiSS addr | Content | Value in this RTL |
| --- | --- | --- |
| 0x40 | BSEL | refused (one bank only, D2 Table 4) |
| 0x41 | EDS_BANK | 0x00: no EDS (D2 Table 5) |
| 0x42–0x43 | BP_ID (profile) | 0x0001, placeholder **[verify]**: D2 requires ≠ 0x0000 without EDS; the code is assigned outside D2 (pp. 21–22) |
| 0x44–0x47 | DEV_SN | 0 (allowed by D2; no NVM) |
| 0x78–0x7D | DEV_ID | "R1JFE0" (0x52 0x31 0x4A 0x46 0x45 0x30) |
| 0x7E–0x7F | MFR_ID | 0x0000: the ID is not assigned yet (spec open item 5); RTL parameter `MFR_ID` |

### 4.10 Comparator thresholds and offset calibration

| Addr | Name | Type | Reset | Bits |
| --- | --- | --- | --- | --- |
| 0x36 | `CMP_THR_A` | RW | 0x003F | 5:0 THR_OC_A, 13:8 THR_NEG_A (to `r1_safe`). Reset (0.7): THR_OC 63, THR_NEG 0 = cell code 63 for both cells, the least-sensitive code (0.6: 0x3F3F) |
| 0x37 | `CMP_THR_B` | RW | 0x003F | 5:0 THR_OC_B, 13:8 THR_NEG_B (reset as `CMP_THR_A`) |
| 0x3A | `CMP_CAL_A` | RW | 0x2020 | 5:0 CAL_OC_A, 6 EXH_OC_A (RO), 13:8 CAL_NEG_A, 14 EXH_NEG_A (RO) |
| 0x3B | `CMP_CAL_B` | RW | 0x2020 | 5:0 CAL_OC_B, 6 EXH_OC_B (RO), 13:8 CAL_NEG_B, 14 EXH_NEG_B (RO) |
| 0x3C | `CMP_CAL_IDEAL` | RW | 0x3748 | 6:0 IDEAL_OC, 14:8 IDEAL_NEG: 2 × k_ideal rounded down (half codes); reset 72 (k_ideal 36.31) and 55 (27.69), from `r1_safe` revision 3 |

Comparator order of `cmp[3:0]` and `FAULT[3:0]`: 0 OC_A, 1 NEG_A, 2 OC_B, 3 NEG_B. Code meaning
(`r1_safe` revision 3): cell code c = THR_OC (OC) or 63 − THR_NEG (NEG); calibration code k is
summed into the threshold DAC with step VREF/252 = LSB/8 (k = 32: no shift); a flag = 1 means the
input is above the cell threshold (`POL` = 0 for all four).

Reset thresholds (revision 0.7, r1_top finding R4). With the `r1_safe` formulas Vth_od(code) = (2 code − 63)/63 · VREF and
Vsh_th(code) = VREF · (1/26 + (2 code − 63)/882), VREF = 1.05 V, CAL 32:

| Cell | Reset field | Cell code c | Trips when | Vod threshold | Shunt-referred threshold | At zero current (Vod −0.565 V) |
| --- | --- | --- | --- | --- | --- | --- |
| OC | THR_OC = 63 | 63 | Vod > Vth_od(63) | +1.050 V | +115.4 mV | no flag (margin 1.615 V Vod) |
| NEG | THR_NEG = 0 | 63 | Vod < Vth_od(0) | −1.050 V | −34.6 mV | no flag (margin 0.485 V Vod) |
| NEG, 0.6 reset | THR_NEG = 63 | 0 | Vod < Vth_od(63) | +1.050 V | +115.4 mV | **flag** (R4: FAULT bits 1 and 3 latch, CLR cannot clear) |

Both reset codes are outside the r1_isense output range (codes ≥ 60), so the comparators are in effect off until the host
writes its thresholds. The host writes `CMP_THR_A/B` before `CAL_CRC` and `CLR` (section 4.1).

**Tap indices to `r1_safe` (revision 0.5).** `thr` and `cal` no longer leave the macro. The macro computes the tap indices
of the `r1_safe` string multiplexers and presents them as `tap_p[31:0]` and `tap_n[31:0]`; comparator i (0 OC_A, 1 NEG_A,
2 OC_B, 3 NEG_B) uses `tap_p[8i+7:8i]` = nP and `tap_n[8i+7:8i]` = nN, with c = thr (OC) or 63 - thr (NEG), d = cal - 32:
`nP = 4c + ceil(d/2)`, `nN = 4(63 - c) - floor(d/2)`, both clipped to 0..252. The thr in the formula is the effective
threshold (THR_ZERO during a search). The ports are registered: they change one tick after `CMP_THR`, `CMP_CAL` or the end of a
search, and nP and nN of a comparator always change in the same tick. Reset values (0.7): nP 252, nN 0 on all four comparators (cell code 63, cal 32; 0.6: NEG nP 0, nN 252).
Not covered by `CAL_CRC` (they are derived).

Contract (`r1_safe` README, `sim/cal_model.py`): at zero current, with THR_ZERO = 14 on all four
comparators, k_rel is the first code (ascending, output starting high) at which the output falls,
k_trip the first code (descending, output starting low) at which it rises, and the stored code is

  k_cal = 32 + round((k_rel + k_trip)/2 − k_ideal),  k_ideal = 36.31 (OC) / 27.69 (NEG).

The two-sided search cancels the hysteresis. Revision 0.3 implements this as

  CAL = 32 + floor((k_rel + k_trip − IDEAL) / 2),  IDEAL = `CMP_CAL_IDEAL` field = floor(2 k_ideal),

which equals the contract formula for every k_rel + k_trip while k_ideal is not a multiple of
1/2 (checked on 274 MC comparator samples, README revision 0.3). A 6-bit integer IDEAL
(36 / 28) would differ by one code on 103 of the 274 samples, so the field is 7 bits in half codes.

To calibrate the comparator offsets, do these steps:

1. Set `PWM_PERIOD`, `AZ_START` and `AZ_CFG.AZ_LEN`. Each period must leave at least
   3 × (16 << CAL_STEP) + 4 ticks after the end of `az_win` (reset: 100 ticks).
2. Keep `AZ_CFG.THR_ZERO` = 14 and `CMP_CAL_IDEAL` at its reset value unless `r1_safe` changes.
3. Write `CTRL.CMP_CAL` = 1. The gates stay off during the search, so the shunt current is zero.
4. Wait until `STATUS.CAL_BUSY` = 0 (14 PWM periods).
5. Read `CMP_CAL_A/B`. An `EXH` bit = 1 means that the toggle points are outside the 6-bit range
   or that the result saturates; the code is then not valid.
6. Write the new `CAL_CRC` and `CTRL.CLR` (section 4.4).

During the search (`CAL_BUSY`): all four threshold outputs carry THR_ZERO, the gates are off,
and the comparator faults are blanked (and for 16 ticks after the search; the `AZ_EXT` mask applies in addition). The four comparators
are searched at the same time. Each decision uses the zero-current time after one `az_win`
(STEP = 16 << CAL_STEP ticks): STEP ticks of settling, the preset code for STEP ticks, the probe
code for STEP ticks, then the synchronised flag is sampled. If `az_win` starts again before the
sample, the decision is repeated in the next period.

- Pass R (release side): preset code 0, so the output is high before each probe. A flag = 1 at
  the probe means "not released". 6-bit successive approximation (start 32, flag = 1 keeps the
  bit), then one check window. Result a = the largest code with flag 1; k_rel = a + 1.
- Pass T (trip side): preset code 63, so the output is low before each probe. A flag = 1 means
  "tripped". Same successive approximation and check; k_trip = b = the largest code with flag 1.
- `EXH` = 1 if a pass ends at 63 with flag 1 or at 0 with flag 0, or if CAL saturates at 0 or 63.

The host can write the codes when no search runs; a search overwrites them. During a search,
`CMP_CAL_A/B` read the codes applied at that moment (preset or probe), not a result.

### 4.11 ADC weight correction (PLAN.md D12, D18)

| Addr | Name | Type | Reset | Format |
| --- | --- | --- | --- | --- |
| 0x50–0x5D | `ADC_A_W0`–`ADC_A_W13` | RW | nominal × 4 | [WW(i)-1:0] weight of decision i of slice A (SIN, ISA), units of 1/4 LSB; stored width WW(i) in the table below (0.4) |
| 0x60–0x6D | `ADC_B_W0`–`ADC_B_W13` | RW | nominal × 4 | [WW(i)-1:0] weight of decision i of slice B (COS, ISB), units of 1/4 LSB; same widths (0.4) |

ADC first-conversion discard (revision 0.5; `r1_adc` revision 5: the first conversion after the ADC is enabled is wrong, cause not found):

| Addr | Name | Type | Reset | Bits |
| --- | --- | --- | --- | --- |
| 0x3D | `ADC_CFG` | RW | 1 | [3:0] `DISCARD`: number of frames to drop after a reset of the macro (`por_n`) or a rising edge of `ANA_CTRL.ADC_ARM`; 0 = none, maximum 15. Bits 15:4 read 0. Not covered by `CAL_CRC` |

The frame generator counts the frames it starts after the arm event (reset or `ADC_ARM`). A frame whose number is below `DISCARD` is
dropped when its pair of corrected codes is complete: `sin_code`/`cos_code` (and `smp_valid`) or `i_a`/`i_b` keep their old values,
so the discarded conversion reaches neither the position path nor the current path. The rule applies to both frame types and
both slices together (the slices convert in parallel). Frame timing, `adc_hold`, `is_smp`, `smp_sh` and `LATE` are unchanged.
Bootstrap pre-charge (revision 0.5, binding from `INTERFACES.md` "ADC -> ctrl, first conversion"): after the reset release and after every
`ADC_ARM` rising edge, once no frame is converting, `adc_hold` is high for 2 ticks (no `adc_start`, no `smp_sh`) and then low for at least 11 ticks
(262 ns at 42 MHz) before the first frame may start. The first frame starts `PAIR_TICKS` ticks after the sequence starts (22: 20 ticks of track).
Current strobes that fall in the sequence are delayed (counted in `LATE`). The discard above stays on as the second layer.
A frame that started before the arm event is not dropped. The tracking loop sees one missing pair, as for any overrun. After
the arm the first pair is therefore missing: a reset needs `DISCARD` + 1 frames (22 ticks each) before the first valid position.

Stored width WW(i) (revision 0.4; was 14 bit for all): the bit length of the nominal weight plus 2,
at most 14. Higher bits read 0 and ignore writes. This is 4 x the nominal value, so the 1/8-LSB
unit proposed by `r1_adc` (2 x nominal) also fits.

| i | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| WW(i) bits | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 11 | 12 | 13 | 14 | 14 |
| largest value | 7 | 15 | 31 | 63 | 127 | 255 | 511 | 1023 | 2047 | 2047 | 4095 | 8191 | 16383 | 16383 |

Per slice: code = min(4095, (Σ raw[i] · W[i] + 2) >> 2), i = 0..13. raw[13] is the first (most
significant) decision. The reset weights are the nominal `r1_adc` revision-3 weights × 4,
rounded: W13…W0 = 8130, 4065, 2032, 1016, 508, 315, 158, 79, 39, 20, 10, 5, 2, 1 (sum 16380 =
4095 LSB). The host loads the measured weights of each slice; then it writes `CAL_CRC` (the
weights are covered, section 4.4). One-hot readback of raw decisions (revision 0.4, confirmed by simulation, no RAW register added). To
read decision bit i of a slice, write 4 to that slice's weight W_i and 0 to the other 13 weights. The
code is then exactly b_i (code = (W_i * b_i + 2) >> 2 = b_i; no clamp, because the sum is at most
W_i). Read it in `I_A` / `I_B` (0x29, 0x2A, current frame) or in `RAW_SIN` / `RAW_COS` (0x1D, 0x1E,
encoder frame). Any W_i = 4k gives code k * b_i exactly (k up to 4095, if the stored width of W_i
allows 4k; W_0 allows 4 only). The value 4 fits every stored width. A weight set with all but one
weight zero stops the position loop, so the bench does this with the gates off. Each weight write
clears `CAL_VALID`; the bench restores the weights, writes a new `CAL_CRC` and `CTRL.CLR`
(section 4.4). Evidence: `tb/tb_adcw_onehot.v`, 168 checks (14 decisions, 4 weight values, raw
all ones / bit clear / only bit set), 0 failed (`sim/results/r1ctrl_20261021_v04/adcw_onehot.log`).

Weight correction adds 4 ticks from `valid` to the code (four
decisions per tick). A weight write takes effect for the next conversion. The weight unit
(1/4 LSB) and the bit order are this map's contract; `r1_adc` revision 4 confirms them.

### 4.12 Write timing of configuration registers

Revision 0.3: all RW registers are flip-flops with a write enable (`R1_CFG_FLOPS` in
`rtl/r1_lib.v`). Revision 0.2 used latch words to save area; they failed sign-off STA at the
slow corner (README revision 0.3). A write changes the register at the clock edge that ends the
internal write pulse, 3–5 ticks after `CS_N` rises. The PWM shadow registers stay latch words
(loaded at the counter wrap); they pass sign-off STA in the flip-flop configuration.

Revision 0.4: each word is a bank of flip-flops on its own gated clock (`R1_CFG_GATED`, one clock gate per word) instead of enabled flip-flops. The write edge and the timing seen by the host are the same as in 0.3. The `PWM_PERIOD` shadow is a flip-flop word (no latch, no static logic loop); the duty and phase shadows stay latch words.

## 5. Position path (r1_pos) number formats

| Signal | Format |
| --- | --- |
| ADC codes | 12-bit offset binary, mid-scale 0x800 = 0 |
| Corrected x, y | 18 bit, 4 fractional bits, saturated at ±49151 (±3072 LSB) before the CORDIC |
| CORDIC | 18-bit x/y (0.1: 20 bit), 18-bit angle (2^18 = one turn), 18 iterations after a ±90° pre-rotation |
| H3 correction | θ ← θ − H3_AMP · sin(4θ + H3_PH), 256-entry sine table (8 bit) |
| Tracking loop | NCO θ (16.20 bit) += ω every tick; per pair e = θ_meas − θ(at hold); θ += e·2^−KP, ω += e·2^−KI |
| Output | POS = (±(θ + ω·EXTRAP)) − ZERO_OFS, registered every tick |

One pair is processed in 19 ticks (revision 0.3: two CORDIC iterations per tick; one shared
18 × 17 multiplier, also for the loop gains). A hold in the tick of the previous pair's
`smp_valid` belongs to the next pair. A pair that arrives while the previous pair is still being processed is dropped and counted in
`DIAG_SPI[11:8]`. RTL against the floating-point reference: ≤ 0.024° el (simulated, section 5 of
the README).

## 6. Interface to the analog blocks (macro ports)

| Port | Direction | Meaning |
| --- | --- | --- |
| `clk` | in | `r1_osc` output |
| `por_n` | in | power-on reset, active low (asynchronous assert, synchronous release after 2 `clk` edges); low = reset |
| `adc_hold` | out | high: both sin/cos track-and-holds hold (rising edge = sampling instant) |
| `is_smp` | out | high: both isense track-and-holds hold (rising edge = current sampling instant) |
| `adc_start`, `adc_sel` | out | one-tick pulse: both slices convert; `adc_sel` 0 = {SIN, COS}, 1 = {ISA, ISB} (stable during the conversion) |
| `cur_trk` | out | registered (0.7): 1 = the SAR logic connects the CDAC to ISA/ISB while idle (tracking before the current strobe); 0 = SIN/COS. High from the tick after the scheduler `soon` or `req` until the current frame starts; low during encoder frames |
| `adc_valid_a`, `adc_raw_a[13:0]` | in | slice A: one-tick pulse with the 14 raw decisions ([13] first); synchronous to `clk` |
| `adc_valid_b`, `adc_raw_b[13:0]` | in | slice B: the same |
| `cmp[3:0]` | in | comparator flags (0 OC_A, 1 NEG_A, 2 OC_B, 3 NEG_B), asynchronous, synchronised inside |
| `tap_p[31:0]`, `tap_n[31:0]` | out | `r1_safe` tap indices nP, nN, 8 bit per comparator, comparator i at [8i +: 8] (section 4.10; replace `thr_*` and `cal_*` of 0.3/0.4) |
| `az_win` | out | high: isense auto-zero window |
| `t2f_clk` | in | T2F oscillator, asynchronous, ≤ f_clk/4 |
| `osc_trim[4:0]` | out | to `r1_osc` |
| `pga_c[3:0]` | out | `r1_afe` gain vector `c1 c2 c3 c4` = `pga_c[0..3]` (section 4.8) |
| `t2f_en`, `t2f_mode` | out | `r1_t2f` `en` and `mode` |
| `bias_en` | out | `r1_bias` enable |
| `en_pad`, `cs_n`, `ma_sclk`, `sdi` | in | pads (level-shifted) |
| `slo_sdo`, `fault_n`, `gate_a/b/c` | out | pads |

The testbench ADC model delivers `adc_valid_a` 17 ticks and `adc_valid_b` 16 ticks after the
`adc_start` pulse (assumed; D18 binding conversion time ≤ 17 ticks). The encoder frame is then
22 ticks (section 4.6).

## 7. Change log

| Version | Date | Change |
| --- | --- | --- |
| 0.7 | 2026-10-27 | ID 0x5207. One new output port `cur_trk` (section 6; ADC SAR sub-macro, D21). `CMP_THR_A/B` reset 0x003F (was 0x3F3F: NEG cell code 0 tripped at zero current, r1_top finding R4). `EN` synchroniser reset 1 (`FAULT` after a power-up with `EN` high is 0x1800, finding R3). `OSC_TRIM` hardware lock with `STATUS.TRIM_UNLK` (bit 14) set by a qualifying `OSC_COUNT` read (section 4.3). New register `AZ_EXT` (0x3E, reset 120): comparator mask after `az_win`, replaces the fixed 16 ticks (section 4.6). |
| 0.1 | 2026-10-20 | first draft with the first RTL |
| 0.5 | 2026-10-21 | ID 0x5205. Ownership gaps of the r1_top assembly closed. Ports: `thr_*`, `cal_*` and `ana_ctrl` removed; added `tap_p[31:0]`, `tap_n[31:0]` (tap-index adders in `r1_tapidx`, section 4.10), `pga_c[3:0]`, `t2f_en`, `t2f_mode`, `bias_en`. `ANA_CTRL` (0x0C) reset 0x0028; bits 2:0 `PGA_GAIN` (decoder to the 4 AFE lines), 3 `T2F_EN` (reset 1), 4 `T2F_MODE`, 5 `BIAS_EN` (reset 1), 6 `ADC_ARM`. New register `ADC_CFG` (0x3D, `DISCARD` reset 1) and the first-conversion discard (section 4.11). Bootstrap pre-charge hold sequence after reset and `ADC_ARM` (section 4.11). `r1_biss`: the reset of the MA-domain flops is released through a registered `ma_rel` (CDC finding F), no function change. Bug fix in `r1_gate`: the encoder frame start compare was 8 bit and never fired after `PAIR_TICKS` had been 0 for more than 255 ticks; now 9 bit. No other register, bit meaning or reset value changed. |
| 0.4 | 2026-10-21 | ID 0x5204. Width changes only, no register, bit meaning or reset value removed (D10 area closure, S6 cut C2): `PWM_PERIOD`, `DUTY_A/B/C`, `PHASE_A/B/C`, `AZ_START` are 13 bit (bits 15:13 read 0, ignore writes; f_PWM at least 3.66 kHz at 30 MHz); ADC weights are stored in WW(i) bits (3 to 14, section 4.11). The configuration words are flip-flops on per-word gated clocks (section 4.12, implementation only). Documentation only: `ANA_CTRL` bit assignment (`PGA_GAIN` in 2:0), one-hot weight readback of raw decisions (section 4.11). |
| 0.3 | 2026-10-20 | ID 0x5203. Configuration registers are flip-flops again (section 4.12). Comparator calibration per the `r1_safe` revision-3 contract: two-sided search (release pass with preset 0, trip pass with preset 63, 14 windows), decisions after `az_win`, result relative to the new `CMP_CAL_IDEAL` (0x3C, half codes, reset 72 / 55). `AZ_CFG` 16 bit: THR_ZERO reset 14 (was 32), CAL_STEP bits 15:14 (reset 32 ticks); reset 0x4E00. `CAL_CRC` covers 0x10–0x17, 0x36–0x3C, 0x50–0x5D and 0x60–0x6D (was 0x10–0x17); a search clears `CAL_VALID`. Comparator blanking extended 16 ticks after a search. Host bring-up order in section 4.1 updated. D18: two ADC slices with 14 decisions each (`adc_raw_a/b`, `adc_valid_a/b`, one `adc_start` with `adc_sel`; `adc_mux` and the 13-bit port removed); weights per slice `ADC_A_W0`–`W13` (0x50–0x5D) and `ADC_B_W0`–`W13` (0x60–0x6D), reset = nominal `r1_adc` revision-3 weights × 4 (was `ADC_W0`–`ADC_W12`, binary); encoder frame every 22 ticks, the current frame replaces one encoder frame at the strobe and restarts the frame grid; `SCHED` reset 0x1416 (was 0x201E); weight correction 4 ticks (was 8); `r1_pos` 19 ticks per pair (was 28). |
| 0.2 | 2026-10-20 | ID 0x5202. AS5047P mode removed (`BUS_CFG` bit 8 reserved). `BUS_CFG.LAT_HALF` (bit 14, reset 1). Control channel per D2 (section 3.4): CTS in the header CRC, IDL0, R/W echo, W inverted on refusal, `S` echo, stop bit `P`, sequential read, BSEL refused, EDS_BANK readable. `CTRL.CMP_CAL`, `STATUS` bits 11–13, `CMP_THR_A/B`, `AZ_START`, `AZ_CFG`, `CMP_CAL_A/B`, `ADC_W0`–`ADC_W12`. One current strobe at the channel A centre; `is_smp`, `az_win` ports; 13-bit raw ADC port. `OSC_TRIM` reset 22. `TIMEOUT_TICKS` 12 bit, `TEMP`/`OT_LIM` 14 bit, diagnostic counters 4 bit saturating, KI clamped to 8–23. Configuration registers are latch words (section 4.12). |

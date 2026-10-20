# R1 bus protocols and register map (draft 0.2, 2026-10-20)

Owner block: `r1_ctrl` (`designs/r1-joint/blocks/r1_ctrl`). This document is the contract between
the host, the digital macro (`rtl/r1_ctrl_top.v`) and the analog blocks it connects to. It is a
draft: nothing here is on silicon. The RTL in `rtl/` implements this version (revision 0.2).
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
first falling edge, and the word is read at the first rising edge.

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
| 0x00 | `ID` | RO | 0x5202 | chip 'R', RTL revision 0.2 (0.1: 0x5210) |
| 0x01 | `STATUS` | RO | — | 0 AMP_LOW, 1 AMP_HIGH, 2 OVERSPEED, 3 TRACK_ERR, 4 CAL_VALID, 5 CLK_FAULT, 6 POS_VALID, 7 FAULT, 8 EN (synchronised), 9 GATE_ACTIVE, 10 OSC_DONE, 11 CAL_BUSY, 12 CAL_DONE, 13 CAL_EXH (any comparator) |
| 0x02 | `FAULT` | RO | 0x1800 | latched causes: 0–3 comparator flags `cmp[3:0]`, 4 OTEMP, 5 AMP, 6 OVERSPEED, 7 WDT, 8 STO (EN low), 9 I2T_A, 10 I2T_B, 11 CAL (CRC mismatch), 12 POR |
| 0x03 | `FAULT_MASK` | RW | 0x0000 | 1 = source does not latch; bits 8, 11, 12 cannot be masked |
| 0x04 | `CTRL` | RW | 0x0000 | 0 CLR (W1), 1 GATE_EN, 2 WDT_EN, 3 CMP_CAL (W1, section 4.10) |

`CLR` clears each `FAULT` bit whose source is inactive at that moment. Bit 11 stays set while the
calibration CRC does not match. After reset, the gates stay off until the host does these steps:

1. Write the calibration registers.
2. Write `CAL_CRC`.
3. Write `CTRL.CLR`.
4. Write `CTRL.GATE_EN`.

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
| 0x08 | `OSC_CFG` | RW | 0x0016 | 4:0 OSC_TRIM (to `r1_osc`, reset 22, PLAN.md D13), 8 MEAS (W1) |
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
| 0x17 | `POS_CFG` | RW | 0x0164 | 0 DIR, 4:1 KP (loop gain 2^−KP), 9:5 KI (2^−KI per tick; values outside 8–23 are clamped to 8 or 23) |
| 0x18 | `CAL_CRC` | RW | 0 | 7:0 CRC-8 of 0x10–0x17 |

`CAL_CRC` is CRC-8 with polynomial 0x07, initial value 0xFF, no reflection and no final XOR. It is
computed over the 16 bytes of 0x10..0x17 in address order, high byte first, with the unused bits
as 0 (the values that read back). The hardware checks it continuously. A write to 0x10..0x18
clears `CAL_VALID` until the next complete check (≤ 32 ticks). S1 lists `PHASE` as 10 bit with
a LUT. R1 uses two host-computed words (sin α, 1/cos α) instead, so no LUT is needed.
`CAL_CRC` does not cover the comparator words (0x36–0x3B) or the ADC weights (0x50–0x5C).

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
| 0x35 | `LATE` | RO | 0 | [3:0] current pairs that started after their strobe (saturating) |
| 0x38 | `AZ_START` | RW | 0 | counter value at which `az_win` starts |
| 0x39 | `AZ_CFG` | RW | 0x2000 | 7:0 AZ_LEN (ticks; 0 = no window), 13:8 THR_ZERO (section 4.10) |

Channel x is on while DEAD ≤ (cnt − PHASE_x) mod PERIOD < DUTY_x − DEAD. The gate output is the
registered PWM AND `GATE_ACTIVE` AND the `EN` pad. PERIOD, DUTY and PHASE take effect at the
counter wrap. `GATE_ACTIVE` is 0 while a comparator calibration runs.

Current sampling (0.2): one strobe per period at the centre of the channel A window
(PHASE_A + DUTY_A/2), when DUTY_A ≥ 2·DEAD + 2. At the strobe `is_smp` goes high (both isense
track-and-holds hold), and ISA then ISB are converted. Channel B is therefore sampled at the
channel A centre. For a centred PWM pattern (PHASE_x = C − DUTY_x/2) all windows share that
centre. (0.1: separate strobes at the A and B centres.)

Sin/cos pairs: a pair does not start when a strobe is due within GUARD ticks; GUARD must cover
two conversions. A pair also does not start before the corrected COS code of the previous pair
is out of the weight correction (section 4.11). The pair period is therefore
max(PAIR_TICKS, 2 conversions + about 9 ticks): about 35 ticks with the testbench ADC model
(estimate from the testbench timing, not measured separately).

Auto-zero window: `az_win` is high for AZ_LEN ticks from counter value AZ_START. The host puts
it where both low-side FETs are off. The comparator flags are blanked during `az_win` and for
16 ticks after it.

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
| 0x0C | `ANA_CTRL` | RW | 0 | 16 bits to the analog blocks (PGA gain, enables); bit assignment open until the AFE/ADC/T2F interfaces are written |

### 4.9 BiSS identification (0x40–0x7F)

A native SPI read of 0x40–0x7F returns the BiSS byte in [7:0].

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
| 0x36 | `CMP_THR_A` | RW | 0x3F3F | 5:0 THR_OC_A, 13:8 THR_NEG_A (to `r1_safe`) |
| 0x37 | `CMP_THR_B` | RW | 0x3F3F | 5:0 THR_OC_B, 13:8 THR_NEG_B |
| 0x3A | `CMP_CAL_A` | RW | 0x2020 | 5:0 CAL_OC_A, 6 EXH_OC_A (RO), 13:8 CAL_NEG_A, 14 EXH_NEG_A (RO) |
| 0x3B | `CMP_CAL_B` | RW | 0x2020 | 5:0 CAL_OC_B, 6 EXH_OC_B (RO), 13:8 CAL_NEG_B, 14 EXH_NEG_B (RO) |

Comparator order of `cmp[3:0]` and `FAULT[3:0]`: 0 OC_A, 1 NEG_A, 2 OC_B, 3 NEG_B. The meaning of
the 6-bit threshold and calibration codes (step size, polarity) is set by `r1_safe`; see open
issue in the README.

To calibrate the comparator offsets, do these steps:

1. Set `PWM_PERIOD`, `AZ_START` and `AZ_CFG.AZ_LEN` so that `az_win` falls where the isense
   inputs are at zero current. Set `AZ_CFG.THR_ZERO` to the threshold code for 0 A.
2. Write `CTRL.CMP_CAL` = 1 (with `GATE_EN` as required).
3. Wait until `STATUS.CAL_BUSY` = 0 (7 PWM periods).
4. Read `CMP_CAL_A/B`. An `EXH` bit = 1 means the offset is outside the 6-bit range.

During the search (`CAL_BUSY`): all four threshold outputs carry THR_ZERO, the gates are off,
and the comparator faults are blanked. The search is a successive approximation over the four
comparators at the same time: start at 32, one decision per `az_win` (taken at the last tick of
the window), 6 decisions, then one check window. A flag = 1 at the decision raises the code.
Result: the largest code at which the flag is 1. `EXH` = 1 when the result is 63 and the flag is
still 1, or 0 and the flag is still 0. The host can write the codes when no search runs; a
search overwrites them.

### 4.11 ADC weight correction (PLAN.md D12)

| Addr | Name | Type | Reset | Format |
| --- | --- | --- | --- | --- |
| 0x50–0x5B | `ADC_W0`–`ADC_W11` | RW | 4 × 2^i | [13:0] weight of binary decision i, units of 1/4 LSB |
| 0x5C | `ADC_W12` | RW | 256 | [13:0] weight of the redundant decision (nominal 64 LSB) |

code = min(4095, (Σ raw[i] · ADC_W[i] + 2) >> 2). The reset weights are binary, so an ADC with
raw[12] = 0 gives the plain 12-bit code. All four channels use the same weights. Weight
correction adds 8 ticks from `adc_valid` to the code. A weight write takes effect for the next
conversion.

### 4.12 Write timing of configuration registers

All RW registers except `CTRL` and `OSC_CFG.MEAS` are latch words (revision 0.2, to save area).
A write changes the register in the tick after the internal write pulse, 3–5 ticks after
`CS_N` rises. The value is stable for the rest of the `CS_N` high time and after it. The PWM
shadow registers are latch words too; they load at the counter wrap, as in 0.1.

## 5. Position path (r1_pos) number formats

| Signal | Format |
| --- | --- |
| ADC codes | 12-bit offset binary, mid-scale 0x800 = 0 |
| Corrected x, y | 18 bit, 4 fractional bits, saturated at ±49151 (±3072 LSB) before the CORDIC |
| CORDIC | 18-bit x/y (0.1: 20 bit), 18-bit angle (2^18 = one turn), 18 iterations after a ±90° pre-rotation |
| H3 correction | θ ← θ − H3_AMP · sin(4θ + H3_PH), 256-entry sine table (8 bit) |
| Tracking loop | NCO θ (16.20 bit) += ω every tick; per pair e = θ_meas − θ(at hold); θ += e·2^−KP, ω += e·2^−KI |
| Output | POS = (±(θ + ω·EXTRAP)) − ZERO_OFS, registered every tick |

One pair is processed in 28 ticks (one shared 18 × 17 multiplier, also for the loop gains). A
pair that arrives while the previous pair is still being processed is dropped and counted in
`DIAG_SPI[11:8]`. RTL against the floating-point reference: ≤ 0.024° el (simulated, section 5 of
the README).

## 6. Interface to the analog blocks (macro ports)

| Port | Direction | Meaning |
| --- | --- | --- |
| `clk` | in | `r1_osc` output |
| `por_n` | in | power-on reset, active low (asynchronous assert, synchronous release) |
| `adc_hold` | out | high: both sin/cos track-and-holds hold (rising edge = sampling instant) |
| `is_smp` | out | high: both isense track-and-holds hold (rising edge = current sampling instant) |
| `adc_start`, `adc_mux[1:0]` | out | one-tick pulse: convert channel 0 SIN T&H, 1 COS T&H, 2 ISA, 3 ISB (the mux is stable during the conversion) |
| `adc_valid`, `adc_raw[12:0]` | in | one-tick pulse with the 13 raw decisions: [11:0] binary (11 = MSB), [12] redundant; synchronous to `clk` |
| `cmp[3:0]` | in | comparator flags (0 OC_A, 1 NEG_A, 2 OC_B, 3 NEG_B), asynchronous, synchronised inside |
| `thr_oc_a`, `thr_neg_a`, `thr_oc_b`, `thr_neg_b` [5:0] | out | comparator threshold codes (THR_ZERO during a calibration) |
| `cal_oc_a`, `cal_neg_a`, `cal_oc_b`, `cal_neg_b` [5:0] | out | comparator offset calibration codes |
| `az_win` | out | high: isense auto-zero window |
| `t2f_clk` | in | T2F oscillator, asynchronous, ≤ f_clk/4 |
| `osc_trim[4:0]` | out | to `r1_osc` |
| `ana_ctrl[15:0]` | out | analog control word |
| `en_pad`, `cs_n`, `ma_sclk`, `sdi` | in | pads (level-shifted) |
| `slo_sdo`, `fault_n`, `gate_a/b/c` | out | pads |

The testbench ADC model delivers `adc_valid` 13 ticks after `adc_start` (assumed). With weight
correction, the sin/cos pair period is then about 35 ticks (section 4.6).

## 7. Change log

| Version | Date | Change |
| --- | --- | --- |
| 0.1 | 2026-10-20 | first draft with the first RTL |
| 0.2 | 2026-10-20 | ID 0x5202. AS5047P mode removed (`BUS_CFG` bit 8 reserved). `BUS_CFG.LAT_HALF` (bit 14, reset 1). Control channel per D2 (section 3.4): CTS in the header CRC, IDL0, R/W echo, W inverted on refusal, `S` echo, stop bit `P`, sequential read, BSEL refused, EDS_BANK readable. `CTRL.CMP_CAL`, `STATUS` bits 11–13, `CMP_THR_A/B`, `AZ_START`, `AZ_CFG`, `CMP_CAL_A/B`, `ADC_W0`–`ADC_W12`. One current strobe at the channel A centre; `is_smp`, `az_win` ports; 13-bit raw ADC port. `OSC_TRIM` reset 22. `TIMEOUT_TICKS` 12 bit, `TEMP`/`OT_LIM` 14 bit, diagnostic counters 4 bit saturating, KI clamped to 8–23. Configuration registers are latch words (section 4.12). |

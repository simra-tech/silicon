# G1 serial protocol and register map

Owner block: `G1_CTRL` (`blocks/g1_ctrl`). Version 1.1, 2026-09-19 (change
log in section 7). This document is the contract between the host software,
the digital core (`g1_digital_top`) and the analog blocks it drives. The RTL in
`blocks/g1_ctrl/rtl` and `blocks/g1_seu/rtl` implements exactly this map; the
testbench `blocks/g1_ctrl/sim/tb_g1_digital.v` checks every register against it.
The analog side of the same contract is `blocks/g1_trip/INTERFACE.md` (breaker
path) and `blocks/g1_t2f/INTERFACE.md` (sensor control bits).

All time windows are expressed in cycles of the internal oscillator `osc_clk`
(`G1_OSC`), nominally 10 MHz. The oscillator is uncalibrated: **times below assume 10 MHz; an assumed 8–12 MHz range makes time
+25%/−16.7% relative to nominal**. The host can measure the
actual frequency through `OSC_CNT` (section 4.5) and correct its settings.

## 1. Three-wire serial interface

Pins: `SCLK` (14, in), `SDI` (15, in), `SDO` (16, out). There is no chip
select. The protocol is SPI mode 0 (CPOL = 0, CPHA = 0): `SCLK` idles low,
`SDI` is sampled on the rising edge, `SDO` changes on the falling edge and is
stable at the next rising edge. Bytes are sent MSB first.

### 1.1 Frames

A frame starts with a command byte:

| Bit | Meaning |
| --- | --- |
| 7 | `R/nW`: 1 = read, 0 = write |
| 6:0 | register address, `0x00` to `0x7F` |

**Write frame, 16 clocks**: command byte, then the data byte on `SDI`. The
register is updated a few `osc_clk` cycles after the 16th rising edge. `SDO`
is 0 throughout.

**Read frame, 24 clocks**: command byte, one turnaround byte (host sends
don't-care, `SDO` is 0), then the data byte on `SDO`, MSB first, driven on the
falling edges after clocks 16 to 23 and sampled by the host on rising edges
17 to 24.

```
SCLK  1  2  3  4  5  6  7  8   9 ... 16   17 ... 24
SDI   R  A6 A5 A4 A3 A2 A1 A0  x ... x    x  ... x
SDO   0  0  0  0  0  0  0  0   0 ... 0    D7 ... D0      (read frame)
SDI   0  A6 A5 A4 A3 A2 A1 A0  D7 ... D0                 (write frame)
```

The turnaround byte exists because the register file lives in the `osc_clk`
domain: the address is handed across with a toggle synchroniser, the register
is read once into a holding register, and the holding register is quasi-static
by the time the `SCLK` domain starts shifting it out (section 1.3).

### 1.2 Frame synchronisation

Because there is no chip select, the slave counts clocks. Framing is restored
by an idle timeout: when `SCLK` has been low for 64 `osc_clk` cycles
(nominally 6.4 µs) the bit counter is reset and the next rising edge begins a
new frame. Rules for the host:

- between frames, either continue immediately (back-to-back frames are legal,
  the counter wraps at 16 or 24) or hold `SCLK` low for **at least 128
  `osc_clk` cycles (nominally 12.8 µs, 16 µs with the −20 % oscillator)**;
- never start a frame between 64 and ~80 `osc_clk` cycles of idle: the reset
  pulse is active there and the first edge could be lost;
- after power-up or `EN` rising, wait the same 128 cycles before the first
  frame;
- to recover from any suspected loss of sync, hold `SCLK` low for 128 cycles.

### 1.3 Clock domains and speed

`SCLK` may run up to the `osc_clk` frequency (**`f_SCLK` ≤ `f_OSC`, i.e.
≤ 8 MHz for a −20 % oscillator**). The digital core has two clock domains:

| Domain | Contents |
| --- | --- |
| `SCLK` | bit counter, 7-bit input shift register (plus the live `SDI` bit), command address latch, write address/data latches, `wr_toggle`, `rd_toggle`, output shift register and `SDO` flop (falling edge) |
| `osc_clk` | everything else: register file, trip timer, SEU scrubber, counters |

Handoffs:

- **Write**: at the 16th rising edge the `SCLK` domain latches address and data
  into holding registers and flips `wr_toggle`. The `osc_clk` domain passes
  `wr_toggle` through a two-flop synchroniser, detects the edge and performs
  one register write. Address and data are stable from the 16th edge of one
  frame until the 16th edge of the next, so they are sampled at least
  16 `SCLK` periods minus 3 `osc_clk` periods after they settled.
- **Read**: at the 8th rising edge the address is latched and `rd_toggle`
  flips. The `osc_clk` domain synchronises it (2 flops + edge detect), reads
  the addressed register into `rd_hold[7:0]`, and if the address is the low
  byte of a 16-bit counter also copies the high byte into `hi_hold[7:0]`
  (section 4, "L/H pairs"). Total latency ≤ 4 `osc_clk`. `rd_hold` is then
  untouched until the next read. The `SCLK` domain loads `rd_hold` at the
  falling edge after the 16th rising edge, 7.5 `SCLK` periods after the
  address was latched. With `f_SCLK` ≤ `f_OSC` there is a margin of at least
  3.5 `osc_clk` cycles between the last change of `rd_hold` and its capture.
- **Frame reset**: generated in `osc_clk` from the synchronised `SCLK` (idle
  counter), applied as an asynchronous clear to the `SCLK`-domain bit counter
  for 16 `osc_clk` cycles starting at idle count 64. It can only fire while
  `SCLK` is idle, which is why the host must not start a frame in that
  window (section 1.2).
- **Reset**: the chip reset (`EN` low or power-on, section 3) is asynchronous
  to both domains and released synchronously to `osc_clk`.

In static timing the two clocks are declared asynchronous
(`set_clock_groups -asynchronous`); all cross-domain paths go through the
synchronisers above and are excluded from setup/hold analysis.

## 2. Analog interface of the digital core

Signals between `g1_digital_top` (1.2 V) and the analog blocks. Names follow
`blocks/g1_trip/INTERFACE.md` and `blocks/g1_t2f/INTERFACE.md`. Every signal
of the breaker path is 1.2 V logic on both sides (the G1_GATE latch has its own
shifters); only the three sensor/bandgap control bits enter the 3.3 V domain,
through one `g1_ls_up` cell each (`blocks/g1_ctrl/ls/`).

| Signal | Dir (core) | Width | To / from | Meaning |
| --- | --- | --- | --- | --- |
| `osc_clk` | in | 1 | `G1_OSC` | ~10 MHz clock, ±20 % untrimmed |
| `osc_en` | out | 1 | `G1_OSC` | 1 = oscillator runs (`OSC_CTRL.OSC_EN`, reset 1) |
| `osc_trim[3:0]` | out | 4 | `G1_OSC` | capacitor trim, code 8 nominal, ~2.7 %/LSB (`OSC_CTRL`) |
| `por_n` | in | 1 | analog wrapper | power-on reset, active low; tie high if no POR cell exists |
| `en` | in | 1 | `EN` pad (`en_core`) | enable; low resets the digital core (section 3) |
| `sclk`, `sdi` | in | 1 | pads | serial interface |
| `sdo` | out | 1 | pad | serial data out |
| `cmp_clk` | out | 1 | `G1_TRIP` | comparator strobe = `osc_clk`/2 (5 MHz nominal, 50 % duty). Soft comparator decides on the rising edge, hard comparator on the falling edge |
| `cmp_soft` | in | 1 | `G1_TRIP` soft comparator | 1 = shunt voltage above the soft threshold; updated once per `cmp_clk` rising edge and held |
| `cmp_hard` | in | 1 | `G1_TRIP` hard comparator | same, updated on the falling edge |
| `dac_soft[7:0]` | out | 8 | `G1_TRIP` soft DAC | **effective** code = `DAC_SOFT` − hysteresis + `SENSE_OFS`, saturated at 0/255; shunt threshold = code × 0.196 mV × (V<sub>REF</sub>/1.04 V), full scale 50 mV |
| `dac_hard[7:0]` | out | 8 | `G1_TRIP` hard DAC | effective code = `DAC_HARD` + `SENSE_OFS`, saturated |
| `trip_set_sel` | out | 1 | `G1_TRIP` | 1 = hard comparator reference from the `TRIP_SET` pad instead of `dac_hard` |
| `trip_d` | out | 1 | `G1_GATE` | level = digital trip latch; 1 sets the 3.3 V trip latch |
| `clr_d` | out | 1 | `G1_GATE` | 2-cycle pulse (200 ns nominal, ≥ 160 ns at +20 % clock) on every `CLEAR` command and every retrigger re-enable; clears the 3.3 V latch, reset-dominant |
| `fast_en` | out | 1 | `G1_GATE` | 1 = analog fast path `cmp_hard` → latch, bypassing `HARD_N` and the inrush mask (`MODE.FAST_EN`, reset 0) |
| `tripped` | in | 1 | `G1_GATE` | 3.3 V latch state, level-shifted inside G1_GATE; synchronised here, read as `STATUS2.TRIPPED_A`; a set the core did not command is adopted as a trip with cause "hard" (section 5) |
| `trip`, `gate_en`, `fault_n`, `trip_cause[1:0]` | out | 1, 1, 1, 2 | test / monitor | digital latch state, `en & ~trip`, `~trip`, cause (0 none, 1 soft, 2 hard, 3 forced). The `GATE` and `FAULT_N` pads are driven by G1_GATE, not by these |
| `t2f_en` | out | 1 | `g1_ls_up` → `g1_t2f.en` | `TEMP_CTRL.T2F_EN` (reset 1) |
| `t2f_mode` | out | 1 | `g1_ls_up` → `g1_t2f.mode` | `TEMP_CTRL.T2F_MODE`: 0 PTAT, 1 REF (reset 0) |
| `bgr_r4` | out | 1 | `g1_ls_up` → `g1_bgr.r4` | `TEMP_CTRL.BGR_R4`: 1 = HBT ratio test 1:4 (reset 0) |
| `clk_div_out` | out | 1 | test mux (optional) | `osc_clk / 2^(9+OSC_DIV)` square wave |

Both DAC codes are plain fractions of the sense full scale; nothing in this
map expresses a threshold as a multiple of a nominal current. The
G1_SENSE/G1_TRIP scaling (`INTERFACE.md`) puts the nominal load current at
25 mV = code 128; the reset codes below are 1.2 × and 2.0 × nominal.

## 3. Reset and `EN`

There is no reset pin. The digital reset is asserted asynchronously when
`por_n` is low **or `EN` is low**, and released synchronously to `osc_clk` two
cycles after both are high. `EN` low therefore restores all registers to
their reset values; a host that changes the configuration must rewrite it
after each `EN` cycle. With no host at all the chip runs as a breaker on the
reset values of section 4, which are chosen for that case:

| Behaviour with no serial traffic | Reset value |
| --- | --- |
| hard threshold | code 0xFE (49.8 mV shunt, 2.0 × nominal), 4 consecutive comparator decisions (0.8 µs) |
| soft threshold | code 0x99 (30.0 mV shunt, 1.2 × nominal), trip-off window ~1 ms, symmetric up/down |
| analog fast path | off (`FAST_EN` = 0); oscillator on, trim mid code; sensor on, PTAT mode |
| inrush mask after `EN` | ~1 ms |
| mode | latched: a trip holds until `EN` is cycled |
| SEU scrubber | running, alternating pattern |

## 4. Register map

Access: RW = read/write, RO = read only (writes ignored), WO = write only,
self-clearing (reads as 0x00). Unmapped addresses read 0x00 and ignore writes.
Reserved bits read 0 and must be written 0.

**L/H pairs**: 16-bit values are read low byte first. Reading the `_L` byte
copies the `_H` byte into a holding register in the same `osc_clk` cycle, and
the following `_H` read returns that copy, so the pair is consistent even if
the counter increments between the two frames. Writing 16-bit configuration
values (`SOFT_TIME`) takes effect byte by byte; write `_H` then `_L`, or write
while the soft path is disabled.

### 4.1 Identification

| Addr | Name | Access | Reset | Description |
| --- | --- | --- | --- | --- |
| 0x00 | `CHIP_ID` | RO | 0x47 | 'G' |
| 0x01 | `VERSION` | RO | 0x11 | register map version, `major.minor` in two nibbles (1.1) |

### 4.2 Trip thresholds and timing

| Addr | Name | Access | Reset | Description |
| --- | --- | --- | --- | --- |
| 0x02 | `DAC_SOFT` | RW | 0x99 | soft threshold DAC code, fraction of the shunt full scale (0.196 mV/LSB, 50 mV at 0xFF); 0x99 = 30.0 mV. The code driven to the DAC is `DAC_SOFT` − hysteresis + `SENSE_OFS` (0x2A) |
| 0x03 | `DAC_HARD` | RW | 0xFE | hard threshold DAC code, same scale; 0xFE = 49.8 mV. Driven as `DAC_HARD` + `SENSE_OFS` (0x2B) |
| 0x04 | `SOFT_TIME_L` | RW | 0x27 | soft trip-off window, low byte |
| 0x05 | `SOFT_TIME_H` | RW | 0x00 | soft trip-off window, high byte. Window = `SOFT_TIME` × 256 `osc_clk` cycles: 25.6 µs per LSB, 0x0027 = 9984 cycles ≈ 1.0 ms, 0x030D ≈ 20 ms, maximum 0xFFFF ≈ 1.68 s. 0x0000 trips on the first sample above threshold. |
| 0x06 | `SOFT_CFG` | RW | 0x00 | bits 1:0 `DECAY`: rate at which the soft counter counts down while `cmp_soft` is low: 0 = 1 per sample (symmetric), 1 = 1 per 4 samples, 2 = 1 per 16, 3 = 1 per 64. Bit 2 `HYST_EN`: while the soft counter is above zero, `dac_soft` is lowered by 1 LSB (bit 3 = 0) or 2 LSB (bit 3 `HYST_2` = 1), giving digital hysteresis on the soft comparator. Bits 7:4 reserved. |
| 0x07 | `HARD_N` | RW | 0x04 | hard path: trip when `cmp_hard` has been high for `HARD_N` consecutive comparator decisions (one per `cmp_clk` period = 2 `osc_clk` = 200 ns; 1 to 255; 0 behaves as 1). Counter clears on any low decision. 0x04 = 0.8 µs, 0xFF = 51 µs. |
| 0x08 | `INRUSH` | RW | 0x14 | inrush mask: after reset release (`EN` rising) and after every retrigger re-enable, both trip paths are masked for `INRUSH` × 512 cycles: 51.2 µs per LSB, 0x14 = 10240 cycles ≈ 1.0 ms, 0xC3 ≈ 10 ms. 0 = no mask. |
| 0x09 | `HOLD_TIME` | RW | 0x0C | retrigger hold: time the gate stays off after a trip before re-enabling, `HOLD_TIME` × 8192 cycles: 0.82 ms per LSB, 0x0C ≈ 9.8 ms, 0xF4 ≈ 200 ms. 0 behaves as 1. Also the cool-down after which a successful re-enable resets the retry count. |
| 0x0A | `RETRY_MAX` | RW | 0x03 | retrigger give-up count: number of automatic re-enables before the breaker falls back to latched behaviour. 0xFF = unlimited. |

### 4.3 Mode, control and status

| Addr | Name | Access | Reset | Description |
| --- | --- | --- | --- | --- |
| 0x0B | `MODE` | RW | 0x03 | bit 0 `SOFT_EN`, bit 1 `HARD_EN`: enable each trip path. Bit 2 `RETRIG`: 0 = latched (trip holds until `CLEAR` or `EN` cycle), 1 = retrigger after `HOLD_TIME`, up to `RETRY_MAX` times. Bit 3 `TRIP_SET_SEL`: hard comparator reference from the `TRIP_SET` pad. Bit 4 `FORCE_TRIP`: level; while 1 the breaker is tripped with cause "forced" (a `CLEAR` while it is set re-trips at once). Bit 5 `FAST_EN` (v1.1): enable the G1_GATE analog fast path, `cmp_hard` sets the 3.3 V latch directly with no filter and no inrush mask; the core adopts the trip (cause "hard"). Bits 7:6 reserved. |
| 0x0C | `CTRL` | WO | — | self-clearing command bits. Bit 0 `CLEAR`: clear the trip latch, cause, retry count and hold timer; the inrush mask does **not** restart. Bit 1 `CLR_TRIP_CNT`: zero `TRIP_CNT`. Bit 2 `CLR_PEAK`: zero `SOFT_PEAK`. Bit 3 `CLR_OSC_CNT`: zero `OSC_CNT`. Others ignored. |
| 0x0D | `STATUS` | RO | 0x80 | bit 0 `TRIPPED`. Bits 2:1 `CAUSE`: 0 none, 1 soft, 2 hard, 3 forced (latched at the trip, cleared with the latch). Bit 3 `INRUSH_ACTIVE`. Bit 4 `HOLDING`: in retrigger hold. Bit 5 `GAVE_UP`: retries exhausted, now latched. Bit 6 `SOFT_ARMED`: soft counter above zero. Bit 7 `EN`: always reads 1 (the register is unreadable while `EN` is low). |
| 0x0E | `STATUS2` | RO | — | bit 0 `CMP_SOFT`, bit 1 `CMP_HARD`: synchronised comparator inputs. Bit 2 `GATE_EN`. Bit 3 `TRIPPED_A` (v1.1): synchronised state of the G1_GATE 3.3 V trip latch. Bits 7:4 `RETRY_CNT`: re-enables performed in the current retrigger sequence (saturates at 15 for display). |
| 0x0F | `TRIP_CNT_L` | RO | 0x00 | trip events since reset or `CLR_TRIP_CNT`, 16-bit saturating, low byte (latches `_H`) |
| 0x10 | `TRIP_CNT_H` | RO | 0x00 | high byte |
| 0x11 | `SOFT_PEAK_L` | RO | 0x00 | highest value the soft counter reached since reset or `CLR_PEAK`, in the units of `SOFT_TIME` (256 cycles), low byte (latches `_H`) |
| 0x12 | `SOFT_PEAK_H` | RO | 0x00 | high byte |

### 4.4 SEU monitor (`G1_SEU`)

| Addr | Name | Access | Reset | Description |
| --- | --- | --- | --- | --- |
| 0x18 | `SEU_CTRL` | RW | 0x01 | bit 0 `SCRUB_EN`: compare and count (the registers shift regardless). Bits 2:1 `PATTERN`: 0 = checkerboard (alternating 0/1, 0x55 stream, every flop toggles each clock: dynamic test), 1 = all zeros, 2 = all ones (flops hold static data while clocked: static test), 3 = checkerboard. Bits 7:3 reserved. Enabling or changing `PATTERN` restarts the 256-shift fill in the built configuration. |
| 0x19 | `SEU_CMD` | WO | — | self-clearing. Bit 0 `CLR_CNT`: zero the SEU counters and `SEU_RUN`. Bit 1 `INJ_PLAIN`: invert one bit entering the plain register (self-test; one `SEU_PLAIN` count after propagation through the built 256-stage chain). Bit 2 `INJ_TMR`: invert one bit entering copy A of the TMR register (one `SEU_CORR` count, no `SEU_UNC`). Others ignored. |
| 0x1A | `SEU_STATUS` | RO | — | bit 0 `ACTIVE`: comparing; bit 1 `FILLING`. Bits 7:2 reserved. |
| 0x1B | `SEU_PLAIN_L` | RO | 0x00 | bit errors at the output of the plain register, 16-bit saturating (latches `_H`) |
| 0x1C | `SEU_PLAIN_H` | RO | 0x00 | |
| 0x1D | `SEU_CORR_L` | RO | 0x00 | corrected events: clocks in which any stage of the TMR register had a disagreeing copy, 16-bit saturating (latches `_H`) |
| 0x1E | `SEU_CORR_H` | RO | 0x00 | |
| 0x1F | `SEU_UNC` | RO | 0x00 | uncorrectable: TMR register output ≠ expected (two or more copies of one stage wrong), 8-bit saturating |
| 0x20 | `SEU_RUN` | RO | 0x00 | longest run of consecutive erroneous bits seen at the plain output since reset or `CLR_CNT`, 8-bit saturating |

### 4.5 Oscillator

| Addr | Name | Access | Reset | Description |
| --- | --- | --- | --- | --- |
| 0x24 | `OSC_CNT_L` | RO | 0x00 | free-running 16-bit counter of `osc_clk / 2^(8+OSC_DIV)`, low byte (latches `_H`). At 10 MHz with `OSC_DIV` = 0 it increments every 25.6 µs and wraps every 1.68 s. Two reads a known host time apart give `f_OSC`; `OSC_CTRL.OSC_TRIM` (0x28) then corrects it. |
| 0x25 | `OSC_CNT_H` | RO | 0x00 | |
| 0x26 | `OSC_DIV` | RW | 0x00 | bits 2:0: prescaler exponent added to 8 for `OSC_CNT` and used for `clk_div_out` = `osc_clk / 2^(9+OSC_DIV)`. Bits 7:3 reserved. |

### 4.6 Analog trim and control (added in 1.1)

| Addr | Name | Access | Reset | Description |
| --- | --- | --- | --- | --- |
| 0x27 | `SENSE_OFS` | RW | 0x00 | sense-path offset trim, 8-bit two's complement (−128 to +127). Added to both DAC codes before they are driven, with saturation at 0 and 255; LSB = 0.196 mV shunt-referred, the register spans −25.1 to +24.9 mV, but the usable DAC range is smaller near either endpoint (historical revision-A SENSE MC σ≈4 mV). Applied after the digital hysteresis on the soft code. Available correction is limited by each nominal threshold: at reset hard code 254 only +1 is usable without clipping. With a bracketed interior known-current crossing, use crossing code minus ideal code (positive crossing shift requires positive correction); see the top-level acceptance contract. Analog calibration qualification is incomplete. |
| 0x28 | `OSC_CTRL` | RW | 0x18 | bits 3:0 `OSC_TRIM`: G1_OSC capacitor trim, 8 = nominal, higher = slower (~2.7 %/LSB, `blocks/g1_osc/README.md`). Bit 4 `OSC_EN`: 1 = oscillator runs. **Writing 0 stops the clock of the core itself**: the register file, timers and scrubber halt and the serial interface can no longer complete a write; the only recovery is an `EN` cycle or power-on, which restores the reset value. Provided for test only. Bits 7:5 reserved. |
| 0x29 | `TEMP_CTRL` | RW | 0x01 | bit 0 `T2F_EN`: 1 = sensor oscillator runs, `TEMP_OUT` toggles. Bit 1 `T2F_MODE`: 0 = PTAT (f ∝ T), 1 = REF (f ≈ constant); the ratio of the two readings removes C, the threshold and the comparator delay. Bit 2 `BGR_R4`: 1 = bandgap HBT ratio test 1:4 (diagnostic; V<sub>REF</sub> and all thresholds fall by about 12 %, do not use while the breaker is armed). Bits 7:3 reserved. All three go to the 3.3 V domain through `g1_ls_up`. |
| 0x2A | `DAC_SOFT_EFF` | RO | 0x99 | the code currently driven on `dac_soft[7:0]` (register − hysteresis + offset, saturated) |
| 0x2B | `DAC_HARD_EFF` | RO | 0xFE | the code currently driven on `dac_hard[7:0]` |

### 4.7 Address summary

```
0x00 CHIP_ID       0x08 INRUSH        0x10 TRIP_CNT_H    0x18 SEU_CTRL      0x20 SEU_RUN       0x28 OSC_CTRL
0x01 VERSION       0x09 HOLD_TIME     0x11 SOFT_PEAK_L   0x19 SEU_CMD       0x24 OSC_CNT_L     0x29 TEMP_CTRL
0x02 DAC_SOFT      0x0A RETRY_MAX     0x12 SOFT_PEAK_H   0x1A SEU_STATUS    0x25 OSC_CNT_H     0x2A DAC_SOFT_EFF
0x03 DAC_HARD      0x0B MODE                             0x1B SEU_PLAIN_L   0x26 OSC_DIV       0x2B DAC_HARD_EFF
0x04 SOFT_TIME_L   0x0C CTRL                             0x1C SEU_PLAIN_H   0x27 SENSE_OFS
0x05 SOFT_TIME_H   0x0D STATUS                           0x1D SEU_CORR_L
0x06 SOFT_CFG      0x0E STATUS2                          0x1E SEU_CORR_H
0x07 HARD_N        0x0F TRIP_CNT_L                       0x1F SEU_UNC
```

## 5. Trip timer behaviour

All inputs are sampled every `osc_clk` through two-flop synchronisers
(latency 2 cycles, 0.2 µs nominal). The comparators are dynamic and decide once
per `cmp_clk` period (2 `osc_clk`): the soft comparator on the rising edge, the
hard comparator on the falling edge, each output held by the comparator's own
latch until its next decision.

**Soft path.** A 24-bit up/down counter counts up by one every sample in
which `cmp_soft` is high and down (at the `DECAY` rate) while it is low,
never below zero. When it reaches `SOFT_TIME` × 256 the breaker trips with
cause "soft". A short overcurrent therefore charges the counter and a gap
discharges it; a continuous overcurrent trips after exactly the window; an
intermittent one trips when the accumulated time-above-threshold minus the
decayed gaps reaches the window. The counter is cleared on trip clear and
held at zero while the path is disabled or masked. Its peak is recorded in
`SOFT_PEAK`.

**Hard path.** An 8-bit counter counts consecutive comparator decisions with
`cmp_hard` high and clears on any low decision; at `HARD_N` the breaker trips
with cause "hard". Decisions are sampled once per `cmp_clk` period, in the
`osc_clk` cycle in which the synchronised falling-edge decision is valid, so the
trip latency from the first high decision is 2 × `HARD_N` + 1 cycles plus 0 to 2
cycles of `cmp_clk` phase (simulated: 9 to 12 cycles for `HARD_N` = 4). This is
a glitch filter, not an accumulator.

**Analog latch (G1_GATE).** The digital latch drives `trip_d` (level); the
3.3 V latch in G1_GATE sets on it within nanoseconds. Every clear of the digital
latch (`CLEAR`, retrigger re-enable) produces a `clr_d` pulse of 2 cycles which
clears the analog latch; `EN` low clears it by itself. With `MODE.FAST_EN` = 1
the analog latch is also set directly by `cmp_hard` (no filter, no inrush mask);
the core sees `tripped` rise, adopts the trip into its own latch with cause
"hard", counts it in `TRIP_CNT` and treats it like any other trip (hold,
retrigger, give-up). Adoption is masked for 5 cycles after each `clr_d` so the
not-yet-synchronised old latch state cannot re-trip. Adoption latency
(simulated): ≤ 6 cycles after the analog latch sets.

**Inrush mask.** For `INRUSH` × 512 cycles after reset release and after each
retrigger re-enable, both counters are held at zero. `FORCE_TRIP` is not
masked.

**Latched mode** (`RETRIG` = 0): `trip` (and `trip_d`) stays 1, `gate_en` 0,
`fault_n` 0 until `CTRL.CLEAR` or an `EN` cycle.

**Retrigger mode** (`RETRIG` = 1): after a trip the hold timer runs for
`HOLD_TIME` × 8192 cycles, then the latch clears, the retry count increments,
the inrush mask restarts and the gate is re-enabled. If the breaker then stays
untripped for another `HOLD_TIME` the retry count returns to zero. If it trips
again and the retry count has reached `RETRY_MAX`, the breaker stays latched
(`STATUS.GAVE_UP` = 1) until `CLEAR` or `EN`.

`TRIP_CNT` increments once per trip event (each rising edge of `trip`),
including retriggers, forced trips and adopted analog fast-path trips.

**Sense offset.** `SENSE_OFS` is added (two's complement) to `DAC_HARD` and to
the hysteresis-adjusted `DAC_SOFT` every cycle; the sums are saturated at 0 and
255 before they are driven. The offset therefore moves both thresholds by the
same shunt voltage, which is what a sense-amplifier offset needs; it never
changes the difference between the two thresholds except at the rails.

## 6. SEU monitor behaviour

Two shift registers are clocked by `osc_clk` on every cycle and fed the same
pattern bit: a **plain** register (one flop per stage) and a **TMR** register
(three flops per stage, kept as three separate copy instances so the layout
can place them apart). Register lengths are RTL parameters
(`SEU_PLAIN_LEN`, `SEU_TMR_LEN`); the values built for G1 are stated in
`blocks/g1_seu/README.md`. At every clock, each TMR stage's three outputs are
majority-voted and the vote is written into all three flops of the next stage,
so a single upset is corrected at the next clock. The pattern generator, the
fill counter and all counters are themselves triple-redundant with the same
vote-and-rewrite structure (`g1_tmr_reg`).

There is no clock enable on the chains (sg13g2 has no enable flop; a per-bit
mux would cost 40 % of the flop area). A *dynamic* test uses the checkerboard,
under which every flop toggles each clock; a *static-data* test uses the
all-0 or all-1 pattern, under which the flops are clocked but never change
state. The patterns have period 1 or 2 and both register lengths are even, so
the expected output bit at every clock is the bit being fed in; no delayed
reference generator is needed. Comparison is enabled once max(SEU_PLAIN_LEN, SEU_TMR_LEN) clocks (256 in this build) have
refilled both registers after reset, enable or a pattern change.

Per clock: plain output ≠ expected counts one `SEU_PLAIN` (and extends the
current error run, whose maximum is `SEU_RUN`); any disagreement inside the
TMR register counts one `SEU_CORR`; TMR output ≠ expected counts one
`SEU_UNC`. Counters saturate. `INJ_PLAIN` / `INJ_TMR` exercise the whole path
on silicon without radiation.

Reads of the counters return values frozen at the instant of the read (the
low-byte read also freezes the high byte, section 4); counting is never
suspended, so no event is lost while the host is reading.

## 7. Change log

| Version | Date | Change |
| --- | --- | --- |
| 1.0 | 2026-09-18 | first release, built into `g1_digital` run4 |
| 1.1 | 2026-09-19 | Aligned with `blocks/g1_trip/INTERFACE.md` and `blocks/g1_t2f/INTERFACE.md`. New ports `cmp_clk`, `trip_d`, `clr_d`, `fast_en`, `tripped`, `osc_en`, `osc_trim[3:0]`, `t2f_en`, `t2f_mode`, `bgr_r4` (section 2). New registers 0x27 `SENSE_OFS`, 0x28 `OSC_CTRL`, 0x29 `TEMP_CTRL`, 0x2A `DAC_SOFT_EFF`, 0x2B `DAC_HARD_EFF`; `MODE` bit 5 `FAST_EN`; `STATUS2` bit 3 `TRIPPED_A`; `VERSION` reads 0x11. Existing addresses unchanged. Reset codes `DAC_SOFT` 0x60 → 0x99 and `DAC_HARD` 0x80 → 0xFE, following the shunt scaling (25 mV = nominal current) of the sense path. `HARD_N` counts comparator decisions (200 ns) instead of `osc_clk` samples (100 ns): the reset value 4 now means 0.8 µs. The hard comparator is sampled once per `cmp_clk` period; the soft accumulator is unchanged (still `osc_clk` cycles). Trip cause 2 ("hard") now also covers analog fast-path trips. |

# r1_ctrl run r1ctrl_20261020_r2

Tools: Icarus Verilog version 14.0 (devel) (s20260301-328-geda9fdcd-dirty); Yosys 0.67 (git sha1 2d1509d1b, Release, GNU /usr/bin/c++ 13.3.0); Python 3.12.3 numpy 2.5.1; PDK commit 84374023ee8b4b126bebbba67fcbada0a9c0ff0b. Date 2026-10-20T10:53:10Z.

## (a) V3 position: RTL against the floating-point reference (deg el)

| Case | Head | RTL vs true max / rms | RTL vs true, mean removed max | RTL vs float reference max | tracked vs true (after settle) max, mean removed | lock (pairs) | velocity rel. error |
| --- | --- | --- | --- | --- | --- | --- | --- |
| cal_neg | ofs -0.065, gain 0.8, ph -10.0 deg, h3 0.01, f -1 kHz, noise 0.0 LSB, cal reference, extrap 0 | 0.215 / 0.167 | 0.055 | 0.0188 | 0.059 | 39 | +0.0034 |
| cal_noise | ofs 0.065, gain 1.25, ph 10.0 deg, h3 0.01, f 1 kHz, noise 0.5 LSB, cal reference, extrap 0 | 0.205 / 0.126 | 0.085 | 0.0196 | 0.057 | 36 | -0.0096 |
| cal | ofs 0.065, gain 1.25, ph 10.0 deg, h3 0.01, f 1 kHz, noise 0.0 LSB, cal reference, extrap 0 | 0.170 / 0.128 | 0.051 | 0.0206 | 0.035 | 35 | -0.0110 |
| cal_self | ofs 0.065, gain 1.25, ph 10.0 deg, h3 0.01, f 1 kHz, noise 0.0 LSB, cal self, extrap 0 | 0.555 / 0.310 | 0.441 | 0.0194 | 0.431 | 39 | -0.0071 |
| fast_100k | ofs 0.065, gain 1.25, ph 10.0 deg, h3 0.01, f 100 kHz, noise 0.0 LSB, cal reference, extrap 0 | 0.128 / 0.114 | 0.016 | 0.0089 | 137.329 | 2000 | -1.0000 |
| fast_k0 | ofs 0.065, gain 1.25, ph 10.0 deg, h3 0.01, f 50 kHz, noise 0.0 LSB, cal reference, extrap 0 | 0.163 / 0.127 | 0.037 | 0.0113 | 39.226 | 2000 | -0.9848 |
| fast_k30 | ofs 0.065, gain 1.25, ph 10.0 deg, h3 0.01, f 50 kHz, noise 0.0 LSB, cal reference, extrap 30 | 0.163 / 0.127 | 0.037 | 0.0113 | 38.951 | 2000 | -0.9848 |
| ideal | ofs 0.0, gain 1.0, ph 0.0 deg, h3 0.0, f 1 kHz, noise 0.0 LSB, cal none, extrap 0 | 0.027 / 0.012 | 0.027 | 0.0046 | 0.019 | 35 | -0.0116 |
| uncal | ofs 0.065, gain 1.25, ph 10.0 deg, h3 0.01, f 1 kHz, noise 0.0 LSB, cal none, extrap 0 | 13.946 / 8.477 | 12.445 | 0.0056 | 13.431 | 2000 | -0.0034 |

## (b..f) chip-level testbench

| Log | Checks | Failed | Verdict |
| --- | --- | --- | --- |
| top_biss_23.810.log | 41 | 2 | FAILED |
| top_biss_33.333.log | 41 | 2 | FAILED |
| top_biss_47.619.log | 41 | 2 | FAILED |
| top_gate_33.333.log | 14 | 0 | passed |
| top_safe_33.333.log | 32 | 0 | passed |
| top_spi_33.333.log | 21 | 1 | FAILED |
| top_ssi_23.810.log | 9 | 0 | passed |
| top_ssi_33.333.log | 9 | 0 | passed |
| top_ssi_47.619.log | 9 | 0 | passed |

Information lines:

- `top_biss_23.810.log`: biss f_MA=80000 Hz duty_high=0.4 t_busy=2 T_MA timeout=14.38 us
- `top_biss_23.810.log`: biss f_MA=80000 Hz duty_high=0.6 t_busy=2 T_MA timeout=14.38 us
- `top_biss_23.810.log`: biss f_MA=250000 Hz duty_high=0.4 t_busy=2 T_MA timeout=14.38 us
- `top_biss_23.810.log`: biss f_MA=250000 Hz duty_high=0.6 t_busy=2 T_MA timeout=14.37 us
- `top_biss_23.810.log`: biss f_MA=1000000 Hz duty_high=0.4 t_busy=2 T_MA timeout=14.37 us
- `top_biss_23.810.log`: biss f_MA=1000000 Hz duty_high=0.6 t_busy=2 T_MA timeout=14.38 us
- `top_biss_23.810.log`: biss f_MA=5000000 Hz duty_high=0.4 t_busy=2 T_MA timeout=14.36 us
- `top_biss_23.810.log`: biss f_MA=5000000 Hz duty_high=0.6 t_busy=2 T_MA timeout=14.38 us
- `top_biss_23.810.log`: biss f_MA=10000000 Hz duty_high=0.4 t_busy=3 T_MA timeout=14.37 us
- `top_biss_23.810.log`: biss f_MA=10000000 Hz duty_high=0.6 t_busy=3 T_MA timeout=14.37 us
- `top_biss_23.810.log`: biss timeout measured 14.372 us, 600 ticks = 14.286 us
- `top_biss_23.810.log`: biss latch frame 0: busy 2 MT 0 ST 0x00000 nE nW 01 crc 3c/3c head 0.04549 err 16.375 deg
- `top_biss_23.810.log`: biss latch frame 1: busy 2 MT 0 ST 0x00000 nE nW 01 crc 3c/3c head 0.72869 err 97.673 deg
- `top_biss_23.810.log`: biss latch frame 2: busy 2 MT 0 ST 0x00000 nE nW 01 crc 3c/3c head 0.41180 err 148.246 deg
- `top_biss_23.810.log`: biss latch frame 3: busy 2 MT 0 ST 0x00000 nE nW 01 crc 3c/3c head 0.09490 err 34.162 deg
- `top_biss_23.810.log`: biss latch frame 4: busy 2 MT 0 ST 0x00000 nE nW 01 crc 3c/3c head 0.77801 err 79.918 deg
- `top_biss_23.810.log`: biss latch frame 5: busy 2 MT 0 ST 0x00000 nE nW 01 crc 3c/3c head 0.46112 err 166.001 deg
- `top_biss_23.810.log`: biss latch: max |position at LAT - head angle at LAT| = 166.001 deg el at 10 kHz el
- `top_biss_23.810.log`: biss: 6 multi-turn frames with real position, nE nW 1 1, CRC valid  (t=2804173000)
- `top_biss_23.810.log`: biss: latched position within 0.25 deg el (2 ticks) of the head angle at LAT (10 kHz el)  (t=2804173000)
- `top_biss_23.810.log`: biss control read 0x42 -> 0x00 (S=1, CRC4 wire f)
- `top_biss_23.810.log`: biss control read 0x43 -> 0x01 (S=1, CRC4 wire c)
- `top_biss_23.810.log`: biss control read 0x78 -> 0x52 (S=1, CRC4 wire b)
- `top_biss_23.810.log`: biss control read 0x7f -> 0x00 (S=1, CRC4 wire f)
- `top_biss_33.333.log`: biss f_MA=80000 Hz duty_high=0.4 t_busy=2 T_MA timeout=20.11 us
- `top_biss_33.333.log`: biss f_MA=80000 Hz duty_high=0.6 t_busy=2 T_MA timeout=20.11 us
- `top_biss_33.333.log`: biss f_MA=250000 Hz duty_high=0.4 t_busy=2 T_MA timeout=20.10 us
- `top_biss_33.333.log`: biss f_MA=250000 Hz duty_high=0.6 t_busy=2 T_MA timeout=20.10 us
- `top_biss_33.333.log`: biss f_MA=1000000 Hz duty_high=0.4 t_busy=2 T_MA timeout=20.10 us
- `top_biss_33.333.log`: biss f_MA=1000000 Hz duty_high=0.6 t_busy=2 T_MA timeout=20.10 us
- `top_biss_33.333.log`: biss f_MA=5000000 Hz duty_high=0.4 t_busy=2 T_MA timeout=20.11 us
- `top_biss_33.333.log`: biss f_MA=5000000 Hz duty_high=0.6 t_busy=2 T_MA timeout=20.12 us
- `top_biss_33.333.log`: biss f_MA=10000000 Hz duty_high=0.4 t_busy=3 T_MA timeout=20.11 us
- `top_biss_33.333.log`: biss f_MA=10000000 Hz duty_high=0.6 t_busy=3 T_MA timeout=20.13 us
- `top_biss_33.333.log`: biss timeout measured 20.101 us, 600 ticks = 20.000 us
- `top_biss_33.333.log`: biss latch frame 0: busy 2 MT 0 ST 0x00000 nE nW 01 crc 3c/3c head 0.42779 err 154.004 deg
- `top_biss_33.333.log`: biss latch frame 1: busy 2 MT 0 ST 0x00000 nE nW 01 crc 3c/3c head 0.16854 err 60.674 deg
- `top_biss_33.333.log`: biss latch frame 2: busy 2 MT 0 ST 0x00000 nE nW 01 crc 3c/3c head 0.90922 err 32.681 deg
- `top_biss_33.333.log`: biss latch frame 3: busy 2 MT 0 ST 0x00000 nE nW 01 crc 3c/3c head 0.64990 err 126.036 deg
- `top_biss_33.333.log`: biss latch frame 4: busy 2 MT 0 ST 0x00000 nE nW 01 crc 3c/3c head 0.39059 err 140.612 deg
- `top_biss_33.333.log`: biss latch frame 5: busy 2 MT 0 ST 0x00000 nE nW 01 crc 3c/3c head 0.13127 err 47.257 deg
- `top_biss_33.333.log`: biss latch: max |position at LAT - head angle at LAT| = 154.004 deg el at 10 kHz el
- `top_biss_33.333.log`: biss: 6 multi-turn frames with real position, nE nW 1 1, CRC valid  (t=3076945000)
- `top_biss_33.333.log`: biss: latched position within 0.25 deg el (2 ticks) of the head angle at LAT (10 kHz el)  (t=3076945000)
- `top_biss_33.333.log`: biss control read 0x42 -> 0x00 (S=1, CRC4 wire f)
- `top_biss_33.333.log`: biss control read 0x43 -> 0x01 (S=1, CRC4 wire c)
- `top_biss_33.333.log`: biss control read 0x78 -> 0x52 (S=1, CRC4 wire b)
- `top_biss_33.333.log`: biss control read 0x7f -> 0x00 (S=1, CRC4 wire f)
- `top_biss_47.619.log`: biss f_MA=80000 Hz duty_high=0.4 t_busy=2 T_MA timeout=28.76 us
- `top_biss_47.619.log`: biss f_MA=80000 Hz duty_high=0.6 t_busy=2 T_MA timeout=28.74 us
- `top_biss_47.619.log`: biss f_MA=250000 Hz duty_high=0.4 t_busy=2 T_MA timeout=28.74 us
- `top_biss_47.619.log`: biss f_MA=250000 Hz duty_high=0.6 t_busy=2 T_MA timeout=28.73 us
- `top_biss_47.619.log`: biss f_MA=1000000 Hz duty_high=0.4 t_busy=2 T_MA timeout=28.73 us
- `top_biss_47.619.log`: biss f_MA=1000000 Hz duty_high=0.6 t_busy=2 T_MA timeout=28.73 us
- `top_biss_47.619.log`: biss f_MA=5000000 Hz duty_high=0.4 t_busy=3 T_MA timeout=28.76 us
- `top_biss_47.619.log`: biss f_MA=5000000 Hz duty_high=0.6 t_busy=2 T_MA timeout=28.76 us
- `top_biss_47.619.log`: biss f_MA=10000000 Hz duty_high=0.4 t_busy=3 T_MA timeout=28.73 us
- `top_biss_47.619.log`: biss f_MA=10000000 Hz duty_high=0.6 t_busy=3 T_MA timeout=28.75 us
- `top_biss_47.619.log`: biss timeout measured 28.730 us, 600 ticks = 28.571 us
- `top_biss_47.619.log`: biss latch frame 0: busy 2 MT 0 ST 0x00000 nE nW 01 crc 3c/3c head 0.00784 err 2.822 deg
- `top_biss_47.619.log`: biss latch frame 1: busy 2 MT 0 ST 0x00000 nE nW 01 crc 3c/3c head 0.83488 err 59.444 deg
- `top_biss_47.619.log`: biss latch frame 2: busy 2 MT 0 ST 0x00000 nE nW 01 crc 3c/3c head 0.66156 err 121.839 deg
- `top_biss_47.619.log`: biss latch frame 3: busy 2 MT 0 ST 0x00000 nE nW 01 crc 3c/3c head 0.48824 err 175.766 deg
- `top_biss_47.619.log`: biss latch frame 4: busy 2 MT 0 ST 0x00000 nE nW 01 crc 3c/3c head 0.31493 err 113.374 deg
- `top_biss_47.619.log`: biss latch frame 5: busy 2 MT 0 ST 0x00000 nE nW 01 crc 3c/3c head 0.14161 err 50.979 deg
- `top_biss_47.619.log`: biss latch: max |position at LAT - head angle at LAT| = 175.766 deg el at 10 kHz el
- `top_biss_47.619.log`: biss: 6 multi-turn frames with real position, nE nW 1 1, CRC valid  (t=3486579000)
- `top_biss_47.619.log`: biss: latched position within 0.25 deg el (2 ticks) of the head angle at LAT (10 kHz el)  (t=3486579000)
- `top_biss_47.619.log`: biss control read 0x42 -> 0x00 (S=1, CRC4 wire f)
- `top_biss_47.619.log`: biss control read 0x43 -> 0x01 (S=1, CRC4 wire c)
- `top_biss_47.619.log`: biss control read 0x78 -> 0x52 (S=1, CRC4 wire b)
- `top_biss_47.619.log`: biss control read 0x7f -> 0x00 (S=1, CRC4 wire f)
- `top_gate_33.333.log`: gate A on 16 off 586 (width 570), B on 516 off 786 (width 270), C on 1016 off 386 (width 870); strobes A 301 B 651
- `top_safe_33.333.log`: safe cmp[0]: FAULT 0x0001, FAULT_N low after 4 ticks
- `top_safe_33.333.log`: safe cmp[1]: FAULT 0x0002, FAULT_N low after 4 ticks
- `top_safe_33.333.log`: safe cmp[2]: FAULT 0x0004, FAULT_N low after 4 ticks
- `top_safe_33.333.log`: safe cmp[3]: FAULT 0x0008, FAULT_N low after 4 ticks
- `top_safe_33.333.log`: safe TEMP count 273 (2 MHz over 4096 ticks, expected 273.1)
- `top_safe_33.333.log`: safe watchdog fired 4091 ticks after the last SPI frame (period 4096 ticks)
- `top_safe_33.333.log`: safe FAULT before I2t 0x0000
- `top_safe_33.333.log`: safe I2t: trip after 30827 ticks = 102.8 PWM periods; integer model 103 updates; closed form 102.20 updates
- `top_spi_33.333.log`: OSC_COUNT = 480, expected 480.0 (16 us of 33.333 ns ticks)
- `top_spi_33.333.log`: spi/biss frame: busy 2 data 0x12345 nE nW 11 crc wire 0d calc~ 0d ack 1
- `top_spi_33.333.log`: AS5047P ANGLECOM frame 0xaa6a, angle 10858 of 16384 (expected 3276.8)
- `top_spi_33.333.log`: spi AS: ANGLECOM = head angle (0.2 turn) within 0.3 deg  (t=867495000)
- `top_ssi_23.810.log`: ssi gray=0 data 0x0000099a expected 0x0000099a monoflop 14.36 us
- `top_ssi_23.810.log`: ssi gray=1 data 0x00000d57 expected 0x00000d57 monoflop 14.37 us
- `top_ssi_23.810.log`: ssi clk 23.810 ns: OSC_COUNT 672 -> TIMEOUT_TICKS 840, monoflop 20.09 us (600 ticks untrimmed = 14.29 us)
- `top_ssi_33.333.log`: ssi gray=0 data 0x0000099a expected 0x0000099a monoflop 20.13 us
- `top_ssi_33.333.log`: ssi gray=1 data 0x00000d57 expected 0x00000d57 monoflop 20.10 us
- `top_ssi_33.333.log`: ssi clk 33.333 ns: OSC_COUNT 480 -> TIMEOUT_TICKS 600, monoflop 20.12 us (600 ticks untrimmed = 20.00 us)
- `top_ssi_47.619.log`: ssi gray=0 data 0x0000099a expected 0x0000099a monoflop 28.76 us
- `top_ssi_47.619.log`: ssi gray=1 data 0x00000d57 expected 0x00000d57 monoflop 28.73 us
- `top_ssi_47.619.log`: ssi clk 47.619 ns: OSC_COUNT 336 -> TIMEOUT_TICKS 420, monoflop 20.16 us (600 ticks untrimmed = 28.57 us)

## Synthesis (Yosys, sg13g2_stdcell typ 1.2 V 25 C, abc -D 33333)

- cells 14880, flops 1737, cell area 218277 um2 (30.1 kGE at 7.26 um2 per nand2_1), sequential 85094 um2 (39 %)
- ratio of cell area to the 0.18 mm2 digital budget: 1.21
- macro estimate at the G1 run7 ratio (129 600 um2 macro / 84 796 um2 synthesis): 0.334 mm2 = 1.85 x budget
- per module (hierarchical synthesis, um2): r1_pos 76698, r1_regs 42799, r1_gate 37886, r1_safe 23021, r1_biss 21925, r1_spi 11474, r1_ctrl_top 4808, r1_sinlut 1235, r1_sync2 606

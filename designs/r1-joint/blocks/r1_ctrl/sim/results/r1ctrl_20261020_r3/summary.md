# r1_ctrl run r1ctrl_20261020_r3

Tools: Icarus Verilog version 14.0 (devel) (s20260301-328-geda9fdcd-dirty); Yosys 0.67 (git sha1 2d1509d1b, Release, GNU /usr/bin/c++ 13.3.0); Python 3.12.3 numpy 2.5.1; PDK commit 84374023ee8b4b126bebbba67fcbada0a9c0ff0b. Date 2026-10-20T10:57:38Z.

## (a) V3 position: RTL against the floating-point reference (deg el)

| Case | Head | RTL vs true max / rms | RTL vs true, mean removed max | RTL vs float reference max | tracked vs true (after settle) max, mean removed | lock (pairs) | velocity rel. error |
| --- | --- | --- | --- | --- | --- | --- | --- |
| cal_neg | ofs -0.065, gain 0.8, ph -10.0 deg, h3 0.01, f -1 kHz, noise 0.0 LSB, cal reference, extrap 0 | 0.215 / 0.167 | 0.055 | 0.0188 | 0.057 | 43 | +0.0030 |
| cal_noise | ofs 0.065, gain 1.25, ph 10.0 deg, h3 0.01, f 1 kHz, noise 0.5 LSB, cal reference, extrap 0 | 0.205 / 0.126 | 0.085 | 0.0196 | 0.053 | 41 | -0.0099 |
| cal | ofs 0.065, gain 1.25, ph 10.0 deg, h3 0.01, f 1 kHz, noise 0.0 LSB, cal reference, extrap 0 | 0.170 / 0.128 | 0.051 | 0.0206 | 0.035 | 41 | -0.0108 |
| cal_self | ofs 0.065, gain 1.25, ph 10.0 deg, h3 0.01, f 1 kHz, noise 0.0 LSB, cal self, extrap 0 | 0.555 / 0.310 | 0.441 | 0.0194 | 0.432 | 45 | -0.0072 |
| fast_100k | ofs 0.065, gain 1.25, ph 10.0 deg, h3 0.01, f 100 kHz, noise 0.0 LSB, cal reference, extrap 0 | 0.128 / 0.114 | 0.016 | 0.0089 | 0.004 | 96 | -0.0001 |
| fast_k0 | ofs 0.065, gain 1.25, ph 10.0 deg, h3 0.01, f 50 kHz, noise 0.0 LSB, cal reference, extrap 0 | 0.163 / 0.127 | 0.037 | 0.0113 | 0.009 | 67 | -0.0001 |
| fast_k30 | ofs 0.065, gain 1.25, ph 10.0 deg, h3 0.01, f 50 kHz, noise 0.0 LSB, cal reference, extrap 30 | 0.163 / 0.127 | 0.037 | 0.0113 | 0.009 | 68 | -0.0001 |
| ideal | ofs 0.0, gain 1.0, ph 0.0 deg, h3 0.0, f 1 kHz, noise 0.0 LSB, cal none, extrap 0 | 0.027 / 0.012 | 0.027 | 0.0046 | 0.018 | 40 | -0.0121 |
| uncal | ofs 0.065, gain 1.25, ph 10.0 deg, h3 0.01, f 1 kHz, noise 0.0 LSB, cal none, extrap 0 | 13.946 / 8.477 | 12.445 | 0.0056 | 13.456 | 2000 | -0.0034 |

## (b..f) chip-level testbench

| Log | Checks | Failed | Verdict |
| --- | --- | --- | --- |
| top_biss_23.810.log | 41 | 0 | passed |
| top_biss_33.333.log | 41 | 0 | passed |
| top_biss_47.619.log | 41 | 0 | passed |
| top_gate_33.333.log | 14 | 0 | passed |
| top_safe_33.333.log | 32 | 0 | passed |
| top_spi_33.333.log | 21 | 0 | passed |
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
- `top_biss_23.810.log`: biss latch frame 0: busy 2 MT 5 ST 0x02ea0 nE nW 11 crc 0f/0f head 0.04549 err 0.017 deg
- `top_biss_23.810.log`: biss latch frame 1: busy 2 MT 5 ST 0x2ea2b nE nW 11 crc 21/21 head 0.72869 err 0.002 deg
- `top_biss_23.810.log`: biss latch frame 2: busy 2 MT 6 ST 0x1a5cc nE nW 11 crc 18/18 head 0.41180 err 0.042 deg
- `top_biss_23.810.log`: biss latch frame 3: busy 2 MT 7 ST 0x06131 nE nW 11 crc 31/31 head 0.09490 err 0.007 deg
- `top_biss_23.810.log`: biss latch frame 4: busy 2 MT 7 ST 0x31ca0 nE nW 11 crc 13/13 head 0.77801 err 0.018 deg
- `top_biss_23.810.log`: biss latch frame 5: busy 2 MT 8 ST 0x1d84e nE nW 11 crc 32/32 head 0.46112 err 0.043 deg
- `top_biss_23.810.log`: biss latch: max |position at LAT - head angle at LAT| = 0.043 deg el at 10 kHz el
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
- `top_biss_33.333.log`: biss latch frame 0: busy 2 MT 4 ST 0x1b663 nE nW 11 crc 3a/3a head 0.42779 err 0.116 deg
- `top_biss_33.333.log`: biss latch frame 1: busy 2 MT 5 ST 0x0acc7 nE nW 11 crc 3a/3a head 0.16854 err 0.068 deg
- `top_biss_33.333.log`: biss latch frame 2: busy 2 MT 5 ST 0x3a325 nE nW 11 crc 03/03 head 0.90922 err 0.036 deg
- `top_biss_33.333.log`: biss latch frame 3: busy 2 MT 6 ST 0x299af nE nW 11 crc 37/37 head 0.64990 err 0.066 deg
- `top_biss_33.333.log`: biss latch frame 4: busy 2 MT 7 ST 0x1903e nE nW 11 crc 2f/2f head 0.39059 err 0.098 deg
- `top_biss_33.333.log`: biss latch frame 5: busy 2 MT 8 ST 0x08697 nE nW 11 crc 0b/0b head 0.13127 err 0.060 deg
- `top_biss_33.333.log`: biss latch: max |position at LAT - head angle at LAT| = 0.116 deg el at 10 kHz el
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
- `top_biss_47.619.log`: biss latch frame 0: busy 2 MT 5 ST 0x00814 nE nW 11 crc 0a/0a head 0.00784 err 0.018 deg
- `top_biss_47.619.log`: biss latch frame 1: busy 2 MT 5 ST 0x3571c nE nW 11 crc 37/37 head 0.83488 err 0.068 deg
- `top_biss_47.619.log`: biss latch frame 2: busy 2 MT 6 ST 0x2a5b5 nE nW 11 crc 1f/1f head 0.66156 err 0.095 deg
- `top_biss_47.619.log`: biss latch frame 3: busy 2 MT 7 ST 0x1f44e nE nW 11 crc 35/35 head 0.48824 err 0.123 deg
- `top_biss_47.619.log`: biss latch frame 4: busy 2 MT 8 ST 0x142d5 nE nW 11 crc 05/05 head 0.31493 err 0.121 deg
- `top_biss_47.619.log`: biss latch frame 5: busy 2 MT 9 ST 0x09144 nE nW 11 crc 27/27 head 0.14161 err 0.091 deg
- `top_biss_47.619.log`: biss latch: max |position at LAT - head angle at LAT| = 0.123 deg el at 10 kHz el
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
- `top_spi_33.333.log`: AS5047P ANGLECOM frame 0x8ccd, angle 3277 of 16384 (expected 3276.8)
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

- cells 15201, flops 1738, cell area 220968 um2 (30.4 kGE at 7.26 um2 per nand2_1), sequential 85143 um2 (39 %)
- ratio of cell area to the 0.18 mm2 digital budget: 1.23
- macro estimate at the G1 run7 ratio (129 600 um2 macro / 84 796 um2 synthesis): 0.338 mm2 = 1.88 x budget
- per module (hierarchical synthesis, um2): r1_pos 79637, r1_regs 42799, r1_gate 37886, r1_safe 23021, r1_biss 21785, r1_spi 11494, r1_ctrl_top 4808, r1_sinlut 1235, r1_sync2 606

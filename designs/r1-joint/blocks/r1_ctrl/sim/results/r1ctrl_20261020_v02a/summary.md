# r1_ctrl run r1ctrl_20261020_v02a

Tools: Icarus Verilog version 14.0 (devel) (s20260301-328-geda9fdcd-dirty); Yosys 0.67 (git sha1 2d1509d1b, Release, GNU /usr/bin/c++ 13.3.0); Python 3.12.3 numpy 2.5.1; PDK commit 84374023ee8b4b126bebbba67fcbada0a9c0ff0b. Date 2026-10-20T15:19:16Z.

## (a) V3 position: RTL against the floating-point reference (deg el)

| Case | Head | RTL vs true max / rms | RTL vs true, mean removed max | RTL vs float reference max | tracked vs true (after settle) max, mean removed | lock (pairs) | velocity rel. error |
| --- | --- | --- | --- | --- | --- | --- | --- |
| cal_neg | ofs -0.065, gain 0.8, ph -10.0 deg, h3 0.01, f -1 kHz, noise 0.0 LSB, cal reference, extrap 0 | 0.215 / 0.167 | 0.058 | 0.0214 | 0.058 | 43 | +0.0032 |
| cal_noise | ofs 0.065, gain 1.25, ph 10.0 deg, h3 0.01, f 1 kHz, noise 0.5 LSB, cal reference, extrap 0 | 0.207 / 0.126 | 0.086 | 0.0222 | 0.055 | 41 | -0.0099 |
| cal | ofs 0.065, gain 1.25, ph 10.0 deg, h3 0.01, f 1 kHz, noise 0.0 LSB, cal reference, extrap 0 | 0.173 / 0.128 | 0.054 | 0.0233 | 0.035 | 41 | -0.0110 |
| cal_self | ofs 0.065, gain 1.25, ph 10.0 deg, h3 0.01, f 1 kHz, noise 0.0 LSB, cal self, extrap 0 | 0.555 / 0.310 | 0.446 | 0.0221 | 0.431 | 45 | -0.0071 |
| fast_100k | ofs 0.065, gain 1.25, ph 10.0 deg, h3 0.01, f 100 kHz, noise 0.0 LSB, cal reference, extrap 0 | 0.125 / 0.114 | 0.016 | 0.0084 | 0.004 | 95 | -0.0001 |
| fast_k0 | ofs 0.065, gain 1.25, ph 10.0 deg, h3 0.01, f 50 kHz, noise 0.0 LSB, cal reference, extrap 0 | 0.163 / 0.127 | 0.037 | 0.0113 | 0.008 | 67 | -0.0001 |
| fast_k30 | ofs 0.065, gain 1.25, ph 10.0 deg, h3 0.01, f 50 kHz, noise 0.0 LSB, cal reference, extrap 30 | 0.163 / 0.127 | 0.037 | 0.0113 | 0.009 | 68 | -0.0001 |
| ideal | ofs 0.0, gain 1.0, ph 0.0 deg, h3 0.0, f 1 kHz, noise 0.0 LSB, cal none, extrap 0 | 0.029 / 0.012 | 0.029 | 0.0071 | 0.019 | 40 | -0.0119 |
| uncal | ofs 0.065, gain 1.25, ph 10.0 deg, h3 0.01, f 1 kHz, noise 0.0 LSB, cal none, extrap 0 | 13.946 / 8.477 | 12.448 | 0.0088 | 13.457 | 2000 | -0.0034 |

## (b..f) chip-level testbench

| Log | Checks | Failed | Verdict |
| --- | --- | --- | --- |
| top_biss_23.810.log | 48 | 0 | passed |
| top_biss_33.333.log | 48 | 0 | passed |
| top_biss_47.619.log | 48 | 0 | passed |
| top_cal_33.333.log | 13 | 0 | passed |
| top_gate_33.333.log | 19 | 0 | passed |
| top_safe_33.333.log | 32 | 0 | passed |
| top_spi_33.333.log | 25 | 0 | passed |
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
- `top_biss_23.810.log`: biss latch frame 0: busy 2 MT 5 ST 0x02ea2 nE nW 11 crc 17/17 head 0.04549 err 0.020 deg
- `top_biss_23.810.log`: biss latch frame 1: busy 2 MT 5 ST 0x2ea2a nE nW 11 crc 2d/2d head 0.72869 err 0.003 deg
- `top_biss_23.810.log`: biss latch frame 2: busy 2 MT 6 ST 0x1a5c6 nE nW 11 crc 23/23 head 0.41180 err 0.034 deg
- `top_biss_23.810.log`: biss latch frame 3: busy 2 MT 7 ST 0x0612f nE nW 11 crc 3f/3f head 0.09490 err 0.004 deg
- `top_biss_23.810.log`: biss latch frame 4: busy 2 MT 7 ST 0x31ca4 nE nW 11 crc 23/23 head 0.77801 err 0.013 deg
- `top_biss_23.810.log`: biss latch frame 5: busy 2 MT 8 ST 0x1d850 nE nW 11 crc 3c/3c head 0.46112 err 0.046 deg
- `top_biss_23.810.log`: biss latch: max |position at LAT - head angle at LAT| = 0.046 deg el at 10 kHz el
- `top_biss_23.810.log`: biss LAT_HALF=0 at 100 kHz el: latch error 0.031 .. 0.816 deg el, spread 0.785 deg (1 tick = 0.857 deg)
- `top_biss_23.810.log`: biss LAT_HALF=1 at 100 kHz el: latch error 0.048 .. 0.443 deg el, spread 0.395 deg (1 tick = 0.857 deg)
- `top_biss_23.810.log`: biss cc read 0x42: CDS[1..32] 01111000000001010000000000000001
- `top_biss_23.810.log`: biss cc error counter 0 -> 3
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
- `top_biss_33.333.log`: biss latch frame 0: busy 2 MT 4 ST 0x1b668 nE nW 11 crc 0d/0d head 0.42779 err 0.123 deg
- `top_biss_33.333.log`: biss latch frame 1: busy 2 MT 5 ST 0x0acc0 nE nW 11 crc 1e/1e head 0.16854 err 0.058 deg
- `top_biss_33.333.log`: biss latch frame 2: busy 2 MT 5 ST 0x3a31e nE nW 11 crc 3b/3b head 0.90922 err 0.027 deg
- `top_biss_33.333.log`: biss latch frame 3: busy 2 MT 6 ST 0x299aa nE nW 11 crc 0b/0b head 0.64990 err 0.059 deg
- `top_biss_33.333.log`: biss latch frame 4: busy 2 MT 7 ST 0x1903f nE nW 11 crc 23/23 head 0.39059 err 0.099 deg
- `top_biss_33.333.log`: biss latch frame 5: busy 2 MT 8 ST 0x08696 nE nW 11 crc 07/07 head 0.13127 err 0.058 deg
- `top_biss_33.333.log`: biss latch: max |position at LAT - head angle at LAT| = 0.123 deg el at 10 kHz el
- `top_biss_33.333.log`: biss LAT_HALF=0 at 100 kHz el: latch error 0.010 .. 1.188 deg el, spread 1.178 deg (1 tick = 1.200 deg)
- `top_biss_33.333.log`: biss LAT_HALF=1 at 100 kHz el: latch error -0.007 .. 0.599 deg el, spread 0.607 deg (1 tick = 1.200 deg)
- `top_biss_33.333.log`: biss cc read 0x42: CDS[1..32] 01111000000001010000000000000001
- `top_biss_33.333.log`: biss cc error counter 0 -> 3
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
- `top_biss_47.619.log`: biss latch frame 0: busy 2 MT 5 ST 0x0080f nE nW 11 crc 38/38 head 0.00784 err 0.011 deg
- `top_biss_47.619.log`: biss latch frame 1: busy 2 MT 5 ST 0x3571d nE nW 11 crc 3b/3b head 0.83488 err 0.070 deg
- `top_biss_47.619.log`: biss latch frame 2: busy 2 MT 6 ST 0x2a5be nE nW 11 crc 28/28 head 0.66156 err 0.108 deg
- `top_biss_47.619.log`: biss latch frame 3: busy 2 MT 7 ST 0x1f454 nE nW 11 crc 0b/0b head 0.48824 err 0.131 deg
- `top_biss_47.619.log`: biss latch frame 4: busy 2 MT 8 ST 0x142d4 nE nW 11 crc 09/09 head 0.31493 err 0.120 deg
- `top_biss_47.619.log`: biss latch frame 5: busy 2 MT 9 ST 0x0913e nE nW 11 crc 07/07 head 0.14161 err 0.083 deg
- `top_biss_47.619.log`: biss latch: max |position at LAT - head angle at LAT| = 0.131 deg el at 10 kHz el
- `top_biss_47.619.log`: biss LAT_HALF=0 at 100 kHz el: latch error 0.078 .. 1.671 deg el, spread 1.592 deg (1 tick = 1.714 deg)
- `top_biss_47.619.log`: biss LAT_HALF=1 at 100 kHz el: latch error 0.055 .. 0.839 deg el, spread 0.784 deg (1 tick = 1.714 deg)
- `top_biss_47.619.log`: biss cc read 0x42: CDS[1..32] 01111000000001010000000000000001
- `top_biss_47.619.log`: biss cc error counter 0 -> 3
- `top_cal_33.333.log`: cal search: 1891 ticks, 7 az windows, CAL codes 24 44 0 63 exh 1100
- `top_cal_33.333.log`: cal CMP_CAL_A 0x2c18 CMP_CAL_B 0x7f40
- `top_gate_33.333.log`: gate A on 16 off 586 (width 570), B on 516 off 786 (width 270), C on 1016 off 386 (width 870); ISA start 301 ISB start 315 is_smp 301; az_win 1201..1241
- `top_gate_33.333.log`: gate I_A 2848 with binary weights, 2948 with ADC_W11 = 8592
- `top_safe_33.333.log`: safe cmp[0]: FAULT 0x0001, FAULT_N low after 4 ticks
- `top_safe_33.333.log`: safe cmp[1]: FAULT 0x0002, FAULT_N low after 4 ticks
- `top_safe_33.333.log`: safe cmp[2]: FAULT 0x0004, FAULT_N low after 4 ticks
- `top_safe_33.333.log`: safe cmp[3]: FAULT 0x0008, FAULT_N low after 4 ticks
- `top_safe_33.333.log`: safe TEMP count 273 (2 MHz over 4096 ticks, expected 273.1)
- `top_safe_33.333.log`: safe watchdog fired 4091 ticks after the last SPI frame (period 4096 ticks)
- `top_safe_33.333.log`: safe FAULT before I2t 0x0000
- `top_safe_33.333.log`: safe I2t: trip after 30826 ticks = 102.8 PWM periods; integer model 103 updates; closed form 102.20 updates
- `top_spi_33.333.log`: OSC_COUNT = 480, expected 480.0 (16 us of 33.333 ns ticks)
- `top_spi_33.333.log`: spi/biss frame: busy 2 data 0x12345 nE nW 11 crc wire 0d calc~ 0d ack 1
- `top_ssi_23.810.log`: ssi gray=0 data 0x0000099a expected 0x0000099a monoflop 14.36 us
- `top_ssi_23.810.log`: ssi gray=1 data 0x00000d57 expected 0x00000d57 monoflop 14.37 us
- `top_ssi_23.810.log`: ssi clk 23.810 ns: OSC_COUNT 672 -> TIMEOUT_TICKS 840, monoflop 20.09 us (600 ticks untrimmed = 14.29 us)
- `top_ssi_33.333.log`: ssi gray=0 data 0x0000099a expected 0x0000099a monoflop 20.13 us
- `top_ssi_33.333.log`: ssi gray=1 data 0x00000d57 expected 0x00000d57 monoflop 20.10 us
- `top_ssi_33.333.log`: ssi clk 33.333 ns: OSC_COUNT 480 -> TIMEOUT_TICKS 600, monoflop 20.12 us (600 ticks untrimmed = 20.00 us)
- `top_ssi_47.619.log`: ssi gray=0 data 0x0000099a expected 0x0000099a monoflop 28.76 us
- `top_ssi_47.619.log`: ssi gray=1 data 0x00000d57 expected 0x00000d57 monoflop 28.73 us
- `top_ssi_47.619.log`: ssi clk 47.619 ns: OSC_COUNT 336 -> TIMEOUT_TICKS 420, monoflop 20.16 us (600 ticks untrimmed = 28.57 us)

## Synthesis (Yosys, sg13g2_stdcell typ 1.2 V 25 C, Booth, PDK latch map, abc -D 23810)

- cells 12918, flops 1821, cell area 180168 um2 (24.8 kGE at 7.26 um2 per nand2_1), sequential 46049 um2 (26 %)
- ratio of cell area to the 0.18 mm2 cell-area target (0.28 mm2 placed at about 65 %): 1.00
- macro estimate at the G1 run7 ratio (129 600 um2 macro / 84 796 um2 synthesis): 0.275 mm2 = 1.53 x budget
- per block, children included (hierarchical synthesis, total 184682 um2; the flat run optimises across blocks): r1_pos 61578, r1_regs 36433, r1_gate 33010, r1_safe 23103, r1_biss 16508, r1_spi 6128, r1_ctrl_top (glue) 4076, r1_cmpcal 3569, r1_idrom 180, r1_sync2 98

## ADC weight correction (r1_adcw, tb_adcw + adcw_ref.py, mismatched-CDAC example)

| Weights | max abs DNL (LSB) | max abs INL (LSB) | missing codes | RTL vs integer model mismatches |
| --- | --- | --- | --- | --- |
| binary (reset) | 3.062 | 3.663 | 10 | 0 |
| calibrated (1/4 LSB) | 0.688 | 0.625 | 0 | 0 |

Model-only weight-resolution sweep (same raw decisions): exact: DNL 1.000, INL 0.562, missing 11; 1/2_lsb: DNL 0.938, INL 0.812, missing 0; 1/4_lsb: DNL 0.688, INL 0.625, missing 0; 1/8_lsb: DNL 0.688, INL 0.562, missing 0; 1/16_lsb: DNL 1.000, INL 0.500, missing 1
Checks: {'rtl_bit_exact': True, 'mismatch_example_shows_error_with_binary_weights': True, 'calibrated_no_missing_dnl_lt_1_inl_le_1': True}; verdict passed.

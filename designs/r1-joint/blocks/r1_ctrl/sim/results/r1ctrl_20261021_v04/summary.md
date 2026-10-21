# r1_ctrl run r1ctrl_20261021_v04

Tools: Icarus Verilog version 14.0 (devel) (s20260301-328-geda9fdcd-dirty); Yosys 0.67 (git sha1 2d1509d1b, Release, GNU /usr/bin/c++ 13.3.0); Python 3.12.3 numpy 2.5.1; PDK commit 84374023ee8b4b126bebbba67fcbada0a9c0ff0b. Date 2026-10-21T00:09:07Z.

## (a) V3 position: RTL against the floating-point reference (deg el)

| Case | Head | RTL vs true max / rms | RTL vs true, mean removed max | RTL vs float reference max | tracked vs true (after settle) max, mean removed | lock (pairs) | velocity rel. error |
| --- | --- | --- | --- | --- | --- | --- | --- |
| cal_neg | ofs -0.065, gain 0.8, ph -10.0 deg, h3 0.01, f -1 kHz, noise 0.0 LSB, cal reference, extrap 0 | 0.215 / 0.167 | 0.058 | 0.0214 | 0.056 | 43 | +0.0031 |
| cal_noise | ofs 0.065, gain 1.25, ph 10.0 deg, h3 0.01, f 1 kHz, noise 0.5 LSB, cal reference, extrap 0 | 0.207 / 0.126 | 0.086 | 0.0222 | 0.055 | 41 | -0.0099 |
| cal | ofs 0.065, gain 1.25, ph 10.0 deg, h3 0.01, f 1 kHz, noise 0.0 LSB, cal reference, extrap 0 | 0.173 / 0.128 | 0.054 | 0.0233 | 0.035 | 40 | -0.0110 |
| cal_self | ofs 0.065, gain 1.25, ph 10.0 deg, h3 0.01, f 1 kHz, noise 0.0 LSB, cal self, extrap 0 | 0.555 / 0.310 | 0.446 | 0.0221 | 0.431 | 45 | -0.0071 |
| f22_100k_gap | ofs 0.065, gain 1.25, ph 10.0 deg, h3 0.01, f 100 kHz, noise 0.0 LSB, cal reference, extrap 0 | 0.161 / 0.127 | 0.053 | 0.0167 | 0.016 | 122 | -0.0001 |
| f22_208k_gap | ofs 0.065, gain 1.25, ph 10.0 deg, h3 0.01, f 208 kHz, noise 0.0 LSB, cal reference, extrap 0 | 0.177 / 0.127 | 0.051 | 0.0231 | 0.020 | 1518 | -0.0000 |
| f22_250k_a2x_gap | ofs 0.065, gain 1.25, ph 10.0 deg, h3 0.01, f 250 kHz, noise 0.0 LSB, cal reference, extrap 0 | 0.173 / 0.127 | 0.052 | 0.0206 | 0.013 | 514 | -0.0000 |
| f22_250k_alim_gap | ofs 0.065, gain 1.25, ph 10.0 deg, h3 0.01, f 250 kHz, noise 0.0 LSB, cal reference, extrap 0 | 0.173 / 0.130 | 0.056 | 0.0206 | 0.014 | 533 | -0.0000 |
| f22_250k_amax_gap | ofs 0.065, gain 1.25, ph 10.0 deg, h3 0.01, f 250 kHz, noise 0.5 LSB, cal reference, extrap 0 | 0.214 / 0.128 | 0.098 | 0.0219 | 0.034 | 531 | -0.0000 |
| f22_250k_gap | ofs 0.065, gain 1.25, ph 10.0 deg, h3 0.01, f 250 kHz, noise 0.0 LSB, cal reference, extrap 0 | 0.180 / 0.128 | 0.054 | 0.0229 | 0.011 | 1522 | -0.0000 |
| f22_250k | ofs 0.065, gain 1.25, ph 10.0 deg, h3 0.01, f 250 kHz, noise 0.0 LSB, cal reference, extrap 0 | 0.180 / 0.128 | 0.054 | 0.0229 | 0.011 | 1544 | -0.0000 |
| fast_100k | ofs 0.065, gain 1.25, ph 10.0 deg, h3 0.01, f 100 kHz, noise 0.0 LSB, cal reference, extrap 0 | 0.125 / 0.114 | 0.016 | 0.0084 | 0.004 | 98 | -0.0001 |
| fast_k0 | ofs 0.065, gain 1.25, ph 10.0 deg, h3 0.01, f 50 kHz, noise 0.0 LSB, cal reference, extrap 0 | 0.163 / 0.127 | 0.037 | 0.0113 | 0.009 | 72 | -0.0001 |
| fast_k30 | ofs 0.065, gain 1.25, ph 10.0 deg, h3 0.01, f 50 kHz, noise 0.0 LSB, cal reference, extrap 30 | 0.163 / 0.127 | 0.037 | 0.0113 | 0.009 | 73 | -0.0001 |
| ideal | ofs 0.0, gain 1.0, ph 0.0 deg, h3 0.0, f 1 kHz, noise 0.0 LSB, cal none, extrap 0 | 0.029 / 0.012 | 0.029 | 0.0071 | 0.019 | 40 | -0.0119 |
| uncal | ofs 0.065, gain 1.25, ph 10.0 deg, h3 0.01, f 1 kHz, noise 0.0 LSB, cal none, extrap 0 | 13.946 / 8.477 | 12.448 | 0.0088 | 13.456 | 2000 | -0.0032 |

## Count safety with the D18 22-tick encoder frame (revision 0.3)

Criterion: after acquisition, the per-frame step of the tracked output differs from the true step by less than one count (90 deg el), and the multi-turn position (TURNS, POS) does not slip (offset at the end < 0.5 count). 'multi-turn drift' is the largest transient lag in counts; f22_250k_alim_gap (model limit) and f22_250k_a2x_gap (2 x the design acceleration) are information only.

| Case | ticks/frame | f end (kHz) | deg el per frame | from pair | max step error (deg el) | multi-turn drift (counts) | max tracking error incl. ramp (deg el) | after ramp/settle, mean removed (deg el) | skip / max gap (ticks) | acc (Hz/s) | frames with error > 45 deg |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| f22_100k_gap | 22 | 100 | 26.4 | 122 | 0.034 | 0.0057 | 0.498 | 0.0161 | 68 / 44 | - | 0 |
| f22_208k_gap | 22 | 208 | 54.9 | 200 | 0.782 | 0.0426 | 4.610 | 0.0197 | 68 / 44 | - | 0 |
| f22_250k | 22 | 250 | 66.0 | 200 | 0.171 | 0.0522 | 4.687 | 0.0109 | 0 / 22 | - | 0 |
| f22_250k_a2x_gap | 22 | 250 | 66.0 | 200 | 50.326 | 1.0041 | 90.379 | 0.0131 | 68 / 44 | 4000000000.0 | 102 |
| f22_250k_alim_gap | 22 | 250 | 66.0 | 200 | 42.246 | 0.8856 | 79.716 | 0.0138 | 68 / 44 | 2500000000.0 | 78 |
| f22_250k_amax_gap | 22 | 250 | 66.0 | 200 | 9.117 | 0.5962 | 53.667 | 0.0337 | 68 / 44 | 2000000000.0 | 14 |
| f22_250k_gap | 22 | 250 | 66.0 | 200 | 0.956 | 0.0521 | 5.631 | 0.0115 | 68 / 44 | - | 0 |

## (b..f) chip-level testbench

| Log | Checks | Failed | Verdict |
| --- | --- | --- | --- |
| top_biss_23.810.log | 48 | 0 | passed |
| top_biss_33.333.log | 48 | 0 | passed |
| top_biss_47.619.log | 48 | 0 | passed |
| top_cal_23.810.log | 32 | 0 | passed |
| top_cal_33.333.log | 32 | 0 | passed |
| top_gate_33.333.log | 22 | 0 | passed |
| top_safe_33.333.log | 32 | 0 | passed |
| top_spi_33.333.log | 26 | 0 | passed |
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
- `top_biss_23.810.log`: biss timeout measured 14.373 us, 600 ticks = 14.286 us
- `top_biss_23.810.log`: biss latch frame 0: busy 2 MT 5 ST 0x06558 nE nW 11 crc 01/01 head 0.09885 err 0.042 deg
- `top_biss_23.810.log`: biss latch frame 1: busy 2 MT 5 ST 0x320d1 nE nW 11 crc 1c/1c head 0.78205 err 0.002 deg
- `top_biss_23.810.log`: biss latch frame 2: busy 2 MT 6 ST 0x1dc72 nE nW 11 crc 0b/0b head 0.46516 err 0.042 deg
- `top_biss_23.810.log`: biss latch frame 3: busy 2 MT 7 ST 0x097df nE nW 11 crc 3e/3e head 0.14827 err 0.014 deg
- `top_biss_23.810.log`: biss latch frame 4: busy 2 MT 7 ST 0x35349 nE nW 11 crc 1b/1b head 0.83138 err 0.018 deg
- `top_biss_23.810.log`: biss latch frame 5: busy 2 MT 8 ST 0x20ee9 nE nW 11 crc 0e/0e head 0.51449 err 0.024 deg
- `top_biss_23.810.log`: biss latch: max |position at LAT - head angle at LAT| = 0.042 deg el at 10 kHz el
- `top_biss_23.810.log`: biss LAT_HALF=0 at 100 kHz el: latch error 0.025 .. 0.861 deg el, spread 0.836 deg (1 tick = 0.857 deg)
- `top_biss_23.810.log`: biss LAT_HALF=1 at 100 kHz el: latch error 0.023 .. 0.424 deg el, spread 0.401 deg (1 tick = 0.857 deg)
- `top_biss_23.810.log`: biss cc read 0x42: CDS[1..32] 01111000000001010000000000000001
- `top_biss_23.810.log`: biss cc error counter 0 -> 3
- `top_biss_33.333.log`: biss f_MA=80000 Hz duty_high=0.4 t_busy=2 T_MA timeout=20.11 us
- `top_biss_33.333.log`: biss f_MA=80000 Hz duty_high=0.6 t_busy=2 T_MA timeout=20.11 us
- `top_biss_33.333.log`: biss f_MA=250000 Hz duty_high=0.4 t_busy=2 T_MA timeout=20.10 us
- `top_biss_33.333.log`: biss f_MA=250000 Hz duty_high=0.6 t_busy=2 T_MA timeout=20.10 us
- `top_biss_33.333.log`: biss f_MA=1000000 Hz duty_high=0.4 t_busy=2 T_MA timeout=20.13 us
- `top_biss_33.333.log`: biss f_MA=1000000 Hz duty_high=0.6 t_busy=2 T_MA timeout=20.10 us
- `top_biss_33.333.log`: biss f_MA=5000000 Hz duty_high=0.4 t_busy=2 T_MA timeout=20.11 us
- `top_biss_33.333.log`: biss f_MA=5000000 Hz duty_high=0.6 t_busy=2 T_MA timeout=20.12 us
- `top_biss_33.333.log`: biss f_MA=10000000 Hz duty_high=0.4 t_busy=3 T_MA timeout=20.11 us
- `top_biss_33.333.log`: biss f_MA=10000000 Hz duty_high=0.6 t_busy=3 T_MA timeout=20.13 us
- `top_biss_33.333.log`: biss timeout measured 20.134 us, 600 ticks = 20.000 us
- `top_biss_33.333.log`: biss latch frame 0: busy 2 MT 4 ST 0x24d3e nE nW 11 crc 37/37 head 0.57517 err 0.093 deg
- `top_biss_33.333.log`: biss latch frame 1: busy 2 MT 5 ST 0x143c4 nE nW 11 crc 3c/3c head 0.31591 err 0.095 deg
- `top_biss_33.333.log`: biss latch frame 2: busy 2 MT 6 ST 0x03a17 nE nW 11 crc 36/36 head 0.05660 err 0.045 deg
- `top_biss_33.333.log`: biss latch frame 3: busy 2 MT 6 ST 0x33080 nE nW 11 crc 34/34 head 0.79728 err 0.029 deg
- `top_biss_33.333.log`: biss latch frame 4: busy 2 MT 7 ST 0x22717 nE nW 11 crc 2d/2d head 0.53796 err 0.076 deg
- `top_biss_33.333.log`: biss latch frame 5: busy 2 MT 8 ST 0x11d95 nE nW 11 crc 3c/3c head 0.27864 err 0.088 deg
- `top_biss_33.333.log`: biss latch: max |position at LAT - head angle at LAT| = 0.095 deg el at 10 kHz el
- `top_biss_33.333.log`: biss LAT_HALF=0 at 100 kHz el: latch error 0.016 .. 1.210 deg el, spread 1.194 deg (1 tick = 1.200 deg)
- `top_biss_33.333.log`: biss LAT_HALF=1 at 100 kHz el: latch error -0.008 .. 0.578 deg el, spread 0.585 deg (1 tick = 1.200 deg)
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
- `top_biss_47.619.log`: biss latch frame 0: busy 2 MT 5 ST 0x12ddd nE nW 11 crc 2f/2f head 0.29455 err 0.084 deg
- `top_biss_47.619.log`: biss latch frame 1: busy 2 MT 6 ST 0x07cc0 nE nW 11 crc 37/37 head 0.12158 err 0.087 deg
- `top_biss_47.619.log`: biss latch frame 2: busy 2 MT 6 ST 0x3cb35 nE nW 11 crc 1f/1f head 0.94827 err 0.061 deg
- `top_biss_47.619.log`: biss latch frame 3: busy 2 MT 7 ST 0x319c9 nE nW 11 crc 3e/3e head 0.77495 err 0.081 deg
- `top_biss_47.619.log`: biss latch frame 4: busy 2 MT 8 ST 0x26860 nE nW 11 crc 2e/2e head 0.60163 err 0.106 deg
- `top_biss_47.619.log`: biss latch frame 5: busy 2 MT 9 ST 0x1b6f0 nE nW 11 crc 20/20 head 0.42832 err 0.117 deg
- `top_biss_47.619.log`: biss latch: max |position at LAT - head angle at LAT| = 0.117 deg el at 10 kHz el
- `top_biss_47.619.log`: biss LAT_HALF=0 at 100 kHz el: latch error 0.070 .. 1.689 deg el, spread 1.619 deg (1 tick = 1.714 deg)
- `top_biss_47.619.log`: biss LAT_HALF=1 at 100 kHz el: latch error 0.060 .. 0.851 deg el, spread 0.791 deg (1 tick = 1.714 deg)
- `top_biss_47.619.log`: biss cc read 0x42: CDS[1..32] 01111000000001010000000000000001
- `top_biss_47.619.log`: biss cc error counter 0 -> 3
- `top_cal_23.810.log`: cal round 0 OC_A  ofs   1.300 hy 2.500: RTL 31 exh 0, model 31 exh 0
- `top_cal_23.810.log`: cal round 0 NEG_A ofs  -2.600 hy 3.100: RTL 34 exh 0, model 34 exh 0
- `top_cal_23.810.log`: cal round 0 OC_B  ofs   0.400 hy 1.700: RTL 32 exh 0, model 32 exh 0
- `top_cal_23.810.log`: cal round 0 NEG_B ofs  -0.200 hy 2.900: RTL 32 exh 0, model 32 exh 0
- `top_cal_23.810.log`: cal round 0: 4125 ticks, 14 az windows
- `top_cal_23.810.log`: cal CMP_CAL_A 0x221f CMP_CAL_B 0x2020
- `top_cal_23.810.log`: cal round 1 OC_A  ofs   3.900 hy 3.300: RTL 28 exh 0, model 28 exh 0
- `top_cal_23.810.log`: cal round 1 NEG_A ofs  -3.700 hy 0.600: RTL 36 exh 0, model 36 exh 0
- `top_cal_23.810.log`: cal round 1 OC_B  ofs   0.000 hy 4.000: RTL 32 exh 0, model 32 exh 0
- `top_cal_23.810.log`: cal round 1 NEG_B ofs   2.200 hy 1.000: RTL 29 exh 0, model 29 exh 0
- `top_cal_23.810.log`: cal round 1: 4254 ticks, 14 az windows
- `top_cal_23.810.log`: cal round 2 OC_A  ofs  24.000 hy 2.000: RTL 8 exh 0, model 8 exh 0
- `top_cal_23.810.log`: cal round 2 NEG_A ofs -40.000 hy 2.000: RTL 63 exh 1, model 0 exh 1
- `top_cal_23.810.log`: cal round 2 OC_B  ofs  45.000 hy 2.000: RTL 0 exh 1, model 0 exh 1
- `top_cal_23.810.log`: cal round 2 NEG_B ofs -24.000 hy 2.000: RTL 56 exh 0, model 56 exh 0
- `top_cal_23.810.log`: cal round 2: 4077 ticks, 14 az windows
- `top_cal_23.810.log`: cal round 3 OC_A  ofs -27.000 hy 2.000: RTL 59 exh 1, model 0 exh 1
- `top_cal_23.810.log`: cal round 3 NEG_A ofs  27.000 hy 2.500: RTL 5 exh 1, model 0 exh 1
- `top_cal_23.810.log`: cal round 3 OC_B  ofs  27.500 hy 3.000: RTL 5 exh 0, model 5 exh 0
- `top_cal_23.810.log`: cal round 3 NEG_B ofs -28.500 hy 1.500: RTL 60 exh 0, model 60 exh 0
- `top_cal_23.810.log`: cal round 3: 4262 ticks, 14 az windows
- `top_cal_23.810.log`: cal round 4 OC_A  ofs   4.600 hy 0.648: RTL 28 exh 0, model 28 exh 0
- `top_cal_23.810.log`: cal round 4 NEG_A ofs  19.840 hy 1.536: RTL 12 exh 0, model 12 exh 0
- `top_cal_23.810.log`: cal round 4 OC_B  ofs   9.640 hy 4.080: RTL 22 exh 0, model 22 exh 0
- `top_cal_23.810.log`: cal round 4 NEG_B ofs  -7.760 hy 2.736: RTL 40 exh 0, model 40 exh 0
- `top_cal_23.810.log`: cal round 4: 4077 ticks, 14 az windows
- `top_cal_23.810.log`: cal round 5 OC_A  ofs -12.840 hy 2.716: RTL 45 exh 0, model 45 exh 0
- `top_cal_23.810.log`: cal round 5 NEG_A ofs  -6.200 hy 3.760: RTL 38 exh 0, model 38 exh 0
- `top_cal_23.810.log`: cal round 5 OC_B  ofs  12.340 hy 1.008: RTL 20 exh 0, model 20 exh 0
- `top_cal_23.810.log`: cal round 5 NEG_B ofs -11.660 hy 1.956: RTL 44 exh 0, model 44 exh 0
- `top_cal_23.810.log`: cal round 5: 4077 ticks, 14 az windows
- `top_cal_23.810.log`: cal round 6 OC_A  ofs  16.100 hy 1.368: RTL 16 exh 0, model 16 exh 0
- `top_cal_23.810.log`: cal round 6 NEG_A ofs -16.180 hy 2.200: RTL 48 exh 0, model 48 exh 0
- `top_cal_23.810.log`: cal round 6 OC_B  ofs  14.540 hy 3.916: RTL 17 exh 0, model 17 exh 0
- `top_cal_23.810.log`: cal round 6 NEG_B ofs  13.820 hy 3.976: RTL 18 exh 0, model 18 exh 0
- `top_cal_23.810.log`: cal round 6: 4077 ticks, 14 az windows
- `top_cal_23.810.log`: cal round 7 OC_A  ofs  14.100 hy 3.360: RTL 18 exh 0, model 18 exh 0
- `top_cal_23.810.log`: cal round 7 NEG_A ofs   4.100 hy 2.652: RTL 28 exh 0, model 28 exh 0
- `top_cal_23.810.log`: cal round 7 OC_B  ofs -19.840 hy 1.780: RTL 52 exh 0, model 52 exh 0
- `top_cal_23.810.log`: cal round 7 NEG_B ofs -18.100 hy 3.948: RTL 50 exh 0, model 50 exh 0
- `top_cal_23.810.log`: cal round 7: 4077 ticks, 14 az windows
- `top_cal_23.810.log`: cal round 8 OC_A  ofs  -1.220 hy 2.012: RTL 33 exh 0, model 33 exh 0
- `top_cal_23.810.log`: cal round 8 NEG_A ofs  -5.500 hy 1.548: RTL 37 exh 0, model 37 exh 0
- `top_cal_23.810.log`: cal round 8 OC_B  ofs -15.900 hy 2.684: RTL 48 exh 0, model 48 exh 0
- `top_cal_23.810.log`: cal round 8 NEG_B ofs  -2.760 hy 1.908: RTL 35 exh 0, model 35 exh 0
- `top_cal_23.810.log`: cal round 8: 4077 ticks, 14 az windows
- `top_cal_23.810.log`: cal round 9 OC_A  ofs  -1.720 hy 0.672: RTL 34 exh 0, model 34 exh 0
- `top_cal_23.810.log`: cal round 9 NEG_A ofs  19.120 hy 4.188: RTL 13 exh 0, model 13 exh 0
- `top_cal_23.810.log`: cal round 9 OC_B  ofs -16.400 hy 3.288: RTL 49 exh 0, model 49 exh 0
- `top_cal_23.810.log`: cal round 9 NEG_B ofs   5.480 hy 1.548: RTL 26 exh 0, model 26 exh 0
- `top_cal_23.810.log`: cal round 9: 4077 ticks, 14 az windows
- `top_cal_33.333.log`: cal round 0 OC_A  ofs   1.300 hy 2.500: RTL 31 exh 0, model 31 exh 0
- `top_cal_33.333.log`: cal round 0 NEG_A ofs  -2.600 hy 3.100: RTL 34 exh 0, model 34 exh 0
- `top_cal_33.333.log`: cal round 0 OC_B  ofs   0.400 hy 1.700: RTL 32 exh 0, model 32 exh 0
- `top_cal_33.333.log`: cal round 0 NEG_B ofs  -0.200 hy 2.900: RTL 32 exh 0, model 32 exh 0
- `top_cal_33.333.log`: cal round 0: 4120 ticks, 14 az windows
- `top_cal_33.333.log`: cal CMP_CAL_A 0x221f CMP_CAL_B 0x2020
- `top_cal_33.333.log`: cal round 1 OC_A  ofs   3.900 hy 3.300: RTL 28 exh 0, model 28 exh 0
- `top_cal_33.333.log`: cal round 1 NEG_A ofs  -3.700 hy 0.600: RTL 36 exh 0, model 36 exh 0
- `top_cal_33.333.log`: cal round 1 OC_B  ofs   0.000 hy 4.000: RTL 32 exh 0, model 32 exh 0
- `top_cal_33.333.log`: cal round 1 NEG_B ofs   2.200 hy 1.000: RTL 29 exh 0, model 29 exh 0
- `top_cal_33.333.log`: cal round 1: 4282 ticks, 14 az windows
- `top_cal_33.333.log`: cal round 2 OC_A  ofs  24.000 hy 2.000: RTL 8 exh 0, model 8 exh 0
- `top_cal_33.333.log`: cal round 2 NEG_A ofs -40.000 hy 2.000: RTL 63 exh 1, model 0 exh 1
- `top_cal_33.333.log`: cal round 2 OC_B  ofs  45.000 hy 2.000: RTL 0 exh 1, model 0 exh 1
- `top_cal_33.333.log`: cal round 2 NEG_B ofs -24.000 hy 2.000: RTL 56 exh 0, model 56 exh 0
- `top_cal_33.333.log`: cal round 2: 4108 ticks, 14 az windows
- `top_cal_33.333.log`: cal round 3 OC_A  ofs -27.000 hy 2.000: RTL 59 exh 1, model 0 exh 1
- `top_cal_33.333.log`: cal round 3 NEG_A ofs  27.000 hy 2.500: RTL 5 exh 1, model 0 exh 1
- `top_cal_33.333.log`: cal round 3 OC_B  ofs  27.500 hy 3.000: RTL 5 exh 0, model 5 exh 0
- `top_cal_33.333.log`: cal round 3 NEG_B ofs -28.500 hy 1.500: RTL 60 exh 0, model 60 exh 0
- `top_cal_33.333.log`: cal round 3: 4180 ticks, 14 az windows
- `top_cal_33.333.log`: cal round 4 OC_A  ofs   4.600 hy 0.648: RTL 28 exh 0, model 28 exh 0
- `top_cal_33.333.log`: cal round 4 NEG_A ofs  19.840 hy 1.536: RTL 12 exh 0, model 12 exh 0
- `top_cal_33.333.log`: cal round 4 OC_B  ofs   9.640 hy 4.080: RTL 22 exh 0, model 22 exh 0
- `top_cal_33.333.log`: cal round 4 NEG_B ofs  -7.760 hy 2.736: RTL 40 exh 0, model 40 exh 0
- `top_cal_33.333.log`: cal round 4: 4108 ticks, 14 az windows
- `top_cal_33.333.log`: cal round 5 OC_A  ofs -12.840 hy 2.716: RTL 45 exh 0, model 45 exh 0
- `top_cal_33.333.log`: cal round 5 NEG_A ofs  -6.200 hy 3.760: RTL 38 exh 0, model 38 exh 0
- `top_cal_33.333.log`: cal round 5 OC_B  ofs  12.340 hy 1.008: RTL 20 exh 0, model 20 exh 0
- `top_cal_33.333.log`: cal round 5 NEG_B ofs -11.660 hy 1.956: RTL 44 exh 0, model 44 exh 0
- `top_cal_33.333.log`: cal round 5: 4108 ticks, 14 az windows
- `top_cal_33.333.log`: cal round 6 OC_A  ofs  16.100 hy 1.368: RTL 16 exh 0, model 16 exh 0
- `top_cal_33.333.log`: cal round 6 NEG_A ofs -16.180 hy 2.200: RTL 48 exh 0, model 48 exh 0
- `top_cal_33.333.log`: cal round 6 OC_B  ofs  14.540 hy 3.916: RTL 17 exh 0, model 17 exh 0
- `top_cal_33.333.log`: cal round 6 NEG_B ofs  13.820 hy 3.976: RTL 18 exh 0, model 18 exh 0
- `top_cal_33.333.log`: cal round 6: 4108 ticks, 14 az windows
- `top_cal_33.333.log`: cal round 7 OC_A  ofs  14.100 hy 3.360: RTL 18 exh 0, model 18 exh 0
- `top_cal_33.333.log`: cal round 7 NEG_A ofs   4.100 hy 2.652: RTL 28 exh 0, model 28 exh 0
- `top_cal_33.333.log`: cal round 7 OC_B  ofs -19.840 hy 1.780: RTL 52 exh 0, model 52 exh 0
- `top_cal_33.333.log`: cal round 7 NEG_B ofs -18.100 hy 3.948: RTL 50 exh 0, model 50 exh 0
- `top_cal_33.333.log`: cal round 7: 4108 ticks, 14 az windows
- `top_cal_33.333.log`: cal round 8 OC_A  ofs  -1.220 hy 2.012: RTL 33 exh 0, model 33 exh 0
- `top_cal_33.333.log`: cal round 8 NEG_A ofs  -5.500 hy 1.548: RTL 37 exh 0, model 37 exh 0
- `top_cal_33.333.log`: cal round 8 OC_B  ofs -15.900 hy 2.684: RTL 48 exh 0, model 48 exh 0
- `top_cal_33.333.log`: cal round 8 NEG_B ofs  -2.760 hy 1.908: RTL 35 exh 0, model 35 exh 0
- `top_cal_33.333.log`: cal round 8: 4108 ticks, 14 az windows
- `top_cal_33.333.log`: cal round 9 OC_A  ofs  -1.720 hy 0.672: RTL 34 exh 0, model 34 exh 0
- `top_cal_33.333.log`: cal round 9 NEG_A ofs  19.120 hy 4.188: RTL 13 exh 0, model 13 exh 0
- `top_cal_33.333.log`: cal round 9 OC_B  ofs -16.400 hy 3.288: RTL 49 exh 0, model 49 exh 0
- `top_cal_33.333.log`: cal round 9 NEG_B ofs   5.480 hy 1.548: RTL 26 exh 0, model 26 exh 0
- `top_cal_33.333.log`: cal round 9: 4108 ticks, 14 az windows
- `top_gate_33.333.log`: gate A on 16 off 586 (width 570), B on 516 off 786 (width 270), C on 1016 off 386 (width 870); current frame start 301 is_smp 301; az_win 1201..1241
- `top_gate_33.333.log`: gate encoder frames in one period 67: 65 gaps of 22 ticks, 1 other, longest 48 ticks
- `top_gate_33.333.log`: gate with ADC_A_W13 = 8530: I_A 2948 I_B 2848
- `top_safe_33.333.log`: safe cmp[0]: FAULT 0x0001, FAULT_N low after 4 ticks
- `top_safe_33.333.log`: safe cmp[1]: FAULT 0x0002, FAULT_N low after 4 ticks
- `top_safe_33.333.log`: safe cmp[2]: FAULT 0x0004, FAULT_N low after 4 ticks
- `top_safe_33.333.log`: safe cmp[3]: FAULT 0x0008, FAULT_N low after 4 ticks
- `top_safe_33.333.log`: safe TEMP count 273 (2 MHz over 4096 ticks, expected 273.1)
- `top_safe_33.333.log`: safe watchdog fired 4091 ticks after the last SPI frame (period 4096 ticks)
- `top_safe_33.333.log`: safe FAULT before I2t 0x0000
- `top_safe_33.333.log`: safe I2t: trip after 30847 ticks = 102.8 PWM periods; integer model 103 updates; closed form 102.20 updates
- `top_spi_33.333.log`: OSC_COUNT = 480, expected 480.0 (16 us of 33.333 ns ticks)
- `top_spi_33.333.log`: spi/biss frame: busy 2 data 0x12345 nE nW 11 crc wire 0d calc~ 0d ack 1
- `top_ssi_23.810.log`: ssi gray=0 data 0x0000099a expected 0x0000099a monoflop 14.37 us
- `top_ssi_23.810.log`: ssi gray=1 data 0x00000d57 expected 0x00000d57 monoflop 14.37 us
- `top_ssi_23.810.log`: ssi clk 23.810 ns: OSC_COUNT 672 -> TIMEOUT_TICKS 840, monoflop 20.09 us (600 ticks untrimmed = 14.29 us)
- `top_ssi_33.333.log`: ssi gray=0 data 0x0000099a expected 0x0000099a monoflop 20.10 us
- `top_ssi_33.333.log`: ssi gray=1 data 0x00000d57 expected 0x00000d57 monoflop 20.10 us
- `top_ssi_33.333.log`: ssi clk 33.333 ns: OSC_COUNT 480 -> TIMEOUT_TICKS 600, monoflop 20.12 us (600 ticks untrimmed = 20.00 us)
- `top_ssi_47.619.log`: ssi gray=0 data 0x0000099a expected 0x0000099a monoflop 28.72 us
- `top_ssi_47.619.log`: ssi gray=1 data 0x00000d57 expected 0x00000d57 monoflop 28.73 us
- `top_ssi_47.619.log`: ssi clk 47.619 ns: OSC_COUNT 336 -> TIMEOUT_TICKS 420, monoflop 20.16 us (600 ticks untrimmed = 28.57 us)

## Synthesis (Yosys, sg13g2_stdcell typ 1.2 V 25 C, Booth, PDK latch map, abc -D 23810)

- cells 14777, flops 1985, cell area 219649 um2 (30.3 kGE at 7.26 um2 per nand2_1), sequential 91364 um2 (42 %)
- ratio of cell area to the 0.18 mm2 cell-area target (0.28 mm2 placed at about 65 %): 1.22
- macro estimate at the G1 run7 ratio (129 600 um2 macro / 84 796 um2 synthesis): 0.336 mm2 = 1.87 x budget
- per block, children included (hierarchical synthesis, total 225446 um2; the flat run optimises across blocks): r1_pos 65135, r1_regs 59305, r1_gate 39365, r1_safe 22999, r1_biss 16508, r1_cmpcal 11606, r1_spi 6132, r1_ctrl_top (glue) 4118, r1_idrom 180, r1_sync2 98

## ADC weight correction (r1_adcw, tb_adcw + adcw_ref.py, mismatched-CDAC example)

| Weights | max abs DNL (LSB) | max abs INL (LSB) | missing codes | RTL vs integer model mismatches |
| --- | --- | --- | --- | --- |
| nominal r1_adc rev 3 (reset) | 3.375 | 4.020 | 6 | 0 |
| calibrated (1/4 LSB) | 0.438 | 0.597 | 0 | 0 |

Model-only weight-resolution sweep (same raw decisions): exact: DNL 0.375, INL 0.309, missing 1; 1/2_lsb: DNL 0.688, INL 0.961, missing 1; 1/4_lsb: DNL 0.438, INL 0.597, missing 1; 1/8_lsb: DNL 0.375, INL 0.331, missing 1; 1/16_lsb: DNL 0.375, INL 0.284, missing 1
Checks: {'rtl_bit_exact': True, 'mismatch_example_shows_error_with_nominal_weights': True, 'calibrated_no_missing_dnl_lt_1_inl_le_1': True}; verdict passed.

## Comparator calibration search (r1_cmpcal 0.3) vs r1_safe cal_model.py

- Model: passed: implemented search (half-code CAL_IDEAL) vs r1_safe cal_model on 274 comparator samples: exact 274, within 1 code 274, EXH mismatches 0, initial-state dependence 0; brief wording (6-bit integer CAL_IDEAL): exact 171, within 1 274. cal_model stored k_cal reproduced on 214/214, transient in-sample k_cal reproduced on 60/60
- RTL: passed: RTL (tb_top +test=calmc) vs Python model of the search: 274/274 identical (code and EXH); RTL vs r1_safe cal_model within 1 code: 274/274
- Inputs (r1_safe results, read-only): cal-model-20261020-r3, cal-model-corner-20261020-r3, safe-dcmc-20261020-r3rppd, safe-dcmc-20261020-r3, safe-dccorner-20261020-r3, safe-mc-20261020-r3

# r1_ctrl run r1ctrl_20261028_v09b

Tools: Icarus Verilog version 14.0 (devel) (s20260301-328-geda9fdcd-dirty); Yosys 0.67 (git sha1 2d1509d1b, Release, GNU /usr/bin/c++ 13.3.0); Python 3.12.3 numpy 2.5.1; PDK commit 84374023ee8b4b126bebbba67fcbada0a9c0ff0b. Date 2026-10-28T06:56:05Z.

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
| top_ana_33.333.log | 9 | 0 | passed |
| top_biss_23.810.log | 48 | 0 | passed |
| top_biss_33.333.log | 48 | 0 | passed |
| top_biss_47.619.log | 48 | 0 | passed |
| top_cal_23.810.log | 32 | 0 | passed |
| top_cal_33.333.log | 32 | 0 | passed |
| top_cdc_23.810.log | 4 | 0 | passed |
| top_cdc_33.333.log | 4 | 0 | passed |
| top_cdc_47.619.log | 4 | 0 | passed |
| top_d22_23.810.log | 17 | 0 | passed |
| top_d22_33.333.log | 17 | 0 | passed |
| top_d22_47.619.log | 17 | 0 | passed |
| top_d27_23.810.log | 24 | 0 | passed |
| top_d27_33.333.log | 24 | 0 | passed |
| top_d27_47.619.log | 24 | 0 | passed |
| top_disc_33.333.log | 14 | 0 | passed |
| top_gate_33.333.log | 22 | 0 | passed |
| top_safe_33.333.log | 32 | 0 | passed |
| top_spi_33.333.log | 27 | 0 | passed |
| top_ssi_23.810.log | 9 | 0 | passed |
| top_ssi_33.333.log | 9 | 0 | passed |
| top_ssi_47.619.log | 9 | 0 | passed |
| top_tap_23.810.log | 5 | 0 | passed |
| top_tap_33.333.log | 5 | 0 | passed |
| top_v07_23.810.log | 36 | 0 | passed |
| top_v07_33.333.log | 40 | 0 | passed |
| top_v07_47.619.log | 40 | 0 | passed |

Information lines:

- `top_biss_23.810.log`: biss f_MA=80000 Hz duty_high=0.4 t_busy=2 T_MA timeout=14.40 us
- `top_biss_23.810.log`: biss f_MA=80000 Hz duty_high=0.6 t_busy=2 T_MA timeout=14.40 us
- `top_biss_23.810.log`: biss f_MA=250000 Hz duty_high=0.4 t_busy=2 T_MA timeout=14.40 us
- `top_biss_23.810.log`: biss f_MA=250000 Hz duty_high=0.6 t_busy=2 T_MA timeout=14.39 us
- `top_biss_23.810.log`: biss f_MA=1000000 Hz duty_high=0.4 t_busy=2 T_MA timeout=14.39 us
- `top_biss_23.810.log`: biss f_MA=1000000 Hz duty_high=0.6 t_busy=2 T_MA timeout=14.40 us
- `top_biss_23.810.log`: biss f_MA=5000000 Hz duty_high=0.4 t_busy=2 T_MA timeout=14.38 us
- `top_biss_23.810.log`: biss f_MA=5000000 Hz duty_high=0.6 t_busy=2 T_MA timeout=14.40 us
- `top_biss_23.810.log`: biss f_MA=10000000 Hz duty_high=0.4 t_busy=3 T_MA timeout=14.40 us
- `top_biss_23.810.log`: biss f_MA=10000000 Hz duty_high=0.6 t_busy=3 T_MA timeout=14.39 us
- `top_biss_23.810.log`: biss timeout measured 14.396 us, 600 ticks = 14.286 us
- `top_biss_23.810.log`: biss latch frame 0: busy 2 MT 4 ST 0x18da9 nE nW 11 crc 11/11 head 0.38814 err 0.071 deg
- `top_biss_23.810.log`: biss latch frame 1: busy 2 MT 5 ST 0x0494c nE nW 11 crc 1e/1e head 0.07158 err 0.001 deg
- `top_biss_23.810.log`: biss latch frame 2: busy 2 MT 5 ST 0x30501 nE nW 11 crc 02/02 head 0.75493 err 0.017 deg
- `top_biss_23.810.log`: biss latch frame 3: busy 2 MT 6 ST 0x1c0e9 nE nW 11 crc 3c/3c head 0.43828 err 0.038 deg
- `top_biss_23.810.log`: biss latch frame 4: busy 2 MT 7 ST 0x07c94 nE nW 11 crc 11/11 head 0.12162 err 0.013 deg
- `top_biss_23.810.log`: biss latch frame 5: busy 2 MT 7 ST 0x3383e nE nW 11 crc 01/01 head 0.80497 err 0.018 deg
- `top_biss_23.810.log`: biss latch: max |position at LAT - head angle at LAT| = 0.071 deg el at 10 kHz el
- `top_biss_23.810.log`: biss LAT_HALF=0 at 100 kHz el: latch error 0.043 .. 0.850 deg el, spread 0.807 deg (1 tick = 0.857 deg)
- `top_biss_23.810.log`: biss LAT_HALF=1 at 100 kHz el: latch error 0.028 .. 0.414 deg el, spread 0.386 deg (1 tick = 0.857 deg)
- `top_biss_23.810.log`: biss cc read 0x42: CDS[1..32] 01111000000001010000000000000001
- `top_biss_23.810.log`: biss cc error counter 0 -> 3
- `top_biss_33.333.log`: biss f_MA=80000 Hz duty_high=0.4 t_busy=2 T_MA timeout=20.14 us
- `top_biss_33.333.log`: biss f_MA=80000 Hz duty_high=0.6 t_busy=2 T_MA timeout=20.14 us
- `top_biss_33.333.log`: biss f_MA=250000 Hz duty_high=0.4 t_busy=2 T_MA timeout=20.14 us
- `top_biss_33.333.log`: biss f_MA=250000 Hz duty_high=0.6 t_busy=2 T_MA timeout=20.14 us
- `top_biss_33.333.log`: biss f_MA=1000000 Hz duty_high=0.4 t_busy=2 T_MA timeout=20.17 us
- `top_biss_33.333.log`: biss f_MA=1000000 Hz duty_high=0.6 t_busy=2 T_MA timeout=20.14 us
- `top_biss_33.333.log`: biss f_MA=5000000 Hz duty_high=0.4 t_busy=2 T_MA timeout=20.15 us
- `top_biss_33.333.log`: biss f_MA=5000000 Hz duty_high=0.6 t_busy=2 T_MA timeout=20.15 us
- `top_biss_33.333.log`: biss f_MA=10000000 Hz duty_high=0.4 t_busy=3 T_MA timeout=20.14 us
- `top_biss_33.333.log`: biss f_MA=10000000 Hz duty_high=0.6 t_busy=3 T_MA timeout=20.16 us
- `top_biss_33.333.log`: biss timeout measured 20.168 us, 600 ticks = 20.000 us
- `top_biss_33.333.log`: biss latch frame 0: busy 2 MT 4 ST 0x38157 nE nW 11 crc 1a/1a head 0.87618 err 0.048 deg
- `top_biss_33.333.log`: biss latch frame 1: busy 2 MT 5 ST 0x2783c nE nW 11 crc 33/33 head 0.61726 err 0.058 deg
- `top_biss_33.333.log`: biss latch frame 2: busy 2 MT 6 ST 0x16f21 nE nW 11 crc 15/15 head 0.35827 err 0.093 deg
- `top_biss_33.333.log`: biss latch frame 3: busy 2 MT 7 ST 0x065d2 nE nW 11 crc 1c/1c head 0.09929 err 0.053 deg
- `top_biss_33.333.log`: biss latch frame 4: busy 2 MT 7 ST 0x35c93 nE nW 11 crc 3d/3d head 0.84030 err 0.039 deg
- `top_biss_33.333.log`: biss latch frame 5: busy 2 MT 8 ST 0x25379 nE nW 11 crc 28/28 head 0.58132 err 0.072 deg
- `top_biss_33.333.log`: biss latch: max |position at LAT - head angle at LAT| = 0.093 deg el at 10 kHz el
- `top_biss_33.333.log`: biss LAT_HALF=0 at 100 kHz el: latch error 0.041 .. 1.205 deg el, spread 1.164 deg (1 tick = 1.200 deg)
- `top_biss_33.333.log`: biss LAT_HALF=1 at 100 kHz el: latch error -0.009 .. 0.575 deg el, spread 0.584 deg (1 tick = 1.200 deg)
- `top_biss_33.333.log`: biss cc read 0x42: CDS[1..32] 01111000000001010000000000000001
- `top_biss_33.333.log`: biss cc error counter 0 -> 3
- `top_biss_47.619.log`: biss f_MA=80000 Hz duty_high=0.4 t_busy=2 T_MA timeout=28.81 us
- `top_biss_47.619.log`: biss f_MA=80000 Hz duty_high=0.6 t_busy=2 T_MA timeout=28.78 us
- `top_biss_47.619.log`: biss f_MA=250000 Hz duty_high=0.4 t_busy=2 T_MA timeout=28.78 us
- `top_biss_47.619.log`: biss f_MA=250000 Hz duty_high=0.6 t_busy=2 T_MA timeout=28.77 us
- `top_biss_47.619.log`: biss f_MA=1000000 Hz duty_high=0.4 t_busy=2 T_MA timeout=28.77 us
- `top_biss_47.619.log`: biss f_MA=1000000 Hz duty_high=0.6 t_busy=2 T_MA timeout=28.78 us
- `top_biss_47.619.log`: biss f_MA=5000000 Hz duty_high=0.4 t_busy=3 T_MA timeout=28.80 us
- `top_biss_47.619.log`: biss f_MA=5000000 Hz duty_high=0.6 t_busy=2 T_MA timeout=28.81 us
- `top_biss_47.619.log`: biss f_MA=10000000 Hz duty_high=0.4 t_busy=3 T_MA timeout=28.78 us
- `top_biss_47.619.log`: biss f_MA=10000000 Hz duty_high=0.6 t_busy=3 T_MA timeout=28.80 us
- `top_biss_47.619.log`: biss timeout measured 28.777 us, 600 ticks = 28.571 us
- `top_biss_47.619.log`: biss latch frame 0: busy 2 MT 5 ST 0x27406 nE nW 11 crc 16/16 head 0.61313 err 0.061 deg
- `top_biss_47.619.log`: biss latch frame 1: busy 2 MT 6 ST 0x1c399 nE nW 11 crc 12/12 head 0.44064 err 0.133 deg
- `top_biss_47.619.log`: biss latch frame 2: busy 2 MT 7 ST 0x11296 nE nW 11 crc 21/21 head 0.26780 err 0.125 deg
- `top_biss_47.619.log`: biss latch frame 3: busy 2 MT 8 ST 0x06179 nE nW 11 crc 2b/2b head 0.09496 err 0.081 deg
- `top_biss_47.619.log`: biss latch frame 4: busy 2 MT 8 ST 0x3b073 nE nW 11 crc 10/10 head 0.92212 err 0.068 deg
- `top_biss_47.619.log`: biss latch frame 5: busy 2 MT 9 ST 0x2ff82 nE nW 11 crc 28/28 head 0.74928 err 0.085 deg
- `top_biss_47.619.log`: biss latch: max |position at LAT - head angle at LAT| = 0.133 deg el at 10 kHz el
- `top_biss_47.619.log`: biss LAT_HALF=0 at 100 kHz el: latch error 0.053 .. 1.703 deg el, spread 1.650 deg (1 tick = 1.714 deg)
- `top_biss_47.619.log`: biss LAT_HALF=1 at 100 kHz el: latch error 0.050 .. 0.856 deg el, spread 0.806 deg (1 tick = 1.714 deg)
- `top_biss_47.619.log`: biss cc read 0x42: CDS[1..32] 01111000000001010000000000000001
- `top_biss_47.619.log`: biss cc error counter 0 -> 3
- `top_cal_23.810.log`: cal round 0 OC_A  ofs   1.300 hy 2.500: RTL 31 exh 0, model 31 exh 0
- `top_cal_23.810.log`: cal round 0 NEG_A ofs  -2.600 hy 3.100: RTL 34 exh 0, model 34 exh 0
- `top_cal_23.810.log`: cal round 0 OC_B  ofs   0.400 hy 1.700: RTL 32 exh 0, model 32 exh 0
- `top_cal_23.810.log`: cal round 0 NEG_B ofs  -0.200 hy 2.900: RTL 32 exh 0, model 32 exh 0
- `top_cal_23.810.log`: cal round 0: 4132 ticks, 14 az windows
- `top_cal_23.810.log`: cal CMP_CAL_A 0x221f CMP_CAL_B 0x2020
- `top_cal_23.810.log`: cal round 1 OC_A  ofs   3.900 hy 3.300: RTL 28 exh 0, model 28 exh 0
- `top_cal_23.810.log`: cal round 1 NEG_A ofs  -3.700 hy 0.600: RTL 36 exh 0, model 36 exh 0
- `top_cal_23.810.log`: cal round 1 OC_B  ofs   0.000 hy 4.000: RTL 32 exh 0, model 32 exh 0
- `top_cal_23.810.log`: cal round 1 NEG_B ofs   2.200 hy 1.000: RTL 29 exh 0, model 29 exh 0
- `top_cal_23.810.log`: cal round 1: 4262 ticks, 14 az windows
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
- `top_cal_33.333.log`: cal round 0: 4140 ticks, 14 az windows
- `top_cal_33.333.log`: cal CMP_CAL_A 0x221f CMP_CAL_B 0x2020
- `top_cal_33.333.log`: cal round 1 OC_A  ofs   3.900 hy 3.300: RTL 28 exh 0, model 28 exh 0
- `top_cal_33.333.log`: cal round 1 NEG_A ofs  -3.700 hy 0.600: RTL 36 exh 0, model 36 exh 0
- `top_cal_33.333.log`: cal round 1 OC_B  ofs   0.000 hy 4.000: RTL 32 exh 0, model 32 exh 0
- `top_cal_33.333.log`: cal round 1 NEG_B ofs   2.200 hy 1.000: RTL 29 exh 0, model 29 exh 0
- `top_cal_33.333.log`: cal round 1: 4002 ticks, 14 az windows
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
- `top_cdc_23.810.log`: cdc: SSI 2 MHz, 16 clk phases, position changing every tick: pattern 0 7, pattern 1 9, mixed 0
- `top_cdc_23.810.log`: cdc: SSI 10 MHz (outside the 2 MHz limit), 16 clk phases: pattern 0 6, pattern 1 10, mixed 0 (information, not a check)
- `top_cdc_23.810.log`: cdc: ma_rst_n rising edges 35 (off a clk edge: 0), falling edges 35
- `top_cdc_33.333.log`: cdc: SSI 2 MHz, 16 clk phases, position changing every tick: pattern 0 4, pattern 1 12, mixed 0
- `top_cdc_33.333.log`: cdc: SSI 10 MHz (outside the 2 MHz limit), 16 clk phases: pattern 0 0, pattern 1 8, mixed 8 (information, not a check)
- `top_cdc_33.333.log`: cdc: ma_rst_n rising edges 35 (off a clk edge: 0), falling edges 35
- `top_cdc_47.619.log`: cdc: SSI 2 MHz, 16 clk phases, position changing every tick: pattern 0 7, pattern 1 9, mixed 0
- `top_cdc_47.619.log`: cdc: SSI 10 MHz (outside the 2 MHz limit), 16 clk phases: pattern 0 0, pattern 1 1, mixed 15 (information, not a check)
- `top_cdc_47.619.log`: cdc: ma_rst_n rising edges 35 (off a clk edge: 0), falling edges 35
- `top_d22_23.810.log`: d22 capture since reset: SIN 2394..3447 COS 691..3173
- `top_d22_23.810.log`: d22 capture: 770 pairs, RTL SIN 417..3792 COS 353..3628, model SIN 417..3792 COS 353..3628
- `top_d22_23.810.log`: d22 host calibration: SIN_OFS 57 COS_OFS -57 SIN_GAIN 0x00003f0d COS_GAIN 0x000040fa (A_t 1662.5 LSB)
- `top_d22_23.810.log`: d22 MEAS_ANGLE error at 16 static angles: before 3.518, after 0.0521 deg el; AMPLITUDE 1663 LSB
- `top_d22_33.333.log`: d22 capture since reset: SIN 2131..3447 COS 650..3170
- `top_d22_33.333.log`: d22 capture: 550 pairs, RTL SIN 417..3792 COS 353..3628, model SIN 417..3792 COS 353..3628
- `top_d22_33.333.log`: d22 host calibration: SIN_OFS 57 COS_OFS -57 SIN_GAIN 0x00003f0d COS_GAIN 0x000040fa (A_t 1662.5 LSB)
- `top_d22_33.333.log`: d22 MEAS_ANGLE error at 16 static angles: before 3.518, after 0.0521 deg el; AMPLITUDE 1663 LSB
- `top_d22_47.619.log`: d22 capture since reset: SIN 1730..3447 COS 648..3166
- `top_d22_47.619.log`: d22 capture: 385 pairs, RTL SIN 417..3792 COS 353..3628, model SIN 417..3792 COS 353..3628
- `top_d22_47.619.log`: d22 host calibration: SIN_OFS 57 COS_OFS -57 SIN_GAIN 0x00003f0d COS_GAIN 0x000040fa (A_t 1662.5 LSB)
- `top_d22_47.619.log`: d22 MEAS_ANGLE error at 16 static angles: before 3.518, after 0.0521 deg el; AMPLITUDE 1663 LSB
- `top_d27_23.810.log`: d27 reset words: I_A 1234 (raw 1234), I_B 2900 (raw 2900)
- `top_d27_23.810.log`: d27 vector 0: raw 822 / 1740, I_A 956 (model 956), I_B 888 (model 888)
- `top_d27_23.810.log`: d27 vector 1: raw 3000 / 1000, I_A 3113 (model 3113), I_B 0 (model 0)
- `top_d27_23.810.log`: d27 vector 2: raw 4095 / 0, I_A 4095 (model 4095), I_B 2048 (model 2048)
- `top_d27_23.810.log`: d27 vector 3: raw 0 / 4095, I_A 0 (model 0), I_B 4095 (model 4095)
- `top_d27_23.810.log`: d27 vector 4: raw 2049 / 2047, I_A 2049 (model 2049), I_B 2045 (model 2045)
- `top_d27_23.810.log`: d27 vector 5: raw 2051 / 2045, I_A 2050 (model 2050), I_B 2038 (model 2038)
- `top_d27_23.810.log`: d27 vector 6: raw 1500 / 2600, I_A 2048 (model 2048), I_B 4095 (model 4095)
- `top_d27_23.810.log`: d27 vector 7: raw 2500 / 1600, I_A 2499 (model 2499), I_B 707 (model 707)
- `top_d27_23.810.log`: d27 vector 8: raw 3700 / 400, I_A 3437 (model 3437), I_B 0 (model 0)
- `top_d27_23.810.log`: d27 vector 9: raw 1111 / 3333, I_A 659 (model 659), I_B 4095 (model 4095)
- `top_d27_23.810.log`: d27 vector 10: raw 2048 / 2048, I_A 1 (model 1), I_B 4095 (model 4095)
- `top_d27_23.810.log`: d27 vector 11: raw 600 / 3500, I_A 0 (model 0), I_B 4095 (model 4095)
- `top_d27_23.810.log`: d27 capture: 24 current pairs, RTL IA 415..3690 IB 342..3500, model IA 415..3690 IB 342..3500
- `top_d27_23.810.log`: d27 host calibration: raw 752 / 1722, IA_GAIN 0x00003c92, IA_OFS -1
- `top_d27_23.810.log`: d27 current step: before +5.664 %, after +0.000 % (I_A 822 -> 1740, ideal 822 -> 1740, I_B 1740)
- `top_d27_23.810.log`: d27 I2t below the limit: FAULT 0x00000000, I_A 2798, I_B 2848, I2T_A 2116, I2T_B 2500 (raw A 3048 alone would give 3844)
- `top_d27_23.810.log`: d27 I2t IA_GAIN 1.25: FAULT 0x00000a00, I_A 3298, I2T_A 6084
- `top_d27_23.810.log`: d27 I2t IB_GAIN 1.25 with IB_OFS -800: FAULT 0x00000e00, I_B 3048, I2T_B 3844
- `top_d27_33.333.log`: d27 reset words: I_A 1234 (raw 1234), I_B 2900 (raw 2900)
- `top_d27_33.333.log`: d27 vector 0: raw 822 / 1740, I_A 956 (model 956), I_B 888 (model 888)
- `top_d27_33.333.log`: d27 vector 1: raw 3000 / 1000, I_A 3113 (model 3113), I_B 0 (model 0)
- `top_d27_33.333.log`: d27 vector 2: raw 4095 / 0, I_A 4095 (model 4095), I_B 2048 (model 2048)
- `top_d27_33.333.log`: d27 vector 3: raw 0 / 4095, I_A 0 (model 0), I_B 4095 (model 4095)
- `top_d27_33.333.log`: d27 vector 4: raw 2049 / 2047, I_A 2049 (model 2049), I_B 2045 (model 2045)
- `top_d27_33.333.log`: d27 vector 5: raw 2051 / 2045, I_A 2050 (model 2050), I_B 2038 (model 2038)
- `top_d27_33.333.log`: d27 vector 6: raw 1500 / 2600, I_A 2048 (model 2048), I_B 4095 (model 4095)
- `top_d27_33.333.log`: d27 vector 7: raw 2500 / 1600, I_A 2499 (model 2499), I_B 707 (model 707)
- `top_d27_33.333.log`: d27 vector 8: raw 3700 / 400, I_A 3437 (model 3437), I_B 0 (model 0)
- `top_d27_33.333.log`: d27 vector 9: raw 1111 / 3333, I_A 659 (model 659), I_B 4095 (model 4095)
- `top_d27_33.333.log`: d27 vector 10: raw 2048 / 2048, I_A 1 (model 1), I_B 4095 (model 4095)
- `top_d27_33.333.log`: d27 vector 11: raw 600 / 3500, I_A 0 (model 0), I_B 4095 (model 4095)
- `top_d27_33.333.log`: d27 capture: 24 current pairs, RTL IA 415..3690 IB 342..3500, model IA 415..3690 IB 342..3500
- `top_d27_33.333.log`: d27 host calibration: raw 752 / 1722, IA_GAIN 0x00003c92, IA_OFS -1
- `top_d27_33.333.log`: d27 current step: before +5.664 %, after +0.000 % (I_A 822 -> 1740, ideal 822 -> 1740, I_B 1740)
- `top_d27_33.333.log`: d27 I2t below the limit: FAULT 0x00000000, I_A 2798, I_B 2848, I2T_A 2116, I2T_B 2500 (raw A 3048 alone would give 3844)
- `top_d27_33.333.log`: d27 I2t IA_GAIN 1.25: FAULT 0x00000a00, I_A 3298, I2T_A 6084
- `top_d27_33.333.log`: d27 I2t IB_GAIN 1.25 with IB_OFS -800: FAULT 0x00000e00, I_B 3048, I2T_B 3844
- `top_d27_47.619.log`: d27 reset words: I_A 1234 (raw 1234), I_B 2900 (raw 2900)
- `top_d27_47.619.log`: d27 vector 0: raw 822 / 1740, I_A 956 (model 956), I_B 888 (model 888)
- `top_d27_47.619.log`: d27 vector 1: raw 3000 / 1000, I_A 3113 (model 3113), I_B 0 (model 0)
- `top_d27_47.619.log`: d27 vector 2: raw 4095 / 0, I_A 4095 (model 4095), I_B 2048 (model 2048)
- `top_d27_47.619.log`: d27 vector 3: raw 0 / 4095, I_A 0 (model 0), I_B 4095 (model 4095)
- `top_d27_47.619.log`: d27 vector 4: raw 2049 / 2047, I_A 2049 (model 2049), I_B 2045 (model 2045)
- `top_d27_47.619.log`: d27 vector 5: raw 2051 / 2045, I_A 2050 (model 2050), I_B 2038 (model 2038)
- `top_d27_47.619.log`: d27 vector 6: raw 1500 / 2600, I_A 2048 (model 2048), I_B 4095 (model 4095)
- `top_d27_47.619.log`: d27 vector 7: raw 2500 / 1600, I_A 2499 (model 2499), I_B 707 (model 707)
- `top_d27_47.619.log`: d27 vector 8: raw 3700 / 400, I_A 3437 (model 3437), I_B 0 (model 0)
- `top_d27_47.619.log`: d27 vector 9: raw 1111 / 3333, I_A 659 (model 659), I_B 4095 (model 4095)
- `top_d27_47.619.log`: d27 vector 10: raw 2048 / 2048, I_A 1 (model 1), I_B 4095 (model 4095)
- `top_d27_47.619.log`: d27 vector 11: raw 600 / 3500, I_A 0 (model 0), I_B 4095 (model 4095)
- `top_d27_47.619.log`: d27 capture: 24 current pairs, RTL IA 415..3690 IB 342..3500, model IA 415..3690 IB 342..3500
- `top_d27_47.619.log`: d27 host calibration: raw 752 / 1722, IA_GAIN 0x00003c92, IA_OFS -1
- `top_d27_47.619.log`: d27 current step: before +5.664 %, after +0.000 % (I_A 822 -> 1740, ideal 822 -> 1740, I_B 1740)
- `top_d27_47.619.log`: d27 I2t below the limit: FAULT 0x00000000, I_A 2798, I_B 2848, I2T_A 2116, I2T_B 2500 (raw A 3048 alone would give 3844)
- `top_d27_47.619.log`: d27 I2t IA_GAIN 1.25: FAULT 0x00000a00, I_A 3298, I2T_A 6084
- `top_d27_47.619.log`: d27 I2t IB_GAIN 1.25 with IB_OFS -800: FAULT 0x00000e00, I_B 3048, I2T_B 3844
- `top_disc_33.333.log`: disc A: pre-charge hold 66.7 ns, track before the first sampling edge 666.7 ns
- `top_disc_33.333.log`: disc A: starts 7 (dropped 1), pairs completed 6, delivered 5
- `top_disc_33.333.log`: disc B: starts enc 79 cur 8, dropped enc 13 cur 2, in flight at arm enc 0 cur 0, delivered enc 66 cur 6
- `top_disc_33.333.log`: disc C: starts enc 30 cur 0, dropped enc 0 cur 0, in flight at arm enc 1, delivered enc 31
- `top_gate_33.333.log`: gate A on 16 off 586 (width 570), B on 516 off 786 (width 270), C on 1016 off 386 (width 870); current frame start 301 is_smp 301; az_win 1201..1241
- `top_gate_33.333.log`: gate encoder frames in one period 67: 65 gaps of 22 ticks, 1 other, longest 48 ticks
- `top_gate_33.333.log`: gate: GATE_C = 0 1 ns after EN low in the zero-delay RTL (combinational path)
- `top_gate_33.333.log`: gate with ADC_A_W13 = 8530: I_A 2948 I_B 2848
- `top_safe_33.333.log`: safe cmp[0]: FAULT 0x0001, FAULT_N low after 4 ticks
- `top_safe_33.333.log`: safe cmp[1]: FAULT 0x0002, FAULT_N low after 4 ticks
- `top_safe_33.333.log`: safe cmp[2]: FAULT 0x0004, FAULT_N low after 4 ticks
- `top_safe_33.333.log`: safe cmp[3]: FAULT 0x0008, FAULT_N low after 4 ticks
- `top_safe_33.333.log`: safe TEMP count 274 (2 MHz over 4096 ticks, expected 273.1)
- `top_safe_33.333.log`: safe watchdog fired 4091 ticks after the last SPI frame (period 4096 ticks)
- `top_safe_33.333.log`: safe FAULT before I2t 0x0000
- `top_safe_33.333.log`: safe I2t: trip after 30887 ticks = 103.0 PWM periods; integer model 103 updates; closed form 102.20 updates
- `top_spi_33.333.log`: OSC_COUNT = 480, expected 480.0 (16 us of 33.333 ns ticks)
- `top_spi_33.333.log`: spi/biss frame: busy 2 data 0x12345 nE nW 11 crc wire 0d calc~ 0d ack 1
- `top_ssi_23.810.log`: ssi gray=0 data 0x0000099a expected 0x0000099a monoflop 14.39 us
- `top_ssi_23.810.log`: ssi gray=1 data 0x00000d57 expected 0x00000d57 monoflop 14.40 us
- `top_ssi_23.810.log`: ssi clk 23.810 ns: OSC_COUNT 672 -> TIMEOUT_TICKS 840, monoflop 20.11 us (600 ticks untrimmed = 14.29 us)
- `top_ssi_33.333.log`: ssi gray=0 data 0x0000099a expected 0x0000099a monoflop 20.14 us
- `top_ssi_33.333.log`: ssi gray=1 data 0x00000d57 expected 0x00000d57 monoflop 20.14 us
- `top_ssi_33.333.log`: ssi clk 33.333 ns: OSC_COUNT 479 -> TIMEOUT_TICKS 599, monoflop 20.12 us (600 ticks untrimmed = 20.00 us)
- `top_ssi_47.619.log`: ssi gray=0 data 0x0000099a expected 0x0000099a monoflop 28.76 us
- `top_ssi_47.619.log`: ssi gray=1 data 0x00000d57 expected 0x00000d57 monoflop 28.78 us
- `top_ssi_47.619.log`: ssi clk 47.619 ns: OSC_COUNT 336 -> TIMEOUT_TICKS 420, monoflop 20.21 us (600 ticks untrimmed = 28.57 us)
- `top_v07_23.810.log`: v07 R3: FAULT after power-up with EN high = 0x1800
- `top_v07_23.810.log`: v07 R3: FAULT after power-up with EN low = 0x1900
- `top_v07_23.810.log`: v07 R4: zero-current power-up, flags 0000, FAULT 0x0000
- `top_v07_23.810.log`: v07 lock: clk 23.810 ns, OSC_COUNT 672 (OSC_COUNT[11:4] = 42), STATUS 0x05e0
- `top_v07_23.810.log`: v07 mask: flag from az_win start + 5 ticks, FAULT_N low after 159 ticks (window 40 + AZ_EXT 120 + 2 sync + 2 latch)
- `top_v07_23.810.log`: v07 cur_trk: 4 current frames, cur_trk high for >= 20 ticks up to each strobe (GUARD 20); 268 encoder frames, 268 with cur_trk low at the start; 4 encoder frames still converting when cur_trk rose
- `top_v07_33.333.log`: v07 R3: FAULT after power-up with EN high = 0x1800
- `top_v07_33.333.log`: v07 R3: FAULT after power-up with EN low = 0x1900
- `top_v07_33.333.log`: v07 R4: zero-current power-up, flags 0000, FAULT 0x0000
- `top_v07_33.333.log`: v07 lock: clk 33.333 ns, OSC_COUNT 480 (OSC_COUNT[11:4] = 30), STATUS 0x05e0
- `top_v07_33.333.log`: v07 mask: flag from az_win start + 5 ticks, FAULT_N low after 159 ticks (window 40 + AZ_EXT 120 + 2 sync + 2 latch)
- `top_v07_33.333.log`: v07 cur_trk: 4 current frames, cur_trk high for >= 20 ticks up to each strobe (GUARD 20); 268 encoder frames, 268 with cur_trk low at the start; 4 encoder frames still converting when cur_trk rose
- `top_v07_47.619.log`: v07 R3: FAULT after power-up with EN high = 0x1800
- `top_v07_47.619.log`: v07 R3: FAULT after power-up with EN low = 0x1900
- `top_v07_47.619.log`: v07 R4: zero-current power-up, flags 0000, FAULT 0x0000
- `top_v07_47.619.log`: v07 lock: clk 47.619 ns, OSC_COUNT 336 (OSC_COUNT[11:4] = 21), STATUS 0x45c0
- `top_v07_47.619.log`: v07 mask: flag from az_win start + 5 ticks, FAULT_N low after 159 ticks (window 40 + AZ_EXT 120 + 2 sync + 2 latch)
- `top_v07_47.619.log`: v07 cur_trk: 4 current frames, cur_trk high for >= 20 ticks up to each strobe (GUARD 20); 268 encoder frames, 268 with cur_trk low at the start; 4 encoder frames still converting when cur_trk rose

## Synthesis (Yosys, sg13g2_stdcell typ 1.2 V 25 C, Booth, PDK latch map, abc -D 23810)

- cells 16922, flops 2340, cell area 253057 um2 (34.9 kGE at 7.26 um2 per nand2_1), sequential 108412 um2 (43 %)
- ratio of cell area to the 0.18 mm2 cell-area target (0.28 mm2 placed at about 65 %): 1.41
- macro estimate at the G1 run7 ratio (129 600 um2 macro / 84 796 um2 synthesis): 0.387 mm2 = 2.15 x budget
- per block, children included (hierarchical synthesis, total 259372 um2; the flat run optimises across blocks): r1_regs 75311, r1_pos 65726, r1_gate 40475, r1_safe 23017, r1_biss 16516, r1_cmpcal 11606, r1_icor 7706, r1_tapidx 7365, r1_spi 6132, r1_ctrl_top (glue) 5242, r1_idrom 180, r1_sync2 98

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

## Revision 0.5

- r1_tapidx exhaustive (tb_tapidx.v, tapidx_ref.py): 16384 lane samples, 4096 OC and 4096 NEG (c, k) pairs, 0 mismatches, clipped samples 312 / 312: passed
- SDC ports (flow/check_sdc_ports.py): 30 ports, 128 bits, unconstrained 0, stale patterns 0: passed
- Yosys CHECK passes: 'Found and reported N problems' = ['0'], warning lines 0

## Revision 0.8: D22 channel correction (tb_d22 + d22_ref.py, 4096 pairs per case)

| Case | Points | Mismatches vs integer model | Position error max (deg el) | Registers |
| --- | --- | --- | --- | --- |
| raw | 4096 | 0 | 3.6472 | sin_ofs 0x0, cos_ofs 0x0, sin_gain 0x4000, cos_gain 0x4000, ph_sin 0x0, ph_icos 0x4000, h3 0x0 |
| cor | 4096 | 0 | 0.0299 | sin_ofs 0x39, cos_ofs 0xfc7, sin_gain 0x3f12, cos_gain 0x40f5, ph_sin 0x0, ph_icos 0x4000, h3 0x0 |
| sat | 4096 | 0 |  | sin_ofs 0x800, cos_ofs 0x7ff, sin_gain 0xffff, cos_gain 0xffff, ph_sin 0x7fff, ph_icos 0xffff, h3 0xff80 |
| full | 4096 | 0 |  | sin_ofs 0x8a6, cos_ofs 0x618, sin_gain 0x4e87, cos_gain 0x3327, ph_sin 0xc387, ph_icos 0x3f7f, h3 0x1426 |
| lo | 4096 | 0 |  | sin_ofs 0x7ff, cos_ofs 0x800, sin_gain 0x3000, cos_gain 0x0, ph_sin 0x0, ph_icos 0x4000, h3 0x0 |

Stimulus: {'amp_lsb': 1638.0, 'ofs_sin_lsb': 57.0, 'ofs_cos_lsb': -57.0, 'ofs_mv': 25.048828125, 'gain_sin': 1.03, 'gain_cos': 1.0, 'minmax': {'sin_min': 418, 'sin_max': 3792, 'cos_min': 353, 'cos_max': 3629}}. Criteria: bit-exact all cases; raw max error > 1 deg el; cor max error <= 0.05 deg el. Verdict: passed.

## Revision 0.9: D27 phase-current correction (tb_icor + icor_ref.py, bit-exact)

| Case | Vectors | Outputs | Mismatches | Saturated outputs | Identity violations at reset words |
| --- | --- | --- | --- | --- | --- |
| id | 4096 | 4096 | 0 | 4 | 0 |
| rnd | 8192 | 8192 | 0 | 7555 | 0 |
| sat | 315 | 315 | 0 | 220 | 0 |
| cal | 4096 | 4096 | 0 | 7 | 0 |
| restart | 256 | 256 | 0 | 245 | 0 |

Criteria: every vector bit-exact (both channels), identity at the reset words, all vectors present. Verdict: passed.

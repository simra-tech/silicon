### f(T), nominal corner (hbt_typ, mos_tt, res_typ, cap_typ), 3.3 V / 1.2 V (simulated transient, period averaged over 20 cycles)

| T [C] | f PTAT [MHz] | f REF [MHz] | f_PTAT / f_REF | two-point fit residual, f PTAT [C] | two-point fit residual, ratio [C] | I(3.3 V) [uA] | V_REF [V] | cap peak - V_th [mV] |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| -40 | 1.2411 | 1.5836 | 0.7837 | -1.59 | +0.91 | 44.6 | 1.0435 | 31.9 |
| -25 | 1.3199 | - | - | -1.11 | - | 47.4 | 1.0441 | 32.7 |
| -10 | 1.3984 | 1.5927 | 0.8780 | -0.71 | +0.22 | 50.3 | 1.0447 | 33.8 |
| 5 | 1.4765 | - | - | -0.37 | - | 53.1 | 1.0453 | 34.7 |
| 20 | 1.5544 | - | - | -0.07 | - | 55.9 | 1.0458 | 35.7 |
| 25 | 1.5803 | 1.5966 | 0.9898 | -0.00 | -0.00 | 56.9 | 1.0459 | 36.0 |
| 35 | 1.6319 | - | - | +0.14 | - | 58.8 | 1.0462 | 36.5 |
| 50 | 1.7090 | 1.5973 | 1.0699 | +0.28 | -0.06 | 61.6 | 1.0467 | 37.4 |
| 65 | 1.7855 | 1.5969 | 1.1181 | +0.31 | -0.08 | 64.4 | 1.0472 | 38.5 |
| 80 | 1.8617 | - | - | +0.25 | - | 67.2 | 1.0477 | 39.5 |
| 95 | 1.9372 | - | - | +0.09 | - | 70.0 | 1.0482 | 40.5 |
| 100 | 1.9622 | 1.5942 | 1.2309 | -0.00 | -0.00 | 71.0 | 1.0485 | 40.8 |
| 110 | 2.0121 | - | - | -0.21 | - | 72.8 | 1.0489 | 41.4 |
| 125 | 2.0864 | 1.5903 | 1.3120 | -0.61 | +0.24 | 75.6 | 1.0497 | 42.5 |
| 140 | 2.1604 | - | - | -1.10 | - | 78.4 | 1.0509 | 43.5 |
| 150 | 2.2097 | 1.5849 | 1.3943 | -1.41 | +0.83 | 80.4 | 1.0519 | 44.2 |
| 155 | 2.2346 | - | - | -1.53 | - | 81.3 | 1.0527 | 44.6 |
| 170 | 2.3111 | - | - | -1.50 | - | 84.4 | 1.0559 | 45.8 |
| 175 | 2.3379 | 1.5783 | 1.4812 | -1.24 | +2.88 | 85.6 | 1.0577 | 46.2 |

PTAT mode: slope of the 25/100 C line 5.093 kHz/C (3223 ppm/C of f(25 C)); f(25 C) = 1.5803 MHz.
Two-point (25 C, 100 C) fit residual over -40..150 C: f PTAT -1.59 .. +0.31 C; ratio f_PTAT/f_REF -0.08 .. +0.91 C. Over -40..175 C: f PTAT -1.59 .. +0.31 C; ratio -0.08 .. +2.88 C.

REF mode: f = 1.5783 .. 1.5973 MHz over -40..175 C (55 ppm/C box).

### Supply sensitivity, 27 C, nominal corner

| mode | f at 3.0 V | 3.3 V | 3.6 V [MHz] | sensitivity [ppm/V] | equivalent [C/V] |
| --- | --- | --- | --- | --- | --- |
| PTAT | 1.6012 | 1.5906 | 1.5718 | -30884 | -9.27 |
| REF | 1.6115 | 1.5967 | 1.5702 | -43103 | -12.93 |

1.2 V domain (output level shifter only): f PTAT = 1.5906 MHz at 1.08 V, 1.5906 at 1.20 V, 1.5906 at 1.32 V.

Equivalent [C/V] uses f proportional to absolute temperature (300 K at 27 C).

### Corner spread at 27 C (f PTAT), 8 extreme process corners (hbt bcs/wcs x mos ss/ff x res bcs/wcs) + nominal, cap_typ, plus cap corners

9 process corners: f PTAT = 1.3924 .. 1.8289 MHz (-12.5 % .. +15.0 % of nominal 1.5906 MHz); 9 of 9 runs oscillate.

| corner | f PTAT [MHz] | f REF [MHz] | ratio |
| --- | --- | --- | --- |
| hbt_typ_mos_tt_res_typ_cap_typ | 1.5906 | - | - |
| hbt_bcs_mos_ff_res_bcs_cap_typ | 1.8210 | 1.8690 | 0.9743 |
| hbt_wcs_mos_ss_res_wcs_cap_typ | 1.3987 | 1.3734 | 1.0184 |
| hbt_typ_mos_tt_res_typ_cap_bcs | 1.7590 | 1.7657 | 0.9962 |
| hbt_typ_mos_tt_res_typ_cap_wcs | 1.4517 | 1.4573 | 0.9961 |

Extreme corners over temperature (f PTAT):

| corner | f(-40 C) | f(27 C) | f(175 C) [MHz] | slope -40..175 vs nominal |
| --- | --- | --- | --- | --- |
| hbt_bcs_mos_ff_res_bcs | 1.4205 | 1.8210 | 2.6739 | 1.143 |
| hbt_wcs_mos_ss_res_wcs | 1.0922 | 1.3987 | 2.0579 | 0.880 |

### Cryogenic run, MODEL EXTRAPOLATED (not a prediction: the PDK HBT cards are not characterised below -40 C and the measured SG13G2 ideality factor departs strongly below ~100 K)

| T [C] | mode | f [MHz] | f / f(27 C) | (T / 300 K) for comparison |
| --- | --- | --- | --- | --- |
| -196 | PTAT | no oscillation within the run | - | 0.257 |
| -196 | REF | no oscillation within the run | - | 0.257 |
| -100 | PTAT | no oscillation within the run | - | 0.577 |


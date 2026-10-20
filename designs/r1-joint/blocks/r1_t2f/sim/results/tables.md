### f(T), 3.3 V, tt (simulated)

| T [C] | f PTAT [MHz] | f REF [MHz] | f_PTAT/f_REF | I(3.3 V) [uA] | I(1.2 V) [uA] | V_REF [V] | fit residual [C] |
| --- | --- | --- | --- | --- | --- | --- | --- |
| -40 | 1.2463 | 1.5827 | 0.7875 | 49.0 | 0.13 | 1.0373 | -0.33 |
| -25 | 1.3260 | not run | not run | 52.0 | 0.14 | 1.0373 | -0.12 |
| 0 | 1.4582 | not run | not run | 57.0 | 0.16 | 1.0369 | +0.13 |
| 27 | 1.6003 | 1.5978 | 1.0015 | 62.5 | 0.17 | 1.0360 | +0.26 |
| 50 | 1.7209 | not run | not run | 67.1 | 0.19 | 1.0350 | +0.29 |
| 75 | 1.8513 | not run | not run | 72.2 | 0.20 | 1.0335 | +0.20 |
| 100 | 1.9810 | not run | not run | 77.2 | 0.22 | 1.0318 | -0.03 |
| 125 | 2.1100 | 1.5793 | 1.3360 | 82.3 | 0.24 | 1.0299 | -0.40 |

Least-squares slope over -40..125 C: 5.237 kHz/C; local slope 5.157 .. 5.309 kHz/C; fit residual of one straight line -0.40 .. +0.29 C.

### Supply sensitivity (simulated)

| mode | T [C] | f at 3.0 V [MHz] | 3.3 V | 3.6 V | sensitivity [ppm/V] | [kHz/V] | [C/V] | I(VDDA) 3.0/3.3/3.6 V [uA] |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PTAT | 27 | 1.6043 | 1.6003 | 1.5962 | -8394 | -13.43 | -2.57 | 61.8 / 62.5 / 63.3 |
| PTAT | 125 | 2.1147 | 2.1100 | 2.1046 | -7983 | -16.84 | -3.22 | 81.6 / 82.3 / 83.1 |
| REF | 27 | 1.6018 | 1.5978 | 1.5939 | -8275 | -13.22 | -2.52 | 61.8 / 62.5 / 63.3 |

[C/V] divides the frequency change per volt by the simulated PTAT slope (LS, kHz/C above).

### Process corners at 3.0 and 3.6 V, PTAT (simulated; ss = hbt_wcs+mos_ss+res_wcs, ff = hbt_bcs+mos_ff+res_bcs)

| corner | VDDA [V] | f(-40 C) [MHz] | f(27 C) | f(125 C) | slope -40..125 C [kHz/C] | note |
| --- | --- | --- | --- | --- | --- | --- |
| ss | 3.0 | 1.0991 | 1.4098 | 1.8571 | 4.594 |  |
| ss | 3.6 | 1.0936 | 1.4027 | 1.8479 | 4.572 | -40 C point: tight options (retry) |
| tt | 3.0 | 1.2495 | 1.6043 | 2.1147 | 5.243 |  |
| tt | 3.6 | 1.2431 | 1.5962 | 2.1046 | 5.221 | -40 C point: tight options (retry) |
| ff | 3.0 | 1.4308 | 1.8379 | 2.4236 | 6.017 |  |
| ff | 3.6 | 1.4234 | 1.8289 | 2.4123 | 5.993 | -40 C point: tight options (retry) |

### TEMP_COUNT resolution (simulated f; slope 5.237 kHz/C, least squares)

Method A: count T2F rising edges in a gate of N cycles of the 30 MHz clock. count = N x f_T2F / f_clk.

| N [clk cycles] | gate at 30 MHz | count at -40 C | 27 C | 125 C | LSB [Hz] | LSB [C] (+/-1 count) | gate at 23 / 39 MHz clock |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2^14 = 16384 | 0.546 ms | 681 | 874 | 1152 | 1831 | 0.350 | 0.712 / 0.420 ms |
| 2^16 = 65536 | 2.185 ms | 2723 | 3496 | 4609 | 458 | 0.087 | 2.849 / 1.680 ms |
| 2^18 = 262144 | 8.738 ms | 10891 | 13984 | 18437 | 114 | 0.022 | 11.398 / 6.722 ms |

Method B: count 30 MHz clock cycles over K T2F periods (reciprocal count). count = K x f_clk / f_T2F.

| K [T2F periods] | gate at -40 / 27 / 125 C [ms] | count at -40 C | 27 C | 125 C | LSB [C] at -40 / 27 / 125 C (+/-1 count) |
| --- | --- | --- | --- | --- | --- |
| 2^10 = 1024 | 0.822 / 0.640 / 0.485 | 24649 | 19197 | 14559 | 0.010 / 0.016 / 0.028 |
| 2^12 = 4096 | 3.286 / 2.560 / 1.941 | 98594 | 76786 | 58237 | 0.002 / 0.004 / 0.007 |
| 2^14 = 16384 | 13.146 / 10.238 / 7.765 | 394377 | 307145 | 232949 | 0.001 / 0.001 / 0.002 |

Ratio readout: f_PTAT/f_REF changes by 0.00332 per C (mean over -40..125 C, simulated). One count in each of two counts N_P, N_R (method A, 2^16 window: N_P = 3496, N_R = 3491 at 27 C) gives a ratio step of about 0.00057, i.e. about 0.17 C (worst case, both counts +/-1).

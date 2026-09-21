### V_REF(T), -40 to 175 C in 5 C steps, 27 process corners x 3 supplies (simulated)

| HBT | RES | V_REF 27 C [V] (mos_tt, 3.3 V) | V_REF 27 C range, all MOS/VDD [V] | TC box -40..125 C [ppm/C] min..max | TC box -40..175 C [ppm/C] min..max | I_PTAT 27 C [uA] (tt, 3.3 V) |
| --- | --- | --- | --- | --- | --- | --- |
| hbt_typ | res_typ | 1.0379 | 1.0378 .. 1.0379 | 24.6 .. 25.4 | 22.8 .. 23.8 | 4.134 |
| hbt_typ | res_bcs | 1.0413 | 1.0413 .. 1.0414 | 15.4 .. 16.0 | 14.6 .. 15.5 | 4.727 |
| hbt_typ | res_wcs | 1.0346 | 1.0346 .. 1.0347 | 34.7 .. 35.6 | 31.5 .. 32.7 | 3.648 |
| hbt_bcs | res_typ | 1.0320 | 1.0320 .. 1.0321 | 40.1 .. 40.9 | 36.8 .. 38.0 | 4.137 |
| hbt_bcs | res_bcs | 1.0354 | 1.0354 .. 1.0355 | 28.5 .. 29.2 | 26.7 .. 27.8 | 4.731 |
| hbt_bcs | res_wcs | 1.0288 | 1.0288 .. 1.0289 | 51.3 .. 52.2 | 46.5 .. 47.7 | 3.651 |
| hbt_wcs | res_typ | 1.0452 | 1.0452 .. 1.0453 | 11.0 .. 11.7 | 11.8 .. 12.3 | 4.127 |
| hbt_wcs | res_bcs | 1.0487 | 1.0487 .. 1.0488 | 12.4 .. 12.6 | 15.2 .. 16.7 | 4.720 |
| hbt_wcs | res_wcs | 1.0420 | 1.0419 .. 1.0420 | 18.4 .. 19.2 | 16.8 .. 17.9 | 3.642 |

All 81 runs: V_REF(27 C) = 1.0288 .. 1.0488 V; TC box -40..125 C = 11.0 .. 52.2 ppm/C; -40..175 C = 11.8 .. 47.7 ppm/C.

### Nominal (hbt_typ, mos_tt, res_typ, 3.3 V)

| T [C] | -40 | 27 | 85 | 125 | 150 | 175 |
| --- | --- | --- | --- | --- | --- | --- |
| V_REF [V] | 1.0381 | 1.0379 | 1.0360 | 1.0340 | 1.0331 | 1.0353 |
| I_PTAT [uA] | 3.209 | 4.134 | - | 5.459 | - | 6.167 |
| total current [uA] | - | 22.0 | - | - | - | 32.8 |

delta-V_BE at 27 C = 55.07 mV (ideal kT/q ln 8 = 53.7 mV).

Supply: V_REF(27 C) = 1.03786 / 1.03786 / 1.03786 V at 3.0 / 3.3 / 3.6 V.

Ratio test mode (r4=1, 2:8 = 1:4): V_REF(27 C) = 0.9150 V, I_PTAT = 2.751 uA, delta-V_BE = 36.65 mV (ideal kT/q ln 4 = 35.8 mV).

### Cryogenic run, MODEL EXTRAPOLATED (PDK cards are not characterised below -40 C; numbers are not a prediction)

| HBT corner | V_REF -196 C | -150 C | -100 C | -40 C | I_PTAT -196 C [uA] | V_BE -196 C | delta-V_BE -196 C [mV] |
| --- | --- | --- | --- | --- | --- | --- | --- |
| hbt_bcs | 1.0259 | 1.0301 | 1.0327 | 1.0334 | 1.041 | 0.943 | 13.64 |
| hbt_typ | 1.0275 | 1.0327 | 1.0362 | 1.0381 | 1.042 | 0.944 | 13.66 |
| hbt_wcs | 1.0295 | 1.0360 | 1.0408 | 1.0441 | 1.043 | 0.946 | 13.67 |

### PSRR (AC, V_REF/V_DD), 27 process corners x 3 temperatures, 3.3 V

| | DC (1 Hz) | 1 kHz | 100 kHz | 1 MHz |
| --- | --- | --- | --- | --- |
| nominal 27 C [dB] | -103.0 | -82.3 | -42.3 | -25.0 |
| worst of 81 runs [dB] | -97.3 | -80.8 | -40.9 | -24.3 |

### Monte Carlo, 300 samples, hbt_typ_mismatch + mos_tt_mismatch + res_typ_mismatch, 27 C, 3.3 V

| quantity | mean | sigma | sigma / mean | min | max |
| --- | --- | --- | --- | --- | --- |
| V_REF [V] | 1.0394 | 19.1 mV | 1.84 % | 0.9900 | 1.1028 |
| I_PTAT [uA] | 4.153 | 0.214 | 5.16 % | 3.592 | 4.794 |
| delta-V_BE [mV] | 55.31 | 2.81 | 5.08 % | 47.85 | 64.34 |

### Start-up, 1 ms supply ramp to 3.0 V, 3 ms simulated, 27 corners x {-40, 27, 175} C

81 of 81 runs end with 0.9 V < V_REF < 1.2 V and |I_PTAT| > 1 uA (no stuck zero state). V_REF at the end: 1.0225 .. 1.0505 V. Time to V_REF = 0.93 V: 0.484 .. 0.614 ms after the ramp starts. Overshoot: max V_REF 1.0506 V.

### Start-up, 100 ms supply ramp to 3.0 V, 130 ms simulated, 27 corners at 27 C + typ at -40/175 C

29 of 29 runs end with 0.9 V < V_REF < 1.2 V and |I_PTAT| > 1 uA (no stuck zero state). V_REF at the end: 1.0288 .. 1.0488 V. Time to V_REF = 0.93 V: 48.325 .. 57.891 ms after the ramp starts. Overshoot: max V_REF 1.0488 V.


### f(T), nominal corner (hbt_typ, mos_tt, res_typ, cap_typ), 3.3 V / 1.2 V (simulated transient, period averaged over 20 cycles)

| T [C] | f PTAT [MHz] | f REF [MHz] | f_PTAT / f_REF | two-point fit residual, f PTAT [C] | two-point fit residual, ratio [C] | I(3.3 V) [uA] | V_REF [V] | cap peak - V_th [mV] |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| -40 | 1.2463 | 1.5827 | 0.7875 | -0.85 | +3.78 | 49.0 | 1.0373 | 33.7 |
| -25 | 1.3260 | - | - | -0.58 | - | 52.0 | 1.0373 | 34.5 |
| -10 | 1.4052 | 1.5984 | 0.8791 | -0.38 | +0.83 | 55.0 | 1.0371 | 35.7 |
| 5 | 1.4847 | - | - | -0.16 | - | 58.0 | 1.0367 | 36.6 |
| 20 | 1.5635 | - | - | -0.05 | - | 61.1 | 1.0363 | 37.7 |
| 25 | 1.5898 | 1.5980 | 0.9949 | -0.00 | +0.00 | 62.1 | 1.0361 | 38.0 |
| 35 | 1.6424 | - | - | +0.07 | - | 64.1 | 1.0357 | 38.6 |
| 50 | 1.7209 | 1.5955 | 1.0785 | +0.12 | -0.31 | 67.1 | 1.0350 | 39.7 |
| 65 | 1.7993 | 1.5933 | 1.1293 | +0.17 | -0.32 | 70.2 | 1.0341 | 40.7 |
| 80 | 1.8773 | - | - | +0.11 | - | 73.2 | 1.0332 | 41.8 |
| 95 | 1.9551 | - | - | +0.03 | - | 76.2 | 1.0322 | 42.9 |
| 100 | 1.9810 | 1.5861 | 1.2490 | -0.00 | +0.00 | 77.2 | 1.0318 | 43.2 |
| 110 | 2.0327 | - | - | -0.10 | - | 79.3 | 1.0311 | 43.8 |
| 125 | 2.1100 | 1.5793 | 1.3360 | -0.28 | +0.68 | 82.3 | 1.0299 | 45.0 |
| 140 | 2.1875 | - | - | -0.42 | - | 85.3 | 1.0289 | 45.9 |
| 150 | 2.2395 | 1.5714 | 1.4251 | -0.46 | +1.98 | 87.4 | 1.0284 | 46.7 |
| 155 | 2.2656 | - | - | -0.45 | - | 88.4 | 1.0283 | 47.2 |
| 170 | 2.3465 | - | - | +0.05 | - | 91.8 | 1.0290 | 48.3 |
| 175 | 2.3749 | 1.5628 | 1.5197 | +0.50 | +4.89 | 93.0 | 1.0299 | 48.6 |

PTAT mode: slope of the 25/100 C line 5.217 kHz/C (3281 ppm/C of f(25 C)); f(25 C) = 1.5898 MHz.
Two-point (25 C, 100 C) fit residual over -40..150 C: f PTAT -0.85 .. +0.17 C; ratio f_PTAT/f_REF -0.32 .. +3.78 C. Over -40..175 C: f PTAT -0.85 .. +0.50 C; ratio -0.32 .. +4.89 C.

REF mode: f = 1.5628 .. 1.5984 MHz over -40..175 C (104 ppm/C box).

### Supply sensitivity, 27 C, nominal corner

| mode | f at 3.0 V | 3.3 V | 3.6 V [MHz] | sensitivity [ppm/V] | equivalent [C/V] |
| --- | --- | --- | --- | --- | --- |
| PTAT | 1.6043 | 1.6003 | 1.5962 | -8394 | -2.52 |
| REF | 1.6018 | 1.5978 | 1.5939 | -8275 | -2.48 |

1.2 V domain (output level shifter only): f PTAT = 1.6003 MHz at 1.08 V, 1.6003 at 1.20 V, 1.6003 at 1.32 V.

Equivalent [C/V] uses f proportional to absolute temperature (300 K at 27 C).

### Corner spread at 27 C (f PTAT), 8 extreme process corners (hbt bcs/wcs x mos ss/ff x res bcs/wcs) + nominal, cap_typ, plus cap corners

9 process corners: f PTAT = 1.4048 .. 1.8352 MHz (-12.2 % .. +14.7 % of nominal 1.6003 MHz); 9 of 9 runs oscillate.

| corner | f PTAT [MHz] | f REF [MHz] | ratio |
| --- | --- | --- | --- |
| hbt_typ_mos_tt_res_typ_cap_typ | 1.6003 | - | - |
| hbt_bcs_mos_ff_res_bcs_cap_typ | 1.8335 | 1.8710 | 0.9800 |
| hbt_wcs_mos_ss_res_wcs_cap_typ | 1.4063 | 1.3739 | 1.0236 |
| hbt_typ_mos_tt_res_typ_cap_bcs | 1.7696 | 1.7668 | 1.0016 |
| hbt_typ_mos_tt_res_typ_cap_wcs | 1.4607 | 1.4585 | 1.0015 |

Extreme corners over temperature (f PTAT):

| corner | f(-40 C) | f(27 C) | f(175 C) [MHz] | slope -40..175 vs nominal |
| --- | --- | --- | --- | --- |
| hbt_bcs_mos_ff_res_bcs | 1.4271 | 1.8335 | 2.7204 | 1.146 |
| hbt_wcs_mos_ss_res_wcs | 1.0962 | 1.4063 | 2.0864 | 0.877 |

### Cryogenic run, MODEL EXTRAPOLATED (not a prediction: the PDK HBT cards are not characterised below -40 C and the measured SG13G2 ideality factor departs strongly below ~100 K)

| T [C] | mode | f [MHz] | f / f(27 C) | (T / 300 K) for comparison |
| --- | --- | --- | --- | --- |
| -196 | PTAT | no oscillation within the run | - | 0.257 |
| -196 | REF | no oscillation within the run | - | 0.257 |
| -100 | PTAT | no oscillation within the run | - | 0.577 |

### V_CE of the comparator HBTs (vce suite: whole run including the en=0 hold; min over the oscillation), model card vce_max = 1.6 V

| condition | mode | revision | max V_CE QA1 / QB1 / QA2 / QB2 [V] | min V_CE (oscillating) QA1 / QB1 [V] | f [MHz] | V_th [V] |
| --- | --- | --- | --- | --- | --- | --- |
| 3.6 V, 175 C | PTAT | 2 | 0.84 / 1.09 / 0.83 / 1.10 | 0.70 / 0.64 | 2.3686 | 1.0299 |
| 3.6 V, 175 C | PTAT | 1 (superseded) | 2.29 / 3.08 / 2.29 / 3.08 | 2.01 / 0.72 | 2.2670 | 1.0986 |
| 3.6 V, 175 C | REF | 2 | 0.72 / 1.01 / 0.72 / 1.01 | 0.55 / 0.24 | 1.5616 | 1.5934 |
| 3.6 V, 175 C | REF | 1 (superseded) | 1.78 / 2.64 / 1.78 / 2.64 | 1.51 / 0.23 | 1.5681 | 1.5932 |
| 3.0 V, -40 C | PTAT | 2 | 0.91 / 1.03 / 0.91 / 1.04 | 0.82 / 0.79 | 1.2493 | 1.0373 |
| 3.0 V, -40 C | PTAT | 1 (superseded) | 1.92 / 2.78 / 1.92 / 2.78 | 1.77 / 0.88 | 1.2470 | 1.0392 |
| 3.0 V, -40 C | REF | 2 | 1.00 / 1.06 / 1.00 / 1.06 | 0.92 / 0.85 | 1.5878 | 0.7999 |
| 3.0 V, -40 C | REF | 1 (superseded) | 2.21 / 3.01 / 2.21 / 3.01 | 2.11 / 1.13 | 1.5952 | 0.7953 |
| 3.3 V, 27 C | PTAT | 2 | 0.89 / 1.05 / 0.89 / 1.05 | 0.79 / 0.76 | 1.6001 | 1.0360 |
| 3.3 V, 27 C | PTAT | 1 (superseded) | 2.15 / 3.01 / 2.15 / 3.01 | 1.97 / 0.91 | 1.5904 | 1.0460 |
| 3.3 V, 27 C | REF | 2 | 0.89 / 1.07 / 0.89 / 1.06 | 0.79 / 0.75 | 1.5976 | 1.0376 |
| 3.3 V, 27 C | REF | 1 (superseded) | 2.16 / 3.06 / 2.16 / 3.05 | 1.98 / 0.91 | 1.5964 | 1.0417 |

Revision 2: max V_CE of any comparator HBT over the six runs = 1.10 V.
Revision 1 (same decks on rev1/xschem/g1_t2f.spice): 3.08 V.
Bandgap HBTs in the same runs (for reference; the bandgap has its own cascodes): max V_CE q1 0.79 V, q2 0.83 V, q3 0.78 V, qd1 0.78 V, qd2 0.78 V.


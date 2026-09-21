### Post-layout (kpex 2.5D CC, layout/g1_t2f.gds) vs schematic, nominal corner, 3.3 V / 1.2 V, bandgap in its schematic view

| quantity | unit | schematic | post-layout | delta |
| --- | --- | --- | --- | --- |
| f PTAT -40 C | MHz | 1.2411 | 1.1968 | -3.57 % |
| f PTAT 27 C | MHz | 1.5906 | 1.5323 | -3.66 % |
| f PTAT 125 C | MHz | 2.0864 | 2.0076 | -3.78 % |
| f PTAT 175 C | MHz | 2.3379 | 2.2485 | -3.82 % |
| f REF -40 C | MHz | 1.5836 | 1.5059 | -4.90 % |
| f REF 27 C | MHz | 1.5967 | 1.5242 | -4.54 % |
| f REF 125 C | MHz | 1.5903 | 1.5238 | -4.18 % |
| f REF 175 C | MHz | 1.5783 | 1.5149 | -4.02 % |
| f_PTAT / f_REF -40 C |  | 0.7837 | 0.7947 | +1.40 % |
| f_PTAT / f_REF 27 C |  | 0.9962 | 1.0053 | +0.92 % |
| f_PTAT / f_REF 125 C |  | 1.3120 | 1.3175 | +0.42 % |
| f_PTAT / f_REF 175 C |  | 1.4812 | 1.4843 | +0.20 % |
| PTAT slope of the 25/100 C line | kHz/C | 5.0931 | 4.8825 | -4.13 % |
| PTAT sensitivity (slope / f(25 C)) | ppm/C | 3223 | 3207 | -16 |
| two-point (25/100 C) residual at -40 C | C | -1.59 | -1.69 | -0.10 |
| two-point (25/100 C) residual at 27 C | C | 0.02 | 0.03 | +0.00 |
| two-point (25/100 C) residual at 125 C | C | -0.61 | -0.63 | -0.02 |
| two-point (25/100 C) residual at 175 C | C | -1.24 | -1.29 | -0.05 |
| cap peak - V_th, 27 C PTAT (I_PTAT t_d / C) | mV | 36.11 | 48.45 |  |
| current from 3.3 V, 27 C PTAT | uA | 57.25 | 58.56 |  |
| supply sensitivity PTAT, 3.0 .. 3.6 V, 27 C | ppm/V | -30884 | -32693 | -1809 |
|   equivalent (f proportional to T, 300 K) | C/V | -9.27 | -9.81 | -0.54 |
| supply sensitivity REF, 3.0 .. 3.6 V, 27 C | ppm/V | -43103 | -43931 | -828 |
|   equivalent (f proportional to T, 300 K) | C/V | -12.93 | -13.18 | -0.25 |


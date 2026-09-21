# G1_SENSE schematic vs post-layout (kpex 2.5D CC), simulated (schematic values from ../logs/sense_<tag>.log)

| run | quantity | schematic | post-layout | delta |
| --- | --- | --- | --- | --- |
| mos_ff_res_bcs_3.3V_27C_cm0 | gain (5-45 mV fit) | 19.9873 | 19.9859 | -0.0014 |
| mos_ff_res_bcs_3.3V_27C_cm0 | pedestal ISENSE(0) [V] | 0.99915 | 0.99906 | -0.00010 |
| mos_ff_res_bcs_3.3V_27C_cm0 | ISENSE(50 mV) [V] | 1.99851 | 1.99835 | -0.00016 |
| mos_ff_res_bcs_3.3V_27C_cm0 | vref_buf [V] | not run / not converged | 1.03994 |  |
| mos_ff_res_bcs_3.3V_27C_cm0 | -3 dB bandwidth [MHz] | 4.813 | 4.778 | -0.036 |
| mos_ff_res_bcs_3.3V_27C_cm0 | step 10-90 % [ns] | 68.4 | 68.1 | -0.3 |
| mos_ff_res_bcs_3.3V_27C_cm0 | step to 1 % [ns] (first crossing) | 116.2 | 107.8 | -8.4 |
| mos_ff_res_bcs_3.3V_27C_cm0 | step overshoot [mV] | 7.6 | 22.1 | 14.5 |
| mos_ff_res_bcs_3.3V_27C_cm0 | step: last time outside +-1 % band [ns] (post-layout deck only) | not measured | 198.2 |  |
| mos_ff_res_bcs_3.3V_27C_cm0 | PSRR 1 kHz [dB] | -56.2 | -56.2 | 0.1 |
| mos_ff_res_bcs_3.3V_27C_cm0 | PSRR 1 MHz [dB] | -8.4 | -7.7 | 0.7 |
| mos_ff_res_bcs_3.3V_27C_cm0 | CM gain 1 kHz [dB] | -75.1 | -74.3 | 0.7 |
| mos_ff_res_bcs_3.3V_27C_cm0 | CM gain 1 MHz [dB] | -37.0 | -50.5 | -13.5 |
| mos_ff_res_bcs_3.3V_27C_cm0 | supply current [uA] | not run / not converged | 984 |  |
| mos_ss_res_wcs_3.3V_175C_cm0 | gain (5-45 mV fit) | 19.9858 | 19.9854 | -0.0004 |
| mos_ss_res_wcs_3.3V_175C_cm0 | pedestal ISENSE(0) [V] | 0.99915 | 0.99912 | -0.00003 |
| mos_ss_res_wcs_3.3V_175C_cm0 | ISENSE(50 mV) [V] | 1.99844 | 1.99839 | -0.00005 |
| mos_ss_res_wcs_3.3V_175C_cm0 | vref_buf [V] | 1.03983 | 1.03995 | 0.00012 |
| mos_ss_res_wcs_3.3V_175C_cm0 | -3 dB bandwidth [MHz] | 3.581 | 3.713 | 0.131 |
| mos_ss_res_wcs_3.3V_175C_cm0 | step 10-90 % [ns] | 93.1 | 88.7 | -4.4 |
| mos_ss_res_wcs_3.3V_175C_cm0 | step to 1 % [ns] (first crossing) | 163.5 | 141.3 | -22.2 |
| mos_ss_res_wcs_3.3V_175C_cm0 | step overshoot [mV] | 3.8 | 17.3 | 13.5 |
| mos_ss_res_wcs_3.3V_175C_cm0 | step: last time outside +-1 % band [ns] (post-layout deck only) | not measured | 245.9 |  |
| mos_ss_res_wcs_3.3V_175C_cm0 | PSRR 1 kHz [dB] | -58.0 | -57.7 | 0.3 |
| mos_ss_res_wcs_3.3V_175C_cm0 | PSRR 1 MHz [dB] | -6.2 | -5.7 | 0.5 |
| mos_ss_res_wcs_3.3V_175C_cm0 | CM gain 1 kHz [dB] | -75.5 | -75.4 | 0.1 |
| mos_ss_res_wcs_3.3V_175C_cm0 | CM gain 1 MHz [dB] | -35.4 | -46.8 | -11.4 |
| mos_ss_res_wcs_3.3V_175C_cm0 | supply current [uA] | 1523 | 1536 | 13 |
| mos_tt_res_typ_3.3V_-40C_cm0 | gain (5-45 mV fit) | 19.9896 | 19.9877 | -0.0019 |
| mos_tt_res_typ_3.3V_-40C_cm0 | pedestal ISENSE(0) [V] | 0.99933 | 0.99919 | -0.00015 |
| mos_tt_res_typ_3.3V_-40C_cm0 | ISENSE(50 mV) [V] | 1.99881 | 1.99857 | -0.00024 |
| mos_tt_res_typ_3.3V_-40C_cm0 | vref_buf [V] | not run / not converged | 1.03995 |  |
| mos_tt_res_typ_3.3V_-40C_cm0 | -3 dB bandwidth [MHz] | 4.108 | 4.014 | -0.094 |
| mos_tt_res_typ_3.3V_-40C_cm0 | step 10-90 % [ns] | 80.0 | 80.8 | 0.8 |
| mos_tt_res_typ_3.3V_-40C_cm0 | step to 1 % [ns] (first crossing) | 139.6 | 130.7 | -8.9 |
| mos_tt_res_typ_3.3V_-40C_cm0 | step overshoot [mV] | 4.6 | 14.3 | 9.7 |
| mos_tt_res_typ_3.3V_-40C_cm0 | step: last time outside +-1 % band [ns] (post-layout deck only) | not measured | 214.2 |  |
| mos_tt_res_typ_3.3V_-40C_cm0 | PSRR 1 kHz [dB] | -60.2 | -60.2 | -0.1 |
| mos_tt_res_typ_3.3V_-40C_cm0 | PSRR 1 MHz [dB] | -7.3 | -6.5 | 0.8 |
| mos_tt_res_typ_3.3V_-40C_cm0 | CM gain 1 kHz [dB] | -76.5 | -75.2 | 1.2 |
| mos_tt_res_typ_3.3V_-40C_cm0 | CM gain 1 MHz [dB] | -36.4 | -48.9 | -12.5 |
| mos_tt_res_typ_3.3V_-40C_cm0 | supply current [uA] | not run / not converged | 728 |  |
| mos_tt_res_typ_3.3V_175C_cm0 | gain (5-45 mV fit) | 19.9843 | 19.9840 | -0.0003 |
| mos_tt_res_typ_3.3V_175C_cm0 | pedestal ISENSE(0) [V] | 0.99897 | 0.99893 | -0.00004 |
| mos_tt_res_typ_3.3V_175C_cm0 | ISENSE(50 mV) [V] | 1.99818 | 1.99813 | -0.00005 |
| mos_tt_res_typ_3.3V_175C_cm0 | vref_buf [V] | 1.03997 | 1.03994 | -0.00003 |
| mos_tt_res_typ_3.3V_175C_cm0 | -3 dB bandwidth [MHz] | 4.076 | 4.196 | 0.120 |
| mos_tt_res_typ_3.3V_175C_cm0 | step 10-90 % [ns] | 81.6 | 78.3 | -3.2 |
| mos_tt_res_typ_3.3V_175C_cm0 | step to 1 % [ns] (first crossing) | 140.9 | 124.0 | -16.9 |
| mos_tt_res_typ_3.3V_175C_cm0 | step overshoot [mV] | 5.5 | 20.8 | 15.3 |
| mos_tt_res_typ_3.3V_175C_cm0 | step: last time outside +-1 % band [ns] (post-layout deck only) | not measured | 225.9 |  |
| mos_tt_res_typ_3.3V_175C_cm0 | PSRR 1 kHz [dB] | -55.9 | -55.9 | 0.1 |
| mos_tt_res_typ_3.3V_175C_cm0 | PSRR 1 MHz [dB] | -7.1 | -6.6 | 0.5 |
| mos_tt_res_typ_3.3V_175C_cm0 | CM gain 1 kHz [dB] | -74.3 | -74.2 | 0.1 |
| mos_tt_res_typ_3.3V_175C_cm0 | CM gain 1 MHz [dB] | -36.0 | -48.4 | -12.4 |
| mos_tt_res_typ_3.3V_175C_cm0 | supply current [uA] | 1531 | 1543 | 12 |
| mos_tt_res_typ_3.3V_27C_cm0 | gain (5-45 mV fit) | 19.9881 | 19.9868 | -0.0013 |
| mos_tt_res_typ_3.3V_27C_cm0 | pedestal ISENSE(0) [V] | 0.99924 | 0.99915 | -0.00009 |
| mos_tt_res_typ_3.3V_27C_cm0 | ISENSE(50 mV) [V] | 1.99865 | 1.99849 | -0.00016 |
| mos_tt_res_typ_3.3V_27C_cm0 | vref_buf [V] | 1.03994 | 1.03995 | 0.00001 |
| mos_tt_res_typ_3.3V_27C_cm0 | -3 dB bandwidth [MHz] | 4.186 | 4.186 | -0.001 |
| mos_tt_res_typ_3.3V_27C_cm0 | step 10-90 % [ns] | 78.8 | 77.8 | -1.1 |
| mos_tt_res_typ_3.3V_27C_cm0 | step to 1 % [ns] (first crossing) | 136.2 | 124.0 | -12.2 |
| mos_tt_res_typ_3.3V_27C_cm0 | step overshoot [mV] | 5.4 | 18.2 | 12.8 |
| mos_tt_res_typ_3.3V_27C_cm0 | step: last time outside +-1 % band [ns] (post-layout deck only) | not measured (overshoot < 1 %: = first crossing) | 217.9 |  |
| mos_tt_res_typ_3.3V_27C_cm0 | PSRR 1 kHz [dB] | -57.8 | -57.8 | -0.0 |
| mos_tt_res_typ_3.3V_27C_cm0 | PSRR 1 MHz [dB] | -7.3 | -6.7 | 0.7 |
| mos_tt_res_typ_3.3V_27C_cm0 | CM gain 1 kHz [dB] | -76.0 | -75.2 | 0.8 |
| mos_tt_res_typ_3.3V_27C_cm0 | CM gain 1 MHz [dB] | -36.3 | -48.6 | -12.3 |
| mos_tt_res_typ_3.3V_27C_cm0 | supply current [uA] | 982 | 976 | -6 |


| Net | Driver | R to the far pin (ohm) | Route C incl. fragments (fF) | Net C with pins, slow (fF) | Worst load slew fast / typ / slow (ns) | Loads |
| --- | --- | --- | --- | --- | --- | --- |
| `EN` | port | 0 | 125.7 | 393.5 | 0.000 / 0.000 / 0.000 | sg13g2_IOPadIn |
| `FAULT_N` | `pad11_fault_n/pad (sg13g2_IOPadOut4mA)` | 0 | 125.7 | 131.7 | - / - / - |  |
| `GATE` | `pad10_gate/pad (sg13g2_IOPadOut30mA)` | 0 | 125.7 | 131.7 | - / - / - |  |
| `SCLK` | port | 0 | 125.7 | 393.5 | 0.000 / 0.000 / 0.000 | sg13g2_IOPadIn |
| `SDI` | port | 0 | 125.7 | 393.5 | 0.000 / 0.000 / 0.000 | sg13g2_IOPadIn |
| `SDO` | `pad16_sdo/pad (sg13g2_IOPadOut4mA)` | 0 | 125.7 | 131.7 | - / - / - |  |
| `TEMP_OUT` | `pad17_temp_out/pad (sg13g2_IOPadOut16mA)` | 0 | 125.7 | 131.7 | - / - / - |  |
| `en_i` | `pad12_en/p2c (sg13g2_IOPadIn)` | 389 | 125.2 | 141.0 | 0.166 / 0.221 / 0.316 | g1_gate, sg13g2_antennanp, sg13g2_buf_1 |
| `fault_n_o` | `i_core.u_gate/fault_core (g1_gate)` | 287 | 61.8 | 101.9 | 0.066 / 0.062 / 0.060 | sg13g2_IOPadOut4mA |
| `gate_o` | `i_core.u_gate/gate_core (g1_gate)` | 215 | 80.4 | 120.5 | 0.055 / 0.052 / 0.051 | sg13g2_IOPadOut30mA |
| `i_core_bgr_r4_12` | `i_core.u_digital/output7/X (sg13g2_buf_1)` | 81 | 21.7 | 36.5 | 0.100 / 0.155 / 0.238 | g1_ls_up |
| `i_core_bgr_r4_33` | `i_core.u_ls_r4/out (g1_ls_up)` | 247 | 69.4 | 79.6 | 0.015 / 0.015 / 0.015 | g1_bgr |
| `i_core_clk_div_out` | `i_core.u_digital/output8/X (sg13g2_buf_1)` | - | 0.0 | 3.9 | - / - / - |  |
| `i_core_clr_d` | `i_core.u_digital/output9/X (sg13g2_buf_1)` | 55 | 24.7 | 35.7 | 0.097 / 0.151 / 0.234 | g1_gate |
| `i_core_cmp_clk` | `i_core.u_digital/output10/X (sg13g2_buf_1)` | 280 | 122.5 | 161.7 | 0.429 / 0.662 / 1.014 | g1_trip |
| `i_core_cmp_hard` | `i_core.u_trip/cmp_hard (g1_trip)` | 380 | 180.7 | 191.9 | 0.084 / 0.084 / 0.084 | g1_gate, sg13g2_buf_1 |
| `i_core_cmp_soft` | `i_core.u_trip/cmp_soft (g1_trip)` | 492 | 269.7 | 277.2 | 0.187 / 0.187 / 0.187 | sg13g2_antennanp, sg13g2_buf_1 |
| `i_core_dac_hard_0_` | `i_core.u_digital/output11/X (sg13g2_buf_1)` | 210 | 144.6 | 155.5 | 0.411 / 0.636 / 0.977 | g1_trip |
| `i_core_dac_hard_1_` | `i_core.u_digital/output12/X (sg13g2_buf_1)` | 211 | 141.6 | 153.9 | 0.407 / 0.629 / 0.966 | g1_trip |
| `i_core_dac_hard_2_` | `i_core.u_digital/output13/X (sg13g2_buf_1)` | 247 | 136.3 | 144.8 | 0.383 / 0.593 / 0.909 | g1_trip |
| `i_core_dac_hard_3_` | `i_core.u_digital/output14/X (sg13g2_buf_1)` | 233 | 94.8 | 105.7 | 0.281 / 0.434 / 0.667 | g1_trip |
| `i_core_dac_hard_4_` | `i_core.u_digital/output15/X (sg13g2_buf_1)` | 221 | 108.0 | 117.2 | 0.313 / 0.483 / 0.743 | g1_trip |
| `i_core_dac_hard_5_` | `i_core.u_digital/output16/X (sg13g2_buf_1)` | 223 | 87.0 | 96.1 | 0.256 / 0.396 / 0.607 | g1_trip |
| `i_core_dac_hard_6_` | `i_core.u_digital/output17/X (sg13g2_buf_1)` | 222 | 56.3 | 67.1 | 0.180 / 0.279 / 0.430 | g1_trip |
| `i_core_dac_hard_7_` | `i_core.u_digital/output18/X (sg13g2_buf_1)` | 209 | 57.3 | 66.4 | 0.178 / 0.276 / 0.425 | g1_trip |
| `i_core_dac_soft_0_` | `i_core.u_digital/output19/X (sg13g2_buf_1)` | 108 | 68.7 | 79.6 | 0.212 / 0.328 / 0.505 | g1_trip |
| `i_core_dac_soft_1_` | `i_core.u_digital/output20/X (sg13g2_buf_1)` | 128 | 61.6 | 69.2 | 0.185 / 0.286 / 0.441 | g1_trip |
| `i_core_dac_soft_2_` | `i_core.u_digital/output21/X (sg13g2_buf_1)` | 129 | 48.7 | 58.6 | 0.158 / 0.244 / 0.376 | g1_trip |
| `i_core_dac_soft_3_` | `i_core.u_digital/output22/X (sg13g2_buf_1)` | 127 | 79.3 | 91.0 | 0.241 / 0.374 / 0.575 | g1_trip |
| `i_core_dac_soft_4_` | `i_core.u_digital/output23/X (sg13g2_buf_1)` | 102 | 44.4 | 54.2 | 0.146 / 0.226 / 0.349 | g1_trip |
| `i_core_dac_soft_5_` | `i_core.u_digital/output24/X (sg13g2_buf_1)` | 103 | 48.5 | 58.3 | 0.156 / 0.241 / 0.374 | g1_trip |
| `i_core_dac_soft_6_` | `i_core.u_digital/output25/X (sg13g2_buf_1)` | 60 | 22.0 | 33.3 | 0.092 / 0.142 / 0.219 | g1_trip |
| `i_core_dac_soft_7_` | `i_core.u_digital/output26/X (sg13g2_buf_1)` | 104 | 64.3 | 72.8 | 0.194 / 0.301 / 0.463 | g1_trip |
| `i_core_fast_en` | `i_core.u_digital/output27/X (sg13g2_buf_1)` | 59 | 12.0 | 20.8 | 0.059 / 0.092 / 0.143 | g1_gate |
| `i_core_fault_n_dig` | `i_core.u_digital/output28/X (sg13g2_buf_1)` | - | 0.0 | 0.9 | - / - / - |  |
| `i_core_gate_en` | `i_core.u_digital/output29/X (sg13g2_buf_1)` | - | 0.0 | 3.8 | - / - / - |  |
| `i_core_osc_clk` | `i_core.u_osc/osc_clk (g1_osc)` | 415 | 145.0 | 197.9 | 0.089 / 0.087 / 0.086 | sg13g2_buf_16 |
| `i_core_osc_en` | `i_core.u_digital/g1_digital/L_HI (sg13g2_tiehi)` | 244 | 96.9 | 106.4 | 0.027 / 0.027 / 0.027 | g1_osc |
| `i_core_osc_trim_0_` | `i_core.u_digital/output30/X (sg13g2_buf_1)` | 218 | 92.4 | 108.7 | 0.288 / 0.446 / 0.685 | g1_osc |
| `i_core_osc_trim_1_` | `i_core.u_digital/output31/X (sg13g2_buf_1)` | 243 | 116.4 | 135.3 | 0.358 / 0.554 / 0.851 | g1_osc |
| `i_core_osc_trim_2_` | `i_core.u_digital/output32/X (sg13g2_buf_1)` | 221 | 42.4 | 57.8 | 0.156 / 0.241 / 0.372 | g1_osc |
| `i_core_osc_trim_3_` | `i_core.u_digital/output33/X (sg13g2_buf_1)` | 246 | 132.1 | 148.9 | 0.393 / 0.609 / 0.935 | g1_osc |
| `i_core_sclk_i` | `pad14_sclk/p2c (sg13g2_IOPadIn)` | 410 | 161.4 | 212.8 | 0.223 / 0.304 / 0.439 | sg13g2_buf_16 |
| `i_core_sdi_i` | `pad15_sdi/p2c (sg13g2_IOPadIn)` | 704 | 168.9 | 179.8 | 0.223 / 0.289 / 0.403 | sg13g2_antennanp, sg13g2_buf_1 |
| `i_core_sdo_o` | `i_core.u_digital/output34/X (sg13g2_buf_1)` | 72 | 81.8 | 124.8 | 0.450 / 0.685 / 1.038 | sg13g2_IOPadOut4mA |
| `i_core_t2f_en_12` | `i_core.u_digital/output35/X (sg13g2_buf_1)` | 58 | 29.1 | 43.3 | 0.117 / 0.182 / 0.281 | g1_ls_up |
| `i_core_t2f_en_33` | `i_core.u_ls_en/out (g1_ls_up)` | 451 | 182.4 | 208.9 | 0.074 / 0.074 / 0.074 | g1_t2f |
| `i_core_t2f_mode_12` | `i_core.u_digital/output36/X (sg13g2_buf_1)` | 92 | 32.1 | 46.6 | 0.126 / 0.195 / 0.302 | g1_ls_up |
| `i_core_t2f_mode_33` | `i_core.u_ls_mode/out (g1_ls_up)` | 386 | 167.3 | 181.6 | 0.052 / 0.052 / 0.052 | g1_t2f |
| `i_core_temp_out_o` | `i_core.u_t2f/fout (g1_t2f)` | 126 | 27.1 | 67.2 | 0.023 / 0.021 / 0.020 | sg13g2_IOPadOut16mA |
| `i_core_trip` | `i_core.u_digital/output37/X (sg13g2_buf_1)` | - | 0.0 | 2.1 | - / - / - |  |
| `i_core_trip_cause_0_` | `i_core.u_digital/output38/X (sg13g2_buf_1)` | - | 0.0 | 4.1 | - / - / - |  |
| `i_core_trip_cause_1_` | `i_core.u_digital/output39/X (sg13g2_buf_1)` | - | 0.0 | 5.0 | - / - / - |  |
| `i_core_trip_d` | `i_core.u_digital/output40/X (sg13g2_buf_1)` | 56 | 26.2 | 38.0 | 0.103 / 0.160 / 0.248 | g1_gate |
| `i_core_trip_set_sel` | `i_core.u_digital/output41/X (sg13g2_buf_1)` | - | 0.0 | 6.5 | - / - / - |  |
| `i_core_tripped` | `i_core.u_gate/tripped (g1_gate)` | 351 | 143.2 | 153.2 | 0.027 / 0.027 / 0.027 | sg13g2_antennanp, sg13g2_buf_1 |
| `net` | `i_core.u_digital_1/L_HI (sg13g2_tiehi)` | 323 | 112.0 | 121.8 | 0.030 / 0.030 / 0.030 | sg13g2_buf_1 |

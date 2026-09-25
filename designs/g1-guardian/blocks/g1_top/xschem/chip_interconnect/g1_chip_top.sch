v {xschem version=3.4.8RC file_version=1.3}
G {}
K {}
V {}
S {}
E {}
B 4 120 -2250 620 -560 {dash=5 fill=false}
B 4 3960 -2050 4480 -1150 {dash=5 fill=false}
B 4 700 -2050 3900 -250 {dash=5 fill=false}
B 4 120 -3000 3120 -2848 {fill=false}
T {west IO: analog + 1.2 V inputs} 128 -2244 0 0 0.3 0.3 {layer=4}
T {east IO: outputs} 3968 -2044 0 0 0.3 0.3 {layer=4}
T {core: BGR -> SENSE -> TRIP -> digital -> GATE; OSC clock; T2F; level shifters; test structures} 708 -2044 0 0 0.3 0.3 {layer=4}
T {Every pin carries the net name of the CDL (i_core_* = core nets, _ncN = unconnected pad core pins).  VREF pad = i_core_vref (bandgap output, unbuffered); TRIP_SET pad core net i_core_trip_set has no core load on this chip.} 120 80 0 0 0.3 0.3 {}
T {Not drawn (same subcircuit): 4645 sg13g2_decap_8, 44 Filler400, 40 Filler4000, 38 sg13g2_fill_2, 28 Filler2000, 21 sg13g2_fill_1, 17 sg13g2_decap_4, 6 sg13g2_antennanp, 4 Corner.} 120 98 0 0 0.3 0.3 {}
T {g1_chip_top - chip-level interconnect: analog macros, digital macro, level shifters, pad ring} 132 -2990 0 0 0.55 0.55 {}
T {G1 guardian, chip of record g1_chip_top_1414_r2.gds 9049e87b (r2 2026-09-25; geometry XOR-identical to r1 629d303a); block map: g1_padring/reports/signoff-1414-20260924} 132 -2951 0 0 0.3 0.3 {}
T {On-chip variant: top level of the chip of record (r2); blocks are black boxes, see the block sheets} 132 -2927 0 0 0.3 0.3 {}
T {Netlist-equivalent to the 61 macro / tie / pad / bond-pad instances of g1_padring/netlist/g1_chip_top_1414_r2.cdl sha256 41d47877} 132 -2903 0 0 0.3 0.3 {}
T {Drawn 2026-09-25 by the block generator; device sizes (w, l, ng, m) are on each symbol. Proof: review/schematics-readability-20260925} 132 -2879 0 0 0.25 0.25 {}
C {chip_g1_bgr.sym} 1100 -1250 0 0 {name=Xi_core_u_bgr }
C {chip_g1_digital.sym} 2950 -1250 0 0 {name=Xi_core_u_digital }
C {chip_sg13g2_tiehi.sym} 2600 -500 0 0 {name=Xi_core_u_digital_1 }
C {chip_g1_dose_macro.sym} 1400 -450 0 0 {name=Xi_core_u_dose }
C {chip_g1_dut_macro.sym} 2800 -450 0 0 {name=Xi_core_u_dut }
C {chip_g1_gate.sym} 3700 -1850 0 0 {name=Xi_core_u_gate }
C {chip_g1_ls_up.sym} 3350 -500 0 0 {name=Xi_core_u_ls_en }
C {chip_g1_ls_up.sym} 3350 -350 0 0 {name=Xi_core_u_ls_mode }
C {chip_g1_ls_up.sym} 3350 -650 0 0 {name=Xi_core_u_ls_r4 }
C {chip_g1_osc.sym} 2150 -700 0 0 {name=Xi_core_u_osc }
C {chip_g1_sense.sym} 1500 -1800 0 0 {name=Xi_core_u_sense }
C {chip_g1_t2f.sym} 3700 -1100 0 0 {name=Xi_core_u_t2f }
C {chip_g1_trip.sym} 2150 -1450 0 0 {name=Xi_core_u_trip }
C {chip_G1_VSS_DERIVATIVE__sg13g2_IOPadVdd.sym} 1000 -2450 0 0 {name=Xpad01_vdd }
C {chip_G1_VSS_DERIVATIVE__sg13g2_IOPadVss.sym} 1400 -2450 0 0 {name=Xpad02_vss }
C {chip_G1_VSS_DERIVATIVE__sg13g2_IOPadIOVdd.sym} 1800 -2450 0 0 {name=Xpad03_iovdd }
C {chip_G1_VSS_DERIVATIVE__sg13g2_IOPadIOVss.sym} 2200 -2450 0 0 {name=Xpad04_iovss }
C {chip_G1_VSS_DERIVATIVE__sg13g2_IOPadVss.sym} 2600 -2450 0 0 {name=Xpad05_vss }
C {chip_G1_VSS_DERIVATIVE__sg13g2_IOPadIOVss.sym} 3000 -2450 0 0 {name=Xpad06_iovss }
C {chip_G1_VSS_DERIVATIVE__sg13g2_IOPadAnalog.sym} 400 -2100 0 0 {name=Xpad07_vdda }
C {chip_G1_VSS_DERIVATIVE__sg13g2_IOPadAnalog.sym} 400 -1900 0 0 {name=Xpad08_sense_p }
C {chip_G1_VSS_DERIVATIVE__sg13g2_IOPadAnalog.sym} 400 -1700 0 0 {name=Xpad09_sense_n }
C {chip_G1_VSS_DERIVATIVE__sg13g2_IOPadOut30mA.sym} 4200 -1900 0 1 {name=Xpad10_gate }
C {chip_G1_VSS_DERIVATIVE__sg13g2_IOPadOut4mA.sym} 4200 -1700 0 1 {name=Xpad11_fault_n }
C {chip_G1_VSS_DERIVATIVE__sg13g2_IOPadIn.sym} 400 -1100 0 0 {name=Xpad12_en }
C {chip_G1_VSS_DERIVATIVE__sg13g2_IOPadAnalog.sym} 400 -1300 0 0 {name=Xpad13_trip_set }
C {chip_G1_VSS_DERIVATIVE__sg13g2_IOPadIn.sym} 400 -900 0 0 {name=Xpad14_sclk }
C {chip_G1_VSS_DERIVATIVE__sg13g2_IOPadIn.sym} 400 -700 0 0 {name=Xpad15_sdi }
C {chip_G1_VSS_DERIVATIVE__sg13g2_IOPadOut4mA.sym} 4200 -1500 0 1 {name=Xpad16_sdo }
C {chip_G1_VSS_DERIVATIVE__sg13g2_IOPadOut16mA.sym} 4200 -1300 0 1 {name=Xpad17_temp_out }
C {chip_G1_VSS_DERIVATIVE__sg13g2_IOPadAnalog.sym} 400 -1500 0 0 {name=Xpad18_vref }
C {chip_G1_VSS_DERIVATIVE__sg13g2_IOPadAnalog.sym} 1000 -150 0 0 {name=Xpad19_g_shared }
C {chip_G1_VSS_DERIVATIVE__sg13g2_IOPadAnalog.sym} 1400 -150 0 0 {name=Xpad20_d_std }
C {chip_G1_VSS_DERIVATIVE__sg13g2_IOPadAnalog.sym} 1800 -150 0 0 {name=Xpad21_d_elt }
C {chip_G1_VSS_DERIVATIVE__sg13g2_IOPadAnalog.sym} 2400 -150 0 0 {name=Xpad22_hbt_e }
C {chip_G1_VSS_DERIVATIVE__sg13g2_IOPadAnalog.sym} 2800 -150 0 0 {name=Xpad23_hbt_b }
C {chip_G1_VSS_DERIVATIVE__sg13g2_IOPadAnalog.sym} 3200 -150 0 0 {name=Xpad24_hbt_c }
C {chip_bondpad_70x70_tm1.sym} 1190 -2560 0 0 {name=XIO_BOND_pad01_vdd }
C {chip_bondpad_70x70_tm1.sym} 1590 -2560 0 0 {name=XIO_BOND_pad02_vss }
C {chip_bondpad_70x70_tm1.sym} 1990 -2560 0 0 {name=XIO_BOND_pad03_iovdd }
C {chip_bondpad_70x70_tm1.sym} 2390 -2560 0 0 {name=XIO_BOND_pad04_iovss }
C {chip_bondpad_70x70_tm1.sym} 2790 -2560 0 0 {name=XIO_BOND_pad05_vss }
C {chip_bondpad_70x70_tm1.sym} 3190 -2560 0 0 {name=XIO_BOND_pad06_iovss }
C {chip_bondpad_70x70_tm1.sym} 190 -2100 0 0 {name=XIO_BOND_pad07_vdda }
C {chip_bondpad_70x70_tm1.sym} 190 -1900 0 0 {name=XIO_BOND_pad08_sense_p }
C {chip_bondpad_70x70_tm1.sym} 190 -1700 0 0 {name=XIO_BOND_pad09_sense_n }
C {chip_bondpad_70x70_tm1.sym} 4410 -1900 0 1 {name=XIO_BOND_pad10_gate }
C {chip_bondpad_70x70_tm1.sym} 4410 -1700 0 1 {name=XIO_BOND_pad11_fault_n }
C {chip_bondpad_70x70_tm1.sym} 190 -1100 0 0 {name=XIO_BOND_pad12_en }
C {chip_bondpad_70x70_tm1.sym} 190 -1300 0 0 {name=XIO_BOND_pad13_trip_set }
C {chip_bondpad_70x70_tm1.sym} 190 -900 0 0 {name=XIO_BOND_pad14_sclk }
C {chip_bondpad_70x70_tm1.sym} 190 -700 0 0 {name=XIO_BOND_pad15_sdi }
C {chip_bondpad_70x70_tm1.sym} 4410 -1500 0 1 {name=XIO_BOND_pad16_sdo }
C {chip_bondpad_70x70_tm1.sym} 4410 -1300 0 1 {name=XIO_BOND_pad17_temp_out }
C {chip_bondpad_70x70_tm1.sym} 190 -1500 0 0 {name=XIO_BOND_pad18_vref }
C {chip_bondpad_70x70_tm1.sym} 1190 -40 0 0 {name=XIO_BOND_pad19_g_shared }
C {chip_bondpad_70x70_tm1.sym} 1590 -40 0 0 {name=XIO_BOND_pad20_d_std }
C {chip_bondpad_70x70_tm1.sym} 1990 -40 0 0 {name=XIO_BOND_pad21_d_elt }
C {chip_bondpad_70x70_tm1.sym} 2590 -40 0 0 {name=XIO_BOND_pad22_hbt_e }
C {chip_bondpad_70x70_tm1.sym} 2990 -40 0 0 {name=XIO_BOND_pad23_hbt_b }
C {chip_bondpad_70x70_tm1.sym} 3390 -40 0 0 {name=XIO_BOND_pad24_hbt_c }
C {devices/iopin.sym} 2110 -40 0 0 {name=p0 lab=D_ELT}
C {devices/iopin.sym} 1590 -40 0 1 {name=p1 lab=D_STD}
C {devices/iopin.sym} 190 -1100 0 1 {name=p2 lab=EN}
C {devices/iopin.sym} 4410 -1700 0 0 {name=p3 lab=FAULT_N}
C {devices/iopin.sym} 4410 -1900 0 0 {name=p4 lab=GATE}
C {devices/iopin.sym} 1190 -40 0 1 {name=p5 lab=G_SHARED}
C {devices/iopin.sym} 3110 -40 0 0 {name=p6 lab=HBT_B}
C {devices/iopin.sym} 3510 -40 0 0 {name=p7 lab=HBT_C}
C {devices/iopin.sym} 2710 -40 0 0 {name=p8 lab=HBT_E}
C {devices/iopin.sym} 190 -900 0 1 {name=p9 lab=SCLK}
C {devices/iopin.sym} 190 -700 0 1 {name=p10 lab=SDI}
C {devices/iopin.sym} 4410 -1500 0 0 {name=p11 lab=SDO}
C {devices/iopin.sym} 190 -1700 0 1 {name=p12 lab=SENSE_N}
C {devices/iopin.sym} 190 -1900 0 1 {name=p13 lab=SENSE_P}
C {devices/iopin.sym} 4410 -1300 0 0 {name=p14 lab=TEMP_OUT}
C {devices/iopin.sym} 190 -1300 0 1 {name=p15 lab=TRIP_SET}
C {devices/iopin.sym} 190 -2100 0 1 {name=p16 lab=VDDA}
C {devices/iopin.sym} 190 -1500 0 1 {name=p17 lab=VREF}
C {devices/iopin.sym} 1190 -2560 0 1 {name=p18 lab=VDD}
C {devices/iopin.sym} 2910 -2560 0 0 {name=p19 lab=VSS}
C {devices/iopin.sym} 2110 -2560 0 0 {name=p20 lab=IOVDD}
C {devices/iopin.sym} 3310 -2560 0 0 {name=p21 lab=IOVSS}
C {devices/lab_pin.sym} 1100 -1340 0 0 {name=l1 lab=VDDA}
C {devices/lab_pin.sym} 1100 -1160 0 0 {name=l2 lab=VSS}
C {devices/lab_pin.sym} 1020 -1250 0 0 {name=l3 lab=i_core_bgr_r4_33}
C {devices/lab_pin.sym} 1180 -1300 0 1 {name=l4 lab=i_core_vref}
C {devices/lab_pin.sym} 1180 -1280 0 1 {name=l5 lab=i_core_iptat}
C {devices/lab_pin.sym} 1180 -1260 0 1 {name=l6 lab=i_core_pbias}
C {devices/lab_pin.sym} 1180 -1240 0 1 {name=l7 lab=i_core_pcasc}
C {devices/lab_pin.sym} 1180 -1220 0 1 {name=l8 lab=i_core_unused_vbe}
C {devices/lab_pin.sym} 1180 -1200 0 1 {name=l9 lab=i_core_dvbe}
C {devices/lab_pin.sym} 3090 -1600 0 1 {name=l10 lab=i_core_bgr_r4_12}
C {devices/lab_pin.sym} 3090 -1580 0 1 {name=l11 lab=i_core_clk_div_out}
C {devices/lab_pin.sym} 3090 -1560 0 1 {name=l12 lab=i_core_clr_d}
C {devices/lab_pin.sym} 3090 -1540 0 1 {name=l13 lab=i_core_cmp_clk}
C {devices/lab_pin.sym} 2810 -1320 0 0 {name=l14 lab=i_core_cmp_hard}
C {devices/lab_pin.sym} 2810 -1300 0 0 {name=l15 lab=i_core_cmp_soft}
C {devices/lab_pin.sym} 2810 -1280 0 0 {name=l16 lab=en_i}
C {devices/lab_pin.sym} 3090 -1520 0 1 {name=l17 lab=i_core_fast_en}
C {devices/lab_pin.sym} 3090 -1500 0 1 {name=l18 lab=i_core_fault_n_dig}
C {devices/lab_pin.sym} 3090 -1480 0 1 {name=l19 lab=i_core_gate_en}
C {devices/lab_pin.sym} 2810 -1260 0 0 {name=l20 lab=i_core_osc_clk}
C {devices/lab_pin.sym} 3090 -1460 0 1 {name=l21 lab=i_core_osc_en}
C {devices/lab_pin.sym} 2810 -1240 0 0 {name=l22 lab=net}
C {devices/lab_pin.sym} 2810 -1220 0 0 {name=l23 lab=i_core_sclk_i}
C {devices/lab_pin.sym} 2810 -1200 0 0 {name=l24 lab=i_core_sdi_i}
C {devices/lab_pin.sym} 3090 -1440 0 1 {name=l25 lab=i_core_sdo_o}
C {devices/lab_pin.sym} 3090 -1420 0 1 {name=l26 lab=i_core_t2f_en_12}
C {devices/lab_pin.sym} 3090 -1400 0 1 {name=l27 lab=i_core_t2f_mode_12}
C {devices/lab_pin.sym} 3090 -1380 0 1 {name=l28 lab=i_core_trip}
C {devices/lab_pin.sym} 3090 -1360 0 1 {name=l29 lab=i_core_trip_d}
C {devices/lab_pin.sym} 3090 -1340 0 1 {name=l30 lab=i_core_trip_set_sel}
C {devices/lab_pin.sym} 2810 -1180 0 0 {name=l31 lab=i_core_tripped}
C {devices/lab_pin.sym} 2950 -1640 0 0 {name=l32 lab=VDD}
C {devices/lab_pin.sym} 2950 -860 0 0 {name=l33 lab=VSS}
C {devices/lab_pin.sym} 3090 -1320 0 1 {name=l34 lab=i_core_dac_hard_7_}
C {devices/lab_pin.sym} 3090 -1300 0 1 {name=l35 lab=i_core_dac_hard_6_}
C {devices/lab_pin.sym} 3090 -1280 0 1 {name=l36 lab=i_core_dac_hard_5_}
C {devices/lab_pin.sym} 3090 -1260 0 1 {name=l37 lab=i_core_dac_hard_4_}
C {devices/lab_pin.sym} 3090 -1240 0 1 {name=l38 lab=i_core_dac_hard_3_}
C {devices/lab_pin.sym} 3090 -1220 0 1 {name=l39 lab=i_core_dac_hard_2_}
C {devices/lab_pin.sym} 3090 -1200 0 1 {name=l40 lab=i_core_dac_hard_1_}
C {devices/lab_pin.sym} 3090 -1180 0 1 {name=l41 lab=i_core_dac_hard_0_}
C {devices/lab_pin.sym} 3090 -1160 0 1 {name=l42 lab=i_core_dac_soft_7_}
C {devices/lab_pin.sym} 3090 -1140 0 1 {name=l43 lab=i_core_dac_soft_6_}
C {devices/lab_pin.sym} 3090 -1120 0 1 {name=l44 lab=i_core_dac_soft_5_}
C {devices/lab_pin.sym} 3090 -1100 0 1 {name=l45 lab=i_core_dac_soft_4_}
C {devices/lab_pin.sym} 3090 -1080 0 1 {name=l46 lab=i_core_dac_soft_3_}
C {devices/lab_pin.sym} 3090 -1060 0 1 {name=l47 lab=i_core_dac_soft_2_}
C {devices/lab_pin.sym} 3090 -1040 0 1 {name=l48 lab=i_core_dac_soft_1_}
C {devices/lab_pin.sym} 3090 -1020 0 1 {name=l49 lab=i_core_dac_soft_0_}
C {devices/lab_pin.sym} 3090 -1000 0 1 {name=l50 lab=i_core_osc_trim_3_}
C {devices/lab_pin.sym} 3090 -980 0 1 {name=l51 lab=i_core_osc_trim_2_}
C {devices/lab_pin.sym} 3090 -960 0 1 {name=l52 lab=i_core_osc_trim_1_}
C {devices/lab_pin.sym} 3090 -940 0 1 {name=l53 lab=i_core_osc_trim_0_}
C {devices/lab_pin.sym} 3090 -920 0 1 {name=l54 lab=i_core_trip_cause_1_}
C {devices/lab_pin.sym} 3090 -900 0 1 {name=l55 lab=i_core_trip_cause_0_}
C {devices/lab_pin.sym} 2600 -550 0 0 {name=l56 lab=VDD}
C {devices/lab_pin.sym} 2600 -450 0 0 {name=l57 lab=VSS}
C {devices/lab_pin.sym} 1480 -470 0 1 {name=l58 lab=D_ELT}
C {devices/lab_pin.sym} 1480 -450 0 1 {name=l59 lab=D_STD}
C {devices/lab_pin.sym} 1480 -430 0 1 {name=l60 lab=G_SHARED}
C {devices/lab_pin.sym} 1400 -390 0 0 {name=l61 lab=VSS}
C {devices/lab_pin.sym} 2870 -470 0 1 {name=l62 lab=HBT_C}
C {devices/lab_pin.sym} 2870 -450 0 1 {name=l63 lab=HBT_B}
C {devices/lab_pin.sym} 2870 -430 0 1 {name=l64 lab=HBT_E}
C {devices/lab_pin.sym} 2800 -390 0 0 {name=l65 lab=VSS}
C {devices/lab_pin.sym} 3570 -1890 0 0 {name=l66 lab=i_core_trip_d}
C {devices/lab_pin.sym} 3570 -1870 0 0 {name=l67 lab=i_core_clr_d}
C {devices/lab_pin.sym} 3570 -1850 0 0 {name=l68 lab=i_core_fast_en}
C {devices/lab_pin.sym} 3570 -1830 0 0 {name=l69 lab=i_core_cmp_hard}
C {devices/lab_pin.sym} 3570 -1810 0 0 {name=l70 lab=en_i}
C {devices/lab_pin.sym} 3830 -1870 0 1 {name=l71 lab=gate_o}
C {devices/lab_pin.sym} 3830 -1850 0 1 {name=l72 lab=fault_n_o}
C {devices/lab_pin.sym} 3830 -1830 0 1 {name=l73 lab=i_core_tripped}
C {devices/lab_pin.sym} 3680 -1930 0 0 {name=l74 lab=VDD}
C {devices/lab_pin.sym} 3720 -1930 0 1 {name=l75 lab=VDDA}
C {devices/lab_pin.sym} 3700 -1770 0 0 {name=l76 lab=VSS}
C {devices/lab_pin.sym} 3280 -500 0 0 {name=l77 lab=i_core_t2f_en_12}
C {devices/lab_pin.sym} 3420 -500 0 1 {name=l78 lab=i_core_t2f_en_33}
C {devices/lab_pin.sym} 3330 -550 0 0 {name=l79 lab=VDD}
C {devices/lab_pin.sym} 3370 -550 0 1 {name=l80 lab=VDDA}
C {devices/lab_pin.sym} 3350 -450 0 0 {name=l81 lab=VSS}
C {devices/lab_pin.sym} 3280 -350 0 0 {name=l82 lab=i_core_t2f_mode_12}
C {devices/lab_pin.sym} 3420 -350 0 1 {name=l83 lab=i_core_t2f_mode_33}
C {devices/lab_pin.sym} 3330 -400 0 0 {name=l84 lab=VDD}
C {devices/lab_pin.sym} 3370 -400 0 1 {name=l85 lab=VDDA}
C {devices/lab_pin.sym} 3350 -300 0 0 {name=l86 lab=VSS}
C {devices/lab_pin.sym} 3280 -650 0 0 {name=l87 lab=i_core_bgr_r4_12}
C {devices/lab_pin.sym} 3420 -650 0 1 {name=l88 lab=i_core_bgr_r4_33}
C {devices/lab_pin.sym} 3330 -700 0 0 {name=l89 lab=VDD}
C {devices/lab_pin.sym} 3370 -700 0 1 {name=l90 lab=VDDA}
C {devices/lab_pin.sym} 3350 -600 0 0 {name=l91 lab=VSS}
C {devices/lab_pin.sym} 2050 -740 0 0 {name=l92 lab=i_core_osc_en}
C {devices/lab_pin.sym} 2050 -720 0 0 {name=l93 lab=i_core_osc_trim_0_}
C {devices/lab_pin.sym} 2050 -700 0 0 {name=l94 lab=i_core_osc_trim_1_}
C {devices/lab_pin.sym} 2050 -680 0 0 {name=l95 lab=i_core_osc_trim_2_}
C {devices/lab_pin.sym} 2050 -660 0 0 {name=l96 lab=i_core_osc_trim_3_}
C {devices/lab_pin.sym} 2250 -700 0 1 {name=l97 lab=i_core_osc_clk}
C {devices/lab_pin.sym} 2150 -780 0 0 {name=l98 lab=VDD}
C {devices/lab_pin.sym} 2150 -620 0 0 {name=l99 lab=VSS}
C {devices/lab_pin.sym} 1390 -1830 0 0 {name=l100 lab=SENSE_P}
C {devices/lab_pin.sym} 1390 -1810 0 0 {name=l101 lab=SENSE_N}
C {devices/lab_pin.sym} 1390 -1790 0 0 {name=l102 lab=i_core_vref}
C {devices/lab_pin.sym} 1390 -1770 0 0 {name=l103 lab=i_core_iptat}
C {devices/lab_pin.sym} 1610 -1820 0 1 {name=l104 lab=i_core_isense}
C {devices/lab_pin.sym} 1610 -1800 0 1 {name=l105 lab=i_core_unused_vped}
C {devices/lab_pin.sym} 1610 -1780 0 1 {name=l106 lab=i_core_vref_buf}
C {devices/lab_pin.sym} 1500 -1870 0 0 {name=l107 lab=VDDA}
C {devices/lab_pin.sym} 1500 -1730 0 0 {name=l108 lab=VSS}
C {devices/lab_pin.sym} 3680 -1180 0 0 {name=l109 lab=VDDA}
C {devices/lab_pin.sym} 3720 -1180 0 1 {name=l110 lab=VDD}
C {devices/lab_pin.sym} 3700 -1020 0 0 {name=l111 lab=VSS}
C {devices/lab_pin.sym} 3610 -1140 0 0 {name=l112 lab=i_core_pbias}
C {devices/lab_pin.sym} 3610 -1120 0 0 {name=l113 lab=i_core_pcasc}
C {devices/lab_pin.sym} 3610 -1100 0 0 {name=l114 lab=i_core_vref}
C {devices/lab_pin.sym} 3610 -1080 0 0 {name=l115 lab=i_core_t2f_en_33}
C {devices/lab_pin.sym} 3610 -1060 0 0 {name=l116 lab=i_core_t2f_mode_33}
C {devices/lab_pin.sym} 3790 -1100 0 1 {name=l117 lab=i_core_temp_out_o}
C {devices/lab_pin.sym} 2020 -1630 0 0 {name=l118 lab=i_core_isense}
C {devices/lab_pin.sym} 2020 -1610 0 0 {name=l119 lab=i_core_vref_buf}
C {devices/lab_pin.sym} 2020 -1590 0 0 {name=l120 lab=i_core_cmp_clk}
C {devices/lab_pin.sym} 2020 -1570 0 0 {name=l121 lab=i_core_dac_soft_0_}
C {devices/lab_pin.sym} 2020 -1550 0 0 {name=l122 lab=i_core_dac_soft_1_}
C {devices/lab_pin.sym} 2020 -1530 0 0 {name=l123 lab=i_core_dac_soft_2_}
C {devices/lab_pin.sym} 2020 -1510 0 0 {name=l124 lab=i_core_dac_soft_3_}
C {devices/lab_pin.sym} 2020 -1490 0 0 {name=l125 lab=i_core_dac_soft_4_}
C {devices/lab_pin.sym} 2020 -1470 0 0 {name=l126 lab=i_core_dac_soft_5_}
C {devices/lab_pin.sym} 2020 -1450 0 0 {name=l127 lab=i_core_dac_soft_6_}
C {devices/lab_pin.sym} 2020 -1430 0 0 {name=l128 lab=i_core_dac_soft_7_}
C {devices/lab_pin.sym} 2020 -1410 0 0 {name=l129 lab=i_core_dac_hard_0_}
C {devices/lab_pin.sym} 2020 -1390 0 0 {name=l130 lab=i_core_dac_hard_1_}
C {devices/lab_pin.sym} 2020 -1370 0 0 {name=l131 lab=i_core_dac_hard_2_}
C {devices/lab_pin.sym} 2020 -1350 0 0 {name=l132 lab=i_core_dac_hard_3_}
C {devices/lab_pin.sym} 2020 -1330 0 0 {name=l133 lab=i_core_dac_hard_4_}
C {devices/lab_pin.sym} 2020 -1310 0 0 {name=l134 lab=i_core_dac_hard_5_}
C {devices/lab_pin.sym} 2020 -1290 0 0 {name=l135 lab=i_core_dac_hard_6_}
C {devices/lab_pin.sym} 2020 -1270 0 0 {name=l136 lab=i_core_dac_hard_7_}
C {devices/lab_pin.sym} 2280 -1460 0 1 {name=l137 lab=i_core_cmp_soft}
C {devices/lab_pin.sym} 2280 -1440 0 1 {name=l138 lab=i_core_cmp_hard}
C {devices/lab_pin.sym} 2130 -1670 0 0 {name=l139 lab=VDD}
C {devices/lab_pin.sym} 2170 -1670 0 1 {name=l140 lab=VDDA}
C {devices/lab_pin.sym} 2150 -1230 0 0 {name=l141 lab=VSS}
C {devices/lab_pin.sym} 980 -2500 0 0 {name=l142 lab=VDD}
C {devices/lab_pin.sym} 960 -2400 0 0 {name=l143 lab=VSS}
C {devices/lab_pin.sym} 1020 -2500 0 1 {name=l144 lab=IOVDD}
C {devices/lab_pin.sym} 1000 -2400 0 0 {name=l145 lab=IOVSS}
C {devices/lab_pin.sym} 1040 -2400 0 1 {name=l146 lab=VSS}
C {devices/lab_pin.sym} 1380 -2500 0 0 {name=l147 lab=VDD}
C {devices/lab_pin.sym} 1360 -2400 0 0 {name=l148 lab=VSS}
C {devices/lab_pin.sym} 1420 -2500 0 1 {name=l149 lab=IOVDD}
C {devices/lab_pin.sym} 1400 -2400 0 0 {name=l150 lab=IOVSS}
C {devices/lab_pin.sym} 1440 -2400 0 1 {name=l151 lab=VSS}
C {devices/lab_pin.sym} 1780 -2500 0 0 {name=l152 lab=VDD}
C {devices/lab_pin.sym} 1760 -2400 0 0 {name=l153 lab=VSS}
C {devices/lab_pin.sym} 1820 -2500 0 1 {name=l154 lab=IOVDD}
C {devices/lab_pin.sym} 1800 -2400 0 0 {name=l155 lab=IOVSS}
C {devices/lab_pin.sym} 1840 -2400 0 1 {name=l156 lab=VSS}
C {devices/lab_pin.sym} 2180 -2500 0 0 {name=l157 lab=VDD}
C {devices/lab_pin.sym} 2160 -2400 0 0 {name=l158 lab=VSS}
C {devices/lab_pin.sym} 2220 -2500 0 1 {name=l159 lab=IOVDD}
C {devices/lab_pin.sym} 2200 -2400 0 0 {name=l160 lab=IOVSS}
C {devices/lab_pin.sym} 2240 -2400 0 1 {name=l161 lab=VSS}
C {devices/lab_pin.sym} 2580 -2500 0 0 {name=l162 lab=VDD}
C {devices/lab_pin.sym} 2560 -2400 0 0 {name=l163 lab=VSS}
C {devices/lab_pin.sym} 2620 -2500 0 1 {name=l164 lab=IOVDD}
C {devices/lab_pin.sym} 2600 -2400 0 0 {name=l165 lab=IOVSS}
C {devices/lab_pin.sym} 2640 -2400 0 1 {name=l166 lab=VSS}
C {devices/lab_pin.sym} 2980 -2500 0 0 {name=l167 lab=VDD}
C {devices/lab_pin.sym} 2960 -2400 0 0 {name=l168 lab=VSS}
C {devices/lab_pin.sym} 3020 -2500 0 1 {name=l169 lab=IOVDD}
C {devices/lab_pin.sym} 3000 -2400 0 0 {name=l170 lab=IOVSS}
C {devices/lab_pin.sym} 3040 -2400 0 1 {name=l171 lab=VSS}
C {devices/lab_pin.sym} 490 -2100 0 1 {name=l172 lab=_nc1}
C {devices/lab_pin.sym} 380 -2150 0 0 {name=l173 lab=VDD}
C {devices/lab_pin.sym} 360 -2050 0 0 {name=l174 lab=VSS}
C {devices/lab_pin.sym} 420 -2150 0 1 {name=l175 lab=IOVDD}
C {devices/lab_pin.sym} 400 -2050 0 0 {name=l176 lab=IOVSS}
C {devices/lab_pin.sym} 440 -2050 0 1 {name=l177 lab=VSS}
C {devices/lab_pin.sym} 490 -1900 0 1 {name=l178 lab=_nc2}
C {devices/lab_pin.sym} 380 -1950 0 0 {name=l179 lab=VDD}
C {devices/lab_pin.sym} 360 -1850 0 0 {name=l180 lab=VSS}
C {devices/lab_pin.sym} 420 -1950 0 1 {name=l181 lab=IOVDD}
C {devices/lab_pin.sym} 400 -1850 0 0 {name=l182 lab=IOVSS}
C {devices/lab_pin.sym} 440 -1850 0 1 {name=l183 lab=VSS}
C {devices/lab_pin.sym} 490 -1700 0 1 {name=l184 lab=_nc3}
C {devices/lab_pin.sym} 380 -1750 0 0 {name=l185 lab=VDD}
C {devices/lab_pin.sym} 360 -1650 0 0 {name=l186 lab=VSS}
C {devices/lab_pin.sym} 420 -1750 0 1 {name=l187 lab=IOVDD}
C {devices/lab_pin.sym} 400 -1650 0 0 {name=l188 lab=IOVSS}
C {devices/lab_pin.sym} 440 -1650 0 1 {name=l189 lab=VSS}
C {devices/lab_pin.sym} 4110 -1900 0 0 {name=l190 lab=gate_o}
C {devices/lab_pin.sym} 4220 -1950 0 1 {name=l191 lab=VDD}
C {devices/lab_pin.sym} 4240 -1850 0 1 {name=l192 lab=VSS}
C {devices/lab_pin.sym} 4180 -1950 0 0 {name=l193 lab=IOVDD}
C {devices/lab_pin.sym} 4200 -1850 0 0 {name=l194 lab=IOVSS}
C {devices/lab_pin.sym} 4160 -1850 0 0 {name=l195 lab=VSS}
C {devices/lab_pin.sym} 4110 -1700 0 0 {name=l196 lab=fault_n_o}
C {devices/lab_pin.sym} 4220 -1750 0 1 {name=l197 lab=VDD}
C {devices/lab_pin.sym} 4240 -1650 0 1 {name=l198 lab=VSS}
C {devices/lab_pin.sym} 4180 -1750 0 0 {name=l199 lab=IOVDD}
C {devices/lab_pin.sym} 4200 -1650 0 0 {name=l200 lab=IOVSS}
C {devices/lab_pin.sym} 4160 -1650 0 0 {name=l201 lab=VSS}
C {devices/lab_pin.sym} 490 -1100 0 1 {name=l202 lab=en_i}
C {devices/lab_pin.sym} 380 -1150 0 0 {name=l203 lab=VDD}
C {devices/lab_pin.sym} 360 -1050 0 0 {name=l204 lab=VSS}
C {devices/lab_pin.sym} 420 -1150 0 1 {name=l205 lab=IOVDD}
C {devices/lab_pin.sym} 400 -1050 0 0 {name=l206 lab=IOVSS}
C {devices/lab_pin.sym} 440 -1050 0 1 {name=l207 lab=VSS}
C {devices/lab_pin.sym} 490 -1300 0 1 {name=l208 lab=i_core_trip_set}
C {devices/lab_pin.sym} 380 -1350 0 0 {name=l209 lab=VDD}
C {devices/lab_pin.sym} 360 -1250 0 0 {name=l210 lab=VSS}
C {devices/lab_pin.sym} 420 -1350 0 1 {name=l211 lab=IOVDD}
C {devices/lab_pin.sym} 400 -1250 0 0 {name=l212 lab=IOVSS}
C {devices/lab_pin.sym} 440 -1250 0 1 {name=l213 lab=VSS}
C {devices/lab_pin.sym} 490 -900 0 1 {name=l214 lab=i_core_sclk_i}
C {devices/lab_pin.sym} 380 -950 0 0 {name=l215 lab=VDD}
C {devices/lab_pin.sym} 360 -850 0 0 {name=l216 lab=VSS}
C {devices/lab_pin.sym} 420 -950 0 1 {name=l217 lab=IOVDD}
C {devices/lab_pin.sym} 400 -850 0 0 {name=l218 lab=IOVSS}
C {devices/lab_pin.sym} 440 -850 0 1 {name=l219 lab=VSS}
C {devices/lab_pin.sym} 490 -700 0 1 {name=l220 lab=i_core_sdi_i}
C {devices/lab_pin.sym} 380 -750 0 0 {name=l221 lab=VDD}
C {devices/lab_pin.sym} 360 -650 0 0 {name=l222 lab=VSS}
C {devices/lab_pin.sym} 420 -750 0 1 {name=l223 lab=IOVDD}
C {devices/lab_pin.sym} 400 -650 0 0 {name=l224 lab=IOVSS}
C {devices/lab_pin.sym} 440 -650 0 1 {name=l225 lab=VSS}
C {devices/lab_pin.sym} 4110 -1500 0 0 {name=l226 lab=i_core_sdo_o}
C {devices/lab_pin.sym} 4220 -1550 0 1 {name=l227 lab=VDD}
C {devices/lab_pin.sym} 4240 -1450 0 1 {name=l228 lab=VSS}
C {devices/lab_pin.sym} 4180 -1550 0 0 {name=l229 lab=IOVDD}
C {devices/lab_pin.sym} 4200 -1450 0 0 {name=l230 lab=IOVSS}
C {devices/lab_pin.sym} 4160 -1450 0 0 {name=l231 lab=VSS}
C {devices/lab_pin.sym} 4110 -1300 0 0 {name=l232 lab=i_core_temp_out_o}
C {devices/lab_pin.sym} 4220 -1350 0 1 {name=l233 lab=VDD}
C {devices/lab_pin.sym} 4240 -1250 0 1 {name=l234 lab=VSS}
C {devices/lab_pin.sym} 4180 -1350 0 0 {name=l235 lab=IOVDD}
C {devices/lab_pin.sym} 4200 -1250 0 0 {name=l236 lab=IOVSS}
C {devices/lab_pin.sym} 4160 -1250 0 0 {name=l237 lab=VSS}
C {devices/lab_pin.sym} 490 -1500 0 1 {name=l238 lab=i_core_vref}
C {devices/lab_pin.sym} 380 -1550 0 0 {name=l239 lab=VDD}
C {devices/lab_pin.sym} 360 -1450 0 0 {name=l240 lab=VSS}
C {devices/lab_pin.sym} 420 -1550 0 1 {name=l241 lab=IOVDD}
C {devices/lab_pin.sym} 400 -1450 0 0 {name=l242 lab=IOVSS}
C {devices/lab_pin.sym} 440 -1450 0 1 {name=l243 lab=VSS}
C {devices/lab_pin.sym} 910 -150 0 0 {name=l244 lab=G_SHARED}
C {devices/lab_pin.sym} 1090 -150 0 1 {name=l245 lab=_nc4}
C {devices/lab_pin.sym} 980 -200 0 0 {name=l246 lab=VDD}
C {devices/lab_pin.sym} 960 -100 0 0 {name=l247 lab=VSS}
C {devices/lab_pin.sym} 1020 -200 0 1 {name=l248 lab=IOVDD}
C {devices/lab_pin.sym} 1000 -100 0 0 {name=l249 lab=IOVSS}
C {devices/lab_pin.sym} 1040 -100 0 1 {name=l250 lab=VSS}
C {devices/lab_pin.sym} 1310 -150 0 0 {name=l251 lab=D_STD}
C {devices/lab_pin.sym} 1490 -150 0 1 {name=l252 lab=_nc5}
C {devices/lab_pin.sym} 1380 -200 0 0 {name=l253 lab=VDD}
C {devices/lab_pin.sym} 1360 -100 0 0 {name=l254 lab=VSS}
C {devices/lab_pin.sym} 1420 -200 0 1 {name=l255 lab=IOVDD}
C {devices/lab_pin.sym} 1400 -100 0 0 {name=l256 lab=IOVSS}
C {devices/lab_pin.sym} 1440 -100 0 1 {name=l257 lab=VSS}
C {devices/lab_pin.sym} 1710 -150 0 0 {name=l258 lab=D_ELT}
C {devices/lab_pin.sym} 1890 -150 0 1 {name=l259 lab=_nc6}
C {devices/lab_pin.sym} 1780 -200 0 0 {name=l260 lab=VDD}
C {devices/lab_pin.sym} 1760 -100 0 0 {name=l261 lab=VSS}
C {devices/lab_pin.sym} 1820 -200 0 1 {name=l262 lab=IOVDD}
C {devices/lab_pin.sym} 1800 -100 0 0 {name=l263 lab=IOVSS}
C {devices/lab_pin.sym} 1840 -100 0 1 {name=l264 lab=VSS}
C {devices/lab_pin.sym} 2310 -150 0 0 {name=l265 lab=HBT_E}
C {devices/lab_pin.sym} 2490 -150 0 1 {name=l266 lab=_nc7}
C {devices/lab_pin.sym} 2380 -200 0 0 {name=l267 lab=VDD}
C {devices/lab_pin.sym} 2360 -100 0 0 {name=l268 lab=VSS}
C {devices/lab_pin.sym} 2420 -200 0 1 {name=l269 lab=IOVDD}
C {devices/lab_pin.sym} 2400 -100 0 0 {name=l270 lab=IOVSS}
C {devices/lab_pin.sym} 2440 -100 0 1 {name=l271 lab=VSS}
C {devices/lab_pin.sym} 2710 -150 0 0 {name=l272 lab=HBT_B}
C {devices/lab_pin.sym} 2890 -150 0 1 {name=l273 lab=_nc8}
C {devices/lab_pin.sym} 2780 -200 0 0 {name=l274 lab=VDD}
C {devices/lab_pin.sym} 2760 -100 0 0 {name=l275 lab=VSS}
C {devices/lab_pin.sym} 2820 -200 0 1 {name=l276 lab=IOVDD}
C {devices/lab_pin.sym} 2800 -100 0 0 {name=l277 lab=IOVSS}
C {devices/lab_pin.sym} 2840 -100 0 1 {name=l278 lab=VSS}
C {devices/lab_pin.sym} 3110 -150 0 0 {name=l279 lab=HBT_C}
C {devices/lab_pin.sym} 3290 -150 0 1 {name=l280 lab=_nc9}
C {devices/lab_pin.sym} 3180 -200 0 0 {name=l281 lab=VDD}
C {devices/lab_pin.sym} 3160 -100 0 0 {name=l282 lab=VSS}
C {devices/lab_pin.sym} 3220 -200 0 1 {name=l283 lab=IOVDD}
C {devices/lab_pin.sym} 3200 -100 0 0 {name=l284 lab=IOVSS}
C {devices/lab_pin.sym} 3240 -100 0 1 {name=l285 lab=VSS}
C {devices/lab_pin.sym} 1650 -2560 0 1 {name=l286 lab=VSS}
C {devices/lab_pin.sym} 2450 -2560 0 1 {name=l287 lab=IOVSS}
N 2660 -500 2680 -500 {}
N 2680 -500 2680 -1240 {}
N 2680 -1240 2810 -1240 {}
N 250 -2100 310 -2100 {}
N 250 -1900 310 -1900 {}
N 250 -1700 310 -1700 {}
N 4350 -1900 4290 -1900 {}
N 4350 -1700 4290 -1700 {}
N 250 -1100 310 -1100 {}
N 250 -1300 310 -1300 {}
N 250 -900 310 -900 {}
N 250 -700 310 -700 {}
N 4350 -1500 4290 -1500 {}
N 4350 -1300 4290 -1300 {}
N 250 -1500 310 -1500 {}
N 2050 -40 2110 -40 {}
N 1650 -40 1590 -40 {}
N 250 -1100 190 -1100 {}
N 4350 -1700 4410 -1700 {}
N 4350 -1900 4410 -1900 {}
N 1250 -40 1190 -40 {}
N 3050 -40 3110 -40 {}
N 3450 -40 3510 -40 {}
N 2650 -40 2710 -40 {}
N 250 -900 190 -900 {}
N 250 -700 190 -700 {}
N 4350 -1500 4410 -1500 {}
N 250 -1700 190 -1700 {}
N 250 -1900 190 -1900 {}
N 4350 -1300 4410 -1300 {}
N 250 -1300 190 -1300 {}
N 250 -2100 190 -2100 {}
N 250 -1500 190 -1500 {}
N 1250 -2560 1190 -2560 {}
N 2850 -2560 2910 -2560 {}
N 2050 -2560 2110 -2560 {}
N 3250 -2560 3310 -2560 {}

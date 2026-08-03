v {xschem version=3.4.8RC file_version=1.2}
G {}
K {type=subcircuit
format=".subckt p1_comparator PBIT_OUT PBIT_RAW CLK_OUT_DIV IN_P IN_N CLK_P CLK_N TRIM_P TRIM_N VCC_HBT VDD VSS"
template="name=X1"
}
V {}
S {}
E {}
T {P1_COMPARATOR - 5.0 GS/s Clocked HBT CML Latch + 10-Bit Trim DAC (Bypassed PTAT Mirror)} -200 -250 0 0 0.5 0.5 {}

# Subcircuit Ports
C {devices/opin.sym} 560 -140 0 0 {name=p1 lab=PBIT_OUT}
C {devices/opin.sym} 500 0 0 0 {name=p2 lab=PBIT_RAW}
C {devices/opin.sym} 500 80 0 0 {name=p3 lab=CLK_OUT_DIV}
C {devices/ipin.sym} -300 -80 0 0 {name=p4 lab=IN_P}
C {devices/ipin.sym} -300 -20 0 0 {name=p5 lab=IN_N}
C {devices/ipin.sym} -300 40 0 0 {name=p6 lab=CLK_P}
C {devices/ipin.sym} -300 100 0 0 {name=p7 lab=CLK_N}
C {devices/ipin.sym} -300 160 0 0 {name=p11 lab=TRIM_P}
C {devices/ipin.sym} -300 220 0 0 {name=p12 lab=TRIM_N}
C {devices/iopin.sym} 0 -220 0 0 {name=p8 lab=VCC_HBT}
C {devices/iopin.sym} 100 -220 0 0 {name=p9 lab=VDD}
C {devices/iopin.sym} 0 280 0 0 {name=p10 lab=VSS}

# CML Load Resistors (RC1, RC2 = 300 Ohm, physical rppd)
C {sg13g2_pr/rppd.sym} -180 -170 0 0 {name=RC1 value=300 w=1.0u l=0.838u model=rppd spiceprefix=X}
C {devices/lab_pin.sym} -180 -200 0 0 {lab=VCC_HBT}
C {devices/lab_pin.sym} -180 -140 0 0 {lab=c_n}

C {sg13g2_pr/rppd.sym} -100 -170 0 0 {name=RC2 value=300 w=1.0u l=0.838u model=rppd spiceprefix=X}
C {devices/lab_pin.sym} -100 -200 0 0 {lab=VCC_HBT}
C {devices/lab_pin.sym} -100 -140 0 0 {lab=c_p}

# Track Stage Input Pair (Q1, Q2)
C {sg13g2_pr/npn13G2.sym} -180 -80 0 0 {name=Q1 Nx=1 model=npn13G2 spiceprefix=X}
C {devices/lab_pin.sym} -160 -110 0 0 {lab=c_n}
C {devices/lab_pin.sym} -200 -80 0 0 {lab=IN_P}
C {devices/lab_pin.sym} -160 -50 0 0 {lab=e_track}
C {devices/lab_pin.sym} -160 -80 0 0 {lab=sub!}

C {sg13g2_pr/npn13G2.sym} -100 -80 0 0 {name=Q2 Nx=1 model=npn13G2 spiceprefix=X}
C {devices/lab_pin.sym} -80 -110 0 0 {lab=c_p}
C {devices/lab_pin.sym} -120 -80 0 0 {lab=IN_N}
C {devices/lab_pin.sym} -80 -50 0 0 {lab=e_track}
C {devices/lab_pin.sym} -80 -80 0 0 {lab=sub!}

# Emitter Damping Resistors (RBLEED_TRACK, RBLEED_LATCH = 50 Ohm to e_tail)
C {sg13g2_pr/rppd.sym} -160 -20 0 0 {name=RBLEED_TRACK value=50 w=1.0u l=0.50u model=rppd spiceprefix=X}
C {devices/lab_pin.sym} -160 -50 0 0 {lab=e_track}
C {devices/lab_pin.sym} -160 10 0 0 {lab=e_tail}

C {sg13g2_pr/rppd.sym} 0 -20 0 0 {name=RBLEED_LATCH value=50 w=1.0u l=0.50u model=rppd spiceprefix=X}
C {devices/lab_pin.sym} 0 -50 0 0 {lab=e_latch}
C {devices/lab_pin.sym} 0 10 0 0 {lab=e_tail}

# Latch Stage Regenerative Pair (Q3, Q4)
C {sg13g2_pr/npn13G2.sym} -20 -80 0 0 {name=Q3 Nx=1 model=npn13G2 spiceprefix=X}
C {devices/lab_pin.sym} 0 -110 0 0 {lab=c_n}
C {devices/lab_pin.sym} -40 -80 0 0 {lab=ef_p}
C {devices/lab_pin.sym} 0 -50 0 0 {lab=e_latch}
C {devices/lab_pin.sym} 0 -80 0 0 {lab=sub!}

C {sg13g2_pr/npn13G2.sym} 60 -80 0 0 {name=Q4 Nx=1 model=npn13G2 spiceprefix=X}
C {devices/lab_pin.sym} 80 -110 0 0 {lab=c_p}
C {devices/lab_pin.sym} 40 -80 0 0 {lab=ef_n}
C {devices/lab_pin.sym} 80 -50 0 0 {lab=e_latch}
C {devices/lab_pin.sym} 80 -80 0 0 {lab=sub!}

# Clocked Tail Differential Pair (QCLK_TRACK, QCLK_LATCH)
C {sg13g2_pr/npn13G2.sym} -120 20 0 0 {name=QCLK_TRACK Nx=1 model=npn13G2 spiceprefix=X}
C {devices/lab_pin.sym} -100 -10 0 0 {lab=e_track}
C {devices/lab_pin.sym} -140 20 0 0 {lab=CLK_P}
C {devices/lab_pin.sym} -100 50 0 0 {lab=e_tail}
C {devices/lab_pin.sym} -100 20 0 0 {lab=sub!}

C {sg13g2_pr/npn13G2.sym} 20 20 0 0 {name=QCLK_LATCH Nx=1 model=npn13G2 spiceprefix=X}
C {devices/lab_pin.sym} 40 -10 0 0 {lab=e_latch}
C {devices/lab_pin.sym} 0 20 0 0 {lab=CLK_N}
C {devices/lab_pin.sym} 40 50 0 0 {lab=e_tail}
C {devices/lab_pin.sym} 40 20 0 0 {lab=sub!}

# Internal PTAT Master Reference Generator Cell (Autonomous Bias Node c_p1_comp)
C {sg13g2_pr/sg13_hv_pmos.sym} -200 120 0 0 {name=MP1_COMP w=20.0u l=1.0u model=sg13_hv_pmos spiceprefix=X}
C {devices/lab_pin.sym} -180 90 0 0 {lab=VCC_HBT}
C {devices/lab_pin.sym} -180 150 0 0 {lab=c_p1_comp}
C {devices/lab_pin.sym} -220 120 0 0 {lab=c_p2_comp}
C {devices/lab_pin.sym} -180 120 0 0 {lab=VCC_HBT}

C {sg13g2_pr/sg13_hv_pmos.sym} -140 120 0 0 {name=MP2_COMP w=20.0u l=1.0u model=sg13_hv_pmos spiceprefix=X}
C {devices/lab_pin.sym} -120 90 0 0 {lab=VCC_HBT}
C {devices/lab_pin.sym} -120 150 0 0 {lab=c_p2_comp}
C {devices/lab_pin.sym} -160 120 0 0 {lab=c_p2_comp}
C {devices/lab_pin.sym} -120 120 0 0 {lab=VCC_HBT}

C {sg13g2_pr/npn13G2.sym} -200 220 0 0 {name=QP1_COMP Nx=1 model=npn13G2 spiceprefix=X}
C {devices/lab_pin.sym} -180 190 0 0 {lab=c_p1_comp}
C {devices/lab_pin.sym} -220 220 0 0 {lab=c_p1_comp}
C {devices/lab_pin.sym} -180 250 0 0 {lab=e_p1_comp}
C {devices/lab_pin.sym} -180 220 0 0 {lab=sub!}

C {sg13g2_pr/rppd.sym} -180 280 0 0 {name=RDEG_P1_COMP value=50 w=4.0u l=0.50u model=rppd spiceprefix=X}
C {devices/lab_pin.sym} -180 250 0 0 {lab=e_p1_comp}
C {devices/lab_pin.sym} -180 310 0 0 {lab=VSS}

C {sg13g2_pr/npn13G2.sym} -140 220 0 0 {name=QP2_COMP Nx=4 model=npn13G2 spiceprefix=X}
C {devices/lab_pin.sym} -120 190 0 0 {lab=c_p2_comp}
C {devices/lab_pin.sym} -160 220 0 0 {lab=c_p1_comp}
C {devices/lab_pin.sym} -120 250 0 0 {lab=e_p2_comp}
C {devices/lab_pin.sym} -120 220 0 0 {lab=sub!}

C {sg13g2_pr/rppd.sym} -120 280 0 0 {name=RPTAT_COMP value=178.9 w=2.0u l=1.107u model=rppd spiceprefix=X}
C {devices/lab_pin.sym} -120 250 0 0 {lab=e_p2_comp}
C {devices/lab_pin.sym} -120 310 0 0 {lab=VSS}

# Decoupling Cap for PTAT Bias Node (CSTAB_COMP = 10 pF)
C {sg13g2_pr/cap_cmim.sym} -200 150 0 0 {name=CSTAB_COMP w=80.0u l=83.3u model=cap_cmim spiceprefix=X}
C {devices/lab_pin.sym} -200 180 0 0 {lab=c_p1_comp}
C {devices/lab_pin.sym} -200 120 0 0 {lab=VSS}

# Comparator Tail Current Transistor
C {sg13g2_pr/npn13G2.sym} -50 120 0 0 {name=QS_COMP Nx=6 model=npn13G2 spiceprefix=X}
C {devices/lab_pin.sym} -30 90 0 0 {lab=e_tail}
C {devices/lab_pin.sym} -70 120 0 0 {lab=c_p1_comp}
C {devices/lab_pin.sym} -30 150 0 0 {lab=e_scomp}
C {devices/lab_pin.sym} -30 120 0 0 {lab=sub!}

C {sg13g2_pr/rppd.sym} -30 180 0 0 {name=RDEG_SCOMP value=8.33 w=24.0u l=0.50u model=rppd spiceprefix=X}
C {devices/lab_pin.sym} -30 150 0 0 {lab=e_scomp}
C {devices/lab_pin.sym} -30 210 0 0 {lab=VSS}

# Sub-Block 2: Emitter-Follower Level Shifters (QEF1, QEF2)
C {sg13g2_pr/npn13G2.sym} 140 -80 0 0 {name=QEF1 Nx=1 model=npn13G2 spiceprefix=X}
C {devices/lab_pin.sym} 160 -110 0 0 {lab=VCC_HBT}
C {devices/lab_pin.sym} 120 -80 0 0 {lab=c_p}
C {devices/lab_pin.sym} 160 -50 0 0 {lab=ef_p}
C {devices/lab_pin.sym} 160 -80 0 0 {lab=sub!}

C {sg13g2_pr/npn13G2.sym} 200 -80 0 0 {name=QEF2 Nx=1 model=npn13G2 spiceprefix=X}
C {devices/lab_pin.sym} 220 -110 0 0 {lab=VCC_HBT}
C {devices/lab_pin.sym} 180 -80 0 0 {lab=c_n}
C {devices/lab_pin.sym} 220 -50 0 0 {lab=ef_n}
C {devices/lab_pin.sym} 220 -80 0 0 {lab=sub!}

# Precision Resistor Level-Shifter Network (6.0k / 4.0k -> 0.520V Gate DC)
C {sg13g2_pr/rppd.sym} 160 -20 0 0 {name=R1_P value=6.0k w=1.0u l=22.0u model=rppd spiceprefix=X}
C {devices/lab_pin.sym} 160 -50 0 0 {lab=ef_p}
C {devices/lab_pin.sym} 160 10 0 0 {lab=g_p}

C {sg13g2_pr/rppd.sym} 160 40 0 0 {name=R2_P value=4.0k w=1.0u l=14.5u model=rppd spiceprefix=X}
C {devices/lab_pin.sym} 160 10 0 0 {lab=g_p}
C {devices/lab_pin.sym} 160 70 0 0 {lab=VSS}

C {sg13g2_pr/rppd.sym} 220 -20 0 0 {name=R1_N value=6.0k w=1.0u l=22.0u model=rppd spiceprefix=X}
C {devices/lab_pin.sym} 220 -50 0 0 {lab=ef_n}
C {devices/lab_pin.sym} 220 10 0 0 {lab=g_n}

C {sg13g2_pr/rppd.sym} 220 40 0 0 {name=R2_N value=4.0k w=1.0u l=14.5u model=rppd spiceprefix=X}
C {devices/lab_pin.sym} 220 10 0 0 {lab=g_n}
C {devices/lab_pin.sym} 220 70 0 0 {lab=VSS}

# Sub-Block 3: High-Gain CMOS Differential-to-Single-Ended Converter (1:1 Symmetric PMOS Mirror)
C {sg13g2_pr/sg13_lv_nmos.sym} 260 -80 0 0 {name=M1 w=6.0u l=0.13u model=sg13_lv_nmos spiceprefix=X}
C {devices/lab_pin.sym} 280 -110 0 0 {lab=cml_out_n}
C {devices/lab_pin.sym} 240 -80 0 0 {lab=g_p}
C {devices/lab_pin.sym} 280 -50 0 0 {lab=e_cmos}
C {devices/lab_pin.sym} 280 -80 0 0 {lab=VSS}

C {sg13g2_pr/sg13_lv_nmos.sym} 320 -80 0 0 {name=M2 w=6.0u l=0.13u model=sg13_lv_nmos spiceprefix=X}
C {devices/lab_pin.sym} 340 -110 0 0 {lab=cml_out_p}
C {devices/lab_pin.sym} 300 -80 0 0 {lab=g_n}
C {devices/lab_pin.sym} 340 -50 0 0 {lab=e_cmos}
C {devices/lab_pin.sym} 340 -80 0 0 {lab=VSS}

C {sg13g2_pr/sg13_lv_nmos.sym} 290 -20 0 0 {name=MTAIL w=8.0u l=0.50u model=sg13_lv_nmos spiceprefix=X}
C {devices/lab_pin.sym} 310 -50 0 0 {lab=e_cmos}
C {devices/lab_pin.sym} 270 -20 0 0 {lab=VDD}
C {devices/lab_pin.sym} 310 10 0 0 {lab=VSS}
C {devices/lab_pin.sym} 310 -20 0 0 {lab=VSS}

C {sg13g2_pr/sg13_lv_pmos.sym} 260 -170 0 0 {name=M3 w=8.0u l=0.13u model=sg13_lv_pmos spiceprefix=X}
C {devices/lab_pin.sym} 280 -140 0 0 {lab=cml_out_n}
C {devices/lab_pin.sym} 240 -170 0 0 {lab=cml_out_n}
C {devices/lab_pin.sym} 280 -200 0 0 {lab=VDD}
C {devices/lab_pin.sym} 280 -170 0 0 {lab=VDD}

C {sg13g2_pr/sg13_lv_pmos.sym} 320 -170 0 0 {name=M4 w=8.0u l=0.13u model=sg13_lv_pmos spiceprefix=X}
C {devices/lab_pin.sym} 340 -140 0 0 {lab=cml_out_p}
C {devices/lab_pin.sym} 300 -170 0 0 {lab=cml_out_n}
C {devices/lab_pin.sym} 340 -200 0 0 {lab=VDD}
C {devices/lab_pin.sym} 340 -170 0 0 {lab=VDD}

# CMOS Interface Damping Filter (CDAMP1, CDAMP2 = 38.3 fF)
C {sg13g2_pr/cap_cmim.sym} 350 -140 0 0 {name=CDAMP1 w=5.0u l=5.0u model=cap_cmim spiceprefix=X}
C {devices/lab_pin.sym} 350 -170 0 0 {lab=cml_out_p}
C {devices/lab_pin.sym} 350 -110 0 0 {lab=VSS}

C {sg13g2_pr/cap_cmim.sym} 230 -140 0 0 {name=CDAMP2 w=5.0u l=5.0u model=cap_cmim spiceprefix=X}
C {devices/lab_pin.sym} 230 -170 0 0 {lab=cml_out_n}
C {devices/lab_pin.sym} 230 -110 0 0 {lab=VSS}

# Inverter Driver 1 (M5, M6 -> raw_inv)
C {sg13g2_pr/sg13_lv_pmos.sym} 380 -170 0 0 {name=M5 w=2.83u l=0.13u model=sg13_lv_pmos spiceprefix=X}
C {devices/lab_pin.sym} 400 -140 0 0 {lab=raw_inv}
C {devices/lab_pin.sym} 360 -170 0 0 {lab=cml_out_p}
C {devices/lab_pin.sym} 400 -200 0 0 {lab=VDD}
C {devices/lab_pin.sym} 400 -170 0 0 {lab=VDD}

C {sg13g2_pr/sg13_lv_nmos.sym} 380 -80 0 0 {name=M6 w=2.0u l=0.13u model=sg13_lv_nmos spiceprefix=X}
C {devices/lab_pin.sym} 400 -110 0 0 {lab=raw_inv}
C {devices/lab_pin.sym} 360 -80 0 0 {lab=cml_out_p}
C {devices/lab_pin.sym} 400 -50 0 0 {lab=VSS}
C {devices/lab_pin.sym} 400 -80 0 0 {lab=VSS}

# Inverter Driver 2 (M7, M8 -> PBIT_RAW)
C {sg13g2_pr/sg13_lv_pmos.sym} 440 -170 0 0 {name=M7 w=2.83u l=0.13u model=sg13_lv_pmos spiceprefix=X}
C {devices/lab_pin.sym} 460 -140 0 0 {lab=PBIT_RAW}
C {devices/lab_pin.sym} 420 -170 0 0 {lab=raw_inv}
C {devices/lab_pin.sym} 460 -200 0 0 {lab=VDD}
C {devices/lab_pin.sym} 460 -170 0 0 {lab=VDD}

C {sg13g2_pr/sg13_lv_nmos.sym} 440 -80 0 0 {name=M8 w=2.0u l=0.13u model=sg13_lv_nmos spiceprefix=X}
C {devices/lab_pin.sym} 460 -110 0 0 {lab=PBIT_RAW}
C {devices/lab_pin.sym} 420 -80 0 0 {lab=raw_inv}
C {devices/lab_pin.sym} 460 -50 0 0 {lab=VSS}
C {devices/lab_pin.sym} 460 -80 0 0 {lab=VSS}

# Inverter Driver 3 (M9, M10 -> PBIT_OUT)
C {sg13g2_pr/sg13_lv_pmos.sym} 500 -170 0 0 {name=M9 w=2.83u l=0.13u model=sg13_lv_pmos spiceprefix=X}
C {devices/lab_pin.sym} 520 -140 0 0 {lab=PBIT_OUT}
C {devices/lab_pin.sym} 480 -170 0 0 {lab=PBIT_RAW}
C {devices/lab_pin.sym} 520 -200 0 0 {lab=VDD}
C {devices/lab_pin.sym} 520 -170 0 0 {lab=VDD}

C {sg13g2_pr/sg13_lv_nmos.sym} 500 -80 0 0 {name=M10 w=2.0u l=0.13u model=sg13_lv_nmos spiceprefix=X}
C {devices/lab_pin.sym} 520 -110 0 0 {lab=PBIT_OUT}
C {devices/lab_pin.sym} 480 -80 0 0 {lab=PBIT_RAW}
C {devices/lab_pin.sym} 520 -50 0 0 {lab=VSS}
C {devices/lab_pin.sym} 520 -80 0 0 {lab=VSS}

# Clock Divider Buffer (M11, M12 -> CLK_OUT_DIV driven by CLK_P)
C {sg13g2_pr/sg13_lv_pmos.sym} 440 80 0 0 {name=M11 w=2.83u l=0.13u model=sg13_lv_pmos spiceprefix=X}
C {devices/lab_pin.sym} 460 110 0 0 {lab=CLK_OUT_DIV}
C {devices/lab_pin.sym} 420 80 0 0 {lab=CLK_P}
C {devices/lab_pin.sym} 460 50 0 0 {lab=VDD}
C {devices/lab_pin.sym} 460 80 0 0 {lab=VDD}

C {sg13g2_pr/sg13_lv_nmos.sym} 440 170 0 0 {name=M12 w=2.0u l=0.13u model=sg13_lv_nmos spiceprefix=X}
C {devices/lab_pin.sym} 460 140 0 0 {lab=CLK_OUT_DIV}
C {devices/lab_pin.sym} 420 170 0 0 {lab=CLK_P}
C {devices/lab_pin.sym} 460 200 0 0 {lab=VSS}
C {devices/lab_pin.sym} 460 170 0 0 {lab=VSS}

# Sub-Block 4: Integrated 10-Bit Differential Offset Trim DAC
C {sg13g2_pr/npn13G2.sym} -20 200 0 0 {name=QDAC_P Nx=1 model=npn13G2 spiceprefix=X}
C {devices/lab_pin.sym} 0 170 0 0 {lab=c_p}
C {devices/lab_pin.sym} -40 200 0 0 {lab=TRIM_P}
C {devices/lab_pin.sym} 0 230 0 0 {lab=e_dac_p}
C {devices/lab_pin.sym} 0 200 0 0 {lab=sub!}

C {sg13g2_pr/rppd.sym} 0 260 0 0 {name=RDAC_P value=1.5k w=1.0u l=5.4u model=rppd spiceprefix=X}
C {devices/lab_pin.sym} 0 230 0 0 {lab=e_dac_p}
C {devices/lab_pin.sym} 0 290 0 0 {lab=VSS}

C {sg13g2_pr/npn13G2.sym} 60 200 0 0 {name=QDAC_N Nx=1 model=npn13G2 spiceprefix=X}
C {devices/lab_pin.sym} 80 170 0 0 {lab=c_n}
C {devices/lab_pin.sym} 40 200 0 0 {lab=TRIM_N}
C {devices/lab_pin.sym} 80 230 0 0 {lab=e_dac_n}
C {devices/lab_pin.sym} 80 200 0 0 {lab=sub!}

C {sg13g2_pr/rppd.sym} 80 260 0 0 {name=RDAC_N value=1.5k w=1.0u l=5.4u model=rppd spiceprefix=X}
C {devices/lab_pin.sym} 80 230 0 0 {lab=e_dac_n}
C {devices/lab_pin.sym} 80 290 0 0 {lab=VSS}

# Substrate Tap
C {sg13g2_pr/ptap1.sym} 0 340 0 0 {name=TAP1 w=2.0u l=2.0u model=ptap1 spiceprefix=X}
C {devices/lab_pin.sym} 0 310 0 0 {lab=VSS}
C {devices/lab_pin.sym} 0 370 0 0 {lab=sub!}

v {xschem version=3.4.8RC file_version=1.2}
G {}
K {type=subcircuit
format=".subckt p1_noise_amp NOISE_AMP_P NOISE_AMP_N RAW_NOISE_P RAW_NOISE_N VCC VSS"
template="name=X1"
}
V {}
S {}
E {}
T {P1_NOISE_AMP - 2-Stage AC-Coupled HBT Differential Preamplifier with Forced-Ratio Widlar PTAT} -200 -250 0 0 0.5 0.5 {}
T {Gain = 21.0 dB (11.2x), f_3dB = 5.26 GHz, In = 3.66 mA, P = 9.16 mW} -200 -210 0 0 0.3 0.3 {}

# Subcircuit Ports
C {devices/opin.sym} 400 -100 0 0 {name=p1 lab=NOISE_AMP_P}
C {devices/opin.sym} 400 100 0 0 {name=p2 lab=NOISE_AMP_N}
C {devices/ipin.sym} -300 -100 0 0 {name=p3 lab=RAW_NOISE_P}
C {devices/ipin.sym} -300 100 0 0 {name=p4 lab=RAW_NOISE_N}
C {devices/iopin.sym} 0 -220 0 0 {name=p5 lab=VCC}
C {devices/iopin.sym} 0 280 0 0 {name=p6 lab=VSS}

# Stage 1 Differential Pair (Q1, Q2)
C {sg13g2_pr/npn13G2.sym} -200 -80 0 0 {name=Q1 Nx=2 model=npn13G2 spiceprefix=X}
C {devices/lab_pin.sym} -180 -110 0 0 {lab=c1_n}
C {devices/lab_pin.sym} -220 -80 0 0 {lab=RAW_NOISE_P}
C {devices/lab_pin.sym} -180 -50 0 0 {lab=e1_1}
C {devices/lab_pin.sym} -180 -80 0 0 {lab=sub!}

C {sg13g2_pr/npn13G2.sym} -200 80 0 0 {name=Q2 Nx=2 model=npn13G2 spiceprefix=X}
C {devices/lab_pin.sym} -180 50 0 0 {lab=c1_p}
C {devices/lab_pin.sym} -220 80 0 0 {lab=RAW_NOISE_N}
C {devices/lab_pin.sym} -180 110 0 0 {lab=e1_2}
C {devices/lab_pin.sym} -180 80 0 0 {lab=sub!}

# Connecting Q1 Collector to RC1_1 Pin 2
N -180 -140 -180 -110 {}

# Connecting Q2 Collector to RC1_2 Pin 2
N -180 50 -160 50 {}
N -160 50 -160 140 {}

# Stage 1 Load Resistors (RC1_1, RC1_2 = 255 Ohm)
C {sg13g2_pr/rppd.sym} -180 -170 0 0 {name=RC1_1 value=255 w=1.0u l=0.7115u model=rppd spiceprefix=X}
C {devices/lab_pin.sym} -180 -200 0 0 {lab=VCC}
C {devices/lab_pin.sym} -180 -140 0 0 {lab=c1_n}

C {sg13g2_pr/rppd.sym} -160 170 0 2 {name=RC1_2 value=255 w=1.0u l=0.7115u model=rppd spiceprefix=X}
C {devices/lab_pin.sym} -160 200 0 0 {lab=VCC}
C {devices/lab_pin.sym} -160 140 0 0 {lab=c1_p}

# Stage 1 Emitter Degeneration (RE1_1, RE1_2 = 15 Ohm)
C {sg13g2_pr/rppd.sym} -120 -50 0 0 {name=RE1_1 value=15 w=13.333u l=0.50u model=rppd spiceprefix=X}
C {devices/lab_pin.sym} -120 -80 0 0 {lab=e1_1}
C {devices/lab_pin.sym} -120 -20 0 0 {lab=e1_common}

C {sg13g2_pr/rppd.sym} -120 110 0 0 {name=RE1_2 value=15 w=13.333u l=0.50u model=rppd spiceprefix=X}
C {devices/lab_pin.sym} -120 80 0 0 {lab=e1_2}
C {devices/lab_pin.sym} -120 140 0 0 {lab=e1_common}

# Forced-Ratio Widlar PTAT Master Reference Generator (Pure 1:1 Forcing Loop)
C {sg13g2_pr/sg13_hv_pmos.sym} -70 -200 0 0 {name=MP1 w=20.0u l=1.0u model=sg13_hv_pmos spiceprefix=X}
C {devices/lab_pin.sym} -50 -230 0 0 {lab=VCC}
C {devices/lab_pin.sym} -50 -170 0 0 {lab=c_p1}
C {devices/lab_pin.sym} -90 -200 0 0 {lab=c_p2}
C {devices/lab_pin.sym} -50 -200 0 0 {lab=VCC}

C {sg13g2_pr/sg13_hv_pmos.sym} -10 -200 0 0 {name=MP2 w=20.0u l=1.0u model=sg13_hv_pmos spiceprefix=X}
C {devices/lab_pin.sym} 10 -230 0 0 {lab=VCC}
C {devices/lab_pin.sym} 10 -170 0 0 {lab=c_p2}
C {devices/lab_pin.sym} -30 -200 0 0 {lab=c_p2}
C {devices/lab_pin.sym} 10 -200 0 0 {lab=VCC}

C {sg13g2_pr/npn13G2.sym} -70 -100 0 0 {name=QP1 Nx=1 model=npn13G2 spiceprefix=X}
C {devices/lab_pin.sym} -50 -130 0 0 {lab=c_p1}
C {devices/lab_pin.sym} -90 -100 0 0 {lab=c_p1}
C {devices/lab_pin.sym} -50 -70 0 0 {lab=e_p1}
C {devices/lab_pin.sym} -50 -100 0 0 {lab=sub!}

C {sg13g2_pr/rppd.sym} -50 -40 0 0 {name=RDEG_P1 value=50 w=4.0u l=0.50u model=rppd spiceprefix=X}
C {devices/lab_pin.sym} -50 -10 0 0 {lab=VSS}

C {sg13g2_pr/npn13G2.sym} -10 -100 0 0 {name=QP2 Nx=4 model=npn13G2 spiceprefix=X}
C {devices/lab_pin.sym} 10 -130 0 0 {lab=c_p2}
C {devices/lab_pin.sym} -30 -100 0 0 {lab=c_p1}
C {devices/lab_pin.sym} 10 -70 0 0 {lab=e_p2}
C {devices/lab_pin.sym} 10 -100 0 0 {lab=sub!}

C {sg13g2_pr/rppd.sym} 10 -40 0 0 {name=RPTAT value=178.9 w=2.0u l=1.107u model=rppd spiceprefix=X}
C {devices/lab_pin.sym} 10 -10 0 0 {lab=VSS}

# Stage 1 Scaled Tail Transistor (QS1 driven by c_p1, Nx=9)
C {sg13g2_pr/npn13G2.sym} -50 80 0 0 {name=QS1 Nx=9 model=npn13G2 spiceprefix=X}
C {devices/lab_pin.sym} -30 50 0 0 {lab=e1_common}
C {devices/lab_pin.sym} -70 80 0 0 {lab=c_p1}
C {devices/lab_pin.sym} -30 110 0 0 {lab=e_s1}
C {devices/lab_pin.sym} -30 80 0 0 {lab=sub!}

C {sg13g2_pr/rppd.sym} -30 140 0 0 {name=RDEG_S1 value=5.55 w=36.0u l=0.50u model=rppd spiceprefix=X}
C {devices/lab_pin.sym} -30 170 0 0 {lab=VSS}

# Inter-Stage MIM AC Coupling Capacitors (CAC1, CAC2 = 2.0 pF)
C {sg13g2_pr/cap_cmim.sym} 50 -80 0 0 {name=CAC1 w=36.5u l=36.5u model=cap_cmim spiceprefix=X}
C {devices/lab_pin.sym} 50 -110 0 0 {lab=c1_n}
C {devices/lab_pin.sym} 50 -50 0 0 {lab=b2_p}

C {sg13g2_pr/cap_cmim.sym} 50 80 0 0 {name=CAC2 w=36.5u l=36.5u model=cap_cmim spiceprefix=X}
C {devices/lab_pin.sym} 50 50 0 0 {lab=c1_p}
C {devices/lab_pin.sym} 50 110 0 0 {lab=b2_n}

# Stage 2 Base Bias Resistor Divider (vbias2 = 1.44V)
C {sg13g2_pr/rppd.sym} 130 -230 0 0 {name=RBDIV1 value=10.6k w=1.0u l=40.50u model=rppd spiceprefix=X}
C {devices/lab_pin.sym} 130 -260 0 0 {lab=VCC}
C {devices/lab_pin.sym} 130 -200 0 0 {lab=vbias2}

C {sg13g2_pr/rppd.sym} 130 -170 0 0 {name=RBDIV2 value=14.4k w=1.0u l=55.115u model=rppd spiceprefix=X}
C {devices/lab_pin.sym} 130 -140 0 0 {lab=VSS}

# Stage 2 Base Bias Isolation Resistors (RB2_1, RB2_2 = 50 kOhm)
C {sg13g2_pr/rppd.sym} 170 -170 0 0 {name=RB2_1 value=50k w=1.0u l=192.0u model=rppd spiceprefix=X}
C {devices/lab_pin.sym} 170 -200 0 0 {lab=vbias2}
C {devices/lab_pin.sym} 170 -140 0 0 {lab=b2_p}

C {sg13g2_pr/rppd.sym} 170 170 0 2 {name=RB2_2 value=50k w=1.0u l=192.0u model=rppd spiceprefix=X}
C {devices/lab_pin.sym} 170 200 0 0 {lab=vbias2}
C {devices/lab_pin.sym} 170 140 0 0 {lab=b2_n}

# Stage 2 Differential Pair (Q3, Q4) - Non-inverting Polarity
C {sg13g2_pr/npn13G2.sym} 220 -80 0 0 {name=Q4 Nx=1 model=npn13G2 spiceprefix=X}
C {devices/lab_pin.sym} 240 -110 0 0 {lab=NOISE_AMP_P}
C {devices/lab_pin.sym} 200 -80 0 0 {lab=b2_p}
C {devices/lab_pin.sym} 240 -50 0 0 {lab=e2_1}
C {devices/lab_pin.sym} 240 -80 0 0 {lab=sub!}

C {sg13g2_pr/npn13G2.sym} 220 80 0 0 {name=Q3 Nx=1 model=npn13G2 spiceprefix=X}
C {devices/lab_pin.sym} 240 50 0 0 {lab=NOISE_AMP_N}
C {devices/lab_pin.sym} 200 80 0 0 {lab=b2_n}
C {devices/lab_pin.sym} 260 110 0 0 {lab=e2_2}
C {devices/lab_pin.sym} 240 80 0 0 {lab=sub!}

# Connecting Q4 Collector to RC2_2 Pin 2
N 220 -110 240 -110 {}
N 240 -140 240 -110 {}

# Sideways Routing for Q3 Collector to RC2_1 Pin 2 (running around X=320, Y=170, completely below RE2_2)
N 240 50 320 50 {lab=NOISE_AMP_N}
N 320 50 320 170 {lab=NOISE_AMP_N}
N 320 170 260 170 {lab=NOISE_AMP_N}
N 260 170 260 140 {lab=NOISE_AMP_N}
N 260 140 240 140 {lab=NOISE_AMP_N}

# Connecting Q3 Emitter to RE2_2 Pin 1
N 240 110 280 110 {lab=e2_2}
N 280 110 280 80 {lab=e2_2}

# Stage 2 Load Resistors (RC2_1, RC2_2 = 255 Ohm)
C {sg13g2_pr/rppd.sym} 240 -170 0 0 {name=RC2_2 value=255 w=1.0u l=0.7115u model=rppd spiceprefix=X}
C {devices/lab_pin.sym} 240 -200 0 0 {lab=VCC}
C {devices/lab_pin.sym} 240 -140 0 0 {lab=NOISE_AMP_P}

C {sg13g2_pr/rppd.sym} 240 170 0 2 {name=RC2_1 value=255 w=1.0u l=0.7115u model=rppd spiceprefix=X}
C {devices/lab_pin.sym} 240 200 0 0 {lab=VCC}
C {devices/lab_pin.sym} 240 140 0 0 {lab=NOISE_AMP_N}

# Stage 2 Emitter Degeneration (RE2_1, RE2_2 = 15 Ohm)
C {sg13g2_pr/rppd.sym} 280 -50 0 0 {name=RE2_1 value=15 w=13.333u l=0.50u model=rppd spiceprefix=X}
C {devices/lab_pin.sym} 280 -80 0 0 {lab=e2_1}
C {devices/lab_pin.sym} 280 -20 0 0 {lab=e2_common}

C {sg13g2_pr/rppd.sym} 280 110 0 0 {name=RE2_2 value=15 w=13.333u l=0.50u model=rppd spiceprefix=X}
C {devices/lab_pin.sym} 280 80 0 0 {lab=e2_2}
C {devices/lab_pin.sym} 280 140 0 0 {lab=e2_common}

# Stage 2 Scaled Tail Transistor (QS2 driven by c_p1, Nx=9)
C {sg13g2_pr/npn13G2.sym} 330 80 0 0 {name=QS2 Nx=9 model=npn13G2 spiceprefix=X}
C {devices/lab_pin.sym} 350 50 0 0 {lab=e2_common}
C {devices/lab_pin.sym} 310 80 0 0 {lab=c_p1}
C {devices/lab_pin.sym} 350 110 0 0 {lab=e_s2}
C {devices/lab_pin.sym} 350 80 0 0 {lab=sub!}

C {sg13g2_pr/rppd.sym} 330 140 0 0 {name=RDEG_S2 value=5.55 w=36.0u l=0.50u model=rppd spiceprefix=X}
C {devices/lab_pin.sym} 330 110 0 0 {lab=e_s2}
C {devices/lab_pin.sym} 330 170 0 0 {lab=VSS}

# Substrate Tap ptap1
C {sg13g2_pr/ptap1.sym} 0 240 0 0 {name=TAP1 w=2.0u l=2.0u model=ptap1 spiceprefix=X}
C {devices/lab_pin.sym} 0 210 0 0 {lab=VSS}
C {devices/lab_pin.sym} 0 270 0 0 {lab=sub!}

v {xschem version=3.4.8RC file_version=1.2}
G {}
K {type=subcircuit
format="@spiceprefix@name @pinlist @symname"
template="name=X1"
}
V {}
S {}
E {}
T {P1_NOISE_AMP - 2-Stage Broadband HBT Differential Preamplifier} -200 -250 0 0 0.5 0.5 {}
T {Gain = 21.46 dB (11.8x), f_3dB = 29.6 GHz, inoise = 2.16 nV/rtHz} -200 -210 0 0 0.3 0.3 {}

# Ports
C {devices/opin.sym} 300 -80 0 0 {name=p1 lab=NOISE_AMP_P}
C {devices/opin.sym} 300 80 0 0 {name=p2 lab=NOISE_AMP_N}
C {devices/ipin.sym} -300 -80 0 0 {name=p3 lab=RAW_NOISE_P}
C {devices/ipin.sym} -300 80 0 0 {name=p4 lab=RAW_NOISE_N}
C {devices/iopin.sym} 0 -180 0 0 {name=p5 lab=VCC}
C {devices/iopin.sym} 0 220 0 0 {name=p6 lab=VSS}

# Stage 1 (Nx=2, RE1=15, RC1=240)
C {sg13g2_pr/npn13G2.sym} -150 -50 0 0 {name=Q1 Nx=2 model=npn13G2 spiceprefix=X}
C {sg13g2_pr/npn13G2.sym} -150 50 0 0 {name=Q2 Nx=2 model=npn13G2 spiceprefix=X}
C {devices/res.sym} -100 -120 0 0 {name=RC1_1 value=240 m=1}
C {devices/res.sym} -100 120 0 0 {name=RC1_2 value=240 m=1}
C {devices/res.sym} -80 -20 0 0 {name=RE1_1 value=15 m=1}
C {devices/res.sym} -80 20 0 0 {name=RE1_2 value=15 m=1}
C {devices/isource.sym} -50 0 0 0 {name=ISET1 value=2.0m}

# Stage 2 (Nx=1, RE2=15, RC2=240)
C {sg13g2_pr/npn13G2.sym} 150 -50 0 0 {name=Q3 Nx=1 model=npn13G2 spiceprefix=X}
C {sg13g2_pr/npn13G2.sym} 150 50 0 0 {name=Q4 Nx=1 model=npn13G2 spiceprefix=X}
C {devices/res.sym} 200 -120 0 0 {name=RC2_1 value=240 m=1}
C {devices/res.sym} 200 120 0 0 {name=RC2_2 value=240 m=1}
C {devices/res.sym} 220 -20 0 0 {name=RE2_1 value=15 m=1}
C {devices/res.sym} 220 20 0 0 {name=RE2_2 value=15 m=1}
C {devices/isource.sym} 250 0 0 0 {name=ISET2 value=2.0m}

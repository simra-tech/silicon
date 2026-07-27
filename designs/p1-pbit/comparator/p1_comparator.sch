v {xschem version=3.4.8RC file_version=1.2}
G {}
K {type=subcircuit
format="@spiceprefix@name @pinlist @symname"
template="name=X1"
}
V {}
S {}
E {}
T {P1_COMPARATOR - 5.0 GS/s Clocked HBT CML Latch + 10-Bit Trim DAC} -200 -250 0 0 0.5 0.5 {}
T {Includes Level Shifter & CMOS Rail-to-Rail Output Drivers} -200 -210 0 0 0.3 0.3 {}

# Ports
C {devices/opin.sym} 300 -80 0 0 {name=p1 lab=PBIT_OUT}
C {devices/opin.sym} 300 0 0 0 {name=p2 lab=PBIT_RAW}
C {devices/opin.sym} 300 80 0 0 {name=p3 lab=CLK_OUT_DIV}
C {devices/ipin.sym} -300 -80 0 0 {name=p4 lab=IN_P}
C {devices/ipin.sym} -300 -20 0 0 {name=p5 lab=IN_N}
C {devices/ipin.sym} -300 40 0 0 {name=p6 lab=CLK_P}
C {devices/ipin.sym} -300 100 0 0 {name=p7 lab=CLK_N}
C {devices/iopin.sym} 0 -180 0 0 {name=p8 lab=VCC_HBT}
C {devices/iopin.sym} 100 -180 0 0 {name=p9 lab=VDD}
C {devices/iopin.sym} 0 220 0 0 {name=p10 lab=VSS}

# HBT CML Core & Latch
C {sg13g2_pr/npn13G2.sym} -150 -50 0 0 {name=Q1 Nx=1 model=npn13G2 spiceprefix=X}
C {sg13g2_pr/npn13G2.sym} -150 50 0 0 {name=Q2 Nx=1 model=npn13G2 spiceprefix=X}
C {sg13g2_pr/npn13G2.sym} -50 -50 0 0 {name=Q3 Nx=1 model=npn13G2 spiceprefix=X}
C {sg13g2_pr/npn13G2.sym} -50 50 0 0 {name=Q4 Nx=1 model=npn13G2 spiceprefix=X}

# CMOS Drivers
C {sg13g2_pr/sg13_lv_nmos.sym} 150 -50 0 0 {name=M1 w=2.0u l=0.13u model=sg13_lv_nmos spiceprefix=X}
C {sg13g2_pr/sg13_lv_pmos.sym} 150 50 0 0 {name=M2 w=2.83u l=0.13u model=sg13_lv_pmos spiceprefix=X}

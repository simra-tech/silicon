v {xschem version=3.4.8RC file_version=1.2}
G {}
K {type=subcircuit
format="@spiceprefix@name @pinlist @symname"
template="name=X1"
}
V {}
S {}
E {}
T {P1_NOISE_GEN - Differential HBT Collector Shot Noise Generator} -200 -250 0 0 0.5 0.5 {}
T {Biased at Ic = 1.0 mA per leg, Rc = 1.0 kOhm into VCC=2.5V} -200 -210 0 0 0.3 0.3 {}

# Ports
C {devices/opin.sym} 200 -80 0 0 {name=p1 lab=RAW_NOISE_P}
C {devices/opin.sym} -200 -80 0 0 {name=p2 lab=RAW_NOISE_N}
C {devices/iopin.sym} 0 -180 0 0 {name=p3 lab=VCC}
C {devices/iopin.sym} 0 150 0 0 {name=p4 lab=VSS}

# HBT Differential Pair
C {sg13g2_pr/npn13G2.sym} -100 0 0 0 {name=Q1
Nx=1
model=npn13G2
spiceprefix=X
}
C {sg13g2_pr/npn13G2.sym} 100 0 0 0 {name=Q2
Nx=1
model=npn13G2
spiceprefix=X
}

# Collector Load Resistors (1.0 kOhm)
C {devices/res.sym} -100 -120 0 0 {name=RC1 value=1.0k m=1}
C {devices/res.sym} 100 -120 0 0 {name=RC2 value=1.0k m=1}

# Base Bias Sources
C {devices/vsource.sym} -250 0 0 0 {name=VB1 value=0.872}
C {devices/vsource.sym} 250 0 0 0 {name=VB2 value=0.872}

# Tail Current Source (2.0 mA total -> 1.0 mA per leg)
C {devices/isource.sym} 0 80 0 0 {name=ISET value=2.0m}

# Nets and Wires
# VCC rail
N -100 -180 100 -180 {lab=VCC}
N -100 -180 -100 -150 {lab=VCC}
N 100 -180 100 -150 {lab=VCC}

# Collectors to Loads & Ports
N -100 -90 -100 -30 {lab=RAW_NOISE_N}
N -100 -80 -200 -80 {lab=RAW_NOISE_N}

N 100 -90 100 -30 {lab=RAW_NOISE_P}
N 100 -80 200 -80 {lab=RAW_NOISE_P}

# Emitters to Tail
N -100 30 0 30 {lab=E_TAIL}
N 100 30 0 30 {lab=E_TAIL}
N 0 30 0 50 {lab=E_TAIL}

# Tail to VSS
N 0 110 0 150 {lab=VSS}

# Bases to Bias Sources
N -250 -30 -250 -30 {lab=b1}
N -250 -30 -130 -30 {lab=b1}
N 250 -30 250 -30 {lab=b2}
N 250 -30 130 -30 {lab=b2}

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
T {Biased at Ic = 1.0 mA per leg, Rc = 1.0 kOhm rppd into VCC=2.5V} -200 -210 0 0 0.3 0.3 {}

# Ports (7 External Interface Pins for LVS)
C {devices/opin.sym} 200 -80 0 0 {name=p1 lab=RAW_NOISE_P}
C {devices/opin.sym} -200 -80 0 0 {name=p2 lab=RAW_NOISE_N}
C {devices/iopin.sym} 0 -180 0 0 {name=p3 lab=VCC}
C {devices/iopin.sym} 0 150 0 0 {name=p4 lab=VSS}
C {devices/ipin.sym} -250 0 0 0 {name=p5 lab=VB1}
C {devices/ipin.sym} 250 0 0 0 {name=p6 lab=VB2}
C {devices/iopin.sym} 0 80 0 0 {name=p7 lab=IE}

# HBT Differential Pair
C {sg13g2_pr/npn13G2.sym} -100 0 0 0 {name=Q1 Nx=1 model=npn13G2 spiceprefix=X}
C {sg13g2_pr/npn13G2.sym} 100 0 0 2 {name=Q2 Nx=1 model=npn13G2 spiceprefix=X}

# Collector Load Resistors (1.0 kOhm rppd, l=3.85u, w=1.0u)
C {sg13g2_pr/rppd.sym} -80 -120 0 0 {name=RC1 value=1.0k w=1.0u l=3.85u model=rppd spiceprefix=X}
C {sg13g2_pr/rppd.sym} 80 -120 0 0 {name=RC2 value=1.0k w=1.0u l=3.85u model=rppd spiceprefix=X}

# Substrate Tap ptap1 (2.0u x 2.0u - Dynamic size evaluation from w and l)
C {sg13g2_pr/ptap1.sym} 0 200 0 0 {name=TAP1 w=2.0u l=2.0u model=ptap1 spiceprefix=X}

# Nets and Wires
N -80 -180 80 -180 {lab=VCC}
N 0 -180 0 -180 {lab=VCC}
N -80 -180 -80 -150 {lab=VCC}
N -80 -90 -80 -30 {lab=RAW_NOISE_N}
N -80 -80 -200 -80 {lab=RAW_NOISE_N}
N 80 -180 80 -150 {lab=VCC}
N 80 -90 80 -30 {lab=RAW_NOISE_P}
N 80 -80 200 -80 {lab=RAW_NOISE_P}

# Emitter Tail (y=30)
N -80 30 80 30 {lab=IE}
N 0 30 0 80 {lab=IE}

# Base Bias Wires
N -250 0 -120 0 {lab=VB1}
N 120 0 250 0 {lab=VB2}

# Substrate VSS Wires:
N -80 0 -80 -10 {lab=VSS}
N 80 0 80 -10 {lab=VSS}
N -80 -10 -150 -10 {lab=VSS}
N 80 -10 -80 -10 {lab=VSS}
N -150 -10 -150 150 {lab=VSS}
N -150 150 0 150 {lab=VSS}
N 0 150 0 170 {lab=VSS}
N 0 230 0 250 {lab=sub!}

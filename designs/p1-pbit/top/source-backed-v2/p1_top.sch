v {xschem version=3.4.8RC file_version=1.2}
G {}
K {type=subcircuit
format="@name @pinlist @symname"
template="name=X1"
}
V {}
S {}
E {}
# Block Instantiations
C {p1_noise_gen.sym} -200 0 0 0 {name=X1}
C {p1_noise_amp.sym} 0 0 0 0 {name=X2}
C {p1_comparator.sym} 200 0 0 0 {name=X3}

# Wires for Internal Differential Pairs
# Generator -> Amp: raw_noise_p, raw_noise_n
N -140 -20 -60 -30 {lab=raw_noise_p}
N -140 0 -60 -10 {lab=raw_noise_n}

# Amp -> Comparator: noise_amp_p, noise_amp_n
N 60 -10 140 -50 {lab=noise_amp_p}
N 60 10 140 -30 {lab=noise_amp_n}

# Top-Level External Port Pins in Declared Order:
# PBIT_OUT PBIT_RAW CLK_OUT_DIV CLK_P CLK_N TRIM_P TRIM_N NOISE_GEN_VCC NOISE_GEN_VSS NOISE_AMP_VCC NOISE_AMP_VSS COMPARATOR_VCC_HBT VDD COMPARATOR_VSS VB1 VB2 IE
C {devices/opin.sym} 300 -10 0 0 {name=p1 lab=PBIT_OUT}
C {devices/opin.sym} 300 10 0 0 {name=p2 lab=PBIT_RAW}
C {devices/opin.sym} 300 30 0 0 {name=p3 lab=CLK_OUT_DIV}
C {devices/ipin.sym} 140 -10 0 0 {name=p4 lab=CLK_P}
C {devices/ipin.sym} 140 10 0 0 {name=p5 lab=CLK_N}
C {devices/ipin.sym} 140 30 0 0 {name=p6 lab=TRIM_P}
C {devices/ipin.sym} 140 50 0 0 {name=p7 lab=TRIM_N}
C {devices/iopin.sym} -140 -40 0 0 {name=p8 lab=NOISE_GEN_VCC}
C {devices/iopin.sym} -140 40 0 0 {name=p9 lab=NOISE_GEN_VSS}
C {devices/iopin.sym} 60 -30 0 0 {name=p10 lab=NOISE_AMP_VCC}
C {devices/iopin.sym} 60 30 0 0 {name=p11 lab=NOISE_AMP_VSS}
C {devices/iopin.sym} 260 -50 0 0 {name=p12 lab=COMPARATOR_VCC_HBT}
C {devices/iopin.sym} 260 -30 0 0 {name=p13 lab=VDD}
C {devices/iopin.sym} 260 50 0 0 {name=p14 lab=COMPARATOR_VSS}
C {devices/ipin.sym} -260 -20 0 0 {name=p15 lab=VB1}
C {devices/ipin.sym} -260 -40 0 0 {name=p16 lab=VB2}
C {devices/iopin.sym} -140 20 0 0 {name=p17 lab=IE}

# Connect Block Supply/Bias Ports to Top Ports


N 260 -10 300 -10 {lab=PBIT_OUT}
N 260 10 300 10 {lab=PBIT_RAW}
N 260 30 300 30 {lab=CLK_OUT_DIV}

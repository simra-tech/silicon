v {xschem version=3.4.8RC file_version=1.2}
G {}
K {type=subcircuit
format="@name @pinlist @symname"
template="name=X1"
}
V {}
S {}
E {}
C {p1_top.sym} 0 0 0 0 {name=X1}
C {devices/opin.sym} 60 -70 0 0 {name=p1 lab=PBIT_OUT}
C {devices/opin.sym} 60 -50 0 0 {name=p2 lab=PBIT_RAW}
C {devices/opin.sym} 60 -30 0 0 {name=p3 lab=CLK_OUT_DIV}
C {devices/ipin.sym} -60 -70 0 0 {name=p4 lab=CLK_P}
C {devices/ipin.sym} -60 -50 0 0 {name=p5 lab=CLK_N}
C {devices/ipin.sym} -60 -30 0 0 {name=p6 lab=TRIM_P}
C {devices/ipin.sym} -60 -10 0 0 {name=p7 lab=TRIM_N}
C {devices/iopin.sym} 60 -10 0 0 {name=p8 lab=NOISE_GEN_VCC}
C {devices/iopin.sym} 60 10 0 0 {name=p9 lab=NOISE_GEN_VSS}
C {devices/iopin.sym} 60 30 0 0 {name=p10 lab=NOISE_AMP_VCC}
C {devices/iopin.sym} 60 50 0 0 {name=p11 lab=NOISE_AMP_VSS}
C {devices/iopin.sym} 60 70 0 0 {name=p12 lab=COMPARATOR_VCC_HBT}
C {devices/iopin.sym} 60 90 0 0 {name=p13 lab=VDD}
C {devices/iopin.sym} 60 110 0 0 {name=p14 lab=COMPARATOR_VSS}
C {devices/ipin.sym} -60 10 0 0 {name=p15 lab=VB1}
C {devices/ipin.sym} -60 30 0 0 {name=p16 lab=VB2}
C {devices/iopin.sym} -60 50 0 0 {name=p17 lab=IE}

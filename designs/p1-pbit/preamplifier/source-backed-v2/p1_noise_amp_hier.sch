v {xschem version=3.4.8RC file_version=1.2}
G {}
K {type=subcircuit
format="@name @pinlist @symname"
template="name=X1"
}
V {}
S {}
E {}
C {p1_noise_amp.sym} 0 0 0 0 {name=X1}
C {devices/opin.sym} 60 -10 0 0 {name=p1 lab=NOISE_AMP_P}
C {devices/opin.sym} 60 10 0 0 {name=p2 lab=NOISE_AMP_N}
C {devices/ipin.sym} -60 -30 0 0 {name=p3 lab=RAW_NOISE_P}
C {devices/ipin.sym} -60 -10 0 0 {name=p4 lab=RAW_NOISE_N}
C {devices/iopin.sym} 60 -30 0 0 {name=p5 lab=VCC}
C {devices/iopin.sym} 60 30 0 0 {name=p6 lab=VSS}

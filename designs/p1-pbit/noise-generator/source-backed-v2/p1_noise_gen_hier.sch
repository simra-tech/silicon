v {xschem version=3.4.8RC file_version=1.2}
G {}
K {type=subcircuit
format="@name @pinlist @symname"
template="name=X1"
}
V {}
S {}
E {}
C {p1_noise_gen.sym} 0 0 0 0 {name=X1}
C {devices/opin.sym} 60 -20 0 0 {name=p1 lab=RAW_NOISE_P}
C {devices/opin.sym} 60 0 0 0 {name=p2 lab=RAW_NOISE_N}
C {devices/iopin.sym} 60 -40 0 0 {name=p3 lab=VCC}
C {devices/iopin.sym} 60 40 0 0 {name=p4 lab=VSS}
C {devices/ipin.sym} -60 -20 0 0 {name=p5 lab=VB1}
C {devices/ipin.sym} -60 -40 0 0 {name=p6 lab=VB2}
C {devices/iopin.sym} 60 20 0 0 {name=p7 lab=IE}

v {xschem version=3.4.8RC file_version=1.2}
G {}
K {type=subcircuit
format="@name @pinlist @symname"
template="name=X1"
}
V {}
S {}
E {}
C {p1_comparator.sym} 0 0 0 0 {name=X1}
C {devices/opin.sym} 60 -10 0 0 {name=p1 lab=PBIT_OUT}
C {devices/opin.sym} 60 10 0 0 {name=p2 lab=PBIT_RAW}
C {devices/opin.sym} 60 30 0 0 {name=p3 lab=CLK_OUT_DIV}
C {devices/ipin.sym} -60 -50 0 0 {name=p4 lab=IN_P}
C {devices/ipin.sym} -60 -30 0 0 {name=p5 lab=IN_N}
C {devices/ipin.sym} -60 -10 0 0 {name=p6 lab=CLK_P}
C {devices/ipin.sym} -60 10 0 0 {name=p7 lab=CLK_N}
C {devices/ipin.sym} -60 30 0 0 {name=p11 lab=TRIM_P}
C {devices/ipin.sym} -60 50 0 0 {name=p12 lab=TRIM_N}
C {devices/iopin.sym} 60 -50 0 0 {name=p8 lab=VCC_HBT}
C {devices/iopin.sym} 60 -30 0 0 {name=p9 lab=VDD}
C {devices/iopin.sym} 60 50 0 0 {name=p10 lab=VSS}

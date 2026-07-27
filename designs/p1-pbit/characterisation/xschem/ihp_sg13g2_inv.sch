v {xschem version=3.4.8RC file_version=1.2}
G {}
K {type=subcircuit
format="@spiceprefix@name @pinlist @symname"
template="name=X1"
}
V {}
S {}
E {}
N 20 -40 20 0 {lab=out}
N 20 -20 150 -20 {lab=out}
N -310 -20 -20 -20 {lab=in}
N -20 -70 -20 30 {lab=in}
N 20 -170 20 -100 {lab=vdd}
N 20 -100 20 -70 {lab=vdd}
N 20 30 20 60 {lab=vss}
N 20 60 20 120 {lab=vss}
C {devices/ipin.sym} -310 -20 0 0 {name=p1 lab=in}
C {devices/opin.sym} 150 -20 0 0 {name=p2 lab=out}
C {devices/iopin.sym} 20 -170 0 0 {name=p3 lab=vdd}
C {devices/iopin.sym} 20 120 0 0 {name=p4 lab=vss}
C {sg13g2_pr/sg13_lv_pmos.sym} 0 -70 0 0 {name=M2
l=0.13u
w=1.414u
ng=1
m=1
model=sg13_lv_pmos
spiceprefix=X
}
C {sg13g2_pr/sg13_lv_nmos.sym} 0 30 0 0 {name=M1
l=0.13u
w=1.0u
ng=1
m=1
model=sg13_lv_nmos
spiceprefix=X
}

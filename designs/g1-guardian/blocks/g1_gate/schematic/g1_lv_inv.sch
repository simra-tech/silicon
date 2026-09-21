v {xschem version=3.4.8RC file_version=1.3}
G {}
K {}
V {}
S {}
E {}
T {g1_lv_inv: LV inverter} 0 -40 0 0 0.4 0.4 {}
C {sg13g2_pr/sg13_lv_pmos.sym} 100 -200 0 0 {name=MP model=sg13_lv_pmos w=2u l=0.13u ng=1 m=1}
C {devices/lab_pin.sym} 120 -170 0 0 {name=l1 lab=y}
C {devices/lab_pin.sym} 80 -200 0 0 {name=l2 lab=a}
C {devices/lab_pin.sym} 120 -230 0 0 {name=l3 lab=vdd}
C {devices/lab_pin.sym} 120 -200 0 0 {name=l4 lab=vdd}
C {sg13g2_pr/sg13_lv_nmos.sym} 100 -100 0 0 {name=MN model=sg13_lv_nmos w=1u l=0.13u ng=1 m=1}
C {devices/lab_pin.sym} 120 -130 0 0 {name=l5 lab=y}
C {devices/lab_pin.sym} 80 -100 0 0 {name=l6 lab=a}
C {devices/lab_pin.sym} 120 -70 0 0 {name=l7 lab=vss}
C {devices/lab_pin.sym} 120 -100 0 0 {name=l8 lab=vss}
C {devices/ipin.sym} 300 -200 0 0 {name=pi0 lab=a}
C {devices/opin.sym} 300 -180 0 0 {name=po0 lab=y}
C {devices/iopin.sym} 300 -160 0 0 {name=pb0 lab=vdd}
C {devices/iopin.sym} 300 -140 0 0 {name=pb1 lab=vss}

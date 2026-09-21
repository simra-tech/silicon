v {xschem version=3.4.8RC file_version=1.3}
G {}
K {}
V {}
S {}
E {}
T {g1_lvldn: 3.3 V a/ab -> 1.2 V y (= a level); hv NMOS pull-downs, cross-coupled lv PMOS} 0 -40 0 0 0.4 0.4 {}
C {sg13g2_pr/sg13_hv_nmos.sym} 100 -200 0 0 {name=MN1 model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {devices/lab_pin.sym} 120 -230 0 0 {name=l1 lab=yb}
C {devices/lab_pin.sym} 80 -200 0 0 {name=l2 lab=a}
C {devices/lab_pin.sym} 120 -170 0 0 {name=l3 lab=vss}
C {devices/lab_pin.sym} 120 -200 0 0 {name=l4 lab=vss}
C {sg13g2_pr/sg13_hv_nmos.sym} 200 -200 0 0 {name=MN2 model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {devices/lab_pin.sym} 220 -230 0 0 {name=l5 lab=y}
C {devices/lab_pin.sym} 180 -200 0 0 {name=l6 lab=ab}
C {devices/lab_pin.sym} 220 -170 0 0 {name=l7 lab=vss}
C {devices/lab_pin.sym} 220 -200 0 0 {name=l8 lab=vss}
C {sg13g2_pr/sg13_lv_pmos.sym} 100 -300 0 0 {name=MP1 model=sg13_lv_pmos w=1u l=0.13u ng=1 m=1}
C {devices/lab_pin.sym} 120 -270 0 0 {name=l9 lab=y}
C {devices/lab_pin.sym} 80 -300 0 0 {name=l10 lab=yb}
C {devices/lab_pin.sym} 120 -330 0 0 {name=l11 lab=vdd}
C {devices/lab_pin.sym} 120 -300 0 0 {name=l12 lab=vdd}
C {sg13g2_pr/sg13_lv_pmos.sym} 200 -300 0 0 {name=MP2 model=sg13_lv_pmos w=1u l=0.13u ng=1 m=1}
C {devices/lab_pin.sym} 220 -270 0 0 {name=l13 lab=yb}
C {devices/lab_pin.sym} 180 -300 0 0 {name=l14 lab=y}
C {devices/lab_pin.sym} 220 -330 0 0 {name=l15 lab=vdd}
C {devices/lab_pin.sym} 220 -300 0 0 {name=l16 lab=vdd}
C {devices/ipin.sym} 400 -300 0 0 {name=pi0 lab=a}
C {devices/ipin.sym} 400 -280 0 0 {name=pi1 lab=ab}
C {devices/opin.sym} 400 -260 0 0 {name=po0 lab=y}
C {devices/iopin.sym} 400 -240 0 0 {name=pb0 lab=vdd}
C {devices/iopin.sym} 400 -220 0 0 {name=pb1 lab=vss}

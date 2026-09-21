v {xschem version=3.4.8RC file_version=1.3}
G {}
K {}
V {}
S {}
E {}
T {g1_osc_nand2: LV 2-input NAND} 0 -40 0 0 0.4 0.4 {}
C {sg13g2_pr/sg13_lv_pmos.sym} 100 -300 0 0 {name=MP0 model=sg13_lv_pmos w=1u l=0.13u ng=1 m=1}
C {devices/lab_pin.sym} 120 -270 0 0 {name=l1 lab=y}
C {devices/lab_pin.sym} 80 -300 0 0 {name=l2 lab=a0}
C {devices/lab_pin.sym} 120 -330 0 0 {name=l3 lab=vdd}
C {devices/lab_pin.sym} 120 -300 0 0 {name=l4 lab=vdd}
C {sg13g2_pr/sg13_lv_pmos.sym} 200 -300 0 0 {name=MP1 model=sg13_lv_pmos w=1u l=0.13u ng=1 m=1}
C {devices/lab_pin.sym} 220 -270 0 0 {name=l5 lab=y}
C {devices/lab_pin.sym} 180 -300 0 0 {name=l6 lab=a1}
C {devices/lab_pin.sym} 220 -330 0 0 {name=l7 lab=vdd}
C {devices/lab_pin.sym} 220 -300 0 0 {name=l8 lab=vdd}
C {sg13g2_pr/sg13_lv_nmos.sym} 100 -100 0 0 {name=MN0 model=sg13_lv_nmos w=1u l=0.13u ng=1 m=1}
C {devices/lab_pin.sym} 120 -130 0 0 {name=l9 lab=y}
C {devices/lab_pin.sym} 80 -100 0 0 {name=l10 lab=a0}
C {devices/lab_pin.sym} 120 -70 0 0 {name=l11 lab=n0}
C {devices/lab_pin.sym} 120 -100 0 0 {name=l12 lab=vss}
C {sg13g2_pr/sg13_lv_nmos.sym} 200 -100 0 0 {name=MN1 model=sg13_lv_nmos w=1u l=0.13u ng=1 m=1}
C {devices/lab_pin.sym} 220 -130 0 0 {name=l13 lab=n0}
C {devices/lab_pin.sym} 180 -100 0 0 {name=l14 lab=a1}
C {devices/lab_pin.sym} 220 -70 0 0 {name=l15 lab=vss}
C {devices/lab_pin.sym} 220 -100 0 0 {name=l16 lab=vss}
C {devices/ipin.sym} 400 -300 0 0 {name=pi0 lab=a0}
C {devices/ipin.sym} 400 -280 0 0 {name=pi1 lab=a1}
C {devices/opin.sym} 400 -260 0 0 {name=po0 lab=y}
C {devices/iopin.sym} 400 -240 0 0 {name=pb0 lab=vdd}
C {devices/iopin.sym} 400 -220 0 0 {name=pb1 lab=vss}

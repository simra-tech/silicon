v {xschem version=3.4.8RC file_version=1.3}
G {}
K {}
V {}
S {}
E {}
T {g1_osc_nor3: LV 3-input NOR} 0 -40 0 0 0.4 0.4 {}
C {sg13g2_pr/sg13_lv_pmos.sym} 100 -300 0 0 {name=MP0 model=sg13_lv_pmos w=3u l=0.13u ng=1 m=1}
C {devices/lab_pin.sym} 120 -270 0 0 {name=l1 lab=p0}
C {devices/lab_pin.sym} 80 -300 0 0 {name=l2 lab=a0}
C {devices/lab_pin.sym} 120 -330 0 0 {name=l3 lab=vdd}
C {devices/lab_pin.sym} 120 -300 0 0 {name=l4 lab=vdd}
C {sg13g2_pr/sg13_lv_pmos.sym} 200 -300 0 0 {name=MP1 model=sg13_lv_pmos w=3u l=0.13u ng=1 m=1}
C {devices/lab_pin.sym} 220 -270 0 0 {name=l5 lab=p1}
C {devices/lab_pin.sym} 180 -300 0 0 {name=l6 lab=a1}
C {devices/lab_pin.sym} 220 -330 0 0 {name=l7 lab=p0}
C {devices/lab_pin.sym} 220 -300 0 0 {name=l8 lab=vdd}
C {sg13g2_pr/sg13_lv_pmos.sym} 300 -300 0 0 {name=MP2 model=sg13_lv_pmos w=3u l=0.13u ng=1 m=1}
C {devices/lab_pin.sym} 320 -270 0 0 {name=l9 lab=y}
C {devices/lab_pin.sym} 280 -300 0 0 {name=l10 lab=a2}
C {devices/lab_pin.sym} 320 -330 0 0 {name=l11 lab=p1}
C {devices/lab_pin.sym} 320 -300 0 0 {name=l12 lab=vdd}
C {sg13g2_pr/sg13_lv_nmos.sym} 100 -100 0 0 {name=MN0 model=sg13_lv_nmos w=0.5u l=0.13u ng=1 m=1}
C {devices/lab_pin.sym} 120 -130 0 0 {name=l13 lab=y}
C {devices/lab_pin.sym} 80 -100 0 0 {name=l14 lab=a0}
C {devices/lab_pin.sym} 120 -70 0 0 {name=l15 lab=vss}
C {devices/lab_pin.sym} 120 -100 0 0 {name=l16 lab=vss}
C {sg13g2_pr/sg13_lv_nmos.sym} 200 -100 0 0 {name=MN1 model=sg13_lv_nmos w=0.5u l=0.13u ng=1 m=1}
C {devices/lab_pin.sym} 220 -130 0 0 {name=l17 lab=y}
C {devices/lab_pin.sym} 180 -100 0 0 {name=l18 lab=a1}
C {devices/lab_pin.sym} 220 -70 0 0 {name=l19 lab=vss}
C {devices/lab_pin.sym} 220 -100 0 0 {name=l20 lab=vss}
C {sg13g2_pr/sg13_lv_nmos.sym} 300 -100 0 0 {name=MN2 model=sg13_lv_nmos w=0.5u l=0.13u ng=1 m=1}
C {devices/lab_pin.sym} 320 -130 0 0 {name=l21 lab=y}
C {devices/lab_pin.sym} 280 -100 0 0 {name=l22 lab=a2}
C {devices/lab_pin.sym} 320 -70 0 0 {name=l23 lab=vss}
C {devices/lab_pin.sym} 320 -100 0 0 {name=l24 lab=vss}
C {devices/ipin.sym} 600 -300 0 0 {name=pi0 lab=a0}
C {devices/ipin.sym} 600 -280 0 0 {name=pi1 lab=a1}
C {devices/ipin.sym} 600 -260 0 0 {name=pi2 lab=a2}
C {devices/opin.sym} 600 -240 0 0 {name=po0 lab=y}
C {devices/iopin.sym} 600 -220 0 0 {name=pb0 lab=vdd}
C {devices/iopin.sym} 600 -200 0 0 {name=pb1 lab=vss}

v {xschem version=3.4.8RC file_version=1.3}
G {}
K {}
V {}
S {}
E {}
T {g1_hv_nor2: 3.3 V NOR2} 0 -40 0 0 0.4 0.4 {}
C {sg13g2_pr/sg13_hv_pmos.sym} 100 -400 0 0 {name=MP1 model=sg13_hv_pmos w=7.8u l=0.45u ng=1 m=1}
C {devices/lab_pin.sym} 120 -370 0 0 {name=l1 lab=m}
C {devices/lab_pin.sym} 80 -400 0 0 {name=l2 lab=a}
C {devices/lab_pin.sym} 120 -430 0 0 {name=l3 lab=vdda}
C {devices/lab_pin.sym} 120 -400 0 0 {name=l4 lab=vdda}
C {sg13g2_pr/sg13_hv_pmos.sym} 100 -300 0 0 {name=MP2 model=sg13_hv_pmos w=7.8u l=0.45u ng=1 m=1}
C {devices/lab_pin.sym} 120 -270 0 0 {name=l5 lab=y}
C {devices/lab_pin.sym} 80 -300 0 0 {name=l6 lab=b}
C {devices/lab_pin.sym} 120 -330 0 0 {name=l7 lab=m}
C {devices/lab_pin.sym} 120 -300 0 0 {name=l8 lab=vdda}
C {sg13g2_pr/sg13_hv_nmos.sym} 100 -200 0 0 {name=MN1 model=sg13_hv_nmos w=1.9u l=0.45u ng=1 m=1}
C {devices/lab_pin.sym} 120 -230 0 0 {name=l9 lab=y}
C {devices/lab_pin.sym} 80 -200 0 0 {name=l10 lab=a}
C {devices/lab_pin.sym} 120 -170 0 0 {name=l11 lab=vss}
C {devices/lab_pin.sym} 120 -200 0 0 {name=l12 lab=vss}
C {sg13g2_pr/sg13_hv_nmos.sym} 200 -200 0 0 {name=MN2 model=sg13_hv_nmos w=1.9u l=0.45u ng=1 m=1}
C {devices/lab_pin.sym} 220 -230 0 0 {name=l13 lab=y}
C {devices/lab_pin.sym} 180 -200 0 0 {name=l14 lab=b}
C {devices/lab_pin.sym} 220 -170 0 0 {name=l15 lab=vss}
C {devices/lab_pin.sym} 220 -200 0 0 {name=l16 lab=vss}
C {devices/ipin.sym} 400 -400 0 0 {name=pi0 lab=a}
C {devices/ipin.sym} 400 -380 0 0 {name=pi1 lab=b}
C {devices/opin.sym} 400 -360 0 0 {name=po0 lab=y}
C {devices/iopin.sym} 400 -340 0 0 {name=pb0 lab=vdda}
C {devices/iopin.sym} 400 -320 0 0 {name=pb1 lab=vss}

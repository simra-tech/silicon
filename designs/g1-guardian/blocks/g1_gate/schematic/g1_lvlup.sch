v {xschem version=3.4.8RC file_version=1.3}
G {}
K {}
V {}
S {}
E {}
T {g1_lvlup: 1.2 V in -> 3.3 V out (y = a level); cross-coupled hv PMOS pair} 0 -40 0 0 0.4 0.4 {}
C {g1_lv_inv.sym} 100 -300 0 0 {name=XI }
C {devices/lab_pin.sym} 40 -330 0 0 {name=l1 lab=a}
C {devices/lab_pin.sym} 40 -310 0 0 {name=l2 lab=ab}
C {devices/lab_pin.sym} 40 -290 0 0 {name=l3 lab=vdd}
C {devices/lab_pin.sym} 40 -270 0 0 {name=l4 lab=vss}
C {sg13g2_pr/sg13_hv_nmos.sym} 300 -200 0 0 {name=MN1 model=sg13_hv_nmos w=1.9u l=0.45u ng=1 m=1}
C {devices/lab_pin.sym} 320 -230 0 0 {name=l5 lab=nb}
C {devices/lab_pin.sym} 280 -200 0 0 {name=l6 lab=a}
C {devices/lab_pin.sym} 320 -170 0 0 {name=l7 lab=vss}
C {devices/lab_pin.sym} 320 -200 0 0 {name=l8 lab=vss}
C {sg13g2_pr/sg13_hv_nmos.sym} 400 -200 0 0 {name=MN2 model=sg13_hv_nmos w=1.9u l=0.45u ng=1 m=1}
C {devices/lab_pin.sym} 420 -230 0 0 {name=l9 lab=n}
C {devices/lab_pin.sym} 380 -200 0 0 {name=l10 lab=ab}
C {devices/lab_pin.sym} 420 -170 0 0 {name=l11 lab=vss}
C {devices/lab_pin.sym} 420 -200 0 0 {name=l12 lab=vss}
C {sg13g2_pr/sg13_hv_pmos.sym} 300 -300 0 0 {name=MP1 model=sg13_hv_pmos w=0.3u l=0.45u ng=1 m=1}
C {devices/lab_pin.sym} 320 -270 0 0 {name=l13 lab=nb}
C {devices/lab_pin.sym} 280 -300 0 0 {name=l14 lab=n}
C {devices/lab_pin.sym} 320 -330 0 0 {name=l15 lab=vdda}
C {devices/lab_pin.sym} 320 -300 0 0 {name=l16 lab=vdda}
C {sg13g2_pr/sg13_hv_pmos.sym} 400 -300 0 0 {name=MP2 model=sg13_hv_pmos w=0.3u l=0.45u ng=1 m=1}
C {devices/lab_pin.sym} 420 -270 0 0 {name=l17 lab=n}
C {devices/lab_pin.sym} 380 -300 0 0 {name=l18 lab=nb}
C {devices/lab_pin.sym} 420 -330 0 0 {name=l19 lab=vdda}
C {devices/lab_pin.sym} 420 -300 0 0 {name=l20 lab=vdda}
C {g1_hv_inv.sym} 600 -300 0 0 {name=XO }
C {devices/lab_pin.sym} 540 -330 0 0 {name=l21 lab=nb}
C {devices/lab_pin.sym} 540 -310 0 0 {name=l22 lab=y}
C {devices/lab_pin.sym} 540 -290 0 0 {name=l23 lab=vdda}
C {devices/lab_pin.sym} 540 -270 0 0 {name=l24 lab=vss}
C {devices/ipin.sym} 800 -300 0 0 {name=pi0 lab=a}
C {devices/opin.sym} 800 -280 0 0 {name=po0 lab=y}
C {devices/iopin.sym} 800 -260 0 0 {name=pb0 lab=vdd}
C {devices/iopin.sym} 800 -240 0 0 {name=pb1 lab=vdda}
C {devices/iopin.sym} 800 -220 0 0 {name=pb2 lab=vss}

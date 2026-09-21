v {xschem version=3.4.8RC file_version=1.3}
G {}
K {}
V {}
S {}
E {}
T {g1_osc_cmp: 5-T comparator, out=1 when inp>inn; vbn = tail mirror gate (about 20 uA)} 0 -40 0 0 0.4 0.4 {}
C {sg13g2_pr/sg13_lv_nmos.sym} 300 -100 0 0 {name=MT model=sg13_lv_nmos w=2u l=0.5u ng=1 m=1}
C {devices/lab_pin.sym} 320 -130 0 0 {name=l1 lab=tail}
C {devices/lab_pin.sym} 280 -100 0 0 {name=l2 lab=vbn}
C {devices/lab_pin.sym} 320 -70 0 0 {name=l3 lab=vss}
C {devices/lab_pin.sym} 320 -100 0 0 {name=l4 lab=vss}
C {sg13g2_pr/sg13_lv_nmos.sym} 200 -200 0 0 {name=M1 model=sg13_lv_nmos w=4u l=0.3u ng=1 m=1}
C {devices/lab_pin.sym} 220 -230 0 0 {name=l5 lab=d1}
C {devices/lab_pin.sym} 180 -200 0 0 {name=l6 lab=inp}
C {devices/lab_pin.sym} 220 -170 0 0 {name=l7 lab=tail}
C {devices/lab_pin.sym} 220 -200 0 0 {name=l8 lab=vss}
C {sg13g2_pr/sg13_lv_nmos.sym} 400 -200 0 0 {name=M2 model=sg13_lv_nmos w=4u l=0.3u ng=1 m=1}
C {devices/lab_pin.sym} 420 -230 0 0 {name=l9 lab=o1}
C {devices/lab_pin.sym} 380 -200 0 0 {name=l10 lab=inn}
C {devices/lab_pin.sym} 420 -170 0 0 {name=l11 lab=tail}
C {devices/lab_pin.sym} 420 -200 0 0 {name=l12 lab=vss}
C {sg13g2_pr/sg13_lv_pmos.sym} 200 -350 0 0 {name=M3 model=sg13_lv_pmos w=2u l=0.3u ng=1 m=1}
C {devices/lab_pin.sym} 220 -320 0 0 {name=l13 lab=d1}
C {devices/lab_pin.sym} 180 -350 0 0 {name=l14 lab=d1}
C {devices/lab_pin.sym} 220 -380 0 0 {name=l15 lab=vdd}
C {devices/lab_pin.sym} 220 -350 0 0 {name=l16 lab=vdd}
C {sg13g2_pr/sg13_lv_pmos.sym} 400 -350 0 0 {name=M4 model=sg13_lv_pmos w=2u l=0.3u ng=1 m=1}
C {devices/lab_pin.sym} 420 -320 0 0 {name=l17 lab=o1}
C {devices/lab_pin.sym} 380 -350 0 0 {name=l18 lab=d1}
C {devices/lab_pin.sym} 420 -380 0 0 {name=l19 lab=vdd}
C {devices/lab_pin.sym} 420 -350 0 0 {name=l20 lab=vdd}
C {g1_osc_inv.sym} 650 -250 0 0 {name=XI1 }
C {devices/lab_pin.sym} 590 -280 0 0 {name=l21 lab=o1}
C {devices/lab_pin.sym} 590 -260 0 0 {name=l22 lab=o2}
C {devices/lab_pin.sym} 590 -240 0 0 {name=l23 lab=vdd}
C {devices/lab_pin.sym} 590 -220 0 0 {name=l24 lab=vss}
C {g1_osc_inv.sym} 850 -250 0 0 {name=XI2 }
C {devices/lab_pin.sym} 790 -280 0 0 {name=l25 lab=o2}
C {devices/lab_pin.sym} 790 -260 0 0 {name=l26 lab=out}
C {devices/lab_pin.sym} 790 -240 0 0 {name=l27 lab=vdd}
C {devices/lab_pin.sym} 790 -220 0 0 {name=l28 lab=vss}
C {devices/ipin.sym} 1100 -350 0 0 {name=pi0 lab=inp}
C {devices/ipin.sym} 1100 -330 0 0 {name=pi1 lab=inn}
C {devices/ipin.sym} 1100 -310 0 0 {name=pi2 lab=vbn}
C {devices/opin.sym} 1100 -290 0 0 {name=po0 lab=out}
C {devices/iopin.sym} 1100 -270 0 0 {name=pb0 lab=vdd}
C {devices/iopin.sym} 1100 -250 0 0 {name=pb1 lab=vss}

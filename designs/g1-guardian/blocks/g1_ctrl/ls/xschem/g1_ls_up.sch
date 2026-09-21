v {xschem version=3.4.8RC file_version=1.3}
G {}
K {}
V {}
S {}
E {}
T {g1_ls_up: 1.2 V in -> 3.3 V out (out = in level); LV inverter, hv NMOS pull-downs, cross-coupled hv PMOS keeper, hv output inverter} 0 -40 0 0 0.4 0.4 {}
C {sg13g2_pr/sg13_lv_pmos.sym} 100 -300 0 0 {name=MPI model=sg13_lv_pmos w=2u l=0.13u ng=1 m=1}
C {devices/lab_pin.sym} 120 -270 0 0 {name=l1 lab=inb}
C {devices/lab_pin.sym} 80 -300 0 0 {name=l2 lab=in}
C {devices/lab_pin.sym} 120 -330 0 0 {name=l3 lab=vdd}
C {devices/lab_pin.sym} 120 -300 0 0 {name=l4 lab=vdd}
C {sg13g2_pr/sg13_lv_nmos.sym} 100 -200 0 0 {name=MNI model=sg13_lv_nmos w=1u l=0.13u ng=1 m=1}
C {devices/lab_pin.sym} 120 -230 0 0 {name=l5 lab=inb}
C {devices/lab_pin.sym} 80 -200 0 0 {name=l6 lab=in}
C {devices/lab_pin.sym} 120 -170 0 0 {name=l7 lab=vss}
C {devices/lab_pin.sym} 120 -200 0 0 {name=l8 lab=vss}
C {sg13g2_pr/sg13_hv_nmos.sym} 300 -200 0 0 {name=MN1 model=sg13_hv_nmos w=3.8u l=0.45u ng=1 m=1}
C {devices/lab_pin.sym} 320 -230 0 0 {name=l9 lab=nb}
C {devices/lab_pin.sym} 280 -200 0 0 {name=l10 lab=in}
C {devices/lab_pin.sym} 320 -170 0 0 {name=l11 lab=vss}
C {devices/lab_pin.sym} 320 -200 0 0 {name=l12 lab=vss}
C {sg13g2_pr/sg13_hv_nmos.sym} 400 -200 0 0 {name=MN2 model=sg13_hv_nmos w=3.8u l=0.45u ng=1 m=1}
C {devices/lab_pin.sym} 420 -230 0 0 {name=l13 lab=n}
C {devices/lab_pin.sym} 380 -200 0 0 {name=l14 lab=inb}
C {devices/lab_pin.sym} 420 -170 0 0 {name=l15 lab=vss}
C {devices/lab_pin.sym} 420 -200 0 0 {name=l16 lab=vss}
C {sg13g2_pr/sg13_hv_pmos.sym} 300 -300 0 0 {name=MP1 model=sg13_hv_pmos w=0.3u l=0.45u ng=1 m=1}
C {devices/lab_pin.sym} 320 -270 0 0 {name=l17 lab=nb}
C {devices/lab_pin.sym} 280 -300 0 0 {name=l18 lab=n}
C {devices/lab_pin.sym} 320 -330 0 0 {name=l19 lab=vdda}
C {devices/lab_pin.sym} 320 -300 0 0 {name=l20 lab=vdda}
C {sg13g2_pr/sg13_hv_pmos.sym} 400 -300 0 0 {name=MP2 model=sg13_hv_pmos w=0.3u l=0.45u ng=1 m=1}
C {devices/lab_pin.sym} 420 -270 0 0 {name=l21 lab=n}
C {devices/lab_pin.sym} 380 -300 0 0 {name=l22 lab=nb}
C {devices/lab_pin.sym} 420 -330 0 0 {name=l23 lab=vdda}
C {devices/lab_pin.sym} 420 -300 0 0 {name=l24 lab=vdda}
C {sg13g2_pr/sg13_hv_pmos.sym} 600 -300 0 0 {name=MPO model=sg13_hv_pmos w=3.9u l=0.45u ng=1 m=1}
C {devices/lab_pin.sym} 620 -270 0 0 {name=l25 lab=out}
C {devices/lab_pin.sym} 580 -300 0 0 {name=l26 lab=nb}
C {devices/lab_pin.sym} 620 -330 0 0 {name=l27 lab=vdda}
C {devices/lab_pin.sym} 620 -300 0 0 {name=l28 lab=vdda}
C {sg13g2_pr/sg13_hv_nmos.sym} 600 -200 0 0 {name=MNO model=sg13_hv_nmos w=1.9u l=0.45u ng=1 m=1}
C {devices/lab_pin.sym} 620 -230 0 0 {name=l29 lab=out}
C {devices/lab_pin.sym} 580 -200 0 0 {name=l30 lab=nb}
C {devices/lab_pin.sym} 620 -170 0 0 {name=l31 lab=vss}
C {devices/lab_pin.sym} 620 -200 0 0 {name=l32 lab=vss}
C {devices/ipin.sym} 800 -300 0 0 {name=pi0 lab=in}
C {devices/opin.sym} 800 -280 0 0 {name=po0 lab=out}
C {devices/iopin.sym} 800 -260 0 0 {name=pb0 lab=vdd}
C {devices/iopin.sym} 800 -240 0 0 {name=pb1 lab=vdda}
C {devices/iopin.sym} 800 -220 0 0 {name=pb2 lab=vss}
T {in=1: MN1 pulls nb low, MP2 pulls n to vdda, MPO drives out high. No DC path in either state.} 100 -420 0 0 0.3 0.3 {}

v {xschem version=3.4.8RC file_version=1.3}
G {}
K {}
V {}
S {}
E {}
T {g1_thv_inv: 3.3 V inverter (DAC switch drive)} 0 -40 0 0 0.4 0.4 {}
C {sg13g2_pr/sg13_hv_pmos.sym} 100 -200 0 0 {name=MP model=sg13_hv_pmos w=3.9u l=0.45u ng=1 m=1}
C {devices/lab_pin.sym} 120 -170 0 0 {name=l1 lab=y}
C {devices/lab_pin.sym} 80 -200 0 0 {name=l2 lab=a}
C {devices/lab_pin.sym} 120 -230 0 0 {name=l3 lab=vdda}
C {devices/lab_pin.sym} 120 -200 0 0 {name=l4 lab=vdda}
C {sg13g2_pr/sg13_hv_nmos.sym} 100 -100 0 0 {name=MN model=sg13_hv_nmos w=1.9u l=0.45u ng=1 m=1}
C {devices/lab_pin.sym} 120 -130 0 0 {name=l5 lab=y}
C {devices/lab_pin.sym} 80 -100 0 0 {name=l6 lab=a}
C {devices/lab_pin.sym} 120 -70 0 0 {name=l7 lab=vss}
C {devices/lab_pin.sym} 120 -100 0 0 {name=l8 lab=vss}
C {devices/ipin.sym} 300 -200 0 0 {name=pi0 lab=a}
C {devices/opin.sym} 300 -180 0 0 {name=po0 lab=y}
C {devices/iopin.sym} 300 -160 0 0 {name=pb0 lab=vdda}
C {devices/iopin.sym} 300 -140 0 0 {name=pb1 lab=vss}

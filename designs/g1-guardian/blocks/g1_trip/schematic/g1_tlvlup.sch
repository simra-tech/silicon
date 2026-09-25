v {xschem version=3.4.8RC file_version=1.3}
G {}
K {}
V {}
S {}
E {}
B 4 100 -620 2213 -468 {fill=false}
T {DAC code bit: 1.2 V a -> 3.3 V y (= a) and yb for the thick-oxide switch gates. Structure of sg13g2_LevelUp.} 300 0 0 0 0.3 0.3 {}
T {g1_tlvlup - 1.2 V code bit to 3.3 V y / yb} 112 -610 0 0 0.55 0.55 {}
T {G1 guardian, chip of record g1_chip_top_1414_r2.gds 9049e87b (r2 2026-09-25; geometry XOR-identical to r1 629d303a); block map: g1_padring/reports/signoff-1414-20260924} 112 -571 0 0 0.3 0.3 {}
T {On-chip variant: chip of record (regenpair4 + NF4): soft g1_cmp M1/M2 24u/0.68u ng=4, hard g1_cmp_regenpair4 M3/M4 6u/0.26u; rppd bodies on vss as in the chip deck; layout/g1_trip_lvs.cdl 60a9ad6e + regenpair4/NF4 cell CDLs} 112 -547 0 0 0.3 0.3 {}
T {Netlist-equivalent to the g1_tlvlup subcircuit in sim/qualification/joint586-softinputpair4-nf4-roomcal-s73133-20260924-r1/trip.spice sha256 f5f0a90a (chip deck)} 112 -523 0 0 0.3 0.3 {}
T {Drawn 2026-09-25 by the block generator; device sizes (w, l, ng, m) are on each symbol. Proof: review/schematics-readability-20260925} 112 -499 0 0 0.25 0.25 {}
C {g1_inv.sym} 200 -225 0 0 {name=XI }
C {sg13g2_pr/sg13_hv_nmos.sym} 440 -150 0 0 {name=MN1 model=sg13_hv_nmos w=1.9u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 640 -150 0 0 {name=MN2 model=sg13_hv_nmos w=1.9u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_pmos.sym} 440 -300 0 0 {name=MP1 model=sg13_hv_pmos w=0.3u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_pmos.sym} 640 -300 0 0 {name=MP2 model=sg13_hv_pmos w=0.3u l=0.45u ng=1 m=1}
C {g1_thv_inv.sym} 900 -225 0 0 {name=XO }
C {g1_thv_inv.sym} 1100 -225 0 0 {name=XOB }
C {devices/ipin.sym} 60 -225 0 0 {name=p0 lab=a}
C {devices/opin.sym} 1300 -140 0 0 {name=p1 lab=y}
C {devices/opin.sym} 1300 -225 0 0 {name=p2 lab=yb}
C {devices/iopin.sym} 60 20 0 0 {name=p3 lab=vdd}
C {devices/iopin.sym} 60 50 0 0 {name=p4 lab=vdda}
C {devices/iopin.sym} 60 80 0 0 {name=p5 lab=vss}
C {devices/lab_wire.sym} 300 -225 0 0 {name=l1 lab=ab}
C {devices/lab_pin.sym} 580 -150 0 0 {name=l2 lab=ab}
C {devices/lab_pin.sym} 460 -225 0 0 {name=l3 lab=nb}
C {devices/lab_pin.sym} 660 -225 0 1 {name=l4 lab=n}
C {devices/lab_pin.sym} 800 -225 0 0 {name=l5 lab=nb}
C {devices/lab_wire.sym} 1030 -225 0 0 {name=l6 lab=y}
C {devices/lab_pin.sym} 200 -295 0 1 {name=l7 lab=vdd}
C {devices/lab_pin.sym} 200 -155 0 1 {name=l8 lab=vss}
C {devices/lab_pin.sym} 900 -295 0 1 {name=l9 lab=vdda}
C {devices/lab_pin.sym} 900 -155 0 1 {name=l10 lab=vss}
C {devices/lab_pin.sym} 1100 -295 0 1 {name=l11 lab=vdda}
C {devices/lab_pin.sym} 1100 -155 0 1 {name=l12 lab=vss}
C {devices/lab_pin.sym} 460 -380 0 0 {name=l13 lab=vdda}
C {devices/lab_pin.sym} 460 -70 0 0 {name=l14 lab=vss}
N 460 -150 460 -120 {}
N 660 -150 660 -120 {}
N 460 -300 460 -330 {}
N 660 -300 660 -330 {}
N 60 -225 140 -225 {}
N 110 -225 110 -100 {}
N 110 -100 400 -100 {}
N 400 -100 400 -150 {}
N 400 -150 420 -150 {}
N 260 -225 300 -225 {}
N 620 -150 580 -150 {}
N 460 -270 460 -180 {}
N 660 -270 660 -180 {}
N 460 -245 590 -245 {}
N 590 -245 590 -300 {}
N 590 -300 620 -300 {}
N 660 -205 400 -205 {}
N 400 -205 400 -300 {}
N 400 -300 420 -300 {}
N 840 -225 800 -225 {}
N 960 -225 1040 -225 {}
N 1000 -225 1000 -140 {}
N 1000 -140 1300 -140 {}
N 1160 -225 1300 -225 {}
N 200 -275 200 -295 {}
N 200 -175 200 -155 {}
N 900 -275 900 -295 {}
N 900 -175 900 -155 {}
N 1100 -275 1100 -295 {}
N 1100 -175 1100 -155 {}
N 460 -330 460 -380 {}
N 460 -380 660 -380 {}
N 660 -380 660 -330 {}
N 460 -120 460 -70 {}
N 460 -70 660 -70 {}
N 660 -70 660 -120 {}

v {xschem version=3.4.8RC file_version=1.3}
G {}
K {}
V {}
S {}
E {}
B 4 100 -480 1702 -328 {fill=false}
T {g1_tg - 1.2 V transmission gate, on when en=1 (enb=0)} 112 -470 0 0 0.55 0.55 {}
T {G1 guardian, chip of record g1_chip_top_1414_r2.gds 9049e87b (r2 2026-09-25; geometry XOR-identical to r1 629d303a); block map: g1_padring/reports/signoff-1414-20260924} 112 -431 0 0 0.3 0.3 {}
T {On-chip variant: HISTORICAL 12u/0.34u comparators, NOT on the chip (chip-of-record sheets: ../, G1_TRIP_VARIANT=chip); netlists ../../sim/netlist/*.spice} 112 -407 0 0 0.3 0.3 {}
T {Netlist-equivalent to g1_tg netlisted standalone (no instance in g1_trip)} 112 -383 0 0 0.3 0.3 {}
T {Drawn 2026-09-25 by the block generator; device sizes (w, l, ng, m) are on each symbol. Proof: review/schematics-readability-20260925} 112 -359 0 0 0.25 0.25 {}
C {sg13g2_pr/sg13_lv_nmos.sym} 200 -200 0 0 {name=MN model=sg13_lv_nmos w=1u l=0.13u ng=1 m=1}
C {sg13g2_pr/sg13_lv_pmos.sym} 400 -200 0 0 {name=MP model=sg13_lv_pmos w=2u l=0.13u ng=1 m=1}
C {devices/ipin.sym} 80 -200 0 0 {name=p0 lab=en}
C {devices/ipin.sym} 80 -60 0 0 {name=p1 lab=enb}
C {devices/iopin.sym} 100 -270 0 1 {name=p2 lab=a}
C {devices/iopin.sym} 540 -130 0 0 {name=p3 lab=b}
C {devices/iopin.sym} 80 -30 0 0 {name=p4 lab=vdd}
C {devices/iopin.sym} 80 0 0 0 {name=p5 lab=vss}
C {g1_body_lab.sym} 220 -200 0 0 {name=l1 lab=vss}
C {g1_body_lab.sym} 420 -200 0 0 {name=l2 lab=vdd}
C {devices/lab_pin.sym} 340 -200 0 0 {name=l3 lab=enb}
N 220 -230 220 -270 {}
N 220 -270 420 -270 {}
N 420 -270 420 -230 {}
N 220 -170 220 -130 {}
N 220 -130 420 -130 {}
N 420 -130 420 -170 {}
N 80 -200 180 -200 {}
N 380 -200 340 -200 {}
N 100 -270 220 -270 {}
N 420 -130 540 -130 {}

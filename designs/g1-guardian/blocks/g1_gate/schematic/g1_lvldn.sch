v {xschem version=3.4.8RC file_version=1.3}
G {}
K {}
V {}
S {}
E {}
B 4 120 -600 1722 -448 {fill=false}
T {a/ab: 3.3 V complementary inputs; thick-oxide pull-downs, cross-coupled 1.2 V PMOS load on vdd.} 160 -20 0 0 0.3 0.3 {}
T {g1_lvldn - 3.3 V to 1.2 V level shifter (y = a)} 132 -590 0 0 0.55 0.55 {}
T {G1 guardian, chip of record g1_chip_top_1414_r2.gds 9049e87b (r2 2026-09-25; geometry XOR-identical to r1 629d303a); block map: g1_padring/reports/signoff-1414-20260924} 132 -551 0 0 0.3 0.3 {}
T {On-chip variant: baseline (chip cell retained_g1_gate = layout/g1_gate.gds ddf2c44a; LVS reference layout/g1_gate.cdl 27548c03)} 132 -527 0 0 0.3 0.3 {}
T {Netlist-equivalent to sim/netlist/g1_lvldn.spice sha256 d253d0a6} 132 -503 0 0 0.3 0.3 {}
T {Drawn 2026-09-25 by the block generator; device sizes (w, l, ng, m) are on each symbol. Proof: review/schematics-readability-20260925} 132 -479 0 0 0.25 0.25 {}
C {sg13g2_pr/sg13_hv_nmos.sym} 300 -150 0 0 {name=MN1 model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 500 -150 0 0 {name=MN2 model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_lv_pmos.sym} 500 -300 0 0 {name=MP1 model=sg13_lv_pmos w=1u l=0.13u ng=1 m=1}
C {sg13g2_pr/sg13_lv_pmos.sym} 300 -300 0 0 {name=MP2 model=sg13_lv_pmos w=1u l=0.13u ng=1 m=1}
C {devices/ipin.sym} 100 -150 0 0 {name=p0 lab=a}
C {devices/ipin.sym} 100 -100 0 0 {name=p1 lab=ab}
C {devices/opin.sym} 640 -225 0 0 {name=p2 lab=y}
C {devices/iopin.sym} 160 -380 0 1 {name=p3 lab=vdd}
C {devices/iopin.sym} 160 -70 0 1 {name=p4 lab=vss}
C {devices/lab_pin.sym} 320 -225 0 0 {name=l1 lab=yb}
C {devices/lab_pin.sym} 440 -150 0 0 {name=l2 lab=ab}
N 320 -150 320 -120 {}
N 520 -150 520 -120 {}
N 520 -300 520 -330 {}
N 320 -300 320 -330 {}
N 320 -270 320 -180 {}
N 520 -270 520 -180 {}
N 320 -245 450 -245 {}
N 450 -245 450 -300 {}
N 450 -300 480 -300 {}
N 520 -205 260 -205 {}
N 260 -205 260 -300 {}
N 260 -300 280 -300 {}
N 100 -150 280 -150 {}
N 480 -150 440 -150 {}
N 520 -225 640 -225 {}
N 320 -330 320 -380 {}
N 320 -380 520 -380 {}
N 520 -380 520 -330 {}
N 320 -380 160 -380 {}
N 320 -120 320 -70 {}
N 320 -70 520 -70 {}
N 520 -70 520 -120 {}
N 320 -70 160 -70 {}

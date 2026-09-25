v {xschem version=3.4.8RC file_version=1.3}
G {}
K {}
V {}
S {}
E {}
B 4 120 -600 1722 -448 {fill=false}
T {g1_hv_nor2 - 3.3 V NOR2 (y = !(a + b))} 132 -590 0 0 0.55 0.55 {}
T {G1 guardian, chip of record g1_chip_top_1414_r2.gds 9049e87b (r2 2026-09-25; geometry XOR-identical to r1 629d303a); block map: g1_padring/reports/signoff-1414-20260924} 132 -551 0 0 0.3 0.3 {}
T {On-chip variant: baseline (chip cell retained_g1_gate = layout/g1_gate.gds ddf2c44a; LVS reference layout/g1_gate.cdl 27548c03)} 132 -527 0 0 0.3 0.3 {}
T {Netlist-equivalent to the g1_hv_nor2 subcircuit in sim/netlist/g1_gate.spice sha256 846a55e0} 132 -503 0 0 0.3 0.3 {}
T {Drawn 2026-09-25 by the block generator; device sizes (w, l, ng, m) are on each symbol. Proof: review/schematics-readability-20260925} 132 -479 0 0 0.25 0.25 {}
C {sg13g2_pr/sg13_hv_pmos.sym} 200 -340 0 0 {name=MP1 model=sg13_hv_pmos w=7.8u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_pmos.sym} 200 -240 0 0 {name=MP2 model=sg13_hv_pmos w=7.8u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 200 -100 0 0 {name=MN1 model=sg13_hv_nmos w=1.9u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 380 -100 0 0 {name=MN2 model=sg13_hv_nmos w=1.9u l=0.45u ng=1 m=1}
C {devices/ipin.sym} 60 -300 0 0 {name=p0 lab=a}
C {devices/ipin.sym} 60 -240 0 0 {name=p1 lab=b}
C {devices/opin.sym} 500 -170 0 0 {name=p2 lab=y}
C {devices/iopin.sym} 100 -400 0 1 {name=p3 lab=vdda}
C {devices/iopin.sym} 100 -30 0 1 {name=p4 lab=vss}
C {g1_body_lab.sym} 220 -240 0 0 {name=l1 lab=vdda}
C {devices/lab_wire.sym} 220 -290 0 0 {name=l2 lab=m}
C {devices/lab_pin.sym} 320 -100 0 0 {name=l3 lab=b}
N 220 -340 220 -370 {}
N 220 -100 220 -70 {}
N 400 -100 400 -70 {}
N 220 -310 220 -270 {}
N 220 -210 220 -130 {}
N 220 -170 400 -170 {}
N 400 -170 400 -130 {}
N 400 -170 500 -170 {}
N 160 -340 180 -340 {}
N 160 -100 180 -100 {}
N 160 -340 160 -100 {}
N 60 -300 160 -300 {}
N 60 -240 180 -240 {}
N 360 -100 320 -100 {}
N 220 -370 220 -400 {}
N 220 -400 100 -400 {}
N 220 -70 220 -30 {}
N 220 -30 400 -30 {}
N 400 -30 400 -70 {}
N 220 -30 100 -30 {}

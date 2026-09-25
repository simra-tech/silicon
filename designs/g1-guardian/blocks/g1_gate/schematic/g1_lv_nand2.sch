v {xschem version=3.4.8RC file_version=1.3}
G {}
K {}
V {}
S {}
E {}
B 4 120 -580 1722 -428 {fill=false}
T {g1_lv_nand2 - 1.2 V NAND2 (y = !(a b))} 132 -570 0 0 0.55 0.55 {}
T {G1 guardian, chip of record g1_chip_top_1414_r2.gds 9049e87b (r2 2026-09-25; geometry XOR-identical to r1 629d303a); block map: g1_padring/reports/signoff-1414-20260924} 132 -531 0 0 0.3 0.3 {}
T {On-chip variant: baseline (chip cell retained_g1_gate = layout/g1_gate.gds ddf2c44a; LVS reference layout/g1_gate.cdl 27548c03)} 132 -507 0 0 0.3 0.3 {}
T {Netlist-equivalent to the g1_lv_nand2 subcircuit in sim/netlist/g1_gate.spice sha256 846a55e0} 132 -483 0 0 0.3 0.3 {}
T {Drawn 2026-09-25 by the block generator; device sizes (w, l, ng, m) are on each symbol. Proof: review/schematics-readability-20260925} 132 -459 0 0 0.25 0.25 {}
C {sg13g2_pr/sg13_lv_pmos.sym} 200 -300 0 0 {name=MP1 model=sg13_lv_pmos w=2u l=0.13u ng=1 m=1}
C {sg13g2_pr/sg13_lv_pmos.sym} 360 -300 0 0 {name=MP2 model=sg13_lv_pmos w=2u l=0.13u ng=1 m=1}
C {sg13g2_pr/sg13_lv_nmos.sym} 200 -150 0 0 {name=MN1 model=sg13_lv_nmos w=2u l=0.13u ng=1 m=1}
C {sg13g2_pr/sg13_lv_nmos.sym} 200 -40 0 0 {name=MN2 model=sg13_lv_nmos w=2u l=0.13u ng=1 m=1}
C {devices/ipin.sym} 60 -225 0 0 {name=p0 lab=a}
C {devices/ipin.sym} 60 -40 0 0 {name=p1 lab=b}
C {devices/opin.sym} 480 -225 0 0 {name=p2 lab=y}
C {devices/iopin.sym} 100 -380 0 1 {name=p3 lab=vdd}
C {devices/iopin.sym} 100 40 0 1 {name=p4 lab=vss}
C {g1_body_lab.sym} 220 -150 0 0 {name=l1 lab=vss}
C {devices/lab_wire.sym} 220 -95 0 0 {name=l2 lab=m}
C {devices/lab_pin.sym} 300 -300 0 0 {name=l3 lab=b}
N 220 -300 220 -330 {}
N 380 -300 380 -330 {}
N 220 -40 220 -10 {}
N 180 -300 180 -150 {}
N 220 -270 220 -225 {}
N 220 -225 380 -225 {}
N 380 -225 380 -270 {}
N 220 -225 220 -180 {}
N 220 -120 220 -70 {}
N 60 -225 180 -225 {}
N 60 -40 180 -40 {}
N 340 -300 300 -300 {}
N 380 -225 480 -225 {}
N 220 -330 220 -380 {}
N 220 -380 380 -380 {}
N 380 -380 380 -330 {}
N 220 -380 100 -380 {}
N 220 -10 220 40 {}
N 220 40 100 40 {}

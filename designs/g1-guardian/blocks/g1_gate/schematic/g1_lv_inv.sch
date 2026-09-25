v {xschem version=3.4.8RC file_version=1.3}
G {}
K {}
V {}
S {}
E {}
B 4 120 -560 1722 -408 {fill=false}
T {g1_lv_inv - 1.2 V inverter} 132 -550 0 0 0.55 0.55 {}
T {G1 guardian, chip of record g1_chip_top_1414_r2.gds 9049e87b (r2 2026-09-25; geometry XOR-identical to r1 629d303a); block map: g1_padring/reports/signoff-1414-20260924} 132 -511 0 0 0.3 0.3 {}
T {On-chip variant: baseline (chip cell retained_g1_gate = layout/g1_gate.gds ddf2c44a; LVS reference layout/g1_gate.cdl 27548c03)} 132 -487 0 0 0.3 0.3 {}
T {Netlist-equivalent to the g1_lv_inv subcircuit in sim/netlist/g1_gate.spice sha256 846a55e0} 132 -463 0 0 0.3 0.3 {}
T {Drawn 2026-09-25 by the block generator; device sizes (w, l, ng, m) are on each symbol. Proof: review/schematics-readability-20260925} 132 -439 0 0 0.25 0.25 {}
C {sg13g2_pr/sg13_lv_pmos.sym} 200 -300 0 0 {name=MP model=sg13_lv_pmos w=2u l=0.13u ng=1 m=1}
C {sg13g2_pr/sg13_lv_nmos.sym} 200 -150 0 0 {name=MN model=sg13_lv_nmos w=1u l=0.13u ng=1 m=1}
C {devices/ipin.sym} 80 -225 0 0 {name=p0 lab=a}
C {devices/opin.sym} 360 -225 0 0 {name=p1 lab=y}
C {devices/iopin.sym} 100 -380 0 1 {name=p2 lab=vdd}
C {devices/iopin.sym} 100 -70 0 1 {name=p3 lab=vss}
N 220 -300 220 -330 {}
N 220 -150 220 -120 {}
N 180 -300 180 -150 {}
N 220 -270 220 -180 {}
N 80 -225 180 -225 {}
N 220 -225 360 -225 {}
N 220 -330 220 -380 {}
N 220 -380 100 -380 {}
N 220 -120 220 -70 {}
N 220 -70 100 -70 {}

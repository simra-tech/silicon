v {xschem version=3.4.8RC file_version=1.3}
G {}
K {}
V {}
S {}
E {}
B 4 100 -750 1702 -598 {fill=false}
T {g1_osc_nor2 - 1.2 V 2-input NOR} 112 -740 0 0 0.55 0.55 {}
T {G1 guardian, chip of record g1_chip_top_1414_r2.gds 9049e87b (r2 2026-09-25; geometry XOR-identical to r1 629d303a); block map: g1_padring/reports/signoff-1414-20260924} 112 -701 0 0 0.3 0.3 {}
T {On-chip variant: R0.95 (this sheet): RA/RB rppd 1u/111.15u = chip CDL g1_osc RRA/RRB (canonical CDL 126acd51 lineage); sub-cells = layout/g1_osc_lvs.cdl 8a8fa94a} 112 -677 0 0 0.3 0.3 {}
T {Netlist-equivalent to the g1_osc_nor2 subcircuit in sim/netlist/g1_osc.spice sha256 43a16205 except XRA/XRB l=111.15u (R0.95); sub-cells identical} 112 -653 0 0 0.3 0.3 {}
T {Drawn 2026-09-25 by the block generator; device sizes (w, l, ng, m) are on each symbol. Proof: review/schematics-readability-20260925} 112 -629 0 0 0.25 0.25 {}
C {sg13g2_pr/sg13_lv_pmos.sym} 200 -420 0 0 {name=MP0 model=sg13_lv_pmos w=2u l=0.13u ng=1 m=1}
C {sg13g2_pr/sg13_lv_pmos.sym} 200 -310 0 0 {name=MP1 model=sg13_lv_pmos w=2u l=0.13u ng=1 m=1}
C {sg13g2_pr/sg13_lv_nmos.sym} 200 -100 0 0 {name=MN0 model=sg13_lv_nmos w=0.5u l=0.13u ng=1 m=1}
C {sg13g2_pr/sg13_lv_nmos.sym} 380 -100 0 0 {name=MN1 model=sg13_lv_nmos w=0.5u l=0.13u ng=1 m=1}
C {devices/ipin.sym} 60 -420 0 0 {name=p0 lab=a0}
C {devices/ipin.sym} 60 -310 0 0 {name=p1 lab=a1}
C {devices/opin.sym} 520 -170 0 0 {name=p2 lab=y}
C {devices/iopin.sym} 100 -490 0 1 {name=p3 lab=vdd}
C {devices/iopin.sym} 100 -30 0 1 {name=p4 lab=vss}
C {g1_body_lab.sym} 220 -310 0 0 {name=l1 lab=vdd}
C {devices/lab_pin.sym} 220 -370 0 1 {name=l2 lab=p0}
C {devices/lab_pin.sym} 140 -100 0 0 {name=l3 lab=a0}
C {devices/lab_pin.sym} 320 -100 0 0 {name=l4 lab=a1}
N 220 -420 220 -450 {}
N 220 -100 220 -70 {}
N 400 -100 400 -70 {}
N 220 -390 220 -340 {}
N 220 -280 220 -130 {}
N 220 -170 400 -170 {}
N 400 -130 400 -170 {}
N 60 -420 180 -420 {}
N 180 -100 140 -100 {}
N 60 -310 180 -310 {}
N 360 -100 320 -100 {}
N 400 -170 520 -170 {}
N 100 -490 220 -490 {}
N 220 -450 220 -490 {}
N 100 -30 400 -30 {}
N 220 -70 220 -30 {}
N 400 -70 400 -30 {}

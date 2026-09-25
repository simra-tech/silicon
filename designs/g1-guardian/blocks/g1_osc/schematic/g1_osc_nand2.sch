v {xschem version=3.4.8RC file_version=1.3}
G {}
K {}
V {}
S {}
E {}
B 4 100 -540 1702 -388 {fill=false}
T {g1_osc_nand2 - 1.2 V 2-input NAND} 112 -530 0 0 0.55 0.55 {}
T {G1 guardian, chip of record g1_chip_top_1414_r2.gds 9049e87b (r2 2026-09-25; geometry XOR-identical to r1 629d303a); block map: g1_padring/reports/signoff-1414-20260924} 112 -491 0 0 0.3 0.3 {}
T {On-chip variant: R0.95 (this sheet): RA/RB rppd 1u/111.15u = chip CDL g1_osc RRA/RRB (canonical CDL 126acd51 lineage); sub-cells = layout/g1_osc_lvs.cdl 8a8fa94a} 112 -467 0 0 0.3 0.3 {}
T {Netlist-equivalent to the g1_osc_nand2 subcircuit in sim/netlist/g1_osc.spice sha256 43a16205 except XRA/XRB l=111.15u (R0.95); sub-cells identical} 112 -443 0 0 0.3 0.3 {}
T {Drawn 2026-09-25 by the block generator; device sizes (w, l, ng, m) are on each symbol. Proof: review/schematics-readability-20260925} 112 -419 0 0 0.25 0.25 {}
C {sg13g2_pr/sg13_lv_pmos.sym} 200 -300 0 0 {name=MP0 model=sg13_lv_pmos w=1u l=0.13u ng=1 m=1}
C {sg13g2_pr/sg13_lv_pmos.sym} 380 -300 0 0 {name=MP1 model=sg13_lv_pmos w=1u l=0.13u ng=1 m=1}
C {sg13g2_pr/sg13_lv_nmos.sym} 200 -150 0 0 {name=MN0 model=sg13_lv_nmos w=1u l=0.13u ng=1 m=1}
C {sg13g2_pr/sg13_lv_nmos.sym} 200 -40 0 0 {name=MN1 model=sg13_lv_nmos w=1u l=0.13u ng=1 m=1}
C {devices/ipin.sym} 60 -225 0 0 {name=p0 lab=a0}
C {devices/ipin.sym} 60 -40 0 0 {name=p1 lab=a1}
C {devices/opin.sym} 500 -225 0 0 {name=p2 lab=y}
C {devices/iopin.sym} 100 -380 0 1 {name=p3 lab=vdd}
C {devices/iopin.sym} 100 40 0 1 {name=p4 lab=vss}
C {g1_body_lab.sym} 220 -150 0 0 {name=l1 lab=vss}
C {devices/lab_pin.sym} 220 -95 0 1 {name=l2 lab=n0}
C {devices/lab_pin.sym} 320 -300 0 0 {name=l3 lab=a1}
N 220 -300 220 -330 {}
N 400 -300 400 -330 {}
N 220 -40 220 -10 {}
N 180 -300 180 -150 {}
N 220 -270 220 -225 {}
N 220 -225 400 -225 {}
N 400 -225 400 -270 {}
N 220 -225 220 -180 {}
N 220 -120 220 -70 {}
N 60 -225 180 -225 {}
N 60 -40 180 -40 {}
N 360 -300 320 -300 {}
N 400 -225 500 -225 {}
N 100 -380 400 -380 {}
N 220 -330 220 -380 {}
N 400 -330 400 -380 {}
N 100 40 220 40 {}
N 220 -10 220 40 {}

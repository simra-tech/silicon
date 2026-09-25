v {xschem version=3.4.8RC file_version=1.3}
G {}
K {}
V {}
S {}
E {}
B 4 100 -620 1702 -468 {fill=false}
T {C(top) = 1.50 pF + 100 fF x code (cmim ~1.5 fF/um^2); a trim cap counts when its NMOS switch is on (t_b = 1)} 100 0 0 0 0.3 0.3 {}
T {g1_osc_cbank - timing capacitor: fixed 1.50 pF + 4-bit binary trim} 112 -610 0 0 0.55 0.55 {}
T {G1 guardian, chip of record g1_chip_top_1414_r2.gds 9049e87b (r2 2026-09-25; geometry XOR-identical to r1 629d303a); block map: g1_padring/reports/signoff-1414-20260924} 112 -571 0 0 0.3 0.3 {}
T {On-chip variant: R0.95 (this sheet): RA/RB rppd 1u/111.15u = chip CDL g1_osc RRA/RRB (canonical CDL 126acd51 lineage); sub-cells = layout/g1_osc_lvs.cdl 8a8fa94a} 112 -547 0 0 0.3 0.3 {}
T {Netlist-equivalent to the g1_osc_cbank subcircuit in sim/netlist/g1_osc.spice sha256 43a16205 except XRA/XRB l=111.15u (R0.95); sub-cells identical} 112 -523 0 0 0.3 0.3 {}
T {Drawn 2026-09-25 by the block generator; device sizes (w, l, ng, m) are on each symbol. Proof: review/schematics-readability-20260925} 112 -499 0 0 0.25 0.25 {}
C {sg13g2_pr/cap_cmim.sym} 160 -300 0 0 {name=CF model=cap_cmim w=31.65u l=31.65u m=1}
C {sg13g2_pr/cap_cmim.sym} 380 -300 0 0 {name=CT0 model=cap_cmim w=8.16u l=8.16u m=1}
C {sg13g2_pr/sg13_lv_nmos.sym} 360 -180 0 0 {name=MS0 model=sg13_lv_nmos w=4u l=0.13u ng=1 m=1}
C {sg13g2_pr/cap_cmim.sym} 600 -300 0 0 {name=CT1 model=cap_cmim w=11.55u l=11.55u m=1}
C {sg13g2_pr/sg13_lv_nmos.sym} 580 -180 0 0 {name=MS1 model=sg13_lv_nmos w=4u l=0.13u ng=1 m=1}
C {sg13g2_pr/cap_cmim.sym} 820 -300 0 0 {name=CT2 model=cap_cmim w=16.33u l=16.33u m=1}
C {sg13g2_pr/sg13_lv_nmos.sym} 800 -180 0 0 {name=MS2 model=sg13_lv_nmos w=4u l=0.13u ng=1 m=1}
C {sg13g2_pr/cap_cmim.sym} 1040 -300 0 0 {name=CT3 model=cap_cmim w=23.09u l=23.09u m=1}
C {sg13g2_pr/sg13_lv_nmos.sym} 1020 -180 0 0 {name=MS3 model=sg13_lv_nmos w=4u l=0.13u ng=1 m=1}
C {devices/ipin.sym} 60 -140 0 0 {name=p0 lab=t0}
C {devices/ipin.sym} 60 -115 0 0 {name=p1 lab=t1}
C {devices/ipin.sym} 60 -90 0 0 {name=p2 lab=t2}
C {devices/ipin.sym} 60 -65 0 0 {name=p3 lab=t3}
C {devices/iopin.sym} 100 -400 0 1 {name=p4 lab=top}
C {devices/iopin.sym} 100 -80 0 1 {name=p5 lab=vss}
C {devices/lab_pin.sym} 380 -240 0 1 {name=l1 lab=b0}
C {devices/lab_pin.sym} 600 -240 0 1 {name=l2 lab=b1}
C {devices/lab_pin.sym} 820 -240 0 1 {name=l3 lab=b2}
C {devices/lab_pin.sym} 1040 -240 0 1 {name=l4 lab=b3}
C {devices/lab_pin.sym} 300 -180 0 0 {name=l5 lab=t0}
C {devices/lab_pin.sym} 520 -180 0 0 {name=l6 lab=t1}
C {devices/lab_pin.sym} 740 -180 0 0 {name=l7 lab=t2}
C {devices/lab_pin.sym} 960 -180 0 0 {name=l8 lab=t3}
N 380 -180 380 -150 {}
N 600 -180 600 -150 {}
N 820 -180 820 -150 {}
N 1040 -180 1040 -150 {}
N 160 -330 160 -400 {}
N 160 -400 1040 -400 {}
N 380 -330 380 -400 {}
N 380 -270 380 -210 {}
N 600 -330 600 -400 {}
N 600 -270 600 -210 {}
N 820 -330 820 -400 {}
N 820 -270 820 -210 {}
N 1040 -330 1040 -400 {}
N 1040 -270 1040 -210 {}
N 340 -180 300 -180 {}
N 560 -180 520 -180 {}
N 780 -180 740 -180 {}
N 1000 -180 960 -180 {}
N 100 -400 160 -400 {}
N 160 -270 160 -80 {}
N 160 -80 1040 -80 {}
N 380 -150 380 -80 {}
N 600 -150 600 -80 {}
N 820 -150 820 -80 {}
N 1040 -150 1040 -80 {}
N 100 -80 160 -80 {}

v {xschem version=3.4.8RC file_version=1.3}
G {}
K {}
V {}
S {}
E {}
B 4 150 -500 500 -40 {dash=5 fill=false}
B 4 540 -500 900 -40 {dash=5 fill=false}
B 4 100 -720 1702 -568 {fill=false}
T {5-T NMOS-input stage, PMOS mirror} 158 -494 0 0 0.3 0.3 {layer=4}
T {output inverters} 548 -494 0 0 0.3 0.3 {layer=4}
T {out = 1 when inp > inn; tail from the vbn mirror gate (about 20 uA, MBD in g1_osc)} 150 0 0 0 0.3 0.3 {}
T {g1_osc_cmp - continuous-time comparator} 112 -710 0 0 0.55 0.55 {}
T {G1 guardian, chip of record g1_chip_top_1414_r2.gds 9049e87b (r2 2026-09-25; geometry XOR-identical to r1 629d303a); block map: g1_padring/reports/signoff-1414-20260924} 112 -671 0 0 0.3 0.3 {}
T {On-chip variant: R0.95 (this sheet): RA/RB rppd 1u/111.15u = chip CDL g1_osc RRA/RRB (canonical CDL 126acd51 lineage); sub-cells = layout/g1_osc_lvs.cdl 8a8fa94a} 112 -647 0 0 0.3 0.3 {}
T {Netlist-equivalent to sim/netlist/g1_osc_cmp.spice sha256 ad2ce6b3} 112 -623 0 0 0.3 0.3 {}
T {Drawn 2026-09-25 by the block generator; device sizes (w, l, ng, m) are on each symbol. Proof: review/schematics-readability-20260925} 112 -599 0 0 0.25 0.25 {}
C {sg13g2_pr/sg13_lv_nmos.sym} 300 -130 0 0 {name=MT model=sg13_lv_nmos w=2u l=0.5u ng=1 m=1}
C {sg13g2_pr/sg13_lv_nmos.sym} 200 -250 0 0 {name=M1 model=sg13_lv_nmos w=4u l=0.3u ng=1 m=1}
C {sg13g2_pr/sg13_lv_nmos.sym} 440 -250 0 1 {name=M2 model=sg13_lv_nmos w=4u l=0.3u ng=1 m=1}
C {sg13g2_pr/sg13_lv_pmos.sym} 240 -400 0 1 {name=M3 model=sg13_lv_pmos w=2u l=0.3u ng=1 m=1}
C {sg13g2_pr/sg13_lv_pmos.sym} 400 -400 0 0 {name=M4 model=sg13_lv_pmos w=2u l=0.3u ng=1 m=1}
C {g1_osc_inv.sym} 620 -320 0 0 {name=XI1 }
C {g1_osc_inv.sym} 800 -320 0 0 {name=XI2 }
C {devices/ipin.sym} 60 -250 0 0 {name=p0 lab=inp}
C {devices/ipin.sym} 60 -200 0 0 {name=p1 lab=inn}
C {devices/ipin.sym} 60 -130 0 0 {name=p2 lab=vbn}
C {devices/opin.sym} 960 -320 0 0 {name=p3 lab=out}
C {devices/iopin.sym} 100 -470 0 1 {name=p4 lab=vdd}
C {devices/iopin.sym} 100 -60 0 1 {name=p5 lab=vss}
C {g1_body_lab.sym} 220 -250 0 0 {name=l1 lab=vss}
C {g1_body_lab.sym} 420 -250 0 0 {name=l2 lab=vss}
C {devices/lab_pin.sym} 220 -310 0 0 {name=l3 lab=d1}
C {devices/lab_wire.sym} 300 -190 0 0 {name=l4 lab=tail}
C {devices/lab_pin.sym} 500 -250 0 1 {name=l5 lab=inn}
C {devices/lab_wire.sym} 540 -320 0 0 {name=l6 lab=o1}
C {devices/lab_wire.sym} 730 -320 0 0 {name=l7 lab=o2}
C {devices/lab_pin.sym} 620 -390 0 1 {name=l8 lab=vdd}
C {devices/lab_pin.sym} 620 -250 0 1 {name=l9 lab=vss}
C {devices/lab_pin.sym} 800 -390 0 1 {name=l10 lab=vdd}
C {devices/lab_pin.sym} 800 -250 0 1 {name=l11 lab=vss}
N 320 -130 320 -100 {}
N 220 -400 220 -430 {}
N 420 -400 420 -430 {}
N 220 -370 220 -280 {}
N 420 -370 420 -280 {}
N 260 -400 380 -400 {}
N 320 -400 320 -340 {}
N 320 -340 220 -340 {}
N 220 -220 220 -190 {}
N 220 -190 420 -190 {}
N 420 -190 420 -220 {}
N 320 -190 320 -160 {}
N 60 -250 180 -250 {}
N 460 -250 500 -250 {}
N 60 -130 280 -130 {}
N 420 -320 560 -320 {}
N 680 -320 740 -320 {}
N 860 -320 960 -320 {}
N 620 -370 620 -390 {}
N 620 -270 620 -250 {}
N 800 -370 800 -390 {}
N 800 -270 800 -250 {}
N 100 -470 420 -470 {}
N 220 -430 220 -470 {}
N 420 -430 420 -470 {}
N 100 -60 320 -60 {}
N 320 -100 320 -60 {}

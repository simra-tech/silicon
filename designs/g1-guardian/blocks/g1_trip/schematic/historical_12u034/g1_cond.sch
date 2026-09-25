v {xschem version=3.4.8RC file_version=1.3}
G {}
K {}
V {}
S {}
E {}
B 4 100 -660 1702 -508 {fill=false}
T {icmp = ISENSE / 2 (5 + 5 units of the 10 k SENSE unit rppd 2u/76.7u); CH 1 pF holds icmp against comparator kickback.} 120 -20 0 0 0.3 0.3 {}
T {ISENSE = 1.0 V pedestal + 20 x Vshunt (1.0 .. 2.0 V) -> icmp 0.5 .. 1.0 V, the DAC tap range.} 120 -2 0 0 0.3 0.3 {}
T {g1_cond - ISENSE conditioning: 2:1 divider + 1 pF hold} 112 -650 0 0 0.55 0.55 {}
T {G1 guardian, chip of record g1_chip_top_1414_r2.gds 9049e87b (r2 2026-09-25; geometry XOR-identical to r1 629d303a); block map: g1_padring/reports/signoff-1414-20260924} 112 -611 0 0 0.3 0.3 {}
T {On-chip variant: HISTORICAL 12u/0.34u comparators, NOT on the chip (chip-of-record sheets: ../, G1_TRIP_VARIANT=chip); netlists ../../sim/netlist/*.spice} 112 -587 0 0 0.3 0.3 {}
T {Netlist-equivalent to sim/netlist/g1_cond.spice sha256 ef8ed581} 112 -563 0 0 0.3 0.3 {}
T {Drawn 2026-09-25 by the block generator; device sizes (w, l, ng, m) are on each symbol. Proof: review/schematics-readability-20260925} 112 -539 0 0 0.25 0.25 {}
C {sg13g2_pr/rppd.sym} 300 -300 3 0 {name=RC0 w=2u l=76.7u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 430 -300 3 0 {name=RC1 w=2u l=76.7u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 560 -300 3 0 {name=RC2 w=2u l=76.7u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 690 -300 3 0 {name=RC3 w=2u l=76.7u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 820 -300 3 0 {name=RC4 w=2u l=76.7u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 950 -300 3 0 {name=RC5 w=2u l=76.7u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1080 -300 3 0 {name=RC6 w=2u l=76.7u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1210 -300 3 0 {name=RC7 w=2u l=76.7u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1340 -300 3 0 {name=RC8 w=2u l=76.7u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1470 -300 3 0 {name=RC9 w=2u l=76.7u model=rppd b=0 m=1}
C {sg13g2_pr/cap_cmim.sym} 1000 -180 0 0 {name=CH model=cap_cmim w=26u l=26u m=1}
C {devices/ipin.sym} 120 -300 0 0 {name=p0 lab=isense}
C {devices/opin.sym} 1600 -400 0 0 {name=p1 lab=icmp}
C {devices/iopin.sym} 120 -100 0 1 {name=p2 lab=vss}
C {g1_node_lab.sym} 365 -300 0 0 {name=l1 lab=c0}
C {g1_node_lab.sym} 495 -300 0 0 {name=l2 lab=c1}
C {g1_node_lab.sym} 625 -300 0 0 {name=l3 lab=c2}
C {g1_node_lab.sym} 755 -300 0 0 {name=l4 lab=c3}
C {g1_node_lab.sym} 1015 -300 0 0 {name=l5 lab=c5}
C {g1_node_lab.sym} 1145 -300 0 0 {name=l6 lab=c6}
C {g1_node_lab.sym} 1275 -300 0 0 {name=l7 lab=c7}
C {g1_node_lab.sym} 1405 -300 0 0 {name=l8 lab=c8}
C {devices/lab_wire.sym} 1000 -400 0 0 {name=l9 lab=icmp}
N 330 -300 400 -300 {}
N 460 -300 530 -300 {}
N 590 -300 660 -300 {}
N 720 -300 790 -300 {}
N 850 -300 920 -300 {}
N 980 -300 1050 -300 {}
N 1110 -300 1180 -300 {}
N 1240 -300 1310 -300 {}
N 1370 -300 1440 -300 {}
N 120 -300 270 -300 {}
N 880 -300 880 -400 {}
N 880 -400 1600 -400 {}
N 880 -300 880 -240 {}
N 880 -240 1000 -240 {}
N 1000 -240 1000 -210 {}
N 1500 -300 1640 -300 {}
N 1640 -300 1640 -100 {}
N 1640 -100 1000 -100 {}
N 1000 -100 1000 -150 {}
N 120 -100 1000 -100 {}

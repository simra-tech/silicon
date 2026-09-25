v {xschem version=3.4.8RC file_version=1.3}
G {}
K {}
V {}
S {}
E {}
B 4 90 -760 1000 -110 {dash=5 fill=false}
B 4 1120 -760 1330 -110 {dash=5 fill=false}
B 4 1400 -760 2230 -110 {dash=5 fill=false}
B 4 100 -960 2213 -808 {fill=false}
T {StrongARM latch: precharge (clk=0), evaluate (clk=1); dummies MD1/MD2 cancel input kickback} 98 -754 0 0 0.3 0.3 {layer=4}
T {skewed inverters} 1128 -754 0 0 0.3 0.3 {layer=4}
T {NOR SR latch: holds q between strobes} 1408 -754 0 0 0.3 0.3 {layer=4}
T {q = 1 when inp > inn at the rising clk edge.  Core sizes from 2AMLogic sg13g2-comparator (Apache-2.0), tail bias branch removed.} 90 -40 0 0 0.3 0.3 {}
T {regenpair4: the regenerative NMOS pair M3/M4 is 6u/0.26u (baseline 3u/0.13u); input pair 12u/0.34u.} 90 -22 0 0 0.3 0.3 {}
T {Hard-comparator decision delay on the extraction: not run (g1_trip/README.md).} 90 -4 0 0 0.3 0.3 {}
T {g1_cmp_regenpair4 - 1.2 V StrongARM comparator, hard path (regenerative pair M3/M4 6u/0.26u)} 112 -950 0 0 0.55 0.55 {}
T {G1 guardian, chip of record g1_chip_top_1414_r2.gds 9049e87b (r2 2026-09-25; geometry XOR-identical to r1 629d303a); block map: g1_padring/reports/signoff-1414-20260924} 112 -911 0 0 0.3 0.3 {}
T {On-chip variant: chip of record (regenpair4 + NF4): soft g1_cmp M1/M2 24u/0.68u ng=4, hard g1_cmp_regenpair4 M3/M4 6u/0.26u; rppd bodies on vss as in the chip deck; layout/g1_trip_lvs.cdl 60a9ad6e + regenpair4/NF4 cell CDLs} 112 -887 0 0 0.3 0.3 {}
T {Netlist-equivalent to the g1_cmp_regenpair4 subcircuit in sim/qualification/joint586-softinputpair4-nf4-roomcal-s73133-20260924-r1/trip.spice sha256 f5f0a90a (chip deck)} 112 -863 0 0 0.3 0.3 {}
T {Drawn 2026-09-25 by the block generator; device sizes (w, l, ng, m) are on each symbol. Proof: review/schematics-readability-20260925} 112 -839 0 0 0.25 0.25 {}
C {sg13g2_pr/sg13_lv_nmos.sym} 550 -160 0 0 {name=MTAIL model=sg13_lv_nmos w=16u l=0.13u ng=1 m=1}
C {sg13g2_pr/sg13_lv_nmos.sym} 400 -300 0 0 {name=M1 model=sg13_lv_nmos w=12u l=0.34u ng=1 m=1}
C {sg13g2_pr/sg13_lv_nmos.sym} 700 -300 0 1 {name=M2 model=sg13_lv_nmos w=12u l=0.34u ng=1 m=1}
C {sg13g2_pr/sg13_lv_nmos.sym} 950 -300 0 1 {name=MD1 model=sg13_lv_nmos w=6u l=0.13u ng=1 m=1}
C {sg13g2_pr/sg13_lv_nmos.sym} 150 -300 0 0 {name=MD2 model=sg13_lv_nmos w=6u l=0.13u ng=1 m=1}
C {sg13g2_pr/sg13_lv_nmos.sym} 400 -460 0 0 {name=M3 model=sg13_lv_nmos w=6u l=0.26u ng=1 m=1}
C {sg13g2_pr/sg13_lv_nmos.sym} 700 -460 0 1 {name=M4 model=sg13_lv_nmos w=6u l=0.26u ng=1 m=1}
C {sg13g2_pr/sg13_lv_pmos.sym} 400 -600 0 0 {name=M5 model=sg13_lv_pmos w=3u l=0.13u ng=1 m=1}
C {sg13g2_pr/sg13_lv_pmos.sym} 700 -600 0 1 {name=M6 model=sg13_lv_pmos w=3u l=0.13u ng=1 m=1}
C {sg13g2_pr/sg13_lv_pmos.sym} 150 -600 0 0 {name=M7 model=sg13_lv_pmos w=6u l=0.13u ng=1 m=1}
C {sg13g2_pr/sg13_lv_pmos.sym} 950 -600 0 1 {name=M8 model=sg13_lv_pmos w=6u l=0.13u ng=1 m=1}
C {sg13g2_pr/sg13_lv_pmos.sym} 150 -460 0 0 {name=M9 model=sg13_lv_pmos w=3u l=0.13u ng=1 m=1}
C {sg13g2_pr/sg13_lv_pmos.sym} 950 -460 0 1 {name=M10 model=sg13_lv_pmos w=3u l=0.13u ng=1 m=1}
C {sg13g2_pr/sg13_lv_pmos.sym} 1200 -620 0 0 {name=MIAP model=sg13_lv_pmos w=1u l=0.13u ng=1 m=1}
C {sg13g2_pr/sg13_lv_nmos.sym} 1200 -500 0 0 {name=MIAN model=sg13_lv_nmos w=4u l=0.13u ng=1 m=1}
C {sg13g2_pr/sg13_lv_pmos.sym} 1200 -340 0 0 {name=MIBP model=sg13_lv_pmos w=1u l=0.13u ng=1 m=1}
C {sg13g2_pr/sg13_lv_nmos.sym} 1200 -220 0 0 {name=MIBN model=sg13_lv_nmos w=4u l=0.13u ng=1 m=1}
C {sg13g2_pr/sg13_lv_pmos.sym} 1500 -640 0 0 {name=MNAP1 model=sg13_lv_pmos w=4u l=0.13u ng=1 m=1}
C {sg13g2_pr/sg13_lv_pmos.sym} 1540 -540 0 1 {name=MNAP2 model=sg13_lv_pmos w=4u l=0.13u ng=1 m=1}
C {sg13g2_pr/sg13_lv_nmos.sym} 1500 -380 0 0 {name=MNAN1 model=sg13_lv_nmos w=1.5u l=0.13u ng=1 m=1}
C {sg13g2_pr/sg13_lv_nmos.sym} 1680 -380 0 0 {name=MNAN2 model=sg13_lv_nmos w=1.5u l=0.13u ng=1 m=1}
C {sg13g2_pr/sg13_lv_pmos.sym} 1950 -640 0 0 {name=MNBP1 model=sg13_lv_pmos w=4u l=0.13u ng=1 m=1}
C {sg13g2_pr/sg13_lv_pmos.sym} 1990 -540 0 1 {name=MNBP2 model=sg13_lv_pmos w=4u l=0.13u ng=1 m=1}
C {sg13g2_pr/sg13_lv_nmos.sym} 1950 -380 0 0 {name=MNBN1 model=sg13_lv_nmos w=1.5u l=0.13u ng=1 m=1}
C {sg13g2_pr/sg13_lv_nmos.sym} 2130 -380 0 0 {name=MNBN2 model=sg13_lv_nmos w=1.5u l=0.13u ng=1 m=1}
C {devices/ipin.sym} 60 -380 0 0 {name=p0 lab=inp}
C {devices/ipin.sym} 60 -110 0 0 {name=p1 lab=inn}
C {devices/ipin.sym} 60 -160 0 0 {name=p2 lab=clk}
C {devices/opin.sym} 2260 -450 0 0 {name=p3 lab=q}
C {devices/opin.sym} 1800 -250 0 0 {name=p4 lab=qb}
C {devices/iopin.sym} 100 -700 0 1 {name=p5 lab=vdd}
C {devices/iopin.sym} 100 -90 0 1 {name=p6 lab=vss}
C {g1_body_lab.sym} 420 -300 0 0 {name=l1 lab=vss}
C {g1_body_lab.sym} 680 -300 0 0 {name=l2 lab=vss}
C {g1_body_lab.sym} 930 -300 0 0 {name=l3 lab=vss}
C {g1_body_lab.sym} 170 -300 0 0 {name=l4 lab=vss}
C {g1_body_lab.sym} 420 -460 0 0 {name=l5 lab=vss}
C {g1_body_lab.sym} 680 -460 0 0 {name=l6 lab=vss}
C {g1_body_lab.sym} 1520 -540 0 0 {name=l7 lab=vdd}
C {g1_body_lab.sym} 1970 -540 0 0 {name=l8 lab=vdd}
C {devices/lab_pin.sym} 420 -550 0 1 {name=l9 lab=xn}
C {devices/lab_pin.sym} 680 -550 0 0 {name=l10 lab=yn}
C {devices/lab_pin.sym} 420 -400 0 1 {name=l11 lab=xp}
C {devices/lab_pin.sym} 680 -400 0 0 {name=l12 lab=xq}
C {devices/lab_wire.sym} 540 -230 0 0 {name=l13 lab=tail}
C {devices/lab_pin.sym} 760 -300 0 1 {name=l14 lab=inn}
C {devices/lab_pin.sym} 170 -550 0 0 {name=l15 lab=xn}
C {devices/lab_pin.sym} 100 -600 0 0 {name=l16 lab=clk}
C {devices/lab_pin.sym} 170 -410 0 0 {name=l17 lab=xp}
C {devices/lab_pin.sym} 100 -460 0 0 {name=l18 lab=clk}
C {devices/lab_pin.sym} 930 -550 0 0 {name=l19 lab=yn}
C {devices/lab_pin.sym} 1000 -600 0 1 {name=l20 lab=clk}
C {devices/lab_pin.sym} 930 -410 0 0 {name=l21 lab=xq}
C {devices/lab_pin.sym} 1000 -460 0 1 {name=l22 lab=clk}
C {devices/lab_pin.sym} 170 -510 0 0 {name=l23 lab=vdd}
C {devices/lab_pin.sym} 930 -510 0 0 {name=l24 lab=vdd}
C {devices/lab_pin.sym} 1000 -300 0 1 {name=l25 lab=inp}
C {devices/lab_pin.sym} 100 -300 0 0 {name=l26 lab=inn}
C {devices/lab_pin.sym} 170 -350 0 0 {name=l27 lab=xp}
C {devices/lab_pin.sym} 170 -250 0 0 {name=l28 lab=xp}
C {devices/lab_pin.sym} 930 -350 0 0 {name=l29 lab=xq}
C {devices/lab_pin.sym} 930 -250 0 0 {name=l30 lab=xq}
C {devices/lab_pin.sym} 1140 -560 0 0 {name=l31 lab=xn}
C {devices/lab_pin.sym} 1140 -280 0 0 {name=l32 lab=yn}
C {devices/lab_pin.sym} 1220 -390 0 0 {name=l33 lab=vdd}
C {devices/lab_pin.sym} 1220 -450 0 0 {name=l34 lab=vss}
C {devices/lab_wire.sym} 1330 -560 0 0 {name=l35 lab=xnb}
C {devices/lab_pin.sym} 1520 -590 0 0 {name=l36 lab=na}
C {devices/lab_pin.sym} 1590 -540 0 1 {name=l37 lab=q}
C {devices/lab_pin.sym} 1630 -380 0 0 {name=l38 lab=q}
C {devices/lab_wire.sym} 1420 -280 0 0 {name=l39 lab=ynb}
C {devices/lab_pin.sym} 1890 -640 0 0 {name=l40 lab=ynb}
C {devices/lab_pin.sym} 1890 -380 0 0 {name=l41 lab=ynb}
C {devices/lab_pin.sym} 1970 -590 0 0 {name=l42 lab=nb}
C {devices/lab_pin.sym} 2040 -540 0 1 {name=l43 lab=qb}
C {devices/lab_pin.sym} 2080 -380 0 0 {name=l44 lab=qb}
C {devices/lab_wire.sym} 1780 -450 0 0 {name=l45 lab=qb}
N 570 -160 570 -130 {}
N 420 -600 420 -630 {}
N 680 -600 680 -630 {}
N 170 -600 170 -630 {}
N 930 -600 930 -630 {}
N 170 -460 170 -490 {}
N 930 -460 930 -490 {}
N 1220 -620 1220 -650 {}
N 1220 -500 1220 -470 {}
N 1220 -340 1220 -370 {}
N 1220 -220 1220 -190 {}
N 1520 -640 1520 -670 {}
N 1520 -380 1520 -350 {}
N 1700 -380 1700 -350 {}
N 1970 -640 1970 -670 {}
N 1970 -380 1970 -350 {}
N 2150 -380 2150 -350 {}
N 420 -570 420 -490 {}
N 420 -430 420 -330 {}
N 680 -570 680 -490 {}
N 680 -430 680 -330 {}
N 380 -600 380 -460 {}
N 720 -600 720 -460 {}
N 380 -530 680 -530 {}
N 420 -510 720 -510 {}
N 420 -270 420 -230 {}
N 420 -230 680 -230 {}
N 680 -230 680 -270 {}
N 570 -190 570 -230 {}
N 60 -380 300 -380 {}
N 300 -380 300 -300 {}
N 300 -300 380 -300 {}
N 720 -300 760 -300 {}
N 60 -160 530 -160 {}
N 170 -570 170 -550 {}
N 130 -600 100 -600 {}
N 170 -430 170 -410 {}
N 130 -460 100 -460 {}
N 930 -570 930 -550 {}
N 970 -600 1000 -600 {}
N 930 -430 930 -410 {}
N 970 -460 1000 -460 {}
N 170 -490 170 -510 {}
N 930 -490 930 -510 {}
N 970 -300 1000 -300 {}
N 130 -300 100 -300 {}
N 170 -330 170 -350 {}
N 170 -270 170 -250 {}
N 930 -330 930 -350 {}
N 930 -270 930 -250 {}
N 1180 -620 1180 -500 {}
N 1220 -590 1220 -530 {}
N 1180 -560 1140 -560 {}
N 1180 -340 1180 -220 {}
N 1220 -310 1220 -250 {}
N 1180 -280 1140 -280 {}
N 1220 -370 1220 -390 {}
N 1220 -470 1220 -450 {}
N 1220 -560 1460 -560 {}
N 1480 -640 1460 -640 {}
N 1460 -640 1460 -380 {}
N 1460 -380 1480 -380 {}
N 1520 -610 1520 -570 {}
N 1520 -510 1520 -410 {}
N 1520 -450 1700 -450 {}
N 1700 -450 1700 -410 {}
N 1560 -540 1590 -540 {}
N 1660 -380 1630 -380 {}
N 1220 -280 1420 -280 {}
N 1930 -640 1890 -640 {}
N 1930 -380 1890 -380 {}
N 1970 -610 1970 -570 {}
N 1970 -510 1970 -410 {}
N 1970 -450 2150 -450 {}
N 2150 -450 2150 -410 {}
N 2010 -540 2040 -540 {}
N 2110 -380 2080 -380 {}
N 1700 -450 1800 -450 {}
N 2150 -450 2260 -450 {}
N 1800 -450 1800 -250 {}
N 170 -630 170 -700 {}
N 420 -630 420 -700 {}
N 680 -630 680 -700 {}
N 930 -630 930 -700 {}
N 1220 -650 1220 -700 {}
N 1520 -670 1520 -700 {}
N 1970 -670 1970 -700 {}
N 100 -700 1970 -700 {}
N 570 -130 570 -90 {}
N 1220 -190 1220 -90 {}
N 1520 -350 1520 -90 {}
N 1700 -350 1700 -90 {}
N 1970 -350 1970 -90 {}
N 2150 -350 2150 -90 {}
N 100 -90 2150 -90 {}

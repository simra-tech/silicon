v {xschem version=3.4.8RC file_version=1.3}
G {}
K {}
V {}
S {}
E {}
B 4 140 -900 580 -120 {dash=5 fill=false}
B 4 620 -700 980 -40 {dash=5 fill=false}
B 4 1020 -900 1250 -120 {dash=5 fill=false}
B 4 1300 -1010 2000 -120 {dash=5 fill=false}
B 4 100 -1300 1900 -1148 {fill=false}
T {RC timing branches A / B (5-bit trim)} 148 -894 0 0 0.3 0.3 {layer=4}
T {threshold vdd/2 + bias} 628 -694 0 0 0.3 0.3 {layer=4}
T {comparators} 1028 -894 0 0 0.3 0.3 {layer=4}
T {SR latch, reset switches, clock out} 1308 -1004 0 0 0.3 0.3 {layer=4}
T {q=1: A charges through RA (rsta=0), B held at 0 (rstb=1). va > vdd/2 -> ca=1 -> q=0, B charges. en=0 -> q=0, both banks held, osc_clk=0.} 140 10 0 0 0.3 0.3 {}
T {Half period = R C ln2 + comparator/latch delay; the threshold is a fixed fraction of vdd.} 140 28 0 0 0.3 0.3 {}
T {Simulated values: see ../README.md (schematic level, not measured).} 140 46 0 0 0.3 0.3 {}
T {r1_osc - 1.2 V ping-pong RC relaxation oscillator, 30 MHz nominal, 5-bit trim} 112 -1290 0 0 0.55 0.55 {}
T {G1 guardian, chip of record g1_chip_top_1414_r2.gds 9049e87b (r2 2026-09-25; geometry XOR-identical to r1 629d303a); block map: g1_padring/reports/signoff-1414-20260924} 112 -1251 0 0 0.3 0.3 {}
T {On-chip variant: R1 30 MHz re-tune of G1 g1_osc R0.95 (5-bit trim, tail x2)} 112 -1227 0 0 0.3 0.3 {}
T {Netlist-equivalent to schematic/r1_osc.spice (gen_r1_osc.py revision r2)} 112 -1203 0 0 0.3 0.3 {}
T {Drawn 2026-09-25 by the block generator; device sizes (w, l, ng, m) are on each symbol. Proof: review/schematics-readability-20260925} 112 -1179 0 0 0.25 0.25 {}
C {sg13g2_pr/rppd.sym} 200 -800 0 0 {name=RA w=1u l=48.3u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 200 -420 0 0 {name=RB w=1u l=48.3u model=rppd b=0 m=1}
C {r1_osc_cbank.sym} 320 -620 0 0 {name=XCA }
C {r1_osc_cbank.sym} 320 -240 0 0 {name=XCB }
C {sg13g2_pr/sg13_lv_nmos.sym} 480 -640 0 0 {name=MRA model=sg13_lv_nmos w=4u l=0.13u ng=1 m=1}
C {sg13g2_pr/sg13_lv_nmos.sym} 480 -260 0 0 {name=MRB model=sg13_lv_nmos w=4u l=0.13u ng=1 m=1}
C {sg13g2_pr/rppd.sym} 700 -620 0 0 {name=RT1 w=1u l=384.3u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 700 -460 0 0 {name=RT2 w=1u l=384.3u model=rppd b=0 m=1}
C {sg13g2_pr/cap_cmim.sym} 800 -460 0 0 {name=CTH model=cap_cmim w=26u l=26u m=1}
C {sg13g2_pr/dpantenna.sym} 900 -460 2 0 {name=DANT model=dpantenna l=0.78u w=0.78u}
C {sg13g2_pr/rppd.sym} 860 -230 0 0 {name=RBIAS w=1u l=80u model=rppd b=0 m=1}
C {sg13g2_pr/sg13_lv_nmos.sym} 880 -110 0 1 {name=MBD model=sg13_lv_nmos w=2u l=0.5u ng=1 m=1}
C {r1_osc_cmp.sym} 1150 -720 0 0 {name=XCMPA }
C {r1_osc_cmp.sym} 1150 -340 0 0 {name=XCMPB }
C {r1_osc_inv.sym} 1400 -900 0 0 {name=XEN }
C {r1_osc_nor3.sym} 1450 -720 0 0 {name=XNQ }
C {r1_osc_nor2.sym} 1450 -470 0 0 {name=XNQB }
C {r1_osc_nand2.sym} 1450 -260 0 0 {name=XRSTB }
C {r1_osc_inv.sym} 1720 -900 0 0 {name=XRSTA }
C {r1_osc_inv.sym} 1720 -720 0 0 {name=XB1 }
C {r1_osc_buf4.sym} 1880 -720 0 0 {name=XB2 }
C {devices/ipin.sym} 1260 -900 0 0 {name=p0 lab=en}
C {devices/ipin.sym} 100 -1025 0 0 {name=p1 lab=trim0}
C {devices/ipin.sym} 100 -1000 0 0 {name=p2 lab=trim1}
C {devices/ipin.sym} 100 -975 0 0 {name=p3 lab=trim2}
C {devices/ipin.sym} 100 -950 0 0 {name=p4 lab=trim3}
C {devices/ipin.sym} 100 -925 0 0 {name=p5 lab=trim4}
C {devices/opin.sym} 2060 -720 0 0 {name=p6 lab=osc_clk}
C {devices/iopin.sym} 100 -890 0 0 {name=p7 lab=vdd}
C {devices/iopin.sym} 100 -865 0 0 {name=p8 lab=vss}
C {devices/lab_pin.sym} 320 -720 0 1 {name=l1 lab=va}
C {devices/lab_pin.sym} 320 -520 0 1 {name=l2 lab=vss}
C {devices/lab_pin.sym} 320 -340 0 1 {name=l3 lab=vb}
C {devices/lab_pin.sym} 320 -140 0 1 {name=l4 lab=vss}
C {devices/lab_pin.sym} 1130 -650 0 0 {name=l5 lab=vbn}
C {devices/lab_pin.sym} 1150 -790 0 1 {name=l6 lab=vdd}
C {devices/lab_pin.sym} 1170 -650 0 1 {name=l7 lab=vss}
C {devices/lab_pin.sym} 1130 -270 0 0 {name=l8 lab=vbn}
C {devices/lab_pin.sym} 1150 -410 0 1 {name=l9 lab=vdd}
C {devices/lab_pin.sym} 1170 -270 0 1 {name=l10 lab=vss}
C {devices/lab_pin.sym} 1400 -970 0 1 {name=l11 lab=vdd}
C {devices/lab_pin.sym} 1400 -830 0 1 {name=l12 lab=vss}
C {devices/lab_pin.sym} 1450 -800 0 1 {name=l13 lab=vdd}
C {devices/lab_pin.sym} 1450 -640 0 1 {name=l14 lab=vss}
C {devices/lab_pin.sym} 1450 -540 0 1 {name=l15 lab=vdd}
C {devices/lab_pin.sym} 1450 -400 0 1 {name=l16 lab=vss}
C {devices/lab_pin.sym} 1450 -330 0 1 {name=l17 lab=vdd}
C {devices/lab_pin.sym} 1450 -190 0 1 {name=l18 lab=vss}
C {devices/lab_pin.sym} 1720 -970 0 1 {name=l19 lab=vdd}
C {devices/lab_pin.sym} 1720 -830 0 1 {name=l20 lab=vss}
C {devices/lab_pin.sym} 1720 -790 0 1 {name=l21 lab=vdd}
C {devices/lab_pin.sym} 1720 -650 0 1 {name=l22 lab=vss}
C {devices/lab_pin.sym} 1880 -790 0 1 {name=l23 lab=vdd}
C {devices/lab_pin.sym} 1880 -650 0 1 {name=l24 lab=vss}
C {devices/lab_pin.sym} 200 -850 0 0 {name=l25 lab=vdd}
C {devices/lab_wire.sym} 620 -730 0 0 {name=l26 lab=va}
C {devices/lab_pin.sym} 230 -660 0 0 {name=l27 lab=trim0}
C {devices/lab_pin.sym} 230 -640 0 0 {name=l28 lab=trim1}
C {devices/lab_pin.sym} 230 -620 0 0 {name=l29 lab=trim2}
C {devices/lab_pin.sym} 230 -600 0 0 {name=l30 lab=trim3}
C {devices/lab_pin.sym} 230 -580 0 0 {name=l31 lab=trim4}
C {devices/lab_pin.sym} 200 -470 0 0 {name=l32 lab=vdd}
C {devices/lab_wire.sym} 620 -350 0 0 {name=l33 lab=vb}
C {devices/lab_pin.sym} 230 -280 0 0 {name=l34 lab=trim0}
C {devices/lab_pin.sym} 230 -260 0 0 {name=l35 lab=trim1}
C {devices/lab_pin.sym} 230 -240 0 0 {name=l36 lab=trim2}
C {devices/lab_pin.sym} 230 -220 0 0 {name=l37 lab=trim3}
C {devices/lab_pin.sym} 230 -200 0 0 {name=l38 lab=trim4}
C {devices/lab_pin.sym} 420 -640 0 0 {name=l39 lab=rsta}
C {devices/lab_pin.sym} 420 -260 0 0 {name=l40 lab=rstb}
C {devices/lab_pin.sym} 500 -590 0 0 {name=l41 lab=vss}
C {devices/lab_pin.sym} 500 -210 0 0 {name=l42 lab=vss}
C {devices/lab_pin.sym} 700 -670 0 0 {name=l43 lab=vdd}
C {devices/lab_pin.sym} 700 -410 0 0 {name=l44 lab=vss}
C {devices/lab_pin.sym} 800 -410 0 0 {name=l45 lab=vss}
C {devices/lab_pin.sym} 900 -410 0 0 {name=l46 lab=vdd}
C {devices/lab_wire.sym} 990 -540 0 0 {name=l47 lab=vth}
C {devices/lab_pin.sym} 860 -280 0 0 {name=l48 lab=vdd}
C {devices/lab_pin.sym} 860 -60 0 0 {name=l49 lab=vss}
C {devices/lab_wire.sym} 960 -170 0 0 {name=l50 lab=vbn}
C {devices/lab_wire.sym} 1300 -720 0 0 {name=l51 lab=ca}
C {devices/lab_wire.sym} 1290 -340 0 0 {name=l52 lab=cb}
C {devices/lab_wire.sym} 1520 -900 0 0 {name=l53 lab=en_n}
C {devices/lab_pin.sym} 1350 -720 0 0 {name=l54 lab=en_n}
C {devices/lab_pin.sym} 1350 -700 0 0 {name=l55 lab=qb}
C {devices/lab_pin.sym} 1350 -460 0 0 {name=l56 lab=q}
C {devices/lab_pin.sym} 1350 -270 0 0 {name=l57 lab=qb}
C {devices/lab_pin.sym} 1350 -250 0 0 {name=l58 lab=en}
C {devices/lab_wire.sym} 1560 -720 0 0 {name=l59 lab=q}
C {devices/lab_wire.sym} 1600 -470 0 0 {name=l60 lab=qb}
C {devices/lab_wire.sym} 1600 -260 0 0 {name=l61 lab=rstb}
C {devices/lab_wire.sym} 1840 -900 0 0 {name=l62 lab=rsta}
C {devices/lab_wire.sym} 1805 -720 0 0 {name=l63 lab=qn_b}
N 500 -640 500 -610 {}
N 500 -260 500 -230 {}
N 860 -110 860 -80 {}
N 320 -700 320 -720 {}
N 320 -540 320 -520 {}
N 320 -320 320 -340 {}
N 320 -160 320 -140 {}
N 1130 -670 1130 -650 {}
N 1150 -770 1150 -790 {}
N 1170 -670 1170 -650 {}
N 1130 -290 1130 -270 {}
N 1150 -390 1150 -410 {}
N 1170 -290 1170 -270 {}
N 1400 -950 1400 -970 {}
N 1400 -850 1400 -830 {}
N 1450 -780 1450 -800 {}
N 1450 -660 1450 -640 {}
N 1450 -520 1450 -540 {}
N 1450 -420 1450 -400 {}
N 1450 -310 1450 -330 {}
N 1450 -210 1450 -190 {}
N 1720 -950 1720 -970 {}
N 1720 -850 1720 -830 {}
N 1720 -770 1720 -790 {}
N 1720 -670 1720 -650 {}
N 1880 -770 1880 -790 {}
N 1880 -670 1880 -650 {}
N 200 -830 200 -850 {}
N 200 -770 200 -730 {}
N 200 -730 500 -730 {}
N 500 -730 500 -670 {}
N 320 -700 320 -730 {}
N 500 -730 1040 -730 {}
N 1040 -730 1080 -730 {}
N 260 -660 230 -660 {}
N 260 -640 230 -640 {}
N 260 -620 230 -620 {}
N 260 -600 230 -600 {}
N 260 -580 230 -580 {}
N 200 -450 200 -470 {}
N 200 -390 200 -350 {}
N 200 -350 500 -350 {}
N 500 -350 500 -290 {}
N 320 -320 320 -350 {}
N 500 -350 1040 -350 {}
N 1040 -350 1080 -350 {}
N 260 -280 230 -280 {}
N 260 -260 230 -260 {}
N 260 -240 230 -240 {}
N 260 -220 230 -220 {}
N 260 -200 230 -200 {}
N 460 -640 420 -640 {}
N 460 -260 420 -260 {}
N 500 -610 500 -590 {}
N 500 -230 500 -210 {}
N 700 -650 700 -670 {}
N 700 -590 700 -490 {}
N 700 -430 700 -410 {}
N 700 -540 900 -540 {}
N 900 -540 900 -490 {}
N 800 -540 800 -490 {}
N 800 -430 800 -410 {}
N 900 -430 900 -410 {}
N 900 -540 1000 -540 {}
N 1000 -540 1000 -710 {}
N 1000 -710 1080 -710 {}
N 1000 -540 1000 -330 {}
N 1000 -330 1080 -330 {}
N 860 -260 860 -280 {}
N 860 -200 860 -140 {}
N 900 -110 900 -170 {}
N 900 -170 860 -170 {}
N 900 -170 960 -170 {}
N 860 -80 860 -60 {}
N 1220 -720 1300 -720 {}
N 1300 -720 1300 -740 {}
N 1300 -740 1390 -740 {}
N 1220 -340 1300 -340 {}
N 1300 -340 1300 -480 {}
N 1300 -480 1390 -480 {}
N 1260 -900 1340 -900 {}
N 1460 -900 1520 -900 {}
N 1390 -720 1350 -720 {}
N 1390 -700 1350 -700 {}
N 1390 -460 1350 -460 {}
N 1390 -270 1350 -270 {}
N 1390 -250 1350 -250 {}
N 1510 -720 1600 -720 {}
N 1600 -720 1600 -900 {}
N 1600 -900 1660 -900 {}
N 1600 -720 1660 -720 {}
N 1510 -470 1600 -470 {}
N 1510 -260 1600 -260 {}
N 1780 -900 1840 -900 {}
N 1780 -720 1820 -720 {}
N 1940 -720 2060 -720 {}

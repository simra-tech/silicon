v {xschem version=3.4.8RC file_version=1.3}
G {}
K {}
V {}
S {}
E {}
B 4 170 -800 560 -620 {dash=5 fill=false}
B 4 590 -800 800 -220 {dash=5 fill=false}
B 4 860 -800 1360 -220 {dash=5 fill=false}
B 4 1380 -800 1740 -300 {dash=5 fill=false}
B 4 1760 -800 2440 -300 {dash=5 fill=false}
B 4 120 -1020 1920 -868 {fill=false}
T {1.2 V fast-path AND} 178 -794 0 0 0.3 0.3 {layer=4}
T {1.2 -> 3.3 V} 598 -794 0 0 0.3 0.3 {layer=4}
T {3.3 V set / reset} 868 -794 0 0 0.3 0.3 {layer=4}
T {SR latch, reset dominant} 1388 -794 0 0 0.3 0.3 {layer=4}
T {gate enable + 3.3 -> 1.2 V} 1768 -794 0 0 0.3 0.3 {layer=4}
T {set = trip_d | (hard_cmp & fast_en)     reset = !en_core | clr_d     q = tripped, held in 3.3 V thick-oxide logic} 170 -180 0 0 0.3 0.3 {}
T {gate_core = en_core & !q ; fault_core = !q ; power-up: en_core = 0 forces gate_core = 0} 170 -162 0 0 0.3 0.3 {}
T {Chip level (simulated, chip netlists tt/27 C): pad GATE < 1 V 1.345 us after a hard fault (g1_top RESULTS_20260925)} 170 -144 0 0 0.3 0.3 {}
T {g1_gate - latch-up guardian gate driver: 3.3 V SR latch between 1.2 V level shifters} 132 -1010 0 0 0.55 0.55 {}
T {G1 guardian, chip of record g1_chip_top_1414_r2.gds 9049e87b (r2 2026-09-25; geometry XOR-identical to r1 629d303a); block map: g1_padring/reports/signoff-1414-20260924} 132 -971 0 0 0.3 0.3 {}
T {On-chip variant: baseline (chip cell retained_g1_gate = layout/g1_gate.gds ddf2c44a; LVS reference layout/g1_gate.cdl 27548c03)} 132 -947 0 0 0.3 0.3 {}
T {Netlist-equivalent to sim/netlist/g1_gate.spice sha256 846a55e0} 132 -923 0 0 0.3 0.3 {}
T {Drawn 2026-09-25 by the block generator; device sizes (w, l, ng, m) are on each symbol. Proof: review/schematics-readability-20260925} 132 -899 0 0 0.25 0.25 {}
C {g1_lv_nand2.sym} 300 -700 0 0 {name=XNA }
C {g1_lv_inv.sym} 480 -700 0 0 {name=XIA }
C {g1_lvlup.sym} 700 -700 0 0 {name=XU0 }
C {g1_lvlup.sym} 700 -560 0 0 {name=XU1 }
C {g1_lvlup.sym} 700 -420 0 0 {name=XU2 }
C {g1_lvlup.sym} 700 -280 0 0 {name=XU3 }
C {g1_hv_nor2.sym} 950 -630 0 0 {name=XN1 }
C {g1_hv_inv.sym} 1110 -630 0 0 {name=XI1 }
C {g1_hv_inv.sym} 950 -280 0 0 {name=XI2 }
C {g1_hv_nor2.sym} 1110 -430 0 0 {name=XN2 }
C {g1_hv_inv.sym} 1270 -430 0 0 {name=XI3 }
C {g1_hv_nor2.sym} 1550 -420 0 0 {name=XL1 }
C {g1_hv_nor2.sym} 1550 -640 0 0 {name=XL2 }
C {g1_hv_nor2.sym} 1850 -700 0 0 {name=XG }
C {g1_hv_inv.sym} 2010 -700 0 0 {name=XGI }
C {g1_lvldn.sym} 2300 -700 0 0 {name=XD1 }
C {g1_lvldn.sym} 2300 -540 0 0 {name=XD2 }
C {g1_lvldn.sym} 2300 -380 0 0 {name=XD3 }
C {devices/ipin.sym} 100 -560 0 0 {name=p0 lab=trip_d}
C {devices/ipin.sym} 100 -420 0 0 {name=p1 lab=clr_d}
C {devices/ipin.sym} 100 -670 0 0 {name=p2 lab=fast_en}
C {devices/ipin.sym} 100 -740 0 0 {name=p3 lab=hard_cmp}
C {devices/ipin.sym} 100 -280 0 0 {name=p4 lab=en_core}
C {devices/opin.sym} 2480 -700 0 0 {name=p5 lab=gate_core}
C {devices/opin.sym} 2480 -540 0 0 {name=p6 lab=fault_core}
C {devices/opin.sym} 2480 -380 0 0 {name=p7 lab=tripped}
C {devices/iopin.sym} 100 -120 0 0 {name=p8 lab=vdd}
C {devices/iopin.sym} 100 -90 0 0 {name=p9 lab=vdda}
C {devices/iopin.sym} 100 -60 0 0 {name=p10 lab=vss}
C {devices/lab_pin.sym} 300 -770 0 1 {name=l1 lab=vdd}
C {devices/lab_pin.sym} 300 -630 0 1 {name=l2 lab=vss}
C {devices/lab_pin.sym} 480 -770 0 1 {name=l3 lab=vdd}
C {devices/lab_pin.sym} 480 -630 0 1 {name=l4 lab=vss}
C {devices/lab_pin.sym} 680 -770 0 0 {name=l5 lab=vdd}
C {devices/lab_pin.sym} 720 -770 0 1 {name=l6 lab=vdda}
C {devices/lab_pin.sym} 700 -630 0 1 {name=l7 lab=vss}
C {devices/lab_pin.sym} 680 -630 0 0 {name=l8 lab=vdd}
C {devices/lab_pin.sym} 720 -630 0 1 {name=l9 lab=vdda}
C {devices/lab_pin.sym} 700 -490 0 1 {name=l10 lab=vss}
C {devices/lab_pin.sym} 680 -490 0 0 {name=l11 lab=vdd}
C {devices/lab_pin.sym} 720 -490 0 1 {name=l12 lab=vdda}
C {devices/lab_pin.sym} 700 -350 0 1 {name=l13 lab=vss}
C {devices/lab_pin.sym} 680 -350 0 0 {name=l14 lab=vdd}
C {devices/lab_pin.sym} 720 -350 0 1 {name=l15 lab=vdda}
C {devices/lab_pin.sym} 700 -210 0 1 {name=l16 lab=vss}
C {devices/lab_pin.sym} 950 -700 0 1 {name=l17 lab=vdda}
C {devices/lab_pin.sym} 950 -560 0 1 {name=l18 lab=vss}
C {devices/lab_pin.sym} 1110 -700 0 1 {name=l19 lab=vdda}
C {devices/lab_pin.sym} 1110 -560 0 1 {name=l20 lab=vss}
C {devices/lab_pin.sym} 950 -350 0 1 {name=l21 lab=vdda}
C {devices/lab_pin.sym} 950 -210 0 1 {name=l22 lab=vss}
C {devices/lab_pin.sym} 1110 -500 0 1 {name=l23 lab=vdda}
C {devices/lab_pin.sym} 1110 -360 0 1 {name=l24 lab=vss}
C {devices/lab_pin.sym} 1270 -500 0 1 {name=l25 lab=vdda}
C {devices/lab_pin.sym} 1270 -360 0 1 {name=l26 lab=vss}
C {devices/lab_pin.sym} 1550 -490 0 1 {name=l27 lab=vdda}
C {devices/lab_pin.sym} 1550 -350 0 1 {name=l28 lab=vss}
C {devices/lab_pin.sym} 1550 -710 0 1 {name=l29 lab=vdda}
C {devices/lab_pin.sym} 1550 -570 0 1 {name=l30 lab=vss}
C {devices/lab_pin.sym} 1850 -770 0 1 {name=l31 lab=vdda}
C {devices/lab_pin.sym} 1850 -630 0 1 {name=l32 lab=vss}
C {devices/lab_pin.sym} 2010 -770 0 1 {name=l33 lab=vdda}
C {devices/lab_pin.sym} 2010 -630 0 1 {name=l34 lab=vss}
C {devices/lab_pin.sym} 2300 -770 0 1 {name=l35 lab=vdd}
C {devices/lab_pin.sym} 2300 -630 0 1 {name=l36 lab=vss}
C {devices/lab_pin.sym} 2300 -610 0 1 {name=l37 lab=vdd}
C {devices/lab_pin.sym} 2300 -470 0 1 {name=l38 lab=vss}
C {devices/lab_pin.sym} 2300 -450 0 1 {name=l39 lab=vdd}
C {devices/lab_pin.sym} 2300 -310 0 1 {name=l40 lab=vss}
C {devices/lab_wire.sym} 410 -700 0 0 {name=l41 lab=fast_n}
C {devices/lab_wire.sym} 620 -700 0 0 {name=l42 lab=fast}
C {devices/lab_wire.sym} 820 -700 0 0 {name=l43 lab=fast_h}
C {devices/lab_wire.sym} 840 -560 0 0 {name=l44 lab=trip_h}
C {devices/lab_wire.sym} 980 -420 0 0 {name=l45 lab=clr_h}
C {devices/lab_wire.sym} 870 -280 0 0 {name=l46 lab=en_h}
C {devices/lab_wire.sym} 1045 -630 0 0 {name=l47 lab=set_n}
C {devices/lab_wire.sym} 1090 -280 0 0 {name=l48 lab=en_hn}
C {devices/lab_pin.sym} 1010 -440 0 0 {name=l49 lab=en_hn}
C {devices/lab_wire.sym} 1205 -430 0 0 {name=l50 lab=rst_n}
C {devices/lab_wire.sym} 1300 -630 0 0 {name=l51 lab=set}
C {devices/lab_wire.sym} 1390 -430 0 0 {name=l52 lab=rst}
C {devices/lab_wire.sym} 1720 -420 0 0 {name=l53 lab=q}
C {devices/lab_wire.sym} 1720 -640 0 0 {name=l54 lab=qb}
C {devices/lab_pin.sym} 1750 -710 0 0 {name=l55 lab=en_hn}
C {devices/lab_pin.sym} 1750 -690 0 0 {name=l56 lab=q}
C {devices/lab_wire.sym} 2150 -760 0 0 {name=l57 lab=gate_h}
C {devices/lab_wire.sym} 2160 -700 0 0 {name=l58 lab=gate_hn}
C {devices/lab_pin.sym} 2200 -550 0 0 {name=l59 lab=qb}
C {devices/lab_pin.sym} 2200 -530 0 0 {name=l60 lab=q}
C {devices/lab_pin.sym} 2200 -390 0 0 {name=l61 lab=q}
C {devices/lab_pin.sym} 2200 -370 0 0 {name=l62 lab=qb}
N 300 -750 300 -770 {}
N 300 -650 300 -630 {}
N 480 -750 480 -770 {}
N 480 -650 480 -630 {}
N 680 -750 680 -770 {}
N 720 -750 720 -770 {}
N 700 -650 700 -630 {}
N 680 -610 680 -630 {}
N 720 -610 720 -630 {}
N 700 -510 700 -490 {}
N 680 -470 680 -490 {}
N 720 -470 720 -490 {}
N 700 -370 700 -350 {}
N 680 -330 680 -350 {}
N 720 -330 720 -350 {}
N 700 -230 700 -210 {}
N 950 -680 950 -700 {}
N 950 -580 950 -560 {}
N 1110 -680 1110 -700 {}
N 1110 -580 1110 -560 {}
N 950 -330 950 -350 {}
N 950 -230 950 -210 {}
N 1110 -480 1110 -500 {}
N 1110 -380 1110 -360 {}
N 1270 -480 1270 -500 {}
N 1270 -380 1270 -360 {}
N 1550 -470 1550 -490 {}
N 1550 -370 1550 -350 {}
N 1550 -690 1550 -710 {}
N 1550 -590 1550 -570 {}
N 1850 -750 1850 -770 {}
N 1850 -650 1850 -630 {}
N 2010 -750 2010 -770 {}
N 2010 -650 2010 -630 {}
N 2300 -750 2300 -770 {}
N 2300 -650 2300 -630 {}
N 2300 -590 2300 -610 {}
N 2300 -490 2300 -470 {}
N 2300 -430 2300 -450 {}
N 2300 -330 2300 -310 {}
N 100 -560 630 -560 {}
N 100 -420 630 -420 {}
N 100 -670 200 -670 {}
N 200 -670 200 -690 {}
N 200 -690 240 -690 {}
N 100 -740 200 -740 {}
N 200 -740 200 -710 {}
N 200 -710 240 -710 {}
N 100 -280 630 -280 {}
N 360 -700 420 -700 {}
N 540 -700 630 -700 {}
N 770 -700 830 -700 {}
N 830 -700 830 -640 {}
N 830 -640 890 -640 {}
N 770 -560 850 -560 {}
N 850 -560 850 -620 {}
N 850 -620 890 -620 {}
N 770 -420 1050 -420 {}
N 770 -280 890 -280 {}
N 1010 -630 1050 -630 {}
N 1010 -280 1090 -280 {}
N 1050 -440 1010 -440 {}
N 1170 -430 1210 -430 {}
N 1170 -630 1400 -630 {}
N 1400 -630 1400 -650 {}
N 1400 -650 1490 -650 {}
N 1330 -430 1490 -430 {}
N 1610 -420 1640 -420 {}
N 1640 -420 1640 -530 {}
N 1640 -530 1460 -530 {}
N 1460 -530 1460 -630 {}
N 1460 -630 1490 -630 {}
N 1610 -640 1680 -640 {}
N 1680 -640 1680 -320 {}
N 1680 -320 1440 -320 {}
N 1440 -320 1440 -410 {}
N 1440 -410 1490 -410 {}
N 1640 -420 1720 -420 {}
N 1680 -640 1720 -640 {}
N 1790 -710 1750 -710 {}
N 1790 -690 1750 -690 {}
N 1910 -700 1950 -700 {}
N 1930 -700 1930 -760 {}
N 1930 -760 2200 -760 {}
N 2200 -760 2200 -710 {}
N 2200 -710 2240 -710 {}
N 2070 -700 2220 -700 {}
N 2220 -700 2220 -690 {}
N 2220 -690 2240 -690 {}
N 2240 -550 2200 -550 {}
N 2240 -530 2200 -530 {}
N 2240 -390 2200 -390 {}
N 2240 -370 2200 -370 {}
N 2360 -700 2480 -700 {}
N 2360 -540 2480 -540 {}
N 2360 -380 2480 -380 {}

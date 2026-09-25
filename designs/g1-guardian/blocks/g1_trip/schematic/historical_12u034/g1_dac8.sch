v {xschem version=3.4.8RC file_version=1.3}
G {}
K {}
V {}
S {}
E {}
B 4 40 -3330 1700 -3180 {dash=5 fill=false}
B 4 40 -3060 2460 -1850 {dash=5 fill=false}
B 4 40 -1680 3300 1200 {dash=5 fill=false}
B 4 40 -3700 2440 -3548 {fill=false}
T {8 code-bit level shifters: d_b (1.2 V) -> dh_b / dhn_b (3.3 V)} 48 -3324 0 0 0.3 0.3 {layer=4}
T {resistor string: 530 x rppd 4u/1.2u from vref (top) to vss; taps t0..t255 = units 255..510} 48 -3054 0 0 0.3 0.3 {layer=4}
T {binary tree of thick-oxide NMOS switches, level b (row block b) selected by dh_b / dhn_b} 48 -1674 0 0 0.3 0.3 {layer=4}
T {out = VREF*(255+code)/530 ; code 0 -> 0.5004 V, 255 -> 1.0008 V at VREF=1.04 V; LSB 1.962 mV (VREF/530).} 40 1260 0 0 0.3 0.3 {}
T {Shunt-referred threshold = code x 0.1962 mV x (VREF/1.04 V) (gain 20, divider 1/2). With the BGR586 VREF 1.04546 V (simulated), code 200 = 39.45 mV.} 40 1278 0 0 0.3 0.3 {}
T {g1_dac8 - 8-bit rppd string DAC from VREF with a 3.3 V-driven NMOS binary tree} 52 -3690 0 0 0.55 0.55 {}
T {G1 guardian, chip of record g1_chip_top_1414_r2.gds 9049e87b (r2 2026-09-25; geometry XOR-identical to r1 629d303a); block map: g1_padring/reports/signoff-1414-20260924} 52 -3651 0 0 0.3 0.3 {}
T {On-chip variant: HISTORICAL 12u/0.34u comparators, NOT on the chip (chip-of-record sheets: ../, G1_TRIP_VARIANT=chip); netlists ../../sim/netlist/*.spice} 52 -3627 0 0 0.3 0.3 {}
T {Netlist-equivalent to sim/netlist/g1_dac8.spice sha256 9f967559} 52 -3603 0 0 0.3 0.3 {}
T {Drawn 2026-09-25 by the block generator; device sizes (w, l, ng, m) are on each symbol. Proof: review/schematics-readability-20260925} 52 -3579 0 0 0.25 0.25 {}
C {sg13g2_pr/rppd.sym} 100 -3000 0 0 {name=RU0 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 160 -3000 0 0 {name=RU1 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 220 -3000 0 0 {name=RU2 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 280 -3000 0 0 {name=RU3 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 340 -3000 0 0 {name=RU4 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 400 -3000 0 0 {name=RU5 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 460 -3000 0 0 {name=RU6 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 520 -3000 0 0 {name=RU7 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 580 -3000 0 0 {name=RU8 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 640 -3000 0 0 {name=RU9 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 700 -3000 0 0 {name=RU10 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 760 -3000 0 0 {name=RU11 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 820 -3000 0 0 {name=RU12 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 880 -3000 0 0 {name=RU13 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 940 -3000 0 0 {name=RU14 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1000 -3000 0 0 {name=RU15 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1060 -3000 0 0 {name=RU16 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1120 -3000 0 0 {name=RU17 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1180 -3000 0 0 {name=RU18 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1240 -3000 0 0 {name=RU19 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1300 -3000 0 0 {name=RU20 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1360 -3000 0 0 {name=RU21 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1420 -3000 0 0 {name=RU22 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1480 -3000 0 0 {name=RU23 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1540 -3000 0 0 {name=RU24 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1600 -3000 0 0 {name=RU25 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1660 -3000 0 0 {name=RU26 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1720 -3000 0 0 {name=RU27 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1780 -3000 0 0 {name=RU28 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1840 -3000 0 0 {name=RU29 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1900 -3000 0 0 {name=RU30 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1960 -3000 0 0 {name=RU31 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2020 -3000 0 0 {name=RU32 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2080 -3000 0 0 {name=RU33 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2140 -3000 0 0 {name=RU34 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2200 -3000 0 0 {name=RU35 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2260 -3000 0 0 {name=RU36 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2320 -3000 0 0 {name=RU37 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2380 -3000 0 0 {name=RU38 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2440 -3000 0 0 {name=RU39 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 100 -2920 0 0 {name=RU40 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 160 -2920 0 0 {name=RU41 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 220 -2920 0 0 {name=RU42 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 280 -2920 0 0 {name=RU43 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 340 -2920 0 0 {name=RU44 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 400 -2920 0 0 {name=RU45 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 460 -2920 0 0 {name=RU46 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 520 -2920 0 0 {name=RU47 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 580 -2920 0 0 {name=RU48 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 640 -2920 0 0 {name=RU49 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 700 -2920 0 0 {name=RU50 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 760 -2920 0 0 {name=RU51 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 820 -2920 0 0 {name=RU52 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 880 -2920 0 0 {name=RU53 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 940 -2920 0 0 {name=RU54 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1000 -2920 0 0 {name=RU55 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1060 -2920 0 0 {name=RU56 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1120 -2920 0 0 {name=RU57 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1180 -2920 0 0 {name=RU58 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1240 -2920 0 0 {name=RU59 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1300 -2920 0 0 {name=RU60 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1360 -2920 0 0 {name=RU61 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1420 -2920 0 0 {name=RU62 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1480 -2920 0 0 {name=RU63 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1540 -2920 0 0 {name=RU64 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1600 -2920 0 0 {name=RU65 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1660 -2920 0 0 {name=RU66 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1720 -2920 0 0 {name=RU67 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1780 -2920 0 0 {name=RU68 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1840 -2920 0 0 {name=RU69 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1900 -2920 0 0 {name=RU70 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1960 -2920 0 0 {name=RU71 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2020 -2920 0 0 {name=RU72 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2080 -2920 0 0 {name=RU73 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2140 -2920 0 0 {name=RU74 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2200 -2920 0 0 {name=RU75 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2260 -2920 0 0 {name=RU76 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2320 -2920 0 0 {name=RU77 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2380 -2920 0 0 {name=RU78 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2440 -2920 0 0 {name=RU79 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 100 -2840 0 0 {name=RU80 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 160 -2840 0 0 {name=RU81 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 220 -2840 0 0 {name=RU82 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 280 -2840 0 0 {name=RU83 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 340 -2840 0 0 {name=RU84 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 400 -2840 0 0 {name=RU85 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 460 -2840 0 0 {name=RU86 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 520 -2840 0 0 {name=RU87 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 580 -2840 0 0 {name=RU88 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 640 -2840 0 0 {name=RU89 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 700 -2840 0 0 {name=RU90 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 760 -2840 0 0 {name=RU91 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 820 -2840 0 0 {name=RU92 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 880 -2840 0 0 {name=RU93 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 940 -2840 0 0 {name=RU94 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1000 -2840 0 0 {name=RU95 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1060 -2840 0 0 {name=RU96 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1120 -2840 0 0 {name=RU97 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1180 -2840 0 0 {name=RU98 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1240 -2840 0 0 {name=RU99 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1300 -2840 0 0 {name=RU100 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1360 -2840 0 0 {name=RU101 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1420 -2840 0 0 {name=RU102 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1480 -2840 0 0 {name=RU103 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1540 -2840 0 0 {name=RU104 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1600 -2840 0 0 {name=RU105 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1660 -2840 0 0 {name=RU106 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1720 -2840 0 0 {name=RU107 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1780 -2840 0 0 {name=RU108 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1840 -2840 0 0 {name=RU109 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1900 -2840 0 0 {name=RU110 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1960 -2840 0 0 {name=RU111 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2020 -2840 0 0 {name=RU112 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2080 -2840 0 0 {name=RU113 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2140 -2840 0 0 {name=RU114 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2200 -2840 0 0 {name=RU115 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2260 -2840 0 0 {name=RU116 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2320 -2840 0 0 {name=RU117 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2380 -2840 0 0 {name=RU118 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2440 -2840 0 0 {name=RU119 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 100 -2760 0 0 {name=RU120 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 160 -2760 0 0 {name=RU121 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 220 -2760 0 0 {name=RU122 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 280 -2760 0 0 {name=RU123 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 340 -2760 0 0 {name=RU124 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 400 -2760 0 0 {name=RU125 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 460 -2760 0 0 {name=RU126 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 520 -2760 0 0 {name=RU127 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 580 -2760 0 0 {name=RU128 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 640 -2760 0 0 {name=RU129 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 700 -2760 0 0 {name=RU130 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 760 -2760 0 0 {name=RU131 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 820 -2760 0 0 {name=RU132 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 880 -2760 0 0 {name=RU133 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 940 -2760 0 0 {name=RU134 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1000 -2760 0 0 {name=RU135 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1060 -2760 0 0 {name=RU136 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1120 -2760 0 0 {name=RU137 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1180 -2760 0 0 {name=RU138 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1240 -2760 0 0 {name=RU139 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1300 -2760 0 0 {name=RU140 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1360 -2760 0 0 {name=RU141 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1420 -2760 0 0 {name=RU142 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1480 -2760 0 0 {name=RU143 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1540 -2760 0 0 {name=RU144 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1600 -2760 0 0 {name=RU145 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1660 -2760 0 0 {name=RU146 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1720 -2760 0 0 {name=RU147 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1780 -2760 0 0 {name=RU148 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1840 -2760 0 0 {name=RU149 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1900 -2760 0 0 {name=RU150 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1960 -2760 0 0 {name=RU151 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2020 -2760 0 0 {name=RU152 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2080 -2760 0 0 {name=RU153 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2140 -2760 0 0 {name=RU154 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2200 -2760 0 0 {name=RU155 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2260 -2760 0 0 {name=RU156 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2320 -2760 0 0 {name=RU157 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2380 -2760 0 0 {name=RU158 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2440 -2760 0 0 {name=RU159 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 100 -2680 0 0 {name=RU160 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 160 -2680 0 0 {name=RU161 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 220 -2680 0 0 {name=RU162 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 280 -2680 0 0 {name=RU163 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 340 -2680 0 0 {name=RU164 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 400 -2680 0 0 {name=RU165 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 460 -2680 0 0 {name=RU166 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 520 -2680 0 0 {name=RU167 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 580 -2680 0 0 {name=RU168 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 640 -2680 0 0 {name=RU169 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 700 -2680 0 0 {name=RU170 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 760 -2680 0 0 {name=RU171 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 820 -2680 0 0 {name=RU172 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 880 -2680 0 0 {name=RU173 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 940 -2680 0 0 {name=RU174 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1000 -2680 0 0 {name=RU175 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1060 -2680 0 0 {name=RU176 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1120 -2680 0 0 {name=RU177 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1180 -2680 0 0 {name=RU178 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1240 -2680 0 0 {name=RU179 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1300 -2680 0 0 {name=RU180 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1360 -2680 0 0 {name=RU181 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1420 -2680 0 0 {name=RU182 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1480 -2680 0 0 {name=RU183 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1540 -2680 0 0 {name=RU184 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1600 -2680 0 0 {name=RU185 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1660 -2680 0 0 {name=RU186 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1720 -2680 0 0 {name=RU187 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1780 -2680 0 0 {name=RU188 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1840 -2680 0 0 {name=RU189 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1900 -2680 0 0 {name=RU190 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1960 -2680 0 0 {name=RU191 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2020 -2680 0 0 {name=RU192 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2080 -2680 0 0 {name=RU193 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2140 -2680 0 0 {name=RU194 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2200 -2680 0 0 {name=RU195 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2260 -2680 0 0 {name=RU196 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2320 -2680 0 0 {name=RU197 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2380 -2680 0 0 {name=RU198 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2440 -2680 0 0 {name=RU199 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 100 -2600 0 0 {name=RU200 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 160 -2600 0 0 {name=RU201 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 220 -2600 0 0 {name=RU202 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 280 -2600 0 0 {name=RU203 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 340 -2600 0 0 {name=RU204 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 400 -2600 0 0 {name=RU205 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 460 -2600 0 0 {name=RU206 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 520 -2600 0 0 {name=RU207 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 580 -2600 0 0 {name=RU208 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 640 -2600 0 0 {name=RU209 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 700 -2600 0 0 {name=RU210 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 760 -2600 0 0 {name=RU211 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 820 -2600 0 0 {name=RU212 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 880 -2600 0 0 {name=RU213 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 940 -2600 0 0 {name=RU214 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1000 -2600 0 0 {name=RU215 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1060 -2600 0 0 {name=RU216 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1120 -2600 0 0 {name=RU217 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1180 -2600 0 0 {name=RU218 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1240 -2600 0 0 {name=RU219 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1300 -2600 0 0 {name=RU220 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1360 -2600 0 0 {name=RU221 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1420 -2600 0 0 {name=RU222 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1480 -2600 0 0 {name=RU223 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1540 -2600 0 0 {name=RU224 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1600 -2600 0 0 {name=RU225 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1660 -2600 0 0 {name=RU226 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1720 -2600 0 0 {name=RU227 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1780 -2600 0 0 {name=RU228 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1840 -2600 0 0 {name=RU229 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1900 -2600 0 0 {name=RU230 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1960 -2600 0 0 {name=RU231 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2020 -2600 0 0 {name=RU232 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2080 -2600 0 0 {name=RU233 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2140 -2600 0 0 {name=RU234 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2200 -2600 0 0 {name=RU235 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2260 -2600 0 0 {name=RU236 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2320 -2600 0 0 {name=RU237 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2380 -2600 0 0 {name=RU238 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2440 -2600 0 0 {name=RU239 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 100 -2520 0 0 {name=RU240 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 160 -2520 0 0 {name=RU241 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 220 -2520 0 0 {name=RU242 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 280 -2520 0 0 {name=RU243 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 340 -2520 0 0 {name=RU244 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 400 -2520 0 0 {name=RU245 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 460 -2520 0 0 {name=RU246 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 520 -2520 0 0 {name=RU247 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 580 -2520 0 0 {name=RU248 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 640 -2520 0 0 {name=RU249 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 700 -2520 0 0 {name=RU250 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 760 -2520 0 0 {name=RU251 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 820 -2520 0 0 {name=RU252 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 880 -2520 0 0 {name=RU253 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 940 -2520 0 0 {name=RU254 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1000 -2520 0 0 {name=RU255 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1060 -2520 0 0 {name=RU256 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1120 -2520 0 0 {name=RU257 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1180 -2520 0 0 {name=RU258 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1240 -2520 0 0 {name=RU259 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1300 -2520 0 0 {name=RU260 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1360 -2520 0 0 {name=RU261 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1420 -2520 0 0 {name=RU262 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1480 -2520 0 0 {name=RU263 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1540 -2520 0 0 {name=RU264 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1600 -2520 0 0 {name=RU265 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1660 -2520 0 0 {name=RU266 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1720 -2520 0 0 {name=RU267 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1780 -2520 0 0 {name=RU268 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1840 -2520 0 0 {name=RU269 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1900 -2520 0 0 {name=RU270 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1960 -2520 0 0 {name=RU271 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2020 -2520 0 0 {name=RU272 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2080 -2520 0 0 {name=RU273 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2140 -2520 0 0 {name=RU274 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2200 -2520 0 0 {name=RU275 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2260 -2520 0 0 {name=RU276 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2320 -2520 0 0 {name=RU277 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2380 -2520 0 0 {name=RU278 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2440 -2520 0 0 {name=RU279 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 100 -2440 0 0 {name=RU280 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 160 -2440 0 0 {name=RU281 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 220 -2440 0 0 {name=RU282 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 280 -2440 0 0 {name=RU283 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 340 -2440 0 0 {name=RU284 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 400 -2440 0 0 {name=RU285 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 460 -2440 0 0 {name=RU286 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 520 -2440 0 0 {name=RU287 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 580 -2440 0 0 {name=RU288 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 640 -2440 0 0 {name=RU289 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 700 -2440 0 0 {name=RU290 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 760 -2440 0 0 {name=RU291 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 820 -2440 0 0 {name=RU292 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 880 -2440 0 0 {name=RU293 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 940 -2440 0 0 {name=RU294 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1000 -2440 0 0 {name=RU295 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1060 -2440 0 0 {name=RU296 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1120 -2440 0 0 {name=RU297 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1180 -2440 0 0 {name=RU298 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1240 -2440 0 0 {name=RU299 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1300 -2440 0 0 {name=RU300 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1360 -2440 0 0 {name=RU301 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1420 -2440 0 0 {name=RU302 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1480 -2440 0 0 {name=RU303 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1540 -2440 0 0 {name=RU304 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1600 -2440 0 0 {name=RU305 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1660 -2440 0 0 {name=RU306 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1720 -2440 0 0 {name=RU307 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1780 -2440 0 0 {name=RU308 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1840 -2440 0 0 {name=RU309 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1900 -2440 0 0 {name=RU310 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1960 -2440 0 0 {name=RU311 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2020 -2440 0 0 {name=RU312 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2080 -2440 0 0 {name=RU313 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2140 -2440 0 0 {name=RU314 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2200 -2440 0 0 {name=RU315 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2260 -2440 0 0 {name=RU316 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2320 -2440 0 0 {name=RU317 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2380 -2440 0 0 {name=RU318 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2440 -2440 0 0 {name=RU319 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 100 -2360 0 0 {name=RU320 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 160 -2360 0 0 {name=RU321 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 220 -2360 0 0 {name=RU322 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 280 -2360 0 0 {name=RU323 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 340 -2360 0 0 {name=RU324 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 400 -2360 0 0 {name=RU325 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 460 -2360 0 0 {name=RU326 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 520 -2360 0 0 {name=RU327 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 580 -2360 0 0 {name=RU328 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 640 -2360 0 0 {name=RU329 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 700 -2360 0 0 {name=RU330 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 760 -2360 0 0 {name=RU331 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 820 -2360 0 0 {name=RU332 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 880 -2360 0 0 {name=RU333 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 940 -2360 0 0 {name=RU334 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1000 -2360 0 0 {name=RU335 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1060 -2360 0 0 {name=RU336 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1120 -2360 0 0 {name=RU337 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1180 -2360 0 0 {name=RU338 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1240 -2360 0 0 {name=RU339 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1300 -2360 0 0 {name=RU340 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1360 -2360 0 0 {name=RU341 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1420 -2360 0 0 {name=RU342 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1480 -2360 0 0 {name=RU343 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1540 -2360 0 0 {name=RU344 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1600 -2360 0 0 {name=RU345 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1660 -2360 0 0 {name=RU346 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1720 -2360 0 0 {name=RU347 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1780 -2360 0 0 {name=RU348 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1840 -2360 0 0 {name=RU349 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1900 -2360 0 0 {name=RU350 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1960 -2360 0 0 {name=RU351 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2020 -2360 0 0 {name=RU352 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2080 -2360 0 0 {name=RU353 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2140 -2360 0 0 {name=RU354 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2200 -2360 0 0 {name=RU355 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2260 -2360 0 0 {name=RU356 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2320 -2360 0 0 {name=RU357 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2380 -2360 0 0 {name=RU358 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2440 -2360 0 0 {name=RU359 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 100 -2280 0 0 {name=RU360 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 160 -2280 0 0 {name=RU361 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 220 -2280 0 0 {name=RU362 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 280 -2280 0 0 {name=RU363 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 340 -2280 0 0 {name=RU364 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 400 -2280 0 0 {name=RU365 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 460 -2280 0 0 {name=RU366 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 520 -2280 0 0 {name=RU367 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 580 -2280 0 0 {name=RU368 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 640 -2280 0 0 {name=RU369 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 700 -2280 0 0 {name=RU370 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 760 -2280 0 0 {name=RU371 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 820 -2280 0 0 {name=RU372 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 880 -2280 0 0 {name=RU373 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 940 -2280 0 0 {name=RU374 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1000 -2280 0 0 {name=RU375 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1060 -2280 0 0 {name=RU376 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1120 -2280 0 0 {name=RU377 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1180 -2280 0 0 {name=RU378 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1240 -2280 0 0 {name=RU379 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1300 -2280 0 0 {name=RU380 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1360 -2280 0 0 {name=RU381 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1420 -2280 0 0 {name=RU382 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1480 -2280 0 0 {name=RU383 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1540 -2280 0 0 {name=RU384 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1600 -2280 0 0 {name=RU385 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1660 -2280 0 0 {name=RU386 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1720 -2280 0 0 {name=RU387 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1780 -2280 0 0 {name=RU388 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1840 -2280 0 0 {name=RU389 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1900 -2280 0 0 {name=RU390 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1960 -2280 0 0 {name=RU391 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2020 -2280 0 0 {name=RU392 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2080 -2280 0 0 {name=RU393 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2140 -2280 0 0 {name=RU394 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2200 -2280 0 0 {name=RU395 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2260 -2280 0 0 {name=RU396 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2320 -2280 0 0 {name=RU397 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2380 -2280 0 0 {name=RU398 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2440 -2280 0 0 {name=RU399 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 100 -2200 0 0 {name=RU400 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 160 -2200 0 0 {name=RU401 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 220 -2200 0 0 {name=RU402 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 280 -2200 0 0 {name=RU403 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 340 -2200 0 0 {name=RU404 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 400 -2200 0 0 {name=RU405 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 460 -2200 0 0 {name=RU406 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 520 -2200 0 0 {name=RU407 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 580 -2200 0 0 {name=RU408 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 640 -2200 0 0 {name=RU409 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 700 -2200 0 0 {name=RU410 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 760 -2200 0 0 {name=RU411 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 820 -2200 0 0 {name=RU412 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 880 -2200 0 0 {name=RU413 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 940 -2200 0 0 {name=RU414 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1000 -2200 0 0 {name=RU415 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1060 -2200 0 0 {name=RU416 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1120 -2200 0 0 {name=RU417 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1180 -2200 0 0 {name=RU418 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1240 -2200 0 0 {name=RU419 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1300 -2200 0 0 {name=RU420 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1360 -2200 0 0 {name=RU421 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1420 -2200 0 0 {name=RU422 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1480 -2200 0 0 {name=RU423 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1540 -2200 0 0 {name=RU424 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1600 -2200 0 0 {name=RU425 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1660 -2200 0 0 {name=RU426 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1720 -2200 0 0 {name=RU427 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1780 -2200 0 0 {name=RU428 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1840 -2200 0 0 {name=RU429 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1900 -2200 0 0 {name=RU430 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1960 -2200 0 0 {name=RU431 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2020 -2200 0 0 {name=RU432 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2080 -2200 0 0 {name=RU433 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2140 -2200 0 0 {name=RU434 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2200 -2200 0 0 {name=RU435 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2260 -2200 0 0 {name=RU436 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2320 -2200 0 0 {name=RU437 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2380 -2200 0 0 {name=RU438 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2440 -2200 0 0 {name=RU439 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 100 -2120 0 0 {name=RU440 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 160 -2120 0 0 {name=RU441 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 220 -2120 0 0 {name=RU442 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 280 -2120 0 0 {name=RU443 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 340 -2120 0 0 {name=RU444 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 400 -2120 0 0 {name=RU445 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 460 -2120 0 0 {name=RU446 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 520 -2120 0 0 {name=RU447 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 580 -2120 0 0 {name=RU448 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 640 -2120 0 0 {name=RU449 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 700 -2120 0 0 {name=RU450 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 760 -2120 0 0 {name=RU451 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 820 -2120 0 0 {name=RU452 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 880 -2120 0 0 {name=RU453 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 940 -2120 0 0 {name=RU454 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1000 -2120 0 0 {name=RU455 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1060 -2120 0 0 {name=RU456 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1120 -2120 0 0 {name=RU457 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1180 -2120 0 0 {name=RU458 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1240 -2120 0 0 {name=RU459 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1300 -2120 0 0 {name=RU460 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1360 -2120 0 0 {name=RU461 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1420 -2120 0 0 {name=RU462 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1480 -2120 0 0 {name=RU463 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1540 -2120 0 0 {name=RU464 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1600 -2120 0 0 {name=RU465 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1660 -2120 0 0 {name=RU466 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1720 -2120 0 0 {name=RU467 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1780 -2120 0 0 {name=RU468 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1840 -2120 0 0 {name=RU469 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1900 -2120 0 0 {name=RU470 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1960 -2120 0 0 {name=RU471 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2020 -2120 0 0 {name=RU472 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2080 -2120 0 0 {name=RU473 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2140 -2120 0 0 {name=RU474 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2200 -2120 0 0 {name=RU475 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2260 -2120 0 0 {name=RU476 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2320 -2120 0 0 {name=RU477 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2380 -2120 0 0 {name=RU478 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2440 -2120 0 0 {name=RU479 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 100 -2040 0 0 {name=RU480 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 160 -2040 0 0 {name=RU481 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 220 -2040 0 0 {name=RU482 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 280 -2040 0 0 {name=RU483 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 340 -2040 0 0 {name=RU484 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 400 -2040 0 0 {name=RU485 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 460 -2040 0 0 {name=RU486 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 520 -2040 0 0 {name=RU487 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 580 -2040 0 0 {name=RU488 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 640 -2040 0 0 {name=RU489 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 700 -2040 0 0 {name=RU490 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 760 -2040 0 0 {name=RU491 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 820 -2040 0 0 {name=RU492 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 880 -2040 0 0 {name=RU493 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 940 -2040 0 0 {name=RU494 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1000 -2040 0 0 {name=RU495 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1060 -2040 0 0 {name=RU496 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1120 -2040 0 0 {name=RU497 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1180 -2040 0 0 {name=RU498 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1240 -2040 0 0 {name=RU499 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1300 -2040 0 0 {name=RU500 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1360 -2040 0 0 {name=RU501 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1420 -2040 0 0 {name=RU502 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1480 -2040 0 0 {name=RU503 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1540 -2040 0 0 {name=RU504 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1600 -2040 0 0 {name=RU505 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1660 -2040 0 0 {name=RU506 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1720 -2040 0 0 {name=RU507 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1780 -2040 0 0 {name=RU508 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1840 -2040 0 0 {name=RU509 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1900 -2040 0 0 {name=RU510 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 1960 -2040 0 0 {name=RU511 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2020 -2040 0 0 {name=RU512 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2080 -2040 0 0 {name=RU513 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2140 -2040 0 0 {name=RU514 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2200 -2040 0 0 {name=RU515 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2260 -2040 0 0 {name=RU516 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2320 -2040 0 0 {name=RU517 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2380 -2040 0 0 {name=RU518 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 2440 -2040 0 0 {name=RU519 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 100 -1960 0 0 {name=RU520 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 160 -1960 0 0 {name=RU521 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 220 -1960 0 0 {name=RU522 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 280 -1960 0 0 {name=RU523 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 340 -1960 0 0 {name=RU524 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 400 -1960 0 0 {name=RU525 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 460 -1960 0 0 {name=RU526 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 520 -1960 0 0 {name=RU527 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 580 -1960 0 0 {name=RU528 w=4u l=1.2u model=rppd b=0 m=1}
C {sg13g2_pr/rppd.sym} 640 -1960 0 0 {name=RU529 w=4u l=1.2u model=rppd b=0 m=1}
C {g1_tlvlup.sym} 100 -3250 0 0 {name=XLU0 }
C {g1_tlvlup.sym} 300 -3250 0 0 {name=XLU1 }
C {g1_tlvlup.sym} 500 -3250 0 0 {name=XLU2 }
C {g1_tlvlup.sym} 700 -3250 0 0 {name=XLU3 }
C {g1_tlvlup.sym} 900 -3250 0 0 {name=XLU4 }
C {g1_tlvlup.sym} 1100 -3250 0 0 {name=XLU5 }
C {g1_tlvlup.sym} 1300 -3250 0 0 {name=XLU6 }
C {g1_tlvlup.sym} 1500 -3250 0 0 {name=XLU7 }
C {sg13g2_pr/sg13_hv_nmos.sym} 100 -1600 0 0 {name=MS0_0a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 150 -1600 0 0 {name=MS0_0b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 200 -1600 0 0 {name=MS0_1a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 250 -1600 0 0 {name=MS0_1b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 300 -1600 0 0 {name=MS0_2a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 350 -1600 0 0 {name=MS0_2b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 400 -1600 0 0 {name=MS0_3a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 450 -1600 0 0 {name=MS0_3b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 500 -1600 0 0 {name=MS0_4a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 550 -1600 0 0 {name=MS0_4b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 600 -1600 0 0 {name=MS0_5a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 650 -1600 0 0 {name=MS0_5b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 700 -1600 0 0 {name=MS0_6a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 750 -1600 0 0 {name=MS0_6b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 800 -1600 0 0 {name=MS0_7a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 850 -1600 0 0 {name=MS0_7b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 900 -1600 0 0 {name=MS0_8a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 950 -1600 0 0 {name=MS0_8b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1000 -1600 0 0 {name=MS0_9a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1050 -1600 0 0 {name=MS0_9b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1100 -1600 0 0 {name=MS0_10a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1150 -1600 0 0 {name=MS0_10b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1200 -1600 0 0 {name=MS0_11a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1250 -1600 0 0 {name=MS0_11b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1300 -1600 0 0 {name=MS0_12a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1350 -1600 0 0 {name=MS0_12b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1400 -1600 0 0 {name=MS0_13a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1450 -1600 0 0 {name=MS0_13b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1500 -1600 0 0 {name=MS0_14a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1550 -1600 0 0 {name=MS0_14b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1600 -1600 0 0 {name=MS0_15a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1650 -1600 0 0 {name=MS0_15b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1700 -1600 0 0 {name=MS0_16a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1750 -1600 0 0 {name=MS0_16b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1800 -1600 0 0 {name=MS0_17a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1850 -1600 0 0 {name=MS0_17b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1900 -1600 0 0 {name=MS0_18a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1950 -1600 0 0 {name=MS0_18b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2000 -1600 0 0 {name=MS0_19a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2050 -1600 0 0 {name=MS0_19b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2100 -1600 0 0 {name=MS0_20a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2150 -1600 0 0 {name=MS0_20b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2200 -1600 0 0 {name=MS0_21a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2250 -1600 0 0 {name=MS0_21b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2300 -1600 0 0 {name=MS0_22a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2350 -1600 0 0 {name=MS0_22b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2400 -1600 0 0 {name=MS0_23a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2450 -1600 0 0 {name=MS0_23b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2500 -1600 0 0 {name=MS0_24a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2550 -1600 0 0 {name=MS0_24b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2600 -1600 0 0 {name=MS0_25a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2650 -1600 0 0 {name=MS0_25b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2700 -1600 0 0 {name=MS0_26a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2750 -1600 0 0 {name=MS0_26b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2800 -1600 0 0 {name=MS0_27a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2850 -1600 0 0 {name=MS0_27b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2900 -1600 0 0 {name=MS0_28a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2950 -1600 0 0 {name=MS0_28b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 3000 -1600 0 0 {name=MS0_29a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 3050 -1600 0 0 {name=MS0_29b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 3100 -1600 0 0 {name=MS0_30a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 3150 -1600 0 0 {name=MS0_30b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 3200 -1600 0 0 {name=MS0_31a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 3250 -1600 0 0 {name=MS0_31b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 100 -1520 0 0 {name=MS0_32a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 150 -1520 0 0 {name=MS0_32b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 200 -1520 0 0 {name=MS0_33a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 250 -1520 0 0 {name=MS0_33b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 300 -1520 0 0 {name=MS0_34a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 350 -1520 0 0 {name=MS0_34b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 400 -1520 0 0 {name=MS0_35a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 450 -1520 0 0 {name=MS0_35b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 500 -1520 0 0 {name=MS0_36a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 550 -1520 0 0 {name=MS0_36b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 600 -1520 0 0 {name=MS0_37a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 650 -1520 0 0 {name=MS0_37b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 700 -1520 0 0 {name=MS0_38a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 750 -1520 0 0 {name=MS0_38b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 800 -1520 0 0 {name=MS0_39a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 850 -1520 0 0 {name=MS0_39b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 900 -1520 0 0 {name=MS0_40a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 950 -1520 0 0 {name=MS0_40b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1000 -1520 0 0 {name=MS0_41a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1050 -1520 0 0 {name=MS0_41b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1100 -1520 0 0 {name=MS0_42a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1150 -1520 0 0 {name=MS0_42b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1200 -1520 0 0 {name=MS0_43a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1250 -1520 0 0 {name=MS0_43b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1300 -1520 0 0 {name=MS0_44a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1350 -1520 0 0 {name=MS0_44b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1400 -1520 0 0 {name=MS0_45a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1450 -1520 0 0 {name=MS0_45b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1500 -1520 0 0 {name=MS0_46a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1550 -1520 0 0 {name=MS0_46b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1600 -1520 0 0 {name=MS0_47a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1650 -1520 0 0 {name=MS0_47b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1700 -1520 0 0 {name=MS0_48a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1750 -1520 0 0 {name=MS0_48b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1800 -1520 0 0 {name=MS0_49a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1850 -1520 0 0 {name=MS0_49b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1900 -1520 0 0 {name=MS0_50a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1950 -1520 0 0 {name=MS0_50b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2000 -1520 0 0 {name=MS0_51a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2050 -1520 0 0 {name=MS0_51b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2100 -1520 0 0 {name=MS0_52a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2150 -1520 0 0 {name=MS0_52b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2200 -1520 0 0 {name=MS0_53a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2250 -1520 0 0 {name=MS0_53b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2300 -1520 0 0 {name=MS0_54a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2350 -1520 0 0 {name=MS0_54b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2400 -1520 0 0 {name=MS0_55a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2450 -1520 0 0 {name=MS0_55b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2500 -1520 0 0 {name=MS0_56a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2550 -1520 0 0 {name=MS0_56b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2600 -1520 0 0 {name=MS0_57a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2650 -1520 0 0 {name=MS0_57b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2700 -1520 0 0 {name=MS0_58a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2750 -1520 0 0 {name=MS0_58b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2800 -1520 0 0 {name=MS0_59a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2850 -1520 0 0 {name=MS0_59b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2900 -1520 0 0 {name=MS0_60a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2950 -1520 0 0 {name=MS0_60b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 3000 -1520 0 0 {name=MS0_61a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 3050 -1520 0 0 {name=MS0_61b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 3100 -1520 0 0 {name=MS0_62a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 3150 -1520 0 0 {name=MS0_62b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 3200 -1520 0 0 {name=MS0_63a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 3250 -1520 0 0 {name=MS0_63b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 100 -1440 0 0 {name=MS0_64a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 150 -1440 0 0 {name=MS0_64b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 200 -1440 0 0 {name=MS0_65a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 250 -1440 0 0 {name=MS0_65b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 300 -1440 0 0 {name=MS0_66a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 350 -1440 0 0 {name=MS0_66b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 400 -1440 0 0 {name=MS0_67a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 450 -1440 0 0 {name=MS0_67b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 500 -1440 0 0 {name=MS0_68a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 550 -1440 0 0 {name=MS0_68b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 600 -1440 0 0 {name=MS0_69a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 650 -1440 0 0 {name=MS0_69b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 700 -1440 0 0 {name=MS0_70a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 750 -1440 0 0 {name=MS0_70b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 800 -1440 0 0 {name=MS0_71a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 850 -1440 0 0 {name=MS0_71b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 900 -1440 0 0 {name=MS0_72a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 950 -1440 0 0 {name=MS0_72b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1000 -1440 0 0 {name=MS0_73a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1050 -1440 0 0 {name=MS0_73b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1100 -1440 0 0 {name=MS0_74a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1150 -1440 0 0 {name=MS0_74b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1200 -1440 0 0 {name=MS0_75a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1250 -1440 0 0 {name=MS0_75b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1300 -1440 0 0 {name=MS0_76a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1350 -1440 0 0 {name=MS0_76b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1400 -1440 0 0 {name=MS0_77a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1450 -1440 0 0 {name=MS0_77b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1500 -1440 0 0 {name=MS0_78a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1550 -1440 0 0 {name=MS0_78b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1600 -1440 0 0 {name=MS0_79a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1650 -1440 0 0 {name=MS0_79b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1700 -1440 0 0 {name=MS0_80a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1750 -1440 0 0 {name=MS0_80b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1800 -1440 0 0 {name=MS0_81a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1850 -1440 0 0 {name=MS0_81b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1900 -1440 0 0 {name=MS0_82a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1950 -1440 0 0 {name=MS0_82b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2000 -1440 0 0 {name=MS0_83a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2050 -1440 0 0 {name=MS0_83b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2100 -1440 0 0 {name=MS0_84a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2150 -1440 0 0 {name=MS0_84b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2200 -1440 0 0 {name=MS0_85a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2250 -1440 0 0 {name=MS0_85b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2300 -1440 0 0 {name=MS0_86a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2350 -1440 0 0 {name=MS0_86b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2400 -1440 0 0 {name=MS0_87a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2450 -1440 0 0 {name=MS0_87b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2500 -1440 0 0 {name=MS0_88a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2550 -1440 0 0 {name=MS0_88b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2600 -1440 0 0 {name=MS0_89a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2650 -1440 0 0 {name=MS0_89b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2700 -1440 0 0 {name=MS0_90a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2750 -1440 0 0 {name=MS0_90b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2800 -1440 0 0 {name=MS0_91a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2850 -1440 0 0 {name=MS0_91b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2900 -1440 0 0 {name=MS0_92a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2950 -1440 0 0 {name=MS0_92b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 3000 -1440 0 0 {name=MS0_93a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 3050 -1440 0 0 {name=MS0_93b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 3100 -1440 0 0 {name=MS0_94a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 3150 -1440 0 0 {name=MS0_94b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 3200 -1440 0 0 {name=MS0_95a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 3250 -1440 0 0 {name=MS0_95b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 100 -1360 0 0 {name=MS0_96a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 150 -1360 0 0 {name=MS0_96b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 200 -1360 0 0 {name=MS0_97a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 250 -1360 0 0 {name=MS0_97b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 300 -1360 0 0 {name=MS0_98a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 350 -1360 0 0 {name=MS0_98b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 400 -1360 0 0 {name=MS0_99a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 450 -1360 0 0 {name=MS0_99b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 500 -1360 0 0 {name=MS0_100a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 550 -1360 0 0 {name=MS0_100b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 600 -1360 0 0 {name=MS0_101a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 650 -1360 0 0 {name=MS0_101b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 700 -1360 0 0 {name=MS0_102a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 750 -1360 0 0 {name=MS0_102b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 800 -1360 0 0 {name=MS0_103a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 850 -1360 0 0 {name=MS0_103b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 900 -1360 0 0 {name=MS0_104a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 950 -1360 0 0 {name=MS0_104b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1000 -1360 0 0 {name=MS0_105a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1050 -1360 0 0 {name=MS0_105b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1100 -1360 0 0 {name=MS0_106a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1150 -1360 0 0 {name=MS0_106b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1200 -1360 0 0 {name=MS0_107a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1250 -1360 0 0 {name=MS0_107b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1300 -1360 0 0 {name=MS0_108a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1350 -1360 0 0 {name=MS0_108b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1400 -1360 0 0 {name=MS0_109a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1450 -1360 0 0 {name=MS0_109b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1500 -1360 0 0 {name=MS0_110a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1550 -1360 0 0 {name=MS0_110b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1600 -1360 0 0 {name=MS0_111a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1650 -1360 0 0 {name=MS0_111b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1700 -1360 0 0 {name=MS0_112a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1750 -1360 0 0 {name=MS0_112b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1800 -1360 0 0 {name=MS0_113a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1850 -1360 0 0 {name=MS0_113b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1900 -1360 0 0 {name=MS0_114a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1950 -1360 0 0 {name=MS0_114b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2000 -1360 0 0 {name=MS0_115a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2050 -1360 0 0 {name=MS0_115b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2100 -1360 0 0 {name=MS0_116a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2150 -1360 0 0 {name=MS0_116b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2200 -1360 0 0 {name=MS0_117a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2250 -1360 0 0 {name=MS0_117b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2300 -1360 0 0 {name=MS0_118a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2350 -1360 0 0 {name=MS0_118b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2400 -1360 0 0 {name=MS0_119a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2450 -1360 0 0 {name=MS0_119b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2500 -1360 0 0 {name=MS0_120a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2550 -1360 0 0 {name=MS0_120b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2600 -1360 0 0 {name=MS0_121a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2650 -1360 0 0 {name=MS0_121b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2700 -1360 0 0 {name=MS0_122a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2750 -1360 0 0 {name=MS0_122b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2800 -1360 0 0 {name=MS0_123a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2850 -1360 0 0 {name=MS0_123b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2900 -1360 0 0 {name=MS0_124a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2950 -1360 0 0 {name=MS0_124b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 3000 -1360 0 0 {name=MS0_125a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 3050 -1360 0 0 {name=MS0_125b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 3100 -1360 0 0 {name=MS0_126a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 3150 -1360 0 0 {name=MS0_126b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 3200 -1360 0 0 {name=MS0_127a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 3250 -1360 0 0 {name=MS0_127b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 100 -1200 0 0 {name=MS1_0a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 150 -1200 0 0 {name=MS1_0b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 200 -1200 0 0 {name=MS1_1a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 250 -1200 0 0 {name=MS1_1b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 300 -1200 0 0 {name=MS1_2a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 350 -1200 0 0 {name=MS1_2b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 400 -1200 0 0 {name=MS1_3a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 450 -1200 0 0 {name=MS1_3b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 500 -1200 0 0 {name=MS1_4a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 550 -1200 0 0 {name=MS1_4b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 600 -1200 0 0 {name=MS1_5a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 650 -1200 0 0 {name=MS1_5b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 700 -1200 0 0 {name=MS1_6a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 750 -1200 0 0 {name=MS1_6b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 800 -1200 0 0 {name=MS1_7a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 850 -1200 0 0 {name=MS1_7b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 900 -1200 0 0 {name=MS1_8a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 950 -1200 0 0 {name=MS1_8b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1000 -1200 0 0 {name=MS1_9a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1050 -1200 0 0 {name=MS1_9b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1100 -1200 0 0 {name=MS1_10a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1150 -1200 0 0 {name=MS1_10b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1200 -1200 0 0 {name=MS1_11a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1250 -1200 0 0 {name=MS1_11b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1300 -1200 0 0 {name=MS1_12a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1350 -1200 0 0 {name=MS1_12b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1400 -1200 0 0 {name=MS1_13a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1450 -1200 0 0 {name=MS1_13b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1500 -1200 0 0 {name=MS1_14a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1550 -1200 0 0 {name=MS1_14b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1600 -1200 0 0 {name=MS1_15a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1650 -1200 0 0 {name=MS1_15b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1700 -1200 0 0 {name=MS1_16a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1750 -1200 0 0 {name=MS1_16b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1800 -1200 0 0 {name=MS1_17a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1850 -1200 0 0 {name=MS1_17b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1900 -1200 0 0 {name=MS1_18a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1950 -1200 0 0 {name=MS1_18b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2000 -1200 0 0 {name=MS1_19a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2050 -1200 0 0 {name=MS1_19b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2100 -1200 0 0 {name=MS1_20a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2150 -1200 0 0 {name=MS1_20b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2200 -1200 0 0 {name=MS1_21a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2250 -1200 0 0 {name=MS1_21b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2300 -1200 0 0 {name=MS1_22a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2350 -1200 0 0 {name=MS1_22b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2400 -1200 0 0 {name=MS1_23a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2450 -1200 0 0 {name=MS1_23b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2500 -1200 0 0 {name=MS1_24a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2550 -1200 0 0 {name=MS1_24b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2600 -1200 0 0 {name=MS1_25a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2650 -1200 0 0 {name=MS1_25b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2700 -1200 0 0 {name=MS1_26a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2750 -1200 0 0 {name=MS1_26b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2800 -1200 0 0 {name=MS1_27a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2850 -1200 0 0 {name=MS1_27b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2900 -1200 0 0 {name=MS1_28a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2950 -1200 0 0 {name=MS1_28b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 3000 -1200 0 0 {name=MS1_29a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 3050 -1200 0 0 {name=MS1_29b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 3100 -1200 0 0 {name=MS1_30a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 3150 -1200 0 0 {name=MS1_30b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 3200 -1200 0 0 {name=MS1_31a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 3250 -1200 0 0 {name=MS1_31b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 100 -1120 0 0 {name=MS1_32a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 150 -1120 0 0 {name=MS1_32b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 200 -1120 0 0 {name=MS1_33a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 250 -1120 0 0 {name=MS1_33b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 300 -1120 0 0 {name=MS1_34a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 350 -1120 0 0 {name=MS1_34b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 400 -1120 0 0 {name=MS1_35a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 450 -1120 0 0 {name=MS1_35b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 500 -1120 0 0 {name=MS1_36a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 550 -1120 0 0 {name=MS1_36b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 600 -1120 0 0 {name=MS1_37a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 650 -1120 0 0 {name=MS1_37b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 700 -1120 0 0 {name=MS1_38a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 750 -1120 0 0 {name=MS1_38b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 800 -1120 0 0 {name=MS1_39a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 850 -1120 0 0 {name=MS1_39b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 900 -1120 0 0 {name=MS1_40a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 950 -1120 0 0 {name=MS1_40b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1000 -1120 0 0 {name=MS1_41a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1050 -1120 0 0 {name=MS1_41b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1100 -1120 0 0 {name=MS1_42a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1150 -1120 0 0 {name=MS1_42b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1200 -1120 0 0 {name=MS1_43a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1250 -1120 0 0 {name=MS1_43b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1300 -1120 0 0 {name=MS1_44a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1350 -1120 0 0 {name=MS1_44b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1400 -1120 0 0 {name=MS1_45a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1450 -1120 0 0 {name=MS1_45b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1500 -1120 0 0 {name=MS1_46a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1550 -1120 0 0 {name=MS1_46b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1600 -1120 0 0 {name=MS1_47a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1650 -1120 0 0 {name=MS1_47b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1700 -1120 0 0 {name=MS1_48a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1750 -1120 0 0 {name=MS1_48b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1800 -1120 0 0 {name=MS1_49a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1850 -1120 0 0 {name=MS1_49b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1900 -1120 0 0 {name=MS1_50a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1950 -1120 0 0 {name=MS1_50b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2000 -1120 0 0 {name=MS1_51a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2050 -1120 0 0 {name=MS1_51b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2100 -1120 0 0 {name=MS1_52a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2150 -1120 0 0 {name=MS1_52b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2200 -1120 0 0 {name=MS1_53a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2250 -1120 0 0 {name=MS1_53b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2300 -1120 0 0 {name=MS1_54a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2350 -1120 0 0 {name=MS1_54b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2400 -1120 0 0 {name=MS1_55a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2450 -1120 0 0 {name=MS1_55b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2500 -1120 0 0 {name=MS1_56a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2550 -1120 0 0 {name=MS1_56b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2600 -1120 0 0 {name=MS1_57a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2650 -1120 0 0 {name=MS1_57b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2700 -1120 0 0 {name=MS1_58a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2750 -1120 0 0 {name=MS1_58b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2800 -1120 0 0 {name=MS1_59a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2850 -1120 0 0 {name=MS1_59b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2900 -1120 0 0 {name=MS1_60a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2950 -1120 0 0 {name=MS1_60b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 3000 -1120 0 0 {name=MS1_61a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 3050 -1120 0 0 {name=MS1_61b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 3100 -1120 0 0 {name=MS1_62a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 3150 -1120 0 0 {name=MS1_62b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 3200 -1120 0 0 {name=MS1_63a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 3250 -1120 0 0 {name=MS1_63b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 100 -800 0 0 {name=MS2_0a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 150 -800 0 0 {name=MS2_0b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 200 -800 0 0 {name=MS2_1a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 250 -800 0 0 {name=MS2_1b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 300 -800 0 0 {name=MS2_2a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 350 -800 0 0 {name=MS2_2b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 400 -800 0 0 {name=MS2_3a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 450 -800 0 0 {name=MS2_3b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 500 -800 0 0 {name=MS2_4a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 550 -800 0 0 {name=MS2_4b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 600 -800 0 0 {name=MS2_5a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 650 -800 0 0 {name=MS2_5b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 700 -800 0 0 {name=MS2_6a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 750 -800 0 0 {name=MS2_6b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 800 -800 0 0 {name=MS2_7a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 850 -800 0 0 {name=MS2_7b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 900 -800 0 0 {name=MS2_8a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 950 -800 0 0 {name=MS2_8b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1000 -800 0 0 {name=MS2_9a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1050 -800 0 0 {name=MS2_9b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1100 -800 0 0 {name=MS2_10a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1150 -800 0 0 {name=MS2_10b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1200 -800 0 0 {name=MS2_11a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1250 -800 0 0 {name=MS2_11b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1300 -800 0 0 {name=MS2_12a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1350 -800 0 0 {name=MS2_12b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1400 -800 0 0 {name=MS2_13a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1450 -800 0 0 {name=MS2_13b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1500 -800 0 0 {name=MS2_14a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1550 -800 0 0 {name=MS2_14b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1600 -800 0 0 {name=MS2_15a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1650 -800 0 0 {name=MS2_15b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1700 -800 0 0 {name=MS2_16a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1750 -800 0 0 {name=MS2_16b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1800 -800 0 0 {name=MS2_17a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1850 -800 0 0 {name=MS2_17b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1900 -800 0 0 {name=MS2_18a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1950 -800 0 0 {name=MS2_18b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2000 -800 0 0 {name=MS2_19a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2050 -800 0 0 {name=MS2_19b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2100 -800 0 0 {name=MS2_20a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2150 -800 0 0 {name=MS2_20b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2200 -800 0 0 {name=MS2_21a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2250 -800 0 0 {name=MS2_21b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2300 -800 0 0 {name=MS2_22a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2350 -800 0 0 {name=MS2_22b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2400 -800 0 0 {name=MS2_23a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2450 -800 0 0 {name=MS2_23b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2500 -800 0 0 {name=MS2_24a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2550 -800 0 0 {name=MS2_24b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2600 -800 0 0 {name=MS2_25a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2650 -800 0 0 {name=MS2_25b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2700 -800 0 0 {name=MS2_26a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2750 -800 0 0 {name=MS2_26b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2800 -800 0 0 {name=MS2_27a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2850 -800 0 0 {name=MS2_27b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2900 -800 0 0 {name=MS2_28a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 2950 -800 0 0 {name=MS2_28b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 3000 -800 0 0 {name=MS2_29a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 3050 -800 0 0 {name=MS2_29b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 3100 -800 0 0 {name=MS2_30a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 3150 -800 0 0 {name=MS2_30b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 3200 -800 0 0 {name=MS2_31a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 3250 -800 0 0 {name=MS2_31b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 100 -400 0 0 {name=MS3_0a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 150 -400 0 0 {name=MS3_0b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 200 -400 0 0 {name=MS3_1a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 250 -400 0 0 {name=MS3_1b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 300 -400 0 0 {name=MS3_2a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 350 -400 0 0 {name=MS3_2b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 400 -400 0 0 {name=MS3_3a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 450 -400 0 0 {name=MS3_3b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 500 -400 0 0 {name=MS3_4a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 550 -400 0 0 {name=MS3_4b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 600 -400 0 0 {name=MS3_5a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 650 -400 0 0 {name=MS3_5b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 700 -400 0 0 {name=MS3_6a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 750 -400 0 0 {name=MS3_6b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 800 -400 0 0 {name=MS3_7a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 850 -400 0 0 {name=MS3_7b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 900 -400 0 0 {name=MS3_8a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 950 -400 0 0 {name=MS3_8b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1000 -400 0 0 {name=MS3_9a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1050 -400 0 0 {name=MS3_9b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1100 -400 0 0 {name=MS3_10a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1150 -400 0 0 {name=MS3_10b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1200 -400 0 0 {name=MS3_11a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1250 -400 0 0 {name=MS3_11b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1300 -400 0 0 {name=MS3_12a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1350 -400 0 0 {name=MS3_12b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1400 -400 0 0 {name=MS3_13a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1450 -400 0 0 {name=MS3_13b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1500 -400 0 0 {name=MS3_14a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1550 -400 0 0 {name=MS3_14b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1600 -400 0 0 {name=MS3_15a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1650 -400 0 0 {name=MS3_15b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 100 0 0 0 {name=MS4_0a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 150 0 0 0 {name=MS4_0b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 200 0 0 0 {name=MS4_1a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 250 0 0 0 {name=MS4_1b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 300 0 0 0 {name=MS4_2a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 350 0 0 0 {name=MS4_2b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 400 0 0 0 {name=MS4_3a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 450 0 0 0 {name=MS4_3b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 500 0 0 0 {name=MS4_4a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 550 0 0 0 {name=MS4_4b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 600 0 0 0 {name=MS4_5a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 650 0 0 0 {name=MS4_5b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 700 0 0 0 {name=MS4_6a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 750 0 0 0 {name=MS4_6b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 800 0 0 0 {name=MS4_7a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 850 0 0 0 {name=MS4_7b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 100 400 0 0 {name=MS5_0a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 150 400 0 0 {name=MS5_0b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 200 400 0 0 {name=MS5_1a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 250 400 0 0 {name=MS5_1b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 300 400 0 0 {name=MS5_2a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 350 400 0 0 {name=MS5_2b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 400 400 0 0 {name=MS5_3a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 450 400 0 0 {name=MS5_3b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 100 800 0 0 {name=MS6_0a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 150 800 0 0 {name=MS6_0b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 200 800 0 0 {name=MS6_1a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 250 800 0 0 {name=MS6_1b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 100 1200 0 0 {name=MS7_0a model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 150 1200 0 0 {name=MS7_0b model=sg13_hv_nmos w=2u l=0.45u ng=1 m=1}
C {devices/ipin.sym} 3400 -3000 0 0 {name=p0 lab=vref}
C {devices/ipin.sym} 3400 -2970 0 0 {name=p1 lab=d0}
C {devices/ipin.sym} 3400 -2940 0 0 {name=p2 lab=d1}
C {devices/ipin.sym} 3400 -2910 0 0 {name=p3 lab=d2}
C {devices/ipin.sym} 3400 -2880 0 0 {name=p4 lab=d3}
C {devices/ipin.sym} 3400 -2850 0 0 {name=p5 lab=d4}
C {devices/ipin.sym} 3400 -2820 0 0 {name=p6 lab=d5}
C {devices/ipin.sym} 3400 -2790 0 0 {name=p7 lab=d6}
C {devices/ipin.sym} 3400 -2760 0 0 {name=p8 lab=d7}
C {devices/opin.sym} 3400 -2700 0 0 {name=p9 lab=out}
C {devices/iopin.sym} 3400 -2640 0 0 {name=p10 lab=vdd}
C {devices/iopin.sym} 3400 -2610 0 0 {name=p11 lab=vdda}
C {devices/iopin.sym} 3400 -2580 0 0 {name=p12 lab=vss}
C {devices/lab_pin.sym} 100 -3030 0 0 {name=l1 lab=s0}
C {devices/lab_pin.sym} 100 -2970 0 0 {name=l2 lab=vss}
C {devices/lab_pin.sym} 160 -3030 0 0 {name=l3 lab=s1}
C {devices/lab_pin.sym} 160 -2970 0 0 {name=l4 lab=s0}
C {devices/lab_pin.sym} 220 -3030 0 0 {name=l5 lab=s2}
C {devices/lab_pin.sym} 220 -2970 0 0 {name=l6 lab=s1}
C {devices/lab_pin.sym} 280 -3030 0 0 {name=l7 lab=s3}
C {devices/lab_pin.sym} 280 -2970 0 0 {name=l8 lab=s2}
C {devices/lab_pin.sym} 340 -3030 0 0 {name=l9 lab=s4}
C {devices/lab_pin.sym} 340 -2970 0 0 {name=l10 lab=s3}
C {devices/lab_pin.sym} 400 -3030 0 0 {name=l11 lab=s5}
C {devices/lab_pin.sym} 400 -2970 0 0 {name=l12 lab=s4}
C {devices/lab_pin.sym} 460 -3030 0 0 {name=l13 lab=s6}
C {devices/lab_pin.sym} 460 -2970 0 0 {name=l14 lab=s5}
C {devices/lab_pin.sym} 520 -3030 0 0 {name=l15 lab=s7}
C {devices/lab_pin.sym} 520 -2970 0 0 {name=l16 lab=s6}
C {devices/lab_pin.sym} 580 -3030 0 0 {name=l17 lab=s8}
C {devices/lab_pin.sym} 580 -2970 0 0 {name=l18 lab=s7}
C {devices/lab_pin.sym} 640 -3030 0 0 {name=l19 lab=s9}
C {devices/lab_pin.sym} 640 -2970 0 0 {name=l20 lab=s8}
C {devices/lab_pin.sym} 700 -3030 0 0 {name=l21 lab=s10}
C {devices/lab_pin.sym} 700 -2970 0 0 {name=l22 lab=s9}
C {devices/lab_pin.sym} 760 -3030 0 0 {name=l23 lab=s11}
C {devices/lab_pin.sym} 760 -2970 0 0 {name=l24 lab=s10}
C {devices/lab_pin.sym} 820 -3030 0 0 {name=l25 lab=s12}
C {devices/lab_pin.sym} 820 -2970 0 0 {name=l26 lab=s11}
C {devices/lab_pin.sym} 880 -3030 0 0 {name=l27 lab=s13}
C {devices/lab_pin.sym} 880 -2970 0 0 {name=l28 lab=s12}
C {devices/lab_pin.sym} 940 -3030 0 0 {name=l29 lab=s14}
C {devices/lab_pin.sym} 940 -2970 0 0 {name=l30 lab=s13}
C {devices/lab_pin.sym} 1000 -3030 0 0 {name=l31 lab=s15}
C {devices/lab_pin.sym} 1000 -2970 0 0 {name=l32 lab=s14}
C {devices/lab_pin.sym} 1060 -3030 0 0 {name=l33 lab=s16}
C {devices/lab_pin.sym} 1060 -2970 0 0 {name=l34 lab=s15}
C {devices/lab_pin.sym} 1120 -3030 0 0 {name=l35 lab=s17}
C {devices/lab_pin.sym} 1120 -2970 0 0 {name=l36 lab=s16}
C {devices/lab_pin.sym} 1180 -3030 0 0 {name=l37 lab=s18}
C {devices/lab_pin.sym} 1180 -2970 0 0 {name=l38 lab=s17}
C {devices/lab_pin.sym} 1240 -3030 0 0 {name=l39 lab=s19}
C {devices/lab_pin.sym} 1240 -2970 0 0 {name=l40 lab=s18}
C {devices/lab_pin.sym} 1300 -3030 0 0 {name=l41 lab=s20}
C {devices/lab_pin.sym} 1300 -2970 0 0 {name=l42 lab=s19}
C {devices/lab_pin.sym} 1360 -3030 0 0 {name=l43 lab=s21}
C {devices/lab_pin.sym} 1360 -2970 0 0 {name=l44 lab=s20}
C {devices/lab_pin.sym} 1420 -3030 0 0 {name=l45 lab=s22}
C {devices/lab_pin.sym} 1420 -2970 0 0 {name=l46 lab=s21}
C {devices/lab_pin.sym} 1480 -3030 0 0 {name=l47 lab=s23}
C {devices/lab_pin.sym} 1480 -2970 0 0 {name=l48 lab=s22}
C {devices/lab_pin.sym} 1540 -3030 0 0 {name=l49 lab=s24}
C {devices/lab_pin.sym} 1540 -2970 0 0 {name=l50 lab=s23}
C {devices/lab_pin.sym} 1600 -3030 0 0 {name=l51 lab=s25}
C {devices/lab_pin.sym} 1600 -2970 0 0 {name=l52 lab=s24}
C {devices/lab_pin.sym} 1660 -3030 0 0 {name=l53 lab=s26}
C {devices/lab_pin.sym} 1660 -2970 0 0 {name=l54 lab=s25}
C {devices/lab_pin.sym} 1720 -3030 0 0 {name=l55 lab=s27}
C {devices/lab_pin.sym} 1720 -2970 0 0 {name=l56 lab=s26}
C {devices/lab_pin.sym} 1780 -3030 0 0 {name=l57 lab=s28}
C {devices/lab_pin.sym} 1780 -2970 0 0 {name=l58 lab=s27}
C {devices/lab_pin.sym} 1840 -3030 0 0 {name=l59 lab=s29}
C {devices/lab_pin.sym} 1840 -2970 0 0 {name=l60 lab=s28}
C {devices/lab_pin.sym} 1900 -3030 0 0 {name=l61 lab=s30}
C {devices/lab_pin.sym} 1900 -2970 0 0 {name=l62 lab=s29}
C {devices/lab_pin.sym} 1960 -3030 0 0 {name=l63 lab=s31}
C {devices/lab_pin.sym} 1960 -2970 0 0 {name=l64 lab=s30}
C {devices/lab_pin.sym} 2020 -3030 0 0 {name=l65 lab=s32}
C {devices/lab_pin.sym} 2020 -2970 0 0 {name=l66 lab=s31}
C {devices/lab_pin.sym} 2080 -3030 0 0 {name=l67 lab=s33}
C {devices/lab_pin.sym} 2080 -2970 0 0 {name=l68 lab=s32}
C {devices/lab_pin.sym} 2140 -3030 0 0 {name=l69 lab=s34}
C {devices/lab_pin.sym} 2140 -2970 0 0 {name=l70 lab=s33}
C {devices/lab_pin.sym} 2200 -3030 0 0 {name=l71 lab=s35}
C {devices/lab_pin.sym} 2200 -2970 0 0 {name=l72 lab=s34}
C {devices/lab_pin.sym} 2260 -3030 0 0 {name=l73 lab=s36}
C {devices/lab_pin.sym} 2260 -2970 0 0 {name=l74 lab=s35}
C {devices/lab_pin.sym} 2320 -3030 0 0 {name=l75 lab=s37}
C {devices/lab_pin.sym} 2320 -2970 0 0 {name=l76 lab=s36}
C {devices/lab_pin.sym} 2380 -3030 0 0 {name=l77 lab=s38}
C {devices/lab_pin.sym} 2380 -2970 0 0 {name=l78 lab=s37}
C {devices/lab_pin.sym} 2440 -3030 0 0 {name=l79 lab=s39}
C {devices/lab_pin.sym} 2440 -2970 0 0 {name=l80 lab=s38}
C {devices/lab_pin.sym} 100 -2950 0 0 {name=l81 lab=s40}
C {devices/lab_pin.sym} 100 -2890 0 0 {name=l82 lab=s39}
C {devices/lab_pin.sym} 160 -2950 0 0 {name=l83 lab=s41}
C {devices/lab_pin.sym} 160 -2890 0 0 {name=l84 lab=s40}
C {devices/lab_pin.sym} 220 -2950 0 0 {name=l85 lab=s42}
C {devices/lab_pin.sym} 220 -2890 0 0 {name=l86 lab=s41}
C {devices/lab_pin.sym} 280 -2950 0 0 {name=l87 lab=s43}
C {devices/lab_pin.sym} 280 -2890 0 0 {name=l88 lab=s42}
C {devices/lab_pin.sym} 340 -2950 0 0 {name=l89 lab=s44}
C {devices/lab_pin.sym} 340 -2890 0 0 {name=l90 lab=s43}
C {devices/lab_pin.sym} 400 -2950 0 0 {name=l91 lab=s45}
C {devices/lab_pin.sym} 400 -2890 0 0 {name=l92 lab=s44}
C {devices/lab_pin.sym} 460 -2950 0 0 {name=l93 lab=s46}
C {devices/lab_pin.sym} 460 -2890 0 0 {name=l94 lab=s45}
C {devices/lab_pin.sym} 520 -2950 0 0 {name=l95 lab=s47}
C {devices/lab_pin.sym} 520 -2890 0 0 {name=l96 lab=s46}
C {devices/lab_pin.sym} 580 -2950 0 0 {name=l97 lab=s48}
C {devices/lab_pin.sym} 580 -2890 0 0 {name=l98 lab=s47}
C {devices/lab_pin.sym} 640 -2950 0 0 {name=l99 lab=s49}
C {devices/lab_pin.sym} 640 -2890 0 0 {name=l100 lab=s48}
C {devices/lab_pin.sym} 700 -2950 0 0 {name=l101 lab=s50}
C {devices/lab_pin.sym} 700 -2890 0 0 {name=l102 lab=s49}
C {devices/lab_pin.sym} 760 -2950 0 0 {name=l103 lab=s51}
C {devices/lab_pin.sym} 760 -2890 0 0 {name=l104 lab=s50}
C {devices/lab_pin.sym} 820 -2950 0 0 {name=l105 lab=s52}
C {devices/lab_pin.sym} 820 -2890 0 0 {name=l106 lab=s51}
C {devices/lab_pin.sym} 880 -2950 0 0 {name=l107 lab=s53}
C {devices/lab_pin.sym} 880 -2890 0 0 {name=l108 lab=s52}
C {devices/lab_pin.sym} 940 -2950 0 0 {name=l109 lab=s54}
C {devices/lab_pin.sym} 940 -2890 0 0 {name=l110 lab=s53}
C {devices/lab_pin.sym} 1000 -2950 0 0 {name=l111 lab=s55}
C {devices/lab_pin.sym} 1000 -2890 0 0 {name=l112 lab=s54}
C {devices/lab_pin.sym} 1060 -2950 0 0 {name=l113 lab=s56}
C {devices/lab_pin.sym} 1060 -2890 0 0 {name=l114 lab=s55}
C {devices/lab_pin.sym} 1120 -2950 0 0 {name=l115 lab=s57}
C {devices/lab_pin.sym} 1120 -2890 0 0 {name=l116 lab=s56}
C {devices/lab_pin.sym} 1180 -2950 0 0 {name=l117 lab=s58}
C {devices/lab_pin.sym} 1180 -2890 0 0 {name=l118 lab=s57}
C {devices/lab_pin.sym} 1240 -2950 0 0 {name=l119 lab=s59}
C {devices/lab_pin.sym} 1240 -2890 0 0 {name=l120 lab=s58}
C {devices/lab_pin.sym} 1300 -2950 0 0 {name=l121 lab=s60}
C {devices/lab_pin.sym} 1300 -2890 0 0 {name=l122 lab=s59}
C {devices/lab_pin.sym} 1360 -2950 0 0 {name=l123 lab=s61}
C {devices/lab_pin.sym} 1360 -2890 0 0 {name=l124 lab=s60}
C {devices/lab_pin.sym} 1420 -2950 0 0 {name=l125 lab=s62}
C {devices/lab_pin.sym} 1420 -2890 0 0 {name=l126 lab=s61}
C {devices/lab_pin.sym} 1480 -2950 0 0 {name=l127 lab=s63}
C {devices/lab_pin.sym} 1480 -2890 0 0 {name=l128 lab=s62}
C {devices/lab_pin.sym} 1540 -2950 0 0 {name=l129 lab=s64}
C {devices/lab_pin.sym} 1540 -2890 0 0 {name=l130 lab=s63}
C {devices/lab_pin.sym} 1600 -2950 0 0 {name=l131 lab=s65}
C {devices/lab_pin.sym} 1600 -2890 0 0 {name=l132 lab=s64}
C {devices/lab_pin.sym} 1660 -2950 0 0 {name=l133 lab=s66}
C {devices/lab_pin.sym} 1660 -2890 0 0 {name=l134 lab=s65}
C {devices/lab_pin.sym} 1720 -2950 0 0 {name=l135 lab=s67}
C {devices/lab_pin.sym} 1720 -2890 0 0 {name=l136 lab=s66}
C {devices/lab_pin.sym} 1780 -2950 0 0 {name=l137 lab=s68}
C {devices/lab_pin.sym} 1780 -2890 0 0 {name=l138 lab=s67}
C {devices/lab_pin.sym} 1840 -2950 0 0 {name=l139 lab=s69}
C {devices/lab_pin.sym} 1840 -2890 0 0 {name=l140 lab=s68}
C {devices/lab_pin.sym} 1900 -2950 0 0 {name=l141 lab=s70}
C {devices/lab_pin.sym} 1900 -2890 0 0 {name=l142 lab=s69}
C {devices/lab_pin.sym} 1960 -2950 0 0 {name=l143 lab=s71}
C {devices/lab_pin.sym} 1960 -2890 0 0 {name=l144 lab=s70}
C {devices/lab_pin.sym} 2020 -2950 0 0 {name=l145 lab=s72}
C {devices/lab_pin.sym} 2020 -2890 0 0 {name=l146 lab=s71}
C {devices/lab_pin.sym} 2080 -2950 0 0 {name=l147 lab=s73}
C {devices/lab_pin.sym} 2080 -2890 0 0 {name=l148 lab=s72}
C {devices/lab_pin.sym} 2140 -2950 0 0 {name=l149 lab=s74}
C {devices/lab_pin.sym} 2140 -2890 0 0 {name=l150 lab=s73}
C {devices/lab_pin.sym} 2200 -2950 0 0 {name=l151 lab=s75}
C {devices/lab_pin.sym} 2200 -2890 0 0 {name=l152 lab=s74}
C {devices/lab_pin.sym} 2260 -2950 0 0 {name=l153 lab=s76}
C {devices/lab_pin.sym} 2260 -2890 0 0 {name=l154 lab=s75}
C {devices/lab_pin.sym} 2320 -2950 0 0 {name=l155 lab=s77}
C {devices/lab_pin.sym} 2320 -2890 0 0 {name=l156 lab=s76}
C {devices/lab_pin.sym} 2380 -2950 0 0 {name=l157 lab=s78}
C {devices/lab_pin.sym} 2380 -2890 0 0 {name=l158 lab=s77}
C {devices/lab_pin.sym} 2440 -2950 0 0 {name=l159 lab=s79}
C {devices/lab_pin.sym} 2440 -2890 0 0 {name=l160 lab=s78}
C {devices/lab_pin.sym} 100 -2870 0 0 {name=l161 lab=s80}
C {devices/lab_pin.sym} 100 -2810 0 0 {name=l162 lab=s79}
C {devices/lab_pin.sym} 160 -2870 0 0 {name=l163 lab=s81}
C {devices/lab_pin.sym} 160 -2810 0 0 {name=l164 lab=s80}
C {devices/lab_pin.sym} 220 -2870 0 0 {name=l165 lab=s82}
C {devices/lab_pin.sym} 220 -2810 0 0 {name=l166 lab=s81}
C {devices/lab_pin.sym} 280 -2870 0 0 {name=l167 lab=s83}
C {devices/lab_pin.sym} 280 -2810 0 0 {name=l168 lab=s82}
C {devices/lab_pin.sym} 340 -2870 0 0 {name=l169 lab=s84}
C {devices/lab_pin.sym} 340 -2810 0 0 {name=l170 lab=s83}
C {devices/lab_pin.sym} 400 -2870 0 0 {name=l171 lab=s85}
C {devices/lab_pin.sym} 400 -2810 0 0 {name=l172 lab=s84}
C {devices/lab_pin.sym} 460 -2870 0 0 {name=l173 lab=s86}
C {devices/lab_pin.sym} 460 -2810 0 0 {name=l174 lab=s85}
C {devices/lab_pin.sym} 520 -2870 0 0 {name=l175 lab=s87}
C {devices/lab_pin.sym} 520 -2810 0 0 {name=l176 lab=s86}
C {devices/lab_pin.sym} 580 -2870 0 0 {name=l177 lab=s88}
C {devices/lab_pin.sym} 580 -2810 0 0 {name=l178 lab=s87}
C {devices/lab_pin.sym} 640 -2870 0 0 {name=l179 lab=s89}
C {devices/lab_pin.sym} 640 -2810 0 0 {name=l180 lab=s88}
C {devices/lab_pin.sym} 700 -2870 0 0 {name=l181 lab=s90}
C {devices/lab_pin.sym} 700 -2810 0 0 {name=l182 lab=s89}
C {devices/lab_pin.sym} 760 -2870 0 0 {name=l183 lab=s91}
C {devices/lab_pin.sym} 760 -2810 0 0 {name=l184 lab=s90}
C {devices/lab_pin.sym} 820 -2870 0 0 {name=l185 lab=s92}
C {devices/lab_pin.sym} 820 -2810 0 0 {name=l186 lab=s91}
C {devices/lab_pin.sym} 880 -2870 0 0 {name=l187 lab=s93}
C {devices/lab_pin.sym} 880 -2810 0 0 {name=l188 lab=s92}
C {devices/lab_pin.sym} 940 -2870 0 0 {name=l189 lab=s94}
C {devices/lab_pin.sym} 940 -2810 0 0 {name=l190 lab=s93}
C {devices/lab_pin.sym} 1000 -2870 0 0 {name=l191 lab=s95}
C {devices/lab_pin.sym} 1000 -2810 0 0 {name=l192 lab=s94}
C {devices/lab_pin.sym} 1060 -2870 0 0 {name=l193 lab=s96}
C {devices/lab_pin.sym} 1060 -2810 0 0 {name=l194 lab=s95}
C {devices/lab_pin.sym} 1120 -2870 0 0 {name=l195 lab=s97}
C {devices/lab_pin.sym} 1120 -2810 0 0 {name=l196 lab=s96}
C {devices/lab_pin.sym} 1180 -2870 0 0 {name=l197 lab=s98}
C {devices/lab_pin.sym} 1180 -2810 0 0 {name=l198 lab=s97}
C {devices/lab_pin.sym} 1240 -2870 0 0 {name=l199 lab=s99}
C {devices/lab_pin.sym} 1240 -2810 0 0 {name=l200 lab=s98}
C {devices/lab_pin.sym} 1300 -2870 0 0 {name=l201 lab=s100}
C {devices/lab_pin.sym} 1300 -2810 0 0 {name=l202 lab=s99}
C {devices/lab_pin.sym} 1360 -2870 0 0 {name=l203 lab=s101}
C {devices/lab_pin.sym} 1360 -2810 0 0 {name=l204 lab=s100}
C {devices/lab_pin.sym} 1420 -2870 0 0 {name=l205 lab=s102}
C {devices/lab_pin.sym} 1420 -2810 0 0 {name=l206 lab=s101}
C {devices/lab_pin.sym} 1480 -2870 0 0 {name=l207 lab=s103}
C {devices/lab_pin.sym} 1480 -2810 0 0 {name=l208 lab=s102}
C {devices/lab_pin.sym} 1540 -2870 0 0 {name=l209 lab=s104}
C {devices/lab_pin.sym} 1540 -2810 0 0 {name=l210 lab=s103}
C {devices/lab_pin.sym} 1600 -2870 0 0 {name=l211 lab=s105}
C {devices/lab_pin.sym} 1600 -2810 0 0 {name=l212 lab=s104}
C {devices/lab_pin.sym} 1660 -2870 0 0 {name=l213 lab=s106}
C {devices/lab_pin.sym} 1660 -2810 0 0 {name=l214 lab=s105}
C {devices/lab_pin.sym} 1720 -2870 0 0 {name=l215 lab=s107}
C {devices/lab_pin.sym} 1720 -2810 0 0 {name=l216 lab=s106}
C {devices/lab_pin.sym} 1780 -2870 0 0 {name=l217 lab=s108}
C {devices/lab_pin.sym} 1780 -2810 0 0 {name=l218 lab=s107}
C {devices/lab_pin.sym} 1840 -2870 0 0 {name=l219 lab=s109}
C {devices/lab_pin.sym} 1840 -2810 0 0 {name=l220 lab=s108}
C {devices/lab_pin.sym} 1900 -2870 0 0 {name=l221 lab=s110}
C {devices/lab_pin.sym} 1900 -2810 0 0 {name=l222 lab=s109}
C {devices/lab_pin.sym} 1960 -2870 0 0 {name=l223 lab=s111}
C {devices/lab_pin.sym} 1960 -2810 0 0 {name=l224 lab=s110}
C {devices/lab_pin.sym} 2020 -2870 0 0 {name=l225 lab=s112}
C {devices/lab_pin.sym} 2020 -2810 0 0 {name=l226 lab=s111}
C {devices/lab_pin.sym} 2080 -2870 0 0 {name=l227 lab=s113}
C {devices/lab_pin.sym} 2080 -2810 0 0 {name=l228 lab=s112}
C {devices/lab_pin.sym} 2140 -2870 0 0 {name=l229 lab=s114}
C {devices/lab_pin.sym} 2140 -2810 0 0 {name=l230 lab=s113}
C {devices/lab_pin.sym} 2200 -2870 0 0 {name=l231 lab=s115}
C {devices/lab_pin.sym} 2200 -2810 0 0 {name=l232 lab=s114}
C {devices/lab_pin.sym} 2260 -2870 0 0 {name=l233 lab=s116}
C {devices/lab_pin.sym} 2260 -2810 0 0 {name=l234 lab=s115}
C {devices/lab_pin.sym} 2320 -2870 0 0 {name=l235 lab=s117}
C {devices/lab_pin.sym} 2320 -2810 0 0 {name=l236 lab=s116}
C {devices/lab_pin.sym} 2380 -2870 0 0 {name=l237 lab=s118}
C {devices/lab_pin.sym} 2380 -2810 0 0 {name=l238 lab=s117}
C {devices/lab_pin.sym} 2440 -2870 0 0 {name=l239 lab=s119}
C {devices/lab_pin.sym} 2440 -2810 0 0 {name=l240 lab=s118}
C {devices/lab_pin.sym} 100 -2790 0 0 {name=l241 lab=s120}
C {devices/lab_pin.sym} 100 -2730 0 0 {name=l242 lab=s119}
C {devices/lab_pin.sym} 160 -2790 0 0 {name=l243 lab=s121}
C {devices/lab_pin.sym} 160 -2730 0 0 {name=l244 lab=s120}
C {devices/lab_pin.sym} 220 -2790 0 0 {name=l245 lab=s122}
C {devices/lab_pin.sym} 220 -2730 0 0 {name=l246 lab=s121}
C {devices/lab_pin.sym} 280 -2790 0 0 {name=l247 lab=s123}
C {devices/lab_pin.sym} 280 -2730 0 0 {name=l248 lab=s122}
C {devices/lab_pin.sym} 340 -2790 0 0 {name=l249 lab=s124}
C {devices/lab_pin.sym} 340 -2730 0 0 {name=l250 lab=s123}
C {devices/lab_pin.sym} 400 -2790 0 0 {name=l251 lab=s125}
C {devices/lab_pin.sym} 400 -2730 0 0 {name=l252 lab=s124}
C {devices/lab_pin.sym} 460 -2790 0 0 {name=l253 lab=s126}
C {devices/lab_pin.sym} 460 -2730 0 0 {name=l254 lab=s125}
C {devices/lab_pin.sym} 520 -2790 0 0 {name=l255 lab=s127}
C {devices/lab_pin.sym} 520 -2730 0 0 {name=l256 lab=s126}
C {devices/lab_pin.sym} 580 -2790 0 0 {name=l257 lab=s128}
C {devices/lab_pin.sym} 580 -2730 0 0 {name=l258 lab=s127}
C {devices/lab_pin.sym} 640 -2790 0 0 {name=l259 lab=s129}
C {devices/lab_pin.sym} 640 -2730 0 0 {name=l260 lab=s128}
C {devices/lab_pin.sym} 700 -2790 0 0 {name=l261 lab=s130}
C {devices/lab_pin.sym} 700 -2730 0 0 {name=l262 lab=s129}
C {devices/lab_pin.sym} 760 -2790 0 0 {name=l263 lab=s131}
C {devices/lab_pin.sym} 760 -2730 0 0 {name=l264 lab=s130}
C {devices/lab_pin.sym} 820 -2790 0 0 {name=l265 lab=s132}
C {devices/lab_pin.sym} 820 -2730 0 0 {name=l266 lab=s131}
C {devices/lab_pin.sym} 880 -2790 0 0 {name=l267 lab=s133}
C {devices/lab_pin.sym} 880 -2730 0 0 {name=l268 lab=s132}
C {devices/lab_pin.sym} 940 -2790 0 0 {name=l269 lab=s134}
C {devices/lab_pin.sym} 940 -2730 0 0 {name=l270 lab=s133}
C {devices/lab_pin.sym} 1000 -2790 0 0 {name=l271 lab=s135}
C {devices/lab_pin.sym} 1000 -2730 0 0 {name=l272 lab=s134}
C {devices/lab_pin.sym} 1060 -2790 0 0 {name=l273 lab=s136}
C {devices/lab_pin.sym} 1060 -2730 0 0 {name=l274 lab=s135}
C {devices/lab_pin.sym} 1120 -2790 0 0 {name=l275 lab=s137}
C {devices/lab_pin.sym} 1120 -2730 0 0 {name=l276 lab=s136}
C {devices/lab_pin.sym} 1180 -2790 0 0 {name=l277 lab=s138}
C {devices/lab_pin.sym} 1180 -2730 0 0 {name=l278 lab=s137}
C {devices/lab_pin.sym} 1240 -2790 0 0 {name=l279 lab=s139}
C {devices/lab_pin.sym} 1240 -2730 0 0 {name=l280 lab=s138}
C {devices/lab_pin.sym} 1300 -2790 0 0 {name=l281 lab=s140}
C {devices/lab_pin.sym} 1300 -2730 0 0 {name=l282 lab=s139}
C {devices/lab_pin.sym} 1360 -2790 0 0 {name=l283 lab=s141}
C {devices/lab_pin.sym} 1360 -2730 0 0 {name=l284 lab=s140}
C {devices/lab_pin.sym} 1420 -2790 0 0 {name=l285 lab=s142}
C {devices/lab_pin.sym} 1420 -2730 0 0 {name=l286 lab=s141}
C {devices/lab_pin.sym} 1480 -2790 0 0 {name=l287 lab=s143}
C {devices/lab_pin.sym} 1480 -2730 0 0 {name=l288 lab=s142}
C {devices/lab_pin.sym} 1540 -2790 0 0 {name=l289 lab=s144}
C {devices/lab_pin.sym} 1540 -2730 0 0 {name=l290 lab=s143}
C {devices/lab_pin.sym} 1600 -2790 0 0 {name=l291 lab=s145}
C {devices/lab_pin.sym} 1600 -2730 0 0 {name=l292 lab=s144}
C {devices/lab_pin.sym} 1660 -2790 0 0 {name=l293 lab=s146}
C {devices/lab_pin.sym} 1660 -2730 0 0 {name=l294 lab=s145}
C {devices/lab_pin.sym} 1720 -2790 0 0 {name=l295 lab=s147}
C {devices/lab_pin.sym} 1720 -2730 0 0 {name=l296 lab=s146}
C {devices/lab_pin.sym} 1780 -2790 0 0 {name=l297 lab=s148}
C {devices/lab_pin.sym} 1780 -2730 0 0 {name=l298 lab=s147}
C {devices/lab_pin.sym} 1840 -2790 0 0 {name=l299 lab=s149}
C {devices/lab_pin.sym} 1840 -2730 0 0 {name=l300 lab=s148}
C {devices/lab_pin.sym} 1900 -2790 0 0 {name=l301 lab=s150}
C {devices/lab_pin.sym} 1900 -2730 0 0 {name=l302 lab=s149}
C {devices/lab_pin.sym} 1960 -2790 0 0 {name=l303 lab=s151}
C {devices/lab_pin.sym} 1960 -2730 0 0 {name=l304 lab=s150}
C {devices/lab_pin.sym} 2020 -2790 0 0 {name=l305 lab=s152}
C {devices/lab_pin.sym} 2020 -2730 0 0 {name=l306 lab=s151}
C {devices/lab_pin.sym} 2080 -2790 0 0 {name=l307 lab=s153}
C {devices/lab_pin.sym} 2080 -2730 0 0 {name=l308 lab=s152}
C {devices/lab_pin.sym} 2140 -2790 0 0 {name=l309 lab=s154}
C {devices/lab_pin.sym} 2140 -2730 0 0 {name=l310 lab=s153}
C {devices/lab_pin.sym} 2200 -2790 0 0 {name=l311 lab=s155}
C {devices/lab_pin.sym} 2200 -2730 0 0 {name=l312 lab=s154}
C {devices/lab_pin.sym} 2260 -2790 0 0 {name=l313 lab=s156}
C {devices/lab_pin.sym} 2260 -2730 0 0 {name=l314 lab=s155}
C {devices/lab_pin.sym} 2320 -2790 0 0 {name=l315 lab=s157}
C {devices/lab_pin.sym} 2320 -2730 0 0 {name=l316 lab=s156}
C {devices/lab_pin.sym} 2380 -2790 0 0 {name=l317 lab=s158}
C {devices/lab_pin.sym} 2380 -2730 0 0 {name=l318 lab=s157}
C {devices/lab_pin.sym} 2440 -2790 0 0 {name=l319 lab=s159}
C {devices/lab_pin.sym} 2440 -2730 0 0 {name=l320 lab=s158}
C {devices/lab_pin.sym} 100 -2710 0 0 {name=l321 lab=s160}
C {devices/lab_pin.sym} 100 -2650 0 0 {name=l322 lab=s159}
C {devices/lab_pin.sym} 160 -2710 0 0 {name=l323 lab=s161}
C {devices/lab_pin.sym} 160 -2650 0 0 {name=l324 lab=s160}
C {devices/lab_pin.sym} 220 -2710 0 0 {name=l325 lab=s162}
C {devices/lab_pin.sym} 220 -2650 0 0 {name=l326 lab=s161}
C {devices/lab_pin.sym} 280 -2710 0 0 {name=l327 lab=s163}
C {devices/lab_pin.sym} 280 -2650 0 0 {name=l328 lab=s162}
C {devices/lab_pin.sym} 340 -2710 0 0 {name=l329 lab=s164}
C {devices/lab_pin.sym} 340 -2650 0 0 {name=l330 lab=s163}
C {devices/lab_pin.sym} 400 -2710 0 0 {name=l331 lab=s165}
C {devices/lab_pin.sym} 400 -2650 0 0 {name=l332 lab=s164}
C {devices/lab_pin.sym} 460 -2710 0 0 {name=l333 lab=s166}
C {devices/lab_pin.sym} 460 -2650 0 0 {name=l334 lab=s165}
C {devices/lab_pin.sym} 520 -2710 0 0 {name=l335 lab=s167}
C {devices/lab_pin.sym} 520 -2650 0 0 {name=l336 lab=s166}
C {devices/lab_pin.sym} 580 -2710 0 0 {name=l337 lab=s168}
C {devices/lab_pin.sym} 580 -2650 0 0 {name=l338 lab=s167}
C {devices/lab_pin.sym} 640 -2710 0 0 {name=l339 lab=s169}
C {devices/lab_pin.sym} 640 -2650 0 0 {name=l340 lab=s168}
C {devices/lab_pin.sym} 700 -2710 0 0 {name=l341 lab=s170}
C {devices/lab_pin.sym} 700 -2650 0 0 {name=l342 lab=s169}
C {devices/lab_pin.sym} 760 -2710 0 0 {name=l343 lab=s171}
C {devices/lab_pin.sym} 760 -2650 0 0 {name=l344 lab=s170}
C {devices/lab_pin.sym} 820 -2710 0 0 {name=l345 lab=s172}
C {devices/lab_pin.sym} 820 -2650 0 0 {name=l346 lab=s171}
C {devices/lab_pin.sym} 880 -2710 0 0 {name=l347 lab=s173}
C {devices/lab_pin.sym} 880 -2650 0 0 {name=l348 lab=s172}
C {devices/lab_pin.sym} 940 -2710 0 0 {name=l349 lab=s174}
C {devices/lab_pin.sym} 940 -2650 0 0 {name=l350 lab=s173}
C {devices/lab_pin.sym} 1000 -2710 0 0 {name=l351 lab=s175}
C {devices/lab_pin.sym} 1000 -2650 0 0 {name=l352 lab=s174}
C {devices/lab_pin.sym} 1060 -2710 0 0 {name=l353 lab=s176}
C {devices/lab_pin.sym} 1060 -2650 0 0 {name=l354 lab=s175}
C {devices/lab_pin.sym} 1120 -2710 0 0 {name=l355 lab=s177}
C {devices/lab_pin.sym} 1120 -2650 0 0 {name=l356 lab=s176}
C {devices/lab_pin.sym} 1180 -2710 0 0 {name=l357 lab=s178}
C {devices/lab_pin.sym} 1180 -2650 0 0 {name=l358 lab=s177}
C {devices/lab_pin.sym} 1240 -2710 0 0 {name=l359 lab=s179}
C {devices/lab_pin.sym} 1240 -2650 0 0 {name=l360 lab=s178}
C {devices/lab_pin.sym} 1300 -2710 0 0 {name=l361 lab=s180}
C {devices/lab_pin.sym} 1300 -2650 0 0 {name=l362 lab=s179}
C {devices/lab_pin.sym} 1360 -2710 0 0 {name=l363 lab=s181}
C {devices/lab_pin.sym} 1360 -2650 0 0 {name=l364 lab=s180}
C {devices/lab_pin.sym} 1420 -2710 0 0 {name=l365 lab=s182}
C {devices/lab_pin.sym} 1420 -2650 0 0 {name=l366 lab=s181}
C {devices/lab_pin.sym} 1480 -2710 0 0 {name=l367 lab=s183}
C {devices/lab_pin.sym} 1480 -2650 0 0 {name=l368 lab=s182}
C {devices/lab_pin.sym} 1540 -2710 0 0 {name=l369 lab=s184}
C {devices/lab_pin.sym} 1540 -2650 0 0 {name=l370 lab=s183}
C {devices/lab_pin.sym} 1600 -2710 0 0 {name=l371 lab=s185}
C {devices/lab_pin.sym} 1600 -2650 0 0 {name=l372 lab=s184}
C {devices/lab_pin.sym} 1660 -2710 0 0 {name=l373 lab=s186}
C {devices/lab_pin.sym} 1660 -2650 0 0 {name=l374 lab=s185}
C {devices/lab_pin.sym} 1720 -2710 0 0 {name=l375 lab=s187}
C {devices/lab_pin.sym} 1720 -2650 0 0 {name=l376 lab=s186}
C {devices/lab_pin.sym} 1780 -2710 0 0 {name=l377 lab=s188}
C {devices/lab_pin.sym} 1780 -2650 0 0 {name=l378 lab=s187}
C {devices/lab_pin.sym} 1840 -2710 0 0 {name=l379 lab=s189}
C {devices/lab_pin.sym} 1840 -2650 0 0 {name=l380 lab=s188}
C {devices/lab_pin.sym} 1900 -2710 0 0 {name=l381 lab=s190}
C {devices/lab_pin.sym} 1900 -2650 0 0 {name=l382 lab=s189}
C {devices/lab_pin.sym} 1960 -2710 0 0 {name=l383 lab=s191}
C {devices/lab_pin.sym} 1960 -2650 0 0 {name=l384 lab=s190}
C {devices/lab_pin.sym} 2020 -2710 0 0 {name=l385 lab=s192}
C {devices/lab_pin.sym} 2020 -2650 0 0 {name=l386 lab=s191}
C {devices/lab_pin.sym} 2080 -2710 0 0 {name=l387 lab=s193}
C {devices/lab_pin.sym} 2080 -2650 0 0 {name=l388 lab=s192}
C {devices/lab_pin.sym} 2140 -2710 0 0 {name=l389 lab=s194}
C {devices/lab_pin.sym} 2140 -2650 0 0 {name=l390 lab=s193}
C {devices/lab_pin.sym} 2200 -2710 0 0 {name=l391 lab=s195}
C {devices/lab_pin.sym} 2200 -2650 0 0 {name=l392 lab=s194}
C {devices/lab_pin.sym} 2260 -2710 0 0 {name=l393 lab=s196}
C {devices/lab_pin.sym} 2260 -2650 0 0 {name=l394 lab=s195}
C {devices/lab_pin.sym} 2320 -2710 0 0 {name=l395 lab=s197}
C {devices/lab_pin.sym} 2320 -2650 0 0 {name=l396 lab=s196}
C {devices/lab_pin.sym} 2380 -2710 0 0 {name=l397 lab=s198}
C {devices/lab_pin.sym} 2380 -2650 0 0 {name=l398 lab=s197}
C {devices/lab_pin.sym} 2440 -2710 0 0 {name=l399 lab=s199}
C {devices/lab_pin.sym} 2440 -2650 0 0 {name=l400 lab=s198}
C {devices/lab_pin.sym} 100 -2630 0 0 {name=l401 lab=s200}
C {devices/lab_pin.sym} 100 -2570 0 0 {name=l402 lab=s199}
C {devices/lab_pin.sym} 160 -2630 0 0 {name=l403 lab=s201}
C {devices/lab_pin.sym} 160 -2570 0 0 {name=l404 lab=s200}
C {devices/lab_pin.sym} 220 -2630 0 0 {name=l405 lab=s202}
C {devices/lab_pin.sym} 220 -2570 0 0 {name=l406 lab=s201}
C {devices/lab_pin.sym} 280 -2630 0 0 {name=l407 lab=s203}
C {devices/lab_pin.sym} 280 -2570 0 0 {name=l408 lab=s202}
C {devices/lab_pin.sym} 340 -2630 0 0 {name=l409 lab=s204}
C {devices/lab_pin.sym} 340 -2570 0 0 {name=l410 lab=s203}
C {devices/lab_pin.sym} 400 -2630 0 0 {name=l411 lab=s205}
C {devices/lab_pin.sym} 400 -2570 0 0 {name=l412 lab=s204}
C {devices/lab_pin.sym} 460 -2630 0 0 {name=l413 lab=s206}
C {devices/lab_pin.sym} 460 -2570 0 0 {name=l414 lab=s205}
C {devices/lab_pin.sym} 520 -2630 0 0 {name=l415 lab=s207}
C {devices/lab_pin.sym} 520 -2570 0 0 {name=l416 lab=s206}
C {devices/lab_pin.sym} 580 -2630 0 0 {name=l417 lab=s208}
C {devices/lab_pin.sym} 580 -2570 0 0 {name=l418 lab=s207}
C {devices/lab_pin.sym} 640 -2630 0 0 {name=l419 lab=s209}
C {devices/lab_pin.sym} 640 -2570 0 0 {name=l420 lab=s208}
C {devices/lab_pin.sym} 700 -2630 0 0 {name=l421 lab=s210}
C {devices/lab_pin.sym} 700 -2570 0 0 {name=l422 lab=s209}
C {devices/lab_pin.sym} 760 -2630 0 0 {name=l423 lab=s211}
C {devices/lab_pin.sym} 760 -2570 0 0 {name=l424 lab=s210}
C {devices/lab_pin.sym} 820 -2630 0 0 {name=l425 lab=s212}
C {devices/lab_pin.sym} 820 -2570 0 0 {name=l426 lab=s211}
C {devices/lab_pin.sym} 880 -2630 0 0 {name=l427 lab=s213}
C {devices/lab_pin.sym} 880 -2570 0 0 {name=l428 lab=s212}
C {devices/lab_pin.sym} 940 -2630 0 0 {name=l429 lab=s214}
C {devices/lab_pin.sym} 940 -2570 0 0 {name=l430 lab=s213}
C {devices/lab_pin.sym} 1000 -2630 0 0 {name=l431 lab=s215}
C {devices/lab_pin.sym} 1000 -2570 0 0 {name=l432 lab=s214}
C {devices/lab_pin.sym} 1060 -2630 0 0 {name=l433 lab=s216}
C {devices/lab_pin.sym} 1060 -2570 0 0 {name=l434 lab=s215}
C {devices/lab_pin.sym} 1120 -2630 0 0 {name=l435 lab=s217}
C {devices/lab_pin.sym} 1120 -2570 0 0 {name=l436 lab=s216}
C {devices/lab_pin.sym} 1180 -2630 0 0 {name=l437 lab=s218}
C {devices/lab_pin.sym} 1180 -2570 0 0 {name=l438 lab=s217}
C {devices/lab_pin.sym} 1240 -2630 0 0 {name=l439 lab=s219}
C {devices/lab_pin.sym} 1240 -2570 0 0 {name=l440 lab=s218}
C {devices/lab_pin.sym} 1300 -2630 0 0 {name=l441 lab=s220}
C {devices/lab_pin.sym} 1300 -2570 0 0 {name=l442 lab=s219}
C {devices/lab_pin.sym} 1360 -2630 0 0 {name=l443 lab=s221}
C {devices/lab_pin.sym} 1360 -2570 0 0 {name=l444 lab=s220}
C {devices/lab_pin.sym} 1420 -2630 0 0 {name=l445 lab=s222}
C {devices/lab_pin.sym} 1420 -2570 0 0 {name=l446 lab=s221}
C {devices/lab_pin.sym} 1480 -2630 0 0 {name=l447 lab=s223}
C {devices/lab_pin.sym} 1480 -2570 0 0 {name=l448 lab=s222}
C {devices/lab_pin.sym} 1540 -2630 0 0 {name=l449 lab=s224}
C {devices/lab_pin.sym} 1540 -2570 0 0 {name=l450 lab=s223}
C {devices/lab_pin.sym} 1600 -2630 0 0 {name=l451 lab=s225}
C {devices/lab_pin.sym} 1600 -2570 0 0 {name=l452 lab=s224}
C {devices/lab_pin.sym} 1660 -2630 0 0 {name=l453 lab=s226}
C {devices/lab_pin.sym} 1660 -2570 0 0 {name=l454 lab=s225}
C {devices/lab_pin.sym} 1720 -2630 0 0 {name=l455 lab=s227}
C {devices/lab_pin.sym} 1720 -2570 0 0 {name=l456 lab=s226}
C {devices/lab_pin.sym} 1780 -2630 0 0 {name=l457 lab=s228}
C {devices/lab_pin.sym} 1780 -2570 0 0 {name=l458 lab=s227}
C {devices/lab_pin.sym} 1840 -2630 0 0 {name=l459 lab=s229}
C {devices/lab_pin.sym} 1840 -2570 0 0 {name=l460 lab=s228}
C {devices/lab_pin.sym} 1900 -2630 0 0 {name=l461 lab=s230}
C {devices/lab_pin.sym} 1900 -2570 0 0 {name=l462 lab=s229}
C {devices/lab_pin.sym} 1960 -2630 0 0 {name=l463 lab=s231}
C {devices/lab_pin.sym} 1960 -2570 0 0 {name=l464 lab=s230}
C {devices/lab_pin.sym} 2020 -2630 0 0 {name=l465 lab=s232}
C {devices/lab_pin.sym} 2020 -2570 0 0 {name=l466 lab=s231}
C {devices/lab_pin.sym} 2080 -2630 0 0 {name=l467 lab=s233}
C {devices/lab_pin.sym} 2080 -2570 0 0 {name=l468 lab=s232}
C {devices/lab_pin.sym} 2140 -2630 0 0 {name=l469 lab=s234}
C {devices/lab_pin.sym} 2140 -2570 0 0 {name=l470 lab=s233}
C {devices/lab_pin.sym} 2200 -2630 0 0 {name=l471 lab=s235}
C {devices/lab_pin.sym} 2200 -2570 0 0 {name=l472 lab=s234}
C {devices/lab_pin.sym} 2260 -2630 0 0 {name=l473 lab=s236}
C {devices/lab_pin.sym} 2260 -2570 0 0 {name=l474 lab=s235}
C {devices/lab_pin.sym} 2320 -2630 0 0 {name=l475 lab=s237}
C {devices/lab_pin.sym} 2320 -2570 0 0 {name=l476 lab=s236}
C {devices/lab_pin.sym} 2380 -2630 0 0 {name=l477 lab=s238}
C {devices/lab_pin.sym} 2380 -2570 0 0 {name=l478 lab=s237}
C {devices/lab_pin.sym} 2440 -2630 0 0 {name=l479 lab=s239}
C {devices/lab_pin.sym} 2440 -2570 0 0 {name=l480 lab=s238}
C {devices/lab_pin.sym} 100 -2550 0 0 {name=l481 lab=s240}
C {devices/lab_pin.sym} 100 -2490 0 0 {name=l482 lab=s239}
C {devices/lab_pin.sym} 160 -2550 0 0 {name=l483 lab=s241}
C {devices/lab_pin.sym} 160 -2490 0 0 {name=l484 lab=s240}
C {devices/lab_pin.sym} 220 -2550 0 0 {name=l485 lab=s242}
C {devices/lab_pin.sym} 220 -2490 0 0 {name=l486 lab=s241}
C {devices/lab_pin.sym} 280 -2550 0 0 {name=l487 lab=s243}
C {devices/lab_pin.sym} 280 -2490 0 0 {name=l488 lab=s242}
C {devices/lab_pin.sym} 340 -2550 0 0 {name=l489 lab=s244}
C {devices/lab_pin.sym} 340 -2490 0 0 {name=l490 lab=s243}
C {devices/lab_pin.sym} 400 -2550 0 0 {name=l491 lab=s245}
C {devices/lab_pin.sym} 400 -2490 0 0 {name=l492 lab=s244}
C {devices/lab_pin.sym} 460 -2550 0 0 {name=l493 lab=s246}
C {devices/lab_pin.sym} 460 -2490 0 0 {name=l494 lab=s245}
C {devices/lab_pin.sym} 520 -2550 0 0 {name=l495 lab=s247}
C {devices/lab_pin.sym} 520 -2490 0 0 {name=l496 lab=s246}
C {devices/lab_pin.sym} 580 -2550 0 0 {name=l497 lab=s248}
C {devices/lab_pin.sym} 580 -2490 0 0 {name=l498 lab=s247}
C {devices/lab_pin.sym} 640 -2550 0 0 {name=l499 lab=s249}
C {devices/lab_pin.sym} 640 -2490 0 0 {name=l500 lab=s248}
C {devices/lab_pin.sym} 700 -2550 0 0 {name=l501 lab=s250}
C {devices/lab_pin.sym} 700 -2490 0 0 {name=l502 lab=s249}
C {devices/lab_pin.sym} 760 -2550 0 0 {name=l503 lab=s251}
C {devices/lab_pin.sym} 760 -2490 0 0 {name=l504 lab=s250}
C {devices/lab_pin.sym} 820 -2550 0 0 {name=l505 lab=s252}
C {devices/lab_pin.sym} 820 -2490 0 0 {name=l506 lab=s251}
C {devices/lab_pin.sym} 880 -2550 0 0 {name=l507 lab=s253}
C {devices/lab_pin.sym} 880 -2490 0 0 {name=l508 lab=s252}
C {devices/lab_pin.sym} 940 -2550 0 0 {name=l509 lab=t0}
C {devices/lab_pin.sym} 940 -2490 0 0 {name=l510 lab=s253}
C {devices/lab_pin.sym} 1000 -2550 0 0 {name=l511 lab=t1}
C {devices/lab_pin.sym} 1000 -2490 0 0 {name=l512 lab=t0}
C {devices/lab_pin.sym} 1060 -2550 0 0 {name=l513 lab=t2}
C {devices/lab_pin.sym} 1060 -2490 0 0 {name=l514 lab=t1}
C {devices/lab_pin.sym} 1120 -2550 0 0 {name=l515 lab=t3}
C {devices/lab_pin.sym} 1120 -2490 0 0 {name=l516 lab=t2}
C {devices/lab_pin.sym} 1180 -2550 0 0 {name=l517 lab=t4}
C {devices/lab_pin.sym} 1180 -2490 0 0 {name=l518 lab=t3}
C {devices/lab_pin.sym} 1240 -2550 0 0 {name=l519 lab=t5}
C {devices/lab_pin.sym} 1240 -2490 0 0 {name=l520 lab=t4}
C {devices/lab_pin.sym} 1300 -2550 0 0 {name=l521 lab=t6}
C {devices/lab_pin.sym} 1300 -2490 0 0 {name=l522 lab=t5}
C {devices/lab_pin.sym} 1360 -2550 0 0 {name=l523 lab=t7}
C {devices/lab_pin.sym} 1360 -2490 0 0 {name=l524 lab=t6}
C {devices/lab_pin.sym} 1420 -2550 0 0 {name=l525 lab=t8}
C {devices/lab_pin.sym} 1420 -2490 0 0 {name=l526 lab=t7}
C {devices/lab_pin.sym} 1480 -2550 0 0 {name=l527 lab=t9}
C {devices/lab_pin.sym} 1480 -2490 0 0 {name=l528 lab=t8}
C {devices/lab_pin.sym} 1540 -2550 0 0 {name=l529 lab=t10}
C {devices/lab_pin.sym} 1540 -2490 0 0 {name=l530 lab=t9}
C {devices/lab_pin.sym} 1600 -2550 0 0 {name=l531 lab=t11}
C {devices/lab_pin.sym} 1600 -2490 0 0 {name=l532 lab=t10}
C {devices/lab_pin.sym} 1660 -2550 0 0 {name=l533 lab=t12}
C {devices/lab_pin.sym} 1660 -2490 0 0 {name=l534 lab=t11}
C {devices/lab_pin.sym} 1720 -2550 0 0 {name=l535 lab=t13}
C {devices/lab_pin.sym} 1720 -2490 0 0 {name=l536 lab=t12}
C {devices/lab_pin.sym} 1780 -2550 0 0 {name=l537 lab=t14}
C {devices/lab_pin.sym} 1780 -2490 0 0 {name=l538 lab=t13}
C {devices/lab_pin.sym} 1840 -2550 0 0 {name=l539 lab=t15}
C {devices/lab_pin.sym} 1840 -2490 0 0 {name=l540 lab=t14}
C {devices/lab_pin.sym} 1900 -2550 0 0 {name=l541 lab=t16}
C {devices/lab_pin.sym} 1900 -2490 0 0 {name=l542 lab=t15}
C {devices/lab_pin.sym} 1960 -2550 0 0 {name=l543 lab=t17}
C {devices/lab_pin.sym} 1960 -2490 0 0 {name=l544 lab=t16}
C {devices/lab_pin.sym} 2020 -2550 0 0 {name=l545 lab=t18}
C {devices/lab_pin.sym} 2020 -2490 0 0 {name=l546 lab=t17}
C {devices/lab_pin.sym} 2080 -2550 0 0 {name=l547 lab=t19}
C {devices/lab_pin.sym} 2080 -2490 0 0 {name=l548 lab=t18}
C {devices/lab_pin.sym} 2140 -2550 0 0 {name=l549 lab=t20}
C {devices/lab_pin.sym} 2140 -2490 0 0 {name=l550 lab=t19}
C {devices/lab_pin.sym} 2200 -2550 0 0 {name=l551 lab=t21}
C {devices/lab_pin.sym} 2200 -2490 0 0 {name=l552 lab=t20}
C {devices/lab_pin.sym} 2260 -2550 0 0 {name=l553 lab=t22}
C {devices/lab_pin.sym} 2260 -2490 0 0 {name=l554 lab=t21}
C {devices/lab_pin.sym} 2320 -2550 0 0 {name=l555 lab=t23}
C {devices/lab_pin.sym} 2320 -2490 0 0 {name=l556 lab=t22}
C {devices/lab_pin.sym} 2380 -2550 0 0 {name=l557 lab=t24}
C {devices/lab_pin.sym} 2380 -2490 0 0 {name=l558 lab=t23}
C {devices/lab_pin.sym} 2440 -2550 0 0 {name=l559 lab=t25}
C {devices/lab_pin.sym} 2440 -2490 0 0 {name=l560 lab=t24}
C {devices/lab_pin.sym} 100 -2470 0 0 {name=l561 lab=t26}
C {devices/lab_pin.sym} 100 -2410 0 0 {name=l562 lab=t25}
C {devices/lab_pin.sym} 160 -2470 0 0 {name=l563 lab=t27}
C {devices/lab_pin.sym} 160 -2410 0 0 {name=l564 lab=t26}
C {devices/lab_pin.sym} 220 -2470 0 0 {name=l565 lab=t28}
C {devices/lab_pin.sym} 220 -2410 0 0 {name=l566 lab=t27}
C {devices/lab_pin.sym} 280 -2470 0 0 {name=l567 lab=t29}
C {devices/lab_pin.sym} 280 -2410 0 0 {name=l568 lab=t28}
C {devices/lab_pin.sym} 340 -2470 0 0 {name=l569 lab=t30}
C {devices/lab_pin.sym} 340 -2410 0 0 {name=l570 lab=t29}
C {devices/lab_pin.sym} 400 -2470 0 0 {name=l571 lab=t31}
C {devices/lab_pin.sym} 400 -2410 0 0 {name=l572 lab=t30}
C {devices/lab_pin.sym} 460 -2470 0 0 {name=l573 lab=t32}
C {devices/lab_pin.sym} 460 -2410 0 0 {name=l574 lab=t31}
C {devices/lab_pin.sym} 520 -2470 0 0 {name=l575 lab=t33}
C {devices/lab_pin.sym} 520 -2410 0 0 {name=l576 lab=t32}
C {devices/lab_pin.sym} 580 -2470 0 0 {name=l577 lab=t34}
C {devices/lab_pin.sym} 580 -2410 0 0 {name=l578 lab=t33}
C {devices/lab_pin.sym} 640 -2470 0 0 {name=l579 lab=t35}
C {devices/lab_pin.sym} 640 -2410 0 0 {name=l580 lab=t34}
C {devices/lab_pin.sym} 700 -2470 0 0 {name=l581 lab=t36}
C {devices/lab_pin.sym} 700 -2410 0 0 {name=l582 lab=t35}
C {devices/lab_pin.sym} 760 -2470 0 0 {name=l583 lab=t37}
C {devices/lab_pin.sym} 760 -2410 0 0 {name=l584 lab=t36}
C {devices/lab_pin.sym} 820 -2470 0 0 {name=l585 lab=t38}
C {devices/lab_pin.sym} 820 -2410 0 0 {name=l586 lab=t37}
C {devices/lab_pin.sym} 880 -2470 0 0 {name=l587 lab=t39}
C {devices/lab_pin.sym} 880 -2410 0 0 {name=l588 lab=t38}
C {devices/lab_pin.sym} 940 -2470 0 0 {name=l589 lab=t40}
C {devices/lab_pin.sym} 940 -2410 0 0 {name=l590 lab=t39}
C {devices/lab_pin.sym} 1000 -2470 0 0 {name=l591 lab=t41}
C {devices/lab_pin.sym} 1000 -2410 0 0 {name=l592 lab=t40}
C {devices/lab_pin.sym} 1060 -2470 0 0 {name=l593 lab=t42}
C {devices/lab_pin.sym} 1060 -2410 0 0 {name=l594 lab=t41}
C {devices/lab_pin.sym} 1120 -2470 0 0 {name=l595 lab=t43}
C {devices/lab_pin.sym} 1120 -2410 0 0 {name=l596 lab=t42}
C {devices/lab_pin.sym} 1180 -2470 0 0 {name=l597 lab=t44}
C {devices/lab_pin.sym} 1180 -2410 0 0 {name=l598 lab=t43}
C {devices/lab_pin.sym} 1240 -2470 0 0 {name=l599 lab=t45}
C {devices/lab_pin.sym} 1240 -2410 0 0 {name=l600 lab=t44}
C {devices/lab_pin.sym} 1300 -2470 0 0 {name=l601 lab=t46}
C {devices/lab_pin.sym} 1300 -2410 0 0 {name=l602 lab=t45}
C {devices/lab_pin.sym} 1360 -2470 0 0 {name=l603 lab=t47}
C {devices/lab_pin.sym} 1360 -2410 0 0 {name=l604 lab=t46}
C {devices/lab_pin.sym} 1420 -2470 0 0 {name=l605 lab=t48}
C {devices/lab_pin.sym} 1420 -2410 0 0 {name=l606 lab=t47}
C {devices/lab_pin.sym} 1480 -2470 0 0 {name=l607 lab=t49}
C {devices/lab_pin.sym} 1480 -2410 0 0 {name=l608 lab=t48}
C {devices/lab_pin.sym} 1540 -2470 0 0 {name=l609 lab=t50}
C {devices/lab_pin.sym} 1540 -2410 0 0 {name=l610 lab=t49}
C {devices/lab_pin.sym} 1600 -2470 0 0 {name=l611 lab=t51}
C {devices/lab_pin.sym} 1600 -2410 0 0 {name=l612 lab=t50}
C {devices/lab_pin.sym} 1660 -2470 0 0 {name=l613 lab=t52}
C {devices/lab_pin.sym} 1660 -2410 0 0 {name=l614 lab=t51}
C {devices/lab_pin.sym} 1720 -2470 0 0 {name=l615 lab=t53}
C {devices/lab_pin.sym} 1720 -2410 0 0 {name=l616 lab=t52}
C {devices/lab_pin.sym} 1780 -2470 0 0 {name=l617 lab=t54}
C {devices/lab_pin.sym} 1780 -2410 0 0 {name=l618 lab=t53}
C {devices/lab_pin.sym} 1840 -2470 0 0 {name=l619 lab=t55}
C {devices/lab_pin.sym} 1840 -2410 0 0 {name=l620 lab=t54}
C {devices/lab_pin.sym} 1900 -2470 0 0 {name=l621 lab=t56}
C {devices/lab_pin.sym} 1900 -2410 0 0 {name=l622 lab=t55}
C {devices/lab_pin.sym} 1960 -2470 0 0 {name=l623 lab=t57}
C {devices/lab_pin.sym} 1960 -2410 0 0 {name=l624 lab=t56}
C {devices/lab_pin.sym} 2020 -2470 0 0 {name=l625 lab=t58}
C {devices/lab_pin.sym} 2020 -2410 0 0 {name=l626 lab=t57}
C {devices/lab_pin.sym} 2080 -2470 0 0 {name=l627 lab=t59}
C {devices/lab_pin.sym} 2080 -2410 0 0 {name=l628 lab=t58}
C {devices/lab_pin.sym} 2140 -2470 0 0 {name=l629 lab=t60}
C {devices/lab_pin.sym} 2140 -2410 0 0 {name=l630 lab=t59}
C {devices/lab_pin.sym} 2200 -2470 0 0 {name=l631 lab=t61}
C {devices/lab_pin.sym} 2200 -2410 0 0 {name=l632 lab=t60}
C {devices/lab_pin.sym} 2260 -2470 0 0 {name=l633 lab=t62}
C {devices/lab_pin.sym} 2260 -2410 0 0 {name=l634 lab=t61}
C {devices/lab_pin.sym} 2320 -2470 0 0 {name=l635 lab=t63}
C {devices/lab_pin.sym} 2320 -2410 0 0 {name=l636 lab=t62}
C {devices/lab_pin.sym} 2380 -2470 0 0 {name=l637 lab=t64}
C {devices/lab_pin.sym} 2380 -2410 0 0 {name=l638 lab=t63}
C {devices/lab_pin.sym} 2440 -2470 0 0 {name=l639 lab=t65}
C {devices/lab_pin.sym} 2440 -2410 0 0 {name=l640 lab=t64}
C {devices/lab_pin.sym} 100 -2390 0 0 {name=l641 lab=t66}
C {devices/lab_pin.sym} 100 -2330 0 0 {name=l642 lab=t65}
C {devices/lab_pin.sym} 160 -2390 0 0 {name=l643 lab=t67}
C {devices/lab_pin.sym} 160 -2330 0 0 {name=l644 lab=t66}
C {devices/lab_pin.sym} 220 -2390 0 0 {name=l645 lab=t68}
C {devices/lab_pin.sym} 220 -2330 0 0 {name=l646 lab=t67}
C {devices/lab_pin.sym} 280 -2390 0 0 {name=l647 lab=t69}
C {devices/lab_pin.sym} 280 -2330 0 0 {name=l648 lab=t68}
C {devices/lab_pin.sym} 340 -2390 0 0 {name=l649 lab=t70}
C {devices/lab_pin.sym} 340 -2330 0 0 {name=l650 lab=t69}
C {devices/lab_pin.sym} 400 -2390 0 0 {name=l651 lab=t71}
C {devices/lab_pin.sym} 400 -2330 0 0 {name=l652 lab=t70}
C {devices/lab_pin.sym} 460 -2390 0 0 {name=l653 lab=t72}
C {devices/lab_pin.sym} 460 -2330 0 0 {name=l654 lab=t71}
C {devices/lab_pin.sym} 520 -2390 0 0 {name=l655 lab=t73}
C {devices/lab_pin.sym} 520 -2330 0 0 {name=l656 lab=t72}
C {devices/lab_pin.sym} 580 -2390 0 0 {name=l657 lab=t74}
C {devices/lab_pin.sym} 580 -2330 0 0 {name=l658 lab=t73}
C {devices/lab_pin.sym} 640 -2390 0 0 {name=l659 lab=t75}
C {devices/lab_pin.sym} 640 -2330 0 0 {name=l660 lab=t74}
C {devices/lab_pin.sym} 700 -2390 0 0 {name=l661 lab=t76}
C {devices/lab_pin.sym} 700 -2330 0 0 {name=l662 lab=t75}
C {devices/lab_pin.sym} 760 -2390 0 0 {name=l663 lab=t77}
C {devices/lab_pin.sym} 760 -2330 0 0 {name=l664 lab=t76}
C {devices/lab_pin.sym} 820 -2390 0 0 {name=l665 lab=t78}
C {devices/lab_pin.sym} 820 -2330 0 0 {name=l666 lab=t77}
C {devices/lab_pin.sym} 880 -2390 0 0 {name=l667 lab=t79}
C {devices/lab_pin.sym} 880 -2330 0 0 {name=l668 lab=t78}
C {devices/lab_pin.sym} 940 -2390 0 0 {name=l669 lab=t80}
C {devices/lab_pin.sym} 940 -2330 0 0 {name=l670 lab=t79}
C {devices/lab_pin.sym} 1000 -2390 0 0 {name=l671 lab=t81}
C {devices/lab_pin.sym} 1000 -2330 0 0 {name=l672 lab=t80}
C {devices/lab_pin.sym} 1060 -2390 0 0 {name=l673 lab=t82}
C {devices/lab_pin.sym} 1060 -2330 0 0 {name=l674 lab=t81}
C {devices/lab_pin.sym} 1120 -2390 0 0 {name=l675 lab=t83}
C {devices/lab_pin.sym} 1120 -2330 0 0 {name=l676 lab=t82}
C {devices/lab_pin.sym} 1180 -2390 0 0 {name=l677 lab=t84}
C {devices/lab_pin.sym} 1180 -2330 0 0 {name=l678 lab=t83}
C {devices/lab_pin.sym} 1240 -2390 0 0 {name=l679 lab=t85}
C {devices/lab_pin.sym} 1240 -2330 0 0 {name=l680 lab=t84}
C {devices/lab_pin.sym} 1300 -2390 0 0 {name=l681 lab=t86}
C {devices/lab_pin.sym} 1300 -2330 0 0 {name=l682 lab=t85}
C {devices/lab_pin.sym} 1360 -2390 0 0 {name=l683 lab=t87}
C {devices/lab_pin.sym} 1360 -2330 0 0 {name=l684 lab=t86}
C {devices/lab_pin.sym} 1420 -2390 0 0 {name=l685 lab=t88}
C {devices/lab_pin.sym} 1420 -2330 0 0 {name=l686 lab=t87}
C {devices/lab_pin.sym} 1480 -2390 0 0 {name=l687 lab=t89}
C {devices/lab_pin.sym} 1480 -2330 0 0 {name=l688 lab=t88}
C {devices/lab_pin.sym} 1540 -2390 0 0 {name=l689 lab=t90}
C {devices/lab_pin.sym} 1540 -2330 0 0 {name=l690 lab=t89}
C {devices/lab_pin.sym} 1600 -2390 0 0 {name=l691 lab=t91}
C {devices/lab_pin.sym} 1600 -2330 0 0 {name=l692 lab=t90}
C {devices/lab_pin.sym} 1660 -2390 0 0 {name=l693 lab=t92}
C {devices/lab_pin.sym} 1660 -2330 0 0 {name=l694 lab=t91}
C {devices/lab_pin.sym} 1720 -2390 0 0 {name=l695 lab=t93}
C {devices/lab_pin.sym} 1720 -2330 0 0 {name=l696 lab=t92}
C {devices/lab_pin.sym} 1780 -2390 0 0 {name=l697 lab=t94}
C {devices/lab_pin.sym} 1780 -2330 0 0 {name=l698 lab=t93}
C {devices/lab_pin.sym} 1840 -2390 0 0 {name=l699 lab=t95}
C {devices/lab_pin.sym} 1840 -2330 0 0 {name=l700 lab=t94}
C {devices/lab_pin.sym} 1900 -2390 0 0 {name=l701 lab=t96}
C {devices/lab_pin.sym} 1900 -2330 0 0 {name=l702 lab=t95}
C {devices/lab_pin.sym} 1960 -2390 0 0 {name=l703 lab=t97}
C {devices/lab_pin.sym} 1960 -2330 0 0 {name=l704 lab=t96}
C {devices/lab_pin.sym} 2020 -2390 0 0 {name=l705 lab=t98}
C {devices/lab_pin.sym} 2020 -2330 0 0 {name=l706 lab=t97}
C {devices/lab_pin.sym} 2080 -2390 0 0 {name=l707 lab=t99}
C {devices/lab_pin.sym} 2080 -2330 0 0 {name=l708 lab=t98}
C {devices/lab_pin.sym} 2140 -2390 0 0 {name=l709 lab=t100}
C {devices/lab_pin.sym} 2140 -2330 0 0 {name=l710 lab=t99}
C {devices/lab_pin.sym} 2200 -2390 0 0 {name=l711 lab=t101}
C {devices/lab_pin.sym} 2200 -2330 0 0 {name=l712 lab=t100}
C {devices/lab_pin.sym} 2260 -2390 0 0 {name=l713 lab=t102}
C {devices/lab_pin.sym} 2260 -2330 0 0 {name=l714 lab=t101}
C {devices/lab_pin.sym} 2320 -2390 0 0 {name=l715 lab=t103}
C {devices/lab_pin.sym} 2320 -2330 0 0 {name=l716 lab=t102}
C {devices/lab_pin.sym} 2380 -2390 0 0 {name=l717 lab=t104}
C {devices/lab_pin.sym} 2380 -2330 0 0 {name=l718 lab=t103}
C {devices/lab_pin.sym} 2440 -2390 0 0 {name=l719 lab=t105}
C {devices/lab_pin.sym} 2440 -2330 0 0 {name=l720 lab=t104}
C {devices/lab_pin.sym} 100 -2310 0 0 {name=l721 lab=t106}
C {devices/lab_pin.sym} 100 -2250 0 0 {name=l722 lab=t105}
C {devices/lab_pin.sym} 160 -2310 0 0 {name=l723 lab=t107}
C {devices/lab_pin.sym} 160 -2250 0 0 {name=l724 lab=t106}
C {devices/lab_pin.sym} 220 -2310 0 0 {name=l725 lab=t108}
C {devices/lab_pin.sym} 220 -2250 0 0 {name=l726 lab=t107}
C {devices/lab_pin.sym} 280 -2310 0 0 {name=l727 lab=t109}
C {devices/lab_pin.sym} 280 -2250 0 0 {name=l728 lab=t108}
C {devices/lab_pin.sym} 340 -2310 0 0 {name=l729 lab=t110}
C {devices/lab_pin.sym} 340 -2250 0 0 {name=l730 lab=t109}
C {devices/lab_pin.sym} 400 -2310 0 0 {name=l731 lab=t111}
C {devices/lab_pin.sym} 400 -2250 0 0 {name=l732 lab=t110}
C {devices/lab_pin.sym} 460 -2310 0 0 {name=l733 lab=t112}
C {devices/lab_pin.sym} 460 -2250 0 0 {name=l734 lab=t111}
C {devices/lab_pin.sym} 520 -2310 0 0 {name=l735 lab=t113}
C {devices/lab_pin.sym} 520 -2250 0 0 {name=l736 lab=t112}
C {devices/lab_pin.sym} 580 -2310 0 0 {name=l737 lab=t114}
C {devices/lab_pin.sym} 580 -2250 0 0 {name=l738 lab=t113}
C {devices/lab_pin.sym} 640 -2310 0 0 {name=l739 lab=t115}
C {devices/lab_pin.sym} 640 -2250 0 0 {name=l740 lab=t114}
C {devices/lab_pin.sym} 700 -2310 0 0 {name=l741 lab=t116}
C {devices/lab_pin.sym} 700 -2250 0 0 {name=l742 lab=t115}
C {devices/lab_pin.sym} 760 -2310 0 0 {name=l743 lab=t117}
C {devices/lab_pin.sym} 760 -2250 0 0 {name=l744 lab=t116}
C {devices/lab_pin.sym} 820 -2310 0 0 {name=l745 lab=t118}
C {devices/lab_pin.sym} 820 -2250 0 0 {name=l746 lab=t117}
C {devices/lab_pin.sym} 880 -2310 0 0 {name=l747 lab=t119}
C {devices/lab_pin.sym} 880 -2250 0 0 {name=l748 lab=t118}
C {devices/lab_pin.sym} 940 -2310 0 0 {name=l749 lab=t120}
C {devices/lab_pin.sym} 940 -2250 0 0 {name=l750 lab=t119}
C {devices/lab_pin.sym} 1000 -2310 0 0 {name=l751 lab=t121}
C {devices/lab_pin.sym} 1000 -2250 0 0 {name=l752 lab=t120}
C {devices/lab_pin.sym} 1060 -2310 0 0 {name=l753 lab=t122}
C {devices/lab_pin.sym} 1060 -2250 0 0 {name=l754 lab=t121}
C {devices/lab_pin.sym} 1120 -2310 0 0 {name=l755 lab=t123}
C {devices/lab_pin.sym} 1120 -2250 0 0 {name=l756 lab=t122}
C {devices/lab_pin.sym} 1180 -2310 0 0 {name=l757 lab=t124}
C {devices/lab_pin.sym} 1180 -2250 0 0 {name=l758 lab=t123}
C {devices/lab_pin.sym} 1240 -2310 0 0 {name=l759 lab=t125}
C {devices/lab_pin.sym} 1240 -2250 0 0 {name=l760 lab=t124}
C {devices/lab_pin.sym} 1300 -2310 0 0 {name=l761 lab=t126}
C {devices/lab_pin.sym} 1300 -2250 0 0 {name=l762 lab=t125}
C {devices/lab_pin.sym} 1360 -2310 0 0 {name=l763 lab=t127}
C {devices/lab_pin.sym} 1360 -2250 0 0 {name=l764 lab=t126}
C {devices/lab_pin.sym} 1420 -2310 0 0 {name=l765 lab=t128}
C {devices/lab_pin.sym} 1420 -2250 0 0 {name=l766 lab=t127}
C {devices/lab_pin.sym} 1480 -2310 0 0 {name=l767 lab=t129}
C {devices/lab_pin.sym} 1480 -2250 0 0 {name=l768 lab=t128}
C {devices/lab_pin.sym} 1540 -2310 0 0 {name=l769 lab=t130}
C {devices/lab_pin.sym} 1540 -2250 0 0 {name=l770 lab=t129}
C {devices/lab_pin.sym} 1600 -2310 0 0 {name=l771 lab=t131}
C {devices/lab_pin.sym} 1600 -2250 0 0 {name=l772 lab=t130}
C {devices/lab_pin.sym} 1660 -2310 0 0 {name=l773 lab=t132}
C {devices/lab_pin.sym} 1660 -2250 0 0 {name=l774 lab=t131}
C {devices/lab_pin.sym} 1720 -2310 0 0 {name=l775 lab=t133}
C {devices/lab_pin.sym} 1720 -2250 0 0 {name=l776 lab=t132}
C {devices/lab_pin.sym} 1780 -2310 0 0 {name=l777 lab=t134}
C {devices/lab_pin.sym} 1780 -2250 0 0 {name=l778 lab=t133}
C {devices/lab_pin.sym} 1840 -2310 0 0 {name=l779 lab=t135}
C {devices/lab_pin.sym} 1840 -2250 0 0 {name=l780 lab=t134}
C {devices/lab_pin.sym} 1900 -2310 0 0 {name=l781 lab=t136}
C {devices/lab_pin.sym} 1900 -2250 0 0 {name=l782 lab=t135}
C {devices/lab_pin.sym} 1960 -2310 0 0 {name=l783 lab=t137}
C {devices/lab_pin.sym} 1960 -2250 0 0 {name=l784 lab=t136}
C {devices/lab_pin.sym} 2020 -2310 0 0 {name=l785 lab=t138}
C {devices/lab_pin.sym} 2020 -2250 0 0 {name=l786 lab=t137}
C {devices/lab_pin.sym} 2080 -2310 0 0 {name=l787 lab=t139}
C {devices/lab_pin.sym} 2080 -2250 0 0 {name=l788 lab=t138}
C {devices/lab_pin.sym} 2140 -2310 0 0 {name=l789 lab=t140}
C {devices/lab_pin.sym} 2140 -2250 0 0 {name=l790 lab=t139}
C {devices/lab_pin.sym} 2200 -2310 0 0 {name=l791 lab=t141}
C {devices/lab_pin.sym} 2200 -2250 0 0 {name=l792 lab=t140}
C {devices/lab_pin.sym} 2260 -2310 0 0 {name=l793 lab=t142}
C {devices/lab_pin.sym} 2260 -2250 0 0 {name=l794 lab=t141}
C {devices/lab_pin.sym} 2320 -2310 0 0 {name=l795 lab=t143}
C {devices/lab_pin.sym} 2320 -2250 0 0 {name=l796 lab=t142}
C {devices/lab_pin.sym} 2380 -2310 0 0 {name=l797 lab=t144}
C {devices/lab_pin.sym} 2380 -2250 0 0 {name=l798 lab=t143}
C {devices/lab_pin.sym} 2440 -2310 0 0 {name=l799 lab=t145}
C {devices/lab_pin.sym} 2440 -2250 0 0 {name=l800 lab=t144}
C {devices/lab_pin.sym} 100 -2230 0 0 {name=l801 lab=t146}
C {devices/lab_pin.sym} 100 -2170 0 0 {name=l802 lab=t145}
C {devices/lab_pin.sym} 160 -2230 0 0 {name=l803 lab=t147}
C {devices/lab_pin.sym} 160 -2170 0 0 {name=l804 lab=t146}
C {devices/lab_pin.sym} 220 -2230 0 0 {name=l805 lab=t148}
C {devices/lab_pin.sym} 220 -2170 0 0 {name=l806 lab=t147}
C {devices/lab_pin.sym} 280 -2230 0 0 {name=l807 lab=t149}
C {devices/lab_pin.sym} 280 -2170 0 0 {name=l808 lab=t148}
C {devices/lab_pin.sym} 340 -2230 0 0 {name=l809 lab=t150}
C {devices/lab_pin.sym} 340 -2170 0 0 {name=l810 lab=t149}
C {devices/lab_pin.sym} 400 -2230 0 0 {name=l811 lab=t151}
C {devices/lab_pin.sym} 400 -2170 0 0 {name=l812 lab=t150}
C {devices/lab_pin.sym} 460 -2230 0 0 {name=l813 lab=t152}
C {devices/lab_pin.sym} 460 -2170 0 0 {name=l814 lab=t151}
C {devices/lab_pin.sym} 520 -2230 0 0 {name=l815 lab=t153}
C {devices/lab_pin.sym} 520 -2170 0 0 {name=l816 lab=t152}
C {devices/lab_pin.sym} 580 -2230 0 0 {name=l817 lab=t154}
C {devices/lab_pin.sym} 580 -2170 0 0 {name=l818 lab=t153}
C {devices/lab_pin.sym} 640 -2230 0 0 {name=l819 lab=t155}
C {devices/lab_pin.sym} 640 -2170 0 0 {name=l820 lab=t154}
C {devices/lab_pin.sym} 700 -2230 0 0 {name=l821 lab=t156}
C {devices/lab_pin.sym} 700 -2170 0 0 {name=l822 lab=t155}
C {devices/lab_pin.sym} 760 -2230 0 0 {name=l823 lab=t157}
C {devices/lab_pin.sym} 760 -2170 0 0 {name=l824 lab=t156}
C {devices/lab_pin.sym} 820 -2230 0 0 {name=l825 lab=t158}
C {devices/lab_pin.sym} 820 -2170 0 0 {name=l826 lab=t157}
C {devices/lab_pin.sym} 880 -2230 0 0 {name=l827 lab=t159}
C {devices/lab_pin.sym} 880 -2170 0 0 {name=l828 lab=t158}
C {devices/lab_pin.sym} 940 -2230 0 0 {name=l829 lab=t160}
C {devices/lab_pin.sym} 940 -2170 0 0 {name=l830 lab=t159}
C {devices/lab_pin.sym} 1000 -2230 0 0 {name=l831 lab=t161}
C {devices/lab_pin.sym} 1000 -2170 0 0 {name=l832 lab=t160}
C {devices/lab_pin.sym} 1060 -2230 0 0 {name=l833 lab=t162}
C {devices/lab_pin.sym} 1060 -2170 0 0 {name=l834 lab=t161}
C {devices/lab_pin.sym} 1120 -2230 0 0 {name=l835 lab=t163}
C {devices/lab_pin.sym} 1120 -2170 0 0 {name=l836 lab=t162}
C {devices/lab_pin.sym} 1180 -2230 0 0 {name=l837 lab=t164}
C {devices/lab_pin.sym} 1180 -2170 0 0 {name=l838 lab=t163}
C {devices/lab_pin.sym} 1240 -2230 0 0 {name=l839 lab=t165}
C {devices/lab_pin.sym} 1240 -2170 0 0 {name=l840 lab=t164}
C {devices/lab_pin.sym} 1300 -2230 0 0 {name=l841 lab=t166}
C {devices/lab_pin.sym} 1300 -2170 0 0 {name=l842 lab=t165}
C {devices/lab_pin.sym} 1360 -2230 0 0 {name=l843 lab=t167}
C {devices/lab_pin.sym} 1360 -2170 0 0 {name=l844 lab=t166}
C {devices/lab_pin.sym} 1420 -2230 0 0 {name=l845 lab=t168}
C {devices/lab_pin.sym} 1420 -2170 0 0 {name=l846 lab=t167}
C {devices/lab_pin.sym} 1480 -2230 0 0 {name=l847 lab=t169}
C {devices/lab_pin.sym} 1480 -2170 0 0 {name=l848 lab=t168}
C {devices/lab_pin.sym} 1540 -2230 0 0 {name=l849 lab=t170}
C {devices/lab_pin.sym} 1540 -2170 0 0 {name=l850 lab=t169}
C {devices/lab_pin.sym} 1600 -2230 0 0 {name=l851 lab=t171}
C {devices/lab_pin.sym} 1600 -2170 0 0 {name=l852 lab=t170}
C {devices/lab_pin.sym} 1660 -2230 0 0 {name=l853 lab=t172}
C {devices/lab_pin.sym} 1660 -2170 0 0 {name=l854 lab=t171}
C {devices/lab_pin.sym} 1720 -2230 0 0 {name=l855 lab=t173}
C {devices/lab_pin.sym} 1720 -2170 0 0 {name=l856 lab=t172}
C {devices/lab_pin.sym} 1780 -2230 0 0 {name=l857 lab=t174}
C {devices/lab_pin.sym} 1780 -2170 0 0 {name=l858 lab=t173}
C {devices/lab_pin.sym} 1840 -2230 0 0 {name=l859 lab=t175}
C {devices/lab_pin.sym} 1840 -2170 0 0 {name=l860 lab=t174}
C {devices/lab_pin.sym} 1900 -2230 0 0 {name=l861 lab=t176}
C {devices/lab_pin.sym} 1900 -2170 0 0 {name=l862 lab=t175}
C {devices/lab_pin.sym} 1960 -2230 0 0 {name=l863 lab=t177}
C {devices/lab_pin.sym} 1960 -2170 0 0 {name=l864 lab=t176}
C {devices/lab_pin.sym} 2020 -2230 0 0 {name=l865 lab=t178}
C {devices/lab_pin.sym} 2020 -2170 0 0 {name=l866 lab=t177}
C {devices/lab_pin.sym} 2080 -2230 0 0 {name=l867 lab=t179}
C {devices/lab_pin.sym} 2080 -2170 0 0 {name=l868 lab=t178}
C {devices/lab_pin.sym} 2140 -2230 0 0 {name=l869 lab=t180}
C {devices/lab_pin.sym} 2140 -2170 0 0 {name=l870 lab=t179}
C {devices/lab_pin.sym} 2200 -2230 0 0 {name=l871 lab=t181}
C {devices/lab_pin.sym} 2200 -2170 0 0 {name=l872 lab=t180}
C {devices/lab_pin.sym} 2260 -2230 0 0 {name=l873 lab=t182}
C {devices/lab_pin.sym} 2260 -2170 0 0 {name=l874 lab=t181}
C {devices/lab_pin.sym} 2320 -2230 0 0 {name=l875 lab=t183}
C {devices/lab_pin.sym} 2320 -2170 0 0 {name=l876 lab=t182}
C {devices/lab_pin.sym} 2380 -2230 0 0 {name=l877 lab=t184}
C {devices/lab_pin.sym} 2380 -2170 0 0 {name=l878 lab=t183}
C {devices/lab_pin.sym} 2440 -2230 0 0 {name=l879 lab=t185}
C {devices/lab_pin.sym} 2440 -2170 0 0 {name=l880 lab=t184}
C {devices/lab_pin.sym} 100 -2150 0 0 {name=l881 lab=t186}
C {devices/lab_pin.sym} 100 -2090 0 0 {name=l882 lab=t185}
C {devices/lab_pin.sym} 160 -2150 0 0 {name=l883 lab=t187}
C {devices/lab_pin.sym} 160 -2090 0 0 {name=l884 lab=t186}
C {devices/lab_pin.sym} 220 -2150 0 0 {name=l885 lab=t188}
C {devices/lab_pin.sym} 220 -2090 0 0 {name=l886 lab=t187}
C {devices/lab_pin.sym} 280 -2150 0 0 {name=l887 lab=t189}
C {devices/lab_pin.sym} 280 -2090 0 0 {name=l888 lab=t188}
C {devices/lab_pin.sym} 340 -2150 0 0 {name=l889 lab=t190}
C {devices/lab_pin.sym} 340 -2090 0 0 {name=l890 lab=t189}
C {devices/lab_pin.sym} 400 -2150 0 0 {name=l891 lab=t191}
C {devices/lab_pin.sym} 400 -2090 0 0 {name=l892 lab=t190}
C {devices/lab_pin.sym} 460 -2150 0 0 {name=l893 lab=t192}
C {devices/lab_pin.sym} 460 -2090 0 0 {name=l894 lab=t191}
C {devices/lab_pin.sym} 520 -2150 0 0 {name=l895 lab=t193}
C {devices/lab_pin.sym} 520 -2090 0 0 {name=l896 lab=t192}
C {devices/lab_pin.sym} 580 -2150 0 0 {name=l897 lab=t194}
C {devices/lab_pin.sym} 580 -2090 0 0 {name=l898 lab=t193}
C {devices/lab_pin.sym} 640 -2150 0 0 {name=l899 lab=t195}
C {devices/lab_pin.sym} 640 -2090 0 0 {name=l900 lab=t194}
C {devices/lab_pin.sym} 700 -2150 0 0 {name=l901 lab=t196}
C {devices/lab_pin.sym} 700 -2090 0 0 {name=l902 lab=t195}
C {devices/lab_pin.sym} 760 -2150 0 0 {name=l903 lab=t197}
C {devices/lab_pin.sym} 760 -2090 0 0 {name=l904 lab=t196}
C {devices/lab_pin.sym} 820 -2150 0 0 {name=l905 lab=t198}
C {devices/lab_pin.sym} 820 -2090 0 0 {name=l906 lab=t197}
C {devices/lab_pin.sym} 880 -2150 0 0 {name=l907 lab=t199}
C {devices/lab_pin.sym} 880 -2090 0 0 {name=l908 lab=t198}
C {devices/lab_pin.sym} 940 -2150 0 0 {name=l909 lab=t200}
C {devices/lab_pin.sym} 940 -2090 0 0 {name=l910 lab=t199}
C {devices/lab_pin.sym} 1000 -2150 0 0 {name=l911 lab=t201}
C {devices/lab_pin.sym} 1000 -2090 0 0 {name=l912 lab=t200}
C {devices/lab_pin.sym} 1060 -2150 0 0 {name=l913 lab=t202}
C {devices/lab_pin.sym} 1060 -2090 0 0 {name=l914 lab=t201}
C {devices/lab_pin.sym} 1120 -2150 0 0 {name=l915 lab=t203}
C {devices/lab_pin.sym} 1120 -2090 0 0 {name=l916 lab=t202}
C {devices/lab_pin.sym} 1180 -2150 0 0 {name=l917 lab=t204}
C {devices/lab_pin.sym} 1180 -2090 0 0 {name=l918 lab=t203}
C {devices/lab_pin.sym} 1240 -2150 0 0 {name=l919 lab=t205}
C {devices/lab_pin.sym} 1240 -2090 0 0 {name=l920 lab=t204}
C {devices/lab_pin.sym} 1300 -2150 0 0 {name=l921 lab=t206}
C {devices/lab_pin.sym} 1300 -2090 0 0 {name=l922 lab=t205}
C {devices/lab_pin.sym} 1360 -2150 0 0 {name=l923 lab=t207}
C {devices/lab_pin.sym} 1360 -2090 0 0 {name=l924 lab=t206}
C {devices/lab_pin.sym} 1420 -2150 0 0 {name=l925 lab=t208}
C {devices/lab_pin.sym} 1420 -2090 0 0 {name=l926 lab=t207}
C {devices/lab_pin.sym} 1480 -2150 0 0 {name=l927 lab=t209}
C {devices/lab_pin.sym} 1480 -2090 0 0 {name=l928 lab=t208}
C {devices/lab_pin.sym} 1540 -2150 0 0 {name=l929 lab=t210}
C {devices/lab_pin.sym} 1540 -2090 0 0 {name=l930 lab=t209}
C {devices/lab_pin.sym} 1600 -2150 0 0 {name=l931 lab=t211}
C {devices/lab_pin.sym} 1600 -2090 0 0 {name=l932 lab=t210}
C {devices/lab_pin.sym} 1660 -2150 0 0 {name=l933 lab=t212}
C {devices/lab_pin.sym} 1660 -2090 0 0 {name=l934 lab=t211}
C {devices/lab_pin.sym} 1720 -2150 0 0 {name=l935 lab=t213}
C {devices/lab_pin.sym} 1720 -2090 0 0 {name=l936 lab=t212}
C {devices/lab_pin.sym} 1780 -2150 0 0 {name=l937 lab=t214}
C {devices/lab_pin.sym} 1780 -2090 0 0 {name=l938 lab=t213}
C {devices/lab_pin.sym} 1840 -2150 0 0 {name=l939 lab=t215}
C {devices/lab_pin.sym} 1840 -2090 0 0 {name=l940 lab=t214}
C {devices/lab_pin.sym} 1900 -2150 0 0 {name=l941 lab=t216}
C {devices/lab_pin.sym} 1900 -2090 0 0 {name=l942 lab=t215}
C {devices/lab_pin.sym} 1960 -2150 0 0 {name=l943 lab=t217}
C {devices/lab_pin.sym} 1960 -2090 0 0 {name=l944 lab=t216}
C {devices/lab_pin.sym} 2020 -2150 0 0 {name=l945 lab=t218}
C {devices/lab_pin.sym} 2020 -2090 0 0 {name=l946 lab=t217}
C {devices/lab_pin.sym} 2080 -2150 0 0 {name=l947 lab=t219}
C {devices/lab_pin.sym} 2080 -2090 0 0 {name=l948 lab=t218}
C {devices/lab_pin.sym} 2140 -2150 0 0 {name=l949 lab=t220}
C {devices/lab_pin.sym} 2140 -2090 0 0 {name=l950 lab=t219}
C {devices/lab_pin.sym} 2200 -2150 0 0 {name=l951 lab=t221}
C {devices/lab_pin.sym} 2200 -2090 0 0 {name=l952 lab=t220}
C {devices/lab_pin.sym} 2260 -2150 0 0 {name=l953 lab=t222}
C {devices/lab_pin.sym} 2260 -2090 0 0 {name=l954 lab=t221}
C {devices/lab_pin.sym} 2320 -2150 0 0 {name=l955 lab=t223}
C {devices/lab_pin.sym} 2320 -2090 0 0 {name=l956 lab=t222}
C {devices/lab_pin.sym} 2380 -2150 0 0 {name=l957 lab=t224}
C {devices/lab_pin.sym} 2380 -2090 0 0 {name=l958 lab=t223}
C {devices/lab_pin.sym} 2440 -2150 0 0 {name=l959 lab=t225}
C {devices/lab_pin.sym} 2440 -2090 0 0 {name=l960 lab=t224}
C {devices/lab_pin.sym} 100 -2070 0 0 {name=l961 lab=t226}
C {devices/lab_pin.sym} 100 -2010 0 0 {name=l962 lab=t225}
C {devices/lab_pin.sym} 160 -2070 0 0 {name=l963 lab=t227}
C {devices/lab_pin.sym} 160 -2010 0 0 {name=l964 lab=t226}
C {devices/lab_pin.sym} 220 -2070 0 0 {name=l965 lab=t228}
C {devices/lab_pin.sym} 220 -2010 0 0 {name=l966 lab=t227}
C {devices/lab_pin.sym} 280 -2070 0 0 {name=l967 lab=t229}
C {devices/lab_pin.sym} 280 -2010 0 0 {name=l968 lab=t228}
C {devices/lab_pin.sym} 340 -2070 0 0 {name=l969 lab=t230}
C {devices/lab_pin.sym} 340 -2010 0 0 {name=l970 lab=t229}
C {devices/lab_pin.sym} 400 -2070 0 0 {name=l971 lab=t231}
C {devices/lab_pin.sym} 400 -2010 0 0 {name=l972 lab=t230}
C {devices/lab_pin.sym} 460 -2070 0 0 {name=l973 lab=t232}
C {devices/lab_pin.sym} 460 -2010 0 0 {name=l974 lab=t231}
C {devices/lab_pin.sym} 520 -2070 0 0 {name=l975 lab=t233}
C {devices/lab_pin.sym} 520 -2010 0 0 {name=l976 lab=t232}
C {devices/lab_pin.sym} 580 -2070 0 0 {name=l977 lab=t234}
C {devices/lab_pin.sym} 580 -2010 0 0 {name=l978 lab=t233}
C {devices/lab_pin.sym} 640 -2070 0 0 {name=l979 lab=t235}
C {devices/lab_pin.sym} 640 -2010 0 0 {name=l980 lab=t234}
C {devices/lab_pin.sym} 700 -2070 0 0 {name=l981 lab=t236}
C {devices/lab_pin.sym} 700 -2010 0 0 {name=l982 lab=t235}
C {devices/lab_pin.sym} 760 -2070 0 0 {name=l983 lab=t237}
C {devices/lab_pin.sym} 760 -2010 0 0 {name=l984 lab=t236}
C {devices/lab_pin.sym} 820 -2070 0 0 {name=l985 lab=t238}
C {devices/lab_pin.sym} 820 -2010 0 0 {name=l986 lab=t237}
C {devices/lab_pin.sym} 880 -2070 0 0 {name=l987 lab=t239}
C {devices/lab_pin.sym} 880 -2010 0 0 {name=l988 lab=t238}
C {devices/lab_pin.sym} 940 -2070 0 0 {name=l989 lab=t240}
C {devices/lab_pin.sym} 940 -2010 0 0 {name=l990 lab=t239}
C {devices/lab_pin.sym} 1000 -2070 0 0 {name=l991 lab=t241}
C {devices/lab_pin.sym} 1000 -2010 0 0 {name=l992 lab=t240}
C {devices/lab_pin.sym} 1060 -2070 0 0 {name=l993 lab=t242}
C {devices/lab_pin.sym} 1060 -2010 0 0 {name=l994 lab=t241}
C {devices/lab_pin.sym} 1120 -2070 0 0 {name=l995 lab=t243}
C {devices/lab_pin.sym} 1120 -2010 0 0 {name=l996 lab=t242}
C {devices/lab_pin.sym} 1180 -2070 0 0 {name=l997 lab=t244}
C {devices/lab_pin.sym} 1180 -2010 0 0 {name=l998 lab=t243}
C {devices/lab_pin.sym} 1240 -2070 0 0 {name=l999 lab=t245}
C {devices/lab_pin.sym} 1240 -2010 0 0 {name=l1000 lab=t244}
C {devices/lab_pin.sym} 1300 -2070 0 0 {name=l1001 lab=t246}
C {devices/lab_pin.sym} 1300 -2010 0 0 {name=l1002 lab=t245}
C {devices/lab_pin.sym} 1360 -2070 0 0 {name=l1003 lab=t247}
C {devices/lab_pin.sym} 1360 -2010 0 0 {name=l1004 lab=t246}
C {devices/lab_pin.sym} 1420 -2070 0 0 {name=l1005 lab=t248}
C {devices/lab_pin.sym} 1420 -2010 0 0 {name=l1006 lab=t247}
C {devices/lab_pin.sym} 1480 -2070 0 0 {name=l1007 lab=t249}
C {devices/lab_pin.sym} 1480 -2010 0 0 {name=l1008 lab=t248}
C {devices/lab_pin.sym} 1540 -2070 0 0 {name=l1009 lab=t250}
C {devices/lab_pin.sym} 1540 -2010 0 0 {name=l1010 lab=t249}
C {devices/lab_pin.sym} 1600 -2070 0 0 {name=l1011 lab=t251}
C {devices/lab_pin.sym} 1600 -2010 0 0 {name=l1012 lab=t250}
C {devices/lab_pin.sym} 1660 -2070 0 0 {name=l1013 lab=t252}
C {devices/lab_pin.sym} 1660 -2010 0 0 {name=l1014 lab=t251}
C {devices/lab_pin.sym} 1720 -2070 0 0 {name=l1015 lab=t253}
C {devices/lab_pin.sym} 1720 -2010 0 0 {name=l1016 lab=t252}
C {devices/lab_pin.sym} 1780 -2070 0 0 {name=l1017 lab=t254}
C {devices/lab_pin.sym} 1780 -2010 0 0 {name=l1018 lab=t253}
C {devices/lab_pin.sym} 1840 -2070 0 0 {name=l1019 lab=t255}
C {devices/lab_pin.sym} 1840 -2010 0 0 {name=l1020 lab=t254}
C {devices/lab_pin.sym} 1900 -2070 0 0 {name=l1021 lab=s510}
C {devices/lab_pin.sym} 1900 -2010 0 0 {name=l1022 lab=t255}
C {devices/lab_pin.sym} 1960 -2070 0 0 {name=l1023 lab=s511}
C {devices/lab_pin.sym} 1960 -2010 0 0 {name=l1024 lab=s510}
C {devices/lab_pin.sym} 2020 -2070 0 0 {name=l1025 lab=s512}
C {devices/lab_pin.sym} 2020 -2010 0 0 {name=l1026 lab=s511}
C {devices/lab_pin.sym} 2080 -2070 0 0 {name=l1027 lab=s513}
C {devices/lab_pin.sym} 2080 -2010 0 0 {name=l1028 lab=s512}
C {devices/lab_pin.sym} 2140 -2070 0 0 {name=l1029 lab=s514}
C {devices/lab_pin.sym} 2140 -2010 0 0 {name=l1030 lab=s513}
C {devices/lab_pin.sym} 2200 -2070 0 0 {name=l1031 lab=s515}
C {devices/lab_pin.sym} 2200 -2010 0 0 {name=l1032 lab=s514}
C {devices/lab_pin.sym} 2260 -2070 0 0 {name=l1033 lab=s516}
C {devices/lab_pin.sym} 2260 -2010 0 0 {name=l1034 lab=s515}
C {devices/lab_pin.sym} 2320 -2070 0 0 {name=l1035 lab=s517}
C {devices/lab_pin.sym} 2320 -2010 0 0 {name=l1036 lab=s516}
C {devices/lab_pin.sym} 2380 -2070 0 0 {name=l1037 lab=s518}
C {devices/lab_pin.sym} 2380 -2010 0 0 {name=l1038 lab=s517}
C {devices/lab_pin.sym} 2440 -2070 0 0 {name=l1039 lab=s519}
C {devices/lab_pin.sym} 2440 -2010 0 0 {name=l1040 lab=s518}
C {devices/lab_pin.sym} 100 -1990 0 0 {name=l1041 lab=s520}
C {devices/lab_pin.sym} 100 -1930 0 0 {name=l1042 lab=s519}
C {devices/lab_pin.sym} 160 -1990 0 0 {name=l1043 lab=s521}
C {devices/lab_pin.sym} 160 -1930 0 0 {name=l1044 lab=s520}
C {devices/lab_pin.sym} 220 -1990 0 0 {name=l1045 lab=s522}
C {devices/lab_pin.sym} 220 -1930 0 0 {name=l1046 lab=s521}
C {devices/lab_pin.sym} 280 -1990 0 0 {name=l1047 lab=s523}
C {devices/lab_pin.sym} 280 -1930 0 0 {name=l1048 lab=s522}
C {devices/lab_pin.sym} 340 -1990 0 0 {name=l1049 lab=s524}
C {devices/lab_pin.sym} 340 -1930 0 0 {name=l1050 lab=s523}
C {devices/lab_pin.sym} 400 -1990 0 0 {name=l1051 lab=s525}
C {devices/lab_pin.sym} 400 -1930 0 0 {name=l1052 lab=s524}
C {devices/lab_pin.sym} 460 -1990 0 0 {name=l1053 lab=s526}
C {devices/lab_pin.sym} 460 -1930 0 0 {name=l1054 lab=s525}
C {devices/lab_pin.sym} 520 -1990 0 0 {name=l1055 lab=s527}
C {devices/lab_pin.sym} 520 -1930 0 0 {name=l1056 lab=s526}
C {devices/lab_pin.sym} 580 -1990 0 0 {name=l1057 lab=s528}
C {devices/lab_pin.sym} 580 -1930 0 0 {name=l1058 lab=s527}
C {devices/lab_pin.sym} 640 -1990 0 0 {name=l1059 lab=vref}
C {devices/lab_pin.sym} 640 -1930 0 0 {name=l1060 lab=s528}
C {devices/lab_pin.sym} 30 -3250 0 0 {name=l1061 lab=d0}
C {devices/lab_pin.sym} 170 -3260 0 1 {name=l1062 lab=dh0}
C {devices/lab_pin.sym} 170 -3240 0 1 {name=l1063 lab=dhn0}
C {devices/lab_pin.sym} 80 -3300 0 0 {name=l1064 lab=vdd}
C {devices/lab_pin.sym} 120 -3300 0 1 {name=l1065 lab=vdda}
C {devices/lab_pin.sym} 100 -3200 0 0 {name=l1066 lab=vss}
C {devices/lab_pin.sym} 230 -3250 0 0 {name=l1067 lab=d1}
C {devices/lab_pin.sym} 370 -3260 0 1 {name=l1068 lab=dh1}
C {devices/lab_pin.sym} 370 -3240 0 1 {name=l1069 lab=dhn1}
C {devices/lab_pin.sym} 280 -3300 0 0 {name=l1070 lab=vdd}
C {devices/lab_pin.sym} 320 -3300 0 1 {name=l1071 lab=vdda}
C {devices/lab_pin.sym} 300 -3200 0 0 {name=l1072 lab=vss}
C {devices/lab_pin.sym} 430 -3250 0 0 {name=l1073 lab=d2}
C {devices/lab_pin.sym} 570 -3260 0 1 {name=l1074 lab=dh2}
C {devices/lab_pin.sym} 570 -3240 0 1 {name=l1075 lab=dhn2}
C {devices/lab_pin.sym} 480 -3300 0 0 {name=l1076 lab=vdd}
C {devices/lab_pin.sym} 520 -3300 0 1 {name=l1077 lab=vdda}
C {devices/lab_pin.sym} 500 -3200 0 0 {name=l1078 lab=vss}
C {devices/lab_pin.sym} 630 -3250 0 0 {name=l1079 lab=d3}
C {devices/lab_pin.sym} 770 -3260 0 1 {name=l1080 lab=dh3}
C {devices/lab_pin.sym} 770 -3240 0 1 {name=l1081 lab=dhn3}
C {devices/lab_pin.sym} 680 -3300 0 0 {name=l1082 lab=vdd}
C {devices/lab_pin.sym} 720 -3300 0 1 {name=l1083 lab=vdda}
C {devices/lab_pin.sym} 700 -3200 0 0 {name=l1084 lab=vss}
C {devices/lab_pin.sym} 830 -3250 0 0 {name=l1085 lab=d4}
C {devices/lab_pin.sym} 970 -3260 0 1 {name=l1086 lab=dh4}
C {devices/lab_pin.sym} 970 -3240 0 1 {name=l1087 lab=dhn4}
C {devices/lab_pin.sym} 880 -3300 0 0 {name=l1088 lab=vdd}
C {devices/lab_pin.sym} 920 -3300 0 1 {name=l1089 lab=vdda}
C {devices/lab_pin.sym} 900 -3200 0 0 {name=l1090 lab=vss}
C {devices/lab_pin.sym} 1030 -3250 0 0 {name=l1091 lab=d5}
C {devices/lab_pin.sym} 1170 -3260 0 1 {name=l1092 lab=dh5}
C {devices/lab_pin.sym} 1170 -3240 0 1 {name=l1093 lab=dhn5}
C {devices/lab_pin.sym} 1080 -3300 0 0 {name=l1094 lab=vdd}
C {devices/lab_pin.sym} 1120 -3300 0 1 {name=l1095 lab=vdda}
C {devices/lab_pin.sym} 1100 -3200 0 0 {name=l1096 lab=vss}
C {devices/lab_pin.sym} 1230 -3250 0 0 {name=l1097 lab=d6}
C {devices/lab_pin.sym} 1370 -3260 0 1 {name=l1098 lab=dh6}
C {devices/lab_pin.sym} 1370 -3240 0 1 {name=l1099 lab=dhn6}
C {devices/lab_pin.sym} 1280 -3300 0 0 {name=l1100 lab=vdd}
C {devices/lab_pin.sym} 1320 -3300 0 1 {name=l1101 lab=vdda}
C {devices/lab_pin.sym} 1300 -3200 0 0 {name=l1102 lab=vss}
C {devices/lab_pin.sym} 1430 -3250 0 0 {name=l1103 lab=d7}
C {devices/lab_pin.sym} 1570 -3260 0 1 {name=l1104 lab=dh7}
C {devices/lab_pin.sym} 1570 -3240 0 1 {name=l1105 lab=dhn7}
C {devices/lab_pin.sym} 1480 -3300 0 0 {name=l1106 lab=vdd}
C {devices/lab_pin.sym} 1520 -3300 0 1 {name=l1107 lab=vdda}
C {devices/lab_pin.sym} 1500 -3200 0 0 {name=l1108 lab=vss}
C {devices/lab_pin.sym} 120 -1630 0 1 {name=l1109 lab=t0}
C {devices/lab_pin.sym} 80 -1600 0 0 {name=l1110 lab=dhn0}
C {devices/lab_pin.sym} 120 -1570 0 1 {name=l1111 lab=m0_0}
C {devices/lab_pin.sym} 120 -1600 0 1 {name=l1112 lab=vss}
C {devices/lab_pin.sym} 170 -1630 0 1 {name=l1113 lab=t1}
C {devices/lab_pin.sym} 130 -1600 0 0 {name=l1114 lab=dh0}
C {devices/lab_pin.sym} 170 -1570 0 1 {name=l1115 lab=m0_0}
C {devices/lab_pin.sym} 170 -1600 0 1 {name=l1116 lab=vss}
C {devices/lab_pin.sym} 220 -1630 0 1 {name=l1117 lab=t2}
C {devices/lab_pin.sym} 180 -1600 0 0 {name=l1118 lab=dhn0}
C {devices/lab_pin.sym} 220 -1570 0 1 {name=l1119 lab=m0_1}
C {devices/lab_pin.sym} 220 -1600 0 1 {name=l1120 lab=vss}
C {devices/lab_pin.sym} 270 -1630 0 1 {name=l1121 lab=t3}
C {devices/lab_pin.sym} 230 -1600 0 0 {name=l1122 lab=dh0}
C {devices/lab_pin.sym} 270 -1570 0 1 {name=l1123 lab=m0_1}
C {devices/lab_pin.sym} 270 -1600 0 1 {name=l1124 lab=vss}
C {devices/lab_pin.sym} 320 -1630 0 1 {name=l1125 lab=t4}
C {devices/lab_pin.sym} 280 -1600 0 0 {name=l1126 lab=dhn0}
C {devices/lab_pin.sym} 320 -1570 0 1 {name=l1127 lab=m0_2}
C {devices/lab_pin.sym} 320 -1600 0 1 {name=l1128 lab=vss}
C {devices/lab_pin.sym} 370 -1630 0 1 {name=l1129 lab=t5}
C {devices/lab_pin.sym} 330 -1600 0 0 {name=l1130 lab=dh0}
C {devices/lab_pin.sym} 370 -1570 0 1 {name=l1131 lab=m0_2}
C {devices/lab_pin.sym} 370 -1600 0 1 {name=l1132 lab=vss}
C {devices/lab_pin.sym} 420 -1630 0 1 {name=l1133 lab=t6}
C {devices/lab_pin.sym} 380 -1600 0 0 {name=l1134 lab=dhn0}
C {devices/lab_pin.sym} 420 -1570 0 1 {name=l1135 lab=m0_3}
C {devices/lab_pin.sym} 420 -1600 0 1 {name=l1136 lab=vss}
C {devices/lab_pin.sym} 470 -1630 0 1 {name=l1137 lab=t7}
C {devices/lab_pin.sym} 430 -1600 0 0 {name=l1138 lab=dh0}
C {devices/lab_pin.sym} 470 -1570 0 1 {name=l1139 lab=m0_3}
C {devices/lab_pin.sym} 470 -1600 0 1 {name=l1140 lab=vss}
C {devices/lab_pin.sym} 520 -1630 0 1 {name=l1141 lab=t8}
C {devices/lab_pin.sym} 480 -1600 0 0 {name=l1142 lab=dhn0}
C {devices/lab_pin.sym} 520 -1570 0 1 {name=l1143 lab=m0_4}
C {devices/lab_pin.sym} 520 -1600 0 1 {name=l1144 lab=vss}
C {devices/lab_pin.sym} 570 -1630 0 1 {name=l1145 lab=t9}
C {devices/lab_pin.sym} 530 -1600 0 0 {name=l1146 lab=dh0}
C {devices/lab_pin.sym} 570 -1570 0 1 {name=l1147 lab=m0_4}
C {devices/lab_pin.sym} 570 -1600 0 1 {name=l1148 lab=vss}
C {devices/lab_pin.sym} 620 -1630 0 1 {name=l1149 lab=t10}
C {devices/lab_pin.sym} 580 -1600 0 0 {name=l1150 lab=dhn0}
C {devices/lab_pin.sym} 620 -1570 0 1 {name=l1151 lab=m0_5}
C {devices/lab_pin.sym} 620 -1600 0 1 {name=l1152 lab=vss}
C {devices/lab_pin.sym} 670 -1630 0 1 {name=l1153 lab=t11}
C {devices/lab_pin.sym} 630 -1600 0 0 {name=l1154 lab=dh0}
C {devices/lab_pin.sym} 670 -1570 0 1 {name=l1155 lab=m0_5}
C {devices/lab_pin.sym} 670 -1600 0 1 {name=l1156 lab=vss}
C {devices/lab_pin.sym} 720 -1630 0 1 {name=l1157 lab=t12}
C {devices/lab_pin.sym} 680 -1600 0 0 {name=l1158 lab=dhn0}
C {devices/lab_pin.sym} 720 -1570 0 1 {name=l1159 lab=m0_6}
C {devices/lab_pin.sym} 720 -1600 0 1 {name=l1160 lab=vss}
C {devices/lab_pin.sym} 770 -1630 0 1 {name=l1161 lab=t13}
C {devices/lab_pin.sym} 730 -1600 0 0 {name=l1162 lab=dh0}
C {devices/lab_pin.sym} 770 -1570 0 1 {name=l1163 lab=m0_6}
C {devices/lab_pin.sym} 770 -1600 0 1 {name=l1164 lab=vss}
C {devices/lab_pin.sym} 820 -1630 0 1 {name=l1165 lab=t14}
C {devices/lab_pin.sym} 780 -1600 0 0 {name=l1166 lab=dhn0}
C {devices/lab_pin.sym} 820 -1570 0 1 {name=l1167 lab=m0_7}
C {devices/lab_pin.sym} 820 -1600 0 1 {name=l1168 lab=vss}
C {devices/lab_pin.sym} 870 -1630 0 1 {name=l1169 lab=t15}
C {devices/lab_pin.sym} 830 -1600 0 0 {name=l1170 lab=dh0}
C {devices/lab_pin.sym} 870 -1570 0 1 {name=l1171 lab=m0_7}
C {devices/lab_pin.sym} 870 -1600 0 1 {name=l1172 lab=vss}
C {devices/lab_pin.sym} 920 -1630 0 1 {name=l1173 lab=t16}
C {devices/lab_pin.sym} 880 -1600 0 0 {name=l1174 lab=dhn0}
C {devices/lab_pin.sym} 920 -1570 0 1 {name=l1175 lab=m0_8}
C {devices/lab_pin.sym} 920 -1600 0 1 {name=l1176 lab=vss}
C {devices/lab_pin.sym} 970 -1630 0 1 {name=l1177 lab=t17}
C {devices/lab_pin.sym} 930 -1600 0 0 {name=l1178 lab=dh0}
C {devices/lab_pin.sym} 970 -1570 0 1 {name=l1179 lab=m0_8}
C {devices/lab_pin.sym} 970 -1600 0 1 {name=l1180 lab=vss}
C {devices/lab_pin.sym} 1020 -1630 0 1 {name=l1181 lab=t18}
C {devices/lab_pin.sym} 980 -1600 0 0 {name=l1182 lab=dhn0}
C {devices/lab_pin.sym} 1020 -1570 0 1 {name=l1183 lab=m0_9}
C {devices/lab_pin.sym} 1020 -1600 0 1 {name=l1184 lab=vss}
C {devices/lab_pin.sym} 1070 -1630 0 1 {name=l1185 lab=t19}
C {devices/lab_pin.sym} 1030 -1600 0 0 {name=l1186 lab=dh0}
C {devices/lab_pin.sym} 1070 -1570 0 1 {name=l1187 lab=m0_9}
C {devices/lab_pin.sym} 1070 -1600 0 1 {name=l1188 lab=vss}
C {devices/lab_pin.sym} 1120 -1630 0 1 {name=l1189 lab=t20}
C {devices/lab_pin.sym} 1080 -1600 0 0 {name=l1190 lab=dhn0}
C {devices/lab_pin.sym} 1120 -1570 0 1 {name=l1191 lab=m0_10}
C {devices/lab_pin.sym} 1120 -1600 0 1 {name=l1192 lab=vss}
C {devices/lab_pin.sym} 1170 -1630 0 1 {name=l1193 lab=t21}
C {devices/lab_pin.sym} 1130 -1600 0 0 {name=l1194 lab=dh0}
C {devices/lab_pin.sym} 1170 -1570 0 1 {name=l1195 lab=m0_10}
C {devices/lab_pin.sym} 1170 -1600 0 1 {name=l1196 lab=vss}
C {devices/lab_pin.sym} 1220 -1630 0 1 {name=l1197 lab=t22}
C {devices/lab_pin.sym} 1180 -1600 0 0 {name=l1198 lab=dhn0}
C {devices/lab_pin.sym} 1220 -1570 0 1 {name=l1199 lab=m0_11}
C {devices/lab_pin.sym} 1220 -1600 0 1 {name=l1200 lab=vss}
C {devices/lab_pin.sym} 1270 -1630 0 1 {name=l1201 lab=t23}
C {devices/lab_pin.sym} 1230 -1600 0 0 {name=l1202 lab=dh0}
C {devices/lab_pin.sym} 1270 -1570 0 1 {name=l1203 lab=m0_11}
C {devices/lab_pin.sym} 1270 -1600 0 1 {name=l1204 lab=vss}
C {devices/lab_pin.sym} 1320 -1630 0 1 {name=l1205 lab=t24}
C {devices/lab_pin.sym} 1280 -1600 0 0 {name=l1206 lab=dhn0}
C {devices/lab_pin.sym} 1320 -1570 0 1 {name=l1207 lab=m0_12}
C {devices/lab_pin.sym} 1320 -1600 0 1 {name=l1208 lab=vss}
C {devices/lab_pin.sym} 1370 -1630 0 1 {name=l1209 lab=t25}
C {devices/lab_pin.sym} 1330 -1600 0 0 {name=l1210 lab=dh0}
C {devices/lab_pin.sym} 1370 -1570 0 1 {name=l1211 lab=m0_12}
C {devices/lab_pin.sym} 1370 -1600 0 1 {name=l1212 lab=vss}
C {devices/lab_pin.sym} 1420 -1630 0 1 {name=l1213 lab=t26}
C {devices/lab_pin.sym} 1380 -1600 0 0 {name=l1214 lab=dhn0}
C {devices/lab_pin.sym} 1420 -1570 0 1 {name=l1215 lab=m0_13}
C {devices/lab_pin.sym} 1420 -1600 0 1 {name=l1216 lab=vss}
C {devices/lab_pin.sym} 1470 -1630 0 1 {name=l1217 lab=t27}
C {devices/lab_pin.sym} 1430 -1600 0 0 {name=l1218 lab=dh0}
C {devices/lab_pin.sym} 1470 -1570 0 1 {name=l1219 lab=m0_13}
C {devices/lab_pin.sym} 1470 -1600 0 1 {name=l1220 lab=vss}
C {devices/lab_pin.sym} 1520 -1630 0 1 {name=l1221 lab=t28}
C {devices/lab_pin.sym} 1480 -1600 0 0 {name=l1222 lab=dhn0}
C {devices/lab_pin.sym} 1520 -1570 0 1 {name=l1223 lab=m0_14}
C {devices/lab_pin.sym} 1520 -1600 0 1 {name=l1224 lab=vss}
C {devices/lab_pin.sym} 1570 -1630 0 1 {name=l1225 lab=t29}
C {devices/lab_pin.sym} 1530 -1600 0 0 {name=l1226 lab=dh0}
C {devices/lab_pin.sym} 1570 -1570 0 1 {name=l1227 lab=m0_14}
C {devices/lab_pin.sym} 1570 -1600 0 1 {name=l1228 lab=vss}
C {devices/lab_pin.sym} 1620 -1630 0 1 {name=l1229 lab=t30}
C {devices/lab_pin.sym} 1580 -1600 0 0 {name=l1230 lab=dhn0}
C {devices/lab_pin.sym} 1620 -1570 0 1 {name=l1231 lab=m0_15}
C {devices/lab_pin.sym} 1620 -1600 0 1 {name=l1232 lab=vss}
C {devices/lab_pin.sym} 1670 -1630 0 1 {name=l1233 lab=t31}
C {devices/lab_pin.sym} 1630 -1600 0 0 {name=l1234 lab=dh0}
C {devices/lab_pin.sym} 1670 -1570 0 1 {name=l1235 lab=m0_15}
C {devices/lab_pin.sym} 1670 -1600 0 1 {name=l1236 lab=vss}
C {devices/lab_pin.sym} 1720 -1630 0 1 {name=l1237 lab=t32}
C {devices/lab_pin.sym} 1680 -1600 0 0 {name=l1238 lab=dhn0}
C {devices/lab_pin.sym} 1720 -1570 0 1 {name=l1239 lab=m0_16}
C {devices/lab_pin.sym} 1720 -1600 0 1 {name=l1240 lab=vss}
C {devices/lab_pin.sym} 1770 -1630 0 1 {name=l1241 lab=t33}
C {devices/lab_pin.sym} 1730 -1600 0 0 {name=l1242 lab=dh0}
C {devices/lab_pin.sym} 1770 -1570 0 1 {name=l1243 lab=m0_16}
C {devices/lab_pin.sym} 1770 -1600 0 1 {name=l1244 lab=vss}
C {devices/lab_pin.sym} 1820 -1630 0 1 {name=l1245 lab=t34}
C {devices/lab_pin.sym} 1780 -1600 0 0 {name=l1246 lab=dhn0}
C {devices/lab_pin.sym} 1820 -1570 0 1 {name=l1247 lab=m0_17}
C {devices/lab_pin.sym} 1820 -1600 0 1 {name=l1248 lab=vss}
C {devices/lab_pin.sym} 1870 -1630 0 1 {name=l1249 lab=t35}
C {devices/lab_pin.sym} 1830 -1600 0 0 {name=l1250 lab=dh0}
C {devices/lab_pin.sym} 1870 -1570 0 1 {name=l1251 lab=m0_17}
C {devices/lab_pin.sym} 1870 -1600 0 1 {name=l1252 lab=vss}
C {devices/lab_pin.sym} 1920 -1630 0 1 {name=l1253 lab=t36}
C {devices/lab_pin.sym} 1880 -1600 0 0 {name=l1254 lab=dhn0}
C {devices/lab_pin.sym} 1920 -1570 0 1 {name=l1255 lab=m0_18}
C {devices/lab_pin.sym} 1920 -1600 0 1 {name=l1256 lab=vss}
C {devices/lab_pin.sym} 1970 -1630 0 1 {name=l1257 lab=t37}
C {devices/lab_pin.sym} 1930 -1600 0 0 {name=l1258 lab=dh0}
C {devices/lab_pin.sym} 1970 -1570 0 1 {name=l1259 lab=m0_18}
C {devices/lab_pin.sym} 1970 -1600 0 1 {name=l1260 lab=vss}
C {devices/lab_pin.sym} 2020 -1630 0 1 {name=l1261 lab=t38}
C {devices/lab_pin.sym} 1980 -1600 0 0 {name=l1262 lab=dhn0}
C {devices/lab_pin.sym} 2020 -1570 0 1 {name=l1263 lab=m0_19}
C {devices/lab_pin.sym} 2020 -1600 0 1 {name=l1264 lab=vss}
C {devices/lab_pin.sym} 2070 -1630 0 1 {name=l1265 lab=t39}
C {devices/lab_pin.sym} 2030 -1600 0 0 {name=l1266 lab=dh0}
C {devices/lab_pin.sym} 2070 -1570 0 1 {name=l1267 lab=m0_19}
C {devices/lab_pin.sym} 2070 -1600 0 1 {name=l1268 lab=vss}
C {devices/lab_pin.sym} 2120 -1630 0 1 {name=l1269 lab=t40}
C {devices/lab_pin.sym} 2080 -1600 0 0 {name=l1270 lab=dhn0}
C {devices/lab_pin.sym} 2120 -1570 0 1 {name=l1271 lab=m0_20}
C {devices/lab_pin.sym} 2120 -1600 0 1 {name=l1272 lab=vss}
C {devices/lab_pin.sym} 2170 -1630 0 1 {name=l1273 lab=t41}
C {devices/lab_pin.sym} 2130 -1600 0 0 {name=l1274 lab=dh0}
C {devices/lab_pin.sym} 2170 -1570 0 1 {name=l1275 lab=m0_20}
C {devices/lab_pin.sym} 2170 -1600 0 1 {name=l1276 lab=vss}
C {devices/lab_pin.sym} 2220 -1630 0 1 {name=l1277 lab=t42}
C {devices/lab_pin.sym} 2180 -1600 0 0 {name=l1278 lab=dhn0}
C {devices/lab_pin.sym} 2220 -1570 0 1 {name=l1279 lab=m0_21}
C {devices/lab_pin.sym} 2220 -1600 0 1 {name=l1280 lab=vss}
C {devices/lab_pin.sym} 2270 -1630 0 1 {name=l1281 lab=t43}
C {devices/lab_pin.sym} 2230 -1600 0 0 {name=l1282 lab=dh0}
C {devices/lab_pin.sym} 2270 -1570 0 1 {name=l1283 lab=m0_21}
C {devices/lab_pin.sym} 2270 -1600 0 1 {name=l1284 lab=vss}
C {devices/lab_pin.sym} 2320 -1630 0 1 {name=l1285 lab=t44}
C {devices/lab_pin.sym} 2280 -1600 0 0 {name=l1286 lab=dhn0}
C {devices/lab_pin.sym} 2320 -1570 0 1 {name=l1287 lab=m0_22}
C {devices/lab_pin.sym} 2320 -1600 0 1 {name=l1288 lab=vss}
C {devices/lab_pin.sym} 2370 -1630 0 1 {name=l1289 lab=t45}
C {devices/lab_pin.sym} 2330 -1600 0 0 {name=l1290 lab=dh0}
C {devices/lab_pin.sym} 2370 -1570 0 1 {name=l1291 lab=m0_22}
C {devices/lab_pin.sym} 2370 -1600 0 1 {name=l1292 lab=vss}
C {devices/lab_pin.sym} 2420 -1630 0 1 {name=l1293 lab=t46}
C {devices/lab_pin.sym} 2380 -1600 0 0 {name=l1294 lab=dhn0}
C {devices/lab_pin.sym} 2420 -1570 0 1 {name=l1295 lab=m0_23}
C {devices/lab_pin.sym} 2420 -1600 0 1 {name=l1296 lab=vss}
C {devices/lab_pin.sym} 2470 -1630 0 1 {name=l1297 lab=t47}
C {devices/lab_pin.sym} 2430 -1600 0 0 {name=l1298 lab=dh0}
C {devices/lab_pin.sym} 2470 -1570 0 1 {name=l1299 lab=m0_23}
C {devices/lab_pin.sym} 2470 -1600 0 1 {name=l1300 lab=vss}
C {devices/lab_pin.sym} 2520 -1630 0 1 {name=l1301 lab=t48}
C {devices/lab_pin.sym} 2480 -1600 0 0 {name=l1302 lab=dhn0}
C {devices/lab_pin.sym} 2520 -1570 0 1 {name=l1303 lab=m0_24}
C {devices/lab_pin.sym} 2520 -1600 0 1 {name=l1304 lab=vss}
C {devices/lab_pin.sym} 2570 -1630 0 1 {name=l1305 lab=t49}
C {devices/lab_pin.sym} 2530 -1600 0 0 {name=l1306 lab=dh0}
C {devices/lab_pin.sym} 2570 -1570 0 1 {name=l1307 lab=m0_24}
C {devices/lab_pin.sym} 2570 -1600 0 1 {name=l1308 lab=vss}
C {devices/lab_pin.sym} 2620 -1630 0 1 {name=l1309 lab=t50}
C {devices/lab_pin.sym} 2580 -1600 0 0 {name=l1310 lab=dhn0}
C {devices/lab_pin.sym} 2620 -1570 0 1 {name=l1311 lab=m0_25}
C {devices/lab_pin.sym} 2620 -1600 0 1 {name=l1312 lab=vss}
C {devices/lab_pin.sym} 2670 -1630 0 1 {name=l1313 lab=t51}
C {devices/lab_pin.sym} 2630 -1600 0 0 {name=l1314 lab=dh0}
C {devices/lab_pin.sym} 2670 -1570 0 1 {name=l1315 lab=m0_25}
C {devices/lab_pin.sym} 2670 -1600 0 1 {name=l1316 lab=vss}
C {devices/lab_pin.sym} 2720 -1630 0 1 {name=l1317 lab=t52}
C {devices/lab_pin.sym} 2680 -1600 0 0 {name=l1318 lab=dhn0}
C {devices/lab_pin.sym} 2720 -1570 0 1 {name=l1319 lab=m0_26}
C {devices/lab_pin.sym} 2720 -1600 0 1 {name=l1320 lab=vss}
C {devices/lab_pin.sym} 2770 -1630 0 1 {name=l1321 lab=t53}
C {devices/lab_pin.sym} 2730 -1600 0 0 {name=l1322 lab=dh0}
C {devices/lab_pin.sym} 2770 -1570 0 1 {name=l1323 lab=m0_26}
C {devices/lab_pin.sym} 2770 -1600 0 1 {name=l1324 lab=vss}
C {devices/lab_pin.sym} 2820 -1630 0 1 {name=l1325 lab=t54}
C {devices/lab_pin.sym} 2780 -1600 0 0 {name=l1326 lab=dhn0}
C {devices/lab_pin.sym} 2820 -1570 0 1 {name=l1327 lab=m0_27}
C {devices/lab_pin.sym} 2820 -1600 0 1 {name=l1328 lab=vss}
C {devices/lab_pin.sym} 2870 -1630 0 1 {name=l1329 lab=t55}
C {devices/lab_pin.sym} 2830 -1600 0 0 {name=l1330 lab=dh0}
C {devices/lab_pin.sym} 2870 -1570 0 1 {name=l1331 lab=m0_27}
C {devices/lab_pin.sym} 2870 -1600 0 1 {name=l1332 lab=vss}
C {devices/lab_pin.sym} 2920 -1630 0 1 {name=l1333 lab=t56}
C {devices/lab_pin.sym} 2880 -1600 0 0 {name=l1334 lab=dhn0}
C {devices/lab_pin.sym} 2920 -1570 0 1 {name=l1335 lab=m0_28}
C {devices/lab_pin.sym} 2920 -1600 0 1 {name=l1336 lab=vss}
C {devices/lab_pin.sym} 2970 -1630 0 1 {name=l1337 lab=t57}
C {devices/lab_pin.sym} 2930 -1600 0 0 {name=l1338 lab=dh0}
C {devices/lab_pin.sym} 2970 -1570 0 1 {name=l1339 lab=m0_28}
C {devices/lab_pin.sym} 2970 -1600 0 1 {name=l1340 lab=vss}
C {devices/lab_pin.sym} 3020 -1630 0 1 {name=l1341 lab=t58}
C {devices/lab_pin.sym} 2980 -1600 0 0 {name=l1342 lab=dhn0}
C {devices/lab_pin.sym} 3020 -1570 0 1 {name=l1343 lab=m0_29}
C {devices/lab_pin.sym} 3020 -1600 0 1 {name=l1344 lab=vss}
C {devices/lab_pin.sym} 3070 -1630 0 1 {name=l1345 lab=t59}
C {devices/lab_pin.sym} 3030 -1600 0 0 {name=l1346 lab=dh0}
C {devices/lab_pin.sym} 3070 -1570 0 1 {name=l1347 lab=m0_29}
C {devices/lab_pin.sym} 3070 -1600 0 1 {name=l1348 lab=vss}
C {devices/lab_pin.sym} 3120 -1630 0 1 {name=l1349 lab=t60}
C {devices/lab_pin.sym} 3080 -1600 0 0 {name=l1350 lab=dhn0}
C {devices/lab_pin.sym} 3120 -1570 0 1 {name=l1351 lab=m0_30}
C {devices/lab_pin.sym} 3120 -1600 0 1 {name=l1352 lab=vss}
C {devices/lab_pin.sym} 3170 -1630 0 1 {name=l1353 lab=t61}
C {devices/lab_pin.sym} 3130 -1600 0 0 {name=l1354 lab=dh0}
C {devices/lab_pin.sym} 3170 -1570 0 1 {name=l1355 lab=m0_30}
C {devices/lab_pin.sym} 3170 -1600 0 1 {name=l1356 lab=vss}
C {devices/lab_pin.sym} 3220 -1630 0 1 {name=l1357 lab=t62}
C {devices/lab_pin.sym} 3180 -1600 0 0 {name=l1358 lab=dhn0}
C {devices/lab_pin.sym} 3220 -1570 0 1 {name=l1359 lab=m0_31}
C {devices/lab_pin.sym} 3220 -1600 0 1 {name=l1360 lab=vss}
C {devices/lab_pin.sym} 3270 -1630 0 1 {name=l1361 lab=t63}
C {devices/lab_pin.sym} 3230 -1600 0 0 {name=l1362 lab=dh0}
C {devices/lab_pin.sym} 3270 -1570 0 1 {name=l1363 lab=m0_31}
C {devices/lab_pin.sym} 3270 -1600 0 1 {name=l1364 lab=vss}
C {devices/lab_pin.sym} 120 -1550 0 1 {name=l1365 lab=t64}
C {devices/lab_pin.sym} 80 -1520 0 0 {name=l1366 lab=dhn0}
C {devices/lab_pin.sym} 120 -1490 0 1 {name=l1367 lab=m0_32}
C {devices/lab_pin.sym} 120 -1520 0 1 {name=l1368 lab=vss}
C {devices/lab_pin.sym} 170 -1550 0 1 {name=l1369 lab=t65}
C {devices/lab_pin.sym} 130 -1520 0 0 {name=l1370 lab=dh0}
C {devices/lab_pin.sym} 170 -1490 0 1 {name=l1371 lab=m0_32}
C {devices/lab_pin.sym} 170 -1520 0 1 {name=l1372 lab=vss}
C {devices/lab_pin.sym} 220 -1550 0 1 {name=l1373 lab=t66}
C {devices/lab_pin.sym} 180 -1520 0 0 {name=l1374 lab=dhn0}
C {devices/lab_pin.sym} 220 -1490 0 1 {name=l1375 lab=m0_33}
C {devices/lab_pin.sym} 220 -1520 0 1 {name=l1376 lab=vss}
C {devices/lab_pin.sym} 270 -1550 0 1 {name=l1377 lab=t67}
C {devices/lab_pin.sym} 230 -1520 0 0 {name=l1378 lab=dh0}
C {devices/lab_pin.sym} 270 -1490 0 1 {name=l1379 lab=m0_33}
C {devices/lab_pin.sym} 270 -1520 0 1 {name=l1380 lab=vss}
C {devices/lab_pin.sym} 320 -1550 0 1 {name=l1381 lab=t68}
C {devices/lab_pin.sym} 280 -1520 0 0 {name=l1382 lab=dhn0}
C {devices/lab_pin.sym} 320 -1490 0 1 {name=l1383 lab=m0_34}
C {devices/lab_pin.sym} 320 -1520 0 1 {name=l1384 lab=vss}
C {devices/lab_pin.sym} 370 -1550 0 1 {name=l1385 lab=t69}
C {devices/lab_pin.sym} 330 -1520 0 0 {name=l1386 lab=dh0}
C {devices/lab_pin.sym} 370 -1490 0 1 {name=l1387 lab=m0_34}
C {devices/lab_pin.sym} 370 -1520 0 1 {name=l1388 lab=vss}
C {devices/lab_pin.sym} 420 -1550 0 1 {name=l1389 lab=t70}
C {devices/lab_pin.sym} 380 -1520 0 0 {name=l1390 lab=dhn0}
C {devices/lab_pin.sym} 420 -1490 0 1 {name=l1391 lab=m0_35}
C {devices/lab_pin.sym} 420 -1520 0 1 {name=l1392 lab=vss}
C {devices/lab_pin.sym} 470 -1550 0 1 {name=l1393 lab=t71}
C {devices/lab_pin.sym} 430 -1520 0 0 {name=l1394 lab=dh0}
C {devices/lab_pin.sym} 470 -1490 0 1 {name=l1395 lab=m0_35}
C {devices/lab_pin.sym} 470 -1520 0 1 {name=l1396 lab=vss}
C {devices/lab_pin.sym} 520 -1550 0 1 {name=l1397 lab=t72}
C {devices/lab_pin.sym} 480 -1520 0 0 {name=l1398 lab=dhn0}
C {devices/lab_pin.sym} 520 -1490 0 1 {name=l1399 lab=m0_36}
C {devices/lab_pin.sym} 520 -1520 0 1 {name=l1400 lab=vss}
C {devices/lab_pin.sym} 570 -1550 0 1 {name=l1401 lab=t73}
C {devices/lab_pin.sym} 530 -1520 0 0 {name=l1402 lab=dh0}
C {devices/lab_pin.sym} 570 -1490 0 1 {name=l1403 lab=m0_36}
C {devices/lab_pin.sym} 570 -1520 0 1 {name=l1404 lab=vss}
C {devices/lab_pin.sym} 620 -1550 0 1 {name=l1405 lab=t74}
C {devices/lab_pin.sym} 580 -1520 0 0 {name=l1406 lab=dhn0}
C {devices/lab_pin.sym} 620 -1490 0 1 {name=l1407 lab=m0_37}
C {devices/lab_pin.sym} 620 -1520 0 1 {name=l1408 lab=vss}
C {devices/lab_pin.sym} 670 -1550 0 1 {name=l1409 lab=t75}
C {devices/lab_pin.sym} 630 -1520 0 0 {name=l1410 lab=dh0}
C {devices/lab_pin.sym} 670 -1490 0 1 {name=l1411 lab=m0_37}
C {devices/lab_pin.sym} 670 -1520 0 1 {name=l1412 lab=vss}
C {devices/lab_pin.sym} 720 -1550 0 1 {name=l1413 lab=t76}
C {devices/lab_pin.sym} 680 -1520 0 0 {name=l1414 lab=dhn0}
C {devices/lab_pin.sym} 720 -1490 0 1 {name=l1415 lab=m0_38}
C {devices/lab_pin.sym} 720 -1520 0 1 {name=l1416 lab=vss}
C {devices/lab_pin.sym} 770 -1550 0 1 {name=l1417 lab=t77}
C {devices/lab_pin.sym} 730 -1520 0 0 {name=l1418 lab=dh0}
C {devices/lab_pin.sym} 770 -1490 0 1 {name=l1419 lab=m0_38}
C {devices/lab_pin.sym} 770 -1520 0 1 {name=l1420 lab=vss}
C {devices/lab_pin.sym} 820 -1550 0 1 {name=l1421 lab=t78}
C {devices/lab_pin.sym} 780 -1520 0 0 {name=l1422 lab=dhn0}
C {devices/lab_pin.sym} 820 -1490 0 1 {name=l1423 lab=m0_39}
C {devices/lab_pin.sym} 820 -1520 0 1 {name=l1424 lab=vss}
C {devices/lab_pin.sym} 870 -1550 0 1 {name=l1425 lab=t79}
C {devices/lab_pin.sym} 830 -1520 0 0 {name=l1426 lab=dh0}
C {devices/lab_pin.sym} 870 -1490 0 1 {name=l1427 lab=m0_39}
C {devices/lab_pin.sym} 870 -1520 0 1 {name=l1428 lab=vss}
C {devices/lab_pin.sym} 920 -1550 0 1 {name=l1429 lab=t80}
C {devices/lab_pin.sym} 880 -1520 0 0 {name=l1430 lab=dhn0}
C {devices/lab_pin.sym} 920 -1490 0 1 {name=l1431 lab=m0_40}
C {devices/lab_pin.sym} 920 -1520 0 1 {name=l1432 lab=vss}
C {devices/lab_pin.sym} 970 -1550 0 1 {name=l1433 lab=t81}
C {devices/lab_pin.sym} 930 -1520 0 0 {name=l1434 lab=dh0}
C {devices/lab_pin.sym} 970 -1490 0 1 {name=l1435 lab=m0_40}
C {devices/lab_pin.sym} 970 -1520 0 1 {name=l1436 lab=vss}
C {devices/lab_pin.sym} 1020 -1550 0 1 {name=l1437 lab=t82}
C {devices/lab_pin.sym} 980 -1520 0 0 {name=l1438 lab=dhn0}
C {devices/lab_pin.sym} 1020 -1490 0 1 {name=l1439 lab=m0_41}
C {devices/lab_pin.sym} 1020 -1520 0 1 {name=l1440 lab=vss}
C {devices/lab_pin.sym} 1070 -1550 0 1 {name=l1441 lab=t83}
C {devices/lab_pin.sym} 1030 -1520 0 0 {name=l1442 lab=dh0}
C {devices/lab_pin.sym} 1070 -1490 0 1 {name=l1443 lab=m0_41}
C {devices/lab_pin.sym} 1070 -1520 0 1 {name=l1444 lab=vss}
C {devices/lab_pin.sym} 1120 -1550 0 1 {name=l1445 lab=t84}
C {devices/lab_pin.sym} 1080 -1520 0 0 {name=l1446 lab=dhn0}
C {devices/lab_pin.sym} 1120 -1490 0 1 {name=l1447 lab=m0_42}
C {devices/lab_pin.sym} 1120 -1520 0 1 {name=l1448 lab=vss}
C {devices/lab_pin.sym} 1170 -1550 0 1 {name=l1449 lab=t85}
C {devices/lab_pin.sym} 1130 -1520 0 0 {name=l1450 lab=dh0}
C {devices/lab_pin.sym} 1170 -1490 0 1 {name=l1451 lab=m0_42}
C {devices/lab_pin.sym} 1170 -1520 0 1 {name=l1452 lab=vss}
C {devices/lab_pin.sym} 1220 -1550 0 1 {name=l1453 lab=t86}
C {devices/lab_pin.sym} 1180 -1520 0 0 {name=l1454 lab=dhn0}
C {devices/lab_pin.sym} 1220 -1490 0 1 {name=l1455 lab=m0_43}
C {devices/lab_pin.sym} 1220 -1520 0 1 {name=l1456 lab=vss}
C {devices/lab_pin.sym} 1270 -1550 0 1 {name=l1457 lab=t87}
C {devices/lab_pin.sym} 1230 -1520 0 0 {name=l1458 lab=dh0}
C {devices/lab_pin.sym} 1270 -1490 0 1 {name=l1459 lab=m0_43}
C {devices/lab_pin.sym} 1270 -1520 0 1 {name=l1460 lab=vss}
C {devices/lab_pin.sym} 1320 -1550 0 1 {name=l1461 lab=t88}
C {devices/lab_pin.sym} 1280 -1520 0 0 {name=l1462 lab=dhn0}
C {devices/lab_pin.sym} 1320 -1490 0 1 {name=l1463 lab=m0_44}
C {devices/lab_pin.sym} 1320 -1520 0 1 {name=l1464 lab=vss}
C {devices/lab_pin.sym} 1370 -1550 0 1 {name=l1465 lab=t89}
C {devices/lab_pin.sym} 1330 -1520 0 0 {name=l1466 lab=dh0}
C {devices/lab_pin.sym} 1370 -1490 0 1 {name=l1467 lab=m0_44}
C {devices/lab_pin.sym} 1370 -1520 0 1 {name=l1468 lab=vss}
C {devices/lab_pin.sym} 1420 -1550 0 1 {name=l1469 lab=t90}
C {devices/lab_pin.sym} 1380 -1520 0 0 {name=l1470 lab=dhn0}
C {devices/lab_pin.sym} 1420 -1490 0 1 {name=l1471 lab=m0_45}
C {devices/lab_pin.sym} 1420 -1520 0 1 {name=l1472 lab=vss}
C {devices/lab_pin.sym} 1470 -1550 0 1 {name=l1473 lab=t91}
C {devices/lab_pin.sym} 1430 -1520 0 0 {name=l1474 lab=dh0}
C {devices/lab_pin.sym} 1470 -1490 0 1 {name=l1475 lab=m0_45}
C {devices/lab_pin.sym} 1470 -1520 0 1 {name=l1476 lab=vss}
C {devices/lab_pin.sym} 1520 -1550 0 1 {name=l1477 lab=t92}
C {devices/lab_pin.sym} 1480 -1520 0 0 {name=l1478 lab=dhn0}
C {devices/lab_pin.sym} 1520 -1490 0 1 {name=l1479 lab=m0_46}
C {devices/lab_pin.sym} 1520 -1520 0 1 {name=l1480 lab=vss}
C {devices/lab_pin.sym} 1570 -1550 0 1 {name=l1481 lab=t93}
C {devices/lab_pin.sym} 1530 -1520 0 0 {name=l1482 lab=dh0}
C {devices/lab_pin.sym} 1570 -1490 0 1 {name=l1483 lab=m0_46}
C {devices/lab_pin.sym} 1570 -1520 0 1 {name=l1484 lab=vss}
C {devices/lab_pin.sym} 1620 -1550 0 1 {name=l1485 lab=t94}
C {devices/lab_pin.sym} 1580 -1520 0 0 {name=l1486 lab=dhn0}
C {devices/lab_pin.sym} 1620 -1490 0 1 {name=l1487 lab=m0_47}
C {devices/lab_pin.sym} 1620 -1520 0 1 {name=l1488 lab=vss}
C {devices/lab_pin.sym} 1670 -1550 0 1 {name=l1489 lab=t95}
C {devices/lab_pin.sym} 1630 -1520 0 0 {name=l1490 lab=dh0}
C {devices/lab_pin.sym} 1670 -1490 0 1 {name=l1491 lab=m0_47}
C {devices/lab_pin.sym} 1670 -1520 0 1 {name=l1492 lab=vss}
C {devices/lab_pin.sym} 1720 -1550 0 1 {name=l1493 lab=t96}
C {devices/lab_pin.sym} 1680 -1520 0 0 {name=l1494 lab=dhn0}
C {devices/lab_pin.sym} 1720 -1490 0 1 {name=l1495 lab=m0_48}
C {devices/lab_pin.sym} 1720 -1520 0 1 {name=l1496 lab=vss}
C {devices/lab_pin.sym} 1770 -1550 0 1 {name=l1497 lab=t97}
C {devices/lab_pin.sym} 1730 -1520 0 0 {name=l1498 lab=dh0}
C {devices/lab_pin.sym} 1770 -1490 0 1 {name=l1499 lab=m0_48}
C {devices/lab_pin.sym} 1770 -1520 0 1 {name=l1500 lab=vss}
C {devices/lab_pin.sym} 1820 -1550 0 1 {name=l1501 lab=t98}
C {devices/lab_pin.sym} 1780 -1520 0 0 {name=l1502 lab=dhn0}
C {devices/lab_pin.sym} 1820 -1490 0 1 {name=l1503 lab=m0_49}
C {devices/lab_pin.sym} 1820 -1520 0 1 {name=l1504 lab=vss}
C {devices/lab_pin.sym} 1870 -1550 0 1 {name=l1505 lab=t99}
C {devices/lab_pin.sym} 1830 -1520 0 0 {name=l1506 lab=dh0}
C {devices/lab_pin.sym} 1870 -1490 0 1 {name=l1507 lab=m0_49}
C {devices/lab_pin.sym} 1870 -1520 0 1 {name=l1508 lab=vss}
C {devices/lab_pin.sym} 1920 -1550 0 1 {name=l1509 lab=t100}
C {devices/lab_pin.sym} 1880 -1520 0 0 {name=l1510 lab=dhn0}
C {devices/lab_pin.sym} 1920 -1490 0 1 {name=l1511 lab=m0_50}
C {devices/lab_pin.sym} 1920 -1520 0 1 {name=l1512 lab=vss}
C {devices/lab_pin.sym} 1970 -1550 0 1 {name=l1513 lab=t101}
C {devices/lab_pin.sym} 1930 -1520 0 0 {name=l1514 lab=dh0}
C {devices/lab_pin.sym} 1970 -1490 0 1 {name=l1515 lab=m0_50}
C {devices/lab_pin.sym} 1970 -1520 0 1 {name=l1516 lab=vss}
C {devices/lab_pin.sym} 2020 -1550 0 1 {name=l1517 lab=t102}
C {devices/lab_pin.sym} 1980 -1520 0 0 {name=l1518 lab=dhn0}
C {devices/lab_pin.sym} 2020 -1490 0 1 {name=l1519 lab=m0_51}
C {devices/lab_pin.sym} 2020 -1520 0 1 {name=l1520 lab=vss}
C {devices/lab_pin.sym} 2070 -1550 0 1 {name=l1521 lab=t103}
C {devices/lab_pin.sym} 2030 -1520 0 0 {name=l1522 lab=dh0}
C {devices/lab_pin.sym} 2070 -1490 0 1 {name=l1523 lab=m0_51}
C {devices/lab_pin.sym} 2070 -1520 0 1 {name=l1524 lab=vss}
C {devices/lab_pin.sym} 2120 -1550 0 1 {name=l1525 lab=t104}
C {devices/lab_pin.sym} 2080 -1520 0 0 {name=l1526 lab=dhn0}
C {devices/lab_pin.sym} 2120 -1490 0 1 {name=l1527 lab=m0_52}
C {devices/lab_pin.sym} 2120 -1520 0 1 {name=l1528 lab=vss}
C {devices/lab_pin.sym} 2170 -1550 0 1 {name=l1529 lab=t105}
C {devices/lab_pin.sym} 2130 -1520 0 0 {name=l1530 lab=dh0}
C {devices/lab_pin.sym} 2170 -1490 0 1 {name=l1531 lab=m0_52}
C {devices/lab_pin.sym} 2170 -1520 0 1 {name=l1532 lab=vss}
C {devices/lab_pin.sym} 2220 -1550 0 1 {name=l1533 lab=t106}
C {devices/lab_pin.sym} 2180 -1520 0 0 {name=l1534 lab=dhn0}
C {devices/lab_pin.sym} 2220 -1490 0 1 {name=l1535 lab=m0_53}
C {devices/lab_pin.sym} 2220 -1520 0 1 {name=l1536 lab=vss}
C {devices/lab_pin.sym} 2270 -1550 0 1 {name=l1537 lab=t107}
C {devices/lab_pin.sym} 2230 -1520 0 0 {name=l1538 lab=dh0}
C {devices/lab_pin.sym} 2270 -1490 0 1 {name=l1539 lab=m0_53}
C {devices/lab_pin.sym} 2270 -1520 0 1 {name=l1540 lab=vss}
C {devices/lab_pin.sym} 2320 -1550 0 1 {name=l1541 lab=t108}
C {devices/lab_pin.sym} 2280 -1520 0 0 {name=l1542 lab=dhn0}
C {devices/lab_pin.sym} 2320 -1490 0 1 {name=l1543 lab=m0_54}
C {devices/lab_pin.sym} 2320 -1520 0 1 {name=l1544 lab=vss}
C {devices/lab_pin.sym} 2370 -1550 0 1 {name=l1545 lab=t109}
C {devices/lab_pin.sym} 2330 -1520 0 0 {name=l1546 lab=dh0}
C {devices/lab_pin.sym} 2370 -1490 0 1 {name=l1547 lab=m0_54}
C {devices/lab_pin.sym} 2370 -1520 0 1 {name=l1548 lab=vss}
C {devices/lab_pin.sym} 2420 -1550 0 1 {name=l1549 lab=t110}
C {devices/lab_pin.sym} 2380 -1520 0 0 {name=l1550 lab=dhn0}
C {devices/lab_pin.sym} 2420 -1490 0 1 {name=l1551 lab=m0_55}
C {devices/lab_pin.sym} 2420 -1520 0 1 {name=l1552 lab=vss}
C {devices/lab_pin.sym} 2470 -1550 0 1 {name=l1553 lab=t111}
C {devices/lab_pin.sym} 2430 -1520 0 0 {name=l1554 lab=dh0}
C {devices/lab_pin.sym} 2470 -1490 0 1 {name=l1555 lab=m0_55}
C {devices/lab_pin.sym} 2470 -1520 0 1 {name=l1556 lab=vss}
C {devices/lab_pin.sym} 2520 -1550 0 1 {name=l1557 lab=t112}
C {devices/lab_pin.sym} 2480 -1520 0 0 {name=l1558 lab=dhn0}
C {devices/lab_pin.sym} 2520 -1490 0 1 {name=l1559 lab=m0_56}
C {devices/lab_pin.sym} 2520 -1520 0 1 {name=l1560 lab=vss}
C {devices/lab_pin.sym} 2570 -1550 0 1 {name=l1561 lab=t113}
C {devices/lab_pin.sym} 2530 -1520 0 0 {name=l1562 lab=dh0}
C {devices/lab_pin.sym} 2570 -1490 0 1 {name=l1563 lab=m0_56}
C {devices/lab_pin.sym} 2570 -1520 0 1 {name=l1564 lab=vss}
C {devices/lab_pin.sym} 2620 -1550 0 1 {name=l1565 lab=t114}
C {devices/lab_pin.sym} 2580 -1520 0 0 {name=l1566 lab=dhn0}
C {devices/lab_pin.sym} 2620 -1490 0 1 {name=l1567 lab=m0_57}
C {devices/lab_pin.sym} 2620 -1520 0 1 {name=l1568 lab=vss}
C {devices/lab_pin.sym} 2670 -1550 0 1 {name=l1569 lab=t115}
C {devices/lab_pin.sym} 2630 -1520 0 0 {name=l1570 lab=dh0}
C {devices/lab_pin.sym} 2670 -1490 0 1 {name=l1571 lab=m0_57}
C {devices/lab_pin.sym} 2670 -1520 0 1 {name=l1572 lab=vss}
C {devices/lab_pin.sym} 2720 -1550 0 1 {name=l1573 lab=t116}
C {devices/lab_pin.sym} 2680 -1520 0 0 {name=l1574 lab=dhn0}
C {devices/lab_pin.sym} 2720 -1490 0 1 {name=l1575 lab=m0_58}
C {devices/lab_pin.sym} 2720 -1520 0 1 {name=l1576 lab=vss}
C {devices/lab_pin.sym} 2770 -1550 0 1 {name=l1577 lab=t117}
C {devices/lab_pin.sym} 2730 -1520 0 0 {name=l1578 lab=dh0}
C {devices/lab_pin.sym} 2770 -1490 0 1 {name=l1579 lab=m0_58}
C {devices/lab_pin.sym} 2770 -1520 0 1 {name=l1580 lab=vss}
C {devices/lab_pin.sym} 2820 -1550 0 1 {name=l1581 lab=t118}
C {devices/lab_pin.sym} 2780 -1520 0 0 {name=l1582 lab=dhn0}
C {devices/lab_pin.sym} 2820 -1490 0 1 {name=l1583 lab=m0_59}
C {devices/lab_pin.sym} 2820 -1520 0 1 {name=l1584 lab=vss}
C {devices/lab_pin.sym} 2870 -1550 0 1 {name=l1585 lab=t119}
C {devices/lab_pin.sym} 2830 -1520 0 0 {name=l1586 lab=dh0}
C {devices/lab_pin.sym} 2870 -1490 0 1 {name=l1587 lab=m0_59}
C {devices/lab_pin.sym} 2870 -1520 0 1 {name=l1588 lab=vss}
C {devices/lab_pin.sym} 2920 -1550 0 1 {name=l1589 lab=t120}
C {devices/lab_pin.sym} 2880 -1520 0 0 {name=l1590 lab=dhn0}
C {devices/lab_pin.sym} 2920 -1490 0 1 {name=l1591 lab=m0_60}
C {devices/lab_pin.sym} 2920 -1520 0 1 {name=l1592 lab=vss}
C {devices/lab_pin.sym} 2970 -1550 0 1 {name=l1593 lab=t121}
C {devices/lab_pin.sym} 2930 -1520 0 0 {name=l1594 lab=dh0}
C {devices/lab_pin.sym} 2970 -1490 0 1 {name=l1595 lab=m0_60}
C {devices/lab_pin.sym} 2970 -1520 0 1 {name=l1596 lab=vss}
C {devices/lab_pin.sym} 3020 -1550 0 1 {name=l1597 lab=t122}
C {devices/lab_pin.sym} 2980 -1520 0 0 {name=l1598 lab=dhn0}
C {devices/lab_pin.sym} 3020 -1490 0 1 {name=l1599 lab=m0_61}
C {devices/lab_pin.sym} 3020 -1520 0 1 {name=l1600 lab=vss}
C {devices/lab_pin.sym} 3070 -1550 0 1 {name=l1601 lab=t123}
C {devices/lab_pin.sym} 3030 -1520 0 0 {name=l1602 lab=dh0}
C {devices/lab_pin.sym} 3070 -1490 0 1 {name=l1603 lab=m0_61}
C {devices/lab_pin.sym} 3070 -1520 0 1 {name=l1604 lab=vss}
C {devices/lab_pin.sym} 3120 -1550 0 1 {name=l1605 lab=t124}
C {devices/lab_pin.sym} 3080 -1520 0 0 {name=l1606 lab=dhn0}
C {devices/lab_pin.sym} 3120 -1490 0 1 {name=l1607 lab=m0_62}
C {devices/lab_pin.sym} 3120 -1520 0 1 {name=l1608 lab=vss}
C {devices/lab_pin.sym} 3170 -1550 0 1 {name=l1609 lab=t125}
C {devices/lab_pin.sym} 3130 -1520 0 0 {name=l1610 lab=dh0}
C {devices/lab_pin.sym} 3170 -1490 0 1 {name=l1611 lab=m0_62}
C {devices/lab_pin.sym} 3170 -1520 0 1 {name=l1612 lab=vss}
C {devices/lab_pin.sym} 3220 -1550 0 1 {name=l1613 lab=t126}
C {devices/lab_pin.sym} 3180 -1520 0 0 {name=l1614 lab=dhn0}
C {devices/lab_pin.sym} 3220 -1490 0 1 {name=l1615 lab=m0_63}
C {devices/lab_pin.sym} 3220 -1520 0 1 {name=l1616 lab=vss}
C {devices/lab_pin.sym} 3270 -1550 0 1 {name=l1617 lab=t127}
C {devices/lab_pin.sym} 3230 -1520 0 0 {name=l1618 lab=dh0}
C {devices/lab_pin.sym} 3270 -1490 0 1 {name=l1619 lab=m0_63}
C {devices/lab_pin.sym} 3270 -1520 0 1 {name=l1620 lab=vss}
C {devices/lab_pin.sym} 120 -1470 0 1 {name=l1621 lab=t128}
C {devices/lab_pin.sym} 80 -1440 0 0 {name=l1622 lab=dhn0}
C {devices/lab_pin.sym} 120 -1410 0 1 {name=l1623 lab=m0_64}
C {devices/lab_pin.sym} 120 -1440 0 1 {name=l1624 lab=vss}
C {devices/lab_pin.sym} 170 -1470 0 1 {name=l1625 lab=t129}
C {devices/lab_pin.sym} 130 -1440 0 0 {name=l1626 lab=dh0}
C {devices/lab_pin.sym} 170 -1410 0 1 {name=l1627 lab=m0_64}
C {devices/lab_pin.sym} 170 -1440 0 1 {name=l1628 lab=vss}
C {devices/lab_pin.sym} 220 -1470 0 1 {name=l1629 lab=t130}
C {devices/lab_pin.sym} 180 -1440 0 0 {name=l1630 lab=dhn0}
C {devices/lab_pin.sym} 220 -1410 0 1 {name=l1631 lab=m0_65}
C {devices/lab_pin.sym} 220 -1440 0 1 {name=l1632 lab=vss}
C {devices/lab_pin.sym} 270 -1470 0 1 {name=l1633 lab=t131}
C {devices/lab_pin.sym} 230 -1440 0 0 {name=l1634 lab=dh0}
C {devices/lab_pin.sym} 270 -1410 0 1 {name=l1635 lab=m0_65}
C {devices/lab_pin.sym} 270 -1440 0 1 {name=l1636 lab=vss}
C {devices/lab_pin.sym} 320 -1470 0 1 {name=l1637 lab=t132}
C {devices/lab_pin.sym} 280 -1440 0 0 {name=l1638 lab=dhn0}
C {devices/lab_pin.sym} 320 -1410 0 1 {name=l1639 lab=m0_66}
C {devices/lab_pin.sym} 320 -1440 0 1 {name=l1640 lab=vss}
C {devices/lab_pin.sym} 370 -1470 0 1 {name=l1641 lab=t133}
C {devices/lab_pin.sym} 330 -1440 0 0 {name=l1642 lab=dh0}
C {devices/lab_pin.sym} 370 -1410 0 1 {name=l1643 lab=m0_66}
C {devices/lab_pin.sym} 370 -1440 0 1 {name=l1644 lab=vss}
C {devices/lab_pin.sym} 420 -1470 0 1 {name=l1645 lab=t134}
C {devices/lab_pin.sym} 380 -1440 0 0 {name=l1646 lab=dhn0}
C {devices/lab_pin.sym} 420 -1410 0 1 {name=l1647 lab=m0_67}
C {devices/lab_pin.sym} 420 -1440 0 1 {name=l1648 lab=vss}
C {devices/lab_pin.sym} 470 -1470 0 1 {name=l1649 lab=t135}
C {devices/lab_pin.sym} 430 -1440 0 0 {name=l1650 lab=dh0}
C {devices/lab_pin.sym} 470 -1410 0 1 {name=l1651 lab=m0_67}
C {devices/lab_pin.sym} 470 -1440 0 1 {name=l1652 lab=vss}
C {devices/lab_pin.sym} 520 -1470 0 1 {name=l1653 lab=t136}
C {devices/lab_pin.sym} 480 -1440 0 0 {name=l1654 lab=dhn0}
C {devices/lab_pin.sym} 520 -1410 0 1 {name=l1655 lab=m0_68}
C {devices/lab_pin.sym} 520 -1440 0 1 {name=l1656 lab=vss}
C {devices/lab_pin.sym} 570 -1470 0 1 {name=l1657 lab=t137}
C {devices/lab_pin.sym} 530 -1440 0 0 {name=l1658 lab=dh0}
C {devices/lab_pin.sym} 570 -1410 0 1 {name=l1659 lab=m0_68}
C {devices/lab_pin.sym} 570 -1440 0 1 {name=l1660 lab=vss}
C {devices/lab_pin.sym} 620 -1470 0 1 {name=l1661 lab=t138}
C {devices/lab_pin.sym} 580 -1440 0 0 {name=l1662 lab=dhn0}
C {devices/lab_pin.sym} 620 -1410 0 1 {name=l1663 lab=m0_69}
C {devices/lab_pin.sym} 620 -1440 0 1 {name=l1664 lab=vss}
C {devices/lab_pin.sym} 670 -1470 0 1 {name=l1665 lab=t139}
C {devices/lab_pin.sym} 630 -1440 0 0 {name=l1666 lab=dh0}
C {devices/lab_pin.sym} 670 -1410 0 1 {name=l1667 lab=m0_69}
C {devices/lab_pin.sym} 670 -1440 0 1 {name=l1668 lab=vss}
C {devices/lab_pin.sym} 720 -1470 0 1 {name=l1669 lab=t140}
C {devices/lab_pin.sym} 680 -1440 0 0 {name=l1670 lab=dhn0}
C {devices/lab_pin.sym} 720 -1410 0 1 {name=l1671 lab=m0_70}
C {devices/lab_pin.sym} 720 -1440 0 1 {name=l1672 lab=vss}
C {devices/lab_pin.sym} 770 -1470 0 1 {name=l1673 lab=t141}
C {devices/lab_pin.sym} 730 -1440 0 0 {name=l1674 lab=dh0}
C {devices/lab_pin.sym} 770 -1410 0 1 {name=l1675 lab=m0_70}
C {devices/lab_pin.sym} 770 -1440 0 1 {name=l1676 lab=vss}
C {devices/lab_pin.sym} 820 -1470 0 1 {name=l1677 lab=t142}
C {devices/lab_pin.sym} 780 -1440 0 0 {name=l1678 lab=dhn0}
C {devices/lab_pin.sym} 820 -1410 0 1 {name=l1679 lab=m0_71}
C {devices/lab_pin.sym} 820 -1440 0 1 {name=l1680 lab=vss}
C {devices/lab_pin.sym} 870 -1470 0 1 {name=l1681 lab=t143}
C {devices/lab_pin.sym} 830 -1440 0 0 {name=l1682 lab=dh0}
C {devices/lab_pin.sym} 870 -1410 0 1 {name=l1683 lab=m0_71}
C {devices/lab_pin.sym} 870 -1440 0 1 {name=l1684 lab=vss}
C {devices/lab_pin.sym} 920 -1470 0 1 {name=l1685 lab=t144}
C {devices/lab_pin.sym} 880 -1440 0 0 {name=l1686 lab=dhn0}
C {devices/lab_pin.sym} 920 -1410 0 1 {name=l1687 lab=m0_72}
C {devices/lab_pin.sym} 920 -1440 0 1 {name=l1688 lab=vss}
C {devices/lab_pin.sym} 970 -1470 0 1 {name=l1689 lab=t145}
C {devices/lab_pin.sym} 930 -1440 0 0 {name=l1690 lab=dh0}
C {devices/lab_pin.sym} 970 -1410 0 1 {name=l1691 lab=m0_72}
C {devices/lab_pin.sym} 970 -1440 0 1 {name=l1692 lab=vss}
C {devices/lab_pin.sym} 1020 -1470 0 1 {name=l1693 lab=t146}
C {devices/lab_pin.sym} 980 -1440 0 0 {name=l1694 lab=dhn0}
C {devices/lab_pin.sym} 1020 -1410 0 1 {name=l1695 lab=m0_73}
C {devices/lab_pin.sym} 1020 -1440 0 1 {name=l1696 lab=vss}
C {devices/lab_pin.sym} 1070 -1470 0 1 {name=l1697 lab=t147}
C {devices/lab_pin.sym} 1030 -1440 0 0 {name=l1698 lab=dh0}
C {devices/lab_pin.sym} 1070 -1410 0 1 {name=l1699 lab=m0_73}
C {devices/lab_pin.sym} 1070 -1440 0 1 {name=l1700 lab=vss}
C {devices/lab_pin.sym} 1120 -1470 0 1 {name=l1701 lab=t148}
C {devices/lab_pin.sym} 1080 -1440 0 0 {name=l1702 lab=dhn0}
C {devices/lab_pin.sym} 1120 -1410 0 1 {name=l1703 lab=m0_74}
C {devices/lab_pin.sym} 1120 -1440 0 1 {name=l1704 lab=vss}
C {devices/lab_pin.sym} 1170 -1470 0 1 {name=l1705 lab=t149}
C {devices/lab_pin.sym} 1130 -1440 0 0 {name=l1706 lab=dh0}
C {devices/lab_pin.sym} 1170 -1410 0 1 {name=l1707 lab=m0_74}
C {devices/lab_pin.sym} 1170 -1440 0 1 {name=l1708 lab=vss}
C {devices/lab_pin.sym} 1220 -1470 0 1 {name=l1709 lab=t150}
C {devices/lab_pin.sym} 1180 -1440 0 0 {name=l1710 lab=dhn0}
C {devices/lab_pin.sym} 1220 -1410 0 1 {name=l1711 lab=m0_75}
C {devices/lab_pin.sym} 1220 -1440 0 1 {name=l1712 lab=vss}
C {devices/lab_pin.sym} 1270 -1470 0 1 {name=l1713 lab=t151}
C {devices/lab_pin.sym} 1230 -1440 0 0 {name=l1714 lab=dh0}
C {devices/lab_pin.sym} 1270 -1410 0 1 {name=l1715 lab=m0_75}
C {devices/lab_pin.sym} 1270 -1440 0 1 {name=l1716 lab=vss}
C {devices/lab_pin.sym} 1320 -1470 0 1 {name=l1717 lab=t152}
C {devices/lab_pin.sym} 1280 -1440 0 0 {name=l1718 lab=dhn0}
C {devices/lab_pin.sym} 1320 -1410 0 1 {name=l1719 lab=m0_76}
C {devices/lab_pin.sym} 1320 -1440 0 1 {name=l1720 lab=vss}
C {devices/lab_pin.sym} 1370 -1470 0 1 {name=l1721 lab=t153}
C {devices/lab_pin.sym} 1330 -1440 0 0 {name=l1722 lab=dh0}
C {devices/lab_pin.sym} 1370 -1410 0 1 {name=l1723 lab=m0_76}
C {devices/lab_pin.sym} 1370 -1440 0 1 {name=l1724 lab=vss}
C {devices/lab_pin.sym} 1420 -1470 0 1 {name=l1725 lab=t154}
C {devices/lab_pin.sym} 1380 -1440 0 0 {name=l1726 lab=dhn0}
C {devices/lab_pin.sym} 1420 -1410 0 1 {name=l1727 lab=m0_77}
C {devices/lab_pin.sym} 1420 -1440 0 1 {name=l1728 lab=vss}
C {devices/lab_pin.sym} 1470 -1470 0 1 {name=l1729 lab=t155}
C {devices/lab_pin.sym} 1430 -1440 0 0 {name=l1730 lab=dh0}
C {devices/lab_pin.sym} 1470 -1410 0 1 {name=l1731 lab=m0_77}
C {devices/lab_pin.sym} 1470 -1440 0 1 {name=l1732 lab=vss}
C {devices/lab_pin.sym} 1520 -1470 0 1 {name=l1733 lab=t156}
C {devices/lab_pin.sym} 1480 -1440 0 0 {name=l1734 lab=dhn0}
C {devices/lab_pin.sym} 1520 -1410 0 1 {name=l1735 lab=m0_78}
C {devices/lab_pin.sym} 1520 -1440 0 1 {name=l1736 lab=vss}
C {devices/lab_pin.sym} 1570 -1470 0 1 {name=l1737 lab=t157}
C {devices/lab_pin.sym} 1530 -1440 0 0 {name=l1738 lab=dh0}
C {devices/lab_pin.sym} 1570 -1410 0 1 {name=l1739 lab=m0_78}
C {devices/lab_pin.sym} 1570 -1440 0 1 {name=l1740 lab=vss}
C {devices/lab_pin.sym} 1620 -1470 0 1 {name=l1741 lab=t158}
C {devices/lab_pin.sym} 1580 -1440 0 0 {name=l1742 lab=dhn0}
C {devices/lab_pin.sym} 1620 -1410 0 1 {name=l1743 lab=m0_79}
C {devices/lab_pin.sym} 1620 -1440 0 1 {name=l1744 lab=vss}
C {devices/lab_pin.sym} 1670 -1470 0 1 {name=l1745 lab=t159}
C {devices/lab_pin.sym} 1630 -1440 0 0 {name=l1746 lab=dh0}
C {devices/lab_pin.sym} 1670 -1410 0 1 {name=l1747 lab=m0_79}
C {devices/lab_pin.sym} 1670 -1440 0 1 {name=l1748 lab=vss}
C {devices/lab_pin.sym} 1720 -1470 0 1 {name=l1749 lab=t160}
C {devices/lab_pin.sym} 1680 -1440 0 0 {name=l1750 lab=dhn0}
C {devices/lab_pin.sym} 1720 -1410 0 1 {name=l1751 lab=m0_80}
C {devices/lab_pin.sym} 1720 -1440 0 1 {name=l1752 lab=vss}
C {devices/lab_pin.sym} 1770 -1470 0 1 {name=l1753 lab=t161}
C {devices/lab_pin.sym} 1730 -1440 0 0 {name=l1754 lab=dh0}
C {devices/lab_pin.sym} 1770 -1410 0 1 {name=l1755 lab=m0_80}
C {devices/lab_pin.sym} 1770 -1440 0 1 {name=l1756 lab=vss}
C {devices/lab_pin.sym} 1820 -1470 0 1 {name=l1757 lab=t162}
C {devices/lab_pin.sym} 1780 -1440 0 0 {name=l1758 lab=dhn0}
C {devices/lab_pin.sym} 1820 -1410 0 1 {name=l1759 lab=m0_81}
C {devices/lab_pin.sym} 1820 -1440 0 1 {name=l1760 lab=vss}
C {devices/lab_pin.sym} 1870 -1470 0 1 {name=l1761 lab=t163}
C {devices/lab_pin.sym} 1830 -1440 0 0 {name=l1762 lab=dh0}
C {devices/lab_pin.sym} 1870 -1410 0 1 {name=l1763 lab=m0_81}
C {devices/lab_pin.sym} 1870 -1440 0 1 {name=l1764 lab=vss}
C {devices/lab_pin.sym} 1920 -1470 0 1 {name=l1765 lab=t164}
C {devices/lab_pin.sym} 1880 -1440 0 0 {name=l1766 lab=dhn0}
C {devices/lab_pin.sym} 1920 -1410 0 1 {name=l1767 lab=m0_82}
C {devices/lab_pin.sym} 1920 -1440 0 1 {name=l1768 lab=vss}
C {devices/lab_pin.sym} 1970 -1470 0 1 {name=l1769 lab=t165}
C {devices/lab_pin.sym} 1930 -1440 0 0 {name=l1770 lab=dh0}
C {devices/lab_pin.sym} 1970 -1410 0 1 {name=l1771 lab=m0_82}
C {devices/lab_pin.sym} 1970 -1440 0 1 {name=l1772 lab=vss}
C {devices/lab_pin.sym} 2020 -1470 0 1 {name=l1773 lab=t166}
C {devices/lab_pin.sym} 1980 -1440 0 0 {name=l1774 lab=dhn0}
C {devices/lab_pin.sym} 2020 -1410 0 1 {name=l1775 lab=m0_83}
C {devices/lab_pin.sym} 2020 -1440 0 1 {name=l1776 lab=vss}
C {devices/lab_pin.sym} 2070 -1470 0 1 {name=l1777 lab=t167}
C {devices/lab_pin.sym} 2030 -1440 0 0 {name=l1778 lab=dh0}
C {devices/lab_pin.sym} 2070 -1410 0 1 {name=l1779 lab=m0_83}
C {devices/lab_pin.sym} 2070 -1440 0 1 {name=l1780 lab=vss}
C {devices/lab_pin.sym} 2120 -1470 0 1 {name=l1781 lab=t168}
C {devices/lab_pin.sym} 2080 -1440 0 0 {name=l1782 lab=dhn0}
C {devices/lab_pin.sym} 2120 -1410 0 1 {name=l1783 lab=m0_84}
C {devices/lab_pin.sym} 2120 -1440 0 1 {name=l1784 lab=vss}
C {devices/lab_pin.sym} 2170 -1470 0 1 {name=l1785 lab=t169}
C {devices/lab_pin.sym} 2130 -1440 0 0 {name=l1786 lab=dh0}
C {devices/lab_pin.sym} 2170 -1410 0 1 {name=l1787 lab=m0_84}
C {devices/lab_pin.sym} 2170 -1440 0 1 {name=l1788 lab=vss}
C {devices/lab_pin.sym} 2220 -1470 0 1 {name=l1789 lab=t170}
C {devices/lab_pin.sym} 2180 -1440 0 0 {name=l1790 lab=dhn0}
C {devices/lab_pin.sym} 2220 -1410 0 1 {name=l1791 lab=m0_85}
C {devices/lab_pin.sym} 2220 -1440 0 1 {name=l1792 lab=vss}
C {devices/lab_pin.sym} 2270 -1470 0 1 {name=l1793 lab=t171}
C {devices/lab_pin.sym} 2230 -1440 0 0 {name=l1794 lab=dh0}
C {devices/lab_pin.sym} 2270 -1410 0 1 {name=l1795 lab=m0_85}
C {devices/lab_pin.sym} 2270 -1440 0 1 {name=l1796 lab=vss}
C {devices/lab_pin.sym} 2320 -1470 0 1 {name=l1797 lab=t172}
C {devices/lab_pin.sym} 2280 -1440 0 0 {name=l1798 lab=dhn0}
C {devices/lab_pin.sym} 2320 -1410 0 1 {name=l1799 lab=m0_86}
C {devices/lab_pin.sym} 2320 -1440 0 1 {name=l1800 lab=vss}
C {devices/lab_pin.sym} 2370 -1470 0 1 {name=l1801 lab=t173}
C {devices/lab_pin.sym} 2330 -1440 0 0 {name=l1802 lab=dh0}
C {devices/lab_pin.sym} 2370 -1410 0 1 {name=l1803 lab=m0_86}
C {devices/lab_pin.sym} 2370 -1440 0 1 {name=l1804 lab=vss}
C {devices/lab_pin.sym} 2420 -1470 0 1 {name=l1805 lab=t174}
C {devices/lab_pin.sym} 2380 -1440 0 0 {name=l1806 lab=dhn0}
C {devices/lab_pin.sym} 2420 -1410 0 1 {name=l1807 lab=m0_87}
C {devices/lab_pin.sym} 2420 -1440 0 1 {name=l1808 lab=vss}
C {devices/lab_pin.sym} 2470 -1470 0 1 {name=l1809 lab=t175}
C {devices/lab_pin.sym} 2430 -1440 0 0 {name=l1810 lab=dh0}
C {devices/lab_pin.sym} 2470 -1410 0 1 {name=l1811 lab=m0_87}
C {devices/lab_pin.sym} 2470 -1440 0 1 {name=l1812 lab=vss}
C {devices/lab_pin.sym} 2520 -1470 0 1 {name=l1813 lab=t176}
C {devices/lab_pin.sym} 2480 -1440 0 0 {name=l1814 lab=dhn0}
C {devices/lab_pin.sym} 2520 -1410 0 1 {name=l1815 lab=m0_88}
C {devices/lab_pin.sym} 2520 -1440 0 1 {name=l1816 lab=vss}
C {devices/lab_pin.sym} 2570 -1470 0 1 {name=l1817 lab=t177}
C {devices/lab_pin.sym} 2530 -1440 0 0 {name=l1818 lab=dh0}
C {devices/lab_pin.sym} 2570 -1410 0 1 {name=l1819 lab=m0_88}
C {devices/lab_pin.sym} 2570 -1440 0 1 {name=l1820 lab=vss}
C {devices/lab_pin.sym} 2620 -1470 0 1 {name=l1821 lab=t178}
C {devices/lab_pin.sym} 2580 -1440 0 0 {name=l1822 lab=dhn0}
C {devices/lab_pin.sym} 2620 -1410 0 1 {name=l1823 lab=m0_89}
C {devices/lab_pin.sym} 2620 -1440 0 1 {name=l1824 lab=vss}
C {devices/lab_pin.sym} 2670 -1470 0 1 {name=l1825 lab=t179}
C {devices/lab_pin.sym} 2630 -1440 0 0 {name=l1826 lab=dh0}
C {devices/lab_pin.sym} 2670 -1410 0 1 {name=l1827 lab=m0_89}
C {devices/lab_pin.sym} 2670 -1440 0 1 {name=l1828 lab=vss}
C {devices/lab_pin.sym} 2720 -1470 0 1 {name=l1829 lab=t180}
C {devices/lab_pin.sym} 2680 -1440 0 0 {name=l1830 lab=dhn0}
C {devices/lab_pin.sym} 2720 -1410 0 1 {name=l1831 lab=m0_90}
C {devices/lab_pin.sym} 2720 -1440 0 1 {name=l1832 lab=vss}
C {devices/lab_pin.sym} 2770 -1470 0 1 {name=l1833 lab=t181}
C {devices/lab_pin.sym} 2730 -1440 0 0 {name=l1834 lab=dh0}
C {devices/lab_pin.sym} 2770 -1410 0 1 {name=l1835 lab=m0_90}
C {devices/lab_pin.sym} 2770 -1440 0 1 {name=l1836 lab=vss}
C {devices/lab_pin.sym} 2820 -1470 0 1 {name=l1837 lab=t182}
C {devices/lab_pin.sym} 2780 -1440 0 0 {name=l1838 lab=dhn0}
C {devices/lab_pin.sym} 2820 -1410 0 1 {name=l1839 lab=m0_91}
C {devices/lab_pin.sym} 2820 -1440 0 1 {name=l1840 lab=vss}
C {devices/lab_pin.sym} 2870 -1470 0 1 {name=l1841 lab=t183}
C {devices/lab_pin.sym} 2830 -1440 0 0 {name=l1842 lab=dh0}
C {devices/lab_pin.sym} 2870 -1410 0 1 {name=l1843 lab=m0_91}
C {devices/lab_pin.sym} 2870 -1440 0 1 {name=l1844 lab=vss}
C {devices/lab_pin.sym} 2920 -1470 0 1 {name=l1845 lab=t184}
C {devices/lab_pin.sym} 2880 -1440 0 0 {name=l1846 lab=dhn0}
C {devices/lab_pin.sym} 2920 -1410 0 1 {name=l1847 lab=m0_92}
C {devices/lab_pin.sym} 2920 -1440 0 1 {name=l1848 lab=vss}
C {devices/lab_pin.sym} 2970 -1470 0 1 {name=l1849 lab=t185}
C {devices/lab_pin.sym} 2930 -1440 0 0 {name=l1850 lab=dh0}
C {devices/lab_pin.sym} 2970 -1410 0 1 {name=l1851 lab=m0_92}
C {devices/lab_pin.sym} 2970 -1440 0 1 {name=l1852 lab=vss}
C {devices/lab_pin.sym} 3020 -1470 0 1 {name=l1853 lab=t186}
C {devices/lab_pin.sym} 2980 -1440 0 0 {name=l1854 lab=dhn0}
C {devices/lab_pin.sym} 3020 -1410 0 1 {name=l1855 lab=m0_93}
C {devices/lab_pin.sym} 3020 -1440 0 1 {name=l1856 lab=vss}
C {devices/lab_pin.sym} 3070 -1470 0 1 {name=l1857 lab=t187}
C {devices/lab_pin.sym} 3030 -1440 0 0 {name=l1858 lab=dh0}
C {devices/lab_pin.sym} 3070 -1410 0 1 {name=l1859 lab=m0_93}
C {devices/lab_pin.sym} 3070 -1440 0 1 {name=l1860 lab=vss}
C {devices/lab_pin.sym} 3120 -1470 0 1 {name=l1861 lab=t188}
C {devices/lab_pin.sym} 3080 -1440 0 0 {name=l1862 lab=dhn0}
C {devices/lab_pin.sym} 3120 -1410 0 1 {name=l1863 lab=m0_94}
C {devices/lab_pin.sym} 3120 -1440 0 1 {name=l1864 lab=vss}
C {devices/lab_pin.sym} 3170 -1470 0 1 {name=l1865 lab=t189}
C {devices/lab_pin.sym} 3130 -1440 0 0 {name=l1866 lab=dh0}
C {devices/lab_pin.sym} 3170 -1410 0 1 {name=l1867 lab=m0_94}
C {devices/lab_pin.sym} 3170 -1440 0 1 {name=l1868 lab=vss}
C {devices/lab_pin.sym} 3220 -1470 0 1 {name=l1869 lab=t190}
C {devices/lab_pin.sym} 3180 -1440 0 0 {name=l1870 lab=dhn0}
C {devices/lab_pin.sym} 3220 -1410 0 1 {name=l1871 lab=m0_95}
C {devices/lab_pin.sym} 3220 -1440 0 1 {name=l1872 lab=vss}
C {devices/lab_pin.sym} 3270 -1470 0 1 {name=l1873 lab=t191}
C {devices/lab_pin.sym} 3230 -1440 0 0 {name=l1874 lab=dh0}
C {devices/lab_pin.sym} 3270 -1410 0 1 {name=l1875 lab=m0_95}
C {devices/lab_pin.sym} 3270 -1440 0 1 {name=l1876 lab=vss}
C {devices/lab_pin.sym} 120 -1390 0 1 {name=l1877 lab=t192}
C {devices/lab_pin.sym} 80 -1360 0 0 {name=l1878 lab=dhn0}
C {devices/lab_pin.sym} 120 -1330 0 1 {name=l1879 lab=m0_96}
C {devices/lab_pin.sym} 120 -1360 0 1 {name=l1880 lab=vss}
C {devices/lab_pin.sym} 170 -1390 0 1 {name=l1881 lab=t193}
C {devices/lab_pin.sym} 130 -1360 0 0 {name=l1882 lab=dh0}
C {devices/lab_pin.sym} 170 -1330 0 1 {name=l1883 lab=m0_96}
C {devices/lab_pin.sym} 170 -1360 0 1 {name=l1884 lab=vss}
C {devices/lab_pin.sym} 220 -1390 0 1 {name=l1885 lab=t194}
C {devices/lab_pin.sym} 180 -1360 0 0 {name=l1886 lab=dhn0}
C {devices/lab_pin.sym} 220 -1330 0 1 {name=l1887 lab=m0_97}
C {devices/lab_pin.sym} 220 -1360 0 1 {name=l1888 lab=vss}
C {devices/lab_pin.sym} 270 -1390 0 1 {name=l1889 lab=t195}
C {devices/lab_pin.sym} 230 -1360 0 0 {name=l1890 lab=dh0}
C {devices/lab_pin.sym} 270 -1330 0 1 {name=l1891 lab=m0_97}
C {devices/lab_pin.sym} 270 -1360 0 1 {name=l1892 lab=vss}
C {devices/lab_pin.sym} 320 -1390 0 1 {name=l1893 lab=t196}
C {devices/lab_pin.sym} 280 -1360 0 0 {name=l1894 lab=dhn0}
C {devices/lab_pin.sym} 320 -1330 0 1 {name=l1895 lab=m0_98}
C {devices/lab_pin.sym} 320 -1360 0 1 {name=l1896 lab=vss}
C {devices/lab_pin.sym} 370 -1390 0 1 {name=l1897 lab=t197}
C {devices/lab_pin.sym} 330 -1360 0 0 {name=l1898 lab=dh0}
C {devices/lab_pin.sym} 370 -1330 0 1 {name=l1899 lab=m0_98}
C {devices/lab_pin.sym} 370 -1360 0 1 {name=l1900 lab=vss}
C {devices/lab_pin.sym} 420 -1390 0 1 {name=l1901 lab=t198}
C {devices/lab_pin.sym} 380 -1360 0 0 {name=l1902 lab=dhn0}
C {devices/lab_pin.sym} 420 -1330 0 1 {name=l1903 lab=m0_99}
C {devices/lab_pin.sym} 420 -1360 0 1 {name=l1904 lab=vss}
C {devices/lab_pin.sym} 470 -1390 0 1 {name=l1905 lab=t199}
C {devices/lab_pin.sym} 430 -1360 0 0 {name=l1906 lab=dh0}
C {devices/lab_pin.sym} 470 -1330 0 1 {name=l1907 lab=m0_99}
C {devices/lab_pin.sym} 470 -1360 0 1 {name=l1908 lab=vss}
C {devices/lab_pin.sym} 520 -1390 0 1 {name=l1909 lab=t200}
C {devices/lab_pin.sym} 480 -1360 0 0 {name=l1910 lab=dhn0}
C {devices/lab_pin.sym} 520 -1330 0 1 {name=l1911 lab=m0_100}
C {devices/lab_pin.sym} 520 -1360 0 1 {name=l1912 lab=vss}
C {devices/lab_pin.sym} 570 -1390 0 1 {name=l1913 lab=t201}
C {devices/lab_pin.sym} 530 -1360 0 0 {name=l1914 lab=dh0}
C {devices/lab_pin.sym} 570 -1330 0 1 {name=l1915 lab=m0_100}
C {devices/lab_pin.sym} 570 -1360 0 1 {name=l1916 lab=vss}
C {devices/lab_pin.sym} 620 -1390 0 1 {name=l1917 lab=t202}
C {devices/lab_pin.sym} 580 -1360 0 0 {name=l1918 lab=dhn0}
C {devices/lab_pin.sym} 620 -1330 0 1 {name=l1919 lab=m0_101}
C {devices/lab_pin.sym} 620 -1360 0 1 {name=l1920 lab=vss}
C {devices/lab_pin.sym} 670 -1390 0 1 {name=l1921 lab=t203}
C {devices/lab_pin.sym} 630 -1360 0 0 {name=l1922 lab=dh0}
C {devices/lab_pin.sym} 670 -1330 0 1 {name=l1923 lab=m0_101}
C {devices/lab_pin.sym} 670 -1360 0 1 {name=l1924 lab=vss}
C {devices/lab_pin.sym} 720 -1390 0 1 {name=l1925 lab=t204}
C {devices/lab_pin.sym} 680 -1360 0 0 {name=l1926 lab=dhn0}
C {devices/lab_pin.sym} 720 -1330 0 1 {name=l1927 lab=m0_102}
C {devices/lab_pin.sym} 720 -1360 0 1 {name=l1928 lab=vss}
C {devices/lab_pin.sym} 770 -1390 0 1 {name=l1929 lab=t205}
C {devices/lab_pin.sym} 730 -1360 0 0 {name=l1930 lab=dh0}
C {devices/lab_pin.sym} 770 -1330 0 1 {name=l1931 lab=m0_102}
C {devices/lab_pin.sym} 770 -1360 0 1 {name=l1932 lab=vss}
C {devices/lab_pin.sym} 820 -1390 0 1 {name=l1933 lab=t206}
C {devices/lab_pin.sym} 780 -1360 0 0 {name=l1934 lab=dhn0}
C {devices/lab_pin.sym} 820 -1330 0 1 {name=l1935 lab=m0_103}
C {devices/lab_pin.sym} 820 -1360 0 1 {name=l1936 lab=vss}
C {devices/lab_pin.sym} 870 -1390 0 1 {name=l1937 lab=t207}
C {devices/lab_pin.sym} 830 -1360 0 0 {name=l1938 lab=dh0}
C {devices/lab_pin.sym} 870 -1330 0 1 {name=l1939 lab=m0_103}
C {devices/lab_pin.sym} 870 -1360 0 1 {name=l1940 lab=vss}
C {devices/lab_pin.sym} 920 -1390 0 1 {name=l1941 lab=t208}
C {devices/lab_pin.sym} 880 -1360 0 0 {name=l1942 lab=dhn0}
C {devices/lab_pin.sym} 920 -1330 0 1 {name=l1943 lab=m0_104}
C {devices/lab_pin.sym} 920 -1360 0 1 {name=l1944 lab=vss}
C {devices/lab_pin.sym} 970 -1390 0 1 {name=l1945 lab=t209}
C {devices/lab_pin.sym} 930 -1360 0 0 {name=l1946 lab=dh0}
C {devices/lab_pin.sym} 970 -1330 0 1 {name=l1947 lab=m0_104}
C {devices/lab_pin.sym} 970 -1360 0 1 {name=l1948 lab=vss}
C {devices/lab_pin.sym} 1020 -1390 0 1 {name=l1949 lab=t210}
C {devices/lab_pin.sym} 980 -1360 0 0 {name=l1950 lab=dhn0}
C {devices/lab_pin.sym} 1020 -1330 0 1 {name=l1951 lab=m0_105}
C {devices/lab_pin.sym} 1020 -1360 0 1 {name=l1952 lab=vss}
C {devices/lab_pin.sym} 1070 -1390 0 1 {name=l1953 lab=t211}
C {devices/lab_pin.sym} 1030 -1360 0 0 {name=l1954 lab=dh0}
C {devices/lab_pin.sym} 1070 -1330 0 1 {name=l1955 lab=m0_105}
C {devices/lab_pin.sym} 1070 -1360 0 1 {name=l1956 lab=vss}
C {devices/lab_pin.sym} 1120 -1390 0 1 {name=l1957 lab=t212}
C {devices/lab_pin.sym} 1080 -1360 0 0 {name=l1958 lab=dhn0}
C {devices/lab_pin.sym} 1120 -1330 0 1 {name=l1959 lab=m0_106}
C {devices/lab_pin.sym} 1120 -1360 0 1 {name=l1960 lab=vss}
C {devices/lab_pin.sym} 1170 -1390 0 1 {name=l1961 lab=t213}
C {devices/lab_pin.sym} 1130 -1360 0 0 {name=l1962 lab=dh0}
C {devices/lab_pin.sym} 1170 -1330 0 1 {name=l1963 lab=m0_106}
C {devices/lab_pin.sym} 1170 -1360 0 1 {name=l1964 lab=vss}
C {devices/lab_pin.sym} 1220 -1390 0 1 {name=l1965 lab=t214}
C {devices/lab_pin.sym} 1180 -1360 0 0 {name=l1966 lab=dhn0}
C {devices/lab_pin.sym} 1220 -1330 0 1 {name=l1967 lab=m0_107}
C {devices/lab_pin.sym} 1220 -1360 0 1 {name=l1968 lab=vss}
C {devices/lab_pin.sym} 1270 -1390 0 1 {name=l1969 lab=t215}
C {devices/lab_pin.sym} 1230 -1360 0 0 {name=l1970 lab=dh0}
C {devices/lab_pin.sym} 1270 -1330 0 1 {name=l1971 lab=m0_107}
C {devices/lab_pin.sym} 1270 -1360 0 1 {name=l1972 lab=vss}
C {devices/lab_pin.sym} 1320 -1390 0 1 {name=l1973 lab=t216}
C {devices/lab_pin.sym} 1280 -1360 0 0 {name=l1974 lab=dhn0}
C {devices/lab_pin.sym} 1320 -1330 0 1 {name=l1975 lab=m0_108}
C {devices/lab_pin.sym} 1320 -1360 0 1 {name=l1976 lab=vss}
C {devices/lab_pin.sym} 1370 -1390 0 1 {name=l1977 lab=t217}
C {devices/lab_pin.sym} 1330 -1360 0 0 {name=l1978 lab=dh0}
C {devices/lab_pin.sym} 1370 -1330 0 1 {name=l1979 lab=m0_108}
C {devices/lab_pin.sym} 1370 -1360 0 1 {name=l1980 lab=vss}
C {devices/lab_pin.sym} 1420 -1390 0 1 {name=l1981 lab=t218}
C {devices/lab_pin.sym} 1380 -1360 0 0 {name=l1982 lab=dhn0}
C {devices/lab_pin.sym} 1420 -1330 0 1 {name=l1983 lab=m0_109}
C {devices/lab_pin.sym} 1420 -1360 0 1 {name=l1984 lab=vss}
C {devices/lab_pin.sym} 1470 -1390 0 1 {name=l1985 lab=t219}
C {devices/lab_pin.sym} 1430 -1360 0 0 {name=l1986 lab=dh0}
C {devices/lab_pin.sym} 1470 -1330 0 1 {name=l1987 lab=m0_109}
C {devices/lab_pin.sym} 1470 -1360 0 1 {name=l1988 lab=vss}
C {devices/lab_pin.sym} 1520 -1390 0 1 {name=l1989 lab=t220}
C {devices/lab_pin.sym} 1480 -1360 0 0 {name=l1990 lab=dhn0}
C {devices/lab_pin.sym} 1520 -1330 0 1 {name=l1991 lab=m0_110}
C {devices/lab_pin.sym} 1520 -1360 0 1 {name=l1992 lab=vss}
C {devices/lab_pin.sym} 1570 -1390 0 1 {name=l1993 lab=t221}
C {devices/lab_pin.sym} 1530 -1360 0 0 {name=l1994 lab=dh0}
C {devices/lab_pin.sym} 1570 -1330 0 1 {name=l1995 lab=m0_110}
C {devices/lab_pin.sym} 1570 -1360 0 1 {name=l1996 lab=vss}
C {devices/lab_pin.sym} 1620 -1390 0 1 {name=l1997 lab=t222}
C {devices/lab_pin.sym} 1580 -1360 0 0 {name=l1998 lab=dhn0}
C {devices/lab_pin.sym} 1620 -1330 0 1 {name=l1999 lab=m0_111}
C {devices/lab_pin.sym} 1620 -1360 0 1 {name=l2000 lab=vss}
C {devices/lab_pin.sym} 1670 -1390 0 1 {name=l2001 lab=t223}
C {devices/lab_pin.sym} 1630 -1360 0 0 {name=l2002 lab=dh0}
C {devices/lab_pin.sym} 1670 -1330 0 1 {name=l2003 lab=m0_111}
C {devices/lab_pin.sym} 1670 -1360 0 1 {name=l2004 lab=vss}
C {devices/lab_pin.sym} 1720 -1390 0 1 {name=l2005 lab=t224}
C {devices/lab_pin.sym} 1680 -1360 0 0 {name=l2006 lab=dhn0}
C {devices/lab_pin.sym} 1720 -1330 0 1 {name=l2007 lab=m0_112}
C {devices/lab_pin.sym} 1720 -1360 0 1 {name=l2008 lab=vss}
C {devices/lab_pin.sym} 1770 -1390 0 1 {name=l2009 lab=t225}
C {devices/lab_pin.sym} 1730 -1360 0 0 {name=l2010 lab=dh0}
C {devices/lab_pin.sym} 1770 -1330 0 1 {name=l2011 lab=m0_112}
C {devices/lab_pin.sym} 1770 -1360 0 1 {name=l2012 lab=vss}
C {devices/lab_pin.sym} 1820 -1390 0 1 {name=l2013 lab=t226}
C {devices/lab_pin.sym} 1780 -1360 0 0 {name=l2014 lab=dhn0}
C {devices/lab_pin.sym} 1820 -1330 0 1 {name=l2015 lab=m0_113}
C {devices/lab_pin.sym} 1820 -1360 0 1 {name=l2016 lab=vss}
C {devices/lab_pin.sym} 1870 -1390 0 1 {name=l2017 lab=t227}
C {devices/lab_pin.sym} 1830 -1360 0 0 {name=l2018 lab=dh0}
C {devices/lab_pin.sym} 1870 -1330 0 1 {name=l2019 lab=m0_113}
C {devices/lab_pin.sym} 1870 -1360 0 1 {name=l2020 lab=vss}
C {devices/lab_pin.sym} 1920 -1390 0 1 {name=l2021 lab=t228}
C {devices/lab_pin.sym} 1880 -1360 0 0 {name=l2022 lab=dhn0}
C {devices/lab_pin.sym} 1920 -1330 0 1 {name=l2023 lab=m0_114}
C {devices/lab_pin.sym} 1920 -1360 0 1 {name=l2024 lab=vss}
C {devices/lab_pin.sym} 1970 -1390 0 1 {name=l2025 lab=t229}
C {devices/lab_pin.sym} 1930 -1360 0 0 {name=l2026 lab=dh0}
C {devices/lab_pin.sym} 1970 -1330 0 1 {name=l2027 lab=m0_114}
C {devices/lab_pin.sym} 1970 -1360 0 1 {name=l2028 lab=vss}
C {devices/lab_pin.sym} 2020 -1390 0 1 {name=l2029 lab=t230}
C {devices/lab_pin.sym} 1980 -1360 0 0 {name=l2030 lab=dhn0}
C {devices/lab_pin.sym} 2020 -1330 0 1 {name=l2031 lab=m0_115}
C {devices/lab_pin.sym} 2020 -1360 0 1 {name=l2032 lab=vss}
C {devices/lab_pin.sym} 2070 -1390 0 1 {name=l2033 lab=t231}
C {devices/lab_pin.sym} 2030 -1360 0 0 {name=l2034 lab=dh0}
C {devices/lab_pin.sym} 2070 -1330 0 1 {name=l2035 lab=m0_115}
C {devices/lab_pin.sym} 2070 -1360 0 1 {name=l2036 lab=vss}
C {devices/lab_pin.sym} 2120 -1390 0 1 {name=l2037 lab=t232}
C {devices/lab_pin.sym} 2080 -1360 0 0 {name=l2038 lab=dhn0}
C {devices/lab_pin.sym} 2120 -1330 0 1 {name=l2039 lab=m0_116}
C {devices/lab_pin.sym} 2120 -1360 0 1 {name=l2040 lab=vss}
C {devices/lab_pin.sym} 2170 -1390 0 1 {name=l2041 lab=t233}
C {devices/lab_pin.sym} 2130 -1360 0 0 {name=l2042 lab=dh0}
C {devices/lab_pin.sym} 2170 -1330 0 1 {name=l2043 lab=m0_116}
C {devices/lab_pin.sym} 2170 -1360 0 1 {name=l2044 lab=vss}
C {devices/lab_pin.sym} 2220 -1390 0 1 {name=l2045 lab=t234}
C {devices/lab_pin.sym} 2180 -1360 0 0 {name=l2046 lab=dhn0}
C {devices/lab_pin.sym} 2220 -1330 0 1 {name=l2047 lab=m0_117}
C {devices/lab_pin.sym} 2220 -1360 0 1 {name=l2048 lab=vss}
C {devices/lab_pin.sym} 2270 -1390 0 1 {name=l2049 lab=t235}
C {devices/lab_pin.sym} 2230 -1360 0 0 {name=l2050 lab=dh0}
C {devices/lab_pin.sym} 2270 -1330 0 1 {name=l2051 lab=m0_117}
C {devices/lab_pin.sym} 2270 -1360 0 1 {name=l2052 lab=vss}
C {devices/lab_pin.sym} 2320 -1390 0 1 {name=l2053 lab=t236}
C {devices/lab_pin.sym} 2280 -1360 0 0 {name=l2054 lab=dhn0}
C {devices/lab_pin.sym} 2320 -1330 0 1 {name=l2055 lab=m0_118}
C {devices/lab_pin.sym} 2320 -1360 0 1 {name=l2056 lab=vss}
C {devices/lab_pin.sym} 2370 -1390 0 1 {name=l2057 lab=t237}
C {devices/lab_pin.sym} 2330 -1360 0 0 {name=l2058 lab=dh0}
C {devices/lab_pin.sym} 2370 -1330 0 1 {name=l2059 lab=m0_118}
C {devices/lab_pin.sym} 2370 -1360 0 1 {name=l2060 lab=vss}
C {devices/lab_pin.sym} 2420 -1390 0 1 {name=l2061 lab=t238}
C {devices/lab_pin.sym} 2380 -1360 0 0 {name=l2062 lab=dhn0}
C {devices/lab_pin.sym} 2420 -1330 0 1 {name=l2063 lab=m0_119}
C {devices/lab_pin.sym} 2420 -1360 0 1 {name=l2064 lab=vss}
C {devices/lab_pin.sym} 2470 -1390 0 1 {name=l2065 lab=t239}
C {devices/lab_pin.sym} 2430 -1360 0 0 {name=l2066 lab=dh0}
C {devices/lab_pin.sym} 2470 -1330 0 1 {name=l2067 lab=m0_119}
C {devices/lab_pin.sym} 2470 -1360 0 1 {name=l2068 lab=vss}
C {devices/lab_pin.sym} 2520 -1390 0 1 {name=l2069 lab=t240}
C {devices/lab_pin.sym} 2480 -1360 0 0 {name=l2070 lab=dhn0}
C {devices/lab_pin.sym} 2520 -1330 0 1 {name=l2071 lab=m0_120}
C {devices/lab_pin.sym} 2520 -1360 0 1 {name=l2072 lab=vss}
C {devices/lab_pin.sym} 2570 -1390 0 1 {name=l2073 lab=t241}
C {devices/lab_pin.sym} 2530 -1360 0 0 {name=l2074 lab=dh0}
C {devices/lab_pin.sym} 2570 -1330 0 1 {name=l2075 lab=m0_120}
C {devices/lab_pin.sym} 2570 -1360 0 1 {name=l2076 lab=vss}
C {devices/lab_pin.sym} 2620 -1390 0 1 {name=l2077 lab=t242}
C {devices/lab_pin.sym} 2580 -1360 0 0 {name=l2078 lab=dhn0}
C {devices/lab_pin.sym} 2620 -1330 0 1 {name=l2079 lab=m0_121}
C {devices/lab_pin.sym} 2620 -1360 0 1 {name=l2080 lab=vss}
C {devices/lab_pin.sym} 2670 -1390 0 1 {name=l2081 lab=t243}
C {devices/lab_pin.sym} 2630 -1360 0 0 {name=l2082 lab=dh0}
C {devices/lab_pin.sym} 2670 -1330 0 1 {name=l2083 lab=m0_121}
C {devices/lab_pin.sym} 2670 -1360 0 1 {name=l2084 lab=vss}
C {devices/lab_pin.sym} 2720 -1390 0 1 {name=l2085 lab=t244}
C {devices/lab_pin.sym} 2680 -1360 0 0 {name=l2086 lab=dhn0}
C {devices/lab_pin.sym} 2720 -1330 0 1 {name=l2087 lab=m0_122}
C {devices/lab_pin.sym} 2720 -1360 0 1 {name=l2088 lab=vss}
C {devices/lab_pin.sym} 2770 -1390 0 1 {name=l2089 lab=t245}
C {devices/lab_pin.sym} 2730 -1360 0 0 {name=l2090 lab=dh0}
C {devices/lab_pin.sym} 2770 -1330 0 1 {name=l2091 lab=m0_122}
C {devices/lab_pin.sym} 2770 -1360 0 1 {name=l2092 lab=vss}
C {devices/lab_pin.sym} 2820 -1390 0 1 {name=l2093 lab=t246}
C {devices/lab_pin.sym} 2780 -1360 0 0 {name=l2094 lab=dhn0}
C {devices/lab_pin.sym} 2820 -1330 0 1 {name=l2095 lab=m0_123}
C {devices/lab_pin.sym} 2820 -1360 0 1 {name=l2096 lab=vss}
C {devices/lab_pin.sym} 2870 -1390 0 1 {name=l2097 lab=t247}
C {devices/lab_pin.sym} 2830 -1360 0 0 {name=l2098 lab=dh0}
C {devices/lab_pin.sym} 2870 -1330 0 1 {name=l2099 lab=m0_123}
C {devices/lab_pin.sym} 2870 -1360 0 1 {name=l2100 lab=vss}
C {devices/lab_pin.sym} 2920 -1390 0 1 {name=l2101 lab=t248}
C {devices/lab_pin.sym} 2880 -1360 0 0 {name=l2102 lab=dhn0}
C {devices/lab_pin.sym} 2920 -1330 0 1 {name=l2103 lab=m0_124}
C {devices/lab_pin.sym} 2920 -1360 0 1 {name=l2104 lab=vss}
C {devices/lab_pin.sym} 2970 -1390 0 1 {name=l2105 lab=t249}
C {devices/lab_pin.sym} 2930 -1360 0 0 {name=l2106 lab=dh0}
C {devices/lab_pin.sym} 2970 -1330 0 1 {name=l2107 lab=m0_124}
C {devices/lab_pin.sym} 2970 -1360 0 1 {name=l2108 lab=vss}
C {devices/lab_pin.sym} 3020 -1390 0 1 {name=l2109 lab=t250}
C {devices/lab_pin.sym} 2980 -1360 0 0 {name=l2110 lab=dhn0}
C {devices/lab_pin.sym} 3020 -1330 0 1 {name=l2111 lab=m0_125}
C {devices/lab_pin.sym} 3020 -1360 0 1 {name=l2112 lab=vss}
C {devices/lab_pin.sym} 3070 -1390 0 1 {name=l2113 lab=t251}
C {devices/lab_pin.sym} 3030 -1360 0 0 {name=l2114 lab=dh0}
C {devices/lab_pin.sym} 3070 -1330 0 1 {name=l2115 lab=m0_125}
C {devices/lab_pin.sym} 3070 -1360 0 1 {name=l2116 lab=vss}
C {devices/lab_pin.sym} 3120 -1390 0 1 {name=l2117 lab=t252}
C {devices/lab_pin.sym} 3080 -1360 0 0 {name=l2118 lab=dhn0}
C {devices/lab_pin.sym} 3120 -1330 0 1 {name=l2119 lab=m0_126}
C {devices/lab_pin.sym} 3120 -1360 0 1 {name=l2120 lab=vss}
C {devices/lab_pin.sym} 3170 -1390 0 1 {name=l2121 lab=t253}
C {devices/lab_pin.sym} 3130 -1360 0 0 {name=l2122 lab=dh0}
C {devices/lab_pin.sym} 3170 -1330 0 1 {name=l2123 lab=m0_126}
C {devices/lab_pin.sym} 3170 -1360 0 1 {name=l2124 lab=vss}
C {devices/lab_pin.sym} 3220 -1390 0 1 {name=l2125 lab=t254}
C {devices/lab_pin.sym} 3180 -1360 0 0 {name=l2126 lab=dhn0}
C {devices/lab_pin.sym} 3220 -1330 0 1 {name=l2127 lab=m0_127}
C {devices/lab_pin.sym} 3220 -1360 0 1 {name=l2128 lab=vss}
C {devices/lab_pin.sym} 3270 -1390 0 1 {name=l2129 lab=t255}
C {devices/lab_pin.sym} 3230 -1360 0 0 {name=l2130 lab=dh0}
C {devices/lab_pin.sym} 3270 -1330 0 1 {name=l2131 lab=m0_127}
C {devices/lab_pin.sym} 3270 -1360 0 1 {name=l2132 lab=vss}
C {devices/lab_pin.sym} 120 -1230 0 1 {name=l2133 lab=m0_0}
C {devices/lab_pin.sym} 80 -1200 0 0 {name=l2134 lab=dhn1}
C {devices/lab_pin.sym} 120 -1170 0 1 {name=l2135 lab=m1_0}
C {devices/lab_pin.sym} 120 -1200 0 1 {name=l2136 lab=vss}
C {devices/lab_pin.sym} 170 -1230 0 1 {name=l2137 lab=m0_1}
C {devices/lab_pin.sym} 130 -1200 0 0 {name=l2138 lab=dh1}
C {devices/lab_pin.sym} 170 -1170 0 1 {name=l2139 lab=m1_0}
C {devices/lab_pin.sym} 170 -1200 0 1 {name=l2140 lab=vss}
C {devices/lab_pin.sym} 220 -1230 0 1 {name=l2141 lab=m0_2}
C {devices/lab_pin.sym} 180 -1200 0 0 {name=l2142 lab=dhn1}
C {devices/lab_pin.sym} 220 -1170 0 1 {name=l2143 lab=m1_1}
C {devices/lab_pin.sym} 220 -1200 0 1 {name=l2144 lab=vss}
C {devices/lab_pin.sym} 270 -1230 0 1 {name=l2145 lab=m0_3}
C {devices/lab_pin.sym} 230 -1200 0 0 {name=l2146 lab=dh1}
C {devices/lab_pin.sym} 270 -1170 0 1 {name=l2147 lab=m1_1}
C {devices/lab_pin.sym} 270 -1200 0 1 {name=l2148 lab=vss}
C {devices/lab_pin.sym} 320 -1230 0 1 {name=l2149 lab=m0_4}
C {devices/lab_pin.sym} 280 -1200 0 0 {name=l2150 lab=dhn1}
C {devices/lab_pin.sym} 320 -1170 0 1 {name=l2151 lab=m1_2}
C {devices/lab_pin.sym} 320 -1200 0 1 {name=l2152 lab=vss}
C {devices/lab_pin.sym} 370 -1230 0 1 {name=l2153 lab=m0_5}
C {devices/lab_pin.sym} 330 -1200 0 0 {name=l2154 lab=dh1}
C {devices/lab_pin.sym} 370 -1170 0 1 {name=l2155 lab=m1_2}
C {devices/lab_pin.sym} 370 -1200 0 1 {name=l2156 lab=vss}
C {devices/lab_pin.sym} 420 -1230 0 1 {name=l2157 lab=m0_6}
C {devices/lab_pin.sym} 380 -1200 0 0 {name=l2158 lab=dhn1}
C {devices/lab_pin.sym} 420 -1170 0 1 {name=l2159 lab=m1_3}
C {devices/lab_pin.sym} 420 -1200 0 1 {name=l2160 lab=vss}
C {devices/lab_pin.sym} 470 -1230 0 1 {name=l2161 lab=m0_7}
C {devices/lab_pin.sym} 430 -1200 0 0 {name=l2162 lab=dh1}
C {devices/lab_pin.sym} 470 -1170 0 1 {name=l2163 lab=m1_3}
C {devices/lab_pin.sym} 470 -1200 0 1 {name=l2164 lab=vss}
C {devices/lab_pin.sym} 520 -1230 0 1 {name=l2165 lab=m0_8}
C {devices/lab_pin.sym} 480 -1200 0 0 {name=l2166 lab=dhn1}
C {devices/lab_pin.sym} 520 -1170 0 1 {name=l2167 lab=m1_4}
C {devices/lab_pin.sym} 520 -1200 0 1 {name=l2168 lab=vss}
C {devices/lab_pin.sym} 570 -1230 0 1 {name=l2169 lab=m0_9}
C {devices/lab_pin.sym} 530 -1200 0 0 {name=l2170 lab=dh1}
C {devices/lab_pin.sym} 570 -1170 0 1 {name=l2171 lab=m1_4}
C {devices/lab_pin.sym} 570 -1200 0 1 {name=l2172 lab=vss}
C {devices/lab_pin.sym} 620 -1230 0 1 {name=l2173 lab=m0_10}
C {devices/lab_pin.sym} 580 -1200 0 0 {name=l2174 lab=dhn1}
C {devices/lab_pin.sym} 620 -1170 0 1 {name=l2175 lab=m1_5}
C {devices/lab_pin.sym} 620 -1200 0 1 {name=l2176 lab=vss}
C {devices/lab_pin.sym} 670 -1230 0 1 {name=l2177 lab=m0_11}
C {devices/lab_pin.sym} 630 -1200 0 0 {name=l2178 lab=dh1}
C {devices/lab_pin.sym} 670 -1170 0 1 {name=l2179 lab=m1_5}
C {devices/lab_pin.sym} 670 -1200 0 1 {name=l2180 lab=vss}
C {devices/lab_pin.sym} 720 -1230 0 1 {name=l2181 lab=m0_12}
C {devices/lab_pin.sym} 680 -1200 0 0 {name=l2182 lab=dhn1}
C {devices/lab_pin.sym} 720 -1170 0 1 {name=l2183 lab=m1_6}
C {devices/lab_pin.sym} 720 -1200 0 1 {name=l2184 lab=vss}
C {devices/lab_pin.sym} 770 -1230 0 1 {name=l2185 lab=m0_13}
C {devices/lab_pin.sym} 730 -1200 0 0 {name=l2186 lab=dh1}
C {devices/lab_pin.sym} 770 -1170 0 1 {name=l2187 lab=m1_6}
C {devices/lab_pin.sym} 770 -1200 0 1 {name=l2188 lab=vss}
C {devices/lab_pin.sym} 820 -1230 0 1 {name=l2189 lab=m0_14}
C {devices/lab_pin.sym} 780 -1200 0 0 {name=l2190 lab=dhn1}
C {devices/lab_pin.sym} 820 -1170 0 1 {name=l2191 lab=m1_7}
C {devices/lab_pin.sym} 820 -1200 0 1 {name=l2192 lab=vss}
C {devices/lab_pin.sym} 870 -1230 0 1 {name=l2193 lab=m0_15}
C {devices/lab_pin.sym} 830 -1200 0 0 {name=l2194 lab=dh1}
C {devices/lab_pin.sym} 870 -1170 0 1 {name=l2195 lab=m1_7}
C {devices/lab_pin.sym} 870 -1200 0 1 {name=l2196 lab=vss}
C {devices/lab_pin.sym} 920 -1230 0 1 {name=l2197 lab=m0_16}
C {devices/lab_pin.sym} 880 -1200 0 0 {name=l2198 lab=dhn1}
C {devices/lab_pin.sym} 920 -1170 0 1 {name=l2199 lab=m1_8}
C {devices/lab_pin.sym} 920 -1200 0 1 {name=l2200 lab=vss}
C {devices/lab_pin.sym} 970 -1230 0 1 {name=l2201 lab=m0_17}
C {devices/lab_pin.sym} 930 -1200 0 0 {name=l2202 lab=dh1}
C {devices/lab_pin.sym} 970 -1170 0 1 {name=l2203 lab=m1_8}
C {devices/lab_pin.sym} 970 -1200 0 1 {name=l2204 lab=vss}
C {devices/lab_pin.sym} 1020 -1230 0 1 {name=l2205 lab=m0_18}
C {devices/lab_pin.sym} 980 -1200 0 0 {name=l2206 lab=dhn1}
C {devices/lab_pin.sym} 1020 -1170 0 1 {name=l2207 lab=m1_9}
C {devices/lab_pin.sym} 1020 -1200 0 1 {name=l2208 lab=vss}
C {devices/lab_pin.sym} 1070 -1230 0 1 {name=l2209 lab=m0_19}
C {devices/lab_pin.sym} 1030 -1200 0 0 {name=l2210 lab=dh1}
C {devices/lab_pin.sym} 1070 -1170 0 1 {name=l2211 lab=m1_9}
C {devices/lab_pin.sym} 1070 -1200 0 1 {name=l2212 lab=vss}
C {devices/lab_pin.sym} 1120 -1230 0 1 {name=l2213 lab=m0_20}
C {devices/lab_pin.sym} 1080 -1200 0 0 {name=l2214 lab=dhn1}
C {devices/lab_pin.sym} 1120 -1170 0 1 {name=l2215 lab=m1_10}
C {devices/lab_pin.sym} 1120 -1200 0 1 {name=l2216 lab=vss}
C {devices/lab_pin.sym} 1170 -1230 0 1 {name=l2217 lab=m0_21}
C {devices/lab_pin.sym} 1130 -1200 0 0 {name=l2218 lab=dh1}
C {devices/lab_pin.sym} 1170 -1170 0 1 {name=l2219 lab=m1_10}
C {devices/lab_pin.sym} 1170 -1200 0 1 {name=l2220 lab=vss}
C {devices/lab_pin.sym} 1220 -1230 0 1 {name=l2221 lab=m0_22}
C {devices/lab_pin.sym} 1180 -1200 0 0 {name=l2222 lab=dhn1}
C {devices/lab_pin.sym} 1220 -1170 0 1 {name=l2223 lab=m1_11}
C {devices/lab_pin.sym} 1220 -1200 0 1 {name=l2224 lab=vss}
C {devices/lab_pin.sym} 1270 -1230 0 1 {name=l2225 lab=m0_23}
C {devices/lab_pin.sym} 1230 -1200 0 0 {name=l2226 lab=dh1}
C {devices/lab_pin.sym} 1270 -1170 0 1 {name=l2227 lab=m1_11}
C {devices/lab_pin.sym} 1270 -1200 0 1 {name=l2228 lab=vss}
C {devices/lab_pin.sym} 1320 -1230 0 1 {name=l2229 lab=m0_24}
C {devices/lab_pin.sym} 1280 -1200 0 0 {name=l2230 lab=dhn1}
C {devices/lab_pin.sym} 1320 -1170 0 1 {name=l2231 lab=m1_12}
C {devices/lab_pin.sym} 1320 -1200 0 1 {name=l2232 lab=vss}
C {devices/lab_pin.sym} 1370 -1230 0 1 {name=l2233 lab=m0_25}
C {devices/lab_pin.sym} 1330 -1200 0 0 {name=l2234 lab=dh1}
C {devices/lab_pin.sym} 1370 -1170 0 1 {name=l2235 lab=m1_12}
C {devices/lab_pin.sym} 1370 -1200 0 1 {name=l2236 lab=vss}
C {devices/lab_pin.sym} 1420 -1230 0 1 {name=l2237 lab=m0_26}
C {devices/lab_pin.sym} 1380 -1200 0 0 {name=l2238 lab=dhn1}
C {devices/lab_pin.sym} 1420 -1170 0 1 {name=l2239 lab=m1_13}
C {devices/lab_pin.sym} 1420 -1200 0 1 {name=l2240 lab=vss}
C {devices/lab_pin.sym} 1470 -1230 0 1 {name=l2241 lab=m0_27}
C {devices/lab_pin.sym} 1430 -1200 0 0 {name=l2242 lab=dh1}
C {devices/lab_pin.sym} 1470 -1170 0 1 {name=l2243 lab=m1_13}
C {devices/lab_pin.sym} 1470 -1200 0 1 {name=l2244 lab=vss}
C {devices/lab_pin.sym} 1520 -1230 0 1 {name=l2245 lab=m0_28}
C {devices/lab_pin.sym} 1480 -1200 0 0 {name=l2246 lab=dhn1}
C {devices/lab_pin.sym} 1520 -1170 0 1 {name=l2247 lab=m1_14}
C {devices/lab_pin.sym} 1520 -1200 0 1 {name=l2248 lab=vss}
C {devices/lab_pin.sym} 1570 -1230 0 1 {name=l2249 lab=m0_29}
C {devices/lab_pin.sym} 1530 -1200 0 0 {name=l2250 lab=dh1}
C {devices/lab_pin.sym} 1570 -1170 0 1 {name=l2251 lab=m1_14}
C {devices/lab_pin.sym} 1570 -1200 0 1 {name=l2252 lab=vss}
C {devices/lab_pin.sym} 1620 -1230 0 1 {name=l2253 lab=m0_30}
C {devices/lab_pin.sym} 1580 -1200 0 0 {name=l2254 lab=dhn1}
C {devices/lab_pin.sym} 1620 -1170 0 1 {name=l2255 lab=m1_15}
C {devices/lab_pin.sym} 1620 -1200 0 1 {name=l2256 lab=vss}
C {devices/lab_pin.sym} 1670 -1230 0 1 {name=l2257 lab=m0_31}
C {devices/lab_pin.sym} 1630 -1200 0 0 {name=l2258 lab=dh1}
C {devices/lab_pin.sym} 1670 -1170 0 1 {name=l2259 lab=m1_15}
C {devices/lab_pin.sym} 1670 -1200 0 1 {name=l2260 lab=vss}
C {devices/lab_pin.sym} 1720 -1230 0 1 {name=l2261 lab=m0_32}
C {devices/lab_pin.sym} 1680 -1200 0 0 {name=l2262 lab=dhn1}
C {devices/lab_pin.sym} 1720 -1170 0 1 {name=l2263 lab=m1_16}
C {devices/lab_pin.sym} 1720 -1200 0 1 {name=l2264 lab=vss}
C {devices/lab_pin.sym} 1770 -1230 0 1 {name=l2265 lab=m0_33}
C {devices/lab_pin.sym} 1730 -1200 0 0 {name=l2266 lab=dh1}
C {devices/lab_pin.sym} 1770 -1170 0 1 {name=l2267 lab=m1_16}
C {devices/lab_pin.sym} 1770 -1200 0 1 {name=l2268 lab=vss}
C {devices/lab_pin.sym} 1820 -1230 0 1 {name=l2269 lab=m0_34}
C {devices/lab_pin.sym} 1780 -1200 0 0 {name=l2270 lab=dhn1}
C {devices/lab_pin.sym} 1820 -1170 0 1 {name=l2271 lab=m1_17}
C {devices/lab_pin.sym} 1820 -1200 0 1 {name=l2272 lab=vss}
C {devices/lab_pin.sym} 1870 -1230 0 1 {name=l2273 lab=m0_35}
C {devices/lab_pin.sym} 1830 -1200 0 0 {name=l2274 lab=dh1}
C {devices/lab_pin.sym} 1870 -1170 0 1 {name=l2275 lab=m1_17}
C {devices/lab_pin.sym} 1870 -1200 0 1 {name=l2276 lab=vss}
C {devices/lab_pin.sym} 1920 -1230 0 1 {name=l2277 lab=m0_36}
C {devices/lab_pin.sym} 1880 -1200 0 0 {name=l2278 lab=dhn1}
C {devices/lab_pin.sym} 1920 -1170 0 1 {name=l2279 lab=m1_18}
C {devices/lab_pin.sym} 1920 -1200 0 1 {name=l2280 lab=vss}
C {devices/lab_pin.sym} 1970 -1230 0 1 {name=l2281 lab=m0_37}
C {devices/lab_pin.sym} 1930 -1200 0 0 {name=l2282 lab=dh1}
C {devices/lab_pin.sym} 1970 -1170 0 1 {name=l2283 lab=m1_18}
C {devices/lab_pin.sym} 1970 -1200 0 1 {name=l2284 lab=vss}
C {devices/lab_pin.sym} 2020 -1230 0 1 {name=l2285 lab=m0_38}
C {devices/lab_pin.sym} 1980 -1200 0 0 {name=l2286 lab=dhn1}
C {devices/lab_pin.sym} 2020 -1170 0 1 {name=l2287 lab=m1_19}
C {devices/lab_pin.sym} 2020 -1200 0 1 {name=l2288 lab=vss}
C {devices/lab_pin.sym} 2070 -1230 0 1 {name=l2289 lab=m0_39}
C {devices/lab_pin.sym} 2030 -1200 0 0 {name=l2290 lab=dh1}
C {devices/lab_pin.sym} 2070 -1170 0 1 {name=l2291 lab=m1_19}
C {devices/lab_pin.sym} 2070 -1200 0 1 {name=l2292 lab=vss}
C {devices/lab_pin.sym} 2120 -1230 0 1 {name=l2293 lab=m0_40}
C {devices/lab_pin.sym} 2080 -1200 0 0 {name=l2294 lab=dhn1}
C {devices/lab_pin.sym} 2120 -1170 0 1 {name=l2295 lab=m1_20}
C {devices/lab_pin.sym} 2120 -1200 0 1 {name=l2296 lab=vss}
C {devices/lab_pin.sym} 2170 -1230 0 1 {name=l2297 lab=m0_41}
C {devices/lab_pin.sym} 2130 -1200 0 0 {name=l2298 lab=dh1}
C {devices/lab_pin.sym} 2170 -1170 0 1 {name=l2299 lab=m1_20}
C {devices/lab_pin.sym} 2170 -1200 0 1 {name=l2300 lab=vss}
C {devices/lab_pin.sym} 2220 -1230 0 1 {name=l2301 lab=m0_42}
C {devices/lab_pin.sym} 2180 -1200 0 0 {name=l2302 lab=dhn1}
C {devices/lab_pin.sym} 2220 -1170 0 1 {name=l2303 lab=m1_21}
C {devices/lab_pin.sym} 2220 -1200 0 1 {name=l2304 lab=vss}
C {devices/lab_pin.sym} 2270 -1230 0 1 {name=l2305 lab=m0_43}
C {devices/lab_pin.sym} 2230 -1200 0 0 {name=l2306 lab=dh1}
C {devices/lab_pin.sym} 2270 -1170 0 1 {name=l2307 lab=m1_21}
C {devices/lab_pin.sym} 2270 -1200 0 1 {name=l2308 lab=vss}
C {devices/lab_pin.sym} 2320 -1230 0 1 {name=l2309 lab=m0_44}
C {devices/lab_pin.sym} 2280 -1200 0 0 {name=l2310 lab=dhn1}
C {devices/lab_pin.sym} 2320 -1170 0 1 {name=l2311 lab=m1_22}
C {devices/lab_pin.sym} 2320 -1200 0 1 {name=l2312 lab=vss}
C {devices/lab_pin.sym} 2370 -1230 0 1 {name=l2313 lab=m0_45}
C {devices/lab_pin.sym} 2330 -1200 0 0 {name=l2314 lab=dh1}
C {devices/lab_pin.sym} 2370 -1170 0 1 {name=l2315 lab=m1_22}
C {devices/lab_pin.sym} 2370 -1200 0 1 {name=l2316 lab=vss}
C {devices/lab_pin.sym} 2420 -1230 0 1 {name=l2317 lab=m0_46}
C {devices/lab_pin.sym} 2380 -1200 0 0 {name=l2318 lab=dhn1}
C {devices/lab_pin.sym} 2420 -1170 0 1 {name=l2319 lab=m1_23}
C {devices/lab_pin.sym} 2420 -1200 0 1 {name=l2320 lab=vss}
C {devices/lab_pin.sym} 2470 -1230 0 1 {name=l2321 lab=m0_47}
C {devices/lab_pin.sym} 2430 -1200 0 0 {name=l2322 lab=dh1}
C {devices/lab_pin.sym} 2470 -1170 0 1 {name=l2323 lab=m1_23}
C {devices/lab_pin.sym} 2470 -1200 0 1 {name=l2324 lab=vss}
C {devices/lab_pin.sym} 2520 -1230 0 1 {name=l2325 lab=m0_48}
C {devices/lab_pin.sym} 2480 -1200 0 0 {name=l2326 lab=dhn1}
C {devices/lab_pin.sym} 2520 -1170 0 1 {name=l2327 lab=m1_24}
C {devices/lab_pin.sym} 2520 -1200 0 1 {name=l2328 lab=vss}
C {devices/lab_pin.sym} 2570 -1230 0 1 {name=l2329 lab=m0_49}
C {devices/lab_pin.sym} 2530 -1200 0 0 {name=l2330 lab=dh1}
C {devices/lab_pin.sym} 2570 -1170 0 1 {name=l2331 lab=m1_24}
C {devices/lab_pin.sym} 2570 -1200 0 1 {name=l2332 lab=vss}
C {devices/lab_pin.sym} 2620 -1230 0 1 {name=l2333 lab=m0_50}
C {devices/lab_pin.sym} 2580 -1200 0 0 {name=l2334 lab=dhn1}
C {devices/lab_pin.sym} 2620 -1170 0 1 {name=l2335 lab=m1_25}
C {devices/lab_pin.sym} 2620 -1200 0 1 {name=l2336 lab=vss}
C {devices/lab_pin.sym} 2670 -1230 0 1 {name=l2337 lab=m0_51}
C {devices/lab_pin.sym} 2630 -1200 0 0 {name=l2338 lab=dh1}
C {devices/lab_pin.sym} 2670 -1170 0 1 {name=l2339 lab=m1_25}
C {devices/lab_pin.sym} 2670 -1200 0 1 {name=l2340 lab=vss}
C {devices/lab_pin.sym} 2720 -1230 0 1 {name=l2341 lab=m0_52}
C {devices/lab_pin.sym} 2680 -1200 0 0 {name=l2342 lab=dhn1}
C {devices/lab_pin.sym} 2720 -1170 0 1 {name=l2343 lab=m1_26}
C {devices/lab_pin.sym} 2720 -1200 0 1 {name=l2344 lab=vss}
C {devices/lab_pin.sym} 2770 -1230 0 1 {name=l2345 lab=m0_53}
C {devices/lab_pin.sym} 2730 -1200 0 0 {name=l2346 lab=dh1}
C {devices/lab_pin.sym} 2770 -1170 0 1 {name=l2347 lab=m1_26}
C {devices/lab_pin.sym} 2770 -1200 0 1 {name=l2348 lab=vss}
C {devices/lab_pin.sym} 2820 -1230 0 1 {name=l2349 lab=m0_54}
C {devices/lab_pin.sym} 2780 -1200 0 0 {name=l2350 lab=dhn1}
C {devices/lab_pin.sym} 2820 -1170 0 1 {name=l2351 lab=m1_27}
C {devices/lab_pin.sym} 2820 -1200 0 1 {name=l2352 lab=vss}
C {devices/lab_pin.sym} 2870 -1230 0 1 {name=l2353 lab=m0_55}
C {devices/lab_pin.sym} 2830 -1200 0 0 {name=l2354 lab=dh1}
C {devices/lab_pin.sym} 2870 -1170 0 1 {name=l2355 lab=m1_27}
C {devices/lab_pin.sym} 2870 -1200 0 1 {name=l2356 lab=vss}
C {devices/lab_pin.sym} 2920 -1230 0 1 {name=l2357 lab=m0_56}
C {devices/lab_pin.sym} 2880 -1200 0 0 {name=l2358 lab=dhn1}
C {devices/lab_pin.sym} 2920 -1170 0 1 {name=l2359 lab=m1_28}
C {devices/lab_pin.sym} 2920 -1200 0 1 {name=l2360 lab=vss}
C {devices/lab_pin.sym} 2970 -1230 0 1 {name=l2361 lab=m0_57}
C {devices/lab_pin.sym} 2930 -1200 0 0 {name=l2362 lab=dh1}
C {devices/lab_pin.sym} 2970 -1170 0 1 {name=l2363 lab=m1_28}
C {devices/lab_pin.sym} 2970 -1200 0 1 {name=l2364 lab=vss}
C {devices/lab_pin.sym} 3020 -1230 0 1 {name=l2365 lab=m0_58}
C {devices/lab_pin.sym} 2980 -1200 0 0 {name=l2366 lab=dhn1}
C {devices/lab_pin.sym} 3020 -1170 0 1 {name=l2367 lab=m1_29}
C {devices/lab_pin.sym} 3020 -1200 0 1 {name=l2368 lab=vss}
C {devices/lab_pin.sym} 3070 -1230 0 1 {name=l2369 lab=m0_59}
C {devices/lab_pin.sym} 3030 -1200 0 0 {name=l2370 lab=dh1}
C {devices/lab_pin.sym} 3070 -1170 0 1 {name=l2371 lab=m1_29}
C {devices/lab_pin.sym} 3070 -1200 0 1 {name=l2372 lab=vss}
C {devices/lab_pin.sym} 3120 -1230 0 1 {name=l2373 lab=m0_60}
C {devices/lab_pin.sym} 3080 -1200 0 0 {name=l2374 lab=dhn1}
C {devices/lab_pin.sym} 3120 -1170 0 1 {name=l2375 lab=m1_30}
C {devices/lab_pin.sym} 3120 -1200 0 1 {name=l2376 lab=vss}
C {devices/lab_pin.sym} 3170 -1230 0 1 {name=l2377 lab=m0_61}
C {devices/lab_pin.sym} 3130 -1200 0 0 {name=l2378 lab=dh1}
C {devices/lab_pin.sym} 3170 -1170 0 1 {name=l2379 lab=m1_30}
C {devices/lab_pin.sym} 3170 -1200 0 1 {name=l2380 lab=vss}
C {devices/lab_pin.sym} 3220 -1230 0 1 {name=l2381 lab=m0_62}
C {devices/lab_pin.sym} 3180 -1200 0 0 {name=l2382 lab=dhn1}
C {devices/lab_pin.sym} 3220 -1170 0 1 {name=l2383 lab=m1_31}
C {devices/lab_pin.sym} 3220 -1200 0 1 {name=l2384 lab=vss}
C {devices/lab_pin.sym} 3270 -1230 0 1 {name=l2385 lab=m0_63}
C {devices/lab_pin.sym} 3230 -1200 0 0 {name=l2386 lab=dh1}
C {devices/lab_pin.sym} 3270 -1170 0 1 {name=l2387 lab=m1_31}
C {devices/lab_pin.sym} 3270 -1200 0 1 {name=l2388 lab=vss}
C {devices/lab_pin.sym} 120 -1150 0 1 {name=l2389 lab=m0_64}
C {devices/lab_pin.sym} 80 -1120 0 0 {name=l2390 lab=dhn1}
C {devices/lab_pin.sym} 120 -1090 0 1 {name=l2391 lab=m1_32}
C {devices/lab_pin.sym} 120 -1120 0 1 {name=l2392 lab=vss}
C {devices/lab_pin.sym} 170 -1150 0 1 {name=l2393 lab=m0_65}
C {devices/lab_pin.sym} 130 -1120 0 0 {name=l2394 lab=dh1}
C {devices/lab_pin.sym} 170 -1090 0 1 {name=l2395 lab=m1_32}
C {devices/lab_pin.sym} 170 -1120 0 1 {name=l2396 lab=vss}
C {devices/lab_pin.sym} 220 -1150 0 1 {name=l2397 lab=m0_66}
C {devices/lab_pin.sym} 180 -1120 0 0 {name=l2398 lab=dhn1}
C {devices/lab_pin.sym} 220 -1090 0 1 {name=l2399 lab=m1_33}
C {devices/lab_pin.sym} 220 -1120 0 1 {name=l2400 lab=vss}
C {devices/lab_pin.sym} 270 -1150 0 1 {name=l2401 lab=m0_67}
C {devices/lab_pin.sym} 230 -1120 0 0 {name=l2402 lab=dh1}
C {devices/lab_pin.sym} 270 -1090 0 1 {name=l2403 lab=m1_33}
C {devices/lab_pin.sym} 270 -1120 0 1 {name=l2404 lab=vss}
C {devices/lab_pin.sym} 320 -1150 0 1 {name=l2405 lab=m0_68}
C {devices/lab_pin.sym} 280 -1120 0 0 {name=l2406 lab=dhn1}
C {devices/lab_pin.sym} 320 -1090 0 1 {name=l2407 lab=m1_34}
C {devices/lab_pin.sym} 320 -1120 0 1 {name=l2408 lab=vss}
C {devices/lab_pin.sym} 370 -1150 0 1 {name=l2409 lab=m0_69}
C {devices/lab_pin.sym} 330 -1120 0 0 {name=l2410 lab=dh1}
C {devices/lab_pin.sym} 370 -1090 0 1 {name=l2411 lab=m1_34}
C {devices/lab_pin.sym} 370 -1120 0 1 {name=l2412 lab=vss}
C {devices/lab_pin.sym} 420 -1150 0 1 {name=l2413 lab=m0_70}
C {devices/lab_pin.sym} 380 -1120 0 0 {name=l2414 lab=dhn1}
C {devices/lab_pin.sym} 420 -1090 0 1 {name=l2415 lab=m1_35}
C {devices/lab_pin.sym} 420 -1120 0 1 {name=l2416 lab=vss}
C {devices/lab_pin.sym} 470 -1150 0 1 {name=l2417 lab=m0_71}
C {devices/lab_pin.sym} 430 -1120 0 0 {name=l2418 lab=dh1}
C {devices/lab_pin.sym} 470 -1090 0 1 {name=l2419 lab=m1_35}
C {devices/lab_pin.sym} 470 -1120 0 1 {name=l2420 lab=vss}
C {devices/lab_pin.sym} 520 -1150 0 1 {name=l2421 lab=m0_72}
C {devices/lab_pin.sym} 480 -1120 0 0 {name=l2422 lab=dhn1}
C {devices/lab_pin.sym} 520 -1090 0 1 {name=l2423 lab=m1_36}
C {devices/lab_pin.sym} 520 -1120 0 1 {name=l2424 lab=vss}
C {devices/lab_pin.sym} 570 -1150 0 1 {name=l2425 lab=m0_73}
C {devices/lab_pin.sym} 530 -1120 0 0 {name=l2426 lab=dh1}
C {devices/lab_pin.sym} 570 -1090 0 1 {name=l2427 lab=m1_36}
C {devices/lab_pin.sym} 570 -1120 0 1 {name=l2428 lab=vss}
C {devices/lab_pin.sym} 620 -1150 0 1 {name=l2429 lab=m0_74}
C {devices/lab_pin.sym} 580 -1120 0 0 {name=l2430 lab=dhn1}
C {devices/lab_pin.sym} 620 -1090 0 1 {name=l2431 lab=m1_37}
C {devices/lab_pin.sym} 620 -1120 0 1 {name=l2432 lab=vss}
C {devices/lab_pin.sym} 670 -1150 0 1 {name=l2433 lab=m0_75}
C {devices/lab_pin.sym} 630 -1120 0 0 {name=l2434 lab=dh1}
C {devices/lab_pin.sym} 670 -1090 0 1 {name=l2435 lab=m1_37}
C {devices/lab_pin.sym} 670 -1120 0 1 {name=l2436 lab=vss}
C {devices/lab_pin.sym} 720 -1150 0 1 {name=l2437 lab=m0_76}
C {devices/lab_pin.sym} 680 -1120 0 0 {name=l2438 lab=dhn1}
C {devices/lab_pin.sym} 720 -1090 0 1 {name=l2439 lab=m1_38}
C {devices/lab_pin.sym} 720 -1120 0 1 {name=l2440 lab=vss}
C {devices/lab_pin.sym} 770 -1150 0 1 {name=l2441 lab=m0_77}
C {devices/lab_pin.sym} 730 -1120 0 0 {name=l2442 lab=dh1}
C {devices/lab_pin.sym} 770 -1090 0 1 {name=l2443 lab=m1_38}
C {devices/lab_pin.sym} 770 -1120 0 1 {name=l2444 lab=vss}
C {devices/lab_pin.sym} 820 -1150 0 1 {name=l2445 lab=m0_78}
C {devices/lab_pin.sym} 780 -1120 0 0 {name=l2446 lab=dhn1}
C {devices/lab_pin.sym} 820 -1090 0 1 {name=l2447 lab=m1_39}
C {devices/lab_pin.sym} 820 -1120 0 1 {name=l2448 lab=vss}
C {devices/lab_pin.sym} 870 -1150 0 1 {name=l2449 lab=m0_79}
C {devices/lab_pin.sym} 830 -1120 0 0 {name=l2450 lab=dh1}
C {devices/lab_pin.sym} 870 -1090 0 1 {name=l2451 lab=m1_39}
C {devices/lab_pin.sym} 870 -1120 0 1 {name=l2452 lab=vss}
C {devices/lab_pin.sym} 920 -1150 0 1 {name=l2453 lab=m0_80}
C {devices/lab_pin.sym} 880 -1120 0 0 {name=l2454 lab=dhn1}
C {devices/lab_pin.sym} 920 -1090 0 1 {name=l2455 lab=m1_40}
C {devices/lab_pin.sym} 920 -1120 0 1 {name=l2456 lab=vss}
C {devices/lab_pin.sym} 970 -1150 0 1 {name=l2457 lab=m0_81}
C {devices/lab_pin.sym} 930 -1120 0 0 {name=l2458 lab=dh1}
C {devices/lab_pin.sym} 970 -1090 0 1 {name=l2459 lab=m1_40}
C {devices/lab_pin.sym} 970 -1120 0 1 {name=l2460 lab=vss}
C {devices/lab_pin.sym} 1020 -1150 0 1 {name=l2461 lab=m0_82}
C {devices/lab_pin.sym} 980 -1120 0 0 {name=l2462 lab=dhn1}
C {devices/lab_pin.sym} 1020 -1090 0 1 {name=l2463 lab=m1_41}
C {devices/lab_pin.sym} 1020 -1120 0 1 {name=l2464 lab=vss}
C {devices/lab_pin.sym} 1070 -1150 0 1 {name=l2465 lab=m0_83}
C {devices/lab_pin.sym} 1030 -1120 0 0 {name=l2466 lab=dh1}
C {devices/lab_pin.sym} 1070 -1090 0 1 {name=l2467 lab=m1_41}
C {devices/lab_pin.sym} 1070 -1120 0 1 {name=l2468 lab=vss}
C {devices/lab_pin.sym} 1120 -1150 0 1 {name=l2469 lab=m0_84}
C {devices/lab_pin.sym} 1080 -1120 0 0 {name=l2470 lab=dhn1}
C {devices/lab_pin.sym} 1120 -1090 0 1 {name=l2471 lab=m1_42}
C {devices/lab_pin.sym} 1120 -1120 0 1 {name=l2472 lab=vss}
C {devices/lab_pin.sym} 1170 -1150 0 1 {name=l2473 lab=m0_85}
C {devices/lab_pin.sym} 1130 -1120 0 0 {name=l2474 lab=dh1}
C {devices/lab_pin.sym} 1170 -1090 0 1 {name=l2475 lab=m1_42}
C {devices/lab_pin.sym} 1170 -1120 0 1 {name=l2476 lab=vss}
C {devices/lab_pin.sym} 1220 -1150 0 1 {name=l2477 lab=m0_86}
C {devices/lab_pin.sym} 1180 -1120 0 0 {name=l2478 lab=dhn1}
C {devices/lab_pin.sym} 1220 -1090 0 1 {name=l2479 lab=m1_43}
C {devices/lab_pin.sym} 1220 -1120 0 1 {name=l2480 lab=vss}
C {devices/lab_pin.sym} 1270 -1150 0 1 {name=l2481 lab=m0_87}
C {devices/lab_pin.sym} 1230 -1120 0 0 {name=l2482 lab=dh1}
C {devices/lab_pin.sym} 1270 -1090 0 1 {name=l2483 lab=m1_43}
C {devices/lab_pin.sym} 1270 -1120 0 1 {name=l2484 lab=vss}
C {devices/lab_pin.sym} 1320 -1150 0 1 {name=l2485 lab=m0_88}
C {devices/lab_pin.sym} 1280 -1120 0 0 {name=l2486 lab=dhn1}
C {devices/lab_pin.sym} 1320 -1090 0 1 {name=l2487 lab=m1_44}
C {devices/lab_pin.sym} 1320 -1120 0 1 {name=l2488 lab=vss}
C {devices/lab_pin.sym} 1370 -1150 0 1 {name=l2489 lab=m0_89}
C {devices/lab_pin.sym} 1330 -1120 0 0 {name=l2490 lab=dh1}
C {devices/lab_pin.sym} 1370 -1090 0 1 {name=l2491 lab=m1_44}
C {devices/lab_pin.sym} 1370 -1120 0 1 {name=l2492 lab=vss}
C {devices/lab_pin.sym} 1420 -1150 0 1 {name=l2493 lab=m0_90}
C {devices/lab_pin.sym} 1380 -1120 0 0 {name=l2494 lab=dhn1}
C {devices/lab_pin.sym} 1420 -1090 0 1 {name=l2495 lab=m1_45}
C {devices/lab_pin.sym} 1420 -1120 0 1 {name=l2496 lab=vss}
C {devices/lab_pin.sym} 1470 -1150 0 1 {name=l2497 lab=m0_91}
C {devices/lab_pin.sym} 1430 -1120 0 0 {name=l2498 lab=dh1}
C {devices/lab_pin.sym} 1470 -1090 0 1 {name=l2499 lab=m1_45}
C {devices/lab_pin.sym} 1470 -1120 0 1 {name=l2500 lab=vss}
C {devices/lab_pin.sym} 1520 -1150 0 1 {name=l2501 lab=m0_92}
C {devices/lab_pin.sym} 1480 -1120 0 0 {name=l2502 lab=dhn1}
C {devices/lab_pin.sym} 1520 -1090 0 1 {name=l2503 lab=m1_46}
C {devices/lab_pin.sym} 1520 -1120 0 1 {name=l2504 lab=vss}
C {devices/lab_pin.sym} 1570 -1150 0 1 {name=l2505 lab=m0_93}
C {devices/lab_pin.sym} 1530 -1120 0 0 {name=l2506 lab=dh1}
C {devices/lab_pin.sym} 1570 -1090 0 1 {name=l2507 lab=m1_46}
C {devices/lab_pin.sym} 1570 -1120 0 1 {name=l2508 lab=vss}
C {devices/lab_pin.sym} 1620 -1150 0 1 {name=l2509 lab=m0_94}
C {devices/lab_pin.sym} 1580 -1120 0 0 {name=l2510 lab=dhn1}
C {devices/lab_pin.sym} 1620 -1090 0 1 {name=l2511 lab=m1_47}
C {devices/lab_pin.sym} 1620 -1120 0 1 {name=l2512 lab=vss}
C {devices/lab_pin.sym} 1670 -1150 0 1 {name=l2513 lab=m0_95}
C {devices/lab_pin.sym} 1630 -1120 0 0 {name=l2514 lab=dh1}
C {devices/lab_pin.sym} 1670 -1090 0 1 {name=l2515 lab=m1_47}
C {devices/lab_pin.sym} 1670 -1120 0 1 {name=l2516 lab=vss}
C {devices/lab_pin.sym} 1720 -1150 0 1 {name=l2517 lab=m0_96}
C {devices/lab_pin.sym} 1680 -1120 0 0 {name=l2518 lab=dhn1}
C {devices/lab_pin.sym} 1720 -1090 0 1 {name=l2519 lab=m1_48}
C {devices/lab_pin.sym} 1720 -1120 0 1 {name=l2520 lab=vss}
C {devices/lab_pin.sym} 1770 -1150 0 1 {name=l2521 lab=m0_97}
C {devices/lab_pin.sym} 1730 -1120 0 0 {name=l2522 lab=dh1}
C {devices/lab_pin.sym} 1770 -1090 0 1 {name=l2523 lab=m1_48}
C {devices/lab_pin.sym} 1770 -1120 0 1 {name=l2524 lab=vss}
C {devices/lab_pin.sym} 1820 -1150 0 1 {name=l2525 lab=m0_98}
C {devices/lab_pin.sym} 1780 -1120 0 0 {name=l2526 lab=dhn1}
C {devices/lab_pin.sym} 1820 -1090 0 1 {name=l2527 lab=m1_49}
C {devices/lab_pin.sym} 1820 -1120 0 1 {name=l2528 lab=vss}
C {devices/lab_pin.sym} 1870 -1150 0 1 {name=l2529 lab=m0_99}
C {devices/lab_pin.sym} 1830 -1120 0 0 {name=l2530 lab=dh1}
C {devices/lab_pin.sym} 1870 -1090 0 1 {name=l2531 lab=m1_49}
C {devices/lab_pin.sym} 1870 -1120 0 1 {name=l2532 lab=vss}
C {devices/lab_pin.sym} 1920 -1150 0 1 {name=l2533 lab=m0_100}
C {devices/lab_pin.sym} 1880 -1120 0 0 {name=l2534 lab=dhn1}
C {devices/lab_pin.sym} 1920 -1090 0 1 {name=l2535 lab=m1_50}
C {devices/lab_pin.sym} 1920 -1120 0 1 {name=l2536 lab=vss}
C {devices/lab_pin.sym} 1970 -1150 0 1 {name=l2537 lab=m0_101}
C {devices/lab_pin.sym} 1930 -1120 0 0 {name=l2538 lab=dh1}
C {devices/lab_pin.sym} 1970 -1090 0 1 {name=l2539 lab=m1_50}
C {devices/lab_pin.sym} 1970 -1120 0 1 {name=l2540 lab=vss}
C {devices/lab_pin.sym} 2020 -1150 0 1 {name=l2541 lab=m0_102}
C {devices/lab_pin.sym} 1980 -1120 0 0 {name=l2542 lab=dhn1}
C {devices/lab_pin.sym} 2020 -1090 0 1 {name=l2543 lab=m1_51}
C {devices/lab_pin.sym} 2020 -1120 0 1 {name=l2544 lab=vss}
C {devices/lab_pin.sym} 2070 -1150 0 1 {name=l2545 lab=m0_103}
C {devices/lab_pin.sym} 2030 -1120 0 0 {name=l2546 lab=dh1}
C {devices/lab_pin.sym} 2070 -1090 0 1 {name=l2547 lab=m1_51}
C {devices/lab_pin.sym} 2070 -1120 0 1 {name=l2548 lab=vss}
C {devices/lab_pin.sym} 2120 -1150 0 1 {name=l2549 lab=m0_104}
C {devices/lab_pin.sym} 2080 -1120 0 0 {name=l2550 lab=dhn1}
C {devices/lab_pin.sym} 2120 -1090 0 1 {name=l2551 lab=m1_52}
C {devices/lab_pin.sym} 2120 -1120 0 1 {name=l2552 lab=vss}
C {devices/lab_pin.sym} 2170 -1150 0 1 {name=l2553 lab=m0_105}
C {devices/lab_pin.sym} 2130 -1120 0 0 {name=l2554 lab=dh1}
C {devices/lab_pin.sym} 2170 -1090 0 1 {name=l2555 lab=m1_52}
C {devices/lab_pin.sym} 2170 -1120 0 1 {name=l2556 lab=vss}
C {devices/lab_pin.sym} 2220 -1150 0 1 {name=l2557 lab=m0_106}
C {devices/lab_pin.sym} 2180 -1120 0 0 {name=l2558 lab=dhn1}
C {devices/lab_pin.sym} 2220 -1090 0 1 {name=l2559 lab=m1_53}
C {devices/lab_pin.sym} 2220 -1120 0 1 {name=l2560 lab=vss}
C {devices/lab_pin.sym} 2270 -1150 0 1 {name=l2561 lab=m0_107}
C {devices/lab_pin.sym} 2230 -1120 0 0 {name=l2562 lab=dh1}
C {devices/lab_pin.sym} 2270 -1090 0 1 {name=l2563 lab=m1_53}
C {devices/lab_pin.sym} 2270 -1120 0 1 {name=l2564 lab=vss}
C {devices/lab_pin.sym} 2320 -1150 0 1 {name=l2565 lab=m0_108}
C {devices/lab_pin.sym} 2280 -1120 0 0 {name=l2566 lab=dhn1}
C {devices/lab_pin.sym} 2320 -1090 0 1 {name=l2567 lab=m1_54}
C {devices/lab_pin.sym} 2320 -1120 0 1 {name=l2568 lab=vss}
C {devices/lab_pin.sym} 2370 -1150 0 1 {name=l2569 lab=m0_109}
C {devices/lab_pin.sym} 2330 -1120 0 0 {name=l2570 lab=dh1}
C {devices/lab_pin.sym} 2370 -1090 0 1 {name=l2571 lab=m1_54}
C {devices/lab_pin.sym} 2370 -1120 0 1 {name=l2572 lab=vss}
C {devices/lab_pin.sym} 2420 -1150 0 1 {name=l2573 lab=m0_110}
C {devices/lab_pin.sym} 2380 -1120 0 0 {name=l2574 lab=dhn1}
C {devices/lab_pin.sym} 2420 -1090 0 1 {name=l2575 lab=m1_55}
C {devices/lab_pin.sym} 2420 -1120 0 1 {name=l2576 lab=vss}
C {devices/lab_pin.sym} 2470 -1150 0 1 {name=l2577 lab=m0_111}
C {devices/lab_pin.sym} 2430 -1120 0 0 {name=l2578 lab=dh1}
C {devices/lab_pin.sym} 2470 -1090 0 1 {name=l2579 lab=m1_55}
C {devices/lab_pin.sym} 2470 -1120 0 1 {name=l2580 lab=vss}
C {devices/lab_pin.sym} 2520 -1150 0 1 {name=l2581 lab=m0_112}
C {devices/lab_pin.sym} 2480 -1120 0 0 {name=l2582 lab=dhn1}
C {devices/lab_pin.sym} 2520 -1090 0 1 {name=l2583 lab=m1_56}
C {devices/lab_pin.sym} 2520 -1120 0 1 {name=l2584 lab=vss}
C {devices/lab_pin.sym} 2570 -1150 0 1 {name=l2585 lab=m0_113}
C {devices/lab_pin.sym} 2530 -1120 0 0 {name=l2586 lab=dh1}
C {devices/lab_pin.sym} 2570 -1090 0 1 {name=l2587 lab=m1_56}
C {devices/lab_pin.sym} 2570 -1120 0 1 {name=l2588 lab=vss}
C {devices/lab_pin.sym} 2620 -1150 0 1 {name=l2589 lab=m0_114}
C {devices/lab_pin.sym} 2580 -1120 0 0 {name=l2590 lab=dhn1}
C {devices/lab_pin.sym} 2620 -1090 0 1 {name=l2591 lab=m1_57}
C {devices/lab_pin.sym} 2620 -1120 0 1 {name=l2592 lab=vss}
C {devices/lab_pin.sym} 2670 -1150 0 1 {name=l2593 lab=m0_115}
C {devices/lab_pin.sym} 2630 -1120 0 0 {name=l2594 lab=dh1}
C {devices/lab_pin.sym} 2670 -1090 0 1 {name=l2595 lab=m1_57}
C {devices/lab_pin.sym} 2670 -1120 0 1 {name=l2596 lab=vss}
C {devices/lab_pin.sym} 2720 -1150 0 1 {name=l2597 lab=m0_116}
C {devices/lab_pin.sym} 2680 -1120 0 0 {name=l2598 lab=dhn1}
C {devices/lab_pin.sym} 2720 -1090 0 1 {name=l2599 lab=m1_58}
C {devices/lab_pin.sym} 2720 -1120 0 1 {name=l2600 lab=vss}
C {devices/lab_pin.sym} 2770 -1150 0 1 {name=l2601 lab=m0_117}
C {devices/lab_pin.sym} 2730 -1120 0 0 {name=l2602 lab=dh1}
C {devices/lab_pin.sym} 2770 -1090 0 1 {name=l2603 lab=m1_58}
C {devices/lab_pin.sym} 2770 -1120 0 1 {name=l2604 lab=vss}
C {devices/lab_pin.sym} 2820 -1150 0 1 {name=l2605 lab=m0_118}
C {devices/lab_pin.sym} 2780 -1120 0 0 {name=l2606 lab=dhn1}
C {devices/lab_pin.sym} 2820 -1090 0 1 {name=l2607 lab=m1_59}
C {devices/lab_pin.sym} 2820 -1120 0 1 {name=l2608 lab=vss}
C {devices/lab_pin.sym} 2870 -1150 0 1 {name=l2609 lab=m0_119}
C {devices/lab_pin.sym} 2830 -1120 0 0 {name=l2610 lab=dh1}
C {devices/lab_pin.sym} 2870 -1090 0 1 {name=l2611 lab=m1_59}
C {devices/lab_pin.sym} 2870 -1120 0 1 {name=l2612 lab=vss}
C {devices/lab_pin.sym} 2920 -1150 0 1 {name=l2613 lab=m0_120}
C {devices/lab_pin.sym} 2880 -1120 0 0 {name=l2614 lab=dhn1}
C {devices/lab_pin.sym} 2920 -1090 0 1 {name=l2615 lab=m1_60}
C {devices/lab_pin.sym} 2920 -1120 0 1 {name=l2616 lab=vss}
C {devices/lab_pin.sym} 2970 -1150 0 1 {name=l2617 lab=m0_121}
C {devices/lab_pin.sym} 2930 -1120 0 0 {name=l2618 lab=dh1}
C {devices/lab_pin.sym} 2970 -1090 0 1 {name=l2619 lab=m1_60}
C {devices/lab_pin.sym} 2970 -1120 0 1 {name=l2620 lab=vss}
C {devices/lab_pin.sym} 3020 -1150 0 1 {name=l2621 lab=m0_122}
C {devices/lab_pin.sym} 2980 -1120 0 0 {name=l2622 lab=dhn1}
C {devices/lab_pin.sym} 3020 -1090 0 1 {name=l2623 lab=m1_61}
C {devices/lab_pin.sym} 3020 -1120 0 1 {name=l2624 lab=vss}
C {devices/lab_pin.sym} 3070 -1150 0 1 {name=l2625 lab=m0_123}
C {devices/lab_pin.sym} 3030 -1120 0 0 {name=l2626 lab=dh1}
C {devices/lab_pin.sym} 3070 -1090 0 1 {name=l2627 lab=m1_61}
C {devices/lab_pin.sym} 3070 -1120 0 1 {name=l2628 lab=vss}
C {devices/lab_pin.sym} 3120 -1150 0 1 {name=l2629 lab=m0_124}
C {devices/lab_pin.sym} 3080 -1120 0 0 {name=l2630 lab=dhn1}
C {devices/lab_pin.sym} 3120 -1090 0 1 {name=l2631 lab=m1_62}
C {devices/lab_pin.sym} 3120 -1120 0 1 {name=l2632 lab=vss}
C {devices/lab_pin.sym} 3170 -1150 0 1 {name=l2633 lab=m0_125}
C {devices/lab_pin.sym} 3130 -1120 0 0 {name=l2634 lab=dh1}
C {devices/lab_pin.sym} 3170 -1090 0 1 {name=l2635 lab=m1_62}
C {devices/lab_pin.sym} 3170 -1120 0 1 {name=l2636 lab=vss}
C {devices/lab_pin.sym} 3220 -1150 0 1 {name=l2637 lab=m0_126}
C {devices/lab_pin.sym} 3180 -1120 0 0 {name=l2638 lab=dhn1}
C {devices/lab_pin.sym} 3220 -1090 0 1 {name=l2639 lab=m1_63}
C {devices/lab_pin.sym} 3220 -1120 0 1 {name=l2640 lab=vss}
C {devices/lab_pin.sym} 3270 -1150 0 1 {name=l2641 lab=m0_127}
C {devices/lab_pin.sym} 3230 -1120 0 0 {name=l2642 lab=dh1}
C {devices/lab_pin.sym} 3270 -1090 0 1 {name=l2643 lab=m1_63}
C {devices/lab_pin.sym} 3270 -1120 0 1 {name=l2644 lab=vss}
C {devices/lab_pin.sym} 120 -830 0 1 {name=l2645 lab=m1_0}
C {devices/lab_pin.sym} 80 -800 0 0 {name=l2646 lab=dhn2}
C {devices/lab_pin.sym} 120 -770 0 1 {name=l2647 lab=m2_0}
C {devices/lab_pin.sym} 120 -800 0 1 {name=l2648 lab=vss}
C {devices/lab_pin.sym} 170 -830 0 1 {name=l2649 lab=m1_1}
C {devices/lab_pin.sym} 130 -800 0 0 {name=l2650 lab=dh2}
C {devices/lab_pin.sym} 170 -770 0 1 {name=l2651 lab=m2_0}
C {devices/lab_pin.sym} 170 -800 0 1 {name=l2652 lab=vss}
C {devices/lab_pin.sym} 220 -830 0 1 {name=l2653 lab=m1_2}
C {devices/lab_pin.sym} 180 -800 0 0 {name=l2654 lab=dhn2}
C {devices/lab_pin.sym} 220 -770 0 1 {name=l2655 lab=m2_1}
C {devices/lab_pin.sym} 220 -800 0 1 {name=l2656 lab=vss}
C {devices/lab_pin.sym} 270 -830 0 1 {name=l2657 lab=m1_3}
C {devices/lab_pin.sym} 230 -800 0 0 {name=l2658 lab=dh2}
C {devices/lab_pin.sym} 270 -770 0 1 {name=l2659 lab=m2_1}
C {devices/lab_pin.sym} 270 -800 0 1 {name=l2660 lab=vss}
C {devices/lab_pin.sym} 320 -830 0 1 {name=l2661 lab=m1_4}
C {devices/lab_pin.sym} 280 -800 0 0 {name=l2662 lab=dhn2}
C {devices/lab_pin.sym} 320 -770 0 1 {name=l2663 lab=m2_2}
C {devices/lab_pin.sym} 320 -800 0 1 {name=l2664 lab=vss}
C {devices/lab_pin.sym} 370 -830 0 1 {name=l2665 lab=m1_5}
C {devices/lab_pin.sym} 330 -800 0 0 {name=l2666 lab=dh2}
C {devices/lab_pin.sym} 370 -770 0 1 {name=l2667 lab=m2_2}
C {devices/lab_pin.sym} 370 -800 0 1 {name=l2668 lab=vss}
C {devices/lab_pin.sym} 420 -830 0 1 {name=l2669 lab=m1_6}
C {devices/lab_pin.sym} 380 -800 0 0 {name=l2670 lab=dhn2}
C {devices/lab_pin.sym} 420 -770 0 1 {name=l2671 lab=m2_3}
C {devices/lab_pin.sym} 420 -800 0 1 {name=l2672 lab=vss}
C {devices/lab_pin.sym} 470 -830 0 1 {name=l2673 lab=m1_7}
C {devices/lab_pin.sym} 430 -800 0 0 {name=l2674 lab=dh2}
C {devices/lab_pin.sym} 470 -770 0 1 {name=l2675 lab=m2_3}
C {devices/lab_pin.sym} 470 -800 0 1 {name=l2676 lab=vss}
C {devices/lab_pin.sym} 520 -830 0 1 {name=l2677 lab=m1_8}
C {devices/lab_pin.sym} 480 -800 0 0 {name=l2678 lab=dhn2}
C {devices/lab_pin.sym} 520 -770 0 1 {name=l2679 lab=m2_4}
C {devices/lab_pin.sym} 520 -800 0 1 {name=l2680 lab=vss}
C {devices/lab_pin.sym} 570 -830 0 1 {name=l2681 lab=m1_9}
C {devices/lab_pin.sym} 530 -800 0 0 {name=l2682 lab=dh2}
C {devices/lab_pin.sym} 570 -770 0 1 {name=l2683 lab=m2_4}
C {devices/lab_pin.sym} 570 -800 0 1 {name=l2684 lab=vss}
C {devices/lab_pin.sym} 620 -830 0 1 {name=l2685 lab=m1_10}
C {devices/lab_pin.sym} 580 -800 0 0 {name=l2686 lab=dhn2}
C {devices/lab_pin.sym} 620 -770 0 1 {name=l2687 lab=m2_5}
C {devices/lab_pin.sym} 620 -800 0 1 {name=l2688 lab=vss}
C {devices/lab_pin.sym} 670 -830 0 1 {name=l2689 lab=m1_11}
C {devices/lab_pin.sym} 630 -800 0 0 {name=l2690 lab=dh2}
C {devices/lab_pin.sym} 670 -770 0 1 {name=l2691 lab=m2_5}
C {devices/lab_pin.sym} 670 -800 0 1 {name=l2692 lab=vss}
C {devices/lab_pin.sym} 720 -830 0 1 {name=l2693 lab=m1_12}
C {devices/lab_pin.sym} 680 -800 0 0 {name=l2694 lab=dhn2}
C {devices/lab_pin.sym} 720 -770 0 1 {name=l2695 lab=m2_6}
C {devices/lab_pin.sym} 720 -800 0 1 {name=l2696 lab=vss}
C {devices/lab_pin.sym} 770 -830 0 1 {name=l2697 lab=m1_13}
C {devices/lab_pin.sym} 730 -800 0 0 {name=l2698 lab=dh2}
C {devices/lab_pin.sym} 770 -770 0 1 {name=l2699 lab=m2_6}
C {devices/lab_pin.sym} 770 -800 0 1 {name=l2700 lab=vss}
C {devices/lab_pin.sym} 820 -830 0 1 {name=l2701 lab=m1_14}
C {devices/lab_pin.sym} 780 -800 0 0 {name=l2702 lab=dhn2}
C {devices/lab_pin.sym} 820 -770 0 1 {name=l2703 lab=m2_7}
C {devices/lab_pin.sym} 820 -800 0 1 {name=l2704 lab=vss}
C {devices/lab_pin.sym} 870 -830 0 1 {name=l2705 lab=m1_15}
C {devices/lab_pin.sym} 830 -800 0 0 {name=l2706 lab=dh2}
C {devices/lab_pin.sym} 870 -770 0 1 {name=l2707 lab=m2_7}
C {devices/lab_pin.sym} 870 -800 0 1 {name=l2708 lab=vss}
C {devices/lab_pin.sym} 920 -830 0 1 {name=l2709 lab=m1_16}
C {devices/lab_pin.sym} 880 -800 0 0 {name=l2710 lab=dhn2}
C {devices/lab_pin.sym} 920 -770 0 1 {name=l2711 lab=m2_8}
C {devices/lab_pin.sym} 920 -800 0 1 {name=l2712 lab=vss}
C {devices/lab_pin.sym} 970 -830 0 1 {name=l2713 lab=m1_17}
C {devices/lab_pin.sym} 930 -800 0 0 {name=l2714 lab=dh2}
C {devices/lab_pin.sym} 970 -770 0 1 {name=l2715 lab=m2_8}
C {devices/lab_pin.sym} 970 -800 0 1 {name=l2716 lab=vss}
C {devices/lab_pin.sym} 1020 -830 0 1 {name=l2717 lab=m1_18}
C {devices/lab_pin.sym} 980 -800 0 0 {name=l2718 lab=dhn2}
C {devices/lab_pin.sym} 1020 -770 0 1 {name=l2719 lab=m2_9}
C {devices/lab_pin.sym} 1020 -800 0 1 {name=l2720 lab=vss}
C {devices/lab_pin.sym} 1070 -830 0 1 {name=l2721 lab=m1_19}
C {devices/lab_pin.sym} 1030 -800 0 0 {name=l2722 lab=dh2}
C {devices/lab_pin.sym} 1070 -770 0 1 {name=l2723 lab=m2_9}
C {devices/lab_pin.sym} 1070 -800 0 1 {name=l2724 lab=vss}
C {devices/lab_pin.sym} 1120 -830 0 1 {name=l2725 lab=m1_20}
C {devices/lab_pin.sym} 1080 -800 0 0 {name=l2726 lab=dhn2}
C {devices/lab_pin.sym} 1120 -770 0 1 {name=l2727 lab=m2_10}
C {devices/lab_pin.sym} 1120 -800 0 1 {name=l2728 lab=vss}
C {devices/lab_pin.sym} 1170 -830 0 1 {name=l2729 lab=m1_21}
C {devices/lab_pin.sym} 1130 -800 0 0 {name=l2730 lab=dh2}
C {devices/lab_pin.sym} 1170 -770 0 1 {name=l2731 lab=m2_10}
C {devices/lab_pin.sym} 1170 -800 0 1 {name=l2732 lab=vss}
C {devices/lab_pin.sym} 1220 -830 0 1 {name=l2733 lab=m1_22}
C {devices/lab_pin.sym} 1180 -800 0 0 {name=l2734 lab=dhn2}
C {devices/lab_pin.sym} 1220 -770 0 1 {name=l2735 lab=m2_11}
C {devices/lab_pin.sym} 1220 -800 0 1 {name=l2736 lab=vss}
C {devices/lab_pin.sym} 1270 -830 0 1 {name=l2737 lab=m1_23}
C {devices/lab_pin.sym} 1230 -800 0 0 {name=l2738 lab=dh2}
C {devices/lab_pin.sym} 1270 -770 0 1 {name=l2739 lab=m2_11}
C {devices/lab_pin.sym} 1270 -800 0 1 {name=l2740 lab=vss}
C {devices/lab_pin.sym} 1320 -830 0 1 {name=l2741 lab=m1_24}
C {devices/lab_pin.sym} 1280 -800 0 0 {name=l2742 lab=dhn2}
C {devices/lab_pin.sym} 1320 -770 0 1 {name=l2743 lab=m2_12}
C {devices/lab_pin.sym} 1320 -800 0 1 {name=l2744 lab=vss}
C {devices/lab_pin.sym} 1370 -830 0 1 {name=l2745 lab=m1_25}
C {devices/lab_pin.sym} 1330 -800 0 0 {name=l2746 lab=dh2}
C {devices/lab_pin.sym} 1370 -770 0 1 {name=l2747 lab=m2_12}
C {devices/lab_pin.sym} 1370 -800 0 1 {name=l2748 lab=vss}
C {devices/lab_pin.sym} 1420 -830 0 1 {name=l2749 lab=m1_26}
C {devices/lab_pin.sym} 1380 -800 0 0 {name=l2750 lab=dhn2}
C {devices/lab_pin.sym} 1420 -770 0 1 {name=l2751 lab=m2_13}
C {devices/lab_pin.sym} 1420 -800 0 1 {name=l2752 lab=vss}
C {devices/lab_pin.sym} 1470 -830 0 1 {name=l2753 lab=m1_27}
C {devices/lab_pin.sym} 1430 -800 0 0 {name=l2754 lab=dh2}
C {devices/lab_pin.sym} 1470 -770 0 1 {name=l2755 lab=m2_13}
C {devices/lab_pin.sym} 1470 -800 0 1 {name=l2756 lab=vss}
C {devices/lab_pin.sym} 1520 -830 0 1 {name=l2757 lab=m1_28}
C {devices/lab_pin.sym} 1480 -800 0 0 {name=l2758 lab=dhn2}
C {devices/lab_pin.sym} 1520 -770 0 1 {name=l2759 lab=m2_14}
C {devices/lab_pin.sym} 1520 -800 0 1 {name=l2760 lab=vss}
C {devices/lab_pin.sym} 1570 -830 0 1 {name=l2761 lab=m1_29}
C {devices/lab_pin.sym} 1530 -800 0 0 {name=l2762 lab=dh2}
C {devices/lab_pin.sym} 1570 -770 0 1 {name=l2763 lab=m2_14}
C {devices/lab_pin.sym} 1570 -800 0 1 {name=l2764 lab=vss}
C {devices/lab_pin.sym} 1620 -830 0 1 {name=l2765 lab=m1_30}
C {devices/lab_pin.sym} 1580 -800 0 0 {name=l2766 lab=dhn2}
C {devices/lab_pin.sym} 1620 -770 0 1 {name=l2767 lab=m2_15}
C {devices/lab_pin.sym} 1620 -800 0 1 {name=l2768 lab=vss}
C {devices/lab_pin.sym} 1670 -830 0 1 {name=l2769 lab=m1_31}
C {devices/lab_pin.sym} 1630 -800 0 0 {name=l2770 lab=dh2}
C {devices/lab_pin.sym} 1670 -770 0 1 {name=l2771 lab=m2_15}
C {devices/lab_pin.sym} 1670 -800 0 1 {name=l2772 lab=vss}
C {devices/lab_pin.sym} 1720 -830 0 1 {name=l2773 lab=m1_32}
C {devices/lab_pin.sym} 1680 -800 0 0 {name=l2774 lab=dhn2}
C {devices/lab_pin.sym} 1720 -770 0 1 {name=l2775 lab=m2_16}
C {devices/lab_pin.sym} 1720 -800 0 1 {name=l2776 lab=vss}
C {devices/lab_pin.sym} 1770 -830 0 1 {name=l2777 lab=m1_33}
C {devices/lab_pin.sym} 1730 -800 0 0 {name=l2778 lab=dh2}
C {devices/lab_pin.sym} 1770 -770 0 1 {name=l2779 lab=m2_16}
C {devices/lab_pin.sym} 1770 -800 0 1 {name=l2780 lab=vss}
C {devices/lab_pin.sym} 1820 -830 0 1 {name=l2781 lab=m1_34}
C {devices/lab_pin.sym} 1780 -800 0 0 {name=l2782 lab=dhn2}
C {devices/lab_pin.sym} 1820 -770 0 1 {name=l2783 lab=m2_17}
C {devices/lab_pin.sym} 1820 -800 0 1 {name=l2784 lab=vss}
C {devices/lab_pin.sym} 1870 -830 0 1 {name=l2785 lab=m1_35}
C {devices/lab_pin.sym} 1830 -800 0 0 {name=l2786 lab=dh2}
C {devices/lab_pin.sym} 1870 -770 0 1 {name=l2787 lab=m2_17}
C {devices/lab_pin.sym} 1870 -800 0 1 {name=l2788 lab=vss}
C {devices/lab_pin.sym} 1920 -830 0 1 {name=l2789 lab=m1_36}
C {devices/lab_pin.sym} 1880 -800 0 0 {name=l2790 lab=dhn2}
C {devices/lab_pin.sym} 1920 -770 0 1 {name=l2791 lab=m2_18}
C {devices/lab_pin.sym} 1920 -800 0 1 {name=l2792 lab=vss}
C {devices/lab_pin.sym} 1970 -830 0 1 {name=l2793 lab=m1_37}
C {devices/lab_pin.sym} 1930 -800 0 0 {name=l2794 lab=dh2}
C {devices/lab_pin.sym} 1970 -770 0 1 {name=l2795 lab=m2_18}
C {devices/lab_pin.sym} 1970 -800 0 1 {name=l2796 lab=vss}
C {devices/lab_pin.sym} 2020 -830 0 1 {name=l2797 lab=m1_38}
C {devices/lab_pin.sym} 1980 -800 0 0 {name=l2798 lab=dhn2}
C {devices/lab_pin.sym} 2020 -770 0 1 {name=l2799 lab=m2_19}
C {devices/lab_pin.sym} 2020 -800 0 1 {name=l2800 lab=vss}
C {devices/lab_pin.sym} 2070 -830 0 1 {name=l2801 lab=m1_39}
C {devices/lab_pin.sym} 2030 -800 0 0 {name=l2802 lab=dh2}
C {devices/lab_pin.sym} 2070 -770 0 1 {name=l2803 lab=m2_19}
C {devices/lab_pin.sym} 2070 -800 0 1 {name=l2804 lab=vss}
C {devices/lab_pin.sym} 2120 -830 0 1 {name=l2805 lab=m1_40}
C {devices/lab_pin.sym} 2080 -800 0 0 {name=l2806 lab=dhn2}
C {devices/lab_pin.sym} 2120 -770 0 1 {name=l2807 lab=m2_20}
C {devices/lab_pin.sym} 2120 -800 0 1 {name=l2808 lab=vss}
C {devices/lab_pin.sym} 2170 -830 0 1 {name=l2809 lab=m1_41}
C {devices/lab_pin.sym} 2130 -800 0 0 {name=l2810 lab=dh2}
C {devices/lab_pin.sym} 2170 -770 0 1 {name=l2811 lab=m2_20}
C {devices/lab_pin.sym} 2170 -800 0 1 {name=l2812 lab=vss}
C {devices/lab_pin.sym} 2220 -830 0 1 {name=l2813 lab=m1_42}
C {devices/lab_pin.sym} 2180 -800 0 0 {name=l2814 lab=dhn2}
C {devices/lab_pin.sym} 2220 -770 0 1 {name=l2815 lab=m2_21}
C {devices/lab_pin.sym} 2220 -800 0 1 {name=l2816 lab=vss}
C {devices/lab_pin.sym} 2270 -830 0 1 {name=l2817 lab=m1_43}
C {devices/lab_pin.sym} 2230 -800 0 0 {name=l2818 lab=dh2}
C {devices/lab_pin.sym} 2270 -770 0 1 {name=l2819 lab=m2_21}
C {devices/lab_pin.sym} 2270 -800 0 1 {name=l2820 lab=vss}
C {devices/lab_pin.sym} 2320 -830 0 1 {name=l2821 lab=m1_44}
C {devices/lab_pin.sym} 2280 -800 0 0 {name=l2822 lab=dhn2}
C {devices/lab_pin.sym} 2320 -770 0 1 {name=l2823 lab=m2_22}
C {devices/lab_pin.sym} 2320 -800 0 1 {name=l2824 lab=vss}
C {devices/lab_pin.sym} 2370 -830 0 1 {name=l2825 lab=m1_45}
C {devices/lab_pin.sym} 2330 -800 0 0 {name=l2826 lab=dh2}
C {devices/lab_pin.sym} 2370 -770 0 1 {name=l2827 lab=m2_22}
C {devices/lab_pin.sym} 2370 -800 0 1 {name=l2828 lab=vss}
C {devices/lab_pin.sym} 2420 -830 0 1 {name=l2829 lab=m1_46}
C {devices/lab_pin.sym} 2380 -800 0 0 {name=l2830 lab=dhn2}
C {devices/lab_pin.sym} 2420 -770 0 1 {name=l2831 lab=m2_23}
C {devices/lab_pin.sym} 2420 -800 0 1 {name=l2832 lab=vss}
C {devices/lab_pin.sym} 2470 -830 0 1 {name=l2833 lab=m1_47}
C {devices/lab_pin.sym} 2430 -800 0 0 {name=l2834 lab=dh2}
C {devices/lab_pin.sym} 2470 -770 0 1 {name=l2835 lab=m2_23}
C {devices/lab_pin.sym} 2470 -800 0 1 {name=l2836 lab=vss}
C {devices/lab_pin.sym} 2520 -830 0 1 {name=l2837 lab=m1_48}
C {devices/lab_pin.sym} 2480 -800 0 0 {name=l2838 lab=dhn2}
C {devices/lab_pin.sym} 2520 -770 0 1 {name=l2839 lab=m2_24}
C {devices/lab_pin.sym} 2520 -800 0 1 {name=l2840 lab=vss}
C {devices/lab_pin.sym} 2570 -830 0 1 {name=l2841 lab=m1_49}
C {devices/lab_pin.sym} 2530 -800 0 0 {name=l2842 lab=dh2}
C {devices/lab_pin.sym} 2570 -770 0 1 {name=l2843 lab=m2_24}
C {devices/lab_pin.sym} 2570 -800 0 1 {name=l2844 lab=vss}
C {devices/lab_pin.sym} 2620 -830 0 1 {name=l2845 lab=m1_50}
C {devices/lab_pin.sym} 2580 -800 0 0 {name=l2846 lab=dhn2}
C {devices/lab_pin.sym} 2620 -770 0 1 {name=l2847 lab=m2_25}
C {devices/lab_pin.sym} 2620 -800 0 1 {name=l2848 lab=vss}
C {devices/lab_pin.sym} 2670 -830 0 1 {name=l2849 lab=m1_51}
C {devices/lab_pin.sym} 2630 -800 0 0 {name=l2850 lab=dh2}
C {devices/lab_pin.sym} 2670 -770 0 1 {name=l2851 lab=m2_25}
C {devices/lab_pin.sym} 2670 -800 0 1 {name=l2852 lab=vss}
C {devices/lab_pin.sym} 2720 -830 0 1 {name=l2853 lab=m1_52}
C {devices/lab_pin.sym} 2680 -800 0 0 {name=l2854 lab=dhn2}
C {devices/lab_pin.sym} 2720 -770 0 1 {name=l2855 lab=m2_26}
C {devices/lab_pin.sym} 2720 -800 0 1 {name=l2856 lab=vss}
C {devices/lab_pin.sym} 2770 -830 0 1 {name=l2857 lab=m1_53}
C {devices/lab_pin.sym} 2730 -800 0 0 {name=l2858 lab=dh2}
C {devices/lab_pin.sym} 2770 -770 0 1 {name=l2859 lab=m2_26}
C {devices/lab_pin.sym} 2770 -800 0 1 {name=l2860 lab=vss}
C {devices/lab_pin.sym} 2820 -830 0 1 {name=l2861 lab=m1_54}
C {devices/lab_pin.sym} 2780 -800 0 0 {name=l2862 lab=dhn2}
C {devices/lab_pin.sym} 2820 -770 0 1 {name=l2863 lab=m2_27}
C {devices/lab_pin.sym} 2820 -800 0 1 {name=l2864 lab=vss}
C {devices/lab_pin.sym} 2870 -830 0 1 {name=l2865 lab=m1_55}
C {devices/lab_pin.sym} 2830 -800 0 0 {name=l2866 lab=dh2}
C {devices/lab_pin.sym} 2870 -770 0 1 {name=l2867 lab=m2_27}
C {devices/lab_pin.sym} 2870 -800 0 1 {name=l2868 lab=vss}
C {devices/lab_pin.sym} 2920 -830 0 1 {name=l2869 lab=m1_56}
C {devices/lab_pin.sym} 2880 -800 0 0 {name=l2870 lab=dhn2}
C {devices/lab_pin.sym} 2920 -770 0 1 {name=l2871 lab=m2_28}
C {devices/lab_pin.sym} 2920 -800 0 1 {name=l2872 lab=vss}
C {devices/lab_pin.sym} 2970 -830 0 1 {name=l2873 lab=m1_57}
C {devices/lab_pin.sym} 2930 -800 0 0 {name=l2874 lab=dh2}
C {devices/lab_pin.sym} 2970 -770 0 1 {name=l2875 lab=m2_28}
C {devices/lab_pin.sym} 2970 -800 0 1 {name=l2876 lab=vss}
C {devices/lab_pin.sym} 3020 -830 0 1 {name=l2877 lab=m1_58}
C {devices/lab_pin.sym} 2980 -800 0 0 {name=l2878 lab=dhn2}
C {devices/lab_pin.sym} 3020 -770 0 1 {name=l2879 lab=m2_29}
C {devices/lab_pin.sym} 3020 -800 0 1 {name=l2880 lab=vss}
C {devices/lab_pin.sym} 3070 -830 0 1 {name=l2881 lab=m1_59}
C {devices/lab_pin.sym} 3030 -800 0 0 {name=l2882 lab=dh2}
C {devices/lab_pin.sym} 3070 -770 0 1 {name=l2883 lab=m2_29}
C {devices/lab_pin.sym} 3070 -800 0 1 {name=l2884 lab=vss}
C {devices/lab_pin.sym} 3120 -830 0 1 {name=l2885 lab=m1_60}
C {devices/lab_pin.sym} 3080 -800 0 0 {name=l2886 lab=dhn2}
C {devices/lab_pin.sym} 3120 -770 0 1 {name=l2887 lab=m2_30}
C {devices/lab_pin.sym} 3120 -800 0 1 {name=l2888 lab=vss}
C {devices/lab_pin.sym} 3170 -830 0 1 {name=l2889 lab=m1_61}
C {devices/lab_pin.sym} 3130 -800 0 0 {name=l2890 lab=dh2}
C {devices/lab_pin.sym} 3170 -770 0 1 {name=l2891 lab=m2_30}
C {devices/lab_pin.sym} 3170 -800 0 1 {name=l2892 lab=vss}
C {devices/lab_pin.sym} 3220 -830 0 1 {name=l2893 lab=m1_62}
C {devices/lab_pin.sym} 3180 -800 0 0 {name=l2894 lab=dhn2}
C {devices/lab_pin.sym} 3220 -770 0 1 {name=l2895 lab=m2_31}
C {devices/lab_pin.sym} 3220 -800 0 1 {name=l2896 lab=vss}
C {devices/lab_pin.sym} 3270 -830 0 1 {name=l2897 lab=m1_63}
C {devices/lab_pin.sym} 3230 -800 0 0 {name=l2898 lab=dh2}
C {devices/lab_pin.sym} 3270 -770 0 1 {name=l2899 lab=m2_31}
C {devices/lab_pin.sym} 3270 -800 0 1 {name=l2900 lab=vss}
C {devices/lab_pin.sym} 120 -430 0 1 {name=l2901 lab=m2_0}
C {devices/lab_pin.sym} 80 -400 0 0 {name=l2902 lab=dhn3}
C {devices/lab_pin.sym} 120 -370 0 1 {name=l2903 lab=m3_0}
C {devices/lab_pin.sym} 120 -400 0 1 {name=l2904 lab=vss}
C {devices/lab_pin.sym} 170 -430 0 1 {name=l2905 lab=m2_1}
C {devices/lab_pin.sym} 130 -400 0 0 {name=l2906 lab=dh3}
C {devices/lab_pin.sym} 170 -370 0 1 {name=l2907 lab=m3_0}
C {devices/lab_pin.sym} 170 -400 0 1 {name=l2908 lab=vss}
C {devices/lab_pin.sym} 220 -430 0 1 {name=l2909 lab=m2_2}
C {devices/lab_pin.sym} 180 -400 0 0 {name=l2910 lab=dhn3}
C {devices/lab_pin.sym} 220 -370 0 1 {name=l2911 lab=m3_1}
C {devices/lab_pin.sym} 220 -400 0 1 {name=l2912 lab=vss}
C {devices/lab_pin.sym} 270 -430 0 1 {name=l2913 lab=m2_3}
C {devices/lab_pin.sym} 230 -400 0 0 {name=l2914 lab=dh3}
C {devices/lab_pin.sym} 270 -370 0 1 {name=l2915 lab=m3_1}
C {devices/lab_pin.sym} 270 -400 0 1 {name=l2916 lab=vss}
C {devices/lab_pin.sym} 320 -430 0 1 {name=l2917 lab=m2_4}
C {devices/lab_pin.sym} 280 -400 0 0 {name=l2918 lab=dhn3}
C {devices/lab_pin.sym} 320 -370 0 1 {name=l2919 lab=m3_2}
C {devices/lab_pin.sym} 320 -400 0 1 {name=l2920 lab=vss}
C {devices/lab_pin.sym} 370 -430 0 1 {name=l2921 lab=m2_5}
C {devices/lab_pin.sym} 330 -400 0 0 {name=l2922 lab=dh3}
C {devices/lab_pin.sym} 370 -370 0 1 {name=l2923 lab=m3_2}
C {devices/lab_pin.sym} 370 -400 0 1 {name=l2924 lab=vss}
C {devices/lab_pin.sym} 420 -430 0 1 {name=l2925 lab=m2_6}
C {devices/lab_pin.sym} 380 -400 0 0 {name=l2926 lab=dhn3}
C {devices/lab_pin.sym} 420 -370 0 1 {name=l2927 lab=m3_3}
C {devices/lab_pin.sym} 420 -400 0 1 {name=l2928 lab=vss}
C {devices/lab_pin.sym} 470 -430 0 1 {name=l2929 lab=m2_7}
C {devices/lab_pin.sym} 430 -400 0 0 {name=l2930 lab=dh3}
C {devices/lab_pin.sym} 470 -370 0 1 {name=l2931 lab=m3_3}
C {devices/lab_pin.sym} 470 -400 0 1 {name=l2932 lab=vss}
C {devices/lab_pin.sym} 520 -430 0 1 {name=l2933 lab=m2_8}
C {devices/lab_pin.sym} 480 -400 0 0 {name=l2934 lab=dhn3}
C {devices/lab_pin.sym} 520 -370 0 1 {name=l2935 lab=m3_4}
C {devices/lab_pin.sym} 520 -400 0 1 {name=l2936 lab=vss}
C {devices/lab_pin.sym} 570 -430 0 1 {name=l2937 lab=m2_9}
C {devices/lab_pin.sym} 530 -400 0 0 {name=l2938 lab=dh3}
C {devices/lab_pin.sym} 570 -370 0 1 {name=l2939 lab=m3_4}
C {devices/lab_pin.sym} 570 -400 0 1 {name=l2940 lab=vss}
C {devices/lab_pin.sym} 620 -430 0 1 {name=l2941 lab=m2_10}
C {devices/lab_pin.sym} 580 -400 0 0 {name=l2942 lab=dhn3}
C {devices/lab_pin.sym} 620 -370 0 1 {name=l2943 lab=m3_5}
C {devices/lab_pin.sym} 620 -400 0 1 {name=l2944 lab=vss}
C {devices/lab_pin.sym} 670 -430 0 1 {name=l2945 lab=m2_11}
C {devices/lab_pin.sym} 630 -400 0 0 {name=l2946 lab=dh3}
C {devices/lab_pin.sym} 670 -370 0 1 {name=l2947 lab=m3_5}
C {devices/lab_pin.sym} 670 -400 0 1 {name=l2948 lab=vss}
C {devices/lab_pin.sym} 720 -430 0 1 {name=l2949 lab=m2_12}
C {devices/lab_pin.sym} 680 -400 0 0 {name=l2950 lab=dhn3}
C {devices/lab_pin.sym} 720 -370 0 1 {name=l2951 lab=m3_6}
C {devices/lab_pin.sym} 720 -400 0 1 {name=l2952 lab=vss}
C {devices/lab_pin.sym} 770 -430 0 1 {name=l2953 lab=m2_13}
C {devices/lab_pin.sym} 730 -400 0 0 {name=l2954 lab=dh3}
C {devices/lab_pin.sym} 770 -370 0 1 {name=l2955 lab=m3_6}
C {devices/lab_pin.sym} 770 -400 0 1 {name=l2956 lab=vss}
C {devices/lab_pin.sym} 820 -430 0 1 {name=l2957 lab=m2_14}
C {devices/lab_pin.sym} 780 -400 0 0 {name=l2958 lab=dhn3}
C {devices/lab_pin.sym} 820 -370 0 1 {name=l2959 lab=m3_7}
C {devices/lab_pin.sym} 820 -400 0 1 {name=l2960 lab=vss}
C {devices/lab_pin.sym} 870 -430 0 1 {name=l2961 lab=m2_15}
C {devices/lab_pin.sym} 830 -400 0 0 {name=l2962 lab=dh3}
C {devices/lab_pin.sym} 870 -370 0 1 {name=l2963 lab=m3_7}
C {devices/lab_pin.sym} 870 -400 0 1 {name=l2964 lab=vss}
C {devices/lab_pin.sym} 920 -430 0 1 {name=l2965 lab=m2_16}
C {devices/lab_pin.sym} 880 -400 0 0 {name=l2966 lab=dhn3}
C {devices/lab_pin.sym} 920 -370 0 1 {name=l2967 lab=m3_8}
C {devices/lab_pin.sym} 920 -400 0 1 {name=l2968 lab=vss}
C {devices/lab_pin.sym} 970 -430 0 1 {name=l2969 lab=m2_17}
C {devices/lab_pin.sym} 930 -400 0 0 {name=l2970 lab=dh3}
C {devices/lab_pin.sym} 970 -370 0 1 {name=l2971 lab=m3_8}
C {devices/lab_pin.sym} 970 -400 0 1 {name=l2972 lab=vss}
C {devices/lab_pin.sym} 1020 -430 0 1 {name=l2973 lab=m2_18}
C {devices/lab_pin.sym} 980 -400 0 0 {name=l2974 lab=dhn3}
C {devices/lab_pin.sym} 1020 -370 0 1 {name=l2975 lab=m3_9}
C {devices/lab_pin.sym} 1020 -400 0 1 {name=l2976 lab=vss}
C {devices/lab_pin.sym} 1070 -430 0 1 {name=l2977 lab=m2_19}
C {devices/lab_pin.sym} 1030 -400 0 0 {name=l2978 lab=dh3}
C {devices/lab_pin.sym} 1070 -370 0 1 {name=l2979 lab=m3_9}
C {devices/lab_pin.sym} 1070 -400 0 1 {name=l2980 lab=vss}
C {devices/lab_pin.sym} 1120 -430 0 1 {name=l2981 lab=m2_20}
C {devices/lab_pin.sym} 1080 -400 0 0 {name=l2982 lab=dhn3}
C {devices/lab_pin.sym} 1120 -370 0 1 {name=l2983 lab=m3_10}
C {devices/lab_pin.sym} 1120 -400 0 1 {name=l2984 lab=vss}
C {devices/lab_pin.sym} 1170 -430 0 1 {name=l2985 lab=m2_21}
C {devices/lab_pin.sym} 1130 -400 0 0 {name=l2986 lab=dh3}
C {devices/lab_pin.sym} 1170 -370 0 1 {name=l2987 lab=m3_10}
C {devices/lab_pin.sym} 1170 -400 0 1 {name=l2988 lab=vss}
C {devices/lab_pin.sym} 1220 -430 0 1 {name=l2989 lab=m2_22}
C {devices/lab_pin.sym} 1180 -400 0 0 {name=l2990 lab=dhn3}
C {devices/lab_pin.sym} 1220 -370 0 1 {name=l2991 lab=m3_11}
C {devices/lab_pin.sym} 1220 -400 0 1 {name=l2992 lab=vss}
C {devices/lab_pin.sym} 1270 -430 0 1 {name=l2993 lab=m2_23}
C {devices/lab_pin.sym} 1230 -400 0 0 {name=l2994 lab=dh3}
C {devices/lab_pin.sym} 1270 -370 0 1 {name=l2995 lab=m3_11}
C {devices/lab_pin.sym} 1270 -400 0 1 {name=l2996 lab=vss}
C {devices/lab_pin.sym} 1320 -430 0 1 {name=l2997 lab=m2_24}
C {devices/lab_pin.sym} 1280 -400 0 0 {name=l2998 lab=dhn3}
C {devices/lab_pin.sym} 1320 -370 0 1 {name=l2999 lab=m3_12}
C {devices/lab_pin.sym} 1320 -400 0 1 {name=l3000 lab=vss}
C {devices/lab_pin.sym} 1370 -430 0 1 {name=l3001 lab=m2_25}
C {devices/lab_pin.sym} 1330 -400 0 0 {name=l3002 lab=dh3}
C {devices/lab_pin.sym} 1370 -370 0 1 {name=l3003 lab=m3_12}
C {devices/lab_pin.sym} 1370 -400 0 1 {name=l3004 lab=vss}
C {devices/lab_pin.sym} 1420 -430 0 1 {name=l3005 lab=m2_26}
C {devices/lab_pin.sym} 1380 -400 0 0 {name=l3006 lab=dhn3}
C {devices/lab_pin.sym} 1420 -370 0 1 {name=l3007 lab=m3_13}
C {devices/lab_pin.sym} 1420 -400 0 1 {name=l3008 lab=vss}
C {devices/lab_pin.sym} 1470 -430 0 1 {name=l3009 lab=m2_27}
C {devices/lab_pin.sym} 1430 -400 0 0 {name=l3010 lab=dh3}
C {devices/lab_pin.sym} 1470 -370 0 1 {name=l3011 lab=m3_13}
C {devices/lab_pin.sym} 1470 -400 0 1 {name=l3012 lab=vss}
C {devices/lab_pin.sym} 1520 -430 0 1 {name=l3013 lab=m2_28}
C {devices/lab_pin.sym} 1480 -400 0 0 {name=l3014 lab=dhn3}
C {devices/lab_pin.sym} 1520 -370 0 1 {name=l3015 lab=m3_14}
C {devices/lab_pin.sym} 1520 -400 0 1 {name=l3016 lab=vss}
C {devices/lab_pin.sym} 1570 -430 0 1 {name=l3017 lab=m2_29}
C {devices/lab_pin.sym} 1530 -400 0 0 {name=l3018 lab=dh3}
C {devices/lab_pin.sym} 1570 -370 0 1 {name=l3019 lab=m3_14}
C {devices/lab_pin.sym} 1570 -400 0 1 {name=l3020 lab=vss}
C {devices/lab_pin.sym} 1620 -430 0 1 {name=l3021 lab=m2_30}
C {devices/lab_pin.sym} 1580 -400 0 0 {name=l3022 lab=dhn3}
C {devices/lab_pin.sym} 1620 -370 0 1 {name=l3023 lab=m3_15}
C {devices/lab_pin.sym} 1620 -400 0 1 {name=l3024 lab=vss}
C {devices/lab_pin.sym} 1670 -430 0 1 {name=l3025 lab=m2_31}
C {devices/lab_pin.sym} 1630 -400 0 0 {name=l3026 lab=dh3}
C {devices/lab_pin.sym} 1670 -370 0 1 {name=l3027 lab=m3_15}
C {devices/lab_pin.sym} 1670 -400 0 1 {name=l3028 lab=vss}
C {devices/lab_pin.sym} 120 -30 0 1 {name=l3029 lab=m3_0}
C {devices/lab_pin.sym} 80 0 0 0 {name=l3030 lab=dhn4}
C {devices/lab_pin.sym} 120 30 0 1 {name=l3031 lab=m4_0}
C {devices/lab_pin.sym} 120 0 0 1 {name=l3032 lab=vss}
C {devices/lab_pin.sym} 170 -30 0 1 {name=l3033 lab=m3_1}
C {devices/lab_pin.sym} 130 0 0 0 {name=l3034 lab=dh4}
C {devices/lab_pin.sym} 170 30 0 1 {name=l3035 lab=m4_0}
C {devices/lab_pin.sym} 170 0 0 1 {name=l3036 lab=vss}
C {devices/lab_pin.sym} 220 -30 0 1 {name=l3037 lab=m3_2}
C {devices/lab_pin.sym} 180 0 0 0 {name=l3038 lab=dhn4}
C {devices/lab_pin.sym} 220 30 0 1 {name=l3039 lab=m4_1}
C {devices/lab_pin.sym} 220 0 0 1 {name=l3040 lab=vss}
C {devices/lab_pin.sym} 270 -30 0 1 {name=l3041 lab=m3_3}
C {devices/lab_pin.sym} 230 0 0 0 {name=l3042 lab=dh4}
C {devices/lab_pin.sym} 270 30 0 1 {name=l3043 lab=m4_1}
C {devices/lab_pin.sym} 270 0 0 1 {name=l3044 lab=vss}
C {devices/lab_pin.sym} 320 -30 0 1 {name=l3045 lab=m3_4}
C {devices/lab_pin.sym} 280 0 0 0 {name=l3046 lab=dhn4}
C {devices/lab_pin.sym} 320 30 0 1 {name=l3047 lab=m4_2}
C {devices/lab_pin.sym} 320 0 0 1 {name=l3048 lab=vss}
C {devices/lab_pin.sym} 370 -30 0 1 {name=l3049 lab=m3_5}
C {devices/lab_pin.sym} 330 0 0 0 {name=l3050 lab=dh4}
C {devices/lab_pin.sym} 370 30 0 1 {name=l3051 lab=m4_2}
C {devices/lab_pin.sym} 370 0 0 1 {name=l3052 lab=vss}
C {devices/lab_pin.sym} 420 -30 0 1 {name=l3053 lab=m3_6}
C {devices/lab_pin.sym} 380 0 0 0 {name=l3054 lab=dhn4}
C {devices/lab_pin.sym} 420 30 0 1 {name=l3055 lab=m4_3}
C {devices/lab_pin.sym} 420 0 0 1 {name=l3056 lab=vss}
C {devices/lab_pin.sym} 470 -30 0 1 {name=l3057 lab=m3_7}
C {devices/lab_pin.sym} 430 0 0 0 {name=l3058 lab=dh4}
C {devices/lab_pin.sym} 470 30 0 1 {name=l3059 lab=m4_3}
C {devices/lab_pin.sym} 470 0 0 1 {name=l3060 lab=vss}
C {devices/lab_pin.sym} 520 -30 0 1 {name=l3061 lab=m3_8}
C {devices/lab_pin.sym} 480 0 0 0 {name=l3062 lab=dhn4}
C {devices/lab_pin.sym} 520 30 0 1 {name=l3063 lab=m4_4}
C {devices/lab_pin.sym} 520 0 0 1 {name=l3064 lab=vss}
C {devices/lab_pin.sym} 570 -30 0 1 {name=l3065 lab=m3_9}
C {devices/lab_pin.sym} 530 0 0 0 {name=l3066 lab=dh4}
C {devices/lab_pin.sym} 570 30 0 1 {name=l3067 lab=m4_4}
C {devices/lab_pin.sym} 570 0 0 1 {name=l3068 lab=vss}
C {devices/lab_pin.sym} 620 -30 0 1 {name=l3069 lab=m3_10}
C {devices/lab_pin.sym} 580 0 0 0 {name=l3070 lab=dhn4}
C {devices/lab_pin.sym} 620 30 0 1 {name=l3071 lab=m4_5}
C {devices/lab_pin.sym} 620 0 0 1 {name=l3072 lab=vss}
C {devices/lab_pin.sym} 670 -30 0 1 {name=l3073 lab=m3_11}
C {devices/lab_pin.sym} 630 0 0 0 {name=l3074 lab=dh4}
C {devices/lab_pin.sym} 670 30 0 1 {name=l3075 lab=m4_5}
C {devices/lab_pin.sym} 670 0 0 1 {name=l3076 lab=vss}
C {devices/lab_pin.sym} 720 -30 0 1 {name=l3077 lab=m3_12}
C {devices/lab_pin.sym} 680 0 0 0 {name=l3078 lab=dhn4}
C {devices/lab_pin.sym} 720 30 0 1 {name=l3079 lab=m4_6}
C {devices/lab_pin.sym} 720 0 0 1 {name=l3080 lab=vss}
C {devices/lab_pin.sym} 770 -30 0 1 {name=l3081 lab=m3_13}
C {devices/lab_pin.sym} 730 0 0 0 {name=l3082 lab=dh4}
C {devices/lab_pin.sym} 770 30 0 1 {name=l3083 lab=m4_6}
C {devices/lab_pin.sym} 770 0 0 1 {name=l3084 lab=vss}
C {devices/lab_pin.sym} 820 -30 0 1 {name=l3085 lab=m3_14}
C {devices/lab_pin.sym} 780 0 0 0 {name=l3086 lab=dhn4}
C {devices/lab_pin.sym} 820 30 0 1 {name=l3087 lab=m4_7}
C {devices/lab_pin.sym} 820 0 0 1 {name=l3088 lab=vss}
C {devices/lab_pin.sym} 870 -30 0 1 {name=l3089 lab=m3_15}
C {devices/lab_pin.sym} 830 0 0 0 {name=l3090 lab=dh4}
C {devices/lab_pin.sym} 870 30 0 1 {name=l3091 lab=m4_7}
C {devices/lab_pin.sym} 870 0 0 1 {name=l3092 lab=vss}
C {devices/lab_pin.sym} 120 370 0 1 {name=l3093 lab=m4_0}
C {devices/lab_pin.sym} 80 400 0 0 {name=l3094 lab=dhn5}
C {devices/lab_pin.sym} 120 430 0 1 {name=l3095 lab=m5_0}
C {devices/lab_pin.sym} 120 400 0 1 {name=l3096 lab=vss}
C {devices/lab_pin.sym} 170 370 0 1 {name=l3097 lab=m4_1}
C {devices/lab_pin.sym} 130 400 0 0 {name=l3098 lab=dh5}
C {devices/lab_pin.sym} 170 430 0 1 {name=l3099 lab=m5_0}
C {devices/lab_pin.sym} 170 400 0 1 {name=l3100 lab=vss}
C {devices/lab_pin.sym} 220 370 0 1 {name=l3101 lab=m4_2}
C {devices/lab_pin.sym} 180 400 0 0 {name=l3102 lab=dhn5}
C {devices/lab_pin.sym} 220 430 0 1 {name=l3103 lab=m5_1}
C {devices/lab_pin.sym} 220 400 0 1 {name=l3104 lab=vss}
C {devices/lab_pin.sym} 270 370 0 1 {name=l3105 lab=m4_3}
C {devices/lab_pin.sym} 230 400 0 0 {name=l3106 lab=dh5}
C {devices/lab_pin.sym} 270 430 0 1 {name=l3107 lab=m5_1}
C {devices/lab_pin.sym} 270 400 0 1 {name=l3108 lab=vss}
C {devices/lab_pin.sym} 320 370 0 1 {name=l3109 lab=m4_4}
C {devices/lab_pin.sym} 280 400 0 0 {name=l3110 lab=dhn5}
C {devices/lab_pin.sym} 320 430 0 1 {name=l3111 lab=m5_2}
C {devices/lab_pin.sym} 320 400 0 1 {name=l3112 lab=vss}
C {devices/lab_pin.sym} 370 370 0 1 {name=l3113 lab=m4_5}
C {devices/lab_pin.sym} 330 400 0 0 {name=l3114 lab=dh5}
C {devices/lab_pin.sym} 370 430 0 1 {name=l3115 lab=m5_2}
C {devices/lab_pin.sym} 370 400 0 1 {name=l3116 lab=vss}
C {devices/lab_pin.sym} 420 370 0 1 {name=l3117 lab=m4_6}
C {devices/lab_pin.sym} 380 400 0 0 {name=l3118 lab=dhn5}
C {devices/lab_pin.sym} 420 430 0 1 {name=l3119 lab=m5_3}
C {devices/lab_pin.sym} 420 400 0 1 {name=l3120 lab=vss}
C {devices/lab_pin.sym} 470 370 0 1 {name=l3121 lab=m4_7}
C {devices/lab_pin.sym} 430 400 0 0 {name=l3122 lab=dh5}
C {devices/lab_pin.sym} 470 430 0 1 {name=l3123 lab=m5_3}
C {devices/lab_pin.sym} 470 400 0 1 {name=l3124 lab=vss}
C {devices/lab_pin.sym} 120 770 0 1 {name=l3125 lab=m5_0}
C {devices/lab_pin.sym} 80 800 0 0 {name=l3126 lab=dhn6}
C {devices/lab_pin.sym} 120 830 0 1 {name=l3127 lab=m6_0}
C {devices/lab_pin.sym} 120 800 0 1 {name=l3128 lab=vss}
C {devices/lab_pin.sym} 170 770 0 1 {name=l3129 lab=m5_1}
C {devices/lab_pin.sym} 130 800 0 0 {name=l3130 lab=dh6}
C {devices/lab_pin.sym} 170 830 0 1 {name=l3131 lab=m6_0}
C {devices/lab_pin.sym} 170 800 0 1 {name=l3132 lab=vss}
C {devices/lab_pin.sym} 220 770 0 1 {name=l3133 lab=m5_2}
C {devices/lab_pin.sym} 180 800 0 0 {name=l3134 lab=dhn6}
C {devices/lab_pin.sym} 220 830 0 1 {name=l3135 lab=m6_1}
C {devices/lab_pin.sym} 220 800 0 1 {name=l3136 lab=vss}
C {devices/lab_pin.sym} 270 770 0 1 {name=l3137 lab=m5_3}
C {devices/lab_pin.sym} 230 800 0 0 {name=l3138 lab=dh6}
C {devices/lab_pin.sym} 270 830 0 1 {name=l3139 lab=m6_1}
C {devices/lab_pin.sym} 270 800 0 1 {name=l3140 lab=vss}
C {devices/lab_pin.sym} 120 1170 0 1 {name=l3141 lab=m6_0}
C {devices/lab_pin.sym} 80 1200 0 0 {name=l3142 lab=dhn7}
C {devices/lab_pin.sym} 120 1230 0 1 {name=l3143 lab=out}
C {devices/lab_pin.sym} 120 1200 0 1 {name=l3144 lab=vss}
C {devices/lab_pin.sym} 170 1170 0 1 {name=l3145 lab=m6_1}
C {devices/lab_pin.sym} 130 1200 0 0 {name=l3146 lab=dh7}
C {devices/lab_pin.sym} 170 1230 0 1 {name=l3147 lab=out}
C {devices/lab_pin.sym} 170 1200 0 1 {name=l3148 lab=vss}

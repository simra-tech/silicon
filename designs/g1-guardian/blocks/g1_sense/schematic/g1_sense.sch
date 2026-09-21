v {xschem version=3.4.8RC file_version=1.3}
G {}
K {}
V {}
S {}
E {}
T {g1_sense: difference amplifier gain 20, pedestal VPED = 51/53 VREF (1.0008 V at VREF 1.04), ISENSE = VPED + 20*(SENSE_P-SENSE_N)} 0 -40 0 0 0.4 0.4 {}
C {sg13g2_pr/rppd.sym} 100 -1800 0 0 {name=R1N0 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 100 -1830 0 0 {name=l1 lab=sense_n}
C {devices/lab_pin.sym} 100 -1770 0 0 {name=l2 lab=vn}
C {sg13g2_pr/rppd.sym} 200 -1800 0 0 {name=R2N0 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 200 -1830 0 0 {name=l3 lab=vn}
C {devices/lab_pin.sym} 200 -1770 0 0 {name=l4 lab=R2N_0}
C {sg13g2_pr/rppd.sym} 200 -1720 0 0 {name=R2N1 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 200 -1750 0 0 {name=l5 lab=R2N_0}
C {devices/lab_pin.sym} 200 -1690 0 0 {name=l6 lab=R2N_1}
C {sg13g2_pr/rppd.sym} 200 -1640 0 0 {name=R2N2 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 200 -1670 0 0 {name=l7 lab=R2N_1}
C {devices/lab_pin.sym} 200 -1610 0 0 {name=l8 lab=R2N_2}
C {sg13g2_pr/rppd.sym} 200 -1560 0 0 {name=R2N3 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 200 -1590 0 0 {name=l9 lab=R2N_2}
C {devices/lab_pin.sym} 200 -1530 0 0 {name=l10 lab=R2N_3}
C {sg13g2_pr/rppd.sym} 200 -1480 0 0 {name=R2N4 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 200 -1510 0 0 {name=l11 lab=R2N_3}
C {devices/lab_pin.sym} 200 -1450 0 0 {name=l12 lab=R2N_4}
C {sg13g2_pr/rppd.sym} 200 -1400 0 0 {name=R2N5 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 200 -1430 0 0 {name=l13 lab=R2N_4}
C {devices/lab_pin.sym} 200 -1370 0 0 {name=l14 lab=R2N_5}
C {sg13g2_pr/rppd.sym} 200 -1320 0 0 {name=R2N6 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 200 -1350 0 0 {name=l15 lab=R2N_5}
C {devices/lab_pin.sym} 200 -1290 0 0 {name=l16 lab=R2N_6}
C {sg13g2_pr/rppd.sym} 200 -1240 0 0 {name=R2N7 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 200 -1270 0 0 {name=l17 lab=R2N_6}
C {devices/lab_pin.sym} 200 -1210 0 0 {name=l18 lab=R2N_7}
C {sg13g2_pr/rppd.sym} 200 -1160 0 0 {name=R2N8 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 200 -1190 0 0 {name=l19 lab=R2N_7}
C {devices/lab_pin.sym} 200 -1130 0 0 {name=l20 lab=R2N_8}
C {sg13g2_pr/rppd.sym} 200 -1080 0 0 {name=R2N9 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 200 -1110 0 0 {name=l21 lab=R2N_8}
C {devices/lab_pin.sym} 200 -1050 0 0 {name=l22 lab=R2N_9}
C {sg13g2_pr/rppd.sym} 200 -1000 0 0 {name=R2N10 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 200 -1030 0 0 {name=l23 lab=R2N_9}
C {devices/lab_pin.sym} 200 -970 0 0 {name=l24 lab=R2N_10}
C {sg13g2_pr/rppd.sym} 200 -920 0 0 {name=R2N11 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 200 -950 0 0 {name=l25 lab=R2N_10}
C {devices/lab_pin.sym} 200 -890 0 0 {name=l26 lab=R2N_11}
C {sg13g2_pr/rppd.sym} 200 -840 0 0 {name=R2N12 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 200 -870 0 0 {name=l27 lab=R2N_11}
C {devices/lab_pin.sym} 200 -810 0 0 {name=l28 lab=R2N_12}
C {sg13g2_pr/rppd.sym} 200 -760 0 0 {name=R2N13 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 200 -790 0 0 {name=l29 lab=R2N_12}
C {devices/lab_pin.sym} 200 -730 0 0 {name=l30 lab=R2N_13}
C {sg13g2_pr/rppd.sym} 200 -680 0 0 {name=R2N14 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 200 -710 0 0 {name=l31 lab=R2N_13}
C {devices/lab_pin.sym} 200 -650 0 0 {name=l32 lab=R2N_14}
C {sg13g2_pr/rppd.sym} 200 -600 0 0 {name=R2N15 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 200 -630 0 0 {name=l33 lab=R2N_14}
C {devices/lab_pin.sym} 200 -570 0 0 {name=l34 lab=R2N_15}
C {sg13g2_pr/rppd.sym} 200 -520 0 0 {name=R2N16 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 200 -550 0 0 {name=l35 lab=R2N_15}
C {devices/lab_pin.sym} 200 -490 0 0 {name=l36 lab=R2N_16}
C {sg13g2_pr/rppd.sym} 200 -440 0 0 {name=R2N17 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 200 -470 0 0 {name=l37 lab=R2N_16}
C {devices/lab_pin.sym} 200 -410 0 0 {name=l38 lab=R2N_17}
C {sg13g2_pr/rppd.sym} 200 -360 0 0 {name=R2N18 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 200 -390 0 0 {name=l39 lab=R2N_17}
C {devices/lab_pin.sym} 200 -330 0 0 {name=l40 lab=R2N_18}
C {sg13g2_pr/rppd.sym} 200 -280 0 0 {name=R2N19 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 200 -310 0 0 {name=l41 lab=R2N_18}
C {devices/lab_pin.sym} 200 -250 0 0 {name=l42 lab=isense}
C {sg13g2_pr/rppd.sym} 400 -1800 0 0 {name=R1P0 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 400 -1830 0 0 {name=l43 lab=sense_p}
C {devices/lab_pin.sym} 400 -1770 0 0 {name=l44 lab=vp}
C {sg13g2_pr/rppd.sym} 500 -1800 0 0 {name=R2P0 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 500 -1830 0 0 {name=l45 lab=vp}
C {devices/lab_pin.sym} 500 -1770 0 0 {name=l46 lab=R2P_0}
C {sg13g2_pr/rppd.sym} 500 -1720 0 0 {name=R2P1 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 500 -1750 0 0 {name=l47 lab=R2P_0}
C {devices/lab_pin.sym} 500 -1690 0 0 {name=l48 lab=R2P_1}
C {sg13g2_pr/rppd.sym} 500 -1640 0 0 {name=R2P2 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 500 -1670 0 0 {name=l49 lab=R2P_1}
C {devices/lab_pin.sym} 500 -1610 0 0 {name=l50 lab=R2P_2}
C {sg13g2_pr/rppd.sym} 500 -1560 0 0 {name=R2P3 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 500 -1590 0 0 {name=l51 lab=R2P_2}
C {devices/lab_pin.sym} 500 -1530 0 0 {name=l52 lab=R2P_3}
C {sg13g2_pr/rppd.sym} 500 -1480 0 0 {name=R2P4 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 500 -1510 0 0 {name=l53 lab=R2P_3}
C {devices/lab_pin.sym} 500 -1450 0 0 {name=l54 lab=R2P_4}
C {sg13g2_pr/rppd.sym} 500 -1400 0 0 {name=R2P5 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 500 -1430 0 0 {name=l55 lab=R2P_4}
C {devices/lab_pin.sym} 500 -1370 0 0 {name=l56 lab=R2P_5}
C {sg13g2_pr/rppd.sym} 500 -1320 0 0 {name=R2P6 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 500 -1350 0 0 {name=l57 lab=R2P_5}
C {devices/lab_pin.sym} 500 -1290 0 0 {name=l58 lab=R2P_6}
C {sg13g2_pr/rppd.sym} 500 -1240 0 0 {name=R2P7 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 500 -1270 0 0 {name=l59 lab=R2P_6}
C {devices/lab_pin.sym} 500 -1210 0 0 {name=l60 lab=R2P_7}
C {sg13g2_pr/rppd.sym} 500 -1160 0 0 {name=R2P8 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 500 -1190 0 0 {name=l61 lab=R2P_7}
C {devices/lab_pin.sym} 500 -1130 0 0 {name=l62 lab=R2P_8}
C {sg13g2_pr/rppd.sym} 500 -1080 0 0 {name=R2P9 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 500 -1110 0 0 {name=l63 lab=R2P_8}
C {devices/lab_pin.sym} 500 -1050 0 0 {name=l64 lab=R2P_9}
C {sg13g2_pr/rppd.sym} 500 -1000 0 0 {name=R2P10 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 500 -1030 0 0 {name=l65 lab=R2P_9}
C {devices/lab_pin.sym} 500 -970 0 0 {name=l66 lab=R2P_10}
C {sg13g2_pr/rppd.sym} 500 -920 0 0 {name=R2P11 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 500 -950 0 0 {name=l67 lab=R2P_10}
C {devices/lab_pin.sym} 500 -890 0 0 {name=l68 lab=R2P_11}
C {sg13g2_pr/rppd.sym} 500 -840 0 0 {name=R2P12 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 500 -870 0 0 {name=l69 lab=R2P_11}
C {devices/lab_pin.sym} 500 -810 0 0 {name=l70 lab=R2P_12}
C {sg13g2_pr/rppd.sym} 500 -760 0 0 {name=R2P13 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 500 -790 0 0 {name=l71 lab=R2P_12}
C {devices/lab_pin.sym} 500 -730 0 0 {name=l72 lab=R2P_13}
C {sg13g2_pr/rppd.sym} 500 -680 0 0 {name=R2P14 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 500 -710 0 0 {name=l73 lab=R2P_13}
C {devices/lab_pin.sym} 500 -650 0 0 {name=l74 lab=R2P_14}
C {sg13g2_pr/rppd.sym} 500 -600 0 0 {name=R2P15 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 500 -630 0 0 {name=l75 lab=R2P_14}
C {devices/lab_pin.sym} 500 -570 0 0 {name=l76 lab=R2P_15}
C {sg13g2_pr/rppd.sym} 500 -520 0 0 {name=R2P16 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 500 -550 0 0 {name=l77 lab=R2P_15}
C {devices/lab_pin.sym} 500 -490 0 0 {name=l78 lab=R2P_16}
C {sg13g2_pr/rppd.sym} 500 -440 0 0 {name=R2P17 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 500 -470 0 0 {name=l79 lab=R2P_16}
C {devices/lab_pin.sym} 500 -410 0 0 {name=l80 lab=R2P_17}
C {sg13g2_pr/rppd.sym} 500 -360 0 0 {name=R2P18 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 500 -390 0 0 {name=l81 lab=R2P_17}
C {devices/lab_pin.sym} 500 -330 0 0 {name=l82 lab=R2P_18}
C {sg13g2_pr/rppd.sym} 500 -280 0 0 {name=R2P19 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 500 -310 0 0 {name=l83 lab=R2P_18}
C {devices/lab_pin.sym} 500 -250 0 0 {name=l84 lab=vped}
C {sg13g2_pr/rppd.sym} 700 -1800 0 0 {name=RD10 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 700 -1830 0 0 {name=l85 lab=vref_buf}
C {devices/lab_pin.sym} 700 -1770 0 0 {name=l86 lab=RD1_0}
C {sg13g2_pr/rppd.sym} 700 -1720 0 0 {name=RD11 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 700 -1750 0 0 {name=l87 lab=RD1_0}
C {devices/lab_pin.sym} 700 -1690 0 0 {name=l88 lab=vped_ref}
C {sg13g2_pr/rppd.sym} 800 -1800 0 0 {name=RD20 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 800 -1830 0 0 {name=l89 lab=vped_ref}
C {devices/lab_pin.sym} 800 -1770 0 0 {name=l90 lab=RD2_0}
C {sg13g2_pr/rppd.sym} 800 -1720 0 0 {name=RD21 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 800 -1750 0 0 {name=l91 lab=RD2_0}
C {devices/lab_pin.sym} 800 -1690 0 0 {name=l92 lab=RD2_1}
C {sg13g2_pr/rppd.sym} 800 -1640 0 0 {name=RD22 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 800 -1670 0 0 {name=l93 lab=RD2_1}
C {devices/lab_pin.sym} 800 -1610 0 0 {name=l94 lab=RD2_2}
C {sg13g2_pr/rppd.sym} 800 -1560 0 0 {name=RD23 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 800 -1590 0 0 {name=l95 lab=RD2_2}
C {devices/lab_pin.sym} 800 -1530 0 0 {name=l96 lab=RD2_3}
C {sg13g2_pr/rppd.sym} 800 -1480 0 0 {name=RD24 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 800 -1510 0 0 {name=l97 lab=RD2_3}
C {devices/lab_pin.sym} 800 -1450 0 0 {name=l98 lab=RD2_4}
C {sg13g2_pr/rppd.sym} 800 -1400 0 0 {name=RD25 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 800 -1430 0 0 {name=l99 lab=RD2_4}
C {devices/lab_pin.sym} 800 -1370 0 0 {name=l100 lab=RD2_5}
C {sg13g2_pr/rppd.sym} 800 -1320 0 0 {name=RD26 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 800 -1350 0 0 {name=l101 lab=RD2_5}
C {devices/lab_pin.sym} 800 -1290 0 0 {name=l102 lab=RD2_6}
C {sg13g2_pr/rppd.sym} 800 -1240 0 0 {name=RD27 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 800 -1270 0 0 {name=l103 lab=RD2_6}
C {devices/lab_pin.sym} 800 -1210 0 0 {name=l104 lab=RD2_7}
C {sg13g2_pr/rppd.sym} 800 -1160 0 0 {name=RD28 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 800 -1190 0 0 {name=l105 lab=RD2_7}
C {devices/lab_pin.sym} 800 -1130 0 0 {name=l106 lab=RD2_8}
C {sg13g2_pr/rppd.sym} 800 -1080 0 0 {name=RD29 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 800 -1110 0 0 {name=l107 lab=RD2_8}
C {devices/lab_pin.sym} 800 -1050 0 0 {name=l108 lab=RD2_9}
C {sg13g2_pr/rppd.sym} 800 -1000 0 0 {name=RD210 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 800 -1030 0 0 {name=l109 lab=RD2_9}
C {devices/lab_pin.sym} 800 -970 0 0 {name=l110 lab=RD2_10}
C {sg13g2_pr/rppd.sym} 800 -920 0 0 {name=RD211 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 800 -950 0 0 {name=l111 lab=RD2_10}
C {devices/lab_pin.sym} 800 -890 0 0 {name=l112 lab=RD2_11}
C {sg13g2_pr/rppd.sym} 800 -840 0 0 {name=RD212 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 800 -870 0 0 {name=l113 lab=RD2_11}
C {devices/lab_pin.sym} 800 -810 0 0 {name=l114 lab=RD2_12}
C {sg13g2_pr/rppd.sym} 800 -760 0 0 {name=RD213 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 800 -790 0 0 {name=l115 lab=RD2_12}
C {devices/lab_pin.sym} 800 -730 0 0 {name=l116 lab=RD2_13}
C {sg13g2_pr/rppd.sym} 800 -680 0 0 {name=RD214 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 800 -710 0 0 {name=l117 lab=RD2_13}
C {devices/lab_pin.sym} 800 -650 0 0 {name=l118 lab=RD2_14}
C {sg13g2_pr/rppd.sym} 800 -600 0 0 {name=RD215 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 800 -630 0 0 {name=l119 lab=RD2_14}
C {devices/lab_pin.sym} 800 -570 0 0 {name=l120 lab=RD2_15}
C {sg13g2_pr/rppd.sym} 800 -520 0 0 {name=RD216 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 800 -550 0 0 {name=l121 lab=RD2_15}
C {devices/lab_pin.sym} 800 -490 0 0 {name=l122 lab=RD2_16}
C {sg13g2_pr/rppd.sym} 800 -440 0 0 {name=RD217 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 800 -470 0 0 {name=l123 lab=RD2_16}
C {devices/lab_pin.sym} 800 -410 0 0 {name=l124 lab=RD2_17}
C {sg13g2_pr/rppd.sym} 800 -360 0 0 {name=RD218 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 800 -390 0 0 {name=l125 lab=RD2_17}
C {devices/lab_pin.sym} 800 -330 0 0 {name=l126 lab=RD2_18}
C {sg13g2_pr/rppd.sym} 800 -280 0 0 {name=RD219 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 800 -310 0 0 {name=l127 lab=RD2_18}
C {devices/lab_pin.sym} 800 -250 0 0 {name=l128 lab=RD2_19}
C {sg13g2_pr/rppd.sym} 800 -200 0 0 {name=RD220 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 800 -230 0 0 {name=l129 lab=RD2_19}
C {devices/lab_pin.sym} 800 -170 0 0 {name=l130 lab=RD2_20}
C {sg13g2_pr/rppd.sym} 800 -120 0 0 {name=RD221 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 800 -150 0 0 {name=l131 lab=RD2_20}
C {devices/lab_pin.sym} 800 -90 0 0 {name=l132 lab=RD2_21}
C {sg13g2_pr/rppd.sym} 800 -40 0 0 {name=RD222 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 800 -70 0 0 {name=l133 lab=RD2_21}
C {devices/lab_pin.sym} 800 -10 0 0 {name=l134 lab=RD2_22}
C {sg13g2_pr/rppd.sym} 800 40 0 0 {name=RD223 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 800 10 0 0 {name=l135 lab=RD2_22}
C {devices/lab_pin.sym} 800 70 0 0 {name=l136 lab=RD2_23}
C {sg13g2_pr/rppd.sym} 800 120 0 0 {name=RD224 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 800 90 0 0 {name=l137 lab=RD2_23}
C {devices/lab_pin.sym} 800 150 0 0 {name=l138 lab=RD2_24}
C {sg13g2_pr/rppd.sym} 800 200 0 0 {name=RD225 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 800 170 0 0 {name=l139 lab=RD2_24}
C {devices/lab_pin.sym} 800 230 0 0 {name=l140 lab=RD2_25}
C {sg13g2_pr/rppd.sym} 800 280 0 0 {name=RD226 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 800 250 0 0 {name=l141 lab=RD2_25}
C {devices/lab_pin.sym} 800 310 0 0 {name=l142 lab=RD2_26}
C {sg13g2_pr/rppd.sym} 800 360 0 0 {name=RD227 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 800 330 0 0 {name=l143 lab=RD2_26}
C {devices/lab_pin.sym} 800 390 0 0 {name=l144 lab=RD2_27}
C {sg13g2_pr/rppd.sym} 800 440 0 0 {name=RD228 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 800 410 0 0 {name=l145 lab=RD2_27}
C {devices/lab_pin.sym} 800 470 0 0 {name=l146 lab=RD2_28}
C {sg13g2_pr/rppd.sym} 800 520 0 0 {name=RD229 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 800 490 0 0 {name=l147 lab=RD2_28}
C {devices/lab_pin.sym} 800 550 0 0 {name=l148 lab=RD2_29}
C {sg13g2_pr/rppd.sym} 800 600 0 0 {name=RD230 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 800 570 0 0 {name=l149 lab=RD2_29}
C {devices/lab_pin.sym} 800 630 0 0 {name=l150 lab=RD2_30}
C {sg13g2_pr/rppd.sym} 800 680 0 0 {name=RD231 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 800 650 0 0 {name=l151 lab=RD2_30}
C {devices/lab_pin.sym} 800 710 0 0 {name=l152 lab=RD2_31}
C {sg13g2_pr/rppd.sym} 800 760 0 0 {name=RD232 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 800 730 0 0 {name=l153 lab=RD2_31}
C {devices/lab_pin.sym} 800 790 0 0 {name=l154 lab=RD2_32}
C {sg13g2_pr/rppd.sym} 800 840 0 0 {name=RD233 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 800 810 0 0 {name=l155 lab=RD2_32}
C {devices/lab_pin.sym} 800 870 0 0 {name=l156 lab=RD2_33}
C {sg13g2_pr/rppd.sym} 800 920 0 0 {name=RD234 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 800 890 0 0 {name=l157 lab=RD2_33}
C {devices/lab_pin.sym} 800 950 0 0 {name=l158 lab=RD2_34}
C {sg13g2_pr/rppd.sym} 800 1000 0 0 {name=RD235 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 800 970 0 0 {name=l159 lab=RD2_34}
C {devices/lab_pin.sym} 800 1030 0 0 {name=l160 lab=RD2_35}
C {sg13g2_pr/rppd.sym} 800 1080 0 0 {name=RD236 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 800 1050 0 0 {name=l161 lab=RD2_35}
C {devices/lab_pin.sym} 800 1110 0 0 {name=l162 lab=RD2_36}
C {sg13g2_pr/rppd.sym} 800 1160 0 0 {name=RD237 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 800 1130 0 0 {name=l163 lab=RD2_36}
C {devices/lab_pin.sym} 800 1190 0 0 {name=l164 lab=RD2_37}
C {sg13g2_pr/rppd.sym} 800 1240 0 0 {name=RD238 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 800 1210 0 0 {name=l165 lab=RD2_37}
C {devices/lab_pin.sym} 800 1270 0 0 {name=l166 lab=RD2_38}
C {sg13g2_pr/rppd.sym} 800 1320 0 0 {name=RD239 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 800 1290 0 0 {name=l167 lab=RD2_38}
C {devices/lab_pin.sym} 800 1350 0 0 {name=l168 lab=RD2_39}
C {sg13g2_pr/rppd.sym} 800 1400 0 0 {name=RD240 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 800 1370 0 0 {name=l169 lab=RD2_39}
C {devices/lab_pin.sym} 800 1430 0 0 {name=l170 lab=RD2_40}
C {sg13g2_pr/rppd.sym} 800 1480 0 0 {name=RD241 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 800 1450 0 0 {name=l171 lab=RD2_40}
C {devices/lab_pin.sym} 800 1510 0 0 {name=l172 lab=RD2_41}
C {sg13g2_pr/rppd.sym} 800 1560 0 0 {name=RD242 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 800 1530 0 0 {name=l173 lab=RD2_41}
C {devices/lab_pin.sym} 800 1590 0 0 {name=l174 lab=RD2_42}
C {sg13g2_pr/rppd.sym} 800 1640 0 0 {name=RD243 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 800 1610 0 0 {name=l175 lab=RD2_42}
C {devices/lab_pin.sym} 800 1670 0 0 {name=l176 lab=RD2_43}
C {sg13g2_pr/rppd.sym} 800 1720 0 0 {name=RD244 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 800 1690 0 0 {name=l177 lab=RD2_43}
C {devices/lab_pin.sym} 800 1750 0 0 {name=l178 lab=RD2_44}
C {sg13g2_pr/rppd.sym} 800 1800 0 0 {name=RD245 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 800 1770 0 0 {name=l179 lab=RD2_44}
C {devices/lab_pin.sym} 800 1830 0 0 {name=l180 lab=RD2_45}
C {sg13g2_pr/rppd.sym} 800 1880 0 0 {name=RD246 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 800 1850 0 0 {name=l181 lab=RD2_45}
C {devices/lab_pin.sym} 800 1910 0 0 {name=l182 lab=RD2_46}
C {sg13g2_pr/rppd.sym} 800 1960 0 0 {name=RD247 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 800 1930 0 0 {name=l183 lab=RD2_46}
C {devices/lab_pin.sym} 800 1990 0 0 {name=l184 lab=RD2_47}
C {sg13g2_pr/rppd.sym} 800 2040 0 0 {name=RD248 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 800 2010 0 0 {name=l185 lab=RD2_47}
C {devices/lab_pin.sym} 800 2070 0 0 {name=l186 lab=RD2_48}
C {sg13g2_pr/rppd.sym} 800 2120 0 0 {name=RD249 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 800 2090 0 0 {name=l187 lab=RD2_48}
C {devices/lab_pin.sym} 800 2150 0 0 {name=l188 lab=RD2_49}
C {sg13g2_pr/rppd.sym} 800 2200 0 0 {name=RD250 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {devices/lab_pin.sym} 800 2170 0 0 {name=l189 lab=RD2_49}
C {devices/lab_pin.sym} 800 2230 0 0 {name=l190 lab=vss}
C {sg13g2_pr/sg13_hv_nmos.sym} 1000 -1800 0 0 {name=MBI model=sg13_hv_nmos w=3.3u l=1u ng=1 m=1}
C {devices/lab_pin.sym} 1020 -1830 0 0 {name=l191 lab=iptat}
C {devices/lab_pin.sym} 980 -1800 0 0 {name=l192 lab=iptat}
C {devices/lab_pin.sym} 1020 -1770 0 0 {name=l193 lab=vss}
C {devices/lab_pin.sym} 1020 -1800 0 0 {name=l194 lab=vss}
C {g1_ota.sym} 1100 -1500 0 0 {name=XOTA }
C {devices/lab_pin.sym} 1040 -1550 0 0 {name=l195 lab=vp}
C {devices/lab_pin.sym} 1040 -1530 0 0 {name=l196 lab=vn}
C {devices/lab_pin.sym} 1040 -1510 0 0 {name=l197 lab=iptat}
C {devices/lab_pin.sym} 1040 -1490 0 0 {name=l198 lab=isense}
C {devices/lab_pin.sym} 1040 -1470 0 0 {name=l199 lab=vdd}
C {devices/lab_pin.sym} 1040 -1450 0 0 {name=l200 lab=vss}
C {g1_ota.sym} 1100 -1200 0 0 {name=XBUF }
C {devices/lab_pin.sym} 1040 -1250 0 0 {name=l201 lab=vped_ref}
C {devices/lab_pin.sym} 1040 -1230 0 0 {name=l202 lab=vped}
C {devices/lab_pin.sym} 1040 -1210 0 0 {name=l203 lab=iptat}
C {devices/lab_pin.sym} 1040 -1190 0 0 {name=l204 lab=vped}
C {devices/lab_pin.sym} 1040 -1170 0 0 {name=l205 lab=vdd}
C {devices/lab_pin.sym} 1040 -1150 0 0 {name=l206 lab=vss}
C {g1_ota.sym} 1100 -900 0 0 {name=XREF }
C {devices/lab_pin.sym} 1040 -950 0 0 {name=l207 lab=vref}
C {devices/lab_pin.sym} 1040 -930 0 0 {name=l208 lab=vref_buf}
C {devices/lab_pin.sym} 1040 -910 0 0 {name=l209 lab=iptat}
C {devices/lab_pin.sym} 1040 -890 0 0 {name=l210 lab=vref_buf}
C {devices/lab_pin.sym} 1040 -870 0 0 {name=l211 lab=vdd}
C {devices/lab_pin.sym} 1040 -850 0 0 {name=l212 lab=vss}
C {devices/ipin.sym} 1400 -1500 0 0 {name=pi0 lab=sense_p}
C {devices/ipin.sym} 1400 -1480 0 0 {name=pi1 lab=sense_n}
C {devices/ipin.sym} 1400 -1460 0 0 {name=pi2 lab=vref}
C {devices/ipin.sym} 1400 -1440 0 0 {name=pi3 lab=iptat}
C {devices/opin.sym} 1400 -1420 0 0 {name=po0 lab=isense}
C {devices/opin.sym} 1400 -1400 0 0 {name=po1 lab=vped}
C {devices/opin.sym} 1400 -1380 0 0 {name=po2 lab=vref_buf}
C {devices/iopin.sym} 1400 -1360 0 0 {name=pb0 lab=vdd}
C {devices/iopin.sym} 1400 -1340 0 0 {name=pb1 lab=vss}
T {iptat: 4.13 uA PTAT from G1_BGR into MBI; all three OTAs run at ~350 uA each (PTAT). vref_buf feeds the G1_TRIP DAC strings.} 100 -1900 0 0 0.3 0.3 {}

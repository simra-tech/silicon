v {xschem version=3.4.8RC file_version=1.3}
G {}
K {}
V {}
S {}
E {}
T {g1_osc: ping-pong RC relaxation oscillator, f ~ 1/(2 R C ln2), threshold VDD/2, en, 4-bit trim} 0 -40 0 0 0.4 0.4 {}
C {sg13g2_pr/rppd.sym} 100 -900 0 0 {name=RA w=1u l=117u model=rppd b=0 m=1}
C {devices/lab_pin.sym} 100 -930 0 0 {name=l1 lab=vdd}
C {devices/lab_pin.sym} 100 -870 0 0 {name=l2 lab=va}
C {sg13g2_pr/rppd.sym} 200 -900 0 0 {name=RB w=1u l=117u model=rppd b=0 m=1}
C {devices/lab_pin.sym} 200 -930 0 0 {name=l3 lab=vdd}
C {devices/lab_pin.sym} 200 -870 0 0 {name=l4 lab=vb}
C {g1_osc_cbank.sym} 400 -900 0 0 {name=XCA }
C {devices/lab_pin.sym} 340 -950 0 0 {name=l5 lab=trim0}
C {devices/lab_pin.sym} 340 -930 0 0 {name=l6 lab=trim1}
C {devices/lab_pin.sym} 340 -910 0 0 {name=l7 lab=trim2}
C {devices/lab_pin.sym} 340 -890 0 0 {name=l8 lab=trim3}
C {devices/lab_pin.sym} 340 -870 0 0 {name=l9 lab=va}
C {devices/lab_pin.sym} 340 -850 0 0 {name=l10 lab=vss}
C {g1_osc_cbank.sym} 400 -600 0 0 {name=XCB }
C {devices/lab_pin.sym} 340 -650 0 0 {name=l11 lab=trim0}
C {devices/lab_pin.sym} 340 -630 0 0 {name=l12 lab=trim1}
C {devices/lab_pin.sym} 340 -610 0 0 {name=l13 lab=trim2}
C {devices/lab_pin.sym} 340 -590 0 0 {name=l14 lab=trim3}
C {devices/lab_pin.sym} 340 -570 0 0 {name=l15 lab=vb}
C {devices/lab_pin.sym} 340 -550 0 0 {name=l16 lab=vss}
C {sg13g2_pr/sg13_lv_nmos.sym} 600 -900 0 0 {name=MRA model=sg13_lv_nmos w=4u l=0.13u ng=1 m=1}
C {devices/lab_pin.sym} 620 -930 0 0 {name=l17 lab=va}
C {devices/lab_pin.sym} 580 -900 0 0 {name=l18 lab=rsta}
C {devices/lab_pin.sym} 620 -870 0 0 {name=l19 lab=vss}
C {devices/lab_pin.sym} 620 -900 0 0 {name=l20 lab=vss}
C {sg13g2_pr/sg13_lv_nmos.sym} 600 -600 0 0 {name=MRB model=sg13_lv_nmos w=4u l=0.13u ng=1 m=1}
C {devices/lab_pin.sym} 620 -630 0 0 {name=l21 lab=vb}
C {devices/lab_pin.sym} 580 -600 0 0 {name=l22 lab=rstb}
C {devices/lab_pin.sym} 620 -570 0 0 {name=l23 lab=vss}
C {devices/lab_pin.sym} 620 -600 0 0 {name=l24 lab=vss}
C {sg13g2_pr/rppd.sym} 800 -900 0 0 {name=RT1 w=1u l=384.3u model=rppd b=0 m=1}
C {devices/lab_pin.sym} 800 -930 0 0 {name=l25 lab=vdd}
C {devices/lab_pin.sym} 800 -870 0 0 {name=l26 lab=vth}
C {sg13g2_pr/rppd.sym} 800 -700 0 0 {name=RT2 w=1u l=384.3u model=rppd b=0 m=1}
C {devices/lab_pin.sym} 800 -730 0 0 {name=l27 lab=vth}
C {devices/lab_pin.sym} 800 -670 0 0 {name=l28 lab=vss}
C {sg13g2_pr/cap_cmim.sym} 800 -500 0 0 {name=CTH model=cap_cmim w=26u l=26u m=1}
C {devices/lab_pin.sym} 800 -530 0 0 {name=l29 lab=vth}
C {devices/lab_pin.sym} 800 -470 0 0 {name=l30 lab=vss}
C {sg13g2_pr/dpantenna.sym} 800 -300 0 0 {name=DANT model=dpantenna l=0.78u w=0.78u}
C {devices/lab_pin.sym} 800 -270 0 0 {name=l31 lab=vth}
C {devices/lab_pin.sym} 800 -330 0 0 {name=l32 lab=vdd}
C {sg13g2_pr/rppd.sym} 950 -900 0 0 {name=RBIAS w=1u l=134.3u model=rppd b=0 m=1}
C {devices/lab_pin.sym} 950 -930 0 0 {name=l33 lab=vdd}
C {devices/lab_pin.sym} 950 -870 0 0 {name=l34 lab=vbn}
C {sg13g2_pr/sg13_lv_nmos.sym} 950 -700 0 0 {name=MBD model=sg13_lv_nmos w=2u l=0.5u ng=1 m=1}
C {devices/lab_pin.sym} 970 -730 0 0 {name=l35 lab=vbn}
C {devices/lab_pin.sym} 930 -700 0 0 {name=l36 lab=vbn}
C {devices/lab_pin.sym} 970 -670 0 0 {name=l37 lab=vss}
C {devices/lab_pin.sym} 970 -700 0 0 {name=l38 lab=vss}
C {g1_osc_cmp.sym} 1200 -900 0 0 {name=XCMPA }
C {devices/lab_pin.sym} 1140 -950 0 0 {name=l39 lab=va}
C {devices/lab_pin.sym} 1140 -930 0 0 {name=l40 lab=vth}
C {devices/lab_pin.sym} 1140 -910 0 0 {name=l41 lab=vbn}
C {devices/lab_pin.sym} 1140 -890 0 0 {name=l42 lab=ca}
C {devices/lab_pin.sym} 1140 -870 0 0 {name=l43 lab=vdd}
C {devices/lab_pin.sym} 1140 -850 0 0 {name=l44 lab=vss}
C {g1_osc_cmp.sym} 1200 -600 0 0 {name=XCMPB }
C {devices/lab_pin.sym} 1140 -650 0 0 {name=l45 lab=vb}
C {devices/lab_pin.sym} 1140 -630 0 0 {name=l46 lab=vth}
C {devices/lab_pin.sym} 1140 -610 0 0 {name=l47 lab=vbn}
C {devices/lab_pin.sym} 1140 -590 0 0 {name=l48 lab=cb}
C {devices/lab_pin.sym} 1140 -570 0 0 {name=l49 lab=vdd}
C {devices/lab_pin.sym} 1140 -550 0 0 {name=l50 lab=vss}
C {g1_osc_inv.sym} 1500 -1000 0 0 {name=XEN }
C {devices/lab_pin.sym} 1440 -1030 0 0 {name=l51 lab=en}
C {devices/lab_pin.sym} 1440 -1010 0 0 {name=l52 lab=en_n}
C {devices/lab_pin.sym} 1440 -990 0 0 {name=l53 lab=vdd}
C {devices/lab_pin.sym} 1440 -970 0 0 {name=l54 lab=vss}
C {g1_osc_nor3.sym} 1500 -800 0 0 {name=XNQ }
C {devices/lab_pin.sym} 1440 -850 0 0 {name=l55 lab=ca}
C {devices/lab_pin.sym} 1440 -830 0 0 {name=l56 lab=en_n}
C {devices/lab_pin.sym} 1440 -810 0 0 {name=l57 lab=qb}
C {devices/lab_pin.sym} 1440 -790 0 0 {name=l58 lab=q}
C {devices/lab_pin.sym} 1440 -770 0 0 {name=l59 lab=vdd}
C {devices/lab_pin.sym} 1440 -750 0 0 {name=l60 lab=vss}
C {g1_osc_nor2.sym} 1500 -550 0 0 {name=XNQB }
C {devices/lab_pin.sym} 1440 -590 0 0 {name=l61 lab=cb}
C {devices/lab_pin.sym} 1440 -570 0 0 {name=l62 lab=q}
C {devices/lab_pin.sym} 1440 -550 0 0 {name=l63 lab=qb}
C {devices/lab_pin.sym} 1440 -530 0 0 {name=l64 lab=vdd}
C {devices/lab_pin.sym} 1440 -510 0 0 {name=l65 lab=vss}
C {g1_osc_nand2.sym} 1500 -300 0 0 {name=XRSTB }
C {devices/lab_pin.sym} 1440 -340 0 0 {name=l66 lab=qb}
C {devices/lab_pin.sym} 1440 -320 0 0 {name=l67 lab=en}
C {devices/lab_pin.sym} 1440 -300 0 0 {name=l68 lab=rstb}
C {devices/lab_pin.sym} 1440 -280 0 0 {name=l69 lab=vdd}
C {devices/lab_pin.sym} 1440 -260 0 0 {name=l70 lab=vss}
C {g1_osc_inv.sym} 1750 -1000 0 0 {name=XRSTA }
C {devices/lab_pin.sym} 1690 -1030 0 0 {name=l71 lab=q}
C {devices/lab_pin.sym} 1690 -1010 0 0 {name=l72 lab=rsta}
C {devices/lab_pin.sym} 1690 -990 0 0 {name=l73 lab=vdd}
C {devices/lab_pin.sym} 1690 -970 0 0 {name=l74 lab=vss}
C {g1_osc_inv.sym} 1750 -800 0 0 {name=XB1 }
C {devices/lab_pin.sym} 1690 -830 0 0 {name=l75 lab=q}
C {devices/lab_pin.sym} 1690 -810 0 0 {name=l76 lab=qn_b}
C {devices/lab_pin.sym} 1690 -790 0 0 {name=l77 lab=vdd}
C {devices/lab_pin.sym} 1690 -770 0 0 {name=l78 lab=vss}
C {g1_osc_inv.sym} 1750 -600 0 0 {name=XB2 }
C {devices/lab_pin.sym} 1690 -630 0 0 {name=l79 lab=qn_b}
C {devices/lab_pin.sym} 1690 -610 0 0 {name=l80 lab=osc_clk}
C {devices/lab_pin.sym} 1690 -590 0 0 {name=l81 lab=vdd}
C {devices/lab_pin.sym} 1690 -570 0 0 {name=l82 lab=vss}
C {devices/ipin.sym} 2000 -1000 0 0 {name=pi0 lab=en}
C {devices/ipin.sym} 2000 -980 0 0 {name=pi1 lab=trim0}
C {devices/ipin.sym} 2000 -960 0 0 {name=pi2 lab=trim1}
C {devices/ipin.sym} 2000 -940 0 0 {name=pi3 lab=trim2}
C {devices/ipin.sym} 2000 -920 0 0 {name=pi4 lab=trim3}
C {devices/opin.sym} 2000 -900 0 0 {name=po0 lab=osc_clk}
C {devices/iopin.sym} 2000 -880 0 0 {name=pb0 lab=vdd}
C {devices/iopin.sym} 2000 -860 0 0 {name=pb1 lab=vss}
T {q=1: A charges (rsta=0), B held (rstb=1). va > vdd/2 -> ca=1 -> q=0. en=0 -> q=0, both banks held, osc_clk=0.} 100 -1100 0 0 0.3 0.3 {}

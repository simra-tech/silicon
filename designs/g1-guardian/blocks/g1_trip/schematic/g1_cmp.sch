v {xschem version=3.4.8RC file_version=1.3}
G {}
K {}
V {}
S {}
E {}
T {g1_cmp: StrongARM latch, 1.2 V; q=1 when inp>inn, held by SR latch between strobes} 0 -40 0 0 0.4 0.4 {}
C {sg13g2_pr/sg13_lv_nmos.sym} 400 -100 0 0 {name=MTAIL model=sg13_lv_nmos w=16u l=0.13u ng=1 m=1}
C {devices/lab_pin.sym} 420 -130 0 0 {name=l1 lab=tail}
C {devices/lab_pin.sym} 380 -100 0 0 {name=l2 lab=clk}
C {devices/lab_pin.sym} 420 -70 0 0 {name=l3 lab=vss}
C {devices/lab_pin.sym} 420 -100 0 0 {name=l4 lab=vss}
C {sg13g2_pr/sg13_lv_nmos.sym} 300 -200 0 0 {name=M1 model=sg13_lv_nmos w=12u l=0.34u ng=1 m=1}
C {devices/lab_pin.sym} 320 -230 0 0 {name=l5 lab=xp}
C {devices/lab_pin.sym} 280 -200 0 0 {name=l6 lab=inp}
C {devices/lab_pin.sym} 320 -170 0 0 {name=l7 lab=tail}
C {devices/lab_pin.sym} 320 -200 0 0 {name=l8 lab=vss}
C {sg13g2_pr/sg13_lv_nmos.sym} 500 -200 0 0 {name=M2 model=sg13_lv_nmos w=12u l=0.34u ng=1 m=1}
C {devices/lab_pin.sym} 520 -230 0 0 {name=l9 lab=xq}
C {devices/lab_pin.sym} 480 -200 0 0 {name=l10 lab=inn}
C {devices/lab_pin.sym} 520 -170 0 0 {name=l11 lab=tail}
C {devices/lab_pin.sym} 520 -200 0 0 {name=l12 lab=vss}
C {sg13g2_pr/sg13_lv_nmos.sym} 200 -200 0 0 {name=MD1 model=sg13_lv_nmos w=6u l=0.13u ng=1 m=1}
C {devices/lab_pin.sym} 220 -230 0 0 {name=l13 lab=xq}
C {devices/lab_pin.sym} 180 -200 0 0 {name=l14 lab=inp}
C {devices/lab_pin.sym} 220 -170 0 0 {name=l15 lab=xq}
C {devices/lab_pin.sym} 220 -200 0 0 {name=l16 lab=vss}
C {sg13g2_pr/sg13_lv_nmos.sym} 600 -200 0 0 {name=MD2 model=sg13_lv_nmos w=6u l=0.13u ng=1 m=1}
C {devices/lab_pin.sym} 620 -230 0 0 {name=l17 lab=xp}
C {devices/lab_pin.sym} 580 -200 0 0 {name=l18 lab=inn}
C {devices/lab_pin.sym} 620 -170 0 0 {name=l19 lab=xp}
C {devices/lab_pin.sym} 620 -200 0 0 {name=l20 lab=vss}
C {sg13g2_pr/sg13_lv_nmos.sym} 300 -300 0 0 {name=M3 model=sg13_lv_nmos w=3u l=0.13u ng=1 m=1}
C {devices/lab_pin.sym} 320 -330 0 0 {name=l21 lab=xn}
C {devices/lab_pin.sym} 280 -300 0 0 {name=l22 lab=yn}
C {devices/lab_pin.sym} 320 -270 0 0 {name=l23 lab=xp}
C {devices/lab_pin.sym} 320 -300 0 0 {name=l24 lab=vss}
C {sg13g2_pr/sg13_lv_nmos.sym} 500 -300 0 0 {name=M4 model=sg13_lv_nmos w=3u l=0.13u ng=1 m=1}
C {devices/lab_pin.sym} 520 -330 0 0 {name=l25 lab=yn}
C {devices/lab_pin.sym} 480 -300 0 0 {name=l26 lab=xn}
C {devices/lab_pin.sym} 520 -270 0 0 {name=l27 lab=xq}
C {devices/lab_pin.sym} 520 -300 0 0 {name=l28 lab=vss}
C {sg13g2_pr/sg13_lv_pmos.sym} 300 -400 0 0 {name=M5 model=sg13_lv_pmos w=3u l=0.13u ng=1 m=1}
C {devices/lab_pin.sym} 320 -370 0 0 {name=l29 lab=xn}
C {devices/lab_pin.sym} 280 -400 0 0 {name=l30 lab=yn}
C {devices/lab_pin.sym} 320 -430 0 0 {name=l31 lab=vdd}
C {devices/lab_pin.sym} 320 -400 0 0 {name=l32 lab=vdd}
C {sg13g2_pr/sg13_lv_pmos.sym} 500 -400 0 0 {name=M6 model=sg13_lv_pmos w=3u l=0.13u ng=1 m=1}
C {devices/lab_pin.sym} 520 -370 0 0 {name=l33 lab=yn}
C {devices/lab_pin.sym} 480 -400 0 0 {name=l34 lab=xn}
C {devices/lab_pin.sym} 520 -430 0 0 {name=l35 lab=vdd}
C {devices/lab_pin.sym} 520 -400 0 0 {name=l36 lab=vdd}
C {sg13g2_pr/sg13_lv_pmos.sym} 200 -400 0 0 {name=M7 model=sg13_lv_pmos w=6u l=0.13u ng=1 m=1}
C {devices/lab_pin.sym} 220 -370 0 0 {name=l37 lab=xn}
C {devices/lab_pin.sym} 180 -400 0 0 {name=l38 lab=clk}
C {devices/lab_pin.sym} 220 -430 0 0 {name=l39 lab=vdd}
C {devices/lab_pin.sym} 220 -400 0 0 {name=l40 lab=vdd}
C {sg13g2_pr/sg13_lv_pmos.sym} 600 -400 0 0 {name=M8 model=sg13_lv_pmos w=6u l=0.13u ng=1 m=1}
C {devices/lab_pin.sym} 620 -370 0 0 {name=l41 lab=yn}
C {devices/lab_pin.sym} 580 -400 0 0 {name=l42 lab=clk}
C {devices/lab_pin.sym} 620 -430 0 0 {name=l43 lab=vdd}
C {devices/lab_pin.sym} 620 -400 0 0 {name=l44 lab=vdd}
C {sg13g2_pr/sg13_lv_pmos.sym} 200 -300 0 0 {name=M9 model=sg13_lv_pmos w=3u l=0.13u ng=1 m=1}
C {devices/lab_pin.sym} 220 -270 0 0 {name=l45 lab=xp}
C {devices/lab_pin.sym} 180 -300 0 0 {name=l46 lab=clk}
C {devices/lab_pin.sym} 220 -330 0 0 {name=l47 lab=vdd}
C {devices/lab_pin.sym} 220 -300 0 0 {name=l48 lab=vdd}
C {sg13g2_pr/sg13_lv_pmos.sym} 600 -300 0 0 {name=M10 model=sg13_lv_pmos w=3u l=0.13u ng=1 m=1}
C {devices/lab_pin.sym} 620 -270 0 0 {name=l49 lab=xq}
C {devices/lab_pin.sym} 580 -300 0 0 {name=l50 lab=clk}
C {devices/lab_pin.sym} 620 -330 0 0 {name=l51 lab=vdd}
C {devices/lab_pin.sym} 620 -300 0 0 {name=l52 lab=vdd}
C {sg13g2_pr/sg13_lv_pmos.sym} 800 -400 0 0 {name=MIAP model=sg13_lv_pmos w=1u l=0.13u ng=1 m=1}
C {devices/lab_pin.sym} 820 -370 0 0 {name=l53 lab=xnb}
C {devices/lab_pin.sym} 780 -400 0 0 {name=l54 lab=xn}
C {devices/lab_pin.sym} 820 -430 0 0 {name=l55 lab=vdd}
C {devices/lab_pin.sym} 820 -400 0 0 {name=l56 lab=vdd}
C {sg13g2_pr/sg13_lv_nmos.sym} 800 -300 0 0 {name=MIAN model=sg13_lv_nmos w=4u l=0.13u ng=1 m=1}
C {devices/lab_pin.sym} 820 -330 0 0 {name=l57 lab=xnb}
C {devices/lab_pin.sym} 780 -300 0 0 {name=l58 lab=xn}
C {devices/lab_pin.sym} 820 -270 0 0 {name=l59 lab=vss}
C {devices/lab_pin.sym} 820 -300 0 0 {name=l60 lab=vss}
C {sg13g2_pr/sg13_lv_pmos.sym} 900 -400 0 0 {name=MIBP model=sg13_lv_pmos w=1u l=0.13u ng=1 m=1}
C {devices/lab_pin.sym} 920 -370 0 0 {name=l61 lab=ynb}
C {devices/lab_pin.sym} 880 -400 0 0 {name=l62 lab=yn}
C {devices/lab_pin.sym} 920 -430 0 0 {name=l63 lab=vdd}
C {devices/lab_pin.sym} 920 -400 0 0 {name=l64 lab=vdd}
C {sg13g2_pr/sg13_lv_nmos.sym} 900 -300 0 0 {name=MIBN model=sg13_lv_nmos w=4u l=0.13u ng=1 m=1}
C {devices/lab_pin.sym} 920 -330 0 0 {name=l65 lab=ynb}
C {devices/lab_pin.sym} 880 -300 0 0 {name=l66 lab=yn}
C {devices/lab_pin.sym} 920 -270 0 0 {name=l67 lab=vss}
C {devices/lab_pin.sym} 920 -300 0 0 {name=l68 lab=vss}
C {sg13g2_pr/sg13_lv_pmos.sym} 1100 -500 0 0 {name=MNAP1 model=sg13_lv_pmos w=4u l=0.13u ng=1 m=1}
C {devices/lab_pin.sym} 1120 -470 0 0 {name=l69 lab=na}
C {devices/lab_pin.sym} 1080 -500 0 0 {name=l70 lab=xnb}
C {devices/lab_pin.sym} 1120 -530 0 0 {name=l71 lab=vdd}
C {devices/lab_pin.sym} 1120 -500 0 0 {name=l72 lab=vdd}
C {sg13g2_pr/sg13_lv_pmos.sym} 1100 -400 0 0 {name=MNAP2 model=sg13_lv_pmos w=4u l=0.13u ng=1 m=1}
C {devices/lab_pin.sym} 1120 -370 0 0 {name=l73 lab=qb}
C {devices/lab_pin.sym} 1080 -400 0 0 {name=l74 lab=q}
C {devices/lab_pin.sym} 1120 -430 0 0 {name=l75 lab=na}
C {devices/lab_pin.sym} 1120 -400 0 0 {name=l76 lab=vdd}
C {sg13g2_pr/sg13_lv_nmos.sym} 1100 -300 0 0 {name=MNAN1 model=sg13_lv_nmos w=1.5u l=0.13u ng=1 m=1}
C {devices/lab_pin.sym} 1120 -330 0 0 {name=l77 lab=qb}
C {devices/lab_pin.sym} 1080 -300 0 0 {name=l78 lab=xnb}
C {devices/lab_pin.sym} 1120 -270 0 0 {name=l79 lab=vss}
C {devices/lab_pin.sym} 1120 -300 0 0 {name=l80 lab=vss}
C {sg13g2_pr/sg13_lv_nmos.sym} 1100 -200 0 0 {name=MNAN2 model=sg13_lv_nmos w=1.5u l=0.13u ng=1 m=1}
C {devices/lab_pin.sym} 1120 -230 0 0 {name=l81 lab=qb}
C {devices/lab_pin.sym} 1080 -200 0 0 {name=l82 lab=q}
C {devices/lab_pin.sym} 1120 -170 0 0 {name=l83 lab=vss}
C {devices/lab_pin.sym} 1120 -200 0 0 {name=l84 lab=vss}
C {sg13g2_pr/sg13_lv_pmos.sym} 1250 -500 0 0 {name=MNBP1 model=sg13_lv_pmos w=4u l=0.13u ng=1 m=1}
C {devices/lab_pin.sym} 1270 -470 0 0 {name=l85 lab=nb}
C {devices/lab_pin.sym} 1230 -500 0 0 {name=l86 lab=ynb}
C {devices/lab_pin.sym} 1270 -530 0 0 {name=l87 lab=vdd}
C {devices/lab_pin.sym} 1270 -500 0 0 {name=l88 lab=vdd}
C {sg13g2_pr/sg13_lv_pmos.sym} 1250 -400 0 0 {name=MNBP2 model=sg13_lv_pmos w=4u l=0.13u ng=1 m=1}
C {devices/lab_pin.sym} 1270 -370 0 0 {name=l89 lab=q}
C {devices/lab_pin.sym} 1230 -400 0 0 {name=l90 lab=qb}
C {devices/lab_pin.sym} 1270 -430 0 0 {name=l91 lab=nb}
C {devices/lab_pin.sym} 1270 -400 0 0 {name=l92 lab=vdd}
C {sg13g2_pr/sg13_lv_nmos.sym} 1250 -300 0 0 {name=MNBN1 model=sg13_lv_nmos w=1.5u l=0.13u ng=1 m=1}
C {devices/lab_pin.sym} 1270 -330 0 0 {name=l93 lab=q}
C {devices/lab_pin.sym} 1230 -300 0 0 {name=l94 lab=ynb}
C {devices/lab_pin.sym} 1270 -270 0 0 {name=l95 lab=vss}
C {devices/lab_pin.sym} 1270 -300 0 0 {name=l96 lab=vss}
C {sg13g2_pr/sg13_lv_nmos.sym} 1250 -200 0 0 {name=MNBN2 model=sg13_lv_nmos w=1.5u l=0.13u ng=1 m=1}
C {devices/lab_pin.sym} 1270 -230 0 0 {name=l97 lab=q}
C {devices/lab_pin.sym} 1230 -200 0 0 {name=l98 lab=qb}
C {devices/lab_pin.sym} 1270 -170 0 0 {name=l99 lab=vss}
C {devices/lab_pin.sym} 1270 -200 0 0 {name=l100 lab=vss}
C {devices/ipin.sym} 1500 -500 0 0 {name=pi0 lab=inp}
C {devices/ipin.sym} 1500 -480 0 0 {name=pi1 lab=inn}
C {devices/ipin.sym} 1500 -460 0 0 {name=pi2 lab=clk}
C {devices/opin.sym} 1500 -440 0 0 {name=po0 lab=q}
C {devices/opin.sym} 1500 -420 0 0 {name=po1 lab=qb}
C {devices/iopin.sym} 1500 -400 0 0 {name=pb0 lab=vdd}
C {devices/iopin.sym} 1500 -380 0 0 {name=pb1 lab=vss}

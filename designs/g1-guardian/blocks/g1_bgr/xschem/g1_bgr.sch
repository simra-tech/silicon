v {xschem version=3.4.8RC file_version=1.3}
G {}
K {}
V {}
S {}
E {}
T {G1_BGR: op-amp-less cascoded self-biased npn13G2 bandgap, 3.3 V} 0 -220 0 0 0.4 0.4 {}
C {devices/iopin.sym} 0 -160 0 0 {name=p0 lab=vdd}
C {devices/iopin.sym} 80 -160 0 0 {name=p1 lab=vss}
C {devices/ipin.sym} 160 -160 0 0 {name=p2 lab=r4}
C {devices/opin.sym} 240 -160 0 0 {name=p3 lab=vref}
C {devices/opin.sym} 320 -160 0 0 {name=p4 lab=iptat}
C {devices/opin.sym} 400 -160 0 0 {name=p5 lab=pbias}
C {devices/opin.sym} 480 -160 0 0 {name=p6 lab=pcasc}
C {devices/opin.sym} 560 -160 0 0 {name=p7 lab=vbe}
C {devices/opin.sym} 640 -160 0 0 {name=p8 lab=dvbe}
C {sg13g2_pr/sg13_hv_pmos.sym} 60 40 0 0 {name=MP1 w=10u l=4u ng=1 m=1 mm_ok=1 model=sg13_hv_pmos spiceprefix=X}
C {devices/lab_pin.sym} 80 70 0 0 {name=l0 sig_type=std_logic lab=d1}
C {devices/lab_pin.sym} 40 40 0 0 {name=l1 sig_type=std_logic lab=pbias}
C {devices/lab_pin.sym} 80 10 0 0 {name=l2 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 80 40 0 0 {name=l3 sig_type=std_logic lab=vdd}
C {sg13g2_pr/sg13_hv_pmos.sym} 220 40 0 0 {name=MC1 w=10u l=4u ng=1 m=1 mm_ok=1 model=sg13_hv_pmos spiceprefix=X}
C {devices/lab_pin.sym} 240 70 0 0 {name=l4 sig_type=std_logic lab=n1}
C {devices/lab_pin.sym} 200 40 0 0 {name=l5 sig_type=std_logic lab=pcasc}
C {devices/lab_pin.sym} 240 10 0 0 {name=l6 sig_type=std_logic lab=d1}
C {devices/lab_pin.sym} 240 40 0 0 {name=l7 sig_type=std_logic lab=d1}
C {sg13g2_pr/sg13_hv_pmos.sym} 380 40 0 0 {name=MP2 w=10u l=4u ng=1 m=1 mm_ok=1 model=sg13_hv_pmos spiceprefix=X}
C {devices/lab_pin.sym} 400 70 0 0 {name=l8 sig_type=std_logic lab=d2}
C {devices/lab_pin.sym} 360 40 0 0 {name=l9 sig_type=std_logic lab=pbias}
C {devices/lab_pin.sym} 400 10 0 0 {name=l10 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 400 40 0 0 {name=l11 sig_type=std_logic lab=vdd}
C {sg13g2_pr/sg13_hv_pmos.sym} 540 40 0 0 {name=MC2 w=10u l=4u ng=1 m=1 mm_ok=1 model=sg13_hv_pmos spiceprefix=X}
C {devices/lab_pin.sym} 560 70 0 0 {name=l12 sig_type=std_logic lab=pbias}
C {devices/lab_pin.sym} 520 40 0 0 {name=l13 sig_type=std_logic lab=pcasc}
C {devices/lab_pin.sym} 560 10 0 0 {name=l14 sig_type=std_logic lab=d2}
C {devices/lab_pin.sym} 560 40 0 0 {name=l15 sig_type=std_logic lab=d2}
C {sg13g2_pr/rppd.sym} 700 40 0 0 {name=RB w=1u l=500u model=rppd body=sub! spiceprefix=X b=0 m=1 mm_ok=1}
C {devices/lab_pin.sym} 700 10 0 0 {name=l16 sig_type=std_logic lab=pbias}
C {devices/lab_pin.sym} 700 70 0 0 {name=l17 sig_type=std_logic lab=pcasc}
C {sg13g2_pr/sg13_hv_nmos.sym} 860 40 0 0 {name=MNC1 w=20u l=1u ng=1 m=1 mm_ok=1 model=sg13_hv_nmos spiceprefix=X}
C {devices/lab_pin.sym} 880 10 0 0 {name=l18 sig_type=std_logic lab=n1}
C {devices/lab_pin.sym} 840 40 0 0 {name=l19 sig_type=std_logic lab=vb2}
C {devices/lab_pin.sym} 880 70 0 0 {name=l20 sig_type=std_logic lab=vbe}
C {devices/lab_pin.sym} 880 40 0 0 {name=l21 sig_type=std_logic lab=vss}
C {sg13g2_pr/sg13_hv_nmos.sym} 1020 40 0 0 {name=MNC2 w=20u l=1u ng=1 m=1 mm_ok=1 model=sg13_hv_nmos spiceprefix=X}
C {devices/lab_pin.sym} 1040 10 0 0 {name=l22 sig_type=std_logic lab=pcasc}
C {devices/lab_pin.sym} 1000 40 0 0 {name=l23 sig_type=std_logic lab=vb2}
C {devices/lab_pin.sym} 1040 70 0 0 {name=l24 sig_type=std_logic lab=c2}
C {devices/lab_pin.sym} 1040 40 0 0 {name=l25 sig_type=std_logic lab=vss}
C {sg13g2_pr/sg13_hv_pmos.sym} 1180 40 0 0 {name=MP5 w=10u l=4u ng=1 m=1 mm_ok=1 model=sg13_hv_pmos spiceprefix=X}
C {devices/lab_pin.sym} 1200 70 0 0 {name=l26 sig_type=std_logic lab=d5}
C {devices/lab_pin.sym} 1160 40 0 0 {name=l27 sig_type=std_logic lab=pbias}
C {devices/lab_pin.sym} 1200 10 0 0 {name=l28 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 1200 40 0 0 {name=l29 sig_type=std_logic lab=vdd}
C {sg13g2_pr/sg13_hv_pmos.sym} 60 180 0 0 {name=MC5 w=10u l=4u ng=1 m=1 mm_ok=1 model=sg13_hv_pmos spiceprefix=X}
C {devices/lab_pin.sym} 80 210 0 0 {name=l30 sig_type=std_logic lab=vb2}
C {devices/lab_pin.sym} 40 180 0 0 {name=l31 sig_type=std_logic lab=pcasc}
C {devices/lab_pin.sym} 80 150 0 0 {name=l32 sig_type=std_logic lab=d5}
C {devices/lab_pin.sym} 80 180 0 0 {name=l33 sig_type=std_logic lab=d5}
C {sg13g2_pr/rppd.sym} 220 180 0 0 {name=RX w=1u l=192u model=rppd body=sub! spiceprefix=X b=0 m=1 mm_ok=1}
C {devices/lab_pin.sym} 220 150 0 0 {name=l34 sig_type=std_logic lab=vb2}
C {devices/lab_pin.sym} 220 210 0 0 {name=l35 sig_type=std_logic lab=vd1}
C {sg13g2_pr/npn13G2.sym} 380 180 0 0 {name=QD1 model=npn13G2 spiceprefix=X Nx=1 mm_ok=1}
C {devices/lab_pin.sym} 400 150 0 0 {name=l36 sig_type=std_logic lab=vd1}
C {devices/lab_pin.sym} 360 180 0 0 {name=l37 sig_type=std_logic lab=vd1}
C {devices/lab_pin.sym} 400 210 0 0 {name=l38 sig_type=std_logic lab=vd2}
C {devices/lab_pin.sym} 400 180 0 0 {name=l39 sig_type=std_logic lab=vss}
C {sg13g2_pr/npn13G2.sym} 540 180 0 0 {name=QD2 model=npn13G2 spiceprefix=X Nx=1 mm_ok=1}
C {devices/lab_pin.sym} 560 150 0 0 {name=l40 sig_type=std_logic lab=vd2}
C {devices/lab_pin.sym} 520 180 0 0 {name=l41 sig_type=std_logic lab=vd2}
C {devices/lab_pin.sym} 560 210 0 0 {name=l42 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 560 180 0 0 {name=l43 sig_type=std_logic lab=vss}
C {sg13g2_pr/npn13G2.sym} 700 180 0 0 {name=Q1 model=npn13G2 spiceprefix=X Nx=1 mm_ok=1}
C {devices/lab_pin.sym} 720 150 0 0 {name=l44 sig_type=std_logic lab=vbe}
C {devices/lab_pin.sym} 680 180 0 0 {name=l45 sig_type=std_logic lab=vbe}
C {devices/lab_pin.sym} 720 210 0 0 {name=l46 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 720 180 0 0 {name=l47 sig_type=std_logic lab=vss}
C {sg13g2_pr/npn13G2.sym} 860 180 0 0 {name=Q1B model=npn13G2 spiceprefix=X Nx=1 mm_ok=1}
C {devices/lab_pin.sym} 880 150 0 0 {name=l48 sig_type=std_logic lab=vbe}
C {devices/lab_pin.sym} 840 180 0 0 {name=l49 sig_type=std_logic lab=b1b}
C {devices/lab_pin.sym} 880 210 0 0 {name=l50 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 880 180 0 0 {name=l51 sig_type=std_logic lab=vss}
C {sg13g2_pr/npn13G2.sym} 1020 180 0 0 {name=Q2A model=npn13G2 spiceprefix=X Nx=1 mm_ok=1}
C {devices/lab_pin.sym} 1040 150 0 0 {name=l52 sig_type=std_logic lab=c2}
C {devices/lab_pin.sym} 1000 180 0 0 {name=l53 sig_type=std_logic lab=vbe}
C {devices/lab_pin.sym} 1040 210 0 0 {name=l54 sig_type=std_logic lab=dvbe}
C {devices/lab_pin.sym} 1040 180 0 0 {name=l55 sig_type=std_logic lab=vss}
C {sg13g2_pr/npn13G2.sym} 1180 180 0 0 {name=Q2B model=npn13G2 spiceprefix=X Nx=1 mm_ok=1}
C {devices/lab_pin.sym} 1200 150 0 0 {name=l56 sig_type=std_logic lab=c2}
C {devices/lab_pin.sym} 1160 180 0 0 {name=l57 sig_type=std_logic lab=vbe}
C {devices/lab_pin.sym} 1200 210 0 0 {name=l58 sig_type=std_logic lab=dvbe}
C {devices/lab_pin.sym} 1200 180 0 0 {name=l59 sig_type=std_logic lab=vss}
C {sg13g2_pr/npn13G2.sym} 60 320 0 0 {name=Q2C model=npn13G2 spiceprefix=X Nx=1 mm_ok=1}
C {devices/lab_pin.sym} 80 290 0 0 {name=l60 sig_type=std_logic lab=c2}
C {devices/lab_pin.sym} 40 320 0 0 {name=l61 sig_type=std_logic lab=vbe}
C {devices/lab_pin.sym} 80 350 0 0 {name=l62 sig_type=std_logic lab=dvbe}
C {devices/lab_pin.sym} 80 320 0 0 {name=l63 sig_type=std_logic lab=vss}
C {sg13g2_pr/npn13G2.sym} 220 320 0 0 {name=Q2D model=npn13G2 spiceprefix=X Nx=1 mm_ok=1}
C {devices/lab_pin.sym} 240 290 0 0 {name=l64 sig_type=std_logic lab=c2}
C {devices/lab_pin.sym} 200 320 0 0 {name=l65 sig_type=std_logic lab=vbe}
C {devices/lab_pin.sym} 240 350 0 0 {name=l66 sig_type=std_logic lab=dvbe}
C {devices/lab_pin.sym} 240 320 0 0 {name=l67 sig_type=std_logic lab=vss}
C {sg13g2_pr/npn13G2.sym} 380 320 0 0 {name=Q2E model=npn13G2 spiceprefix=X Nx=1 mm_ok=1}
C {devices/lab_pin.sym} 400 290 0 0 {name=l68 sig_type=std_logic lab=c2}
C {devices/lab_pin.sym} 360 320 0 0 {name=l69 sig_type=std_logic lab=vbe}
C {devices/lab_pin.sym} 400 350 0 0 {name=l70 sig_type=std_logic lab=dvbe}
C {devices/lab_pin.sym} 400 320 0 0 {name=l71 sig_type=std_logic lab=vss}
C {sg13g2_pr/npn13G2.sym} 540 320 0 0 {name=Q2F model=npn13G2 spiceprefix=X Nx=1 mm_ok=1}
C {devices/lab_pin.sym} 560 290 0 0 {name=l72 sig_type=std_logic lab=c2}
C {devices/lab_pin.sym} 520 320 0 0 {name=l73 sig_type=std_logic lab=vbe}
C {devices/lab_pin.sym} 560 350 0 0 {name=l74 sig_type=std_logic lab=dvbe}
C {devices/lab_pin.sym} 560 320 0 0 {name=l75 sig_type=std_logic lab=vss}
C {sg13g2_pr/npn13G2.sym} 700 320 0 0 {name=Q2G model=npn13G2 spiceprefix=X Nx=1 mm_ok=1}
C {devices/lab_pin.sym} 720 290 0 0 {name=l76 sig_type=std_logic lab=c2}
C {devices/lab_pin.sym} 680 320 0 0 {name=l77 sig_type=std_logic lab=vbe}
C {devices/lab_pin.sym} 720 350 0 0 {name=l78 sig_type=std_logic lab=dvbe}
C {devices/lab_pin.sym} 720 320 0 0 {name=l79 sig_type=std_logic lab=vss}
C {sg13g2_pr/npn13G2.sym} 860 320 0 0 {name=Q2H model=npn13G2 spiceprefix=X Nx=1 mm_ok=1}
C {devices/lab_pin.sym} 880 290 0 0 {name=l80 sig_type=std_logic lab=c2}
C {devices/lab_pin.sym} 840 320 0 0 {name=l81 sig_type=std_logic lab=vbe}
C {devices/lab_pin.sym} 880 350 0 0 {name=l82 sig_type=std_logic lab=dvbe}
C {devices/lab_pin.sym} 880 320 0 0 {name=l83 sig_type=std_logic lab=vss}
C {sg13g2_pr/rppd.sym} 1020 320 0 0 {name=R1 w=1u l=51.5u model=rppd body=sub! spiceprefix=X b=0 m=1 mm_ok=1}
C {devices/lab_pin.sym} 1020 290 0 0 {name=l84 sig_type=std_logic lab=dvbe}
C {devices/lab_pin.sym} 1020 350 0 0 {name=l85 sig_type=std_logic lab=vss}
C {sg13g2_pr/sg13_hv_pmos.sym} 1180 320 0 0 {name=MP3 w=10u l=4u ng=1 m=1 mm_ok=1 model=sg13_hv_pmos spiceprefix=X}
C {devices/lab_pin.sym} 1200 350 0 0 {name=l86 sig_type=std_logic lab=d3}
C {devices/lab_pin.sym} 1160 320 0 0 {name=l87 sig_type=std_logic lab=pbias}
C {devices/lab_pin.sym} 1200 290 0 0 {name=l88 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 1200 320 0 0 {name=l89 sig_type=std_logic lab=vdd}
C {sg13g2_pr/sg13_hv_pmos.sym} 60 460 0 0 {name=MC3 w=10u l=4u ng=1 m=1 mm_ok=1 model=sg13_hv_pmos spiceprefix=X}
C {devices/lab_pin.sym} 80 490 0 0 {name=l90 sig_type=std_logic lab=vref}
C {devices/lab_pin.sym} 40 460 0 0 {name=l91 sig_type=std_logic lab=pcasc}
C {devices/lab_pin.sym} 80 430 0 0 {name=l92 sig_type=std_logic lab=d3}
C {devices/lab_pin.sym} 80 460 0 0 {name=l93 sig_type=std_logic lab=d3}
C {sg13g2_pr/rppd.sym} 220 460 0 0 {name=R2 w=1u l=315u model=rppd body=sub! spiceprefix=X b=0 m=1 mm_ok=1}
C {devices/lab_pin.sym} 220 430 0 0 {name=l94 sig_type=std_logic lab=vref}
C {devices/lab_pin.sym} 220 490 0 0 {name=l95 sig_type=std_logic lab=vbe3}
C {sg13g2_pr/npn13G2.sym} 380 460 0 0 {name=Q3 model=npn13G2 spiceprefix=X Nx=1 mm_ok=1}
C {devices/lab_pin.sym} 400 430 0 0 {name=l96 sig_type=std_logic lab=vbe3}
C {devices/lab_pin.sym} 360 460 0 0 {name=l97 sig_type=std_logic lab=vbe3}
C {devices/lab_pin.sym} 400 490 0 0 {name=l98 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 400 460 0 0 {name=l99 sig_type=std_logic lab=vss}
C {sg13g2_pr/sg13_hv_pmos.sym} 540 460 0 0 {name=MP4 w=10u l=4u ng=1 m=1 mm_ok=1 model=sg13_hv_pmos spiceprefix=X}
C {devices/lab_pin.sym} 560 490 0 0 {name=l100 sig_type=std_logic lab=d4}
C {devices/lab_pin.sym} 520 460 0 0 {name=l101 sig_type=std_logic lab=pbias}
C {devices/lab_pin.sym} 560 430 0 0 {name=l102 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 560 460 0 0 {name=l103 sig_type=std_logic lab=vdd}
C {sg13g2_pr/sg13_hv_pmos.sym} 700 460 0 0 {name=MC4 w=10u l=4u ng=1 m=1 mm_ok=1 model=sg13_hv_pmos spiceprefix=X}
C {devices/lab_pin.sym} 720 490 0 0 {name=l104 sig_type=std_logic lab=iptat}
C {devices/lab_pin.sym} 680 460 0 0 {name=l105 sig_type=std_logic lab=pcasc}
C {devices/lab_pin.sym} 720 430 0 0 {name=l106 sig_type=std_logic lab=d4}
C {devices/lab_pin.sym} 720 460 0 0 {name=l107 sig_type=std_logic lab=d4}
C {sg13g2_pr/sg13_hv_pmos.sym} 860 460 0 0 {name=MPS w=10u l=4u ng=1 m=1 mm_ok=1 model=sg13_hv_pmos spiceprefix=X}
C {devices/lab_pin.sym} 880 490 0 0 {name=l108 sig_type=std_logic lab=det}
C {devices/lab_pin.sym} 840 460 0 0 {name=l109 sig_type=std_logic lab=pbias}
C {devices/lab_pin.sym} 880 430 0 0 {name=l110 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 880 460 0 0 {name=l111 sig_type=std_logic lab=vdd}
C {sg13g2_pr/rhigh.sym} 1020 460 0 0 {name=RDET w=0.5u l=735u model=rhigh body=sub! spiceprefix=X b=0 m=1 mm_ok=1}
C {devices/lab_pin.sym} 1020 430 0 0 {name=l112 sig_type=std_logic lab=det}
C {devices/lab_pin.sym} 1020 490 0 0 {name=l113 sig_type=std_logic lab=vss}
C {sg13g2_pr/sg13_hv_nmos.sym} 1180 460 0 0 {name=MNI w=1u l=0.5u ng=1 m=1 mm_ok=1 model=sg13_hv_nmos spiceprefix=X}
C {devices/lab_pin.sym} 1200 430 0 0 {name=l114 sig_type=std_logic lab=kick}
C {devices/lab_pin.sym} 1160 460 0 0 {name=l115 sig_type=std_logic lab=det}
C {devices/lab_pin.sym} 1200 490 0 0 {name=l116 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 1200 460 0 0 {name=l117 sig_type=std_logic lab=vss}
C {sg13g2_pr/sg13_hv_pmos.sym} 60 600 0 0 {name=MPI w=2u l=0.5u ng=1 m=1 mm_ok=1 model=sg13_hv_pmos spiceprefix=X}
C {devices/lab_pin.sym} 80 630 0 0 {name=l118 sig_type=std_logic lab=kick}
C {devices/lab_pin.sym} 40 600 0 0 {name=l119 sig_type=std_logic lab=det}
C {devices/lab_pin.sym} 80 570 0 0 {name=l120 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 80 600 0 0 {name=l121 sig_type=std_logic lab=vdd}
C {sg13g2_pr/sg13_hv_nmos.sym} 220 600 0 0 {name=MKFB w=1u l=4u ng=1 m=1 mm_ok=1 model=sg13_hv_nmos spiceprefix=X}
C {devices/lab_pin.sym} 240 570 0 0 {name=l122 sig_type=std_logic lab=pbias}
C {devices/lab_pin.sym} 200 600 0 0 {name=l123 sig_type=std_logic lab=kick}
C {devices/lab_pin.sym} 240 630 0 0 {name=l124 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 240 600 0 0 {name=l125 sig_type=std_logic lab=vss}
C {sg13g2_pr/sg13_hv_nmos.sym} 380 600 0 0 {name=MSW1 w=2u l=0.5u ng=1 m=1 mm_ok=1 model=sg13_hv_nmos spiceprefix=X}
C {devices/lab_pin.sym} 400 570 0 0 {name=l126 sig_type=std_logic lab=vbe}
C {devices/lab_pin.sym} 360 600 0 0 {name=l127 sig_type=std_logic lab=r4}
C {devices/lab_pin.sym} 400 630 0 0 {name=l128 sig_type=std_logic lab=b1b}
C {devices/lab_pin.sym} 400 600 0 0 {name=l129 sig_type=std_logic lab=vss}
C {sg13g2_pr/sg13_hv_nmos.sym} 540 600 0 0 {name=MSW2 w=1u l=0.5u ng=1 m=1 mm_ok=1 model=sg13_hv_nmos spiceprefix=X}
C {devices/lab_pin.sym} 560 570 0 0 {name=l130 sig_type=std_logic lab=b1b}
C {devices/lab_pin.sym} 520 600 0 0 {name=l131 sig_type=std_logic lab=r4n}
C {devices/lab_pin.sym} 560 630 0 0 {name=l132 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 560 600 0 0 {name=l133 sig_type=std_logic lab=vss}
C {sg13g2_pr/sg13_hv_nmos.sym} 700 600 0 0 {name=MNI2 w=1u l=0.5u ng=1 m=1 mm_ok=1 model=sg13_hv_nmos spiceprefix=X}
C {devices/lab_pin.sym} 720 570 0 0 {name=l134 sig_type=std_logic lab=r4n}
C {devices/lab_pin.sym} 680 600 0 0 {name=l135 sig_type=std_logic lab=r4}
C {devices/lab_pin.sym} 720 630 0 0 {name=l136 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 720 600 0 0 {name=l137 sig_type=std_logic lab=vss}
C {sg13g2_pr/sg13_hv_pmos.sym} 860 600 0 0 {name=MPI2 w=2u l=0.5u ng=1 m=1 mm_ok=1 model=sg13_hv_pmos spiceprefix=X}
C {devices/lab_pin.sym} 880 630 0 0 {name=l138 sig_type=std_logic lab=r4n}
C {devices/lab_pin.sym} 840 600 0 0 {name=l139 sig_type=std_logic lab=r4}
C {devices/lab_pin.sym} 880 570 0 0 {name=l140 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 880 600 0 0 {name=l141 sig_type=std_logic lab=vdd}

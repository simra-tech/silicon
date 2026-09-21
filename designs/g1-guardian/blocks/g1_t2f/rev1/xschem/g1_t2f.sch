v {xschem version=3.4.8RC file_version=1.3}
G {}
K {}
V {}
S {}
E {}
T {G1_T2F: I_PTAT relaxation oscillator, VREF or I_PTAT*R threshold, 1.2 V output} 0 -220 0 0 0.4 0.4 {}
C {devices/iopin.sym} 0 -160 0 0 {name=p0 lab=vdd}
C {devices/iopin.sym} 80 -160 0 0 {name=p1 lab=vdd12}
C {devices/iopin.sym} 160 -160 0 0 {name=p2 lab=vss}
C {devices/ipin.sym} 240 -160 0 0 {name=p3 lab=pbias}
C {devices/ipin.sym} 320 -160 0 0 {name=p4 lab=pcasc}
C {devices/ipin.sym} 400 -160 0 0 {name=p5 lab=vref}
C {devices/ipin.sym} 480 -160 0 0 {name=p6 lab=en}
C {devices/ipin.sym} 560 -160 0 0 {name=p7 lab=mode}
C {devices/opin.sym} 640 -160 0 0 {name=p8 lab=fout}
C {sg13g2_pr/sg13_hv_pmos.sym} 60 40 0 0 {name=MPO w=10u l=4u ng=1 m=1 mm_ok=1 model=sg13_hv_pmos spiceprefix=X}
C {devices/lab_pin.sym} 80 70 0 0 {name=l0 sig_type=std_logic lab=do}
C {devices/lab_pin.sym} 40 40 0 0 {name=l1 sig_type=std_logic lab=pbias}
C {devices/lab_pin.sym} 80 10 0 0 {name=l2 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 80 40 0 0 {name=l3 sig_type=std_logic lab=vdd}
C {sg13g2_pr/sg13_hv_pmos.sym} 220 40 0 0 {name=MCO w=10u l=4u ng=1 m=1 mm_ok=1 model=sg13_hv_pmos spiceprefix=X}
C {devices/lab_pin.sym} 240 70 0 0 {name=l4 sig_type=std_logic lab=isrc}
C {devices/lab_pin.sym} 200 40 0 0 {name=l5 sig_type=std_logic lab=pcasc}
C {devices/lab_pin.sym} 240 10 0 0 {name=l6 sig_type=std_logic lab=do}
C {devices/lab_pin.sym} 240 40 0 0 {name=l7 sig_type=std_logic lab=do}
C {sg13g2_pr/sg13_hv_pmos.sym} 380 40 0 0 {name=MPR w=10u l=4u ng=1 m=2 mm_ok=1 model=sg13_hv_pmos spiceprefix=X}
C {devices/lab_pin.sym} 400 70 0 0 {name=l8 sig_type=std_logic lab=dr}
C {devices/lab_pin.sym} 360 40 0 0 {name=l9 sig_type=std_logic lab=pbias}
C {devices/lab_pin.sym} 400 10 0 0 {name=l10 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 400 40 0 0 {name=l11 sig_type=std_logic lab=vdd}
C {sg13g2_pr/sg13_hv_pmos.sym} 540 40 0 0 {name=MCR w=10u l=4u ng=1 m=2 mm_ok=1 model=sg13_hv_pmos spiceprefix=X}
C {devices/lab_pin.sym} 560 70 0 0 {name=l12 sig_type=std_logic lab=vr}
C {devices/lab_pin.sym} 520 40 0 0 {name=l13 sig_type=std_logic lab=pcasc}
C {devices/lab_pin.sym} 560 10 0 0 {name=l14 sig_type=std_logic lab=dr}
C {devices/lab_pin.sym} 560 40 0 0 {name=l15 sig_type=std_logic lab=dr}
C {sg13g2_pr/rppd.sym} 700 40 0 0 {name=RREF w=0.5u l=245u model=rppd body=sub! spiceprefix=X b=0 m=1 mm_ok=1}
C {devices/lab_pin.sym} 700 10 0 0 {name=l16 sig_type=std_logic lab=vr}
C {devices/lab_pin.sym} 700 70 0 0 {name=l17 sig_type=std_logic lab=vss}
C {sg13g2_pr/sg13_hv_pmos.sym} 860 40 0 0 {name=MPB w=10u l=4u ng=1 m=1 mm_ok=1 model=sg13_hv_pmos spiceprefix=X}
C {devices/lab_pin.sym} 880 70 0 0 {name=l18 sig_type=std_logic lab=db}
C {devices/lab_pin.sym} 840 40 0 0 {name=l19 sig_type=std_logic lab=pbias}
C {devices/lab_pin.sym} 880 10 0 0 {name=l20 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 880 40 0 0 {name=l21 sig_type=std_logic lab=vdd}
C {sg13g2_pr/sg13_hv_pmos.sym} 1020 40 0 0 {name=MCB w=10u l=4u ng=1 m=1 mm_ok=1 model=sg13_hv_pmos spiceprefix=X}
C {devices/lab_pin.sym} 1040 70 0 0 {name=l22 sig_type=std_logic lab=nbias}
C {devices/lab_pin.sym} 1000 40 0 0 {name=l23 sig_type=std_logic lab=pcasc}
C {devices/lab_pin.sym} 1040 10 0 0 {name=l24 sig_type=std_logic lab=db}
C {devices/lab_pin.sym} 1040 40 0 0 {name=l25 sig_type=std_logic lab=db}
C {sg13g2_pr/sg13_hv_nmos.sym} 1180 40 0 0 {name=MNB w=10u l=2u ng=1 m=1 mm_ok=1 model=sg13_hv_nmos spiceprefix=X}
C {devices/lab_pin.sym} 1200 10 0 0 {name=l26 sig_type=std_logic lab=nbias}
C {devices/lab_pin.sym} 1160 40 0 0 {name=l27 sig_type=std_logic lab=nbias}
C {devices/lab_pin.sym} 1200 70 0 0 {name=l28 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 1200 40 0 0 {name=l29 sig_type=std_logic lab=vss}
C {sg13g2_pr/sg13_hv_nmos.sym} 60 180 0 0 {name=MX1 w=4u l=0.5u ng=1 m=1 mm_ok=1 model=sg13_hv_nmos spiceprefix=X}
C {devices/lab_pin.sym} 80 150 0 0 {name=l30 sig_type=std_logic lab=vref}
C {devices/lab_pin.sym} 40 180 0 0 {name=l31 sig_type=std_logic lab=moden}
C {devices/lab_pin.sym} 80 210 0 0 {name=l32 sig_type=std_logic lab=vth}
C {devices/lab_pin.sym} 80 180 0 0 {name=l33 sig_type=std_logic lab=vss}
C {sg13g2_pr/sg13_hv_nmos.sym} 220 180 0 0 {name=MX2 w=4u l=0.5u ng=1 m=1 mm_ok=1 model=sg13_hv_nmos spiceprefix=X}
C {devices/lab_pin.sym} 240 150 0 0 {name=l34 sig_type=std_logic lab=vr}
C {devices/lab_pin.sym} 200 180 0 0 {name=l35 sig_type=std_logic lab=mode}
C {devices/lab_pin.sym} 240 210 0 0 {name=l36 sig_type=std_logic lab=vth}
C {devices/lab_pin.sym} 240 180 0 0 {name=l37 sig_type=std_logic lab=vss}
C {sg13g2_pr/sg13_hv_nmos.sym} 380 180 0 0 {name=IMN w=1u l=0.5u ng=1 m=1 mm_ok=1 model=sg13_hv_nmos spiceprefix=X}
C {devices/lab_pin.sym} 400 150 0 0 {name=l38 sig_type=std_logic lab=moden}
C {devices/lab_pin.sym} 360 180 0 0 {name=l39 sig_type=std_logic lab=mode}
C {devices/lab_pin.sym} 400 210 0 0 {name=l40 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 400 180 0 0 {name=l41 sig_type=std_logic lab=vss}
C {sg13g2_pr/sg13_hv_pmos.sym} 540 180 0 0 {name=IMP w=2u l=0.5u ng=1 m=1 mm_ok=1 model=sg13_hv_pmos spiceprefix=X}
C {devices/lab_pin.sym} 560 210 0 0 {name=l42 sig_type=std_logic lab=moden}
C {devices/lab_pin.sym} 520 180 0 0 {name=l43 sig_type=std_logic lab=mode}
C {devices/lab_pin.sym} 560 150 0 0 {name=l44 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 560 180 0 0 {name=l45 sig_type=std_logic lab=vdd}
C {sg13g2_pr/npn13G2.sym} 700 180 0 0 {name=QA1 model=npn13G2 spiceprefix=X Nx=1 mm_ok=1}
C {devices/lab_pin.sym} 720 150 0 0 {name=l46 sig_type=std_logic lab=oa1}
C {devices/lab_pin.sym} 680 180 0 0 {name=l47 sig_type=std_logic lab=vth}
C {devices/lab_pin.sym} 720 210 0 0 {name=l48 sig_type=std_logic lab=tail1}
C {devices/lab_pin.sym} 720 180 0 0 {name=l49 sig_type=std_logic lab=vss}
C {sg13g2_pr/npn13G2.sym} 860 180 0 0 {name=QB1 model=npn13G2 spiceprefix=X Nx=1 mm_ok=1}
C {devices/lab_pin.sym} 880 150 0 0 {name=l50 sig_type=std_logic lab=ob1}
C {devices/lab_pin.sym} 840 180 0 0 {name=l51 sig_type=std_logic lab=cap1}
C {devices/lab_pin.sym} 880 210 0 0 {name=l52 sig_type=std_logic lab=tail1}
C {devices/lab_pin.sym} 880 180 0 0 {name=l53 sig_type=std_logic lab=vss}
C {sg13g2_pr/sg13_hv_pmos.sym} 1020 180 0 0 {name=MLA1 w=4u l=1u ng=1 m=1 mm_ok=1 model=sg13_hv_pmos spiceprefix=X}
C {devices/lab_pin.sym} 1040 210 0 0 {name=l54 sig_type=std_logic lab=oa1}
C {devices/lab_pin.sym} 1000 180 0 0 {name=l55 sig_type=std_logic lab=oa1}
C {devices/lab_pin.sym} 1040 150 0 0 {name=l56 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 1040 180 0 0 {name=l57 sig_type=std_logic lab=vdd}
C {sg13g2_pr/sg13_hv_pmos.sym} 1180 180 0 0 {name=MLB1 w=4u l=1u ng=1 m=1 mm_ok=1 model=sg13_hv_pmos spiceprefix=X}
C {devices/lab_pin.sym} 1200 210 0 0 {name=l58 sig_type=std_logic lab=ob1}
C {devices/lab_pin.sym} 1160 180 0 0 {name=l59 sig_type=std_logic lab=oa1}
C {devices/lab_pin.sym} 1200 150 0 0 {name=l60 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 1200 180 0 0 {name=l61 sig_type=std_logic lab=vdd}
C {sg13g2_pr/sg13_hv_nmos.sym} 60 320 0 0 {name=MT1 w=20u l=2u ng=1 m=1 mm_ok=1 model=sg13_hv_nmos spiceprefix=X}
C {devices/lab_pin.sym} 80 290 0 0 {name=l62 sig_type=std_logic lab=tail1}
C {devices/lab_pin.sym} 40 320 0 0 {name=l63 sig_type=std_logic lab=nbias}
C {devices/lab_pin.sym} 80 350 0 0 {name=l64 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 80 320 0 0 {name=l65 sig_type=std_logic lab=vss}
C {sg13g2_pr/sg13_hv_nmos.sym} 220 320 0 0 {name=IC1AN w=1u l=0.5u ng=1 m=1 mm_ok=1 model=sg13_hv_nmos spiceprefix=X}
C {devices/lab_pin.sym} 240 290 0 0 {name=l66 sig_type=std_logic lab=c1}
C {devices/lab_pin.sym} 200 320 0 0 {name=l67 sig_type=std_logic lab=ob1}
C {devices/lab_pin.sym} 240 350 0 0 {name=l68 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 240 320 0 0 {name=l69 sig_type=std_logic lab=vss}
C {sg13g2_pr/sg13_hv_pmos.sym} 380 320 0 0 {name=IC1AP w=2u l=0.5u ng=1 m=1 mm_ok=1 model=sg13_hv_pmos spiceprefix=X}
C {devices/lab_pin.sym} 400 350 0 0 {name=l70 sig_type=std_logic lab=c1}
C {devices/lab_pin.sym} 360 320 0 0 {name=l71 sig_type=std_logic lab=ob1}
C {devices/lab_pin.sym} 400 290 0 0 {name=l72 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 400 320 0 0 {name=l73 sig_type=std_logic lab=vdd}
C {sg13g2_pr/sg13_hv_nmos.sym} 540 320 0 0 {name=IC1BN w=2u l=0.5u ng=1 m=1 mm_ok=1 model=sg13_hv_nmos spiceprefix=X}
C {devices/lab_pin.sym} 560 290 0 0 {name=l74 sig_type=std_logic lab=sn}
C {devices/lab_pin.sym} 520 320 0 0 {name=l75 sig_type=std_logic lab=c1}
C {devices/lab_pin.sym} 560 350 0 0 {name=l76 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 560 320 0 0 {name=l77 sig_type=std_logic lab=vss}
C {sg13g2_pr/sg13_hv_pmos.sym} 700 320 0 0 {name=IC1BP w=4u l=0.5u ng=1 m=1 mm_ok=1 model=sg13_hv_pmos spiceprefix=X}
C {devices/lab_pin.sym} 720 350 0 0 {name=l78 sig_type=std_logic lab=sn}
C {devices/lab_pin.sym} 680 320 0 0 {name=l79 sig_type=std_logic lab=c1}
C {devices/lab_pin.sym} 720 290 0 0 {name=l80 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 720 320 0 0 {name=l81 sig_type=std_logic lab=vdd}
C {sg13g2_pr/npn13G2.sym} 860 320 0 0 {name=QA2 model=npn13G2 spiceprefix=X Nx=1 mm_ok=1}
C {devices/lab_pin.sym} 880 290 0 0 {name=l82 sig_type=std_logic lab=oa2}
C {devices/lab_pin.sym} 840 320 0 0 {name=l83 sig_type=std_logic lab=vth}
C {devices/lab_pin.sym} 880 350 0 0 {name=l84 sig_type=std_logic lab=tail2}
C {devices/lab_pin.sym} 880 320 0 0 {name=l85 sig_type=std_logic lab=vss}
C {sg13g2_pr/npn13G2.sym} 1020 320 0 0 {name=QB2 model=npn13G2 spiceprefix=X Nx=1 mm_ok=1}
C {devices/lab_pin.sym} 1040 290 0 0 {name=l86 sig_type=std_logic lab=ob2}
C {devices/lab_pin.sym} 1000 320 0 0 {name=l87 sig_type=std_logic lab=cap2}
C {devices/lab_pin.sym} 1040 350 0 0 {name=l88 sig_type=std_logic lab=tail2}
C {devices/lab_pin.sym} 1040 320 0 0 {name=l89 sig_type=std_logic lab=vss}
C {sg13g2_pr/sg13_hv_pmos.sym} 1180 320 0 0 {name=MLA2 w=4u l=1u ng=1 m=1 mm_ok=1 model=sg13_hv_pmos spiceprefix=X}
C {devices/lab_pin.sym} 1200 350 0 0 {name=l90 sig_type=std_logic lab=oa2}
C {devices/lab_pin.sym} 1160 320 0 0 {name=l91 sig_type=std_logic lab=oa2}
C {devices/lab_pin.sym} 1200 290 0 0 {name=l92 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 1200 320 0 0 {name=l93 sig_type=std_logic lab=vdd}
C {sg13g2_pr/sg13_hv_pmos.sym} 60 460 0 0 {name=MLB2 w=4u l=1u ng=1 m=1 mm_ok=1 model=sg13_hv_pmos spiceprefix=X}
C {devices/lab_pin.sym} 80 490 0 0 {name=l94 sig_type=std_logic lab=ob2}
C {devices/lab_pin.sym} 40 460 0 0 {name=l95 sig_type=std_logic lab=oa2}
C {devices/lab_pin.sym} 80 430 0 0 {name=l96 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 80 460 0 0 {name=l97 sig_type=std_logic lab=vdd}
C {sg13g2_pr/sg13_hv_nmos.sym} 220 460 0 0 {name=MT2 w=20u l=2u ng=1 m=1 mm_ok=1 model=sg13_hv_nmos spiceprefix=X}
C {devices/lab_pin.sym} 240 430 0 0 {name=l98 sig_type=std_logic lab=tail2}
C {devices/lab_pin.sym} 200 460 0 0 {name=l99 sig_type=std_logic lab=nbias}
C {devices/lab_pin.sym} 240 490 0 0 {name=l100 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 240 460 0 0 {name=l101 sig_type=std_logic lab=vss}
C {sg13g2_pr/sg13_hv_nmos.sym} 380 460 0 0 {name=IC2AN w=1u l=0.5u ng=1 m=1 mm_ok=1 model=sg13_hv_nmos spiceprefix=X}
C {devices/lab_pin.sym} 400 430 0 0 {name=l102 sig_type=std_logic lab=c2}
C {devices/lab_pin.sym} 360 460 0 0 {name=l103 sig_type=std_logic lab=ob2}
C {devices/lab_pin.sym} 400 490 0 0 {name=l104 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 400 460 0 0 {name=l105 sig_type=std_logic lab=vss}
C {sg13g2_pr/sg13_hv_pmos.sym} 540 460 0 0 {name=IC2AP w=2u l=0.5u ng=1 m=1 mm_ok=1 model=sg13_hv_pmos spiceprefix=X}
C {devices/lab_pin.sym} 560 490 0 0 {name=l106 sig_type=std_logic lab=c2}
C {devices/lab_pin.sym} 520 460 0 0 {name=l107 sig_type=std_logic lab=ob2}
C {devices/lab_pin.sym} 560 430 0 0 {name=l108 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 560 460 0 0 {name=l109 sig_type=std_logic lab=vdd}
C {sg13g2_pr/sg13_hv_nmos.sym} 700 460 0 0 {name=IC2BN w=2u l=0.5u ng=1 m=1 mm_ok=1 model=sg13_hv_nmos spiceprefix=X}
C {devices/lab_pin.sym} 720 430 0 0 {name=l110 sig_type=std_logic lab=rn}
C {devices/lab_pin.sym} 680 460 0 0 {name=l111 sig_type=std_logic lab=c2}
C {devices/lab_pin.sym} 720 490 0 0 {name=l112 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 720 460 0 0 {name=l113 sig_type=std_logic lab=vss}
C {sg13g2_pr/sg13_hv_pmos.sym} 860 460 0 0 {name=IC2BP w=4u l=0.5u ng=1 m=1 mm_ok=1 model=sg13_hv_pmos spiceprefix=X}
C {devices/lab_pin.sym} 880 490 0 0 {name=l114 sig_type=std_logic lab=rn}
C {devices/lab_pin.sym} 840 460 0 0 {name=l115 sig_type=std_logic lab=c2}
C {devices/lab_pin.sym} 880 430 0 0 {name=l116 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 880 460 0 0 {name=l117 sig_type=std_logic lab=vdd}
C {sg13g2_pr/sg13_hv_pmos.sym} 1020 460 0 0 {name=NQPA w=2u l=0.5u ng=1 m=1 mm_ok=1 model=sg13_hv_pmos spiceprefix=X}
C {devices/lab_pin.sym} 1040 490 0 0 {name=l118 sig_type=std_logic lab=q}
C {devices/lab_pin.sym} 1000 460 0 0 {name=l119 sig_type=std_logic lab=sn}
C {devices/lab_pin.sym} 1040 430 0 0 {name=l120 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 1040 460 0 0 {name=l121 sig_type=std_logic lab=vdd}
C {sg13g2_pr/sg13_hv_pmos.sym} 1180 460 0 0 {name=NQPB w=2u l=0.5u ng=1 m=1 mm_ok=1 model=sg13_hv_pmos spiceprefix=X}
C {devices/lab_pin.sym} 1200 490 0 0 {name=l122 sig_type=std_logic lab=q}
C {devices/lab_pin.sym} 1160 460 0 0 {name=l123 sig_type=std_logic lab=qn}
C {devices/lab_pin.sym} 1200 430 0 0 {name=l124 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 1200 460 0 0 {name=l125 sig_type=std_logic lab=vdd}
C {sg13g2_pr/sg13_hv_nmos.sym} 60 600 0 0 {name=NQNA w=2u l=0.5u ng=1 m=1 mm_ok=1 model=sg13_hv_nmos spiceprefix=X}
C {devices/lab_pin.sym} 80 570 0 0 {name=l126 sig_type=std_logic lab=q}
C {devices/lab_pin.sym} 40 600 0 0 {name=l127 sig_type=std_logic lab=sn}
C {devices/lab_pin.sym} 80 630 0 0 {name=l128 sig_type=std_logic lab=NQ_i}
C {devices/lab_pin.sym} 80 600 0 0 {name=l129 sig_type=std_logic lab=vss}
C {sg13g2_pr/sg13_hv_nmos.sym} 220 600 0 0 {name=NQNB w=2u l=0.5u ng=1 m=1 mm_ok=1 model=sg13_hv_nmos spiceprefix=X}
C {devices/lab_pin.sym} 240 570 0 0 {name=l130 sig_type=std_logic lab=NQ_i}
C {devices/lab_pin.sym} 200 600 0 0 {name=l131 sig_type=std_logic lab=qn}
C {devices/lab_pin.sym} 240 630 0 0 {name=l132 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 240 600 0 0 {name=l133 sig_type=std_logic lab=vss}
C {sg13g2_pr/sg13_hv_pmos.sym} 380 600 0 0 {name=NQNPA w=2u l=0.5u ng=1 m=1 mm_ok=1 model=sg13_hv_pmos spiceprefix=X}
C {devices/lab_pin.sym} 400 630 0 0 {name=l134 sig_type=std_logic lab=qn}
C {devices/lab_pin.sym} 360 600 0 0 {name=l135 sig_type=std_logic lab=rn}
C {devices/lab_pin.sym} 400 570 0 0 {name=l136 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 400 600 0 0 {name=l137 sig_type=std_logic lab=vdd}
C {sg13g2_pr/sg13_hv_pmos.sym} 540 600 0 0 {name=NQNPB w=2u l=0.5u ng=1 m=1 mm_ok=1 model=sg13_hv_pmos spiceprefix=X}
C {devices/lab_pin.sym} 560 630 0 0 {name=l138 sig_type=std_logic lab=qn}
C {devices/lab_pin.sym} 520 600 0 0 {name=l139 sig_type=std_logic lab=q}
C {devices/lab_pin.sym} 560 570 0 0 {name=l140 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 560 600 0 0 {name=l141 sig_type=std_logic lab=vdd}
C {sg13g2_pr/sg13_hv_pmos.sym} 700 600 0 0 {name=NQNPC w=2u l=0.5u ng=1 m=1 mm_ok=1 model=sg13_hv_pmos spiceprefix=X}
C {devices/lab_pin.sym} 720 630 0 0 {name=l142 sig_type=std_logic lab=qn}
C {devices/lab_pin.sym} 680 600 0 0 {name=l143 sig_type=std_logic lab=en}
C {devices/lab_pin.sym} 720 570 0 0 {name=l144 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 720 600 0 0 {name=l145 sig_type=std_logic lab=vdd}
C {sg13g2_pr/sg13_hv_nmos.sym} 860 600 0 0 {name=NQNNA w=3u l=0.5u ng=1 m=1 mm_ok=1 model=sg13_hv_nmos spiceprefix=X}
C {devices/lab_pin.sym} 880 570 0 0 {name=l146 sig_type=std_logic lab=qn}
C {devices/lab_pin.sym} 840 600 0 0 {name=l147 sig_type=std_logic lab=rn}
C {devices/lab_pin.sym} 880 630 0 0 {name=l148 sig_type=std_logic lab=NQN_i}
C {devices/lab_pin.sym} 880 600 0 0 {name=l149 sig_type=std_logic lab=vss}
C {sg13g2_pr/sg13_hv_nmos.sym} 1020 600 0 0 {name=NQNNB w=3u l=0.5u ng=1 m=1 mm_ok=1 model=sg13_hv_nmos spiceprefix=X}
C {devices/lab_pin.sym} 1040 570 0 0 {name=l150 sig_type=std_logic lab=NQN_i}
C {devices/lab_pin.sym} 1000 600 0 0 {name=l151 sig_type=std_logic lab=q}
C {devices/lab_pin.sym} 1040 630 0 0 {name=l152 sig_type=std_logic lab=NQN_j}
C {devices/lab_pin.sym} 1040 600 0 0 {name=l153 sig_type=std_logic lab=vss}
C {sg13g2_pr/sg13_hv_nmos.sym} 1180 600 0 0 {name=NQNNC w=3u l=0.5u ng=1 m=1 mm_ok=1 model=sg13_hv_nmos spiceprefix=X}
C {devices/lab_pin.sym} 1200 570 0 0 {name=l154 sig_type=std_logic lab=NQN_j}
C {devices/lab_pin.sym} 1160 600 0 0 {name=l155 sig_type=std_logic lab=en}
C {devices/lab_pin.sym} 1200 630 0 0 {name=l156 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 1200 600 0 0 {name=l157 sig_type=std_logic lab=vss}
C {sg13g2_pr/sg13_hv_pmos.sym} 60 740 0 0 {name=ND1PA w=2u l=0.5u ng=1 m=1 mm_ok=1 model=sg13_hv_pmos spiceprefix=X}
C {devices/lab_pin.sym} 80 770 0 0 {name=l158 sig_type=std_logic lab=d1g}
C {devices/lab_pin.sym} 40 740 0 0 {name=l159 sig_type=std_logic lab=qn}
C {devices/lab_pin.sym} 80 710 0 0 {name=l160 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 80 740 0 0 {name=l161 sig_type=std_logic lab=vdd}
C {sg13g2_pr/sg13_hv_pmos.sym} 220 740 0 0 {name=ND1PB w=2u l=0.5u ng=1 m=1 mm_ok=1 model=sg13_hv_pmos spiceprefix=X}
C {devices/lab_pin.sym} 240 770 0 0 {name=l162 sig_type=std_logic lab=d1g}
C {devices/lab_pin.sym} 200 740 0 0 {name=l163 sig_type=std_logic lab=en}
C {devices/lab_pin.sym} 240 710 0 0 {name=l164 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 240 740 0 0 {name=l165 sig_type=std_logic lab=vdd}
C {sg13g2_pr/sg13_hv_nmos.sym} 380 740 0 0 {name=ND1NA w=2u l=0.5u ng=1 m=1 mm_ok=1 model=sg13_hv_nmos spiceprefix=X}
C {devices/lab_pin.sym} 400 710 0 0 {name=l166 sig_type=std_logic lab=d1g}
C {devices/lab_pin.sym} 360 740 0 0 {name=l167 sig_type=std_logic lab=qn}
C {devices/lab_pin.sym} 400 770 0 0 {name=l168 sig_type=std_logic lab=ND1_i}
C {devices/lab_pin.sym} 400 740 0 0 {name=l169 sig_type=std_logic lab=vss}
C {sg13g2_pr/sg13_hv_nmos.sym} 540 740 0 0 {name=ND1NB w=2u l=0.5u ng=1 m=1 mm_ok=1 model=sg13_hv_nmos spiceprefix=X}
C {devices/lab_pin.sym} 560 710 0 0 {name=l170 sig_type=std_logic lab=ND1_i}
C {devices/lab_pin.sym} 520 740 0 0 {name=l171 sig_type=std_logic lab=en}
C {devices/lab_pin.sym} 560 770 0 0 {name=l172 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 560 740 0 0 {name=l173 sig_type=std_logic lab=vss}
C {sg13g2_pr/sg13_hv_pmos.sym} 700 740 0 0 {name=ND2PA w=2u l=0.5u ng=1 m=1 mm_ok=1 model=sg13_hv_pmos spiceprefix=X}
C {devices/lab_pin.sym} 720 770 0 0 {name=l174 sig_type=std_logic lab=d2g}
C {devices/lab_pin.sym} 680 740 0 0 {name=l175 sig_type=std_logic lab=q}
C {devices/lab_pin.sym} 720 710 0 0 {name=l176 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 720 740 0 0 {name=l177 sig_type=std_logic lab=vdd}
C {sg13g2_pr/sg13_hv_pmos.sym} 860 740 0 0 {name=ND2PB w=2u l=0.5u ng=1 m=1 mm_ok=1 model=sg13_hv_pmos spiceprefix=X}
C {devices/lab_pin.sym} 880 770 0 0 {name=l178 sig_type=std_logic lab=d2g}
C {devices/lab_pin.sym} 840 740 0 0 {name=l179 sig_type=std_logic lab=en}
C {devices/lab_pin.sym} 880 710 0 0 {name=l180 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 880 740 0 0 {name=l181 sig_type=std_logic lab=vdd}
C {sg13g2_pr/sg13_hv_nmos.sym} 1020 740 0 0 {name=ND2NA w=2u l=0.5u ng=1 m=1 mm_ok=1 model=sg13_hv_nmos spiceprefix=X}
C {devices/lab_pin.sym} 1040 710 0 0 {name=l182 sig_type=std_logic lab=d2g}
C {devices/lab_pin.sym} 1000 740 0 0 {name=l183 sig_type=std_logic lab=q}
C {devices/lab_pin.sym} 1040 770 0 0 {name=l184 sig_type=std_logic lab=ND2_i}
C {devices/lab_pin.sym} 1040 740 0 0 {name=l185 sig_type=std_logic lab=vss}
C {sg13g2_pr/sg13_hv_nmos.sym} 1180 740 0 0 {name=ND2NB w=2u l=0.5u ng=1 m=1 mm_ok=1 model=sg13_hv_nmos spiceprefix=X}
C {devices/lab_pin.sym} 1200 710 0 0 {name=l186 sig_type=std_logic lab=ND2_i}
C {devices/lab_pin.sym} 1160 740 0 0 {name=l187 sig_type=std_logic lab=en}
C {devices/lab_pin.sym} 1200 770 0 0 {name=l188 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 1200 740 0 0 {name=l189 sig_type=std_logic lab=vss}
C {sg13g2_pr/sg13_hv_pmos.sym} 60 880 0 0 {name=SW1 w=4u l=0.5u ng=1 m=1 mm_ok=1 model=sg13_hv_pmos spiceprefix=X}
C {devices/lab_pin.sym} 80 910 0 0 {name=l190 sig_type=std_logic lab=cap1}
C {devices/lab_pin.sym} 40 880 0 0 {name=l191 sig_type=std_logic lab=d1g}
C {devices/lab_pin.sym} 80 850 0 0 {name=l192 sig_type=std_logic lab=isrc}
C {devices/lab_pin.sym} 80 880 0 0 {name=l193 sig_type=std_logic lab=vdd}
C {sg13g2_pr/sg13_hv_nmos.sym} 220 880 0 0 {name=D1 w=4u l=0.5u ng=1 m=1 mm_ok=1 model=sg13_hv_nmos spiceprefix=X}
C {devices/lab_pin.sym} 240 850 0 0 {name=l194 sig_type=std_logic lab=cap1}
C {devices/lab_pin.sym} 200 880 0 0 {name=l195 sig_type=std_logic lab=d1g}
C {devices/lab_pin.sym} 240 910 0 0 {name=l196 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 240 880 0 0 {name=l197 sig_type=std_logic lab=vss}
C {sg13g2_pr/sg13_hv_pmos.sym} 380 880 0 0 {name=SW2 w=4u l=0.5u ng=1 m=1 mm_ok=1 model=sg13_hv_pmos spiceprefix=X}
C {devices/lab_pin.sym} 400 910 0 0 {name=l198 sig_type=std_logic lab=cap2}
C {devices/lab_pin.sym} 360 880 0 0 {name=l199 sig_type=std_logic lab=d2g}
C {devices/lab_pin.sym} 400 850 0 0 {name=l200 sig_type=std_logic lab=isrc}
C {devices/lab_pin.sym} 400 880 0 0 {name=l201 sig_type=std_logic lab=vdd}
C {sg13g2_pr/sg13_hv_nmos.sym} 540 880 0 0 {name=D2 w=4u l=0.5u ng=1 m=1 mm_ok=1 model=sg13_hv_nmos spiceprefix=X}
C {devices/lab_pin.sym} 560 850 0 0 {name=l202 sig_type=std_logic lab=cap2}
C {devices/lab_pin.sym} 520 880 0 0 {name=l203 sig_type=std_logic lab=d2g}
C {devices/lab_pin.sym} 560 910 0 0 {name=l204 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 560 880 0 0 {name=l205 sig_type=std_logic lab=vss}
C {sg13g2_pr/cap_cmim.sym} 700 880 0 0 {name=C1 model=cap_cmim w=28u l=28u m=1 mm_ok=1 spiceprefix=X}
C {devices/lab_pin.sym} 700 850 0 0 {name=l206 sig_type=std_logic lab=cap1}
C {devices/lab_pin.sym} 700 910 0 0 {name=l207 sig_type=std_logic lab=vss}
C {sg13g2_pr/cap_cmim.sym} 860 880 0 0 {name=C2 model=cap_cmim w=28u l=28u m=1 mm_ok=1 spiceprefix=X}
C {devices/lab_pin.sym} 860 850 0 0 {name=l208 sig_type=std_logic lab=cap2}
C {devices/lab_pin.sym} 860 910 0 0 {name=l209 sig_type=std_logic lab=vss}
C {sg13g2_pr/sg13_hv_nmos.sym} 1020 880 0 0 {name=IAN w=1u l=0.5u ng=1 m=1 mm_ok=1 model=sg13_hv_nmos spiceprefix=X}
C {devices/lab_pin.sym} 1040 850 0 0 {name=l210 sig_type=std_logic lab=a}
C {devices/lab_pin.sym} 1000 880 0 0 {name=l211 sig_type=std_logic lab=d2g}
C {devices/lab_pin.sym} 1040 910 0 0 {name=l212 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 1040 880 0 0 {name=l213 sig_type=std_logic lab=vss}
C {sg13g2_pr/sg13_hv_pmos.sym} 1180 880 0 0 {name=IAP w=2u l=0.5u ng=1 m=1 mm_ok=1 model=sg13_hv_pmos spiceprefix=X}
C {devices/lab_pin.sym} 1200 910 0 0 {name=l214 sig_type=std_logic lab=a}
C {devices/lab_pin.sym} 1160 880 0 0 {name=l215 sig_type=std_logic lab=d2g}
C {devices/lab_pin.sym} 1200 850 0 0 {name=l216 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 1200 880 0 0 {name=l217 sig_type=std_logic lab=vdd}
C {sg13g2_pr/sg13_hv_nmos.sym} 60 1020 0 0 {name=MLSA w=2u l=0.5u ng=1 m=1 mm_ok=1 model=sg13_hv_nmos spiceprefix=X}
C {devices/lab_pin.sym} 80 990 0 0 {name=l218 sig_type=std_logic lab=lsa}
C {devices/lab_pin.sym} 40 1020 0 0 {name=l219 sig_type=std_logic lab=a}
C {devices/lab_pin.sym} 80 1050 0 0 {name=l220 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 80 1020 0 0 {name=l221 sig_type=std_logic lab=vss}
C {sg13g2_pr/sg13_hv_nmos.sym} 220 1020 0 0 {name=MLSB w=2u l=0.5u ng=1 m=1 mm_ok=1 model=sg13_hv_nmos spiceprefix=X}
C {devices/lab_pin.sym} 240 990 0 0 {name=l222 sig_type=std_logic lab=lsb}
C {devices/lab_pin.sym} 200 1020 0 0 {name=l223 sig_type=std_logic lab=d2g}
C {devices/lab_pin.sym} 240 1050 0 0 {name=l224 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 240 1020 0 0 {name=l225 sig_type=std_logic lab=vss}
C {sg13g2_pr/sg13_lv_pmos.sym} 380 1020 0 0 {name=MLPA w=0.5u l=0.3u ng=1 m=1 mm_ok=1 model=sg13_lv_pmos spiceprefix=X}
C {devices/lab_pin.sym} 400 1050 0 0 {name=l226 sig_type=std_logic lab=lsa}
C {devices/lab_pin.sym} 360 1020 0 0 {name=l227 sig_type=std_logic lab=lsb}
C {devices/lab_pin.sym} 400 990 0 0 {name=l228 sig_type=std_logic lab=vdd12}
C {devices/lab_pin.sym} 400 1020 0 0 {name=l229 sig_type=std_logic lab=vdd12}
C {sg13g2_pr/sg13_lv_pmos.sym} 540 1020 0 0 {name=MLPB w=0.5u l=0.3u ng=1 m=1 mm_ok=1 model=sg13_lv_pmos spiceprefix=X}
C {devices/lab_pin.sym} 560 1050 0 0 {name=l230 sig_type=std_logic lab=lsb}
C {devices/lab_pin.sym} 520 1020 0 0 {name=l231 sig_type=std_logic lab=lsa}
C {devices/lab_pin.sym} 560 990 0 0 {name=l232 sig_type=std_logic lab=vdd12}
C {devices/lab_pin.sym} 560 1020 0 0 {name=l233 sig_type=std_logic lab=vdd12}
C {sg13g2_pr/sg13_lv_nmos.sym} 700 1020 0 0 {name=IO1N w=0.5u l=0.13u ng=1 m=1 mm_ok=1 model=sg13_lv_nmos spiceprefix=X}
C {devices/lab_pin.sym} 720 990 0 0 {name=l234 sig_type=std_logic lab=fon}
C {devices/lab_pin.sym} 680 1020 0 0 {name=l235 sig_type=std_logic lab=lsb}
C {devices/lab_pin.sym} 720 1050 0 0 {name=l236 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 720 1020 0 0 {name=l237 sig_type=std_logic lab=vss}
C {sg13g2_pr/sg13_lv_pmos.sym} 860 1020 0 0 {name=IO1P w=1u l=0.13u ng=1 m=1 mm_ok=1 model=sg13_lv_pmos spiceprefix=X}
C {devices/lab_pin.sym} 880 1050 0 0 {name=l238 sig_type=std_logic lab=fon}
C {devices/lab_pin.sym} 840 1020 0 0 {name=l239 sig_type=std_logic lab=lsb}
C {devices/lab_pin.sym} 880 990 0 0 {name=l240 sig_type=std_logic lab=vdd12}
C {devices/lab_pin.sym} 880 1020 0 0 {name=l241 sig_type=std_logic lab=vdd12}
C {sg13g2_pr/sg13_lv_nmos.sym} 1020 1020 0 0 {name=IO2N w=1u l=0.13u ng=1 m=1 mm_ok=1 model=sg13_lv_nmos spiceprefix=X}
C {devices/lab_pin.sym} 1040 990 0 0 {name=l242 sig_type=std_logic lab=fout}
C {devices/lab_pin.sym} 1000 1020 0 0 {name=l243 sig_type=std_logic lab=fon}
C {devices/lab_pin.sym} 1040 1050 0 0 {name=l244 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 1040 1020 0 0 {name=l245 sig_type=std_logic lab=vss}
C {sg13g2_pr/sg13_lv_pmos.sym} 1180 1020 0 0 {name=IO2P w=2u l=0.13u ng=1 m=1 mm_ok=1 model=sg13_lv_pmos spiceprefix=X}
C {devices/lab_pin.sym} 1200 1050 0 0 {name=l246 sig_type=std_logic lab=fout}
C {devices/lab_pin.sym} 1160 1020 0 0 {name=l247 sig_type=std_logic lab=fon}
C {devices/lab_pin.sym} 1200 990 0 0 {name=l248 sig_type=std_logic lab=vdd12}
C {devices/lab_pin.sym} 1200 1020 0 0 {name=l249 sig_type=std_logic lab=vdd12}

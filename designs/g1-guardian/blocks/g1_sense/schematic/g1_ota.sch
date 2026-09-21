v {xschem version=3.4.8RC file_version=1.3}
G {}
K {}
V {}
S {}
E {}
T {g1_ota: 3.3 V PMOS-input folded-cascode + CS output stage; vbn = NMOS bias gate (1.25 uA/um of hv nmos L=1u)} 0 -40 0 0 0.4 0.4 {}
C {sg13g2_pr/sg13_hv_nmos.sym} 200 -200 0 0 {name=MB2 model=sg13_hv_nmos w=8u l=1u ng=2 m=1}
C {devices/lab_pin.sym} 220 -230 0 0 {name=l1 lab=vbp}
C {devices/lab_pin.sym} 180 -200 0 0 {name=l2 lab=vbn}
C {devices/lab_pin.sym} 220 -170 0 0 {name=l3 lab=vss}
C {devices/lab_pin.sym} 220 -200 0 0 {name=l4 lab=vss}
C {sg13g2_pr/sg13_hv_pmos.sym} 200 -400 0 0 {name=MB3 model=sg13_hv_pmos w=16u l=1u ng=4 m=1}
C {devices/lab_pin.sym} 220 -370 0 0 {name=l5 lab=vbp}
C {devices/lab_pin.sym} 180 -400 0 0 {name=l6 lab=vbp}
C {devices/lab_pin.sym} 220 -430 0 0 {name=l7 lab=vdd}
C {devices/lab_pin.sym} 220 -400 0 0 {name=l8 lab=vdd}
C {sg13g2_pr/sg13_hv_pmos.sym} 300 -400 0 0 {name=MB5 model=sg13_hv_pmos w=16u l=1u ng=4 m=1}
C {devices/lab_pin.sym} 320 -370 0 0 {name=l9 lab=vbnc}
C {devices/lab_pin.sym} 280 -400 0 0 {name=l10 lab=vbp}
C {devices/lab_pin.sym} 320 -430 0 0 {name=l11 lab=vdd}
C {devices/lab_pin.sym} 320 -400 0 0 {name=l12 lab=vdd}
C {sg13g2_pr/sg13_hv_nmos.sym} 300 -200 0 0 {name=MB4 model=sg13_hv_nmos w=1.6u l=1u ng=1 m=1}
C {devices/lab_pin.sym} 320 -230 0 0 {name=l13 lab=vbnc}
C {devices/lab_pin.sym} 280 -200 0 0 {name=l14 lab=vbnc}
C {devices/lab_pin.sym} 320 -170 0 0 {name=l15 lab=vss}
C {devices/lab_pin.sym} 320 -200 0 0 {name=l16 lab=vss}
C {sg13g2_pr/sg13_hv_nmos.sym} 400 -200 0 0 {name=MB6 model=sg13_hv_nmos w=8u l=1u ng=2 m=1}
C {devices/lab_pin.sym} 420 -230 0 0 {name=l17 lab=vbpc}
C {devices/lab_pin.sym} 380 -200 0 0 {name=l18 lab=vbn}
C {devices/lab_pin.sym} 420 -170 0 0 {name=l19 lab=vss}
C {devices/lab_pin.sym} 420 -200 0 0 {name=l20 lab=vss}
C {sg13g2_pr/sg13_hv_pmos.sym} 400 -400 0 0 {name=MB7 model=sg13_hv_pmos w=3.2u l=1u ng=1 m=1}
C {devices/lab_pin.sym} 420 -370 0 0 {name=l21 lab=vbpc}
C {devices/lab_pin.sym} 380 -400 0 0 {name=l22 lab=vbpc}
C {devices/lab_pin.sym} 420 -430 0 0 {name=l23 lab=vdd}
C {devices/lab_pin.sym} 420 -400 0 0 {name=l24 lab=vdd}
C {sg13g2_pr/sg13_hv_pmos.sym} 600 -500 0 0 {name=MT model=sg13_hv_pmos w=128u l=1u ng=16 m=1}
C {devices/lab_pin.sym} 620 -470 0 0 {name=l25 lab=tail}
C {devices/lab_pin.sym} 580 -500 0 0 {name=l26 lab=vbp}
C {devices/lab_pin.sym} 620 -530 0 0 {name=l27 lab=vdd}
C {devices/lab_pin.sym} 620 -500 0 0 {name=l28 lab=vdd}
C {sg13g2_pr/sg13_hv_pmos.sym} 550 -350 0 0 {name=M1 model=sg13_hv_pmos w=96u l=2u ng=16 m=1}
C {devices/lab_pin.sym} 570 -320 0 0 {name=l29 lab=fn}
C {devices/lab_pin.sym} 530 -350 0 0 {name=l30 lab=inn}
C {devices/lab_pin.sym} 570 -380 0 0 {name=l31 lab=tail}
C {devices/lab_pin.sym} 570 -350 0 0 {name=l32 lab=vdd}
C {sg13g2_pr/sg13_hv_pmos.sym} 700 -350 0 0 {name=M2 model=sg13_hv_pmos w=96u l=2u ng=16 m=1}
C {devices/lab_pin.sym} 720 -320 0 0 {name=l33 lab=fp}
C {devices/lab_pin.sym} 680 -350 0 0 {name=l34 lab=inp}
C {devices/lab_pin.sym} 720 -380 0 0 {name=l35 lab=tail}
C {devices/lab_pin.sym} 720 -350 0 0 {name=l36 lab=vdd}
C {sg13g2_pr/sg13_hv_nmos.sym} 550 -100 0 0 {name=M3 model=sg13_hv_nmos w=80u l=1u ng=10 m=1}
C {devices/lab_pin.sym} 570 -130 0 0 {name=l37 lab=fn}
C {devices/lab_pin.sym} 530 -100 0 0 {name=l38 lab=vbn}
C {devices/lab_pin.sym} 570 -70 0 0 {name=l39 lab=vss}
C {devices/lab_pin.sym} 570 -100 0 0 {name=l40 lab=vss}
C {sg13g2_pr/sg13_hv_nmos.sym} 700 -100 0 0 {name=M4 model=sg13_hv_nmos w=80u l=1u ng=10 m=1}
C {devices/lab_pin.sym} 720 -130 0 0 {name=l41 lab=fp}
C {devices/lab_pin.sym} 680 -100 0 0 {name=l42 lab=vbn}
C {devices/lab_pin.sym} 720 -70 0 0 {name=l43 lab=vss}
C {devices/lab_pin.sym} 720 -100 0 0 {name=l44 lab=vss}
C {sg13g2_pr/sg13_hv_nmos.sym} 550 -200 0 0 {name=M13 model=sg13_hv_nmos w=48u l=1u ng=6 m=1}
C {devices/lab_pin.sym} 570 -230 0 0 {name=l45 lab=mir}
C {devices/lab_pin.sym} 530 -200 0 0 {name=l46 lab=vbnc}
C {devices/lab_pin.sym} 570 -170 0 0 {name=l47 lab=fn}
C {devices/lab_pin.sym} 570 -200 0 0 {name=l48 lab=vss}
C {sg13g2_pr/sg13_hv_nmos.sym} 700 -200 0 0 {name=M16 model=sg13_hv_nmos w=48u l=1u ng=6 m=1}
C {devices/lab_pin.sym} 720 -230 0 0 {name=l49 lab=out1}
C {devices/lab_pin.sym} 680 -200 0 0 {name=l50 lab=vbnc}
C {devices/lab_pin.sym} 720 -170 0 0 {name=l51 lab=fp}
C {devices/lab_pin.sym} 720 -200 0 0 {name=l52 lab=vss}
C {sg13g2_pr/sg13_hv_pmos.sym} 900 -500 0 0 {name=M14 model=sg13_hv_pmos w=96u l=1u ng=12 m=1}
C {devices/lab_pin.sym} 920 -470 0 0 {name=l53 lab=pc1}
C {devices/lab_pin.sym} 880 -500 0 0 {name=l54 lab=mir}
C {devices/lab_pin.sym} 920 -530 0 0 {name=l55 lab=vdd}
C {devices/lab_pin.sym} 920 -500 0 0 {name=l56 lab=vdd}
C {sg13g2_pr/sg13_hv_pmos.sym} 1050 -500 0 0 {name=M11 model=sg13_hv_pmos w=96u l=1u ng=12 m=1}
C {devices/lab_pin.sym} 1070 -470 0 0 {name=l57 lab=pc2}
C {devices/lab_pin.sym} 1030 -500 0 0 {name=l58 lab=mir}
C {devices/lab_pin.sym} 1070 -530 0 0 {name=l59 lab=vdd}
C {devices/lab_pin.sym} 1070 -500 0 0 {name=l60 lab=vdd}
C {sg13g2_pr/sg13_hv_pmos.sym} 900 -400 0 0 {name=M15 model=sg13_hv_pmos w=96u l=1u ng=12 m=1}
C {devices/lab_pin.sym} 920 -370 0 0 {name=l61 lab=mir}
C {devices/lab_pin.sym} 880 -400 0 0 {name=l62 lab=vbpc}
C {devices/lab_pin.sym} 920 -430 0 0 {name=l63 lab=pc1}
C {devices/lab_pin.sym} 920 -400 0 0 {name=l64 lab=vdd}
C {sg13g2_pr/sg13_hv_pmos.sym} 1050 -400 0 0 {name=M12 model=sg13_hv_pmos w=96u l=1u ng=12 m=1}
C {devices/lab_pin.sym} 1070 -370 0 0 {name=l65 lab=out1}
C {devices/lab_pin.sym} 1030 -400 0 0 {name=l66 lab=vbpc}
C {devices/lab_pin.sym} 1070 -430 0 0 {name=l67 lab=pc2}
C {devices/lab_pin.sym} 1070 -400 0 0 {name=l68 lab=vdd}
C {sg13g2_pr/sg13_hv_pmos.sym} 1250 -500 0 0 {name=M20 model=sg13_hv_pmos w=192u l=1u ng=24 m=1}
C {devices/lab_pin.sym} 1270 -470 0 0 {name=l69 lab=out}
C {devices/lab_pin.sym} 1230 -500 0 0 {name=l70 lab=out1}
C {devices/lab_pin.sym} 1270 -530 0 0 {name=l71 lab=vdd}
C {devices/lab_pin.sym} 1270 -500 0 0 {name=l72 lab=vdd}
C {sg13g2_pr/sg13_hv_nmos.sym} 1250 -300 0 0 {name=M21 model=sg13_hv_nmos w=96u l=1u ng=12 m=1}
C {devices/lab_pin.sym} 1270 -330 0 0 {name=l73 lab=out}
C {devices/lab_pin.sym} 1230 -300 0 0 {name=l74 lab=vbn}
C {devices/lab_pin.sym} 1270 -270 0 0 {name=l75 lab=vss}
C {devices/lab_pin.sym} 1270 -300 0 0 {name=l76 lab=vss}
C {sg13g2_pr/rppd.sym} 1150 -200 0 0 {name=RZ w=1u l=6.2u model=rppd b=0 m=1}
C {devices/lab_pin.sym} 1150 -230 0 0 {name=l77 lab=out1}
C {devices/lab_pin.sym} 1150 -170 0 0 {name=l78 lab=cz}
C {sg13g2_pr/cap_cmim.sym} 1250 -150 0 0 {name=CC model=cap_cmim w=23u l=23u m=1}
C {devices/lab_pin.sym} 1250 -180 0 0 {name=l79 lab=cz}
C {devices/lab_pin.sym} 1250 -120 0 0 {name=l80 lab=out}
C {devices/ipin.sym} 1500 -500 0 0 {name=pi0 lab=inp}
C {devices/ipin.sym} 1500 -480 0 0 {name=pi1 lab=inn}
C {devices/ipin.sym} 1500 -460 0 0 {name=pi2 lab=vbn}
C {devices/opin.sym} 1500 -440 0 0 {name=po0 lab=out}
C {devices/iopin.sym} 1500 -420 0 0 {name=pb0 lab=vdd}
C {devices/iopin.sym} 1500 -400 0 0 {name=pb1 lab=vss}
T {Currents with vbn from an 8u/1u diode at 10 uA equivalent: tail 80uA, PMOS sources 60uA, NMOS sources 100uA; stage 2 120uA class A; two-stage Miller compensated (Cc 0.8 pF, Rz 1.7 kOhm).} 100 -650 0 0 0.3 0.3 {}
T {inn on M1 (mirror side), inp on M2: stage-1 output out1 falls when inp rises, stage 2 inverts -> out rises. ibias: 10 uA sunk into MB1 diode.} 100 -600 0 0 0.3 0.3 {}

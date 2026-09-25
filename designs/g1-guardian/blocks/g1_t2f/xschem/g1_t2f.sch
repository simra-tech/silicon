v {xschem version=3.4.8RC file_version=1.3}
G {}
K {}
V {}
S {}
E {}
B 4 140 -880 1260 450 {dash=5 fill=false}
B 4 1300 -560 1640 380 {dash=5 fill=false}
B 4 1680 -700 2560 420 {dash=5 fill=false}
B 4 2800 -720 3900 420 {dash=5 fill=false}
B 4 3940 -620 4880 -300 {dash=5 fill=false}
B 4 140 -1500 2540 -1348 {fill=false}
T {PTAT legs (pbias/pcasc from G1_BGR), R_REF, cascode gate rail vcg, threshold select} 148 -874 0 0 0.3 0.3 {layer=4}
T {current steering + timing caps} 1308 -554 0 0 0.3 0.3 {layer=4}
T {comparators: npn13G2 pair, collector cascodes, PMOS mirror} 1688 -694 0 0 0.3 0.3 {layer=4}
T {NAND RS latch + steering drive} 2808 -714 0 0 0.3 0.3 {layer=4}
T {3.3 V -> 1.2 V and output buffer} 3948 -614 0 0 0.3 0.3 {layer=4}
T {mode=0: vth = VREF, f proportional to I_PTAT / VREF (PTAT).  mode=1: vth = 2 I_PTAT R_REF, f = 1/(2 R_REF C), temperature-independent to first order.} 140 520 0 0 0.3 0.3 {}
T {Simulated (not measured), chip BGR586: 1.507 MHz at 25 C, 4.909 kHz/C slope (block); chip netlists 1.518 MHz at 27 C, 1.997 MHz at 125 C (README.md).} 140 538 0 0 0.3 0.3 {}
T {Revision 2: collector cascodes MCA/MCB keep V_CE = V_BE + ~0.3 V (npn13G2 vce_max 1.6 V); bleeders MBA/MBB keep the off cascode conducting.} 140 556 0 0 0.3 0.3 {}
T {g1_t2f - temperature-to-frequency converter, revision 2 (I_PTAT relaxation oscillator, cascoded HBT comparators)} 152 -1490 0 0 0.55 0.55 {}
T {G1 guardian, chip of record g1_chip_top_1414_r2.gds 9049e87b (r2 2026-09-25; geometry XOR-identical to r1 629d303a); block map: g1_padring/reports/signoff-1414-20260924} 152 -1451 0 0 0.3 0.3 {}
T {On-chip variant: baseline (not rev1) = layout/g1_t2f.gds c2ae89a9, LVS reference layout/g1_t2f_lvs.cdl ce4d82b7} 152 -1427 0 0 0.3 0.3 {}
T {Netlist-equivalent to g1_t2f.spice sha256 8011b761 (flattened device/connectivity comparison)} 152 -1403 0 0 0.3 0.3 {}
T {Drawn 2026-09-25 by the block generator; device sizes (w, l, ng, m) are on each symbol. Proof: review/schematics-readability-20260925} 152 -1379 0 0 0.25 0.25 {}
C {sg13g2_pr/sg13_hv_pmos.sym} 200 -800 0 0 {name=MPO w=10u l=4u ng=1 m=1 mm_ok=1 model=sg13_hv_pmos spiceprefix=X}
C {sg13g2_pr/sg13_hv_pmos.sym} 200 -690 0 0 {name=MCO w=10u l=4u ng=1 m=1 mm_ok=1 model=sg13_hv_pmos spiceprefix=X}
C {sg13g2_pr/sg13_hv_pmos.sym} 400 -800 0 0 {name=MPR w=10u l=4u ng=1 m=2 mm_ok=1 model=sg13_hv_pmos spiceprefix=X}
C {sg13g2_pr/sg13_hv_pmos.sym} 400 -690 0 0 {name=MCR w=10u l=4u ng=1 m=2 mm_ok=1 model=sg13_hv_pmos spiceprefix=X}
C {sg13g2_pr/rppd.sym} 420 -580 0 0 {name=RREF1 w=0.5u l=24.5u model=rppd body=sub! spiceprefix=X b=0 m=1 mm_ok=1}
C {sg13g2_pr/rppd.sym} 420 -500 0 0 {name=RREF2 w=0.5u l=24.5u model=rppd body=sub! spiceprefix=X b=0 m=1 mm_ok=1}
C {sg13g2_pr/rppd.sym} 420 -420 0 0 {name=RREF3 w=0.5u l=24.5u model=rppd body=sub! spiceprefix=X b=0 m=1 mm_ok=1}
C {sg13g2_pr/rppd.sym} 420 -340 0 0 {name=RREF4 w=0.5u l=24.5u model=rppd body=sub! spiceprefix=X b=0 m=1 mm_ok=1}
C {sg13g2_pr/rppd.sym} 420 -260 0 0 {name=RREF5 w=0.5u l=24.5u model=rppd body=sub! spiceprefix=X b=0 m=1 mm_ok=1}
C {sg13g2_pr/rppd.sym} 420 -180 0 0 {name=RREF6 w=0.5u l=24.5u model=rppd body=sub! spiceprefix=X b=0 m=1 mm_ok=1}
C {sg13g2_pr/rppd.sym} 420 -100 0 0 {name=RREF7 w=0.5u l=24.5u model=rppd body=sub! spiceprefix=X b=0 m=1 mm_ok=1}
C {sg13g2_pr/rppd.sym} 420 -20 0 0 {name=RREF8 w=0.5u l=24.5u model=rppd body=sub! spiceprefix=X b=0 m=1 mm_ok=1}
C {sg13g2_pr/rppd.sym} 420 60 0 0 {name=RREF9 w=0.5u l=24.5u model=rppd body=sub! spiceprefix=X b=0 m=1 mm_ok=1}
C {sg13g2_pr/rppd.sym} 420 140 0 0 {name=RREF10 w=0.5u l=24.5u model=rppd body=sub! spiceprefix=X b=0 m=1 mm_ok=1}
C {sg13g2_pr/sg13_hv_pmos.sym} 600 -800 0 0 {name=MPB w=10u l=4u ng=1 m=1 mm_ok=1 model=sg13_hv_pmos spiceprefix=X}
C {sg13g2_pr/sg13_hv_pmos.sym} 600 -690 0 0 {name=MCB w=10u l=4u ng=1 m=1 mm_ok=1 model=sg13_hv_pmos spiceprefix=X}
C {sg13g2_pr/sg13_hv_nmos.sym} 600 -380 0 0 {name=MNB w=10u l=2u ng=1 m=1 mm_ok=1 model=sg13_hv_nmos spiceprefix=X}
C {sg13g2_pr/sg13_hv_pmos.sym} 800 -800 0 0 {name=MPF w=10u l=4u ng=1 m=1 mm_ok=1 model=sg13_hv_pmos spiceprefix=X}
C {sg13g2_pr/sg13_hv_pmos.sym} 800 -620 0 0 {name=MSF w=2u l=2u ng=1 m=1 mm_ok=1 model=sg13_hv_pmos spiceprefix=X}
C {sg13g2_pr/sg13_hv_nmos.sym} 1000 -620 0 0 {name=MX1 w=4u l=0.5u ng=1 m=1 mm_ok=1 model=sg13_hv_nmos spiceprefix=X}
C {sg13g2_pr/sg13_hv_nmos.sym} 1160 -620 0 0 {name=MX2 w=4u l=0.5u ng=1 m=1 mm_ok=1 model=sg13_hv_nmos spiceprefix=X}
C {sg13g2_pr/sg13_hv_nmos.sym} 1080 -300 0 0 {name=IMN w=1u l=0.5u ng=1 m=1 mm_ok=1 model=sg13_hv_nmos spiceprefix=X}
C {sg13g2_pr/sg13_hv_pmos.sym} 1080 -420 0 0 {name=IMP w=2u l=0.5u ng=1 m=1 mm_ok=1 model=sg13_hv_pmos spiceprefix=X}
C {sg13g2_pr/npn13G2.sym} 1800 -420 0 0 {name=QA1 model=npn13G2 spiceprefix=X Nx=1 mm_ok=1}
C {sg13g2_pr/npn13G2.sym} 2040 -420 0 1 {name=QB1 model=npn13G2 spiceprefix=X Nx=1 mm_ok=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1840 -540 0 1 {name=MCA1 w=4u l=1u ng=1 m=1 mm_ok=1 model=sg13_hv_nmos spiceprefix=X}
C {sg13g2_pr/sg13_hv_nmos.sym} 2000 -540 0 0 {name=MCB1 w=4u l=1u ng=1 m=1 mm_ok=1 model=sg13_hv_nmos spiceprefix=X}
C {sg13g2_pr/sg13_hv_nmos.sym} 1720 -460 0 0 {name=MBA1 w=0.5u l=2u ng=1 m=1 mm_ok=1 model=sg13_hv_nmos spiceprefix=X}
C {sg13g2_pr/sg13_hv_nmos.sym} 2100 -460 0 1 {name=MBB1 w=0.5u l=2u ng=1 m=1 mm_ok=1 model=sg13_hv_nmos spiceprefix=X}
C {sg13g2_pr/sg13_hv_pmos.sym} 1840 -660 0 1 {name=MLA1 w=4u l=1u ng=1 m=1 mm_ok=1 model=sg13_hv_pmos spiceprefix=X}
C {sg13g2_pr/sg13_hv_pmos.sym} 2000 -660 0 0 {name=MLB1 w=4u l=1u ng=1 m=1 mm_ok=1 model=sg13_hv_pmos spiceprefix=X}
C {sg13g2_pr/sg13_hv_nmos.sym} 1900 -300 0 0 {name=MT1 w=20u l=2u ng=1 m=1 mm_ok=1 model=sg13_hv_nmos spiceprefix=X}
C {sg13g2_pr/sg13_hv_nmos.sym} 2220 -520 0 0 {name=IC1AN w=1u l=0.5u ng=1 m=1 mm_ok=1 model=sg13_hv_nmos spiceprefix=X}
C {sg13g2_pr/sg13_hv_pmos.sym} 2220 -640 0 0 {name=IC1AP w=2u l=0.5u ng=1 m=1 mm_ok=1 model=sg13_hv_pmos spiceprefix=X}
C {sg13g2_pr/sg13_hv_nmos.sym} 2400 -520 0 0 {name=IC1BN w=2u l=0.5u ng=1 m=1 mm_ok=1 model=sg13_hv_nmos spiceprefix=X}
C {sg13g2_pr/sg13_hv_pmos.sym} 2400 -640 0 0 {name=IC1BP w=4u l=0.5u ng=1 m=1 mm_ok=1 model=sg13_hv_pmos spiceprefix=X}
C {sg13g2_pr/npn13G2.sym} 1800 200 0 0 {name=QA2 model=npn13G2 spiceprefix=X Nx=1 mm_ok=1}
C {sg13g2_pr/npn13G2.sym} 2040 200 0 1 {name=QB2 model=npn13G2 spiceprefix=X Nx=1 mm_ok=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1840 80 0 1 {name=MCA2 w=4u l=1u ng=1 m=1 mm_ok=1 model=sg13_hv_nmos spiceprefix=X}
C {sg13g2_pr/sg13_hv_nmos.sym} 2000 80 0 0 {name=MCB2 w=4u l=1u ng=1 m=1 mm_ok=1 model=sg13_hv_nmos spiceprefix=X}
C {sg13g2_pr/sg13_hv_nmos.sym} 1720 160 0 0 {name=MBA2 w=0.5u l=2u ng=1 m=1 mm_ok=1 model=sg13_hv_nmos spiceprefix=X}
C {sg13g2_pr/sg13_hv_nmos.sym} 2100 160 0 1 {name=MBB2 w=0.5u l=2u ng=1 m=1 mm_ok=1 model=sg13_hv_nmos spiceprefix=X}
C {sg13g2_pr/sg13_hv_pmos.sym} 1840 -40 0 1 {name=MLA2 w=4u l=1u ng=1 m=1 mm_ok=1 model=sg13_hv_pmos spiceprefix=X}
C {sg13g2_pr/sg13_hv_pmos.sym} 2000 -40 0 0 {name=MLB2 w=4u l=1u ng=1 m=1 mm_ok=1 model=sg13_hv_pmos spiceprefix=X}
C {sg13g2_pr/sg13_hv_nmos.sym} 1900 320 0 0 {name=MT2 w=20u l=2u ng=1 m=1 mm_ok=1 model=sg13_hv_nmos spiceprefix=X}
C {sg13g2_pr/sg13_hv_nmos.sym} 2220 100 0 0 {name=IC2AN w=1u l=0.5u ng=1 m=1 mm_ok=1 model=sg13_hv_nmos spiceprefix=X}
C {sg13g2_pr/sg13_hv_pmos.sym} 2220 -20 0 0 {name=IC2AP w=2u l=0.5u ng=1 m=1 mm_ok=1 model=sg13_hv_pmos spiceprefix=X}
C {sg13g2_pr/sg13_hv_nmos.sym} 2400 100 0 0 {name=IC2BN w=2u l=0.5u ng=1 m=1 mm_ok=1 model=sg13_hv_nmos spiceprefix=X}
C {sg13g2_pr/sg13_hv_pmos.sym} 2400 -20 0 0 {name=IC2BP w=4u l=0.5u ng=1 m=1 mm_ok=1 model=sg13_hv_pmos spiceprefix=X}
C {sg13g2_pr/sg13_hv_pmos.sym} 2900 -670 0 0 {name=NQPA w=2u l=0.5u ng=1 m=1 mm_ok=1 model=sg13_hv_pmos spiceprefix=X}
C {sg13g2_pr/sg13_hv_pmos.sym} 3060 -670 0 0 {name=NQPB w=2u l=0.5u ng=1 m=1 mm_ok=1 model=sg13_hv_pmos spiceprefix=X}
C {sg13g2_pr/sg13_hv_nmos.sym} 2900 -500 0 0 {name=NQNA w=2u l=0.5u ng=1 m=1 mm_ok=1 model=sg13_hv_nmos spiceprefix=X}
C {sg13g2_pr/sg13_hv_nmos.sym} 2900 -390 0 0 {name=NQNB w=2u l=0.5u ng=1 m=1 mm_ok=1 model=sg13_hv_nmos spiceprefix=X}
C {sg13g2_pr/sg13_hv_pmos.sym} 2900 -130 0 0 {name=NQNPA w=2u l=0.5u ng=1 m=1 mm_ok=1 model=sg13_hv_pmos spiceprefix=X}
C {sg13g2_pr/sg13_hv_pmos.sym} 3060 -130 0 0 {name=NQNPB w=2u l=0.5u ng=1 m=1 mm_ok=1 model=sg13_hv_pmos spiceprefix=X}
C {sg13g2_pr/sg13_hv_pmos.sym} 3220 -130 0 0 {name=NQNPC w=2u l=0.5u ng=1 m=1 mm_ok=1 model=sg13_hv_pmos spiceprefix=X}
C {sg13g2_pr/sg13_hv_nmos.sym} 2900 40 0 0 {name=NQNNA w=3u l=0.5u ng=1 m=1 mm_ok=1 model=sg13_hv_nmos spiceprefix=X}
C {sg13g2_pr/sg13_hv_nmos.sym} 2900 150 0 0 {name=NQNNB w=3u l=0.5u ng=1 m=1 mm_ok=1 model=sg13_hv_nmos spiceprefix=X}
C {sg13g2_pr/sg13_hv_nmos.sym} 2900 260 0 0 {name=NQNNC w=3u l=0.5u ng=1 m=1 mm_ok=1 model=sg13_hv_nmos spiceprefix=X}
C {sg13g2_pr/sg13_hv_pmos.sym} 3500 -670 0 0 {name=ND1PA w=2u l=0.5u ng=1 m=1 mm_ok=1 model=sg13_hv_pmos spiceprefix=X}
C {sg13g2_pr/sg13_hv_pmos.sym} 3660 -670 0 0 {name=ND1PB w=2u l=0.5u ng=1 m=1 mm_ok=1 model=sg13_hv_pmos spiceprefix=X}
C {sg13g2_pr/sg13_hv_nmos.sym} 3500 -500 0 0 {name=ND1NA w=2u l=0.5u ng=1 m=1 mm_ok=1 model=sg13_hv_nmos spiceprefix=X}
C {sg13g2_pr/sg13_hv_nmos.sym} 3500 -390 0 0 {name=ND1NB w=2u l=0.5u ng=1 m=1 mm_ok=1 model=sg13_hv_nmos spiceprefix=X}
C {sg13g2_pr/sg13_hv_pmos.sym} 3500 -130 0 0 {name=ND2PA w=2u l=0.5u ng=1 m=1 mm_ok=1 model=sg13_hv_pmos spiceprefix=X}
C {sg13g2_pr/sg13_hv_pmos.sym} 3660 -130 0 0 {name=ND2PB w=2u l=0.5u ng=1 m=1 mm_ok=1 model=sg13_hv_pmos spiceprefix=X}
C {sg13g2_pr/sg13_hv_nmos.sym} 3500 40 0 0 {name=ND2NA w=2u l=0.5u ng=1 m=1 mm_ok=1 model=sg13_hv_nmos spiceprefix=X}
C {sg13g2_pr/sg13_hv_nmos.sym} 3500 150 0 0 {name=ND2NB w=2u l=0.5u ng=1 m=1 mm_ok=1 model=sg13_hv_nmos spiceprefix=X}
C {sg13g2_pr/sg13_hv_pmos.sym} 1400 -480 0 0 {name=SW1 w=4u l=0.5u ng=1 m=1 mm_ok=1 model=sg13_hv_pmos spiceprefix=X}
C {sg13g2_pr/sg13_hv_nmos.sym} 1400 -360 0 0 {name=D1 w=4u l=0.5u ng=1 m=1 mm_ok=1 model=sg13_hv_nmos spiceprefix=X}
C {sg13g2_pr/sg13_hv_pmos.sym} 1400 140 0 0 {name=SW2 w=4u l=0.5u ng=1 m=1 mm_ok=1 model=sg13_hv_pmos spiceprefix=X}
C {sg13g2_pr/sg13_hv_nmos.sym} 1400 260 0 0 {name=D2 w=4u l=0.5u ng=1 m=1 mm_ok=1 model=sg13_hv_nmos spiceprefix=X}
C {sg13g2_pr/cap_cmim.sym} 1540 -390 0 0 {name=C1 model=cap_cmim w=28u l=28u m=1 mm_ok=1 spiceprefix=X}
C {sg13g2_pr/cap_cmim.sym} 1540 230 0 0 {name=C2 model=cap_cmim w=28u l=28u m=1 mm_ok=1 spiceprefix=X}
C {sg13g2_pr/sg13_hv_nmos.sym} 4000 -380 0 0 {name=IAN w=1u l=0.5u ng=1 m=1 mm_ok=1 model=sg13_hv_nmos spiceprefix=X}
C {sg13g2_pr/sg13_hv_pmos.sym} 4000 -500 0 0 {name=IAP w=2u l=0.5u ng=1 m=1 mm_ok=1 model=sg13_hv_pmos spiceprefix=X}
C {sg13g2_pr/sg13_hv_nmos.sym} 4200 -380 0 0 {name=MLSA w=2u l=0.5u ng=1 m=1 mm_ok=1 model=sg13_hv_nmos spiceprefix=X}
C {sg13g2_pr/sg13_hv_nmos.sym} 4400 -380 0 0 {name=MLSB w=2u l=0.5u ng=1 m=1 mm_ok=1 model=sg13_hv_nmos spiceprefix=X}
C {sg13g2_pr/sg13_lv_pmos.sym} 4200 -510 0 0 {name=MLPA w=0.5u l=0.3u ng=1 m=1 mm_ok=1 model=sg13_lv_pmos spiceprefix=X}
C {sg13g2_pr/sg13_lv_pmos.sym} 4400 -510 0 0 {name=MLPB w=0.5u l=0.3u ng=1 m=1 mm_ok=1 model=sg13_lv_pmos spiceprefix=X}
C {sg13g2_pr/sg13_lv_nmos.sym} 4600 -380 0 0 {name=IO1N w=0.5u l=0.13u ng=1 m=1 mm_ok=1 model=sg13_lv_nmos spiceprefix=X}
C {sg13g2_pr/sg13_lv_pmos.sym} 4600 -500 0 0 {name=IO1P w=1u l=0.13u ng=1 m=1 mm_ok=1 model=sg13_lv_pmos spiceprefix=X}
C {sg13g2_pr/sg13_lv_nmos.sym} 4780 -380 0 0 {name=IO2N w=1u l=0.13u ng=1 m=1 mm_ok=1 model=sg13_lv_nmos spiceprefix=X}
C {sg13g2_pr/sg13_lv_pmos.sym} 4780 -500 0 0 {name=IO2P w=2u l=0.13u ng=1 m=1 mm_ok=1 model=sg13_lv_pmos spiceprefix=X}
C {devices/iopin.sym} 100 -1100 0 0 {name=p0 lab=vdd}
C {devices/iopin.sym} 100 -1070 0 0 {name=p1 lab=vdd12}
C {devices/iopin.sym} 100 -1040 0 0 {name=p2 lab=vss}
C {devices/ipin.sym} 100 -1010 0 0 {name=p3 lab=pbias}
C {devices/ipin.sym} 100 -980 0 0 {name=p4 lab=pcasc}
C {devices/ipin.sym} 100 -950 0 0 {name=p5 lab=vref}
C {devices/ipin.sym} 100 -920 0 0 {name=p6 lab=en}
C {devices/ipin.sym} 100 -890 0 0 {name=p7 lab=mode}
C {devices/opin.sym} 4950 -440 0 0 {name=p8 lab=fout}
C {g1_body_lab.sym} 1020 -620 0 0 {name=l1 lab=vss}
C {g1_body_lab.sym} 1180 -620 0 0 {name=l2 lab=vss}
C {g1_body_lab.sym} 1820 -540 0 0 {name=l3 lab=vss}
C {g1_body_lab.sym} 2020 -540 0 0 {name=l4 lab=vss}
C {g1_body_lab.sym} 1820 80 0 0 {name=l5 lab=vss}
C {g1_body_lab.sym} 2020 80 0 0 {name=l6 lab=vss}
C {g1_body_lab.sym} 2920 -500 0 0 {name=l7 lab=vss}
C {g1_body_lab.sym} 2920 40 0 0 {name=l8 lab=vss}
C {g1_body_lab.sym} 2920 150 0 0 {name=l9 lab=vss}
C {g1_body_lab.sym} 3520 -500 0 0 {name=l10 lab=vss}
C {g1_body_lab.sym} 3520 40 0 0 {name=l11 lab=vss}
C {g1_body_lab.sym} 1420 -480 0 0 {name=l12 lab=vdd}
C {g1_body_lab.sym} 1420 140 0 0 {name=l13 lab=vdd}
C {devices/lab_pin.sym} 220 -850 0 0 {name=l14 lab=vdd}
C {devices/lab_pin.sym} 420 -850 0 0 {name=l15 lab=vdd}
C {devices/lab_pin.sym} 620 -850 0 0 {name=l16 lab=vdd}
C {devices/lab_pin.sym} 160 -840 0 0 {name=l17 lab=pbias}
C {devices/lab_pin.sym} 170 -650 0 0 {name=l18 lab=pcasc}
C {devices/lab_pin.sym} 220 -600 0 0 {name=l19 lab=isrc}
C {devices/lab_pin.sym} 420 -625 0 1 {name=l20 lab=vr}
C {g1_node_lab.sym} 420 -540 0 0 {name=l21 lab=vr_1}
C {g1_node_lab.sym} 420 -460 0 0 {name=l22 lab=vr_2}
C {g1_node_lab.sym} 420 -380 0 0 {name=l23 lab=vr_3}
C {g1_node_lab.sym} 420 -300 0 0 {name=l24 lab=vr_4}
C {g1_node_lab.sym} 420 -220 0 0 {name=l25 lab=vr_5}
C {g1_node_lab.sym} 420 -140 0 0 {name=l26 lab=vr_6}
C {g1_node_lab.sym} 420 -60 0 0 {name=l27 lab=vr_7}
C {g1_node_lab.sym} 420 20 0 0 {name=l28 lab=vr_8}
C {g1_node_lab.sym} 420 100 0 0 {name=l29 lab=vr_9}
C {devices/lab_pin.sym} 420 190 0 0 {name=l30 lab=vss}
C {devices/lab_pin.sym} 620 -500 0 1 {name=l31 lab=nbias}
C {devices/lab_pin.sym} 620 -330 0 0 {name=l32 lab=vss}
C {devices/lab_pin.sym} 820 -670 0 1 {name=l33 lab=vcg}
C {devices/lab_pin.sym} 820 -850 0 0 {name=l34 lab=vdd}
C {devices/lab_pin.sym} 750 -620 0 0 {name=l35 lab=vth}
C {devices/lab_pin.sym} 820 -570 0 0 {name=l36 lab=vss}
C {devices/lab_pin.sym} 1100 -530 0 0 {name=l37 lab=vth}
C {devices/lab_pin.sym} 1020 -670 0 0 {name=l38 lab=vref}
C {devices/lab_pin.sym} 1180 -670 0 0 {name=l39 lab=vr}
C {devices/lab_pin.sym} 950 -620 0 0 {name=l40 lab=moden}
C {devices/lab_pin.sym} 1110 -620 0 0 {name=l41 lab=mode}
C {devices/lab_pin.sym} 1020 -360 0 0 {name=l42 lab=mode}
C {devices/lab_pin.sym} 1180 -360 0 1 {name=l43 lab=moden}
C {devices/lab_pin.sym} 1100 -470 0 0 {name=l44 lab=vdd}
C {devices/lab_pin.sym} 1100 -250 0 0 {name=l45 lab=vss}
C {devices/lab_pin.sym} 1340 -420 0 0 {name=l46 lab=d1g}
C {devices/lab_wire.sym} 1500 -420 0 0 {name=l47 lab=cap1}
C {devices/lab_pin.sym} 1420 -530 0 0 {name=l48 lab=isrc}
C {devices/lab_pin.sym} 1420 -310 0 0 {name=l49 lab=vss}
C {devices/lab_pin.sym} 1540 -340 0 0 {name=l50 lab=vss}
C {devices/lab_pin.sym} 1340 200 0 0 {name=l51 lab=d2g}
C {devices/lab_wire.sym} 1500 200 0 0 {name=l52 lab=cap2}
C {devices/lab_pin.sym} 1420 90 0 0 {name=l53 lab=isrc}
C {devices/lab_pin.sym} 1420 310 0 0 {name=l54 lab=vss}
C {devices/lab_pin.sym} 1540 280 0 0 {name=l55 lab=vss}
C {devices/lab_pin.sym} 1820 -595 0 0 {name=l56 lab=oa1}
C {devices/lab_wire.sym} 1940 -540 0 0 {name=l57 lab=vcg}
C {devices/lab_pin.sym} 1820 -465 0 0 {name=l58 lab=ca1}
C {devices/lab_pin.sym} 2020 -465 0 1 {name=l59 lab=cb1}
C {devices/lab_pin.sym} 1670 -460 0 0 {name=l60 lab=nbias}
C {devices/lab_pin.sym} 2150 -460 0 1 {name=l61 lab=nbias}
C {devices/lab_pin.sym} 1740 -410 0 0 {name=l62 lab=vss}
C {devices/lab_pin.sym} 2080 -410 0 0 {name=l63 lab=vss}
C {devices/lab_wire.sym} 1900 -360 0 0 {name=l64 lab=tail1}
C {devices/lab_pin.sym} 1850 -300 0 0 {name=l65 lab=nbias}
C {devices/lab_pin.sym} 1920 -250 0 0 {name=l66 lab=vss}
C {devices/lab_pin.sym} 1750 -420 0 0 {name=l67 lab=vth}
C {devices/lab_pin.sym} 2090 -420 0 1 {name=l68 lab=cap1}
C {g1_node_lab.sym} 1820 -420 0 0 {name=l69 lab=vss}
C {g1_node_lab.sym} 2020 -420 0 0 {name=l70 lab=vss}
C {devices/lab_pin.sym} 1820 -710 0 0 {name=l71 lab=vdd}
C {devices/lab_pin.sym} 2020 -710 0 0 {name=l72 lab=vdd}
C {devices/lab_pin.sym} 2240 -690 0 0 {name=l73 lab=vdd}
C {devices/lab_pin.sym} 2240 -470 0 0 {name=l74 lab=vss}
C {devices/lab_pin.sym} 2420 -690 0 0 {name=l75 lab=vdd}
C {devices/lab_pin.sym} 2420 -470 0 0 {name=l76 lab=vss}
C {devices/lab_wire.sym} 2130 -600 0 0 {name=l77 lab=ob1}
C {devices/lab_wire.sym} 2340 -580 0 0 {name=l78 lab=c1}
C {devices/lab_wire.sym} 2520 -580 0 0 {name=l79 lab=sn}
C {devices/lab_pin.sym} 1820 25 0 0 {name=l80 lab=oa2}
C {devices/lab_wire.sym} 1940 80 0 0 {name=l81 lab=vcg}
C {devices/lab_pin.sym} 1820 155 0 0 {name=l82 lab=ca2}
C {devices/lab_pin.sym} 2020 155 0 1 {name=l83 lab=cb2}
C {devices/lab_pin.sym} 1670 160 0 0 {name=l84 lab=nbias}
C {devices/lab_pin.sym} 2150 160 0 1 {name=l85 lab=nbias}
C {devices/lab_pin.sym} 1740 210 0 0 {name=l86 lab=vss}
C {devices/lab_pin.sym} 2080 210 0 0 {name=l87 lab=vss}
C {devices/lab_wire.sym} 1900 260 0 0 {name=l88 lab=tail2}
C {devices/lab_pin.sym} 1850 320 0 0 {name=l89 lab=nbias}
C {devices/lab_pin.sym} 1920 370 0 0 {name=l90 lab=vss}
C {devices/lab_pin.sym} 1750 200 0 0 {name=l91 lab=vth}
C {devices/lab_pin.sym} 2090 200 0 1 {name=l92 lab=cap2}
C {g1_node_lab.sym} 1820 200 0 0 {name=l93 lab=vss}
C {g1_node_lab.sym} 2020 200 0 0 {name=l94 lab=vss}
C {devices/lab_pin.sym} 1820 -90 0 0 {name=l95 lab=vdd}
C {devices/lab_pin.sym} 2020 -90 0 0 {name=l96 lab=vdd}
C {devices/lab_pin.sym} 2240 -70 0 0 {name=l97 lab=vdd}
C {devices/lab_pin.sym} 2240 150 0 0 {name=l98 lab=vss}
C {devices/lab_pin.sym} 2420 -70 0 0 {name=l99 lab=vdd}
C {devices/lab_pin.sym} 2420 150 0 0 {name=l100 lab=vss}
C {devices/lab_wire.sym} 2130 20 0 0 {name=l101 lab=ob2}
C {devices/lab_wire.sym} 2340 40 0 0 {name=l102 lab=c2}
C {devices/lab_wire.sym} 2520 40 0 0 {name=l103 lab=rn}
C {g1_node_lab.sym} 2920 -445 0 0 {name=l104 lab=NQ_i}
C {devices/lab_pin.sym} 2920 -720 0 0 {name=l105 lab=vdd}
C {devices/lab_pin.sym} 3080 -720 0 0 {name=l106 lab=vdd}
C {devices/lab_pin.sym} 2920 -340 0 0 {name=l107 lab=vss}
C {devices/lab_wire.sym} 3180 -595 0 0 {name=l108 lab=q}
C {g1_node_lab.sym} 2920 95 0 0 {name=l109 lab=NQN_i}
C {g1_node_lab.sym} 2920 205 0 0 {name=l110 lab=NQN_j}
C {devices/lab_pin.sym} 2920 -180 0 0 {name=l111 lab=vdd}
C {devices/lab_pin.sym} 3080 -180 0 0 {name=l112 lab=vdd}
C {devices/lab_pin.sym} 3240 -180 0 0 {name=l113 lab=vdd}
C {devices/lab_pin.sym} 2920 310 0 0 {name=l114 lab=vss}
C {devices/lab_wire.sym} 3340 -55 0 0 {name=l115 lab=qn}
C {g1_node_lab.sym} 3520 -445 0 0 {name=l116 lab=ND1_i}
C {devices/lab_pin.sym} 3520 -720 0 0 {name=l117 lab=vdd}
C {devices/lab_pin.sym} 3680 -720 0 0 {name=l118 lab=vdd}
C {devices/lab_pin.sym} 3520 -340 0 0 {name=l119 lab=vss}
C {devices/lab_wire.sym} 3780 -595 0 0 {name=l120 lab=d1g}
C {g1_node_lab.sym} 3520 95 0 0 {name=l121 lab=ND2_i}
C {devices/lab_pin.sym} 3520 -180 0 0 {name=l122 lab=vdd}
C {devices/lab_pin.sym} 3680 -180 0 0 {name=l123 lab=vdd}
C {devices/lab_pin.sym} 3520 200 0 0 {name=l124 lab=vss}
C {devices/lab_wire.sym} 3780 -55 0 0 {name=l125 lab=d2g}
C {devices/lab_pin.sym} 4020 -550 0 0 {name=l126 lab=vdd}
C {devices/lab_pin.sym} 4020 -330 0 0 {name=l127 lab=vss}
C {devices/lab_pin.sym} 3940 -440 0 0 {name=l128 lab=d2g}
C {devices/lab_wire.sym} 4080 -440 0 0 {name=l129 lab=a}
C {devices/lab_pin.sym} 4220 -455 0 0 {name=l130 lab=lsa}
C {devices/lab_pin.sym} 4420 -455 0 1 {name=l131 lab=lsb}
C {devices/lab_pin.sym} 4350 -380 0 0 {name=l132 lab=d2g}
C {devices/lab_pin.sym} 4220 -330 0 0 {name=l133 lab=vss}
C {devices/lab_pin.sym} 4420 -330 0 0 {name=l134 lab=vss}
C {devices/lab_pin.sym} 4220 -560 0 0 {name=l135 lab=vdd12}
C {devices/lab_pin.sym} 4420 -560 0 0 {name=l136 lab=vdd12}
C {devices/lab_pin.sym} 4620 -550 0 0 {name=l137 lab=vdd12}
C {devices/lab_pin.sym} 4620 -330 0 0 {name=l138 lab=vss}
C {devices/lab_pin.sym} 4800 -550 0 0 {name=l139 lab=vdd12}
C {devices/lab_pin.sym} 4800 -330 0 0 {name=l140 lab=vss}
C {devices/lab_wire.sym} 4720 -440 0 0 {name=l141 lab=fon}
C {devices/lab_pin.sym} 220 -770 0 1 {name=l142 lab=do}
C {devices/lab_pin.sym} 420 -770 0 1 {name=l143 lab=dr}
C {devices/lab_pin.sym} 620 -770 0 1 {name=l144 lab=db}
C {devices/lab_pin.sym} 2880 -670 0 0 {name=l145 lab=sn}
C {devices/lab_pin.sym} 3040 -670 0 0 {name=l146 lab=qn}
C {devices/lab_pin.sym} 2880 -390 0 0 {name=l147 lab=qn}
C {devices/lab_pin.sym} 2880 -130 0 0 {name=l148 lab=rn}
C {devices/lab_pin.sym} 3040 -130 0 0 {name=l149 lab=q}
C {devices/lab_pin.sym} 3200 -130 0 0 {name=l150 lab=en}
C {devices/lab_pin.sym} 2880 150 0 0 {name=l151 lab=q}
C {devices/lab_pin.sym} 2880 260 0 0 {name=l152 lab=en}
C {devices/lab_pin.sym} 3480 -670 0 0 {name=l153 lab=qn}
C {devices/lab_pin.sym} 3640 -670 0 0 {name=l154 lab=en}
C {devices/lab_pin.sym} 3480 -390 0 0 {name=l155 lab=en}
C {devices/lab_pin.sym} 3480 -130 0 0 {name=l156 lab=q}
C {devices/lab_pin.sym} 3640 -130 0 0 {name=l157 lab=en}
C {devices/lab_pin.sym} 3480 150 0 0 {name=l158 lab=en}
N 220 -800 220 -830 {}
N 220 -690 220 -720 {}
N 420 -800 420 -830 {}
N 420 -690 420 -720 {}
N 620 -800 620 -830 {}
N 620 -690 620 -720 {}
N 620 -380 620 -350 {}
N 820 -800 820 -830 {}
N 820 -620 820 -650 {}
N 1100 -300 1100 -270 {}
N 1100 -420 1100 -450 {}
N 1740 -460 1740 -430 {}
N 2080 -460 2080 -430 {}
N 1820 -660 1820 -690 {}
N 2020 -660 2020 -690 {}
N 1920 -300 1920 -270 {}
N 2240 -520 2240 -490 {}
N 2240 -640 2240 -670 {}
N 2420 -520 2420 -490 {}
N 2420 -640 2420 -670 {}
N 1740 160 1740 190 {}
N 2080 160 2080 190 {}
N 1820 -40 1820 -70 {}
N 2020 -40 2020 -70 {}
N 1920 320 1920 350 {}
N 2240 100 2240 130 {}
N 2240 -20 2240 -50 {}
N 2420 100 2420 130 {}
N 2420 -20 2420 -50 {}
N 2920 -670 2920 -700 {}
N 3080 -670 3080 -700 {}
N 2920 -390 2920 -360 {}
N 2920 -130 2920 -160 {}
N 3080 -130 3080 -160 {}
N 3240 -130 3240 -160 {}
N 2920 260 2920 290 {}
N 3520 -670 3520 -700 {}
N 3680 -670 3680 -700 {}
N 3520 -390 3520 -360 {}
N 3520 -130 3520 -160 {}
N 3680 -130 3680 -160 {}
N 3520 150 3520 180 {}
N 1420 -360 1420 -330 {}
N 1420 260 1420 290 {}
N 4020 -380 4020 -350 {}
N 4020 -500 4020 -530 {}
N 4220 -380 4220 -350 {}
N 4420 -380 4420 -350 {}
N 4220 -510 4220 -540 {}
N 4420 -510 4420 -540 {}
N 4620 -380 4620 -350 {}
N 4620 -500 4620 -530 {}
N 4800 -380 4800 -350 {}
N 4800 -500 4800 -530 {}
N 220 -770 220 -720 {}
N 220 -830 220 -850 {}
N 420 -770 420 -720 {}
N 420 -830 420 -850 {}
N 620 -770 620 -720 {}
N 620 -830 620 -850 {}
N 180 -800 160 -800 {}
N 160 -800 160 -840 {}
N 160 -840 780 -840 {}
N 780 -840 780 -800 {}
N 380 -800 380 -840 {}
N 580 -800 580 -840 {}
N 180 -690 170 -690 {}
N 170 -690 170 -650 {}
N 170 -650 560 -650 {}
N 560 -650 580 -650 {}
N 580 -650 580 -690 {}
N 380 -690 380 -650 {}
N 220 -660 220 -600 {}
N 420 -660 420 -610 {}
N 420 -550 420 -530 {}
N 420 -470 420 -450 {}
N 420 -390 420 -370 {}
N 420 -310 420 -290 {}
N 420 -230 420 -210 {}
N 420 -150 420 -130 {}
N 420 -70 420 -50 {}
N 420 10 420 30 {}
N 420 90 420 110 {}
N 420 170 420 190 {}
N 620 -660 620 -410 {}
N 580 -380 580 -440 {}
N 580 -440 620 -440 {}
N 620 -350 620 -330 {}
N 820 -770 820 -650 {}
N 820 -830 820 -850 {}
N 780 -620 750 -620 {}
N 820 -590 820 -570 {}
N 1020 -590 1020 -560 {}
N 1020 -560 1180 -560 {}
N 1180 -560 1180 -590 {}
N 1100 -560 1100 -530 {}
N 1020 -650 1020 -670 {}
N 1180 -650 1180 -670 {}
N 980 -620 950 -620 {}
N 1140 -620 1110 -620 {}
N 1060 -420 1060 -300 {}
N 1100 -390 1100 -330 {}
N 1060 -360 1020 -360 {}
N 1100 -360 1180 -360 {}
N 1100 -450 1100 -470 {}
N 1100 -270 1100 -250 {}
N 1380 -480 1380 -360 {}
N 1420 -450 1420 -390 {}
N 1380 -420 1340 -420 {}
N 1420 -420 1540 -420 {}
N 1420 -510 1420 -530 {}
N 1420 -330 1420 -310 {}
N 1540 -360 1540 -340 {}
N 1380 140 1380 260 {}
N 1420 170 1420 230 {}
N 1380 200 1340 200 {}
N 1420 200 1540 200 {}
N 1420 110 1420 90 {}
N 1420 290 1420 310 {}
N 1540 260 1540 280 {}
N 1820 -630 1820 -570 {}
N 2020 -630 2020 -570 {}
N 1860 -660 1980 -660 {}
N 1900 -660 1900 -610 {}
N 1900 -610 1820 -610 {}
N 1860 -540 1980 -540 {}
N 1820 -510 1820 -450 {}
N 2020 -510 2020 -450 {}
N 1740 -490 1740 -480 {}
N 1740 -480 1820 -480 {}
N 2080 -490 2080 -480 {}
N 2080 -480 2020 -480 {}
N 1700 -460 1670 -460 {}
N 2120 -460 2150 -460 {}
N 1740 -430 1740 -410 {}
N 2080 -430 2080 -410 {}
N 1820 -390 1820 -360 {}
N 1820 -360 2020 -360 {}
N 2020 -360 2020 -390 {}
N 1920 -330 1920 -360 {}
N 1880 -300 1850 -300 {}
N 1920 -270 1920 -250 {}
N 1780 -420 1750 -420 {}
N 2060 -420 2090 -420 {}
N 1820 -690 1820 -710 {}
N 2020 -690 2020 -710 {}
N 2200 -640 2200 -520 {}
N 2240 -610 2240 -550 {}
N 2240 -670 2240 -690 {}
N 2240 -490 2240 -470 {}
N 2380 -640 2380 -520 {}
N 2420 -610 2420 -550 {}
N 2420 -670 2420 -690 {}
N 2420 -490 2420 -470 {}
N 2020 -600 2200 -600 {}
N 2240 -580 2380 -580 {}
N 2420 -580 2520 -580 {}
N 1820 -10 1820 50 {}
N 2020 -10 2020 50 {}
N 1860 -40 1980 -40 {}
N 1900 -40 1900 10 {}
N 1900 10 1820 10 {}
N 1860 80 1980 80 {}
N 1820 110 1820 170 {}
N 2020 110 2020 170 {}
N 1740 130 1740 140 {}
N 1740 140 1820 140 {}
N 2080 130 2080 140 {}
N 2080 140 2020 140 {}
N 1700 160 1670 160 {}
N 2120 160 2150 160 {}
N 1740 190 1740 210 {}
N 2080 190 2080 210 {}
N 1820 230 1820 260 {}
N 1820 260 2020 260 {}
N 2020 260 2020 230 {}
N 1920 290 1920 260 {}
N 1880 320 1850 320 {}
N 1920 350 1920 370 {}
N 1780 200 1750 200 {}
N 2060 200 2090 200 {}
N 1820 -70 1820 -90 {}
N 2020 -70 2020 -90 {}
N 2200 -20 2200 100 {}
N 2240 10 2240 70 {}
N 2240 -50 2240 -70 {}
N 2240 130 2240 150 {}
N 2380 -20 2380 100 {}
N 2420 10 2420 70 {}
N 2420 -50 2420 -70 {}
N 2420 130 2420 150 {}
N 2020 20 2200 20 {}
N 2240 40 2380 40 {}
N 2420 40 2520 40 {}
N 2920 -640 2920 -595 {}
N 2920 -595 3080 -595 {}
N 3080 -640 3080 -595 {}
N 2920 -595 2920 -530 {}
N 2920 -470 2920 -420 {}
N 2880 -670 2880 -500 {}
N 2920 -700 2920 -720 {}
N 3080 -700 3080 -720 {}
N 2920 -360 2920 -340 {}
N 3080 -595 3180 -595 {}
N 2920 -100 2920 -55 {}
N 2920 -55 3240 -55 {}
N 3080 -100 3080 -55 {}
N 3240 -100 3240 -55 {}
N 2920 -55 2920 10 {}
N 2920 70 2920 120 {}
N 2920 180 2920 230 {}
N 2880 -130 2880 40 {}
N 2920 -160 2920 -180 {}
N 3080 -160 3080 -180 {}
N 3240 -160 3240 -180 {}
N 2920 290 2920 310 {}
N 3240 -55 3340 -55 {}
N 3520 -640 3520 -595 {}
N 3520 -595 3680 -595 {}
N 3680 -640 3680 -595 {}
N 3520 -595 3520 -530 {}
N 3520 -470 3520 -420 {}
N 3480 -670 3480 -500 {}
N 3520 -700 3520 -720 {}
N 3680 -700 3680 -720 {}
N 3520 -360 3520 -340 {}
N 3680 -595 3780 -595 {}
N 3520 -100 3520 -55 {}
N 3520 -55 3680 -55 {}
N 3680 -100 3680 -55 {}
N 3520 -55 3520 10 {}
N 3520 70 3520 120 {}
N 3480 -130 3480 40 {}
N 3520 -160 3520 -180 {}
N 3680 -160 3680 -180 {}
N 3520 180 3520 200 {}
N 3680 -55 3780 -55 {}
N 3980 -500 3980 -380 {}
N 4020 -470 4020 -410 {}
N 4020 -530 4020 -550 {}
N 4020 -350 4020 -330 {}
N 3980 -440 3940 -440 {}
N 4020 -440 4100 -440 {}
N 4100 -440 4100 -380 {}
N 4100 -380 4180 -380 {}
N 4220 -480 4220 -410 {}
N 4420 -480 4420 -410 {}
N 4220 -470 4350 -470 {}
N 4350 -470 4350 -510 {}
N 4350 -510 4380 -510 {}
N 4420 -430 4160 -430 {}
N 4160 -430 4160 -510 {}
N 4160 -510 4180 -510 {}
N 4380 -380 4350 -380 {}
N 4220 -350 4220 -330 {}
N 4420 -350 4420 -330 {}
N 4220 -540 4220 -560 {}
N 4420 -540 4420 -560 {}
N 4580 -500 4580 -380 {}
N 4620 -470 4620 -410 {}
N 4620 -530 4620 -550 {}
N 4620 -350 4620 -330 {}
N 4760 -500 4760 -380 {}
N 4800 -470 4800 -410 {}
N 4800 -530 4800 -550 {}
N 4800 -350 4800 -330 {}
N 4420 -450 4500 -450 {}
N 4500 -450 4500 -440 {}
N 4500 -440 4580 -440 {}
N 4620 -440 4760 -440 {}
N 4800 -440 4950 -440 {}

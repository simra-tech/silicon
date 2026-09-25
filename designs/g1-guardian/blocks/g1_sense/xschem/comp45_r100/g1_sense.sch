v {xschem version=3.4.8RC file_version=1.3}
G {}
K {}
V {}
S {}
E {}
B 4 100 -2560 2000 -2408 {fill=false}
T {iptat: 4.13 uA PTAT from G1_BGR into MBI; the three OTAs run at about 350 uA each (PTAT).} 100 40 0 0 0.3 0.3 {}
T {g1_sense - low-side shunt amplifier: gain 20 difference amplifier + VREF-derived 1.0 V pedestal} 112 -2550 0 0 0.55 0.55 {}
T {G1 guardian, chip of record g1_chip_top_1414_r2.gds 9049e87b (r2 2026-09-25; geometry XOR-identical to r1 629d303a); block map: g1_padring/reports/signoff-1414-20260924} 112 -2511 0 0 0.3 0.3 {}
T {On-chip variant: comp45 + R100, the SENSE amplifier on the chip: layout g1_sense_physical.gds 450a4906, LVS reference native-reference CDL 696b43fd} 112 -2487 0 0 0.3 0.3 {}
T {Netlist-equivalent to reports/rz100-partial-field-evidence-20260923-r1/sense-comp45-rz100-actual-source-20260923-r1/candidate.spice sha256 aeee4d41 (source bb933fda)} 112 -2463 0 0 0.3 0.3 {}
T {Drawn 2026-09-25 by the block generator; device sizes (w, l, ng, m) are on each symbol. Proof: review/schematics-readability-20260925} 112 -2439 0 0 0.25 0.25 {}
C {sg13g2_pr/rppd.sym} 400 -1310 3 0 {name=R1N0 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 900 -2150 0 0 {name=R2N0 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 900 -2070 0 0 {name=R2N1 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 900 -1990 0 0 {name=R2N2 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 900 -1910 0 0 {name=R2N3 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 900 -1830 0 0 {name=R2N4 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 900 -1750 0 0 {name=R2N5 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 900 -1670 0 0 {name=R2N6 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 900 -1590 0 0 {name=R2N7 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 900 -1510 0 0 {name=R2N8 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 900 -1430 0 0 {name=R2N9 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 1070 -1430 2 1 {name=R2N10 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 1070 -1510 2 1 {name=R2N11 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 1070 -1590 2 1 {name=R2N12 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 1070 -1670 2 1 {name=R2N13 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 1070 -1750 2 1 {name=R2N14 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 1070 -1830 2 1 {name=R2N15 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 1070 -1910 2 1 {name=R2N16 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 1070 -1990 2 1 {name=R2N17 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 1070 -2070 2 1 {name=R2N18 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 1070 -2150 2 1 {name=R2N19 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 400 -1100 3 0 {name=R1P0 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 560 -1000 0 0 {name=R2P0 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 560 -920 0 0 {name=R2P1 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 560 -840 0 0 {name=R2P2 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 560 -760 0 0 {name=R2P3 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 560 -680 0 0 {name=R2P4 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 560 -600 0 0 {name=R2P5 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 560 -520 0 0 {name=R2P6 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 560 -440 0 0 {name=R2P7 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 560 -360 0 0 {name=R2P8 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 560 -280 0 0 {name=R2P9 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 730 -280 2 1 {name=R2P10 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 730 -360 2 1 {name=R2P11 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 730 -440 2 1 {name=R2P12 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 730 -520 2 1 {name=R2P13 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 730 -600 2 1 {name=R2P14 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 730 -680 2 1 {name=R2P15 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 730 -760 2 1 {name=R2P16 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 730 -840 2 1 {name=R2P17 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 730 -920 2 1 {name=R2P18 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 730 -1000 2 1 {name=R2P19 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 1700 -560 0 0 {name=RD10 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 1700 -480 0 0 {name=RD11 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 1900 -560 0 0 {name=RD20 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 1900 -480 0 0 {name=RD21 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 1900 -400 0 0 {name=RD22 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 1900 -320 0 0 {name=RD23 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 1900 -240 0 0 {name=RD24 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 1900 -160 0 0 {name=RD25 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 1900 -80 0 0 {name=RD26 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 1900 0 0 0 {name=RD27 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 1900 80 0 0 {name=RD28 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 1900 160 0 0 {name=RD29 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 2070 160 2 1 {name=RD210 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 2070 80 2 1 {name=RD211 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 2070 0 2 1 {name=RD212 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 2070 -80 2 1 {name=RD213 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 2070 -160 2 1 {name=RD214 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 2070 -240 2 1 {name=RD215 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 2070 -320 2 1 {name=RD216 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 2070 -400 2 1 {name=RD217 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 2070 -480 2 1 {name=RD218 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 2070 -560 2 1 {name=RD219 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 2240 -560 0 0 {name=RD220 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 2240 -480 0 0 {name=RD221 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 2240 -400 0 0 {name=RD222 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 2240 -320 0 0 {name=RD223 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 2240 -240 0 0 {name=RD224 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 2240 -160 0 0 {name=RD225 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 2240 -80 0 0 {name=RD226 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 2240 0 0 0 {name=RD227 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 2240 80 0 0 {name=RD228 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 2240 160 0 0 {name=RD229 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 2410 160 2 1 {name=RD230 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 2410 80 2 1 {name=RD231 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 2410 0 2 1 {name=RD232 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 2410 -80 2 1 {name=RD233 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 2410 -160 2 1 {name=RD234 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 2410 -240 2 1 {name=RD235 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 2410 -320 2 1 {name=RD236 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 2410 -400 2 1 {name=RD237 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 2410 -480 2 1 {name=RD238 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 2410 -560 2 1 {name=RD239 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 2580 -560 0 0 {name=RD240 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 2580 -480 0 0 {name=RD241 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 2580 -400 0 0 {name=RD242 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 2580 -320 0 0 {name=RD243 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 2580 -240 0 0 {name=RD244 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 2580 -160 0 0 {name=RD245 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 2580 -80 0 0 {name=RD246 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 2580 0 0 0 {name=RD247 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 2580 80 0 0 {name=RD248 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 2580 160 0 0 {name=RD249 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/rppd.sym} 2750 160 2 1 {name=RD250 w=2u l=76.7u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/sg13_hv_nmos.sym} 300 -300 0 0 {name=MBI model=sg13_hv_nmos w=3.3u l=1u ng=1 m=1}
C {g1_ota_main_candidate.sym} 1400 -1300 0 0 {name=XOTA }
C {g1_ota.sym} 1300 -850 0 0 {name=XBUF }
C {g1_ota.sym} 1300 -500 0 0 {name=XREF }
C {devices/ipin.sym} 100 -1100 0 0 {name=p0 lab=sense_p}
C {devices/ipin.sym} 100 -1310 0 0 {name=p1 lab=sense_n}
C {devices/ipin.sym} 1000 -490 0 0 {name=p2 lab=vref}
C {devices/ipin.sym} 100 -360 0 0 {name=p3 lab=iptat}
C {devices/opin.sym} 1900 -1300 0 0 {name=p4 lab=isense}
C {devices/opin.sym} 1900 -850 0 0 {name=p5 lab=vped}
C {devices/opin.sym} 1500 -380 0 0 {name=p6 lab=vref_buf}
C {devices/iopin.sym} 100 -200 0 0 {name=p7 lab=vdd}
C {devices/iopin.sym} 100 -170 0 0 {name=p8 lab=vss}
C {g1_node_lab.sym} 900 -2110 0 0 {name=l1 lab=R2N_0}
C {g1_node_lab.sym} 900 -2030 0 0 {name=l2 lab=R2N_1}
C {g1_node_lab.sym} 900 -1950 0 0 {name=l3 lab=R2N_2}
C {g1_node_lab.sym} 900 -1870 0 0 {name=l4 lab=R2N_3}
C {g1_node_lab.sym} 900 -1790 0 0 {name=l5 lab=R2N_4}
C {g1_node_lab.sym} 900 -1710 0 0 {name=l6 lab=R2N_5}
C {g1_node_lab.sym} 900 -1630 0 0 {name=l7 lab=R2N_6}
C {g1_node_lab.sym} 900 -1550 0 0 {name=l8 lab=R2N_7}
C {g1_node_lab.sym} 900 -1470 0 0 {name=l9 lab=R2N_8}
C {g1_node_lab.sym} 985 -1380 0 0 {name=l10 lab=R2N_9}
C {g1_node_lab.sym} 1070 -1470 0 0 {name=l11 lab=R2N_10}
C {g1_node_lab.sym} 1070 -1550 0 0 {name=l12 lab=R2N_11}
C {g1_node_lab.sym} 1070 -1630 0 0 {name=l13 lab=R2N_12}
C {g1_node_lab.sym} 1070 -1710 0 0 {name=l14 lab=R2N_13}
C {g1_node_lab.sym} 1070 -1790 0 0 {name=l15 lab=R2N_14}
C {g1_node_lab.sym} 1070 -1870 0 0 {name=l16 lab=R2N_15}
C {g1_node_lab.sym} 1070 -1950 0 0 {name=l17 lab=R2N_16}
C {g1_node_lab.sym} 1070 -2030 0 0 {name=l18 lab=R2N_17}
C {g1_node_lab.sym} 1070 -2110 0 0 {name=l19 lab=R2N_18}
C {g1_node_lab.sym} 560 -960 0 0 {name=l20 lab=R2P_0}
C {g1_node_lab.sym} 560 -880 0 0 {name=l21 lab=R2P_1}
C {g1_node_lab.sym} 560 -800 0 0 {name=l22 lab=R2P_2}
C {g1_node_lab.sym} 560 -720 0 0 {name=l23 lab=R2P_3}
C {g1_node_lab.sym} 560 -640 0 0 {name=l24 lab=R2P_4}
C {g1_node_lab.sym} 560 -560 0 0 {name=l25 lab=R2P_5}
C {g1_node_lab.sym} 560 -480 0 0 {name=l26 lab=R2P_6}
C {g1_node_lab.sym} 560 -400 0 0 {name=l27 lab=R2P_7}
C {g1_node_lab.sym} 560 -320 0 0 {name=l28 lab=R2P_8}
C {g1_node_lab.sym} 645 -230 0 0 {name=l29 lab=R2P_9}
C {g1_node_lab.sym} 730 -320 0 0 {name=l30 lab=R2P_10}
C {g1_node_lab.sym} 730 -400 0 0 {name=l31 lab=R2P_11}
C {g1_node_lab.sym} 730 -480 0 0 {name=l32 lab=R2P_12}
C {g1_node_lab.sym} 730 -560 0 0 {name=l33 lab=R2P_13}
C {g1_node_lab.sym} 730 -640 0 0 {name=l34 lab=R2P_14}
C {g1_node_lab.sym} 730 -720 0 0 {name=l35 lab=R2P_15}
C {g1_node_lab.sym} 730 -800 0 0 {name=l36 lab=R2P_16}
C {g1_node_lab.sym} 730 -880 0 0 {name=l37 lab=R2P_17}
C {g1_node_lab.sym} 730 -960 0 0 {name=l38 lab=R2P_18}
C {g1_node_lab.sym} 1700 -520 0 0 {name=l39 lab=RD1_0}
C {g1_node_lab.sym} 1900 -520 0 0 {name=l40 lab=RD2_0}
C {g1_node_lab.sym} 1900 -440 0 0 {name=l41 lab=RD2_1}
C {g1_node_lab.sym} 1900 -360 0 0 {name=l42 lab=RD2_2}
C {g1_node_lab.sym} 1900 -280 0 0 {name=l43 lab=RD2_3}
C {g1_node_lab.sym} 1900 -200 0 0 {name=l44 lab=RD2_4}
C {g1_node_lab.sym} 1900 -120 0 0 {name=l45 lab=RD2_5}
C {g1_node_lab.sym} 1900 -40 0 0 {name=l46 lab=RD2_6}
C {g1_node_lab.sym} 1900 40 0 0 {name=l47 lab=RD2_7}
C {g1_node_lab.sym} 1900 120 0 0 {name=l48 lab=RD2_8}
C {g1_node_lab.sym} 1985 210 0 0 {name=l49 lab=RD2_9}
C {g1_node_lab.sym} 2070 120 0 0 {name=l50 lab=RD2_10}
C {g1_node_lab.sym} 2070 40 0 0 {name=l51 lab=RD2_11}
C {g1_node_lab.sym} 2070 -40 0 0 {name=l52 lab=RD2_12}
C {g1_node_lab.sym} 2070 -120 0 0 {name=l53 lab=RD2_13}
C {g1_node_lab.sym} 2070 -200 0 0 {name=l54 lab=RD2_14}
C {g1_node_lab.sym} 2070 -280 0 0 {name=l55 lab=RD2_15}
C {g1_node_lab.sym} 2070 -360 0 0 {name=l56 lab=RD2_16}
C {g1_node_lab.sym} 2070 -440 0 0 {name=l57 lab=RD2_17}
C {g1_node_lab.sym} 2070 -520 0 0 {name=l58 lab=RD2_18}
C {g1_node_lab.sym} 2155 -610 0 0 {name=l59 lab=RD2_19}
C {g1_node_lab.sym} 2240 -520 0 0 {name=l60 lab=RD2_20}
C {g1_node_lab.sym} 2240 -440 0 0 {name=l61 lab=RD2_21}
C {g1_node_lab.sym} 2240 -360 0 0 {name=l62 lab=RD2_22}
C {g1_node_lab.sym} 2240 -280 0 0 {name=l63 lab=RD2_23}
C {g1_node_lab.sym} 2240 -200 0 0 {name=l64 lab=RD2_24}
C {g1_node_lab.sym} 2240 -120 0 0 {name=l65 lab=RD2_25}
C {g1_node_lab.sym} 2240 -40 0 0 {name=l66 lab=RD2_26}
C {g1_node_lab.sym} 2240 40 0 0 {name=l67 lab=RD2_27}
C {g1_node_lab.sym} 2240 120 0 0 {name=l68 lab=RD2_28}
C {g1_node_lab.sym} 2325 210 0 0 {name=l69 lab=RD2_29}
C {g1_node_lab.sym} 2410 120 0 0 {name=l70 lab=RD2_30}
C {g1_node_lab.sym} 2410 40 0 0 {name=l71 lab=RD2_31}
C {g1_node_lab.sym} 2410 -40 0 0 {name=l72 lab=RD2_32}
C {g1_node_lab.sym} 2410 -120 0 0 {name=l73 lab=RD2_33}
C {g1_node_lab.sym} 2410 -200 0 0 {name=l74 lab=RD2_34}
C {g1_node_lab.sym} 2410 -280 0 0 {name=l75 lab=RD2_35}
C {g1_node_lab.sym} 2410 -360 0 0 {name=l76 lab=RD2_36}
C {g1_node_lab.sym} 2410 -440 0 0 {name=l77 lab=RD2_37}
C {g1_node_lab.sym} 2410 -520 0 0 {name=l78 lab=RD2_38}
C {g1_node_lab.sym} 2495 -610 0 0 {name=l79 lab=RD2_39}
C {g1_node_lab.sym} 2580 -520 0 0 {name=l80 lab=RD2_40}
C {g1_node_lab.sym} 2580 -440 0 0 {name=l81 lab=RD2_41}
C {g1_node_lab.sym} 2580 -360 0 0 {name=l82 lab=RD2_42}
C {g1_node_lab.sym} 2580 -280 0 0 {name=l83 lab=RD2_43}
C {g1_node_lab.sym} 2580 -200 0 0 {name=l84 lab=RD2_44}
C {g1_node_lab.sym} 2580 -120 0 0 {name=l85 lab=RD2_45}
C {g1_node_lab.sym} 2580 -40 0 0 {name=l86 lab=RD2_46}
C {g1_node_lab.sym} 2580 40 0 0 {name=l87 lab=RD2_47}
C {g1_node_lab.sym} 2580 120 0 0 {name=l88 lab=RD2_48}
C {g1_node_lab.sym} 2665 210 0 0 {name=l89 lab=RD2_49}
C {devices/lab_pin.sym} 1380 -1230 0 0 {name=l90 lab=iptat}
C {devices/lab_pin.sym} 1400 -1370 0 1 {name=l91 lab=vdd}
C {devices/lab_pin.sym} 1420 -1230 0 1 {name=l92 lab=vss}
C {devices/lab_pin.sym} 1280 -780 0 0 {name=l93 lab=iptat}
C {devices/lab_pin.sym} 1300 -920 0 1 {name=l94 lab=vdd}
C {devices/lab_pin.sym} 1320 -780 0 1 {name=l95 lab=vss}
C {devices/lab_pin.sym} 1280 -430 0 0 {name=l96 lab=iptat}
C {devices/lab_pin.sym} 1300 -570 0 1 {name=l97 lab=vdd}
C {devices/lab_pin.sym} 1320 -430 0 1 {name=l98 lab=vss}
C {devices/lab_wire.sym} 600 -1310 0 0 {name=l99 lab=vn}
C {devices/lab_wire.sym} 520 -1100 0 0 {name=l100 lab=vp}
C {devices/lab_wire.sym} 1760 -1300 0 0 {name=l101 lab=isense}
C {devices/lab_wire.sym} 1000 -1060 0 0 {name=l102 lab=vped}
C {devices/lab_wire.sym} 1560 -500 0 0 {name=l103 lab=vref_buf}
C {devices/lab_wire.sym} 1840 -420 0 0 {name=l104 lab=vped_ref}
C {devices/lab_pin.sym} 2750 150 0 0 {name=l105 lab=vss}
C {devices/lab_pin.sym} 1190 -840 0 0 {name=l106 lab=vped_ref}
C {devices/lab_wire.sym} 1560 -850 0 0 {name=l107 lab=vped}
C {devices/lab_pin.sym} 320 -250 0 0 {name=l108 lab=vss}
N 900 -2120 900 -2100 {}
N 900 -2040 900 -2020 {}
N 900 -1960 900 -1940 {}
N 900 -1880 900 -1860 {}
N 900 -1800 900 -1780 {}
N 900 -1720 900 -1700 {}
N 900 -1640 900 -1620 {}
N 900 -1560 900 -1540 {}
N 900 -1480 900 -1460 {}
N 900 -1400 900 -1380 {}
N 900 -1380 1070 -1380 {}
N 1070 -1380 1070 -1400 {}
N 1070 -1460 1070 -1480 {}
N 1070 -1540 1070 -1560 {}
N 1070 -1620 1070 -1640 {}
N 1070 -1700 1070 -1720 {}
N 1070 -1780 1070 -1800 {}
N 1070 -1860 1070 -1880 {}
N 1070 -1940 1070 -1960 {}
N 1070 -2020 1070 -2040 {}
N 1070 -2100 1070 -2120 {}
N 560 -970 560 -950 {}
N 560 -890 560 -870 {}
N 560 -810 560 -790 {}
N 560 -730 560 -710 {}
N 560 -650 560 -630 {}
N 560 -570 560 -550 {}
N 560 -490 560 -470 {}
N 560 -410 560 -390 {}
N 560 -330 560 -310 {}
N 560 -250 560 -230 {}
N 560 -230 730 -230 {}
N 730 -230 730 -250 {}
N 730 -310 730 -330 {}
N 730 -390 730 -410 {}
N 730 -470 730 -490 {}
N 730 -550 730 -570 {}
N 730 -630 730 -650 {}
N 730 -710 730 -730 {}
N 730 -790 730 -810 {}
N 730 -870 730 -890 {}
N 730 -950 730 -970 {}
N 1700 -530 1700 -510 {}
N 1900 -530 1900 -510 {}
N 1900 -450 1900 -430 {}
N 1900 -370 1900 -350 {}
N 1900 -290 1900 -270 {}
N 1900 -210 1900 -190 {}
N 1900 -130 1900 -110 {}
N 1900 -50 1900 -30 {}
N 1900 30 1900 50 {}
N 1900 110 1900 130 {}
N 1900 190 1900 210 {}
N 1900 210 2070 210 {}
N 2070 210 2070 190 {}
N 2070 130 2070 110 {}
N 2070 50 2070 30 {}
N 2070 -30 2070 -50 {}
N 2070 -110 2070 -130 {}
N 2070 -190 2070 -210 {}
N 2070 -270 2070 -290 {}
N 2070 -350 2070 -370 {}
N 2070 -430 2070 -450 {}
N 2070 -510 2070 -530 {}
N 2070 -590 2070 -610 {}
N 2070 -610 2240 -610 {}
N 2240 -610 2240 -590 {}
N 2240 -530 2240 -510 {}
N 2240 -450 2240 -430 {}
N 2240 -370 2240 -350 {}
N 2240 -290 2240 -270 {}
N 2240 -210 2240 -190 {}
N 2240 -130 2240 -110 {}
N 2240 -50 2240 -30 {}
N 2240 30 2240 50 {}
N 2240 110 2240 130 {}
N 2240 190 2240 210 {}
N 2240 210 2410 210 {}
N 2410 210 2410 190 {}
N 2410 130 2410 110 {}
N 2410 50 2410 30 {}
N 2410 -30 2410 -50 {}
N 2410 -110 2410 -130 {}
N 2410 -190 2410 -210 {}
N 2410 -270 2410 -290 {}
N 2410 -350 2410 -370 {}
N 2410 -430 2410 -450 {}
N 2410 -510 2410 -530 {}
N 2410 -590 2410 -610 {}
N 2410 -610 2580 -610 {}
N 2580 -610 2580 -590 {}
N 2580 -530 2580 -510 {}
N 2580 -450 2580 -430 {}
N 2580 -370 2580 -350 {}
N 2580 -290 2580 -270 {}
N 2580 -210 2580 -190 {}
N 2580 -130 2580 -110 {}
N 2580 -50 2580 -30 {}
N 2580 30 2580 50 {}
N 2580 110 2580 130 {}
N 2580 190 2580 210 {}
N 2580 210 2750 210 {}
N 2750 210 2750 190 {}
N 320 -300 320 -270 {}
N 1380 -1250 1380 -1230 {}
N 1400 -1350 1400 -1370 {}
N 1420 -1250 1420 -1230 {}
N 1280 -800 1280 -780 {}
N 1300 -900 1300 -920 {}
N 1320 -800 1320 -780 {}
N 1280 -450 1280 -430 {}
N 1300 -550 1300 -570 {}
N 1320 -450 1320 -430 {}
N 100 -1100 370 -1100 {}
N 100 -1310 370 -1310 {}
N 430 -1310 1330 -1310 {}
N 700 -1310 700 -2220 {}
N 700 -2220 900 -2220 {}
N 900 -2220 900 -2180 {}
N 430 -1100 1200 -1100 {}
N 1200 -1100 1200 -1290 {}
N 1200 -1290 1330 -1290 {}
N 560 -1100 560 -1030 {}
N 1070 -2180 1070 -2220 {}
N 1070 -2220 1600 -2220 {}
N 1600 -2220 1600 -1300 {}
N 1470 -1300 1800 -1300 {}
N 730 -1030 730 -1060 {}
N 730 -1060 1000 -1060 {}
N 1000 -490 1230 -490 {}
N 1370 -500 1420 -500 {}
N 1420 -500 1420 -600 {}
N 1420 -600 1210 -600 {}
N 1210 -600 1210 -510 {}
N 1210 -510 1230 -510 {}
N 1420 -500 1600 -500 {}
N 1500 -500 1500 -380 {}
N 1600 -500 1600 -620 {}
N 1600 -620 1700 -620 {}
N 1700 -620 1700 -590 {}
N 1700 -450 1700 -420 {}
N 1700 -420 1850 -420 {}
N 1850 -420 1850 -620 {}
N 1850 -620 1900 -620 {}
N 1900 -620 1900 -590 {}
N 2750 130 2750 150 {}
N 1230 -840 1190 -840 {}
N 1370 -850 1420 -850 {}
N 1420 -850 1420 -950 {}
N 1420 -950 1210 -950 {}
N 1210 -950 1210 -860 {}
N 1210 -860 1230 -860 {}
N 1420 -850 1560 -850 {}
N 100 -360 320 -360 {}
N 320 -360 320 -330 {}
N 280 -300 280 -360 {}
N 320 -270 320 -250 {}
N 1800 -1300 1900 -1300 {}
N 1560 -850 1900 -850 {}

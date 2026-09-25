v {xschem version=3.4.8RC file_version=1.3}
G {}
K {}
V {}
S {}
E {}
B 4 130 -770 700 -120 {dash=5 fill=false}
B 4 1130 -760 1540 -400 {dash=5 fill=false}
B 4 1680 -770 2000 -120 {dash=5 fill=false}
B 4 130 -1060 2076 -908 {fill=false}
T {bias: Sooch wide-swing cascode (vbp, vbnc, vbpc from vbn)} 138 -764 0 0 0.3 0.3 {layer=4}
T {PMOS input pair + tail} 1138 -754 0 0 0.3 0.3 {layer=4}
T {CS output stage + Miller RZ/CC} 1688 -764 0 0 0.3 0.3 {layer=4}
T {comp45 + R100: M1/M2 4x wider, NMOS/PMOS sources and PMOS cascodes 4x wider and L=4u, RZ 1u/100u (R100), CC 45u x 23u (comp45). The notes below are the revision-B design values.} 130 -40 0 0 0.3 0.3 {}
T {Folded cascode: left branch M14/M15/M13/M3 (mirror side, node mir), right branch M11/M12/M16/M4 (node out1).} 130 -22 0 0 0.3 0.3 {}
T {Design currents (generator, vbn from an 8u/1u diode at 10 uA equivalent): tail 80 uA, PMOS sources 60 uA, NMOS sources 100 uA,} 130 -4 0 0 0.3 0.3 {}
T {stage 2 120 uA class A; Cc 0.8 pF, Rz 1.7 kOhm.  inn on M1 (mirror side), inp on M2: out rises when inp rises.} 130 14 0 0 0.3 0.3 {}
T {Bodies: wire to source where equal; b:<net> tag where the body is a rail but not the source.} 130 32 0 0 0.3 0.3 {}
T {g1_ota_main_candidate - 3.3 V folded-cascode OTA, main amplifier XOTA (comp45 + R100)} 142 -1050 0 0 0.55 0.55 {}
T {G1 guardian, chip of record g1_chip_top_1414_r2.gds 9049e87b (r2 2026-09-25; geometry XOR-identical to r1 629d303a); block map: g1_padring/reports/signoff-1414-20260924} 142 -1011 0 0 0.3 0.3 {}
T {On-chip variant: comp45 + R100, the SENSE amplifier on the chip: layout g1_sense_physical.gds 450a4906, LVS reference native-reference CDL 696b43fd} 142 -987 0 0 0.3 0.3 {}
T {Netlist-equivalent to the g1_ota_main_candidate subcircuit in reports/rz100-partial-field-evidence-20260923-r1/sense-comp45-rz100-actual-source-20260923-r1/candidate.spice sha256 aeee4d41 (source bb933fda)} 142 -963 0 0 0.3 0.3 {}
T {Drawn 2026-09-25 by the block generator; device sizes (w, l, ng, m) are on each symbol. Proof: review/schematics-readability-20260925} 142 -939 0 0 0.25 0.25 {}
C {sg13g2_pr/sg13_hv_nmos.sym} 200 -190 0 0 {name=MB2 model=sg13_hv_nmos w=8u l=1u ng=2 m=1}
C {sg13g2_pr/sg13_hv_pmos.sym} 200 -700 0 0 {name=MB3 model=sg13_hv_pmos w=16u l=1u ng=4 m=1}
C {sg13g2_pr/sg13_hv_pmos.sym} 400 -700 0 0 {name=MB5 model=sg13_hv_pmos w=16u l=1u ng=4 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 400 -190 0 0 {name=MB4 model=sg13_hv_nmos w=1.6u l=1u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 600 -190 0 0 {name=MB6 model=sg13_hv_nmos w=8u l=1u ng=2 m=1}
C {sg13g2_pr/sg13_hv_pmos.sym} 600 -700 0 0 {name=MB7 model=sg13_hv_pmos w=3.2u l=1u ng=1 m=1}
C {sg13g2_pr/sg13_hv_pmos.sym} 1300 -700 0 0 {name=MT model=sg13_hv_pmos w=128u l=1u ng=16 m=1}
C {sg13g2_pr/sg13_hv_pmos.sym} 1200 -520 0 0 {name=M1 model=sg13_hv_pmos w=384u l=2u ng=64 m=1}
C {sg13g2_pr/sg13_hv_pmos.sym} 1440 -520 0 1 {name=M2 model=sg13_hv_pmos w=384u l=2u ng=64 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1000 -190 0 0 {name=M3 model=sg13_hv_nmos w=320u l=4u ng=40 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1640 -190 0 1 {name=M4 model=sg13_hv_nmos w=320u l=4u ng=40 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1000 -330 0 0 {name=M13 model=sg13_hv_nmos w=48u l=1u ng=6 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1640 -330 0 1 {name=M16 model=sg13_hv_nmos w=48u l=1u ng=6 m=1}
C {sg13g2_pr/sg13_hv_pmos.sym} 1000 -700 0 0 {name=M14 model=sg13_hv_pmos w=384u l=4u ng=48 m=1}
C {sg13g2_pr/sg13_hv_pmos.sym} 1640 -700 0 1 {name=M11 model=sg13_hv_pmos w=384u l=4u ng=48 m=1}
C {sg13g2_pr/sg13_hv_pmos.sym} 1000 -590 0 0 {name=M15 model=sg13_hv_pmos w=384u l=4u ng=48 m=1}
C {sg13g2_pr/sg13_hv_pmos.sym} 1640 -590 0 1 {name=M12 model=sg13_hv_pmos w=384u l=4u ng=48 m=1}
C {sg13g2_pr/sg13_hv_pmos.sym} 1900 -700 0 0 {name=M20 model=sg13_hv_pmos w=192u l=1u ng=24 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 1900 -190 0 0 {name=M21 model=sg13_hv_nmos w=96u l=1u ng=12 m=1}
C {sg13g2_pr/rppd.sym} 1700 -440 3 0 {name=RZ w=1u l=100u model=rppd b=0 m=1 body=vss}
C {sg13g2_pr/cap_cmim.sym} 1800 -440 3 0 {name=CC model=cap_cmim w=45u l=23u m=1}
C {devices/ipin.sym} 1520 -520 0 1 {name=p0 lab=inp}
C {devices/ipin.sym} 1120 -520 0 0 {name=p1 lab=inn}
C {devices/ipin.sym} 100 -190 0 0 {name=p2 lab=vbn}
C {devices/opin.sym} 2060 -440 0 0 {name=p3 lab=out}
C {devices/iopin.sym} 100 -790 0 1 {name=p4 lab=vdd}
C {devices/iopin.sym} 100 -100 0 1 {name=p5 lab=vss}
C {g1_body_lab.sym} 1220 -520 0 0 {name=l1 lab=vdd}
C {g1_body_lab.sym} 1420 -520 0 0 {name=l2 lab=vdd}
C {g1_body_lab.sym} 1020 -330 0 0 {name=l3 lab=vss}
C {g1_body_lab.sym} 1620 -330 0 0 {name=l4 lab=vss}
C {g1_body_lab.sym} 1020 -590 0 0 {name=l5 lab=vdd}
C {g1_body_lab.sym} 1620 -590 0 0 {name=l6 lab=vdd}
C {devices/lab_wire.sym} 300 -650 0 0 {name=l7 lab=vbp}
C {devices/lab_pin.sym} 420 -450 0 1 {name=l8 lab=vbnc}
C {devices/lab_pin.sym} 620 -450 0 1 {name=l9 lab=vbpc}
C {devices/lab_pin.sym} 550 -190 0 0 {name=l10 lab=vbn}
C {devices/lab_pin.sym} 1250 -700 0 0 {name=l11 lab=vbp}
C {devices/lab_wire.sym} 1300 -610 0 0 {name=l12 lab=tail}
C {devices/lab_pin.sym} 1020 -645 0 1 {name=l13 lab=pc1}
C {devices/lab_pin.sym} 1020 -240 0 0 {name=l14 lab=fn}
C {devices/lab_pin.sym} 1620 -645 0 0 {name=l15 lab=pc2}
C {devices/lab_pin.sym} 1620 -240 0 1 {name=l16 lab=fp}
C {devices/lab_pin.sym} 1020 -420 0 1 {name=l17 lab=mir}
C {devices/lab_pin.sym} 1690 -700 0 1 {name=l18 lab=mir}
C {devices/lab_pin.sym} 980 -590 0 0 {name=l19 lab=vbpc}
C {devices/lab_pin.sym} 1690 -590 0 1 {name=l20 lab=vbpc}
C {devices/lab_pin.sym} 950 -330 0 0 {name=l21 lab=vbnc}
C {devices/lab_pin.sym} 1690 -330 0 1 {name=l22 lab=vbnc}
C {devices/lab_pin.sym} 950 -190 0 0 {name=l23 lab=vbn}
C {devices/lab_pin.sym} 1690 -190 0 1 {name=l24 lab=vbn}
C {devices/lab_wire.sym} 1780 -500 0 0 {name=l25 lab=out1}
C {g1_node_lab.sym} 1750 -440 0 0 {name=l26 lab=cz}
C {devices/lab_pin.sym} 1850 -190 0 0 {name=l27 lab=vbn}
N 220 -190 220 -160 {}
N 220 -700 220 -730 {}
N 420 -700 420 -730 {}
N 420 -190 420 -160 {}
N 620 -190 620 -160 {}
N 620 -700 620 -730 {}
N 1320 -700 1320 -730 {}
N 1020 -190 1020 -160 {}
N 1620 -190 1620 -160 {}
N 1020 -700 1020 -730 {}
N 1620 -700 1620 -730 {}
N 1920 -700 1920 -730 {}
N 1920 -190 1920 -160 {}
N 220 -670 220 -220 {}
N 180 -700 180 -650 {}
N 180 -650 220 -650 {}
N 220 -650 300 -650 {}
N 300 -650 300 -700 {}
N 300 -700 380 -700 {}
N 420 -670 420 -220 {}
N 380 -190 380 -250 {}
N 380 -250 420 -250 {}
N 620 -670 620 -220 {}
N 580 -700 580 -650 {}
N 580 -650 620 -650 {}
N 580 -190 550 -190 {}
N 1280 -700 1250 -700 {}
N 1320 -670 1320 -610 {}
N 1220 -610 1420 -610 {}
N 1220 -610 1220 -550 {}
N 1420 -610 1420 -550 {}
N 1220 -490 1220 -260 {}
N 1220 -260 1020 -260 {}
N 1420 -490 1420 -260 {}
N 1420 -260 1620 -260 {}
N 1020 -670 1020 -620 {}
N 1020 -560 1020 -360 {}
N 1020 -300 1020 -220 {}
N 1620 -670 1620 -620 {}
N 1620 -560 1620 -360 {}
N 1620 -300 1620 -220 {}
N 980 -700 900 -700 {}
N 900 -700 900 -460 {}
N 900 -460 1020 -460 {}
N 1660 -700 1690 -700 {}
N 1660 -590 1690 -590 {}
N 980 -330 950 -330 {}
N 1660 -330 1690 -330 {}
N 980 -190 950 -190 {}
N 1660 -190 1690 -190 {}
N 1620 -500 1800 -500 {}
N 1800 -500 1800 -700 {}
N 1800 -700 1880 -700 {}
N 1640 -500 1640 -440 {}
N 1640 -440 1670 -440 {}
N 1730 -440 1770 -440 {}
N 1920 -670 1920 -220 {}
N 1830 -440 1920 -440 {}
N 1880 -190 1850 -190 {}
N 1460 -520 1520 -520 {}
N 1120 -520 1180 -520 {}
N 100 -190 180 -190 {}
N 1920 -440 2060 -440 {}
N 220 -730 220 -790 {}
N 420 -730 420 -790 {}
N 620 -730 620 -790 {}
N 1320 -730 1320 -790 {}
N 1020 -730 1020 -790 {}
N 1620 -730 1620 -790 {}
N 1920 -730 1920 -790 {}
N 100 -790 1920 -790 {}
N 220 -160 220 -100 {}
N 420 -160 420 -100 {}
N 620 -160 620 -100 {}
N 1020 -160 1020 -100 {}
N 1620 -160 1620 -100 {}
N 1920 -160 1920 -100 {}
N 100 -100 1920 -100 {}

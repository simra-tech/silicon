v {xschem version=3.4.8RC file_version=1.3}
G {}
K {}
V {}
S {}
E {}
B 4 100 -1500 2100 -1348 {fill=false}
T {vref = buffered VREF from G1_SENSE (vref_buf). cmp_x = 1 while ISENSE/2 > VREF*(255+code)/530, i.e. shunt voltage > code x 0.1962 mV x (VREF/1.04 V).} 100 60 0 0 0.3 0.3 {}
T {Soft comparator strobes on the rising edge of cmp_clk (osc_clk/2, about 4.7 MHz with the 9.44 MHz chip clock, simulated), hard on the falling edge.} 100 78 0 0 0.3 0.3 {}
T {Chip (regenpair4 + NF4, simulated block bench): hard path trips 40-56 LSB below its code, soft within 1 LSB (sim/postlayout/README.md).} 100 96 0 0 0.3 0.3 {}
T {g1_trip - shunt-current trip: ISENSE/2 against two 8-bit VREF string DACs, soft + hard StrongARM comparators} 112 -1490 0 0 0.55 0.55 {}
T {G1 guardian, chip of record g1_chip_top_1414_r2.gds 9049e87b (r2 2026-09-25; geometry XOR-identical to r1 629d303a); block map: g1_padring/reports/signoff-1414-20260924} 112 -1451 0 0 0.3 0.3 {}
T {On-chip variant: HISTORICAL 12u/0.34u comparators, NOT on the chip (chip-of-record sheets: ../, G1_TRIP_VARIANT=chip); netlists ../../sim/netlist/*.spice} 112 -1427 0 0 0.3 0.3 {}
T {Netlist-equivalent to sim/netlist/g1_trip.spice sha256 6f265319} 112 -1403 0 0 0.3 0.3 {}
T {Drawn 2026-09-25 by the block generator; device sizes (w, l, ng, m) are on each symbol. Proof: review/schematics-readability-20260925} 112 -1379 0 0 0.25 0.25 {}
C {g1_cond.sym} 300 -650 0 0 {name=XCOND }
C {g1_dac8.sym} 700 -1000 0 0 {name=XDACS }
C {g1_dac8.sym} 700 -350 0 0 {name=XDACH }
C {sg13g2_pr/cap_cmim.sym} 870 -920 0 0 {name=CHS model=cap_cmim w=26u l=26u m=1}
C {sg13g2_pr/cap_cmim.sym} 870 -270 0 0 {name=CHH model=cap_cmim w=26u l=26u m=1}
C {g1_inv.sym} 900 -120 0 0 {name=XCLKI }
C {g1_cmp.sym} 1150 -980 0 0 {name=XCS }
C {g1_cmp.sym} 1150 -330 0 0 {name=XCH }
C {devices/ipin.sym} 100 -650 0 0 {name=p0 lab=isense}
C {devices/ipin.sym} 100 -1200 0 0 {name=p1 lab=vref}
C {devices/ipin.sym} 100 -120 0 0 {name=p2 lab=cmp_clk}
C {devices/ipin.sym} 100 -1060 0 0 {name=p3 lab=soft0}
C {devices/ipin.sym} 100 -1040 0 0 {name=p4 lab=soft1}
C {devices/ipin.sym} 100 -1020 0 0 {name=p5 lab=soft2}
C {devices/ipin.sym} 100 -1000 0 0 {name=p6 lab=soft3}
C {devices/ipin.sym} 100 -980 0 0 {name=p7 lab=soft4}
C {devices/ipin.sym} 100 -960 0 0 {name=p8 lab=soft5}
C {devices/ipin.sym} 100 -940 0 0 {name=p9 lab=soft6}
C {devices/ipin.sym} 100 -920 0 0 {name=p10 lab=soft7}
C {devices/ipin.sym} 100 -410 0 0 {name=p11 lab=hard0}
C {devices/ipin.sym} 100 -390 0 0 {name=p12 lab=hard1}
C {devices/ipin.sym} 100 -370 0 0 {name=p13 lab=hard2}
C {devices/ipin.sym} 100 -350 0 0 {name=p14 lab=hard3}
C {devices/ipin.sym} 100 -330 0 0 {name=p15 lab=hard4}
C {devices/ipin.sym} 100 -310 0 0 {name=p16 lab=hard5}
C {devices/ipin.sym} 100 -290 0 0 {name=p17 lab=hard6}
C {devices/ipin.sym} 100 -270 0 0 {name=p18 lab=hard7}
C {devices/opin.sym} 1400 -990 0 0 {name=p19 lab=cmp_soft}
C {devices/opin.sym} 1400 -340 0 0 {name=p20 lab=cmp_hard}
C {devices/iopin.sym} 100 -60 0 0 {name=p21 lab=vdd}
C {devices/iopin.sym} 100 -35 0 0 {name=p22 lab=vdda}
C {devices/iopin.sym} 100 -10 0 0 {name=p23 lab=vss}
C {devices/lab_pin.sym} 300 -580 0 1 {name=l1 lab=vss}
C {devices/lab_pin.sym} 680 -1140 0 0 {name=l2 lab=vdd}
C {devices/lab_pin.sym} 720 -1140 0 1 {name=l3 lab=vdda}
C {devices/lab_pin.sym} 700 -860 0 1 {name=l4 lab=vss}
C {devices/lab_pin.sym} 680 -490 0 0 {name=l5 lab=vdd}
C {devices/lab_pin.sym} 720 -490 0 1 {name=l6 lab=vdda}
C {devices/lab_pin.sym} 700 -210 0 1 {name=l7 lab=vss}
C {devices/lab_pin.sym} 900 -190 0 1 {name=l8 lab=vdd}
C {devices/lab_pin.sym} 900 -50 0 1 {name=l9 lab=vss}
C {devices/lab_pin.sym} 1130 -910 0 0 {name=l10 lab=cmp_clk}
C {devices/lab_pin.sym} 1150 -1050 0 1 {name=l11 lab=vdd}
C {devices/lab_pin.sym} 1170 -910 0 1 {name=l12 lab=vss}
C {devices/lab_pin.sym} 1130 -260 0 0 {name=l13 lab=cmp_clk_n}
C {devices/lab_pin.sym} 1150 -400 0 1 {name=l14 lab=vdd}
C {devices/lab_pin.sym} 1170 -260 0 1 {name=l15 lab=vss}
C {devices/lab_pin.sym} 580 -1080 0 0 {name=l16 lab=vref}
C {devices/lab_pin.sym} 580 -430 0 0 {name=l17 lab=vref}
C {devices/lab_pin.sym} 870 -870 0 0 {name=l18 lab=vss}
C {devices/lab_wire.sym} 940 -1000 0 0 {name=l19 lab=vth_soft}
C {devices/lab_pin.sym} 870 -220 0 0 {name=l20 lab=vss}
C {devices/lab_wire.sym} 940 -350 0 0 {name=l21 lab=vth_hard}
C {devices/lab_wire.sym} 600 -650 0 0 {name=l22 lab=icmp}
C {devices/lab_pin.sym} 1040 -320 0 0 {name=l23 lab=icmp}
C {devices/lab_wire.sym} 1100 -120 0 0 {name=l24 lab=cmp_clk_n}
C {devices/lab_pin.sym} 1260 -970 0 1 {name=l25 lab=cmp_soft_n}
C {devices/lab_pin.sym} 1260 -320 0 1 {name=l26 lab=cmp_hard_n}
N 300 -600 300 -580 {}
N 680 -1120 680 -1140 {}
N 720 -1120 720 -1140 {}
N 700 -880 700 -860 {}
N 680 -470 680 -490 {}
N 720 -470 720 -490 {}
N 700 -230 700 -210 {}
N 900 -170 900 -190 {}
N 900 -70 900 -50 {}
N 1130 -930 1130 -910 {}
N 1150 -1030 1150 -1050 {}
N 1170 -930 1170 -910 {}
N 1130 -280 1130 -260 {}
N 1150 -380 1150 -400 {}
N 1170 -280 1170 -260 {}
N 100 -650 210 -650 {}
N 620 -1080 580 -1080 {}
N 620 -430 580 -430 {}
N 100 -120 840 -120 {}
N 100 -1060 620 -1060 {}
N 100 -1040 620 -1040 {}
N 100 -1020 620 -1020 {}
N 100 -1000 620 -1000 {}
N 100 -980 620 -980 {}
N 100 -960 620 -960 {}
N 100 -940 620 -940 {}
N 100 -920 620 -920 {}
N 100 -410 620 -410 {}
N 100 -390 620 -390 {}
N 100 -370 620 -370 {}
N 100 -350 620 -350 {}
N 100 -330 620 -330 {}
N 100 -310 620 -310 {}
N 100 -290 620 -290 {}
N 100 -270 620 -270 {}
N 780 -1000 950 -1000 {}
N 950 -1000 950 -990 {}
N 950 -990 1080 -990 {}
N 870 -1000 870 -950 {}
N 870 -890 870 -870 {}
N 780 -350 950 -350 {}
N 950 -350 950 -340 {}
N 950 -340 1080 -340 {}
N 870 -350 870 -300 {}
N 870 -240 870 -220 {}
N 390 -650 1000 -650 {}
N 1000 -650 1000 -970 {}
N 1000 -970 1080 -970 {}
N 1080 -320 1040 -320 {}
N 960 -120 1130 -120 {}
N 1130 -120 1130 -280 {}
N 1220 -990 1400 -990 {}
N 1220 -970 1260 -970 {}
N 1220 -340 1400 -340 {}
N 1220 -320 1260 -320 {}

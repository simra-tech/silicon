v {xschem version=3.4.8RC file_version=1.3}
G {}
K {}
V {}
S {}
E {}
B 4 130 -430 330 -40 {dash=5 fill=false}
B 4 350 -430 760 -40 {dash=5 fill=false}
B 4 780 -430 1080 -40 {dash=5 fill=false}
B 4 130 -700 1732 -548 {fill=false}
T {LV inverter (vdd 1.2 V)} 138 -424 0 0 0.3 0.3 {layer=4}
T {pull-downs + cross-coupled keeper (vdda 3.3 V)} 358 -424 0 0 0.3 0.3 {layer=4}
T {HV output inverter} 788 -424 0 0 0.3 0.3 {layer=4}
T {in=1: MN1 pulls nb low, MP2 pulls n to vdda, MPO drives out high. No DC path in either state.} 140 10 0 0 0.3 0.3 {}
T {MN1/MN2 widened to 3.8 um so the LV-driven pull-down wins at vdd 1.08 V, vdda 3.63 V, mos_ss, -40 C.} 140 28 0 0 0.3 0.3 {}
T {Used 3x on the chip (t2f_en, t2f_mode, bgr_r4): static register bits, no timing requirement.} 140 46 0 0 0.3 0.3 {}
T {g1_ls_up - 1.2 V to 3.3 V level shifter (no static current)} 142 -690 0 0 0.55 0.55 {}
T {G1 guardian, chip of record g1_chip_top_1414_r2.gds 9049e87b (r2 2026-09-25; geometry XOR-identical to r1 629d303a); block map: g1_padring/reports/signoff-1414-20260924} 142 -651 0 0 0.3 0.3 {}
T {On-chip variant: baseline, 3 instances retained_g1_ls_up; layout g1_ls_up.gds 85de277c, LVS reference g1_ls_up.cdl 3465d0a6} 142 -627 0 0 0.3 0.3 {}
T {Netlist-equivalent to sim/netlist/g1_ls_up.spice sha256 5567c807 (flattened device/connectivity comparison)} 142 -603 0 0 0.3 0.3 {}
T {Drawn 2026-09-25 by the block generator; device sizes (w, l, ng, m) are on each symbol. Proof: review/schematics-readability-20260925} 142 -579 0 0 0.25 0.25 {}
C {sg13g2_pr/sg13_lv_pmos.sym} 200 -300 0 0 {name=MPI model=sg13_lv_pmos w=2u l=0.13u ng=1 m=1}
C {sg13g2_pr/sg13_lv_nmos.sym} 200 -150 0 0 {name=MNI model=sg13_lv_nmos w=1u l=0.13u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 440 -150 0 0 {name=MN1 model=sg13_hv_nmos w=3.8u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 640 -150 0 0 {name=MN2 model=sg13_hv_nmos w=3.8u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_pmos.sym} 440 -300 0 0 {name=MP1 model=sg13_hv_pmos w=0.3u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_pmos.sym} 640 -300 0 0 {name=MP2 model=sg13_hv_pmos w=0.3u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_pmos.sym} 900 -300 0 0 {name=MPO model=sg13_hv_pmos w=3.9u l=0.45u ng=1 m=1}
C {sg13g2_pr/sg13_hv_nmos.sym} 900 -150 0 0 {name=MNO model=sg13_hv_nmos w=1.9u l=0.45u ng=1 m=1}
C {devices/ipin.sym} 60 -225 0 0 {name=p0 lab=in}
C {devices/opin.sym} 1040 -225 0 0 {name=p1 lab=out}
C {devices/iopin.sym} 60 40 0 0 {name=p2 lab=vdd}
C {devices/iopin.sym} 60 70 0 0 {name=p3 lab=vdda}
C {devices/iopin.sym} 60 100 0 0 {name=p4 lab=vss}
C {devices/lab_pin.sym} 300 -225 0 1 {name=l1 lab=inb}
C {devices/lab_pin.sym} 380 -150 0 0 {name=l2 lab=in}
C {devices/lab_pin.sym} 580 -150 0 0 {name=l3 lab=inb}
C {devices/lab_pin.sym} 460 -225 0 0 {name=l4 lab=nb}
C {devices/lab_pin.sym} 660 -225 0 1 {name=l5 lab=n}
C {devices/lab_pin.sym} 840 -225 0 0 {name=l6 lab=nb}
C {devices/lab_pin.sym} 220 -390 0 0 {name=l7 lab=vdd}
C {devices/lab_pin.sym} 460 -390 0 0 {name=l8 lab=vdda}
C {devices/lab_pin.sym} 220 -70 0 0 {name=l9 lab=vss}
N 220 -300 220 -330 {}
N 220 -150 220 -120 {}
N 460 -150 460 -120 {}
N 660 -150 660 -120 {}
N 460 -300 460 -330 {}
N 660 -300 660 -330 {}
N 920 -300 920 -330 {}
N 920 -150 920 -120 {}
N 60 -225 180 -225 {}
N 180 -300 180 -150 {}
N 220 -270 220 -180 {}
N 220 -225 300 -225 {}
N 420 -150 380 -150 {}
N 620 -150 580 -150 {}
N 460 -270 460 -180 {}
N 660 -270 660 -180 {}
N 460 -245 590 -245 {}
N 590 -245 590 -300 {}
N 590 -300 620 -300 {}
N 660 -205 400 -205 {}
N 400 -205 400 -300 {}
N 400 -300 420 -300 {}
N 880 -300 880 -150 {}
N 880 -225 840 -225 {}
N 920 -270 920 -180 {}
N 920 -225 1040 -225 {}
N 220 -330 220 -390 {}
N 460 -330 460 -390 {}
N 460 -390 920 -390 {}
N 660 -330 660 -390 {}
N 920 -330 920 -390 {}
N 220 -120 220 -70 {}
N 220 -70 920 -70 {}
N 460 -120 460 -70 {}
N 660 -120 660 -70 {}
N 920 -120 920 -70 {}

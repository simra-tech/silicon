v {xschem version=3.4.8RC file_version=1.3}
G {}
K {}
V {}
S {}
E {}
B 4 40 -560 2126 -408 {fill=false}
T {two 10u/1u fingers with drain and source swapped (shared diffusion); gate on vb2} 60 -40 0 0 0.3 0.3 {}
T {bgr586_ncas - NMOS collector cascode unit} 52 -550 0 0 0.55 0.55 {}
T {G1 guardian, chip of record g1_chip_top_1414_r2.gds 9049e87b (r2 2026-09-25; geometry XOR-identical to r1 629d303a); block map: g1_padring/reports/signoff-1414-20260924} 52 -511 0 0 0.3 0.3 {}
T {On-chip variant: BGR586 = the chip BGR (cell __rz_port_text_031_g1_bgr_candidate); layout bank.gds e3ecfc62, LVS reference bank.cdl 7f8e6e8c} 52 -487 0 0 0.3 0.3 {}
T {Netlist-equivalent to the bgr586_ncas subcircuit of the drawn BGR586 netlist (flattened comparison against sim/qualification/candidates/bgr_loop24_qref4_r253p465_hv06/bgr_loop24_qref4_r253p465_hv06.spice sha256 586ffb58)} 52 -463 0 0 0.3 0.3 {}
T {Drawn 2026-09-25 by the block generator; device sizes (w, l, ng, m) are on each symbol. Proof: review/schematics-readability-20260925} 52 -439 0 0 0.25 0.25 {}
C {b586_nmos.sym} 200 -250 0 0 {name=XMA model=sg13_hv_nmos l=1u w=10u as=3.4p ad=3.4p ps=20.68u pd=20.68u rfmode=0}
C {b586_nmos.sym} 360 -250 0 0 {name=XMB model=sg13_hv_nmos l=1u w=10u as=3.4p ad=3.4p ps=20.68u pd=20.68u rfmode=0}
C {devices/iopin.sym} 220 -380 0 0 {name=p0 lab=a}
C {devices/iopin.sym} 220 -120 0 0 {name=p1 lab=b}
C {devices/ipin.sym} 80 -250 0 0 {name=p2 lab=g}
C {devices/iopin.sym} 80 -80 0 0 {name=p3 lab=vss}
C {devices/lab_pin.sym} 340 -250 0 0 {name=l1 lab=g}
C {devices/lab_pin.sym} 220 -250 0 1 {name=l2 lab=vss}
C {devices/lab_pin.sym} 380 -250 0 1 {name=l3 lab=vss}
N 220 -280 220 -320 {}
N 220 -320 440 -320 {}
N 440 -320 440 -200 {}
N 440 -200 380 -200 {}
N 380 -200 380 -220 {}
N 220 -220 220 -190 {}
N 220 -190 300 -190 {}
N 300 -190 300 -300 {}
N 300 -300 380 -300 {}
N 380 -300 380 -280 {}
N 220 -380 220 -320 {}
N 220 -190 220 -120 {}
N 80 -250 180 -250 {}

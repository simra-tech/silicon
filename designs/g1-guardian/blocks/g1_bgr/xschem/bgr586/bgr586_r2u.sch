v {xschem version=3.4.8RC file_version=1.3}
G {}
K {}
V {}
S {}
E {}
B 4 40 -560 2116 -408 {fill=false}
T {bgr586_r2u - R2 unit: rppd 1u x 53.465u} 52 -550 0 0 0.55 0.55 {}
T {G1 guardian, chip of record g1_chip_top_1414_r2.gds 9049e87b (r2 2026-09-25; geometry XOR-identical to r1 629d303a); block map: g1_padring/reports/signoff-1414-20260924} 52 -511 0 0 0.3 0.3 {}
T {On-chip variant: BGR586 = the chip BGR (cell __rz_port_text_031_g1_bgr_candidate); layout bank.gds e3ecfc62, LVS reference bank.cdl 7f8e6e8c} 52 -487 0 0 0.3 0.3 {}
T {Netlist-equivalent to the bgr586_r2u subcircuit of the drawn BGR586 netlist (flattened comparison against sim/qualification/candidates/bgr_loop24_qref4_r253p465_hv06/bgr_loop24_qref4_r253p465_hv06.spice sha256 586ffb58)} 52 -463 0 0 0.3 0.3 {}
T {Drawn 2026-09-25 by the block generator; device sizes (w, l, ng, m) are on each symbol. Proof: review/schematics-readability-20260925} 52 -439 0 0 0.25 0.25 {}
C {b586_res.sym} 200 -250 0 0 {name=XR model=rppd w=1u l=53.465u b=0 mult=1}
C {devices/iopin.sym} 200 -340 0 0 {name=p0 lab=p}
C {devices/iopin.sym} 200 -160 0 0 {name=p1 lab=m}
C {devices/iopin.sym} 320 -250 0 0 {name=p2 lab=bd}
N 200 -280 200 -340 {}
N 200 -220 200 -160 {}
N 220 -250 320 -250 {}

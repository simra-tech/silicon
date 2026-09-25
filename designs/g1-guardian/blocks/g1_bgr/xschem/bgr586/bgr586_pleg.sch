v {xschem version=3.4.8RC file_version=1.3}
G {}
K {}
V {}
S {}
E {}
B 4 40 -560 2126 -408 {fill=false}
T {mirror half pair = one 10u/4u mirror unit (MPx); cascode MCx in its own n-well, body = source} 60 -20 0 0 0.3 0.3 {}
T {bgr586_pleg - PMOS mirror unit + cascode (one PTAT-loop leg unit)} 52 -550 0 0 0.55 0.55 {}
T {G1 guardian, chip of record g1_chip_top_1414_r2.gds 9049e87b (r2 2026-09-25; geometry XOR-identical to r1 629d303a); block map: g1_padring/reports/signoff-1414-20260924} 52 -511 0 0 0.3 0.3 {}
T {On-chip variant: BGR586 = the chip BGR (cell __rz_port_text_031_g1_bgr_candidate); layout bank.gds e3ecfc62, LVS reference bank.cdl 7f8e6e8c} 52 -487 0 0 0.3 0.3 {}
T {Netlist-equivalent to the bgr586_pleg subcircuit of the drawn BGR586 netlist (flattened comparison against sim/qualification/candidates/bgr_loop24_qref4_r253p465_hv06/bgr_loop24_qref4_r253p465_hv06.spice sha256 586ffb58)} 52 -463 0 0 0.3 0.3 {}
T {Drawn 2026-09-25 by the block generator; device sizes (w, l, ng, m) are on each symbol. Proof: review/schematics-readability-20260925} 52 -439 0 0 0.25 0.25 {}
C {b586_pmos.sym} 200 -300 0 0 {name=XMA model=sg13_hv_pmos l=4u w=5u as=1.7p ad=1.7p ps=10.68u pd=10.68u rfmode=0}
C {b586_pmos.sym} 360 -300 0 0 {name=XMB model=sg13_hv_pmos l=4u w=5u as=1.7p ad=1.7p ps=10.68u pd=10.68u rfmode=0}
C {b586_pmos.sym} 200 -170 0 0 {name=XMC model=sg13_hv_pmos l=4u w=10u as=3.4p ad=3.4p ps=20.68u pd=20.68u rfmode=0}
C {devices/opin.sym} 220 -60 0 0 {name=p0 lab=out}
C {devices/iopin.sym} 500 -235 0 0 {name=p1 lab=mid}
C {devices/ipin.sym} 80 -340 0 0 {name=p2 lab=pbias}
C {devices/ipin.sym} 80 -170 0 0 {name=p3 lab=pcasc}
C {devices/iopin.sym} 80 -380 0 0 {name=p4 lab=vdd}
N 220 -300 220 -330 {}
N 380 -300 380 -330 {}
N 220 -170 220 -200 {}
N 220 -270 220 -235 {}
N 220 -235 380 -235 {}
N 380 -235 380 -270 {}
N 220 -235 220 -200 {}
N 180 -300 170 -300 {}
N 170 -300 170 -340 {}
N 170 -340 330 -340 {}
N 330 -340 330 -300 {}
N 330 -300 340 -300 {}
N 220 -330 220 -380 {}
N 220 -380 380 -380 {}
N 380 -380 380 -330 {}
N 220 -140 220 -60 {}
N 380 -235 500 -235 {}
N 80 -340 170 -340 {}
N 80 -170 180 -170 {}
N 80 -380 220 -380 {}

v {xschem version=3.4.8RC file_version=1.3}
G {}
K {}
V {}
S {}
E {}
T {G1 reference + sensor hierarchy check: g1_bgr feeding g1_t2f} 0 -200 0 0 0.4 0.4 {}
C {devices/iopin.sym} 0 -140 0 0 {name=p0 lab=vdd}
C {devices/iopin.sym} 80 -140 0 0 {name=p1 lab=vdd12}
C {devices/iopin.sym} 160 -140 0 0 {name=p2 lab=vss}
C {devices/ipin.sym} 240 -140 0 0 {name=p3 lab=r4}
C {devices/ipin.sym} 320 -140 0 0 {name=p4 lab=en}
C {devices/ipin.sym} 400 -140 0 0 {name=p5 lab=mode}
C {devices/opin.sym} 480 -140 0 0 {name=p6 lab=vref}
C {devices/opin.sym} 560 -140 0 0 {name=p7 lab=iptat}
C {devices/opin.sym} 640 -140 0 0 {name=p8 lab=fout}
C {devices/opin.sym} 720 -140 0 0 {name=p9 lab=vbe}
C {devices/opin.sym} 800 -140 0 0 {name=p10 lab=dvbe}
C {g1_bgr.sym} 200 100 0 0 {name=xbgr}
C {devices/lab_pin.sym} 120 50.0 0 0 {name=lxbgr0 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 120 70.0 0 0 {name=lxbgr1 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 120 90.0 0 0 {name=lxbgr2 sig_type=std_logic lab=r4}
C {devices/lab_pin.sym} 280 50.0 0 0 {name=loxbgr0 sig_type=std_logic lab=vref}
C {devices/lab_pin.sym} 280 70.0 0 0 {name=loxbgr1 sig_type=std_logic lab=iptat}
C {devices/lab_pin.sym} 280 90.0 0 0 {name=loxbgr2 sig_type=std_logic lab=pbias}
C {devices/lab_pin.sym} 280 110.0 0 0 {name=loxbgr3 sig_type=std_logic lab=pcasc}
C {devices/lab_pin.sym} 280 130.0 0 0 {name=loxbgr4 sig_type=std_logic lab=vbe}
C {devices/lab_pin.sym} 280 150.0 0 0 {name=loxbgr5 sig_type=std_logic lab=dvbe}
C {g1_t2f.sym} 600 100 0 0 {name=xt2f}
C {devices/lab_pin.sym} 520 30.0 0 0 {name=lxt2f0 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 520 50.0 0 0 {name=lxt2f1 sig_type=std_logic lab=vdd12}
C {devices/lab_pin.sym} 520 70.0 0 0 {name=lxt2f2 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 520 90.0 0 0 {name=lxt2f3 sig_type=std_logic lab=pbias}
C {devices/lab_pin.sym} 520 110.0 0 0 {name=lxt2f4 sig_type=std_logic lab=pcasc}
C {devices/lab_pin.sym} 520 130.0 0 0 {name=lxt2f5 sig_type=std_logic lab=vref}
C {devices/lab_pin.sym} 520 150.0 0 0 {name=lxt2f6 sig_type=std_logic lab=en}
C {devices/lab_pin.sym} 520 170.0 0 0 {name=lxt2f7 sig_type=std_logic lab=mode}
C {devices/lab_pin.sym} 680 30.0 0 0 {name=loxt2f0 sig_type=std_logic lab=fout}

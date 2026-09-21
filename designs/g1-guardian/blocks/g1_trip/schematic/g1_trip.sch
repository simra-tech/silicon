v {xschem version=3.4.8RC file_version=1.3}
G {}
K {}
V {}
S {}
E {}
T {g1_trip: conditioning + 2 x DAC + 2 x StrongARM; soft strobed on cmp_clk rising, hard on its inverse} 0 -40 0 0 0.4 0.4 {}
C {g1_cond.sym} 200 -600 0 0 {name=XCOND }
C {devices/lab_pin.sym} 140 -620 0 0 {name=l1 lab=isense}
C {devices/lab_pin.sym} 140 -600 0 0 {name=l2 lab=icmp}
C {devices/lab_pin.sym} 140 -580 0 0 {name=l3 lab=vss}
C {g1_dac8.sym} 500 -700 0 0 {name=XDACS }
C {devices/lab_pin.sym} 440 -820 0 0 {name=l4 lab=vref}
C {devices/lab_pin.sym} 440 -800 0 0 {name=l5 lab=soft0}
C {devices/lab_pin.sym} 440 -780 0 0 {name=l6 lab=soft1}
C {devices/lab_pin.sym} 440 -760 0 0 {name=l7 lab=soft2}
C {devices/lab_pin.sym} 440 -740 0 0 {name=l8 lab=soft3}
C {devices/lab_pin.sym} 440 -720 0 0 {name=l9 lab=soft4}
C {devices/lab_pin.sym} 440 -700 0 0 {name=l10 lab=soft5}
C {devices/lab_pin.sym} 440 -680 0 0 {name=l11 lab=soft6}
C {devices/lab_pin.sym} 440 -660 0 0 {name=l12 lab=soft7}
C {devices/lab_pin.sym} 440 -640 0 0 {name=l13 lab=vth_soft}
C {devices/lab_pin.sym} 440 -620 0 0 {name=l14 lab=vdd}
C {devices/lab_pin.sym} 440 -600 0 0 {name=l15 lab=vdda}
C {devices/lab_pin.sym} 440 -580 0 0 {name=l16 lab=vss}
C {g1_dac8.sym} 500 -400 0 0 {name=XDACH }
C {devices/lab_pin.sym} 440 -520 0 0 {name=l17 lab=vref}
C {devices/lab_pin.sym} 440 -500 0 0 {name=l18 lab=hard0}
C {devices/lab_pin.sym} 440 -480 0 0 {name=l19 lab=hard1}
C {devices/lab_pin.sym} 440 -460 0 0 {name=l20 lab=hard2}
C {devices/lab_pin.sym} 440 -440 0 0 {name=l21 lab=hard3}
C {devices/lab_pin.sym} 440 -420 0 0 {name=l22 lab=hard4}
C {devices/lab_pin.sym} 440 -400 0 0 {name=l23 lab=hard5}
C {devices/lab_pin.sym} 440 -380 0 0 {name=l24 lab=hard6}
C {devices/lab_pin.sym} 440 -360 0 0 {name=l25 lab=hard7}
C {devices/lab_pin.sym} 440 -340 0 0 {name=l26 lab=vth_hard}
C {devices/lab_pin.sym} 440 -320 0 0 {name=l27 lab=vdd}
C {devices/lab_pin.sym} 440 -300 0 0 {name=l28 lab=vdda}
C {devices/lab_pin.sym} 440 -280 0 0 {name=l29 lab=vss}
C {sg13g2_pr/cap_cmim.sym} 700 -700 0 0 {name=CHS model=cap_cmim w=26u l=26u m=1}
C {devices/lab_pin.sym} 700 -730 0 0 {name=l30 lab=vth_soft}
C {devices/lab_pin.sym} 700 -670 0 0 {name=l31 lab=vss}
C {sg13g2_pr/cap_cmim.sym} 700 -400 0 0 {name=CHH model=cap_cmim w=26u l=26u m=1}
C {devices/lab_pin.sym} 700 -430 0 0 {name=l32 lab=vth_hard}
C {devices/lab_pin.sym} 700 -370 0 0 {name=l33 lab=vss}
C {g1_inv.sym} 800 -200 0 0 {name=XCLKI }
C {devices/lab_pin.sym} 740 -230 0 0 {name=l34 lab=cmp_clk}
C {devices/lab_pin.sym} 740 -210 0 0 {name=l35 lab=cmp_clk_n}
C {devices/lab_pin.sym} 740 -190 0 0 {name=l36 lab=vdd}
C {devices/lab_pin.sym} 740 -170 0 0 {name=l37 lab=vss}
C {g1_cmp.sym} 1000 -700 0 0 {name=XCS }
C {devices/lab_pin.sym} 940 -760 0 0 {name=l38 lab=icmp}
C {devices/lab_pin.sym} 940 -740 0 0 {name=l39 lab=vth_soft}
C {devices/lab_pin.sym} 940 -720 0 0 {name=l40 lab=cmp_clk}
C {devices/lab_pin.sym} 940 -700 0 0 {name=l41 lab=cmp_soft}
C {devices/lab_pin.sym} 940 -680 0 0 {name=l42 lab=cmp_soft_n}
C {devices/lab_pin.sym} 940 -660 0 0 {name=l43 lab=vdd}
C {devices/lab_pin.sym} 940 -640 0 0 {name=l44 lab=vss}
C {g1_cmp.sym} 1000 -400 0 0 {name=XCH }
C {devices/lab_pin.sym} 940 -460 0 0 {name=l45 lab=icmp}
C {devices/lab_pin.sym} 940 -440 0 0 {name=l46 lab=vth_hard}
C {devices/lab_pin.sym} 940 -420 0 0 {name=l47 lab=cmp_clk_n}
C {devices/lab_pin.sym} 940 -400 0 0 {name=l48 lab=cmp_hard}
C {devices/lab_pin.sym} 940 -380 0 0 {name=l49 lab=cmp_hard_n}
C {devices/lab_pin.sym} 940 -360 0 0 {name=l50 lab=vdd}
C {devices/lab_pin.sym} 940 -340 0 0 {name=l51 lab=vss}
C {devices/ipin.sym} 1300 -800 0 0 {name=pi0 lab=isense}
C {devices/ipin.sym} 1300 -780 0 0 {name=pi1 lab=vref}
C {devices/ipin.sym} 1300 -760 0 0 {name=pi2 lab=cmp_clk}
C {devices/ipin.sym} 1300 -740 0 0 {name=pi3 lab=soft0}
C {devices/ipin.sym} 1300 -720 0 0 {name=pi4 lab=soft1}
C {devices/ipin.sym} 1300 -700 0 0 {name=pi5 lab=soft2}
C {devices/ipin.sym} 1300 -680 0 0 {name=pi6 lab=soft3}
C {devices/ipin.sym} 1300 -660 0 0 {name=pi7 lab=soft4}
C {devices/ipin.sym} 1300 -640 0 0 {name=pi8 lab=soft5}
C {devices/ipin.sym} 1300 -620 0 0 {name=pi9 lab=soft6}
C {devices/ipin.sym} 1300 -600 0 0 {name=pi10 lab=soft7}
C {devices/ipin.sym} 1300 -580 0 0 {name=pi11 lab=hard0}
C {devices/ipin.sym} 1300 -560 0 0 {name=pi12 lab=hard1}
C {devices/ipin.sym} 1300 -540 0 0 {name=pi13 lab=hard2}
C {devices/ipin.sym} 1300 -520 0 0 {name=pi14 lab=hard3}
C {devices/ipin.sym} 1300 -500 0 0 {name=pi15 lab=hard4}
C {devices/ipin.sym} 1300 -480 0 0 {name=pi16 lab=hard5}
C {devices/ipin.sym} 1300 -460 0 0 {name=pi17 lab=hard6}
C {devices/ipin.sym} 1300 -440 0 0 {name=pi18 lab=hard7}
C {devices/opin.sym} 1300 -420 0 0 {name=po0 lab=cmp_soft}
C {devices/opin.sym} 1300 -400 0 0 {name=po1 lab=cmp_hard}
C {devices/iopin.sym} 1300 -380 0 0 {name=pb0 lab=vdd}
C {devices/iopin.sym} 1300 -360 0 0 {name=pb1 lab=vdda}
C {devices/iopin.sym} 1300 -340 0 0 {name=pb2 lab=vss}
T {vref = buffered VREF from G1_SENSE. cmp_x = 1 while ISENSE/2 > VREF*(255+code)/530, i.e. shunt voltage > code*0.1962 mV*(VREF/1.04)} 200 -900 0 0 0.3 0.3 {}

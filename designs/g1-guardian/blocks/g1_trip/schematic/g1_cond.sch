v {xschem version=3.4.8RC file_version=1.3}
G {}
K {}
V {}
S {}
E {}
T {g1_cond: isense_cmp = ISENSE/2 (5+5 units of 10 k), 1 pF hold} 0 -40 0 0 0.4 0.4 {}
C {sg13g2_pr/rppd.sym} 100 -300 0 0 {name=RC0 w=2u l=76.7u model=rppd b=0 m=1}
C {devices/lab_pin.sym} 100 -330 0 0 {name=l1 lab=isense}
C {devices/lab_pin.sym} 100 -270 0 0 {name=l2 lab=c0}
C {sg13g2_pr/rppd.sym} 180 -300 0 0 {name=RC1 w=2u l=76.7u model=rppd b=0 m=1}
C {devices/lab_pin.sym} 180 -330 0 0 {name=l3 lab=c0}
C {devices/lab_pin.sym} 180 -270 0 0 {name=l4 lab=c1}
C {sg13g2_pr/rppd.sym} 260 -300 0 0 {name=RC2 w=2u l=76.7u model=rppd b=0 m=1}
C {devices/lab_pin.sym} 260 -330 0 0 {name=l5 lab=c1}
C {devices/lab_pin.sym} 260 -270 0 0 {name=l6 lab=c2}
C {sg13g2_pr/rppd.sym} 340 -300 0 0 {name=RC3 w=2u l=76.7u model=rppd b=0 m=1}
C {devices/lab_pin.sym} 340 -330 0 0 {name=l7 lab=c2}
C {devices/lab_pin.sym} 340 -270 0 0 {name=l8 lab=c3}
C {sg13g2_pr/rppd.sym} 420 -300 0 0 {name=RC4 w=2u l=76.7u model=rppd b=0 m=1}
C {devices/lab_pin.sym} 420 -330 0 0 {name=l9 lab=c3}
C {devices/lab_pin.sym} 420 -270 0 0 {name=l10 lab=icmp}
C {sg13g2_pr/rppd.sym} 500 -300 0 0 {name=RC5 w=2u l=76.7u model=rppd b=0 m=1}
C {devices/lab_pin.sym} 500 -330 0 0 {name=l11 lab=icmp}
C {devices/lab_pin.sym} 500 -270 0 0 {name=l12 lab=c5}
C {sg13g2_pr/rppd.sym} 580 -300 0 0 {name=RC6 w=2u l=76.7u model=rppd b=0 m=1}
C {devices/lab_pin.sym} 580 -330 0 0 {name=l13 lab=c5}
C {devices/lab_pin.sym} 580 -270 0 0 {name=l14 lab=c6}
C {sg13g2_pr/rppd.sym} 660 -300 0 0 {name=RC7 w=2u l=76.7u model=rppd b=0 m=1}
C {devices/lab_pin.sym} 660 -330 0 0 {name=l15 lab=c6}
C {devices/lab_pin.sym} 660 -270 0 0 {name=l16 lab=c7}
C {sg13g2_pr/rppd.sym} 740 -300 0 0 {name=RC8 w=2u l=76.7u model=rppd b=0 m=1}
C {devices/lab_pin.sym} 740 -330 0 0 {name=l17 lab=c7}
C {devices/lab_pin.sym} 740 -270 0 0 {name=l18 lab=c8}
C {sg13g2_pr/rppd.sym} 820 -300 0 0 {name=RC9 w=2u l=76.7u model=rppd b=0 m=1}
C {devices/lab_pin.sym} 820 -330 0 0 {name=l19 lab=c8}
C {devices/lab_pin.sym} 820 -270 0 0 {name=l20 lab=vss}
C {sg13g2_pr/cap_cmim.sym} 1000 -300 0 0 {name=CH model=cap_cmim w=26u l=26u m=1}
C {devices/lab_pin.sym} 1000 -330 0 0 {name=l21 lab=icmp}
C {devices/lab_pin.sym} 1000 -270 0 0 {name=l22 lab=vss}
C {devices/ipin.sym} 1200 -300 0 0 {name=pi0 lab=isense}
C {devices/opin.sym} 1200 -280 0 0 {name=po0 lab=icmp}
C {devices/iopin.sym} 1200 -260 0 0 {name=pb0 lab=vss}

v {xschem version=3.4.8RC file_version=1.2}
G {}
K {}
V {}
S {}
E {}

* Geometry note. The panel renders this into 644 x 588 px and fits to the
* tighter axis. The previous drawing was 1120 x 640 units, aspect 1.75, so it
* fitted to width and left the bottom third of the panel empty while the top
* was crammed. This one is 1110 x 900, aspect 1.23, close to the panel's 1.10.
* Box text is left-inset 18 units and every line is short enough to end well
* inside the box, so a net label sitting in a 120-unit gap cannot reach it.

T {P1 p-Bit - Top-Level Block Diagram} -555 -520 0 0 0.40 0.40 {}
T {0.32 mm2 of a 0.2-0.5 budget - probe-pad only - IHP SG13G2 SiGe BiCMOS} -555 -460 0 0 0.20 0.20 {}

* ---- signal chain -------------------------------------------------------
B 4 -555 -380 -265 -140 {fill=false color=5}
T {P1_NOISE_GEN} -537 -345 0 0 0.28 0.28 {}
T {SiGe HBT npn13G2} -537 -295 0 0 0.20 0.20 {}
T {forward shot noise} -537 -255 0 0 0.20 0.20 {}
T {0.03 mm2} -537 -185 0 0 0.20 0.20 {}

B 4 -145 -380 145 -140 {fill=false color=5}
T {P1_NOISE_AMP} -127 -345 0 0 0.28 0.28 {}
T {SiGe HBT CML} -127 -295 0 0 0.20 0.20 {}
T {broadband preamp} -127 -255 0 0 0.20 0.20 {}
T {0.05 mm2} -127 -185 0 0 0.20 0.20 {}

B 4 265 -380 555 -140 {fill=false color=5}
T {P1_COMPARATOR} 283 -345 0 0 0.28 0.28 {}
T {HBT CML + CMOS} 283 -295 0 0 0.20 0.20 {}
T {clocked latch} 283 -255 0 0 0.20 0.20 {}
T {0.04 mm2} 283 -185 0 0 0.20 0.20 {}

* ---- support row --------------------------------------------------------
B 4 -555 140 -265 380 {fill=false color=6}
T {P1_NOISE_TEST} -537 175 0 0 0.28 0.28 {}
T {replica HBT source} -537 225 0 0 0.20 0.20 {}
T {50 ohm GSG monitor} -537 265 0 0 0.20 0.20 {}
T {0.05 mm2} -537 335 0 0 0.20 0.20 {}

B 4 -145 140 555 380 {fill=false color=7}
T {P1_PAD_ARRAY} -127 175 0 0 0.28 0.28 {}
T {GSG RF + DC bias pads, 100 um pitch} -127 225 0 0 0.20 0.20 {}
T {probe-pad only, no wire-bonds} -127 265 0 0 0.20 0.20 {}
T {0.15 mm2} -127 335 0 0 0.20 0.20 {}

* ---- interconnect. Labels sit above each wire, centred in the clear gap. --
N -265 -260 -145 -260 {lab=RAW_NOISE}
T {RAW_NOISE} -257 -290 0 0 0.20 0.20 {}

N 145 -260 265 -260 {lab=AMP_OUT}
T {AMP_OUT} 164 -290 0 0 0.20 0.20 {}

N -410 -140 -410 140 {lab=RAW_NOISE_MON}
T {RAW_NOISE_MON} -395 10 0 0 0.20 0.20 {}

N 430 -140 430 140 {lab=PBIT_OUT}
T {PBIT_OUT} 450 10 0 0 0.20 0.20 {}

N 300 140 300 -140 {lab=CLK_IN}
T {CLK_IN} 190 10 0 0 0.20 0.20 {}

v {xschem version=3.4.8RC file_version=1.3
* bandgap_top -- top-level integration wiring bandgap_core + bandgap_amp +
* bandgap_startup together (issue #58), closing the loop for the first
* time. Matches gf180-bandgap's and sky130-bandgap's own bandgap_top.sch
* pattern (spec/porting-plan.md Sec 5's cross-reference): instantiate the
* three blocks and wire them at the nodes they actually share.
*
*   core.fb    <- amp.out       (amp servos the shared mirror-gate node)
*   core.sns1  -> amp.in_n      (inverting input -- see bandgap_amp.sch's
*                                 header "polarity" section for why sns1,
*                                 not sns2, is inverting)
*   core.sns2  -> amp.in_p      (non-inverting input)
*   startup.sns1 <- core.sns1   (startup senses the same node the amp's
*                                 in_n does, to know when the core is
*                                 running)
*   startup.fb -> core.fb       (shared with amp.out -- the startup kick
*                                 pulls this node low during the degenerate
*                                 zero-current state; bandgap_amp.sch's own
*                                 header explains why the amp's own MTAIL
*                                 tail-bias device collapses along with the
*                                 core in that state, so the startup kick is
*                                 load-bearing for both blocks, not just the
*                                 core)
*
* Exposed pins: vdd, vss, vref -- matching both sibling repos' minimal
* top-level pin set. Internal nodes (fb, sns1, sns2, and bandgap_amp's own
* internal tail/d1/d2/pn nodes) are deliberately NOT exposed here; a future
* testbench that needs to probe them directly does so by wiring the three
* sub-blocks' netlists in verbatim, the same way sim/startup-core-handover
* already does for core+startup (see sim/README.md and this issue's own
* closed-loop testbench, sim/closed-loop-startup/).
*
* No trim network, no cascode/PSRR output stage -- both explicitly out of
* this issue's scope (see design/README.md).
}
G {}
K {}
V {}
S {}
E {}
C {bandgap_core.sym} 0 0 0 0 {name=x1}
N -40 48 -60 48 {}
C {lab_pin.sym} -60 48 0 0 {name=l1 lab=vdd}
N -40 16 -60 16 {}
C {lab_pin.sym} -60 16 0 0 {name=l2 lab=sns1}
N -40 -16 -60 -16 {}
C {lab_pin.sym} -60 -16 0 0 {name=l3 lab=sns2}
N -40 -48 -60 -48 {}
C {lab_pin.sym} -60 -48 0 0 {name=l4 lab=vss}
N 40 48 60 48 {}
C {lab_pin.sym} 60 48 0 0 {name=l5 lab=fb}
N 40 -16 60 -16 {}
C {lab_pin.sym} 60 -16 0 0 {name=l6 lab=vref}
C {bandgap_amp.sym} 600 250 0 0 {name=x2}
N 570 274 550 274 {}
C {lab_pin.sym} 550 274 0 0 {name=l7 lab=sns2}
N 570 246 550 246 {}
C {lab_pin.sym} 550 246 0 0 {name=l8 lab=sns1}
N 570 220 550 220 {}
C {lab_pin.sym} 550 220 0 0 {name=l9 lab=vss}
N 630 264 650 264 {}
C {lab_pin.sym} 650 264 0 0 {name=l10 lab=fb}
N 630 220 650 220 {}
C {lab_pin.sym} 650 220 0 0 {name=l11 lab=vdd}
C {bandgap_startup.sym} 0 -300 0 0 {name=x3}
N -30 -276 -50 -276 {}
C {lab_pin.sym} -50 -276 0 0 {name=l12 lab=vdd}
N -30 -326 -50 -326 {}
C {lab_pin.sym} -50 -326 0 0 {name=l13 lab=vss}
N -30 -300 -50 -300 {}
C {lab_pin.sym} -50 -300 0 0 {name=l14 lab=sns1}
N 30 -300 50 -300 {}
C {lab_pin.sym} 50 -300 0 0 {name=l15 lab=fb}
C {iopin.sym} -250 48 0 0 {name=p1 lab=vdd}
C {iopin.sym} -250 -48 0 0 {name=p2 lab=vss}
C {iopin.sym} 250 -16 0 0 {name=p3 lab=vref}

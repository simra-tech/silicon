v {xschem version=3.4.8RC file_version=1.3
* bandgap_amp -- error amplifier closing the loop for bandgap_core.sch
* (issue #58), per DR-0001 (spec/decision-records/0001-bipolar-device-selection.md).
*
* Servos bandgap_core's mirror gate "fb" to force sns1 = sns2, the same
* job gf180-bandgap's and sky130-bandgap's own bandgap_amp.sch/error_amp.sch
* do for their own cores (spec/porting-plan.md Sec 5) -- but neither
* sibling's *device-level* topology transfers unmodified: this core's
* sense nodes sit at a low, near-vss common mode (~0.7-0.8V, one VBE),
* exactly the situation sky130-bandgap's ORIGINAL placeholder amplifier
* (that repo's issue #8, commit e599e30) was built for -- "VINP/VINN are
* the core's sense nodes (~0.73 V = one VEB, which forces a PMOS input
* pair)". This schematic mirrors THAT topology choice (a PMOS input pair,
* folded through an NMOS-then-PMOS mirror chain so the output can swing
* close to vdd), not gf180's NMOS-input placeholder (gf180's core's sense
* nodes sit near vdd, the opposite polarity -- not this core's situation).
*
* -------------------------------------------------------------- polarity
* bandgap_core.sch's three legs (M1/M2/M3, gated together by "fb") carry
* equal current I(fb), monotonically DECREASING in fb (raising fb lowers
* each sg13_hv_pmos leg's |Vgs| overdrive). sns1 = VBE(Q1,I) directly;
* sns2 = VBE(Q2,I) + I*R2 (Q2 is the Nx=8 leg, so VBE(Q2,I) < VBE(Q1,I) by
* about VT*ln(8), nearly current-independent). So:
*   e := sns2 - sns1 ~= I*R2 - VT*ln(8)
* is monotonically INCREASING in I (de/dI ~= R2, the dominant term), hence
* monotonically DECREASING in fb (de/dfb = de/dI * dI/dfb < 0, since
* dI/dfb < 0). For negative feedback, this amplifier's output must
* INCREASE with e = sns2 - sns1 (so that e-up -> fb-up -> I-down -> e-down,
* a restoring loop): sns2 is therefore this amplifier's non-inverting
* input (in_p), sns1 the inverting input (in_n). Getting this backwards
* would make the loop positive feedback (rail to a supply rather than
* settle) -- this is the single most safety-critical wiring decision in
* this schematic and in design/bandgap_top.sch's instantiation of it.
*
* ---------------------------------------------------------------- topology
* Single-stage, current-mirror-folded OTA, all real sg13_hv_pmos/
* sg13_hv_nmos devices (3.3V-rated per DR-0002), no bipolar device at all
* -- so DR-0001's Consequences-section BVCEO/BVEBO constraint on any
* bipolar device does not bind here by construction, the same "noted
* explicitly, not silently true" discipline bandgap_startup.sch's header
* already applies to its own all-MOS design. Every device here operates
* well inside sg13_hv_pmos/sg13_hv_nmos's 3.3V Vgs/Vds rating (DR-0002):
* Vgs never exceeds about one Vsg/Vgs overdrive plus the ~0.7-0.8V input
* common mode, far below the rail.
*
*   MTAIL   sg13_hv_pmos, gate=out (this amplifier's OWN output/fb node),
*           source=vdd, drain=tail. Matched 1:1 (w=10u l=1u, identical
*           geometry) to bandgap_core.sch's M1/M2/M3, so this amplifier's
*           own tail current tracks the core's own per-branch current I
*           exactly -- the same self-consistency gf180-bandgap's and
*           sky130-bandgap's amps get from an explicit tail_bias/ITAIL pin
*           fed by an internal core bias leg. THIS core (design/bandgap_core.sch)
*           has no such internal bias-mirror leg to export as a pin (its
*           three legs are all direct DUT branches, not one DUT + one bias
*           replica) -- so rather than add a pin/leg to the already-landed
*           core schematic (out of this issue's scope), MTAIL senses "fb"
*           directly, which is available for exactly this purpose: gate
*           current is zero, so tapping fb here adds no DC load to
*           whatever drives it, the same non-loading tap bandgap_core's
*           own M1/M2/M3 gates already are. This also reproduces, on
*           purpose, the same startup dependency gf180's amp header flags:
*           "if the core sits in its zero-current degenerate state ...
*           this amp goes to zero current right along with it" -- an
*           idealized VCVS/behavioral amp would mask that degenerate
*           state; a real device here does not, which is exactly why
*           design/bandgap_startup.sch's kick is load-bearing for this
*           amplifier too, not just for the core (see "bias order" below).
*   MP1/MP2 sg13_hv_pmos input pair (w=20u l=1u, wider than MTAIL so the
*           tail current splits with headroom), sources tied to "tail".
*           MP1 gate = in_p (non-inverting, wired to sns2 at the top
*           level), MP2 gate = in_n (inverting, wired to sns1) -- see
*           "polarity" above. Bulk tied to vdd (standard PMOS n-well tie),
*           not to "tail", so the source-bulk junction (bulk=vdd,
*           source=tail <= vdd) stays reverse-biased by construction.
*   MN1/MN2 sg13_hv_nmos diode-connected loads on each input-pair drain
*           (d1, d2 respectively) -- w=10u l=1u, matched to each other so
*           d1/d2 sit at the same voltage and the input pair sees no
*           systematic Vds imbalance (the same symmetry argument
*           sky130-bandgap's original placeholder amp header makes).
*   MN3     sg13_hv_nmos, gate=d1 (mirrors MN1 1:1, w=10u l=1u), drain=out.
*           Sinks I(MP1) out of the output node directly.
*   MN4/MP3/MP4
*           sg13_hv_nmos MN4 (gate=d2, mirrors MN2 1:1) pulls down an
*           internal "pn" node; sg13_hv_pmos MP3 (diode-connected on "pn",
*           source=vdd) supplies that pulled current from vdd; sg13_hv_pmos
*           MP4 (gate=pn, mirrors MP3 1:1, source=vdd) sources that same
*           current INTO the output node. Net effect: out = I(MP2) sourced
*           via MP4 minus I(MP1) sunk via MN3 -- the same NMOS-then-PMOS
*           fold sky130-bandgap's and gf180-bandgap's own placeholder amps
*           use, and for the identical reason: a plain 5-transistor OTA's
*           output is also an input-pair drain, bounded well below vdd by
*           the tail node's own headroom, and cannot swing close enough to
*           vdd to fully turn OFF bandgap_core's PMOS mirror legs (M1-M3
*           need "fb" near vdd to shut off). Folding the output onto a
*           PMOS-sourced node bounded only by an NMOS to vss and a PMOS to
*           vdd removes that ceiling.
*
* All mirror pairs here are matched 1:1 (MTAIL vs bandgap_core's M1-M3;
* MN3 vs MN1; MN4 vs MN2; MP4 vs MP3) -- the simplest, least sizing-error-
* prone first pass, matching bandgap_core.sch's and bandgap_startup.sch's
* own "provisional, not yet simulation-grounded" sizing discipline. No
* explicit compensation capacitor is added in this first pass (loop
* stability is not yet measured -- see design/README.md's "what has and
* has not been verified" note for this issue); a future revision may need
* one, the same way gf180-bandgap's amp eventually grew dominant-pole
* compensation (that repo's issue #56) once its own loop was measured.
*
* --------------------------------------------------------------- bias order
* Like gf180-bandgap's own placeholder amp (that repo's issue #8 header),
* this amplifier has no independent bias reference anywhere: MTAIL's own
* gate is this amplifier's output, which collapses toward vdd right along
* with bandgap_core's own degenerate (zero-current) state, so BOTH the
* core and this amplifier come up from the same startup kick
* (design/bandgap_startup.sch's MKFB pulling "fb" low) rather than one
* bootstrapping the other independently. This is deliberate, not an
* oversight -- see design/bandgap_top.sch for how the three blocks share
* that one "fb" node.
*
* Pins: vdd, vss, in_p, in_n, out
}
G {}
K {}
V {}
S {}
E {}
C {sg13g2_pr/sg13_hv_pmos.sym} -600 0 0 0 {name=MTAIL model=sg13_hv_pmos w=10u l=1u ng=1 m=1}
N -580 -30 -560 -50 {}
C {lab_pin.sym} -560 -50 0 0 {name=l1 lab=vdd}
N -620 0 -640 0 {}
C {lab_pin.sym} -640 0 0 0 {name=l2 lab=out}
N -580 0 -560 0 {}
C {lab_pin.sym} -560 0 0 0 {name=l3 lab=vdd}
N -580 30 -560 50 {}
C {lab_pin.sym} -560 50 0 0 {name=l4 lab=tail}
C {sg13g2_pr/sg13_hv_pmos.sym} 0 0 0 0 {name=MP1 model=sg13_hv_pmos w=20u l=1u ng=1 m=1}
N 20 -30 40 -50 {}
C {lab_pin.sym} 40 -50 0 0 {name=l5 lab=tail}
N -20 0 -40 0 {}
C {lab_pin.sym} -40 0 0 0 {name=l6 lab=in_p}
N 20 0 40 0 {}
C {lab_pin.sym} 40 0 0 0 {name=l7 lab=vdd}
N 20 30 40 50 {}
C {lab_pin.sym} 40 50 0 0 {name=l8 lab=d1}
C {sg13g2_pr/sg13_hv_pmos.sym} 400 0 0 0 {name=MP2 model=sg13_hv_pmos w=20u l=1u ng=1 m=1}
N 420 -30 440 -50 {}
C {lab_pin.sym} 440 -50 0 0 {name=l9 lab=tail}
N 380 0 360 0 {}
C {lab_pin.sym} 360 0 0 0 {name=l10 lab=in_n}
N 420 0 440 0 {}
C {lab_pin.sym} 440 0 0 0 {name=l11 lab=vdd}
N 420 30 440 50 {}
C {lab_pin.sym} 440 50 0 0 {name=l12 lab=d2}
C {sg13g2_pr/sg13_hv_pmos.sym} 1200 0 0 0 {name=MP3 model=sg13_hv_pmos w=10u l=1u ng=1 m=1}
N 1220 -30 1240 -50 {}
C {lab_pin.sym} 1240 -50 0 0 {name=l13 lab=vdd}
N 1180 0 1160 0 {}
C {lab_pin.sym} 1160 0 0 0 {name=l14 lab=pn}
N 1220 0 1240 0 {}
C {lab_pin.sym} 1240 0 0 0 {name=l15 lab=vdd}
N 1220 30 1240 50 {}
C {lab_pin.sym} 1240 50 0 0 {name=l16 lab=pn}
C {sg13g2_pr/sg13_hv_pmos.sym} 1600 0 0 0 {name=MP4 model=sg13_hv_pmos w=10u l=1u ng=1 m=1}
N 1620 -30 1640 -50 {}
C {lab_pin.sym} 1640 -50 0 0 {name=l17 lab=vdd}
N 1580 0 1560 0 {}
C {lab_pin.sym} 1560 0 0 0 {name=l18 lab=pn}
N 1620 0 1640 0 {}
C {lab_pin.sym} 1640 0 0 0 {name=l19 lab=vdd}
N 1620 30 1640 50 {}
C {lab_pin.sym} 1640 50 0 0 {name=l20 lab=out}
C {sg13g2_pr/sg13_hv_nmos.sym} 0 400 0 0 {name=MN1 model=sg13_hv_nmos w=10u l=1u ng=1 m=1}
N 20 370 40 350 {}
C {lab_pin.sym} 40 350 0 0 {name=l21 lab=d1}
N -20 400 -40 400 {}
C {lab_pin.sym} -40 400 0 0 {name=l22 lab=d1}
N 20 400 40 400 {}
C {lab_pin.sym} 40 400 0 0 {name=l23 lab=vss}
N 20 430 40 450 {}
C {lab_pin.sym} 40 450 0 0 {name=l24 lab=vss}
C {sg13g2_pr/sg13_hv_nmos.sym} 400 400 0 0 {name=MN2 model=sg13_hv_nmos w=10u l=1u ng=1 m=1}
N 420 370 440 350 {}
C {lab_pin.sym} 440 350 0 0 {name=l25 lab=d2}
N 380 400 360 400 {}
C {lab_pin.sym} 360 400 0 0 {name=l26 lab=d2}
N 420 400 440 400 {}
C {lab_pin.sym} 440 400 0 0 {name=l27 lab=vss}
N 420 430 440 450 {}
C {lab_pin.sym} 440 450 0 0 {name=l28 lab=vss}
C {sg13g2_pr/sg13_hv_nmos.sym} 800 400 0 0 {name=MN3 model=sg13_hv_nmos w=10u l=1u ng=1 m=1}
N 820 370 840 350 {}
C {lab_pin.sym} 840 350 0 0 {name=l29 lab=out}
N 780 400 760 400 {}
C {lab_pin.sym} 760 400 0 0 {name=l30 lab=d1}
N 820 400 840 400 {}
C {lab_pin.sym} 840 400 0 0 {name=l31 lab=vss}
N 820 430 840 450 {}
C {lab_pin.sym} 840 450 0 0 {name=l32 lab=vss}
C {sg13g2_pr/sg13_hv_nmos.sym} 1200 400 0 0 {name=MN4 model=sg13_hv_nmos w=10u l=1u ng=1 m=1}
N 1220 370 1240 350 {}
C {lab_pin.sym} 1240 350 0 0 {name=l33 lab=pn}
N 1180 400 1160 400 {}
C {lab_pin.sym} 1160 400 0 0 {name=l34 lab=d2}
N 1220 400 1240 400 {}
C {lab_pin.sym} 1240 400 0 0 {name=l35 lab=vss}
N 1220 430 1240 450 {}
C {lab_pin.sym} 1240 450 0 0 {name=l36 lab=vss}
C {iopin.sym} -900 0 0 0 {name=p1 lab=vdd}
C {iopin.sym} -900 700 0 0 {name=p2 lab=vss}
C {iopin.sym} -900 -100 0 0 {name=p3 lab=in_p}
C {iopin.sym} -900 100 0 0 {name=p4 lab=in_n}
C {iopin.sym} 1900 50 0 0 {name=p5 lab=out}

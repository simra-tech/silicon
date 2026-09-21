v {xschem version=3.4.8RC file_version=1.3
* bandgap_core -- grounded-emitter npn13G2 (SiGe:C HBT) diode-referenced core
* (issue #9), per DR-0001 (spec/decision-records/0001-bipolar-device-selection.md)
* and DR-0002 (spec/decision-records/0002-supply-voltage-scope.md).
*
* THIS IS NOT A RE-PARAMETERIZED COPY of gf180-bandgap's or sky130-bandgap's
* grounded-collector PNP-pair Brokaw/Kuijk core (spec/porting-plan.md Sec 5).
* npn13G2 is an NPN device, so the diode-connected sensing devices here sit
* base-tied-to-collector, EMITTER grounded -- the mirror pushes current into
* each device's collector/base node from above, the mirror image of the
* PNP siblings' base/collector-grounded, emitter-driven-from-above core.
*
* Three matched sg13_hv_pmos mirror legs (M1, M2, M3; DR-0002: 3.3V HV
* flavor), gate-driven by an external error amplifier via "fb" (the
* amplifier itself, and the top-level integration wiring it to this core,
* are follow-on scope -- see design/README.md and the issue this PR closes
* for the explicit follow-up-issue note; gf180-bandgap and sky130-bandgap
* both decomposed core/amp/startup/top across separate issues too, this
* repo follows the same split rather than a single all-in-one schematic).
*
*   Q1 (npn13G2, Nx=1)  -- branch 1, unit device, sensed directly at sns1
*                          (M1 drain, no series resistor).
*   Q2 (npn13G2, Nx=8)  -- branch 2, 8x drawn (native Nx emitter-multiplicity
*                          parameter -- porting-plan.md Sec 2/Sec 5 notes
*                          this is closer to gf180's directly-sizable device
*                          than sky130's fixed-geometry PNP array), fed
*                          through PTAT resistor R2 from the M2 mirror node
*                          "sns2" down to Q2's collector/base node.
*   Q3 (npn13G2, Nx=1)  -- output branch, fed through summing resistor R1
*                          from the M3 mirror node (== "vref" directly, no
*                          cascode in this first pass -- see below) down to
*                          Q3's collector/base node.
*
* With a future external amplifier forcing sns1 = sns2 (this core exposes
* both as ports for that loop -- amplifier is out of this issue's scope),
* the amplifier's servo action drops the PTAT delta-VBE(Q1,Q2) entirely
* across R2 (Q1 has no series resistor), giving a PTAT branch current
*   I = dVBE(Q1,Q2) / R2 = VT*ln(Nx2/Nx1)/R2 = VT*ln(8)/R2
* mirrored (M1=M2=M3, same W/L) into the output branch, where
*   vref = VBE(Q3) + I*R1
* is the classic Brokaw CTAT+PTAT sum -- VBE(Q3) is this HBT's CTAT term
* (diode-connected, ~0.7-0.8V, falling with temperature), I*R1 is the PTAT
* term, sized (provisionally -- see below) to null the first-order TC the
* same way both sibling cores do, adapted to npn13G2's real device numbers
* per spec/porting-plan.md Sec 6 (IC07 anchor: ~3.8uA typ at VBE=0.7V,
* Nx=1, used below to pick the branch design current).
*
* BVCEO/BVEBO SAFETY (DR-0001 Consequences; porting-plan.md Sec 3): Q1-Q3
* are diode-connected (Vbc=0 by construction) with Vce = Vbe ~= 0.7-0.8V at
* the design current -- far below npn13G2's BVCEO target/min of 1.6V/1.4V,
* and never reverse-biased (Veb ~= 0, forward operation only), so no
* breakdown margin issue exists for these three core devices under any
* PVT corner this schematic's topology can reach. No cascode is used on
* the M1-M3 mirror in this first pass (unlike gf180's core, which cascodes
* its PMOS mirror purely for PSRR -- see spec/porting-plan.md Sec 5 on why
* that framing does not transfer as a "PSRR nicety" here): the mirror
* devices themselves are sg13_hv_pmos (3.3V-rated), and their Vds here
* (VDD minus a ~0.7-0.8V branch node) stays well inside that rating without
* one. A future cascode/output-stage revision, if added for PSRR, would
* still need to keep any BIPOLAR device it adds within the same BVCEO/BVEBO
* ceiling -- this core's own three devices already satisfy that constraint
* by construction (diode-connected, low Vce), so the constraint currently
* binds on nothing in this schematic; flagged here per the issue's
* "traceable design intent" ask, not because anything here is at risk.
*
* SIZING (PROVISIONAL, matching the sibling repos' own first-pass sizing
* practice, e.g. gf180 DR-0001-era bandgap_core.sch -- not yet simulation-
* verified; #10 (PVT testbenches) is the issue that grounds these numbers
* in actual sim/ evidence):
*   Design current I ~= 5uA/branch (anchored near npn13G2's own IC07
*   process-spec target current, 3.8uA typ/2.6-5.2uA range at VBE=0.7V,
*   Nx=1 -- spec/porting-plan.md Sec 6), giving:
*     R2 = VT*ln(8)/I ~= 25.85mV*2.079/5uA ~= 10.75 kOhm
*         -> rppd, w=2um (>=2um per the process spec's precision-resistor
*            recommendation, spec/porting-plan.md Sec 2), l ~= 82.7um
*            (solved from rppd.sym's own R(w,l) formula, b=0 bends)
*     R1 was originally sized for a provisional vref ~= 1.2V target with
*         VBE(Q3) ~= 0.75V assumed (not yet simulated): R1 = (1.2 - 0.75)/5uA
*         = 90 kOhm -> rppd, w=2um, l ~= 694.5um (same formula). #86's
*         closed-loop PVT sweep grounded that provisional value in real
*         sim/ evidence and found its measured TC (349-376 ppm/C across all
*         15 process corners, sim/closed-loop-vref-pvt/records/
*         20260826-103022-014570b-tc.csv) ~7-8x over the draft
*         spec/porting-plan.md Sec 6 TC row (< 50 ppm/C) -- the R1/R2
*         ratio's implied PTAT gain (R1/R2*ln(8) ~= 17.5) undercancels
*         VBE(Q3)'s CTAT slope for npn13G2 at this branch current, which
*         needs measurably less PTAT gain than the ~17-20x rule-of-thumb
*         silicon-BJT literature value to null first-order TC.
*     R1 RETUNED (issue #134): a resistor-ratio-only retune, R2 unchanged --
*         l = 511um (R1/R2*ln(8) ~= 12.85, down from ~17.5), found by
*         sweeping R1 in sim (design current I is set by R2 alone, so this
*         retune does not change branch current, only the vref DC level and
*         its TC) and selecting the length nearest the sim-measured
*         minimum-|TC| crossing at the typ/3.30V corner, then confirmed
*         across all 15 process corners x 3 supplies via both the endpoint
*         method (matching sim/closed-loop-vref-pvt's own 3-temperature-point
*         convention) and a finer 8-temperature-point box-method scan (needed
*         because vref(T) is no longer monotonic this close to the
*         first-order-cancellation point -- see
*         measurements/2026-08-tc-retune/README.md for the full derivation,
*         per-corner table and the vref(T) curvature analysis). Worst-case
*         measured box TC across the grid is ~19 ppm/C (wcs corner) --
*         inside the draft < 50 ppm/C row. This retune trades away the
*         (also-unverified, separately tracked -- issue #133) ~1.2V Output
*         reference target: vref moves to ~1.045V at this R1/R2 ratio. R1's
*         length change also desyncs layout/bandgap_core's existing GDS/PEX
*         evidence (sized for l=694.5um) -- re-layout is tracked as a
*         separate follow-on, not done in this schematic-level fix.
*   Mirror M1=M2=M3: sg13_hv_pmos, W=10u/L=1u (W/L=10, matched across all
*   three legs by construction -- mirror accuracy depends on this match,
*   not on the absolute W/L chosen here).
* R2 is unchanged; R1 is simulation-grounded as of issue #134 (see above).
* Earlier note ("#10 will re-derive them") predates #86's PVT-sweep grounding
* and #134's retune -- kept for history, superseded by the above.
*
* UNIT-DEVICE DECOMPOSITION (issue #149, T1 tracker #4 item 4 cause d):
* M1/M2/M3 previously each drew as ONE `sg13_hv_pmos w=10u l=1u` instance,
* identical at the recognised-device level -- with bipolar (Q1-Q3) and
* resistor recognition both blind to the mirrors' true downstream
* differentiation at the time this was first found (PR #27), the sg13g2
* `klt lvs` deck saw three structurally-indistinguishable pfet nodes: a
* genuine graph automorphism (`layout/README.md` "Permanent blockers" #2).
* Each leg's *total* mirror width stays exactly W/L=10u/1u (the ratio the
* mirror's accuracy depends on, per the note above -- unchanged), but is
* now decomposed into a per-leg-distinct COUNT of parallel unit fingers,
* wired together at all 4 terminals so the electrical node is unchanged --
* M1: 1x, M2: 2x, M3: 3x (the *minimum* pairwise-distinct device-count
* set, {1,2,3}, not {1,2,4}: see "NOT electrically exact" below for why a
* smaller device-count spread was deliberately chosen over the deeper
* 4-way split this issue's own first draft used):
*   M1: 1x unit,                  w=10u l=1u        (unchanged)
*   M2: 2x units (M2A/M2B),       w=9u+1u l=1u       (9u + 1u = 10u)
*   M3: 3x units (M3A/M3B/M3C),   w=8u+1u+1u l=1u    (8u + 1u + 1u = 10u)
* Each leg keeps one dominant near-original-width finger plus the minimum
* number of small "trim" fingers needed to reach its target device count
* -- chosen (over an equal-width split, e.g. 3x3.33u for M3) because it
* measurably reduces the real compact-model mismatch this decomposition
* introduces (see below): a dominant finger close to M1's own 10u behaves
* closest to the pre-#149 device, so only the trim finger(s)' own smaller
* contribution is exposed to the compact model's width-dependent terms.
* This makes the M1/M2/M3 branch subgraphs structurally distinct (1 vs 2
* vs 3 same-class devices hanging off each mirror node) independent of
* whether the deck's canonicaliser weighs device parameters at all --
* Option 1 from issue #149 ("differentiated geometry with preserved
* ratios ... via unit-device decomposition").
*
* NOT electrically exact -- quantified, not assumed. Unlike an idealised
* SPICE parallel-device sum, IHP-SG13G2's real `sg13_hv_pmos` PSP103
* compact model is NOT scale-invariant in W: an isolated fixed-Vgs/Vds DC
* op-point check (same bias on M1 vs M2A+M2B vs M3A+M3B+M3C, this circuit's
* own device instances, no other circuitry) measures M2's total current
* ~1.0% above M1's, M3's ~2.0% above M1's -- a real, reproducible,
* device-count-driven deviation (not width-narrowing alone: it persists,
* nearly unchanged, from a 1u trim finger down to a 0.5u one, and roughly
* doubles between a 2-count and 3-count branch) confirmed to come from
* recognised-device-count itself, not from any bug in this decomposition's
* wiring. A shallower {1,2,4}-count, equal-width-finger version of this
* same fix (this issue's own first-implemented draft) measured a ~1%
* closed-loop vref shift at every PVT corner from this effect; the
* {1,2,3}-count, dominant+trim-finger geometry above was chosen
* specifically to minimize it (device-count spread is the minimum
* pairwise-distinct set possible, and the trim fingers are kept as small
* as this design's existing HV-pfet width precedent -- w=2u, see MKFB in
* bandgap_startup.sch -- comfortably allows). Full closed-loop PVT
* evidence (all 45 corners, vs a same-day pre-#149 re-baseline run against
* the CURRENT (post-#134-retune) netlist, both runs using this exact
* testbench/tooling) measured a max vref(3ms) delta of 3.81 mV (0.366%,
* bcs/-40C/3.63V) and a 45-corner average of 3.28 mV (~0.31%) -- smaller
* than the ~15 mV process-corner-to-corner spread this design already has
* at any fixed PVT point, and the TC (ppm/C) this repo actually tracks
* against spec/porting-plan.md Sec 6's draft target moved by <=1.3 ppm/C
* at every corner/supply group (worst-case box TC stays ~18 ppm/C, inside
* the draft <50 ppm/C row both before and after). See
* sim/closed-loop-vref-pvt/records/ for the full per-corner CSV this
* summary is drawn from, not assumed from the isolated-device check above
* alone.
*
* Pins: vdd, vss, fb, sns1, sns2, vref
}
G {}
K {}
V {}
S {}
E {}
C {sg13g2_pr/sg13_hv_pmos.sym} 0 200 0 0 {name=M1 model=sg13_hv_pmos w=10u l=1u ng=1 m=1}
N 20 170 40 150 {}
C {lab_pin.sym} 40 150 0 0 {name=l1 lab=vdd}
N 20 200 40 200 {}
C {lab_pin.sym} 40 200 0 0 {name=l2 lab=vdd}
N -20 200 -40 200 {}
C {lab_pin.sym} -40 200 0 0 {name=l3 lab=fb}
N 20 230 40 250 {}
C {lab_pin.sym} 40 250 0 0 {name=l4 lab=sns1}
C {sg13g2_pr/npn13G2.sym} 0 600 0 0 {name=Q1 model=npn13G2 spiceprefix=X Nx=1}
N 20 570 40 550 {}
C {lab_pin.sym} 40 550 0 0 {name=l5 lab=sns1}
N -20 600 -40 600 {}
C {lab_pin.sym} -40 600 0 0 {name=l6 lab=sns1}
N 20 630 40 650 {}
C {lab_pin.sym} 40 650 0 0 {name=l7 lab=vss}
N 20 600 40 600 {}
C {lab_pin.sym} 40 600 0 0 {name=l8 lab=vss}
C {sg13g2_pr/sg13_hv_pmos.sym} 400 200 0 0 {name=M2A model=sg13_hv_pmos w=9u l=1u ng=1 m=1}
N 420 170 440 150 {}
C {lab_pin.sym} 440 150 0 0 {name=l9 lab=vdd}
N 420 200 440 200 {}
C {lab_pin.sym} 440 200 0 0 {name=l10 lab=vdd}
N 380 200 360 200 {}
C {lab_pin.sym} 360 200 0 0 {name=l11 lab=fb}
N 420 230 440 250 {}
C {lab_pin.sym} 440 250 0 0 {name=l12 lab=sns2}
C {sg13g2_pr/sg13_hv_pmos.sym} 400 280 0 0 {name=M2B model=sg13_hv_pmos w=1u l=1u ng=1 m=1}
N 420 250 440 230 {}
C {lab_pin.sym} 440 230 0 0 {name=l29 lab=vdd}
N 420 280 440 280 {}
C {lab_pin.sym} 440 280 0 0 {name=l30 lab=vdd}
N 380 280 360 280 {}
C {lab_pin.sym} 360 280 0 0 {name=l31 lab=fb}
N 420 310 440 330 {}
C {lab_pin.sym} 440 330 0 0 {name=l32 lab=sns2}
C {sg13g2_pr/rppd.sym} 400 400 0 0 {name=R2 model=rppd body=sub! spiceprefix=X w=2u l=82.7u b=0 m=1}
N 400 370 400 350 {}
C {lab_pin.sym} 400 350 0 0 {name=l13 lab=sns2}
N 400 430 400 450 {}
C {lab_pin.sym} 400 450 0 0 {name=l14 lab=cb2}
C {sg13g2_pr/npn13G2.sym} 400 600 0 0 {name=Q2 model=npn13G2 spiceprefix=X Nx=8}
N 420 570 440 550 {}
C {lab_pin.sym} 440 550 0 0 {name=l15 lab=cb2}
N 380 600 360 600 {}
C {lab_pin.sym} 360 600 0 0 {name=l16 lab=cb2}
N 420 630 440 650 {}
C {lab_pin.sym} 440 650 0 0 {name=l17 lab=vss}
N 420 600 440 600 {}
C {lab_pin.sym} 440 600 0 0 {name=l18 lab=vss}
C {sg13g2_pr/sg13_hv_pmos.sym} 800 200 0 0 {name=M3A model=sg13_hv_pmos w=8u l=1u ng=1 m=1}
N 820 170 840 150 {}
C {lab_pin.sym} 840 150 0 0 {name=l19 lab=vdd}
N 820 200 840 200 {}
C {lab_pin.sym} 840 200 0 0 {name=l20 lab=vdd}
N 780 200 760 200 {}
C {lab_pin.sym} 760 200 0 0 {name=l21 lab=fb}
N 820 230 840 250 {}
C {lab_pin.sym} 840 250 0 0 {name=l22 lab=vref}
C {sg13g2_pr/sg13_hv_pmos.sym} 800 280 0 0 {name=M3B model=sg13_hv_pmos w=1u l=1u ng=1 m=1}
N 820 250 840 230 {}
C {lab_pin.sym} 840 230 0 0 {name=l33 lab=vdd}
N 820 280 840 280 {}
C {lab_pin.sym} 840 280 0 0 {name=l34 lab=vdd}
N 780 280 760 280 {}
C {lab_pin.sym} 760 280 0 0 {name=l35 lab=fb}
N 820 310 840 330 {}
C {lab_pin.sym} 840 330 0 0 {name=l36 lab=vref}
C {sg13g2_pr/sg13_hv_pmos.sym} 800 360 0 0 {name=M3C model=sg13_hv_pmos w=1u l=1u ng=1 m=1}
N 820 330 840 310 {}
C {lab_pin.sym} 840 310 0 0 {name=l37 lab=vdd}
N 820 360 840 360 {}
C {lab_pin.sym} 840 360 0 0 {name=l38 lab=vdd}
N 780 360 760 360 {}
C {lab_pin.sym} 760 360 0 0 {name=l39 lab=fb}
N 820 390 840 410 {}
C {lab_pin.sym} 840 410 0 0 {name=l40 lab=vref}
C {sg13g2_pr/rppd.sym} 1050 400 0 0 {name=R1 model=rppd body=sub! spiceprefix=X w=2u l=511u b=0 m=1}
N 1050 370 1050 350 {}
C {lab_pin.sym} 1050 350 0 0 {name=l23 lab=vref}
N 1050 430 1050 450 {}
C {lab_pin.sym} 1050 450 0 0 {name=l24 lab=cb3}
C {sg13g2_pr/npn13G2.sym} 1050 600 0 0 {name=Q3 model=npn13G2 spiceprefix=X Nx=1}
N 1070 570 1090 550 {}
C {lab_pin.sym} 1090 550 0 0 {name=l25 lab=cb3}
N 1030 600 1010 600 {}
C {lab_pin.sym} 1010 600 0 0 {name=l26 lab=cb3}
N 1070 630 1090 650 {}
C {lab_pin.sym} 1090 650 0 0 {name=l27 lab=vss}
N 1070 600 1090 600 {}
C {lab_pin.sym} 1090 600 0 0 {name=l28 lab=vss}
C {iopin.sym} -200 200 0 0 {name=p1 lab=vdd}
C {iopin.sym} -200 600 0 0 {name=p2 lab=vss}
C {iopin.sym} -200 100 0 0 {name=p3 lab=fb}
C {iopin.sym} -200 570 0 0 {name=p4 lab=sns1}
C {iopin.sym} -200 300 0 0 {name=p5 lab=sns2}
C {iopin.sym} 1250 400 0 0 {name=p6 lab=vref}

v {xschem version=3.4.8RC file_version=1.3
* bandgap_startup -- current-sensing, self-disabling startup kick (issue #9),
* per DR-0001 (spec/decision-records/0001-bipolar-device-selection.md)
* Consequences section: any bipolar device in the startup path must respect
* npn13G2's BVCEO/BVEBO (1.0-1.6V target range) -- this circuit uses NO
* bipolar device at all (pure sg13_hv_nmos + one resistor), so that
* constraint does not bind here by construction; noted explicitly per the
* issue's "traceable design intent" ask, same as bandgap_core.sch's header.
*
* Modeled on gf180-bandgap's bandgap_startup.sch current-sensing/self-
* disabling pattern (DR-0001 there rejects a voltage-detect startup as
* chicken-and-egg, and a continuously-conducting bleeder as an Iq cost, in
* favor of sensing the core's own bias current) -- adapted to this core's
* actual exposed nodes. gf180's version senses an internal "ibias" node
* from its core's own diode-connected NMOS bias-mirror leg; THIS core
* (design/bandgap_core.sch, issue #9) has no such leg in its first pass (no
* amplifier-tail bias generator yet -- amplifier is follow-on scope), so
* this circuit instead senses "sns1" directly: bandgap_core's own Q1
* collector/base node, which swings ~0V in the degenerate (all-mirror-off)
* state up to ~0.7-0.8V (Q1's VBE) once the core's mirror is conducting --
* the same qualitative 0V-to-~0.75V swing gf180's "ibias" sensing scheme
* relies on, just read from a different (but equally core-internal, equally
* well-defined) node.
*
* Three devices:
*   RPU      rhigh resistor, vdd -> det. Always-on weak pull-up (rhigh
*            chosen over rppd/rsil for this non-ratio-critical bulk
*            resistance -- porting-plan.md Sec 2's density/TC tradeoff
*            table -- since neither rhigh's strong opposite-sign TC nor its
*            absolute-value tolerance matters for a binary kick signal).
*            Sized ~2 Mohm so its own steady-state current (once MSENSE
*            clamps det low) is ~1.65uA at 3.3V -- a small, itemized
*            addition to the core's own ~15uA (3-branch) design Iq, both
*            PROVISIONAL pending #10.
*   MSENSE   sg13_hv_nmos, gate=sns1, drain=det, source=vss. Off (sns1~0V)
*            in the degenerate state; once the core establishes its ~5uA
*            design current, sns1 rises to ~Q1's VBE and MSENSE conducts
*            far more strongly than RPU can source, clamping det low.
*   MKFB     sg13_hv_nmos, gate=det, drain=fb, source=vss. Kicks
*            bandgap_core's mirror gate "fb" low (turning M1-M3 on) while
*            det is high (degenerate state); releases once MSENSE clamps
*            det low.
*
* Self-starting: at power-up (sns1=0, MSENSE off), RPU pulls det toward
* vdd, turning MKFB on -- fail-safe default is "try to kick". Self-
* disabling: once sns1 rises past MSENSE's threshold, MSENSE overpowers RPU
* and clamps det low, turning MKFB off -- its only remaining contribution is
* subthreshold leakage on fb.
*
* SIZING (re-derived against sim/ evidence -- see below; originally
* PROVISIONAL/hand-picked, same status as bandgap_core.sch's, until #22/#24
* built the OSDI models and the PVT-cornered testbenches that could actually
* check it):
*   RPU:     rhigh, w=1u, l~=1411.3u (R~=2Mohm, solved from rhigh.sym's own
*            R(w,l) formula, b=0 bends)
*   MSENSE:  sg13_hv_nmos, W=10u L=0.5u. Was W=2u through #22's
*            sim/startup-trip-point testbench; #24's cross-bench check
*            (comparing that testbench's trip point against
*            sim/core-open-loop-bias's real sns1 operating point) found the
*            W=2u trip point sitting ABOVE the core's own sns1 at 125 C in
*            the wcs/sf corners (wcs_125c_2.97v/3.30v/3.63v, sf_125c_3.63v)
*            by a few mV -- meaning MKFB would not fully release once the
*            core is actually running there. #24's co-simulated
*            core+startup transient testbench
*            (sim/startup-core-handover/testbench/tb_startup_core_handover.spice.tmpl)
*            confirmed this is a real, and substantially amplified, problem:
*            with the W=2u sense device, the unreleased MKFB current
*            (~15-17uA at the worst point) drives the mirror current well
*            above its ~5uA design point, which self-consistently holds
*            sns1 high enough to keep MKFB partially on -- a stable
*            partial-release state, not a transient artifact (checked out
*            to 10ms). Widening MSENSE to W=10u (5x) drops the residual
*            MKFB current below ~1nA and recovers sns1 to within 0.1mV of
*            the core-only (no startup circuit) operating point at every
*            previously-failing corner, confirmed by re-running both the
*            co-simulation and the standalone sim/startup-trip-point sweep;
*            see spec/decision-records/0003-startup-sense-nmos-resize.md.
*   MKFB:    sg13_hv_nmos, W=2u L=0.5u -- unchanged; sized only to pull fb
*            low against M1-M3's gate capacitance once MSENSE has clamped
*            det low, not to carry current itself, and #24 found no reason
*            to resize it (the margin problem is MSENSE's release strength
*            vs RPU, not MKFB's pull-down strength).
*
* Pins: vdd, vss, sns1, fb
}
G {}
K {}
V {}
S {}
E {}
C {sg13g2_pr/rhigh.sym} 0 0 0 0 {name=RPU model=rhigh body=sub! spiceprefix=X w=1u l=1411.3u b=0 m=1}
N 0 -30 0 -50 {}
C {lab_pin.sym} 0 -50 0 0 {name=l1 lab=vdd}
N 0 30 0 50 {}
C {lab_pin.sym} 0 50 0 0 {name=l2 lab=det}
C {sg13g2_pr/sg13_hv_nmos.sym} 400 0 0 0 {name=MSENSE model=sg13_hv_nmos w=10u l=0.5u ng=1 m=1}
N 420 -30 440 -50 {}
C {lab_pin.sym} 440 -50 0 0 {name=l3 lab=det}
N 380 0 360 0 {}
C {lab_pin.sym} 360 0 0 0 {name=l4 lab=sns1}
N 420 30 440 50 {}
C {lab_pin.sym} 440 50 0 0 {name=l5 lab=vss}
N 420 0 440 0 {}
C {lab_pin.sym} 440 0 0 0 {name=l6 lab=vss}
C {sg13g2_pr/sg13_hv_nmos.sym} 800 0 0 0 {name=MKFB model=sg13_hv_nmos w=2u l=0.5u ng=1 m=1}
N 820 -30 840 -50 {}
C {lab_pin.sym} 840 -50 0 0 {name=l7 lab=fb}
N 780 0 760 0 {}
C {lab_pin.sym} 760 0 0 0 {name=l8 lab=det}
N 820 30 840 50 {}
C {lab_pin.sym} 840 50 0 0 {name=l9 lab=vss}
N 820 0 840 0 {}
C {lab_pin.sym} 840 0 0 0 {name=l10 lab=vss}
C {iopin.sym} -200 0 0 0 {name=p1 lab=vdd}
C {iopin.sym} -200 200 0 0 {name=p2 lab=vss}
C {iopin.sym} 200 -100 0 0 {name=p3 lab=sns1}
C {iopin.sym} 1000 -30 0 0 {name=p4 lab=fb}

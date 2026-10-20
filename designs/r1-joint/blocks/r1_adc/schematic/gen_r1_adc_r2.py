#!/usr/bin/env python3
"""Generate the R1 ADC revision-2 schematic-level SPICE library (schematic/r1_adc_r2.spice, r1_adc_r2_mm.spice).

Revision 2 against revision 1 (gen_r1_adc.py, kept unchanged):
  * VREF = 1.0 V (D11). Full scale = +-VREF * C_switched / (C_top + C_par), about +-0.97 V differential.
  * 13 decisions (12 + 1 redundant, D12), 22 fF units kept, sub-binary array. MSB array on the top node:
    16, 8, 4, 2, 1 Cu (as revision 1). LSB array on the lsb node: 64, 32, 16, 8, 4, 2, 1 Cu (127 Cu).
    Bridge Cb = 1.249 Cu (cap_cmim 4.23 x 4.23 um, 27.52 fF): one top unit = 205.4 raw steps, the LSB array
    = 255 raw steps. Nominal decision weights (raw steps): 3286, 1643, 821, 411, 205, 128, 64, 32, 16, 8, 4, 2, 1
    (sum 6621 -> 1 raw step = 0.619 LSB of the 12-bit output). Every top-array decision and the bridge
    boundary have +50 raw steps (+31 LSB) of redundancy; the raw step below 0.7 LSB keeps the re-quantisation
    DNL of the corrected 12-bit code within -0.38 / +0.24 LSB. History: two earlier revision-2 arrays with a raw
    step of about 1 LSB failed DNL <= 0.5 after correction by construction (runs r2-cdac-mc50-tt-cp0,
    r2-cdac-mc50-tt-b-cp0; README).
  * Output: 13 raw decision bits per slice (raw image rawX = sum b_j 2^(12-j), 0..8191); the code is formed in
    r1_ctrl as code = sat12((sum b_j w_j + 4) >> 3) with host-loaded 14-bit weights (11.3 fixed point).
  * Per-slice track controls: trk_a0 (SIN), trk_a1 (ISA), trk_b0 (COS), trk_b1 (ISB). Slice A tracks again
    while slice B converts. Flag reset of a slice = OR of its two track signals.
  * Comparator r1_cmp2: larger PMOS input pair and PMOS-capacitor integration nodes (noise <= 60 uV target).
  * Reference buffer r1_refbuf: rhigh divider 22/23 of the 1.045 V bandgap node, HV OTA (VDDA 3.3 V) and HV
    NMOS source follower with MIM decoupling (see the subckt header).
Python 3.6 compatible.
"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))

NB = 12            # switched capacitors per side (C11..C0); 13 decisions
CU_W = "3.78u"     # unit 22.04 fF (S4)
CB_W = "4.23u"     # bridge 27.52 fF = 1.249 Cu
CAPS = {11: ("top", 16), 10: ("top", 8), 9: ("top", 4), 8: ("top", 2), 7: ("top", 1),
        6: ("lsb", 64), 5: ("lsb", 32), 4: ("lsb", 16), 3: ("lsb", 8), 2: ("lsb", 4), 1: ("lsb", 2), 0: ("lsb", 1)}
ND = 13            # decisions per slice

# comparator sizes (revision 2); see sim/r2/README section in the block README
CMP = dict(wi="48u", li="0.3u", ngi=12, wt="16u", wtc="16u", ltc="0.5u", wcap="16u", lcap="4u", wr="2u", wh="8u", ratio=20)


def bootsw():
    return """
* ---------------------------------------------------------------------------------------------
* r1_bootsw: bootstrapped NMOS sampling switch (unchanged from revision 1).
* ---------------------------------------------------------------------------------------------
.subckt r1_bootsw vin out trk trkb vdd gnd wsw=6u cboot=200f
XMS   vin  g    out  gnd  sg13_lv_nmos w={wsw} l=0.13u ng=2 m=1
Cboot cbp  cbn  {cboot}
XM1   cbn  trkb gnd  gnd  sg13_lv_nmos w=1u l=0.13u ng=1 m=1
XM3   cbp  g    vdd  cbp  sg13_lv_pmos w=1u l=0.13u ng=1 m=1
XM8   g    x    cbp  cbp  sg13_lv_pmos w=2u l=0.13u ng=1 m=1
XM4   x    trk  vdd  vdd  sg13_lv_pmos w=0.5u l=0.13u ng=1 m=1
XM5   x    trk  cbn  gnd  sg13_lv_nmos w=1u l=0.13u ng=1 m=1
XM7   x    g    cbn  gnd  sg13_lv_nmos w=0.5u l=0.13u ng=1 m=1
XM9   cbn  g    vin  gnd  sg13_lv_nmos w=2u l=0.13u ng=1 m=1
XM10  g    vdd  n10  gnd  sg13_lv_nmos w=2u l=0.13u ng=1 m=1
XM11  n10  trkb gnd  gnd  sg13_lv_nmos w=2u l=0.13u ng=1 m=1
.ends r1_bootsw

.subckt r1_offsw vin out gnd wsw=6u
XMS   vin  gnd  out  gnd  sg13_lv_nmos w={wsw} l=0.13u ng=2 m=1
.ends r1_offsw

* bottom-plate drivers (unchanged): in=0 -> out=VREF, in=1 -> out=GND
.subckt r1_drv in out vref gnd wp=1u wn=0.5u
XMP out in vref vref sg13_lv_pmos w={wp} l=0.13u ng=1 m=1
XMN out in gnd  gnd  sg13_lv_nmos w={wn} l=0.13u ng=1 m=1
.ends r1_drv

.subckt r1_drv_sw in out vref gnd
BU vref out i=(v(vref)-v(out))*(1e-12+2.5e-3*(0.5-0.5*tanh(20*(v(in)-0.6))))
BD out gnd i=(v(out)-v(gnd))*(1e-12+2.5e-3*(0.5+0.5*tanh(20*(v(in)-0.6))))
.ends r1_drv_sw
"""


def cdac(mc):
    name = "r1_cdac2_side_mc" if mc else "r1_cdac2_side"
    bl = " ".join("b%d" % k for k in range(NB - 1, -1, -1))
    s = ["",
         "* ---------------------------------------------------------------------------------------------",
         "* %s: one side of the revision-2 split array. Unit Cu = cap_cmim %s x %s (22.04 fF)." % (name, CU_W, CU_W),
         "* top: C11..C7 = 16, 8, 4, 2, 1 Cu; bridge Cb = cap_cmim %s x %s (1.249 Cu) top-lsb;" % (CB_W, CB_W),
         "* lsb: C6..C0 = 64, 32, 16, 8, 4, 2, 1 Cu (sub-binary with the top array). %s" % ("One instance per unit (mismatch MC, mm_ok={mm})." if mc else "Nominal (m=)."),
         "* ---------------------------------------------------------------------------------------------",
         ".subckt %s top lsb %s%s" % (name, bl, " mm=1" if mc else "")]
    for k in range(NB - 1, -1, -1):
        node, u = CAPS[k]
        if mc:
            for i in range(u):
                s.append("XC%d_%d %s b%d cap_cmim w=%s l=%s mm_ok={mm}" % (k, i, node, k, CU_W, CU_W))
        else:
            s.append("XC%d %s b%d cap_cmim w=%s l=%s m=%d" % (k, node, k, CU_W, CU_W, u))
    s.append("XCB top lsb cap_cmim w=%s l=%s%s" % (CB_W, CB_W, " mm_ok={mm}" if mc else " m=1"))
    s.append(".ends %s" % name)
    return "\n".join(s) + "\n"


def comparator():
    c = dict(CMP)
    c["wtcd"] = "%gu" % (float(c["wtc"].rstrip("u")) / c["ratio"])
    return """
* ---------------------------------------------------------------------------------------------
* r1_cmp2: double-tail dynamic comparator, revision 2 (low noise). Same topology as r1_cmp.
* PMOS input pair {wi}/{li} ng={ngi}; integration nodes dip/din loaded by PMOS gate capacitors {wcap}/{lcap}
* (gate on the node, source/drain/bulk at VDD: inverted channel while the node is below VDD-|VT|), which sets
* the integration time and therefore the noise bandwidth. Reset devices {wr}.
* clk=1, clkb=0: evaluate. clk=0: reset, outp = outn = VDD. inp > inn -> outp stays high.
* ---------------------------------------------------------------------------------------------
.subckt r1_cmp2_s1 inp inn dip din clkb vbp vdd gnd wi=48u li=0.3u ngi=12 wt=16u wtc=16u ltc=0.5u
* first (integrating) stage of r1_cmp2; separate so that the noise deck can bias dip/din externally.
* Tail = switch XMT1 (clkb) in series with current source XMTC (gate vbp from r1_cmp2_bias): the integration
* current, and therefore the integration time and noise, stays nearly constant while the input common mode
* falls from 0.6 V to 0.1 V during monotonic switching.
XMT1 tail0 clkb vdd  vdd sg13_lv_pmos w={{wt}} l=0.13u ng=4 m=1
XMTC tail  vbp  tail0 vdd sg13_lv_pmos w={{wtc}} l={{ltc}} ng=2 m=1
XM1  dip  inp  tail vdd sg13_lv_pmos w={{wi}} l={{li}} ng={{ngi}} m=1
XM2  din  inn  tail vdd sg13_lv_pmos w={{wi}} l={{li}} ng={{ngi}} m=1
.ends r1_cmp2_s1

.subckt r1_cmp2 inp inn clk clkb outp outn vbp vdd gnd wi={wi} li={li} ngi={ngi} wt={wt} wtc={wtc} ltc={ltc} wcap={wcap} lcap={lcap} wr={wr} wh={wh}
XS1  inp inn dip din clkb vbp vdd gnd r1_cmp2_s1 wi={{wi}} li={{li}} ngi={{ngi}} wt={{wt}} wtc={{wtc}} ltc={{ltc}}
XCI1 vdd  dip  vdd  vdd sg13_lv_pmos w={{wcap}} l={{lcap}} ng=2 m=1
XCI2 vdd  din  vdd  vdd sg13_lv_pmos w={{wcap}} l={{lcap}} ng=2 m=1
XMR1 dip  clkb gnd  gnd sg13_lv_nmos w={{wr}} l=0.13u ng=1 m=1
XMR2 din  clkb gnd  gnd sg13_lv_nmos w={{wr}} l=0.13u ng=1 m=1
XMT2 lt   clk  gnd  gnd sg13_lv_nmos w=4u l=0.13u ng=1 m=1
XMN1 outp outn lt   gnd sg13_lv_nmos w=2u l=0.13u ng=1 m=1
XMN2 outn outp lt   gnd sg13_lv_nmos w=2u l=0.13u ng=1 m=1
XMP1 outp outn vdd  vdd sg13_lv_pmos w=2u l=0.13u ng=1 m=1
XMP2 outn outp vdd  vdd sg13_lv_pmos w=2u l=0.13u ng=1 m=1
XMH1 outp dip  vdd  vdd sg13_lv_pmos w={{wh}} l=0.13u ng=2 m=1
XMH2 outn din  vdd  vdd sg13_lv_pmos w={{wh}} l=0.13u ng=2 m=1
XBP1 outpb outp vdd vdd sg13_lv_pmos w=1u l=0.13u ng=1 m=1
XBN1 outpb outp gnd gnd sg13_lv_nmos w=0.5u l=0.13u ng=1 m=1
XBP2 outnb outn vdd vdd sg13_lv_pmos w=1u l=0.13u ng=1 m=1
XBN2 outnb outn gnd gnd sg13_lv_nmos w=0.5u l=0.13u ng=1 m=1
Cbp outpb gnd 3f
Cbn outnb gnd 3f
.ends r1_cmp2

* r1_cmp2_bias: bias of the comparator tail current sources. ib = ideal reference current (stands in for the
* bandgap-derived bias current; labelled ideal in the run records). Diode XMBD with w = wtc / {ratio}.
.subckt r1_cmp2_bias vbp vdd gnd ib=14u
Ibc vbp gnd {{ib}}
XMBD vbp vbp vdd vdd sg13_lv_pmos w={wtcd} l={ltc} ng=1 m=1
.ends r1_cmp2_bias
""".format(**c)


def inv(name, a, y, vdd, gnd, wp="1u", wn="0.5u"):
    return ("XP%s %s %s %s %s sg13_lv_pmos w=%s l=0.13u ng=1 m=1\n"
            "XN%s %s %s %s %s sg13_lv_nmos w=%s l=0.13u ng=1 m=1\n" % (name, y, a, vdd, vdd, wp, name, y, a, gnd, gnd, wn))


def th(fast):
    name = "r1_th2_fast" if fast else "r1_th2"
    cp = " ".join("cp%d" % k for k in range(NB - 1, -1, -1))
    cn = " ".join("cn%d" % k for k in range(NB - 1, -1, -1))
    s = ["",
         "* ---------------------------------------------------------------------------------------------",
         "* %s: one revision-2 track-and-hold slice (CDAC P and N, top-plate sampling)." % name,
         "* in0 sampled while trk0=1, in1 while trk1=1 (never both); sample on the falling edge. lsb nodes reset",
         "* to VREF while either path tracks. cpK/cnK = 1: bottom plate K of side P/N goes VREF -> GND.",
         "* Fast variant: in1 pair reduced to r1_offsw (gate low), trk1 unused; drivers r1_drv_sw (ideal 400 ohm)." if fast else
         "* Full variant: both input pairs with complete bootstrapped switches; transistor drivers r1_drv.",
         "* ---------------------------------------------------------------------------------------------",
         ".subckt %s in0p in0n in1p in1n trk0 trk1 top_p top_n %s %s vdd vref gnd" % (name, cp, cn)]
    s.append(inv("T0a", "trk0", "t0b", "vdd", "gnd", "2u", "1u").rstrip())
    s.append(inv("T0b", "t0b", "t0", "vdd", "gnd", "4u", "2u").rstrip())
    if not fast:
        s.append(inv("T1a", "trk1", "t1b", "vdd", "gnd", "2u", "1u").rstrip())
        s.append(inv("T1b", "t1b", "t1", "vdd", "gnd", "4u", "2u").rstrip())
    s.append("XS0P in0p top_p t0 t0b vdd gnd r1_bootsw")
    s.append("XS0N in0n top_n t0 t0b vdd gnd r1_bootsw")
    if fast:
        s.append("XS1P in1p top_p gnd r1_offsw")
        s.append("XS1N in1n top_n gnd r1_offsw")
        s.append("Rtrk1 trk1 gnd 1e9")
        rb = "t0b"
    else:
        s.append("XS1P in1p top_p t1 t1b vdd gnd r1_bootsw")
        s.append("XS1N in1n top_n t1 t1b vdd gnd r1_bootsw")
        s.append("XPR1 rstb_n t0b vdd vdd sg13_lv_pmos w=1u l=0.13u ng=1 m=1")
        s.append("XPR2 rstb_n t1b vdd vdd sg13_lv_pmos w=1u l=0.13u ng=1 m=1")
        s.append("XNR1 rstb_n t0b nr gnd sg13_lv_nmos w=1u l=0.13u ng=1 m=1")
        s.append("XNR2 nr t1b gnd gnd sg13_lv_nmos w=1u l=0.13u ng=1 m=1")
        s.append(inv("R3", "rstb_n", "rstb", "vdd", "gnd").rstrip())
        rb = "rstb"
    s.append("XLRP lsb_p %s vref vref sg13_lv_pmos w=1u l=0.13u ng=1 m=1" % rb)
    s.append("XLRN lsb_n %s vref vref sg13_lv_pmos w=1u l=0.13u ng=1 m=1" % rb)
    s.append("XDACP top_p lsb_p " + " ".join("bp%d" % k for k in range(NB - 1, -1, -1)) + " r1_cdac2_side")
    s.append("XDACN top_n lsb_n " + " ".join("bn%d" % k for k in range(NB - 1, -1, -1)) + " r1_cdac2_side")
    for side in ("p", "n"):
        for k in range(NB - 1, -1, -1):
            if fast:
                s.append("XD%s%d c%s%d b%s%d vref gnd r1_drv_sw" % (side, k, side, k, side, k))
            else:
                w = ("wp=2u wn=1u" if k >= 9 else "wp=1u wn=0.5u")
                s.append("XD%s%d c%s%d b%s%d vref gnd r1_drv %s" % (side, k, side, k, side, k, w))
    s.append(".ends %s" % name)
    return "\n".join(s) + "\n"


def stb_list():
    return " ".join("stb%d" % k for k in range(2 * ND))


def ctl_list(pfx):
    return " ".join("%s%d" % (pfx, k) for k in range(NB - 1, -1, -1))


def sar_logic():
    """Per slice X (a: decisions in stb0..12, b: stb13..25), decision k = 0..12:
       P_k <= outp at stb; V_k <= 1 at stb (decision taken); N_k = V_k AND NOT P_k; reset by rstX = trkX0 OR trkX1.
       Exactly one side switches per decision even if the comparator has not resolved at stb (metastable input,
       |residue| small): the redundancy then absorbs the arbitrary decision. (First revision-2 logic captured
       outn separately and lost a 1024-LSB decision at +0.3 mV input: run r2-quick-tt-c.)
       Capacitor C(11-k) (k = 0..11): cp = P_k, cn = N_k. Raw bit r_k (k = 0 first) <= P_k at latX.
       rawX = sum r_k 2^(12-k) (analog image 0..8191, for the decks only)."""
    s = ["",
         "* ---------------------------------------------------------------------------------------------",
         "* r1_sar2_logic: XSPICE SAR register, 13 decisions per slice, raw-bit output (D12).",
         "* Timing inputs from r1_ctrl (ideal sources in the decks): mclk, wina, winb, lata, latb, stb0..stb25,",
         "* track signals trka0 trka1 trkb0 trkb1 (flag reset of slice X while either of its paths tracks).",
         "* Comparator clocks: clkX = mclk AND winX. Raw bits: ra12..ra0 / rb12..rb0 (ra12 = first decision).",
         "* Per decision: P <= outp at stb, V <= 1 at stb, N = V AND NOT P (one side switches per decision).",
         "* ---------------------------------------------------------------------------------------------",
         ".subckt r1_sar2_logic oap oan obp obn mclk wina winb trka0 trka1 trkb0 trkb1 lata latb %s "
         "clka clkab clkb clkbb %s %s %s %s rawa rawb vdd gnd"
         % (stb_list(), ctl_list("cpa"), ctl_list("cna"), ctl_list("cpb"), ctl_list("cnb"))]
    s.append(".model r1_adcb adc_bridge(in_low=0.6 in_high=0.6 rise_delay=20p fall_delay=20p)")
    s.append(".model r1_dacb dac_bridge(out_low=0 out_high=1.2 out_undef=0.6 input_load=1e-15 t_rise=80p t_fall=80p)")
    s.append(".model r1_dff d_dff(clk_delay=80p set_delay=80p reset_delay=80p ic=0 rise_delay=20p fall_delay=20p)")
    s.append(".model r1_and d_and(rise_delay=30p fall_delay=30p)")
    s.append(".model r1_nand d_nand(rise_delay=30p fall_delay=30p)")
    s.append(".model r1_or d_or(rise_delay=30p fall_delay=30p)")
    ins = ["vdd", "oap", "oan", "obp", "obn", "mclk", "wina", "winb", "trka0", "trka1", "trkb0", "trkb1", "lata", "latb"] + \
          ["stb%d" % k for k in range(2 * ND)]
    s.append("ABR [%s] [%s] r1_adcb" % (" ".join(ins), " ".join("d_" + x for x in ins)))
    s.append("AGA1 [d_mclk d_wina] g_clka r1_and")
    s.append("AGA2 [d_mclk d_wina] g_clkab r1_nand")
    s.append("AGB1 [d_mclk d_winb] g_clkb r1_and")
    s.append("AGB2 [d_mclk d_winb] g_clkbb r1_nand")
    s.append("AORA [d_trka0 d_trka1] d_rsta r1_or")
    s.append("AORB [d_trkb0 d_trkb1] d_rstb r1_or")
    outs_d, outs_a = ["g_clka", "g_clkab", "g_clkb", "g_clkbb"], ["clka", "clkab", "clkb", "clkbb"]
    for ch, op, on, off in (("a", "d_oap", "d_oan", 0), ("b", "d_obp", "d_obn", ND)):
        for k in range(ND):
            st = "d_stb%d" % (k + off)
            s.append("AFP%s%d %s %s NULL d_rst%s fp%s%d nfp%s%d r1_dff" % (ch, k, op, st, ch, ch, k, ch, k))
            if k < NB:
                s.append("AFV%s%d d_vdd %s NULL d_rst%s fv%s%d nfv%s%d r1_dff" % (ch, k, st, ch, ch, k, ch, k))
                s.append("AFN%s%d [fv%s%d nfp%s%d] fn%s%d r1_and" % (ch, k, ch, k, ch, k, ch, k))
                outs_d += ["fp%s%d" % (ch, k), "fn%s%d" % (ch, k)]
                outs_a += ["cp%s%d" % (ch, NB - 1 - k), "cn%s%d" % (ch, NB - 1 - k)]
            s.append("AQ%s%d fp%s%d d_lat%s NULL NULL q%s%d nq%s%d r1_dff" % (ch, k, ch, k, ch, ch, k, ch, k))
        for k in range(ND):
            outs_d.append("q%s%d" % (ch, k))
            outs_a.append("r%s%d" % (ch, ND - 1 - k))
    s.append("ADB [%s] [%s] r1_dacb" % (" ".join(outs_d), " ".join(outs_a)))
    for ch in ("a", "b"):
        terms = "+".join("%d*v(r%s%d)" % (2 ** b, ch, b) for b in range(ND))
        s.append("Braw%s raw%s gnd v=(%s)/1.2" % (ch, ch, terms))
    s.append(".ends r1_sar2_logic")
    return "\n".join(s) + "\n"


CORE_PORTS = ("sinp sinn cosp cosn isap isan isbp isbn trka0 trka1 trkb0 trkb1 mclk wina winb lata latb %s "
              "rawa rawb topap topan topbp topbn vdd vref gnd")


def core(kind):
    name = {"full": "r1_adc2_core", "fast": "r1_adc2_core_fast", "fast_a": "r1_adc2_core_fast_a"}[kind]
    thn = "r1_th2" if kind == "full" else "r1_th2_fast"
    s = ["",
         "* ---------------------------------------------------------------------------------------------",
         "* %s: R1 ADC revision-2 core. Slice A: in0 = SIN, in1 = ISA. Slice B: in0 = COS, in1 = ISB." % name,
         "* Frame (30 cycles of 30 MHz): A decides in cycles 0-12, B in 13-25; A tracks 13-29, B tracks 26-29." if kind != "fast_a" else
         "* Slice A only (slice B and comparator B removed, comparator-B inputs of the SAR logic tied); static decks.",
         "* ---------------------------------------------------------------------------------------------",
         (".subckt %s " % name) + CORE_PORTS % stb_list()]
    s.append("XTHA sinp sinn isap isan trka0 trka1 topap topan %s %s vdd vref gnd %s" % (ctl_list("cpa"), ctl_list("cna"), thn))
    s.append("XCBIAS vbp vdd gnd r1_cmp2_bias")
    s.append("XCMPA topap topan clka clkab oap oan vbp vdd gnd r1_cmp2")
    if kind == "fast_a":
        s += ["Vtieb1 obp gnd 1.2", "Vtieb2 obn gnd 0", "Rtb1 topbp gnd 1e9", "Rtb2 topbn gnd 1e9"]
    else:
        s.append("XTHB cosp cosn isbp isbn trkb0 trkb1 topbp topbn %s %s vdd vref gnd %s" % (ctl_list("cpb"), ctl_list("cnb"), thn))
        s.append("XCMPB topbp topbn clkb clkbb obp obn vbp vdd gnd r1_cmp2")
    s.append("XSAR oap oan obp obn mclk wina winb trka0 trka1 trkb0 trkb1 lata latb %s clka clkab clkb clkbb %s %s %s %s "
             "rawa rawb vdd gnd r1_sar2_logic" % (stb_list(), ctl_list("cpa"), ctl_list("cna"), ctl_list("cpb"), ctl_list("cnb")))
    s.append(".ends %s" % name)
    return "\n".join(s) + "\n"


def refbuf():
    seg = "\n".join("XRD%d n%d n%d gnd rhigh w=1e-6 l=10e-6 m=1" % (i, i, i + 1) for i in range(1, 23))
    seg = seg.replace("XRD1 n1 ", "XRD1 vbg ").replace(" n2 gnd rhigh", " vtap gnd rhigh", 1).replace("XRD2 n2 ", "XRD2 vtap ")
    return """
* ---------------------------------------------------------------------------------------------
* r1_refbuf: ADC reference buffer, 1.0 V from the bandgap node (vbg = 1.045 V, G1 lineage; ideal in the decks).
*  divider: 23 equal rhigh segments (w 1 um, l 10 um), tap 22/23 from ground: 0.99957 V; ~3 uA from vbg.
*  error amplifier (VDDA 3.3 V, thick oxide): HV NMOS pair (+ vtap, - vref), HV PMOS mirror, tail = 2 x bias.
*  output stage: HV NMOS source follower (drain VDDA, msf x 4 x 10/0.45 um) sunk by an HV NMOS mirror of
*  mib x the bias current at vref; gate node held by a MIM capacitor (cg MIM cells of 50 x 50 um, 3.76 pF each)
*  so that the fast CDAC charge is served by the follower (1/gm) and the decoupling capacitor.
*  decoupling: ndec MIM cells of 70 x 70 um (7.36 pF each) on vref.
*  bias: ibias (ideal 5 uA reference current; stands in for the bandgap-derived iptat bias).
* Ports: vbg vref vdda gnd.
* ---------------------------------------------------------------------------------------------
.subckt r1_refbuf vbg vref vdda gnd msf=8 mib=40 ndec=6 ncg=1
%s
XRD23 n23 gnd gnd rhigh w=1e-6 l=10e-6 m=1
Ibias vdda nb 5u
XMB0 nb nb gnd gnd sg13_hv_nmos w=2u l=1u ng=1 m=1
XMT  ntl nb gnd gnd sg13_hv_nmos w=2u l=1u ng=1 m=2
XM1  na  vtap ntl gnd sg13_hv_nmos w=10u l=1u ng=2 m=1
XM2  ng  vref ntl gnd sg13_hv_nmos w=10u l=1u ng=2 m=1
XM3  na  na  vdda vdda sg13_hv_pmos w=4u l=1u ng=1 m=1
XM4  ng  na  vdda vdda sg13_hv_pmos w=4u l=1u ng=1 m=1
XCG  ng  gnd cap_cmim w=50u l=50u m={ncg}
XMSF vdda ng vref gnd sg13_hv_nmos w=10u l=0.45u ng=4 m={msf}
XMIB vref nb gnd gnd sg13_hv_nmos w=2u l=1u ng=1 m={mib}
XCD  vref gnd cap_cmim w=70u l=70u m={ndec}
.ends r1_refbuf
""" % seg


def main():
    hdr = ("* r1_adc_r2.spice -- R1 12-bit SAR ADC revision 2, schematic-level library (generated by gen_r1_adc_r2.py; "
           "do not edit)\n* Requires: cornerMOSlv.lib, cornerMOShv.lib (r1_refbuf), cornerCAP.lib, cornerRES.lib (r1_refbuf), "
           "XSPICE digital code models, PSP/R3 OSDI.\n")
    body = (bootsw() + cdac(False) + cdac(True) + comparator() + th(False) + th(True) + sar_logic()
            + core("full") + core("fast") + core("fast_a") + refbuf())
    with open(os.path.join(HERE, "r1_adc_r2.spice"), "w") as f:
        f.write(hdr + body)
    mm = re.sub(r"(sg13_(?:lv|hv)_[np]mos [^\n]*?m=(?:1|\{\w+\}))", r"\1 mm_ok={mmos}", body)
    with open(os.path.join(HERE, "r1_adc_r2_mm.spice"), "w") as f:
        f.write(hdr.replace("r1_adc_r2.spice --", "r1_adc_r2_mm.spice --") +
                "* Mismatch-capable copy: MOS instances carry mm_ok={mmos} (deck sets .param mmos).\n" + mm)
    print("wrote r1_adc_r2.spice, r1_adc_r2_mm.spice")


if __name__ == "__main__":
    main()

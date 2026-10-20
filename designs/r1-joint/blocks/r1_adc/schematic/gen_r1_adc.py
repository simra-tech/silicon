#!/usr/bin/env python3
"""Generate the R1 ADC schematic-level SPICE library (schematic/r1_adc.spice).

12-bit differential SAR, 1.2 V domain, two top-plate-sampled CDAC track-and-holds (A, B) sampled on one
edge, a 2 x 2 input multiplexer (A: SIN or ISA, B: COS or ISB), one SAR logic block, one comparator per
CDAC, split 6+6 bridge MIM array, monotonic switching. Python 3.6 compatible.

Sub-circuits written:
  r1_bootsw        bootstrapped NMOS sampling switch (Abo-Gray type)
  r1_offsw         the main device of an unselected bootstrapped switch only (gate held low): load model
  r1_drv           bottom-plate driver, CMOS inverter between VREF and GND
  r1_drv_sw        bottom-plate driver, ideal switch pair (Ron) between VREF and GND (fast decks)
  r1_cdac_side     one side of the split array (nominal: m= multipliers)
  r1_cdac_side_mc  one side of the split array, one cap_cmim instance per unit (mismatch MC)
  r1_cmp           double-tail dynamic comparator, PMOS input pair
  r1_th            one track-and-hold slice: CDAC P and N, 2 bootstrapped input pairs, LSB-node reset,
                   track buffers, 22 bottom-plate drivers
  r1_th_fast       same, unselected input pair reduced to r1_offsw, drivers r1_drv_sw
  r1_sar_logic     XSPICE digital SAR register (B / BN flags), comparator clock gating, output latch
  r1_adc_core      2 x r1_th + 2 x r1_cmp + r1_sar_logic
  r1_adc_core_fast 2 x r1_th_fast + 2 x r1_cmp + r1_sar_logic
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))

NB = 11            # switched capacitors per side (C10..C0)
# unit capacitor: cap_cmim w = l = 3.78 um -> 1.5 fF/um2 * 14.29 um2 + 40 aF/um * 15.12 um = 22.04 fF (S4)
CU_W = "3.78u"
CU_L = "3.78u"
# cap index -> (node, units). C10..C6 on the top node (MSB array), C5..C0 on the LSB node.
CAPS = {10: ("top", 16), 9: ("top", 8), 8: ("top", 4), 7: ("top", 2), 6: ("top", 1),
        5: ("lsb", 32), 4: ("lsb", 16), 3: ("lsb", 8), 2: ("lsb", 4), 1: ("lsb", 2), 0: ("lsb", 1)}


def nm(w, l, ng=1):
    return "w=%s l=%s ng=%d m=1" % (w, l, ng)


def bootsw():
    return """
* ---------------------------------------------------------------------------------------------
* r1_bootsw: bootstrapped NMOS sampling switch. trk=1 (trkb=0): out follows vin, gate g = vin + VDD.
* Boost capacitor ideal 200 fF in this step (to be a MIM or MOS capacitor in layout).
* Thin-oxide stress: every device sees <= VDD between any two terminals (MN10 splits the g discharge).
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

* r1_offsw: main device of a deselected bootstrapped switch (gate held at gnd), load and feed-through model
.subckt r1_offsw vin out gnd wsw=6u
XMS   vin  gnd  out  gnd  sg13_lv_nmos w={wsw} l=0.13u ng=2 m=1
.ends r1_offsw
"""


def drivers():
    return """
* ---------------------------------------------------------------------------------------------
* Bottom-plate drivers. in=0 -> out=VREF (reset / sampling state); in=1 -> out=GND (monotonic step).
* ---------------------------------------------------------------------------------------------
.subckt r1_drv in out vref gnd wp=1u wn=0.5u
XMP out in vref vref sg13_lv_pmos w={wp} l=0.13u ng=1 m=1
XMN out in gnd  gnd  sg13_lv_nmos w={wn} l=0.13u ng=1 m=1
.ends r1_drv

* fast-deck driver: ideal smooth conductance pair, Ron 400 ohm, Roff 1e12 (marked ideal in run records).
* s = 0.5*(1+tanh(20*(v(in)-0.6))): in=0 -> out tied to VREF, in=1.2 -> out tied to GND. Current is drawn from VREF.
.subckt r1_drv_sw in out vref gnd
BU vref out i=(v(vref)-v(out))*(1e-12+2.5e-3*(0.5-0.5*tanh(20*(v(in)-0.6))))
BD out gnd i=(v(out)-v(gnd))*(1e-12+2.5e-3*(0.5+0.5*tanh(20*(v(in)-0.6))))
.ends r1_drv_sw
"""


def cdac_nominal():
    s = ["",
         "* ---------------------------------------------------------------------------------------------",
         "* r1_cdac_side: one side of the split 6+6 bridge array. Unit Cu = cap_cmim %s x %s (22.04 fF)." % (CU_W, CU_L),
         "* MSB array on top: C10..C6 = 16,8,4,2,1 Cu; bridge Cb = 1 Cu (top-lsb); LSB array on lsb: C5..C0 = 32..1 Cu",
         "* (63 Cu, no dummy, so Cb/(63+Cb) = 1/64 exactly). Bottom plates b10..b0. Nominal: multipliers m=.",
         "* ---------------------------------------------------------------------------------------------",
         ".subckt r1_cdac_side top lsb " + " ".join("b%d" % k for k in range(NB - 1, -1, -1))]
    for k in range(NB - 1, -1, -1):
        node, u = CAPS[k]
        s.append("XC%d %s b%d cap_cmim w=%s l=%s m=%d" % (k, node, k, CU_W, CU_L, u))
    s.append("XCB top lsb cap_cmim w=%s l=%s m=1" % (CU_W, CU_L))
    s.append(".ends r1_cdac_side")
    return "\n".join(s) + "\n"


def cdac_mc():
    s = ["",
         "* r1_cdac_side_mc: same array, one cap_cmim instance per unit so that each unit draws its own",
         "* mismatch value (cap_*_mismatch section, mm_ok=1).",
         ".subckt r1_cdac_side_mc top lsb " + " ".join("b%d" % k for k in range(NB - 1, -1, -1)) + " mm=1"]
    for k in range(NB - 1, -1, -1):
        node, u = CAPS[k]
        for i in range(u):
            s.append("XC%d_%d %s b%d cap_cmim w=%s l=%s mm_ok={mm}" % (k, i, node, k, CU_W, CU_L))
    s.append("XCB top lsb cap_cmim w=%s l=%s mm_ok={mm}" % (CU_W, CU_L))
    s.append(".ends r1_cdac_side_mc")
    return "\n".join(s) + "\n"


def comparator():
    return """
* ---------------------------------------------------------------------------------------------
* r1_cmp: double-tail dynamic comparator (AnalogAcademy module 3 / Lin 2010 lineage, Schinkel stage 2).
* PMOS input pair so that the input common mode may fall from 0.6 V to ~0 V (monotonic switching).
* clk=1, clkb=0: evaluate. clk=0: reset, outp = outn = VDD. Decision: inp > inn -> outp stays high.
* ---------------------------------------------------------------------------------------------
.subckt r1_cmp inp inn clk clkb outp outn vdd gnd
XMT1 tail clkb vdd  vdd sg13_lv_pmos w=8u l=0.13u ng=2 m=1
XM1  dip  inp  tail vdd sg13_lv_pmos w=16u l=0.2u ng=4 m=1
XM2  din  inn  tail vdd sg13_lv_pmos w=16u l=0.2u ng=4 m=1
XMR1 dip  clkb gnd  gnd sg13_lv_nmos w=1u l=0.13u ng=1 m=1
XMR2 din  clkb gnd  gnd sg13_lv_nmos w=1u l=0.13u ng=1 m=1
XMT2 lt   clk  gnd  gnd sg13_lv_nmos w=4u l=0.13u ng=1 m=1
XMN1 outp outn lt   gnd sg13_lv_nmos w=2u l=0.13u ng=1 m=1
XMN2 outn outp lt   gnd sg13_lv_nmos w=2u l=0.13u ng=1 m=1
XMP1 outp outn vdd  vdd sg13_lv_pmos w=2u l=0.13u ng=1 m=1
XMP2 outn outp vdd  vdd sg13_lv_pmos w=2u l=0.13u ng=1 m=1
XMH1 outp dip  vdd  vdd sg13_lv_pmos w=2u l=0.13u ng=1 m=1
XMH2 outn din  vdd  vdd sg13_lv_pmos w=2u l=0.13u ng=1 m=1
* output buffers (load of the SAR register inputs)
XBP1 outpb outp vdd vdd sg13_lv_pmos w=1u l=0.13u ng=1 m=1
XBN1 outpb outp gnd gnd sg13_lv_nmos w=0.5u l=0.13u ng=1 m=1
XBP2 outnb outn vdd vdd sg13_lv_pmos w=1u l=0.13u ng=1 m=1
XBN2 outnb outn gnd gnd sg13_lv_nmos w=0.5u l=0.13u ng=1 m=1
Cbp outpb gnd 3f
Cbn outnb gnd 3f
.ends r1_cmp
"""


def inv(name, a, y, vdd, gnd, wp="1u", wn="0.5u"):
    return ("XP%s %s %s %s %s sg13_lv_pmos w=%s l=0.13u ng=1 m=1\n"
            "XN%s %s %s %s %s sg13_lv_nmos w=%s l=0.13u ng=1 m=1\n" % (name, y, a, vdd, vdd, wp, name, y, a, gnd, gnd, wn))


def th(fast):
    name = "r1_th_fast" if fast else "r1_th"
    cp = " ".join("cp%d" % k for k in range(NB - 1, -1, -1))
    cn = " ".join("cn%d" % k for k in range(NB - 1, -1, -1))
    s = ["",
         "* ---------------------------------------------------------------------------------------------",
         "* %s: one track-and-hold slice = CDAC P and N with top-plate sampling." % name,
         "* in0 (encoder SIN or COS) sampled when trk0=1, in1 (current channel) when trk1=1. The sample is",
         "* taken on the falling edge of trk0/trk1 (common for both slices). lsb nodes reset to VREF in track.",
         "* cpK/cnK = 1: bottom plate of capacitor K on side P/N goes VREF -> GND.",
         "* top_p/top_n are the comparator inputs.",
         "* Fast variant: deselected input pair = r1_offsw only; drivers r1_drv_sw (ideal switches)." if fast else
         "* Full variant: both input pairs with complete bootstrapped switches; transistor drivers.",
         "* ---------------------------------------------------------------------------------------------",
         ".subckt %s in0p in0n in1p in1n trk0 trk1 top_p top_n %s %s vdd vref gnd" % (name, cp, cn)]
    # track buffers: two inverters per trk input -> trkX (buffered) and trkXb
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
        s.append("* trk1 unused in the fast variant (deselected path)")
        s.append("Rtrk1 trk1 gnd 1e9")
        trkany_b = "t0b"
    else:
        s.append("XS1P in1p top_p t1 t1b vdd gnd r1_bootsw")
        s.append("XS1N in1n top_n t1 t1b vdd gnd r1_bootsw")
        # lsb reset when either path tracks: nand(t0b, t1b) inverted -> active-low gate for PMOS reset
        s.append("* lsb reset gate rstb = NOT(t0 OR t1) = AND(t0b, t1b) (static CMOS)")
        s.append("XPR1 rstb_n t0b vdd vdd sg13_lv_pmos w=1u l=0.13u ng=1 m=1")
        s.append("XPR2 rstb_n t1b vdd vdd sg13_lv_pmos w=1u l=0.13u ng=1 m=1")
        s.append("XNR1 rstb_n t0b nr gnd sg13_lv_nmos w=1u l=0.13u ng=1 m=1")
        s.append("XNR2 nr t1b gnd gnd sg13_lv_nmos w=1u l=0.13u ng=1 m=1")
        s.append(inv("R3", "rstb_n", "rstb", "vdd", "gnd").rstrip())
        trkany_b = "rstb"
    s.append("* lsb-node reset to VREF during track (PMOS, gate low in track)")
    s.append("XLRP lsb_p %s vref vref sg13_lv_pmos w=1u l=0.13u ng=1 m=1" % trkany_b)
    s.append("XLRN lsb_n %s vref vref sg13_lv_pmos w=1u l=0.13u ng=1 m=1" % trkany_b)
    s.append("XDACP top_p lsb_p " + " ".join("bp%d" % k for k in range(NB - 1, -1, -1)) + " r1_cdac_side")
    s.append("XDACN top_n lsb_n " + " ".join("bn%d" % k for k in range(NB - 1, -1, -1)) + " r1_cdac_side")
    drv = "r1_drv_sw" if fast else "r1_drv"
    for side in ("p", "n"):
        for k in range(NB - 1, -1, -1):
            if fast:
                s.append("XD%s%d c%s%d b%s%d vref gnd %s" % (side, k, side, k, side, k, drv))
            else:
                w = ("wp=2u wn=1u" if k >= 8 else "wp=1u wn=0.5u")
                s.append("XD%s%d c%s%d b%s%d vref gnd %s %s" % (side, k, side, k, side, k, drv, w))
    s.append(".ends %s" % name)
    return "\n".join(s) + "\n"


def sar_logic():
    """XSPICE SAR register. Per channel X in (A, B), decision k = 0..11 (k=0 -> b11, MSB):
       flag P_k <= outp at strobe k, flag N_k <= outn at strobe k; reset by rst (track).
       Bottom-plate control for capacitor C(10-k): cp = P_k, cn = N_k (k = 0..10).
       Output latch: code bit b(11-k) <= P_k at lat. Comparator clocks: clkX = mclk AND winX."""
    stbA = " ".join("stb%d" % k for k in range(24))
    cpa = " ".join("cpa%d" % k for k in range(NB - 1, -1, -1))
    cna = " ".join("cna%d" % k for k in range(NB - 1, -1, -1))
    cpb = " ".join("cpb%d" % k for k in range(NB - 1, -1, -1))
    cnb = " ".join("cnb%d" % k for k in range(NB - 1, -1, -1))
    s = ["",
         "* ---------------------------------------------------------------------------------------------",
         "* r1_sar_logic: XSPICE digital SAR register (behavioural-structural, B/BN flags as in",
         "* AnalogAcademy sar_logic.v). Timing inputs (mclk, winA, winB, rst, lat, stb0..stb23) come from the",
         "* controller (r1_ctrl); in this step from ideal sources in the test bench.",
         "* Outputs: clkA/clkAb, clkB/clkBb comparator clocks; cpaK/cnaK, cpbK/cnbK bottom-plate controls;",
         "* codeA/codeB analog image of the latched 12-bit codes (0..4095) for the decks.",
         "* ---------------------------------------------------------------------------------------------",
         ".subckt r1_sar_logic oap oan obp obn mclk wina winb rst lat %s clka clkab clkb clkbb %s %s %s %s codea codeb vdd gnd"
         % (stbA, cpa, cna, cpb, cnb)]
    s.append(".model r1_adcb adc_bridge(in_low=0.6 in_high=0.6 rise_delay=20p fall_delay=20p)")
    s.append(".model r1_dacb dac_bridge(out_low=0 out_high=1.2 out_undef=0.6 input_load=1e-15 t_rise=80p t_fall=80p)")
    s.append(".model r1_dff d_dff(clk_delay=80p set_delay=80p reset_delay=80p ic=0 rise_delay=20p fall_delay=20p)")
    s.append(".model r1_and d_and(rise_delay=30p fall_delay=30p)")
    s.append(".model r1_nand d_nand(rise_delay=30p fall_delay=30p)")
    ins = ["oap", "oan", "obp", "obn", "mclk", "wina", "winb", "rst", "lat"] + ["stb%d" % k for k in range(24)]
    s.append("ABR [%s] [%s] r1_adcb" % (" ".join(ins), " ".join("d_" + x for x in ins)))
    s.append("AGA1 [d_mclk d_wina] g_clka r1_and")
    s.append("AGA2 [d_mclk d_wina] g_clkab r1_nand")
    s.append("AGB1 [d_mclk d_winb] g_clkb r1_and")
    s.append("AGB2 [d_mclk d_winb] g_clkbb r1_nand")
    outs_d, outs_a = ["g_clka", "g_clkab", "g_clkb", "g_clkbb"], ["clka", "clkab", "clkb", "clkbb"]
    for ch, op, on, off in (("a", "d_oap", "d_oan", 0), ("b", "d_obp", "d_obn", 12)):
        for k in range(12):
            st = "d_stb%d" % (k + off)
            s.append("AFP%s%d %s %s NULL d_rst fp%s%d nfp%s%d r1_dff" % (ch, k, op, st, ch, k, ch, k))
            if k < 11:
                s.append("AFN%s%d %s %s NULL d_rst fn%s%d nfn%s%d r1_dff" % (ch, k, on, st, ch, k, ch, k))
                outs_d += ["fp%s%d" % (ch, k), "fn%s%d" % (ch, k)]
                outs_a += ["cp%s%d" % (ch, 10 - k), "cn%s%d" % (ch, 10 - k)]
            s.append("AQ%s%d fp%s%d d_lat NULL NULL q%s%d nq%s%d r1_dff" % (ch, 11 - k, ch, k, ch, 11 - k, ch, 11 - k))
        for b in range(12):
            outs_d.append("q%s%d" % (ch, b))
            outs_a.append("qa_%s%d" % (ch, b))
    s.append("ADB [%s] [%s] r1_dacb" % (" ".join(outs_d), " ".join(outs_a)))
    for ch in ("a", "b"):
        terms = "+".join("%d*v(qa_%s%d)" % (2 ** b, ch, b) for b in range(12))
        s.append("Bcode%s code%s gnd v=(%s)/1.2" % (ch, ch, terms))
    s.append(".ends r1_sar_logic")
    return "\n".join(s) + "\n"


def core(fast):
    name = "r1_adc_core_fast" if fast else "r1_adc_core"
    th_name = "r1_th_fast" if fast else "r1_th"
    stb = " ".join("stb%d" % k for k in range(24))
    s = ["",
         "* ---------------------------------------------------------------------------------------------",
         "* %s: R1 ADC core. Slice A: in0 = SIN, in1 = ISA. Slice B: in0 = COS, in1 = ISB." % name,
         "* trk_enc samples SIN and COS together, trk_cur samples ISA and ISB together (one edge each).",
         "* Conversion order per 1 us frame (30 MHz, 30 cycles): A in cycles 0-11, B in 12-23, track 24-29.",
         "* ---------------------------------------------------------------------------------------------",
         ".subckt %s sinp sinn cosp cosn isap isan isbp isbn trk_enc trk_cur mclk wina winb rst lat %s codea codeb "
         "topap topan topbp topbn vdd vref gnd" % (name, stb)]
    cpa = " ".join("cpa%d" % k for k in range(NB - 1, -1, -1))
    cna = " ".join("cna%d" % k for k in range(NB - 1, -1, -1))
    cpb = " ".join("cpb%d" % k for k in range(NB - 1, -1, -1))
    cnb = " ".join("cnb%d" % k for k in range(NB - 1, -1, -1))
    s.append("XTHA sinp sinn isap isan trk_enc trk_cur topap topan %s %s vdd vref gnd %s" % (cpa, cna, th_name))
    s.append("XTHB cosp cosn isbp isbn trk_enc trk_cur topbp topbn %s %s vdd vref gnd %s" % (cpb, cnb, th_name))
    s.append("XCMPA topap topan clka clkab oap oan vdd gnd r1_cmp")
    s.append("XCMPB topbp topbn clkb clkbb obp obn vdd gnd r1_cmp")
    s.append("XSAR oap oan obp obn mclk wina winb rst lat %s clka clkab clkb clkbb %s %s %s %s codea codeb vdd gnd r1_sar_logic"
             % (stb, cpa, cna, cpb, cnb))
    s.append(".ends %s" % name)
    return "\n".join(s) + "\n"


def core_single():
    """Slice A only (static decks at nominal with ideal supplies: slice B does not interact with slice A)."""
    stb = " ".join("stb%d" % k for k in range(24))
    cpa = " ".join("cpa%d" % k for k in range(NB - 1, -1, -1))
    cna = " ".join("cna%d" % k for k in range(NB - 1, -1, -1))
    cpb = " ".join("cpb%d" % k for k in range(NB - 1, -1, -1))
    cnb = " ".join("cnb%d" % k for k in range(NB - 1, -1, -1))
    s = ["",
         "* r1_adc_core_fast_a: r1_adc_core_fast with slice B and comparator B removed (comparator B inputs of",
         "* the SAR logic tied). Same port list as r1_adc_core_fast. For static-linearity decks only.",
         ".subckt r1_adc_core_fast_a sinp sinn cosp cosn isap isan isbp isbn trk_enc trk_cur mclk wina winb rst lat %s "
         "codea codeb topap topan topbp topbn vdd vref gnd" % stb,
         "XTHA sinp sinn isap isan trk_enc trk_cur topap topan %s %s vdd vref gnd r1_th_fast" % (cpa, cna),
         "XCMPA topap topan clka clkab oap oan vdd gnd r1_cmp",
         "Vtieb1 obp gnd 1.2", "Vtieb2 obn gnd 0",
         "Rtb1 topbp gnd 1e9", "Rtb2 topbn gnd 1e9",
         "XSAR oap oan obp obn mclk wina winb rst lat %s clka clkab clkb clkbb %s %s %s %s codea codeb vdd gnd r1_sar_logic"
         % (stb, cpa, cna, cpb, cnb),
         ".ends r1_adc_core_fast_a"]
    return "\n".join(s) + "\n"


def main():
    hdr = ("* r1_adc.spice -- R1 12-bit SAR ADC, schematic-level library (generated by gen_r1_adc.py; do not edit)\n"
           "* Requires: cornerMOSlv.lib (mos_*), cornerCAP.lib (cap_*), XSPICE digital code models, PSP OSDI.\n")
    body = (bootsw() + drivers() + cdac_nominal() + cdac_mc() + comparator() + th(False) + th(True) + sar_logic()
            + core(False) + core(True) + core_single())
    with open(os.path.join(HERE, "r1_adc.spice"), "w") as f:
        f.write(hdr + body)
    # mismatch-capable copy: every MOS instance carries mm_ok={mmos}; the deck defines .param mmos=0|1
    import re
    mm = re.sub(r"(sg13_lv_[np]mos [^\n]*?m=1)", r"\1 mm_ok={mmos}", body)
    with open(os.path.join(HERE, "r1_adc_mm.spice"), "w") as f:
        f.write(hdr.replace("r1_adc.spice --", "r1_adc_mm.spice --") +
                "* Mismatch-capable copy of r1_adc.spice: MOS instances carry mm_ok={mmos} (deck sets .param mmos).\n" + mm)
    print("wrote r1_adc.spice, r1_adc_mm.spice")


if __name__ == "__main__":
    main()

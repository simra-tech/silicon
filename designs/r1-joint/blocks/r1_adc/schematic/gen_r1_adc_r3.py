#!/usr/bin/env python3
"""Generate the R1 ADC revision-3 schematic-level SPICE library (schematic/r1_adc_r3.spice, r1_adc_r3_mm.spice).

Revision 3 against revision 2 (gen_r1_adc_r2.py, kept unchanged):
  * 14 decisions (12 + 2 redundant, D17). The LSB array gets a half unit C0 = cap_cmim 2.67 x 2.67 um (about
    0.505 Cu) on the lsb node. 13 switched capacitors per side: top 16, 8, 4, 2, 1 Cu (C12..C8), bridge
    1.249 Cu, lsb 64, 32, 16, 8, 4, 2, 1 Cu (C7..C1) and 0.5 Cu (C0). Decision j = 0..12 switches C(12-j);
    decision 13 only compares. Raw step about 0.31 LSB.
  * Both slices convert in parallel (D17), each with its own comparator and its own SAR register. Decisions run
    at two per clk30 tick (half-tick decision period 16.67 ns, comparator evaluates 13.5 ns, resets 3.2 ns).
    The 36-tick frame then gives 7.1 ticks per conversion and a 10-tick (332 ns) track window per slot.
  * Comparator r1_cmp3: r1_cmp2 topology with larger integration capacitors and a resistor-defined bias
    (r1_cmp3_bias: diode PMOS + rppd resistor to ground, I = (VDD - Vsg)/R). The tail current follows
    VDD - |Vtp|, the same quantity that sets the integration swing, so the integration time (and the noise)
    varies less with corner than with the fixed 14 uA of revision 2.
  * Reference buffer r1_refbuf3: the revision-2 circuit with the revision-3 defaults (see the subckt header).
Python 3.6 compatible.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gen_r1_adc_r2 as r2   # bootstrapped switch, off switch and drivers are unchanged

NB = 13            # switched capacitors per side (C12..C0); 14 decisions
ND = 14
CU_W = "3.78u"
CB_W = "4.23u"
CH_W = "2.67u"     # half unit
CAPS = {12: ("top", 16), 11: ("top", 8), 10: ("top", 4), 9: ("top", 2), 8: ("top", 1),
        7: ("lsb", 64), 6: ("lsb", 32), 5: ("lsb", 16), 4: ("lsb", 8), 3: ("lsb", 4), 2: ("lsb", 2), 1: ("lsb", 1),
        0: ("lsb", "h")}

# comparator sizes (revision 3); chosen in sim/r3 comparator runs (README, Revision 3)
CMP = dict(wi="48u", li="0.3u", ngi=12, wt="16u", wtc="16u", ltc="0.5u", wcap="32u", lcap="4u", wr="8u", wh="8u",
           ratio=20, rbw="1u", rbl="160u")
# reference buffer defaults (revision 3)
REF = dict(msf=32, mib=160, ndec=6, ncg=1)


def cdac(mc):
    name = "r1_cdac3_side_mc" if mc else "r1_cdac3_side"
    bl = " ".join("b%d" % k for k in range(NB - 1, -1, -1))
    s = ["",
         "* " + "-" * 93,
         "* %s: one side of the revision-3 split array (14 decisions). Unit Cu = cap_cmim %s x %s (22.04 fF)." % (name, CU_W, CU_W),
         "* top: C12..C8 = 16, 8, 4, 2, 1 Cu; bridge Cb = cap_cmim %s x %s (1.249 Cu) top-lsb;" % (CB_W, CB_W),
         "* lsb: C7..C1 = 64, 32, 16, 8, 4, 2, 1 Cu, C0 = cap_cmim %s x %s (half unit). %s" % (CH_W, CH_W, "One instance per unit (mismatch MC)." if mc else "Nominal (m=)."),
         "* " + "-" * 93,
         ".subckt %s top lsb %s%s" % (name, bl, " mm=1" if mc else "")]
    for k in range(NB - 1, -1, -1):
        node, u = CAPS[k]
        if u == "h":
            s.append("XC0 %s b0 cap_cmim w=%s l=%s%s" % (node, CH_W, CH_W, " mm_ok={mm}" if mc else " m=1"))
        elif mc:
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
* r1_cmp3: double-tail dynamic comparator, revision 3. Topology of r1_cmp2 (revision 2); integration
* capacitors {wcap}/{lcap} (PMOS gate capacitors on dip/din). clk=1, clkb=0: evaluate; clk=0: reset.
* inp > inn -> outp stays high.
* ---------------------------------------------------------------------------------------------
.subckt r1_cmp3_s1 inp inn dip din clkb vbp vdd gnd wi=48u li=0.3u ngi=12 wt=16u wtc=16u ltc=0.5u
XMT1 tail0 clkb vdd  vdd sg13_lv_pmos w={{wt}} l=0.13u ng=4 m=1
XMTC tail  vbp  tail0 vdd sg13_lv_pmos w={{wtc}} l={{ltc}} ng=2 m=1
XM1  dip  inp  tail vdd sg13_lv_pmos w={{wi}} l={{li}} ng={{ngi}} m=1
XM2  din  inn  tail vdd sg13_lv_pmos w={{wi}} l={{li}} ng={{ngi}} m=1
.ends r1_cmp3_s1

.subckt r1_cmp3 inp inn clk clkb outp outn vbp vdd gnd wi={wi} li={li} ngi={ngi} wt={wt} wtc={wtc} ltc={ltc} wcap={wcap} lcap={lcap} wr={wr} wh={wh}
XS1  inp inn dip din clkb vbp vdd gnd r1_cmp3_s1 wi={{wi}} li={{li}} ngi={{ngi}} wt={{wt}} wtc={{wtc}} ltc={{ltc}}
XCI1 vdd  dip  vdd  vdd sg13_lv_pmos w={{wcap}} l={{lcap}} ng=4 m=1
XCI2 vdd  din  vdd  vdd sg13_lv_pmos w={{wcap}} l={{lcap}} ng=4 m=1
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
.ends r1_cmp3

* r1_cmp3_bias: tail bias, I = (VDD - Vsg(XMBD)) / R with R = rppd {rbw} x {rbl} (about 42 kohm at
* 260 ohm/sq + heads). Diode XMBD w = wtc / {ratio}. The current falls where VDD - |Vtp| falls (low VDD, slow
* PMOS), which keeps the integration time C_int (VDD - |Vtp|) / I nearly constant.
.subckt r1_cmp3_bias vbp vdd gnd rbw={rbw} rbl={rbl}
XMBD vbp vbp vdd vdd sg13_lv_pmos w={wtcd} l={ltc} ng=1 m=1
XRB  vbp gnd gnd rppd w={{rbw}} l={{rbl}} m=1
.ends r1_cmp3_bias

* r1_cmp3_ibias: the revision-2 ideal-current bias, kept for comparison runs only.
.subckt r1_cmp3_ibias vbp vdd gnd ib=14u
Ibc vbp gnd {{ib}}
XMBD vbp vbp vdd vdd sg13_lv_pmos w={wtcd} l={ltc} ng=1 m=1
.ends r1_cmp3_ibias
""".format(**c)


def inv(name, a, y, vdd, gnd, wp="1u", wn="0.5u"):
    return ("XP%s %s %s %s %s sg13_lv_pmos w=%s l=0.13u ng=1 m=1\n"
            "XN%s %s %s %s %s sg13_lv_nmos w=%s l=0.13u ng=1 m=1\n" % (name, y, a, vdd, vdd, wp, name, y, a, gnd, gnd, wn))


def th(fast):
    name = "r1_th3_fast" if fast else "r1_th3"
    cp = " ".join("cp%d" % k for k in range(NB - 1, -1, -1))
    cn = " ".join("cn%d" % k for k in range(NB - 1, -1, -1))
    s = ["",
         "* " + "-" * 93,
         "* %s: one revision-3 track-and-hold slice (CDAC P and N, top-plate sampling, 13 caps per side)." % name,
         "* in0 sampled while trk0=1, in1 while trk1=1 (never both); sample on the falling edge. lsb nodes reset",
         "* to VREF while either path tracks. cpK/cnK = 1: bottom plate K of side P/N goes VREF -> GND.",
         "* Fast variant: in1 pair reduced to r1_offsw, trk1 unused; drivers r1_drv_sw (ideal 400 ohm)." if fast else
         "* Full variant: both input pairs with complete bootstrapped switches; transistor drivers r1_drv.",
         "* " + "-" * 93,
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
    s.append("XDACP top_p lsb_p " + " ".join("bp%d" % k for k in range(NB - 1, -1, -1)) + " r1_cdac3_side")
    s.append("XDACN top_n lsb_n " + " ".join("bn%d" % k for k in range(NB - 1, -1, -1)) + " r1_cdac3_side")
    for side in ("p", "n"):
        for k in range(NB - 1, -1, -1):
            if fast:
                s.append("XD%s%d c%s%d b%s%d vref gnd r1_drv_sw" % (side, k, side, k, side, k))
            else:
                w = ("wp=2u wn=1u" if k >= 10 else "wp=1u wn=0.5u")
                s.append("XD%s%d c%s%d b%s%d vref gnd r1_drv %s" % (side, k, side, k, side, k, w))
    s.append(".ends %s" % name)
    return "\n".join(s) + "\n"


def stb_list():
    return " ".join("stb%d" % k for k in range(ND))


def ctl_list(pfx):
    return " ".join("%s%d" % (pfx, k) for k in range(NB - 1, -1, -1))


def sar_logic():
    s = ["",
         "* " + "-" * 93,
         "* r1_sar3_logic: XSPICE SAR registers, 14 decisions, one register per slice (D17: both slices convert",
         "* in parallel, own comparator and own register). Timing inputs from r1_ctrl (ideal in the decks):",
         "* mclk (comparator evaluate, two per clk30 tick), wina/winb (conversion windows), stb0..stb13 (decision",
         "* strobes, common to both slices), lata/latb, track signals (flag reset of slice X while it tracks).",
         "* Per decision: P <= outp at stb, V <= 1 at stb, N = V AND NOT P (exactly one side switches).",
         "* Raw bits rX13..rX0 (rX13 = first decision) latched at latX.",
         "* " + "-" * 93,
         ".subckt r1_sar3_logic oap oan obp obn mclk wina winb trka0 trka1 trkb0 trkb1 lata latb %s "
         "clka clkab clkb clkbb %s %s %s %s rawa rawb vdd gnd"
         % (stb_list(), ctl_list("cpa"), ctl_list("cna"), ctl_list("cpb"), ctl_list("cnb"))]
    s.append(".model r1_adcb adc_bridge(in_low=0.6 in_high=0.6 rise_delay=20p fall_delay=20p)")
    s.append(".model r1_dacb dac_bridge(out_low=0 out_high=1.2 out_undef=0.6 input_load=1e-15 t_rise=80p t_fall=80p)")
    s.append(".model r1_dff d_dff(clk_delay=80p set_delay=80p reset_delay=80p ic=0 rise_delay=20p fall_delay=20p)")
    s.append(".model r1_and d_and(rise_delay=30p fall_delay=30p)")
    s.append(".model r1_nand d_nand(rise_delay=30p fall_delay=30p)")
    s.append(".model r1_or d_or(rise_delay=30p fall_delay=30p)")
    ins = ["vdd", "oap", "oan", "obp", "obn", "mclk", "wina", "winb", "trka0", "trka1", "trkb0", "trkb1", "lata", "latb"] + \
          ["stb%d" % k for k in range(ND)]
    s.append("ABR [%s] [%s] r1_adcb" % (" ".join(ins), " ".join("d_" + x for x in ins)))
    s.append("AGA1 [d_mclk d_wina] g_clka r1_and")
    s.append("AGA2 [d_mclk d_wina] g_clkab r1_nand")
    s.append("AGB1 [d_mclk d_winb] g_clkb r1_and")
    s.append("AGB2 [d_mclk d_winb] g_clkbb r1_nand")
    s.append("AORA [d_trka0 d_trka1] d_rsta r1_or")
    s.append("AORB [d_trkb0 d_trkb1] d_rstb r1_or")
    outs_d, outs_a = ["g_clka", "g_clkab", "g_clkb", "g_clkbb"], ["clka", "clkab", "clkb", "clkbb"]
    for ch, op in (("a", "d_oap"), ("b", "d_obp")):
        for k in range(ND):
            st = "d_stb%d" % k
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
    s.append(".ends r1_sar3_logic")
    return "\n".join(s) + "\n"


CORE_PORTS = ("sinp sinn cosp cosn isap isan isbp isbn trka0 trka1 trkb0 trkb1 mclk wina winb lata latb %s "
              "rawa rawb topap topan topbp topbn vdd vref gnd")


def core(kind):
    name = {"full": "r1_adc3_core", "fast": "r1_adc3_core_fast"}[kind]
    thn = "r1_th3" if kind == "full" else "r1_th3_fast"
    s = ["",
         "* " + "-" * 93,
         "* %s: R1 ADC revision-3 core. Slice A: in0 = SIN, in1 = ISA. Slice B: in0 = COS, in1 = ISB." % name,
         "* Both slices convert in parallel (D17). Comparator bias r1_cmp3_bias shared by both comparators.",
         "* " + "-" * 93,
         (".subckt %s " % name) + CORE_PORTS % stb_list()]
    s.append("XTHA sinp sinn isap isan trka0 trka1 topap topan %s %s vdd vref gnd %s" % (ctl_list("cpa"), ctl_list("cna"), thn))
    s.append("XCBIAS vbp vdd gnd r1_cmp3_bias")
    s.append("XCMPA topap topan clka clkab oap oan vbp vdd gnd r1_cmp3")
    s.append("XTHB cosp cosn isbp isbn trkb0 trkb1 topbp topbn %s %s vdd vref gnd %s" % (ctl_list("cpb"), ctl_list("cnb"), thn))
    s.append("XCMPB topbp topbn clkb clkbb obp obn vbp vdd gnd r1_cmp3")
    s.append("XSAR oap oan obp obn mclk wina winb trka0 trka1 trkb0 trkb1 lata latb %s clka clkab clkb clkbb %s %s %s %s "
             "rawa rawb vdd gnd r1_sar3_logic" % (stb_list(), ctl_list("cpa"), ctl_list("cna"), ctl_list("cpb"), ctl_list("cnb")))
    s.append(".ends %s" % name)
    return "\n".join(s) + "\n"


def refbuf():
    t = r2.refbuf()
    t = t.replace("r1_refbuf vbg vref vdda gnd msf=8 mib=40 ndec=6 ncg=1",
                  "r1_refbuf3 vbg vref vdda gnd msf=%d mib=%d ndec=%d ncg=%d" % (REF["msf"], REF["mib"], REF["ndec"], REF["ncg"]))
    t = t.replace(".ends r1_refbuf", ".ends r1_refbuf3")
    t = t.replace("* r1_refbuf: ADC reference buffer,", "* r1_refbuf3 (revision 3, circuit of revision-2 r1_refbuf, new defaults): ADC reference buffer,")
    return t


def main():
    hdr = ("* r1_adc_r3.spice -- R1 12-bit SAR ADC revision 3, schematic-level library (generated by gen_r1_adc_r3.py; "
           "do not edit)\n* Requires: cornerMOSlv.lib, cornerMOShv.lib (r1_refbuf3), cornerCAP.lib, cornerRES.lib, "
           "XSPICE digital code models, PSP/R3 OSDI.\n")
    body = (r2.bootsw() + cdac(False) + cdac(True) + comparator() + th(False) + th(True) + sar_logic()
            + core("full") + core("fast") + refbuf())
    with open(os.path.join(HERE, "r1_adc_r3.spice"), "w") as f:
        f.write(hdr + body)
    mm = re.sub(r"(sg13_(?:lv|hv)_[np]mos [^\n]*?m=(?:1|\{\w+\}))", r"\1 mm_ok={mmos}", body)
    with open(os.path.join(HERE, "r1_adc_r3_mm.spice"), "w") as f:
        f.write(hdr.replace("r1_adc_r3.spice --", "r1_adc_r3_mm.spice --") +
                "* Mismatch-capable copy: MOS instances carry mm_ok={mmos} (deck sets .param mmos).\n" + mm)
    print("wrote r1_adc_r3.spice, r1_adc_r3_mm.spice")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Generate the R1 ADC revision-4 schematic-level SPICE library (schematic/r1_adc_r4.spice, r1_adc_r4_mm.spice).

Revision 4 against revision 3 (gen_r1_adc_r3.py, kept unchanged), decision D18:
  * One decision per clk30 tick (33.3 ns). The two-decisions-per-tick timing of revision 3 and its undesigned
    3 ns evaluate/reset delay cell are removed.
  * r1_cmp4_clkgen (new, transistor level): comparator clock from clk30. A rising clk30 edge (the decision
    strobe of r1_ctrl) starts a short reset pulse (one-shot: 5-inverter delay chain + NAND); the comparator
    evaluates for the rest of the tick. mclk = 1: evaluate. No separate timing edge from r1_ctrl is needed.
  * r1_cmp4: the r1_cmp3 topology with larger integration capacitors and reset NMOS for the longer evaluation
    window (sizes in CMP below, chosen by the sim/r4 comparator sweep, README Revision 4).
  * r1_sar4_logic: one strobe set per slice (stba0..13, stbb0..13), so slice B can run with a fixed offset of
    N ticks after slice A (R2-4 stagger option). Comparator clock of slice X = mclk AND winX.
  * r1_th4*: the LSB-array bottom-plate drivers (C7..C0) and the lsb-node reset use a separate port vrefl.
    Tie vrefl to vref for one common reference; drive it from its own buffer for the separate-LSB-reference
    option (R2-4 option 3).
  * r1_adc4_core (full), r1_adc4_core_fast, r1_adc4_core_fast_mc (MIM mismatch, one cap_cmim per unit).
  * r1_refbuf4: the r1_refbuf3 circuit (unchanged), defaults of the chosen option.
Python 3.6 compatible.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gen_r1_adc_r2 as r2   # bootstrapped switch, off switch and drivers are unchanged
import gen_r1_adc_r3 as r3   # CDAC sides (r1_cdac3_side, r1_cdac3_side_mc) and inverter helper are unchanged

NB, ND = r3.NB, r3.ND
# comparator sizes (revision 4); chosen in the sim/r4 comparator sweep (README, Revision 4)
CMP = dict(wi="48u", li="0.3u", ngi=12, wt="16u", wtc="16u", ltc="0.5u", wcap="80u", lcap="4u", wr="20u", wh="8u",
           ratio=20, rbw="1u", rbl="160u")
# comparator clock one-shot (revision 4): inverter chain device sizes and load
CKG = dict(wn="0.5u", wp="1u", ln="0.5u", lp="0.5u", cl="10f", nst=5)
# reference buffer defaults (revision 4)
REF = dict(msf=32, mib=160, ndec=6, ncg=1, mt=1, lt="8u")   # chosen R2-4 option (README Revision 4)


def comparator():
    t = r3.comparator()
    for a, b in (("r1_cmp3_s1", "r1_cmp4_s1"), ("r1_cmp3_bias", "r1_cmp4_bias"), ("r1_cmp3_ibias", "r1_cmp4_ibias"),
                 ("r1_cmp3", "r1_cmp4")):
        t = t.replace(a, b)
    c = dict(CMP)
    for k in ("wcap", "wr", "wi", "li", "ngi"):
        t = re.sub(r"(\.subckt r1_cmp4 [^\n]*?\b%s=)[^ \n]+" % k, r"\g<1>%s" % c[k], t)
    t = re.sub(r"(\.subckt r1_cmp4_bias [^\n]*?\brbl=)[^ \n]+", r"\g<1>%s" % c["rbl"], t)
    t = t.replace("* r1_cmp3: double-tail dynamic comparator, revision 3. Topology of r1_cmp2 (revision 2); integration",
                  "* r1_cmp4: double-tail dynamic comparator, revision 4 (r1_cmp3 topology, sizes for one decision per tick); integration")
    return t


def clkgen():
    c = dict(CKG)
    n = c["nst"]
    L = ["",
         "* " + "-" * 93,
         "* r1_cmp4_clkgen: comparator clock from clk30 (revision 4). mclk = NAND(clk30, x), x = clk30 inverted and",
         "* delayed by %d inverters (wn %s/%s, wp %s/%s, %s load each). A rising clk30 edge gives mclk = 0 (comparator" % (n, c["wn"], c["ln"], c["wp"], c["lp"], c["cl"]),
         "* reset) for the chain delay; then mclk = 1 (evaluate) until the next rising edge. mclkb = NOT mclk.",
         "* clk30 low half: x = 1 after the falling edge -> NAND output = 1 (evaluate continues). Width: README.",
         "* " + "-" * 93,
         ".subckt r1_cmp4_clkgen clk30 mclk mclkb vdd gnd"]
    prev = "clk30"
    for i in range(n):
        nxt = "x" if i == n - 1 else "d%d" % i
        L.append("XPD%d %s %s vdd vdd sg13_lv_pmos w=%s l=%s ng=1 m=1" % (i, nxt, prev, c["wp"], c["lp"]))
        L.append("XND%d %s %s gnd gnd sg13_lv_nmos w=%s l=%s ng=1 m=1" % (i, nxt, prev, c["wn"], c["ln"]))
        L.append("CD%d %s gnd %s" % (i, nxt, c["cl"]))
        prev = nxt
    L += ["XPA mclk clk30 vdd vdd sg13_lv_pmos w=2u l=0.13u ng=1 m=1",
          "XPB mclk x vdd vdd sg13_lv_pmos w=2u l=0.13u ng=1 m=1",
          "XNA mclk clk30 nn gnd sg13_lv_nmos w=2u l=0.13u ng=1 m=1",
          "XNB nn x gnd gnd sg13_lv_nmos w=2u l=0.13u ng=1 m=1",
          "XPI mclkb mclk vdd vdd sg13_lv_pmos w=2u l=0.13u ng=1 m=1",
          "XNI mclkb mclk gnd gnd sg13_lv_nmos w=1u l=0.13u ng=1 m=1",
          ".ends r1_cmp4_clkgen"]
    return "\n".join(L) + "\n"


def th(fast, mc=False):
    t = r3.th(fast)
    old = "r1_th3_fast" if fast else "r1_th3"
    new = ("r1_th4_fast" if fast else "r1_th4") + ("_mc" if mc else "")
    t = t.replace(old, new)
    t = t.replace(" vdd vref gnd\n", " vdd vref vrefl gnd\n", 1)
    t = t.replace("XLRP lsb_p %s vref vref", "XLRP lsb_p %s vrefl vrefl")
    t = re.sub(r"XLR([PN]) lsb_([pn]) (\w+) vref vref", r"XLR\1 lsb_\2 \3 vrefl vrefl", t)
    for side in ("p", "n"):
        for k in range(0, 8):        # LSB array C7..C0 on vrefl
            t = re.sub(r"(XD%s%d c%s%d b%s%d) vref gnd" % (side, k, side, k, side, k), r"\1 vrefl gnd", t)
    if mc:
        t = t.replace(" r1_cdac3_side\n", " r1_cdac3_side_mc mm=1\n")
    t = t.replace("* %s: one revision-3 track-and-hold slice" % new, "* %s: one revision-4 track-and-hold slice" % new)
    t = t.replace(".ends %s" % new, "* revision 4: LSB-array drivers C7..C0 and the lsb-node reset on vrefl\n.ends %s" % new)
    return t


def stb_list(ch):
    return " ".join("stb%s%d" % (ch, k) for k in range(ND))


def ctl_list(pfx):
    return " ".join("%s%d" % (pfx, k) for k in range(NB - 1, -1, -1))


def sar_logic():
    s = ["",
         "* " + "-" * 93,
         "* r1_sar4_logic: XSPICE SAR registers, 14 decisions, one register per slice (D17/D18: both slices convert",
         "* in parallel, own comparator and own register). Timing inputs from r1_ctrl (ideal in the decks): mclk",
         "* (from r1_cmp4_clkgen), wina/winb (conversion windows), stba0..13 / stbb0..13 (decision strobes, one set",
         "* per slice: slice B may run N ticks after slice A), lata/latb, track signals (flag reset while tracking).",
         "* Per decision: P <= outp at stb, V <= 1 at stb, N = V AND NOT P (exactly one side switches).",
         "* Raw bits rX13..rX0 (rX13 = first decision) latched at latX.",
         "* " + "-" * 93,
         ".subckt r1_sar4_logic oap oan obp obn mclk wina winb trka0 trka1 trkb0 trkb1 lata latb %s %s "
         "clka clkab clkb clkbb %s %s %s %s rawa rawb vdd gnd"
         % (stb_list("a"), stb_list("b"), ctl_list("cpa"), ctl_list("cna"), ctl_list("cpb"), ctl_list("cnb"))]
    s.append(".model r1_adcb adc_bridge(in_low=0.6 in_high=0.6 rise_delay=20p fall_delay=20p)")
    s.append(".model r1_dacb dac_bridge(out_low=0 out_high=1.2 out_undef=0.6 input_load=1e-15 t_rise=80p t_fall=80p)")
    s.append(".model r1_dff d_dff(clk_delay=80p set_delay=80p reset_delay=80p ic=0 rise_delay=20p fall_delay=20p)")
    s.append(".model r1_and d_and(rise_delay=30p fall_delay=30p)")
    s.append(".model r1_nand d_nand(rise_delay=30p fall_delay=30p)")
    s.append(".model r1_or d_or(rise_delay=30p fall_delay=30p)")
    ins = ["vdd", "oap", "oan", "obp", "obn", "mclk", "wina", "winb", "trka0", "trka1", "trkb0", "trkb1", "lata", "latb"] + \
          ["stba%d" % k for k in range(ND)] + ["stbb%d" % k for k in range(ND)]
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
            st = "d_stb%s%d" % (ch, k)
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
    s.append(".ends r1_sar4_logic")
    return "\n".join(s) + "\n"


CORE_PORTS = ("sinp sinn cosp cosn isap isan isbp isbn trka0 trka1 trkb0 trkb1 clk30 wina winb lata latb %s %s "
              "rawa rawb topap topan topbp topbn vdd vref vrefl gnd")


def core(kind):
    name = {"full": "r1_adc4_core", "fast": "r1_adc4_core_fast", "fast_mc": "r1_adc4_core_fast_mc"}[kind]
    thn = {"full": "r1_th4", "fast": "r1_th4_fast", "fast_mc": "r1_th4_fast_mc"}[kind]
    s = ["",
         "* " + "-" * 93,
         "* %s: R1 ADC revision-4 core. Slice A: in0 = SIN, in1 = ISA. Slice B: in0 = COS, in1 = ISB." % name,
         "* Both slices convert in parallel (D18), one decision per clk30 tick; comparator clock from r1_cmp4_clkgen.",
         "* Comparator bias r1_cmp4_bias shared by both comparators. vrefl: LSB-array reference (tie to vref).",
         "* " + "-" * 93,
         (".subckt %s " % name) + CORE_PORTS % (stb_list("a"), stb_list("b"))]
    s.append("XCKG clk30 mclk mclkb vdd gnd r1_cmp4_clkgen")
    s.append("XTHA sinp sinn isap isan trka0 trka1 topap topan %s %s vdd vref vrefl gnd %s" % (ctl_list("cpa"), ctl_list("cna"), thn))
    s.append("XCBIAS vbp vdd gnd r1_cmp4_bias")
    s.append("XCMPA topap topan clka clkab oap oan vbp vdd gnd r1_cmp4")
    s.append("XTHB cosp cosn isbp isbn trkb0 trkb1 topbp topbn %s %s vdd vref vrefl gnd %s" % (ctl_list("cpb"), ctl_list("cnb"), thn))
    s.append("XCMPB topbp topbn clkb clkbb obp obn vbp vdd gnd r1_cmp4")
    s.append("XSAR oap oan obp obn mclk wina winb trka0 trka1 trkb0 trkb1 lata latb %s %s clka clkab clkb clkbb %s %s %s %s "
             "rawa rawb vdd gnd r1_sar4_logic" % (stb_list("a"), stb_list("b"), ctl_list("cpa"), ctl_list("cna"),
                                                   ctl_list("cpb"), ctl_list("cnb")))
    s.append(".ends %s" % name)
    return "\n".join(s) + "\n"


def refbuf():
    t = r3.refbuf().replace("r1_refbuf3", "r1_refbuf4")
    t = re.sub(r"(\.subckt r1_refbuf4 vbg vref vdda gnd) msf=\d+ mib=\d+ ndec=\d+ ncg=\d+",
               r"\1 msf=%d mib=%d ndec=%d ncg=%d mt=%d lt=%s" % (REF["msf"], REF["mib"], REF["ndec"], REF["ncg"], REF["mt"], REF["lt"]), t)
    # revision 4: error-amplifier tail as parameters (mt fingers of 2 um / lt). The amplifier integrates every
    # reference dip onto the gate capacitor (kick ~ gm_ea * Q / (gm_follower * Cg)); a smaller tail current lowers
    # gm_ea and the overshoot that follows each CDAC switch (README Revision 4, R2-4).
    t = t.replace("XMT  ntl nb gnd gnd sg13_hv_nmos w=2u l=1u ng=1 m=2", "XMT  ntl nb gnd gnd sg13_hv_nmos w=2u l={lt} ng=1 m={mt}")
    assert "l={lt} ng=1 m={mt}" in t
    t = t.replace("* r1_refbuf4 (revision 3, circuit of revision-2 r1_refbuf, new defaults)",
                  "* r1_refbuf4 (revision 4, circuit of revision-2 r1_refbuf unchanged, defaults of the chosen R2-4 option)")
    return t


def main():
    hdr = ("* r1_adc_r4.spice -- R1 12-bit SAR ADC revision 4, schematic-level library (generated by gen_r1_adc_r4.py; "
           "do not edit)\n* Requires: cornerMOSlv.lib, cornerMOShv.lib (r1_refbuf4), cornerCAP.lib, cornerRES.lib, "
           "XSPICE digital code models, PSP/R3 OSDI.\n")
    body = (r2.bootsw() + r3.cdac(False) + r3.cdac(True) + comparator() + clkgen() + th(False) + th(True)
            + th(True, mc=True) + sar_logic() + core("full") + core("fast") + core("fast_mc") + refbuf())
    with open(os.path.join(HERE, "r1_adc_r4.spice"), "w") as f:
        f.write(hdr + body)
    mm = re.sub(r"(sg13_(?:lv|hv)_[np]mos [^\n]*?m=(?:1|\{\w+\}))", r"\1 mm_ok={mmos}", body)
    with open(os.path.join(HERE, "r1_adc_r4_mm.spice"), "w") as f:
        f.write(hdr.replace("r1_adc_r4.spice --", "r1_adc_r4_mm.spice --") +
                "* Mismatch-capable copy: MOS instances carry mm_ok={mmos} (deck sets .param mmos).\n" + mm)
    print("wrote r1_adc_r4.spice, r1_adc_r4_mm.spice")


if __name__ == "__main__":
    main()

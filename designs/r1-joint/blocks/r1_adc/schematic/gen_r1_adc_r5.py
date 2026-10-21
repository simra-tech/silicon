#!/usr/bin/env python3
"""Generate the R1 ADC revision-5 schematic-level SPICE library (schematic/r1_adc_r5.spice, r1_adc_r5_mm.spice).

Revision 5 against revision 4 (gen_r1_adc_r4.py, kept unchanged; its cells are reused by import):
  * Decision 0 at the 0.6 V input common mode (coordinator decision 2026-10-21: the CM stays 0.6 V). The
    revision-4 comparator r1_cmp4 has a PMOS input pair; at ss / 125 C / 1.08 V the pair has no headroom at
    CM 0.6 V (VDD - CM - tail drop < |Vtp|) and decision 0 does not resolve. Revision 5 adds per slice a small
    complementary comparator r1_cmp5n (NMOS input pair, the r1_cmp4 double-tail mirrored: integration nodes
    precharged to VDD and discharged by the NMOS pair, PMOS latch tail) that makes decision 0 only. Decisions
    1..13 (CM 0.35 V .. 0.1 V, monotonic switching) stay on r1_cmp4. The NMOS comparator is clocked only while
    decision 0 is open (mclk AND win AND NOT v0), so it is in reset for the rest of the conversion.
  * r1_sar5_logic: r1_sar4_logic + decision 0 from the NMOS comparator and its clock gate.
  * Cores r1_adc5_core(_fast, _fast_mc): per-slice reference ports vrefa vrefb (MSB array C12..C8 and the
    rest) and vrefla vreflb (LSB array C7..C0 and the lsb-node reset). Tie them for one common reference.
  * Reference cells: r1_refbuf5h (= revision-4 r1_refbuf4h: no input divider, vref = vbg), r1_refbuf5 (option 3:
    r1_refbuf5h + a sub-reference follower on the same gate node for the LSB array, vrefl), r1_refps5 (option 2:
    per-slice decoupling capacitor, PMOS switch closed while the slice tracks, open during its conversion),
    r1_reffilt5 (input filter MIM on vbg).
Python 3.6 compatible.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gen_r1_adc_r2 as r2
import gen_r1_adc_r3 as r3
import gen_r1_adc_r4 as r4

NB, ND = r3.NB, r3.ND
# NMOS-input decision-0 comparator (revision 5); sizes chosen in the sim/r5 comparator runs (README Revision 5)
# variant n16rl of sim/r5/gen_cmp5_decks.py set c (sim/results/r5/cmp5n_c.json): noise 57.0 uV at ss / 125 C,
# 8/8 correct at CM 0.5 / 0.6 / 0.7 V at tt, ss, ff, decision time <= 15.5 ns (strobe 30.5 ns)
CMPN = dict(wi="16u", li="0.5u", ngi=4, wt="8u", wtc="4u", ltc="0.5u", wcap="30u", lcap="4u", wr="16u", wh="8u",
            wlp="4u", wlt="8u", ratio=20, rbw="1u", rbl="160u")
# reference defaults (revision 5)
REF = dict(msf=32, mib=160, ndec=6, ncg=1, mt=1, lt="8u")
REFL = dict(msfl=8, mibl=40, ndecl=1)
PS = dict(wsw="40u", nres=3)


def comparator_n():
    c = dict(CMPN)
    c["wtcd"] = "%gu" % (float(c["wtc"].rstrip("u")) / c["ratio"])
    return """
* ---------------------------------------------------------------------------------------------
* r1_cmp5n: NMOS-input double-tail dynamic comparator (revision 5, decision 0 at CM 0.6 V). The r1_cmp4
* topology mirrored: clk=1 (clkb=0) evaluate, the NMOS pair discharges the integration nodes dip/din from VDD
* (integration capacitors: NMOS gate capacitors {wcap}/{lcap}); clk=0 reset (PMOS precharge to VDD, outputs
* held low by XMH1/2). inp > inn -> dip falls first -> XMH1 releases outp first -> outp goes high.
* Reset state of the outputs: low (r1_cmp4: high).
* ---------------------------------------------------------------------------------------------
.subckt r1_cmp5n_s1 inp inn dip din clk vbn vdd gnd wi={wi} li={li} ngi={ngi} wt={wt} wtc={wtc} ltc={ltc}
XMT1 tail0 clk gnd gnd sg13_lv_nmos w={{wt}} l=0.13u ng=2 m=1
XMTC tail  vbn tail0 gnd sg13_lv_nmos w={{wtc}} l={{ltc}} ng=1 m=1
XM1  dip  inp  tail gnd sg13_lv_nmos w={{wi}} l={{li}} ng={{ngi}} m=1
XM2  din  inn  tail gnd sg13_lv_nmos w={{wi}} l={{li}} ng={{ngi}} m=1
.ends r1_cmp5n_s1

.subckt r1_cmp5n inp inn clk clkb outp outn vbn vdd gnd wi={wi} li={li} ngi={ngi} wt={wt} wtc={wtc} ltc={ltc} wcap={wcap} lcap={lcap} wr={wr} wh={wh} wlp={wlp} wlt={wlt}
XS1  inp inn dip din clk vbn vdd gnd r1_cmp5n_s1 wi={{wi}} li={{li}} ngi={{ngi}} wt={{wt}} wtc={{wtc}} ltc={{ltc}}
XCI1 gnd  dip  gnd  gnd sg13_lv_nmos w={{wcap}} l={{lcap}} ng=2 m=1
XCI2 gnd  din  gnd  gnd sg13_lv_nmos w={{wcap}} l={{lcap}} ng=2 m=1
XMR1 dip  clk  vdd  vdd sg13_lv_pmos w={{wr}} l=0.13u ng=1 m=1
XMR2 din  clk  vdd  vdd sg13_lv_pmos w={{wr}} l=0.13u ng=1 m=1
XMT2 lt   clkb vdd  vdd sg13_lv_pmos w={{wlt}} l=0.13u ng=1 m=1
XMP1 outp outn lt   vdd sg13_lv_pmos w={{wlp}} l=0.13u ng=1 m=1
XMP2 outn outp lt   vdd sg13_lv_pmos w={{wlp}} l=0.13u ng=1 m=1
XMN1 outp outn gnd  gnd sg13_lv_nmos w=1u l=0.13u ng=1 m=1
XMN2 outn outp gnd  gnd sg13_lv_nmos w=1u l=0.13u ng=1 m=1
XMH1 outp dip  gnd  gnd sg13_lv_nmos w={{wh}} l=0.13u ng=1 m=1
XMH2 outn din  gnd  gnd sg13_lv_nmos w={{wh}} l=0.13u ng=1 m=1
XBP1 outpb outp vdd vdd sg13_lv_pmos w=1u l=0.13u ng=1 m=1
XBN1 outpb outp gnd gnd sg13_lv_nmos w=0.5u l=0.13u ng=1 m=1
XBP2 outnb outn vdd vdd sg13_lv_pmos w=1u l=0.13u ng=1 m=1
XBN2 outnb outn gnd gnd sg13_lv_nmos w=0.5u l=0.13u ng=1 m=1
Cbp outpb gnd 3f
Cbn outnb gnd 3f
.ends r1_cmp5n

* r1_cmp5n_bias: tail bias of r1_cmp5n, I = (VDD - Vgs(XMBD)) / R, R = rppd {rbw} x {rbl} from VDD (mirror of
* r1_cmp4_bias). Diode XMBD w = wtc / {ratio}.
.subckt r1_cmp5n_bias vbn vdd gnd rbw={rbw} rbl={rbl}
XMBD vbn vbn gnd gnd sg13_lv_nmos w={wtcd} l={ltc} ng=1 m=1
XRB  vdd vbn gnd rppd w={{rbw}} l={{rbl}} m=1
.ends r1_cmp5n_bias
""".format(**c)


def sar_logic():
    t = r4.sar_logic().replace("r1_sar4_logic", "r1_sar5_logic")
    # ports: NMOS-comparator outputs (decision 0) and its clocks
    t = t.replace(".subckt r1_sar5_logic oap oan obp obn mclk",
                  ".subckt r1_sar5_logic oap oan obp obn oanp obnp mclk", 1)
    t = t.replace(" clka clkab clkb clkbb cpa12", " clka clkab clkb clkbb clkna clknab clknb clknbb cpa12", 1)
    t = t.replace('ABR [vdd oap oan obp obn mclk', 'ABR [vdd oap oan obp obn oanp obnp mclk', 1)
    t = t.replace('[d_vdd d_oap d_oan d_obp d_obn d_mclk', '[d_vdd d_oap d_oan d_obp d_obn d_oanp d_obnp d_mclk', 1)
    t = t.replace("AGB2 [d_mclk d_winb] g_clkbb r1_nand",
                  "AGB2 [d_mclk d_winb] g_clkbb r1_nand\n"
                  "* revision 5: NMOS comparator clock, open only while decision 0 is open (V flag of decision 0 = 0)\n"
                  "AGNA1 [d_mclk d_wina nfva0] g_clkna r1_and\n"
                  "AGNA2 [d_mclk d_wina nfva0] g_clknab r1_nand\n"
                  "AGNB1 [d_mclk d_winb nfvb0] g_clknb r1_and\n"
                  "AGNB2 [d_mclk d_winb nfvb0] g_clknbb r1_nand", 1)
    t = t.replace('outs_d_placeholder', '')
    t = t.replace("ADB [g_clka g_clkab g_clkb g_clkbb ", "ADB [g_clka g_clkab g_clkb g_clkbb g_clkna g_clknab g_clknb g_clknbb ", 1)
    t = t.replace("] [clka clkab clkb clkbb ", "] [clka clkab clkb clkbb clkna clknab clknb clknbb ", 1)
    # decision 0 of each slice from the NMOS comparator
    t = t.replace("AFPa0 d_oap d_stba0", "AFPa0 d_oanp d_stba0", 1)
    t = t.replace("AFPb0 d_obp d_stbb0", "AFPb0 d_obnp d_stbb0", 1)
    for s in ("AFPa0 d_oanp", "AFPb0 d_obnp", "g_clkna r1_and", "clkna clknab clknb clknbb cpa12", "d_oanp d_obnp d_mclk",
              "ADB [g_clka g_clkab g_clkb g_clkbb g_clkna"):
        assert s in t, s
    t = t.replace("* r1_sar5_logic: XSPICE SAR registers, 14 decisions,",
                  "* r1_sar5_logic (revision 5: decision 0 from the NMOS comparator r1_cmp5n, clocks clkn*): XSPICE SAR registers, 14 decisions,")
    return t


def core_ports():
    return ("sinp sinn cosp cosn isap isan isbp isbn trka0 trka1 trkb0 trkb1 clk30 wina winb lata latb %s %s "
            "rawa rawb topap topan topbp topbn vdd vrefa vrefb vrefla vreflb gnd") % (r4.stb_list("a"), r4.stb_list("b"))


def core(kind):
    name = {"full": "r1_adc5_core", "fast": "r1_adc5_core_fast", "fast_mc": "r1_adc5_core_fast_mc"}[kind]
    thn = {"full": "r1_th4", "fast": "r1_th4_fast", "fast_mc": "r1_th4_fast_mc"}[kind]
    s = ["",
         "* " + "-" * 93,
         "* %s: R1 ADC revision-5 core. Slice A: in0 = SIN, in1 = ISA. Slice B: in0 = COS, in1 = ISB." % name,
         "* Both slices convert in parallel (D18), one decision per clk30 tick. Decision 0: NMOS-input r1_cmp5n;",
         "* decisions 1..13: PMOS-input r1_cmp4. Per-slice reference ports: vrefX (C12..C8 and C7..C0 drivers of the",
         "* revision-4 split: MSB array) and vreflX (LSB array C7..C0 and lsb-node reset). Tie for one reference.",
         "* " + "-" * 93,
         (".subckt %s " % name) + core_ports()]
    s.append("XCKG clk30 mclk mclkb vdd gnd r1_cmp4_clkgen")
    s.append("XTHA sinp sinn isap isan trka0 trka1 topap topan %s %s vdd vrefa vrefla gnd %s" % (r4.ctl_list("cpa"), r4.ctl_list("cna"), thn))
    s.append("XCBIAS vbp vdd gnd r1_cmp4_bias")
    s.append("XCBIASN vbn vdd gnd r1_cmp5n_bias")
    s.append("XCMPA topap topan clka clkab oap oan vbp vdd gnd r1_cmp4")
    s.append("XCMPNA topap topan clkna clknab oanp oann vbn vdd gnd r1_cmp5n")
    s.append("XTHB cosp cosn isbp isbn trkb0 trkb1 topbp topbn %s %s vdd vrefb vreflb gnd %s" % (r4.ctl_list("cpb"), r4.ctl_list("cnb"), thn))
    s.append("XCMPB topbp topbn clkb clkbb obp obn vbp vdd gnd r1_cmp4")
    s.append("XCMPNB topbp topbn clknb clknbb obnp obnn vbn vdd gnd r1_cmp5n")
    s.append("XSAR oap oan obp obn oanp obnp mclk wina winb trka0 trka1 trkb0 trkb1 lata latb %s %s clka clkab clkb clkbb "
             "clkna clknab clknb clknbb %s %s %s %s rawa rawb vdd gnd r1_sar5_logic"
             % (r4.stb_list("a"), r4.stb_list("b"), r4.ctl_list("cpa"), r4.ctl_list("cna"), r4.ctl_list("cpb"), r4.ctl_list("cnb")))
    s.append(".ends %s" % name)
    return "\n".join(s) + "\n"


def refcells():
    """r1_refbuf5h (= r1_refbuf4h), r1_refbuf5 (option 3 sub-reference), r1_refps5 (option 2), r1_reffilt5."""
    t = r4.refbuf()
    t = "\n".join(l for l in t.split("\n") if not l.startswith("XRD"))
    t = t.replace(".subckt r1_refbuf4 vbg vref vdda gnd", ".subckt r1_refbuf5h vbg vref vdda gnd")
    t = t.replace(".ends r1_refbuf4", ".ends r1_refbuf5h").replace("XM1  na  vtap ntl", "XM1  na  vbg ntl")
    assert "vtap" not in t.split(".subckt r1_refbuf5h")[1]
    i = t.index(".subckt r1_refbuf5h")
    body5h = t[i:]
    hdr5h = ("\n* r1_refbuf5h: revision-4 r1_refbuf4h (r1_refbuf4 without the input divider; error-amplifier gate on vbg,\n"
             "* vref = vbg). Accepted baseline (coordinator 2026-10-21). Same devices as r1_refbuf4 otherwise.\n")
    # bias pin (coordinator 2026-10-21, r1_bias track): the 5 uA source moves out of the cell. r1_bias sources a PTAT
    # current (5.07 uA at tt, 3.5-7.7 uA over PVT) into the existing diode XMB0 on node nb, now a port. Pure port
    # change: the device list is unchanged except that the internal Ibias is removed. r1_refbuf5h (baseline, rejected)
    # keeps its internal source.
    b5 = body5h.replace(".subckt r1_refbuf5h vbg vref vdda gnd", ".subckt r1_refbuf5 vbg vref vrefl nb vdda gnd")
    assert "Ibias vdda nb 5u\n" in b5
    b5 = b5.replace("Ibias vdda nb 5u\n", "* nb: bias input, current sourced into the diode XMB0 by r1_bias (ib_adc_ref)\n")
    b5 = b5.replace(".ends r1_refbuf5h",
                    "* option 3: LSB-array sub-reference, a second source follower on the same gate node ng (no second\n"
                    "* loop: vrefl = ng - Vgs at the same current density as the main follower, msfl/mibl = msf/mib)\n"
                    "XMSFL vdda ng vrefl gnd sg13_hv_nmos w=10u l=0.45u ng=4 m={msfl}\n"
                    "XMIBL vrefl nb gnd gnd sg13_hv_nmos w=2u l=1u ng=1 m={mibl}\n"
                    "XCDL vrefl gnd cap_cmim w=70u l=70u m={ndecl}\n"
                    ".ends r1_refbuf5")
    b5 = re.sub(r"(\.subckt r1_refbuf5 vbg vref vrefl nb vdda gnd [^\n]*)", r"\1 msfl=%d mibl=%d ndecl=%d" % (REFL["msfl"], REFL["mibl"], REFL["ndecl"]), b5)
    hdr5 = ("\n* r1_refbuf5 (R2-4 option 3): r1_refbuf5h with a separate LSB-array reference vrefl from the same buffer.\n"
            "* The LSB array (C7..C0, lsb-node reset) draws its switching charge from vrefl and its own decoupling;\n"
            "* the main follower and the error amplifier see only the MSB array (C12..C8).\n"
            "* Pin nb (T2 2026-10-21): bias current input (r1_bias ib_adc_ref, 5.07 uA at tt) into the diode XMB0.\n")
    ps = ("\n* r1_refps5 (R2-4 option 2): per-slice decoupling capacitor. PMOS switch from the buffer output vin to the slice\n"
          "* reference vout, closed while the slice tracks (trk0 OR trk1), open during its conversion; Cres = nres MIM\n"
          "* cells of 70 x 70 um (7.36 pF each) on vout. Gate = NOR(trk0, trk1) (1.2 V domain).\n"
          ".subckt r1_refps5 vin vout trk0 trk1 vdd gnd wsw=%s nres=%d\n"
          "XNP1 nx trk0 vdd vdd sg13_lv_pmos w=2u l=0.13u ng=1 m=1\n"
          "XNP2 g trk1 nx vdd sg13_lv_pmos w=2u l=0.13u ng=1 m=1\n"
          "XNN1 g trk0 gnd gnd sg13_lv_nmos w=1u l=0.13u ng=1 m=1\n"
          "XNN2 g trk1 gnd gnd sg13_lv_nmos w=1u l=0.13u ng=1 m=1\n"
          "XSW vout g vin vdd sg13_lv_pmos w={wsw} l=0.13u ng=8 m=1\n"
          "XCR vout gnd cap_cmim w=70u l=70u m={nres}\n"
          ".ends r1_refps5\n" % (PS["wsw"], PS["nres"]))
    filt = ("\n* r1_reffilt5: reference input filter, MIM w x w from vbg to ground (with the r1_bgr source resistance).\n"
            ".subckt r1_reffilt5 vbg gnd w=82u\n"
            "XCF vbg gnd cap_cmim w={w} l={w} m=1\n"
            ".ends r1_reffilt5\n")
    return hdr5h + body5h + "\n" + hdr5 + b5 + "\n" + ps + filt


def main():
    hdr = ("* r1_adc_r5.spice -- R1 12-bit SAR ADC revision 5, schematic-level library (generated by gen_r1_adc_r5.py; "
           "do not edit)\n* Requires: cornerMOSlv.lib, cornerMOShv.lib (reference cells), cornerCAP.lib, cornerRES.lib, "
           "XSPICE digital code models, PSP/R3 OSDI.\n"
           "* Unchanged revision-4 cells (same names): r1_bootsw, r1_offsw, r1_drv(_sw), r1_cdac3_side(_mc), r1_cmp4(_s1),\n"
           "* r1_cmp4_bias, r1_cmp4_clkgen, r1_th4, r1_th4_fast, r1_th4_fast_mc.\n")
    body = (r2.bootsw() + r3.cdac(False) + r3.cdac(True) + r4.comparator() + comparator_n() + r4.clkgen() + r4.th(False)
            + r4.th(True) + r4.th(True, mc=True) + sar_logic() + core("full") + core("fast") + core("fast_mc") + refcells())
    with open(os.path.join(HERE, "r1_adc_r5.spice"), "w") as f:
        f.write(hdr + body)
    mm = re.sub(r"(sg13_(?:lv|hv)_[np]mos [^\n]*?m=(?:1|\{\w+\}))", r"\1 mm_ok={mmos}", body)
    with open(os.path.join(HERE, "r1_adc_r5_mm.spice"), "w") as f:
        f.write(hdr.replace("r1_adc_r5.spice --", "r1_adc_r5_mm.spice --") +
                "* Mismatch-capable copy: MOS instances carry mm_ok={mmos} (deck sets .param mmos).\n" + mm)
    print("wrote r1_adc_r5.spice, r1_adc_r5_mm.spice")


if __name__ == "__main__":
    main()

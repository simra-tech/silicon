#!/usr/bin/env python3
"""Generate the `stb` suite decks of r1_isense (T4 follow-up c, 2026-10-21):

  tb_isense_stbpre.cir   AZ sequence on the channel alone; prints HOLDVALS (hold-cap voltages after the auto-zero)
  tb_isense_stb.cir      loop gain, NORMAL state (az = azh = 0): hold caps tied at DC to the pre-run values through 1 GH
                         (open for AC), five breaks (see LOOPS), three shunt levels (0, +100 mV, -20 mV)
  tb_isense_stbaz.cir    loop gain, AZ CLOSED state (az = azh = 1): output breaks and the AZ servo break at the aux-pair gates
  tb_isense_stbstep.cir  shunt step 0 -> 100 mV, 10 ns edge, real netlist, same load fixture

Method: Tian double injection, Wiedmann form, as r1_afe (r1_afe/sim/tb_afe_stb.cir, validated on a toy network in
r1_afe/sim/tb_stb_toy.cir, relative error 4.7e-8):  T = -1/(1-1/(2*(i1*v2-v1*i2)+v1+i2)),  v = driver-side node
voltage, i = probe-source current, run 1 voltage injection, run 2 current injection; DM/CM from (p -/+ n)/2.
The probes sit in a deck-local copy of r1_isense_ch (r1_isense_ch_stb) generated from the netlist of record, which is
included unchanged; no edit of the record.

Breaks (driver side | load side), all other loops closed:
  1 dm_out / 2 cm_out  OTA outputs OUTP/OUTN: output devices XMOx/XMLx + Miller Cc (incl. Rz, stage-1 outputs, folding,
                       aux pair, input pair) | RF arms, CMFB sense, pins (2 pF + comparator gates)
                       dm_out = main differential loop; cm_out = CM loop incl. the CMFB path and the CM path through
                       the input pair and the resistor network (the Nyquist-valid CM loop)
  3 cmfb               CMFB path alone (vcms -> gate of XMF1), other loops closed (informational, not a valid Nyquist
                       break when the input-pair CM loop is also > 1, as in r1_afe revision C finding 2)
  4 dm_in / 5 cm_in    input-pair gates sa/sb (resistor network | gates), cross-check of 1 and 2 (normal state)
  6 dm_aux / 7 cm_aux  aux-pair gates (hold node | gates), the AZ servo (AZ closed state)
Load fixture = the joint path fixture of r1_safe (tb_safe_joint3.cir): sense outputs drive the thick-PMOS gates of two
real r1_safe_cmp (OC and NEG of channel a, code THR = 44 on the string, path-fixture muxes) and 2 pF per output.
"""
import os, re, sys
here = os.path.dirname(os.path.abspath(__file__))
net = open(os.path.join(here, "..", "schematic", "r1_isense.spice")).read()
a = net.index(".subckt r1_isense_ch "); b = net.index(".ends r1_isense_ch", a) + len(".ends r1_isense_ch")
sub0 = net[a:b]

THR = int(os.environ.get("R1_THR", "44"))
def npn(c, k=32):
    d = k - 32
    return min(252, max(0, 4 * c - ((-d) // 2))), min(252, max(0, 4 * (63 - c) - (d // 2)))

def edit(s, old, new):
    assert s.count(old) == 1, (old, s.count(old))
    return s.replace(old, new)

def stb_sub(hold):
    s = sub0.replace(".subckt r1_isense_ch isp isn outp outn vref vcm ibias az_lv azh_lv vdda vdd vss",
                     ".subckt r1_isense_ch_stb isp isn outp outn vref vcm ibias az_lv azh_lv vdda vdd vss")
    assert "r1_isense_ch_stb" in s
    for o, n in (("XMOA outp x1a", "XMOA outpi x1a"), ("XMOB outn x1b", "XMOB outni x1b"),
                 ("XMLA outp vbl", "XMLA outpi vbl"), ("XMLB outn vbl", "XMLB outni vbl"),
                 ("XCCA cza outp ", "XCCA cza outpi "), ("XCCB czb outn ", "XCCB czb outni "),
                 ("XM1 f1 sa tail", "XM1 f1 sai tail"), ("XM2 f2 sb tail", "XM2 f2 sbi tail"),
                 ("XMF1 vcmfb vcms ctail", "XMF1 vcmfb vcmsy ctail"),
                 ("XA1 f1 h1 atail", "XA1 f1 h1g atail"), ("XA2 f2 h2 atail", "XA2 f2 h2g atail")):
        s = edit(s, o, n)
    P = ["* ---- loop-gain probes (test only; Tian double injection). Driver-side node carries the + terminal and the current injection",
         "Vpop outpi outp dc 0 ac {vo_p}", "Vpon outni outn dc 0 ac {vo_n}", "Ipop 0 outpi dc 0 ac {io_p}", "Ipon 0 outni dc 0 ac {io_n}",
         "Vpsa sa sai dc 0 ac {vi_p}", "Vpsb sb sbi dc 0 ac {vi_n}", "Ipsa 0 sa dc 0 ac {ii_p}", "Ipsb 0 sb dc 0 ac {ii_n}",
         "Vpc vcms vcmsy dc 0 ac {vc}", "Ipc 0 vcms dc 0 ac {ic}",
         "Vpq1 h1 h1g dc 0 ac {va_p}", "Vpq2 h2 h2g dc 0 ac {va_n}", "Ipq1 0 h1 dc 0 ac {ja_p}", "Ipq2 0 h2 dc 0 ac {ja_n}"]
    if hold:
        P += ["* hold caps tied at DC to the post-AZ voltages (1 GH is open for AC): normal state, switches off",
              "Lhd1 h1 hd1 1G", "Vhd1 hd1 0 dc @@VH1@@", "Lhd2 h2 hd2 1G", "Vhd2 hd2 0 dc @@VH2@@"]
    return s.replace(".ends r1_isense_ch", "\n".join(P) + "\n.ends r1_isense_ch_stb")

LIB = """.lib /foss/pdks/ihp-sg13g2/libs.tech/ngspice/models/cornerMOSlv.lib @@MOS@@
.lib /foss/pdks/ihp-sg13g2/libs.tech/ngspice/models/cornerMOShv.lib @@MOS@@
.lib /foss/pdks/ihp-sg13g2/libs.tech/ngspice/models/cornerRES.lib @@RES@@
.lib /foss/pdks/ihp-sg13g2/libs.tech/ngspice/models/cornerCAP.lib @@CAP@@
.temp @@TEMP@@
.include /work/designs/r1-joint/blocks/r1_isense/schematic/r1_isense.spice"""
SUP = """Vdda vdda 0 dc @@VDDA@@
Vdd vdd 0 dc @@VDD@@
* IDEAL REFERENCE SOURCES (this step only), as the joint path fixture of r1_safe
Vref vref 0 dc 1.05
Vcm vcm 0 dc 0.6
Iba vdda iba dc {5u*(@@TEMP@@+273.15)/300.15}"""

def fixture():
    """string + path-fixture muxes + OC and NEG comparators of channel a (as gen_tb_safe_joint3.py) + output loads."""
    L = []; w = L.append
    w("* ---- r1_safe load of channel a: string, conducting mux paths (path fixture), OC and NEG comparators, code %d, k = 32" % THR)
    w("Ioa vdda ibias_oa dc {5u*(@@TEMP@@+273.15)/300.15}\nIna vdda ibias_na dc {5u*(@@TEMP@@+273.15)/300.15}")
    w("Cba ibias_oa 0 100f\nCbb ibias_na 0 100f")
    w("XSTR vref %s 0 r1_safe_string" % " ".join("t%d" % k for k in range(253)))
    def path(n, out, pre):
        cur = "t%d" % n
        for lev in range(8):
            nxt = out if lev == 7 else "%s_l%d" % (pre, lev)
            sib = "t%d" % min(252, n ^ (1 << lev))
            w("X%s_on%d %s vdda %s 0 sg13_hv_nmos w=0.5u l=0.45u ng=1 m=1 mm_ok=1" % (pre, lev, cur, nxt))
            w("X%s_off%d %s 0 %s 0 sg13_hv_nmos w=0.5u l=0.45u ng=1 m=1 mm_ok=1" % (pre, lev, sib, nxt))
            cur = nxt
    for cm, c, inp, inn, out in (("oa", THR, "outa_p", "outa_n", "oc_a"), ("na", 63 - THR, "outa_n", "outa_p", "neg_a")):
        nP, nN = npn(c)
        w("* %s: cell code %d: REFP = T%d, REFN = T%d" % (cm, c, nP, nN))
        path(nP, "refp_" + cm, "mp" + cm); path(nN, "refn_" + cm, "mn" + cm)
        w("X%s %s %s refp_%s refn_%s %s ibias_%s vdda vdd 0 r1_safe_cmp" % (cm.upper(), inp, inn, cm, cm, out, cm))
    w("CL1 oc_a 0 10f\nCL2 neg_a 0 10f")
    w("* ADC input load per output: series @@RL@@ ohm + @@CL@@ to ground + @@CW@@ wiring (joint fixture: 0.001 ohm, 2p, 0)")
    w("Rld1 outa_p ldp @@RL@@\nCld1 ldp 0 @@CL@@\nRld2 outa_n ldn @@RL@@\nCld2 ldn 0 @@CL@@\nCw1 outa_p 0 @@CW@@\nCw2 outa_n 0 @@CW@@")
    return "\n".join(L)

SAFE_INC = ".include /work/designs/r1-joint/blocks/r1_safe/schematic/r1_safe.spice"

def stb_deck(az, loops, name, title):
    hold = not az
    azv = "@@VDD@@" if az else "0"
    lev = "0 0.1 -0.02" if not az else "0"
    H = ["* " + title, "* " + __doc__.strip().replace("\n", "\n* "),
         LIB, SAFE_INC, ".option gmin=1e-12", SUP,
         "Vaz az 0 dc %s\nVazh azh 0 dc %s" % (azv, azv),
         "Vnn isn 0 dc 0\nVin isp isn dc 0",
         "* loop-gain probe parameters (AC magnitudes; all zero except the break under test)",
         ".param vo_p=0 vo_n=0 io_p=0 io_n=0 vi_p=0 vi_n=0 ii_p=0 ii_n=0 vc=0 ic=0 va_p=0 va_n=0 ja_p=0 ja_n=0",
         stb_sub(hold),
         "XA isp isn outa_p outa_n vref vcm iba az azh vdda vdd 0 r1_isense_ch_stb", fixture()]
    # per loop: (voltage-injection params, current-injection params, v node, i source, DM/CM combination)
    LP = {
        1: (("vo_p", 1, "vo_n", -1), ("io_p", 1, "io_n", -1), "xa.outpi", "xa.outni", "v.xa.vpop", "v.xa.vpon", "-"),
        2: (("vo_p", 1, "vo_n", 1), ("io_p", 1, "io_n", 1), "xa.outpi", "xa.outni", "v.xa.vpop", "v.xa.vpon", "+"),
        3: (("vc", 1), ("ic", 1), "xa.vcms", None, "v.xa.vpc", None, "1"),
        4: (("vi_p", 1, "vi_n", -1), ("ii_p", 1, "ii_n", -1), "xa.sa", "xa.sb", "v.xa.vpsa", "v.xa.vpsb", "-"),
        5: (("vi_p", 1, "vi_n", 1), ("ii_p", 1, "ii_n", 1), "xa.sa", "xa.sb", "v.xa.vpsa", "v.xa.vpsb", "+"),
        6: (("va_p", 1, "va_n", -1), ("ja_p", 1, "ja_n", -1), "xa.h1", "xa.h2", "v.xa.vpq1", "v.xa.vpq2", "-"),
        7: (("va_p", 1, "va_n", 1), ("ja_p", 1, "ja_n", 1), "xa.h1", "xa.h2", "v.xa.vpq1", "v.xa.vpq2", "+"),
    }
    C = [".control", "let li = 0", "foreach vs %s" % lev, "  foreach lp %s" % " ".join(str(x) for x in loops)]
    def setp(kind):
        out = []
        for lp, d in LP.items():
            pr = d[0] if kind == 0 else d[1]
            out.append("    if $lp = %d" % lp)
            for i in range(0, len(pr), 2):
                out.append("      alterparam %s=%g" % (pr[i], pr[i + 1]))
            out.append("    end")
        return out
    zero = ["    alterparam %s=0" % p for p in "vo_p vo_n io_p io_n vi_p vi_n ii_p ii_n vc ic va_p va_n ja_p ja_n".split()]
    C += setp(0)
    C += ["    reset", "    alter vin dc = $vs", "    ac dec 20 100 1g"]
    C += zero + setp(1)
    C += ["    reset", "    alter vin dc = $vs", "    ac dec 20 100 1g"]
    C += zero
    for lp, d in LP.items():
        v, n, iv, in_, comb = d[2], d[3], d[4], d[5], d[6]
        C.append("    if $lp = %d" % lp)
        for k in ("1", "2"):
            if n is None:
                C.append("      let v%s = ac%s.v(%s)" % (k, k, v)); C.append("      let i%s = ac%s.i(%s)" % (k, k, iv))
            else:
                C.append("      let v%s = (ac%s.v(%s)%sac%s.v(%s))/2" % (k, k, v, comb, k, n))
                C.append("      let i%s = (ac%s.i(%s)%sac%s.i(%s))/2" % (k, k, iv, comb, k, in_))
        C.append("    end")
    C += ["    let tl = -1/(1-1/(2*(i1*v2-v1*i2)+v1+i2))", "    let tdb = db(tl)", "    let tph = 180/pi*cph(tl)",
          "    let fid = 10*li + $lp", "    wrdata @@OUT@@_t$&fid tdb tph", '    echo "STBFILE level=$vs loop=$lp"', "    destroy all",
          "  end", "  let li = li + 1", "end", ".endc", ".end"]
    return "\n".join(H + C) + "\n"

PRE = """* r1_isense stb suite, pre-run: auto-zero sequence on the channel alone (zero shunt current), hold-cap voltages after AZ.
%s
.option gmin=1e-12 method=gear reltol=1e-4 abstol=1e-12 vntol=1e-7
%s
Vaz az 0 pwl(0 @@VDD@@ 2.05u @@VDD@@ 2.051u 0)
Vazh azh 0 pwl(0 @@VDD@@ 2.0u @@VDD@@ 2.001u 0)
Vnn isn 0 dc 0
Vin isp isn dc 0
XDUT isp isn outp outn vref vcm iba az azh vdda vdd 0 r1_isense_ch
CLP outp 0 2p
CLN outn 0 2p
.control
tran 0.5n 3.6u 0 0.5n
meas tran vh1 find v(xdut.h1) at=3.5u
meas tran vh2 find v(xdut.h2) at=3.5u
meas tran vop find v(outp) at=3.5u
meas tran von find v(outn) at=3.5u
echo "HOLDVALS VH1=$&vh1 VH2=$&vh2 VOP=$&vop VON=$&von"
.endc
.end
""" % (LIB, SUP)

STEP = """* r1_isense stb suite, shunt step 0 -> 100 mV (10 ns edge) at 3.0 us after the auto-zero, real netlist of record, joint load fixture
* (two real r1_safe_cmp at code %d on the string, path-fixture muxes, @@CL@@ per output).
%s
%s
.option gmin=1e-12 method=gear reltol=1e-4 abstol=1e-12 vntol=1e-7
%s
Vaz az 0 pwl(0 @@VDD@@ 2.05u @@VDD@@ 2.051u 0)
Vazh azh 0 pwl(0 @@VDD@@ 2.0u @@VDD@@ 2.001u 0)
Vnn isn 0 dc 0
Vin isp isn pwl(0 0 3u 0 3.01u 0.1 7u 0.1)
XA isp isn outa_p outa_n vref vcm iba az azh vdda vdd 0 r1_isense_ch
%s
.control
set wr_singlescale
set wr_vecnames
tran 0.5n 7u 0 0.5n
wrdata @@OUT@@_step.txt v(outa_p) v(outa_n) v(isp) v(oc_a) v(neg_a)
.endc
.end
""" % (THR, LIB, SAFE_INC, SUP, fixture())

CMSTEP = STEP.replace("step 0 -> 100 mV (10 ns edge) at 3.0 us after the auto-zero", "common-mode reference step: VCM 0.60 -> 0.62 V (10 ns edge) at 3.5 us after the auto-zero (CM loop cross-check, normal state)").replace(
    "Vin isp isn pwl(0 0 3u 0 3.01u 0.1 7u 0.1)", "Vin isp isn dc 0").replace("tran 0.5n 7u 0 0.5n", "tran 0.5n 4.6u 0 0.5n").replace(
    "Vcm vcm 0 dc 0.6", "Vcm vcm 0 pwl(0 0.6 3.5u 0.6 3.51u 0.62)").replace("_step.txt", "_cmstep.txt")
assert "3.51u 0.62" in CMSTEP and "_cmstep.txt" in CMSTEP, (("3.51u 0.62" in CMSTEP), ("_cmstep.txt" in CMSTEP))

TAG = os.environ.get("R1_TAG", "")      # e.g. R1_TAG=c14 R1_THR=14 -> tb_isense_stbc14.cir (comparators at the calibration point)
if __name__ == "__main__":
    if not TAG:
        open(os.path.join(here, "tb_isense_stbpre.cir"), "w").write(PRE)
    open(os.path.join(here, "tb_isense_stb%s.cir" % TAG), "w").write(
        stb_deck(False, [1, 2, 3, 4, 5], "stb", "r1_isense loop gain, NORMAL state (az = azh = 0), shunt levels 0 / +100 mV / -20 mV"))
    if not TAG:
      open(os.path.join(here, "tb_isense_stbaz.cir"), "w").write(
        stb_deck(True, [1, 2, 3, 6, 7], "stbaz", "r1_isense loop gain, AZ CLOSED state (az = azh = 1), zero shunt current"))
    if not TAG:
        open(os.path.join(here, "tb_isense_stbstep.cir"), "w").write(STEP)
        open(os.path.join(here, "tb_isense_stbcm.cir"), "w").write(CMSTEP)
    print("ok")

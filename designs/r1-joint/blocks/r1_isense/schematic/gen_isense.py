#!/usr/bin/env python3
"""Write r1_isense.spice from r1_isense.spice.tmpl with the frozen device sizes below.
Usage: python3 gen_isense.py [KEY=VALUE ...] [--out FILE]   (overrides are for sizing studies only)."""
import sys, os
SIZES = {
    "W1": "40",     # input pair width (um), L = 1 um, ng = 8
    "WA": "8",      # auxiliary (AZ) pair width (um), L = 4 um
    "WO": "16",     # stage-2 thick NMOS width (um), L = 0.5 um
    "WL": "40",     # stage-2 thin PMOS load width (um)
    "LL": "0.25",   # stage-2 thin PMOS load and bias-diode length (um)
    "RZL": "3.6",   # nulling resistor length (um), rppd w = 1 um
    "CCW": "12",    # Miller cap side (um), cmim square
    "WSP": "10",    # pedestal switch width (um), thick NMOS L = 0.45 um
    "WSF": "40",    # RF-arm series switch width (um), thick NMOS L = 0.45 um
    # revision 2 parameters. Defaults = REVISION 2 (2026-10-21). Revision 1 (r1_isense_rev1.spice, sha256 5db34e0a8f7c...) is
    # reproduced, apart from comment lines, by:  gen_isense.py BFC=0 FDC=0 RDG=0 RH=0 TP=0 MS=7 MCS=2 --out <file>
    "MCS": "1",     # CMFB sink multiplier per side (units w8/l2)
    "MS": "8",      # fixed folding sink multiplier per side (5 uA units w8/l2)
    "MFD": "3",     # CMFB diode multiplier (XMFD, XMFE)
    "MTC": "6",     # CMFB tail multiplier (5 uA PMOS units)
    "CMW": "8",     # CM-sense bypass cap side (um), cmim square
    "CXW": "0",     # cross-coupled (CM-only) Miller cap side (um), cza -> outn and czb -> outp; 0 = none
    "BFC": "1",     # 1 = wide-swing reference for the fixed folding sinks (cascode XMBFC, gate vbnc): Vds(XMBF) = fold node
    "FDC": "1",     # 1 = cascodes XMFDC/XMFEC (gate vbnc) on the CMFB diodes: Vds(XMFD) = fold node
    "RDG": "50",     # CMFB pair source degeneration, rppd w = 1 um, length in um (about 0.26 kOhm/um); 0 = none
    "REFX": "1",    # n: XMB6 and XMBF (reference of the fixed folding sinks) as n x n series-parallel composites of their unit (mismatch / n)
    "RH": "50",      # series resistor between the stage-1 output and each hold switch, rhigh w = 1 um, kOhm; 0 = none
    "TP": "2",      # 1 = two-path CMFB: slow integrating path (pair XMG1/XMG2, mirror, C_int at vint, XMI steals from vcmfb) for DC accuracy
    #      2 = two-path CMFB, slow path as a reference trim: degenerated OTA (XMG1 vcms / XMG2 vcm, RTG source resistors,
    #          mirror load) integrates on XCI at node vint, and vint replaces vcm at the gate of XMF2 (fast pair reference)
    "RTG": "0",   #   TP=2: slow-pair source degeneration, rhigh w = 1 um, kOhm per side
    "TPT": "1",     #   slow-path tail, 5 uA PMOS units
    "TCR": "vcm",   #   TP=2: bottom node of the integrating cap XCI (vss, or vcm: vint then follows a vcm step at once)
    "TGW": "0.5",     #   TP=2: slow-path tail width (um, l = 2 um; 4 um = one 5 uA unit, 1 um = 1.25 uA)
    "TPW": "1", "TPL": "24",      # slow pair W/L (um)
    "TMW": "8", "TML": "32",      # slow-path NMOS mirror W/L (um)
    "TIW": "1", "TIL": "10",     # XMI W/L (um)
    "TPC": "36",    #   C_int side (um), cmim square
    "LAG": "0",     # CMFB lag network at the sink gates "R1k,R2k,Cside": rhigh R1 series, rhigh R2 + cmim C shunt; 0 = none
}
def composite(name, d, g, sr, b, model, w, l, n):
    """n parallel strings of n series unit devices (same unit W/L, n*n units of area: the drain current equals one unit)"""
    if n == 1:
        return "%s %s %s %s %s %s w=%su l=%su ng=1 m=1 mm_ok=1" % (name, d, g, sr, b, model, w, l)
    out = ["* %s: %d x %d series-parallel composite of the w=%s/l=%s unit (rev 2, mismatch / %d)" % (name, n, n, w, l, n)]
    for k in range(n):
        nodes = [sr] + ["%s_%d_%d" % (name.lower(), k, j) for j in range(1, n)] + [d]
        for j in range(n):
            out.append("%s_%d_%d %s %s %s %s %s w=%su l=%su ng=1 m=1 mm_ok=1" % (name, k, j, nodes[j + 1], g, nodes[j], b, model, w, l))
    return "\n".join(out)

def expand(S):
    """optional netlist lines (revision 2)"""
    L = {}
    n = int(S["REFX"])
    L["B6REF"] = composite("XMB6", "vbf", "vbp", "vdda", "vdda", "sg13_hv_pmos", "4", "2", n)
    if S["BFC"] == "1":
        wc = 10.0   # 5 uA at the XMN1 density (20 uA / 40 um)
        L["BFREF"] = ("* wide-swing reference (rev 2): XMBF drain at the fold-node voltage through XMBFC (same current density as XMN1)\n"
                      + composite("XMBF", "vbfs", "vbf", "vss", "vss", "sg13_hv_nmos", "8", "2", n) + "\n"
                      "XMBFC vbf vbnc vbfs vss sg13_hv_nmos w=%gu l=2u ng=1 m=1 mm_ok=1" % wc)
    else:
        L["BFREF"] = composite("XMBF", "vbf", "vbf", "vss", "vss", "sg13_hv_nmos", "8", "2", n)
    m = S["MFD"]
    if S["FDC"] == "1":
        wc = 40.0 * (float(S["MTC"]) * 5 / 2) / 20.0   # current per diode MTC*5/2 uA at the XMN1 density (20 uA / 40 um)
        L["CMFBD"] = ("* CMFB diodes with cascodes (rev 2): Vds(XMFD/XMFE) at the fold-node voltage, as the CMFB sinks\n"
                      "XMFD vcmfs vcmfb vss vss sg13_hv_nmos w=8u l=2u ng=1 m=%s mm_ok=1\n"
                      "XMFDC vcmfb vbnc vcmfs vss sg13_hv_nmos w=%gu l=2u ng=1 m=1 mm_ok=1\n"
                      "XMFE vcmds vcmd vss vss sg13_hv_nmos w=8u l=2u ng=1 m=%s mm_ok=1\n"
                      "XMFEC vcmd vbnc vcmds vss sg13_hv_nmos w=%gu l=2u ng=1 m=1 mm_ok=1" % (m, wc, m, wc))
    else:
        L["CMFBD"] = ("XMFD vcmfb vcmfb vss vss sg13_hv_nmos w=8u l=2u ng=1 m=%s mm_ok=1\n"
                      "XMFE vcmd vcmd vss vss sg13_hv_nmos w=8u l=2u ng=1 m=%s mm_ok=1" % (m, m))
    if float(S["CXW"]) > 0:
        L["XCROSS"] = ("* cross-coupled Miller caps (rev 2): add to the Miller cap for CM, subtract for DM (as r1_afe revision D)\n"
                       "XCXA cza outn cap_cmim w=%su l=%su m=1 mm_ok=1\nXCXB czb outp cap_cmim w=%su l=%su m=1 mm_ok=1" % ((S["CXW"],) * 4))
    else:
        L["XCROSS"] = "* (no cross-coupled Miller caps)"
    if float(S["RDG"]) > 0:
        L["SF1"], L["SF2"] = "sf1", "sf2"
        L["DEGEN"] = ("* CMFB pair source degeneration (rev 2): lowers the CM loop gain at all frequencies\n"
                      "XRDG1 ctail sf1 vss rppd w=1u l=%su m=1 b=0 mm_ok=1\nXRDG2 ctail sf2 vss rppd w=1u l=%su m=1 b=0 mm_ok=1" % (S["RDG"], S["RDG"]))
    else:
        L["SF1"], L["SF2"], L["DEGEN"] = "ctail", "ctail", "* (no CMFB degeneration)"
    if float(S["RH"]) > 0:
        L["XH1"], L["XH2"] = "xh1", "xh2"
        L["HOLDR"] = ("* hold-path series resistors (rev 2): isolate the hold caps from the stage-1 output node above the AZ servo band\n"
                      "XRH1 x1a xh1 vss rhigh w=1u l=%gu m=1 b=0 mm_ok=1\nXRH2 x1b xh2 vss rhigh w=1u l=%gu m=1 b=0 mm_ok=1" % ((0.75 * float(S["RH"]),) * 2))
    else:
        L["XH1"], L["XH2"], L["HOLDR"] = "x1a", "x1b", "* (no hold-path series resistors)"
    if S["TP"] == "1":
        L["TWOPATH"] = ("* two-path CMFB (rev 2). Slow path: pair XMG1 (vcms) / XMG2 (vcm), NMOS mirror load, output vint integrates on XCI;\n"
                        "* XMI (gate vint) takes current from the CMFB diode node vcmfb, so the slow path trims the sink current until the\n"
                        "* output CM equals vcm (DC accuracy: slow-pair offset only). Fast path: XMF1/XMF2 (degenerated, RDG) sets the CM crossover.\n"
                        "XMTG gtail vbp vdda vdda sg13_hv_pmos w=%su l=2u ng=1 m=%s mm_ok=1\n"
                        "XMG1 vgd vcms gtail gtail sg13_hv_pmos w=%su l=%su ng=1 m=1 mm_ok=1\n"
                        "XMG2 vint vcm gtail gtail sg13_hv_pmos w=%su l=%su ng=1 m=1 mm_ok=1\n"
                        "XMGD vgd vgd vss vss sg13_hv_nmos w=%su l=%su ng=1 m=1 mm_ok=1\n"
                        "XMGM vint vgd vss vss sg13_hv_nmos w=%su l=%su ng=1 m=1 mm_ok=1\n"
                        "XCI vint vss cap_cmim w=%su l=%su m=1 mm_ok=1\n"
                        "XMI vcmfb vint vss vss sg13_hv_nmos w=%su l=%su ng=1 m=1 mm_ok=1" % (
                            S["TGW"], S["TPT"], S["TPW"], S["TPL"], S["TPW"], S["TPL"], S["TMW"], S["TML"], S["TMW"], S["TML"], S["TPC"], S["TPC"], S["TIW"], S["TIL"]))
    elif S["TP"] == "2":
        L["TWOPATH"] = ("* two-path CMFB (rev 2). Slow path: OTA XMG1 (gate vcms) / XMG2 (gate vcm), long-channel, NMOS mirror load (diode on the\n"
                        "* XMG2 side), output vint at the XMG1 drain integrates on XCI (bottom plate at %s). vint is the reference gate of the fast pair (XMF2), so\n"
                        "* the slow path moves the fast-path reference until the output CM equals vcm (DC accuracy: slow-OTA offset only).\n"
                        "* Fast path: XMF1/XMF2 with source degeneration (RDG) sets the CM loop crossover.\n"
                        "XMTG gtail vbp vdda vdda sg13_hv_pmos w=%su l=2u ng=1 m=%s mm_ok=1\n"
                        "%s"
                        "XMG1 vint vcms %s gtail sg13_hv_pmos w=%su l=%su ng=1 m=1 mm_ok=1\n"
                        "XMG2 vgd vcm %s gtail sg13_hv_pmos w=%su l=%su ng=1 m=1 mm_ok=1\n"
                        "XMGD vgd vgd vss vss sg13_hv_nmos w=%su l=%su ng=1 m=1 mm_ok=1\n"
                        "XMGM vint vgd vss vss sg13_hv_nmos w=%su l=%su ng=1 m=1 mm_ok=1\n"
                        "XCI vint %s cap_cmim w=%su l=%su m=1 mm_ok=1" % (
                            S["TCR"], S["TGW"], S["TPT"], ("XRTG1 gtail gs1 vss rhigh w=1u l=%gu m=1 b=0 mm_ok=1\nXRTG2 gtail gs2 vss rhigh w=1u l=%gu m=1 b=0 mm_ok=1\n" % (
                                0.75 * float(S["RTG"]), 0.75 * float(S["RTG"]))) if float(S["RTG"]) > 0 else "",
                            "gs1" if float(S["RTG"]) > 0 else "gtail", S["TPW"], S["TPL"], "gs2" if float(S["RTG"]) > 0 else "gtail", S["TPW"], S["TPL"],
                            S["TMW"], S["TML"], S["TMW"], S["TML"], S["TCR"], S["TPC"], S["TPC"]))
    else:
        L["TWOPATH"] = "* (single-path CMFB)"
    L["F2G"] = "vint" if S["TP"] == "2" else "vcm"
    if S["LAG"] != "0":
        r1, r2, cs = [float(x) for x in S["LAG"].split(",")]
        L["VCMG"] = "vcmg"
        # rhigh w = 1 um: 200 kOhm at l = 150 um (XRCA), i.e. 0.75 um per kOhm
        L["LAGNET"] = ("* CMFB lag network (rev 2): sink gates behind R1, shunt R2 + C; DC unchanged (gates draw no current)\n"
                       "XRLG1 vcmfb vcmg vss rhigh w=1u l=%gu m=1 b=0 mm_ok=1\nXRLG2 vcmg vlag vss rhigh w=1u l=%gu m=1 b=0 mm_ok=1\n"
                       "XCLG vlag vss cap_cmim w=%gu l=%gu m=1 mm_ok=1" % (0.75 * r1, 0.75 * r2, cs, cs))
    else:
        L["VCMG"], L["LAGNET"] = "vcmfb", "* (no CMFB lag network)"
    return L
here = os.path.dirname(os.path.abspath(__file__))
out = os.path.join(here, "r1_isense.spice")
args = sys.argv[1:]
if "--out" in args:
    i = args.index("--out"); out = args[i + 1]; del args[i:i + 2]
for a in args:
    k, v = a.split("=", 1); SIZES[k] = v
txt = open(os.path.join(here, "r1_isense.spice.tmpl")).read()
for k, v in list(expand(SIZES).items()) + list(SIZES.items()):
    txt = txt.replace("@@%s@@" % k, v)
assert "@@" not in txt, "unfilled placeholder"
hdr = "* GENERATED by gen_isense.py from r1_isense.spice.tmpl -- do not edit; sizes: %s\n" % \
      " ".join("%s=%s" % kv for kv in sorted(SIZES.items()))
open(out, "w").write(hdr + txt)
print(out)

#!/usr/bin/env python3
"""Write the R1_OSC schematic-level SPICE source (schematic/r1_osc.spice).

R1_OSC is the G1 R0.95 ping-pong RC relaxation oscillator (designs/g1-guardian/blocks/g1_osc,
schematic-level source sim/netlist/g1_osc.spice with RA/RB = R0.95) re-tuned for 30 MHz:

  * timing resistors RA/RB: rppd 1 um wide, shorter (R0.95 111.15 um -> L_R below)
  * timing capacitor banks: fixed cmim + 5-bit trim built from a 25 fF unit cmim (bit i = 2**i units),
    one NMOS switch to vss per bit (switch width scales with the bit)
  * comparator tail current raised (bias reference current up, tail mirror ratio M_TAIL)
  * SR latch, enable and reset logic as G1; output buffer upsized
  * threshold vdd/2 from the G1 rppd divider with the 1 pF cmim hold capacitor and the antenna diode

Half period = R*C*ln2 + t_d.  en=0 forces Q=0 and holds both banks discharged; osc_clk is low.
Ports: en trim0 trim1 trim2 trim3 trim4 osc_clk vdd vss  (1.2 V core domain).

Usage: python3 gen_r1_osc.py [out.spice]   (sizes are the module constants below; the MC deck needs
mm_ok=1 on every device, which this netlist carries; the non-mismatch model sections ignore it).
"""
import sys

# ---- sizes (revision tracked in ../README.md) ----
REV = "r1"
L_R = "48.3u"         # timing rppd length per branch, w = 1 um  (R ~ 70 + 260*L[um] Ohm)
C_UNIT_SIDE = 4.03   # um: unit cmim 4.03 x 4.03 um  ~ 25.0 fF (1.5 fF/um2 + 40 aF/um perimeter)
C_FIX_SIDE = 28.55   # um: fixed cmim per bank ~ 1.23 pF
SW_W = ["0.5u", "0.5u", "1u", "2u", "4u"]   # trim switch NMOS widths, bit 0..4 (l = 0.13 um)
L_RBIAS = "80u"      # bias reference rppd (vdd -> diode), w = 1 um
M_TAIL = 2           # comparator tail = M_TAIL x reference diode (2u/0.5u)
L_RT = "384.3u"      # threshold divider rppd, each half (G1 value)
CTH_SIDE = "26u"     # threshold hold cmim (G1 value, ~1 pF)


def cbank():
    lines = [".subckt r1_osc_cbank t0 t1 t2 t3 t4 top vss",
             "* fixed cmim + 5-bit binary trim; bit i = 2**i unit cmim in parallel (m), NMOS switch to vss",
             "XCF top vss cap_cmim w=%.2fu l=%.2fu m=1 mm_ok=1" % (C_FIX_SIDE, C_FIX_SIDE)]
    for i in range(5):
        lines.append("XCT%d top b%d cap_cmim w=%.2fu l=%.2fu m=%d mm_ok=1" % (i, i, C_UNIT_SIDE, C_UNIT_SIDE, 2 ** i))
        lines.append("XMS%d b%d t%d vss vss sg13_lv_nmos w=%s l=0.13u ng=1 m=1 mm_ok=1" % (i, i, i, SW_W[i]))
    lines.append(".ends")
    return lines


def cmp_():
    return [".subckt r1_osc_cmp inp inn vbn out vdd vss",
            "* continuous-time comparator: NMOS-input 5-T pair, PMOS mirror, two inverters (G1 g1_osc_cmp, tail x%d)" % M_TAIL,
            "XMT tail vbn vss vss sg13_lv_nmos w=2u l=0.5u ng=1 m=%d mm_ok=1" % M_TAIL,
            "XM1 d1 inp tail vss sg13_lv_nmos w=4u l=0.3u ng=1 m=1 mm_ok=1",
            "XM2 o1 inn tail vss sg13_lv_nmos w=4u l=0.3u ng=1 m=1 mm_ok=1",
            "XM3 d1 d1 vdd vdd sg13_lv_pmos w=2u l=0.3u ng=1 m=1 mm_ok=1",
            "XM4 o1 d1 vdd vdd sg13_lv_pmos w=2u l=0.3u ng=1 m=1 mm_ok=1",
            "XI1 o1 o2 vdd vss r1_osc_inv",
            "XI2 o2 out vdd vss r1_osc_inv",
            ".ends"]


def gates():
    return [
        ".subckt r1_osc_inv a y vdd vss",
        "XMP y a vdd vdd sg13_lv_pmos w=1u l=0.13u ng=1 m=1 mm_ok=1",
        "XMN y a vss vss sg13_lv_nmos w=0.5u l=0.13u ng=1 m=1 mm_ok=1",
        ".ends",
        ".subckt r1_osc_buf4 a y vdd vss",
        "* output inverter, 4x the unit inverter",
        "XMP y a vdd vdd sg13_lv_pmos w=4u l=0.13u ng=1 m=1 mm_ok=1",
        "XMN y a vss vss sg13_lv_nmos w=2u l=0.13u ng=1 m=1 mm_ok=1",
        ".ends",
        ".subckt r1_osc_nor3 a0 a1 a2 y vdd vss",
        "XMP0 p0 a0 vdd vdd sg13_lv_pmos w=3u l=0.13u ng=1 m=1 mm_ok=1",
        "XMP1 p1 a1 p0 vdd sg13_lv_pmos w=3u l=0.13u ng=1 m=1 mm_ok=1",
        "XMP2 y a2 p1 vdd sg13_lv_pmos w=3u l=0.13u ng=1 m=1 mm_ok=1",
        "XMN0 y a0 vss vss sg13_lv_nmos w=0.5u l=0.13u ng=1 m=1 mm_ok=1",
        "XMN1 y a1 vss vss sg13_lv_nmos w=0.5u l=0.13u ng=1 m=1 mm_ok=1",
        "XMN2 y a2 vss vss sg13_lv_nmos w=0.5u l=0.13u ng=1 m=1 mm_ok=1",
        ".ends",
        ".subckt r1_osc_nor2 a0 a1 y vdd vss",
        "XMP0 p0 a0 vdd vdd sg13_lv_pmos w=2u l=0.13u ng=1 m=1 mm_ok=1",
        "XMP1 y a1 p0 vdd sg13_lv_pmos w=2u l=0.13u ng=1 m=1 mm_ok=1",
        "XMN0 y a0 vss vss sg13_lv_nmos w=0.5u l=0.13u ng=1 m=1 mm_ok=1",
        "XMN1 y a1 vss vss sg13_lv_nmos w=0.5u l=0.13u ng=1 m=1 mm_ok=1",
        ".ends",
        ".subckt r1_osc_nand2 a0 a1 y vdd vss",
        "XMP0 y a0 vdd vdd sg13_lv_pmos w=1u l=0.13u ng=1 m=1 mm_ok=1",
        "XMP1 y a1 vdd vdd sg13_lv_pmos w=1u l=0.13u ng=1 m=1 mm_ok=1",
        "XMN0 y a0 n0 vss sg13_lv_nmos w=1u l=0.13u ng=1 m=1 mm_ok=1",
        "XMN1 n0 a1 vss vss sg13_lv_nmos w=1u l=0.13u ng=1 m=1 mm_ok=1",
        ".ends",
    ]


def top():
    tr = "trim0 trim1 trim2 trim3 trim4"
    return [
        ".subckt r1_osc en trim0 trim1 trim2 trim3 trim4 osc_clk vdd vss",
        "XRA vdd va sub! rppd w=1u l=%s m=1 b=0 mm_ok=1" % L_R,
        "XRB vdd vb sub! rppd w=1u l=%s m=1 b=0 mm_ok=1" % L_R,
        "XCA %s va vss r1_osc_cbank" % tr,
        "XCB %s vb vss r1_osc_cbank" % tr,
        "XMRA va rsta vss vss sg13_lv_nmos w=4u l=0.13u ng=1 m=1 mm_ok=1",
        "XMRB vb rstb vss vss sg13_lv_nmos w=4u l=0.13u ng=1 m=1 mm_ok=1",
        "XRT1 vdd vth sub! rppd w=1u l=%s m=1 b=0 mm_ok=1" % L_RT,
        "XRT2 vth vss sub! rppd w=1u l=%s m=1 b=0 mm_ok=1" % L_RT,
        "XCTH vth vss cap_cmim w=%s l=%s m=1 mm_ok=1" % (CTH_SIDE, CTH_SIDE),
        "XDANT vth vdd dpantenna l=0.78u w=0.78u",
        "XRBIAS vdd vbn sub! rppd w=1u l=%s m=1 b=0 mm_ok=1" % L_RBIAS,
        "XMBD vbn vbn vss vss sg13_lv_nmos w=2u l=0.5u ng=1 m=1 mm_ok=1",
        "XCMPA va vth vbn ca vdd vss r1_osc_cmp",
        "XCMPB vb vth vbn cb vdd vss r1_osc_cmp",
        "XEN en en_n vdd vss r1_osc_inv",
        "XNQ ca en_n qb q vdd vss r1_osc_nor3",
        "XNQB cb q qb vdd vss r1_osc_nor2",
        "XRSTB qb en rstb vdd vss r1_osc_nand2",
        "XRSTA q rsta vdd vss r1_osc_inv",
        "XB1 q qn_b vdd vss r1_osc_inv",
        "XB2 qn_b osc_clk vdd vss r1_osc_buf4",
        ".ends",
    ]


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "r1_osc.spice"
    hdr = ["* R1_OSC schematic-level source, revision %s, written by schematic/gen_r1_osc.py" % REV,
           "* 30 MHz nominal ping-pong RC relaxation oscillator, 5-bit cmim trim; lineage G1 g1_osc R0.95",
           "* sizes: L_R=%s C_fix=%.2fx%.2f um C_unit=%.2fx%.2f um SW_W=%s L_RBIAS=%s M_TAIL=%d"
           % (L_R, C_FIX_SIDE, C_FIX_SIDE, C_UNIT_SIDE, C_UNIT_SIDE, ",".join(SW_W), L_RBIAS, M_TAIL)]
    body = hdr + top() + [""] + cbank() + [""] + cmp_() + [""] + gates()
    with open(out, "w") as f:
        f.write("\n".join(body) + "\n")


if __name__ == "__main__":
    main()

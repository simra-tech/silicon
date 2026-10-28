#!/usr/bin/env python3
"""T2o (PLAN.md D28 item 1, 2026-10-28): small-signal impedance of the reference path at a slice port of an extracted
r1_adc netlist (r1_adc_lay_pr); wiring term = Z(port) - Z(main node).

The SAR is not in the deck: every sar_* line is held at a DC level (CDAC lines 0 = every bottom plate on its reference,
comparator clocks in reset, track switches open), so the CDAC presents its full bottom-plate load to the reference ports.
Bandgap: 1.045 V through 190 kOhm into vref_in (the 10 pF filter is in the layout netlist); ibias: 5 uA from vdda.
A 1 A AC current is injected into one node at a time (the analysis is linear): main node vrefl (follower source),
slice A port vrefl__p4, main node vref, slice A port vref__p13. v(node) = Z.
usage: gen_zref.py <run id> <netlist> <corner> <temp> <vdd>"""
import os, re, sys
rid, net, corner, temp, vdd = sys.argv[1:6]
root = os.environ["G1_RESULTS_ROOT"]
BLOCK = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
src = open(os.path.join(BLOCK, net)).read()
m = re.search(r"^\.subckt r1_adc_lay_pr ([^\n]*)", src, re.M)
pins = m.group(1).split()
PORTS = ['vrefl__p4', 'vref__p13']
# a copy of r1_adc_lay_pr with the two slice-port nodes as extra pins
body = re.search(r"^\.subckt r1_adc_lay_pr .*?^\.ends", src, re.M | re.S).group(0)
body = body.replace(".subckt r1_adc_lay_pr " + m.group(1), ".subckt r1_adc_lay_zp " + m.group(1) + " " + " ".join(PORTS), 1)
d = os.path.join(root, "r1_adc", rid)
os.makedirs(d, exist_ok=True)
open(os.path.join(d, "zp.spice"), "w").write(body + "\n")
conn = []
for p in pins:
    if p in ('vdd',): conn.append('vdd')
    elif p == 'vdda': conn.append('vdda')
    elif p == 'vss': conn.append('0')
    elif p == 'vref_in': conn.append('vbg')
    elif p == 'ibias': conn.append('nb')
    elif p in ('vref', 'vrefl'): conn.append(p)
    elif p.startswith('ain_') or p in ('vcm', 'vcm2'): conn.append('vcmn')
    elif p == 'clk': conn.append('0')
    elif p.startswith('sar_clk'): conn.append('vdd' if p.endswith('b') else '0')
    elif p.startswith('sar_c') or p.startswith('sar_trk'): conn.append('0')
    else: conn.append('nc_' + p)
L = ["* reference-path impedance (T2o, sim/post/b9/gen_zref.py): %s, %s %s C VDD %s" % (net, corner, temp, vdd),
     ".lib /foss/pdks/ihp-sg13g2/libs.tech/ngspice/models/cornerMOSlv.lib %s" % corner,
     ".lib /foss/pdks/ihp-sg13g2/libs.tech/ngspice/models/cornerMOShv.lib %s" % corner,
     ".lib /foss/pdks/ihp-sg13g2/libs.tech/ngspice/models/cornerCAP.lib cap_typ",
     ".lib /foss/pdks/ihp-sg13g2/libs.tech/ngspice/models/cornerRES.lib res_typ",
     ".include schematic/r1_adc_r5.spice", ".include %s" % net, ".include %s/zp.spice" % d, ".temp %s" % temp,
     ".option reltol=1e-4 vntol=1e-6 abstol=1e-12 sparse noopiter",
     "Vdd vdd 0 %s" % vdd, "Vdda vdda 0 3.3", "Vbgi vbgi 0 1.045", "Rbg vbgi vbg 190k", "Ib vdda nb 5u", "Vcm vcmn 0 0.6",
     "X1 " + " ".join(conn) + " " + " ".join(PORTS) + " r1_adc_lay_zp"]
for p in pins:
    if ('nc_' + p) in conn:
        L.append("Rnc_%s nc_%s 0 1G" % (p, p))
L += ["Ia1 0 vrefl DC 0 AC 0", "Ia2 0 vrefl__p4 DC 0 AC 0", "Ia3 0 vref DC 0 AC 0", "Ia4 0 vref__p13 DC 0 AC 0"]
L.append(".control")
L.append("op")
L.append("print v(vref) v(vrefl) v(vref__p13) v(vrefl__p4) v(vbg) v(x1.xref_ng) i(vdda) > %s/op.txt" % d)
for tag, src_ in (('l_main', 'Ia1'), ('l_port', 'Ia2'), ('m_main', 'Ia3'), ('m_port', 'Ia4')):
    L += ["alter %s acmag = 1" % src_, "ac dec 10 1k 3g",
          "wrdata %s/z_%s.txt vm(vrefl) vm(vrefl__p4) vm(vref) vm(vref__p13)" % (d, tag),
          "alter %s acmag = 0" % src_]
L += [".endc", ".end"]
open(os.path.join(d, "deck.cir"), "w").write("\n".join(L) + "\n")
print(os.path.join(d, "deck.cir"))

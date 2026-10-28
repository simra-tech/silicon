#!/usr/bin/env python3
"""T2o (PLAN.md D28 item 3, 2026-10-28): regeneration time of the decision comparators against the input, with the
comparator clock rising at a given strobe after a 16 ns reset (revision-6 strobe: clk falling edge).

Schematic cells of the netlist of record (schematic/r1_adc_r5.spice: r1_cmp4 with r1_cmp4_bias, r1_cmp5n with
r1_cmp5n_bias), one instance per differential input vd (both signs), each with its own bias cell (one shared bias for all instances starves the tails through the
gate coupling of the tails at the strobe: runs b9-regen2-*, ledger F-20261030-T2o-02), all on one ideal clock (clk rises at 16.67 ns,
falls at 33.33 + 16.67 ns; complement ideal). Regeneration = first time after the strobe at which an output leaves its
reset level by VDD / 2 (r1_cmp4: min(outp, outn) < VDD / 2; r1_cmp5n: max(outp, outn) > VDD / 2), as r24_d23.py.
Output deck: <G1_RESULTS_ROOT>/r1_adc/<id>/deck.cir; results by post_regen.py.
usage: gen_regen.py <run id> <corner mos_tt|mos_ss|mos_ff> <temp> <vdd> <cm> [<r1_cmp4 instance params> [<r1_cmp5n params>]]
Instance params (what-if, not a netlist change), e.g. "wcap=40u": the r1_cmp4 integration capacitors halved."""
import os, sys
rid, corner, temp, vdd, cm = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4]), float(sys.argv[5])
P4 = sys.argv[6] if len(sys.argv) > 6 else ""
P5 = sys.argv[7] if len(sys.argv) > 7 else ""
root = os.environ["G1_RESULTS_ROOT"]
VD = [s * v for v in (1e-6, 3e-6, 1e-5, 3e-5, 1e-4, 2e-4, 4e-4, 1e-3, 3e-3, 1e-2, 3e-2) for s in (1, -1)]
L = ["* regeneration sweep, %s %s C VDD %.3g V, CM %.3g V (T2o, sim/post/b9/gen_regen.py) %s %s" % (corner, temp, vdd, cm, P4, P5),
     ".lib /foss/pdks/ihp-sg13g2/libs.tech/ngspice/models/cornerMOSlv.lib %s" % corner,
     ".lib /foss/pdks/ihp-sg13g2/libs.tech/ngspice/models/cornerMOShv.lib %s" % corner,
     ".lib /foss/pdks/ihp-sg13g2/libs.tech/ngspice/models/cornerCAP.lib cap_typ",
     ".lib /foss/pdks/ihp-sg13g2/libs.tech/ngspice/models/cornerRES.lib res_typ",
     ".include schematic/r1_adc_r5.spice", ".temp %s" % temp,
     ".option reltol=1e-4 vntol=1e-7 abstol=1e-13 method=gear",
     "Vdd vdd 0 %.4g" % vdd,
     "Vck ck 0 PULSE(0 %.4g 16.6667n 50p 50p 33.2333n 66.6667n)" % vdd,
     "Vckb ckb 0 PULSE(%.4g 0 16.6667n 50p 50p 33.2333n 66.6667n)" % vdd,
     ]
for i, v in enumerate(VD):
    L += ["Vp%d p%d 0 %.9g" % (i, i, cm + v / 2), "Vn%d n%d 0 %.9g" % (i, i, cm - v / 2),
          "XB4_%d vbp%d vdd 0 r1_cmp4_bias" % (i, i), "XB5_%d vbn%d vdd 0 r1_cmp5n_bias" % (i, i),
          "XC4_%d p%d n%d ck ckb a%d b%d vbp%d vdd 0 r1_cmp4 %s" % (i, i, i, i, i, i, P4),
          "XC5_%d p%d n%d ck ckb c%d d%d vbn%d vdd 0 r1_cmp5n %s" % (i, i, i, i, i, i, P5)]
L += [".control", "tran 5p 50n 0 20p", "set wr_singlescale", "set wr_vecnames", "option numdgt=7",
      "wrdata %s/r1_adc/%s/regen.txt v(ck) %s" % (root, rid, " ".join("v(a%d) v(b%d) v(c%d) v(d%d)" % (i, i, i, i) for i in range(len(VD)))),
      ".endc", ".end"]
d = os.path.join(root, "r1_adc", rid)
os.makedirs(d, exist_ok=True)
open(os.path.join(d, "deck.cir"), "w").write("\n".join(L) + "\n")
open(os.path.join(d, "vd.txt"), "w").write(" ".join("%.9g" % v for v in VD) + "\n")
print(os.path.join(d, "deck.cir"))

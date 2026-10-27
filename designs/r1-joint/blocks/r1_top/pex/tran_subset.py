# SPDX-License-Identifier: Apache-2.0
"""r1_top try g, chip-level extraction (track T11), check (d): 1 us transient of the extracted top network with
schematic macros on the current path (the subset of testbench test 3: shunt pads -> r1_isense -> ADC input pins).

  python3 tran_subset.py <netlist dir> <r1_top_g_pex.spice | r1_top_g_pex_red.spice> <out dir> [tstop_us]

Deck (built from the RC subcircuit r1_top_rc, not from the wrapper, so that only the subset is instantiated):
  real (netlists of record): the extracted top-level network r1_top_rc (tt sheet values), r1_isense revision 2
    (schematic/r1_isense.spice), r1_bias revision 2 (schematic/r1_bias.spice: bias currents, POR, VREF buffer of
    VREF_B; deck-local copy with npn13G2 selft=0, testbench deviation D4), the four IOPadAnalog cells of ISA_P/N and
    ISB_P/N (PDK sg13g2_io.spi, deck-local copy without dantenna, testbench deviation D1).
  ideal (MODEL parts of this check): r1_bgr outputs at its pins (VREF_BG 1.045 V, PBIAS 2.297 V, PCASC 1.75 V, the
    testbench nodeset D6); the r1_ctrl_top AZ_WIN output (ideal 1.2 V pulse at the ctrl pin, 2 us period: low in the
    run); VCM 0.6 V through 1 kOhm at the r1_adc vcm pin (testbench MODEL M4); supplies at the bond pads (VDD 1.2 V,
    VDDA 3.3 V, IOVDD 3.3 V, VSS and IOVSS 0 V); shunt inputs at the pads: ISA_N, ISB_N 0 V, ISA_P 0 -> 30 mV,
    ISB_P 0 -> 80 mV at 0.3 us (testbench test 3 levels A and B).
  not instantiated (their pins load nothing but the extracted wiring): r1_adc, r1_afe, r1_safe, r1_t2f, r1_osc,
    r1_ctrl_top, r1_gate_lv, r1_ls, decap and tie cells, the other IO cells.
Options as the testbench decks 2-6 (deviation D9): method=gear maxord=2 reltol=2e-3 abstol=1e-10 vntol=1e-5.
Outputs: <out>/tran_subset.cir, .log, tran_subset.json (wall time, s per simulated us, ISN_OUT* at the ADC pins).
"""
import json
import os
import re
import subprocess
import sys
import time

ND, NLF, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
TSTOP = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0
os.makedirs(OUT, exist_ok=True)
REPO = "/work"
PDK = "/foss/pdks/ihp-sg13g2"
MODELS = PDK + "/libs.tech/ngspice/models"
IOSPI = PDK + "/libs.ref/sg13g2_io/spice/sg13g2_io.spi"
BLK = REPO + "/designs/r1-joint/blocks"


def norm(p):
    return re.sub(r"_+$", "", re.sub(r"[\[\]<>]", "_", p.lower()))


# deck-local IO copy without dantenna
lines = open(IOSPI).read().splitlines()
out = ["* deck-local copy of the PDK sg13g2_io.spi without dantenna instances (testbench deviation D1)"]
nrem = 0
for l in lines:
    t = l.split()
    if t and t[0][0] in "Xx" and "dantenna" in [w for w in t if "=" not in w][-1:]:
        out.append("* removed: " + l)
        nrem += 1
        continue
    out.append(l)
open(os.path.join(OUT, "sg13g2_io_nodcn.spi"), "w").write("\n".join(out) + "\n")
# deck-local r1_bias with selft=0 on the HBTs
b = open(BLK + "/r1_bias/schematic/r1_bias.spice").read().splitlines()
nb = 0
for i, l in enumerate(b):
    if l.split() and l.split()[0][0] in "Xx" and "npn13G2" in l:
        b[i] = l + " selft=0"
        nb += 1
open(os.path.join(OUT, "r1_bias_selft0.spice"), "w").write("\n".join(b) + "\n")

# ports of r1_top_rc
src = open(os.path.join(ND, NLF)).read()
m = re.search(r"\.subckt r1_top_rc(.*?)\n(?!\+)", src, re.S)
hdr = m.group(1).replace("\n+", " ").split()
ports = [x for x in hdr if "=" not in x and x != "params:"]
P = set(ports)


def pn(inst, pin):
    q = "%s__%s" % (inst, norm(pin))
    return q if q in P else q + "_nc"


ISEN = "isa_p isa_n isb_p isb_n outa_p outa_n outb_p outb_n vref vcm ibias_a ibias_b az_a azh_a az_b azh_b vdda vdd vss".split()
BIAS = ("vdda vdd vss pbias pcasc ib_afe_s1 ib_afe_s2 ib_afe_c1 ib_afe_c2 ib_is_a ib_is_b ib_sf_oa ib_sf_na ib_sf_ob "
        "ib_sf_nb ib_adc_ref por_n vref vref_b").split()
L = ["* T11 check (d): 1 us transient, extracted top network %s + schematic r1_isense, r1_bias (current path)" % NLF,
     ".lib %s/cornerMOSlv.lib mos_tt" % MODELS, ".lib %s/cornerMOShv.lib mos_tt" % MODELS,
     ".lib %s/cornerRES.lib res_typ" % MODELS, ".lib %s/cornerCAP.lib cap_typ" % MODELS,
     ".lib %s/cornerHBT.lib hbt_typ" % MODELS, ".lib %s/cornerDIO.lib dio_tt" % MODELS,
     ".include %s" % os.path.join(OUT, "sg13g2_io_nodcn.spi"),
     ".include %s" % os.path.join(ND, NLF),
     ".include %s/r1_isense/schematic/r1_isense.spice" % BLK,
     ".include %s" % os.path.join(OUT, "r1_bias_selft0.spice"),
     "Xrc " + " ".join(p if p != "sub" else "VSS" for p in ports) + " r1_top_rc ictrl_p=0",
     "Xu_isense " + " ".join(pn("u_isense", p) for p in ISEN) + " r1_isense",
     "Xu_bias " + " ".join(pn("u_bias", p) for p in BIAS) + " r1_bias"]
for pad in ("isa_p", "isa_n", "isb_p", "isb_n"):
    io = "io_" + pad
    L.append("Xio_%s %s %s %s %s %s %s sg13g2_IOPadAnalog" % (pad, io + "__pad", io + "__padres", io + "__vdd", io + "__vss",
                                                            io + "__iovdd", io + "__iovss"))
L += ["* supplies and pads",
      "Vvdd VDD 0 1.2", "Vvdda VDDA 0 3.3", "Vvss VSS 0 0", "Viovdd IOVDD 0 3.3", "Viovss IOVSS 0 0",
      "Visa_n ISA_N 0 0", "Visb_n ISB_N 0 0",
      "Visa_p ISA_P 0 PWL(0 0 0.3u 0 0.31u 30m)", "Visb_p ISB_P 0 PWL(0 0 0.3u 0 0.31u 80m)",
      "* r1_bgr outputs (ideal, testbench nodeset D6)",
      "Vbgr_vref %s 0 1.045" % pn("u_bgr", "vref"), "Vbgr_pbias %s 0 2.297" % pn("u_bgr", "pbias"),
      "Vbgr_pcasc %s 0 1.75" % pn("u_bgr", "pcasc"),
      "* r1_ctrl_top az_win (ideal), VCM model at the ADC vcm pin",
      "Vaz %s 0 PULSE(0 1.2 1.5u 0.25n 0.25n 0.5u 2u)" % pn("u_ctrl", "az_win"),
      "Vvcm vcm_i 0 0.6", "Rvcm vcm_i %s 1k" % pn("u_adc", "vcm"),
      ".options method=gear maxord=2 reltol=2e-3 abstol=1e-10 vntol=1e-5 chgtol=1e-14 rshunt=1e12",
      ".control", "set num_threads=1", "tran 0.2n %gu" % TSTOP]
probes = [pn("u_adc", "ain_isa_p"), pn("u_adc", "ain_isa_n"), pn("u_adc", "ain_isb_p"), pn("u_adc", "ain_isb_n"),
          pn("u_isense", "outa_p"), pn("u_isense", "vref"), pn("u_bias", "vref_b"), pn("u_bias", "por_n")]
for p in probes:
    L.append("meas tran %s_end find v(%s) at=%gu" % (re.sub(r"\W", "_", p), p, TSTOP * 0.99))
    L.append("meas tran %s_pre find v(%s) at=0.29u" % (re.sub(r"\W", "_", p), p))
L += ["rusage all", ".endc", ".end"]
deck = os.path.join(OUT, "tran_subset.cir")
open(deck, "w").write("\n".join(L) + "\n")
# the PSP/OSDI models load from .spiceinit in the working directory (copy of tb/.spiceinit)
open(os.path.join(OUT, ".spiceinit"), "w").write(open(REPO + "/designs/r1-joint/blocks/r1_top/tb/.spiceinit").read())
t0 = time.time()
o = subprocess.run(["ngspice", "-b", deck], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True,
                   cwd=OUT).stdout
wall = time.time() - t0
open(os.path.join(OUT, "tran_subset.log"), "w").write(o)
meas = {}
for ln in o.splitlines():
    mm = re.match(r"\s*(\S+_(?:end|pre))\s*=\s*([-+0-9.eE]+)", ln)
    if mm:
        meas[mm.group(1)] = float(mm.group(2))
done = len(meas) == 2 * len(probes)
r = {"netlist": NLF, "tstop_us": TSTOP, "wall_s": round(wall, 1), "s_per_us": round(wall / TSTOP, 1),
     "completed": done, "measures_V": meas, "io_dantenna_removed": nrem, "bias_hbt_selft0": nb,
     "ports_of_rc": len(ports)}
json.dump(r, open(os.path.join(OUT, "tran_subset.json"), "w"), indent=1)
print(json.dumps(r, indent=1))

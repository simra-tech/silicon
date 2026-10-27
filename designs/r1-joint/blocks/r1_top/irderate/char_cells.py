# SPDX-License-Identifier: Apache-2.0
"""r1_top try g, ctrl IR-drop derate (track T11b), step 1: delay of PDK standard cells against the supply voltage.

  python3 char_cells.py <out dir> <corner: ss125 | ff-40> <V1,V2,...> [<timeout s per deck, default 600>]

Method: ngspice 46 with the PDK models (cornerMOSlv.lib mos_ss at 125 C, or mos_ff at -40 C) and the PDK standard-cell
SPICE netlist (sg13g2_stdcell.spice). Every node of the deck is on one supply V (the whole cell sees VDD - VSS = V).
Pin orders as the PDK subckts (buf_1: X A VDD VSS; inv_1: Y A VDD VSS). Cells (each driven by two sg13g2_buf_1 from a 50 ps ramp, so the input slew scales with V as in the real path):
  buf_1     A -> X                    (the fanout buffers of the ctrl critical path)
  o21ai_1   A1 -> Y, A2 = 0, B1 = V    (series PMOS pull-up stack; the AOI/OAI gates of the path)
  dfrbpq_1  CLK -> Q, RESET_B = V      (launch flip-flop clock-to-output)
  xor2_1    A -> X, B = 0              (extra: the xor chains of the multiplier)
Loads: "fo3" = 3 x sg13g2_inv_1 inputs + 4 fF; "fo6" = 6 x sg13g2_inv_1 inputs + 15 fF.
Delay = 50 % in to 50 % out, mean of rise and fall. Output: <out>/char_<corner>.json (delays in ps per V).
"""
import json
import os
import subprocess
import sys

OUT, CORNER, VS = sys.argv[1], sys.argv[2], [float(v) for v in sys.argv[3].split(",")]
TMO = int(sys.argv[4]) if len(sys.argv) > 4 else 600      # seconds per deck (a deck over the limit is recorded as None)
os.makedirs(OUT, exist_ok=True)
# the PSP/OSDI models load from .spiceinit in the working directory (copy of tb/.spiceinit, as pex/tran_subset.py)
open(os.path.join(OUT, ".spiceinit"), "w").write(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                                    "..", "tb", ".spiceinit")).read())
MOS, TEMP = {"ss125": ("mos_ss", 125), "ff-40": ("mos_ff", -40)}[CORNER]
PDK = "/foss/pdks/ihp-sg13g2"
CELLS = {
    "buf_1": ("Xd out a vdd 0 sg13g2_buf_1", "a", "out", False),
    "o21ai_1": ("Xd out a 0 vdd vdd 0 sg13g2_o21ai_1", "a", "out", True),
    "dfrbpq_1": ("Xd out a dd vdd vdd 0 sg13g2_dfrbpq_1", "a", "out", None),
    "xor2_1": ("Xd out a 0 vdd 0 sg13g2_xor2_1", "a", "out", False),
}
LOADS = {"fo3": (3, 4e-15), "fo6": (6, 15e-15)}


def deck(cell, load, v):
    inst, a, o, inv = CELLS[cell]
    n, cw = LOADS[load]
    L = ["* char %s %s %.4f V %s" % (cell, load, v, CORNER),
         ".lib %s/libs.tech/ngspice/models/cornerMOSlv.lib %s" % (PDK, MOS),
         ".include %s/libs.ref/sg13g2_stdcell/spice/sg13g2_stdcell.spice" % PDK,
         ".temp %d" % TEMP,
         ".option method=gear reltol=1e-4",
         "Vdd vdd 0 %.5f" % v,
         "Vu u 0 PULSE(0 1 1n 50p 50p 4.95n 10n)",
         "Bin in0 0 V=v(vdd)*v(u)",
         "Xs1 in1 in0 vdd 0 sg13g2_buf_1",
         "Xs2 a in1 vdd 0 sg13g2_buf_1"]
    if cell == "dfrbpq_1":
        # data toggles every second clock edge, 5 ns before the rising clock edge (D edges at 6 n, 16 n, ...)
        L += ["Vud ud 0 PULSE(0 1 6n 50p 50p 9.95n 20n)", "Bd d0 0 V=v(vdd)*v(ud)",
              "Xs3 d1 d0 vdd 0 sg13g2_buf_1", "Xs4 dd d1 vdd 0 sg13g2_buf_1"]
    L.append(inst)
    for k in range(n):
        L.append("Xl%d nl%d out vdd 0 sg13g2_inv_1" % (k, k))
    L.append("Cw out 0 %g" % cw)
    L.append(".control")
    L.append("tran 2p 42n")
    h = v / 2
    if cell == "dfrbpq_1":
        # clock rising edges at 1 n + 10 n k; D high 6-16 n, 26-36 n: Q rises after the edge at 11 n, falls after 21 n
        L += ["meas tran tr trig v(a) val=%g rise=1 td=10n targ v(out) val=%g rise=1 td=10n" % (h, h),
              "meas tran tf trig v(a) val=%g rise=1 td=20n targ v(out) val=%g fall=1 td=20n" % (h, h)]
    else:
        e1, e2 = ("fall", "rise") if inv else ("rise", "fall")
        L += ["meas tran tr trig v(a) val=%g rise=2 targ v(out) val=%g %s=2" % (h, h, e1),
              "meas tran tf trig v(a) val=%g fall=2 targ v(out) val=%g %s=2" % (h, h, e2)]
    L += ["echo RESULT $&tr $&tf", ".endc", ".end"]
    return "\n".join(L) + "\n"


res = {"corner": CORNER, "mos": MOS, "temp_C": TEMP, "loads": LOADS, "method": __doc__.strip().splitlines()[0],
       "delay_ps": {}}
for cell in CELLS:
    for load in LOADS:
        key = "%s/%s" % (cell, load)
        res["delay_ps"][key] = {}
        for v in VS:
            f = os.path.join(OUT, "%s_%s_%s_%.4f.cir" % (CORNER, cell, load, v))
            open(f, "w").write(deck(cell, load, v))
            try:
                p = subprocess.run(["ngspice", "-b", f], capture_output=True, text=True, cwd=OUT, timeout=TMO)
                txt = p.stdout + p.stderr
            except subprocess.TimeoutExpired as e:
                txt = "TIMEOUT after %d s (char_cells.py)\n" % TMO
                p = type("P", (), {"stdout": ""})()
            open(f[:-4] + ".log", "w").write(txt)
            tr = tf = None
            for ln in p.stdout.splitlines():
                if ln.startswith("RESULT"):
                    t = ln.split()
                    tr, tf = float(t[1]) * 1e12, float(t[2]) * 1e12
            res["delay_ps"][key]["%.4f" % v] = {"rise": tr, "fall": tf,
                                                 "mean": None if tr is None else (tr + tf) / 2}
            print(key, "%.4f" % v, tr, tf, flush=True)
json.dump(res, open(os.path.join(OUT, "char_%s.json" % CORNER), "w"), indent=1)

# SPDX-License-Identifier: Apache-2.0
"""Build the top-level LVS reference r1_top.cdl for the partial R1 assembly (track T8).

  python3 make_top_cdl.py <ctrl.cdl from pnl2cdl.py> <out.cdl> <out.json>

Contents, in this order: the r1_ctrl_top CDL (PDK standard-cell library + the macro netlist, from pnl2cdl.py),
the block LVS references of record (r1_bgr, r1_t2f, r1_ls, r1_gate_lv, r1_safe), empty subcircuits for the
placeholders, and the top subcircuit r1_top. The ring is inlined flat into r1_top from the G1-form projected
reference r1_padring_1600_projected_ref.cdl (its core-side nets FAULT_N_C2P, GATE_*_C2P, SLO_SDO_C2P,
*_P2C keep their names). Every instance pin that is not routed today gets a unique net `<inst>__<pin>`.
The net names here equal the labels in r1_top.gds (layout/r1_top_assemble.py).
"""
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BLK = os.path.normpath(os.path.join(HERE, "..", ".."))
ctrl_cdl, out, out_json = sys.argv[1:4]

SRC = {
    "r1_bgr": os.path.join(BLK, "r1_bgr/layout/r1_bgr_lvs.cdl"),
    "r1_t2f": os.path.join(BLK, "r1_t2f/layout/r1_t2f_lvs.cdl"),
    "r1_ls": os.path.join(BLK, "r1_ls/layout/r1_ls_lvs.cdl"),
    "r1_gate_lv": os.path.join(BLK, "r1_gate/layout/r1_gate_lv_lvs.cdl"),
    "r1_safe": os.path.join(BLK, "r1_safe/layout/r1_safe_lvs.cdl"),
}
RING = os.path.join(BLK, "r1_padring/netlist/r1_padring_1600_projected_ref.cdl")

def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()

def subckts(text):
    """name -> port list for every .SUBCKT in text (continuation lines joined)."""
    res = {}
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        if lines[i].upper().startswith(".SUBCKT"):
            toks = lines[i].split()
            while i + 1 < len(lines) and lines[i + 1].startswith("+"):
                i += 1
                toks += lines[i].split()[1:]
            res[toks[1]] = [t for t in toks[2:] if "=" not in t]
        i += 1
    return res

def strip_end(t):
    return "\n".join(l for l in t.splitlines() if l.strip().lower() != ".end")

parts = []
ports = {}
ct = open(ctrl_cdl).read()
parts.append(strip_end(ct))
ports.update(subckts(ct))
for name, p in SRC.items():
    t = open(p).read()
    parts.append("* ---- %s (%s, sha256 %s)\n" % (name, os.path.relpath(p, os.path.join(BLK, "..", "..", "..")), sha(p)) + strip_end(t))
    ports.update(subckts(t))

# placeholders: empty subcircuits (pins = the stubs drawn in the layout, names sanitised)
asm = json.load(open(os.environ["R1_TOP_ASM_JSON"]))
def san(n):
    return re.sub(r"[\[\]]", "_", n)
for ph, pins in asm["placeholder_pins"].items():
    pl = [san(p["pin"]) for p in pins]
    parts.append(".SUBCKT %s %s\n* placeholder: no devices (pending macro)\n.ENDS" % (ph, " ".join(pl)))
    ports[ph] = pl

# ring, flat
rt = open(RING).read()
m = re.search(r"^\.SUBCKT R1_PADRING(.*?)^\.ENDS R1_PADRING", rt, re.S | re.M)
body = m.group(1).splitlines()
hdr = []
k = 0
while k < len(body) and (k == 0 or body[k].startswith("+")):
    hdr += body[k].replace("+", " ").split()
    k += 1
ring_pins = hdr
ring_body = "\n".join(body[k:])

CONN = {
    "u_ctrl": ("r1_ctrl_top", {
        "cs_n": "CS_N_P2C", "ma_sclk": "MA_SCLK_P2C", "slo_sdo": "SLO_SDO_C2P", "sdi": "SDI_P2C",
        "en_pad": "EN_STO_IN_P2C", "fault_n": "FAULT_N_C2P", "gate_a": "PWM_A", "gate_b": "PWM_B",
        "gate_c": "PWM_C", "cmp_0_": "CMP_OC_A", "cmp_1_": "CMP_NEG_A", "cmp_2_": "CMP_OC_B",
        "cmp_3_": "CMP_NEG_B", "t2f_clk": "T2F_FOUT", "VDD": "VDD", "VSS": "VSS"}),
    "u_gate": ("r1_gate_lv", {"pwm_a": "PWM_A", "pwm_b": "PWM_B", "pwm_c": "PWM_C", "gate_en": "VDD",
                              "gc_a": "GATE_A_C2P", "gc_b": "GATE_B_C2P", "gc_c": "GATE_C_C2P",
                              "vdd": "VDD", "vss": "VSS"}),
    "u_bgr": ("r1_bgr", {"vdd": "VDDA", "vss": "VSS", "vref": "VREF_BG", "pbias": "T2F_PBIAS",
                         "pcasc": "T2F_PCASC"}),
    "u_t2f": ("r1_t2f", {"vdd": "VDDA", "vdd12": "VDD", "vss": "VSS", "pbias": "T2F_PBIAS",
                         "pcasc": "T2F_PCASC", "vref": "VREF_BG", "fout": "T2F_FOUT"}),
    "u_safe": ("r1_safe", {"vref": "VREF_BG", "oc_a": "CMP_OC_A", "neg_a": "CMP_NEG_A", "oc_b": "CMP_OC_B",
                           "neg_b": "CMP_NEG_B", "vdda": "VDDA", "vdd": "VDD", "vss": "VSS"}),
}
for k in range(4):
    CONN["u_ls_afe%d" % k] = ("r1_ls", {"vss": "VSS"})   # substrate tap: vss joins the chip substrate (VSS)
for k in range(2):
    CONN["u_ls_t2f%d" % k] = ("r1_ls", {"vss": "VSS"})
for ph in asm["placeholder_pins"]:
    CONN["u_" + ph] = (ph, {})

lines = [".SUBCKT r1_top " + " ".join(ring_pins),
         "* ring of record, flat (G1-form projected reference, %s)" % os.path.basename(RING), ring_body]
table = {}
for inst, (cell, conn) in CONN.items():
    pl = ports[cell]
    unknown = [p for p in conn if p not in pl]
    if unknown:
        sys.exit("%s: pins %s not in %s" % (inst, unknown, cell))
    nets = [conn.get(p, "%s__%s" % (inst, p)) for p in pl]
    lines.append("X%s %s / %s" % (inst, " ".join(nets), cell))
    table[inst] = {"cell": cell, "connected": conn, "unconnected": [p for p in pl if p not in conn]}
dr = asm.get("antenna_decap_row")
if dr:
    if dr["cell"] not in ports:
        sys.exit("decap cell %s not in the library part of the ctrl CDL" % dr["cell"])
    for k in range(dr["count"]):
        lines.append("Xu_decap_ant_%d VDD VSS / %s" % (k, dr["cell"]))
    table["u_decap_ant[0:%d]" % (dr["count"] - 1)] = {"cell": dr["cell"], "connected": {"VDD": "VDD", "VSS": "VSS"},
                                                       "unconnected": []}
lines.append(".ENDS r1_top")
parts.append("\n".join(lines))
with open(out, "w") as f:
    f.write("* r1_top LVS reference (partial assembly, track T8), generated by make_top_cdl.py\n")
    f.write("\n\n".join(parts) + "\n")
info = {"output": os.path.basename(out), "output_sha256": sha(out),
        "inputs": {os.path.basename(p): sha(p) for p in list(SRC.values()) + [RING, ctrl_cdl]},
        "ring_pins": ring_pins, "instances": table}
json.dump(info, open(out_json, "w"), indent=1)
print("written", out, info["output_sha256"])

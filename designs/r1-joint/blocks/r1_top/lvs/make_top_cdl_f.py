# SPDX-License-Identifier: Apache-2.0
"""Build the top-level LVS reference r1_top.cdl for R1 assembly try f (track T8): every macro real.

  python3 make_top_cdl_f.py <r1_top_assembly.json> <ctrl.cdl from pnl2cdl.py> <out.cdl> <out.json> <ofrecord_dir>

Method of make_top_cdl_e.py. Contents, in this order: the r1_ctrl_top 0.6 CDL (PDK standard-cell library + the
gate-level netlist of run r1ctrl_ll_20261026_t12, from pnl2cdl.py), the block LVS references of record (hash-checked):
r1_bgr, r1_t2f, r1_ls, r1_gate_lv, r1_safe, r1_osc (repository), r1_bias revision 2, r1_adc revision 5 layout A,
r1_afe layout E3, r1_isense layout c (<ofrecord_dir>, git HEAD copies), and the top subcircuit r1_top. The ring is
inlined flat from the G1-form projected reference r1_padring_1700_projected_ref.cdl. The instance pin -> net map is the
`connections` table that the layout generator (layout/r1_top_assemble_f.py) writes: one table for layout and
reference. Every subcircuit port that the table does not name gets a unique net `<inst>__<port>`.
Drop-in of a new block CDL: replace the file in <ofrecord_dir> and export R1F_CDL_SHA_<macro> with its sha256.
"""
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BLK = os.path.normpath(os.path.join(HERE, "..", ".."))
REPO = os.path.normpath(os.path.join(BLK, "..", "..", ".."))
asm_json, ctrl_cdl, out, out_json, ofr = sys.argv[1:6]

SRC = {
    "r1_bgr": os.path.join(BLK, "r1_bgr/layout/r1_bgr_lvs.cdl"),
    "r1_t2f": os.path.join(BLK, "r1_t2f/layout/r1_t2f_lvs.cdl"),
    "r1_ls": os.path.join(BLK, "r1_ls/layout/r1_ls_lvs.cdl"),
    "r1_gate_lv": os.path.join(BLK, "r1_gate/layout/r1_gate_lv_lvs.cdl"),
    "r1_safe": os.path.join(BLK, "r1_safe/layout/r1_safe_lvs.cdl"),
    "r1_osc": os.path.join(BLK, "r1_osc/layout/r1_osc_lvs.cdl"),
    "r1_bias": os.path.join(ofr, "r1_bias_lvs.cdl"),
    "r1_afe": os.path.join(ofr, "r1_afe_lvs.cdl"),
    "r1_adc": os.path.join(ofr, "r1_adc_lvs.cdl"),
    "r1_isense": os.path.join(ofr, "r1_isense_lvs.cdl"),
}
EXPECT = {"r1_afe": "112be732b3b772301fd1bb7c20dc1f697788197573fd83976aa49019419bad69",       # layout E3
          "r1_isense": "3021793df19e112a96bdcb6d5618b3b3a00e06bc80baa02c7e293da16f3212f2",    # layout c
          "r1_bias": "abb7bc280fd1632ec405e7cef62a2b4ba0ab688bc6fa85d897d1b0913a36b4a8",      # revision 2
          "r1_adc": "2e18b5c2f80a2755f83f4c181012f6733bfb8cbede01f993abfadf51a534e18b",       # revision 5, layout A
          "r1_osc": "600d5f2bb983601d904142c9d15f62beb363b91bbfafe7ded63c1e2cea6912aa"}
for _k in list(EXPECT):
    if os.environ.get("R1F_CDL_SHA_" + _k):
        EXPECT[_k] = os.environ["R1F_CDL_SHA_" + _k]
RING = os.path.join(BLK, "r1_padring/netlist/r1_padring_1700_projected_ref.cdl")


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def subckts(text):
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


def rel(p):
    if p.startswith(REPO):
        return os.path.relpath(p, REPO)
    return "<G1_RESULTS_ROOT>/r1_top/<run>/inputs/ofrecord/" + os.path.basename(p)


parts, ports = [], {}
ct = open(ctrl_cdl).read()
parts.append(strip_end(ct))
ports.update(subckts(ct))
for name, p in SRC.items():
    if name in EXPECT and sha(p) != EXPECT[name]:
        sys.exit("%s: LVS reference %s is not the netlist of record" % (name, sha(p)))
    t = open(p).read()
    parts.append("* ---- %s (%s, sha256 %s)\n" % (name, rel(p), sha(p)) + strip_end(t))
    ports.update(subckts(t))

rt = open(RING).read()
m = re.search(r"^\.SUBCKT R1_PADRING(.*?)^\.ENDS R1_PADRING", rt, re.S | re.M)
body = m.group(1).splitlines()
hdr, k = [], 0
while k < len(body) and (k == 0 or body[k].startswith("+")):
    hdr += body[k].replace("+", " ").split()
    k += 1
ring_pins, ring_body = hdr, "\n".join(body[k:])

asm = json.load(open(asm_json))


def port_name(cell, pin):
    """layout pin label -> subcircuit port name: ctrl (pnl2cdl) a[k] -> a_k_; r1_adc a[k] -> a<k>."""
    if cell == "r1_ctrl_top":
        return re.sub(r"\[(\d+)\]", r"_\1_", pin)
    if cell == "r1_adc":
        return re.sub(r"\[(\d+)\]", r"<\1>", pin)
    return pin


lines = [".SUBCKT r1_top " + " ".join(ring_pins),
         "* ring of record, flat (G1-form projected reference, %s)" % os.path.basename(RING), ring_body]
table = {}
for inst, rec in asm["connections"].items():
    cell = rec["cell"]
    conn = {port_name(cell, p): n for p, n in rec["pins"].items()}
    pl = ports[cell]
    unknown = [p for p in conn if p not in pl]
    if unknown:
        sys.exit("%s: pins %s not in %s" % (inst, unknown, cell))
    nets = [conn.get(p, "%s__%s" % (inst, re.sub(r"[<>\[\]]", "_", p))) for p in pl]
    lines.append("X%s %s / %s" % (inst, " ".join(nets), cell))
    table[inst] = {"cell": cell, "connected": conn, "unconnected": [p for p in pl if p not in conn]}
dr = asm.get("antenna_decap_row")
if dr:
    for k in range(dr["count"]):
        lines.append("Xu_decap_ant_%d VDD VSS / %s" % (k, dr["cell"]))
    table["u_decap_ant[0:%d]" % (dr["count"] - 1)] = {"cell": dr["cell"], "connected": {"VDD": "VDD", "VSS": "VSS"},
                                                       "unconnected": []}
lines.append(".ENDS r1_top")
parts.append("\n".join(lines))
with open(out, "w") as f:
    f.write("* r1_top LVS reference (assembly try f, track T8), generated by make_top_cdl_f.py\n")
    f.write("\n\n".join(parts) + "\n")
info = {"output": os.path.basename(out), "output_sha256": sha(out),
        "inputs": {rel(p): sha(p) for p in list(SRC.values()) + [RING]},
        "ctrl_cdl_sha256": sha(ctrl_cdl), "assembly_json_sha256": sha(asm_json),
        "ring_pins": ring_pins, "instances": table}
json.dump(info, open(out_json, "w"), indent=1)
print("written", out, info["output_sha256"])

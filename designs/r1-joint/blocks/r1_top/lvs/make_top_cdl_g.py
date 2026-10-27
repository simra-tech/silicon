# SPDX-License-Identifier: Apache-2.0
"""Build the top-level LVS reference r1_top.cdl for R1 assembly try g (track T8e): the chip CDL of record.

  python3 make_top_cdl_g.py <r1_top_assembly.json> <ctrl.cdl from pnl2cdl.py> <out.cdl> <out.json> <ofrecord_dir>

Copy of make_top_cdl_f.py. Contents, in this order: the r1_ctrl_top 0.8 CDL (PDK standard-cell library + the
gate-level netlist of run r1ctrl_ll_20261027_t22, from pnl2cdl.py), the block LVS references (hash-checked):
r1_bgr, r1_t2f, r1_ls, r1_gate_lv, r1_safe (revision 3), r1_osc (revision 2) (repository), r1_bias revision 2,
r1_adc B5 CDL (analog netlist of record + the r1_adc_sar gate-level netlist, layout/r1_adc_lvs_b5.cdl; also the B6
reference), r1_afe layout E6 (revision F2), r1_isense layout c (revision 2) (<ofrecord_dir>, snapshots), and the top
subcircuit r1_top. Try g: a subcircuit that an earlier part already defines (the PDK standard cells and the bondpad
cell, which the ADC CDL carries as well) is written once; a second definition must be identical (whitespace aside),
else the script stops. The ring is
inlined flat from the G1-form projected reference r1_padring_1700_projected_ref.cdl. The instance pin -> net map is the
`connections` table that the layout generator (layout/r1_top_assemble_f.py) writes: one table for layout and
reference. Every subcircuit port that the table does not name gets a unique net `<inst>__<port>`.
Drop-in of a new block CDL: replace the file in <ofrecord_dir> and export R1G_CDL_SHA_<macro> with its sha256.
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
EXPECT = {"r1_afe": "4271a5f9d38794c7be2daa399c04ba8a702daae5cd796a3e525d300f0bec91a7",       # layout E6 (F2)
          "r1_isense": "3021793df19e112a96bdcb6d5618b3b3a00e06bc80baa02c7e293da16f3212f2",    # layout c
          "r1_bias": "abb7bc280fd1632ec405e7cef62a2b4ba0ab688bc6fa85d897d1b0913a36b4a8",      # revision 2
          "r1_adc": "0740d3a21d00e32faeec149c3f5b594d45e4791c6ffee137edf84795e70b0392",       # B5 CDL (+ SAR), B6 too
          "r1_osc": "600d5f2bb983601d904142c9d15f62beb363b91bbfafe7ded63c1e2cea6912aa",
          "r1_safe": "a083d26387c3006de04e2f6b19f454aaa39c81af23b213f545aae8af3b570732",
          "r1_bgr": "c4d175eebf104a852ce0d9b4b426a0cfa6ede80bc39e7088c179c9ae179fae2b",
          "r1_t2f": "9867279d8e07805a9af642fd42067b14862e43fcbc39ae31cbb17bf753cef9aa",
          "r1_ls": "4f3fefbedfa219acf7d9506d8e8edc878be372f5abc551cba2471caaf2a12460",
          "r1_gate_lv": "c0602540bbe0bc34c023a511e7ee1c8f03e6c4e519624d611fe187a5b3afe4ea"}
for _k in list(EXPECT):
    if os.environ.get("R1G_CDL_SHA_" + _k):
        EXPECT[_k] = os.environ["R1G_CDL_SHA_" + _k]
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


DEFINED = {}          # subcircuit name (lower case) -> normalised body
DUPS = []


def blocks_dedup(text, src):
    """drop .SUBCKT ... .ENDS blocks already defined by an earlier part (identical text required)."""
    out, cur, name = [], None, None
    for ln in text.splitlines():
        u = ln.strip().upper()
        if cur is None and u.startswith(".SUBCKT"):
            cur, name = [ln], ln.split()[1].lower()
            continue
        if cur is not None:
            cur.append(ln)
            if u.startswith(".ENDS"):
                norm = " ".join(" ".join(l.split()) for l in cur if l.strip() and not l.lstrip().startswith("*"))
                if name in DEFINED:
                    if DEFINED[name] != norm:
                        sys.exit("%s: subcircuit %s differs from its earlier definition" % (src, name))
                    DUPS.append({"subckt": name, "dropped_from": src})
                else:
                    DEFINED[name] = norm
                    out.extend(cur)
                cur = None
            continue
        out.append(ln)
    if cur is not None:
        sys.exit("%s: unterminated subcircuit %s" % (src, name))
    return "\n".join(out)


def rel(p):
    if p.startswith(REPO):
        return os.path.relpath(p, REPO)
    return "<G1_RESULTS_ROOT>/r1_top/<run>/inputs/ofrecord/" + os.path.basename(p)


parts, ports = [], {}
ct = open(ctrl_cdl).read()
parts.append(blocks_dedup(strip_end(ct), "r1_ctrl_top"))
ports.update(subckts(ct))
for name, p in SRC.items():
    if name in EXPECT and sha(p) != EXPECT[name]:
        sys.exit("%s: LVS reference %s is not the netlist of record" % (name, sha(p)))
    t = open(p).read()
    parts.append("* ---- %s (%s, sha256 %s)\n" % (name, rel(p), sha(p)) + blocks_dedup(strip_end(t), name))
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
    f.write("* r1_top LVS reference (assembly try g, track T8e), generated by make_top_cdl_g.py\n")
    f.write("\n\n".join(parts) + "\n")
info = {"output": os.path.basename(out), "output_sha256": sha(out),
        "inputs": {rel(p): sha(p) for p in list(SRC.values()) + [RING]},
        "ctrl_cdl_sha256": sha(ctrl_cdl), "assembly_json_sha256": sha(asm_json),
        "ring_pins": ring_pins, "instances": table, "duplicate_subckts_dropped": DUPS,
        "subckts": sorted(DEFINED)}
json.dump(info, open(out_json, "w"), indent=1)
print("written", out, info["output_sha256"])

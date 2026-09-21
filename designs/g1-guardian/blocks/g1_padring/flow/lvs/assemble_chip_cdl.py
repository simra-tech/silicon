#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Assemble the chip CDL of g1_chip_top from the flow's powered Verilog netlist,
the PDK standard-cell and IO CDLs and the macro CDLs of record.

  python3 assemble_chip_cdl.py <chip.pnl.v> <out.cdl> --macro <name>=<cdl> ... \
      --lib <cdl> ... [--digital <g1_digital.pnl.v>]

* every <lib> CDL is copied in full (PDK sg13g2_stdcell.cdl, sg13g2_io.cdl);
* every --macro CDL is copied in full (its top subcircuit must be named <name>,
  pin order taken from its .SUBCKT line);
* --digital: the digital macro's own powered Verilog netlist is converted to a
  subcircuit g1_digital (standard cells from the PDK CDL), so the chip CDL is
  transistor-level everywhere except the analog macros' own CDL content;
* the bondpad cell gets an empty subcircuit (metal only);
* sg13g2_IOPadAnalog: `padbare` is the same conductor as `pad` (ip/sg13g2_io_padbare),
  the nets are merged as in pnl2cdl.py.
"""
import re
import sys

args = sys.argv[1:]
pnl, out = args[0], args[1]
macros, libs, digital = {}, [], None
i = 2
while i < len(args):
    if args[i] == "--macro":
        n, f = args[i + 1].split("=", 1); macros[n] = f; i += 2
    elif args[i] == "--lib":
        libs.append(args[i + 1]); i += 2
    elif args[i] == "--digital":
        digital = args[i + 1]; i += 2
    else:
        sys.exit("bad argument " + args[i])


def subckt_pins(text):
    """{name: [pins]} for every .SUBCKT (with + continuation lines)."""
    res = {}
    lines = text.splitlines()
    k = 0
    while k < len(lines):
        ln = lines[k]
        if ln.upper().startswith(".SUBCKT"):
            toks = ln.split()
            while k + 1 < len(lines) and lines[k + 1].startswith("+"):
                k += 1; toks += lines[k].split()[1:]
            res[toks[1]] = toks[2:]
        k += 1
    return res


def san(n):
    n = n.strip()
    if n.startswith("\\"):
        n = n[1:].strip()
    return re.sub(r"[.\[\]]", "_", n)


SAME_CONDUCTOR = {"sg13g2_IOPadAnalog": ("padbare", "pad")}


def verilog_to_subckt(vfile, pin_order, extra_cells):
    """Convert one powered gate-level Verilog module into a CDL subcircuit."""
    text = open(vfile).read()
    m = re.search(r"module\s+(\w+)\s*\((.*?)\);", text, re.S)
    top = m.group(1)
    body = re.sub(r"//.*", "", text[m.end():])
    # vector ports (input/output/inout [N:M] name) are expanded MSB..LSB to name[i]
    vec = {}
    for d in re.finditer(r"\b(?:input|output|inout)\s*\[(\d+):(\d+)\]\s*([\w\\\[\]. ]+?)\s*;", body):
        hi, lo = int(d.group(1)), int(d.group(2))
        for nm in d.group(3).split(","):
            vec[san(nm)] = (hi, lo)
    ports = []
    for p in m.group(2).replace("\n", " ").split(","):
        p = san(p)
        if not p:
            continue
        if p in vec:
            hi, lo = vec[p]
            ports += [san(f"{p}[{i}]") for i in range(hi, lo - 1, -1)]
        else:
            ports.append(p)
    inst_re = re.compile(r"^\s*(\w+)\s+(\\\S+\s|\S+)\s*\((.*?)\);", re.S | re.M)
    # a connection is .pin(net) or .bus({netN, ..., net0}) (concatenation, MSB first)
    conn_re = re.compile(r"\.(\w+)\s*\(\s*(\{[^}]*\}|[^(){}]*)\)")
    alias, insts = {}, []
    for mm in inst_re.finditer(body):
        cell, inst, conns = mm.group(1), san(mm.group(2)), mm.group(3)
        if cell in ("wire", "input", "output", "inout", "assign", "module"):
            continue
        conn = {}
        for k, v in conn_re.findall(conns):
            v = v.strip()
            if v.startswith("{"):
                bits = [b for b in v.strip("{}").replace("\n", " ").split(",") if b.strip()]
                n = len(bits)
                for idx, b in enumerate(bits):          # MSB first
                    conn[san(f"{k}[{n - 1 - idx}]")] = san(b)
            else:
                conn[san(k)] = san(v) if v else ""
        if cell in SAME_CONDUCTOR:
            a, b = SAME_CONDUCTOR[cell]
            if conn.get(a) and conn.get(b) and conn[a] != conn[b]:
                alias[conn[a]] = conn[b]
        insts.append((cell, inst, conn))

    def res(n):
        while n in alias:
            n = alias[n]
        return n

    nc = 0
    lines = [f".SUBCKT {top} " + " ".join(res(p) for p in ports)]
    counts = {}
    for cell, inst, conn in insts:
        if cell in extra_cells:
            order = extra_cells[cell]
        elif cell in pin_order:
            order = pin_order[cell]
        else:
            sys.exit(f"{vfile}: no subcircuit for cell {cell}")
        nets = []
        for p in order:
            key = p
            # Verilog bus pins are dac_soft[3]; CDL pins may be dac_soft[3] too
            v = conn.get(san(key), "")
            if v == "":
                nc += 1; v = f"_nc{nc}"
            nets.append(res(v))
        lines.append(f"X{inst} " + " ".join(nets) + f" / {cell}")
        counts[cell] = counts.get(cell, 0) + 1
    lines.append(".ENDS")
    return top, "\n".join(lines) + "\n", counts, nc


lib_texts = [open(f).read() for f in libs]
pin_order = {}
for t in lib_texts:
    pin_order.update(subckt_pins(t))
macro_texts = {}
for name, f in macros.items():
    t = open(f).read()
    pins = subckt_pins(t)
    if name not in pins:
        sys.exit(f"{f}: no .SUBCKT {name}")
    macro_texts[name] = t
    pin_order[name] = pins[name]
pin_order["bondpad_70x70_tm1"] = ["pad"]

with open(out, "w") as f:
    f.write("* chip CDL of g1_chip_top assembled by assemble_chip_cdl.py\n")
    f.write("* libraries: " + " ".join(libs) + "\n")
    for t in lib_texts:
        f.write(t + "\n")
    f.write(".SUBCKT bondpad_70x70_tm1 pad\n*.PININFO pad:B\n* metal-only bond pad\n.ENDS\n\n")
    for name, t in macro_texts.items():
        f.write(f"* ---- macro {name} ({macros[name]}) ----\n" + t + "\n")
    if digital:
        top, txt, counts, nc = verilog_to_subckt(digital, pin_order, {})
        pin_order[top] = re.search(r"\.SUBCKT \w+ (.*)", txt).group(1).split()
        f.write(f"* ---- digital macro {top} from {digital} ----\n" + txt + "\n")
        print(f"{top}: {sum(counts.values())} instances, {nc} unconnected pins")
    top, txt, counts, nc = verilog_to_subckt(pnl, pin_order, {})
    f.write("* ---- chip ----\n" + txt)
    print(f"{top}: {sum(counts.values())} instances, {nc} unconnected pins")
    for c in sorted(counts):
        if not c.startswith("sg13g2_decap") and not c.startswith("sg13g2_fill"):
            print(f"  {counts[c]:6d} {c}")

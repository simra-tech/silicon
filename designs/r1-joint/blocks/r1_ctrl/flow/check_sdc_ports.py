#!/usr/bin/env python3
"""Check flow/r1_ctrl.sdc against the ports of rtl/r1_ctrl_top.v (revision 0.5).
Every port bit must be a clock, have an input or output delay, or be a false-path source,
and every get_ports pattern in the SDC must match at least one port bit (no stale names).
Writes the port list (name, direction, width, constraint) as JSON. Exit 1 on any gap.
Usage: check_sdc_ports.py <rtl/r1_ctrl_top.v> <flow/r1_ctrl.sdc> <out.json>
SPDX-License-Identifier: Apache-2.0"""
import json
import re
import sys


def ports(vfile):
    src = open(vfile).read()
    head = src[src.index("module r1_ctrl_top"):]
    head = head[head.index(") (") + 3: head.index(");")]
    head = re.sub(r"//[^\n]*", "", head)
    out = []
    # split declarations: keep direction/width across comma-separated names
    cur_dir, cur_w = None, 1
    for tok in re.finditer(r"(input|output)?\s*(?:wire|reg)?\s*(\[\s*(\d+)\s*:\s*(\d+)\s*\])?\s*([A-Za-z_]\w*)\s*(?:,|$)", head.replace("\n", " ")):
        d, _, msb, lsb, name = tok.groups()
        if d:
            cur_dir = d
            cur_w = (int(msb) - int(lsb) + 1) if msb is not None else 1
        out.append((name, cur_dir, cur_w))
    return out


def bits(plist):
    for name, d, w in plist:
        if w == 1:
            yield name, d, name
        else:
            for i in range(w):
                yield name, d, f"{name}[{i}]"


def pat_re(p):
    return re.compile("^" + "".join(".*" if c == "*" else re.escape(c) for c in p) + "$")


def sdc_patterns(sdc):
    text = re.sub(r"\\\n", " ", open(sdc).read())
    text = "\n".join(l.split("#")[0] for l in text.splitlines())
    res = []   # (command, kind, [patterns])
    for line in text.splitlines():
        line = line.strip()
        if "get_ports" not in line:
            continue
        cmd = line.split()[0]
        if cmd == "set":
            cmd = "set_var"
        kind = None
        if cmd == "create_clock":
            kind = "clock"
        elif cmd == "set_input_delay":
            kind = "input_delay"
        elif cmd == "set_output_delay":
            kind = "output_delay"
        elif cmd == "set_false_path":
            kind = "false_path"
        elif cmd == "set_var":
            kind = "output_delay_var"   # `set clk_outputs [get_ports ...]` used by set_output_delay $clk_outputs
        for m in re.finditer(r"get_ports\s+(\{[^}]*\}|\S+?)\]", line):
            pats = m.group(1).strip("{}").split()
            res.append((cmd, kind, pats))
    return res


def main():
    vfile, sdc, out = sys.argv[1:4]
    plist = ports(vfile)
    allbits = list(bits(plist))
    cons = {b: set() for _, _, b in allbits}
    stale = []
    for cmd, kind, pats in sdc_patterns(sdc):
        for p in pats:
            rx = pat_re(p)
            hit = [b for _, _, b in allbits if rx.match(b)]
            if not hit:
                stale.append((cmd, p))
            for b in hit:
                cons[b].add("output_delay" if kind == "output_delay_var" else kind)
    gaps = []
    for name, d, b in allbits:
        k = cons[b]
        ok = (d == "input" and (k & {"clock", "input_delay", "false_path"})) or (d == "output" and "output_delay" in k)
        if not ok:
            gaps.append(b)
    res = dict(ports=[dict(name=n, direction=d, width=w) for n, d, w in plist],
               port_bits=len(allbits),
               constrained={n: sorted(set().union(*[cons[b] for nm, _, b in allbits if nm == n])) for n, _, _ in plist},
               unconstrained_bits=gaps, stale_patterns=stale,
               disposition="passed" if not gaps and not stale else "FAILED")
    json.dump(res, open(out, "w"), indent=1)
    print(f"{len(plist)} ports, {len(allbits)} bits, unconstrained {len(gaps)}, stale patterns {len(stale)}: {res['disposition']}")
    for g in gaps:
        print("unconstrained:", g)
    for s in stale:
        print("stale pattern:", s)
    sys.exit(0 if res["disposition"] == "passed" else 1)


if __name__ == "__main__":
    main()

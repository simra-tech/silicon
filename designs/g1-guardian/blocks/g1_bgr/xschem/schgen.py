"""Minimal xschem .sch/.sym writer used by the G1_BGR and G1_T2F schematics.

Instances are placed on a grid; every device pin gets a lab_pin carrying its net
name, so connectivity is by label, not by drawn wires. The resulting .sch files
netlist with `xschem -n -q -x` and are the source for the LVS netlists.
"""

# pin offsets (x, y) of the PDK symbols, in xschem units, relative to the instance origin
PINS = {
    "sg13g2_pr/sg13_hv_pmos.sym": {"D": (20, 30), "G": (-20, 0), "S": (20, -30), "B": (20, 0)},
    "sg13g2_pr/sg13_lv_pmos.sym": {"D": (20, 30), "G": (-20, 0), "S": (20, -30), "B": (20, 0)},
    "sg13g2_pr/sg13_hv_nmos.sym": {"D": (20, -30), "G": (-20, 0), "S": (20, 30), "B": (20, 0)},
    "sg13g2_pr/sg13_lv_nmos.sym": {"D": (20, -30), "G": (-20, 0), "S": (20, 30), "B": (20, 0)},
    "sg13g2_pr/npn13G2.sym": {"C": (20, -30), "B": (-20, 0), "E": (20, 30), "S": (20, 0)},
    "sg13g2_pr/rppd.sym": {"P": (0, -30), "M": (0, 30)},
    "sg13g2_pr/rhigh.sym": {"P": (0, -30), "M": (0, 30)},
    "sg13g2_pr/cap_cmim.sym": {"c0": (0, -30), "c1": (0, 30)},
}

HEADER = "v {xschem version=3.4.8RC file_version=1.3}\nG {}\nK {}\nV {}\nS {}\nE {}\n"


def _props(d):
    return " ".join(f"{k}={v}" for k, v in d.items())


def write_sch(path, title, ports, instances, cols=8, pitch=(160, 140)):
    """ports: list of (name, dir) with dir in {in, out, inout}.
    instances: list of (symbol, name, {pin: net}, {param: value})."""
    out = [HEADER]
    out.append(f"T {{{title}}} 0 -220 0 0 0.4 0.4 {{}}\n")
    # ports along the top row
    for i, (name, d) in enumerate(ports):
        sym = {"in": "devices/ipin.sym", "out": "devices/opin.sym", "inout": "devices/iopin.sym"}[d]
        out.append(f"C {{{sym}}} {i * 80} -160 0 0 {{name=p{i} lab={name}}}\n")
    lab = 0
    for k, (sym, name, pins, params) in enumerate(instances):
        col, row = k % cols, k // cols
        x, y = 60 + col * pitch[0], 40 + row * pitch[1]
        out.append(f"C {{{sym}}} {x} {y} 0 0 {{name={name} {_props(params)}}}\n")
        for pin, net in pins.items():
            dx, dy = PINS[sym][pin]
            out.append(f"C {{devices/lab_pin.sym}} {x + dx} {y + dy} 0 0 {{name=l{lab} sig_type=std_logic lab={net}}}\n")
            lab += 1
    with open(path, "w") as f:
        f.write("".join(out))


def write_sym(path, cell, ports):
    """Box symbol with one pin per port, inputs on the left, outputs on the right."""
    ins = [p for p in ports if p[1] in ("in", "inout")]
    outs = [p for p in ports if p[1] == "out"]
    h = max(len(ins), len(outs)) * 20 + 20
    out = [HEADER.replace("K {}", f"K {{type=subcircuit\nformat=\"@name @pinlist @symname\"\ntemplate=\"name=x1\"}}")]
    out.append(f"B 4 -60 -{h/2} 60 {h/2} {{}}\n")
    out.append(f"T {{{cell}}} -55 -{h/2 + 15} 0 0 0.3 0.3 {{}}\n")
    for i, (name, d) in enumerate(ins):
        y = -h / 2 + 20 + i * 20
        out.append(f"L 4 -80 {y} -60 {y} {{}}\n")
        out.append(f"B 5 -82.5 {y - 2.5} -77.5 {y + 2.5} {{name={name} dir={d}}}\n")
        out.append(f"T {{{name}}} -55 {y - 4} 0 0 0.2 0.2 {{}}\n")
    for i, (name, d) in enumerate(outs):
        y = -h / 2 + 20 + i * 20
        out.append(f"L 4 60 {y} 80 {y} {{}}\n")
        out.append(f"B 5 77.5 {y - 2.5} 82.5 {y + 2.5} {{name={name} dir={d}}}\n")
        out.append(f"T {{{name}}} 55 {y - 4} 0 1 0.2 0.2 {{}}\n")
    with open(path, "w") as f:
        f.write("".join(out))

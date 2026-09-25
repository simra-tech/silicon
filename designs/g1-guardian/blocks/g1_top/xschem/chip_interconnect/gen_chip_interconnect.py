"""Chip-level interconnect sheet of the G1 chip of record (g1_chip_top, 1414 um).

Draws the macro, level-shifter, tie, pad-cell and bond-pad instances of the top-level subcircuit of
../../../g1_padring/netlist/g1_chip_top_1414_r2.cdl (41d47877; the drawn instances are
identical in the r1 CDL g1_chip_top_1414.cdl af5a4dbd) with their instance names and nets as
they are in that netlist; every block is a black-box symbol (type=primitive) whose pin order is the
subcircuit pin order in the CDL.  Not drawn: the standard fill/decap/antenna cells, the IO corner and
IO filler cells of the same subcircuit (listed with counts in the title block).  The comparison of
the drawn instances with the CDL is recorded in designs/g1-guardian/review/schematics-readability-20260925.

Run from this directory: python3 gen_chip_interconnect.py
"""
import collections
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.environ.get("CHIP_OUT_DIR", HERE)
CDL = os.path.join(HERE, "..", "..", "..", "g1_padring", "netlist", "g1_chip_top_1414_r2.cdl")


def _find_flow():
    d = HERE
    while not os.path.isdir(os.path.join(d, "flow", "schematic")):
        if os.path.dirname(d) == d:
            raise SystemExit("flow/schematic not found above " + HERE)
        d = os.path.dirname(d)
    return os.path.join(d, "flow", "schematic")


sys.path.insert(0, _find_flow())
from xsch_readable import Sheet, write_symbol  # noqa: E402

PADPFX = "G1_VSS_DERIVATIVE__sg13g2_"
DRAWN = {"g1_bgr", "g1_digital", "g1_dose_macro", "g1_dut_macro", "g1_gate", "g1_ls_up", "g1_osc", "g1_sense", "g1_t2f",
         "g1_trip", "sg13g2_tiehi", "bondpad_70x70_tm1"} | {PADPFX + c for c in (
             "IOPadAnalog", "IOPadIn", "IOPadOut4mA", "IOPadOut16mA", "IOPadOut30mA", "IOPadVdd", "IOPadVss", "IOPadIOVdd", "IOPadIOVss")}


def read_cdl():
    txt = open(CDL).read().replace("\n+", " ")
    pins = {}
    for m in re.finditer(r"^\.SUBCKT\s+(\S+)([^\n]*)", txt, re.M | re.I):
        pins[m.group(1)] = m.group(2).split()
    top = re.search(r"^\.SUBCKT g1_chip_top .*?^\.ENDS", txt, re.M | re.S | re.I).group(0).splitlines()
    ports = top[0].split()[2:]
    insts, skipped = [], collections.Counter()
    for line in top[1:]:
        t = line.split()
        if not t or t[0].startswith(".") or t[0].startswith("*"):
            continue
        cell = t[t.index("/") + 1] if "/" in t else t[-1]
        nets = t[1:t.index("/")] if "/" in t else t[1:-1]
        if cell in DRAWN:
            insts.append((t[0], cell, nets))
        else:
            skipped[cell] += 1
    return ports, pins, insts, skipped


def pin_sides(cell, pins):
    """Symbol sides by function: inputs left, outputs right, supplies top/bottom."""
    sup_top = [p for p in pins if p.lower() in ("vdd", "vdda", "vdd12", "iovdd")]
    sup_bot = [p for p in pins if p.lower() in ("vss", "iovss") or p.startswith("G1_EXPLICIT")]
    rest = [p for p in pins if p not in sup_top + sup_bot]
    outs = {"g1_bgr": ["vref", "iptat", "pbias", "pcasc", "vbe", "dvbe"], "g1_sense": ["isense", "vped", "vref_buf"],
            "g1_trip": ["cmp_soft", "cmp_hard"], "g1_gate": ["gate_core", "fault_core", "tripped"], "g1_ls_up": ["out"],
            "g1_osc": ["osc_clk"], "g1_t2f": ["fout"], "sg13g2_tiehi": ["L_HI"],
            "g1_digital": [p for p in rest if p not in ("cmp_hard", "cmp_soft", "en", "osc_clk", "por_n", "sclk", "sdi", "tripped")],
            "g1_dose_macro": rest, "g1_dut_macro": rest, "bondpad_70x70_tm1": rest}
    if cell.startswith(PADPFX):
        return dict(left=[p for p in rest if p == "pad"], right=[p for p in rest if p != "pad"], top=sup_top, bottom=sup_bot)
    o = outs[cell]
    return dict(left=[p for p in rest if p not in o], right=[p for p in rest if p in o], top=sup_top, bottom=sup_bot)


def symfile(cell):
    """Local black-box symbol file; "chip_" prefix so that no PDK library symbol of the same name
    (e.g. sg13g2_stdcells/sg13g2_tiehi.sym) is picked up instead.  The netlist keeps the CDL cell name."""
    return "chip_" + cell + ".sym"


def safe(p):
    return p.replace("[", "_").replace("]", "")


def main():
    ports, pins, insts, skipped = read_cdl()
    cells = sorted(set(c for _, c, _ in insts))
    for c in cells:
        ps = [safe(p) for p in pins[c]]
        sides = dict((k, [safe(p) for p in v]) for k, v in pin_sides(c, pins[c]).items())
        label = c.replace(PADPFX, "") if c.startswith(PADPFX) else c
        write_symbol(os.path.join(OUT, symfile(c)), c, ps, {}, label=label, ktype="primitive", netlist_name=c, **sides)
    # placement: pads on the west/east edges and the south row, supply pads on the north row
    pos = {
        "Xpad08_sense_p": (400, -1900), "Xpad09_sense_n": (400, -1700), "Xpad18_vref": (400, -1500),
        "Xpad13_trip_set": (400, -1300), "Xpad12_en": (400, -1100), "Xpad14_sclk": (400, -900), "Xpad15_sdi": (400, -700),
        "Xpad07_vdda": (400, -2100),
        "Xpad10_gate": (4200, -1900), "Xpad11_fault_n": (4200, -1700), "Xpad16_sdo": (4200, -1500), "Xpad17_temp_out": (4200, -1300),
        "Xpad19_g_shared": (1000, -150), "Xpad20_d_std": (1400, -150), "Xpad21_d_elt": (1800, -150),
        "Xpad22_hbt_e": (2400, -150), "Xpad23_hbt_b": (2800, -150), "Xpad24_hbt_c": (3200, -150),
        "Xpad01_vdd": (1000, -2450), "Xpad02_vss": (1400, -2450), "Xpad03_iovdd": (1800, -2450), "Xpad04_iovss": (2200, -2450),
        "Xpad05_vss": (2600, -2450), "Xpad06_iovss": (3000, -2450),
        "Xi_core_u_bgr": (1100, -1250), "Xi_core_u_sense": (1500, -1800), "Xi_core_u_trip": (2150, -1450),
        "Xi_core_u_digital": (2950, -1250), "Xi_core_u_gate": (3700, -1850), "Xi_core_u_osc": (2150, -700),
        "Xi_core_u_t2f": (3700, -1100), "Xi_core_u_ls_en": (3350, -500), "Xi_core_u_ls_mode": (3350, -350),
        "Xi_core_u_ls_r4": (3350, -650), "Xi_core_u_dose": (1400, -450), "Xi_core_u_dut": (2800, -450),
        "Xi_core_u_digital_1": (2600, -500),
    }
    s = Sheet("g1_chip_top")
    I = {}
    west = [n for n in pos if pos[n][0] == 400]
    east = [n for n in pos if pos[n][0] == 4200]
    for name, cell, nets in insts:
        if cell == "bondpad_70x70_tm1":
            continue
        x, y = pos[name]
        flip = 1 if name in east else 0
        I[name] = s.inst(name, symfile(cell), x, y, dict(zip([safe(p) for p in pins[cell]], nets)), flip=flip,
                         sympath=os.path.join(OUT, symfile(cell)))
    # the digital macro's por_n is tied high by Xi_core_u_digital_1 (net "net")
    t, d = I["Xi_core_u_digital_1"], I["Xi_core_u_digital"]
    s.wire(t["L_HI"], (t["L_HI"][0] + 20, t["L_HI"][1]), (t["L_HI"][0] + 20, d["por_n"][1]), d["por_n"])
    # bond pads next to their pad cells; the chip ports on the bond pads
    padnet = {}
    for name, cell, nets in insts:
        if cell != "bondpad_70x70_tm1":
            continue
        tag = name.replace("XIO_BOND_", "X")
        pc = I[tag]
        if tag in west or tag in east:
            pt = pc["pad"]
            bx = pt[0] - 120 if tag in west else pt[0] + 120
            I[name] = s.inst(name, symfile(cell), bx, pt[1], {"pad": nets[0]}, flip=0 if tag in west else 1,
                             sympath=os.path.join(OUT, symfile(cell)))
            s.wire(I[name]["pad"], pt)
        else:
            ox, oy = pc.origin
            I[name] = s.inst(name, symfile(cell), ox + 190, oy + (110 if oy > -1000 else -110), {"pad": nets[0]},
                             sympath=os.path.join(OUT, symfile(cell)))
        padnet[nets[0]] = I[name]["pad"]
    for p in ports:
        pt = padnet[p]
        s.port(p, (pt[0] - 60, pt[1]) if pt[0] < 2000 else (pt[0] + 60, pt[1]), "inout", flip=1 if pt[0] < 2000 else 0)
        s.wire(pt, (pt[0] - 60, pt[1]) if pt[0] < 2000 else (pt[0] + 60, pt[1]))
    s.frame(120, -2250, 620, -560, "west IO: analog + 1.2 V inputs")
    s.frame(3960, -2050, 4480, -1150, "east IO: outputs")
    s.frame(700, -2050, 3900, -250, "core: BGR -> SENSE -> TRIP -> digital -> GATE; OSC clock; T2F; level shifters; test structures")
    note = ", ".join("%d %s" % (v, k.replace(PADPFX, "")) for k, v in sorted(skipped.items(), key=lambda kv: -kv[1]))
    s.text("Every pin carries the net name of the CDL (i_core_* = core nets, _ncN = unconnected pad core pins).  VREF pad = i_core_vref (bandgap output, "
           "unbuffered); TRIP_SET pad core net i_core_trip_set has no core load on this chip.\n"
           "Not drawn (same subcircuit): " + note + ".", 120, 80)
    s.title_block(120, -3000, "g1_chip_top", "chip-level interconnect: analog macros, digital macro, level shifters, pad ring",
                  "the %d macro / tie / pad / bond-pad instances of g1_padring/netlist/g1_chip_top_1414_r2.cdl sha256 41d47877" % len(insts),
                  "top level of the chip of record (r2); blocks are black boxes, see the block sheets",
                  width=3000)
    s.write(os.path.join(OUT, "g1_chip_top.sch"))
    print("drew %d instances; skipped %s" % (len(insts), dict(skipped)))


if __name__ == "__main__":
    main()

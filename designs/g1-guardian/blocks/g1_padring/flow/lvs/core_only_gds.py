# SPDX-License-Identifier: Apache-2.0
"""Core-only view of the chip GDS for a KLayout LVS that excludes the IO ring.

  klayout -b -rd gds=<chip.gds> -rd out=<core.gds> -rd lef=<sg13g2_io.lef> \
          -rd defp=<chip.def> -r core_only_gds.py

1. Standard-cell variants: the chip stream-out keeps the standard cells that
   arrive inside a macro GDS under renamed cells (`sg13g2_nand2_1$1`, ...)
   next to the PDK cells of the same name placed by the chip flow. The LVS
   deck flattens cells with no schematic counterpart, which would make the
   layout `g1_digital` flat while its CDL keeps the cells, and KLayout then
   skips the comparison ("subcircuits failed to compare"). Every `sg13g2_*$n`
   cell that is geometrically identical to its base cell is folded onto the
   base cell; one without a base cell is renamed. Non-identical variants are
   reported and left alone.
2. Pad-terminal labels: for every removed pad the net on its core-side
   terminal (p2c, c2p, padres, padbare) is labelled on the routed wire
   nearest the pad (DEF NETS routing), using the CDL port name of the core
   subcircuit (`assemble_chip_cdl.py` names: `.`, `[`, `]` -> `_`; the
   padbare net of an sg13g2_IOPadAnalog carries the pad's own net name).
   VDD, VSS and VDDA are labelled on their longest top-metal stripe inside
   the core (DEF SPECIALNETS).
3. The IO cells, fillers, corners, bondpads and the seal ring are removed,
   together with every top-cell shape lying entirely outside the pad ring's
   inner edge (the DEF pin squares on the bondpads and their texts); the
   top cell is renamed `g1_core`.
"""
import re
import pya

gds, out, lef_path, def_path = globals()["gds"], globals()["out"], globals()["lef"], globals()["defp"]
ly = pya.Layout(); ly.read(gds)
top = ly.cell("g1_chip_top")
dbu = ly.dbu


def san(n):
    return re.sub(r"[.\[\]]", "_", n)


# --- 1. fold the standard-cell variants onto the PDK cells ------------------
def same_geometry(a, b):
    # merged geometry and texts per layer (the chip GDS carries duplicated,
    # overlapping copies of the std-cell shapes, hence the merge, not a count)
    if a.bbox() != b.bbox() or a.child_instances() != b.child_instances():
        return False
    for li in ly.layer_indexes():
        ra = pya.Region(a.begin_shapes_rec(li)); rb = pya.Region(b.begin_shapes_rec(li))
        if not (ra ^ rb).is_empty():
            return False
        ta = {(s.text_string, s.text_trans.disp.x, s.text_trans.disp.y) for s in a.shapes(li).each() if s.is_text()}
        tb = {(s.text_string, s.text_trans.disp.x, s.text_trans.disp.y) for s in b.shapes(li).each() if s.is_text()}
        if ta != tb:
            return False
    return True

folded, renamed, differing = {}, [], []
for c in list(ly.each_cell()):
    m = re.match(r"(sg13g2_\w+?)\$\d+$", c.name)
    if not m:
        continue
    base = ly.cell(m.group(1))
    if base is None:
        renamed.append((c.name, m.group(1))); c.name = m.group(1); continue
    if not same_geometry(c, base):
        differing.append(c.name); continue
    n = 0
    for pidx in list(c.each_parent_cell()):
        parent = ly.cell(pidx)
        for inst in list(parent.each_inst()):
            if inst.cell_index == c.cell_index():
                ci = inst.cell_inst; ci.cell_index = base.cell_index(); parent.replace(inst, ci); n += 1
    folded[c.name] = n
    ly.delete_cell(c.cell_index())
print(f"std-cell variants folded onto their PDK cells: {len(folded)} cells, {sum(folded.values())} instances")
print("std-cell variants renamed (no base cell):", renamed)
print("std-cell variants left alone (geometry differs from the base cell):", differing)

# --- pad instances and their nets from the DEF ------------------------------
D = open(def_path).read()
comp = D[D.index("COMPONENTS"):D.index("END COMPONENTS")]
pads = {}
for m in re.finditer(r"-\s+(\S+)\s+(sg13g2_IOPad\w+)\s*\+\s*FIXED\s*\(\s*(-?\d+)\s+(-?\d+)\s*\)\s*(\w+)", comp):
    pads[m.group(1)] = (m.group(2), int(m.group(3)), int(m.group(4)), m.group(5))
pin_net, routing = {}, {}
SEG = re.compile(r"(?:ROUTED|NEW)\s+(\w+)\s+(?:(\d+)\s+)?(?:\+\s+SHAPE\s+\w+\s+)?\(\s*(-?\d+)\s+(-?\d+)\s*\)\s*(?:\(\s*(-?\d+|\*)\s+(-?\d+|\*)\s*\))?")
for sec_start, sec_end in (("\nNETS", "END NETS"), ("SPECIALNETS", "END SPECIALNETS")):
    sec = D[D.index(sec_start):D.index(sec_end)]
    for rec in re.split(r"\n\s*-\s+", sec)[1:]:      # one record per "- <net> ... ;"
        net = rec.split()[0]
        head = rec.split("+")[0]                      # pin list precedes the first "+ USE/ROUTED"
        for inst, pin in re.findall(r"\(\s*(\S+)\s+(\S+)\s*\)", head):
            if inst != "PIN":
                pin_net[(inst, pin)] = net
        segs = []
        for m in SEG.finditer(rec):
            lay, w, x1, y1, x2, y2 = m.groups()
            if x2 is None:
                continue
            x1, y1 = int(x1), int(y1)
            x2 = x1 if x2 == "*" else int(x2); y2 = y1 if y2 == "*" else int(y2)
            segs.append((lay, x1, y1, x2, y2))
        routing.setdefault(net, []).extend(segs)

# --- core-side pin geometry from the LEF (cell coordinates) ------------------
L = open(lef_path).read()
core_pins = {}   # (macro, pin) -> [(layer, x1, y1, x2, y2)] in um, rects reaching the cell's core edge
for mm in re.finditer(r"MACRO\s+(sg13g2_IOPad\w+)(.*?)END\s+\1", L, re.S):
    macro, body = mm.group(1), mm.group(2)
    for pm in re.finditer(r"PIN\s+(\w+)\s+(.*?)END\s+\1", body, re.S):
        pin, pb = pm.group(1), pm.group(2)
        if pin not in ("p2c", "c2p", "padres", "padbare", "c2p_en"):
            continue
        rects = re.findall(r"LAYER\s+(Metal[23])\s*;\s*RECT\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)", pb)
        tops = [(l, *map(float, r)) for l, *r in rects if float(r[3]) >= 179.9]
        if tops:
            core_pins[(macro, pin)] = tops

def xform(orient, ox, oy, w, h, x, y):
    # LEF/DEF orientation of an 80 x 180 cell placed with lower-left (ox, oy)
    if orient == "N":  return ox + x, oy + y
    if orient == "S":  return ox + w - x, oy + h - y
    if orient == "W":  return ox + h - y, oy + x
    if orient == "E":  return ox + y, oy + w - x
    if orient == "FN": return ox + w - x, oy + y
    if orient == "FS": return ox + x, oy + h - y
    if orient == "FW": return ox + y, oy + x
    if orient == "FE": return ox + h - y, oy + w - x
    raise ValueError(orient)

# --- 2. labels ---------------------------------------------------------------
LAYER_TXT = {"Metal1": (8, 25), "Metal2": (10, 25), "Metal3": (30, 25), "Metal4": (50, 25),
             "Metal5": (67, 25), "TopMetal1": (126, 25), "TopMetal2": (134, 25)}

def put_label(name, lay, x, y):
    top.shapes(ly.layer(*LAYER_TXT[lay])).insert(pya.Text(name, pya.Trans(pya.Point(int(x), int(y)))))

def seg_mid_near(segs, px, py):
    best = None
    for lay, x1, y1, x2, y2 in segs:
        if lay not in LAYER_TXT:
            continue
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        d = (mx - px) ** 2 + (my - py) ** 2
        if best is None or d < best[0]:
            best = (d, lay, mx, my)
    return best

written, missing = [], []
for inst, (macro, ox, oy, orient) in sorted(pads.items()):
    for pin in ("p2c", "c2p", "padres", "padbare"):
        key = (inst, pin)
        if key not in pin_net:
            continue
        net = pin_net[key]
        if net in ("VDD", "VSS", "VDDA", "IOVDD", "IOVSS"):
            continue                                   # supplies: labelled on the PDN below
        name = san(pin_net[(inst, "pad")] if (pin == "padbare" and macro == "sg13g2_IOPadAnalog") else net)
        if (macro, pin) not in core_pins:
            missing.append((inst, pin, net, "no LEF pin geometry")); continue
        lname, x1, y1, x2, y2 = core_pins[(macro, pin)][-1]
        X, Y = xform(orient, ox / 1000, oy / 1000, 80.0, 180.0, (x1 + x2) / 2, 180.0)
        hit = seg_mid_near(routing.get(net, []), X * 1000, Y * 1000)
        if hit is None:
            missing.append((inst, pin, net, "net has no routing")); continue
        _, lay, mx, my = hit
        put_label(name, lay, mx, my)
        written.append((inst, pin, net, name, lay, mx / 1000, my / 1000))

CORE = (364000, 364000, 986000, 986000)
for net in ("VDD", "VSS", "VDDA"):
    best = None
    for lay, x1, y1, x2, y2 in routing.get(net, []):
        if lay not in ("TopMetal1", "TopMetal2"):
            continue
        if not (CORE[0] <= min(x1, x2) and max(x1, x2) <= CORE[2] and CORE[1] <= min(y1, y2) and max(y1, y2) <= CORE[3]):
            continue
        ln = abs(x2 - x1) + abs(y2 - y1)
        if best is None or ln > best[0]:
            best = (ln, lay, (x1 + x2) / 2, (y1 + y2) / 2)
    if best is None:
        missing.append(("-", "-", net, "no top-metal stripe inside the core")); continue
    _, lay, mx, my = best
    put_label(net, lay, mx, my)
    written.append(("(PDN)", "-", net, net, lay, mx / 1000, my / 1000))

for w in written:
    print("label %-22s <- %s %s (net %s) on %s at (%.3f, %.3f)" % (w[3], w[0], w[1], w[2], w[4], w[5], w[6]))
print(f"{len(written)} labels written; not labelled: {missing}")

# --- 3. remove the ring, the seal ring and everything outside the ring's inner edge
removed = {}
for inst in list(top.each_inst()):
    n = inst.cell.name
    if (n.startswith("sg13g2_IOPad") or n.startswith("sg13g2_Filler") or n == "sg13g2_Corner"
            or n.startswith("bondpad_70x70") or "seal" in n.lower()):
        removed[n] = removed.get(n, 0) + 1
        top.erase(inst)
print("removed instances:", removed)
inner = pya.Box(320000, 320000, 1030000, 1030000)     # pads: 141 um edge spacing + 180 um cell, 1 um margin
dropped = 0
for li in ly.layer_indexes():
    for sh in list(top.shapes(li).each()):
        if not sh.bbox().touches(inner):
            top.shapes(li).erase(sh); dropped += 1
print(f"top-cell shapes outside the ring's inner edge dropped: {dropped}")
top.name = "g1_core"
ly.write(out)
print("wrote", out, "(top cell g1_core)")

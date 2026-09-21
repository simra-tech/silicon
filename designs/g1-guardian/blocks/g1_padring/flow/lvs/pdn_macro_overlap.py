# SPDX-License-Identifier: Apache-2.0
"""Chip supply shapes against the macros' internal metal.

  klayout -b -rd gds=<chip.gds> -rd defp=<chip.def> -rd lefs=<a.lef,b.lef,...> \
          -r pdn_macro_overlap.py

For every block instance of the DEF (the G1 macros and the sg13g2_io pad,
corner and filler cells; placement = DEF point and orientation applied to the
LEF SIZE box) and every special net (SPECIALNETS: stripes, patches,
via cells taken from the GDS `VIA_*` cells): the overlap of the net's shapes
with the cell's own metal on the same layer, minus the cell's pin rectangles
of that net (from the LEFs, `lefs`). Anything
left is a supply shape touching macro metal that is not its pin, i.e. a
potential short into the macro (a via stack pad over internal wiring, a stripe
over a plate). Also reports the pin overlaps themselves (the intended
connections) as a count, and checks that every special net touching a macro
pin is the pin's net.
"""
import re
import pya

gds, def_path = globals()["gds"], globals()["defp"]
lefs = globals().get("lefs", "")
ly = pya.Layout(); ly.read(gds)
top = ly.cell("g1_chip_top")
D = open(def_path).read()
LAY = {"Metal1": 8, "Metal2": 10, "Metal3": 30, "Metal4": 50, "Metal5": 67, "TopMetal1": 126, "TopMetal2": 134,
       "Via1": 19, "Via2": 29, "Via3": 49, "Via4": 66, "TopVia1": 125, "TopVia2": 133}

# --- LEF pins ---------------------------------------------------------------------
lef_pins, lef_size = {}, {}   # macro -> [(pin, layer, x1, y1, x2, y2)] in um; macro -> (w, h)
for path in [p for p in lefs.split(",") if p]:
    L = open(path).read()
    for mm in re.finditer(r"MACRO\s+(\S+)(.*?)END\s+\1", L, re.S):
        macro, body = mm.group(1), mm.group(2)
        sz = re.search(r"SIZE\s+([\d.]+)\s+BY\s+([\d.]+)", body)
        if sz:
            lef_size[macro] = (float(sz.group(1)), float(sz.group(2)))
        for pm in re.finditer(r"PIN\s+(\S+)\s+(.*?)END\s+\1", body, re.S):
            pin, pb = pm.group(1), pm.group(2)
            for lm in re.finditer(r"LAYER\s+(\w+)\s*;((?:\s*RECT[^;]*;)+)", pb):
                for r in re.findall(r"RECT\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)", lm.group(2)):
                    lef_pins.setdefault(macro, []).append((pin, lm.group(1), *map(float, r)))

# --- instances and pin nets --------------------------------------------------------
comp = D[D.index("COMPONENTS"):D.index("END COMPONENTS")]
insts = {}
def is_block(name):
    return name.startswith("g1_") or name.startswith("sg13g2_IOPad") or name.startswith("sg13g2_Corner") or name.startswith("sg13g2_Filler")
for m in re.finditer(r"-\s+(\S+)\s+(\S+)\s*\+\s*(?:FIXED|PLACED)\s*\(\s*(-?\d+)\s+(-?\d+)\s*\)\s*(\w+)", comp):
    if ly.cell(m.group(2)) is not None and is_block(m.group(2)):
        insts[m.group(1)] = (m.group(2), int(m.group(3)), int(m.group(4)), m.group(5))
# DEF orientation -> KLayout transformation code (checked against the GDS instances)
ORIENT = {"N": pya.Trans.R0, "W": pya.Trans.R90, "S": pya.Trans.R180, "E": pya.Trans.R270,
          "FN": pya.Trans.M90, "FS": pya.Trans.M0, "FW": pya.Trans.M45, "FE": pya.Trans.M135}
def placement(macro, ox, oy, orient):
    # the DEF point is the lower-left corner of the oriented LEF SIZE box
    w, h = lef_size[macro]
    rb = pya.Box(0, 0, int(w * 1000), int(h * 1000)).transformed(pya.Trans(ORIENT[orient]))
    return pya.Trans(ORIENT[orient], pya.Point(ox - rb.left, oy - rb.bottom))
pin_net, wild = {}, {}      # ( inst pin ) -> net; ( * pin ) -> net for every instance with that pin
for sec_start, sec_end in (("\nNETS", "END NETS"), ("SPECIALNETS", "END SPECIALNETS")):
    sec = D[D.index(sec_start):D.index(sec_end)]
    for rec in re.split(r"\n\s*-\s+", sec)[1:]:
        net = rec.split()[0]
        for inst, pin in re.findall(r"\(\s*(\S+)\s+(\S+)\s*\)", rec.split("+")[0]):
            if inst == "*":
                wild[pin] = net
            else:
                pin_net[(inst, pin)] = net
def net_of(inst, pin):
    return pin_net.get((inst, pin), wild.get(pin, "-"))

# --- special-net shapes ------------------------------------------------------------
SEG = re.compile(r"(?:ROUTED|NEW)\s+(\w+)\s+(\d+)\s+(?:\+\s+SHAPE\s+\w+\s+)?\(\s*(-?\d+)\s+(-?\d+)\s*\)\s*(?:\(\s*(-?\d+|\*)\s+(-?\d+|\*)\s*\)|(\w+))")
via_cache = {}
def via_shapes(vname):
    if vname in via_cache:
        return via_cache[vname]
    c = ly.cell("VIA_" + vname); out = []
    if c is None:
        print("WARNING: no GDS cell for via", vname)
    else:
        for lname, gl in LAY.items():
            li = ly.find_layer(gl, 0)
            if li is None: continue
            r = pya.Region(c.begin_shapes_rec(li))
            if not r.is_empty(): out.append((lname, r))
    via_cache[vname] = out
    return out
special = {}
sec = D[D.index("SPECIALNETS"):D.index("END SPECIALNETS")]
for rec in re.split(r"\n\s*-\s+", sec)[1:]:
    net = rec.split()[0]
    for m in SEG.finditer(rec):
        lay, w, x1, y1, x2, y2, vname = m.groups()
        x1, y1, w = int(x1), int(y1), int(w)
        if vname:
            for lname, r in via_shapes(vname):
                special.setdefault((net, lname), pya.Region()).insert(r.moved(x1, y1))
        else:
            x2 = x1 if x2 == "*" else int(x2); y2 = y1 if y2 == "*" else int(y2)
            box = pya.Box(x1 - w // 2, min(y1, y2), x1 + w // 2, max(y1, y2)) if x1 == x2 else pya.Box(min(x1, x2), y1 - w // 2, max(x1, x2), y1 + w // 2)
            special.setdefault((net, lay), pya.Region()).insert(box)
nets = sorted({k[0] for k in special})
print("special nets:", nets, "| block instances:", sorted(insts))

# --- per instance ------------------------------------------------------------------
problems = 0
for iname, (macro, ox, oy, orient) in sorted(insts.items()):
    mc = ly.cell(macro)
    if macro not in lef_size:
        print(f"{iname} ({macro}): no LEF given (size and pins unknown), skipped"); problems += 1; continue
    tr = placement(macro, ox, oy, orient)
    pins = {}
    for pin, lname, x1, y1, x2, y2 in lef_pins.get(macro, []):
        net = net_of(iname, pin)
        pins.setdefault((net, lname), pya.Region()).insert(pya.Box(int(x1 * 1000), int(y1 * 1000), int(x2 * 1000), int(y2 * 1000)).transformed(tr))
    bbox = mc.bbox().transformed(tr)
    for net in nets:
        for lname in ("Metal1", "Metal2", "Metal3", "Metal4", "Metal5", "TopMetal1", "TopMetal2"):
            sp = special.get((net, lname))
            if sp is None: continue
            sp_here = sp & pya.Region(bbox)
            if sp_here.is_empty(): continue
            li = ly.find_layer(LAY[lname], 0)
            macro_metal = pya.Region(mc.begin_shapes_rec(li)).transformed(tr) if li is not None else pya.Region()
            ov = sp_here & macro_metal
            if ov.is_empty(): continue
            # the pin rectangles, grown by 50 nm: a via pad is 0.44 um tall on a
            # 0.4 um rail and the macro's own wires join the pin at its edge
            own = pins.get((net, lname), pya.Region()).sized(50)
            intended = ov & own
            foreign = ov - own
            for other_net, other_l in pins:
                if other_l == lname and other_net != net and not (sp_here & pins[(other_net, other_l)]).is_empty():
                    print(f"SHORT {iname}: {net} {lname} touches the macro pin of net {other_net}"); problems += 1
            if not foreign.is_empty():
                problems += 1
                print(f"FOREIGN {iname} ({macro}): {net} on {lname} overlaps macro metal outside its pins: {foreign.count()} polygons, {foreign.area()/1e6:.3f} um2, e.g. {[str(p.bbox()) for p in list(foreign.each())[:4]]}")
            elif not intended.is_empty():
                print(f"ok      {iname}: {net} {lname} on its pin(s), {intended.area()/1e6:.2f} um2")
print("problems:", problems)

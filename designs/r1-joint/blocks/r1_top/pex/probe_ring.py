# SPDX-License-Identifier: Apache-2.0
"""T11 probe: IO cells of the ring, their pins and labels, instance positions (development aid)."""
import klayout.db as db
ly = db.Layout(); ly.read(g)  # noqa: F821
ring = ly.cell("r1_padring")
seen = set()
for inst in ring.each_inst():
    c = inst.cell
    if "IOPad" in c.name or "bondpad" in c.name:
        print("inst", c.name, inst.dcplx_trans, inst.dbbox())
    if c.name in seen:
        continue
    seen.add(c.name)
    out = []
    for li in ly.layer_indexes():
        info = ly.get_info(li)
        for s in c.shapes(li).each():
            if s.is_text():
                out.append("%d/%d %s @%s" % (info.layer, info.datatype, s.text_string, s.dtext.position()))
        if info.datatype == 2 and c.shapes(li).size():
            out.append("%d/2 x%d %s" % (info.layer, c.shapes(li).size(), [str(s.dbbox()) for s in c.shapes(li).each()][:6]))
    print("cell", c.name, c.dbbox(), out[:30])
for li in ly.layer_indexes():
    info = ly.get_info(li)
    for s in ring.shapes(li).each():
        if s.is_text():
            print("ring text", info, s.text_string, s.dtext.position())

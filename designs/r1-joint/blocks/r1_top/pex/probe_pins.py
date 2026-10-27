# SPDX-License-Identifier: Apache-2.0
"""T11 probe: pin-purpose shapes and labels per macro cell (development aid)."""
import klayout.db as db
ly = db.Layout(); ly.read(g)  # noqa: F821
top = ly.cell("r1_top")
for inst in top.each_inst():
    c = inst.cell
    if c.name == "r1_padring":
        continue
    out = []
    for li in ly.layer_indexes():
        info = ly.get_info(li)
        if info.datatype in (2, 25):
            n = c.shapes(li).size()
            if n:
                out.append("%d/%d:%d" % (info.layer, info.datatype, n))
    print(c.name, inst.dcplx_trans, c.dbbox(), " ".join(out))
c = ly.cell("r1_adc")
for li in ly.layer_indexes():
    info = ly.get_info(li)
    if info.datatype == 25:
        for s in list(c.shapes(li).each())[:3]:
            p = s.dtext.position()
            # what shapes at the label in datatype 0 and 2
            hits = []
            for dt in (0, 2):
                l2 = ly.find_layer(info.layer, dt)
                if l2 is None:
                    continue
                r = db.Region(c.begin_shapes_rec_touching(l2, db.DBox(p.x - 0.01, p.y - 0.01, p.x + 0.01, p.y + 0.01)))
                hits.append((dt, [str(b.bbox().to_dtype(ly.dbu)) for b in r.each()][:3]))
            print("adc label", info, s.text_string, p, hits)

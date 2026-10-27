# diagnostic (layout B4): bounding x-extent of each layer inside a y band of the top cell (shapes of the top cell only,
# child instances listed separately). klayout -b -r probe_extent.py -rd gds=<gds> -rd y1=<um> -rd y2=<um>
import pya
ly = pya.Layout(); ly.read(gds)
top = ly.top_cell()
y1_, y2_ = float(y1), float(y2)
for li in ly.layer_indexes():
    info = ly.get_info(li)
    xs = []
    for sh in top.shapes(li).each_overlapping(pya.DBox(0, y1_, 439, y2_).to_itype(ly.dbu)):
        b = sh.dbbox()
        xs.append((round(b.left, 2), round(b.right, 2), round(b.bottom, 2), round(b.top, 2)))
    if xs:
        segs = sorted(xs)
        # merge x intervals
        m = []
        for a in segs:
            if m and a[0] <= m[-1][1] + 1.0:
                m[-1] = [m[-1][0], max(m[-1][1], a[1]), min(m[-1][2], a[2]), max(m[-1][3], a[3])]
            else:
                m.append(list(a))
        print(info, len(xs), [tuple(x) for x in m[:12]], '...' if len(m) > 12 else '')
for inst in top.each_inst():
    b = inst.dbbox()
    if b.top > y1_:
        print('inst', inst.cell.name, b)

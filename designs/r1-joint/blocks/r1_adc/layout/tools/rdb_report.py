"""Per-rule counts and the first locations of a KLayout DRC report.  klayout -b -r tools/rdb_report.py -rd db=<lyrdb> [-rd n=5]"""
import pya
db = globals()['db']; n = int(globals().get('n', '5'))
r = pya.ReportDatabase(''); r.load(db)
cats = {}
for it in r.each_item():
    c = r.category_by_id(it.category_id()).name()
    cats.setdefault(c, []).append(it)
tot = 0
for c in sorted(cats):
    its = cats[c]; tot += len(its)
    locs = []
    for it in its[:n]:
        for v in it.each_value():
            try: b = v.box() if v.is_box() else (v.edge_pair().bbox() if v.is_edge_pair() else (v.polygon().bbox() if v.is_polygon() else (v.edge().bbox() if v.is_edge() else None)))
            except Exception: b = None
            if b: locs.append('%s(%.2f,%.2f;%.2f,%.2f)' % (r.cell_by_id(it.cell_id()).name()[:14] + ':', b.left, b.bottom, b.right, b.top)); break
    print('%-28s %5d  %s' % (c, len(its), ' '.join(locs)))
print('TOTAL', tot)

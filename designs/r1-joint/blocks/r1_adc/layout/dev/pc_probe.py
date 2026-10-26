import pya
lib = pya.Library.library_by_name('SG13_dev')
ly = lib.layout()
for w in ('3.78u','4.23u','2.67u','70u'):
    pcv = ly.add_pcell_variant(ly.pcell_id('cmim'), {'Calculate':'C','w':w,'l':w})
    c = ly.cell(pcv)
    print('==', w)
    for li in ly.layer_indexes():
        info = ly.get_info(li)
        r = pya.Region(c.begin_shapes_rec(li))
        if not r.is_empty():
            print(info, r.count(), r.bbox(), [str(p.bbox()) for p in list(r.each())[:3]])

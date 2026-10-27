import pya, sys
ly = pya.Layout(); ly.read(gds)
top = ly.top_cell()
print("top", top.name, [ly.cell(i).name for i in top.each_child_cell()])
out = []
for li in ly.layer_indexes():
    info = ly.get_info(li)
    it = top.begin_shapes_rec(li)
    while not it.at_end():
        s = it.shape()
        if s.is_text():
            t = s.text.transformed(it.trans())
            if 'sar' in t.string or t.string.startswith('top') or t.string in ('mclk','op','on','onp','onn','clk','clkb','clkn','clknb','trk0','trk1') or t.string.startswith('cp') or t.string.startswith('cn'):
                out.append((t.string, info.layer, info.datatype, round(t.x*ly.dbu,3), round(t.y*ly.dbu,3), it.cell().name))
        it.next()
for o in sorted(out): print(*o)

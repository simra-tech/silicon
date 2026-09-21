import pya
ly = pya.Layout(); ly.read(globals()["gds"]); top = ly.top_cell()
# fill shapes: in the top cell only, or also inside macro cells? count by cell for Metal3 fill
li = ly.find_layer(30, 22)
cells = {}
it = top.begin_shapes_rec(li)
while not it.at_end():
    n = ly.cell(it.cell_index()).name; cells[n] = cells.get(n, 0) + 1; it.next()
print("Metal3 fill shapes per cell:", dict(sorted(cells.items(), key=lambda kv: -kv[1])[:6]))
# does the sense footprint contain any top-level fill? (it did not in the density report)
box = pya.Region(pya.Box(733000, 440000, 985160, 629250))
r = pya.Region(top.shapes(li)); print("top-cell Metal3 fill inside the sense footprint:", (r & box).count())

# Control for the antenna result: copy a GDS and delete all top-level instances of cells whose name matches a pattern.
#   klayout -b -r strip_cells.py -rd i=<in> -rd o=<out> -rd pat=<regex>
import pya, re, collections
ly = pya.Layout(); ly.read(i); T = ly.top_cell(); n = collections.Counter()
for inst in list(T.each_inst()):
    if re.search(pat, inst.cell.name): n[inst.cell.name] += 1; inst.delete()
for _ in range(20):
    orph = [c for c in ly.each_cell() if c.cell_index() != T.cell_index() and c.parent_cells() == 0]
    if not orph: break
    for c in orph: ly.delete_cell(c.cell_index())
o_ = pya.SaveLayoutOptions(); o_.format = 'GDS2'; o_.gds2_write_timestamps = False
ly.write(o, o_); print(dict(n))

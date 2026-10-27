# diagnostic (layout B4): top-cell text labels whose name starts with a prefix, with layer and position (um), as CSV.
# klayout -b -r probe_labels.py -rd gds=<gds> -rd prefix=sar_ -rd out=<csv>
import pya
ly = pya.Layout(); ly.read(gds)
top = ly.top_cell()
rows = []
for li in ly.layer_indexes():
    inf = ly.get_info(li)
    for sh in top.shapes(li).each():
        if sh.is_text() and sh.text_string.startswith(prefix):
            t = sh.dtext
            rows.append((sh.text_string, '%d/%d' % (inf.layer, inf.datatype), round(t.x, 3), round(t.y, 3)))
rows.sort()
with open(out, 'w') as f:
    f.write('net,layer,x_um,y_um\n')
    for r in rows:
        f.write('%s,%s,%.3f,%.3f\n' % r)
print(len(rows))

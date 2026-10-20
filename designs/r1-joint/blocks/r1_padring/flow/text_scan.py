# list text strings by layer in the top cell hierarchy (flat) matching a pattern.  klayout -b -r text_scan.py -rd gds=<f> -rd pat=<regex>
import pya, re, collections
ly = pya.Layout(); ly.read(gds); top = ly.top_cell()
c = collections.Counter(); ex = {}
for li in ly.layer_indexes():
    info = ly.get_info(li)
    it = top.begin_shapes_rec(li)
    it.shape_flags = pya.Shapes.STexts
    while not it.at_end():
        s = it.shape()
        if s.is_text() and re.search(pat, s.text_string):
            k = (info.layer, info.datatype, s.text_string); c[k] += 1
            ex.setdefault(k, (it.trans() * s.text.trans.disp).to_s(), )
        it.next()
for k, v in sorted(c.items()): print(k, v, ex[k])

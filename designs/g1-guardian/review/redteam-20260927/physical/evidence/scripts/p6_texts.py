import pya, json
G = '/work/designs/g1-guardian/blocks/g1_padring/layout/g1_chip_top_1414_r3.gds'
ly = pya.Layout(); ly.read(G); top = ly.cell('g1_chip_top'); dbu = ly.dbu
out = []; n = 0
for li in ly.layer_indexes():
    it = top.begin_shapes_rec(li); it.shape_flags = pya.Shapes.STexts
    while not it.at_end():
        t = it.shape().text.transformed(it.trans()); n += 1
        x, y = t.x * dbu, t.y * dbu
        if x <= 0 or y <= 0 or x >= 1414 or y >= 1414:
            out.append((str(ly.get_info(li)), t.string[:40], x, y, ly.cell(it.cell_index()).name))
        it.next()
print(json.dumps(dict(n_texts=n, n_on_or_outside_die_edge=len(out), sample=out[:20]), indent=1))

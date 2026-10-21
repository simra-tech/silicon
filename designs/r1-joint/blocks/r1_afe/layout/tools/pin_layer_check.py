"""Pin and layer check of an r1_afe GDS against a reference GDS (E2). Prints JSON.
klayout -b -r tools/pin_layer_check.py -rd gds=<new.gds> -rd ref=<reference.gds>
pins: Metal3 pin (30/2) shapes with their text labels (30/25) of the top cell; 'same' = equal set of (label, box).
layers: TopMetal2 (134/0) area must be 0; TopMetal1 (126/0) area outside MIM (36/0) must be 0; bbox in um."""
import json, pya
def info(path):
    ly = pya.Layout(); ly.read(path); top = ly.top_cell()
    def reg(l, d):
        li = ly.find_layer(l, d)
        return pya.Region(top.begin_shapes_rec(li)) if li is not None else pya.Region()
    pins = reg(30, 2).merged()
    labs = []
    li = ly.find_layer(30, 25)
    if li is not None:
        it = top.begin_shapes_rec(li)
        while not it.at_end():
            s = it.shape()
            if s.is_text():
                p = s.text.trans.disp.to_dtype(ly.dbu) if False else it.trans() * s.text.trans.disp
                for poly in pins.each():
                    if poly.bbox().contains(p):
                        b = poly.bbox().to_dtype(ly.dbu)
                        labs.append((s.text.string, round(b.left, 3), round(b.bottom, 3), round(b.right, 3), round(b.top, 3)))
                        break
                else:
                    labs.append((s.text.string, None))
            it.next()
    tm1cells = {}
    li = ly.find_layer(126, 0)
    if li is not None:
        it = top.begin_shapes_rec(li)
        while not it.at_end():
            n = ly.cell(it.cell_index()).name
            tm1cells[n] = tm1cells.get(n, 0) + 1
            it.next()
    tm1 = reg(126, 0).merged(); mim = reg(36, 0).merged(); tm2 = reg(134, 0); m5 = reg(67, 0)
    um2 = lambda r: round(r.area() * ly.dbu ** 2, 3)
    bb = top.dbbox()
    return dict(top=top.name, bbox_um=[round(bb.width(), 3), round(bb.height(), 3)], pins=sorted(labs, key=str),
                topmetal2_um2=um2(tm2), topmetal1_um2=um2(tm1), topmetal1_outside_mim_um2=um2(tm1 - mim.sized(int(round(0.6 / ly.dbu)))),
                topmetal1_not_over_mim_polys=(tm1 - mim.sized(int(round(0.6 / ly.dbu)))).count(), metal5_um2=um2(m5), mim_um2=um2(mim), topmetal1_cells=tm1cells)
a, b = info(globals()['gds']), info(globals()['ref'])
out = dict(new={k: v for k, v in a.items() if k != 'pins'}, ref={k: v for k, v in b.items() if k != 'pins'},
           n_pins=[len(a['pins']), len(b['pins'])], pins_same=a['pins'] == b['pins'], pins_set_same=set(a['pins']) == set(b['pins']), n_pins_unique=[len(set(a['pins'])), len(set(b['pins']))],
           pins_only_new=[p for p in a['pins'] if p not in b['pins']], pins_only_ref=[p for p in b['pins'] if p not in a['pins']])
print(json.dumps(out, indent=1))

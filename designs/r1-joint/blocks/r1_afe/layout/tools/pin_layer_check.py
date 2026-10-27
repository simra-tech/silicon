"""Pin and layer check of an r1_afe GDS against a reference GDS (E2). Prints JSON.
klayout -b -r tools/pin_layer_check.py -rd gds=<new.gds> -rd ref=<reference.gds>
pins: Metal3 pin (30/2) shapes with their text labels (30/25) of the top cell; 'same' = equal set of (label, box).
E5: also centres_same (label + centre), supply pin widths, signal_pins_same.
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
# E5 (assembly try f): supply pins >= 1 um wide at the macro edge with the E4 centres. Compare (label, centre) and
# report the pin widths along the edge; 'centres_same' must be true, 'supply_min_width_um' >= 1.0.
def cen(pins):
    return sorted([((p[0], round((p[1] + p[3]) / 2, 3), round((p[2] + p[4]) / 2, 3)) if p[1] is not None else (p[0], None)) for p in pins], key=str)
def width(p):
    return round(min(p[3] - p[1], p[4] - p[2]), 3) if p[1] is not None else None
out['centres_same'] = sorted(set(cen(a['pins'])), key=str) == sorted(set(cen(b['pins'])), key=str)   # unique (label, centre); E4 had duplicate texts on pin nodes
out['supply_pin_widths_um'] = sorted(width(p) for p in a['pins'] if p[0] in ('vdd', 'vss', 'vdda') and p[1] is not None)
out['supply_pins_without_box'] = [p for p in a['pins'] if p[0] in ('vdd', 'vss', 'vdda') and p[1] is None]
out['supply_min_width_um'] = min(out['supply_pin_widths_um']) if out['supply_pin_widths_um'] else None
out['signal_pins_same'] = sorted(set(p for p in a['pins'] if p[0] not in ('vdd', 'vss', 'vdda')), key=str) == sorted(set(p for p in b['pins'] if p[0] not in ('vdd', 'vss', 'vdda')), key=str)
print(json.dumps(out, indent=1))

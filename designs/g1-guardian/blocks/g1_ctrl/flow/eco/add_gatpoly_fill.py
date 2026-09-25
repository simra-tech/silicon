#!/usr/bin/env python3
"""Additive GatPoly fill (5/22) in the chip top cell until a target area is added.

Same geometry method as review/audits/add_native_poly_fill.py (which is locked to its
own candidate directory): stock GFil sizes from the PDK rule table (5.0 x 1.4 um
rectangles, >= 0.8 um to each other and to existing GatPoly fill), placed only inside
the seal-ring interior (holes of 39/0), >= 1.1 um from Activ, GatPoly, NWell, nBuLay,
ThickGateOx, Cont, Metal1-adjacent FEOL layers and existing Activ fill, never in
GatPoly/Activ no-fill (5/23, 1/23). Rectangles are added phase by phase (fixed
offsets) and, within the last phase, in (y, x) order until --target-um2 is reached.
Nothing but 5/22 in the top cell changes (checked on the re-read output: every other
layer, all texts and all instances identical).

  add_gatpoly_fill.py --in <chip.gds> --out <chip_filled.gds> --target-um2 600 --report <json>
"""
import argparse
import collections
import hashlib
import json

import klayout.db as db


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def region(ly, cell, ld):
    li = ly.find_layer(*ld)
    return db.Region() if li is None else db.Region(cell.begin_shapes_rec(li)).merged()


def texts(ly, cell):
    out = collections.Counter()
    for li in ly.layer_indexes():
        it = cell.begin_shapes_rec(li)
        while not it.at_end():
            if it.shape().is_text():
                t = it.shape().text.transformed(it.trans())
                out[(str(ly.get_info(li)), t.string, t.x, t.y)] += 1
            it.next()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--in', dest='inp', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--target-um2', type=float, required=True)
    ap.add_argument('--report', required=True)
    a = ap.parse_args()
    pdk = '/foss/pdks/ihp-sg13g2'
    assert open(pdk + '/COMMIT').read().strip() == '84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
    rules = json.load(open(pdk + '/libs.tech/klayout/tech/drc/rule_decks/sg13g2_tech_default.json'))
    tables = [rules] + [v for v in rules.values() if isinstance(v, dict)]
    table, = [v for v in tables if 'GFil_size_x' in v]
    assert {k: table[k] for k in ('GFil_size_x', 'GFil_size_y', 'GFil_c', 'GFil_d', 'GFil_e')} == {
        'GFil_size_x': 5.0, 'GFil_size_y': 1.4, 'GFil_c': .8, 'GFil_d': 1.1, 'GFil_e': 1.1}
    ly = db.Layout(); ly.read(a.inp)
    top, = ly.top_cells()
    assert abs(ly.dbu - .001) < 1e-12
    get = lambda l, d=0: region(ly, top, (l, d))
    die = top.bbox().area() * 1e-6
    poly_before = (get(5, 0) + get(5, 22)).merged().area() * 1e-6
    interior = get(39).holes()
    assert not interior.is_empty()
    obstacles = db.Region()
    for l, d in ((1, 0), (5, 0), (6, 0), (14, 0), (7, 21), (28, 0), (31, 0), (32, 0), (26, 0), (1, 22)):
        obstacles += get(l, d).sized(1100)
    obstacles += get(5, 23) + get(1, 23)
    old = get(5, 22)
    blocked = (obstacles + old.sized(800)).merged()
    bbox = interior.bbox()
    schedule = [(0, 0), (2500, 0), (5000, 0), (7500, 0), (0, 1250), (2500, 1250), (5000, 1250), (7500, 1250)]
    added = db.Region(); phases = []
    for dx, dy in schedule:
        trial = db.Region()
        for row, y in enumerate(range(bbox.bottom + dy, bbox.top - 1400, 2500)):
            for x in range(bbox.left + dx + (row % 2) * 5000, bbox.right - 5000, 10000):
                trial.insert(db.Box(x, y, x + 5000, y + 1400))
        legal = trial.inside(interior).not_interacting(blocked)
        need = a.target_um2 - added.area() * 1e-6
        boxes = sorted((p.bbox() for p in legal.each()), key=lambda b: (b.bottom, b.left))
        take = db.Region()
        for b in boxes:
            if take.area() * 1e-6 >= need:
                break
            take.insert(b)
        added += take
        blocked = (blocked + take.sized(800)).merged()
        phases.append(dict(offset_dbu=[dx, dy], legal=legal.count(), taken=take.count(),
                           area_um2=round(take.area() * 1e-6, 3)))
        if added.area() * 1e-6 >= a.target_um2:
            break
    assert (added & old).is_empty() and (added - interior).is_empty()
    assert added.area() * 1e-6 >= a.target_um2, 'target not reached'
    tx = texts(ly, top)
    before = {str(ly.get_info(li)): region(ly, top, (ly.get_info(li).layer, ly.get_info(li).datatype))
              for li in ly.layer_indexes()}
    insts = collections.Counter((i.cell.name, str(i.trans)) for i in top.each_inst())
    top.shapes(ly.layer(5, 22)).insert(added)
    opt = db.SaveLayoutOptions(); opt.gds2_write_timestamps = False
    ly.write(a.out, opt)
    # verification on the re-read file
    s = db.Layout(); s.read(a.out); st, = s.top_cells()
    assert texts(s, st) == tx
    assert collections.Counter((i.cell.name, str(i.trans)) for i in st.each_inst()) == insts
    changed = {}
    for li in s.layer_indexes():
        info = s.get_info(li)
        exp = before.get(str(info), db.Region())
        if (info.layer, info.datatype) == (5, 22):
            exp = (exp + added).merged()
        n = (region(s, st, (info.layer, info.datatype)) ^ exp).count()
        if n:
            changed[str(info)] = n
    assert not changed, changed
    poly_after = (region(s, st, (5, 0)) + region(s, st, (5, 22))).merged().area() * 1e-6
    rep = dict(input=a.inp, input_sha256=sha(a.inp), output=a.out, output_sha256=sha(a.out),
               target_um2=a.target_um2, added_um2=round(added.area() * 1e-6, 3), rectangles=added.count(),
               added_bbox_um=str(added.bbox().to_dtype(ly.dbu)), phases=phases,
               gatpoly_before_um2=round(poly_before, 3), gatpoly_after_um2=round(poly_after, 3),
               global_ratio_before_pct=round(100 * poly_before / die, 4),
               global_ratio_after_pct=round(100 * poly_after / die, 4),
               only_5_22_changed=True, texts_instances_held=True)
    json.dump(rep, open(a.report, 'w'), indent=1)
    print(json.dumps(rep, indent=1))


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Additive GatPoly fill (5/22) in the chip top cell until a target area is added.

Same geometry method as review/audits/add_native_poly_fill.py (which is locked to its
own candidate directory): stock GFil sizes from the PDK rule table (5.0 x 1.4 um
rectangles at most, >= 0.8 um to each other and to existing GatPoly fill), placed only inside
the seal-ring interior (holes of 39/0), >= 1.1 um from Activ, GatPoly, NWell, nBuLay,
Cont, pSD, nSD:block, SalBlock (GFil.d), NWell, nBuLay (GFil.e) and existing Activ
fill (margins per layer, --obstacles), never in
GatPoly/Activ no-fill (5/23, 1/23), and outside every --exclude-box (+1.1 um).
Placement: row strips 1.4 um high on a 2.2 um pitch, free intervals cut into
<= 5.0 um pieces 0.8 um apart, >= --min-width-nm wide; rectangles are taken in
(y, x) order until --target-um2 is reached. The stock checks involved are GFil.a-c,
GFil.f, GFil.j (maximal deck) and GFil.g (global density).
Nothing but 5/22 in the top cell changes (checked on the re-read output: every other
layer, all texts and all instances identical).

  add_gatpoly_fill.py --in <chip.gds> --out <chip_filled.gds> --target-um2 700 \
      --exclude-box 367,364,727,724 --report <json>
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
    ap.add_argument('--min-width-nm', type=int, default=1000)
    # layer/datatype[:margin_nm]. Default = add_native_poly_fill.py's list. The stock rules
    # are GFil.d (1.1 um to Activ 1/0, GatPoly 5/0, Cont 6/0, pSD 14/0, nSD:block 7/21,
    # SalBlock 28/0) and GFil.e (1.1 um to NWell 31/0, nBuLay 32/0); Activ fill 1/22 has no
    # spacing rule to GatPoly fill (GFil.j only constrains overlap), so it may take a
    # smaller margin, e.g. 1/22:300.
    ap.add_argument('--obstacles', default='1/0,5/0,6/0,14/0,7/21,28/0,31/0,32/0,26/0,1/22')
    ap.add_argument('--exclude-box', action='append', default=[], help='x0,y0,x1,y1 in um')
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
    for t in a.obstacles.split(','):               # layer/datatype[:margin_nm], default 1100
        ld, _, margin = t.partition(':')
        l, d = map(int, ld.split('/'))
        obstacles += get(l, d).sized(int(margin) if margin else 1100)
    obstacles += get(5, 23) + get(1, 23)
    old = get(5, 22)
    blocked = (obstacles + old.sized(800)).merged()
    for box in a.exclude_box:                       # e.g. the digital macro outline
        x0, y0, x1, y1 = (int(round(float(v) * 1000)) for v in box.split(','))
        blocked += db.Region(db.Box(x0, y0, x1, y1)).sized(1100)
    blocked.merge()
    # Row strips: rectangles 1.4 um high (GFil size y), 0.8 um apart vertically
    # (GFil.c); along a row, free intervals are cut into pieces of <= 5.0 um (GFil.a)
    # separated by 0.8 um, pieces narrower than --min-width dropped (GFil.b = 0.7).
    free = (interior - blocked).merged()
    ok_rows = free.sized(0, -700)                   # centre points whose 1.4 um column is free
    bbox = interior.bbox()
    added = db.Region(); phases = []
    for dy in (0, 1100):                            # two row phases, the second fills between
        rows = db.Region()
        for y in range(bbox.bottom + 700 + dy, bbox.top - 700, 2200):
            rows.insert(db.Box(bbox.left, y - 1, bbox.right, y + 1))
        pieces = (ok_rows & rows) - added.sized(800)
        take = db.Region()
        for p in sorted((q.bbox() for q in pieces.each()), key=lambda b: (b.bottom, b.left)):
            yc = (p.bottom + p.top) // 2
            x = p.left
            while p.right - x >= a.min_width_nm:
                w = min(5000, p.right - x)
                take.insert(db.Box(x, yc - 700, x + w, yc + 700))
                x += w + 800
        take = take.not_interacting(blocked).not_interacting(added.sized(799))
        # rectangles of this phase closer than 0.8 um to each other: keep the first in (y, x) order
        kept = db.Region()
        for b in sorted((q.bbox() for q in take.each()), key=lambda b: (b.bottom, b.left)):
            if (added.area() + kept.area()) * 1e-6 >= a.target_um2:
                break
            if kept.is_empty() or db.Region(b).sized(799).interacting(kept).is_empty():
                kept.insert(b)
        added += kept
        phases.append(dict(row_offset_dbu=dy, candidates=take.count(), kept=kept.count(),
                           area_um2=round(kept.area() * 1e-6, 3)))
        if added.area() * 1e-6 >= a.target_um2:
            break
    json.dump(dict(status='placement done', phases=phases, added_um2=added.area() * 1e-6),
              open(a.report, 'w'), indent=1)
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
               only_5_22_changed=True, texts_instances_held=True,
               obstacles_sized_1p1um=a.obstacles, exclude_boxes=a.exclude_box, min_width_nm=a.min_width_nm)
    json.dump(rep, open(a.report, 'w'), indent=1)
    print(json.dumps(rep, indent=1))


if __name__ == '__main__':
    main()

"""Verify a bond-map CSV against a chip GDS geometrically (same method as the 2026-09-25 physical review, s2):
each row must coincide with one Passiv 9/0 opening (merged polygon < 200 um wide) whose centre equals the CSV centre
to 1 dbu and whose size equals the CSV size; TopMetal2 encloses it by >= 2.1 um; it lies inside dfpad 41/0; the
top-level TopMetal2 label (134/25) at the opening centre, if any, equals logical_pin; the CSV hash column equals the
GDS sha256. klayout -b -r verify_bondmap.py -rd g=<gds> -rd csvf=<csv> -rd out=<json>"""
import pya, csv, json, hashlib
sha = hashlib.sha256(open(g, 'rb').read()).hexdigest()
ly = pya.Layout(); ly.read(g); top, = ly.top_cells(); dbu = ly.dbu
def L(l, d):
    li = ly.find_layer(l, d)
    return pya.Region() if li is None else pya.Region(top.begin_shapes_rec(li))
ops = [p for p in L(9, 0).merged().each() if p.bbox().width() < 200000]
tm2 = L(134, 0); dfp = L(41, 0)
labels = {}
li = ly.find_layer(134, 25)
for s in top.shapes(li).each(pya.Shapes.STexts): labels[(s.text.x, s.text.y)] = s.text_string
OUT = out
rows = list(csv.DictReader(open(csvf))); out = []; used = set()
for r in rows:
    cx, cy = round(float(r['opening_center_x_um']) / dbu), round(float(r['opening_center_y_um']) / dbu)
    w, h = round(float(r['opening_width_um']) / dbu), round(float(r['opening_height_um']) / dbu)
    m = [k for k, p in enumerate(ops) if p.bbox().center() == pya.Point(cx, cy)]
    rec = dict(pad=int(r['pad_number']), pin=r['logical_pin'], side=r['side'], x=cx * dbu, y=cy * dbu, openings_matched=len(m))
    if len(m) == 1:
        p = ops[m[0]]; used.add(m[0]); pr = pya.Region(p)
        rec.update(rect=p.is_box(), size_ok=(p.bbox().width(), p.bbox().height()) == (w, h),
                   tm2_encl_2p1=(pr.sized(2100) - tm2).is_empty(), in_dfpad=(pr - dfp).is_empty(),
                   label=labels.get((cx, cy)), label_ok=labels.get((cx, cy)) in (None, r['logical_pin']),
                   hash_ok=r['candidate_gds_sha256'] == sha, die_ok=(float(r['die_width_um']), float(r['die_height_um'])) == (top.bbox().width() * dbu, top.bbox().height() * dbu))
        rec['ok'] = all(rec[k] for k in ('rect', 'size_ok', 'tm2_encl_2p1', 'in_dfpad', 'label_ok', 'hash_ok', 'die_ok'))
    else: rec['ok'] = False
    out.append(rec)
res = dict(gds=g, gds_sha256=sha, csv=csvf, csv_sha256=hashlib.sha256(open(csvf, 'rb').read()).hexdigest(),
           openings_in_gds=len(ops), rows=len(rows), openings_unmatched=len(ops) - len(used), labels_134_25=len(labels),
           labels_at_row_centres=sum(1 for o in out if o.get('label')), all_ok=all(o['ok'] for o in out) and len(used) == len(ops) == len(rows), pads=out)
open(OUT, 'w').write(json.dumps(res, indent=1) + '\n')
print(json.dumps({k: v for k, v in res.items() if k != 'pads'}, indent=1))

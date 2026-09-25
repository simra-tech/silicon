"""Generate the G1 QFN24 bond plan from the chip GDS of record.
Reads the 24 Passiv 9/0 openings and the TopMetal2 labels (134/25) from the GDS, checks them against the bond-map
rows, places the die in the package, derives the QFN24 lead opposite each pad, checks that no two wires cross, and
writes: the bond-map CSV (input rows + GDS hash + status + lead columns), the SVG drawing and a JSON summary.

Package convention (top view): leads numbered counter-clockwise, lead 1 = top lead of the left side next to the
top-left corner (pin-1 mark). Left side leads 1-6 top->bottom, bottom 7-12 left->right, right 13-18 bottom->top,
top 19-24 right->left. Die placement: centred on the paddle, rotated 90 deg clockwise from the GDS view, so the GDS
south edge (pads 1-6) faces leads 1-6. "Directly opposite" = same rank along the side in the counter-clockwise
direction. Nominal package dimensions (body 4.00 mm, pitch 0.50 mm, lead 0.25 x 0.40 mm, paddle 2.60 mm) are for the
drawing only; the assembly house's package drawing governs.

Run in the pinned container from the repository root:
  klayout -b -r designs/g1-guardian/padframe/bondplan_20260925.py -rd gds=<r2.gds> -rd src_csv=<r2 csv> \
          -rd out_csv=<r3 csv> -rd out_svg=<svg> -rd out_json=<json>"""
import pya, csv, json, hashlib, math
GDS_SHA = '9049e87b0303893573ed82f56a5d41f926c4db126e8d972062553c7d19996d2c'
BODY, PITCH, LEAD_W, LEAD_L, PADDLE = 4.0, 0.5, 0.25, 0.40, 2.60
sha = hashlib.sha256(open(gds, 'rb').read()).hexdigest(); assert sha == GDS_SHA, sha
ly = pya.Layout(); ly.read(gds); top, = ly.top_cells(); dbu = ly.dbu
die = top.bbox(); assert die == pya.Box(0, 0, 1414000, 1414000)
W = die.width() * dbu / 1000.0                                  # mm
li = ly.find_layer(9, 0)
ops = [p.bbox() for p in pya.Region(top.begin_shapes_rec(li)).merged().each() if p.bbox().width() < 200000]
assert len(ops) == 24
labels = {(t.text.x, t.text.y): t.text_string for t in top.shapes(ly.find_layer(134, 25)).each(pya.Shapes.STexts)}
rows = list(csv.DictReader(open(src_csv)))
pads = []
for r in rows:
    c = pya.Point(round(float(r['opening_center_x_um']) / dbu), round(float(r['opening_center_y_um']) / dbu))
    m = [b for b in ops if b.center() == c]; assert len(m) == 1, r
    b = m[0]; lab = labels.get((c.x, c.y)); assert lab in (None, r['logical_pin']), (r, lab)
    x, y = c.x * dbu / 1000.0, c.y * dbu / 1000.0
    u, v = y - W / 2, -(x - W / 2)                                # rotate 90 deg clockwise about the die centre (mm)
    side = max([('left', -u), ('right', u), ('bottom', -v), ('top', v)], key=lambda s: s[1])[0]
    pads.append(dict(pad=int(r['pad_number']), net=r['logical_pin'], gds_side=r['side'], x_um=x * 1000, y_um=y * 1000,
                     w_um=b.width() * dbu, h_um=b.height() * dbu, label=lab, u=u, v=v, pkg_side=side, row=r))
# lead geometry, counter-clockwise from pin 1 (top of left side)
H = BODY / 2; offs = [(k - 2.5) * PITCH for k in range(6)]          # -1.25 .. +1.25
leads = {}
for k in range(6):
    leads[1 + k] = ('left', -H, -offs[k]);  leads[7 + k] = ('bottom', offs[k], -H)
    leads[13 + k] = ('right', H, offs[k]);  leads[19 + k] = ('top', -offs[k], H)
def ccw_key(side, u, v): return {'left': -v, 'bottom': u, 'right': v, 'top': -u}[side]
def tip(n):                                                      # inner end of the lead (bond point)
    s, x, y = leads[n]; d = LEAD_L
    return {'left': (x + d, y), 'right': (x - d, y), 'bottom': (x, y + d), 'top': (x, y - d)}[s]
for side in ('left', 'bottom', 'right', 'top'):
    ps = sorted([p for p in pads if p["pkg_side"] == side], key=lambda p: ccw_key(side, p['u'], p['v']))
    ls = sorted([n for n in leads if leads[n][0] == side], key=lambda n: ccw_key(side, leads[n][1], leads[n][2]))
    assert len(ps) == len(ls) == 6
    for p, n in zip(ps, ls): p['lead'] = n
for p in pads:
    tx, ty = tip(p['lead']); p['wire_mm'] = round(math.hypot(tx - p['u'], ty - p['v']), 3)
# crossing check: every pair of wires (proper segment intersection)
def cross(a, b, c, d):
    def o(p, q, r): return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
    return o(a, b, c) * o(a, b, d) < 0 and o(c, d, a) * o(c, d, b) < 0
segs = [((p['u'], p['v']), tip(p['lead'])) for p in pads]
crossings = sum(cross(*segs[i], *segs[j]) for i in range(24) for j in range(i + 1, 24))
# the alternative (pad n -> lead n) for comparison
segs_n = [((p['u'], p['v']), tip(p['pad'])) for p in pads]
crossings_n = sum(cross(*segs_n[i], *segs_n[j]) for i in range(24) for j in range(i + 1, 24))
pads.sort(key=lambda p: p['pad'])
# CSV r3
hdr = list(rows[0].keys()) + ['qfn24_lead', 'lead_side']
with open(out_csv, 'w', newline='') as f:
    w = csv.writer(f, lineterminator='\n'); w.writerow(hdr)
    for p in pads:
        r = dict(p['row']); r['candidate_gds_sha256'] = sha; r['status'] = 'chip_of_record'
        w.writerow([r[k] for k in rows[0].keys()] + [p['lead'], p['pkg_side']])
# SVG (1 mm = S px, origin at the package centre, y up)
S, M = 200, 1.25
X = lambda u: round((u + H + M) * S, 2); Y = lambda v: round((H + M - v) * S, 2)
size = round((BODY + 2 * M) * S)
o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size + 70}" viewBox="0 0 {size} {size + 70}" font-family="Helvetica, Arial, sans-serif">',
     f'<rect width="100%" height="100%" fill="#ffffff"/>',
     f'<text x="{size / 2}" y="28" font-size="18" text-anchor="middle" fill="#111">G1 QFN24 bond plan, top view (die GDS sha256 {sha[:8]}…)</text>',
     f'<rect x="{X(-H)}" y="{Y(H)}" width="{BODY * S}" height="{BODY * S}" fill="#f4f4f2" stroke="#333" stroke-width="2"/>',
     f'<rect x="{X(-PADDLE / 2)}" y="{Y(PADDLE / 2)}" width="{PADDLE * S}" height="{PADDLE * S}" fill="#e3e3de" stroke="#777" stroke-dasharray="6 4"/>',
     f'<text x="{X(0)}" y="{Y(-PADDLE / 2) - 8}" font-size="11" text-anchor="middle" fill="#555">exposed paddle = VSS</text>',
     f'<circle cx="{X(-H + 0.22)}" cy="{Y(H - 0.22)}" r="7" fill="#111"/>',
     f'<text x="{X(-H + 0.36)}" y="{Y(H - 0.22) + 4}" font-size="12" fill="#111">pin 1</text>']
hw = W / 2
o.append(f'<rect x="{X(-hw)}" y="{Y(hw)}" width="{W * S}" height="{W * S}" fill="#cfd8e3" stroke="#1f3b5a" stroke-width="1.5"/>')
o.append(f'<text x="{X(0)}" y="{Y(0.05)}" font-size="9" text-anchor="middle" fill="#1f3b5a">die 1414 um</text>')
o.append(f'<line x1="{X(-0.09)}" y1="{Y(-0.04)}" x2="{X(0.07)}" y2="{Y(-0.04)}" stroke="#1f3b5a" stroke-width="1.5"/>')
o.append(f'<path d="M {X(0.09)} {Y(-0.04)} l -8 -4 l 0 8 z" fill="#1f3b5a"/>')
o.append(f'<text x="{X(0)}" y="{Y(-0.10)}" font-size="9" text-anchor="middle" fill="#1f3b5a">GDS north</text>')
for n, (s, x, y) in leads.items():
    if s in ('left', 'right'): rx, ry, rw, rh = (x if s == 'left' else x - LEAD_L), y + LEAD_W / 2, LEAD_L, LEAD_W
    else: rx, ry, rw, rh = x - LEAD_W / 2, (y + LEAD_L if s == 'bottom' else y), LEAD_W, LEAD_L
    o.append(f'<rect x="{X(rx)}" y="{Y(ry)}" width="{rw * S}" height="{rh * S}" fill="#c9a94a" stroke="#6b5518"/>')
    net = next(p['net'] for p in pads if p['lead'] == n)
    dx, dy, anchor, rot = {'left': (-0.08, 0, 'end', 0), 'right': (0.08, 0, 'start', 0), 'bottom': (0, -0.08, 'end', -90), 'top': (0, 0.08, 'start', -90)}[s]
    tx, ty = X(x + dx), Y(y + dy) + (4 if rot == 0 else 0)
    o.append(f'<text x="{tx}" y="{ty}" font-size="12" text-anchor="{anchor}" fill="#111" transform="rotate({rot} {tx} {ty})"><tspan font-weight="bold">{n}</tspan><tspan dx="5">{net}</tspan></text>')
for p in pads:
    ow = p['w_um'] / 1000
    o.append(f'<line x1="{X(p["u"])}" y1="{Y(p["v"])}" x2="{X(tip(p["lead"])[0])}" y2="{Y(tip(p["lead"])[1])}" stroke="#b03a2e" stroke-width="1.4"/>')
    o.append(f'<rect x="{X(p["u"] - ow / 2)}" y="{Y(p["v"] + ow / 2)}" width="{ow * S}" height="{ow * S}" fill="#ffffff" stroke="#1f3b5a"/>')
    s = p['pkg_side']; inset = 0.07
    dx, dy, anchor, rot = {'left': (inset, 0, 'start', 0), 'right': (-inset, 0, 'end', 0), 'bottom': (0, inset, 'start', -90), 'top': (0, -inset, 'end', -90)}[s]
    tx, ty = X(p['u'] + dx), Y(p['v'] + dy) + (3 if rot == 0 else 0)
    o.append(f'<text x="{tx}" y="{ty}" font-size="8" text-anchor="{anchor}" fill="#1f3b5a" transform="rotate({rot} {tx} {ty})">{p["pad"]} {p["net"]}</text>')
o.append(f'<text x="{size / 2}" y="{size + 32}" font-size="12" text-anchor="middle" fill="#333">Leads counter-clockwise from pin 1 (top-left). Each die pad bonds to the lead opposite it; {crossings} wire crossings.</text>')
o.append(f'<text x="{size / 2}" y="{size + 10}" font-size="12" text-anchor="middle" fill="#333">Die rotated 90 deg clockwise from the GDS view: GDS south edge (pads 1-6) faces leads 1-6; GDS north edge faces leads 13-18.</text>')
o.append(f'<text x="{size / 2}" y="{size + 54}" font-size="12" text-anchor="middle" fill="#333">Package outline, lead and paddle sizes nominal (drawing only). Die pads labelled "die pad number, net".</text>')
o.append('</svg>')
open(out_svg, 'w').write('\n'.join(o) + '\n')
summary = dict(gds=gds, gds_sha256=sha, out_csv=out_csv, out_svg=out_svg, crossings_opposite=crossings, crossings_if_pad_n_to_lead_n=crossings_n,
               labels_checked=sum(1 for p in pads if p['label']),
               pads=[{k: p[k] for k in ('pad', 'net', 'gds_side', 'x_um', 'y_um', 'w_um', 'h_um', 'pkg_side', 'lead', 'wire_mm')} for p in pads])
open(out_json, 'w').write(json.dumps(summary, indent=1) + '\n')
print(json.dumps({k: v for k, v in summary.items() if k != 'pads'}))
for p in summary['pads']: print(p)

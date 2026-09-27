#!/usr/bin/env python3
"""Bond-wire geometry of the r3 bond plan in package coordinates (nominal QFN24 4x4 mm, 0.5 mm pitch,
lead 0.25 x 0.40 mm, paddle 2.60 mm as in padframe/bondplan_20260925.py). Die rotated 90 deg CW, centred."""
import json, math, sys, itertools
d = json.load(open(sys.argv[1])); pads = d['pads']
BODY, PITCH, LW, LL = 4.0, 0.5, 0.25, 0.40
H = BODY / 2; offs = [(k - 2.5) * PITCH for k in range(6)]
leads = {}
for k in range(6):
    leads[1 + k] = ('left', -H, -offs[k]); leads[7 + k] = ('bottom', offs[k], -H)
    leads[13 + k] = ('right', H, offs[k]); leads[19 + k] = ('top', -offs[k], H)
def tip(n):
    s, x, y = leads[n]
    return {'left': (x + LL, y), 'right': (x - LL, y), 'bottom': (x, y + LL), 'top': (x, y - LL)}[s]
C = 0.707  # die centre, mm
def pk(x, y):  # GDS um -> package mm, 90 deg CW: (u, v) = (y', -x')
    return ((y / 1000 - C), -(x / 1000 - C))
def segdist(p1, p2, q1, q2):
    def pd(p, a, b):
        ax, ay = a; bx, by = b; px, py = p; dx, dy = bx - ax, by - ay
        t = max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
        return math.hypot(px - ax - t * dx, py - ay - t * dy)
    return min(pd(p1, q1, q2), pd(p2, q1, q2), pd(q1, p1, p2), pd(q2, p1, p2))
out = []
W = {}
for p in pads:
    u, v = pk(p['x_um'], p['y_um']); t = tip(p['lead']); W[p['pad']] = ((u, v), t)
    side = leads[p['lead']][0]
    normal = {'left': (-1, 0), 'right': (1, 0), 'bottom': (0, -1), 'top': (0, 1)}[side]
    dx, dy = t[0] - u, t[1] - v; L = math.hypot(dx, dy)
    ang = math.degrees(math.acos((dx * normal[0] + dy * normal[1]) / L))
    # angle at the lead: deviation from the lead axis
    out.append(dict(pad=p['pad'], net=p['net'], lead=p['lead'], wire_mm=round(L, 3), angle_from_edge_normal_deg=round(ang, 1)))
pairs = []
for a, b in itertools.combinations(W, 2):
    pairs.append((segdist(*W[a], *W[b]), a, b))
pairs.sort()
# distance of each wire (2D projection) to any other pad opening centre (on the die only)
near = []
for a in W:
    for p in pads:
        if p['pad'] == a: continue
        c = pk(p['x_um'], p['y_um'])
        (p1, p2) = W[a]
        dd = segdist(c, c, p1, p2) if False else min(segdist(p1, p2, c, (c[0]+1e-9, c[1])), 9)
        near.append((round(dd * 1000, 1), a, p['pad']))
near.sort()
res = dict(wires=out, max_angle_deg=max(o['angle_from_edge_normal_deg'] for o in out),
           max_wire_mm=max(o['wire_mm'] for o in out), min_wire_mm=min(o['wire_mm'] for o in out),
           closest_wire_pairs_um=[(round(x * 1000, 1), a, b) for x, a, b in pairs[:8]],
           closest_wire_to_other_pad_centre_um=near[:8],
           pad_pitch_um=112.0, opening_um=65.8, gap_between_openings_um=round(112 - 65.8, 1))
json.dump(res, open(sys.argv[2], 'w'), indent=1)
print(json.dumps(res, indent=1))

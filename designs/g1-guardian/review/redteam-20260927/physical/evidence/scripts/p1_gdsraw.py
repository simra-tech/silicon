#!/usr/bin/env python3
"""Raw GDSII record audit (no KLayout): structure names, element hygiene, grid, angles, limits."""
import struct, sys, json, collections, math, hashlib
fn, out = sys.argv[1], sys.argv[2]
data = open(fn, 'rb').read()
res = {'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}
def real8(b):
    s = -1 if b[0] & 0x80 else 1; e = (b[0] & 0x7f) - 64
    m = int.from_bytes(b[1:8], 'big') / float(1 << 56)
    return s * m * 16.0 ** e
MASK = {(1,0),(5,0),(6,0),(7,0),(8,0),(10,0),(19,0),(29,0),(30,0),(49,0),(50,0),(66,0),(67,0),(125,0),(126,0),(133,0),(134,0),(9,0),(14,0),(31,0),(32,0),(36,0),(44,0),(46,0),(28,0),(29,0),(128,0),(129,0),(24,0),(25,0),(1,22),(5,22),(8,22),(10,22),(30,22),(50,22),(67,22),(126,22),(134,22)}
MANH_ONLY = {(6,0),(19,0),(29,0),(49,0),(66,0),(125,0),(133,0),(129,0)}
pos = 0; cells = collections.OrderedDict(); names = collections.Counter(); refs = collections.Counter()
cur = None; el = None; stats = collections.Counter(); issues = collections.defaultdict(list)
layers = collections.Counter(); texts_layers = collections.Counter(); maxpts = (0, None)
pathtypes = collections.Counter(); widths0 = []; mags = collections.Counter(); angles = collections.Counter()
units = None; hdr = None; libname = None; props = 0
def add(k, v):
    if len(issues[k]) < 30: issues[k].append(v)
    stats['issue_'+k] += 1
while pos < len(data):
    ln, rt = struct.unpack('>HH', data[pos:pos+4])
    if ln < 4: break
    body = data[pos+4:pos+ln]; pos += ln
    if rt == 0x0002: hdr = struct.unpack('>h', body)[0]
    elif rt == 0x0206: libname = body.rstrip(b'\0').decode()
    elif rt == 0x0305: units = (real8(body[:8]), real8(body[8:16]))
    elif rt == 0x0606:
        cur = body.rstrip(b'\0').decode('latin1'); names[cur] += 1; cells[cur] = collections.Counter()
    elif rt in (0x0800, 0x0900, 0x0A00, 0x0B00, 0x0C00, 0x2D00, 0x1500):
        el = {'t': rt}; cells[cur][{0x0800:'boundary',0x0900:'path',0x0A00:'sref',0x0B00:'aref',0x0C00:'text',0x2D00:'box',0x1500:'node'}[rt]] += 1
    elif rt == 0x0D02: el['l'] = struct.unpack('>h', body)[0]
    elif rt in (0x0E02, 0x1602, 0x2E02): el['d'] = struct.unpack('>h', body)[0]
    elif rt == 0x0F03: el['w'] = struct.unpack('>i', body)[0]
    elif rt == 0x2102: el['pt'] = struct.unpack('>h', body)[0]
    elif rt == 0x1206: el['sname'] = body.rstrip(b'\0').decode('latin1')
    elif rt == 0x1906: el['s'] = body.rstrip(b'\0').decode('latin1')
    elif rt == 0x1B05: el['mag'] = real8(body)
    elif rt == 0x1C05: el['ang'] = real8(body)
    elif rt == 0x2B02: props += 1
    elif rt == 0x1003:
        n = len(body)//4; el['xy'] = struct.unpack('>%di' % n, body)
    elif rt == 0x1100:
        t = el['t']; ld = (el.get('l'), el.get('d'))
        xy = el.get('xy', ()); pts = list(zip(xy[0::2], xy[1::2]))
        if t in (0x0800, 0x0900): layers[ld] += 1
        if t == 0x0800:
            if len(pts) > maxpts[0]: maxpts = (len(pts), cur)
            if len(pts) > 8191: add('boundary_gt8191pts', (cur, ld, len(pts)))
            if pts[0] != pts[-1]: add('boundary_not_closed', (cur, ld))
            p = pts[:-1]
            if len(p) < 3: add('boundary_lt3', (cur, ld, pts[:4]))
            a = 0
            for i in range(len(p)):
                x1, y1 = p[i]; x2, y2 = p[(i+1) % len(p)]; a += x1*y2 - x2*y1
            if a == 0: add('boundary_zero_area', (cur, ld, pts[:5]))
            dup = sum(1 for i in range(len(p)) if p[i] == p[(i+1) % len(p)])
            if dup: add('boundary_dup_vertex', (cur, ld, dup))
            if ld in MASK:
                if any(x % 5 or y % 5 for x, y in p): add('offgrid5nm_boundary', (cur, ld, [q for q in p if q[0] % 5 or q[1] % 5][:2]))
                for i in range(len(p)):
                    x1, y1 = p[i]; x2, y2 = p[(i+1) % len(p)]; dx, dy = x2-x1, y2-y1
                    if dx and dy:
                        if ld in MANH_ONLY or abs(dx) != abs(dy): add('non_manhattan_or_45', (cur, ld, (x1, y1, x2, y2))); break
        elif t == 0x0900:
            w = el.get('w', 0); pathtypes[el.get('pt', 0)] += 1
            if w == 0: add('path_width0', (cur, ld, pts[:3]))
            if w < 0: add('path_absolute_width', (cur, ld, w))
            if len(pts) < 2: add('path_lt2pts', (cur, ld))
            if any(pts[i] == pts[i+1] for i in range(len(pts)-1)): add('path_zero_segment', (cur, ld))
            if ld in MASK and (w % 10 if el.get('pt',0) in (0,2,4) else 0): add('path_width_odd_grid', (cur, ld, w))
            if ld in MASK and any(x % 5 or y % 5 for x, y in pts): add('offgrid5nm_path', (cur, ld))
        elif t == 0x0C00:
            texts_layers[ld] += 1
            if not el.get('s'): add('text_empty', (cur, ld))
            if 'mag' in el: mags[('text', el['mag'])] += 1
        elif t in (0x0A00, 0x0B00):
            refs[el['sname']] += 1
            if 'mag' in el and el['mag'] != 1.0: add('ref_mag', (cur, el['sname'], el['mag']))
            ang = el.get('ang', 0.0)
            angles[ang] += 1
            if ang % 90: add('ref_angle', (cur, el['sname'], ang))
            if any(x % 5 or y % 5 for x, y in pts): add('ref_origin_offgrid5nm', (cur, el['sname'], pts[0]))
            if t == 0x0B00: add('aref_present', (cur, el['sname']))
        elif t in (0x2D00, 0x1500): add('box_or_node_element', (cur, ld))
        el = None
    elif rt == 0x0400: break
res['header_version'] = hdr; res['libname'] = libname; res['units'] = units
res['ncells'] = len(cells); res['dup_names'] = [n for n, c in names.items() if c > 1]
res['empty_cells'] = [n for n, c in cells.items() if sum(c.values()) == 0]
res['undefined_refs'] = [n for n in refs if n not in cells]
res['unreferenced'] = [n for n in cells if n not in refs]
res['names_gt32'] = sum(1 for n in cells if len(n) > 32)
res['names_bad_chars'] = [n for n in cells if not all(ch.isalnum() or ch in '_$' for ch in n)]
res['max_boundary_pts'] = maxpts
res['layers_geom'] = {'%d/%d' % k: v for k, v in sorted(layers.items())}
res['layers_text'] = {'%d/%d' % k: v for k, v in sorted(texts_layers.items())}
res['pathtypes'] = dict(pathtypes); res['ref_angles'] = {str(k): v for k, v in angles.items()}; res['properties'] = props
res['issue_counts'] = {k: v for k, v in stats.items()}; res['issues'] = issues
json.dump(res, open(out, 'w'), indent=1, default=str)
print(json.dumps({k: res[k] for k in ('sha256','header_version','libname','units','ncells','dup_names','empty_cells','undefined_refs','unreferenced','names_gt32','names_bad_chars','max_boundary_pts','pathtypes','ref_angles','properties','issue_counts')}, indent=1, default=str))

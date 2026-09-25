#!/usr/bin/env python3
"""Raw GDSII record comparison of two files (host python3, no KLayout). Splits both record streams into the
library header and one record list per structure (BGNSTR..ENDSTR, keyed by STRNAME). Structures are paired by
name through the rename map; within each pair the records are compared one by one, with SNAME references mapped.
Usage: gds_record_diff.py <r1.gds> <r2.gds> <old:new,...> [out.json]"""
import sys, json, struct, hashlib, collections
NAMES = {0x00: 'HEADER', 0x01: 'BGNLIB', 0x02: 'LIBNAME', 0x05: 'BGNSTR', 0x06: 'STRNAME', 0x12: 'SNAME', 0x19: 'STRING',
         0x1B: 'MAG', 0x0D: 'LAYER', 0x16: 'TEXTTYPE', 0x17: 'PRESENTATION', 0x10: 'XY', 0x1A: 'STRANS', 0x0C: 'TEXT'}
def recs(p):
    b = open(p, 'rb').read(); i = 0; out = []
    while i < len(b):
        n, t = struct.unpack('>HH', b[i:i + 4])
        if n == 0: break
        out.append((t >> 8, b[i + 4:i + n])); i += n
    return out
REN = dict(x.split(':') for x in sys.argv[3].split(',') if x)
def split(rs):
    head, strs, cur, order = [], {}, None, []
    for t, d in rs:
        if t == 0x05: cur = [(t, d)]; continue
        if cur is None: head.append((t, d)); continue
        cur.append((t, d))
        if t == 0x07:
            name = next(x for tt, x in cur if tt == 0x06).rstrip(b'\0').decode('latin1'); strs[name] = cur; order.append(name); cur = None
    return head, strs, order
A, B = recs(sys.argv[1]), recs(sys.argv[2])
(ha, sa, oa), (hb, sb, ob) = split(A), split(B)
res = dict(a=sys.argv[1], a_sha256=hashlib.sha256(open(sys.argv[1], 'rb').read()).hexdigest(),
           b=sys.argv[2], b_sha256=hashlib.sha256(open(sys.argv[2], 'rb').read()).hexdigest(), rename=REN,
           records=[len(A), len(B)], structures=[len(sa), len(sb)], header_records_equal=ha == hb,
           structure_names_equal_modulo_rename=sorted(REN.get(n, n) for n in sa) == sorted(sb),
           structure_order_equal_modulo_rename=[REN.get(n, n) for n in oa] == ob)
enc = lambda n: n.encode('latin1')
def elements(rs, mapping):
    """Multiset of elements (records from element start to ENDEL, SNAME mapped) plus the structure header."""
    hdr, els, cur = [], collections.Counter(), None
    for t, d in rs:
        if t in (0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x15, 0x2D): cur = [(t, d)]; continue  # BOUNDARY PATH SREF AREF TEXT NODE BOX
        if cur is None:
            if t == 0x06: d = enc(mapping.get(d.rstrip(b'\0').decode('latin1'), d.rstrip(b'\0').decode('latin1')))
            hdr.append((t, d)); continue
        if t == 0x12: d = enc(mapping.get(d.rstrip(b'\0').decode('latin1'), d.rstrip(b'\0').decode('latin1')))
        if t == 0x06 or t == 0x12: pass
        cur.append((t, d.rstrip(b'\0') if t in (0x12, 0x19) else d))
        if t == 0x11: els[tuple(cur)] += 1; cur = None
    return hdr, els
def show(el):
    out = {}
    for t, d in el:
        k = NAMES.get(t, hex(t))
        out[k] = d.decode('latin1') if t in (0x12, 0x19) else (list(struct.unpack('>%di' % (len(d) // 4), d)) if t == 0x10 else d.hex())
    return out
diffs = collections.defaultdict(list); n_el = [0, 0]; renamed_refs = collections.Counter()
for n, ra in sa.items():
    rb = sb.get(REN.get(n, n))
    if rb is None: diffs['missing_structure'].append(n); continue
    ha_, ea = elements(ra, REN); hb_, eb = elements(rb, {})
    n_el[0] += sum(ea.values()); n_el[1] += sum(eb.values())
    for t, d in ra:
        if t == 0x12 and d.rstrip(b'\0').decode('latin1') in REN: renamed_refs[f"{d.rstrip(bytes(1)).decode()} -> {REN[d.rstrip(bytes(1)).decode()]} (in {REN.get(n, n)})"] += 1
    if ha_ != hb_: diffs['structure_header'].append(n)
    if ea != eb:
        diffs['elements'].append(dict(structure=n, only_a=[show(e) for e in (ea - eb)], only_b=[show(e) for e in (eb - ea)]))
res['elements'] = n_el
res['renamed_structures'] = {o: REN[o] for o in REN if o in sa}
res['renamed_references'] = renamed_refs
res['differences'] = diffs
res['only_expected_differences'] = res['header_records_equal'] and res['structure_names_equal_modulo_rename'] and \
    set(diffs) == {'elements'} and len(diffs['elements']) == 1 and diffs['elements'][0]['structure'] == 'g1_chip_top' and \
    len(diffs['elements'][0]['only_a']) == 2 and len(diffs['elements'][0]['only_b']) == 2 and \
    sorted({k: v for k, v in e.items() if k != 'STRING'}.__repr__() for e in diffs['elements'][0]['only_a']) == \
    sorted({k: v for k, v in e.items() if k != 'STRING'}.__repr__() for e in diffs['elements'][0]['only_b'])
s = json.dumps(res, indent=1, default=str); print(s)
if len(sys.argv) > 4: open(sys.argv[4], 'w').write(s + '\n')

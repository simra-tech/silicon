# Cut the GATE macro cell from the chip GDS and compare it with the block GDS files (flattened, per layer)
import pya
ch = pya.Layout(); ch.read(chip)
cands = [c for c in ch.each_cell() if 'g1_gate' in c.name]
print('chip cells matching g1_gate:', [(c.name, str(c.bbox()), [ch.cell(p).name for p in c.each_parent_cell()]) for c in cands])
cell = [c for c in cands if c.name.endswith('retained_g1_gate')][0]
for inst in ch.cell([p for p in cell.each_parent_cell()][0]).each_inst():
    if inst.cell_index == cell.cell_index(): print('placed', inst.trans)
out = pya.Layout(); out.dbu = ch.dbu
top = out.create_cell('g1_gate'); top.copy_tree(cell)
print('cut sub-cells:', sorted(c.name for c in out.each_cell()))
out.write(cutpath)
def layers(ly):
    t = ly.top_cell(); d = {}
    for li in ly.layer_indexes():
        info = ly.get_info(li); r = pya.Region(t.begin_shapes_rec(li)); r.merge()
        tx = sorted((s.text_string, s.text_pos.x, s.text_pos.y) for s in (it.shape().text.transformed(it.trans()) for it in [])) if False else None
        d[(info.layer, info.datatype)] = r
    return d
def texts(ly):
    t = ly.top_cell(); res = []
    for li in ly.layer_indexes():
        it = t.begin_shapes_rec(li)
        while not it.at_end():
            s = it.shape()
            if s.is_text():
                tt = s.text.transformed(it.trans())
                res.append((ly.get_info(li).layer, ly.get_info(li).datatype, tt.string, tt.x, tt.y))
            it.next()
    return sorted(res)
a = pya.Layout(); a.read(cutpath)
for ref in refs.split(','):
    b = pya.Layout(); b.read(ref)
    print('=== vs', ref.split('/')[-1], 'top', b.top_cell().name, 'bbox cut', a.top_cell().bbox(), 'ref', b.top_cell().bbox())
    la, lb = layers(a), layers(b)
    ndiff = nfilldiff = 0
    for k in sorted(set(la) | set(lb)):
        ra = la.get(k, pya.Region()); rb = lb.get(k, pya.Region())
        x = ra ^ rb
        if not x.is_empty():
            if k[1] == 22: nfilldiff += 1
            else: ndiff += 1
            print('  layer %d/%d differs: cut %.3f um2 ref %.3f um2 xor %.3f um2' % (k[0], k[1], ra.area()*1e-6, rb.area()*1e-6, x.area()*1e-6))
    print('  non-fill layers differing:', ndiff, ' fill (datatype 22) layers differing:', nfilldiff, ' layers compared:', len(set(la) | set(lb)))
    ta, tb = texts(a), texts(b)
    print('  texts: cut %d ref %d identical=%s' % (len(ta), len(tb), ta == tb))
    if ta != tb:
        sa, sb = set(ta), set(tb)
        print('   only in cut:', sorted(sa - sb)[:10]); print('   only in ref:', sorted(sb - sa)[:10])

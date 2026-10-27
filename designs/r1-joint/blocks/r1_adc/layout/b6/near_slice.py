# T2l (layout B6): where do the nets of `nets` (comma list) come close to top_p / top_n inside the circuit r1_adc_slice
# of an lvsdb? The lvsdb layers have no names (l<k>); the GDS layer of each is read from the LVS layout. For every
# layer pair (A of the net, B of the top plate): same layer = side-wall neighbourhood within d um; different layers =
# projected overlap (vertical coupling). Prints area and the largest boxes (slice-local um).
# usage: klayout -b -r near_slice.py -rd db=<lvsdb> -rd nets=clk,trk0,vdd -rd d=0.6
import pya
lvs = pya.LayoutVsSchematic(); lvs.read(db)
c = lvs.netlist().circuit_by_name('r1_adc_slice')
ly = lvs.internal_layout()
GDS = {(8, 0): 'M1', (10, 0): 'M2', (30, 0): 'M3', (50, 0): 'M4', (67, 0): 'M5', (126, 0): 'TM1', (36, 0): 'MIM'}
names = {}
for ln in lvs.layer_names():
    try:
        names[ln] = str(lvs.layer_info(lvs.layer_by_name(ln).layer_index() if hasattr(lvs.layer_by_name(ln), 'layer_index') else lvs.layer_by_name(ln).index()))
    except Exception as e:
        names[ln] = ln
dd = int(float(d) * 1000)
def regs(net):
    out = {}
    for ln in lvs.layer_names():
        r = lvs.shapes_of_net(c.net_by_name(net), lvs.layer_by_name(ln), True)
        if not r.is_empty():
            out[ln] = r.merged()
    return out
TP = {t: regs(t) for t in ('top_p', 'top_n')}
for t in TP:
    for ln, r in TP[t].items():
        print('%s layer %s (%s): %d shapes bbox %s' % (t, ln, names[ln], r.count(), r.bbox().to_dtype(0.001)))
for nn in nets.split(','):
    if c.net_by_name(nn) is None:
        print(nn, 'not in r1_adc_slice'); continue
    R = regs(nn)
    for t in ('top_p', 'top_n'):
        tot = 0.0
        for ln, ra in R.items():
            for ln2, rb in TP[t].items():
                near = (ra & rb.sized(dd)) if ln == ln2 else (ra & rb)
                if near.is_empty():
                    continue
                a = near.area() * 1e-6
                tot += a
                bxs = sorted([p.bbox().to_dtype(0.001) for p in near.each()], key=lambda b: -b.area())
                print('%-6s %-5s %-4s/%-4s %s area %7.3f um2 n %3d  %s' % (nn, t, ln, ln2, 'side' if ln == ln2 else 'ovl ', a,
                      near.count(), ' '.join('(%.1f,%.1f;%.1f,%.1f)' % (b.left, b.bottom, b.right, b.top) for b in bxs[:6])))
        print('%-6s %-5s total %.3f um2' % (nn, t, tot))

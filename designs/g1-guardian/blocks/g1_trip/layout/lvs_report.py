# klayout -b -r lvs_report.py -rd db=<lvsdb>  : print non-matching objects of the LVS cross reference
import pya
lvs = pya.LayoutVsSchematic()
lvs.read(db)
xr = lvs.xref()
bad = {pya.NetlistCrossReference.NoMatch: 'NoMatch', pya.NetlistCrossReference.Mismatch: 'Mismatch',
       pya.NetlistCrossReference.Skipped: 'Skipped', pya.NetlistCrossReference.MatchWithWarning: 'Warn'}
def nm(o):
    if o is None:
        return '-'
    return o.expanded_name() if hasattr(o, 'expanded_name') else o.name
for cp in xr.each_circuit_pair():
    st = cp.status()
    print('CIRCUIT', nm(cp.first()), '<->', nm(cp.second()), bad.get(st, 'Match'))
    if st == pya.NetlistCrossReference.Match:
        continue
    n = 0
    for pp in xr.each_pin_pair(cp):
        if pp.status() != pya.NetlistCrossReference.Match:
            print('  PIN', nm(pp.first()), nm(pp.second()), bad.get(pp.status(), pp.status()))
    for npair in xr.each_net_pair(cp):
        if npair.status() != pya.NetlistCrossReference.Match:
            a, b = npair.first(), npair.second()
            print('  NET', nm(a), '<->', nm(b), bad.get(npair.status(), npair.status()))
            for net in (a, b):
                if net is None: continue
                terms = ['%s.%s' % (t.device().expanded_name(), t.terminal_def().name) for t in net.each_terminal()]
                pins = [p.pin().expanded_name() for p in net.each_pin()]
                subs = ['%s.%s' % (s.subcircuit().expanded_name(), s.pin().expanded_name()) for s in net.each_subcircuit_pin()]
                print('      ', 'L' if net is a else 'S', 'terms', terms[:12], 'pins', pins, 'subs', subs[:6])
            n += 1
            if n > 30: break
    n = 0
    for dp in xr.each_device_pair(cp):
        if dp.status() != pya.NetlistCrossReference.Match:
            a, b = dp.first(), dp.second()
            def dd(d):
                if d is None: return '-'
                return '%s(%s) %s' % (d.expanded_name(), d.device_class().name, ' '.join('%s=%s' % (t.name, d.net_for_terminal(t.id()).expanded_name() if d.net_for_terminal(t.id()) else '?') for t in d.device_class().terminal_definitions()))
            print('  DEV', dd(a), '<->', dd(b), bad.get(dp.status(), dp.status()))
            n += 1
            if n > 30: break

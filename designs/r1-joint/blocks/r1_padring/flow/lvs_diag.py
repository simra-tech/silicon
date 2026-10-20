# Summarise the unmatched devices/nets of a KLayout LVS database.  klayout -b -r lvs_diag.py -rd db=<lvsdb>
import pya, collections
l = pya.LayoutVsSchematic(); l.read(db); x = l.xref()
for cp in x.each_circuit_pair():
    print('circuit', cp.first().name if cp.first() else None, cp.second().name if cp.second() else None, cp.status())
    cl = collections.Counter(); ref = collections.Counter(); ex = {}
    for p in x.each_device_pair(cp):
        a, b = p.first(), p.second()
        st = str(p.status())
        key = (st, a.device_class().name if a else None, b.device_class().name if b else None)
        cl[key] += 1
        ex.setdefault(key, (a.expanded_name() if a else None, b.expanded_name() if b else None))
    for k, v in sorted(cl.items(), key=lambda t: str(t)): print('  dev', k, v, ex[k])
    # unmatched nets
    n = collections.Counter(str(p.status()) for p in x.each_net_pair(cp)); print('  nets', dict(n))
    for p in list(x.each_net_pair(cp)):
        if str(p.status()) != 'Match':
            a, b = p.first(), p.second()
            print('   net', str(p.status()), a.expanded_name() if a else None, b.expanded_name() if b else None,
                  (len(list(a.each_terminal())) if a else None), (len(list(b.each_terminal())) if b else None))
            break
    print('  layout devices total', len(list(cp.first().each_device())), 'ref devices total', len(list(cp.second().each_device())))
    c = collections.Counter(d.device_class().name for d in cp.first().each_device()); print('  layout classes', dict(c))
    c = collections.Counter(d.device_class().name for d in cp.second().each_device()); print('  ref classes', dict(c))

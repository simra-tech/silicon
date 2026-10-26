"""Summarise a KLayout .lvsdb (options -rd nn=<nets shown> -rd nd=<devices shown>): per circuit pair status, unmatched nets and devices, device and net counts.
klayout -b -r lvsdb_report.py -rd db=<file.lvsdb>"""
import pya
db = globals()['db']; NN = int(globals().get('nn', '25')); ND = int(globals().get('nd', '15'))
l2n = pya.LayoutVsSchematic(); l2n.read(db)
xr = l2n.xref()
for cp in xr.each_circuit_pair():
    a, b = cp.first(), cp.second()
    print('CIRCUIT', a.name if a else None, b.name if b else None, cp.status())
    na = sum(1 for _ in a.each_net()) if a else 0; nb = sum(1 for _ in b.each_net()) if b else 0
    da = sum(1 for _ in a.each_device()) if a else 0; dbb = sum(1 for _ in b.each_device()) if b else 0
    print('  nets layout/schematic', na, nb, ' devices', da, dbb)
    n = 0
    for np_ in xr.each_net_pair(cp):
        if np_.status() != pya.NetlistCrossReference.Match:
            n += 1
            if n <= NN:
                print('  NET', np_.status(), np_.first().expanded_name() if np_.first() else None, np_.second().expanded_name() if np_.second() else None)
    print('  net non-matches', n)
    m = 0
    for dp in xr.each_device_pair(cp):
        if dp.status() != pya.NetlistCrossReference.Match:
            m += 1
            if m <= ND:
                d1, d2 = dp.first(), dp.second()
                print('  DEV', dp.status(), d1.expanded_name() if d1 else None, d1.device_class().name if d1 else '', d2.expanded_name() if d2 else None,
                      [(p.name, round(d1.parameter(p.name), 4)) for p in d1.device_class().parameter_definitions()] if d1 else '',
                      [(p.name, round(d2.parameter(p.name), 4)) for p in d2.device_class().parameter_definitions()] if d2 else '',
                      [(t.name, (lambda x: x.expanded_name() if x else None)(d1.net_for_terminal(t.id()))) for t in d1.device_class().terminal_definitions()] if d1 else '',
                      [(t.name, (lambda x: x.expanded_name() if x else None)(d2.net_for_terminal(t.id()))) for t in d2.device_class().terminal_definitions()] if d2 else '')
    print('  device non-matches', m)

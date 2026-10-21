# KLayout batch: summarise an LVS database (-rd db=<file.lvsdb> [-rd n=20]). Prints device/net counts per side and
# the first n unmatched or mismatched nets and devices of the top circuit pair.
import pya
lvs = pya.LayoutVsSchematic()
lvs.read(db)
N = int(globals().get('n', '20'))
xref = lvs.xref()
for cp in xref.each_circuit_pair():
    a, b = cp.first(), cp.second()
    print('circuit', a.name if a else None, b.name if b else None, 'status', cp.status())
    if a:
        print('  layout: devices', len(list(a.each_device())), 'nets', len(list(a.each_net())), 'pins', len(list(a.each_pin())))
    if b:
        print('  schematic: devices', len(list(b.each_device())), 'nets', len(list(b.each_net())), 'pins', len(list(b.each_pin())))
    k = 0
    for np_ in xref.each_net_pair(cp):
        if np_.status() != pya.NetlistCrossReference.Match and k < N:
            f, s = np_.first(), np_.second()
            print('  NET', np_.status(), f.expanded_name() if f else None, '|', s.expanded_name() if s else None)
            k += 1
    k = 0
    for dp in xref.each_device_pair(cp):
        if dp.status() != pya.NetlistCrossReference.Match and k < N:
            f, s = dp.first(), dp.second()
            def dd(d):
                if not d:
                    return None
                return '%s %s %s' % (d.expanded_name(), d.device_class().name,
                                     ' '.join('%s=%s' % (t.name, d.net_for_terminal(t.id()).expanded_name() if d.net_for_terminal(t.id()) else '-')
                                              for t in d.device_class().terminal_definitions()))
            print('  DEV', dp.status(), dd(f), '|', dd(s))
            k += 1

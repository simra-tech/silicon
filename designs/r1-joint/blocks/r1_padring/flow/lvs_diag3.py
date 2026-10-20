import pya
l = pya.LayoutVsSchematic(); l.read(db); x = l.xref()
def term(dev):
    out = []
    for t in dev.device_class().terminal_definitions():
        n = dev.net_for_terminal(t.id())
        out.append('%s=%s' % (t.name, n.expanded_name() if n else None))
    return ' '.join(out)
for cp in x.each_circuit_pair():
    for p in x.each_device_pair(cp):
        b = p.second()
        if str(p.status()) != 'Match' and b is not None and ('PAD16' in b.expanded_name() or 'PAD02' in b.expanded_name() or 'PAD01' in b.expanded_name()):
            a = p.first()
            print(str(p.status()), '| L:', a.expanded_name() if a else None, term(a) if a else '', '| R:', b.expanded_name(), term(b))

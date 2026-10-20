import pya
l = pya.LayoutVsSchematic(); l.read(db); x = l.xref()
for cp in x.each_circuit_pair():
    names = sorted(str(p.first().expanded_name() if p.first() else '-') + '|' + str(p.second().expanded_name() if p.second() else '-') for p in x.each_pin_pair(cp))
    print(len(names)); print(' '.join(names))

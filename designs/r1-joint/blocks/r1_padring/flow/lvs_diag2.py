import pya, collections, re
l = pya.LayoutVsSchematic(); l.read(db); x = l.xref()
for cp in x.each_circuit_pair():
    per = collections.Counter(); tot = collections.Counter()
    for p in x.each_device_pair(cp):
        b = p.second(); name = b.expanded_name() if b else str(p.first().expanded_name())
        m = re.search(r'(PAD\d+_[A-Z_]+|IO_[A-Z_0-9]+)', name)
        k = m.group(1) if m else name[:20]
        tot[k] += 1
        if str(p.status()) != 'Match': per[k] += 1
    for k in sorted(tot): print(k, 'mismatch', per[k], 'of', tot[k])
    print('unmatched nets (first 12)')
    c = 0
    for p in x.each_net_pair(cp):
        if str(p.status()) != 'Match' and c < 12:
            a, b = p.first(), p.second(); c += 1
            print('  ', str(p.status()), a.expanded_name() if a else None, '|', b.expanded_name() if b else None)

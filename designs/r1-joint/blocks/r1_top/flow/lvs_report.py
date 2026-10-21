# KLayout batch: summarise an LVS database (-rd db=<file.lvsdb> [-rd n=30]). Per circuit pair: status and counts;
# for non-matching pairs the first n unmatched nets, devices, pins and subcircuits. (Method of blocks/r1_safe/layout/lvs_report.py.)
import pya
lvs = pya.LayoutVsSchematic()
lvs.read(db)
N = int(globals().get('n', '30'))
xref = lvs.xref()
NC = pya.NetlistCrossReference
for cp in xref.each_circuit_pair():
    a, b = cp.first(), cp.second()
    st = cp.status()
    line = 'circuit %s | %s status %s' % (a.name if a else None, b.name if b else None, st)
    cnt = lambda c: (len(list(c.each_device())), len(list(c.each_net())), c.pin_count(), len(list(c.each_subcircuit())))
    if a: line += ' L(dev %d net %d pin %d sub %d)' % cnt(a)
    if b: line += ' S(dev %d net %d pin %d sub %d)' % cnt(b)
    print(line)
    if st == NC.Match:
        continue
    for kind, it in (('NET', xref.each_net_pair(cp)), ('DEV', xref.each_device_pair(cp)),
                     ('PIN', xref.each_pin_pair(cp)), ('SUB', xref.each_subcircuit_pair(cp))):
        k = 0
        for p in it:
            if p.status() != NC.Match and k < N:
                f, s = p.first(), p.second()
                nm = lambda o: (o.expanded_name() if hasattr(o, 'expanded_name') else o.name) if o else None
                print('  %s %s %s | %s' % (kind, p.status(), nm(f), nm(s)))
                k += 1

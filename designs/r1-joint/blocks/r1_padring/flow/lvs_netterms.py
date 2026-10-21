# Terminal count per device class on the nets $1, VSS, IOVSS of the layout and the reference netlist.
import pya, collections
l = pya.LayoutVsSchematic(); l.read(db); x = l.xref()
for cp in x.each_circuit_pair():
    for p in x.each_net_pair(cp):
        if str(p.status()) != 'Mismatch': continue
        for side, n in (('layout', p.first()), ('ref', p.second())):
            c = collections.Counter()
            for r in n.each_terminal():
                c[(r.device().device_class().name, r.terminal_def().name)] += 1
            print(side, n.expanded_name(), n.pin_count(), dict(c), 'subcircuit pins', sum(1 for _ in n.each_subcircuit_pin()))

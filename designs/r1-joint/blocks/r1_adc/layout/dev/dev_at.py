"""layout-B debug: devices of a circuit near a point, with terminal nets. klayout -b -r dev/dev_at.py -rd db=<lvsdb> -rd circuit=<c> -rd x=.. -rd y=.. [-rd r=5]"""
import pya
l2n = pya.LayoutVsSchematic(); l2n.read(globals()['db'])
c = l2n.netlist().circuit_by_name(globals()['circuit'])
x, y, r = float(globals()['x']), float(globals()['y']), float(globals().get('r', '5'))
dbu = l2n.internal_layout().dbu
for d in c.each_device():
    t = d.trans.disp
    if abs(t.x - x) < r and abs(t.y - y) < r:
        nets = {}
        for td in d.device_class().terminal_definitions():
            n = d.net_for_terminal(td.id())
            nets[td.name] = n.expanded_name() if n else None
        print(d.expanded_name(), d.device_class().name, round(t.x, 3), round(t.y, 3), nets, {p.name: round(d.parameter(p.name), 3) for p in d.device_class().parameter_definitions() if p.name in ('W', 'L')})

# klayout -b -r lvs_mismatches.py -rd db=<lvsdb>: list every non-Match device/net/pin pair
import pya, json
l = pya.LayoutVsSchematic(); l.read(db); x = l.xref()
out = []
for cp in x.each_circuit_pair():
    for kind, it in [('device', x.each_device_pair), ('net', x.each_net_pair), ('pin', x.each_pin_pair)]:
        for p in it(cp):
            if str(p.status()) == 'Match':
                continue
            a, b = p.first(), p.second()
            def desc(o):
                if o is None: return None
                if kind == 'device':
                    return dict(name=o.expanded_name(), cls=o.device_class().name,
                                params={pd.name: o.parameter(pd.id()) for pd in o.device_class().parameter_definitions()},
                                terms={t.name: (o.net_for_terminal(t.id()).expanded_name() if o.net_for_terminal(t.id()) else None)
                                       for t in o.device_class().terminal_definitions()})
                return o.expanded_name() if hasattr(o, 'expanded_name') else o.name
            out.append(dict(circuit=cp.first().name if cp.first() else None, kind=kind, status=str(p.status()),
                            layout=desc(a), reference=desc(b)))
print(json.dumps(out, indent=1, default=str))

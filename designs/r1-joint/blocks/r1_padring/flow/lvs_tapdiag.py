# Print the tap device pairs (status, parameters, terminal nets), the mismatching nets and the compare log of a KLayout LVS database.
#   klayout -b -r flow/lvs_tapdiag.py -rd db=<lvsdb>
import pya
l = pya.LayoutVsSchematic(); l.read(db); x = l.xref()
def desc(d):
    if d is None: return None
    t = ' '.join('%s=%s' % (td.name, (d.net_for_terminal(td.id()).expanded_name() if d.net_for_terminal(td.id()) else None)) for td in d.device_class().terminal_definitions())
    p = ' '.join('%s=%g' % (pd.name, d.parameter(pd.id())) for pd in d.device_class().parameter_definitions())
    return '%s %s [%s] %s' % (d.expanded_name(), d.device_class().name, t, p)
for cp in x.each_circuit_pair():
    print('circuit', cp.first().name, cp.second().name, cp.status())
    for p in x.each_device_pair(cp):
        a, b = p.first(), p.second()
        cn = (a or b).device_class().name.lower()
        if 'tap' in cn or str(p.status()) != 'Match':
            print(' DEV', p.status(), '| L:', desc(a), '| R:', desc(b))
    for p in x.each_net_pair(cp):
        if str(p.status()) != 'Match':
            print(' NET', p.status(), p.first().expanded_name() if p.first() else None, '|', p.second().expanded_name() if p.second() else None)
    try:
        for e in x.each_log_entry(cp): print(' LOG', e.severity, e.message)
    except Exception as ex: print(' no log API', ex)
    dc = l.netlist().device_class_by_name('ptap1') if l.netlist() else None
    if dc: print(' ptap1 class comparer', dc.equal_parameters if hasattr(dc, 'equal_parameters') else None)

# List nets and devices that do not match in a KLayout LVS database. klayout -b -r flow/lvs_netdiff.py -rd db=<lvsdb>
import pya
l = pya.LayoutVsSchematic(); l.read(db); x = l.xref()
for cp in x.each_circuit_pair():
    for p in x.each_net_pair(cp):
        st = str(p.status())
        if 'Match' != st: print('NET', st, p.first().expanded_name() if p.first() else None, '|', p.second().expanded_name() if p.second() else None)
    for p in x.each_device_pair(cp):
        st = str(p.status())
        if st != 'Match': print('DEV', st, p.first().expanded_name() if p.first() else None, '|', p.second().expanded_name() if p.second() else None) if st == 'MatchWithWarning' else None

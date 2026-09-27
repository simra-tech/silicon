# Metal-only connectivity of the r3 chip (M1..TM2 + vias), independent of the LVS deck.
# Pad -> net, top-level label names per net, supply-net distinctness, signal pad reach into the core.
import pya, json, os, collections
G = '/work/designs/g1-guardian/blocks/g1_padring/layout/g1_chip_top_1414_r3.gds'
OUT = '${BULK}/redteam-20260927/physical/p3'; os.makedirs(OUT, exist_ok=True)
ly = pya.Layout(); ly.read(G); top = ly.cell('g1_chip_top'); dbu = ly.dbu
l2n = pya.LayoutToNetlist(pya.RecursiveShapeIterator(ly, top, [])); l2n.threads = 2
names = [('M1',8),('V1',19),('M2',10),('V2',29),('M3',30),('V3',49),('M4',50),('V4',66),('M5',67),('TV1',125),('TM1',126),('TV2',133),('TM2',134)]
R = {n: l2n.make_layer(ly.layer(l, 0), n) for n, l in names}
seq = [n for n, _ in names]
for n in seq: l2n.connect(R[n])
for i in range(0, len(seq) - 2, 2):
    l2n.connect(R[seq[i]], R[seq[i+1]]); l2n.connect(R[seq[i+1]], R[seq[i+2]])
# pin-purpose shapes (x/2) also conduct in the flow; include them on their metal
for n, l in [('M1',8),('M2',10),('M3',30),('M4',50),('M5',67),('TM1',126),('TM2',134)]:
    li = ly.find_layer(l, 2)
    if li is not None:
        rp = l2n.make_layer(li, n + 'p'); l2n.connect(rp); l2n.connect(rp, R[n])
l2n.extract_netlist()
def probe(layer, x, y):
    net = l2n.probe_net(R[layer], pya.DPoint(x, y))
    return None if net is None else net
def key(net): return (net.circuit().name, net.cluster_id)
res = {}
pads = [(1,'VDD',395,101),(2,'VSS',507,101),(3,'IOVDD',619,101),(4,'IOVSS',731,101),(5,'VSS',843,101),(6,'IOVSS',955,101),
        (7,'VDDA',1313,395),(8,'SENSE_P',1313,507),(9,'SENSE_N',1313,619),(10,'GATE',1313,731),(11,'FAULT_N',1313,843),(12,'EN',1313,955),
        (13,'TRIP_SET',395,1313),(14,'SCLK',507,1313),(15,'SDI',619,1313),(16,'SDO',731,1313),(17,'TEMP_OUT',843,1313),(18,'VREF',955,1313),
        (19,'G_SHARED',101,395),(20,'D_STD',101,507),(21,'D_ELT',101,619),(22,'HBT_E',101,731),(23,'HBT_B',101,843),(24,'HBT_C',101,955)]
padnet = {}
for n, nm, x, y in pads:
    net = probe('TM2', x, y)
    padnet[n] = net
# group pads by net
groups = collections.defaultdict(list)
for n, nm, x, y in pads:
    k = key(padnet[n]) if padnet[n] else None
    groups[str(k)].append((n, nm))
res['pad_groups'] = dict(groups)
res['n_distinct_pad_nets'] = len(groups)
# expected: VDD{1}, VSS{2,5}, IOVDD{3}, IOVSS{4,6}, 18 singles
exp = {frozenset([1]), frozenset([2,5]), frozenset([3]), frozenset([4,6])} | {frozenset([i]) for i in range(7,25)}
got = {frozenset(n for n, _ in v) for v in groups.values()}
res['pad_grouping_as_expected'] = (got == exp)
# top-cell labels on text layers -> nets
TXT = {8:'M1',10:'M2',30:'M3',50:'M4',67:'M5',126:'TM1',134:'TM2'}
labnet = collections.defaultdict(set); unplaced = []
for l, mn in TXT.items():
    for dt in (25, 0, 2):
        li = ly.find_layer(l, dt)
        if li is None: continue
        for s in top.shapes(li).each(pya.Shapes.STexts):
            t = s.text; net = probe(mn, t.x * dbu, t.y * dbu)
            if net is None: unplaced.append((f'{l}/{dt}', t.string, t.x * dbu, t.y * dbu))
            else: labnet[str(key(net))].add(t.string)
res['labels_not_on_metal'] = unplaced
res['nets_with_multiple_label_names'] = {k: sorted(v) for k, v in labnet.items() if len(v) > 1}
res['pad_net_labels'] = {str(n): sorted(labnet.get(str(key(padnet[n])), [])) if padnet[n] else None for n, *_ in pads}
# extent of each pad net (recursive shapes): does it reach the core (> 330 um from every die edge)?
reach = {}
for n, nm, x, y in pads:
    net = padnet[n]
    if net is None: reach[n] = None; continue
    bb = pya.Box()
    for ln in ('M1','M2','M3','M4','M5','TM1','TM2'):
        r = l2n.shapes_of_net(net, R[ln], True)
        bb += r.bbox()
    b = pya.DBox(bb.left*dbu, bb.bottom*dbu, bb.right*dbu, bb.top*dbu)
    inner = pya.DBox(330, 330, 1084, 1084)
    reach[n] = dict(net=nm, bbox=[round(b.left,1), round(b.bottom,1), round(b.right,1), round(b.top,1)], reaches_core=b.overlaps(inner))
res['pad_net_extent'] = reach
# supply-domain distinctness at metal level
sup = {nm: str(key(padnet[n])) for n, nm, *_ in pads if nm in ('VDD','VSS','IOVDD','IOVSS','VDDA')}
res['supply_nets'] = sup
res['supply_nets_distinct'] = len(set(sup.values())) == 5
# macro power pins
mc = ly.cell('__rz_port_text_000_retained_g1_digital')
mp = []
for inst in top.each_inst():
    if inst.cell_index == mc.cell_index():
        for l, mn in [(126,'TM1'),(67,'M5'),(50,'M4')]:
            for dt in (25, 2, 0):
                li = ly.find_layer(l, dt)
                if li is None: continue
                for s in mc.shapes(li).each(pya.Shapes.STexts):
                    if s.text.string.upper() in ('VPWR','VGND','VDD','VSS','VCC','GND'):
                        p = inst.trans * s.text.trans.disp
                        net = probe(mn, p.x * dbu, p.y * dbu)
                        mp.append((f'{l}/{dt}', s.text.string, round(p.x*dbu,2), round(p.y*dbu,2), str(key(net)) if net else None))
res['macro_power_labels'] = mp[:40]; res['macro_power_label_nets'] = sorted(set((a[1], a[4]) for a in mp))
json.dump(res, open(OUT + '/conn.json', 'w'), indent=1, default=str)
print(json.dumps({k: res[k] for k in ('n_distinct_pad_nets','pad_grouping_as_expected','supply_nets','supply_nets_distinct','nets_with_multiple_label_names','macro_power_label_nets')}, indent=1, default=str))

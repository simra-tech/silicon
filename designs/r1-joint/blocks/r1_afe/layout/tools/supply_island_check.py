"""Metal-only connectivity of the channel supply ports (layout E3). KLayout batch script:
  klayout -b -r tools/supply_island_check.py -rd gds=<r1_afe.gds> -rd ports=<r1_afe_ports.json> [-rd nets=vdd,vss]
For each net, a flood fill from the top-cell pins of r1_afe over Metal1..Metal5 (drawing and pin) and Via1..Via4 of
the flattened layout (no Cont, Activ, well or substrate). The device supply ports of the sin channel (instance xsin,
translation from r1_afe_ports.json) and of the top cell that the flood does not reach have no metal path to the pin.
LVS can still match through a non-metal connection (layout-e3-dev10: OTA1 output-stage PMOS sources).
Prints JSON; 'unreached' must be empty."""
import json
import pya
ly = pya.Layout(); ly.read(gds)
top = ly.cell('r1_afe'); dbu = ly.dbu
def reg(l, dts=(0, 2)):
    r = pya.Region()
    for d in dts:
        li = ly.find_layer(l, d)
        if li is not None:
            r += pya.Region(top.begin_shapes_rec(li))
    return r.merged()
M = [reg(l) for l in (8, 10, 30, 50, 67)]          # drawing + pin (the LVS conductor)
V = [reg(l, (0,)) for l in (19, 29, 49, 66)]
PJ = json.load(open(ports))
ox, oy = PJ['inst_origin']['xsin']
def shape(p, dx=0.0, dy=0.0):
    if p['box']:
        b = p['box']
        return pya.Region(pya.DBox(b[0] + dx, b[1] + dy, b[2] + dx, b[3] + dy).to_itype(dbu))
    x, y = p['pt'][0] + dx, p['pt'][1] + dy
    return pya.Region(pya.DBox(x - 0.01, y - 0.01, x + 0.01, y + 0.01).to_itype(dbu))
out = {}
for net in globals().get('nets', 'vdd,vss').split(','):
    cl = [pya.Region() for _ in M]
    for p in PJ['r1_afe']:
        if p['net'] == net and p['dev'] == '@pin':
            cl[p['layer'] - 1] += M[p['layer'] - 1].interacting(shape(p))
    for _ in range(5000):
        n0 = sum(c.count() for c in cl)
        for i in range(4):
            v = V[i].interacting(cl[i]) + V[i].interacting(cl[i + 1])
            cl[i + 1] = (cl[i + 1] + M[i + 1].interacting(v)).merged()
            cl[i] = (cl[i] + M[i].interacting(v)).merged()
        if sum(c.count() for c in cl) == n0:
            break
    bad, n = [], 0
    for scope, plist, dx, dy in (('xsin', PJ['r1_afe_ch'], ox, oy), ('top', PJ['r1_afe'], 0.0, 0.0)):
        for p in plist:
            if p['net'] != net or p['dev'].startswith('@'):
                continue
            n += 1
            if cl[p['layer'] - 1].interacting(shape(p, dx, dy)).is_empty():
                bad.append(dict(scope=scope, dev=p['dev'], term=p['term'], layer=p['layer']))
    out[net] = dict(ports=n, unreached=bad)
print(json.dumps(out, indent=1))

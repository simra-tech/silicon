#!/usr/bin/env python3
"""Physical metal/via probes of repeated IOVDD labels; labels never merge nets."""
import argparse
import hashlib
import json
from pathlib import Path
import pya
from sense_route_manifest import load_candidate_resistances

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--manifest', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
assert not a.output.exists()
manifest, _ = load_candidate_resistances(a.manifest)
ly = pya.Layout(); ly.read(str(a.manifest.parent / 'g1_chip_top.gds'))
top = ly.cell('g1_chip_top'); pad = ly.cell('sg13g2_IOPadAnalog')
metals = [8, 10, 30, 50, 67, 126, 134]
points = []
for layer in metals:
    it = pad.begin_shapes_rec(ly.layer(layer, 25))
    while not it.at_end():
        shape = it.shape()
        if shape.is_text() and shape.text.string.lower() == 'iovdd':
            point = it.trans() * shape.text.trans.disp
            record = (layer, point.x, point.y)
            if record not in points:
                points.append(record)
        it.next()
assert len(points) >= 2, points

def network(cell):
    netlist = pya.LayoutToNetlist(pya.RecursiveShapeIterator(ly, cell, []))
    layers = {}
    for layer in metals:
        layers[layer] = netlist.make_layer(ly.layer(layer, 0), 'M' + str(layer))
        netlist.connect(layers[layer])
    for cut, lower, upper in zip([19, 29, 49, 66, 125, 133], metals, metals[1:]):
        via = netlist.make_layer(ly.layer(cut, 0), 'V' + str(cut))
        netlist.connect(via); netlist.connect(via, layers[lower]); netlist.connect(via, layers[upper])
    netlist.extract_netlist()
    return netlist, layers

def probe(netlist, layers, layer, point):
    net = netlist.probe_net(layers[layer], point)
    return None if net is None else {'circuit': net.circuit().name, 'cluster_id': net.cluster_id}

standalone, sl = network(pad)
local = [{'layer': layer, 'point_um': [x*ly.dbu, y*ly.dbu],
          'physical_net': probe(standalone, sl, layer, pya.Point(x, y))} for layer, x, y in points]
assembled, al = network(top)
rows = []
for inst in top.each_inst():
    if inst.cell.name != pad.name:
        continue
    probes = []
    for layer, x, y in points:
        point = inst.cplx_trans * pya.Point(x, y)
        probes.append({'layer': layer, 'local_point_um': [x*ly.dbu, y*ly.dbu],
                       'top_point_um': [point.x*ly.dbu, point.y*ly.dbu],
                       'physical_net': probe(assembled, al, layer, point)})
    nets = {tuple(sorted(item['physical_net'].items())) for item in probes if item['physical_net']}
    rows.append({'instance_transform': str(inst.cplx_trans), 'probes': probes,
                 'all_probes_present': all(item['physical_net'] for item in probes),
                 'one_connected_cluster': len(nets) == 1 and all(item['physical_net'] for item in probes)})
assert len(rows) == 11, len(rows)
result = {'scope': 'Candidate standalone AnalogIO and its11placedinstances. Probe coordinates selected from existing IOVDD text, but connectivity uses only physical metals/vias with no labels, wells, substrate or virtual joining. Not full device connectivity/LVS.',
          'candidate_sha256': manifest['candidate_sha256'], 'klayout_version': pya.__version__,
          'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          'standalone_probes': local, 'assembled_instances': rows,
          'assembled_all_iovdd_probe_groups_connected': all(row['one_connected_cluster'] for row in rows)}
a.output.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))

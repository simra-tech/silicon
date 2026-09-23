#!/usr/bin/env python3
"""Bind the approved moved-pad map to actual saved extracted conductors."""
import argparse
import csv
import json
from pathlib import Path
import re
import pya
from prepare_full_marker import sha, region, PARENT


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ('candidate', 'database', 'bondmap', 'source', 'output'):
        ap.add_argument('--' + name, type=Path, required=True)
    ap.add_argument('--database-sha256', required=True)
    a = ap.parse_args()
    assert not a.output.exists() and pya.__version__ == '0.30.9'
    meta = json.loads((a.candidate / 'analysis.json').read_text())
    gds = a.candidate / 'io_marker_native.gds'
    assert meta['status'].startswith('passed') and meta['parent_GDS_sha256'] == PARENT
    assert sha(gds) == meta['GDS_sha256'] == 'ae62bf68aa001144c08a37c58ac3553c6e5f2013a6824b340218e84962066aca'
    assert sha(a.database) == a.database_sha256
    assert sha(a.source) == 'f4ce6848bd7dd179d2ef4cbd8a4ea6bf9788bcfa1ff4b93fabae8bf18b6378f9'
    top_name = 'placed_core_NOT_CONNECTED_FULLCHIP'
    source_pins, = re.findall(r'^\.SUBCKT ' + top_name + r' ([^\n]+)$', a.source.read_text(), re.M)
    source_pins = source_pins.split(); assert len(set(source_pins)) == 22
    pads = list(csv.DictReader(a.bondmap.open()))
    assert len(pads) == 24 and {p['logical_pin'] for p in pads} == set(source_pins)
    assert all(p['candidate_gds_sha256'] == PARENT for p in pads)
    inputs = {str(p): sha(p) for p in (gds, a.database, a.bondmap, a.source, a.candidate / 'analysis.json')}
    ly = pya.Layout(); ly.read(str(gds)); top = ly.cell(top_name)
    raw = ((region(ly, top, pya.LayerInfo(134, 0)) + region(ly, top, pya.LayerInfo(134, 22)))
           - region(ly, top, pya.LayerInfo(134, 24))).merged()
    opening = region(ly, top, pya.LayerInfo(9, 0))
    db = pya.LayoutVsSchematic(); db.read(str(a.database))
    circuit = db.netlist().circuit_by_name(top_name); assert circuit
    pins = [(p.id(), p.name(), circuit.net_for_pin(p.id()).cluster_id) for p in circuit.each_pin()]
    matches = []
    for index in db.layer_indexes():
        value = db.layer_by_index(index)
        if isinstance(value, pya.Region) and value.bbox() == raw.bbox() and (value ^ raw).is_empty():
            matches.append(index)
    assert len(matches) == 1, 'Exact native TM2 layer not uniquely resolved'
    layer = db.layer_by_index(matches[0]); rows = []; identities = {}
    for p in pads:
        x, y, w, h = [round(float(p[k]) * 1000) for k in
                      ('opening_center_x_um', 'opening_center_y_um', 'opening_width_um', 'opening_height_um')]
        assert w == h == 65800
        box = pya.Box(x - w // 2, y - h // 2, x + w // 2, y + h // 2)
        assert (pya.Region(box) - opening).is_empty() and (pya.Region(box) - raw).is_empty()
        points = [(x, y), (box.left + 1, box.bottom + 1), (box.right - 1, box.top - 1)]
        probes = []
        for xy in points:
            net = db.probe_net(layer, pya.Point(*xy)); assert net is not None
            probes.append(dict(layer=matches[0], xy=list(xy), net=dict(
                circuit=net.circuit().name, cluster_id=net.cluster_id, name=net.name)))
        actual = {(q['net']['circuit'], q['net']['cluster_id']) for q in probes}
        assert len(actual) == 1
        identity, = actual; assert identity[0] == top_name
        identities.setdefault(p['logical_pin'], set()).add(identity)
        rows.append(dict(pin=p['logical_pin'], pad_number=int(p['pad_number']),
                         rectangle=[box.left, box.bottom, box.right, box.top], probes=probes))
    assert len(identities) == 22 and all(len(v) == 1 for v in identities.values())
    assert len({next(iter(v)) for v in identities.values()}) == 22
    assert pins == [(p.id(), p.name(), circuit.net_for_pin(p.id()).cluster_id) for p in circuit.each_pin()]
    assert all(sha(Path(p)) == h for p, h in inputs.items())
    result = dict(status='passed read-only 24 physical ports / 22 distinct saved-net bindings; adapter not run',
                  inputs=inputs, script_sha256=sha(Path(__file__)), exact_TM2_layers=matches,
                  original_pins=pins, ports=rows, logical_bindings={k: list(next(iter(v))) for k, v in identities.items()},
                  unchanged_geometry_source_and_netlist='passed', physical_interface_adapter='not run', strict_LVS='not run')
    a.output.mkdir(parents=True)
    (a.output / 'source.py').write_bytes(Path(__file__).read_bytes())
    (a.output / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
    print(result['status'])


if __name__ == '__main__':
    main()


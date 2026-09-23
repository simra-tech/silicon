#!/usr/bin/env python3
"""Read-only physical external-port to saved extracted-net binding; no adapter."""
import argparse
import hashlib
import json
from pathlib import Path
import pya


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--bulk', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    a = ap.parse_args()
    assert not a.output.exists() and pya.__version__ == '0.30.9'
    inputs = {
        'database': (a.bulk/'fullchip-native-strict-lvs-20260923-r2/reports/sealed_native.lvsdb', '1c8f3f91b8be00e0fbbdf4c2a40734fb5f8fe8b0388b1780768699e1a2afcbcf'),
        'GDS': (a.bulk/'final-native-sealring-20260923-r1/sealed_native.gds', '3a24f4d76b3d91141d09515e498383ec36bec4f5bbcffbb7a53456f82259c0e9'),
        'annotations': (a.bulk/'final-top-annotation-audit-20260923-r1/analysis.json', '86e2fbbd98106027a2f8ecdd2c5bfede114445b96e0be831e55a7bc5114051f5'),
        'ports': (a.bulk/'final-native-terminals-20260923-r1/external_bterms.json', 'b8f47a27ccd01741d721016db594d8bd39e246fdec57380e5806d42edc0f63b0'),
    }
    assert all(sha(p) == h for p, h in inputs.values())
    a.output.mkdir(parents=True)
    (a.output/'worker_snapshot.py').write_bytes(Path(__file__).read_bytes())
    annotations = json.loads(inputs['annotations'][0].read_text())
    ports = json.loads(inputs['ports'][0].read_text())
    assert annotations['status'].startswith('passed') and not annotations['missing_expected_port_labels']
    assert ports['physical_ports'] == 24 and ports['logical_BTerms'] == 22 and not ports['errors']
    db = pya.LayoutVsSchematic()
    db.read(str(inputs['database'][0]))
    circuit = db.netlist().circuit_by_name('placed_core_NOT_CONNECTED_FULLCHIP')
    pins_before = [(p.id(), p.name(), circuit.net_for_pin(p.id()).cluster_id) for p in circuit.each_pin()]
    assert len(pins_before) == 71
    ly = pya.Layout()
    ly.read(str(inputs['GDS'][0]))
    top = ly.cell(circuit.name)
    def region(layer, datatype):
        return pya.Region(top.begin_shapes_rec(ly.layer(layer, datatype)))
    # Exact pinned layer formula; classify extraction-layer identity by full
    # geometry equality, never guess an unnamed computed layer's purpose.
    raw = (region(134, 0) + region(134, 22)) - region(134, 24)
    raw.merge()
    layer_rows, matches = [], []
    for index in db.layer_indexes():
        value = db.layer_by_index(index)
        row = dict(index=index, name=db.layer_name(index), info=str(db.layer_info(index)), type=type(value).__name__)
        if isinstance(value, pya.Region):
            row['bbox'] = str(value.bbox())
            if value.bbox() == raw.bbox():
                xor = (value ^ raw)
                row['native_TM2_XOR_area_dbu2'] = xor.area()
                if xor.is_empty():
                    matches.append(index)
        layer_rows.append(row)
    result = dict(status='running read-only probes', input_sha256={k:h for k,(_,h) in inputs.items()},
                  script_sha256=sha(Path(__file__)), exact_TM2_layers=matches, layers=layer_rows,
                  original_pins=pins_before, physical_interface_adapter='not run', native_LVS='not run')
    def save():
        (a.output/'summary.json').write_text(json.dumps(result, indent=2)+'\n')
    save()
    assert matches, 'No saved extraction layer has exact native TopMetal2 geometry'
    rows = []
    for port in ports['ports']:
        assert port['status'] == 'passed' and port['layer'] == 134
        x1,y1,x2,y2 = port['bbox_dbu']
        points = [((x1+x2)//2,(y1+y2)//2)]
        label, = [r for r in annotations['proposed_annotations'] if r['pin'] == port['pin']]
        texts = [r for r in label['present_texts'] if r['text'] == port['pin']]
        # The annotation report binds at least one physical rectangle for
        # duplicated logical supplies; every other rectangle still probes.
        points += [tuple(r['xy']) for r in texts if x1 <= r['xy'][0] <= x2 and y1 <= r['xy'][1] <= y2]
        probes = []
        for index in matches:
            for xy in sorted(set(points)):
                net = db.probe_net(db.layer_by_index(index), pya.Point(*xy))
                probes.append(dict(layer=index, xy=list(xy), net=None if net is None else
                                   dict(circuit=net.circuit().name, cluster_id=net.cluster_id, name=net.name)))
        rows.append(dict(pin=port['pin'], rectangle=port['bbox_dbu'], native_component=port['actual_components'], probes=probes))
    result['ports'] = rows
    identities = {}
    for row in rows:
        ids = {(p['net']['circuit'], p['net']['cluster_id']) for p in row['probes'] if p['net'] is not None}
        assert len(ids) == 1 and all(p['net'] is not None for p in row['probes']), row
        identity, = ids
        assert identity[0] == circuit.name, row
        identities.setdefault(row['pin'], set()).add(identity)
    assert len(identities) == 22 and all(len(v) == 1 for v in identities.values())
    assert len({next(iter(v)) for v in identities.values()}) == 22, 'Distinct logical source ports share extracted net'
    result['logical_bindings'] = {k:list(next(iter(v))) for k,v in identities.items()}
    assert pins_before == [(p.id(), p.name(), circuit.net_for_pin(p.id()).cluster_id) for p in circuit.each_pin()]
    assert all(sha(p) == h for p,h in inputs.values())
    result['status'] = 'passed read-only 24 physical ports / 22 distinct saved-net bindings; adapter not run'
    result['all_71_original_pins_unchanged'] = True
    save()
    print(result['status'])


if __name__ == '__main__':
    main()

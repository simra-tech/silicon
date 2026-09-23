#!/usr/bin/env python3
"""Read saved strict LVS topology and native IO geometry without new extraction."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
import os
from pathlib import Path
import pya
from inspect_stock_result_r3 import analyze, device, label, value


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def netrow(n):
    if n is None:
        return None
    return dict(name=n.name, expanded_name=n.expanded_name(), qname=n.qname(),
                cluster_id=n.cluster_id, pins=[value(p, 'pin_id') for p in n.each_pin()])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--run', type=Path, required=True)
    ap.add_argument('--gds', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    a = ap.parse_args()
    assert not a.output.exists() and len(os.sched_getaffinity(0)) == 1
    assert pya.__version__ == '0.30.9'
    a.output.mkdir(parents=True)
    (a.output / 'worker_snapshot.py').write_bytes(Path(__file__).read_bytes())
    top = 'placed_core_NOT_CONNECTED_FULLCHIP'
    pins = json.loads((a.run / 'expected_source_pins.json').read_text())
    parsed = analyze(a.run / 'reports', 0, top, True, pins)
    (a.output / 'strict_analysis_r3.json').write_text(json.dumps(parsed, indent=2) + '\n')
    assert parsed['checks']['native_extraction_strict_unrelaxed_switches']
    assert parsed['checks']['reference_source_top_pin_set_exact']
    assert parsed['explicit_engine_mismatch'] and parsed['status'].startswith('failed')
    db = pya.LayoutVsSchematic()
    path = a.run / 'reports/sealed_native.lvsdb'
    db.read(str(path))
    result = dict(status='running saved IO topology audit', saved_database_sha256=sha(path),
                  strict_LVS='failed', seed='not applicable', new_stock_run='not run', cells=[])
    names = [r['layout'] for r in parsed['database']['circuits'] if r['status'] == 'NoMatch']
    layout = pya.Layout()
    layout.read(str(a.gds))
    assert sha(a.gds) == '3a24f4d76b3d91141d09515e498383ec36bec4f5bbcffbb7a53456f82259c0e9'
    stockpath = Path('/foss/pdks/ihp-sg13g2/libs.ref/sg13g2_io/gds/sg13g2_io.gds')
    stock = pya.Layout()
    stock.read(str(stockpath))
    assert sha(stockpath) == '4281a855377b6a1ca46356e9391258dc14e8efc3b8051a65befc0fe9db3c7825'
    for name in names:
        row = dict(name=name, sides={})
        for side, nl in [('layout', db.netlist()), ('reference', db.reference)]:
            circuit = nl.circuit_by_name(name if side == 'layout' else name.upper())
            assert circuit is not None
            nets = list(circuit.each_net())
            duplicates = {n: count for n, count in Counter(n.name for n in nets).items() if n and count > 1}
            cr = dict(devices=[device(d) for d in circuit.each_device()],
                      nets=[netrow(n) for n in nets], duplicate_named_nets=duplicates,
                      pins=[dict(id=p.id(), name=p.name(), net=netrow(circuit.net_for_pin(p.id()))) for p in circuit.each_pin()],
                      parent_instances=[])
            for parent in nl.each_circuit():
                for inst in parent.each_subcircuit():
                    if inst.circuit_ref() != circuit:
                        continue
                    mapping = [dict(child_pin_id=p.id(), child_name=p.name(),
                                    child_net=netrow(circuit.net_for_pin(p.id())),
                                    parent_net=netrow(inst.net_for_pin(p.id()))) for p in circuit.each_pin()]
                    groups = defaultdict(list)
                    for m in mapping:
                        if m['child_net'] is not None and m['child_net']['name'] in duplicates:
                            groups[m['child_net']['name']].append(m['parent_net'])
                    cr['parent_instances'].append(dict(parent=parent.name, instance=inst.expanded_name(),
                                                      pin_mapping=mapping,
                                                      duplicate_name_parent_cluster_counts={key: len({(n['qname'], n['cluster_id']) if n else None for n in vals}) for key, vals in groups.items()}))
            row['sides'][side] = cr
        ca, cb = layout.cell(name), stock.cell(name)
        assert ca is not None and cb is not None
        changes = []
        for li in sorted({(x.layer, x.datatype) for ly in (layout, stock) for x in ly.layer_infos()}):
            ra = pya.Region(ca.begin_shapes_rec(layout.layer(*li))).merged()
            rb = pya.Region(cb.begin_shapes_rec(stock.layer(*li))).merged()
            xor = ra ^ rb
            if not xor.is_empty():
                changes.append(dict(layer=list(li), xor_area_dbu2=xor.area()))
        row['native_stock_polygon_XOR'] = changes
        row['native_stock_polygon_parity'] = not changes
        if name == 'sg13g2_SecondaryProtection':
            marker = pya.Region(ca.begin_shapes_rec(layout.layer(128, 0)))
            row['native_PolyRes128_0_polygon_count'] = marker.count()
        result['cells'].append(row)
        (a.output / 'topology.json').write_text(json.dumps(result, indent=2) + '\n')
    result.update(status='passed saved evidence collection; strict LVS remains failed',
                  all14_native_stock_polygon_parity=all(r['native_stock_polygon_parity'] for r in result['cells']),
                  GDS_sha256=sha(a.gds), stock_GDS_sha256=sha(stockpath),
                  script_sha256=sha(Path(__file__)), parser_sha256=sha(Path(__file__).with_name('inspect_stock_result_r3.py')),
                  make_top_level_pins_documentation=pya.Netlist.make_top_level_pins.__doc__)
    (a.output / 'topology.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'cells'}, indent=2))


if __name__ == '__main__':
    main()

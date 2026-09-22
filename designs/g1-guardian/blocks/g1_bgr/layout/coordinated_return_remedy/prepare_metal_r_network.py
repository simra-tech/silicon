#!/usr/bin/env python3
"""Source-bound actual metallization preparation, excluding internal devices."""
import argparse
import collections
import datetime
import json
import os
from pathlib import Path
import re
import sys
import time
import pya

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
sys.path.insert(0, str(HERE.parent / 'coordinated_full_closure'))
from build_assembly import PAIRS, METALS, CUTS, SOURCE
from export_cc_api import sha, dump, plain


def main():
    ap = argparse.ArgumentParser()
    for name in ('gds', 'currents', 'output', 'resource-gate'):
        ap.add_argument('--' + name, type=Path, required=True)
    args = ap.parse_args()
    gate = json.loads(args.resource_gate.read_text())
    age = (datetime.datetime.now(datetime.timezone.utc) - datetime.datetime.fromisoformat(gate['utc'])).total_seconds()
    assert gate['status'] == 'passed' and 0 <= age < 1800
    assert len(os.sched_getaffinity(0)) == 1 and next(iter(os.sched_getaffinity(0))) in range(4)
    assert pya.__version__ == '0.30.9'
    assert sha(args.gds) == '71892e4308000401f857c88eda21c8590dc03c1d7534fecc4851104baec17383'
    assert sha(SOURCE) == '586ffb58b6af31c77a2e7cbcb83b173ffa4713ec62401da30901c5a7e606283b'
    assert sha(args.currents) == '2fee5fa86dd88c4d0c7b89a8a994ce406b7e0508f5853da7400d7d952eb32827'
    args.output.mkdir(exist_ok=False)
    (args.output / 'worker_snapshot.py').write_bytes(Path(__file__).read_bytes())
    start = time.monotonic()
    receipt = dict(status='running', domain='conditional native-M1-to-macro-port metallization',
                   physical_IR_qualification='not run', source_insertion='not run', seed='not applicable')
    dump(args.output / 'summary.json', receipt)
    try:
        bulk = Path(os.environ['G1_RESULTS_ROOT'])
        routing = bulk / 'bgr-assembly-20260922-r5/routing.json'
        probes = json.loads(routing.read_text())['source_probes']
        ledger = json.loads(args.currents.read_text())
        devices = {r['source_id']: r for r in ledger['devices']}
        assert len(devices) == 1036
        original = pya.Layout()
        original.read(str(args.gds))
        source_top = original.top_cell()
        ly = pya.Layout()
        ly.dbu = .001
        top = ly.create_cell('metallization')
        indices, regions = {}, {}
        for name, pair in PAIRS.items():
            r = plain(pya.Region(source_top.begin_shapes_rec(original.layer(*pair))))
            indices[name] = ly.layer(*pair)
            regions[name] = r
            for polygon in r.each():
                top.shapes(indices[name]).insert(polygon)
        ltn = pya.LayoutToNetlist(pya.RecursiveShapeIterator(ly, top, []))
        layers = {name: ltn.make_layer(indices[name], name) for name in PAIRS}
        for name in PAIRS:
            ltn.connect(layers[name])
        for cut, ends in CUTS.items():
            for end in ends:
                ltn.connect(layers[cut], layers[end])
        ltn.extract_netlist()
        points, ownership, source_terms = {}, collections.defaultdict(set), []
        represented = set()
        for probe in probes:
            name = probe['instance']
            if name not in devices and name != 'full_port':
                continue
            terminal = probe['terminal']
            layer = probe['layer']
            xy = tuple(probe['point'])
            if name in devices:
                device = devices[name]
                if name.startswith('XR'):
                    terminal = str(int(terminal) + 1)
                elif name.startswith('XQ'):
                    terminal = 'BN' if terminal == 'S' else terminal
                    if terminal == 'E':
                        layer = 'M1'
                assert layer == 'M1'
                assert device['source_terminal_nodes'][terminal] == probe['net']
                injection = device['inferred_injection_into_wire_A'][terminal]
                represented.add(name)
                source_terms.append((name, terminal))
            else:
                injection = 0.
            node = ltn.probe_net(layers[layer], pya.Point(*xy))
            assert node is not None, (name, terminal, layer, xy)
            component = node.cluster_id
            ownership[component].add(probe['net'])
            key = (layer,) + xy
            record = points.setdefault(key, dict(layer=layer, point_dbu=list(xy), source_net=probe['net'],
                component=component, injection_A=0., sources=[], reference_ports=[]))
            assert record['source_net'] == probe['net'] and record['component'] == component
            if name == 'full_port':
                record['reference_ports'].append(terminal)
            else:
                record['injection_A'] += injection
                record['sources'].append(dict(source_id=name, terminal=terminal, injection_A=injection))
        assert represented == set(devices) and len(source_terms) == len(set(source_terms)) == 3346
        assert len(ownership) == 55 and all(len(nets) == 1 for nets in ownership.values())
        assert len({next(iter(nets)) for nets in ownership.values()}) == 55
        circuit = ltn.netlist().circuit_by_name('metallization')
        assert len(list(circuit.each_net())) == 55
        rows = sorted(points.values(), key=lambda r: (r['layer'], r['point_dbu']))
        for index, row in enumerate(rows):
            row['id'] = index
        references = {port: r['id'] for r in rows for port in r['reference_ports']}
        assert set(references) == {'vdd', 'vss', 'r4', 'vref', 'iptat', 'pbias', 'pcasc', 'vbe', 'dvbe'}
        omitted = [dict(source_id=name, terminal='BN', current_A=d['inferred_injection_into_wire_A']['BN'])
                   for name, d in devices.items() if name.startswith('XR')]
        assert len(omitted) == 399 and all(r['current_A'] == 0 for r in omitted)
        ly.write(str(args.output / 'metallization.gds'))
        saved = pya.Layout()
        saved.read(str(args.output / 'metallization.gds'))
        assert all((r ^ plain(pya.Region(saved.top_cell().begin_shapes_rec(saved.layer(*PAIRS[name]))))).is_empty()
                   for name, r in regions.items())
        lef = Path('/foss/pdks/ihp-sg13g2/libs.ref/sg13g2_stdcell/lef/sg13g2_tech.lef')
        tech = Path('/usr/local/lib/python3.12/dist-packages/klayout_pex_protobuf/ihp-sg13g2_tech.pb.json')
        assert sha(lef) == '054f5b7b24d72365b4b1088be1331e04c1c2e3805de9f99c37e71938ed231efc'
        assert sha(tech) == '6ece2ac73930696f77b257d14fcf9d29d9e02451e7df99c72239746c18369a92'
        lv = {}
        for name, body in re.findall(r'^LAYER (\S+)\s*\n(.*?)^END \1\s*$', lef.read_text(), re.M | re.S):
            if name in ['Metal' + str(i) for i in range(1, 6)] + list(CUTS):
                values = re.findall(r'^\s*RESISTANCE\s+(?:RPERSQ\s+)?([0-9.]+)\s*;', body, re.M)
                assert len(values) == 1
                lv[name] = float(values[0])
        resistance = json.loads(tech.read_text())['process_parasitics']['resistance']
        kv = {r['layer_name']: r['resistance'] / 1000 for r in resistance['layers']}
        kv.update({r['via_name']: r['resistance'] / 1000 for r in resistance['vias']})
        scenarios = {}
        for name, values in [('LEF', lv), ('KPEX', kv)]:
            scenarios[name] = dict(sheet_ohm={metal: values['Metal' + metal[1:]] for metal in METALS},
                                   cut_ohm={cut: values[cut] for cut in CUTS})
        for cut in CUTS:
            assert all(p.area() == 190 * 190 for p in regions[cut].each()), cut
        dump(args.output / 'points.json', rows)
        dump(args.output / 'scenarios.json', scenarios)
        dump(args.output / 'omitted_resistor_substrates.json', omitted)
        net_I = {net: sum(r['injection_A'] for r in rows if r['source_net'] == net)
                 for net in sorted({r['source_net'] for r in rows})}
        receipt.update(status='passed conditional metallization preparation', source_devices=1036,
            represented_terminal_incidences=3346, distinct_injection_points=len(rows), source_net_count=55,
            references=references, omitted_R_substrate_count=399, nominal_only_zero_R_substrate=True,
            source_net_injection_A=net_I, all_nine_layer_union_XOR_zero=True,
            geometry_counts={name: dict(polygons=r.count(), area_um2=r.area() * 1e-6) for name, r in regions.items()},
            inputs={str(p): sha(p) for p in (args.gds, args.currents, routing, SOURCE, lef, tech,
                                            HERE / 'METALLIZATION_R_CONTRACT_20260922.md', Path(__file__))},
            outputs={n: sha(args.output / n) for n in ('metallization.gds', 'points.json', 'scenarios.json', 'omitted_resistor_substrates.json')},
            boundaries='point injection at native M1 access; MOS/HBT body currents at native M1 guard access, not a substrate model',
            unresolved='internal/electrode contact reference plane, compact rc/re ownership, native spreading, wells/substrate, PVT, nonlinear redistribution')
    except Exception as error:
        receipt.update(status='failed conditional metallization preparation', error=repr(error))
        raise
    finally:
        receipt['wall_s'] = time.monotonic() - start
        dump(args.output / 'summary.json', receipt)
        print(json.dumps({k: v for k, v in receipt.items() if k != 'source_net_injection_A'}, indent=2))


if __name__ == '__main__':
    main()

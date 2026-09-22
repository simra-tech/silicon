#!/usr/bin/env python3
"""Native-fixed two-interface Via2 doubling at the existing precision star."""
import argparse
import datetime
import json
import os
from pathlib import Path
import sys
import pya
from build_viaquad import texts

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'coordinated_full_closure'))
from build_assembly import Assembly, PAIRS, region, sha, dump, ROOT, SOURCE


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--resource-gate', type=Path, required=True)
    args = ap.parse_args()
    gate = json.loads(args.resource_gate.read_text())
    age = (datetime.datetime.now(datetime.timezone.utc) - datetime.datetime.fromisoformat(gate['utc'])).total_seconds()
    assert gate['status'] == 'passed' and 0 <= age < 1800
    assert len(os.sched_getaffinity(0)) == 1 and next(iter(os.sched_getaffinity(0))) == 1
    bulk = Path(os.environ['G1_RESULTS_ROOT'])
    base = bulk / 'bgr-assembly-viaquad-20260922-r3'
    original = bulk / 'bgr-assembly-20260922-r5'
    pack_path = ROOT / 'designs/g1-guardian/review/audits/coordinated-bbox-pack-586-20260922-r1.json'
    assert sha(base / 'bank.gds') == '943fa1787490571ebf0120c303b9326ac9290b49c70df9a73b5bea7014093f7a'
    assert sha(SOURCE) == '586ffb58b6af31c77a2e7cbcb83b173ffa4713ec62401da30901c5a7e606283b'
    prep = json.loads((base / 'preparation.json').read_text())
    assert prep['status'] == 'passed preparation'
    args.output.mkdir(exist_ok=False)
    (args.output / 'worker_snapshot.py').write_bytes(Path(__file__).read_bytes())
    receipt = dict(status='running', command=sys.argv, cpu=1, watchdog_s=180, memory_reservation_gib=4,
                   memory_enforced=False, resource_gate_sha256=sha(args.resource_gate))
    dump(args.output / 'run.json', receipt)
    try:
        ly = pya.Layout()
        ly.read(str(base / 'bank.gds'))
        top = ly.top_cell()
        before = {(ly.get_info(i).layer, ly.get_info(i).datatype): region(top, i) for i in ly.layer_indices()}
        text_before = texts(top)
        hierarchy = sorted((c.name, c.child_instances()) for c in ly.each_cell())
        removed, added, m2 = pya.Region(), pya.Region(), pya.Region()
        changes = []
        for y in (15060, 16260):
            old = [[15905, y + d - 95, 16095, y + d + 95] for d in (-210, 210)]
            new = [[16000 + dx - 95, y + dy - 95, 16000 + dx + 95, y + dy + 95]
                   for dx in (-210, 210) for dy in (-210, 210)]
            for b in old:
                removed.insert(pya.Box(*b))
            for b in new:
                added.insert(pya.Box(*b))
            m2.insert(pya.Box(15640, y - 360, 16360, y + 360))
            changes.append(dict(center_dbu=[16000, y], old_union_cuts=old, new_cuts=new))
        m2.insert(pya.Box(15640, 15060, 16360, 16260))
        assert (removed - before[PAIRS['Via2']]).is_empty()
        index = ly.layer(*PAIRS['Via2'])
        targets = {tuple(b) for c in changes for b in c['old_union_cuts']}
        hits = []
        iterator = top.begin_shapes_rec(index)
        while not iterator.at_end():
            shape = iterator.shape()
            if shape.is_box() or shape.is_polygon():
                box = shape.bbox().transformed(iterator.trans())
                key = (box.left, box.bottom, box.right, box.top)
                if key in targets:
                    assert (pya.Region(shape.polygon.transformed(iterator.trans())) ^ pya.Region(box)).is_empty()
                    hits.append((key, shape))
            iterator.next()
        assert {key for key, _ in hits} == targets
        # Coincident R-bank and HBT-bank cuts are one physical unioned cut;
        # remove every coincident representation, not just one instance.
        for _, shape in hits:
            shape.delete()
        for polygon in added.each():
            top.shapes(index).insert(polygon)
        for polygon in m2.merged().each():
            top.shapes(ly.layer(*PAIRS['M2'])).insert(polygon)
        expected = dict(before)
        expected[PAIRS['Via2']] = (before[PAIRS['Via2']] - removed) + added
        expected[PAIRS['M2']] = before[PAIRS['M2']] + m2
        natives = pya.Region()
        pack = json.loads(pack_path.read_text())['BGR_devices']
        assert len(pack) == 1036
        for device in pack:
            natives.insert(pya.DBox(*device['bbox_um']).to_itype(.001))
        assert ((removed + added + m2) & natives).is_empty()
        ly.write(str(args.output / 'bank.gds'))
        (args.output / 'bank.cdl').write_bytes((base / 'bank.cdl').read_bytes())
        saved = pya.Layout()
        saved.read(str(args.output / 'bank.gds'))
        actual = saved.top_cell()
        assert all((r ^ region(actual, saved.layer(*pair))).is_empty() for pair, r in expected.items())
        assert texts(actual) == text_before
        assert sorted((c.name, c.child_instances()) for c in saved.each_cell()) == hierarchy
        for layer in ('M2', 'M3'):
            assert (added.sized(55) - region(actual, saved.layer(*PAIRS[layer]))).is_empty()
        graph = Assembly(args.output)
        graph.probes = json.loads((original / 'routing.json').read_text())['source_probes']
        graph.star = json.loads((base / 'changed_shapes.json').read_text())['star_interfaces']
        full = graph.graph(actual)
        cuts = [graph.graph(actual, (r,)) for r in graph.star]
        cuts += [graph.graph(actual, tuple(graph.star)), graph.graph(actual, precision=True)]
        dump(args.output / 'terminal_graph.json', full)
        dump(args.output / 'star_cuts.json', cuts)
        assert full['status'] == 'passed' and len(cuts) == 7 and all(c['status'] == 'passed' for c in cuts)
        assert (pya.Region(actual.bbox()) - pya.Region(pya.Box(0, 0, 420000, 354000))).is_empty()
        assert all(p.x % 5 == p.y % 5 == 0 for index in saved.layer_indices()
                   for polygon in region(actual, index).each() for p in polygon.each_point_hull())
        paths = [base / n for n in ('bank.gds', 'bank.cdl', 'preparation.json', 'changed_shapes.json')]
        paths += [original / 'routing.json', SOURCE, pack_path, Path(__file__), HERE / 'build_viaquad.py',
                  HERE.parent / 'coordinated_full_closure/build_assembly.py']
        result = dict(status='passed preparation', inputs={str(p): sha(p) for p in paths},
            source_ports=prep['source_ports'], source_nets=prep['source_nets'], source_count=1036,
            changed_interfaces=changes, removed_physical_cuts=4, removed_hierarchical_shapes=len(hits), added_cuts=8,
            M2_stem_width_um=.72, geometry_scope='Via2/M2 only, same two interface centers, all native/source/text/hierarchy unchanged',
            all_layer_exact_delta=True, native_bbox_delta_zero=True, via_enclosures=True, saved_graph_and_seven_cuts=True,
            gds_sha256=sha(args.output / 'bank.gds'), cdl_sha256=sha(args.output / 'bank.cdl'),
            stock_DRC_LVS_PEX_electrical='not run', adoption='not run', seed='not applicable')
        dump(args.output / 'preparation.json', result)
        receipt.update(status='passed', preparation_sha256=sha(args.output / 'preparation.json'))
    except Exception as error:
        receipt.update(status='failed', error=repr(error))
        raise
    finally:
        dump(args.output / 'run.json', receipt)
        print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()

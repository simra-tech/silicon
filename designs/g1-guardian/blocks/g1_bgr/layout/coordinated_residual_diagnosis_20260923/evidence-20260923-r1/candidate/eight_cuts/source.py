#!/usr/bin/env python3
"""Generate only the passed additive DVBE landing/cut candidate."""
import argparse
import json
import os
from pathlib import Path
import sys
import time
import pya

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent/'coordinated_full_closure'))
sys.path.insert(0, str(HERE.parent/'coordinated_return_remedy'))
from build_assembly import Assembly, PAIRS, CUTS, region, sha, dump, SOURCE
from build_viaquad import texts


def local_records(layout, excluded):
    return {c.name: dict(instances=sorted((i.cell.name, str(i.cplx_trans), str(i.a), str(i.b),
                    i.na, i.nb, i.prop_id) for i in c.each_inst()),
                shapes=sorted((str(layout.get_info(li)), str(s)) for li in layout.layer_indices()
                              for s in c.shapes(li).each()))
            for c in layout.each_cell() if c.name != excluded}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--preflight', type=Path, required=True)
    a = ap.parse_args()
    assert not a.output.exists()
    assert set(os.sched_getaffinity(0)) == {48}
    bulk = Path(os.environ['G1_RESULTS_ROOT'])
    base = bulk/'bgr-supply-candidate-20260923-r1'
    assert sha(base/'bank.gds') == 'e3ecfc6208fcae71c6b2f4223b7db3900677acfe30987b50ba6365c720297feb'
    assert sha(SOURCE) == '586ffb58b6af31c77a2e7cbcb83b173ffa4713ec62401da30901c5a7e606283b'
    pre = json.loads(a.preflight.read_text())
    assert pre['status'] == 'passed geometric screen' and all(c['passed'] for c in pre['checks'])
    assert all(sha(Path(p)) == h for p, h in pre['inputs'].items())
    assert {r['net'] for r in pre['ledger']} == {'dvbe'}
    assert {r['layer'] for r in pre['ledger']} == {'M2', 'M3', 'M4', 'M5', 'Via2', 'Via3', 'Via4'}
    route = bulk/'bgr-assembly-20260922-r5/routing.json'
    star = bulk/'bgr-assembly-viaquad-20260922-r3/changed_shapes.json'
    paths = [base/'bank.gds', base/'bank.cdl', base/'preparation.json', a.preflight,
             route, star, SOURCE, Path(__file__).resolve(),
             HERE.parent/'coordinated_full_closure/build_assembly.py',
             HERE.parent/'coordinated_return_remedy/build_viaquad.py']
    inputs = {str(p): sha(p) for p in paths}
    a.output.mkdir(parents=True)
    (a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    start = time.monotonic()
    receipt = dict(status='running', candidate_adoption='not run')
    try:
        ly = pya.Layout()
        ly.read(str(base/'bank.gds'))
        top = ly.top_cell()
        old = {(ly.get_info(i).layer, ly.get_info(i).datatype): region(top, i) for i in ly.layer_indices()}
        old_native = local_records(ly, top.name)
        old_texts = texts(top)
        old_instances = sorted((i.cell.name, str(i.cplx_trans), str(i.a), str(i.b), i.na, i.nb, i.prop_id) for i in top.each_inst())
        overlay = pya.Layout()
        overlay.dbu = ly.dbu
        ot = overlay.create_cell('g1_bgr_dvbe_redundant_cuts_overlay')
        added, ledger, already_present = {}, [], []
        for r in pre['ledger']:
            pair = PAIRS[r['layer']]
            box = pya.Box(*r['bbox_dbu'])
            shape = pya.Region(box)
            if r['layer'] in CUTS and (shape-old.get(pair, pya.Region())).is_empty():
                already_present.append(r)
                continue
            top.shapes(ly.layer(*pair)).insert(box)
            ot.shapes(overlay.layer(*pair)).insert(box)
            added.setdefault(pair, pya.Region()).insert(box)
            ledger.append(r)
        assert len(already_present) == 4 and all(r['role'] == 'lower_six_cut' for r in already_present)
        assert sum(r['layer'] in CUTS for r in ledger) == 32
        ly.write(str(a.output/'bank.gds'))
        overlay.write(str(a.output/'redundant_cuts_overlay.gds'))
        (a.output/'bank.cdl').write_bytes((base/'bank.cdl').read_bytes())
        saved = pya.Layout()
        saved.read(str(a.output/'bank.gds'))
        actual = saved.top_cell()
        assert local_records(saved, actual.name) == old_native and texts(actual) == old_texts
        assert sorted((i.cell.name, str(i.cplx_trans), str(i.a), str(i.b), i.na, i.nb, i.prop_id) for i in actual.each_inst()) == old_instances
        pairs = set(old) | {(saved.get_info(i).layer, saved.get_info(i).datatype) for i in saved.layer_indices()}
        for pair in pairs:
            assert (region(actual, saved.layer(*pair)) ^ (old.get(pair, pya.Region())+added.get(pair, pya.Region()))).is_empty(), pair
        graph = Assembly(a.output)
        graph.probes = json.loads(route.read_text())['source_probes']
        graph.star = json.loads(star.read_text())['star_interfaces']
        full = graph.graph(actual)
        cuts = [graph.graph(actual, (role,)) for role in graph.star]
        cuts += [graph.graph(actual, tuple(graph.star)), graph.graph(actual, precision=True)]
        dump(a.output/'terminal_graph.json', full)
        dump(a.output/'star_cuts.json', cuts)
        assert full['status'] == 'passed' and len(cuts) == 7 and all(c['status'] == 'passed' for c in cuts)
        ltn = pya.LayoutToNetlist(pya.RecursiveShapeIterator(saved, actual, []))
        layers = {k: ltn.make_layer(saved.layer(*p), k) for k, p in PAIRS.items()}
        for k in layers:
            ltn.connect(layers[k])
        for cut, ends in CUTS.items():
            for end in ends:
                ltn.connect(layers[cut], layers[end])
        ltn.extract_netlist()
        nets = {}
        for p in graph.probes:
            n = ltn.probe_net(layers[p['layer']], pya.Point(*p['point']))
            assert n
            if p['net'] in nets:
                assert nets[p['net']].cluster_id == n.cluster_id
            nets[p['net']] = n
        assert len(nets) == 55
        ownership = []
        for r in ledger:
            shape = pya.Region(pya.Box(*r['bbox_dbu']))
            assert (shape-ltn.shapes_of_net(nets['dvbe'], layers[r['layer']], True)).is_empty()
            for end in CUTS.get(r['layer'], ()):
                assert (shape.sized(55)-ltn.shapes_of_net(nets['dvbe'], layers[end], True)).is_empty()
            ownership.append(dict(r, all_area_owned_by_DVBE=True))
        dump(a.output/'added_geometry_ownership.json', ownership)
        assert (pya.Region(actual.bbox())-pya.Region(pya.Box(0, 0, 420000, 354000))).is_empty()
        assert all(sha(Path(p)) == h for p, h in inputs.items())
        result = dict(status='passed preparation', inputs=inputs, source_count=1036,
            source_ports=json.loads((base/'preparation.json').read_text())['source_ports'],
            source_nets=sorted(nets), added_geometry=ledger, retained_existing_cuts=already_present,
            added_cuts=32, all_native_text_instance_parity=True, all_layer_native_plus_overlay_XOR_zero=True,
            all55nets_seven_star_cuts=True, all_added_metal_cut_faces_same_net=True,
            gds_sha256=sha(a.output/'bank.gds'), cdl_sha256=sha(a.output/'bank.cdl'),
            overlay_sha256=sha(a.output/'redundant_cuts_overlay.gds'),
            stock_DRC_LVS_AP='not run', full_parent_context='not run', conditional_OP='not run', adoption='not run')
        dump(a.output/'preparation.json', result)
        receipt['status'] = 'passed'
    except Exception as exc:
        receipt.update(status='failed', exception=repr(exc))
        raise
    finally:
        receipt['wall_s'] = time.monotonic()-start
        dump(a.output/'run.json', receipt)
        print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()

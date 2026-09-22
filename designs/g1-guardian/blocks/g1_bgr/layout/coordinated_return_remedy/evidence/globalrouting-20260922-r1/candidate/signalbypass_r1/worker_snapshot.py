#!/usr/bin/env python3
"""Bounded c2/VBE bypass candidate; original ports/native and TopMetal held."""
import argparse
import datetime
import json
import os
from pathlib import Path
import sys
import time
import pya
from build_viaquad import texts

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'coordinated_full_closure'))
from build_assembly import Assembly, PAIRS, CUTS, region, sha, dump, SOURCE


def main():
    ap = argparse.ArgumentParser()
    for name in ('output', 'resource-gate', 'preflight'):
        ap.add_argument('--' + name, type=Path, required=True)
    args = ap.parse_args()
    gate = json.loads(args.resource_gate.read_text())
    age = (datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(gate['utc'])).total_seconds()
    assert gate['status'] == 'passed' and 0 <= age < 1800
    assert len(os.sched_getaffinity(0)) == 1 and next(iter(os.sched_getaffinity(0))) == 1
    bulk = Path(os.environ['G1_RESULTS_ROOT'])
    base = bulk / 'bgr-assembly-globalrails-20260922-r1'
    assert sha(base / 'bank.gds') == 'e9b6653d74ae841beb831bebdbbc9942cdfba064e13d4d00c49751b83a77111c'
    preflight = json.loads(args.preflight.read_text())
    assert preflight['status'] == 'passed preflight' and all(r['passed'] for r in preflight['checks'])
    assert preflight['mutual_added_net_clearance_findings'] == []
    assert {r['net'] for r in preflight['ledger']} == {'c2','vbe'}
    assert {r['layer'] for r in preflight['ledger']} == {'M4','M5','Via4'}
    assert all(sha(Path(p)) == h for p,h in preflight['inputs'].items())
    assert sha(SOURCE) == '586ffb58b6af31c77a2e7cbcb83b173ffa4713ec62401da30901c5a7e606283b'
    args.output.mkdir(exist_ok=False)
    (args.output/'worker_snapshot.py').write_bytes(Path(__file__).read_bytes())
    start = time.monotonic()
    receipt = dict(status='running', cpu=1, watchdog_s=180, memory_reservation_gib=4, memory_enforced=False)
    dump(args.output/'run.json', receipt)
    try:
        ly = pya.Layout()
        ly.read(str(base/'bank.gds'))
        top = ly.top_cell()
        before = {(ly.get_info(i).layer,ly.get_info(i).datatype):region(top,i) for i in ly.layer_indices()}
        text_before = texts(top)
        hierarchy = sorted((c.name,c.child_instances()) for c in ly.each_cell())
        additions = {}
        ledger = []
        for proposal in preflight['ledger']:
            bbox = list(proposal['bbox_dbu'])
            pair = PAIRS[proposal['layer']]
            shape = pya.Box(*bbox)
            additions.setdefault(pair,pya.Region()).insert(shape)
            top.shapes(ly.layer(*pair)).insert(shape)
            ledger.append(dict(proposal, actual_added_rectangle_dbu=bbox))
        ly.write(str(args.output/'bank.gds'))
        (args.output/'bank.cdl').write_bytes((base/'bank.cdl').read_bytes())
        saved = pya.Layout()
        saved.read(str(args.output/'bank.gds'))
        actual = saved.top_cell()
        assert texts(actual) == text_before
        assert sorted((c.name,c.child_instances()) for c in saved.each_cell()) == hierarchy
        deltas = []
        for pair,old in before.items():
            current = region(actual,saved.layer(*pair))
            expected = old + additions.get(pair,pya.Region())
            assert (current^expected).is_empty(),pair
            assert (old-current).is_empty(),pair
            if pair in additions:
                delta = current-old
                deltas.append(dict(layer=list(pair),added_area_um2=delta.area()*1e-6,removed_area_um2=0))
        for proposal in ledger:
            if proposal['layer'] in CUTS:
                via = pya.Region(pya.Box(*proposal['bbox_dbu']))
                assert all((via.sized(55)-region(actual,saved.layer(*PAIRS[m]))).is_empty() for m in CUTS[proposal['layer']])
        original = bulk/'bgr-assembly-20260922-r5'
        viaquad = bulk/'bgr-assembly-viaquad-20260922-r3'
        graph = Assembly(args.output)
        graph.probes = json.loads((original/'routing.json').read_text())['source_probes']
        graph.star = json.loads((viaquad/'changed_shapes.json').read_text())['star_interfaces']
        full = graph.graph(actual)
        cuts = [graph.graph(actual,(role,)) for role in graph.star]
        cuts += [graph.graph(actual,tuple(graph.star)),graph.graph(actual,precision=True)]
        dump(args.output/'terminal_graph.json',full)
        dump(args.output/'star_cuts.json',cuts)
        assert full['status'] == 'passed' and len(cuts)==7 and all(c['status']=='passed' for c in cuts)
        assert (pya.Region(actual.bbox())-pya.Region(pya.Box(0,0,420000,354000))).is_empty()
        assert all(p.x%5==p.y%5==0 for i in saved.layer_indices() for poly in region(actual,i).each() for p in poly.each_point_hull())
        paths = [base/'bank.gds',base/'bank.cdl',base/'preparation.json',args.preflight,args.resource_gate,
                 SOURCE,Path(__file__),HERE/'build_viaquad.py',HERE.parent/'coordinated_full_closure/build_assembly.py',
                 original/'routing.json',viaquad/'changed_shapes.json']
        prep = json.loads((base/'preparation.json').read_text())
        result = dict(status='passed preparation',inputs={str(p):sha(p) for p in paths},
            source_count=1036,source_ports=prep['source_ports'],source_nets=prep['source_nets'],
            additive_route_ledger=ledger,actual_layer_delta=deltas,all_other_layers_XOR_zero=True,
            TopMetal1_TopMetal2_unchanged=True,new_via_enclosures=True,
            original_polygons_preserved=True,text_hierarchy_port_parity=True,
            native_devices_placement_source_unchanged=True,all55nets_seven_star_cuts=True,
            additional_metal_over_resistors='present; field coupling not qualified',
            gds_sha256=sha(args.output/'bank.gds'),cdl_sha256=sha(args.output/'bank.cdl'),
            stock_DRC_LVS_AP='not run',conditional_R='not run',electrical_qualification='not run',adoption='not run')
        dump(args.output/'preparation.json',result)
        receipt.update(status='passed',preparation_sha256=sha(args.output/'preparation.json'))
    except Exception as error:
        receipt.update(status='failed',error=repr(error))
        raise
    finally:
        receipt.update(wall_s=time.monotonic()-start)
        dump(args.output/'run.json',receipt)
        print(json.dumps(receipt,indent=2))


if __name__ == '__main__':
    main()



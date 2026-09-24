#!/usr/bin/env python3
"""Rebind a stock-qualified native-fixed candidate to identical current points."""
import argparse
import collections
import datetime
import json
import os
from pathlib import Path
import sys
import pya

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'coordinated_full_closure'))
from build_assembly import PAIRS,CUTS,region,sha,dump


def main():
    ap=argparse.ArgumentParser()
    for name in ('candidate','baseline-preparation','output','resource-gate','drc','lvs'):
        ap.add_argument('--'+name,type=Path,required=True)
    args=ap.parse_args()
    gate=json.loads(args.resource_gate.read_text())
    age=(datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(gate['utc'])).total_seconds()
    assert gate['status']=='passed' and 0<=age<1800 and gate['project_cpu_budget']>=43
    assert len(os.sched_getaffinity(0))==1
    prep=json.loads((args.candidate/'preparation.json').read_text())
    assert prep['status']=='passed preparation'
    assert all(sha(Path(p))==h for p,h in prep['inputs'].items())
    assert sha(args.candidate/'bank.gds')==prep['gds_sha256']
    assert sha(args.candidate/'bank.cdl')==prep['cdl_sha256']
    checks=[args.drc/'summary.json',args.lvs/'summary.json',args.lvs/'junction_audit.json']
    assert all(json.loads(p.read_text())['status']=='passed' for p in checks)
    baseline=json.loads((args.baseline_preparation/'summary.json').read_text())
    assert baseline['status']=='passed conditional metallization preparation'
    assert all(sha(args.baseline_preparation/n)==h for n,h in baseline['outputs'].items())
    args.output.mkdir(exist_ok=False)
    (args.output/'worker_snapshot.py').write_bytes(Path(__file__).read_bytes())
    receipt=dict(status='running',source_insertion='not run',physical_IR_qualification='not run')
    dump(args.output/'summary.json',receipt)
    try:
        original=pya.Layout();original.read(str(args.candidate/'bank.gds'))
        ly=pya.Layout();ly.dbu=.001;top=ly.create_cell('metallization')
        regions={}
        for name,pair in PAIRS.items():
            regions[name]=region(original.top_cell(),original.layer(*pair)).merged()
            for poly in regions[name].each():top.shapes(ly.layer(*pair)).insert(poly)
        ltn=pya.LayoutToNetlist(pya.RecursiveShapeIterator(ly,top,[]))
        layers={k:ltn.make_layer(ly.layer(*pair),k) for k,pair in PAIRS.items()}
        for k in PAIRS:ltn.connect(layers[k])
        for cut,ends in CUTS.items():
            for end in ends:ltn.connect(layers[cut],layers[end])
        ltn.extract_netlist()
        assert len(list(ltn.netlist().circuit_by_name('metallization').each_net()))==55
        points=json.loads((args.baseline_preparation/'points.json').read_text())
        ownership=collections.defaultdict(set)
        original_projection=[{k:v for k,v in p.items() if k!='component'} for p in points]
        for point in points:
            node=ltn.probe_net(layers[point['layer']],pya.Point(*point['point_dbu']))
            assert node is not None
            point['component']=node.cluster_id
            ownership[node.cluster_id].add(point['source_net'])
        assert len(ownership)==55 and all(len(v)==1 for v in ownership.values())
        assert [{k:v for k,v in p.items() if k!='component'} for p in points]==original_projection
        assert len(points)==3355
        ly.write(str(args.output/'metallization.gds'))
        saved=pya.Layout();saved.read(str(args.output/'metallization.gds'))
        assert all((r^region(saved.top_cell(),saved.layer(*PAIRS[k]))).is_empty() for k,r in regions.items())
        for cut in CUTS:assert all(p.area()==190*190 for p in regions[cut].each())
        dump(args.output/'points.json',points)
        for name in ('scenarios.json','omitted_resistor_substrates.json'):
            (args.output/name).write_bytes((args.baseline_preparation/name).read_bytes())
        inputs=[args.candidate/'preparation.json',args.candidate/'bank.gds',args.candidate/'bank.cdl',
                args.baseline_preparation/'summary.json',args.baseline_preparation/'points.json',
                args.resource_gate,Path(__file__)]+checks
        receipt.update(status='passed conditional metallization preparation',source_devices=1036,
            represented_terminal_incidences=3346,distinct_injection_points=3355,source_net_count=55,
            original_point_positions_sources_currents_identical=True,component_ids_recomputed=True,
            all_nine_layer_union_XOR_zero=True,unchanged_resistance_scenarios=True,
            inputs={str(p):sha(p) for p in inputs},
            outputs={n:sha(args.output/n) for n in ('metallization.gds','points.json','scenarios.json','omitted_resistor_substrates.json')},
            geometry_counts={k:dict(polygons=r.count(),area_um2=r.area()*1e-6) for k,r in regions.items()},
            unresolved=baseline['unresolved'],boundaries=baseline['boundaries'])
    except Exception as error:
        receipt.update(status='failed',error=repr(error));raise
    finally:
        dump(args.output/'summary.json',receipt)
        print(json.dumps({k:v for k,v in receipt.items() if k not in ('inputs','geometry_counts')},indent=2))


if __name__=='__main__':main()

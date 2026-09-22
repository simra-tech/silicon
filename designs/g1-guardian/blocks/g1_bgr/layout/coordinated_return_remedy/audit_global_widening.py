#!/usr/bin/env python3
"""Read-only same-layer route-widening ownership and clearance preflight."""
import argparse
import json
import os
from pathlib import Path
import sys
import pya

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'coordinated_full_closure'))
from build_assembly import PAIRS, METALS, CUTS, region, sha, dump

PROPOSALS = [
    dict(name='general_VSS_collector', net='vss', layer='M3', bbox=[16400, 12660, 417950, 15460],
         reason='Add below existing general rail, leaving precision rail and finite star untouched.'),
    dict(name='east_VSS_trunk', net='vss', layer='M5', bbox=[417800, 14910, 419500, 143550],
         reason='Widen outward into existing reservation; same layer and endpoints.'),
    dict(name='east_VDD_port_link', net='vdd', layer='M3', bbox=[287210, 141960, 418750, 142440],
         reason='Same centerline, .48um width; neighboring .60um pitch permits only limited widening.'),
    dict(name='VDD_MOS_vertical', net='vdd', layer='M4', bbox=[286640, 142200, 287360, 312000],
         reason='Same vertical routing column, .72um width; actual obstacles decide.'),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--gds', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    assert sha(args.gds) == '71892e4308000401f857c88eda21c8590dc03c1d7534fecc4851104baec17383'
    assert len(os.sched_getaffinity(0)) == 1
    assert not args.output.exists()
    ly = pya.Layout()
    ly.read(str(args.gds))
    top = ly.top_cell()
    ltn = pya.LayoutToNetlist(pya.RecursiveShapeIterator(ly, top, []))
    layers = {k: ltn.make_layer(ly.layer(*v), k) for k, v in PAIRS.items()}
    for k in PAIRS:
        ltn.connect(layers[k])
    for cut, ends in CUTS.items():
        for end in ends:
            ltn.connect(layers[cut], layers[end])
    ltn.extract_netlist()
    route = Path(os.environ['G1_RESULTS_ROOT']) / 'bgr-assembly-20260922-r5/routing.json'
    probes = json.loads(route.read_text())['source_probes']
    net_objects = {}
    for probe in probes:
        net = ltn.probe_net(layers[probe['layer']], pya.Point(*probe['point']))
        assert net is not None
        if probe['net'] in net_objects:
            assert net_objects[probe['net']].cluster_id == net.cluster_id
        net_objects[probe['net']] = net
    assert len(net_objects) == 55
    reports = []
    for proposal in PROPOSALS:
        owned = ltn.shapes_of_net(net_objects[proposal['net']], layers[proposal['layer']], True)
        assert isinstance(owned, pya.Region)
        all_metal = region(top, ly.layer(*PAIRS[proposal['layer']]))
        other = all_metal - owned
        new = pya.Region(pya.Box(*proposal['bbox']))
        delta = new - all_metal
        collision = new & other
        near = new.sized(210) & other
        reports.append(dict(proposal, original_net_area_um2=owned.area()*1e-6,
            added_area_um2=delta.area()*1e-6, touches_existing_own_net=not (new & owned).is_empty(),
            crossnet_overlap_um2=collision.area()*1e-6, other_net_within_210nm_area_um2=near.area()*1e-6,
            near_obstacle_bboxes_dbu=[[p.bbox().left,p.bbox().bottom,p.bbox().right,p.bbox().top] for p in near.each()],
            same_net_union_connected=(owned + new).merged().count() <= owned.merged().count(),
            passed=collision.is_empty() and near.is_empty() and not (new & owned).is_empty()))
    dump(args.output, dict(status='passed' if all(r['passed'] for r in reports) else 'failed proposal clearance',
        inputs={str(p):sha(p) for p in (args.gds,route,Path(__file__))}, proposals=reports,
        mutation='not run', stock_DRC_LVS='not run', electrical_qualification='not run'))
    print(json.dumps(reports, indent=2))


if __name__ == '__main__':
    main()

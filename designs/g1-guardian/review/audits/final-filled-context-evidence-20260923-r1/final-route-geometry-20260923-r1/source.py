#!/usr/bin/env python3
"""Bind final critical DEF centerlines to native GDS and inventory nearby fill."""
import argparse
import json
import os
from pathlib import Path
import statistics
import sys
import pya
from route_inventory import VICTIMS, LAYERS, sha
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from place_closed_analog import region

NUMBERS = dict(zip(LAYERS, [8, 10, 30, 50, 67, 126, 134]))


def stripe(segment):
    return pya.Region(pya.Path([pya.Point(*segment['start_dbu']),
                                pya.Point(*segment['end_dbu'])], 2, 0, 0))


def controls():
    s = dict(start_dbu=[0, 0], end_dbu=[1000, 0])
    solid = pya.Region(pya.Box(-100, -100, 1100, 100))
    broken = solid-pya.Region(pya.Box(400, -200, 600, 200))
    offset = pya.Region(pya.Box(-100, 10, 1100, 210))
    assert (stripe(s)-solid).is_empty()
    assert not (stripe(s)-broken).is_empty()
    assert not (stripe(s)-offset).is_empty()
    return 'passed covered, missing-interior and off-center rejection'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for option in ('inventory', 'candidate', 'output'):
        parser.add_argument('--'+option, type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists() and len(os.sched_getaffinity(0)) == 1
    assert pya.__version__ == '0.30.9'
    data = json.loads(args.inventory.read_text())
    assert data['status'] == 'passed exact DEF grammar and route inventory'
    assert data['DEF_sha256'] == '348dba8bc4db2f4aeefb9233f7aa5fb60512e7132963628dce7df5a0bfb2b612'
    metadata = json.loads((args.candidate/'analysis.json').read_text())
    source = args.candidate/'filled_native.gds'
    assert metadata['status'].startswith('passed')
    assert sha(source) == metadata['GDS_sha256'] == '4d3907c50f07946ef27a6d53402cf319264499a21379d2de80e9c4f1adbae299'
    args.output.mkdir(parents=True)
    (args.output/'source.py').write_bytes(Path(__file__).read_bytes())
    result = dict(status='running', GDS_sha256=sha(source), DEF_sha256=data['DEF_sha256'],
        inventory_sha256=sha(args.inventory), metadata_sha256=sha(args.candidate/'analysis.json'),
        script_sha256=sha(Path(__file__)), helper_sha256=sha(Path(__file__).with_name('route_inventory.py')),
        KLayout=pya.__version__, controls=controls(), routes=[],
        not_run=['full device/terminal connectivity in this invocation', 'capacitance extraction',
                 'via/contact resistance', 'actual-source electrical coupling acceptance'],
        not_applicable=['statistical seed for deterministic geometry'],
        limitations=['Only six critical analog DEF signal nets; supply and native macro internals excluded.',
                    'Two-nanometer centerline stripe with zero endpoint extension is a coverage probe, not complete wire-polygon equivalence.',
                    'Sampled width and L/median-width are geometric estimates; junction widening and end effects are not a sheet-R model.',
                    'Datatype22 proximity is projected geometry, not electrical connection or a ground assignment.',
                    'Unfilled terminal proof is separate; this check does not promote incomplete LVS or PEX.'])
    try:
        layout = pya.Layout(); layout.read(str(source)); top = layout.top_cell()
        assert layout.dbu == .001 and top.name == 'placed_core_NOT_CONNECTED_FULLCHIP'
        assert top.bbox() == pya.Box(0, 0, 1414000, 1414000)
        metals = {name: region(layout, top, pya.LayerInfo(number, 0)) for name, number in NUMBERS.items()}
        fills = {name: region(layout, top, pya.LayerInfo(number, 22)) for name, number in NUMBERS.items()}
        failures = []
        for net in data['nets']:
            if net['net'] not in VICTIMS:
                continue
            segments = [s for path in net['paths'] for s in path['segments']]
            corridors = {}; rows = []
            assert segments
            for index, segment in enumerate(segments):
                layer = segment['layer']; narrow = stripe(segment)
                missing = narrow-metals[layer]
                covered = missing.is_empty()
                if not covered:
                    failures.append([net['net'], index])
                first, second = segment['start_dbu'], segment['end_dbu']
                horizontal = first[1] == second[1]
                widths = []
                for fraction in (.25, .5, .75):
                    x, y = [round(first[i]+fraction*(second[i]-first[i])) for i in range(2)]
                    box = pya.Box(x-1, y-10000, x+1, y+10000) if horizontal else pya.Box(x-10000, y-1, x+10000, y+1)
                    hits = [poly for poly in (metals[layer]&pya.Region(box)).merged().each()
                            if poly.inside(pya.Point(x, y))]
                    assert len(hits) <= 1
                    widths.append((hits[0].bbox().height() if horizontal else hits[0].bbox().width())*.001 if hits else None)
                valid = [v for v in widths if v is not None]
                clipped = any(v >= 19.998 for v in valid)
                estimate = segment['length_dbu']*.001/statistics.median(valid) if len(valid) == 3 and not clipped else None
                rows.append(dict(segment_index=index, **segment, centerline_status='passed' if covered else 'failed',
                    missing_stripe_area_um2=missing.area()*1e-6, sampled_widths_um=widths,
                    width_sample_clipped=clipped, geometric_squares_estimate=estimate))
                corridors.setdefault(layer, pya.Region())
                corridors[layer] += narrow
            proximity = []
            for layer, corridor in corridors.items():
                corridor = corridor.merged(); index = LAYERS.index(layer)
                for neighbor in LAYERS[max(0, index-1):min(len(LAYERS), index+2)]:
                    bands = []
                    for distance in (0, 1, 2, 5, 10, 20):
                        window = corridor.sized(distance*1000)
                        overlap = fills[neighbor]&window
                        bands.append(dict(centerline_expansion_um=distance,
                            projected_fill_area_um2=overlap.area()*1e-6,
                            interacting_fill_polygons=fills[neighbor].interacting(window).count()))
                    proximity.append(dict(route_layer=layer, fill_layer=neighbor, bands=bands))
            result['routes'].append(dict(net=net['net'], segments=rows, fill_proximity=proximity))
        assert {row['net'] for row in result['routes']} == VICTIMS
        assert sha(source) == result['GDS_sha256'] and sha(args.inventory) == result['inventory_sha256']
        result.update(status='passed exact critical-route centerline coverage and fill inventory' if not failures else 'failed critical-route coverage', failures=failures)
    except Exception as error:
        result.update(status='failed geometry audit', error=repr(error))
        raise
    finally:
        (args.output/'analysis.json').write_text(json.dumps(result, indent=2)+'\n')
        print(json.dumps({k:v for k,v in result.items() if k != 'routes'}, indent=2))
    raise SystemExit(0 if result['status'].startswith('passed') else 1)


if __name__ == '__main__':
    main()

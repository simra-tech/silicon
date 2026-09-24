#!/usr/bin/env python3
"""Strict inventory of final DEF signal routes; geometry, not extracted RC."""
import argparse
import hashlib
import json
from pathlib import Path
import re

LAYERS = ['Metal1', 'Metal2', 'Metal3', 'Metal4', 'Metal5', 'TopMetal1', 'TopMetal2']
VICTIMS = {'i_core.sense_p', 'i_core.sense_n', 'i_core.isense',
           'i_core.vref', 'i_core.vref_buf', 'i_core.iptat'}
POINT = re.compile(r'\(\s+([*-]?\d+|\*)\s+([*-]?\d+|\*)(?:\s+(-?\d+))?\s+\)')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def name(token):
    # Only the escaping actually emitted by the pinned router is supported.
    token = token.replace('\\[', '[').replace('\\]', ']')
    assert '\\' not in token, token
    return token


def route(text):
    layer, rest = text.strip().split(None, 1)
    assert layer in LAYERS, layer
    points, extensions = [], []
    while True:
        match = POINT.match(rest)
        if not match:
            break
        values = match.group(1, 2)
        assert points or '*' not in values, 'First point cannot inherit coordinates'
        point = [points[-1][i] if value == '*' else int(value)
                 for i, value in enumerate(values)]
        points.append(point)
        extensions.append(None if match[3] is None else int(match[3]))
        rest = rest[match.end():].strip()
    assert points, text
    segments = []
    for first, second in zip(points, points[1:]):
        assert first != second and (first[0] == second[0] or first[1] == second[1]), 'Non-Manhattan/zero segment'
        segments.append(dict(layer=layer, start_dbu=first, end_dbu=second,
                             length_dbu=abs(first[0]-second[0])+abs(first[1]-second[1])))
    patch = via = None
    if rest.startswith('RECT '):
        match = re.fullmatch(r'RECT\s+\(\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)\s+\)', rest)
        assert match and len(points) == 1 and extensions == [None], rest
        offsets = list(map(int, match.groups()))
        assert offsets[0] < offsets[2] and offsets[1] < offsets[3]
        patch = dict(layer=layer, anchor_dbu=points[0], offsets_dbu=offsets)
    elif rest:
        assert re.fullmatch(r'(?:Via[1-4]_[XY]{2}|TopVia[12](?:EWNS|NS|EW)?)', rest), rest
        assert len(points) == 1 and extensions == [None]
        via = dict(lower_route_layer=layer, name=rest, point_dbu=points[0])
    else:
        assert segments, 'Unexplained isolated route point'
    return dict(layer=layer, points_dbu=points, endpoint_extensions_dbu=extensions,
                segments=segments, patch=patch, via=via)


def parse(text):
    units, = re.findall(r'^UNITS DISTANCE MICRONS (\d+) ;$', text, re.M)
    count, section = re.findall(r'^NETS (\d+) ;\s*\n(.*?)^END NETS$', text, re.M | re.S)[0]
    records = re.findall(r'^\s*- (.*?)\s*;', section, re.M | re.S)
    assert len(records) == int(count)
    assert not re.sub(r'^\s*- (.*?)\s*;', '', section, flags=re.M | re.S).strip()
    nets = []
    for record in records:
        head, *routed = record.split('+ ROUTED')
        assert len(routed) <= 1
        match = re.fullmatch(r'(\S+)\s+(.+?)\s+\+ USE (SIGNAL|CLOCK)\s*', head, re.S)
        assert match, head
        endpoints = re.findall(r'\(\s*(\S+)\s+(\S+)\s*\)', match[2])
        assert endpoints and not re.sub(r'\(\s*(\S+)\s+(\S+)\s*\)', '', match[2]).strip()
        paths = [route(part) for part in re.split(r'\bNEW\s+', routed[0])] if routed else []
        nets.append(dict(net=name(match[1]), use=match[3], endpoints=[list(map(name, pair)) for pair in endpoints],
                         paths=paths, status='routed' if paths else 'no route declared'))
    assert len({net['net'] for net in nets}) == len(nets)
    return int(units), nets


def parallel_candidates(nets, units):
    """All same/adjacent-layer parallel overlaps within 20um centerlines."""
    segments = [(net['net'], index, segment) for net in nets
                for index, segment in enumerate(s for path in net['paths'] for s in path['segments'])]
    rows = []
    for victim, vi, first in segments:
        if victim not in VICTIMS:
            continue
        a, b = first['start_dbu'], first['end_dbu']
        axis = 1 if a[0] == b[0] else 0
        for neighbor, ni, second in segments:
            if neighbor == victim:
                continue
            c, d = second['start_dbu'], second['end_dbu']
            if (c[1-axis] != d[1-axis] or
                    abs(LAYERS.index(first['layer'])-LAYERS.index(second['layer'])) > 1):
                continue
            low, high = max(min(a[axis], b[axis]), min(c[axis], d[axis])), min(max(a[axis], b[axis]), max(c[axis], d[axis]))
            separation = abs(a[1-axis]-c[1-axis])
            if high <= low or separation > 20*units:
                continue
            rows.append(dict(victim=victim, neighbor=neighbor,
                victim_segment=vi, neighbor_segment=ni,
                victim_layer=first['layer'], neighbor_layer=second['layer'],
                longitudinal_axis='y' if axis else 'x', shared_interval_dbu=[low, high],
                victim_transverse_dbu=a[1-axis], neighbor_transverse_dbu=c[1-axis],
                overlap_um=(high-low)/units, centerline_separation_um=separation/units))
    return sorted(rows, key=lambda row: (row['victim'], row['centerline_separation_um'], -row['overlap_um'], row['neighbor']))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for argument in ('route', 'output'):
        parser.add_argument('--'+argument, type=Path, required=True)
    parser.add_argument('--route-metadata-sha256',help='Explicit immutable successor binding; default original route is unchanged')
    args = parser.parse_args()
    assert not args.output.exists()
    args.output.mkdir(parents=True)
    (args.output/'source.py').write_bytes(Path(__file__).read_bytes())
    source = args.route/'detailed.def'
    metadata = json.loads((args.route/'analysis.json').read_text())
    if metadata['status']=='passed exact three-segment g_shared_bare spacing repair; stock checks not run':
        assert args.route_metadata_sha256
        import sys
        sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
        from repair_gshared_route_spacing import validate_patch
        validate_patch(args.route)
    else:
        assert metadata['status'] == 'passed isolated detailed-route candidate with zero router markers'
    assert sha(source) == metadata['detailed.def_sha256']
    if args.route_metadata_sha256:
        assert sha(args.route/'analysis.json')==args.route_metadata_sha256
    else:
        assert sha(source)=='348dba8bc4db2f4aeefb9233f7aa5fb60512e7132963628dce7df5a0bfb2b612'
    units, nets = parse(source.read_text())
    assert units == 1000 and VICTIMS <= {net['net'] for net in nets}
    result = dict(status='passed exact DEF grammar and route inventory', DEF_sha256=sha(source),
        metadata_sha256=sha(args.route/'analysis.json'), script_sha256=sha(Path(__file__)),
        units_per_um=units, nets=nets, parallel_candidates=parallel_candidates(nets, units),
        not_run=['actual GDS polygon coverage', 'full connectivity in this invocation',
                 'width/spacing verification', 'capacitance or resistance extraction', 'electrical acceptance'],
        not_applicable=['random seed for deterministic geometry parsing'],
        limitations=['NETS excludes SPECIALNETS and macro-internal geometry.',
                    'Endpoint extension and RECT patches retained separately; not approximated as centerline length.',
                    'Parallel centerline proximity is not edge clearance, coupling, or a complete crossing/via context inventory.',
                    'Previous-layout coupling results do not transfer through this inventory.'])
    (args.output/'analysis.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(dict(status=result['status'], nets=len(nets),
        routed=sum(bool(net['paths']) for net in nets), parallel_candidates=len(result['parallel_candidates']))))


if __name__ == '__main__':
    main()

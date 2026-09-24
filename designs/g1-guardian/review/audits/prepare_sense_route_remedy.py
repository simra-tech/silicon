#!/usr/bin/env python3
"""Generate isolated SENSE route geometry; no stock sign-off checks are implied."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path
import pya

ROOT = Path(__file__).resolve().parents[4]
SOURCE = ROOT / 'build/scratch/pad-outward-dummy-clean-20260921/g1_chip_top.gds'
EXPECTED = '2d895efbb0e1c35ed7c891d376b010e041005d731ecd6d5448d872adfe55c9ca'
DELIVERED = ROOT / 'designs/g1-guardian/blocks/g1_padring/layout/g1_chip_top.gds'
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert sha(SOURCE) == EXPECTED
    delivered_hash = sha(DELIVERED)
    args.output.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(__file__, args.output / 'generator.py')
    ly = pya.Layout()
    ly.read(str(SOURCE))
    top = ly.cell('g1_chip_top')
    dbu = ly.dbu
    box = lambda *q: pya.DBox(*q).to_itype(dbu)
    window = box(984.8, 457, 1030, 607)
    before = {key: pya.Region(top.begin_shapes_rec(ly.layer(*key))).merged()
              for key in [(30, 0), (49, 0), (50, 0), (30, 22), (50, 22)]}
    removed = []
    for layer, count in ((30, 4), (50, 2)):
        shapes = [s for s in top.shapes(ly.layer(layer, 0)).each_overlapping(window)
                  if not s.is_text() and (window & s.bbox()) == s.bbox()]
        assert len(shapes) == count, (layer, len(shapes))
        for shape in shapes:
            removed.append({'layer': layer, 'polygon_um': str(shape.polygon.to_dtype(dbu))})
            shape.delete()
    via_points = [(1022.4, 458.64), (1022.4, 605.22),
                  (1022.88, 464.52), (1022.88, 493.5)]
    via_instances = []
    for x, y in via_points:
        point = pya.DPoint(x, y).to_itype(dbu)
        matches = [i for i in top.each_inst() if i.bbox().contains(point)
                   and i.cell.name == 'VIA_Via3_XY']
        assert len(matches) == 1, (x, y, [(i.cell.name, str(i.bbox())) for i in matches])
        inst = matches[0]
        assert not inst.is_regular_array()
        via_instances.append({'cell': inst.cell.name, 'point_um': [x, y]})
        inst.delete()
    additions = {30: pya.Region(), 49: pya.Region(), 50: pya.Region()}
    routes = []
    for name, track, pad_y, core_y, width in [
            ('P', 1024.5, 493.5, 464.52, .5),
            ('N', 1021.0, 605.22, 458.64, 2.5)]:
        segments = [(30, (984.96, core_y), (track, core_y), 1.0),
                    (50, (track, core_y), (track, pad_y), width),
                    (30, (track, pad_y), (1029.12, pad_y), 1.0)]
        wire_r = cap = 0.0
        records = []
        for layer, start, end, wire_width in segments:
            path = pya.DPath([pya.DPoint(*start), pya.DPoint(*end)], wire_width,
                             wire_width / 2, wire_width / 2)
            additions[layer].insert(path.to_itype(dbu))
            length = abs(start[0] - end[0]) + abs(start[1] - end[1])
            resistance = .103 * length / wire_width
            capacitance = (1.2e-5 if layer == 30 else 8.94e-6) * length * wire_width
            capacitance += (4.48e-5 if layer == 30 else 4.5e-5) * 2 * length
            wire_r += resistance
            cap += capacitance * 1000
            records.append({'layer': layer, 'start_um': start, 'end_um': end,
                            'width_um': wire_width, 'length_um': length,
                            'wire_R_ohm_estimate': resistance})
        for y in (core_y, pad_y):
            # 2x2 cuts: 0.19 width, 0.22 space, 0.05 enclosure on both metals.
            for dx in (-.205, .205):
                for dy in (-.205, .205):
                    additions[49].insert(box(track + dx - .095, y + dy - .095,
                                             track + dx + .095, y + dy + .095))
            for layer in (30, 50):
                additions[layer].insert(box(track - .35, y - .35, track + .35, y + .35))
        routes.append({'net': name, 'segments': records, 'via_arrays': 2,
                       'cuts_per_array': 4, 'wire_R_ohm_estimate': wire_r,
                       'via_R_ohm_estimate': 2 * 20 / 4,
                       'total_R_ohm_estimate': wire_r + 10,
                       'ground_C_fF_estimate': cap})
    fill_removed = {}
    # Reconstruct only affected fill layers at top level. Delete whole fill
    # polygons touching the clearance window, preserving all other geometry.
    for layer in (30, 50):
        keepout = additions[layer].sized(round(.30 / dbu))
        fill = before[layer, 22]
        removed_fill = fill.interacting(keepout)
        retained = fill - removed_fill
        for cell in ly.each_cell():
            cell.shapes(ly.layer(layer, 22)).clear()
        top.shapes(ly.layer(layer, 22)).insert(retained)
        fill_removed[str(layer)] = {'polygons': removed_fill.count(),
                                    'area_um2': removed_fill.area() * dbu ** 2,
                                    'geometry_um': [str(q.to_dtype(dbu)) for q in removed_fill.each()]}
    for layer, region in additions.items():
        top.shapes(ly.layer(layer, 0)).insert(region.merged())
    candidate = args.output / 'g1_chip_top.gds'
    ly.write(str(candidate))
    deltas = {}
    for key, source in before.items():
        current = pya.Region(top.begin_shapes_rec(ly.layer(*key))).merged()
        xor = source ^ current
        deltas[f'{key[0]}/{key[1]}'] = {'XOR_area_um2': xor.area() * dbu ** 2,
                                      'XOR_bbox_um': str(xor.bbox().to_dtype(dbu))}
    manifest = {'scope': 'UNPROMOTED scratch geometry; physical/electrical sign-off not run',
                'source_gds': str(SOURCE.relative_to(ROOT)), 'source_sha256': EXPECTED,
                'delivered_sha256': delivered_hash, 'candidate_sha256': sha(candidate),
                'generator_sha256': sha(Path(__file__)), 'klayout_version': pya.__version__,
                'removed_top_routes': removed, 'removed_via_instances': via_instances,
                'routes': routes, 'removed_fill': fill_removed, 'geometry_deltas': deltas,
                'checks': {'stock_DRC': 'not run', 'conductor_connectivity': 'not run',
                           'density': 'not run', 'antenna': 'not run', 'LVS': 'not run',
                           'PEX': 'not run', 'electrical_route_anchor': 'not run',
                           'pinned_KLayout_parity': 'not run', 'production_adoption': 'not run'},
                'estimate_limits': ['Sheet resistance .103 ohm/square and single via 20 ohm from prior nominal technology audit.',
                                    'Uniform current and ideal via parallelism; spreading, corners, terminal access excluded.',
                                    'Capacitance uses prior LEF area/edge coefficients; no coupling/fill extraction.']}
    assert sha(SOURCE) == EXPECTED and sha(DELIVERED) == delivered_hash
    (args.output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({'candidate_sha256': manifest['candidate_sha256'], 'routes': routes,
                      'geometry_deltas': deltas}, indent=2))


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Exact delivered-GDS interface clips; focused coupling diagnostics, not LVS."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

import pya

ROOT = Path(__file__).resolve().parents[4]
PAIRS = {
    'isense_clock': ('i_core.isense', 'i_core.cmp_clk', 50, 615.72, 733.92, 734.4, 29.4),
    'vref_dac': ('i_core.vref', 'i_core.dac_soft[5]', 10, 711.27, 732.0, 731.52, 114.66),
    'vrefbuf_dac': ('i_core.vref_buf', 'i_core.dac_hard[4]', 50, 705.81, 732.96, 732.48, 118.86),
    'iptat_isense': ('i_core.iptat', 'i_core.isense', 50, 632.73, 733.44, 733.92, 260.82),
}
METALS = [8, 10, 30, 50, 67, 126, 134]
VIAS = [19, 29, 49, 66, 125, 133]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pair', choices=sorted(PAIRS), required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--gds', type=Path, default=ROOT/'designs/g1-guardian/blocks/g1_padring/layout/g1_chip_top.gds')
    parser.add_argument('--expected-sha256', required=True)
    parser.add_argument('--length-um', type=float, default=20)
    parser.add_argument('--context-um', type=float, default=12)
    args = parser.parse_args()
    victim, neighbor, target_layer, y, xp, xn, overlap = PAIRS[args.pair]
    if not 0 < args.length_um < overlap or not 2 <= args.context_um <= 96:
        parser.error('clip length must stay inside the shared segment; context 2..96 um')
    source_path = args.gds.resolve()
    if sha(source_path) != args.expected_sha256:
        parser.error('GDS identity changed; do not silently follow geometry edits')
    args.output.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(__file__, args.output/'prepare.py')
    layout = pya.Layout()
    layout.read(str(source_path))
    top = layout.cell('g1_chip_top')
    assert top is not None
    dbu = layout.dbu
    center_x = (xp + xn)/2
    bounds = [center_x-args.context_um/2, y-args.length_um/2,
              center_x+args.context_um/2, y+args.length_um/2]
    window = pya.Region(pya.DBox(*bounds).to_itype(dbu))
    regions = {}
    for layer in METALS + VIAS:
        for datatype in ([0, 22] if layer in METALS else [0]):
            regions[layer, datatype] = (pya.Region(top.begin_shapes_rec(layout.layer(layer, datatype))) & window).merged()
    points = {'P': pya.DPoint(xp, y).to_itype(dbu),
              'N': pya.DPoint(xn, y).to_itype(dbu)}
    labels = []
    for (layer, datatype), region in regions.items():
        if layer not in METALS:
            continue
        for index, polygon in enumerate(region.each()):
            matches = [name for name, point in points.items()
                       if layer == target_layer and datatype == 0 and polygon.inside(point)]
            if matches:
                assert len(matches) == 1, 'two target wires geometrically joined'
                name = matches[0]
                point = points[name]
                # The target must cross both longitudinal clip boundaries.
                assert polygon.bbox().bottom == window.bbox().bottom
                assert polygon.bbox().top == window.bbox().top
            else:
                name = ('FILL' if datatype == 22 else 'CTX') + '_L%d_%d' % (layer, index)
                point = polygon.bbox().center()
                if not polygon.inside(point):
                    point = list(polygon.decompose_trapezoids())[0].bbox().center()
                    assert polygon.inside(point)
            labels.append(dict(name=name, source_layer=[layer, datatype], point_dbu=[point.x, point.y]))
    assert sum(lab['name'] == 'P' for lab in labels) == 1
    assert sum(lab['name'] == 'N' for lab in labels) == 1
    variants = []
    for mode in ['no_fill', 'actual_fill']:
        out = pya.Layout()
        out.dbu = dbu
        # Existing stock-extraction runner uses this diagnostic top-cell name.
        cell = out.create_cell('sense_fill_clip')
        for (layer, datatype), region in regions.items():
            if mode != 'no_fill' or datatype != 22:
                cell.shapes(out.layer(layer, datatype)).insert(region)
        for label in labels:
            layer, datatype = label['source_layer']
            if mode != 'no_fill' or datatype != 22:
                cell.shapes(out.layer(layer, 25)).insert(pya.Text(label['name'], pya.Trans(*label['point_dbu'])))
        path = args.output/(mode+'.gds')
        out.write(str(path))
        check = pya.Layout()
        check.read(str(path))
        checks = []
        for (layer, datatype), region in regions.items():
            expected = pya.Region() if mode == 'no_fill' and datatype == 22 else region
            got = pya.Region(check.cell('sense_fill_clip').begin_shapes_rec(check.layer(layer, datatype)))
            assert (expected ^ got).is_empty()
            checks.append(dict(layer=[layer, datatype], polygons=got.count(), xor_area_um2=0))
        variants.append(dict(variant=mode, sha256=sha(path), geometry=checks))
    package = Path('/usr/local/lib/python3.12/dist-packages/klayout_pex')
    rules = package/'pdk/ihp-sg13g2/libs.tech/kpex'
    record = dict(status='passed', pair=args.pair, labels=labels,
                  target_names={'P': victim, 'N': neighbor}, target_layer=[target_layer, 0],
                  target_points_um={'P': [xp, y], 'N': [xn, y]}, source_gds=str(source_path.relative_to(ROOT)),
                  source_gds_sha256=sha(source_path), clip_box_um=bounds, length_um=args.length_um,
                  context_um=args.context_um, observed_parallel_length_um=overlap,
                  dbu_um=dbu, klayout_version=pya.__version__, variants=variants,
                  installed_deck_hashes={str(p.relative_to(package)): sha(p) for p in rules.rglob('*.lvs')},
                  scope='Exact clipped metal/via geometry plus diagnostic labels; target identity follows delivered DEF/GDS midpoint audit, not full connectivity proof. Devices and outside-clip conductors omitted. Grounded context in later reduction is a diagnostic boundary, not actual activity. No whole-route scaling or electrical qualification implied.')
    (args.output/'provenance.json').write_text(json.dumps(record, indent=2)+'\n')
    print(json.dumps(dict(status='passed', pair=args.pair, box=bounds, variants=[v['sha256'] for v in variants])))


if __name__ == '__main__':
    main()

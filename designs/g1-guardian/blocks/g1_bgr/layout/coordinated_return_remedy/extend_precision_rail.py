#!/usr/bin/env python3
"""Actual XR16 metallic rail/current tree; compact head/contact R excluded."""
import argparse
import json
import os
from pathlib import Path
import sys
import pya

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'coordinated_full_closure'))
from export_cc_api import sha, dump, plain


def main():
    ap = argparse.ArgumentParser()
    for name in ('gds', 'access', 'output'):
        ap.add_argument('--' + name, type=Path, required=True)
    args = ap.parse_args()
    assert len(os.sched_getaffinity(0)) == 1
    assert sha(args.gds) == '71892e4308000401f857c88eda21c8590dc03c1d7534fecc4851104baec17383'
    access = json.loads(args.access.read_text())
    assert access['status'].startswith('passed actual access inventory')
    ly = pya.Layout()
    ly.read(str(args.gds))
    top = ly.top_cell()
    pairs = {'M1': 8, 'M2': 10, 'M3': 30, 'M4': 50, 'Via1': 19, 'Via2': 29, 'Via3': 49}
    regions = {name: plain(pya.Region(top.begin_shapes_rec(ly.layer(layer, 0)))) for name, layer in pairs.items()}
    polygons = {name: list(r.each()) for name, r in regions.items()}
    def contained(name, box):
        assert plain(pya.Region(pya.Box(*box)) - regions[name]).is_empty(), (name, box)
    def cuts(name, x, y, quad=False):
        expected = [[x + dx - 95, y + dy - 95, x + dx + 95, y + dy + 95]
                    for dx in ((-210, 210) if quad else (0,)) for dy in (-210, 210)]
        for box in expected:
            contained(name, box)
        window = pya.Region(pya.Box(x - 370, y - 370, x + 370, y + 370))
        hits = [p for p in polygons[name] if not plain(pya.Region(p) & window).is_empty()]
        actual = sorted([p.bbox().left, p.bbox().bottom, p.bbox().right, p.bbox().top] for p in hits)
        assert actual == sorted(expected), (name, x, y, actual)
        return expected
    # Exact actual continuous precision rail, and shared stem after remedy.
    contained('M3', [16000, 15860, 403000, 16660])
    contained('M2', [15640, 15060, 16360, 16260])
    interfaces = [dict(center_dbu=[16000, y], cuts=cuts('Via2', 16000, y, True)) for y in (15060, 16260)]
    rows = []
    for head in access['resistor_precision_heads']:
        hx, hy = head['M1_probe_dbu']
        x, target = hx - 300, 16260
        upper = hy > target
        column_layer = 'M4' if upper else 'M2'
        contained(column_layer, [x - 150, min(hy, target), x + 150, max(hy, target)])
        arrays = [dict(layer='Via1', center_dbu=[x, hy], boxes=cuts('Via1', x, hy))]
        if upper:
            arrays += [dict(layer=layer, center_dbu=[x, hy], boxes=cuts(layer, x, hy)) for layer in ('Via2', 'Via3')]
            arrays.append(dict(layer='Via3', center_dbu=[x, target], boxes=cuts('Via3', x, target)))
        else:
            arrays.append(dict(layer='Via2', center_dbu=[x, target], boxes=cuts('Via2', x, target)))
        rows.append(dict(source=head['source'], x_dbu=x, head_y_dbu=hy, injection_A=head['injection_A'],
                         column_layer=column_layer, column_length_um=abs(hy - target) * .001,
                         column_width_um=.3, arrays=arrays))
    rows.sort(key=lambda r: r['x_dbu'])
    assert len(rows) == 24 and len({r['x_dbu'] for r in rows}) == 24
    scenarios = {}
    iq56 = access['precision_stem']['Q56_injection_A']
    ir16 = sum(r['injection_A'] for r in rows)
    for name, sheet, via in [('LEF', .103, 20.), ('KPEX', .088, 9.)]:
        previous, cumulative = 16000, 0.
        values, edges = [], []
        stem_R = 2 * via / 4 + sheet * 1.2 / .72
        for i, row in enumerate(rows):
            current = sum(r['injection_A'] for r in rows[i:])
            segment_R = sheet * (row['x_dbu'] - previous) / 800
            cumulative += current * segment_R
            edges.append(dict(from_x_dbu=previous, to_x_dbu=row['x_dbu'], current_A=current,
                              resistance_ohm=segment_R, drop_V=current * segment_R))
            local_wire_R = sheet * row['column_length_um'] / row['column_width_um']
            local_vias_R = len(row['arrays']) * via / 2
            local_V = row['injection_A'] * (local_wire_R + local_vias_R)
            matrix_V = sum(sheet * (min(row['x_dbu'], other['x_dbu']) - 16000) / 800 * other['injection_A'] for other in rows)
            assert abs(matrix_V - cumulative) < 1e-15
            values.append(dict(source=row['source'], rail_V=cumulative, column_R_ohm=local_wire_R,
                array_R_ohm=local_vias_R, local_access_V=local_V, common_stem_V=(iq56 + ir16) * stem_R,
                partial_total_V=cumulative + local_V + (iq56 + ir16) * stem_R))
            previous = row['x_dbu']
        scenarios[name] = dict(per_source=values, rail_edges=edges, shared_stem_R_ohm=stem_R,
            shared_stem_drop_V=(iq56 + ir16) * stem_R, maximum_partial_drop_V=max(r['partial_total_V'] for r in values))
    args.output.mkdir(exist_ok=False)
    (args.output / 'worker_snapshot.py').write_bytes(Path(__file__).read_bytes())
    receipt = dict(status='passed geometry-owned partial precision-rail sensitivity; full IR qualification not run',
        inputs={str(p): sha(p) for p in (args.gds, args.access, Path(__file__))}, source_count=24,
        heads=rows, native_precision_interface_arrays=interfaces, scenarios=scenarios,
        XR16_injection_A=ir16, shared_stem_Q56_plus_XR16_injection_A=iq56 + ir16,
        omitted=['M1 native head/electrode reference plane and spreading', 'finite generalVSS hub and all other injected currents',
                 'well/substrate and full model-boundary ownership', 'PVT and selfconsistent voltage-dependent current redistribution'],
        double_count_control='No native Cont or resistor head/body R added: unchanged R3CMC already has explicit per-end rc.',
        numerical_full_R='not run', adoption='not run', seed='not applicable')
    dump(args.output / 'summary.json', receipt)
    print(json.dumps({name: {k: v for k, v in row.items() if k not in ('per_source', 'rail_edges')}
                      for name, row in scenarios.items()}, indent=2))


if __name__ == '__main__':
    main()

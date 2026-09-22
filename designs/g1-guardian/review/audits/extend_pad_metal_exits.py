#!/usr/bin/env python3
"""Add parent-level pad exits; preserve stock cells and prove no new net merge."""
import argparse
import collections
import json
import os
from pathlib import Path
import pya
from audit_placed_decap_domains import physical, identity
from place_closed_analog import region, text_records, sha


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--parent', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    assert not a.output.exists() and len(os.sched_getaffinity(0)) == 1
    assert pya.__version__ == '0.30.9'
    metadata = json.loads((a.parent/'analysis.json').read_text())
    source = a.parent/'fullchip_instances_unrouted.gds'
    assert metadata['status'].startswith('passed') and sha(source) == metadata['GDS_sha256']
    a.output.mkdir(parents=True)
    (a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    layout = pya.Layout(); layout.read(str(source)); top = layout.top_cell()
    assert layout.dbu == .001
    before = {str(i): region(layout, top, i) for i in layout.layer_infos()}
    texts = text_records(layout, top)
    oldnet, oldlayers = physical(layout, top)
    pads = [i for i in top.each_inst() if i.cell.name.startswith('retained_fullchip_sg13g2_IOPad')]
    assert len(pads) == 24
    additions = collections.defaultdict(pya.Region)
    records = []
    for instance in pads:
        # PDK-native outward stub x=5..75, y=0..3 um; extend the
        # actual parent conductor to y=7 um as required by Pad.fR.
        trans = instance.trans
        pin = trans*pya.Point(40000, 1500)
        for layer in (126, 134):
            original = before[str(pya.LayerInfo(layer, 0))]
            stub = pya.Region(trans*pya.Box(5000, 0, 75000, 3000))
            assert (stub-original).is_empty(), (instance.cell.name, layer, 'missing native stub')
            box = trans*pya.Box(5000, 0, 75000, 7000)
            wanted = pya.Region(box)
            target = identity(oldnet, oldlayers[layer], [pin.x, pin.y])
            assert target is not None
            touched = []
            for polygon in original.interacting(wanted).each():
                point = next(polygon.each_point_hull())
                found = identity(oldnet, oldlayers[layer], [point.x, point.y])
                assert found is not None, (layer, str(point), 'off-metal boundary probe')
                if found != target:
                    diagnostic = dict(cell=instance.cell.name, transform=str(trans), layer=layer,
                                      proposed_box=str(box), target=list(target), found=list(found),
                                      tested_point=str(point), polygon=str(polygon),
                                      intersection=[str(q) for q in (pya.Region(polygon)&wanted).each()])
                    (a.output/'conflict.json').write_text(json.dumps(diagnostic, indent=2)+'\n')
                    raise AssertionError(diagnostic)
                touched.append(list(found))
            assert touched
            extra = wanted-original
            # No added metal may newly contact an old via cut whose old
            # backing was absent: otherwise a different layer could merge.
            for cut in ({126: (125, 133), 134: (133,)}[layer]):
                assert (extra & before[str(pya.LayerInfo(cut, 0))]).is_empty(), (layer, cut, 'new old-via contact')
            additions[layer] += wanted
            records.append(dict(cell=instance.cell.name, transform=str(trans), layer=layer,
                                bbox_dbu=[box.left, box.bottom, box.right, box.top],
                                original_net=list(target), touched_original_components=touched,
                                new_area_um2=extra.area()*1e-6))
    assert len(records) == 48
    # New exits are spatially separate. Existing common supplies may share an
    # original component, but no distinct old components can be merged.
    for index, row in enumerate(records):
        for other in records[index+1:]:
            if row['layer'] == other['layer'] and pya.Box(*row['bbox_dbu']).touches(pya.Box(*other['bbox_dbu'])):
                assert row['original_net'] == other['original_net']
    for layer, shapes in additions.items():
        for polygon in shapes.each():
            top.shapes(layout.layer(layer, 0)).insert(polygon)
    for info in layout.layer_infos():
        expected = before[str(info)] + additions[info.layer] if info.datatype == 0 and info.layer in additions else before[str(info)]
        assert (region(layout, top, info)^expected).is_empty()
    assert text_records(layout, top) == texts
    output = a.output/'pad_exit_extended.gds'; layout.write(str(output))
    saved = pya.Layout(); saved.read(str(output)); st = saved.top_cell()
    assert text_records(saved, st) == texts
    for info in layout.layer_infos():
        assert (region(saved, st, info)^region(layout, top, info)).is_empty()
    result = dict(status='passed scoped additive pad-exit geometry and no-old-net-merge proof',
                  GDS_sha256=sha(output), parent_GDS_sha256=sha(source), script_sha256=sha(Path(__file__)),
                  original_native_cells_geometry_and_texts='passed', saved_roundtrip='passed',
                  pad_cells=24, exit_rectangles=48, additions=records,
                  not_run=['stock main/maximal/density/antenna DRC', 'fullchip LVS/PEX/PDN/routes',
                           'current IR/EM and electrical adoption'],
                  not_applicable=['PDK cell or rule-deck modifications'])
    (a.output/'analysis.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k != 'additions'}, indent=2))


if __name__ == '__main__':
    main()

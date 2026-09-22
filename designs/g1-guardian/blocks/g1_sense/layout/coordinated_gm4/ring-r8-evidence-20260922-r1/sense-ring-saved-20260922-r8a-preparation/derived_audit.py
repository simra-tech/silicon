#!/usr/bin/env python3
"""Saved r6/r7 geometry delta, nine-port identity and global ring keepout."""
import argparse
import json
import os
from pathlib import Path
from build_native_prototypes import pya, snapshot, sha
from audit_power_ports_revision import read


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('candidate', 'prior', 'output'):
        p.add_argument('--' + name, type=Path, required=True)
    a = p.parse_args()
    assert os.sched_getaffinity(0) == {6} and not a.output.exists()
    ly, cell, manifest = read(a.candidate)
    pl, prior, pm = read(a.prior)
    assert pm['GDS_sha256'] == '9559f0d309f0c14d2f226e56138dfd0283cf2b847f0b536929565e4a739b9b02'
    changes = []
    for info in set(ly.layer_infos()) | set(pl.layer_infos()):
        left = pya.Region([pya.Polygon(x) for x in pya.Region(cell.begin_shapes_rec(ly.layer(info))).each()]).merged()
        right = pya.Region([pya.Polygon(x) for x in pya.Region(prior.begin_shapes_rec(pl.layer(info))).each()]).merged()
        delta = left ^ right
        if not delta.is_empty():
            assert info.datatype == 0 and info.layer in (50, 66, 67, 125, 126, 133, 134), info.to_s()
            changes.append(dict(layer=info.layer, added_um2=(left-right).area()*1e-6,
                                removed_um2=(right-left).area()*1e-6))
    def annotations(layout, top):
        rows = []
        for li in layout.layer_indexes():
            info = layout.get_info(li)
            if info.datatype in (2, 25):
                for shape in top.shapes(li).each():
                    rows.append((info.to_s(), shape.to_s()))
        return sorted(rows)
    assert annotations(ly, cell) == annotations(pl, prior)
    labels = []
    for li in ly.layer_indexes():
        info = ly.get_info(li)
        if info.datatype != 25:
            continue
        for shape in cell.shapes(li).each():
            if not shape.is_text():
                continue
            point = shape.text.trans.disp
            pin = pya.Region(cell.shapes(ly.layer(info.layer, 2))).interacting(pya.Region(pya.Box(point.x, point.y, point.x+1, point.y+1)))
            assert pin.count() == 1 and (pin-snapshot(cell, info.layer)).is_empty()
            b = pin.bbox()
            labels.append(dict(name=shape.text.string, layer=info.layer, pin_datatype=2,
                               label_datatype=25, point_um=[point.x*.001, point.y*.001],
                               bbox_um=[v*.001 for v in (b.left,b.bottom,b.right,b.top)]))
    assert len(labels) == 9 and len({r['name'] for r in labels}) == 9
    contexts = []
    for plate in snapshot(cell,36).each():
        for margin in (1500,5000):
            window = pya.Region(plate.bbox().enlarged(margin))
            for layer in (36,67,126,129):
                delta = (snapshot(cell,layer)^snapshot(prior,layer)) & window
                contexts.append(dict(plate_bbox=str(plate.bbox()),layer=layer,margin_um=margin*.001,XOR_um2=delta.area()*1e-6))
                if margin==1500:assert delta.is_empty(), contexts[-1]
    tm2 = snapshot(cell,134)
    tv2 = snapshot(cell,133)
    assert tm2.bbox().left >= 36160 and tv2.bbox().left >= 36160
    result = dict(status='passed saved ring-keepout and unchanged-port/native gate',
                  GDS_sha256=manifest['GDS_sha256'], prior_GDS_sha256=pm['GDS_sha256'],
                  script_sha256=sha(Path(__file__)), changes=changes, ports=sorted(labels,key=lambda r:r['name']),
                  MIM_context_XOR=contexts, native_Activ_Poly_Cont_XOR_um2=0,
                  TM2_min_local_x_um=tm2.bbox().left*.001, TopVia2_min_local_x_um=tv2.bbox().left*.001,
                  global_TM2_min_y_um=331+tm2.bbox().left*.001,
                  nearest_ring_top_y_um=362.16, ring_clearance_um=331+tm2.bbox().left*.001-362.16,
                  full_core_integration='not run', full_PEX='not run', current_margin='not run', adoption='not run')
    a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    main()

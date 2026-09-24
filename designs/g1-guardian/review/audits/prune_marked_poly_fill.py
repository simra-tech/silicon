#!/usr/bin/env python3
"""Remove only whole pure GatPoly-fill instances touched by stock GFil.d markers.

This is a design repair, not a deck edit. Functional geometry and all reachable
non-root definitions remain exact. Fresh full DRC/density/antenna are required.
"""
import argparse
from decimal import Decimal
import json
import os
from pathlib import Path
import re
import time
import xml.etree.ElementTree as ET
import pya
from place_closed_analog import region, sha
from prepare_digital_reroute_native_hierarchy import hierarchy, properties
from prune_reroute_context_fill import direct, protected


def marker_seeds(report):
    items = ET.parse(report).findall('.//items/item')
    assert len(items) == 3
    boxes = []
    for item in items:
        assert item.findtext('category') == "'GFil.d'"
        assert item.findtext('cell') == 'placed_core_NOT_CONNECTED_FULLCHIP'
        value, = [v.text for v in item.findall('values/value')]
        assert value.startswith('edge-pair: ')
        numbers = re.findall(r'-?\d+(?:\.\d+)?', value)
        assert len(numbers) == 8
        coordinates = [Decimal(n)*1000 for n in numbers]
        assert all(n == int(n) for n in coordinates)
        x1,y1,x2,y2 = map(int,coordinates[4:])
        # One-DBU probing box touches the reported filler edge; this is not
        # the physical clearance criterion, which remains the stock rule.
        boxes.append(pya.Box(min(x1,x2),min(y1,y2),max(x1,x2),max(y1,y2)).enlarged(1))
    return boxes


def payload(layout, cell):
    assert '_FILL_CELL' in cell.name and not list(cell.each_inst())
    rows = [(layout.get_info(li),s) for li in layout.layer_indexes() for s in cell.shapes(li).each()]
    assert len(rows) == 1 and not cell.properties()
    info, shape = rows[0]
    assert (info.layer,info.datatype) == (5,22)
    assert not shape.is_text() and not shape.properties()
    return shape.polygon


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['candidate','drc','output']:
        parser.add_argument('--'+name,type=Path,required=True)
    args = parser.parse_args()
    assert not args.output.exists() and len(os.sched_getaffinity(0)) == 1
    assert pya.__version__ == '0.30.9'
    source = args.candidate/'analog_pair_native.gds'
    metadata = args.candidate/'analysis.json'
    meta = json.loads(metadata.read_text())
    assert meta['status'] == 'passed isolated analog-pair hierarchy replacement'
    assert sha(source) == meta['GDS_sha256'] == 'be54644ebfffdc85bf4ed136966a31e60f374290b9ba7bd179753aa0b038d307'
    check = json.loads((args.drc/'summary.json').read_text())
    assert check['status'] == 'failed scoped candidate DRC' and check['GDS_sha256'] == sha(source)
    deck, = check['decks']; assert deck['name'] == 'main' and deck['returncode'] == 0
    report, = deck['reports']; assert report['categories'] == {"'GFil.d'":3}
    report_path = args.drc/report['path']; assert sha(report_path) == report['sha256']
    boxes = marker_seeds(report_path)
    inputs = {str(p):sha(p) for p in [source,metadata,args.drc/'summary.json',report_path,Path(__file__)]}
    args.output.mkdir(parents=True);(args.output/'source.py').write_bytes(Path(__file__).read_bytes())
    result = dict(status='running marked poly-fill repair',inputs=inputs,source_GDS_sha256=sha(source),
                  source_metadata_sha256=sha(metadata),not_run=['Fresh stock main/maximal/density/antenna',
                  'Terminal partition','Affected fill-dependent parasitics/electrical','Adoption'])
    started = time.monotonic()
    try:
        layout = pya.Layout();layout.read(str(source));top = layout.top_cell()
        assert layout.dbu == .001 and top.name == 'placed_core_NOT_CONNECTED_FULLCHIP'
        original = hierarchy(layout,top); roots = direct(layout,top); held = protected(top)
        bounds = top.bbox(); props = properties(top)
        fill_before = region(layout,top,pya.LayerInfo(5,22))
        removed = pya.Region(); ledger = []; coverage = [0]*len(boxes)
        for instance in list(top.each_inst()):
            if '_FILL_CELL' not in instance.cell.name:
                continue
            li = layout.find_layer(pya.LayerInfo(5,22))
            if li is None or instance.cell.shapes(li).is_empty():
                continue
            polygon = payload(layout,instance.cell); assert not instance.properties()
            selected = []; keep = []
            for transform in instance.cell_inst.each_cplx_trans():
                placed = polygon.transformed(transform)
                hits = [i for i,b in enumerate(boxes) if not (pya.Region(placed)&pya.Region(b)).is_empty()]
                if not hits:
                    keep.append(transform);continue
                for i in hits: coverage[i] += 1
                selected.append(dict(transform=str(transform),polygon=placed.to_s(),marker_indices=hits))
                removed.insert(placed)
            if not selected:
                continue
            ledger.append(dict(cell=instance.cell.name,original_array=str(instance.cell_inst),removed=selected,
                               retained_transforms=[str(t) for t in keep]))
            index = instance.cell_index;instance.delete()
            for transform in keep:top.insert(pya.CellInstArray(index,transform))
        assert ledger and all(coverage)
        assert direct(layout,top) == roots and protected(top) == held and properties(top) == props
        assert top.bbox() == bounds
        after = hierarchy(layout,top)
        assert all(original[name] == digest for name,digest in after.items() if name != top.name)
        fill_after = region(layout,top,pya.LayerInfo(5,22))
        assert (fill_after ^ (fill_before-removed)).is_empty()
        clean = pya.Layout();clean.dbu = layout.dbu;ct = clean.create_cell(top.name);ct.copy_tree(top)
        assert hierarchy(clean,ct) == after
        output = args.output/'poly_fill_pruned.gds';clean.write(str(output))
        saved = pya.Layout();saved.read(str(output));st = saved.top_cell()
        assert hierarchy(saved,st) == after and st.bbox() == bounds and saved.dbu == .001
        assert all(sha(Path(p)) == h for p,h in inputs.items())
        result.update(status='passed exact marked poly-fill pruning',GDS_sha256=sha(output),top_cell=top.name,
                      removed_repetitions=sum(len(row['removed']) for row in ledger),
                      removed_area_um2=removed.area()*1e-6,ledger=ledger,marker_coverage=coverage,
                      native_cell_definitions='passed all reachable non-root definitions including properties held',
                      functional_root_geometry='passed all direct shapes texts and nonfill instances held',
                      exact_single_top_roundtrip='passed')
    except Exception as exc:
        result.update(status='failed marked poly-fill repair',error=repr(exc));raise
    finally:
        result['wall_s'] = time.monotonic()-started
        (args.output/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__ == '__main__':
    main()

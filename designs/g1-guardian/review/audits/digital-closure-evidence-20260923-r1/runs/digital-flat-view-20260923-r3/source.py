#!/usr/bin/env python3
"""Prepare an independent flat LVS view without promoting cell-local pin labels.

Only descendant TEXT records are removed. Every top TEXT record and every
non-TEXT layer's physical area must equal the original recursive geometry.
The source GDS and source netlist remain immutable. This is not adoption.
"""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import time
import klayout.db as k
from fullchip_reference_closure.audit_reference import parse_verilog


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def text_records(layout, top):
    return sorted((layout.get_info(li).to_s(), s.text.to_s())
                  for li in layout.layer_indexes() for s in top.shapes(li).each()
                  if s.is_text())


def verify_geometry(source, original, derived, top):
    assert source.dbu == derived.dbu and original.bbox() == top.bbox()
    infos = {source.get_info(li).to_s():source.get_info(li) for li in source.layer_indexes()}
    assert set(infos) == {derived.get_info(li).to_s() for li in derived.layer_indexes()}
    checks = {}
    for name, info in infos.items():
        before_iter = original.begin_shapes_rec(source.find_layer(info))
        after_iter = top.begin_shapes_rec(derived.find_layer(info))
        # TEXT records are checked separately; Region's generic iterator may
        # otherwise represent text extents as boxes on annotation layers.
        before_iter.shape_flags = k.Shapes.SBoxes | k.Shapes.SPolygons | k.Shapes.SPaths
        after_iter.shape_flags = k.Shapes.SBoxes | k.Shapes.SPolygons | k.Shapes.SPaths
        before = k.Region(before_iter)
        after = k.Region(after_iter)
        delta = before ^ after
        assert delta.is_empty(), 'Physical layer changed: '+name
        checks[name] = dict(xor_area_dbu2=delta.area(), original_area_dbu2=before.area())
    assert text_records(source, original) == text_records(derived, top), 'Top TEXT changed'
    assert sum(1 for _ in top.each_inst()) == 0
    return checks


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ('gds', 'pnl', 'output'):
        p.add_argument('--'+key, type=Path, required=True)
    p.add_argument('--gds-sha256', required=True)
    p.add_argument('--pnl-sha256', required=True)
    a = p.parse_args()
    assert len(os.sched_getaffinity(0)) == 1 and not a.output.exists()
    assert sha(a.gds) == a.gds_sha256 and sha(a.pnl) == a.pnl_sha256
    a.output.mkdir(parents=True)
    (a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    record = dict(status='running', input_gds_sha256=a.gds_sha256,
                  input_pnl_sha256=a.pnl_sha256, not_run=['Stock LVS on derived view', 'Adoption'],
                  not_applicable=['Statistical seed'])
    start = time.monotonic()
    try:
        module, ports, _ = parse_verilog(a.pnl.read_text())
        source = k.Layout(); source.read(str(a.gds)); original = source.cell(module)
        assert original is not None and module == 'g1_digital' and len(ports) == 46
        derived = k.Layout(); derived.read(str(a.gds)); top = derived.cell(module)
        labels = [s.text.string for li in derived.layer_indexes()
                  for s in top.shapes(li).each() if s.is_text()]
        record['observed_top_label_counts'] = dict(Counter(labels))
        # Both supply ports are labelled on TM1 and TM2 in the source GDS.
        # Keep all48 records; this is46 distinct source ports, not48 ports.
        expected = Counter(ports); expected.update(('VDD', 'VSS'))
        assert Counter(labels) == expected, 'Top source port labels not exact46 plus dual-metal supply labels'
        for rail in ('VDD', 'VSS'):
            layers = [derived.get_info(li).to_s() for li in derived.layer_indexes()
                      for s in top.shapes(li).each() if s.is_text() and s.text.string == rail]
            assert sorted(layers) == ['126/25', '134/25'], (rail, layers)
        removed = []
        for cell in derived.each_cell():
            if cell.cell_index() == top.cell_index():
                continue
            for li in derived.layer_indexes():
                texts = [s for s in cell.shapes(li).each() if s.is_text()]
                for shape in texts:
                    removed.append(dict(cell=cell.name, layer=derived.get_info(li).to_s(),
                                        text=shape.text.to_s()))
                    shape.delete()
        assert removed
        top.flatten(-1, True)
        checks = verify_geometry(source, original, derived, top)
        output = a.output/'g1_digital.gds'; derived.write(str(output))
        reload = k.Layout(); reload.read(str(output))
        replay_checks = verify_geometry(source, original, reload, reload.cell(module))
        assert replay_checks == checks
        assert sha(a.gds) == a.gds_sha256 and sha(a.pnl) == a.pnl_sha256
        record.update(status='passed geometry-exact flat input with exact source top TEXT',
                      output_sha256=sha(output), layers=checks, source_ports=ports,
                      removed_descendant_text=removed,
                      top_text=text_records(source, original), saved_roundtrip=True)
    except Exception as exc:
        record.update(status='failed flat-view preparation', error=repr(exc))
        raise
    finally:
        record['wall_s'] = time.monotonic()-start
        (a.output/'summary.json').write_text(json.dumps(record, indent=2)+'\n')


if __name__ == '__main__':
    main()

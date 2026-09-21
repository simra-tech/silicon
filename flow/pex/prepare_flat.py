#!/usr/bin/env python3
"""Flatten a derived extraction view; prove all nontext polygons unchanged.

Child pin labels are removed to avoid shorting independent repeated-cell pins.
The source layout and top-level pin labels are retained unchanged.
"""
import argparse, hashlib, json
from pathlib import Path
import klayout.db as kdb

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument('--input', required=True, type=Path)
ap.add_argument('--cell', required=True)
ap.add_argument('--output', required=True, type=Path)
ap.add_argument('--report', required=True, type=Path)
a = ap.parse_args()
if a.output.exists() or a.report.exists():
    ap.error('refusing to overwrite evidence')
ly = kdb.Layout(); ly.read(str(a.input)); top = ly.cell(a.cell)
if top is None: ap.error('top cell missing')
layers = list(ly.layer_indices())
before = {i: kdb.Region(top.begin_shapes_rec(i)).merged() for i in layers}
removed = 0
for ci in top.called_cells():
    cell = ly.cell(ci)
    for i in layers:
        for shape in list(cell.shapes(i).each()):
            if shape.is_text():
                shape.delete(); removed += 1
top.flatten(True)
a.output.parent.mkdir(parents=True, exist_ok=True)
opts = kdb.SaveLayoutOptions(); opts.select_cell(top.cell_index())
ly.write(str(a.output), opts)
check = kdb.Layout(); check.read(str(a.output)); flat = check.cell(a.cell)
rows = []
for i in layers:
    info = ly.get_info(i); idx = check.find_layer(info)
    after = kdb.Region(flat.begin_shapes_rec(idx)).merged() if idx is not None else kdb.Region()
    delta = before[i] ^ after
    rows.append(dict(layer=info.to_s(), before_area_um2=before[i].area()*ly.dbu**2,
                     xor_area_um2=delta.area()*ly.dbu**2, xor_polygons=delta.count()))
passed = all(r['xor_polygons'] == 0 for r in rows) and flat.child_instances() == 0
report = dict(status='passed' if passed else 'failed', klayout_version=kdb.__version__,
              input=str(a.input), output=str(a.output), cell=a.cell, dbu_um=ly.dbu,
              input_sha256=hashlib.sha256(a.input.read_bytes()).hexdigest(),
              output_sha256=hashlib.sha256(a.output.read_bytes()).hexdigest(),
              script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              removed_child_texts=removed, layers=rows,
              scope='Merged nontext geometry identity; child labels intentionally removed; not LVS or DRC.')
a.report.parent.mkdir(parents=True, exist_ok=True)
a.report.write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report, indent=2))
if not passed: raise SystemExit(1)

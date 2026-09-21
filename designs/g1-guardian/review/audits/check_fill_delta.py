#!/usr/bin/env python3
"""Verify fill cleanup changes only removed datatype-22 geometry, never drawings."""
import argparse
import hashlib
import json
from pathlib import Path
import pya

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('before',type=Path)
p.add_argument('after',type=Path)
p.add_argument('report',type=Path)
p.add_argument('--top',default='g1_chip_top')
a=p.parse_args()
if a.report.exists():raise FileExistsError('Preserve prior comparison evidence')
layouts=[]
for path in (a.before,a.after):
    layout=pya.Layout();layout.read(str(path));layouts.append(layout)
assert layouts[0].dbu==layouts[1].dbu
keys=sorted(set((l.get_info(i).layer,l.get_info(i).datatype) for l in layouts for i in l.layer_indexes()))
rows=[]
for layer,datatype in keys:
    regions=[pya.Region(l.cell(a.top).begin_shapes_rec(l.layer(layer,datatype))).merged() for l in layouts]
    removed,added=regions[0]-regions[1],regions[1]-regions[0]
    if removed.is_empty() and added.is_empty():continue
    rows.append({'layer':layer,'datatype':datatype,'removed_polygons':removed.count(),'added_polygons':added.count(),
                 'removed_area_um2':removed.area()*layouts[0].dbu**2,'added_area_um2':added.area()*layouts[0].dbu**2})
passed=bool(rows) and all(r['datatype']==22 and r['layer'] in (1,5,8) and r['added_polygons']==0 for r in rows)
data={'status':'passed' if passed else 'failed','scope':'All-layer merged polygon delta; text labels are not compared',
      'before':str(a.before),'after':str(a.after),'before_sha256':hashlib.sha256(a.before.read_bytes()).hexdigest(),
      'after_sha256':hashlib.sha256(a.after.read_bytes()).hexdigest(),'klayout_version':pya.__version__,'changed_layers':rows}
a.report.write_text(json.dumps(data,indent=2)+'\n')
print(json.dumps(data,indent=2))
raise SystemExit(0 if passed else 1)

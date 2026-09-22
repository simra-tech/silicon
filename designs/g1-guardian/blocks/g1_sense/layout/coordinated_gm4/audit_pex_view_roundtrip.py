#!/usr/bin/env python3
"""Read-only XOR investigation of merged flattening and GDS round-trip."""
import argparse,hashlib,json,os
from pathlib import Path
import pya
p=argparse.ArgumentParser()
for k in('before','after','output'):p.add_argument('--'+k,type=Path,required=True)
a=p.parse_args();assert not a.output.exists() and len(os.sched_getaffinity(0))==1 and pya.__version__=='0.30.9';layouts=[]
for path in(a.before,a.after):
    ly=pya.Layout();ly.read(str(path));layouts.append(ly)
rows=[]
def materialize(region):
    result=pya.Region()
    for polygon in region.each():result.insert(pya.Polygon(polygon))
    return result
for info in layouts[0].layer_infos():
    if info.datatype in(2,25):continue
    regions=[pya.Region(ly.cell('g1_sense_physical').begin_shapes_rec(ly.layer(info)))for ly in layouts];raw=regions[0]^regions[1];merged=regions[0].merged()^regions[1].merged();initial_empty=[raw.is_empty(),merged.is_empty()]
    flat=materialize(materialize(regions[0])^materialize(regions[1]))
    if not all(initial_empty)or not flat.is_empty():rows.append(dict(layer=info.layer,datatype=info.datatype,initial_empty_flags=initial_empty,raw_XOR_um2=raw.area()*1e-6,merged_XOR_um2=merged.area()*1e-6,raw_count=raw.count(),merged_count=merged.count(),materialized_count=flat.count(),materialized_XOR_um2=flat.area()*1e-6,materialized_empty=flat.is_empty(),materialized_boxes=[str(poly.bbox())for poly in flat.each()][:10]))
result=dict(status='passed materialized polygon XOR0'if all(r['materialized_empty']for r in rows)else'failed geometric roundtrip XOR',rows=rows,before_sha256=hashlib.sha256(a.before.read_bytes()).hexdigest(),after_sha256=hashlib.sha256(a.after.read_bytes()).hexdigest(),script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

#!/usr/bin/env python3
"""Flatten only hierarchy, preserving all native/device/port text and polygons."""
import argparse,hashlib,json
from pathlib import Path
import pya
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def region(c,l):return pya.Region(c.begin_shapes_rec(l)).merged()
def texts(c):
 ly=c.layout();rows=[]
 for i in ly.layer_indices():
  it=c.begin_shapes_rec(i)
  while not it.at_end():
   if it.shape().is_text():
    t=it.shape().text;rows.append((ly.get_info(i).to_s(),t.string,str(it.trans()*t.trans)))
   it.next()
 return sorted(rows)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--input',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--report',type=Path,required=True);a=ap.parse_args()
 assert not a.output.exists() and not a.report.exists() and pya.__version__=='0.30.9'
 ly=pya.Layout();ly.read(str(a.input));top=ly.cell('g1_bgr');assert top
 original=sha(a.input);native_text=texts(top);before={ly.get_info(i).to_s():region(top,i) for i in ly.layer_indices()}
 top.flatten(True);assert top.child_instances()==0
 ly.write(str(a.output));saved=pya.Layout();saved.read(str(a.output));cell=saved.cell('g1_bgr');rows=[]
 for i in ly.layer_indices():
  info=ly.get_info(i);delta=before[info.to_s()]^region(cell,saved.layer(info));rows.append(dict(layer=info.to_s(),xor_polygons=delta.count(),xor_area_dbu2=delta.area()))
 passed=all(r['xor_polygons']==0 for r in rows) and texts(cell)==native_text and sha(a.input)==original
 result=dict(status='passed' if passed else'failed',input_sha256=original,output_sha256=sha(a.output),native_text_count=len(native_text),text_exact=texts(cell)==native_text,
             polygon_layers=rows,script_sha256=sha(Path(__file__)),modifications='Hierarchy flattening only; all native text and polygons retained.')
 a.report.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='polygon_layers'},indent=2));return 0 if passed else 1
if __name__=='__main__':raise SystemExit(main())

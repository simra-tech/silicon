"""Read-only report inventory with explicit identity-transform proof; no waiver."""
import argparse,collections,hashlib,json,re,xml.etree.ElementTree as ET
from pathlib import Path
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def summarize(path):
 tree=ET.parse(path);top='placed_core_NOT_CONNECTED_FULLCHIP'
 for cell in tree.findall('./cells/cell'):
  name=cell.findtext('name');refs=cell.findall('./references/ref')
  if name==top:assert not refs
  else:
   assert name=='new_signal_routes' and len(refs)==1
   assert refs[0].findtext('parent')==top and refs[0].findtext('trans')=='r0 *1 0,0'
 counts=collections.Counter();unique={}
 for item in tree.findall('./items/item'):
  category=item.findtext('category').strip("'");cell=item.findtext('cell');values=tuple(v.text for v in item.findall('./values/value'))
  assert cell in [top,'new_signal_routes'];counts[category,cell]+=1
  points=[]
  for v in values:
   assert v.startswith('edge-pair:');nums=[float(s) for s in re.findall(r'-?\d+(?:\.\d+)?',v)]
   assert len(nums)==8;points+=list(zip(nums[::2],nums[1::2]))
  key=(category,values)
  if key not in unique:unique[key]=dict(category=category,values=values,cells=[],bbox_um=[min(x for x,y in points),min(y for x,y in points),max(x for x,y in points),max(y for x,y in points)])
  unique[key]['cells'].append(cell)
 return dict(status='passed read-only exact report inventory; all DRC failures retained',report_sha256=sha(path),
  reported_markers=sum(counts.values()),counts=[dict(category=c,cell=n,count=v) for (c,n),v in sorted(counts.items())],
  distinct_report_values=list(unique.values()),scope='Identity transform proved for both report cells. Duplicate text inventory is diagnostic, not marker suppression or physical acceptance.')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--report',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
 result=summarize(a.report);a.output.write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(result['counts'],indent=2))
 for category in sorted({r['category'] for r in result['distinct_report_values']}):
  rows=[r for r in result['distinct_report_values'] if r['category']==category]
  print(category,len(rows),'distinct reported edge pairs; first12:',json.dumps(rows[:12]))

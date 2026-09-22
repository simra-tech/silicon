#!/usr/bin/env python3
"""Read-only source-node attribution of all336 MOS W/L and junction fields."""
import argparse,collections,hashlib,json,os,sys
from decimal import Decimal
from pathlib import Path
import pya
HERE=Path(__file__).resolve().parent
SOURCE=HERE.parent.parent/'sim/qualification/candidates/bgr_loop24_qref4_r253p465_hv06/bgr_loop24_qref4_r253p465_hv06.spice'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def number(v):
 factors={'u':Decimal('1e-6'),'p':Decimal('1e-12'),'n':Decimal('1e-9')}
 return Decimal(v[:-1])*factors[v[-1]] if v[-1] in factors else Decimal(v)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--stock',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
 assert not a.output.exists() and pya.__version__=='0.30.9' and len(os.sched_getaffinity(0))==1
 assert sha(SOURCE)=='586ffb58b6af31c77a2e7cbcb83b173ffa4713ec62401da30901c5a7e606283b'
 summary=json.loads((a.stock/'summary.json').read_text());assert summary['status']=='passed'
 paths=list((a.stock/'reports').glob('*.lvsdb'));assert len(paths)==1;path=paths[0];original=sha(path)
 expected={};count=0
 for l in SOURCE.read_text().splitlines():
  if not l.startswith('XM'):continue
  f=l.split();d,g,s,b=f[1:5];p=dict(x.split('=') for x in f[6:]);assert set(p)=={'l','w','as','ad','ps','pd','rfmode'} and p['rfmode']=='0'
  key=(f[5],float(number(p['l'])*Decimal('1e6')),g,b,tuple(sorted((d,s))))
  row=expected.setdefault(key,dict(instances=[],W=0.,junctions=collections.defaultdict(lambda:[0.,0.])))
  row['instances'].append(f[0]);row['W']+=float(number(p['w'])*Decimal('1e6'));count+=1
  for net,area,perim in ((s,'as','ps'),(d,'ad','pd')):
   row['junctions'][net][0]+=float(number(p[area])*Decimal('1e12'));row['junctions'][net][1]+=float(number(p[perim])*Decimal('1e6'))
 assert count==336 and len(expected)==20
 db=pya.LayoutVsSchematic();db.read(str(path));xr=db.xref();cps=list(xr.each_circuit_pair());assert len(cps)==1;cp=cps[0]
 assert cp.status()==pya.NetlistCrossReference.Match
 netmap={}
 for p in xr.each_net_pair(cp):
  assert p.status()==pya.NetlistCrossReference.Match;netmap[p.first().name]=p.second().name.lower()
 rows=[];seen=set()
 for pair in xr.each_device_pair(cp):
  assert pair.status()==pya.NetlistCrossReference.Match;dev=pair.first();cls=dev.device_class()
  if cls.name not in('sg13_hv_nmos','sg13_hv_pmos'):continue
  terminals={t.name:netmap[dev.net_for_terminal(t.id).name] for t in cls.terminal_definitions()}
  values={k:dev.parameter(k) for k in('L','W','AS','AD','PS','PD')}
  key=(cls.name,round(values['L'],8),terminals['G'],terminals['B'],tuple(sorted((terminals['D'],terminals['S']))))
  assert key in expected and key not in seen,key;seen.add(key);wanted=expected[key]
  actual=collections.defaultdict(lambda:[0.,0.])
  for term,area,perim in(('S','AS','PS'),('D','AD','PD')):
   actual[terminals[term]][0]+=values[area];actual[terminals[term]][1]+=values[perim]
  delta={'W':values['W']-wanted['W']}
  for net in wanted['junctions']:
   for i,n in enumerate(('area_um2','perimeter_um')):delta[net+'/'+n]=actual[net][i]-wanted['junctions'][net][i]
  rows.append(dict(model=cls.name,source_instances=wanted['instances'],source_nodes=terminals,extracted=values,
                   source_W_um=wanted['W'],source_junctions_by_net=dict(wanted['junctions']),actual_junctions_by_net=dict(actual),
                   deltas=delta,status='passed' if all(abs(v)<1e-7 for v in delta.values()) else'failed'))
 assert len(rows)==20 and seen==set(expected);unchanged=sha(path)==original
 result=dict(status='passed' if unchanged and all(r['status']=='passed' for r in rows) else'failed',source_MOS_count=count,combined_groups=len(rows),rows=rows,
             source_sha256=sha(SOURCE),stock_database_sha256=original,stock_summary_sha256=sha(a.stock/'summary.json'),script_sha256=sha(Path(__file__)),
             database_unchanged=unchanged,model_applicability_and_electrical='not run; exact geometry fields do not establish model scope or electrical performance')
 a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='rows'},indent=2));return 0 if result['status']=='passed' else 1
if __name__=='__main__':
 try:raise SystemExit(main())
 except Exception as e:
  if '--output' in sys.argv:
   p=Path(sys.argv[sys.argv.index('--output')+1])
   if not p.exists():p.write_text(json.dumps(dict(status='failed',error=repr(e),script_sha256=sha(Path(__file__))),indent=2)+'\n')
  raise

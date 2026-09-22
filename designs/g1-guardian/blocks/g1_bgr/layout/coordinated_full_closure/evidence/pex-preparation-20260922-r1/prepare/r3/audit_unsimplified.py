#!/usr/bin/env python3
"""Require exact extracted instances and source-node/device field parity."""
import collections,hashlib,json
from decimal import Decimal
from pathlib import Path
import pya
HERE=Path(__file__).resolve().parent
SOURCE=HERE.parent.parent/'sim/qualification/candidates/bgr_loop24_qref4_r253p465_hv06/bgr_loop24_qref4_r253p465_hv06.spice'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def num(s):
 scales={'u':1e-6,'p':1e-12,'n':1e-9}
 return float(s[:-1])*scales[s[-1]] if s[-1] in scales else float(s)
def audit(path,output,grounded_proof=None):
 assert not output.exists() and sha(SOURCE)=='586ffb58b6af31c77a2e7cbcb83b173ffa4713ec62401da30901c5a7e606283b'
 source={l.split()[0][2:].lower():l for l in SOURCE.read_text().splitlines() if l.startswith(('XM','XR','XQ'))};assert len(source)==1036
 omitted=set()
 if grounded_proof is not None:
  assert sha(grounded_proof)=='0d146e08578604904e2cde5cb0af641d6c5b8ffbe1ed9d8a0c566ee6edf7ba67'
  proof=json.loads(grounded_proof.read_text());assert proof['status']=='passed'
  omitted={l.split()[0][2:].lower() for l in proof['source_lines']};assert omitted=={'55','57','58','59','61','63','64','65','66'}
  for name in omitted:assert source[name] in proof['source_lines']
  source={name:line for name,line in source.items() if name not in omitted};assert len(source)==1027
 db=pya.LayoutVsSchematic();db.read(str(path));xr=db.xref();cps=list(xr.each_circuit_pair());assert len(cps)==1;cp=cps[0];assert cp.status()==pya.NetlistCrossReference.Match
 mapping={}
 for pair in xr.each_net_pair(cp):
  assert pair.status()==pya.NetlistCrossReference.Match;mapping[pair.first().name]=pair.second().name.lower()
 seen=set();rows=[]
 for pair in xr.each_device_pair(cp):
  assert pair.status()==pya.NetlistCrossReference.Match;name=pair.second().name.lower();assert name in source and name not in seen;seen.add(name)
  line=source[name];f=line.split();dev=pair.first();cls=dev.device_class();nt={t.name:mapping[dev.net_for_terminal(t.name).name] for t in cls.terminal_definitions()}
  values={p.name:dev.parameter(p.name) for p in cls.parameter_definitions()};deltas={};topology=False
  if f[0].startswith('XM'):
   params=dict(x.split('=') for x in f[6:]);assert cls.name==f[5]
   topology=nt['G']==f[2] and nt['B']==f[4] and sorted((nt['D'],nt['S']))==sorted((f[1],f[3]))
   for k in('l','w'):deltas[k]=values[k.upper()]-num(params[k])*1e6
   deltas['rfmode']=values['rfmode']-num(params['rfmode'])
   actual=collections.defaultdict(lambda:[0.,0.]);expected=collections.defaultdict(lambda:[0.,0.])
   for net,ak,pk in((nt['S'],'AS','PS'),(nt['D'],'AD','PD')):
    actual[net][0]+=values[ak];actual[net][1]+=values[pk]
   for net,ak,pk in((f[1],'ad','pd'),(f[3],'as','ps')):
    expected[net][0]+=num(params[ak])*1e12;expected[net][1]+=num(params[pk])*1e6
   for net,values_by_net in expected.items():
    deltas[net+'/area']=actual[net][0]-values_by_net[0];deltas[net+'/perimeter']=actual[net][1]-values_by_net[1]
  elif f[0].startswith('XQ'):
   params=dict(x.split('=') for x in f[6:]);assert cls.name==f[5]
   topology=all(nt[k]==v for k,v in zip(('C','B','E','S'),f[1:5]))
   for k in('we','le'):deltas[k]=values[k]-num(params[k])*1e6
   for k in('Nx','m'):deltas[k]=values[k]-num(params[k])
  else:
   params=dict(x.split('=') for x in f[5:]);assert cls.name==f[4]
   topology=sorted((nt[cls.name+'_1'],nt[cls.name+'_2']))==sorted(f[1:3]) and nt[cls.name+'_sub']==f[3]
   for k in('w','l'):deltas[k]=values[k]-num(params[k])*1e6
   for k in('b','m'):deltas[k]=values[k]-num(params[k])
  rows.append(dict(source_instance=f[0],source_line=line,model=cls.name,terminals=nt,extracted_fields=values,deltas=deltas,
                   status='passed' if topology and all(abs(v)<1e-7 for v in deltas.values()) else'failed',source_node_topology=topology))
 assert seen==set(source)
 result=dict(status='passed' if all(r['status']=='passed' for r in rows) else'failed',instance_count=len(rows),model_counts=dict(collections.Counter(r['model'] for r in rows)),
             net_map=mapping,rows=rows,source_sha256=sha(SOURCE),database_sha256=sha(path),script_sha256=sha(Path(__file__)),
             coverage='1027 extracted + 9 geometrically verified grounded dummies' if omitted else '1036 extracted',
             omitted_extraction_only_ids=sorted(omitted),grounded_proof_sha256=sha(grounded_proof) if grounded_proof else None,
             model_applicability_electrical='not run; device geometry fields and connectivity only')
 output.write_text(json.dumps(result,indent=2)+'\n');return result

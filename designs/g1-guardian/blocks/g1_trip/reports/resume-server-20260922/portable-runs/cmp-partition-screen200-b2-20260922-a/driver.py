#!/usr/bin/env python3
"""Frozen comparator samples in bounded individual-temperature leaves; retain attempts."""
import argparse,json,re,subprocess,sys
from pathlib import Path
from result_directory import allocate_run
SIM=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--run-id',required=True);p.add_argument('--image-id',required=True);p.add_argument('--seeds',required=True);p.add_argument('--reuse-campaign');p.add_argument('--resume',action='store_true');p.add_argument('--source-sha256',help='Require frozen comparator extraction bytes in every newly launched leaf');a=p.parse_args();out=SIM/'qualification'/a.run_id
for leaf in ['cmp-temperature-partition-pilot-20260922-a-p00','cmp-temperature-partition-pilot-20260922-a-p01']:
 assert json.loads((SIM/'qualification'/leaf/'partition_comparison.json').read_text())['status']=='passed','Partition qualification incomplete'
if a.resume:assert out.is_dir()
else:
 out=allocate_run(SIM,a.run_id);(out/'driver.py').write_text(Path(__file__).read_text());(out/'provenance.json').write_text(json.dumps({'arguments':sys.argv[1:],'scope':'Tighttrap cellPEX0.75V commonmode, full401staircase/temperature, same seeded circuit in individual300s bounded processes. Qualified temperature partition, not identical multi-analysis deck. Complete cases may be referenced from preserved incomplete attempts; original failures stay in their raw directories.','partition_qualification':['cmp-temperature-partition-pilot-20260922-a-p00','cmp-temperature-partition-pilot-20260922-a-p01']},indent=2)+'\n')
old={};old_dir=None
if a.reuse_campaign:
 old_dir=SIM/'qualification'/a.reuse_campaign;old={r['seed']:r for r in json.loads((old_dir/'summary.json').read_text())}
summary=[]
def persist():(out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
def identity(d,seed):
 pr=json.loads((d/'provenance.json').read_text());return {'image':pr['image_id'],'pdk':pr['pdk_commit'],'engine':pr['ngspice'],'models':pr['model_hashes'],'source':(d/'cmp.spice').read_text(),'circuit':(d/f'seed{seed}.cir').read_text().split('.control')[0].replace(d.name,'@RUN@'),'tran_commands':sorted(set(re.findall(r'^tran .+$',(d/f'seed{seed}.cir').read_text(),re.M)))}
for seed in map(int,a.seeds.split(',')):
 sample={'seed':seed,'status':'running','watchdog_status':'partitioned','wall_s':0,'wall_s_scope':'new leaves only; original attempt cost separately retained','fingerprints':[],'frozen_fingerprints':False,'cases':[],'case_evidence':[],'original_attempts':[]};summary.append(sample);fp=None;source=None
 if seed in old:sample['original_attempts'].append({'campaign':a.reuse_campaign,'status':old[seed]['status'],'wall_s':old[seed]['wall_s']})
 for ti,temp in enumerate([25.,-40.,125.]):
  leaf=f'{a.run_id}-s{seed}-t{ti}';d=SIM/'qualification'/leaf;reuse=None
  if seed in old:
   for j,c in enumerate(old[seed]['cases']):
    if c['temp_C']==temp and c['average_CM_V']==.75 and c['status']=='passed' and j<len(old[seed]['fingerprints']) and len(old[seed]['fingerprints'][j])==32:reuse=(j,c);break
  if reuse:
   j,case=reuse;d=old_dir;params=old[seed]['fingerprints'][j];case_wall=0;kind='preserved completed case from original attempt';rawstatus=old[seed]['status']
  else:
   cmd=[sys.executable,str(SIM/'run_cmp_qualification.py'),'--run-id',leaf,'--image-id',a.image_id,'--seeds',str(seed),'--temps',str(temp),'--cm','.75','--maxstep-ns','.2','--tight-trap','--netlist','cell-pex']
   if a.source_sha256:cmd+=['--source-sha256',a.source_sha256]
   if a.resume and d.exists():
    assert json.loads((d/'provenance.json').read_text())['arguments']==cmd[2:];assert (d/'summary.json').exists(),'Incomplete leaf needs explicit recovery'
   else:
    if (out/'PAUSE_REQUESTED').exists():sample['next_command']=cmd[2:];persist();sys.exit(0)
    subprocess.run(cmd,cwd=SIM)
   raw=json.loads((d/'summary.json').read_text())[0];case=raw['cases'][0];params=raw['fingerprints'][0] if raw['fingerprints'] else [];case_wall=raw['wall_s'];kind='new individual-temperature leaf';rawstatus=raw['status']
  observed=identity(d,seed)
  if source is None:source=observed
  if fp is None:fp=params
  valid=case['status']=='passed' and len(params)==32 and params==fp and source==observed
  sample['wall_s']+=case_wall;sample['cases'].append(case);sample['fingerprints'].append(params);sample['case_evidence'].append({'temperature_C':temp,'run':d.name,'case_tag':case['tag'],'kind':kind,'raw_attempt_status':rawstatus,'case_completion_and_frozen_source_sample_status':'passed' if valid else 'failed'})
  if not valid:sample['status']='failed/incomplete';persist();break
  persist()
 else:sample['status']='passed';sample['frozen_fingerprints']=True
 persist()

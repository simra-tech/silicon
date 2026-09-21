#!/usr/bin/env python3
"""Isolated unchanged vendor model checks against stated datasheet conditions.

These checks qualify parser behavior approximately, not device production limits.
"""
import argparse,datetime,hashlib,json,math,re,subprocess,sys,uuid
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[5]
sys.path.insert(0,str(HERE.parent));sys.path.insert(0,str(HERE.parents[2]/'g1_top/sim'))
from run_fet_campaign import MODEL_SHA
from run_bounded import run_bounded,atomic_json
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--model',type=Path,required=True);ap.add_argument('--image-id',required=True);ap.add_argument('--timeout',type=float,default=60);ap.add_argument('--method',choices=['trap','gear'],default='gear');a=ap.parse_args()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
if sha(a.model)!=MODEL_SHA:ap.error('vendor file hash mismatch')
out=HERE.parent/'campaigns'/('vendorcheck_'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid.uuid4().hex[:8]);out.mkdir(parents=True,exist_ok=False)
md=dict(options={k:str(v) if isinstance(v,Path) else v for k,v in vars(a).items()},model_sha256=sha(a.model),runner_sha256=sha(Path(__file__)),ngspice_version=subprocess.check_output(['ngspice','-v'],text=True),datasheet_url='https://www.ti.com/lit/ds/symlink/csd16340q3.pdf',datasheet_revision='SLPS247E, August2014, electrical characteristics page3',scope='Unchanged2010vendor transient model/parser validation against typical static/charge points, not worst-case tolerance/thermal/SOA qualification.')
cases=[]
for name,stim,control,vectors,typ,metric in [
 ('rds_2p5','Vg g 0 2.5\nId 0 d 20','op','v(d) v(g)',.0061,'Rds_ohm'),
 ('rds_4p5','Vg g 0 4.5\nId 0 d 20','op','v(d) v(g)',.0043,'Rds_ohm'),
 ('rds_8','Vg g 0 8\nId 0 d 20','op','v(d) v(g)',.0038,'Rds_ohm'),
 ('threshold','Vg g 0 .8\nVtie g d 0','dc Vg .5 1.2 .001','v(d) v(g) i(vtie)',.85,'Vth_V'),
 ('body_diode','Vg g 0 0\nId d 0 20','op','v(d) v(g)',.8,'Vsd_V'),
 ('charge','Ig 0 g pwl(0 0 1u 0 1.001u .001)\nRgate g 0 1e12\nVhold hold 0 pwl(0 1 .99u 1 .991u 0)\nSreset g 0 hold 0 reset\n.model reset SW(Ron=1 Roff=1e12 Vt=.5 Vh=.1)\nId 0 d 20\nBclamp d 0 I=max(0,(v(d)-12.5)/.001)','tran 1n 10u 0 1n','v(d) v(g)',6.5e-9,'Qg_4p5_C')]:
 wave=out/(name+'.tsv');deck=out/(name+'.cir')
 deck.write_text(f'''* Isolated vendor parser/model validation: {name}
.param ptrc1=3.25e-3 ptrc2=9.0e-6 pwidth=1.3392864 perim=2.7
.incpslt {a.model.resolve()}
.temp 25
.option method={a.method} reltol=1e-5 abstol=1e-13 vntol=1e-7
XFET d g 0 CSD16340Q3
{stim}
.control
set num_threads=1
set numdgt=15
set wr_singlescale
set wr_vecnames
{control}
wrdata {wave} {vectors}
quit
.endc
.end
''')
 with (out/(name+'.log')).open('x') as log:r=run_bounded(['ngspice','-b',str(deck)],log,out/(name+'.json'),a.timeout,cwd=out,metadata=dict(md,case=name,deck_sha256=sha(deck)),interval_s=5)
 result=dict(case=name,status=r['status'],completion='failed',electrical_acceptance='not run',wall_s=r['wall_s'])
 try:
  if r['status']!='completed' or re.search(r'Timestep too small|simulation aborted|doAnalyses:|^Error:',(out/(name+'.log')).read_text(),re.I|re.M):raise ValueError('solver incomplete/error')
  rows=[list(map(float,l.split())) for l in wave.read_text().splitlines()[1:] if l.strip()]
  if not rows or any(not all(map(math.isfinite,row)) for row in rows):raise ValueError('missing/nonfinite data')
  def crossing(idx,target):
   for p,q in zip(rows,rows[1:]):
    if p[idx]<=target<=q[idx] and q[idx]>p[idx]:return p[0]+(q[0]-p[0])*(target-p[idx])/(q[idx]-p[idx])
   raise ValueError('target not bracketed')
  if metric=='Rds_ohm':value=rows[-1][1]/20
  elif metric=='Vsd_V':value=-rows[-1][1]
  elif metric=='Vth_V':
   if abs(rows[-1][0]-1.2)>1e-9:raise ValueError('DC endpoint missing')
   value=crossing(3,250e-6)
  else:
   if abs(rows[-1][0]-10e-6)>1e-12:raise ValueError('transient endpoint missing')
   pre=min(rows,key=lambda r:abs(r[0]-1e-6))
   if abs(pre[2])>.01 or not 12.4<pre[1]<12.6:raise ValueError('gate-charge initial gate/drain bias not established')
   value=(crossing(2,4.5)-1.0005e-6)*.001
  result.update(completion='passed',metric=metric,simulated=value,datasheet_typical=typ,relative_difference=value/typ-1,wave_sha256=sha(wave),engineering_parser_check='Within20% of datasheet typical; this is a fixture acceptance assumption, not a datasheet production limit.',electrical_acceptance='passed' if abs(value/typ-1)<.2 else 'failed')
 except (OSError,ValueError) as e:result['error']=str(e).replace(str(ROOT)+'/', '')
 atomic_json(out/(name+'.acceptance.json'),result);cases.append(result);atomic_json(out/'campaign.json',dict(md,cases=cases));print(json.dumps(result),flush=True)
print(out)
if any(r['electrical_acceptance']!='passed' for r in cases):raise SystemExit(1)

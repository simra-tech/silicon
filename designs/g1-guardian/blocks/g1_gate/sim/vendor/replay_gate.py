#!/usr/bin/env python3
"""Diagnose the unchanged FET model using an ideal replay of observed terminal VGS.

This removes the IHP driver and its source impedance. It is an isolation test,
not a substitute for the failed coupled fixture or an accepted circuit waveform.
The final observed VGS is held through 8 us; the source can be a partial waveform.
"""
import argparse,bisect,datetime,hashlib,json,math,re,subprocess,sys,uuid
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[5]
sys.path.insert(0,str(HERE.parent));sys.path.insert(0,str(HERE.parents[2]/'g1_top/sim'))
from run_fet_campaign import MODEL_SHA
from run_bounded import run_bounded,atomic_json
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument('--model',type=Path,required=True);ap.add_argument('--source',type=Path,required=True)
 ap.add_argument('--image-id',required=True);ap.add_argument('--timeout',type=float,default=60)
 ap.add_argument('--temp',type=float,choices=[27,125],default=125)
 ap.add_argument('--drive',choices=['vgs','pad'],default='vgs',help='imposed terminalVGS or observed padvoltage driving the original22ohm/10kohm network')
 ap.add_argument('--resample-ps',type=float,default=100,help='finite PWL interval; avoid replaying collapsed solver timesteps')
 ap.add_argument('--accuracy',choices=['baseline','tight'],default='baseline');a=ap.parse_args()
 if sha(a.model)!=MODEL_SHA:ap.error('model SHA mismatch')
 cols,*lines=a.source.read_text().splitlines()
 if cols.split()[2]!='v(gfet,source)':ap.error('source VGS column unexpected')
 rows=[list(map(float,l.split())) for l in lines if l.strip()]
 if not rows or rows[0][0]!=0 or rows[-1][0]>=8e-6 or any(not all(map(math.isfinite,r)) for r in rows) or any(q[0]<=p[0] for p,q in zip(rows,rows[1:])):ap.error('invalid or unexpected source times')
 if not 10<=a.resample_ps<=1000:ap.error('resample interval must be10..1000ps')
 times=[r[0] for r in rows]
 def interp(t,ts,vs):
  j=max(1,min(len(ts)-1,bisect.bisect_left(ts,t)));k=(t-ts[j-1])/(ts[j]-ts[j-1])
  return vs[j-1]+k*(vs[j]-vs[j-1])
 step=a.resample_ps*1e-12
 rt=[i*step for i in range(int(times[-1]/step)+1)]
 if times[-1]-rt[-1]<step*.01:rt[-1]=times[-1]
 else:rt.append(times[-1])
 column=2 if a.drive=='vgs' else 1;source_values=[r[column] for r in rows]
 rv=[interp(t,times,source_values) for t in rt]
 replay_error=max(abs(r[column]-interp(r[0],rt,rv)) for r in rows)
 out=HERE.parent/'campaigns'/('vendor_replay_'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid.uuid4().hex[:8]);out.mkdir(exist_ok=False)
 tol='reltol=0.005 abstol=1e-9 vntol=1e-5 chgtol=1e-13' if a.accuracy=='baseline' else 'reltol=1e-5 abstol=1e-14 vntol=1e-7 chgtol=1e-14'
 pwl='\n+ '.join('%.17g %.17g'%(t,v) for t,v in zip(rt,rv))
 deck=out/'fixture.cir';wave=out/'wave.tsv'
 drive_nodes='gfet source' if a.drive=='vgs' else 'pad 0'
 gate_network='' if a.drive=='vgs' else 'Rgate pad gfet 22\nRpulldown gfet source 10k\n'
 deck.write_text(f'''* Vendor-only numerical isolation, ideal imposed observed VGS
.param ptrc1=3.25e-3 ptrc2=9.0e-6 pwidth=1.3392864 perim=2.7
.incpslt {a.model.resolve()}
.temp {a.temp}
.option method=gear itl4=100 {tol}
Vbus bus 0 5
Rload bus load 1.25
Lload load drain 100n
Vfet drain dfet 0
XFET dfet gfet source CSD16340Q3
Rsource source 0 35m
Dfly drain bus fixture_clamp
.model fixture_clamp D(is=1n n=1 rs=0.05 tt=10n cjo=50p bv=60)
{gate_network}Vdrive {drive_nodes} pwl({pwl}
+ 8u {rows[-1][column]:.17g})
.control
set num_threads=1
set numdgt=15
set wr_singlescale
set wr_vecnames
tran 1n 8u 0 1n
wrdata {wave} v(gfet,source) v(dfet,source) i(vfet) i(Lload) i(vdrive)
quit
.endc
.end
''')
 md=dict(options={k:str(v) if isinstance(v,Path) else v for k,v in vars(a).items()},source_wave=str(a.source.relative_to(ROOT)),source_sha256=sha(a.source),source_endpoint_s=rows[-1][0],model_sha256=sha(a.model),deck_sha256=sha(deck),runner_sha256=sha(Path(__file__)),ngspice_version=subprocess.check_output(['ngspice','-v'],text=True),scope=__doc__)
 md.update(replay_points=len(rt),max_source_reconstruction_error_V=replay_error,minimum_source_interval_s=min(q-p for p,q in zip(times,times[1:])))
 with (out/'run.log').open('x') as log:r=run_bounded(['ngspice','-b',str(deck)],log,out/'run.json',a.timeout,cwd=out,metadata=md)
 result=dict(solver_status=r['status'],wall_s=r['wall_s'],completion='not run to completion' if r['status']=='timeout' else 'failed',electrical_acceptance='not applicable: diagnostic replay')
 try:
  rr=[list(map(float,l.split())) for l in wave.read_text().splitlines()[1:] if l.strip()]
  if not rr or any(not all(map(math.isfinite,x)) for x in rr):raise ValueError('empty/nonfinite observations')
  result.update(observed_end_s=rr[-1][0],wave_sha256=sha(wave))
  bad=re.search(r'Timestep too small|simulation.*aborted|doAnalyses:|^Error:',(out/'run.log').read_text(),re.M|re.I)
  if r['status']=='completed' and not bad and abs(rr[-1][0]-8e-6)<1e-12:result['completion']='passed'
 except (OSError,ValueError) as e:result['error']=str(e).replace(str(ROOT)+'/', '')
 atomic_json(out/'assessment.json',result);print(out.relative_to(ROOT));print(json.dumps(result,indent=2))
 if result['completion']!='passed':raise SystemExit(1)
if __name__=='__main__':main()

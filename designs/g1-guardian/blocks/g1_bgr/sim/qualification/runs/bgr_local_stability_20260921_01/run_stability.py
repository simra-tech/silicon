#!/usr/bin/env python3
"""Two-injection local return-ratio diagnostic; does not assert global stability.
Method: Tian et al., IEEE Circuits & Devices Jan2001 eqs21–30.
Probe sign: Vprobe=e-f, Iprobe=0->e, if=-i(Vprobe).
All original DC connectivity is retained by zero-valued probe sources.
"""
import argparse,cmath,hashlib,json,math,re,shutil,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
PDK=Path('/foss/pdks/ihp-sg13g2')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read_data(p):
 with p.open() as f:next(f);rows=[list(map(float,l.split())) for l in f if l.strip()]
 assert rows and all(all(map(math.isfinite,r)) for r in rows)
 return rows
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--run-id',required=True);ap.add_argument('--image-id',required=True);ap.add_argument('--suite',choices=['anchor','bgr','pz'],required=True);ap.add_argument('--stop-file',type=Path);a=ap.parse_args()
 assert (PDK/'COMMIT').read_text().strip()=='84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
 out=HERE/'runs'/a.run_id;out.mkdir(parents=True,exist_ok=False);shutil.copy(__file__,out/'run_stability.py');shutil.copy(HERE/'.spiceinit',out/'.spiceinit');shutil.copy(HERE.parent/'postlayout/g1_bgr_pex.spice',out/'baseline.spice')
 manifest={'command':sys.argv,'image_id':a.image_id,'pdk_commit':(PDK/'COMMIT').read_text().strip(),'ngspice':subprocess.check_output(['ngspice','--version'],text=True),'source_sha256':{n:sha(out/n) for n in ['run_stability.py','.spiceinit','baseline.spice']},'model_sha256':{str(p.relative_to(PDK)):sha(p) for p in sorted((PDK/'libs.tech/ngspice/models').glob('*.lib'))},'method_source':'https://community.cadence.com/cfs-file/__key/communityserver-discussions-components-files/38/00900125_5F00_striving_5F00_for_5F00_small_5F00_signal_5F00_stability_5F00_circuits_5F00_devices_5F00_2001.pdf','scope':'Conditional local return ratio at one selected gate fanout. Other internal loops remain closed; no proof this cut breaks all feedback paths, no global PM/GM acceptance claim. Pole analysis separate if supported.','cases':[]}
 def save(): (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 def simulate(name,deck):
  (out/(name+'.cir')).write_text(deck);start=time.monotonic()
  with (out/(name+'.log')).open('w') as log:
   try:rc=subprocess.run(['ngspice','-b',name+'.cir'],cwd=out,stdout=log,stderr=subprocess.STDOUT,timeout=120).returncode;timed=False
   except subprocess.TimeoutExpired:rc=None;timed=True
  return {'name':name,'solver_exit':rc,'timed_out':timed,'wall_seconds':time.monotonic()-start,'deck_sha256':sha(out/(name+'.cir'))}
 cases=[('analytic','typ','tt','typ',3.3,27)] if a.suite=='anchor' else [(probe,h,m,r,v,t) for h,m,r,v,t in [('typ','tt','typ',3.3,27),('wcs','ss','wcs',3.0,-40),('bcs','ff','bcs',3.6,125)] for probe in (['pz'] if a.suite=='pz' else ['pbias','pcasc'])]
 save()
 for probe,h,m,r,v,t in cases:
  if a.stop_file and a.stop_file.exists():manifest['campaign_status']='paused at requested leaf boundary';save();break
  tag=f'{probe}_{h}_{m}_{r}_{v}_{t}';row={'name':tag,'probe':probe,'hbt':h,'mos':m,'res':r,'vdda':v,'temperature_C':t,'status':'not run','simulations':[]};manifest['cases'].append(row);save()
  if a.suite=='anchor':
   base='* Analytic bilateral feedback anchor\nRe e 0 1k\nRf f 0 500\nCf f 0 1n\nGforward f 0 e 0 .01\nGreverse e 0 f 0 .002\nVprobe e f dc 0 ac {pv}\nIprobe 0 e dc 0 ac {pi}\n';ev='v(e)';iv='-i(Vprobe)'
  else:
   text=(out/'baseline.spice').read_text();changed=[]
   if a.suite!='pz':
    lines=[]
    for line in text.splitlines():
     words=line.split()
     if line.startswith('XM') and words[2]==probe:changed.append(words[0]);words[2]='gate_probe';line=' '.join(words)
     if line.lower().startswith('.ends'):lines+=['Vprobe gate_probe '+probe+' dc 0 ac {pv}','Iprobe vss gate_probe dc 0 ac {pi}']
     lines.append(line)
    text='\n'.join(lines)+'\n';assert changed
   source=out/(tag+'.spice');source.write_text(text);row.update(changed_gate_pins=changed,probe_netlist_sha256=sha(source))
   base='* BGR local stability diagnostic\n'+''.join(f'.lib {PDK}/libs.tech/ngspice/models/{lib}.lib {corner}\n' for lib,corner in [('cornerHBT','hbt_'+h),('cornerMOShv','mos_'+m),('cornerRES','res_'+r)])
   base+=f'.include {source.name}\n.option gmin=1e-15 abstol=1e-14 reltol=1e-5 vntol=1e-7\n.temp {t}\n.global sub!\nVsub sub! 0 0\nVdd vdd 0 {v}\nVr4 r4 0 0\nXbgr vdd 0 r4 vref iptat pbias pcasc vbe dvbe g1_bgr\nVload iptat 0 1\nCload vref 0 1p\n';ev='v(xbgr.gate_probe)';iv='-i(v.xbgr.vprobe)'
  if a.suite=='pz':
   name=tag;deck=base+'.control\nset num_threads=1\nset numdgt=15\nop\nprint v(vref) v(pbias) v(pcasc)\npz vref 0 vref 0 cur pol\nprint all\nquit\n.endc\n.end\n';sim=simulate(name,deck);row['simulations'].append(sim);log=(out/(name+'.log')).read_text(errors='replace');row.update(status='not run' if sim['timed_out'] else 'failed',log_tail=log[-4000:]);save();continue
  datas={}
  for injection,pv,pi in [('voltage',1,0),('current',0,1)]:
   if a.stop_file and a.stop_file.exists():row['status']='not run';row['reason']='paused before next injection';break
   name=tag+'_'+injection
   deck=base+f'.param pv={pv} pi={pi}\n.control\nset num_threads=1\nset numdgt=15\nset wr_singlescale\nset wr_vecnames\nop\n'+('print v(vref) v(pbias) v(pcasc)\n' if a.suite!='anchor' else '')+'ac dec 100 1 1g\n'+f'let ifout={iv}\nlet ve={ev}\nwrdata {name}.dat real(ifout) imag(ifout) real(ve) imag(ve)\nquit\n.endc\n.end\n'
   sim=simulate(name,deck);row['simulations'].append(sim)
   try:
    log=(out/(name+'.log')).read_text(errors='replace');data=read_data(out/(name+'.dat'));assert sim['solver_exit']==0 and data[-1][0]>=.999e9 and all(len(x)==5 for x in data) and not re.search(r'(?im)^Error|Timestep too small|analysis aborted',log);datas[injection]=data
   except (OSError,AssertionError,ValueError):row['status']='not run' if sim['timed_out'] else 'failed';row['reason']='solver/data failure';save();break
  if len(datas)!=2:save();continue
  points=[]
  for vd,idata in zip(datas['voltage'],datas['current']):
   assert vd[0]==idata[0];f=vd[0];A=complex(*idata[1:3]);B=complex(*vd[1:3]);C=complex(*idata[3:5]);D=complex(*vd[3:5]);delta=A*D-B*C;den=1+A-D-2*delta;T=(2*delta-A+D)/den
   p={'frequency_Hz':f,'T_real':T.real,'T_imag':T.imag,'T_magnitude':abs(T),'T_phase_deg':math.degrees(cmath.phase(T)),'return_difference_magnitude':abs(1+T)}
   if a.suite=='anchor':p['relative_error']=abs(T-(.012/complex(.003,2*math.pi*f*1e-9)))/abs(.012/complex(.003,2*math.pi*f*1e-9))
   points.append(p)
  (out/(tag+'_return_ratio.json')).write_text(json.dumps(points,indent=2)+'\n');row.update(status='passed',frequency_points=len(points),low_frequency_return_ratio=[points[0]['T_real'],points[0]['T_imag']],minimum_return_difference_magnitude=min(p['return_difference_magnitude'] for p in points),maximum_return_ratio_magnitude=max(p['T_magnitude'] for p in points),global_stability_status='not run',gain_phase_margin_acceptance='not applicable to unqualified single-loop reduction')
  if a.suite=='anchor':row['maximum_relative_error']=max(p['relative_error'] for p in points);row['analytic_agreement_status']='passed' if row['maximum_relative_error']<1e-8 else 'failed'
  save();print(json.dumps(row),flush=True)
if __name__=='__main__':main()

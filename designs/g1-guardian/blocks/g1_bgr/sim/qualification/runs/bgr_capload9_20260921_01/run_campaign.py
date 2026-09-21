#!/usr/bin/env python3
"""Bounded, sequential BGR capacitance-PEX qualification/corner campaign.
Run in pinned container from this directory. Existing run directories are refused.
"""
import argparse, csv, hashlib, itertools, json, math, re, shutil, subprocess, time
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
PDK=Path('/foss/pdks/ihp-sg13g2')
MODELS=PDK/'libs.tech/ngspice/models'
PEX=HERE.parent/'postlayout/g1_bgr_pex.spice'
PIN='84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--run-id',required=True); ap.add_argument('--image-id',required=True); ap.add_argument('--suite',choices=['qualify','mc','corners','startup','stress','capload'],required=True); ap.add_argument('--samples',type=int,default=20); ap.add_argument('--seed-start',type=int,default=42001); a=ap.parse_args()
 assert (PDK/'COMMIT').read_text().strip()==PIN
 out=HERE/'runs'/a.run_id; out.mkdir(parents=True,exist_ok=False)
 shutil.copy(Path(__file__),out/Path(__file__).name)
 shutil.copy(HERE/'.spiceinit',out/'.spiceinit'); shutil.copy(PEX,out/'pex_nominal.spice')
 src=PEX.read_text(); (out/'pex_mm.spice').write_text('\n'.join(x+' mm_ok=1' if x.startswith(('XM','XQ','XR')) else x for x in src.splitlines())+'\n')
 manifest={'command':['python3','run_campaign.py',*__import__('sys').argv[1:]],'image_id':a.image_id,'pdk_commit':PIN,'git_commit':subprocess.check_output(['git','-c','safe.directory=/work','rev-parse','HEAD'],text=True).strip(),'ngspice':subprocess.check_output(['ngspice','--version'],text=True),'pex_sha256':sha(PEX),'runner_sha256':sha(Path(__file__)),'model_sha256':{str(p.relative_to(PDK)):sha(p) for p in sorted(MODELS.glob('*.lib'))},'osdi_sha256':{str(p.relative_to(PDK)):sha(p) for p in sorted((PDK/'libs.tech/ngspice/osdi').glob('*.osdi'))},'solver':'gmin=1e-15 abstol=1e-14 reltol=1e-5 vntol=1e-7','temperature_validity':'-40 to 125 C model range','fixture':'C-PEX standalone BGR; IPTAT at ideal 1 V; VREF 1 pF unless explicit cload_F; r4=0 except explicit mode-transition case. Stress fixtures are characterization, not actual downstream loads.','cases':[]}
 def run(name,hbt='typ',mos='tt',res='typ',vdd=3.3,seed=42001,mm=False,startup=None,reverse=False,stress=None,cload=1e-12,temperature=27):
  suffix='_mismatch' if mm else ''; libs=[('cornerHBT','hbt_'+hbt+suffix),('cornerMOShv','mos_'+mos+suffix),('cornerRES','res_'+res+suffix)]
  text='* G1_BGR standalone capacitance-PEX qualification\n'+''.join(f'.lib {MODELS}/{lib}.lib {corner}\n' for lib,corner in libs)+f'.include pex_{"mm" if mm else "nominal"}.spice\n.option seed={seed} gmin=1e-15 abstol=1e-14 reltol=1e-5 vntol=1e-7\n.global sub!\nVsub sub! 0 0\nVdd vdd 0 {vdd}\nVr4 r4 0 0\nXbgr vdd 0 r4 vref iptat pbias pcasc vbe dvbe g1_bgr\nVload iptat 0 1\nCload vref 0 1p\n.control\nset numdgt=15\nset wr_singlescale\nset wr_vecnames\n'
  fingerprint='print @n.xbgr.xm34.nsg13_hv_nmos[delvto] @n.xbgr.xr16.nr1[nsmm_rsh] @q.xbgr.xq56.qnpn13g2[area]\n'
  if stress:
   text+=f'set num_threads=1\noption temp={temperature}\n'
   if stress=='dip': text+='alter @vdd[pwl] = [ 0 3.3 5u 3.3 5.01u 1.8 10u 1.8 10.01u 3.3 40u 3.3 ]\n'
   elif stress=='r4': text+='alter @vr4[pwl] = [ 0 0 5u 0 5.01u 3.3 20u 3.3 20.01u 0 40u 0 ]\n'
   elif stress=='load': text=text.replace('Cload vref 0 1p\n','Cload vref 0 1p\nIstep vref 0 pwl(0 0 5u 0 5.01u 100n 20u 100n 20.01u 0 40u 0)\n')
   text+='tran 2n 40u\n'
  elif startup:
   temp,ramp=startup; stop=ramp*3
   text+=f'option temp={temp}\nalter @vdd[pwl] = [ 0 0 {ramp} {vdd} {stop} {vdd} ]\ntran {ramp/500} {stop} uic\n'
  else:
   text+='op\n'+fingerprint+('dc temp 125 -40 -5\n' if reverse else 'dc temp -40 125 5\n')+fingerprint
  text=text.replace('Cload vref 0 1p',f'Cload vref 0 {cload}')
  text+=f'wrdata {name}.dat v(vref) i(vload) i(vdd) v(vbe) v(dvbe) v(pbias) v(pcasc) v(xbgr.c2) v(xbgr.vbe3) v(xbgr.vd1) v(xbgr.vd2)\nquit\n.endc\n.end\n'
  (out/f'{name}.cir').write_text(text); start=time.monotonic(); timed=False
  with (out/f'{name}.log').open('w') as log:
   try: proc=subprocess.run(['ngspice','-b',f'{name}.cir'],cwd=out,stdout=log,stderr=subprocess.STDOUT,timeout=300 if (startup or stress) else 120); rc=proc.returncode
   except subprocess.TimeoutExpired: timed=True; rc=None
  row={'name':name,'hbt':hbt,'mos':mos,'res':res,'vdd':vdd,'seed':seed,'mm':mm,'startup':startup,'stress':stress,'cload_F':cload,'stress_temperature_C':temperature if stress else None,'watchdog_seconds':300 if (startup or stress) else 120,'timed_out':timed,'solver_exit':rc,'wall_seconds':time.monotonic()-start,'status':'not run' if timed else 'failed','completion':'timed out' if timed else 'solver or data failure','deck_sha256':sha(out/f'{name}.cir')}
  log=(out/f'{name}.log').read_text(errors='replace')
  row['fingerprints']=re.findall(r'@[^\s]+\s*=\s*([-+0-9.eE]+)',log)
  try:
   d=np.loadtxt(out/f'{name}.dat',skiprows=1); endpoint=40e-6 if stress else (startup[1]*3 if startup else (-40 if reverse else 125))
   if rc==0 and np.isfinite(d).all() and abs(d[-1,0]-endpoint)<(1e-12 if startup or stress else 1e-7) and not re.search(r'(?im)^Error|Timestep too small|analysis aborted',log):
    row.update(status='passed',completion='complete',vref_min=float(d[:,1].min()),vref_max=float(d[:,1].max()),iptat_min=float(d[:,2].min()),iptat_max=float(d[:,2].max()),current_max=float(-d[:,3].min()),hbt_vce_max=float(max(abs(d[:,4]).max(),abs(d[:,8]-d[:,5]).max(),abs(d[:,9]).max(),abs(d[:,10]-d[:,11]).max(),abs(d[:,11]).max())))
    if stress:
     row.update(vref_initial=float(d[0,1]),vref_end=float(d[-1,1]),relative_return_error_percent=float((d[-1,1]/d[0,1]-1)*100),characterization_acceptance="not applicable; stimulus characterization, no recovery budget adopted")
    elif not startup:
     order=np.argsort(d[:,0]); v25=float(np.interp(25,d[order,0],d[order,1])); row['vref25']=v25; row['tc_ppm_C']=(row['vref_max']-row['vref_min'])/v25/165*1e6; row['tc_status']='passed' if row['tc_ppm_C']<=50 else 'failed'
    else: row['vref_end']=float(d[-1,1]); row['startup_level_status']='passed' if .9<d[-1,1]<1.2 else 'failed'
  except (OSError,ValueError,IndexError): pass
  manifest['cases'].append(row); (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n'); print(json.dumps(row),flush=True)
 if a.suite=='qualify':
  run('enabled_a',mm=True); run('enabled_repeat',mm=True); run('enabled_seed2',mm=True,seed=42002); run('enabled_reverse',mm=True,reverse=True); run('disabled_a'); run('disabled_seed2',seed=42002)
 elif a.suite=='mc':
  for seed in range(a.seed_start,a.seed_start+a.samples): run(f'mc_{seed}',seed=seed,mm=True)
 elif a.suite=='corners':
  for h,m,r,v in itertools.product(['typ','bcs','wcs'],['tt','ff','ss'],['typ','bcs','wcs'],[3.0,3.3,3.6]): run(f'{h}_{m}_{r}_{v}',hbt=h,mos=m,res=r,vdd=v)
 elif a.suite=='startup':
  for h,m,r,t in [('typ','tt','typ',27),('wcs','ss','wcs',-40),('bcs','ff','bcs',125)]:
   for ramp in [.001,.1]: run(f'{h}_{m}_{r}_{t}_{ramp}',hbt=h,mos=m,res=r,vdd=3.0,startup=(t,ramp))
 elif a.suite=='capload':
  for h,m,r,t,v in [('typ','tt','typ',27,3.3),('wcs','ss','wcs',-40,3.0),('bcs','ff','bcs',125,3.6)]:
   for cap in [1e-13,1e-11,1e-10]:run(f'{h}_{m}_{r}_{t}_cap{cap:g}',hbt=h,mos=m,res=r,vdd=v,stress='load',cload=cap,temperature=t)
 else:
  for stress in ['dip','r4','load']:run(stress,stress=stress)
if __name__=='__main__': main()

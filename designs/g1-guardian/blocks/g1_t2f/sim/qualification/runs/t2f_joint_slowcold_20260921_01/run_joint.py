#!/usr/bin/env python3
"""Bounded joint BGR/T2F C-PEX transient; retains unique run and finite vectors."""
import argparse, hashlib, json, re, shutil, subprocess, time
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
BLOCKS=HERE.parents[2]
PDK=Path('/foss/pdks/ihp-sg13g2')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--run-id',required=True); ap.add_argument('--image-id',required=True); ap.add_argument('--temperatures',default='-40'); ap.add_argument('--tstop-us',type=float,default=32); ap.add_argument('--vdd',type=float,default=3.3); ap.add_argument('--vdd12',type=float,default=1.2); ap.add_argument('--hbt',choices=['typ','bcs','wcs'],default='typ'); ap.add_argument('--mos',choices=['tt','ss','ff'],default='tt'); ap.add_argument('--res',choices=['typ','bcs','wcs'],default='typ'); ap.add_argument('--cap',choices=['typ','bcs','wcs'],default='typ'); a=ap.parse_args()
 assert (PDK/'COMMIT').read_text().strip()=='84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
 out=HERE/'runs'/a.run_id; out.mkdir(parents=True,exist_ok=False)
 shutil.copy(Path(__file__),out/Path(__file__).name)
 files={'bgr.spice':BLOCKS/'g1_bgr/sim/postlayout/g1_bgr_pex.spice','t2f.spice':HERE.parent/'postlayout/g1_t2f_pex.spice','.spiceinit':HERE.parent/'.spiceinit'}
 for dest,src in files.items(): shutil.copy(src,out/dest)
 template=(HERE.parent/'postlayout/decks/ftemp_ptat_T-40.cir').read_text()
 manifest={'command':['python3','run_joint.py',*__import__('sys').argv[1:]],'image_id':a.image_id,'pdk_commit':(PDK/'COMMIT').read_text().strip(),'git_commit':subprocess.check_output(['git','-c','safe.directory=/work','rev-parse','HEAD'],text=True).strip(),'ngspice':subprocess.check_output(['ngspice','--version'],text=True),'runner_sha256':sha(Path(__file__)),'input_sha256':{dest:sha(src) for dest,src in files.items()},'models_sha256':{str(p.relative_to(PDK)):sha(p) for p in sorted((PDK/'libs.tech/ngspice/models').glob('*.lib'))},'temperature_validity':'-40 to 125 C model range','limitations':'Capacitance-only PEX; ideal IPTAT 1 V termination and 50 fF output; explicit per-case corners; no pad or joint MC.','cases':[]}
 for temp in map(float,a.temperatures.split(',')):
  name=f'ptat_T{temp:g}'; deck=template.replace('bandgap schematic view','bandgap C-PEX view').replace('.include ../../../../g1_bgr/xschem/g1_bgr.spice','.include bgr.spice').replace('.include ../g1_t2f_pex.spice','.include t2f.spice').replace('.temp -40',f'.temp {temp}').replace('Vdd vdd 0 dc 3.3',f'Vdd vdd 0 dc {a.vdd}').replace('Vdd12 vdd12 0 dc 1.2',f'Vdd12 vdd12 0 dc {a.vdd12}').replace('1.01u 3.3',f'1.01u {a.vdd}').replace('tran 5n 40u',f'tran 5n {a.tstop_us}u').replace('set filetype=ascii','set filetype=ascii\nset numdgt=15')
  deck=deck.replace(' hbt_typ',' hbt_'+a.hbt).replace(' mos_tt',' mos_'+a.mos).replace(' res_typ',' res_'+a.res).replace(' cap_typ',' cap_'+a.cap)
  vectors='v(fout) v(vref) i(vdd) i(vdd12) v(xt2f.cap1) v(xt2f.cap2) v(xt2f.ca1) v(xt2f.tail1) v(xt2f.cb1) v(xt2f.ca2) v(xt2f.tail2) v(xt2f.cb2)'
  deck=deck.replace('.endc',f'wrdata {name}.dat {vectors}\nquit\n.endc'); (out/f'{name}.cir').write_text(deck)
  start=time.monotonic(); timed=False
  with (out/f'{name}.log').open('w') as log:
   try: p=subprocess.run(['ngspice','-b',f'{name}.cir'],cwd=out,stdout=log,stderr=subprocess.STDOUT,timeout=300); rc=p.returncode
   except subprocess.TimeoutExpired: timed=True; rc=None
  log=(out/f'{name}.log').read_text(errors='replace'); measurements={k:float(v) for k,v in re.findall(r'(?m)^(\w+)\s*=\s*([-+0-9.eE]+)',log)}
  row={'name':name,'temperature_C':temp,'hbt':a.hbt,'mos':a.mos,'res':a.res,'cap':a.cap,'vdd':a.vdd,'vdd12':a.vdd12,'watchdog_seconds':300,'timed_out':timed,'solver_exit':rc,'wall_seconds':time.monotonic()-start,'status':'not run' if timed else 'failed','measurements':measurements,'deck_sha256':sha(out/f'{name}.cir')}
  try:
   d=np.loadtxt(out/f'{name}.dat',skiprows=1)
   if rc==0 and np.isfinite(d).all() and abs(d[-1,0]-a.tstop_us*1e-6)<1e-12 and all(k in measurements for k in ['freq','t_a','t_b','t_half_a','fout_hi','fout_lo']) and not re.search(r'(?im)^Error|Timestep too small|analysis aborted',log):
    row['status']='passed'; row['completed_tstop_s']=float(d[-1,0]); row['t2f_hbt_vce_max_V']=float(max(abs(d[:,7]-d[:,8]).max(),abs(d[:,9]-d[:,8]).max(),abs(d[:,10]-d[:,11]).max(),abs(d[:,12]-d[:,11]).max())); row['hbt_vce_status']='passed' if row['t2f_hbt_vce_max_V']<=1.6 else 'failed'
  except (OSError,ValueError,IndexError): pass
  manifest['cases'].append(row); (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n'); print(json.dumps(row),flush=True)
if __name__=='__main__': main()

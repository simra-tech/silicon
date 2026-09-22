#!/usr/bin/env python3
"""Bounded joint BGR/T2F adverse process/rail harness. Explicit PDK corner-mismatch libraries; must qualify frozen same-corner samples before MC."""
import argparse, hashlib, json, math, re, shutil, subprocess, time
from pathlib import Path
HERE=Path(__file__).resolve().parent
BLOCKS=HERE.parents[2]
PDK=Path('/foss/pdks/ihp-sg13g2')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--run-id',required=True); ap.add_argument('--image-id',required=True); ap.add_argument('--temperatures',default='-40'); ap.add_argument('--tstop-us',type=float,default=32); ap.add_argument('--vdd',type=float,default=3.3); ap.add_argument('--vdd12',type=float,default=1.2); ap.add_argument('--hbt',choices=['typ','bcs','wcs'],default='typ'); ap.add_argument('--mos',choices=['tt','ss','ff'],default='tt'); ap.add_argument('--res',choices=['typ','bcs','wcs'],default='typ'); ap.add_argument('--cap',choices=['typ','bcs','wcs'],default='typ'); ap.add_argument('--mismatch',action='store_true'); ap.add_argument('--seed',type=int,default=51001); ap.add_argument('--op-only',action='store_true'); ap.add_argument('--stop-file',type=Path); a=ap.parse_args()
 if a.mismatch:
  for library,section in [('cornerHBT','hbt_'+a.hbt),('cornerMOShv','mos_'+a.mos),('cornerMOSlv','mos_'+a.mos),('cornerRES','res_'+a.res),('cornerCAP','cap_'+a.cap)]:
   assert re.search(r'(?im)^\.lib\s+'+re.escape(section+'_mismatch')+r'\s*$',(PDK/'libs.tech/ngspice/models'/(library+'.lib')).read_text(encoding='latin1')), 'PDK does not expose requested corner mismatch section'
 assert (PDK/'COMMIT').read_text().strip()=='84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
 out=HERE/'runs'/a.run_id; out.mkdir(parents=True,exist_ok=False)
 shutil.copy(Path(__file__),out/Path(__file__).name)
 files={'bgr.spice':BLOCKS/'g1_bgr/sim/postlayout/g1_bgr_pex.spice','t2f.spice':HERE.parent/'postlayout/g1_t2f_pex.spice','.spiceinit':HERE.parent/'.spiceinit'}
 for dest,src in files.items(): shutil.copy(src,out/dest)
 if a.mismatch:
  for name in ['bgr.spice','t2f.spice']:
   path=out/name; text=path.read_text(); path.write_text('\n'.join(line+' mm_ok=1' if line.startswith(('XM','XQ','XR','XC')) else line for line in text.splitlines())+'\n')
 queries=[]
 for view,instance in [('bgr.spice','xbgr'),('t2f.spice','xt2f')]:
  for line in (out/view).read_text().splitlines():
   fields=line.split()
   if not fields:continue
   device=fields[0].lower()
   if line.startswith('XM'):queries.extend(f'@n.{instance}.{device}.n{fields[5]}[{parameter}]' for parameter in ['w','l','delvto','factuo'])
   elif line.startswith('XR'):queries.extend(f'@n.{instance}.{device}.nr1[{parameter}]' for parameter in ['nsmm_rsh','nsmm_w','nsmm_l'])
   elif line.startswith('XQ'):queries.append(f'@q.{instance}.{device}.qnpn13g2[area]')
   elif line.startswith('XC'):queries.append(f'@c.{instance}.{device}.c1[scale]')
 template=(HERE.parent/'postlayout/decks/ftemp_ptat_T-40.cir').read_text()
 manifest={'command':['python3','run_joint_adverse.py',*__import__('sys').argv[1:]],'image_id':a.image_id,'pdk_commit':(PDK/'COMMIT').read_text().strip(),'git_commit':subprocess.check_output(['git','-c','safe.directory=/work','rev-parse','HEAD'],text=True).strip(),'ngspice':subprocess.check_output(['ngspice','--version'],text=True),'runner_sha256':sha(Path(__file__)),'input_sha256':{dest:sha(src) for dest,src in files.items()},'realized_netlist_sha256':{name:sha(out/name) for name in ['bgr.spice','t2f.spice']},'mismatch':a.mismatch,'seed':a.seed,'op_only':a.op_only,'models_sha256':{str(p.relative_to(PDK)):sha(p) for p in sorted((PDK/'libs.tech/ngspice/models').glob('*.lib'))},'temperature_validity':'-40 to 125 C model range','limitations':'Capacitance-only PEX; ideal IPTAT 1 V termination and 50 fF output; explicit per-case corners; no actual pad; model-local mismatch only when requested, spatial correlation absent.','fingerprint_parameters':queries,'cases':[]}
 for temp in map(float,a.temperatures.split(',')):
  if a.stop_file and a.stop_file.exists():
   manifest['campaign_status']='paused at requested leaf boundary'; manifest['not_run_temperatures']=[t for t in map(float,a.temperatures.split(',')) if t not in [c['temperature_C'] for c in manifest['cases']]]
   (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n'); break
  name=f'ptat_T{temp:g}'; deck=template.replace('bandgap schematic view','bandgap C-PEX view').replace('.include ../../../../g1_bgr/xschem/g1_bgr.spice','.include bgr.spice').replace('.include ../g1_t2f_pex.spice','.include t2f.spice').replace('.temp -40',f'.temp {temp}').replace('Vdd vdd 0 dc 3.3',f'Vdd vdd 0 dc {a.vdd}').replace('Vdd12 vdd12 0 dc 1.2',f'Vdd12 vdd12 0 dc {a.vdd12}').replace('1.01u 3.3',f'1.01u {a.vdd}').replace('tran 5n 40u',f'tran 5n {a.tstop_us}u').replace('set filetype=ascii','set filetype=ascii\nset numdgt=15')
  deck=deck.replace(' hbt_typ',' hbt_'+a.hbt).replace(' mos_tt',' mos_'+a.mos).replace(' res_typ',' res_'+a.res).replace(' cap_typ',' cap_'+a.cap)
  deck=deck.replace('.control\n','.control\nset num_threads=1\n')
  fingerprint=''.join('print '+q+'\n' for q in queries)
  if a.mismatch:
   for kind in ['hbt_'+a.hbt,'mos_'+a.mos,'res_'+a.res,'cap_'+a.cap]: deck=deck.replace(' '+kind,' '+kind+'_mismatch')
   deck=deck.replace('.option gmin=',f'.option seed={a.seed}\n.option gmin=')
   deck=deck.replace(f'tran 5n {a.tstop_us}u',f'op\n{fingerprint}tran 5n {a.tstop_us}u\n{fingerprint}')
  if a.op_only:
   deck=deck.split('.control')[0]+'.control\nset num_threads=1\nset numdgt=15\nop\n'+fingerprint+'print v(vref)\nquit\n.endc\n.end\n'
  deck=f'* G1_T2F joint C-PEX: T={temp} C, VDDA={a.vdd} V, VDD={a.vdd12} V, HBT={a.hbt}, MOS={a.mos}, R={a.res}, C={a.cap}, mismatch={a.mismatch}, seed={a.seed}\n'+'\n'.join(deck.splitlines()[1:])+'\n'
  vectors='v(fout) v(vref) i(vdd) i(vdd12) v(xt2f.cap1) v(xt2f.cap2) v(xt2f.ca1) v(xt2f.tail1) v(xt2f.cb1) v(xt2f.ca2) v(xt2f.tail2) v(xt2f.cb2)'
  deck=deck if a.op_only else deck.replace('.endc',f'wrdata {name}.dat {vectors}\nquit\n.endc'); (out/f'{name}.cir').write_text(deck)
  start=time.monotonic(); timed=False
  with (out/f'{name}.log').open('w') as log, (out/f'{name}.stderr.log').open('w') as err:
   try: p=subprocess.run(['ngspice','-b',f'{name}.cir'],cwd=out,stdout=log,stderr=err,timeout=120 if a.op_only else 300); rc=p.returncode
   except subprocess.TimeoutExpired: timed=True; rc=None
  log=(out/f'{name}.log').read_text(errors='replace'); measurements={k:float(v) for k,v in re.findall(r'(?m)^(\w+)\s*=\s*([-+0-9.eE]+)',log)}
  row={'name':name,'temperature_C':temp,'mismatch':a.mismatch,'seed':a.seed,'op_only':a.op_only,'hbt':a.hbt,'mos':a.mos,'res':a.res,'cap':a.cap,'vdd':a.vdd,'vdd12':a.vdd12,'watchdog_seconds':120 if a.op_only else 300,'timed_out':timed,'solver_exit':rc,'wall_seconds':time.monotonic()-start,'status':'not run' if timed else 'failed','measurements':measurements,'deck_sha256':sha(out/f'{name}.cir')}
  row['fingerprints']=re.findall(r'@[^\s]+\s*=\s*([-+0-9.eE]+)',log)
  log+='\n'+(out/f'{name}.stderr.log').read_text(errors='replace')
  if a.op_only and rc==0 and len(row['fingerprints'])==len(queries) and not re.search(r'(?im)^Error|no such parameter',log): row['status']='passed'
  try:
   with (out/f'{name}.dat').open() as data:
    next(data); d=[list(map(float,line.split())) for line in data if line.strip()]
   if rc==0 and d and all(len(r)==13 and all(map(math.isfinite,r)) for r in d) and abs(d[-1][0]-a.tstop_us*1e-6)<1e-12 and all(k in measurements for k in ['freq','t_a','t_b','t_half_a','fout_hi','fout_lo']) and not re.search(r'(?im)^Error|Timestep too small|analysis aborted',log):
    row['status']='passed'; row['completed_tstop_s']=d[-1][0]; row['t2f_hbt_vce_max_V']=max(abs(r[i]-r[j]) for r in d for i,j in [(7,8),(9,8),(10,11),(12,11)]); row['hbt_vce_status']='passed' if row['t2f_hbt_vce_max_V']<=1.6 else 'failed'
  except (OSError,ValueError,IndexError): pass
  manifest['cases'].append(row); (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n'); print(json.dumps(row),flush=True)
if __name__=='__main__': main()

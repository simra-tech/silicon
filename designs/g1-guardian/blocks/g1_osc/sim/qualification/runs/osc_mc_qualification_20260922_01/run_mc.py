#!/usr/bin/env python3
"""Qualified OSC device/bank mismatch with preserved physical-instance ordering.
All MOS/R/CMIM instances get mm_ok explicitly; fixed extracted wire C is retained.
"""
import argparse,hashlib,json,math,re,shutil,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;PDK=Path('/foss/pdks/ihp-sg13g2')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--run-id',required=True);ap.add_argument('--image-id',required=True);ap.add_argument('--suite',choices=['qualify','screen'],required=True);ap.add_argument('--first-seed',type=int,default=61001);ap.add_argument('--samples',type=int,default=20);ap.add_argument('--codes',default='0,15');ap.add_argument('--tuple',choices=['nominal','slowhot'],default='nominal');ap.add_argument('--r-charge-scale',type=float,default=1.0);ap.add_argument('--stop-file',type=Path);a=ap.parse_args()
 assert (PDK/'COMMIT').read_text().strip()=='84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
 assert 0.5<=a.r_charge_scale<=1
 out=HERE/'runs'/a.run_id;out.mkdir(parents=True,exist_ok=False);shutil.copy(__file__,out/'run_mc.py');shutil.copy(HERE.parent/'.spiceinit',out/'.spiceinit');shutil.copy(HERE.parent/'postlayout/g1_osc_pex.spice',out/'baseline.spice')
 raw=(out/'baseline.spice').read_text();sources={};fp=[]
 for mm in [False,True]:
  lines=[]
  for line in raw.splitlines():
   words=line.split()
   if words and words[0] in ['XR53','XR54','XR55','XR56']:line=line.replace('l=58.5u',f'l={58.5*a.r_charge_scale:g}u')
   if line.startswith(('XM','XR','XC')):
    if mm:
     name=words[0].lower()
     if name.startswith('xm'):var=f'@n.x1.{name}.nsg13_lv_{"pmos" if "sg13_lv_pmos" in words else "nmos"}[delvto]'
     elif name.startswith('xr'):var=f'@n.x1.{name}.nr1[nsmm_rsh]'
     else:var=f'@c.x1.{name}.c1[scale]'
     if name.startswith('xm'):fp.extend(var.replace('[delvto]',f'[{parameter}]') for parameter in ['w','l','delvto','factuo'])
     elif name.startswith('xr'):fp.extend(var.replace('[nsmm_rsh]',f'[{parameter}]') for parameter in ['nsmm_rsh','nsmm_w','nsmm_l'])
     else:fp.append(var)
    line+=' mm_ok='+str(int(mm))
   lines.append(line)
  sources[mm]=out/('mismatch.spice' if mm else 'disabled.spice');sources[mm].write_text('\n'.join(lines)+'\n')
 assert len(fp)==269
 manifest={'command':sys.argv,'image_id':a.image_id,'ngspice':subprocess.check_output(['ngspice','--version'],text=True),'pdk_commit':(PDK/'COMMIT').read_text().strip(),'source_sha256':{n:sha(out/n) for n in ['run_mc.py','baseline.spice','mismatch.spice','disabled.spice','.spiceinit']},'model_sha256':{str(p.relative_to(PDK)):sha(p) for p in sorted((PDK/'libs.tech/ngspice/models').glob('*.lib'))},'fingerprint_parameters':fp,'physical_sample_policy':'same source/order/seed and mismatch library family across code/temperature; all269 realized parameters of80 MOS/R/CMIM devices before/after analyses','limitations':'Capacitance-only PEX; reinserted PDK CMIM geometry, not extracted plates; no spatial correlation;50fF output stand-in; no physical jitter; diode one available nominal model; inheritedrshunt1e12 unchanged','cases':[]}
 def save(): (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 seed=a.first_seed
 cases=[('enabled',seed,8,27,True,True),('repeat',seed,8,27,True,True),('seed2',seed+1,8,27,True,True),('cold',seed,8,-40,True,True),('code15',seed,15,27,True,True),('disabled',seed,8,27,False,True),('disabled_seed2',seed+1,8,27,False,True),('transient',seed,8,27,True,False),('transient_repeat',seed,8,27,True,False)] if a.suite=='qualify' else [(f's{s}_c{c}',s,c,27 if a.tuple=='nominal' else 125,True,False) for s in range(a.first_seed,a.first_seed+a.samples) for c in map(int,a.codes.split(','))]
 manifest['expected_cases']=[case[0] for case in cases]
 save()
 for name,seed,code,temp,mm,op_only in cases:
  if a.stop_file and a.stop_file.exists():manifest['campaign_status']='paused at requested leaf boundary';save();break
  assert 0<=code<=15
  mos,res,cap,vdd=('tt','typ','typ',1.2) if a.tuple=='nominal' else ('ss','wcs','wcs',1.08)
  deck=(HERE.parent/'postlayout/tb_osc_pex.cir').read_text();suffix='_mismatch'
  for k,v in {'MOS':'mos_'+mos+suffix,'RES':'res_'+res+suffix,'CAP':'cap_'+cap+suffix,'VDD':vdd,'TEMP':temp,**{'B'+str(i):(code>>i)&1 for i in range(4)}}.items():deck=deck.replace('@@'+k+'@@',str(v))
  deck=deck.replace('.include postlayout/g1_osc_pex.spice','.include '+sources[mm].name).replace('.option rshunt=1e12',f'.option seed={seed} rshunt=1e12')
  fingerprints=''.join('print '+f+'\n' for f in fp)
  control='set num_threads=1\nset filetype=ascii\nset numdgt=15\nset wr_singlescale\nset wr_vecnames\nop\n'+fingerprints
  if op_only:deck=deck.split('.control')[0]+'.control\n'+control+'quit\n.endc\n.end\n'
  else:deck=deck.replace('set filetype=ascii\n',control).replace('tran 0.2n 3.3u','tran 0.2n 6u\n'+fingerprints).replace('.endc',f'print fmhz duty iua\nwrdata {name}.dat v(osc_clk) i(vdd) v(x1.va) v(x1.vb)\nquit\n.endc')
  (out/(name+'.cir')).write_text(deck);start=time.monotonic();timed=False
  with (out/(name+'.log')).open('w') as log,(out/(name+'.stderr')).open('w') as err:
   try:rc=subprocess.run(['ngspice','-b',name+'.cir'],cwd=out,stdout=log,stderr=err,timeout=120 if op_only else 300).returncode
   except subprocess.TimeoutExpired:rc=None;timed=True
  log=(out/(name+'.log')).read_text(errors='replace');err=(out/(name+'.stderr')).read_text(errors='replace');measurements={k:float(v) for k,v in re.findall(r'(?m)^(\w+)\s*=\s*([-+0-9.eE]+)',log)}
  actualfp=re.findall(r'@[^\s]+\s*=\s*([-+0-9.eE]+)',log);row={'name':name,'seed':seed,'code':code,'temperature_C':temp,'mos':mos,'res':res,'cap':cap,'vdd':vdd,'mm':mm,'op_only':op_only,'solver_exit':rc,'timed_out':timed,'wall_seconds':time.monotonic()-start,'deck_sha256':sha(out/(name+'.cir')),'fingerprints':actualfp,'measurements':measurements,'status':'not run' if timed else 'failed'}
  try:finite_fp=all(math.isfinite(float(v)) for v in actualfp)
  except ValueError:finite_fp=False
  good=finite_fp and rc==0 and len(actualfp)==len(fp)*(1 if op_only else 2) and not re.search(r'(?im)^Error|no such parameter|Timestep too small|analysis aborted',log+'\n'+err)
  if op_only and good:row['status']='passed'
  elif good:
   try:
    with (out/(name+'.dat')).open() as f:next(f);d=[list(map(float,l.split())) for l in f if l.strip()]
    if d and all(len(r)==5 and all(map(math.isfinite,r)) for r in d) and abs(d[-1][0]-6e-6)<1e-12 and all(k in measurements for k in ['fmhz','duty','t1','t2','th1']) and actualfp[:len(fp)]==actualfp[len(fp):]:
     row.update(status='passed',high_width_s=measurements['th1']-measurements['t1'],low_width_s=(measurements['t2']-measurements['t1'])/10-(measurements['th1']-measurements['t1']))
   except (OSError,ValueError,IndexError):pass
  manifest['cases'].append(row);save();print(json.dumps({k:v for k,v in row.items() if k!='fingerprints'}),flush=True)
  if a.suite=='qualify' and row['status']!='passed':manifest['qualification_stop']='First failed case retained; remaining expected cases not run pending diagnosis';save();break
if __name__=='__main__':main()

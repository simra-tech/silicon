#!/usr/bin/env python3
"""Screen all16 OSC trim codes at explicit PVT tuples, sequential300s ceilings."""
import argparse,hashlib,json,re,shutil,subprocess,time
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent; PDK=Path('/foss/pdks/ihp-sg13g2')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--run-id',required=True); ap.add_argument('--image-id',required=True); ap.add_argument('--suite',choices=['pilot','trim'],default='pilot'); ap.add_argument('--shards',type=int,default=1); ap.add_argument('--shard-index',type=int,default=0); ap.add_argument('--tuples',choices=['full','nominal','slowhot','candidate'],default='full'); ap.add_argument('--codes'); ap.add_argument('--r-charge-scale',type=float,default=1.0); ap.add_argument('--tstop-us',type=float); a=ap.parse_args(); assert 0<=a.shard_index<a.shards
 assert (PDK/'COMMIT').read_text().strip()=='84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
 out=HERE/'runs'/a.run_id; out.mkdir(parents=True,exist_ok=False)
 shutil.copy(Path(__file__),out/Path(__file__).name)
 for name,src in [('.spiceinit',HERE.parent/'.spiceinit'),('osc.spice',HERE.parent/'postlayout/g1_osc_pex.spice')]: shutil.copy(src,out/name)
 shutil.copy(out/'osc.spice',out/'osc_source.spice')
 assert 0.5<=a.r_charge_scale<=1.0
 text=(out/'osc.spice').read_text(); edited=[]
 if a.r_charge_scale!=1.0:
  lines=[]
  for line in text.splitlines():
   fields=line.split()
   if fields and fields[0] in ['XR53','XR54','XR55','XR56']:
    assert fields[4]=='rppd' and 'l=58.5u' in fields
    line=line.replace('l=58.5u',f'l={58.5*a.r_charge_scale:g}u');edited.append(fields[0])
   lines.append(line)
  assert len(edited)==4
  (out/'osc.spice').write_text('\n'.join(lines)+'\n')
 tmpl=(HERE.parent/'postlayout/tb_osc_pex.cir').read_text()
 man={'command':['python3','run_trim.py',*__import__('sys').argv[1:]],'image_id':a.image_id,'pdk_commit':(PDK/'COMMIT').read_text().strip(),'ngspice':subprocess.check_output(['ngspice','--version'],text=True),'git_commit':subprocess.check_output(['git','-c','safe.directory=/work','rev-parse','HEAD'],text=True).strip(),'runner_sha256':sha(Path(__file__)),'pex_sha256':sha(out/'osc.spice'),'source_pex_sha256':sha(out/'osc_source.spice'),'candidate':{'charging_resistor_length_scale':a.r_charge_scale,'edited_instances':edited,'physical_status':'isolated device sizing sensitivity with original extracted wire capacitance; no layout regenerated'},'models_sha256':{str(p.relative_to(PDK)):sha(p) for p in sorted((PDK/'libs.tech/ngspice/models').glob('*.lib'))},'limitations':'Existing rshunt1e12 fixture retained;50fF output stand-in;capacitance-only PEX with ideal reinserted MIM;not full PVT Cartesian or mismatch','cases':[]}
 tuples=[('tt','typ','typ',1.2,27),('ss','wcs','wcs',1.08,-40),('ss','wcs','wcs',1.08,125),('ff','bcs','bcs',1.32,-40),('ff','bcs','bcs',1.32,125)]
 if a.tuples=='nominal': tuples=tuples[:1]
 elif a.tuples=='slowhot': tuples=[tuples[2]]
 elif a.tuples=='candidate': tuples=[tuples[0],tuples[2]]
 elif a.suite=='pilot': tuples=tuples[:1]
 for tuple_index,(mos,res,cap,vdd,temp) in enumerate(tuples):
  for code in (list(map(int,a.codes.split(','))) if a.codes else ([8] if a.suite=='pilot' else range(16))):
   assert 0<=code<16
   if (tuple_index*16+code)%a.shards!=a.shard_index: continue
   name=f'{mos}_{res}_{cap}_{vdd}_{temp}_c{code}'; tstop=a.tstop_us or (3.3 if a.suite=='pilot' else 6.0); deck=tmpl.replace('tran 0.2n 3.3u',f'tran 0.2n {tstop}u')
   substitutions={'MOS':'mos_'+mos,'RES':'res_'+res,'CAP':'cap_'+cap,'VDD':vdd,'TEMP':temp,**{'B'+str(i):(code>>i)&1 for i in range(4)}}
   for k,v in substitutions.items(): deck=deck.replace('@@'+k+'@@',str(v))
   deck=deck.replace('.control\n','.control\nset num_threads=1\n').replace('.include postlayout/g1_osc_pex.spice','.include osc.spice').replace('set filetype=ascii','set filetype=ascii\nset numdgt=15\nset wr_singlescale\nset wr_vecnames').replace('.endc',f'print fmhz duty iua\nwrdata {name}.dat v(osc_clk) i(vdd) v(x1.va) v(x1.vb)\nquit\n.endc')
   (out/f'{name}.cir').write_text(deck); start=time.monotonic(); timed=False
   with (out/f'{name}.log').open('w') as log:
    try: proc=subprocess.run(['ngspice','-b',f'{name}.cir'],cwd=out,stdout=log,stderr=subprocess.STDOUT,timeout=300); rc=proc.returncode
    except subprocess.TimeoutExpired: timed=True; rc=None
   text=(out/f'{name}.log').read_text(errors='replace'); meas={k:float(v) for k,v in re.findall(r'(?m)^(\w+)\s*=\s*([-+0-9.eE]+)',text)}
   row={'name':name,'code':code,'charging_resistor_length_scale':a.r_charge_scale,'mos':mos,'res':res,'cap':cap,'vdd':vdd,'temp':temp,'tstop_us':tstop,'watchdog_seconds':300,'timed_out':timed,'solver_exit':rc,'wall_seconds':time.monotonic()-start,'status':'not run' if timed else 'failed','measurements':meas,'deck_sha256':sha(out/f'{name}.cir')}
   try:
    d=np.loadtxt(out/f'{name}.dat',skiprows=1)
    if rc==0 and np.isfinite(d).all() and abs(d[-1,0]-tstop*1e-6)<1e-12 and all(k in meas for k in ['fmhz','duty','t1','t2','th1']) and not re.search(r'(?im)^Error|Timestep too small|analysis aborted',text):
     row['status']='passed'; row['high_width_s']=(meas['th1']-meas['t1']); row['low_width_s']=(meas['t2']-meas['t1'])/10-row['high_width_s']
   except (OSError,ValueError,IndexError): pass
   man['cases'].append(row); (out/'manifest.json').write_text(json.dumps(man,indent=2)+'\n'); print(json.dumps(row),flush=True)
if __name__=='__main__': main()

#!/usr/bin/env python3
"""Synthetic external perturbation sensitivity; NOT physical device-noise jitter.
Stores identical fixed normalized PWL waveform and zero-amplitude breakpoint anchor.
"""
import argparse,hashlib,json,math,random,re,shutil,statistics,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;DESIGN=HERE.parents[3];PDK=Path('/foss/pdks/ihp-sg13g2')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def edges(d,col,level):
 return [a[0]+(level-a[col])*(b[0]-a[0])/(b[col]-a[col]) for a,b in zip(d,d[1:]) if a[col]<level<=b[col]]
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--run-id',required=True);ap.add_argument('--image-id',required=True);ap.add_argument('--block',choices=['osc','t2f'],required=True);ap.add_argument('--rms-mV',default='0,1,5');ap.add_argument('--waveform-seed',type=int,default=9871);ap.add_argument('--stop-file',type=Path);a=ap.parse_args();base=DESIGN/f'blocks/g1_{a.block}/sim/qualification';out=base/'runs'/a.run_id;out.mkdir(exist_ok=False);shutil.copy(__file__,out/Path(__file__).name)
 stop,window=(20e-6,5e-6) if a.block=='osc' else (32e-6,8e-6);dt=2e-9;tau=100e-9;alpha=math.exp(-dt/tau);rng=random.Random(a.waveform_seed);y=rng.gauss(0,1);wave=[]
 for i in range(round(stop/dt)+1):
  t=i*dt;y=alpha*y+math.sqrt(1-alpha*alpha)*rng.gauss(0,1);wave.append((t,y*min(t/1e-6,1)))
 (out/'normalized_pwl.json').write_text(json.dumps(wave,separators=(',',':'))+'\n')
 if a.block=='osc':
  source=DESIGN/'blocks/g1_osc/sim';shutil.copy(source/'.spiceinit',out/'.spiceinit');shutil.copy(source/'postlayout/g1_osc_pex.spice',out/'osc.spice');deck=(source/'postlayout/tb_osc_pex.cir').read_text().split('.control')[0]
  for k,v in {'MOS':'mos_tt','RES':'res_typ','CAP':'cap_typ','TEMP':27,'VDD':1.2,'B0':0,'B1':0,'B2':0,'B3':1}.items():deck=deck.replace('@@'+k+'@@',str(v))
  deck=deck.replace('.include postlayout/g1_osc_pex.spice','.include osc.spice');assert 'Vdd vdd 0 dc {VDD}' in deck;deck=deck.replace('Vdd vdd 0 dc {VDD}','* supply replaced by stored synthetic PWL');connection=('Vnoise vdd 0',1.2);vectors=['v(osc_clk)','v(vdd)','i(vnoise)','v(x1.va)','v(x1.vb)'];step='0.2n'
 else:
  source=HERE/'runs/t2f_joint_temp7_20260921_01'
  for name in ['.spiceinit','bgr.spice','t2f.spice']:shutil.copy(source/name,out/name)
  deck=(source/'ptat_T25.cir').read_text().split('.control')[0];old='Xt2f vdd vdd12 0 pbias pcasc vref en mode fout g1_t2f';assert old in deck;deck=deck.replace(old,old.replace('vref en','vref_injected en'));connection=('Vnoise vref_injected vref',0);vectors=['v(fout)','v(vref_injected)','i(vdd)','v(vref)','i(vdd12)'];step='5n'
 m={'command':sys.argv,'image_id':a.image_id,'ngspice':subprocess.check_output(['ngspice','--version'],text=True),'pdk_commit':(PDK/'COMMIT').read_text().strip(),'model_sha256':{str(p.relative_to(PDK)):sha(p) for p in sorted((PDK/'libs.tech/ngspice/models').glob('*.lib'))},'source_sha256':{p.name:sha(p) for p in out.iterdir() if p.suffix=='.spice' or p.name=='.spiceinit'},'waveform_sha256':sha(out/'normalized_pwl.json'),'synthetic_model':{'seed':a.waveform_seed,'discrete_OU_dt_s':dt,'time_constant_s':tau,'linear_interpolation':True,'nominal_one_pole_corner_Hz':1/(2*math.pi*tau),'one_us_amplitude_ramp':True,'stationary_rms_target':'unit waveform scaled by requestedmillivolts; finite realizedRMSreported separately'},'acceptance':'characterization only; no physical jitter or adopted jitter budget','limitations':'External synthetic perturbation only, notPDKdevice-noise/phase-noise prediction. No sourcecorrelation/substrate/package/spatialnoise. T2F noise is idealseriesreference perturbation; OSCnoise is idealrail perturbation. Finite record and numericalbaseline limitaccuracy. Output50fFstand-in, coreCPEX only.','cases':[]};save=lambda:(out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n');save()
 for rms in map(float,a.rms_mV.split(',')):
  if a.stop_file and a.stop_file.exists():m['campaign_status']='paused at requested leaf boundary';save();break
  assert 0<=rms<=10;name=f'rms_{rms:g}mV';stim=connection[0]+' PWL(\n'+''.join(f'+ {t:.12g} {connection[1]+rms*.001*y:.15g}\n' for t,y in wave)+'+ )\n';text=deck+stim+'.control\nset num_threads=1\nset numdgt=15\nset wr_singlescale\nset wr_vecnames\n'+f'tran {step} {stop:.12g}\nwrdata {name}.dat '+' '.join(vectors)+'\nquit\n.endc\n.end\n';(out/(name+'.cir')).write_text(text);start=time.monotonic()
  with (out/(name+'.log')).open('w') as log,(out/(name+'.stderr')).open('w') as err:
   try:rc=subprocess.run(['ngspice','-b',name+'.cir'],cwd=out,stdout=log,stderr=err,timeout=300).returncode;timed=False
   except subprocess.TimeoutExpired:rc=None;timed=True
  noise=[rms*.001*y for t,y in wave if t>=window];r={'requested_rms_mV':rms,'synthetic_window_mean_V':statistics.mean(noise),'synthetic_window_std_V':statistics.pstdev(noise),'solver_exit':rc,'timed_out':timed,'wall_seconds':time.monotonic()-start,'deck_sha256':sha(out/(name+'.cir')),'status':'not run' if timed else 'failed'}
  try:
   with (out/(name+'.dat')).open() as f:next(f);d=[list(map(float,l.split())) for l in f if l.strip()]
   log=(out/(name+'.log')).read_text()+'\n'+(out/(name+'.stderr')).read_text()
   if rc==0 and d and all(len(x)==6 and all(map(math.isfinite,x)) for x in d) and abs(d[-1][0]-stop)<1e-12 and not re.search(r'(?im)^Error|Timestep too small|analysis aborted',log):
    ee=[t for t in edges(d,1,.6) if window<=t<=stop];periods=[v-u for u,v in zip(ee,ee[1:])];assert len(periods)>=10;r.update(status='passed',period_count=len(periods),measurement_window_start_s=window,measurement_window_end_s=stop,mean_frequency_Hz=1/statistics.mean(periods),period_std_s=statistics.pstdev(periods),period_min_s=min(periods),period_max_s=max(periods),period_peak_to_peak_s=max(periods)-min(periods),cycle_to_cycle_rms_s=math.sqrt(statistics.mean((b-a)**2 for a,b in zip(periods,periods[1:]))),rising_edges_s=ee,periods_s=periods)
  except (OSError,ValueError,IndexError,StopIteration,AssertionError):pass
  m['cases'].append(r);save();print(json.dumps({k:v for k,v in r.items() if k not in ['rising_edges_s','periods_s']}),flush=True)
if __name__=='__main__':main()

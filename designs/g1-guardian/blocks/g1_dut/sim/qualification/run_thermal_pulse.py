#!/usr/bin/env python3
"""Selected pad-inclusive HBT thermal-pulse diagnostics, not package thermal models."""
import argparse,hashlib,json,math,os,re,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[6];SIM=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'designs/g1-guardian/blocks/g1_top/sim'))
from run_bounded import run_bounded
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run-id',required=True);a=p.parse_args();out=SIM/'qualification'/a.run_id;out.mkdir(exist_ok=False);shutil.copyfile(Path(__file__),out/'runner.py');prior=SIM/'qualification/selfheat_pilot_20260922_r1';assert json.loads((prior/'qualification.json').read_text())['status']=='passed';base=SIM/'qualification/macro_20260921T153803Z_e82d0d1c/tt_27_1.2_3.3.cir';pex=SIM.parent/'reports/flat-pex-20260921T150414Z_3db2c2ca/ngspice_pex.spice'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for v in [0,1]:shutil.copyfile(prior/f'coupon_selft{v}.spice',out/f'coupon_selft{v}.spice')
prov={'scope':'Device-local PDK thermalRC transient, originalflatCPEX/pads/routeRC. Base0.65->0.8V pulse at100ns,10ns edges,200ns high,1us observation. No package or sharedchipthermal model; selft0 control is diagnostic.','source_hashes':{str(x.relative_to(ROOT)):sha(x) for x in [base,pex,prior/'provenance.json',prior/'qualification.json',Path(__file__)]},'prior_provenance':json.loads((prior/'provenance.json').read_text()),'maximum_step_s':1e-10,'mode':'selectedtyp27/bcs85'};(out/'provenance.json').write_text(json.dumps(prov,indent=2)+'\n');results=[]
for corner,temp in [('typ',27),('bcs',85)]:
 for selft in [0,1]:
  name=f'{corner}_{temp}_selft{selft}';leaf=out/name;leaf.mkdir();shutil.copyfile(base.parent/'.spiceinit',leaf/'.spiceinit');deck=base.read_text().split('.control')[0].replace(str(pex),str(out/f'coupon_selft{selft}.spice')).replace('.temp 27',f'.temp {temp}').replace('hbt_typ\n',f'hbt_{corner}\n').replace('Vb b_pad 0 0.7','Vb b_pad 0 pulse(0.65 0.8 100n 10n 10n 200n 2u)');deck+='.control\nset num_threads=1\nset numdgt=15\nset wr_singlescale\nset wr_vecnames\ntran .1n 1u 0 .1n\nwrdata '+str(leaf/'wave.tsv')+' v(b_pad) v(b) v(c) v(e) i(vm_b) i(vm_c) i(vm_e) v(x1.xq1.t)\necho HBT_PULSE_END\nquit 0\n.endc\n.end\n';(leaf/'fixture.cir').write_text(deck)
  with (leaf/'tool.log').open('x') as log:state=run_bounded(['ngspice','-b','fixture.cir'],log,leaf/'run.json',60,cwd=leaf,env=dict(os.environ,OMP_NUM_THREADS='1'),metadata={'corner':corner,'ambient_C':temp,'selft':selft,'deck_sha256':sha(leaf/'fixture.cir')},interval_s=.2)
  wave=leaf/'wave.tsv';rows=[list(map(float,l.split())) for l in wave.read_text().splitlines()[1:]] if wave.exists() else [];log=(leaf/'tool.log').read_text();errors=[l for l in log.splitlines() if re.search(r'(?i)(^Error|fatal|timestep too small|doAnalyses:)',l)];ok=bool(rows) and rows[-1][0]>=1e-6*(1-1e-9) and all(len(r)==9 and all(map(math.isfinite,r)) for r in rows)
  mean=lambda idx,lo,hi:sum(r[idx] for r in rows if lo<=r[0]<=hi)/sum(lo<=r[0]<=hi for r in rows)
  res={'name':name,'corner':corner,'ambient_C':temp,'selft':selft,'status':'passed' if ok and not errors and state['returncode']==0 and 'HBT_PULSE_END' in log else 'failed','wall_s':state['wall_s'],'errors':errors,'rows':len(rows),'wave_sha256':sha(wave) if wave.exists() else None}
  if ok:
   cold=mean(8,50e-9,90e-9);hot=mean(8,250e-9,290e-9);final=mean(8,900e-9,1e-6);times=[]
   if hot>cold+1e-9:
    for f in [.1,.9]:
     threshold=cold+f*(hot-cold);pairs=[(x,y) for x,y in zip(rows,rows[1:]) if 100e-9<=y[0]<250e-9 and x[8]<=threshold<=y[8]];x,y=pairs[0];times.append(x[0]+(threshold-x[8])/(y[8]-x[8])*(y[0]-x[0]))
   res.update(initial_rise_K=cold,high_plateau_rise_K=hot,final_rise_K=final,thermal_10to90_s=times[-1]-times[0] if times else None,IC_initial_A=mean(6,50e-9,90e-9),IC_high_A=mean(6,250e-9,290e-9),IC_final_A=mean(6,900e-9,1e-6),maximum_rise_K=max(r[8] for r in rows),maximum_VCE_V=max(r[3]-r[4] for r in rows),maximum_junction_C=temp+max(r[8] for r in rows))
  results.append(res);(out/'manifest.json').write_text(json.dumps({'cases':results,'scope':prov['scope']},indent=2)+'\n');print(json.dumps(res),flush=True)
  if res['status']!='passed':raise SystemExit(1)

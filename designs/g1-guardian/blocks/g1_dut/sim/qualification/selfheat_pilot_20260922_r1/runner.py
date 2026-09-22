#!/usr/bin/env python3
"""Pinned HBT built-in self-heating sensitivity with unchanged pad/route fixture."""
import argparse,hashlib,json,math,os,re,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[6];SIM=Path(__file__).resolve().parents[1];PDK=Path('/foss/pdks/ihp-sg13g2');sys.path.insert(0,str(ROOT/'designs/g1-guardian/blocks/g1_top/sim'))
from run_bounded import run_bounded
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run-id',required=True);p.add_argument('--mode',choices=['pilot','screen'],required=True);p.add_argument('--pilot',type=Path);a=p.parse_args();out=SIM/'qualification'/a.run_id;out.mkdir(exist_ok=False);shutil.copyfile(Path(__file__),out/'runner.py')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
base=SIM/'qualification/macro_20260921T153803Z_e82d0d1c/tt_27_1.2_3.3.cir';pex=SIM.parent/'reports/flat-pex-20260921T150414Z_3db2c2ca/ngspice_pex.spice';model=PDK/'libs.tech/ngspice/models/sg13g2_hbt_mod.lib';init=base.parent/'.spiceinit';source=pex.read_text();assert source.count('XQ1 ')==1 and 'selft=' not in source
for val in [0,1]:(out/f'coupon_selft{val}.spice').write_text('\n'.join(l+f' selft={val}' if l.startswith('XQ1 ') else l for l in source.splitlines())+'\n')
sub=re.search(r'(?ims)^\.subckt npn13G2\s.*?^\.ends npn13G2',model.read_text(errors='replace'))[0];assert '+selft=1' in sub and "rth = '1*selft*3.26E+03*(4/Nx)**0.9'" in sub
(out/'hbt_model_excerpt.txt').write_text(sub+'\n')
provenance={'scope':'Flat-CPEX HBT with existing detailed analog pads and estimated routeRC; existing PDK selft parameter toggled on copied coupon instance only. selft1 is already the PDK default. No model-card edit, package/chip thermal coupling, radiation model or measured thermal result.','inputs':{str(x.relative_to(ROOT)):sha(x) for x in [base,pex,init,Path(__file__)]},'model_sha256':{str(x.relative_to(PDK)):sha(x) for x in sorted((PDK/'libs.tech/ngspice/models').glob('*.lib'))},'pdk_commit':(PDK/'COMMIT').read_text().strip(),'image_id':'sha256:5fd78498e578c6e9ec10828c248ca3790fc88250ff6caf545521b29e448ea3c0','ngspice_version':subprocess.check_output(['ngspice','--version'],text=True),'nominal_Rth_K_per_W':3.26e3*4**.9,'nominal_Cth_J_per_K':1.60e-12*.25**.95,'temperature_node':'v(x1.xq1.t), built-in VBIC thermal output, interpreted as junction riseK','model_range_screen':'Source-model stated VBE0.65..0.96,VCE0.4..2.0,IC<3mA*Nx,ambient-40..125C; separately report VCE<=1.6V terminal limit and junctionT<=125C. Off-region Gummel points outside stated range are characterization only.'}
assert provenance['pdk_commit']=='84374023ee8b4b126bebbba67fcbada0a9c0ff0b';(out/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
if a.mode=='screen':assert a.pilot and json.loads(a.pilot.read_text())['status']=='passed'
def run(corner,temp,selft):
 name=f'{corner}_{temp}_selft{selft}';leaf=out/name;leaf.mkdir();shutil.copyfile(init,leaf/'.spiceinit');deck=base.read_text().split('.control')[0].replace('.temp 27',f'.temp {temp}').replace('hbt_typ\n',f'hbt_{corner}\n')
 if selft!='default':deck=deck.replace(str(pex),str(out/f'coupon_selft{selft}.spice'))
 deck+='.control\nset num_threads=1\nset numdgt=15\nset wr_singlescale\nset wr_vecnames\ndc Vb 0.30 0.85 0.001\nwrdata '+str(leaf/'wave.tsv')+' v(b) v(c) v(e) i(vm_b) i(vm_c) i(vm_e) i(vb) i(vc) i(ve) i(vdd) i(vdda) v(x1.xq1.t)\necho HBT_THERMAL_END\nquit 0\n.endc\n.end\n';(leaf/'fixture.cir').write_text(deck)
 with (leaf/'tool.log').open('x') as f:state=run_bounded(['ngspice','-b','fixture.cir'],f,leaf/'run.json',30,cwd=leaf,env=dict(os.environ,OMP_NUM_THREADS='1'),metadata={'corner':corner,'ambient_C':temp,'selft':selft,'deck_sha256':sha(leaf/'fixture.cir')},interval_s=.1)
 log=(leaf/'tool.log').read_text();wave=leaf/'wave.tsv';rows=[]
 if wave.exists():rows=[list(map(float,l.split())) for l in wave.read_text().splitlines()[1:] if l.strip()]
 errors=[l for l in log.splitlines() if re.search(r'(?i)(^Error|fatal|timestep too small|doAnalyses:)',l)];valid=len(rows)==551 and all(len(r)==13 and all(map(math.isfinite,r)) for r in rows)
 points=[]
 for r in rows:
  vbe=r[1]-r[3];vce=r[2]-r[3];ic=r[5];ib=r[4];power=vce*ic+vbe*ib;points.append({'external_base_V':r[0],'VBE_V':vbe,'VCE_V':vce,'IC_A':ic,'IB_A':ib,'collector_external_A':-r[8],'collector_pad_A':-r[8]-ic,'temperature_rise_K':r[12],'junction_C':temp+r[12],'terminal_power_W':power,'model_bias_range':.65<=vbe<=.96 and .4<=vce<=2 and 0<=ic<.003,'thermal_power_over_terminal_power':r[12]/provenance['nominal_Rth_K_per_W']/power if power>1e-12 else None})
 anchors=[]
 for target in [1e-7,1e-6,1e-5,1e-4,1e-3]:
  pairs=[(x,y) for x,y in zip(points,points[1:]) if x['IC_A']<=target<=y['IC_A']]
  if pairs:
   x,y=pairs[0];frac=(target-x['IC_A'])/(y['IC_A']-x['IC_A']);anchors.append({'target_IC_A':target,**{k:x[k]+frac*(y[k]-x[k]) for k in ['external_base_V','VBE_V','VCE_V','IB_A','collector_external_A','collector_pad_A','temperature_rise_K','junction_C','terminal_power_W']}})
 status='passed' if state['returncode']==0 and valid and not errors and 'HBT_THERMAL_END' in log else 'failed';result={'name':name,'corner':corner,'ambient_C':temp,'selft':selft,'status':status,'wall_s':state['wall_s'],'errors':errors,'rows':len(rows),'wave_sha256':sha(wave) if wave.exists() else None,'anchors':anchors,'maximum_temperature_rise_K':max((x['temperature_rise_K'] for x in points),default=None),'maximum_IC_A':max((x['IC_A'] for x in points),default=None),'VCE_over_1p6_count':sum(x['VCE_V']>1.6 for x in points),'outside_stated_bias_count':sum(not x['model_bias_range'] for x in points),'junction_above_125C_count':sum(x['junction_C']>125+1e-9 for x in points)};(leaf/'analysis.json').write_text(json.dumps(result,indent=2)+'\n');print(name,status,round(state['wall_s'],3),flush=True);return result
specs=[('typ',27,s) for s in ['default',1,0]] if a.mode=='pilot' else [(c,t,s) for c in ['typ','bcs','wcs'] for t in [-40,27,85,125] for s in [1,0]];results=[]
for case in specs:
 results.append(run(*case));(out/'manifest.json').write_text(json.dumps({'cases':results,'scope':provenance['scope']},indent=2)+'\n')
 if results[-1]['status']!='passed':break
if a.mode=='pilot':
 checks={'all3_complete':len(results)==3 and all(r['status']=='passed' for r in results)}
 if checks['all3_complete']:checks.update(default_equals_explicit_on=results[0]['wave_sha256']==results[1]['wave_sha256'],disabled_temperature_zero=results[2]['maximum_temperature_rise_K']==0,enabled_temperature_positive=results[1]['maximum_temperature_rise_K']>0,on_off_currents_differ=results[1]['maximum_IC_A']!=results[2]['maximum_IC_A'])
 q={'status':'passed' if all(checks.values()) else 'failed','checks':checks};(out/'qualification.json').write_text(json.dumps(q,indent=2)+'\n');print(json.dumps(q));assert q['status']=='passed'
else:assert len(results)==24 and all(r['status']=='passed' for r in results)

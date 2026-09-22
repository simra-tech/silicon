#!/usr/bin/env python3
"""Qualify and characterize only the two DOSE coupon mismatch instances."""
import argparse,hashlib,json,math,os,re,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[6];SIM=Path(__file__).resolve().parents[1];PDK=Path('/foss/pdks/ihp-sg13g2');sys.path.insert(0,str(ROOT/'designs/g1-guardian/blocks/g1_top/sim'))
from run_bounded import run_bounded
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run-id',required=True);p.add_argument('--mode',choices=['qualify','nominal','hot'],required=True);p.add_argument('--qualification',type=Path);p.add_argument('--seeds',default='');a=p.parse_args();out=SIM/'qualification'/a.run_id;out.mkdir(exist_ok=False);shutil.copyfile(Path(__file__),out/'runner.py')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
base=SIM/'qualification/macro_20260921T153804Z_b4ddcb86/tt_27_1.2_3.3.cir';pex=SIM.parent/'reports/flat-pex-20260921T150428Z_7652097b/ngspice_pex.spice';init=base.parent/'.spiceinit';io=PDK/'libs.ref/sg13g2_io/spice/sg13g2_io.spi';models=PDK/'libs.tech/ngspice/models';assert (PDK/'COMMIT').read_text().strip()=='84374023ee8b4b126bebbba67fcbada0a9c0ff0b';assert 'mm_ok' not in io.read_text()
for name in ['sg13g2_moslv_mod_mismatch.lib','sg13g2_moshv_mod_mismatch.lib']:assert 'mm_ok=0' in (models/name).read_text()
original=pex.read_text();coupon_lines=[l for l in original.splitlines() if l.startswith('XM')];assert len(coupon_lines)==2 and all('mm_ok' not in l for l in coupon_lines)
for enabled in [0,1]:(out/f'coupon_mm{enabled}.spice').write_text('\n'.join(l+f' mm_ok={enabled}' if l.startswith('XM') else l for l in original.splitlines())+'\n')
coupon=['n.x1.xm1.nsg13_lv_nmos','n.x1.xm2.nsg13_hv_nmos'];pads=[f'n.xp_{pad}.xi{child}.{dev}.nsg13_hv_{kind}mos' for pad in ['g','dh','dl'] for child,dev,kind in [('0','xp0','p'),('0','xp1','p'),('4','xn0','n')]];targets=coupon+pads
provenance={'scope':'Only2coupon mm_ok instances enabled in flatCPEX; unchanged detailedAnalogPads defaultmm_ok0, actual routeR estimates and lumpedC fixture. No radiation calibration, packaged leakage floor, allocated acceptance tolerance or pad mismatch characterization.','mode':a.mode,'inputs':{str(x.relative_to(ROOT)):sha(x) for x in [base,pex,init,Path(__file__)]},'model_sha256':{str(x.relative_to(PDK)):sha(x) for x in sorted(models.glob('*.lib'))},'io_sha256':sha(io),'pdk_commit':(PDK/'COMMIT').read_text().strip(),'ngspice_version':subprocess.check_output(['ngspice','--version'],text=True),'image_id':'sha256:5fd78498e578c6e9ec10828c248ca3790fc88250ff6caf545521b29e448ea3c0','fingerprint_targets':targets,'parameters':['w','l','delvto','factuo']}
(out/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
if a.mode!='qualify':
 assert a.qualification is not None
 q=json.loads(a.qualification.read_text());assert q['status']=='passed';provenance['qualification_sha256']=sha(a.qualification);(out/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')

def run(name,seed,enabled,temps):
 leaf=out/name;leaf.mkdir();shutil.copyfile(init,leaf/'.spiceinit');deck=base.read_text().split('.control')[0];deck=deck.replace(str(pex),str(out/f'coupon_mm{enabled}.spice')).replace('mos_tt\n','mos_tt_mismatch\n');assert str(out/f'coupon_mm{enabled}.spice') in deck
 deck+=f'.option seed={seed}\n';control=['set num_threads=1','set numdgt=15','set wr_singlescale','set wr_vecnames',f'setseed {seed}','reset'];fpnames=[]
 for ti,temp in enumerate(temps):
  control += [f'set temp={temp}','alter Vg dc=0','op']
  for phase in ['before','after']:
   marker=f't{ti}_{temp}_{phase}';fpnames.append(marker);control += ['echo FP_BEGIN '+marker]+[f'print @{target}[{param}]' for target in targets for param in ['w','l','delvto','factuo']]+['echo FP_END '+marker]
   if phase=='before':control += ['dc Vg -0.3 1.2 0.01',f'wrdata {leaf}/t{ti}_{temp}.tsv v(g) v(dh) v(dl) i(vm_g) i(vm_dh) i(vm_dl) i(vg) i(vdh) i(vdl) i(vdd) i(vdda)']
 control += ['echo DOSE_MISMATCH_END','quit 0'];deck+='.control\n'+'\n'.join(control)+'\n.endc\n.end\n';(leaf/'fixture.cir').write_text(deck)
 with (leaf/'tool.log').open('x') as f:state=run_bounded(['ngspice','-b','fixture.cir'],f,leaf/'run.json',30,cwd=leaf,env=dict(os.environ,OMP_NUM_THREADS='1'),metadata={'seed':seed,'enabled':enabled,'temps':temps,'deck_sha256':sha(leaf/'fixture.cir')},interval_s=.1)
 log=(leaf/'tool.log').read_text();fps={}
 for marker in fpnames:
  part=log.split('FP_BEGIN '+marker+'\n')[-1].split('FP_END '+marker)[0];fps[marker]={key:float(value) for key,value in re.findall(r'(?m)^(@[^\s]+)\s*=\s*([-+0-9.eE]+)',part)}
 valid=all(len(x)==44 and all(map(math.isfinite,x.values())) for x in fps.values());frozen=valid and all(x==next(iter(fps.values())) for x in fps.values());points={};waves={}
 for ti,temp in enumerate(temps):
  path=leaf/f't{ti}_{temp}.tsv'
  if not path.exists():continue
  rows=[list(map(float,l.split())) for l in path.read_text().splitlines()[1:] if l.strip()];assert all(len(r)==12 for r in rows)
  points[f't{ti}_{temp}']={}
  for vg in [0.,.3,.6,1.2]:
   r=min(rows,key=lambda r:abs(r[0]-vg));assert abs(r[0]-vg)<1e-8
   points[f't{ti}_{temp}'][str(vg)]={'applied_gate_V':r[0],'intrinsic_gate_V':r[1],'HV_drain_V':r[2],'LV_drain_V':r[3],'HV_device_A':r[5],'LV_device_A':r[6],'HV_external_A':-r[8],'LV_external_A':-r[9],'HV_pad_A':-r[8]-r[5],'LV_pad_A':-r[9]-r[6]}
  waves[f't{ti}_{temp}']={'sha256':sha(path),'rows':len(rows)}
 errors=[x for x in log.splitlines() if re.search(r'(?i)(^Error|fatal|timestep too small|doAnalyses:)',x)]
 status='passed' if state['returncode']==0 and frozen and len(waves)==len(temps) and all(x['rows']==151 for x in waves.values()) and not errors and 'DOSE_MISMATCH_END' in log else 'failed'
 row={'name':name,'seed':seed,'mismatch_enabled':enabled,'temps':temps,'status':status,'watchdog_status':state['status'],'wall_s':state['wall_s'],'errors':errors,'fingerprints':fps,'frozen_all44':frozen,'waves':waves,'points':points};(leaf/'analysis.json').write_text(json.dumps(row,indent=2)+'\n');print(name,status,round(state['wall_s'],3),flush=True);return row

cases=[]
if a.mode=='qualify':specs=[('repeat_a',55001,1),('repeat_b',55001,1),('changed',55002,1),('disabled_a',55001,0),('disabled_b',55002,0)]
else:specs=[(f'seed{s}',s,1) for s in (list(map(int,a.seeds.split(','))) if a.seeds else range(55101,55201))]
for name,seed,enabled in specs:
 cases.append(run(name,seed,enabled,[27,125,27] if a.mode in ['qualify','hot'] else [27]));(out/'manifest.json').write_text(json.dumps({'cases':cases,'scope':provenance['scope']},indent=2)+'\n')
 if cases[-1]['status']!='passed':break
if a.mode=='qualify':
 checks={};complete=len(cases)==5 and all(c['status']=='passed' for c in cases);checks['all_leaves_completed_frozen']=complete
 if complete:
  first=lambda i:next(iter(cases[i]['fingerprints'].values()))
  checks['same_seed_fingerprints_repeat']=first(0)==first(1)
  checks['same_seed_waves_repeat']=cases[0]['waves']==cases[1]['waves']
  checks['changed_seed_each_coupon_changes']=all(any(first(0)[f'@{t}[{p}]']!=first(2)[f'@{t}[{p}]'] for p in ['w','l','delvto','factuo']) for t in coupon)
  checks['pad_all36_params_unchanged']=all(all(fp[f'@{t}[{p}]']==first(0)[f'@{t}[{p}]'] for t in pads for p in ['w','l','delvto','factuo']) for c in cases for fp in c['fingerprints'].values())
  checks['pad_delvto0_factuo1']=all(first(0)[f'@{t}[delvto]']==0 and first(0)[f'@{t}[factuo]']==1 for t in pads)
  checks['disabled_fingerprints_seed_invariant']=first(3)==first(4)
  checks['disabled_currents_seed_invariant']=cases[3]['waves']==cases[4]['waves']
  checks['disabled_coupon_delvto0_factuo1']=all(first(3)[f'@{t}[delvto]']==0 and first(3)[f'@{t}[factuo]']==1 for t in coupon)
  checks['LV_zero_gate_current_changes']=cases[0]['points']['t0_27']['0.0']['LV_device_A']!=cases[2]['points']['t0_27']['0.0']['LV_device_A']
  checks['HV_on_current_changes']=cases[0]['points']['t0_27']['1.2']['HV_device_A']!=cases[2]['points']['t0_27']['1.2']['HV_device_A']
  checks['temperature_return_currents_repeat']=all(c['waves']['t0_27']==c['waves']['t2_27'] for c in cases)
 result={'status':'passed' if checks and all(checks.values()) else 'failed','checks':checks,'case_count':len(cases),'script_sha256':sha(Path(__file__))};(out/'qualification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
 if result['status']!='passed':raise SystemExit(1)
elif len(cases)!=len(specs) or any(c['status']!='passed' for c in cases):raise SystemExit(1)

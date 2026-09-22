#!/usr/bin/env python3
"""Actual VREF pad + declared10nF board load, bounded transistor-level dynamic cases."""
import argparse,hashlib,json,math,os,re,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];AUD=ROOT/'designs/g1-guardian/review/audits';sys.path.insert(0,str(ROOT/'designs/g1-guardian/blocks/g1_top/sim'))
from run_bounded import run_bounded
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--temperatures',default='27');p.add_argument('--cases',default='load,dip,startup');p.add_argument('--timeout',type=float,default=120);a=p.parse_args();out=a.output.resolve();out.mkdir(exist_ok=False);shutil.copyfile(__file__,out/'runner.py')
src=AUD/'vref-pad-loading-20260922-r2';shutil.copyfile(src/'pex_nominal.spice',out/'pex_nominal.spice');base=(src/'pad_R1_open/fixture.cir').read_text().split('.control')[0];base+='Cboard pad 0 10n\n';prov=json.loads((src/'provenance.json').read_text());prov.update({'scope':'Canonical BGR CPEX, unchanged AnalogPad, declared10nF external capacitor;613.3425ohm whole-treeR sensitivity, ideal1VIPTATload. Nominal process, requested temperatures. Idealcommonrails; no downstreamSENSE/T2Fload/packageESR/inductance qualification.','source_deck_sha256':hashlib.sha256((src/'pad_R1_open/fixture.cir').read_bytes()).hexdigest(),'board_cap_F':1e-8});(out/'provenance.json').write_text(json.dumps(prov,indent=2)+'\n');results=[]
for temp in map(float,a.temperatures.split(',')):
 for case in a.cases.split(','):
  name=f'{case}_{temp:g}C';leaf=out/name;leaf.mkdir();shutil.copyfile(src/'pad_R1_open/.spiceinit',leaf/'.spiceinit');deck=base
  if case=='load':deck+='Istep pad 0 pwl(0 0 100u 0 110u 100n 2m 100n 2.01m 0 5m 0)\n';uic=''
  elif case=='dip':deck=deck.replace('Vdd vdd 0 3.3','Vdd vdd 0 pwl(0 3.3 100u 3.3 110u 3.0 500u 3.0 510u 3.3 5m 3.3)');uic=''
  elif case=='startup':deck=deck.replace('Vdd vdd 0 3.3','Vdd vdd 0 pwl(0 0 1m 3.3 5m 3.3)').replace('Vdigital vd 0 1.2','Vdigital vd 0 pwl(0 0 1m 1.2 5m 1.2)');uic=' uic'
  else:raise ValueError(case)
  deck+=f'.temp {temp}\n.control\nset num_threads=1\nset numdgt=15\nset wr_singlescale\nset wr_vecnames\ntran 1u 5m 0 1u{uic}\nwrdata wave.tsv v(vref) v(padres) v(pad) v(vdd) i(vmeasure) i(vload) i(vdd) i(vdigital)\necho VREF_DYNAMIC_END\nquit 0\n.endc\n.end\n';(leaf/'fixture.cir').write_text(deck)
  with (leaf/'tool.log').open('x') as log:state=run_bounded(['ngspice','-b','fixture.cir'],log,leaf/'run.json',a.timeout,cwd=leaf,env=dict(os.environ,OMP_NUM_THREADS='1'),metadata={'temperature_C':temp,'case':case,'deck_sha256':hashlib.sha256((leaf/'fixture.cir').read_bytes()).hexdigest()},interval_s=.2)
  wave=leaf/'wave.tsv';rows=[list(map(float,l.split())) for l in wave.read_text().splitlines()[1:]] if wave.exists() else [];text=(leaf/'tool.log').read_text();errs=[l for l in text.splitlines() if re.search(r'(?i)(^Error|fatal|timestep too small|doAnalyses:)',l)];ok=state['returncode']==0 and rows and len(rows[-1])==9 and rows[-1][0]>=.005*(1-1e-9) and all(all(map(math.isfinite,r)) for r in rows) and not errs
  record={'name':name,'case':case,'temperature_C':temp,'solver_status':'passed' if ok else 'failed','endpoint_s':rows[-1][0] if rows else None,'rows':len(rows),'wall_s':state['wall_s'],'errors':errs,'wave_sha256':hashlib.sha256(wave.read_bytes()).hexdigest() if wave.exists() else None,'acceptance_status':'not run: characterization limits not assigned'};results.append(record);(out/'manifest.json').write_text(json.dumps({'scope':prov['scope'],'cases':results},indent=2)+'\n');print(json.dumps(record),flush=True)

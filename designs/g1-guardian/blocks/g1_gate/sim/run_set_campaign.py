#!/usr/bin/env python3
"""Exploratory current-pulse injection in the extracted GATE latch.

Charge is an electrical fixture parameter, not LET or a radiation cross section.
No external FET/pad model;20fF receiver-load assumption on logic outputs.
"""
import argparse,datetime,hashlib,itertools,json,math,re,shutil,subprocess,sys,uuid
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
sys.path.insert(0,str(HERE.parents[1]/'g1_top/sim'))
from run_bounded import run_bounded,atomic_json
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--image-id',required=True);ap.add_argument('--full',action='store_true');ap.add_argument('--timeout',type=float,default=120)
ap.add_argument('--hold-trip',action='store_true',help='keep digital trip asserted after initial latch set')
ap.add_argument('--state',choices=['both','armed','tripped'],default='both');ap.add_argument('--charge-fc',type=float)
a=ap.parse_args()
out=HERE/'campaigns'/('set_'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid.uuid4().hex[:8]);out.mkdir(parents=True,exist_ok=False)
shutil.copyfile(HERE/'.spiceinit',out/'.spiceinit');net=HERE/'postlayout/g1_gate_pex.spice';pdk=Path('/foss/pdks/ihp-sg13g2')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
md=dict(image_id=a.image_id,pdk_commit=(pdk/'COMMIT').read_text().strip(),ngspice_version=subprocess.check_output(['ngspice','-v'],text=True),source_sha256={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),net,HERE/'.spiceinit']},model_sha256={str(p.relative_to(pdk)):sha(p) for p in sorted((pdk/'libs.tech/ngspice/models').rglob('*')) if p.is_file()},scope='Unloaded GATE latch C-PEX;20fF output loads; nominal rails/PVT; imposed current pulses, no LET mapping/radiation-hardness inference.')
results=[];atomic_json(out/'campaign.json',dict(md,status='running',cases=results))
md['options']=vars(a)
configs=itertools.product(['armed','tripped'] if a.state=='both' else [a.state],['n_34','n_35'],[-1,1],[a.charge_fc] if a.charge_fc is not None else [10,100,1000] if a.full else [100])
for state,node,sign,charge in configs:
 name=f'{state}_{node}_{sign}_{charge}fC';wave=out/(name+'.tsv');dp=out/(name+'.cir')
 #10ps ramps plus990ps plateau:integral exactlyI*1ns.
 current=sign*charge*1e-6
 trip='pwl(0 0 1u 0 1.001u 1.2 1.1u 1.2 1.101u 0)' if state=='tripped' else '0'
 if state=='tripped' and a.hold_trip:trip='pwl(0 0 1u 0 1.001u 1.2 3u 1.2)'
 text=f'''* Exploratory latch current pulse, not a particle model
.lib {pdk}/libs.tech/ngspice/models/cornerMOSlv.lib mos_tt
.lib {pdk}/libs.tech/ngspice/models/cornerMOShv.lib mos_tt
.include {net}
.option method=gear reltol=1e-5 abstol=1e-14 vntol=1e-7
.temp 27
Vdd vdd 0 1.2
'''
 text+=f'''Vdda vdda 0 3.3
Ven en 0 pwl(0 0 0.2u 0 0.201u 1.2)
Vtrip td 0 {trip}
XG td 0 0 0 en gate fault tripped vdd vdda 0 g1_gate
Cgate gate 0 20f
Cfault fault 0 20f
Ctrip tripped 0 20f
Iinj 0 xg.{node} pwl(0 0 2u 0 2.00001u {current} 2.001u {current} 2.00101u 0)
.control
set num_threads=1
set numdgt=15
set wr_singlescale
set wr_vecnames
tran 100p 3u 0 100p
wrdata {wave} v(gate) v(fault) v(tripped) v(xg.n_34) v(xg.n_35)
quit
.endc
.end
''';dp.write_text(text)
 with (out/(name+'.log')).open('x') as log:r=run_bounded(['ngspice','-b',str(dp)],log,out/(name+'.json'),a.timeout,cwd=out,metadata=dict(md,case=name,deck_sha256=sha(dp)),interval_s=5)
 result=dict(case=name,completion='failed',classification='not run',wall_s=r['wall_s'],injected_charge_C=sign*charge*1e-15)
 try:
  log=(out/(name+'.log')).read_text()
  if r['status']!='completed' or re.search(r'Timestep too small|simulation aborted|doAnalyses:|^Error:',log,re.I|re.M):raise ValueError('solver incomplete/error')
  rows=[[float(x) for x in line.split()] for line in wave.read_text().splitlines()[1:] if line.strip()]
  if not rows or abs(rows[-1][0]-3e-6)>1e-12 or any(not all(map(math.isfinite,row)) for row in rows):raise ValueError('endpoint/nonfinite')
  pre=min(rows,key=lambda r:abs(r[0]-1.9e-6));expected=state=='tripped'
  if (pre[3]>.6)!=expected:raise ValueError('initial latch state not established')
  end=rows[-1];changed=(end[3]>.6)!=expected
  result.update(completion='passed',classification=('dangerous latch rearm' if expected else 'false trip') if changed else 'recovered/unchanged latch',gate_end_V=end[1],tripped_end_V=end[3],node_min_V=min(min(r[4:6]) for r in rows),node_max_V=max(max(r[4:6]) for r in rows),wave_sha256=sha(wave))
  post=[r for r in rows if r[0]>=2e-6]
  result['gate_core_max_after_injection_V']=max(r[1] for r in post)
 except (OSError,ValueError) as e:result['error']=str(e)
 atomic_json(out/(name+'.acceptance.json'),result);results.append(result);atomic_json(out/'campaign.json',dict(md,status='running',cases=results));print(name,result['completion'],result['classification'],flush=True)
atomic_json(out/'campaign.json',dict(md,status='completed',cases=results));print(out)
if any(r['completion']!='passed' for r in results):raise SystemExit(1)

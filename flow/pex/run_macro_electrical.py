#!/usr/bin/env python3
"""Bounded macro C-PEX electrical characterization; saved data, not sign-off.

Pads are the unchanged detailed sg13g2_IOPadAnalog model on bare terminals.
Route series resistance and external leakage are explicit fixture assumptions.
"""
import argparse,datetime,hashlib,itertools,json,math,re,shutil,subprocess,sys,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];BLOCKS=ROOT/'designs/g1-guardian/blocks'
sys.path.insert(0,str(BLOCKS/'g1_top/sim'))
from run_bounded import run_bounded,atomic_json
PDK=Path('/foss/pdks/ihp-sg13g2');MODELS=PDK/'libs.tech/ngspice/models'
ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('block',choices=['dut','dose','ls']);ap.add_argument('--pex',required=True,type=Path)
ap.add_argument('--image-id',required=True);ap.add_argument('--full',action='store_true')
ap.add_argument('--pads',action='store_true');ap.add_argument('--wire-r',type=float,default=0.001)
ap.add_argument('--load-ff',type=float,default=20);ap.add_argument('--step-ps',type=float,default=100)
ap.add_argument('--route-estimates',type=Path,help='geometry/LEF sensitivity table; not extracted RC')
ap.add_argument('--timeout',type=float,default=120)
ap.add_argument('--rail-policy',choices=['contract','ten-percent-stress'],default='contract')
ap.add_argument('--numerics',choices=['baseline','floor18','floor20'],default='baseline',help='leakage numerical-floor qualification; retains unchanged device models')
ap.add_argument('--zero-gate-only',action='store_true',help='DOSE: start DC at0V and sweep to10mV to isolate off-current solver floor')
a=ap.parse_args();a.pex=a.pex.resolve()
if a.zero_gate_only and a.block!='dose':ap.error('zero-gate-only applies toDOSE')
route_map={}
if a.route_estimates:route_map={r['net']:r for r in json.loads(a.route_estimates.read_text())['routes']}
block=BLOCKS/('g1_ctrl/ls' if a.block=='ls' else 'g1_'+a.block)
out=block/'sim/qualification'/('macro_'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid.uuid4().hex[:8]);out.mkdir(parents=True,exist_ok=False)
shutil.copyfile(BLOCKS/'g1_gate/sim/.spiceinit',out/'.spiceinit')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
md=dict(options={k:str(v) if isinstance(v,Path) else v for k,v in vars(a).items()},image_id=a.image_id,
 pdk_commit=(PDK/'COMMIT').read_text().strip(),ngspice_version=subprocess.check_output(['ngspice','-v'],text=True),
 source_sha256={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),a.pex,out/'.spiceinit']},
 model_sha256={str(p.relative_to(PDK)):sha(p) for p in sorted(MODELS.rglob('*')) if p.is_file()},
 io_sha256=sha(PDK/'libs.ref/sg13g2_io/spice/sg13g2_io.spi'),
 scope='Macro C-PEX and optional detailed bare-pad model; assumed route R/load. Not full assembled RC or physical leakage validation.')
if a.route_estimates:md['route_estimates_sha256']=sha(a.route_estimates)
corners=['tt','ss','ff'] if a.full else ['tt'];temps=[-40,27,85,125] if a.full else [27]
rails=([(1.08,3.0),(1.2,3.3),(1.32,3.6)] if a.rail_policy=='contract' else [(1.08,2.97),(1.2,3.3),(1.32,3.63)]) if a.full else [(1.2,3.3)]
cases=[];atomic_json(out/'campaign.json',dict(md,status='running',cases=cases))
for corner,temp,(vdd,vdda) in itertools.product(corners,temps,rails):
 name=f'{corner}_{temp}_{vdd}_{vdda}';wave=out/(name+'.tsv');dp=out/(name+'.cir')
 hbt={'tt':'typ','ss':'wcs','ff':'bcs'}[corner]
 options={'baseline':'.option method=gear reltol=1e-4 abstol=1e-16 vntol=1e-7 gmin=1e-16','floor18':'.option method=gear reltol=1e-6 abstol=1e-18 vntol=1e-9 gmin=1e-18','floor20':'.option method=gear reltol=1e-7 abstol=1e-20 vntol=1e-10 gmin=1e-20'}
 lines=[f'* {a.block} extracted macro characterization',f'.include {a.pex}',f'.temp {temp}',
 options[a.numerics],
 '.global sub!','Vsub sub! 0 0',f'Vdd vdd 0 {vdd}',f'Vdda vdda 0 {vdda}']
 for lib,c in [('MOSlv','mos_'+corner),('MOShv','mos_'+corner),('HBT','hbt_'+hbt),('RES','res_typ'),('CAP','cap_typ'),('DIO','dio_'+corner)]:
  lines.append(f'.lib {MODELS}/corner{lib}.lib {c}')
 if a.pads:lines.append(f'.include {PDK}/libs.ref/sg13g2_io/spice/sg13g2_io.spi')
 def route(pin):
  if a.pads:lines.append(f'XP_{pin} {pin}_pad {pin}_unused vdd 0 vdda 0 sg13g2_IOPadAnalog')
  net={'b':'hbt_b_bare','c':'hbt_c_bare','e':'hbt_e_bare','g':'g_shared_bare','dh':'d_elt_bare','dl':'d_std_bare'}[pin]
  estimate=route_map.get(net);resistance=estimate['wire_R_ohm_estimate'] if estimate else a.wire_r
  lines.append(f'R_{pin} {pin}_pad {pin}_wire {resistance}')
  if estimate:lines.extend([f'CRa_{pin} {pin}_pad 0 {estimate["ground_C_fF_estimate"]/2}f',f'CRb_{pin} {pin}_wire 0 {estimate["ground_C_fF_estimate"]/2}f'])
  lines.append(f'VM_{pin} {pin}_wire {pin} 0')
 if a.block=='ls':
  lines+=['X1 in out vdd vdda 0 g1_ls_up',f'Cload out 0 {a.load_ff}f',
   f'Vin in 0 pwl(0 0 300n 0 301n {vdd} 600n {vdd} 601n 0 900n 0)']
  control=f'tran {a.step_ps}p 900n';vectors='v(in) v(out) i(vdd) i(vdda)';endpoint=900e-9
 elif a.block=='dut':
  for pin in ['b','c','e']:route(pin)
  lines+=['X1 b c e 0 g1_dut_macro','Vb b_pad 0 0.7','Vc c_pad 0 1.0','Ve e_pad 0 0']
  control='dc Vb 0.30 0.85 0.001';vectors='v(b) v(c) v(e) i(vm_b) i(vm_c) i(vm_e) i(vb) i(vc) i(ve) i(vdd) i(vdda)';endpoint=.85
 else:
  for pin in ['g','dh','dl']:route(pin)
  lines+=['X1 dh dl g 0 g1_dose_macro','Vg g_pad 0 0','Vdh dh_pad 0 1.2','Vdl dl_pad 0 1.2']
  control='dc Vg -0.3 1.2 0.01';vectors='v(g) v(dh) v(dl) i(vm_g) i(vm_dh) i(vm_dl) i(vg) i(vdh) i(vdl) i(vdd) i(vdda)';endpoint=1.2
  if a.zero_gate_only:control='dc Vg 0 .01 .01';endpoint=.01
 lines+=['.control','set num_threads=1','set numdgt=15','set wr_singlescale','set wr_vecnames',control,f'wrdata {wave} {vectors}','quit','.endc','.end']
 dp.write_text('\n'.join(lines)+'\n')
 with (out/(name+'.log')).open('x') as log:r=run_bounded(['ngspice','-b',str(dp)],log,out/(name+'.json'),a.timeout,cwd=out,metadata=dict(md,case=name,deck_sha256=sha(dp)),interval_s=5)
 result=dict(case=name,status=r['status'],wall_s=r['wall_s'],completion='failed',electrical_acceptance='not assessed')
 try:
  log=(out/(name+'.log')).read_text()
  if r['status']!='completed' or re.search(r'Timestep too small|simulation aborted|doAnalyses:|^Error:',log,re.M|re.I):raise ValueError('solver failure/incomplete')
  data=[[float(x) for x in l.split()] for l in wave.read_text().splitlines()[1:] if l.strip()]
  if len(data)<2 or abs(data[-1][0]-endpoint)>1e-10 or any(not all(map(math.isfinite,row)) for row in data):raise ValueError('saved data incomplete/nonfinite')
  result['completion']='passed';result['data_sha256']=sha(wave);result['rows']=len(data)
  if a.block=='ls':
   lo=[r[2] for r in data if 200e-9<=r[0]<=290e-9 or 800e-9<=r[0]<=890e-9];hi=[r[2] for r in data if 500e-9<=r[0]<=590e-9]
   result['metrics']=dict(low_max_V=max(lo),high_min_V=min(hi))
   result['electrical_acceptance']='passed' if max(lo)<.1*vdda and min(hi)>.9*vdda else 'failed'
  else:result['metrics']=dict(last=data[-1],minimum=[min(r[i] for r in data) for i in range(len(data[0]))],maximum=[max(r[i] for r in data) for i in range(len(data[0]))])
 except (OSError,ValueError) as e:result['error']=str(e)
 atomic_json(out/(name+'.acceptance.json'),result);cases.append(result);atomic_json(out/'campaign.json',dict(md,status='running',cases=cases));print(name,result['completion'],result['electrical_acceptance'],r['wall_s'],flush=True)
atomic_json(out/'campaign.json',dict(md,status='completed',cases=cases));print(out)
if any(c['completion']!='passed' or c['electrical_acceptance']=='failed' for c in cases):raise SystemExit(1)

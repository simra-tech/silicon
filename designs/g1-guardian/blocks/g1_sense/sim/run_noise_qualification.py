#!/usr/bin/env python3
"""Bounded simulated SENSE noise with ideal reference/bias, real divider and hold load."""
import argparse,hashlib,json,math,re,subprocess,sys
from pathlib import Path
SIM=Path(__file__).resolve().parent;ROOT=SIM.parents[4];PDK=Path('/foss/pdks/ihp-sg13g2')
sys.path.insert(0,str(SIM.parents[1]/'g1_top/sim'))
from run_bounded import run_bounded
p=argparse.ArgumentParser();p.add_argument('--run-id',required=True);p.add_argument('--image-id',required=True);p.add_argument('--source-run');a=p.parse_args()
out=SIM/'qualification'/a.run_id;out.mkdir(exist_ok=False);(out/'runner.py').write_text(Path(__file__).read_text());source=SIM/'qualification'/a.source_run/'sense_substrate_tied.spice' if a.source_run else SIM/'netlist/g1_sense.spice';(out/'sense.spice').write_text(source.read_text().replace(' sub! ',' vss '))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
assert (PDK/'COMMIT').read_text().strip()=='84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
base=(SIM/'tb_sense.cir').read_text().split('.control')[0]
for k,v in {'VDDA':3.3,'VCM':-.0125,'MOS':'mos_tt','RES':'res_typ','CAP':'cap_typ','TEMP':27}.items():base=base.replace('@@'+k+'@@',str(v))
base=base.replace('.include netlist/g1_sense.spice','.include '+str((out/'sense.spice').relative_to(SIM))).replace('Vsh shp cm dc 0 ac 1','Vsh shp cm dc .025 ac 1')
base+='.option reltol=1e-5 vntol=1e-7 abstol=1e-14\n.control\nset num_threads=1\nset numdgt=15\nset wr_singlescale\nset wr_vecnames\nop\nprint v(isense) v(vped) v(vref_buf) i(vdd)\nnoise v(isense) Vsh dec 100 1 10meg\nsetplot noise1\nwrdata '+str((out/'noise.dat').relative_to(SIM))+' onoise_spectrum inoise_spectrum\nsetplot noise2\nprint onoise_total inoise_total\necho QUALIFICATION_END\nquit 0\n.endc\n.end\n'
dp=out/'noise.cir';dp.write_text(base);(out/'provenance.json').write_text(json.dumps({'arguments':sys.argv[1:],'image_id':a.image_id,'pdk_commit':(PDK/'COMMIT').read_text().strip(),'ngspice':subprocess.check_output(['ngspice','--version'],text=True),'source_hashes':{str(f.relative_to(ROOT)):sha(f) for f in [source,SIM/'tb_sense.cir',Path(__file__)]},'model_hashes':{str(f.relative_to(PDK)):sha(f) for f in (PDK/'libs.tech/ngspice/models').rglob('*') if f.is_file()},'scope':'Simulated TT27C3.3V25mV differential, trueCM0V; ideal VREF/PTAT, actual passive TRIP divider/hold plus300fF load. No BGR noise, pads, mismatch, PEX or clocked comparator kickback. No allocated noise acceptance limit.'},indent=2)+'\n')
with (out/'noise.log').open('x') as log:state=run_bounded(['ngspice','-b',str(dp.relative_to(SIM))],log,out/'watchdog.json',120,cwd=SIM,metadata={'deck_sha256':sha(dp)},interval_s=.5)
log=(out/'noise.log').read_text();errors=[line for line in log.splitlines() if re.search(r'(?i)(^error|timestep too small|doAnalyses:|no such)',line)];rows=[]
if (out/'noise.dat').exists():
 for line in (out/'noise.dat').read_text().splitlines()[1:]:
  try:r=list(map(float,line.split()));assert len(r)==3 and all(map(math.isfinite,r));rows.append(r)
  except (ValueError,AssertionError):pass
status='passed' if state['status']=='completed' and state['returncode']==0 and not errors and len(rows)==701 and rows[-1][0]>=.999e7 and 'QUALIFICATION_END' in log and all(min(r[1:])>=0 for r in rows) else 'failed'
if state['status'] in ['timeout','interrupted']:status='not run to completion'
summary={'status':status,'watchdog_status':state['status'],'wall_s':state['wall_s'],'rows':len(rows),'errors':errors,'noise_acceptance':'not applicable: no allocated block noise limit','bands':[]}
if status=='passed':
 for limit in [1e3,1e5,2e6,1e7]:
  total=[0.,0.]
  for lo,hi in zip(rows,rows[1:]):
   end=min(hi[0],limit)
   if end<=lo[0]:continue
   q=(end-lo[0])/(hi[0]-lo[0])
   for col in [1,2]:
    # Integrate spectral density squared, linearly interpolating PSD at band edge.
    endpsd=lo[col]**2+q*(hi[col]**2-lo[col]**2);total[col-1]+=(lo[col]**2+endpsd)*(end-lo[0])/2
  summary['bands'].append({'frequency_Hz':[1,limit],'output_rms_V':math.sqrt(total[0]),'input_referred_rms_V':math.sqrt(total[1]),'output_divided_by_nominal20_rms_V':math.sqrt(total[0])/20})
 summary['ngspice_integrated_1Hz_10MHz']={k:float(v) for k,v in re.findall(r'^(onoise_total|inoise_total)\s*=\s*([-+0-9.eE]+)',log,re.M)}
(out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))

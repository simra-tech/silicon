#!/usr/bin/env python3
"""Six bounded copied SENSE OP cases with routing-derived supply/return resistance."""
import argparse,concurrent.futures,hashlib,json,math,os,re,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];A=ROOT/'designs/g1-guardian/review/audits';S=ROOT/'designs/g1-guardian/blocks/g1_sense/sim';PDK=Path('/foss/pdks/ihp-sg13g2')
sys.path.insert(0,str(ROOT/'designs/g1-guardian/blocks/g1_top/sim'))
from run_bounded import run_bounded
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--scales',default='0,1,2');a=p.parse_args();a.output=a.output.resolve();a.output.mkdir(exist_ok=False);shutil.copyfile(Path(__file__),a.output/'runner.py');
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
base=S/'qualification/corners-20260921-a/tt_typ_3.3V_27C.cir';net=base.parent/'sense_substrate_tied.spice';budget=A/'supply-budget-20260921-r3/budget.json';d=json.loads(budget.read_text());row=next(r for r in d['loop_R_estimates'] if r['instance']=='i_core.u_sense' and r['supply']=='VDDA' and r['mode']=='mesh_parallel');forward=max(row['supply_R_range_ohm']);back=max(row['return_R_range_ohm']);shutil.copyfile(net,a.output/net.name);shutil.copyfile(S/'.spiceinit',a.output/'.spiceinit')
assert (PDK/'COMMIT').read_text().strip()=='84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
provenance={'scope':'Schematic SENSE with tied resistor substrates, ideal fixed global VREF/PTAT/input/load fixture. Actual routing model single-access max supply/return R applied to SENSE alone, not all chip loads. No PEX/pad/package or reference-interaction qualification.','pdk_commit':(PDK/'COMMIT').read_text().strip(),'ngspice_version':subprocess.check_output(['ngspice','--version'],text=True),'inputs':{str(x.relative_to(ROOT)):sha(x) for x in [base,net,budget,S/'.spiceinit',base.parent/'provenance.json']},'image_id':'sha256:5fd78498e578c6e9ec10828c248ca3790fc88250ff6caf545521b29e448ea3c0','nominal_supply_R_ohm':forward,'nominal_return_R_ohm':back,'return_semantics':'Only XDUT vss moved to local return; external input/reference/load return remain global0. Resistor bodies in copied netlist follow local vss. Bias source remains ideal, supplied from local vdd.','parallel_jobs':1,'threads_per_job':1}
(a.output/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
def run(v,scale):
 name=f'v{v:g}_r{scale:g}';out=a.output/name;out.mkdir();deck=base.read_text().replace('VDDA=3.3',f'VDDA={v:g}').replace('.include qualification/corners-20260921-a/sense_substrate_tied.spice','.include ../sense_substrate_tied.spice').replace('Vdd vdd 0 dc {VDDA}',f'Vdd vdd_source 0 dc {{VDDA}}\nRfeed vdd_source vdd {max(1e-9,forward*scale):.16g}\nVret vss vss_res 0\nRreturn vss_res 0 {max(1e-9,back*scale):.16g}').replace('vref_buf vdd 0 g1_sense','vref_buf vdd vss g1_sense').replace('$&i(vdd)','$&i(vdd) $&i(vret) $&v(vdd) $&v(vss)')
 if scale==0:
  deck=re.sub(r'^Rfeed .+$','Vfeed vdd_source vdd 0',deck,flags=re.M)
  deck=deck.replace('Vret vss vss_res 0','Vret vss 0 0')
  deck=re.sub(r'^Rreturn .+\n','',deck,flags=re.M)
 (out/'fixture.cir').write_text(deck);shutil.copyfile(a.output/'.spiceinit',out/'.spiceinit')
 with (out/'tool.log').open('x') as f:state=run_bounded(['ngspice','-b','fixture.cir'],f,out/'run.json',90,cwd=out,env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1'),metadata={'deck_sha256':sha(out/'fixture.cir'),'rail_V':v,'resistance_scale':scale,'source_R_ohm':max(1e-9,forward*scale),'return_R_ohm':max(1e-9,back*scale)},interval_s=.5)
 log=(out/'tool.log').read_text();rows={}
 for line in log.splitlines():
  if line.startswith('ROW '):
   f=line.split()
   try:
    vals=list(map(float,f[2:]))
    if len(vals)==10 and all(map(math.isfinite,vals)):rows[f[1]]=vals
   except ValueError:pass
 errors=[x for x in log.splitlines() if re.search(r'(?i)(^Error|fatal|timestep too small|doAnalyses:)',x)]
 result={'name':name,'rail_V':v,'resistance_scale':scale,'rows':rows,'columns':['isense_V','vped_V','vref_buf_V','vp_V','vn_V','vped_ref_V','source_current_A','return_current_A','local_vdd_V','local_vss_V'],'errors':errors,'watchdog_status':state['status'],'returncode':state['returncode'],'wall_s':state['wall_s'],'status':'passed' if state['returncode']==0 and len(rows)==9 and not errors and 'QUALIFICATION_END' in log else 'failed'}
 (out/'summary.json').write_text(json.dumps(result,indent=2)+'\n');print(name,result['status'],state['wall_s'],flush=True);return result
results=[run(v,s) for v in [3.3,3.0] for s in map(float,a.scales.split(','))]
(a.output/'summary.json').write_text(json.dumps(results,indent=2)+'\n')
if any(x['status']!='passed' for x in results):raise SystemExit(1)

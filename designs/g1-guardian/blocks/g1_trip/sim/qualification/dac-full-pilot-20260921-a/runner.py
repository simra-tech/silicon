#!/usr/bin/env python3
"""Full DAC-switch/conditioner MC with actual SENSE reference buffer; bounded DC cases."""
import argparse,hashlib,json,math,re,subprocess,sys
from pathlib import Path
SIM=Path(__file__).resolve().parent;ROOT=SIM.parents[4];PDK=Path('/foss/pdks/ihp-sg13g2')
sys.path.insert(0,str(SIM.parents[1]/'g1_top/sim'))
from run_bounded import run_bounded

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--run-id',required=True);p.add_argument('--image-id',required=True);p.add_argument('--seeds',default='51001');p.add_argument('--temps',default='25,125,25');p.add_argument('--codes',default='all');a=p.parse_args()
 out=SIM/'qualification'/a.run_id;out.mkdir(parents=True,exist_ok=False);(out/'runner.py').write_text(Path(__file__).read_text())
 assert (PDK/'COMMIT').read_text().strip()=='84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
 sources=[SIM/'netlist/g1_trip.spice',SIM.parents[1]/'g1_sense/sim/netlist/g1_sense.spice']
 for name,src in zip(['trip','sense'],sources):(out/(name+'.spice')).write_text(src.read_text().replace(' sub! ',' vss '))
 base=(SIM/'tb_kickback.cir').read_text().split('.control')[0].replace('@@VSH@@','.025').replace('mos_tt','mos_tt_mismatch').replace('res_typ','res_typ_mismatch').replace('.temp 27','.temp 25')
 base=base.replace('.include ../../g1_sense/sim/netlist/g1_sense.spice','.include '+str((out/'sense.spice').relative_to(SIM))).replace('.include netlist/g1_trip.spice','.include '+str((out/'trip.spice').relative_to(SIM)))
 base=re.sub(r'^Vclk .+$','Vclk clk 0 dc 0',base,flags=re.M)
 # VREF current measures both real strings plus sense buffer feedback; no ideal buffer substitution.
 prov={'arguments':sys.argv[1:],'image_id':a.image_id,'pdk_commit':(PDK/'COMMIT').read_text().strip(),'ngspice':subprocess.check_output(['ngspice','--version'],text=True),'source_hashes':{str(x.relative_to(ROOT)):sha(x) for x in sources+[Path(__file__),SIM/'tb_kickback.cir']},'model_hashes':{str(x.relative_to(PDK)):sha(x) for x in (PDK/'libs.tech/ngspice/models').rglob('*') if x.is_file()},'scope':'Both full transistor DAC strings, switch trees, level shifters, conditioner/comparators and actual SENSE buffer. Ideal BGR VREF/PTAT. Clock static0; all-code DC only. All explicit schematic MOS/resistor mm_ok=1 retained. No PEX/joint BGR or dynamic settling claim.'}
 (out/'provenance.json').write_text(json.dumps(prov,indent=2)+'\n');summary=[]
 codes=list(range(256)) if a.codes=='all' else list(map(int,a.codes.split(',')))
 for seed in map(int,a.seeds.split(',')):
  ctl=['set num_threads=1','set numdgt=15',f'setseed {seed}','reset'];expected=[]
  for ti,temp in enumerate(map(float,a.temps.split(','))):
   ctl += [f'set temp={temp}',f'alter Iib dc={4.13e-6*(temp+273.15)/300.15:.16g}']
   for code in codes:
    for bit in range(8):
     for prefix in ['Vs','Vh']:ctl.append(f'alter {prefix}{bit} dc={1.2*((code>>bit)&1):g}')
    ctl += ['op',f'echo ROW {ti} {temp} {code} $&v(xt.vth_soft) $&v(xt.vth_hard) $&v(vref_buf) $&v(isense) $&i(vdda)']
    expected.append((ti,code))
   ctl += [f'echo FINGERPRINT {ti}']
   for path,model in [('xt.xdacs.xms7_0a','sg13_hv_nmos'),('xt.xdach.xms7_0b','sg13_hv_nmos'),('xt.xcs.xm1','sg13_lv_nmos'),('xt.xch.xm1','sg13_lv_nmos'),('xs.xref.xm1','sg13_hv_pmos')]:
    for par in ['w','l','delvto','factuo']:ctl.append(f'print @n.{path}.n{model}[{par}]')
   for par in ['nsmm_rsh','nsmm_w','nsmm_l']:ctl.append(f'print @n.xt.xdacs.xru0.nr1[{par}]')
  ctl+=['echo QUALIFICATION_END','quit 0'];name=f'seed{seed}';deck=out/(name+'.cir');deck.write_text(base+'.control\n'+'\n'.join(ctl)+'\n.endc\n.end\n')
  with (out/(name+'.log')).open('x') as log:state=run_bounded(['ngspice','-b',str(deck.relative_to(SIM))],log,out/(name+'.json'),120,cwd=SIM,metadata={'seed':seed,'deck_sha256':sha(deck)},interval_s=.5)
  log=(out/(name+'.log')).read_text();rows=[]
  for line in log.splitlines():
   if line.startswith('ROW '):
    try:row=list(map(float,line.split()[1:]));assert len(row)==8 and all(map(math.isfinite,row));rows.append(row)
    except (ValueError,AssertionError):pass
  errors=[l for l in log.splitlines() if re.search(r'(?i)(^error|timestep too small|doAnalyses:|no such)',l)]
  fps=[]
  for piece in log.split('FINGERPRINT ')[1:]:fps.append(re.findall(r'^(@[^=]+) = (\S+)',piece.split('ROW ')[0],re.M))
  r={'seed':seed,'wall_s':state['wall_s'],'watchdog_status':state['status'],'returncode':state['returncode'],'status':'passed' if len(rows)==len(expected) and not errors and state['returncode']==0 and 'QUALIFICATION_END' in log else 'failed','valid_rows':len(rows),'expected_rows':len(expected),'rows':rows,'errors':errors,'fingerprints':fps,'frozen_fingerprints':bool(fps) and len(fps[0])==23 and all(f==fps[0] for f in fps)}
  if state['status']=='timeout':r['status']='not run to completion'
  r['transfer']=[]
  for ti in sorted({int(x[0]) for x in rows}):
   rr=[x for x in rows if x[0]==ti]
   if len(rr)!=256:continue
   for col,which in [(3,'soft'),(4,'hard')]:
    vs=[x[col] for x in rr];lsb=(vs[-1]-vs[0])/255;dnls=[(v-u)/lsb-1 for u,v in zip(vs,vs[1:])];inls=[(v-vs[0])/lsb-i for i,v in enumerate(vs)]
    r['transfer'].append({'temperature_C':rr[0][1],'temperature_index':ti,'threshold':which,'min_DNL_LSB':min(dnls),'max_abs_INL_LSB':max(map(abs,inls)),'monotonicity_status':'passed' if min(dnls)>-1 else 'failed','lsb_V':lsb,'vref_buffer_min_max_V':[min(x[5] for x in rr),max(x[5] for x in rr)]})
  summary.append(r);(out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(name,r['status'],len(rows),round(r['wall_s'],2),r['frozen_fingerprints'],flush=True)
if __name__=='__main__':main()

#!/usr/bin/env python3
"""Full DAC-switch/conditioner MC with actual SENSE reference buffer; bounded DC cases."""
import argparse,hashlib,json,math,re,subprocess,sys
from pathlib import Path
SIM=Path(__file__).resolve().parent;ROOT=SIM.parents[4];PDK=Path('/foss/pdks/ihp-sg13g2')
sys.path.insert(0,str(SIM.parents[1]/'g1_top/sim'))
from run_bounded import run_bounded

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--run-id',required=True);p.add_argument('--image-id',required=True);p.add_argument('--seeds',default='51001');p.add_argument('--temps',default='25,125,25');p.add_argument('--codes',default='all');p.add_argument('--dc-sweep',action='store_true');p.add_argument('--hold-comparators-reset',action='store_true');p.add_argument('--omit-comparators',action='store_true');p.add_argument('--dac-nodesets',action='store_true');p.add_argument('--tight',action='store_true');p.add_argument('--actual-bgr',action='store_true');a=p.parse_args()
 out=SIM/'qualification'/a.run_id;out.mkdir(parents=True,exist_ok=False);(out/'runner.py').write_text(Path(__file__).read_text())
 assert (PDK/'COMMIT').read_text().strip()=='84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
 sources=[SIM/'netlist/g1_trip.spice',SIM.parents[1]/'g1_sense/sim/netlist/g1_sense.spice']
 for name,src in zip(['trip','sense'],sources):
  net=src.read_text().replace(' sub! ',' vss ')
  if name=='trip' and a.hold_comparators_reset:
   net,n=re.subn(r'^(XCH icmp vth_hard) cmp_clk_n',r'\1 cmp_clk',net,flags=re.M);assert n==1
  if name=='trip' and a.omit_comparators:
   net,n=re.subn(r'^(XC[SH] icmp .+ g1_cmp)$',r'* DC isolation diagnostic omitted comparator: \1',net,flags=re.M);assert n==2
  (out/(name+'.spice')).write_text(net)
 base=(SIM/'tb_kickback.cir').read_text().split('.control')[0].replace('@@VSH@@','.025').replace('mos_tt','mos_tt_mismatch').replace('res_typ','res_typ_mismatch').replace('.temp 27','.temp 25')
 base=base.replace('.include ../../g1_sense/sim/netlist/g1_sense.spice','.include '+str((out/'sense.spice').relative_to(SIM))).replace('.include netlist/g1_trip.spice','.include '+str((out/'trip.spice').relative_to(SIM)))
 base=re.sub(r'^Vclk .+$','Vclk clk 0 dc 0',base,flags=re.M)
 base=base.replace('.save ','.save v(vref_buf) i(vdda) ')
 nodes=(SIM.parents[1]/'g1_sense/sim/tb_sense_mc.cir').read_text().split('.nodeset ',1)[1].split('.option itl1',1)[0]
 if not a.actual_bgr:base += '.nodeset '+nodes.replace('xdut.','xs.').replace('{VPEDN}','1.000755')+'.option itl1=400 itl2=200\n'
 bgr=None
 if a.actual_bgr:
  bgr=SIM.parents[1]/'g1_bgr/sim/qualification/runs/bgr_mc20_20260921_01/pex_mm.spice'
  assert sha(bgr)=='944aaf94b9a005718abd0ebd92956acc99e8cb7a23ec8556d406736f4e8ef6f9'
  (out/'bgr.spice').write_text(bgr.read_text());sources.append(bgr)
  base=re.sub(r'^(Vref|Iib) .+\n','',base,flags=re.M).replace('cap_typ','cap_typ_mismatch')
  base += '.lib /foss/pdks/ihp-sg13g2/libs.tech/ngspice/models/cornerHBT.lib hbt_typ_mismatch\n.include '+str((out/'bgr.spice').relative_to(SIM))+'\nVr4 r4 0 0\nXbgr vdda 0 r4 vref iptat pbias pcasc vbe dvbe g1_bgr\n.global sub!\nVsub sub! 0 0\n.option gmin=1e-15 abstol=1e-14 reltol=1e-5 vntol=1e-7\n'
 if a.dc_sweep:
  assert a.codes=='all'
  for bit in range(8):
   for prefix in ['s','h']:
    base=re.sub(r'^V'+prefix+str(bit)+r' .+$',f'B{prefix}{bit} {prefix}{bit} 0 V=1.2*(floor((v(code)+0.1)/{2**bit})-2*floor((v(code)+0.1)/{2**(bit+1)}))',base,flags=re.M)
  base+='Vcode code 0 0\n'
 if a.dac_nodesets:
  for dac in ['xdacs','xdach']:
   for i in range(529):base+=f'.nodeset v(xt.{dac}.s{i})={1.04*(i+1)/530:.15g}\n'
   for bit in range(8):
    for node,val in [(f'dh{bit}',0),(f'dhn{bit}',3.3),(f'xlu{bit}.n',0),(f'xlu{bit}.nb',3.3),(f'xlu{bit}.ab',1.2)]:base+=f'.nodeset v(xt.{dac}.{node})={val}\n'
 if a.tight:base+='.option gmin=1e-15 reltol=1e-5 vntol=1e-7 abstol=1e-14\n'
 # VREF current measures both real strings plus sense buffer feedback; no ideal buffer substitution.
 prov={'arguments':sys.argv[1:],'image_id':a.image_id,'pdk_commit':(PDK/'COMMIT').read_text().strip(),'ngspice':subprocess.check_output(['ngspice','--version'],text=True),'source_hashes':{str(x.relative_to(ROOT)):sha(x) for x in sources+[Path(__file__),SIM/'tb_kickback.cir']},'model_hashes':{str(x.relative_to(PDK)):sha(x) for x in (PDK/'libs.tech/ngspice/models').rglob('*') if x.is_file()},'actual_bgr':a.actual_bgr,'bgr_source_sha256':sha(bgr) if bgr else None,'git_head':subprocess.check_output(['git','-c','safe.directory=/work','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'comparator_core_omitted_diagnostic':a.omit_comparators,'both_comparators_held_reset':a.hold_comparators_reset,'scope':('Flagged BGR PEX drives actual SENSE VREF/IPTAT; ' if a.actual_bgr else 'Ideal BGR VREF/PTAT; ')+'Both full transistor DAC strings, switch trees, level shifters, conditioner/comparators and actual SENSE buffer. Clock static0; all-code DC only. All explicit schematic MOS/resistor mm_ok=1 retained. SENSE/TRIP schematic; no dynamic settling or full-chip claim.'}
 (out/'provenance.json').write_text(json.dumps(prov,indent=2)+'\n');summary=[]
 codes=list(range(256)) if a.codes=='all' else list(map(int,a.codes.split(',')))
 for seed in map(int,a.seeds.split(',')):
  ctl=['set num_threads=1','set numdgt=15',f'setseed {seed}','reset'];expected=[];sweeps=[]
  for ti,temp in enumerate(map(float,a.temps.split(','))):
   ctl += [f'set temp={temp}']
   if not a.actual_bgr:ctl += [f'alter Iib dc={4.13e-6*(temp+273.15)/300.15:.16g}']
   if a.dc_sweep:
    wave=out/f'seed{seed}_t{ti}.dat';sweeps.append((ti,temp,wave));expected.extend((ti,c) for c in codes)
    ctl += ['dc Vcode 0 255 1','set wr_singlescale','set wr_vecnames',f'wrdata {wave.relative_to(SIM)} v(xt.vth_soft) v(xt.vth_hard) v(vref_buf) v(isense) i(vdda)']
   for code in ([] if a.dc_sweep else codes):
    for bit in range(8):
     for prefix in ['Vs','Vh']:ctl.append(f'alter {prefix}{bit} dc={1.2*((code>>bit)&1):g}')
    ctl += ['op',f'echo ROW {ti} {temp} {code} $&v(xt.vth_soft) $&v(xt.vth_hard) $&v(vref_buf) $&v(isense) $&i(vdda)']
    expected.append((ti,code))
   ctl += [f'echo FINGERPRINT {ti}']
   for path,model in [('xt.xdacs.xms7_0a','sg13_hv_nmos'),('xt.xdach.xms7_0b','sg13_hv_nmos'),('xt.xcs.xm1','sg13_lv_nmos'),('xt.xch.xm1','sg13_lv_nmos'),('xs.xref.xm1','sg13_hv_pmos')]:
    if a.omit_comparators and path.startswith(('xt.xcs','xt.xch.')):continue
    for par in ['w','l','delvto','factuo']:ctl.append(f'print @n.{path}.n{model}[{par}]')
   for par in ['nsmm_rsh','nsmm_w','nsmm_l']:ctl.append(f'print @n.xt.xdacs.xru0.nr1[{par}]')
   if a.actual_bgr:
    for par in ['w','l','delvto','factuo']:ctl.append(f'print @n.xbgr.xm34.nsg13_hv_nmos[{par}]')
    for par in ['nsmm_rsh','nsmm_w','nsmm_l']:ctl.append(f'print @n.xbgr.xr16.nr1[{par}]')
    ctl.append('print @q.xbgr.xq56.qnpn13g2[area]')
  ctl+=['echo QUALIFICATION_END','quit 0'];name=f'seed{seed}';deck=out/(name+'.cir');deck.write_text(base+'.control\n'+'\n'.join(ctl)+'\n.endc\n.end\n')
  with (out/(name+'.log')).open('x') as log:state=run_bounded(['ngspice','-b',str(deck.relative_to(SIM))],log,out/(name+'.json'),120,cwd=SIM,metadata={'seed':seed,'deck_sha256':sha(deck)},interval_s=.5)
  log=(out/(name+'.log')).read_text();rows=[]
  for line in log.splitlines():
   if line.startswith('ROW '):
    try:row=list(map(float,line.split()[1:]));assert len(row)==8 and all(map(math.isfinite,row));rows.append(row)
    except (ValueError,AssertionError):pass
  for ti,temp,wave in sweeps:
   if wave.exists():
    for line in wave.read_text().splitlines():
     try:
      nums=list(map(float,line.split()));assert len(nums)==6 and all(map(math.isfinite,nums));rows.append([ti,temp,*nums])
     except (ValueError,AssertionError):pass
  errors=[l for l in log.splitlines() if re.search(r'(?i)(^error|timestep too small|doAnalyses:|no such)',l)]
  fps=[]
  for piece in log.split('FINGERPRINT ')[1:]:fps.append(re.findall(r'^(@[^=]+) = (\S+)',piece.split('ROW ')[0],re.M))
  r={'seed':seed,'wall_s':state['wall_s'],'watchdog_status':state['status'],'returncode':state['returncode'],'status':'passed' if len(rows)==len(expected) and not errors and state['returncode']==0 and 'QUALIFICATION_END' in log else 'failed','valid_rows':len(rows),'expected_rows':len(expected),'rows':rows,'errors':errors,'fingerprints':fps,'frozen_fingerprints':bool(fps) and len(fps[0])==((15 if a.omit_comparators else 23)+(8 if a.actual_bgr else 0)) and all(f==fps[0] for f in fps)}
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

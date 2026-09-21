#!/usr/bin/env python3
"""Reproducible fine comparator staircase; core source fixture, not loaded-chain yield."""
import argparse,bisect,hashlib,json,math,re,subprocess,sys
from pathlib import Path
SIM=Path(__file__).resolve().parent;ROOT=SIM.parents[4];PDK=Path('/foss/pdks/ihp-sg13g2')
sys.path.insert(0,str(SIM.parents[1]/'g1_top/sim'))
from run_bounded import run_bounded

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--run-id',required=True);p.add_argument('--image-id',required=True);p.add_argument('--seeds',default='61001');p.add_argument('--temps',default='25,-40,125,25');p.add_argument('--cm',default='.5,.75,1.0');p.add_argument('--step-mv',type=float,default=.1);p.add_argument('--range-mv',type=float,default=20);p.add_argument('--source-ohm',type=float,default=1000);p.add_argument('--maxstep-ns',type=float,default=1);p.add_argument('--tight-gear',action='store_true');p.add_argument('--tight-trap',action='store_true');p.add_argument('--netlist',choices=['sch','cell-pex'],default='sch');p.add_argument('--nominal',action='store_true');a=p.parse_args()
 out=SIM/'qualification'/a.run_id;out.mkdir(parents=True,exist_ok=False);(out/'runner.py').write_text(Path(__file__).read_text());src=SIM/'netlist/g1_cmp.spice' if a.netlist=='sch' else SIM.parent/'reports/pex/g1_cmp_cell/g1_cmp_k25d_pex_netlist.spice'
 net=src.read_text();fp_mos=['xm1','xm2','xmtail']
 if a.netlist=='cell-pex':
  (out/'raw_cell_extraction.spice').write_text(net);lines=[]
  for raw in net.splitlines():
   if raw.startswith('+'):lines[-1]+=' '+raw[1:]
   else:lines.append(raw)
  def node(x):return x.replace('\\$','n').replace('VSUBS','vss')
  converted=['* Existing standalone revision1 comparator CC-PEX; no macro routes. Explicit per-finger mismatch flags.','.subckt g1_cmp inp inn clk q qb vdd vss'];nm=nc=0
  for line in lines:
   t=line.split()
   if not t or t[0].startswith(('*','.')):continue
   if t[0].startswith('M$'):
    pd=dict(x.split('=',1) for x in t[6:] if '=' in x);converted.append('XM'+t[0][2:]+' '+' '.join(map(node,t[1:5]))+' '+t[5]+' w='+pd['W'].lower()+' l='+pd['L'].lower()+' ng=1 m=1 mm_ok=1');nm+=1
   elif t[0].startswith('Cext_'):converted.append(t[0]+' '+node(t[1])+' '+node(t[2])+' '+t[3]);nc+=1
   else:raise AssertionError(line)
  assert (nm,nc)==(30,109)
  net='\n'.join(converted+['.ends'])+'\n';fp_mos=['xm6','xm7','xm8','xm9','xm12','xm13','xm14','xm15']
 (out/'cmp.spice').write_text(net)
 assert (PDK/'COMMIT').read_text().strip()=='84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
 prov={'arguments':sys.argv[1:],'image_id':a.image_id,'pdk_commit':(PDK/'COMMIT').read_text().strip(),'ngspice':subprocess.check_output(['ngspice','--version'],text=True),'source_hashes':{str(x.relative_to(ROOT)):sha(x) for x in [src,Path(__file__)]},'model_hashes':{str(x.relative_to(PDK)):sha(x) for x in (PDK/'libs.tech/ngspice/models').rglob('*') if x.is_file()},'netlist':a.netlist,'nominal':a.nominal,'cell_pex_note':'Existing revision1 standalonecell extraction; all30MOS and109parasiticcaps retained. W/L/ng/m model convention matches existing macro converter; AS/AD/PS/PD omitted. Two6um input fingers per side, four4um tail fingers. Independent flags per physicalfinger, no cross-topology seed pairing. Surrounding macro routing not included.' if a.netlist=='cell-pex' else None,'scope':'Comparator schematic all MOS mismatch flags1; input staircase with 1pF and declared equal source resistances. Both inputs change symmetrically around true average common mode. Sample20ns after10MHz strobe. Frozen random parameters across temperature/common mode; no reset between conditions. Not loaded SENSE/DAC chain or PEX.'}
 (out/'provenance.json').write_text(json.dumps(prov,indent=2)+'\n');summary=[]
 diffs=[(-a.range_mv+i*a.step_mv)*.001 for i in range(round(2*a.range_mv/a.step_mv)+1)];pwl=[]
 for i,d in enumerate(diffs):
  if i:pwl.append(f'{i*100e-9-1e-9:.15g} {diffs[i-1]:.15g}')
  pwl.append(f'{i*100e-9:.15g} {d:.15g}')
 end=(len(diffs)-1)*100e-9+90e-9
 for seed in map(int,a.seeds.split(',')):
  base=f'''* Fine symmetric comparator staircase
.lib /foss/pdks/ihp-sg13g2/libs.tech/ngspice/models/cornerMOSlv.lib mos_tt_mismatch
.temp25
.include {str((out/'cmp.spice').relative_to(SIM))}
Vdd vdd 0 1.2
Vcm cm 0 .75
Vod od 0 pwl({' '.join(pwl)})
Ep inp0 0 value={{v(cm)+v(od)/2}}
En inn0 0 value={{v(cm)-v(od)/2}}
Rp inp0 inp {a.source_ohm}
Rn inn0 inn {a.source_ohm}
Cp inp 0 1p
Cn inn 0 1p
Vclk clk 0 pulse(0 1.2 20n .2n .2n 50n 100n)
X1 inp inn clk q qb vdd 0 g1_cmp
Cq q 0 10f
Cqb qb 0 10f
.save v(q) v(qb) v(inp) v(inn) v(clk)
'''.replace('.temp25','.temp 25')
  if a.nominal:base=base.replace('mos_tt_mismatch','mos_tt')
  if a.tight_gear or a.tight_trap:base+='.option reltol=1e-5 vntol=1e-7 abstol=1e-14'+(' method=gear' if a.tight_gear else ' method=trap')+'\n'
  ctl=['set num_threads=1','set numdgt=15',f'setseed {seed}','reset'];cases=[]
  for ti,temp in enumerate(map(float,a.temps.split(','))):
   ctl.append(f'set temp={temp}')
   for cm in map(float,a.cm.split(',')):
    tag=f'seed{seed}_t{ti}_cm{cm}';wave=out/(tag+'.dat');cases.append((tag,temp,cm,wave))
    ctl += [f'alter Vcm dc={cm}',f'tran .2n {end:.15g} 0 {a.maxstep_ns}n','set wr_singlescale','set wr_vecnames',f'wrdata {wave.relative_to(SIM)} v(q) v(qb) v(inp) v(inn) v(clk)',f'echo FINGERPRINT {tag}']
    for mos in fp_mos:
     for par in ['w','l','delvto','factuo']:ctl.append(f'print @n.x1.{mos}.nsg13_lv_nmos[{par}]')
  ctl+=['echo QUALIFICATION_END','quit 0'];name=f'seed{seed}';dp=out/(name+'.cir');dp.write_text(base+'.control\n'+'\n'.join(ctl)+'\n.endc\n.end\n')
  with (out/(name+'.log')).open('x') as log:state=run_bounded(['ngspice','-b',str(dp.relative_to(SIM))],log,out/(name+'.json'),300,cwd=SIM,metadata={'seed':seed,'deck_sha256':sha(dp)},interval_s=.5)
  log=(out/(name+'.log')).read_text();errors=[l for l in log.splitlines() if re.search(r'(?i)(^error|timestep too small|doAnalyses:|no such)',l)];fps=[re.findall(r'^(@[^=]+) = (\S+)',x,re.M) for x in log.split('FINGERPRINT ')[1:]]
  r={'seed':seed,'wall_s':state['wall_s'],'watchdog_status':state['status'],'returncode':state['returncode'],'errors':errors,'fingerprints':fps,'frozen_fingerprints':bool(fps) and len(fps[0])==4*len(fp_mos) and all(f==fps[0] for f in fps),'cases':[]}
  for tag,temp,cm,wave in cases:
   row={'tag':tag,'temp_C':temp,'average_CM_V':cm,'status':'not run'}
   if wave.exists():
    data=[]
    for l in wave.read_text().splitlines():
     try:data.append(list(map(float,l.split())))
     except ValueError:pass
    if data and data[-1][0]>=end*(1-1e-9):
     times=[x[0] for x in data];qs=[]
     for i in range(len(diffs)):
      t=i*100e-9+40e-9;j=bisect.bisect_left(times,t);lo,hi=data[j-1:j+1];qs.append(lo[1]+(t-lo[0])/(hi[0]-lo[0])*(hi[1]-lo[1]))
     highs=[q>.6 for q in qs];first=next((i for i,h in enumerate(highs) if h),None)
     lastlow=next((i for i in range(len(highs)-1,-1,-1) if not highs[i]),None)
     row.update(ambiguity_interval_V=[diffs[first-1],diffs[lastlow+1]] if first is not None and first>0 and lastlow is not None and lastlow+1<len(diffs) else None,status='passed',sampled_q_V=qs,monotonic_decisions=all(not a or b for a,b in zip(highs,highs[1:])),bracketed=first is not None and first>0 and all(highs[first:]),crossing_bracket_V=[diffs[first-1],diffs[first]] if first is not None and first>0 else None)
   r['cases'].append(row)
  r['status']='passed' if state['returncode']==0 and not errors and all(c['status']=='passed' for c in r['cases']) and 'QUALIFICATION_END' in log else 'failed'
  if state['status']=='timeout':r['status']='not run to completion'
  summary.append(r);(out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(name,r['status'],round(r['wall_s'],2),r['frozen_fingerprints'],flush=True)
if __name__=='__main__':main()

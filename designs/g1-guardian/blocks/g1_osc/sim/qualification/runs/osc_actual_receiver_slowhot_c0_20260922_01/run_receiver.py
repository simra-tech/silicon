#!/usr/bin/env python3
"""Actual OSC clock-tree input receivers and internal SPEF; assembly RC estimate.
The next16 buffer outputs use an explicitly swept load, not invented extracted pins.
"""
import argparse,hashlib,json,math,re,shutil,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;DESIGN=HERE.parents[3];PDK=Path('/foss/pdks/ihp-sg13g2');AUDIT=DESIGN/'review/audits'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def crossings(d,col,level,rise=True):
 out=[]
 for a,b in zip(d,d[1:]):
  if (a[col]<level<=b[col]) if rise else (a[col]>level>=b[col]):out.append(a[0]+(level-a[col])*(b[0]-a[0])/(b[col]-a[col]))
 return out
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--run-id',required=True);ap.add_argument('--image-id',required=True);ap.add_argument('--tuple',choices=['nominal','slowcold','slowhot','fastcold'],default='nominal');ap.add_argument('--code',type=int,default=8);ap.add_argument('--r-charge-scale',type=float,default=1);ap.add_argument('--route-scale',type=float,default=1);ap.add_argument('--leaf-load-fF',type=float,default=100);ap.add_argument('--reenable',action='store_true');ap.add_argument('--enable-ramp-us',type=float,default=.001);a=ap.parse_args();assert 0<=a.code<=15 and a.route_scale>0 and 0<=a.leaf_load_fF<=1000 and 0<a.enable_ramp_us<2
 mos,res,cap,vdd,temp={'nominal':('tt','typ','typ',1.2,27),'slowcold':('ss','wcs','wcs',1.08,-40),'slowhot':('ss','wcs','wcs',1.08,125),'fastcold':('ff','bcs','bcs',1.32,-40)}[a.tuple];out=HERE/'runs'/a.run_id;out.mkdir(exist_ok=False);shutil.copy(__file__,out/Path(__file__).name);shutil.copy(HERE.parent/'.spiceinit',out/'.spiceinit');shutil.copy(HERE.parent/'postlayout/g1_osc_pex.spice',out/'baseline.spice');source=(out/'baseline.spice').read_text();lines=[]
 for line in source.splitlines():
  if line.split() and line.split()[0] in ['XR53','XR54','XR55','XR56']:line=line.replace('l=58.5u',f'l={58.5*a.r_charge_scale:g}u')
  lines.append(line)
 (out/'osc.spice').write_text('\n'.join(lines)+'\n');cellsource=PDK/'libs.ref/sg13g2_stdcell/spice/sg13g2_stdcell.spice';shutil.copy(cellsource,out/'stdcells.spice');loadinfo=json.loads((AUDIT/'osc-clock-load-20260922.json').read_text());assert sha(cellsource)==loadinfo['libs.ref/sg13g2_stdcell/spice/sg13g2_stdcell.spice']['sha256']
 for kind in ['input','root_output']:shutil.copy(AUDIT/f'osc-clock-{kind}-20260922-r2.spef-fragment',out/(kind+'.spef'))
 shutil.copy(AUDIT/'osc-clock-load-20260922.json',out/'load_provenance.json');shutil.copy(AUDIT/'osc-route-geometry-20260922-r1.json',out/'assembly_route_geometry.json')
 nodes={};node=lambda s:nodes.setdefault(s,'clk_port' if s=='osc_clk' else 'sp_'+re.sub('[^a-zA-Z0-9]','_',s));network=[];external=[];totals={};receivers=[]
 for kind in ['input','root_output']:
  text=(out/(kind+'.spef')).read_text();mode='';cc=0;rr=0;groundcaps=0
  for line in text.splitlines():
   if line in ['*CONN','*CAP','*RES','*END']:mode=line;continue
   p=line.split()
   if not p:continue
   if mode=='*CONN' and p[0]=='*I' and p[2]=='I' and kind=='root_output':receivers.append(p[1])
   if mode=='*CAP' and p[0].isdigit() and float(p[-1])!=0:
    value=float(p[-1])*1e-12;cc+=value
    if len(p)==3:network.append(f'C_{kind}_{p[0]} {node(p[1])} 0 {value:.15g}');groundcaps+=1
    else:
     network.append(f'C_{kind}_{p[0]} {node(p[1])} {node(p[2])} {value:.15g}');external.append(p[2])
   if mode=='*RES' and p[0].isdigit():network.append(f'R_{kind}_{p[0]} {node(p[1])} {node(p[2])} {p[3]}');rr+=float(p[3])
  totals[kind]={'summed_R_ohm_not_effective_path':rr,'Csum_F':cc,'ground_cap_count':groundcaps}
 assert len(receivers)==16
 for i,n in enumerate(sorted(set(external))):network.append(f'Vquiet_{i} {node(n)} 0 0')
 # Whole-tree assembly R is intentionally a series sensitivity overestimate;
 # port stubs mean it is not an extracted effective driver-to-load path.
 route_R=459.7558*a.route_scale;route_C=60.3853e-15*a.route_scale
 network += [f'Rassembly osc_clk clk_port {route_R:.15g}',f'Cassembly_near osc_clk 0 {route_C/2:.15g}',f'Cassembly_far clk_port 0 {route_C/2:.15g}',f'Xroot {node("*11993:X")} {node("*11993:A")} vddclk 0 sg13g2_buf_16']
 for i,n in enumerate(receivers):
  network.append(f'Xleaf{i} leaf{i} {node(n)} vddclk 0 sg13g2_buf_8')
  if a.leaf_load_fF:network.append(f'Cleaf{i} leaf{i} 0 {a.leaf_load_fF*1e-15:.15g}')
 (out/'clock_load.spice').write_text('* Exact internal SPEF + actual receiver cells; estimatedassembly piRC\n'+'\n'.join(network)+'\n')
 deck=(HERE.parent/'postlayout/tb_osc_pex.cir').read_text().split('.control')[0]
 for k,v in {'MOS':'mos_'+mos,'RES':'res_'+res,'CAP':'cap_'+cap,'TEMP':temp,'VDD':vdd,**{'B'+str(i):(a.code>>i)&1 for i in range(4)}}.items():deck=deck.replace('@@'+k+'@@',str(v))
 deck=deck.replace('.include postlayout/g1_osc_pex.spice','.include osc.spice\n.include stdcells.spice\n.include clock_load.spice').replace('Cload osc_clk 0 50f','* Replaced50fFstand-in withreceiver/SPEF network\nVddclk vddclk 0 dc {VDD}')
 ramp=a.enable_ramp_us;enable=f'Ven en 0 PWL(0 0 0.05u 0 {0.05+ramp:g}u {vdd}'
 enable+=f' 3u {vdd} 3.01u 0 5u 0 {5+ramp:g}u {vdd})' if a.reenable else ')';deck=re.sub(r'^Ven .*$',enable,deck,flags=re.M);stop=10e-6 if a.reenable else 6e-6
 vectors=['v(osc_clk)',f'v({node("*11993:A")})',f'v({node("*11993:X")})','v(en)','i(vdd)','i(vddclk)']+[f'v(leaf{i})' for i in range(16)];deck+='.control\nset num_threads=1\nset numdgt=15\nset wr_singlescale\nset wr_vecnames\n'+f'tran 0.2n {stop:g}\nwrdata receiver.dat '+' '.join(vectors)+'\nquit\n.endc\n.end\n';(out/'receiver.cir').write_text(deck)
 m={'command':sys.argv,'image_id':a.image_id,'ngspice':subprocess.check_output(['ngspice','--version'],text=True),'pdk_commit':(PDK/'COMMIT').read_text().strip(),'model_sha256':{str(p.relative_to(PDK)):sha(p) for p in sorted((PDK/'libs.tech/ngspice/models').glob('*.lib'))},'source_sha256':{p.name:sha(p) for p in out.iterdir() if p.is_file()},'tuple':a.tuple,'code':a.code,'vdd':vdd,'temperature_C':temp,'SPEF':totals,'external_couplings_clamped_quiet':external,'assembly_estimated_series_R_ohm':route_R,'assembly_estimated_C_F':route_C,'leaf_output_assumed_load_fF':a.leaf_load_fF,'limitations':'Rootbuf16+16immediatebuf8 actualPDKcells and internalnominalSPEF. Assemblywhole-tree R insertedseries as explicit sensitivity; not exactrouteRC. One15.4008aF externalcoupling clampedquiet. Furtherclocktree/DFFloadingrepresented by recordedleafoutputcapacitors, not actualfullCTRL. No mismatch orphysicaljitter qualification.','status':'not run'};save=lambda:(out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n');save();start=time.monotonic()
 with (out/'receiver.log').open('w') as log,(out/'receiver.stderr').open('w') as err:
  try:rc=subprocess.run(['ngspice','-b','receiver.cir'],cwd=out,stdout=log,stderr=err,timeout=300).returncode;timed=False
  except subprocess.TimeoutExpired:rc=None;timed=True
 m.update(solver_exit=rc,timed_out=timed,wall_seconds=time.monotonic()-start,status='not run' if timed else 'failed')
 try:
  with (out/'receiver.dat').open() as f:next(f);d=[list(map(float,l.split())) for l in f if l.strip()]
  logs=(out/'receiver.log').read_text()+'\n'+(out/'receiver.stderr').read_text()
  if rc==0 and d and all(len(r)==23 and all(map(math.isfinite,r)) for r in d) and abs(d[-1][0]-stop)<1e-12 and not re.search(r'(?im)^Error|Timestep too small|analysis aborted',logs):
   m['status']='passed';windows=[('steady',2e-6,5.8e-6)] if not a.reenable else [('before_disable',1.8e-6,2.9e-6),('reenabled',7e-6,9.8e-6)];analysis={}
   for label,lo,hi in windows:
    all_edges=[[t for t in crossings(d,col,vdd/2) if lo<=t<=hi] for col in [1,2,3,*range(7,23)]];reference=all_edges[0];analysis[label]={'edge_counts':[len(e) for e in all_edges],'frequency_Hz':(len(reference)-1)/(reference[-1]-reference[0]) if len(reference)>=2 else None,'all_receivers_oscillate':all(len(e)>=4 for e in all_edges)}
   m['windows']=analysis;m['receiver_function_status']='passed' if all(x['all_receivers_oscillate'] for x in analysis.values()) else 'failed'
   pulse=[]
   for col in [1,2,3,*range(7,23)]:
    rises=[t for t in crossings(d,col,vdd/2) if t>=2e-6];falls=crossings(d,col,vdd/2,False);high=[];low=[]
    for left,right in zip(rises,rises[1:]):
     if a.reenable and left<7e-6:continue
     ff=[t for t in falls if left<t<right]
     if ff:high.append(ff[0]-left);low.append(right-ff[0])
    pulse.append({'vector':vectors[col-1],'high_min_s':min(high) if high else None,'low_min_s':min(low) if low else None,'mean_duty_percent':100*sum(high)/(sum(high)+sum(low)) if high else None,'minimum_voltage_V':min(r[col] for r in d),'maximum_voltage_V':max(r[col] for r in d)})
   m['receiver_pulses']=pulse
   if a.reenable:m['disabled_rising_edges']=[sum(3.1e-6<t<4.9e-6 for t in crossings(d,col,vdd/2)) for col in [1,2,3,*range(7,23)]];m['disable_status']='passed' if not any(m['disabled_rising_edges']) else 'failed'
 except (OSError,ValueError,IndexError,StopIteration):pass
 save();print(json.dumps({k:v for k,v in m.items() if k not in ['model_sha256','source_sha256','ngspice']},indent=2))
if __name__=='__main__':main()

#!/usr/bin/env python3
"""Joint extracted BGR/T2F control transitions with actual extracted up-shifters.
Route pi-RC is an explicit LEF/geometry sensitivity estimate, not extracted RC.
"""
import argparse,hashlib,json,math,re,shutil,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;DESIGN=HERE.parents[3];PDK=Path('/foss/pdks/ihp-sg13g2')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def crossings(rows,col,threshold,rise=True):
 result=[]
 for a,b in zip(rows,rows[1:]):
  if (a[col]<threshold<=b[col]) if rise else (a[col]>threshold>=b[col]):
   result.append(a[0]+(threshold-a[col])*(b[0]-a[0])/(b[col]-a[col]))
 return result
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--run-id',required=True);ap.add_argument('--image-id',required=True);ap.add_argument('--case',choices=['nominal','slowcold','fasthot'],default='nominal');a=ap.parse_args()
 h,m,r,c,v,v12,temp={'nominal':('typ','tt','typ','typ',3.3,1.2,27),'slowcold':('wcs','ss','wcs','wcs',3.0,1.08,-40),'fasthot':('bcs','ff','bcs','bcs',3.6,1.32,125)}[a.case]
 assert (PDK/'COMMIT').read_text().strip()=='84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
 out=HERE/'runs'/a.run_id;out.mkdir(parents=True,exist_ok=False)
 sources={'bgr.spice':DESIGN/'blocks/g1_bgr/sim/postlayout/g1_bgr_pex.spice','t2f.spice':HERE.parent/'postlayout/g1_t2f_pex.spice','ls.spice':DESIGN/'blocks/g1_ctrl/ls/reports/flat-pex-20260921T150429Z_42162722/ngspice_pex.spice','route_estimates.json':DESIGN/'review/audits/external-route-rc-estimates-20260921.json','.spiceinit':HERE.parent/'.spiceinit',Path(__file__).name:Path(__file__)}
 for name,p in sources.items():shutil.copy(p,out/name)
 routes=json.loads((out/'route_estimates.json').read_text())['routes'];route_keys={'r4':'i_core.bgr_r4_33','en':'i_core.t2f_en_33','mode':'i_core.t2f_mode_33'}
 deck=f'* Joint BGR/T2F and three extracted up-shifters: {a.case}\n'+''.join(f'.lib {PDK}/libs.tech/ngspice/models/{lib}.lib {corner}\n' for lib,corner in [('cornerHBT','hbt_'+h),('cornerMOShv','mos_'+m),('cornerMOSlv','mos_'+m),('cornerRES','res_'+r),('cornerCAP','cap_'+c)])
 deck+=f'''.include bgr.spice
.include t2f.spice
.include ls.spice
.option gmin=1e-15 abstol=1e-13 reltol=1e-4 vntol=1e-6 method=gear
.temp {temp}
.global sub!
Vsub sub! 0 0
Vdd vdd 0 {v}
Vdd12 vdd12 0 {v12}
Ven en_in 0 pwl(0 0 1u 0 1.01u {v12} 12u {v12} 12.01u 0 18u 0 18.01u {v12})
Vmode mode_in 0 pwl(0 0 30u 0 30.01u {v12} 42u {v12} 42.01u 0)
Vr4 r4_in 0 pwl(0 0 60u 0 60.01u {v12} 72u {v12} 72.01u 0)
Xbgr vdd 0 r4 vref iptat pbias pcasc vbe dvbe g1_bgr
Vload iptat 0 1
Xt2f vdd vdd12 0 pbias pcasc vref en mode fout g1_t2f
Cout fout 0 50f
'''
 selected={}
 for node,key in route_keys.items():
  route=next(x for x in routes if x['net']==key);selected[node]=route;rr=route['wire_R_ohm_estimate'];cc=route['ground_C_fF_estimate']*1e-15/2
  deck+=f'Xls_{node} {node}_in {node}_drv vdd12 vdd 0 g1_ls_up\nRroute_{node} {node}_drv {node} {rr}\nCnear_{node} {node}_drv 0 {cc}\nCfar_{node} {node} 0 {cc}\n'
 vectors=['v(fout)','v(vref)','i(vdd)','i(vdd12)','v(en_in)','v(en)','v(mode_in)','v(mode)','v(r4_in)','v(r4)','v(xt2f.ca1)','v(xt2f.tail1)','v(xt2f.cb1)','v(xt2f.ca2)','v(xt2f.tail2)','v(xt2f.cb2)','v(xt2f.vth)']
 deck+='.control\nset num_threads=1\nset numdgt=15\nset wr_singlescale\nset wr_vecnames\ntran 5n 90u\nwrdata transitions.dat '+' '.join(vectors)+'\nquit\n.endc\n.end\n';(out/'transitions.cir').write_text(deck)
 manifest={'command':sys.argv,'case':a.case,'image_id':a.image_id,'ngspice':subprocess.check_output(['ngspice','--version'],text=True),'pdk_commit':(PDK/'COMMIT').read_text().strip(),'source_sha256':{k:sha(p) for k,p in sources.items()},'deck_sha256':sha(out/'transitions.cir'),'model_sha256':{str(p.relative_to(PDK)):sha(p) for p in sorted((PDK/'libs.tech/ngspice/models').glob('*.lib'))},'selected_routes':selected,'conditions':dict(hbt=h,mos=m,res=r,cap=c,vdda=v,vdd=v12,temperature_C=temp),'watchdog_seconds':300,'status':'not run','limitations':'BGR/T2F/up-shifter C-PEX; route estimates omit viaR/coupling/fill and process/temperature variation; ideal1V IPTAT termination;50fF fout pad stand-in;no mismatch. Receiver-loaded up-shifter result only, not fullCTRL connectivity/CDC proof.'}
 (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');start=time.monotonic();timed=False
 with (out/'transitions.log').open('w') as log:
  try:rc=subprocess.run(['ngspice','-b','transitions.cir'],cwd=out,stdout=log,stderr=subprocess.STDOUT,timeout=300).returncode
  except subprocess.TimeoutExpired:rc=None;timed=True
 manifest.update(solver_exit=rc,timed_out=timed,wall_seconds=time.monotonic()-start,status='not run' if timed else 'failed')
 log=(out/'transitions.log').read_text(errors='replace')
 try:
  with (out/'transitions.dat').open() as f:next(f);d=[list(map(float,line.split())) for line in f if line.strip()]
  if rc==0 and d and all(len(row)==18 and all(map(math.isfinite,row)) for row in d) and abs(d[-1][0]-90e-6)<1e-12 and not re.search(r'(?im)^Error|Timestep too small|analysis aborted',log):
   manifest['status']='passed';edges=crossings(d,1,v12/2);windows={}
   for name,lo,hi in [('initial_ptat',5,11),('reenabled_ptat',22,29),('reference_mode',34,41),('returned_ptat',46,58),('r4_high',64,70),('r4_returned',80,89)]:
    ee=[t for t in edges if lo*1e-6<=t<=hi*1e-6];windows[name]={'rising_edges':len(ee),'status':'passed' if len(ee)>=4 else 'failed','frequency_Hz':(len(ee)-1)/(ee[-1]-ee[0]) if len(ee)>=2 else None}
   manifest['frequency_windows']=windows;off=[row for row in d if 13e-6<=row[0]<=17e-6];manifest['disabled_output_max_V']=max(row[1] for row in off);manifest['disabled_rising_edges']=sum(13e-6<t<17e-6 for t in edges)
   manifest['disable_status']='passed' if manifest['disabled_rising_edges']==0 else 'failed'
   vce=max(abs(row[i]-row[j]) for row in d for i,j in [(11,12),(13,12),(14,15),(16,15)]);manifest.update(hbt_vce_max_V=vce,hbt_vce_status='passed' if vce<=1.6 else 'failed')
   control={}
   for node,ii,oo,events in [('en',5,6,[(1,True),(12,False),(18,True)]),('mode',7,8,[(30,True),(42,False)]),('r4',9,10,[(60,True),(72,False)])]:
    delays=[]
    for when,rise in events:
     inp=[t for t in crossings(d,ii,v12/2,rise) if when*1e-6<=t<(when+1)*1e-6];output=[t for t in crossings(d,oo,v/2,rise) if when*1e-6<=t<(when+1)*1e-6]
     delays.append({'event_us':when,'rise':rise,'delay_s':output[0]-inp[0] if inp and output else None})
    quiet=[row for row in d if all(not(e*1e-6<=row[0]<(e+0.1)*1e-6) for e,_ in events)];valid=all(row[oo]>=.9*v if row[ii]>=.9*v12 else row[oo]<=.1*v for row in quiet)
    control[node]={'events':delays,'logic_status':'passed' if valid and all(x['delay_s'] is not None for x in delays) else 'failed'}
   manifest['up_shifter_receivers']=control
 except (OSError,ValueError,IndexError,StopIteration):pass
 (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest,indent=2))
if __name__=='__main__':main()

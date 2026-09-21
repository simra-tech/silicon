#!/usr/bin/env python3
"""Split actual GATE core/pad currents and test integrated source-node KCL."""
import argparse,bisect,hashlib,json,shutil
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(exist_ok=False);shutil.copyfile(Path(__file__),a.output/'runner.py')
def read(name):
 lines=(a.run/name).read_text().splitlines();return lines[0].split(),[list(map(float,x.split())) for x in lines[1:] if x.strip()]
header,rows=read('split_power_wave.tsv');ph,power=read('power_wave.tsv');assert header==['time','v(vdd)','v(vdda)','i(vcored)','i(vcorea)','i(vpadd)','i(vpada)'];assert len(rows)==len(power);assert all(r[0]==s[0] for r,s in zip(rows,power));times=[r[0] for r in rows];assert all(y>x for x,y in zip(times,times[1:]));assert times[-1]>=12e-6
# time, local VDD/VDDA, coreD/coreA/padD/padA branch draw, sourceD/sourceA draw
rows=[r+[-s[5],-s[6]] for r,s in zip(rows,power)]
def at(t):
 i=bisect.bisect_left(times,t)
 if i<len(times) and times[i]==t:return rows[i]
 assert 0<i<len(times)
 x,y=rows[i-1],rows[i];f=(t-x[0])/(y[0]-x[0]);return [t]+[v+f*(w-v) for v,w in zip(x[1:],y[1:])]
def integral(w,f):return sum((y[0]-x[0])*(f(x)+f(y))/2 for x,y in zip(w,w[1:]))
def stats(lo,hi):
 w=[at(lo)]+[r for r in rows if lo<r[0]<hi]+[at(hi)];rails={}
 for name,v,c in [('core_VDD',1,3),('core_VDDA',2,4),('pad_VDD',1,5),('pad_IOVDD',2,6)]:
  q=integral(w,lambda r:r[c]);energy=integral(w,lambda r:r[c]*r[v]);peak=max(w,key=lambda r:r[c]);rails[name]={'mean_current_A':q/(hi-lo),'charge_C':q,'energy_J':energy,'mean_power_W':energy/(hi-lo),'sampled_peak_current_A':peak[c],'peak_time_s':peak[0],'minimum_current_A':min(r[c] for r in w)}
 kcl={}
 for name,v,core,pad,source in [('VDD',1,3,5,7),('VDDA_plus_IOVDD',2,4,6,8)]:
  qsource=integral(w,lambda r:r[source]);qload=integral(w,lambda r:r[core]+r[pad]);qcap=1e-9*(w[-1][v]-w[0][v]);err=qsource-qload-qcap;kcl[name]={'source_charge_C':qsource,'branch_charge_C':qload,'capacitor_charge_change_C':qcap,'residual_C':err,'relative_to_source_charge':abs(err)/max(abs(qsource),1e-18)}
 return {'start_s':lo,'end_s':hi,'branches':rails,'integrated_KCL':kcl,'total_branch_mean_power_W':sum(r['mean_power_W'] for r in rails.values())}
windows={name:stats(lo,hi) for name,lo,hi in [('disabled',0.,.19e-6),('armed',2e-6,4e-6),('tripped',8e-6,12e-6),('enable_event',.19e-6,1e-6),('trip_event',4.99e-6,6e-6),('whole_trace',0.,12e-6)]}
max_abs=max(abs(x['residual_C']) for w in windows.values() for x in w['integrated_KCL'].values());assert max_abs<1e-13,max_abs
for name,t,before,after in [('enable_event',.2e-6,'disabled','armed'),('trip_event',5e-6,'armed','tripped')]:
 for rail,row in windows[name]['branches'].items():
  base=windows[before]['branches'][rail]['mean_current_A']*(t-windows[name]['start_s'])+windows[after]['branches'][rail]['mean_current_A']*(windows[name]['end_s']-t);row['excess_charge_piecewise_steady_C']=row['charge_C']-base
summary={'scope':'Simulated branch draw at the local nodes of a common 0.5ohm/1nF source fixture. Core VDDA/VDD separated from pad IOVDD/VDD by ideal zero-volt probes. Core VSS and pad IOVSS remain common0. Does not qualify assembled independent rail or return impedance.','inputs':{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in [a.run/n for n in ['split_power_wave.tsv','power_wave.tsv','fixture.cir','run.json','run.log']]},'rows':len(rows),'windows':windows,'KCL_status':'passed','maximum_integrated_KCL_residual_C':max_abs,'KCL_tolerance_C':1e-13,'KCL_method':'Trapezoidal source minus summed branch charge minus 1nF times endpoint voltage change; residual includes saved-wave integration and simulator numerical error.','whole_chip_power_and_IR':'not run'}
(a.output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps({'armed':windows['armed'],'maximum_integrated_KCL_residual_C':max_abs},indent=2))

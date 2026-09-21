#!/usr/bin/env python3
"""Integrate retained GATE source-current traces without launching simulation."""
import argparse,bisect,hashlib,json,shutil
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(exist_ok=False);shutil.copyfile(Path(__file__),a.output/'runner.py')
wave=a.run/'power_wave.tsv';lines=wave.read_text().splitlines();header=lines[0].split();assert header==['time','v(vdd_s)','v(vdda_s)','v(vdd)','v(vdda)','i(vdd)','i(vdda)'],header
rows=[list(map(float,x.split())) for x in lines[1:] if x.strip()];times=[r[0] for r in rows];assert all(y>x for x,y in zip(times,times[1:]));assert times[-1]>=12e-6
for r in rows:r[5]*=-1;r[6]*=-1 # positive means current supplied by ideal source

def at(t):
 i=bisect.bisect_left(times,t)
 if i<len(times) and times[i]==t:return rows[i]
 assert 0<i<len(times)
 x,y=rows[i-1],rows[i];f=(t-x[0])/(y[0]-x[0]);return [t]+[v+f*(w-v) for v,w in zip(x[1:],y[1:])]
def window(lo,hi):return [at(lo)]+[r for r in rows if lo<r[0]<hi]+[at(hi)]
def integral(w,fun):return sum((y[0]-x[0])*(fun(x)+fun(y))/2 for x,y in zip(w,w[1:]))
def stats(lo,hi):
 w=window(lo,hi);rails={}
 for name,src,pin,cur in [('VDD',1,3,5),('VDDA',2,4,6)]:
  charge=integral(w,lambda r:r[cur]);energy=integral(w,lambda r:r[cur]*r[src]);peak=max(w,key=lambda r:r[cur]);minimum=min(w,key=lambda r:r[cur]);
  rails[name]={'mean_source_current_A':charge/(hi-lo),'source_charge_C':charge,'source_energy_J':energy,'mean_source_power_W':energy/(hi-lo),'sampled_peak_source_current_A':peak[cur],'peak_time_s':peak[0],'minimum_source_current_A':minimum[cur],'minimum_pin_voltage_V':min(r[pin] for r in w),'local_1nF_energy_change_J':.5e-9*(w[-1][pin]**2-w[0][pin]**2)}
 return {'start_s':lo,'end_s':hi,'sample_count_including_interpolated_bounds':len(w),'rails':rails,'total_mean_source_power_W':sum(r['mean_source_power_W'] for r in rails.values())}
windows={name:stats(lo,hi) for name,lo,hi in [('disabled',0.,.19e-6),('armed',2e-6,4e-6),('tripped',8e-6,12e-6),('enable_event',.19e-6,1e-6),('trip_event',4.99e-6,6e-6),('whole_trace',0.,12e-6)]}
for event,t,before,after in [('enable_event',.2e-6,'disabled','armed'),('trip_event',5e-6,'armed','tripped')]:
 for rail,data in windows[event]['rails'].items():
  lo,hi=windows[event]['start_s'],windows[event]['end_s'];baseline=windows[before]['rails'][rail]['mean_source_current_A']*(t-lo)+windows[after]['rails'][rail]['mean_source_current_A']*(hi-t)
  data['excess_source_charge_over_piecewise_steady_C']=data['source_charge_C']-baseline
 windows[event]['baseline_definition']=f'{before} mean before {t:g}s, {after} mean after; removes assumed piecewise steady source current'
root=Path(__file__).resolve().parents[4]
cdl=root/'designs/g1-guardian/blocks/g1_padring/netlist/g1_chip_top.cdl'
rail_connections=[line for line in cdl.read_text().splitlines() if line.startswith(('Xpad10_gate ','Xpad11_fault_n '))]
assert len(rail_connections)==2 and all('VDD VSS IOVDD IOVSS' in line for line in rail_connections)
resistor_error={name:max(abs((r[src]-r[pin])/.5-r[cur]) for r in rows) for name,src,pin,cur in [('VDD',1,3,5),('VDDA',2,4,6)]}
assert max(resistor_error.values())<1e-8,resistor_error
inputs={str(f.relative_to(root)) if f.is_absolute() else str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in [wave,a.run/'fixture.cir',a.run/'run.json',a.run/'run.log',cdl]}
result={'scope':'Simulated source currents of actual GATE, 30mA gate pad, 4mA fault pad, vendor-FET fixture at nominal rails/PVT; ideal sources include 0.5ohm series resistor and 1nF local capacitor per rail. External 5V load source power is excluded. Source current is not instantaneous internal device current. No assembled PDN/package qualification.','inputs':inputs,'wave_header':header,'rows':len(rows),'time_s':[times[0],times[-1]],'assembled_rail_connections':rail_connections,'maximum_source_resistor_current_residual_A':resistor_error,'assembled_rail_scope':'Pads use IOVDD/IOVSS while core uses VDDA/VSS; fixture combines both. Do not assign the combined current to the core VDDA mesh.','integration':'Piecewise-linear endpoint interpolation and trapezoidal integration; source current sign inverted so supply draw is positive. Peaks are sampled, not guaranteed continuous extrema.','windows':windows,'whole_chip_power_and_IR':'not run'}
(a.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(windows,indent=2))

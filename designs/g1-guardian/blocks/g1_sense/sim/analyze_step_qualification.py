#!/usr/bin/env python3
"""Characterize last exit from the1% step band, not merely first99% crossing."""
import argparse,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('directory',type=Path);a=p.parse_args()
rows=json.loads((a.directory/'summary.json').read_text());results=[]
for r in rows:
 m=r['measures'];path=a.directory/(r['name']+'_step.dat')
 data=[list(map(float,line.split())) for line in path.read_text().splitlines()[1:] if line.strip()]
 amplitude=m['vhi']-m['vlo'];tolerance=.01*abs(amplitude)
 after=[(t,v) for t,v in data if t>=1e-6]
 outside=[i for i,(t,v) in enumerate(after) if abs(v-m['vhi'])>tolerance]
 last=outside[-1] if outside else -1
 settled=last<len(after)-1
 next_time=after[last+1][0] if settled else None
 results.append({'case':r['name'],'solver_status':r['status'],'gain':r.get('gain'),'bandwidth_Hz':m['f3db'],
 'ac_peaking_dB':m['gpk']-m['g1k'],'step_overshoot_percent':100*(max(v for t,v in after)-m['vhi'])/amplitude,
 'rise_10_90_s':m['t90']-m['t10'],'first99percent_crossing_delay_s':m['tsettle']-1e-6,
 'last1percent_band_exit_delay_s':after[last][0]-1e-6 if last>=0 else None,
 'first_saved_time_after_final1percent_band_entry_delay_s':next_time-1e-6 if settled else None,
 'settled_through_saved_endpoint':settled,'saved_endpoint_s':after[-1][0],
 'last_band_crossing_bracket_s':[after[last][0],next_time] if settled and last>=0 else None})
report={'scope':'Nominal schematic ideal reference/bias step0→50mV at1us.1% of measured step amplitude; saved-point crossing bracket, not phase margin or PEX/corner qualification. Existing tsettle measurement is first99% crossing only.','cases':results}
with (a.directory/'step_characterization.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
print(json.dumps(report,indent=2))

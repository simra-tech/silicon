#!/usr/bin/env python3
"""Report exact completed DC tuples; numerical and electrical status stay separate."""
import argparse,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('directory',type=Path);a=p.parse_args()
raw=json.loads((a.directory/'summary.json').read_text());tuples=[]
for case in raw:
    record={k:case[k] for k in ['name','corner','status','valid_rows','wall_s']}
    if case['status']=='passed':
        rows=case['rows'];gain=[]
        for cm in [-.1,0,.3]:
            gain.append((rows[f't0_c{cm}_s0.05'][0]-rows[f't0_c{cm}_s0'][0])/.05)
        record.update(gain_min=min(gain),gain_max=max(gain),gain_status='passed' if min(gain)>=19.9 and max(gain)<=20.1 else 'failed',
            max_supply_current_A=max(-v[6] for v in rows.values()),min_output_V=min(v[0] for v in rows.values()),max_output_V=max(v[0] for v in rows.values()))
    tuples.append(record)
completed=[r for r in tuples if r['status']=='passed']
r={'coverage':'3 MOS(tt/ss/ff) x3 resistor(typ/bcs/wcs) x3 VDDA(3.0/3.3/3.6) x4 temperatures(-40/27/85/125); actual mean common mode -0.1/0/0.3V x shunt0/25/50mV',
   'ideal_sources':'VREF1.04V; IPTAT4.13uA*(T+273.15)/300.15; no BGR or pads',
   'planned_tuples':108,'attempted':len(raw),'completed':len(completed),'failed':sum(r['status']=='failed' for r in raw),'not_run_to_completion':sum(r['status']=='not run to completion' for r in raw),'not_run':108-len(raw),
   'gain_failures':sum(x['gain_status']=='failed' for x in completed),'tuples':tuples}
if completed:r.update(gain_min=min(x['gain_min'] for x in completed),gain_max=max(x['gain_max'] for x in completed),max_supply_current_A=max(x['max_supply_current_A'] for x in completed))
(a.directory/'analysis.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps({k:v for k,v in r.items() if k!='tuples'},indent=2))

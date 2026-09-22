#!/usr/bin/env python3
"""Retain actual digital clock receiver/SPEF load and assembled-route scope."""
from pathlib import Path
import re,json,hashlib
root=Path(__file__).resolve().parents[4]
p=root/'designs/g1-guardian/blocks/g1_ctrl/flow/runs/run7/final/spef/nom/g1_digital.nom.spef';s=p.read_text();a=root/'designs/g1-guardian/review/audits';mapping=dict(re.findall(r'^\*(\d+) (\S+)$',s,re.M));data={}
assert not (a/'osc-clock-load-20260922.json').exists()
for n,label in [(29,'input'),(2686,'root_output')]:
 b=re.search(r'^\*D_NET \*'+str(n)+r' .*?^\*END',s,re.M|re.S)[0];(a/f'osc-clock-{label}-20260922-r2.spef-fragment').write_text(b+'\n');data[label]={'spef_total_cap_pF':float(b.splitlines()[0].split()[-1]),'connections':[{ 'instance':mapping.get(m[0],m[0]),'pin':m[1],'direction':m[2],'cell':m[3]} for m in re.findall(r'^\*I \*(\d+):(\S+) (\S) \*D (\S+)',b,re.M)]}
lib=Path('/foss/pdks/ihp-sg13g2/libs.ref/sg13g2_stdcell/spice/sg13g2_stdcell.spice');tech=Path('/foss/pdks/ihp-sg13g2/libs.ref/sg13g2_stdcell/lef/sg13g2_tech.lef');t=tech.read_text();data['vias']={}
for name in ['Via2_YX','Via3_XY','Via4_YX']:
 b=re.search(r'^\s*VIA\s+'+name+r'\b(.*?)^\s*END '+name,t,re.M|re.S|re.I)[1];data['vias'][name]=b
for f in [p,lib,tech]:data[str(f.relative_to(root)) if f.is_relative_to(root) else str(f.relative_to('/foss/pdks/ihp-sg13g2'))]={'sha256':hashlib.sha256(f.read_bytes()).hexdigest()}
(a/'osc-clock-load-20260922.json').write_text(json.dumps(data,indent=2)+'\n');print(json.dumps(data,indent=2))

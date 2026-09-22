#!/usr/bin/env python3
"""Evaluate the installed ngspice diode branch equations without changing cards.

Restricted to nominal27C darea/dperim at the SecondaryProtection geometry.
This is a simulator equation diagnostic, not a physical diode model correction.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--pdk',type=Path,default=Path('/foss/pdks/ihp-sg13g2'))
    ap.add_argument('--ngspice-source',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args()
    if a.output.exists():ap.error('preserve existing analysis')
    models=a.pdk/'libs.tech/ngspice/models/diodes.lib'
    source=a.ngspice_source/'src/spicelib/devices/dio'
    s=models.read_text()
    constants=a.ngspice_source/'src/include/ngspice/const.h'
    constants_text=constants.read_text()
    boltz=float(re.search(r'#define CONSTboltz\s+(\S+)',constants_text)[1])
    charge=float(re.search(r'#define CHARGE\s+(\S+)',constants_text)[1])
    vt=boltz/charge*300.15
    rows=[]
    for name,area in [('darea',3.1*.64),('dperim',(3.1+.64)*2)]:
        line=re.search(r'^\.model\s+'+name+r'\s+D\s.*$',s,re.I|re.M)[0]
        p={k.lower():float(v) for k,v in re.findall(r'(\w+)\s*=\s*([-+0-9.eE]+)',line)}
        assert p['tnom']==27
        csat=p['is']*area;cbv=p['ibv'];nbv=p['nbv'];bv=p['bv']
        x=bv-nbv*vt*math.log(1+cbv/csat)
        for _ in range(25):x=bv-nbv*vt*math.log(cbv/csat+1-x/vt)
        v=-3*p['n']*vt
        rec=p.get('isr',0)*area*(math.exp(v/(p.get('nr',2)*vt))-1)*((1-v/p['vj'])**2+.005)**(p['m']/2)
        forward=csat*(math.exp(v/(p['n']*vt))-1)+rec
        reverse=-csat*math.exp(-(x+v)/(nbv*vt))+rec
        rows.append(dict(model=name,area_factor=area,parameters=p,effective_breakdown_V=x,
            branch_voltage_V=v,current_forward_side_A=forward,current_breakdown_side_A=reverse,
            branch_current_jump_A=reverse-forward,negative_effective_breakdown=x<0))
    report=dict(scope=__doc__,pdk_commit=(a.pdk/'COMMIT').read_text().strip(),diodes_sha256=sha(models),
        source_sha256={p.name:sha(p) for p in [source/'dioload.c',source/'diotemp.c',source/'diosetup.c',constants]},
        assumptions='ngspice level1, nominal27C, no selfheat; default NR2 verified in diosetup.c; GMIN term cancels across branch; no model edits.',
        references=['https://ngspice.sourceforge.io/docs/ngspice-46-manual.pdf','https://github.com/IHP-GmbH/IHP-Open-PDK/issues/921'],results=rows)
    a.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(rows,indent=2))

if __name__=='__main__':main()

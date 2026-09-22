#!/usr/bin/env python3
"""Preserve completed/partial startup diagnostics without promoting failed runs."""
import hashlib
import json
import math
import re
from pathlib import Path

HERE=Path(__file__).resolve().parent
RUN='bgr_loop24q4_hv06_startup2_20260922_r3'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rows(p):return [[float(v) for v in line.split()] for line in p.read_text().splitlines()[1:] if line.strip()]
def main():
    directory=HERE/'runs'/RUN;m=json.loads((directory/'manifest.json').read_text())
    result={'run':RUN,'recorded_campaign_status':m['status'],'manifest_sha256':sha(directory/'manifest.json'),
            'candidate_sha256':m['candidate_sha256'],'cases':[],'status':'diagnostic only; original statuses preserved'}
    indices={n:i+1 for i,n in enumerate(m['terminal_nodes'])}
    for c in m['cases']:
        name=c['name'];data=rows(directory/(name+'.dat'));term=rows(directory/(name+'_terminals.dat'))
        logs=(directory/(name+'.log')).read_text()+'\n'+(directory/(name+'.stderr.log')).read_text()
        assert len(data)==len(term)>0 and all(math.isfinite(v) for row in data+term for v in row)
        assert [r[0] for r in data]==[r[0] for r in term] and all(b[0]>a[0] for a,b in zip(data,data[1:]))
        extrema=[]
        for d in m['devices']:
            if d['instance'] not in ['XM29','XM31','XM32','XM33'] and not d['instance'].startswith('XQ'):continue
            pairs=['gs','gd','ds'] if d['instance'].startswith('XM') else ['ce']
            for pair in pairs:
                p,n=[d['terminals'][x] for x in pair]
                values=[(r[indices[p]] if p!='0' else 0)-(r[indices[n]] if n!='0' else 0) for r in term]
                index=max(range(len(values)),key=lambda i:abs(values[i]))
                extrema.append({'instance':d['instance'],'pair':pair,'max_abs_V':abs(values[index]),'signed_V':values[index],'time_s':term[index][0]})
        result['cases'].append({'name':name,'original_status':c['status'],'solver_exit':c['solver_exit'],
            'saved_rows':len(data),'first_saved_s':data[0][0],'last_saved_s':data[-1][0],
            'required_endpoint_s':3*c['startup'][1],'endpoint_reached':abs(data[-1][0]-3*c['startup'][1])<1e-9,
            'data_terminal_grids_exact_and_strictly_increasing':True,
            'unobserved_initial_interval_s':[0,data[0][0]],
            'last_VREF_V':data[-1][1],'last_IPTAT_A':data[-1][2],
            'observed_current_peak_A':max(-r[3] for r in data),
            'temperature_limiter_NaN_present':'temperature limiting function received NaN' in logs,
            'solver_failure_lines':[line for line in logs.splitlines() if re.search('Timestep too small|trouble with|simulation.*aborted',line)],
            'observed_terminal_extrema_only':extrema,
            'waveform_sha256':sha(directory/(name+'.dat')),'terminal_waveform_sha256':sha(directory/(name+'_terminals.dat')),
            'scope':'Observed saved interval only; no unsaved initial or post-abort peak/settling bound. Failed original remains failed.'})
    out=HERE/'short_hv_startup_diagnostics_20260922_r3.json';assert not out.exists()
    out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({**result,'cases':[{k:v for k,v in c.items() if k!='observed_terminal_extrema_only'} for c in result['cases']]}))
if __name__=='__main__':main()

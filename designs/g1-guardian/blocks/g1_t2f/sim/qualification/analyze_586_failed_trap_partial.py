#!/usr/bin/env python3
"""Observe exported partial failed-trap data, never relabel original2us contract."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import numpy as np
from prepare_586_fast76002_method import HERE,GEAR,sha
from run_bgr_substitution_draw_audit import read_group
from wave_archive import open_wave
from analyze_586_fast76002_method import edges


def load(path):
    with open_wave(path,'rb') as stream:blob=stream.read()
    lines=blob.splitlines();names=lines[0].decode().split()
    data=np.array([list(map(float,line.split())) for line in lines[1:] if line.strip()])
    assert len(names)==13 and data.shape[1]==13 and np.isfinite(data).all() and np.all(np.diff(data[:,0])>0)
    return blob,names,data


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();assert not a.output.exists()
    run=HERE/'runs/t2f586-fast76002-trap2us-20260923-a'
    row,=json.loads((run/'summary.json').read_text());prep=json.loads((run/'preparation.json').read_text())
    assert row['control_status']=='failed' and row['runtime']['status']=='completed'
    assert len(row['errors'])==1 and 'Timestep too small' in row['errors'][0]
    log=(run/'run.log').read_text()
    before={tag:read_group(log,'P0_'+tag+'_BEFORE',keys) for tag,keys in prep['groups'].items()}
    after={tag:read_group(log,'P0_'+tag+'_AFTER',keys) for tag,keys in prep['groups'].items()}
    gear,=json.loads((GEAR/'summary.json').read_text())
    assert sum(map(len,before.values()))==3180 and before==after==prep['required_before3180']==gear['parameters_before']==gear['parameters_after']
    assert (run/'probe.cir').read_text().replace('method=trap','method=gear')==(GEAR/'probe.cir').read_text()
    assert all(sha(run/n)==sha(GEAR/n) for n in ['bgr.spice','t2f.spice','.spiceinit','population_inventory.json'])
    old,names,x=load(GEAR/'phase0.dat');new,other,y=load(run/'phase0.dat');assert names==other
    endpoint=float(y[-1,0]);assert 0<endpoint<2e-6 and x[-1,0]==2e-6
    union=np.unique(np.concatenate([x[x[:,0]<=endpoint,0],y[:,0]]))
    assert union[0]>=max(x[0,0],y[0,0]) and union[-1]<=min(x[-1,0],y[-1,0])
    differences={}
    for i,name in enumerate(names[1:],1):
        delta=np.interp(union,y[:,0],y[:,i])-np.interp(union,x[:,0],x[:,i])
        differences[name]=dict(unit='A' if name.startswith('i(') else 'V',max_abs=float(np.abs(delta).max()),
            rms=float(np.sqrt(np.mean(delta**2))),scope='unweightedcommon-overlap uniongrid linearinterpolation only')
    events={}
    for label,rising in [('rising',True),('falling',False)]:
        old_edges=[t for t in edges(x,rising) if t<=endpoint];new_edges=edges(y,rising)
        events[label]=dict(gear_s=old_edges,trap_s=new_edges,count_exact=len(old_edges)==len(new_edges),
            index_paired_delta_s=[b-a for a,b in zip(old_edges,new_edges)])
    initial,positive=log.split('Initial Transient Solution',1)
    result=dict(status='passed finite-partial observation audit; original trap diagnostic FAILED',
        original_failure=row['errors'],original_watchdog_s=600,original_wall_s=row['runtime']['wall_s'],
        failed_contract_endpoint_s=2e-6,exported_partial_endpoint_s=endpoint,partial_rows=len(y),
        full3180_before_after='passed exact Gear/originaldraw despite abortedTRAN',
        parameter_vector_sha256=hashlib.sha256(json.dumps(before,sort_keys=True).encode()).hexdigest(),
        full2us_wave_comparison='not run; trap did not reach2us',
        exact_complete_decoded_wave_comparison='failed; unequal endpoint/grid/bytes, no waiver',
        common_overlap_0p6V_events=events,common_overlap_vector_differences=differences,
        partial_HBT_external_VCE_max_V=float(max(np.abs(y[:,i]-y[:,j]).max() for i,j in [(7,8),(9,8),(10,11),(12,11)])),
        partial_positive_interval_s=dict(minimum=float(np.diff(y[:,0]).min()),median=float(np.median(np.diff(y[:,0]))),maximum=float(np.diff(y[:,0]).max())),
        warnings_before_initial_transient=len(re.findall('warning',initial,re.I)),warnings_after_initial_transient=len(re.findall('warning',positive,re.I)),
        decoded_partial_sha256=hashlib.sha256(new).hexdigest(),gear_decoded_sha256=hashlib.sha256(old).hexdigest(),
        receipts_sha256={n:sha(run/n) for n in ['summary.json','preparation.json','provenance.json','probe.cir','run.log','run.json','phase0.dat.gz','phase0.dat.archive.json']},
        analyzer_sha256=sha(Path(__file__)),
        scope='Failed same-input Gear-to-trap diagnostic; completedpost-abort queries and actualpartialvectors only. Namedtroubleinstance is solver diagnostic, not proven causal device defect. No32usretry, solveradoption, threshold/refit/sourcechange, populationrelease or fullwavequalification.')
    a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['common_overlap_vector_differences','receipts_sha256']},indent=2))


if __name__=='__main__':main()

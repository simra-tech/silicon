#!/usr/bin/env python3
"""Audit the frozen coordinated candidate's nominal design-control stage."""
import argparse
import hashlib
import json
import math
import re
from pathlib import Path

HERE=Path(__file__).resolve().parent
NAME='bgr_loop24_qref4_r253p465'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--nominal-run',required=True)
    ap.add_argument('--probe-run',required=True)
    ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args()
    assert not a.output.exists()
    candidate=HERE/'candidates'/NAME
    frozen=json.loads((candidate/'manifest.json').read_text())
    npath=HERE/'runs'/a.nominal_run
    ppath=HERE/'runs'/a.probe_run
    nominal=json.loads((npath/'manifest.json').read_text())
    probe=json.loads((ppath/'manifest.json').read_text())
    n=nominal['cases'][0]
    parameters=frozen['fingerprint_parameters']
    fp=n['fingerprints']
    assert len(nominal['cases'])==1 and n['status']=='passed' and not n['mm']
    assert nominal['pex_sha256']==frozen['candidate_sha256']==sha(candidate/(NAME+'.spice'))
    assert n['fingerprint_parameters']==parameters and len(parameters)==2842
    assert len(fp)==5684 and fp[:2842]==fp[2842:] and all(math.isfinite(float(v)) for v in fp)
    assert len(probe['cases'])==2 and all(c['status']=='passed' for c in probe['cases'])
    for key in ['pdk_commit','image_id','model_sha256','osdi_sha256']:
        assert nominal[key]==probe[key],key
    assert sha(npath/'.spiceinit')==sha(ppath/'.spiceinit')==probe['spiceinit_sha256']
    baseline,current=probe['cases']
    assert baseline['source_sha256']==frozen['baseline_sha256']
    assert current['source_sha256']==frozen['candidate_sha256']
    rows=[[float(x) for x in line.split()] for line in (npath/'nominal.dat').read_text().splitlines()[1:] if line.strip()]
    assert len(rows)==34 and [r[0] for r in rows]==list(range(-40,126,5))
    assert all(len(r)==12 and all(math.isfinite(x) for x in r) for r in rows)
    row25=next(r for r in rows if r[0]==25)
    maxpairs={}
    literal=[]
    limits={'gs':3.0,'gd':3.0,'gb':3.0,'ds':3.0,'db':1.6,'sb':1.6}
    for item in current['external_terminal_voltages']:
        kind=item['instance'][:2];pair=item['pair'];key=kind+'_'+pair
        if key not in maxpairs or abs(item['voltage_V'])>abs(maxpairs[key]['voltage_V']):maxpairs[key]=item
        limit=limits[pair] if kind=='XM' else 1.6 if kind=='XQ' and pair=='ce' else None
        if limit is not None and abs(item['voltage_V'])>limit+1e-9:literal.append(dict(item,literal_model_limit_V=limit))
    grouped={}
    for name, (prefix,ids,copies) in frozen['mapping_groups'].items():
        if prefix!='XQ':continue
        roots={'@q.xbgr.xq'+str(i)+'.' for i in ids}
        unitrows=[r for r in probe['unit_current_comparisons'] if any(r['baseline_parameter'].startswith(p) for p in roots)]
        assert len(unitrows)==len(ids)*copies
        grouped[name]={'unit_count':len(unitrows),'max_absolute_relative_IC_delta':max(abs(r['relative_delta']) for r in unitrows),'worst_unit':max(unitrows,key=lambda r:abs(r['relative_delta']))}
    warning_audit={}
    for label,path in [('nominal',npath/'nominal'),('baseline_OP',ppath/'baseline'),('candidate_OP',ppath/'candidate')]:
        log=Path(str(path)+'.log').read_text()
        stderr=Path(str(path)+'.stderr.log').read_text()
        text=log+'\n'+stderr
        warning_audit[label]={'log_sha256':sha(Path(str(path)+'.log')),
            'stderr_sha256':sha(Path(str(path)+'.stderr.log')),
            'warning_line_count':sum('warning' in line.lower() for line in text.splitlines()),
            'r3_internal_vmax_warning_count':text.count('voltage is greater than specified by vmax'),
            'temperature_limiter_NaN_present':'temperature limiting function received NaN' in text,
            'dynamic_gmin_stepping_completed':'Dynamic gmin stepping completed' in text,
            'solver_error_pattern_present':bool(re.search(r'(?im)^Error|analysis aborted|Timestep too small',text)),
            'scope':'Final finite exports do not erase intrinsic-model warnings; internal trial-state attribution not run.'}
    out={'status':'passed numerical/source/inventory audit; adoption not run',
         'candidate_sha256':frozen['candidate_sha256'],
         'nominal_manifest_sha256':sha(npath/'manifest.json'),'probe_manifest_sha256':sha(ppath/'manifest.json'),
         'all_parameter_count':2842,'pre_post_temperature_fingerprints':'passed byte-string equality',
         'nominal_TC_ppm_C':n['tc_ppm_C'],'nominal_TC_status':n['tc_status'],
         'nominal_VREF25_V':row25[1],'nominal_IPTAT25_A':row25[2],'nominal_supply25_A':-row25[3],
         'nominal_power25_W':-row25[3]*3.3,
         'baseline_OP_supply25_A':baseline['supply_current_A'],'candidate_OP_supply25_A':current['supply_current_A'],
         'nominal_sweep_vs_OP_VREF_delta_V':row25[1]-current['node_voltages_V']['vref'],
         'nominal_sweep_vs_OP_IPTAT_delta_A':row25[2]-current['iptat_A'],
         'unit_current_groups':grouped,'maximum_absolute_unit_IC_relative_delta':probe['maximum_absolute_unit_IC_relative_delta'],
         'maximum_external_terminal_by_kind_pair':maxpairs,'literal_model_exceedances':literal,
         'model_warning_audit':warning_audit,'model_validity_status':'unqualified; retained HV geometry/voltage and intrinsic-model warnings',
         'short_HV_NMOS_XM31_XM33':[r for r in current['external_terminal_voltages'] if r['instance'] in ['XM31','XM33'] and r['pair'] in ['gs','gd','ds']],
         'wall_seconds':{'nominal':n['wall_seconds'],'probe_sum':sum(c['wall_seconds'] for c in probe['cases'])},
         'remaining_gates':['HV short-length model scope unresolved; literal PSP MAX not adopted foundry reliability limit','startup/adverse/load/stability/noise/PSRR not run on this source','all-parameter mismatch qualification and independent MC not run','new physical fit/layout/DRC/LVS/via-current/fill/PEX not run','downstream source-specific calibration requalification not run'],
         'scope':'Nominal numerical, TC and quantified density diagnostics only. Unit-current preservation not extrapolated to mismatch yield or spatial independence.'}
    a.output.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({k:v for k,v in out.items() if k not in ['maximum_external_terminal_by_kind_pair','literal_model_exceedances']}))

if __name__=='__main__':main()

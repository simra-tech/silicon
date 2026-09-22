#!/usr/bin/env python3
"""Exact parent/derivative source, input-deck and2842-parameter nominal audit."""
import hashlib
import json
import math
from pathlib import Path

HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read_rows(p):return [[float(v) for v in line.split()] for line in p.read_text().splitlines()[1:] if line.strip()]

def main():
    olddir=HERE/'runs/bgr_loop24q4_nominal_20260922_r1'
    newdir=HERE/'runs/bgr_loop24q4_hv06_nominal_20260922_r1'
    old=json.loads((olddir/'manifest.json').read_text());new=json.loads((newdir/'manifest.json').read_text())
    om=old['cases'][0];nm=new['cases'][0]
    candidate=HERE/'candidates/bgr_loop24_qref4_r253p465_hv06'
    frozen=json.loads((candidate/'manifest.json').read_text())
    assert len(old['cases'])==len(new['cases'])==1 and om['status']==nm['status']=='passed'
    assert new['pex_sha256']==frozen['candidate_sha256']==sha(candidate/'bgr_loop24_qref4_r253p465_hv06.spice')
    assert old['pex_sha256']==frozen['parent_source_sha256']
    for key in ['image_id','pdk_commit','model_sha256','osdi_sha256','solver']:
        assert old[key]==new[key],key
    assert sha(olddir/'.spiceinit')==sha(newdir/'.spiceinit')
    assert sha(olddir/'nominal.cir')==sha(newdir/'nominal.cir')
    assert om['fingerprint_parameters']==nm['fingerprint_parameters']==frozen['fingerprint_parameters']
    params=nm['fingerprint_parameters'];assert len(params)==len(set(params))==2842
    assert len(nm['fingerprints'])==5684 and nm['fingerprints'][:2842]==nm['fingerprints'][2842:]
    changes=[{'parameter':p,'before':a,'after':b} for p,a,b in zip(params,om['fingerprints'][:2842],nm['fingerprints'][:2842]) if a!=b]
    assert {row['parameter'] for row in changes}=={'@n.xbgr.xm31.nsg13_hv_nmos[l]','@n.xbgr.xm33.nsg13_hv_nmos[l]'}
    assert all(row['before']=='5.000000000000000e-07' and row['after']=='6.000000000000001e-07' for row in changes)
    before=read_rows(olddir/'nominal.dat');after=read_rows(newdir/'nominal.dat')
    assert len(before)==len(after)==34 and [r[0] for r in after]==list(range(-40,126,5))
    assert [r[0] for r in before]==[r[0] for r in after]
    assert all(len(r)==12 and all(map(math.isfinite,r)) for r in after)
    columns=['VREF_V','IPTAT_A','supply_branch_A','VBE_V','dVBE_V','PBIAS_V','PCASC_V','c2_V','VBE3_V','vd1_V','vd2_V']
    delta={name:max(abs(b[i]-a[i]) for a,b in zip(before,after)) for i,name in enumerate(columns,1)}
    row25=next(r for r in after if r[0]==25)
    logs=(newdir/'nominal.log').read_text()+'\n'+(newdir/'nominal.stderr.log').read_text()
    result={'status':'passed nominal source/input/parameter audit; startup not run',
            'candidate_sha256':new['pex_sha256'],'parent_sha256':old['pex_sha256'],
            'nominal_manifest_sha256':sha(newdir/'manifest.json'),'parent_nominal_manifest_sha256':sha(olddir/'manifest.json'),
            'exact_same_input_deck_sha256':sha(newdir/'nominal.cir'),
            'parameter_count':2842,'pre_post_temperature_freeze':'passed','only_changed_parameters':changes,
            'length_readback_note':'SPICE .6u reports6.000000000000001e-7m, one binary rounding step from Python literal.6e-6. Initial analysis literal-float equality rejected this; corrected check freezes actual reported strings. All2842 pre/post strings remain exactly equal and all2840 non-target parent values identical.',
            'nominal_TC_ppm_C':nm['tc_ppm_C'],'nominal_TC_status':nm['tc_status'],'nominal_VREF25_V':row25[1],
            'nominal_IPTAT25_A':row25[2],'nominal_supply25_A':-row25[3],'nominal_power25_W':-row25[3]*3.3,
            'full_temperature_max_absolute_output_deltas_from_parent':delta,
            'wall_seconds':nm['wall_seconds'],'temperature_limiter_NaN_present':'temperature limiting function received NaN' in logs,
            'r3_internal_vmax_warning_count':logs.count('voltage is greater than specified by vmax'),
            'scope':'Only original XM31/XM33 L.5→.6um. Explicitjunction A/P retained after stockisolatedgeometry check. No modelcard/othergeometry change. Addresses27C3.3V gate-lengthcondition only, not3.6V/125C reliability or newwirePEX/fit/adoption. Directunit-density25C probe on derivative not run.'}
    out=HERE/'short_hv_nominal_audit_20260922_r1.json';assert not out.exists()
    out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))

if __name__=='__main__':main()

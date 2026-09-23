#!/usr/bin/env python3
"""Algebraic closed-loop error observations; not intrinsic OTA offset extraction."""
import argparse,json,math
from pathlib import Path
from run_rz100_mc_control import parse,electrical,sha
from prepare_rz100_dc_grid import SOURCE

def components(row,cal,residual):
    # Saved order: ISENSE, VPED, VREF_BUF, main VP, main VN, VPED_REF, I(VDD).
    ratio=51/53
    ref=lambda r:1.04-r[2]
    buf=lambda r:r[5]-r[1]
    main=lambda r:r[3]-r[4]
    divider=lambda r:r[5]-ratio*r[2]
    terms=dict(reference_buffer_drift_V=-ratio*(ref(row)-ref(cal))/20,
        pedestal_buffer_drift_V=-(buf(row)-buf(cal))/20,
        divider_remainder_V=(divider(row)-divider(cal))/20,
        main_closed_loop_difference_drift_V=-21*(main(row)-main(cal))/20)
    pedestal=(row[1]-cal[1])/20
    assert math.isclose(sum(terms[k] for k in ['reference_buffer_drift_V','pedestal_buffer_drift_V','divider_remainder_V']),pedestal,abs_tol=1e-15)
    terms['main_network_remainder_V']=residual-sum(terms.values())
    assert math.isclose(sum(terms.values()),residual,abs_tol=1e-15)
    return dict(three_OTA_closed_loop_input_differences_V=dict(main=main(row),reference=ref(row),pedestal=buf(row)),
        residual_decomposition_input_referred_V=terms,residual_V=residual)

def controls():
    c=[1.5,1.,1.04,.2,.2,1.,-.001]
    assert all(v==0 for v in components(c,c,0)['residual_decomposition_input_referred_V'].values())
    r=c.copy();r[1]+=.002
    p=components(r,c,.0001)['residual_decomposition_input_referred_V']
    assert math.isclose(p['pedestal_buffer_drift_V'],.0001,abs_tol=1e-15)
    assert abs(p['main_network_remainder_V'])<1e-15
    r=c.copy();r[3]+=.001
    p=components(r,c,-.00105)['residual_decomposition_input_referred_V']
    assert math.isclose(p['main_closed_loop_difference_drift_V'],-.00105,abs_tol=1e-15)
    return ['zero-drift identity','pedestal sign and normalization','main sign and normalization']

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--run',type=Path,required=True)
    ap.add_argument('--screen',type=Path,help='Remaining80 directory for a combined100 audit')
    ap.add_argument('--packet',type=Path,required=True)
    ap.add_argument('--audit',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args();assert not a.output.exists()
    tests=controls();audit=json.loads(a.audit.read_text())
    pc=json.loads((a.packet/'contract.json').read_text())
    source=(a.packet/'candidate.spice').read_text()
    assert sha(a.packet/'candidate.spice')==SOURCE
    for line in ['XOTA vp vn iptat isense vdd vss g1_ota_main_candidate',
        'XBUF vped_ref vped iptat vped vdd vss g1_ota','XREF vref vref_buf iptat vref_buf vdd vss g1_ota']:
        assert line in source
    samples=[]
    for entry in audit['rows']:
        if entry['controls']!='passed':continue
        directory=a.run if entry['seed']<=41020 else a.screen
        assert directory is not None, 'Combined audit requires the remaining80 directory'
        folder=directory/f"seed{entry['seed']}"
        assert sha(folder/'run.log')==entry['log_sha256']
        observed=parse((folder/'run.log').read_text(),pc['queries'])
        rows=observed['rows'];cal=rows['t0_c0_s0.025'];e=electrical(rows);points=[]
        for p in e['points']:
            t=[25,-40,125].index(p['temperature_C'])
            row=rows[f"t{t}_c{p['sense_n_V']}_s{p['shunt_V']}"]
            points.append(dict(**p,**{k:v for k,v in components(row,cal,p['residual_V']).items() if k!='residual_V'}))
        worst=max((p for p in points if -.1<=p['true_cm_V']<=.3),key=lambda p:abs(p['residual_V']))
        samples.append(dict(seed=entry['seed'],worst_supported=worst,points=points))
    result=dict(status='passed saved-data algebraic identities',samples=samples,controls=tests,
        source_sha256=SOURCE,audit_sha256=sha(a.audit),scope='Closed-loop effective input differences include finite gain, loading and mismatch. Drift terms are nominal-ratio algebra; remainders retain network effects. Not intrinsic isolated OTA offsets or causal variance attribution.',
        full_population=audit['status'],intrinsic_OTA_offsets='not run',full_PEX='not run',hardware='not applicable')
    a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(status=result['status'],samples=len(samples),controls=tests)))

if __name__=='__main__':main()

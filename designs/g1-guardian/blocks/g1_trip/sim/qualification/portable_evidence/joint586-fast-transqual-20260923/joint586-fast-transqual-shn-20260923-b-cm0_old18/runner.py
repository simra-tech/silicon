#!/usr/bin/env python3
"""One immutable owncorner TRANS control; optional exact18-column SHN projection."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import sys
from prepare_joint586_adverse_transients import phases,append_shn,transform_fixture,SIM,ROOT,REFERENCE,sha
from run_joint586_transients import phase_parameters
from run_nominal_clock_probe import analyze_wave,validate_saved_nodes,run_bounded
from analyze_bgr_substitution_outcomes import warning_inventory
from wave_archive import archive_new_wave,open_wave


def compare18(old,new):
    assert len(old)==len(new) and len(old)>1
    projection=[]
    for i,(a,b) in enumerate(zip(old,new)):
        assert len(a.split())==18 and len(b.split())==19 and a.endswith(b'\n') and b.endswith(b'\n')
        prefix=b[:len(a)-1]+b'\n';assert prefix==a,'Original18 decoded-byte mismatch row%d'%i
        if i:assert list(map(float,b.split()[:18]))==list(map(float,a.split()))
        projection.append(prefix)
    return dict(status='passed exact18column decoded-byte and numeric-row projection',rows_including_header=len(old),
        projected_original_sha256=hashlib.sha256(b''.join(projection)).hexdigest())


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run-id',required=True);p.add_argument('--image-id',required=True)
    a=p.parse_args();assert '/' not in a.run_id
    out=SIM/'qualification'/a.run_id;prep=json.loads((out/'preparation.json').read_text())
    assert not (out/'run.log').exists()
    ref=SIM/'qualification'/REFERENCE;original=(ref/'population_transient.cir').read_text()
    base,unused=transform_fixture(original,prep['corner'],3.3,1.2,prep['common_mode_V'])
    expected=phases(base,REFERENCE,a.run_id,prep['seed'],prep['temperatures_C'])
    if prep['columns']==19:expected=append_shn(expected)
    deck=out/'population_transient.cir';assert deck.read_text()==expected and sha(deck)==prep['deck_sha256']
    assert all(sha(ROOT/n)==v for n,v in prep['live_bindings_sha256'].items())
    assert all(sha(out/n)==v for n,v in prep['source_hashes'].items())
    assert sha(out/'population_inventory.json')==prep['inventory_sha256']
    first=expected.split('echo PHASE0_END\n')[0]+'quit 0\n.endc\n.end\n'
    validate_saved_nodes(first,(out/'trip.spice').read_text())
    old_run=None
    if prep['original18_parity_reference']:
        old_run=SIM/'qualification'/prep['original18_parity_reference']
        old_prep=json.loads((old_run/'preparation.json').read_text());old_result,=json.loads((old_run/'summary.json').read_text())
        assert old_result['parameter_wave_contract_status']=='passed'
        for field in ['corner','seed','temperatures_C','common_mode_V','source_hashes','expected_vectors']:
            assert prep[field]==old_prep[field]
        assert append_shn((old_run/'population_transient.cir').read_text().replace(old_run.name,out.name))==expected
    pd=Path('/foss/pdks/ihp-sg13g2')
    runtime=dict(image_id_observed_by_host=a.image_id,pdk_commit=(pd/'COMMIT').read_text().strip(),
        ngspice_version=subprocess.check_output(['ngspice','--version'],universal_newlines=True),
        model_sha256={str(f.relative_to(pd)):sha(f) for f in (pd/'libs.tech/ngspice/models').rglob('*') if f.is_file()},solver='sparse')
    assert runtime==prep['expected_runtime_identity']
    (out/'runner.py').write_text(Path(__file__).read_text())
    (out/'provenance.json').write_text(json.dumps(dict(arguments=sys.argv[1:],runtime_identity=runtime,
        source_hashes=prep['source_hashes'],runner_sha256=sha(Path(__file__)),preparation_sha256=sha(out/'preparation.json'),
        input_checks=dict(deck=True,sources=True,inventory=True,live_bindings=True,runtime=True),physical_scope=prep['physical_scope']),indent=2)+'\n')
    with (out/'run.log').open('x') as stream:
        state=run_bounded(['ngspice','-b',str(deck.relative_to(SIM))],stream,out/'run.json',prep['watchdog_s'],cwd=SIM,interval_s=1)
    log=(out/'run.log').read_text()
    errors=[line for line in log.splitlines() if re.search(r'(?i)(^error|timestep too small|doAnalyses:|no such vector|no such parameter|not available|cannot parse)',line)]
    complete=state['status']=='completed' and state['returncode']==0 and not errors and 'JOINT_POPULATION_TRAN_END' in log
    records=[];parity=dict(status='not applicable; original18vector control')
    if complete:
        try:
            for i,temp in enumerate(prep['temperatures_C']):
                section,=re.findall(r'^PHASE%d_BEGIN\n(.*?)^PHASE%d_END$'%(i,i),log,re.M|re.S)
                params=phase_parameters(section,prep['groups'],prep['expected_vectors'][i])
                wave=out/('phase%d.dat'%i);blob=wave.read_bytes();lines=blob.splitlines(keepends=True)
                data=[list(map(float,line.split())) for line in lines[1:] if line.strip()]
                assert len(lines[0].split())==prep['columns']
                assert data and all(len(row)==prep['columns'] and all(math.isfinite(v) for v in row) for row in data)
                assert abs(data[-1][0]-1.02e-6)<1e-18
                analysis=analyze_wave([r[:13] for r in data],prep['prospective_sampling'])
                entry=dict(params,temperature_C=temp,decoded_wave_sha256=sha(wave),wave_rows=len(data),wave_analysis=analysis,
                    decisions={k:v['measured_edge_decision'] for k,v in analysis['comparators'].items()})
                if prep['columns']==19:
                    # SHP is original column17; appendactualSHN ascolumn18.
                    mean=[(r[17]+r[18])/2 for r in data];diff=[r[17]-r[18] for r in data]
                    entry['actual_input_observation']=dict(mean_common_mode_minmax_V=[min(mean),max(mean)],
                        differential_minmax_V=[min(diff),max(diff)],shn_minmax_V=[min(r[18] for r in data),max(r[18] for r in data)])
                    assert max(abs(v-prep['common_mode_V']) for v in mean)<1e-12 and max(abs(v-.025) for v in diff)<1e-12
                    with open_wave(old_run/('phase%d.dat'%i),'rb') as stream:old=stream.read().splitlines(keepends=True)
                    parity=compare18(old,lines)
                records.append(entry)
        except (AssertionError,OSError,ValueError,KeyError,IndexError) as error:
            errors.append('TRANS parameter/wave/output audit failed: '+repr(error))
    valid=complete and not errors and len(records)==len(prep['temperatures_C'])
    sampling=valid and all(r['wave_analysis']['sampling_status']=='passed' for r in records)
    result=dict(corner=prep['corner'],label=prep['label'],seed=prep['seed'],runtime=state,errors=errors,
        parameter_wave_contract_status='passed' if valid else 'failed',decision_sampling_status='passed' if sampling else 'failed or not run',
        warnings=warning_inventory(log),phases=records,original18_prefix_parity=parity,scope=prep['scope'])
    if valid and len(records)==4:
        result['return_decoded_wavebytes_exact']=(out/'phase0.dat').read_bytes()==(out/'phase3.dat').read_bytes()
    (out/'summary.json').write_text(json.dumps([result],indent=2)+'\n')
    for wave in sorted(out.glob('phase*.dat')):archive_new_wave(wave)
    print(json.dumps({k:v for k,v in result.items() if k not in ['warnings','phases']},indent=2))
    raise SystemExit(0 if valid and sampling else 1)


if __name__=='__main__':main()

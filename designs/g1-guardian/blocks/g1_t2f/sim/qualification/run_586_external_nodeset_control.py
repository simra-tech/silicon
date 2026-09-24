#!/usr/bin/env python3
"""One bounded OP-only initialization arm; no solver or population adoption."""
import argparse
import json
import math
from pathlib import Path
import re
import subprocess
import sys
from prepare_586_external_nodeset_controls import HERE,ROOT,REFERENCE,transform,sha,ARMS
from run_586_klu_adverse_first_sample import errors_in
from run_586_population_control import phase_text
from run_bgr_substitution_draw_audit import read_group
from run_nominal_clock_probe import run_bounded
from analyze_bgr_substitution_outcomes import warning_inventory
from result_directory import allocate_run


def analyze(out,packet,case,state):
    log=(out/'run.log').read_text();errors=errors_in(log)
    result=dict(status='failed',errors=errors,warnings=warning_inventory(log),runtime=state,
        label=case['label'],solver=case['solver'],full3180_status='not run',
        scope='OP diagnostic only; no waveform, frequency, accuracy, solver adoption or population release.')
    try:
        assert state['status']=='completed' and state['returncode']==0 and not errors
        banner='Using KLU as Direct Linear Solver' if case['solver']=='klu' else 'Using SPARSE 1.3 as Direct Linear Solver'
        assert banner in log and 'PHASE0_END' in log
        phase=phase_text(log,0)
        before={tag:read_group(phase,'P0_'+tag+'_BEFORE',keys) for tag,keys in packet['groups'].items()}
        after={tag:read_group(phase,'P0_'+tag+'_AFTER',keys) for tag,keys in packet['groups'].items()}
        assert sum(map(len,before.values()))==3180 and before==after==packet['expected_parameters']
        output,=re.findall(r'^wrdata \S+ (.+)$',(out/'probe.cir').read_text(),re.M)
        lines=(out/'op.dat').read_bytes().splitlines();assert len(lines)==2
        header=[s.decode() for s in lines[0].split()];tokens=lines[1].split();values=list(map(float,tokens))
        assert len(header)==len(values)==17 and header[1:]==output.split()
        assert all(math.isfinite(value) for value in values)
        observations=dict(zip(header[1:],values[1:]))
        vce=max(abs(observations['v(xt2f.'+a+')']-observations['v(xt2f.'+b+')']) for a,b in
            [('ca1','tail1'),('cb1','tail1'),('ca2','tail2'),('cb2','tail2')])
        assert vce<=1.6
        result.update(parameters_before=before,parameters_after=after,full3180_status='passed',
            op_header=header,op_scale_not_physical_time=True,op_values=values,
            decoded_token_rows=[[token.decode() for token in line.split()] for line in lines],
            hbt_external_vce_max_V=vce,op_sha256=sha(out/'op.dat'))
        result['status']='passed OP/full3180 evidence'
    except (AssertionError,KeyError,ValueError,OSError,IndexError) as error:
        result['analysis_error']=repr(error)
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--implementation',required=True)
    p.add_argument('--implementation-sha256',required=True);p.add_argument('--label',choices=ARMS,required=True)
    p.add_argument('--image-id',required=True);a=p.parse_args()
    implementation=ROOT/a.implementation;assert sha(implementation)==a.implementation_sha256
    bound=json.loads(implementation.read_text())
    assert all(sha(ROOT/name)==value for name,value in bound['bindings_sha256'].items())
    contract=ROOT/bound['contract'];assert sha(contract)==bound['contract_sha256']
    packet=json.loads(contract.read_text());assert all(sha(ROOT/name)==value for name,value in packet['bindings_sha256'].items())
    case,=[row for row in packet['cases'] if row['label']==a.label]
    expected=transform((REFERENCE/'p02/probe.cir').read_text(),a.label,packet['guesses'])
    assert (contract.parent/(a.label+'.cir')).read_text()==expected
    assert sha(contract.parent/(a.label+'.cir'))==case['deck_sha256']
    pd=Path('/foss/pdks/ihp-sg13g2')
    runtime=dict(image_id=a.image_id,pdk_commit=(pd/'COMMIT').read_text().strip(),
        ngspice=subprocess.check_output(['ngspice','--version'],universal_newlines=True),
        models_sha256={str(f.relative_to(pd)):sha(f) for f in sorted((pd/'libs.tech/ngspice/models').glob('*.lib'))},
        osdi_sha256={str(f.relative_to(pd)):sha(f) for f in sorted((pd/'libs.tech/ngspice/osdi').glob('*.osdi'))})
    assert runtime==packet['runtime_identity']
    assert all(sha(REFERENCE/name)==value for name,value in packet['source_hashes'].items())
    out=allocate_run(HERE.parent,case['run_id'],relative_parent='qualification/runs')
    for name in ['bgr.spice','t2f.spice','population_inventory.json']:(out/name).write_bytes((REFERENCE/name).read_bytes())
    (out/'.spiceinit').write_bytes((REFERENCE/'p02/.spiceinit').read_bytes())
    (out/'probe.cir').write_text(expected);(out/'runner.py').write_text(Path(__file__).read_text())
    (out/'provenance.json').write_text(json.dumps(dict(arguments=sys.argv[1:],implementation_sha256=a.implementation_sha256,
        contract_sha256=sha(contract),runtime_identity=runtime,runner_sha256=sha(Path(__file__)),source_hashes=packet['source_hashes'],
        case=case),indent=2)+'\n')
    assert case['watchdog_s']==300
    with (out/'run.log').open('x') as stream:state=run_bounded(['ngspice','-b','probe.cir'],stream,out/'run.json',300,cwd=out,interval_s=1)
    result=analyze(out,packet,case,state);(out/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print(result['status']);raise SystemExit(0 if result['status']=='passed OP/full3180 evidence' else 1)


if __name__=='__main__':main()

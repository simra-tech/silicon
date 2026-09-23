#!/usr/bin/env python3
"""One failed fast lowcold fixture KLU diagnostic; no gate alias or adoption."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
from prepare_joint586_fastcold_klu import transform, SIM, ROOT, ORIGINAL, sha
from run_joint586_transients import phase_parameters
from run_nominal_clock_probe import run_bounded, validate_saved_nodes
from audit_joint586_adverse_transients import wave_check
from analyze_bgr_substitution_outcomes import warning_inventory
from wave_archive import archive_new_wave


def qualification(path,prep):
    audit=json.loads(path.read_text())
    assert audit['status']=='passed strict owncorner TRANS qualification' and audit['corner']==prep['corner']
    assert all(audit['checks'].values()) and not audit['audit_errors']
    packet=ROOT/prep['transient_packet'];assert sha(packet)==audit['packet_sha256']
    for case in json.loads(packet.read_text())['cases']:
        run=SIM/'qualification'/case['run']
        assert all(sha(run/n)==v for n,v in audit['receipts_sha256'][case['label']].items())
    return audit


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run-id',required=True)
    p.add_argument('--image-id',required=True);p.add_argument('--qualification-audit',type=Path,required=True)
    a=p.parse_args();assert '/' not in a.run_id
    out=SIM/'qualification'/a.run_id;prep=json.loads((out/'preparation.json').read_text())
    assert not (out/'run.log').exists();qualification(a.qualification_audit,prep)
    original=(ORIGINAL/'population_transient.cir').read_text()
    deck=out/'population_transient.cir'
    assert deck.read_text()==transform(original,a.run_id)
    assert sha(deck)==prep['deck_sha256'] and all(sha(ROOT/n)==v for n,v in prep['live_bindings_sha256'].items())
    assert all(sha(out/n)==v for n,v in prep['source_hashes'].items())
    assert sha(out/'population_inventory.json')==prep['inventory_sha256']
    validate_saved_nodes(deck.read_text(),(out/'trip.spice').read_text())
    pd=Path('/foss/pdks/ihp-sg13g2')
    runtime=dict(image_id_observed_by_host=a.image_id,pdk_commit=(pd/'COMMIT').read_text().strip(),
        ngspice_version=subprocess.check_output(['ngspice','--version'],universal_newlines=True),
        model_sha256={str(f.relative_to(pd)):sha(f) for f in (pd/'libs.tech/ngspice/models').rglob('*') if f.is_file()},solver='klu')
    assert runtime==dict(prep['expected_runtime_identity'],solver='klu')
    (out/'runner.py').write_text(Path(__file__).read_text())
    (out/'provenance.json').write_text(json.dumps(dict(arguments=sys.argv[1:],runtime_identity=runtime,
        preparation_sha256=sha(out/'preparation.json'),qualified_audit_sha256=sha(a.qualification_audit),
        source_hashes=prep['source_hashes'],runner_sha256=sha(Path(__file__)),
        input_checks=dict(deck=True,sources=True,inventory=True,bindings=True,runtime=True,own_TRANS=True)),indent=2)+'\n')
    with (out/'run.log').open('x') as stream:
        state=run_bounded(['ngspice','-b',str(deck.relative_to(SIM))],stream,out/'run.json',1200,cwd=SIM,interval_s=1)
    log=(out/'run.log').read_text()
    errors=[line for line in log.splitlines() if re.search(r'(?i)(^error|timestep too small|doAnalyses:|no such vector|no such parameter|not available|cannot parse)',line)]
    result=dict(status='failed separate KLU fixture diagnostic',condition=prep['condition'],corner=prep['corner'],seed=prep['seed'],
        runtime=state,errors=errors,parameter_wave_status='not run',decision_sampling_status='not run',
        warnings=warning_inventory(log),scope=prep['scope'])
    try:
        assert state['status']=='completed' and state['returncode']==0 and not errors and 'JOINT_POPULATION_TRAN_END' in log
        assert 'Using KLU as Direct Linear Solver' in log and 'Using SPARSE 1.3 as Direct Linear Solver' not in log
        section,=re.findall(r'^PHASE0_BEGIN\n(.*?)^PHASE0_END$',log,re.M|re.S)
        params=phase_parameters(section,prep['groups'],prep['expected_vector'])
        data,analysis=wave_check((out/'phase0.dat').read_bytes(),19,prep['prospective_sampling'])
        cm=prep['condition'][4];mean=[(r[17]+r[18])/2 for r in data];diff=[r[17]-r[18] for r in data]
        assert max(abs(v-cm) for v in mean)<1e-12 and max(abs(v-.025) for v in diff)<1e-12
        observation=dict(mean_common_mode_minmax_V=[min(mean),max(mean)],differential_minmax_V=[min(diff),max(diff)],
            shn_minmax_V=[min(r[18] for r in data),max(r[18] for r in data)])
        result.update(parameter_wave_status='passed',parameters=params,wave_analysis=analysis,
            decoded_wave_sha256=sha(out/'phase0.dat'),wave_rows=len(data),actual_input_observation=observation,
            decision_sampling_status=analysis['sampling_status'],decisions={k:v['measured_edge_decision'] for k,v in analysis['comparators'].items()})
        result['status']='passed separate KLU fixture diagnostic' if analysis['sampling_status']=='passed' else 'failed original decision sampling; finite parameter-valid fixture'
    except (AssertionError,ValueError,OSError,KeyError,IndexError) as error:
        errors.append('Fixture audit failed: '+repr(error))
    (out/'summary.json').write_text(json.dumps([result],indent=2)+'\n')
    if (out/'phase0.dat').exists():archive_new_wave(out/'phase0.dat')
    print(json.dumps({k:v for k,v in result.items() if k not in ['warnings','parameters','wave_analysis']},indent=2))
    raise SystemExit(0 if result['status']=='passed separate KLU fixture diagnostic' else 1)


if __name__=='__main__':main()


#!/usr/bin/env python3
"""One frozen crossed-CM leaf; numerical and electrical results stay separate."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from prepare_joint586_fast_nodeset_crossed_cm import SIM,ROOT,REFERENCE,sha,make_deck
from run_joint586_transients import phase_parameters
from run_nominal_clock_probe import validate_saved_nodes,run_bounded
from run_joint586_fast_nodeset_rescue import numerical_gate,errors_in
from audit_joint586_adverse_transients import wave_check
from wave_archive import open_wave,archive_new_wave
from analyze_bgr_substitution_outcomes import warning_inventory


def check_inputs(out,digest,index):
    assert sha(out/'preparation.json')==digest
    prep=json.loads((out/'preparation.json').read_text())
    assert prep['corner']=='fast' and prep['seed']==78101 and prep['watchdog_s']==1200
    assert len(prep['cases'])==72 and [r['index'] for r in prep['cases']]==list(range(72))
    assert all(sha(ROOT/n)==v for n,v in prep['live_bindings_sha256'].items())
    assert all(sha(out/n)==v for n,v in prep['source_hashes'].items())
    assert sha(out/'population_inventory.json')==prep['inventory_sha256']
    row=prep['cases'][index];leaf=out/('p%02d'%index)
    expected=make_deck((SIM/'qualification'/REFERENCE/'population_transient.cir').read_text(),out.name,row)
    assert (leaf/'probe.cir').read_text()==expected and sha(leaf/'probe.cir')==row['deck_sha256']
    validate_saved_nodes(expected,(out/'trip.spice').read_text())
    return prep,row,leaf


def inspect_leaf(prep,row,leaf):
    state=json.loads((leaf/'run.json').read_text());log=(leaf/'run.log').read_text()
    numerical_gate(state,log);assert state['timeout_s']==1200
    section,=re.findall(r'^PHASE0_BEGIN\n(.*?)^PHASE0_END$',log,re.M|re.S)
    params=phase_parameters(section,prep['groups'],prep['expected_vector'])
    with open_wave(leaf/'phase0.dat','rb') as stream:blob=stream.read()
    output,=[l for l in (leaf/'probe.cir').read_text().splitlines() if l.startswith('wrdata ')]
    assert blob.splitlines()[0].decode().split()==['time']+output.split()[2:]
    data,analysis=wave_check(blob,19,prep['prospective_sampling']);assert analysis['sampling_status']=='passed'
    cm=row['condition'][4];means=[(r[17]+r[18])/2 for r in data];diffs=[r[17]-r[18] for r in data]
    assert max(abs(v-cm) for v in means)<1e-12 and max(abs(v-row['shunt_V']) for v in diffs)<1e-12
    decisions={k:v['measured_edge_decision'] for k,v in analysis['comparators'].items()}
    assert set(decisions)=={'soft','hard'} and all(type(v) is bool for v in decisions.values())
    return dict(numerical_status='passed',electrical_status='passed' if decisions==row['expected_decisions'] else 'failed',
        decisions=decisions,parameter_audit=params,wave_analysis=analysis,wave_rows=len(data),
        decoded_wave_sha256=hashlib.sha256(blob).hexdigest(),actual_input_observation=dict(
            mean_common_mode_minmax_V=[min(means),max(means)],differential_minmax_V=[min(diffs),max(diffs)]))


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run-id',required=True)
    p.add_argument('--preparation-sha256',required=True);p.add_argument('--index',type=int,required=True);p.add_argument('--image-id',required=True)
    a=p.parse_args();assert 0<=a.index<72
    out=SIM/'qualification'/a.run_id;prep,row,leaf=check_inputs(out,a.preparation_sha256,a.index)
    assert not (leaf/'run.log').exists() and not (leaf/'summary.json').exists()
    pd=Path('/foss/pdks/ihp-sg13g2')
    runtime=dict(image_id_observed_by_host=a.image_id,pdk_commit=(pd/'COMMIT').read_text().strip(),
        ngspice_version=subprocess.check_output(['ngspice','--version'],universal_newlines=True),
        model_sha256={str(f.relative_to(pd)):sha(f) for f in (pd/'libs.tech/ngspice/models').rglob('*') if f.is_file()},solver='sparse')
    assert runtime==prep['runtime_identity']
    (leaf/'runner.py').write_text(Path(__file__).read_text())
    (leaf/'provenance.json').write_text(json.dumps(dict(arguments=sys.argv[1:],preparation_sha256=a.preparation_sha256,
        runtime_identity=runtime,runner_sha256=sha(Path(__file__)),source_hashes=prep['source_hashes']),indent=2)+'\n')
    with (leaf/'run.log').open('x') as stream:
        state=run_bounded(['ngspice','-b',str((leaf/'probe.cir').relative_to(SIM))],stream,leaf/'run.json',1200,cwd=SIM,interval_s=1)
    log=(leaf/'run.log').read_text();result=dict(row,runtime=state,numerical_status='failed',electrical_status='not run',
        errors=errors_in(log),warnings=warning_inventory(log),scope=prep['scope'])
    try:result.update(inspect_leaf(prep,row,leaf))
    except (AssertionError,ValueError,KeyError,OSError,IndexError) as error:result['analysis_error']=repr(error)
    (leaf/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    if (leaf/'phase0.dat').exists():archive_new_wave(leaf/'phase0.dat')
    print(json.dumps({k:result[k] for k in ['index','numerical_status','electrical_status']}))
    raise SystemExit(0 if result['numerical_status']=='passed' else 1)


if __name__=='__main__':main()


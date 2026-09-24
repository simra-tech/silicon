#!/usr/bin/env python3
"""Bounded twoOP control or independent reanalysis; preserves first exact failures."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from prepare_dac586_twoop_chunk import ROOT,SIM,transform
from run_dac586_chunk_control import analyze
from run_dac586_static_control import sha
from run_nominal_clock_probe import run_bounded


def analyze_twoop(out,prep,state):
    result=analyze(out,prep,state)
    if 'timing' in result:
        result['timing']['warm_four_OP_plus_query_output_wall_s']=result['timing'].pop('warm_two_OP_plus_query_output_wall_s')
    result['solves_per_changed_code']=2
    return result


def bound(execution,digest,label):
    assert sha(execution)==digest
    packet=json.loads(execution.read_text())
    assert all(sha(ROOT/name)==value for name,value in packet['source_and_reference_sha256'].items())
    out=SIM/'qualification'/(packet['prefix']+'-'+label);prep=json.loads((out/'preparation.json').read_text())
    assert sha(out/'preparation.json')==packet['preparations_sha256'][str((out/'preparation.json').relative_to(ROOT))]
    assert prep['solves_per_changed_code']==2
    ref=SIM/'qualification'/prep['initial_reference']
    assert (out/'dac_chunk.cir').read_text()==transform((ref/'dac_static.cir').read_text(),ref.name,out.name,prep['groups'])
    assert sha(out/'dac_chunk.cir')==prep['deck_sha256']
    assert all(sha(out/name)==value for name,value in prep['source_hashes'].items())
    assert all(sha(ROOT/name)==value for name,value in prep['bindings_sha256'].items())
    assert sha(out/'population_inventory.json')==prep['inventory_sha256']
    return packet,out,prep


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--execution',required=True)
    p.add_argument('--execution-sha256',required=True);p.add_argument('--label',choices=['room','hot'],required=True)
    p.add_argument('--image-id');p.add_argument('--audit-output');a=p.parse_args()
    execution=ROOT/a.execution;packet,out,prep=bound(execution,a.execution_sha256,a.label)
    if a.audit_output:
        provenance=json.loads((out/'provenance.json').read_text())
        assert provenance['execution_sha256']==a.execution_sha256
        assert provenance['runtime_identity']==prep['expected_runtime_identity']
        assert provenance['runner_sha256']==sha(Path(__file__))
        result=analyze_twoop(out,prep,json.loads((out/'run.json').read_text()))
        assert result==json.loads((out/'summary.json').read_text())
        target=ROOT/a.audit_output;assert not target.exists()
        target.write_text(json.dumps(dict(status=result['status'],execution_sha256=a.execution_sha256,
            comparisons=result['anchor_comparisons'],timing=result.get('timing'),errors=result['errors'],
            receipts_sha256={name:sha(out/name) for name in ['summary.json','run.json','run.log','provenance.json','run.progress.jsonl']}),indent=2)+'\n')
        return
    assert a.image_id and not any((out/name).exists() for name in ['run.json','run.log','summary.json','provenance.json'])
    pd=Path('/foss/pdks/ihp-sg13g2')
    runtime=dict(image_id_observed_by_host=a.image_id,pdk_commit=(pd/'COMMIT').read_text().strip(),
        ngspice_version=subprocess.check_output(['ngspice','--version'],universal_newlines=True),
        model_sha256={str(path.relative_to(pd)):sha(path) for path in (pd/'libs.tech/ngspice/models').rglob('*') if path.is_file()},solver='sparse')
    assert runtime==prep['expected_runtime_identity']
    (out/'runner.py').write_text(Path(__file__).read_text())
    (out/'provenance.json').write_text(json.dumps(dict(arguments=sys.argv[1:],runtime_identity=runtime,
        execution_sha256=a.execution_sha256,runner_sha256=sha(Path(__file__)),source_hashes=prep['source_hashes']),indent=2)+'\n')
    assert prep['prospective_watchdog_s']==600
    with (out/'run.log').open('x') as stream:
        state=run_bounded(['ngspice','-b',str((out/'dac_chunk.cir').relative_to(SIM))],stream,out/'run.json',600,cwd=SIM,interval_s=1)
    result=analyze_twoop(out,prep,state)
    (out/'summary.json').write_text(json.dumps(result,indent=2)+'\n');print(result['status'])
    raise SystemExit(0 if result['status']=='passed' else 1)


if __name__=='__main__':main()

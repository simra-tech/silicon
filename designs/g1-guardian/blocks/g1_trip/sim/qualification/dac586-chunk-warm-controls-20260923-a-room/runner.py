#!/usr/bin/env python3
"""Run a single frozen same-instance DAC continuation after strict static qualification."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

from prepare_dac586_chunk_controls import SIM, ROOT, transform
from run_dac586_static_control import sha, analyze as static_analysis, read_op, compare_columns
from run_bgr_substitution_draw_audit import read_group
from run_nominal_clock_probe import run_bounded


def timing(log_bytes, progress):
    def bracket(marker):
        assert log_bytes.count(marker) == 1
        target=log_bytes.index(marker)+len(marker)
        before=[row['wall_s'] for row in progress if row.get('log_bytes',0)<target]
        after=[row['wall_s'] for row in progress if row.get('log_bytes',0)>=target]
        assert after
        return [max(before) if before else 0., min(after)]
    start=bracket(b'DAC_CHUNK_WARM_BEGIN\n');end=bracket(b'DAC_CHUNK_WARM_END\n')
    return {'initial_two_OP_plus_query_output_wall_s':start,
        'warm_two_OP_plus_query_output_wall_s':[max(0,end[0]-start[1]),max(0,end[1]-start[0])],
        'scope':'Intervals from unbuffered log-byte snapshots; include query/output overhead, not isolated solver CPU time.'}


def analyze(out, prep, state):
    ref=SIM/'qualification'/prep['initial_reference']
    original=json.loads((ref/'preparation.json').read_text())
    initial=dict(original,scope=prep['scope'])
    result=static_analysis(out,initial,state)
    result['chunk_status']='failed';result['anchor_comparisons']={}
    if result['status']!='passed':return result
    result['status']='failed'
    try:
        log=(out/'run.log').read_text()
        assert 'DAC_CHUNK_WARM_END' in log
        groups={tag:read_group(log,'CHUNK_'+tag+'_AFTER',queries) for tag,queries in prep['groups'].items()}
        vector=groups['NON_BGR']+groups['BGR']
        assert vector==prep['expected_full_parameters']
        lookup=dict(vector);assert groups['LEGACY27']==[[key,lookup[key]] for key in prep['groups']['LEGACY27']]
        for filename,reference_name in [('op0.dat',prep['initial_reference']),('code128.dat',prep['anchor128_reference']),
                                        ('return127.dat',prep['initial_reference'])]:
            reference=SIM/'qualification'/reference_name
            summary=json.loads((reference/'summary.json').read_text());assert summary['status']=='passed'
            header=(reference/'op0.dat').read_text().splitlines()[0].split()
            candidate=read_op(out/filename,header);baseline=read_op(reference/'op0.dat',header)
            exact=compare_columns(candidate,baseline,12)
            result['anchor_comparisons'][filename]=dict(exact,
                maximum_abs_voltage_difference_V=max(abs(a-b) for a,b in zip(candidate[1][1:10],baseline[1][1:10])),
                maximum_abs_supply_current_difference_A=max(abs(a-b) for a,b in zip(candidate[1][10:],baseline[1][10:])))
        result['chunk_after11512']=vector;result['chunk_after27']=groups['LEGACY27']
        progress=[json.loads(line) for line in (out/'run.progress.jsonl').read_text().splitlines()]
        result['timing']=timing((out/'run.log').read_bytes(),progress)
        assert all(row['numeric_rows_exact'] and row['decoded_column_token_bytes_exact'] for row in result['anchor_comparisons'].values()), 'Strict static/warm overlap failed'
        result['status']='passed';result['chunk_status']='passed strict anchor/full-draw continuation'
    except (AssertionError,ValueError,KeyError,IndexError,OSError) as error:
        result['errors'].append('Chunk audit: '+str(error))
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-id',required=True);parser.add_argument('--preparation-sha256',required=True)
    parser.add_argument('--execution',required=True);parser.add_argument('--execution-sha256',required=True)
    parser.add_argument('--image-id',required=True);args=parser.parse_args()
    assert '/' not in args.run_id
    out=SIM/'qualification'/args.run_id;assert sha(out/'preparation.json')==args.preparation_sha256
    prep=json.loads((out/'preparation.json').read_text())
    execution=ROOT/args.execution;assert sha(execution)==args.execution_sha256
    bound=json.loads(execution.read_text())
    assert bound['preparations_sha256'][str((out/'preparation.json').relative_to(ROOT))]==args.preparation_sha256
    assert all(sha(ROOT/name)==value for name,value in bound['source_and_reference_sha256'].items())
    assert str(Path(__file__).resolve().relative_to(ROOT)) in bound['source_and_reference_sha256']
    audit=ROOT/bound['static_audit'];report=json.loads(audit.read_text())
    assert sha(audit)==bound['static_audit_sha256'] and report['status']=='passed static anchor qualification'
    assert report['completed_controls']==report['expected_controls']==11
    assert not any((out/name).exists() for name in ['run.json','run.log','summary.json','provenance.json'])
    reference=SIM/'qualification'/prep['initial_reference']
    expected=transform((reference/'dac_static.cir').read_text(),reference.name,out.name,prep['groups'])
    pd=Path('/foss/pdks/ihp-sg13g2')
    runtime={'image_id_observed_by_host':args.image_id,'pdk_commit':(pd/'COMMIT').read_text().strip(),
        'ngspice_version':subprocess.check_output(['ngspice','--version'],universal_newlines=True),
        'model_sha256':{str(path.relative_to(pd)):sha(path) for path in (pd/'libs.tech/ngspice/models').rglob('*') if path.is_file()},'solver':'sparse'}
    checks={'deck_exact':(out/'dac_chunk.cir').read_text()==expected and sha(out/'dac_chunk.cir')==prep['deck_sha256'],
        'source_exact':all(sha(out/name)==value for name,value in prep['source_hashes'].items()),
        'inventory_exact':sha(out/'population_inventory.json')==prep['inventory_sha256'],
        'bindings_exact':all(sha(ROOT/name)==value for name,value in prep['bindings_sha256'].items()),
        'runtime_exact':runtime==prep['expected_runtime_identity']}
    provenance=dict(arguments=sys.argv[1:],runtime_identity=runtime,input_checks=checks,
        execution_sha256=args.execution_sha256,preparation_sha256=args.preparation_sha256,
        runner_sha256=sha(Path(__file__)),source_hashes=prep['source_hashes'])
    (out/'runner.py').write_text(Path(__file__).read_text())
    (out/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
    assert all(checks.values()), 'Preflight failed; no simulator launched'
    assert prep['prospective_watchdog_s']==600
    with (out/'run.log').open('x') as stream:
        state=run_bounded(['ngspice','-b',str((out/'dac_chunk.cir').relative_to(SIM))],stream,out/'run.json',600,cwd=SIM,interval_s=1)
    result=analyze(out,prep,state)
    (out/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({key:value for key,value in result.items() if key not in ['phases','warnings','chunk_after11512']},indent=2))
    raise SystemExit(0 if result['status']=='passed' else 1)


if __name__=='__main__':main()

"""Bounded eight-code continuation diagnostic; no all-code qualification."""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from prepare_dac586_lowcarry_probe import ROOT,SIM,REFERENCE,chunk_deck,sha
from prepare_dac586_dc_controls import ADDED
from run_dac586_dc_control import table,check_row,reference_comparison
from run_dac586_static_control import fatal_errors
from run_bgr_substitution_draw_audit import read_group
from run_nominal_clock_probe import run_bounded


def analyze(out,prep,state):
    log=(out/'run.log').read_text();errors=fatal_errors(log)
    result=dict(numerical_status='failed',consistency_status='not run',errors=errors,runtime=state,
        scope='Eight-code method/throughput diagnostic only; no isolated leakage, dynamic or all-code acceptance.')
    try:
        assert state['status']=='completed' and state['returncode']==0 and not errors
        assert 'Using SPARSE 1.3 as Direct Linear Solver' in log and 'POPULATION_OP_END' in log
        assert log.count('DAC_LOWCARRY_BEGIN')==log.count('DAC_LOWCARRY_END')==1
        groups={tag+'_'+when:read_group(log,'P0_'+tag+'_'+when,keys) for tag,keys in prep['groups'].items() for when in ['BEFORE','AFTER']}
        expected=prep['expected_full_parameters'];assert len(expected)==11512
        assert groups['NON_BGR_BEFORE']+groups['BGR_BEFORE']==groups['NON_BGR_AFTER']+groups['BGR_AFTER']==expected
        lookup=dict(expected);anchors=[[key,lookup[key]] for key in prep['groups']['LEGACY27']]
        assert groups['LEGACY27_BEFORE']==groups['LEGACY27_AFTER']==anchors
        after={tag:read_group(log,'DC_'+tag+'_AFTER',keys) for tag,keys in prep['groups'].items()}
        assert after['NON_BGR']+after['BGR']==expected and after['LEGACY27']==anchors
        header=(REFERENCE/'op0.dat').read_text().splitlines()[0].split();assert len(header)==12
        original=table(REFERENCE/'op0.dat',header,1);fullheader=header+ADDED
        op=table(out/'op0.dat',fullheader,1);check_row(op[1][0],0,0,0.)
        comparisons={'op0.dat':reference_comparison(op[0][1],op[1][0],original,True)};tables={}
        for filename,codes in [('forward.dat',list(range(8))),('reverse.dat',list(range(7,-1,-1)))]:
            values=table(out/filename,['v-sweep']+fullheader[1:],8)
            assert [r[0] for r in values[1]]==codes
            for index,code in enumerate(codes):
                check_row(values[1][index],code,code,float(code))
                if code==0:comparisons[filename+':0']=reference_comparison(values[0][index+1],values[1][index],original,False)
            tables[filename]=values[1]
        reverse=list(reversed(tables['reverse.dat']))
        differences={str(code):dict(maximum_voltage_difference_V=max(abs(x-y) for x,y in zip(a[1:10],b[1:10])),
            maximum_total_supply_current_difference_A=max(abs(x-y) for x,y in zip(a[10:12],b[10:12])))
            for code,(a,b) in enumerate(zip(tables['forward.dat'],reverse))}
        progress=[json.loads(line) for line in (out/'run.progress.jsonl').read_text().splitlines()]
        raw=(out/'run.log').read_bytes();start=raw.index(b'DAC_LOWCARRY_BEGIN\n');ends=list(re.finditer(rb'No\. of Data Rows\s*:\s*8\s*\r?\n',raw));assert len(ends)==2
        def bracket(offset):
            before=[r['wall_s'] for r in progress if r.get('log_bytes',0)<offset];following=[r['wall_s'] for r in progress if r.get('log_bytes',0)>=offset]
            return [max(before) if before else 0.,min(following) if following else state['wall_s']]
        def delta(a,b):return [max(0,a[0]-b[1]),max(0,a[1]-b[0])]
        initial=bracket(start);forward=bracket(ends[0].end());backward=bracket(ends[1].end())
        sections=[raw[:start],raw[start:ends[0].end()],raw[ends[0].end():ends[1].end()]]
        timing=dict(initial_two_OP_and_inventory_s=initial,forward_eight_code_s=delta(forward,initial),reverse_eight_code_and_prior_output_s=delta(backward,forward),
            dynamic_gmin_starts_initial_forward_reverse=[s.count(b'Starting dynamic gmin stepping') for s in sections],
            scope='Observed byte-progress brackets include initialization/output; no inference of per-point time where not logged.')
        result.update(numerical_status='passed',consistency_status='passed original code0 method screen' if all(c['prospective_consistency_passed'] for c in comparisons.values()) else 'failed original code0 method screen',
            strict_original_code0_equivalence=all(c['numeric_exact'] and c['decoded_numeric_token_bytes_exact'] for c in comparisons.values()),
            full11512_and27_exact=True,reference_comparisons=comparisons,forward_reverse_differences=differences,timing=timing,
            tables_sha256={n:sha(out/n) for n in ['op0.dat','forward.dat','reverse.dat']},
            unsupported_scope='Codes1..7 lack original independent static anchors. Finite comparisons are not a uniform error proof; no DNL/yield/guard acceptance.')
    except (AssertionError,KeyError,ValueError,IndexError,OSError) as error:result['analysis_error']=repr(error)
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--execution',required=True);p.add_argument('--execution-sha256',required=True);p.add_argument('--label',required=True);p.add_argument('--image-id',required=True);a=p.parse_args()
    execution=ROOT/a.execution;assert sha(execution)==a.execution_sha256;e=json.loads(execution.read_text())
    assert all(sha(ROOT/n)==v for n,v in e['bindings_sha256'].items())
    packet=ROOT/e['packet'];assert sha(packet)==e['packet_sha256'];d=json.loads(packet.read_text())
    assert all(sha(ROOT/n)==v for n,v in d['bindings_sha256'].items())
    case,=[c for c in d['controls'] if c['label']==a.label];out=SIM/'qualification'/case['run'];assert sha(out/'preparation.json')==case['preparation_sha256']
    prep=json.loads((out/'preparation.json').read_text());assert not (out/'run.log').exists()
    assert all(sha(ROOT/n)==v for n,v in prep['bindings_sha256'].items())
    assert all(sha(out/n)==v for n,v in prep['source_hashes'].items()) and sha(out/'population_inventory.json')==prep['inventory_sha256']
    assert (out/'dac_lowcarry.cir').read_text()==chunk_deck((REFERENCE/'dac_static.cir').read_text(),REFERENCE.name,out.name,prep['groups'])
    assert sha(out/'dac_lowcarry.cir')==prep['deck_sha256']==case['deck_sha256'] and case['watchdog_s']==600
    pd=Path('/foss/pdks/ihp-sg13g2');runtime=dict(image_id_observed_by_host=a.image_id,pdk_commit=(pd/'COMMIT').read_text().strip(),
        ngspice_version=subprocess.check_output(['ngspice','--version'],universal_newlines=True),
        model_sha256={str(f.relative_to(pd)):sha(f) for f in (pd/'libs.tech/ngspice/models').rglob('*') if f.is_file()},solver='sparse')
    assert runtime==prep['expected_runtime_identity']
    (out/'runner.py').write_text(Path(__file__).read_text());(out/'provenance.json').write_text(json.dumps(dict(arguments=sys.argv[1:],execution_sha256=a.execution_sha256,
        preparation_sha256=case['preparation_sha256'],runtime_identity=runtime,source_hashes=prep['source_hashes']),indent=2)+'\n')
    with (out/'run.log').open('x') as stream:state=run_bounded(['ngspice','-b',str((out/'dac_lowcarry.cir').relative_to(SIM))],stream,out/'run.json',600,cwd=SIM,interval_s=1)
    result=analyze(out,prep,state);(out/'summary.json').write_text(json.dumps(result,indent=2)+'\n');print(result['numerical_status'],result['consistency_status'])
    raise SystemExit(0 if result['numerical_status']=='passed' else 1)


if __name__=='__main__':main()

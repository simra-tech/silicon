#!/usr/bin/env python3
"""One prospective source-held DAC method control, with separate exact comparisons."""
import argparse
import json
import math
from pathlib import Path
import re
import subprocess
import sys
from prepare_dac586_dc_controls import ROOT,SIM,ADDED,transform
from run_dac586_static_control import sha,fatal_errors,compare_columns
from run_bgr_substitution_draw_audit import read_group
from run_nominal_clock_probe import run_bounded
from analyze_bgr_substitution_outcomes import warning_inventory
from dac586_dc_metrics import actual_bits,VOLTAGE_COMPARISON_V,CURRENT_COMPARISON_A


def table(path,header,rows):
    lines=path.read_bytes().splitlines();tokens=[line.split() for line in lines]
    assert len(lines)==rows+1 and [x.decode() for x in tokens[0]]==header
    data=[list(map(float,line)) for line in tokens[1:]]
    assert all(len(row)==len(header) and all(math.isfinite(v) for v in row) for row in data)
    return tokens,data


def reference_comparison(tokens,values,reference,include_scale):
    raw,=reference[1];start=0 if include_scale else 1
    numeric=values[start:12]==raw[start:12]
    exact_tokens=tokens[start:12]==reference[0][1][start:12]
    vmax=max(abs(a-b) for a,b in zip(values[1:10],raw[1:10]))
    imax=max(abs(a-b) for a,b in zip(values[10:12],raw[10:12]))
    return dict(numeric_exact=numeric,decoded_numeric_token_bytes_exact=exact_tokens,
        maximum_voltage_difference_V=vmax,maximum_total_supply_current_difference_A=imax,
        prospective_consistency_passed=vmax<=VOLTAGE_COMPARISON_V and imax<=CURRENT_COMPARISON_A,
        op_or_dc_scale_compared=include_scale)


def check_row(values,soft,hard,code_value):
    assert len(values)==30 and actual_bits(values[12:28],soft,hard), 'Actualbit map not exact'
    assert values[28]==code_value, 'Actual code source voltage differs'


def timing(out,total):
    log=(out/'run.log').read_bytes();progress=[json.loads(line) for line in (out/'run.progress.jsonl').read_text().splitlines()]
    def bracket(offset):
        before=[r['wall_s'] for r in progress if r.get('log_bytes',0)<offset]
        after=[r['wall_s'] for r in progress if r.get('log_bytes',0)>=offset]
        return [max(before) if before else 0.,min(after) if after else total]
    marker=b'DAC_DC_BEGIN\n';assert log.count(marker)==1
    start=bracket(log.index(marker)+len(marker))
    matches=list(re.finditer(rb'No\. of Data Rows\s*:\s*2\s*\r?\n',log));assert len(matches)==2
    forward=bracket(matches[0].end());reverse=bracket(matches[1].end())
    def delta(a,b):return [max(0,a[0]-b[1]),max(0,a[1]-b[0])]
    return dict(initial_two_OP_and_inventory_wall_s=start,forward_two_point_DC_wall_s=delta(forward,start),
        reverse_two_point_DC_and_previous_output_wall_s=delta(reverse,forward),
        scope='Byte-progress intervals include analysis initialization and output. Two-point timing alone does not establish marginal cost for256codes.')


def analyze(out,prep,state):
    log=(out/'run.log').read_text();errors=fatal_errors(log)
    result=dict(status='failed method control',runtime=state,errors=errors,warnings=warning_inventory(log),
        method=prep['method'],phases=[],reference_comparisons={},strict_static_equivalence='not run',
        scope='Conditional numerical method control only; original exact failures retained, no all-code/statistical/dynamic/leakage qualification.')
    try:
        assert state['status']=='completed' and state['returncode']==0 and not errors
        assert 'Using SPARSE 1.3 as Direct Linear Solver' in log and 'POPULATION_OP_END' in log
        ref=SIM/'qualification'/prep['reference_static'];oldheader=(ref/'op0.dat').read_text().splitlines()[0].split()
        assert len(oldheader)==12
        header=oldheader+ADDED;records=[]
        expected=prep['expected_full_parameters'];lookup=dict(expected);assert len(expected)==len(lookup)==11512
        for index,temperature in enumerate(prep['temperatures_C']):
            groups={tag+'_'+when:read_group(log,'P%d_%s_%s'%(index,tag,when),keys)
                for tag,keys in prep['groups'].items() for when in ['BEFORE','AFTER']}
            assert groups['NON_BGR_BEFORE']+groups['BGR_BEFORE']==groups['NON_BGR_AFTER']+groups['BGR_AFTER']==expected
            anchors=[[key,lookup[key]] for key in prep['groups']['LEGACY27']]
            assert groups['LEGACY27_BEFORE']==groups['LEGACY27_AFTER']==anchors
            name='op%d.dat'%index;record=table(out/name,header,1);records.append(record)
            check_row(record[1][0],prep['codes'][0],prep['codes'][1],0.)
            old=table(ref/name,oldheader,1)
            result['reference_comparisons'][name]=reference_comparison(record[0][1],record[1][0],old,True)
            result['phases'].append(dict(temperature_C=temperature,full11512_before_after_exact=True,legacy27_exact=True,
                parameters_before=groups['NON_BGR_BEFORE']+groups['BGR_BEFORE'],op_values=record[1][0],op_sha256=sha(out/name)))
        if len(records)>1:
            result['same_method_return_exact']=records[0]==records[-1]
            assert result['same_method_return_exact'], 'SameBmethod returnedOP differs exactly'
        if prep['method']=='dc-two-point-forward-reverse':
            assert 'DAC_DC_BEGIN' in log and 'DAC_DC_END' in log
            after={tag:read_group(log,'DC_'+tag+'_AFTER',keys) for tag,keys in prep['groups'].items()}
            assert after['NON_BGR']+after['BGR']==expected and after['LEGACY27']==anchors
            result['dc_after11512']=after['NON_BGR']+after['BGR'];result['dc_after27']=anchors
            result['dc_rows']={}
            result['timing']=timing(out,state['wall_s'])
            suffix='room' if prep['temperatures_C']==[25] else 'hot'
            assert prep['temperatures_C'] in [[25],[125]]
            for filename,codes in [('forward.dat',[0,1]),('reverse.dat',[1,0])]:
                record=table(out/filename,['v-sweep']+header[1:],2)
                assert [row[0] for row in record[1]]==codes
                for index,relative in enumerate(codes):
                    code=127+relative;check_row(record[1][index],code,code,float(relative))
                    original=SIM/'qualification'/('dac586-static-controls-20260923-a-c%d-%s'%(code,suffix))
                    old=table(original/'op0.dat',oldheader,1)
                    result['reference_comparisons'][filename+':'+str(code)]=reference_comparison(record[0][index+1],record[1][index],old,False)
                result['dc_rows'][filename]=record[1]
        comparisons=list(result['reference_comparisons'].values())
        result['strict_static_equivalence']='passed' if all(r['numeric_exact'] and r['decoded_numeric_token_bytes_exact'] for r in comparisons) else 'failed'
        result['prospective_consistency']='passed' if all(r['prospective_consistency_passed'] for r in comparisons) else 'failed'
        assert result['prospective_consistency']=='passed', 'Prospective numerical consistency failed'
        result['status']='passed conditional method control; exact status separate'
    except (AssertionError,KeyError,ValueError,IndexError,OSError) as error:
        result['analysis_error']=repr(error)
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--execution',required=True)
    p.add_argument('--execution-sha256',required=True);p.add_argument('--label',required=True);p.add_argument('--image-id',required=True);a=p.parse_args()
    execution=ROOT/a.execution;assert sha(execution)==a.execution_sha256;packet=json.loads(execution.read_text())
    assert packet['numerical_comparison_approved'] is True
    assert all(sha(ROOT/name)==value for name,value in packet['source_bindings_sha256'].items())
    proposal=ROOT/packet['proposal'];assert sha(proposal)==packet['proposal_sha256'];proposal=json.loads(proposal.read_text())
    case,=[r for r in proposal['controls'] if r['label']==a.label]
    out=SIM/'qualification'/case['run'];assert sha(out/'preparation.json')==case['preparation_sha256'];prep=json.loads((out/'preparation.json').read_text())
    assert all(sha(ROOT/name)==value for name,value in proposal['bindings_sha256'].items())
    assert all(sha(ROOT/name)==value for name,value in prep['bindings_sha256'].items())
    assert all(sha(out/name)==value for name,value in prep['source_hashes'].items())
    assert sha(out/'population_inventory.json')==prep['inventory_sha256']
    assert prep['output_equivalence']['voltage_abs_V']==VOLTAGE_COMPARISON_V
    assert prep['output_equivalence']['current_abs_A']==CURRENT_COMPARISON_A
    ref=SIM/'qualification'/prep['reference_static'];dc=prep['method']=='dc-two-point-forward-reverse'
    assert (out/'dac_dc.cir').read_text()==transform((ref/'dac_static.cir').read_text(),ref.name,out.name,*prep['codes'],prep['groups'],dc=dc)
    assert sha(out/'dac_dc.cir')==prep['deck_sha256']
    if dc:
        audit=ROOT/packet['required_static_method_audit'];d=json.loads(audit.read_text())
        assert d['status']=='passed conditional staticB11 qualification' and d['execution_sha256']==a.execution_sha256
        assert d['completed_controls']==11
        assert d['repeat_exact'] is True and d['return_exact'] is True
        for row in d['controls']:
            assert row['status'].startswith('passed conditional')
            assert all(sha(SIM/'qualification'/row['run']/name)==value for name,value in row['receipts_sha256'].items())
    assert not any((out/name).exists() for name in ['run.json','run.log','summary.json','provenance.json'])
    pd=Path('/foss/pdks/ihp-sg13g2')
    runtime=dict(image_id_observed_by_host=a.image_id,pdk_commit=(pd/'COMMIT').read_text().strip(),
        ngspice_version=subprocess.check_output(['ngspice','--version'],universal_newlines=True),
        model_sha256={str(path.relative_to(pd)):sha(path) for path in (pd/'libs.tech/ngspice/models').rglob('*') if path.is_file()},solver='sparse')
    assert runtime==prep['expected_runtime_identity']
    (out/'runner.py').write_text(Path(__file__).read_text())
    (out/'provenance.json').write_text(json.dumps(dict(arguments=sys.argv[1:],execution_sha256=a.execution_sha256,
        preparation_sha256=sha(out/'preparation.json'),runtime_identity=runtime,runner_sha256=sha(Path(__file__)),source_hashes=prep['source_hashes']),indent=2)+'\n')
    assert case['watchdog_s']==prep['prospective_bound_s']
    with (out/'run.log').open('x') as stream:
        state=run_bounded(['ngspice','-b',str((out/'dac_dc.cir').relative_to(SIM))],stream,out/'run.json',case['watchdog_s'],cwd=SIM,interval_s=1)
    result=analyze(out,prep,state);(out/'summary.json').write_text(json.dumps(result,indent=2)+'\n');print(result['status'])
    raise SystemExit(0 if result['status'].startswith('passed conditional') else 1)


if __name__=='__main__':main()

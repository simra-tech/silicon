#!/usr/bin/env python3
"""Fail-closed OP-only nodeset diagnostic; original unlaunched r1 retained."""
import argparse
import json
import math
from pathlib import Path
import re
import subprocess
import sys
from prepare_joint586_fastcold_nodeset import SIM,ROOT,ORIGINAL,NODES,sha,transform
from run_joint586_transients import phase_parameters
from run_nominal_clock_probe import run_bounded
from analyze_bgr_substitution_outcomes import warning_inventory

def output_values(blob):
    lines=blob.decode().splitlines()
    header=lines[0].split()
    assert len(header)==9 and header[1:]==['v('+n+')' for n in NODES], 'Wrong OP vector names/order'
    data=[list(map(float,l.split())) for l in lines[1:] if l.strip()]
    assert len(data)==1 and len(data[0])==9 and all(math.isfinite(v) for v in data[0])
    return dict(zip(NODES,data[0][1:]))

def numerical_gate(state,errors,log,solver):
    assert state['status']=='completed' and state['returncode']==0 and not errors and 'JOINT_NODESET_OP_END' in log
    banner='Using KLU as Direct Linear Solver' if solver=='klu' else 'Using SPARSE 1.3 as Direct Linear Solver'
    assert banner in log

def baseline_comparison(base,base_blob,values,blob):
    assert base['status']=='passed finite fullparameter OP diagnostic; exact comparisons separate'
    assert not base.get('analysis_error') and not base['errors']
    assert output_values(base_blob)==base['op_nodes_V']
    return dict(baseline_nodes_exact=values==base['op_nodes_V'],baseline_data_bytes_exact=blob==base_blob,
        baseline_deltas_V={n:values[n]-base['op_nodes_V'][n] for n in NODES})

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--contract',type=Path,required=True);p.add_argument('--contract-sha256',required=True);p.add_argument('--label',required=True);p.add_argument('--image-id',required=True);a=p.parse_args()
    assert sha(a.contract)==a.contract_sha256
    packet=json.loads(a.contract.read_text());case,=[c for c in packet['cases'] if c['label']==a.label]
    out=SIM/'qualification'/case['run'];deck=out/'op.cir';assert not (out/'run.log').exists()
    assert all(sha(ROOT/n)==v for n,v in packet['bindings_sha256'].items())
    expected,audit=transform((ORIGINAL/'population_transient.cir').read_text(),case['run'],a.label,packet['guesses_original_printed_strings'])
    assert deck.read_text()==expected and sha(deck)==case['deck_sha256']
    assert json.loads((out/'transform_audit.json').read_text())==audit and sha(out/'transform_audit.json')==case['transform_sha256']
    assert all(sha(out/n)==sha(ORIGINAL/n)==v for n,v in packet['source_hashes'].items())
    pd=Path('/foss/pdks/ihp-sg13g2')
    runtime=dict(image_id_observed_by_host=a.image_id,pdk_commit=(pd/'COMMIT').read_text().strip(),ngspice_version=subprocess.check_output(['ngspice','--version'],universal_newlines=True),model_sha256={str(f.relative_to(pd)):sha(f) for f in (pd/'libs.tech/ngspice/models').rglob('*') if f.is_file()},solver=case['solver'])
    assert runtime==dict(packet['expected_runtime_identity'],solver=case['solver'])
    (out/'provenance.json').write_text(json.dumps(dict(runtime_identity=runtime,contract_sha256=sha(a.contract),arguments=sys.argv[1:],source_hashes=packet['source_hashes'],input_checks=dict(deck=True,fullbindings=True,source=True,runtime=True),runner_sha256=sha(Path(__file__))),indent=2)+'\n')
    (out/'runner.py').write_text(Path(__file__).read_text())
    with (out/'run.log').open('x') as stream:state=run_bounded(['ngspice','-b',str(deck.relative_to(SIM))],stream,out/'run.json',300,cwd=SIM,interval_s=1)
    log=(out/'run.log').read_text();errors=[l for l in log.splitlines() if re.search(r'^Error|Timestep too small|doAnalyses:|no such vector|no such parameter|not available|cannot parse',l,re.I)]
    result=dict(status='failed OP-only initialization diagnostic',runtime=state,errors=errors,warnings=warning_inventory(log),parameters='not run',OP_comparisons='not run',scope=packet['scope'])
    try:
        section,=re.findall(r'^PHASE0_BEGIN\n(.*?)^PHASE0_END$',log,re.M|re.S)
        result['parameters']=phase_parameters(section,packet['groups'],packet['expected_vector'])
        numerical_gate(state,errors,log,case['solver'])
        blob=(out/'op.dat').read_bytes();values=output_values(blob)
        original={n:float(v) for n,v in packet['guesses_original_printed_strings'].items()}
        comparisons=dict(original_printed_values_exact=values==original,node_delta_V={n:values[n]-original[n] for n in NODES},precision_scope='Original15digit printed values versus output15digit; no byte-parity claim against absent originalOPfile. No acceptance bound substituted.')
        if case['label']!='sparse':
            baseline=SIM/'qualification'/packet['cases'][0]['run']
            base,=json.loads((baseline/'summary.json').read_text())
            comparisons.update(baseline_comparison(base,(baseline/'op.dat').read_bytes(),values,blob))
        # Publish PASS only after every numerical, parameter, output and
        # required baseline gate completed; exact differences remain separate.
        result.update(status='passed finite fullparameter OP diagnostic; exact comparisons separate',op_nodes_V=values,op_data_sha256=sha(out/'op.dat'),OP_comparisons=comparisons)
    except (AssertionError,ValueError,KeyError,OSError,IndexError) as error:
        result.update(status='failed OP-only initialization diagnostic',analysis_error=repr(error))
    (out/'summary.json').write_text(json.dumps([result],indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['parameters','warnings']},indent=2));raise SystemExit(0 if result['status'].startswith('passed finite') else 1)

if __name__=='__main__':main()

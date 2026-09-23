#!/usr/bin/env python3
"""Read-only initialization/range evidence; rounded OP is not full model validity."""
import argparse
import hashlib
import json
from pathlib import Path
import re

HERE=Path(__file__).resolve().parent
ORIGINAL=HERE/'qualification/joint586-fast-fixture-controls-20260923-b-low_cold_cm0'
KLU=HERE/'qualification/joint586-fast-lowcold-klu-20260923-a'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def initial_nodes(log):
    tail=log.split('Initial Transient Solution',1)[1].split('Reference value',1)[0]
    values={}
    for line in tail.splitlines():
        match=re.fullmatch(r'\s*([^\s]+)\s+([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)\s*',line)
        if match:values[match[1].lower()]=float(match[2])
    assert values and all(abs(v)<1e12 for v in values.values())
    values['0']=0.0
    return values

def hbt_rows(source, nodes):
    portmap=dict(vdd='vdda',vss='0',r4='r4',vref='vref',iptat='iptat',pbias='pbias',pcasc='pcasc',vbe='vbe',dvbe='dvbe')
    result=[]
    for line in source.splitlines():
        if not line.startswith('XQ'):continue
        f=line.lower().split();assert f[5]=='npn13g2'
        names=[portmap.get(n,'xbgr.'+n) for n in f[1:5]]
        voltages=[nodes[n] for n in names]
        c,b,e,bn=voltages;vbe=b-e;vce=c-e
        dummy=all(n=='0' for n in names)
        result.append(dict(source_id=f[0],nodes=dict(zip(['C','B','E','BN'],names)),
            rounded_external_voltages_V=dict(zip(['C','B','E','BN'],voltages)),VBE_V=vbe,VCE_V=vce,
            grounded_dummy=dummy,within_external_abs_VCE_1p6=abs(vce)<=1.6,
            within_documented_forward_VBE_range=.65<=vbe<=.96,
            within_documented_forward_VCE_range=.4<=vce<=2,
            current_density_range='not run; no native external collector currents saved'))
    assert len(result)==301
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--pinned-model-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert not a.output.exists()
    model=a.pinned_model_root/'libs.tech/ngspice/models/sg13g2_hbt_mod_mismatch.lib'
    expected=json.loads((KLU/'provenance.json').read_text())['runtime_identity']['model_sha256']
    rel='libs.tech/ngspice/models/sg13g2_hbt_mod_mismatch.lib'
    assert sha(model)==expected[rel]
    raw=model.read_text(encoding='latin-1');assert 'vce :(0.4 - 2.0)' in raw and 'vbe :(0.65 - 0.96)' in raw and 'Maximum collector-to-emitter voltage: 1.6' in raw
    logs=[(ORIGINAL/'run.log').read_text(),(KLU/'run.log').read_text()]
    nodes=initial_nodes(logs[0]);rows=hbt_rows((ORIGINAL/'bgr.spice').read_text(),nodes)
    quiet_section=logs[0].split('BIAS_OBSERVATION_OP\n',1)[1].split('BIAS_OBSERVATION_OP_END',1)[0]
    quiet={k:float(v) for k,v in re.findall(r'v\(([^)]+)\)\s*=\s*([-+0-9.eE]+)',quiet_section)}
    assert len(quiet)==9
    chronology=[]
    for solver,log in zip(['SPARSE','KLU'],logs):
        events=[]
        for number,line in enumerate(log.splitlines(),1):
            if re.search(r'Starting .*stepping|stepping completed|stepping failed|singular matrix|Transient op (?:started|failed)|operating point could not|doAnalyses:',line):
                events.append(dict(line=number,text=line))
        chronology.append(dict(solver=solver,events=events))
    result=dict(status='completed read-only diagnosis; original numerical failures retained',
        source_and_receipt_sha256={str((d/n).relative_to(HERE)):sha(d/n) for d in [ORIGINAL,KLU] for n in ['run.log','run.json','summary.json','bgr.spice','population_transient.cir']},
        pinned_model=dict(path=rel,sha256=sha(model),temperature_C=-40,documented_temperature_range_C=[-40,125],
            documented_forward_VBE_V=[.65,.96],documented_forward_VCE_V=[.4,2],external_maximum_VCE_V=1.6,
            current_density_limit_A_per_Nx=.003),
        original_sparse_quiet_15digit_nodes_V=quiet,rounded_initial_solution_node_count=len(nodes),
        hbt_external_OP_rows=rows,hbt_counts=dict(total=len(rows),grounded_dummy=sum(r['grounded_dummy'] for r in rows),
            external_abs_VCE_exceedances=sum(not r['within_external_abs_VCE_1p6'] for r in rows),
            outside_forward_VBE=sum(not r['within_documented_forward_VBE_range'] for r in rows),
            outside_forward_VCE=sum(not r['within_documented_forward_VCE_range'] for r in rows)),
        external_VBE_range_V=[min(r['VBE_V'] for r in rows),max(r['VBE_V'] for r in rows)],
        external_VCE_range_V=[min(r['VCE_V'] for r in rows),max(r['VCE_V'] for r in rows)],
        failure_chronology=chronology,
        q55_scope='Grounded dummy: all four external terminals VSS. Reported trouble instance is not demonstrated root cause.',
        model_applicability='Not qualified. Rounded external OP voltages do not establish all internal junction/current-density/transient bounds. Off/startup devices and dummies are outside documented forward-active ranges; no waiver inferred.',
        internal_node_warning='OSDI #names may follow compressed-node labels; no physical #i1/#i2 identity inferred.',
        proposed_next=dict(status='not run; proposal only',hypothesis='KLU Newton/homotopy initialization basin differs from finite SPARSE OP; temporary external-node guesses may test this.',
            controls='Paired OP-only SPARSE and KLU, identical canonical external-node .nodeset guesses from original SPARSE OP, full11512+27 exact; no internal #nodes, IC, UIC, tolerance, source, card, seed or rail changes.',
            limit_s_per_control=300,interpretation='OP convergence does not demonstrate positive-time stepping speed or fast30 eligibility. Preserve exact OP differences separately.'),
        analyzer_sha256=sha(Path(__file__)))
    a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['status','hbt_counts','external_VBE_range_V','external_VCE_range_V']},indent=2))

if __name__=='__main__':main()

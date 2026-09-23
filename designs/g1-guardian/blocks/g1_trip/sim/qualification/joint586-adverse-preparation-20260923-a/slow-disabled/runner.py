#!/usr/bin/env python3
"""One reviewed adverse OP control, no transient or ensemble dispatch."""
import argparse
import json
import math
from pathlib import Path
import re
import subprocess
import sys
from prepare_joint586_adverse import transform_fixture,make_control,disabled_source,SIM,ROOT,REFERENCE,sha
from prepare_joint586_population import NODES
from run_bgr_substitution_draw_audit import read_group
from run_nominal_clock_probe import run_bounded
from analyze_bgr_substitution_outcomes import warning_inventory


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--contract',type=Path,required=True)
    p.add_argument('--contract-sha256',required=True)
    p.add_argument('--corner',choices=['slow','fast'],required=True)
    p.add_argument('--label',required=True)
    p.add_argument('--image-id',required=True)
    a=p.parse_args()
    assert sha(a.contract)==a.contract_sha256
    packet=json.loads(a.contract.read_text())
    case,=[r for r in packet['op_controls'] if r['corner']==a.corner and r['label']==a.label]
    deck=ROOT/case['deck'];out=deck.parent
    assert not (out/'run.log').exists() and not (out/'summary.json').exists()
    ref=SIM/'qualification'/REFERENCE
    groups=packet['groups']
    logical=str(out.relative_to(SIM/'qualification'))
    original=(ref/'population_transient.cir').read_text().split('.control\n')[0].replace(REFERENCE,logical)
    body,unused=transform_fixture(original,a.corner,3.3,1.2,None)
    assert deck.read_text()==body+make_control(logical,case['seed'],case['temperatures_C'],groups)
    assert sha(deck)==case['deck_sha256']
    assert all(sha(ROOT/name)==digest for name,digest in packet['live_bindings_sha256'].items())
    for name,digest in case['source_hashes'].items():
        assert sha(out/name)==digest
        source=(ref/name).read_text()
        assert (out/name).read_text()==(source if case['enabled'] else disabled_source(source))
    pd=Path('/foss/pdks/ihp-sg13g2')
    runtime=dict(image_id_observed_by_host=a.image_id,pdk_commit=(pd/'COMMIT').read_text().strip(),
        ngspice_version=subprocess.check_output(['ngspice','--version'],universal_newlines=True),
        model_sha256={str(f.relative_to(pd)):sha(f) for f in (pd/'libs.tech/ngspice/models').rglob('*') if f.is_file()},solver='sparse')
    assert runtime==packet['expected_runtime_identity']
    prov=dict(arguments=sys.argv[1:],runtime_identity=runtime,source_hashes=case['source_hashes'],
        input_checks=dict(exact_body_control=True,source_restore=True,contract_binding=True,runtime=True),
        contract_sha256=sha(a.contract),runner_sha256=sha(Path(__file__)),physical_scope=packet['physical_scope'])
    (out/'provenance.json').write_text(json.dumps(prov,indent=2)+'\n')
    (out/'runner.py').write_text(Path(__file__).read_text())
    with (out/'run.log').open('x') as stream:
        state=run_bounded(['ngspice','-b',str(deck.relative_to(SIM))],stream,out/'run.json',case['maximum_wall_s'],cwd=SIM,interval_s=1)
    log=(out/'run.log').read_text()
    errors=[line for line in log.splitlines() if re.search(r'(?i)(^error|timestep too small|doAnalyses:|no such vector|no such parameter|not available|cannot parse)',line)]
    complete=state['status']=='completed' and state['returncode']==0 and not errors and 'POPULATION_OP_END' in log
    phases=[]
    if complete:
        try:
            for index,temp in enumerate(case['temperatures_C']):
                observed={tag+'_'+when:read_group(log,'P%d_%s_%s'%(index,tag,when),keys)
                    for tag,keys in groups.items() for when in ['BEFORE','AFTER']}
                before=observed['NON_BGR_BEFORE']+observed['BGR_BEFORE']
                after=observed['NON_BGR_AFTER']+observed['BGR_AFTER']
                assert len(before)==11512 and before==after and all(math.isfinite(float(v)) for k,v in before)
                values=dict(before)
                assert all(observed['LEGACY27_'+when]==[[k,values[k]] for k in groups['LEGACY27']] for when in ['BEFORE','AFTER'])
                assert all(float(v)>0 for k,v in before if k.endswith(('[w]','[l]','[scale]','[area]')))
                if phases:assert before==phases[0]['parameters_before']
                if not case['enabled']:
                    for k,v in before:
                        if k.endswith(('[delvto]','[nsmm_rsh]','[nsmm_w]','[nsmm_l]')):assert float(v)==0
                        if k.endswith(('[factuo]','[scale]')):assert float(v)==1
                wave=out/('op%d.dat'%index)
                data=[list(map(float,line.split())) for line in wave.read_text().splitlines()[1:] if line.strip()]
                assert len(data)==1 and len(data[0])==10 and all(math.isfinite(v) for v in data[0])
                phases.append(dict(temperature_C=temp,parameters_before=before,parameters_after=after,
                    legacy27=observed['LEGACY27_BEFORE'],op_nodes_V=dict(zip(NODES,data[0][1:])),op_data_sha256=sha(wave)))
        except (AssertionError,ValueError,KeyError,IndexError,OSError) as error:
            errors.append('Inventory/output audit failed: '+repr(error))
    valid=complete and not errors and len(phases)==len(case['temperatures_C'])
    result=dict(op_qualification_status='passed' if valid else 'failed',corner=a.corner,label=a.label,seed=case['seed'],
        enabled=case['enabled'],runtime=state,errors=errors,warnings=warning_inventory(log),phases=phases,
        scope='One bounded owncorner OP control; no transient/population/adoption qualification. Source/model/card unchanged; disabledflags explicit. Cross-run exact/variation checks separate.')
    if valid and len(phases)==4:
        result['return_exact_opdata_bytes']=(out/'op0.dat').read_bytes()==(out/'op3.dat').read_bytes()
        result['return_max_abs_node_change_V']=max(abs(phases[0]['op_nodes_V'][n]-phases[3]['op_nodes_V'][n]) for n in NODES)
        result['return_separate_1uV_bound']=result['return_max_abs_node_change_V']<=1e-6
    (out/'summary.json').write_text(json.dumps([result],indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['warnings','phases']},indent=2))
    raise SystemExit(0 if valid else 1)


if __name__=='__main__':main()

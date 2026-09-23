#!/usr/bin/env python3
"""Reaudit five separate exact-input recoveries without editing original samples."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
from run_586_nearendpoint_recovery import HERE,ROOT,sha,numerical_gate,validate_wave,calibrate
from run_586_population_control import phase_text
from run_586_source_control import load_wave
from run_bgr_substitution_draw_audit import read_group


def checked_phase(state,summary_runtime,log):
    assert state==summary_runtime
    errors=[l for l in log.splitlines() if re.search(r'^Error|Timestep too small|analysis aborted|doAnalyses:|no such vector|no such parameter|not available|cannot parse',l,re.I)]
    numerical_gate(state,errors,log)
    return phase_text(log,0)


def leaf_audit(path,row,prep):
    state=json.loads((path/'run.json').read_text())
    log=(path/'run.log').read_text()
    phase=checked_phase(state,row['runtime'],log)
    before={tag:read_group(phase,'P0_'+tag+'_BEFORE',keys) for tag,keys in prep['groups'].items()}
    after={tag:read_group(phase,'P0_'+tag+'_AFTER',keys) for tag,keys in prep['groups'].items()}
    assert before==after==prep['expected_full3180']==row['parameters_before']==row['parameters_after']
    assert sum(map(len,before.values()))==3180
    blob,data=load_wave(path/'phase0.dat')
    vce=validate_wave(blob,data,prep['expected_header_tokens'])
    assert vce==row['t2f_hbt_external_vce_max_V'] and len(data)==row['wave_rows']
    assert hashlib.sha256(blob).hexdigest()==row['waveform_sha256']
    values={k:float(v) for k,v in re.findall(r'(?m)^(\w+)\s*=\s*([-+0-9.eE]+)',phase)}
    assert values==row['measurements']
    assert all(k in values and math.isfinite(values[k]) for k in ['freq','t_a','t_b','t_half_a','fout_hi','fout_lo'])
    assert values['freq']>0 and values['t_b']>values['t_a']
    return dict(status='passed independent full3180/source/log/header/wave/VCE/scalar audit',frequency_Hz=values['freq'],
        decoded_wave_sha256=hashlib.sha256(blob).hexdigest(),parameters_sha256=hashlib.sha256(json.dumps(before,sort_keys=True).encode()).hexdigest(),
        receipts_sha256={n:sha(path/n) for n in ['probe.cir','summary.json','run.json','run.log']})


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--implementation',type=Path,required=True)
    p.add_argument('--implementation-sha256',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert not a.output.exists() and sha(a.implementation)==a.implementation_sha256
    impl=json.loads(a.implementation.read_text());packet=ROOT/impl['preparation_packet']
    assert sha(packet)==impl['preparation_packet_sha256']
    assert all(sha(ROOT/n)==v for n,v in impl['implementation_bindings_sha256'].items())
    cases=json.loads(packet.read_text())['cases']
    assert [c['seed'] for c in cases]==[74140,74144,74145,74149,74150]
    records=[]
    for case in cases:
        out=HERE/'runs'/case['run_id'];record=dict(seed=case['seed'],run=case['run_id'],evidence_status='not run')
        records.append(record)
        if not (out/'summary.json').exists():continue
        try:
            prep=json.loads((out/'preparation.json').read_text());assert sha(out/'preparation.json')==case['preparation_sha256']
            assert all(sha(ROOT/n)==v for n,v in prep['bindings_sha256'].items())
            assert all(sha(out/n)==v for n,v in prep['source_hashes'].items())
            parent=HERE/'runs'/prep['original_parent'];old=parent/prep['original_leaf']
            assert (out/'probe.cir').read_bytes()==(old/'probe.cir').read_bytes() and sha(out/'probe.cir')==case['exact_deck_sha256']
            inventory=json.loads((out/'population_inventory.json').read_text())
            assert inventory['parameter_count']==3180 and inventory['primitive_count']==1129
            row,=json.loads((out/'summary.json').read_text());state=json.loads((out/'run.json').read_text())
            provenance=json.loads((out/'provenance.json').read_text())
            assert state==row['runtime'] and state['timeout_s']==900
            assert provenance['runtime_identity']==prep['expected_runtime_identity']
            assert provenance['implementation_sha256']==a.implementation_sha256 and all(provenance['input_checks'].values())
            assert sha(out/'runner.py')==provenance['runner_sha256']==sha(HERE/'run_586_nearendpoint_recovery.py')
            record.update(evidence_status='passed input/runtime receipts; failed attempt retained',recovery_status=row['status'],
                original_sample_status='failed original600s unchanged',original_parent_summary_sha256=sha(parent/'summary.json'),
                recovery_receipts_sha256={n:sha(out/n) for n in ['summary.json','run.json','provenance.json','probe.cir','run.log']})
            if row['status'].startswith('passed numerical'):
                recovered=leaf_audit(out,row,prep);frequencies={prep['temperature_C']:recovered['frequency_Hz']};siblings=[]
                for reuse in prep['successful_original_leaf_reuse']:
                    leaf=parent/reuse['leaf'];assert all(sha(leaf/n)==v for n,v in reuse['receipts_sha256'].items())
                    sibling,=json.loads((leaf/'summary.json').read_text());assert sibling['status']==sibling['full3180_status']=='passed'
                    audited=leaf_audit(leaf,sibling,prep);siblings.append(audited)
                    assert sibling['temperature_C'] not in frequencies
                    frequencies[sibling['temperature_C']]=audited['frequency_Hz']
                assert len(siblings)==3 and set(frequencies)=={25,100,-40,125}
                derived=calibrate(frequencies)
                assert derived==row['separate_calibration'] and derived['status']==row['separate_calibration_status']
                record.update(evidence_status='passed independent recovery and three original sibling reaudit',
                    recovery=recovered,original_siblings=siblings,separate_calibration=derived,
                    scope='Recovery-derived calibration is separate; original failed sample denominator/status remains unchanged.')
        except (AssertionError,ValueError,KeyError,OSError,IndexError) as error:
            record.update(evidence_status='failed independent recovery audit',analysis_error=repr(error))
    result=dict(status='completed independent audit; all original failures retained',records=records,
        requested=5,not_run=sum(r['evidence_status']=='not run' for r in records),
        integrity_failures=sum(r['evidence_status']=='failed independent recovery audit' for r in records),
        implementation_sha256=a.implementation_sha256,auditor_sha256=sha(Path(__file__)),
        scope='No replacement, survivor-only denominator, originalstatus rewrite, retryladder or solver change.')
    a.output.write_text(json.dumps(result,indent=2)+'\n');print(a.output,sha(a.output))


if __name__=='__main__':main()

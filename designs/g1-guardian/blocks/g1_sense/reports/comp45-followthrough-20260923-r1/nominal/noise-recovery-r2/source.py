#!/usr/bin/env python3
"""Restore established endpoint handling on saved noise data; no simulator rerun."""
import argparse,json
from pathlib import Path
from run_comp45_followthrough import SOURCE,spectrum
from run_loaded_followthrough import get_reference,errors
from run_loaded_compensation_candidate import parameter_gate,candidate_source
from run_loaded_noise_audit import sha,quiet_values,tests
from run_loaded_ac_audit import observations

def main():
    p=argparse.ArgumentParser();p.add_argument('--leaf',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert not a.output.exists();tests()
    old=json.loads((a.leaf/'summary.json').read_text());contract=json.loads((a.leaf/'contract.json').read_text())
    assert old['status']=='failed' and old['mode']=='noise' and old['analysis_error']=='AssertionError()'
    assert old['runtime']['status']=='completed' and old['runtime']['returncode']==0
    _,ref,prep,expected,_=get_reference('settling','rise')
    assert contract['original_source_hashes']==prep['source_hashes']
    assert json.loads((a.leaf/'provenance.json').read_text())['runtime_identity']==prep['expected_runtime_identity']
    assert (a.leaf/'candidate.spice').read_text()==candidate_source((ref/'sense.spice').read_text(),'62','45')
    assert sha(a.leaf/'candidate.spice')==SOURCE and all(sha(ref/n)==h for n,h in prep['source_hashes'].items())
    log=(a.leaf/'run.log').read_text();assert not errors(log) and 'LOADED_NOISE_END' in log
    result=dict(old);result['original_failed_analysis_error']=result.pop('analysis_error')
    result['parameter_gate']=parameter_gate(log,prep['groups'],expected,'45')
    assert result['quiet_op_V']==quiet_values(log) and result['operating_point']==observations(log)
    result.update(spectrum(a.leaf,log))
    result.update(status='passed candidate followthrough leaf',saved_data_only=True,original_failed_status=old['status'],
        correction='Restore existing original audit endpoint relative1e-12 check and min(requested,savedlast) integration boundary. No solver/tolerance/raw-data change.',
        original_failed_leaf_bindings={n:sha(a.leaf/n) for n in ['summary.json','contract.json','runner.py','candidate.spice','probe.cir','provenance.json','run.log','ac.dat','noise.dat']})
    a.output.mkdir(parents=True);(a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    (a.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['warnings','parameter_gate']},indent=2))
if __name__=='__main__':main()

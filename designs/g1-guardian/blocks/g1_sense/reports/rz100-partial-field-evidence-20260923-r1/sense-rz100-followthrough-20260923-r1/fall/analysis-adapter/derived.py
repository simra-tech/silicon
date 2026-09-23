#!/usr/bin/env python3
"""Independent candidate DC-target step analysis, with no invented timing limit."""
import argparse,json
from pathlib import Path
from expose_rz100_internal_nodes import SOURCE
from run_loaded_followthrough import TARGETS
from run_loaded_noise_audit import sha,table
from analyze_loaded_followthrough import characterize_step,tests

def main():
    p=argparse.ArgumentParser();p.add_argument('--parent',type=Path,required=True);p.add_argument('--case',choices=['rise','fall'],required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert not a.output.exists();control=tests()
    records={};contracts={}
    for mode in ['dc','step']:
        leaf=a.parent/mode;r=json.loads((leaf/'summary.json').read_text());c=json.loads((leaf/'contract.json').read_text())
        assert r['status']=='passed candidate followthrough leaf' and r['mode']==mode and r['case']==a.case
        assert sha(leaf/'candidate.spice')==c['candidate_source_sha256']==SOURCE
        assert r['parameter_gate']['candidate11512_before_after_exact'] and r['parameter_gate']['legacy27_exact']
        records[mode]=r;contracts[mode]=c
    assert contracts['dc']['original_source_hashes']==contracts['step']['original_source_hashes']
    assert records['step']['own_initial_OP_exact'] and records['step']['own_initial_observations_exact']
    assert records['dc']['parameter_gate']['parameters']==records['step']['parameter_gate']['parameters']
    header=['time','v(clk)','v(xt.icmp)','v(xt.vth_soft)','v(xt.vth_hard)','v(cmp_soft)','v(cmp_hard)','v(isense)','v(xt.cmp_clk_n)','v(xt.xch.xp)','v(xt.xch.xq)','v(xt.xch.xn)','v(xt.xch.yn)','v(vref)','v(iptat)','v(vref_buf)','v(vped)','v(shp)']
    wave=table(a.parent/'step/phase0.dat',header)
    result=characterize_step(wave[:,0],wave[:,header.index('v(isense)')],records['step']['quiet_op_V']['v(isense)'],records['dc']['quiet_op_V']['v(isense)'])
    gain=result['amplitude_V']/(TARGETS[a.case]-.025)
    result.update(status='completed candidate settling characterization',case=a.case,candidate_source_sha256=SOURCE,
        DC_endpoint_gain_V_per_V=gain,DC_endpoint_gain_status='passed' if 19.9<=gain<=20.1 else 'failed',
        settling_time_limit='not allocated; reported1% saved-point band is characterization only',
        source_scope='Candidate own-source exact initial9OP/observations/full11512; no original-source transient transfer or population/physical acceptance',
        controls=control,bindings={mode:{n:sha(a.parent/mode/n) for n in ['summary.json','contract.json','candidate.spice','probe.cir','provenance.json','run.log']} for mode in records},
        wave_sha256=sha(a.parent/'step/phase0.dat'))
    a.output.mkdir(parents=True);(a.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()

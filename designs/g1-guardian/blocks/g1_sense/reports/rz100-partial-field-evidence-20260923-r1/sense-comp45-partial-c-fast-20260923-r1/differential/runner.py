#!/usr/bin/env python3
"""Own-source partial-C AC/Tian diagnostic. Never complete physical PM signoff."""
import argparse,json,os,subprocess
from pathlib import Path
import numpy as np
from expose_comp45_internal_nodes import parse,SOURCE
from run_loaded_followthrough import get_reference,adverse_deck,errors
from run_loaded_ac_audit import OBS,observations
from run_loaded_noise_audit import TRIP,IMAGE,MANIFEST,sha,quiet_values,warning_inventory,table,run_bounded
from run_loaded_compensation_candidate import parameter_gate,controls,crossings

def probe(source):
    line,=[line for line in source.splitlines() if line.startswith('XOTA ')]
    words=line.split();assert len(words)==19 and words[1:7]==['vp','vn','iptat','isense','vdd','vss']
    assert words[-1]=='g1_ota_main_candidate'
    changed=' '.join(words[:2]+['main_loop_e']+words[3:])
    assert source.count(line)==1 and 'main_loop_e' not in source
    extra='Vmain_probe main_loop_e vn dc 0 ac {pv}\nImain_probe vss main_loop_e dc 0 ac {pi}\n'
    derived=source.replace(line,changed).replace('.ends',extra+'.ends',1)
    assert derived.replace(extra,'',1).replace(changed,line)==source
    return derived

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ['packet','anchor','output']:p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--baseline',type=Path);p.add_argument('--case',choices=['fast','slow'],required=True)
    p.add_argument('--mode',choices=['differential','tian_voltage','tian_current'],required=True)
    p.add_argument('--cpu',choices=[1,7],type=int,required=True);a=p.parse_args()
    assert os.sched_getaffinity(0)=={a.cpu} and not a.output.exists()
    packet=json.loads((a.packet/'summary.json').read_text());source=(a.packet/'sense_partial_c.spice').read_text()
    assert packet['status']=='prepared incomplete partial-C diagnostic COPY only'
    assert sha(a.packet/'sense_partial_c.spice')==packet['diagnostic_source_sha256'] and packet['original_source_sha256']==SOURCE
    assert packet['added_count']==844 and packet['excluded_count']==134 and packet['exact_inverse']
    assert not packet['primitive_model_or_parameter_changes'] and not packet['full_MIM_pair_subtraction']
    original_anchor=json.loads((a.anchor/'summary.json').read_text())
    assert original_anchor['status']=='passed candidate source/finite leaf' and original_anchor['mode']=='differential' and original_anchor['case']==a.case
    if original_anchor.get('reanalysis_only'):
        anchor_raw=a.anchor.parent/'differential'
        assert all(sha(anchor_raw/n)==h for n,h in original_anchor['original_failed_leaf_bindings'].items())
    else:anchor_raw=a.anchor
    assert sha(anchor_raw/'candidate.spice')==SOURCE
    run,ref,prep,expected,_=get_reference('adverse',a.case)
    base=None
    if a.mode!='differential':
        assert a.baseline;base=json.loads((a.baseline/'summary.json').read_text())
        assert base['status']=='passed partial-C source/OP/finite leaf' and base['mode']=='differential' and base['case']==a.case
        assert base['source_sha256']==packet['diagnostic_source_sha256']
    a.output.mkdir(parents=True);(a.output/'candidate.spice').write_text(source)
    if a.mode!='differential':(a.output/'probe.spice').write_text(probe(source))
    deck=adverse_deck((ref/'population_transient.cir').read_text(),a.output,a.mode,run,prep['groups'])
    if a.mode=='differential':
        old='.include qualification/'+run+'/sense.spice';assert deck.count(old)==1
        deck=deck.replace(old,'.include '+str(a.output/'candidate.spice'))
    (a.output/'probe.cir').write_text(deck);(a.output/'runner.py').write_bytes(Path(__file__).read_bytes())
    contract=dict(case=a.case,mode=a.mode,cpu=a.cpu,source_sha256=packet['diagnostic_source_sha256'],
        canonical_source_sha256=SOURCE,packet_sha256=sha(a.packet/'summary.json'),source_hashes=prep['source_hashes'],
        reference_preparation_sha256=sha(ref/'preparation.json'),original_candidate_anchor_sha256=sha(a.anchor/'summary.json'),
        partial_baseline_sha256=sha(a.baseline/'summary.json') if base else None,watchdog_s=120,
        criteria=dict(gain_min=19.9,gain_max=20.1,BW_min_Hz=2e6,PM_min_deg=60,GM_min_dB=10,probe_V_max=1e-6,probe_A_max=1e-9),
        scope='844 positive full source-net-pair capacitors;134 unbound VSUBS terms explicitly omitted, not physicalzero/bound. No fullfield/adoption claim.',
        probe_plane='Established main inn feedback probe; all extracted ideal-net routing C remains on source nets, nativecompact-device inn moves across series probe. Closed-probe DC equivalence mandatory.')
    (a.output/'contract.json').write_text(json.dumps(contract,indent=2)+'\n')
    pd=Path('/foss/pdks/ihp-sg13g2');runtime=dict(image_id_observed_by_host=MANIFEST,pdk_commit=(pd/'COMMIT').read_text().strip(),
        ngspice_version=subprocess.check_output(['ngspice','--version'],text=True),
        model_sha256={str(f.relative_to(pd)):sha(f) for f in (pd/'libs.tech/ngspice/models').rglob('*') if f.is_file()},solver='sparse')
    assert runtime==prep['expected_runtime_identity']
    (a.output/'provenance.json').write_text(json.dumps(dict(runtime_identity=runtime,OCI_config=IMAGE,runtime_exact=True),indent=2)+'\n')
    with (a.output/'run.log').open('x') as log:state=run_bounded(['ngspice','-b',str(a.output/'probe.cir')],log,a.output/'run.json',120,cwd=TRIP,interval_s=1)
    text=(a.output/'run.log').read_text();result=dict(status='failed partial-C diagnostic',case=a.case,mode=a.mode,runtime=state,
        source_sha256=packet['diagnostic_source_sha256'],errors=errors(text),warnings=warning_inventory(text),complete_field_PM='not qualified')
    try:
        assert state['status']=='completed' and state['returncode']==0 and not result['errors'] and 'LOADED_FOLLOWTHROUGH_END' in text
        assert all(sha(ref/n)==h for n,h in prep['source_hashes'].items())
        assert sha(a.output/'candidate.spice')==packet['diagnostic_source_sha256']
        result['parameter_gate']=parameter_gate(text,prep['groups'],expected,'45')
        op=quiet_values(text);obs=observations(text);result.update(quiet_op_V=op,operating_point=obs)
        if a.mode=='differential':
            result['original_candidate_OP_exact']=op==original_anchor['quiet_op_V']
            result['original_candidate_observations_exact']=obs==original_anchor['operating_point']
            assert result['original_candidate_OP_exact'] and result['original_candidate_observations_exact']
        else:
            delta={n:abs(obs[n]-base['operating_point'][n]) for n in OBS};result['probe_DC_abs_delta']=delta
            assert max(abs(op[n]-base['quiet_op_V'][n]) for n in op)<=1e-6
            assert all(d<=(1e-9 if n.startswith('i(') else 1e-6) for n,d in delta.items())
        header=['frequency','ac_re','ac_im'] if a.mode=='differential' else ['frequency','ir','ii','vr','vi']
        wave=table(a.output/'ac.dat',header);assert wave.shape==(901,len(header))
        if a.mode=='differential':
            basis=table(a.output/'input_basis.dat',['frequency','p_re','p_im','n_re','n_im'])
            assert np.array_equal(basis[:,0],wave[:,0]) and np.max(abs(basis[:,1:]-np.array([.5,0,-.5,0])))<=1e-12
            controls();mag=abs(wave[:,1]+1j*wave[:,2]);db=20*np.log10(mag);bw=crossings(wave[:,0],db,db[0]-3.010299956639812)
            result.update(gain_1Hz_V_per_V=float(mag[0]),gain_status='passed' if 19.9<=mag[0]<=20.1 else 'failed',
                halfpower_downcrossings_Hz=[q[2] for q in bw],bandwidth_status='passed' if bw and bw[0][2]>=2e6 else 'failed')
        result['status']='passed partial-C source/OP/finite leaf'
    except (AssertionError,ValueError,KeyError,IndexError,OSError) as exc:result['analysis_error']=repr(exc)
    (a.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['parameter_gate','warnings']},indent=2))
    raise SystemExit(0 if result['status'].startswith('passed') else 1)

if __name__=='__main__':main()

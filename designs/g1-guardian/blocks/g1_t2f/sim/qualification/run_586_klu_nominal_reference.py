#!/usr/bin/env python3
"""One source-held same-KLU nominal reference; no adoption or population dispatch."""
import argparse,hashlib,json,math,re,subprocess,sys
from pathlib import Path
import numpy as np
from prepare_586_klu_nominal_references import HERE,ROOT,sha,transform
from run_586_source_control import load_wave
from run_bgr_substitution_draw_audit import read_group
from run_nominal_clock_probe import run_bounded
from analyze_bgr_substitution_outcomes import warning_inventory
from run_586_nearendpoint_recovery import validate_wave
from wave_archive import archive_new_wave

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--implementation',type=Path,required=True);p.add_argument('--implementation-sha256',required=True);p.add_argument('--corner',required=True);p.add_argument('--image-id',required=True);a=p.parse_args()
    assert sha(a.implementation)==a.implementation_sha256
    impl=json.loads(a.implementation.read_text());packet_path=ROOT/impl['nominal_packet']
    assert sha(packet_path)==impl['nominal_packet_sha256'] and all(sha(ROOT/n)==v for n,v in impl['implementation_bindings_sha256'].items())
    case,=[c for c in json.loads(packet_path.read_text())['cases'] if c['corner']==a.corner]
    out=HERE/'runs'/case['run_id'];prep=json.loads((out/'preparation.json').read_text());assert sha(out/'preparation.json')==case['preparation_sha256']
    old=HERE/'runs'/prep['original_run'];oldprep=json.loads((old/'preparation.json').read_text());oldprov=json.loads((old/'provenance.json').read_text())
    assert not (out/'run.log').exists() and all(sha(ROOT/n)==v for n,v in prep['bindings_sha256'].items())
    assert sha(out/'probe.cir')==case['deck_sha256']==prep['deck_sha256'] and (out/'probe.cir').read_text()==transform((old/'probe.cir').read_text())
    assert all(sha(out/n)==sha(old/n)==v for n,v in prep['source_hashes'].items())
    oldblob,_=load_wave(old/oldprep['output_wave']);header=oldblob.splitlines()[0].decode().split();assert len(header)==13
    pd=Path('/foss/pdks/ihp-sg13g2')
    runtime=dict(image_id=a.image_id,pdk_commit=(pd/'COMMIT').read_text().strip(),ngspice=subprocess.check_output(['ngspice','--version'],universal_newlines=True),models_sha256={str(f.relative_to(pd)):sha(f) for f in sorted((pd/'libs.tech/ngspice/models').glob('*.lib'))},osdi_sha256={str(f.relative_to(pd)):sha(f) for f in sorted((pd/'libs.tech/ngspice/osdi').glob('*.osdi'))})
    assert runtime==oldprov['runtime_identity']
    (out/'runner.py').write_text(Path(__file__).read_text())
    (out/'provenance.json').write_text(json.dumps(dict(runtime_identity=runtime,input_checks=dict(source=True,deck=True,bindings=True,runtime=True),implementation_sha256=sha(a.implementation),packet_sha256=sha(packet_path),preparation_sha256=sha(out/'preparation.json'),runner_sha256=sha(Path(__file__)),source_hashes=prep['source_hashes']),indent=2)+'\n')
    with (out/'run.log').open('x') as stream:state=run_bounded(['ngspice','-b','probe.cir'],stream,out/'run.json',600,cwd=out,interval_s=1)
    log=(out/'run.log').read_text();errors=[l for l in log.splitlines() if re.search(r'^Error|Timestep too small|analysis aborted|doAnalyses:|no such vector|no such parameter|not available|cannot parse',l,re.I)]
    result=dict(status='failed matched nominal KLU reference',runtime=state,errors=errors,warnings=warning_inventory(log),full3180_status='not run to completion',solver_adoption='not run')
    try:
        assert state['status']=='completed' and state['returncode']==0 and not errors and 'Using KLU as Direct Linear Solver' in log
        before={tag:read_group(log,tag+'_BEFORE',keys) for tag,keys in prep['groups'].items()};after={tag:read_group(log,tag+'_AFTER',keys) for tag,keys in prep['groups'].items()}
        assert sum(map(len,before.values()))==3180 and before==after==prep['expected_full3180']
        blob,data=load_wave(out/oldprep['output_wave']);vce=validate_wave(blob,data,header)
        values={k:float(v) for k,v in re.findall(r'(?m)^(\w+)\s*=\s*([-+0-9.eE]+)',log)}
        assert all(k in values and math.isfinite(values[k]) for k in ['freq','t_a','t_b','t_half_a','fout_hi','fout_lo']) and values['freq']>0 and values['t_b']>values['t_a']
        result.update(status='passed matched nominal KLU reference; SPARSE exact comparison separate',full3180_status='passed',parameters_before=before,parameters_after=after,measurements=values,t2f_hbt_external_vce_max_V=vce,output_wave=oldprep['output_wave'],wave_rows=len(data),waveform_sha256=hashlib.sha256(blob).hexdigest(),original_sparse_decoded_bytes_exact=blob==oldblob)
    except (AssertionError,ValueError,OSError,KeyError,IndexError) as error:result.update(status='failed matched nominal KLU reference',analysis_error=repr(error))
    (out/'summary.json').write_text(json.dumps([result],indent=2)+'\n')
    if (out/oldprep['output_wave']).exists():archive_new_wave(out/oldprep['output_wave'])
    print(json.dumps({k:v for k,v in result.items() if k not in ['warnings','parameters_before','parameters_after']},indent=2));raise SystemExit(0 if result['status'].startswith('passed matched') else 1)

if __name__=='__main__':main()

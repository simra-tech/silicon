#!/usr/bin/env python3
"""Exactly four cohort1 local12x12 paired sites; qualified pilot logic unchanged."""
import argparse,hashlib,json,math,os,re,shutil,sys
from pathlib import Path
import numpy as np
import pya
ROOT=Path(__file__).resolve().parents[4];BASE=Path(__file__).parent
sys.path.insert(0,str(ROOT/'designs/g1-guardian/blocks/g1_top/sim'))
from run_bounded import run_bounded
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--parent-manifest',type=Path,required=True);p.add_argument('--manifest',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
assert not a.output.exists() and len(os.sched_getaffinity(0))==1 and pya.__version__=='0.30.9'
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest();load=lambda path:json.loads(path.read_text())
parent=load(a.parent_manifest);candidate=load(a.manifest);assert candidate['parent_candidate_sha256']==parent['candidate_sha256']
helpers=['prepare_local_via_remaining_clip.py','analyze_local_target_cap.py','run_fill_clip_pex.py','export_clip_lvsdb.lvs'];hashes={name:sha(BASE/name) for name in helpers}
a.output.mkdir(parents=True);out=a.output.resolve();shutil.copyfile(__file__,out/'runner.py');phases=[];checks=[];results={}
contract={'stage_ids':[15, 17, 18, 20],'window_um':[12,12],'parent_sha256':parent['candidate_sha256'],'candidate_sha256':candidate['candidate_sha256'],'helper_hashes':hashes,
    'cut_and_KPEX_child_timeout_s':120,'AC_timeout_s':30,'max_output_bytes':33554432,'AC_abs_tolerance_F':1e-25,'Schur_charge_residual_limit_F':1e-25,
    'expansion':'none; exactly cohort4 four paired sites','boundary':'Proven target-net pieces idealoutsideequipotential; othercontexts grounded, fillgrounded/floating diagnostic; not actualactivity, fullRC, currentmargin orconvergence'}
(out/'contract.json').write_text(json.dumps(contract,indent=2)+'\n')
(out/'derived_runner.py').write_text(DERIVED_SOURCE)

def run(command,leaf,label,limit):
    assert all(sha(BASE/name)==digest for name,digest in hashes.items())
    with (leaf/(label+'.log')).open('x') as stream:state=run_bounded(command,stream,leaf/(label+'.json'),limit,cwd=ROOT,env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1'),interval_s=1)
    phases.append({'path':str(leaf.relative_to(out)),'phase':label,'status':state['status'],'returncode':state['returncode'],'wall_s':state['wall_s']});(out/'phases.json').write_text(json.dumps(phases,indent=2)+'\n')
    assert state['status']=='completed' and state['returncode']==0
    assert sum(path.stat().st_size for path in out.rglob('*') if path.is_file())<=contract['max_output_bytes']
def check_ac(deck,expected):
    run(['ngspice','-b',str(deck)],deck.parent,deck.stem+'_check',30);log=deck.with_name(deck.stem+'_check.log').read_text();values=re.findall(r'^ceff\s*=\s*([-+\d.eE]+)\s*$',log,re.M)
    assert len(values)==1 and 'LOCAL_CAP_AC_END' in log and not re.search(r'(?im)^Error|fatal|timestep too small|doAnalyses:',log)
    observed=float(values[0]);error=abs(observed-expected);assert math.isfinite(observed) and error<=1e-25
    row={'deck':str(deck.relative_to(out)),'expected_F':expected,'observed_F':observed,'abs_error_F':error,'status':'passed'};checks.append(row);(out/'AC_checks.json').write_text(json.dumps(checks,indent=2)+'\n')
# Two distinct target pieces: internal target capacitance must cancel under equal voltage.
synthetic=out/'synthetic';synthetic.mkdir();matrix=np.zeros((4,4))
for i,j,value in [(0,2,2e-15),(1,2,3e-15),(2,3,5e-15),(0,3,1e-15),(0,1,7e-15)]:matrix[i,i]+=value;matrix[j,j]+=value;matrix[i,j]-=value;matrix[j,i]-=value
for mode,expected in [('grounded',6e-15),('floating',3.5e-15)]:
    eff=matrix[:2,:2].copy()
    if mode=='floating':eff-=matrix[:2,2:3]@np.linalg.solve(matrix[2:3,2:3],matrix[2:3,:2])
    actual=float(np.ones(2)@eff@np.ones(2));assert abs(actual-expected)<=1e-25
    fill='0' if mode=='grounded' else 'F';deck=synthetic/(mode+'.cir')
    deck.write_text('* synthetic target-piece aggregation\nC1 P '+fill+' 2f\nC2 P '+fill+' 3f\nC3 '+fill+' 0 5f\nC4 P 0 1f\nVP P 0 AC 1\n.control\nset numdgt=17\nac lin 1 1Meg 1Meg\nlet ceff = -imag(i(VP))/(2*pi*1e6)\nprint ceff\necho LOCAL_CAP_AC_END\nquit\n.endc\n.end\n')
    check_ac(deck,expected)
for label,stage_id in [('vref_corner', 15), ('vref_midleft', 17), ('vref_midright', 18), ('vdda_feed', 20)]:
    results[label]={}
    for view,manifest in [('parent',a.parent_manifest),('candidate',a.manifest)]:
        leaf=out/label/view;leaf.mkdir(parents=True);gds=(manifest.parent/'g1_chip_top.gds').resolve();expected=load(manifest)['candidate_sha256'];assert sha(gds)==expected
        run(['python3',str(BASE/'prepare_local_via_remaining_clip.py'),'--stage-manifest',str(a.manifest.resolve()),'--stage-id',str(stage_id),'--gds',str(gds),'--expected-sha256',expected,'--output',str(leaf/'clip')],leaf,'prepare',120)
        run(['python3',str(BASE/'run_fill_clip_pex.py'),'--clip',str(leaf/'clip'),'--output',str(leaf/'pex')],leaf,'pex',500)
        records=load(leaf/'pex/manifest.json');assert len(records)==2 and all(row['extract_status']=='completed' and row['extract_returncode']==0 and row['kpex_status']=='completed' and row['kpex_returncode']==0 for row in records)
        run(['python3',str(BASE/'analyze_local_target_cap.py'),'--clip',str(leaf/'clip'),'--pex',str(leaf/'pex'),'--output',str(leaf/'analysis')],leaf,'analyze',120)
        summary=load(leaf/'analysis/summary.json');results[label][view]=summary
        for variant in ('no_fill','actual_fill'):
            for mode in ('grounded_fill','floating_fill'):
                value=summary['results'][variant]['modes'][mode];assert math.isfinite(value['floating_charge_residual_F']) and value['floating_charge_residual_F']<=1e-25
                check_ac(leaf/'analysis'/(variant+'_'+mode+'.cir'),value['target_ground_equivalent_fF']*1e-15)
        assert sha(gds)==expected
assert len(checks)==34 and all(row['status']=='passed' for row in checks)
deltas={label:{variant:{mode:results[label]['candidate']['results'][variant]['modes'][mode]['target_ground_equivalent_fF']-results[label]['parent']['results'][variant]['modes'][mode]['target_ground_equivalent_fF'] for mode in ('grounded_fill','floating_fill')} for variant in ('no_fill','actual_fill')} for label in results}
result={'status':'passed cohort4 four pairedsites and32ACcomparisons plus2syntheticcontrols','contract_sha256':sha(out/'contract.json'),'deltas_fF':deltas,'results':results,
    'physical_scope':'stages15,17,18,20 only; no automaticotherstageexpansion. Local metal-only load under declaredboundaries; notfullRC/activity/currentmargin/convergence/electricaladoption.'}
(out/'summary.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({key:value for key,value in result.items() if key!='results'},indent=2))

"""Bound original-rule full-parent main DRC; no signoff outside this scope."""
import argparse,json,os,subprocess,time,xml.etree.ElementTree as ET,sys
from pathlib import Path
from inspect_soft_inputpair4_parent_r1 import ROOT,PARENT,PARENT_SHA,sha
sys.path.insert(0,str(ROOT/'designs/g1-guardian/review/audits/io_tap_closure/physical_source/integration_purefill'))
import current_rz_bindings as prior
import current_rz_stock_preconditions as pre

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--candidate-dir',required=True);ap.add_argument('--run-dir',required=True);a=ap.parse_args()
    out=Path(a.candidate_dir);run=Path(a.run_dir);assert not run.exists()
    preparation=json.loads((out/'preparation.json').read_text())
    assert sha(PARENT)==PARENT_SHA==preparation['parent_sha256']
    assert sha(out/'candidate.gds')==preparation['candidate_sha256']
    assert sha(out/'candidate.cdl')==preparation['candidate_reference_sha256']
    assert all(preparation[k] is True for k in ['all_original_instances_exact','all_non_target_cells_exact','macro_pin_text_boundary_layers_exact','root_shapes_and_fill_held'])
    assert os.sched_getaffinity(0)=={2}
    pdk=Path('/foss/pdks/ihp-sg13g2');assert (pdk/'COMMIT').read_text().strip()=='84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
    expected=json.loads(prior.bound(prior.PHYSICAL['main']).read_text())['stock_rule_hashes']
    def held():return pre.require_rules(pre.rule_files(expected),pre.rule_files(pre.rule_tree(pdk,'libs.tech/klayout/tech')))
    assert held();bound={str(p):sha(p) for p in [out/'preparation.json',out/'candidate.gds',out/'candidate.cdl',Path(__file__)]}
    command=['python3',str(pdk/'libs.tech/klayout/tech/drc/run_drc.py'),'--path='+str(out/'candidate.gds'),'--topcell='+preparation['top'],'--run_mode=deep','--no_density','--run_dir='+str(run)]
    log=Path(str(run)+'.engine.log');assert not log.exists();start=time.monotonic()
    with log.open('x') as stream:
        try:rc=subprocess.run(command,stdout=stream,stderr=subprocess.STDOUT,timeout=1150).returncode
        except subprocess.TimeoutExpired:rc=124
    reports=list(run.glob('*.lyrdb')) if run.exists() else []
    markers=len(ET.parse(reports[0]).findall('.//items/item')) if len(reports)==1 else None
    unchanged=all(sha(Path(n))==h for n,h in bound.items());rules=held()
    result=dict(status='passed full-parent main/no-density DRC' if rc==0 and markers==0 and unchanged and rules else 'failed full-parent main/no-density DRC',
        returncode=rc,markers=markers,wall_s=time.monotonic()-start,command=command,inputs_sha256=bound,
        stock_rules_held=rules,inputs_held=unchanged,log_sha256=sha(log),reports_sha256={str(p):sha(p) for p in reports},
        not_run=['separate density','separate antenna','canonical full-parent LVS','loaded electrical','adoption'])
    summary=Path(str(run)+'.summary.json')
    with summary.open('x') as stream:json.dump(result,stream,indent=2)
    print(json.dumps(result));raise SystemExit(0 if result['status'].startswith('passed') else 1)
if __name__=='__main__':main()

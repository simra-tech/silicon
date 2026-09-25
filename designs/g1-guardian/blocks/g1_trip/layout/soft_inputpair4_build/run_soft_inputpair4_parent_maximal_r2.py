"""Run only unfinished stock maximal table; retain completed main and timeout."""
import argparse,importlib.util,json,os,subprocess,sys,time,xml.etree.ElementTree as ET
from pathlib import Path
from inspect_soft_inputpair4_parent_r1 import ROOT,sha
sys.path.insert(0,str(ROOT/'designs/g1-guardian/review/audits'))
from run_core_maximal_only import PDK,DRC,switches
sys.path.insert(0,str(ROOT/'designs/g1-guardian/review/audits/io_tap_closure/physical_source/integration_purefill'))
import current_rz_bindings as prior
import current_rz_stock_preconditions as pre
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--candidate-dir',required=True);ap.add_argument('--execute',action='store_true');a=ap.parse_args()
    out=Path(a.candidate_dir);gds=out/'candidate.gds';run=out/'drc-maximal-r2'
    original=out/'drc-main.summary.json';old=json.loads(original.read_text());prep=json.loads((out/'preparation.json').read_text())
    assert old['returncode']==124 and old['stock_rules_held'] and old['inputs_held']
    assert len(old['reports_sha256'])==1
    mainpath,digest=next(iter(old['reports_sha256'].items()));mainpath=Path(mainpath)
    assert mainpath.name.endswith('_main.lyrdb') and sha(mainpath)==digest
    assert len(ET.parse(mainpath).findall('.//items/item'))==0
    assert "tables 'main' completed in 487.47 seconds" in (out/'drc-main.engine.log').read_text()
    assert sha(gds)==prep['candidate_sha256'] and os.sched_getaffinity(0)=={2}
    assert (PDK/'COMMIT').read_text().strip()=='84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
    expected=json.loads(prior.bound(prior.PHYSICAL['main']).read_text())['stock_rule_hashes']
    def held():return pre.require_rules(pre.rule_files(expected),pre.rule_files(pre.rule_tree(PDK,'libs.tech/klayout/tech')))
    assert held()
    sys.path.insert(0,str(DRC));spec=importlib.util.spec_from_file_location('pinned_stock_drc',DRC/'run_drc.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    sw=switches(module,gds,prep['top']);assert str(sw['threads'])=='1'
    if a.execute:
        module.run_check(DRC/'rule_decks/sg13g2_maximal.drc',['sg13g2_maximal'],str(gds),run/'reports',sw);return
    assert not run.exists();(run/'reports').mkdir(parents=True)
    bindings={str(p):sha(p) for p in [gds,out/'candidate.cdl',out/'preparation.json',original,mainpath,Path(__file__),ROOT/'designs/g1-guardian/review/audits/run_core_maximal_only.py']}
    cmd=['timeout','--kill-after=5','1130','python3',str(Path(__file__).resolve()),'--candidate-dir',str(out),'--execute'];start=time.monotonic()
    with (run/'engine.log').open('x') as stream:rc=subprocess.run(cmd,stdout=stream,stderr=subprocess.STDOUT).returncode
    reports=[]
    for p in (run/'reports').glob('*_sg13g2_maximal.lyrdb'):
        reports.append(dict(path=str(p),sha256=sha(p),markers=len(ET.parse(p).findall('.//items/item'))))
    unchanged=held() and all(sha(Path(p))==h for p,h in bindings.items())
    passed=rc==0 and unchanged and len(reports)==1 and reports[0]['markers']==0
    result=dict(status='passed scoped maximal DRC' if passed else 'failed scoped maximal DRC',returncode=rc,wall_s=time.monotonic()-start,reports=reports,
        bindings_sha256=bindings,stock_rules_and_inputs_held=unchanged,command=cmd,switches={k:str(v)for k,v in sw.items()},
        previous_combined_timeout_retained=True,reused_main=dict(sha256=digest,markers=0,wall_s=487.47),
        thread_policy='Explicit threads1, same CPU2 affinity; previous requested128/effective NLWP1 retained',
        not_run=['density','antenna','native CPEX','loaded electrical','population/adoption'])
    with (run/'summary.json').open('x') as stream:json.dump(result,stream,indent=2)
    print(result['status']);raise SystemExit(0 if passed else 1)
if __name__=='__main__':main()

"""Strict projected-reference stock LVS of isolated soft-pair parent.

Canonical source is retained separately. No unprojected canonical credit.
"""
import argparse,json,os,subprocess,sys
from pathlib import Path
from inspect_soft_inputpair4_parent_r1 import ROOT,sha
from prepare_soft_inputpair4_parent_r3 import SOURCE,reference
sys.path.insert(0,str(ROOT/'designs/g1-guardian/review/audits/io_tap_closure/physical_source/integration_purefill'))
import run_osc_r095_fullchip_stock_lvs as baseline
def read(p):return json.loads(p.read_text())
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--candidate-dir',required=True);ap.add_argument('--run-dir',required=True);a=ap.parse_args()
    out=Path(a.candidate_dir);run=Path(a.run_dir);assert not run.exists()
    files,deck,rules_held=baseline.prove_inputs();assert os.sched_getaffinity(0)=={2}
    geom=read(out/'independent_geometry_audit.json');prep=read(out/'preparation.json')
    assert geom['status']=='passed independent exact non-target and bounded soft-cell/q-feed delta audit'
    assert geom['all_original_instances_exact'] and geom['all_non_target_geometry_text_exact'] and geom['root_shapes_fill_and_macro_die_pins_exact']
    assert sha(out/'candidate.gds')==prep['candidate_sha256'] and (out/'candidate.cdl').read_text()==reference(SOURCE.read_text())
    projected=out/'comparison-r1/comparison_only.cdl';projection=read(out/'comparison-r1/summary.json');flat=out/'flat-r1/physical_AP_three_dummy_flat_reference.cdl';flatproof=read(out/'flat-r1/summary.json')
    assert projection['reverse_bytes_exact'] is True and projection['only_two_soft_size_lines_changed'] is True
    assert projection['canonical_source_sha256']==sha(out/'candidate.cdl') and projection['projected_source_sha256']==sha(projected)
    assert len(projection['removed'])==3 and all(r['nodes']==['VDD']*4 and r['model']=='SG13_HV_PMOS' for r in projection['removed'].values())
    assert flatproof['status']=='passed exact stock-reader source flatten roundtrip' and flatproof['input_sha256']==sha(projected) and flatproof['output_sha256']==sha(flat)
    assert flatproof['primitive_count']==76059 and flatproof['roundtrip_pairs']['device']=={'Match':76059} and flatproof['roundtrip_pairs']['pin']=={'Match':22}
    for name in ['candidate.gds','candidate.cdl','preparation.json','independent_geometry_audit.json','comparison-r1/comparison_only.cdl','comparison-r1/summary.json','flat-r1/physical_AP_three_dummy_flat_reference.cdl','flat-r1/summary.json']:
        files[out/name]=sha(out/name)
    files[Path(__file__).resolve()]=sha(Path(__file__))
    cmd=['python3',str(deck),'--layout',str(out/'candidate.gds'),'--netlist',str(flat),'--topcell',baseline.TOP,'--run_mode','deep','--top_lvl_pins','--spice_comments','--run_dir',str(run)]
    log=Path(str(run)+'.engine.log');assert not log.exists()
    with log.open('x') as stream:
        try:rc=subprocess.run(cmd,stdout=stream,stderr=subprocess.STDOUT,timeout=1050).returncode
        except subprocess.TimeoutExpired:rc=124
    analysis=run/'strict_analysis.json';parser=baseline.prior.bound(baseline.prior.STRICT_PARSER)
    parse=['python3',str(parser),'--reports',str(run),'--returncode',str(rc),'--top',baseline.TOP,'--pins-json',str(baseline.prior.bound(baseline.prior.EXPECTED_PINS)),'--output',str(analysis),'--mode','deep']
    with Path(str(run)+'.parser.log').open('x') as stream:
        try:prc=subprocess.run(parse,stdout=stream,stderr=subprocess.STDOUT,timeout=70).returncode
        except subprocess.TimeoutExpired:prc=124
    strict=read(analysis) if analysis.exists() else {};held=rules_held() and baseline.pre.require_bound_hashes(files)
    passed=rc==prc==0 and strict.get('status')=='passed strict saved comparison' and strict.get('checks') and all(strict['checks'].values()) and held
    result=dict(status='passed projected-reference strict stock LVS' if passed else 'failed projected-reference strict stock LVS',engine_returncode=rc,parser_returncode=prc,
        canonical_source_sha256=sha(out/'candidate.cdl'),comparison_source_sha256=sha(flat),candidate_gds_sha256=sha(out/'candidate.gds'),
        source_projection_is_not_canonical=True,canonical_unprojected_LVS='not run',source_omissions='three independently proved unchanged all-VDD pad dummy PMOS, comparison only',
        native_scope='Existing exact OSC dummy proof plus independent exact non-target geometry/instance preservation',
        independent_geometry_audit_sha256=sha(out/'independent_geometry_audit.json'),bound_inputs_sha256={str(p):h for p,h in files.items()},
        stock_rules_and_inputs_held=held,analysis_sha256=sha(analysis) if analysis.exists() else None,command=cmd,
        not_run=['loaded electrical','population qualification','adoption'])
    with Path(str(run)+'.summary.json').open('x') as stream:json.dump(result,stream,indent=2)
    print(result['status']);raise SystemExit(0 if passed else 1)
if __name__=='__main__':main()

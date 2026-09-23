#!/usr/bin/env python3
"""Pinned strict stock LVS runner for the current RZ100 physical candidate.

The primitive-flat CDL is comparison-only. The canonical circuit source stays
unchanged and is separately hash-bound. This wrapper never weakens stock ports.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import current_rz_bindings as b
import current_rz_stock_preconditions as pre

TOP='placed_core_NOT_CONNECTED_FULLCHIP'
PIN='84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
def read(spec):return json.loads(b.bound(spec).read_text())
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--summary',type=Path,required=True)
    ap.add_argument('--execute',action='store_true')
    ap.add_argument('--run-dir',type=Path)
    ap.add_argument('--resource-gate',type=Path);a=ap.parse_args()
    assert not a.summary.exists()
    assert os.sched_getaffinity(0)=={0},'this bounded stock wrapper requires CPU0 only'
    canonical=b.bound(b.ORIGINAL_SOURCE);layout=b.bound(b.CANDIDATE);reference=b.bound(b.FLAT_REFERENCE)
    parser=b.bound(b.STRICT_PARSER);pins=b.bound(b.EXPECTED_PINS)
    bound_files={canonical:b.ORIGINAL_SOURCE[1],layout:b.CANDIDATE[1],
                 reference:b.FLAT_REFERENCE[1],parser:b.STRICT_PARSER[1],
                 pins:b.EXPECTED_PINS[1]}
    pre.require_bound_hashes(bound_files)
    dummy=read(b.DUMMY_PROOF);flat=read(b.FLAT_REFERENCE_PROOF);identity=read(b.IDENTITY_PROOF)
    assert dummy['status']=='passed independent three-dummy source/native-terminal proof'
    assert flat['status']=='passed exact stock-reader source flatten roundtrip'
    assert flat['output_sha256']==b.FLAT_REFERENCE[1] and identity['candidate_GDS_sha256']==b.CANDIDATE[1]
    assert identity['flattened_all_layer_nontext_XOR_dbu2']==0
    assert b.sha(canonical)==b.ORIGINAL_SOURCE[1] and b.sha(reference)==b.FLAT_REFERENCE[1]
    pdk=Path(os.environ.get('PDK_ROOT','/foss/pdks'))/os.environ.get('PDK','ihp-sg13g2')
    assert (pdk/'COMMIT').read_text().strip()==PIN
    deck=pdk/'libs.tech/klayout/tech/lvs/run_lvs.py';assert deck.is_file()
    lvs_rules=read(b.STOCK_LVS_RULE_BASELINE)['stock_rule_hashes']
    tech_rules=read(b.PHYSICAL['main'])['stock_rule_hashes']
    def rules_held():
        pre.require_rules(pre.rule_files(lvs_rules),pre.rule_files(pre.rule_tree(pdk,'libs.tech/klayout/tech/lvs')))
        pre.require_rules(pre.rule_files(tech_rules),pre.rule_files(pre.rule_tree(pdk,'libs.tech/klayout/tech')))
        return True
    assert rules_held()
    result=dict(status='running',top=TOP,canonical_source_sha256=b.ORIGINAL_SOURCE[1],
        comparison_only_source_sha256=b.FLAT_REFERENCE[1],layout_gds_sha256=b.CANDIDATE[1],
        dummy_proof_sha256=b.DUMMY_PROOF[1],flat_source_proof_sha256=b.FLAT_REFERENCE_PROOF[1],
        strict_missing_ports=True,stock_deck_unmodified=True,
        generated_python_bytecode_excluded_from_rule_hash_match=True,
        comparison_source_is_not_canonical_source=True,
        source_device_omissions='exactly three separately proved source-only VDD-to-VDD pad dummies')
    a.summary.parent.mkdir(parents=True,exist_ok=True)
    if not a.execute:
        strict=read(b.STRICT_ANALYSIS);db=b.bound(b.STRICT_DB)
        assert strict['status']=='passed strict saved comparison' and all(strict['checks'].values())
        assert strict['database']['layout'][TOP]['devices']==61684
        assert strict['database']['layout'][TOP]['nets']==31173
        assert len(strict['database']['layout'][TOP]['pins'])==22 and db.is_file()
        result.update(status='passed exact existing strict stock LVS evidence bound; new engine not run',
                      prior_analysis_sha256=b.STRICT_ANALYSIS[1],prior_lvsdb_sha256=b.STRICT_DB[1],
                      new_engine_run='not run')
    else:
        assert a.run_dir is not None and not a.run_dir.exists()
        assert a.resource_gate is not None and a.resource_gate.is_file()
        gate=json.loads(a.resource_gate.read_text())
        pre.require_affinity(gate,os.sched_getaffinity(0),0)
        cmd=['python3',str(deck),'--layout',str(layout),'--netlist',str(reference),
             '--topcell',TOP,'--run_mode','deep','--top_lvl_pins','--spice_comments',
             '--run_dir',str(a.run_dir)]
        log=a.summary.with_suffix('.engine.log');assert not log.exists()
        with log.open('x') as stream:
            try:
                engine=subprocess.run(['timeout','--kill-after=5','600']+cmd,
                                      stdout=stream,stderr=subprocess.STDOUT,check=False,timeout=610)
                engine_rc=engine.returncode
            except subprocess.TimeoutExpired:
                engine_rc=124
        analysis=a.run_dir/'strict_analysis.json'
        parsed_rc=None
        if a.run_dir.is_dir() and not analysis.exists():
            parse_cmd=['python3',str(parser),'--reports',str(a.run_dir),
                       '--returncode',str(engine_rc),'--top',TOP,'--pins-json',str(pins),
                       '--output',str(analysis),'--mode','deep']
            parse_log=a.summary.with_suffix('.parser.log');assert not parse_log.exists()
            with parse_log.open('x') as stream:
                try:
                    parsed=subprocess.run(['timeout','--kill-after=5','60']+parse_cmd,
                                          stdout=stream,stderr=subprocess.STDOUT,check=False,timeout=70)
                    parsed_rc=parsed.returncode
                except subprocess.TimeoutExpired:
                    parsed_rc=124
        strict=json.loads(analysis.read_text()) if analysis.is_file() else {}
        try:rules_after=rules_held()
        except AssertionError:rules_after=False
        try:bindings_after=pre.require_bound_hashes(bound_files)
        except (AssertionError,OSError):bindings_after=False
        passed=(engine_rc==0 and parsed_rc==0 and
                strict.get('status')=='passed strict saved comparison' and
                all(strict.get('checks',{}).values()) and rules_after and bindings_after)
        result.update(status='passed strict stock deep LVS' if passed else 'failed strict stock deep LVS',
                      new_engine_run='passed' if passed else 'failed',engine_returncode=engine_rc,
                      parser_returncode=parsed_rc,stock_command=cmd,
                      stock_deck_unmodified=rules_after,
                      bound_inputs_unchanged_after_engine=bindings_after,
                      analysis_sha256=b.sha(analysis) if analysis.is_file() else None)
    a.summary.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(status=result['status'],new_engine_run=result['new_engine_run'])))
    raise SystemExit(0 if result['status'].startswith('passed') else 1)
if __name__=='__main__':main()

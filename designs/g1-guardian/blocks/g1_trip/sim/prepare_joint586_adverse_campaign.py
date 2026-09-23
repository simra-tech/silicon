#!/usr/bin/env python3
"""Freeze required adverse30 scheduling/criteria contract; never launch samples."""
import argparse
import difflib
import json
from pathlib import Path
from prepare_joint586_adverse import SIM,ROOT,CONDITIONS,sha


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--campaign-id',required=True)
    a=p.parse_args();assert '/' not in a.campaign_id
    out=SIM/'qualification'/a.campaign_id;assert not out.exists();out.mkdir()
    prior=SIM/'qualification/joint586-adverse-preparation-20260923-a/contract.json'
    original=json.loads(prior.read_text())
    assert original['population_seeds']==dict(slow=list(range(77101,77131)),fast=list(range(78101,78131)))
    paths=[prior,Path(__file__),SIM/'run_joint586_adverse_calibration.py',SIM/'run_joint586_calibration.py',
        SIM/'run_joint_calibration.py',SIM/'audit_bgr_calibration_tree.py',SIM/'prepare_bgr_calibration_probe.py',
        SIM/'prepare_joint586_adverse.py',SIM/'prepare_joint586_adverse_transients.py',
        SIM/'run_joint586_transients.py',SIM/'run_nominal_clock_probe.py',SIM/'run_bgr_substitution_draw_audit.py',
        SIM/'run_bgr_substitution_transient.py',SIM/'wave_archive.py',SIM/'analyze_bgr_substitution_outcomes.py',
        SIM/'result_directory.py',SIM/'audit_joint586_adverse_transients.py',SIM/'audit_joint586_adverse_fixture_controls.py']
    bindings={str(q.absolute().relative_to(ROOT)):sha(q) for q in paths}
    for corner in ['slow','fast']:
        for name in ['joint586-'+corner+'-transqual-shn-20260923-b.json','joint586-'+corner+'-fixture-controls-20260923-b.json']:
            path=SIM/'qualification'/name;bindings[str(path.relative_to(ROOT))]=sha(path)
    old=(SIM/'run_joint586_calibration.py').read_text();new=(SIM/'run_joint586_adverse_calibration.py').read_text()
    (out/'declared_runner_difference.diff').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),
        fromfile='frozenTypical300Runner',tofile='requiredOwncorner30Runner')))
    contract=dict(status='prepared only; ownTRANS/sixfixtures/firstsample gates required before expansion',
        sample_count_per_corner=30,population_seeds=original['population_seeds'],conditions=[list(c) for c in CONDITIONS],
        watchdog_per_leaf_s=1200,expected_leaves_per_sample=70,source_hashes=original['canonical_source_hashes'],
        runtime_identity=original['expected_runtime_identity'],inventory_count=11512,legacy_count=27,randomized_primitives=3500,
        live_bindings_sha256=bindings,runner_difference_sha256=sha(out/'declared_runner_difference.diff'),
        calibration=original['calibration'],sampling=original['sampling'],physical_scope=original['physical_scope'],
        progression='Eachcorner own10TRANS controls and sixrail/CM controls. First independent sample complete evidence audit. Then exactfirst20 screen and independent disposition before final10. Valid electricalfails retained; numerical/source/parameter/harness failures require disposition before dependent expansion. Fixed30 denominator, no retries/replacements/filtering.',
        required_crossed_CM_deterministic_status='not run; remaining144declared crossedCM/temp/rail guards/residuals are a separate obligation, not covered by this population',
        required_crossed_CM_conditions=original['remaining_selected_deterministic_conditions'],forecast=original['forecast'])
    (out/'contract.json').write_text(json.dumps(contract,indent=2)+'\n')
    print(str((out/'contract.json').relative_to(ROOT)),sha(out/'contract.json'))


if __name__=='__main__':main()

#!/usr/bin/env python3
"""Declare the remaining144 crossed common-mode checks; no analog launch."""
import argparse,json
from pathlib import Path
from run_joint586_adverse_staged import SIM,ROOT,sha


def rows(conditions):
    guards=[(.027,False,False),(.033,True,False),(.9*204*1.04/5300,True,False),(1.1*204*1.04/5300,True,True)]
    result=[]
    for corner,seed in [('slow',77101),('fast',78101)]:
        for index,condition in enumerate(conditions):
            label='crossed%02d'%index
            fixture=[label,condition['temperature_C'],condition['VDDA_V'],condition['VDD_V'],condition['true_common_mode_V']]
            for kind,code_key,values in [('guard','corrected_codes',guards),('residual','fixed_residual_codes',[(.0245,False,False),(.0255,True,True)])]:
                for shunt,soft,hard in values:
                    result.append(dict(corner=corner,seed=seed,condition=fixture,kind=kind,calibration_code_key=code_key,
                        shunt_V=shunt,expected_decisions=dict(soft=soft,hard=hard)))
    assert len(result)==144
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();assert not a.output.exists()
    prior=SIM/'qualification/joint586-adverse30-contract-20260923-b/contract.json'
    contract=json.loads(prior.read_text());assert sha(prior)=='2bff2817772337148c16d3c4d7d7ed432a41715cd69d8eb0bff3c4e35202438c'
    assert all(sha(ROOT/n)==v for n,v in contract['live_bindings_sha256'].items())
    checks=rows(contract['required_crossed_CM_conditions'])
    result=dict(status='not run; prospective remaining deterministic coverage only',
        prior_contract_sha256=sha(prior),source_hashes=contract['source_hashes'],runtime_identity=contract['runtime_identity'],
        inventory_count=11512,legacy_count=27,wave_columns=19,endpoint_s=1.02e-6,leaf_watchdog_s=1200,
        planned_leaf_count=144,planned_conditions_per_corner=12,checks=checks,
        code_and_vector_binding='NOTRUN until each own firstsample independent staged audit passes source/numerical/bracket gate. Use that same seed77101or78101 frozen originalbinary corrected and fixedresidual codes plus all11512 parameters. No newindependent sample, no refit and no population-count credit.',
        required_preflight='Prepare exactdecks only after actualcode/vector bindings exist. Use unchanged adverse_deck transform; only declared temp/rails/trueCM and originalguard/residual shunt/codes. Require everylive source/helper/runtime/parameter binding and actualSHP/SHNmean/differential. Own firstsample electricalfails stayfailed; do not selectanother seed.',
        acceptance='Original fourguard expecteddecisions and two halfmV residualdecisions, actual/legacy sampling unchanged. Retain everyfailed/missing/numerical leaf; no interpolation or waiver.',
        scheduling='Independent fresh one-thread leaves, unique directories, host resource/CPUleases beforelaunch. Not authorized by this file alone; this is a frozen scope declaration, not a runnable harness or completedqualification.',
        forecast_cpu_hours=contract['forecast']['projected_deterministic_cpu_hours'],
        maximum_watchdog_cpu_hours=144*1200/3600,
        preparer_sha256=sha(Path(__file__)),
        helper_sha256={n:sha(SIM/n) for n in ['run_joint586_adverse_staged.py','audit_joint586_adverse_staged.py','prepare_joint586_adverse.py','prepare_joint586_adverse_transients.py']},
        physical_scope=contract['physical_scope'])
    a.output.write_text(json.dumps(result,indent=2)+'\n');print(sha(a.output))


if __name__=='__main__':main()

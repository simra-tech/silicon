#!/usr/bin/env python3
"""Source/AP/model-branch and complete positive-network controls; no analog."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

HERE = Path(__file__).resolve().parent


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--receipt', type=Path, required=True)
    ap.add_argument('--resource-gate', type=Path, required=True)
    a = ap.parse_args()
    assert not a.receipt.exists() and set(os.sched_getaffinity(0)) == {48}
    gate = json.loads(a.resource_gate.read_text())
    assert gate['status'] == 'passed' and gate['project_cpu_budget'] >= 56
    assert gate['ram_available_bytes'] >= 16*2**30 and gate['external_allocation']['expected_growth_gib'] >= 2
    bulk = Path(os.environ['G1_RESULTS_ROOT'])
    layout = HERE.parent
    candidate = bulk/'bgr-dvbe-cuts-candidate-20260923-r2'
    drc = bulk/'bgr-dvbe-cuts-drc-20260923-r2'
    lvs = bulk/'bgr-dvbe-cuts-lvs-20260923-r2'
    context = bulk/'bgr-dvbe-cuts-parent-context-20260923-r3/analysis.json'
    context_result = json.loads(context.read_text())
    assert context_result['status'] == 'passed held-parent source-owned clearance'
    assert context_result['inputs'][str(candidate/'bank.gds')] == sha(candidate/'bank.gds')
    assert all(sha(Path(p)) == h for p, h in context_result['inputs'].items())
    for folder in (drc, lvs):
        result = json.loads((folder/'summary.json').read_text())
        assert result['status'] == 'passed'
        assert result['inputs'][str(candidate/'bank.gds')] == sha(candidate/'bank.gds')
    preparation = bulk/'bgr-dvbe-cuts-metal-prepare-20260923-r1'
    fixture = bulk/'bgr-dvbe-cuts-fixture-20260923-r1'
    source = layout.parent/'sim/qualification/candidates/bgr_loop24_qref4_r253p465_hv06/bgr_loop24_qref4_r253p465_hv06.spice'
    base_fixture = layout.parent/'sim/qualification/runs/bgr586-raw-current-ledger-20260922-a/nominal.cir'
    baseline = bulk/'bgr-external-pin-metal-prepare-20260923-r3'
    models = bulk/'bgr-dvbe-cuts-screen-20260923-r2/pinned_models.json'
    scripts = [layout/'coordinated_full_closure/audit_junctions.py',
               layout/'coordinated_dvbe_remedy_20260923/prepare_metal.py',
               HERE/'run_network.py', layout/'coordinated_return_remedy/extract_metal_r.py',
               layout/'coordinated_return_remedy/audit_metal_r_solution.py',
               layout/'coordinated_dvbe_followup_20260923/prepare_fixture.py',
               layout/'coordinated_model_boundary/audit_external_pin_source.py', HERE/'audit_bn.py']
    paths = [Path(__file__).resolve(), a.resource_gate, context, source, base_fixture, models,
             candidate/'preparation.json', candidate/'bank.gds', candidate/'bank.cdl',
             drc/'summary.json', lvs/'summary.json', baseline/'summary.json', baseline/'points.json']+scripts
    inputs = {str(p): sha(p) for p in paths}
    a.receipt.mkdir(parents=True)
    (a.receipt/'source.py').write_bytes(Path(__file__).read_bytes())
    result = dict(status='running', inputs=inputs, stages=[], analog='not run', adoption='not run')

    def save():
        (a.receipt/'summary.json').write_text(json.dumps(result, indent=2)+'\n')

    def run(name, args):
        command = ['python3']+[str(x) for x in args]
        start = time.monotonic()
        with (a.receipt/(name+'.log')).open('x') as log:
            child = subprocess.run(['timeout', '-k', '5', '90']+command, stdout=log, stderr=subprocess.STDOUT)
        result['stages'].append(dict(name=name, command=command, returncode=child.returncode,
                                     wall_s=time.monotonic()-start, watchdog_s=90))
        save()
        assert child.returncode == 0, name

    save()
    try:
        run('source336AP', [scripts[0], '--stock', lvs, '--output', lvs/'junction_audit.json'])
        run('model_BN_branches', [scripts[7], '--models', models, '--output', bulk/'bgr-dvbe-cuts-BN-audit-20260923-r1'])
        run('metal_preparation', [scripts[1], '--candidate', candidate, '--baseline-preparation', baseline,
                                 '--output', preparation, '--resource-gate', a.resource_gate, '--drc', drc, '--lvs', lvs])
        networks = {}
        for scenario, control in [('KPEX', 'bgr-metal-r-controls-kpex-20260922-r4'), ('LEF', 'bgr-metal-r-controls-lef-20260922-r2')]:
            name = 'bgr-metal-r-dvbe-cuts-'+scenario.lower()+'-20260923-r1'
            networks[scenario] = bulk/name
            run('metal_'+scenario, [scripts[2], '--run-id', name, '--preparation', preparation,
                '--resource-gate', a.resource_gate, '--mode', 'full', '--scenario', scenario,
                '--control', bulk/control/'result/summary.json'])
            run('independent_'+scenario, [scripts[4], '--result', networks[scenario]/'result',
                                         '--output', networks[scenario]/'independent_audit.json'])
        run('fixture_preparation', [scripts[5], '--source', source, '--fixture', base_fixture,
            '--preparation', preparation, '--kpex-network', networks['KPEX'], '--lef-network', networks['LEF'],
            '--baseline-points', baseline/'points.json', '--output', fixture, '--resource-gate', a.resource_gate])
        run('independent_source', [scripts[6], '--prepared', fixture, '--source', source])
        assert all(sha(Path(p)) == h for p, h in inputs.items())
        result.update(status='passed source/AP/model-branch/positive-network controls; analog not run', prepared_fixture=str(fixture))
    except Exception as exc:
        result.update(status='failed', error=repr(exc))
        raise
    finally:
        save()
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()

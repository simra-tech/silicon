#!/usr/bin/env python3
"""Read-only matched OP comparison and complete stationary model KCL."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    assert set(os.sched_getaffinity(0)) == {48}
    bulk = Path(os.environ['G1_RESULTS_ROOT'])
    run = bulk/'bgr-dvbe-cuts-kpex-20260923-r1'
    prep = bulk/'bgr-dvbe-cuts-fixture-20260923-r1'
    out = bulk/'bgr-dvbe-cuts-comparison-20260923-r1'
    assert not out.exists()
    analyze = HERE.parent/'coordinated_model_boundary/analyze_external_pin.py'
    compare = HERE.parent/'coordinated_dvbe_remedy_20260923/compare_dvbe.py'
    source = HERE.parents[1]/'sim/qualification/candidates/bgr_loop24_qref4_r253p465_hv06/bgr_loop24_qref4_r253p465_hv06.spice'
    bn = bulk/'bgr-dvbe-cuts-BN-audit-20260923-r1/analysis.json'
    kcl = HERE/'audit_complete_dc_kcl.py'
    inputs = {str(p):sha(p) for p in (analyze, compare, source, bn, kcl,
        run/'summary.json', run/'metal_node_voltages.json', prep/'summary.json', Path(__file__).resolve())}
    out.mkdir()
    (out/'source.py').write_bytes(Path(__file__).read_bytes())
    result = dict(status='running saved-data audit', inputs=inputs, stages=[], new_simulation='not run')
    commands = [[sys.executable,str(analyze),'--run',str(run),'--prepared',str(prep)]]
    for bprep,brun,name in [('bgr-supply-fixture-20260923-r1','bgr-supply-kpex-20260923-r1','vs_supply_parent.json'),
                          ('bgr-external-pin-source-20260923-r1','bgr-external-pin-kpex-20260923-r1','vs_original.json')]:
        commands.append([sys.executable,str(compare),'--baseline-prepared',str(bulk/bprep),
            '--candidate-prepared',str(prep),'--baseline-run',str(bulk/brun),
            '--candidate-run',str(run),'--source',str(source),'--output',str(out/name)])
    commands.append([sys.executable,str(kcl),'--run',str(run),'--prepared',str(prep),
                     '--BN-proof',str(bn),'--output',str(out/'stationary_model_KCL.json')])
    try:
        for index, command in enumerate(commands):
            with (out/('stage%d.log'%index)).open('x') as log:
                child = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=60)
            result['stages'].append(dict(command=command, returncode=child.returncode))
            assert child.returncode == 0, index
        comparison = json.loads((out/'vs_supply_parent.json').read_text())
        assert all(sha(Path(p)) == h for p,h in inputs.items())
        result.update(status='passed complete saved-data comparisons; conditional not qualified',
            delta_VREF_V=comparison['delta_VREF_V'], remaining_VREF_error_V=comparison['remaining_VREF_error_V'],
            exact_maximum_principle='passed' if comparison['after']['exact_maximum_principle'] else 'failed',
            exact_maximum_excursion_V=comparison['after']['maximum_principle_excursion_V'],
            physical_BN_attachment='not run/unresolved', model_contact_partition='unresolved',
            PVT_startup_stability='not run', integration='not run', adoption='not run')
    except Exception as exc:
        result.update(status='failed saved-data audit', error=repr(exc))
        raise
    finally:
        (out/'summary.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('inputs','stages')}, indent=2))


if __name__ == '__main__':
    main()

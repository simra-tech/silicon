#!/usr/bin/env python3
"""Bounded, output-only internal AC/OP observation with exact baseline parity."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import numpy as np
from prepare_loaded_bandwidth_observation import build
from run_loaded_followthrough import get_reference, check_parameters, errors
from run_loaded_noise_audit import (IMAGE, MANIFEST, TRIP, sha, read_group,
                                   quiet_values, warning_inventory, table, run_bounded)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert os.sched_getaffinity(0) == {1} and args.output.is_absolute()
    assert not args.output.exists()
    baseline = json.loads((args.baseline/'summary.json').read_text())
    assert baseline['status'] == 'passed source/OP/finite leaf'
    assert baseline['kind'] == 'adverse' and baseline['mode'] == 'differential'
    run, ref, prep, expected, op = get_reference('adverse', baseline['case'])
    assert baseline['reference_summary_sha256'] == sha(ref/'summary.json')
    assert baseline['full11512_and27_exact'] and baseline['quiet_op_V'] == op
    old_contract = json.loads((args.baseline/'contract.json').read_text())
    assert sha(args.baseline/'probe.cir') == old_contract['deck_sha256']
    originals = {name:sha(args.baseline/name) for name in
                 ['summary.json','contract.json','provenance.json','probe.cir','ac.dat','input_basis.dat']}
    deck, contract = build((args.baseline/'probe.cir').read_text(),
                           (ref/'sense.spice').read_text(), prep['groups'],
                           args.baseline, args.output)
    args.output.mkdir(parents=True)
    contract.update(case=baseline['case'], reference_run=run,
                    baseline_sha256=originals, source_hashes=prep['source_hashes'],
                    child_timeout_s=120, strict_output_parity_required=True,
                    scope='Native compact-model observables only; no geometry/physical terminal partition or new compensation adoption.')
    (args.output/'contract.json').write_text(json.dumps(contract,indent=2)+'\n')
    (args.output/'probe.cir').write_text(deck)
    for name in ['run_loaded_bandwidth_observation.py','prepare_loaded_bandwidth_observation.py']:
        (args.output/name).write_bytes(Path(__file__).with_name(name).read_bytes())
    pd = Path('/foss/pdks/ihp-sg13g2')
    runtime = dict(image_id_observed_by_host=MANIFEST,
        pdk_commit=(pd/'COMMIT').read_text().strip(),
        ngspice_version=subprocess.check_output(['ngspice','--version'],universal_newlines=True),
        model_sha256={str(f.relative_to(pd)):sha(f) for f in
                      (pd/'libs.tech/ngspice/models').rglob('*') if f.is_file()},solver='sparse')
    (args.output/'provenance.json').write_text(json.dumps(dict(runtime_identity=runtime,
        OCI_manifest_digest=MANIFEST,OCI_config_digest=IMAGE,
        runtime_exact=runtime==prep['expected_runtime_identity']),indent=2)+'\n')
    assert runtime == prep['expected_runtime_identity']
    with (args.output/'run.log').open('x') as stream:
        state = run_bounded(['ngspice','-b',str(args.output/'probe.cir')],stream,
                            args.output/'run.json',120,cwd=TRIP,interval_s=1)
    log = (args.output/'run.log').read_text()
    result = dict(status='failed',case=baseline['case'],runtime=state,
                  errors=errors(log),warnings=warning_inventory(log))
    try:
        assert state['status']=='completed' and state['returncode']==0
        assert not result['errors'] and 'LOADED_FOLLOWTHROUGH_END' in log
        assert all(sha(args.baseline/name)==h for name,h in originals.items())
        assert all(sha(ref/name)==h for name,h in prep['source_hashes'].items())
        check_parameters(log,prep['groups'],expected)
        result['full11512_and27_exact'] = True
        observed = quiet_values(log)
        result['quiet_op_exact'] = observed == op
        result['quiet_op_V'] = observed
        assert result['quiet_op_exact']
        for name in ['ac.dat','input_basis.dat']:
            result[name+'_byte_exact'] = (args.output/name).read_bytes()==(args.baseline/name).read_bytes()
            assert result[name+'_byte_exact']
        quantities = read_group(log,'BANDWIDTH_DEVICE_OP',contract['op_queries'])
        assert len(quantities)==190
        result['model_observables'] = quantities
        ac = table(args.output/'ac.dat',['frequency','ac_re','ac_im'])
        nodes = table(args.output/'bandwidth_nodes.dat',contract['columns'])
        assert nodes.shape==(901,37) and np.array_equal(nodes[:,0],ac[:,0])
        result['finite_node_spectra'] = 18
        result['source_inverse_exact'] = contract['source_inverse_exact']
        result['status'] = 'passed output-only source/parameter/OP/AC parity'
    except (AssertionError,ValueError,KeyError,IndexError,OSError) as exc:
        result['analysis_error'] = repr(exc)
    (args.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['warnings','model_observables']},indent=2))
    raise SystemExit(0 if result['status'].startswith('passed') else 1)


if __name__ == '__main__':
    main()

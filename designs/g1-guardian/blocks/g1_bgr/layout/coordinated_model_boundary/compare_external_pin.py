#!/usr/bin/env python3
"""Compare completed M1/M2-boundary nominal OPs without adopting either."""
import argparse
import hashlib
import json
from pathlib import Path


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--bulk', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    a = ap.parse_args()
    assert not a.output.exists()
    inputs = {}
    rows = []
    for case in ('kpex', 'lef'):
        old = a.bulk / ('bgr-metal-sensitivity-' + case + '-20260922-r1')
        new = a.bulk / ('bgr-external-pin-' + case + '-20260923-r1')
        values = []
        for folder in (old, new):
            for name in ('summary.json', 'conditional_analysis.json'):
                inputs[str(folder/name)] = sha(folder/name)
            summary = json.loads((folder/'summary.json').read_text())
            result = json.loads((folder/'conditional_analysis.json').read_text())
            assert summary['status'] == 'passed conditional nonlinear OP completion and source controls'
            assert summary['all2842_parameters_exact'] and not summary['errors']
            assert result['source_devices'] == 1036 and result['source_net_count'] == 55
            values.append((summary,result))
        os, ov = values[0]
        ns, nv = values[1]
        assert os['parameter_before'] == ns['parameter_before']
        oldports = ov['actual_macro_ports']
        newports = nv['actual_macro_ports']
        assert set(oldports) == set(newports) and len(newports) == 9
        rows.append(dict(case=case, original_source_VREF_V=nv['source_net_voltage_ranges']['vref']['zero_R_V'],
            old_M1_VREF_V=oldports['vref']['voltage_V'], new_M2_VREF_V=newports['vref']['voltage_V'],
            plane_only_delta_VREF_V=newports['vref']['voltage_V']-oldports['vref']['voltage_V'],
            new_delta_from_original_VREF_V=newports['vref']['voltage_V']-nv['source_net_voltage_ranges']['vref']['zero_R_V'],
            old_supply_current_into_metal_A=oldports['vdd']['current_into_metal_A'],
            new_supply_current_into_metal_A=newports['vdd']['current_into_metal_A'],
            new_wall_s=ns['runtime']['wall_s'], old_wall_s=os['runtime']['wall_s'],
            finite_points=ns['finite_point_count'], finite_nodes=ns['finite_node_count'],
            new_positive_edges=nv['positive_edges'], full2842_parameter_parity=True,
            interior_KCL_max_A=nv['metal_interior_KCL_max_A'],
            inferred_MOS_HBT_terminal_KCL_max_A=nv['inferred_MOS_HBT_point_KCL_max_A'],
            resistor_terminal_KCL=nv['resistor_end_current_attribution'],
            warnings=ns['warnings']))
    result = dict(status='passed completed-view comparison; neither view physically qualified',
        cases=rows, inputs=inputs, worker_sha256=sha(Path(__file__)),
        temperature_startup_stability_MC='not run', physical_model_plane_qualification='failed to establish',
        canonical_source_changes='not applicable; source held', adoption='not run')
    a.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Nominal model-inferred1036port ledger, explicitly distinct from individual metering."""
import argparse
import json
from pathlib import Path
import re
from run_586_pvt import sha

HERE = Path(__file__).resolve().parent


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    mapping_path = HERE/'bgr586-terminal-mapping-provisional-20260922.json'
    mapping = json.loads(mapping_path.read_text())
    control = HERE/'runs/bgr586-external22port-control-20260922-a'
    qualified = json.loads((control/'analysis.json').read_text())
    assert qualified['status'].startswith('passed independent nominal22port')
    assert qualified['full2842_before_after_original_exact'] and qualified['canonical_source_restoration_exact']
    assert qualified['maximum_abs_mapping_delta_A'] <= qualified['prospective_per_port_bound_A'] == 1e-12
    assert mapping['source_devices'] == 1036 and mapping['nodes'] == 55
    raw = HERE/mapping['run']
    assert sha(raw/'summary.json') == mapping['summary_sha256'] and sha(raw/'provenance.json') == mapping['provenance_sha256']
    assert mapping['source_sha256'] == '586ffb58b6af31c77a2e7cbcb83b173ffa4713ec62401da30901c5a7e606283b'
    records, emitter = [], []
    for old in mapping['device_records']:
        row = dict(source_id=old['source_name'], model=old['model'], source_terminal_nodes=old['terminals'],
                   inferred_external_port_current_A=old['candidate_external_currents_A'],
                   inferred_injection_into_wire_A={key: -value for key, value in old['candidate_external_currents_A'].items()},
                   internal_drain_source_swapped=old['internal_drain_source_swapped'],
                   provenance='Model-field interpretation at canonical nominal firstOP, with representative22port mapping qualification; NOT individually instrumented device ports.')
        if old['source_name'].startswith('XR'):
            row['substrate_current_basis'] = 'Zero is inferred at this nominalDCOP from explicitly metered rhighXR1 and rppdXR16 representative substrate terminals; not directly queried for this resistor and not a transient/all-temperature zero claim.'
        records.append(row)
        if re.fullmatch(r'XQ(?:56|60|62|67)(?:_u\d+)?', row['source_id']):
            emitter.append({'source_id': row['source_id'], 'emitter_source_node': row['source_terminal_nodes']['E'],
                            'port_current_entering_device_A': row['inferred_external_port_current_A']['E'],
                            'injection_into_return_wire_A': row['inferred_injection_into_wire_A']['E']})
    assert len(emitter) == 76
    result = {'status': 'completed nominal model-inferred externalport ledger with representative qualification',
              'source_sha256': mapping['source_sha256'], 'source_devices': len(records), 'nominal_temperature_C': 27,
              'positive_sign_convention': 'External portcurrent enters device. Injection from device into its connected wire is the negative.',
              'raw_ledger_run': mapping['run'], 'raw_ledger_receipts': {'summary_sha256': mapping['summary_sha256'], 'provenance_sha256': mapping['provenance_sha256']},
              'representative_control': {'run': str(control.relative_to(HERE)), 'analysis_sha256': sha(control/'analysis.json'),
                                         'original_failed_summary_sha256': sha(control/'summary.json'), 'maximum_abs_mapping_delta_A': qualified['maximum_abs_mapping_delta_A'],
                                         'prospective_per_port_bound_A': qualified['prospective_per_port_bound_A'], 'original_dc_bytes_exact': qualified['original_dc_bytes_exact']},
              'interpretation_audit_sha256': sha(mapping_path), 'node_voltages_V': mapping['node_voltage_V'],
              'aggregate_node_kcl_residual_A': mapping['candidate_kcl_residual_A'], 'aggregate_maximum_abs_kcl_residual_A': mapping['candidate_maximum_abs_kcl_residual_A'],
              'devices': records, 'selected_hbt_return_emitters': emitter,
              'selected_hbt_return_injection_sum_A': sum(r['injection_into_return_wire_A'] for r in emitter),
              'scope': 'Nominal27C,3.3V,standaloneideal1VIPTAT/1pFVREF, mismatchdisabled. Actualraw3885fields/full2842/originalDCwave exact control, with separatelymetered22representativeports. Full1036externalport values are model-basedinferences. Original22port runnerJSONfailure and originalwaveexactfailure retained. 55nodeaggregateKCLmax1.296pA is reported, not assigned a new acceptancebound. For first-order nominalwire/LEF sensitivity only; not fullIR, transientpeaks, process/mismatch envelope, physicalCC adoption or lifetime qualification.'}
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ['devices', 'selected_hbt_return_emitters', 'node_voltages_V', 'aggregate_node_kcl_residual_A']}, indent=2))


if __name__ == '__main__':
    main()

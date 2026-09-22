#!/usr/bin/env python3
"""Expose candidate mapping assumptions and KCL residuals, not a qualified port ledger."""
import argparse
from collections import defaultdict
import json
from pathlib import Path
from run_586_pvt import sha

HERE = Path(__file__).resolve().parent


def candidate_mos(fields, vd, vs):
    assert len(fields) == 5 and fields[4] in [-1, 1]
    result = [value*fields[4] for value in fields[:4]]
    swapped = (vd-vs)*fields[4] < 0
    if swapped:
        result[0], result[2] = result[2], result[0]
    return result, swapped


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    run = HERE/'runs/bgr586-raw-current-ledger-20260922-a'
    summary, = json.loads((run/'summary.json').read_text())
    prov = json.loads((run/'provenance.json').read_text())
    assert summary['status'].startswith('passed raw ledger') and summary['full2842_before_after_original_exact'] and summary['original_dc_bytes_exact']
    fields = {key: float(value) for key, value in summary['raw_fields']}
    nodes = dict(zip(prov['node_order'], [summary['op_node_and_supply_values'][v] for v in prov['exported_vectors'][:55]]))
    residuals = defaultdict(float)
    records = []
    for row in prov['source_device_inventory']:
        values = [fields[q] for q in row['queries']]
        keys = list(row['terminals'])
        nets = list(row['terminals'].values())
        if row['source_name'].startswith('XM'):
            currents, swapped = candidate_mos(values, nodes[nets[0]], nodes[nets[2]])
            interpretation = 'Candidate ctype times rawPSP total fields, with D/Sswap when ctype*(VD−VS)<0; representative external-probe validation not run.'
        elif row['source_name'].startswith('XQ'):
            currents = values[:3]+[-values[4]-values[5]]
            swapped = None
            interpretation = 'Candidate intrinsicC/B/E direct and externalBN=−Rsub[i]−Csub[i]; thermalexcluded. Representative external-probe validation not run.'
        else:
            currents = [-values[0], values[0], 0.0]
            swapped = None
            interpretation = 'Diagnostic ONLY: internalibody direction2→1 assigned to ends and BNset0 to inspect nodeKCL. External end/substrate currents remain unavailable/unqualified; zero is an explicit test assumption, not a measured current.'
        for net, value in zip(nets, currents):
            residuals[net] += value
        records.append({'source_name': row['source_name'], 'model': row['model'], 'terminals': row['terminals'],
                        'candidate_external_currents_A': dict(zip(keys, currents)), 'internal_drain_source_swapped': swapped,
                        'interpretation': interpretation, 'qualification_status': 'not run; candidate mapping only'})
    for net, vector in [('vdd', 'i(vdd)'), ('iptat', 'i(vload)'), ('r4', 'i(vr4)')]:
        value = summary['op_node_and_supply_values'][vector]
        residuals[net] += value
        residuals['vss'] -= value
    result = {'status': 'observed candidate mapping consistency; external-port qualification not run',
              'run': str(run.relative_to(HERE)), 'source_sha256': prov['source_sha256'], 'summary_sha256': sha(run/'summary.json'), 'provenance_sha256': sha(run/'provenance.json'),
              'source_devices': len(records), 'nodes': len(residuals), 'node_voltage_V': nodes,
              'candidate_kcl_residual_A': dict(residuals), 'candidate_maximum_abs_kcl_residual_A': max(abs(x) for x in residuals.values()),
              'device_records': records,
              'scope': 'Read-only interpretation of exact-parity rawOPfields. No criterion adopted after observing residuals, no physicalIR proof. 399resistor external/substrate currents not measured; displayedzero is an explicitly provisional consistency assumption. Native PSPorientation/ctype and HBTwrapper mapping require representative external-probe controls before use as qualified port currents.'}
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ['device_records', 'node_voltage_V', 'candidate_kcl_residual_A']}, indent=2))


if __name__ == '__main__':
    main()

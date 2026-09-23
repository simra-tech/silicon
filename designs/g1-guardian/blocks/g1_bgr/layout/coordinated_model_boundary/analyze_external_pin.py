#!/usr/bin/env python3
"""Read-only conditional OP attribution; no physical qualification inferred."""
import argparse
import collections
import hashlib
import json
import math
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
QUAL = HERE.parents[1] / 'sim/qualification'
sys.path.insert(0, str(QUAL))
from audit_586_raw_terminal_mapping import candidate_mos


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--run', type=Path, required=True)
    ap.add_argument('--prepared', type=Path, required=True)
    a = ap.parse_args()
    summary = json.loads((a.run / 'summary.json').read_text())
    assert summary['status'] == 'passed conditional nonlinear OP completion and source controls'
    temperature = re.findall(r'Doing analysis at TEMP = (\S+) and TNOM = (\S+)', (a.run / 'run.log').read_text())
    assert temperature == [('27.000000', '27.000000')]
    case = summary['case']
    folder = a.prepared / case
    prep = json.loads((a.prepared / 'summary.json').read_text())
    scenario = next(s for s in prep['scenarios'] if s['scenario'].lower() == case)
    assert all(sha(folder / n) == h for n, h in scenario['outputs'].items())
    assert summary['preparation_sha256'] == sha(a.prepared / 'summary.json')
    voltage = json.loads((a.run / 'metal_node_voltages.json').read_text())
    edges = json.loads((folder / 'positive_edges.json').read_text())
    terms = json.loads((folder / 'terminal_map.json').read_text())
    points = json.loads((folder / 'point_nodes.json').read_text())
    anchors = json.loads((folder / 'anchors.json').read_text())
    point_nodes = {p['node'] for p in points}
    assert len(voltage) == scenario['contracted_node_count'] and all(math.isfinite(v) for v in voltage.values())
    raw = {k: float(v) for k, v in summary['raw_fields']}
    reference = QUAL / 'runs/bgr586-raw-current-ledger-20260922-a'
    ref, = json.loads((reference / 'summary.json').read_text())
    prov = json.loads((reference / 'provenance.json').read_text())
    old_fields = {k: float(v) for k, v in ref['raw_fields']}
    oldvoltage = {net: ref['op_node_and_supply_values'][expr] for net, expr in zip(prov['node_order'], prov['exported_vectors'])}
    port_qualification = QUAL / 'runs/bgr586-external22port-control-20260922-a/analysis.json'
    qualification = json.loads(port_qualification.read_text())
    assert qualification['status'].startswith('passed')
    current_parts = collections.defaultdict(list)
    edge_power, largest_edges = [], []
    for edge in edges:
        delta = voltage[edge['a']] - voltage[edge['b']]
        current = delta / edge['R_ohm']
        current_parts[edge['a']].append(current)
        current_parts[edge['b']].append(-current)
        edge_power.append(delta * current)
        largest_edges.append(dict(resistor=edge['resistor'], a=edge['a'], b=edge['b'],
                                  delta_V=delta, current_A=current, R_ohm=edge['R_ohm']))
    outgoing = {node: math.fsum(v) for node, v in current_parts.items()}
    interior = {node: value for node, value in outgoing.items() if node not in point_nodes}
    mapped = {(t['source_id'], t['terminal']): t for t in terms}
    device_records, model_kcl, unqualified_r_nodes = [], collections.defaultdict(list), set()
    for row in prov['source_device_inventory']:
        name = row['source_name']
        values = [raw[q] for q in row['queries']]
        terminal_names = list(row['terminals'])
        newv = {t: voltage[mapped[(name, t)]['new']] for t in terminal_names if (name, t) in mapped}
        if name.startswith('XM'):
            currents, swapped = candidate_mos(values, newv['D'], newv['S'])
            _, old_swapped = candidate_mos([old_fields[q] for q in row['queries']],
                                           oldvoltage[row['terminals']['D']], oldvoltage[row['terminals']['S']])
            attribution = 'Representative-probe-qualified wrapper mapping, inferred for this device/new bias; actual local D/S voltages and ctype used'
        elif name.startswith('XQ'):
            currents, swapped, old_swapped = values[:3] + [-values[4] - values[5]], None, None
            attribution = 'Representative-probe-qualified wrapper mapping, inferred for this device/new bias; internal thermal node excluded'
        else:
            currents, swapped, old_swapped = None, None, None
            attribution = 'Raw ibody only; no inferred BN zero or complete external-current mapping at new split bias'
            unqualified_r_nodes.update(mapped[(name, t)]['new'] for t in ('1', '2'))
        if currents is not None:
            for term, value in zip(terminal_names, currents):
                model_kcl[mapped[(name, term)]['new']].append(value)
        device_records.append(dict(source_id=name, model=row['model'], terminal_voltage_V=newv,
                                   voltage_change_from_zero_V={t: v - oldvoltage[row['terminals'][t]] for t, v in newv.items()},
                                   current_entering_device_A=dict(zip(terminal_names, currents)) if currents is not None else None,
                                   raw_resistor_ibody_A=values[0] if currents is None else None,
                                   drain_source_swapped=swapped, original_drain_source_swapped=old_swapped,
                                   attribution=attribution))
    device_kcl = {node: math.fsum([outgoing[node]] + values) for node, values in model_kcl.items()
                  if node not in unqualified_r_nodes}
    net_points = collections.defaultdict(list)
    for p in points:
        net_points[p['source_net']].append(voltage[p['node']])
    net_results = {net: dict(min_V=min(v), max_V=max(v), span_V=max(v) - min(v),
                             zero_R_V=oldvoltage[net], max_absolute_change_from_zero_V=max(abs(x - oldvoltage[net]) for x in v))
                   for net, v in net_points.items()}
    actual_ports = {p['source_net']: dict(voltage_V=voltage[p['source_net']],
                                         current_into_metal_A=outgoing[p['source_net']])
                    for p in anchors if p['kind'] == 'actual macro port'}
    result = dict(status='completed conditional saved-OP attribution; no electrical qualification',
                  observed_TEMP_C=27, observed_TNOM_C=27,
                  case=case, source_devices=1036, nodes=len(voltage), positive_edges=len(edges),
                  source_net_count=55, total_metal_power_W=math.fsum(edge_power),
                  metal_interior_KCL_max_A=max(abs(v) for v in interior.values()),
                  metal_interior_nodes=len(interior),
                  inferred_MOS_HBT_point_KCL_max_A=max(abs(v) for v in device_kcl.values()),
                  inferred_MOS_HBT_point_nodes=len(device_kcl),
                  MOS_orientation_changes=sum(r['drain_source_swapped'] != r['original_drain_source_swapped'] for r in device_records if r['source_id'].startswith('XM')),
                  actual_macro_ports=actual_ports, source_net_voltage_ranges=net_results,
                  resistor_BN_current='not available; not assumed zero at changed bias',
                  resistor_end_current_attribution='not run; excluded from complete-current/KCL claim',
                  full_device_terminal_KCL='not run / incomplete', physical_reference_plane='unresolved',
                  double_count='unresolved native-metal/model overlap', adoption='not run',
                  largest_100_edge_voltage_differences=sorted(largest_edges, key=lambda r: abs(r['delta_V']), reverse=True)[:100],
                  devices=device_records,
                  inputs={str(p): sha(p) for p in [a.run / 'summary.json', a.run / 'run.log', a.run / 'metal_node_voltages.json',
                      folder / 'positive_edges.json', folder / 'terminal_map.json', folder / 'point_nodes.json',
                      folder / 'anchors.json', reference / 'summary.json', reference / 'provenance.json',
                      port_qualification, QUAL / 'audit_586_raw_terminal_mapping.py', Path(__file__)]})
    output = a.run / 'conditional_analysis.json'
    assert not output.exists()
    output.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ('devices', 'inputs', 'largest_100_edge_voltage_differences', 'source_net_voltage_ranges')}, indent=2))


if __name__ == '__main__':
    main()

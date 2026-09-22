#!/usr/bin/env python3
"""Prepare, never simulate, exact nominal T2F controls for final BGR586 coverage."""
import argparse
import collections
import difflib
import hashlib
import json
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
BLOCKS = HERE.parents[2]
ROOT = HERE.parents[5]
sys.path.insert(0, str(BLOCKS/'g1_trip/sim'))
from result_directory import allocate_run

BASE = HERE/'runs/t2f_interpolation_probe_20260921_01'
BGR = BLOCKS/'g1_bgr/sim/qualification/runs/bgr_one_draw_20260922_r1'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory(source, prefix):
    queries, primitives = [], []
    for line in source.splitlines():
        fields = line.split()
        if not fields:
            continue
        name = fields[0].lower()
        if line.startswith('XM'):
            keys = ['@n.'+prefix+'.'+name+'.n'+fields[5]+'['+p+']' for p in ['w', 'l', 'delvto', 'factuo']]
            kind = 'MOS'
        elif line.startswith('XR'):
            keys = ['@n.'+prefix+'.'+name+'.nr1['+p+']' for p in ['nsmm_rsh', 'nsmm_w', 'nsmm_l']]
            kind = 'R'
        elif line.startswith('XQ'):
            keys = ['@q.'+prefix+'.'+name+'.qnpn13g2[area]']
            kind = 'HBT'
        elif line.startswith('XC'):
            keys = ['@c.'+prefix+'.'+name+'.c1[scale]']
            kind = 'CMIM'
        else:
            continue
        queries.extend(keys)
        primitives.append(dict(instance=prefix+'.'+name, kind=kind, source_line=line, queries=keys))
    assert len(queries) == len(set(queries))
    return queries, primitives


def query_block(tag, queries):
    return 'echo '+tag+'_BEGIN\n'+''.join('print '+q+'\n' for q in queries)+'echo '+tag+'_END\n'


def transform(original, temperature, groups, host_replay=False):
    assert original.count('.temp 12.5\n') == 1
    assert original.count('set num_threads=1\n') == 1
    assert original.count('tran 5n 32u\n') == 1
    if host_replay:
        assert temperature == 12.5 and not groups
        return original
    result = original.replace('.temp 12.5\n', '.temp '+str(float(temperature))+'\n')
    before = ''.join(query_block(tag+'_BEFORE', queries) for tag, queries in groups.items())
    after = ''.join(query_block(tag+'_AFTER', queries) for tag, queries in groups.items())
    return result.replace('tran 5n 32u\n', 'op\n'+before+'tran 5n 32u\n'+after)


def strip_queries(deck):
    return re.sub(r'(?m)^echo (BGR|T2F)_(BEFORE|AFTER)_BEGIN\n.*?^echo \1_\2_END\n', '', deck, flags=re.S)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--campaign-id', required=True)
    args = p.parse_args()
    assert re.fullmatch('[a-z0-9-]+', args.campaign_id)
    destination = HERE/(args.campaign_id+'.json')
    assert not destination.exists()
    legacy = json.loads((BASE/'manifest.json').read_text())
    nominal = json.loads((BGR/'manifest.json').read_text())
    source_new = BGR/'disabled/pex_nominal.spice'
    assert sha(source_new) == nominal['source_sha256'] == '586ffb58b6af31c77a2e7cbcb83b173ffa4713ec62401da30901c5a7e606283b'
    assert all(sha(BASE/name) == expected for name, expected in legacy['realized_netlist_sha256'].items())
    assert sha(BASE/'.spiceinit') == legacy['input_sha256']['.spiceinit']
    original = (BASE/'ptat_T12.5.cir').read_text()
    case, = [row for row in legacy['cases'] if row['temperature_C'] == 12.5]
    assert case['status'] == 'passed' and case['deck_sha256'] == sha(BASE/'ptat_T12.5.cir')
    assert case['completed_tstop_s'] == 32e-6
    tq, ti = inventory((BASE/'t2f.spice').read_text(), 'xt2f')
    oq, oi = inventory((BASE/'bgr.spice').read_text(), 'xbgr')
    nq, ni = inventory(source_new.read_text(), 'xbgr')
    assert len(tq) == 338 and len(oq) == 242 and len(nq) == 2842
    assert nq == nominal['parameters']
    disabled, = [row for row in nominal['cases'] if row['name'] == 'disabled']
    assert disabled['parameters_before'] == disabled['parameters_after']
    paths = [BASE/n for n in ['manifest.json', 'ptat_T12.5.cir', 'ptat_T12.5.dat', 'ptat_T12.5.log', 'bgr.spice', 't2f.spice', '.spiceinit']]+[BGR/'manifest.json', source_new, Path(__file__).resolve()]
    binding = {str(path.relative_to(ROOT)): sha(path) for path in paths}
    definitions = [('old-host', 'old', 12.5, True), ('old-inventory', 'old', 12.5, False), ('new-paired', '586', 12.5, False),
                   ('new-t25', '586', 25, False), ('new-t100', '586', 100, False), ('new-tm40', '586', -40, False), ('new-t125', '586', 125, False)]
    prepared, normalized = [], {}
    for label, source_kind, temp, host in definitions:
        run_id = args.campaign_id+'-'+label
        out = allocate_run(HERE.parent, run_id, relative_parent='qualification/runs')
        sources = {'bgr.spice': BASE/'bgr.spice' if source_kind == 'old' else source_new, 't2f.spice': BASE/'t2f.spice', '.spiceinit': BASE/'.spiceinit'}
        for name, path in sources.items():
            (out/name).write_bytes(path.read_bytes())
        groups = {} if host else {'BGR': oq if source_kind == 'old' else nq, 'T2F': tq}
        deck = transform(original, temp, groups, host_replay=host)
        (out/'probe.cir').write_text(deck)
        (out/'declared_fixture_difference.diff').write_text(''.join(difflib.unified_diff(original.splitlines(True), deck.splitlines(True), fromfile='qualifiedOldNominal12p5', tofile=label)))
        body_old = (BASE/'bgr.spice').read_text()
        body_new = (out/'bgr.spice').read_text()
        (out/'declared_bgr_source_difference.diff').write_text(''.join(difflib.unified_diff(body_old.splitlines(True), body_new.splitlines(True), fromfile='historicalBGR72417', tofile=source_kind)))
        counts = collections.Counter(row['kind'] for row in (oi if source_kind == 'old' else ni)+ti)
        receipt = dict(status='not run; preparation only', run_id=run_id, label=label, source_kind=source_kind, temperature_C=temp,
                       source_hashes={name: sha(out/name) for name in sources}, deck_sha256=sha(out/'probe.cir'),
                       bindings_sha256=binding, runtime=dict(image_id=legacy['image_id'], pdk_commit=legacy['pdk_commit'], ngspice=legacy['ngspice'],
                                                            models_sha256=legacy['models_sha256'], osdi_sha256=nominal['runtime']['osdi_sha256']),
                       query_groups=groups, query_count=sum(map(len, groups.values())), primitive_counts=dict(counts),
                       expected_nominal_BGR2842=disabled['parameters_before'] if source_kind == '586' else None,
                       historical_reference_run=str(BASE.relative_to(ROOT)), historical_wave='ptat_T12.5.dat',
                       output_wave='ptat_T12.5.dat', simulator_threads=1, original_init_threads=4,
                       thread_contract='Original .spiceinit unchanged; original deck explicitly overrides to one thread before every analysis.',
                       watchdog_proposal_s=300 if source_kind == 'old' else 600,
                       gates=dict(complete_finite_13_columns=True, endpoint_s=32e-6, full_parameters_before_after=not host,
                                  T2F338_exact_old_instrumented_control=source_kind == '586', nominal_BGR2842_exact=source_kind == '586',
                                  original_byte_numeric_time_grid_comparison=source_kind == 'old', comparator_HBT_external_VCE_limit_V=1.6,
                                  original_frequency_measurements_and_edge_indices=True),
                       scope='Nominal libraries and unmodified source cards. Historical source population is not new586 coverage. Explicit OP/query instrumentation must be qualified against original13-column wave; exact failures stay separate. Candidate12.5 comparison changes BGR source only after removing output queries; no waveform equality claim across source substitution.32us timing,50fF output,ideal1VIPTAT termination,3.3/1.2V rails and finite enable edge preserved. No actual pad, newphysicalCC, mismatch population or adoption claim.')
        (out/'preparation.json').write_text(json.dumps(receipt, indent=2)+'\n')
        normalized[label] = strip_queries(deck)
        prepared.append(dict(run_id=run_id, label=label, temperature_C=temp, source_kind=source_kind,
                             preparation_sha256=sha(out/'preparation.json'), deck_sha256=sha(out/'probe.cir'), query_count=receipt['query_count'],
                             source_hashes=receipt['source_hashes'], watchdog_proposal_s=receipt['watchdog_proposal_s']))
    assert normalized['old-inventory'] == normalized['new-paired']
    packet = dict(status='not run; seven controls prepared for review', cases=prepared, binding_sha256=binding,
                  old_host_replay_deck_exact=True, old_vs_new_paired_body_ignoring_query_output_exact=True,
                  old_inventory_queries=580, candidate_inventory_queries=3180, unchanged_T2F_parameters=338,
                  added_OP_scope='Explicit initialization/control change, not assumed transparent. Oldhost replay thenoldinventory13-column exactcomparison precedes candidate interpretation.',
                  calibration_contract=dict(calibration_temperatures_C=[25, 100], independent_temperatures_C=[-40, 125],
                                            method='T_est=25+(f-f25)/((f100-f25)/75)', max_abs_independent_residual_C=2,
                                            historical_linear_failures_preserved=True, correction_curve='none; no new LUT/reciprocal adoption'),
                  planning=dict(max_parallel_leaves=2, expected_external_growth_gib=.15, expected_home_growth_gib=.03,
                                authority='preparation only; no simulator launch or slot allocation',
                                qualification_order=['old-host', 'old-inventory', 'new-paired', 'four new temperature anchors']),
                  limitations='Four-temperature nominal pilot only; intermediate/PVT/mismatch/temperature-return controls still not run for final586 T2F. Newpopulation random-draw ordering must be independently qualified before any ensemble.')
    destination.write_text(json.dumps(packet, indent=2)+'\n')
    print(json.dumps(dict(packet=str(destination.relative_to(ROOT)), sha256=sha(destination), cases=prepared), indent=2))


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Prepare six reviewed controls for a distinct full T2F586 mismatch population."""
import argparse
import difflib
import json
from pathlib import Path
import re
from prepare_586_source_controls import BASE, BGR, HERE, ROOT, inventory, query_block, sha
from result_directory import allocate_run

NOMINAL_PACKET = HERE/'t2f586-source-controls-20260922-a.json'
CASES = [('enabled', 74001, True, [25]), ('repeat', 74001, True, [25]),
         ('changed', 74002, True, [25]), ('disabled', 74001, False, [25]),
         ('disabledchanged', 74002, False, [25]), ('return', 74001, True, [25, 125, -40, 25])]


def mismatch_source(source, enabled):
    assert not re.search(r'\bmm_ok\s*=', source)
    lines = source.splitlines(True)
    result = ''.join(line.rstrip('\n')+' mm_ok='+str(int(enabled))+'\n'
                     if line.startswith(('XM', 'XR', 'XQ', 'XC')) else line for line in lines)
    assert result.replace(' mm_ok='+str(int(enabled)), '') == source
    return result


def make_deck(original, seed, temperatures, groups):
    assert seed in [74001, 74002] and temperatures in [[25], [25, 125, -40, 25]]
    body, control = original.split('.control\n')
    assert body.count('.temp 12.5\n') == 1
    body = body.replace('.temp 12.5\n', '.temp 25\n')
    for corner, count in [('hbt_typ', 1), ('mos_tt', 2), ('res_typ', 1), ('cap_typ', 1)]:
        assert body.count(' '+corner+'\n') == count
        body = body.replace(' '+corner+'\n', ' '+corner+'_mismatch\n')
    header, tail = control.split('tran 5n 32u\n')
    measurements, ending = tail.split('wrdata ptat_T12.5.dat ')
    vectors, rest = ending.split('\n', 1)
    assert rest == 'quit\n.endc\n\n.end\n'
    assert header.count('set num_threads=1\n') == 1
    control = header+'setseed %d\nreset\n' % seed
    for phase, temperature in enumerate(temperatures):
        control += 'echo PHASE%d_BEGIN\nset temp=%d\nop\n' % (phase, temperature)
        for when in ['BEFORE', 'AFTER']:
            if when == 'AFTER':
                control += 'tran 5n 32u\n'
            for tag, queries in groups.items():
                control += query_block('P%d_%s_%s' % (phase, tag, when), queries)
        control += measurements+'wrdata phase%d.dat %s\necho PHASE%d_END\n' % (phase, vectors, phase)
    control += 'quit\n.endc\n\n.end\n'
    assert control.count('\nreset\n') == control.count('\nsetseed ') == 1
    assert control.count('tran 5n 32u\n') == len(temperatures)
    return body+'.control\n'+control


def prepare(campaign_id):
    assert re.fullmatch('[a-z0-9-]+', campaign_id)
    output = HERE/(campaign_id+'.json')
    assert not output.exists()
    nominal_packet = json.loads(NOMINAL_PACKET.read_text())
    nominal_case, = [r for r in nominal_packet['cases'] if r['label'] == 'new-paired']
    nominal_run = HERE/'runs'/nominal_case['run_id']
    nominal_result, = json.loads((nominal_run/'summary.json').read_text())
    assert nominal_result['control_status'] == nominal_result['full_inventory_status'] == 'passed'
    prep = json.loads((nominal_run/'preparation.json').read_text())
    nominal_sources = {n: (nominal_run/n).read_text() for n in ['bgr.spice', 't2f.spice']}
    enabled_sources = {n: mismatch_source(s, True) for n, s in nominal_sources.items()}
    assert enabled_sources['bgr.spice'] == (BGR/'enabled/pex_mm.spice').read_text()
    groups, targets = {}, []
    for tag, name, prefix in [('BGR', 'bgr.spice', 'xbgr'), ('T2F', 't2f.spice', 'xt2f')]:
        groups[tag], local = inventory(enabled_sources[name], prefix)
        for item in local:
            item['group'] = tag
        targets.extend(local)
    assert len(groups['BGR']) == 2842 and len(groups['T2F']) == 338
    assert len(targets) == 1129 and sum(map(len, groups.values())) == 3180
    all_queries = sum(groups.values(), [])
    assert len(set(all_queries)) == 3180
    original = (BASE/'ptat_T12.5.cir').read_text()
    paths = [NOMINAL_PACKET, nominal_run/'summary.json', nominal_run/'preparation.json',
             nominal_run/'bgr.spice', nominal_run/'t2f.spice', nominal_run/'.spiceinit',
             BASE/'ptat_T12.5.cir', BGR/'enabled/pex_mm.spice', Path(__file__).resolve()]
    bindings = {str(p.relative_to(ROOT)): sha(p) for p in paths}
    rows = []
    for label, seed, enabled, temperatures in CASES:
        run_id = campaign_id+'-'+label
        out = allocate_run(HERE.parent, run_id, relative_parent='qualification/runs')
        local = {n: mismatch_source(s, enabled) for n, s in nominal_sources.items()}
        for name, text in local.items():
            (out/name).write_text(text)
        (out/'.spiceinit').write_bytes((nominal_run/'.spiceinit').read_bytes())
        deck = make_deck(original, seed, temperatures, groups)
        (out/'probe.cir').write_text(deck)
        (out/'population_inventory.json').write_text(json.dumps(dict(groups=groups, primitives=targets,
            parameter_count=3180, primitive_count=1129, group_counts=dict(BGR=1036, T2F=93)), indent=2)+'\n')
        (out/'declared_population_deck_difference.diff').write_text(''.join(difflib.unified_diff(
            original.splitlines(True), deck.splitlines(True), fromfile='qualifiedNominal12p5', tofile=label)))
        differences = {name: ''.join(difflib.unified_diff(nominal_sources[name].splitlines(True), text.splitlines(True),
            fromfile='nominal/'+name, tofile='population/'+name)) for name, text in local.items()}
        (out/'declared_population_source_difference.json').write_text(json.dumps(differences, indent=2)+'\n')
        receipt = dict(status='not run; preparation for review only', run_id=run_id, label=label, seed=seed,
            mismatch_enabled=enabled, temperatures_C=temperatures, groups=groups,
            source_hashes={n: sha(out/n) for n in ['bgr.spice', 't2f.spice', '.spiceinit']},
            deck_sha256=sha(out/'probe.cir'), inventory_sha256=sha(out/'population_inventory.json'),
            runtime=prep['runtime'], live_bindings_sha256=bindings,
            nominal_parameters=nominal_result['parameters_before'], nominal_source_hashes=prep['source_hashes'],
            nominal_packet=str(NOMINAL_PACKET.relative_to(ROOT)),
            required_nominal_analysis=str((HERE/'t2f586-nominal-calibration-20260922.json').relative_to(ROOT)),
            watchdog_s=600*len(temperatures), outputs=['phase%d.dat' % p for p in range(len(temperatures))],
            required_comparisons='Full3180 before/after and across phases exact; enabled/repeat exact13-column waves; enabled74002 variation in every randomized primitive in BGR and T2F. Disabled74001/74002 exact vectors and waves, also exact nominal25C wave. Return25C exact wave and exact fullvectors, separate numerical differences retained.',
            scope='NEW1129-primitive T2F586 joint mismatch population, not historical510xx or jointSENSE730xx realization equivalence. Sources only add mm_ok at original1129calls; pinned cards unchanged.32us/50fF/ideal1VIPTAT/3.3V1.2V/enable/tolerances preserved. Original25/100linear calibration andheldout±2C remain mandatory for any future ensemble. No actualpad/newphysicalCC/sourceadoption claim.',
            planning=dict(simulation_status='not run; six controls require review and nominalanchoracceptance',
                          max_parallel_processes=1, cpu_allocation='one coordinator-loaned slot',
                          expected_external_growth_GiB=.20 if len(temperatures)>1 else .05))
        (out/'preparation.json').write_text(json.dumps(receipt, indent=2)+'\n')
        (out/'preparer.py').write_text(Path(__file__).read_text())
        rows.append(dict(label=label, seed=seed, run_id=run_id, temperatures_C=temperatures,
                         preparation_sha256=sha(out/'preparation.json'), deck_sha256=sha(out/'probe.cir'),
                         source_hashes=receipt['source_hashes'], watchdog_s=receipt['watchdog_s']))
    packet = dict(status='not run; six prepared qualification controls awaiting review', cases=rows,
        parameter_count=3180, primitive_count=1129, new_seed_ids=[74001, 74002],
        inventory_sha256=sha(HERE/'runs'/rows[0]['run_id']/'population_inventory.json'),
        no_ensemble_release=True, nominal_packet_sha256=sha(NOMINAL_PACKET),
        rationale='Required final586 source coverage preserves original300population obligation. HistoricaloldBGR seeds are not this population. No acceptance or correctioncurve change.')
    output.write_text(json.dumps(packet, indent=2)+'\n')
    return dict(packet=str(output.relative_to(ROOT)), sha256=sha(output), cases=rows)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--campaign-id', required=True)
    print(json.dumps(prepare(parser.parse_args().campaign_id), indent=2))

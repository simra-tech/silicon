#!/usr/bin/env python3
"""Add eleven selected supply-stage meters to already qualified copied instrumentation."""
import argparse
import difflib
import json
from pathlib import Path
import re
from run_sense_branch_current import sha
from result_directory import allocate_run

SIM = Path(__file__).resolve().parent
ROOT = SIM.parents[4]
TARGETS = {'g1_ota_main_candidate': {'XM11': 'vdd', 'XM14': 'vdd', 'XMT': 'vdd', 'XM20': 'vdd', 'XM3': 'vss', 'XM4': 'vss', 'XM21': 'vss'},
           'g1_ota': {'XM11': 'vdd', 'XM14': 'vdd'}}


def instrument(original):
    result, changes = original, []
    for subckt, devices in TARGETS.items():
        section, = re.findall(r'(?m)^\.subckt '+subckt+r' .+\n[\s\S]*?^\.ends\s*$', result)
        modified = section
        for name, rail in devices.items():
            line, = re.findall(r'^'+name+r' .+$', section, re.M)
            fields = line.split()
            assert fields[5] in ['sg13_hv_pmos', 'sg13_hv_nmos']
            monitor = 'stage_'+name.lower()+'_supply'
            pins = [i for i in range(1, 5) if fields[i] == rail]
            assert len(pins) == 2
            for i in pins:
                fields[i] = monitor
            replacement = ' '.join(fields)+'\nVSTAGE_'+name+' '+rail+' '+monitor+' 0'
            modified = modified.replace(line, replacement)
            changes.append(dict(subcircuit=subckt, device=name, rail=rail, original=line, replacement=replacement, monitor=monitor, supply_pin_indices=pins))
        result = result.replace(section, modified)
    restored = result
    for row in changes:
        assert restored.count(row['replacement']) == 1
        restored = restored.replace(row['replacement'], row['original'])
    assert restored == original
    instances = []
    for macro, subckt in [('xota', 'g1_ota_main_candidate'), ('xbuf', 'g1_ota'), ('xref', 'g1_ota')]:
        for row in changes:
            if row['subcircuit'] == subckt:
                instances.append(dict(macro=macro, device=row['device'], rail=row['rail'],
                                      current='i(v.xs.'+macro+'.vstage_'+row['device'].lower()+')',
                                      voltage='v(xs.'+macro+'.'+row['monitor']+')'))
    assert len(instances) == 11 and sum(r['rail'] == 'vdd' for r in instances) == 8
    return result, changes, instances


def transform(original, old_id, new_id, instances):
    vectors = [r['current'] for r in instances]+[r['voltage'] for r in instances]
    result = original.replace(old_id, new_id)
    result, count = re.subn(r'^(\.save .+)$', lambda m: m[1]+' '+' '.join(vectors), result, flags=re.M)
    assert count == 1
    markers = [s for s in ['echo POPULATION_OP_END\n', 'echo JOINT_POPULATION_TRAN_END\n'] if s in result]
    assert len(markers) == 1 and result.count(markers[0]) == 1
    return result.replace(markers[0], 'wrdata qualification/'+new_id+'/stages.dat '+' '.join(vectors)+'\n'+markers[0])


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run-id', required=True)
    p.add_argument('--mode', choices=['op', 'tran'], required=True)
    p.add_argument('--label', choices=['room', 'hot'], required=True)
    p.add_argument('--qualified-stage-op')
    args = p.parse_args()
    refid = ('sense-monitor-shunt-op-'+args.label+'-20260922-b') if args.mode == 'op' else ('sense-accounted-current-tran-'+args.label+'-20260922-a')
    ref = SIM/'qualification'/refid
    base = json.loads((ref/'preparation.json').read_text())
    row, = json.loads((ref/'summary.json').read_text())
    assert row['status'].startswith('passed') and row['current_accounting']['accounted_1pA_status'] == 'passed'
    assert len(row['parameter_audit']['parameters_before']) == 11512
    source, changes, instances = instrument((ref/'sense.spice').read_text())
    if args.mode == 'tran':
        assert args.qualified_stage_op
        op = SIM/'qualification'/args.qualified_stage_op
        opresult, = json.loads((op/'summary.json').read_text())
        assert opresult['stage_current_contract_status'] == 'passed'
        assert (op/'sense.spice').read_text() == source
    out = allocate_run(SIM, args.run_id)
    for name in ['trip.spice', 'bgr.spice', 'population_inventory.json']:
        (out/name).write_bytes((ref/name).read_bytes())
    (out/'sense.spice').write_text(source)
    deck = transform((ref/'probe.cir').read_text(), ref.name, out.name, instances)
    (out/'probe.cir').write_text(deck)
    for kind, original, modified in [('source', (ref/'sense.spice').read_text(), source), ('deck', (ref/'probe.cir').read_text().replace(ref.name, '@RUN@'), deck.replace(out.name, '@RUN@'))]:
        (out/('declared_supply_stage_'+kind+'.diff')).write_text(''.join(difflib.unified_diff(original.splitlines(True), modified.splitlines(True), fromfile='priorAccountedControl', tofile='declaredSupplyStageControl')))
    bindings = {str(f.relative_to(ROOT)): sha(f) for f in [ref/'preparation.json', ref/'summary.json', ref/'provenance.json', ref/'probe.cir', ref/'sense.spice', ref/'trip.spice', ref/'bgr.spice', SIM/'prepare_sense_supply_stages.py', SIM/'run_sense_supply_stages.py']}
    if args.mode == 'tran':
        bindings.update({str(f.relative_to(ROOT)): sha(f) for f in [op/'summary.json', op/'preparation.json', op/'sense.spice']})
    prep = dict(run=out.name, mode=args.mode, label=args.label, temperature_C=base['temperature_C'], seed=73001,
                reference_run=ref.name, canonical_reference_run=base['reference_op_run'] if args.mode == 'op' else base['reference_run'],
                canonical_wave_name=('op%d.dat' % base['reference_op_phase']) if args.mode == 'op' else 'phase0.dat',
                qualified_stage_op=args.qualified_stage_op, source_changes=changes, stage_instances=instances,
                runtime_identity=base['expected_runtime_identity'], groups=base['groups'], prospective_sampling=base['prospective_sampling'],
                source_hashes={name: sha(out/name) for name in ['sense.spice', 'trip.spice', 'bgr.spice']}, deck_sha256=sha(out/'probe.cir'), bindings_sha256=bindings,
                watchdog_s=120 if args.mode == 'op' else 1200, kcl_bound_A=1e-12,
                scope='Eleven selected supply-stage meters on copiedSENSE only. Same73001/full11512/27/5MHz/1.02us/codes135151/shunt25mV. EightadditionalVDD+threeVSSnodes, actual1Tohmnode shunts explicitlyaccounted. Canonicalsource untouched/restorable. Originalvoltageexact comparisons remain separatefailures ifdifferent. Representative25/125C only, not envelope/physicaladoption/hotlifetime.')
    (out/'preparation.json').write_text(json.dumps(prep, indent=2)+'\n')
    print(json.dumps({'prepared': out.name, 'source_sha256': prep['source_hashes']['sense.spice'], 'deck_sha256': prep['deck_sha256']}))


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Prepare separate rail-terminal current probes on a restorable SENSE copy."""
import argparse
import difflib
import json
from pathlib import Path
import re
from result_directory import allocate_run
from run_sense_branch_current import sha

SIM = Path(__file__).resolve().parent
ROOT = SIM.parents[4]
SUBCKTS = ['g1_sense', 'g1_ota', 'g1_ota_main_candidate']
MACROS = [('top', 'g1_sense'), ('xota', 'g1_ota_main_candidate'), ('xbuf', 'g1_ota'), ('xref', 'g1_ota')]


def instrument(original):
    result, sections, definitions = original, [], []
    for subckt in SUBCKTS:
        section, = re.findall(r'(?m)^\.subckt '+subckt+r' .+\n[\s\S]*?^\.ends\s*$', result)
        lines, records, meters, bank_pins = [], [], [], []
        for line in section.splitlines(True):
            fields = line.split()
            if not fields or not fields[0].startswith('X'):
                lines.append(line)
                continue
            changed = False
            if len(fields) > 5 and fields[5] in ['sg13_hv_nmos', 'sg13_hv_pmos']:
                for index, terminal in enumerate(['D', 'G', 'S', 'B'], 1):
                    if fields[index] not in ['vdd', 'vss']:
                        continue
                    rail = fields[index]
                    name = fields[0].lower()+'_'+terminal.lower()
                    monitor = 'railmon_'+name
                    records.append(dict(subcircuit=subckt, device=fields[0], terminal=terminal, rail=rail, meter='VPORT_'+name, monitor=monitor, kind='individual MOS external terminal'))
                    meters.append('VPORT_'+name+' '+rail+' '+monitor+' 0\n')
                    fields[index] = monitor
                    changed = True
            elif len(fields) > 4 and fields[4] == 'rppd':
                for index, terminal in enumerate(['1', '2', 'BN'], 1):
                    if fields[index] != 'vss':
                        continue
                    if subckt == 'g1_sense':
                        bank_pins.append(dict(device=fields[0], terminal=terminal, original_node='vss'))
                        fields[index] = 'railmon_rbank_vss'
                    else:
                        name = fields[0].lower()+'_'+terminal.lower()
                        monitor = 'railmon_'+name
                        records.append(dict(subcircuit=subckt, device=fields[0], terminal=terminal, rail='vss', meter='VPORT_'+name, monitor=monitor, kind='individual resistor external terminal'))
                        meters.append('VPORT_'+name+' vss '+monitor+' 0\n')
                        fields[index] = monitor
                    changed = True
            lines.append((' '.join(fields)+'\n') if changed else line)
        if bank_pins:
            assert subckt == 'g1_sense'
            records.append(dict(subcircuit=subckt, device='RBANK', terminal='VSS_GROUP', rail='vss', meter='VPORT_rbank_vss', monitor='railmon_rbank_vss', kind='signed aggregate resistor-bank VSS ports', member_ports=bank_pins))
            meters.append('VPORT_rbank_vss vss railmon_rbank_vss 0\n')
        modified = ''.join(lines)
        modified, count = re.subn(r'(?m)^(\.ends\s*)$', lambda m: ''.join(meters)+m[0], modified)
        assert count == 1
        result = result.replace(section, modified)
        sections.append(dict(subcircuit=subckt, original=section, instrumented=modified))
        definitions.extend(records)
    restored = result
    for row in sections:
        assert restored.count(row['instrumented']) == 1
        restored = restored.replace(row['instrumented'], row['original'])
    assert restored == original
    instances = []
    for macro, subckt in MACROS:
        prefix = 'xs' if macro == 'top' else 'xs.'+macro
        for row in definitions:
            if row['subcircuit'] == subckt:
                instances.append(dict(row, macro=macro, current='i(v.'+prefix+'.'+row['meter'].lower()+')', voltage='v('+prefix+'.'+row['monitor']+')'))
    assert all(r['terminal'] in ['D', 'G', 'S', 'B', '1', '2', 'BN', 'VSS_GROUP'] for r in instances)
    assert len([r for r in instances if r['device'] == 'RBANK']) == 1
    return result, sections, instances


def transform(original, old_id, new_id, instances):
    vectors = [r['current'] for r in instances]+[r['voltage'] for r in instances]
    result = original.replace(old_id, new_id)
    result, count = re.subn(r'^(\.save .+)$', lambda m: m[1]+' '+' '.join(vectors), result, flags=re.M)
    assert count == 1
    markers = [s for s in ['echo POPULATION_OP_END\n', 'echo JOINT_POPULATION_TRAN_END\n'] if s in result]
    assert len(markers) == 1 and result.count(markers[0]) == 1
    return result.replace(markers[0], 'wrdata qualification/'+new_id+'/rail_terminals.dat '+' '.join(vectors)+'\n'+markers[0])


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run-id', required=True)
    p.add_argument('--mode', choices=['op', 'tran'], required=True)
    p.add_argument('--label', choices=['room', 'hot'], required=True)
    p.add_argument('--qualified-terminal-op')
    args = p.parse_args()
    refid = 'sense-monitor-shunt-op-'+args.label+'-20260922-b' if args.mode == 'op' else 'sense-accounted-current-tran-'+args.label+'-20260922-a'
    ref = SIM/'qualification'/refid
    base = json.loads((ref/'preparation.json').read_text())
    reference, = json.loads((ref/'summary.json').read_text())
    assert reference['status'].startswith('passed') and reference['current_accounting']['accounted_1pA_status'] == 'passed'
    assert len(reference['parameter_audit']['parameters_before']) == 11512
    source, sections, instances = instrument((ref/'sense.spice').read_text())
    if args.mode == 'tran':
        assert args.qualified_terminal_op
        op = SIM/'qualification'/args.qualified_terminal_op
        result, = json.loads((op/'summary.json').read_text())
        assert result['terminal_current_contract_status'] == 'passed' and (op/'sense.spice').read_text() == source
    out = allocate_run(SIM, args.run_id)
    for name in ['trip.spice', 'bgr.spice', 'population_inventory.json']:
        (out/name).write_bytes((ref/name).read_bytes())
    (out/'sense.spice').write_text(source)
    deck = transform((ref/'probe.cir').read_text(), ref.name, out.name, instances)
    (out/'probe.cir').write_text(deck)
    for kind, original, modified in [('source', (ref/'sense.spice').read_text(), source), ('deck', (ref/'probe.cir').read_text().replace(ref.name, '@RUN@'), deck.replace(out.name, '@RUN@'))]:
        (out/('declared_rail_terminal_'+kind+'.diff')).write_text(''.join(difflib.unified_diff(original.splitlines(True), modified.splitlines(True), fromfile='qualifiedMacroControl', tofile='separateRailTerminalControl')))
    paths = [ref/n for n in ['preparation.json', 'summary.json', 'provenance.json', 'probe.cir', 'sense.spice', 'trip.spice', 'bgr.spice']]+[SIM/n for n in ['prepare_sense_rail_terminals.py', 'run_sense_rail_terminals.py', 'run_sense_supply_stages.py', 'run_sense_branch_current.py', 'sense_monitor_shunt_op.py', 'run_joint586_transients.py', 'run_nominal_clock_probe.py']]
    if args.mode == 'tran':
        paths += [op/n for n in ['summary.json', 'preparation.json', 'sense.spice']]
    prep = dict(run=out.name, mode=args.mode, label=args.label, temperature_C=base['temperature_C'], seed=73001,
                reference_run=ref.name, canonical_reference_run=base['reference_op_run'] if args.mode == 'op' else base['reference_run'],
                canonical_wave_name=('op%d.dat' % base['reference_op_phase']) if args.mode == 'op' else 'phase0.dat',
                qualified_terminal_op=args.qualified_terminal_op, source_sections=sections, terminal_instances=instances,
                runtime_identity=base['expected_runtime_identity'], groups=base['groups'], prospective_sampling=base['prospective_sampling'],
                source_hashes={n: sha(out/n) for n in ['sense.spice', 'trip.spice', 'bgr.spice']}, deck_sha256=sha(out/'probe.cir'),
                bindings_sha256={str(f.relative_to(ROOT)): sha(f) for f in paths}, watchdog_s=120 if args.mode == 'op' else 1200,
                kcl_bound_A=1e-12, scope='Separate external MOS rail-terminal meters, including source versus body, on a byte-restorable copied SENSE source. Resistor-bank VSS is explicitly a signed aggregate, not individual resistor currents. Actual added-node rshunts are measured and subtracted; raw/exact-voltage comparison failures remain separate. Same 73001 full 11512/27 realization, 5 MHz, codes 135/151, shunt 25 mV, 3.3 V, representative room/hot only. No canonical source/model changes, physical adoption, complete corner envelope, or lifetime rating.')
    (out/'preparation.json').write_text(json.dumps(prep, indent=2)+'\n')
    print(json.dumps(dict(prepared=out.name, terminals=len(instances), vdd_monitors=sum(r['rail'] == 'vdd' for r in instances), source_sha256=prep['source_hashes']['sense.spice'], deck_sha256=prep['deck_sha256'])))


if __name__ == '__main__':
    main()

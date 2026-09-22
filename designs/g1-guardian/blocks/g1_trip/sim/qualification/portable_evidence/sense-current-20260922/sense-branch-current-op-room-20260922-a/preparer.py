#!/usr/bin/env python3
"""Copied-source zero-volt SENSE branch probes; never edit canonical sources."""
import argparse
import difflib
import hashlib
import json
from pathlib import Path
import re
from prepare_joint586_population import make_control
from result_directory import allocate_run

SIM = Path(__file__).resolve().parent
ROOT = SIM.parents[4]
CURRENTS = ['i(vsense_total)', 'i(v.xs.vbranch_ota)', 'i(v.xs.vbranch_buf)', 'i(v.xs.vbranch_ref)']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def instrument_source(original):
    result, records = original, []
    for label in ['OTA', 'BUF', 'REF']:
        line, = re.findall(r'^X'+label+r' .+$', result, re.M)
        words = line.split()
        assert words[5:7] == ['vdd', 'vss'] and len(words) == 8
        words[5] = 'vdd_'+label.lower()+'_monitor'
        changed = ' '.join(words)
        voltage = 'VBRANCH_'+label+' vdd '+words[5]+' 0'
        result = result.replace(line+'\n', changed+'\n'+voltage+'\n')
        records.append({'original': line, 'instrumented': changed, 'zero_voltage_source': voltage})
    restored = result
    for record in records:
        restored = restored.replace(record['instrumented']+'\n'+record['zero_voltage_source']+'\n', record['original']+'\n')
    assert restored == original
    return result, records


def instrument_deck(original, old_id, new_id, mode, temperature, groups):
    result = original.replace(old_id, new_id)
    line, = re.findall(r'^XS .+ g1_sense$', result, re.M)
    assert line.split()[-3:] == ['vdda', '0', 'g1_sense']
    changed = line.replace(' vdda 0 g1_sense', ' sense_vdd_monitor 0 g1_sense')
    result = result.replace(line+'\n', changed+'\nVsense_total vdda sense_vdd_monitor 0\n')
    result, count = re.subn(r'^(\.save .+)$', lambda m: m[1]+' '+' '.join(CURRENTS), result, flags=re.M)
    assert count == 1
    if mode == 'op':
        result = result.split('.control\n')[0]+make_control(new_id, 73001, [temperature], groups)
        marker = 'echo POPULATION_OP_END\n'
        result = result.replace(marker, 'wrdata qualification/'+new_id+'/currents.dat '+' '.join(CURRENTS)+'\n'+marker)
    else:
        assert result.count('tran 0.2n 1.02u 0 0.2n\n') == 1
        marker = 'echo JOINT_POPULATION_TRAN_END\n'
        result = result.replace(marker, 'wrdata qualification/'+new_id+'/currents.dat '+' '.join(CURRENTS)+'\n'+marker)
    assert result.count('wrdata qualification/'+new_id+'/currents.dat ') == 1
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run-id', required=True)
    p.add_argument('--mode', choices=['op', 'tran'], required=True)
    p.add_argument('--label', choices=['room', 'hot'], required=True)
    p.add_argument('--qualified-current-op')
    a = p.parse_args()
    temp = 25 if a.label == 'room' else 125
    ref = SIM/'qualification'/('joint586-mm-tranqual-20260922-a-'+('enabled' if a.label == 'room' else 'hot'))
    prep = json.loads((ref/'preparation.json').read_text())
    summary, = json.loads((ref/'summary.json').read_text())
    assert summary['parameter_wave_contract_status'] == summary['decision_sampling_status'] == 'passed'
    assert prep['seed'] == 73001 and prep['temperatures_C'] == [temp]
    current_op = None
    if a.mode == 'tran':
        assert a.qualified_current_op
        current_op = SIM/'qualification'/a.qualified_current_op
        op_result, = json.loads((current_op/'summary.json').read_text())
        assert op_result['current_measurement_contract_status'] == 'passed'
    source, changes = instrument_source((ref/'sense.spice').read_text())
    assert sha(ref/'sense.spice') == 'baab6183c364477da1dd332e4585ae7201b3776bf0f836014744a42809e13877'
    original = (ref/'population_transient.cir').read_text()
    deck = instrument_deck(original, ref.name, a.run_id, a.mode, temp, prep['groups'])
    out = allocate_run(SIM, a.run_id)
    for name in ['trip.spice', 'bgr.spice', 'population_inventory.json']:
        (out/name).write_bytes((ref/name).read_bytes())
    (out/'sense.spice').write_text(source)
    (out/'probe.cir').write_text(deck)
    (out/'declared_current_source_difference.diff').write_text(''.join(difflib.unified_diff((ref/'sense.spice').read_text().splitlines(True), source.splitlines(True), fromfile='canonical', tofile='copiedCurrentInstrumentation')))
    (out/'declared_current_deck_difference.diff').write_text(''.join(difflib.unified_diff(original.replace(ref.name, '@RUN@').splitlines(True), deck.replace(out.name, '@RUN@').splitlines(True), fromfile='qualifiedTransient', tofile=a.mode+'CurrentControl')))
    bindings = {str(path.relative_to(ROOT)): sha(path) for path in [ref/'summary.json', ref/'provenance.json', ref/'preparation.json', ref/'population_transient.cir', ref/'sense.spice', ref/'trip.spice', ref/'bgr.spice', ref/'population_inventory.json', SIM/'prepare_sense_branch_current.py', SIM/'run_sense_branch_current.py']}
    if current_op:
        bindings.update({str(path.relative_to(ROOT)): sha(path) for path in [current_op/'summary.json', current_op/'preparation.json', current_op/'sense.spice', current_op/'probe.cir']})
    opref = SIM/'qualification'/prep['qualified_op_run']
    bindings[str((opref/'summary.json').relative_to(ROOT))] = sha(opref/'summary.json')
    control = {'run': out.name, 'mode': a.mode, 'label': a.label, 'temperature_C': temp, 'seed': 73001,
               'reference_run': ref.name, 'reference_op_run': opref.name, 'reference_op_phase': prep['qualified_op_phase_indices'][0],
               'qualified_current_op': a.qualified_current_op, 'source_changes': changes,
               'canonical_source_hashes': prep['source_hashes'], 'instrumented_source_hashes': {name: sha(out/name) for name in ['sense.spice', 'trip.spice', 'bgr.spice']},
               'groups': prep['groups'], 'expected_runtime_identity': prep['expected_runtime_identity'], 'prospective_sampling': prep['prospective_sampling'],
               'deck_sha256': sha(out/'probe.cir'), 'live_bindings_sha256': bindings,
               'current_order': ['sense_total', 'xota', 'xbuf', 'xref'], 'kcl_maximum_abs_residual_A': 1e-12,
               'watchdog_s': 120 if a.mode == 'op' else 1200,
               'scope': 'Only3copied SENSE VDDport zeroV probes plus one independent topSENSE zeroV supplymeter; original18wave unchanged separateexport. All11512+27 exact; originalvoltagebyte/numericcomparison recorded independently, never silentlywaived. Positive current enters macro VDD. CM0/shunt25mV/codes135151, nominalprocess seed73001 at25/125C only; not worstcase/envelope or newphysicalqualification.'}
    (out/'preparation.json').write_text(json.dumps(control, indent=2)+'\n')
    (out/'preparer.py').write_text(Path(__file__).read_text())
    print(json.dumps({'run': out.name, 'mode': a.mode, 'deck_sha256': control['deck_sha256'], 'source_hashes': control['instrumented_source_hashes']}))


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Prepare six frozen-population transients and one same-instance return control."""
import argparse
import difflib
import hashlib
import json
from pathlib import Path
import re
from result_directory import allocate_run

SIM = Path(__file__).resolve().parent
ROOT = SIM.parents[4]
TEMPLATE = 'joint-bgr586-recal-s71002-p10-20260922-a'
OP_PREFIX = 'joint586-mm-opqual-20260922-a-'
CASES = [('enabled', 73001, [25]), ('repeat', 73001, [25]),
         ('hot', 73001, [125]), ('cold', 73001, [-40]),
         ('disabled', 73001, [25]), ('disabledchanged', 73002, [25]),
         ('return', 73001, [25, 125, -40, 25])]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def transform(original, old_id, new_id, seed, temperatures):
    body, control = original.split('.control\n')
    header, core = control.split('reset\n', 1)
    core, ending = core.split('quit 0\n', 1)
    assert ending == '.endc\n.end\n' and header.count('setseed 71002\n') == 1
    assert core.count('tran 0.2n 1.02u 0 0.2n\n') == 1
    body, count = re.subn(r'^\.temp .+$', '.temp '+str(float(temperatures[0])), body, flags=re.M)
    assert count == 1
    result = body.replace(old_id, new_id)+'.control\n'+header.replace('setseed 71002\n', 'setseed %d\n' % seed)+'reset\n'
    for index, temp in enumerate(temperatures):
        phase = core.replace(old_id, new_id).replace('hard_+0mV.dat', 'phase%d.dat' % index)
        assert phase.replace(new_id, old_id).replace('phase%d.dat' % index, 'hard_+0mV.dat') == core
        if len(temperatures) > 1:
            result += 'set temp=%d\n' % temp
        result += 'echo PHASE%d_BEGIN\n' % index+phase+'echo PHASE%d_END\n' % index
    result += 'echo JOINT_POPULATION_TRAN_END\nquit 0\n.endc\n.end\n'
    assert result.count('\nreset\n') == result.count('\nsetseed ') == 1
    assert result.count('tran 0.2n 1.02u 0 0.2n\n') == len(temperatures)
    return result


def prepare(prefix):
    audit_path = SIM/'qualification/joint586-opqual-recovery-audit-20260922.json'
    audit = json.loads(audit_path.read_text())
    assert audit['status'].startswith('passed') and all(audit['checks'].values())
    assert audit['strict_return_status'] == 'passed'
    template = SIM/'qualification'/TEMPLATE
    original = (template/'hard_+0mV.cir').read_text()
    template_prep = json.loads((template/'preparation.json').read_text())
    results = []
    for label, seed, temperatures in CASES:
        op_label = label if label.startswith('disabled') else ('return' if label in ['hot', 'cold', 'return'] else 'enabled')
        reference = SIM/'qualification'/audit['actual_control_runs'][op_label]
        op, = json.loads((reference/'summary.json').read_text())
        op_prep = json.loads((reference/'preparation.json').read_text())
        assert op['op_qualification_status'] == 'passed' and op['seed'] == seed
        assert all(sha(reference/name) == value for name, value in audit['receipts_sha256'][op_label].items())
        indices = list(range(4)) if label == 'return' else ([1] if label == 'hot' else ([2] if label == 'cold' else [0]))
        assert [op['phases'][i]['temperature_C'] for i in indices] == temperatures
        run_id = prefix+'-'+label
        new = transform(original, TEMPLATE, run_id, seed, temperatures)
        bindings = {str(path.relative_to(ROOT)): sha(path) for path in
                    [audit_path, reference/'summary.json', reference/'provenance.json', reference/'preparation.json',
                     reference/'population_inventory.json', reference/'population_op.cir',
                     reference/'sense.spice', reference/'trip.spice', reference/'bgr.spice',
                     template/'preparation.json', template/'hard_+0mV.cir',
                     SIM/'prepare_joint586_transients.py', SIM/'run_joint586_transients.py']}
        out = allocate_run(SIM, run_id)
        for name in ['sense.spice', 'trip.spice', 'bgr.spice', 'population_inventory.json']:
            (out/name).write_bytes((reference/name).read_bytes())
        (out/'population_transient.cir').write_text(new)
        diff = ''.join(difflib.unified_diff(original.replace(TEMPLATE, '@RUN@').splitlines(True), new.replace(run_id, '@RUN@').splitlines(True), fromfile='nominal586Control', tofile='qualifiedFullPopulationTransient'))
        (out/'declared_population_transient_difference.diff').write_text(diff)
        prep = {'run': run_id, 'label': label, 'seed': seed, 'temperatures_C': temperatures,
                'template_run': TEMPLATE, 'qualified_op_run': reference.name, 'qualified_op_phase_indices': indices,
                'source_hashes': op_prep['source_hashes'], 'deck_sha256': sha(out/'population_transient.cir'),
                'inventory_sha256': sha(out/'population_inventory.json'), 'live_bindings_sha256': bindings,
                'expected_runtime_identity': op_prep['expected_runtime_identity'],
                'prospective_sampling': template_prep['prospective_sampling'],
                'groups': op_prep['prospective_groups'], 'mismatch_enabled': op_prep['mismatch_enabled'],
                'fixed_codes': [135, 151], 'shunt_V': .025,
                'planning': {'watchdog_s': 1200 if len(temperatures) == 1 else 4800,
                             'maximum_leaf_GiB': .05 if len(temperatures) == 1 else .2},
                'scope': 'New full joint586 population. Exact original1.02us5MHz/18savedvectors/stimulus/solver per phase; BGR/full-disabled sources exactly OPqualified. One initial reset/seed; multi-phase settemp only. All11512 beforeafter vs correspondingOP,27anchors, actual/legacy late3 decisions. No broadpopulation/physicaladoption claim.',
                'physical_scope': op_prep['physical_scope'],
                'stale_comments': 'Inherited10MHz/code153 comments are preserved; executable5MHz/code135151 is authoritative.'}
        (out/'preparation.json').write_text(json.dumps(prep, indent=2)+'\n')
        (out/'preparer.py').write_text(Path(__file__).read_text())
        results.append({'run': run_id, 'source_hashes': prep['source_hashes'], 'deck_sha256': prep['deck_sha256'], 'bound_s': prep['planning']['watchdog_s']})
    return results


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--prefix', required=True)
    a = p.parse_args()
    print(json.dumps(prepare(a.prefix), indent=2))

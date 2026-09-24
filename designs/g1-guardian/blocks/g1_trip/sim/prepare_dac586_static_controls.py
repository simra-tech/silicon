#!/usr/bin/env python3
"""Prepare only final-source DAC OP controls; never launch a simulator."""
import argparse
import difflib
import hashlib
import json
from pathlib import Path
import re

from prepare_joint586_population import make_control, NODES
from result_directory import allocate_run

SIM = Path(__file__).resolve().parent
ROOT = SIM.parents[4]
REFERENCE = 'joint586-mm-opqual-20260922-a-enabled'
AUDIT = SIM/'qualification/joint586-opqual-recovery-audit-20260922.json'
EXTRA = ['i(vdda)', 'i(vdd)']
CASES = [('output', 135, 151, [25]), ('repeat', 135, 151, [25])]
CASES += [('c%d-%s' % (code, label), code, code, [temp])
          for code in [0, 127, 128, 255] for label, temp in [('room', 25), ('hot', 125)]]
CASES += [('return', 135, 151, [25, 125, -40, 25])]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def code_body(body, soft, hard):
    assert type(soft) is int and type(hard) is int
    assert 0 <= soft <= 255 and 0 <= hard <= 255
    original = body
    for prefix, code, old_code in [('s', soft, 135), ('h', hard, 151)]:
        for bit in range(8):
            old = 'V%s%d %s%d 0 dc %s' % (prefix, bit, prefix, bit, '1.2' if (old_code >> bit) & 1 else '0')
            new = 'V%s%d %s%d 0 dc %s' % (prefix, bit, prefix, bit, '1.2' if (code >> bit) & 1 else '0')
            assert len(re.findall('^'+re.escape(old)+'$', body, re.M)) == 1
            body = re.sub('^'+re.escape(old)+'$', new, body, flags=re.M)
    # Restore by terminal identity, not an ambiguous global voltage substitution.
    restored = body
    for prefix, old_code in [('s', 135), ('h', 151)]:
        for bit in range(8):
            restored, count = re.subn(r'^V%s%d .+$' % (prefix, bit),
                'V%s%d %s%d 0 dc %s' % (prefix, bit, prefix, bit, '1.2' if (old_code >> bit) & 1 else '0'),
                restored, flags=re.M)
            assert count == 1
    assert restored == original
    return body


def transform(original, old_id, new_id, soft, hard, temperatures, groups):
    body, _ = original.split('.control\n')
    assert original == body + make_control(old_id, 73001, [25], groups)
    body = code_body(body, soft, hard).replace(old_id, new_id)
    saves = [line for line in body.splitlines() if line.startswith('.save ')]
    assert len(saves) == 1 and not any(vector in saves[0] for vector in EXTRA)
    body = body.replace(saves[0]+'\n', saves[0]+' '+' '.join(EXTRA)+'\n')
    control = make_control(new_id, 73001, temperatures, groups)
    old_vectors = ' '.join('v('+node+')' for node in NODES)
    for index in range(len(temperatures)):
        old = 'wrdata qualification/%s/op%d.dat %s\n' % (new_id, index, old_vectors)
        assert control.count(old) == 1
        control = control.replace(old, old.rstrip('\n')+' '+' '.join(EXTRA)+'\n')
    result = body+control
    assert result.count('\nreset\n') == result.count('\nsetseed ') == 1
    assert not re.search(r'^(tran|dc|alter|altermod|ac|noise)\b', control, re.M)
    assert result.count('\nop\n') == 2*len(temperatures)
    return result


def prepare(prefix):
    audit = json.loads(AUDIT.read_text())
    assert audit['status'].startswith('passed') and all(audit['checks'].values())
    assert audit['strict_return_status'] == 'passed'
    ref = SIM/'qualification'/REFERENCE
    prep = json.loads((ref/'preparation.json').read_text())
    summary, = json.loads((ref/'summary.json').read_text())
    assert summary['op_qualification_status'] == 'passed'
    assert audit['actual_control_runs']['enabled'] == REFERENCE
    assert all(sha(ref/name) == value for name, value in audit['receipts_sha256']['enabled'].items())
    groups = prep['prospective_groups']
    assert len(groups['NON_BGR']) == 8670 and len(groups['BGR']) == 2842 and len(groups['LEGACY27']) == 27
    assert len(set(groups['NON_BGR']+groups['BGR'])) == 11512
    original = (ref/'population_op.cir').read_text()
    bindings = {str(path.relative_to(ROOT)): sha(path) for path in
                [AUDIT, Path(__file__).resolve(), SIM/'prepare_joint586_population.py', SIM/'result_directory.py']+
                [ref/name for name in ['preparation.json', 'summary.json', 'provenance.json', 'op0.dat',
                                      'population_op.cir', 'population_inventory.json', 'sense.spice', 'trip.spice', 'bgr.spice']]}
    rows = []
    for label, soft, hard, temperatures in CASES:
        run_id = prefix+'-'+label
        deck = transform(original, REFERENCE, run_id, soft, hard, temperatures, groups)
        out = allocate_run(SIM, run_id)
        for name in ['sense.spice', 'trip.spice', 'bgr.spice', 'population_inventory.json']:
            (out/name).write_bytes((ref/name).read_bytes())
        (out/'dac_static.cir').write_text(deck)
        diff = ''.join(difflib.unified_diff(original.replace(REFERENCE, '@RUN@').splitlines(True),
                    deck.replace(run_id, '@RUN@').splitlines(True), fromfile='qualifiedJointOP', tofile='dacStaticControl'))
        (out/'declared_difference.diff').write_text(diff)
        contract = {'status': 'prepared only; simulation not run', 'run': run_id, 'label': label,
            'seed': 73001, 'codes': [soft, hard], 'temperatures_C': temperatures,
            'deck_sha256': sha(out/'dac_static.cir'), 'source_hashes': prep['source_hashes'],
            'inventory_sha256': sha(out/'population_inventory.json'), 'groups': groups,
            'expected_runtime_identity': prep['expected_runtime_identity'], 'bindings_sha256': bindings,
            'reference_run': REFERENCE, 'expected_full_parameters': summary['phases'][0]['parameters_before'],
            'columns': ['OP_scale']+['v('+node+')' for node in NODES]+EXTRA,
            'prospective_bound_s': 300 if len(temperatures) == 1 else 1200,
            'prospective_bulk_GiB': .02 if len(temperatures) == 1 else .08,
            'required_gates': ['completed exit0; fatal errors including analysis aborted absent; POPULATION_OP_END',
                'all11512 BEFORE/AFTER exactly reference every phase; legacy27 agrees; exact source/model/runtime',
                'one finite OP row per phase with exact named12-column header; OP scale is not time',
                'output/repeat first10 decoded columns and values exact original OP; repeat all12 exact',
                'return first/last full12 columns exact; temperature-return differences retained separately'],
            'scope': 'Unchanged full final586/gm4/TRIP sources, actual reference and both full switch trees. '
                'Only static16bit source values and appended supply observations change. Original clock and '
                'comparator connections retained (soft reset/hard evaluate at OP); no reset rewiring. '
                'Total i(vdda)/i(vdd) includes other blocks and is NOT DAC leakage or per-DAC allocation. '
                'No all256, dynamic carry/settling, mismatch ensemble or physical qualification is claimed.',
            'acceptance': {'monotonicity': 'DNL>-1 LSB; not tested by sparse anchors',
                'INL_limit': 'not allocated; report only', 'leakage_limit': 'not allocated; measurement not yet isolated',
                'code_validity': 'existing >=1us; not tested by OP'},
            'physical_scope': prep['physical_scope']}
        (out/'preparation.json').write_text(json.dumps(contract, indent=2)+'\n')
        rows.append({'run': run_id, 'preparation_sha256': sha(out/'preparation.json'),
                     'deck_sha256': contract['deck_sha256'], 'status': contract['status']})
    return rows


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prefix', required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.prefix), indent=2))

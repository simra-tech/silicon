#!/usr/bin/env python3
"""Prepare six OP-only controls for a NEW full joint586 mismatch population."""
import argparse
import difflib
import hashlib
import json
from pathlib import Path
import re
from result_directory import allocate_run
from prepare_bgr_substitution_draw_audit import inventory_non_bgr, bgr_queries

SIM = Path(__file__).resolve().parent
ROOT = SIM.parents[4]
REF = SIM/'qualification/joint-bgr586-recal-s71002-p10-20260922-a'
BGR_REF = SIM.parents[1]/'g1_bgr/sim/qualification/runs/bgr_one_draw_20260922_r1'
NODES = ['vref', 'iptat', 'vref_buf', 'vped', 'shp', 'isense', 'xt.icmp', 'xt.vth_soft', 'xt.vth_hard']
CASES = [('enabled', 73001, [25]), ('repeat', 73001, [25]), ('changed', 73002, [25]),
         ('return', 73001, [25, 125, -40, 25]), ('disabled', 73001, [25]), ('disabledchanged', 73002, [25])]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def disabled_source(source):
    assert 'mm_ok=0' not in source and 'mm_ok=1' in source
    result = source.replace('mm_ok=1', 'mm_ok=0')
    assert result.replace('mm_ok=0', 'mm_ok=1') == source
    return result


def make_control(run_id, seed, temperatures, groups):
    control = '.control\nset num_threads=1\nset numdgt=15\nset filetype=ascii\nset wr_singlescale\nset wr_vecnames\nsetseed %d\nreset\n' % seed
    for index, temp in enumerate(temperatures):
        control += 'set temp=%d\nop\n' % temp
        for when in ['BEFORE', 'AFTER']:
            if when == 'AFTER':
                control += 'op\n'
            for tag, queries in groups.items():
                label = 'P%d_%s_%s' % (index, tag, when)
                control += 'echo '+label+'_BEGIN\n'+''.join('print '+key+'\n' for key in queries)+'echo '+label+'_END\n'
        control += 'wrdata qualification/%s/op%d.dat %s\n' % (run_id, index, ' '.join('v('+node+')' for node in NODES))
    control += 'echo POPULATION_OP_END\nquit 0\n.endc\n.end\n'
    assert control.count('\nreset\n') == control.count('\nsetseed ') == 1
    assert not re.search(r'^(tran|dc|ac|alter|altermod)\b', control, re.M)
    return control


def prepare(prefix):
    refprep = json.loads((REF/'preparation.json').read_text())
    m = json.loads((BGR_REF/'manifest.json').read_text())
    assert m['status'] == 'passed harness qualification'
    sources = {name: (REF/name).read_text() for name in ['sense.spice', 'trip.spice', 'bgr.spice']}
    assert all(sha(REF/name) == value for name, value in refprep['source_hashes'].items())
    bgr_mm = (BGR_REF/'enabled/pex_mm.spice').read_text()
    assert bgr_mm.replace(' mm_ok=1', '') == sources['bgr.spice']
    assert bgr_mm.count(' mm_ok=1') == 1036
    assert sha(REF/'bgr.spice') == m['source_sha256'] == '586ffb58b6af31c77a2e7cbcb83b173ffa4713ec62401da30901c5a7e606283b'
    sources['bgr.spice'] = bgr_mm
    inventory = inventory_non_bgr(sources['sense.spice'], sources['trip.spice'])
    bgr = bgr_queries(bgr_mm)
    assert len(bgr) == 2842 and bgr == m['parameters']
    groups = {'NON_BGR': inventory['queries'], 'BGR': bgr, 'LEGACY27': [k for k, v in refprep['original27_observations']]}
    assert len(set(groups['NON_BGR']+groups['BGR'])) == 11512
    assert set(groups['LEGACY27']).issubset(groups['NON_BGR']+groups['BGR'])
    inventory.update(bgr_queries=bgr, all_queries=groups['NON_BGR']+groups['BGR'], legacy27=groups['LEGACY27'],
                     bgr_device_count=1036, full_device_count=3500, full_parameter_count=11512,
                     randomized_target_groups={'nonBGR': '2464 MOS/R/CMIM instances;8670 parameters, including all6CMIM scales',
                                               'BGR': '336MOS/399R/301HBT instances;2842 parameters'},
                     scope='Complete source-instantiated3500-device target inventory. New joint population, not old71002 realization equivalence. Actual parameter availability/freeze/variation not run.')
    original = (REF/'hard_+0mV.cir').read_text()
    body = original.split('.control\n')[0]
    assert original.count('.control\n') == 1
    rows = []
    for label, seed, temperatures in CASES:
        run_id = prefix+'-'+label
        enabled = not label.startswith('disabled')
        local = sources if enabled else {k: disabled_source(v) for k, v in sources.items()}
        deck = body.replace(REF.name, run_id)+make_control(run_id, seed, temperatures, groups)
        assert deck.split('.control\n')[0].replace(run_id, REF.name) == body
        out = allocate_run(SIM, run_id)
        for name, text in local.items():
            (out/name).write_text(text)
        (out/'population_op.cir').write_text(deck)
        (out/'population_inventory.json').write_text(json.dumps(inventory, indent=2)+'\n')
        diff = ''.join(difflib.unified_diff(original.replace(REF.name, '@RUN@').splitlines(True), deck.replace(run_id, '@RUN@').splitlines(True), fromfile='nominal586CalibrationFullTransient', tofile='newPopulationOpOnly'))
        (out/'declared_population_deck_difference.diff').write_text(diff)
        differences = {}
        for name in local:
            old = (REF/name).read_text()
            differences[name] = ''.join(difflib.unified_diff(old.splitlines(True), local[name].splitlines(True), fromfile='original/'+name, tofile='newPopulation/'+name))
        (out/'declared_population_source_difference.json').write_text(json.dumps(differences, indent=2)+'\n')
        bindings = {str(path.relative_to(ROOT)): sha(path) for path in
                    [REF/'preparation.json', REF/'hard_+0mV.cir', REF/'sense.spice', REF/'trip.spice', REF/'bgr.spice',
                     BGR_REF/'manifest.json', BGR_REF/'enabled/pex_mm.spice', BGR_REF/'enabled/pex_nominal.spice',
                     SIM/'prepare_joint586_population.py', SIM/'run_joint586_population_op.py']}
        prep = {'run': run_id, 'label': label, 'seed': seed, 'mismatch_enabled': enabled, 'temperatures_C': temperatures,
                'source_hashes': {name: sha(out/name) for name in local}, 'source_nominal_BGR_sha256': m['source_sha256'],
                'deck_sha256': sha(out/'population_op.cir'), 'inventory_sha256': sha(out/'population_inventory.json'),
                'expected_runtime_identity': refprep['expected_runtime_identity'], 'live_bindings_sha256': bindings,
                'reference_run': REF.name, 'qualified_BGR_mismatch_source': str((BGR_REF/'enabled/pex_mm.spice').relative_to(ROOT)),
                'prospective_groups': groups, 'disabled_BGR_nominal_expected': refprep['candidate2842_nominal_expected'],
                'repeat_contract': 'All11512 values before/after and across repeat/temperature-return exact. Enabled73002 must change randomized primitive values in both BGR/nonBGR groups. Disabled73001/73002 fullvectors and OPdata exact; no seed-equivalence to old71002.',
                'return_contract': 'Same instance25→125→−40→25, one initial reset/seed only. Exact returned25 OPdata equality and separate prospective1uV per-node bound both reported; neither silently substitutes for the other.',
                'stimulus': {'codes': [135, 151], 'shunt_V': .025, 'VDDA_V': 3.3, 'VDD_V': 1.2, 'clock_declaration': '5MHz unchanged; no transient analysis'},
                'planning': {'watchdog_s': 120 if len(temperatures) == 1 else 300, 'maximum_leaf_GiB': .04, 'simulation_status': 'not run; awaiting contract review'},
                'physical_scope': 'Existing model-level sources and inherited capacitance assumptions; unresolvedSENSEphysicalfidelity and finalBGR/SENSEgeometryPEX remain separate. No source dimension/body/model-card change or adoption.'}
        (out/'preparation.json').write_text(json.dumps(prep, indent=2)+'\n')
        (out/'preparer.py').write_text(Path(__file__).read_text())
        rows.append({'run': run_id, 'seed': seed, 'temperatures_C': temperatures, 'deck_sha256': prep['deck_sha256'], 'source_hashes': prep['source_hashes']})
    return rows


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--prefix', required=True)
    a = p.parse_args()
    print(json.dumps(prepare(a.prefix), indent=2))

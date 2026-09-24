#!/usr/bin/env python3
"""Prepare two OP-only random-draw audits; no transient or simulator launch."""
import argparse
import collections
import difflib
import hashlib
import json
from pathlib import Path
import re
from result_directory import allocate_run

SIM = Path(__file__).resolve().parent
BGR = SIM.parents[1] / 'g1_bgr/sim/qualification'
CANDIDATE = BGR / 'candidates/bgr_loop24_qref4_r253p465_hv06/bgr_loop24_qref4_r253p465_hv06.spice'
CANDIDATE_SHA = '586ffb58b6af31c77a2e7cbcb83b173ffa4713ec62401da30901c5a7e606283b'
MODELS = {'rppd', 'rhigh', 'cap_cmim', 'sg13_hv_nmos', 'sg13_hv_pmos', 'sg13_lv_nmos', 'sg13_lv_pmos'}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory_non_bgr(sense, trip):
    definitions = {}
    for source in [sense, trip]:
        name = None
        for line in source.splitlines():
            if line.lower().startswith('.subckt '):
                name = line.split()[1]
                assert name not in definitions
                definitions[name] = []
            elif line.lower().startswith('.ends'):
                name = None
            elif name and line.startswith('X'):
                definitions[name].append(line.split())
    devices = []
    queries = []
    def walk(name, hierarchy):
        for fields in definitions[name]:
            matches = [word for word in fields[1:] if word in definitions or word in MODELS]
            assert len(matches) == 1, fields
            model = matches[0]
            path = hierarchy + '.' + fields[0].lower()
            if model in definitions:
                walk(model, path)
                continue
            assert 'mm_ok=1' in fields, ('Unexpected nonBGR mismatch policy', fields)
            devices.append({'path': path, 'model': model})
            if model.startswith('sg13_'):
                queries.extend('@n.%s.n%s[%s]' % (path, model, parameter) for parameter in ['w', 'l', 'delvto', 'factuo'])
            elif model in ['rppd', 'rhigh']:
                queries.extend('@n.%s.nr1[%s]' % (path, parameter) for parameter in ['nsmm_rsh', 'nsmm_w', 'nsmm_l'])
            else:
                assert model == 'cap_cmim'
                queries.append('@c.%s.c1[scale]' % path)
    walk('g1_sense', 'xs')
    walk('g1_trip', 'xt')
    assert len(queries) == len(set(queries)) == 8670
    assert len(devices) == 2464
    return {'queries': queries, 'devices': devices,
            'model_counts': dict(collections.Counter(d['model'] for d in devices)),
            'query_count': len(queries),
            'scope': 'Every source-instantiated nonBGR MOS w/l/delvto/factuo, resistor nsmm_rsh/w/l, and six CMIM scale mismatch values. Capacitance scale query availability is not run; unsupportedquery must failclosed, never omitcaps or launch transient.'}


def bgr_queries(source):
    queries = []
    for line in source.splitlines():
        fields = line.split()
        if not fields:
            continue
        name = fields[0].lower()
        if line.startswith('XM'):
            queries.extend('@n.xbgr.%s.n%s[%s]' % (name, fields[5], parameter) for parameter in ['w', 'l', 'delvto', 'factuo'])
        elif line.startswith('XR'):
            queries.extend('@n.xbgr.%s.nr1[%s]' % (name, parameter) for parameter in ['nsmm_rsh', 'nsmm_w', 'nsmm_l'])
        elif line.startswith('XQ'):
            queries.append('@q.xbgr.%s.qnpn13g2[area]' % name)
    assert len(queries) == len(set(queries))
    return queries


def prepare(reference_id, baseline_id, candidate_id):
    original = SIM / 'qualification' / reference_id
    old, = json.loads((original / 'summary.json').read_text())
    prep = json.loads((original / 'preparation.json').read_text())
    assert old['seed'] == 71002 and old['temperature_C'] == 25 and old['output_only_qualification_status'] == 'passed'
    assert old['all27_parameters_exact'] and len(old['fingerprints']) == 27
    legacy = dict(old['fingerprints'])
    non_bgr_anchors = {key: value for key, value in legacy.items() if '.xbgr.' not in key}
    assert len(non_bgr_anchors) == 24
    sources = {name: (original / name).read_text() for name in ['sense.spice', 'trip.spice', 'bgr.spice']}
    inventory = inventory_non_bgr(sources['sense.spice'], sources['trip.spice'])
    assert set(non_bgr_anchors).issubset(inventory['queries'])
    assert sha(CANDIDATE) == CANDIDATE_SHA
    candidate = CANDIDATE.read_text()
    assert not re.search(r'\bmm_ok\b', candidate)
    candidate_manifest = json.loads((CANDIDATE.parent / 'manifest.json').read_text())
    candidate_queries = bgr_queries(candidate)
    assert candidate_queries == candidate_manifest['fingerprint_parameters'] and len(candidate_queries) == 2842
    nominal_path = BGR / 'runs/bgr_loop24q4_hv06_nominal_20260922_r1/manifest.json'
    nominal = json.loads(nominal_path.read_text())
    nominal_case, = nominal['cases']
    assert nominal['pex_sha256'] == CANDIDATE_SHA and nominal_case['status'] == 'passed'
    assert nominal_case['fingerprint_parameters'] == candidate_queries
    assert len(nominal_case['fingerprints']) == 5684
    nominal_values = nominal_case['fingerprints'][:2842]
    assert nominal_values == nominal_case['fingerprints'][2842:]
    original_deck = (original / (prep['case'] + '.cir')).read_text()
    prefix = original_deck.split('.control\n')[0]
    assert original_deck.count('.control\n') == 1
    rows = []
    for label, run_id, bgr_source in [('baseline', baseline_id, sources['bgr.spice']), ('candidate', candidate_id, candidate)]:
        local_sources = dict(sources, **{'bgr.spice': bgr_source})
        bgr_inventory = bgr_queries(bgr_source)
        groups = [('LEGACY27', list(legacy)), ('NON_BGR_ALL', inventory['queries']), ('BGR_ALL', bgr_inventory)]
        control = '.control\nset num_threads=1\nset numdgt=15\nset filetype=ascii\nsetseed 71002\nreset\nop\n'
        for tag, queries in groups:
            control += 'echo ' + tag + '_BEGIN\n' + ''.join('print ' + query + '\n' for query in queries) + 'echo ' + tag + '_END\n'
        control += 'print v(vref) v(iptat) v(vref_buf) v(vped) v(shp) v(isense) v(xt.icmp) v(xt.vth_soft) v(xt.vth_hard)\necho DRAW_AUDIT_END\nquit 0\n.endc\n.end\n'
        deck = prefix.replace(reference_id, run_id) + control
        assert not re.search(r'^tran\b', deck, re.M)
        out = allocate_run(SIM, run_id)
        for name, text in local_sources.items():
            (out / name).write_text(text)
        (out / 'draw_audit.cir').write_text(deck)
        (out / 'preparer.py').write_text(Path(__file__).read_text())
        (out / 'non_bgr_inventory.json').write_text(json.dumps(inventory, indent=2) + '\n')
        diff = ''.join(difflib.unified_diff(original_deck.replace(reference_id, '@RUN@').splitlines(True),
                    deck.replace(run_id, '@RUN@').splitlines(True), fromfile='originalObservationTransient', tofile=label+'OpOnlyAudit'))
        (out / 'declared_draw_audit_difference.diff').write_text(diff)
        record = {'status': 'prepared only; simulator not run', 'run': run_id, 'kind': label,
                  'reference_run': reference_id, 'seed': 71002, 'temperature_C': 25,
                  'source_hashes': {name: sha(out / name) for name in local_sources},
                  'deck_sha256': sha(out / 'draw_audit.cir'), 'non_bgr_inventory_sha256': sha(out / 'non_bgr_inventory.json'),
                  'expected_runtime_identity': prep['expected_runtime_identity'],
                  'legacy27_expected': legacy, 'non_bgr24_expected': non_bgr_anchors,
                  'non_bgr_query_count': len(inventory['queries']), 'bgr_queries': bgr_inventory,
                  'expected_candidate2842_nominal_values': nominal_values if label == 'candidate' else None,
                  'candidate_nominal_reference_manifest_sha256': sha(nominal_path),
                  'candidate_nominal_reference': str(nominal_path.relative_to(SIM.parents[4])),
                  'mismatch_policy': 'SENSE/TRIP sources remain exact explicitmm_ok=1. BaselineBGR remains exact explicitmm_ok=1. CandidateBGR remains literal586sourcewithno_mm_ok, inheriting pinnedwrapperdefault0 under unchangedsharedmismatchlibraries; all2842valuesmust verify nominal. No PDK/card/libraryreplacement.',
                  'random_draw_policy': 'Do not assume mm_ok=0 avoids randomstreamconsumption or that a seed identifies the same circuit realization after BGRdevicecount changes. Require original24anchors, then exactbaseline-vs-candidate8670nonBGRparametersincluding6CMIMscales. Failure or invalidquery blocksanysubstitution transient; no drawretuning, indexskipping or modeloverride.',
                  'legacy_bgr_policy': 'Original27contains24nonBGR+3oldBGRparameters. Baseline mustmatchall27; candidate24mustmatch, but3BGRvaluesareseparatelyreported andmustnotbeclaimedunchanged under nominalBGRsubstitution.',
                  'stimulus_scope': 'Originalroom fixture devices/bodyconnections/loads/rails/shunt/code/clockdeclaration andOPinitialization exact exceptrunlabels/BGRsource. OPonly; fullnonBGRdrawaudit is prerequisite, not transient/frequency/temp/hotqualification.',
                  'planning': {'proposed_timeout_s': 120, 'proposed_home_growth_GiB_for_pair': .1,
                               'analog_launch_status': 'not authorized; prepare only'},
                  'remaining': 'OPqueryavailability/numericalcompletion/fullnonBGRparity/2842nominalvalues not run; room/hot source-substitutiontransients not run; no recalibration/MC/adoption.'}
        (out / 'preparation.json').write_text(json.dumps(record, indent=2) + '\n')
        rows.append({key: record[key] for key in ['run', 'kind', 'deck_sha256', 'source_hashes', 'non_bgr_query_count']})
    return rows


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference', required=True)
    parser.add_argument('--baseline-id', required=True)
    parser.add_argument('--candidate-id', required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.reference, args.baseline_id, args.candidate_id), indent=2))

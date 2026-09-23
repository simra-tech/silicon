#!/usr/bin/env python3
"""Inspect actual engine output and every saved cross-reference status."""
import argparse
import collections
import functools
import hashlib
import json
from pathlib import Path
import re


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def value(obj, name):
    result = getattr(obj, name)
    return result() if callable(result) else result


def label(obj):
    if obj is None:
        return None
    for key in ('expanded_name', 'name'):
        if hasattr(obj, key):
            return value(obj, key)
    return str(obj)


def device(obj):
    if obj is None:
        return None
    cls = obj.device_class()
    return dict(name=label(obj), model=value(cls, 'name'),
                parameters={value(p, 'name'): obj.parameter(value(p, 'name')) for p in cls.parameter_definitions()},
                terminals={value(t, 'name'): label(obj.net_for_terminal(value(t, 'name'))) for t in cls.terminal_definitions()})


def inventory(netlist):
    rows = {}
    for circuit in netlist.each_circuit():
        rows[value(circuit, 'name')] = dict(
            devices=sum(1 for _ in circuit.each_device()),
            models=dict(collections.Counter(value(d.device_class(), 'name') for d in circuit.each_device())),
            nets=sum(1 for _ in circuit.each_net()),
            pins=[label(p) for p in circuit.each_pin()],
            children=[value(value(s, 'circuit_ref'), 'name') for s in circuit.each_subcircuit()])
    @functools.lru_cache(None)
    def expanded(name, trail=()):
        assert name not in trail, 'Cyclic circuit hierarchy'
        return rows[name]['devices'] + sum(expanded(child, trail + (name,)) for child in rows[name]['children'])
    for name in rows:
        rows[name]['expanded_devices'] = expanded(name)
    return rows


def inspect_database(path, expected_top):
    import pya
    assert pya.__version__ == '0.30.9'
    db = pya.LayoutVsSchematic()
    db.read(str(path))
    xr = db.xref()
    X = pya.NetlistCrossReference
    statuses = {X.Match: 'Match', X.MatchWithWarning: 'MatchWithWarning', X.Mismatch: 'Mismatch',
                X.NoMatch: 'NoMatch', X.Skipped: 'Skipped', X.None_: 'None'}
    inventories = {side: inventory(value(db, key)) for side, key in [('layout', 'netlist'), ('reference', 'reference')]}
    def reachable(rows):
        todo = [expected_top] if expected_top in rows else []
        seen = set()
        while todo:
            name = todo.pop()
            if name not in seen:
                seen.add(name)
                todo.extend(rows[name]['children'])
        return seen
    reach = {side: reachable(rows) for side, rows in inventories.items()}
    paired = {'layout': set(), 'reference': set()}
    circuits = []
    for cp in xr.each_circuit_pair():
        row = dict(layout=label(cp.first()), reference=label(cp.second()), status=statuses[cp.status()], pairs={}, bad_pairs={}, side_counts={})
        row['reachable_from_chip'] = any(row[side] in reach[side] for side in reach)
        for side in reach:
            if row[side] in reach[side]:
                paired[side].add(row[side])
        for kind, method in [('device', xr.each_device_pair), ('net', xr.each_net_pair),
                             ('pin', xr.each_pin_pair), ('subcircuit', xr.each_subcircuit_pair)]:
            counter = collections.Counter()
            side_counts = {'layout': 0, 'reference': 0}
            bad = []
            for pair in method(cp):
                status = statuses[pair.status()]
                counter[status] += 1
                side_counts['layout'] += pair.first() is not None
                side_counts['reference'] += pair.second() is not None
                if status != 'Match':
                    mapper = device if kind == 'device' else label
                    bad.append(dict(status=status, layout=mapper(pair.first()), reference=mapper(pair.second())))
            row['pairs'][kind] = dict(counter)
            row['bad_pairs'][kind] = bad
            row['side_counts'][kind] = side_counts
        row['all_side_inventory_counts_covered'] = True
        for side in reach:
            if row[side] in reach[side]:
                original = inventories[side][row[side]]
                expected = dict(device=original['devices'], net=original['nets'], pin=len(original['pins']), subcircuit=len(original['children']))
                if any(row['side_counts'][kind][side] != count for kind, count in expected.items()):
                    row['all_side_inventory_counts_covered'] = False
        circuits.append(row)
    selected = [row for row in circuits if row['reachable_from_chip']]
    coverage = all(reach[side] and paired[side] == reach[side] for side in reach)
    strict = bool(selected) and coverage and all(row['status'] == 'Match' and row['all_side_inventory_counts_covered'] and
                                                all(set(counts) <= {'Match'} for counts in row['pairs'].values()) for row in selected)
    return dict(status='passed' if strict else 'failed', sha256=sha(path), circuits=circuits,
                reachable_circuits={side: sorted(names) for side, names in reach.items()},
                all_reachable_circuits_paired=coverage,
                unreachable_definitions='Reported separately, not chip devices; any pair reachable on either side remains required.',
                **inventories)


def classify(returncode, engine, database, expected_top, physical=True, expected_pins=None):
    positive = 'Congratulations! Netlists match.' in engine
    negative = "Netlists don't match" in engine
    signatures = positive and not negative
    forbidden_errors = bool(re.search(r'ERROR\s*:|\bException\b|Traceback|Segmentation fault', engine))
    checks = dict(process_exit_zero=returncode == 0, explicit_engine_match_only=signatures,
                  no_engine_error=not forbidden_errors, saved_database=database is not None)
    if database is not None:
        checks['strict_all_pairs_Match'] = database['status'] == 'passed'
        for side in ('layout', 'reference'):
            top = database[side].get(expected_top)
            checks[side + '_top_present_nonempty'] = top is not None and top['expanded_devices'] > 0
            if expected_pins is not None:
                checks[side + '_source_top_pin_set_exact'] = top is not None and sorted(top['pins']) == sorted(expected_pins)
    if physical:
        required = ['Selected LAYOUT_NETLIST option: (none)', 'Selected NET_ONLY option: false',
                    'Selected IGNORE_TOP_PORTS_MISMATCH option: false', 'Selected IMPLICIT_NETS option: (none)',
                    'Selected DISABLE_TAP_EXTRACTION option: false',
                    'Starting SG13G2 LVS Comparison in strict port mode.',
                    'flag_missing_ports enabled: missing/mislabeled top-level ports are treated as errors.']
        checks['native_extraction_strict_unrelaxed_switches'] = all(s in engine for s in required)
    return dict(status='passed strict saved comparison' if all(checks.values()) else 'failed strict saved comparison',
                checks=checks, explicit_engine_match=positive, explicit_engine_mismatch=negative,
                process_returncode=returncode, wrapper_summary_not_used=True)


def analyze(folder, returncode, expected_top, physical=True, expected_pins=None):
    logs = []
    for path in folder.rglob('*.log'):
        text = path.read_text(errors='replace')
        if 'Starting running SG13G2 Klayout LVS runset' in text and not path.name.startswith('lvs_run_'):
            logs.append((path, text))
    # Ignore console copies outside the stock report directory; caller supplies
    # that directory, which must have exactly one actual engine log.
    assert len(logs) == 1, 'Missing or ambiguous actual engine log'
    path, engine = logs[0]
    dbs = list(folder.rglob('*.lvsdb'))
    assert len(dbs) <= 1, 'Ambiguous result databases'
    parsed = inspect_database(dbs[0], expected_top) if dbs else None
    result = classify(returncode, engine, parsed, expected_top, physical, expected_pins)
    result.update(engine_log=str(path.relative_to(folder)), engine_log_sha256=sha(path), database=parsed,
                  parser_sha256=sha(Path(__file__)), physical_extraction_required=physical)
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--reports', type=Path, required=True)
    p.add_argument('--returncode', type=int, required=True)
    p.add_argument('--top', required=True)
    p.add_argument('--pins-json', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    assert not a.output.exists()
    result = analyze(a.reports, a.returncode, a.top, True, json.loads(a.pins_json.read_text()))
    a.output.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'database'}, indent=2))
    raise SystemExit(0 if result['status'].startswith('passed') else 1)


if __name__ == '__main__':
    main()

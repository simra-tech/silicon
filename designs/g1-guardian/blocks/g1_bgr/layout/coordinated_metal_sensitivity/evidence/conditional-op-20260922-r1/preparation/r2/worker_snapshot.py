#!/usr/bin/env python3
"""Prepare, but never launch, a conditional metallic-boundary OP experiment."""
import argparse
import collections
import datetime
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import re


SOURCE_SHA = '586ffb58b6af31c77a2e7cbcb83b173ffa4713ec62401da30901c5a7e606283b'
FIXTURE_SHA = '06afbd5138cc67283dd27130ee942210498c8fd6d1fc55df4f79c4335373bc3e'
PORTS = 'vdd vss r4 vref iptat pbias pcasc vbe dvbe'.split()
TERMS = {'XR': ['1', '2', 'BN'], 'XM': ['D', 'G', 'S', 'B'],
         'XQ': ['C', 'B', 'E', 'BN']}


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def dump(p, obj):
    p.write_text(json.dumps(obj, indent=2, allow_nan=False) + '\n')


class Union:
    def __init__(self, keys):
        self.parent = {k: k for k in keys}

    def find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def join(self, a, b):
        a, b = self.find(a), self.find(b)
        self.parent[max(a, b)] = min(a, b)


def prepare(args, scenario):
    run = args.network_root / ('bgr-metal-r-signalbypass-' + scenario.lower() + '-20260922-r1')
    result = run / 'result'
    receipt = json.loads((result / 'summary.json').read_text())
    audit = json.loads((run / 'independent_audit.json').read_text())
    assert receipt['status'] == 'passed conditional fixed-current metallic solve'
    assert audit['status'] == 'passed independent saved-network numerical audit; physical IR not qualified'
    assert audit['scenario'] == scenario
    assert sha(result / 'raw_network.json.gz') == receipt['raw_network_sha256']
    assert receipt['scenario'] == scenario
    raw = json.loads(gzip.decompress((result / 'raw_network.json.gz').read_bytes()).decode())
    points = json.loads((args.preparation / 'points.json').read_text())
    zero = Union([n['id'] for n in raw['nodes']])
    all_edges = Union([n['id'] for n in raw['nodes']])
    for edge in raw['edges']:
        assert math.isfinite(edge['R_ohm']) and edge['R_ohm'] >= 0
        all_edges.join(edge['a'], edge['b'])
        if edge['R_ohm'] == 0:
            zero.join(edge['a'], edge['b'])
    point_node = {p['id']: zero.find(raw['point_to_node'][str(p['id'])]) for p in points}
    grouped = collections.defaultdict(list)
    for p in points:
        grouped[p['source_net']].append(p)
    assert len(grouped) == 55
    ownership = {}
    names = {zero.find(n['id']): 'mr_n' + str(zero.find(n['id'])) for n in raw['nodes']}
    anchors = []
    for net, members in sorted(grouped.items()):
        components = {all_edges.find(raw['point_to_node'][str(p['id'])]) for p in members}
        assert len(components) == 1
        component = next(iter(components))
        assert component not in ownership
        ownership[component] = net
        ports = [p for p in members if p['reference_ports']]
        assert len(ports) <= 1
        anchor = ports[0] if ports else min(members, key=lambda p: p['id'])
        assert bool(ports) == (net in PORTS)
        names[point_node[anchor['id']]] = net
        anchors.append(dict(source_net=net, point_id=anchor['id'], zero_group=point_node[anchor['id']],
                            kind='actual macro port' if ports else 'unqualified historical-cap alias only'))
    assert set(ownership) == {all_edges.find(n['id']) for n in raw['nodes']}
    assert len(names.values()) == len(set(names.values()))
    terminal_map = {}
    for p in points:
        for source in p['sources']:
            key = (source['source_id'], source['terminal'])
            assert key not in terminal_map
            terminal_map[key] = dict(source_net=p['source_net'], point_id=p['id'],
                                     node=names[point_node[p['id']]])
    assert len(terminal_map) == 3346
    original = args.source.read_text()
    converted, restored, changes, bn, seen = [], [], [], [], set()
    for number, line in enumerate(original.splitlines(keepends=True), 1):
        matches = list(re.finditer(r'\S+', line))
        if not matches or matches[0].group()[:2] not in TERMS:
            converted.append(line)
            restored.append(line)
            continue
        device = matches[0].group()
        assert device not in seen
        seen.add(device)
        terms = TERMS[device[:2]]
        edits = []
        for i, term in enumerate(terms, 1):
            token = matches[i]
            old = token.group()
            if device.startswith('XR') and term == 'BN':
                assert old == 'vss' and (device, term) not in terminal_map
                bn.append(dict(source_id=device, node=old, attribution='unqualified ideal global substrate return'))
                continue
            row = terminal_map[(device, term)]
            assert row['source_net'] == old
            edits.append((token.start(), token.end(), row['node']))
            changes.append(dict(source_id=device, terminal=term, line=number,
                                old=old, new=row['node'], point_id=row['point_id']))
        changed = line
        for start, end, replacement in reversed(edits):
            changed = changed[:start] + replacement + changed[end:]
        new_matches = list(re.finditer(r'\S+', changed))
        reverse = changed
        for i in reversed(range(1, len(terms) + 1)):
            token = new_matches[i]
            reverse = reverse[:token.start()] + matches[i].group() + reverse[token.end():]
        assert reverse == line
        converted.append(changed)
        restored.append(reverse)
    assert len(seen) == 1036 and len(bn) == 399 and len(changes) == 3346
    assert ''.join(restored) == original
    primitive_counts = collections.Counter(n[:2] for n in seen)
    assert dict(primitive_counts) == {'XR': 399, 'XM': 336, 'XQ': 301}
    capacitors = [line for line in original.splitlines(keepends=True) if re.match(r'^C\S+\s', line, re.I)]
    assert len(capacitors) == 329
    positive, edge_ledger = [], []
    for i, edge in enumerate(raw['edges']):
        if edge['R_ohm'] == 0:
            continue
        a, b = names[zero.find(edge['a'])], names[zero.find(edge['b'])]
        value = format(edge['R_ohm'], '.17g')
        assert float(value) == edge['R_ohm']
        positive.append('Rmr_{} {} {} {}\n'.format(i, a, b, value))
        edge_ledger.append(dict(raw_edge_id=edge['id'], resistor='Rmr_' + str(i),
                                a=a, b=b, R_ohm=edge['R_ohm'], same_zero_group=a == b))
    assert len(positive) + sum(e['R_ohm'] == 0 for e in raw['edges']) == len(raw['edges'])
    text = ''.join(converted)
    ends = list(re.finditer(r'^\.ends[^\n]*(?:\n|$)', text, re.M | re.I))
    assert len(ends) == 1
    text = text[:ends[0].start()] + ''.join(positive) + text[ends[0].start():]
    assert [l for l in text.splitlines(keepends=True) if re.match(r'^C\S+\s', l, re.I)] == capacitors
    out = args.output / scenario.lower()
    out.mkdir()
    (out / 'conditional_metal.spice').write_text(text)
    (out / 'zero_r_original.spice').write_bytes(args.source.read_bytes())
    assert sha(out / 'zero_r_original.spice') == SOURCE_SHA
    dump(out / 'terminal_map.json', changes)
    dump(out / 'positive_edges.json', edge_ledger)
    dump(out / 'anchors.json', anchors)
    dump(out / 'unqualified_resistor_bn.json', bn)
    fixture = args.fixture.read_text()
    assert fixture.count('\ndc temp -40 125 5\n') == 1
    prefix = fixture.split('\ndc temp -40 125 5\n')[0] + '\n'
    assert prefix.count('\nop\n') == 1
    assert '.include pex_nominal.spice\n' in prefix
    # Only input/output names and output-only observability change. No DC sweep.
    prefix = prefix.replace('.include pex_nominal.spice\n', '.include conditional_metal.spice\n')
    prefix += 'echo METALLIC_POINT_VOLTAGES_BEGIN\n'
    for p in points:
        node = names[point_node[p['id']]]
        expression = 'v(vdd)-v(vdd)' if node == 'vss' else (
            'v({})'.format(node) if node in PORTS else 'v(xbgr.{})'.format(node))
        prefix += 'print {}\n'.format(expression)
    prefix += 'echo METALLIC_POINT_VOLTAGES_END\nquit\n.endc\n.end\n'
    (out / 'nominal.cir').write_text(prefix)
    (out / 'zero_r.cir').write_text(prefix.split('echo METALLIC_POINT_VOLTAGES_BEGIN\n')[0].replace(
        '.include conditional_metal.spice\n', '.include zero_r_original.spice\n') + 'quit\n.endc\n.end\n')
    dump(out / 'point_nodes.json', [dict(point_id=p['id'], node=names[point_node[p['id']]],
                                      source_net=p['source_net']) for p in points])
    return dict(scenario=scenario, status='passed preparation; nonlinear not run',
                raw_network_sha256=sha(result / 'raw_network.json.gz'),
                original_edges=len(raw['edges']), exact_zero_edges=len(raw['edges']) - len(positive),
                preserved_positive_edges=len(positive), contracted_node_count=len(names),
                positive_same_zero_group=sum(e['same_zero_group'] for e in edge_ledger),
                inputs={str(p): sha(p) for p in [result / 'raw_network.json.gz',
                        result / 'summary.json', run / 'independent_audit.json']},
                original_source_reconstruction_sha256=SOURCE_SHA,
                source_devices=dict(primitive_counts), mapped_terminals=len(changes),
                unqualified_ideal_resistor_BN=len(bn), original_capacitors=len(capacitors),
                outputs={p.name: sha(p) for p in sorted(out.iterdir())})


def main():
    ap = argparse.ArgumentParser()
    for name in ('source', 'fixture', 'preparation', 'network-root', 'output', 'resource-gate'):
        ap.add_argument('--' + name, type=Path, required=True)
    args = ap.parse_args()
    assert len(os.sched_getaffinity(0)) == 1
    gate = json.loads(args.resource_gate.read_text())
    when = datetime.datetime.fromisoformat(gate['utc'])
    age = (datetime.datetime.now(datetime.timezone.utc) - when).total_seconds()
    assert gate['status'] == 'passed' and 0 <= age < 1800
    assert sha(args.source) == SOURCE_SHA and sha(args.fixture) == FIXTURE_SHA
    assert sha(args.preparation / 'points.json') == '9ab83676c2b76d38cfaa5146ae7a3def5759b93bb777acdb2af62f178c7cda3f'
    args.output.mkdir(exist_ok=False)
    (args.output / 'worker_snapshot.py').write_bytes(Path(__file__).read_bytes())
    receipt = dict(status='running preparation', nonlinear='not run', adoption='not run')
    dump(args.output / 'summary.json', receipt)
    try:
        receipt['scenarios'] = [prepare(args, s) for s in ('KPEX', 'LEF')]
        receipt['status'] = 'passed conditional source preparation'
        receipt['inputs'] = {str(p): sha(p) for p in [args.source, args.fixture,
                             args.preparation / 'points.json', args.resource_gate, Path(__file__)]}
    except Exception as error:
        receipt.update(status='failed preparation', error=repr(error))
        raise
    finally:
        dump(args.output / 'summary.json', receipt)
        print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()

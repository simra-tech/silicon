#!/usr/bin/env python3
"""Independent saved-SPICE topology and literal-source reconstruction audit."""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import re


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--prepared', type=Path, required=True)
    ap.add_argument('--source', type=Path, required=True)
    args = ap.parse_args()
    receipt = json.loads((args.prepared / 'summary.json').read_text())
    assert receipt['status'] == 'passed conditional source preparation'
    output = []
    for scenario in receipt['scenarios']:
        folder = args.prepared / scenario['scenario'].lower()
        assert all(sha(folder / n) == h for n, h in scenario['outputs'].items())
        transformed = (folder / 'conditional_metal.spice').read_text()
        edges = json.loads((folder / 'positive_edges.json').read_text())
        anchors = json.loads((folder / 'anchors.json').read_text())
        neighbors = collections.defaultdict(set)
        for e in edges:
            neighbors[e['a']].add(e['b'])
            neighbors[e['b']].add(e['a'])
        ownership = {}
        for anchor in anchors:
            net = anchor['source_net']
            seen, stack = set(), [net]
            while stack:
                node = stack.pop()
                if node in seen:
                    continue
                seen.add(node)
                stack.extend(neighbors[node] - seen)
            assert not set(ownership) & seen, 'Metal connects distinct original nets'
            ownership.update({n: net for n in seen})
        assert len(anchors) == 55 and set(ownership) == set(neighbors)
        expected_resistors = {
            e['resistor']: '{} {} {} {}\n'.format(e['resistor'], e['a'], e['b'], format(e['R_ohm'], '.17g'))
            for e in edges}
        restored, resistors, device_count, capacitors = [], [], 0, []
        terminals = {'XR': 3, 'XM': 4, 'XQ': 4}
        for line in transformed.splitlines(keepends=True):
            tokens = list(re.finditer(r'\S+', line))
            if not tokens:
                restored.append(line)
                continue
            identifier = tokens[0].group()
            if identifier.startswith('Rmr_'):
                assert line == expected_resistors[identifier]
                resistors.append(identifier)
                continue
            if identifier[:2] in terminals:
                device_count += 1
                for i in reversed(range(1, 1 + terminals[identifier[:2]])):
                    token = tokens[i]
                    name = token.group()
                    assert name in ownership
                    line = line[:token.start()] + ownership[name] + line[token.end():]
            if re.match(r'^C\S+\s', line, re.I):
                capacitors.append(line)
                assert all(tokens[i].group() in ownership for i in (1, 2))
            restored.append(line)
        assert ''.join(restored).encode() == args.source.read_bytes()
        assert len(resistors) == len(set(resistors)) == len(edges) == 42855
        assert device_count == 1036 and len(capacitors) == 329
        assert sha(folder / 'zero_r_original.spice') == sha(args.source)
        assert len(ownership) == 33650
        output.append(dict(scenario=scenario['scenario'], status='passed independent source/topology audit',
                           original_bytes_reconstructed_by_full_R_graph_contraction=True,
                           unchanged_model_records=1036, original_capacitors=329,
                           exactly_preserved_positive_resistors=len(edges), source_net_components=55,
                           contracted_nodes=len(ownership), no_generic_contact_R=True,
                           no_fixed_current_injections=True, nonlinear='not run',
                           physical_reference_plane='not qualified', electrode_double_count='unresolved'))
    target = args.prepared / 'independent_source_audit.json'
    assert not target.exists()
    target.write_text(json.dumps(dict(status='passed', source_sha256=sha(args.source),
                                     worker_sha256=sha(Path(__file__)), scenarios=output), indent=2) + '\n')
    print(target.read_text())


if __name__ == '__main__':
    main()

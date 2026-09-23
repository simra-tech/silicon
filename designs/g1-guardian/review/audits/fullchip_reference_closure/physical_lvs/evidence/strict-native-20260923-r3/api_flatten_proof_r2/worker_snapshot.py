#!/usr/bin/env python3
"""Independent hierarchy terminal-union proof around native API flattening."""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import traceback
import pya


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def parameters(d):
    return {p.name: d.parameter(p.name).hex() for p in d.device_class().parameter_definitions()}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--database', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    a = ap.parse_args()
    assert not a.output.exists() and set(os.sched_getaffinity(0)) == {1}
    assert sha(a.database) == '1c8f3f91b8be00e0fbbdf4c2a40734fb5f8fe8b0388b1780768699e1a2afcbcf'
    assert pya.__version__ == '0.30.9'
    a.output.mkdir(parents=True)
    (a.output / 'worker_snapshot.py').write_bytes(Path(__file__).read_bytes())
    result = dict(status='running independent API flatten audit', new_extraction='not run', comparison='not run')
    try:
        db = pya.LayoutVsSchematic()
        db.read(str(a.database))
        nl = db.netlist().dup()
        top = nl.circuit_by_name('placed_core_NOT_CONNECTED_FULLCHIP')
        assert top
        parent = {}
        expected = {}
        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x
        def unite(a, b):
            a, b = find(a), find(b)
            if a != b:
                parent[b] = a
        def walk(circuit, path):
            nets = {}
            for n in circuit.each_net():
                assert n.cluster_id not in nets
                key = (tuple(path), n.cluster_id)
                nets[n.cluster_id] = key
                parent[key] = key
            for d in circuit.each_device():
                name = '.'.join(path + [d.expanded_name()])
                assert name not in expected
                expected[name] = dict(model=d.device_class().name, parameters=parameters(d),
                    terminals={t.name: nets[d.net_for_terminal(t.name).cluster_id] for t in d.device_class().terminal_definitions()})
            for inst in circuit.each_subcircuit():
                child = inst.circuit_ref()
                child_nets = walk(child, path + [inst.expanded_name()])
                for pin in child.each_pin():
                    pn, cn = inst.net_for_pin(pin.id()), child.net_for_pin(pin.id())
                    assert pn is not None and cn is not None
                    unite(nets[pn.cluster_id], child_nets[cn.cluster_id])
            return nets
        top_nets = walk(top, [])
        pins = [(p.id(), p.name(), top_nets[top.net_for_pin(p.id()).cluster_id]) for p in top.each_pin()]
        expected_roots = {find(k) for k in parent}
        before_models = Counter(v['model'] for v in expected.values())
        result.update(before_devices=len(expected), before_hierarchy_nets=len(parent),
                      independently_unioned_nets=len(expected_roots), original_top_pins=[p[1] for p in pins],
                      original_top_pin_count=len(pins), before_models=dict(before_models))
        nl.flatten()
        flat = nl.circuit_by_name('placed_core_NOT_CONNECTED_FULLCHIP')
        assert sum(1 for _ in flat.each_subcircuit()) == 0
        actual = {d.expanded_name(): d for d in flat.each_device()}
        result['after_devices'] = len(actual)
        result['missing_names'] = sorted(set(expected) - set(actual))[:30]
        result['extra_names'] = sorted(set(actual) - set(expected))[:30]
        assert set(actual) == set(expected), 'Flattened device path identity changed'
        flat_nets = list(flat.each_net())
        for i, net in enumerate(flat_nets):
            net.set_property('_G1_READONLY_AUDIT_NET_ID', i)
        forward, reverse = {}, {}
        def bind(old, new):
            old = find(old)
            new = new.property('_G1_READONLY_AUDIT_NET_ID')
            assert new is not None
            if old in forward:
                assert forward[old] == new, 'API flatten split an independently united net'
            if new in reverse:
                assert reverse[new] == old, 'API flatten merged independent nets'
            forward[old], reverse[new] = new, old
        terminal_count = 0
        for name, old in expected.items():
            d = actual[name]
            assert old['model'] == d.device_class().name
            assert old['parameters'] == parameters(d), 'Binary64 parameter changed'
            assert set(old['terminals']) == {t.name for t in d.device_class().terminal_definitions()}
            for terminal, key in old['terminals'].items():
                bind(key, d.net_for_terminal(terminal))
                terminal_count += 1
        observed_pins = [(p.id(), p.name()) for p in flat.each_pin()]
        assert observed_pins == [(p[0], p[1]) for p in pins]
        for pin_id, _, key in pins:
            bind(key, flat.net_for_pin(pin_id))
        assert len(flat_nets) == len(expected_roots)
        assert len(forward) == len(expected_roots), 'Unobserved isolated net: cannot claim complete graph coverage'
        result.update(status='passed exact primitive/terminal-graph API flatten proof',
                      terminal_connections=terminal_count, after_nets=len(flat_nets),
                      complete_bijective_terminal_graph=True, all_binary64_parameters_exact=True,
                      source_top_pin_mismatch='failed retained 71-versus-22; not repaired',
                      metadata_only_net_ids='Audit properties only; no electrical node or device mutation.',
                      database_sha256=sha(a.database), script_sha256=sha(Path(__file__)))
    except BaseException as exc:
        result.update(status='failed API flatten audit', exception=repr(exc), traceback=traceback.format_exc())
        raise
    finally:
        (a.output / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
        print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()

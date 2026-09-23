#!/usr/bin/env python3
"""Check source connectivity after deleting only proved CTS buffer/load roles."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
from fullchip_reference_closure.audit_reference import parse_verilog


def normalize(instances):
    aliases, regular, loads = {}, {}, []
    for name, row in instances.items():
        master, c = row['master'], row['connections']
        if name.startswith('clkbuf_'):
            assert re.fullmatch(r'sg13g2_buf_\d+', master), (name, master)
            assert set(c) == {'A', 'X'} and c['X'] not in aliases
            aliases[c['X']] = c['A']
        elif name.startswith('clkload'):
            assert re.fullmatch(r'clkload\d+', name)
            assert re.fullmatch(r'sg13g2_(buf|inv)_\d+', master)
            assert set(c) == {'A'}, 'Dummy has a connected output'
            loads.append(c['A'])
        else:
            regular[name] = row

    def resolve(net):
        seen = set()
        while net in aliases:
            assert net not in seen, 'Clock buffer cycle'
            seen.add(net)
            net = aliases[net]
        return net

    for net in aliases:
        resolve(net)
    result = {name: dict(master=row['master'], connections={p: resolve(n) for p, n in row['connections'].items()})
              for name, row in regular.items()}
    # Count every actual attached pin, including dummy loads, without
    # removing their physical loading from the fanout result.
    incidence = Counter(n for row in instances.values() for n in row['connections'].values())
    fanout = {name: incidence[row['connections']['X']] - 1
              for name, row in instances.items() if name.startswith('clkbuf_')}
    return result, fanout, len(loads)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--reference', type=Path, required=True)
    p.add_argument('--candidate', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    assert not a.output.exists()
    observations = []
    for path in (a.reference, a.candidate):
        module, ports, instances = parse_verilog(path.read_text())
        normalized, fanout, loads = normalize(instances)
        observations.append((module, ports, normalized))
        if path == a.candidate:
            detail = dict(instances=len(instances), nonclock_instances=len(normalized),
                          clock_buffers=len(fanout), dangling_output_clock_loads=loads,
                          fanout=fanout, max_clock_fanout=max(fanout.values()),
                          over_limit={k: v for k, v in fanout.items() if v > 8})
    result = dict(status='passed' if observations[0] == observations[1] else 'failed',
                  check='Exact named non-clock device and terminal graph after proved noninverting CTS buffer contraction',
                  inputs={str(x): hashlib.sha256(x.read_bytes()).hexdigest() for x in (a.reference, a.candidate)},
                  candidate=detail,
                  fanout_status='failed' if detail['over_limit'] else 'passed',
                  not_run=['Timing equivalence', 'Placement geometry', 'Routed parasitics', 'Physical signoff'])
    a.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'candidate'}, indent=2))
    assert result['status'] == 'passed'


if __name__ == '__main__':
    main()

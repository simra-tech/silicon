#!/usr/bin/env python3
"""Audit all routed macro STA corners and every unannotated clock dummy."""
import argparse
import hashlib
import json
from pathlib import Path
import re
from fullchip_reference_closure.audit_reference import parse_verilog
from audit_digital_cts_graph import normalize


def annotation_control(report, instances):
    match = re.search(r'Found (\d+) unannotated drivers\.\n(.*?)Found (\d+) partially unannotated drivers\.', report, re.S)
    assert match and int(match.group(3)) == 0
    lines = [x.strip() for x in match.group(2).splitlines() if x.strip()]
    expected = {name for name in instances if re.fullmatch(r'clkload\d+', name)}
    assert len(lines) == int(match.group(1)) == len(expected) == 60
    found = set()
    for line in lines:
        name, pin = line.rsplit('/', 1)
        assert name in expected and name not in found
        row = instances[name]
        master = row['master']
        assert re.fullmatch(r'sg13g2_(buf|inv)_\d+', master)
        assert pin == ('Y' if '_inv_' in master else 'X')
        assert set(row['connections']) == {'A'}, 'Output is connected'
        found.add(name)
    assert found == expected
    return len(found)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--sta', type=Path, required=True)
    p.add_argument('--netlist', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    assert not a.output.exists()
    module, ports, instances = parse_verilog(a.netlist.read_text())
    assert module == 'g1_digital'
    normalized, fanout, loads = normalize(instances)
    assert len(fanout) == 222 and max(fanout.values()) <= 8 and loads == 60
    state = a.sta/'state_out.json'
    metrics = json.loads(state.read_text())['metrics']
    corners = ('nom_fast_1p32V_m40C', 'nom_slow_1p08V_125C', 'nom_typ_1p20V_25C')
    held = [a.netlist, state, Path(__file__)]
    results = {}
    for corner in corners:
        suffix = '__corner:'+corner
        for key in ('design__max_slew_violation__count', 'design__max_fanout_violation__count',
                    'design__max_cap_violation__count', 'timing__hold_vio__count',
                    'timing__setup_vio__count', 'timing__unannotated_net_filtered__count'):
            assert metrics[key+suffix] == 0, (corner, key)
        assert metrics['timing__unannotated_net__count'+suffix] == 60
        report = a.sta/corner/'checks.rpt'
        held.append(report)
        count = annotation_control(report.read_text(), instances)
        setup, hold = [metrics['timing__'+x+'__ws'+suffix] for x in ('setup', 'hold')]
        assert setup > 0 and hold > 0
        results[corner] = dict(setup_slack_ns=setup, hold_slack_ns=hold,
                               exactly_unconnected_dummy_outputs=count)
    record = dict(status='passed scoped routed macro STA and annotation audit',
                  corners=results, max_clock_fanout=max(fanout.values()),
                  clock_buffers=len(fanout), inputs_sha256={str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in held},
                  not_run=['Full-chip timing integration', 'Physical signoff adoption',
                           'Analog jitter and metastability qualification'],
                  not_applicable=['Statistical seed'])
    a.output.write_text(json.dumps(record, indent=2)+'\n')
    print(json.dumps(record, indent=2))


if __name__ == '__main__':
    main()

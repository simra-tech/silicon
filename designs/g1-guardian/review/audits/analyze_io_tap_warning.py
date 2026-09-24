#!/usr/bin/env python3
"""Decode the saved LevelUpInv tap pair, including MatchWithWarning details."""
import argparse
import hashlib
import json
from pathlib import Path
import re

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('directory', type=Path)
a = p.parse_args()
target = a.directory / 'tap_warning_analysis.json'
assert not target.exists()
rows = []
for variant in ('original', 'normalized'):
    path = a.directory / variant / 'lvs/g1_chip_top.lvsdb'
    text = path.read_text()
    layout, rest = text.split('\nH(\n', 1)
    reference, cross = rest.split('\nZ(\n', 1)
    def parse_devices(section):
        devices = {}
        for identifier, model, body in re.findall(r'^  D\((\d+) (\S+)\n(.*?)^  \)', section, re.M | re.S):
            devices[identifier] = {'class': model,
                                  'parameters': {name: float(value) for name, value in re.findall(r'^   E\((\S+) ([-+0-9.eE]+)\)', body, re.M)},
                                  'terminals': dict(re.findall(r'^   T\((\S+) (\d+)\)', body, re.M))}
        return devices
    ld, rd = parse_devices(layout), parse_devices(reference)
    assert len(ld) == 9 and len(rd) == (8 if variant == 'original' else 9)
    taps = {key: value for key, value in ld.items() if 'ptap1' in value['class'].lower()}
    assert len(taps) == 1
    tap_id, tap = next(iter(taps.items()))
    pair = re.search(r'^   D\(' + tap_id + r' (\d+|\(\)) (\S+)\)', cross, re.M)
    assert pair
    netpairs = {left: (right, status) for left, right, status in re.findall(r'^   N\((\d+) (\d+) (\S+)\)', cross, re.M)}
    record = {'variant': variant, 'database_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
              'tap_pair_status': {'0': 'Mismatch', 'W': 'MatchWithWarning', '1': 'Match'}[pair[2]],
              'layout_tap': tap, 'reference_tap': None if pair[1] == '()' else rd[pair[1]],
              'circuit_status': 'failed', 'mismatched_net_pairs': [
                  {'layout_net_id': left, 'reference_net_id': right}
                  for left, (right, status) in netpairs.items() if status == '0']}
    if variant == 'normalized':
        assert pair[2] == 'W'
        reference_tap = record['reference_tap']
        assert reference_tap['class'] == 'PTAP1'
        record['parameter_differences'] = {
            name: {'layout': tap['parameters'][name], 'reference': reference_tap['parameters'][name],
                   'delta': tap['parameters'][name] - reference_tap['parameters'][name]}
            for name in ('A', 'P')}
        record['terminal_mapping_consistent_with_compared_net_pairs'] = all(
            netpairs[layout_net][0] == reference_tap['terminals'][terminal]
            for terminal, layout_net in tap['terminals'].items())
        assert record['terminal_mapping_consistent_with_compared_net_pairs']
    else:
        assert pair[1] == '()' and pair[2] == '0'
    rows.append(record)
result = {'scope': 'Detailed saved-database diagnosis; MatchWithWarning is not parameter acceptance. No new LVS or golden-reference change.',
          'binding_repair': 'passed', 'parameter_comparison': 'failed',
          'standalone_LVS': 'failed', 'rows': rows,
          'interpretation': 'Normalized tap TIE/WELL respect existing net pairing, while A and P differ; mismatched nets are incident on that warned device. This diagnoses the local case, not full assembled connectivity.'}
target.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))

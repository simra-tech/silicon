#!/usr/bin/env python3
"""Replace only historical parasitics in isolated views, preserving1036 models."""
import argparse
import collections
from decimal import Decimal
import json
from pathlib import Path
import re

from audit_unsimplified import sha, SOURCE
from run_pex_prepare import HERE


def number(token):
    match = re.fullmatch(r'([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)([afpnum]?)', token)
    assert match is not None, token
    return Decimal(match[1]) * {'': Decimal(1), 'a': Decimal('1e-18'), 'f': Decimal('1e-15'),
                              'p': Decimal('1e-12'), 'n': Decimal('1e-9'), 'u': Decimal('1e-6'), 'm': Decimal('1e-3')}[match[2]]


def logical_lines(text):
    lines = []
    for line in text.splitlines():
        if line.startswith('+'):
            assert lines
            lines[-1] += ' ' + line[1:].strip()
        else:
            lines.append(line)
    return lines


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--extraction', type=Path, required=True)
    ap.add_argument('--cpex', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    assert not args.output.exists()
    args.output.mkdir()
    report = {'status': 'running', 'scope': 'isolated derived parasitic views; no canonical edit or adoption',
              'superseded_intent': 'Adding newCC to baseline329C was rejected before conversion because it double-counts parasitics.',
              'electrical_stability': 'not run', 'wire_resistance': 'not run', 'seed': 'not applicable'}
    def save():
        (args.output / 'summary.json').write_text(json.dumps(report, indent=2) + '\n')
    save()
    try:
        assert sha(SOURCE) == '586ffb58b6af31c77a2e7cbcb83b173ffa4713ec62401da30901c5a7e606283b'
        extraction_path = args.extraction / 'source_device_audit.json'
        extraction = json.loads(extraction_path.read_text())
        assert extraction['status'] == 'passed' and extraction['instance_count'] == 1027
        cpex_path = args.cpex / 'summary.json'
        cpex = json.loads(cpex_path.read_text())
        assert cpex['status'] == 'passed capacitance generation' and cpex['inputs_support_unchanged']
        raw = Path(cpex['raw_pex'])
        assert sha(raw) == cpex['raw_pex_sha256']
        original = SOURCE.read_bytes()
        lines = original.decode().splitlines(keepends=True)
        cap_positions = [(i, line) for i, line in enumerate(lines) if line.lstrip().lower().startswith('c')]
        assert len(cap_positions) == 329
        assert all(line.startswith('Cext_') and len(line.split()) == 4 for _, line in cap_positions)
        assert {line.split()[0] for _, line in cap_positions} == {'Cext_' + str(i) for i in range(1, 330)}
        historical_source = HERE.parent.parent / 'sim/postlayout/g1_bgr_pex.spice'
        assert sha(historical_source) == '72417e072003d2ce28a108c47ef6ac86927ce6c6f89f3a614f360165a31c9d77'
        assert [line for _, line in cap_positions] == [line for line in historical_source.read_text().splitlines(keepends=True) if line.startswith('Cext_')]
        old_names = {line.split()[0] for _, line in cap_positions}
        device_lines = [line for line in lines if line.startswith(('XM', 'XR', 'XQ'))]
        assert len(device_lines) == 1036
        source_nodes = set()
        for line in device_lines:
            fields = line.split()
            source_nodes.update(fields[1:4] if fields[0].startswith('XR') else fields[1:5])
        assert len(source_nodes) == 55
        mapping = extraction['net_map']
        assert len(mapping) == 55 and set(mapping.values()) == source_nodes
        assert len(set(mapping.values())) == 55
        # VSUBS is KPEX's global physical-substrate capacitive reference; this
        # block uses generalVSS substrate/guard. It is NOT internal HBT s1/t.
        mapping = dict(mapping, VSUBS='vss')
        kept = [(i, line) for i, line in enumerate(lines) if i not in {index for index, _ in cap_positions}]
        reconstructed = ''.join(line for _, line in sorted(kept + cap_positions)).encode()
        assert reconstructed == original
        skeleton = ''.join(line for _, line in kept).encode()
        assert [line for line in skeleton.decode().splitlines(keepends=True) if line.startswith(('XM', 'XR', 'XQ'))] == device_lines
        assert not any(line.lstrip().lower().startswith('c') for line in skeleton.decode().splitlines())
        caps = []
        used_names = set()
        terminal_audit = []
        net_total = collections.defaultdict(Decimal)
        raw_lines = logical_lines(raw.read_text())
        raw_cap_lines = [line for line in raw_lines if line.lstrip().lower().startswith('c')]
        assert all(line.startswith('Cext_') for line in raw_cap_lines)
        for line in raw_lines:
            fields = line.split()
            if not fields or not fields[0].startswith('Cext_'):
                continue
            assert len(fields) == 4 and fields[0] not in used_names
            used_names.add(fields[0])
            keys = [token.replace('\\', '') for token in fields[1:3]]
            assert all(key in mapping for key in keys), keys
            nodes = [mapping[key] for key in keys]
            value = number(fields[3])
            assert value.is_finite() and value >= 0
            name = 'Ccoord_' + fields[0][5:]
            assert name not in old_names
            caps.append(name + ' ' + ' '.join(nodes) + ' ' + str(value) + '\n')
            terminal_audit.append({'raw_name': fields[0], 'new_name': name, 'raw_nodes': fields[1:3],
                                   'mapped_nodes': nodes, 'raw_value': fields[3], 'farads': str(value),
                                   'shorted_after_mapping': nodes[0] == nodes[1]})
            for node in set(nodes):
                net_total[node] += value
        assert len(caps) == cpex['capacitor_count'] and len(caps) > 0
        assert len(caps) == len(raw_cap_lines)
        assert not any(line.startswith('Rext') for line in raw_lines)
        sk_lines = skeleton.decode().splitlines(keepends=True)
        end = [i for i, line in enumerate(sk_lines) if line.lower().startswith('.ends')]
        assert len(end) == 1
        new = ''.join(sk_lines[:end[0]] + caps + sk_lines[end[0]:]).encode()
        assert [line for line in new.decode().splitlines(keepends=True) if line.startswith(('XM', 'XR', 'XQ'))] == device_lines
        assert [line for line in new.decode().splitlines(keepends=True) if not line.startswith('Ccoord_')] == sk_lines
        for name, data in [('baseline_586.spice', original), ('reconstructed_586.spice', reconstructed),
                           ('zero_new_capacitance.spice', skeleton), ('coordinated_cc.spice', new)]:
            (args.output / name).write_bytes(data)
        old_ledger = [{'line_index_zero_based': i, 'line_exact': line, 'farads': str(number(line.split()[3]))} for i, line in cap_positions]
        (args.output / 'historical_329_ledger.json').write_text(json.dumps(old_ledger, indent=2) + '\n')
        (args.output / 'capacitance_mapping.json').write_text(json.dumps({'net_mapping': mapping, 'capacitors': terminal_audit}, indent=2) + '\n')
        (args.output / Path(__file__).name).write_bytes(Path(__file__).read_bytes())
        report.update(status='passed view preparation', inputs={str(path): sha(path) for path in (SOURCE, historical_source, extraction_path, cpex_path, raw, Path(__file__))},
                      artifacts={path.name: sha(path) for path in args.output.iterdir() if path.name != 'summary.json'},
                      source_devices_unchanged=1036, historical_capacitors=329,
                      historical_total_f=str(sum((number(line.split()[3]) for _, line in cap_positions), Decimal(0))),
                      new_capacitors=len(caps), new_total_f=str(sum((Decimal(row['farads']) for row in terminal_audit), Decimal(0))),
                      shorted_capacitors_retained=sum(row['shorted_after_mapping'] for row in terminal_audit),
                      net_total_f={key: str(value) for key, value in sorted(net_total.items())},
                      line_position_reconstruction='passed; byte-identical586 including original329C',
                      zero_newC_control='passed; exact cap-free1036-device skeleton, NOT original329-C source',
                      intentional_capacitor_audit='passed: all329 capacitor statements byte-identical historicalpostlayoutCext_1..329; no other capacitor statements',
                      substrate_mapping='VSUBS→generalVSS, consistent originalblock substrate convention; does NOT map internal HBT s1/t',
                      original_source_unchanged=sha(SOURCE) == '586ffb58b6af31c77a2e7cbcb83b173ffa4713ec62401da30901c5a7e606283b')
    except Exception as error:
        report.update(status='failed', error=repr(error))
    save()
    print(json.dumps({key: value for key, value in report.items() if key not in ('artifacts', 'inputs', 'net_total_f')}, indent=2))
    return 0 if report['status'] == 'passed view preparation' else 1


if __name__ == '__main__':
    raise SystemExit(main())

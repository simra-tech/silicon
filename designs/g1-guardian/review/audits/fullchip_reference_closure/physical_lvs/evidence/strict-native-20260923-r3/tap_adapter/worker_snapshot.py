#!/usr/bin/env python3
"""A separately named source-only tap syntax view; no parameter correction."""
import argparse
import hashlib
import json
from pathlib import Path
import re


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def adapt(source):
    lines = source.splitlines(keepends=True)
    pattern = re.compile(r'^(\s*)(X\S+)(\s+\S+\s+\S+\s+[pn]tap1\s+.*?)(\r?\n)?$', re.I)
    edits, seen, cells = [], {}, {}
    current = None
    for i, line in enumerate(lines):
        header = re.match(r'^\s*\.subckt\s+(\S+)', line, re.I)
        if header:
            current = header[1]
            assert current.casefold() not in cells
            cells[current.casefold()] = current
            seen[current] = set()
        fields = line.strip().split()
        if current and fields and fields[0][0].upper() in 'RMCQDXL':
            assert fields[0].casefold() not in seen[current]
            seen[current].add(fields[0].casefold())
        match = pattern.match(line)
        if match:
            assert current
            new_name = 'R_G1_TAP_SYNTAX_' + match[2]
            edits.append(dict(line_number=i + 1, cell=current, original_name=match[2],
                              adapted_name=new_name, exact_suffix=match[3],
                              original=line, adapted=match[1] + new_name + match[3] + (match[4] or '')))
    assert edits
    for e in edits:
        assert e['adapted_name'].casefold() not in seen[e['cell']]
        seen[e['cell']].add(e['adapted_name'].casefold())
        lines[e['line_number'] - 1] = e['adapted']
    result = ''.join(lines)
    restored = result.splitlines(keepends=True)
    for e in edits:
        assert restored[e['line_number'] - 1] == e['adapted']
        restored[e['line_number'] - 1] = e['original']
    assert ''.join(restored) == source
    assert len(lines) == len(source.splitlines(keepends=True))
    return result, edits


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    assert not a.output.exists()
    assert sha(a.source) == 'f4ce6848bd7dd179d2ef4cbd8a4ea6bf9788bcfa1ff4b93fabae8bf18b6378f9'
    source = a.source.read_bytes().decode('utf-8')
    result, edits = adapt(source)
    assert len(edits) == 63 and len({e['cell'] for e in edits}) == 41
    control = '.SUBCKT CONTROL A B\nXR0 A B ptap1 A=1p P=4u\n.ENDS\n'
    assert adapt(control)[1][0]['exact_suffix'] == ' A B ptap1 A=1p P=4u'
    negative_cases = [control.replace('.ENDS', 'R_G1_TAP_SYNTAX_XR0 A B 1\n.ENDS'),
                      control.replace('.ENDS', 'xr0 A B ptap1 A=1p P=4u\n.ENDS'),
                      control.replace('XR0 A B ptap1 A=1p P=4u\n', '')]
    for case in negative_cases:
        try:
            adapt(case)
        except AssertionError:
            pass
        else:
            raise AssertionError('Invalid collision/empty control accepted')
    a.output.mkdir(parents=True)
    target = a.output / 'fullchip_tap_prefix_only.cdl'
    target.write_bytes(result.encode())
    (a.output / 'worker_snapshot.py').write_bytes(Path(__file__).read_bytes())
    report = dict(status='passed source-only adapter preparation; not adopted',
                  source_sha256=sha(a.source), adapted_sha256=sha(target), script_sha256=sha(Path(__file__)),
                  edits=edits, checks=dict(exact_reverse_transform='passed',
                  node_model_parameter_suffixes='passed byte-identical', instance_counts='passed unchanged',
                  unique_names='passed', collision_duplicate_empty_negative_controls='passed',
                  stock_reader='not run', stock_LVS='not run', native_geometry_changes='not applicable',
                  electrical_model_parameter_changes='not applicable', stochastic_seed='not applicable'),
                  retained_failures=['Original tap A/P disagreement remains unmodified.',
                                     'Missing PolyRes recognition is a separate native issue.',
                                     'Parent-joined clamp/diode topology remains a separate audit.'])
    (a.output / 'summary.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'edits'}, indent=2))


if __name__ == '__main__':
    main()

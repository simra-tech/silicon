#!/usr/bin/env python3
"""Audit the saved R100 raw CC boundary without assigning missing terminals."""
import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def assess(rows, expected):
    assert len(expected) == 134 and 'VSUBS' not in expected
    assert len(rows) == 978
    seen = set()
    substrate = []
    source = []
    for row in rows:
        a, b = row['net1'], row['net2']
        pair = tuple(sorted((a, b)))
        assert a != b and pair not in seen
        seen.add(pair)
        value = row['capacitance_fF']
        assert math.isfinite(value) and value > 0
        assert float.fromhex(row['capacitance_fF_hex']) == value
        assert a in expected or a == 'VSUBS'
        assert b in expected or b == 'VSUBS'
        (substrate if 'VSUBS' in pair else source).append(value)
    assert len(source) == 844 and len(substrate) == 134
    assert {next(n for n in (r['net1'], r['net2']) if n != 'VSUBS')
            for r in rows if 'VSUBS' in (r['net1'], r['net2'])} == expected
    return {'source_pair_count': len(source), 'unbound_VSUBS_count': len(substrate),
            'unbound_VSUBS_total_fF': math.fsum(substrate),
            'unbound_VSUBS_max_fF': max(substrate)}


def self_test():
    expected = {'n{:03d}'.format(i) for i in range(134)}
    rows = [dict(net1=n, net2='VSUBS', capacitance_fF=1.0,
                 capacitance_fF_hex=(1.0).hex()) for n in sorted(expected)]
    for i, (a, b) in enumerate(itertools.islice(itertools.combinations(sorted(expected), 2), 844)):
        value = float(i + 1)
        rows.append(dict(net1=a, net2=b,
                         capacitance_fF=value, capacitance_fF_hex=value.hex()))
    assert assess(rows, expected)['unbound_VSUBS_count'] == 134
    rows[-1] = dict(rows[-2])  # Deliberately duplicate a pair.
    try:
        assess(rows, expected)
    except AssertionError:
        pass
    else:
        raise AssertionError('duplicate-pair control escaped')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--field', type=Path)
    parser.add_argument('--native', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        self_test()
        print('passed duplicate-pair rejection control')
        return
    assert args.field and args.native and args.output and not args.output.exists()
    field = json.loads((args.field / 'summary.json').read_text())
    native = json.loads((args.native / 'manifest.json').read_text())
    cap_path = args.field / 'exact_capacitances.json'
    assert field['status'] == 'passed raw native CC only; completefield FAILED'
    assert field['source_sha256'] == native['source_sha256']
    assert field['native_GDS_sha256'] == native['GDS_sha256']
    assert field['capacitor_sha256'] == digest(cap_path)
    assert field['capacitor_count'] == 978
    assert field['unknown_capacitor_nodes'] == []
    assert field['VSUBS'] == 'unbound extractor substrate; no implicit0/VSS assignment'
    counts = assess(json.loads(cap_path.read_text()), set(field['expected_source_labels']))
    result = dict(status='passed saved CC inventory; complete PEX not qualified',
                  source_sha256=field['source_sha256'],
                  native_GDS_sha256=native['GDS_sha256'],
                  field_summary_sha256=digest(args.field / 'summary.json'),
                  capacitances_sha256=digest(cap_path),
                  checks=counts, VSUBS_binding='unsupported; not assigned to VSS or zero',
                  MIM_extrinsic='not qualified', tap_contact_fields='not qualified',
                  finite_wire_resistance='not run in CC extraction',
                  compact_model_plane='not qualified', full_PEX='not qualified')
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps(result['checks']))


if __name__ == '__main__':
    main()

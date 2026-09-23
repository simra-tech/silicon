#!/usr/bin/env python3
"""Read completed points from ngspice-46 binary raw, including a stopped run."""
import argparse
import json
import math
import re
import struct
from pathlib import Path


def read_raw(path):
    raw = path.read_bytes()
    header, body = raw.split(b'Binary:\n', 1)
    text = header.decode('ascii')
    assert 'Flags: real' in text
    number = int(re.search(r'No. Variables:\s*(\d+)', text).group(1))
    names = [line.split()[1] for line in text.split('Variables:\n')[1].splitlines()
             if line.strip() and line.strip()[0].isdigit()]
    assert len(names) == number and names[0] == 'time'
    stride = 8 * number
    rows = [row for row in struct.iter_unpack('<' + 'd' * number,
             body[:len(body) // stride * stride])]
    assert rows and all(math.isfinite(x) for row in rows for x in row)
    assert rows[0][0] == 0 and all(b[0] > a[0] for a, b in zip(rows, rows[1:]))
    return names, rows, len(body) % stride


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--raw', type=Path, required=True)
    p.add_argument('--control-wave', type=Path)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    assert not a.output.exists()
    names, rows, partial = read_raw(a.raw)
    result = dict(status='diagnostic only; no 16us acceptance',
                  saved_vectors=names, complete_points=len(rows),
                  trailing_incomplete_bytes=partial, first_s=rows[0][0],
                  last_s=rows[-1][0], first_10ns_points=sum(r[0] <= 10e-9 for r in rows))
    if a.control_wave:
        lines = a.control_wave.read_text().splitlines()
        labels = lines[0].split()
        control = [list(map(float, line.split())) for line in lines[1:] if line.strip()]
        assert len(control) == len(rows)
        common = sorted(set(names) & set(labels))
        assert len(common) >= 8
        checks = {}
        for name in common:
            i, j = names.index(name), labels.index(name)
            checks[name] = max(abs(rawrow[i] - textrow[j]) for rawrow, textrow in zip(rows, control))
        assert all(v == 0 for v in checks.values()), checks
        result.update(prefix_exact='passed', common_vector_count=len(common),
                      common_max_abs_difference=checks)
    else:
        tail = rows[max(0, len(rows) - 1000):]
        steps = [(b[0] - a[0], b[0]) for a, b in zip(rows, rows[1:])]
        result['first_step_below'] = {
            str(limit): next((time for step, time in steps if step < limit), None)
            for limit in [1e-10, 1e-11, 1e-12, 1e-13, 1e-14]}
        result['step_counts_below'] = {
            str(limit): sum(step < limit for step, _ in steps)
            for limit in [1e-10, 1e-11, 1e-12, 1e-13, 1e-14]}
        result['tail_1000_span_s'] = tail[-1][0] - tail[0][0]
        result['tail_1000_min_step_s'] = min(b[0] - a[0] for a, b in zip(tail, tail[1:]))
        result['tail_1000_max_step_s'] = max(b[0] - a[0] for a, b in zip(tail, tail[1:]))
        result['tail_ranges'] = {name: [min(row[i] for row in tail), max(row[i] for row in tail)]
                                 for i, name in enumerate(names) if i}
        behavior = []
        for i, name in enumerate(names[1:], 1):
            values = [row[i] for row in tail]
            changes = [b - a for a, b in zip(values, values[1:])]
            span = max(values) - min(values)
            variation = sum(abs(x) for x in changes)
            flips = sum(a * b < 0 for a, b in zip(changes, changes[1:]))
            behavior.append(dict(name=name, span=span, total_variation=variation,
                                 variation_to_span=variation / span if span else 0,
                                 sign_flips=flips))
        result['largest_tail_variation_to_span'] = sorted(
            behavior, key=lambda q: q['variation_to_span'], reverse=True)[:30]
        result['largest_tail_voltage_spans'] = sorted(
            (q for q in behavior if q['name'].startswith('v(')),
            key=lambda q: q['span'], reverse=True)[:30]
    a.output.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps({k: result[k] for k in ['complete_points', 'last_s']}))


if __name__ == '__main__':
    main()

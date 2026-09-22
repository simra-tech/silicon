"""Strict decoded-byte and numeric prefix gate; no resampling or tolerances."""
import hashlib
import math
from wave_archive import open_wave


def select_prefix(raw, stop_s=200e-9):
    lines = raw.splitlines(keepends=True)
    assert len(lines[0].split()) == 18
    parsed = [list(map(float, line.split())) for line in lines[1:]]
    assert parsed and all(len(row) == 18 and all(math.isfinite(v) for v in row) for row in parsed)
    assert parsed[0][0] == 0 and parsed[-1][0] > stop_s
    assert all(a[0] < b[0] for a, b in zip(parsed, parsed[1:]))
    kept = [(line, row) for line, row in zip(lines[1:], parsed) if row[0] <= stop_s]
    assert kept
    decoded = lines[0]+b''.join(line for line, row in kept)
    return {'bytes': decoded, 'rows': [row for line, row in kept],
            'sha256': hashlib.sha256(decoded).hexdigest(), 'byte_count': len(decoded),
            'row_count': len(kept), 'last_included_time_s': kept[-1][1][0]}


def compare_prefix_bytes(reference, candidate):
    old, new = select_prefix(reference), select_prefix(candidate)
    numeric = old['rows'] == new['rows']
    byte_exact = old['bytes'] == new['bytes']
    difference = next((i for i, (a, b) in enumerate(zip(old['rows'], new['rows'])) if a != b), None)
    return {'status': 'passed exact decoded bytes and numeric rows' if numeric and byte_exact else 'failed prefix parity',
            'numeric_rows_exact': numeric, 'decoded_bytes_exact': byte_exact,
            'reference': {key: old[key] for key in ['sha256', 'byte_count', 'row_count', 'last_included_time_s']},
            'candidate': {key: new[key] for key in ['sha256', 'byte_count', 'row_count', 'last_included_time_s']},
            'first_differing_numeric_row_zero_based': difference,
            'scope': 'All original18columns including time, decoded header/row bytes andnumeric values for0<=t<=200ns. No interpolation, tolerance, row removal or alternate sample alignment.219ns endpoint deliberately excluded; laterfullwave analyzed separately.'}


def compare_prefix_waves(reference, candidate):
    with open_wave(reference, 'rb') as stream:
        old = stream.read()
    with open_wave(candidate, 'rb') as stream:
        new = stream.read()
    return compare_prefix_bytes(old, new)

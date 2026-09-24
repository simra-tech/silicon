#!/usr/bin/env python3
"""Prepare an isolated full-chip LVS source for the physical R0.95 candidate.

The current hierarchical source combines each pair of charging segments into
one resistor. Two 55.575 um segments therefore replace each 117 um resistor
with 111.15 um. This does not adopt geometry or qualify electrical behavior.
"""
import argparse
import hashlib
import json
from pathlib import Path

SOURCE_SHA = '94e50a2a7f0646282f4499831bcfe03a2cf8871fbc33a7549b6e8f94fded207b'
HEADER = '.subckt g1_osc en trim[0] trim[1] trim[2] trim[3] osc_clk VDD VSS\n'
OLD = (
    'RRA VDD va VSS rppd w=1u l=117u b=0 m=1\n',
    'RRB VDD vb VSS rppd w=1u l=117u b=0 m=1\n',
)
NEW = tuple(line.replace('l=117u', 'l=111.15u') for line in OLD)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def rewrite_block(text):
    assert text.count(HEADER) == 1, 'Missing or ambiguous OSC interface'
    before, tail = text.split(HEADER)
    assert '\n.ends\n' in tail
    block, after = tail.split('\n.ends\n', 1)
    block += '\n'
    updated = block
    for old, new in zip(OLD, NEW):
        assert updated.count(old) == 1 and new not in updated
        updated = updated.replace(old, new)
    restored = updated
    for old, new in zip(OLD, NEW):
        restored = restored.replace(new, old)
    assert restored == block
    return before + HEADER + updated + '.ends\n' + after


def convert(data):
    assert sha(data) == SOURCE_SHA, 'Unexpected current full-chip source'
    result = rewrite_block(data.decode()).encode()
    assert result != data
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    paths = [p.resolve() for p in (args.source, args.output, args.report)]
    assert len(set(paths)) == 3
    assert not args.output.exists() and not args.report.exists()
    original = args.source.read_bytes()
    candidate = convert(original)
    with args.output.open('xb') as stream:
        stream.write(candidate)
    report = dict(
        status='prepared isolated candidate; full-chip LVS not run',
        source_sha256=SOURCE_SHA, candidate_sha256=sha(candidate),
        generator_sha256=sha(Path(__file__).read_bytes()),
        substitutions=[dict(before=a.strip(), after=b.strip()) for a, b in zip(OLD, NEW)],
        scope='Only two OSC charging resistor lengths; all other source bytes preserved',
        fullchip_geometry='not run', fullchip_lvs='not run',
        electrical_qualification='not run', production_adoption='not run')
    with args.report.open('x') as stream:
        json.dump(report, stream, indent=2)
        stream.write('\n')
    assert args.source.read_bytes() == original
    print(json.dumps(report, sort_keys=True))


if __name__ == '__main__':
    main()

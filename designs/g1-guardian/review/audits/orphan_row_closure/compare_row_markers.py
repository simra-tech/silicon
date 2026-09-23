#!/usr/bin/env python3
"""Exact main/maximal marker comparison; inherited failures are not waived."""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(folder, kind, expected_gds):
    receipt = json.loads((folder / 'summary.json').read_text())
    assert receipt['GDS_sha256'] == expected_gds
    assert receipt['inputs_rules_unchanged'] and len(receipt['decks']) == 1
    deck = receipt['decks'][0]
    assert deck['name'] == kind and deck['returncode'] == 0
    assert len(deck['reports']) == 1
    report = deck['reports'][0]
    path = folder / report['path']
    assert sha(path) == report['sha256']
    markers = collections.Counter()
    for item in ET.parse(path).findall('.//items/item'):
        markers[(item.findtext('category'), item.findtext('cell'),
                 tuple(v.text for v in item.findall('values/value')))] += 1
    assert sum(markers.values()) == report['markers']
    return receipt, markers


def rows(counter):
    return [dict(category=k[0], cell=k[1], values=k[2], count=v)
            for k, v in sorted(counter.items())]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ('baseline', 'candidate', 'output'):
        p.add_argument('--' + key, type=Path, required=True)
    p.add_argument('--deck', choices=['main', 'maximal'], required=True)
    a = p.parse_args()
    assert not a.output.exists()
    before, old = load(a.baseline, a.deck, '9940011f4061ec17815ff65f86c2448ad07145cf6a1d87645f4ab80bbb815669')
    after, new = load(a.candidate, a.deck, 'ce5a047019438c397e077be46d6550f9517c32161371712d78a6b4f21409f9d6')
    assert before['stock_rule_hashes'] == after['stock_rule_hashes']
    assert {k: v for k, v in before['switches'].items() if k != 'input'} == {
        k: v for k, v in after['switches'].items() if k != 'input'}
    added, removed = new - old, old - new
    result = dict(status='passed exact marker preservation' if not added and not removed else 'failed exact marker preservation',
                  deck=a.deck, baseline_summary_sha256=sha(a.baseline / 'summary.json'),
                  candidate_summary_sha256=sha(a.candidate / 'summary.json'), script_sha256=sha(Path(__file__)),
                  baseline_markers=sum(old.values()), candidate_markers=sum(new.values()),
                  added=rows(added), removed=rows(removed), inherited_failures=rows(old & new),
                  absolute_stock_acceptance='failed' if new else 'passed',
                  scope='Exact category/cell/value multiset and unchanged stock switches/rules; no inherited-marker waiver',
                  not_run=['other decks in this comparison', 'fullchip LVS', 'current/IR/EM/lifetime', 'electrical adoption'])
    a.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if not added and not removed else 1)


if __name__ == '__main__':
    main()

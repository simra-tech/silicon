#!/usr/bin/env python3
"""Compare native and source-oriented stock A/P with the unchanged r8 control."""
import argparse
import hashlib
import json
from pathlib import Path


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('before', 'after', 'output'):
        parser.add_argument('--'+key, type=Path, required=True)
    args = parser.parse_args(); assert not args.output.exists()
    before = json.loads(args.before.read_text()); after = json.loads(args.after.read_text())
    assert before['source_sha256'] == after['source_sha256']
    fields = ('source_line', 'source_node_actual', 'source_default',
              'native_junction_allocation', 'delta_stock_minus_source_default', 'status')
    old = {r['device']: r for r in before['rows']}
    new = {r['device']: r for r in after['rows']}
    assert len(old) == len(new) == 58 and set(old) == set(new)
    differences = [{'device': name, 'field': field, 'before': old[name][field], 'after': new[name][field]}
                   for name in sorted(old) for field in fields if old[name][field] != new[name][field]]
    counts_held = before['counts'] == after['counts'] == {'passed': 7, 'failed': 51}
    passed = not differences and counts_held and before['stock_classes'] == after['stock_classes']
    result = dict(status='passed exact source-oriented junction delta' if passed else 'failed junction delta',
                  before_sha256=sha(args.before), after_sha256=sha(args.after),
                  source_sha256=before['source_sha256'], script_sha256=sha(Path(__file__)),
                  rows=58, differences=differences, annotation_counts=after['counts'],
                  original_stock_annotation_failures='retained, not waived by strict LVS',
                  intrinsic_shared_junction_applicability='not qualified by this comparison',
                  intrinsic_gate_resistance_applicability='not qualified by this comparison')
    args.output.write_text(json.dumps(result, indent=2)+'\n'); print(json.dumps(result, indent=2))
    raise SystemExit(0 if passed else 1)


if __name__ == '__main__': main()

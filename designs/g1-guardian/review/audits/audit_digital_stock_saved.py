#!/usr/bin/env python3
"""Inspect the merged stock report and both engine logs, without re-execution."""
import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    assert not a.output.exists()
    old = json.loads((a.run/'summary.json').read_text())
    assert old['inputs_rules_held'] and len(old['checks']) == 2
    assert all(x['returncode']==0 for x in old['checks'])
    mainlog = a.run/'reports/g1_digital_g1_digital_main.log'
    maxlog = a.run/'reports/g1_digital_g1_digital_sg13g2_maximal.log'
    assert "DRC run for tables 'main' completed" in mainlog.read_text()
    assert 'DRC run for maximum ruleSet completed' in maxlog.read_text()
    console = a.run/'main_maximal.log'
    assert 'Number of DRC errors for maximum rule set: 0' in console.read_text()
    merged = a.run/'reports/g1_digital_g1_digital_full.lyrdb'
    ant = a.run/'antenna.lyrdb'
    assert list((a.run/'reports').glob('*.lyrdb')) == [merged]
    for path, check in [(merged, old['checks'][0]), (ant, old['checks'][1])]:
        assert len(check['reports']) == 1 and check['reports'][0]['sha256'] == sha(path)
        assert not ET.parse(path).findall('.//items/item')
    # Original wrapper source is frozen beside its result; the working helper
    # may now contain the repaired parser and is not substituted as evidence.
    source = a.run/'source.py'
    source_keys = [k for k in old['inputs_rules_sha256'] if k.endswith('/run_digital_stock.py')]
    assert len(source_keys) == 1 and old['inputs_rules_sha256'][source_keys[0]] == sha(source)
    paths = [a.run/'summary.json', source, mainlog, maxlog, console, merged, ant, Path(__file__)]
    result = dict(status='passed saved stock main/maximal/antenna evidence',
                  original_wrapper_status=old['status'], original_parser_failure_retained=True,
                  engine_reruns=0, checks=dict(main='passed', maximal='passed', antenna='passed'),
                  input_gds_sha256=old['input_gds_sha256'],
                  evidence_sha256={str(x):sha(x) for x in paths},
                  not_run=['Full-chip integrated density', 'Full-chip adoption'],
                  not_applicable=['Statistical seed'])
    a.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()

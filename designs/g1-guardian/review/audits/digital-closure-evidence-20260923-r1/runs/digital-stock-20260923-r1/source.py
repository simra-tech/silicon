#!/usr/bin/env python3
"""Independent unchanged stock main/max/antenna checks on a routed macro."""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
import xml.etree.ElementTree as ET
import pya


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--gds', type=Path, required=True)
    p.add_argument('--sha256', required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    assert not a.output.exists() and len(os.sched_getaffinity(0)) == 1
    pdk = Path('/foss/pdks/ihp-sg13g2')
    assert pya.__version__ == '0.30.9'
    assert (pdk/'COMMIT').read_text().strip() == '84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
    assert sha(a.gds) == a.sha256
    ly = pya.Layout(); ly.read(str(a.gds))
    top = ly.top_cell()
    assert top.name == 'g1_digital' and ly.dbu == .001
    assert top.bbox() == pya.Box(0, 0, 360000, 360000)
    drc = pdk/'libs.tech/klayout/tech/drc'
    held = {str(q):sha(q) for q in drc.rglob('*') if q.is_file()}
    held.update({str(a.gds):sha(a.gds), str(Path(__file__)):sha(Path(__file__))})
    a.output.mkdir(parents=True)
    (a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    record = dict(status='running', input_gds_sha256=a.sha256, inputs_rules_sha256=held,
                  checks=[], affinity=sorted(os.sched_getaffinity(0)),
                  not_run=['Integrated die density', 'Full-chip LVS/PEX', 'Adoption'],
                  not_applicable=['Statistical seed', 'Package-pad geometry in this macro'])
    def save():
        (a.output/'summary.json').write_text(json.dumps(record, indent=2)+'\n')
    save()
    main = ['python3', str(drc/'run_drc.py'), '--path='+str(a.gds),
            '--run_mode=deep', '--topcell=g1_digital', '--no_density', '--mp=1',
            '--run_dir='+str(a.output/'reports')]
    ant = ['klayout', '-b', '-zz', '-r', str(drc/'rule_decks/antenna.drc'),
           '-rd', 'input='+str(a.gds), '-rd', 'topcell=g1_digital',
           '-rd', 'report='+str(a.output/'antenna.lyrdb'), '-rd', 'threads=1']
    for name, command in [('main_maximal', main), ('antenna', ant)]:
        started = time.monotonic()
        command = ['timeout', '--kill-after=5', '600']+command
        with (a.output/(name+'.log')).open('x') as log:
            child = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
        files = sorted((a.output/'reports').rglob('*.lyrdb')) if name == 'main_maximal' else [a.output/'antenna.lyrdb']
        reports = []
        for path in files:
            if not path.exists(): continue
            counts = Counter(i.findtext('category') for i in ET.parse(path).findall('.//items/item'))
            reports.append(dict(file=str(path.relative_to(a.output)), sha256=sha(path),
                                markers=sum(counts.values()), categories=dict(counts)))
        complete = len(reports) == (2 if name == 'main_maximal' else 1)
        if name == 'main_maximal':
            logs = '\n'.join(q.read_text(errors='replace') for q in (a.output/'reports').rglob('*.log'))
            complete = complete and "DRC run for tables 'main' completed" in logs and 'DRC run for maximum ruleSet completed' in logs
        record['checks'].append(dict(name=name, command=command, returncode=child.returncode,
                                     wall_s=time.monotonic()-started, reports=reports,
                                     status='passed' if child.returncode == 0 and complete and all(x['markers']==0 for x in reports) else 'failed'))
        save()
    record['inputs_rules_held'] = all(sha(Path(q)) == h for q,h in held.items())
    passed = record['inputs_rules_held'] and all(x['status']=='passed' for x in record['checks'])
    record['status'] = 'passed scoped stock main/maximal/antenna' if passed else 'failed scoped stock checks'
    save()
    raise SystemExit(0 if passed else 1)


if __name__ == '__main__':
    main()

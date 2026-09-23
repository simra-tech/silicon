#!/usr/bin/env python3
"""Stock density or antenna check on an exact assembled die, with boundary proof."""
import argparse
import collections
import json
import os
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET
import pya
from place_closed_analog import region, sha

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT/'designs/g1-guardian/blocks/g1_top/sim'))
from run_bounded import run_bounded
PDK = Path('/foss/pdks/ihp-sg13g2')
PIN = '84374023ee8b4b126bebbba67fcbada0a9c0ff0b'


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--candidate', type=Path, required=True)
    p.add_argument('--gds-name', required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--check', choices=['density', 'antenna'], required=True)
    p.add_argument('--watchdog', type=int, default=900)
    a = p.parse_args()
    assert not a.output.exists() and 60 <= a.watchdog <= 1800
    assert Path(a.gds_name).name == a.gds_name and len(os.sched_getaffinity(0)) == 1
    assert pya.__version__ == '0.30.9' and (PDK/'COMMIT').read_text().strip() == PIN
    source = a.candidate/a.gds_name; meta = json.loads((a.candidate/'analysis.json').read_text())
    assert meta['status'].startswith('passed') and sha(source) == meta['GDS_sha256']
    ly = pya.Layout(); ly.read(str(source)); top = ly.top_cell()
    die = pya.Region(pya.Box(0, 0, 1414000, 1414000))
    assert top.bbox() == die.bbox() and ly.dbu == .001
    assert region(ly, top, pya.LayerInfo(189, 0)).is_empty()
    boundary = region(ly, top, pya.LayerInfo(39, 4))
    assert boundary.count() == 1 and (boundary^die).is_empty()
    drc = PDK/'libs.tech/klayout/tech/drc'
    rules = {str(q.relative_to(drc)): sha(q) for q in drc.rglob('*') if q.is_file()}
    a.output.mkdir(parents=True); (a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    report = a.output/(a.check+'.lyrdb')
    command = ['klayout', '-b', '-zz', '-r', str(drc/'rule_decks'/(a.check+'.drc')),
               '-rd', 'input='+str(source), '-rd', 'topcell='+top.name,
               '-rd', 'report='+str(report), '-rd', 'threads=1']
    if a.check == 'density': command += ['-rd', 'density_sanity=true']
    result = dict(status='running', check=a.check, command=command, GDS_sha256=sha(source),
        candidate_metadata_sha256=sha(a.candidate/'analysis.json'), script_sha256=sha(Path(__file__)),
        PDK_commit=PIN, KLayout=subprocess.check_output(['klayout', '-v'], text=True).strip(),
        stock_rule_hashes=rules, density_boundary_area_um2=1999396,
        density_boundary='single native EdgeSeal.boundary; prBoundary absent',
        not_run=['other stock decks in this invocation', 'complete LVS/PEX/currentIR/EM', 'electrical adoption'])
    receipt = a.output/'summary.json'; receipt.write_text(json.dumps(result, indent=2)+'\n')
    with (a.output/'tool.log').open('x') as stream:
        state = run_bounded(command, stream, a.output/'run.json', a.watchdog, cwd=ROOT,
            env=dict(os.environ, OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1'), interval_s=1)
    unchanged = sha(source) == result['GDS_sha256'] and all(sha(drc/q) == value for q, value in rules.items())
    result.update(status='failed', runtime=state, inputs_rules_unchanged=unchanged,
                  completed_rule_result='not run')
    if state['status'] == 'completed' and state['returncode'] == 0 and report.is_file():
        cats = collections.Counter(i.findtext('category').strip("'") for i in ET.parse(report).findall('.//items/item'))
        result.update(markers=sum(cats.values()), categories=dict(cats), report_sha256=sha(report))
        boundary_log_ok = True
        if a.check == 'density':
            log = (a.output/'tool.log').read_text()
            boundary_log_ok = 'Using EdgeSeal.boundary (39/4) for chip area: 1999396' in log
        result.update(boundary_log_consistent=boundary_log_ok,
            completed_rule_result='passed' if not cats else 'failed',
            status='passed' if not cats and unchanged and boundary_log_ok else 'failed')
    receipt.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'stock_rule_hashes'}, indent=2))
    raise SystemExit(0 if result['status'] == 'passed' else 1)


if __name__ == '__main__':
    main()

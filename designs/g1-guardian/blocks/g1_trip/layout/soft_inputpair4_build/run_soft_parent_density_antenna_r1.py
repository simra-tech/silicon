"""Unmodified pinned-rule density/antenna checks of exact folded-parent GDS."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from inspect_soft_inputpair4_parent_r1 import ROOT, sha

sys.path.insert(0, str(ROOT / 'designs/g1-guardian/review/audits/io_tap_closure/physical_source/integration_purefill'))
import current_rz_bindings as prior
import current_rz_stock_preconditions as pre

CANDIDATE = Path(os.environ['G1_RESULTS_ROOT'])/'soft-inputpair4-parent-20260924-r3'
GDS_SHA = '60730627d24e1fb6b880138edc3e50fdd7c14624bb2dfbbc631e084b7415eca1'


def command(mode, pdk, run, top):
    assert mode in ('density', 'antenna')
    return ['python3', str(pdk / 'libs.tech/klayout/tech/drc/run_drc.py'),
            '--path=' + str(CANDIDATE / 'candidate.gds'), '--topcell=' + top,
            '--run_mode=deep', '--density_thr=1', '--' + mode + '_only',
            '--run_dir=' + str(run)] + (['--antenna'] if mode == 'antenna' else [])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['density', 'antenna'], required=True)
    args = parser.parse_args()
    assert os.sched_getaffinity(0) == {14}
    preparation = json.loads((CANDIDATE / 'preparation.json').read_text())
    assert sha(CANDIDATE / 'candidate.gds') == preparation['candidate_sha256'] == GDS_SHA
    assert sha(CANDIDATE / 'candidate.cdl') == preparation['candidate_reference_sha256']
    pdk = Path('/foss/pdks/ihp-sg13g2')
    assert (pdk / 'COMMIT').read_text().strip() == '84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
    expected = json.loads(prior.bound(prior.PHYSICAL['main']).read_text())['stock_rule_hashes']
    def held():
        return pre.require_rules(pre.rule_files(expected), pre.rule_files(pre.rule_tree(pdk, 'libs.tech/klayout/tech')))
    assert held()
    bindings = {str(p): sha(p) for p in [CANDIDATE / 'preparation.json', CANDIDATE / 'candidate.gds', CANDIDATE / 'candidate.cdl', Path(__file__)]}
    out = CANDIDATE / (args.mode + '_cpu14_r1')
    out.mkdir(exist_ok=False)
    cmd = command(args.mode, pdk, out / 'reports', preparation['top'])
    log = out / 'engine.log'
    start = time.monotonic()
    with log.open('x') as stream:
        rc = subprocess.run(['timeout', '--kill-after=5s', '900s'] + cmd,
                            stdout=stream, stderr=subprocess.STDOUT).returncode
    reports = list((out / 'reports').glob('*.lyrdb'))
    markers = len(ET.parse(reports[0]).findall('.//items/item')) if len(reports) == 1 else None
    inputs_held = all(sha(Path(name)) == digest for name, digest in bindings.items())
    rules_held = held()
    passed = rc == 0 and markers == 0 and inputs_held and rules_held
    result = dict(status='passed' if passed else 'failed', check=args.mode, returncode=rc,
                  markers=markers, wall_s=time.monotonic() - start, command=cmd,
                  inputs_sha256=bindings, inputs_held=inputs_held, stock_rules_held=rules_held,
                  log_sha256=sha(log), reports_sha256={p.name: sha(p) for p in reports},
                  klayout_version=subprocess.check_output(['klayout', '-v'], universal_newlines=True).strip(),
                  pdk_commit=(pdk / 'COMMIT').read_text().strip(),
                  electrical_acceptance='not run', final_integrated_acceptance='not run')
    with (out / 'summary.json').open('x') as stream:
        json.dump(result, stream, indent=2)
    print(json.dumps(result))
    raise SystemExit(0 if passed else 1)


if __name__ == '__main__':
    main()

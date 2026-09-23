#!/usr/bin/env python3
"""One bounded native fullchip LVS run, unchanged source reference and rules."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import traceback
import pya

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
sys.path.insert(0, str(ROOT / 'designs/g1-guardian/blocks/g1_top/sim'))
from run_bounded import run_bounded

PDK = Path('/foss/pdks/ihp-sg13g2')
REFERENCE = HERE.parent / 'name_interface/evidence/prepared/g1_chip_top_layout_name_only.cdl'
TOP = 'placed_core_NOT_CONNECTED_FULLCHIP'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path, data):
    path.write_text(json.dumps(data, indent=2, allow_nan=False) + '\n')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--layout', type=Path, required=True)
    p.add_argument('--layout-sha256', required=True)
    p.add_argument('--candidate-analysis', type=Path, required=True)
    p.add_argument('--resource-gate', type=Path, required=True)
    p.add_argument('--minimum-global-cpus', type=int, default=43)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    assert not a.output.exists()
    a.output.mkdir(parents=True)
    (a.output / 'runner_snapshot.py').write_bytes(Path(__file__).read_bytes())
    parser = HERE / 'inspect_stock_result.py'
    (a.output / 'parser_snapshot.py').write_bytes(parser.read_bytes())
    result = dict(status='running preflight', physical_extraction='not run', fullchip_LVS='not run')
    passed = False
    try:
        assert len(os.sched_getaffinity(0)) == 1 and pya.__version__ == '0.30.9'
        gate = json.loads(a.resource_gate.read_text())
        age = (datetime.datetime.now(datetime.timezone.utc) - datetime.datetime.fromisoformat(gate['utc'])).total_seconds()
        assert gate['status'] == 'passed' and 0 <= age < 1800 and gate['project_cpu_budget'] >= a.minimum_global_cpus
        assert (PDK / 'COMMIT').read_text().strip() == '84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
        assert sha(REFERENCE) == 'f4ce6848bd7dd179d2ef4cbd8a4ea6bf9788bcfa1ff4b93fabae8bf18b6378f9'
        assert sha(a.layout) == a.layout_sha256
        candidate = json.loads(a.candidate_analysis.read_text())
        assert candidate['status'].startswith('passed') and candidate['GDS_sha256'] == a.layout_sha256
        layout = pya.Layout()
        layout.read(str(a.layout))
        assert layout.cell(TOP) is not None and layout.dbu == .001
        header, = re.findall(r'^\.SUBCKT ' + TOP + r' ([^\n]+)$', REFERENCE.read_text(), re.M)
        pins = header.split()
        assert len(pins) == len(set(pins)) == 22
        dump(a.output / 'expected_source_pins.json', pins)
        rules = {str(path.relative_to(PDK)): sha(path) for path in (PDK / 'libs.tech/klayout/tech/lvs').rglob('*') if path.is_file()}
        inputs = {str(path): sha(path) for path in (a.layout, a.candidate_analysis, REFERENCE, Path(__file__), parser)}
        command = ['python3', str(PDK / 'libs.tech/klayout/tech/lvs/run_lvs.py'),
                   '--layout', str(a.layout.resolve()), '--netlist', str(REFERENCE.resolve()), '--topcell', TOP,
                   '--run_mode', 'deep', '--top_lvl_pins', '--spice_comments', '--run_dir', str((a.output / 'reports').resolve())]
        result.update(status='running native extraction and strict comparison', inputs=inputs, stock_rule_hashes=rules,
                      resource_gate_sha256=sha(a.resource_gate), source_top_pins=pins, command=command,
                      watchdog_seconds=900, kill_grace_seconds=5, analysis_watchdog_seconds=120,
                      reservation_GiB=16, memory_enforced=False, expected_external_growth_GiB=2,
                      known_prior_failure='IO tap source/native A/P mismatch retained; no reference tailoring',
                      not_run=['new physical PEX', 'electrical adoption', 'model applicability qualification'], seed='not applicable')
        dump(a.output / 'summary.json', result)
        with (a.output / 'stock_console.log').open('x') as log:
            run = run_bounded(command, log, a.output / 'run.json', 900, cwd=ROOT,
                              env=dict(os.environ, KLAYOUT_PATH=str(PDK / 'libs.tech/klayout')), interval_s=5)
        result.update(run=run, physical_extraction='attempted; see actual engine report', fullchip_LVS='failed or incomplete until independent report passes')
        dump(a.output / 'summary.json', result)
        analysis_command = ['python3', str(parser), '--reports', str(a.output / 'reports'),
                            '--returncode', str(run['returncode']), '--top', TOP,
                            '--pins-json', str(a.output / 'expected_source_pins.json'), '--output', str(a.output / 'strict_analysis.json')]
        with (a.output / 'analysis.log').open('x') as log:
            check = run_bounded(analysis_command, log, a.output / 'analysis_run.json', 120, cwd=ROOT, interval_s=5)
        result['analysis_run'] = check
        parsed = json.loads((a.output / 'strict_analysis.json').read_text()) if (a.output / 'strict_analysis.json').exists() else None
        result['strict_analysis'] = {k: v for k, v in parsed.items() if k != 'database'} if parsed else None
        unchanged = all(sha(Path(path)) == expected for path, expected in inputs.items()) and all(sha(PDK / path) == expected for path, expected in rules.items())
        result['inputs_rules_unchanged'] = unchanged
        result['output_bytes'] = sum(path.stat().st_size for path in a.output.rglob('*') if path.is_file())
        bounded = result['output_bytes'] < 2 * 1024**3
        passed = run['status'] == 'completed' and check['status'] == 'completed' and parsed is not None and parsed['status'].startswith('passed') and unchanged and bounded
        result.update(status='passed strict fullchip stock comparison' if passed else 'failed strict fullchip stock comparison',
                      fullchip_LVS='passed' if passed else 'failed', output_growth_gate='passed' if bounded else 'failed')
    except BaseException as exc:
        result.update(status='failed preflight or analysis', exception=repr(exc), traceback=traceback.format_exc())
    finally:
        dump(a.output / 'summary.json', result)
        print(json.dumps({k: v for k, v in result.items() if k not in ('inputs', 'stock_rule_hashes')}, indent=2))
    raise SystemExit(0 if passed else 1)


if __name__ == '__main__':
    main()

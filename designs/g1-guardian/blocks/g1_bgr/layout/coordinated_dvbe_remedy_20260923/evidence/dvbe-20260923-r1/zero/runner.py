#!/usr/bin/env python3
"""One bounded frozen OP leaf; conditional metal sensitivity, not qualification."""
import argparse
import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import numpy as np

HERE = Path(__file__).resolve().parent
QUAL = HERE.parents[1] / 'sim/qualification'
sys.path.insert(0, str(HERE.parents[2] / 'g1_top/sim'))
from run_bounded import run_bounded


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def dump(p, value):
    p.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def printed_section(log, marker):
    section, = re.findall(r'^' + marker + r'_BEGIN\n(.*?)^' + marker + r'_END$', log, re.M | re.S)
    pairs = re.findall(r'^([^=\n]+?)\s*=\s*(\S+)\s*$', section, re.M)
    pairs = [[k.strip(), v] for k, v in pairs]
    assert all(math.isfinite(float(v)) for k, v in pairs)
    return section, pairs


def main():
    ap = argparse.ArgumentParser()
    for name in ('prepared', 'output', 'resource-gate'):
        ap.add_argument('--' + name, type=Path, required=True)
    ap.add_argument('--case', choices=('zero', 'kpex', 'lef'), required=True)
    ap.add_argument('--zero-control', type=Path)
    ap.add_argument('--image-id', required=True)
    ap.add_argument('--cpu', type=int, choices=(0,), default=0)
    a = ap.parse_args()
    a.output.mkdir(exist_ok=False)
    (a.output / 'runner.py').write_bytes(Path(__file__).read_bytes())
    summary = dict(status='running preflight', simulation='not run', case=a.case,
                   adoption='not run', physical_IR='not qualified', no_double_count='unresolved')
    dump(a.output / 'summary.json', summary)
    try:
        assert os.sched_getaffinity(0) == {a.cpu}
        gate = json.loads(a.resource_gate.read_text())
        age = (datetime.datetime.now(datetime.timezone.utc) - datetime.datetime.fromisoformat(gate['utc'])).total_seconds()
        assert gate['status'] == 'passed' and 0 <= age < 1800
        assert gate['project_cpu_budget'] >= 43 and gate['ram_available_bytes'] >= 8 * 2**30
        prep = json.loads((a.prepared / 'summary.json').read_text())
        audit = json.loads((a.prepared / 'independent_source_audit.json').read_text())
        assert prep['status'] == 'passed conditional source preparation' and audit['status'] == 'passed'
        assert all(sha(Path(p)) == h for p, h in prep['inputs'].items())
        scenario = next(s for s in prep['scenarios'] if s['scenario'].lower() == ('kpex' if a.case == 'zero' else a.case))
        assert all(sha(Path(p)) == h for p, h in scenario['inputs'].items())
        folder = a.prepared / ('kpex' if a.case == 'zero' else a.case)
        assert all(sha(folder / n) == h for n, h in scenario['outputs'].items())
        base = QUAL / 'runs/bgr_one_draw_20260922_r1'
        qm = json.loads((base / 'manifest.json').read_text())
        reference = QUAL / 'runs/bgr586-raw-current-ledger-20260922-a'
        ref, = json.loads((reference / 'summary.json').read_text())
        assert ref['status'].startswith('passed') and ref['full2842_before_after_original_exact']
        assert a.image_id == qm['runtime']['image_id']
        pd = Path('/foss/pdks/ihp-sg13g2')
        assert (pd / 'COMMIT').read_text().strip() == qm['runtime']['pdk_commit']
        assert subprocess.check_output(['ngspice', '--version'], text=True) == qm['ngspice']
        for key, directory, pattern in [('model_sha256', 'models', '*.lib'), ('osdi_sha256', 'osdi', '*.osdi')]:
            assert qm['runtime'][key] == {str(f.relative_to(pd)): sha(f) for f in sorted((pd / 'libs.tech/ngspice' / directory).glob(pattern))}
        init = base / 'disabled/.spiceinit'
        assert sha(init) == qm['init_sha256']
        if a.case != 'zero':
            assert a.zero_control is not None
            control = json.loads((a.zero_control / 'summary.json').read_text())
            assert control['status'] == 'passed exact-zero OP control'
            assert control['case'] == 'zero' and control['original_OP_bytes_exact']
            assert control['all2842_parameters_exact'] and control['all3885_raw_fields_exact']
            assert control['preparation_sha256'] == sha(a.prepared / 'summary.json')
        inputs = [a.prepared / 'summary.json', a.prepared / 'independent_source_audit.json',
                  base / 'manifest.json', reference / 'summary.json', reference / 'op_nodes.dat',
                  init, a.resource_gate, Path(__file__), HERE.parents[5] / 'flow/run.sh',
                  HERE.parents[2] / 'g1_top/sim/run_bounded.py']
        inputs.extend(folder / n for n in scenario['outputs'])
        if a.zero_control is not None:
            inputs.append(a.zero_control / 'summary.json')
        deck_name, source_name = ('zero_r.cir', 'zero_r_original.spice') if a.case == 'zero' else ('nominal.cir', 'conditional_metal.spice')
        for name in (deck_name, source_name):
            (a.output / name).write_bytes((folder / name).read_bytes())
        (a.output / '.spiceinit').write_bytes(init.read_bytes())
        frozen = {str(p): sha(p) for p in inputs}
        provenance = dict(inputs=frozen, runtime=qm['runtime'], ngspice=qm['ngspice'],
                          source_sha256=sha(a.output / source_name), deck_sha256=sha(a.output / deck_name),
                          thread_count=1, CPU=a.cpu, memory_reservation_only_GiB=8,
                          watchdog_s=120 if a.case == 'zero' else 600, kill_grace_s=5,
                          assumptions=['HBT E native M2-pin attachment; all other original points held; calibration boundary unresolved',
                                       '399 resistor BN ideal global VSS', 'Lumped body guard points',
                                       'Historical capacitor node attachment unqualified; DC only'])
        dump(a.output / 'provenance.json', provenance)
        with (a.output / 'run.log').open('x') as stream:
            state = run_bounded(['ngspice', '-b', deck_name], stream, a.output / 'run.json',
                                provenance['watchdog_s'], cwd=a.output, interval_s=1)
        log = (a.output / 'run.log').read_text()
        errors = [l for l in log.splitlines() if re.search(r'(?i)(^error|no such vector|no such parameter|analysis aborted|timestep too small|doAnalyses:|not available)', l)]
        warnings = [l for l in log.splitlines() if re.search(r'(?i)(warning|gmin|converg|singular)', l)]
        summary.update(simulation='completed' if state['status'] == 'completed' else 'not run to completion',
                       runtime=state, errors=errors, warnings=warnings,
                       preparation_sha256=sha(a.prepared / 'summary.json'))
        assert all(sha(Path(p)) == h for p, h in frozen.items())
        assert state['status'] == 'completed' and state['returncode'] == 0 and not errors
        raw_section, raw = printed_section(log, 'RAW_CURRENT_LEDGER')
        remaining = log.replace(raw_section, '')
        parameters = [list(p) for p in re.findall(r'^(@[^\s]+)\s*=\s*(\S+)', remaining, re.M)]
        assert len(parameters) == 2842 and [p[0] for p in parameters] == qm['parameters']
        assert parameters == ref['parameter_before']
        assert len(raw) == 3885 and [p[0] for p in raw] == [p[0] for p in ref['raw_fields']]
        op_data = np.loadtxt(str(a.output / 'op_nodes.dat'), skiprows=1, ndmin=2)
        assert op_data.shape == (1, 60) and np.isfinite(op_data).all()
        summary.update(all2842_parameters_exact=True, original_OP_bytes_exact=(a.output / 'op_nodes.dat').read_bytes() == (reference / 'op_nodes.dat').read_bytes(),
                       all3885_raw_fields_exact=raw == ref['raw_fields'], raw_fields=raw,
                       parameter_before=parameters, op_node_values=op_data[0].tolist(), post_DC_parameters='not run')
        if a.case == 'zero':
            assert summary['original_OP_bytes_exact'] and summary['all3885_raw_fields_exact']
            summary['status'] = 'passed exact-zero OP control'
        else:
            point_section, point_values = printed_section(log, 'METALLIC_POINT_VOLTAGES')
            node_section, node_values = printed_section(log, 'METALLIC_ALL_NODE_VOLTAGES')
            expected = json.loads((folder / 'observed_nodes.json').read_text())
            point_map = json.loads((folder / 'point_nodes.json').read_text())
            assert len(point_values) == len(point_map) == 3355
            assert len(node_values) == len(expected) == scenario['contracted_node_count']
            assert [p[0] for p in node_values] == [p['expression'] for p in expected]
            voltage = {p['node']: float(value[1]) for p, value in zip(expected, node_values)}
            assert all(float(v[1]) == voltage[p['node']] for p, v in zip(point_map, point_values))
            dump(a.output / 'metal_node_voltages.json', voltage)
            summary.update(status='passed conditional nonlinear OP completion and source controls',
                           finite_point_count=len(point_values), finite_node_count=len(node_values),
                           terminal_current_attribution='analysis pending; resistor BN coverage unqualified',
                           metal_KCL='analysis pending', electrical_acceptance='not qualified')
    except Exception as error:
        summary.update(status='failed', error=repr(error))
        raise
    finally:
        dump(a.output / 'summary.json', summary)
        print(json.dumps({k: v for k, v in summary.items() if k not in ('raw_fields', 'parameter_before', 'op_node_values')}, indent=2))


if __name__ == '__main__':
    main()

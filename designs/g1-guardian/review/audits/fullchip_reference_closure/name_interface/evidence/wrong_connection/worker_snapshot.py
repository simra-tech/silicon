#!/usr/bin/env python3
"""Bounded stock layout-netlist alignment control; no physical extraction."""
import argparse
from collections import Counter
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
import pya

PDK = Path('/foss/pdks/ihp-sg13g2')


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def dump(p, d):
    p.write_text(json.dumps(d, indent=2) + '\n')


def value(obj, name):
    result = getattr(obj, name)
    return result() if callable(result) else result


def inventory(netlist):
    rows = {}
    for circuit in netlist.each_circuit():
        children = [value(sub, 'circuit_ref').name for sub in circuit.each_subcircuit()]
        children = [c() if callable(c) else c for c in children]
        rows[value(circuit, 'name')] = dict(devices=sum(1 for _ in circuit.each_device()),
                                            pins=[value(p, 'name') for p in circuit.each_pin()], children=children)
    def total(name, trail=()):
        assert name not in trail
        return rows[name]['devices'] + sum(total(child, trail + (name,)) for child in rows[name]['children'])
    for name in rows:
        rows[name]['expanded_devices'] = total(name)
    return rows


def strict(path):
    db = pya.LayoutVsSchematic()
    db.read(str(path))
    xr = db.xref()
    X = pya.NetlistCrossReference
    names = {X.Match: 'Match', X.MatchWithWarning: 'MatchWithWarning', X.Mismatch: 'Mismatch',
             X.NoMatch: 'NoMatch', X.Skipped: 'Skipped', X.None_: 'None'}
    rows = []
    for pair in xr.each_circuit_pair():
        row = dict(status=names[pair.status()], children={})
        for kind, method in [('device', xr.each_device_pair), ('net', xr.each_net_pair),
                             ('pin', xr.each_pin_pair), ('subcircuit', xr.each_subcircuit_pair)]:
            row['children'][kind] = dict(Counter(names[p.status()] for p in method(pair)))
        rows.append(row)
    passed = bool(rows) and all(r['status'] == 'Match' and all(set(v) <= {'Match'} for v in r['children'].values()) for r in rows)
    return dict(status='passed' if passed else 'failed', circuits=rows,
                layout=inventory(value(db, 'netlist')), reference=inventory(value(db, 'reference')), sha256=sha(path))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--prepared', type=Path, required=True)
    ap.add_argument('--case', required=True)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--resource-gate', type=Path, required=True)
    a = ap.parse_args()
    assert not a.output.exists() and len(os.sched_getaffinity(0)) == 1
    gate = json.loads(a.resource_gate.read_text())
    age = (datetime.datetime.now(datetime.timezone.utc) - datetime.datetime.fromisoformat(gate['utc'])).total_seconds()
    assert gate['status'] == 'passed' and 0 <= age < 1800
    assert pya.__version__ == '0.30.9'
    assert (PDK / 'COMMIT').read_text().strip() == '84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
    prep = json.loads((a.prepared / 'summary.json').read_text())
    case, = [r for r in prep['cases'] if r['name'] == a.case]
    reference = a.prepared / 'control_reference.cdl'
    layout = a.prepared / case['layout_netlist']
    assert sha(reference) == prep['control_reference_sha256'] and sha(layout) == case['sha256']
    a.output.mkdir(parents=True)
    (a.output / 'worker_snapshot.py').write_bytes(Path(__file__).read_bytes())
    bindings = {str(p.relative_to(PDK)): sha(p) for p in (PDK / 'libs.tech/klayout/tech/lvs').rglob('*')
                if p.is_file() and p.suffix in ('.lvs', '.py', '.rb', '.json')}
    command = ['python3', str(PDK / 'libs.tech/klayout/tech/lvs/run_lvs.py'),
               '--layout_netlist=' + str(layout), '--netlist=' + str(reference),
               '--topcell=' + case['top'], '--run_mode=deep', '--run_dir=' + str(a.output / 'reports')]
    result = dict(status='running stock name-control', case=case, command=command, stock_rule_hashes=bindings,
                  resource_gate_sha256=sha(a.resource_gate), prepared_sha256=sha(a.prepared / 'summary.json'),
                  physical_extraction='not run', fullchip_LVS='not run', seed='not applicable',
                  watchdog_seconds=180, kill_grace_seconds=5, script_sha256=sha(Path(__file__)))
    dump(a.output / 'summary.json', result)
    start = time.monotonic()
    with (a.output / 'stock.log').open('x') as log:
        run = subprocess.run(['timeout', '--kill-after=5', '180'] + command, stdout=log, stderr=subprocess.STDOUT)
    result.update(returncode=run.returncode, wall_seconds=time.monotonic() - start)
    passed = False
    try:
        reports = [strict(p) for p in (a.output / 'reports').rglob('*.lvsdb')]
        logs = '\n'.join(p.read_text(errors='replace') for p in (a.output / 'reports').rglob('*.log'))
        assert len(reports) == 1 and reports[0]['circuits']
        result['strict_report'] = reports[0]
        positive = 'Congratulations! Netlists match.' in logs and "Netlists don't match" not in logs
        negative = "Netlists don't match" in logs and 'Congratulations! Netlists match.' not in logs
        assert positive != negative
        actual = positive and reports[0]['status'] == 'passed'
        assert positive == actual, 'Log success with incomplete strict match'
        assert run.returncode not in (124, 137)
        assert all(sha(PDK / name) == h for name, h in bindings.items())
        assert sha(reference) == prep['control_reference_sha256'] and sha(layout) == case['sha256']
        result.update(explicit_match=positive, explicit_mismatch=negative, actual_strict_match=actual,
                      input_rules_unchanged=True)
        # Every positive must retain the full four-device expanded circuit on
        # both sides; child alias control must expose four direct top devices.
        if case['expected_match'] is True:
            for side in ('layout', 'reference'):
                assert reports[0][side]['NAME_CONTROL_TOP']['expanded_devices'] == 4
                assert len(reports[0][side]['NAME_CONTROL_TOP']['pins']) == 4
                if a.case == 'child_alias':
                    assert reports[0][side]['NAME_CONTROL_TOP']['devices'] == 4
                    assert not reports[0][side]['NAME_CONTROL_TOP']['children']
            passed = actual and run.returncode == 0
        elif case['expected_match'] is False:
            assert any(v['expanded_devices'] > 0 for v in reports[0]['layout'].values())
            assert any(v['expanded_devices'] > 0 for v in reports[0]['reference'].values())
            passed = not actual and negative
        else:
            passed = True  # observation, not a pre-assumed top-pairing result
        result['status'] = ('passed stock-control expectation' if passed else 'failed stock-control expectation') if case['expected_match'] is not None else 'completed top-name behavior observation'
    except Exception as exc:
        result.update(status='failed stock-control parsing or preservation', exception_type=type(exc).__name__, detail=str(exc))
    result['output_bytes'] = sum(p.stat().st_size for p in a.output.rglob('*') if p.is_file())
    assert result['output_bytes'] < .05 * 1024**3
    dump(a.output / 'summary.json', result)
    print(json.dumps({k: v for k, v in result.items() if k != 'stock_rule_hashes'}, indent=2))
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())

#!/usr/bin/env python3
"""Small exact-geometry union experiment: strict LVS then unpruned CC parity."""
import argparse
import collections
import datetime
from decimal import Decimal
import json
import os
from pathlib import Path
import re
import subprocess
import time

import pya

from audit_unsimplified import sha
from prepare_capacitance_views import logical_lines, number
from run_pex_prepare import HERE, ROOT, SUPPORT
from run_stock import strict


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--run-id', required=True)
    ap.add_argument('--resource-gate', type=Path, required=True)
    args = ap.parse_args()
    assert re.fullmatch('bgr-union-pilot-[a-z0-9-]+', args.run_id)
    assert len(os.sched_getaffinity(0)) == 1 and next(iter(os.sched_getaffinity(0))) in range(4)
    gate = json.loads(args.resource_gate.read_text())
    age = (datetime.datetime.now(datetime.timezone.utc) - datetime.datetime.fromisoformat(gate['utc'])).total_seconds()
    assert gate['status'] == 'passed' and 0 <= age < 1800
    bulk = Path(os.environ['G1_RESULTS_ROOT'])
    assert str(bulk) == gate['external_allocation']['root'] and gate['external_allocation']['expected_growth_gib'] >= 2
    geometry = bulk / 'bgr-union-pilot-geometry-20260922-r1'
    preparation = json.loads((geometry / 'summary.json').read_text())
    assert preparation['status'] == 'passed exact-union preparation' and preparation['all_text_exact']
    assert all(row['xor_polygons'] == 0 for row in preparation['layers'])
    cdl = ROOT / 'build/scratch/bgr-hbt-worstrows-20260922-r2/pilot.cdl'
    assert sha(cdl) == '8aeac3748ccc6c00a6804bb75e63f07332a67acf64b27daf6cac71f8e3990e72'
    wrapper = ROOT / 'flow/pex/export_lvsdb.lvs'
    out = bulk / args.run_id
    out.mkdir(exist_ok=False)
    files = [geometry / 'summary.json', geometry / 'flat.gds', geometry / 'union.gds', cdl, wrapper, Path(__file__),
             HERE / 'prepare_capacitance_views.py', HERE / 'run_stock.py']
    inputs = {str(path): sha(path) for path in files}
    support = {str(path.relative_to(SUPPORT)): sha(path) for path in SUPPORT.rglob('*') if path.is_file()}
    for path in files[3:]:
        (out / path.name).write_bytes(path.read_bytes())
    receipt = {'status': 'running', 'inputs': inputs, 'support_hashes': support, 'steps': [], 'variants': {},
               'resource_gate_sha256': sha(args.resource_gate), 'scope': '34HBT fixedgeometry representation control, not fullBGR extraction',
               'prospective_cc_parity': 'Exact mapped capacitor multiset and exact unpruned netpair matrix; no tolerance or pruning.',
               'wire_R_electrical': 'not run', 'seed': 'not applicable'}
    def save():
        (out / 'summary.json').write_text(json.dumps(receipt, indent=2) + '\n')
    save()
    begin = time.monotonic()
    def step(name, cmd, limit):
        start = time.monotonic()
        with (out / (name + '.log')).open('x') as log:
            result = subprocess.run(['timeout', '--kill-after=5', str(limit)] + cmd, stdout=log, stderr=subprocess.STDOUT)
        receipt['steps'].append({'name': name, 'command': cmd, 'watchdog_s': limit, 'returncode': result.returncode, 'wall_s': time.monotonic() - start})
        save()
        assert result.returncode == 0, (name, result.returncode)
    try:
        for variant in ('flat', 'union'):
            assert sha(geometry / (variant + '.gds')) == preparation[variant + '_sha256']
            db_path = out / (variant + '.lvsdb')
            cmd = ['klayout', '-b', '-r', str(wrapper)]
            for arg in ['input=' + str(geometry / (variant + '.gds')), 'topcell=bgr_hbt_worstrows', 'schematic=' + str(cdl),
                        'report=' + str(db_path), 'export_netlist=' + str(out / (variant + '.cir')),
                        'target_netlist=' + str(out / (variant + '_stock.cir')), 'log=' + str(out / (variant + '_detail.log')),
                        'thr=1', 'run_mode=deep', 'no_simplify=true', 'combine_devices=false', 'purge=false',
                        'purge_nets=false', 'top_lvl_pins=true', 'no_series_res=true', 'no_parallel_res=true']:
                cmd += ['-rd', arg]
            step(variant + '_lvs', cmd, 180)
            log = (out / (variant + '_lvs.log')).read_text()
            assert 'Congratulations! Netlists match.' in log and "Netlists don't match" not in log
            status = strict(db_path)
            assert status['status'] == 'passed'
            children = status['circuits'][0]['children']
            assert children['device'] == {'Match': 34} and children['net'] == {'Match': 6} and children['pin'] == {'Match': 6}
            db = pya.LayoutVsSchematic()
            db.read(str(db_path))
            xref = db.xref()
            circuit = next(xref.each_circuit_pair())
            mapping = {pair.first().name: pair.second().name.lower() for pair in xref.each_net_pair(circuit)}
            mapping['VSUBS'] = 'VSUBS'  # retain global substrate as distinct for full unpruned parity
            records = []
            for pair in xref.each_device_pair(circuit):
                layout_device, source_device = pair.first(), pair.second()
                cls = layout_device.device_class()
                assert cls.name.lower() == source_device.device_class().name.lower() == 'npn13g2'
                parameters = {p.name: layout_device.parameter(p.name) for p in cls.parameter_definitions()}
                assert all(abs(value - source_device.parameter(key)) < 1e-12 for key, value in parameters.items())
                nodes = {term.name: mapping[layout_device.net_for_terminal(term.name).name] for term in cls.terminal_definitions()}
                assert all(node == source_device.net_for_terminal(term).name.lower() for term, node in nodes.items())
                records.append({'reference_name': source_device.name, 'parameters': parameters, 'nodes': nodes})
            receipt['variants'][variant] = {'strict_lvs': status, 'device_records': sorted(records, key=lambda row: row['reference_name'])}
            save()
            step(variant + '_cc', ['kpex', '--threads', '1', '--pdk', 'ihp-sg13g2', '--lvsdb', str(db_path),
                                  '--cell', 'bgr_hbt_worstrows', '--2.5D', '--mode', 'CC', '--out_dir', str(out / (variant + '_kpex'))], 300)
            candidates = list((out / (variant + '_kpex')).rglob('*_k25d_pex_netlist.spice'))
            assert len(candidates) == 1
            raw = candidates[0]
            caps = []
            totals = collections.defaultdict(Decimal)
            for line in logical_lines(raw.read_text()):
                if not line.lower().startswith('c'):
                    continue
                f = line.split()
                assert f[0].startswith('Cext_') and len(f) == 4
                nodes = tuple(sorted(mapping[token.replace('\\', '')] for token in f[1:3]))
                value = number(f[3])
                assert value.is_finite() and value >= 0
                caps.append((nodes[0], nodes[1], str(value)))
                totals[nodes] += value
            assert caps
            receipt['variants'][variant].update(raw_pex_sha256=sha(raw), capacitors=sorted(caps),
                matrix={','.join(pair): str(value) for pair, value in sorted(totals.items())}, capacitor_count=len(caps))
            save()
        flat, union = receipt['variants']['flat'], receipt['variants']['union']
        receipt['checks'] = {'all_device_records_exact': flat['device_records'] == union['device_records'],
                             'capacitor_multiset_exact': flat['capacitors'] == union['capacitors'],
                             'unpruned_matrix_exact': flat['matrix'] == union['matrix']}
        receipt['status'] = 'passed strictLVS and exactCC representation parity' if all(receipt['checks'].values()) else 'failed representation parity'
    except Exception as error:
        receipt.update(status='failed', error=repr(error))
    unchanged = all(sha(Path(path)) == digest for path, digest in inputs.items()) and all(sha(SUPPORT / path) == digest for path, digest in support.items())
    growth = sum(path.stat().st_size for path in out.rglob('*') if path.is_file())
    receipt.update(inputs_support_unchanged=unchanged, output_bytes=growth, wall_s=time.monotonic() - begin,
                   finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    if not unchanged or growth > 2 * 2**30:
        receipt['status'] = 'failed final input/output gate'
    save()
    print(json.dumps({key: value for key, value in receipt.items() if key not in ('inputs', 'support_hashes', 'variants')}, indent=2))
    return 0 if receipt['status'] == 'passed strictLVS and exactCC representation parity' else 1


if __name__ == '__main__':
    raise SystemExit(main())

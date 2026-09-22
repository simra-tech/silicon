#!/usr/bin/env python3
"""Diagnostic replacement-only CC view from unpruned native binary64 results.

This is not a completeness/adoption gate. The supplied substrate binding is an
explicit block-level assumption, never a connection of internal HBT s1 or t.
"""
import argparse
import collections
from decimal import Decimal, localcontext
import hashlib
import json
import math
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def exact_farads(value):
    assert math.isfinite(value) and value >= 0
    with localcontext() as context:
        context.prec = 1200
        farads = Decimal.from_float(value) * Decimal('1e-15')
        assert float(farads * Decimal('1e15')) == value
        return str(farads)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--raw', type=Path, required=True)
    ap.add_argument('--extraction', type=Path, required=True)
    ap.add_argument('--controls', type=Path, required=True)
    ap.add_argument('--materials', type=Path, required=True)
    ap.add_argument('--substrate-node', choices=('vss',), required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    args.output.mkdir(exist_ok=False)
    receipt = dict(status='running', scope='diagnostic derived CC view only; no canonical edit',
                   material_completeness='not qualified', electrical_stability='not run', adoption='not run',
                   wire_resistance='not run', seed='not applicable')
    def save():
        (args.output / 'summary.json').write_text(json.dumps(receipt, indent=2) + '\n')
    save()
    files = [args.raw / 'launch.json', args.raw / 'result/summary.json', args.raw / 'result/exact_capacitances.json',
             args.extraction / 'source_device_audit.json', args.materials / 'summary.json',
             args.controls / 'baseline_586.spice', args.controls / 'reconstructed_586.spice',
             args.controls / 'zero_new_capacitance.spice', args.controls / 'historical_329_ledger.json', Path(__file__)]
    source = Path(__file__).resolve().parents[2] / 'sim/qualification/candidates/bgr_loop24_qref4_r253p465_hv06/bgr_loop24_qref4_r253p465_hv06.spice'
    files.append(source)
    try:
        bindings = {str(p): sha(p) for p in files}
        receipt['inputs'] = bindings
        launch = json.loads(files[0].read_text())
        raw = json.loads(files[1].read_text())
        assert launch['status'] == 'passed' and launch['inputs_unchanged']
        assert raw['status'] == 'passed raw CC generation; completeness not qualified'
        assert raw['all_inputs_tools_unchanged'] and raw['binary64_roundtrip'] == 'passed'
        assert sha(files[2]) == raw['capacitance_sha256']
        audit = json.loads(files[3].read_text())
        assert sha(files[3]) == 'b7e34e2f40436510355aaa50de4dd341f15ddab0d7774d499795c361bf0f5389'
        assert audit['status'] == 'passed' and audit['instance_count'] == 1027
        assert raw['database_sha256'] == '6bc87673405b26f4cbc9f23c7ddf77d49c35b2ae12ec70dc0c0786f8d797856f'
        baseline = files[5].read_bytes()
        reconstructed = files[6].read_bytes()
        skeleton = files[7].read_bytes()
        ledger = json.loads(files[8].read_text())
        assert sha(source) == sha(files[5]) == sha(files[6]) == '586ffb58b6af31c77a2e7cbcb83b173ffa4713ec62401da30901c5a7e606283b'
        assert baseline == reconstructed == source.read_bytes()
        assert sha(files[7]) == '08f55fa0a1f797f7cbf277e5ca1cffc0eaf1ec3b38be082e071535766e2d98be'
        lines = baseline.decode().splitlines(keepends=True)
        old = [(i, line) for i, line in enumerate(lines) if line.startswith('Cext_')]
        assert len(old) == len(ledger) == 329
        assert not any(line.lstrip().lower().startswith('c') for line in skeleton.decode().splitlines())
        assert ''.join(line for line in lines if not line.startswith('Cext_')).encode() == skeleton
        devices = [line for line in lines if line.startswith(('XM', 'XR', 'XQ'))]
        assert len(devices) == 1036
        nodes = set()
        for line in devices:
            words = line.split()
            nodes.update(words[1:4] if words[0].startswith('XR') else words[1:5])
        mapping = audit['net_map']
        assert len(nodes) == len(mapping) == len(set(mapping.values())) == 55
        assert set(mapping.values()) == nodes
        mapping = dict(mapping, VSUBS=args.substrate_node)
        rows = json.loads(files[2].read_text())
        assert len(rows) == raw['capacitor_count']
        cap_lines = []
        mapped = []
        pairs = set()
        totals = collections.defaultdict(Decimal)
        with localcontext() as context:
            context.prec = 1200
            for index, row in enumerate(rows, 1):
                pair = (row['net1'], row['net2'])
                assert pair not in pairs and pair[0] != pair[1]
                pairs.add(pair)
                value = float.fromhex(row['capacitance_fF_hex'])
                assert value == row['capacitance_fF']
                farads = exact_farads(value)
                terminals = [mapping[name] for name in pair]
                name = 'Ccoord_' + str(index)
                cap_lines.append(name + ' ' + ' '.join(terminals) + ' ' + farads + '\n')
                mapped.append(dict(name=name, raw_nodes=list(pair), mapped_nodes=terminals,
                                   native_fF_hex=value.hex(), farads_exact=farads,
                                   shorted_after_mapping=terminals[0] == terminals[1]))
                for terminal in set(terminals):
                    totals[terminal] += Decimal(farads)
        sk = skeleton.decode().splitlines(keepends=True)
        end = [i for i, line in enumerate(sk) if line.lower().startswith('.ends')]
        assert len(end) == 1
        new = ''.join(sk[:end[0]] + cap_lines + sk[end[0]:]).encode()
        assert [line for line in new.decode().splitlines(keepends=True) if not line.startswith('Ccoord_')] == sk
        assert [line for line in new.decode().splitlines(keepends=True) if line.startswith(('XM', 'XR', 'XQ'))] == devices
        for name, data in [('baseline_586.spice', baseline), ('reconstructed_586.spice', reconstructed),
                           ('zero_new_capacitance.spice', skeleton), ('coordinated_cc_diagnostic.spice', new)]:
            (args.output / name).write_bytes(data)
        (args.output / 'capacitance_mapping.json').write_text(json.dumps(dict(net_mapping=mapping, capacitors=mapped), indent=2) + '\n')
        (args.output / 'worker_snapshot.py').write_bytes(Path(__file__).read_bytes())
        receipt.update(status='passed diagnostic view preparation; completeness not qualified',
                       artifacts={p.name: sha(p) for p in args.output.iterdir() if p.name != 'summary.json'},
                       unchanged_device_records=1036, historical_removed=329, new_capacitors=len(rows),
                       binary64_fF_to_exact_decimal_F='passed all values, no pruning',
                       shorted_after_mapping_retained=sum(r['shorted_after_mapping'] for r in mapped),
                       net_total_F={k: str(v) for k, v in sorted(totals.items())},
                       source_reconstruction='passed byte-identical original329C source',
                       zero_newC='passed exact cap-free1036 skeleton; NOT original329C source',
                       substrate_binding='explicit assumed VSUBS→generalVSS; not internal HBT s1/t or thermal equivalence',
                       all_inputs_unchanged=all(sha(Path(p)) == h for p, h in bindings.items()))
        assert receipt['all_inputs_unchanged']
    except Exception as error:
        receipt.update(status='failed view preparation', error=repr(error))
        raise
    finally:
        save()
    print(json.dumps({k: v for k, v in receipt.items() if k not in ('inputs', 'artifacts', 'net_total_F')}, indent=2))


if __name__ == '__main__':
    main()

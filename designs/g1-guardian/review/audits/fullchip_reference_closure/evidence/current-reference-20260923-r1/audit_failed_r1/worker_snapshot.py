#!/usr/bin/env python3
"""Independent saved-reference pin/net/token audit, with no extraction feedback."""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import traceback

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
DESIGN = ROOT / 'designs/g1-guardian'
PDK = Path('/foss/pdks/ihp-sg13g2')


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def dump(p, d):
    p.write_text(json.dumps(d, indent=2) + '\n')


def canonical_name(name):
    name = name.strip().lstrip('\\')
    return name.replace('.', '_').replace('[', '_').replace(']', '_')


def parse_verilog(text):
    # This checker does not import either generation helper.
    text = re.sub(r'//[^\n]*', '', text)
    match = re.search(r'\bmodule\s+(\w+)\s*\((.*?)\)\s*;', text, re.S)
    assert match
    module = match[1]
    header_ports = [s.strip() for s in match[2].split(',')]
    declarations, insts = {}, {}
    for statement in text[match.end():].split(';'):
        s = statement.strip()
        if not s or s == 'endmodule':
            continue
        d = re.fullmatch(r'(input|output|inout)\s+(?:\[(\d+):(\d+)\]\s*)?(.+)', s, re.S)
        if d:
            for name in d[4].split(','):
                name = name.strip().lstrip('\\')
                declarations[name] = [name] if d[2] is None else [name + '[' + str(i) + ']' for i in range(int(d[2]), int(d[3]) - 1, -1)]
            continue
        if re.match(r'^(wire|assign)\s', s):
            assert not s.startswith('assign '), 'Unexpected source assignment needs explicit handling'
            continue
        i = re.fullmatch(r'(\w+)\s+(\\\S+\s+|\S+)\s*\((.*)\)', s, re.S)
        assert i, s[:150]
        master, name = i[1], i[2].strip().lstrip('\\')
        assert name not in insts
        body = i[3]
        matches = list(re.finditer(r'\.(\w+)\s*\(\s*([^()]*)\)', body, re.S))
        remainder = body
        for m in reversed(matches):
            remainder = remainder[:m.start()] + remainder[m.end():]
        assert not remainder.replace(',', '').strip(), remainder
        conns = {}
        for m in matches:
            pin, net = m[1], m[2].strip()
            if net.startswith('{'):
                assert net.endswith('}')
                bits = [x.strip().lstrip('\\') for x in net[1:-1].split(',')]
                pairs = [(pin + '[' + str(len(bits) - j - 1) + ']', n) for j, n in enumerate(bits)]
            else:
                pairs = [(pin, net.lstrip('\\'))]
            for pin, net in pairs:
                assert pin not in conns
                conns[pin] = net
        insts[name] = dict(master=master, connections=conns)
    ports = [p for name in header_ports for p in declarations[name]]
    return module, ports, insts


def parse_cdl(text):
    logical = []
    for raw in text.splitlines():
        if raw.startswith('+'):
            logical[-1] += ' ' + raw[1:].strip()
        else:
            logical.append(raw)
    cells, current = {}, None
    for line in logical:
        fields = line.split()
        if not fields or fields[0].startswith('*'):
            continue
        if fields[0].lower() == '.subckt':
            assert current is None and fields[1].lower() not in {n.lower() for n in cells}
            current = fields[1]
            cells[current] = dict(ports=fields[2:], records=[])
        elif fields[0].lower() == '.ends':
            assert current is not None
            current = None
        elif current is not None:
            cells[current]['records'].append(line)
        else:
            assert fields[0].lower() in ('.global', '.end'), line
    assert current is None
    return cells


def alias_resolver(instances):
    parents, aliases = {}, []
    def resolve(name):
        trail = set()
        while name in parents:
            assert name not in trail
            trail.add(name)
            name = parents[name]
        return name
    for name, row in instances.items():
        if row['master'] != 'sg13g2_IOPadAnalog':
            continue
        conns = row['connections']
        if conns.get('pad') and conns.get('padbare') and conns['pad'] != conns['padbare']:
            parents[resolve(conns['padbare'])] = resolve(conns['pad'])
            aliases.append(dict(instance=name, original_net=conns['padbare'], canonical_net=conns['pad']))
    return resolve, aliases


def check_mapping(cell_name, ports, instances, cells, resolve):
    cell = cells[cell_name]
    assert cell['ports'] == [canonical_name(resolve(p)) for p in ports]
    emitted = {}
    for line in cell['records']:
        f = line.split()
        assert f[0].startswith('X') and f[-2] == '/'
        name = f[0][1:]
        assert name not in emitted
        emitted[name] = dict(master=f[-1], nodes=f[1:-2])
    assert set(emitted) == {canonical_name(n) for n in instances}
    assert len(emitted) == len(instances)
    ledger, floating, used_nets = [], [], set()
    sanitized_nets = {}
    for name, source in instances.items():
        master = source['master']
        target = emitted[canonical_name(name)]
        assert target['master'] == master
        order = cells[master]['ports']
        assert len(order) == len(target['nodes'])
        allowed_extra = {'padbare'} if master == 'sg13g2_IOPadAnalog' else set()
        pin_keys = {canonical_name(p) for p in order}
        assert not {canonical_name(p) for p in source['connections']} - pin_keys - allowed_extra
        source_by_pin = {canonical_name(k): v for k, v in source['connections'].items()}
        for pin, actual in zip(order, target['nodes']):
            original = source_by_pin.get(canonical_name(pin))
            if original:
                resolved = resolve(original)
                expected = canonical_name(resolved)
                assert actual == expected, (cell_name, name, pin, original, expected, actual)
                assert expected.lower() not in sanitized_nets or sanitized_nets[expected.lower()] == resolved
                sanitized_nets[expected.lower()] = resolved
                used_nets.add(actual)
                ledger.append(dict(instance=name, master=master, pin=pin, source_net=original,
                                   resolved_source_net=resolved, emitted_net=actual))
            else:
                assert re.fullmatch(r'_nc[1-9][0-9]*', actual)
                floating.append(dict(instance=name, master=master, pin=pin, generated_net=actual,
                                     source_status='omitted named connection' if original is None else 'explicit empty connection'))
    nc = [row['generated_net'] for row in floating]
    assert len(nc) == len(set(nc)) and not set(nc) & used_nets
    assert len(set(canonical_name(n).lower() for n in instances)) == len(instances)
    return dict(instance_count=len(instances), connected_terminal_count=len(ledger),
                singleton_unconnected_count=len(floating), floating=floating, terminal_ledger=ledger,
                source_net_count_after_aliases=len(sanitized_nets))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--prepared', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    a = ap.parse_args()
    assert not a.output.exists()
    a.output.mkdir(parents=True)
    (a.output / 'worker_snapshot.py').write_bytes(Path(__file__).read_bytes())
    result = dict(status='running independent source audit')
    try:
        assert len(os.sched_getaffinity(0)) == 1
        bulk = Path(os.environ['G1_RESULTS_ROOT'])
        summary = json.loads((a.prepared / 'summary.json').read_text())
        assert summary['status'] == 'passed preparation only; independent mapping audit pending'
        ref = a.prepared / 'g1_chip_top_current.cdl'
        assert sha(ref) == summary['reference_sha256']
        text = ref.read_text()
        cells = parse_cdl(text)
        sources = {name: PDK / ('libs.ref/' + ('sg13g2_io' if name == 'sg13g2_io.cdl' else 'sg13g2_stdcell') + '/cdl/' + name)
                   for name in ('sg13g2_io.cdl', 'sg13g2_stdcell.cdl')}
        sources.update({name: DESIGN / path for name, path in {
            'g1_gate': 'blocks/g1_gate/layout/g1_gate.cdl', 'g1_osc': 'blocks/g1_osc/layout/g1_osc_lvs.cdl',
            'g1_t2f': 'blocks/g1_t2f/layout/g1_t2f_lvs.cdl', 'g1_trip': 'blocks/g1_trip/layout/g1_trip_lvs.cdl',
            'g1_dose_macro': 'blocks/g1_dose/schematic/g1_dose_macro.cdl',
            'g1_dut_macro': 'blocks/g1_dut/schematic/g1_dut_macro.cdl',
            'g1_ls_up': 'blocks/g1_ctrl/ls/sim/netlist/g1_ls_up.cdl'}.items()})
        chunk_audits = []
        for row in summary['copied_source_chunks']:
            label = row['label']
            chunk, = re.findall(r'\* BEGIN_SOURCE ' + re.escape(label) + r'\n(.*?)\n\* END_SOURCE ' + re.escape(label) + r'\n', text, re.S)
            assert digest(chunk) == row['sha256'] and len(chunk.encode()) == row['bytes']
            if label in sources:
                assert chunk.encode() == sources[label].read_bytes()
                assert sha(sources[label]) == summary['source_inputs'][label]
            elif label == 'g1_bgr':
                source = bulk / 'bgr-assembly-signalbypass-20260922-r1/bank.cdl'
                assert sha(source) == summary['source_inputs']['BGR_reference'] and chunk.encode() == source.read_bytes()
                assert len(cells['g1_bgr']['records']) == 1036
            elif label == 'g1_sense':
                source = bulk / 'sense-ring-reference-20260922-r8a/g1_sense_physical.cdl'
                assert sha(source) == summary['source_inputs']['SENSE_reference']
                expected = source.read_text().splitlines(keepends=True)
                expected[0] = expected[0].replace('g1_sense_physical', 'g1_sense', 1)
                assert chunk == ''.join(expected)
            else:
                raise AssertionError(label)
            chunk_audits.append(dict(label=label, sha256=digest(chunk), status='passed exact source bytes with declared SENSE top-name projection only'))
        pnl = DESIGN / 'blocks/g1_padring/netlist/g1_chip_top.pnl.v'
        digital = DESIGN / 'blocks/g1_ctrl/layout/g1_digital.pnl.v'
        assert sha(pnl) == summary['source_inputs']['chip_PNL'] and sha(digital) == summary['source_inputs']['digital_PNL']
        top, ports, original = parse_verilog(pnl.read_text())
        assert top == 'g1_chip_top' and len(original) == 4884
        tsv = bulk / 'fullchip-def-odb-20260922-r5/roundtrip.tsv'
        assert sha(tsv) == summary['source_inputs']['roundtrip']
        physical, connections, nets, bterms, mterms = {}, {}, set(), {}, {}
        for line in tsv.read_text().splitlines():
            f = line.split('\t')
            if f[0] == 'INST':
                physical[f[1]] = f[2]
            elif f[0] == 'NET':
                nets.add(f[1])
            elif f[0] == 'MTERM':
                mterms.setdefault(f[1], set()).add(f[2])
            elif f[0] == 'CONN':
                if f[2] == 'PIN':
                    bterms[f[3]] = f[1]
                else:
                    assert (f[2], f[3]) not in connections
                    connections[f[2], f[3]] = f[1]
        assert len(nets) == 90 and len(physical) == 4904 and set(bterms) == set(ports)
        for name, row in original.items():
            assert physical[name] == row['master']
            for pin, net in row['connections'].items():
                if net:
                    assert connections[name, pin] == net, (name, pin, net, connections.get((name, pin)))
        added = {name: dict(master=master, connections={pin: net for (inst, pin), net in connections.items() if inst == name})
                 for name, master in physical.items() if name not in original}
        assert len(added) == 20
        assert all(row['master'].startswith('sg13g2_Filler') and row['connections'] ==
                   {'iovdd': 'IOVDD', 'iovss': 'IOVSS', 'vdd': 'VDD', 'vss': 'VSS'} for row in added.values())
        complete = dict(original, **added)
        expected_connections = {(name, pin): net for name, row in complete.items() for pin, net in row['connections'].items() if net}
        assert expected_connections == connections
        assert set(expected_connections.values()) | set(bterms.values()) == nets
        library_verilog = DESIGN / 'blocks/g1_padring/ip/sg13g2_io_padbare/verilog/sg13g2_io.v'
        body, = re.findall(r'module sg13g2_IOPadAnalog\s*\(.*?\);(.*?)endmodule', library_verilog.read_text(), re.S)
        assert body.count('assign pad = padbare;') == body.count('assign padbare = pad;') == 1
        resolve, aliases = alias_resolver(original)
        assert len(aliases) == 8
        top_mapping = check_mapping(top, ports, complete, cells, resolve)
        dg, dp, di = parse_verilog(digital.read_text())
        digital_mapping = check_mapping(dg, dp, di, cells, lambda n: n)
        assert top_mapping['singleton_unconnected_count'] == summary['generated_unconnected_pins']['top'] == 9
        assert digital_mapping['singleton_unconnected_count'] == summary['generated_unconnected_pins']['digital'] == 56
        assert all(row['master'] == 'sg13g2_IOPadAnalog' and row['pin'] == 'padres' for row in top_mapping['floating'])
        result.update(status='passed independent saved source/reference mapping audit; not LVS',
                      reference_sha256=sha(ref), preparation_sha256=sha(a.prepared / 'summary.json'),
                      chunks=chunk_audits, top_mapping=top_mapping, digital_mapping=digital_mapping,
                      original_source_graph_nets=90, top_source_connections=len(connections),
                      aliases=aliases, alias_library_sha256=sha(library_verilog),
                      added_fillers=added, top_ports=ports,
                      checks=dict(original4884_source_instance_pin_net_bindings='passed', added20_filler_connections='passed',
                                  all90_roundtrip_nets='passed', complete_emitted4904_mapping='passed',
                                  digital7992_source_mapping='passed', all_source_library_model_parameter_bytes='passed',
                                  alias_scope8='passed', unconnected65_explicitly_accounted='passed',
                                  source_or_sanitizer_collisions='passed none', strict_IO_tap_comparison='failed prior result',
                                  new_fullchip_LVS='not run', current_geometry_cellname_interface='not run',
                                  physical_electrical_adoption='not run', stochastic_seed='not applicable'),
                      script_sha256=sha(Path(__file__)))
    except BaseException as exc:
        result.update(status='failed independent source/reference mapping audit', exception_type=type(exc).__name__,
                      detail=str(exc), traceback=traceback.format_exc())
        dump(a.output / 'failure.json', result)
        dump(a.output / 'summary.json', result)
        raise
    dump(a.output / 'summary.json', result)
    print(json.dumps({k: v for k, v in result.items() if k not in ('top_mapping', 'digital_mapping', 'added_fillers', 'chunks')}, indent=2))


if __name__ == '__main__':
    main()

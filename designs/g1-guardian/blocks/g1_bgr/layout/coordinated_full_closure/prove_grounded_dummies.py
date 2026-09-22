#!/usr/bin/env python3
"""Read-only nine-dummy exclusion proof; never writes a source or rule deck."""
import argparse
import collections
import hashlib
import json
import re
from pathlib import Path

import pya

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent.parent / 'sim/qualification/candidates/bgr_loop24_qref4_r253p465_hv06/bgr_loop24_qref4_r253p465_hv06.spice'
EXPECTED = {'XQ55', 'XQ57', 'XQ58', 'XQ59', 'XQ61', 'XQ63', 'XQ64', 'XQ65', 'XQ66'}
SUPPORT = Path('/usr/local/lib/python3.12/dist-packages/klayout_pex/pdk/ihp-sg13g2/libs.tech/kpex')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--assembly', type=Path, required=True)
    ap.add_argument('--extraction', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    assert not args.output.exists() and pya.__version__ == '0.30.9'
    assert sha(SOURCE) == '586ffb58b6af31c77a2e7cbcb83b173ffa4713ec62401da30901c5a7e606283b'
    lines = [line for line in SOURCE.read_text().splitlines() if line.startswith(('XQ', 'XM', 'XR'))]
    grounded = [line for line in lines if line.startswith('XQ') and line.split()[1:5] == ['vss'] * 4]
    assert len(lines) == 1036 and {line.split()[0] for line in grounded} == EXPECTED
    graph_path = args.assembly / 'terminal_graph.json'
    graph = json.loads(graph_path.read_text())
    observations = [row for row in graph['observations'] if row['instance'] in EXPECTED]
    assert graph['status'] == 'passed' and len(observations) == 36
    for name in EXPECTED:
        rows = [row for row in observations if row['instance'] == name]
        assert len(rows) == 4 and {str(row['terminal']) for row in rows} == {'C', 'B', 'E', 'S'}
        assert all(row['net'] == row['expected'] == 'vss' and row['component'] == 1 for row in rows)
    parity_path = args.extraction / 'flat_parity.json'
    parity = json.loads(parity_path.read_text())
    assert parity['status'] == 'passed' and parity['text_exact']
    assert all(row['xor_polygons'] == 0 for row in parity['polygon_layers'])
    assert sha(args.assembly / 'bank.gds') == parity['input_sha256']
    assert sha(args.extraction / 'flat.gds') == parity['output_sha256']
    db_path = args.extraction / 'extraction.lvsdb'
    db = pya.LayoutVsSchematic()
    db.read(str(db_path))
    xr = db.xref()
    circuits = list(xr.each_circuit_pair())
    assert len(circuits) == 1
    statuses = collections.Counter()
    missing = []
    for pair in xr.each_device_pair(circuits[0]):
        statuses[str(pair.status())] += 1
        if pair.first() is None:
            dev = pair.second()
            cls = dev.device_class()
            missing.append({'reference_name': dev.name, 'model': cls.name,
                            'terminals': {term.name: dev.net_for_terminal(term.name).name for term in cls.terminal_definitions()},
                            'parameters': {par.name: dev.parameter(par.name) for par in cls.parameter_definitions()}})
        else:
            assert pair.status() == pya.NetlistCrossReference.Match
    assert len(missing) == 9 and {'XQ' + row['reference_name'] for row in missing} == EXPECTED
    assert all({value.lower() for value in row['terminals'].values()} == {'vss'} for row in missing)
    # Execute only the installed API's purge on an in-memory reference copy.
    # No layout, original database, schematic, deck, or model is written.
    copied = db.reference.dup()
    before = {dev.name for circuit in copied.each_circuit() for dev in circuit.each_device()}
    copied.purge_devices()
    after = {dev.name for circuit in copied.each_circuit() for dev in circuit.each_device()}
    assert len(before) == 1036 and len(after) == 1027
    assert {'XQ' + name for name in before - after} == EXPECTED
    mapping_path = SUPPORT / 'rule_decks/rfmos_model_mapping.lvs'
    mapping = mapping_path.read_text()
    assert "target_netlist.purge_devices\n  target_netlist.purge" in mapping
    assert "apply_rfmos_model_mapping.call(netlist, 'layout_netlist')" in mapping
    model_path = Path('/foss/pdks/ihp-sg13g2/libs.tech/ngspice/models/sg13g2_hbt_mod.lib')
    model = model_path.read_text(encoding='latin1')
    header = re.search(r'(?m)^\.subckt\s+npn13G2\s+c\s+b\s+e\s+bn\s*$', model)
    assert header is not None
    begin = header.start()
    end = model.index('.ends', begin)
    subckt = model[begin:end]
    assert 'Qnpn13G2 c b e s1 t ' in subckt and 'Rsub s1 bn ' in subckt and 'Rt t 0 ' in subckt
    bindings = {str(path): sha(path) for path in (SOURCE, graph_path, parity_path, db_path, mapping_path, model_path,
                                                args.assembly / 'bank.gds', args.assembly / 'bank.cdl', args.extraction / 'flat.gds', Path(__file__))}
    result = {'status': 'passed', 'source_count': 1036, 'extracted_count': 1027,
              'source_lines': grounded, 'physical_terminal_probes': observations, 'missing_reference_devices': missing,
              'xref_device_status_counts': dict(statuses), 'installed_api_purge_control': {'status': 'passed', 'before': len(before),
              'after': len(after), 'removed': sorted(before - after)}, 'bindings': bindings,
              'native_polygon_and_annotation_parity': 'passed; unchanged flat view includes all nine dummies',
              'extractor_condition': 'Unconditional layout-side purge_devices in rfmos_model_mapping, before optional simplification gates.',
              'upstream_semantics': 'https://raw.githubusercontent.com/KLayout/klayout/v0.30.9/src/db/db/dbCircuit.cc#L773-L803',
              'external_terminals': 'C/B/E/S correspond to model c/b/e/bn; all 36 physical terminals are general VSS.',
              'external_thermal_pin': 'not applicable; canonical npn13G2 is four-port, not npn13G2_5t',
              'internal_nodes': 'Internal s1 and thermal t are NOT asserted to equal physical VSS. Canonical electrical model and all nine instances remain.',
              'internal_thermal_behavior': 'not run', 'conductor_parasitic_extraction': 'not run; no geometry is removed',
              'derived_reference': 'not run; semantic review required', 'original_1036_reference_lvs': 'failed; retained',
              'klayout_version': pya.__version__, 'seed': 'not applicable'}
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({key: value for key, value in result.items() if key not in ('bindings', 'physical_terminal_probes', 'missing_reference_devices')}, indent=2))


if __name__ == '__main__':
    main()

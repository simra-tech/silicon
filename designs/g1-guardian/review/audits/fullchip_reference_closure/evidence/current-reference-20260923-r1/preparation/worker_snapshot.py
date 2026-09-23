#!/usr/bin/env python3
"""Distinct source-bound fullchip reference; preserve native-library mismatches."""
import argparse
import ast
from collections import Counter
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import traceback

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
DESIGN = ROOT / 'designs/g1-guardian'
PDK = Path('/foss/pdks/ihp-sg13g2')


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def dump(p, d):
    p.write_text(json.dumps(d, indent=2) + '\n')


def load_functions(path, names, namespace):
    tree = ast.parse(path.read_text())
    selected = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    assert {n.name for n in selected} == set(names)
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(path), 'exec'), namespace)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--resource-gate', type=Path, required=True)
    a = ap.parse_args()
    assert not a.output.exists()
    a.output.mkdir(parents=True)
    (a.output / 'worker_snapshot.py').write_bytes(Path(__file__).read_bytes())
    result = dict(status='running source-only reference preparation', fullchip_LVS='not run')
    dump(a.output / 'summary.json', result)
    try:
        assert len(os.sched_getaffinity(0)) == 1
        gate = json.loads(a.resource_gate.read_text())
        age = (datetime.datetime.now(datetime.timezone.utc) - datetime.datetime.fromisoformat(gate['utc'])).total_seconds()
        assert gate['status'] == 'passed' and 0 <= age < 1800
        assert (PDK / 'COMMIT').read_text().strip() == '84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
        bulk = Path(os.environ['G1_RESULTS_ROOT'])
        pnl = DESIGN / 'blocks/g1_padring/netlist/g1_chip_top.pnl.v'
        digital = DESIGN / 'blocks/g1_ctrl/layout/g1_digital.pnl.v'
        tsv = bulk / 'fullchip-def-odb-20260922-r5/roundtrip.tsv'
        bgr = bulk / 'bgr-assembly-signalbypass-20260922-r1/bank.cdl'
        bgds = bgr.with_name('bank.gds')
        sense = bulk / 'sense-ring-reference-20260922-r8a/g1_sense_physical.cdl'
        sgds = bulk / 'sense-ring-routing-20260922-r8a/g1_sense_physical.gds'
        canonical_bgr = DESIGN / 'blocks/g1_bgr/sim/qualification/candidates/bgr_loop24_qref4_r253p465_hv06/bgr_loop24_qref4_r253p465_hv06.spice'
        canonical_sense = DESIGN / 'blocks/g1_sense/reports/resume-server-20260922/gm4comp3-qualified-source.spice'
        expected = {pnl: '3ee42e820cbec6d7b0f04eb55c847eaa613daddb93423593197a51fa21df5d9a',
                    tsv: '43be000677b631983ae7f159d988cc6d1654679caa436e6ab3da62b1df2452fd',
                    bgr: '7f8e6e8c606b1e04321c5c9b20e94610d34d42055c8818d03d79352b3a4710b2',
                    bgds: '6d86b9d40333958cb8186d486d29db1532a816e302871e11d07e0f1d999cfc04',
                    sense: 'e3e3c22fa0e59c61f5acc79f3733833ec2a144fe3f133ed09f7922a395deec20',
                    sgds: '8060e30ac14a1c4aeb1cf62204c9e95d9a68dbad3d73412fbb34c6a33be8b4f7',
                    canonical_bgr: '586ffb58b6af31c77a2e7cbcb83b173ffa4713ec62401da30901c5a7e606283b',
                    canonical_sense: 'baab6183c364477da1dd332e4585ae7201b3776bf0f836014744a42809e13877'}
        for p, wanted in expected.items():
            assert sha(p) == wanted, p.name
        source = canonical_bgr.read_text().splitlines()
        ports = next(line.split()[2:] for line in source if line.lower().startswith('.subckt'))
        prim = [line for line in source if line.startswith(('XM', 'XR', 'XQ'))]
        assert len(prim) == 1036
        bgr_text = '.subckt g1_bgr ' + ' '.join(ports) + '\n' + '\n'.join(
            'M' + line[2:] if line.startswith('XM') else line[1:] for line in prim) + '\n.ends g1_bgr\n'
        assert bgr_text.encode() == bgr.read_bytes()
        converter = DESIGN / 'blocks/g1_sense/layout/spice2cdl.py'
        namespace = dict(re=re, PRIM={'sg13_hv_pmos': 'M', 'sg13_hv_nmos': 'M', 'sg13_lv_pmos': 'M',
                                     'sg13_lv_nmos': 'M', 'rppd': 'R', 'rhigh': 'R', 'rsil': 'R', 'cap_cmim': 'C'},
                         DROP={'ng', 'mm_ok'})
        load_functions(converter, ['convert'], namespace)
        canonical = canonical_sense.read_text()
        assert canonical.count('.subckt g1_sense ') == 1
        local = canonical.replace('.subckt g1_sense ', '.subckt g1_sense_physical ')
        reconstructed = '\n'.join(namespace['convert'](local.splitlines())) + '\n'
        assert reconstructed.encode() == sense.read_bytes()
        sense_text = sense.read_text().replace('.subckt g1_sense_physical ', '.subckt g1_sense ', 1)
        assert sense_text.splitlines()[1:] == sense.read_text().splitlines()[1:]
        assembler = DESIGN / 'blocks/g1_padring/flow/lvs/assemble_chip_cdl.py'
        ns = dict(re=re, sys=sys, SAME_CONDUCTOR={'sg13g2_IOPadAnalog': ('padbare', 'pad')})
        load_functions(assembler, ['subckt_pins', 'san', 'verilog_to_subckt'], ns)
        libraries = {
            'sg13g2_stdcell.cdl': PDK / 'libs.ref/sg13g2_stdcell/cdl/sg13g2_stdcell.cdl',
            'sg13g2_io.cdl': PDK / 'libs.ref/sg13g2_io/cdl/sg13g2_io.cdl'}
        assert sha(libraries['sg13g2_io.cdl']) == '7a30e902099e8a8f85e0ae853167904df3793357a793a7b4dc82237b72b3eec4'
        macros = {
            'g1_gate': DESIGN / 'blocks/g1_gate/layout/g1_gate.cdl',
            'g1_osc': DESIGN / 'blocks/g1_osc/layout/g1_osc_lvs.cdl',
            'g1_t2f': DESIGN / 'blocks/g1_t2f/layout/g1_t2f_lvs.cdl',
            'g1_trip': DESIGN / 'blocks/g1_trip/layout/g1_trip_lvs.cdl',
            'g1_dose_macro': DESIGN / 'blocks/g1_dose/schematic/g1_dose_macro.cdl',
            'g1_dut_macro': DESIGN / 'blocks/g1_dut/schematic/g1_dut_macro.cdl',
            'g1_ls_up': DESIGN / 'blocks/g1_ctrl/ls/sim/netlist/g1_ls_up.cdl'}
        texts = {name: p.read_text() for name, p in libraries.items()}
        texts.update({name: p.read_text() for name, p in macros.items()})
        texts.update(g1_bgr=bgr_text, g1_sense=sense_text)
        pin_order = {}
        for label, text in texts.items():
            definitions = ns['subckt_pins'](text)
            assert not {name.lower() for name in definitions} & {name.lower() for name in pin_order}, label
            pin_order.update(definitions)
        pin_order['bondpad_70x70_tm1'] = ['pad']
        dt, dtxt, dc, dnc = ns['verilog_to_subckt'](str(digital), pin_order, {})
        assert dt == 'g1_digital'
        pin_order.update(ns['subckt_pins'](dtxt))
        top, toptext, counts, nc = ns['verilog_to_subckt'](str(pnl), pin_order, {})
        assert top == 'g1_chip_top' and sum(counts.values()) == 4884
        original = {m[2].lstrip('\\'): m[1] for m in re.finditer(r'^\s*(\S+)\s+(\S+)\s*\(\.', pnl.read_text(), re.M)}
        physical, connections = {}, {}
        for line in tsv.read_text().splitlines():
            fields = line.split('\t')
            if fields[0] == 'INST':
                assert fields[1] not in physical
                physical[fields[1]] = fields[2]
            if fields[0] == 'CONN' and fields[2] != 'PIN':
                key = tuple(fields[2:])
                assert key not in connections
                connections[key] = fields[1]
        assert len(physical) == 4904 and all(physical.get(k) == v for k, v in original.items())
        additions = []
        for name, master in physical.items():
            if name in original:
                continue
            assert master.startswith('sg13g2_Filler')
            conn = {pin: connections[name, pin] for pin in pin_order[master]}
            assert set(conn) == {'iovdd', 'iovss', 'vdd', 'vss'}
            assert conn == {'iovdd': 'IOVDD', 'iovss': 'IOVSS', 'vdd': 'VDD', 'vss': 'VSS'}
            additions.append(dict(instance=name, master=master, pin_connections=conn,
                                  cdl='X' + ns['san'](name) + ' ' + ' '.join(conn[p] for p in pin_order[master]) + ' / ' + master))
        assert len(additions) == 20
        assert toptext.endswith('.ENDS\n')
        toptext = toptext[:-len('.ENDS\n')] + '\n'.join(row['cdl'] for row in additions) + '\n.ENDS\n'
        output = '* DISTINCT source-bound current fullchip reference; not LVS-qualified\n'
        chunks = []
        for label, text in texts.items():
            output += '* BEGIN_SOURCE ' + label + '\n' + text + '\n* END_SOURCE ' + label + '\n'
            chunks.append(dict(label=label, bytes=len(text.encode()), sha256=hashlib.sha256(text.encode()).hexdigest()))
        output += '.SUBCKT bondpad_70x70_tm1 pad\n* Original metal-only bondpad interface\n.ENDS\n'
        output += '* BEGIN_DIGITAL\n' + dtxt + '* END_DIGITAL\n* BEGIN_TOP\n' + toptext + '* END_TOP\n'
        reference = a.output / 'g1_chip_top_current.cdl'
        reference.write_text(output)
        (a.output / 'g1_chip_top_only.cdl').write_text(toptext)
        (a.output / 'g1_digital_source.cdl').write_text(dtxt)
        input_paths = dict(libraries)
        input_paths.update(macros)
        input_paths.update(chip_PNL=pnl, digital_PNL=digital, roundtrip=tsv, BGR_reference=bgr,
                           BGR_GDS=bgds, SENSE_reference=sense, SENSE_GDS=sgds,
                           BGR_canonical=canonical_bgr, SENSE_canonical=canonical_sense,
                           source_converter=assembler, sense_converter=converter)
        result.update(status='passed preparation only; independent mapping audit pending',
                      source_inputs={name: sha(p) for name, p in input_paths.items()},
                      copied_source_chunks=chunks, top_ports=ns['subckt_pins'](toptext)[top],
                      original_top_instances=sum(counts.values()), added_fillers=additions,
                      top_instance_count=4904, digital_instance_count=sum(dc.values()),
                      generated_unconnected_pins=dict(top=nc, digital=dnc),
                      source_macro_ports={name: pin_order[name] for name in list(macros) + ['g1_bgr', 'g1_sense', 'g1_digital']},
                      checks=dict(BGR1036_exact_reference_reconstruction='passed', SENSE_exact_reference_reconstruction='passed',
                                  original_library_bytes='passed', original_top_instance_master_binding='passed',
                                  explicit_twenty_fillers='passed', independent_full_mapping='not run',
                                  strict_fullchip_LVS='not run', known_IO_tap_strict_comparison='failed prior result'),
                      reference_sha256=sha(reference), resource_gate_sha256=sha(a.resource_gate),
                      script_sha256=sha(Path(__file__)), original_electrical_sources_unchanged=True)
        assert all(sha(p) == result['source_inputs'][name] for name, p in input_paths.items())
    except BaseException as exc:
        result.update(status='failed source-only reference preparation', exception_type=type(exc).__name__,
                      detail=str(exc), traceback=traceback.format_exc())
        dump(a.output / 'failure.json', result)
        dump(a.output / 'summary.json', result)
        raise
    dump(a.output / 'summary.json', result)
    print(json.dumps({k: v for k, v in result.items() if k not in ('source_inputs', 'source_macro_ports', 'copied_source_chunks', 'added_fillers')}, indent=2))


if __name__ == '__main__':
    main()

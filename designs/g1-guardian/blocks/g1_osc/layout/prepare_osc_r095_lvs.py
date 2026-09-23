#!/usr/bin/env python3
"""Derive native-device LVS reference from the exact simulated R0.95 source.

Only explicitly named Cext_* baseline wire parasitics are excluded: stock
device LVS does not extract those capacitors. Native MOS, segmented resistors,
MIM capacitors and antenna diode remain. This is not a new electrical/PEX
netlist; simulations must never use the resulting parasitic-free CDL.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

import lvs_netlist

SOURCE_SHA = 'f08bf0517066736fa0a4763b0a7a380d06a7b670730239d1be05a21133f4d319'
CONVERTER_SHA = '5908db3635617c71c11435536b5a50342578555682848b567a2ba5457493f734'
PORTMAP = dict(vdd='VDD', vss='VSS', **{'trim%d'%n:'trim[%d]'%n for n in range(4)})


def sha(data):
    return hashlib.sha256(data).hexdigest()


def convert(source):
    if sha(source) != SOURCE_SHA:
        raise ValueError('Unexpected candidate source')
    if sha(Path(lvs_netlist.__file__).read_bytes()) != CONVERTER_SHA:
        raise ValueError('Unexpected converter')
    kept, excluded, devices = [], [], Counter()
    for line in source.decode().splitlines():
        tokens = line.split()
        if not tokens or tokens[0].startswith('*'):
            continue
        if tokens[0].startswith('Cext_'):
            assert len(tokens) == 4
            excluded.append(line)
        elif tokens[0].startswith('X'):
            model = next(t for t in reversed(tokens) if '=' not in t)
            assert model in ('sg13_lv_nmos', 'sg13_lv_pmos', 'rppd', 'dpantenna', 'cap_cmim')
            devices[model] += 1
            kept.append(line)
        elif tokens[0].lower() in ('.subckt', '.ends'):
            kept.append(line)
        else:
            raise ValueError('Unclassified source line: '+line)
    assert sum(devices.values()) == 81 and devices['rppd'] == 18
    assert devices['cap_cmim'] == 11 and devices['dpantenna'] == 1
    assert devices['sg13_lv_nmos'] + devices['sg13_lv_pmos'] == 51
    assert len(excluded) == 609 and len({line.split()[0] for line in excluded}) == len(excluded)
    converted = lvs_netlist.convert(kept, 'g1_osc', PORTMAP)
    return '\n'.join(converted)+'\n', dict(native_devices=dict(devices),
        native_source_lines=[line for line in kept if line.startswith('X')],
        converted_native_lines=[line for line in converted if not line.startswith('.')],
        excluded_baseline_wire_capacitors=len(excluded),
        excluded_lines_sha256=sha(('\n'.join(excluded)+'\n').encode()))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    report = args.output.with_suffix('.json')
    assert not args.output.exists() and not report.exists()
    text, counts = convert(args.source.read_bytes())
    args.output.write_text('* Native-device LVS comparison only; not electrical simulation\n'+text)
    report.write_text(json.dumps(dict(status='prepared; stock LVS not run',
        source_sha256=SOURCE_SHA, converter_sha256=CONVERTER_SHA,
        reference_sha256=sha(args.output.read_bytes()), **counts), indent=2)+'\n')


if __name__ == '__main__':
    main()

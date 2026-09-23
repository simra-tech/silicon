#!/usr/bin/env python3
"""Correct two instance/net name collisions; exact reversible netlist change."""
import argparse
import hashlib
import json
from pathlib import Path
import re
from fullchip_reference_closure.audit_reference import parse_verilog


def rename_instances(text):
    original = text
    before_module, before_ports, before = parse_verilog(original)
    mapping = {}
    for index in (0, 1):
        old = 'clkbuf_fanout_split%d_osc_clk' % index
        new = old + '_cell'
        assert new not in text and old in before
        assert before[old]['master'] == 'sg13g2_buf_16'
        assert before[old]['connections']['X'] == old
        pattern = r'(\bsg13g2_buf_16\s+)' + old + r'(\s*\()'
        text, count = re.subn(pattern, lambda m: m.group(1)+new+m.group(2), text)
        assert count == 1
        mapping[old] = new
    module, ports, after = parse_verilog(text)
    assert (module, ports) == (before_module, before_ports)
    assert {mapping.get(name, name): row for name, row in before.items()} == after
    restored = text
    for old, new in mapping.items():
        restored = restored.replace(new, old)
    assert restored == original
    return text, mapping


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    assert not a.output.exists()
    original = a.input.read_bytes()
    corrected, mapping = rename_instances(original.decode())
    a.output.mkdir(parents=True)
    (a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    out = a.output/'g1_digital.nl.v'
    out.write_text(corrected)
    result = dict(status='passed exact reversible two-instance rename',
                  input=str(a.input), input_sha256=hashlib.sha256(original).hexdigest(),
                  output_sha256=hashlib.sha256(out.read_bytes()).hexdigest(), mapping=mapping,
                  not_run=['Corresponding routed OpenDB/DEF canonical rename',
                           'Independent functional equivalence', 'Adoption'])
    (a.output/'summary.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()

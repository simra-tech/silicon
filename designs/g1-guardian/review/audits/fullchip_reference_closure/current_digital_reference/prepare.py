#!/usr/bin/env python3
"""Independently bind current digital source and replace only its CDL block."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from audit_reference import parse_verilog, parse_cdl, canonical_name, check_mapping


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def powered_equivalence(logical, physical):
    lm, lp, li = parse_verilog(logical)
    pm, pp, pi = parse_verilog(physical)
    assert lm == pm == 'g1_digital' and lp == pp and len(lp) == 46
    assert set(li) == set(pi) and len(li) == 7771
    additions = []
    for name, row in li.items():
        actual = pi[name]
        assert row['master'] == actual['master']
        assert all(actual['connections'].get(p) == n for p,n in row['connections'].items())
        extra = {p:n for p,n in actual['connections'].items() if p not in row['connections']}
        assert not set(extra)-{'VDD', 'VSS'}
        assert all(p == n for p,n in extra.items())
        assert actual['connections'].get('VDD') == 'VDD' and actual['connections'].get('VSS') == 'VSS'
        additions.extend(dict(instance=name, pin=p, node=n) for p,n in sorted(extra.items()))
    return pp, pi, additions


def ordered_interface(old, new):
    assert len(old) == len(new) == 46
    assert [canonical_name(p) for p in old] == [canonical_name(p) for p in new]
    assert len({canonical_name(p) for p in new}) == 46


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output', type=Path, required=True)
    a = ap.parse_args()
    assert not a.output.exists() and len(os.sched_getaffinity(0)) == 1
    bulk = Path(os.environ['G1_RESULTS_ROOT'])
    original = bulk/'io-explicit-vss-reference-20260923-r5/explicit_vss.cdl'
    logical = bulk/'digital-final-nlrename-20260923-r1/g1_digital.nl.v'
    physical = bulk/'digital-final-pnlrename-20260923-r1/g1_digital.nl.v'
    stock = bulk/'digital-cleanflat-lvs-20260923-r1'
    reference = stock/'g1_digital_source.cdl'
    lib = Path('/foss/pdks/ihp-sg13g2/libs.ref/sg13g2_stdcell/cdl/sg13g2_stdcell.cdl')
    geometry = bulk/'digital-reroute-streamout-20260923-r1/signal_routed_native.gds'
    terminal = bulk/'digital-reroute-terminals-20260923-r1/analysis.json'
    wanted = {original: '18b6ec3f70bdc74ab2acc98c97b8bcad7185a8d6de26288b6f66af0e159cd0fc',
        logical: '6181b988eeaa28953a37bc11b2f4fb4b66325ed518c4cfa74387bfb83845a301',
        physical: '4fd0b6165a53d292ab8b14abf2b3e70be1333598a5fe1a29ea6ebe9ec6ba0a60',
        reference: '3cb199c177023100a24877f04b116c182b583a8100d8628b2a828db312bb062f',
        lib: '6f629dc6b0d21df83fba7deb462a11217dd4b0737e99cd18a0a05ab876667c9a',
        stock/'summary.json': 'c33d7df26852825d561d67ccd8418fcc918a4748b95e1f11723a4774333b87df',
        geometry: '9a52cc71122df8fcc56bbd3ec3e0842958e1f7eec0f73c64ed21a8e2c7ea1805'}
    for p,h in wanted.items():
        assert sha(p) == h, p
    s = json.loads((stock/'summary.json').read_text())
    assert s['status'] == 'passed strict native stock macro LVS' and all(s['strict_checks'].values())
    t = json.loads(terminal.read_text())
    assert t['status'] == 'passed exact held terminal partition and physical ports'
    assert t['inputs'][str(geometry)] == sha(geometry)
    inputs = {str(p):sha(p) for p in list(wanted)+[terminal, Path(__file__).resolve(), HERE.parent/'audit_reference.py']}
    a.output.mkdir(parents=True)
    (a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    result = dict(status='running source-only successor', inputs=inputs, fullchip_LVS='not run')
    try:
        ports, instances, powers = powered_equivalence(logical.read_text(), physical.read_text())
        prefix = lib.read_text()+'\n'
        assert reference.read_text().startswith(prefix)
        digital = reference.read_text()[len(prefix):]
        cells = parse_cdl(digital)
        assert list(cells) == ['g1_digital'] and cells['g1_digital']['ports'] == ports
        inverse_ports = {p:canonical_name(p) for p in ports if p != canonical_name(p)}
        sanitized = re.sub(r'\S+', lambda m:inverse_ports.get(m.group(), m.group()), digital)
        mapping = check_mapping('g1_digital', ports, instances, parse_cdl(prefix+sanitized), lambda n:n)
        assert mapping['instance_count'] == 7771 and mapping['singleton_unconnected_count'] == 60
        old = original.read_text()
        assert old.count(lib.read_text()) == 1
        match, = list(re.finditer(r'(?ms)(^\* BEGIN_DIGITAL\n)(.*?)(^\* END_DIGITAL\n)', old))
        old_body = match[2]
        old_cell = parse_cdl(old_body)['g1_digital']
        ordered_interface(old_cell['ports'], ports)
        successor = old[:match.start(2)]+digital+old[match.end(2):]
        assert successor[:match.start(2)] == old[:match.start(2)]
        assert successor[match.start(2)+len(digital):] == old[match.end(2):]
        assert successor[:match.start(2)]+old_body+successor[match.start(2)+len(digital):] == old
        before, after = parse_cdl(old), parse_cdl(successor)
        assert set(before) == set(after)
        assert all(before[n] == after[n] for n in before if n != 'g1_digital')
        negative = []
        for name, fn in [
            ('changed_functional_connection', lambda:powered_equivalence(logical.read_text(), physical.read_text().replace('.A2(\\u_core.u_seu.u_phase.qc[0] )', '.A2(VSS)', 1))),
            ('wrong_power_connection', lambda:powered_equivalence(logical.read_text(), physical.read_text().replace('.VDD(VDD)', '.VDD(VSS)', 1))),
            ('missing_physical_instance', lambda:powered_equivalence(logical.read_text(), physical.read_text().replace('sg13g2_a21o_1 _3250_', 'sg13g2_a21o_1 REMOVED_3250_', 1))),
            ('swapped_ordered_interface', lambda:ordered_interface(old_cell['ports'], [ports[1],ports[0]]+ports[2:])),
        ]:
            rejected = False
            try:
                fn()
            except AssertionError:
                rejected = True
            assert rejected, name
            negative.append(dict(name=name, rejected=True))
        assert all(sha(Path(p)) == h for p,h in inputs.items())
        output = a.output/'current_digital_explicit_vss.cdl'
        output.write_text(successor)
        (a.output/'old_digital_block.cdl').write_text(old_body)
        (a.output/'new_digital_block.cdl').write_text(digital)
        (a.output/'mapping.json').write_text(json.dumps(mapping, indent=2)+'\n')
        result.update(status='passed reversible current-digital reference preparation; fullchip LVS not run',
            source_sha256=sha(output), current_digital_instances=7771,
            explicit_power_connections_added=powers, negative_controls=negative,
            ordered46ports=ports, every_other_source_byte_held=True, reverse_original_exact=True,
            body_interface='owner-authorized explicit VSS derivative held',
            tap_AP='unresolved; original values held', grounded_dummy_projection='not applied',
            model_rule_changes='not applicable', adoption='not run')
    except Exception as exc:
        result.update(status='failed source-only successor', error=repr(exc))
        raise
    finally:
        (a.output/'summary.json').write_text(json.dumps(result, indent=2)+'\n')


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""One top-token-only view plus isolated unchanged-deck name-control fixtures."""
import argparse
import hashlib
import json
from pathlib import Path


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--reference', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    a = ap.parse_args()
    assert not a.output.exists()
    original = a.reference.read_bytes()
    assert sha(original) == 'd680bbcc6d66fc13bcebb225b9e94d667c617bc6bb7402bf7a35255ae462c4cc'
    old = b'.SUBCKT g1_chip_top '
    new = b'.SUBCKT placed_core_NOT_CONNECTED_FULLCHIP '
    assert original.count(old) == 1 and original.count(new) == 0
    offset = original.index(old) + len(b'.SUBCKT ')
    old_name, new_name = b'g1_chip_top', b'placed_core_NOT_CONNECTED_FULLCHIP'
    changed = original[:offset] + new_name + original[offset + len(old_name):]
    assert changed.replace(new, old, 1) == original
    assert changed[:offset] == original[:offset]
    assert changed[offset + len(new_name):] == original[offset + len(old_name):]
    # Whitespace-separated token differential: exactly the one top identifier.
    before, after = original.split(), changed.split()
    edits = [(i, x.decode(), y.decode()) for i, (x, y) in enumerate(zip(before, after)) if x != y]
    assert len(before) == len(after) and len(edits) == 1
    assert edits[0][1:] == ('g1_chip_top', 'placed_core_NOT_CONNECTED_FULLCHIP')
    a.output.mkdir(parents=True)
    (a.output / 'worker_snapshot.py').write_bytes(Path(__file__).read_bytes())
    (a.output / 'g1_chip_top_layout_name_only.cdl').write_bytes(changed)
    leaf = '.SUBCKT {leaf} A Y VDD VSS\nMN Y A VSS VSS sg13_lv_nmos W=0.8u L=0.13u\nMP Y A VDD VDD sg13_lv_pmos W=1.6u L=0.13u\n.ENDS\n'
    top = '.SUBCKT {top} A Y VDD VSS\nX1 A N VDD VSS {leaf}\nX2 {second_input} Y VDD VSS {leaf}\n.ENDS\n'
    def fixture(leaf_name, top_name='NAME_CONTROL_TOP', second_input='N'):
        return leaf.format(leaf=leaf_name) + top.format(top=top_name, leaf=leaf_name, second_input=second_input)
    reference = fixture('LOGICAL_INV')
    (a.output / 'control_reference.cdl').write_text(reference)
    cases = [dict(name='same_names', leaf='LOGICAL_INV', top='NAME_CONTROL_TOP', second_input='N', expected_match=True),
             dict(name='child_alias', leaf='RETAINED_INV', top='NAME_CONTROL_TOP', second_input='N', expected_match=True),
             dict(name='wrong_connection', leaf='RETAINED_INV', top='NAME_CONTROL_TOP', second_input='A', expected_match=False),
             dict(name='top_alias_observation', leaf='RETAINED_INV', top='OTHER_TOP', second_input='N', expected_match=None)]
    for row in cases:
        data = fixture(row['leaf'], row['top'], row['second_input'])
        target = a.output / (row['name'] + '_layout.cdl')
        target.write_text(data)
        row.update(layout_netlist=target.name, sha256=sha(data.encode()))
    result = dict(status='passed top-name-only exact differential and control preparation',
                  original_reference_sha256=sha(original), derived_reference_sha256=sha(changed),
                  byte_offset=offset, byte_edit=dict(before=old_name.decode(), after=new_name.decode()),
                  token_edits=edits, unchanged_prefix_sha256=sha(original[:offset]),
                  unchanged_suffix_sha256=sha(original[offset + len(old_name):]),
                  control_reference_sha256=sha(reference.encode()), cases=cases,
                  checks=dict(exact_single_name_token_change='passed', all_body_library_bytes='passed',
                              inverse_reconstruction='passed', original_reference_unchanged='passed',
                              unchanged_stock_name_controls='not run', physical_extraction='not run',
                              fullchip_LVS='not run', model_deck_changes='not run', seed='not applicable'),
                  script_sha256=sha(Path(__file__).read_bytes()))
    assert sha(a.reference.read_bytes()) == result['original_reference_sha256']
    (a.output / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()

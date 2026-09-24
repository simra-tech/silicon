#!/usr/bin/env python3
"""Replace only a proved native SENSE hierarchy; hold the entire parent root.

Intended for a source-bound compensation successor after BGR cuts are already
integrated. No BGR overlay is added, removed, or flattened by this operation.
Fresh affected physical and electrical checks remain mandatory.
"""
import argparse
import json
import os
from pathlib import Path
import time
import klayout.db as k
from replace_analog_pair_candidate import (
    sha, protected, root_without, structural_digest, validate_proof,
)
from replace_digital_macro_candidate import equal_macro


def replace(layout, top, target_name, transform, old, old_cell, new, new_cell):
    assert layout.dbu == old.dbu == new.dbu == .001
    assert target_name != top.name
    target = layout.cell(target_name)
    assert target is not None
    instance, = [i for i in top.each_inst() if i.cell_index == target.cell_index()]
    assert str(instance.cplx_trans) == transform
    assert instance.na <= 1 and instance.nb <= 1 and target.parent_cells() == 1
    equal_macro(old, old_cell, layout, target)
    assert structural_digest(old_cell) == structural_digest(target)
    held = protected(top, {target_name})
    root = root_without(top, set())
    bbox = top.bbox()
    target.clear()
    target.copy_tree(new_cell)
    equal_macro(new, new_cell, layout, target)
    assert structural_digest(new_cell) == structural_digest(target)
    assert protected(top, {target_name}) == held
    assert root_without(top, set()) == root and top.bbox() == bbox
    return held, root, bbox


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--manifest-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert k.__version__ == '0.30.9' and len(os.sched_getaffinity(0)) == 1
    assert not args.output.exists() and sha(args.manifest) == args.manifest_sha256
    contract = json.loads(args.manifest.read_text())
    assert contract['status'] == 'frozen SENSE-only preparation; no adoption'
    row = contract['replacement']
    assert row['role'] == 'SENSE' and row['target_cell'] == 'g1_sense_candidate'
    assert row['transform'] == 'r90 *1 1031000,331000'
    here = Path(__file__).resolve().parent
    inputs = {str(p):sha(p) for p in [args.manifest, Path(__file__),
        here/'replace_analog_pair_candidate.py', here/'replace_digital_macro_candidate.py',
        here/'prepare_digital_reroute_native_hierarchy.py']}
    for item in [contract['parent']['gds'], row['old_gds'], row['new_gds']]:
        assert sha(item['path']) == item['sha256']
        inputs[item['path']] = item['sha256']
    assert contract['parent']['proofs'] and row['proofs']
    for proof in contract['parent']['proofs'] + row['proofs']:
        validate_proof(proof)
        inputs[proof['path']] = proof['sha256']
    args.output.mkdir(parents=True)
    (args.output/'source.py').write_bytes(Path(__file__).read_bytes())
    result = dict(status='running SENSE-only replacement', inputs_sha256=inputs,
        not_run=['Fresh affected stock DRC/maximal/density/antenna',
                 'Fresh device LVS and terminal partition',
                 'Candidate-specific parasitic/electrical qualification', 'Adoption'])
    started = time.monotonic()
    try:
        layout = k.Layout(); layout.read(contract['parent']['gds']['path'])
        top = layout.cell(contract['parent']['top_cell'])
        assert top is not None and [c.name for c in layout.top_cells()] == [top.name]
        old = k.Layout(); old.read(row['old_gds']['path'])
        new = k.Layout(); new.read(row['new_gds']['path'])
        old_cell = old.cell(row['old_gds']['cell'])
        new_cell = new.cell(row['new_gds']['cell'])
        assert old_cell is not None and new_cell is not None
        held, root, bbox = replace(layout, top, row['target_cell'], row['transform'],
                                  old, old_cell, new, new_cell)
        clean = k.Layout(); clean.dbu = layout.dbu
        ct = clean.create_cell(top.name); ct.copy_tree(top)
        assert structural_digest(ct) == structural_digest(top)
        assert protected(ct, {row['target_cell']}) == held
        assert root_without(ct, set()) == root
        dest = args.output/'sense_replaced_native.gds'; clean.write(str(dest))
        saved = k.Layout(); saved.read(str(dest)); st = saved.cell(top.name)
        assert [c.name for c in saved.top_cells()] == [top.name]
        assert saved.dbu == .001 and st.bbox() == bbox
        assert protected(st, {row['target_cell']}) == held
        assert root_without(st, set()) == root
        equal_macro(new, new_cell, saved, saved.cell(row['target_cell']))
        assert structural_digest(new_cell) == structural_digest(saved.cell(row['target_cell']))
        assert all(sha(p) == h for p,h in inputs.items())
        result.update(status='passed isolated SENSE-only native hierarchy replacement',
            GDS_sha256=sha(dest), top_cell=top.name,
            original_parent_sha256=contract['parent']['gds']['sha256'],
            new_native_sha256=row['new_gds']['sha256'],
            new_native_hierarchy=structural_digest(new_cell),
            transform=row['transform'], unchanged_cell_signatures=held,
            all_root_shapes_texts_properties_instances_and_die_held=True,
            all_other_native_hierarchies_held=True, saved_roundtrip='passed',
            BGR_overlay_changes='not applicable; all existing BGR and root records held')
    except Exception as exc:
        result.update(status='failed SENSE-only native hierarchy replacement', error=repr(exc))
        raise
    finally:
        result['wall_s'] = time.monotonic()-started
        (args.output/'analysis.json').write_text(json.dumps(result, indent=2)+'\n')


if __name__ == '__main__':
    main()

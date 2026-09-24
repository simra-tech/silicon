#!/usr/bin/env python3
"""Prepare native SENSE replacement plus minimal BGR cuts in an isolated parent.

The manifest fixes input hashes, exact proof predicates, instance transforms
and cell identities. This preparation preserves every non-target cell and the
entire root definition, including properties. It is not full-chip acceptance.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import time
import klayout.db as k
from prepare_digital_reroute_native_hierarchy import signature, properties
from replace_digital_macro_candidate import equal_macro, physical


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def protected(top, targets):
    pending = [top]
    result = {}
    while pending:
        cell = pending.pop()
        if cell.name in targets or cell.name in result:
            continue
        result[cell.name] = signature(cell.layout(), cell)
        pending.extend(i.cell for i in cell.each_inst())
    return result


def structural_digest(cell, memo=None):
    """Hierarchy-sensitive copy identity, independent only of cell-name aliases."""
    if memo is None:
        memo = {}
    if cell.cell_index() in memo:
        return memo[cell.cell_index()]
    layout = cell.layout()
    shapes = []
    for li in layout.layer_indexes():
        info = layout.get_info(li)
        shapes.extend((info.layer, info.datatype, s.to_s(), properties(s))
                      for s in cell.shapes(li).each())
    children = sorted((structural_digest(i.cell, memo), str(i.cplx_trans),
                       str(i.a), str(i.b), i.na, i.nb, properties(i))
                      for i in cell.each_inst())
    raw = json.dumps([properties(cell), sorted(shapes), children],
                     separators=(',', ':')).encode()
    memo[cell.cell_index()] = hashlib.sha256(raw).hexdigest()
    return memo[cell.cell_index()]


def validate_proof(record):
    path = Path(record['path'])
    assert sha(path) == record['sha256'], str(path)
    data = json.loads(path.read_text())
    assert record['equals'], 'A proof must have explicit acceptance predicates'
    for keys, expected in record['equals']:
        observed = data
        for key in keys:
            observed = observed[key]
        assert observed == expected, (str(path), keys, observed, expected)


def root_without(top, excluded):
    """Exact root signature excluding only explicitly named added instances."""
    layout = top.layout()
    shapes = []
    for li in layout.layer_indexes():
        info = layout.get_info(li)
        shapes.extend((info.layer, info.datatype, s.to_s(), properties(s))
                      for s in top.shapes(li).each())
    children = sorted((i.cell.name, str(i.cplx_trans), str(i.a), str(i.b),
                       i.na, i.nb, properties(i)) for i in top.each_inst()
                      if i.cell.name not in excluded)
    return [properties(top), sorted(shapes), children]


def effective_bgr(layout, top, row, extra=None):
    """Check native + existing global supply overlay (+ new local cuts)."""
    expected = k.Layout(); expected.read(row['path'])
    cell = expected.cell(row['cell']); assert cell is not None
    components = []
    for name in ['g1_bgr_candidate', 'bgr_supply_additive_context_candidate'] + ([extra] if extra else []):
        inst, = [i for i in top.each_inst() if i.cell.name == name]
        assert inst.na <= 1 and inst.nb <= 1
        wanted = 'r0 *1 0,0' if name == 'bgr_supply_additive_context_candidate' else 'r0 *1 331000,732000'
        assert str(inst.cplx_trans) == wanted
        components.append(inst)
    pairs = {(i.layer, i.datatype) for i in layout.layer_infos()+expected.layer_infos()}
    trans = k.ICplxTrans(1, 0, False, 331000, 732000)
    checks = []
    for layer, datatype in sorted(pairs):
        info = k.LayerInfo(layer, datatype)
        actual = k.Region()
        for inst in components:
            actual += physical(layout, inst.cell, info).transformed(inst.cplx_trans)
        wanted = physical(expected, cell, info).transformed(trans)
        assert (actual ^ wanted).is_empty(), ('effective BGR', layer, datatype)
        checks.append(dict(layer=layer, datatype=datatype, xor_dbu2=0))
    return checks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--manifest-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert k.__version__ == '0.30.9' and len(os.sched_getaffinity(0)) == 1
    assert not args.output.exists() and sha(args.manifest) == args.manifest_sha256
    contract = json.loads(args.manifest.read_text())
    assert contract['status'] == 'frozen preparation only; no source adoption'
    assert [r['role'] for r in contract['replacements']] == ['SENSE']
    additive = contract['bgr_additive']
    inputs = {str(args.manifest): sha(args.manifest), str(Path(__file__)): sha(__file__)}
    for row in [contract['parent']] + contract['replacements']:
        for key in (['gds'] if row is contract['parent'] else ['old_gds', 'new_gds']):
            item = row[key]
            assert sha(item['path']) == item['sha256']
            inputs[item['path']] = item['sha256']
    for key in ['overlay', 'old_effective', 'new_effective']:
        item = additive[key]
        assert sha(item['path']) == item['sha256']
        inputs[item['path']] = item['sha256']
    for row in contract['replacements'] + [additive]:
        assert row['proofs']
        for proof in row['proofs']:
            validate_proof(proof)
            inputs[proof['path']] = proof['sha256']
    args.output.mkdir(parents=True)
    (args.output/'source.py').write_bytes(Path(__file__).read_bytes())
    result = dict(status='running', inputs_sha256=inputs, replacements=[],
                  not_run=['Full-parent terminal/device connectivity',
                           'Stock full-parent DRC/maximal/density/antenna',
                           'Affected parasitic and electrical checks',
                           'Source adoption'], not_applicable=['Random seed'])
    start = time.monotonic()
    try:
        layout = k.Layout(); layout.read(contract['parent']['gds']['path'])
        top = layout.cell(contract['parent']['top_cell'])
        assert top is not None and layout.dbu == .001
        assert [c.name for c in layout.top_cells()] == [top.name]
        target_names = {r['target_cell'] for r in contract['replacements']}
        assert len(target_names) == 1 and top.name not in target_names
        before = protected(top, target_names)
        original_root = root_without(top, set())
        bbox = top.bbox()
        result['old_effective_bgr'] = effective_bgr(layout, top, additive['old_effective'])
        targets = []
        for row in contract['replacements']:
            target = layout.cell(row['target_cell']); assert target is not None
            instance, = [i for i in top.each_inst() if i.cell_index == target.cell_index()]
            assert str(instance.cplx_trans) == row['transform']
            assert instance.na <= 1 and instance.nb <= 1
            assert target.parent_cells() == 1
            old = k.Layout(); old.read(row['old_gds']['path'])
            new = k.Layout(); new.read(row['new_gds']['path'])
            old_cell = old.cell(row['old_gds']['cell'])
            new_cell = new.cell(row['new_gds']['cell'])
            assert old_cell is not None and new_cell is not None
            equal_macro(old, old_cell, layout, target)
            assert structural_digest(old_cell) == structural_digest(target)
            targets.append((row, target, new, new_cell))
        for row, target, new, new_cell in targets:
            target.clear(); target.copy_tree(new_cell)
            equal_macro(new, new_cell, layout, target)
            assert structural_digest(new_cell) == structural_digest(target)
            result['replacements'].append(dict(role=row['role'],
                target_cell=target.name, transform=row['transform'],
                new_hierarchy_digest=structural_digest(new_cell),
                new_gds_sha256=row['new_gds']['sha256']))
        assert protected(top, target_names) == before
        overlay = k.Layout(); overlay.read(additive['overlay']['path'])
        overlay_cell = overlay.cell(additive['overlay']['cell']); assert overlay_cell is not None
        assert overlay.dbu == layout.dbu
        added_name = 'bgr_redundant_cuts_context_candidate'
        assert layout.cell(added_name) is None
        added = layout.create_cell(added_name); added.copy_tree(overlay_cell)
        assert structural_digest(added) == structural_digest(overlay_cell)
        top.insert(k.CellInstArray(added.cell_index(), k.Trans(331000,732000)))
        assert root_without(top, {added_name}) == original_root
        result['new_effective_bgr'] = effective_bgr(layout, top, additive['new_effective'], added_name)
        held = protected(top, target_names | {added_name})
        assert {n: v for n, v in held.items() if n != top.name} == {n: v for n, v in before.items() if n != top.name}
        assert top.bbox() == bbox
        output = args.output/'analog_pair_native.gds'
        # Old target-only descendants can become unreachable after copy_tree.
        # Serialize the exact reachable tree, not those obsolete auxiliary roots.
        clean = k.Layout(); clean.dbu = layout.dbu
        clean_top = clean.create_cell(top.name); clean_top.copy_tree(top)
        assert structural_digest(clean_top) == structural_digest(top)
        assert protected(clean_top, target_names | {added_name}) == held
        assert root_without(clean_top, {added_name}) == original_root
        clean.write(str(output))
        saved = k.Layout(); saved.read(str(output)); st = saved.cell(top.name)
        assert [c.name for c in saved.top_cells()] == [top.name]
        assert saved.dbu == layout.dbu and st.bbox() == bbox
        assert protected(st, target_names | {added_name}) == held
        assert root_without(st, {added_name}) == original_root
        assert structural_digest(saved.cell(added_name)) == structural_digest(overlay_cell)
        result['saved_effective_bgr'] = effective_bgr(saved, st, additive['new_effective'], added_name)
        for row, target, new, new_cell in targets:
            final_cell = saved.cell(target.name)
            equal_macro(new, new_cell, saved, final_cell)
            assert structural_digest(new_cell) == structural_digest(final_cell)
        assert all(sha(path) == digest for path, digest in inputs.items())
        result.update(status='passed isolated analog-pair hierarchy replacement',
                      GDS_sha256=sha(output), top_cell=top.name,
                      original_parent_sha256=contract['parent']['gds']['sha256'],
                      unchanged_cell_signatures=before,
                      top_definition_die_pad_map='passed exact preservation except one declared BGR cuts instance',
                      saved_hierarchy_and_geometry='passed')
    except Exception as exc:
        result.update(status='failed analog-pair preparation', error=repr(exc))
        raise
    finally:
        result['wall_s'] = time.monotonic()-start
        (args.output/'analysis.json').write_text(json.dumps(result, indent=2)+'\n')


if __name__ == '__main__':
    main()

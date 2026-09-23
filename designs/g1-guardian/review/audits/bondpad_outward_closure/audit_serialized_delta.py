#!/usr/bin/env python3
"""Independent actual-file inverse and closed-form pad-sweep geometry proof."""
import argparse
import json
import os
from pathlib import Path
import sys
import pya
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from place_closed_analog import region, sha, text_records
from build_candidate import signature, PARENT_SHA, TOP, PAD


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ('parent', 'candidate', 'output'):
        p.add_argument('--' + key, type=Path, required=True)
    a = p.parse_args()
    assert not a.output.exists() and len(os.sched_getaffinity(0)) == 1
    assert sha(a.parent) == PARENT_SHA
    meta = json.loads((a.candidate / 'analysis.json').read_text())
    source = a.candidate / 'pad_outward_native.gds'
    assert sha(source) == meta['GDS_sha256'] and meta['bridge_mode'].startswith('exact swept')
    old = pya.Layout(); old.read(str(a.parent)); new = pya.Layout(); new.read(str(source))
    ot, nt = old.top_cell(), new.top_cell()
    assert ot.name == nt.name == TOP and old.dbu == new.dbu == .001
    before, after = signature(old), signature(new)
    extra = 'bondpad_outward_5um_retained_metal'
    assert set(after) - set(before) == {extra} and not set(before) - set(after)
    assert all(after[name] == digest for name, digest in before.items() if name != TOP)
    assert text_records(old, ot) == text_records(new, nt)
    movement = {tuple(m['new_bbox_dbu']): m for m in meta['pad_moves']}
    layer_audits = []; inverse = []; expected_bridge = pya.Region()
    for inst in nt.each_inst():
        if inst.cell.name != PAD:
            continue
        b = inst.bbox(); move = movement[(b.left, b.bottom, b.right, b.top)]
        dx, dy = move['shift_dbu']; assert abs(dx) + abs(dy) == 5000 and dx * dy == 0
        new_outer = pya.Box(*move['new_bbox_dbu']); old_outer = pya.Box(*move['old_bbox_dbu'])
        new_inner = new_outer.enlarged(-4070); old_inner = old_outer.enlarged(-4070)
        # Independent closed form: swept outer rectangle minus intersection of
        # endpoint holes. No four-bar decomposition reused from the builder.
        expected_bridge |= pya.Region(old_outer + new_outer) - (pya.Region(old_inner) & pya.Region(new_inner))
        inverse.append((inst, pya.ICplxTrans(1, 0, False, -dx, -dy) * inst.cplx_trans))
    assert len(inverse) == 24
    observed_bridge = region(new, new.cell(extra), pya.LayerInfo(126, 0))
    assert (observed_bridge ^ expected_bridge).is_empty()
    # Negative controls: a single DBU removal/addition must be detected.
    first = meta['pad_moves'][0]; x, y = first['old_bbox_dbu'][:2]
    removal = pya.Region(pya.Box(x, y, x + 1, y + 1))
    addition = pya.Region(pya.Box(200000, 200000, 200001, 200001))
    assert not ((observed_bridge - removal) ^ expected_bridge).is_empty()
    assert not ((observed_bridge | addition) ^ expected_bridge).is_empty()
    all_layers = {(old.get_info(k).layer, old.get_info(k).datatype) for k in old.layer_indexes()}
    all_layers |= {(new.get_info(k).layer, new.get_info(k).datatype) for k in new.layer_indexes()}
    # Local native-cell signatures above establish every untouched layer;
    # compare the five changed flattened layers explicitly.
    for layer in (9, 41, 126, 133, 134):
        left, right = region(old, ot, pya.LayerInfo(layer, 0)), region(new, nt, pya.LayerInfo(layer, 0))
        added, removed = right - left, left - right
        wanted = meta['layer_delta'][str(layer) + '/0']
        assert added.area() * 1e-6 == wanted['added_area_um2'] and removed.area() * 1e-6 == wanted['removed_area_um2']
        layer_audits.append(dict(layer=layer, added_area_um2=added.area() * 1e-6, removed_area_um2=removed.area() * 1e-6))
    for inst, transform in inverse:
        inst.cplx_trans = transform
    bridge, = [i for i in nt.each_inst() if i.cell.name == extra]
    bridge.delete(); new.delete_cell(new.cell(extra).cell_index())
    assert signature(new) == before
    result = dict(status='passed independent serialized inverse and swept-frame geometry',
                  parent_GDS_sha256=PARENT_SHA, GDS_sha256=sha(source), script_sha256=sha(Path(__file__)),
                  signature_helper_sha256=sha(Path(__file__).with_name('build_candidate.py')),
                  original_cells=len(before), original_cell_signatures=before,
                  candidate_cell_signatures=after, layer_delta=layer_audits,
                  checks=dict(all_original_cells_unchanged='passed', all_recursive_texts_unchanged='passed',
                              exactly_24_5um_transforms='passed', actual_file_inverse_exact='passed',
                              independent_closed_form_sweep='passed', one_DBU_removal_rejected='passed',
                              one_DBU_addition_rejected='passed'),
                  not_run=['stock or electrical acceptance in this audit'],
                  not_applicable=['new circuit devices', 'model/rule edits'])
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2) + '\n'); print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()

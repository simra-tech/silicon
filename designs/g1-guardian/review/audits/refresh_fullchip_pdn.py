#!/usr/bin/env python3
"""Replace only proved direct core routes, retaining the native IO hierarchy."""
import argparse
import json
import os
from pathlib import Path
import pya
from place_closed_analog import region, text_records, sha


def signature(top):
    return sorted((i.cell.name, str(i.cplx_trans)) for i in top.each_inst())


def direct_texts(layout, top):
    return sorted((str(i), str(s.text)) for i in layout.layer_infos()
                  for s in top.shapes(layout.layer(i)).each() if s.is_text())


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('native', 'previous-core', 'next-core', 'output'):
        p.add_argument('--'+name, type=Path, required=True)
    a = p.parse_args()
    assert not a.output.exists() and len(os.sched_getaffinity(0)) == 1 and pya.__version__ == '0.30.9'
    metadata = [json.loads((d/'analysis.json').read_text()) for d in (a.native, a.previous_core, a.next_core)]
    native, previous, following = metadata
    paths = [a.native/'fullchip_instances_unrouted.gds', a.previous_core/'decap_pdn_core.gds', a.next_core/'decap_pdn_core.gds']
    assert all(m['status'].startswith('passed') and sha(f) == m['GDS_sha256'] for m, f in zip(metadata, paths))
    assert native['core_GDS_sha256'] == previous['GDS_sha256']
    assert previous['parent_GDS_sha256'] == following['parent_GDS_sha256']
    assert previous['placement_sha256'] == following['placement_sha256']
    assert previous['M1_M2_pin_pairs_connected_to_correct_ring'] == following['M1_M2_pin_pairs_connected_to_correct_ring'] == 9324
    a.output.mkdir(parents=True); (a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    layouts = []
    for path in paths:
        layout = pya.Layout(); layout.read(str(path)); assert layout.dbu == .001
        layouts.append(layout)
    ly, old, new = layouts
    top, ot, nt = [l.top_cell() for l in layouts]
    instances = signature(top)
    assert len(instances) == 4904 and len(signature(ot)) == 4674 and signature(ot) == signature(nt)
    # All source-cell trees, not just their names/placements, remain exact.
    seen = set()
    for inst in ot.each_inst():
        cell = inst.cell
        if cell.name in seen: continue
        peer = new.cell(cell.name); assert peer is not None
        assert text_records(old, cell) == text_records(new, peer)
        for info in set(old.layer_infos()+new.layer_infos()):
            assert (region(old, cell, info)^region(new, peer, info)).is_empty()
        seen.add(cell.name)
    assert direct_texts(ly, top) == direct_texts(old, ot)
    changed = []
    for info in set(ly.layer_infos()+old.layer_infos()):
        actual = pya.Region(top.shapes(ly.layer(info)))
        expected = pya.Region(ot.shapes(old.layer(info)))
        assert (actual^expected).is_empty(), str(info)
    before = {str(i): region(ly, top, i) for i in ly.layer_infos()}
    texts = text_records(ly, top)
    for info in list(ly.layer_infos()): top.shapes(ly.layer(info)).clear()
    for info in new.layer_infos():
        for shape in nt.shapes(new.layer(info)).each(): top.shapes(ly.layer(info)).insert(shape)
    assert direct_texts(old, ot) == direct_texts(new, nt)
    for info in ly.layer_infos():
        old_direct = pya.Region(ot.shapes(old.layer(info)))
        new_direct = pya.Region(nt.shapes(new.layer(info)))
        # Compare the retained native hierarchy plus the exact replacement,
        # including overlapping shapes; do not use subtraction to erase a
        # native polygon beneath an old route.
        expected = (before.get(str(info), pya.Region())-old_direct)+new_direct
        actual = region(ly, top, info)
        # Any original native overlap belongs to both core revisions and must
        # remain: exact child preservation above proves that extra coverage.
        removed = old_direct-new_direct
        child_overlap = pya.Region()
        if not removed.is_empty():
            cache = {}
            for inst in ot.each_inst():
                key = inst.cell_index
                if key not in cache: cache[key] = region(old, inst.cell, info)
                child_overlap += cache[key].transformed(inst.cplx_trans)&removed
        assert (actual^(expected+child_overlap)).is_empty(), str(info)
        if not (old_direct^new_direct).is_empty(): changed.append(str(info))
    assert text_records(ly, top) == texts and signature(top) == instances
    output = a.output/'fullchip_instances_unrouted.gds'; ly.write(str(output))
    saved = pya.Layout(); saved.read(str(output)); st = saved.top_cell()
    assert text_records(saved, st) == texts and signature(st) == instances
    for info in ly.layer_infos(): assert (region(ly, top, info)^region(saved, st, info)).is_empty()
    result = dict(native)
    result.update(status='passed source-preserving full native PDN route refresh; unrouted signals',
                  GDS_sha256=sha(output), core_GDS_sha256=following['GDS_sha256'],
                  previous_native_GDS_sha256=sha(paths[0]), previous_core_GDS_sha256=sha(paths[1]),
                  script_sha256=sha(Path(__file__)), native_cell_trees_exact='passed',
                  direct_route_layers_changed=changed, saved_roundtrip='passed',
                  not_run=['new PDN/native IO combined connectivity', 'SENSE overlay merge',
                           'signal routes', 'stock DRC/LVS/PEX/currentIR/EM/density/antenna', 'adoption'])
    (a.output/'analysis.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='native_added_instances'}, indent=2))


if __name__ == '__main__':
    main()

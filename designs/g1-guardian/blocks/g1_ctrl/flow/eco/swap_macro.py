#!/usr/bin/env python3
"""Swap the g1_digital macro inside the chip GDS, keeping the instance and all
top-level geometry.

  swap_macro.py --chip <chip.gds> --cell __rz_port_text_000_retained_g1_digital \
      --macro <new g1_digital.gds> [--macro-top g1_digital] \
      [--netlist <new nl.v> --def <new def>] --out <chip_swapped.gds> --report <report.json>

Steps
 1. The target cell's own subtree is pruned (sub-cells used nowhere else are
    deleted) and its shapes and instances are cleared. The cell itself, its
    name and every instance of it in the chip (placement, orientation) stay.
 2. The new macro's content is copied into the emptied cell. A sub-cell of the
    new macro whose name already exists in the chip is reused only if its
    flattened geometry and texts are identical; otherwise it is created as
    eco_<name>. Nothing outside the target cell is touched.
 3. Port-text normalisation as in the chip of record
    (review/audits/io_tap_closure/physical_source/integration_purefill/
    normalize_rz_port_text.py): top-level labels of macro pins that have no
    label in the chip's current cell (pins the chip leaves unconnected) are
    removed; with --netlist/--def, every instance whose output pin is left
    unconnected in the netlist (CTS dummy clock loads) and whose master is in
    --strip-masters gets an instance-local clone of its cell without that pin's
    label (__eco_port_text_<n>_<master>), as the chip did for its 29
    sg13g2_inv_{2,4,8} clock loads. sg13g2_buf_4 was added on 2026-09-25: in the r3
    candidate, three buf_4 dummy loads left synthetic X pins in projected LVS. inv_1 and
    buf_8 dummy loads have never produced a pin. Projected LVS must show exactly 22 pins.
 4. Checks written to the report: XOR of the old and new cell on every pin layer
    (x/2); new TopMetal1/TopMetal2 drawing inside the old one (the chip's TM1
    stripes cross the macro and the chip's TM fill surrounds its TM shapes); on
    every label layer (x/25, as text sets), bounding box, and the unchanged
    remainder of the chip (XOR of the whole chip with the target cell emptied
    in both, all layers). swapped = pin XORs empty, TopMetal inside old, and remainder
    unchanged.
The chip DRC/LVS/antenna suite must then be re-run on the output.
"""
import argparse
import hashlib
import json
import re

import klayout.db as db

PIN_LAYERS = [(8, 2), (10, 2), (30, 2), (50, 2), (67, 2), (126, 2), (134, 2)]
TEXT_LAYERS = [(8, 25), (10, 25), (30, 25), (50, 25), (67, 25), (126, 25), (134, 25)]
TM_LAYERS = [(126, 0), (134, 0)]
OUT_PINS = {'Y', 'X', 'Q', 'Q_N'}


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def region(ly, cell, ld, top_only=False):
    li = ly.find_layer(*ld)
    if li is None:
        return db.Region()
    return db.Region(cell.shapes(li) if top_only else cell.begin_shapes_rec(li)).merged()


def texts(ly, cell, ld, top_only=True):
    li = ly.find_layer(*ld)
    if li is None:
        return set()
    if top_only:
        return {(s.text.string, s.text.x, s.text.y) for s in cell.shapes(li).each() if s.is_text()}
    out = set()
    it = cell.begin_shapes_rec(li)
    while not it.at_end():
        s = it.shape()
        if s.is_text():
            t = s.text.transformed(it.trans())
            out.add((t.string, t.x, t.y))
        it.next()
    return out


def cell_signature(ly, cell):
    sig = []
    for li in ly.layer_indexes():
        info = ly.get_info(li)
        r = db.Region(cell.begin_shapes_rec(li)).merged()
        if not r.is_empty():
            sig.append(((info.layer, info.datatype), sorted(str(p) for p in r.each())))
        t = texts(ly, cell, (info.layer, info.datatype), top_only=False)
        if t:
            sig.append((('T', info.layer, info.datatype), sorted(t)))
    return sig


def floating_outputs(nl_path, def_path, masters):
    """{(master, x, y, orient): [pin]} for instances with an unconnected output."""
    text = open(nl_path).read()
    inst_re = re.compile(r'^\s*(sg13g2_\w+)\s+(\S+)\s*\((.*?)\);', re.S | re.M)
    pins = re.compile(r'\.(\w+)\(')
    want = {}
    for m in inst_re.finditer(text):
        cell, name, body = m.groups()
        if cell not in masters:
            continue
        connected = set(pins.findall(body))
        # output pin of the master: Y for inverters, X for buffers (other masters not handled)
        out_pin = 'Y' if cell.startswith('sg13g2_inv') else 'X' if cell.startswith('sg13g2_buf') else None
        missing = [out_pin] if out_pin and out_pin not in connected else []
        if missing:
            want[name] = (cell, missing)
    comp = re.compile(r'^\s*- (\S+) (\S+) .*?\+ (?:PLACED|FIXED) \( (-?\d+) (-?\d+) \) (\S+)', re.M)
    out = {}
    for m in comp.finditer(open(def_path).read()):
        name, cell, x, y, o = m.groups()
        if name in want:
            out[name] = (cell, int(x), int(y), o, want[name][1])
    assert len(out) == len(want), 'instances missing from DEF'
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--chip', required=True)
    ap.add_argument('--cell', required=True)
    ap.add_argument('--macro', required=True)
    ap.add_argument('--macro-top', default='g1_digital')
    ap.add_argument('--netlist')
    ap.add_argument('--def', dest='deff')
    ap.add_argument('--strip-masters', default='sg13g2_inv_2,sg13g2_inv_4,sg13g2_inv_8,sg13g2_buf_4')
    ap.add_argument('--out', required=True)
    ap.add_argument('--report', required=True)
    a = ap.parse_args()
    rep = {'chip': a.chip, 'chip_sha256': sha(a.chip), 'macro': a.macro, 'macro_sha256': sha(a.macro),
           'cell': a.cell}

    chip = db.Layout(); chip.read(a.chip)
    ref = db.Layout(); ref.read(a.chip)          # untouched copy for the checks
    src = db.Layout(); src.read(a.macro)
    assert abs(chip.dbu - src.dbu) < 1e-12
    tgt = chip.cell(a.cell); stop = src.cell(a.macro_top)
    assert tgt is not None and stop is not None
    rep['instances_of_target'] = [str(i.dcplx_trans) for p in tgt.each_parent_cell()
                                  for i in chip.cell(p).each_inst() if i.cell_index == tgt.cell_index()]
    old_bbox = tgt.bbox()
    old_labels = {ld: texts(ref, ref.cell(a.cell), ld) for ld in TEXT_LAYERS}

    # 1. empty the target cell
    names_before = {c.name for c in chip.each_cell()}
    tgt.prune_subcells()
    tgt.clear()
    rep['cells_deleted'] = len(names_before - {c.name for c in chip.each_cell()})

    # 2. copy the new macro, reusing identical same-name library cells
    reused, renamed, created = [], [], []
    cm = db.CellMapping()
    cm.for_single_cell(chip, tgt.cell_index(), src, stop.cell_index())
    for ci in sorted(stop.called_cells()):
        sc = src.cell(ci)
        ex = chip.cell(sc.name)
        if ex is not None and cell_signature(chip, ex) == cell_signature(src, sc):
            cm.map(ci, ex.cell_index()); reused.append(sc.name)
        else:
            name = sc.name if ex is None else 'eco_' + sc.name
            assert chip.cell(name) is None, name
            nc = chip.create_cell(name)
            cm.map(ci, nc.cell_index())
            (created if ex is None else renamed).append(name)
    new_cells = set(created + renamed)
    lmap = {}
    for li in src.layer_indexes():
        info = src.get_info(li)
        lmap[li] = chip.layer(info.layer, info.datatype)
    for ci in [stop.cell_index()] + sorted(stop.called_cells()):
        sc = src.cell(ci)
        dc = chip.cell(cm.cell_mapping(ci))
        if ci != stop.cell_index() and dc.name not in new_cells:
            continue
        for li, dli in lmap.items():
            dc.shapes(dli).insert(sc.shapes(li))
        for inst in sc.each_inst():
            ia = inst.cell_inst.dup()
            ia.cell_index = cm.cell_mapping(inst.cell_index)
            dc.insert(ia)
    rep['subcells_reused'], rep['subcells_renamed'], rep['subcells_created'] = len(reused), renamed, len(created)

    # 3. port-text normalisation
    removed = []
    for ld in TEXT_LAYERS:
        li = chip.find_layer(*ld)
        if li is None:
            continue
        for s in list(tgt.shapes(li).each()):
            if s.is_text() and not any(t[0] == s.text.string for t in old_labels[ld]):
                removed.append((ld, s.text.string)); tgt.shapes(li).erase(s)
    rep['top_labels_removed'] = removed
    clones = []
    if a.netlist and a.deff:
        masters = set(a.strip_masters.split(','))
        flo = floating_outputs(a.netlist, a.deff, masters)
        prb = chip.layer(189, 4)            # prBoundary: the cell outline the DEF location refers to
        by_pos = {}
        for name, (cell, x, y, o, pins) in flo.items():
            by_pos.setdefault(cell, []).append((name, x, y, pins))
        for inst in list(tgt.each_inst()):
            cname = chip.cell(inst.cell_index).name
            if cname.startswith('eco_'):
                cname = cname[4:]
            if cname not in by_pos:
                continue
            b = inst.bbox_per_layer(prb)
            hit = [r for r in by_pos[cname] if r[1] == b.left and r[2] == b.bottom]
            if not hit:
                continue
            assert len(hit) == 1
            name, _, _, pins = hit[0]
            base = chip.cell(inst.cell_index)
            cl = chip.create_cell('__eco_port_text_%03d_%s' % (len(clones), cname))
            cl.copy_shapes(base)
            n_erased = 0
            for li in chip.layer_indexes():
                for s in list(cl.shapes(li).each()):
                    if s.is_text() and s.text.string in pins:
                        cl.shapes(li).erase(s); n_erased += 1
            assert n_erased >= 1, (name, cname)
            ia = inst.cell_inst.dup(); ia.cell_index = cl.cell_index(); inst.cell_inst = ia
            clones.append({'instance': name, 'master': cname, 'labels_removed': n_erased})
        rep['floating_output_instances'] = len(flo)
        orphans = [c for c in chip.each_cell() if c.name in new_cells and c.parent_cells() == 0]
        rep['orphans_deleted_after_cloning'] = sorted(c.name for c in orphans)
        for c in orphans:
            chip.delete_cell(c.cell_index())
    rep['instance_label_clones'] = clones

    # 4. checks
    new = chip.cell(a.cell); old = ref.cell(a.cell)
    chk = {'bbox_equal': new.bbox() == old_bbox, 'bbox': str(new.bbox())}
    for ld in PIN_LAYERS:
        x = region(ref, old, ld, True) ^ region(chip, new, ld, True)   # macro pins: top level of the cell
        chk['xor_%d_%d' % ld] = x.count()
    for ld in TM_LAYERS:   # new TopMetal must lie inside the old one (chip TM1 stripes and TM fill)
        chk['tm_outside_old_%d_%d' % ld] = (region(chip, new, ld) - region(ref, old, ld)).count()
    allx = {}
    for li in ref.layer_indexes():
        info = ref.get_info(li)
        n = (region(ref, old, (info.layer, info.datatype)) ^ region(chip, new, (info.layer, info.datatype))).count()
        if n:
            allx[str(info)] = n
    chk['cell_xor_all_layers_nonempty'] = allx
    do, dn = texts(ref, old, (8, 25), top_only=False), texts(chip, new, (8, 25), top_only=False)
    chk['deep_metal1_labels'] = {'old': len(do), 'new': len(dn), 'only_old': len(do - dn), 'only_new': len(dn - do)}      # informational: a new macro differs inside
    for ld in TEXT_LAYERS:
        o, n = old_labels[ld], texts(chip, new, ld)
        chk['labels_%d_%d' % ld] = {'only_old': sorted(o - n), 'only_new': sorted(n - o)}
    # remainder of the chip: empty the target in both layouts and XOR everything
    ref.cell(a.cell).prune_subcells(); ref.cell(a.cell).clear()
    tops_a, tops_b = [c.name for c in ref.top_cells()], [c.name for c in chip.top_cells()]
    assert len(tops_b) == 1 and tops_b[0] in tops_a, (tops_a, tops_b)
    top_a, top_b = ref.cell(tops_b[0]), chip.cell(tops_b[0])
    diff = {}
    for li in ref.layer_indexes():
        info = ref.get_info(li)
        la = db.Region(top_a.begin_shapes_rec(li))
        lb_i = chip.find_layer(info.layer, info.datatype)
        cellsb = chip.cell(a.cell)
        # region of chip without the target cell
        it = top_b.begin_shapes_rec(lb_i)
        it.unselect_cells([cellsb.cell_index()])
        lb = db.Region(it)
        n = (la ^ lb).count()
        if n:
            diff[str(info)] = n
    chk['remainder_xor_nonempty_layers'] = diff
    pin_ok = all(v == 0 for k, v in chk.items() if k.startswith(('xor_', 'tm_outside_old_')))
    rep['checks'] = chk
    rep['swapped'] = bool(pin_ok and chk['bbox_equal'] and not diff)
    opt = db.SaveLayoutOptions(); opt.gds2_write_timestamps = False
    chip.write(a.out, opt)
    rep['out'] = a.out; rep['out_sha256'] = sha(a.out)
    json.dump(rep, open(a.report, 'w'), indent=1, default=str)
    print(json.dumps({k: rep[k] for k in ('swapped', 'cells_deleted', 'subcells_reused', 'subcells_renamed',
                                          'subcells_created', 'top_labels_removed')}, default=str))
    print(json.dumps({k: v for k, v in chk.items() if not k.startswith('labels')}, default=str))
    print('label differences', {k: v for k, v in chk.items() if k.startswith('labels') and (v['only_old'] or v['only_new'])})
    print('clones', len(clones))


if __name__ == '__main__':
    main()

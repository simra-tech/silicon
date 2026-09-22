#!/usr/bin/env python3
"""Two frozen-contact metal-return controls, not a routed bank or stock check."""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import pya

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
LAYOUT = HERE.parent
SOURCE = LAYOUT.parent/'sim/qualification/candidates/bgr_loop24_qref4_r253p465_hv06/bgr_loop24_qref4_r253p465_hv06.spice'
PACK = ROOT/'designs/g1-guardian/review/audits/coordinated-bbox-pack-586-20260922-r1.json'
CONTACT = ROOT/'build/scratch/bgr-hbt-contact-prototypes-20260922-r1'
STOCK = ROOT/'build/scratch/bgr-second-stock-20260922-r1/summary.json'
PDK = Path('/foss/pdks/ihp-sg13g2')
PINNED = {
    SOURCE: '586ffb58b6af31c77a2e7cbcb83b173ffa4713ec62401da30901c5a7e606283b',
    PACK: '2663805a5180a1961850c1068b0c1c3615c010cd2ec47d38a228d65dde4800cb',
    CONTACT/'manifest.json': 'bcdb1f01f4287db750935896756b5947db22898612a9bb77b229f6f0553d4fc2',
    STOCK: '42d35eaf4daec387389fc0e027e1db271f542536d850f4b01524f5d5a496ae48',
    LAYOUT/'coordinated_586/build_hbt_contact_prototypes.py': '1fdc4be4be7cbcc0891aab1403c7f4024a4dc301bfae2ce2cf6592e15118ebdd',
    LAYOUT/'g1_bgr_layout.py': 'dee7f8fa5ab94165946e342625ed72c00e6a174592bb47a0af9f9054b8ce171e',
}
LAYERS = {'M1': (8, 0), 'Via1': (19, 0), 'M2': (10, 0), 'Via2': (29, 0), 'M3': (30, 0)}
REMOVE = [
    ('M1', [9580, 6970, 10420, 7270]),
    ('M1', [9640, 6970, 10360, 7270]),
    ('Via1', [9695, 7025, 9885, 7215]),
    ('Via1', [10115, 7025, 10305, 7215]),
    ('M2', [9640, 6970, 10360, 7270]),
    ('M2', [9640, 6760, 10360, 9760]),
]


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p, value): p.write_text(json.dumps(value, indent=2)+'\n')


def region(cell, li):
    result = pya.Region(cell.begin_shapes_rec(li)); result.flatten()
    return result


def records(cell):
    result = []
    for li in cell.layout().layer_indices():
        info = cell.layout().get_info(li)
        for shape in cell.shapes(li).each():
            result.append((info.layer, info.datatype, shape.to_s()))
    return collections.Counter(result)


def native_snapshot(top):
    # Snapshot every recursive layer of every direct native child. Top-level
    # added contacts are intentionally excluded from this immutable reference.
    rows = []
    for inst in top.each_inst():
        cell = inst.cell
        rows.append((cell.name, inst.to_s(), {
            li: region(cell, li) for li in top.layout().layer_indices()}))
    assert len(rows) == 1, 'exactly one unchanged native PCell instance'
    return rows


def terminal_graph(top, distinct_cb, separated):
    ly = top.layout(); polygons = {}; regions = {}; parent = []
    for name in ('M1', 'M2', 'M3'):
        regions[name] = region(top, ly.layer(*LAYERS[name])).merged()
        polygons[name] = []
        for poly in regions[name].each():
            index = len(parent); parent.append(index)
            polygons[name].append((index, poly))
    def find(index):
        while parent[index] != index:
            parent[index] = parent[parent[index]]; index = parent[index]
        return index
    errors = []
    for via, low, high in [('Via1', 'M1', 'M2'), ('Via2', 'M2', 'M3')]:
        for cut in region(top, ly.layer(*LAYERS[via])).each():
            hits = []
            for name in (low, high):
                hit = [i for i, p in polygons[name] if not (pya.Region(p) & pya.Region(cut)).is_empty()]
                if len(hit) != 1 or not (pya.Region(cut)-regions[name]).is_empty():
                    errors.append(dict(check='via_landing', via=via, layer=name, hits=hit))
                hits += hit
            for i in hits[1:]: parent[find(i)] = find(hits[0])
    seeds = {'C': ('M1', [9250,11200]), 'B': ('M1', [10600,8500]),
             'E': ('M2', [10000,10000]), 'S': ('M1', [12900,10200])}
    components = {}
    for name, (layer, xy) in seeds.items():
        hits = [i for i,p in polygons[layer] if p.inside(pya.Point(*xy))]
        if len(hits) != 1:
            errors.append(dict(check='terminal_seed', terminal=name, hits=hits))
        else: components[name] = find(hits[0])
    if len(components) == 4:
        expected = {('C','B'): not distinct_cb, ('E','S'): not separated,
                    ('C','E'): False, ('C','S'): False, ('B','E'): False, ('B','S'): False}
        for pair, equal in expected.items():
            if (components[pair[0]] == components[pair[1]]) != equal:
                errors.append(dict(check='terminal_partition', pair=pair, expected_connected=equal))
    return dict(status='passed' if not errors else 'failed', errors=errors,
                terminal_components=components, physical_components=len({find(i) for i in range(len(parent))}),
                labels_implicitly_connected=False, substrate_conductivity='not evaluated')


def variant(proto, out):
    path = CONTACT/(proto['name']+'.gds')
    ly = pya.Layout(); ly.read(str(path)); top = ly.top_cell()
    assert ly.dbu == .001
    before = records(top)
    native = native_snapshot(top)
    all_layers = {li: region(top, li) for li in ly.layer_indices()}
    original = terminal_graph(top, proto['name'].endswith('02'), False)
    assert original['status'] == 'passed', original
    removed = []
    for layer, coords in REMOVE:
        li = ly.layer(*LAYERS[layer]); target = pya.Box(*coords)
        matches = [s for s in top.shapes(li).each() if s.is_box() and s.box == target]
        assert len(matches) == 1, (layer, coords, len(matches))
        info = ly.get_info(li)
        removed.append((info.layer, info.datatype, matches[0].to_s()))
        matches[0].delete()
    assert records(top) == before-collections.Counter(removed)
    after = terminal_graph(top, proto['name'].endswith('02'), True)
    assert after['status'] == 'passed', after
    children = list(top.each_inst())
    native_checks = []
    for (name, instance, layers), current in zip(native, children):
        assert current.cell.name == name and current.to_s() == instance
        native_checks += [(region(current.cell, li)^r).is_empty() for li,r in layers.items()]
    assert all(native_checks)
    xor = []
    for li, r in all_layers.items():
        info = ly.get_info(li); delta = region(top, li)^r
        changed = not delta.is_empty()
        if (info.layer, info.datatype) not in (LAYERS['M1'], LAYERS['M2'], LAYERS['Via1']):
            assert not changed, str(info)
        xor.append(dict(layer=info.layer, datatype=info.datatype, xor_area_dbu2=delta.area(), changed=changed))
    name = proto['name'].replace('proto', 'return_control')
    top.name = name
    gds = out/(name+'.gds'); ly.write(str(gds))
    # Read back serialized geometry; no qualification by an in-memory-only graph.
    loaded = pya.Layout(); loaded.read(str(gds)); saved = loaded.top_cell()
    assert records(saved) == records(top)
    saved_graph = terminal_graph(saved, proto['name'].endswith('02'), True)
    assert saved_graph == after
    for li in ly.layer_indices():
        other = loaded.layer(ly.get_info(li))
        assert (region(saved, other)^region(top, li)).is_empty()
    f = proto['source_line'].split(); ports = list(dict.fromkeys(f[1:5]))
    cdl = out/(name+'.cdl')
    cdl.write_text('.subckt '+name+' '+' '.join(ports)+'\nQUNIT '+' '.join(f[1:])+'\n.ends '+name+'\n')
    return dict(name=name, status='passed preparation', source_line=proto['source_line'],
                represented_instances=proto['represented_instances'], original_gds_sha256=sha(path),
                removed_top_level_shapes=[dict(layer=a, datatype=b, shape=c) for a,b,c in removed],
                all_other_top_shapes_texts_identical=True, native_all_layers_xor_zero=all(native_checks),
                flattened_layer_xor=xor, original_graph=original, revised_saved_graph=saved_graph,
                gds_sha256=sha(gds), cdl_sha256=sha(cdl), stock_DRC_LVS='not run',
                physical_star='not run; deliberately unjoined return control')


def ledger(out, manifest):
    source = {l.split()[0]: l for l in SOURCE.read_text().splitlines() if l.startswith(('XM','XR','XQ'))}
    pack = json.loads(PACK.read_text())['BGR_devices']
    assert len(source) == len(pack) == 1036
    assert all(source[d['name']] == d['source_line'] for d in pack)
    rows = [d for d in pack if d['kind'] == 'npn13G2']
    assert len(rows) == 301
    assert {n for d in rows for n in d['source_line'].split()[1:5]} == {'vss','vbe','c2','dvbe','vd1','vd2','b1b','vbe3'}
    functional = [d for d in rows if d['source_line'].split()[3] == 'vss' and len(set(d['source_line'].split()[1:5])) > 1]
    counts = collections.Counter(d['original'] for d in functional)
    assert counts == {'XQ56':24, 'XQ60':4, 'XQ62':24, 'XQ67':24}
    dummy = [d for d in rows if set(d['source_line'].split()[1:5]) == {'vss'}]
    assert len(dummy) == 9 and {d['name'] for d in dummy} == set(manifest['prototypes'][0]['represented_instances'])
    # Do not mutate even the in-memory original pack records when adding roles.
    roles = {d['name']: ('general_guard_and_dummy' if d in dummy else
                       'emitter_'+d['original'] if d in functional else
                       'source_'+d['source_line'].split()[3]) for d in rows}
    groups = collections.defaultdict(list)
    for d in pack: groups[d['original']].append(d)
    centroids = {}
    for name, ds in groups.items():
        if len(ds) <= 1: continue
        centroids[name] = dict(count=len(ds), center_um=[
            sum((d['bbox_um'][i]+d['bbox_um'][i+2])/2 for d in ds)/len(ds) for i in (0,1)])
    assert len(centroids) == 50
    result = dict(status='passed source and fixed-ledger checks; geometry placement not run',
                  source_sha256=sha(SOURCE), pack_sha256=sha(PACK), hbt_count=301,
                  source_nets=sorted({n for d in rows for n in d['source_line'].split()[1:5]}),
                  functional_vss_emitter_counts=dict(counts), unchanged_dummy_names=[d['name'] for d in dummy],
                  all_50_macro_replication_centroids=centroids, fixed_devices=rows,
                  emitter_route_roles=roles, source_net_renaming=False,
                  star_connection_and_full_bank_geometry='not run')
    dump(out/'bank_source_placement_ledger.json', result)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--output', required=True, type=Path); a = ap.parse_args()
    assert a.output.is_dir() and not (a.output/'controls.json').exists()
    assert pya.__version__ == '0.30.9'
    assert (PDK/'COMMIT').read_text().strip() == '84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
    for p,h in PINNED.items(): assert sha(p) == h, str(p)
    assert json.loads(STOCK.read_text())['status'] == 'passed'
    manifest = json.loads((CONTACT/'manifest.json').read_text())
    inputs = dict(PINNED)
    for proto in manifest['prototypes']:
        p = CONTACT/(proto['name']+'.gds'); assert sha(p) == proto['gds_sha256']
        inputs[p] = sha(p)
    ledger(a.output, manifest)
    result = dict(status='running', variants=[], inputs={str(p.relative_to(ROOT)):sha(p) for p in inputs},
                  script_sha256=sha(Path(__file__)), klayout=pya.__version__,
                  pdk_commit=(PDK/'COMMIT').read_text().strip(), seed='not applicable',
                  full_bank_stock_analog='not run')
    dump(a.output/'controls.json', result)
    for proto in manifest['prototypes'][1:3]:
        result['variants'].append(variant(proto, a.output)); dump(a.output/'controls.json', result)
    for p,h in inputs.items(): assert sha(p) == h
    result['status'] = 'passed two contact and source-placement controls'
    result['artifacts'] = {p.name:sha(p) for p in a.output.iterdir() if p.suffix in ('.gds','.cdl') or p.name == 'bank_source_placement_ledger.json'}
    dump(a.output/'controls.json', result); print(json.dumps(result, indent=2))


if __name__ == '__main__': main()

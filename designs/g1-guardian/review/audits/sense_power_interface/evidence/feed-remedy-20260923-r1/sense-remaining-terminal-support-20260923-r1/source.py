#!/usr/bin/env python3
"""Read native support sets for 171 terminals; no model attachment selected."""
import argparse
import collections
import gzip
import json
import os
from pathlib import Path
import time
import klayout.db as kdb
import extract_sense_contact_topology as mesh


def point(values): return kdb.Point(*(round(v*1000) for v in values))


def polygon_record(polygon):
    return dict(hull_dbu=[[p.x,p.y] for p in polygon.each_point_hull()],
                holes_dbu=[[[p.x,p.y] for p in polygon.each_point_hole(i)] for i in range(polygon.holes())],
                area_dbu2=polygon.area())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('ledger','classification','footprints','output'):
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args(); assert not args.output.exists()
    assert len(os.sched_getaffinity(0)) == 1 and kdb.__version__ == '0.30.9'
    sha, dump = mesh.engine.base.sha, mesh.engine.base.dump
    ledger = json.loads(args.ledger.read_text()); footprints = json.loads(args.footprints.read_text())
    classification = json.loads((args.classification/'summary.json').read_text())
    assert classification['status'] == 'passed geometry classification; unresolved model boundaries retained'
    assert classification['unclassified_count'] == 0
    assert footprints['classification_summary_sha256'] == sha(args.classification/'summary.json')
    assert footprints['ledger_sha256'] == sha(args.ledger) == classification['ledger_sha256']
    contacts = json.loads(gzip.decompress((args.classification/'contacts.json.gz').read_bytes()))
    assert sha(args.classification/'contacts.json.gz') == classification['contact_ledger_sha256']
    base = mesh.GM4/'ring-r8-evidence-20260922-r1'
    gds = base/'sense-ring-routing-20260922-r8a/g1_sense_physical.gds'
    reference = base/'sense-ring-reference-20260922-r8a/manifest.json'
    source = mesh.GM4.parents[1]/'reports/resume-server-20260922/gm4comp3-qualified-source.spice'
    assert sha(reference) == ledger['reference_manifest_sha256']
    assert sha(gds) == ledger['GDS_sha256'] == footprints['GDS_sha256'] == classification['GDS_sha256']
    assert sha(source) == ledger['source_sha256'] == footprints['source_sha256'] == classification['source_sha256']
    args.output.mkdir(parents=True); (args.output/'source.py').write_bytes(Path(__file__).read_bytes())
    result = dict(status='running support geometry only', source_sha256=sha(source), GDS_sha256=sha(gds),
                  reference_sha256=sha(reference), ledger_sha256=sha(args.ledger), script_sha256=sha(Path(__file__)),
                  classification_sha256=sha(args.classification/'summary.json'),
                  contact_catalog_sha256=sha(args.footprints), model_attachment='not qualified', adoption='not run')
    start = time.monotonic()
    try:
        layout = kdb.Layout(); layout.read(str(gds)); cell = layout.cell('g1_sense_physical')
        regions = {name: mesh.materialize(cell,pair) for name,pair in mesh.engine.PAIRS.items()}
        hold = mesh.native_graph(regions); native, layers = hold[1:]
        names = collections.defaultdict(set)
        for footprint in footprints['footprints']:
            net = native.probe_net(layers['M1'], kdb.Box(*footprint['bbox_dbu']).center()); assert net is not None
            names[net.cluster_id].add(footprint['source_net'])
        metal_by_layer = {p[0]:n for n,p in mesh.engine.PAIRS.items() if n not in mesh.engine.CUTS}
        for slot in ledger['slots']:
            for witness in slot.get('witnesses',[]):
                if witness['layer'] not in metal_by_layer: continue
                net = native.probe_net(layers[metal_by_layer[witness['layer']]], point(witness['point_um']))
                assert net is not None; names[net.cluster_id].add(slot['source_net'])
        assert len(names) == 134 and all(len(v)==1 for v in names.values())
        def metal_net(layer, p):
            net = native.probe_net(layers[layer],p); assert net is not None and net.cluster_id in names
            return next(iter(names[net.cluster_id]))
        active, poly = mesh.materialize(cell,(1,0)), mesh.materialize(cell,(5,0))
        wells = list(mesh.materialize(cell,(31,0)).each())
        psd = mesh.materialize(cell,(14,0))
        ids = {tuple(r['bbox_dbu']):r['id'] for r in footprints['footprints']}
        supports = collections.defaultdict(list)
        for contact in contacts:
            if 'tap' not in contact['classification']: continue
            box = kdb.Box(*contact['bbox_dbu']); shape = kdb.Region(box)
            members = [i for i,w in enumerate(wells) if w.inside(box.center())]
            if members:
                assert len(members)==1 and contact['source_net']=='vdd'
                assert (shape-kdb.Region(wells[members[0]])).is_empty() and (shape&psd).is_empty()
                key = 'well_'+str(members[0])
            else:
                assert contact['source_net']=='vss' and (shape-psd).is_empty()
                key = 'compatible_substrate_pool_not_local_path'
            supports[key].append(ids[tuple(contact['bbox_dbu'])])
        assert sum(len(v) for v in supports.values()) == 21804
        devices = {r['device']:r for r in ledger['devices'] if 'mos' in r['model']}
        ref = json.loads(reference.read_text()); gate_probes = [p for p in ref['terminal_audit']['probes'] if p['terminal']=='gate']
        assert len(gate_probes)==835 and len(devices)==58
        channel_by_point = {}
        for channel in (active&poly).each():
            found = [p for p in gate_probes if channel.inside(point(p['point_um']))]
            assert len(found)==1
            name = found[0]['device']; assert name in devices
            channel_by_point.setdefault(name,[]).append(channel)
        assert sum(map(len,channel_by_point.values()))==835 and set(channel_by_point)==set(devices)
        slots = []
        for name, device in devices.items():
            well_ids = set()
            for channel in channel_by_point[name]:
                found = [i for i,w in enumerate(wells) if w.inside(channel.bbox().center())]
                if device['model'].endswith('pmos'):
                    assert len(found)==1 and (kdb.Region(channel)-kdb.Region(wells[found[0]])).is_empty()
                    well_ids.add(found[0])
                else:
                    assert not found and all((kdb.Region(channel)&kdb.Region(w)).is_empty() for w in wells)
            if device['model'].endswith('pmos'):
                groups = ['well_'+str(i) for i in sorted(well_ids)]
                assert groups and all(supports[g] for g in groups) and device['terminal_nets']['B']=='vdd'
                scope = 'actual same-NWell tap support; no well resistance or current allocation'
            else:
                groups = ['compatible_substrate_pool_not_local_path']
                assert supports[groups[0]] and device['terminal_nets']['B']=='vss'
                scope = 'compatible source-net substrate pool only; no local path or isolation inference'
            slots.append(dict(device=name,terminal='B',source_net=device['terminal_nets']['B'],
                              support_sets=groups, channel_count=len(channel_by_point[name]), scope=scope))
        resbodies = list(mesh.materialize(cell,(128,0)).each()); used_bodies = set()
        by_slot = {(s['device'],s['terminal']):s for s in ledger['slots']}
        for slot in ledger['slots']:
            if slot.get('terminal')!='BN': continue
            a = point(by_slot[slot['device'],'1']['witnesses'][0]['point_um'])
            b = point(by_slot[slot['device'],'2']['witnesses'][0]['point_um'])
            mid = kdb.Point((a.x+b.x)//2,(a.y+b.y)//2)
            found = [i for i,p in enumerate(resbodies) if p.inside(mid)]; assert len(found)==1
            used_bodies.add(found[0]); body = kdb.Region(resbodies[found[0]])
            assert slot['source_net']=='vss'
            slots.append(dict(device=slot['device'],terminal='BN',source_net=slot['source_net'],
                              body_polygon=polygon_record(resbodies[found[0]]),
                              projected_NWell_overlap_dbu2=sum((body&kdb.Region(w)).area() for w in wells),
                              support_sets=['compatible_substrate_pool_not_local_path'],
                              scope='source-defined BN plus compatible substrate pool; no local spreading path'))
        assert len(used_bodies)==len(resbodies)==98
        plates = list(mesh.materialize(cell,(36,0)).each()); vmim = mesh.materialize(cell,(129,0))
        used_plates=set(); used_cuts=kdb.Region()
        for slot in ledger['slots']:
            if slot.get('model')!='cap_cmim' or slot['terminal']!='TOP': continue
            q = point(slot['witnesses'][0]['point_um']); found=[i for i,p in enumerate(plates) if p.inside(q)]
            assert len(found)==1; index=found[0]; used_plates.add(index); plate=kdb.Region(plates[index])
            cuts=vmim.inside(plate); assert not cuts.is_empty()
            assert (cuts-regions['TM1']).is_empty() and (plate-regions['M5']).is_empty()
            bottom=by_slot[slot['device'],'BOTTOM']; assert metal_net('M5',q)==bottom['source_net']
            cut_rows=[]
            for cut in cuts.each():
                assert metal_net('TM1',mesh.inside_point(cut))==slot['source_net']
                used_cuts.insert(cut);cut_rows.append(polygon_record(cut))
            slots.append(dict(device=slot['device'],terminal='TOP',source_net=slot['source_net'],
                              plate=polygon_record(plates[index]),Vmim_129=cut_rows,
                              scope='actual plate and top electrode access only; intrinsic and series ownership unresolved'))
            slots.append(dict(device=slot['device'],terminal='BOTTOM',source_net=bottom['source_net'],
                              M5_under_plate=polygon_record(plates[index]),
                              scope='actual M5 coverage under plate only; not full-net equipotential or model deembedding'))
        assert len(used_plates)==len(plates)==3 and (used_cuts^vmim).is_empty()
        pins=[]; labels=[]
        for li in layout.layer_indexes():
            info=layout.get_info(li)
            if info.datatype==2:
                for shape in cell.shapes(li).each():
                    if shape.is_box() or shape.is_polygon():pins.append((info.layer,kdb.Polygon(shape.box) if shape.is_box() else kdb.Polygon(shape.polygon)))
            if info.datatype==25:
                for shape in cell.shapes(li).each():
                    if shape.is_text(): labels.append((info.layer,shape.text.string,kdb.Point(shape.text.x,shape.text.y)))
        assert len(pins)==len(labels)==9
        for slot in ledger['slots']:
            if slot['device']!='PORT':continue
            matches=[(layer,p) for layer,name,p in labels if name==slot['source_net']];assert len(matches)==1
            layer,p=matches[0]; shapes=[poly for l,poly in pins if l==layer and poly.inside(p)];assert len(shapes)==1
            metal=metal_by_layer[layer];assert metal_net(metal,p)==slot['source_net']
            assert (kdb.Region(shapes[0])-regions[metal]).is_empty()
            slots.append(dict(device='PORT',terminal=slot['terminal'],source_net=slot['source_net'],
                              layer=layer,pin_polygon=polygon_record(shapes[0]),
                              scope='exact source pin support; fullchip boundary condition and injection not selected'))
        assert len(slots)==171 and len({(s['device'],s['terminal']) for s in slots})==171
        dump(args.output/'support_sets.json',dict(support_sets=dict(supports),slots=slots))
        assert sha(source)==result['source_sha256'] and sha(gds)==result['GDS_sha256']
        result.update(status='passed 171-slot native support inventory; all model attachments unqualified',
                      slots=171,well_components=len(wells),body_slots=58,BN_slots=98,MIM_slots=6,port_slots=9,
                      physical_tap_contacts=21804,Vmim_cuts=vmim.count(),source_nets=134,channels=835,
                      support_sets_sha256=sha(args.output/'support_sets.json'),
                      not_run=['Per-device well/substrate spreading resistance and current distribution',
                               'Body/BN/MIM/external-port model reference planes', 'Compact-model weights or current injection',
                               'ZeroR source/parameter/wave parity', 'Electrical/IR/EM/fullchip adoption'])
    except Exception as exc:
        result.update(status='failed remaining-terminal support inventory',error=repr(exc));raise
    finally:
        result['wall_s']=time.monotonic()-start;dump(args.output/'summary.json',result);print(json.dumps(result,indent=2))


if __name__=='__main__':main()

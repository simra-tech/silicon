#!/usr/bin/env python3
"""Repeat the exact held source-terminal and pad partition after macro replacement."""
import argparse
import collections
import json
import os
from pathlib import Path
import time
import pya
from flat_metal_connectivity import flat_physical
from audit_placed_decap_domains import identity
from audit_native_terminal_connectivity import CUTS, LAYERS, SUPPLIES
from place_closed_analog import region, sha


def bijective(pairs):
    forward=collections.defaultdict(set);reverse=collections.defaultdict(set)
    for a,b in pairs:forward[a].add(b);reverse[b].add(a)
    return bool(pairs) and all(len(s)==1 for s in forward.values()) and all(len(s)==1 for s in reverse.values())


def sense_projection_lineage(meta, projection):
    """Validate lineage only; actual terminal connectivity is recomputed below."""
    assert meta['status']=='passed isolated SENSE-only native hierarchy replacement'
    assert meta['saved_roundtrip']=='passed'
    assert meta['all_root_shapes_texts_properties_instances_and_die_held'] is True
    assert meta['all_other_native_hierarchies_held'] is True
    assert meta['transform']=='r90 *1 1031000,331000'
    assert projection['status']=='passed exact 33-object hierarchy-only projection; stock LVS not run'
    assert meta['original_parent_sha256']==projection['GDS_sha256']
    assert projection['object_count']==33 and projection['via_cut_count']==26
    assert projection['metal_landing_count']==7
    assert len(projection['full_affected_layer_XOR'])==7
    assert all(r['xor_dbu2']==0 for r in projection['full_affected_layer_XOR'])
    for key in ('all_other_cell_definitions_exact','all_root_text_and_nonoverlay_objects_exact',
                'source_bytes_exact','inverse_saved_projection_all_definitions_exact'):
        assert projection[key] is True
    return projection['original_GDS_sha256']


def hard_only_lineage(meta, geometry, audit):
    """Check the isolated hard-clone proof before fresh fullparent partition."""
    assert meta['status']=='passed isolated native preparation and strict comparator source checks; fullparent DRC not yet run'
    assert geometry['output_sha256']==meta['GDS_sha256']
    assert geometry['input_sha256']==meta['source_parent_sha256']
    assert geometry['pins_exact'] is True and geometry['all_other_generated_devices_exact'] is True
    assert len(geometry['changed_devices'])==2
    for old,new in geometry['changed_devices']:
        assert old['kind']==new['kind']=='nmos' and old['ng']==new['ng']==1
        assert (old['w'],old['l'],new['w'],new['l'])==(3,.13,6,.26)
    assert audit['status']=='passed isolated hard comparator DRC main/maximal and strict two-sided LVS'
    assert len(audit['circuits'])==1
    circuit=audit['circuits'][0]
    assert (circuit['pins'],circuit['nets'],circuit['devices'],circuit['subcircuits'])==(7,16,25,0)
    held=audit['all_original_native_hierarchy_checks']
    assert held['all_original_cells']==293 and held['all_original_direct_shapes_texts_exact'] is True
    assert held['only_instance_change']=='hard comparator at208000,162000; root global overlays exact'
    return meta['source_parent_sha256']


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('candidate','parent-terminals','output'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--parent-terminals-sha256',required=True)
    p.add_argument('--reroute-unrouted',type=Path)
    p.add_argument('--reroute-fill',type=Path)
    p.add_argument('--route-fill-source',type=Path)
    p.add_argument('--route-repair-original',type=Path)
    p.add_argument('--route-repair-geometry',type=Path)
    p.add_argument('--analog-pair',action='store_true')
    p.add_argument('--analog-poly-fill-parent',type=Path)
    p.add_argument('--sense-overlay-parent',type=Path)
    p.add_argument('--hard-only',action='store_true')
    a=p.parse_args();assert not a.output.exists() and len(os.sched_getaffinity(0))==1
    meta=json.loads((a.candidate/'analysis.json').read_text())
    lineage=[]
    if a.hard_only:
        assert not any([a.sense_overlay_parent,a.analog_poly_fill_parent,a.analog_pair,a.route_fill_source,a.reroute_unrouted,a.reroute_fill,a.route_repair_original,a.route_repair_geometry])
        geometry_path=a.candidate/'summary.json';audit_path=a.candidate/'strict_audit.json'
        assert sha(geometry_path)==meta['geometry_summary_sha256']
        assert sha(audit_path)==meta['strict_audit_sha256']
        geometry=json.loads(geometry_path.read_text());audit=json.loads(audit_path.read_text())
        parent_sha=hard_only_lineage(meta,geometry,audit)
        assert all(sha(a.candidate/f)==h for f,h in audit['inputs'].items())
        meta=dict(meta,original_parent_sha256=parent_sha,top_cell='placed_core_NOT_CONNECTED_FULLCHIP')
        gds=a.candidate/'candidate.gds'
        lineage=[geometry_path,audit_path]+[a.candidate/f for f in audit['inputs']]
    elif a.sense_overlay_parent:
        assert not any([a.analog_poly_fill_parent,a.analog_pair,a.route_fill_source,a.reroute_unrouted,a.reroute_fill,a.route_repair_original,a.route_repair_geometry])
        projection_path=a.sense_overlay_parent/'analysis.json'
        projection_gds=a.sense_overlay_parent/'overlay_flattened.gds'
        projection=json.loads(projection_path.read_text())
        old_sha=sense_projection_lineage(meta,projection)
        assert sha(projection_gds)==projection['GDS_sha256']
        assert meta['inputs_sha256'][str(projection_path)]==sha(projection_path)
        assert all(sha(Path(f))==h for f,h in meta['inputs_sha256'].items())
        assert all(sha(Path(f))==h for f,h in projection['inputs'].items())
        meta=dict(meta,original_parent_sha256=old_sha)
        gds=a.candidate/'sense_replaced_native.gds'
        lineage=[projection_path,projection_gds]+[Path(f) for f in meta['inputs_sha256']]+[Path(f) for f in projection['inputs']]
    elif a.analog_poly_fill_parent:
        assert not any([a.analog_pair,a.route_fill_source,a.reroute_unrouted,a.reroute_fill,a.route_repair_original,a.route_repair_geometry])
        assert meta['status']=='passed exact marked poly-fill pruning'
        assert meta['native_cell_definitions']=='passed all reachable non-root definitions including properties held'
        assert meta['functional_root_geometry']=='passed all direct shapes texts and nonfill instances held'
        assert meta['exact_single_top_roundtrip']=='passed'
        source_meta=a.analog_poly_fill_parent/'analysis.json'
        source_gds=a.analog_poly_fill_parent/'analog_pair_native.gds'
        source=json.loads(source_meta.read_text())
        assert source['status']=='passed isolated analog-pair hierarchy replacement'
        assert source['saved_hierarchy_and_geometry']=='passed'
        assert meta['source_metadata_sha256']==sha(source_meta)
        assert meta['source_GDS_sha256']==source['GDS_sha256']==sha(source_gds)
        assert all(sha(Path(f))==h for f,h in meta['inputs'].items())
        assert all(sha(Path(f))==h for f,h in source['inputs_sha256'].items())
        assert meta['removed_repetitions']>0 and all(meta['marker_coverage'])
        meta=dict(meta,original_parent_sha256=source['GDS_sha256'])
        gds=a.candidate/'poly_fill_pruned.gds'
        lineage=[source_meta,source_gds]+[Path(f) for f in meta['inputs']]+[Path(f) for f in source['inputs_sha256']]
    elif a.analog_pair:
        assert not any([a.route_fill_source,a.reroute_unrouted,a.reroute_fill,a.route_repair_original,a.route_repair_geometry])
        assert meta['status']=='passed isolated analog-pair hierarchy replacement'
        assert meta['saved_hierarchy_and_geometry']=='passed'
        assert meta['top_definition_die_pad_map']=='passed exact preservation except one declared BGR cuts instance'
        assert len(meta['replacements'])==1 and meta['replacements'][0]['role']=='SENSE'
        assert meta['replacements'][0]['transform']=='r90 *1 1031000,331000'
        assert meta['old_effective_bgr'] and meta['new_effective_bgr']==meta['saved_effective_bgr']
        assert all(row['xor_dbu2']==0 for row in meta['old_effective_bgr']+meta['new_effective_bgr'])
        assert all(sha(Path(f))==h for f,h in meta['inputs_sha256'].items())
        gds=a.candidate/'analog_pair_native.gds'
    elif a.route_fill_source:
        assert not a.reroute_unrouted and not a.reroute_fill
        assert meta['status']=='passed exact route-near floating-fill pruning'
        assert meta['native_cell_definitions']=='passed all reachable non-root definitions including properties held'
        assert meta['functional_root_geometry']=='passed all direct shapes texts and nonfill instances held'
        assert meta['exact_single_top_roundtrip']=='passed'
        source_meta=a.route_fill_source/'analysis.json'
        source_gds=a.route_fill_source/'signal_routed_native.gds'
        source=json.loads(source_meta.read_text())
        assert source['status']=='passed native-preserving DEF signal-route streamout and exact geometry roundtrip'
        assert meta['source_metadata_sha256']==sha(source_meta)
        assert meta['source_GDS_sha256']==source['GDS_sha256']==sha(source_gds)
        meta=dict(meta,original_parent_sha256=source['GDS_sha256'])
        gds=a.candidate/'route_fill_pruned.gds'
        lineage=[source_meta,source_gds]
        if a.route_repair_original or a.route_repair_geometry:
            assert a.route_repair_original and a.route_repair_geometry
            geometry=json.loads(a.route_repair_geometry.read_text())
            assert geometry['status']=='passed bounded M3-only route geometry delta and occupied three-segment windows'
            assert geometry['same_die_texts_all_other_layers']
            old_gds=a.route_repair_original/'signal_routed_native.gds'
            old_meta=a.route_repair_original/'analysis.json'
            old_source=json.loads(old_meta.read_text())
            assert old_source['status']=='passed native-preserving DEF signal-route streamout and exact geometry roundtrip'
            assert old_source['GDS_sha256']==sha(old_gds)
            assert set(geometry['inputs'])==set(map(str,[old_gds,old_meta,source_gds,source_meta]))
            assert all(sha(Path(f))==h for f,h in geometry['inputs'].items())
            assert source['route_validation_scope']=='passed exact three-segment g_shared_bare spacing repair; stock checks not run'
            meta['original_parent_sha256']=sha(old_gds)
            lineage += [old_gds,old_meta,a.route_repair_geometry]
    elif a.reroute_unrouted or a.reroute_fill:
        assert a.reroute_unrouted and a.reroute_fill
        assert meta['status']=='passed native-preserving DEF signal-route streamout and exact geometry roundtrip'
        assert meta['native_geometry_and_texts_held']==meta['saved_roundtrip']=='passed'
        native_path=a.reroute_unrouted/'analysis.json';fill_path=a.reroute_fill/'analysis.json'
        native=json.loads(native_path.read_text());fill=json.loads(fill_path.read_text())
        assert native['status']=='passed exact old-route removal with all other native definitions held'
        assert fill['status']=='passed exact macro-near floating-fill pruning'
        assert meta['native_GDS_sha256']==native['GDS_sha256']==sha(a.reroute_unrouted/'unrouted_native.gds')
        assert native['input_GDS_sha256']==fill['GDS_sha256']==sha(a.reroute_fill/'digital_fill_pruned.gds')
        assert native['input_metadata_sha256']==sha(fill_path)
        assert meta['native_instances_retained']==native['native_root_instances']
        meta=dict(meta,top_cell=native['top_cell'],original_parent_sha256=fill['original_parent_sha256'])
        gds=a.candidate/'signal_routed_native.gds'
        lineage=[native_path,fill_path,a.reroute_unrouted/'unrouted_native.gds',a.reroute_fill/'digital_fill_pruned.gds']
    else:
        assert meta['status']=='passed isolated digital replacement and exact other-cell preservation'
        gds=a.candidate/'digital_replaced_native.gds'
    assert not (a.route_repair_original or a.route_repair_geometry) or a.route_fill_source
    assert sha(gds)==meta['GDS_sha256']
    assert sha(a.parent_terminals)==a.parent_terminals_sha256
    old=json.loads(a.parent_terminals.read_text())
    assert old['status']=='passed exact held terminal partition and physical ports'
    assert old['GDS_sha256']==meta['original_parent_sha256']
    assert old['source_connections_exact'] and old['all_five_supplies_distinct']
    assert not old['errors'] and not old['split_components'] and not old['unexpected_merges']
    assert len(old['observations'])==10222 and len(old['physical_ports'])==24
    assert len({(r['net'],r['instance'],r['pin']) for r in old['observations']})==10222
    inputs={str(f):sha(f) for f in (gds,a.candidate/'analysis.json',a.parent_terminals,Path(__file__),Path(__file__).with_name('flat_metal_connectivity.py'))}
    inputs.update({str(f):sha(f) for f in lineage})
    a.output.mkdir(parents=True);(a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    result=dict(status='running',inputs=inputs,not_run=['Device-aware full-chip LVS','Stock DRC and antenna/density','Electrical adoption'])
    start=time.monotonic()
    try:
        assert bijective([('a',1),('a',1),('b',2)])
        assert not bijective([('a',1),('a',2)]) and not bijective([('a',1),('b',1)]) and not bijective([])
        ly=pya.Layout();ly.read(str(gds));top=ly.cell(meta['top_cell'])
        assert top is not None and meta['top_cell']=='placed_core_NOT_CONNECTED_FULLCHIP'
        net,metal,held=flat_physical(ly,top)
        actual={layer:region(ly,top,pya.LayerInfo(layer,0)) for layer in LAYERS.values()}
        observations=[];old_new=collections.defaultdict(set);new_old=collections.defaultdict(set)
        by_logical=collections.defaultdict(set);by_physical=collections.defaultdict(set)
        for row in old['observations']:
            clusters=set();windows=[]
            for window in row['windows']:
                layer=window['layer'];box=pya.Box(*window['bbox']);found=set()
                for polygon in (actual[layer]&pya.Region(box)).each():
                    point=next(polygon.each_point_hull())
                    for probe_layer in CUTS.get(layer,(layer,)):
                        key=identity(net,metal[probe_layer],[point.x,point.y])
                        assert key is not None,(row['instance'],row['pin'])
                        found.add(key)
                clusters.update(found);windows.append(dict(layer=layer,bbox=window['bbox'],clusters=[list(v) for v in sorted(found)]))
            assert len(clusters)==len(row['clusters'])==1,(row['instance'],row['pin'],clusters)
            new=next(iter(clusters));prior=tuple(row['clusters'][0]);old_new[prior].add(new);new_old[new].add(prior)
            by_logical[row['net']].add(new);by_physical[new].add(row['net'])
            observations.append(dict(instance=row['instance'],pin=row['pin'],net=row['net'],clusters=[list(new)],windows=windows))
        result.update(observations=observations,terminal_observations=len(observations),
            split_old_components=[dict(old=list(k),new=[list(v) for v in sorted(s)]) for k,s in old_new.items() if len(s)!=1],
            merged_old_components=[dict(new=list(k),old=[list(v) for v in sorted(s)]) for k,s in new_old.items() if len(s)!=1],
            split_logical_nets={k:[list(v) for v in sorted(s)] for k,s in by_logical.items() if len(s)!=1},
            actual_aliases=sorted(sorted(s) for s in by_physical.values() if len(s)>1))
        assert bijective([(left,right) for left,rights in old_new.items() for right in rights]), 'Changed physical partition; see saved split/merge observations'
        assert all(len(s)==1 for s in by_logical.values())
        assert len({next(iter(by_logical[k])) for k in SUPPLIES})==5
        aliases=sorted(sorted(s) for s in by_physical.values() if len(s)>1)
        assert aliases==old['source_justified_aliases'] and len(aliases)==8
        ports=[]
        for row in old['physical_ports']:
            box=pya.Box(*row['bbox_dbu']);assert (pya.Region(box)-actual[134]).is_empty()
            found=set()
            for polygon in (actual[134]&pya.Region(box)).each():
                point=next(polygon.each_point_hull());key=identity(net,metal[134],[point.x,point.y])
                assert key is not None;found.add(key)
            assert len(found)==1 and found==old_new[tuple(row['components'][0])],row
            ports.append(dict(row,components=[list(next(iter(found)))],status='passed'))
        assert len(ports)==24 and len({r['pin'] for r in ports})==22
        assert all(sha(Path(f))==h for f,h in inputs.items())
        result.update(status='passed exact held terminal partition and physical ports',GDS_sha256=sha(gds),
            observations=observations,terminal_observations=len(observations),physical_ports=ports,
            old_to_new_component_bijection=True,source_connections_exact=True,all_five_supplies_distinct=True,
            source_justified_aliases=aliases,errors=[],unexpected_merges=[],split_components={},
            partition_controls='positive pass; split/merge/empty rejected',flat_geometry='instance-resolved conductor geometry, no label-based joins')
    except Exception as exc:
        result.update(status='failed terminal or physical-port gate',error=repr(exc));raise
    finally:
        result['wall_s']=time.monotonic()-start
        (a.output/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':main()

#!/usr/bin/env python3
"""Read-only adjacency/coverage inventory; no clip, PEX or model is generated."""
import argparse
import collections
import copy
import json
import os
from pathlib import Path
import time
import pya
from build_sense_dual_gate import snapshot
from screen_sense_dual_gate_proposal import GM4, graph, regions, sha, inside_point

BASELINE = '8060e30ac14a1c4aeb1cf62204c9e95d9a68dbad3d73412fbb34c6a33be8b4f7'
CANDIDATE = '4b8a82d4a19127e5975d558381cd0f1057235cf51dfbbc58e2219b0f0c4a8bd1'
SOURCE = 'baab6183c364477da1dd332e4585ae7201b3776bf0f836014744a42809e13877'
METALS = (8, 10, 30, 50, 67, 126, 134)


def bounds(box): return [box.left, box.bottom, box.right, box.top]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--candidate', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(); assert not a.output.exists()
    assert len(os.sched_getaffinity(0)) == 1 and pya.__version__ == '0.30.9'
    base = GM4/'ring-r8-evidence-20260922-r1/sense-ring-routing-20260922-r8a/g1_sense_physical.gds'
    new = a.candidate/'g1_sense_physical.gds'
    source = GM4.parents[1]/'reports/resume-server-20260922/gm4comp3-qualified-source.spice'
    assert sha(base) == BASELINE and sha(new) == CANDIDATE and sha(source) == SOURCE
    m = json.loads((a.candidate/'manifest.json').read_text())
    assert m['GDS_sha256'] == CANDIDATE
    changes = json.loads((a.candidate/'changed_shapes.json').read_text()); assert len(changes) == 4
    a.output.mkdir(parents=True); (a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    result = dict(status='running source-bound field adjacency inventory', baseline_GDS_sha256=BASELINE,
        candidate_GDS_sha256=CANDIDATE, source_sha256=SOURCE, script_sha256=sha(Path(__file__)),
        changed_shapes_sha256=sha(a.candidate/'changed_shapes.json'), new_GDS_saved=False,
        PEX='not run', capacitance_acceptance='not run', model_composition='not qualified', adoption='not run')
    start = time.monotonic()
    try:
        native = {}; snapshots = {}; ownership = {}; held = []
        for tag, path in [('before', base), ('after', new)]:
            ly = pya.Layout(); ly.read(str(path)); top = ly.cell('g1_sense_physical')
            snaps = snapshot(top); regs = regions(top)
            hold = graph(regs, copy.deepcopy(m['terminal_audit']['probes'])); held.append((ly, hold))
            net, layers, expected, audit = hold[1:]
            assert audit['status'] == 'passed' and audit['source_net_count'] == 134
            names = {next(iter(v)): name for name, v in expected.items()}
            owned = {}
            for layer in METALS:
                groups = collections.defaultdict(pya.Region)
                for poly in regs[layer].each():
                    found = net.probe_net(layers[layer], inside_point(poly)); assert found is not None
                    groups[names.get(found.cluster_id, 'UNASSIGNED:'+str(found.cluster_id))].insert(poly)
                owned[layer] = groups
            native[tag] = regs; snapshots[tag] = snaps; ownership[tag] = owned
        for key in set(snapshots['before'])|set(snapshots['after']):
            old = snapshots['before'].get(key, pya.Region()); now = snapshots['after'].get(key, pya.Region())
            assert (old-now).is_empty()
            if key not in ((10, 0), (19, 0)): assert (old^now).is_empty(), key
        accounted = {10:pya.Region(),19:pya.Region()}; rows = []
        for change in changes:
            metal = pya.Region(pya.Box(*change['M2_bbox_dbu']))-native['before'][10]
            cuts = pya.Region()
            for b in change['Via1_bboxes_dbu']: cuts.insert(pya.Box(*b))
            assert cuts.count() == 8 and (cuts & native['before'][19]).is_empty()
            assert (metal-ownership['after'][10][change['net']]).is_empty()
            accounted[10] += metal; accounted[19] += cuts
            centers = [(b[0]+b[2])//2 for b in change['Via1_bboxes_dbu']]
            sites = [('middle', (change['x1']+change['x2'])//2),
                     ('first_cut_group', (min(centers[:4])+max(centers[:4]))//2),
                     ('last_cut_group', (min(centers[4:])+max(centers[4:]))//2),
                     ('trunk', change['x2'])]
            windows = []; covered = pya.Region()
            for kind, x in sites:
                for transverse in (24000, 48000):
                    # Prospective fixed20um longitudinal interval; context ladder only.
                    box = pya.Box(x-10000,change['y']-transverse//2,x+10000,change['y']+transverse//2)
                    window = pya.Region(box); covered += window
                    point = pya.Point(x,change['y'])
                    witness = pya.Region(pya.Box(point.x-1,point.y-1,point.x+1,point.y+1))
                    assert all((witness-ownership[tag][10][change['net']]).is_empty() for tag in ('before','after'))
                    adjacent = {}
                    for tag in ('before','after'):
                        adjacent[tag] = [dict(layer=layer, source_net=name,
                            clipped_area_dbu2=(region & window).area(),
                            projected_overlap_changed_M2_dbu2=(region & metal).area())
                            for layer, groups in ownership[tag].items() for name,region in groups.items()
                            if not (region & window).is_empty()]
                    omitted = [dict(layer=list(key), clipped_area_dbu2=(region & window).area(),
                                    projected_overlap_changed_M2_dbu2=(region & metal).area())
                        for key,region in snapshots['before'].items()
                        if key[0] in (1,5,6,31,36,128,129) and not (region & window).is_empty()]
                    windows.append(dict(site=kind, bbox_dbu=bounds(box), transverse_context_dbu=transverse,
                        longitudinal_length_dbu=20000, target_point_dbu=[x,change['y']], target_source_net=change['net'],
                        adjacency=adjacent, omitted_primitive_materials=omitted,
                        same_fullnet_clipped_components='Separate physical components retain unique labels; no text-based joins'))
            rows.append(dict(device=change['device'], net=change['net'], added_M2_dbu2=metal.area(),
                added_Via1_count=8, planned_window_union_changed_M2_dbu2=(covered & metal).area(),
                changed_M2_outside_planned_windows_dbu2=(metal-covered).area(), windows=windows))
        for layer, region in accounted.items():
            assert (region^(native['after'][layer]-native['before'][layer])).is_empty(), layer
        result.update(status='passed exact changed-geometry adjacency inventory; field extraction not run', rows=rows,
            accounted_M2_area_dbu2=accounted[10].area(), accounted_Via1_count=accounted[19].count(),
            source_graphs='134 nets held in both source geometries',
            scope='Candidate macro only, not final filled/routed fullchip; planned overlapping windows cannot be summed as full-route capacitance')
        assert sha(base)==BASELINE and sha(new)==CANDIDATE and sha(source)==SOURCE
    except Exception as exc:
        result.update(status='failed field adjacency inventory',error=repr(exc)); raise
    finally:
        result['wall_s']=time.monotonic()-start
        (a.output/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps({k:v for k,v in result.items() if k!='rows'},indent=2))


if __name__=='__main__': main()

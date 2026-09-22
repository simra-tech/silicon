#!/usr/bin/env python3
"""Actual top-route/PDN via cuts and sampled wires; device/pad interiors need a separate audit."""
import argparse
import collections
import hashlib
import json
import os
from pathlib import Path
import re
import pya
from sense_route_manifest import load_candidate_resistances

ROOT = Path(__file__).resolve().parents[4]
BLOCK = ROOT / 'designs/g1-guardian/blocks/g1_padring'
METALS = {'Metal1': 8, 'Metal2': 10, 'Metal3': 30, 'Metal4': 50, 'Metal5': 67, 'TopMetal1': 126, 'TopMetal2': 134}
CUTS = {19: (8, 10), 29: (10, 30), 49: (30, 50), 66: (50, 67), 125: (67, 126), 133: (126, 134)}
WANTED = {'VDDA', 'VDD', 'VSS', 'IOVDD', 'IOVSS', 'GATE', 'gate_o', 'i_core.iptat', 'i_core.isense',
          'i_core.vref', 'i_core.vref_buf', 'i_core.pbias', 'i_core.pcasc', 'i_core.sense_p', 'i_core.sense_n', 'i_core.cmp_clk'}
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--manifest', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args(); assert not a.output.exists(); assert len(os.sched_getaffinity(0)) == 1
assert pya.__version__ == '0.30.9'
manifest, _ = load_candidate_resistances(a.manifest)
limit_path = Path(__file__).with_name('current_limits_20260922.json')
limits = json.loads(limit_path.read_text())
cut_names = {19:'Via1',29:'Via2',49:'Via3',66:'Via4',125:'TopVia1',133:'TopVia2'}
gds = a.manifest.parent / 'g1_chip_top.gds'
deffile = BLOCK / 'flow/runs/assembly-1350/final/def/g1_chip_top.def'
text = deffile.read_text(); units = int(re.search(r'UNITS DISTANCE MICRONS (\d+)', text)[1])
ly = pya.Layout(); ly.read(str(gds)); top = ly.cell('g1_chip_top'); dbu = ly.dbu
regions = {number: pya.Region(top.begin_shapes_rec(ly.layer(number, 0))).merged() for number in METALS.values()}
network = pya.LayoutToNetlist(pya.RecursiveShapeIterator(ly, top, [])); nl = {}
for number in METALS.values():
    nl[number] = network.make_layer(ly.layer(number, 0), 'M' + str(number)); network.connect(nl[number])
for cut, (lower, upper) in CUTS.items():
    layer = network.make_layer(ly.layer(cut, 0), 'V' + str(cut))
    network.connect(layer); network.connect(layer, nl[lower]); network.connect(layer, nl[upper])
network.extract_netlist()
via_at = collections.defaultdict(list)
for inst in top.each_inst():
    if not inst.cell.name.startswith('VIA_'):
        continue
    for transform in inst.cell_inst.each_cplx_trans():
        via_at[(transform.disp.x, transform.disp.y)].append((inst.cell, transform))

def cut_record(cut, polygons):
    lower, upper = CUTS[cut]
    merged = polygons.merged(); distinct = list(merged.each())
    bounds = merged.bbox(); box_region = pya.Region(bounds)
    local = {number: (pya.Region(top.begin_shapes_rec_overlapping(ly.layer(number,0),bounds)) & box_region).merged()
             for number in (lower,upper)}
    all_bridges = bool(distinct) and all((merged-local[number]).is_empty() for number in (lower,upper))
    common_continuous_landing = bool(distinct) and all((box_region-local[number]).is_empty() for number in (lower,upper))
    point = distinct[0].bbox().center() if distinct else None
    net = network.probe_net(nl[lower], point) if point is not None else None
    limit = limits['cut_limit_mA'][cut_names[cut]]
    target = limits['engineering_screen']['utilization_target']
    return {'cut_layer': cut, 'lower_layer': lower, 'upper_layer': upper, 'actual_cut_count': len(distinct),
            'cut_bboxes_um': [[q.bbox().left*dbu, q.bbox().bottom*dbu, q.bbox().right*dbu, q.bbox().top*dbu] for q in distinct],
            'each_cut_fully_on_both_metals': all_bridges,
            'complete_cut_bbox_covered_by_both_metals': common_continuous_landing,
            'one_cut_open_local_bridge_remaining': len(distinct)>1 and common_continuous_landing,
            'one_cut_open_global_path': 'not run; a local single cut may have a remote parallel path',
            'physical_cluster': None if net is None else {'circuit': net.circuit().name, 'cluster_id': net.cluster_id},
            'current_source_conditions': 'not run; root V18a current mapping pending',
            'per_cut_table_limit_mA_at105C_11years': limit,
            'branch_mA_at_engineering_target_worst_single_cut_allocation': target*limit,
            'branch_mA_at_engineering_target_conditional_equal_sharing': target*limit*len(distinct),
            'remaining_branch_mA_at_target_conditional_equal_sharing_one_cut_open': target*limit*max(0,len(distinct)-1),
            'applicable_limit_utilization_margin': 'not run; no unsupported current-sharing/derating assumption'}

def via_record(name, point):
    location = pya.DPoint(*point).to_itype(dbu); found = via_at.get((location.x, location.y), [])
    exact = [(cell, transform) for cell, transform in found if cell.name == 'VIA_' + name]
    cuts = []
    for cell, transform in exact:
        for number in CUTS:
            region = pya.Region(cell.begin_shapes_rec(ly.layer(number, 0))).transformed(transform)
            if not region.is_empty(): cuts.append(cut_record(number, region))
    return {'definition': name, 'point_um': point, 'matching_top_instances': len(exact), 'cut_stages': cuts,
            'status': 'passed' if exact and cuts and all(row['each_cut_fully_on_both_metals'] for row in cuts) else 'failed'}

def wire_record(layer, start, end, declared_width=None):
    number = METALS[layer]; horizontal = start[1] == end[1]; widths = []
    for fraction in (.25, .5, .75):
        x, y = [start[i] + fraction*(end[i]-start[i]) for i in (0, 1)]
        window = pya.DBox(x-dbu,y-10,x+dbu,y+10) if horizontal else pya.DBox(x-10,y-dbu,x+10,y+dbu)
        box = window.to_itype(dbu)
        intersection = (pya.Region(top.begin_shapes_rec_overlapping(ly.layer(number,0),box)) & pya.Region(box)).merged()
        hits = [q for q in intersection.each() if q.inside(pya.DPoint(x,y).to_itype(dbu))]
        widths.append(None if not hits else (hits[0].bbox().height() if horizontal else hits[0].bbox().width())*dbu)
    narrow = pya.Region(pya.DPath([pya.DPoint(*start),pya.DPoint(*end)], 2*dbu).to_itype(dbu))
    local = pya.Region(top.begin_shapes_rec_overlapping(ly.layer(number,0),narrow.bbox()))
    return {'layer': layer, 'start_um': start, 'end_um': end, 'declared_width_um': declared_width,
            'sample_fractions': [.25,.5,.75], 'actual_sampled_width_um': widths,
            'cross_section_clipped_at20um': any(width is not None and width>=19.998 for width in widths),
            'centerline_covered': (narrow-local).is_empty()}

rows = {}
for section in ('NETS', 'SPECIALNETS'):
    body = re.search(r'^'+section+r' \d+ ;(.*?)^END '+section, text, re.M|re.S)[1]
    for entry in re.findall(r'^\s*- (.*?) ;', body, re.M|re.S):
        name = entry.split()[0]
        if name not in WANTED: continue
        row = rows.setdefault(name, {'net': name, 'sections': [], 'wires': [], 'vias': []})
        row['sections'].append(section)
        if name in ('i_core.sense_p', 'i_core.sense_n'): continue
        for route in re.split(r'(?:\+ ROUTED|\bNEW)\s+', entry)[1:]:
            layer = route.split()[0]
            if layer not in METALS: continue
            coords = list(re.finditer(r'\(\s*([*\d-]+)\s+([*\d-]+)(?:\s+[\d-]+)?\s*\)', route)); points = []
            for match in coords:
                points.append([points[-1][i] if match[i+1]=='*' else int(match[i+1])/units for i in (0,1)])
            header = route.split('(',1)[0].split()
            width = int(header[1])/units if len(header)>1 and header[1].isdigit() else None
            for first, second in zip(points, points[1:]):
                if first != second:
                    assert first[0]==second[0] or first[1]==second[1]
                    row['wires'].append(wire_record(layer, first, second, width))
            if coords:
                tail = route[coords[-1].end():].strip().split()
                if tail and 'via' in tail[0].lower(): row['vias'].append(via_record(tail[0], points[-1]))
        print(name, len(row['wires']), len(row['vias']), flush=True)
for route in manifest['routes']:
    row = rows['i_core.sense_' + route['net'].lower()]
    row['route_source'] = 'Exact candidate manifest; stale DEF route deliberately replaced'
    for segment in route['segments']:
        layer = next(name for name, number in METALS.items() if number == segment['layer'])
        row['wires'].append(wire_record(layer, segment['start_um'], segment['end_um'], segment['width_um']))
    vertical = next(segment for segment in route['segments'] if segment['layer']==50)
    for point in (vertical['start_um'], vertical['end_um']):
        x,y = point; box = pya.DBox(x-.35,y-.35,x+.35,y+.35).to_itype(dbu)
        actual = pya.Region(top.begin_shapes_rec_overlapping(ly.layer(49,0), box)) & pya.Region(box)
        record = cut_record(49, actual); assert record['actual_cut_count'] == 4
        row['vias'].append({'definition': 'candidate drawn2x2Via3', 'point_um': point, 'cut_stages': [record],
                            'status': 'passed' if record['each_cut_fully_on_both_metals'] else 'failed'})
result = {'scope': 'Actual GDS cuts at selected DEF-assigned top-route/PDN transition sites plus candidate SENSE replacement. Three wire-width samples per segment are not exhaustive neck detection. Local cut-open bridge screen does not prove global topology, current capacity or yield. Device contacts, internal IO power/output stages and inside-macro port-to-device stacks remain separate inventory work.',
          'candidate_sha256': manifest['candidate_sha256'], 'def_sha256': hashlib.sha256(deffile.read_bytes()).hexdigest(),
          'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), 'klayout_version': pya.__version__,
          'current_limit_record_sha256': hashlib.sha256(limit_path.read_bytes()).hexdigest(),
          'absent_requested_nets': sorted(WANTED-set(rows)), 'nets': list(rows.values()),
          'pad_internal_Gate_IOVDD_IOVSS': 'not run; DEF contains ports/abutment, not explicit route geometry',
          'macro_internal_device_contacts': 'not run', 'current_margin_qualification': 'not run'}
a.output.write_text(json.dumps(result, indent=2) + '\n')

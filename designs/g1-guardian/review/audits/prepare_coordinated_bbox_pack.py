#!/usr/bin/env python3
"""Constructive, source-bound rectangle placement study; saves JSON, NEVER GDS.

Native footprints are qualified inventories, not enlarged/modified PCells.
Reservations are engineering assumptions, not stock-rule qualification.
"""
import argparse, collections, hashlib, json, math, re
from pathlib import Path

BASE = Path(__file__).parent
ROOT = BASE.parents[3]
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--output', type=Path, required=True)
p.add_argument('--corridor-plan', choices=('wide','compact'), default='wide')
p.add_argument('--decap-packing', choices=('fixed-grid','site-greedy'), default='fixed-grid')
p.add_argument('--floorplan', choices=('io-window','ring-aware'), default='io-window')
a = p.parse_args()
assert not a.output.exists()
die_side = 1414 if a.floorplan=='ring-aware' else 1414.21
bgr_height = 354 if a.floorplan=='ring-aware' else 360
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
load = lambda p: json.loads(p.read_text())
source = ROOT/'designs/g1-guardian/blocks/g1_bgr/sim/qualification/candidates/bgr_loop24_qref4_r253p465/bgr_loop24_qref4_r253p465.spice'
assert sha(source) == '53513ab43c62ead3a4c171f5a026b165e2a0bfda2b5b0cb5b104a30aae33a4e2'
inventory_path = BASE/'bgr-array-area-20260922-r2/inventory.json'
inventory = load(inventory_path)
gm4_path = BASE/'gm4-pcell-footprint-20260922-r2.json'
gm4 = load(gm4_path)
assert gm4['source_sha256'] == 'baab6183c364477da1dd332e4585ae7201b3776bf0f836014744a42809e13877'
grid = load(BASE/'rppd-grid-20260922-r3.json')

def overlap(a, b):
    return min(a[2], b[2])-max(a[0], b[0]) > 1e-8 and min(a[3], b[3])-max(a[1], b[1]) > 1e-8

def inside(a, b):
    return all((a[i] >= b[i]-1e-8 if i < 2 else a[i] <= b[i]+1e-8) for i in range(4))

def expand(b, margin):
    return [b[0]-margin, b[1]-margin, b[2]+margin, b[3]+margin]

def box(cx, cy, w, h):
    return [cx-w/2, cy-h/2, cx+w/2, cy+h/2]

def grid_box(cx, cy, w, h, snap_up):
    # Opposite pair members round in opposite directions, preserving pair centroid.
    q = (lambda z: math.ceil(z/.005-1e-8)*.005) if snap_up else (lambda z: math.floor(z/.005+1e-8)*.005)
    x, y = q(cx-w/2), q(cy-h/2)
    return [x,y,x+w,y+h]

def check_rectangles(rows, boundary, field='bbox_um'):
    assert all(inside(r[field], boundary) for r in rows)
    assert all(not overlap(r[field], s[field]) for i, r in enumerate(rows) for s in rows[i+1:])

native = {}
for row in inventory['pcells']:
    if row['kind'] in ('pmosHV', 'nmosHV'):
        assert len(row['gate_boxes_um']) == 1
        length, width = row['gate_boxes_um'][0]
        key = (row['kind'], width, length)
        dimensions = (row['width_um'], row['height_um'])
        if key in native:
            assert native[key] == dimensions
        native[key] = dimensions
devices = []
for line in source.read_text().splitlines():
    if not re.match(r'^X[MRQ]', line):
        continue
    words = line.split()
    params = dict(re.findall(r'\b(w|l)=([\d.]+)u', line))
    if words[0].startswith('XM'):
        kind = 'pmosHV' if 'sg13_hv_pmos' in words else 'nmosHV'
        key = (kind, float(params['w']), float(params['l']))
        width, height = native[key]
        zone = ('pmos10' if key == ('pmosHV', 10, 4) else
                'pmos5' if key == ('pmosHV', 5, 4) else
                'nmos10' if key == ('nmosHV', 10, 1) else 'startup')
    elif words[0].startswith('XQ'):
        kind, zone, width, height = 'npn13G2', 'hbt', 6.7, 7.11
    else:
        kind, zone = ('rhigh' if 'rhigh' in words else 'rppd'), 'resistor'
        width, height = float(params['w'])+.4, float(params['l'])+1.22
    devices.append(dict(name=words[0], original=words[0].split('_u')[0], kind=kind,
                        zone=zone, width_um=width, height_um=height, source_line=line))
assert collections.Counter(d['kind'] for d in devices) == {
    'pmosHV': 235, 'nmosHV': 101, 'npn13G2': 301, 'rppd': 384, 'rhigh': 15}

# Each even replicated source group gets point-symmetric slot pairs.
# Odd original-only units are assigned unused slots, without asserting their matching.
zones = {
    'resistor': dict(x=20, y=10, nx=200, ny=2, pitch_x=1.9, pitch_y=62, slot_h=54.685),
    'hbt': dict(x=8, y=140, nx=17, ny=19, pitch_x=10.7, pitch_y=11.11, slot_h=11.11),
    'pmos10': dict(x=202, y=140, nx=21, ny=5, pitch_x=9.92, pitch_y=15.24, slot_h=15.24),
    'pmos5': dict(x=207, y=220.2, nx=20, ny=8, pitch_x=9.92, pitch_y=10.24, slot_h=10.24),
    'nmos10': dict(x=203, y=306.12, nx=33, ny=3, pitch_x=6.22, pitch_y=15.04, slot_h=15.04),
}
placed = []
centroids = []
unused = {}
for name, spec in zones.items():
    nx, ny = spec['nx'], spec['ny']
    slots = [(spec['x']+(x+.5)*spec['pitch_x'], spec['y']+y*spec['pitch_y']+spec['slot_h']/2)
             for y in range(ny) for x in range(nx)]
    pairs = [(i, len(slots)-1-i) for i in range(len(slots)//2)]
    # Deterministic dispersed distribution; no claim of gradient/thermal qualification.
    pairs.sort(key=lambda ij: ((ij[0]*37) % max(1, len(pairs)), ij[0]))
    groups = collections.defaultdict(list)
    for d in devices:
        if d['zone'] == name:
            groups[d['original']].append(d)
    used = set()
    for original, members in sorted(groups.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        selected = []
        if len(members) % 2 == 0:
            assert len(pairs) >= len(members)//2
            for _ in range(len(members)//2):
                i, j = pairs.pop(0)
                selected.extend([i, j])
        else:
            available = [i for i in range(len(slots)) if i not in used]
            selected = available[:len(members)]
            assert len(selected) == len(members)
            selected_set = set(selected)
            pairs = [ij for ij in pairs if not selected_set.intersection(ij)]
        used.update(selected)
        group_rows = []
        for pair_index, (d, i) in enumerate(zip(members, selected)):
            cx, cy = slots[i]
            row = dict(d, bbox_um=grid_box(cx,cy,d['width_um'],d['height_um'],pair_index%2==1),slot_index=i)
            row['reservation_um'] = expand(row['bbox_um'], 0 if name == 'resistor' else 2)
            placed.append(row)
            group_rows.append(row)
        if len(members) > 1:
            cx = sum((r['bbox_um'][0]+r['bbox_um'][2])/2 for r in group_rows)/len(selected)
            cy = sum((r['bbox_um'][1]+r['bbox_um'][3])/2 for r in group_rows)/len(selected)
            target = [(slots[0][0]+slots[-1][0])/2, (slots[0][1]+slots[-1][1])/2]
            assert max(abs(cx-target[0]), abs(cy-target[1])) < 1e-9
            centroids.append(dict(original=original, count=len(members), centroid_um=[cx,cy], zone=name))
    unused[name] = [slots[i] for i in range(len(slots)) if i not in used]
for d, (cx, cy) in zip([d for d in devices if d['zone']=='startup'], unused['pmos10']):
    b = box(cx, cy, d['width_um'], d['height_um'])
    placed.append(dict(d, bbox_um=b, reservation_um=expand(b,2), slot_index='unused pmos10 slot'))
assert len(placed) == len(devices) == 1036
check_rectangles(placed, [0,0,420,bgr_height])
check_rectangles([r for r in placed if r['zone']!='resistor'], [0,0,420,bgr_height], 'reservation_um')
assert all(abs(v/.005-round(v/.005)) < 1e-7 for r in placed for v in r['bbox_um'])

# Main OTA: unchanged complete native arrays, no folding or PCell geometry edits.
main = {r['device']:r for r in gm4['devices'] if r['view']=='candidate'}
ota = []
large = [('XM1','XM2'), ('XM3','XM4'), ('XM14','XM11'), ('XM15','XM12')]
for index, names in enumerate(large):
    for name, cy in zip(names, [12+index*13.5, 106.5-index*13.5]):
        r = main[name]
        ota.append(dict(name=name, bbox_um=box(115,cy,r['width_um'],r['height_um'])))
for names, y in [(['XMB2','XMB3','XMB5','XMB4','XMB6','XMB7','XCC'],117),
                 (['XMT','XM13','XM16','XM20','XM21','XRZ'],147)]:
    x = 5
    for name in names:
        r = main[name]
        ota.append(dict(name=name,bbox_um=[x,y,x+r['width_um'],y+r['height_um']]))
        x += r['width_um']+4
assert set(r['name'] for r in ota) == set(main)
for r in ota:
    r['reservation_um'] = expand(r['bbox_um'],2)
check_rectangles(ota,[0,0,230,164],'reservation_um')
sense_parts = [dict(name='main_OTA',bbox_um=[5,5,235,169]),
               dict(name='unchanged_XBUF',bbox_um=[5,181,102.85,232.2]),
               dict(name='unchanged_XREF',bbox_um=[111,181,208.85,232.2]),
               dict(name='resistor_array_and_existing_ring',bbox_um=[247,8,379.5,178.48])]
check_rectangles(sense_parts,[0,0,385,240])

macros = [dict(name=n,bbox_um=b) for n,b in [
    ('g1_digital',[331,331,691,691]), ('g1_sense_candidate',[701,331,1086,571]),
    ('g1_bgr_candidate',[331,723,751,1083]), ('g1_trip',[771,723,1000,930]),
    ('g1_osc',[771,945,937,1082.57]), ('g1_t2f',[953,945,1045,1047.6]),
    ('g1_gate',[931,603,1061.68,653.65]), ('g1_dut',[781,603,815,637]),
    ('g1_dose',[831,603,861,633]), ('g1_ls_0',[781,659,790.2,670.7]),
    ('g1_ls_1',[801,659,810.2,670.7]), ('g1_ls_2',[821,659,830.2,670.7])]]
if a.floorplan=='ring-aware':
    macros = [dict(name=n,bbox_um=b,orientation=o) for n,b,o in [
        ('g1_digital',[367,364,727,724],'R0'),
        ('g1_sense_candidate',[791,331,1031,716],'R90'),
        ('g1_bgr_candidate',[331,732,751,1086],'R0'),
        ('g1_trip',[771,736,1000,943],'R0'),
        ('g1_osc',[771,953,937,1090.57],'R0'),
        ('g1_t2f',[953,953,1045,1055.6],'R0'),
        ('g1_gate',[731,545,781.65,675.68],'R90'),
        ('g1_dut',[733,400,767,434],'R0'),
        ('g1_dose',[733,450,763,480],'R0'),
        ('g1_ls_0',[733,490,742.2,501.7],'R0'),
        ('g1_ls_1',[753,490,762.2,501.7],'R0'),
        ('g1_ls_2',[773,490,782.2,501.7],'R0')]]
core = [321,321,die_side-321,die_side-321]
check_rectangles(macros,core)
corridors = [dict(name=n,bbox_um=b) for n,b in [
    ('main_horizontal',[331,699,1086,715]),
    ('upper_analog_vertical',[751,723,771,1083]),
    ('digital_SENSE_interface',[691,331,701,691]),
    ('SENSE_north_ports',[701,579,1086,595]),
    ('SENSE_east_input_pair',[1086,331,1093.21,571])]]
if a.corridor_plan == 'compact':
    corridors[0]['bbox_um'] = [331,703,1086,711]
    corridors[1]['bbox_um'] = [755,723,767,1083]
    corridors[3]['bbox_um'] = [701,583,1086,591]
if a.floorplan=='ring-aware':
    assert a.corridor_plan=='compact' and a.decap_packing=='site-greedy'
    corridors=[dict(name=n,bbox_um=b) for n,b in [
        ('main_horizontal',[331,724,1093,732]),
        ('upper_analog_vertical',[755,732,767,1086]),
        ('digital_SENSE_interface',[783,331,791,724]),
        ('rotated_SENSE_north_input_pair',[791,716,1031,724]),
        ('rotated_SENSE_south_reference_output_ports',[791,321,1031,331])]]
assert all(not overlap(c['bbox_um'],m['bbox_um']) for c in corridors for m in macros)
original_decaps = [r for r in inventory['all_top_placements'] if r['cell'].startswith('sg13g2_decap')]
counts = collections.Counter(r['cell'] for r in original_decaps)
assert counts == {'sg13g2_decap_8':4645,'sg13g2_decap_4':17}
# Site-based capacity placement, one unchanged instance per slot. No power reassignment.
# Avoid expanded macro bboxes, named signal corridors, and 6um-wide PDN access lanes.
obstacles = [expand(m['bbox_um'],3) for m in macros]+[c['bbox_um'] for c in corridors]
pdn_lanes = []
for x in [358.8+i*75.6 for i in range(10)]:
    pdn_lanes.append([x-3,321,x+3,die_side-321])
obstacles += pdn_lanes
decap_slots = []
for row in range(203):
    y = (324 if a.decap_packing=='site-greedy' else 328.86)+row*3.78
    if y+3.78 > 1087:
        break
    site = 0
    while site < 1600:
        x = 327.36+site*.48
        b = [x,y,x+3.36,y+3.78]
        if b[2] > 1087:
            break
        blocked = [o for o in obstacles if overlap(b,o)]
        if not blocked:
            decap_slots.append(dict(bbox_um=b,orientation='R0' if row%2==0 else 'MX',row=row,site=site))
            site += 7
        elif a.decap_packing=='site-greedy':
            site = max(site+1,math.ceil((max(o[2] for o in blocked)-327.36-1e-8)/.48))
        else:
            site += 7
capacity_passed = len(decap_slots) >= len(original_decaps)
decaps = []
for i,(original,slot) in enumerate(zip(original_decaps,decap_slots)):
    slot = dict(slot)
    if original['cell']=='sg13g2_decap_4':
        slot['bbox_um'] = slot['bbox_um'][:2]+[slot['bbox_um'][0]+1.92,slot['bbox_um'][3]]
    decaps.append(dict(slot,original_inventory_index=i,cell=original['cell'],original_bbox_um=original['bbox_um']))
check_rectangles(decaps,core)
result = dict(status=('passed' if capacity_passed else 'failed')+' constructive rectangle capacity; legal routed placement not run',
    corridor_plan=a.corridor_plan,decap_capacity_passed=capacity_passed,decap_packing=a.decap_packing,
    floorplan=a.floorplan,ring_proposed_die_side_um=1414,
    placed_decap_count=len(decaps),requested_decap_count=len(original_decaps),
    script_sha256=sha(Path(__file__)),BGR_source_sha256=sha(source),gm4_source_sha256=gm4['source_sha256'],
    inventory_sha256=sha(inventory_path),gm4_inventory_sha256=sha(gm4_path),
    source_device_counts=dict(collections.Counter(d['kind'] for d in devices)),
    BGR_macro_um=[420,bgr_height],BGR_devices=placed,BGR_zones=zones,replicated_group_centroids=centroids,
    SENSE_macro_um=[385,240],main_OTA_macro_um=[230,164],main_OTA_devices=ota,SENSE_parts=sense_parts,
    die_side_um=die_side,die_area_um2=die_side**2,inner_core_um=core,macros=macros,port_corridors=corridors,
    retained_decap_counts=dict(counts),available_decap8_sites=len(decap_slots),decap_placements=decaps,
    decap_LEF_sha256='c9bbc02d0c2cba3b15cd89a208750d25de882f02a2927ae78ba6422109fb01d0',
    decap_site_um=[.48,3.78],decap8_LEF_um=[3.36,3.78],decap4_LEF_um=[1.92,3.78],
    PDN_access_lane_reservations_um=pdn_lanes,
    verified_HV06_derivative_native_delta_um2=.408,
    no_saved_GDS=True,no_canonical_mutation=True,BGR_native_bbox_vertices_5nm_grid_passed=True,
    limitations=[
        'No PCell/contact/well/guard/route shapes generated. 2um MOS/HBT margins are engineering reservations, not foundry legal rules.',
        'Replicated-group point centroids verified; common-centroid routing, orientation effects, matching, thermal gradients, dummy design and device access are not qualified.',
        'Original resistor pitches retained; source535 exact units and full native gm4 arrays, not smaller folded approximations.',
        'SENSE existing resistor-array ring extent from original source formula132.5x170.48; east input-port tracks and macro ring need rerouting within reserved edge space.',
        'All4662 decap instances are required; placed_decap_count records actual coverage and any shortfall fails. Per-instance VDD/VDDA/VSS connectivity is not reassigned or validated by this inventory-only study.',
        'Moving macros and north/east IO ring requires redesigned port routes, PDN feeds, bond map and whole-chip verification. Existing route/current/coupling results do not transfer.',
        'Top-metal PDN pitch75.6um and2.2um width are retained intentions; proposed6um access lanes are not drawn feeds or current-margin qualification.',
        'No stock DRC/LVS/density/antenna/PEX/STA or final legal floorplan run; no physical adoption. The2mm2 budget does not itself confirm external allocation.' ])
a.output.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ('BGR_devices','main_OTA_devices','decap_placements','replicated_group_centroids')},indent=2))
if not capacity_passed:
    raise SystemExit(2)

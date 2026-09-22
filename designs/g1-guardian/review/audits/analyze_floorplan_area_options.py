#!/usr/bin/env python3
"""Read-only geometric area bounds from qualified placement inventory; no fit signoff."""
import argparse,hashlib,json,math
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
base=Path(__file__).parent;source=base/'bgr-array-area-20260922-r2/inventory.json';inventory=json.loads(source.read_text())
placements=inventory['all_top_placements'];macros=[row for row in placements if row['cell'].startswith('g1_')]
decaps=[row for row in placements if row['cell'].startswith('sg13g2_decap')]
def overlap(a,b):return max(0,min(a[2],b[2])-max(a[0],b[0]))*max(0,min(a[3],b[3])-max(a[1],b[1]))
def area(b):return (b[2]-b[0])*(b[3]-b[1])
def union_area(boxes):
    xs=sorted(set(x for b in boxes for x in (b[0],b[2])));total=0
    for left,right in zip(xs,xs[1:]):
        intervals=sorted((b[1],b[3]) for b in boxes if b[0]<right and b[2]>left)
        end=-1e30;height=0
        for low,high in intervals:
            height+=max(0,high-max(low,end));end=max(end,high)
        total+=(right-left)*height
    return total
def largest_macro_free_rectangles(core,obstacles):
    xs=sorted(set([core[0],core[2]]+[max(core[0],min(core[2],b[i])) for b in obstacles for i in (0,2)]));out=[]
    for i,left in enumerate(xs):
        for right in xs[i+1:]:
            intervals=sorted((max(core[1],b[1]),min(core[3],b[3])) for b in obstacles if b[0]<right and b[2]>left and b[1]<core[3] and b[3]>core[1])
            bottom=core[1]
            for low,high in intervals+[(core[3],core[3])]:
                if low>bottom:
                    box=[left,bottom,right,low];out.append({'bbox_um':box,'area_um2':area(box),'existing_decap_bbox_overlap_sum_um2':sum(overlap(box,row['bbox_um']) for row in decaps)})
                bottom=max(bottom,high)
    return sorted(out,key=lambda row:-row['area_um2'])[:8]
macro_area=union_area([r['bbox_um'] for r in macros]);decap_area=union_area([r['bbox_um'] for r in decaps])
# Reserve the previously defined SENSE local envelope; gm4 fit inside it is NOT established by this reservation.
sense_reservation=[727,408,1029,648]
obstacles=[r['bbox_um'] for r in macros if r['cell'] not in ('g1_bgr','g1_sense')]+[sense_reservation]
side=math.sqrt(2000000);delta=side-1350;scenarios=[]
for name,core in [('existing_ring_fixed',[321,321,1029,1029]),('2mm2_square_ring_moved_east_north_hypothesis',[321,321,1029+delta,1029+delta])]:
    scenarios.append({'name':name,'core_rectangle_um':core,'gross_core_rectangle_um2':area(core),'largest_rectangles_avoiding_fixed_macro_bboxes':largest_macro_free_rectangles(core,obstacles),
        'scope':'BGR may replace its own existing footprint; other macro bboxes fixed; reserved SENSE envelope. Decaps itemized, not removed. PDN, signals, fill, guards, matching and routing not accounted as available area. Expanded scenario requires ring/PDN/bonding redesign, not an implemented option.'})
result={'status':'passed read-only arithmetic, physical fit not run','inventory_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'GDS_sha256':inventory['gds_sha256'],
    'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'macros':macros,'macro_bbox_union_um2':macro_area,'decap_instances':len(decaps),'decap_bbox_union_um2':decap_area,
    'current_die_um2':1350**2,'budget_die_um2':2000000,'square_budget_side_um':side,'square_side_increment_um':delta,
    'gross_die_increment_um2':2000000-1350**2,'gross_core_increment_fixed_ring_depth_um2':(708+delta)**2-708**2,
    'sense_reserved_region_um':sense_reservation,'sense_reserved_region_area_um2':area(sense_reservation),'gm4_specific_footprint':'not run; existing isolated PCell inventory is older gm3 matching16, not interchangeable',
    'scenarios':scenarios,'legal_pitch_reduction':'not run; existing1.9um resistor pitch is not minimum rule. Any reduction needs contact/head, implant, well, routing and matching checks; bounding-box overlap alone is insufficient.',
    'limitations':['Gross union and empty rectangles do not establish available placement area with PDN/routes/decaps preserved.','Ring movement consumes part of die growth;177500um2 die margin is not177500um2 core margin.','No floorplan, source, PCell, GDS, model, deck, extraction or simulation changed.']}
gm4_path=base/'gm4-pcell-footprint-20260922-r2.json'
if gm4_path.exists():
    gm4=json.loads(gm4_path.read_text());selective_path=base/'bgr-selective-area-20260922-r1.json';selective=json.loads(selective_path.read_text())
    loop=selective['groups']['selective_loop_unit']['native_bbox_sum_um2'];qref=selective['groups']['Qref_unit']['native_bbox_sum_um2'];original=selective['baseline_native_bbox_sum_um2'];factor=selective['baseline_macro_um2']/original
    native24=original+23*loop+3*qref+24*1.4*(53.465-52.5)
    proposals=[]
    for name,native in [('loop24_Qref4_R2fixed53p465',native24),('loop32_Qref4_no_R2_change',selective['proposals']['selective32_Qref4']['native_bbox_sum_um2'])]:
        estimated=native*factor;reserved_total=macro_area-10416-252.16*189.25+area(sense_reservation)+estimated+decap_area
        proposals.append({'name':name,'native_bbox_accounting_um2':native,'baseline_overhead_BRG_estimate_um2':estimated,'same_area_square_side_um':math.sqrt(estimated),
            'macro_reservations_plus_retained_decap_sum_um2':reserved_total,'existing_core_gross_remainder_um2':708**2-reserved_total,
            'expanded_core_gross_remainder_um2':(708+delta)**2-reserved_total,'status':'placement/routing/PDN/matching fit not run; arithmetic only'})
    result.update(gm4_inventory_sha256=hashlib.sha256(gm4_path.read_bytes()).hexdigest(),gm4_source_sha256=gm4['source_sha256'],
        gm4_specific_footprint=gm4['totals'],gm4_whole_SENSE_overhead_estimate_um2=gm4['whole_SENSE_estimate_replace_only_main_OTA_um2'],
        gm4_envelope_arithmetic_headroom_um2=area(sense_reservation)-gm4['whole_SENSE_estimate_replace_only_main_OTA_um2'],
        BGR_proposals=proposals,loop24_Qref4_native_plus_retained_resistor_column_pitch_um2=native24+.5*(24*761.8+24*(53.465+1.22)),
        BGR_fixed_nominal_centering_scope='Root/reference proposed circuit design change, not per-sample calibration; no source or geometry generated, no TC result or fit acceptance.',
        gm4_baseline_regenerated_vs_delivered_MOS_bbox_um2=[gm4['totals']['baseline']['MOS_bbox_sum_um2'],2495.3352])
a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({key:value for key,value in result.items() if key not in ('macros','scenarios')},indent=2));print([(s['name'],s['largest_rectangles_avoiding_fixed_macro_bboxes'][0]) for s in scenarios])

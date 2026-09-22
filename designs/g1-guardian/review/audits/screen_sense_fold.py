#!/usr/bin/env python3
"""Isolated rectangle/centroid screen for regrouping SENSE inside unchanged outline."""
import argparse,json,hashlib,shutil
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(exist_ok=False);shutil.copyfile(__file__,a.output/'analyzer.py');aud=Path(__file__).resolve().parent;inv=aud/'bgr-array-area-20260922-r2/inventory.json';data=json.loads(inv.read_text());area=aud/'sense-candidate-area-20260922-r2/summary.json';s=json.loads(area.read_text())
region=[727,321,1029,648]
proposals=[{'name':'Main OTA: folded candidate','bbox_um':[735,335,995,463],'status':'routing/guards not implemented','color':'#e7a74d'}, {'name':'Resistor array: rotate90°','bbox_um':[735,480,915,622],'status':'original132.50×170.48um guard+tracks, rotated and reserved180×142um; rerouting required','color':'#6eadd4'}, {'name':'Baseline buffer OTA','bbox_um':[925,482,1025,536],'status':'97.85×51.2um cell plus small allowance; relocated','color':'#8abe86'}, {'name':'Baseline VREF OTA','bbox_um':[925,544,1025,598],'status':'97.85×51.2um cell plus small allowance; relocated','color':'#b5ce91'}]
def overlap(a,b):return max(0,min(a[2],b[2])-max(a[0],b[0]))*max(0,min(a[3],b[3])-max(a[1],b[1]))
assert all(region[0]<=r['bbox_um'][0]<r['bbox_um'][2]<=region[2] and region[1]<=r['bbox_um'][1]<r['bbox_um'][3]<=region[3] for r in proposals)
assert all(overlap(x['bbox_um'],y['bbox_um'])==0 for i,x in enumerate(proposals) for y in proposals[i+1:])
fixed=[r for r in data['all_top_placements'] if (r['cell'].startswith('g1_') and r['cell']!='g1_sense') or r['cell'].startswith('sg13g2_IO')]
collisions=[{'proposal':x['name'],'existing':y} for x in proposals for y in fixed if overlap(x['bbox_um'],y['bbox_um'])>0];assert not collisions
# Four equal chunks per logicalPMOS, twelve fingers/chunk; preserve first moments.
pa=['ABCD','DCBA','CDAB','BADC'];mom={g:{'chunks':4,'fingers':48,'column_centroid':sum(row.index(g) for row in pa)/4,'row_centroid':1.5} for g in 'ABCD'};assert all(v['column_centroid']==1.5 for v in mom.values())
# M3/M4 four equal10fingerchunks/device, preserving both first moments.
ns=['ABBA','BAAB'];nm={g:{'chunks':4,'fingers':40,'column_centroid':sum(i for row in ns for i,c in enumerate(row) if c==g)/4,'row_centroid':sum(j for j,row in enumerate(ns) for c in row if c==g)/4} for g in 'AB'};assert all(v['column_centroid']==1.5 and v['row_centroid']==.5 for v in nm.values())
pattern='ABBA'*24;inp={g:{'fingers':pattern.count(g),'index_centroid':sum(i for i,c in enumerate(pattern) if c==g)/pattern.count(g)} for g in 'AB'};assert inp['A']==inp['B']
row_alloc=[{'group':'NMOS folded+fixed','height_um':27,'width_limit_um':239.4},{'group':'PA4centroidrows','height_um':53,'width_limit_um':239.4},{'group':'Input96fingers','height_um':10,'width_limit_um':239.4},{'group':'PC unchanged','height_um':12,'width_limit_um':239.4}];assert sum(r['height_um'] for r in row_alloc)+3*4+12<=128
result={'status':'passed: reservedrectangles/nonoverlap/firstmoment arithmetic only','scope':'Floorplan feasibility screen, not actualconnectedlayout or adoption. Shows a bounded southwardregrouping option absent from priorareaenvelope.','inputs':{str(f.relative_to(aud)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [inv,area]},'expanded_local_region_um':region,'expanded_region_area_um2':302*327,'proposals':proposals,'fixed_macro_IO_bbox_collisions':collisions,'pa_chunk_map':pa,'pa_centroids':mom,'NMOS_chunk_map':ns,'NMOS_centroids':nm,'input_pair_pattern':pattern,'input_pair_centroids':inp,'main_row_height_allocations':row_alloc,'main_reserved_area_um2':260*128,'resistor_original_guard_and_tracks_um':[132.5,170.48],'preserved_die_um':[1350,1350],'not_run':['PCellsegmentedconnectedplacement','DRC/LVS/density/antenna','guard/tapspacingimplementation','routecongestionandpinassignment','PDN/decap/fillregeneration','newPEX/stability/mismatchlayoutverification','adoption'], 'cautions':['No device/macro is actually moved. Existing PDN/decaps/fill/routes inside proposal are not free and require regeneration.','PAlettermapping must map exactsource/drain/bodylogicaldevicesbeforelayout. Equalfirstmoments do not establishbalancedRCor higherordergradient cancellation.','Nativeenclosureoverlap/segmentedfingers require carefulDRC; schematicngandMCstatisticscannotbesilentlychanged.','10umnewroutingcorridor and assumedrowspacing are reservations,notrouted proof.','ExistingneighborPadbboxenclosuresusedasobstacles;fullguard/latchup/ESDclearancenotqualified.']}
(a.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
fig,ax=plt.subplots(figsize=(7,7));ax.add_patch(Rectangle((727,321),302,327,fill=False,linestyle='--',edgecolor='black'))
for r in fixed:
 b=r['bbox_um']
 if overlap(b,[690,285,1070,690]):ax.add_patch(Rectangle((b[0],b[1]),b[2]-b[0],b[3]-b[1],facecolor='#dedede',edgecolor='#777777'));ax.text((b[0]+b[2])/2,(b[1]+b[3])/2,r['cell'].replace('sg13g2_',''),ha='center',va='center',fontsize=7,clip_on=True)
for r in proposals:
 b=r['bbox_um'];ax.add_patch(Rectangle((b[0],b[1]),b[2]-b[0],b[3]-b[1],facecolor=r['color'],edgecolor='black'));ax.text((b[0]+b[2])/2,(b[1]+b[3])/2,r['name'].replace(': ',':\n'),ha='center',va='center',fontsize=8)
ax.set(xlim=(700,1060),ylim=(295,675),xlabel='Die X (µm)',ylabel='Die Y (µm)',title='SENSE: isolated reservation screen\nNo routed candidate; existing die outline retained');ax.set_aspect('equal');fig.tight_layout();fig.savefig(a.output/'reservation.png',dpi=160);fig.savefig(a.output/'reservation.svg')
print(json.dumps(result,indent=2))

#!/usr/bin/env python3
"""Delivered route/floating-fill proximity geometry; no unsupported capacitance extraction."""
import argparse,hashlib,json,statistics
from pathlib import Path
import pya
ROOT=Path(__file__).resolve().parents[4];AUD=ROOT/'designs/g1-guardian/review/audits';METALS={'Metal1':8,'Metal2':10,'Metal3':30,'Metal4':50,'Metal5':67,'TopMetal1':126,'TopMetal2':134};p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists();gds=ROOT/'designs/g1-guardian/blocks/g1_padring/layout/g1_chip_top.gds';routefile=AUD/'sense-route-geometry-20260922-r1.json';rcfile=AUD/'external-route-rc-estimates-20260921.json';ly=pya.Layout();ly.read(str(gds));top=ly.cell('g1_chip_top');dbu=ly.dbu;fill={k:pya.Region(top.begin_shapes_rec(ly.layer(n,22))).merged() for k,n in METALS.items()};params=json.loads(rcfile.read_text())['layers'];rows=[]
for net in json.loads(routefile.read_text())['routes']:
 assert net['centerline_coverage_status']=='passed';layerpaths={}
 for seg in net['segments']:
  width=statistics.median(w for w in seg['sampled_widths_um'] if w is not None);r=pya.Region(pya.DPath([pya.DPoint(*seg['start_um']),pya.DPoint(*seg['end_um'])],width).to_itype(dbu));layerpaths.setdefault(seg['layer'],pya.Region());layerpaths[seg['layer']]+=r
 by=[]
 for metal,r in layerpaths.items():
  r=r.merged();idx=list(METALS).index(metal)
  for fm in list(METALS)[max(0,idx-1):min(len(METALS),idx+2)]:
   f=fill[fm];near=[]
   for dist in [0,1,2,5,10,20]:
    window=r.sized(round(dist/dbu));inter=f&window;near.append({'expanded_distance_um':dist,'overlap_area_um2':inter.area()*dbu**2,'interacting_fill_polygons':f.interacting(window).count()})
   lo,hi=0,round(20/dbu)
   if (r&f).is_empty():
    if (r.sized(hi)&f).is_empty():gap=None
    else:
     while hi-lo>1:
      mid=(lo+hi)//2
      if (r.sized(mid)&f).is_empty():lo=mid
      else:hi=mid
     gap=hi*dbu
   else:gap=0
   by.append({'route_layer':metal,'fill_layer':fm,'relationship':'same-layer' if metal==fm else 'adjacent-layer projection','Linf_expansion_to_first_area_overlap_um':gap,'gap_search_limit_um':20,'bands':near})
 R=sum(v['estimated_squares']*params[k]['sheet_ohm'] for k,v in net['layers'].items());C=sum(z['length_um']*(z['length_um']/z['estimated_squares_from_median_width']*params[z['layer']]['area_pF_um2']+2*params[z['layer']]['edge_pF_um']) for z in net['segments'])*1e-12
 rows.append({'net':net['net'],'length_um':net['total_length_um'],'wire_only_R_ohm_estimate':R,'wire_ground_C_F_estimate':C,'via_names':[v['name'] for v in net['via_instances']],'fill_proximity':by})
a.output.write_text(json.dumps({'scope':'Read-only deliveredGDS datatype22fill near DEFroute corridors with sampledmedianwidth. No conductorlabel propagation or capacitancecoupling extraction.','klayout_version':pya.__version__,'inputs':{str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [gds,routefile,rcfile]},'routes':rows,'limitations':['Minkowski sized-region overlap is axis-aligned geometricproximity, not3Ddielectric distance.','Cross-layer overlap does not implyconnectivity. Fill floating/grounded status is not extracted.','Existing nominalLEF groundC is not fillcoupling and must not be addedagainasfillcapacitance.','Nearfillgeometry alone cannot establish differentialerror, shielding or crosstalk; selectiveelectrostatic extraction/electricalsensitivity remainsnotrun.','Internalmacro nets and below-M1 devices are outside this route audit.']},indent=2)+'\n');print(json.dumps([{k:v for k,v in r.items() if k!='fill_proximity'} for r in rows],indent=2))

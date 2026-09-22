#!/usr/bin/env python3
"""Read-only native-clearance PDN spine and decap feeder reachability screen."""
import argparse
import collections
import json
import os
import time
from pathlib import Path
import pya
from place_closed_analog import region, sha, HERE
from audit_placed_decap_domains import physical, identity


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--core',type=Path,required=True)
    p.add_argument('--placement',type=Path,required=True)
    p.add_argument('--power-overlay',type=Path,action='append',default=[])
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    assert not a.output.exists() and len(os.sched_getaffinity(0))==1 and pya.__version__=='0.30.9'
    source=a.core/'refreshed_core.gds';meta=json.loads((a.core/'analysis.json').read_text())
    assert meta['status'].startswith('passed') and sha(source)==meta['GDS_sha256']
    a.output.mkdir(parents=True);(a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    started=time.monotonic()
    placed=json.loads((a.placement/'analysis.json').read_text())
    pack=json.loads((HERE/'coordinated-bbox-pack-20260922-r4.json').read_text())
    layout=pya.Layout();layout.read(str(source));top=layout.top_cell()
    net,metals=physical(layout,top)
    tm1=region(layout,top,pya.LayerInfo(126,0));m2=region(layout,top,pya.LayerInfo(10,0))
    upper_forbidden={layer:(region(layout,top,pya.LayerInfo(layer,0)).sized(400)+
                            region(layout,top,pya.LayerInfo(layer,22)).sized(420))for layer in (30,50,67)}
    m2_fill_forbidden=region(layout,top,pya.LayerInfo(10,22)).sized(420)
    overlay_bindings=[]
    for folder in a.power_overlay:
        metadata=json.loads((folder/'analysis.json').read_text())
        overlay=folder/'power_overlay.gds'
        assert metadata['status'].startswith('passed') and sha(overlay)==metadata['overlay_sha256']
        ol=pya.Layout();ol.read(str(overlay));ot=ol.top_cell();assert ol.dbu==.001
        # Existing macro supply branches own these lower-metal corridors.
        # A valid spine reservation alone does not reserve its via landings.
        m2_fill_forbidden+=region(ol,ot,pya.LayerInfo(10,0)).sized(420)
        for layer in upper_forbidden:
            upper_forbidden[layer]+=region(ol,ot,pya.LayerInfo(layer,0)).sized(420)
        overlay_bindings.append(dict(sha256=sha(overlay),metadata_sha256=sha(folder/'analysis.json')))
    landing_clear={}
    rings={
        'VDD':[pya.Box(344820,347160,359820,1066300),pya.Box(1054420,347160,1069420,1066300)],
        'VSS':[pya.Box(324820,327160,339820,1086300),pya.Box(1074420,327160,1089420,1086300)]}
    horizontals={'VDD':[(347160,362160),(1051300,1066300)],'VSS':[(327160,342160),(1071300,1086300)]}
    spines=[]
    lanes=[(index,'VDD'if index%2==0 else'VSS',box)for index,box in enumerate(pack['PDN_access_lane_reservations_um'])]
    # Existing side-ring conductors also provide legal vertical supply axes;
    # omitting these strands leaves the narrow edge decap islands stranded.
    for label,boxes in rings.items():
        for box in boxes:
            x=box.center().x/1000
            # Keep the existing full ring width. Narrow parallel extensions
            # would leave a sub-rule notch against the nearby lane-0 spine.
            lanes.append((100+len(lanes),label,[box.left/1000,321,box.right/1000,1093]))
    # Additional upper-metal axes in the narrow digital/analog interface.
    # Decaps are not removed: every lower-layer stack still needs a separate
    # native-clearance test, and these strands are screened against all TM1.
    lanes.extend([(200,'VDD',[747,321,753,1093]),(201,'VSS',[771,321,777,1093])])
    for index,label,box in lanes:
        own=pya.Region()
        for b in rings[label]:own.insert(b)
        assert (own-tm1).is_empty()
        forbidden=(tm1-own).sized(5000)+region(layout,top,pya.LayerInfo(126,22)).sized(5000)
        rawbox=pya.DBox(*box).to_itype(.001)
        # A side bite must not discard both legal full-width end segments.
        # Conservatively remove its entire y band, without weaving/narrowing.
        blocked_bands=pya.Region()
        for polygon in (forbidden&pya.Region(rawbox)).each():
            bb=polygon.bbox()
            blocked_bands.insert(pya.Box(rawbox.left,bb.bottom,rawbox.right,bb.top))
        candidate=pya.Region(rawbox)-blocked_bands
        for polygon in candidate.each():
            bbox=polygon.bbox()
            # Keep straight full-width pieces connected to an actual matching
            # ring crossing. A disconnected middle island is not a supply.
            if polygon.area()!=bbox.area() or bbox.width()<6000:continue
            crossings=[y for y in horizontals[label]if bbox.bottom<=y[0] and bbox.top>=y[1]]
            if not crossings:continue
            spines.append(dict(net=label,lane=index,bbox=[bbox.left,bbox.bottom,bbox.right,bbox.top],ring_crossings=crossings))
    groups=collections.defaultdict(list)
    for row in placed['decaps']:
        for label,pin in row['pins'].items():
            point=pin['placed_dbu'];key=identity(net,metals[10],point)
            assert key is not None
            groups[(label,key)].append(point)
    assert len(groups)==464
    by_label={label:{key for (name,key)in groups if name==label}for label in ('VDD','VSS')}
    assert not(by_label['VDD']&by_label['VSS'])
    supply_m2={};supply_forbidden={}
    for label in ('VDD','VSS'):
        mask=pya.Region()
        for (name,key),points in groups.items():
            if name==label:
                for x,y in points:mask.insert(pya.Box(x-1,y-1,x+1,y+1))
        supply_m2[label]=m2.interacting(mask)
        supply_forbidden[label]=(m2-supply_m2[label]).sized(400)+m2_fill_forbidden
    assert(supply_m2['VDD']&supply_m2['VSS']).is_empty()
    print(json.dumps(dict(phase='native graph and spine preparation',elapsed_s=time.monotonic()-started,spines=len(spines),components=len(groups))),flush=True)
    # Find existing M2 connected polygons by native probe labels. No source
    # voltage label is joined geometrically; feed polarity follows proven
    # placement metadata and will require a later full no-unexpected-merge gate.
    plans=[];missing=[]
    for (label,component),points in groups.items():
        own=pya.Region()
        point_mask=pya.Region()
        for x,y in points:point_mask.insert(pya.Box(x-1,y-1,x+1,y+1))
        for polygon in m2.interacting(point_mask).each():
            own.insert(polygon)
        assert not own.is_empty()
        # Joining separate components of the SAME proven decap supply is the
        # purpose of the PDN. Other logical supplies/native nets remain blocked.
        forbidden=supply_forbidden[label]
        candidates=[]
        for spine in spines:
            if spine['net']!=label:continue
            b=pya.Box(*spine['bbox']);sx=b.center().x
            for x,y in sorted(set(map(tuple,points)),key=lambda q:abs(q[0]-sx)):
                if spine['net']!=label or not b.bottom+2000<y<b.top-2000:continue
                feed=pya.Box(min(x,sx)-400,y-400,max(x,sx)+400,y+400)
                if not (pya.Region(feed)&forbidden).is_empty():continue
                # Via-stack landing clearance is assessed on all intermediate
                # native routing layers, not only the M2 wire corridor.
                landing=pya.Region(pya.Box(sx-1500,y-1500,sx+1500,y+1500))
                if (sx,y)not in landing_clear:
                    landing_clear[sx,y]=all((landing&shape).is_empty()for shape in upper_forbidden.values())
                if not landing_clear[sx,y]:
                    continue
                candidates.append(dict(spine_lane=spine['lane'],source_point=[x,y],via_center=[sx,y],
                                       route_layer=10,M2_bbox=[feed.left,feed.bottom,feed.right,feed.top],length_dbu=abs(x-sx)))
                break
        if not candidates:
            # A narrow island may be blocked horizontally on M2. Its source
            # stack can stop on M5, fly over intervening lower-metal circuitry,
            # and reach TM1 only inside its same-supply spine. Never add TM1
            # at the source endpoint where a different supply spine may pass.
            for spine in spines:
                if spine['net']!=label:continue
                b=pya.Box(*spine['bbox']);sx=b.center().x
                for x,y in sorted(set(map(tuple,points)),key=lambda q:abs(q[0]-sx)):
                    if not b.bottom+2000<y<b.top-2000:continue
                    sourcepad=pya.Region(pya.Box(x-400,y-400,x+400,y+400))
                    if not(sourcepad&forbidden).is_empty():continue
                    if any(not(sourcepad&upper_forbidden[layer]).is_empty()for layer in (30,50)):continue
                    bridge=pya.Box(min(x,sx)-750,y-750,max(x,sx)+750,y+750)
                    if not(pya.Region(bridge)&upper_forbidden[67]).is_empty():continue
                    candidates.append(dict(spine_lane=spine['lane'],source_point=[x,y],via_center=[sx,y],route_layer=67,
                                           M2_bbox=[x-400,y-400,x+400,y+400],
                                           M5_bbox=[bridge.left,bridge.bottom,bridge.right,bridge.top],length_dbu=abs(x-sx)))
                    break
        if candidates:
            plans.append(dict(net=label,component=list(component),pins=len(points),best=min(candidates,key=lambda r:r['length_dbu'])))
        else:missing.append(dict(net=label,component=list(component),pins=len(points),example=points[0]))
        if (len(plans)+len(missing))%20==0:
            progress=dict(phase='feeder screening',elapsed_s=time.monotonic()-started,completed=len(plans)+len(missing),reachable=len(plans),unreachable=len(missing))
            (a.output/'progress.json').write_text(json.dumps(progress,indent=2)+'\n');print(json.dumps(progress),flush=True)
    result=dict(status='passed read-only PDN reachability screen; no geometry adopted',source_GDS_sha256=sha(source),
                reserved_power_overlays=overlay_bindings,
                script_sha256=sha(Path(__file__)),spines=spines,components=len(groups),reachable=len(plans),
                unreachable=len(missing),plans=plans,missing=missing,
                not_run=['all via-stack geometry and redundant cuts','feeder-to-feeder interaction',
                         'physical PDN construction/connectivity','macro/pad power feeds','stock DRC/LVS/PEX/currentIR/EM'],
                not_applicable=['electrical adoption from read-only reachability'])
    (a.output/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items()if k not in ('plans','missing')},indent=2))


if __name__=='__main__':main()

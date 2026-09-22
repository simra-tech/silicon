#!/usr/bin/env python3
"""Read-only independent arithmetic review; no layout library or file writes."""
import collections
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[6]
PACK=ROOT/'designs/g1-guardian/review/audits/coordinated-bbox-pack-586-20260922-r1.json'
assert hashlib.sha256(PACK.read_bytes()).hexdigest()=='2663805a5180a1961850c1068b0c1c3615c010cd2ec47d38a228d65dde4800cb'
rows=collections.defaultdict(list)
for d in json.loads(PACK.read_text())['BGR_devices']:
    if d['kind']=='npn13G2':rows[d['slot_index']//17].append(d)
channels=[];base={};upper={};returns={}
for r,ds in rows.items():
    base[r]=set();upper[r]=set();returns[r]=set()
    for d in ds:
        c,b,e,s=d['source_line'].split()[1:5]
        if len({c,b,e,s})==1:continue
        base[r].add(b)
        if c!=b:upper[r].add(c)
        if e!='vss':upper[r].add(e)
        else:returns[r].add(d['original'])
    assert len(base[r])<=2 and len(upper[r])<=3
    assert len(returns[r])<=2 and (len(returns[r])<2 or 'XQ62' in returns[r])
for r in range(18):
    tracks=[(.15+.6*i,.3,'upper:'+n) for i,n in enumerate(sorted(upper[r]))]
    tracks+=[(2.2,.8,'guard')]
    tracks += [(3.65-.6*i,.3,'next_base:'+n) for i,n in enumerate(sorted(base[r+1]))]
    tracks.sort()
    gaps=[tracks[i+1][0]-tracks[i+1][1]/2-tracks[i][0]-tracks[i][1]/2 for i in range(len(tracks)-1)]
    assert min(gaps)>=.3-1e-10
    assert tracks[0][0]-tracks[0][1]/2>=-1e-10 and tracks[-1][0]+tracks[-1][1]/2<=4
    channels.append(dict(lower_row=r,upper_roles=sorted(upper[r]),next_base_roles=sorted(base[r+1]),
                         tracks=tracks,minimum_edge_gap_um=min(gaps)))
# Independent rectangular screen of the five lower M4 star branches, including
# square wire endcaps. These are not a replacement for the actual GDS audit.
branches={'XQ56':(1.2,16.26,16,16.26),'XQ60':(2.6,15.06,13.6,15.06),
          'XQ67':(4,13.86,14.8,15.06),'XQ62':(5.4,12.66,16,15.06),
          'guard':(7.2,11.46,17.2,15.06)}
rects={}
for n,(x,y,tx,ty) in branches.items():
    rects[n]=[(x-.4,y-.4,tx+.4,y+.4)]
    if ty!=y:rects[n].append((tx-.4,y-.4,tx+.4,ty+.4))
for n,rr in rects.items():
    for m,ss in rects.items():
        if n>=m:continue
        for a in rr:
            for b in ss:
                assert a[2]+.3<=b[0]+1e-10 or b[2]+.3<=a[0]+1e-10 or a[3]+.3<=b[1]+1e-10 or b[3]+.3<=a[1]+1e-10,(n,m,a,b)
print(json.dumps(dict(status='passed independent arithmetic only',channels=channels,
    physical_return_roles={r:sorted(v) for r,v in returns.items()},star_M4_rectangles=rects,
    star_M4_crossrole_300nm_rectangle_screen=True,
    explicit_old_literal_channel_failure='4.4um demand in4um retained, not rerouted evidence',
    actual_native_via_route_collision_graph_stock='not run by this script',seed='not applicable'),indent=2))

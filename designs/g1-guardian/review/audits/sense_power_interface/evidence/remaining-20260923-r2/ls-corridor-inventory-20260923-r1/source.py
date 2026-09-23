#!/usr/bin/env python3
"""Read-only flattened LS corridor and root-net ownership inventory."""
import argparse
import json
from pathlib import Path
import pya
from build_ls_interface import flat_physical, region, sha, METALS, CUTS, box


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--gds',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();assert not a.output.exists()
    assert sha(a.gds)=='88e5911aeaa4f0ae9c3c4712f4f2430563affa32bae0fe6c6c48c142e9611bdb'
    ly=pya.Layout();ly.read(str(a.gds));top=ly.top_cell()
    flat,net,metals=flat_physical(ly,top)
    roots={n:net.probe_net(metals[134],pya.Point(*pt))for n,pt in
           [('VDD',(395000,354660)),('VSS',(507000,334660))]}
    owned={n:{l:net.shapes_of_net(r,metals[l],True)for l in METALS}for n,r in roots.items()}
    window=box(730,484,788,508);rows=[]
    for layer in METALS+tuple(CUTS):
        native=region(ly,top,pya.LayerInfo(layer,0))
        for poly in native.interacting(window).each():
            part=pya.Region(poly)&window;b=poly.bbox()
            domains=[]
            for name,shapes in owned.items():
                if layer in METALS:
                    match=part&shapes[layer]
                else:
                    lo,hi=CUTS[layer];match=part&shapes[lo]&shapes[hi]
                if not match.is_empty():
                    assert(part-match).is_empty();domains.append(name)
            assert len(domains)<=1
            rows.append(dict(layer=layer,root_net=domains[0]if domains else None,
                             bbox_um=[v*.001 for v in(b.left,b.bottom,b.right,b.top)],
                             clipped_polygons=[str(q)for q in part.each()]))
    a.output.mkdir(parents=True);(a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    data=dict(status='passed read-only flat root ownership inventory',GDS_sha256=sha(a.gds),
              script_sha256=sha(Path(__file__)),rows=rows,not_run=['geometry changes','DRC','current qualification'])
    (a.output/'analysis.json').write_text(json.dumps(data,indent=2)+'\n')
    print(json.dumps(dict(status=data['status'],rows=len(rows))))


if __name__=='__main__':main()

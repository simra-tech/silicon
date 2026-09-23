#!/usr/bin/env python3
"""Read-only exact floating-fill inventory around the new TRIP metal."""
import argparse
import json
import os
from pathlib import Path
import pya
from build_ls_interface import region,sha


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in('source','candidate','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();assert not a.output.exists()and len(os.sched_getaffinity(0))==1 and pya.__version__=='0.30.9'
    assert sha(a.source)=='c99f3ae11b4501610939aa09b4581535a42d257f76951a25b4c84dd72a3afb90'
    ly=pya.Layout();ly.read(str(a.source));top=ly.cell('g1_trip')
    overlay=pya.Layout();overlay.read(str(a.candidate/'internal_overlay_local.gds'));ot=overlay.top_cell()
    card=Path('/foss/pdks/ihp-sg13g2/libs.tech/klayout/tech/drc/rule_decks/sg13g2_tech_default.json')
    def selected(value):
        result={}
        if isinstance(value,dict):
            for key,item in value.items():
                if 'fil'in key.lower()and isinstance(item,(int,float,str)):result[key]=item
                result.update(selected(item))
        elif isinstance(value,list):
            for item in value:result.update(selected(item))
        return result
    parameters=selected(json.loads(card.read_text()))
    rows=[]
    for layer in(8,10,30,50,67):
        draw=region(overlay,ot,pya.LayerInfo(layer,0));fill=region(ly,top,pya.LayerInfo(layer,22))
        owners=[]
        for cell in ly.each_cell():
            count=sum(1 for s in cell.shapes(ly.layer(layer,22)).each())
            if count:owners.append(dict(cell=cell.name,shapes=count))
        margins=[]
        for gap in(.42,.5,1.):
            selected=fill.interacting(draw.sized(round(gap*1000)))
            margins.append(dict(gap_um=gap,polygons=selected.count(),area_um2=selected.area()*1e-6,
                                bbox_um=[[v*.001 for v in(b.left,b.bottom,b.right,b.top)]for b in(q.bbox()for q in selected.each())]))
        rows.append(dict(layer=layer,datatype=22,fill_owners=owners,total_fill_polygons=fill.count(),
                         total_fill_area_um2=fill.area()*1e-6,prospective_halos=margins))
    a.output.mkdir(parents=True);(a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    (a.output/'analysis.json').write_text(json.dumps(dict(status='passed read-only fill inventory; no geometry saved',
        source_GDS_sha256=sha(a.source),candidate_overlay_sha256=sha(a.candidate/'internal_overlay_local.gds'),
        stock_fill_parameters=parameters,stock_card_sha256=sha(card),
        script_sha256=sha(Path(__file__)),rows=rows,not_run=['fill modification','final density','stock remedy acceptance']),indent=2)+'\n')
    print(json.dumps(dict(rows=rows,stock_fill_parameters=parameters),indent=2))


if __name__=='__main__':main()

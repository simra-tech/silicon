"""Independent native GDS delta and occupied wire windows after the DEF repair."""
import argparse,json,os
from pathlib import Path
import pya
from place_closed_analog import region,sha
from streamout_native_signal_routes import text_records

def main():
    p=argparse.ArgumentParser()
    for key in ['original','candidate','output']:p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();assert not a.output.exists() and len(os.sched_getaffinity(0))==1
    held={};layouts=[]
    for folder in [a.original,a.candidate]:
        m=json.loads((folder/'analysis.json').read_text());g=folder/'signal_routed_native.gds'
        assert m['status']=='passed native-preserving DEF signal-route streamout and exact geometry roundtrip'
        assert sha(g)==m['GDS_sha256'];held[str(g)]=sha(g);held[str(folder/'analysis.json')]=sha(folder/'analysis.json')
        ly=pya.Layout();ly.read(str(g));assert ly.dbu==.001
        layouts.append((ly,ly.top_cell()))
    (old,ot),(new,nt)=layouts
    assert ot.name==nt.name and ot.bbox()==nt.bbox()
    assert text_records(old,ot)==text_records(new,nt)
    infos={(i.layer,i.datatype) for ly,_ in layouts for i in ly.layer_infos()}
    deltas=[]
    for layer,datatype in sorted(infos):
        info=pya.LayerInfo(layer,datatype);before=region(old,ot,info);after=region(new,nt,info)
        removed=before-after;added=after-before
        if removed.is_empty() and added.is_empty():continue
        assert (layer,datatype)==(30,0)
        window=pya.Region(pya.Box(404000,359800,415850,360650))
        assert ((removed+added)-window).is_empty()
        old_wire=pya.Region(pya.Box(404160,360260,415680,360460))
        new_wire=pya.Region(pya.Box(404160,360380,415680,360580))
        assert (old_wire-before).is_empty() and (new_wire-after).is_empty()
        for x in [404160,415680]:
            assert (pya.Region(pya.Box(x-100,359940,x+100,360480))-after).is_empty()
        deltas.append(dict(layer=layer,datatype=datatype,removed_area_um2=removed.area()*1e-6,added_area_um2=added.area()*1e-6,
                           removed_polygons=[p.to_s() for p in removed.each()],added_polygons=[p.to_s() for p in added.each()]))
    assert len(deltas)==1 and deltas[0]['added_area_um2']>0 and deltas[0]['removed_area_um2']>0
    assert all(sha(Path(f))==h for f,h in held.items())
    a.output.mkdir(parents=True);(a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    result=dict(status='passed bounded M3-only route geometry delta and occupied three-segment windows',inputs=held,deltas=deltas,
                same_die_texts_all_other_layers=True,not_run=['Full source-terminal connectivity','Stock DRC','RCX/electrical adoption'])
    (a.output/'analysis.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

if __name__=='__main__':main()

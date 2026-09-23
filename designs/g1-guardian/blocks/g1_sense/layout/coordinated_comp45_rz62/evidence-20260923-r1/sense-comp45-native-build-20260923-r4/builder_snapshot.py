#!/usr/bin/env python3
"""Isolated two-passive native replacement in r8; no canonical/fullchip mutation."""
import argparse,collections,copy,json,os
from pathlib import Path
from inspect_passive_sites import lib,pya,sha,regions,native,box,PARENT,SOURCE
from build_power_revision import snapshot,full_nets_upper

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ['parent','metadata','source','output']:p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--cpu',type=int,required=True);a=p.parse_args()
    assert os.sched_getaffinity(0)=={a.cpu} and a.cpu==1 and pya.__version__=='0.30.9'
    assert not a.output.exists() and sha(a.parent)==PARENT and sha(a.source)==SOURCE
    m=json.loads(a.metadata.read_text());assert m['GDS_sha256']==PARENT
    a.output.mkdir(parents=True);(a.output/'builder_snapshot.py').write_bytes(Path(__file__).read_bytes())
    result=dict(status='running isolated C45/R62 replacement',parent_GDS_sha256=PARENT,source_sha256=SOURCE,
        parent_metadata_sha256=sha(a.metadata),builder_sha256=sha(Path(__file__)),stock_checks='not run',PEX='not run',adoption='not run')
    try:
        ly=pya.Layout();ly.read(str(a.parent));cell=ly.cell('g1_sense_physical');cell.flatten(True)
        before=regions(cell);texts={}
        for li in ly.layer_indexes():
            info=ly.get_info(li);texts[(info.layer,info.datatype)]=[s.text.dup() for s in cell.shapes(li).each() if s.is_text()]
        oldregs={};newregs={};native_records=[]
        def saved_native(kind,params,label):
            rawly,raw=native(kind,params);r=regions(raw)
            path=a.output/(label+'_native_control.gds');rawly.write(str(path))
            savedly=pya.Layout();savedly.read(str(path));saved=savedly.cell(raw.name)
            s=regions(saved);assert set(r)==set(s) and all((r[k]^s[k]).is_empty() for k in r)
            return savedly,saved
        recipes=[('XCC','cmim',dict(Calculate='C',w='69u',l='23u'),dict(Calculate='C',w='45u',l='23u'),[60.46,122.,130.66,146.2],pya.Trans.R0),
                 ('XRZ','rppd',dict(Calculate='R',w='1u',l='6.2u'),dict(Calculate='R',w='1u',l='62u'),[123.92,152.,125.32,159.42],pya.Trans.R270)]
        for name,kind,oldpars,newpars,target,rotation in recipes:
            oldly,old=saved_native(kind,oldpars,name+'_old');oldbox=old.bbox()
            oldtrans=pya.Trans(round(target[0]*1000)-oldbox.left,round(target[1]*1000)-oldbox.bottom)
            o={k:r.transformed(oldtrans) for k,r in regions(old).items()}
            assert all((r-before.get(k,pya.Region())).is_empty() for k,r in o.items())
            newly,new=saved_native(kind,newpars,name+'_new');rot=pya.Trans(rotation);b=pya.Region(new.bbox()).transformed(rot).bbox()
            trans=pya.Trans(rot.rot,False,round(target[0]*1000)-b.left,round(target[1]*1000)-b.bottom)
            n={k:r.transformed(trans) for k,r in regions(new).items()}
            # Native cell annotation text is replaced exactly; every unrelated text is held.
            for local,transform,remove in [(old,oldtrans,True),(new,trans,False)]:
                for li in local.layout().layer_indexes():
                    info=local.layout().get_info(li);key=(info.layer,info.datatype)
                    it=local.begin_shapes_rec(li)
                    while not it.at_end():
                        if it.shape().is_text():
                            text=it.shape().text.transformed(it.trans()).transformed(transform)
                            if remove:
                                hits=[i for i,t in enumerate(texts.get(key,[])) if t.to_s()==text.to_s()]
                                assert len(hits)==1,(name,text.to_s(),hits,[t.to_s() for t in texts.get(key,[]) if t.string==text.string]);texts[key].pop(hits[0])
                            else:texts.setdefault(key,[]).append(text)
                        it.next()
            for dest,data in [(oldregs,o),(newregs,n)]:
                for k,r in data.items():dest[k]=dest.get(k,pya.Region())+r
            native_records.append(dict(device=name,old_parameters=oldpars,new_parameters=newpars,
                old_transform=str(oldtrans),new_transform=str(trans),old_native_layers={str(k):box(r) for k,r in o.items()},new_native_layers={str(k):box(r) for k,r in n.items()}))
        changed=set(oldregs)|set(newregs)
        for key in changed:
            li=ly.layer(*key);cell.shapes(li).clear()
            r=(before.get(key,pya.Region())-oldregs.get(key,pya.Region()))+newregs.get(key,pya.Region())
            for poly in r.merged().each():cell.shapes(li).insert(poly)
            for text in texts.get(key,[]):cell.shapes(li).insert(text)
        D=lib.Draw(ly,cell)
        # Restore only narrow same-net top/bottom egress, not the old full plates.
        D.box('M5',106.16,126.,130.16,127.2)
        D.box('TM1',105.4,130.6,129.4,132.6)
        # R270 retains out1 at left, cz at right; source/model terminal order held.
        D.vwire('M1',124.3,152.33,153.02,.34)
        D.hwire('M1',124.25,124.3,153.02,.34)
        D.stack(186.81,152.38,'M1','M3')
        D.vwire('M3',186.81,133.,152.38,.4)
        D.stack(186.81,133.,'M3','M4')
        probes=copy.deepcopy(m['terminal_audit']['probes'])
        rz=[q for q in probes if q['device']=='XOTA/XRZ'];assert len(rz)==2
        for q in rz:q['point_um']=[124.25,153.02] if q['net']=='XOTA/out1' else [186.81,152.38]
        after=regions(cell)
        assert (before[(1,0)]^after[(1,0)]).is_empty()
        oldchannels=before[(1,0)]&before[(5,0)];newchannels=after[(1,0)]&after[(5,0)]
        assert oldchannels.count()==835 and (oldchannels^newchannels).is_empty()
        assert all((before[k]^after.get(k,pya.Region())).is_empty() for k in before if k[1] in [2,25])
        result.update(native_replacements=native_records,active_XOR_um2=0.,channel_XOR_um2=0.,channels=835,
            delta_layers={str(k):dict(removed_um2=(before.get(k,pya.Region())-after.get(k,pya.Region())).area()*1e-6,
                added_um2=(after.get(k,pya.Region())-before.get(k,pya.Region())).area()*1e-6) for k in set(before)|set(after) if not (before.get(k,pya.Region())^after.get(k,pya.Region())).is_empty()})
        graph=full_nets_upper(cell,probes);result['terminal_audit']=graph
        (a.output/'preaudit.json').write_text(json.dumps(result,indent=2)+'\n')
        assert graph['status']=='passed' and graph['source_net_count']==134,(graph['opens'],graph['shorts'])
        b=cell.bbox();assert b.left>=0 and b.bottom>=0 and b.right<=385000 and b.top<=240000
        gds=a.output/'g1_sense_physical.gds';ly.write(str(gds))
        saved=pya.Layout();saved.read(str(gds));sc=saved.cell(cell.name);sr=regions(sc)
        assert set(sr)==set(after) and all((sr[k]^r).is_empty() for k,r in after.items())
        saved_texts={}
        for li in saved.layer_indexes():
            info=saved.get_info(li);saved_texts[(info.layer,info.datatype)]=[s.text.to_s() for s in sc.shapes(li).each() if s.is_text()]
        for key in set(texts)|set(saved_texts):
            assert collections.Counter(t.to_s() for t in texts.get(key,[]))==collections.Counter(saved_texts.get(key,[])),key
        saved_graph=full_nets_upper(sc,copy.deepcopy(probes));assert saved_graph['status']=='passed'
        result.update(status='passed isolated two-passive geometry/connectivity',GDS_sha256=sha(gds),
            bbox_um=box(pya.Region(b)),saved_polygon_XOR_um2=0.,external_port_map=m['external_port_map'],
            model_AP_scope='Unchanged MOS native topology; prior51 extracted A/P annotation differences and intrinsic attachment limits retained.',
            field_scope='Changed intrinsic MIM and added terminal routes need affected field checks. Complete MIM field coverage still unresolved.')
    except Exception as exc:
        result.update(status='failed isolated two-passive geometry/connectivity',error=repr(exc));(a.output/'failure.json').write_text(json.dumps(result,indent=2)+'\n');raise
    (a.output/'manifest.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='terminal_audit'},indent=2))
if __name__=='__main__':main()

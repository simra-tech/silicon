#!/usr/bin/env python3
"""Four exact XM14 ordinary-metal clips; no field or electrical acceptance."""
import argparse
import collections
import copy
import json
import os
from pathlib import Path
import time
import pya
from screen_sense_dual_gate_proposal import GM4, graph, regions, sha, inside_point
from build_sense_dual_gate import snapshot
from prepare_sense_feed_field_inventory import BASELINE, CANDIDATE, SOURCE, METALS

CUTS = {19:(8,10),29:(10,30),49:(30,50),66:(50,67),125:(67,126),133:(126,134)}
INVENTORY = '338d0eef0acd33ccc13a13b451de4b87eca567bacd26e23fb23b2b4184c4c8ef'
NETS = {24:{'vdd','vss','XOTA/pc1','XOTA/mir','XOTA/vbpc'},
        48:{'vdd','vss','XOTA/pc1','XOTA/mir','XOTA/vbpc','XOTA/fn','XOTA/out1','XOTA/pc2','iptat'}}


def local_membership(cell, labels):
    ly=cell.layout(); net=pya.LayoutToNetlist(pya.RecursiveShapeIterator(ly,cell,[])); layers={}
    for layer in METALS:
        layers[layer]=net.make_layer(ly.layer(layer,0),'M'+str(layer)); net.connect(layers[layer])
    for layer,joined in CUTS.items():
        cut=net.make_layer(ly.layer(layer,0),'V'+str(layer)); net.connect(cut)
        for conductor in joined: net.connect(cut,layers[conductor])
    net.extract_netlist(); groups=collections.defaultdict(list)
    for row in labels:
        found=net.probe_net(layers[row['layer']],pya.Point(*row['point_dbu'])); assert found is not None
        groups[found.cluster_id].append(row)
    count=sum(1 for c in net.netlist().each_circuit() for n in c.each_net())
    assert count==len(groups),'Unlabelled physical component'
    records=[]
    for rows in groups.values():
        sources={r['source_net'] for r in rows}; assert len(sources)==1,'Foreign source-net merge'
        records.append(dict(labels=sorted(r['label'] for r in rows),source_net=next(iter(sources)),
                            group=rows[0]['group']))
    return sorted(records,key=lambda r:r['labels'])


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('candidate','inventory','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();assert not a.output.exists() and len(os.sched_getaffinity(0))==1 and pya.__version__=='0.30.9'
    assert sha(a.inventory)==INVENTORY
    inv=json.loads(a.inventory.read_text());assert inv['status']=='passed exact changed-geometry adjacency inventory; field extraction not run'
    source=GM4.parents[1]/'reports/resume-server-20260922/gm4comp3-qualified-source.spice';assert sha(source)==SOURCE
    base=GM4/'ring-r8-evidence-20260922-r1/sense-ring-routing-20260922-r8a/g1_sense_physical.gds'
    candidate=a.candidate/'g1_sense_physical.gds';assert sha(base)==BASELINE and sha(candidate)==CANDIDATE
    m=json.loads((a.candidate/'manifest.json').read_text());assert m['GDS_sha256']==CANDIDATE
    a.output.mkdir(parents=True);(a.output/'source.py').write_bytes(Path(__file__).read_bytes())
    result=dict(status='running four-clip geometry preparation',source_sha256=SOURCE,
        baseline_GDS_sha256=BASELINE,candidate_GDS_sha256=CANDIDATE,inventory_sha256=INVENTORY,
        script_sha256=sha(Path(__file__)),clips=[],not_run=['KPEX','AC/context acceptance','Complete field','Circuit composition/adoption'])
    start=time.monotonic()
    try:
        for state,path,digest in [('before',base,BASELINE),('after',candidate,CANDIDATE)]:
            ly=pya.Layout();ly.read(str(path));cell=ly.cell('g1_sense_physical')
            native=regions(cell); all_layers=snapshot(cell)
            hold=graph(native,copy.deepcopy(m['terminal_audit']['probes']));net,layers,expected,audit=hold[1:]
            assert audit['status']=='passed' and audit['source_net_count']==134
            physical_names={next(iter(v)):name for name,v in expected.items()}
            for context in (24,48):
                name=state+str(context);leaf=a.output/name;leaf.mkdir()
                box=pya.Box(112790,49030-context*500,132790,49030+context*500);window=pya.Region(box)
                assert all((all_layers.get((layer,22),pya.Region())&window).is_empty() for layer in METALS),'Unexpected actual fill'
                assert all((all_layers.get((layer,0),pya.Region())&window).is_empty() for layer in (36,129)),'Native MIM/Vmim in pilot'
                clipped={layer:(native[layer]&window).merged() for layer in METALS+tuple(CUTS)}
                labels=[];p_anchor=pya.Point(122790,49030)
                for layer in METALS:
                    for index,polygon in enumerate(clipped[layer].each()):
                        pt=inside_point(polygon);found=net.probe_net(layers[layer],pt);assert found is not None
                        source_net=physical_names.get(found.cluster_id);assert source_net is not None
                        group='P' if source_net=='vdd' else 'N' if source_net=='XOTA/pc1' else 'context'
                        label=('PSEG' if group=='P' else 'NSEG' if group=='N' else 'CTX')+'_L%d_%d'%(layer,index)
                        if layer==10 and polygon.inside(p_anchor):
                            assert group=='P';label='P';pt=p_anchor
                        labels.append(dict(label=label,group=group,source_net=source_net,layer=layer,
                            point_dbu=[pt.x,pt.y],polygon_area_dbu2=polygon.area(),polygon_bbox_dbu=str(polygon.bbox())))
                n_candidates=[r for r in labels if r['group']=='N' and r['layer']==8];assert n_candidates
                chosen=sorted(n_candidates,key=lambda r:(-r['polygon_area_dbu2'],r['label']))[0];chosen['label']='N'
                assert sum(r['label']=='P' for r in labels)==sum(r['label']=='N' for r in labels)==1
                assert {r['source_net'] for r in labels}==NETS[context]
                out=pya.Layout();out.dbu=.001;top=out.create_cell('sense_fill_clip')
                for layer,region in clipped.items():top.shapes(out.layer(layer,0)).insert(region)
                for row in labels:top.shapes(out.layer(row['layer'],25)).insert(pya.Text(row['label'],pya.Trans(*row['point_dbu'])))
                membership=local_membership(top,labels)
                target=leaf/'clip.gds';out.write(str(target));saved=pya.Layout();saved.read(str(target));again=saved.cell('sense_fill_clip')
                for layer,region in clipped.items():
                    observed=pya.Region(again.begin_shapes_rec(saved.layer(layer,0)))
                    assert (region^observed).is_empty(),(name,layer)
                assert local_membership(again,labels)==membership
                saved_labels=sorted((saved.get_info(li).layer,s.text.string,s.text.trans.disp.x,s.text.trans.disp.y)
                    for li in saved.layer_indexes() if saved.get_info(li).datatype==25 for s in again.shapes(li).each() if s.is_text())
                assert saved_labels==sorted((r['layer'],r['label'],*r['point_dbu']) for r in labels)
                excluded=[dict(layer=list(key),clipped_area_dbu2=(region&window).area())
                    for key,region in all_layers.items() if key[0] in (1,5,6,31,36,128,129) and not (region&window).is_empty()]
                proof=dict(status='passed exact source/member/roundtrip clip preparation',source_GDS_sha256=digest,
                    source_sha256=SOURCE,GDS_sha256=sha(target),state=state,context_um=context,
                    bbox_dbu=[box.left,box.bottom,box.right,box.top],labels=labels,components=membership,
                    fill_count=0,MIM_Vmim_count=0,excluded_primitive_materials=excluded,
                    boundary='P/N same-full-net pieces ideally tied only outside clip; all other drawing nets and VSUBS grounded diagnostic',
                    scope='Ordinary-metal only; no device-owned Poly/Active/Cont/depletion field or finite-R terminal model')
                (leaf/'provenance.json').write_text(json.dumps(proof,indent=2)+'\n')
                result['clips'].append(dict(name=name,GDS_sha256=sha(target),provenance_sha256=sha(leaf/'provenance.json'),
                    labels=len(labels),components=len(membership)))
        assert len(result['clips'])==4 and sha(base)==BASELINE and sha(candidate)==CANDIDATE and sha(source)==SOURCE
        result['status']='passed four exact source-held XM14 pilot clips; extraction not run'
    except Exception as exc:
        result.update(status='failed field clip preparation',error=repr(exc));raise
    finally:
        result['wall_s']=time.monotonic()-start
        (a.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()

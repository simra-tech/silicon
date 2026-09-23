#!/usr/bin/env python3
"""Isolated additive M2 source-feeder remedy; all primitive geometry is held."""
import argparse
import collections
import copy
import json
import os
from pathlib import Path
import time
import pya
from build_sense_dual_gate import snapshot, text_snapshot, hierarchy
from screen_sense_dual_gate_proposal import GM4, graph, regions, sha, inside_point

STATUS='passed source-held M2 feeder geometry; stock checks not run'
FEEDS=[dict(device='XOTA/XM14',net='vdd',x1=15380,x2=230200,y=49030,expected_contacts=575),
       dict(device='XOTA/XM11',net='vdd',x1=15380,x2=230200,y=89530,expected_contacts=575),
       dict(device='XOTA/XM4',net='vss',x1=32900,x2=231400,y=103030,expected_contacts=483),
       dict(device='XOTA/XM3',net='vss',x1=32900,x2=231400,y=35530,expected_contacts=483)]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--footprints',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--maximum-width-dbu',type=int,default=6000)
    args=parser.parse_args();assert not args.output.exists()
    assert len(os.sched_getaffinity(0))==1 and pya.__version__=='0.30.9'
    assert args.maximum_width_dbu in (800,1200,1600,2200,2400,3200,4000,6000)
    base=GM4/'ring-r8-evidence-20260922-r1'
    parent=base/'sense-ring-routing-20260922-r8a';gds=parent/'g1_sense_physical.gds'
    reference=base/'sense-ring-reference-20260922-r8a/manifest.json'
    source=GM4.parents[1]/'reports/resume-server-20260922/gm4comp3-qualified-source.spice'
    catalog=json.loads(args.footprints.read_text())
    assert sha(gds)==catalog['GDS_sha256']=='8060e30ac14a1c4aeb1cf62204c9e95d9a68dbad3d73412fbb34c6a33be8b4f7'
    assert sha(source)==catalog['source_sha256']=='baab6183c364477da1dd332e4585ae7201b3776bf0f836014744a42809e13877'
    ref=json.loads(reference.read_text());assert ref['source_sha256']==sha(source)
    args.output.mkdir(parents=True);(args.output/'source.py').write_bytes(Path(__file__).read_bytes())
    result=dict(status='running isolated M2 feeder build',source_sha256=sha(source),baseline_GDS_sha256=sha(gds),
                reference_sha256=sha(reference),footprints_sha256=sha(args.footprints),script_sha256=sha(Path(__file__)),
                new_GDS_saved=False,source_parameters_unchanged=True,
                not_run=['Stock main/maximal/strict LVS','New metal-R topology and bound comparison',
                         'Affected field/current/electrical and intrinsic applicability','Fullchip adoption'])
    start=time.monotonic()
    try:
        ly=pya.Layout();ly.read(str(gds));cell=ly.cell('g1_sense_physical')
        old=snapshot(cell);old_text=text_snapshot(cell);old_hierarchy=hierarchy(ly);native=regions(cell)
        probes=copy.deepcopy(ref['terminal_audit']['probes'])
        hold=graph(native,probes);network,layers,expected,before=hold[1:]
        assert before['status']=='passed' and before['source_net_count']==134
        names={next(iter(v)):name for name,v in expected.items()}
        owned=collections.defaultdict(pya.Region)
        for poly in native[10].each():
            net=network.probe_net(layers[10],inside_point(poly));assert net is not None
            owned[names.get(net.cluster_id,'UNASSIGNED:'+str(net.cluster_id))].insert(poly)
        additions={10:pya.Region(),19:pya.Region()};changed=[];screens=[]
        for feed in FEEDS:
            x1,x2,y=feed['x1'],feed['x2'],feed['y'];foreign=native[10]-owned[feed['net']]
            original=pya.Region(pya.Box(x1-200,y-200,x2+200,y+200))
            assert (original-owned[feed['net']]).is_empty(),'Expected original .4um feeder not present'
            choices=[]
            for width in (800,1200,1600,2200,2400,3200,4000,6000):
                if width>args.maximum_width_dbu:continue
                rectangle=pya.Box(x1-200,y-width//2,x2+200,y+width//2)
                # Conservative preparation screen, not a substitution for stock rules.
                clearance=1000 if width>2500 else 400
                conflict=pya.Region(rectangle).sized(clearance-1)&foreign
                screens.append(dict(device=feed['device'],width_dbu=width,clearance_dbu=clearance,
                                    foreign_overlap_dbu2=conflict.area(),passed=conflict.is_empty()))
                if conflict.is_empty():choices.append((width,rectangle))
            assert choices,('No screened widening',feed['device'])
            width,rectangle=choices[-1];additions[10].insert(rectangle)
            # The existing M1 source bar, not a nearby same-net tap, must contain
            # every source-owned contact and the original first source access.
            source_shapes=[p for p in native[8].each() if p.inside(pya.Point(x1,y))]
            assert len(source_shapes)==1;bar=pya.Region(source_shapes[0])
            contacts=[r for r in catalog['footprints'] if any(o['device']==feed['device'] and o['terminal']=='S' for o in r['owners'])]
            assert len(contacts)==feed['expected_contacts']
            assert all((pya.Region(pya.Box(*r['bbox_dbu']))-bar).is_empty() for r in contacts)
            available=[]
            for x in range(x1+1000,x2-1000,420):
                cut=pya.Region(pya.Box(x-95,y-95,x+95,y+95))
                if not (cut.sized(50)-bar).is_empty():continue
                if not (cut.sized(219)&native[19]).is_empty():continue
                if not (cut.sized(50)-pya.Region(rectangle)).is_empty():continue
                available.append(x)
            assert len(available)>=8,('Missing eight legal M1-source-bar cut sites',feed['device'])
            selected=available[:4]+available[-4:];assert len(set(selected))==8
            cuts=[]
            for x in selected:
                box=pya.Box(x-95,y-95,x+95,y+95);new=pya.Region(box)
                assert (new.sized(219)&additions[19]).is_empty()
                additions[19].insert(box);cuts.append([box.left,box.bottom,box.right,box.top])
            changed.append(dict(feed,selected_width_dbu=width,M2_bbox_dbu=[rectangle.left,rectangle.bottom,rectangle.right,rectangle.top],
                                Via1_bboxes_dbu=cuts,unchanged_M1_source_bar_contacts=len(contacts)))
        (args.output/'screen.json').write_text(json.dumps(screens,indent=2)+'\n')
        for layer,region in additions.items():
            region.merge();cell.shapes(ly.layer(layer,0)).insert(region)
        after_native=regions(cell);after=graph(after_native,probes)[-1]
        assert after['status']=='passed' and after['source_net_count']==134
        assert after['all_physical_nets']==before['all_physical_nets']
        for layer in(1,5,6,8,30,50,67,126,134,501):assert (native[layer]^after_native[layer]).is_empty()
        output=args.output/'g1_sense_physical.gds';ly.write(str(output));result['new_GDS_saved']=True
        saved=pya.Layout();saved.read(str(output));top=saved.cell(cell.name);new=snapshot(top)
        for key in set(old)|set(new):
            added=additions.get(key[0],pya.Region()) if key[1]==0 else pya.Region()
            assert (new.get(key,pya.Region())^(old.get(key,pya.Region())+added)).is_empty(),key
        assert text_snapshot(top)==old_text and hierarchy(saved)==old_hierarchy
        saved_audit=graph(regions(top),copy.deepcopy(probes))[-1];assert saved_audit==after
        assert sha(source)==result['source_sha256'] and sha(gds)==result['baseline_GDS_sha256']
        manifest=json.loads((parent/'manifest.json').read_text())
        manifest.update(status=STATUS,GDS_sha256=sha(output),baseline_GDS_sha256=sha(gds),
                        terminal_audit=dict(saved_audit,probes=probes),source_unchanged=True,stock_checks='not run',PEX='not run',adoption='not run')
        (args.output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
        (args.output/'changed_shapes.json').write_text(json.dumps(changed,indent=2)+'\n')
        result.update(status=STATUS,GDS_sha256=sha(output),before_graph=before,after_graph=saved_audit,
                      selected_widths_dbu=[r['selected_width_dbu'] for r in changed],added_Via1_cuts=additions[19].count(),
                      primitive_channels_diffusions_contacts_M1_exact=True,all_other_layers_text_hierarchy_exact=True,
                      M2_added_area_dbu2=(additions[10]-native[10]).area())
    except Exception as exc:
        result.update(status='failed M2 feeder geometry',error=repr(exc));raise
    finally:
        result['wall_s']=time.monotonic()-start
        (args.output/'analysis.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()

#!/usr/bin/env python3
"""Add only the approved19 signal and2 T2F feed cuts; account all drawing deltas."""
import argparse,hashlib,json,os
from pathlib import Path
import pya
from sense_route_manifest import load_candidate_resistances
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--manifest',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
a=p.parse_args();assert not a.output.exists() and pya.__version__=='0.30.9' and len(os.sched_getaffinity(0))==1
base=Path(__file__).parent;sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
m,_=load_candidate_resistances(a.manifest)
inputs={name:base/name for name in ('signal-via-redundancy-screen-20260922-r1.json','vref-via-asymmetric-screen-20260922-r1.json','t2f-feed-topvia-pair-screen-20260922-r1.json')}
signal,asym,feeds=[json.loads(path.read_text()) for path in inputs.values()]
assert all(row['candidate_sha256']==m['candidate_sha256'] for row in (signal,asym,feeds))
patches=[]
for row in signal['results']:
    if row['net'].split('.')[-1] not in ('gate_o','cmp_clk','vref','iptat'):continue
    option=row['provisional_best_option']
    if option is None:
        assert row['net']==asym['net'] and row['point_um']==asym['point_um'] and asym['status'].startswith('passed')
        option=asym
    assert option['cut_spacing_clear']
    patches.append({'net':row['net'],'point_um':row['point_um'],'cut_layer':row['cut_layer'],'old_cut_bbox_um':row['existing_cut_bbox_um'],
        'added_cut_bbox_um':option['added_cut_bbox_um'],'metals':option['metals'],'scope':'critical signal local single-open redundancy; load and added C not qualified'})
assert len(patches)==19
for row in feeds['results']:
    option=row['provisional_best_option'];assert option and option['cut_spacing_clear']
    patches.append({'net':row['net'],'point_um':row['point_um'],'cut_layer':133,'old_cut_bbox_um':row['old_cut_bbox_um'],
        'added_cut_bbox_um':option['added_cut_bbox_um'],'metals':option['metals'],'scope':'proven T2F feed single-open isolation; actual access-current partition unknown'})
assert len(patches)==21
ly=pya.Layout();ly.read(str(a.manifest.parent/'g1_chip_top.gds'));top=ly.cell('g1_chip_top');dbu=ly.dbu;assert dbu==.001
box=lambda values:pya.DBox(*values).to_itype(dbu)
additions={};checks=[]
for row in patches:
    old,new=box(row['old_cut_bbox_um']),box(row['added_cut_bbox_um'])
    additions.setdefault(row['cut_layer'],pya.Region()).insert(new)
    for metal in row['metals']:additions.setdefault(metal['layer'],pya.Region()).insert(box(metal['landing_bbox_um']))
    checks.append({'net':row['net'],'point_um':row['point_um'],'both_cuts_fully_in_each_common_landing':all((pya.Region(old)+pya.Region(new)-pya.Region(box(metal['landing_bbox_um']))).is_empty() for metal in row['metals'])})
assert all(row['both_cuts_fully_in_each_common_landing'] for row in checks)
before={layer:pya.Region(top.begin_shapes_rec(ly.layer(layer,0))).merged() for layer in additions}
for layer,region in additions.items():
    for shape in region.merged().each():top.shapes(ly.layer(layer,0)).insert(shape)
a.output.mkdir(parents=True);candidate=a.output/'g1_chip_top.gds';ly.write(str(candidate))
reloaded=pya.Layout();reloaded.read(str(candidate));aftertop=reloaded.cell('g1_chip_top');accounting=[]
original=pya.Layout();original.read(str(a.manifest.parent/'g1_chip_top.gds'));originaltop=original.cell('g1_chip_top')
keys={(i.layer,i.datatype) for i in original.layer_infos()}|{(i.layer,i.datatype) for i in reloaded.layer_infos()}
for layer,datatype in sorted(keys):
    left=before[layer] if datatype==0 and layer in before else pya.Region(originaltop.begin_shapes_rec(original.layer(layer,datatype))).merged()
    right=pya.Region(aftertop.begin_shapes_rec(reloaded.layer(layer,datatype))).merged()
    expected=(left+additions[layer]).merged() if datatype==0 and layer in additions else left
    xor=right^expected;removed=left-right;added=right-left
    assert xor.is_empty() and removed.is_empty(),(layer,datatype)
    if not added.is_empty():accounting.append({'layer':layer,'datatype':datatype,'added_area_um2':added.area()*dbu**2,'removed_area_um2':0,'unexpected_XOR_um2':0})
assert sha(a.manifest.parent/'g1_chip_top.gds')==m['candidate_sha256']
result=dict(m);result.update(candidate_sha256=sha(candidate),parent_candidate_sha256=m['candidate_sha256'],parent_manifest_sha256=sha(a.manifest),
    script_sha256=sha(Path(__file__)),screen_hashes={name:sha(path) for name,path in inputs.items()},via_patches=patches,
    local_one_cut_open_landing_checks=checks,all_nontext_layers_exact_additive_accounting='passed',drawing_delta=accounting,
    scope='Approved19 critical signal stages plus2 T2F feed TopVia2 cuts. Original cuts, stock cells, fill, routes and existing SENSE arrays retained. Source routes field inherited unchanged; it is not new whole-candidate RC extraction.',
    deferred_signal_stages=12,stock_DRC_LVS_antenna_density='not run',global_connectivity='not run',current_margin='not run',affected_RC='not run')
(a.output/'manifest.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'candidate_sha256':result['candidate_sha256'],'patches':len(patches),'drawing_delta':accounting},indent=2))
